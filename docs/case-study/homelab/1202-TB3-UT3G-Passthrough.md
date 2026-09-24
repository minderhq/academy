---
Document ID: 1202
Title: Thunderbolt 3 eGPU Passthrough Configuration
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

# 1202: Thunderbolt 3 eGPU Passthrough Configuration

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Thunderbolt 3 Architecture](#thunderbolt-3-architecture)
- [Hardware Configuration](#hardware-configuration)
- [BIOS Configuration](#bios-configuration)
- [Linux Configuration](#linux-configuration)
- [VM Passthrough Configuration](#vm-passthrough-configuration)
- [Performance Considerations](#performance-considerations)
- [VM Guest Configuration](#vm-guest-configuration)
- [K3s GPU Integration](#k3s-gpu-integration)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Thunderbolt 3 Architecture
- Configure and operate Hardware Configuration
- Configure and operate BIOS Configuration
- Configure and operate Linux Configuration
- Configure and operate VM Passthrough Configuration
- Measure and evaluate Performance Considerations

---

## Abstract
This document details the configuration of PCIe passthrough for the RTX 2080 Ti eGPU connected via Thunderbolt 3 to the Intel NUC. This enables direct GPU access from K3s pods for AI workloads.

## Thunderbolt 3 Architecture

### TB3 Protocol Stack
```text
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (PCIe Tunnelling / DisplayPort / USB)  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Transport Layer                 │
│  (Thunderbolt Protocol - 20Gbps/lane)   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Physical Layer                  │
│  (4 lanes of 10Gbps = 40Gbps total)     │
└─────────────────────────────────────────┘
```

### PCIe Tunneling Over TB3
```text
[RTX 2080 Ti] ← PCIe x16 → [eGPU Enclosure TB3 Controller]
                                          ↓
                                    [TB3 Cable]
                                          ↓
                            [Intel NUC TB3 Port]
                                          ↓
                             [PCIe Tunnel to CPU]
```

## Hardware Configuration

### eGPU Enclosure (Razer Core X / UT3G)
```text
Controller: Intel Alpine Ridge
Bands:     4x PCIe 3.0 lanes (32Gbps theoretical)
Power:      100W (60W for GPU + rest for system)
```

### GPU Specifications
```text
Model:      NVIDIA RTX 2080 Ti
Cores:      4352 CUDA cores
VRAM:       11GB GDDR6
Memory BW:  616 GB/s
TDP:        250W
```

## BIOS Configuration

### Required BIOS Settings
```text
Intel VT-x:                 Enabled
Intel VT-d:                 Enabled
Thunderbolt Security:       No Security (or User Mode)
Thunderbolt Support:        Always On
PCIe Native Power Mgmt:     Enabled
Above 4G Decoding:          Enabled
```

### Verification
```bash
# Check IOMMU support
dmesg | grep -e IOMMU -e AMD-Vi

# Expected output:
# DMAR: IOMMU enabled
```

## Linux Configuration

### 1. IOMMU Kernel Parameters
```bash
# Edit /etc/default/grub
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt \
  pcie_acs_override_downstream_multifunction \
  vfio-pci.ids=10de:1e04,10de:10f8"

# 10de:1e04 = RTX 2080 Ti GPU
# 10de:10f8 = RTX 2080 Ti Audio

update-grub && reboot
```

### 2. Thunderbolt Device Authorization
```bash
# Install bolt (TB3 daemon)
apt install bolt

# Authorize and save device
boltctl enroll

# Set to auto-authorize
boltctl configure --auto 0

# Verify
boltctl list
# o20: RTX 2080 Ti eGPU
#   ├─ status: authorized
#   └─ stored: yes
```

### 3. VFIO Configuration
```bash
# Load VFIO modules
cat >> /etc/modules << EOF
vfio
vfio_pci
vfio_iommu_type1
vfio_virqfd
EOF

# Bind GPU to VFIO
echo "options vfio-pci ids=10de:1e04,10de:10f8" \
  > /etc/modprobe.d/vfio.conf

update-initramfs -u && reboot
```

## VM Passthrough Configuration

### Proxmox VM Config
```bash
# Edit /etc/pve/qemu-server/102.conf (K3s Worker VM)
cpu: host,hidden=0,flags=+hv-evmcs
machine: q35
hostpci0: 20:00.0,pcie=1,x-vga=on,rombar=0
hostpci1: 20:00.1,pcie=1
```

### Explanation
```text
20:00.0 = GPU PCIe address (check with lspci)
20:00.1 = Audio controller
pcie=1   = Use PCIe (not PCI) passthrough
x-vga=on = Enable VGA framebuffer access
rombar=0 = Disable ROM (saves BAR space)
```

### Finding GPU Address
```bash
# On Proxmox host
lspci -nnk -d 10de:

# Example output:
# 20:00.0 VGA compatible controller: NVIDIA Corporation TU102 [GeForce RTX 2080 Ti]
# 20:00.1 Audio device: NVIDIA Corporation TU102 High Definition Audio Controller
```

## Performance Considerations

### TB3 Bandwidth Analysis
```text
PCIe 3.0 x4 theoretical:  31.5 Gbps
RTX 2080 Ti needs:        ~16-20 Gbps (typical AI workload)

Bottleneck Analysis:
- Small batch inference:  No bottleneck (VRAM resident)
- Large model training:   Some bottleneck (H2D transfers)
- Inference streaming:    Minimal impact
```

### Overhead Comparison
```yaml
Direct PCIe 3.0 x16:  0% overhead
TB3 (PCIe 3.0 x4):   ~15-20% overhead for data-heavy workloads

Mitigation:
- Use CUDA unified memory carefully
- Keep model weights in VRAM
- Batch inferences when possible
```

## VM Guest Configuration

### GPU VM (Ubuntu 22.04)
```bash
# Inside the VM, verify GPU
lspci | grep -i nvidia

# Install NVIDIA drivers
apt install linux-headers-generic
add-apt-repository ppa:graphics-drivers/ppa
apt update
apt install nvidia-driver-535

# Verify
nvidia-smi
```

### CUDA Installation
```bash
# Download CUDA
wget https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda_12.2.0_535.54.03_linux.run

# Install (no kernel modules needed - driver already installed)
sh cuda_12.2.0_535.54.03_linux.run --toolkit --silent

# Add to PATH
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
```

## K3s GPU Integration

### NVIDIA Device Plugin
```bash
# In K3s worker VM with GPU
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Verify
kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds

# Check GPU allocation
kubectl describe node | grep nvidia.com/gpu
```

### GPU Pod Example
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-test
spec:
  containers:
  - name: cuda-test
    image: nvidia/cuda:12.2.0-runtime-ubuntu22.04
    resources:
      limits:
        nvidia.com/gpu: 1
    command: ["nvidia-smi"]
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Code 43 error | Driver mismatch in VM | Reinstall guest drivers |
| GPU not visible | VFIO not bound | Check `lspci -nnk -d 10de:` |
| TB3 disconnect | Power saving | Set TB3 to "Always On" |
| Poor performance | PCIe renegotiation | Warm boot, not cold boot |

### Diagnostic Commands
```bash
# Check TB3 connection
boltctl list

# Verify IOMMU groups
find /sys/kernel/iommu_groups/ -type l

# Check VFIO binding
dmesg | grep vfio

# Monitor GPU performance
nvidia-smi dmon -s u
```

---

## References

### Related ai-engineering-curriculum Documents

- [1101: Fiber GPON Modem Configuration](1101-Fiber-GPON-Modem.md)
- [1102: Star Topology Core Network Design](1102-Star-Topology-Core.md)

---

## Next Steps

- Continue with: **[1203: Nvidia Kernel Module](../../phases/phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md)**
- Assessment: **[Phase 1 Quiz](../../00-META/assessment/phase1-quiz.md)**

---

**Related Documents:**
- [1201: Proxmox Hypervisor](../../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)
- [1203: Nvidia Kernel Module](../../phases/phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md)
- [1302: GPU Scheduler](../../phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)

**Experiment Template:** `experiments/EXP_1202_TB3_PASSTHROUGH.md`
