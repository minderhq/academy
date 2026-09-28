---
Document ID: 1200-VIRTUALIZATION-README
Title: "1200: Virtualization and GPU Passthrough"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Beginner
---

# 1200: Virtualization and GPU Passthrough

## Module Overview

This module covers virtualization technologies and GPU passthrough configurations essential for running LLM workloads in virtualized environments. You'll learn how to set up Proxmox VE, configure GPU passthrough, and optimize VMs for maximum LLM performance.

## Why Virtualization Matters for LLMs

### 1. Resource Isolation

**Problem Solved:**
```text
Without Virtualization:
├── Host OS runs everything
├── Model A crashes → entire system unstable ❌
├── Model B needs different CUDA version → conflict ❌
└── Hard to manage dependencies

With Virtualization:
├── Each model in isolated VM
├── Model A crashes → other VMs unaffected ✅
├── Each VM has own CUDA/driver version ✅
└── Easy dependency management
```

**Real-World Example:**
```yaml
Setup: 4x RTX 4090, Proxmox host
VM Configuration:
  VM-100: Llama-3-70B, CUDA 12.1, 2x GPU
  VM-101: Stable Diffusion XL, CUDA 11.8, 1x GPU
  VM-102: Whisper Large, CUDA 12.2, 1x GPU
Benefits:
  - Each VM optimized for its workload
  - Independent updates
  - Resource quotas enforced
  - Crash isolation
```

### 2. GPU Passthrough Performance

**Performance Comparison:**

| Configuration | GPU Utilization | Memory Bandwidth | Latency |
|---------------|-----------------|------------------|---------|
| **Native (Bare Metal)** | 100% | 100% | Baseline |
| **VM without Passthrough** | 0% (software rendering) | 0% | N/A |
| **VM with VGPU (virtual)** | 70-85% | 70-85% | +5-10% |
| **VM with Passthrough** | 98-100% | 98-100% | +1-2% |

**Key Insight:**
```text
GPU Passthrough = Near-native performance
Overhead: <2% for most workloads
Cost: Slight complexity increase
Benefit: Full isolation + flexibility
```

### 3. Flexibility & Migration

**Scenario 1: Hardware Upgrade**
```yaml
Before: Need to upgrade GPU driver
  - Stop all services ❌
  - Update host driver ❌
  - Hope nothing breaks ❌
  - Restart everything ❌

After with VMs:
  - Migrate VM to another host (live migration) ✅
  - Update driver on empty host ✅
  - Migrate VM back ✅
  - Zero downtime ✅
```

**Scenario 2: Load Balancing**
```yaml
Auto-migration based on load:
Host A (4x GPU):
  - Load: 95% → Trigger migration
  - Move VM-100 to Host B
  - Result: Both hosts at ~70%

Benefits:
  - Dynamic resource allocation
  - Automated load balancing
  - Energy savings (turn off idle hosts)
```

### 4. Cost Efficiency

**Hardware Utilization:**
```text
Without Virtualization:
├── Server 1: Running Llama-3-70B (2x GPU)
├── Server 2: Running training (4x GPU)
├── Server 3: Running inference (2x GPU)
└── Server 4: Idle (wasted) ❌
Total: 4 servers, 8 GPUs

With Virtualization:
├── Host-1 (4x GPU):
│   ├── VM-100: Llama-3-70B (2x GPU)
│   ├── VM-101: Training (1x GPU)
│   └── VM-102: Inference (1x GPU)
└── Host-2 (4x GPU):
    ├── VM-103: Backup inference (2x GPU)
    └── Available: 2x GPU for experiments
Total: 2 servers, 8 GPUs (50% hardware savings!)
```

## Virtualization Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                      Hardware Layer                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │
│  │ GPU 0   │ │ GPU 1   │ │ GPU 2   │ │ GPU 3   │             │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘             │
└───────┼──────────┼──────────┼──────────┼─────────────────────┘
        │          │          │          │
┌───────┴──────────┴──────────┴──────────┴─────────────────────┐
│                    Proxmox VE Host                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Hypervisor (KVM)                                   │    │
│  │  - Memory management                                │    │
│  │  - CPU scheduling                                   │    │
│  │  - I/O handling                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  VFIO    │  │  VFIO    │  │  VFIO    │  │  VFIO    │   │
│  │  GPU 0   │  │  GPU 1   │  │  GPU 2   │  │  GPU 3   │   │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘   │
└────────┼────────────┼────────────┼────────────┼────────────┘
         │            │            │            │
┌────────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────────┐
│  VM-100     │  │ VM-101  │  │ VM-102  │  │ VM-103      │
│ ┌──────────┐│  │┌───────┐│  │┌───────┐│  │┌──────────┐│
│ │Guest OS  ││  ││Guest  ││  ││Guest  ││  ││Guest OS  ││
│ │CUDA 12.1 ││  ││CUDA   ││  ││CUDA   ││  ││CUDA 11.8 ││
│ │Llama-3   ││  ││Stable ││  ││Whisp  ││  ││Falcon    ││
│ │Passthrough│ │ ││Passth ││  ││Pass  ││  ││Passthrough││
│ └──────────┘│  │└───────┘│  │└───────┘│  │└──────────┘│
└─────────────┘  └─────────┘  └─────────┘  └─────────────┘
```

## Hypervisor Options for LLMs

### Proxmox VE (Recommended)

**Pros:**
```yaml
✅ Native GPU passthrough support
✅ ZFS built-in (for fast storage)
✅ Web GUI + CLI
✅ Live migration
✅ Backup/snapshot integration
✅ Open source (free)
✅ Debian-based (familiar)
✅ Large community
```

**Cons:**
```yaml
❌ Steep learning curve
❌ Requires dedicated hardware (typically)
❌ GPU passthrough setup complex
```

**Best For:**
- Production deployments
- Multi-GPU systems
- Users comfortable with Linux CLI

### KVM/QEMU (Manual Setup)

**Pros:**
```yaml
✅ Maximum flexibility
✅ No overhead of web GUI
✅ Can run on any Linux distro
✅ Fine-grained control
```

**Cons:**
```yaml
❌ Manual configuration required
❌ No built-in management interface
❌ Complex XML/libvirt configs
```

**Best For:**
- Advanced users
- Custom deployments
- Learning hypervisor internals

### VMware ESXi

**Pros:**
```yaml
✅ Enterprise features
✅ Excellent management UI
✅ Robust support
✅ Wide hardware compatibility
```

**Cons:**
```yaml
❌ Expensive (paid license required for GPU passthrough)
❌ Consumer GPU passthrough limited
❌ Less flexible than KVM
❌ Not open source
```

**Best For:**
- Enterprise environments
- Users with budget for licenses
- Teams needing commercial support

### Xen

**Pros:**
```yaml
✅ High security (type 1 hypervisor)
✅ Good paravirtualization support
✅ Used by major cloud providers
```

**Cons:**
```yaml
❌ Steeper learning curve
❌ Less community support than KVM
❌ GPU passthrough more complex
```

**Best For:**
- Security-focused deployments
- Cloud-like infrastructure

## Quick Start Guide

### Step 1: Hardware Requirements

**Minimum for Learning:**
```yaml
CPU:
  - Intel: VT-x enabled (4th Gen or newer)
  - AMD: AMD-V (Ryzen or newer)
  - Cores: 4+ (8+ recommended)

RAM:
  - 16 GB (32 GB recommended)
  - DDR4/DDR5

GPU:
  - Any NVIDIA GPU (Kepler or newer)
  - AMD GPUs supported but less ideal for LLMs

Storage:
  - 100 GB SSD
  - 500 GB recommended
```

**Recommended for Production:**
```yaml
CPU:
  - Intel: Xeon or Core i9 (VT-d supported)
  - AMD: EPYC or Ryzen 9 (SVM supported)
  - Cores: 16+ (32+ for multiple VMs)

RAM:
  - 128 GB (256 GB+ for multiple VMs)
  - ECC recommended

GPU:
  - 2-4x NVIDIA GPUs (same model recommended)
  - NVLink support (for multi-GPU)

Storage:
  - 1 TB+ NVMe SSD
  - ZFS RAID recommended
```

### Step 2: Install Proxmox VE

**Download:**
```bash
# Download from official site
https://www.proxmox.com/en/downloads

# Create bootable USB
ventoy -> Copy ISO to USB

# Boot from USB and install
Follow graphical installer
```

**Post-Install Configuration:**
```bash
# Update system
apt update && apt dist-upgrade -y

# Enable no-subscription repository (optional)
nano /etc/apt/sources.list.d/pve-no-subscription.list

# Add GPU passthrough prerequisites
apt install -y \
  vfio \
  iommu=pt \
  intel_iommu=on \
  initramfs
```

### Step 3: Enable IOMMU

**For Intel CPUs:**
```bash
# Edit GRUB
nano /etc/default/grub

# Add to GRUB_CMDLINE_LINUX_DEFAULT
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"

# Update GRUB
update-grub
update-initramfs -u

# Reboot
reboot
```

**For AMD CPUs:**
```bash
# Edit GRUB
nano /etc/default/grub

# Add to GRUB_CMDLINE_LINUX_DEFAULT
GRUB_CMDLINE_LINUX_DEFAULT="quiet amd_iommu=on iommu=pt"

# Update GRUB
update-grub
update-initramfs -u

# Reboot
reboot
```

### Step 4: Verify IOMMU

```bash
# Check IOMMU is enabled
dmesg | grep -e IOMMU -e AMD-Vi -e DMAR

# Expected output (Intel):
# DMAR: IOMMU enabled
# pci 0000:00:00.0: Adding to iommu group 0

# Expected output (AMD):
# AMD-Vi: IOMMU enabled

# List IOMMU groups
find /sys/kernel/iommu_groups/ -type l
```

### Step 5: Configure GPU Passthrough

**Step 5.1: Blacklist Nouveau (if using NVIDIA)**
```bash
# Create blacklist file
nano /etc/modprobe.d/blacklist-nouveau.conf

# Add:
blacklist nouveau
options nouveau modeset=0

# Update initramfs
update-initramfs -u
```

**Step 5.2: Load VFIO Modules**
```bash
# Add modules to load
echo "vfio" >> /etc/modules
echo "vfio_iommu_type1" >> /etc/modules
echo "vfio_pci" >> /etc/modules
echo "vfio_virqfd" >> /etc/modules

# Update initramfs
update-initramfs -u
```

**Step 5.3: Find GPU IDs**
```bash
# List all GPUs
lspci -nnk | grep -A 3 VGA

# Example output:
# 01:00.0 VGA compatible controller [0300]: NVIDIA Corporation ...
# Subsystem: ...
# Kernel driver in use: nvidia
# Kernel modules: nvidia

# Note the GPU ID (e.g., 10de:2204)
lspci -nn | grep NVIDIA
```

**Step 5.4: Bind GPU to VFIO**
```bash
# Edit VFIO config
nano /etc/modprobe.d/vfio.conf

# Add GPU IDs (replace with your IDs)
options vfio-pci ids=10de:2204,10de:2205

# Update initramfs
update-initramfs -u
reboot
```

**Step 5.5: Verify VFIO Binding**
```bash
# After reboot, check GPU driver
lspci -nnk | grep -A 3 VGA

# Expected output:
# 01:00.0 VGA compatible controller: NVIDIA ...
# Kernel driver in use: vfio-pci ✅
# Kernel modules: vfio-pci
```

## Common Virtualization Pitfalls

### ❌ Pitfall 1: Wrong IOMMU Configuration

**Problem:**
```yaml
Symptoms:
- VM won't start with GPU
- Error: "Failed to assign device"
- GPU works on host but not in VM

Root Cause:
- IOMMU not enabled in BIOS
- Wrong kernel parameters
- CPU doesn't support VT-d/AMD-Vi
```

**Solution:**
```bash
# Check BIOS settings
# Intel: Look for "VT-d" or "Intel Virtualization Technology for Directed I/O"
# AMD: Look for "SVM" or "AMD IOMMU"

# Verify kernel parameters
cat /proc/cmdline | grep iommu

# Should see:
# intel_iommu=on iommu=pt (Intel)
# OR
# amd_iommu=on iommu=pt (AMD)
```

### ❌ Pitfall 2: GPU Other Resources Not Passed Through

**Problem:**
```yaml
Symptoms:
- VM boots with GPU
- No display output
- GPU shows up in VM but doesn't work

Root Cause:
- GPU audio function not passed through
- GPU USB controller not passed through
- GPU serial bus not passed through
```

**Solution:**
```text
# In Proxmox VM GUI:
1. Identify all GPU functions:
   lspci -nn | grep NVIDIA

2. Add all functions to VM config:
   - GPU: 01:00.0 (VGA)
   - Audio: 01:00.1 (Audio)
   - USB: 01:00.2 (USB)
   - Serial: 01:00.3 (Serial)

3. Set to "All Functions" in Proxmox GUI
```

### ❌ Pitfall 3: Memory/PCIe Bus Issues

**Problem:**
```text
Symptoms:
- Random VM crashes
- GPU disappears from VM
- "achine Check Exception" errors

Root Cause:
- PCIe ACS (Access Control Services) issues
- Memory mapping conflicts
- BIOS memory hole settings
```

**Solution:**
```bash
# Disable PCIe ACS
echo "options vfio-pci disable_acs_redirection=1" >> /etc/modprobe.d/vfio.conf

# Or patch ACS (advanced)
# See: https://patchwork.kernel.org/project/linux-pci/patch/

# Alternative: Use motherboard with proper ACS support
```

### ❌ Pitfall 4: Driver Conflicts

**Problem:**
```yaml
Symptoms:
- GPU works on host but not in VM
- VM crashes when loading GPU driver
- Multiple driver versions installed
```

**Solution:**
```bash
# Ensure host doesn't load NVIDIA driver
# Method 1: Blacklist (already done)
# Method 2: Uninstall host driver
apt remove nvidia-driver-*

# Method 3: Mask GPU from host
# Edit /etc/modprobe.d/vfio.conf
options vfio-pci ids=10de:2204,10de:2205 disable_vga=1
```

## Performance Optimization

### CPU Pinning

**What it does:**
```text
Without Pinning:
├── VM vCPUs can migrate between physical cores
├── Cache misses increase
└── Performance inconsistent ❌

With Pinning:
├── VM vCPUs locked to specific physical cores
├── Cache locality optimized
└── Performance consistent ✅
```

**Configuration (Proxmox GUI):**
```text
1. Select VM -> Hardware -> Processors
2. Set "CPU Type" to "host"
3. Enable "CPU Pinning"
4. Assign cores:
   VM-100 (4 vCPU):
     - Cores: 0,1,2,3 (physical)
     - NUMA: Same as GPU NUMA node
```

**Configuration (CLI):**
```bash
# Edit VM config
nano /etc/pve/qemu-server/100.conf

# Add CPU pinning
cpulimit: "4"
cpuunits: "1024"
vcpus: "4"
cores: "4"
numa: 1
args: -set device.host-pci.0.addr=02.0 -set device.host-pci.1.addr=02.1

# Pin vCPUs to physical cores
# Add to /etc/pve/lxc/100.conf
lxc.cgroup.cpuset.cpus = "0-3"
```

### Huge Pages

**Benefits:**
```text
Standard Pages (4KB):
├── More page table entries
├── More TLB misses
└── Lower performance ❌

Huge Pages (2MB/1GB):
├── Fewer page table entries
├── Fewer TLB misses
└── Better performance ✅

Performance gain: 5-15% for memory-intensive workloads
```

**Configuration:**
```bash
# Enable huge pages
echo "vm.nr_hugepages = 1024" >> /etc/sysctl.conf
sysctl -p

# Verify
cat /proc/meminfo | grep Huge
# HugePages_Total:    1024
# HugePages_Free:     1024

# Configure VM to use huge pages
# In Proxmox GUI: VM -> Memory -> "Huge Pages"
# Or in config:
memory: 32768
hugepages: 2
```

### Storage Optimization

**ZFS Setup for Best Performance:**
```bash
# Create ZFS pool with SSD
zpool create -f zpool /dev/nvme0n1

# Create dataset for VMs
zfs create -o mountpoint=/var/lib/vz zpool/vm

# Optimize for VMs
zfs set compression=lz4 zpool/vm
zfs set atime=off zpool/vm
zfs set recordsize=1M zpool/vm

# Enable ZIL (ZFS Intent Log) on SSD
zpool add zpool log /dev/nvme1n1
```

**Alternative: Use LVM with Caching**
```bash
# Setup LVM with fast cache
pvcreate /dev/nvme0n1  # Fast SSD
pvcreate /dev/sda      # Slow HDD

vgcreate vg0 /dev/nvme0n1 /dev/sda

# Create cached volume
lvcreate -L 500G -T vg0/pool
lvcreate -V 200G -T vg0/pool -n vm-100-disk-0

# Add cache
lvconvert --type cache --cachemode writeback \
  --cache-pool vg0/cache vg0/vm-100-disk-0
```

### Network Optimization

**Virtio vs. E1000:**
```text
E1000 (Emulated):
├── Emulated hardware
├── CPU overhead
└── ~1 Gbps max ❌

Virtio (Paravirtualized):
├── Optimized drivers
├── Minimal CPU overhead
└── 10+ Gbps ✅

Performance gain: 3-5x
```

**Configuration:**
```yaml
# In Proxmox GUI:
# VM -> Network -> Model: "VirtIO (paravirtualized)"

# Or in config:
net0: virtio=XX:XX:XX:XX:XX:XX,bridge=vmbr0,firewall=1

# Enable multiqueue for 10Gbps+
net0: virtio=XX:XX:XX:XX:XX:XX,bridge=vmbr0,queues=4
```

## Troubleshooting Guide

### Problem 1: VM Won't Start with GPU

**Symptoms:**
```text
Error: "KVM_VGIC: invalid vgic interrupt number"
Error: "Failed to assign device"
```

**Diagnosis:**
```bash
# Check IOMMU groups
find /sys/kernel/iommu_groups/ -type l -ls

# Check GPU status
lspci -nnk -d ::0300

# Check kernel logs
dmesg | grep -i vfio
```

**Solutions:**
1. **Ensure all GPU functions are passed through**
2. **Check BIOS IOMMU settings**
3. **Verify VFIO binding**
4. **Try legacy interrupt mode** (BIOS setting)

### Problem 2: Poor GPU Performance in VM

**Symptoms:**
```text
Expected: 50 tokens/sec
Actual: 5 tokens/sec ❌

GPU utilization: 30%
Memory usage: 20%
```

**Diagnosis:**
```bash
# Check for PCIe errors
dmesg | grep -i pcie

# Check power management
nvidia-smi -q -d POWER

# Check for throttling
nvidia-smi -q -d THERMAL
```

**Solutions:**
1. **Enable CPU pinning**
2. **Enable huge pages**
3. **Set VM to high priority**
4. **Check power limits in BIOS**
5. **Disable power management in VM**

### Problem 3: GPU Not Visible in VM

**Symptoms:**
```text
lspci in VM: No GPU found ✗
nvidia-smi: "Command not found"
```

**Diagnosis:**
```bash
# Check host GPU binding
lspci -nnk | grep -A 3 VGA

# Check VM config
cat /etc/pve/qemu-server/100.conf | grep hostpci

# Check QEMU logs
tail -f /var/log/qemu-server/100.log
```

**Solutions:**
1. **Verify VFIO binding on host**
2. **Check all GPU functions are added**
3. **Ensure ROM file is loaded (if needed)**
4. **Add QEMU GPU options** (if needed)

### Problem 4: VM Random Crashes

**Symptoms:**
```text
VM runs for minutes/hours then crashes
No clear error message
```

**Diagnosis:**
```bash
# Check for hardware errors
dmesg | grep -i "mce\|hardware error"

# Check memory
memtest86+  # Run from boot

# Check temperatures
sensors
```

**Solutions:**
1. **Test RAM with memtest86+**
2. **Check PSU capacity (GPU power spikes)**
3. **Disable power management in BIOS**
4. **Update BIOS/UEFI**
5. **Check for overclocking instability**

## Best Practices

### ✅ DO

1. **Use separate networks for management and data**
   ```yaml
   vmbr0: Management (SSH, Proxmox GUI)
   vmbr1: Data (VM traffic, storage)
   vmbr2: Storage (dedicated for iSCSI/NFS)
   ```

2. **Implement backup strategy**
   ```yaml
   Daily backups:
     - Incremental: Every 4 hours
     - Full: Weekly
   Retention:
     - Daily: 7 days
     - Weekly: 4 weeks
     - Monthly: 3 months
   ```

3. **Monitor VM performance**
   ```yaml
   Metrics to track:
     - CPU usage per VM
     - Memory usage per VM
     - GPU utilization
     - Disk I/O
     - Network I/O
   Tools:
     - Proxmox built-in graphs
     - Grafana + Prometheus
   ```

4. **Document your configuration**
   ```yaml
   Documentation should include:
     - VM IDs and purposes
     - GPU assignments
     - Network mappings
     - Backup schedules
     - Recovery procedures
   ```

5. **Test disaster recovery**
   ```yaml
   Monthly test:
     - Restore from backup
     - Verify GPU passthrough works
     - Test VM migration
     - Document issues
   ```

### ❌ DON'T

1. **Don't skip testing in non-production**
   ```yaml
   Bad idea:
     - Configure GPU passthrough in production VM first ❌

   Better approach:
     - Create test VM
     - Verify everything works
     - Then move to production
   ```

2. **Don't assign all resources to one VM**
   ```yaml
   Bad idea:
     - VM-100: All 4 GPUs ❌
     - No room for other VMs

   Better approach:
     - VM-100: 2 GPUs (production)
     - VM-101: 1 GPU (testing)
     - VM-102: 1 GPU (development)
   ```

3. **Don't ignore BIOS settings**
   ```yaml
   Critical BIOS settings:
     - VT-d/AMD-Vi: Enabled
     - Above 4G decoding: Enabled
     - Resizable BAR: Enabled (if supported)
     - Power management: Disabled (for max performance)
   ```

4. **Don't forget about updates**
   ```text
   Update schedule:
     - Proxmox: Monthly
     - Guest VMs: Monthly
     - GPU drivers: As needed
   Always test updates on non-production first
   ```

## Real-World Examples

### Example 1: Home LLM Server

```yaml
Hardware:
  CPU: Ryzen 9 5950X (16 cores)
  RAM: 128 GB DDR4
  GPU: 2x RTX 4090 (24 GB each)
  Storage: 2 TB NVMe SSD

Configuration:
  Host: Proxmox VE 8.1

  VM-100 (Llama-3-70B Inference):
    vCPU: 8
    RAM: 48 GB
    GPU: 1x RTX 4090
    Storage: 500 GB
    OS: Ubuntu 22.04 LTS
    CUDA: 12.1
    Model: Llama-3-70B (4-bit)

  VM-101 (Stable Diffusion):
    vCPU: 4
    RAM: 24 GB
    GPU: 1x RTX 4090
    Storage: 200 GB
    OS: Ubuntu 22.04 LTS
    CUDA: 11.8

  VM-102 (Development):
    vCPU: 4
    RAM: 32 GB
    GPU: None (software testing)
    Storage: 300 GB
    OS: Ubuntu 22.04 LTS

Performance:
  - Llama-3-70B: 25 tokens/sec
  - Stable Diffusion: 20 iterations/sec
  - Utilization: 85% avg

Cost:
  - Hardware: $6,000
  - Monthly: $100 (electricity)
```

### Example 2: Startup Production

```yaml
Hardware:
  Host 1:
    CPU: Dual Xeon Gold 6248 (48 cores)
    RAM: 384 GB ECC
    GPU: 4x A100 40 GB
    Storage: 4 TB NVMe (RAID 1)

  Host 2: (Same as Host 1)

Configuration:
  Proxmox Cluster: 2 nodes, 3rd as quorum witness

  Host-1 VMs:
    VM-100 (Production API):
      vCPU: 16
      RAM: 128 GB
      GPU: 2x A100
      Model: Fine-tuned Llama-3-70B

    VM-101 (Batch Processing):
      vCPU: 16
      RAM: 128 GB
      GPU: 2x A100
      Model: Custom 34B

  Host-2 VMs:
    VM-200 (Production API - Hot Standby):
      vCPU: 16
      RAM: 128 GB
      GPU: 2x A100
      Model: Fine-tuned Llama-3-70B

    VM-201 (Training):
      vCPU: 24
      RAM: 256 GB
      GPU: 4x A100
      Model: Training 7B from scratch

Features:
  - Live migration between hosts
  - Automatic failover
  - Hourly backups
  - Monitoring alerts
  - Load balancing

Performance:
  - Inference: 200 tokens/sec per user
  - Concurrent users: 500+
  - Training: 3 days for 7B model
  - Uptime: 99.9%

Cost:
  - Hardware: $200,000
  - Monthly: $5,000 (hosting)
```

## Learning Path

1. **[1201: Proxmox Hypervisor SOP](./1201-Proxmox-Hypervisor-SOP.md)** - Virtualization platform setup
2. **[1202: GPU Passthrough (IOMMU/VFIO)](./1202-TB3-UT3G-Passthrough.md)** - IOMMU/VFIO GPU passthrough
3. **[1203: Nvidia Kernel Modules](./1203-Nvidia-Kernel-Module.md)** - Driver configuration
4. **[1204: Multi-GPU Setup](./1204-Multi-GPU-Setup.md)** - Multiple GPU configuration

## Prerequisites

Before starting this module, ensure you understand:

### Basic Knowledge
- **Linux System Administration:** Command line, file system, package management
- **Hardware Virtualization:** What a hypervisor is, CPU virtualization extensions
- **GPU Architecture:** Basic GPU components, PCIe, memory
- **Networking:** IP addressing, bridges, VLANs

### Hardware Requirements
- **CPU:** Intel VT-x/VT-d or AMD-V/SVM support
- **RAM:** 16 GB minimum, 32 GB+ recommended
- **GPU:** At least one NVIDIA GPU (Kepler or newer)
- **Storage:** 100 GB SSD minimum

### Software Skills
- **Text Editor:** nano, vim, or similar
- **SSH:** Remote server access
- **Terminal:** Comfortable with bash commands

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

Validate your knowledge:

- **[assessment/QUIZ.md](./assessment/QUIZ.md)** - Test your understanding (20 questions, 80% to pass)
- **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** - Hands-on exercises

## Key Takeaways

After completing this module, you will be able to:

✅ **Understand virtualization fundamentals for LLMs**
   - Hypervisor types and when to use each
   - Resource isolation benefits
   - Cost optimization strategies

✅ **Deploy Proxmox VE for LLM workloads**
   - Installation and configuration
   - Network setup
   - Storage configuration

✅ **Configure GPU passthrough**
   - IOMMU setup
   - VFIO configuration
   - Multi-GPU setups

✅ **Optimize VM performance for LLMs**
   - CPU pinning for consistency
   - Huge pages for memory performance
   - Storage and network optimization

✅ **Troubleshoot virtualization issues**
   - IOMMU problems
   - GPU passthrough failures
   - Performance bottlenecks

✅ **Implement best practices**
   - Backup strategies
   - Monitoring setup
   - Disaster recovery

## Additional Resources

### Tools & Utilities

```bash
# Proxmox Management
qm                 # VM management
pct                # Container management
pvesm              # Storage management
pveum              # User management

# GPU Passthrough
lspci              # List PCI devices
lsmod              # List kernel modules
dmesg              # Kernel logs
virsh              # Virtualization shell (if using KVM)

# Testing
vainfo             # VA-API info
vulkaninfo         # Vulkan info
nvidia-smi         # NVIDIA GPU monitoring
```

### Further Reading

**Documentation:**
- [Proxmox VE Admin Guide](https://pve.proxmox.com/pve-docs/)
- [KVM Documentation](https://www.linux-kvm.org/page/Documents)
- [VFIO Documentation](https://www.kernel.org/doc/Documentation/vfio.txt)

**Books:**
- "KVM Virtualization Cookbook" by Konstantin Ivanov
- "Mastering Proxmox VE" by Rik Jaeger

**Online Courses:**
- [Proxmox VE Full Course](https://www.youtube.com/watch?v=ZEjO9g4l6Ww)
- [Linux Virtualization](https://www.redhat.com/en/topics/virtualization)

### Community Resources

**Forums:**
- [Proxmox Forums](https://forum.proxmox.com/)
- [r/Proxmox on Reddit](https://www.reddit.com/r/Proxmox/)
- [r/homelab](https://www.reddit.com/r/homelab/)

**GPU Passthrough Specific:**
- [Arch Wiki: PCIe Passthrough](https://wiki.archlinux.org/title/PCI_passthrough_via_OVMF)
- [Proxmox GPU Passthrough Guide](https://pve.proxmox.com/wiki/Pci_passthrough)

## Module Completion Checklist

```text
Understanding:
  - [ ] I can explain hypervisor types (Type 1 vs Type 2)
  - [ ] I understand IOMMU and VFIO
  - [ ] I know when to use GPU passthrough vs software GPU
  - [ ] I can calculate resource requirements for VMs

Practical Skills:
  - [ ] I have installed Proxmox VE
  - [ ] I have enabled IOMMU in BIOS and kernel
  - [ ] I have configured GPU passthrough
  - [ ] I have created a VM with passed-through GPU
  - [ ] I have optimized VM performance

Hardware:
  - [ ] My CPU supports VT-d/AMD-Vi
  - [ ] My motherboard supports IOMMU
  - [ ] I have adequate RAM for multiple VMs
  - [ ] My GPU is compatible with passthrough

Production Ready:
  - [ ] I have implemented backup strategy
  - [ ] I have configured monitoring
  - [ ] I have tested disaster recovery
  - [ ] I have documented my setup
```

## Glossary

| Term | Definition |
|------|------------|
| **Hypervisor** | Software that creates and runs virtual machines |
| **Type 1 Hypervisor** | Bare-metal hypervisor running directly on hardware (e.g., Proxmox) |
| **Type 2 Hypervisor** | Hosted hypervisor running on top of an OS (e.g., VirtualBox) |
| **IOMMU** | Input/Output Memory Management Unit - for device isolation |
| **VT-d/AMD-Vi** | Intel/AMD implementations of IOMMU |
| **VFIO** | Virtual Function I/O - secure device assignment |
| **PCI Passthrough** | Direct hardware access from VM to physical device |
| **GPU Passthrough** | Passing GPU through to VM for near-native performance |
| **vCPU** | Virtual CPU assigned to a VM |
| **NUMA** | Non-Uniform Memory Access - memory locality optimization |
| **Huge Pages** | Large memory pages (2MB/1GB) for better performance |
| **CPU Pinning** | Locking vCPUs to specific physical cores |
| **Live Migration** | Moving running VM between hosts without downtime |
| **ZFS** | Combined file system and logical volume manager |

---

**Module Duration:** 10-12 hours
**Difficulty:** Intermediate

**Ready to proceed?** Continue to [1201: Proxmox Hypervisor SOP](./1201-Proxmox-Hypervisor-SOP.md)
