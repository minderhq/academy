---
Document ID: 5100-PEFT-README
Title: "5100: Parameter-Efficient Fine-Tuning (PEFT)"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Beginner
---

# 5100: Parameter-Efficient Fine-Tuning (PEFT)

## Module Overview

This module covers Parameter-Efficient Fine-Tuning techniques that enable adapting large language models to specific tasks with minimal computational resources. You'll master LoRA, QLoRA, and other PEFT methods.

**Why This Matters:**
- Fine-tuning a 70B model normally requires hundreds of GBs of VRAM
- PEFT methods reduce memory by 10-100x while maintaining quality
- Critical for customizing LLMs for specific domains or tasks
- Foundation of modern LLM adaptation workflows

## Learning Objectives

After completing this module, you will be able to:

- **LoRA Fundamentals**: Understand low-rank adaptation theory and implementation
- **QLoRA Pipelines**: Fine-tune quantized models with 4-bit precision
- **Hyperparameter Tuning**: Optimize rank, alpha, and dropout for PEFT
- **Multi-Adapter Systems**: Manage and compose multiple fine-tuned adapters
- **Production PEFT**: Deploy and serve PEFT models efficiently

## Module Contents

### [5101: LoRA Logic](./5101-LoRA-Logic.md)
**Low-Rank Adaptation Theory and Practice**

- LoRA mathematical foundation
- Rank decomposition and parameter efficiency
- Target module selection strategies
- Initializing LoRA weights
- Merging adapters with base models

**Experiments:**
- Implement LoRA from scratch
- Compare different rank configurations
- Measure quality vs parameter tradeoffs
- Profile memory and speed

### [5102: QLoRA Pipelines](./5102-QLoRA-Pipelines.md)
**4-bit Quantization + LoRA**

- QLoRA architecture and innovations
- 4-bit NormalFloat (NF4) quantization
- Double quantization and paged optimizers
- Training quantized models
- Hardware requirements and optimization

**Experiments:**
- Set up QLoRA training pipeline
- Fine-tune a quantized 7B model
- Compare QLoRA vs full fine-tuning
- Optimize memory usage

### 5104: LoRA Implementation Guide
**End-to-End LoRA Workshop** (Guide)

- Complete LoRA implementation walkthrough
- Hugging Face PEFT library
- Custom LoRA implementations
- Advanced techniques (DoRA, IA3, AdapterFusion)
- Production deployment strategies

**Guide:** [guides/5104-LoRA-Implementation-Guide.md](./guides/5104-LoRA-Implementation-Guide.md)
- [5103: Adapters](./5103-Adapters.md)

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 2100: Calculus (gradient computation)
- [ ] Module 2200: Frameworks (PyTorch proficiency)
- [ ] Module 2400: Pretraining (training fundamentals)
- [ ] Module 3100-3400: Transformer architectures
- [ ] GPU with 12GB+ VRAM (for QLoRA)

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)
### Practice Exercises
- **Format:** Complete fine-tuning projects
- **Duration:** 8-12 hours
- **Topics:**
  - Implement LoRA from scratch
  - Fine-tune models with QLoRA
  - Build multi-adapter systems
  - Deploy PEFT models
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **4100: Low-Bit Quantization** (quantization fundamentals)
- **5200: Alignment** (fine-tuning for alignment)
- **6100: Vector Embeddings** (embedding adaptation)
- **7200: Tools** (function calling with PEFT)

## Time Commitment

| Activity | Time |
|----------|------|
| Reading (5101) | 3 hours |
| Experiments (5101) | 3 hours |
| Reading (5102) | 3 hours |
| Experiments (5102) | 4 hours |
| Guide (5104) | 3 hours |
| Practice | 8-12 hours |
| **Total** | **24-28 hours** |

## Resources

**Essential Libraries:**
- Hugging Face PEFT
- bitsandbytes
- Axolotl (training framework)
- AutoTrain Advanced

**Essential Papers:**
- "LoRA: Low-Rank Adaptation of Large Language Models"
- "QLoRA: Efficient Finetuning of Quantized LLMs"
- "PEFT: Parameter-Efficient Fine-Tuning"

## Memory Comparison

| Method | 7B Model VRAM | 70B Model VRAM | Quality |
|--------|---------------|----------------|---------|
| Full Fine-tuning | ~120 GB | ~800 GB | 100% |
| LoRA (r=16) | ~16 GB | ~120 GB | 98-99% |
| QLoRA (4-bit) | ~12 GB | ~48 GB | 96-98% |
| QLoRA (4-bit, r=8) | ~10 GB | ~40 GB | 95-97% |

## LoRA Hyperparameters

| Parameter | Range | Effect | Default |
|-----------|-------|--------|---------|
| Rank (r) | 4-64 | Higher = more parameters | 16 |
| Alpha (α) | 8-128 | Scaling factor | 2×r |
| Dropout | 0-0.2 | Regularization | 0.05-0.1 |
| Target Modules | - | Which layers to adapt | q_proj, v_proj |

## Tips for Success

1. **Start with LoRA**: Understand basics before QLoRA
2. **Choose rank wisely**: r=16 is a good starting point
3. **Target specific modules**: q/v proj for most tasks
4. **Monitor overfitting**: Small datasets need lower rank
5. **Save adapters separately**: Keep base model unchanged

## Common Pitfalls

- **Rank too low**: Underfits complex tasks
- **Rank too high**: Wastes memory, may overfit
- **Wrong target modules**: All linear layers is usually unnecessary
- **Forgetting alpha**: Scaling factor matters for training dynamics
- **Not testing base model**: Always establish baseline

## When to Use PEFT

| Scenario | Recommended Approach |
|----------|---------------------|
| Custom domain adaptation | LoRA (r=16-32) |
| Single GPU setup | QLoRA (4-bit) |
| Multiple tasks | Multi-adapter setup |
| Rapid iteration | LoRA (small r) |
| Production deployment | Merge adapters |

## PEFT Method Comparison

| Method | Parameters | VRAM (7B) | Speed | Quality |
|--------|-----------|-----------|-------|---------|
| LoRA | 0.1-1% | Low | Fast | ⭐⭐⭐⭐⭐ |
| QLoRA | 0.1-1% | Very Low | Medium | ⭐⭐⭐⭐ |
| Adapter Layers | 1-5% | Medium | Fast | ⭐⭐⭐⭐ |
| Prefix Tuning | 0.01% | Very Low | Fast | ⭐⭐⭐ |
| IA³ | <0.1% | Very Low | Fast | ⭐⭐⭐⭐ |
| Full Fine-tuning | 100% | Very High | Medium | ⭐⭐⭐⭐⭐ |

---

**Next Module:** [5200: Alignment](../5200-alignment/README.md)

**Previous Module:** [4400: Advanced Techniques](../../phase4-quantization/4400-advanced-techniques/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 5 documentation.

