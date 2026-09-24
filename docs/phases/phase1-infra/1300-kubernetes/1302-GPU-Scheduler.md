---
Document ID: 1302
Title: GPU Scheduler Configuration
Phase: 1
Module: 1300
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'kubernetes', 'k3s', 'gpu']
---

# 1302: GPU Scheduler Configuration

## Abstract
The K3s GPU scheduler enables intelligent allocation of RTX 2080 Ti resources across AI workloads. This document covers device plugin configuration, resource management, and scheduling strategies.

## GPU Resource Model

### Kubernetes Resource Model
```
Traditional CPU/Memory:    Quantitative (count/bytes)
GPU Resources:             Qualitative + Quantitative

nvidia.com/gpu: 1          → Allocate 1 GPU (exclusive)
nvidia.com/gpu.memory:     → Request specific VRAM (custom)
nvidia.com/gpu.count:      → Number of GPUs
nvidia.com/gpu.product:    → GPU model constraint
```

### Resource Allocation Types
```
Exclusive Allocation:      Pod gets entire GPU
Shared Allocation:         Multiple pods share GPU (MIG - not on 2080 Ti)
Time-Sliced:               Multiple pods, time-division
```

## NVIDIA Device Plugin

### Architecture
```
┌─────────────────────────────────────────────┐
│         Kubernetes Scheduler                │
│         (Resource: nvidia.com/gpu)          │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│         NVIDIA Device Plugin                │
│         (DaemonSet on GPU nodes)            │
│         - Discovers GPU                     │
│         - Reports resources                │
│         - Handles device assignment         │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│         Kubelet                             │
│         (Pod lifecycle)                     │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│         nvidia-smi (CUDA runtime)           │
└─────────────────────────────────────────────┘
```

### Device Plugin Deployment
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nvidia-device-plugin-daemonset
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: nvidia-device-plugin-ds
  template:
    metadata:
      labels:
        name: nvidia-device-plugin-ds
    spec:
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      containers:
      - image: nvcr.io/nvidia/k8s-device-plugin:v0.14.0
        name: nvidia-device-plugin
        args:
          - --mig-strategy=single
          - --fail-on-init-error=true
        env:
          - name: NVIDIA_VISIBLE_DEVICES
            value: "all"
        volumeMounts:
          - name: device-plugin
            mountPath: /var/lib/kubelet/device-plugins
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
      volumes:
        - name: device-plugin
          hostPath:
            path: /var/lib/kubelet/device-plugins
```

## Scheduling Strategies

### Strategy 1: Node Selector (Simple)
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: inference-pod
spec:
  nodeName: omega-worker-gpu  # Direct to GPU node
  containers:
  - name: inference
    image: vllm/vllm-openai:latest
    resources:
      limits:
        nvidia.com/gpu: 1
```

### Strategy 2: Node Selector + Tolerations
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: training-pod
spec:
  nodeSelector:
    accelerator: nvidia-2080ti  # Must have this label
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
  containers:
  - name: trainer
    image: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
    resources:
      limits:
        nvidia.com/gpu: 1
        memory: "16Gi"
```

### Strategy 3: Priority Classes
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: gpu-critical
value: 1000
globalDefault: false
description: "Critical GPU workloads"
---
apiVersion: v1
kind: Pod
metadata:
  name: priority-training
spec:
  priorityClassName: gpu-critical
  containers:
  - name: train
    image: my-training:latest
    resources:
      limits:
        nvidia.com/gpu: 1
```

## Resource Management

### GPU Memory Slicing (Experimental)
```yaml
# For RTX 2080 Ti, we can use time-slicing
# This is NOT MIG (Maxwell is too old for MIG)

apiVersion: v1
kind: ConfigMap
metadata:
  name: nvidia-plugin-config
  namespace: kube-system
data:
  config.yaml: |
    version: v1
    sharing:
      timeSlicing:
        renameByDefault: false
        failRequestsGreaterThanOne: true
        plugins:
        - name: nvidia.com/gpu
          renameByDefault: false
          failRequestsGreaterThanOne: false
          devices:
          - name: "0"
            # Split 11GB into 3 slices
            # WARNING: This is time-slicing, not real partitioning
            slices: 3
```

### Custom Resources (Advanced)
```yaml
# Extending device plugin for finer-grained control
# This requires modifying the device plugin

apiVersion: v1
kind: Pod
metadata:
  name: custom-gpu-request
spec:
  containers:
  - name: app
    image: myapp:latest
    resources:
      requests:
        nvidia.com/gpu.memory: "4096"  # Request 4GB VRAM
        nvidia.com/gpu.count: "0.25"   # Fractional GPU
      limits:
        nvidia.com/gpu.memory: "8192"
        nvidia.com/gpu.count: "0.5"
```

## Workload Isolation

### GPU Process Isolation
```bash
# Use MPS (Multi-Process Service) for better isolation
# Not true isolation, but prevents one process from killing another

# In the pod:
nvidia-cuda-mps-control -d

# Launch processes under MPS
CUDA_MPS_PIPE_DIRECTORY=/tmp/mps \
CUDA_VISIBLE_DEVICES=0 \
my_python_script.py
```

### cgroups for GPU
```bash
# Limit GPU power per pod
# Via nvidia-smi
nvidia-smi -i 0 -pl 150  # Limit to 150W

# Or via systemd service
[Service]
ExecStart=/usr/bin/my-app
CPUAccounting=true
CPUQuota=200%
MemoryAccounting=true
MemoryLimit=8G
```

## Scheduler Behavior

### Pod Scheduling Flow
```
1. Pod created with GPU request
2. Scheduler filters nodes:
   - Must have nvidia.com/gpu available
   - Must match node selectors
   - Must tolerate taints
3. Scheduler scores nodes:
   - Resource availability
   - Priority class
   - Pod affinity/anti-affinity
4. Pod assigned to node
5. Kubelet requests GPU from device plugin
6. Device plugin assigns GPU (passes device to container)
```

### Preemption
```yaml
# High priority pod can preempt low priority
apiVersion: v1
kind: Pod
metadata:
  name: high-priority-inference
spec:
  priorityClassName: gpu-critical  # Value: 1000
  containers:
  - name: inference
    image: vllm:latest
    resources:
      limits:
        nvidia.com/gpu: 1

# If GPU full, this will kill a lower priority pod
```

## Monitoring GPU Usage

### Prometheus Metrics
```yaml
# gpu-exporter deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-metrics-exporter
  namespace: monitoring
spec:
  template:
    spec:
      hostNetwork: true
      containers:
      - name: exporter
        image: mindprince/gpu-metrics-exporter:v1.0.0
        ports:
        - containerPort: 9401
        volumeMounts:
        - name: gpu
          mountPath: /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1
        - name: proc
          mountPath: /proc
      volumes:
      - name: gpu
        hostPath:
          path: /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.535
      - name: proc
        hostPath:
          path: /proc
```

### Queries
```promql
# GPU utilization
nvidia_gpu_utilization

# GPU memory used
nvidia_memory_used_bytes

# GPU temperature
nvidia_temperature_gpu

# GPU power draw
nvidia_power_draw_watts

# Pod GPU allocation
kube_pod_container_resource_requests{resource="nvidia.com/gpu"}
```

## Common Patterns

### Pattern 1: Inference Service
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-inference
spec:
  replicas: 1  # Single replica per GPU
  selector:
    matchLabels:
      app: llm-inference
  template:
    metadata:
      labels:
        app: llm-inference
    spec:
      nodeSelector:
        gpu.memory: 11GB
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        args:
          - --model
          - meta-llama/Llama-2-7b
          - --tensor-parallel-size
          - "1"
          - --gpu-memory-utilization
          - "0.9"
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "10Gi"
        volumeMounts:
          - name: models
            mountPath: /models
      volumes:
        - name: models
          persistentVolumeClaim:
            claimName: model-cache
```

### Pattern 2: Training Job
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: finetune-job
spec:
  template:
    spec:
      restartPolicy: OnFailure
      priorityClassName: gpu-training
      containers:
      - name: trainer
        image: my-trainer:latest
        command:
          - python
          - train.py
          - --model
          - llama-7b
          - --batch-size
          - "32"
          - --grad-accum
          - "4"
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
          requests:
            nvidia.com/gpu: 1
            memory: "16Gi"
        volumeMounts:
          - name: data
            mountPath: /data
          - name: output
            mountPath: /output
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: training-data
        - name: output
          persistentVolumeClaim:
            claimName: model-output
```

---

## Next Steps

- Continue with: **[1303: Storage Classes](./1303-Storage-Classes.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1202: TB3 Passthrough](../1200-virtualization/1202-TB3-UT3G-Passthrough.md)
- [1203: Nvidia Kernel Module](../1200-virtualization/1203-Nvidia-Kernel-Module.md)
- [1301: K3s Architecture](./1301-K3s-Master-Worker-Arch.md)

**Experiment Template:** `experiments/EXP_1302_GPU_SCHEDULER.md`
