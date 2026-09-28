---
Document ID: 1501
Title: Monitoring and Observability
Phase: 1
Module: 1500
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'monitoring', 'observability', 'prometheus']
---

# 1501: Monitoring and Observability

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Architecture](#architecture)
- [Component 1: Prometheus (Metrics Collection)](#component-1-prometheus-metrics-collection)
- [Component 2: Grafana (Dashboards)](#component-2-grafana-dashboards)
- [Component 3: Loki (Log Aggregation)](#component-3-loki-log-aggregation)
- [Component 4: Tempo (Tracing)](#component-4-tempo-tracing)
- [Component 5: Custom Exporters](#component-5-custom-exporters)
- [K3s Monitoring Stack](#k3s-monitoring-stack)
- [Alert Rules](#alert-rules)
- [Quick Start](#quick-start)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Map the monitoring stack (Prometheus, Grafana, Loki, Tempo, exporters, K3s) and route each signal type to its store
- Configure Prometheus scrape jobs, alert rules, and the Alertmanager integration from the compose deployment
- Build Grafana panels from vLLM rate and histogram series and explain Qdrant's gauge-only /metrics limits
- Ship container logs through Promtail's docker_sd pipeline and query them in Loki
- Emit OTLP agent spans to Tempo from Python and instrument a custom prometheus_client exporter
- Fire the HighErrorRate, AgentDown, QdrantDeadReplicas, and GPUOutOfMemory rules and verify each alert end to end

---

## Abstract
Complete monitoring stack for tracking infrastructure health, model performance, and agent behavior in a home lab.

## Architecture

```text
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
│  - Ollama (metrics via exporter)          │              │      │
│  - vLLM (metrics)                        │              │      │
│  - Agents (traces)                       │              │      │
│  - K3s cluster (metrics)                  │              │      │
└─────────────────────────────────────────────────────────────────┘
```

## Component 1: Prometheus (Metrics Collection)

### Docker Compose Setup

```yaml
# Merge into docker-compose.yml. The shared network is declared once at
# the top level: networks: { project-omega-net: {} }
services:
  prometheus:
    image: prom/prometheus:v3.15.0   # pinned release (Sep 2026); check releases for newer
    container_name: project-omega-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
      - ./monitoring/prometheus/data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    # Needed to scrape the agent exporter running on the host (Component 5).
    # Inside a container, localhost is the container itself.
    extra_hosts:
      - 'host.docker.internal:host-gateway'
    restart: unless-stopped
    networks:
      - project-omega-net

  alertmanager:
    image: prom/alertmanager:v0.34.1   # pinned release (Sep 2026); check releases for newer
    container_name: project-omega-alertmanager
    ports:
      - "9093:9093"
    # The image ships a usable default /etc/alertmanager/alertmanager.yml,
    # so no config mount is required to receive alerts.
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
    cluster: 'PROJECT-OMEGA'
    env: 'lab'

# Load the alert rules (evaluated every evaluation_interval)
rule_files:
  - /etc/prometheus/alerts.yml

# Alerting
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Scrape configs (/metrics is the default metrics_path)
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Qdrant metrics (served on the REST port, enabled by default)
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']

  # Neo4j metrics are disabled by default. Enable them in neo4j.conf:
  #   server.metrics.prometheus.enabled=true
  #   server.metrics.prometheus.endpoint=0.0.0.0:2004
  # (the default endpoint binds localhost only, which the Prometheus
  # container cannot reach)
  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:2004']

  # Ollama has NO native /metrics endpoint (open feature request,
  # ollama/ollama#3144). Monitor inference through the GPU metrics (dcgm
  # job below), or deploy a community exporter such as
  # NorskHelsenett/ollama-metrics and scrape it here.
  # - job_name: 'ollama'
  #   static_configs:
  #     - targets: ['ollama-exporter:<port>']

  # Node exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['192.168.1.100:9100', '192.168.1.101:9100']

  # dcgm-exporter (GPU metrics) on the GPU host, next to node-exporter
  - job_name: 'dcgm'
    static_configs:
      - targets: ['192.168.1.100:9400']

  # cAdvisor (container metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # Agent metrics from the custom exporter (Component 5) running on the
  # host, reachable through the host gateway mapped in the compose file
  - job_name: 'agents'
    static_configs:
      - targets: ['host.docker.internal:8000']

  # NOTE: this docker stack does NOT scrape the K3s cluster —
  # kubernetes_sd_configs discovers cluster-internal IPs that the docker
  # bridge cannot reach. Run kube-prometheus-stack inside the cluster
  # instead (see K3s Monitoring Stack below).
```

## Component 2: Grafana (Dashboards)

### Setup

```yaml
services:
  grafana:
    image: grafana/grafana:13.2.2   # pinned release (Sep 2026); check releases for newer
    container_name: project-omega-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=your_secure_password
      # No GF_INSTALL_PLUGINS needed — the old grafana-piechart-panel and
      # grafana-worldmap-panel plugins are deprecated; Pie chart and Geomap
      # are built-in core panels since Grafana 8/9
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
        "title": "Generated Tokens per Second",
        "targets": [
          {
            "expr": "sum(rate(vllm:generation_tokens_total[1m]))"
          }
        ]
      },
      {
        "title": "Request Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(vllm:e2e_request_latency_seconds_bucket[5m])) by (le))"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "targets": [
          {
            "expr": "DCGM_FI_DEV_GPU_UTIL"
          }
        ]
      }
    ]
  }
}
```

### Dashboard: Vector Database

Qdrant's built-in `/metrics` endpoint exposes **gauges only** — collection and
vector counts, memory usage, and cluster health. It publishes no per-request
counters or latency histograms, so there is no QPS or p95 panel to build from
it; query-level latency belongs in the application's own instrumentation.

```json
{
  "dashboard": {
    "title": "Qdrant State",
    "panels": [
      {
        "title": "Collections",
        "targets": [
          {
            "expr": "collections_total"
          }
        ]
      },
      {
        "title": "Vectors Stored",
        "targets": [
          {
            "expr": "collections_vector_total"
          }
        ]
      },
      {
        "title": "Resident Memory",
        "targets": [
          {
            "expr": "memory_resident_bytes"
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
    image: grafana/loki:2.9.8   # pin the LTS; 3.x changed config defaults
    container_name: project-omega-loki
    ports:
      - "3100:3100"
    volumes:
      # Mount the config as a single file — a directory mount over /etc/loki
      # hides the image's default local-config.yaml and Loki aborts on startup
      - ./monitoring/loki/local-config.yaml:/etc/loki/local-config.yaml:ro
      - ./monitoring/loki/data:/loki
    networks:
      - project-omega-net

  promtail:
    image: grafana/promtail:2.9.8   # match the Loki LTS; Promtail is in LTS maintenance — new deployments use Grafana Alloy
    container_name: project-omega-promtail
    volumes:
      - /var/log:/var/log:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro   # docker_sd needs it
      - ./monitoring/promtail/config.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - project-omega-net
```

### Loki Config

This is the image's shipped default `local-config.yaml`, copied into the repo
with one deliberate fix: the default `ruler.alertmanager_url` points at
`localhost:9093`, and inside the container localhost is the container itself —
the compose service name is what actually routes the ruler's alerts.

```yaml
# monitoring/loki/local-config.yaml — the grafana/loki:2.9.8 default,
# with the ruler's alertmanager_url pointed at the compose service name
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://alertmanager:9093

analytics:
  reporting_enabled: false
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
    image: grafana/tempo:3.0.3   # pinned release (Aug 2026); check releases for newer
    container_name: project-omega-tempo
    ports:
      - "3200:3200"  # HTTP API + TraceQL UI
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
    # The legacy -storage.trace.* flags no longer configure Tempo; point it
    # at a config file instead
    command: "-target=all -config.file=/etc/tempo/tempo.yaml"
    volumes:
      - ./monitoring/tempo/tempo.yaml:/etc/tempo/tempo.yaml:ro
      - ./monitoring/tempo/data:/var/tempo
    networks:
      - project-omega-net
```

The receiver endpoints in Tempo's defaults bind to localhost, and inside the
container localhost is the container itself — bind `0.0.0.0` or no other
container can reach the OTLP ports:

```yaml
# monitoring/tempo/tempo.yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
        http:
          endpoint: "0.0.0.0:4318"

storage:
  trace:
    backend: local
    wal:
      path: /var/tempo/wal
    local:
      path: /var/tempo/blocks

usage_report:
  reporting_enabled: false
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
import time

from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics — pass Counter names WITHOUT the _total suffix; the client library
# strips it if given and appends it automatically when the series is exposed
agent_requests = Counter('agent_requests', 'Total agent requests', ['agent_type'])
agent_duration = Histogram('agent_duration_seconds', 'Agent execution duration')
agent_errors = Counter('agent_errors', 'Agent errors', ['error_type'])
active_agents = Gauge('active_agents', 'Currently active agents')

# Instrument agent
class InstrumentedAgent:
    def __init__(self, agent_type):
        self.agent_type = agent_type

    def _execute(self, query):
        # Replace with your agent loop (tool calls, LLM requests, ...)
        return f"stub result for: {query}"

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

# Run the exporter
if __name__ == "__main__":
    # start_http_server serves /metrics on port 8000 in a daemon thread
    start_http_server(8000)
    # One warmup run so the series exist before the first scrape
    InstrumentedAgent("react").run("warmup query")
    # Keep the process alive — only the metrics server runs in a thread
    while True:
        time.sleep(60)
```

### GPU Metrics Exporter

GPU metrics come from NVIDIA's [dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter).
It listens on `:9400` by default and publishes one series per counter from its
default counter set — including `DCGM_FI_DEV_GPU_UTIL` (GPU utilization),
`DCGM_FI_DEV_FB_USED` and `DCGM_FI_DEV_FB_FREE` (framebuffer memory):

```bash
docker run -d --restart unless-stopped \
  --gpus all --cap-add SYS_ADMIN \
  -p 9400:9400 \
  nvcr.io/nvidia/k8s/dcgm-exporter:4.6.1-4.8.4-distroless   # pinned chart-default tag (exporter-dcgm-distroless format); check NGC for newer
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
# monitoring/prometheus/alerts.yml — mounted into the prometheus container
# and loaded via rule_files in prometheus.yml
groups:
  - name: agent_alerts
    interval: 30s
    rules:
      # agent_errors_total — the exposed series name (the client appends _total)
      - alert: HighErrorRate
        expr: sum(rate(agent_errors_total[5m])) > 0.1
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
      # Qdrant /metrics publishes no latency histograms; alert on replica health
      - alert: QdrantDeadReplicas
        expr: collection_dead_replicas > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Qdrant collection has dead replicas"

  - name: gpu_alerts
    interval: 15s
    rules:
      - alert: GPUOutOfMemory
        expr: DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE) > 0.95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU framebuffer memory is running out"
```

## Quick Start

```bash
# From the repo root, after merging the services and configs above
docker compose up -d

# Access dashboards
# Grafana:            http://192.168.1.100:3000
# Prometheus:         http://192.168.1.100:9090
# Alertmanager:       http://192.168.1.100:9093
# Tempo (TraceQL UI): http://192.168.1.100:3200
# Loki:               http://192.168.1.100:3100
```

---

## References

### Related PROJECT-OMEGA Documents

- [1502: Model Drift Detection](1502-Model-Drift-Detection.md)
- [1503: LLM Observability](1503-LLM-Observability.md)

### External References

- [Prometheus configuration reference](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Loki 2.9 documentation](https://grafana.com/docs/loki/v2.9.x/)
- [Tempo documentation](https://grafana.com/docs/tempo/latest/)
- [dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter)
- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Ollama metrics feature request](https://github.com/ollama/ollama/issues/3144)
- [Qdrant monitoring guide](https://qdrant.tech/documentation/guides/monitoring/)

---

## Next Steps

- Continue with: **[1502: Model Drift Detection](./1502-Model-Drift-Detection.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [1102: Network Topology Design](../1100-network/1102-Star-Topology-Core.md)
- [1301: K3s Architecture](../1300-kubernetes/1301-K3s-Master-Worker-Arch.md)
- [1402: vLLM and TGI](../1400-llmops/1402-vLLM-and-TGI.md)
