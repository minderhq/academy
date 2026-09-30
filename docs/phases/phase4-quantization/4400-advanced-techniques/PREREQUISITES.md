---
Document ID: 4400-PREREQUISITES
Title: "4400: Advanced Quantization Techniques - Prerequisites"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
Tags: ['prerequisites', 'quantization', 'advanced']
---

# 4400: Advanced Quantization Techniques - Prerequisites

## Before You Start

This module covers advanced quantization techniques beyond basic QAT.

**Required Knowledge:**

### Quantization Fundamentals
- INT8 vs INT4 vs FP16
- Scale and zero-point calculation
- Per-channel vs per-tensor quantization
- Post-training quantization

### Linear Algebra
- Matrix multiplication
- Singular Value Decomposition (SVD)
- Hessian matrix
- Outlier detection

### Optimization
- Gradient descent
- Second-order methods (Hessian)
- Optimal brain surgery (pruning)

### If you're not familiar:

**Review Resources:**
- "GPTQ: Accurate Post-Training Quantization" (Frantar et al., 2022)
- "AWQ: Activation-aware Weight Quantization" (Lin et al., 2023)
- GGUF documentation (llama.cpp)
- ExLlamaV2 documentation

**Estimated Review Time:** 4-5 hours

---

## Self-Assessment

Can you:
- [ ] Explain the difference between PTQ and QAT?
- [ ] Calculate optimal scale for quantization?
- [ ] Describe what makes a layer "sensitive" to quantization?
- [ ] Understand the trade-offs between different quantization formats?

**If YES:** Start with [4401: GPTQ](./4401-GPTQ.md)

**If NO:** Review the resources above first, especially:
- 4100: Low-bit Quantization
- 4300: Quantization Aware Training
