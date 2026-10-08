---
Document ID: TUTORIAL-004
Title: "TUTORIAL-004: Monitoring & Observability for AI Systems"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 90 minutes
Prerequisites: [PHASE-1]
Tags: ['tutorial', 'monitoring', 'observability']
---

# TUTORIAL-004: Monitoring & Observability for AI Systems

**Prerequisites:** TUTORIAL-001 (Hello LLM), TUTORIAL-002 (Docker Essentials), LAB-001 (Docker & LLM)
**Time:** 90 minutes
**Difficulty:** ⭐⭐ Intermediate

---

## Tutorial Goals

After this tutorial, you will:

- ✅ Understand observability pillars (Metrics, Logs, Traces)
- ✅ Deploy Prometheus for metrics collection
- ✅ Set up Grafana for visualization
- ✅ Configure Loki for log aggregation
- ✅ Use Tempo for distributed tracing
- ✅ Monitor GPU and LLM performance

---

## Part 1: Understanding Observability (15 minutes)

### The Three Pillars

**1. Metrics (Prometheus)**

- Numerical measurements over time
- Examples: CPU usage, memory, request rate, GPU utilization
- Great for: Alerts, dashboards, trend analysis

**2. Logs (Loki)**

- Discrete events with timestamps
- Examples: Error messages, debug output, API calls
- Great for: Debugging, auditing, troubleshooting

**3. Traces (Tempo)**

- Request journey through distributed systems
- Examples: User request → API → LLM → Database → Response
- Great for: Performance analysis, bottleneck identification

### Why Observability Matters for AI

```python
# Without observability:
# "My model is slow" - but why?

# With observability:
# "Model latency: 2.5s"
# "GPU utilization: 45%" (not fully used!)
# "Token processing: 1800 tokens/s" (could be faster)
# → Solution: Increase batch size or enable KV cache optimization
```

---

## Part 2: Deploy Monitoring Stack (30 minutes)

### Task: Deploy Prometheus, Grafana, Loki, Tempo

```bash
# Create monitoring directory
mkdir ~/monitoring-tutorial
cd ~/monitoring-tutorial

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'

services:
  # Prometheus - Metrics Collection
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - monitoring

  # Grafana - Visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    restart: unless-stopped
    networks:
      - monitoring

  # Loki - Log Aggregation
  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    volumes:
      - ./loki/loki.yml:/etc/loki/local-config.yaml:ro
      - loki-data:/tmp/loki
    command: -config.file=/etc/loki/local-config.yaml
    restart: unless-stopped
    networks:
      - monitoring

  # Promtail - Log Collector
  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    volumes:
      - ./promtail/promtail.yml:/etc/promtail/config.yml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    restart: unless-stopped
    networks:
      - monitoring
    depends_on:
      - loki

  # Tempo - Distributed Tracing
  tempo:
    image: grafana/tempo:latest
    container_name: tempo
    ports:
      - "3200:3200"  # Tempo
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
    volumes:
      - ./tempo/tempo.yml:/etc/tempo.yaml:ro
      - tempo-data:/tmp/tempo
    command: -config.file=/etc/tempo.yaml
    restart: unless-stopped
    networks:
      - monitoring

  # Node Exporter - Host Metrics
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
    restart: unless-stopped
    networks:
      - monitoring

  # cAdvisor - Container Metrics
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    restart: unless-stopped
    networks:
      - monitoring

  # GPU Exporter - NVIDIA GPU Metrics
  gpu-exporter:
    image: mindprince/gpu_exporter:latest
    container_name: gpu-exporter
    ports:
      - "9445:9445"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
  loki-data:
  tempo-data:
EOF
```

### Create configuration files:

```bash
# Create directories
mkdir -p prometheus grafana/provisioning/{datasources,dashboards} loki promtail tempo

# Prometheus config
cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'gpu-exporter'
    static_configs:
      - targets: ['gpu-exporter:9445']
    scrape_interval: 5s

  - job_name: 'docker'
    static_configs:
      - targets: ['172.17.0.1:9323']
EOF

# Loki config
cat > loki/loki.yml << 'EOF'
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
    final_sleep: 0s
    chunk_idle_period: 5m
    chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: loki_index_
        period: 24h
      chunks:
        prefix: loki_chunk_
        period: 24h

storage_config:
  filesystem:
    directory: /tmp/loki

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

# Promtail config
cat > promtail/promtail.yml << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: container-logs
          __path__: /var/lib/docker/containers/*/*.log

  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: system-logs
          __path__: /var/log/*.log
EOF

# Tempo config
cat > tempo/tempo.yml << 'EOF'
server:
  http_listen_port: 3200

metrics_generator:
  processor:
    service_graphs:
      max_items: 10000
      expiry: 15m
  span_metrics:
    dimensions:
      - service_name
      - http.method
      - http.status_code
  local:
    span_metrics:
      endpoint: tempo:9009
    metrics:
      - name: search_calls_total
        type: histogram
      - name: search_duration_seconds
        type: histogram
      - name: search_failed_calls_total
        type: histogram

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo
EOF
```

### Start the monitoring stack:

```bash
# Build and start
docker compose up -d

# Check all services are running
docker compose ps

# Should see 8 services running
```

### Checkpoint: Part 2
**Verify:** All 8 services running, Prometheus at [http://localhost:9090](http://localhost:9090)

---

## Part 3: Configure Grafana Dashboards (20 minutes)

### Task: Set up datasources and dashboards

```bash
# Create Grafana datasource provisioning
cat > grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

cat > grafana/provisioning/datasources/loki.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
EOF

cat > grafana/provisioning/datasources/tempo.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: true
EOF

# Create dashboard provider
cat > grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
```

### Import dashboards:

```bash
# Create dashboards directory
mkdir -p grafana/dashboards

# Download system dashboard
curl -o grafana/dashboards/system-dashboard.json \
  https://grafana.com/api/dashboards/1860/revisions/1/download

# Download Docker dashboard
curl -o grafana/dashboards/docker-dashboard.json \
  https://grafana.com/api/dashboards/179/revisions/7/download
```

### Restart Grafana to load provisioning:

```bash
docker compose restart grafana
```

### Access Grafana:
- URL: [http://localhost:3000](http://localhost:3000)
- Username: admin
- Password: admin

### Checkpoint: Part 3
**Verify:** Grafana accessible, datasources connected, dashboards loaded

---

## Part 4: Monitor GPU Performance (15 minutes)

### Task: Set up GPU monitoring

```bash
# Check GPU exporter is working
curl http://localhost:9445/metrics

# You should see GPU metrics:
# nvidia_gpu_memory_used_bytes
# nvidia_gpu_utilization
# nvidia_gpu_power_usage
# nvidia_gpu_temperature_celsius
```

### Query GPU metrics in Prometheus:

```promql
# Open http://localhost:9090

# Try these queries:

# GPU utilization percentage
rate(nvidia_gpu_utilization_gpu0[5m]) * 100

# GPU memory in GB
nvidia_gpu_memory_used_bytes{gpu="0"} / 1024 / 1024 / 1024

# GPU temperature
nvidia_gpu_temperature_celsius_gpu{gpu="0"}

# GPU power usage (Watts)
nvidia_gpu_power_usage_milliwatts{gpu="0"} / 1000
```

### Create GPU dashboard in Grafana:

1. Open Grafana: [http://localhost:3000](http://localhost:3000)
2. Click "+" → "New Dashboard"
3. Add panels with these queries:

**Panel 1: GPU Utilization**
```text
Query: rate(nvidia_gpu_utilization_gpu0[5m]) * 100
Type: Time series
Title: GPU Utilization %
Unit: Percent (0-100)
```

**Panel 2: GPU Memory**
```text
Query: nvidia_gpu_memory_used_bytes{gpu="0"} / 1024 / 1024 / 1024
Type: Time series
Title: GPU Memory (GB)
Unit: Data (IEC)
```

**Panel 3: GPU Temperature**
```text
Query: nvidia_gpu_temperature_celsius_gpu{gpu="0"}
Type: Stat
Title: Current Temperature
Unit: Celsius
```

### Checkpoint: Part 4
**Verify:** GPU metrics visible in Grafana

---

## Part 5: Monitor LLM Applications (10 minutes)

### Task: Add tracing to LLM service

```python
# ~/monitoring-tutorial/example_llm_with_tracing.py
import asyncio
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry import metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
import time
import requests

app = FastAPI(title="Monitored LLM API")

# Setup tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True
)

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Setup metrics
meter_provider = MeterProvider()
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="localhost:4317", insecure=True)
)
meter_provider.add_metric_reader(metric_reader)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Create metrics
request_counter = meter.create_counter(
    "llm_requests_total",
    description="Total number of LLM requests"
)

request_duration = meter.create_histogram(
    "llm_request_duration_seconds",
    description="LLM request duration"
)

@app.post("/generate")
async def generate_text(prompt: str):
    """Generate text with tracing"""

    # Create a span for tracing
    with tracer.start_as_current_span("generate_text") as span:
        span.set_attribute("prompt.length", len(prompt))
        span.set_attribute("model", "mistral")

        start_time = time.time()

        # Call Ollama
        try:
            with tracer.start_as_current_span("ollama_request"):
                response = await asyncio.to_thread(requests.post,
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "mistral",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=120
                )
                response.raise_for_status()

                result = response.json().get("response", "")
                span.set_attribute("response.length", len(result))
                span.set_attribute("status", "success")

        except Exception as e:
            span.set_attribute("status", "error")
            span.set_attribute("error.message", str(e))
            raise

        duration = time.time() - start_time

        # Record metrics
        request_counter.add(1, {"model": "mistral"})
        request_duration.record(duration, {"model": "mistral"})

        span.set_attribute("duration", duration)

        return {"response": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Test the monitored service:

```bash
# Install dependencies
uv pip install fastapi uvicorn opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi requests

# Run the service
python example_llm_with_tracing.py

# In another terminal, make requests
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
```

### View traces in Grafana:

1. Open Grafana: [http://localhost:3000](http://localhost:3000)
2. Go to "Explore" → "Tempo"
3. You should see traces for your requests
4. Click on a trace to see the timeline:
   - generate_text (parent span)
   - ollama_request (child span)

### Checkpoint: Part 5
**Verify:** Traces visible in Tempo

---

## Summary

### What You Learned

| Component | Purpose | Access |
|-----------|---------|--------|
| **Prometheus** | Metrics collection | [http://localhost:9090](http://localhost:9090) |
| **Grafana** | Visualization | [http://localhost:3000](http://localhost:3000) |
| **Loki** | Log aggregation | [http://localhost:3100](http://localhost:3100) |
| **Tempo** | Distributed tracing | [http://localhost:3200](http://localhost:3200) |
| **Node Exporter** | Host metrics | [http://localhost:9100/metrics](http://localhost:9100/metrics) |
| **cAdvisor** | Container metrics | [http://localhost:8080/metrics](http://localhost:8080/metrics) |
| **GPU Exporter** | GPU metrics | [http://localhost:9445/metrics](http://localhost:9445/metrics) |

### Key Takeaways

1. **Metrics** tell you WHAT happened (CPU 80%, memory 4GB)
2. **Logs** tell you WHY it happened (Error: Out of memory)
3. **Traces** tell you WHERE it happened (Service A → Service B → Database)
4. **Together** they give complete observability

### Quick Commands

```bash
# View logs
docker compose logs -f prometheus

# Check metrics
curl http://localhost:9445/metrics | grep gpu

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=up'

# Stop everything
docker compose down
```

---

## Next Steps

- **[1501: Monitoring Stack](../../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)** - Deep dive into monitoring
- **[LAB-001: Docker & LLM](../labs/LAB-001-Docker-LLM.md)** - Add monitoring to LLM apps
- **[TUTORIAL-005: Production Deployment](TUTORIAL-005-Production-Deployment.md)** - Deploy to production

---

**You're now monitoring-ready!** 📊
