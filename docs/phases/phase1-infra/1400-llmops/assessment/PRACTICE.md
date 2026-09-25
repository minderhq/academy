---
Document ID: 1400-PRACTICE
Title: "1400: LLMOps - Practice"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
---

# 1400: LLMOps - Practice

## Exercises

### Exercise 1: Ollama Setup

**Objective:** Install Ollama, pull a model, and run inference locally.

**Solution:**

```bash
#!/bin/bash
# setup_ollama.sh - Complete Ollama installation and setup

# 1. Install Ollama
echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
echo "Verifying Ollama installation..."
ollama --version

# Expected output: ollama version is 0.1.x or higher

# 2. Pull model (Llama 2 7B)
echo "Pulling Llama 2 7B model..."
ollama pull llama2:7b

# Expected output: Shows download progress for model files

# 3. List available models
echo "Available models:"
ollama list

# Expected output: Shows llama2:7b in the list

# 4. Run simple inference
echo "Running inference test..."
ollama run llama2:7b "The future of AI is"

# Expected output: Completes the sentence with generated text

# 5. Interactive mode
echo "Starting interactive mode (press Ctrl-D to exit)..."
ollama run llama2:7b

# 6. Test with different parameters
echo "Testing with custom parameters..."
ollama run llama2:7b "Explain quantum computing" --temperature 0.5 --num_predict 100

# Troubleshooting Tips:
# - If curl fails: Check internet connection and firewall settings
# - If model pull fails: Verify disk space (requires ~4GB for llama2:7b)
# - If inference is slow: Check CPU/GPU resources with 'htop' or 'nvidia-smi'

# Expected outputs:
# Installation: Success message with version
# Model pull: Progress bar showing download
# Inference: Generated text completing the prompt
```

```python
# ollama_client.py - Python client for Ollama
import requests
import json

class OllamaClient:
    """Complete Python client for Ollama API."""

    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def generate(self, model, prompt, **kwargs):
        """Generate text using Ollama."""
        url = f"{self.base_url}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }

        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def chat(self, model, messages, **kwargs):
        """Chat completion using Ollama."""
        url = f"{self.base_url}/api/chat"
        data = {
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs
        }

        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def list_models(self):
        """List available models."""
        url = f"{self.base_url}/api/tags"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Usage examples
if __name__ == "__main__":
    client = OllamaClient()

    # List models
    models = client.list_models()
    print("Available models:", json.dumps(models, indent=2))

    # Generate text
    result = client.generate(
        model="llama2:7b",
        prompt="The future of AI is",
        temperature=0.7,
        num_predict=150
    )
    print("\nGenerated text:")
    print(result.get("response", ""))

    # Chat completion
    chat_result = client.chat(
        model="llama2:7b",
        messages=[
            {"role": "user", "content": "What is machine learning?"}
        ]
    )
    print("\nChat response:")
    print(chat_result.get("message", {}).get("content", ""))
```

### Exercise 2: vLLM Serving

**Objective:** Start a vLLM server and test it with OpenAI-compatible API.

**Solution:**

```bash
#!/bin/bash
# start_vllm.sh - Complete vLLM server startup script

# 1. Install vLLM
echo "Installing vLLM..."
pip install vllm>=0.6.0

# 2. Start vLLM server with optimized settings
echo "Starting vLLM server..."
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-hf \
    --tensor-parallel-size 1 \
    --dtype half \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 4096 \
    --block-size 16 \
    --disable-log-requests

# Expected output:
# INFO: Started server process
# INFO: Uvicorn running on http://0.0.0.0:8000

# Troubleshooting Tips:
# - If OOM error: Reduce --gpu-memory-utilization to 0.8 or lower
# - If model not found: Ensure HUGGING_FACE_TOKEN is set for private models
# - If port in use: Change --port to available port
# - If slow inference: Check GPU utilization with 'nvidia-smi'
```

```bash
#!/bin/bash
# test_vllm.sh - Complete vLLM testing script

# Wait for server to be ready
echo "Waiting for vLLM server..."
until curl -s http://localhost:8000/health > /dev/null; do
    echo "Server not ready, waiting..."
    sleep 2
done
echo "Server is ready!"

# 1. Health check
echo "=== Health Check ==="
curl http://localhost:8000/health

# Expected output: {"status":"ok"}

# 2. List models
echo -e "\n=== Available Models ==="
curl http://localhost:8000/v1/models

# Expected output: JSON with model list

# 3. Chat completion
echo -e "\n=== Chat Completion ==="
curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "meta-llama/Llama-2-7b-hf",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain neural networks in one sentence."}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }' | jq '.'

# Expected output: JSON with assistant's response

# 4. Streaming completion
echo -e "\n=== Streaming Completion ==="
curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "meta-llama/Llama-2-7b-hf",
        "messages": [{"role": "user", "content": "Count to 5"}],
        "stream": true
    }'

# Expected output: Multiple JSON chunks with streaming tokens

# 5. Performance test
echo -e "\n=== Performance Test ==="
time curl -X POST http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "meta-llama/Llama-2-7b-hf",
        "prompt": "Write a short story about AI",
        "max_tokens": 200
    }' > /dev/null

# Expected output: Time taken for generation
```

```python
# vllm_client.py - Complete Python client for vLLM
import requests
import json
from typing import List, Dict, Optional

class VLLMClient:
    """Production-ready client for vLLM OpenAI-compatible API."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def health_check(self) -> bool:
        """Check if server is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_models(self) -> List[str]:
        """List available models."""
        response = requests.get(f"{self.base_url}/v1/models")
        response.raise_for_status()
        data = response.json()
        return [model["id"] for model in data.get("data", [])]

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "meta-llama/Llama-2-7b-hf",
        temperature: float = 0.7,
        max_tokens: int = 100,
        stream: bool = False
    ) -> Dict:
        """Create chat completion."""
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def completion(
        self,
        prompt: str,
        model: str = "meta-llama/Llama-2-7b-hf",
        temperature: float = 0.7,
        max_tokens: int = 100
    ) -> Dict:
        """Create text completion."""
        url = f"{self.base_url}/v1/completions"
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == "__main__":
    client = VLLMClient()

    # Health check
    print(f"Server healthy: {client.health_check()}")

    # List models
    models = client.list_models()
    print(f"Available models: {models}")

    # Chat completion
    response = client.chat_completion(
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        max_tokens=50
    )
    print("\nResponse:")
    print(response["choices"][0]["message"]["content"])
```

### Exercise 3: Monitoring Setup

**Objective:** Setup Prometheus metrics for vLLM monitoring.

**Solution:**

```python
# vllm_metrics.py - Complete Prometheus monitoring setup
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import time
import logging
from functools import wraps
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define metrics
request_count = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'status']
)

token_count = Counter(
    'llm_tokens_total',
    'Total tokens generated',
    ['model', 'type']  # type: input or output
)

latency = Histogram(
    'llm_inference_latency_seconds',
    'Inference latency',
    ['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

gpu_memory_usage = Gauge(
    'llm_gpu_memory_bytes',
    'GPU memory usage',
    ['gpu_id']
)

active_requests = Gauge(
    'llm_active_requests',
    'Currently active requests'
)

batch_size = Histogram(
    'llm_batch_size',
    'Batch size per request',
    buckets=[1, 2, 4, 8, 16, 32, 64]
)

class LLMMetricsCollector:
    """Complete metrics collection for LLM serving."""

    def __init__(self):
        self.start_time = time.time()

    def start_metrics_server(self, port: int = 8001):
        """Start Prometheus metrics server."""
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")

    def track_request(self, model: str):
        """Decorator to track requests."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                active_requests.inc()
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    request_count.labels(model=model, status='success').inc()
                    return result
                except Exception as e:
                    request_count.labels(model=model, status='error').inc()
                    logger.error(f"Request failed: {e}")
                    raise
                finally:
                    latency.labels(model=model).observe(time.time() - start_time)
                    active_requests.dec()
            return wrapper
        return decorator

    def record_tokens(self, model: str, input_tokens: int, output_tokens: int):
        """Record token counts."""
        token_count.labels(model=model, type='input').inc(input_tokens)
        token_count.labels(model=model, type='output').inc(output_tokens)

    def update_gpu_memory(self, gpu_id: int, memory_bytes: int):
        """Update GPU memory usage."""
        gpu_memory_usage.labels(gpu_id=gpu_id).set(memory_bytes)

    def record_batch_size(self, size: int):
        """Record batch size."""
        batch_size.observe(size)

# Usage example
metrics = LLMMetricsCollector()
metrics.start_metrics_server()

@metrics.track_request(model="llama2-7b")
def generate_with_metrics(prompt: str, max_tokens: int = 100):
    """Simulate LLM generation with metrics."""
    # Simulate inference
    time.sleep(0.5)

    # Record tokens (simulated)
    input_tokens = len(prompt.split())
    output_tokens = max_tokens
    metrics.record_tokens("llama2-7b", input_tokens, output_tokens)

    # Record batch size
    metrics.record_batch_size(1)

    return f"Generated {output_tokens} tokens"

# Test
if __name__ == "__main__":
    logger.info("Testing metrics collection...")

    # Generate some requests
    for i in range(5):
        result = generate_with_metrics("Hello, world!", 50)
        logger.info(f"Request {i+1}: {result}")

    logger.info("Metrics available at http://localhost:8001/metrics")
    logger.info("Sample output: llm_requests_total{model='llama2-7b',status='success'} 5.0")
```

```yaml
# prometheus.yml - Prometheus configuration for vLLM
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'vllm-metrics'
    static_configs:
      - targets: ['localhost:8001']
        labels:
          service: 'vllm'
          environment: 'production'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
```

### Exercise 4: Load Balancing

**Objective:** Setup Nginx load balancer for multiple vLLM backends.

**Solution:**

```nginx
# nginx.conf - Complete Nginx load balancer configuration
upstream vllm_backends {
    # Load balancing algorithm: least_conn
    least_conn;

    # Backend servers
    server vllm-1:8000 max_fails=3 fail_timeout=30s weight=1;
    server vllm-2:8000 max_fails=3 fail_timeout=30s weight=1;
    server vllm-3:8000 max_fails=3 fail_timeout=30s weight=1;

    # Keepalive connections
    keepalive 32;
    keepalive_timeout 60s;
}

server {
    listen 80;
    server_name llm.example.com;

    # Logging
    access_log /var/log/nginx/vllm_access.log;
    error_log /var/log/nginx/vllm_error.log;

    # Client settings
    client_max_body_size 100M;
    client_body_timeout 300s;
    client_header_timeout 300s;

    # Proxy settings
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    proxy_buffering off;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # vLLM API endpoints
    location /v1/ {
        proxy_pass http://vllm_backends;

        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # HTTP/1.1
        proxy_http_version 1.1;
    }

    # Metrics endpoint
    location /metrics {
        proxy_pass http://vllm_backends/metrics;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```yaml
# docker-compose.yml - Complete vLLM cluster setup

services:
  vllm-1:
    image: vllm/vllm-openai:v0.6.0
    container_name: vllm-1
    ports:
      - "8001:8000"
    command: >
      --model meta-llama/Llama-2-7b-hf
      --host 0.0.0.0
      --port 8000
      --gpu-memory-utilization 0.9
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - vllm-network

  vllm-2:
    image: vllm/vllm-openai:v0.6.0
    container_name: vllm-2
    ports:
      - "8002:8000"
    command: >
      --model meta-llama/Llama-2-7b-hf
      --host 0.0.0.0
      --port 8000
      --gpu-memory-utilization 0.9
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - vllm-network

  vllm-3:
    image: vllm/vllm-openai:v0.6.0
    container_name: vllm-3
    ports:
      - "8003:8000"
    command: >
      --model meta-llama/Llama-2-7b-hf
      --host 0.0.0.0
      --port 8000
      --gpu-memory-utilization 0.9
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - vllm-network

  nginx:
    image: nginx:1.25-alpine
    container_name: nginx-lb
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - vllm-1
      - vllm-2
      - vllm-3
    networks:
      - vllm-network

networks:
  vllm-network:
    driver: bridge
```

```bash
# test_load_balancer.sh - Test load balancer distribution
#!/bin/bash

ENDPOINT="http://localhost/v1/chat/completions"

echo "Testing load balancer distribution..."
echo "Sending 10 requests..."

for i in {1..10}; do
  response=$(curl -s -X POST $ENDPOINT \
    -H "Content-Type: application/json" \
    -d '{
      "model": "meta-llama/Llama-2-7b-hf",
      "messages": [{"role": "user", "content": "Hello"}]
    }')

  echo "Request $i completed"
  sleep 0.1
done

# Check nginx logs for distribution
echo -e "\nRequest distribution:"
docker logs nginx-lb --tail=50 | grep "vllm-" | awk '{print $1}' | sort | uniq -c

# Expected output: Shows requests distributed across backends
```

### Exercise 5: Model Drift Detection

**Objective:** Monitor model performance and detect drift.

**Solution:**

```python
# model_drift.py - Complete model drift detection system
import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class DriftAlert:
    """Alert data for model drift."""
    metric_name: str
    baseline_value: float
    current_value: float
    change_percent: float
    severity: str  # 'low', 'medium', 'high'
    timestamp: datetime

class ModelDriftDetector:
    """Complete model drift detection system."""

    def __init__(self, threshold: float = 0.05):
        """
        Initialize drift detector.

        Args:
            threshold: Relative change threshold (5% = 0.05)
        """
        self.threshold = threshold
        self.baseline_metrics = {}
        self.alerts = []

    def set_baseline(self, metrics: Dict[str, float]):
        """Set baseline metrics from golden dataset."""
        self.baseline_metrics = metrics.copy()
        print(f"Baseline set: {json.dumps(metrics, indent=2)}")

    def detect_drift(
        self,
        current_metrics: Dict[str, float]
    ) -> Tuple[bool, List[DriftAlert]]:
        """
        Detect if model performance has degraded.

        Args:
            current_metrics: Current performance metrics

        Returns:
            Tuple of (drift_detected, list of alerts)
        """
        drift_detected = False
        alerts = []

        for metric_name, current_value in current_metrics.items():
            if metric_name not in self.baseline_metrics:
                continue

            baseline_value = self.baseline_metrics[metric_name]

            # Calculate relative change
            if baseline_value > 0:
                relative_change = abs(current_value - baseline_value) / baseline_value
            else:
                relative_change = 0.0

            # Check if change exceeds threshold
            if relative_change > self.threshold:
                drift_detected = True

                # Determine severity
                severity = self._get_severity(relative_change)

                alert = DriftAlert(
                    metric_name=metric_name,
                    baseline_value=baseline_value,
                    current_value=current_value,
                    change_percent=relative_change * 100,
                    severity=severity,
                    timestamp=datetime.now()
                )
                alerts.append(alert)

        self.alerts.extend(alerts)
        return drift_detected, alerts

    def _get_severity(self, relative_change: float) -> str:
        """Determine alert severity based on change magnitude."""
        if relative_change > 0.20:  # >20% change
            return "high"
        elif relative_change > 0.10:  # >10% change
            return "medium"
        else:
            return "low"

    def get_alert_summary(self) -> Dict:
        """Get summary of all alerts."""
        if not self.alerts:
            return {"total_alerts": 0, "by_severity": {}}

        severity_counts = {}
        for alert in self.alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1

        return {
            "total_alerts": len(self.alerts),
            "by_severity": severity_counts,
            "recent_alerts": [
                {
                    "metric": a.metric_name,
                    "change": f"{a.change_percent:.2f}%",
                    "severity": a.severity,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in self.alerts[-5:]
            ]
        }

class PerformanceMonitor:
    """Monitor model performance over time."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history = {}

    def record_metrics(self, metrics: Dict[str, float]):
        """Record metrics for current batch."""
        for metric_name, value in metrics.items():
            if metric_name not in self.metrics_history:
                self.metrics_history[metric_name] = []

            self.metrics_history[metric_name].append(value)

            # Keep only recent history
            if len(self.metrics_history[metric_name]) > self.window_size:
                self.metrics_history[metric_name].pop(0)

    def get_average_metrics(self) -> Dict[str, float]:
        """Get average metrics over the window."""
        averages = {}
        for metric_name, values in self.metrics_history.items():
            if values:
                averages[metric_name] = np.mean(values)
        return averages

    def get_std_metrics(self) -> Dict[str, float]:
        """Get standard deviation of metrics."""
        stds = {}
        for metric_name, values in self.metrics_history.items():
            if len(values) > 1:
                stds[metric_name] = np.std(values)
        return stds

# Usage example
if __name__ == "__main__":
    # Initialize detector
    detector = ModelDriftDetector(threshold=0.05)
    monitor = PerformanceMonitor(window_size=100)

    # Set baseline from golden dataset
    baseline_metrics = {
        "accuracy": 0.92,
        "precision": 0.89,
        "recall": 0.87,
        "f1_score": 0.88,
        "latency_p50": 0.5,
        "latency_p95": 1.2,
        "throughput": 100.0
    }
    detector.set_baseline(baseline_metrics)

    # Simulate monitoring
    print("\n=== Simulating Model Monitoring ===\n")

    # Normal performance
    print("Monitoring batch 1 (normal)...")
    current_metrics = {
        "accuracy": 0.918,
        "precision": 0.885,
        "recall": 0.868,
        "f1_score": 0.876,
        "latency_p50": 0.52,
        "latency_p95": 1.25,
        "throughput": 98.0
    }
    monitor.record_metrics(current_metrics)
    drift, alerts = detector.detect_drift(current_metrics)

    if drift:
        print(f"⚠️  DRIFT DETECTED: {len(alerts)} alerts")
        for alert in alerts:
            print(f"  - {alert.metric_name}: {alert.change_percent:.2f}% change")
    else:
        print("✓ Performance within normal range")

    # Degraded performance
    print("\nMonitoring batch 2 (degraded)...")
    degraded_metrics = {
        "accuracy": 0.85,  # 7.6% drop
        "precision": 0.82,  # 7.9% drop
        "recall": 0.80,  # 8.0% drop
        "f1_score": 0.81,  # 8.0% drop
        "latency_p50": 0.65,  # 30% increase
        "latency_p95": 1.8,  # 50% increase
        "throughput": 85.0  # 15% drop
    }
    monitor.record_metrics(degraded_metrics)
    drift, alerts = detector.detect_drift(degraded_metrics)

    if drift:
        print(f"⚠️  DRIFT DETECTED: {len(alerts)} alerts")
        for alert in alerts:
            print(f"  - {alert.metric_name}: {alert.change_percent:.2f}% change ({alert.severity} severity)")
    else:
        print("✓ Performance within normal range")

    # Get alert summary
    print("\n=== Alert Summary ===")
    summary = detector.get_alert_summary()
    print(json.dumps(summary, indent=2))

    # Get performance stats
    print("\n=== Performance Statistics ===")
    avg_metrics = monitor.get_average_metrics()
    std_metrics = monitor.get_std_metrics()
    print(f"Averages: {json.dumps(avg_metrics, indent=2)}")
    print(f"Std Devs: {json.dumps(std_metrics, indent=2)}")

# Expected output:
# Baseline metrics set
# Monitoring shows drift detection
# Alerts with severity levels
# Performance statistics
```

---

## Summary

This practice guide covers:

1. **Ollama Setup:** Installation, model management, and local inference
2. **vLLM Serving:** Production server setup with OpenAI-compatible API
3. **Monitoring:** Prometheus metrics collection and exposure
4. **Load Balancing:** Nginx configuration for multi-instance deployment
5. **Drift Detection:** Performance monitoring and alerting system

**Expected Learning Outcomes:**
- Deploy and manage LLM inference servers
- Implement monitoring and observability
- Setup load balancing for high availability
- Detect and respond to model performance drift
