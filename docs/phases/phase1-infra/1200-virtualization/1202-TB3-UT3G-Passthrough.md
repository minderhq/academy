---
Document ID: 1202
Title: GPU Passthrough (IOMMU/VFIO)
Phase: 1
Module: 1200
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: [1201] Proxmox Hypervisor SOP
Related: [1201, 1203, 1204]
Tags: [virtualization, proxmox, gpu, iommu, vfio]
Hardware: [x86_64 host with VT-d or AMD-Vi, one NVIDIA GPU (8GB+ VRAM)]
Software: [Proxmox VE, Linux guest with NVIDIA drivers]
---

# 1202: GPU Passthrough (IOMMU/VFIO)

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Overview
- Explain Prerequisites: IOMMU Hardware Support
- Explain Enabling IOMMU in the Kernel
- Explain Verifying IOMMU Groups
- Explain VFIO Binding and Host Driver Blacklisting
- Configure and operate Proxmox VM Configuration

---

## Abstract

GPU passthrough assigns a physical NVIDIA GPU to a single virtual machine, giving that VM near-native CUDA performance while the host runs other workloads. This document covers the IOMMU prerequisites, kernel configuration, IOMMU group verification, VFIO binding, and the Proxmox VM settings required to make passthrough work on any x86_64 host with VT-d or AMD-Vi.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Prerequisites: IOMMU Hardware Support](#2-prerequisites-iommu-hardware-support)
- [3. Enabling IOMMU in the Kernel](#3-enabling-iommu-in-the-kernel)
- [4. Verifying IOMMU Groups](#4-verifying-iommu-groups)
- [5. VFIO Binding and Host Driver Blacklisting](#5-vfio-binding-and-host-driver-blacklisting)
- [6. Proxmox VM Configuration](#6-proxmox-vm-configuration)
- [7. Guest GPU Verification](#7-guest-gpu-verification)
- [8. NVIDIA-Specific Quirks](#8-nvidia-specific-quirks)
- [9. Troubleshooting](#9-troubleshooting)
- [10. When a Dedicated GPU Beats an External One](#10-when-a-dedicated-gpu-beats-an-external-one)

---

## 1. Overview

### 1.1 Passthrough vs Host GPU

You have two ways to give container/VM workloads access to a GPU:

| Approach | How it works | Trade-offs |
|----------|--------------|------------|
| **Host GPU** | Driver on the Proxmox host; VMs/LXC use it via device mapping | One driver stack; but host and guest share VRAM and driver state; LXC-only for NVIDIA containers is simpler, VMs cannot use it directly |
| **Passthrough (VFIO)** | The entire PCI device is detached from the host and assigned to one VM | Near-native performance, clean driver isolation; the GPU is unavailable to the host and to any other VM while passed through |

For this course, passthrough is the pattern used for the K3s GPU worker VM: the VM gets exclusive use of the card, the NVIDIA device plugin advertises it to the cluster, and the host stays driver-free and stable.

### 1.2 What Passthrough Requires

1. A CPU and motherboard with an IOMMU: **Intel VT-d** or **AMD-Vi** (both are standard on anything from the last decade).
2. IOMMU enabled in BIOS/UEFI *and* on the Linux kernel command line.
3. The GPU in an isolated IOMMU group (Section 4).
4. The GPU bound to the `vfio-pci` driver on the host, with vendor drivers blacklisted (Section 5).

---

## 2. Prerequisites: IOMMU Hardware Support

The IOMMU (Input-Output Memory Management Unit) is what makes PCI passthrough safe: it translates device DMA addresses and enforces per-group isolation.

Enable it in BIOS/UEFI first. Names vary by vendor:

```text
Intel platforms:      VT-d, "Intel Virtualization Technology for Directed I/O"
AMD platforms:        AMD-Vi / IOMMU, "SVM" (SVM covers AMD-V; IOMMU is a separate toggle)
Also useful:          Above 4G Decoding: Enabled (see Section 9 for why)
                      Resizable BAR / Smart Access Memory: optional
```

Verify that the platform actually implements the feature:

```bash
# CPU flags - look for "vmx" (Intel VT-x) or "svm" (AMD-V),
# and "dmar"/"amd_iommu" evidence in the next command:
grep -E 'vmx|svm' /proc/cpuinfo | head -1

# IOMMU support reported by the kernel:
dmesg | grep -e IOMMU -e AMD-Vi
```

---

## 3. Enabling IOMMU in the Kernel

### 3.1 GRUB Configuration

Edit `/etc/default/grub` and extend the command line:

```bash
# Intel host:
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"

# AMD host:
GRUB_CMDLINE_LINUX_DEFAULT="quiet amd_iommu=on iommu=pt"
```

What each parameter does:

```text
intel_iommu=on   Force-enable the Intel IOMMU driver (some distros default off)
amd_iommu=on     Same for AMD (usually on by default, harmless to set)
iommu=pt         Pass-through mode for non-passthrough devices:
                 devices the host keeps (NVMe, NICs) skip translation,
                 avoiding a small performance penalty
```

Apply and reboot:

```bash
update-grub
reboot
```

### 3.2 Post-Reboot Verification

```bash
dmesg | grep -i -e DMAR -e IOMMU

# Expected on Intel:
#   DMAR: IOMMU enabled
# Expected on AMD:
#   AMD-Vi: Interrupt remapping enabled

# IOMMU groups should now exist in sysfs:
ls /sys/kernel/iommu_groups/
```

If the directory is empty, the IOMMU is not active - return to Section 2 (BIOS) and Section 3 (kernel line).

---

## 4. Verifying IOMMU Groups

Devices in the same IOMMU group can DMA to each other. To pass a device through safely, its group must contain nothing the host needs.

### 4.1 Group Listing Script

```bash
#!/bin/bash
# find_symlinked_groups - list every PCI device with its IOMMU group
for g in /sys/kernel/iommu_groups/*; do
    echo "IOMMU Group ${g##*/}:"
    for d in "$g"/devices/*; do
        echo -e "\t$(lspci -nns ${d##*/})"
    done
done
```

Example output:

```text
IOMMU Group 14:
        01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA106 [GeForce RTX 3060] [10de:2503] (rev a1)
        01:00.1 Audio device [0403]: NVIDIA Corporation GA106 High Definition Audio [10de:228b] (rev a1)
```

A group containing **only the GPU and its own audio function** is ideal (this is typical for a physical PCIe x16 slot on a board with a modern chipset).

### 4.2 Deciding Whether Your Group Is Usable

| Group contents | Verdict |
|----------------|---------|
| GPU + GPU audio only | Pass through both functions together |
| GPU + unrelated PCI devices (USB controller, NIC...) | Risky: passing the group's other devices too, or enabling ACS override (Section 9.3) |
| GPU shares a group with the root port itself | Common on consumer boards with few slots; may still pass if nothing else is in the group |

Note: the GPU's audio function must be passed through alongside the GPU or HDMI audio inside the VM breaks.

---

## 5. VFIO Binding and Host Driver Blacklisting

### 5.1 Load VFIO Modules at Boot

```bash
# /etc/modules - append:
vfio
vfio_pci
vfio_iommu_type1
vfio_virqfd        # no longer needed on kernels >= 6.2; harmless if present
```

### 5.2 Bind the GPU to vfio-pci Early

Binding by ID is robust across topology changes. Get your IDs from Section 4 (`10de:` is NVIDIA's vendor ID; the second pair is the device ID):

```bash
lspci -nn | grep -i nvidia
# 01:00.0 VGA compatible controller [10de:2503]
# 01:00.1 Audio device [10de:228b]

# /etc/modprobe.d/vfio.conf:
options vfio-pci ids=10de:2503,10de:228b
```

### 5.3 Blacklist Host-Side GPU Drivers

If the host loads `nouveau` or the proprietary `nvidia` driver first, VFIO cannot claim the device:

```bash
# /etc/modprobe.d/blacklist-gpu.conf:
blacklist nouveau
blacklist nvidia
blacklist nvidiafb
options nouveau modeset=0
```

Apply everything:

```bash
update-initramfs -u -k all
reboot
```

### 5.4 Verify the Binding

```bash
lspci -nnk -s 01:00.
# 01:00.0 VGA compatible controller: NVIDIA ...
#         Kernel driver in use: vfio-pci     <-- this is what you want
```

---

## 6. Proxmox VM Configuration

### 6.1 VM Prerequisites

Passthrough requires a modern machine type and UEFI firmware:

```text
Machine:  q35          (Intel's modern chipset model; required for PCIe passthrough)
BIOS:     OVMF (UEFI)  (SeaBIOS works but complicates large-BAR setups)
```

Create or adjust the VM (VMID 102 in the examples below):

```bash
qm set 102 --machine q35 --bios ovmf
qm set 102 --hostpci0 0000:01:00.0,pcie=1,x-vga=1
qm set 102 --hostpci1 0000:01:00.1,pcie=1
```

### 6.2 Flag Meanings

```text
0000:01:00.0   PCI address of the GPU (domain:bus:slot.function)
pcie=1         Present the device as PCIe (not legacy PCI) - required for
               modern NVIDIA drivers to map large BARs correctly
x-vga=1        Mark as the VM's primary VGA (needed for console output;
               harmless for headless CUDA VMs)
hostpci1       The GPU's audio function, passed alongside the video function
```

Alternatively use the GUI: **VM -> Hardware -> Add -> PCI Device**, tick *All Functions* to grab video + audio in one step, tick *PCI-Express*.

The resulting config file (`/etc/pve/qemu-server/102.conf`) contains:

```text
machine: q35
bios: ovmf
hostpci0: 0000:01:00.0,pcie=1,x-vga=1
hostpci1: 0000:01:00.1,pcie=1
```

---

## 7. Guest GPU Verification

Inside the (Ubuntu 22.04/24.04) guest:

```bash
# 1. The GPU must appear on the PCI bus:
lspci | grep -i nvidia
# 01:00.0 VGA compatible controller: NVIDIA Corporation ...

# 2. Install the driver:
apt update && apt install -y nvidia-driver-535-server   # or current branch

# 3. The moment of truth:
nvidia-smi
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 535.xx       Driver Version: 535.xx       CUDA Version: 12.2     |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        ...           | Memory-Usage         | GPU-Util             |
```

If `nvidia-smi` reports the card with correct VRAM, passthrough is complete. Install the CUDA toolkit only if you need to compile kernels; PyTorch/Docker images bundle their own CUDA runtime.

---

## 8. NVIDIA-Specific Quirks

### 8.1 The "Code 43" Historical Note

Older GeForce drivers refused to run inside VMs (error 43), and users worked around it by hiding the hypervisor signature (`args: -cpu host,kvm=off` or `hidden=1`). **This is no longer needed**: modern NVIDIA drivers (465+, since 2021) run fine in VMs on any GeForce card. Only reach for the hidden-state flags if you are troubleshooting a genuinely ancient driver.

### 8.2 vendor-reset Is for AMD, Not NVIDIA

The `vendor-reset` kernel module exists to reset certain **AMD** datacenter cards (Arcturus/Aldebaran) that fail on re-init. Consumer NVIDIA cards reset through standard FLR/RST paths - adding vendor-reset to an NVIDIA passthrough stack does nothing. Do not install it "just in case."

### 8.3 Reset Bugs

Some NVIDIA consumer cards do not reset cleanly between VM starts (the VM works on first boot, fails after reboot until the host reboots). Mitigations, in order of preference:

1. `echo 1 > /sys/bus/pci/devices/0000:01:00.0/reset` from the host between VM sessions.
2. Passthrough all GPU functions (video + audio) - partial passthrough often causes failed resets.
3. Boot order: give the GPU its own power cycle via the VM's stop/start rather than guest-initiated reboot.

---

## 9. Troubleshooting

### 9.1 Common Errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| `/sys/kernel/iommu_groups/` empty | IOMMU not enabled (BIOS or kernel) | Re-check BIOS toggle; verify `intel_iommu=on`/`amd_iommu=on` in GRUB (Sections 2-3) |
| `qm start` fails: "device is not isolated" | GPU shares IOMMU group with host devices | Pass the whole group, or enable ACS override (9.2), or move the card to another slot |
| VM starts but no GPU in `lspci` | vfio-pci did not claim the device | Check `lspci -nnk` on host shows `vfio-pci`; blacklist and initramfs (Section 5) |
| `nvidia-smi` fails: "No devices were found" | Driver loaded but BAR mapping failed | Enable Above 4G Decoding; add `pcie=1` to hostpci (Section 6) |
| `BAR 1: can't reserve [mem ...]` in guest dmesg | BAR above 4G not enabled in firmware | Enable *Above 4G Decoding* (and *Resizable BAR* if available) in BIOS; keep OVMF + q35 |
| Works once, fails after VM reboot | GPU reset bug | Section 8.3 |
| Host becomes unresponsive at VM start | Host still had nvidia driver attached | Verify blacklist took effect; `dmesg \| grep vfio` |

### 9.2 ACS Override (Last Resort)

`pcie_acs_override=downstream,multifunction` on the kernel command line fabricates isolation that the hardware does not provide. It makes passthrough work on boards with poor group layout but weakens the IOMMU's protection guarantees. Prefer moving the card to a different physical slot first.

### 9.3 Diagnostic Checklist

```bash
# Host: is the IOMMU on?
dmesg | grep -i -e DMAR -e IOMMU

# Host: which group is the GPU in, and what else is in it?
./find_symlinked_groups.sh | grep -A 5 -i nvidia

# Host: driver in use?
lspci -nnk -d 10de:

# Host: VFIO claimed it?
dmesg | grep vfio

# Guest: card present at all?
lspci | grep -i nvidia

# Guest: driver complaints?
dmesg | grep -i -e NVRM -e nvidia
```

---

## 10. When a Dedicated GPU Beats an External One

A GPU connected by a physical PCIe slot is the reference case: full x16 bandwidth, no added latency, and the simplest IOMMU layout. If your machine is a laptop or small-form-factor box without a free slot, a GPU over an external enclosure is workable - the card appears as a regular PCIe device, and everything in this document applies unchanged. The caveat is bandwidth: external links (e.g., Thunderbolt's PCIe tunneling) carry roughly a quarter of a physical x16 slot, so workloads that shuttle large tensors between host RAM and VRAM pay a measurable penalty, while VRAM-resident inference is barely affected. For a learning lab, either path is fine; for a permanent multi-node setup, prefer native PCIe.

---

## References

### Related ai-engineering-curriculum Documents

- [1201: Proxmox Hypervisor Standard Operating Procedures](1201-Proxmox-Hypervisor-SOP.md)
- [1203: NVIDIA Kernel Module Management](1203-Nvidia-Kernel-Module.md)
- [1204: Multi-GPU Setup](1204-Multi-GPU-Setup.md)

---

## Next Steps

- Continue with: **[1203: Nvidia Kernel Module](./1203-Nvidia-Kernel-Module.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1201: Proxmox Hypervisor](./1201-Proxmox-Hypervisor-SOP.md)
- [1203: Nvidia Kernel Module](./1203-Nvidia-Kernel-Module.md)
- [1204: Multi-GPU Setup](./1204-Multi-GPU-Setup.md)

---

**Document ID:** 1202
**Last Updated:** 2026-09-24
**Status:** Complete
**Related Documents:** [1201, 1203, 1204]
