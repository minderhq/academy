---
Document ID: 1403
Title: "1403: vLLM Production Deployment Guide"
Phase: 1
Module: 1400
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'llmops', 'vllm']
---

# 1403: vLLM Production Deployment Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Architecture](#architecture)
- [Deployment Options](#deployment-options)
- [Configuration Guide](#configuration-guide)
- [Client Usage Examples](#client-usage-examples)
- [Advanced Configuration](#advanced-configuration)
- [Performance Benchmarks](#performance-benchmarks)
- [Troubleshooting](#troubleshooting)
- [Quick Start](#quick-start)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Walk the production stack diagram - Nginx gateway, vLLM server, Prometheus - and state what each layer adds
- Deploy the pinned vllm/vllm-openai image via Docker Compose and K3s with PVC model cache and health-gated probes
- Size gpu_memory_utilization, max_model_len, and max_num_seqs from the 11GB budget math (~4.9GB left for KV)
- Call the OpenAI-compatible API with streaming from Python, curl, and TypeScript, honoring --api-key auth
- Operate the advanced pieces: multi-model routing, replica-pool nginx LB, Prometheus scraping, and the FastAPI model-aware gateway
- Read the V1 Prometheus metrics (kv_cache_usage_perc, preemptions, TTFT histograms) and benchmark concurrency honestly

---

## Abstract
vLLM is a high-throughput LLM inference engine: PagedAttention segments the KV cache into fixed-size pages to eliminate fragmentation, and continuous batching keeps the GPU fed across concurrent requests. On an 11GB-class GPU, fp16 7B weights (~14GB) do not fit — every runnable example in this guide serves a pre-quantized AWQ checkpoint (~3.5GB weights).

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                       vLLM Production Stack                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │                     API Gateway (Nginx)                        │      │
│  │              /v1/completions, /v1/chat/completions            │      │
│  └────────────────────────────┬───────────────────────────────────┘      │
│                               │                                          │
│  ┌────────────────────────────▼───────────────────────────────────┐      │
│  │                    vLLM Server (OpenAI API)                    │      │
│  │  ┌────────────────────────────────────────────────────────┐    │      │
│  │  │              Request Router & Scheduler                 │    │      │
│  │  └────────────────────────────────────────────────────────┘    │      │
│  │  ┌────────────────────────────────────────────────────────┐    │      │
│  │  │              KV Cache Manager                          │    │      │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │    │      │
│  │  │  │ Block 0  │ │ Block 1  │ │ Block 2  │ │ Block N  │    │    │      │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │    │      │
│  │  └────────────────────────────────────────────────────────┘    │      │
│  │  ┌────────────────────────────────────────────────────────┐    │      │
│  │  │              PagedAttention Kernel                     │    │      │
│  │  │     GPU 0 (11GB-class GPU) │ GPU 1 (optional)             │    │      │
│  │  └────────────────────────────────────────────────────────┘    │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                               │                                          │
│  ┌────────────────────────────▼───────────────────────────────────┐      │
│  │              Monitoring (Prometheus + Grafana)                 │      │
│  │   - Request rate, latency, throughput                         │      │
│  │   - GPU utilization, memory, temperature                      │      │
│  │   - KV cache usage                                            │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Deployment Options

### Option 1: Docker Compose (Recommended for Single GPU)

```yaml
# docker-compose.yml
services:
  vllm-qwen:
    image: vllm/vllm-openai:v0.30.0   # pinned release (Sep 2026); check releases for newer
    container_name: academy-vllm-qwen
    ports:
      - "8000:8000"
    # command: overrides CMD — the image ENTRYPOINT (the OpenAI-compatible
    # API server) is preserved, so these are server arguments:
    command: >
      --model Qwen/Qwen3-8B-AWQ
      --tensor-parallel-size 1
      --gpu-memory-utilization 0.9
      --max-model-len 4096
      --dtype half
      --host 0.0.0.0
      --port 8000
      --api-key ${VLLM_API_KEY:?set VLLM_API_KEY in .env}
      # delete the --api-key line to serve without authentication
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      # python3 ships in the image; curl is not guaranteed to be present
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - academy-net
    volumes:
      - /srv/models/vllm:/root/.cache/huggingface
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # The Meta-Llama-3.1 lineage is gated on the Hub (contact info +
  # license acceptance), and the hugging-quants AWQ mirror keeps that
  # gate — this service needs an HF token with accepted license terms.
  # Pre-quantized INT4 weights still fit 11GB.
  vllm-llama:
    image: vllm/vllm-openai:v0.30.0
    container_name: academy-vllm-llama
    ports:
      - "8001:8000"
    command: >
      --model hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4
      --tensor-parallel-size 1
      --gpu-memory-utilization 0.9
      --max-model-len 4096
      --dtype half
      --host 0.0.0.0
      --port 8000
    environment:
      - HF_TOKEN=${HF_TOKEN:?set HF_TOKEN in .env}   # gated checkpoint
      - CUDA_VISIBLE_DEVICES=1   # second GPU; on a single 11GB GPU run only
                                 # ONE service — two 7B servers don't fit
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - academy-net

networks:
  # create once first: docker network create academy-net
  academy-net:
    external: true
```

### Option 2: K3s Deployment (for Cluster)

```yaml
# k8s-vllm-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-qwen
  namespace: academy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm-qwen
  template:
    metadata:
      labels:
        app: vllm-qwen
    spec:
      nodeSelector:
        accelerator: nvidia   # must match the GPU node label (see 1301)
      containers:
      - name: vllm
        image: vllm/vllm-openai:v0.30.0   # pinned release (Sep 2026); check releases for newer
        # args (not command:) — command: would replace the image ENTRYPOINT
        args:
          - --model
          - Qwen/Qwen3-8B-AWQ   # pre-quantized AWQ: fits 11GB
          - --tensor-parallel-size
          - "1"
          - --gpu-memory-utilization
          - "0.9"
          - --max-model-len
          - "4096"
          - --dtype
          - half
        ports:
        - containerPort: 8000
          name: http
        # Gated checkpoints (e.g. meta-llama/Meta-Llama-3.1-8B-Instruct) additionally
        # need the token:
        # env:
        # - name: HF_TOKEN
        #   valueFrom:
        #     secretKeyRef:
        #       name: hf-token
        #       key: token
        resources:
          requests:
            memory: "8Gi"
            cpu: "2"
            nvidia.com/gpu: "1"
          limits:
            memory: "11Gi"
            cpu: "4"
            nvidia.com/gpu: "1"
        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache/huggingface
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          # first boot downloads ~3.5GB of weights to the PVC — don't
          # kill-restart-loop the pod before that finishes
          initialDelaySeconds: 300
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-qwen
  namespace: academy
spec:
  selector:
    app: vllm-qwen
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache-pvc
  namespace: academy
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: nfs-standard   # NFS CSI storage class (see 1303)
  resources:
    requests:
      storage: 50Gi
```

## Configuration Guide

### Key Parameters Explained

| Parameter | Default | Description | 11GB-class GPU Guidance |
|-----------|---------|-------------|------------------------|
| `--tensor-parallel-size` | 1 | GPUs used for tensor parallelism | 1 (single GPU) |
| `--gpu-memory-utilization` | 0.9 | Fraction of total VRAM vLLM may use (weights + KV cache + activations) | 0.9 — lower only when other processes share the GPU |
| `--max-model-len` | model's `max_position_embeddings` | Max sequence length. Qwen3-8B's ceiling is 40960 — left at the default it over-runs the 11GB KV budget, so set it explicitly | 4096 |
| `--dtype` | auto (from checkpoint config) | Compute dtype for activations/KV | `half` for AWQ checkpoints |
| `--quantization` | auto-detected for pre-quantized checkpoints | awq/gptq — requires a pre-quantized checkpoint repo | pre-quantized AWQ |
| `--block-size` | 16 | KV cache block size | leave the default |
| `--enable-prefix-caching` | enabled (V1 engine) | Cache shared prefixes | keep on; disable only when benchmarking identical prompts |
| `--max-num-seqs` | 256 | Max concurrent sequences | 64–128 (KV-cache-bound on 11GB) |

### Performance Tuning Configuration

```bash
# High Throughput Configuration (pre-quantized AWQ: ~5.5GB weights)
--model Qwen/Qwen3-8B-AWQ \
--gpu-memory-utilization 0.9 \
--max-model-len 2048 \
--max-num-seqs 128 \
--dtype half
# prefix caching stays on for shared system prompts

# Long Context Configuration
--model Qwen/Qwen3-8B-AWQ \
--gpu-memory-utilization 0.9 \
--max-model-len 8192 \
--max-num-seqs 16 \
--dtype half
# budget check: 0.9 x 11GB ~ 9.9GB, minus ~6.1GB weights and ~1.2GB
# activations leaves ~2.6GB for KV. Qwen3-8B's GQA is roomier per
# token (8 KV heads vs 4): ~144KB fp16 (2 x 36 layers x 1024 kv-dim
# x 2 bytes), so an 8k sequence needs ~1.2GB — roughly two fit, and
# context length joins concurrency as a first-order budget term.

# Balanced Configuration (11GB VRAM)
--model Qwen/Qwen3-8B-AWQ \
--gpu-memory-utilization 0.9 \
--max-model-len 4096 \
--max-num-seqs 64 \
--dtype half
```

## Client Usage Examples

### Python Client

```python
# vllm_client.py
import os

from openai import OpenAI

# The model name must match the checkpoint the server was started with
client = OpenAI(
    base_url="http://192.168.1.100:8000/v1",
    api_key=os.environ["VLLM_API_KEY"],   # required only when the server runs --api-key
)

# Chat completion
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B-AWQ",
    messages=[
        {"role": "system", "content": "You are a helpful assistant for academy."},
        {"role": "user", "content": "Explain quantum computing in simple terms."},
    ],
    max_tokens=512,
    temperature=0.7,
    stream=True,
)

# Stream response — some chunks carry no choices, so guard the index
for chunk in response:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# Non-streaming response
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B-AWQ",
    messages=[{"role": "user", "content": "What is AI?"}],
    max_tokens=100,
)
print(response.choices[0].message.content)
```

### cURL Examples

```bash
# Health check
curl http://192.168.1.100:8000/health

# List models
curl http://192.168.1.100:8000/v1/models

# Chat completion (Authorization header only needed with --api-key)
curl -X POST http://192.168.1.100:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${VLLM_API_KEY:?export VLLM_API_KEY first}" \
  -d '{
    "model": "Qwen/Qwen3-8B-AWQ",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'

# Completion (non-chat)
curl -X POST http://192.168.1.100:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B-AWQ",
    "prompt": "The future of AI is",
    "max_tokens": 50
  }'
```

### JavaScript/TypeScript Client

```typescript
// vllm_client.ts
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://192.168.1.100:8000/v1',
  apiKey: process.env.VLLM_API_KEY as string,
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'Qwen/Qwen3-8B-AWQ',
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: 'Explain Docker.' },
    ],
    max_tokens: 500,
    temperature: 0.7,
  });

  console.log(response.choices[0].message.content);
}

// Streaming
async function chatStream() {
  const stream = await client.chat.completions.create({
    model: 'Qwen/Qwen3-8B-AWQ',
    messages: [
      { role: 'user', content: 'Write a short poem.' },
    ],
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}
```

## Advanced Configuration

### 1. Multi-Model Deployment

```yaml
# docker-compose-multi-model.yml
services:
  vllm-router:
    image: nginx:alpine
    container_name: vllm-router
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - vllm-qwen
      - vllm-phi
    networks:
      - academy-net

  # One model per service. One 11GB GPU hosts roughly one quantized 7B
  # (weights + KV cache) — put services on different GPUs via
  # CUDA_VISIBLE_DEVICES.
  vllm-qwen:
    image: vllm/vllm-openai:v0.30.0   # pinned release (Sep 2026); check releases for newer
    container_name: vllm-qwen
    ports:
      - "8001:8000"
    command: >
      --model Qwen/Qwen3-8B-AWQ
      --gpu-memory-utilization 0.9 --max-model-len 4096 --dtype half
    environment:
      - CUDA_VISIBLE_DEVICES=0
    networks:
      - academy-net

  # phi-2 (2.7B, MIT license) runs fp16 in ~5.5GB — small enough alone,
  # max context defaults to its 2048-token ceiling
  vllm-phi:
    image: vllm/vllm-openai:v0.30.0
    container_name: vllm-phi
    ports:
      - "8003:8000"
    command: >
      --model microsoft/phi-2
      --gpu-memory-utilization 0.9
    environment:
      - CUDA_VISIBLE_DEVICES=1
    networks:
      - academy-net
```

### 2. Load Balancer Configuration (nginx.conf)

```nginx
# nginx.conf — load-balance across REPLICAS OF ONE MODEL.
# Different models are not interchangeable: a request for model X must not
# land on model Y. Use plain LB only within a replica pool, and route
# across models in model-aware code (see the API gateway below).
events {
    worker_connections 1024;
}

http {
    upstream qwen_replicas {
        least_conn;
        server vllm-qwen:8000;
        # add replicas with: docker compose up --scale vllm-qwen=2
        # (remove container_name from the service first — scaling
        # conflicts with a fixed container name)
    }

    server {
        listen 80;
        server_name _;

        location /v1 {
            proxy_pass http://qwen_replicas;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_buffering off;
            # long generations exceed the default 60s upstream timeout
            proxy_read_timeout 300s;
        }

        location /health {
            proxy_pass http://qwen_replicas/health;
        }
    }
}
```

### 3. Monitoring Setup

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus-vllm.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - academy-net
```

```yaml
# prometheus-vllm.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'vllm'
    static_configs:
      - targets: ['vllm-qwen:8000']
    metrics_path: /metrics
```

vLLM serves its own Prometheus metrics at `/metrics` on the API port — no
sidecar exporter is needed. Key series (V1 engine):

```text
vllm:num_requests_running / vllm:num_requests_waiting   gauges
vllm:kv_cache_usage_perc      KV budget saturation (sustained ~1.0 = raise
                              gpu_memory_utilization or cut max_model_len)
vllm:num_preemptions_total    over-budget sequences preempted and recomputed
rate(vllm:prompt_tokens_total[5m])       prompt throughput
rate(vllm:generation_tokens_total[5m])   generation throughput
vllm:time_to_first_token_seconds,
vllm:e2e_request_latency_seconds         latency histograms (histogram_quantile
                                         for p50/p90/p99)
```

### 4. API Gateway with Authentication

```python
# api_gateway.py
from fastapi import FastAPI, HTTPException, Request, Response
from httpx import AsyncClient
import os

app = FastAPI()

# Route by the full repo name the server was started with — the "model"
# field in requests carries exactly that name
VLLM_ENDPOINTS = {
    "Qwen/Qwen3-8B-AWQ": "http://vllm-qwen:8000/v1",
    "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4": "http://vllm-llama:8000/v1",
}
DEFAULT_ENDPOINT = VLLM_ENDPOINTS["Qwen/Qwen3-8B-AWQ"]

# Drop empty entries: with API_KEYS unset, "".split(",") yields [""] —
# an empty-key entry would let requests without an Authorization
# header authenticate
API_KEYS = {k for k in os.getenv("API_KEYS", "").split(",") if k}

async def verify_api_key(request: Request):
    if not API_KEYS:
        return  # auth stays disabled until API_KEYS is configured
    api_key = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    await verify_api_key(request)

    body = await request.json()
    backend = VLLM_ENDPOINTS.get(body.get("model"), DEFAULT_ENDPOINT)

    async with AsyncClient() as client:
        response = await client.post(
            f"{backend}/chat/completions",
            json=body,
            timeout=300.0
        )

    # Forward the upstream content-type — reading the body with .json()
    # would collapse a streaming (SSE) response into one blob; streaming
    # requests need a StreamingResponse passthrough (httpx stream +
    # aiter_raw)
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )
```

## Performance Benchmarks

### Expected Performance (11GB-class GPU)

```text
Aggregate throughput on one 11GB GPU — illustrative ranges; measure on
your own hardware with the concurrency techniques below.

Model              Quant      Context    Aggregate tok/s
──────────────────────────────────────────────────────────
Qwen3-8B           AWQ 4-bit  2048       ~40-80
Llama-3.1-8B       AWQ 4-bit  2048       ~30-60
Phi-2              fp16       2048       ~60-100 (2.7B weights)
Llama-3.1-8B       fp16       —          does not fit 11GB (~16GB weights)
Mixtral-8x7B       4-bit      —          does not fit 11GB (~26GB weights)

Per-stream latency stays in the single-digit tok/s; continuous batching
multiplies aggregate throughput roughly with concurrency until the KV
cache saturates (watch vllm:kv_cache_usage_perc).
```

### Throughput Optimization Tips

```python
# Send requests concurrently — server-side continuous batching fills
# the GPU automatically
import asyncio
import os

from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.environ["VLLM_API_KEY"],
)

async def ask(question: str) -> str:
    response = await client.chat.completions.create(
        model="Qwen/Qwen3-8B-AWQ",
        messages=[{"role": "user", "content": question}],
        max_tokens=256,
    )
    return response.choices[0].message.content

async def main():
    questions = ["What is AI?", "Explain ML.", "Define neural networks."]
    answers = await asyncio.gather(*(ask(q) for q in questions))

asyncio.run(main())

# chat.completions.create takes ONE conversation per call — putting
# several user messages into a single messages list is not batching;
# the parallelism comes from concurrent requests, not message lists.
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```text
Error: CUDA out of memory
```

**Solutions:**
```bash
# Serve a pre-quantized checkpoint — fp16 7B weights (~15GB) are over
# budget; --quantization awq is auto-detected from the checkpoint config
--model Qwen/Qwen3-8B-AWQ

# Shorter sequences shrink the KV cache
--max-model-len 2048

# Cap concurrent sequences
--max-num-seqs 32

# Only when other processes share the GPU:
--gpu-memory-utilization 0.8
```

#### 2. Slow First Request

```text
The first request after startup takes 10+ seconds
```

**Why:** startup includes a warmup dummy run and CUDA graph capture, and
early requests still pay for lazily-compiled kernels. There is no
`--preload-model` flag — readiness is signalled by `/health` returning 200.

**Solutions:**
```bash
# Gate traffic on health before sending real requests
curl http://localhost:8000/health   # 200 = ready

# Diagnose startup cost only — keep CUDA graphs on in production,
# enforce_eager disables them and slows steady-state serving:
--enforce-eager
```

#### 3. High Latency

```text
P95 latency > 500ms
```

**Solutions:**
```bash
# Reduce concurrent requests
--max-num-seqs 32

# Use smaller context
--max-model-len 2048

# Shared system prompts: prefix caching avoids recomputation
# (already on by default on the V1 engine)

# Smaller model for latency-bound paths
--model microsoft/phi-2
```

## Quick Start

```bash
# 1. Pull the vLLM OpenAI-compatible server image (pinned release; check releases for newer)
docker pull vllm/vllm-openai:v0.30.0

# 2. Start the server — the pre-quantized AWQ checkpoint fits an 11GB GPU
#    (fp16 7B weights need ~15GB and would OOM)
docker run -d --gpus all \
  -p 8000:8000 \
  --name vllm-qwen \
  vllm/vllm-openai:v0.30.0 \
  --model Qwen/Qwen3-8B-AWQ \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096

# 3. Test with curl (no --api-key above, so no auth is required)
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen3-8B-AWQ", "messages": [{"role": "user", "content": "Hello!"}]}'

# 4. Test with Python
uv pip install openai
python -c "from openai import OpenAI; client = OpenAI(base_url='http://localhost:8000/v1', api_key='dummy'); print(client.chat.completions.create(model='Qwen/Qwen3-8B-AWQ', messages=[{'role': 'user', 'content': 'Hello!'}]).choices[0].message.content)"
```


---

## Summary

vLLM in production is PagedAttention plus continuous batching: the KV cache is segmented into fixed-size pages so fragmentation disappears, and the GPU stays fed across concurrent requests. This guide deployed it on an 11GB class GPU under one standing constraint - fp16 7B does not fit, so every runnable example serves a pre-quantized AWQ checkpoint. It covered the architecture, deployment options, the configuration guide, client usage examples, advanced configuration, measured performance benchmarks, troubleshooting, and a quick start to get serving first. The practice it encodes: deploy from the quick start, tune from the benchmarks, and never serve fp16 on 11GB.

## References

### Related Minder Academy Documents

- [1404: Text Generation Inference (TGI) Deployment Guide](1404-TGI-Deployment-Guide.md)

---

## Next Steps

- Continue with: **[1404-TGI-Deployment-Guide.md](./1404-TGI-Deployment-Guide.md)** — legacy
  reference only: the TGI repo was archived on GitHub (read-only) in March 2026; new production
  deployments default to vLLM (this guide)

---

**Related:**

- [1402: vLLM and TGI](../1402-vLLM-and-TGI.md)
- [1401: Ollama Enterprise](../1401-Ollama-Enterprise.md)
- [4101: GGUF Physics](../../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- [1302: GPU Scheduler](../../1300-kubernetes/1302-GPU-Scheduler.md)
- [1501: Monitoring and Observability](../../1500-monitoring/1501-Monitoring-and-Observability.md)
