---
Document ID: 1400-LLMOPS-README
Title: "1400: LLMOps and Model Serving"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Beginner
---

# 1400: LLMOps and Model Serving

## Module Overview

This module covers production LLMOps practices and model serving infrastructure for deploying LLMs in production environments. You'll learn about high-performance serving engines (vLLM, TGI), production deployment strategies, monitoring, A/B testing, and cost optimization.

## Why LLMOps Matters for LLMs

### 1. Production Readiness: Deploy Models Reliably at Scale

**Development vs Production:**
```text
Development (your laptop):
├── Single user (you) ✅
├── Model loads in 30 seconds ✅
├── Errors visible in console ✅
└── Restart if it crashes ✅

Production (thousands of users):
├── 10,000+ concurrent requests ❌
├── Must load in <1 second ❌
├── Errors must not affect users ❌
├── Auto-restart <5 seconds ❌
├── Zero downtime deployments ❌
└── Load balancing across servers ❌
```

**Real-World Example:**
```yaml
Scenario: Black Friday traffic spike

Manual approach:
  09:00: Traffic increases 100x
  09:01: Server crashes
  09:05: Engineer wakes up to alert
  09:15: Engineer manually scales
  09:20: Service back online
  Result: 20 minutes downtime, angry customers ❌

LLMOps approach:
  09:00: Traffic increases 100x
  09:00:05: Auto-scaler detects load
  09:00:10: New instances spun up
  09:00:30: Traffic distributed
  09:01: Load balancer stabilized
  Result: 1 minute degraded service, no downtime ✅
```

### 2. Performance Optimization: Maximize Throughput

**Throughput Comparison (Same Hardware):**

| Serving Method | Tokens/Second | Latency (p50) | Latency (p99) |
|----------------|---------------|---------------|---------------|
| **Basic Python** | 10 | 500ms | 2000ms |
| **Ollama** | 50 | 100ms | 500ms |
| **Text Generation Inference (TGI)** | 150 | 50ms | 200ms |
| **vLLM** | 250 | 30ms | 100ms |

**Key Insight:**
```text
Same GPU, same model:
- Basic Python: 10 tokens/sec ❌
- vLLM: 250 tokens/sec ✅

25x improvement = 25x cost savings!
```

**vLLM vs TGI:**
```yaml
vLLM (PagedAttention):
  Pros:
    - Highest throughput
    - Best for high-concurrency
    - Open source
  Cons:
    - Memory intensive
    - Newer (less stable)
  Best For: High-volume API services

TGI (HuggingFace):
  Pros:
    - Production hardened
    - Easy setup
    - Many features (quantization, etc.)
  Cons:
    - Lower throughput than vLLM
    - More memory overhead
  Best For: Enterprise deployments
```

### 3. Monitoring: Track Performance and Resources

**What to Monitor:**

| Category | Metrics | Why It Matters |
|----------|---------|----------------|
| **Performance** | Tokens/sec, latency, throughput | User experience |
| **Resources** | GPU utilization, memory, temperature | Capacity planning |
| **Errors** | Error rate, timeout rate, failures | Reliability |
| **Business** | Requests/user, model usage | Cost optimization |

**Real-World Alert Example:**
```yaml
Alert: High GPU Memory
  Condition: GPU memory > 95% for 5 minutes
  Impact: Model may crash, users see errors
  Action: Auto-scale or offload to another GPU

Alert: High P99 Latency
  Condition: P99 latency > 500ms for 10 minutes
  Impact: Slow response for some users
  Action: Scale up or optimize model

Alert: High Error Rate
  Condition: Error rate > 1% for 5 minutes
  Impact: Failed requests
  Action: Investigate logs, restart if needed
```

### 4. Cost Management: Optimize GPU Utilization

**Cost Breakdown (Annual):**

| Component | Monthly | Annual | % of Total |
|-----------|---------|--------|------------|
| **GPU Hardware** | $5,000 | $60,000 | 60% |
| **Cloud/Hosting** | $2,000 | $24,000 | 24% |
| **Engineering** | $1,500 | $18,000 | 18% |
| **Software/Licenses** | $500 | $6,000 | 6% |
| **Total** | $9,000 | $108,000 | 100% |

**Optimization Strategies:**
```yaml
# Before optimization:
4x A100 GPUs: 40% utilization
Cost: $9,000/month
Tokens/month: 10 billion
Cost per million tokens: $0.90

# After optimization (vLLM + batching):
4x A100 GPUs: 85% utilization
Cost: $9,000/month (same)
Tokens/month: 21 billion
Cost per million tokens: $0.43
Savings: 52%!
```

## LLMOps Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                        │
│                   (ALB / NGINX / Envoy)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                       API Gateway                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Rate Limiting | Auth | Routing | Logging           │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌───────▼────────┐
│   vLLM Pod 1   │  │  vLLM Pod 2  │  │  vLLM Pod 3    │
│  (GPU 0, GPU1) │  │  (GPU 2,3)   │  │  (GPU 4,5)     │
└───────┬────────┘  └──────┬───────┘  └───────┬────────┘
        │                  │                   │
        └──────────────────┼───────────────────┘
                           │
                  ┌────────▼────────┐
                  │  Model Storage  │
                  │  (S3 / Local)   │
                  └─────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Monitoring Stack                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Prometheus│  │ Grafana  │  │  Loki    │  │ Alerts   │   │
│  │(Metrics) │  │(Dashboards│  │ (Logs)   │  │(PagerDuty│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Model Serving Engines

### 1. vLLM (Highest Performance)

**Key Features:**
- **PagedAttention:** Efficient memory management
- **Continuous Batching:** Dynamic batch sizing
- **High Throughput:** 200-300 tokens/sec per GPU
- **Open Source:** Apache 2.0 license

**Architecture:**
```python
# vLLM uses PagedAttention (like OS virtual memory)

Traditional approach:
├── KV cache allocated for max sequence
├── Wasted memory for short sequences
└── Limited by worst-case scenario ❌

PagedAttention:
├── KV cache divided into "pages"
├── Pages allocated on-demand
├── Pages can be shared between sequences
└── 2-4x more sequences per GPU ✅
```

**Quick Start:**
```bash
# Install vLLM
uv pip install vllm

# Start server
python -m vllm.entrypoints.api_server \
  --model meta-llama/Llama-3-70B \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096 \
  --port 8000

# Test
curl http://localhost:8000/generate \
  -d '{"prompt": "Hello, world!", "max_tokens": 50}'
```

**Docker Deployment:**
```yaml
# docker-compose.yml
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    environment:
      - MODEL_NAME=meta-llama/Llama-3-70B
      - TENSOR_PARALLEL_SIZE=2
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
    volumes:
      - ./models:/root/.cache/huggingface
```

### 2. Text Generation Inference (TGI)

**Key Features:**
- **Production Hardened:** Battle-tested by HuggingFace
- **Easy Setup:** One-command deployment
- **Features:** Quantization, Flash Attention, Streaming
- **Enterprise Support:** Commercial support available

**Quick Start:**
```bash
# Launch TGI
model=meta-llama/Llama-3-70B
volume=$PWD/data # share a volume with the Docker container to avoid downloading weights every run

docker run --gpus all --shm-size 1g -p 8080:80 \
  -v $volume:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id $model \
  --num-shard 2 \
  --quantize bitsandbytes-nf4

# Test
curl 127.0.0.1:8080/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":20}}'
```

**Kubernetes Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tgi-llama-70b
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tgi-llama
  template:
    metadata:
      labels:
        app: tgi-llama
    spec:
      containers:
      - name: tgi
        image: ghcr.io/huggingface/text-generation-inference:latest
        args:
          - --model-id
          - meta-llama/Llama-3-70B
          - --num-shard
          - "2"
          - --quantize
          - bitsandbytes-nf4
        ports:
        - containerPort: 80
        resources:
          limits:
            nvidia.com/gpu: 2
```

### 3. Ollama (Simplicity)

**Key Features:**
- **Zero Configuration:** Works out of the box
- **Local First:** Runs on your machine
- **Easy API:** Simple REST API
- **Model Management:** Built-in model downloads

**Quick Start:**
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Run model
ollama run llama3:70b

# API server runs automatically on :11434
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:70b",
  "prompt": "Why is the sky blue?"
}'
```

**Pros/Cons:**
```yaml
Pros:
  ✅ Easiest to set up
  ✅ Great for local development
  ✅ Built-in model management
  ✅ Cross-platform

Cons:
  ❌ Lower throughput than vLLM/TGI
  ❌ Less customizable
  ❌ Not designed for high-scale production
```

## Comparison: vLLM vs TGI vs Ollama

| Feature | vLLM | TGI | Ollama |
|---------|------|-----|--------|
| **Throughput** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Ease of Use** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Production Ready** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Features** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Memory Efficiency** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Best For** | High-scale APIs | Enterprise | Local/Edge |

## Quick Start Guide

### Step 1: Choose Your Engine

| Use Case | Recommended Engine |
|----------|-------------------|
| **Learning/Local** | Ollama |
| **Medium Production (<1000 users)** | TGI |
| **High Production (>1000 users)** | vLLM |
| **Enterprise with Support** | TGI |

### Step 2: Production Deployment with vLLM

**Systemd Service:**
```bash
# /etc/systemd/system/vllm.service
[Unit]
Description=vLLM Server
After=network.target

[Service]
Type=simple
User=llm
WorkingDirectory=/opt/vllm
Environment="MODEL_NAME=meta-llama/Llama-3-70B"
Environment="TENSOR_PARALLEL_SIZE=2"
ExecStart=/usr/bin/python3 -m vllm.entrypoints.api_server \
  --model $MODEL_NAME \
  --tensor-parallel-size $TENSOR_PARALLEL_SIZE \
  --gpu-memory-utilization 0.9 \
  --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
systemctl enable vllm
systemctl start vllm

# Check status
systemctl status vllm
```

### Step 3: Load Balancing

**Nginx Configuration:**
```nginx
upstream vllm_backend {
    least_conn;
    server vllm-1:8000 max_fails=3 fail_timeout=30s;
    server vllm-2:8000 max_fails=3 fail_timeout=30s;
    server vllm-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name llm-api.example.com;

    location /generate {
        proxy_pass http://vllm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

### Step 4: Monitoring Setup

**Prometheus Configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'vllm'
    static_configs:
      - targets: ['vllm-1:8000', 'vllm-2:8000', 'vllm-3:8000']
    metrics_path: /metrics
```

**Grafana Dashboard:**
```yaml
# Key metrics to track
panels:
  - title: Tokens per Second
    query: rate(vllm_tokens_generated_total[1m])

  - title: Request Latency (p95)
    # quantiles come from the cumulative _bucket series via rate()
    query: histogram_quantile(0.95, rate(vllm_request_duration_seconds_bucket[5m]))

  - title: GPU Utilization
    query: DCGM_FI_DEV_GPU_UTIL

  - title: GPU Memory Used
    query: DCGM_FI_DEV_FB_USED
```

## Common LLMOps Pitfalls

### ❌ Pitfall 1: Cold Starts

**Problem:**
```text
First request: 30 seconds (model loading) ❌
Subsequent: 100ms ✅

User experience: "Why is it slow the first time?"
```

**Solution:**
```yaml
# Method 1: Preload on startup ✅
# vLLM loads model on server start
# Keeps model in GPU memory

# Method 2: Warmup requests ✅
# Send dummy requests after deployment
curl -X POST http://localhost:8000/generate \
  -d '{"prompt": "warmup", "max_tokens": 1}'

# Method 3: Canary deployment ✅
# Keep 1 instance always warm
# Scale others as needed
```

### ❌ Pitfall 2: Memory Fragmentation

**Problem:**
```text
After 1000 requests:
- GPU memory: 95% used
- Available: 5% (fragmented)
- New request fails: "Out of memory" ❌
```

**Solution:**
```yaml
# Use vLLM with PagedAttention ✅
python -m vllm.entrypoints.api_server \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096 \
  --block-size 16

# Regular restarts to clear fragmentation ✅
# Kubernetes: Rolling restart every 24h
# Systemd: Restart=on-failure
```

### ❌ Pitfall 3: No Rate Limiting

**Problem:**
```text
Normal load: 100 requests/sec ✅
Attack/Bot: 10,000 requests/sec ❌
Result: All users affected
```

**Solution:**
```python
# rate_limit.py
from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

@app.post("/generate")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def generate(request: Request, prompt: str):
    # Your generation logic
    pass
```

### ❌ Pitfall 4: Missing Observability

**Problem:**
```text
User: "It's slow"
You: "Let me check... I have no metrics" ❌
```

**Solution:**
```yaml
# Minimum metrics to collect:
Essential:
  - Request rate
  - Latency (p50, p95, p99)
  - Error rate
  - GPU utilization
  - GPU memory

Recommended:
  - Tokens per second
  - Batch size distribution
  - Queue depth
  - Model loading time
  - Cache hit rate
```

## Production Best Practices

### 1. Deployment Strategies

**Blue-Green Deployment:**
```text
Step 1: Deploy new version to "green"
  - Current traffic: blue (v1.0)
  - New deployment: green (v1.1)
  - Test green in isolation

Step 2: Switch traffic
  - Gradual: 10% -> 50% -> 100%
  - Monitor for errors

Step 3: Full cutover
  - All traffic: green
  - Keep blue for rollback

Step 4: Cleanup
  - If green successful: remove blue
  - If green fails: revert to blue
```

**A/B Testing Models:**
```yaml
# Deploy multiple model versions
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-service-v1
spec:
  replicas: 3  # 75% traffic
  template:
    metadata:
      labels:
        version: v1.0

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-service-v2
spec:
  replicas: 1  # 25% traffic (canary)
  template:
    metadata:
      labels:
        version: v1.1
```

### 2. Scaling Strategies

**Horizontal Scaling (More Replicas):**
```yaml
When to scale:
  - CPU/GPU utilization > 80%
  - Queue depth increasing
  - Latency degrading

Auto-scaling (Kubernetes):
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: nvidia.com/gpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Vertical Scaling (Larger GPU):**
```yaml
When to scale:
  - Model doesn't fit in memory
  - Need higher throughput
  - Cost per token better on larger GPU

Migration path:
  2x RTX 4090 (24GB each) → 1x A100 (80GB)
  - Tokens/sec: 50 → 150
  - Cost: Same
  - Performance: 3x better ✅
```

### 3. Cost Optimization

**Right-Sizing GPUs:**
```yaml
Model Requirements:
  Llama-3-8B (4-bit): 6 GB GPU memory
  Llama-3-70B (4-bit): 40 GB GPU memory

GPU Selection:
  Llama-3-8B: RTX 3060 (12 GB) ✅ Cost: $300
  Llama-3-70B: RTX 4090 (24 GB) ❌ Too small
  Llama-3-70B: A100 (80 GB) ✅ Cost: $15,000

Better option:
  Llama-3-70B (4-bit): 2x RTX 3090 (24GB each)
  - Cost: $1,500 vs $15,000
  - Tensor parallelism: 2 GPUs
  - Performance: Slightly slower (90%)
  - Cost savings: 90%!
```

**Spot Instances:**
```yaml
Cloud Spot/Preemptible:
  Normal instance: $3/hour
  Spot instance: $0.50/hour (83% savings!)

Trade-offs:
  ❌ Can be interrupted
  ✅ Great for batch jobs
  ✅ OK for stateless inference

Mitigation:
  - Use checkpointing
  - Multi-region deployment
  - Auto-restart on interruption
```

## Real-World Examples

### Example 1: Startup API Service

```yaml
Setup:
  Engine: vLLM
  Model: Llama-3-70B (4-bit)
  Hardware: 4x A100 (40GB)
  Deployment: Kubernetes (6 replicas)

Configuration:
  - Load balancer: NGINX
  - Auto-scaling: 2-10 replicas
  - Monitoring: Prometheus + Grafana
  - Rate limiting: 100 req/min per user

Results:
  - Throughput: 1,500 tokens/sec
  - Latency p50: 30ms
  - Latency p99: 150ms
  - Concurrent users: 2,000+
  - Uptime: 99.95%
  - Cost: $20,000/month

Lessons Learned:
  - vLLM critical for performance
  - Auto-scaling prevents overprovisioning
  - Monitoring saved production multiple times
```

### Example 2: Enterprise On-Premise

```yaml
Setup:
  Engine: TGI
  Model: Custom 120B (8-bit)
  Hardware: 8x H100 (80GB)
  Deployment: Bare metal + Docker Swarm

Configuration:
  - Load balancer: HAProxy
  - Fixed scaling: 8 replicas (1 per GPU)
  - Monitoring: Datadog
  - Security: VPN + mTLS

Results:
  - Throughput: 3,000 tokens/sec
  - Latency p50: 20ms
  - Latency p99: 80ms
  - Concurrent users: 5,000+
  - Uptime: 99.99%
  - Cost: $500,000 (hardware) + $100k/year (ops)

Lessons Learned:
  - TGI chosen for enterprise support
  - On-premise for data security
  - Fixed capacity simplifies ops
  - Heavy monitoring investment pays off
```

## Learning Path

### Core Concepts
1. **[1401: Ollama Enterprise](./1401-Ollama-Enterprise.md)** - Production Ollama deployment
2. **[1402: vLLM and TGI](./1402-vLLM-and-TGI.md)** - High-performance serving engines

### Production Guides
3. **[guides/1404: vLLM Production Deployment](./guides/1404-vLLM-Production-Deployment.md)** - Complete vLLM setup
4. **[guides/1405: TGI Deployment Guide](./guides/1405-TGI-Deployment-Guide.md)** - TGI production deployment

## Prerequisites

Before starting this module, ensure you understand:

### Basic Knowledge
- **Docker & Containers:** Building images, running containers
- **Model Quantization:** 4-bit, 8-bit quantization basics
- **API Design:** REST APIs, load balancing concepts
- **Monitoring:** Metrics, logging, alerting fundamentals

### Hardware Requirements
- **GPU:** At least one NVIDIA GPU (8GB+ VRAM)
- **RAM:** 32 GB minimum
- **Storage:** 200 GB SSD for models

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

Validate your knowledge:

- **[assessment/QUIZ.md](./assessment/QUIZ.md)** - Test your understanding (20 questions, 80% to pass)
- **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** - Hands-on LLMOps exercises

## Key Takeaways

After completing this module, you will be able to:

✅ **Choose the right serving engine**
   - Ollama for local development
   - vLLM for high-throughput production
   - TGI for enterprise deployments

✅ **Deploy production-grade LLM services**
   - Container-based deployments
   - Load balancing strategies
   - High availability setups

✅ **Implement monitoring and observability**
   - Performance metrics (latency, throughput)
   - Resource monitoring (GPU, memory)
   - Alert configuration

✅ **Optimize serving performance**
   - PagedAttention for efficiency
   - Continuous batching
   - Right-sizing GPU resources

✅ **Handle production operations**
   - Blue-green deployments
   - A/B testing models
   - Auto-scaling strategies
   - Cost optimization

## Additional Resources

### Tools & Utilities

```bash
# Model Serving
ollama             # Local model serving
vllm serve         # High-performance serving
tgi-server         # TGI server

# Monitoring
prometheus         # Metrics collection
grafana            # Dashboards
dcgm-exporter      # GPU metrics

# Load Testing
hey                # HTTP load testing
wrk                # HTTP benchmark
locust             # Python load testing
```

### Further Reading

**Documentation:**
- [vLLM Documentation](https://docs.vllm.ai/)
- [TGI Documentation](https://huggingface.co/docs/text-generation-inference)
- [Ollama Documentation](https://ollama.ai/)

**Books:**
- "Designing Machine Learning Systems" by Chip Huyen
- "Introducing MLOps" by Mark Treveil
- "Building Machine Learning Pipelines" by Hannes Hapke

**Online Courses:**
- [LLMOps: LLMOps with LangChain](https://www.deeplearning.ai/short-courses/)
- [Production ML Systems](https://www.fullstackdeeplearning.com/)

### Community Resources

**Forums:**
- [vLLM Discord](https://discord.gg/vllm)
- [HuggingFace Forums](https://discuss.huggingface.co/)
- [r/LocalLLaMA on Reddit](https://www.reddit.com/r/LocalLLaMA/)

**Blogs:**
- [vLLM Blog](https://blog.vllm.ai/)
- [HuggingFace Blog](https://huggingface.co/blog)
- [LlamaIndex Blog](https://llamaindex.ai/blog/)

## Module Completion Checklist

```yaml
Understanding:
  - [ ] I can explain vLLM vs TGI vs Ollama
  - [ ] I understand PagedAttention
  - [ ] I know when to use each serving engine
  - [ ] I can design a production serving architecture

Practical Skills:
  - [ ] I have deployed vLLM or TGI
  - [ ] I have configured load balancing
  - [ ] I have set up monitoring
  - [ ] I have implemented auto-scaling

Production Ready:
  - [ ] I have tested blue-green deployments
  - [ ] I have configured alerts
  - [ ] I have optimized GPU utilization
  - [ ] I have documented my deployment
```

## Glossary

| Term | Definition |
|------|------------|
| **vLLM** | High-performance LLM serving engine with PagedAttention |
| **TGI** | Text Generation Inference - HuggingFace's serving engine |
| **PagedAttention** | Memory-efficient attention mechanism (like virtual memory) |
| **Continuous Batching** | Dynamic batch sizing for better throughput |
| **Tensor Parallelism** | Split model across multiple GPUs |
| **PagedAttention KV Cache** | Divides KV cache into pages for efficient memory use |
| **Blue-Green Deployment** | Zero-downtime deployment strategy |
| **A/B Testing** | Running multiple model versions simultaneously |
| **HPA** | Horizontal Pod Autoscaler - automatic scaling |
| **Ollama** | Simple local LLM serving tool |

---

**Module Duration:** 12-15 hours
**Difficulty:** Advanced

**Ready to proceed?** Continue to [1401: Ollama Enterprise](./1401-Ollama-Enterprise.md)
