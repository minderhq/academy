# 1405: Text Generation Inference (TGI) Deployment Guide

## Abstract
Complete deployment guide for Text Generation Inference (TGI), Hugging Face's high-performance LLM serving engine, optimized for PROJECT-OMEGA infrastructure.

## TGI vs vLLM Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TGI vs vLLM Feature Comparison                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Feature                    │ TGI           │ vLLM          │          │
│  ──────────────────────────────┼──────────────┼──────────────┤          │
│  OpenAI API Compatibility    │ ✅ Full       │ ✅ Full      │          │
│  PagedAttention               │ ✅ Native     │ ✅ Native    │          │
│  Flash Attention 2            │ ✅ Native     │ ✅ Native    │          │
│  Batching                     │ ✅ Dynamic    │ ✅ Continuous│          │
│  Quantization (AWQ/GPTQ)      │ ✅ Native     │ ✅ AWQ only  │          │
│  Speculative Decoding         │ ✅ Native     │ ✅ Experimental│       │
│  LoRA Adapters                │ ✅ Native     │ ✅ Via PEFT   │          │
│  Tensor Parallelism           │ ✅ Multi-GPU  │ ✅ Multi-GPU  │          │
│  SHARDING                     │ ✅ Native     │ ✅ Native    │          │
│  Streaming                    │ ✅ Server-Sent │ ✅ Server-Sent│         │
│  JSON Mode                    │ ✅ Native     │ ✅ Regex     │          │
│  Grammar Constrained          │ ✅ Native     │ ❌            │          │
│  Tool Calling                 │ ✅ Native     │ ❌            │          │
│  Easy Docker Setup            │ ✅ One-line   │ ✅ One-line  │          │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Single Command Deployment

```bash
# Deploy Mistral-7B with all optimizations
model=mistralai/Mistral-7B-Instruct-v0.2

docker run -d --gpus all \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id $model \
  --quantize awq \
  --max-total-tokens 8192 \
  --max-batch-prefill-tokens 4096 \
  --shard 1 \
  --dtype float16
```

## Configuration Guide

### Basic Configuration

```bash
# Minimum viable configuration
docker run -d --gpus all \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2
```

### Optimized Configuration (11GB-class GPU)

```bash
# Memory-optimized for 11GB VRAM
docker run -d --gpus all \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2 \
  \
  # Quantization (reduces VRAM by ~4GB)
  --quantize awq \
  \
  # Context limits
  --max-total-tokens 8192 \
  --max-batch-total-tokens 16384 \
  --max-batch-prefill-tokens 4096 \
  \
  # Memory optimization
  --max-batch-size 16 \
  --max-waiting-tokens 32 \
  \
  # Performance
  --dtype float16 \
  --shard 1 \
  \
  # Features
  --enable-kv-cache-slicing \
  --enable-prefix-caching \
  \
  # API
  --hostname 0.0.0.0 \
  --port 8080
```

## Parameter Reference

| Parameter | Default | Description | 11GB-class GPU Value |
|-----------|---------|-------------|-------------------|
| `--model-id` | - | Model name/path | mistralai/Mistral-7B-Instruct-v0.2 |
| `--quantize` | None | Quantization (awq/gptq/bnb) | awq (for 7B+ models) |
| `--max-total-tokens` | Auto | Max total tokens (prompt + gen) | 8192 |
| `--max-batch-total-tokens` | Auto | Max tokens in batch | 16384 |
| `--max-batch-prefill-tokens` | Auto | Max tokens for prefill | 4096 |
| `--max-batch-size` | Auto | Max concurrent requests | 16 |
| `--dtype` | auto | Data type | float16 |
| `--shard` | Auto | Tensor parallelism (GPU count) | 1 |
| `--enable-kv-cache-slicing` | False | Slice KV cache across GPUs | True |
| `--enable-prefix-caching` | False | Cache shared prompts | True |

## Deployment Options

### Option 1: Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: "3.8"

services:
  tgi-mistral:
    image: ghcr.io/huggingface/text-generation-inference:latest
    container_name: project-omega-tgi-mistral
    ports:
      - "8080:80"
    environment:
      - MODEL_ID=mistralai/Mistral-7B-Instruct-v0.2
      - QUANTIZE=awq
      - MAX_TOTAL_TOKENS=8192
      - MAX_BATCH_TOTAL_TOKENS=16384
      - MAX_BATCH_PREFILL_TOKENS=4096
      - DTYPE=float16
      - ENABLE_PREFIX_CACHING=true
      - ENABLE_KV_CACHE_SLICING=true
    command: >
      --model-id ${MODEL_ID}
      --quantize ${QUANTIZE}
      --max-total-tokens ${MAX_TOTAL_TOKENS}
      --max-batch-total-tokens ${MAX_BATCH_TOTAL_TOKENS}
      --max-batch-prefill-tokens ${MAX_BATCH_PREFILL_TOKENS}
      --dtype ${DTYPE}
      --enable-prefix-caching ${ENABLE_PREFIX_CACHING}
      --enable-kv-cache-slicing ${ENABLE_KV_CACHE_SLICING}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - project-omega-net
    volumes:
      - /srv/models/tgi:/data
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  project-omega-net:
    external: true
```

### Option 2: Kubernetes Deployment

```yaml
# k8s-tgi-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tgi-mistral
  namespace: project-omega
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tgi-mistral
  template:
    metadata:
      labels:
        app: tgi-mistral
    spec:
      containers:
      - name: tgi
        image: ghcr.io/huggingface/text-generation-inference:latest
        ports:
        - containerPort: 80
          name: http
        env:
        - name: MODEL_ID
          value: "mistralai/Mistral-7B-Instruct-v0.2"
        - name: QUANTIZE
          value: "awq"
        - name: MAX_TOTAL_TOKENS
          value: "8192"
        - name: ENABLE_PREFIX_CACHING
          value: "true"
        args:
        - --model-id=$(MODEL_ID)
        - --quantize=$(QUANTIZE)
        - --max-total-tokens=$(MAX_TOTAL_TOKENS)
        - --enable-prefix-caching=$(ENABLE_PREFIX_CACHING)
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
          mountPath: /data
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: tgi-model-pvc
      nodeSelector:
        gpu: "true"

---
apiVersion: v1
kind: Service
metadata:
  name: tgi-mistral
  namespace: project-omega
spec:
  selector:
    app: tgi-mistral
  ports:
  - port: 80
    targetPort: 80
    name: http
  type: ClusterIP
```

## Client Usage Examples

### Python Client

```python
# tgi_client.py
import requests
import json

class TGIClient:
    """TGI client with OpenAI-compatible API"""

    def __init__(self, base_url: str = "http://192.168.1.100:8080"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.95,
        do_sample: bool = True,
        stream: bool = False,
    ):
        """Generate text"""

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": do_sample,
            },
            "stream": stream,
        }

        if stream:
            return self._stream_generate(payload)
        else:
            response = requests.post(
                f"{self.base_url}/generate",
                headers=self.headers,
                json=payload,
            )
            return response.json()[0]["generated_text"]

    def _stream_generate(self, payload: dict):
        """Stream generation"""

        response = requests.post(
            f"{self.base_url}/generate_stream",
            headers=self.headers,
            json=payload,
            stream=True,
        )

        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                yield chunk["token"]["text"]

    def chat(
        self,
        messages: list,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False,
    ):
        """Chat completion (OpenAI compatible)"""

        # Convert to TGI format
        prompt = self._format_chat(messages)

        return self.generate(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            stream=stream,
        )

    def _format_chat(self, messages: list) -> str:
        """Format chat messages"""

        formatted = []
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"]
            formatted.append(f"{role}: {content}")

        formatted.append("Assistant:")
        return "\n".join(formatted)


# Usage
client = TGIClient()

# Simple generation
response = client.generate("Explain quantum computing:", max_new_tokens=100)
print(response)

# Chat completion
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Docker?"},
]
response = client.chat(messages, max_new_tokens=200)
print(response)

# Streaming
for token in client.generate("Tell me a story:", stream=True):
    print(token, end="", flush=True)
```

### cURL Examples

```bash
# Health check
curl http://192.168.1.100:8080/health

# Model info
curl http://192.168.1.100:8080/model

# Generate
curl -X POST http://192.168.1.100:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "Explain AI:",
    "parameters": {
      "max_new_tokens": 100,
      "temperature": 0.7
    }
  }'

# Stream
curl -X POST http://192.168.1.100:8080/generate_stream \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "Count to 10:",
    "parameters": {"max_new_tokens": 50}
  }'

# OpenAI compatible (v1 endpoint)
curl -X POST http://192.168.1.100:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistralai/Mistral-7B-Instruct-v0.2",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 100
  }'
```

### JavaScript/TypeScript Client

```typescript
// tgi_client.ts
interface GenerateOptions {
  max_new_tokens?: number;
  temperature?: number;
  top_p?: number;
  do_sample?: boolean;
}

class TGIClient {
  constructor(private baseUrl: string = "http://192.168.1.100:8080") {}

  async generate(
    prompt: string,
    options: GenerateOptions = {}
  ): Promise<string> {
    const response = await fetch(`${this.baseUrl}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        inputs: prompt,
        parameters: {
          max_new_tokens: 256,
          temperature: 0.7,
          top_p: 0.95,
          do_sample: true,
          ...options,
        },
      }),
    });

    const data = await response.json();
    return data[0].generated_text;
  }

  async *generateStream(
    prompt: string,
    options: GenerateOptions = {}
  ): AsyncGenerator<string> {
    const response = await fetch(`${this.baseUrl}/generate_stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        inputs: prompt,
        parameters: { ...options },
      }),
    });

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n").filter(Boolean);

      for (const line of lines) {
        const data = JSON.parse(line);
        yield data.token.text;
      }
    }
  }
}

// Usage
const client = new TGIClient();

// Simple generation
const response = await client.generate("Explain TypeScript:");
console.log(response);

// Streaming
for await (const token of client.generateStream("Write a poem:")) {
  process.stdout.write(token);
}
```

## Advanced Features

### 1. LoRA Adapters

```bash
# Deploy with LoRA adapter support
docker run -d --gpus all \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2 \
  --lora-modules /data/lora \
  --lora-adapter lora-chat:./lora-chat-adapter \
  --lora-adapter lora-code:./lora-code-adapter
```

```python
# Use specific LoRA adapter
payload = {
    "inputs": "Write Python code:",
    "parameters": {
        "max_new_tokens": 256,
        "adapter_id": "lora-code",  # Use code adapter
    },
}
```

### 2. Speculative Decoding

```bash
# Enable speculative decoding
docker run -d --gpus all \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2 \
  --speculative-decoding-model microsoft/phi-2 \
  --num-speculative-tokens 5
```

### 3. Grammar Constrained Generation

```python
# JSON output with grammar
import json

grammar = json.dumps({
    "type": "json",
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
    },
})

payload = {
    "inputs": "Generate a person profile:",
    "parameters": {
        "max_new_tokens": 128,
        "grammar": grammar,
    },
}

response = requests.post(
    "http://localhost:8080/generate",
    json=payload,
)
result = response.json()[0]["generated_text"]
print(result)  # Guaranteed valid JSON
```

### 4. Tool Calling

```python
# Tool calling with TGI
tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
]

payload = {
    "inputs": "Search for recent AI news",
    "parameters": {
        "max_new_tokens": 256,
        "tools": tools,
        "tool_choice": "auto",
    },
}
```

## Performance Tuning

### Batch Size Optimization

```python
# Test optimal batch size
import time
import requests

def benchmark_batch_size(batch_size: int):
    """Benchmark different batch sizes"""

    prompts = ["Hello!"] * batch_size

    start = time.time()
    responses = [
        requests.post(
            "http://localhost:8080/generate",
            json={"inputs": p, "parameters": {"max_new_tokens": 50}},
        )
        for p in prompts
    ]
    elapsed = time.time() - start

    tokens_per_sec = (50 * batch_size) / elapsed
    return tokens_per_sec


for bs in [1, 2, 4, 8, 16]:
    tps = benchmark_batch_size(bs)
    print(f"Batch {bs:2d}: {tps:6.1f} tokens/sec")
```

### Prefix Caching

```bash
# Enable prefix caching for shared system prompts
docker run -d --gpus all \
  -p 8080:80 \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2 \
  --enable-prefix-caching \
  --max-batch-size 32
```

## Monitoring

### Metrics Endpoint

```bash
# TGI exposes metrics at /metrics
curl http://localhost:8080/metrics

# Key metrics:
# - tgi_cache_token_count: KV cache size
# - tgi_cache_hit_rate: KV cache efficiency
# - tgi_request_duration: Request latency
# - tgi_request_success: Total requests
# - tgi_batch_inference_count: Batches processed
```

### Prometheus Integration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tgi'
    static_configs:
      - targets: ['tgi-mistral:80']
    metrics_path: /metrics
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```
Error: CUDA out of memory
```

**Solutions:**
```bash
# Reduce max total tokens
--max-total-tokens 4096

# Enable quantization
--quantize awq

# Reduce batch size
--max-batch-size 4
```

#### 2. Slow First Request

```
First request takes 10+ seconds
```

**Solutions:**
```bash
# Use AWQ quantization (faster loading)
--quantize awq

# Increase warmup
--max-batch-prefill-tokens 2048
```

#### 3. Low Throughput

```
Less than 10 tokens/sec
```

**Solutions:**
```bash
# Enable prefix caching
--enable-prefix-caching

# Increase batch size
--max-batch-size 16

# Use smaller context
--max-total-tokens 4096
```

## Quick Start

```bash
# 1. Pull latest TGI image
docker pull ghcr.io/huggingface/text-generation-inference:latest

# 2. Start TGI server
docker run -d --gpus all \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2 \
  --quantize awq

# 3. Test generation
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello!", "parameters": {"max_new_tokens": 50}}'

# 4. Test with Python
pip install requests
python -c "import requests; print(requests.post('http://localhost:8080/generate', json={'inputs': 'Hello!', 'parameters': {'max_new_tokens': 50}}).json()[0]['generated_text'])"
```


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [1402: vLLM and TGI](../1402-vLLM-and-TGI.md)
- [1404: vLLM Production Deployment](./1404-vLLM-Production-Deployment.md)
- [1401: Ollama Enterprise](../1401-Ollama-Enterprise.md)
- [4201: Context Window Physics](../../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [1501: Monitoring and Observability](../../1500-Monitoring/1501-Monitoring-and-Observability.md)
