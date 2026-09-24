---
Document ID: 1404
Title: "1404: vLLM Production Deployment Guide"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# 1404: vLLM Production Deployment Guide

## Abstract
Complete production deployment guide for vLLM (Virtual Large Language Model) high-throughput inference engine on AI Engineering Curriculum infrastructure.

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
│  │   - KV cache hit rate                                         │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Deployment Options

### Option 1: Docker Compose (Recommended for Single GPU)

```yaml
# docker-compose.yml
version: "3.8"

services:
  vllm-mistral:
    image: vllm/vllm-openai:latest
    container_name: ai-engineering-curriculum-vllm-mistral
    ports:
      - "8000:8000"
    command: >
      --model mistralai/Mistral-7B-Instruct-v0.2
      --tensor-parallel-size 1
      --gpu-memory-utilization 0.9
      --max-model-len 4096
      --dtype float16
      --host 0.0.0.0
      --port 8000
      --api-key optional-api-key
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - VLLM_USAGE_SOURCE=production
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ai-engineering-curriculum-net
    volumes:
      - /srv/models/vllm:/root/.cache/huggingface
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  vllm-llama:
    image: vllm/vllm-openai:latest
    container_name: ai-engineering-curriculum-vllm-llama
    ports:
      - "8001:8000"
    command: >
      --model meta-llama/Llama-2-7b-chat-hf
      --tensor-parallel-size 1
      --gpu-memory-utilization 0.9
      --max-model-len 4096
      --dtype float16
      --host 0.0.0.0
      --port 8000
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
    networks:
      - ai-engineering-curriculum-net
    depends_on:
      - vllm-mistral

networks:
  ai-engineering-curriculum-net:
    external: true
```

### Option 2: K3s Deployment (for Cluster)

```yaml
# k8s-vllm-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-config
  namespace: ai-engineering-curriculum
data:
  MODEL_NAME: "mistralai/Mistral-7B-Instruct-v0.2"
  TENSOR_PARALLEL_SIZE: "1"
  GPU_MEMORY_UTILIZATION: "0.9"
  MAX_MODEL_LEN: "4096"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-mistral
  namespace: ai-engineering-curriculum
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm-mistral
  template:
    metadata:
      labels:
        app: vllm-mistral
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: MODEL_NAME
          valueFrom:
            configMapKeyRef:
              name: vllm-config
              key: MODEL_NAME
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        command: ["/bin/bash", "-c"]
        args:
          - |
            vllm serve $(MODEL_NAME) \
              --tensor-parallel-size $(TENSOR_PARALLEL_SIZE) \
              --gpu-memory-utilization $(GPU_MEMORY_UTILIZATION) \
              --max-model-len $(MAX_MODEL_LEN) \
              --dtype float16 \
              --host 0.0.0.0 \
              --port 8000
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
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      nodeSelector:
        gpu: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-mistral
  namespace: ai-engineering-curriculum
spec:
  selector:
    app: vllm-mistral
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
  namespace: ai-engineering-curriculum
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: nfs-standard
  resources:
    requests:
      storage: 50Gi
```

## Configuration Guide

### Key Parameters Explained

| Parameter | Default | Description | 11GB-class GPU Recommended |
|-----------|---------|-------------|------------------------|
| `--tensor-parallel-size` | 1 | Number of GPUs for tensor parallelism | 1 (single GPU) |
| `--gpu-memory-utilization` | 0.9 | Fraction of GPU memory to use | 0.85 (leave room for KV cache) |
| `--max-model-len` | 4096 | Maximum sequence length | 4096 (balance quality/speed) |
| `--dtype` | auto | Data type (float16/bfloat16) | float16 (better performance) |
| `--quantization` | None | 4-bit/8-bit quantization | awq (if memory constrained) |
| `--block-size` | 16 | KV cache block size | 16 (default) |
| `--enable-prefix-caching` | False | Cache shared prefixes | True (for system prompts) |
| `--max-num-seqs` | 256 | Max concurrent sequences | 128 (limited by VRAM) |

### Performance Tuning Configuration

```bash
# High Throughput Configuration
--model mistralai/Mistral-7B-Instruct-v0.2 \
--gpu-memory-utilization 0.95 \
--max-model-len 2048 \
--max-num-seqs 256 \
--enable-prefix-caching \
--dtype float16

# Long Context Configuration
--model mistralai/Mistral-7B-Instruct-v0.2 \
--gpu-memory-utilization 0.85 \
--max-model-len 8192 \
--max-num-seqs 32 \
--block-size 32 \
--dtype float16

# Memory Optimized Configuration (for 11GB VRAM)
--model mistralai/Mistral-7B-Instruct-v0.2 \
--quantization awq \
--gpu-memory-utilization 0.9 \
--max-model-len 4096 \
--max-num-seqs 64 \
--dtype float16
```

## Client Usage Examples

### Python Client

```python
# vllm_client.py
from openai import OpenAI

# Initialize client
client = OpenAI(
    base_url="http://192.168.1.100:8000/v1",
    api_key="optional-api-key",
)

# Chat completion
response = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[
        {"role": "system", "content": "You are a helpful assistant for ai-engineering-curriculum."},
        {"role": "user", "content": "Explain quantum computing in simple terms."},
    ],
    max_tokens=512,
    temperature=0.7,
    stream=True,
)

# Stream response
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# Non-streaming response
response = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
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

# Chat completion
curl -X POST http://192.168.1.100:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer optional-api-key" \
  -d '{
    "model": "mistralai/Mistral-7B-Instruct-v0.2",
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
    "model": "mistralai/Mistral-7B-Instruct-v0.2",
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
  apiKey: 'optional-api-key',
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'mistralai/Mistral-7B-Instruct-v0.2',
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
    model: 'mistralai/Mistral-7B-Instruct-v0.2',
    messages: [
      { role: 'user', 'content': 'Write a short poem.' },
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
      - vllm-mistral
      - vllm-llama
      - vllm-phi
    networks:
      - ai-engineering-curriculum-net

  vllm-mistral:
    image: vllm/vllm-openai:latest
    container_name: vllm-mistral
    ports:
      - "8001:8000"
    command: --model mistralai/Mistral-7B-Instruct-v0.2 --port 8000
    networks:
      - ai-engineering-curriculum-net

  vllm-llama:
    image: vllm/vllm-openai:latest
    container_name: vllm-llama
    ports:
      - "8002:8000"
    command: --model meta-llama/Llama-2-7b-chat-hf --port 8000
    networks:
      - ai-engineering-curriculum-net

  vllm-phi:
    image: vllm/vllm-openai:latest
    container_name: vllm-phi
    ports:
      - "8003:8000"
    command: --model microsoft/phi-2 --port 8000
    networks:
      - ai-engineering-curriculum-net
```

### 2. Load Balancer Configuration (nginx.conf)

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream vllm_backends {
        least_conn;
        server vllm-mistral:8000 weight=3;
        server vllm-llama:8000 weight=2;
        server vllm-phi:8000 weight=1;
    }

    server {
        listen 80;
        server_name _;

        location /v1 {
            proxy_pass http://vllm-backends;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_buffering off;
        }

        location /health {
            proxy_pass http://vllm-backends/health;
        }
    }
}
```

### 3. Monitoring Setup

```yaml
# Add to docker-compose.yml
  prometheus-vllm-exporter:
    image: prom/prometheus:latest
    container_name: prometheus-vllm-exporter
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus-vllm.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - ai-engineering-curriculum-net
```

```yaml
# prometheus-vllm.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'vllm'
    static_configs:
      - targets: ['vllm-mistral:8000']
    metrics_path: /metrics
```

### 4. API Gateway with Authentication

```python
# api_gateway.py
from fastapi import FastAPI, Request, HTTPException
from httpx import AsyncClient
import os

app = FastAPI()

VLLM_ENDPOINTS = {
    "mistral": "http://vllm-mistral:8000/v1",
    "llama": "http://vllm-llama:8000/v1",
}

API_KEYS = os.getenv("API_KEYS", "").split(",")

async def verify_api_key(request: Request):
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    await verify_api_key(request)

    body = await request.json()
    model = body.get("model", "mistral")

    # Route to appropriate backend
    if model in VLLM_ENDPOINTS:
        backend = VLLM_ENDPOINTS[model]
    else:
        backend = VLLM_ENDPOINTS["mistral"]

    async with AsyncClient() as client:
        response = await client.post(
            f"{backend}/chat/completions",
            json=body,
            timeout=300.0
        )

    return response.json()
```

## Performance Benchmarks

### 11GB-class GPU (11GB VRAM) Performance

| Model | Quantization | Max Seq Len | Batch Size | Throughput | Latency (p50) |
|-------|-------------|-------------|------------|------------|---------------|
| Mistral-7B | FP16 | 2048 | 8 | 45 tok/s | 80ms |
| Mistral-7B | AWQ 4-bit | 4096 | 16 | 65 tok/s | 60ms |
| Llama-2-7B | FP16 | 2048 | 8 | 42 tok/s | 85ms |
| Llama-2-7B | AWQ 4-bit | 4096 | 16 | 60 tok/s | 65ms |
| Phi-2 | FP16 | 2048 | 16 | 80 tok/s | 40ms |
| Mixtral-8x7B | AWQ 4-bit | 2048 | 1 | 15 tok/s | 200ms |

### Throughput Optimization Tips

```python
# Batch multiple requests
requests = [
    "What is AI?",
    "Explain ML.",
    "Define neural networks.",
]

responses = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[{"role": "user", "content": req} for req in requests],
)

# Use streaming for faster time-to-first-token
response = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
)
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```text
Error: CUDA out of memory
```

**Solutions:**
```bash
# Reduce max sequence length
--max-model-len 2048

# Reduce batch size
--max-num-seqs 32

# Enable quantization
--quantization awq

# Reduce GPU memory utilization
--gpu-memory-utilization 0.8
```

#### 2. Slow First Request

```text
First request takes 10+ seconds
```

**Solutions:**
```bash
# Enable model preloading
--preload-model

# Increase warmup time
--gpu-memory-utilization 0.85

# Use smaller model for quick starts
--model microsoft/phi-2
```

#### 3: High Latency

```text
P95 latency > 500ms
```

**Solutions:**
```bash
# Reduce concurrent requests
--max-num-seqs 32

# Use smaller context
--max-model-len 2048

# Enable prefix caching
--enable-prefix-caching

# Use faster model
--model mistralai/Mistral-7B-Instruct-v0.2
```

## Quick Start

```bash
# 1. Pull latest vLLM image
docker pull vllm/vllm-openai:latest

# 2. Start vLLM server
docker run -d --gpus all \
  -p 8000:8000 \
  --name vllm-mistral \
  vllm/vllm-openai:latest \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096

# 3. Test with curl
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mistralai/Mistral-7B-Instruct-v0.2", "messages": [{"role": "user", "content": "Hello!"}]}'

# 4. Test with Python
pip install openai
python -c "from openai import OpenAI; client = OpenAI(base_url='http://localhost:8000/v1', api_key='dummy'); print(client.chat.completions.create(model='mistralai/Mistral-7B-Instruct-v0.2', messages=[{'role': 'user', 'content': 'Hello!'}]).choices[0].message.content)"
```


---

## Next Steps

- Continue with: **[1405-TGI-Deployment-Guide.md](./1405-TGI-Deployment-Guide.md)**

---
---

**Related:**
- [1402: vLLM and TGI](../1402-vLLM-and-TGI.md)
- [1401: Ollama Enterprise](../1401-Ollama-Enterprise.md)
- [4101: GGUF Physics](../../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- [1302: GPU Scheduler](../../1300-kubernetes/1302-GPU-Scheduler.md)
- [1501: Monitoring and Observability](../../1500-Monitoring/1501-Monitoring-and-Observability.md)
