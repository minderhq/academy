---
Document ID: 1201
Title: Proxmox Hypervisor Standard Operating Procedures
Phase: 1
Module: 1200
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'virtualization', 'proxmox', 'gpu']
---

# 1201: Proxmox Hypervisor Standard Operating Procedures

## Abstract
Proxmox VE is the foundation of PROJECT-OMEGA's virtualization layer, hosting the K3s cluster and providing infrastructure for GPU passthrough to the NUC's RTX 2080 Ti.

## Hardware Architecture

### Intel NUC Specifications
```
Model: Intel NUC 12 Enthusiast (Serpent Canyon)
CPU:  i7-12700H (12 cores / 20 threads)
RAM:  64GB DDR5-4800 (2×32GB)
Storage: 2TB NVMe SSD
eGPU: RTX 2080 Ti via Thunderbolt 3
NIC: 2.5Gbps Ethernet
```

### Proxmox Installation
```bash
# Download latest ISO
wget https://enterprise.proxmox.com/iso/proxmox-ve_*.iso

# Create bootable USB
dd if=proxmox-ve.iso of=/dev/sdX bs=4M status=progress

# Boot and install with ZFS
Target: /dev/nvme0n1
ZFS Configuration: RAID-1 (mirror) if dual NVMe available
```

## Post-Installation Configuration

### 1. Network Setup
```bash
# Edit /etc/network/interfaces
auto eno1
iface eno1 inet static
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

# Adjust ARC max (use 50% of RAM)
echo "options zfs zfs_arc_max=34359738368" >> /etc/modprobe.d/zfs.conf

# Disable ZFS commit delay (better for VMs)
echo "options zfs zfs_txg_timeout=5" >> /etc/modprobe.d/zfs.conf

# Rebuild initramfs
update-initramfs -u
```

## CPU Pinning & NUMA Awareness

### CPU Topology Analysis
```bash
# Check CPU topology
lscpu -p=CPU,CORE,SOCKET

# Example output for i7-12700H:
# P-Cores: 6 (hyperthreaded = 12 threads)
# E-Cores: 8 (no hyperthreading)
# Total: 20 logical CPUs
```

### CPU Pinning Strategy
```
VM 101 (K3s Master):  P-Cores 0-3 (4 vCPU)
VM 102 (K3s Worker):  P-Cores 4-7 (4 vCPU)
Host:                 P-Cores 8-11 + All E-Cores
```

### VM CPU Configuration
```bash
# In Proxmox GUI or /etc/pve/qemu-server/101.conf
cpu: host,hidden=0,flags=+hv-evmcs
cores: 4
sockets: 1
numa: 1
vcpus: 4

# CPU Pinning via hooks
# /var/lib/vz/snippets/vm-pinning.sh
cat >> /etc/pve/qemu-server/101.conf << EOF
args: -set device virtio0.pci.0,addr=0x04
EOF
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
# Enable 1GB huge pages
echo 1024 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages

# Make persistent
echo "vm.nr_hugepages = 1024" >> /etc/sysctl.conf

# Verify
cat /proc/meminfo | grep Huge
```

## Storage Configuration

### ZFS Dataset Layout
```
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
```

## Thunderbolt 3 / eGPU Preparation

### TB3 Device Identification
```bash
# List TB3 devices
boltctl list

# Example output:
# o20: RTX 2080 Ti eGPU
#   Vendor: Razer
#   Sysfs: /sys/bus/thunderbolt/devices/0-20
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
# /etc/pve/vzdump.cron
# Daily backup at 2AM
00 02 * * * vzdump 101 --storage rpool-backups \
  --mode snapshot --compress zstd --mailnotification always

# Weekly full backup
00 03 * * 0 vzdump --all 101,102 \
  --storage rpool-backups \
  --mode snapshot \
  --compress zstd \
  --keep-last 4
```

### Backup Retention
```
Daily:   Keep last 7 days
Weekly:  Keep last 4 weeks
Monthly: Keep last 3 months
```

## Monitoring

### Proxmox Metrics
```bash
# Enable metrics export
pvesh set /cluster/metrics \
  --type influxdb \
  --server influx.local \
  --influxdb-server 192.168.1.100:8086 \
  --influxdb-protocol http
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

## Next Steps

- Continue with: **[1202: TB3 Passthrough](./1202-TB3-UT3G-Passthrough.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1202: TB3 Passthrough](./1202-TB3-UT3G-Passthrough.md)
- [1203: Nvidia Kernel Module](./1203-Nvidia-Kernel-Module.md)
- [1301: K3s Architecture](../1300-kubernetes/1301-K3s-Master-Worker-Arch.md)

**Experiment Template:** `experiments/EXP_1201_PROXMOX.md`
