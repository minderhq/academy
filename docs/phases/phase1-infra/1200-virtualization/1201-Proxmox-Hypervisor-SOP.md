---
Document ID: 1201
Title: Proxmox Hypervisor Standard Operating Procedures
Phase: 1
Module: 1200
Last Updated: 2026-09-25
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'virtualization', 'proxmox', 'gpu']
---

# 1201: Proxmox Hypervisor Standard Operating Procedures

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Hardware Requirements](#hardware-requirements)
- [Post-Installation Configuration](#post-installation-configuration)
- [CPU Pinning & NUMA Awareness](#cpu-pinning--numa-awareness)
- [Memory Management](#memory-management)
- [Storage Configuration](#storage-configuration)
- [GPU Passthrough Preparation](#gpu-passthrough-preparation)
- [VM Templates](#vm-templates)
- [Backup Strategy](#backup-strategy)
- [Monitoring](#monitoring)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Hardware Requirements
- Configure and operate Post-Installation Configuration
- Explain CPU Pinning & NUMA Awareness
- Explain Memory Management
- Configure and operate Storage Configuration
- Explain GPU Passthrough Preparation

---

## Abstract
Proxmox VE is the virtualization layer at the center of this infrastructure, hosting the K3s cluster and providing the platform for GPU passthrough to a single NVIDIA GPU.

## Hardware Requirements

### Reference Hardware

Any machine meeting these minimums works - a dedicated desktop, a mini PC, a repurposed server, or a cloud VM with PCI passthrough enabled:

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| CPU | x86_64 with VT-d (Intel) or AMD-Vi (AMD) | 8+ cores | IOMMU support is required for GPU passthrough |
| RAM | 16 GB | 32 GB+ | K3s VMs plus host overhead |
| GPU | None (CPU-only path works) | One NVIDIA GPU with 8GB+ VRAM | Passthrough-capable (see [1202](./1202-TB3-UT3G-Passthrough.md)) |
| Storage | 250 GB | 500 GB+ NVMe | ZFS prefers fast local disks |
| Network | 1 Gbps Ethernet | Multi-gig | Any wired NIC |

Virtualization extensions to confirm in BIOS/UEFI before installing: **VT-x** (Intel) or **SVM** (AMD), plus **VT-d** / **IOMMU** for passthrough.

### Proxmox Installation
```bash
# Download the latest ISO from https://www.proxmox.com/en/downloads
# (the filename changes with each release, e.g. proxmox-ve_8.3-1.iso)
wget https://download.proxmox.com/iso/proxmox-ve_8.3-1.iso

# Create bootable USB
dd if=proxmox-ve.iso of=/dev/sdX bs=4M status=progress

# Boot and install with ZFS
# Target: /dev/nvme0n1
# ZFS Configuration: RAID-1 (mirror) if dual NVMe available
```

## Post-Installation Configuration

### 1. Network Setup
```bash
# Edit /etc/network/interfaces - the host IP lives on the bridge;
# VMs attach to vmbr0 (see the VM template below)
iface eno1 inet manual

auto vmbr0
iface vmbr0 inet static
    address 192.168.1.10/24
    gateway 192.168.1.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    mtu 9000

# Apply changes
ifreload -a
```

### 2. Repository Configuration
```bash
# Remove enterprise repository (no subscription)
rm /etc/apt/sources.list.d/pve-enterprise.list

# Add no-subscription repository
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
  > /etc/apt/sources.list.d/pve-no-subscription.list

# Update
apt update && apt dist-upgrade -y
```

### 3. ZFS Tuning
```bash
# Enable ZFS compression
zfs set compression=lz4 rpool

# Adjust ARC max (example: 32GB cap on a 64GB host; budget ~50% of your RAM)
echo "options zfs zfs_arc_max=34359738368" >> /etc/modprobe.d/zfs.conf

# TXG timeout (seconds) - how long ZFS batches dirty data before
# committing. 5 is already the default; lower it (e.g. 1) to trade
# throughput for lower VM write latency
echo "options zfs zfs_txg_timeout=5" >> /etc/modprobe.d/zfs.conf

# Rebuild initramfs
update-initramfs -u
```

## CPU Pinning & NUMA Awareness

### CPU Topology Analysis
```bash
# Check CPU topology
lscpu -p=CPU,CORE,SOCKET

# Example output (any modern CPU): one line per logical CPU,
# listing CPU index, physical core, and socket. Uniform cores are
# the common case; heterogeneous (P/E-core) laptop CPUs need care.
```

### CPU Pinning Strategy
```text
VM 101 (K3s Master):  cores 0-3 (4 vCPU)
VM 102 (K3s Worker):  cores 4-7 (4 vCPU)
Host:                 all remaining cores
```

### VM CPU Configuration
```bash
# In Proxmox GUI or /etc/pve/qemu-server/101.conf
# (+hv-evmcs is Intel-only - remove that flag on AMD hosts)
cpu: host,hidden=0,flags=+hv-evmcs
cores: 4
sockets: 1
numa: 1
vcpus: 4

# CPU Pinning via hookscript
# 1. Enable snippets on the local storage (once per cluster):
pvesm set local --content iso,vztmpl,backup,snippets

# 2. Create the snippet:
cat > /var/lib/vz/snippets/vm-pinning.sh << 'EOF'
#!/bin/bash
VMID="$1"; ACTION="$2"
if [ "$ACTION" == "post-start" ]; then
  VMPID=$(cat /var/run/qemu-server/${VMID}.pid)
  taskset -pc 0-3 "$VMPID"
fi
EOF
chmod +x /var/lib/vz/snippets/vm-pinning.sh

# 3. Attach the hookscript to the VM (repeats on every start):
qm set 101 --hookscript local:snippets/vm-pinning.sh
```

## Memory Management

### Memory Ballooning
```bash
# Disable for K3s nodes (predictable memory needed)
# In VM config:
balloon: 0

# Set static memory
memory: 16384  # 16GB for K3s Master
```

### Huge Pages
```bash
# Reserve 16 x 1GiB huge pages (= 16 GiB - must fit in host RAM)
echo 16 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages

# Make persistent (applied at boot, before memory fragmentation)
echo "vm.nr_hugepages = 16" >> /etc/sysctl.conf

# Verify
cat /proc/meminfo | grep Huge
```

## Storage Configuration

### ZFS Dataset Layout
```text
rpool (ROOT)
├── rpool/ROOT (System)
├── rpool/data (VM storage)
├── rpool/images (Disk images)
└── rpool/backups (VM backups)
```

### Storage Pool Configuration
```bash
# Create storage for VM images
zfs create -o mountpoint=/var/lib/vz rpool/data
zfs create -o compression=lz4 -o sync=standard rpool/images

# Add to Proxmox storage
pvesm add zfspool rpool-images \
  --pool rpool/images \
  --content rootdir,images \
  --sparse 1

# Add backup storage (used by the backup section below)
zfs create rpool/backups
pvesm add zfspool rpool-backups \
  --pool rpool/backups \
  --content backup
```

## GPU Passthrough Preparation

### GPU Device Identification
```bash
# List NVIDIA devices and their PCI addresses
lspci -nn | grep -i nvidia

# Example output:
# 01:00.0 VGA compatible controller [10de:2503]: NVIDIA Corporation ...
# 01:00.1 Audio device [10de:228b]: NVIDIA Corporation ...
```

### IOMMU Configuration
```bash
# Edit /etc/default/grub
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"

# Update grub
update-grub

# Add VFIO modules
cat >> /etc/modules << EOF
vfio
vfio_pci
vfio_iommu_type1
EOF
```

## VM Templates

### K3s Master VM Template
```bash
# Create VM
qm create 101 \
  --name k3s-master \
  --memory 16384 \
  --cores 4 \
  --net0 virtio,bridge=vmbr0,mtu=9000 \
  --scsihw virtio-scsi-pci \
  --ostype l26

# Import cloud-init disk
qm importdisk 101 ubuntu-22.04-cloud.img rpool-images

# Attach disk
qm set 101 --scsi0 rpool-images:vm-101-disk-0

# Add cloud-init drive
qm set 101 --ide2 rpool-images:cloudinit

# Set boot order
qm set 101 --boot order=scsi0

# Enable QEMU guest agent
qm set 101 --agent enabled=1

# Convert to template
qm template 101
```

## Backup Strategy

### Automated Backups
```bash
# Root crontab (crontab -e). The Datacenter > Backup GUI is the
# managed alternative - it stores jobs in /etc/pve/jobs.cfg.

# Daily backup at 2AM, keep 7 (matches the retention policy below)
00 02 * * * vzdump 101 --storage rpool-backups \
  --mode snapshot --compress zstd --keep-last 7 \
  --mailnotification always

# Weekly backup of both VMs, Sunday 3AM, keep 4
00 03 * * 0 vzdump 101 102 \
  --storage rpool-backups \
  --mode snapshot \
  --compress zstd \
  --keep-last 4
```

### Backup Retention
```text
Daily:   Keep last 7 days
Weekly:  Keep last 4 weeks
Monthly: Keep last 3 months
```

## Monitoring

### Proxmox Metrics
```bash
# Export metrics to InfluxDB (creates the server entry; InfluxDB
# receives these over UDP port 8089)
pvesh create /cluster/metrics \
  --id influx-local \
  --type influxdb \
  --server 192.168.1.100 \
  --port 8089 \
  --influxdbproto udp
```

### Health Checks
```bash
# ZFS health
zpool status -x

# SMART monitoring
smartctl -a /dev/nvme0n1

# Temperature
sensors
```

---

## References

### Related ai-engineering-curriculum Documents

- [1202: GPU Passthrough (IOMMU/VFIO)](1202-TB3-UT3G-Passthrough.md)
- [1203: NVIDIA Kernel Module Management](1203-Nvidia-Kernel-Module.md)
- [1204: Multi-GPU Setup](1204-Multi-GPU-Setup.md)

---

## Next Steps

- Continue with: **[1202: GPU Passthrough (IOMMU/VFIO)](./1202-TB3-UT3G-Passthrough.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1202: GPU Passthrough (IOMMU/VFIO)](./1202-TB3-UT3G-Passthrough.md)
- [1203: NVIDIA Kernel Module Management](./1203-Nvidia-Kernel-Module.md)
- [1301: K3s Master-Worker Architecture](../1300-kubernetes/1301-K3s-Master-Worker-Arch.md)

