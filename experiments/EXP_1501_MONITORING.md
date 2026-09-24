---
Document ID: EXP_1501
Title: "EXP_1501: Monitoring and Observability Experiments"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# EXP_1501: Monitoring and Observability Experiments

## Overview
Practical experiments for monitoring LLM infrastructure, model performance, and agent behavior on AI Engineering Curriculum.

## Experiment 1: Prometheus Metrics Collection

### Objective
Set up Prometheus to collect metrics from LLM inference, vector databases, and agents.

### Implementation
```python
# prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# Define metrics
inference_requests = Counter(
    'inference_requests_total',
    'Total inference requests',
    ['model', 'status']
)

inference_duration = Histogram(
    'inference_duration_seconds',
    'Inference duration',
    ['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

tokens_generated = Histogram(
    'tokens_generated_total',
    'Tokens generated per request',
    ['model'],
    buckets=[10, 50, 100, 500, 1000, 2000]
)

gpu_memory_usage = Gauge(
    'gpu_memory_usage_bytes',
    'GPU memory usage',
    ['gpu_id']
)

gpu_utilization = Gauge(
    'gpu_utilization_percent',
    'GPU utilization percentage',
    ['gpu_id']
)

vector_search_requests = Counter(
    'vector_search_requests_total',
    'Total vector search requests',
    ['database', 'status']
)

vector_search_duration = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration',
    ['database'],
    bins=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

agent_requests = Counter(
    'agent_requests_total',
    'Total agent requests',
    ['agent_type', 'status']
)

agent_duration = Histogram(
    'agent_duration_seconds',
    'Agent execution duration',
    ['agent_type'],
    buckets=[1, 5, 10, 30, 60, 120]
)

# Decorator for tracking inference
def track_inference(model_name: str):
    """Decorator to track inference metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                tokens = result.get('tokens', 0)
                if tokens:
                    tokens_generated.labels(model=model_name).observe(tokens)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                inference_requests.labels(model=model_name, status=status).inc()
                inference_duration.labels(model=model_name).observe(duration)

        return wrapper
    return decorator


# GPU monitoring
def monitor_gpu():
    """Monitor GPU metrics"""
    import pynvml

    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)

        # Memory usage
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_memory_usage.labels(gpu_id='0').set(mem_info.used)

        # Utilization
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_utilization.labels(gpu_id='0').set(util.gpu)

    except Exception as e:
        print(f"GPU monitoring error: {e}")


# Usage example
@track_inference(model_name="mistral-7b")
def run_inference(prompt: str):
    """Run inference with tracking"""
    # Simulate inference
    time.sleep(0.5)
    return {"tokens": 42}


def test_metrics():
    """Test metrics collection"""

    print("Testing Prometheus Metrics")
    print("="*60)

    # Start metrics server
    start_http_server(8000)
    print("Metrics server started on http://localhost:8000/metrics")

    # Simulate some requests
    for i in range(10):
        run_inference("Test prompt")

        # Monitor GPU
        monitor_gpu()

        time.sleep(0.1)

    print("\nMetrics collected. Check http://localhost:8000/metrics")


if __name__ == "__main__":
    test_metrics()
```

---

## Experiment 2: Grafana Dashboard Setup

### Objective
Create Grafana dashboards for LLM monitoring.

### Dashboard Configuration
```json
{
  "dashboard": {
    "title": "LLM Monitoring Dashboard",
    "panels": [
      {
        "title": "Inference Requests per Minute",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(inference_requests_total[1m])",
            "legendFormat": "{{model}} - {{status}}"
          }
        ]
      },
      {
        "title": "Inference Duration (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(inference_duration_seconds_bucket[5m]))",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "title": "Tokens per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(tokens_generated_total[1m])",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "title": "GPU Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "gpu_memory_usage_bytes / 1024^3",
            "legendFormat": "GPU {{gpu_id}} (GB)"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "type": "gauge",
        "targets": [
          {
            "expr": "gpu_utilization_percent",
            "legendFormat": "GPU {{gpu_id}}"
          }
        ]
      },
      {
        "title": "Vector Search Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(vector_search_duration_seconds_bucket[5m]))",
            "legendFormat": "{{database}}"
          }
        ]
      },
      {
        "title": "Agent Execution Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(agent_duration_seconds_sum[5m]) / rate(agent_duration_seconds_count[5m])",
            "legendFormat": "{{agent_type}}"
          }
        ]
      }
    ]
  }
}
```

---

## Experiment 3: Loki Log Aggregation

### Objective
Aggregate logs from LLM services using Loki.

### Log Configuration
```python
# logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

# Setup structured logging
def setup_logging(service_name: str):
    """Setup structured logging for Loki"""

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # JSON formatter for Loki
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        timestamp=True
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Usage in LLM service
class LLMService:
    """LLM service with structured logging"""

    def __init__(self):
        self.logger = setup_logging("llm-service")

    def generate(self, prompt: str, max_tokens: int = 100):
        """Generate with logging"""

        self.logger.info("generation_started",
                       prompt_length=len(prompt),
                       max_tokens=max_tokens)

        start = time.time()

        try:
            # Run inference
            result = self._generate(prompt, max_tokens)

            duration = time.time() - start

            self.logger.info("generation_completed",
                           tokens_generated=result['tokens'],
                           duration=duration,
                           tokens_per_second=result['tokens']/duration)

            return result

        except Exception as e:
            self.logger.error("generation_failed",
                            error=str(e),
                            error_type=type(e).__name__)
            raise


def test_logging():
    """Test logging"""

    print("Testing Structured Logging")
    print("="*60)

    service = LLMService()

    # Generate some logs
    for i in range(5):
        service.generate(f"Test prompt {i}")

    print("\nLogs generated. Check Loki for aggregation.")
```

### Promtail Configuration
```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: llm-service
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels:
          - __meta_docker_container_name
        target_label: container
      - source_labels:
          - __meta_docker_container_log_stream
        target_label: stream
```

---

## Experiment 4: Tempo Distributed Tracing

### Objective
Trace requests across LLM services, vector DB, and agents.

### Tracing Implementation
```python
# tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# Setup tracing
resource = Resource(attributes={
    SERVICE_NAME: "llm-service"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
trace_provider = trace.get_tracer_provider()

# Add Tempo exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://tempo:4317")
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

tracer = trace.get_tracer(__name__)


class TracedLLMService:
    """LLM service with tracing"""

    def __init__(self):
        self.client = None  # Your LLM client

    @tracer.start_as_current_span("llm.generate")
    def generate(self, prompt: str, max_tokens: int = 100):
        """Generate with tracing"""

        # Add attributes to span
        current_span = trace.get_current_span()
        current_span.set_attribute("prompt.length", len(prompt))
        current_span.set_attribute("max_tokens", max_tokens)

        with tracer.start_as_current_span("llm.model_inference"):
            # Run inference
            result = self._generate(prompt, max_tokens)

            current_span.set_attribute("tokens.generated", result['tokens'])

        return result

    def _generate(self, prompt: str, max_tokens: int):
        # Simulate inference
        time.sleep(0.5)
        return {"tokens": 42}


class TracedRAGService:
    """RAG service with tracing"""

    def __init__(self):
        self.vector_db = None
        self.llm = TracedLLMService()

    @tracer.start_as_current_span("rag.query")
    def query(self, query: str):
        """RAG query with tracing"""

        current_span = trace.get_current_span()
        current_span.set_attribute("query", query)

        with tracer.start_as_current_span("rag.vector_search"):
            # Vector search
            results = self._search(query)
            current_span.set_attribute("search.results", len(results))

        with tracer.start_as_current_span("rag.context_building"):
            # Build context
            context = "\n".join([r['text'] for r in results])

        with tracer.start_as_current_span("rag.generation"):
            # Generate response
            prompt = f"Context: {context}\n\nQuestion: {query}"
            result = self.llm.generate(prompt)

        return result

    def _search(self, query: str):
        # Simulate search
        time.sleep(0.1)
        return [{"text": "Result 1"}, {"text": "Result 2"}]


def test_tracing():
    """Test tracing"""

    print("Testing Distributed Tracing")
    print("="*60)

    rag = TracedRAGService()

    # Run traced query
    result = rag.query("What is AI?")

    print("\nTrace generated. Check Tempo UI at http://localhost:3200")


if __name__ == "__main__":
    test_tracing()
```

---

## Experiment 5: Custom Metrics for LLM Quality

### Objective
Track LLM output quality metrics.

### Quality Metrics
```python
# quality_metrics.py
from prometheus_client import Histogram, Gauge
import json

# Quality metrics
response_length = Histogram(
    'llm_response_length_chars',
    'Response length in characters',
    ['model']
)

response_diversity = Gauge(
    'llm_response_diversity',
    'Unique token ratio',
    ['model']
)

perplexity_score = Histogram(
    'llm_perplexity',
    'Model perplexity',
    ['model'],
    buckets=[1, 5, 10, 20, 50, 100]
)


class QualityMetrics:
    """Track LLM quality metrics"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def track_response(self, response: str):
        """Track response quality metrics"""

        # Response length
        response_length.labels(model=self.model_name).observe(len(response))

        # Diversity (unique tokens / total tokens)
        tokens = response.split()
        if tokens:
            diversity = len(set(tokens)) / len(tokens)
            response_diversity.labels(model=self.model_name).set(diversity)

    def track_perplexity(self, perplexity: float):
        """Track model perplexity"""

        perplexity_score.labels(model=self.model_name).observe(perplexity)


def test_quality_metrics():
    """Test quality metrics"""

    print("Testing Quality Metrics")
    print("="*60)

    quality = QualityMetrics("mistral-7b")

    # Simulate responses
    responses = [
        "This is a short response.",
        "This is a much longer response with more detail and information.",
        "Duplicate duplicate duplicate duplicate",
    ]

    for response in responses:
        quality.track_response(response)

    print("\nQuality metrics collected")
```

---

## Experiment 6: Alert Rules

### Objective
Set up alerting for LLM infrastructure issues.

### Alert Configuration
```yaml
# alerts.yml
groups:
  - name: llm_alerts
    interval: 30s
    rules:
      - alert: HighInferenceLatency
        expr: histogram_quantile(0.95, rate(inference_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High inference latency detected"
          description: "95th percentile latency is {{ $value }}s"

      - alert: HighGPUMemory
        expr: gpu_memory_usage_bytes / 1024^3 > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High GPU memory usage"
          description: "GPU memory usage is {{ $value }}GB"

      - alert: GPUOutOfMemory
        expr: gpu_memory_usage_bytes / 1024^3 > 11
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "GPU out of memory"
          description: "GPU memory usage is {{ $value }}GB"

      - alert: HighErrorRate
        expr: rate(inference_requests_total{status="error"}[5m]) / rate(inference_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: SlowVectorSearch
        expr: histogram_quantile(0.95, rate(vector_search_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow vector search"
          description: "95th percentile search latency is {{ $value }}s"

  - name: agent_alerts
    interval: 30s
    rules:
      - alert: AgentExecutionTimeout
        expr: agent_duration_seconds{agent_type="react"} > 120
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Agent execution timeout"
          description: "Agent {{ $labels.agent_type }} running for {{ $value }}s"

      - alert: AgentHighErrorRate
        expr: rate(agent_requests_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Agent high error rate"
          description: "Agent error rate is {{ $value | humanizePercentage }}"
```

---

## Experiment 7: Agent Performance Dashboard

### Objective
Monitor agent behavior and performance.

### Agent Metrics
```python
# agent_metrics.py
from prometheus_client import Counter, Histogram, Gauge
from typing import Dict, Any

# Agent-specific metrics
agent_tool_calls = Counter(
    'agent_tool_calls_total',
    'Total agent tool calls',
    ['agent_type', 'tool_name', 'status']
)

agent_reasoning_steps = Histogram(
    'agent_reasoning_steps_total',
    'Number of reasoning steps',
    ['agent_type'],
    buckets=[1, 2, 3, 5, 10, 20]
)

agent_memory_access = Counter(
    'agent_memory_access_total',
    'Agent memory accesses',
    ['agent_type', 'memory_type', 'status']
)


class InstrumentedAgent:
    """Agent with metrics instrumentation"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type

    def run(self, query: str):
        """Run agent with tracking"""

        steps = 0

        with agent_duration.labels(agent_type=self.agent_type).time():
            try:
                # Track reasoning steps
                while not self._is_done():
                    steps += 1
                    self._think()

                agent_requests.labels(
                    agent_type=self.agent_type,
                    status="success"
                ).inc()

                agent_reasoning_steps.labels(
                    agent_type=self.agent_type
                ).observe(steps)

            except Exception as e:
                agent_requests.labels(
                    agent_type=self.agent_type,
                    status="error"
                ).inc()
                raise

    def _think(self):
        """Simulate thinking"""
        time.sleep(0.1)

    def _is_done(self):
        """Check if done"""
        return False


def test_agent_metrics():
    """Test agent metrics"""

    print("Testing Agent Metrics")
    print("="*60)

    agent = InstrumentedAgent("react-agent")

    # Run agent
    agent.run("Test query")

    print("\nAgent metrics collected")
```

---

## Quick Start

### Deploy Monitoring Stack

```bash
# Start Prometheus, Grafana, Loki, Tempo using the compose definitions
# provided in the companion lesson:
# docs/phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md

# Access dashboards
# Grafana: http://192.168.1.100:3000
# Prometheus: http://192.168.1.100:9090
# Loki: http://192.168.1.100:3100
# Tempo: http://192.168.1.100:3200
```

### Run Metrics Server

```bash
# Start metrics server
python prometheus_metrics.py

# Check metrics
curl http://localhost:8000/metrics
```

---

## Expected Results

### Metrics Coverage

| Component | Metrics | Status |
|-----------|---------|--------|
| LLM Inference | Requests, duration, tokens, errors | ✅ |
| GPU | Memory, utilization, temperature | ✅ |
| Vector DB | Searches, latency, index size | ✅ |
| Agents | Requests, duration, tool calls, memory | ✅ |
| Quality | Response length, diversity, perplexity | ✅ |

### Dashboard Views

1. **LLM Performance**: Requests/sec, latency, throughput
2. **Resource Usage**: GPU memory, CPU, storage
3. **RAG Pipeline**: Search latency, retrieval accuracy
4. **Agent Behavior**: Tool usage, reasoning depth, success rate

---

## Experiment Checklist

- [ ] Prometheus metrics setup
- [ ] Grafana dashboard creation
- [ ] Loki log aggregation
- [ ] Tempo distributed tracing
- [ ] Custom quality metrics
- [ ] Alert rule configuration
- [ ] Agent instrumentation
- [ ] Performance baseline measurement
- [ ] Load testing with monitoring
- [ ] Alert testing and tuning

---

## Related Documentation
- [1501: Monitoring and Observability](../docs/phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
- [1402: vLLM and TGI](../docs/phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [6403: Qdrant Production Deployment](../docs/phases/phase6-rag/6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md)
- [7101: ReAct Loop System](../docs/phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
