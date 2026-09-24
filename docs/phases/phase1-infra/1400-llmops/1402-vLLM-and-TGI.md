---
Document ID: 1402
Title: vLLM and TGI High-Concurrency Inference
Phase: 1
Module: 1400
Last Updated: 2026-09-24
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
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare Comparison
- Explain vLLM Architecture
- Configure and operate vLLM Installation
- Configure and operate vLLM Configuration
- Configure and operate TGI Installation
- Measure and evaluate Performance Tuning

---

## Abstract
vLLM and Text Generation Inference (TGI) are optimized inference engines for LLMs. They provide PagedAttention, continuous batching, and KV cache optimization for high-throughput serving on an 11GB-class GPU.

## Comparison

| Feature | vLLM | TGI |
|---------|------|-----|
| PagedAttention | Yes | No |
| Continuous Batching | Yes | Yes |
| Multi-GPU | Yes | Yes |
| Open Source | MIT | Apache 2.0 |
| Model Support | HuggingFace | HuggingFace |
| Flash Attention | Yes | Yes |
| Speculative Decoding | Yes | Experimental |
| Recommended For | Research/Custom | Production/Enterprise |

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
GPU VRAM (11GB):
┌────────────────────────────────────────────────────┐
│ Model Weights         ~4-5GB (Llama-7B fp16)      │
├────────────────────────────────────────────────────┤
│ KV Cache (Paged)      ~4-5GB (dynamic)            │
├────────────────────────────────────────────────────┤
│ Activation Buffer     ~1GB                         │
└────────────────────────────────────────────────────┘
```

## vLLM Installation

### From Source
```bash
# On GPU VM with CUDA 12.1
git clone https://github.com/vllm-project/vllm.git
cd vllm

# Install with CUDA
pip install -e . --no-build-isolation

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
        accelerator: nvidia-gpu
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        command:
          - --model
          - meta-llama/Llama-2-7b-hf
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
    model="meta-llama/Llama-2-7b-hf",

    # Tensor Parallelism (multi-GPU)
    tensor_parallel_size=1,          # 1 for single 11GB-class GPU

    # Memory Management
    gpu_memory_utilization=0.9,     # Use 90% of GPU for KV cache
    max_model_len=4096,              # Max sequence length
    swap_space=4,                    # GB of CPU swap for KV cache

    # Quantization
    quantization="awq",              # or "gptq", "squeezellm"
    dtype="half",                    # fp16 for faster inference

    # Optimization
    enforce_eager=True,              # Disable CUDA graph (debugging)
    max_num_batched_tokens=4096,     # Max tokens per batch
    trust_remote_code=True
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
        accelerator: nvidia-gpu
      containers:
      - name: tgi
        image: ghcr.io/huggingface/text-generation-inference:latest
        command:
          - --model-id
          - meta-llama/Llama-2-7b-hf
          - --num-shard
          - "1"
          - --max-total-tokens
          - "4096"
          - --max-batch-total-tokens
          - "8192"
          - --dtype
          - float16
        ports:
        - containerPort: 80
        env:
        - name: HF_TOKEN
          valueFrom:
            secretKeyRef:
              name: hf-token
              key: token
        - name: FLASH_ATTENTION
          value: "true"
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "12Gi"
```

## Performance Tuning

### Memory Utilization
```python
# For an 11GB VRAM GPU (11GB VRAM)
# Llama-7B fp16: ~13GB weights (doesn't fit!)
# Solution: Quantization

# AWQ 4-bit quantization
llm = LLM(
    model="TheBloke/Llama-2-7B-AWQ",
    quantization="awq",
    gpu_memory_utilization=0.9,
    max_model_len=8192  # Longer context with quantized weights
)

# Memory breakdown (AWQ):
# Weights: ~3.5GB (4-bit)
# KV Cache: ~6GB (at 8k context)
# Activations: ~1.5GB
# Total: ~11GB (fits!)
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
    tokens_per_sec = batch_size * 512 / duration
    print(f"Batch {batch_size}: {tokens_per_sec:.1f} tok/s")
```

### KV Cache Configuration
```python
# vLLM KV cache allocation
# Larger cache = longer context OR more concurrent requests

# Option 1: Maximize context length
llm = LLM(
    model="...",
    gpu_memory_utilization=0.9,
    max_model_len=16384,  # 16k context
    # But: limited concurrent requests
)

# Option 2: Maximize concurrency
llm = LLM(
    model="...",
    gpu_memory_utilization=0.9,
    max_model_len=2048,  # Shorter context
    # But: more concurrent requests
)
```

## API Usage

### vLLM OpenAI-Compatible API
```bash
# Start server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-2-7b-hf \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9

# Use with OpenAI client
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="meta-llama/Llama-2-7b-hf",
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
        model="meta-llama/Llama-2-7b-hf",
        gpu_memory_utilization=0.9
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
Model          Quant    Context    Tokens/sec
────────────────────────────────────────────
Llama-2-7B     fp16     2048       ~30-40
Llama-2-7B     AWQ      2048       ~40-50
Llama-2-7B     4-bit    2048       ~50-60
Mistral-7B     fp16     2048       ~35-45
Mixtral-8x7B   4-bit    4096       ~5-10 (slow)
```

## Monitoring

### vLLM Metrics
```python
# vLLM exposes Prometheus metrics
# Default port: 8000

import requests

metrics = requests.get("http://localhost:8000/metrics").text

# Key metrics:
# vllm:num_requests_waiting
# vllm:num_requests_running
# vllm:num_requests_swapped
# vllm:gpu_cache_usage_perc
# vllm:avg_prompt_throughput_toks_per_s
# vllm:avg_generation_throughput_toks_per_s
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

## References

### Related ai-engineering-curriculum Documents

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

**Experiment Template:** `experiments/EXP_1402_VLLM_TGI.md`
