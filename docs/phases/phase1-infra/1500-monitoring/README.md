---
Document ID: 1500-MONITORING-README
Title: "1500: Monitoring and Observability for LLM Systems"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Beginner
---

# 1500: Monitoring and Observability for LLM Systems

## Module Overview

This module covers monitoring and observability practices specifically for LLM systems, including model performance tracking, drift detection, resource monitoring, and debugging. You'll learn how to set up comprehensive monitoring stacks for production LLM deployments.

## Why Monitoring Matters for LLMs

### 1. Performance Tracking: Ensure Models Meet SLA Requirements

**SLA Example:**
```text
Service Level Agreement:
- Response time (p50): <100ms
- Response time (p95): <300ms
- Response time (p99): <1000ms
- Throughput: >100 tokens/sec
- Uptime: >99.9%

Without monitoring:
├── Don't know if we're meeting SLA ❌
├── Users complain before we know there's a problem ❌
└── Can't prove SLA compliance ❌

With monitoring:
├── Real-time SLA tracking ✅
├── Alerts before users notice ✅
└── SLA reports for management ✅
```

**Real-World Example:**
```yaml
Scenario: Gradual performance degradation

Without monitoring:
  Week 1: Latency p95: 100ms ✅
  Week 2: Latency p95: 150ms (unnoticed)
  Week 3: Latency p95: 300ms (still unnoticed)
  Week 4: Latency p95: 500ms (users start complaining)
  Week 5: Emergency debugging, root cause found
  Result: 1 month of poor performance, lost users ❌

With monitoring:
  Week 1: Latency p95: 100ms ✅
  Week 2: Latency p95: 150ms, alert fires
  Action: Investigated, found database query slowing down
  Fix: Added index, back to 100ms
  Result: 1 day of degraded performance ✅
```

### 2. Drift Detection: Catch Model Degradation Early

**Types of Drift:**

| Drift Type | Description | Example |
|------------|-------------|---------|
| **Data Drift** | Input distribution changes | Users start asking questions in a new domain |
| **Concept Drift** | Relationship between input/output changes | Model's knowledge becomes outdated |
| **Performance Drift** | Model quality degrades | Accuracy drops from 95% to 80% |

**Detection Example:**
```text
# Monitor input distribution over time
metrics.track("prompt_length", len(prompt))
metrics.track("prompt_language", detect_language(prompt))
metrics.track("user_intent", classify_intent(prompt))

# Alert on drift
if prompt_length_distribution_changed():
    alert("Data drift detected!")

if accuracy_degraded(10%):
    alert("Model performance degraded!")
```

### 3. Resource Optimization: Monitor GPU/CPU/Memory

**Why Monitor Resources:**
```text
Scenario: Underutilized GPUs

Without monitoring:
├── 8 GPUs deployed ✅
├── Actual usage: 20% ❌
├── Cost: $10,000/month ❌
└── Waste: $8,000/month ❌

With monitoring:
├── 8 GPUs deployed ✅
├── Monitoring shows: 20% usage ✅
├── Action: Scale down to 2 GPUs ✅
├── New cost: $2,500/month ✅
└── Savings: $7,500/month (75%)! ✅
```

**Key Metrics to Track:**
```yaml
GPU Metrics:
  - Utilization (%)
  - Memory used/total
  - Temperature
  - Power consumption
  - SM (streaming multiprocessor) efficiency

CPU Metrics:
  - Utilization (%)
  - Load average
  - Context switches

Memory Metrics:
  - RAM used/total
  - Swap usage
  - Cache vs working set

Network Metrics:
  - Bandwidth (tx/rx)
  - Packet loss
  - Latency
```

### 4. Debugging: Identify and Resolve Production Issues

**Debugging Scenario:**
```text
User Report: "Responses are slow"

Without monitoring:
├── SSH into server
├── Run top, htop, nvidia-smi
├── Everything looks normal
├── Can't reproduce issue
├── Give up
└── User frustrated ❌

With monitoring:
├── Check Grafana dashboard
├── See spike in p99 latency at 2:00 AM
├── Correlated with: GPU memory at 95%
├── Root cause: Backup job running at 2 AM
├── Fix: Move backup to 4 AM
└── Issue resolved ✅
```

## The Three Pillars of Observability

```text
┌─────────────────────────────────────────────────────────────┐
│                   OBSERVABILITY STACK                        │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │     METRICS      │  │      LOGS        │  │  TRACES    │ │
│  │  (What happened) │  │ (Why it happened)│  │ (Where)    │ │
│  │                  │  │                  │  │            │ │
│  │ • Prometheus     │  │ • Loki/Elastic   │  │ • Jaeger   │ │
│  │ • Grafana        │  │ • Fluent Bit     │  │ • Tempo    │ │
│  │ • DCGM Exporter  │  │ • Vector         │  │ • Zipkin   │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              VISUALIZATION & ALERTING                 │   │
│  │  • Grafana Dashboards  • PagerDuty/Slack Alerts      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Pillar 1: Metrics

**What are Metrics?**
- Time-series data (timestamp + value)
- Numerical measurements
- Aggregatable (sum, avg, max, min)

**LLM-Specific Metrics:**

| Category | Metric | Why Important |
|----------|--------|---------------|
| **Performance** | Request latency (p50, p95, p99) | User experience |
| **Performance** | Tokens per second | Throughput |
| **Performance** | Queue depth | Capacity planning |
| **Quality** | Response rating (user feedback) | Model quality |
| **Quality** | Error rate | Reliability |
| **Resources** | GPU utilization | Cost optimization |
| **Resources** | GPU memory used | Capacity planning |
| **Business** | Requests per user | Usage patterns |
| **Business** | Model usage by feature | Product insights |

### Pillar 2: Logs

**What are Logs?**
- Discrete events
- Text-based records
- Contextual information

**LLM-Specific Logs:**

Request log:
```json
{
  "timestamp": "2026-02-04T10:30:00Z",
  "level": "info",
  "request_id": "req-abc123",
  "user_id": "user-456",
  "model": "llama-3-70b",
  "prompt": "What is machine learning?",
  "prompt_tokens": 7,
  "completion": "Machine learning is...",
  "completion_tokens": 150,
  "total_tokens": 157,
  "latency_ms": 350,
  "gpu_used": "gpu-0",
  "temperature": 0.7
}
```

Error log:
```json
{
  "timestamp": "2026-02-04T10:31:00Z",
  "level": "error",
  "request_id": "req-def456",
  "error": "CUDA out of memory",
  "gpu_memory_used": "79GB",
  "gpu_memory_total": "80GB",
  "model": "llama-3-70b",
  "stack_trace": "..."
}
```

### Pillar 3: Traces

**What are Traces?**
- Request journey through system
- Parent-child relationships
- Distributed context

**LLM Request Trace:**
```text
Request: "What is machine learning?"

Trace:
├── API Gateway (5ms)
│   └── → Rate limiting check
│
├── Load Balancer (2ms)
│   └── → Route to vLLM-1
│
├── vLLM Server (300ms)
│   ├── Tokenization (10ms)
│   ├── Model forward pass (250ms)
│   │   └── GPU: 98% utilization
│   └── Detokenization (5ms)
│
└── Response formatting (10ms)

Total: 317ms
Bottleneck: Model forward pass (250ms)
```

## LLM Monitoring Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        LLM Application                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  API → Model → Response                               │    │
│  │  ↓         ↓         ↓                                │    │
│  │ emit_metrics() emit_logs() emit_trace()               │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────┬─────────────────────────────────┬────────────────┘
             │                                 │
┌────────────▼─────────┐           ┌──────────▼────────────────┐
│   Prometheus         │           │      Loki                 │
│   (Metrics Store)     │           │      (Log Store)          │
│  ┌─────────────────┐ │           │  ┌────────────────────┐  │
│  │ Time Series DB  │ │           │  │ Log Aggregation    │  │
│  │ PromQL Queries  │ │           │  │ Full-text Search   │  │
│  └─────────────────┘ │           │  └────────────────────┘  │
└────────────┬─────────┘           └──────────┬────────────────┘
             │                                 │
             └────────────┬────────────────────┘
                          │
                  ┌───────▼────────┐
                  │    Grafana     │
                  │  Dashboards    │
                  │   + Alerts     │
                  └────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    GPU Monitoring Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ DCGM     │  │Node      │  │cAdvisor  │  │Custom    │   │
│  │Exporter  │  │Exporter  │  │          │  │Exporter  │   │
│  │(GPU)     │  │(System)  │  │(Containers)│  │(LLM)     │   │
│  └─────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
│        │            │            │            │            │
│        └────────────┴────────────┴────────────┴──────────┘ │
│                              │                               │
│                         ┌─────▼─────┐                        │
│                         │Prometheus │                        │
│                         │Scrape     │                        │
│                         └───────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start Guide

### Step 1: Install Monitoring Stack

**Docker Compose Setup:**
```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

volumes:
  prometheus-data:
  grafana-data:
```

### Step 2: Configure Prometheus

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # GPU metrics (DCGM Exporter)
  - job_name: 'dcgm'
    static_configs:
      - targets: ['gpu-exporter:9400']

  # Node metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # vLLM metrics
  - job_name: 'vllm'
    static_configs:
      - targets: ['vllm-1:8000', 'vllm-2:8000']
    metrics_path: /metrics

  # TGI metrics
  - job_name: 'tgi'
    static_configs:
      - targets: ['tgi-1:80', 'tgi-2:80']
    metrics_path: /metrics
```

### Step 3: Deploy GPU Exporter

**DCGM Exporter:**
```bash
# Run DCGM Exporter
docker run -d \
  --name dcgm-exporter \
  --gpus all \
  -p 9400:9400 \
  nvidia/dcgm-exporter:latest

# Verify metrics
curl http://localhost:9400/metrics

# Example metrics:
# DCGM_FI_DEV_GPU_UTIL{GPU="0",device="nvidia0"} 85.0
# DCGM_FI_DEV_FB_USED{GPU="0",device="nvidia0"} 21474836480
# DCGM_FI_DEV_TEMP{GPU="0",device="nvidia0"} 65.0
```

### Step 4: Create Grafana Dashboard

**Import Dashboard:**
```json
{
  "title": "LLM Monitoring Dashboard",
  "panels": [
    {
      "title": "Tokens per Second",
      "targets": [
        {
          "expr": "rate(vllm_tokens_generated_total[1m])"
        }
      ]
    },
    {
      "title": "Request Latency (p95)",
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
          "expr": "DCGM_FI_DEV_GPU_UTIL"
        }
      ]
    },
    {
      "title": "GPU Memory",
      "targets": [
        {
          "expr": "DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL * 100"
        }
      ]
    }
  ]
}
```

### Step 5: Configure Alerts

**Alert Rules:**
```yaml
# alert_rules.yml
groups:
  - name: llm_alerts
    interval: 30s
    rules:
      # High latency alert
      - alert: HighP99Latency
        expr: histogram_quantile(0.99, rate(vllm_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High P99 latency detected"
          description: "P99 latency is {{ $value }}s (threshold: 1s)"

      # GPU memory alert
      - alert: HighGPUMemory
        expr: DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL > 0.95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "GPU memory critically high"
          description: "GPU {{ $labels.GPU }} memory at {{ $value }}%"

      # Low throughput alert
      - alert: LowThroughput
        expr: rate(vllm_tokens_generated_total[5m]) < 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low token throughput"
          description: "Generating {{ $value }} tokens/sec (expected: >10)"
```

**Alert Notifications:**
```yaml
# alertmanager.yml
receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK'
        channel: '#llm-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty-notifications'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ .GroupLabels.alertname }}'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 12h

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-notifications'
```

## Common Monitoring Pitfalls

### ❌ Pitfall 1: Monitoring Everything

**Problem:**
```text
Monitoring all possible metrics:
├── 10,000+ metrics ❌
├── Alert fatigue ❌
├── Can't find what matters ❌
└── Storage costs high ❌
```

**Solution:**
```yaml
# Focus on key metrics

Essential (monitor and alert):
  - Request latency (p50, p95, p99)
  - Error rate
  - GPU utilization
  - GPU memory

Important (monitor, optional alert):
  - Tokens per second
  - Queue depth
  - CPU usage
  - Network I/O

Nice to have (monitor only):
  - Request rate by user
  - Model feature usage
  - Temperature
  - Power consumption

Rule: If you don't have an alert, do you need the metric?
```

### ❌ Pitfall 2: Alerting on Single Data Points

**Problem:**
```yaml
# Bad: Alert on single data point
alert: HighLatency
expr: latency > 1  # Triggers on ANY spike ❌

Result:
- Alerts every time one request is slow
- False positives during normal variance
- Engineers ignore alerts
```

**Solution:**
```yaml
# Good: Alert on sustained issues
alert: HighLatency
expr: rate(latency[5m]) > 1  # Average over 5 minutes
for: 5m  # Must persist for 5 minutes

Result:
- Only alerts on real problems
- Fewer false positives
- Engineers trust alerts
```

### ❌ Pitfall 3: No Business Metrics

**Problem:**
```text
Monitoring only technical metrics:
├── GPU utilization: 80% ✅
├── Latency: 100ms ✅
├── Error rate: 0.1% ✅
└── Users: Unhappy ❌

Why? Model responses are low quality but "fast" and "available"
```

**Solution:**
```yaml
# Add business metrics

User Satisfaction:
  - User ratings (thumbs up/down)
  - User feedback text
  - Response quality scores

Model Quality:
  - Factual accuracy (vs ground truth)
  - Hallucination rate
  - Toxicity score

Usage Patterns:
  - Daily active users
  - Requests per user
  - Feature adoption rate
```

### ❌ Pitfall 4: No Historical Context

**Problem:**
```yaml
Alert: "GPU utilization is 80%"

Question: Is this normal?
Answer: I don't know, no historical data ❌

Result:
- False positive (normal for this time)
- Or missed problem (should be 95%)
```

**Solution:**
```yaml
# Compare to historical baseline

Alert: "GPU utilization is 80%"
Context: "Normally 95% at this time, now 80%"
Action: Investigate (something changed)

# Use Prometheus comparisons
expr: gpu_utilization < avg_over_time(gpu_utilization[7d]) * 0.9

# Alerts when current is 10% below 7-day average
```

## Production Best Practices

### 1. Metric Naming

**Best Practices:**
```yaml
# Good metric names ✅
llm_requests_total
llm_request_duration_seconds
llm_tokens_generated_total
gpu_utilization_percent
model_load_time_seconds

# Bad metric names ❌
requests           # No prefix
llm_latency        # No unit
llm_token_gen      # Abbreviated
gpu                # Too vague
time               # Overloaded term
```

### 2. Label Strategy

**Good Labels:**
```yaml
# Add useful dimensions
llm_requests_total{
  model="llama-3-70b",
  version="v1.2",
  gpu="0",
  user_tier="premium"
}

# Common labels:
- model: Which model
- version: Model version
- gpu: GPU ID
- user_tier: User segment
- region: Geographic region
- error_type: Error classification
```

### 3. Dashboard Design

**Dashboard Hierarchy:**
```text
1. Executive Dashboard (high-level)
   ├── Requests per day
   ├── Active users
   ├── Uptime %
   └── Cost per user

2. Operational Dashboard (hourly)
   ├── Request rate
   ├── Latency (p50, p95, p99)
   ├── Error rate
   └── GPU utilization

3. Debugging Dashboard (detailed)
   ├── Per-GPU metrics
   ├── Per-model metrics
   ├── Request traces
   └── Error logs
```

### 4. Alert Strategy

**Alert Tiers:**
```yaml
P1 (Critical):
  - Service down (100% errors)
  - Data loss
  - Security breach
  Action: Wake up on-call immediately

P2 (High):
  - Degraded performance (2x latency)
  - High error rate (5%+)
  - GPU at 100% memory
  Action: Page on-call, respond within 15 minutes

P3 (Medium):
  - Slight degradation (1.5x latency)
  - One GPU failed (others working)
  - Model drift detected
  Action: Slack message, respond within 1 hour

P4 (Low):
  - Below-target performance
  - Capacity warning
  - Cost over budget
  Action: Email, investigate during business hours
```

## Real-World Examples

### Example 1: Startup Production Stack

```yaml
Setup:
  Scale: 4x A100 GPUs
  Requests: 10M/day

Monitoring Stack:
  Metrics: Prometheus (2 years retention)
  Logs: Loki (30 days retention)
  Dashboards: Grafana (15 dashboards)
  Alerts: PagerDuty + Slack

Key Metrics Tracked:
  Technical:
    - Latency (p50, p95, p99)
    - Throughput (tokens/sec)
    - GPU utilization
    - Error rate

  Business:
    - Daily active users
    - Requests per user
    - User satisfaction score

  Cost:
    - GPU hours per day
    - Cost per 1M tokens
    - Reserved vs spot instances

Results:
  - MTD (Mean Time to Detect): <5 minutes
  - MTR (Mean Time to Resolve): <30 minutes
  - False positive rate: <5%
  - Cost: $500/month (monitoring only)

ROI:
  - Prevented 3 major outages (saved $50k+)
  - Optimized GPU usage (saved $8k/month)
  - Improved user satisfaction (15% increase)
```

### Example 2: Enterprise Multi-Model

```yaml
Setup:
  Scale: 32x H100 GPUs
  Models: 8 different models
  Requests: 100M/day

Monitoring Stack:
  Metrics: VictoriaMetrics (cluster)
  Logs: Elasticsearch (90 days)
  Traces: Jaeger
  Dashboards: Grafana (50+ dashboards)
  Alerts: Opsgenie

Advanced Features:
  - Model comparison dashboards
  - A/B testing metrics
  - Drift detection alerts
  - Capacity planning reports
  - Cost allocation per team

Results:
  - Detected model drift 2 weeks before users noticed
  - Optimized model routing (20% cost savings)
  - Reduced alert noise by 80%
  - Improved SLA compliance from 99.5% to 99.95%
```

## Learning Path

1. **[1501: Monitoring and Observability](./1501-Monitoring-and-Observability.md)** - Foundations of LLM monitoring
2. **[1502: Model Drift Detection](./1502-Model-Drift-Detection.md)** - Detecting model degradation
3. **[1503: LLM Observability](./1503-LLM-Observability.md)** - Advanced observability techniques

## Prerequisites

Before starting this module, ensure you understand:

### Basic Knowledge
- **Monitoring Concepts:** Metrics, logs, traces (three pillars)
- **Time Series Data:** Understanding of time-based data
- **Statistical Analysis:** Averages, percentiles, distributions
- **Alerting:** Threshold-based alerts, escalation

### Technical Requirements
- **Basic Linux:** System monitoring commands
- **Docker:** Running containers, viewing logs
- **Networking:** HTTP, ports, load balancing concepts

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

Validate your knowledge:

- **[assessment/QUIZ.md](./assessment/QUIZ.md)** - Test your understanding (20 questions, 80% to pass)
- **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** - Hands-on monitoring exercises

## Key Takeaways

After completing this module, you will be able to:

✅ **Set up comprehensive monitoring for LLM systems**
   - Deploy Prometheus + Grafana stack
   - Configure GPU monitoring with DCGM
   - Collect application-specific metrics

✅ **Implement the three pillars of observability**
   - Metrics: What happened (Prometheus)
   - Logs: Why it happened (Loki)
   - Traces: Where it happened (Jaeger)

✅ **Detect and diagnose model drift**
   - Monitor input distribution changes
   - Track model quality metrics
   - Alert on performance degradation

✅ **Configure effective alerts**
   - Set up alert thresholds
   - Configure alert routing
   - Avoid alert fatigue

✅ **Create meaningful dashboards**
   - Executive dashboards (high-level)
   - Operational dashboards (real-time)
   - Debugging dashboards (detailed)

✅ **Optimize based on monitoring data**
   - Right-size GPU resources
   - Identify performance bottlenecks
   - Track cost efficiency

## Additional Resources

### Tools & Utilities

```bash
# Monitoring Stack
prometheus         # Metrics collection
grafana-cli        # Dashboard management
alertmanager       # Alert routing

# GPU Monitoring
dcgm-exporter      # NVIDIA GPU metrics
nvidia-smi         # Quick GPU stats

# Log Aggregation
loki               # Log aggregation
promtail           # Log collection
logcli             # Log querying

# Tracing
jaeger-all-in-one  # Distributed tracing
tempo              # High-performance tracing
```

### Further Reading

**Documentation:**
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [NVIDIA DCGM](https://developer.nvidia.com/dcgm/)
- [OpenTelemetry](https://opentelemetry.io/docs/)

**Books:**
- "Monitoring Distributed Systems" by B. B. Jones
- "Site Reliability Engineering" by Google SRE team
- "Observability Engineering" by Charity Majors

**Online Courses:**
- [Prometheus Training](https://prometheus.io/community/training/)
- [Grafana Fundamentals](https://grafana.com/tutorials/)
- [SRE Fundamentals](https://www.cloudskills.google.com/paths/sre)

### Community Resources

**Forums:**
- [Prometheus Users](https://groups.google.com/g/prometheus-users)
- [Grafana Community](https://community.grafana.com/)
- [r/prometheus on Reddit](https://www.reddit.com/r/prometheus/)

**Blogs:**
- [Grafana Blog](https://grafana.com/blog/)
- [Prometheus Blog](https://prometheus.io/blog/)
- [Observability Blog](https://www.honeycomb.io/blog/)

## Module Completion Checklist

```yaml
Understanding:
  - [ ] I understand the three pillars of observability
  - [ ] I can explain key LLM metrics
  - [ ] I know when to alert vs just monitor
  - [ ] I can design a monitoring strategy

Practical Skills:
  - [ ] I have deployed Prometheus + Grafana
  - [ ] I have configured DCGM exporter
  - [ ] I have created custom dashboards
  - [ ] I have set up alerting rules

Production Ready:
  - [ ] I have monitoring for all critical services
  - [ ] I have configured alert notifications
  - [ ] I have tested alert escalation
  - [ ] I have documented runbooks for alerts
```

## Glossary

| Term | Definition |
|------|------------|
| **Metrics** | Time-series numerical measurements |
| **Logs** | Discrete text-based events |
| **Traces** | Request journey through distributed systems |
| **Prometheus** | Time-series database and monitoring system |
| **Grafana** | Visualization and dashboarding platform |
| **PromQL** | Prometheus Query Language |
| **DCGM** | Data Center GPU Manager (NVIDIA) |
| **SLA** | Service Level Agreement |
| **MTTD** | Mean Time To Detect (issue) |
| **MTTR** | Mean Time To Resolve (issue) |
| **Percentile** | Value below which percentage of data falls (p95 = 95th percentile) |
| **Histogram** | Distribution of values across buckets |
| **Alertmanager** | Prometheus alert routing and management |
| **Loki** | Grafana's log aggregation system |
| **Jaeger** | Distributed tracing system |
| **OpenTelemetry** | Observability framework standard |

---

**Module Duration:** 8-10 hours
**Difficulty:** Intermediate-Advanced

**Ready to proceed?** Continue to [1501: Monitoring and Observability](./1501-Monitoring-and-Observability.md)
