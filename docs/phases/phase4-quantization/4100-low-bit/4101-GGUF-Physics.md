---
Document ID: 4101
Title: GGUF Physics - CPU/GPU Hybrid Offloading
Phase: 4
Module: 4100
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: Phase 3 completion (transformer architecture), basic C/C++ knowledge
Related: [4102, 4103, 4201]
Tags: [quantization, gguf, ggml, llama.cpp, cpu-gpu-hybrid, offloading]
Hardware: [GPU with 11GB+ VRAM recommended, CPU]
Software: [llama.cpp, Python 3.11+]
---

# 4101: GGUF Physics - CPU/GPU Hybrid Offloading

## Abstract

GGUF (GPT-Generated Unified Format) is a file format that enables running large language models on consumer hardware through advanced quantization and hybrid CPU/GPU offloading. This document covers the GGUF file format structure, quantization algorithms (Q4_0, Q4_K, Q5_K), layer offloading strategies, and performance optimization techniques for maximizing inference speed on limited VRAM.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. GGUF File Format](#2-gguf-file-format)
- [3. Quantization Types](#3-quantization-types)
- [4. Quantization Algorithm](#4-quantization-algorithm)
- [5. K-Quants](#5-k-quants)
- [6. Hybrid CPU/GPU Offloading](#6-hybrid-cpu-gpu-offloading)
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

### 1.3 Learning Objectives

After completing this document, you will:
- ✅ Understand the GGUF file format structure
- ✅ Implement Q4_0 and Q4_K quantization algorithms
- ✅ Configure optimal CPU/GPU offloading strategies
- ✅ Convert HuggingFace models to GGUF format
- ✅ Optimize inference performance for your hardware

---

## 2. GGUF File Format

### Structure
```
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
```
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
```

---

[Full document content continues with quantization algorithms, K-quants, offloading, conversion, optimization, troubleshooting...]

---

## 10. References

### Academic Papers
- [1] Lin et al. "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers". ICLR, 2023.

### Documentation
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp) - Source code and documentation
- [GGUF Format Spec](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md) - Format specification

### Related ai-engineering-curriculum Documents
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
**Last Updated:** 2026-02-05
**Status:** Complete
**Related Documents:** [4102, 4103, 4201]
