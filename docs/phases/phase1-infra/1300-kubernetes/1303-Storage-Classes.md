---
Document ID: 1303
Title: "1303: Storage Classes for Dynamic Provisioning"
Phase: 1
Module: 1300
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'kubernetes', 'k3s', 'gpu']
---

# 1303: Storage Classes for Dynamic Provisioning

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Storage Architecture](#storage-architecture)
- [NFS Server Configuration](#nfs-server-configuration)
- [CSI Driver Installation](#csi-driver-installation)
- [Storage Class Definitions](#storage-class-definitions)
- [PVC Examples](#pvc-examples)
- [Performance Tuning](#performance-tuning)
- [Volume Snapshots](#volume-snapshots)
- [Monitoring](#monitoring)
- [Best Practices](#best-practices)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Trace the PVC → StorageClass → CSI provisioner → PV chain and say what each of the three StorageClasses in this lesson customizes
- Export an NFS share for the provisioner (root squashing off, fsid=0) and verify it with showmount from a K3s node
- Install csi-driver-nfs with Helm and define nfs-standard / nfs-fast / nfs-archive yourself - the chart creates no StorageClass by default
- Pick onDelete, reclaimPolicy, and volumeBindingMode per workload: Delete+Immediate for scratch, Retain for weights, WaitForFirstConsumer for archives
- Reason through mount options - rsize/wsize caps, sync vs async, hard vs soft with timeo/retrans, NFS 4.2 vs 4.1 - and their throughput/durability trade-offs
- Enable the snapshot-controller chart value, take a VolumeSnapshot of the model-cache PVC, and alert at 90% full via kubelet_volume_stats

---

## Abstract
Dynamic storage provisioning enables automatic creation of persistent volumes on demand. This document covers configuring K3s to dynamically provision NFS storage from any NFS server - a NAS appliance or a plain Linux box with an exported directory.

## Storage Architecture

### Storage Hierarchy
```text
┌─────────────────────────────────────────────────────────┐
│                    K3s Storage Layer                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  PVC (Persistent Volume Claim)                          │
│    "I need 10Gi of fast storage"                        │
│           ↓                                             │
│  StorageClass                                           │
│    "Use nfs-fast for this claim"                        │
│           ↓                                             │
│  Provisioner                                           │
│    "Create subdirectory on the NFS server"              │
│           ↓                                             │
│  PV (Persistent Volume)                                 │
│    "192.168.1.100:/srv/k8s-storage/pvc-abc123"          │
│           ↓                                             │
│  Physical Storage                                       │
│    NFS server (any RAID-capable NAS or Linux host)      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## NFS Server Configuration

Any machine that runs an NFS server works: a NAS appliance (configure shares and exports through its web UI, following its documentation) or a plain Linux box as shown below.

### Install the NFS Server (Linux)
```bash
# Debian/Ubuntu
apt install nfs-kernel-server

# RHEL/Fedora
dnf install nfs-utils
```

### Create and Export a Directory
```bash
# One directory is enough - the CSI driver creates a per-PVC
# subdirectory under the share automatically:
mkdir -p /srv/k8s-storage
```

### Configure Export
Edit `/etc/exports`:
```text
/srv/k8s-storage \
  192.168.1.0/24(rw,async,no_root_squash,no_subtree_check,fsid=0)
```

Apply and verify:
```bash
exportfs -ra
exportfs -v
```

On a NAS appliance the same settings exist as checkboxes/share permissions: enable NFS service, export the share to 192.168.1.0/24 with root squashing disabled for the provisioner to work.

### Verify
```bash
# From K3s node
showmount -e 192.168.1.100

# Expected output:
# /srv/k8s-storage 192.168.1.0/24
```

## CSI Driver Installation

### NFS CSI Driver
```bash
# Add the official chart repo and install the driver. The chart
# creates no StorageClass by default - this lesson defines its own
# three classes below (nfs-standard / nfs-fast / nfs-archive):
helm repo add csi-driver-nfs \
  https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs \
  --namespace kube-system

# Verify the driver pods are running:
kubectl -n kube-system get pod -o wide -l app=csi-nfs-controller
kubectl -n kube-system get pod -o wide -l app=csi-nfs-node
```

### Why Not the Legacy Provisioner?
An older non-CSI option, `nfs-subdir-external-provisioner`
(registry.k8s.io/sig-storage/nfs-subdir-external-provisioner), still
works but predates the CSI volume model: no VolumeSnapshots and no
volume expansion (attempting one fails with "didn't find a plugin
capable of expanding the volume"). The CSI driver above is the
maintained path and is what this lesson uses - it is also the
provisioner the 1301 StorageClass (`nfs.csi.k8s.io`) points at.

## Storage Class Definitions

### Standard Class (General Purpose)
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-standard
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: nfs.csi.k8s.io
parameters:
  server: 192.168.1.100
  share: /srv/k8s-storage
  onDelete: delete         # Remove the PVC's subdirectory when the PVC is deleted
reclaimPolicy: Delete
volumeBindingMode: Immediate
mountOptions:
  - hard
  - nfsvers=4.2
  - noatime
  - rsize=1048576           # 1MB read size
  - wsize=1048576           # 1MB write size
```

### Fast Class (for Model Weights)
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-fast
provisioner: nfs.csi.k8s.io
parameters:
  server: 192.168.1.100
  share: /srv/k8s-storage
  onDelete: retain         # Keep the subdirectory's data when the PVC is deleted
reclaimPolicy: Retain      # Keep the PV object itself too
volumeBindingMode: Immediate
mountOptions:
  - hard
  - nfsvers=4.2
  - noatime
  - sync                    # Write-through (slower but safer)
  - rsize=1048576
  - wsize=1048576
```

### Archive Class (for Datasets)
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-archive
provisioner: nfs.csi.k8s.io
parameters:
  server: 192.168.1.100
  share: /srv/k8s-storage
  onDelete: archive        # Move data aside instead of deleting it
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer  # Bind at pod schedule time
mountOptions:
  - hard
  - nfsvers=4.1            # More stable for large files
  - noatime
  - async                  # Faster writes
```

## PVC Examples

### Model Cache PVC
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache
  namespace: ai-services
spec:
  storageClassName: nfs-fast
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
```

### Training Data PVC
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: training-data
  namespace: ai-training
spec:
  storageClassName: nfs-standard
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 500Gi
```

### Output PVC
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-output
  namespace: ai-training
spec:
  storageClassName: nfs-standard
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

## Performance Tuning

### NFS Tuning Parameters
```yaml
mountOptions:
  # Block size
  - rsize=1048576           # Read chunk size (1MB = 2^20)
  - wsize=1048576           # Write chunk size

  # Caching (noac is just actimeo=0 + page-cache bypass; one line is enough)
  - actimeo=0              # Attribute cache timeout (0 = disable)

  # Write behavior - mutually exclusive, pick ONE
  - sync                   # Write-through (safer, slower)
  # - async                # Write-back (faster, risk of data loss)

  # Connection - mutually exclusive, pick ONE
  - hard                   # Hard mount (retry forever)
  # - soft                 # Soft mount (timeout after retrans)
  - timeo=600              # Timeout (deciseconds, 600 = 60s)
  - retrans=2              # Retries before timeout

  # Protocol version - pick one
  - nfsvers=4.2            # NFS 4.2 (latest features)
  # - nfsvers=4.1          # NFS 4.1 (older, widely compatible)
```

### Filesystem Considerations
```text
The NFS server's local filesystem affects behavior; any of these work:

ext4 / xfs : Simple, fast, boring (recommended default)
ZFS        : Snapshots, compression (lz4/zstd), checksumming
Btrfs      : Snapshots, compression, copy-on-write

Tuning for AI workloads:
- Disable per-share snapshots on high-churn directories (checkpoints)
- Enable transparent compression for model weights (they compress well)
- RAID-1/10 gives read throughput; RAIDZ/5 trades writes for capacity
- An SSD cache tier helps random reads during many small model loads
```

## Volume Snapshots

### Snapshot Integration
```bash
# Kubernetes-side snapshots need the snapshot CRDs and a
# snapshot-controller. The csi-driver-nfs chart can deploy one:
helm upgrade csi-driver-nfs csi-driver-nfs/csi-driver-nfs \
  --namespace kube-system \
  --reuse-values \
  --set externalSnapshotter.enabled=true

# Snapshot on the server (ZFS example):
zfs snapshot tank/k8s-storage@model-snapshot

# Btrfs example:
btrfs subvolume snapshot /srv/k8s-storage /srv/k8s-storage/.snapshots/model-snapshot
```

### Snapshot Class
```yaml
# There is no kubectl create subcommand for snapshots - declare a
# VolumeSnapshot object (same namespace as the source PVC):
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: nfs-snapshot
driver: nfs.csi.k8s.io
deletionPolicy: Delete
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: model-snapshot
  namespace: ai-services
spec:
  volumeSnapshotClassName: nfs-snapshot
  source:
    persistentVolumeClaimName: model-cache  # the PVC from PVC Examples
```

## Monitoring

### Storage Metrics
```promql
# PV usage
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes

# NFS performance
rate(node_nfs_rpc_retransmissions_total[5m])

# Disk I/O
rate(node_disk_io_time_seconds_total[5m])
```

### Alerting
```yaml
# Prometheus alert
- alert: PVCNearlyFull
  expr: |
    kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "PVC {{ $labels.persistentvolumeclaim }} is 90% full"
```

## Best Practices

### 1. Use ReadWriteMany When Possible
```text
Multiple pods can access the same PVC
Essential for:
- Model serving (all pods read same weights)
- Training (multiple workers read same dataset)
```

### 2. Separate Hot and Cold Data
```text
Hot data (models, active datasets):  Use fast class with SSD cache
Cold data (archives, logs):          Use standard class
```

### 3. Cap PVC Sizes with a LimitRange
```yaml
# A PVC has no resources.limits field - to cap how big a claim can be,
# put a LimitRange in the namespace. It bounds the REQUESTED size at
# claim time (NFS itself cannot enforce per-volume usage quotas):
apiVersion: v1
kind: LimitRange
metadata:
  name: storage-cap
  namespace: ai-training
spec:
  limits:
  - type: PersistentVolumeClaim
    max:
      storage: 50Gi
    min:
      storage: 1Gi
```

### 4. Use Volume Claim Templates
```yaml
# StatefulSet auto-creates PVCs
volumeClaimTemplates:
- metadata:
    name: data
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: nfs-fast
    resources:
      requests:
        storage: 10Gi
```

---

## Summary

Dynamic provisioning lets a pod ask for storage and get it: a PVC states the need, a StorageClass names the provisioner, and the CSI driver creates the volume on demand. This lesson configured exactly that against NFS - server setup, CSI driver installation, StorageClass definitions, and PVC examples - then the operational layers: performance tuning, volume snapshots, monitoring, and best practices. The rule it leaves: any NFS server becomes cluster storage, and the StorageClass is the single point where speed, reclaim policy, and default-ness are decided.

## References

### Related PROJECT-OMEGA Documents

- [1301: K3s Master-Worker Architecture](1301-K3s-Master-Worker-Arch.md)
- [1302: GPU Scheduler Configuration](1302-GPU-Scheduler.md)

---

## Next Steps

- Next Module: **[1400: LLMOps](../1400-llmops/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1301: K3s Master-Worker Architecture](./1301-K3s-Master-Worker-Arch.md)
- [1401: Ollama Enterprise Deployment](../1400-llmops/1401-Ollama-Enterprise.md)
- [6101: HNSW Indexing - Efficient Semantic Search at Scale](../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)

