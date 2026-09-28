---
Document ID: 4400-ADVANCED-TECHNIQUES-README
Title: "4400: Advanced Quantization Techniques"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Beginner
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

✅ Apply GPTQ for accurate post-training quantization
✅ Use AWQ for activation-aware quantization
✅ Convert models to GGUF format
✅ Optimize models for EXL2 inference
✅ Combine sparsity with quantization
✅ Understand 1.58-bit quantization limits
✅ Deploy quantized models to production

---

**Module Duration:** 10-12 hours
**Difficulty:** Advanced
