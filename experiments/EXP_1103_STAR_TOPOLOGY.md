# EXP_1103: Star Topology and Network Performance Experiments

## Overview
Practical experiments for configuring and optimizing star topology network infrastructure for 2.5Gbps LLM model serving.

## Experiment 1: Star Topology Setup

### Objective
Configure a star topology network with central switch for optimal throughput and minimal latency.

### Implementation

```python
# network_topology.py
import subprocess
import json
from typing import Dict, List

class StarTopologyConfig:
    """Configure star topology network"""

    def __init__(self, switch_ip: str = "192.168.1.1"):
        self.switch_ip = switch_ip
        self.devices = {}

    def discover_network(self):
        """Discover all devices on network"""
        print("Discovering network devices...")

        # Scan network for devices
        result = subprocess.run(
            ["nmap", "-sn", "192.168.1.0/24"],
            capture_output=True,
            text=True
        )

        # Parse results
        lines = result.stdout.split('\n')
        for line in lines:
            if "Nmap scan report for" in line:
                ip = line.split()[-1]
                self.devices[ip] = {"status": "up"}

        print(f"Found {len(self.devices)} devices")
        return self.devices

    def measure_latency(self, target: str, count: int = 10):
        """Measure latency to target device"""
        print(f"Measuring latency to {target}...")

        result = subprocess.run(
            ["ping", "-c", str(count), target],
            capture_output=True,
            text=True
        )

        # Parse ping results
        lines = result.stdout.split('\n')
        for line in lines:
            if "min/avg/max" in line:
                stats = line.split('=')[-1].strip()
                return stats

        return None

    def test_bandwidth(self, target: str, duration: int = 10):
        """Test bandwidth to target device"""
        print(f"Testing bandwidth to {target}...")

        # Use iperf3 for bandwidth testing
        result = subprocess.run(
            ["iperf3", "-c", target, "-t", str(duration)],
            capture_output=True,
            text=True
        )

        # Parse results
        lines = result.stdout.split('\n')
        for line in lines:
            if "sender" in line and "Mbits/sec" in line:
                parts = line.split()
                bandwidth = parts[6]
                return bandwidth

        return None

    def analyze_bottlenecks(self):
        """Identify network bottlenecks"""
        print("\nNetwork Bottleneck Analysis")
        print("=" * 60)

        results = {}

        for device in self.devices:
            latency = self.measure_latency(device)
            results[device] = {"latency": latency}

        # Find devices with high latency
        for device, stats in results.items():
            if stats["latency"]:
                parts = stats["latency"].split('/')
                avg_latency = float(parts[1])
                if avg_latency > 5.0:  # 5ms threshold
                    print(f"⚠️  {device}: High latency ({stats['latency']})")
                else:
                    print(f"✅ {device}: Normal latency ({stats['latency']})")

        return results


def test_star_topology():
    """Test star topology configuration"""

    print("Star Topology Network Test")
    print("=" * 60)

    config = StarTopologyConfig()

    # Discover devices
    devices = config.discover_network()

    # Measure latencies
    print("\nLatency Measurements:")
    for device in devices:
        latency = config.measure_latency(device)
        print(f"{device}: {latency}")

    # Analyze bottlenecks
    config.analyze_bottlenecks()


if __name__ == "__main__":
    test_star_topology()
```

---

## Experiment 2: Jumbo Frames Configuration

### Objective
Configure jumbo frames (MTU 9000) for improved throughput in LLM model serving.

### Implementation

```python
# jumbo_frames.py
import subprocess
import re

class JumboFramesConfig:
    """Configure jumbo frames for network interfaces"""

    def __init__(self, interface: str = "eth0"):
        self.interface = interface
        self.target_mtu = 9000

    def check_current_mtu(self):
        """Check current MTU setting"""
        result = subprocess.run(
            ["ip", "link", "show", self.interface],
            capture_output=True,
            text=True
        )

        # Parse MTU from output
        match = re.search(r'mtu (\d+)', result.stdout)
        if match:
            current_mtu = int(match.group(1))
            print(f"Current MTU: {current_mtu}")
            return current_mtu

        return None

    def set_mtu(self, mtu: int = 9000):
        """Set MTU for interface"""
        print(f"Setting MTU to {mtu}...")

        try:
            subprocess.run(
                ["sudo", "ip", "link", "set", self.interface, "mtu", str(mtu)],
                check=True,
                capture_output=True
            )
            print(f"✅ MTU set to {mtu}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to set MTU: {e}")
            return False

    def verify_mtu(self):
        """Verify MTU setting"""
        current = self.check_current_mtu()
        if current == self.target_mtu:
            print(f"✅ MTU verified: {current}")
            return True
        else:
            print(f"❌ MTU mismatch: expected {self.target_mtu}, got {current}")
            return False

    def test_throughput(self, host: str, mtu: int = 9000):
        """Test throughput with specific MTU"""
        print(f"\nTesting throughput with MTU {mtu}...")

        # Use iperf3 to test
        result = subprocess.run(
            ["iperf3", "-c", host, "-t", "10", "-M", str(mtu)],
            capture_output=True,
            text=True
        )

        # Parse bandwidth
        for line in result.stdout.split('\n'):
            if "Mbits/sec" in line and "sender" in line:
                bandwidth = line.split()[6]
                print(f"Bandwidth: {bandwidth} Mbits/sec")
                return float(bandwidth)

        return None

    def compare_mtu_performance(self, host: str):
        """Compare performance with different MTU sizes"""
        print("\nMTU Performance Comparison")
        print("=" * 60)

        mtus = [1500, 4000, 9000]
        results = {}

        for mtu in mtus:
            print(f"\nTesting MTU {mtu}...")

            # Set MTU
            self.set_mtu(mtu)

            # Test throughput
            bandwidth = self.test_throughput(host, mtu)
            results[mtu] = bandwidth

        # Display comparison
        print("\nResults:")
        for mtu, bw in results.items():
            if bw:
                improvement = (bw / results[1500] - 1) * 100
                print(f"MTU {mtu}: {bw:.2f} Mbits/sec ({improvement:+.1f}%)")

        return results


def test_jumbo_frames():
    """Test jumbo frames configuration"""

    print("Jumbo Frames Configuration Test")
    print("=" * 60)

    config = JumboFramesConfig()

    # Check current MTU
    current = config.check_current_mtu()

    # Set to 9000
    if config.set_mtu(9000):
        config.verify_mtu()


if __name__ == "__main__":
    test_jumbo_frames()
```

---

## Experiment 3: Network Latency Optimization

### Objective
Minimize network latency for real-time LLM inference.

### Implementation

```python
# latency_optimization.py
import subprocess
import time
import statistics

class LatencyOptimizer:
    """Optimize network latency for LLM serving"""

    def __init__(self, target_host: str):
        self.target_host = target_host
        self.measurements = []

    def continuous_ping(self, count: int = 100):
        """Continuous ping measurement"""
        print(f"Pinging {self.target_host} {count} times...")

        result = subprocess.run(
            ["ping", "-c", str(count), self.target_host],
            capture_output=True,
            text=True
        )

        # Parse ping times
        times = []
        for line in result.stdout.split('\n'):
            if 'time=' in line:
                time_str = line.split('time=')[-1].split(' ')[0]
                times.append(float(time_str))

        return times

    def analyze_latency(self, times: list):
        """Analyze latency measurements"""
        if not times:
            return None

        stats = {
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0
        }

        print("\nLatency Statistics:")
        print(f"  Min: {stats['min']:.2f} ms")
        print(f"  Max: {stats['max']:.2f} ms")
        print(f"  Avg: {stats['avg']:.2f} ms")
        print(f"  Median: {stats['median']:.2f} ms")
        print(f"  Std Dev: {stats['stdev']:.2f} ms")

        return stats

    def measure_jitter(self, count: int = 100):
        """Measure network jitter (variation in latency)"""
        print(f"Measuring jitter to {self.target_host}...")

        times = self.continuous_ping(count)

        # Calculate jitter
        if len(times) > 1:
            jitter = []
            for i in range(1, len(times)):
                jitter.append(abs(times[i] - times[i-1]))

            avg_jitter = statistics.mean(jitter)
            max_jitter = max(jitter)

            print(f"\nJitter Statistics:")
            print(f"  Average: {avg_jitter:.2f} ms")
            print(f"  Maximum: {max_jitter:.2f} ms")

            return {"avg": avg_jitter, "max": max_jitter}

        return None

    def test_packet_loss(self, count: int = 1000):
        """Test for packet loss"""
        print(f"Testing packet loss ({count} packets)...")

        result = subprocess.run(
            ["ping", "-c", str(count), self.target_host],
            capture_output=True,
            text=True
        )

        # Parse packet loss
        for line in result.stdout.split('\n'):
            if 'packet loss' in line:
                loss_str = line.split(',')[2].strip().split('%')[0]
                loss_pct = float(loss_str)
                print(f"Packet Loss: {loss_pct}%")
                return loss_pct

        return None

    def optimize_network_settings(self):
        """Apply network optimizations"""
        print("\nApplying network optimizations...")

        optimizations = []

        # Disable TCP slow start
        try:
            subprocess.run(
                ["sudo", "sysctl", "-w", "net.ipv4.tcp_slow_start_after_idle=0"],
                check=True
            )
            optimizations.append("Disabled TCP slow start after idle")
        except:
            pass

        # Increase TCP buffers
        try:
            subprocess.run(
                ["sudo", "sysctl", "-w", "net.core.rmem_max=134217728"],
                check=True
            )
            subprocess.run(
                ["sudo", "sysctl", "-w", "net.core.wmem_max=134217728"],
                check=True
            )
            optimizations.append("Increased TCP buffers")
        except:
            pass

        # Enable BBR congestion control
        try:
            subprocess.run(
                ["sudo", "sysctl", "-w", "net.ipv4.tcp_congestion_control=bbr"],
                check=True
            )
            optimizations.append("Enabled BBR congestion control")
        except:
            pass

        for opt in optimizations:
            print(f"  ✅ {opt}")

        return optimizations


def test_latency_optimization():
    """Test latency optimizations"""

    print("Network Latency Optimization Test")
    print("=" * 60)

    optimizer = LatencyOptimizer("192.168.1.1")

    # Baseline measurements
    print("\n--- Baseline Measurements ---")
    times = optimizer.continuous_ping(100)
    optimizer.analyze_latency(times)
    optimizer.measure_jitter(100)
    optimizer.test_packet_loss(1000)

    # Apply optimizations
    optimizer.optimize_network_settings()

    # Post-optimization measurements
    print("\n--- Post-Optimization Measurements ---")
    times = optimizer.continuous_ping(100)
    optimizer.analyze_latency(times)
    optimizer.measure_jitter(100)
    optimizer.test_packet_loss(1000)


if __name__ == "__main__":
    test_latency_optimization()
```

---

## Experiment 4: 2.5Gbps Throughput Validation

### Objective
Validate 2.5Gbps throughput for large model transfers.

### Implementation

```python
# throughput_test.py
import subprocess
import time

class ThroughputTest:
    """Test network throughput for LLM model serving"""

    def __init__(self, server_ip: str):
        self.server_ip = server_ip
        self.test_duration = 30

    def test_tcp_throughput(self):
        """Test TCP throughput with iperf3"""
        print(f"Testing TCP throughput to {self.server_ip}...")

        result = subprocess.run(
            ["iperf3", "-c", self.server_ip, "-t", str(self.test_duration), "-i", "1"],
            capture_output=True,
            text=True
        )

        # Parse results
        print("\nThroughput Results:")
        for line in result.stdout.split('\n'):
            if 'Mbits/sec' in line and 'sender' in line:
                parts = line.split()
                interval = parts[2]
                bandwidth = parts[6]
                transfer = parts[4]
                print(f"  Interval {interval}: {bandwidth} Mbits/sec ({transfer})")

        return result

    def test_udp_throughput(self):
        """Test UDP throughput"""
        print(f"Testing UDP throughput to {self.server_ip}...")

        result = subprocess.run(
            ["iperf3", "-c", self.server_ip, "-u", "-b", "2.5G", "-t", str(self.test_duration)],
            capture_output=True,
            text=True
        )

        print("\nUDP Results:")
        for line in result.stdout.split('\n'):
            if 'Mbits/sec' in line:
                print(f"  {line.strip()}")

        return result

    def test_model_transfer(self, model_size_gb: int = 7):
        """Simulate model file transfer"""
        print(f"\nTesting {model_size_gb}GB model transfer...")

        start_time = time.time()

        # Use dd to generate and transfer test file
        subprocess.run(
            ["dd", "if=/dev/zero", "bs=1M", "count=f{model_size_gb * 1024}",
             "|", "nc", self.server_ip, "5001"],
            shell=True
        )

        duration = time.time() - start_time
        throughput_gbps = (model_size_gb * 8) / duration

        print(f"Transfer time: {duration:.2f} seconds")
        print(f"Throughput: {throughput_gbps:.2f} Gbps")

        return {"duration": duration, "throughput": throughput_gbps}

    def test_concurrent_streams(self, streams: int = 4):
        """Test concurrent connection streams"""
        print(f"\nTesting {streams} concurrent streams...")

        # Run multiple iperf3 instances
        processes = []
        for i in range(streams):
            p = subprocess.Popen(
                ["iperf3", "-c", self.server_ip, "-t", "30", "-P", "1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            processes.append(p)

        # Wait for completion
        for p in processes:
            p.wait()

        print(f"Completed {streams} concurrent streams")


def test_throughput():
    """Test network throughput"""

    print("2.5Gbps Network Throughput Test")
    print("=" * 60)

    test = ThroughputTest("192.168.1.1")

    # Test TCP throughput
    test.test_tcp_throughput()

    # Test UDP throughput
    test.test_udp_throughput()

    # Test model transfer
    test.test_model_transfer(7)

    # Test concurrent streams
    test.test_concurrent_streams(4)


if __name__ == "__main__":
    test_throughput()
```

---

## Quick Start

### Test Star Topology

```bash
# Discover network devices
python network_topology.py

# Test latency to all devices
python latency_optimization.py
```

### Configure Jumbo Frames

```bash
# Set MTU to 9000
sudo ip link set eth0 mtu 9000

# Verify setting
ip link show eth0

# Test throughput with jumbo frames
python jumbo_frames.py
```

### Run Throughput Tests

```bash
# Start iperf3 server on receiving end
iperf3 -s

# Run throughput test from client
python throughput_test.py
```

---

## Expected Results

### Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| **Throughput** | 2.5 Gbps | 2.0+ Gbps |
| **Latency** | <1ms | <2ms |
| **Jitter** | <0.5ms | <1ms |
| **Packet Loss** | 0% | <0.1% |

### Jumbo Frames Benefit

| MTU Size | Throughput | Improvement |
|----------|-----------|-------------|
| 1500 (default) | 1.8 Gbps | baseline |
| 4000 | 2.1 Gbps | +16% |
| 9000 | 2.35 Gbps | +30% |

---

## Experiment Checklist

- [ ] Star topology configuration
- [ ] Device discovery and mapping
- [ ] Latency measurement to all devices
- [ ] Jumbo frames configuration
- [ ] MTU size comparison
- [ ] Network optimization application
- [ ] Throughput validation
- [ ] Concurrent stream testing
- [ ] Model transfer simulation
- [ ] Baseline performance documentation

---

## Related Documentation

- [1102: Star Topology Core](../docs/phases/phase1-infra/1100-network/1102-Star-Topology-Core.md)
- [1103: Jumbo Frames and MTU](../docs/phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md)
- [1402: vLLM and TGI](../docs/phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
