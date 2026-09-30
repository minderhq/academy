---
Document ID: QUICK-REF-VOLUME-1
Title: "Volume 1: Infrastructure Mastery - Quick Reference"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'infrastructure', 'docker', 'kubernetes']
---

# Volume 1: Infrastructure Mastery - Quick Reference

**Build Your AI Laboratory** - Essential commands and concepts

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Fiber/GPON Modem                           │
│              (Jumbo Frames: 9000 MTU)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Proxmox Host                               │
│  ┌──────────────────────────────────────────────┐      │
│  │  VM 1: GPU Passthrough (A100/H100)           │      │
│  │  VM 2: GPU Passthrough (A100/H100)           │      │
│  │  VM 3: K3s Master                            │      │
│  │  VM 4: K3s Worker 1                          │      │
│  │  VM 5: K3s Worker 2                          │      │
│  └──────────────────────────────────────────────┘      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              K3s Kubernetes Cluster                     │
│  ┌──────────────────────────────────────────────┐      │
│  │  GPU Node 1     GPU Node 2    Storage Node   │      │
│  │  (vLLM/TGI)     (vLLM/TGI)     (Longhorn)    │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## Network Configuration

### Jumbo Frames Setup
```bash
# Enable 9000 MTU for better throughput
# Proxmox host
cat > /etc/network/interfaces << EOF
iface eno1 inet static
    address 192.168.1.10/24
    gateway 192.168.1.1
    mtu 9000
EOF

# Restart networking
systemctl restart networking

# Verify MTU
ip link show eno1 | grep mtu
```

### Star Topology Core
```text
# Core switch configuration
# All devices connect to central switch
# Reduces latency and simplifies management

# Benefits:
- Single point of configuration
- Predictable latency
- Easy troubleshooting
- Supports GPU direct (RDMA)
```

---

## Proxmox Commands

### VM Management
```bash
# List VMs
qm list

# Create VM
qm create 100 --name gpu-vm1 --memory 128000 --cores 64

# GPU Passthrough
qm set 100 --hostpci0 01:00.0,pcie=1

# Start VM
qm start 100

# Console into VM
qm terminal 100
```

### Storage Management
```bash
# List storage
pvesm status

# Add local directory storage
pvesm add dir local-zfs --path /mnt/data

# Add NFS storage
pvesm add nfs nfs-storage --server 192.168.1.100 --export /data
```

---

## GPU Passthrough

### IOMMU Setup
```bash
# Enable IOMMU in GRUB
# /etc/default/grub
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"

# Update GRUB
update-grub
update-initramfs -u

# Reboot
reboot

# Verify IOMMU
dmesg | grep -e IOMMU -e DMAR
```

### VFIO Configuration
```bash
# Load VFIO modules
echo "vfio" >> /etc/modules
echo "vfio_pci" >> /etc/modules
echo "vfio_iommu_type1" >> /etc/modules

# Blacklist NVIDIA driver (for passthrough)
echo "blacklist nvidia" >> /etc/modprobe.d/blacklist.conf
echo "blacklist nouveau" >> /etc/modprobe.d/blacklist.conf

# Update initramfs
update-initramfs -u
```

---

## K3s Kubernetes

### Installation
```bash
# Master node
curl -sfL https://get.k3s.io | sh -

# Get token
cat /var/lib/rancher/k3s/server/node-token

# Worker node
curl -sfL https://get.k3s.io | K3S_URL=https://master:6443 K3S_TOKEN=xxx sh -

# Verify
kubectl get nodes
```

### GPU Scheduler
```bash
# Install NVIDIA device plugin
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Verify GPUs
kubectl get nodes -o json | jq '.items[].status.allocatable'
```

### Storage Classes
```bash
# Create storage class
cat > storage-class.yaml << EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-storage
provisioner: driver.longhorn.io
parameters:
  numberOfReplicas: "3"
  staleReplicaTimeout: "2880"
allowVolumeExpansion: true
EOF

kubectl apply -f storage-class.yaml

# Use in pod
kubectl apply -f - << EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-storage
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: fast-storage
  resources:
    requests:
      storage: 100Gi
EOF
```

---

## LLMOps Stack

### vLLM Deployment
```yaml
# vllm-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-llama3-70b
spec:
  replicas: 2
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
        resources:
          limits:
            nvidia.com/gpu: 4
        env:
        - name: MODEL_NAME
          value: "meta-llama/Llama-2-70b-hf"
        - name: TENSOR_PARALLEL_SIZE
          value: "4"
        ports:
        - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
spec:
  selector:
    app: vllm
  ports:
  - port: 8000
  type: LoadBalancer
```

### TGI Deployment
```yaml
# tgi-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tgi-falcon-40b
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: tgi
        image: ghcr.io/huggingface/text-generation-inference:latest
        resources:
          limits:
            nvidia.com/gpu: 4
        args:
        - --model-id
        - tiiuae/falcon-40b
        - --tensor-parallel-size
        - "4"
        - --max-total-tokens
        - "8192"
```

---

## Monitoring

### Prometheus Configuration
```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
- job_name: 'kubernetes-pods'
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: true

- job_name: 'nvidia-gpu'
  static_configs:
  - targets: ['gpu-exporter:9400']
```

### Grafana Dashboards
```text
# Import GPU monitoring dashboard
# Dashboard ID: 14531 (NVIDIA GPU Metrics)

# Key metrics to monitor:
- GPU Utilization
- GPU Memory Usage
- Temperature
- Power Consumption
- Throughput (tokens/sec)
```

---

## Troubleshooting

### Common Issues

**GPU not visible in container:**
```bash
# Check GPU passthrough
lspci | grep -i nvidia

# Check nvidia-smi
nvidia-smi

# Check device plugin
kubectl logs -n kube-system nvidia-device-plugin-xxx
```

**High latency:**
```bash
# Check network MTU
ip link show | grep mtu

# Check GPU memory
nvidia-smi

# Check pod resources
kubectl top pods
```

**Storage issues:**
```bash
# Check PV/PVC status
kubectl get pv,pvc

# Check storage class
kubectl get sc

# Check Longhorn
kubectl get -n longhorn volume
```

---

## Quick Start Checklist

- [ ] Network configured (Jumbo Frames enabled)
- [ ] Proxmox installed and configured
- [ ] GPU passthrough working
- [ ] K3s cluster deployed
- [ ] GPU scheduler configured
- [ ] Storage class created
- [ ] vLLM/TGI deployed
- [ ] Monitoring setup
- [ ] Load balancer configured
- [ ] Test with sample model

---

## Next Steps

1. Complete LAB-001: Docker & LLM
2. Read 1401-Ollama-Enterprise.md
3. Read 1402-vLLM-and-TGI.md
4. Deploy first model to production

---

**Volume:** 1 - Infrastructure Mastery
**Estimated Time:** 40-50 hours
