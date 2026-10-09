---
Document ID: 4400-ADVANCED-TECHNIQUES-README
Title: "4400: Advanced Quantization Techniques"
Last Updated: 2026-10-09
Status: Complete
Difficulty: Advanced
Prerequisites: [4100, 4300]
Estimated Time: 31 hours
Tags: ['module', 'quantization', 'advanced']
---

# 4400: Advanced Quantization Techniques

## Module Overview

This module covers advanced quantization techniques beyond basic QAT, including GGUF/EXL2 formats, GPTQ, AWQ, and cutting-edge research methods.

## Why Advanced Techniques Matter

- **Extreme compression:** Push beyond 4-bit to 3-bit, 2-bit
- **Better accuracy:** Maintain performance at low bits
- **Faster inference:** Optimized formats for specific hardware
- **Specialized formats:** GGUF for CPU, EXL2 for GPU

## Learning Path

### Core Concepts
1. **[4401: GPTQ](./4401-GPTQ.md)** - Accurate 4-bit quantization without retraining
2. **[4402: AWQ](./4402-AWQ.md)** - Activation-aware quantization
3. **[4403: GGUF Format](./4403-GGUF-Format.md)** - llama.cpp file format and ecosystem
4. **[4404: EXL2 Format](./4404-EXL2-Format.md)** - ExLlamaV2 format for GPU inference

### Advanced Methods
5. **[4405: Sparsity + Quantization](./4405-Sparsity-Quantization.md)** - Combining pruning with quantization
6. **[4406: 1.58-bit Quantization](./4406-1.58-bit-Quantization.md)** - The frontier of extreme quantization
7. **[4407: Ternary & Binary Networks](./4407-Ternary-Binary.md)** - {-1, 0, +1} weights

### Practical Guides
8. **[guides/4408: Quantizing for Production](./guides/4408-Quantizing-for-Production.md)** - End-to-end quantization workflow
9. **[guides/4409: Hardware-Specific Optimization](./guides/4409-Hardware-Specific-Optimization.md)** - CPU, GPU, NPU, mobile

## Research Spotlight: GSQ-RCO (2026)

The newest entry in extreme low-bit quantization is **GSQ-RCO** from ISTA-DASLab, a two-part pipeline that pushes below uniform 4-bit without the usual accuracy cliff:

- **GSQ (Gumbel-Softmax Quantization)** - a post-training method that makes the discrete choice of quantization grid differentiable via a Gumbel-Softmax relaxation, so per-group scales are *learned* rather than searched. It matches vector-quantization accuracy at low bits while staying pure scalar quantization. Paper: [arXiv:2604.18556](https://arxiv.org/abs/2604.18556) - Code: [IST-DASLab/GSQ](https://github.com/IST-DASLab/GSQ)
- **RCO (Riemannian Constrained Optimization)** - the budget allocator: it treats the total size budget as a Riemannian manifold and assigns one of K quantization types to each tensor under an *exact* budget, using projected updates plus binary search. Paper: [arXiv:2605.00649](https://arxiv.org/abs/2605.00649)

Together, GSQ-RCO releases report ~3.5 bits-per-weight models that match or beat uniform 4-bit - the released GGUFs (for example [ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF)) fit a 27B model with 128K context into roughly 12 GB of VRAM. This is the same value proposition 4100 covers for uniform formats (GGUF, EXL2), applied per-tensor instead of per-model.

**Where it fits in this module:** read this after 4405-4407 - GSQ-RCO is the production-grade answer to the question those lessons raise: how low can bits go before accuracy collapses, and who decides which layer gets how many bits.

## Prerequisites

Before starting this module, ensure you understand:

- **Basic quantization** (from 4100: Low-bit Quantization)
- **QAT fundamentals** (from 4300: QAT)
- **Transformer architecture** (from 3400: Architectures)
- **PyTorch basics** (from 2200: Frameworks)

See [PREREQUISITES.md](./PREREQUISITES.md) for details.

## Assessment

Validate your knowledge with:

- **[assessment/QUIZ.md](./assessment/QUIZ.md)** - Test your understanding (20 questions, 80% to pass)
- **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** - Hands-on exercises

## Related Topics

- **4100: Low-bit Quantization** - GGUF, EXL2, AWQ basics
- **4200: KV Cache** - Quantizing attention cache
- **4300: QAT** - Quantization aware training
- **2300: Framework Engineering** - Building quantization into frameworks

## Key Takeaways

After this module, you will be able to:

- ✅ Apply GPTQ for accurate post-training quantization
- ✅ Use AWQ for activation-aware quantization
- ✅ Convert models to GGUF format
- ✅ Optimize models for EXL2 inference
- ✅ Combine sparsity with quantization
- ✅ Understand 1.58-bit quantization limits
- ✅ Deploy quantized models to production

---

**Module Duration:** 10-12 hours

**Difficulty:** ⭐⭐⭐ Advanced
