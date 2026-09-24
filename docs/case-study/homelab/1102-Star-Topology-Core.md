---
Document ID: 1102
Title: Star Topology Core Network Design
Phase: 1
Module: 1100
Last Updated: 2026-02-05
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'networking', 'hardware']
---

# 1102: Star Topology Core Network Design

## Abstract
The star topology forms the backbone of AI Engineering Curriculum's network, enabling 2.5Gbps connectivity between all critical infrastructure components. A central switch acts as the "Star-Hub" distributing packets to all endpoints.

## Topology Diagram

```text
                    ┌─────────────────────────────────────┐
                    │      2.5Gbps Managed Switch #1      │
                    │         (Star Topology Hub)         │
                    │                                     │
                    │  Port 1: WAN (GPON ONT)             │
                    │  Port 2-4: Salon Devices            │
                    │  Port 5-8: Office/Lab               │
                    │  Port 9:    NAS LAN3                │
                    │  Port 10:   NUC Proxmox             │
                    │  Port 11-16: 2.5G Expansion         │
                    └─────────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ↓                        ↓                        ↓
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │   Salon     │          │   Office    │          │  Server     │
    │  Zone       │          │   Zone      │          │  Zone       │
    └─────────────┘          └─────────────┘          └─────────────┘
```

## Hardware Specifications

### Switch Requirements
| Specification | Minimum | Recommended |
|---------------|---------|-------------|
| Speed | 2.5Gbps | 10Gbps |
| Backplane | 50Gbps+ | 100Gbps+ |
| Buffer | 8MB+ | 16MB+ |
| MTU Support | 9000 | 9000+ |

### Recommended Models
- **Q-NAP QSW-2104-1T**: 4-port 2.5G with 10G uplink
- **Zyxel XGS1210-12**: 12-port Multi-Gig with 10G
- **TP-Link TL-SG3210XHP**: 10-port 2.5G Smart Switch

## Packet Flow Analysis

### Path 1: NAS → NUC (AI Training)
```text
[NAS LAN3 @ 2.5G] → [Switch] → [NUC @ 2.5G]
Latency: <0.5ms
Jumbo Frames: Enabled (MTU 9000)
```

### Path 2: Internet → All Devices
```text
[GPON ONT] → [Switch Port 1] → [Broadcast to all]
NAT: Handled by router on Port 1
DHCP: Handled by router
```

### Path 3: NUC → eGPU (TB3 Internal)
```text
Not network path - PCIe tunnel over Thunderbolt 3
Bandwidth: ~32Gbps (4x PCIe 3.0)
```

## VLAN Configuration

### Recommended VLAN Layout
```text
VLAN 10 (Management):   Switch, APs, NAS
VLAN 20 (IoT):          Smart devices, isolated
VLAN 30 (Servers):      Proxmox, K3s nodes
VLAN 40 (Workstations): PC, NUC
VLAN 50 (Guest):        Guest network (isolated)
```

### Switch Port Configuration
```bash
# Example for most switches
interface 1/0/9
  description NAS-LAN3
  switchport mode trunk
  switchport trunk allowed vlan 10,30,40
  mtu 9216
  speed 2500full

interface 1/0/10
  description NUC-Proxmox
  switchport mode access
  switchport access vlan 30
  mtu 9216
  speed 2500full
```

## Traffic Management

### QoS Priority Queue
```text
Priority 1 (Highest):   VoIP, SSH
Priority 2:             K8s API, Storage I/O
Priority 3:             General traffic
Priority 4 (Lowest):    Bulk transfer, Backup
```

### Flow Control
```text
802.3x Flow Control: ENABLED (prevents packet loss)
PFC (Priority Flow Control): Consider for 10G upgrade
```

## Performance Optimization

### 2.5Gbps Real-World Throughput
```text
Protocol     Theoretical    Real-World     Efficiency
─────────────────────────────────────────────────────
TCP (IPv4)   2.5 Gbps       2.3-2.4 Gbps   92-96%
TCP (IPv6)   2.5 Gbps       2.3-2.4 Gbps   92-96%
SMB (Win)    2.5 Gbps       2.2-2.3 Gbps   88-92%
NFS (Linux)  2.5 Gbps       2.3-2.4 Gbps   92-96%
```

### Link Aggregation (LACP)
For NAS with multiple LAN ports:
```text
NAS LAN1 + LAN2 + LAN3 → LAGG → Switch Port 20-22
Result: 7.5Gbps theoretical (6Gbps real-world)
```

## Monitoring & Diagnostics

### SNMP Monitoring
```bash
# Enable SNMP on switch
snmp-server community "public" RO
snmp-server enable traps

# Monitor from NAS
snmpwalk -v2c -c public <switch-ip> IF-MIB::ifHCInOctets
```

### Port Statistics to Monitor
- **CRC Errors**: Physical layer issues
- **Collisions**: Duplex mismatch
- **Discards**: Buffer overflow
- **Pause Frames**: Flow control activity

## Integration Points

| Connection | Switch Port | VLAN | Speed |
|------------|-------------|------|-------|
| GPON ONT | 1 | trunk | 1G |
| Router | 2 | trunk | 2.5G |
| NAS LAN3 | 9 | 10,30,40 | 2.5G |
| NUC Proxmox | 10 | 30 | 2.5G |
| Salon AP | 3-4 | 10,40 | 1G/2.5G |
| Office PC | 5-6 | 40 | 2.5G |

---

## Next Steps

- Continue with: **[1103: Jumbo Frames and MTU](../../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md)**
- Practical: **[LAB-001: Docker & LLM](../../learning-resources/labs/LAB-001-Docker-LLM.md)**
- Assessment: **[Phase 1 Quiz](../../00-META/assessment/phase1-quiz.md)**

---

**Related Documents:**
- [1101: Fiber GPON Modem](./1101-Fiber-GPON-Modem.md)
- [1103: Jumbo Frames and MTU](../../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md)
- [1301: K3s Architecture](../../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md)

**Experiment Template:** `experiments/EXP_1102_STAR_TOPO.md`
