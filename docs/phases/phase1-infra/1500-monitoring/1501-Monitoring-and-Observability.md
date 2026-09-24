---
Document ID: 1501
Title: Monitoring and Observability for PROJECT-OMEGA
Phase: 1
Module: 1500
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'monitoring', 'observability', 'prometheus']
---

# 1501: Monitoring and Observability for PROJECT-OMEGA

## Abstract
Complete monitoring stack for tracking infrastructure health, model performance, and agent behavior on PROJECT-OMEGA HomeLab.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Grafana     │◄───│   Prometheus  │◄───│   Exporters  │      │
│  │  (Dashboards)│    │   (Metrics)   │    │              │      │
│  └──────────────┘    └──────────────┘    │              │      │
│         │                  │              │              │      │
│         ▼                  ▼              │              │      │
│  ┌──────────────┐    ┌──────────────┐    │  ┌──────────┐ │      │
│  │   Loki       │    │   Tempo      │    │  │ cAdvisor │ │      │
│  │  (Logs)      │    │  (Traces)     │    │  │ (Docker) │ │      │
│  └──────────────┘    └──────────────┘    │  └──────────┘ │      │
│                                          │              │      │
│  Sources:                                 │              │      │
│  - Qdrant (metrics)                      │              │      │
│  - Neo4j (metrics)                       │              │      │
│  - Ollama (metrics)                      │              │      │
│  - vLLM (metrics)                        │              │      │
│  - Agents (traces)                       │              │      │
│  - K3s cluster (metrics)                  │              │      │
└─────────────────────────────────────────────────────────────────┘
```

## Component 1: Prometheus (Metrics Collection)

### Docker Compose Setup

```yaml
# Add to docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: project-omega-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - project-omega-net
```

### Configuration

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'project-omega'
    env: 'homelab'

# Alerting
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Scrape configs
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Qdrant metrics
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    metrics_path: /metrics

  # Neo4j metrics
  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:2004']
    metrics_path: /metrics

  # Ollama metrics
  - job_name: 'ollama'
    static_configs:
      - targets: ['ollama:11434']
    metrics_path: /metrics

  # Node exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['192.168.1.100:9100', '192.168.1.101:9100']

  # cAdvisor (container metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # K3s cluster
  - job_name: 'k3s'
    kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
            - project-omega
```

## Component 2: Grafana (Dashboards)

### Setup

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    container_name: project-omega-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=your_secure_password
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel
    volumes:
      - ./monitoring/grafana/data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    restart: unless-stopped
    networks:
      - project-omega-net
```

### Dashboard: Model Inference

```json
{
  "dashboard": {
    "title": "Model Inference Metrics",
    "panels": [
      {
        "title": "Tokens per Second",
        "targets": [
          {
            "expr": "rate(vllm_requests_total[1m])"
          }
        ]
      },
      {
        "title": "Request Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(vllm_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "targets": [
          {
            "expr": "nvidia_gpu_utilization"
          }
        ]
      }
    ]
  }
}
```

### Dashboard: Vector Database

```json
{
  "dashboard": {
    "title": "Qdrant Performance",
    "panels": [
      {
        "title": "Search QPS",
        "targets": [
          {
            "expr": "rate(qdrant_search_requests_total[1m])"
          }
        ]
      },
      {
        "title": "Search Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(qdrant_search_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Vector Count",
        "targets": [
          {
            "expr": "qdrant_vectors_total"
          }
        ]
      }
    ]
  }
}
```

## Component 3: Loki (Log Aggregation)

### Setup

```yaml
services:
  loki:
    image: grafana/loki:latest
    container_name: project-omega-loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - ./monitoring/loki:/etc/loki
    networks:
      - project-omega-net

  promtail:
    image: grafana/promtail:latest
    container_name: project-omega-promtail
    volumes:
      - /var/log:/var/log:ro
      - ./monitoring/promtail/config.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - project-omega-net
```

### Promtail Config

```yaml
# monitoring/promtail/config.yml
server:
  http_listen_port: 9080

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels:
          - __meta_docker_container_name
        target_label: container
```

## Component 4: Tempo (Tracing)

### Setup for Agent Tracing

```yaml
services:
  tempo:
    image: grafana/tempo:latest
    container_name: project-omega-tempo
    ports:
      - "3200:3200"  # Jaeger UI
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
    command:
      - "-storage.trace.backend=local"
      - "-storage.trace.local.path=/tmp"
      - "-auth.enabled=false"
    volumes:
      - ./monitoring/tempo/data:/tmp
    networks:
      - project-omega-net
```

### OpenTelemetry for Python Agents

```python
# agent_tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# Setup tracing
resource = Resource(attributes={
    SERVICE_NAME: "react-agent"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://tempo:4317"))
)

tracer = trace.get_tracer(__name__)

# Use in agent
def run_agent_with_tracing():
    with tracer.start_as_current_span("agent_execution") as span:
        span.set_attribute("query", "What is AI?")

        with tracer.start_as_current_span("tool_search"):
            # Execute search
            pass

        with tracer.start_as_current_span("llm_generation"):
            # Generate response
            span.set_attribute("tokens", 150)
```

## Component 5: Custom Exporters

### Agent Metrics Exporter

```python
# agent_exporter.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
agent_requests = Counter('agent_requests_total', 'Total agent requests', ['agent_type'])
agent_duration = Histogram('agent_duration_seconds', 'Agent execution duration')
agent_errors = Counter('agent_errors_total', 'Agent errors', ['error_type'])
active_agents = Gauge('active_agents', 'Currently active agents')

# Instrument agent
class InstrumentedAgent:
    def __init__(self, agent_type):
        self.agent_type = agent_type

    def run(self, query):
        active_agents.inc()
        agent_requests.labels(agent_type=self.agent_type).inc()

        with agent_duration.time():
            try:
                result = self._execute(query)
                return result
            except Exception as e:
                agent_errors.labels(error_type=type(e).__name__).inc()
                raise
            finally:
                active_agents.dec()

# Start exporter
if __name__ == "__main__":
    start_http_server(8000)
```

## K3s Monitoring Stack

### Helm Charts

```bash
# Add Prometheus community charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/k3s-prometheus-values.yaml
```

### Values Configuration

```yaml
# monitoring/k3s-prometheus-values.yaml
grafana:
  enabled: true
  ingress:
    enabled: true
    hosts: ["grafana.project-omega.local"]

prometheus:
  prometheusSpec:
    retention: 15d
    resources:
      requests:
        memory: "512Mi"
        cpu: "100m"
      limits:
        memory: "2Gi"
        cpu: "1000m"

alertmanager:
  enabled: true

nodeExporter:
  enabled: true

kubeStateMetrics:
  enabled: true
```

## Alert Rules

### Prometheus Alerts

```yaml
# monitoring/alerts.yml
groups:
  - name: agent_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(agent_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in agents"

      - alert: AgentDown
        expr: up{job="agents"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Agent instance is down"

  - name: vector_db_alerts
    interval: 30s
    rules:
      - alert: SlowSearch
        expr: histogram_quantile(0.95, rate(qdrant_search_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Vector search is slow"

  - name: gpu_alerts
    interval: 15s
    rules:
      - alert: GPUOutOfMemory
        expr: nvidia_gpu_memory_utilization > 0.95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU is running out of memory"
```

## Quick Start

```bash
# Clone configs
git clone https://github.com/project-omega/monitoring.git
cd monitoring

# Deploy all services
docker-compose up -d

# Access dashboards
# Grafana: http://192.168.1.100:3000
# Prometheus: http://192.168.1.100:9090
# Tempo: http://192.168.1.100:3200
# Loki: http://192.168.1.100:3100
```

---

## Next Steps

- Continue with: **[1502: Model Drift Detection](./1502-Model-Drift-Detection.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [1102: Star Topology Core](../1100-network/1102-Star-Topology-Core.md)
- [1301: K3s Architecture](../1300-kubernetes/1301-K3s-Master-Worker-Arch.md)
- [1402: vLLM and TGI](../1400-llmops/1402-vLLM-and-TGI.md)
