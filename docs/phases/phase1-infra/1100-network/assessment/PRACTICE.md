---
Document ID: 1100-PRACTICE
Title: "1100: Network - Practice"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Beginner
Estimated Time: 1 hour
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'networking', 'wan']
---

# 1100: Network - Practice

**Module:** Network Infrastructure for AI

**Document ID:** 1100

**Difficulty:** ⭐ Beginner

**Time:** 2-3 hours

---

## Exercises

### Exercise 1: Network Requirements Analysis

**Task:** Analyze network requirements for an AI training setup.

**Scenario:** You're setting up a home AI lab with:

- 1 GPU workstation (3090/4090)
- 1 CPU-only inference server
- 1 NAS for model storage

**Questions:**

1. What minimum bandwidth do you need between workstation and NAS?
2. Do you need a fiber uplink (e.g., GPON) for this setup?
3. What latency is acceptable for training?
4. When would fiber be necessary?

**Answer:**

1. 1Gbps is sufficient (model weights load once per session)
2. No, copper Ethernet is adequate for home setup
3. Latency doesn't affect training (only distributed training needs low latency)
4. When training across locations or downloading huge datasets frequently

---

### Exercise 2: Network Topology Design

**Task:** Design network topology for small AI team (5 people).

**Requirements:**

- Shared GPU server (4x A100)
- Individual workstations
- Model storage (50TB)
- Internet connectivity

**Draw diagram showing:**

- Switch placement
- VLAN separation (if needed)
- Backup considerations

**Solution:**
```text
Internet (Fiber 1Gbps)
    |
[Router/Firewall]
    |
[10Gbps Switch]
    |
    +--[VLAN 10: Workstations]-- 5x Workstations
    +--[VLAN 20: GPU Server]-- 4x A100 Server
    +--[VLAN 30: Storage]-- NAS (50TB)
```

---

### Exercise 3: Shared vs Dedicated Uplink

**Task:** Compare a shared consumer uplink (GPON as the example) with dedicated fiber for AI workloads.

**Create table comparing:**

| Feature | GPON | Dedicated Fiber |
|---------|------|-----------------|
| Bandwidth | ? | ? |
| Latency | ? | ? |
| Cost | ? | ? |
| Use Case | ? | ? |

**Solution:**

| Feature | GPON | Dedicated Fiber |
|---------|------|-----------------|
| Bandwidth | 2.5Gbps shared | 1-10Gbps dedicated |
| Latency | 10-20ms | 1-5ms |
| Cost | Low ($50-100/mo) | High ($500-2000/mo) |
| Use Case | Home, small lab | Data center, multi-site training |

---

### Exercise 4: Bandwidth Calculation

**Task:** Calculate download time for Llama 3.3 70B (Q4_K_M).

**Given:**

- Model size: ~42 GB
- Connection: GPON 2.5 Gbps (actual ~200 MB/s)

**Calculate:**

- Download time at 100% speed
- Realistic time (80% efficiency)
- At 1Gbps copper Ethernet

**Solution:**

- Theoretical: 42 GB / 200 MB/s = 210 seconds = 3.5 minutes
- Realistic: 42 GB / 160 MB/s = ~4.4 minutes
- 1Gbps: 42 GB / 100 MB/s = ~7 minutes

---

### Exercise 5: Troubleshooting Network Issues

**Scenario:** Training job failing with timeout errors.

**Symptoms:**

- Training to network storage
- Random timeouts during checkpoint saves
- Local training works fine

**Debug steps:**

1. Check network stats: `iperf3` between GPU server and NAS
2. Monitor errors: `dmesg | grep -i error`
3. Check cable quality (CAT6 vs CAT5e)
4. Verify switch port settings (duplex, speed)

**Common fixes:**

- Replace CAT5e with CAT6a
- Enable flow control on switch
- Use local SSD for checkpoints, sync to NAS later

**Success Criteria:** Checkpoint saves complete without timeouts; `iperf3` sustains expected throughput between GPU server and NAS for 60+ minutes.

---

## Project

**Build a home AI network:**

1. **Hardware:**
   - 10Gbps switch (used enterprise gear, e.g., Mikrotik/Ubiquiti)
   - CAT6a cables
   - WiFi 6 AP for management

2. **Configuration:**
   - Separate VLAN for GPU server
   - Jumbo frames (9000 MTU) for internal traffic
   - Bonded interfaces for NAS

3. **Test:**
   - `iperf3` between all nodes
   - Measure actual model download speeds
   - Test checkpoint save/restore

---

**Completed:** ___ / 5 exercises

**Project:** ___ / 3 steps

## Next Steps

- Review **[QUIZ.md](./QUIZ.md)** to test your knowledge
