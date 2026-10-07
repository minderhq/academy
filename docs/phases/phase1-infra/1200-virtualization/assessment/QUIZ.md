---
Document ID: 1200-QUIZ
Title: "1200: Virtualization - Quiz"
Last Updated: 2026-10-07
Status: Complete
Difficulty: Beginner
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'infrastructure', 'virtualization']
---

# 1200: Virtualization - Quiz

## Instructions

- **25 questions**
- **Passing score: 80%** (20/25 correct)
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
B) No GPU access
C) Only CPU access
D) A VM to directly access GPU hardware

**3. A GPU passed through to a VM connects to the CPU via:**

A) HDMI connection
B) USB connection
C) PCIe lanes
D) Ethernet

**4. IOMMU is required for:**

A) CPU passthrough
B) Storage passthrough
C) Network passthrough
D) GPU passthrough

**5. Proxmox is based on:**

A) Red Hat Enterprise Linux
B) CentOS
C) Ubuntu
D) Debian

**6. A virtual machine differs from a container because:**

A) VMs use less memory
B) Containers are faster
C) VMs have full OS, containers share kernel
D) No difference

**7. VFIO stands for:**

A) Virtual Function I/O
B) Video File Input Output
C) Virtual File System Only
D) A framebuffer compression standard for guest GPUs

**8. The VGA arbiter controls:**

A) Storage access
B) Network access
C) GPU access between host and VM
D) CPU access

**9. For multi-GPU passthrough, you need:**

A) No IOMMU
B) One IOMMU group
C) Multiple IOMMU groups
D) Special hardware only

**10. OVMF is:**

A) A type of hypervisor
B) A container runtime
C) A GPU driver
D) UEFI firmware for VMs

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

A) Enable both physical GPUs in the host for exclusive host rendering and display
B) Disable host GPU driver
C) Use integrated graphics for host
D) Disabling the host GPU driver and using integrated graphics for the host

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

**21. You need to serve one model while fine-tuning another on the same machine. Per the lesson's single-GPU limits, this is:**

A) Fine on one 11GB card with memory growth enabled
B) Not practical on one card - add a second accelerator instead
C) Only possible with nn.DataParallel
D) Possible if the model is quantized to 4-bit

**22. For production multi-GPU training on one node, the lesson recommends:**

A) nn.DataParallel, which splits each batch automatically
B) A single GPU with gradient accumulation
C) DistributedDataParallel, launched with torchrun
D) Pipeline parallelism for every workload

**23. Launching with `torchrun --nproc_per_node=2 train.py` gives each process:**

A) RANK, WORLD_SIZE, MASTER_ADDR, and MASTER_PORT in its environment
B) A pre-built DistributedDataParallel model instance
C) Its own copy of the dataset on local disk
D) A CUDA graph of the training step

**24. Llama-2-13B at fp16 will not serve on two 11GB cards with vLLM `--tensor-parallel-size 2` because:**

A) Tensor parallelism requires identical GPU models
B) vLLM only supports 7B-class models
C) The KV cache alone exceeds 22GB
D) Each shard needs about 13GB - more than one card holds

**25. Two GPUs sit in different IOMMU groups and cannot peer directly. The lesson's NCCL fix is:**

A) Upgrading to the newest NCCL version
B) Setting NCCL_P2P_DISABLE=1
C) Switching the backend to MPI
D) Moving both GPUs into one VM

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 5, 6, 10, 15, 16, 18:** [1201: Proxmox Hypervisor Standard Operating Procedures](../1201-Proxmox-Hypervisor-SOP.md) — hypervisor platform and VM resources
- **Questions 2-4, 7-9, 12-14, 19, 20:** [1202: GPU Passthrough (IOMMU/VFIO)](../1202-TB3-UT3G-Passthrough.md) — passthrough mechanics and IOMMU group isolation
- **Questions 11, 17:** [1203: NVIDIA Kernel Module Management](../1203-Nvidia-Kernel-Module.md) — host-side kernel module handoff
- **Questions 21-25:** [1204: Multi-GPU Setup](../1204-Multi-GPU-Setup.md) — single-GPU limits, DataParallel versus DDP, torchrun environment variables, vLLM shard sizing, and the NCCL peer-access fix

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Type 1 (bare-metal) hypervisors run directly on hardware; Type 2 runs on top of an OS |
| 2 | D | Passthrough hands the whole GPU to one VM; sharing is SR-IOV/vGPU territory, not passthrough |
| 3 | C | The GPU sits on PCIe lanes; USB/HDMI/Ethernet are not the bus |
| 4 | D | IOMMU remaps device DMA so a VM can safely own a device |
| 5 | D | Proxmox VE is Debian-based |
| 6 | C | A VM virtualizes hardware and runs a full guest OS; containers share the host kernel |
| 7 | A | VFIO = Virtual Function I/O, the kernel framework for secure device passthrough |
| 8 | C | The VGA arbiter decides which side (host or VM) owns VGA output |
| 9 | C | Each passed device needs a clean IOMMU group; multi-GPU means multiple groups |
| 10 | D | OVMF is the UEFI firmware build for QEMU/KVM VMs |
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
| 21 | B | Serving one model while fine-tuning another competes for the same 11GB; the lesson's answer is a second accelerator, not a memory trick |
| 22 | C | DDP runs one process per GPU with gradient all-reduce; DataParallel's single-process fan-out is not the production recommendation |
| 23 | A | torchrun exports RANK, WORLD_SIZE, MASTER_ADDR, and MASTER_PORT so every process can join the rendezvous |
| 24 | D | 13B at fp16 is ~26GB; two shards still need ~13GB each - more than one 11GB card holds (a 7B at ~8GB per shard fits) |
| 25 | B | NCCL_P2P_DISABLE=1 routes collectives through shared memory when the peer path across IOMMU groups is blocked |

---

## Scoring

- **20-25 correct:** Excellent understanding of virtualization
- **18-19 correct:** Good, review missed topics
- **15-17 correct:** Needs more study
- **<15 correct:** Please review the module materials
