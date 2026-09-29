---
Document ID: 4408
Title: "4408: Quantizing for Production"
Phase: 4
Module: 4400
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'production', 'deployment', 'gptq', 'gguf', 'serving']
---

# 4408: Quantizing for Production

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Pipeline at a Glance](#the-pipeline-at-a-glance)
- [Step 1: Model Selection](#step-1-model-selection)
- [Step 2: Calibration Data](#step-2-calibration-data)
- [Step 3: Choose the Method](#step-3-choose-the-method)
- [Step 4: Run Quantization](#step-4-run-quantization)
- [Step 5: Validate Before Shipping](#step-5-validate-before-shipping)
- [Step 6: Deploy](#step-6-deploy)
- [Production Checklist](#production-checklist)
- [Common Issues](#common-issues)
- [Best Practices](#best-practices)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Run the six-step production quantization pipeline end to end: select → calibrate → choose → quantize → validate → deploy
- Build a calibration set that actually protects quality — in-distribution samples at serving-length sequences — and explain what breaks when either property is violated
- Choose a format from the deployment target using the 2026 toolchain reality: GPTQ via `transformers` for GPU serving, GGUF for CPU, EXL2 for local GPU, FP8 on Hopper-class datacenter hardware
- Validate a quantized model with three independent gates (perplexity delta, KL vs the FP teacher, latency/throughput on target hardware) instead of one weak signal
- Serve the result with vLLM and identify why a hand-rolled `model.generate` wrapper is a demo pattern, not a production one

---

## Abstract

Quantizing a model for production is a pipeline, not a one-liner: the format decision, the calibration set, and the validation gates each independently decide whether the shipped model is a win or an incident. This guide walks the full six steps with the 2026 toolchain — the standalone AutoGPTQ and AutoAWQ packages are no longer maintained, so GPTQ runs through the `transformers`-native config, CPU deployment goes through llama.cpp's current converter, and datacenter serving on Hopper-class GPUs increasingly skips INT4 entirely for FP8. Just as important as producing the quantized checkpoint is *proving* it: perplexity deltas on your own domain data, distribution divergence against the full-precision teacher, and benchmarks on the hardware you will actually serve on. The algorithm theory lives in [4401](../4401-GPTQ.md) and [4402](../4402-AWQ.md); this guide is the surrounding operational discipline.

## The Pipeline at a Glance

```text
1. SELECT       base model, license, architecture support
2. CALIBRATE    256-512 in-distribution samples at serving length
3. CHOOSE       format + runtime from the deployment target
4. QUANTIZE     run the conversion; record every parameter
5. VALIDATE     three gates: perplexity, KL vs FP, perf on target HW
6. DEPLOY       serving stack, monitoring, rollback plan

Skip step 2 and no downstream fix matters; skip step 5 and you
find out from users.
```

## Step 1: Model Selection

Check architecture support and the license *programmatically* — model configs do not carry a `license` field; the license lives in the model card metadata exposed as tags:

```python
from huggingface_hub import HfApi
from transformers import AutoConfig

model_id = "meta-llama/Llama-2-7b-hf"

config = AutoConfig.from_pretrained(model_id)

# architectures every major quantization path supports well
SUPPORTED = {"llama", "mistral", "mixtral", "qwen2", "phi3", "gemma2"}
if config.model_type not in SUPPORTED:
    print(f"Warning: {config.model_type} may lag in kernel support")

def model_license(model_id: str):
    """License arrives as a 'license:<name>' tag, not a config
    attribute - read it from the Hub API."""
    info = HfApi().model_info(model_id)
    for tag in info.tags:
        if tag.startswith("license:"):
            return tag.split(":", 1)[1]
    return None    # no license tag: treat as unusable commercially

print(model_license(model_id))
```

```text
Selection criteria that matter for quantization
- parameter count vs your memory budget AT the target bit-width
  (a 7B at INT4 fits 12GB consumer cards; a 13B does not)
- architecture maturity: quantization kernels land for popular
  archs first; brand-new architectures quantize last
- if a quantized checkpoint already exists from the publisher
  (Qwen, Gemma ship official quants) - prefer it, they are
  validated more deeply than a fresh local conversion
```

## Step 2: Calibration Data

PTQ minimizes weight reconstruction error **against the activations your traffic produces** — the calibration set is a proxy for that traffic, and its two properties are load-bearing:

```python
def build_calibration_texts(domain_texts, tokenizer,
                            num_samples=256, min_chars=200):
    """In-distribution strings; transformers tokenizes them
    internally for GPTQConfig, so pass raw text, not tensors."""
    seen = [t.strip() for t in domain_texts
            if len(t.strip()) >= min_chars]
    return seen[:num_samples]

# example: a code-focused model gets code, not wikitext
with open("code_samples.txt", encoding="utf-8") as f:
    domain_texts = f.read().split("\n\n")     # chunked documents

calibration_texts = build_calibration_texts(domain_texts, tokenizer)
```

```text
The two properties that decide calibration quality
1. IN-DISTRIBUTION: 256-512 samples from your actual domain.
   C4/wikitext defaults measure generic English; for a code,
   legal, or medical model they miscalibrate the scales that
   matter (the #1 cause of "GPTQ hurt my model")
2. SERVING-LENGTH: calibrate at the sequence length you serve
   at (or above). Scales fit on 512-token samples degrade on
   8k-token prompts - outlier statistics accumulate with depth

Budget guidance: 128 samples is the floor, 256-512 is the
standard, beyond ~1024 the gains flatten (4401).
```

## Step 3: Choose the Method

The decision is made by the deployment target — and the 2026 toolchain narrowed the options:

```text
Target                       Format + runtime
---------------------------  ------------------------------------
GPU datacenter, many users   GPTQ/AWQ W4A16 + vLLM
                             (H100-class: FP8 instead - W8A8,
                             near-lossless, no calibration)
CPU only / consumer devices  GGUF Q4_K_M + llama.cpp
Local single-user GPU        EXL2 or GGUF + exllamav2/llama.cpp
Accuracy-critical + data +   QAT (training-time; different budget,
compute budget               different lesson)

Deprecated, do not start new work on: standalone AutoGPTQ and
AutoAWQ repos (both archived/unmaintained). Use the
transformers-native configs and llm-compressor instead.
```

```python
# Config templates for the formats this guide runs in Step 4

GPTQ_CONFIG = dict(
    bits=4,
    group_size=128,     # 64 for stubborn layers (2x scales)
    desc_act=True,      # activation ordering - helps LLMs
)

GGUF_QUANT = "Q4_K_M"   # CPU sweet spot; Q5_K_M if quality-tight
EXL2_BITS = 4.5         # exl2 hits the target bpw with automatic
                        # per-layer mixed precision
```

Format deep-dives live in [4403](../4403-GGUF-Format.md) and [4404](../4404-EXL2-Format.md).

## Step 4: Run Quantization

### GPTQ via transformers (GPU serving path)

```python
import torch
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          GPTQConfig)

model_id = "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_id)

quant_config = GPTQConfig(
    bits=GPTQ_CONFIG["bits"],
    group_size=GPTQ_CONFIG["group_size"],
    desc_act=GPTQ_CONFIG["desc_act"],
    dataset=calibration_texts,      # your Step-2 texts
    tokenizer=tokenizer,
)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quant_config,
    device_map="auto",
    torch_dtype=torch.float16,
)

out_dir = "./models/llama-2-7b-w4a16-gptq"
model.save_pretrained(out_dir)
tokenizer.save_pretrained(out_dir)

# the saved checkpoint loads back like any HF model:
# AutoModelForCausalLM.from_pretrained(out_dir, ...)
```

```text
Notes
- quantization RUNS ON GPU: the full-precision model must fit
  during the pass (7B ~= 14GB FP16 + overhead) - a CPU-only
  box cannot GPTQ a 7B; use GGUF there instead
- requires a maintained GPTQ backend (gptqmodel); the legacy
  auto-gptq/optimum path is deprecated
- AWQ equivalent exists for loading pre-quantized checkpoints
  (AwqConfig); producing NEW AWQ quantizations now goes through
  llm-compressor (4402)
```

### GGUF (CPU path) — two steps

```bash
# 1) HF weights -> f16 GGUF (current converter name)
python convert_hf_to_gguf.py ./Llama-2-7b-hf \
    --outfile ./models/base-f16.gguf --outtype f16

# 2) quantize with the llama.cpp binary
./llama-quantize ./models/base-f16.gguf \
    ./models/llama-2-7b-Q4_K_M.gguf Q4_K_M
```

```bash
# optional: keep sensitive layers (attention) higher precision
python convert_hf_to_gguf.py ./Llama-2-7b-hf \
    --outfile ./models/mixed.gguf --outtype f16 \
    --tensor-type "ffn_=q8_0"
./llama-quantize ./models/mixed.gguf ./models/mixed-Q4_K_M.gguf Q4_K_M
```

### EXL2 (local GPU path)

```bash
# from the exllamav2 repo; -c is a calibration file (jsonl),
# -b the target bits-per-weight, -hf writes the HF config/tokenizer
python convert.py \
    -i ./Llama-2-7b-hf \
    -o ./models/llama-2-7b-exl2-4.5bpw \
    -c calibration.jsonl \
    -b 4.5 \
    -hf
```

### FP8 (Hopper-class datacenter path)

```text
On H100-class GPUs, FP8 (W8A8) has largely replaced INT4 for
serving: near-lossless quality, no calibration set required
with dynamic scaling, native tensor-core throughput.

Fastest route - let vLLM quantize at load time:
    vllm serve meta-llama/Llama-2-7b-hf --quantization fp8

For a saved FP8 checkpoint, produce it with llm-compressor
(vLLM's companion quantization library); its output is a
standard HF checkpoint vLLM serves natively.
```

## Step 5: Validate Before Shipping

Three independent gates. One green light is not a signal; three are.

### Gate 1: Perplexity on YOUR domain

```python
import torch

@torch.no_grad()
def evaluate_perplexity(model, tokenizer, texts, max_length=2048):
    """Tokenize FIRST - a raw-text dataset has no input_ids;
    weighted mean NLL over the whole corpus -> perplexity."""
    model.eval()
    device = next(model.parameters()).device
    total_nll, total_tokens = 0.0, 0

    for text in texts:
        ids = tokenizer(text, return_tensors="pt", truncation=True,
                        max_length=max_length).input_ids.to(device)
        if ids.size(1) < 2:
            continue
        loss = model(input_ids=ids, labels=ids).loss  # batch mean
        total_nll += loss.item() * ids.size(1)
        total_tokens += ids.size(1)

    return float(torch.exp(torch.tensor(total_nll / total_tokens)))
```

```text
Gate: perplexity delta vs FP16 <= 5% on your DOMAIN eval set.
Generic benchmarks (wikitext) can look fine while domain
capability fell apart - and vice versa. Measure both if you can.
```

### Gate 2: KL divergence vs the FP teacher

Perplexity is one aggregate number; KL catches *distributional* damage that an average hides:

```python
@torch.no_grad()
def prompt_kl(fp_model, q_model, tokenizer, prompt, device):
    ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    p = torch.log_softmax(fp_model(ids).logits, dim=-1)
    q = torch.log_softmax(q_model(ids).logits, dim=-1)
    return torch.nn.functional.kl_div(
        q, p, log_target=True, reduction="batchmean").item()
```

```text
Run 50+ REAL prompts through both models; watch for a tail of
high-KL prompts - a median of 0.05 with a tail at 3.0 means
specific capabilities broke. Investigate the tail before ship.
```

### Gate 3: Performance on the TARGET hardware

```python
import time
import torch

@torch.no_grad()
def benchmark_decode(model, tokenizer, prompt,
                     max_new_tokens=64, warmup=5, iters=20):
    model.eval()
    device = next(model.parameters()).device
    for _ in range(warmup):
        ids = tokenizer(prompt, return_tensors="pt").to(device)
        model.generate(**ids, max_new_tokens=8)

    start = time.perf_counter()
    out_tokens = 0
    for _ in range(iters):
        ids = tokenizer(prompt, return_tensors="pt").to(device)
        model.generate(**ids, max_new_tokens=max_new_tokens)
        out_tokens += max_new_tokens
    elapsed = time.perf_counter() - start
    return out_tokens / elapsed      # tokens/sec, single stream
```

```text
Caveat: this measures the transformers generate() loop, which
is NOT your serving throughput (no batching, no paged KV).
It is a same-harness comparison FP vs quantized - valid for the
relative claim. ABSOLUTE serving numbers come from the serving
stack's benchmark (vLLM benchmark_serving: TTFT + TPOT).
```

## Step 6: Deploy

### The honest answer: a real serving stack

```bash
# pre-quantized GPTQ/AWQ checkpoint, served directly
vllm serve ./models/llama-2-7b-w4a16-gptq --dtype float16

# FP8 quantization at load time (Hopper-class)
vllm serve meta-llama/Llama-2-7b-hf --quantization fp8
```

```text
Why vLLM instead of a generate() wrapper
- continuous batching (10-100x throughput at the same GPU)
- paged KV cache (memory scales with ACTUAL sequence lengths)
- OpenAI-compatible API + metrics for free
A hand-rolled FastAPI + model.generate service is a demo
pattern: one concurrent user saturates it. Only embed the model
in your own service when you specifically need in-process
control - and then use the pattern below, knowing its limits.
```

### Embedded-service pattern (only when you must)

```python
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_DIR = "./models/llama-2-7b-w4a16-gptq"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    app.state.model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR, torch_dtype=torch.float16, device_map="cuda")
    app.state.model.eval()
    yield

app = FastAPI(lifespan=lifespan)     # load once, not per request

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 128
    temperature: float = 0.7

@app.post("/generate")
def _generate_impl(req: GenerationRequest):
    tok = app.state.tokenizer
    model = app.state.model
    ids = tok(req.prompt, return_tensors="pt").to(model.device)

    sampling = {}
    if req.temperature > 0:
        sampling = dict(do_sample=True, temperature=req.temperature)

    out = model.generate(**ids,
                         max_new_tokens=req.max_tokens,
                         **sampling)
    n_new = out.shape[1] - ids.input_ids.shape[1]
    return {"text": tok.decode(out[0][ids.input_ids.shape[1]:],
                               skip_special_tokens=True),
            "tokens": n_new}
```

### Monitoring

```python
import time
from fastapi import Response
from prometheus_client import (Counter, Histogram,
                               generate_latest)

REQUESTS = Counter("generate_requests_total",
                   "Generation requests")
LATENCY = Histogram("generate_latency_seconds",
                    "End-to-end request latency")
TOKENS = Counter("generate_output_tokens_total",
                 "Output tokens generated")

@app.post("/generate")
def generate(req: GenerationRequest):
    REQUESTS.inc()
    with LATENCY.time():
        result = _generate_impl(req)      # the handler above
    TOKENS.inc(result["tokens"])
    return result

@app.get("/metrics")
def metrics():
    return Response(generate_latest(),
                    media_type="text/plain")
```

```text
What to alert on in production for a QUANTIZED model
- p95 latency and TTFT regressions (quant kernels + batching
  interact with load in non-obvious ways)
- output token distribution shifts vs the FP baseline (a slow
  quality regression, not a crash)
- fallback rate: if your stack can downgrade to FP16 on OOM,
  a rising fallback rate silently doubles your GPU footprint
```

## Production Checklist

```text
- [ ] License verified via Hub API for your actual use case
- [ ] Calibration: 256-512 in-distribution samples, serving-length
- [ ] Every quantization parameter recorded (format, bits,
      group_size, calibration set hash + count)
- [ ] Gate 1: perplexity delta <= 5% on DOMAIN eval
- [ ] Gate 2: KL vs FP teacher on 50+ real prompts, tail inspected
- [ ] Gate 3: TTFT/TPOT benchmarked on TARGET hardware + load
- [ ] Format <-> runtime pairing verified END-TO-END in the
      serving stack (load + generate, not just file exists)
- [ ] FP16 checkpoint retained for rollback
- [ ] Monitoring + alerting wired (latency, token distribution)
- [ ] Canary or shadow deployment before full traffic
```

## Common Issues

### Perplexity blowup after GPTQ

```text
Ordered fixes
1. calibration/domain mismatch -> rebuild Step 2 in-distribution
2. embeddings/lm_head quantized -> keep them FP (default in most
   recipes; verify in the saved config)
3. stubborn layers -> group_size 128 -> 64 (doubles scale memory,
   usually recovers most of the delta)
4. still broken -> desc_act=True if off, or bits 4 -> 8 for the
   worst layers via a mixed recipe (llm-compressor)
```

### Long prompts degrade, short ones are fine

```text
Calibration length < serving length. Recalibrate with
sequences at (or above) your production context size - outlier
statistics accumulate with depth, and short-sample scales
clip under long prompts.
```

### Quantized model will not load in the serving stack

```text
Format <-> runtime pairing is strict:
- GGUF runs in llama.cpp-family runtimes, NOT in vLLM/TRT-LLM
- EXL2 runs in exllamav2 only
- vLLM accepts GPTQ/AWQ/FP8-style HF checkpoints - if it
  rejects one, re-export via the maintained path rather than
  force an unsupported scheme
```

### Quantization OOMs on your box

```text
GPTQ needs the FP model resident on GPU during the pass
(7B ~= 14GB+). Options: a bigger GPU, CPU offload with a large
time penalty, or GGUF (converts from disk, needs no GPU).
```

## Best Practices

```text
1. Prefer publisher-released quantized checkpoints when they
   exist - deeper validation than a fresh local conversion
2. Calibration quality > algorithm choice: in-distribution
   samples at serving length fix more models than parameter
   tuning does
3. Validate with three gates (perplexity, KL tail, target-HW
   perf); any single gate can pass a broken model
4. Do not start new work on AutoGPTQ/AutoAWQ - transformers
   configs + llm-compressor are the maintained 2026 paths
5. Hopper-class datacenter serving: evaluate FP8 before INT4 -
   near-lossless W8A8 with zero calibration beats a 4-bit
   compromise when VRAM allows
6. Record calibration set hash + parameters with the artifact;
   an unexplained checkpoint cannot be reproduced or debugged
7. Keep the FP16 checkpoint until the quantized service has a
   production track record - rollback is the cheapest insurance
```

---

## Summary

Quantizing a model for production is a pipeline, not a one-liner: six steps - model selection, calibration data, method choice, the quantization run, validation gates, deployment - and each can independently turn the win into an incident. This guide walked the 2026 toolchain, where the standalone AutoGPTQ and AutoAWQ packages are unmaintained and GPTQ runs through the transformers-native config. Keep the production checklist pinned: validate perplexity and task metrics before shipping, benchmark on the target hardware, and treat any accuracy gap as a calibration-data smell first.

## References

### Related PROJECT-OMEGA Documents

- [4401: GPTQ](../4401-GPTQ.md)
- [4402: AWQ](../4402-AWQ.md)
- [4403: GGUF Format](../4403-GGUF-Format.md)
- [4404: EXL2 Format](../4404-EXL2-Format.md)
- [4409: Hardware-Specific Quantization Optimization](./4409-Hardware-Specific-Optimization.md)

---

## Next Steps

- Continue with: **[4409: Hardware-Specific Quantization Optimization](./4409-Hardware-Specific-Optimization.md)**
- Assessment: **[assessment/QUIZ.md](../assessment/QUIZ.md)**
