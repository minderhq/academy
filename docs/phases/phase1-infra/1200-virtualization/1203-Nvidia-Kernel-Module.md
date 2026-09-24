---
Document ID: 1203
Title: NVIDIA Kernel Module Management
Phase: 1
Module: 1200
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'virtualization', 'proxmox', 'gpu']
---

# 1203: NVIDIA Kernel Module Management

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [NVIDIA Driver Architecture](#nvidia-driver-architecture)
- [Kernel Modules Explained](#kernel-modules-explained)
- [Installation Methods](#installation-methods)
- [Module Configuration](#module-configuration)
- [CUDA Memory Management](#cuda-memory-management)
- [Power Management](#power-management)
- [Driver Orchestration in Kubernetes](#driver-orchestration-in-kubernetes)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain NVIDIA Driver Architecture
- Explain Kernel Modules Explained
- Apply Installation Methods
- Configure and operate Module Configuration
- Explain CUDA Memory Management
- Explain Power Management

---

## Abstract
This document covers NVIDIA driver and kernel module management for an 11GB-class GPU in a passthrough environment. Proper module handling ensures GPU stability across reboots and kernel updates.

## NVIDIA Driver Architecture

### Component Stack
```text
┌─────────────────────────────────────────┐
│         User Space                      │
│  CUDA Toolkit, cuDNN, TensorRT          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         NVIDIA Driver (535.xx.x)        │
│  libnvidia-ml.so (nvidia-smi API)       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Kernel Modules                  │
│  nvidia.ko, nvidia-uvm.ko, nvidia-mig.ko│
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Hardware (11GB-class GPU)          │
└─────────────────────────────────────────┘
```

## Kernel Modules Explained

### Module Breakdown
```text
nvidia.ko           - Main driver module (4352 CUDA cores management)
nvidia-uvm.ko       - Unified Virtual Memory (for CUDA managed memory)
nvidia-mig.ko       - Multi-Instance GPU (not used on 11GB-class GPU)
nvidia-drm.ko       - Direct Rendering Manager (display output)
nvidia-peermem.ko   - Peer-to-peer memory (GPUDirect)
```

### Module Loading Order
```bash
# Critical load order
1. nvidia          # Core driver
2. nvidia-uvm      # Memory management
3. nvidia-drm      # Display (if needed)
4. nvidia-peermem  # Optional, for RDMA
```

## Installation Methods

### Method 1: DKMS (Dynamic Kernel Module Support)
```bash
# Install DKMS build dependencies
apt install dkms build-essential linux-headers-$(uname -r)

# Install NVIDIA driver with DKMS
apt install nvidia-driver-535

# DKMS rebuilds module on kernel update automatically
dkms status
# nvidia/535.154.05, 6.5.0-14-amd64, x86_64: installed
```

### Method 2: Package Manager (Ubuntu)
```bash
# Add graphics PPA
add-apt-repository ppa:graphics-drivers/ppa
apt update

# Install meta-package (tracks recommended version)
apt install nvidia-driver-535

# Check loaded modules
lsmod | grep nvidia
```

### Method 3: NVIDIA Runfile (For Specific Versions)
```bash
# Download from NVIDIA
wget https://download.nvidia.com/XFree86/Linux-x86_64/535.154.05/NVIDIA-Linux-x86_64-535.154.05.run

# Install with kernel module source
chmod +x NVIDIA-Linux-x86_64-*.run
./NVIDIA-Linux-x86_64-*.run --kernel-source-path /usr/src/linux-headers-$(uname -r)

# Don't install OpenGL (conflicts with mesa)
./NVIDIA-Linux-x86_64-*.run --no-opengl-files --kernel-source-only
```

## Module Configuration

### Blacklisting Nouveau
```bash
# Create blacklist
cat > /etc/modprobe.d/blacklist-nouveau.conf << EOF
blacklist nouveau
blacklist lbm-nouveau
options nouveau modeset=0
alias nouveau off
alias lbm-nouveau off
EOF

# Update initramfs
update-initramfs -u

# Reboot required
reboot

# Verify nouveau is not loaded
lsmod | grep nouveau  # Should return nothing
```

### Module Parameters
```bash
# Edit /etc/modprobe.d/nvidia.conf
options nvidia NVreg_EnableGpuFirmware=0
options nvidia NVreg_EnablePageRetirement=1
options nvidia NVreg_UsePageAttributeTable=1
options nvidia NVreg_EnableStreamMemOPs=1
options nvidia NVreg_EnableGpuFirmware=0
options nvidia NVreg_DynamicPowerManagement=0

# Explanation:
# EnablePageRetirement: Handle bad VRAM pages gracefully
# UsePageAttributeTable: Improved memory performance
# EnableStreamMemOPs: Enable CUDA stream operations
# DynamicPowerManagement: Disable for eGPU stability
```

### Persistence Mode
```bash
# Enable persistence (keeps driver loaded)
nvidia-smi -pm 1

# Make persistent across reboots
cat > /etc/systemd/system/nvidia-persistence.service << EOF
[Unit]
Description=NVIDIA Persistence Mode
After=syslog.target

[Service]
Type=oneshot
ExecStart=/usr/bin/nvidia-smi -pm 1
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl enable nvidia-persistence.service
```

## CUDA Memory Management

### Unified Memory (nvidia-uvm)
```yaml
Standard Memory:     CPU pointer → memcpy → GPU pointer
Unified Memory:      Single pointer accessible by CPU and GPU

Benefits:
- Automatic data migration
- Oversubscription (use more VRAM than available)
- Simplified code
```

### BAR1 Configuration
```bash
# Check BAR1 size (CPU-accessible GPU memory)
nvidia-smi -q | grep -A 3 "Bar1 Memory Usage"

# Increase BAR1 for better CPU↔GPU transfer
# Requires BIOS resizeable BAR support (SAM)
```

## Power Management

### Power States (P-States)
```bash
P0:  Maximum performance (all cores active)
P1-P8: Intermediate states
P8:  Minimum power (idle)

For eGPU, avoid P-state switching:
nvidia-smi -pl 250  # Set power limit to TDP
```

### Thermal Management
```bash
# Check current temperature
nvidia-smi --query-gpu=temperature.gpu --format=csv

# Set fan curve (if available)
nvidia-settings -a "[gpu:0]/GPUFanControlState=1"
nvidia-settings -a "[fan:0]/GPUTargetFanSpeed=50"

# For eGPU, monitor carefully:
watch -n 1 nvidia-smi
```

## Driver Orchestration in Kubernetes

### Init Container for Driver Loading
```yaml
apiVersion: v1
kind: Pod
spec:
  initContainers:
  - name: nvidia-driver-check
    image: ubuntu:22.04
    command:
    - sh
    - -c
    - |
      # Verify modules loaded
      lsmod | grep nvidia || exit 1
      # Verify device files
      ls -l /dev/nvidia0 || exit 1
  containers:
  - name: main-app
    image: your-app:latest
    resources:
      limits:
        nvidia.com/gpu: 1
```

### DaemonSet for Node Management
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nvidia-driver-validator
spec:
  selector:
    matchLabels:
      app: nvidia-validator
  template:
    metadata:
      labels:
        app: nvidia-validator
    spec:
      hostPID: true
      containers:
      - name: validator
        image: nvidia/driver:535.54.03-ubuntu22.04
        securityContext:
          privileged: true
        volumeMounts:
        - name: dev
          mountPath: /dev
      volumes:
      - name: dev
        hostPath:
          path: /dev
```

## Troubleshooting

### Common Module Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Code 43 | Version mismatch | Update guest driver |
| Module not loading | Wrong kernel headers | Install `linux-headers-generic` |
| CUDA OOM | Memory leak | `nvidia-smi --gpu-reset` |
| Slow transfers | UVM not loaded | `modprobe nvidia-uvm` |

### Diagnostic Commands
```bash
# Check module version
modinfo nvidia

# Check loaded modules
lsmod | grep nvidia

# Check module parameters
systool -v -m nvidia

# Check device nodes
ls -l /dev/nvidia*

# Full GPU info
nvidia-smi -q

# CUDA compatibility
nvcc --version
```

### Debug Log
```bash
# Enable debug logging
echo "options nvidia NVreg_ResmanDebugLevel=0xff" \
  > /etc/modprobe.d/nvidia-debug.conf

# Check dmesg
dmesg | grep -i nvidia

# X11 log (if using display)
cat /var/log/Xorg.0.log | grep -i nvidia
```

---

## References

### Related ai-engineering-curriculum Documents

- [1201: Proxmox Hypervisor Standard Operating Procedures](1201-Proxmox-Hypervisor-SOP.md)
- [1202: GPU Passthrough (IOMMU/VFIO)](1202-TB3-UT3G-Passthrough.md)
- [1204: Multi-GPU Setup](1204-Multi-GPU-Setup.md)

---

## Next Steps

- Continue with: **[1204: Multi-GPU Setup](./1204-Multi-GPU-Setup.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1202: GPU Passthrough (IOMMU/VFIO)](./1202-TB3-UT3G-Passthrough.md)
- [1302: GPU Scheduler](../1300-kubernetes/1302-GPU-Scheduler.md)
- [2203: CUDA Kernel](../../phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Syb-Level.md)

**Experiment Template:** `experiments/EXP_1203_NVIDIA_MODULES.md`
