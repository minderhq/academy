# Phase 1: Infrastructure Fabric [1000]

## Table of Contents

- [Overview](#overview)
- [Why Infrastructure Matters](#why-infrastructure-matters)
- [Network Architecture](#network-architecture)
- [Virtualization Stack](#virtualization-stack)
- [Kubernetes Cluster](#kubernetes-cluster)
- [LLMOps Infrastructure](#llmops-infrastructure)
- [Monitoring Stack](#monitoring-stack)
- [Hardware Requirements](#hardware-requirements)
- [Module Structure](#module-structure)
- [Learning Path](#learning-path)
- [Key Takeaways](#key-takeaways)
- [Common Pitfalls](#common-pitfalls)
- [Pro Tips](#pro-tips)
- [Performance Benchmarks](#performance-benchmarks)
- [Related Experiments](#related-experiments)

---

## Overview

**Converting hardware into a programmable, scalable, 2.5G-throughput factory.**

This phase covers the foundational infrastructure needed to run enterprise-grade AI systems on consumer HomeLab hardware, enabling you to:
- Build a 2.5Gbps star topology network
- Configure GPU passthrough for VM access
- Deploy multi-node K3s Kubernetes cluster
- Run vLLM/TGI for high-throughput inference
- Set up comprehensive monitoring with Prometheus

---

## Why Infrastructure Matters

### The Foundation Problem

```
┌─────────────────────────────────────────────────────────┐
│               Poor Infrastructure                        │
├─────────────────────────────────────────────────────────┤
│ ❌ Network bottlenecks (1Gbps limits throughput)        │
│ │ GPU trapped in host OS (can't be used by VMs)         │
│ ❌ Manual deployments (no orchestration)                │
│ │ No monitoring (blind to failures)                     │
│ ❌ Single points of failure                             │
└─────────────────────────────────────────────────────────┘

With Proper Infrastructure:
┌─────────────────────────────────────────────────────────┐
│               Enterprise-Grade HomeLab                  │
├─────────────────────────────────────────────────────────┤
│ ✅ 2.5Gbps throughput (model loading 2.5x faster)       │
│ ✅ GPU passthrough (VMs access GPU directly)            │
│ ✅ K8s orchestration (auto-scaling, self-healing)       │
│ ✅ Full observability (metrics, logs, traces)            │
│ ✅ Production-ready deployment                          │
└─────────────────────────────────────────────────────────┘
```

### Infrastructure Value

| Component | Without | With | Impact |
|-----------|---------|------|--------|
| **Network** | 1Gbps | 2.5Gbps + Jumbo Frames | 2.5x faster model loading |
| **GPU Passthrough** | Host only | VM access | Full isolation and flexibility |
| **Kubernetes** | Manual | K3s cluster | Auto-deployment, scaling |
| **Monitoring** | None | Prometheus + Grafana | Proactive issue detection |

---

## Network Architecture

```mermaid
graph LR
    A[ISP Fiber] --> B[GPON Modem<br/>Bridge Mode]
    B --> C[2.5Gbps Switch<br/>Star Hub]

    C --> D[Proxmox Host]
    C --> E[Synology NAS]
    C --> F[Intel NUC]
    C --> G[Workstations]

    D --> H[VM: K3s Master]
    D --> I[VM: K3s Worker]

    I --> J[GPU: RTX 2080 Ti<br/>Passthrough]

    style C fill:#fff9c4
    style J fill:#c8e6c9
```

### 2.5Gbps Star Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    Star Topology Benefits                       │
├─────────────────────────────────────────────────────────────────┤
│ Component           │ Benefit                                  │
├─────────────────────────────────────────────────────────────────┤
│ Central Switch      │ Single point of management, 2.5Gbps back │
│ Jumbo Frames (MTU 9000) │ 2.5x more data per packet           │
│ Direct Connections  │ Minimal latency (<1ms)                   │
│ Redundant Paths     │ No single point of failure              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Virtualization Stack

### Proxmox + GPU Passthrough

```
Host: Proxmox VE
├── VM 101: K3s Master (4 vCPU, 8GB RAM)
├── VM 102: K3s Worker + GPU (8 vCPU, 16GB RAM, RTX 2080 Ti)
├── VM 103: Database (2 vCPU, 4GB RAM)
└── VM 104: Monitoring (2 vCPU, 4GB RAM)

GPU: RTX 2080 Ti (11GB VRAM)
└── Passthrough to VM 102 (K3s Worker)
    ├── IOMMU enabled
    ├── VFIO drivers loaded
    └── Direct device access
```

### Virtualization Benefits

| Feature | Description |
|---------|-------------|
| **Resource Isolation** | Each VM gets dedicated CPU/RAM |
| **GPU Passthrough** | VM accesses GPU directly (near-native performance) |
| **Snapshot/Restore** | Easy backup and recovery |
| **Live Migration** | Move VMs without downtime |

---

## Kubernetes Cluster

### K3s Multi-Node Architecture

```mermaid
graph TB
    subgraph "Cluster Control Plane"
        A[K3s Master<br/>Synology VM]
    end

    subgraph "Worker Nodes"
        B[Worker 1<br/>Proxmox VM + GPU]
        C[Worker 2<br/>Intel NUC]
    end

    A -->|API Server| B
    A -->|API Server| C

    B --> D[GPU Scheduler]
    B --> E[Storage Class<br/>NFS from Synology]

    C --> E

    F[Deployments] --> B
    F --> C

    style A fill:#ffcc80
    style B fill:#c8e6c9
    style D fill:#fff9c4
```

### K3s Benefits

- **Lightweight**: Single binary, minimal dependencies
- **GPU Support**: Nvidia device plugin for GPU scheduling
- **Storage**: Dynamic NFS provisioning from Synology
- **Networking**: Flannel CNI with 2.5Gbps backend

---

## LLMOps Infrastructure

### vLLM and TGI

```
┌─────────────────────────────────────────────────────────────────┐
│                  Inference Engine Comparison                    │
├─────────────────────────────────────────────────────────────────┤
│ Feature             │ Ollama    │ vLLM      │ TGI              │
├─────────────────────────────────────────────────────────────────┤
│ Concurrency         │ Low       │ Very High │ High             │
│ Throughput (tok/s)  │ 30-50     │ 200-500   │ 150-300          │
│ Memory Efficiency   │ Medium    │ Best      │ High             │
│ PagedAttention      │ ❌        │ ✅        │ ✅               │
│ Quantization        │ GGUF      │ AWQ/GPTQ  │ AWQ/GPTQ/BNB     │
│ Use Case            │ Dev/Test  │ Production │ Production       │
└─────────────────────────────────────────────────────────────────┘
```

### Engine Selection

| Scenario | Recommended Engine | Why |
|----------|-------------------|-----|
| **Development** | Ollama | Easy setup, local testing |
| **High Throughput** | vLLM | PagedAttention, best concurrency |
| **Production** | TGI or vLLM | Battle-tested, production-ready |
| **Low Memory** | vLLM + AWQ | Best memory efficiency |

---

## Monitoring Stack

### Observability Architecture

```mermaid
graph LR
    A[Applications] --> B[Metrics]
    A --> C[Logs]
    A --> D[Traces]

    B --> E[Prometheus]
    C --> F[Loki]
    D --> G[Tempo]

    E --> H[Grafana]
    F --> H
    G --> H

    I[Node Exporter] --> E
    J[cAdvisor] --> E
    K[GPU Exporter] --> E

    style H fill:#f8bbd0
    style E fill:#fff9c4
```

### Monitoring Components

| Component | Purpose | Data Collected |
|-----------|---------|----------------|
| **Prometheus** | Metrics collection | CPU, RAM, GPU, network |
| **Grafana** | Visualization | Dashboards, alerts |
| **Loki** | Log aggregation | Application logs |
| **Tempo** | Distributed tracing | Request flows |
| **Node Exporter** | Host metrics | System-level stats |
| **cAdvisor** | Container metrics | Docker/K8s stats |
| **GPU Exporter** | GPU metrics | Utilization, memory, temp |

---

## Hardware Requirements

### Minimum Specifications

| Component | Minimum | Recommended | Purpose |
|-----------|---------|-------------|---------|
| **Host CPU** | 6 cores | 12+ cores | Proxmox + VMs |
| **Host RAM** | 32GB | 64GB+ | VM memory allocation |
| **GPU** | RTX 2080 Ti | RTX 3090/4090 | Model inference |
| **GPU VRAM** | 11GB | 24GB+ | Larger models |
| **Network** | 2.5Gbps switch | 10Gbps | Fast data transfer |
| **Storage** | 500GB NVMe | 1TB+ NVMe | Fast I/O for models |
| **NAS** | Synology DS720+ | DS923+ | Central storage |

### Cost Analysis (Estimated)

| Component | Cost (USD) |
|-----------|------------|
| Intel NUC 12th Gen | $600-800 |
| RTX 2080 Ti (used) | $400-500 |
| 2.5Gbps Switch | $50-100 |
| Synology DS720+ | $400-500 |
| Proxmox Host (DIY) | $800-1000 |
| **Total** | **~$2,250-2,900** |

---

## Module Structure

### [1100] Network Topology & Traffic Management

| Document | Description | Time | Difficulty |
|----------|-------------|------|------------|
| [1101: Fiber GPON Modem](./1100-network/1101-Fiber-GPON-Modem.md) | Signal path, WAN bypass | 2h | Beginner |
| [1102: Star Topology Core](./1100-network/1102-Star-Topology-Core.md) | 2.5Gbps switch configuration | 3h | Intermediate |
| [1103: Jumbo Frames and MTU](./1100-network/1103-Jumbo-Frames-and-MTU.md) | MTU 9000 optimization | 2h | Intermediate |

**What You'll Learn:**
- GPON modem bridge mode configuration
- Star topology with 2.5Gbps switch
- Jumbo frames (MTU 9000) for throughput optimization
- Network latency optimization

**Hands-On Practice:**
- Configure GPON modem in bridge mode
- Set up star topology network
- Enable jumbo frames end-to-end
- Benchmark network throughput

### [1200] Host Virtualization & PCIE Passthrough

| Document | Description | Time | Difficulty |
|----------|-------------|------|------------|
| [1201: Proxmox Hypervisor SOP](./1200-virtualization/1201-Proxmox-Hypervisor-SOP.md) | Core pinning, RAM balloons | 3h | Intermediate |
| [1202: TB3 UT3G Passthrough](./1200-virtualization/1202-TB3-UT3G-Passthrough.md) | Thunderbolt 3 GPU passthrough | 4h | Advanced |
| [1203: Nvidia Kernel Module](./1200-virtualization/1203-Nvidia-Kernel-Module.md) | DKMS, driver stability | 2h | Intermediate |
| [1204: Multi-GPU Setup](./1200-virtualization/1204-Multi-GPU-Setup.md) | Multiple GPU configuration | 3h | Advanced |

**What You'll Learn:**
- Proxmox VE installation and configuration
- CPU pinning and memory ballooning
- GPU passthrough via Thunderbolt 3
- Nvidia driver management in VMs

**Hands-On Practice:**
- Install Proxmox VE on bare metal
- Configure VM with GPU passthrough
- Verify GPU access in VM with nvidia-smi
- Set up multi-GPU configuration

### [1300] Kubernetes (K3s) & Container Orchestration

| Document | Description | Time | Difficulty |
|----------|-------------|------|------------|
| [1301: K3s Architecture](./1300-kubernetes/1301-K3s-Master-Worker-Arch.md) | Multi-node cluster setup | 4h | Intermediate |
| [1302: GPU Scheduler](./1300-kubernetes/1302-GPU-Scheduler.md) | Nvidia device plugin | 3h | Advanced |
| [1303: Storage Classes](./1300-kubernetes/1303-Storage-Classes.md) | Dynamic NFS provisioning | 2h | Intermediate |

**What You'll Learn:**
- K3s multi-node cluster deployment
- GPU scheduling with Nvidia device plugin
- Dynamic storage provisioning with NFS
- Pod deployment and scaling

**Hands-On Practice:**
- Deploy K3s master and worker nodes
- Configure GPU scheduler
- Create storage class for dynamic provisioning
- Deploy sample GPU workload

### [1400] LLMOps Infrastructure

| Document | Description | Time | Difficulty |
|----------|-------------|------|------------|
| [1401: Ollama Enterprise](./1400-llmops/1401-Ollama-Enterprise.md) | Local model APIs | 2h | Beginner |
| [1402: vLLM and TGI](./1400-llmops/1402-vLLM-and-TGI.md) | High-concurrency engines | 4h | Intermediate |
| [1404: vLLM Production](./1400-llmops/guides/1404-vLLM-Production-Deployment.md) | Production deployment | 3h | Advanced |
| [1405: TGI Deployment](./1400-llmops/guides/1405-TGI-Deployment-Guide.md) | TGI setup guide | 3h | Advanced |

**What You'll Learn:**
- Ollama for local model serving
- vLLM PagedAttention mechanism
- TGI production deployment
- Model quantization (AWQ, GPTQ)

**Hands-On Practice:**
- Deploy Ollama on K3s
- Configure vLLM with quantized model
- Set up TGI for production
- Benchmark inference throughput

### [1500] Monitoring & Observability

| Document | Description | Time | Difficulty |
|----------|-------------|------|------------|
| [1501: Monitoring Stack](./1500-monitoring/1501-Monitoring-and-Observability.md) | Prometheus + Grafana + Loki | 4h | Intermediate |

**What You'll Learn:**
- Prometheus metrics collection
- Grafana dashboard creation
- Loki log aggregation
- Tempo distributed tracing
- Alert configuration

**Hands-On Practice:**
- Deploy Prometheus on K3s
- Create Grafana dashboards
- Set up Loki for log aggregation
- Configure alerts

---

## Learning Path

### Recommended Flow

```mermaid
graph TD
    A[Start] --> B{Hardware Ready?}

    B -->|No| C[Acquire Hardware]
    B -->|Yes| D[1100: Network Setup]

    C --> D

    D --> E[1200: Proxmox + GPU Passthrough]
    E --> F[1300: K3s Cluster]
    F --> G[1400: vLLM/TGI Deployment]
    G --> H[1500: Monitoring Stack]

    H --> I[Infrastructure Complete]

    style D fill:#e1f5fe
    style E fill:#fff3e0
    style F fill:#f3e5f5
    style G fill:#fce4ec
    style H fill:#c8e6c9
```

### Time Estimates

| Module | Reading | Practice | Total |
|--------|---------|----------|-------|
| 1100: Network | 7h | 5h | 12h |
| 1200: Virtualization | 12h | 8h | 20h |
| 1300: K3s | 9h | 6h | 15h |
| 1400: LLMOps | 12h | 8h | 20h |
| 1500: Monitoring | 4h | 4h | 8h |
| **Total** | **44h** | **31h** | **75h** |

---

## Key Takeaways

### ✅ You Will Learn

After completing this phase, you will be able to:

1. **Build High-Speed Network**
   - Configure 2.5Gbps star topology
   - Enable jumbo frames (MTU 9000)
   - Optimize network latency
   - Benchmark throughput performance

2. **Configure GPU Passthrough**
   - Set up IOMMU in Proxmox
   - Configure VFIO drivers
   - Passthrough GPU to VM
   - Verify with nvidia-smi

3. **Deploy K3s Cluster**
   - Install K3s master and workers
   - Configure GPU scheduler
   - Set up dynamic storage
   - Deploy GPU workloads

4. **Run Production Inference**
   - Deploy vLLM with PagedAttention
   - Configure TGI for production
   - Use quantized models (AWQ/GPTQ)
   - Optimize throughput and latency

5. **Monitor Everything**
   - Set up Prometheus metrics
   - Create Grafana dashboards
   - Aggregate logs with Loki
   - Configure alerts

---

## Common Pitfalls

### ⚠️ MTU Mismatch

**Pitfall:** Different MTU settings causing packet fragmentation
```bash
# Wrong: MTU mismatch between devices
ip link show eth0  # MTU 1500
ip link show docker0  # MTU 1500
# Result: Packet loss, poor performance

# Right: Consistent MTU 9000 end-to-end
ip link set eth0 mtu 9000
ip link set docker0 mtu 9000
# Verify with ping test
ping -M do -s 8972 192.168.1.1
```

### ⚠️ GPU Passthrough Fails

**Pitfall:** IOMMU not properly configured
```bash
# Wrong: GPU not in isolated IOMMU group
lspci -nnk -d ::1a
# Shows GPU shared with other devices

# Right: Isolated IOMMU group
# Add to /etc/default/grub:
# GRUB_CMDLINE_LINUX_DEFAULT="intel_iommu=on iommu=pt"
sudo update-grub && sudo reboot

# Verify with:
dmesg | grep -e DMAR -e IOMMU
```

### ⚠️ K3s GPU Not Available

**Pitfall:** Nvidia device plugin not installed
```bash
# Wrong: GPU not visible to K8s
kubectl get nodes
# Shows no GPU resources

# Right: Install Nvidia device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Verify GPU is available
kubectl describe node | grep nvidia.com/gpu
```

### ⚠️ vLLM Out of Memory

**Pitfall:** Loading full model without quantization
```python
# Wrong: Load full model (11GB+)
vllm serve mistralai/Mistral-7B-Instruct-v0.2
# Error: CUDA out of memory

# Right: Use quantized model
vllm serve mistralai/Mistral-7B-Instruct-v0.2 \
  --quantization awq \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9
```

### ⚠️ Monitoring Data Loss

**Pitfall:** Prometheus not persisting metrics
```yaml
# Wrong: Default ephemeral storage
# Data lost on pod restart

# Right: Persistent volume claim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-data
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 50Gi
```

---

## Pro Tips

### 💡 Network Optimization

**Tip:** Test throughput before deploying
```bash
# Test with iperf3
iperf3 -s  # Server
iperf3 -c 192.168.1.1 -t 30  # Client

# Expected: >2 Gbps with 2.5Gbps network
# If <1 Gbps: Check cables (Cat6+ required)
```

### 💡 Proxmox Performance

**Tip:** Pin CPU cores for GPU VM
```bash
# Edit VM config
vim /etc/pve/qemu-server/102.conf

# Add CPU pinning
cores: 4
cpuunits: 1024
vcpus: 0
hostpci0: 0000:03:00.0,pcie=1
# Pin VM to physical cores 4-7
args: -set device.hostpci0.host=03:00.0 -set device.hostpci0 rombar=0
```

### 💡 K3s Quick Deploy

**Tip:** Use installation script with tokens
```bash
# Master
curl -sfL https://get.k3s.io | sh -
TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)

# Worker
curl -sfL https://get.k3s.io | \
  K3S_URL=https://192.168.1.100:6443 \
  K3S_TOKEN=$TOKEN sh -
```

### 💡 vLLM Performance

**Tip:** Tune block size for throughput
```bash
vllm serve model \
  --block-size 16 \  # Default, good for most
  --max-num-seqs 256 \  # Increase for high concurrency
  --max-num-batched-tokens 8192  # Increase for faster generation
```

### 💡 Prometheus Retention

**Tip:** Adjust retention for storage
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Reduce retention if storage limited
# storage.tsdb.retention.time: 15d  # Default 15d
# storage.tsdb.retention.size: 10GB  # Alternative
```

---

## Performance Benchmarks

### Network Performance

| Configuration | Throughput | Latency |
|---------------|------------|---------|
| 1Gbps + MTU 1500 | 950 Mbps | 1-2ms |
| 2.5Gbps + MTU 1500 | 2.3 Gbps | 1ms |
| 2.5Gbps + MTU 9000 | 2.4 Gbps | <1ms |

### GPU Passthrough Overhead

| Configuration | Inference (tok/s) | Overhead |
|---------------|-------------------|----------|
| Native GPU | 120 | 0% |
| Passthrough (VM) | 118 | ~2% |
| No Passthrough (software) | N/A | N/A |

### Inference Engine Throughput

| Engine | Model | Quantization | Throughput (req/s) |
|--------|-------|--------------|-------------------|
| Ollama | Mistral 7B | Q4_0 | 5-10 |
| vLLM | Mistral 7B | AWQ | 50-100 |
| TGI | Mistral 7B | AWQ | 40-80 |
| vLLM | Llama 3 8B | FP16 | 30-60 |

### Memory Usage

| Model | Precision | VRAM Required |
|-------|-----------|---------------|
| Mistral 7B | FP16 | 14 GB |
| Mistral 7B | 4-bit (AWQ) | 5 GB |
| Llama 3 8B | FP16 | 16 GB |
| Llama 3 8B | 4-bit (AWQ) | 6 GB |

---

## Related Experiments

### Hands-on Practice

1. **[EXP_1101: GPON](../../../experiments/EXP_1101_GPON.md)**
   - Configure GPON modem bridge mode
   - Test WAN bypass
   - Verify internet connectivity

2. **[EXP_1103: Star Topology](../../../experiments/EXP_1103_STAR_TOPOLOGY.md)**
   - Build 2.5Gbps star topology
   - Enable jumbo frames
   - Benchmark network performance

3. **[EXP_1302: GPU Scheduler](../../../experiments/EXP_1302_GPU_SCHEDULER.md)**
   - Deploy K3s GPU scheduler
   - Run GPU workloads
   - Verify resource allocation

4. **[EXP_1403: TGI Tuning](../../../experiments/EXP_1403_TGI_TUNING.md)**
   - Deploy TGI server
   - Optimize parameters
   - Benchmark throughput

5. **[EXP_1404: vLLM Tuning](../../../experiments/EXP_1404_VLLM_TUNING.md)**
   - Deploy vLLM server
   - Tune block size and concurrency
   - Compare vs TGI

6. **[EXP_1501: Monitoring](../../../experiments/EXP_1501_MONITORING.md)**
   - Deploy Prometheus + Grafana
   - Create dashboards
   - Set up alerts

---

## Assessment

Validate your knowledge with:

- **[Phase a Quiz](../../00-META/assessment/phase1-quiz.md)** - Test your understanding (25 questions, 80% to pass)
- **[Phase a Practice](../../00-META/assessment/phase1-practice.md)** - Hands-on infrastructure exercises

---

## Related Topics

- **Phase 2:** AI/ML Foundations
- **Phase 4:** Model Quantization
- **Phase 5:** Fine-Tuning
- **SOL-001:** Complete Enterprise Solution

---

## Next Steps

After completing this phase:

1. **Deploy Your Infrastructure**
   - Set up network and virtualization
   - Deploy K3s cluster
   - Configure monitoring

2. **Continue Learning**
   - **Phase 2:** Learn AI/ML foundations
   - **Phase 4:** Quantize models for efficiency
   - **Phase 6:** Build RAG systems

---

**Status:** ✅ Complete
**Module Duration:** 75 hours (44 reading + 31 practice)
**Difficulty:** Intermediate
**Last Updated:** 2026-02-05

**Ready to build your HomeLab infrastructure?** Start with [1101: Fiber GPON Modem](./1100-network/1101-Fiber-GPON-Modem.md) or [1102: Star Topology Core](./1100-network/1102-Star-Topology-Core.md)
