# 2200: Deep Learning Frameworks

## Module Overview

This module dives deep into the architecture and internals of modern deep learning frameworks. You'll understand how PyTorch, TensorFlow, and JAX work under the hood, from computational graphs to CUDA kernels.

**Why This Matters:**
- Frameworks are the tools you'll use daily for LLM development
- Understanding internals helps debug complex model issues
- Performance optimization requires knowledge of graph execution
- Custom kernel writing becomes necessary for advanced operations

## Learning Objectives

After completing this module, you will be able to:

- **Computational Graphs**: Understand dynamic vs static graph execution
- **Framework Internals**: Grasp autograd, memory management, and execution engines
- **Compiler Technology**: Learn XLA, TorchDynamo, and graph optimization
- **CUDA Programming**: Write custom GPU kernels for performance
- **Cross-Framework Skills**: Navigate PyTorch, TensorFlow, and JAX effectively

## Module Contents

### 2201: PyTorch Computational Graphs
**Dynamic Graphs and Autograd Systems**

- PyTorch architecture overview
- Dynamic vs static computational graphs
- Autograd engine internals
- Tensor lifecycle and memory management
- TorchScript compilation

**Experiments:**
- Build a minimal autograd system
- Profile PyTorch graph execution
- Implement custom autograd functions

### 2202: TensorFlow XLA and Compilers
**Accelerated Linear Algebra and Graph Optimization**

- TensorFlow 2.x architecture
- XLA (Accelerated Linear Algebra) compiler
- Graph optimization passes
- TPU execution and bridging
- tf.function and AutoGraph

**Experiments:**
- XLA compilation analysis
- Performance profiling with TPUs
- Custom graph optimizations

### 2203: CUDA Kernel Programming
**GPU Kernel Development for LLMs**

- CUDA programming fundamentals
- Thread hierarchy and memory model
- Writing custom CUDA kernels
- Kernel fusion for attention mechanisms
- Performance optimization techniques

**Experiments:**
- Implement vector addition kernel
- Write a fused attention kernel
- Profile and optimize GPU kernels

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 2100: Calculus (tensor operations, derivatives)
- [ ] Strong Python programming skills
- [ ] Basic C/C++ understanding
- [ ] GPU fundamentals (CUDA basics)
- [ ] Linux command line proficiency

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** Framework architecture, graphs, CUDA
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Advanced coding and kernel development
- **Duration:** 4-6 hours
- **Topics:**
  - Build a mini-PyTorch autograd
  - Write custom CUDA kernels
  - Optimize graph execution
  - Cross-framework model conversion
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **2100: Calculus** - Mathematical foundations for autograd
- **2300: Framework Engineering** - Building production ML systems
- **2400: Pretraining** - Framework usage at scale
- **4100: Quantization** - Custom quantization operators

## Time Commitment

| Activity | Time |
|----------|------|
| Reading (2201) | 3 hours |
| Experiments (2201) | 3 hours |
| Reading (2202) | 2 hours |
| Experiments (2202) | 2 hours |
| Reading (2203) | 4 hours |
| Experiments (2203) | 6 hours |
| Quiz | 30 minutes |
| Practice | 4-6 hours |
| **Total** | **24-26 hours** |

## Resources

**Essential Reading:**
- PyTorch Internals Documentation
- TensorFlow Developer Guide
- CUDA C Programming Guide

**Optional:**
- "Deep Learning with PyTorch" (Stevens et al.)
- "Programming Massively Parallel Processors" (Hwu & Kirk)

## Tips for Success

1. **Start with PyTorch**: It's the most LLM-friendly framework
2. **Profile everything**: Use profilers to understand execution
3. **Read source code**: Framework source is educational
4. **Experiment with kernels**: Write simple CUDA kernels first
5. **Compare frameworks**: Implement same model in PyTorch and TensorFlow

## Common Pitfalls

- **Ignoring memory management**: GPU memory is limited and expensive
- **Over-optimizing early**: Profile before optimizing
- **Skipping C++**: Many framework internals are C++ based
- **Not using autograd properly**: Manual gradients are error-prone
- **CPU vs GPU confusion**: Always verify tensor device placement

## Framework Comparison

| Feature | PyTorch | TensorFlow | JAX |
|---------|---------|------------|-----|
| Graph Type | Dynamic | Static/Dynamic | Functional |
| Research Friendliness | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Production Ready | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| LLM Ecosystem | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Learning Curve | Medium | Steep | Steep |

---

**Next Module:** [2300: Framework Engineering](../2300-framework-engineering/README.md)

**Previous Module:** [2100: Calculus](../2100-calculus/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 2 documentation.

---

**Last Updated:** 2026-02-04
