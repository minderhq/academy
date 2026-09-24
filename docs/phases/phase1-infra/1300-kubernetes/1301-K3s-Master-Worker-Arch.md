---
Document ID: 1301
Title: K3s Master-Worker Architecture
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

# 1301: K3s Master-Worker Architecture

## Abstract
K3s is a lightweight Kubernetes distribution optimized for edge computing and IoT. Here it orchestrates a small multi-node cluster: a control-plane node (any Linux VM or box) and a GPU worker node that runs AI workloads.

## Architecture Overview

### Cluster Topology
```
┌─────────────────────────────────────────────────────────────┐
│                       K3s Cluster                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │  Control-Plane   │         │   Worker Node    │        │
│  │      Node        │◄────────┤   (GPU Node)     │        │
│  │ (Linux VM/box)   │  API    │                  │        │
│  │  - API Server    │  6443   │  - Kubelet       │        │
│  │  - Scheduler     │────────►│  - Containerd    │        │
│  │  - Controller    │         │  - GPU Device    │        │
│  │  - etcd          │         │  - NVIDIA GPU    │        │
│  └──────────────────┘         └──────────────────┘        │
│         │                              │                   │
└─────────┼──────────────────────────────┼───────────────────┘
          │                              │
     VLAN 30                        VLAN 30
          │                              │
   [Storage Server]            [Managed Switch]
                                         │
                                    [192.168.1.0/24]
```

### Component Breakdown

#### Master Node (Control Plane)
```
Services:                 Port:    Purpose:
────────────────────────────────────────────────────
API Server                6443     All cluster communication
Scheduler                 -        Pod placement decisions
Controller Manager        10250    Runs controllers
etcd                      2379     Cluster state database
```

#### Worker Node (GPU + Kubelet)
```
Services:                 Port:    Purpose:
────────────────────────────────────────────────────
Kubelet                   10250    Pod lifecycle management
Containerd                -        Container runtime
Flannel/Cilium            8472     Overlay networking
NVIDIA Device Plugin      -        GPU resource exposure
```

## Installation

### Control-Plane Node
```bash
# Download K3s binary
curl -sfL https://get.k3s.io | sh -

# Check status
systemctl status k3s

# Get join token
cat /var/lib/rancher/k3s/server/node-token
# Output: K10abc...def::server:abc123...

# Get server IP
ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1
```

### GPU Worker Node
```bash
# Install K3s agent
curl -sfL https://get.k3s.io | K3S_URL=https://192.168.1.50:6443 \
  K3S_TOKEN=K10abc...def::server:abc123... sh -

# Verify connection
kubectl get nodes
```

## Configuration

### Master Configuration (/etc/rancher/k3s/config.yaml)
```yaml
# Cluster identity
cluster-domain: "omega.local"
cluster-dns: "10.43.0.10"

# Networking
flannel-iface: "eth0"
flannel-mtu: 9000
node-name: "omega-master"

# etcd configuration
etcd-expose-metrics: true

# Disable unnecessary features
disable:
  - traefik          # Use ingress-nginx instead
  - servicelb        # Use MetalLB instead

# Feature gates
feature-gates: "CPUManager=true,MemoryManager=true"

# Audit logging
audit-log-file: "/var/log/k3s/audit.log"
audit-log-maxage: 30
audit-log-maxbackup: 10
```

### Worker Configuration
```yaml
# Node identity
node-name: "omega-worker-gpu"
node-external-ip: "192.168.1.10"

# GPU support
kubelet-arg:
  - "feature-gates=DevicePlugins=false"
  - "cpu-manager-policy=static"

# Containerd
containerd-arg:
  - "config=/var/lib/rancher/k3s/agent/etc/containerd/config.toml"

# Resolv.conf (for custom DNS)
resolv-conf: "/etc/k3s-resolv.conf"
```

## GPU Node Configuration

### NVIDIA Device Plugin
```bash
# Deploy device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Verify
kubectl -n kube-system logs ds/nvidia-device-plugin-daemonset
```

### Node Labels for GPU
```bash
# Label GPU node (use values matching YOUR hardware)
kubectl label node omega-worker-gpu \
  accelerator=nvidia \
  gpu.memory=11GB \
  gpu.count=1

# Verify
kubectl describe node omega-worker-gpu | grep -A 5 "Labels"
```

### Taints for GPU-Only Workloads
```bash
# Taint GPU node (optional - only GPU pods can schedule)
kubectl taint node omega-worker-gpu \
  nvidia.com/gpu=true:NoSchedule

# Pods need toleration:
# tolerations:
# - key: nvidia.com/gpu
#   operator: Exists
#   effect: NoSchedule
```

## Storage Integration

### NFS Storage (Static PV)
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-ai-pv
spec:
  capacity:
    storage: 1Ti
  accessModes:
    - ReadWriteMany
  nfs:
    server: 192.168.1.100
    path: "/srv/ai-storage"
  mountOptions:
    - hard
    - nfsvers=4.2
    - noatime
---
apiVersion: storage.k8s.io/v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-ai-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Ti
  volumeName: nfs-ai-pv
  storageClassName: ""
```

### StorageClass for Dynamic Provisioning
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs
provisioner: nfs.csi.k8s.io
parameters:
  server: 192.168.1.100
  share: /srv/ai-storage
reclaimPolicy: Delete
volumeBindingMode: Immediate
mountOptions:
  - hard
  - nfsvers=4.2
  - noatime
```

## Networking

### Cluster IP Range
```
Pod CIDR:        10.42.0.0/16
Service CIDR:    10.43.0.0/16
Cluster Domain:  omega.local
```

### Flannel Configuration
```yaml
# ConfigMap for flannel
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-flannel-cfg
  namespace: kube-system
data:
  net-conf.json: |
    {
      "Network": "10.42.0.0/16",
      "Backend": {
        "Type": "vxlan",
        "Port": 8472,
        "MTU": 9000
      }
    }
```

### Ingress Configuration
```bash
# Install ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --set controller.service.type=NodePort \
  --set controller.config.use-forwarded-headers="true"
```

## Resource Management

### CPU Manager (Static Policy)
```yaml
# Kubelet config
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cpuManagerPolicy: static
cpuManagerPolicyOptions:
  "full-pcpus-only": "true"
systemReserved:
  cpu: "2"
  memory: "4Gi"
kubeReserved:
  cpu: "1"
  memory: "2Gi"
```

### Memory Manager
```yaml
memoryManagerPolicy: Static
evictionHard:
  memory.available: "512Mi"
  nodefs.available: "10%"
```

## Monitoring

### Metrics Server
```bash
# Install
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/metrics-server/main/components.yaml

# Add trusted CA for self-signed certs
patch=`
- op: add
  path: /spec/template/spec/containers/0/args/-
  value: --kubelet-insecure-tls
`
kubectl patch deployment metrics-server -n kube-system --type=json -p="$patch"
```

### Node Exporter
```bash
# Deploy node exporter
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus-node-exporter prometheus-community/prometheus-node-exporter \
  --set service.hostPort=9100
```

---

## Next Steps

- Continue with: **[1302: GPU Scheduler](./1302-GPU-Scheduler.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1201: Proxmox Hypervisor](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)
- [1302: GPU Scheduler](./1302-GPU-Scheduler.md)
- [1303: Storage Classes](./1303-Storage-Classes.md)

**Experiment Template:** `experiments/EXP_1301_K3S_ARCH.md`
