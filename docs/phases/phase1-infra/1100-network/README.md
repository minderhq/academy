---
Document ID: 1100-NETWORK-README
Title: "1100: Network Fundamentals for LLM Infrastructure"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Beginner
Prerequisites: []
Estimated Time: 8 hours
Tags: ['module', 'networking', 'wan']
---

# 1100: Network Fundamentals for LLM Infrastructure

## Module Overview

This module covers networking fundamentals essential for deploying and operating LLM infrastructure, from hardware setup to network topology optimization. You'll learn how to build a high-performance network that supports model training, inference, and production deployment. Lesson 1104 closes the module with the protocol stack itself: the seven layers one request crosses, TCP versus UDP, DNS resolution, and the port and TLS handshake ledger.

## Why Networking Matters for LLMs

### 1. Model Serving & Inference

**Bandwidth Requirements:**

- **Small models (1-7B):** 100-500 Mbps per concurrent user
- **Medium models (13-34B):** 500 Mbps - 2 Gbps per concurrent user
- **Large models (70B+):** 2-10 Gbps per concurrent user

**Real-World Example:**
```text
Serving Llama-3.3-70B with 4-bit quantization:
- Model size: ~40 GB
- Token throughput: ~50 tokens/sec per GPU
- Network impact: ~500 Mbps per active inference request
- Recommended: 10 Gbps network for production
```

### 2. Distributed Training

**Network Types for Training:**

- **InfiniBand:** 200-400 Gbps, low latency (1µs) - Best for large clusters
- **RoCE (RDMA over Converged Ethernet):** 100-200 Gbps - Cost-effective alternative
- **Standard Ethernet:** 25-100 Gbps - Suitable for small clusters

**Training Bottleneck Example:**
```text
Training a 70B model on 8 GPUs:
- Compute time per step: 200ms
- Gradient sync time (1Gbps): 500ms ❌ Bottleneck!
- Gradient sync time (100Gbps): 5ms ✅ No bottleneck

Lesson: Network speed can make training 100x slower
```

### 3. API Access & Production Deployment

**Latency Requirements:**

- **Chat applications:** <200ms total latency
- **Real-time translation:** <100ms total latency
- **Batch processing:** <1s acceptable

**Latency Budget Example:**
```text
Total budget: 200ms for chat response
├── Model inference: 100ms
├── Network (server → user): 30ms
├── Network (user → server): 30ms
├── Preprocessing: 20ms
└── Postprocessing: 20ms

Network optimization saves 60ms (30% of budget!)
```

### 4. Multi-GPU & Multi-Node Setups

**GPU-to-GPU Communication:**

- **NVLink:** 300-600 GB/s (within same node)
- **PCIe 4.0 x16:** 32 GB/s (within same node)
- **100Gb Ethernet:** 12.5 GB/s (between nodes)
- **25Gb Ethernet:** 3.1 GB/s (between nodes)

**Impact on Model Parallelism:**
```text
Pipeline Parallelism across 2 nodes (100GbE):
- Each forward pass: ~50ms compute + ~10ms communication
- With slow network (1GbE): ~50ms compute + ~1000ms communication ❌
- With fast network (100GbE): ~50ms compute + ~10ms communication ✅
```

## Network Architecture Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                        Internet (ISP)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Fiber Modem   │
                    │  (fiber/cable) │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │  Main Router   │
                    │  (10/25/40GbE) │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌────────▼────────┐
│  Compute Node  │  │ Storage Node │  │  Inference Node │
│  (4x GPU)      │  │  (NAS/SAN)   │  │  (2x GPU)       │
└────────────────┘  └──────────────┘  └─────────────────┘
```

## Performance Benchmarks

### Network Speed Impact on LLM Operations

| Operation | 1 Gbps | 10 Gbps | 25 Gbps | 100 Gbps |
|-----------|--------|---------|---------|----------|
| **Model Download (70B)** | 10 min | 1 min | 24 sec | 6 sec |
| **Dataset Load (100GB)** | 15 min | 1.5 min | 36 sec | 9 sec |
| **Checkpoint Save** | 20 min | 2 min | 48 sec | 12 sec |
| **Distributed Training Step** | 1000ms | 100ms | 40ms | 10ms |
| **Inference Response (streaming)** | 500ms | 50ms | 20ms | 5ms |

### Real-World Case Studies

**Case 1: Startup with Limited Budget**
```text
Setup: 4x RTX 4090, 25GbE network
Model: Llama-3.3-70B (4-bit quantized)
Result: 15 tokens/sec per user, supports 50 concurrent users
Cost: $20,000 (hardware) + $500/month (internet)
```

**Case 2: Production System**
```text
Setup: 8x H100, InfiniBand NDR400
Model: Custom 175B model
Result: 200 tokens/sec per user, supports 10,000 concurrent users
Cost: $2,000,000 (hardware) + $50,000/month (dedicated line)
```

## Quick Start Guide

### Step 1: Assess Your Requirements

**For Home Lab / Learning:**
```text
Budget: $500 - $2,000
Network: 1-10 Gbps
Use Case: Learning, small model inference (≤7B)
Recommended: 1 Gbps fiber + consumer router
```

**For Startup / Production:**
```text
Budget: $5,000 - $50,000
Network: 10-25 Gbps
Use Case: Model serving, training medium models (≤34B)
Recommended: 10 Gbps fiber + enterprise switch + dedicated firewall
```

**For Enterprise / Research:**
```text
Budget: $100,000+
Network: 100 Gbps+ with InfiniBand
Use Case: Training large models (70B+), production serving
Recommended: Dedicated fiber line, InfiniBand/RoCE, professional setup
```

### Step 2: Choose Your Network Type

| Network Type | Speed | Cost | Use Case |
|--------------|-------|------|----------|
| **Standard Ethernet** | 1 Gbps | $50-200 | Home lab, learning |
| **Gaming Fiber** | 2-10 Gbps | $100-500 | Small models, inference |
| **Enterprise Fiber** | 10-40 Gbps | $1,000-5,000 | Medium models, training |
| **Data Center Fiber** | 100 Gbps+ | $10,000+ | Large models, production |

### Step 3: Hardware Selection

**For 1-10 Gbps Networks:**
```yaml
Router:
  - Consumer: ASUS AX11000, Netgear RAX120
  - Prosumer: Ubiquiti EdgeRouter, MikroTik
  - Budget: $200-500

Switch:
  - Managed: Netgear GS110TP, TP-Link T1500G
  - Budget: $150-400

Cabling:
  - Cat6: Up to 10 Gbps (55m)
  - Cat6a: Up to 10 Gbps (100m)
  - Budget: $50-100
```

**For 25-100 Gbps Networks:**
```yaml
Router:
  - Enterprise: Cisco ASR, Juniper MX
  - Budget: $2,000-10,000

Switch:
  - Data Center: Arista 7050, Dell N1500
  - Budget: $3,000-15,000

Cabling:
  - Fiber: OM4/OM5, Single Mode
  - DAC: Direct Attach Cables
  - Budget: $500-2,000
```

## Learning Path

1. **[1101: Internet Uplink & Modem Configuration](./1101-Fiber-GPON-Modem.md)** - Internet uplink setup
2. **[1102: Network Topology Design](./1102-Star-Topology-Core.md)** - Network architecture design
3. **[1103: Jumbo Frames and MTU](./1103-Jumbo-Frames-and-MTU.md)** - Performance optimization
4. **[1104: The Protocol Stack - OSI Layers, TCP, and DNS](./1104-Protocol-Stack-TCP-and-DNS.md)** - OSI layers, TCP vs UDP, DNS, ports and TLS handshakes

## Prerequisites

Before starting this module, ensure you understand:

### Basic Knowledge
- **TCP/IP Fundamentals:** Packets, ports, protocols (HTTP, HTTPS, SSH) - covered by [1104](./1104-Protocol-Stack-TCP-and-DNS.md)
- **DNS:** How domain names resolve to IPs - covered by [1104](./1104-Protocol-Stack-TCP-and-DNS.md)
- **IP Addressing:** IPv4 vs IPv6, subnets, CIDR notation
- **Network Hardware:** Difference between routers, switches, modems

### Hardware Requirements
- **Computer:** Linux, macOS, or Windows with administrative access
- **Network Cable:** At least 1 Cat6 Ethernet cable
- **Basic Tools:** Network cable tester (optional but helpful)

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Common Networking Pitfalls

### Pitfall 1: Neglecting Upload Speed

**Pitfall:**
```text
Most ISPs advertise: "1 Gbps download!"
Actual: 1 Gbps down / 50 Mbps up ❌

Impact on LLMs:
- Downloading models: Fast ✅
- Uploading checkpoints: Painfully slow ❌
- Distributed training: Severe bottleneck ❌
```

**Solution:**

- Always check upload speeds
- For training, aim for symmetric connections (1:1 ratio)
- For inference, minimum 100 Mbps upload per 10 concurrent users

### Pitfall 2: WiFi vs Wired

**Pitfall:**
```text
WiFi 6E theoretical: 9.6 Gbps
WiFi 6E actual (5ft away): 2 Gbps
WiFi 6E actual (50ft away): 200 Mbps
Ethernet 1 Gbps actual: 940 Mbps (consistent) ✅

Impact: Inconsistent latency, packet loss, interference
```

**Solution:**

- **Never** use WiFi for training nodes
- **Never** use WiFi for production inference servers
- Use WiFi only for development/testing
- Always use wired connections for GPUs

### Pitfall 3: Wrong MTU Configuration

**Pitfall:**
```text
Default MTU: 1500 bytes
Jumbo frames: 9000 bytes
Benefit: 6x fewer packets, less overhead

If MTU mismatch:
- Path MTU Discovery fails
- Packets get dropped
- Connection hangs or times out
```

**Solution:**

- Test MTU before enabling jumbo frames
- Ensure all network devices support jumbo frames
- See [1103: Jumbo Frames and MTU](./1103-Jumbo-Frames-and-MTU.md)

## Network Optimization Checklist

### Bandwidth Optimization

```text
Step 1: Baseline Testing
  command: iperf3 -c server.example.com -t 60
  target:
    - 1 Gbps: >900 Mbps
    - 10 Gbps: >9 Gbps
    - 25 Gbps: >22 Gbps

Step 2: Enable Jumbo Frames
  mtu: 9000
  test: ping -c 4 -M do -s 8972 target.host
  expected: "no fragmentation"

Step 3: Optimize TCP Settings
  sysctl:
    - net.core.rmem_max = 134217728
    - net.core.wmem_max = 134217728
    - net.ipv4.tcp_rmem = "4096 87380 67108864"
    - net.ipv4.tcp_wmem = "4096 65536 67108864"
```

### Latency Optimization

```text
Step 1: Measure Baseline
  command: ping -c 100 target.host | tail -1
  target: <1ms (local), <50ms (regional)

Step 2: Enable BBR Congestion Control
  command: sysctl -w net.ipv4.tcp_congestion_control=bbr
  benefit: Better throughput, lower latency

Step 3: Disable Unnecessary Services
  services:
    - Disable: mDNS, UPnP, NetBIOS
    - Keep: NTP, SSH, HTTP(S)
```

### Reliability Optimization

```text
Step 1: Enable Link Aggregation
  method: LACP (802.3ad)
  benefit: Redundancy + increased bandwidth
  config: 2x 10Gbps → 20Gbps aggregate

Step 2: Configure Redundant Paths
  topology:
    - Primary: ISP A → Router A → Switch
    - Backup: ISP B → Router B → Switch
  failover: <1 second

Step 3: Network Monitoring
  tools:
    - prometheus-node-exporter: Metrics
    - grafana: Dashboards
    - smokeping: Latency monitoring
```

## Troubleshooting Guide

### Problem 1: Slow Model Downloads

**Symptoms:**
```text
Expected: 1 Gbps download
Actual: 100 Mbps download

Downloading Llama-3.3-70B:
- Expected time: ~6 minutes
- Actual time: ~60 minutes ❌
```

**Diagnosis:**
```bash
# Test direct internet speed
speedtest-cli

# Test local network
iperf3 -c server_ip

# Check for throttling
cat /proc/sys/net/ipv4/tcp_available_congestion_control
```

**Solutions:**

1. **ISP Throttling:** Contact ISP or upgrade plan
2. **Bad Cable:** Replace Ethernet cable
3. **Router Limitation:** Upgrade to 10Gbps router
4. **MTU Issues:** Lower MTU to 1400 for testing

### Problem 2: High Training Latency

**Symptoms:**
```text
Expected training speed: 50 steps/sec
Actual training speed: 5 steps/sec ❌

NVIDIA SMI shows: GPU utilization 20% ❌
Should be: 90%+ ✅
```

**Diagnosis:**
```bash
# Check network during training
nvidia-smi dmon -s u

# Measure inter-GPU communication
nccu -m bandwidthTest

# Check NCCL settings
export NCCL_DEBUG=INFO
export NCCL_IB_TIMEOUT=22
```

**Solutions:**

1. **Upgrade Network:** 1Gbps → 10Gbps minimum
2. **Enable GPUDirect:** Bypass CPU for GPU-GPU transfers
3. **Use NCCL:** Optimized for multi-GPU training
4. **Reduce Batch Size:** Less data to sync

### Problem 3: Inference Timeout Errors

**Symptoms:**
```text
Error: "ReadTimeoutError: HTTPConnectionPool: Read timed out"
Frequency: Random, mostly under load
```

**Diagnosis:**
```bash
# Measure request latency
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/generate"

# Check packet loss
ping -c 1000 server_ip | grep "packet loss"

# Monitor TCP retransmissions
ss -s | grep "retransmits"
```

**Solutions:**

1. **Increase Timeout:** Adjust API client timeouts
2. **Enable Keep-Alive:** Reuse connections
3. **Load Balancing:** Distribute across multiple servers
4. **Upgrade Network:** Add bandwidth

## Performance Monitoring

### Essential Metrics

```yaml
Network Metrics:
  - Bandwidth (Mbps/Gbps): Current throughput
  - Latency (ms): Round-trip time
  - Packet Loss (%): Lost packets
  - Jitter (ms): Latency variation
  - TCP Retransmissions: Network quality

LLM-Specific Metrics:
  - Tokens/sec: Generation speed
  - Request Latency: End-to-end time
  - Queue Depth: Backlog of requests
  - GPU Memory Usage: Model size impact
  - Network-to-Compute Ratio: Bottleneck indicator
```

### Monitoring Setup

```bash
# Install node exporter
sudo apt install prometheus-node-exporter

# Configure Grafana dashboard
# Add panels for:
# 1. Network traffic (rx/tx bytes)
# 2. Network errors (rx/tx errors)
# 3. TCP connections (established, time_wait)
# 4. GPU utilization
# 5. GPU memory usage
# 6: Inference latency
# 7: Tokens per second
```

Alert rules (`prometheus.yml`):
```yaml
groups:
  - name: network_alerts
    rules:
      - alert: HighPacketLoss
        expr: rate(node_network_receive_errs_total[5m]) > 10
        for: 5m
        annotations:
          summary: "High packet loss detected"

      - alert: LowInferenceThroughput
        expr: rate(llm_tokens_generated[5m]) < 10
        for: 10m
        annotations:
          summary: "Inference speed degraded"
```

## Best Practices

### DO

1. **Always use wired connections for GPUs**
   - WiFi is fine for development
   - Never for production or training

2. **Oversize your network**
   - If you need 1 Gbps, install 10 Gbps
   - Future-proof your investment

3. **Monitor everything**
   - Network metrics
   - GPU metrics
   - Application metrics

4. **Test before deploying**
   - Load test with synthetic traffic
   - Test failover scenarios
   - Validate MTU configuration

5. **Document your network**
   - IP address assignments
   - Cable labeling
   - Configuration backups

### DON'T

1. **Don't mix WiFi and wired for training**
   - Inconsistent performance
   - Hard to debug

2. **Don't forget upload speeds**
   - Critical for distributed training
   - Checkpoint uploads

3. **Don't ignore physical layer**
   - Bad cables cause mysterious issues
   - Cable test before deployment

4. **Don't skip redundancy**
   - Single point of failure = downtime
   - Always have backup paths

5. **Don't forget security**
   - Isolate training network from internet
   - Use VPNs for remote access
   - Regular security updates

## Cost Optimization

### Budget-Friendly Alternatives

| Enterprise Solution | Budget Alternative | Cost Savings |
|---------------------|-------------------|--------------|
| Cisco Router ($5,000) | MikroTik ($200) | 96% |
| Arista Switch ($10,000) | Used Dell ($500) | 95% |
| Fiber SFP ($300) | Copper SFP ($30) | 90% |
| Professional Cabling | DIY with tester | 80% |

### When to Invest

**Worth the money:**

- ✅ High-quality Ethernet cables (Cat6a)
- ✅ Managed switches with monitoring
- ✅ Enterprise router for production
- ✅ Fiber for runs >100m

**Not worth it:**

- ❌ "Gaming" network cards
- ❌ Expensive "AI-optimized" switches
- ❌ Gold-plated Ethernet cables
- ❌ Router marketing gimmicks

## Real-World Examples

### Example 1: Home LLM Setup

```yaml
Hardware:
  - GPUs: 2x RTX 4090
  - Network: 1 Gbps fiber
  - Router: ASUS AX11000
  - Switch: Netgear GS105

Results:
  - Model: Llama-3.3-70B (4-bit)
  - Inference: 25 tokens/sec
  - Concurrent users: 5-10
  - Monthly cost: $100

Lessons Learned:
  - 1 Gbps sufficient for 2 GPUs
  - Upload speed limiting checkpoint saves
  - WiFi fine for dev, wired for GPUs
```

### Example 2: Startup Production

```yaml
Hardware:
  - GPUs: 8x A100 40GB
  - Network: 10 Gbps dedicated fiber
  - Router: Ubiquiti EdgeRouter Infinity
  - Switch: Arista 7050 (used)

Results:
  - Model: Fine-tuned Llama-3.3-70B
  - Inference: 200 tokens/sec
  - Concurrent users: 200-500
  - Monthly cost: $2,000

Lessons Learned:
  - 10 Gbps minimum for production
  - Used switches saved $8,000
  - Monitoring essential for debugging
  - Redundant ISP prevented 24h outage
```

### Example 3: Research Cluster

```yaml
Hardware:
  - GPUs: 32x H100 80GB
  - Network: InfiniBand NDR400
  - Router: Juniper MX960
  - Switch: NVIDIA Quantum-2

Results:
  - Model: Custom 175B
  - Training: 3 days (vs 30 days on Ethernet)
  - Monthly cost: $50,000

Lessons Learned:
  - InfiniBand justified for large scale
  - Network = 10x speedup in training
  - Complexity increases significantly
  - Expert network engineer required
```

## Next Steps

After completing this module:

1. **Practice with your setup**
   - Configure jumbo frames
   - Test network performance
   - Set up monitoring

2. **Move to Phase 1.2: Virtualization**
   - Learn to set up VMs for isolation
   - Practice with Proxmox/KVM

3. **Build your first LLM server**
   - Download a model
   - Set up inference
   - Test serving performance

## Assessment

Validate your knowledge:

- **[assessment/QUIZ.md](./assessment/QUIZ.md)** - Test your understanding (20 questions, 80% to pass)
- **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** - Hands-on exercises

## Key Takeaways

After completing this module, you will understand:

- ✅ **Network requirements for different LLM workloads**
    - Small models (1-7B): 1 Gbps sufficient
    - Medium models (13-34B): 10 Gbps recommended
    - Large models (70B+): 25-100 Gbps required

- ✅ **How to set up a high-speed internet uplink**
    - Uplink technology differences (GPON, EPON, DOCSIS)
    - Modem configuration
    - Router setup

- ✅ **Network topology design for AI workloads**
    - Star topology advantages
    - Redundancy planning
    - Hardware selection

- ✅ **MTU and jumbo frames optimization**
    - When to use jumbo frames
    - Configuration steps
    - Troubleshooting MTU issues

- ✅ **Network troubleshooting for LLM infrastructure**
    - Bandwidth bottlenecks
    - Latency issues
    - Packet loss diagnosis

- ✅ **Performance monitoring and optimization**
    - Key metrics to track
    - Tools for monitoring
    - Alert configuration

- ✅ **Cost optimization strategies**
    - Budget-friendly alternatives
    - When to invest
    - ROI considerations

## Additional Resources

### Tools & Utilities

```bash
# Network Testing
iperf3          # Bandwidth testing
ping            # Latency testing
mtr             # Combined traceroute/ping
speedtest-cli   # Internet speed test
wireshark       # Packet analysis

# Configuration
ethtool         # Ethernet settings
ip              # Network configuration
ss              # Socket statistics
netstat         # Network statistics

# Monitoring
prometheus      # Metrics collection
grafana         # Dashboards
node_exporter   # System metrics
```

### Further Reading

**Books:**

- "Network Warrior" by Gary A. Donahue
- "Computer Networking: A Top-Down Approach" by Kurose & Ross

**Online Courses:**

- [Networking Fundamentals - NetworkChuck](https://www.youtube.com/@NetworkChuck)
- [Practical Networking](https://www.youtube.com/watch?v=1jM4v5iSOD4)

**Community:**

- [/r/homelab](https://www.reddit.com/r/homelab/) - Home lab enthusiasts
- [/r/networking](https://www.reddit.com/r/networking/) - Networking professionals
- [Network Engineering Stack Exchange](https://networkengineering.stackexchange.com/)

## Module Completion Checklist

```text
Understanding:
  - [ ] I can explain bandwidth vs latency
  - [ ] I know when to use jumbo frames
  - [ ] I understand network topology design
  - [ ] I can calculate bandwidth requirements for my models

Practical Skills:
  - [ ] I can test network performance
  - [ ] I can configure MTU settings
  - [ ] I can troubleshoot network issues
  - [ ] I can set up monitoring

Hardware:
  - [ ] I have assessed my requirements
  - [ ] I have selected appropriate hardware
  - [ ] I understand budget vs performance trade-offs

Production Ready:
  - [ ] I have designed redundant paths
  - [ ] I have configured alerts
  - [ ] I have documented my network setup
  - [ ] I have tested failover scenarios
```

## Glossary

| Term | Definition |
|------|------------|
| **Bandwidth** | Maximum data transfer rate (Mbps/Gbps) |
| **Latency** | Time for data to travel from source to destination (ms) |
| **MTU** | Maximum Transmission Unit - largest packet size (bytes) |
| **Jumbo Frames** | Ethernet frames larger than standard 1500 bytes |
| **GPON** | Gigabit Passive Optical Network - fiber standard |
| **InfiniBand** | High-speed, low-latency networking for data centers |
| **RoCE** | RDMA over Converged Ethernet |
| **LACP** | Link Aggregation Control Protocol - bond multiple links |
| **ISP** | Internet Service Provider |
| **SFP** | Small Form-factor Pluggable - transceiver module |

---

**Module Duration:** 8-10 hours

**Difficulty:** ⭐ Beginner

**Ready to proceed?** Continue to [1101: Internet Uplink & Modem Configuration](./1101-Fiber-GPON-Modem.md)
