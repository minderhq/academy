---
Document ID: 1101
Title: Internet Uplink & Modem Configuration
Phase: 1
Module: 1100
Last Updated: 2026-09-25
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Prerequisites: Basic networking knowledge
Related: [1102, 1103, 1201]
Tags: [networking, wan, uplink, bridge-mode, isp]
Hardware: [WAN uplink (fiber ONT, cable modem, DSL modem, or fixed-wireless CPE), Ethernet router]
Software: [Web browser, terminal]
---

# 1101: Internet Uplink & Modem Configuration

## Abstract

Every AI lab starts with a WAN uplink: the connection between your network and the internet. This document covers the common uplink technologies (fiber, cable, DSL, fixed wireless), how to configure the provider modem or gateway in router mode vs bridge mode, MTU considerations, and how to verify that your uplink actually delivers the throughput you are paying for. It closes with the safest ways to expose self-hosted AI services to the internet.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. WAN Uplink Technologies](#2-wan-uplink-technologies)
- [3. Router Mode vs Bridge Mode](#3-router-mode-vs-bridge-mode)
- [4. MTU Considerations](#4-mtu-considerations)
- [5. Verifying Uplink Throughput](#5-verifying-uplink-throughput)
- [6. Exposing Lab Services to the Internet](#6-exposing-lab-services-to-the-internet)
- [7. Troubleshooting](#7-troubleshooting)
- [8. Summary](#8-summary)
- [Case Study: Fiber GPON Uplink](#case-study-fiber-gpon-uplink)

---

## 1. Overview

### 1.1 Purpose

The WAN uplink is the entry point for internet connectivity in your lab. Everything else in this course - the star topology, the hypervisor, the GPU node - sits behind it. Getting the uplink configured correctly matters for two reasons:

1. **Throughput**: Downloading model weights (often 5-40 GB each) is bandwidth-bound. A misconfigured uplink slows every `pull` and `wget` you run.
2. **Control**: You want *your* router, not the ISP's combo box, to own NAT, DHCP, and firewall decisions.

### 1.2 Prerequisites

- Basic understanding of networking concepts (IP addressing, NAT, DHCP)
- Access to the administrative interface of your modem/gateway
- An active internet subscription of any type
- An Ethernet cable (Cat5e or better) from the modem to your router

### 1.3 Learning Objectives

After completing this document, you will be able to:

- Identify which WAN technology you have and its realistic performance ceiling
- Decide between router mode and bridge mode, and configure each
- Set a correct MTU for your uplink type
- Measure real uplink throughput and latency with `iperf3` and `ping`
- Expose a self-hosted service safely, understanding the risks

---

## 2. WAN Uplink Technologies

### 2.1 Technology Comparison

There is no single "correct" uplink. Any of the technologies below can run this course; what changes is the hardware at your edge and the performance ceiling.

| Technology | Typical Downstream | Typical Upstream | Media | Notes |
|------------|-------------------|------------------|-------|-------|
| **Fiber (e.g., GPON)** | 300 Mbps - 10 Gbps | Symmetric or 2:1 | Optical | Signal carried to an ONT/ONU box; Ethernet out |
| **Cable (DOCSIS 3.1)** | 100 Mbps - 2 Gbps | 10-100 Mbps | Coax | Shared bandwidth with neighbors; asymmetry common |
| **DSL / VDSL2 / G.fast** | 20-300 Mbps | 5-100 Mbps | Telephone line | Performance degrades with distance from the DSLAM |
| **Fixed wireless / 5G FWA** | 50-1000 Mbps | Variable | Radio | Latency and throughput vary with congestion and weather |
| **Cellular (LTE/5G hotspot)** | 20-500 Mbps | Variable | Radio | Usable fallback; NAT and CGNAT complicate inbound access |

### 2.2 Example: GPON Fiber Architecture

Fiber deployments such as GPON (Gigabit Passive Optical Network) are one common example. The provider terminates a shared optical signal at a passive splitter, and a small ONT box in your home converts light back to Ethernet:

```text
OLT (provider equipment)
    | (fiber, up to ~20 km)
Passive splitter (1:32 or 1:64)
    | (fiber to each subscriber)
ONT / ONU (your premises) --> Ethernet --> your router
```

Key properties of the fiber example:

| Property | Typical Value |
|----------|---------------|
| Downstream (shared) | 2.488 Gbps (GPON) or 10 Gbps (XGS-PON) |
| Upstream (shared) | 1.244 Gbps (GPON) |
| Optical receive power | -8 to -28 dBm (check the ONT status page) |

The same pattern applies to every technology: a provider-owned device converts the carrier medium to Ethernet, and your job is to make sure the *routing* happens on equipment you control.

---

## 3. Router Mode vs Bridge Mode

### 3.1 The Double NAT Problem

Most ISPs ship a combined modem + router + Wi-Fi gateway. In its default **router mode**, that box performs NAT itself, and if you attach your own router behind it, packets traverse **two** NAT layers:

```text
Internet --> [ISP gateway: NAT #1] --> [Your router: NAT #2] --> Lab
```

Double NAT works for outbound traffic but causes:

- Broken or unreliable inbound port forwarding (which gateway forwards the port?)
- Game/VoIP/STUN quirks and duplicate DHCP servers
- Two firewall rule sets to maintain

### 3.2 Option A: Bridge Mode (Recommended)

Bridge mode disables routing/NAT on the provider box, passing the public IP straight through to your router:

```text
Internet --> [ISP gateway: bridge] --> [Your router: NAT, DHCP, firewall] --> Lab
```

Generic configuration steps (menu names vary by vendor):

```text
1. Log in to the gateway admin UI (usually http://192.168.100.1 or http://192.168.1.1)
2. Navigate to WAN / Internet / Connection settings
3. Set operating mode: Bridge
4. If asked, set the ISP VLAN ID (commonly required on fiber; 0 = untagged elsewhere)
5. Disable the gateway's Wi-Fi radios
6. Apply and let the gateway reboot
7. Reboot your own router - it should now receive the public IP on its WAN port
```

Verification - the WAN IP on your router should match your public IP:

```bash
# From a client behind your router - the public IP as seen from the internet:
curl -s ifconfig.me

# On the ROUTER itself (SSH session, or its UI's WAN status page) - the WAN address:
ip addr show
# If they match (and are not RFC1918/private), bridge mode is working
```

### 3.3 Option B: Router Mode with Demilitarized Zone (DMZ)

If the ISP gateway cannot be bridged (some are locked), put your router in the gateway's **DMZ**. The gateway forwards all unsolicited traffic to your router, which still applies its own firewall. It is functionally single-NAT from your lab's point of view, with the gateway still holding the public IP.

### 3.4 CGNAT Consideration

On cable, fixed wireless, and cellular uplinks, the ISP may apply **carrier-grade NAT (CGNAT)**: you never receive a routable public IP at all. Inbound hosting (Section 6) then requires a tunnel or relay (e.g., a VPN to a VPS with a public IP, Cloudflare Tunnel, or Tailscale Funnel). Check whether your router's WAN IP is in `100.64.0.0/10` - that range signals CGNAT.

---

## 4. MTU Considerations

MTU (Maximum Transmission Unit) is the largest packet size a link carries. Getting it wrong causes the classic "some sites load, others hang" symptom.

| Uplink Type | Typical WAN MTU | Why |
|-------------|-----------------|-----|
| Ethernet/fiber, DHCP | 1500 | Standard Ethernet payload |
| PPPoE (common on DSL/fiber) | 1492 | 8 bytes consumed by PPPoE header |
| Some mobile/fixed wireless | 1420-1440 | Tunnel overhead varies |

```bash
# Discover the largest unfragmented payload to a public host
# Linux (8972 + 28 bytes of IP/ICMP headers = 9000 for jumbo LANs;
#        for a 1500 WAN, start at 1472):
ping -M do -s 1472 -c 3 1.1.1.1

# Windows equivalent:
ping 1.1.1.1 -f -l 1472
```

If the probe fails, lower the payload in 10-byte steps until it succeeds; add 28 to find the true MTU.

MSS clamping on your router is the belt-and-braces fix for paths that drop the "Fragmentation Needed" ICMP messages PMTUD relies on:

```bash
# On your router (iptables example):
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
  -j TCPMSS --clamp-mss-to-pmtu
```

Note: jumbo frames (MTU 9000) are a **LAN-only** optimization. See [1103: Jumbo Frames and MTU](./1103-Jumbo-Frames-and-MTU.md) - the WAN link stays at 1500/1492.

---

## 5. Verifying Uplink Throughput

Marketing numbers describe the best case. Measure what you actually get.

### 5.1 Latency Baseline

```bash
# Round-trip time to a nearby well-connected host
ping -c 20 1.1.1.1

# Reference points:
#   Fiber / cable:        2-30 ms
#   DSL:                  10-40 ms
#   Fixed wireless / 5G:  20-80 ms
#   Satellite LEO:        30-80 ms
```

Latency matters for interactive AI workloads (streaming tokens to a remote client, pulling from Hugging Face).

### 5.2 iperf3 Against a Public Server

Many public `iperf3` servers exist (search "public iperf3 servers" for a current list), or use a VPS you control:

```bash
# On the VPS:
iperf3 -s

# From your lab (download test, 4 parallel streams):
iperf3 -c <vps-ip> -P 4 -R -t 30

# Upload test:
iperf3 -c <vps-ip> -P 4 -t 30
```

### 5.3 Interpreting Results

```text
Observed vs advertised:
  >= 90% of plan     : healthy
  60-90% of plan     : normal for shared media (cable) at peak hours
  < 60% of plan      : investigate (Section 7)

Asymmetric links: upload may be 5-20x slower than download.
Self-hosting visitors will be limited by UPLOAD bandwidth.
```

---

## 6. Exposing Lab Services to the Internet

Self-hosting an OpenAI-compatible API or a Grafana dashboard is a common goal. There are two mainstream patterns.

### 6.1 Port Forwarding

Forward a specific external port to an internal host:

```text
WAN :8443 --> 192.168.1.50:8443   (e.g., inference API on your GPU server)
```

**Security warning - read before opening any port:**

- Exposing an LLM API keylessly means anyone on the internet can burn your GPU hours. Always put authentication (reverse proxy with TLS + auth, API gateway) in front of the service.
- Forward only the exact ports needed; never use DMZ-toward-a-lab-host.
- Keep the host patched; an exposed K3s API server or hypervisor UI is a critical incident waiting to happen.
- Prefer inbound-allow-nothing designs (Section 6.2) when possible.

### 6.2 Outbound Tunnels (Safer Default)

Instead of allowing inbound connections, establish an outbound tunnel from the lab to a relay:

- **WireGuard/Tailscale to a VPS**: the VPS holds the public IP and reverse-proxies to the lab over the tunnel.
- **Cloudflare Tunnel**: no public IP required at all; also a workaround for CGNAT.

```text
[User] --> [VPS / edge] <--outbound WireGuard tunnel-- [Lab service]
```

No firewall ports are opened on your uplink, and the attack surface moves to the VPS, where it is easier to monitor and rebuild.

---

## 7. Troubleshooting

### 7.1 Common Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Frequent disconnects (fiber) | Marginal optical signal | Check Rx power in ONT status page (-8 to -28 dBm); call ISP if out of range |
| Some websites hang | MTU mismatch / PMTUD black hole | Lower MTU or enable MSS clamping (Section 4) |
| Cannot reach lab from outside | Double NAT or CGNAT | Bridge mode, DMZ, or outbound tunnel (Sections 3, 6.2) |
| Speed far below plan at all hours | Old modem / negotiation at 100 Mbps | Check link speed on router WAN port; request modem swap |
| Slow only at peak hours | Shared-media congestion (cable/fixed wireless) | Expected; measure at different times |
| Public IP starts with 100.64-100.127 | CGNAT | Use tunnel-based exposure |

### 7.2 Diagnostic Commands

```bash
# What IP does the world see for us?
curl -s ifconfig.me

# Is the WAN interface in bridge mode? (run on router)
ip -4 addr show | grep -A 2 <wan-iface>

# Latency and loss over 60 seconds
ping -c 60 1.1.1.1 | tail -3

# Trace where the path breaks
traceroute 1.1.1.1
```

---

## 8. Summary

- Any uplink technology (fiber, cable, DSL, fixed wireless) can host this course; know your realistic ceiling.
- Prefer **bridge mode** so your router owns NAT, DHCP, and the firewall; use DMZ if the gateway cannot be bridged.
- Match MTU to the uplink type (1500, or 1492 under PPPoE) and clamp MSS as a safety net.
- Measure real throughput with `iperf3`; upload bandwidth governs self-hosting.
- Expose services via outbound tunnels when possible; if you port-forward, authenticate everything.

---

## Case Study: Fiber GPON Uplink

The original build this course was developed on used a fiber GPON uplink, so the generic flow above (bridge mode, MTU, throughput verification) looked like this in practice.

**Line parameters.** GPON carries the whole downstream on a shared wavelength; the ITU-T G.984 family defines the split:

| Parameter | Value |
|-----------|-------|
| Downstream (shared) | 2.488 Gbps |
| Upstream (shared) | 1.244 Gbps |
| Wavelengths | 1490 nm (down), 1310 nm (up) |
| Split ratio at the street cabinet | 1:32 typical (1:64 allowed) |

**Optical budget.** The ONT status page exposes receive/transmit power. The build treated these ranges as healthy:

| Metric | Acceptable range |
|--------|------------------|
| Rx power | -8 to -28 dBm |
| Tx power | 0 to +7 dBm |
| ONT temperature | < 70 C |

Out-of-range Rx power shows up as LOS light loss or intermittent drops long before throughput tests fail (Section 7.1).

**Signal path.** After bridge mode, the physical chain was:

```text
[ISP OLT] --fiber--> [splitter] --fiber--> [ONT] --CAT6A--> [2.5G switch, port 1]
                                                                  |
                        +-----------------------------------------+
                        |                    |                    |
                   living-room            office              NAS (LAN3)
                   devices + AP           workstation         Synology
```

**Measured throughput.** The 2.488 Gbps shared downstream translates to roughly 2.2-2.3 Gbps of real TCP goodput after overhead. Read the "healthy" threshold in Section 5.3 against the shared rate, not the marketing number on the plan.

**Redundancy.** For an uplink this critical to model downloads, the build planned a WAN bypass path, which the generic sections do not cover:

1. **4G/5G backup**: a USB LTE modem as a secondary WAN on the router.
2. **Multi-WAN**: policy routing or load balancing between GPON and the backup.
3. **Failover**: automatic switchover when the GPON link drops, so long-running weight downloads survive an ISP outage.

---

## References

### Related ai-engineering-curriculum Documents

- [1102: Network Topology Design](1102-Star-Topology-Core.md)
- [1103: Jumbo Frames and MTU Optimization](1103-Jumbo-Frames-and-MTU.md)
- [1201: Proxmox Hypervisor Standard Operating Procedures](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)

---

## Next Steps

- Continue with: **[1102: Network Topology Design](./1102-Star-Topology-Core.md)**
- Practical: **[LAB-001: Docker & LLM](../../../learning-resources/labs/LAB-001-Docker-LLM.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**

---

**Related Documents:**
- [1102: Network Topology Design](./1102-Star-Topology-Core.md) - LAN design behind the uplink
- [1103: Jumbo Frames and MTU](./1103-Jumbo-Frames-and-MTU.md) - LAN MTU optimization
- [1201: Proxmox Hypervisor SOP](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md) - The server that sits behind this uplink

**Case Study Experiment:** [EXP_1101: GPON Configuration](../../../../experiments/EXP_1101_GPON.md) - a hands-on fiber (GPON) example from the original build

---

**Document ID:** 1101
**Status:** Complete
**Related Documents:** [1102, 1103, 1201]
