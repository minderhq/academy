---
Document ID: 1402
Title: "1402: vLLM and TGI High-Concurrency Inference"
Phase: 1
Module: 1400
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'llmops', 'ollama', 'vllm', 'tgi']
---

# 1402: vLLM and TGI High-Concurrency Inference

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Comparison](#comparison)
- [vLLM Architecture](#vllm-architecture)
- [vLLM Installation](#vllm-installation)
- [vLLM Configuration](#vllm-configuration)
- [TGI Installation](#tgi-installation)
- [Performance Tuning](#performance-tuning)
- [API Usage](#api-usage)
- [Benchmarking](#benchmarking)
- [Monitoring](#monitoring)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Contrast the vLLM and TGI feature sets and place each engine in its 2026 status (vLLM the default; TGI archived)
- Explain PagedAttention's page-level KV allocation against contiguous caching and the 11GB VRAM layout
- Deploy vLLM from wheels (uv pip) or the pinned Docker image on a GPU node serving an AWQ checkpoint
- Tune gpu_memory_utilization, max_model_len, and quantization - and budget KV cache from the layer/hidden-size math
- Run the TGI container as the archived legacy engine (auto-detected quantization, HF token handling for gated models)
- Benchmark throughput honestly (count EOS-truncated tokens) and read the V1 Prometheus metrics

---

## Abstract
vLLM and Text Generation Inference (TGI) are optimized inference engines for LLMs. Both provide continuous batching and KV cache management for high-throughput serving on an 11GB-class GPU; vLLM additionally brings PagedAttention, which segments the KV cache into fixed-size pages to eliminate fragmentation. On 11GB, fp16 7B weights (~14GB) do not fit — the runnable examples in this lesson use a pre-quantized AWQ checkpoint (~3.5GB).

## Comparison

| Feature | vLLM | TGI |
|---------|------|-----|
| PagedAttention | Yes | No |
| Continuous Batching | Yes | Yes |
| Multi-GPU | Yes | Yes |
| Open Source | Apache 2.0 | Apache 2.0 |
| Model Support | Hugging Face | Hugging Face |
| Flash Attention | Yes | Yes |
| Speculative Decoding | Yes | Experimental |
| Recommended For | Research/Custom + production default | Legacy - existing fleets only |

Status note (Sep 2026): the TGI repository was archived on GitHub
(read-only) in March 2026; v3.3.7 was its final release. The server
still runs and the TGI sections below remain technically valid, but new
production deployments should default to vLLM.

## vLLM Architecture

### PagedAttention Mechanism
```text
Traditional KV Cache:
[───────────────────────────────────────────────────────]
Fixed contiguous allocation → Waste + Fragmentation

Paged KV Cache (vLLM):
[Page 1][Page 2][Page 3][Page 4][Page 5]...
Non-contiguous blocks → Efficient reuse

Analogy: Like virtual memory paging for LLM KV cache
```

### Memory Layout
```text
GPU VRAM (11GB, gpu_memory_utilization=0.9 → ~9.9GB usable):
┌────────────────────────────────────────────────────┐
│ Model Weights         ~5.5GB (Qwen2.5-7B AWQ 4-bit)│
├────────────────────────────────────────────────────┤
│ KV Cache (Paged)      ~4-5GB (dynamic)            │
├────────────────────────────────────────────────────┤
│ Activations + CUDA    ~1-2GB                       │
└────────────────────────────────────────────────────┘

Note: the same 7B-class model in fp16 needs ~15GB for weights
alone (7.6B params × 2 bytes) — it does not fit 11GB at all.
Quantization is not optional on this hardware (see
Performance Tuning below).
```

## vLLM Installation

### From Source
```bash
# Recommended: prebuilt wheel (Linux + CUDA)
uv pip install vllm

# From source (development):
# On GPU VM with CUDA 12.1
git clone https://github.com/vllm-project/vllm.git
cd vllm
uv pip install -e . --no-build-isolation

# Verify
python -c "import vllm; print(vllm.__version__)"
```

### Docker/Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm
  namespace: ai-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      nodeSelector:
        accelerator: nvidia   # must match the GPU node label (see 1301)
      containers:
      - name: vllm
        image: vllm/vllm-openai:v0.30.0   # pinned release (Sep 2026); check releases for newer
        # args (not command:) — command: would replace the image ENTRYPOINT
        args:
          - --model
          - Qwen/Qwen2.5-7B-Instruct-AWQ   # pre-quantized AWQ: ungated, fits 11GB
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
        env:
        - name: HF_HOME
          value: /models
        # Gated models (e.g. meta-llama/Meta-Llama-3.1-8B-Instruct) also need:
        # - name: HF_TOKEN
        #   valueFrom:
        #     secretKeyRef:
        #       name: hf-token
        #       key: token
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "12Gi"
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: hf-model-cache
```

## vLLM Configuration

### Key Parameters
```python
from vllm import LLM, SamplingParams

# Initialize
llm = LLM(
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",  # pre-quantized checkpoint (ungated, fits 11GB)

    # Tensor Parallelism (multi-GPU)
    tensor_parallel_size=1,          # 1 for single 11GB-class GPU

    # Memory Management
    gpu_memory_utilization=0.9,     # fraction of total VRAM vLLM may use
                                     # (weights + KV cache + activations)
    max_model_len=4096,              # Max sequence length
    # swap_space: legacy-engine KV CPU swap (GB) — the V1 engine ignores it;
    # over-budget sequences are preempted and recomputed instead

    # Quantization
    quantization="awq",              # requires a pre-quantized AWQ checkpoint
                                     # (as above); "gptq" likewise needs a GPTQ repo
    dtype="half",                    # compute dtype for activations/KV

    # Optimization
    enforce_eager=True,              # Disable CUDA graph (debugging)
    max_num_batched_tokens=4096,     # Max tokens per batch
    # no trust_remote_code - the AWQ checkpoint loads with stock transformers code
)

# Sampling parameters
sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
    repetition_penalty=1.1
)
```

### Continuous Batching
```text
Static Batching (Traditional):
Batch 1: [Request A (1000 tokens), Request B (500 tokens)]
Wait for both to complete before processing new requests

Continuous Batching (vLLM):
Time →
Batch 1: [A:1000][B:500]
Batch 2:        [A:1500][B:1000][C:200]  ← Added C!
Batch 3:               [B:1500][C:700][D:300]  ← A complete, added D!

Result: Higher throughput, lower latency
```

## TGI Installation

### Docker/Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tgi
  namespace: ai-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tgi
  template:
    metadata:
      labels:
        app: tgi
    spec:
      nodeSelector:
        accelerator: nvidia   # must match the GPU node label (see 1301)
      containers:
      - name: tgi
        image: ghcr.io/huggingface/text-generation-inference:3.3.7   # final release - repo archived Mar 2026
        # args (not command:) — command: would replace the
        # text-generation-launcher entrypoint
        args:
          - --model-id
          - Qwen/Qwen2.5-7B-Instruct-AWQ   # pre-quantized AWQ: quantization is
                                      # auto-detected — no --quantize/--dtype
          - --num-shard
          - "1"
          - --max-total-tokens
          - "4096"
          - --max-batch-total-tokens
          - "8192"
        ports:
        - containerPort: 80
        # Flash attention is auto-enabled when the model and kernels support
        # it — there is no FLASH_ATTENTION environment variable to set.
        # Qwen/Qwen2.5-7B-Instruct-AWQ is ungated, so no token is needed. For a
        # gated model, add:
        # env:
        # - name: HF_TOKEN
        #   valueFrom:
        #     secretKeyRef:
        #       name: hf-token
        #       key: token
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "12Gi"
```

## Performance Tuning

### Memory Utilization
```python
# For an 11GB VRAM GPU
# Qwen2.5-7B fp16: ~15GB weights alone (doesn't fit!)
# Solution: pre-quantized checkpoints

llm = LLM(
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
    quantization="awq",
    gpu_memory_utilization=0.9,
    max_model_len=8192  # Longer context with quantized weights
)

# Memory budget: 0.9 × 11GB ≈ 9.9GB (AWQ)
# Weights:     ~5.5GB (4-bit)
# Activations: ~1.5GB
# KV Cache:    ~2.9GB left
#
# KV cache math (Qwen2.5-7B, fp16 KV, GQA):
#   per token = 2 (K+V) × 28 layers × 512 kv-dim × 2 bytes ≈ 57KB
#   one 8k-token sequence: 8192 × 57KB ≈ 0.5GB  → five-plus fit
```

### Batch Size Optimization
```python
# Find optimal batch size via experimentation
import time

for batch_size in [1, 2, 4, 8, 16, 32]:
    prompts = ["Tell me a story"] * batch_size
    start = time.time()
    outputs = llm.generate(prompts, sampling_params)
    duration = time.time() - start
    # Count actual generated tokens — requests may stop early on EOS, so
    # batch_size * max_tokens overestimates throughput
    tokens = sum(len(o.outputs[0].token_ids) for o in outputs)
    print(f"Batch {batch_size}: {tokens / duration:.1f} tok/s ({duration:.2f}s)")
```

### KV Cache Configuration
```python
# vLLM KV cache allocation
# Larger cache = longer context OR more concurrent requests.
# One LLM instance owns the whole gpu_memory_utilization budget —
# pick one configuration per process.

# Option 1: Maximize context length
llm = LLM(
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
    gpu_memory_utilization=0.9,
    max_model_len=4096,  # a KV-budget-friendly slice; the model's own
                         # ceiling is 32768 (max_position_embeddings)
)

# Option 2: Maximize concurrency
llm = LLM(
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
    gpu_memory_utilization=0.9,
    max_model_len=2048,  # Shorter context → more KV pages per request
)
```

## API Usage

### vLLM OpenAI-Compatible API
```bash
# Start server — must be a quantized checkpoint to fit 11GB
vllm serve Qwen/Qwen2.5-7B-Instruct-AWQ \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9
```

```python
# Use with OpenAI client — the model name must match the served model
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=512
)
```

### TGI API
```bash
# Generate
curl -X POST http://localhost:80/generate \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "Write a haiku about AI",
    "parameters": {
      "max_new_tokens": 100,
      "temperature": 0.7
    }
  }'

# Stream
curl -X POST http://localhost:80/generate_stream \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "Count to 10",
    "parameters": {"max_new_tokens": 50}
  }'
```

## Benchmarking

### Benchmark Script
```python
import time
import numpy as np
from vllm import LLM, SamplingParams

def benchmark_vllm():
    llm = LLM(
        model="Qwen/Qwen2.5-7B-Instruct-AWQ",
        gpu_memory_utilization=0.9,
        enable_prefix_caching=False,  # identical prompts would all hit the
                                      # prefix cache and skew the numbers
    )

    test_cases = [
        ("Short prompt", "Hello!" * 10),
        ("Medium prompt", "Hello!" * 100),
        ("Long prompt", "Hello!" * 500),
    ]

    for name, prompt in test_cases:
        times = []
        for _ in range(10):
            start = time.time()
            outputs = llm.generate([prompt], SamplingParams(max_tokens=100))
            times.append(time.time() - start)

        print(f"{name}: {np.mean(times):.3f}s ± {np.std(times):.3f}s")

benchmark_vllm()
```

### Expected Performance (11GB VRAM GPU)
```text
Aggregate throughput on one 11GB GPU — illustrative ranges; measure on
your own hardware with the script above.

Model          Quant      Context    Aggregate tok/s
──────────────────────────────────────────────────────
Qwen2.5-7B     AWQ 4-bit  2048       ~40-80
Qwen2.5-7B     GPTQ 4-bit 2048       ~40-80
Llama-3.1-8B   AWQ 4-bit  2048       ~30-60
Qwen2.5-7B     fp16       —          does not fit 11GB (~15GB weights)
Mixtral-8x7B   4-bit      —          does not fit 11GB (~26GB weights)

Per-stream latency is single-digit tok/s; continuous batching multiplies
aggregate throughput roughly with concurrency until the KV cache
saturates (watch vllm:kv_cache_usage_perc).
```

## Monitoring

### vLLM Metrics
```python
# vLLM exposes Prometheus metrics
# Default port: 8000

import requests

metrics = requests.get("http://localhost:8000/metrics", timeout=5).text

# Key metrics (vLLM V1 engine):
# vllm:num_requests_running     gauge — executing now
# vllm:num_requests_waiting     gauge — queued waiting for KV budget
# vllm:kv_cache_usage_perc      gauge — 0-1; sustained ~1.0 means raise
#                               gpu_memory_utilization or cut max_model_len
# vllm:num_preemptions_total    counter — V1 has no CPU swap; over-budget
#                               sequences are preempted and recomputed
#
# Throughput has no precomputed gauge — derive it from the token counters:
#   rate(vllm:prompt_tokens_total[5m])
#   rate(vllm:generation_tokens_total[5m])
# Latency histograms (p50/p90/p99 via histogram_quantile()):
#   vllm:time_to_first_token_seconds, vllm:e2e_request_latency_seconds
```

### GPU Monitoring
```bash
# Monitor during inference
watch -n 0.1 nvidia-smi

# Check for:
# - GPU utilization (should be >90%)
# - Memory usage (should be stable)
# - Temperature (<80°C)
# - Power draw (<250W)
```

---

## Summary

vLLM and TGI are the optimized inference engines for high-throughput serving, and both live on the same two ideas: continuous batching and managed KV cache. vLLM adds PagedAttention, segmenting the cache into fixed-size pages to eliminate fragmentation. The constraint this lesson repeats on 11GB: fp16 7B weights need ~14GB and do not fit, so every runnable example serves a pre-quantized AWQ checkpoint (~3.5GB). It compared the engines, walked vLLM architecture and installation, TGI installation, configuration, performance tuning, API usage, benchmarking, and monitoring. The takeaway: benchmark both on your workload - the winner is measured, not assumed.

## References

### Related Minder Academy Documents

- [1401: Ollama Enterprise Deployment](1401-Ollama-Enterprise.md)

---

## Next Steps

- Next Module: **[1500: Monitoring](../1500-monitoring/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**

- [1302: GPU Scheduler](../1300-kubernetes/1302-GPU-Scheduler.md)
- [1401: Ollama Enterprise](./1401-Ollama-Enterprise.md)
- [4101: GGUF Physics](../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- [4202: Speculative Decoding](../../phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md)

