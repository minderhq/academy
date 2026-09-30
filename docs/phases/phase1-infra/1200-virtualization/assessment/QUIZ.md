---
Document ID: 1200-QUIZ
Title: "1200: Virtualization - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Beginner
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'infrastructure', 'virtualization']
---

# 1200: Virtualization - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)
- **Time limit:** None

---

## Questions

**1. Type 1 hypervisors run:**

A) On top of an operating system
B) Only in containers
C) Directly on hardware
D) Only on Windows

**2. GPU passthrough allows:**

A) Multiple VMs to share one GPU
B) A VM to directly access GPU hardware
C) Only CPU access
D) No GPU access

**3. A GPU passed through to a VM connects to the CPU via:**

A) PCIe lanes
B) USB connection
C) HDMI connection
D) Ethernet

**4. IOMMU is required for:**

A) CPU passthrough
B) GPU passthrough
C) Network passthrough
D) Storage passthrough

**5. Proxmox is based on:**

A) Red Hat Enterprise Linux
B) Debian
C) Ubuntu
D) CentOS

**6. A virtual machine differs from a container because:**

A) VMs have full OS, containers share kernel
B) Containers are faster
C) VMs use less memory
D) No difference

**7. VFIO stands for:**

A) Virtual Function I/O
B) Video File Input Output
C) Virtual File System Only
D) None of the above

**8. The VGA arbiter controls:**

A) GPU access between host and VM
B) Network access
C) Storage access
D) CPU access

**9. For multi-GPU passthrough, you need:**

A) Multiple IOMMU groups
B) One IOMMU group
C) No IOMMU
D) Special hardware only

**10. OVMF is:**

A) A type of hypervisor
B) UEFI firmware for VMs
C) A GPU driver
D) A container runtime

**11. Blacklisting Nouveau is necessary because:**

A) It's buggy
B) It conflicts with Nvidia drivers
C) It's not open source
D) It uses too much memory

**12. PCIe passthrough requires:**

A) ACS enablement
B) Disabled IOMMU
C) No configuration
D) Windows host

**13. Looking glass is used for:**

A) VM console access
B) GPU video forwarding
C) Network monitoring
D) Storage management

**14. A GPU in an IOMMU group with other devices:**

A) Can't be passed through
B) Can be passed through
C) Requires special configuration
D) Is not supported

**15. Virtual machine memory:**

A) Can be overcommitted
B) Must be exactly physical RAM
C) Can't exceed host RAM
D) Is unlimited

**16. vCPUs in a VM:**

A) Map 1:1 to physical CPUs
B) Can be overcommitted
C) Must be less than physical cores
D) Are always slower

**17. When setting up GPU passthrough, you should:**

A) Enable both GPUs in host
B) Disable host GPU driver
C) Use integrated graphics for host
D) Both B and C

**18. The EFI disk in Proxmox:**

A) Contains VM configuration
B) Is for booting VMs in UEFI mode
C) Stores GPU drivers
D) Is not needed

**19. For passthrough, the GPU should be in:**

A) The first PCIe slot
B) Its own IOMMU group
C) A shared IOMMU group
D) Any slot

**20. After configuring passthrough, the VM:**

A) Sees the GPU as physical hardware
B) Sees a virtual GPU
C) Can't use the GPU
D) Needs special drivers

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Type 1 (bare-metal) hypervisors run directly on hardware; Type 2 runs on top of an OS |
| 2 | B | Passthrough hands the whole GPU to one VM; sharing is SR-IOV/vGPU territory, not passthrough |
| 3 | A | The GPU sits on PCIe lanes; USB/HDMI/Ethernet are not the bus |
| 4 | B | IOMMU remaps device DMA so a VM can safely own a device |
| 5 | B | Proxmox VE is Debian-based |
| 6 | A | A VM virtualizes hardware and runs a full guest OS; containers share the host kernel |
| 7 | A | VFIO = Virtual Function I/O, the kernel framework for secure device passthrough |
| 8 | A | The VGA arbiter decides which side (host or VM) owns VGA output |
| 9 | A | Each passed device needs a clean IOMMU group; multi-GPU means multiple groups |
| 10 | B | OVMF is the UEFI firmware build for QEMU/KVM VMs |
| 11 | B | Nouveau is the open Nvidia driver; blacklisted so the vendor driver can bind to the card |
| 12 | A | ACS lets the IOMMU isolate devices sharing a bridge, enabling clean passthrough |
| 13 | B | Looking Glass forwards the VM's GPU framebuffer to the host display near-natively |
| 14 | A | A shared group passes all-or-nothing; the GPU must be alone in its group |
| 15 | A | Memory can be overcommitted beyond physical RAM (ballooning, KSM) |
| 16 | B | vCPUs are scheduled onto physical cores, so they can be overcommitted |
| 17 | D | The host must give up the card: disable its driver and run the host on integrated graphics |
| 18 | B | The EFI disk holds UEFI variables so a VM can boot in UEFI mode |
| 19 | B | Cleanest passthrough is a GPU alone in its own IOMMU group |
| 20 | A | The card is handed over as physical hardware; the guest installs the vendor driver as on a real machine |

---

## Scoring

- **16-20 correct:** Excellent understanding of virtualization
- **14-15 correct:** Good, review missed topics
- **12-13 correct:** Needs more study
- **<12 correct:** Please review the module materials
