---
Document ID: 1301
Title: "1301: K3s Master-Worker Architecture"
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

# 1301: K3s Master-Worker Architecture

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Architecture Overview](#architecture-overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [GPU Node Configuration](#gpu-node-configuration)
- [Storage Integration](#storage-integration)
- [Networking](#networking)
- [Resource Management](#resource-management)
- [Monitoring](#monitoring)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Map the K3s control plane (API server :6443, embedded SQLite, scheduler/controller) to its GPU worker counterpart (kubelet :10250, containerd, flannel :8472) and justify when etcd replaces SQLite for HA
- Bootstrap a cluster with get.k3s.io — `K3S_URL` plus node-token on workers — then shape `config.yaml` (disable traefik/servicelb, add audit `kube-apiserver-arg` flags)
- Expose GPUs to pods through the NVIDIA device plugin, using labels and taints/tolerations so only GPU-requesting pods schedule onto GPU nodes
- Provision shared training storage with NFS static PV/PVC (`ReadWriteMany`) backed by the `nfs.csi.k8s.io` StorageClass
- Reason about flannel networking — pod CIDR 10.42.0.0/16, service CIDR 10.43.0.0/16, vxlan MTU 9000, ingress-nginx NodePort — when debugging cross-node connectivity
- Tune the kubelet resource policy (static cpu-manager, `full-pcpus-only`, reserved system memory, `evictionHard`) so training pods never starve the node

---

## Abstract
K3s is a lightweight Kubernetes distribution optimized for edge computing and IoT. Here it orchestrates a small multi-node cluster: a control-plane node (any Linux VM or box) and a GPU worker node that runs AI workloads.

## Architecture Overview

### Cluster Topology
```text
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
│  │  - Controller    │         │  - Device Plugin │        │
│  │  - SQLite store  │         │  - NVIDIA GPU    │        │
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
```text
Services:                 Port:    Purpose:
────────────────────────────────────────────────────
API Server                6443     All cluster communication
Scheduler                 -        Pod placement decisions
Controller Manager        -        Runs controllers
SQLite (embedded)         -        Cluster state database
# Single-server k3s boots with an embedded SQLite datastore; etcd
# only comes into play for HA (2+ server nodes). 10250 is the
# kubelet port - every node listens on it, not just the control plane.
```

#### Worker Node (GPU + Kubelet)
```text
Services:                 Port:    Purpose:
────────────────────────────────────────────────────
Kubelet                   10250    Pod lifecycle management
Containerd                -        Container runtime
Flannel (default CNI)     8472     Overlay networking
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
cluster-domain: "academy.local"
cluster-dns: "10.43.0.10"

# Networking
flannel-iface: "eth0"
# NOTE: there is no flannel-mtu flag - the overlay MTU is set in the
# flannel net-conf (see the Flannel Configuration section below).

# Disable unnecessary features
disable:
  - traefik          # Use ingress-nginx instead
  - servicelb        # Use MetalLB instead

# CPU/Memory managers are kubelet POLICIES, not feature gates (k3s has
# no feature-gates flag either) - configure them through the kubelet
# config, see the Resource Management section.

# Audit logging - k3s has no audit-log-* flags; they are passed to the
# API server (audit-policy-file must point at a real policy file):
kube-apiserver-arg:
  - "audit-policy-file=/etc/rancher/k3s/audit-policy.yaml"
  - "audit-log-path=/var/log/k3s/audit.log"
  - "audit-log-maxage=30"
  - "audit-log-maxbackup=10"
```

### Worker Configuration (/etc/rancher/k3s/config.yaml on the agent)
```yaml
# Node identity
node-name: "academy-worker-gpu"
node-external-ip: "192.168.1.10"

# GPU support
kubelet-arg:
  - "cpu-manager-policy=static"

# Device plugins MUST stay enabled for GPUs: the NVIDIA device plugin
# talks to the kubelet's DevicePlugin socket, and modern Kubernetes
# has no DevicePlugins gate to turn off. Never add
# "feature-gates=DevicePlugins=false" on a GPU node - it would hide
# the GPU from Kubernetes entirely.

# Containerd - k3s has no containerd-arg flag; to customize containerd
# write a template instead:
#   /var/lib/rancher/k3s/agent/etc/containerd/config.toml.tmpl
# (k3s renders it into config.toml on start)

# Resolv.conf (for custom DNS)
resolv-conf: "/etc/k3s-resolv.conf"
```

## GPU Node Configuration

### NVIDIA Device Plugin
```bash
# Deploy device plugin (v0.20.x is the current line - older tags like
# v0.14 predate today's driver/containerd combos)
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.20.1/nvidia-device-plugin.yml

# Verify
kubectl -n kube-system logs ds/nvidia-device-plugin-daemonset

# For full driver + plugin lifecycle management NVIDIA ships the GPU
# Operator; the standalone plugin above stays fine for a fixed driver
# setup like this homelab (see 1203's driver DaemonSet for the
# container equivalent).
```

### Node Labels for GPU
```bash
# Label GPU node (use values matching YOUR hardware)
kubectl label node academy-worker-gpu \
  accelerator=nvidia \
  gpu.memory=11GB \
  gpu.count=1

# Verify
kubectl describe node academy-worker-gpu | grep -A 5 "Labels"
```

### Taints for GPU-Only Workloads
```bash
# Taint GPU node (optional - only GPU pods can schedule)
kubectl taint node academy-worker-gpu \
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
```text
Pod CIDR:        10.42.0.0/16
Service CIDR:    10.43.0.0/16
Cluster Domain:  academy.local
```

### Flannel Configuration
```bash
# k3s runs flannel in-process (no kube-flannel DaemonSet), so the
# upstream flannel ConfigMap does not apply here. Override the net-conf
# through the documented --flannel-conf flag, set identically on ALL
# server nodes, then restart k3s:
cat > /etc/rancher/k3s/flannel-net-conf.json <<'EOF'
{
  "Network": "10.42.0.0/16",
  "Backend": {
    "Type": "vxlan",
    "Port": 8472,
    "MTU": 9000
  }
}
EOF
# In config.yaml on every server node:
#   flannel-conf: "/etc/rancher/k3s/flannel-net-conf.json"
systemctl restart k3s
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
# Install (the manifest ships as a release asset, not in the repo
# tree - raw .../main/components.yaml is a 404):
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Homelab kubelets use self-signed certs - add --kubelet-insecure-tls
# (--type json takes a literal JSON patch array, not YAML):
kubectl patch deployment metrics-server -n kube-system \
  --type json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

### Node Exporter
```bash
# Deploy node exporter (hostNetwork binds it to the host's :9100)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus-node-exporter prometheus-community/prometheus-node-exporter \
  --set hostNetwork=true
```

---

## Summary

K3s is a lightweight Kubernetes distribution built for edge and homelab scale, and this lesson is its architecture: a control-plane node and a GPU worker node running AI workloads. It walked installation and configuration, GPU node configuration, storage integration, networking, resource management, and monitoring - the pieces that turn two machines into one schedulable cluster. The rule it leaves: K3s gives you real Kubernetes semantics at a fraction of the operational weight, and the architecture page is where that trade is made deliberately.

## References

### Related Minder Academy Documents

- [1302: GPU Scheduler Configuration](1302-GPU-Scheduler.md)
- [1303: Storage Classes for Dynamic Provisioning](1303-Storage-Classes.md)

---

## Next Steps

- Continue with: **[1302: GPU Scheduler Configuration](./1302-GPU-Scheduler.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**

- [1201: Proxmox Hypervisor Standard Operating Procedures](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)
- [1302: GPU Scheduler Configuration](./1302-GPU-Scheduler.md)
- [1303: Storage Classes for Dynamic Provisioning](./1303-Storage-Classes.md)

