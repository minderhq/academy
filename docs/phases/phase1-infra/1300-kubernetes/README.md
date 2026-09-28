---
Document ID: 1300-KUBERNETES-README
Title: "1300: Kubernetes for LLM Deployment"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Beginner
---

# 1300: Kubernetes for LLM Deployment

## Module Overview

This module covers Kubernetes deployment patterns for running LLM inference and training workloads at scale. You'll learn how to deploy lightweight Kubernetes with K3s, configure GPU scheduling, set up persistent storage for model weights, and implement auto-scaling for production LLM services.

## Why Kubernetes for LLMs

### 1. Scalability: Auto-Scale Based on Demand

**Manual Scaling Problem:**
```text
Without Kubernetes:
├── Monitor load manually ❌
├── SSH into servers to add replicas ❌
├── Copy models to new servers ❌
├── Configure load balancer ❌
└── Takes 30-60 minutes to scale ❌

With Kubernetes:
├── Define autoscaling policy
├── HPA (Horizontal Pod Autoscaler) watches metrics
├── Automatically adds pods when load increases
├── Load balancing built-in
└── Scaling in 30-60 seconds ✅
```

**Real-World Example:**
```yaml
Scenario: Sudden traffic spike

Manual approach:
  09:00: Traffic increases to 10x normal
  09:05: Alert fires, engineer woken up
  09:15: Engineer SSHs into servers
  09:30: New servers provisioned (30 min total)
  09:45: Models downloaded and deployed
  Result: 45 minutes of downtime ❌

Kubernetes approach:
  09:00: Traffic increases to 10x normal
  09:00:30: HPA detects high CPU/GPU utilization
  09:00:45: New pods automatically created
  09:01:00: New pods serving traffic
  Result: 1 minute to handle spike ✅
```

### 2. High Availability: Built-in Redundancy

**Without Kubernetes:**
```text
Server dies:
├── Service goes down ❌
├── Users see errors ❌
├── Manual intervention required ❌
└── Recovery time: 30+ minutes ❌
```

**With Kubernetes:**
```text
Node dies:
├── Kubernetes detects failure (<5 seconds)
├── Reschedules pods to healthy nodes
├── Service continues automatically
└── Recovery time: <30 seconds ✅

Example deployment:
  - 3 nodes, each with 2 GPUs
  - 6 replicas of LLM service (1 per GPU)
  - 1 node fails → 4 pods remain
  - Kubernetes reschedules 2 pods
  - 100% capacity restored automatically
```

### 3. Resource Management: Efficient GPU Allocation

**Problem: GPUs are Expensive**
```text
Scenario: 4 GPUs, 3 models

Without Kubernetes (static allocation):
├── GPU 0: Llama-3-70B (underutilized at 20%)
├── GPU 1: Llama-3-70B (underutilized at 20%)
├── GPU 2: Whisper (underutilized at 10%)
├── GPU 3: Stable Diffusion (underutilized at 15%)
└── Total utilization: 16% ❌ (waste of $30k hardware!)
```

**With Kubernetes (dynamic allocation):**
```text
Kubernetes monitors GPU utilization
Automatically consolidates workloads:
├── GPU 0: Llama-3-70B + Whisper (50% utilization)
├── GPU 1: Llama-3-70B + Stable Diffusion (60%)
├── GPU 2: Available for burst workloads
├── GPU 3: Available for experiments
└── Total utilization: 55% ✅ (3x efficiency!)
```

### 4. Multi-Model Serving: Run Multiple Models Simultaneously

**Architecture:**
```text
                    Internet
                       │
                  ┌────▼────┐
                  │ Ingress │
                  └────┬────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │ Llama-3 │   │ Whisper │   │ Stable  │
   │  Service│   │ Service │   │ Diff.   │
   │ (70B)   │   │ (Large) │   │ Service │
   └────┬────┘   └────┬────┘   └────┬────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
              ┌────────▼────────┐
              │  GPU Pool (4x)  │
              │  Dynamic alloc  │
              └─────────────────┘
```

**Benefits:**
- **Isolation:** Each model in separate container
- **Versioning:** Run A/B tests of different model versions
- **Resource quotas:** Prevent one model from starving others
- **Independent scaling:** Scale each model based on demand

## Kubernetes Architecture for LLMs

```text
┌──────────────────────────────────────────────────────────────┐
│                         Load Balancer                        │
│                  (Cloud: ALB / On-prem: Nginx)               │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                      Kubernetes Cluster                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Control Plane                     │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │    │
│  │  │ API     │  │Scheduler│  │Controller│            │    │
│  │  │ Server  │  │         │  │ Manager  │             │    │
│  │  └────┬────┘  └────┬────┘  └────┬────┘             │    │
│  └───────┼────────────┼────────────┼───────────────────┘    │
│          │            │            │                         │
│  ┌───────┴────────────┴────────────┴─────────────────────┐   │
│  │                     Worker Nodes                      │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐      │   │
│  │  │   Node 1   │  │   Node 2   │  │   Node 3   │      │   │
│  │  │  (Master)  │  │  (Worker)  │  │  (Worker)  │      │   │
│  │  │            │  │            │  │            │      │   │
│  │  │ ┌────────┐ │  │ ┌────────┐ │  │ ┌────────┐ │      │   │
│  │  │ │Kubelet │ │  │ │Kubelet │ │  │ │Kubelet │ │      │   │
│  │  │ └───┬────┘ │  │ └───┬────┘ │  │ └───┬────┘ │      │   │
│  │  │     │      │  │     │      │  │     │      │      │   │
│  │  │ ┌───▼───┐  │  │ ┌───▼───┐  │  │ ┌───▼───┐  │      │   │
│  │  │ │ Pod:  │  │  │ │ Pod:  │  │  │ │ Pod:  │  │      │   │
│  │  │ │Llama  │  │  │ │Whisper│  │  │ │Stable │  │      │   │
│  │  │ │-70B   │  │  │ │Large  │  │  │ │Diff.  │  │      │   │
│  │  │ └───┬───┘  │  │ └───┬───┘  │  │ └───┬───┘  │      │   │
│  │  │     │      │  │     │      │  │     │      │      │   │
│  │  │ ┌───▼───┐  │  │ ┌───▼───┐  │  │ ┌───▼───┐  │      │   │
│  │  │ │GPU 0  │  │  │ │GPU 1  │  │  │ │GPU 2  │  │      │   │
│  │  │ │GPU 1  │  │  │ │GPU 3  │  │  │ │GPU 4  │  │      │   │
│  │  │ └───────┘  │  │ └───────┘  │  │ └───────┘  │      │   │
│  │  └────────────┘  └────────────┘  └────────────┘      │   │
│  │                                                       │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │            Storage Classes                    │   │   │
│  │  │  ┌────────┐  ┌────────┐  ┌────────┐          │   │   │
│  │  │  │ Local  │  │  NFS   │  │  Ceph  │          │   │   │
│  │  │  │ Path   │  │        │  │  RBD   │          │   │   │
│  │  │  └────────┘  └────────┘  └────────┘          │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Kubernetes Distributions for LLMs

### K3s (Recommended for Edge/Home Labs)

**Pros:**
```text
✅ Lightweight: <500MB binary
✅ Single binary: Easy installation
✅ ARM64 support: Run on Raspberry Pi
✅ Perfect for edge deployment
✅ Minimal resource overhead
✅ Quick setup: <5 minutes
```

**Cons:**
```yaml
❌ Not for large clusters (>50 nodes)
❌ Limited enterprise features
❌ Basic load balancing
```

**Best For:**
- Home labs
- Edge inference
- Development environments
- Single-node clusters

**Example Installation:**
```bash
# Install K3s in <30 seconds
curl -sfL https://get.k3s.io | sh -

# Verify installation
kubectl get nodes

# Enable GPU support
# Edit /etc/rancher/k3s/config.yaml
echo "kubelet-arg=config=--feature-gates=DevicePlugins=false" >> \
  /etc/rancher/k3s/config.yaml

systemctl restart k3s
```

### kubeadm + Kubelet (Standard Kubernetes)

**Pros:**
```yaml
✅ Full Kubernetes feature set
✅ Upstream compatibility
✅ Flexible customization
✅ Production-ready
✅ Large community
```

**Cons:**
```yaml
❌ Complex setup (30-60 minutes)
❌ More resource overhead
❌ Manual configuration required
```

**Best For:**
- Production clusters
- Multi-node deployments
- Enterprises with dedicated ops teams

### EKS / GKE / AKS (Managed Services)

**Pros:**
```yaml
✅ No control plane management
✅ Auto-upgrades
✅ Integrated cloud services
✅ Enterprise support
✅ Best for production (cloud)
```

**Cons:**
```yaml
❌ Expensive (control plane costs)
❌ Vendor lock-in
❌ GPU add-on costs
❌ Less control
```

**Best For:**
- Cloud-native deployments
- Enterprises with cloud budget
- Teams wanting managed operations

## Quick Start Guide

### Step 1: Choose Your Distribution

**For Learning/Home Lab:**
```yaml
Distribution: K3s
Hardware: 1 server
GPUs: 1-2
RAM: 16 GB+
Cost: Free
```

**For Production (On-Premise):**
```yaml
Distribution: kubeadm
Hardware: 3+ servers
GPUs: 6+ (2 per node)
RAM: 64 GB+ per node
Cost: $50k-200k (hardware)
```

**For Production (Cloud):**
```yaml
Distribution: EKS/GKE/AKS
Hardware: Managed
GPUs: 3+ nodes with GPU
RAM: Configurable
Cost: $5k-20k/month
```

### Step 2: Install K3s (Learning/Edge)

**Single Node Setup:**
```bash
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Check status
systemctl status k3s

# Get kubeconfig
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Verify
kubectl get nodes
# NAME    STATUS   ROLES                  AGE   VERSION
# node1   Ready    control-plane,master   10s   v1.28.5+k3s1
```

**Multi-Node Setup:**
```bash
# On master node
curl -sfL https://get.k3s.io | K3S_TOKEN=secret sh -s - --server

# Get node token
cat /var/lib/rancher/k3s/server/node-token

# On worker nodes
curl -sfL https://get.k3s.io | K3S_TOKEN=xxx K3S_URL=https://master:6443 sh -

# Verify on master
kubectl get nodes
```

### Step 3: Enable GPU Support

**Install NVIDIA Device Plugin:**
```bash
# Add NVIDIA Helm repo
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install device plugin
kubectl create -f https://raw.githubusercontent.com/\
  NVIDIA/k8s-device-plugin/v0.14.0/deployments/\
  static/nvidia-device-plugin.yml

# Verify GPUs
kubectl get nodes -o json | grep nvidia.com/gpu
```

**Test GPU Pod:**
```yaml
# gpu-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-test
spec:
  containers:
  - name: gpu-test
    image: nvidia/cuda:12.1.0-base-ubuntu22.04
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 1
```

```bash
# Deploy test pod
kubectl apply -f gpu-test-pod.yaml

# Check logs (should see nvidia-smi output)
kubectl logs gpu-test
```

### Step 4: Deploy LLM Inference Service

**Deployment YAML:**
```yaml
# llama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llama-inference
spec:
  replicas: 2  # 2 replicas = 2 GPUs
  selector:
    matchLabels:
      app: llama-inference
  template:
    metadata:
      labels:
        app: llama-inference
    spec:
      containers:
      - name: inference
        image: your-registry/llama-inference:v1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            nvidia.com/gpu: 1
            memory: "16Gi"
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
        env:
        - name: MODEL_NAME
          value: "meta-llama/Llama-3-70B"
        - name: QUANTIZATION
          value: "4bit"
        volumeMounts:
        - name: model-cache
          mountPath: /models
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-storage-pvc
```

**Service YAML:**
```yaml
# llama-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: llama-inference
spec:
  selector:
    app: llama-inference
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Deploy:**
```bash
# Create PVC for model storage
kubectl apply -f model-pvc.yaml

# Deploy inference service
kubectl apply -f llama-deployment.yaml
kubectl apply -f llama-service.yaml

# Check status
kubectl get pods
kubectl get svc

# Test
curl -X POST http://${SERVICE_IP}/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
```

### Step 5: Configure Auto-Scaling

**Horizontal Pod Autoscaler:**
```yaml
# llama-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llama-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llama-inference
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: nvidia.com/gpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

**Deploy HPA:**
```bash
kubectl apply -f llama-hpa.yaml

# Watch HPA status
kubectl get hpa -w

# Simulate load
# HPA will automatically add replicas
kubectl get pods
```

## Common Kubernetes Pitfalls

### ❌ Pitfall 1: GPU Resource Not Requested

**Problem:**
```yaml
Symptoms:
- Pod pending with "Insufficient nvidia.com/gpu"
- Scheduler can't place pod
- GPUs appear available

Root Cause:
- Forgot to request GPU in resources
- Or request doesn't match limit
```

**Solution:**
```yaml
# Wrong ❌
resources:
  limits:
    nvidia.com/gpu: 1

# Correct ✅
resources:
  requests:
    nvidia.com/gpu: 1
  limits:
    nvidia.com/gpu: 1

# Note: For GPUs, requests must equal limits
```

### ❌ Pitfall 2: Model Not in Image

**Problem:**
```yaml
Symptoms:
- Pod takes forever to start
- High bandwidth usage on deployment
- Model downloaded from internet each time

Root Cause:
- Model not baked into container image
- Pod downloads from HuggingFace each start
```

**Solution:**
```dockerfile
# Method 1: Bake into image ✅
FROM python:3.11-slim

# Download during build
RUN python -c "from transformers import AutoModel; \
  AutoModel.from_pretrained('meta-llama/Llama-3-70B')"
```

Method 2: Use PVC:

```yaml
volumes:
- name: model-cache
  persistentVolumeClaim:
    claimName: model-storage-pvc

# Init container to download model
initContainers:
- name: download-model
  image: python:3.11-slim
  command: ["python", "-c", "download model"]
  volumeMounts:
  - name: model-cache
    mountPath: /models
```

### ❌ Pitfall 3: Memory Limits Too Low

**Problem:**
```yaml
Symptoms:
- Pod OOMKilled
- Inference fails mid-generation
- Random crashes

Root Cause:
- Model size > memory limit
- Forgot about KV cache memory
- Activations not accounted for
```

**Solution:**
```yaml
# Calculate memory requirements:
# Model size (4-bit 70B) = ~40 GB
# KV cache (max 2048 tokens) = ~8 GB
# Activations = ~4 GB
# Overhead = ~4 GB
# Total = ~56 GB

# Set appropriate limits ✅
resources:
  requests:
    nvidia.com/gpu: 1
    memory: "48Gi"   # GPU memory
  limits:
    nvidia.com/gpu: 1
    memory: "64Gi"   # Leave headroom
```

### ❌ Pitfall 4: Wrong Storage Class

**Problem:**
```yaml
Symptoms:
- Slow inference (waiting for model loading)
- Pods timeout on PVC mount
- Poor performance

Root Cause:
- Using network storage for models
- Not using local SSD storage
```

**Solution:**
```yaml
# Use local-path for models ✅
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-storage-pvc
spec:
  storageClassName: local-path  # Fast local storage
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 500Gi

# Or use NVMe for performance ✅
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nvme-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

## Performance Optimization

### 1. GPU Node Affinity

**Pin pods to GPU nodes:**
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: nvidia.com/gpu.product
          operator: In
          values:
          - NVIDIA_A100-SXM4-40GB
```

### 2. Pod Priority

**Ensure critical pods get GPU first:**
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-inference
value: 1000
globalDefault: false
description: "High priority for production inference"
```

```yaml
# Apply to critical pods
priorityClassName: high-priority-inference
```

### 3. Request/Limit Optimization

**Best practices for LLMs:**
```yaml
resources:
  # For GPU: requests must equal limits
  nvidia.com/gpu: "1"

  # For CPU: request low, limit high
  cpu: "2"      # Minimum
  cpu: "8"      # Maximum (burst)

  # For memory: request accurately
  memory: "48Gi"   # Expected usage
  memory: "64Gi"   # Maximum allowed
```

### 4. Batch Processing with Jobs

**For training/batch inference:**
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-inference
spec:
  completions: 100  # 100 batches
  parallelism: 4    # Process 4 at a time
  template:
    spec:
      containers:
      - name: batch
        image: your-registry/batch-inference
        resources:
          limits:
            nvidia.com/gpu: 1
      restartPolicy: OnFailure
```

## Troubleshooting Guide

### Problem 1: Pod Pending - Insufficient GPU

**Diagnosis:**
```bash
# Check pod status
kubectl describe pod ${POD_NAME}

# Look for:
# Events: 0/4 nodes are available: 4 Insufficient nvidia.com/gpu
```

**Solutions:**
1. **Check GPU availability**
   ```bash
   kubectl describe nodes | grep nvidia.com/gpu
   ```

2. **Add more GPU nodes**
3. **Delete unused pods**
4. **Check resource requests match limits**

### Problem 2: Pod CrashLoopBackOff

**Diagnosis:**
```bash
# Check logs
kubectl logs ${POD_NAME}

# Common errors:
# - "CUDA out of memory"
# - "Model not found"
# - "Permission denied"
```

**Solutions:**
1. **Increase memory limits**
2. **Check model path in PVC**
3. **Verify PVC permissions**

### Problem 3: Slow Inference

**Diagnosis:**
```bash
# Check pod placement
kubectl get pods -o wide

# Check node resources
kubectl top nodes
kubectl top pods
```

**Solutions:**
1. **Use local storage for models**
2. **Check for network bottlenecks**
3. **Verify GPU utilization**
4. **Consider model quantization**

## Real-World Examples

### Example 1: Home Lab LLM Server

```yaml
Setup:
  Hardware: 1x x86_64 host, 2x 24GB GPUs (e.g., RTX 4090)
  Kubernetes: K3s single-node
  Models: Llama-3-70B, Whisper Large

Configuration:
  Deployment: 2 replicas (1 per GPU)
  Storage: 1 TB NVMe for models
  Autoscaling: Manual (2 replicas max)
  Load Balancing: Traefik ingress

Results:
  - Inference: 25 tokens/sec
  - Concurrent users: 5-10
  - Uptime: 99%
  - Cost: $6,000 (hardware)

Benefits of K3s:
  - Single binary installation
  - Automatic restart on failure
  - Easy model updates (rolling deploy)
  - Resource isolation between models
```

### Example 2: Startup Production

```yaml
Setup:
  Hardware: 6 nodes (4 GPU each = 24 A100s)
  Kubernetes: kubeadm cluster
  Models: Custom 70B fine-tunes

Configuration:
  - 3 models deployed simultaneously
  - 12 replicas per model (4 per node type)
  - HPA: Min 12, Max 24 replicas
  - Storage: Ceph RBD (distributed)
  - Ingress: NGINX + Cert-Manager

Results:
  - Inference: 150 tokens/sec
  - Concurrent users: 1000+
  - Autoscaling: 30 seconds to scale
  - Uptime: 99.9%
  - Cost: $200,000 (hardware)

Benefits of Kubernetes:
  - Automatic scaling based on load
  - Zero-downtime updates
  - GPU utilization: 70% (vs 20% static)
  - Multi-region deployment ready
```

## Learning Path

1. **[1301: K3s Master-Worker Architecture](./1301-K3s-Master-Worker-Arch.md)** - Lightweight Kubernetes setup
2. **[1302: GPU Scheduler](./1302-GPU-Scheduler.md)** - GPU resource scheduling
3. **[1303: Storage Classes](./1303-Storage-Classes.md)** - Persistent storage for models

## Prerequisites

Before starting this module, ensure you understand:

### Basic Knowledge
- **Docker & Containers:** Images, containers, Dockerfile basics
- **Kubernetes Fundamentals:** Pods, Services, Deployments, Namespaces
- **YAML Configuration:** Writing and reading YAML files
- **Linux Command Line:** bash, file operations, permissions

### Hardware Requirements
- **CPU:** 4+ cores (8+ recommended for multi-node)
- **RAM:** 16 GB minimum (32 GB+ for production)
- **GPU:** At least one NVIDIA GPU for testing
- **Storage:** 100 GB SSD (500 GB+ for models)

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

Validate your knowledge:

- **[assessment/QUIZ.md](./assessment/QUIZ.md)** - Test your understanding (20 questions, 80% to pass)
- **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** - Hands-on Kubernetes exercises

## Key Takeaways

After completing this module, you will be able to:

✅ **Choose the right Kubernetes distribution**
   - K3s for edge/home labs
   - kubeadm for production on-premise
   - EKS/GKE/AKS for cloud deployments

✅ **Deploy GPU-enabled Kubernetes clusters**
   - Install K3s with GPU support
   - Configure NVIDIA device plugin
   - Verify GPU allocation

✅ **Deploy LLM inference services**
   - Create deployments with GPU requests
   - Configure services and ingress
   - Implement rolling updates

✅ **Implement auto-scaling**
   - Horizontal Pod Autoscaler (HPA)
   - GPU-based metrics
   - Scaling policies

✅ **Manage storage for models**
   - Persistent Volume Claims
   - Storage classes (local, NFS, Ceph)
   - Model caching strategies

✅ **Troubleshoot Kubernetes issues**
   - Pod scheduling problems
   - GPU allocation failures
   - Performance bottlenecks

## Additional Resources

### Tools & Utilities

```bash
# Kubernetes Management
kubectl            # Command-line tool for K8s
k9s                # Terminal UI for K8s
helm               # Package manager
kubectx/kubens     # Context/namespace switcher

# GPU Management
nvidia-smi         # GPU monitoring
dcgm-exporter      # GPU metrics for Prometheus
kubectl-gpu        # GPU plugin for kubectl

# Testing
curl               # Test API endpoints
ab/hey/wrk         # Load testing tools
```

### Further Reading

**Documentation:**
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [K3s Documentation](https://docs.k3s.io/)
- [NVIDIA Kubernetes Device Plugin](https://github.com/NVIDIA/k8s-device-plugin)

**Books:**
- "Kubernetes in Action" by Marko Luksa
- "The Kubernetes Book" by Nigel Poulton
- "Cloud Native DevOps with Kubernetes" by Justin Garrison

**Online Courses:**
- [Kubernetes for Beginners](https://www.youtube.com/watch?v=X48VuDVwjeo)
- [Certified Kubernetes Administrator (CKA)](https://www.udemy.com/course/certified-kubernetes-administrator-with-practice-tests/)

### Community Resources

**Forums:**
- [Kubernetes Slack](https://slack.k8s.io/)
- [Kubernetes Discussion](https://discuss.kubernetes.io/)
- [r/kubernetes on Reddit](https://www.reddit.com/r/kubernetes/)

**GPU-Specific:**
- [NVIDIA Cloud Native](https://github.com/NVIDIA/cloud-native)
- [GPU Operator](https://github.com/NVIDIA/gpu-operator)

## Module Completion Checklist

```text
Understanding:
  - [ ] I can explain Kubernetes architecture
  - [ ] I understand pods, services, deployments
  - [ ] I know how GPU passthrough works in K8s
  - [ ] I can design a K8s deployment for LLMs

Practical Skills:
  - [ ] I have installed K3s or kubeadm
  - [ ] I have configured NVIDIA device plugin
  - [ ] I have deployed an LLM inference service
  - [ ] I have configured HPA for auto-scaling
  - [ ] I have set up PVCs for model storage

Production Ready:
  - [ ] I have implemented monitoring
  - [ ] I have configured ingress/SSL
  - [ ] I have tested rolling updates
  - [ ] I have documented my deployment
```

## Glossary

| Term | Definition |
|------|------------|
| **Pod** | Smallest deployable unit in Kubernetes (one or more containers) |
| **Deployment** | Manages replica sets and rolling updates |
| **Service** | Network endpoint for pods (stable IP/DNS) |
| **Ingress** | HTTP/S routing to services |
| **HPA** | Horizontal Pod Autoscaler - scales replicas based on metrics |
| **PVC** | Persistent Volume Claim - request for storage |
| **StorageClass** | Defines storage types (local, NFS, etc.) |
| **Node** | Physical or virtual machine in cluster |
| **Control Plane** | Kubernetes master components (API, scheduler, controller) |
| **Kubelet** | Agent on each node that manages pods |
| **K3s** | Lightweight Kubernetes distribution |
| **Helm** | Kubernetes package manager (like apt for K8s) |
| **Namespace** | Logical cluster within a physical cluster |

---

**Module Duration:** 8-10 hours
**Difficulty:** Intermediate-Advanced

**Ready to proceed?** Continue to [1301: K3s Master-Worker Architecture](./1301-K3s-Master-Worker-Arch.md)
