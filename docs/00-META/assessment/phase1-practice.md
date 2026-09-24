# Phase 1: Infrastructure Practice

## Hands-On Exercises

### Exercise 1: Configure Star Topology Network

**Objective:** Set up a star topology network with a central managed switch.

```bash
#!/bin/bash
# network_setup.sh - Star Topology Configuration

# Variables
SWITCH_IP="192.168.1.1"
NETMASK="255.255.255.0"
NETWORK="192.168.1.0/24"

echo "=== Star Topology Network Setup ==="
echo "Switch IP: $SWITCH_IP"
echo "Network: $NETWORK"

# 1. Configure network interface
echo "Step 1: Configuring network interface..."
ip addr show eth0

# Set IP address
sudo ip addr add 192.168.1.100/24 dev eth0
sudo ip link set eth0 up

# Verify
ip addr show eth0

# 2. Configure jumbo frames (MTU 9000)
echo "Step 2: Configuring jumbo frames..."
sudo ip link set eth0 mtu 9000

# Verify MTU
ip link show eth0 | grep mtu

# 3. Test connectivity to switch
echo "Step 3: Testing connectivity..."
ping -c 5 $SWITCH_IP

# 4. Measure latency
echo "Step 4: Measuring latency..."
ping -c 100 $SWITCH_IP | tail -1

# 5. Test throughput with iperf3
echo "Step 5: Testing throughput..."
iperf3 -c $SWITCH_IP -t 30

# Expected output: near line rate (>900 Mbps on gigabit, higher on multi-gig)
echo "=== Network Setup Complete ==="
```

**Expected Results:**
- MTU set to 9000
- Latency <1ms
- Throughput near line rate

**Troubleshooting:**
- If MTU change fails: Check if driver supports jumbo frames
- If throughput is low: Check cable category (Cat6+ required)
- If latency is high: Check for network congestion

---

### Exercise 2: GPU Passthrough Configuration

**Objective:** Configure GPU passthrough on Proxmox for VM access.

```bash
#!/bin/bash
# gpu_passthrough.sh - GPU Passthrough Setup

echo "=== GPU Passthrough Configuration ==="

# 1. Enable IOMMU in GRUB
echo "Step 1: Enabling IOMMU..."
sudo nano /etc/default/grub
# Add to GRUB_CMDLINE_LINUX_DEFAULT: "intel_iommu=on iommu=pt"

# Update GRUB
sudo update-grub

# 2. Check IOMMU groups
echo "Step 2: Checking IOMMU groups..."
find /sys/kernel/iommu_groups/ -type l -name "devices:*" -exec sh -c 'echo "Group: $(basename $(dirname {}))"; ls -l {}; echo' \;

# Look for GPU in isolated group
# Expected: GPU in its own IOMMU group

# 3. Load VFIO modules
echo "Step 3: Loading VFIO modules..."
echo "vfio" | sudo tee /etc/modules-load.d/vfio.conf
echo "vfio_pci" | sudo tee -a /etc/modules-load.d/vfio.conf
echo "vfio_iommu_type1" | sudo tee -a /etc/modules-load.d/vfio.conf

# 4. Configure VFIO for GPU
echo "Step 4: Configuring VFIO..."
sudo lspci -nnk -d ::1a

# Find GPU ID (e.g., 10de:1e82 for an 11GB-class GPU)
echo "Add GPU ID to /etc/modprobe.d/vfio.conf:"
echo "options vfio-pci ids=10de:1e82"

# 5. Blacklist NVIDIA driver
echo "Step 5: Blacklisting nouveau..."
echo "blacklist nouveau" | sudo tee /etc/modprobe.d/blacklist-nouveau.conf
echo "options nouveau modeset=0" | sudo tee -a /etc/modprobe.d/blacklist-nouveau.conf
sudo update-initramfs -u

# 6. Reboot
echo "Step 6: Reboot to apply changes..."
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi

echo "=== GPU Passthrough Configuration Complete ==="
echo "After reboot, verify with: dmesg | grep -e DMAR -e IOMMU"
```

**Expected Results:**
- IOMMU enabled in dmesg
- GPU in isolated IOMMU group
- VFIO modules loaded
- VM can see GPU directly

**Verification:**
```bash
# After reboot, verify IOMMU
dmesg | grep -e DMAR -e IOMMU

# Verify VFIO
lsmod | grep vfio

# Check GPU visibility in VM
qm config 100  # Replace with your VM ID
```

---

### Exercise 3: K3s Cluster Setup

**Objective:** Deploy multi-node K3s cluster.

```bash
#!/bin/bash
# k3s_cluster.sh - K3s Cluster Setup

echo "=== K3s Multi-Node Cluster Setup ==="

# Server 1 (Master)
echo "Step 1: Installing K3s on master node..."
curl -sfL https://get.k3s.io | sh -

# Get cluster token
TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)
MASTER_IP=$(hostname -I | awk '{print $1}')

echo "Master IP: $MASTER_IP"
echo "Cluster Token: $TOKEN"

# Server 2 (Worker)
echo "Step 2: Joining worker node..."
curl -sfL https://get.k3s.io | K3S_URL=https://$MASTER_IP:6443 K3S_TOKEN=$TOKEN sh -

# Verify cluster
echo "Step 3: Verifying cluster..."
sudo k3s kubectl get nodes

# Get cluster info
sudo k3s kubectl cluster-info

# Check pods
sudo k3s kubectl get pods -A

echo "=== K3s Cluster Setup Complete ==="
```

**Expected Results:**
- 2 nodes in cluster (1 master, 1 worker)
- All nodes Ready
- Core pods running

**Troubleshooting:**
- If nodes can't join: Check firewall (ports 6443, 10250)
- If pods not starting: Check resource availability
- If token invalid: Regenerate on master node

---

### Exercise 4: vLLM Server Deployment

**Objective:** Deploy vLLM server with quantized model.

```python
# vllm_deploy.py - vLLM Server Deployment

import subprocess
import requests
import time

def deploy_vllm():
    """Deploy vLLM server with AWQ quantization"""

    print("=== vLLM Server Deployment ===")

    # Pull latest image
    print("Step 1: Pulling vLLM image...")
    subprocess.run([
        "docker", "pull",
        "vllm/vllm-openai:latest"
    ])

    # Start vLLM server
    print("Step 2: Starting vLLM server...")
    cmd = [
        "docker", "run", "-d", "--name", "vllm-server",
        "--gpus", "all",
        "-p", "8000:8000",
        "-v", "/srv/models/vllm:/models",
        "vllm/vllm-openai:latest",
        "--model", "mistralai/Mistral-7B-Instruct-v0.2",
        "--quantization", "awq",
        "--max-model-len", "4096",
        "--gpu-memory-utilization", "0.9",
        "--block-size", "16"
    ]

    subprocess.run(cmd, check=True)

    # Wait for startup
    print("Step 3: Waiting for server startup...")
    time.sleep(30)

    # Health check
    print("Step 4: Health check...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server healthy!")
        else:
            print("❌ Server not responding")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test inference
    print("Step 5: Testing inference...")
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "messages": [{"role": "user", "content": "Hello!"}],
                "max_tokens": 50
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Inference successful!")
            print(f"Response: {result['choices'][0]['message']['content']}")
        else:
            print(f"❌ Inference failed: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("=== vLLM Deployment Complete ===")

if __name__ == "__main__":
    deploy_vllm()
```

**Expected Results:**
- vLLM container running
- Health check passes
- Inference returns response
- Memory <11GB

**Monitoring:**
```bash
# Check container status
docker ps | grep vllm

# View logs
docker logs -f vllm-server

# Check GPU usage
nvidia-smi

# Test load
for i in {1..10}; do
  curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"mistralai/Mistral-7B-Instruct-v0.2","messages":[{"role":"user","content":"Test"}]}'
done
```

---

### Exercise 5: Prometheus Monitoring Setup

**Objective:** Set up Prometheus for LLM infrastructure monitoring.

```yaml
# prometheus_config.yml - Prometheus Configuration

global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Rule files
rule_files:
  - "alerts.yml"

# Scrape configurations
scrape_configs:
  # vLLM metrics
  - job_name: 'vllm'
    static_configs:
      - targets: ['vllm-server:8000']
    metrics_path: '/metrics'

  # Qdrant metrics
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    metrics_path: '/metrics'

  # Node exporter
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # GPU metrics
  - job_name: 'gpu'
    static_configs:
      - targets: ['gpu-exporter:9400']

  # Docker stats
  - job_name: 'docker'
    static_configs:
      - targets: ['cadvisor:8080']
```

```bash
# monitoring_stack.sh - Deploy Monitoring Stack

#!/bin/bash

echo "=== Deploying Monitoring Stack ==="

# Create network
docker network create monitoring

# Deploy Prometheus
docker run -d \
  --name prometheus \
  --network monitoring \
  -p 9090:9090 \
  -v /srv/docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v /srv/docker/prometheus/alerts.yml:/etc/prometheus/alerts.yml \
  prom/prometheus:latest

# Deploy Grafana
docker run -d \
  --name grafana \
  --network monitoring \
  -p 3000:3000 \
  -v /srv/docker/grafana:/var/lib/grafana \
  grafana/grafana:latest

# Deploy Loki
docker run -d \
  --name loki \
  --network monitoring \
  -p 3100:3100 \
  -v /srv/docker/loki:/loki \
  grafana/loki:latest

# Deploy Tempo
docker run -d \
  --name tempo \
  --network monitoring \
  -p 3200:3200 \
  -v /srv/docker/tempo:/etc/tempo \
  grafana/tempo:latest

# Deploy Node Exporter
docker run -d \
  --name node-exporter \
  --network monitoring \
  -p 9100:9100 \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  --network host \
  prom/node-exporter:latest

# Deploy cAdvisor
docker run -d \
  --name cadvisor \
  --network monitoring \
  -p 8080:8080 \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:ro \
  -v /sys:/sys:ro \
  -v /var/lib/docker/:/var/lib/docker:ro \
  gcr.io/cadvisor/cadvisor:latest

echo "=== Monitoring Stack Deployed ==="
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000 (admin/admin)"
echo "Loki: http://localhost:3100"
echo "Tempo: http://localhost:3200"
```

**Verification:**
```bash
# Check all containers
docker ps | grep -E 'prometheus|grafana|loki|tempo|cadvisor'

# Check metrics endpoint
curl http://localhost:9090/-/healthy
curl http://localhost:9090/api/v1/targets

# Access Grafana
firefox http://localhost:3000
# Login: admin/admin
# Add Prometheus datasource: http://prometheus:9090
```

---

## Bonus: Infrastructure Validation

```bash
#!/bin/bash
# validate_infrastructure.sh - Complete Infrastructure Validation

echo "=== PROJECT-OMEGA Infrastructure Validation ==="

# Track results
PASSED=0
FAILED=0

# Test functions
test_network() {
    echo -n "Testing lab network... "
    PING_RESULT=$(ping -c 5 192.168.1.1 | tail -1 | awk '{print $4}')
    if [[ "$PING_RESULT" < "2.0" ]]; then
        echo "✅ PASS (latency: $PING_RESULT ms)"
        ((PASSED++))
    else
        echo "❌ FAIL (latency: $PING_RESULT ms)"
        ((FAILED++))
    fi
}

test_jumbo_frames() {
    echo -n "Testing jumbo frames... "
    MTU=$(ip link show eth0 | grep mtu | awk '{print $2}')
    if [ "$MTU" = "9000" ]; then
        echo "✅ PASS (MTU: $MTU)"
        ((PASSED++))
    else
        echo "❌ FAIL (MTU: $MTU, expected 9000)"
        ((FAILED++))
    fi
}

test_gpu_passthrough() {
    echo -n "Testing GPU passthrough... "
    if dmesg | grep -q "VFIO"; then
        echo "✅ PASS (VFIO enabled)"
        ((PASSED++))
    else
        echo "❌ FAIL (VFIO not enabled)"
        ((FAILED++))
    fi
}

test_k3s_cluster() {
    echo -n "Testing K3s cluster... "
    NODES=$(sudo k3s kubectl get nodes --no-headers 2>/dev/null | wc -l)
    if [ "$NODES" -ge "2" ]; then
        echo "✅ PASS ($NODES nodes ready)"
        ((PASSED++))
    else
        echo "❌ FAIL (only $NODES nodes)"
        ((FAILED++))
    fi
}

test_vllm_server() {
    echo -n "Testing vLLM server... "
    RESPONSE=$(curl -s http://localhost:8000/health)
    if [ -n "$RESPONSE" ]; then
        echo "✅ PASS (server responding)"
        ((PASSED++))
    else
        echo "❌ FAIL (server not responding)"
        ((FAILED++))
    fi
}

test_prometheus() {
    echo -n "Testing Prometheus... "
    RESPONSE=$(curl -s http://localhost:9090/-/healthy)
    if [ -n "$RESPONSE" ]; then
        echo "✅ PASS (Prometheus healthy)"
        ((PASSED++))
    else
        echo "❌ FAIL (Prometheus not healthy)"
        ((FAILED++))
    fi
}

test_grafana() {
    echo -n "Testing Grafana... "
    RESPONSE=$(curl -s http://localhost:3000/api/health)
    if [ -n "$RESPONSE" ]; then
        echo "✅ PASS (Grafana accessible)"
        ((PASSED++))
    else
        echo "❌ FAIL (Grafana not accessible)"
        ((FAILED++))
    fi
}

test_qdrant() {
    echo -n "Testing Qdrant... "
    RESPONSE=$(curl -s http://localhost:6333/collections)
    if [ -n "$RESPONSE" ]; then
        echo "✅ PASS (Qdrant accessible)"
        ((PASSED++))
    else
        echo "❌ FAIL (Qdrant not accessible)"
        ((FAILED++))
    fi
}

# Run all tests
test_network
test_jumbo_frames
test_gpu_passthrough
test_k3s_cluster
test_vllm_server
test_prometheus
test_grafana
test_qdrant

# Summary
echo ""
echo "=== Validation Summary ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed. Review logs above."
    exit 1
fi
```

---

## Completion Checklist

- [ ] Star topology configured with a managed switch
- [ ] Jumbo frames (MTU 9000) enabled
- [ ] GPU passthrough working on VM
- [ ] K3s cluster with 2+ nodes
- [ ] vLLM serving quantized model
- [ ] Prometheus monitoring deployed
- [ ] Grafana dashboards created
- [ ] Log aggregation (Loki) configured
- [ ] All services healthy
- [ ] Infrastructure validated

---

**Last Updated:** 2026-02-05
