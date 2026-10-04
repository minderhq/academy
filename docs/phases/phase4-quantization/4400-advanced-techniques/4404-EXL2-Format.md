---
Document ID: 4404
Title: "4404: EXL2 Format"
Phase: 4
Module: 4400
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'advanced', 'optimization']
---

# 4404: EXL2 Format

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [What is EXL2?](#what-is-exl2)
- [EXL2 vs Other Formats](#exl2-vs-other-formats)
- [Converting to EXL2](#converting-to-exl2)
- [Running EXL2 Models](#running-exl2-models)
- [Streaming Inference](#streaming-inference)
- [Low VRAM Mode](#low-vram-mode)
- [Performance Optimization](#performance-optimization)
- [Benchmarking](#benchmarking)
- [EXL2 File Structure](#exl2-file-structure)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [EXL2 vs GGUF Decision Tree](#exl2-vs-gguf-decision-tree)
- [Summary](#summary)
- [Further Reading](#further-reading)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Position EXL2 in the format table — NVIDIA-GPU-only ExLlamaV2 format that mixes per-layer 2/3/4/5/6/8-bit quants to hit any average bitrate between 2 and 8 BPW; the v2 repo is archived, development continues on ExLlamaV3
- Run the two-pass conversion — `convert.py -i <hf_dir> -o <out_dir> -c calib.parquet -b 3.0` (one AVERAGE-BPW target, `-hb 6` head bits, parquet calibration or the built-in default; there is no `--out_file`, no comma-separated `--bits` list, no per-layer DSL)
- Load and generate with `ExLlamaV2DynamicGenerator(model=, cache=, tokenizer=)` — keyword args in that order, sampling via `ExLlamaV2Sampler.Settings` (temperature/top_p/token_repetition_penalty), `stop_conditions` taking token IDs or strings, `add_bos=True`
- Stream through the job API — `ExLlamaV2DynamicJob(input_ids=…)` enqueued, then `generator.iterate()` reading `result.get("text", "")` per chunk
- Right-size VRAM — `ExLlamaV2Cache(batch_size=…, lazy=True)` (there is no `max_batch_size` kwarg), `max_seq_len` dominating cache size, and `config.low_mem` as a faster-loading low-memory mode (not disk streaming)
- Debug quality by raising the average — re-quantize with a higher `-b` (3.0 → 4.5) and `-hb 8`; bit mixing is the converter's measurement pass, not a CLI you steer per layer

---

## Abstract

EXL2 is the quantization format for ExLlamaV2, a highly optimized inference library for NVIDIA GPUs.

## What is EXL2?

EXL2 (ExLlamaV2 Format) is designed specifically for GPU inference:

```text
EXL2 Features:
- Optimized for NVIDIA GPUs (CUDA kernels)
- Per-layer 2/3/4/5/6/8-bit mixing to hit any average BPW 2-8
- Bit assignment chosen by a measurement pass over calibration data
- Head layers (output) kept at higher precision (-hb, default 6)
```

## EXL2 vs Other Formats

| Format | Target | Speed (GPU) | VRAM Usage | CPU Support |
|--------|--------|-------------|------------|-------------|
| **EXL2** | GPU | Fastest | Low | No |
| **GGUF** | CPU/GPU | Fast | Medium | Yes |
| **GPTQ** | GPU | Medium | Medium | No |
| **AWQ** | GPU | Fast | Medium | No |

## Converting to EXL2

### Using ExLlamaV2

```bash
# Install ExLlamaV2 (the v2 repo is archived; v3 lives at
# turboderp-org/exllamav3 — same two-pass measurement flow)
uv pip install exllamav2

# Convert HF model to EXL2: -i source dir, -o output dir (also the
# converter's scratch space), -c parquet calibration dataset (omit for
# the built-in default), -b SINGLE average-BPW target
python convert.py \
    -i ./Llama-2-7b-hf \
    -o ./Llama-2-7b-exl2 \
    -c calibration_data.parquet \
    -b 4.0
# Resume: a non-empty -o dir resumes the conversion unless -nr is passed
```

### Bit-width Specification

```bash
# One average-BPW target — the converter's measurement pass then picks
# a per-layer mix (2/3/4/5/6/8-bit) whose weighted average lands on it
python convert.py -i ./model -o ./model-exl2 -b 4.0

# Head/output layers at higher precision (-hb, default 6; 2-6 and 8
# accepted — only 6 and 8 tend to matter in practice)
python convert.py -i ./model -o ./model-exl2 -b 3.0 -hb 8

# There is no per-layer CLI: "blk.0-10:6.0" style specs don't exist.
# Steering quality means raising the average (-b 4.5) and the head
# bits, and letting the measurement pass redistribute
```

## Running EXL2 Models

### Python API

```python
from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Cache,
    ExLlamaV2Tokenizer,
)
from exllamav2.generator import ExLlamaV2DynamicGenerator, ExLlamaV2Sampler

# Load config
config = ExLlamaV2Config()
config.model_dir = "./Llama-2-7b-exl2"
config.max_seq_len = 2048
config.scale_pos_emb = 1.0

# Load model
model = ExLlamaV2(config)
model.load()

# Load tokenizer
tokenizer = ExLlamaV2Tokenizer(config)

# Create cache
cache = ExLlamaV2Cache(model, max_seq_len=2048, lazy=True)

# Generate — keyword args: model, cache, tokenizer (in that order)
generator = ExLlamaV2DynamicGenerator(
    model=model,
    cache=cache,
    tokenizer=tokenizer,
)

settings = ExLlamaV2Sampler.Settings()
settings.temperature = 0.7
settings.top_k = 40
settings.top_p = 0.9
settings.token_repetition_penalty = 1.0

text = generator.generate(
    "The future of AI is",
    gen_settings=settings,
    max_new_tokens=128,
    add_bos=True,
)
print(text)
```

### Chat Completion

```python
from exllamav2.generator import ExLlamaV2DynamicGenerator, ExLlamaV2Sampler

# generator built as above — the dynamic generator has no
# append_message()/run() chat helpers; apply the model's chat template
# to the messages, then call generate()
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
]

prompt = tokenizer.apply_chat_template(messages)
settings = ExLlamaV2Sampler.Settings(temperature=0.0)

response = generator.generate(
    prompt=prompt,
    gen_settings=settings,
    max_new_tokens=256,
)
print(response)
```

## Streaming Inference

```python
from exllamav2.generator import ExLlamaV2DynamicJob

# The dynamic generator streams through JOBS: enqueue one per prompt,
# then iterate() yields lists of result dicts as tokens are produced —
# the loop ends when num_remaining_jobs() hits zero
input_ids = tokenizer.encode("The capital of France is", add_bos=True)

generator.enqueue(ExLlamaV2DynamicJob(input_ids=input_ids, max_new_tokens=128))

while generator.num_remaining_jobs():
    results = generator.iterate()
    for result in results:
        chunk = result.get("text", "")
        print(chunk, end="", flush=True)

print()
```

## Low VRAM Mode

```python
# Trim VRAM the three ways that actually exist: low_mem trades a bit of
# speed for lower memory (smaller CUDA-graph/attention buffers — it is
# NOT disk streaming; EXL2 loads weights to GPU), a shorter max_seq_len
# (the cache is sized from it), and a small batch_size
config = ExLlamaV2Config()
config.model_dir = "./Llama-2-7b-exl2"
config.max_seq_len = 4096
config.low_mem = True  # Lower memory, faster loading

model = ExLlamaV2(config)
model.load()

cache = ExLlamaV2Cache(
    model,
    max_seq_len=4096,
    lazy=True,
    batch_size=1,
)

generator = ExLlamaV2DynamicGenerator(
    model=model,
    cache=cache,
    tokenizer=tokenizer,
)
response = generator.generate(
    "Your prompt here",
    gen_settings=ExLlamaV2Sampler.Settings(temperature=0.0),
    max_new_tokens=512,
)
```

## Performance Optimization

### Batch Size Tuning

```python
# The dynamic generator batches automatically: every enqueued job shares
# the one cache, and batch_size reserves cache slots per concurrent job

# Single user
cache = ExLlamaV2Cache(model, max_seq_len=2048, batch_size=1)

# Eight concurrent jobs
cache = ExLlamaV2Cache(model, max_seq_len=2048, batch_size=8)
```

### Expert Quantization

```text
There is no per-layer bit DSL in convert.py — the measurement pass
distributes 2-8-bit quants across layers to hit the average you name.
Steering quality means two levers:

  -b 4.5      # higher average = more headroom everywhere
  -hb 8       # output/head layers at 8 bits; the pass protects the
              # layers its measurements flag as sensitive

(Explicit per-tensor bit control lives in the GPTQ/AWQ toolchains —
see 4401/4402 — or in QAT, see 4305.)
```

## Benchmarking

```python
import time
from exllamav2.generator import ExLlamaV2Sampler

def benchmark_exl2(generator, prompts):
    times = []
    for prompt in prompts:
        start = time.time()
        _ = generator.generate(
            prompt=prompt,
            gen_settings=ExLlamaV2Sampler.Settings(temperature=0.0),
            max_new_tokens=128,
            add_bos=True,
        )
        end = time.time()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    tokens_per_sec = 128 / avg_time

    return tokens_per_sec

prompts = ["The capital of France is"] * 10
tps = benchmark_exl2(generator, prompts)
print(f"Speed: {tps:.2f} tokens/sec")

# generate() also takes a LIST of prompts and runs them as one batch:
# generator.generate(prompt=["…"] * 100, max_new_tokens=1000)
```

## EXL2 File Structure

```text
Llama-2-7b-exl2/            # an ordinary HF-style output DIRECTORY —
│                           # there is no .exl2 file, no cache.calibration
├── config.json             # Model config (quantization_config notes BPW)
├── tokenizer.model         # SentencePiece tokenizer
├── output.safetensors      # Quantized weights (sharded when large)
└── measurement.json        # The measurement pass's per-layer sensitivity
                            # scores — a rerun against the same -o dir
                            # reuses these when resuming
```

## Troubleshooting

### Issue 1: Out of Memory

```python
# Solution: Enable low mem mode
config.low_mem = True

# Or reduce context length
config.max_seq_len = 2048  # Instead of 4096

# Or use lazy cache
cache = ExLlamaV2Cache(model, max_seq_len=2048, lazy=True)
```

### Issue 2: Slow First Generation

```python
# Solution: throwaway warm-up generation. The first generate() call pays
# kernel/CUDA-graph initialization; the dynamic generator has no
# warmup() method — run one short prompt and discard it
_ = generator.generate(
    prompt="hi",
    gen_settings=ExLlamaV2Sampler.Settings(temperature=0.0),
    max_new_tokens=8,
)
```

### Issue 3: Quality Degradation

```bash
# Solution: raise the average — the measurement pass redistributes bits
# toward the sensitive layers it found; there is no per-layer --bits DSL
python convert.py \
    -i ./model \
    -o ./model-exl2-4.5bpw \
    -c calibration_data.parquet \
    -b 4.5 \
    -hb 8
```

## Best Practices

1. **Target the average, not per-layer bits:** the measurement pass assigns bits by measured sensitivity
2. **Use low_mem when VRAM-bound:** a little speed for lower memory — it is not disk streaming; pick the BPW you can afford
3. **Warm up before benchmarking:** discard one short generate() after loading
4. **Keep calibration parquet handy:** the measurement pass scores sensitivity against it, and a non-empty -o dir lets you resume
5. **Check measurement.json:** it records the per-layer sensitivities the converter used

## EXL2 vs GGUF Decision Tree

```text
Need CPU inference?
└─ Yes: Use GGUF
└─ No: Have NVIDIA GPU?
    └─ Yes: Use EXL2 (faster)
    └─ No: Use GGUF
```

## Summary

EXL2 is ExLlamaV2's answer to one question: what does maximum inference speed on NVIDIA hardware look like? Its trick is per-layer variable bit-width - the converter allocates precision where sensitivity demands it within an average bitrate budget. This lesson covered choosing EXL2 over GGUF and when not to, converting and running models, streaming inference and the low-VRAM mode, and benchmarking honestly. The decision tree is the durable takeaway: GPU-bound single-user inference favors EXL2; most everything else favors GGUF.

## Further Reading

- **GitHub:** [https://github.com/turboderp-org/exllamav2](https://github.com/turboderp-org/exllamav2) (archived — successor: [https://github.com/turboderp-org/exllamav3](https://github.com/turboderp-org/exllamav3))
- **Conversion docs:** exllamav2 `doc/convert.md` (every convert.py flag)
- **Generator docs:** exllamav2 `doc/dynamic.md` (DynamicGenerator + job API)

## References

### Related Minder Academy Documents

- [4401: GPTQ](4401-GPTQ.md)
- [4402: AWQ](4402-AWQ.md)
- [4403: GGUF Format](4403-GGUF-Format.md)
- [4405: Sparsity + Quantization](4405-Sparsity-Quantization.md)
- [4406: 1.58-bit Quantization](4406-1.58-bit-Quantization.md)
- [4407: Ternary & Binary Networks](4407-Ternary-Binary.md)

---

## Next Steps

→ **[4405: Sparsity + Quantization](./4405-Sparsity-Quantization.md)** - Combining pruning with quantization
