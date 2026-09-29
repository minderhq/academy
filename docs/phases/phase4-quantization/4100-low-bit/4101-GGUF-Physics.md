---
Document ID: 4101
Title: "4101: GGUF Physics - CPU/GPU Hybrid Offloading"
Phase: 4
Module: 4100
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: Phase 3 completion (transformer architecture), basic C/C++ knowledge
Related: [4102, 4103, 4201]
Tags: [quantization, gguf, ggml, llama.cpp, cpu-gpu-hybrid, offloading]
Hardware: [GPU with 11GB+ VRAM recommended, CPU]
Software: [llama.cpp, Python 3.13+]
---

# 4101: GGUF Physics - CPU/GPU Hybrid Offloading

## Abstract

GGUF (GPT-Generated Unified Format) is a file format that enables running large language models on consumer hardware through advanced quantization and hybrid CPU/GPU offloading. This document covers the GGUF file format structure, quantization algorithms (Q4_0, Q4_K, Q5_K), layer offloading strategies, and performance optimization techniques for maximizing inference speed on limited VRAM.

---

## Table of Contents

- [1. Overview](#1-overview)
- [Learning Objectives](#learning-objectives)
- [2. GGUF File Format](#2-gguf-file-format)
- [3. Quantization Types](#3-quantization-types)
- [4. Quantization Algorithm](#4-quantization-algorithm)
- [5. K-Quants](#5-k-quants)
- [6. Hybrid CPU/GPU Offloading](#6-hybrid-cpugpu-offloading)
- [7. GGUF Conversion](#7-gguf-conversion)
- [8. Performance Optimization](#8-performance-optimization)
- [9. Troubleshooting](#9-troubleshooting)
- [10. References](#10-references)

---

## 1. Overview

### 1.1 Purpose

GGUF enables running 7B-30B parameter models on consumer hardware by:
- Quantizing weights to 4-8 bits (4x+ compression)
- Offloading layers between CPU and GPU
- Using memory-mapped file loading

> **⚠️ Hardware Reality Check:**
> - **7B-13B models**: Run well on 8-12GB VRAM GPUs (e.g., RTX 3060, RTX 4060 Ti)
> - **30B-34B models**: Require 20-24GB VRAM (e.g., RTX 3090, RTX 4090) OR hybrid CPU/GPU offloading
> - **70B models**: Require 40GB+ VRAM (e.g., A100) OR very slow CPU-only inference
>
> Hybrid offloading trades speed for memory - larger models on smaller GPUs are possible but significantly slower

### 1.2 Prerequisites

- **Math:** Understanding of quantization, fixed-point arithmetic
- **Programming:** C/C++, Python
- **Previous:** [3402: Decoder-Only Models](../../phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md)

## Learning Objectives
After completing this document, you will:
- ✅ Understand the GGUF file format structure
- ✅ Implement Q4_0 and Q4_K quantization algorithms
- ✅ Configure optimal CPU/GPU offloading strategies
- ✅ Convert Hugging Face models to GGUF format
- ✅ Optimize inference performance for your hardware

---

## 2. GGUF File Format

### Structure
```text
GGUF File Structure:
┌─────────────────────────────────────────────┐
│  General Header (Magic + Version)           │
├─────────────────────────────────────────────┤
│  Metadata (KV pairs)                        │
│  - Architecture (llama, mistral, etc.)      │
│  - Vocabulary size                          │
│  - Context length                           │
│  - Model parameters                         │
├─────────────────────────────────────────────┤
│  Tensor Information                         │
│  - Name, shape, dtype, offset               │
├─────────────────────────────────────────────┤
│  Tensor Data (quantized weights)            │
└─────────────────────────────────────────────┘
```

### Header Layout
```c
// GGUF header structure
typedef struct {
    uint32_t magic;       // 0x46554747 ("GGUF")
    uint32_t version;     // Format version (3 is current)
    uint64_t tensor_count;    // Number of tensors
    uint64_t metadata_kv_count; // Number of metadata entries
} GGUFHeader;

// Each tensor has metadata
typedef struct {
    char* name;           // e.g., "blk.0.attn_q"
    uint32_t n_dims;      // Number of dimensions
    uint64_t* shape;      // Dimension sizes
    uint32_t dtype;       // Quantization type
    uint64_t offset;      // File offset
} GGUFTensorInfo;
```

---

## 3. Quantization Types

### GGUF Quantization Formats
```python
# Quantization format reference
GGUF_FORMATS = {
    # 4-bit formats (most popular)
    "Q4_0": {"bits": 4.5, "block_size": 32, "description": "Basic 4-bit"},
    "Q4_K": {"bits": 4.5, "block_size": 32, "description": "K-quants 4-bit"},

    # 5-bit formats
    "Q5_0": {"bits": 5.5, "block_size": 32, "description": "Basic 5-bit"},
    "Q5_K": {"bits": 5.5, "block_size": 32, "description": "K-quants 5-bit"},

    # 6-bit formats
    "Q6_K": {"bits": 6.5, "block_size": 32, "description": "K-quants 6-bit"},

    # 8-bit format
    "Q8_0": {"bits": 8.0, "block_size": 32, "description": "8-bit (near fp16 quality)"},
}
```

### VRAM Requirements (7B Model)
```text
Quantization    VRAM Usage    Quality (Perplexity)
───────────────────────────────────────────────────
Q4_0           ~4.5 GB       Baseline
Q4_K           ~4.5 GB       +5% better
Q5_0           ~5.5 GB       +10% better
Q5_K           ~5.5 GB       +12% better
Q6_K           ~6.5 GB       +15% better
Q8_0           ~8.5 GB       +20% better (near fp16)
fp16           ~14 GB        Reference

For 11GB VRAM GPU:
  - Best quality: Q5_K or Q6_K
  - Balanced: Q4_K or Q5_0
  - Maximum context: Q4_0

> **📊 Model Size Reference:**
> - 7B @ Q4_K: ~4.5 GB VRAM
> - 13B @ Q4_K: ~8 GB VRAM
> - 30B @ Q4_K: ~16 GB VRAM (requires RTX 3090/4090)
> - 70B @ Q4_K: ~35 GB VRAM (requires A100/H100 or heavy offloading)
```

---

## 4. Quantization Algorithm

### Q4_0: The Baseline Scheme

Q4_0 quantizes weights in **blocks of 32 values**. Each block stores one
FP16 scale and 32 four-bit integers:

```text
Q4_0 block (32 weights):
┌──────────────┬──────────────────────────────┐
│ scale (FP16) │ 32 × 4-bit quants (16 bytes) │
│    2 bytes   │         16 bytes             │
└──────────────┴──────────────────────────────┘
Size: 18 bytes / 32 weights = 4.5 bits per weight
```

```python
import numpy as np

def quantize_q4_0(weights: np.ndarray) -> dict:
    """Quantize one block of 32 FP16 weights to Q4_0."""
    assert weights.size == 32
    d = np.abs(weights).max() / 7.0          # symmetric scale
    if d == 0:
        d = 1e-8                              # all-zero block guard
    q = np.clip(np.round(weights / d), -8, 7).astype(np.int8)
    return {"d": d.astype(np.float16), "q": q}  # pack q as 4-bit nibbles

def dequantize_q4_0(block: dict) -> np.ndarray:
    return block["d"].astype(np.float32) * block["q"].astype(np.float32)
```

**Where:**
- **d**: per-block scale, maps the 4-bit integer range back to weight range
- **q**: integer codes clamped to [-8, 7]
- Error per weight is bounded by `d / 2` — smaller blocks adapt to local weight distributions

### Q4_K: Finer Scales

Q4_K keeps the 4-bit payload but adds a **hierarchy of scales**
(see Section 5), which shrinks the quantization error without adding
bits per weight.

---

## 5. K-Quants

### Super-Block Structure

K-quants group **256 weights into a super-block** of 8 sub-blocks of 32.
Each sub-block gets its own scale and offset; the 8 scales are themselves
compressed with a shared exponent:

```text
Q4_K super-block (256 weights, 144 bytes → 4.5 bpw):
┌────────────────────────────────────────────────────────┐
│ ql: 128 bytes  (256 × 4-bit quantized values)          │
│ qh: 12 bytes   (8 × 6-bit scales + min, split encoded) │
│ + shared 2-bit exponents and sign bits for scales      │
└────────────────────────────────────────────────────────┘
Weight ≈ d_scale[sub] × q4 + d_min[sub]
```

### Why K-Quants Win at the Same Size

| Property | Q4_0 | Q4_K |
|----------|------|------|
| Weights per super-block | 32 | 256 |
| Independent scales | 1 | 8 |
| Handles asymmetric ranges | No (symmetric only) | Yes (min offset) |
| Perplexity penalty vs FP16 | Baseline | ~5% better |
| Bits per weight | 4.5 | 4.5 |

> **📊 Rule of Thumb:**
> - `Q4_K_M` (medium) is the default recommendation for balanced size/quality
> - `Q4_K_S` (small) when every 100 MB matters
> - `Q6_K` when you have the VRAM — near-lossless for most models
> - Legacy `Q4_0`/`Q5_0` remain for tool compatibility, not for quality

---

## 6. Hybrid CPU/GPU Offloading

### The `-ngl` Knob

llama.cpp offloads whole transformer layers to the GPU with `--n-gpu-layers`:

```bash
# Offload 24 of 32 layers, keep 8 on CPU
./llama-server -m model-q4_k_m.gguf -ngl 24 -c 4096
```

```text
VRAM budget = model weights (offloaded layers)
            + KV cache (grows with context length - ALWAYS on GPU)
            + compute buffers (~200-500 MB)

RAM budget = weights of remaining CPU layers
```

### What Actually Bottlenecks Speed

Decode speed is **memory-bandwidth-bound**: each generated token requires
reading every active weight once. When some layers live on the CPU, those
layers are read from system RAM (25-100 GB/s) instead of VRAM (200-900 GB/s),
so partial offload performance drops sharply, not linearly:

```text
Illustrative: 7B Q4_K_M, RTX 3060 + DDR4
──────────────────────────────────────────
-ngl 32 (all)      ~35-45 tokens/s
-ngl 28            ~12-15 tokens/s
-ngl 24             ~7-9 tokens/s
-ngl 0  (CPU only)  ~5-7 tokens/s
```

> **⚠️ Practical Threshold:**
> Either the model fits fully on the GPU (fast), or a large fraction spills
> to CPU (slow). Offloading "just a few layers" of a model that mostly runs
> on CPU yields little benefit — the CPU layers still dominate.

### Choosing a Configuration

| GPU VRAM | Fully offloaded target |
|----------|------------------------|
| 8 GB     | 7-8B @ Q4_K_M |
| 12 GB    | 13B @ Q4_K_M, or 7-8B @ Q6_K |
| 24 GB    | 30B+ @ Q4_K_M, or 13B @ Q8_0 |
| 48 GB+   | 70B @ Q4_K_M |

---

## 7. GGUF Conversion

### Two-Step: FP16 Export, Then Quantize

```bash
# Step 1: convert Hugging Face weights to (unquantized) GGUF
python convert_hf_to_gguf.py ./my-model-hf \
    --outtype f16 \
    --outfile my-model-f16.gguf

# Step 2: quantize from the FP16 master
./llama-quantize my-model-f16.gguf my-model-q4_k_m.gguf Q4_K_M
```

**Requirements and pitfalls:**
- The HF directory must contain tokenizer files (`tokenizer.json` /
  `tokenizer.model`) and the model config
- **Merge LoRA adapters first** (`model.merge_and_unload()` in PEFT) —
  converters do not apply adapters
- Always quantize from the FP16 master; quantizing an already-quantized
  file compounds error
- For chat models, verify the chat template is detected (`--chat-template`
  override if not)

---

## 8. Performance Optimization

### Decode Is Bandwidth, Prefill Is Compute

| Phase | Bound by | Optimization |
|-------|----------|--------------|
| Prompt processing (prefill) | Compute | More GPU layers, larger `-ub` batch |
| Token generation (decode) | Memory bandwidth | Lower bpw, fewer CPU layers |

### Checklist

```bash
# A well-tuned consumer setup
./llama-server -m model-q4_k_m.gguf \
    -ngl 99 \
    -c 8192 \
    -ctk q8_0 -ctv q8_0 \
    -fa \
    -t 8 \
    --mlock
```

- **`-ctk q8_0 -ctv q8_0`**: quantize the KV cache — roughly halves KV
  memory for ~1% quality cost (details: [4201](../4200-kv-cache/4201-Context-Window-Physics.md))
- **`-fa`**: FlashAttention — faster prompt processing, lower buffer memory
- **`-t N`**: set to *physical* cores; hyper-threads usually hurt
- **`--mlock`**: pin weights in RAM (skip if RAM-tight; mmap is the default and fine for most)
- **Measure, don't guess**: `./llama-bench -m model.gguf -ngl 99 -p 512 -n 128`

### Speculative Decoding

Pair a small draft model with the main model to raise decode throughput —
see [4202: Speculative Decoding](../4200-kv-cache/4202-Speculative-Decoding.md).

---

## 9. Troubleshooting

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| `CUDA out of memory` at load | Weights + KV cache exceed VRAM | Lower quant (Q4_K_S), reduce `-ngl`, reduce `-c`, add `-ctk/-ctv q8_0` |
| `invalid magic` / load failure | Corrupted or truncated download | Re-download; verify SHA256 |
| Gibberish output | Bad conversion or wrong quant source | Re-convert from FP16 master with `llama-quantize` |
| < 2 tokens/s despite GPU | Most layers still on CPU | Check `-ngl`; watch VRAM usage — if far under capacity, raise `-ngl` |
| Out of system RAM while loading | `--no-mmap` with tight RAM | Drop `--no-mmap`, let mmap page weights from disk |
| Slow prompt processing | Prefill on CPU, or tiny batch | Raise `-ngl`, increase `-ub`/`-b` |
| Thread contention on hybrid CPUs | Scheduler spreads over E-cores | Pin `-t` to P-cores; benchmark both settings |

---

## 10. References

### Academic Papers
- [1] Lin et al. "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers". ICLR, 2023.

### Documentation
- [llama.cpp GitHub](https://github.com/ggml-org/llama.cpp) - Source code and documentation
- [GGUF Format Spec](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md) - Format specification

### Related PROJECT-OMEGA Documents
- [4102: EXL2 and AWQ](./4102-EXL2-and-AWQ.md) - VRAM-only quantization
- [4103: Double Quantization](./4103-Double-Quantization.md) - BitsAndBytes 4-bit
- [4201: Context Window Physics](../4200-kv-cache/4201-Context-Window-Physics.md) - KV cache optimization

### Experiments
- [EXP_4101: GGUF](../../../../experiments/EXP_4101_GGUF.md) - Hands-on GGUF experiments

### External Resources
- [The.llama.cpp Blog](https://llama-cpp-python.readthedocs.io/) - Python bindings guide

---

## Next Steps

- Continue with: **[4102: EXL2 and AWQ](./4102-EXL2-and-AWQ.md)**
- Practical: **[LAB-001: Docker & LLM](../../../learning-resources/labs/LAB-001-Docker-LLM.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**

---

**Document ID:** 4101
**Status:** Complete
**Related Documents:** [4102, 4103, 4201]
