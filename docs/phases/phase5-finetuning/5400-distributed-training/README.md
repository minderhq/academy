---
Document ID: 5400-DISTRIBUTED-TRAINING-README
Title: "5400: Distributed Training"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Prerequisites: [5300]
Estimated Time: 21 hours
Tags: ['module', 'training', 'distributed']
---

# 5400: Distributed Training

## Module Overview

This module covers distributed training techniques for scaling model training across multiple GPUs and nodes.

## Why Distributed Training Matters

- **Scale:** Train models that don't fit on one GPU
- **Speed:** Parallelize computation for faster training
- **Large batches:** Enable larger batch sizes for better convergence
- **Resource utilization:** Make full use of available hardware

## Learning Path

1. **[5401: Data Parallelism](./5401-Data-Parallelism.md)** - DP, DDP, FSDP
2. **[5402: Model Parallelism](./5402-Model-Parallelism.md)** - Pipeline, tensor parallel
3. **[5403: Mixed Precision Training](./5403-Mixed-Precision.md)** - FP16, BF16, automatic mixed precision
4. **[5404: Distributed Optimization](./5404-Distributed-Optimization.md)** - Gradient synchronization, all-reduce
5. **[5405: FSDP2 and torchao](./5405-FSDP2-and-torchao.md)** - Per-parameter sharding, float8/QAT quantized training
6. **[5406: Distributed LR Scaling](./5406-Distributed-LR-Scaling.md)** - The linear rule, the stability wall, warmup sizing, the critical batch size

## Prerequisites

Before starting this module, ensure you understand:

- **PyTorch basics** (from 2200: Frameworks)
- **Training loops** (from 2400: Pretraining)
- **Gradient descent** (from 2100: Calculus)

See [PREREQUISITES.md](./PREREQUISITES.md) for details.

## Key Takeaways

After this module, you will be able to:

✅ Implement data parallel training with DDP
✅ Use FSDP for sharding large models
✅ Apply model parallelism techniques
✅ Use mixed precision training
✅ Optimize distributed training performance
✅ Shard models with FSDP2's fully_shard and train through torchao quantization
✅ Scale the learning rate with world size under the linear rule, the wall, and a correctly sized warmup

---

**Module Duration:** 10-12 hours
**Difficulty:** ⭐⭐⭐ Advanced


## Assessment

- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)
