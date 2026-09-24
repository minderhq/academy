# Volume 2: AI/ML Foundations

**"The Mathematics of Intelligence"** - Deep dive into the calculus, linear algebra, and frameworks behind AI.

---

## 📚 Volume Overview

**Difficulty:** ⭐⭐ Intermediate
**Time:** 3-4 weeks (part-time)
**Prerequisites:** Volume 1, high school math (algebra, basic calculus), Python programming

### What You'll Learn

After completing this volume, you will be able to:
- ✅ Understand tensor operations and einsum notation
- ✅ Implement backpropagation from scratch
- ✅ Optimize PyTorch computational graphs
- ✅ Write basic CUDA kernels
- ✅ Understand TensorFlow XLA compilation

### Why This Volume Matters

Before understanding model architectures, fine-tuning, or optimization, you need to understand the **fundamental mathematics and computational frameworks** that power modern AI. This volume gives you:

- **Deep mathematical intuition** - Understand *why* models work, not just *how* to use them
- **Framework mastery** - Optimize code for performance
- **CUDA basics** - Bridge Python and GPU execution
- **Foundations for advanced topics** - Required for Volumes 3-7

---

## 🗺️ Learning Path

### Week 1: Tensor Algebra & Calculus

#### Day 1-3: Tensor Operations
**The fundamental data structure of AI**

1. **[2101: Tensor Algebra](../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)** (2-3 hours)
   - Tensor dimensions and shapes
   - Dot products and matrix multiplication
   - Einstein summation (einsum) notation
   - Broadcasting rules
   - GPU tensor operations

**Practice:**
```python
# You'll learn to write:
import torch

# Einstein summation
C = torch.einsum('ij,jk->ik', A, B)

# Broadcasting
D = torch.randn(3, 1, 2) + torch.randn(1, 4, 2)

# Batched operations
batch_result = torch.bmm(batch_A, batch_B)
```

2. **[Experiment: Tensor Algebra](../../experiments/EXP_2101_TENSOR_ALGEBRA.md)** (2 hours)
   - Hands-on tensor operations
   - Performance benchmarks
   - CPU vs GPU comparison

**Checkpoint:** You understand tensor operations and einsum

---

#### Day 4-5: Backpropagation & Derivatives
**How neural networks learn**

1. **[2102: Backpropagation](../phases/phase2-foundations/2100-calculus/2102-Backpropagation-and-Derivatives.md)** (2-3 hours)
   - Chain rule in computational graphs
   - Gradient computation
   - Automatic differentiation
   - Vanishing/exploding gradients
   - Gradient clipping

**Key Concepts:**
```
Forward pass: Compute output
Backward pass: Compute gradients
Update: Adjust weights using gradients

∂L/∂w = ∂L/∂a × ∂a/∂z × ∂z/∂w
```

2. **[Experiment: Backpropagation](../../experiments/EXP_2102_BACKPROPAGATION.md)** (2 hours)
   - Implement backprop from scratch
   - Compare with PyTorch autograd
   - Visualize gradient flow

**Checkpoint:** You understand how gradients are computed

---

### Week 2: Framework Deep Dive

#### Day 1-3: PyTorch Computational Graphs
**Understanding dynamic computation**

1. **[2201: PyTorch Graphs](../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)** (2-3 hours)
   - Dynamic vs Static graphs
   - Autograd engine
   - Computational graph tracing
   - Memory optimization
   - Gradient checkpointing

**Practice:**
```python
# You'll learn to:
# 1. Trace computation graph
import torchviz

x = torch.randn(2, 2, requires_grad=True)
y = x * 2
z = y.mean()
z.backward()
torchviz.make_dot(z)

# 2. Optimize memory with gradient checkpointing
from torch.utils.checkpoint import checkpoint

def custom_forward(x):
    return complex_function(x)

output = checkpoint(custom_forward, input_tensor)
```

2. **[Experiment: PyTorch Optimization](../../experiments/EXP_2201_PYTORCH_GRAPHS.md)** (2 hours)
   - Profile computation graphs
   - Optimize memory usage
   - Compare dynamic vs static

**Checkpoint:** You can optimize PyTorch code

---

#### Day 4-5: TensorFlow XLA & Acceleration
**Compiler optimizations**

1. **[2202: TensorFlow XLA](../phases/phase2-foundations/2200-frameworks/2202-TensorFlow-XLA-Compilers.md)** (2 hours)
   - XLA (Accelerated Linear Algebra)
   - JIT compilation
   - Fusion optimizations
   - TPUs and accelerators

**Key Concepts:**
```
Python Code → TensorFlow Graph → XLA Compiler → Optimized HLO → Device Code
```

2. **[Experiment: XLA Optimization](../../experiments/EXP_2202_TENSORFLOW_XLA.md)** (1 hour)
   - Benchmark XLA vs eager execution
   - Profile fused operations
   - Memory usage comparison

**Checkpoint:** You understand compilation optimization

---

### Week 3: CUDA & Low-Level Optimization

#### Day 1-4: CUDA Kernel Programming
**Bridging Python and GPU**

1. **[2203: CUDA Kernels](../phases/phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Syb-Level.md)** (3-4 hours)
   - CUDA programming model
   - Kernel launch and execution
   - Memory hierarchy (global, shared, registers)
   - Thread blocks and grids
   - Warp execution
   - Memory coalescing

**Practice:**
```python
# You'll learn to write CUDA kernels:
import torch

# Simple CUDA kernel
@torch.cuda.jit
def matmul_kernel(A, B, C):
    # Each thread computes one element
    row = torch.cuda.blockIdx.y * torch.cuda.blockDim.y + torch.cuda.threadIdx.y
    col = torch.cuda.blockIdx.x * torch.cuda.blockDim.x + torch.cuda.threadIdx.x

    # Compute dot product
    sum_val = 0.0
    for k in range(A.shape[1]):
        sum_val += A[row, k] * B[k, col]

    C[row, col] = sum_val
```

2. **[Experiment: CUDA Kernels](../../experiments/EXP_2203_CUDA_KERNELS.md)** (3-4 hours)
   - Write custom CUDA kernels
   - Profile kernel performance
   - Optimize memory access patterns
   - Compare with PyTorch implementations

**Checkpoint:** You can write basic CUDA kernels

---

#### Day 5-7: Pre-training Fundamentals (NEW)
**Understanding the complete training pipeline**

1. **[2401: Pre-training Fundamentals](../phases/phase2-foundations/2400-pretraining/2401-Pre-training-Fundamentals.md)** (4-5 hours)
   - Data collection and curation
   - Tokenizer training
   - Training curriculum design
   - Evaluation frameworks
   - Infrastructure requirements

**Key Topics:**
```python
# Public datasets for pre-training
datasets = {
    "Common Crawl": "100+ TB web data",
    "C4": "750GB cleaned web data",
    "RedPajama": "1.2T tokens (LLaMA reproduction)",
    "The Pile": "825GB curated diverse data",
    "SlimPajama": "627B tokens (cleaned RedPajama)",
    "Wikipedia": "20GB factual knowledge",
    "arXiv": "10GB scientific papers",
}

# Data pipeline
Collect → Filter → Deduplicate → Tokenize → Train

# Training curriculum
Stage 1 (30%): High-quality foundations (Wikipedia, Books)
Stage 2 (40%): Diverse web knowledge (C4, StackExchange)
Stage 3 (20%): Instructional data
Stage 4 (10%): Annealing on highest quality

# Compute estimation
# 7B model, 1T tokens, A100 GPUs:
# - Training time: ~21 days with 8 GPUs
# - Estimated cost: ~$12,000
```

2. **[LAB-006: Train Small Model](../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md)** (6-8 hours)
   - Prepare Wikipedia dataset
   - Train BPE tokenizer
   - Implement 10M parameter transformer
   - Train end-to-end
   - Evaluate and generate text

**Checkpoint:** You understand pre-training and can train a small model

---

#### Day 8: Development Tools

1. **[CHEAT-SHEET-003: Git](../learning-resources/cheat-sheets/CHEAT-SHEET-003-Git.md)** (reference)
   - Git for AI/ML projects
   - Version control workflows
   - Git LFS for large models

2. **[CHEAT-SHEET-004: Linux](../learning-resources/cheat-sheets/CHEAT-SHEET-004-Linux.md)** (reference)
   - Process management
   - GPU monitoring
   - System optimization

**Checkpoint:** You have essential development tools

---

## 🎯 Volume 2 Capstone Projects

### Project A: Implement Autograd from Scratch

**Time:** 4-6 hours
**Difficulty:** ⭐⭐⭐

**Tasks:**
1. Implement a Tensor class with automatic differentiation
2. Support basic operations (add, mul, matmul)
3. Implement backpropagation
4. Test on simple neural network
5. Compare with PyTorch autograd

**Skills Demonstrated:**
- Understanding of computational graphs ✅
- Gradient computation ✅
- Python programming ✅

### Project B: Optimize PyTorch Model

**Time:** 3-4 hours
**Difficulty:** ⭐⭐

**Tasks:**
1. Profile a PyTorch model
2. Identify bottlenecks
3. Apply optimizations:
   - Gradient checkpointing
   - Mixed precision
   - Memory-efficient attention
4. Benchmark improvements

**Skills Demonstrated:**
- PyTorch optimization ✅
- Profiling and debugging ✅
- Performance analysis ✅

### Project C: CUDA Kernel for Custom Operation

**Time:** 6-8 hours
**Difficulty:** ⭐⭐⭐⭐

**Tasks:**
1. Design a custom operation (e.g., specialized attention)
2. Implement CUDA kernel
3. Optimize memory access
4. Benchmark vs PyTorch
5. Document performance

**Skills Demonstrated:**
- CUDA programming ✅
- GPU optimization ✅
- Performance engineering ✅

---

## 📋 Volume 2 Checklist

Use this checklist to track your progress:

### Core Content (Required)
- [ ] **2101: Tensor Algebra** (2-3 hours)
- [ ] **EXP_2101: Tensor Algebra Experiment** (2 hours)
- [ ] **2102: Backpropagation** (2-3 hours)
- [ ] **EXP_2102: Backpropagation Experiment** (2 hours)
- [ ] **2201: PyTorch Graphs** (2-3 hours)
- [ ] **EXP_2201: PyTorch Graphs Experiment** (2 hours)
- [ ] **2202: TensorFlow XLA** (2 hours)
- [ ] **EXP_2202: XLA Experiment** (1 hour)
- [ ] **2203: CUDA Kernels** (3-4 hours)
- [ ] **EXP_2203: CUDA Experiment** (3-4 hours)
- [ ] **2401: Pre-training Fundamentals** (4-5 hours) (NEW)
- [ ] **2402: Large-Scale Training** (4-5 hours) (NEW)
- [ ] **2403: Evaluation Frameworks** (3-4 hours) (NEW)
- [ ] **LAB-006: Train Model from Scratch** (6-8 hours) (NEW)
- [ ] **CHEAT-SHEET-003: Git** (reference)
- [ ] **CHEAT-SHEET-004: Linux** (reference)

**Total Core Time:** ~50-55 hours (including new pre-training content)

### Capstone Projects (Choose 1)
- [ ] **Project A: Implement Autograd** (4-6 hours)
- [ ] **Project B: Optimize PyTorch Model** (3-4 hours)
- [ ] **Project C: CUDA Kernel** (6-8 hours)

---

## 🔗 Cross-References

### How Volume 2 Connects to Other Volumes:

**Tensor Algebra (2101) →**
- Volume 3: Understanding attention mechanisms
- Volume 4: Quantization arithmetic
- Volume 5: LoRA low-rank decomposition

**Backpropagation (2102) →**
- Volume 3: Training dynamics
- Volume 5: Fine-tuning and DPO
- Volume 7: Optimization strategies

**PyTorch Graphs (2201) →**
- Volume 3: Model architecture implementation
- Volume 4: Efficient inference
- Volume 6: RAG optimization

**CUDA Kernels (2203) →**
- Volume 3: Flash Attention implementation
- Volume 4: Custom quantization kernels
- Volume 7: Production optimization

---

## 📊 Volume 2 Statistics

| Metric | Value |
|--------|-------|
| **Core Documents** | 8 files (+3 pre-training guides) |
| **Experiments** | 5 experiments |
| **Labs** | 1 lab (LAB-006) |
| **Cheat Sheets** | 2 (Git, Linux) |
| **Capstone Projects** | 3 projects |
| **Estimated Time** | 50-55 hours (core) + 4-8 hours (project) |
| **Difficulty** | ⭐⭐ Intermediate |

---

## 💡 Key Takeaways

### Mathematical Foundations

**Tensors:**
```python
# Scalars (0D): x = 5
# Vectors (1D): x = [1, 2, 3]
# Matrices (2D): x = [[1, 2], [3, 4]]
# Tensors (3D+): x = torch.randn(batch, seq, hidden)
```

**Einsum Notation:**
```python
# Matrix multiplication: 'ij,jk->ik'
# Batch matmul: 'bij,bjk->bik'
# Dot product: 'i,i->'
# Transpose: 'ij->ji'
```

### Backpropagation

**Chain Rule:**
```
If y = f(x) and L = g(y)
Then dL/dx = dL/dy × dy/dx
```

**Gradient Flow:**
- Forward: Build computation graph
- Backward: Compute gradients via chain rule
- Update: Adjust weights using gradients

### CUDA Programming

**Key Concepts:**
- **Grid:** Collection of blocks
- **Block:** Collection of threads
- **Warp:** 32 threads executing together
- **Memory Hierarchy:** Registers > Shared > Global

---

## 🆘 Troubleshooting

### Common Issues in Volume 2

**Problem:** Einstein summation confusing
- **Solution:** Start with simple examples, use torch.einsum's debugging mode

**Problem:** Gradients are None
- **Solution:** Ensure `requires_grad=True` and operation is differentiable

**Problem:** CUDA kernel slower than PyTorch
- **Solution:** Profile memory access, check coalescing, consider shared memory

**Problem:** XLA not improving performance
- **Solution:** Check operation fusion, ensure compatible operations

For more help, see **[TROUBLESHOOTING-Common-Issues.md](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)**

---

## 🎓 After Volume 2

### You're Ready For:

**Volume 3: LLM Internals** - Understand transformer architecture
**Volume 4: Quantization** - Optimize model arithmetic
**Volume 5: Fine-Tuning** - Understand gradient-based adaptation

### Skills You've Gained:

```python
# You can now:
✅ Manipulate tensors efficiently
✅ Understand automatic differentiation
✅ Optimize PyTorch code
✅ Write basic CUDA kernels
✅ Understand pre-training pipeline
✅ Train small models from scratch
✅ Understand large-scale training (FSDP, DeepSpeed)
✅ Evaluate models comprehensively (MMLU, HellaSwag, GSM8K)
✅ Profile and debug AI code
✅ Use development tools effectively
```

---

## 🚀 Next Steps

1. **Track your progress** in [PROGRESS-TRACKER.md](../00-META/PROGRESS-TRACKER.md)
2. **Continue to Volume 3** for transformer internals
3. **OR skip to Volume 5** if you want to focus on fine-tuning
4. **Review the [VOLUME-GUIDE.md](../00-META/VOLUME-GUIDE.md)** for alternative learning paths

---

**Recommended Resources:**
- **[PyTorch Documentation](https://pytorch.org/docs/stable/)**
- **[CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)**
- **[Einstein Summation](https://rockt.github.io/2018/04/30/einsum)** - Excellent einsum tutorial

---

**Volume 2 Status:** 🟢 Complete
**Last Updated:** 2026-02-04
**Maintainer:** PROJECT-OMEGA Team
