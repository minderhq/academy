---
Document ID: 2101
Title: Tensor Algebra and Linear Algebra for AI
Phase: 2
Module: 2100
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['math', 'calculus', 'tensors', 'backpropagation']
---

# 2101: Tensor Algebra and Linear Algebra for AI

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
print(x numel())    # 2 * 3 * 4 * 5 = 120

# Common shapes for AI:
Image batch:    (B, C, H, W) = (32, 3, 224, 224)
Sequence:       (B, L, D) = (8, 512, 768)
Attention:      (B, H, L, L) = (8, 12, 512, 512)
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
A = torch.randn(3, 1)  # [[1], [2], [3]]
B = torch.randn(1, 4)  # [[1, 2, 3, 4]]
C = A + B              # [[2, 3, 4, 5], [3, 4, 5, 6], [4, 5, 6, 7]]

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

# Sum over dimensions
A = torch.randn(3, 4, 5)
B = torch.einsum('ijk->ij', A, sum over k)  # (3, 4)
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

## Dimensionality Reduction

### Reduction Operations
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

## GPU Tensor Operations

### Moving Tensors to GPU
```python
# Check CUDA availability
print(torch.cuda.is_available())  # True
print(torch.cuda.device_count())  # Number of GPUs

# Move tensor to GPU
x = torch.randn(3, 4)
x_gpu = x.to('cuda')
x_gpu = x.cuda()

# Create directly on GPU
x = torch.randn(3, 4, device='cuda')

# Specific GPU (11GB-class GPU)
x = torch.randn(3, 4, device='cuda:0')

# Move back to CPU
x_cpu = x_gpu.cpu()
```

### Tensor Cores (11GB-class GPU)
```yaml
Tensor Cores specialize in matrix multiplication:
- FP16 (half precision) input
- FP32 (full precision) accumulation
- Up to 8x faster than CUDA cores

Supported operations:
- FMA: a × b + c
- Matrix multiply: (M, K) × (K, N) = (M, N)

Requirements:
- Dimensions must be multiples of 8 (for FP16)
- Use amp.autocast() for automatic mixed precision
```

### Mixed Precision Example
```python
import torch
from torch.cuda.amp import autocast, GradScaler

model = MyModel().cuda()
optimizer = torch.optim.Adam(model.parameters())
scaler = GradScaler()

for data, target in dataloader:
    data, target = data.cuda(), target.cuda()

    # Automatic mixed precision
    with autocast():
        output = model(data)
        loss = F.cross_entropy(output, target)

    # Scale gradients to prevent underflow
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

    # Convolve
    out = torch.einsum('nihwjk,ojk->nohw', patches, kernel)

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
    var = x.var(dim=-1, keepdim=True)

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

## Next Steps

- Continue with: **[2102: Backpropagation](./2102-Backpropagation-and-Derivatives.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [2102: Backpropagation](./2102-Backpropagation-and-Derivatives.md)
- [2201: PyTorch Graphs](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)
- [2203: CUDA Kernels](../2200-frameworks/2203-CUDA-Kernel-Syb-Level.md)

**Experiment Template:** `experiments/EXP_2101_TENSOR_ALGEBRA.md`
