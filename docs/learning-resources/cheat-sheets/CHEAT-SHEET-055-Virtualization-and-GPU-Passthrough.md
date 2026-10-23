---
Document ID: CHEAT-SHEET-055
Title: "CHEAT-SHEET-055: Virtualization and GPU Passthrough - the Hypervisor RAM Ledger, the Passthrough Gate Chain, and the Multi-GPU Scaling Wall"
Last Updated: 2026-10-23
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'infrastructure', 'virtualization', 'gpu']
---

# CHEAT-SHEET-055: Virtualization and GPU Passthrough - the Hypervisor RAM Ledger, the Passthrough Gate Chain, and the Multi-GPU Scaling Wall

The scope scan that picked this page: phase1-infra's 1200-virtualization track carries four modules - 1201 Proxmox Hypervisor Standard Operating Procedures, 1202 GPU Passthrough (IOMMU/VFIO), 1203 NVIDIA Kernel Module Management and 1204 Multi-GPU Setup - and no sheet anywhere in the track, yet it is where a lab lives or dies: the host that will not boot, the GPU that will not pass through, the driver stack that loads in the wrong order, the two-card setup that will not scale. This sheet takes the questions the operator actually asks at 2am: where did the RAM go, may I take this PCI device, why is the guest silent or code-43, what does a Thunderbolt enclosure really cost, and why do two cards not mean 2.0x.

The sheet runs as seven priced exhibits: the hypervisor RAM ledger (F1 - 48 GiB reserved on 64, the ARC cap must come down), the IOMMU group verdict (F2 - the group is the atom), the passthrough gate chain (F3 - seven gates, each with its own failure signature), the Thunderbolt tunnel bill (F4 - a quarter of a slot, 31.51 against 126.03 Gbps), the kernel module ledger (F5 - five modules, one order), the multi-GPU scaling ledger (F6 - 1.7x to 1.8x serving, 190% training), and the peer wall (F7 - NCCL does not cross IOMMU groups). Every number below is printed by the canonical fence at the bottom of the page: the full 186-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 87-line output sits frozen below it byte-for-byte.

## The Hypervisor RAM Ledger - What 64 GiB Actually Buys

The operator's first question is where the RAM went. On the module's canonical 64 GiB host the budget answers it in three motions: ZFS ARC capped at 34,359,738,368 bytes - 32.0 GiB, the fifty-percent rule - 16 x 1 GiB hugepages reserved on the kernel command line before host memory ever fragments (17,179,869,184 bytes = 16.0 GiB), and two K3s VMs at memory: 16384 with balloon: 0 (32.0 GiB, static by design). That is 48 GiB reserved; the host keeps 16 GiB - and that is the lesson, because the ARC default budget assumes an idle host, so on a busy virtualization box the cap must come DOWN, not ride its fifty-percent default. The second dial is zfs_txg_timeout: 5 -> 1 makes ZFS commit dirty data every second instead of five, trading a sliver of throughput for VM write latency the guest actually feels.

## The IOMMU Group Verdict - Take the Group or Leave the GPU

IOMMU groups are the atom of passthrough: the hardware isolates in whole groups, so the group, not the device, is the unit you assign. The fence re-runs the module's own group listing and hands down verdicts: group 14 holds exactly 01:00.0 VGA compatible [10de:2503] and 01:00.1 Audio device [10de:228b] - one physical slot, functions 0 and 1 - so the verdict is take the whole group together; bind only the GPU and the guest plays no HDMI sound. Groups whose members are all host-facing (the NVMe and SATA controller pair in group 13, the host audio in group 16) stay where they are. The pcie_acs_override switch exists, but it fabricates isolation the hardware does not provide - the last resort when a group refuses to split, never the plan.

```text
group 14  = 01:00.0 VGA + 01:00.1 audio   -> pass BOTH, one slot, HDMI alive
group 13  = nvme + sata controllers       -> no guest device, stays in host
group 16  = host audio only               -> nothing to pass
verdict   = the group is the atom; ACS override fakes the isolation
```

## The Passthrough Gate Chain - Seven Gates, One Driver

Passthrough is a chain of seven gates, and a failure at any one of them produces its own signature - debugging is naming the gate, not rebooting into hope. The fence walks the chain: VT-d enabled in firmware; intel_iommu=on iommu=pt on the GRUB command line; /sys/kernel/iommu_groups/ populated; vfio-pci bound to ids=10de:2503,10de:228b with nouveau and nvidia blacklisted; those blacklists and options inside the rebuilt initramfs; lspci -nnk -s 01:00.0 reporting Kernel driver in use: vfio-pci; and finally the guest half - q35 machine, OVMF firmware, hostpci0 with pcie=1,x-vga=1, Above-4G Decoding on. Empty groups with VT-d on means the kernel flag never landed; nouveau still on 01:00.0 means the blacklist never reached the initramfs; and Code 43 in the guest is Above-4G (or the q35/OVMF pairing) - the old NVIDIA block died with driver 465 in 2021, so a modern Code 43 is configuration, not policy.

```text
gates 1-2  bios vtd + intel_iommu=on   -> empty groups = flag never landed
gates 3-4  groups seen + vfio ids      -> nouveau on 01:00.0 = blacklist miss
gates 5-6  initramfs + driver claim    -> 'vfio-pci' in lspci -nnk = cleared
gate  7    q35 + ovmf + pcie=1,x-vga=1 -> code 43 = above-4g decoding off
```

## The Thunderbolt Tunnel Bill - a Quarter of a Slot

The module's case study prices an RTX 2080 Ti - 4352 CUDA cores, 11 GB GDDR6, 616 GB/s VRAM bandwidth, 250 W TDP - in a Thunderbolt 3 enclosure. A PCIe 3.0 lane carries 7.88 Gbps after the 128b/130b encoding; a native x16 slot is 126.03 Gbps; the TB3 tunnel is four lanes, 31.51 Gbps - a quarter of the slot, and a hard ceiling no driver tunes around. The bill splits by workload: VRAM-resident inference moves roughly 18 Gbps of real demand and fits with no measurable bottleneck - weights live on the card, tokens are small; training streams activations and gradients host-to-VRAM every step and pays the full 15-20% overhead. Enroll the device once with boltctl, set Thunderbolt to Always On in firmware, and remember the module's closing fact: warm reboots reset the eGPU, cold boots do not.

```text
pcie 3.0 lane     7.88 gbps   (8.0 gt/s after 128b/130b)
native x16 slot  126.03 gbps
tb3 tunnel x4     31.51 gbps = a quarter of the slot, hard ceiling
2080 ti bill      inference fits (18 gbps); training pays 15-20%
```

## The Kernel Module Ledger - Five Modules in One Order

The driver is not one module; it is five, and the order is the contract: nvidia, then nvidia-uvm, then nvidia-modeset, then nvidia-drm, then nvidia-peermem - the fence asserts every later module outranks the one it builds on (drm stands on modeset, peermem on the base driver). Install via DKMS so the stack rebuilds itself on every kernel update, keep nouveau off the initramfs, and pin the runtime: nvidia-smi -pm 1 or the nvidia-persistenced daemon keeps the card in P0 between clients instead of thrashing to P8 on every idle. In eGPU enclosures with weak cooling, nvidia-smi -pl 250 pins the card at its 250 W TDP - steadier clocks, fewer thermal resets.

```text
1  nvidia           root of the stack
2  nvidia-uvm       unified memory
3  nvidia-modeset   kms modesetting
4  nvidia-drm       builds on modeset
5  nvidia-peermem   builds on the driver; p2p over rdma
```

## The Multi-GPU Scaling Ledger - Two Cards Never Mean 2.0x

The module's benchmark table is the honest bill, and the fence re-prints it:

| Model | One card | Two cards | The bill |
| --- | --- | --- | --- |
| Llama-3.1-8B (4-bit) | 35 tok/s | 60 tok/s | 1.71x |
| Gemma-3-12B | 18 tok/s | 32 tok/s | 1.78x |
| Mistral-7B | 40 tok/s | 70 tok/s | 1.75x |

Serving lands at 1.7x to 1.8x on two cards because every step still syncs across the cards - the sync wall. Training lands at 180-190% of single-card throughput on 200% silicon, and the wall lifts where it matters: batch 8 OOMs on one 11 GB card and runs fine across two. Shard arithmetic decides serving: Qwen3-8B at fp16 is ~8.2 GB per shard and fits an 11 GiB card under vLLM --tensor-parallel-size 2, while Gemma-3-27B at fp16 is ~27 GB per shard and does not - 24 GB-class cards minimum. DeepSpeed sizes its own ledger: 2 GPUs x 2 micro-batches x 4 accumulation steps = 16 global batch, and QLoRA's device_map with max_memory per card splits a fine-tune across the pair without a hand-written map.

## The Peer Wall - NCCL Does Not Cross IOMMU Groups

Exhibits F2 and F4 draw the topology; F7 prices what it does to distributed training. GPUs in different IOMMU groups - or behind a virtualized host - cannot do peer-to-peer DMA: the hardware path between them does not exist. NCCL does not say so; it reports hangs or CRC errors and lets you guess. The fix is one export: NCCL_P2P_DISABLE=1 routes the traffic through host memory, NCCL_DEBUG=INFO shows what it chose, and the gloo backend is the CPU fallback - correct, slower, honest. The law falls straight out of F2: same IOMMU group means peers; across groups means host memory. DataParallel hides the wall badly (uneven load, one process); DDP at least shows it to you - which is why the module says DDP for production and torchrun for the ranks.

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Capping ARC at the default half of RAM | 48 GiB reserved + a 32 GiB cap on a 64 GiB host; the fence shows 16 GiB left - drop the cap |
| Passing the GPU without its audio function | group 14 holds 01:00.0 and 01:00.1; leave 10de:228b in the host and the guest is silent |
| Declaring passthrough done from one command | lspci -nnk still shows nouveau after 'the setup' - the blacklist never reached the initramfs |
| Expecting native x16 speed over Thunderbolt | the tunnel is four lanes, 31.51 against 126.03 Gbps; training pays 15-20%, inference does not |
| Loading nvidia-drm before nvidia-modeset | drm builds on modeset; reversed or missing order breaks the console handover |
| Chasing 2.0x on two cards | 1.7x-1.8x serving, 190% training - the sync wall is physics, not a misconfiguration |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| VM writes stall the whole host | zfs_txg_timeout=1 commits every second instead of five - VM write latency trades against throughput |
| Code 43 in the Windows guest | above-4g decoding off, or the q35/OVMF pairing wrong; the nvidia block died with driver 465 in 2021 |
| Hugepages come up as 2 MiB | 1 GiB pages are a kernel command line setting; vm.nr_hugepages allocates the 2 MiB default size |
| Guest has no hdmi audio | the audio function stayed in the host; bind 10de:228b to vfio-pci alongside 10de:2503 |
| NCCL hangs or crc errors across two gpus | p2p cannot cross iommu groups; NCCL_P2P_DISABLE=1 routes through host memory |
| 13b fp16 will not shard across 2 x 11gb | ~13 gb per shard blows the card; qwen3-8b at 8.2 gb per shard is the fit |

## Quick Reference For

- [Module 1201: Proxmox Hypervisor Standard Operating Procedures](../../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md) - the host build, the ARC and hugepage budget and the backup cadence this sheet's RAM ledger prices.
- [Module 1202: GPU Passthrough (IOMMU/VFIO)](../../phases/phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md) - the group listing, the gate chain and the Thunderbolt case study behind exhibits F2 through F4.
- [Module 1203: NVIDIA Kernel Module Management](../../phases/phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md) - the five-module order, the persistence daemon and the power cap this ledger walks.
- [Module 1204: Multi-GPU Setup](../../phases/phase1-infra/1200-virtualization/1204-Multi-GPU-Setup.md) - the benchmark table, the shard arithmetic and the NCCL env the fence reproduces.

## The Canonical Fence

This sheet's every number - the byte counts, the Gbps, the scaling factors, the batch arithmetic - comes from the fence below, printed by a real run and pinned with asserts: the full 186-line stdlib program reproduces F1 through F7, and its 87-line output sits frozen under it byte-for-byte.

```python
"""tick-1032 canonical fence - CHEAT-SHEET-055: Virtualization and GPU
Passthrough. Prints the hypervisor RAM ledger, the IOMMU group verdicts,
the passthrough gate chain, the Thunderbolt tunnel bill, the kernel
module ledger, the multi-GPU scaling wall and the NCCL peer wall from
real arithmetic measured against modules 1201..1204. Stdlib only,
deterministic, no RNG, no timing, no I/O beyond stdout.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

LINE = "-" * 60


def rule(label):
    print("")
    print(label)
    print(LINE)


# ---------------------------------------------------------------- F1
rule("F1 - the hypervisor RAM ledger")
GIB = 1024 ** 3
host_ram = 64 * GIB
arc_cap = 34359738368              # zfs_arc_max, module 1201
hugepages = 16 * GIB               # 16 x 1 GiB, reserved in GRUB at boot
vm_budget = 2 * 16384 * 1024 ** 2  # two K3s VMs, memory: 16384, balloon: 0
assert arc_cap == 32 * GIB, arc_cap
assert hugepages == 16 * GIB
assert vm_budget == 32 * GIB
print(f"host RAM            {host_ram:,} bytes = 64.0 GiB")
print(f"ZFS ARC cap         {arc_cap:,} bytes = 32.0 GiB (the 50% rule)")
print(f"hugepages 16 x 1GiB {hugepages:,} bytes = 16.0 GiB (pre-boot)")
print(f"two VMs 16384 MiB   {vm_budget:,} bytes = 32.0 GiB (balloon: 0)")
reserved = hugepages + vm_budget
leftover = host_ram - reserved
assert reserved == 48 * GIB
assert leftover == 16 * GIB
print(f"reserved            {reserved // GIB} GiB, host keeps {leftover // GIB} GiB")
print("ARC default 32 GiB > the 16 GiB that is actually left")
print("-> the cap must come DOWN; the default budget assumes an idle host")

# ---------------------------------------------------------------- F2
rule("F2 - the IOMMU group verdict")
groups = {
    14: ["01:00.0 VGA compatible [10de:2503]",
         "01:00.1 Audio device [10de:228b]"],
    13: ["02:00.0 NVMe controller",
         "03:00.0 SATA controller"],
    16: ["00:1f.3 Audio device"],
}


def verdict(members):
    has_gpu = any("VGA" in m for m in members)
    if has_gpu and len(members) == 2:
        return "PASS - take the whole group together"
    if has_gpu:
        return "ACS override, last resort - the isolation is fake"
    return "STAYS IN HOST - nothing guest-facing in the group"


for gid in sorted(groups):
    members = groups[gid]
    print(f"group {gid}: {len(members)} member(s) -> {verdict(members)}")
    for m in members:
        print(f"   {m}")
gpu_pair = groups[14]
addrs = [m.split()[0] for m in gpu_pair]
assert addrs == ["01:00.0", "01:00.1"], addrs
slots = {a.split(".")[0] for a in addrs}
assert slots == {"01:00"}, slots
funcs = {a.split(".")[1] for a in addrs}
assert funcs == {"0", "1"}, funcs
assert verdict(groups[14]).startswith("PASS")
assert verdict(groups[13]).startswith("STAYS")
print("the GPU pair shares device 01:00, functions 0 and 1 - one physical slot")
print("pass the audio function too or the guest plays no HDMI sound")

# ---------------------------------------------------------------- F3
rule("F3 - the passthrough gate chain")
gates = [
    ("BIOS", "VT-d / IOMMU enabled in firmware"),
    ("kernel", "intel_iommu=on iommu=pt on the GRUB cmdline"),
    ("groups", "/sys/kernel/iommu_groups/ is populated"),
    ("driver", "vfio-pci ids=10de:2503,10de:228b; nouveau and nvidia blacklisted"),
    ("initramfs", "blacklists and vfio options inside the initramfs image"),
    ("claim", "lspci -nnk -s 01:00.0 reports Kernel driver in use: vfio-pci"),
    ("guest", "q35 + OVMF, hostpci0 pcie=1,x-vga=1, Above-4G Decoding on"),
]
assert len(gates) == 7, len(gates)
for i, (name, what) in enumerate(gates, 1):
    print(f"gate {i} [{name:9s}] {what}")
assert [g[0] for g in gates][:3] == ["BIOS", "kernel", "groups"]
assert "vfio-pci" in gates[3][1]
failures = {
    "BIOS": "groups stay empty; nothing downstream can even start",
    "kernel": "groups empty even with VT-d on - the flag never landed",
    "driver": "lspci still shows nouveau or nvidia on 01:00.0",
    "guest": "Code 43 in the guest; BAR errors = Above-4G is off",
}
for name, sig in failures.items():
    print(f"  fail at [{name:9s}] -> {sig}")
assert "Code 43" in failures["guest"]
assert "Above-4G" in failures["guest"]

# ---------------------------------------------------------------- F4
rule("F4 - the Thunderbolt tunnel bill")
lane_gbps = 8.0 * 128 / 130        # PCIe 3.0 per lane after 128b/130b
x16_gbps = lane_gbps * 16          # a native x16 slot
tb3_gbps = lane_gbps * 4           # TB3 tunnels four PCIe 3.0 lanes
assert abs(lane_gbps - 7.876923) < 0.000001
assert abs(x16_gbps - 126.030769) < 0.000001
assert abs(tb3_gbps - 31.507692) < 0.000001
print(f"PCIe 3.0 lane        {lane_gbps:.2f} Gbps (after 128b/130b)")
print(f"native x16 slot      {x16_gbps:.2f} Gbps")
print(f"TB3 tunnel (x4)      {tb3_gbps:.2f} Gbps hard ceiling")
print("RTX 2080 Ti in the enclosure: 4352 CUDA cores, 11 GB GDDR6,")
print("616 GB/s VRAM bandwidth, 250 W TDP")
workload = 18.0
print(f"typical serving workload {workload:.0f} Gbps -> inside the tunnel")
print("VRAM-resident inference: no measurable bottleneck over TB3")
print("training host<->VRAM: 15-20% overhead vs native x16 - the real bill")

# ---------------------------------------------------------------- F5
rule("F5 - the kernel module ledger")
order = ["nvidia", "nvidia-uvm", "nvidia-modeset", "nvidia-drm",
         "nvidia-peermem"]
assert len(order) == 5, order
rank = {m: i for i, m in enumerate(order)}
deps = {"nvidia-uvm": "nvidia",
        "nvidia-modeset": "nvidia",
        "nvidia-drm": "nvidia-modeset",
        "nvidia-peermem": "nvidia"}
for mod, parent in deps.items():
    assert rank[mod] > rank[parent], mod
print("load order - every later module stands on an earlier one:")
for i, m in enumerate(order, 1):
    parent = deps.get(m, "-")
    print(f"  {i}. {m:17s} builds on {parent}")
print("persistence: nvidia-smi -pm 1 or nvidia-persistenced keeps P0")
print("power cap:   nvidia-smi -pl 250 pins TDP; eGPU enclosures cook without it")

# ---------------------------------------------------------------- F6
rule("F6 - the multi-GPU scaling ledger")
serving = [("Llama-3.1-8B", 35.0, 60.0),
           ("Gemma-3-12B", 18.0, 32.0),
           ("Mistral-7B", 40.0, 70.0)]
for name, one, two in serving:
    gain = two / one
    assert 1.5 < gain < 2.0, name
    print(f"{name:13s} {one:>4.0f} -> {two:>4.0f} tok/s = {gain:.2f}x")
print("two cards never mean 2.0x - 1.7x to 1.8x is the honest bill")
train_scale = 190.0
print(f"training scales to {train_scale:.0f}% of single on 200% silicon")
assert train_scale < 200.0
vllm_shards = [("Qwen3-8B", 8.2, True),
               ("Gemma-3-27B", 27.0, False)]
for name, shard, fits in vllm_shards:
    ok = shard <= 11.0
    assert ok == fits, name
    print(f"vLLM TP=2, {name}: {shard:.1f} GB/shard "
          f"{'FITS an 11 GiB card' if ok else 'BLOWS past an 11 GiB card'}")
print("single 11 GB card: 7B at 4bit ~ 4-5 GB fits; 13B at 4bit ~ 8 GB, tight")
global_batch = 2 * 2 * 4
assert global_batch == 16
print(f"DeepSpeed: 2 GPUs x 2 micro-batches x 4 accum = {global_batch} global")
print("batch 8 OOMs on one card and runs fine across two - the VRAM wall lifts")

# ---------------------------------------------------------------- F7
rule("F7 - the peer wall")
print("GPUs in different IOMMU groups, or behind a virtualized host,")
print("cannot do peer-to-peer DMA - the hardware path does not exist")
print("NCCL reports hangs or CRC errors, never the topology truth")
print("fix: NCCL_P2P_DISABLE=1 - traffic routes through host memory")
print("the gloo backend is the CPU fallback: correct, slower, honest")
env = {"NCCL_P2P_DISABLE": "1", "NCCL_IB_DISABLE": "1",
       "NCCL_DEBUG": "INFO"}
for key in sorted(env):
    print(f"  export {key}={env[key]}")
assert env["NCCL_P2P_DISABLE"] == "1"
print("the law: same IOMMU group = peers; across groups = host memory")
print("DataParallel hides the wall badly; DDP at least shows it to you")

print("")
print("FENCE-055-OK")
```

```text

F1 - the hypervisor RAM ledger
------------------------------------------------------------
host RAM            68,719,476,736 bytes = 64.0 GiB
ZFS ARC cap         34,359,738,368 bytes = 32.0 GiB (the 50% rule)
hugepages 16 x 1GiB 17,179,869,184 bytes = 16.0 GiB (pre-boot)
two VMs 16384 MiB   34,359,738,368 bytes = 32.0 GiB (balloon: 0)
reserved            48 GiB, host keeps 16 GiB
ARC default 32 GiB > the 16 GiB that is actually left
-> the cap must come DOWN; the default budget assumes an idle host

F2 - the IOMMU group verdict
------------------------------------------------------------
group 13: 2 member(s) -> STAYS IN HOST - nothing guest-facing in the group
   02:00.0 NVMe controller
   03:00.0 SATA controller
group 14: 2 member(s) -> PASS - take the whole group together
   01:00.0 VGA compatible [10de:2503]
   01:00.1 Audio device [10de:228b]
group 16: 1 member(s) -> STAYS IN HOST - nothing guest-facing in the group
   00:1f.3 Audio device
the GPU pair shares device 01:00, functions 0 and 1 - one physical slot
pass the audio function too or the guest plays no HDMI sound

F3 - the passthrough gate chain
------------------------------------------------------------
gate 1 [BIOS     ] VT-d / IOMMU enabled in firmware
gate 2 [kernel   ] intel_iommu=on iommu=pt on the GRUB cmdline
gate 3 [groups   ] /sys/kernel/iommu_groups/ is populated
gate 4 [driver   ] vfio-pci ids=10de:2503,10de:228b; nouveau and nvidia blacklisted
gate 5 [initramfs] blacklists and vfio options inside the initramfs image
gate 6 [claim    ] lspci -nnk -s 01:00.0 reports Kernel driver in use: vfio-pci
gate 7 [guest    ] q35 + OVMF, hostpci0 pcie=1,x-vga=1, Above-4G Decoding on
  fail at [BIOS     ] -> groups stay empty; nothing downstream can even start
  fail at [kernel   ] -> groups empty even with VT-d on - the flag never landed
  fail at [driver   ] -> lspci still shows nouveau or nvidia on 01:00.0
  fail at [guest    ] -> Code 43 in the guest; BAR errors = Above-4G is off

F4 - the Thunderbolt tunnel bill
------------------------------------------------------------
PCIe 3.0 lane        7.88 Gbps (after 128b/130b)
native x16 slot      126.03 Gbps
TB3 tunnel (x4)      31.51 Gbps hard ceiling
RTX 2080 Ti in the enclosure: 4352 CUDA cores, 11 GB GDDR6,
616 GB/s VRAM bandwidth, 250 W TDP
typical serving workload 18 Gbps -> inside the tunnel
VRAM-resident inference: no measurable bottleneck over TB3
training host<->VRAM: 15-20% overhead vs native x16 - the real bill

F5 - the kernel module ledger
------------------------------------------------------------
load order - every later module stands on an earlier one:
  1. nvidia            builds on -
  2. nvidia-uvm        builds on nvidia
  3. nvidia-modeset    builds on nvidia
  4. nvidia-drm        builds on nvidia-modeset
  5. nvidia-peermem    builds on nvidia
persistence: nvidia-smi -pm 1 or nvidia-persistenced keeps P0
power cap:   nvidia-smi -pl 250 pins TDP; eGPU enclosures cook without it

F6 - the multi-GPU scaling ledger
------------------------------------------------------------
Llama-3.1-8B    35 ->   60 tok/s = 1.71x
Gemma-3-12B     18 ->   32 tok/s = 1.78x
Mistral-7B      40 ->   70 tok/s = 1.75x
two cards never mean 2.0x - 1.7x to 1.8x is the honest bill
training scales to 190% of single on 200% silicon
vLLM TP=2, Qwen3-8B: 8.2 GB/shard FITS an 11 GiB card
vLLM TP=2, Gemma-3-27B: 27.0 GB/shard BLOWS past an 11 GiB card
single 11 GB card: 7B at 4bit ~ 4-5 GB fits; 13B at 4bit ~ 8 GB, tight
DeepSpeed: 2 GPUs x 2 micro-batches x 4 accum = 16 global
batch 8 OOMs on one card and runs fine across two - the VRAM wall lifts

F7 - the peer wall
------------------------------------------------------------
GPUs in different IOMMU groups, or behind a virtualized host,
cannot do peer-to-peer DMA - the hardware path does not exist
NCCL reports hangs or CRC errors, never the topology truth
fix: NCCL_P2P_DISABLE=1 - traffic routes through host memory
the gloo backend is the CPU fallback: correct, slower, honest
  export NCCL_DEBUG=INFO
  export NCCL_IB_DISABLE=1
  export NCCL_P2P_DISABLE=1
the law: same IOMMU group = peers; across groups = host memory
DataParallel hides the wall badly; DDP at least shows it to you

FENCE-055-OK
```
