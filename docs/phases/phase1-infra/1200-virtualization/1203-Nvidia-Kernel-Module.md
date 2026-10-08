---
Document ID: 1203
Title: "1203: NVIDIA Kernel Module Management"
Phase: 1
Module: 1200
Last Updated: 2026-10-08
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
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Sketch the userspace-to-kernel component stack of the NVIDIA driver and name which parts ship as kernel modules
- Trace the load order of nvidia, nvidia-uvm, nvidia-modeset, nvidia-drm, and nvidia-peermem and state each module's role
- Install the driver through DKMS, ubuntu-drivers, or the NVIDIA runfile, and verify the loaded version with modinfo
- Blacklist nouveau, set NVreg parameters in /etc/modprobe.d, and enable driver persistence across reboots
- Distinguish CUDA unified memory from explicit copies and check the BAR1 aperture that bounds host-to-device transfers
- Read GPU P-states, temperatures, and power limits with nvidia-smi and cap the draw for thermally constrained enclosures

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
│         NVIDIA Driver (580.xx.x)        │
│  libnvidia-ml.so (nvidia-smi API)       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Kernel Modules                  │
│  nvidia.ko, nvidia-uvm.ko,              │
│  nvidia-modeset.ko, nvidia-drm.ko       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Hardware (11GB-class GPU)       │
└─────────────────────────────────────────┘
```

## Kernel Modules Explained

### Module Breakdown
```text
nvidia.ko           - Main driver module (4352 CUDA cores management)
nvidia-uvm.ko       - Unified Virtual Memory (for CUDA managed memory)
nvidia-modeset.ko   - Kernel mode-setting (display config; nvidia-drm depends on it)
nvidia-drm.ko       - Direct Rendering Manager (display output)
nvidia-peermem.ko   - Peer-to-peer memory (GPUDirect)

# MIG (Multi-Instance GPU) is a driver feature of A100/A30/H100-class
# GPUs managed through NVML - it is not a separate kernel module.
```

### Module Loading Order
```bash
# Critical load order
1. nvidia          # Core driver
2. nvidia-uvm      # Memory management
3. nvidia-modeset  # Display mode-setting (nvidia-drm needs it)
4. nvidia-drm      # Display (if needed)
5. nvidia-peermem  # Optional, for RDMA
```

## Installation Methods

### Method 1: DKMS (Dynamic Kernel Module Support)
```bash
# Install DKMS build dependencies
apt install dkms build-essential linux-headers-$(uname -r)

# Install NVIDIA driver with DKMS - the -dkms package registers the
# module build with DKMS
apt install nvidia-driver-580 nvidia-dkms-580

# DKMS rebuilds module on kernel update automatically
dkms status
# nvidia/580.65.06, 6.8.0-45-amd64, x86_64: installed
```

### Method 2: Package Manager (Ubuntu)
```bash
# Ubuntu ships current NVIDIA branches in its own archive - let
# ubuntu-drivers pick the recommended one for the detected GPU
ubuntu-drivers devices
ubuntu-drivers install nvidia:580

# Check loaded modules
lsmod | grep nvidia
```

### Method 3: NVIDIA Runfile (For Specific Versions)
```bash
# Download from NVIDIA
wget https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/NVIDIA-Linux-x86_64-580.65.06.run

# Single invocation: point at the matching kernel headers and skip
# the OpenGL userspace libraries (they conflict with mesa)
chmod +x NVIDIA-Linux-x86_64-*.run
./NVIDIA-Linux-x86_64-*.run \
  --kernel-source-path=/usr/src/linux-headers-$(uname -r) \
  --no-opengl-files
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
options nvidia NVreg_DynamicPowerManagement=0

# Explanation:
# EnableGpuFirmware: 0 = legacy firmware path instead of the GSP
#   (GPU System Processor) firmware; the open kernel modules require
#   GSP and the proprietary driver defaults to it on Turing and
#   newer, so keep the default (1) on modern stacks
# EnablePageRetirement: Handle bad VRAM pages gracefully
# UsePageAttributeTable: Improved memory performance
# EnableStreamMemOPs: Enable CUDA stream operations
# DynamicPowerManagement: 0 keeps the GPU always initialized
#   (no runtime D3) - the steady choice for eGPU enclosures
```

### Persistence Mode
```bash
# Enable persistence (keeps the driver initialized between clients)
nvidia-smi -pm 1

# Persistence across reboots: use the nvidia-persistenced daemon that
# ships with the driver packages - no hand-rolled unit needed
systemctl enable --now nvidia-persistenced
```

## CUDA Memory Management

### Unified Memory (nvidia-uvm)
```text
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
# P0:  Maximum performance state
# P8:  Idle (minimum power draw); P1-P12 are intermediate
#      states - which ones a card exposes varies by model

# For eGPU, cap power draw at TDP - steadier clocks under load
# (enclosures often have weak cooling):
nvidia-smi -pl 250  # Set power limit to TDP
```

### Thermal Management
```bash
# Check current temperature
nvidia-smi --query-gpu=temperature.gpu --format=csv

# Pin a static fan speed (static target - not a curve)
nvidia-settings -a "[gpu:0]/GPUFanControlState=1"
nvidia-settings -a "[fan:0]/GPUTargetFanSpeed=50"

# For eGPU, monitor carefully:
watch -n 1 nvidia-smi
```

## Driver Orchestration in Kubernetes

### Init Container for Driver Readiness Check
```yaml
apiVersion: v1
kind: Pod
spec:
  initContainers:
  - name: nvidia-driver-check
    image: ubuntu:24.04
    command:
    - sh
    - -c
    - |
      # Host kernel modules are visible through /proc/modules
      # (the ubuntu base image has no kmod, hence no lsmod):
      grep -q '^nvidia' /proc/modules || exit 1
      # Device files need an explicit hostPath mount - the init
      # container does not request nvidia.com/gpu itself
      ls -l /dev/nvidia0 || exit 1
    volumeMounts:
    - name: dev
      mountPath: /dev
  containers:
  - name: main-app
    image: your-app:latest
    resources:
      limits:
        nvidia.com/gpu: 1
  volumes:
  - name: dev
    hostPath:
      path: /dev
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
        # Driver containers live on NGC (Docker Hub nvidia/driver is
        # deprecated); the tag embeds driver AND host kernel version
        image: nvcr.io/nvidia/driver:580-6.8.0-45-generic-ubuntu24.04
        securityContext:
          privileged: true
        volumeMounts:
        - name: dev
          mountPath: /dev
        - name: modules
          mountPath: /lib/modules
        - name: kernelsrc
          mountPath: /usr/src
      volumes:
      - name: dev
        hostPath:
          path: /dev
      - name: modules
        hostPath:
          path: /lib/modules
      - name: kernelsrc
        hostPath:
          path: /usr/src
```

## Troubleshooting

### Common Module Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Code 43 | Guest driver rejects the virtual environment (consumer-GPU passthrough is allowed natively since driver 465; older drivers need `hidden=1`, see 1201) | Update the guest driver, or set `hidden=1` in the VM config |
| Module not loading | Wrong kernel headers | Install `linux-headers-generic` |
| CUDA OOM | VRAM still held after crashed/killed pods | Stop GPU pods, then `nvidia-smi --gpu-reset` (reset requires the GPU idle) |
| CUDA app fails: "UVM not available" | nvidia_uvm not loaded | `modprobe nvidia-uvm` |

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

## Summary

NVIDIA GPU stability across reboots and kernel updates is a kernel-module management problem: the user-space stack (CUDA toolkit, cuDNN, TensorRT) sits on the driver, which sits on the modules the kernel loads. This lesson covered the component architecture, the modules explained, installation methods and module configuration, CUDA memory management, power management, and how the driver is orchestrated inside Kubernetes. Troubleshooting closes it: when the GPU disappears after an update, the module version, the loaded kernel, and the persistence daemon are the first three places to look.

## References

### Related Minder Academy Documents

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
- [1302: GPU Scheduler Configuration](../1300-kubernetes/1302-GPU-Scheduler.md)
- [2203: CUDA Kernel Programming and GPU Architecture](../../phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Programming.md)

