---
Document ID: 1103
Title: Jumbo Frames and MTU Optimization
Phase: 1
Module: 1100
Last Updated: 2026-09-25
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'networking', 'hardware']
---

# 1103: Jumbo Frames and MTU Optimization

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [MTU Fundamentals](#mtu-fundamentals)
- [Mathematics of MTU](#mathematics-of-mtu)
- [Configuration by Component](#configuration-by-component)
- [Path MTU Discovery (PMTUD)](#path-mtu-discovery-pmtud)
- [Performance Benchmarks](#performance-benchmarks)
- [Troubleshooting MTU Issues](#troubleshooting-mtu-issues)
- [MTU by Use Case](#mtu-by-use-case)
- [Summary Configuration](#summary-configuration)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain the reasoning behind MTU Fundamentals
- Explain Mathematics of MTU
- Apply Configuration by Component
- Explain Path MTU Discovery (PMTUD)
- Measure and evaluate Performance Benchmarks
- Diagnose and resolve MTU Issues

---

## Abstract
Jumbo Frames enable Ethernet packets larger than the standard 1500 bytes, reducing CPU overhead and increasing throughput for large data transfers. On any high-throughput LAN (gigabit and above), MTU 9000 provides measurable performance benefits.

## MTU Fundamentals

### Standard vs Jumbo Frames
```text
Standard MTU 1500:  ~718 packets/MB (IPv4, 1460-byte payload)
Jumbo MTU 9000:     ~117 packets/MB (8966-byte payload)
Reduction:          ~84% fewer packets
```

### Why It Matters
```text
For an 11GB model file transfer over the LAN:
MTU 1500: ~7,500,000 packets → High CPU overhead
MTU 9000: ~1,200,000 packets  → Low CPU overhead
```

## Mathematics of MTU

### Packet Processing Overhead
```text
CPU Cycles per packet interrupt: ~10,000 cycles
At 3.5GHz CPU: ~2.86µs per packet

MTU 1500 (11GB):
  Packets: 7,500,000
  CPU time: 7,500,000 × 2.86µs = 21.5 seconds

MTU 9000 (11GB):
  Packets: 1,200,000
  CPU time: 1,200,000 × 2.86µs = 3.4 seconds
```

### Throughput Efficiency
```text
Effective Throughput = Line Rate × (Payload / Total Size)

MTU 1500 (IPv4):
  Payload: 1460 bytes
  Total: 1538 bytes (with headers)
  Efficiency: 94.9%

MTU 9000 (IPv4):
  Payload: 8966 bytes
  Total: 9038 bytes
  Efficiency: 99.2%

Gain: 4.3% more data per bit
```

## Configuration by Component

### 1. Switch Configuration
```text
# Most managed switches
system mtu 9216
# or per-port
interface 1/0/9
  mtu 9216
```

### 2. NAS or Storage Server (Linux)
```bash
# Set MTU immediately (replace eth0 with your interface name)
ip link set dev eth0 mtu 9000

# Make it persistent, RHEL-style (/etc/sysconfig/network-scripts/ifcfg-eth0):
MTU=9000

# Or Debian-style (/etc/network/interfaces):
#   iface eth0 inet static
#       address 192.168.1.100/24
#       mtu 9000

# Apply
systemctl restart networking    # or: ifreload -a
```

### 3. Proxmox Host
```bash
# Edit /etc/network/interfaces
auto eno1
iface eno1 inet static
    address 192.168.1.10/24
    gateway 192.168.1.1
    mtu 9000

# Apply
ifreload -a
```

### 4. K3s Container Network
```yaml
# Flannel CNI configuration
# /etc/rancher/k3s/config.yaml
flannel-iface: eno1
flannel-mtu: 9000

# Or for Cilium (MTU is normally auto-detected; override via extraConfig)
helm install cilium cilium/cilium \
  --set tunnel=vxlan \
  --set extraConfig.mtu=9000
```

### 5. Windows Client
```powershell
# Get interface name
Get-NetIPInterface

# Set MTU
Set-NetIPInterface -InterfaceAlias "Ethernet" -MTU 9000
```

## Path MTU Discovery (PMTUD)

### How It Works
```text
Host A (MTU 9000) → Host B (MTU 1500)
                    ↓
                [DF bit set]
                    ↓
            Router sends "Fragmentation Needed"
                    ↓
            Host A reduces MSS for this path
```

### Common PMTUD Issues
```text
Problem: Black hole router (drops ICMP)
Solution: Clamp MSS to safe value
```

### MSS Clamping
```bash
# On router/edge device
iptables -t mangle -A FORWARD -p tcp \
  --tcp-flags SYN,RST SYN \
  -j TCPMSS --clamp-mss-to-pmtu
```

## Performance Benchmarks

### iperf3 Results (Storage Server ↔ GPU Server, multi-gigabit LAN)
```text
MTU 1500:
  [ ID] Interval           Transfer     Bitrate
  [  4]   0.00-60.00 sec  15.6 GBytes  2.23 Gbits/sec

MTU 9000:
  [ ID] Interval           Transfer     Bitrate
  [  4]   0.00-60.00 sec  16.8 GBytes  2.40 Gbits/sec

Improvement: 7.6% throughput
CPU Usage: -15% during transfer
```

### Large File Transfer (SMB)
```text
11GB Model File:
  MTU 1500: 38 seconds → 2.30 Gbps avg
  MTU 9000: 36 seconds → 2.44 Gbps avg
  Improvement: ~6% faster transfer
```

## Troubleshooting MTU Issues

### Test MTU Path
```bash
# Linux
ping -M do -s 8972 192.168.1.10

# Windows
ping 192.168.1.10 -f -l 8972

# Success = "Reply from..."
# Failure = "Packet needs to be fragmented"
```

### Check Current MTU
```bash
# Linux
ip link show dev eth0
# Look for "mtu 9000"

# Windows
netsh interface ipv4 show subinterfaces
```

### Common Issues
| Symptom | Cause | Solution |
|---------|-------|----------|
| Intermittent drops | MTU mismatch | Verify end-to-end MTU |
| Slow transfers | PMTUD failure | Enable MSS clamping |
| Connection timeout | DF bit + low MTU | Reduce MTU or fix router |

## MTU by Use Case

```text
Use Case                    Recommended MTU
─────────────────────────────────────────────
General Internet           1500 (ISP limit)
LAN (NAS to Workstation)   9000
K8s Pod-to-Pod             9000
Storage (NFS/iSCSI)        9000
VPN (Wireguard)            1420 (tunnel overhead)
Video Streaming            1500 (compatible)
```

## Summary Configuration

### End-to-End MTU 9000 Path
```text
[Switch Port] ← MTU 9000 ←
      ↓
[NAS / Storage Server] ← MTU 9000 ←
      ↓
[High-Throughput LAN Link]
      ↓
[Server Port] ← MTU 9000 ←
      ↓
[Proxmox Bridge] ← MTU 9000 ←
      ↓
[K3s Pod Network] ← MTU 9000
```

---

## References

### Related ai-engineering-curriculum Documents

- [1101: Internet Uplink & Modem Configuration](1101-Fiber-GPON-Modem.md)
- [1102: Network Topology Design](1102-Star-Topology-Core.md)

---

## Next Steps

- Next Module: **[1200: Virtualization](../1200-virtualization/)**
- Continue with: **[1201: Proxmox Hypervisor SOP](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1102: Network Topology Design](./1102-Star-Topology-Core.md)
- [1201: Proxmox Hypervisor](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)
- [1301: K3s Master-Worker Architecture](../1300-kubernetes/1301-K3s-Master-Worker-Arch.md)

