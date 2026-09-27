---
Document ID: 1405
Title: "1405: Text Generation Inference (TGI) Deployment Guide"
Last Updated: 2026-09-27
Status: Complete
Difficulty: Intermediate
---

# 1405: Text Generation Inference (TGI) Deployment Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [TGI vs vLLM Comparison](#tgi-vs-vllm-comparison)
- [Quick Start](#quick-start)
- [Configuration Guide](#configuration-guide)
- [Parameter Reference](#parameter-reference)
- [Deployment Options](#deployment-options)
- [Client Usage Examples](#client-usage-examples)
- [Advanced Features](#advanced-features)
- [Performance Tuning](#performance-tuning)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [End-to-End Deployment Walkthrough](#end-to-end-deployment-walkthrough)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Describe TGI's architecture (Rust router, per-shard Python server, launcher) and its archived 2026 status against vLLM
- Deploy TGI from the pinned ghcr image (final release 3.3.7) via docker run, Compose, and Kubernetes with a PVC model cache
- Budget the KV cache from the 128KB/token math and set --max-total-tokens / --max-batch-total-tokens accordingly
- Call the native /generate and SSE /generate_stream APIs plus the OpenAI-compatible /v1/chat/completions endpoint
- Use the advanced features: per-request LoRA adapters, n-gram/Medusa speculative decoding, and grammar-constrained output
- Read the tgi_* Prometheus series and benchmark aggregate throughput with concurrent clients

---

## Abstract

Text Generation Inference (TGI) is Hugging Face's production serving stack: a Rust
HTTP router (continuous batching, validation, OpenAI-compatible endpoints) in front
of a Python `text-generation-server` process per GPU shard, all started by the
`text-generation-launcher` binary. This guide deploys TGI on an 11GB-class GPU.

The constraint that shapes every command below: **fp16 7B weights need ~14GB and do
not fit 11GB**. All runnable examples therefore use a *pre-quantized* AWQ
checkpoint (TheBloke/Mistral-7B-Instruct-v0.2-AWQ, ~3.5GB weights, ungated).
Pre-quantized checkpoints declare their quantization in `config.json`, so TGI
auto-detects it — no `--quantize`, no `--dtype`.

Versions matter with TGI: the launcher CLI has changed across major versions
(speculative decoding, prefix-caching flags). Everything here matches TGI 3.x,
verified against the `huggingface/text-generation-inference` source.

Status (Sep 2026): the TGI repository was archived on GitHub (read-only) in
March 2026; v3.3.7 was its final release. Everything in this guide remains
runnable on the archived codebase, but the engine is maintenance-only — treat
this as legacy-deployment reference and default new production deployments to
vLLM (see the comparison below and guide 1404).

## TGI vs vLLM Comparison

| Feature | TGI 3.x | vLLM |
|---------|---------|------|
| Continuous batching | ✅ | ✅ |
| Flash Attention | ✅ (default: flashinfer backend) | ✅ |
| PagedAttention | ❌ (TGI's KV cache is block-allocated, not paged) | ✅ |
| Multi-GPU (tensor/shard parallel) | ✅ `--num-shard` / NCCL | ✅ tensor parallel |
| Quantization | AWQ, GPTQ, EETQ, bitsandbytes, Marlin, ExL2, compressed-tensors, FP8 | Same families plus more |
| Speculative decoding | ✅ `--speculate` (n-gram or Medusa heads) | ✅ (draft models, n-gram, MTP) |
| LoRA adapters | ✅ served from the launcher (`--lora-adapters`) | ✅ |
| Prefix caching | ✅ on by default (flashinfer; off with LoRA) | ✅ on by default (V1) |
| Structured output | ✅ JSON/regex grammar (Outlines) | ✅ guided JSON/regex (Outlines/xgrammar) |
| Tool calling | ✅ via `/v1/chat/completions` | ✅ via `/v1/chat/completions` |
| OpenAI-compatible API | ✅ | ✅ |

Both engines are Apache 2.0. With the TGI repository archived (read-only) in
March 2026, vLLM is the default for new production deployments; TGI remains a
valid maintenance choice for existing Hugging Face-native fleets, while vLLM
additionally offers PagedAttention-level KV tuning and a wider plugin surface
(see [1404](1404-vLLM-Production-Deployment.md)).

## Quick Start

### Single Command Deployment

```bash
# Deploy a pre-quantized AWQ checkpoint that fits 11GB
model=TheBloke/Mistral-7B-Instruct-v0.2-AWQ

docker run -d --gpus all \
  --shm-size 1g \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:3.3.7 \
  --model-id $model \
  --max-total-tokens 8192 \
  --max-batch-prefill-tokens 4096
```

Notes:

- **`-p 8080:80`**: the official image sets `ENV PORT=80`, and the launcher reads
  `PORT` from the environment — so the server listens on container port 80 even
  though the launcher CLI default (outside Docker) is 3000.
- **`--shm-size 1g`**: NCCL shared-memory headroom; the upstream quick start
  recommends it.
- **No `--quantize`/`--dtype`**: the checkpoint is pre-quantized AWQ and
  `--dtype` is rejected alongside `--quantize`.

## Configuration Guide

### Basic Configuration

```bash
# Minimum viable configuration
docker run -d --gpus all \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:3.3.7 \
  --model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ
```

### Optimized Configuration (11GB-class GPU)

```bash
# Comments stay OUTSIDE the command: inside a backslash-continued line a
# leading # would swallow every flag after it.
docker run -d --gpus all \
  --shm-size 1g \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:3.3.7 \
  --model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ \
  --max-total-tokens 8192 \
  --max-batch-total-tokens 16384 \
  --max-batch-prefill-tokens 4096 \
  --max-batch-size 16 \
  --max-waiting-tokens 20 \
  --waiting-served-ratio 0.3 \
  --max-concurrent-requests 128 \
  --hostname 0.0.0.0 \
  --num-shard 1
```

Context limits: see the KV budget math under Performance Tuning. The container
port stays 80 (`PORT` env from the image).

There is no `--enable-prefix-caching` flag: prefix caching is controlled by the
`PREFIX_CACHING` environment variable and is **on by default** in TGI 3.x (and is
switched off automatically for vision-language models, encoder-decoder models, and
when LoRA adapters are served).

## Parameter Reference

Defaults verified against the TGI 3.x launcher source.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--model-id` | required | Hub repo id or local path |
| `--num-shard` | auto (GPU count) | Shard count (launcher flag is `--num-shard`, not `--shard`) |
| `--quantize` | None (auto for pre-quantized repos) | `awq`, `gptq`, `eetq`, `bitsandbytes`, `bitsandbytes-nf4`, `exl2`, `marlin`, `compressed-tensors`, `fp8` |
| `--dtype` | model default (fp16/bf16) | `float16` or `bfloat16`; **cannot be combined with `--quantize`** |
| `--max-total-tokens` | computed at warmup | Per-request ceiling: prompt + generated tokens |
| `--max-batch-total-tokens` | computed at warmup | Token budget of one batch — main KV-cache knob |
| `--max-batch-prefill-tokens` | computed | Token budget of one prefill pass |
| `--max-batch-size` | None (no hard cap) | Max requests per batch; for hardware that can't do unpadded batches |
| `--max-concurrent-requests` | 128 | Router-side concurrency limit (excess requests get HTTP 429) |
| `--max-waiting-tokens` | 20 | Queue fills this many tokens before forming a new batch |
| `--waiting-served-ratio` | 0.3 | Waiting/running ratio above which new batches form eagerly |
| `--hostname` | 0.0.0.0 | Bind address |
| `--port` | 3000 (`PORT` env wins) | In the official image `PORT=80`, so the container listens on 80 |
| `--lora-adapters` | empty | `id=path[@revision]` pairs, comma-separated |
| `--speculate` | off | N tokens to speculate (n-gram by default; Medusa heads used if present) |
| `--kv-cache-dtype` | model dtype | `fp8_e4m3fn` or `fp8_e5m2` on CUDA |

## Deployment Options

### Option 1: Docker Compose (Recommended)

```yaml
# docker-compose.yml
#
# command: passes flags to the image entrypoint (tgi-entrypoint.sh execs
# text-generation-launcher "$@"). These are literal values — compose
# interpolates ${VAR} from your HOST environment, NOT from the service's
# environment: block, so never route flags through variables here.

services:
  tgi-mistral:
    image: ghcr.io/huggingface/text-generation-inference:3.3.7
    container_name: ai-engineering-curriculum-tgi-mistral
    ports:
      - "8080:80"
    shm_size: "1g"
    command: >
      --model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ
      --max-total-tokens 8192
      --max-batch-total-tokens 16384
      --max-batch-prefill-tokens 4096
      --max-batch-size 16
      --max-concurrent-requests 128
      --hostname 0.0.0.0
    # Gated models need a token; TheBloke AWQ repos are ungated:
    # environment:
    #   HF_TOKEN: ${HF_TOKEN}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      # First boot downloads ~3.5GB of weights; give the probe time to start
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 300s
    networks:
      - ai-engineering-curriculum-net
    volumes:
      - /srv/models/tgi:/data
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  ai-engineering-curriculum-net:
    external: true
```

The image sets `HF_HOME=/data`, so the bind-mounted volume caches downloaded
weights across container restarts.

### Option 2: Kubernetes Deployment

```yaml
# k8s-tgi-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tgi-mistral
  namespace: ai-engineering-curriculum
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
        image: ghcr.io/huggingface/text-generation-inference:3.3.7
        # args (not command:) — command: would replace the
        # text-generation-launcher entrypoint
        args:
          - --model-id
          - TheBloke/Mistral-7B-Instruct-v0.2-AWQ   # pre-quantized AWQ:
                                                    # quantization is
                                                    # auto-detected — no
                                                    # --quantize/--dtype
          - --max-total-tokens
          - "8192"
          - --max-batch-total-tokens
          - "16384"
          - --max-batch-prefill-tokens
          - "4096"
          - --max-concurrent-requests
          - "128"
        ports:
        - containerPort: 80
          name: http
        # TheBloke/Llama-2-7B-AWQ-style repos are ungated, so no token is
        # needed. For a gated model, add:
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
            memory: "12Gi"
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
        accelerator: nvidia   # must match the GPU node label (see 1301)

---
apiVersion: v1
kind: Service
metadata:
  name: tgi-mistral
  namespace: ai-engineering-curriculum
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
import json
import requests

class TGIClient:
    """TGI client covering both the native and OpenAI-compatible APIs."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.95,
        do_sample: bool = True,
    ) -> str:
        """Generate text (native API). Returns the generated continuation."""
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": do_sample,
            },
        }
        # /generate returns an OBJECT: {"generated_text": "...", "details": {...}}
        response = requests.post(f"{self.base_url}/generate", json=payload)
        response.raise_for_status()
        return response.json()["generated_text"]

    def stream_generate(self, prompt: str, max_new_tokens: int = 256):
        """Stream generation (native API, Server-Sent Events)."""
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": max_new_tokens},
        }
        response = requests.post(
            f"{self.base_url}/generate_stream",
            json=payload,
            stream=True,
        )
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            yield chunk["token"]["text"]

    def chat(self, messages: list, max_tokens: int = 256, temperature: float = 0.7) -> str:
        """Chat via the OpenAI-compatible endpoint.

        The server applies the model's real chat template — no manual
        "User:/Assistant:" formatting, which is wrong for Mistral and
        every other templated model.
        """
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "tgi",               # single-model server; name is
                                              # accepted but not routed
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


# Usage
client = TGIClient()

# Simple generation
print(client.generate("Explain quantum computing:", max_new_tokens=100))

# Chat completion
print(client.chat([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Docker?"},
], max_tokens=200))

# Streaming
for token in client.stream_generate("Tell me a story:", max_new_tokens=120):
    print(token, end="", flush=True)
```

### cURL Examples

```bash
# Health check (returns 200 once the model is ready)
curl http://localhost:8080/health

# Model info: model id, dtype, device, grammar support
curl http://localhost:8080/info

# Generate — response is {"generated_text": "...", "details": {...}}
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "Explain AI:",
    "parameters": {
      "max_new_tokens": 100,
      "temperature": 0.7
    }
  }'

# Stream (Server-Sent Events: "data: {json}" lines, terminated by "data: [DONE]")
curl -N -X POST http://localhost:8080/generate_stream \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "Count to 10:",
    "parameters": {"max_new_tokens": 50}
  }'

# OpenAI-compatible chat completions
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tgi",
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
  constructor(private baseUrl: string = "http://localhost:8080") {}

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
    return data.generated_text;   // object, not an array
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
        parameters: { max_new_tokens: 256, ...options },
      }),
    });

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";   // keep the partial last line

      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const data = line.slice("data:".length).trim();
        if (data === "[DONE]") return;
        yield JSON.parse(data).token.text;
      }
    }
  }
}

// Usage
const client = new TGIClient();

const response = await client.generate("Explain TypeScript:");
console.log(response);

for await (const token of client.generateStream("Write a poem:")) {
  process.stdout.write(token);
}
```

## Advanced Features

### 1. LoRA Adapters

TGI serves multiple LoRA adapters from one base model — pass them at launch and
select per request with `adapter_id`:

```bash
docker run -d --gpus all \
  --shm-size 1g \
  -p 8080:80 \
  --name tgi-mistral \
  -v /srv/models/lora:/data/lora:ro \
  ghcr.io/huggingface/text-generation-inference:3.3.7 \
  --model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ \
  --lora-adapters "lora-chat=/data/lora/chat-adapter,lora-code=/data/lora/code-adapter"
```

```python
# Select an adapter per request
payload = {
    "inputs": "Write Python code:",
    "parameters": {
        "max_new_tokens": 256,
        "adapter_id": "lora-code",
    },
}
```

Caveat: serving LoRA adapters disables prefix caching for the server — plan
capacity accordingly (see the source-verified note under Performance Tuning).

### 2. Speculative Decoding

TGI 3.x takes a single flag — how many tokens to speculate:

```bash
docker run -d --gpus all \
  --shm-size 1g \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:3.3.7 \
  --model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ \
  --speculate 4
```

Two modes, chosen automatically:

- **n-gram**: drafts from n-grams already in the prompt/context. Near-free
  overhead; wins when output repeats the input (code edits, structured data,
  summarization).
- **Medusa**: if the checkpoint ships Medusa heads, TGI picks them up
  automatically; extra head weights trade VRAM for higher acceptance rates.

There is no draft-model flag: older TGI 2.x options like
`--speculative-decoding-model` do not exist in the current launcher. Larger
speculation depth helps only while acceptance stays high — tune with real
traffic. Theory: [4202: Speculative Decoding](../../../phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md).

### 3. Grammar-Constrained Generation

`parameters.grammar` takes a type/value pair — `json` (a JSON Schema, backed by
Outlines) or `regex`:

```python
import requests

payload = {
    "inputs": "Generate a person profile:",
    "parameters": {
        "max_new_tokens": 128,
        "grammar": {
            "type": "json",
            "value": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
                "required": ["name", "age"],
            },
        },
    },
}

response = requests.post("http://localhost:8080/generate", json=payload)
print(response.json()["generated_text"])
# Output is constrained to the schema at every generated token — not a
# post-hoc repair. Long schemas can still stall generation when the grammar
# accepts only long token sequences, so keep schemas small.
```

### 4. Tool Calling

Tool calling lives on the OpenAI-compatible chat endpoint, **not** on
`/generate` — the native request schema has no `tools` field. The router
applies the model's chat template and converts tool schemas into a JSON
grammar that constrains tool-call output:

```python
import requests

tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }
]

response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    json={
        "model": "tgi",
        "messages": [{"role": "user", "content": "Search for recent AI news"}],
        "tools": tools,
        "tool_choice": "auto",
        "max_tokens": 256,
    },
)
message = response.json()["choices"][0]["message"]
# message["tool_calls"] is populated when the model decides to call a tool
print(message.get("tool_calls"))
```

## Performance Tuning

### KV Cache Budget (11GB-class GPU)

```text
TheBloke/Mistral-7B-Instruct-v0.2-AWQ on ~11GB VRAM:

Weights:        ~3.5GB   (4-bit AWQ; fp16 would be ~14GB — doesn't fit)
CUDA + compute: ~1.5-2GB
KV cache:       remaining ~5GB, budgeted by --max-batch-total-tokens

KV per token (Mistral-7B: 32 layers, 8 KV heads × 128 dim, fp16 KV):
  2 (K+V) × 32 × 8 × 128 × 2 bytes = 128 KB/token

--max-batch-total-tokens 16384  →  16384 × 128KB ≈ 2GB KV ceiling
One 8k-token request ≈ 1GB       →  ~4 concurrent 8k requests fit

Rules of thumb:
- OOM at warmup → lower --max-total-tokens / --max-batch-total-tokens
- More concurrency → shorter --max-total-tokens (smaller per-request slice)
```

### Throughput Benchmark (Concurrent Clients)

```python
# The sequential loop below TGI's router measures nothing useful: the router
# batches CONCURRENT requests, so load must be concurrent. Count real
# generated tokens — max_new_tokens assumes no early EOS stop.
import time
from concurrent.futures import ThreadPoolExecutor

import requests

URL = "http://localhost:8080/generate"


def one_request() -> int:
    r = requests.post(
        URL,
        json={"inputs": "Summarize the theory of relativity.",
              "parameters": {"max_new_tokens": 100}},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["details"]["generated_tokens"]


def benchmark(concurrency: int) -> float:
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        start = time.time()
        token_counts = list(pool.map(lambda _: one_request(), range(concurrency)))
        elapsed = time.time() - start
    tokens = sum(token_counts)
    print(f"concurrency={concurrency:2d}: {tokens / elapsed:6.1f} tok/s aggregate")
    return tokens / elapsed


for c in [1, 2, 4, 8, 16]:
    benchmark(c)
```

Aggregate throughput should climb roughly with concurrency until the KV cache
saturates; per-stream decode stays single-digit tok/s on an 11GB GPU — that is
memory-bandwidth-bound decode, not a misconfiguration.

### Prefix Caching

Prefix caching is **on by default** (TGI 3.x, flashinfer-backed): repeated
prompt prefixes skip prefill KV recomputation. There is no
`--enable-prefix-caching` flag. Control it with the environment:

```bash
# Explicitly disable (e.g. when benchmarking with identical prompts —
# a warm prefix cache would inflate your numbers):
docker run -d --gpus all \
  -p 8080:80 \
  -e PREFIX_CACHING=false \
  ghcr.io/huggingface/text-generation-inference:3.3.7 \
  --model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ
```

TGI automatically disables prefix caching for vision-language models,
encoder-decoder models, and when LoRA adapters are served (`--lora-adapters`).
Measure with `tgi_request_inference_duration` percentiles before/after — don't
assume the cache helps your workload.

## Monitoring

### Metrics Endpoint

```bash
# TGI exposes Prometheus metrics at /metrics
curl http://localhost:8080/metrics
```

Key series (names verified against the TGI 3.x router source):

```text
tgi_request_count                        counter  — requests received
tgi_request_success                      counter  — successful requests
tgi_request_failure                      counter  — failed requests
tgi_request_generated_tokens             counter  — tokens generated (sum) →
                                                    rate() gives output tok/s
tgi_request_input_length                 histogram — prompt length distribution
tgi_request_duration                     histogram — end-to-end latency
tgi_request_queue_duration               histogram — time waiting for a batch
tgi_request_inference_duration           histogram — time inside the engine
tgi_request_mean_time_per_token_duration histogram — per-token decode latency
tgi_queue_size                           gauge    — requests waiting in the queue
tgi_batch_inference_count                counter  — batches executed
tgi_batch_current_size                   gauge    — requests in the running batch
tgi_batch_current_max_tokens             gauge    — token budget of running batches
```

(There is no `tgi_cache_hit_rate` metric in TGI — prefix-cache effectiveness
must be inferred from `tgi_request_inference_duration`.)

### Prometheus Integration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tgi'
    static_configs:
      - targets: ['tgi-mistral:80']
    metrics_path: /metrics
```

Full dashboards: [1501: Monitoring and Observability](../../1500-monitoring/1501-Monitoring-and-Observability.md).

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```text
Error: CUDA out of memory
```

**Solutions:**

```bash
# Use a pre-quantized checkpoint (fp16 7B ≈ 14GB never fits 11GB)
--model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ

# Shrink the KV budget (KV per token: ~128KB for Mistral-7B)
--max-total-tokens 4096
--max-batch-total-tokens 8192

# Cap requests per batch
--max-batch-size 4
```

#### 2. Slow First Request

```text
First request takes tens of seconds (or the health check fails for minutes)
```

**Cause:** the first start downloads weights (~3.5GB for AWQ 7B), loads them to
the GPU, and runs a warmup pass that measures the KV cache. This is expected,
not a bug — TGI's `/health` only returns 200 when the server is actually ready.

**Solutions:**

```bash
# Cache weights on a volume so restarts skip the download
-v /srv/models/tgi:/data          # image sets HF_HOME=/data

# Give orchestrators a realistic grace period
# docker compose: healthcheck.start_period: 300s
```

#### 3. Low Throughput

```text
Single request: <10 tokens/sec
```

**First:** this is normal for single-stream decode on an 11GB GPU — measure
aggregate throughput with concurrent clients (benchmark above) before tuning.

**Solutions:**

```bash
# Raise the batch token budget (the main throughput knob)
--max-batch-total-tokens 32768

# Raise the router concurrency ceiling if requests get HTTP 429
--max-concurrent-requests 256

# Shorter contexts → more KV room for concurrent requests
--max-total-tokens 4096
```

#### 4. 401 Unauthorized on Model Download

```text
Gated repo (e.g. mistralai/* or meta-llama/*) requires accepting the license
and a token.
```

**Solutions:**

```bash
# Pass a token (gated models only — TheBloke AWQ repos are ungated)
docker run ... -e HF_TOKEN=hf_xxx ...

# Or avoid gating entirely by using an ungated mirror of the weights
```

#### 5. Quantization Errors with `--quantize awq` on a Full-Precision Repo

```text
Error: model ... is not quantized / quantization mismatch
```

**Cause:** `--quantize awq` requires a checkpoint that was quantized with AWQ —
it does not quantize on the fly. A plain fp16 repo fails.

**Solution:** use a pre-quantized AWQ repo and drop the flag entirely:

```bash
--model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ   # auto-detected
```

## End-to-End Deployment Walkthrough

```bash
# 1. Pull the pinned final-release image (repo archived Mar 2026)
docker pull ghcr.io/huggingface/text-generation-inference:3.3.7

# 2. Start TGI with a checkpoint that fits 11GB
docker run -d --gpus all \
  --shm-size 1g \
  -p 8080:80 \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:3.3.7 \
  --model-id TheBloke/Mistral-7B-Instruct-v0.2-AWQ \
  --max-total-tokens 8192

# 3. Wait for readiness, then check model info
curl http://localhost:8080/health
curl http://localhost:8080/info

# 4. Test generation — note the object response
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello!", "parameters": {"max_new_tokens": 50}}'

# 5. Test with Python
uv pip install requests
python -c "import requests; print(requests.post('http://localhost:8080/generate', json={'inputs': 'Hello!', 'parameters': {'max_new_tokens': 50}}).json()['generated_text'])"
```

---

## References

### Related ai-engineering-curriculum Documents

- [1404: vLLM Production Deployment Guide](1404-vLLM-Production-Deployment.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**

---

**Related:**
- [1402: vLLM and TGI](../1402-vLLM-and-TGI.md)
- [1404: vLLM Production Deployment](./1404-vLLM-Production-Deployment.md)
- [1401: Ollama Enterprise](../1401-Ollama-Enterprise.md)
- [4201: Context Window Physics](../../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [1501: Monitoring and Observability](../../1500-monitoring/1501-Monitoring-and-Observability.md)
