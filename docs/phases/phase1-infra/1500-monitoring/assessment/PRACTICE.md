# 1500: Monitoring - Practice

## Exercises

### Exercise 1: Prometheus Setup

**Objective:** Configure and run Prometheus for monitoring LLM applications.

**Solution:**

```yaml
# prometheus.yml - Complete Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'llm-production'
    environment: 'prod'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# Rule files
rule_files:
    - 'alerts.yml'

# Scrape configurations
scrape_configs:
  # LLM API metrics
  - job_name: 'llm-api'
    static_configs:
      - targets:
          - 'localhost:8000'
        labels:
          service: 'vllm'
          team: 'ml-infra'

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets:
          - 'localhost:9090'

  # Node exporter for system metrics
  - job_name: 'node'
    static_configs:
      - targets:
          - 'localhost:9100'

  # GPU metrics
  - job_name: 'gpu-exporter'
    static_configs:
      - targets:
          - 'localhost:9400'

  # cAdvisor for container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets:
          - 'localhost:8080'
```

```bash
#!/bin/bash
# start_prometheus.sh - Complete Prometheus startup script

# 1. Create directories
mkdir -p prometheus/data prometheus/config

# 2. Create configuration
cat > prometheus/config/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'llm-api'
    static_configs:
      - targets: ['localhost:8000']
EOF

# 3. Run Prometheus with Docker
docker run -d \
    --name prometheus \
    --network host \
    -p 9090:9090 \
    -v $(pwd)/prometheus/config/prometheus.yml:/etc/prometheus/prometheus.yml \
    -v $(pwd)/prometheus/data:/prometheus \
    prom/prometheus:latest \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus \
    --web.console.libraries=/usr/share/prometheus/console_libraries \
    --web.console.templates=/usr/share/prometheus/consoles

# 4. Wait for startup
echo "Waiting for Prometheus to start..."
sleep 5

# 5. Verify
curl -s http://localhost:9090/-/healthy | grep "Prometheus is Healthy."

# 6. Check targets
echo "Checking targets..."
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Expected output:
# Prometheus is Healthy.
# Shows job names and health status

# Troubleshooting Tips:
# - If port 9090 in use: Change port mapping or stop conflicting service
# - If config errors: Validate with 'promtool check config prometheus.yml'
# - If permission errors: Check volume permissions for /prometheus/data
```

### Exercise 2: Grafana Dashboard

**Objective:** Create a comprehensive monitoring dashboard for LLM applications.

**Solution:**

```python
# create_grafana_dashboard.py - Complete dashboard configuration
import json

dashboard = {
    "dashboard": {
        "title": "LLM Production Monitoring",
        "description": "Complete monitoring for LLM inference serving",
        "tags": ["llm", "inference", "production"],
        "timezone": "UTC",
        "refresh": "10s",
        "panels": [
            {
                "id": 1,
                "title": "Request Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(llm_requests_total{model='llama2-7b'}[1m])",
                        "legendFormat": "{{status}} requests/sec"
                    }
                ],
                "yAxes": [
                    {"label": "Requests/sec"}
                ]
            },
            {
                "id": 2,
                "title": "Tokens per Second",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(llm_tokens_total{model='llama2-7b',type='output'}[1m])",
                        "legendFormat": "Output tokens/sec"
                    },
                    {
                        "expr": "rate(llm_tokens_total{model='llama2-7b',type='input'}[1m])",
                        "legendFormat": "Input tokens/sec"
                    }
                ],
                "yAxes": [
                    {"label": "Tokens/sec"}
                ]
            },
            {
                "id": 3,
                "title": "P95 Latency",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(llm_inference_latency_seconds_bucket{model='llama2-7b'}[5m]))",
                        "legendFormat": "P95 Latency"
                    }
                ],
                "yAxes": [
                    {"label": "Seconds"}
                ]
            },
            {
                "id": 4,
                "title": "GPU Utilization",
                "type": "graph",
                "targets": [
                    {
                        "expr": "nvidia_gpu_utilization",
                        "legendFormat": "GPU {{gpu_id}}"
                    }
                ],
                "yAxes": [
                    {"label": "Percent", "min": 0, "max": 100}
                ]
            },
            {
                "id": 5,
                "title": "GPU Memory Usage",
                "type": "graph",
                "targets": [
                    {
                        "expr": "nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes * 100",
                        "legendFormat": "GPU {{gpu_id}} memory %"
                    }
                ],
                "yAxes": [
                    {"label": "Percent", "min": 0, "max": 100}
                ]
            },
            {
                "id": 6,
                "title": "Active Requests",
                "type": "stat",
                "targets": [
                    {
                        "expr": "llm_active_requests",
                        "legendFormat": "Active"
                    }
                ]
            },
            {
                "id": 7,
                "title": "Error Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(llm_requests_total{status='error'}[5m]) / rate(llm_requests_total[5m]) * 100",
                        "legendFormat": "Error rate %"
                    }
                ],
                "yAxes": [
                    {"label": "Percent", "min": 0, "max": 100}
                ]
            },
            {
                "id": 8,
                "title": "Throughput",
                "type": "graph",
                "targets": [
                    {
                        "expr": "sum(rate(llm_tokens_total{type='output'}[5m]))",
                        "legendFormat": "Total tokens/sec"
                    }
                ],
                "yAxes": [
                    {"label": "Tokens/sec"}
                ]
            }
        ]
    }
}

# Save dashboard
with open('grafana_llm_dashboard.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("Dashboard configuration saved to grafana_llm_dashboard.json")

# Expected output:
# JSON file with complete dashboard configuration
```

```bash
#!/bin/bash
# setup_grafana.sh - Complete Grafana setup

# 1. Start Grafana with Docker
docker run -d \
    --name grafana \
    -p 3000:3000 \
    -e GF_SECURITY_ADMIN_PASSWORD=admin \
    -e GF_USERS_ALLOW_SIGN_UP=false \
    grafana/grafana:latest

# 2. Wait for startup
echo "Waiting for Grafana to start..."
sleep 10

# 3. Verify
curl -s http://localhost:3000/api/health | grep "commit"

# 4. Add Prometheus datasource
curl -X POST http://localhost:3000/api/datasources \
    -u admin:admin \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://localhost:9090",
        "access": "proxy",
        "isDefault": true
    }'

# 5. Import dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
    -u admin:admin \
    -H "Content-Type: application/json" \
    -d @grafana_llm_dashboard.json

# 6. Display access info
echo "=== Grafana Setup Complete ==="
echo "URL: http://localhost:3000"
echo "Username: admin"
echo "Password: admin"
echo ""
echo "Expected output:"
echo "- Dashboard shows 8 panels with LLM metrics"
echo "- Data populates from Prometheus"
echo "- Refresh every 10 seconds"

# Troubleshooting Tips:
# - If connection refused: Check if container is running with 'docker ps'
# - If datasource error: Verify Prometheus is accessible at http://localhost:9090
# - If dashboard import fails: Check JSON format and API credentials
```

### Exercise 3: Custom Metrics

**Objective:** Implement comprehensive metrics collection for LLM applications.

**Solution:**

```python
# llm_metrics_collector.py - Complete metrics collection system
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import logging
from functools import wraps
from typing import Dict, Any, Optional
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMMetrics:
    """Complete metrics collection for LLM serving."""

    def __init__(self):
        # Request metrics
        self.requests_total = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['model', 'status', 'endpoint']
        )

        # Token metrics
        self.tokens_generated = Counter(
            'llm_tokens_total',
            'Tokens generated',
            ['model', 'type']  # type: input, output
        )

        # Latency metrics with detailed buckets
        self.inference_latency = Histogram(
            'llm_inference_latency_seconds',
            'Inference latency',
            ['model', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )

        # Preprocessing latency
        self.preprocessing_latency = Histogram(
            'llm_preprocessing_latency_seconds',
            'Tokenization and preprocessing latency',
            ['model'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
        )

        # Postprocessing latency
        self.postprocessing_latency = Histogram(
            'llm_postprocessing_latency_seconds',
            'Detokenization and postprocessing latency',
            ['model'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
        )

        # GPU metrics
        self.gpu_memory_usage = Gauge(
            'llm_gpu_memory_bytes',
            'GPU memory usage',
            ['model', 'gpu_id']
        )

        self.gpu_utilization = Gauge(
            'llm_gpu_utilization_percent',
            'GPU utilization percentage',
            ['model', 'gpu_id']
        )

        # Active requests
        self.active_requests = Gauge(
            'llm_active_requests',
            'Currently active requests',
            ['model']
        )

        # Queue metrics
        self.queue_size = Gauge(
            'llm_queue_size',
            'Current request queue size',
            ['model']
        )

        # Batch metrics
        self.batch_size = Histogram(
            'llm_batch_size',
            'Request batch size',
            ['model'],
            buckets=[1, 2, 4, 8, 16, 32, 64, 128]
        )

        # Cache metrics
        self.cache_hits = Counter(
            'llm_cache_hits_total',
            'KV cache hits',
            ['model']
        )

        self.cache_misses = Counter(
            'llm_cache_misses_total',
            'KV cache misses',
            ['model']
        )

    def track_request(self, model: str, endpoint: str = "chat"):
        """Decorator to track requests with full metrics."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.active_requests.labels(model=model).inc()
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)

                    # Record success
                    self.requests_total.labels(
                        model=model,
                        status='success',
                        endpoint=endpoint
                    ).inc()

                    return result

                except Exception as e:
                    # Record error
                    self.requests_total.labels(
                        model=model,
                        status='error',
                        endpoint=endpoint
                    ).inc()
                    logger.error(f"Request failed: {e}")
                    raise

                finally:
                    # Record latency
                    latency = time.time() - start_time
                    self.inference_latency.labels(model=model, endpoint=endpoint).observe(latency)
                    self.active_requests.labels(model=model).dec()

            return wrapper
        return decorator

    def record_tokens(self, model: str, input_tokens: int, output_tokens: int):
        """Record token counts."""
        self.tokens_generated.labels(model=model, type='input').inc(input_tokens)
        self.tokens_generated.labels(model=model, type='output').inc(output_tokens)

    def record_batch(self, model: str, batch_size: int):
        """Record batch size."""
        self.batch_size.labels(model=model).observe(batch_size)

    def update_gpu_metrics(self, model: str, gpu_id: int = 0):
        """Update GPU metrics from system."""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)

            # Memory usage
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            self.gpu_memory_usage.labels(model=model, gpu_id=gpu_id).set(mem_info.used)

            # GPU utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            self.gpu_utilization.labels(model=model, gpu_id=gpu_id).set(utilization.gpu)

        except Exception as e:
            logger.warning(f"Failed to get GPU metrics: {e}")

    def record_cache_hit(self, model: str):
        """Record cache hit."""
        self.cache_hits.labels(model=model).inc()

    def record_cache_miss(self, model: str):
        """Record cache miss."""
        self.cache_misses.labels(model=model).inc()

# Usage example with inference loop
metrics = LLMMetrics()

def generate_with_metrics(model, prompt: str, max_tokens: int = 100):
    """Generate text with complete metrics tracking."""
    model_name = "llama2-7b"

    # Preprocessing
    preprocess_start = time.time()
    tokens = tokenize(prompt)
    preprocessing_time = time.time() - preprocess_start
    metrics.preprocessing_latency.labels(model=model_name).observe(preprocessing_time)

    # Inference
    with metrics.track_request(model_name):
        outputs = model.generate(tokens, max_tokens=max_tokens)

    # Postprocessing
    postprocess_start = time.time()
    text = detokenize(outputs)
    postprocessing_time = time.time() - postprocess_start
    metrics.postprocessing_latency.labels(model=model_name).observe(postprocessing_time)

    # Record metrics
    num_tokens = len(outputs)
    metrics.record_tokens(model_name, len(tokens), num_tokens)
    metrics.record_batch(model_name, 1)

    # Update GPU metrics
    metrics.update_gpu_metrics(model_name)

    return text

# Test the metrics system
if __name__ == "__main__":
    # Start metrics server
    start_http_server(8001)
    logger.info("Metrics server started on port 8001")

    # Simulate some requests
    @metrics.track_request(model="llama2-7b", endpoint="chat")
    def mock_inference(prompt: str):
        time.sleep(0.1)  # Simulate inference
        return "Generated response"

    # Generate test traffic
    logger.info("Generating test metrics...")
    for i in range(10):
        response = mock_inference(f"Test prompt {i}")
        metrics.record_tokens("llama2-7b", 5, 20)
        logger.info(f"Request {i+1}: {response}")

    logger.info("Metrics available at http://localhost:8001/metrics")
    logger.info("Expected output:")
    logger.info("  - llm_requests_total{model='llama2-7b',status='success'} 10.0")
    logger.info("  - llm_tokens_total{model='llama2-7b',type='input'} 50.0")
    logger.info("  - llm_tokens_total{model='llama2-7b',type='output'} 200.0")
```

### Exercise 4: Alert Rules

**Objective:** Configure comprehensive alerting for LLM applications.

**Solution:**

```yaml
# alerts.yml - Complete alert configuration
groups:
  - name: llm_performance_alerts
    interval: 30s
    rules:
      # High latency alert
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(llm_inference_latency_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
          team: ml-infra
        annotations:
          summary: "LLM inference latency too high"
          description: "P95 latency is {{ $value }}s for model {{ $labels.model }}"
          runbook_url: "https://runbooks.example.com/high-latency"

      # Critical latency alert
      - alert: CriticalLatency
        expr: |
          histogram_quantile(0.95, rate(llm_inference_latency_seconds_bucket[5m])) > 10
        for: 2m
        labels:
          severity: critical
          team: ml-infra
        annotations:
          summary: "Critical LLM inference latency"
          description: "P95 latency is {{ $value }}s - immediate action required"

      # Low throughput alert
      - alert: LowThroughput
        expr: |
          rate(llm_tokens_total{type='output'}[5m]) < 100
        for: 10m
        labels:
          severity: warning
          team: ml-infra
        annotations:
          summary: "Token throughput below threshold"
          description: "Throughput is {{ $value }} tokens/sec (expected >100)"

      # High error rate alert
      - alert: HighErrorRate
        expr: |
          rate(llm_requests_total{status='error'}[5m]) / rate(llm_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
          team: ml-infra
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Critical error rate alert
      - alert: CriticalErrorRate
        expr: |
          rate(llm_requests_total{status='error'}[5m]) / rate(llm_requests_total[5m]) > 0.10
        for: 2m
        labels:
          severity: critical
          team: ml-infra
        annotations:
          summary: "Critical error rate"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # High GPU memory alert
      - alert: HighGPUMemory
        expr: |
          llm_gpu_memory_bytes / nvidia_gpu_total_memory_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          team: ml-infra
        annotations:
          summary: "GPU memory usage critical"
          description: "GPU {{ $labels.gpu_id }} memory usage is {{ $value | humanizePercentage }}"

      # GPU OOM prediction
      - alert: GPUMemoryPredictedOOM
        expr: |
          predict_linear(llm_gpu_memory_bytes[1h], 3600) > nvidia_gpu_total_memory_bytes * 0.95
        for: 5m
        labels:
          severity: warning
          team: ml-infra
        annotations:
          summary: "GPU predicted to run out of memory"
          description: "GPU {{ $labels.gpu_id }} will OOM within 1 hour at current rate"

      # Service down alert
      - alert: ServiceDown
        expr: up{job='llm-api'} == 0
        for: 1m
        labels:
          severity: critical
          team: ml-infra
        annotations:
          summary: "LLM service is down"
          description: "LLM API {{ $labels.instance }} has been down for more than 1 minute"

      # Queue growing alert
      - alert: QueueGrowing
        expr: |
          llm_queue_size > 100
        for: 5m
        labels:
          severity: warning
          team: ml-infra
        annotations:
          summary: "Request queue growing"
          description: "Queue size is {{ $value }} requests"

  - name: llm_infrastructure_alerts
    interval: 30s
    rules:
      # High CPU alert
      - alert: HighCPUUsage
        expr: |
          rate(process_cpu_seconds_total{job='llm-api'}[5m]) > 0.8
        for: 10m
        labels:
          severity: warning
          team: infra
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value | humanizePercentage }}"

      # High memory alert
      - alert: HighMemoryUsage
        expr: |
          process_resident_memory_bytes{job='llm-api'} / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          team: infra
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # Disk space alert
      - alert: LowDiskSpace
        expr: |
          node_filesystem_avail_bytes{mountpoint='/'} / node_filesystem_size_bytes{mountpoint='/'} < 0.1
        for: 5m
        labels:
          severity: warning
          team: infra
        annotations:
          summary: "Low disk space"
          description: "Disk space is {{ $value | humanizePercentage }} available"
```

```bash
#!/bin/bash
# setup_alerts.sh - Complete alert setup

# 1. Validate alert rules
docker run --rm \
    -v $(pwd)/alerts.yml:/etc/prometheus/alerts.yml \
    prom/prometheus:latest \
    promtool check config /etc/prometheus/alerts.yml

# Expected output: SUCCESS: 0 rule files found

# 2. Update Prometheus configuration to use alerts
cat >> prometheus.yml <<EOF

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

# Load alert rules
rule_files:
    - 'alerts.yml'
EOF

# 3. Restart Prometheus with alerts
docker restart prometheus

# 4. Verify alerts are loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {name: .name, type: .type}'

# 5. Check alert status
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alert: .labels.alertname, state: .state}'

# Expected output:
# List of all alert rules with their names and types
# Current state of alerts (firing, pending, inactive)

# Troubleshooting Tips:
# - If alerts not loaded: Check Prometheus logs with 'docker logs prometheus'
# - If validation fails: Use 'promtool check rules' to find syntax errors
# - If alerts not firing: Check expression in Prometheus UI graph view
```

### Exercise 5: Log Aggregation

**Objective:** Implement structured logging with JSON output and log aggregation.

**Solution:**

```python
# structured_logging.py - Complete structured logging system
import structlog
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager

# Configure structlog
structlog.configure(
    processors=[
        # Add log level
        structlog.stdlib.add_log_level,

        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),

        # Add logger name
        structlog.stdlib.add_logger_name,

        # Add call site info
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),

        # Format as JSON
        structlog.processors.JSONRenderer()

        # For development, use ConsoleRenderer instead:
        # structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

class LLMLogger:
    """Structured logger for LLM applications."""

    def __init__(self, service_name: str = "llm-service"):
        self.logger = structlog.get_logger()
        self.service_name = service_name

    def log_request(
        self,
        request_id: str,
        model: str,
        endpoint: str,
        prompt: str,
        prompt_tokens: int,
        max_tokens: int,
        parameters: Dict[str, Any],
        **kwargs
    ):
        """Log incoming request."""
        self.logger.info(
            "llm_request",
            service=self.service_name,
            request_id=request_id,
            model=model,
            endpoint=endpoint,
            prompt_length=len(prompt),
            prompt_tokens=prompt_tokens,
            max_tokens=max_tokens,
            parameters=parameters,
            **kwargs
        )

    def log_response(
        self,
        request_id: str,
        model: str,
        output_text: str,
        output_tokens: int,
        latency_seconds: float,
        **kwargs
    ):
        """Log response."""
        self.logger.info(
            "llm_response",
            service=self.service_name,
            request_id=request_id,
            model=model,
            output_length=len(output_text),
            output_tokens=output_tokens,
            latency_ms=latency_seconds * 1000,
            tokens_per_second=output_tokens / latency_seconds if latency_seconds > 0 else 0,
            **kwargs
        )

    def log_error(
        self,
        request_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        **kwargs
    ):
        """Log error."""
        self.logger.error(
            "llm_error",
            service=self.service_name,
            request_id=request_id,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            **kwargs
        )

    def log_system_metrics(
        self,
        gpu_id: int,
        gpu_memory_used: int,
        gpu_memory_total: int,
        gpu_utilization: float,
        **kwargs
    ):
        """Log system metrics."""
        self.logger.info(
            "system_metrics",
            service=self.service_name,
            gpu_id=gpu_id,
            gpu_memory_used_bytes=gpu_memory_used,
            gpu_memory_total_bytes=gpu_memory_total,
            gpu_memory_percent=(gpu_memory_used / gpu_memory_total * 100),
            gpu_utilization_percent=gpu_utilization,
            **kwargs
        )

    @contextmanager
    def log_latency(self, operation: str, **context):
        """Context manager to log operation latency."""
        start_time = time.time()
        try:
            yield
        finally:
            latency = time.time() - start_time
            self.logger.info(
                "operation_latency",
                service=self.service_name,
                operation=operation,
                latency_seconds=latency,
                **context
            )

# Usage examples
logger = LLMLogger()

def process_request(request_id: str, prompt: str):
    """Process request with complete logging."""
    model = "llama2-7b"

    # Log request
    logger.log_request(
        request_id=request_id,
        model=model,
        endpoint="chat",
        prompt=prompt,
        prompt_tokens=len(prompt.split()),
        max_tokens=100,
        parameters={"temperature": 0.7}
    )

    # Log preprocessing latency
    with logger.log_latency("preprocessing", request_id=request_id):
        tokens = tokenize(prompt)

    # Log inference latency
    with logger.log_latency("inference", request_id=request_id):
        try:
            output = generate(tokens)
            output_text = detokenize(output)

            # Log response
            logger.log_response(
                request_id=request_id,
                model=model,
                output_text=output_text,
                output_tokens=len(output),
                latency_seconds=0.5
            )

            return output_text

        except Exception as e:
            # Log error
            logger.log_error(
                request_id=request_id,
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )
            raise

# Test the logger
if __name__ == "__main__":
    import uuid

    print("=== Structured Logging Demo ===\n")

    # Generate a request ID
    request_id = str(uuid.uuid4())

    # Log a request
    logger.log_request(
        request_id=request_id,
        model="llama2-7b",
        endpoint="chat",
        prompt="What is AI?",
        prompt_tokens=4,
        max_tokens=100,
        parameters={"temperature": 0.7, "top_p": 0.9}
    )

    # Log a response
    logger.log_response(
        request_id=request_id,
        model="llama2-7b",
        output_text="AI is artificial intelligence.",
        output_tokens=5,
        latency_seconds=0.5
    )

    # Log system metrics
    logger.log_system_metrics(
        gpu_id=0,
        gpu_memory_used=8 * 1024**3,  # 8GB
        gpu_memory_total=24 * 1024**3,  # 24GB
        gpu_utilization=75.5
    )

    # Log an error
    logger.log_error(
        request_id=request_id,
        error_type="ValueError",
        error_message="Invalid temperature parameter",
        stack_trace="Traceback..."
    )

    print("\nExpected JSON log output:")
    print(json.dumps({
        "event": "llm_request",
        "service": "llm-service",
        "request_id": request_id,
        "model": "llama2-7b",
        "prompt_length": 10,
        "timestamp": "2026-02-05T10:30:00.000Z",
        "level": "info",
        "logger": "__main__"
    }, indent=2))
```

```bash
#!/bin/bash
# setup_log_aggregation.sh - Complete log aggregation setup

# 1. Create Loki configuration
cat > loki-config.yml <<EOF
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 1h
  max_chunk_age: 1h

schema_config:
  configs:
    - from: 2026-02-05
      store: boltdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb:
    directory: /loki/index
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
EOF

# 2. Start Loki with Docker
docker run -d \
    --name loki \
    -p 3100:3100 \
    -v $(pwd)/loki-data:/loki \
    -v $(pwd)/loki-config.yml:/etc/loki/local-config.yaml \
    grafana/loki:latest \
    -config.file=/etc/loki/local-config.yaml

# 3. Start Promtail to collect logs
cat > promtail-config.yml <<EOF
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: llm-service
    static_configs:
      - targets:
          - localhost
        labels:
          job: llm-service
          environment: production
          __path__: /var/log/llm-service/*.log
EOF

docker run -d \
    --name promtail \
    -v $(pwd)/promtail-config.yml:/etc/promtail/config.yml \
    -v /var/log:/var/log:ro \
    grafana/promtail:latest \
    -config.file=/etc/promtail/config.yml

# 4. Add Loki datasource to Grafana
curl -X POST http://localhost:3000/api/datasources \
    -u admin:admin \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Loki",
        "type": "loki",
        "url": "http://localhost:3100",
        "access": "proxy"
    }'

echo "=== Log Aggregation Setup Complete ==="
echo "Loki: http://localhost:3100"
echo "Promtail: Collecting logs from /var/log"
echo ""
echo "Query logs in Grafana:"
echo '{job="llm-service"} |= "llm_request"'
echo ""
echo "Expected output:"
echo "- Logs aggregated in Loki"
echo "- Queryable in Grafana Explore"
echo "- Structured JSON logs searchable"

# Troubleshooting Tips:
# - If logs not appearing: Check Promtail logs with 'docker logs promtail'
# - If connection errors: Verify Loki is accessible at http://localhost:3100
# - If parsing errors: Check log format matches Promtail configuration
```

---

## Summary

This practice guide covers:

1. **Prometheus Setup:** Configuration and deployment for metrics collection
2. **Grafana Dashboards:** Comprehensive monitoring visualization
3. **Custom Metrics:** Production-ready metrics collection system
4. **Alert Rules:** Complete alerting configuration for monitoring
5. **Log Aggregation:** Structured logging with Loki integration

**Expected Learning Outcomes:**
- Deploy and configure Prometheus for monitoring
- Create comprehensive Grafana dashboards
- Implement custom metrics collection
- Setup alerting for proactive monitoring
- Aggregate and query structured logs

**Last Updated:** 2026-02-05
**Status:** ✅ Complete
