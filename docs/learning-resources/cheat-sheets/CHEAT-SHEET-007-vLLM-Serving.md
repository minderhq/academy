---
Document ID: CHEAT-SHEET-007
Title: "CHEAT-SHEET-007: vLLM Serving & Inference"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'vllm', 'inference', 'serving']
---

# CHEAT-SHEET-007: vLLM Serving & Inference

## Quick Reference for High-Throughput LLM Serving

**Version:** 1.0

---

## Installation

### Install vLLM

```bash
# In the course environment (uv standard - see ENVIRONMENT-SETUP):
uv pip install vllm

# Verify
python -c "import vllm; print(vllm.__version__)"
nvidia-smi   # driver + GPU must be visible before serving
```

### Docker Server Image

```bash
docker run --gpus all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3.1-8B-Instruct
```

---

## Serving an LLM

### Basic Serve

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9
```

### Common Serve Flags

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --served-model-name qwen7b \            # alias clients request
  --host 0.0.0.0 --port 8000 \
  --dtype bfloat16 \                      # or float16 / auto
  --max-model-len 16384 \                 # cap context to save KV memory
  --max-num-seqs 256 \                    # concurrent sequences
  --gpu-memory-utilization 0.90 \         # KV cache share of GPU memory
  --disable-log-requests                  # quieter logs in production
```

---

## OpenAI-Compatible API

### Chat Completions

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen7b",
    "messages": [{"role": "user", "content": "Explain KV cache in one line."}],
    "temperature": 0.2,
    "max_tokens": 128
  }'
```

### Discovery Endpoints

```bash
curl http://localhost:8000/v1/models          # served model names
curl http://localhost:8000/health             # liveness probe
curl http://localhost:8000/metrics            # Prometheus metrics
```

---

## Offline Batch Inference

```python
from vllm import LLM, SamplingParams

llm = LLM(model="Qwen/Qwen2.5-7B-Instruct", max_model_len=8192)
params = SamplingParams(temperature=0.2, top_p=0.9, max_tokens=256)

prompts = ["Summarize attention.", "List three vector databases."]
outputs = llm.generate(prompts, params)

for out in outputs:
    print(out.outputs[0].text)
```

---

## Quantization

### Serve a Pre-Quantized Model

```bash
# AWQ / GPTQ checkpoints load with the right kernel automatically
vllm serve Qwen/Qwen2.5-7B-Instruct-AWQ --max-model-len 8192
```

### Explicit Quantization and KV-Cache Quantization

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --quantization fp8 \
  --kv-cache-dtype fp8                    # doubles effective KV capacity
```

---

## Parallelism

### Tensor and Pipeline Parallelism

```bash
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --tensor-parallel-size 4 \              # split layers across GPUs
  --pipeline-parallel-size 2 \            # split layers across stages
  --max-model-len 16384
```

```bash
# Single node must expose GPUs 0-3 for -tp 4
CUDA_VISIBLE_DEVICES=0,1,2,3 vllm serve ... --tensor-parallel-size 4
```

---

## Throughput Tuning

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --enable-prefix-caching \               # reuse shared prompt KV (default on)
  --enable-chunked-prefill \              # interleave prefill with decode
  --max-num-batched-tokens 8192           # prefill chunk size
```

### Structured Output

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
resp = client.chat.completions.create(
    model="qwen7b",
    messages=[{"role": "user", "content": "Return a 3-item grocery list."}],
    extra_body={
        "guided_json": {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "string"}}},
            "required": ["items"],
        }
    },
)
```

### Tool Calling

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --enable-auto-tool-choice \
  --tool-call-parser hermes               # parser must match the model's format
```

---

## Speculative Decoding

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --speculative-config '{"method": "ngram", "num_speculative_tokens": 3}'
```

---

## Embeddings and Scoring

```bash
vllm serve BAAI/bge-base-en-v1.5 --task embed
curl http://localhost:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "BAAI/bge-base-en-v1.5", "input": "hello"}'
```

---

## Troubleshooting

```bash
# CUDA out of memory during profiling
#   -> lower --gpu-memory-utilization (0.85) and --max-model-len,
#      or serve a pre-quantized checkpoint

# Model exceeds free VRAM even at util 0.9
#   -> shrink --max-num-seqs, cap --max-model-len, add -tp 2

# Port already in use
#   -> --port 8001, or stop the stale server (fuser -k 8000/tcp)

# Slow first request
#   -> CUDA graph capture + warmup happen once at startup; keep a
#      health-check warm-up call in your deploy scripts
```

---

**Quick Reference for:**

- [Module 1402: vLLM & TGI High-Concurrency Inference](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [EXP_1404: vLLM Tuning](../../../experiments/EXP_1404_VLLM_TUNING.md)
- [Module 1302: GPU Scheduler](../../phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)
- [CHEAT-SHEET-006: Kubernetes for LLM Deployment](./CHEAT-SHEET-006-Kubernetes.md)
