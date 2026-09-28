---
Document ID: 1300-PRACTICE
Title: "1300: Kubernetes - Practice"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# 1300: Kubernetes - Practice

## Exercises

### Exercise 1: Deploy Simple Application

**Objective:** Deploy a 3-replica nginx application with resource limits and verify deployment.

**Solution:**

```yaml
# deployment.yaml - Complete deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
  labels:
    app: test
    env: practice
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx:1.25-alpine
        ports:
        - containerPort: 80
          protocol: TCP
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
```

```bash
# Deploy the application
kubectl apply -f deployment.yaml

# Verify deployment status
kubectl get deployments
kubectl get pods -l app=test

# Check pod details
kubectl describe pod -l app=test

# View logs
kubectl logs -l app=test --tail=20

# Expected output:
# NAME       READY   UP-TO-DATE   AVAILABLE   AGE
# test-app   3/3     3            3           30s

# Troubleshooting Tips:
# - If pods are pending: Check node resources with 'kubectl describe nodes'
# - If pods are crash looping: Check logs with 'kubectl logs ${POD_NAME}'
# - If image pull errors: Verify image name and registry access
```

### Exercise 2: GPU Deployment

**Objective:** Deploy an LLM serving application with GPU resource allocation.

**Solution:**

```yaml
# gpu-deployment.yaml - GPU-enabled deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-serving
  labels:
    app: llm-serving
    component: inference
spec:
  replicas: 1
  selector:
    matchLabels:
      app: llm-serving
  template:
    metadata:
      labels:
        app: llm-serving
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:v0.6.0
        # The vLLM OpenAI server is configured with CLI flags, not
        # env vars - MODEL_NAME-style env settings are silently
        # ignored. The model here is ungated; a gated model (Llama-2
        # etc.) would also need an HF token injected as HF_TOKEN.
        args:
        - --model=Qwen/Qwen2.5-7B-Instruct
        - --tensor-parallel-size=1
        - --dtype=half
        - --max-model-len=4096
        ports:
        - containerPort: 8000
          protocol: TCP
        resources:
          requests:
            memory: "16Gi"
            cpu: "4"
            nvidia.com/gpu: 1
          limits:
            memory: "32Gi"
            cpu: "8"
            nvidia.com/gpu: 1
        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache
      volumes:
      - name: model-cache
        emptyDir: {}
      # The selector needs labeled nodes first:
      #   kubectl label node <node-name> gpu=true
      nodeSelector:
        gpu: "true"
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

```bash
# Deploy GPU application
kubectl apply -f gpu-deployment.yaml

# Verify GPU allocation - "Allocated resources" is a section of node
# describe output, not pod describe, so grepping the pod never matches
kubectl get pods -l app=llm-serving
kubectl get pod -l app=llm-serving \
  -o jsonpath='{.items[0].spec.containers[0].resources}' && echo
kubectl describe node | grep -A 10 "Allocated resources" | head -15

# Check GPU utilization from within pod
kubectl exec -it deployment/llm-serving -- nvidia-smi

# Expected output should show:
# - Pod status: Running
# - GPU allocated: nvidia.com/gpu: 1
# - nvidia-smi shows GPU memory usage

# Troubleshooting Tips:
# - If pod pending: Check GPU availability with 'kubectl describe nodes'
# - If GPU not allocated: Verify node has GPU with 'kubectl get nodes -o json | grep gpu'
# - If OOMKilled: Increase memory limit or reduce model size
```

### Exercise 3: Service and Ingress

**Objective:** Expose the LLM service internally and externally.

**Solution:**

```yaml
# service.yaml - LoadBalancer service
apiVersion: v1
kind: Service
metadata:
  name: llm-service
  labels:
    app: llm-serving
spec:
  type: LoadBalancer
  selector:
    app: llm-serving
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

```yaml
# ingress.yaml - Ingress for domain-based routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - llm.example.com
    secretName: llm-tls
  rules:
  - host: llm.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: llm-service
            port:
              number: 80
```

```bash
# Apply service and ingress
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Verify service
kubectl get svc llm-service
kubectl describe svc llm-service

# Test service access. On on-prem/homelab clusters a LoadBalancer IP
# only appears with MetalLB/kube-vip installed; on kind/minikube use
# port-forward or a NodePort service instead.
SERVICE_IP=$(kubectl get svc llm-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$SERVICE_IP:80/v1/models

# Test ingress (after DNS propagation)
curl https://llm.example.com/v1/models

# Expected output:
# Service shows external IP
# curl returns JSON list of available models

# Troubleshooting Tips:
# - If external IP pending: Check cloud provider load balancer support
# - If connection refused: Verify targetPort matches container port
# - If 502 errors: Check pod readiness and service selector labels
```

### Exercise 4: ConfigMap and Secrets

**Objective:** Externalize configuration using ConfigMaps and Secrets.

**Solution:**

```yaml
# configmap.yaml - Application configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  labels:
    app: llm-serving
data:
  MODEL_NAME: "meta-llama/Llama-2-7b-hf"
  MAX_TOKENS: "2048"
  TEMPERATURE: "0.7"
  TOP_P: "0.9"
  LOG_LEVEL: "info"
  PROMPT_TEMPLATE: |
    You are a helpful AI assistant.
    User: {prompt}
    Assistant:
```

```yaml
# secret.yaml - Sensitive configuration
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
  labels:
    app: llm-serving
type: Opaque
stringData:
  HF_TOKEN: "hf_your_token_here"  # huggingface_hub reads HF_TOKEN (or HUGGING_FACE_HUB_TOKEN), not HUGGING_FACE_TOKEN
  API_KEY: "your-api-key-here"
  DATABASE_URL: "postgresql://user:pass@localhost:5432/db"
```

```yaml
# deployment-with-config.yaml - Deployment using ConfigMap and Secret
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-serving-configured
spec:
  replicas: 1
  selector:
    matchLabels:
      app: llm-serving
  template:
    metadata:
      labels:
        app: llm-serving
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:v0.6.0
        # envFrom injects every key of both resources as environment
        # variables - no per-key env entries are needed on top of it
        # (the old MODEL_NAME / HUGGING_FACE_TOKEN entries only
        # duplicated what envFrom already provided).
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secret
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
          readOnly: true
      volumes:
      - name: config-volume
        configMap:
          name: app-config
          items:
          - key: PROMPT_TEMPLATE
            path: prompt.txt
```

```bash
# Apply configurations
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment-with-config.yaml

# Verify configurations
kubectl get configmap app-config -o yaml
kubectl get secret app-secret -o yaml

# Test configuration injection
kubectl exec deployment/llm-serving-configured -- env | grep MODEL_NAME
kubectl exec deployment/llm-serving-configured -- cat /etc/config/prompt.txt

# Expected output:
# ConfigMap shows all configuration data
# Secret shows base64-encoded values (or use -o jsonpath for clear text)
# Pod environment variables contain ConfigMap and Secret values

# Troubleshooting Tips:
# - If env vars not set: Check valueFrom field references and resource names
# - If secret fails: Verify base64 encoding with 'echo -n value | base64'
# - If volume mount fails: Check path and readOnly settings
```

### Exercise 5: Scaling and Rollout

**Objective:** Scale deployments and perform rolling updates with rollback capability.

**Solution:**

```bash
# Scaling operations

# Manual scaling to 5 replicas (once the HPA below exists it overrides
# manual scale - delete it first: kubectl delete hpa test-app)
kubectl scale deployment test-app --replicas=5

# Verify scaling
kubectl get deployments test-app
kubectl get pods -l app=test

# Autoscaling based on CPU (requires metrics server)
kubectl autoscale deployment test-app --min=2 --max=10 --cpu-percent=70

# Check HPA status
kubectl get hpa

# Update deployment with a NEW tag - setting the same tag the
# manifest already has changes nothing and no rollout starts
# (--record is deprecated and ignored; revision history is tracked
# automatically)
kubectl set image deployment/test-app nginx=nginx:1.27-alpine

# Watch rollout status in real-time
kubectl rollout status deployment/test-app --watch

# View rollout history
kubectl rollout history deployment/test-app

# Expected output:
# NAME       READY   UP-TO-DATE   AVAILABLE   AGE
# test-app   5/5     5            5           2m

# Rollout strategies and rollback

# Pause rollout (for manual verification)
kubectl rollout pause deployment/test-app

# Verify new pods before continuing
kubectl get pods

# Resume rollout
kubectl rollout resume deployment/test-app

# Rollback to previous version
kubectl rollout undo deployment/test-app

# Rollback to specific revision
kubectl rollout undo deployment/test-app --to-revision=2

# Expected output:
# Shows rollout history with revisions
# Undo command restores previous configuration

# Troubleshooting Tips:
# - If rollout stuck: Check pod status with 'kubectl describe pod'
# - If scaling fails: Verify resource requests/limits match node capacity
# - If rollback needed: Use 'kubectl rollout history' to find revision

# Complete workflow example
echo "=== Scaling and Rollout Workflow ==="

# 1. Initial deployment
kubectl apply -f deployment.yaml
echo "✓ Initial deployment created"

# 2. Scale up
kubectl scale deployment test-app --replicas=5
kubectl wait --for=condition=available deployment/test-app --timeout=60s
echo "✓ Scaled to 5 replicas"

# 3. Update image (a tag different from the manifest, so a rollout starts)
kubectl set image deployment/test-app nginx=nginx:1.27-alpine
echo "✓ Image update initiated"

# 4. Monitor rollout
kubectl rollout status deployment/test-app --timeout=120s
echo "✓ Rollout completed"

# 5. Check history
kubectl rollout history deployment/test-app
echo "✓ History displayed"

# 6. Test rollback if needed
# kubectl rollout undo deployment/test-app
# echo "✓ Rollback completed"

echo "=== Workflow Complete ==="
```

---

## Summary

This practice guide covers:

1. **Deploying Applications:** Creating deployments with proper resource management and health checks
2. **GPU Deployments:** Allocating and managing GPU resources for ML workloads
3. **Service Exposure:** Using Services and Ingress for internal and external access
4. **Configuration Management:** Externalizing configuration with ConfigMaps and Secrets
5. **Scaling and Updates:** Manual scaling, autoscaling, and rolling updates with rollback

**Expected Learning Outcomes:**
- Deploy and manage containerized applications in Kubernetes
- Handle GPU resources for ML/AI workloads
- Implement proper networking and exposure strategies
- Separate configuration from application code
- Perform safe updates and scaling operations
