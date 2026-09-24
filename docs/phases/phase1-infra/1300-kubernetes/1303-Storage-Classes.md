---
Document ID: 1303
Title: Storage Classes for Dynamic Provisioning
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

# 1303: Storage Classes for Dynamic Provisioning

## Abstract
Dynamic storage provisioning enables automatic creation of persistent volumes on demand. This document covers configuring K3s to dynamically provision NFS storage from the Synology DS720+.

## Storage Architecture

### Storage Hierarchy
```
┌─────────────────────────────────────────────────────────┐
│                    K3s Storage Layer                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  PVC (Persistent Volume Claim)                          │
│    "I need 10Gi of fast storage"                        │
│           ↓                                             │
│  StorageClass                                           │
│    "Use synology-nfs-fast for this claim"               │
│           ↓                                             │
│  Provisioner                                           │
│    "Create NFS share on Synology"                       │
│           ↓                                             │
│  PV (Persistent Volume)                                 │
│    "192.168.1.100:/volume1/k3s/pvc-abc123"              │
│           ↓                                             │
│  Physical Storage                                       │
│    Synology DS720+ (RAID-1 Btrfs)                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Synology NFS Configuration

### Enable NFS Service
```
Control Panel → File Services → NFS
Enable NFS Service: ON
```

### Create NFS Share
```bash
# SSH into Synology
ssh admin@192.168.1.100

# Create directory
mkdir -p /volume1/k8s-storage/{models,data,output}

# Set permissions
chmod 777 /volume1/k8s-storage
```

### Configure Export
```bash
# Edit /etc/exports
/volume1/k8s-storage \
  192.168.1.0/24(rw,async,no_root_squash,no_subtree_check,crossmnt,fsid=0)

# Reload exports
/usr/syno/etc/rc.sysv/nfsd restart
# or
exportfs -ra
```

### Verify
```bash
# From K3s node
showmount -e 192.168.1.100

# Expected output:
# /volume1/k8s-storage 192.168.1.0/24
```

## CSI Driver Installation

### NFS CSI Driver
```bash
# Add Helm repo
helm repo add csi-driver-nfs \
  https://raw.githubusercontent.com/kubernetes-sigs/nfs-subdir-external-provisioner/master/deploy/charts

# Install
helm install csi-driver-nfs csi-driver-nfs/nfs-subdir-external-provisioner \
  --namespace kube-system \
  --set nfs.server=192.168.1.100 \
  --set nfs.path=/volume1/k8s-storage \
  --set storageClass.default=true \
  --set storageClass.name=synology-nfs
```

### Alternative: Manual Provisioner
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nfs-client-provisioner
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nfs-client-provisioner
  template:
    metadata:
      labels:
        app: nfs-client-provisioner
    spec:
      serviceAccountName: nfs-client-provisioner
      containers:
      - name: nfs-client-provisioner
        image: registry.k8s.io/sig-storage/nfs-subdir-external-provisioner:v4.0.2
        volumeMounts:
        - name: nfs-client-root
          mountPath: /persistentvolumes
        env:
        - name: PROVISIONER_NAME
          value: k8s-sigs.io/nfs-subdir-external-provisioner
        - name: NFS_SERVER
          value: 192.168.1.100
        - name: NFS_PATH
          value: /volume1/k8s-storage
      volumes:
      - name: nfs-client-root
        nfs:
          server: 192.168.1.100
          path: /volume1/k8s-storage
```

## Storage Class Definitions

### Standard Class (General Purpose)
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: synology-nfs-standard
provisioner: k8s-sigs.io/nfs-subdir-external-provisioner
parameters:
  archiveOnDelete: "false"  # Keep data after PVC deletion
reclaimPolicy: Delete       # or Retain
volumeBindingMode: Immediate
allowVolumeExpansion: true
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
  name: synology-nfs-fast
provisioner: k8s-sigs.io/nfs-subdir-external-provisioner
parameters:
  archiveOnDelete: "false"
reclaimPolicy: Retain        # Keep data
volumeBindingMode: Immediate
allowVolumeExpansion: true
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
  name: synology-nfs-archive
provisioner: k8s-sigs.io/nfs-subdir-external-provisioner
parameters:
  archiveOnDelete: "true"   # Archive on delete
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer  # Bind at pod schedule time
allowVolumeExpansion: true
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
  storageClassName: synology-nfs-fast
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
  storageClassName: synology-nfs-standard
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
  storageClassName: synology-nfs-standard
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

  # Caching
  - noac                   # No attribute cache (force fresh reads)
  - actimeo=0              # Attribute cache timeout (0 = disable)

  # Write behavior
  - sync                   # Write-through (safer, slower)
  - async                  # Write-back (faster, risk of data loss)

  # Connection
  - hard                   # Hard mount (retry forever)
  - soft                   # Soft mount (timeout after retrans)
  - timeo=600              # Timeout (deciseconds, 600 = 60s)
  - retrans=2              # Retries before timeout

  # Protocol version
  - nfsvers=4.2            # NFS 4.2 (latest features)
  - nfsvers=4.1            # NFS 4.1 (more stable)
```

### Btrfs Considerations
```
Synology DS720+ uses Btrfs (if configured)

Advantages:
- Snapshots
- Compression (zstd, lzo)
- Self-healing (RAID-1)
- Copy-on-write

Tuning for AI workloads:
- Disable snapshots for high-churn directories
- Enable compression for model weights
- Use SSD cache if available
```

## Volume Snapshots

### Synology Snapshot Integration
```bash
# Create snapshot from Synology
synoshare --snapshot synology-nfs take k3s-models

# From Kubernetes
kubectl create snapshotvolumesnapshot model-snapshot \
  --source=model-cache-pvc
```

### Snapshot Class
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: synology-nfs-snapshot
driver: csi.nfs.com
deletionPolicy: Delete
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
```
Multiple pods can access the same PVC
Essential for:
- Model serving (all pods read same weights)
- Training (multiple workers read same dataset)
```

### 2. Separate Hot and Cold Data
```
Hot data (models, active datasets):  Use fast class with SSD cache
Cold data (archives, logs):          Use standard class
```

### 3. Set Resource Limits
```yaml
# Prevent runaway storage consumption
resources:
  requests:
    storage: 10Gi
  limits:
    storage: 50Gi  # Reject writes above 50Gi
```

### 4. Use Volume Claim Templates
```yaml
# StatefulSet auto-creates PVCs
volumeClaimTemplates:
- metadata:
    name: data
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: synology-nfs-fast
    resources:
      requests:
        storage: 10Gi
```

---

## Next Steps

- Next Module: **[1400: LLMOps](../1400-llmops/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1301: K3s Architecture](./1301-K3s-Master-Worker-Arch.md)
- [1401: Ollama Enterprise](../1400-llmops/1401-Ollama-Enterprise.md)
- [6101: HNSW Indexing](../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)

**Experiment Template:** `experiments/EXP_1303_STORAGE.md`
