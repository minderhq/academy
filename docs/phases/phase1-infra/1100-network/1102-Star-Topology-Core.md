---
Document ID: 1102
Title: "1102: Network Topology Design"
Phase: 1
Module: 1100
Last Updated: 2026-10-08
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Prerequisites: [1101]
Related: [1103, 1201]
Tags: ['networking', 'topology', 'vlan', 'switch', 'star-topology']
Hardware: [Managed Ethernet switch, Cat5e/6/6a cabling, router]
Software: [Switch management CLI or web UI]
---

# 1102: Network Topology Design

## Abstract

The physical and logical layout of your network determines how well the AI lab performs under load. This document explains why a star topology is the default for small labs, how to select a switch, how to segment an AI lab into VLANs, and how to plan subnets and names so the network stays legible as it grows.

---

## Table of Contents

- [1. Overview](#1-overview)
- [Learning Objectives](#learning-objectives)
- [2. Why Star Topology](#2-why-star-topology)
- [3. Switch Selection](#3-switch-selection)
- [4. VLAN Segmentation for AI Labs](#4-vlan-segmentation-for-ai-labs)
- [5. Subnet and IP Planning](#5-subnet-and-ip-planning)
- [6. Naming Conventions](#6-naming-conventions)
- [7. Basic Switch Configuration](#7-basic-switch-configuration)
- [8. Cabling](#8-cabling)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Summary](#10-summary)
- [Case Study: A 2.5G Apartment Star Network](#case-study-a-25g-apartment-star-network)

---

## 1. Overview

### 1.1 Purpose

Before a single VM boots, decide how devices connect and how traffic flows. A deliberate topology prevents the two most common small-lab failure modes: daisy-chained devices that collapse under load, and a single flat network where a noisy training job starves the management interface.

### 1.2 Prerequisites

- [1101: Internet Uplink & Modem Configuration](./1101-Fiber-GPON-Modem.md) or equivalent
- Access to at least one managed switch (unmanaged works for a minimal two-node lab, but VLANs require managed)

## Learning Objectives
After completing this document, you will be able to:

- Justify star topology over daisy-chain or mesh-at-home alternatives
- Choose a switch using concrete criteria
- Design a VLAN plan for management, storage, compute, and serving traffic
- Allocate IPs in a way that survives growth
- Configure VLANs on a generic managed switch

---

## 2. Why Star Topology

In a star topology every device connects to a central switch:

```text
                    +-------------------------------------+
                    |        Managed Switch (hub)         |
                    |                                     |
                    |  Port 1:  WAN/router uplink         |
                    |  Port 2:  Hypervisor / GPU server   |
                    |  Port 3:  Storage server (optional) |
                    |  Port 4:  Workstation               |
                    |  Port 5+: Expansion                 |
                    +-----------------+-------------------+
                                      |
              +-----------------------+-----------------------+
              |                       |                       |
              v                       v                       v
        +----------+           +----------+            +----------+
        |  Server  |           | Storage  |            | Clients  |
        +----------+           +----------+            +----------+
```

### 2.1 Comparison with Alternatives

| Property | Star | Daisy-chain | Wi-Fi mesh |
|----------|------|-------------|------------|
| Any-to-any hop count | 2 (device-switch-device) | Up to N | 2-4 (via nodes) |
| Failure isolation | One cable affects one device | A dead mid-chain link splits the network | Variable |
| Deterministic latency | Yes | No (grows with chain depth) | No |
| Throughput under load | Full line rate per port | Shared along the chain | Radio-bound |
| Cabling effort | One cable per device | Minimal | None |

The decisive property for AI workloads is **deterministic bandwidth between storage and GPU nodes**. Moving an 11 GB model file over NFS while training logs stream to the same storage server is exactly the traffic pattern star topology handles and chains do not.

---

## 3. Switch Selection

You do not need exotic hardware. Evaluate any switch against this table:

| Criterion | Minimum | When it matters |
|-----------|---------|-----------------|
| Port speed | 1 Gbps all ports | Baseline; fine for a single-GPU lab |
| Multi-gig / 2.5G+ ports | Optional | Useful if your NICs support it and NFS transfers are slow |
| 10G uplink/SFP+ | Optional | Storage-heavy labs, multi-node clusters |
| Managed (VLANs) | Required for VLAN section | Unmanaged switches cannot create or assign VLANs (all ports effectively sit in VLAN 1) |
| Jumbo frame support (MTU 9216) | Recommended | Pairs with [1103](./1103-Jumbo-Frames-and-MTU.md) |
| Backplane capacity | >= 2x sum of all port speeds (full duplex) | Prevents blocking under full load |
| Fanless or quiet | Nice to have | Labs usually live in living spaces |

Selection guidance:

- **Two-node lab (server + workstation):** any unmanaged 1G switch works.
- **Lab with NAS or multi-GPU server:** managed switch with VLAN support; multi-gig ports optional.
- **Multi-node training:** managed switch, jumbo frames, and consider 10G on storage uplinks.

LACP (link aggregation) is a vendor-neutral way to add bandwidth between switch and storage server: two or four 1G ports behave as one logical link. It raises aggregate throughput but not single-stream speed.

---

## 4. VLAN Segmentation for AI Labs

VLANs split one physical switch into isolated logical networks. The value for an AI lab: management traffic stays reachable when a training run saturates the network, and serving traffic cannot reach the hypervisor's admin UI.

### 4.1 Example VLAN Plan

| VLAN ID | Name | Carries | Example Subnet |
|---------|------|---------|----------------|
| 10 | Management | Hypervisor UI, switch/AP admin, BMC/IPMI | 192.168.10.0/24 |
| 20 | Storage | NFS, iSCSI, backup traffic | 192.168.20.0/24 |
| 30 | GPU Compute | Node-to-node training traffic, cluster overlay | 192.168.30.0/24 |
| 40 | Inference | Serving APIs, ingress from users | 192.168.40.0/24 |
| 50 | Workstations (optional) | Personal devices, internet clients | 192.168.50.0/24 |

### 4.2 Design Rules

1. **Management VLAN is the most protected.** Only admin workstations get routed access to it.
2. **Storage VLAN is the most private.** It often has no gateway at all - if it cannot reach the internet, it cannot be attacked from it.
3. **Compute and inference can be separate**, so a batch-training broadcast storm never touches user-facing latency. On a two-node lab, a single combined VLAN is an acceptable simplification.
4. Inter-VLAN routing happens on the router/firewall (or a Layer-3 switch), with explicit allow rules only.

---

## 5. Subnet and IP Planning

Pick one subnet per VLAN and reserve ranges by role so that an IP address tells you what a machine is. The example below uses 192.168.1.0/24 for a flat (single-VLAN) starter lab; scale the pattern to the per-VLAN subnets above as you grow.

### 5.1 Example Allocation (192.168.1.0/24)

| Range | Role | Assignment method |
|-------|------|-------------------|
| 192.168.1.1 | Router/gateway | Static |
| 192.168.1.2-9 | Network gear (switch, APs) | Static |
| 192.168.1.10 | Hypervisor / primary server | Static (example used throughout this course) |
| 192.168.1.50 | GPU worker / second node | Static |
| 192.168.1.100 | NAS / storage server (optional) | Static |
| 192.168.1.150-199 | Workstations | DHCP reservation |
| 192.168.1.200-254 | Guest/DHCP pool | Dynamic |

### 5.2 Why Bother

- Static addresses for servers mean firewall rules, NFS exports, and K3s node configs never rot after a reboot.
- Role-based ranges make `grep 192.168.1.` in a config file immediately interpretable.
- Document the table in your repo (this file is the template); an undocumented static IP is a future outage.

---

## 6. Naming Conventions

Names should encode function, not brand or purchase date:

```text
Pattern:  <role><index>.<domain>

academy-gw1      - gateway/router
academy-sw1      - switch 1
academy-hv1      - hypervisor node 1 (example: 192.168.1.10)
academy-gpu1     - GPU worker node (example: 192.168.1.50)
academy-nas      - storage server (example: 192.168.1.100)
academy-ws1      - workstation
```

Rules of thumb:

- Lowercase, hyphen-separated, DNS-safe (K3s and NFS both embed hostnames in configs).
- Role first so tab-completion and `kubectl get nodes` group meaningfully.
- Keep the search domain short (`academy.local` or your own domain) and use it consistently for cluster-internal DNS.

---

## 7. Basic Switch Configuration

The CLI dialect varies by vendor (Cisco-style, NETGEAR, MikroTik, ProCurve...), but the concepts are identical. The example below is a Cisco-like generic dialect:

```text
! 1. Define the VLANs
vlan 10
  name MGMT
vlan 20
  name STORAGE
vlan 30
  name GPU-COMPUTE
vlan 40
  name INFERENCE

! 2. Trunk port to the server (carries multiple VLANs, 802.1Q tagged)
interface gi1/0/2
  description academy-hv1
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30,40
  mtu 9216

! 3. Access port to a plain client (one untagged VLAN)
interface gi1/0/4
  description workstation
  switchport mode access
  switchport access vlan 50
  mtu 9216

! 4. Trunk to the router (inter-VLAN routing lives here)
interface gi1/0/1
  description uplink-to-router
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30,40,50
```

On the Linux side (hypervisor or server), tagged VLANs are created as subinterfaces:

```bash
# /etc/network/interfaces (Debian/Proxmox style) - VLAN 20 for storage
auto eno1.20
iface eno1.20 inet static
    address 192.168.20.10/24
    vlan-raw-device eno1
```

Verify from a connected host:

```bash
ping -c 3 192.168.20.10     # storage VLAN reachable

# Confirm the subinterface is tagged with VLAN 20 (world-readable, no sudo needed):
grep VID /proc/net/vlan/eno1.20        # expect: VID: 20
```

---

## 8. Cabling

Copper Ethernet categories set the ceiling:

| Cable | 1 Gbps | 2.5/5G Multi-Gig | 10 Gbps | Notes |
|-------|--------|------------------|---------|-------|
| Cat5e | 100 m | 2.5G at 100 m; 5G needs Cat6 | Not rated | Adequate for most starter labs |
| Cat6 | 100 m | Supported | Up to ~55 m | Common sweet spot |
| Cat6a | 100 m | Supported | 100 m | Required for 10G across a room |

Practical rules:

- Buy pre-terminated cables; field-crimped ends are the top source of intermittent CRC errors.
- Avoid running copper parallel to power cables for long runs; cross at 90 degrees.
- Label both ends (a label maker pays for itself the first time you re-cable at midnight).
- Fiber (DAC or SFP+) only matters at 10G+ distances; not needed in a starter lab.

---

## 9. Troubleshooting

### 9.1 Common Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Device unreachable after VLAN change | Port still in access mode on old VLAN | Set trunk + allowed VLAN list (Section 7) |
| VLAN-tagged host gets no DHCP | No DHCP relay/helper on that VLAN | Add `ip helper-address <router>` or run DHCP per-VLAN |
| Intermittent slowdowns on one port | Bad cable / CRC errors | Replace cable; check port error counters |
| Can reach storage VLAN from workstation | Missing inter-VLAN ACL | Add deny rule on router between VLAN 50 and VLAN 20 |
| Switch reboots under load | Power budget exceeded (PoE models) | Check PoE draw vs budget |
| Everything works until jumbo frames enabled | One hop has MTU 1500 | Walk the path with `ping -M do -s 8972` (see [1103](./1103-Jumbo-Frames-and-MTU.md)) |

### 9.2 Diagnostic Commands

```bash
# Port error counters (CRC, collisions) - most switches expose via CLI:
show interfaces counters errors

# Verify which VLAN a port carries:
show interfaces gi1/0/2 switchport

# From a Linux host: confirm the interface is up and tagged correctly:
ip -d link show eno1.20
```

---

## 10. Summary

- Star topology (everything to one switch) is the correct default: deterministic latency, isolated failures, easy growth.
- Switch selection: managed + VLAN support is the one hard requirement; port speed beyond 1G is optional.
- Segment by traffic type (management / storage / compute / inference) so load and blast radius stay contained.
- Plan IP ranges by role and document them; static IPs for anything with a firewall rule or NFS export.
- Cat5e is enough for 1G; Cat6a covers 10G. Label your cables.

---

## Case Study: A 2.5G Apartment Star Network

The original build ran a 16-port 2.5G managed switch through a small apartment with three zones - the generic star above with real port assignments:

```text
             +--------------------------------------------+
             |        2.5G managed switch (star hub)      |
             |  P1 WAN (ONT)        P5-8 office/lab       |
             |  P2-4 living room    P9 NAS      P10 NUC   |
             |  P11-16 expansion                          |
             +---------------------+----------------------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
   living room                office                    server
   AP, media, IoT             workstation, lab PC       NAS, NUC (Proxmox)
```

**Packet flows that justified the design:**

| Flow | Path | Why it matters |
|------|------|----------------|
| Model transfer NAS -> NUC | NAS LAN3 (P9) -> switch -> NUC (P10) | < 0.5 ms, jumbo frames (MTU 9000) on both ends |
| Internet -> all devices | ONT (P1) -> switch -> everywhere | NAT/DHCP on the router behind bridge mode (see [1101](./1101-Fiber-GPON-Modem.md)) |
| NUC -> eGPU | Not a network path | PCIe tunnel over Thunderbolt 3, ~32 Gbps - the switch never sees it |

**VLAN plan the build actually used** (different roles than the lesson table - a home needs an IoT quarantine):

| VLAN | Name | Carries |
|------|------|---------|
| 10 | Management | Switch, APs, NAS admin |
| 20 | IoT | Smart devices, isolated from everything else |
| 30 | Servers | Proxmox, K3s nodes |
| 40 | Workstations | PC, NUC desktop clients |
| 50 | Guest | Internet-only, fully isolated |

**Real-world 2.5G throughput:**

| Protocol | Theoretical | Measured | Efficiency |
|----------|-------------|----------|------------|
| TCP (IPv4) | 2.5 Gbps | 2.3-2.4 Gbps | 92-96% |
| SMB (Windows) | 2.5 Gbps | 2.2-2.3 Gbps | 88-92% |
| NFS (Linux) | 2.5 Gbps | 2.3-2.4 Gbps | 92-96% |

**QoS and flow control.** The switch queued by priority: SSH/VoIP highest, cluster API and storage I/O next, general traffic, bulk backup last. 802.3x flow control stayed enabled so a saturated NFS stream degraded instead of dropping packets.

**LACP in practice.** The NAS aggregated LAN1+LAN2+LAN3 into one LAG: 7.5 Gbps theoretical, about 6 Gbps real-world for parallel streams - and no improvement for a single NFS stream, exactly the caveat Section 3 makes.

**Monitoring.** SNMP on the switch (`snmpwalk -v2c -c public <switch-ip> IF-MIB::ifHCInOctets` from the NAS), with periodic checks of per-port CRC errors, discards, and pause frames - the counters that catch cabling problems before users do.

---

## References

### Related Minder Academy Documents

- [1103: Jumbo Frames and MTU Optimization](1103-Jumbo-Frames-and-MTU.md)
- [1201: Proxmox Hypervisor Standard Operating Procedures](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)

---

## Next Steps

- Continue with: **[1103: Jumbo Frames and MTU](./1103-Jumbo-Frames-and-MTU.md)**
- Practical: **[LAB-001: Docker & LLM](../../../learning-resources/labs/LAB-001-Docker-LLM.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**

- [1101: Internet Uplink & Modem Configuration](./1101-Fiber-GPON-Modem.md)
- [1103: Jumbo Frames and MTU](./1103-Jumbo-Frames-and-MTU.md)
- [1201: Proxmox Hypervisor SOP](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)

**Case Study Experiment:** [EXP_1102: Star Topology and Network Performance Experiments](../../../../experiments/EXP_1102_STAR_TOPOLOGY.md) - hands-on topology and throughput experiments from the original build

---

**Document ID:** 1102

**Status:** Complete

**Related Documents:** [1103, 1201]
