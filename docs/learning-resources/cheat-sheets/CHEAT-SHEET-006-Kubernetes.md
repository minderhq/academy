---
Document ID: CHEAT-SHEET-006
Title: "CHEAT-SHEET-006: Kubernetes for LLM Deployment"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'kubernetes', 'deployment']
---

# CHEAT-SHEET-006: Kubernetes for LLM Deployment

## Quick Reference for K3s/K8s LLM Workloads

**Version:** 1.1

---

## Installation

### K3s Quick Install

```bash
# Server (Master)
curl -sfL https://get.k3s.io | sh -

# Get node token
sudo cat /var/lib/rancher/k3s/server/node-token

# Worker
curl -sfL https://get.k3s.io | K3S_URL=https://server-ip:6443 K3S_TOKEN=xxx sh -

# Verify
kubectl get nodes
```

---

## Basic Commands

### Cluster Info

```bash
kubectl cluster-info
kubectl get nodes
kubectl get pods -A
kubectl get services
```

### Namespace Operations

```bash
kubectl create namespace llm
kubectl config set-context --current --namespace=llm
kubectl get all -n llm
```

---

## Deployments

### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-server
  namespace: llm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1
          requests:
            memory: "16Gi"
            cpu: "4"
        # vLLM reads no config env vars - the server takes --model as a
        # CLI arg; $(MODEL_NAME) expands from the container's env below
        args:
        - "--model"
        - "$(MODEL_NAME)"
        env:
        - name: MODEL_NAME
          value: "Qwen/Qwen2.5-7B-Instruct"
        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-pvc
      nodeSelector:
        gpu: "true"
```

### Deploy

```bash
kubectl apply -f deployment.yaml
kubectl get deployments -n llm
kubectl rollout status deployment/vllm-server -n llm
```

---

## Services

### LoadBalancer Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
  namespace: llm
spec:
  type: LoadBalancer
  selector:
    app: vllm
  ports:
  - port: 8000
    targetPort: 8000
```

### NodePort Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
  namespace: llm
spec:
  type: NodePort
  selector:
    app: vllm
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30080
```

---

## GPU Scheduling

### NVIDIA Device Plugin

```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

### Node with GPU Label

```bash
kubectl label nodes node1 gpu=true
kubectl get nodes --show-labels
```

### GPU Resource Request

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
  requests:
    memory: "16Gi"
```

---

## Storage

### PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-pvc
  namespace: llm
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: nfs-storage
```

### Storage Class (NFS)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
provisioner: nfs-provisioner
parameters:
  archiveOnDelete: "false"
```

---

## ConfigMaps & Secrets

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-config
  namespace: llm
data:
  # envFrom maps each key 1:1 to an env var name - use env-style keys
  # (a dotted key cannot be referenced as $model.name in any shell)
  MODEL_NAME: "Qwen/Qwen2.5-7B-Instruct"
  MAX_TOKENS: "2048"
  API_PORT: "8000"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: llm
type: Opaque
data:
  openai-key: BASE64_ENCODED_KEY
  huggingface-token: BASE64_ENCODED_TOKEN
```

### Use in Pod

```yaml
envFrom:
  - configMapRef:
      name: llm-config
  - secretRef:
      name: api-keys
```

---

## Scaling

### Manual Scaling

```bash
kubectl scale deployment/vllm-server --replicas=3 -n llm
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutcaler
metadata:
  name: vllm-hpa
  namespace: llm
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-server
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Monitoring

### Port Forward

```bash
kubectl port-forward service/vllm-service 8000:8000 -n llm
```

### Logs

```bash
kubectl logs -f deployment/vllm-server -n llm
kubectl logs -f pod/vllm-server-xxx -n llm --previous
```

### Exec into Pod

```bash
kubectl exec -it pod/vllm-server-xxx -n llm -- /bin/bash
```

### Describe Pod

```bash
kubectl describe pod vllm-server-xxx -n llm
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl get pods -n llm

# Check events
kubectl describe pod pod-name -n llm

# Check logs
kubectl logs pod-name -n llm
```

### GPU Not Available

```bash
# Check GPU on node
kubectl describe node node-name | grep nvidia.com/gpu

# Check device plugin
kubectl get pods -n kube-system | grep nvidia
```

### Common Issues

| Issue | Solution |
|-------|----------|
| CrashLoopBackOff | Check logs, verify resources |
| ImagePullBackOff | Verify image name, check registry auth |
| OOMKilled | Increase memory limits |
| Insufficient nvidia.com/gpu | Verify GPU available, check device plugin |

---

## Tips

### Get YAML from Running Pod

```bash
kubectl get pod pod-name -n llm -o yaml
```

### Edit Live Deployment

```bash
kubectl edit deployment vllm-server -n llm
```

### Delete Pod (Will recreate)

```bash
kubectl delete pod pod-name -n llm
```

### Restart Deployment

```bash
kubectl rollout restart deployment/vllm-server -n llm
```

### Get All Resources

```bash
kubectl get all -n llm
kubectl get pv,pvc -n llm
kubectl get configmaps,secrets -n llm
```

---

## Cleanup

```bash
# Delete deployment
kubectl delete deployment vllm-server -n llm

# Delete service
kubectl delete service vllm-service -n llm

# Delete namespace and all resources
kubectl delete namespace llm
```

---

**Quick Reference for:**

- [Module 1300: K3s & Container Orchestration](../../phases/phase1-infra/1300-kubernetes/README.md)
- [LAB-001: Docker LLM](../labs/LAB-001-Docker-LLM.md)
- [EXP_1302: GPU Scheduler](../../../experiments/EXP_1302_GPU_SCHEDULER.md)
