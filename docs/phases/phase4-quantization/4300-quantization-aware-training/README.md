---
Document ID: 4300-QUANTIZATION-AWARE-TRAINING-README
Title: "4300: Quantization Aware Training (QAT)"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Prerequisites: [4100]
Estimated Time: 20 hours
Tags: ['module', 'quantization', 'qat']
---

# 4300: Quantization Aware Training (QAT)

## Module Overview

This module covers Quantization Aware Training (QAT), a technique to train models that perform well after quantization. Unlike Post-Training Quantization (PTQ), QAT simulates quantization effects during training, allowing the model to adapt to lower precision.

## Why QAT Matters

- **Better accuracy than PTQ**: Models learn to compensate for quantization loss
- **Extreme compression**: Enable 4-bit, 3-bit, even 2-bit inference
- **Production deployment**: Run LLMs on consumer hardware
- **Edge deployment**: Deploy models on mobile/IoT devices

## Learning Path

### Core Concepts (Start Here)
1. **[4301: QAT Foundations](./4301-QAT-Foundations.md)** - What is QAT, how it works, why it's better than PTQ
2. **[4302: Fake Quantization](./4302-Fake-Quantization.md)** - Straight-through estimators, quantization simulation
3. **[4303: QAT for Transformers](./4303-QAT-for-Transformers.md)** - Applying QAT to attention layers, embeddings, activations

### Advanced Techniques
4. **[4304: Low-bit QAT](./4304-Low-bit-QAT.md)** - 4-bit, 3-bit, 2-bit training strategies
5. **[4305: Quantization Configuration](./4305-Quantization-Configuration.md)** - Selecting which layers to quantize, per-channel vs per-tensor

### Practical Guides
6. **[guides/4306-PyTorch-QAT](./guides/4306-PyTorch-QAT.md)** - QAT with PyTorch native support
7. **[guides/4307-Transformers-QAT](./guides/4307-Transformers-QAT.md)** - QAT with Hugging Face Transformers
8. **[guides/4308-BitBlade-QAT](./guides/4308-BitBlade-QAT.md)** - Advanced QAT with bitsandbytes

## Prerequisites

Before starting this module, ensure you understand:

- **Quantization basics** (from 4100: Low-bit Quantization)
- **Transformer architecture** (from 3400: Architectures)
- **Training fundamentals** (from 2400: Pretraining)
- **PyTorch autograd** (how gradients flow through custom ops)

See [PREREQUISITES.md](./PREREQUISITES.md) for details.

## Assessment

Validate your knowledge with:

- **[assessment/QUIZ.md](./assessment/QUIZ.md)** - Test your understanding (20 questions, 80% to pass)
- **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** - Hands-on exercises

## Related Topics

- **4100: Low-bit Quantization** - PTQ techniques (GGUF, EXL2, AWQ)
- **4200: KV Cache** - Quantizing cache for memory efficiency
- **5100: PEFT** - Combining QAT with LoRA/QLoRA
- **2300: Framework Engineering** - Building QAT into ML frameworks

## Key Takeaways

After this module, you will be able to:

- ✅ Explain how QAT differs from PTQ
- ✅ Implement fake quantization with STE
- ✅ Apply QAT to transformer models
- ✅ Configure per-layer quantization schemes
- ✅ Train models for 4-bit inference
- ✅ Evaluate quantized model accuracy
- ✅ Debug common QAT issues

---

**Module Duration:** 8-10 hours

**Difficulty:** ⭐⭐⭐ Advanced
