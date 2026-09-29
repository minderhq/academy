---
Document ID: 2101
Title: "2101: Tensor Algebra and Linear Algebra for AI"
Phase: 2
Module: 2100
Last Updated: 2026-09-27
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['math', 'calculus', 'tensors', 'backpropagation']
---

# 2101: Tensor Algebra and Linear Algebra for AI

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Tensor Fundamentals](#tensor-fundamentals)
- [Tensor Operations](#tensor-operations)
- [Einstein Summation (einsum)](#einstein-summation-einsum)
- [Tensor Manipulations](#tensor-manipulations)
- [Reduction Operations](#reduction-operations)
- [GPU Tensor Operations](#gpu-tensor-operations)
- [Common Patterns in AI](#common-patterns-in-ai)
- [Memory Considerations](#memory-considerations)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Distinguish scalar, vector, matrix, and higher-rank tensors by rank and shape, and read an AI shape such as (B, C, H, W) or (B, H, L, D) into its axes
- Predict broadcasting results from the right-alignment rules and choose between matmul, bmm, and batched matmul for a given shape
- Translate matrix multiply, dot product, outer product, transpose, and batched matmul into einsum index notation and read a spec like `ij,jk->ik` back into prose
- Reshape, permute, and slice tensors while tracking contiguity, and explain when `view` avoids the copy that `reshape` must make
- Contrast reduction operations (sum, mean, max, top-k) with SVD/PCA dimensionality reduction and project data onto the top-k principal components
- Move tensors across CPU/CUDA devices, train with `torch.amp` autocast and GradScaler, and size a 7B model's fp16/int8/int4 memory footprint

---

## Abstract
Tensor algebra is the mathematical foundation of deep learning. Understanding tensor operations, dimensions, and the Einstein summation convention is essential for implementing and optimizing neural networks on GPU hardware.

## Tensor Fundamentals

### Scalar, Vector, Matrix, Tensor
```text
Scalar (0-rank tensor):    x = 5
Vector (1-rank tensor):    x = [1, 2, 3, 4]
Matrix (2-rank tensor):    x = [[1, 2], [3, 4]]
Tensor (3-rank tensor):    x = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]

In PyTorch:
scalar = torch.tensor(5)
vector = torch.tensor([1, 2, 3, 4])
matrix = torch.tensor([[1, 2], [3, 4]])
tensor3d = torch.tensor([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
```

### Tensor Shapes and Dimensions
```python
import torch

x = torch.randn(2, 3, 4, 5)
print(x.shape)      # torch.Size([2, 3, 4, 5])
print(x.ndim)       # 4
print(x.size(0))    # 2
print(x.numel())    # 2 * 3 * 4 * 5 = 120

# Common shapes for AI:
# Image batch:    (B, C, H, W) = (32, 3, 224, 224)
# Sequence:       (B, L, D) = (8, 512, 768)
# Attention:      (B, H, L, L) = (8, 12, 512, 512)
```

## Tensor Operations

### Element-wise Operations
```python
import torch

A = torch.tensor([[1, 2], [3, 4]])
B = torch.tensor([[5, 6], [7, 8]])

# Addition (element-wise)
C = A + B  # [[6, 8], [10, 12]]

# Multiplication (element-wise)
D = A * B  # [[5, 12], [21, 32]]

# Broadcasting
A = torch.tensor([[1.0], [2.0], [3.0]])       # (3, 1)
B = torch.tensor([[10.0, 20.0, 30.0, 40.0]])  # (1, 4)
C = A + B              # (3, 4): [[11, 21, 31, 41],
                       #          [12, 22, 32, 42],
                       #          [13, 23, 33, 43]]

# Broadcasting rules:
# 1. Align dimensions on the right
# 2. Dimensions must be equal OR one of them is 1
# 3. Missing dimensions are treated as 1
```

### Matrix Multiplication
```python
A = torch.randn(3, 4)  # (3, 4)
B = torch.randn(4, 5)  # (4, 5)

C = torch.matmul(A, B)      # (3, 5)
C = A @ B                   # Same, Python 3.5+
C = torch.mm(A, B)          # Same, 2D only

# Batch matrix multiplication
A = torch.randn(10, 3, 4)   # (10, 3, 4)
B = torch.randn(10, 4, 5)   # (10, 4, 5)
C = torch.bmm(A, B)         # (10, 3, 5)

# For higher dimensions, use matmul
A = torch.randn(2, 3, 4, 5)
B = torch.randn(2, 3, 5, 6)
C = torch.matmul(A, B)      # (2, 3, 4, 6)
```

## Einstein Summation (einsum)

### The Einstein Notation
```text
Principle: Sum over repeated indices

ij,jk->ik  means:
  Σ_j A[i,j] * B[j,k] = C[i,k]

This is matrix multiplication!
```

### Common einsum Patterns
```python
import torch

# Matrix multiplication
A = torch.randn(3, 4)
B = torch.randn(4, 5)
C = torch.einsum('ij,jk->ik', A, B)  # (3, 5)

# Dot product (vectors)
a = torch.randn(5)
b = torch.randn(5)
c = torch.einsum('i,i->', a, b)  # scalar

# Outer product
a = torch.randn(3)
b = torch.randn(4)
C = torch.einsum('i,j->ij', a, b)  # (3, 4)

# Batch matrix multiplication
A = torch.randn(10, 3, 4)
B = torch.randn(10, 4, 5)
C = torch.einsum('bij,bjk->bik', A, B)  # (10, 3, 5)

# Transpose
A = torch.randn(3, 4)
B = torch.einsum('ij->ji', A)  # (4, 3)

# Sum over dimensions (indices missing from the output are summed away)
A = torch.randn(3, 4, 5)
B = torch.einsum('ijk->ij', A)  # (3, 4) - k is summed over
```

### Attention with einsum
```python
# Scaled dot-product attention
def attention_einsum(Q, K, V):
    """
    Q, K, V: (batch, heads, seq_len, head_dim)
    """
    # Score = Q @ K^T / sqrt(d_k)
    scores = torch.einsum('bhid,bhjd->bhij', Q, K) / (Q.size(-1) ** 0.5)

    # Softmax over sequence dimension
    attn_weights = torch.softmax(scores, dim=-1)

    # Output = weights @ V
    output = torch.einsum('bhij,bhjd->bhid', attn_weights, V)

    return output

# Example usage
B, H, L, D = 8, 12, 512, 64
Q = K = V = torch.randn(B, H, L, D)
output = attention_einsum(Q, K, V)
```

## Tensor Manipulations

### Reshaping
```python
x = torch.arange(12)  # [0, 1, 2, ..., 11]

# Reshape (must preserve total elements)
y = x.reshape(3, 4)   # [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]
y = x.view(3, 4)      # Same, but view doesn't copy data

# Flatten
y = x.flatten()       # [0, 1, 2, ..., 11]

# Squeeze/unsqueeze
x = torch.randn(1, 3, 1, 4)
y = x.squeeze()       # Remove dimensions of size 1: (3, 4)
y = x.unsqueeze(0)    # Add dimension at position 0: (1, 1, 3, 1, 4)

# Permute (transpose multiple dimensions)
x = torch.randn(2, 3, 4)
y = x.permute(2, 0, 1)  # (4, 2, 3)
```

### Slicing and Indexing
```python
x = torch.arange(24).reshape(2, 3, 4)

# Index first dimension
y = x[0]           # (3, 4)

# Slice
y = x[:, 1:, :]    # (2, 2, 4)

# Advanced indexing
indices = torch.tensor([0, 2])
y = x[:, indices, :]  # (2, 2, 4)

# Gather (for embedding lookup)
embeddings = torch.randn(100, 768)  # vocab_size, dim
indices = torch.tensor([5, 10, 15])
y = embeddings[indices]  # (3, 768)
```

## Reduction Operations

Reduction operations collapse one or more dimensions into fewer values (a sum, a mean, a max). They are distinct from **dimensionality reduction** (SVD/PCA, covered at the end of this section), which finds a lower-dimensional subspace that preserves most of the variance.

### Sum, Mean, Max, Top-k
```python
x = torch.randn(2, 3, 4)

# Sum
y = x.sum()                    # Scalar
y = x.sum(dim=0)               # (3, 4) - sum over batch
y = x.sum(dim=(1, 2))          # (2,) - sum over H and W

# Mean
y = x.mean()                   # Scalar
y = x.mean(dim=0, keepdim=True)  # (1, 3, 4)

# Max/Min and argmax/argmin
y = x.max(dim=-1)              # Returns (values, indices)
values, indices = x.max(dim=-1)

# Reduction for attention
attn = torch.randn(8, 12, 512, 512)
attn_weights = torch.softmax(attn, dim=-1)  # Normalize over last dim

# Top-k for sampling
logits = torch.randn(8, 50000)  # Batch, vocab size
topk_values, topk_indices = torch.topk(logits, k=10, dim=-1)
```

### SVD and PCA (True Dimensionality Reduction)

Reduction operations shrink tensors to scalars or vectors. Dimensionality reduction instead projects data onto a lower-dimensional subspace while preserving as much variance as possible. The workhorse is the Singular Value Decomposition, and PCA is SVD applied to mean-centered data:

```python
import torch

# Data matrix: (n_samples, n_features)
X = torch.randn(100, 8)
X_centered = X - X.mean(dim=0)

# SVD: X_centered = U @ diag(S) @ Vh
U, S, Vh = torch.linalg.svd(X_centered, full_matrices=False)
components = Vh.T  # (n_features, n_features); column j = j-th principal axis

# Explained variance ratio (PCA eigenvalues = S^2 / (n - 1))
explained = S ** 2 / (X.shape[0] - 1)
explained_ratio = explained / explained.sum()

# Project onto the top-k principal components
k = 2
X_reduced = X_centered @ components[:, :k]  # (n_samples, k)
```

`components[:, :k]` holds the top-k principal directions (orthonormal, ordered by decreasing variance), and `explained_ratio[j]` is the fraction of total variance captured by component j.

## GPU Tensor Operations

### Moving Tensors to GPU
```python
# Check CUDA availability
print(torch.cuda.is_available())  # True if a CUDA GPU is present
print(torch.cuda.device_count())  # Number of GPUs

# Move tensor to GPU
x = torch.randn(3, 4)
x_gpu = x.to('cuda')
x_gpu = x.cuda()

# Create directly on GPU
x = torch.randn(3, 4, device='cuda')

# Specific GPU by index (cuda:0 = first GPU, cuda:1 = second, ...)
x = torch.randn(3, 4, device='cuda:0')

# Move back to CPU
x_cpu = x_gpu.cpu()
```

### Tensor Cores (Ampere to Blackwell)
```yaml
Tensor Cores specialize in matrix multiplication:
- FP16 (half precision) input, FP32 (full precision) accumulation
- Up to 8x faster than CUDA cores for the same workload

Newer generations widen the input formats:
- Hopper (H100): adds FP8 input with FP32 accumulation
- Blackwell (RTX 50 series, B200): adds FP4/FP6 and doubles FP8 throughput

Core operation (matrix multiply-accumulate):
- D = A × B + C  —  (M, K) × (K, N) + (M, N) = (M, N)

Requirements:
- Dimensions must be multiples of 8 (for FP16; 16 for FP8)
- Use torch.amp autocast("cuda") for automatic mixed precision
```

### Mixed Precision Example
```python
import torch
import torch.nn.functional as F
from torch.amp import autocast, GradScaler

model = torch.nn.Linear(768, 10).cuda()
optimizer = torch.optim.Adam(model.parameters())
scaler = GradScaler("cuda")

# (Stand-in for a real DataLoader)
dataloader = [(torch.randn(32, 768), torch.randint(0, 10, (32,))) for _ in range(3)]

for data, target in dataloader:
    data, target = data.cuda(), target.cuda()

    # Automatic mixed precision (torch.cuda.amp is deprecated since PyTorch 2.4)
    with autocast("cuda"):
        output = model(data)
        loss = F.cross_entropy(output, target)

    # Scale gradients to prevent fp16 underflow
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

## Common Patterns in AI

### Linear Layer
```python
def linear(x, W, b):
    """
    x: (batch, in_features)
    W: (out_features, in_features)
    b: (out_features,)
    """
    return torch.einsum('bi,oi->bo', x, W) + b

# Equivalent to:
# return F.linear(x, W, b)
```

### Convolution as einsum
```python
def conv2d_einsum(x, kernel):
    """
    x: (N, C, H, W)
    kernel: (O, C, kH, kW)
    """
    N, C, H, W = x.shape
    O, _, kH, kW = kernel.shape

    # Extract patches
    patches = x.unfold(2, kH, 1).unfold(3, kW, 1)
    # patches: (N, C, H_out, W_out, kH, kW)

    # Convolve (kernel is indexed o,i,j,k for its four dims O,C,kH,kW)
    out = torch.einsum('nihwjk,oijk->nohw', patches, kernel)

    return out
```

### Layer Normalization
```python
def layer_norm(x, gamma, beta, eps=1e-5):
    """
    x: (batch, seq_len, hidden_dim)
    gamma, beta: (hidden_dim,)
    """
    mean = x.mean(dim=-1, keepdim=True)
    var = x.var(dim=-1, keepdim=True, unbiased=False)  # biased variance, matches F.layer_norm

    x_norm = (x - mean) / torch.sqrt(var + eps)
    return gamma * x_norm + beta
```

## Memory Considerations

### Contiguous Memory
```python
x = torch.randn(3, 4)
y = x.t()  # Transpose - NOT contiguous

print(y.is_contiguous())  # False
y_contiguous = y.contiguous()  # Force contiguous copy

# Operations require contiguous memory
# Some ops automatically make contiguous when needed
```

### In-place Operations
```python
x = torch.randn(3, 4)

# In-place (saves memory)
x.add_(5)      # x = x + 5
x.mul_(2)      # x = x * 2

# Non-in-place (creates new tensor)
y = x.add(5)   # Creates new tensor

# Common in-place ops:
# add_, sub_, mul_, div_, pow_, sqrt_, exp_, log_
```

### Memory Footprint
```python
def get_memory_size(tensor):
    """Calculate memory in MB"""
    return tensor.numel() * tensor.element_size() / (1024 ** 2)

# Example for Llama-7B
model_size = 7e9  # 7B parameters
fp16_size = model_size * 2 / (1024 ** 3)  # ~14 GB
int8_size = model_size * 1 / (1024 ** 3)  # ~7 GB
int4_size = model_size * 0.5 / (1024 ** 3)  # ~3.5 GB
```

---

## References

### Related Documents

- [2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md)

### External References

- [torch.einsum — PyTorch documentation](https://docs.pytorch.org/docs/2.14/generated/torch.einsum.html)
- [torch.linalg.svd — PyTorch documentation](https://docs.pytorch.org/docs/2.14/generated/torch.linalg.svd.html)
- [Automatic Mixed Precision (AMP) — PyTorch documentation](https://docs.pytorch.org/docs/2.14/amp.html)

---

## Next Steps

- Continue with: **[2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md)**
- Assessment: **[2100: Calculus - Quiz](./assessment/QUIZ.md)**

---

**Related:**
- [2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md)
- [2201: PyTorch Computational Graphs and Dynamic Execution](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)
- [2203: CUDA Kernel Programming and GPU Architecture](../2200-frameworks/2203-CUDA-Kernel-Programming.md)

**Experiment:** [EXP-2101: Tensor Algebra](../../../../experiments/EXP_2101_TENSOR_ALGEBRA.md)
