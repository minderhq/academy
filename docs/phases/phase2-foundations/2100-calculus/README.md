---
Document ID: 2100-CALCULUS-README
Title: "2100: Calculus for Deep Learning"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Prerequisites: []
Estimated Time: 8 hours

Tags: ['math', 'calculus', 'tensors', 'backpropagation', 'autograd']
---

# 2100: Calculus for Deep Learning

Build the mathematical engine of deep learning — tensor algebra by hand in PyTorch, then the chain rule as a computational graph you can differentiate.

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

This module covers the essential calculus concepts that power modern deep learning systems. From tensor algebra to backpropagation, you'll build the mathematical foundation needed to understand how neural networks learn.

**Why This Matters:**

- Every neural network training run relies on gradient descent and backpropagation
- Understanding derivatives enables you to debug optimization problems
- Tensor operations are the building blocks of all modern ML frameworks
- Strong calculus intuition helps with model architecture design

---

## Learning Objectives

After completing this module, you will be able to:

- **Tensor Operations**: Manipulate multi-dimensional arrays and understand broadcasting
- **Automatic Differentiation**: Grasp how frameworks compute gradients automatically
- **Backpropagation**: Derive and implement the backward pass for neural networks
- **Optimization Intuition**: Understand gradient flow, vanishing/exploding gradients
- **Chain Rule Mastery**: Apply chain rule to complex computational graphs

---

## Module Contents

Each lesson is written around runnable code — work through the examples, don't just read them.

### Lesson 2101 — Tensors, the Language of Deep Learning

[2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md)

- Tensor shapes and operations (element-wise, matrix multiplication, broadcasting)
- Einstein summation — from dot products to scaled dot-product attention in one notation
- Reductions, SVD/PCA, reshaping, slicing, and memory layout
- GPU tensors, tensor cores, and mixed precision
- AI patterns: linear layers, convolution as einsum, layer normalization

### Lesson 2102 — The Backpropagation Engine

[2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md)

- Chain rule for scalars and tensors, forward and backward passes on computational graphs
- How PyTorch autograd works under the hood
- Common gradient patterns (linear layer, ReLU, softmax + cross-entropy)
- Vanishing and exploding gradients — and the standard fixes
- Hessians, gradient accumulation, and best practices (zeroing, inference mode, checkpointing)

---

## Learning Path

1. **Verify readiness** with [2100: Calculus for Deep Learning - Prerequisites](./PREREQUISITES.md)
2. **[2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md)** — shapes, broadcasting, einsum, GPU tensors
3. **[2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md)** — chain rule, autograd, the backward pass
4. **Check understanding** with the [2100: Calculus - Quiz](./assessment/QUIZ.md)
5. **Apply it** with the [2100: Calculus - Practice](./assessment/PRACTICE.md) exercises

---

## Prerequisites

**Required:**

- [ ] Vectors and matrices — dot products and matrix multiplication at the by-hand level
- [ ] Derivatives and the chain rule — single-variable calculus is enough to start
- [ ] Python programming fundamentals, ideally with some NumPy

**Helpful:**

- A CUDA GPU for the 2101 GPU sections — every code example runs on CPU, and the GPU blocks are clearly marked and optional
- PyTorch installed — 2101 starts tensor knowledge from zero

**Review:** [2100: Calculus for Deep Learning - Prerequisites](./PREREQUISITES.md) for detailed requirements with runnable self-check examples.

---

## Assessment

### Knowledge Check

- **[2100: Calculus - Quiz](./assessment/QUIZ.md)** — 20 questions across both lessons, 80% to pass

### Practice Exercises

- **Format:** Hands-on coding exercises
- **Duration:** 2-3 hours
- **Topics:**
  - Compute derivatives analytically and with autograd
  - Run gradient descent in 1D and 2D
  - Apply the chain rule to composite functions
- **Location:** [2100: Calculus - Practice](./assessment/PRACTICE.md)

---

## Related Modules

- [2200: Deep Learning Frameworks](../2200-frameworks/README.md) — implement the tensor operations and autograd you just understood
- [Phase 2: Module 2300 - Framework Engineering](../2300-framework-engineering/README.md) — build them into working ML systems
- [\[3100\]: Attention Architectures](../../phase3-transformers/3100-attention/README.md) — gradient flow through attention layers
- [4100: Low-Bit Quantization](../../phase4-quantization/4100-low-bit/README.md) — calculus in quantization-aware training

---

## Time Commitment

| Activity | Time |
|----------|------|
| Reading (2101) | 2 hours |
| Experiments (2101) | 2 hours |
| Reading (2102) | 2 hours |
| Experiments (2102) | 2 hours |
| Quiz | 1 hour |
| Practice | 2-3 hours |
| **Total** | **11-12 hours** |

---

## Resources

**Essential Reading:**

- [Mathematics for Machine Learning](https://mml-book.github.io/) (Deisenroth, Faisal & Ong) — free PDF; the linear algebra and vector calculus chapters map directly onto this module
- [Deep Learning](https://www.deeplearningbook.org/) (Goodfellow, Bengio & Courville) — Chapter 2 (Linear Algebra), free to read online
- [CS231n Notes](https://cs231n.github.io/) (Stanford) — "Backpropagation, Intuitions" and the gradient-check walkthroughs

**Optional:**

- [The Matrix Calculus You Need For Deep Learning](https://explained.ai/matrix-calculus/) (Parr & Howard) — the vector-chain-rule reference Lesson 2102 leans on
- [Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) (3Blue1Brown) — geometric intuition for everything in 2101
- [Essence of Calculus](https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr) (3Blue1Brown) — derivatives and the chain rule, visualized

---

## Tips for Success

1. **Don't skip the math**: Understanding derivatives helps debug models
2. **Implement from scratch**: Build a simple autograd before trusting frameworks
3. **Visualize gradients**: Print shape and value at every stage of a backward pass
4. **Practice chain rule**: It's the foundation of backpropagation
5. **Connect to code**: Map every equation to a PyTorch operation and run it

---

## Common Pitfalls

1. **Getting lost in notation:** Focus on concepts, not just symbols
2. **Ignoring dimensionality:** Always track tensor shapes during operations
3. **Skipping manual implementation:** Using frameworks too early limits understanding
4. **Not checking gradients:** Verify autograd against finite differences when debugging

---

## Summary

- This module is the mathematical core of Phase 2: [tensor algebra](./2101-Tensor-Algebra.md) first, then [backpropagation](./2102-Backpropagation-and-Derivatives.md) — closed by a [quiz](./assessment/QUIZ.md) and [hands-on practice](./assessment/PRACTICE.md).
- Everything is runnable: each lesson's examples execute offline on CPU with PyTorch, GPU sections marked and optional.
- Plan for **11-12 hours** (8 hours lessons + 1 hour quiz + 2-3 hours practice).
- These two lessons are the prerequisite chain for the rest of Phase 2: 2200 implements what 2101 explains, 2300 engineers what 2102 derives.

---

## References

### Related Documents

- [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md) — shapes, broadcasting, einsum, GPU tensors
- [2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md) — chain rule, autograd, gradient patterns
- [2100: Calculus for Deep Learning - Prerequisites](./PREREQUISITES.md) — readiness check with runnable self-test examples
- [EXP-2101: Tensor Algebra](../../../../experiments/EXP_2101_TENSOR_ALGEBRA.md) — hands-on tensor exercises
- [EXP-2102: Backpropagation Experiment](../../../../experiments/EXP_2102_BACKPROPAGATION.md) — hands-on backprop exercises
- [Phase 2: Module 2300 - Framework Engineering](../2300-framework-engineering/README.md) — the next module that builds on this one

### External References

- [Mathematics for Machine Learning](https://mml-book.github.io/) — Deisenroth, Faisal & Ong; free PDF
- [Deep Learning](https://www.deeplearningbook.org/) — Goodfellow, Bengio & Courville; Chapter 2
- [CS231n Notes](https://cs231n.github.io/) — Stanford; backpropagation intuitions and gradient checks
- [The Matrix Calculus You Need For Deep Learning](https://explained.ai/matrix-calculus/) — Parr & Howard
- [Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) — 3Blue1Brown
- [Essence of Calculus](https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr) — 3Blue1Brown

---

## Next Steps

1. **Not reviewed yet?** Start with [2100: Calculus for Deep Learning - Prerequisites](./PREREQUISITES.md) and run its self-check examples.
2. **Work the lessons in order:** [2101](./2101-Tensor-Algebra.md) → [2102](./2102-Backpropagation-and-Derivatives.md) — each builds on the previous one.
3. **Close the loop:** take the [quiz](./assessment/QUIZ.md), then the [practice exercises](./assessment/PRACTICE.md).
4. **Continue to the next module:** [2200: Deep Learning Frameworks](../2200-frameworks/README.md)

**Related:** [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md) · [2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md) · [2200: Deep Learning Frameworks](../2200-frameworks/README.md)

**Experiment:** No EXP_21xx overview exists — start from [EXP-2101: Tensor Algebra](../../../../experiments/EXP_2101_TENSOR_ALGEBRA.md) (the hands-on companion to Lesson 2101).
