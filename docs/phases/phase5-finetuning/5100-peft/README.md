---
Document ID: 5100-PEFT-README
Title: "5100: Parameter-Efficient Fine-Tuning (PEFT)"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Prerequisites: [4100]
Estimated Time: 18 hours
Tags: ['module', 'finetuning', 'peft']
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
- **Model Merging**: Combine fine-tuned models with task vectors, TIES sign election, DARE sparsification, and checkpoint soups
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
**4-bit Fine-Tuning on Consumer Hardware**

- QLoRA architecture and innovations
- 4-bit NormalFloat (NF4) quantization
- Double quantization and paged optimizers
- Training quantized models
- Merging QLoRA weights back into the base model

**Experiments:**
- Set up QLoRA training pipeline
- Fine-tune a quantized 7B model
- Compare QLoRA vs full fine-tuning
- Optimize memory usage

### [5103: Adapters](./5103-Adapters.md)
**The Full PEFT Design Space Beyond LoRA**

- Bottleneck adapters
- Soft prompts: prompt and prefix tuning
- IA³ activation scaling and Compacter
- Adapter fusion
- Method comparison and choosing a method

**Experiments:**
- Compare adapter architectures
- Apply prompt/prefix tuning
- Benchmark IA³ vs LoRA
- Select a method for a task profile

### 5104: LoRA Implementation Guide
**LoRA Workshops: From Scratch to Multi-Adapter** (Guide)

- LoRA architecture review
- Implementation 1: LoRA from scratch
- Implementation 2: LoRA with transformers
- Implementation 3: QLoRA (4-bit LoRA)
- Implementation 4: Multi-adapter LoRA

**Guide:** [guides/5104-LoRA-Implementation-Guide.md](./guides/5104-LoRA-Implementation-Guide.md)

### [5105: Model Merging](./5105-Model-Merging.md)
**Task Vectors, TIES, DARE, and Checkpoint Soups**

- Task vectors and the lambda dose
- Sign conflicts: TIES trim-elect-merge
- DARE drop-and-rescale
- SLERP vs linear interpolation
- Checkpoint soups and the mergekit surface

**Experiments:**
- Sweep lambda on a two-task merge
- Break naive addition with sign conflicts
- Verify DARE's expectation preservation in Monte Carlo
- Average checkpoint soups and probe the same-task boundary

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 2100: [Calculus for Deep Learning](../../phase2-foundations/2100-calculus/README.md) (gradient computation)
- [ ] Module 2200: [Deep Learning Frameworks](../../phase2-foundations/2200-frameworks/README.md) (PyTorch proficiency)
- [ ] Module 2400: [LLM Pretraining](../../phase2-foundations/2400-pretraining/README.md) (training fundamentals)
- [ ] Modules 3100-3400: [Transformer Architectures](../../phase3-transformers/3400-architectures/README.md)
- [ ] GPU with 12GB+ VRAM (for QLoRA)

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** LoRA theory, QLoRA pipelines, adapter methods
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Complete fine-tuning projects
- **Duration:** 8 hours
- **Topics:**
  - Implement LoRA from scratch
  - Fine-tune models with QLoRA
  - Build multi-adapter systems
  - Deploy PEFT models
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **[4100: Low-Bit Quantization](../../phase4-quantization/4100-low-bit/README.md)** (quantization fundamentals)
- **[5200: LLM Alignment](../5200-alignment/README.md)** (fine-tuning for alignment)
- **[6100: Vector Embeddings](../../phase6-rag/6100-vector/README.md)** (embedding adaptation)
- **[7200: Tool Calling and Function Execution](../../phase7-agentic/7200-tools/README.md)** (function calling with PEFT)

## Time Commitment

| Activity | Time |
|----------|------|
| [5101: LoRA Logic](./5101-LoRA-Logic.md) | 5 hours |
| [5102: QLoRA Pipelines](./5102-QLoRA-Pipelines.md) | 5 hours |
| [5103: Adapters](./5103-Adapters.md) | 5 hours |
| Guide ([5104](./guides/5104-LoRA-Implementation-Guide.md)) | 5 hours |
| [5105: Model Merging](./5105-Model-Merging.md) | 3 hours |
| Quiz | 30 minutes |
| Practice | 8 hours |
| **Total** | **31.5 hours** |

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

1. **Rank too low:** Underfits complex tasks
2. **Rank too high:** Wastes memory, may overfit
3. **Wrong target modules:** All linear layers is usually unnecessary
4. **Forgetting alpha:** Scaling factor matters for training dynamics
5. **Not testing base model:** Always establish baseline

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

