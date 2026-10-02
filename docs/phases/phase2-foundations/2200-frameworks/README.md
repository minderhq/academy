---
Document ID: 2200-README
Title: "2200: Deep Learning Frameworks"
Phase: 2
Module: 2200
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Estimated Time: 12 hours

Prerequisites: See PREREQUISITES.md
Related: See References
Tags: ['frameworks', 'pytorch', 'autograd', 'tensorflow', 'xla', 'cuda']
---

# 2200: Deep Learning Frameworks

One stack, three viewpoints — how frameworks execute your model (dynamic graphs), how compilers optimize it (XLA), and how the hardware actually computes it (CUDA kernels).

---

## Contents

- [Module Overview](#module-overview)
- [Learning Objectives](#learning-objectives)
- [Module Contents](#module-contents)
- [Learning Path](#learning-path)
- [Prerequisites](#prerequisites)
- [Assessment](#assessment)
- [Related Modules](#related-modules)
- [Time Commitment](#time-commitment)
- [Resources](#resources)
- [Tips for Success](#tips-for-success)
- [Common Pitfalls](#common-pitfalls)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Module Overview

Frameworks are the layer you touch every day as an ML engineer — and the layer you debug when training slows down, memory runs out, or a kernel underperforms. This module takes PyTorch's dynamic graphs, TensorFlow's XLA compiler, and CUDA's execution model apart so the machinery is no longer a black box.

**Why This Matters:**

- Every training and inference system you will build runs on top of these frameworks
- Debugging performance means reading what the framework, the compiler, and the GPU each did to your model
- Custom autograd functions and custom kernels are how research code escapes framework limits
- Understanding static vs dynamic graphs and AOT vs JIT compilation explains why frameworks behave so differently

---

## Learning Objectives

After completing this module, you will be able to:

- **Graph Models**: Explain dynamic vs static computational graphs and pick the right mental model for a debugging session
- **Autograd Internals**: Inspect `.grad_fn` graphs and write custom `torch.autograd.Function` subclasses
- **Compiler Thinking**: Enable and profile XLA, understand operation fusion and HLO, and reason about what compilers can and cannot do
- **GPU Literacy**: Describe the CUDA execution model, the memory hierarchy, and tensor cores well enough to profile and tune kernels
- **Performance Diagnosis**: Move from a slow model to a hypothesis about dispatch, fusion, or memory — with evidence

---

## Module Contents

Each lesson is written around runnable code — work through the examples, don't just read them.

### Lesson 2201 — How Frameworks Execute: PyTorch's Dynamic Graphs

[2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md)

- Dynamic vs static graphs — and what each trades away
- Computational graph construction and `grad_fn` internals
- Dynamic control flow and custom autograd functions
- Graph optimization, debugging, and memory management

### Lesson 2202 — How Compilers Optimize: TensorFlow and XLA

[2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md)

- What XLA is and how to enable it (JIT and AOT)
- Operation fusion and HLO (High-Level Operations) instructions
- Memory optimization and GPU compilation with tensor cores
- Performance profiling, best practices, and troubleshooting

### Lesson 2203 — How the Hardware Computes: CUDA Kernels

[2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Programming.md)

- GPU architecture overview and the CUDA execution model
- Writing CUDA kernels and the memory hierarchy
- PyTorch CUDA integration and tensor core programming
- Optimization techniques and CUDA debugging

---

## Learning Path

1. **Verify readiness** with [2200: Deep Learning Frameworks - Prerequisites](./PREREQUISITES.md)
2. **[2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md)** — dynamic graphs, autograd internals, custom functions
3. **[2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md)** — fusion, HLO, profiling with XLA
4. **[2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Programming.md)** — execution model, memory hierarchy, kernels
5. **Check understanding** with the [2200: Frameworks - Quiz](./assessment/QUIZ.md), then **apply it** with the [2200: Frameworks - Practice](./assessment/PRACTICE.md) exercises

---

## Prerequisites

**Required:**

- [ ] Comfortable Python — classes, decorators, and context managers (the framework's control surface)
- [ ] Autograd basics from 2102: `requires_grad`, `.backward()`, `.grad`, and why graphs matter
- [ ] Tensor fundamentals: shapes, broadcasting, and device placement

**Helpful:**

- A CUDA GPU for the GPU sections of 2202/2203 — every code example runs on CPU where noted, and GPU blocks are clearly marked and optional; no CUDA toolchain is required (PyTorch ships its own kernels)
- C++ or another systems-language exposure, for 2203's kernel listings

**Review:** [2200: Deep Learning Frameworks - Prerequisites](./PREREQUISITES.md) for detailed requirements with runnable self-check examples.

---

## Assessment

### Knowledge Check

- **[2200: Frameworks - Quiz](./assessment/QUIZ.md)** — 20 questions across the three lessons, 80% (16/20) to pass

### Practice Exercises

- **Format:** Hands-on coding exercises
- **Duration:** 4-6 hours
- **Topics:**
  - Build custom autograd functions and inspect graph internals
  - Enable XLA and measure fusion effects
  - Profile a small model and attribute time to dispatch, memory, or kernels
- **Location:** [2200: Frameworks - Practice](./assessment/PRACTICE.md)

---

## Related Modules

- [2100: Calculus for Deep Learning](../2100-calculus/README.md) — the backward-pass math these frameworks automate
- [Phase 2: Module 2300 - Framework Engineering](../2300-framework-engineering/README.md) — turn framework knowledge into engineered training systems
- [2400: LLM Pretraining](../2400-pretraining/README.md) — run the stack at pretraining scale
- [\[3100\]: Attention Architectures](../../phase3-transformers/3100-attention/README.md) — graph and kernel behavior inside attention workloads
- [4100: Low-Bit Quantization](../../phase4-quantization/4100-low-bit/README.md) — compiler and kernel implications of quantized compute

---

## Time Commitment

| Activity | Time |
|----------|------|
| Lesson 2201 (PyTorch graphs) | 4 hours |
| Lesson 2202 (XLA compilers) | 4 hours |
| Lesson 2203 (CUDA kernels) | 4 hours |
| Quiz | 1 hour |
| Practice | 4-6 hours |
| **Total** | **17-19 hours** |

---

## Resources

**Essential Reading:**

- [PyTorch Tutorials](https://docs.pytorch.org/tutorials/) — official tutorials; the autograd and nn.Module walkthroughs map onto Lesson 2201
- [TensorFlow Tutorials](https://www.tensorflow.org/tutorials) — official tutorials; XLA integration context for Lesson 2202
- [CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-programming-guide/index.html) (NVIDIA) — the reference behind Lesson 2203

**Optional:**

- [XLA: Accelerated Linear Algebra](https://openxla.org/xla) (OpenXLA) — the compiler's own overview, architecture, and backends
- [PyTorch Internals](https://blog.ezyang.com/2019/05/pytorch-internals/) (Edward Z. Yang) — tensor structure, dispatch, autograd, and the codebase layout

---

## Tips for Success

1. **Inspect, don't trust**: print `.grad_fn` chains until graph construction feels concrete
2. **Compare the three layers**: run the same model through autograd, XLA, and a hand-written kernel mental model
3. **Profile before optimizing**: every performance claim in these lessons starts with a measurement
4. **Keep GPU code optional**: the CPU paths teach the same concepts; use a GPU when you have one
5. **Read the framework source**: the PyTorch internals essay makes the codebase navigable

---

## Common Pitfalls

1. **Memorizing framework APIs instead of the execution model:** APIs change; dispatch, graphs, and kernels persist
2. **Assuming fusion is free:** compilers change numerics slightly (float32 rounding), and not every fusion is profitable
3. **Mixing devices silently:** a CPU tensor next to a CUDA tensor is the most common runtime error in this module
4. **Optimizing without a baseline:** measure first — 2202's profiling sections exist for a reason

---

## Summary

- This module explains the machinery under every training run from three angles: [how frameworks execute](./2201-PyTorch-Computational-Graphs.md) (dynamic graphs), [how compilers optimize](./2202-TensorFlow-XLA-Compilers.md) (XLA), and [how GPUs compute](./2203-CUDA-Kernel-Programming.md) (CUDA kernels) — closed by a [quiz](./assessment/QUIZ.md) and [hands-on practice](./assessment/PRACTICE.md).
- Everything core is runnable on CPU with PyTorch; GPU and XLA sections are marked and optional.
- Plan for **17-19 hours** (12 hours lessons + 1 hour quiz + 4-6 hours practice).
- Position in Phase 2: 2100 taught the math these frameworks automate, 2200 the machinery itself, and 2300 turns that machinery into engineered training systems.

---

## References

### Related Documents

- [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md) — dynamic graphs, autograd internals
- [2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md) — fusion, HLO, profiling
- [2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Programming.md) — execution model, memory hierarchy
- [2200: Deep Learning Frameworks - Prerequisites](./PREREQUISITES.md) — readiness check with runnable self-test examples
- [EXP-2201: PyTorch Computational Graphs](../../../../experiments/EXP_2201_PYTORCH_GRAPHS.md) — hands-on graph exercises
- [EXP-2202: TensorFlow XLA Optimization](../../../../experiments/EXP_2202_TENSORFLOW_XLA.md) — hands-on XLA exercises
- [EXP-2203: CUDA Kernels](../../../../experiments/EXP_2203_CUDA_KERNELS.md) — hands-on CUDA exercises
- [Phase 2: Module 2300 - Framework Engineering](../2300-framework-engineering/README.md) — the next module that builds on this one

### External References

- [PyTorch Tutorials](https://docs.pytorch.org/tutorials/) — official PyTorch tutorials
- [TensorFlow Tutorials](https://www.tensorflow.org/tutorials) — official TensorFlow tutorials
- [CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-programming-guide/index.html) — NVIDIA
- [XLA: Accelerated Linear Algebra](https://openxla.org/xla) — OpenXLA project
- [PyTorch Internals](https://blog.ezyang.com/2019/05/pytorch-internals/) — Edward Z. Yang

---

## Next Steps

1. **Not reviewed yet?** Start with [2200: Deep Learning Frameworks - Prerequisites](./PREREQUISITES.md) and run its self-check examples.
2. **Work the lessons in order:** [2201](./2201-PyTorch-Computational-Graphs.md) → [2202](./2202-TensorFlow-XLA-Compilers.md) → [2203](./2203-CUDA-Kernel-Programming.md) — each layer builds on the previous one.
3. **Close the loop:** take the [quiz](./assessment/QUIZ.md), then the [practice exercises](./assessment/PRACTICE.md).
4. **Continue to the next module:** [Phase 2: Module 2300 - Framework Engineering](../2300-framework-engineering/README.md)

**Related:** [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md) · [2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md) · [2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Programming.md)

**Experiment:** No EXP_22xx overview exists — start from [EXP-2201: PyTorch Computational Graphs](../../../../experiments/EXP_2201_PYTORCH_GRAPHS.md) (the hands-on companion to Lesson 2201).
