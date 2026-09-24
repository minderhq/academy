---
Document ID: 1101
Title: Fiber GPON Modem Configuration
Phase: 1
Module: 1100
Last Updated: 2026-02-05
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Prerequisites: Basic networking knowledge
Related: [1102, 1103, 1201]
Tags: [networking, fiber, gpont, bridge-mode, isp]
Hardware: [GPON ONT/ONU, Ethernet switch]
Software: [Web browser, terminal]
---

# 1101: Fiber GPON Modem Configuration

## Abstract

This document covers the GPON (Gigabit Passive Optical Network) modem configuration for AI Engineering Curriculum's network infrastructure. You will learn how to configure bridge mode, verify optical signal levels, and integrate the modem with a 2.5Gbps star topology network.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Technical Specifications](#2-technical-specifications)
- [3. Bridge Mode Configuration](#3-bridge-mode-configuration)
- [4. Signal Path Diagram](#4-signal-path-diagram)
- [5. Troubleshooting](#5-troubleshooting)
- [6. Integration with AI Engineering Curriculum](#6-integration-with-ai-engineering-curriculum)
- [7. WAN Bypass (Advanced)](#7-wan-bypass-advanced)
- [8. References](#8-references)

---

## 1. Overview

### 1.1 Purpose

The GPON modem serves as the entry point for fiber-optic internet connectivity in the AI Engineering Curriculum infrastructure. This document provides configuration guidance for optimal performance with 2.5Gbps networks.

### 1.2 Prerequisites

- Basic understanding of networking concepts
- Access to GPON modem administrative interface
- ISP-provided fiber connection
- Ethernet cable (CAT6A recommended for 2.5Gbps)

### 1.3 Learning Objectives

After completing this configuration, you will be able to:
- ✅ Configure GPON modem in bridge mode
- ✅ Verify optical signal levels
- ✅ Integrate modem with 2.5Gbps star topology
- ✅ Troubleshoot common fiber connectivity issues

---

## 2. Technical Specifications

### 2.1 GPON Architecture

```
OLT (Optical Line Terminal)
    ↓ (Fiber - up to 20km)
Splitter (Passive 1:N)
    ↓ (Fiber to each subscriber)
ONT/ONU (Optical Network Terminal/Unit) → Your Modem
```

### 2.2 Key Standards

| Standard | Description |
|----------|-------------|
| **ITU-T G.984** | GPON standard family |
| **Downstream** | 2.488 Gbps |
| **Upstream** | 1.244 Gbps |
| **Wavelengths** | 1490nm (down), 1310nm (up) |
| **Split Ratio** | Typically 1:32 or 1:64 |

---

## 3. Bridge Mode Configuration

### 3.1 Why Bridge Mode?

Bridge mode disables routing/NAT functions on the modem, allowing your downstream router to handle:
- Public IP assignment
- NAT translation
- DHCP server
- Firewall rules
- Port forwarding

### 3.2 Configuration Steps

#### Step 1: Access Modem Interface
```
Default Gateway: 192.168.100.1 or 192.168.1.1
Credentials: admin/admin (check ISP documentation)
```

#### Step 2: Enable Bridge Mode

Navigate to: **Advanced Settings → WAN Settings → Mode**

```
Mode: Bridge
VLAN ID: [ISP-specific, often 0 or disabled]
IGMP: Enabled (for IPTV if applicable)
```

#### Step 3: Disable Wireless (if applicable)
```
Wireless: Disabled
(in 2.4GHz and 5GHz bands)
```

#### Step 4: Save and Reboot
```
Apply Settings → Reboot ONT
```

---

## 4. Signal Path Diagram

```
[ISP OLT] --(Fiber)--> [Splitter] --(Fiber)--> [GPON ONT]
                                                    |
                                                    | (Ethernet)
                                                    ↓
                                            [2.5Gbps Switch #1]
                                                    |
                               +--------------------+--------------------+
                               |                    |                    |
                        [Salon Port]          [Office Port]         [NAS LAN3]
                               |                    |                    |
                               ↓                    ↓                    ↓
                          [PC/Devices]        [Access Point]      [Synology NAS]
```

---

## 5. Troubleshooting

### 5.1 Optical Signal Levels

Check optical power in modem interface:

| Metric | Acceptable Range |
|--------|------------------|
| **Rx Power** | -8 to -28 dBm |
| **Tx Power** | 0 to +7 dBm |
| **Temperature** | < 70°C |

### 5.2 Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| No LOS light | Fiber disconnected | Check SC/APC connector |
| Intermittent drops | Signal degradation | Contact ISP for line check |
| Cannot access modem | IP conflict | Use direct connection |

---

## 6. Integration with AI Engineering Curriculum

### 6.1 Hardware Connection

```
GPON ONT Port 1 ────────┐
                       │
                  [CAT6A/Ethernet]
                       │
         ┌─────────────┴─────────────┐
         │   2.5Gbps Switch #1       │
         │   Port 1 (WAN Input)      │
         └───────────────────────────┘
```

### 6.2 Throughput Considerations

- GPON theoretical: 2.488 Gbps downstream
- Real-world with TCP overhead: ~2.2-2.3 Gbps
- Switch upgrade to 2.5Gbps required for full utilization

---

## 7. WAN Bypass (Advanced)

For redundancy, consider:

1. **4G/5G Backup**: USB LTE modem on secondary router
2. **Multi-WAN**: Load balancing between GPON and backup
3. **Failover**: Automatic switch when GPON down

---

## 8. References

### Technical Standards
- [ITU-T G.984 Series](https://www.itu.int/rec/T-REC-G.984) - GPON standards

### Related AI Engineering Curriculum Documents
- [1102: Star Topology Core](./1102-Star-Topology-Core.md) - Switch configuration
- [1103: Jumbo Frames and MTU](../../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md) - MTU optimization
- [1201: Proxmox Hypervisor SOP](../../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md) - Virtualization setup

### Experiments
- [EXP_1101: GPON Configuration](../experiments/EXP_1101_GPON.md) - Hands-on modem configuration

### External Resources
- [GPON Technology Overview](https://en.wikipedia.org/wiki/Gigabit-capable_PON) - Wikipedia reference

---

## Next Steps

- Continue with: **[1102: Star Topology Core](./1102-Star-Topology-Core.md)**
- Practical: **[LAB-001: Docker & LLM](../../learning-resources/labs/LAB-001-Docker-LLM.md)**
- Assessment: **[Phase 1 Quiz](../../00-META/assessment/phase1-quiz.md)**

---

**Document ID:** 1101
**Last Updated:** 2026-02-05
**Status:** Complete
**Related Documents:** [1102, 1103, 1201]
