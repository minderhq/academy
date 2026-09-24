# EXP_1101_GPON: Fiber GPON Modem Configuration

## Experiment Information
- **Infrastructure Used:** GPON ONT → 2.5Gbps Switch #1 → Multiple endpoints
- **Date:** [TBD]
- **Hardware:** ISP-provided GPON ONT, QNAP QSW-2104-1T Switch
- **Parameters Tested:** Bridge mode, MTU settings, VLAN configuration

## Experiment Setup
```
Physical Connection:
[ISP Fiber] → [GPON ONT] → [Port 1: Switch] → [Clients]
```

## Configuration Steps Taken

### 1. Bridge Mode Configuration
- Accessed ONT interface at 192.168.100.1
- Enabled bridge mode
- Disabled wireless
- Result: Public IP assigned to downstream router

### 2. Switch Configuration
```
Switch Model: QNAP QSW-2104-1T
Port 1: WAN (GPON)
Port 9: NAS LAN3
Port 10: NUC Proxmox
MTU: 9000 (tested)
```

## Measurements

### Without Jumbo Frames (MTU 1500)
```
iperf3 (NAS → NUC):
  [ ID] Interval           Transfer     Bitrate
  [  5]   0.00-60.00 sec  15.2 GBytes  2.12 Gbits/sec
```

### With Jumbo Frames (MTU 9000)
```
iperf3 (NAS → NUC):
  [ ID] Interval           Transfer     Bitrate
  [  5]   0.00-60.00 sec  16.8 GBytes  2.40 Gbits/sec

Improvement: 13.2% throughput
```

## Lessons Learned
- MTU 9000 requires all devices in chain to support it
- Some NICs require manual MTU configuration
- TCP overhead reduction is measurable

## Next Steps
- [ ] Test with 10Gbps switch upgrade
- [ ] Measure latency improvements
- [ ] Document optimal MTU for different workloads

## Related Files
- [1101-Fiber-GPON-Modem.md](../docs/phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md)
- [1102-Star-Topology-Core.md](../docs/phases/phase1-infra/1100-network/1102-Star-Topology-Core.md)
