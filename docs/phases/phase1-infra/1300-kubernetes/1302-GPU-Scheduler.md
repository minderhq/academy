---
Document ID: 1302
Title: "1302: GPU Scheduler Configuration"
Phase: 1
Module: 1300
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'kubernetes', 'k3s', 'gpu']
---

# 1302: GPU Scheduler Configuration

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [GPU Resource Model](#gpu-resource-model)
- [NVIDIA Device Plugin](#nvidia-device-plugin)
- [Scheduling Strategies](#scheduling-strategies)
- [Resource Management](#resource-management)
- [Workload Isolation](#workload-isolation)
- [Scheduler Behavior](#scheduler-behavior)
- [Monitoring GPU Usage](#monitoring-gpu-usage)
- [Common Patterns](#common-patterns)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Map the extended-resource model - why nvidia.com/gpu is integer-only and VRAM placement uses labels instead
- Deploy the NVIDIA device plugin DaemonSet with MIG-off args and time-slicing replicas for consumer cards
- Schedule GPU pods with node selectors, taint tolerations, and priority classes that enable preemption
- Configure time-slicing (renameByDefault, failRequestsGreaterThanOne) and pin pods to VRAM classes with FGD labels
- Export GPU telemetry with dcgm-exporter and read utilization, framebuffer, and power metrics in Prometheus
- Isolate GPU workloads with MPS plus cgroup-level CPU/memory caps alongside the GPU-global power limit

---

## Abstract
The K3s GPU scheduler enables intelligent allocation of 11GB-class GPU resources across AI workloads. This document covers device plugin configuration, resource management, and scheduling strategies.

## GPU Resource Model

### Kubernetes Resource Model
```text
Traditional CPU/Memory:    Quantitative (count/bytes)
GPU Resources:             Qualitative + Quantitative

Schedulable resource (integer values only, in limits):
nvidia.com/gpu: 1          → Allocate 1 GPU (exclusive)
nvidia.com/gpu.shared: 1   → 1 time-sliced replica (renameByDefault: true)

NOT resources - GPU Feature Discovery NODE LABELS (nodeSelector only):
nvidia.com/gpu.memory:     → Card VRAM in MiB, e.g. 11264
nvidia.com/gpu.product:    → GPU model, e.g. NVIDIA-GeForce-RTX-2080-Ti
```

### Resource Allocation Types
```text
Exclusive Allocation:      Pod gets entire GPU
Shared Allocation:         Multiple pods share GPU (MIG - not on 11GB-class GPU)
Time-Sliced:               Multiple pods, time-division
```

## NVIDIA Device Plugin

### Architecture
```text
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
│         NVML / NVIDIA driver (nvidia-smi)  │
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
      - image: nvcr.io/nvidia/k8s-device-plugin:v0.20.1
        name: nvidia-device-plugin
        args:
          # GeForce-class cards have no MIG; "single"/"mixed" are for
          # MIG-capable data-center GPUs (A100/H100) and would advertise
          # no devices here:
          - --mig-strategy=none
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
  nodeName: academy-worker-gpu  # Direct to GPU node
  containers:
  - name: inference
    image: vllm/vllm-openai:v0.30.0
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
    accelerator: nvidia  # The label 1301 puts on the GPU node
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
  containers:
  - name: trainer
    # CUDA 13 runtime image - pairs with the 580 driver branch (see 1203);
    # a container's CUDA must not exceed the max CUDA the host driver supports
    image: pytorch/pytorch:2.9.0-cuda13.0-cudnn9-runtime
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
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: gpu-training
value: 100
globalDefault: false
description: "Batch GPU training - preemptable by gpu-critical"
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
# Time-slicing: the plugin advertises N replicas of the SAME GPU and
# pods take turns on the hardware. This is NOT MIG - MIG requires
# Ampere-or-newer data-center GPUs (A100/A30/H100); consumer cards
# do not support it at all.

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
        resources:
        - name: nvidia.com/gpu
          replicas: 3
```

Feed the config to the plugin by mounting this ConfigMap into the
DaemonSet pod and adding `--config-file=/etc/nvidia-plugin-config/
config.yaml` to the plugin args. With `replicas: 3` the node now
advertises `nvidia.com/gpu: 3` - three pods can share one physical
GPU, each getting at most ~1/3 of its compute time and a share of
the same 11GB VRAM.

### GPU-Aware Placement with Labels
```yaml
# There is no "request 4GB VRAM" knob: extended resources must be
# integer quantities advertised by a device plugin, and the plugin
# publishes only nvidia.com/gpu (fractional values are rejected).
# VRAM-based placement is done with LABELS instead - the hand-made
# ones 1301 applied (accelerator, gpu.memory) or the ones GPU
# Feature Discovery publishes (nvidia.com/gpu.product, MiB memory):
apiVersion: v1
kind: Pod
metadata:
  name: vram-pinned-inference
spec:
  nodeSelector:
    accelerator: nvidia
    gpu.memory: 11GB            # placement label - NOT a resource request
  containers:
  - name: app
    image: myapp:latest
    resources:
      limits:
        nvidia.com/gpu: 1       # the real schedulable GPU resource
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
# GPU power is a GPU-level knob, not a pod-level one: -pl caps the
# whole card for every workload on it (needs root; resets on reboot
# unless persisted).
nvidia-smi -i 0 -pl 150  # Limit the card to 150W (GPU-global)

# CPU/memory of the app itself can be capped per-service:
# [Service]
# ExecStart=/usr/bin/my-app
# CPUAccounting=true
# CPUQuota=200%
# MemoryAccounting=true
# MemoryMax=8G
```

## Scheduler Behavior

### Pod Scheduling Flow
```text
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
    image: vllm/vllm-openai:v0.30.0
    resources:
      limits:
        nvidia.com/gpu: 1

# If GPU full, this will kill a lower priority pod
```

## Monitoring GPU Usage

### Prometheus Metrics
```bash
# NVIDIA's canonical GPU metrics exporter is dcgm-exporter (the
# mindprince exporter this lesson once used is gone from GitHub and
# Docker Hub). The chart deploys a DaemonSet on GPU nodes and wires
# the ServiceMonitor for Prometheus Operator:
helm repo add gpu-helm-charts https://nvidia.github.io/dcgm-exporter/helm-charts
helm repo update
helm install dcgm-exporter gpu-helm-charts/dcgm-exporter \
  --namespace monitoring --create-namespace
```

### Queries
```promql
# GPU utilization (%)
DCGM_FI_DEV_GPU_UTIL

# GPU framebuffer memory used (MiB)
DCGM_FI_DEV_FB_USED

# GPU temperature (C)
DCGM_FI_DEV_GPU_TEMP

# GPU power draw (W)
DCGM_FI_DEV_POWER_USAGE

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
        image: vllm/vllm-openai:v0.30.0
        args:
          # ~6GB fp16 weights - fits the 11GB card at 0.9 utilization
          # (a 7B fp16 model needs ~14GB and would OOM on one card):
          - --model
          - Qwen/Qwen3-4B
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

## Summary

The K3s GPU scheduler turns an 11GB-class card into a schedulable cluster resource: the NVIDIA device plugin advertises nvidia.com/gpu as an integer, exclusive resource, and the time-sliced shared variant serves many pods one GPU in rotation. This lesson covered the resource model, device plugin configuration, scheduling strategies, workload isolation, scheduler behavior, and GPU usage monitoring. The common-patterns section is the practice: exclusive allocation for training runs, shared time-slicing for inference fleets, and the monitoring that shows which one your workloads actually need.

## References

### Related Minder Academy Documents

- [1301: K3s Master-Worker Architecture](1301-K3s-Master-Worker-Arch.md)
- [1303: Storage Classes for Dynamic Provisioning](1303-Storage-Classes.md)

---

## Next Steps

- Continue with: **[1303: Storage Classes for Dynamic Provisioning](./1303-Storage-Classes.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**

- [1202: GPU Passthrough (IOMMU/VFIO)](../1200-virtualization/1202-TB3-UT3G-Passthrough.md)
- [1203: NVIDIA Kernel Module Management](../1200-virtualization/1203-Nvidia-Kernel-Module.md)
- [1301: K3s Master-Worker Architecture](./1301-K3s-Master-Worker-Arch.md)

**Experiment Template:** [EXP_1302: GPU Scheduler](../../../../experiments/EXP_1302_GPU_SCHEDULER.md)
