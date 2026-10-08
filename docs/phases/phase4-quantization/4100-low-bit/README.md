---
Document ID: 4100-LOW-BIT-README
Title: "4100: Low-Bit Quantization"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Prerequisites: [1500]
Estimated Time: 16 hours
Tags: ['module', 'quantization', 'gguf']
---

# 4100: Low-Bit Quantization

## Module Overview

This module covers cutting-edge techniques for quantizing LLMs to extremely low bit widths (4-bit, 3-bit, and beyond). You'll learn how to run massive models on consumer hardware while preserving quality.

**Why This Matters:**

- Low-bit quantization enables LLMs on laptops and phones
- Memory reduction: 16-bit → 4-bit = 4x less memory
- Inference speedup: 2-4x faster with quantized kernels
- Critical for edge deployment and cost reduction

## Learning Objectives

After completing this module, you will be able to:

- **Quantization Fundamentals**: Understand precision, range, and quantization error
- **GGUF Format**: Work with the most popular quantization format for local LLMs
- **EXL2 and AWQ**: Master modern quantization schemes for optimal performance
- **Double Quantization**: Apply nested quantization for extreme compression
- **MXFP4 and NVFP4**: Quantize with the microscaling formats behind gpt-oss and Blackwell tensor cores
- **Quality Preservation**: Balance bit-width with model performance

## Module Contents

### [4101: GGUF Physics](./4101-GGUF-Physics.md)
**GGUF File Format & CPU/GPU Hybrid Offloading**

- GGUF format architecture and design
- Quantization grid and block-wise quantization
- Legacy Q4_0/Q8_0, K-quant (Q2_K through Q6_K), and I-quant (IQ codebook + imatrix) families
- Hybrid CPU/GPU offloading strategies
- GGUF conversion and performance optimization

**Experiments:**

- Convert models to GGUF format
- Compare different quantization levels
- Measure quality vs size tradeoffs
- Benchmark inference speed

### [4102: EXL2 and AWQ](./4102-EXL2-and-AWQ.md)
**EXL2, AWQ, and GPTQ — Extreme Quantization**

- EXL2 format and mixed-precision quantization
- AWQ (Activation-aware Weight Quantization)
- GPTQ gradient-based quantization
- Calibration dataset selection
- Format comparison and hardware fit

**Experiments:**

- Apply EXL2 quantization to models
- Implement AWQ quantization
- Compare AWQ vs GPTQ quality
- Optimize for specific hardware

### [4103: Double Quantization](./4103-Double-Quantization.md)
**Double Quantization & BitsAndBytes (bnb) Logic**

- Double quantization theory and benefits
- Quantizing quantization parameters
- BitsAndBytes implementation details
- Memory savings and quality impact
- Training with quantized weights (bnb)

**Experiments:**

- Implement double quantization
- Measure memory savings
- Analyze quality impact
- Compare with single quantization

### [4104: MXFP4 and NVFP4](./4104-MXFP4-and-NVFP4.md)
**Microscaling Formats - the Hardware-Native 4-Bit Generation**

- The shared microscaling recipe: e2m1 elements plus tiny per-block scales
- MXFP4's power-of-2 e8m0 scale per 32 and the pow2 tax it pays
- NVFP4's e4m3 scale per 16 plus the fp32 per-tensor second level
- The gpt-oss-20b selective-quantization config and its memory ledger
- transformers' Mxfp4Config and torchao's MXTensor surfaces

**Experiments:**

- Emulate e2m1 round-to-nearest in plain torch
- Quantize one weight both ways and compare relative error
- Measure the pow2 tax with per-block scale-use histograms
- Decode the gpt-oss quantization_config

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 2100: [Calculus for Deep Learning](../../phase2-foundations/2100-calculus/README.md) (understanding precision and error)
- [ ] Modules 3100-3400: [Transformer Architectures](../../phase3-transformers/3400-architectures/README.md)
- [ ] Python and NumPy proficiency
- [ ] Basic understanding of floating-point representation
- [ ] GPU access (for experimentation)

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** Quantization methods, GGUF, EXL2, AWQ
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Hands-on quantization projects
- **Duration:** 4 hours
- **Topics:**
  - Convert models to GGUF format
  - Implement EXL2 quantization
  - Apply double quantization
  - Benchmark and compare methods
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:

- **4200: KV Cache** (memory optimization techniques)
- **4300: Quantization-Aware Training** (training for quantization)
- **1400: LLMOps** (deploying quantized models)
- **3300: Decoding** (quantized inference)

## Time Commitment

| Activity | Time |
|----------|------|
| [4101: GGUF Physics](./4101-GGUF-Physics.md) | 4 hours |
| [4102: EXL2 and AWQ](./4102-EXL2-and-AWQ.md) | 4 hours |
| [4103: Double Quantization](./4103-Double-Quantization.md) | 4 hours |
| [4104: MXFP4 and NVFP4](./4104-MXFP4-and-NVFP4.md) | 4 hours |
| Quiz | 30 minutes |
| Practice | 4 hours |
| **Total** | **20.5 hours** |

## Resources

**Essential Tools:**

- llama.cpp (GGUF format)
- AutoGPTQ / AutoAWQ
- exllamav2 (EXL2 format)
- bitsandbytes

**Essential Papers:**

- "GPTQ: Accurate Post-Training Quantization"
- "AWQ: Activation-aware Weight Quantization"
- "QLoRA: Efficient Finetuning of Quantized LLMs"

## Quantization Comparison

| Method | Bits | Memory (7B) | Quality | Speed |
|--------|------|-------------|---------|-------|
| FP16 | 16 | 14 GB | Baseline | 1x |
| 8-bit | 8 | 7 GB | ~98% | 1.5x |
| 4-bit (GPTQ) | 4 | 3.5 GB | ~95% | 2x |
| 4-bit (AWQ) | 4 | 3.5 GB | ~96% | 2.2x |
| EXL2 mixed | 3-5 | 2.5-4 GB | ~94-96% | 2.5x |
| Double Q4 | ~3.5 | 3 GB | ~93% | 2.5x |

## Tips for Success

1. **Start with 4-bit**: It's the sweet spot for most use cases
2. **Measure quality**: Use perplexity and task-specific metrics
3. **Test on your data**: Generic benchmarks may not reflect your use case
4. **Consider hardware**: Different GPUs favor different formats
5. **Keep originals**: Always keep FP16 checkpoint for reference

## Common Pitfalls

1. **Over-quantizing:** Going below 3-bit usually hurts quality too much
2. **Wrong calibration:** Poor calibration data leads to bad quantization
3. **Ignoring outliers:** Some layers need higher precision
4. **Forgetting activation quantization:** Weights aren't everything
5. **Not testing end-to-end:** Benchmarks don't always reflect real usage

## Hardware Recommendations

| Setup | Best Format | Notes |
|-------|-------------|-------|
| NVIDIA GPU | EXL2 / GPTQ | Best CUDA kernels |
| Apple Silicon | GGUF (Metal) | Excellent MLX support |
| CPU | GGUF (Q4_K_M) | llama.cpp optimization |
| Mobile | GGUF (Q2_K) | Smallest footprint |

---

**Next Module:** [4200: KV Cache](../4200-kv-cache/README.md)

**Previous Module:** [3400: Architectures](../../phase3-transformers/3400-architectures/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 4 documentation.

