---
Document ID: EXP_2101
Title: "EXP-2101: Tensor Algebra"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Intermediate
---

# EXP-2101: Tensor Algebra

**Hands-on tensor operations and einsum notation**

---

## 🎯 Experiment Overview

**Time:** 45-60 minutes
**Difficulty:** ⭐⭐ Intermediate
**Prerequisites:**
- Basic Python knowledge
- Understanding of linear algebra basics
- NumPy familiarity helpful

**Learning Objectives:**
- Master tensor operations and broadcasting
- Understand einsum notation
- Implement tensor contractions
- Optimize tensor computations

---

## 📚 Background

Tensors are multi-dimensional arrays that generalize scalars, vectors, and matrices. Understanding tensor operations is fundamental to deep learning.

### Tensor Ranks
- **Rank 0**: Scalar (single number)
- **Rank 1**: Vector (1D array)
- **Rank 2**: Matrix (2D array)
- **Rank 3+**: Tensor (3D and higher)

---

## 🔬 Experiment 1: Tensor Basics (20 minutes)

### Step 1.1: Tensor Creation and Operations

```python
# File: tensor_basics.py
"""
Tensor Operations with NumPy
=============================
"""

import numpy as np

# Create tensors of different ranks
scalar = np.array(5)                    # Rank 0
vector = np.array([1, 2, 3, 4])         # Rank 1
matrix = np.array([[1, 2], [3, 4]])    # Rank 2
tensor3d = np.array([[[1, 2], [3, 4]],
                     [[5, 6], [7, 8]]]) # Rank 3

print("Scalar:", scalar)
print("Vector:", vector)
print("Matrix:\n", matrix)
print("3D Tensor:\n", tensor3d)

# Tensor properties
print(f"\nMatrix shape: {matrix.shape}")
print(f"Matrix ndim: {matrix.ndim}")
print(f"Matrix dtype: {matrix.dtype}")
print(f"Matrix size: {matrix.size}")

# Basic operations
a = np.array([[1, 2], [3, 4]])
b = np.array([[5, 6], [7, 8]])

print(f"\nAddition:\n{a + b}")
print(f"Multiplication (element-wise):\n{a * b}")
print(f"Matrix multiplication:\n{a @ b}")
print(f"Transpose:\n{a.T}")

# Broadcasting
x = np.array([[1, 2, 3], [4, 5, 6]])  # (2, 3)
y = np.array([10, 20, 30])             # (3,)

print(f"\nBroadcasting (2,3) + (3,):\n{x + y}")

# Reduction operations
print(f"\nSum: {x.sum()}")
print(f"Sum along axis 0: {x.sum(axis=0)}")
print(f"Sum along axis 1: {x.sum(axis=1)}")
print(f"Mean: {x.mean()}")
```

**Checkpoint 1:** ✅ Tensor basics understood

---

## 🔬 Experiment 2: Einsum Notation (20 minutes)

### Step 2.1: Mastering Einsum

```python
# File: einsum_tutorial.py
"""
Einstein Summation (Einsum) Notation
====================================
"""

import numpy as np

# Basic einsum operations
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# Matrix multiplication: ij,jk->ik
result = np.einsum('ij,jk->ik', A, B)
print("Matrix multiplication (einsum):\n", result)
print("Verify (A @ B):\n", A @ B)

# Element-wise multiplication: ij,ij->ij
result = np.einsum('ij,ij->ij', A, B)
print("\nElement-wise multiplication:\n", result)
print("Verify (A * B):\n", A * B)

# Trace (sum of diagonal): ii->
result = np.einsum('ii->', A)
print(f"\nTrace: {result}")
print(f"Verify (np.trace): {np.trace(A)}")

# Transpose: ij->ji
result = np.einsum('ij->ji', A)
print(f"\nTranspose:\n{result}")

# Batch matrix multiplication
A_batch = np.random.randn(10, 3, 4)  # 10 matrices of (3, 4)
B_batch = np.random.randn(10, 4, 5)  # 10 matrices of (4, 5)

# bij,bjk->bik (batch matrix multiplication)
result = np.einsum('bij,bjk->bik', A_batch, B_batch)
print(f"\nBatch matmul result shape: {result.shape}")

# Diagonal extraction
C = np.random.randn(4, 4)
diag = np.einsum('ii->i', C)
print(f"\nDiagonal: {diag}")

# Outer product
u = np.array([1, 2, 3])
v = np.array([4, 5, 6])
outer = np.einsum('i,j->ij', u, v)
print(f"\nOuter product:\n{outer}")
```

### Step 2.2: Advanced Einsum

```python
# File: advanced_einsum.py
"""
Advanced Einsum Patterns
========================
"""

import numpy as np

# Tensor contraction
# Contract along shared indices
A = np.random.randn(3, 4, 5)
B = np.random.randn(5, 6)

# ijk,kl->ijl (contract k)
result = np.einsum('ijk,kl->ijl', A, B)
print(f"Contraction result shape: {result.shape}")

# Multiple contractions
A = np.random.randn(2, 3, 4)
B = np.random.randn(4, 5)
C = np.random.randn(5, 6)

# ijk,kl,lm->ijm
result = np.einsum('ijk,kl,lm->ijm', A, B, C)
print(f"Multiple contraction shape: {result.shape}")

# Permutation
A = np.random.randn(2, 3, 4)
B = np.einsum('ijk->kji', A)  # Reverse dimensions
print(f"\nPermutation {A.shape} -> {B.shape}")

# Summation with broadcasting
A = np.random.randn(3, 4)
v = np.random.randn(4)

# ij,j->i (matrix-vector product)
result = np.einsum('ij,j->i', A, v)
print(f"\nMatrix-vector: {result.shape}")

# Complex operation: Batched attention
# Q, K, V: (batch, heads, seq_len, dim)
batch, heads, seq_len, dim = 2, 3, 5, 4

Q = np.random.randn(batch, heads, seq_len, dim)
K = np.random.randn(batch, heads, seq_len, dim)
V = np.random.randn(batch, heads, seq_len, dim)

# bhqd,bhkd->bhqk (attention scores)
scores = np.einsum('bhqd,bhkd->bhqk', Q, K) / np.sqrt(dim)
print(f"\nAttention scores shape: {scores.shape}")

# bhqk,bhkd->bhqd (attention output)
output = np.einsum('bhqk,bhkd->bhqd', scores, V)
print(f"Attention output shape: {output.shape}")
```

**Checkpoint 2:** ✅ Einsum notation mastered

---

## 🔬 Experiment 3: Tensor Contraction (15 minutes)

### Step 3.1: Optimize Tensor Operations

```python
# File: tensor_contraction.py
"""
Efficient Tensor Contractions
==============================
"""

import numpy as np
import time

# Large tensors for benchmarking
A = np.random.randn(100, 200, 300)
B = np.random.randn(300, 150)

# Method 1: Naive loops
def naive_contraction(A, B):
    """Slow manual contraction"""
    result = np.zeros((100, 200, 150))
    for i in range(100):
        for j in range(200):
            for k in range(150):
                for l in range(300):
                    result[i, j, k] += A[i, j, l] * B[l, k]
    return result

# Method 2: Einsum
def einsum_contraction(A, B):
    """Fast einsum contraction"""
    return np.einsum('ijl,lk->ijk', A, B)

# Benchmark
start = time.time()
# result_naive = naive_contraction(A, B)  # Too slow!
# time_naive = time.time() - start

start = time.time()
result_einsum = einsum_contraction(A, B)
time_einsum = time.time() - start

# print(f"Naive: {time_naive:.3f}s")
print(f"Einsum: {time_einsum:.3f}s")
print(f"Result shape: {result_einsum.shape}")

# Memory-efficient operations
# Chaining operations to minimize intermediate tensors
A = np.random.randn(1000, 500)
B = np.random.randn(500, 1000)
C = np.random.randn(1000, 200)

# Efficient: (A @ B) @ C
# Less efficient: A @ (B @ C) if shapes don't align well
result = np.einsum('ij,jk,kl->il', A, B, C)
print(f"\nChained operation shape: {result.shape}")
```

**Checkpoint 3:** ✅ Tensor contractions working

---

## 🔬 Experiment 4: Real-World Applications (15 minutes)

### Step 4.1: Neural Network Operations

```python
# File: nn_tensors.py
"""
Tensor Operations in Neural Networks
====================================
"""

import numpy as np

# Linear layer: y = xW + b
batch_size, input_dim, output_dim = 32, 128, 64

x = np.random.randn(batch_size, input_dim)
W = np.random.randn(input_dim, output_dim) * 0.01
b = np.zeros(output_dim)

# Forward pass: ij,jk->ik
y = np.einsum('ij,jk->ik', x, W) + b
print(f"Linear layer output: {y.shape}")

# Batch normalization
gamma = np.ones(output_dim)
beta = np.zeros(output_dim)

# Compute mean and variance
mean = np.mean(y, axis=0)
var = np.var(y, axis=0)

# Normalize: i->, i->
y_norm = (y - mean) / np.sqrt(var + 1e-5)

# Scale and shift: i,i,i->i
y_out = gamma * y_norm + beta
print(f"Batch norm output: {y_out.shape}")

# Convolution as tensor operation
batch, in_ch, h, w = 2, 3, 5, 5
out_ch, kernel_size = 4, 3

input_tensor = np.random.randn(batch, in_ch, h, w)
kernel = np.random.randn(out_ch, in_ch, kernel_size, kernel_size)

# Manual convolution using einsum (simplified)
output = np.zeros((batch, out_ch, h - kernel_size + 1, w - kernel_size + 1))

for b in range(batch):
    for oc in range(out_ch):
        for ic in range(in_ch):
            for i in range(h - kernel_size + 1):
                for j in range(w - kernel_size + 1):
                    patch = input_tensor[b, ic, i:i+kernel_size, j:j+kernel_size]
                    output[b, oc, i, j] += np.sum(patch * kernel[oc, ic])

print(f"\nConvolution output: {output.shape}")
```

### Step 4.2: Gradient Computation

```python
# File: tensor_gradients.py
"""
Tensor Gradients
================
"""

import numpy as np

# Computational graph for gradients
class Tensor:
    """Simple tensor with gradient tracking"""

    def __init__(self, data, requires_grad=False):
        self.data = np.array(data)
        self.requires_grad = requires_grad
        self.grad = None
        self._backward = lambda: None
        self._prev = []

    def __matmul__(self, other):
        """Matrix multiplication"""
        result = Tensor(self.data @ other.data)
        result._prev = [self, other]

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = Tensor(np.zeros_like(self.data))
                self.grad.data += result.grad.data @ other.data.T
            if other.requires_grad:
                if other.grad is None:
                    other.grad = Tensor(np.zeros_like(other.data))
                other.grad.data += self.data.T @ result.grad.data

        result._backward = _backward
        result.requires_grad = self.requires_grad or other.requires_grad
        return result

    def __add__(self, other):
        """Addition"""
        result = Tensor(self.data + other.data)
        result._prev = [self, other]

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = Tensor(np.zeros_like(self.data))
                self.grad.data += result.grad.data
            if other.requires_grad:
                if other.grad is None:
                    other.grad = Tensor(np.zeros_like(other.data))
                other.grad.data += result.grad.data

        result._backward = _backward
        result.requires_grad = self.requires_grad or other.requires_grad
        return result

    def sum(self):
        """Sum all elements"""
        result = Tensor(np.array(self.data.sum()))
        result._prev = [self]

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = Tensor(np.ones_like(self.data))
                else:
                    self.grad.data += result.grad.data

        result._backward = _backward
        result.requires_grad = self.requires_grad
        return result

    def backward(self):
        """Compute gradients"""
        if not self.requires_grad:
            raise RuntimeError("Called backward on non-requires_grad tensor")

        # Build topological order
        topo = []
        visited = set()

        def build_topo(node):
            if node not in visited:
                visited.add(node)
                for child in node._prev:
                    build_topo(child)
                topo.append(node)

        build_topo(self)

        # Initialize gradient
        self.grad = Tensor(np.ones_like(self.data))

        # Backpropagate
        for node in reversed(topo):
            node._backward()

# Test gradients
x = Tensor([[1, 2], [3, 4]], requires_grad=True)
W = Tensor([[5, 6], [7, 8]], requires_grad=True)

y = x @ W
loss = y.sum()

loss.backward()

print(f"x.grad:\n{x.grad.data}")
print(f"W.grad:\n{W.grad.data}")

# Verify with finite differences
def numerical_grad(f, x, eps=1e-5):
    """Compute numerical gradient"""
    grad = np.zeros_like(x.data)
    it = np.nditer(x.data, flags=['multi_index'])

    for _ in it:
        idx = it.multi_index
        orig = x.data[idx]

        x.data[idx] = orig + eps
        f_plus = f(x).data

        x.data[idx] = orig - eps
        f_minus = f(x).data

        x.data[idx] = orig
        grad[idx] = (f_plus - f_minus) / (2 * eps)

    return grad

x_test = Tensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
W_test = Tensor([[5.0, 6.0], [7.0, 8.0]], requires_grad=False)

def f(x):
    return (x @ W_test).sum()

# Compute gradients both ways for the same function
f(x_test).backward()
num_grad = numerical_grad(f, x_test)
print(f"\nNumerical gradient:\n{num_grad}")
print(f"Analytical gradient:\n{x_test.grad.data}")
print(f"Difference: {np.abs(num_grad - x_test.grad.data).max()}")
```

**Checkpoint 4:** ✅ Real-world applications working

---

## 📊 Performance Comparison

### Einsum vs Traditional Operations

| Operation | Einsum | Traditional | Speedup |
|-----------|--------|------------|---------|
| Matrix multiplication | Similar | Similar | ~1x |
| Complex contractions | Faster | Slower | 2-10x |
| Batch operations | Much faster | Slow loops | 10-100x |
| Memory usage | Optimized | May create intermediates | Varies |

### Best Practices

1. **Use einsum for complex operations** - More readable and often faster
2. **Avoid unnecessary copies** - Use in-place operations when possible
3. **Consider memory layout** - Row-major (C) vs column-major (F)
4. **Profile before optimizing** - Measure actual bottlenecks

---

## ✅ Experiment Checklist

- [ ] Tensor creation and basic operations
- [ ] Broadcasting understood
- [ ] Einsum notation mastered
- [ ] Tensor contractions working
- [ ] Gradient computation verified
- [ ] Real-world applications tested

---

## 🎓 Key Takeaways

1. **Tensors = Multi-dimensional Arrays** - Generalize scalars, vectors, matrices
2. **Einsum is Powerful** - Concise notation for complex tensor operations
3. **Broadcasting Matters** - Understanding shapes prevents bugs
4. **Efficiency Counts** - Right operation order saves memory and time
5. **Gradients Flow** - Chain rule applies to tensors

---

## 🚀 Next Steps

1. **EXP_2102**: Backpropagation - Gradients in neural networks
2. **EXP_2201**: PyTorch Computational Graphs - Automatic differentiation
3. **LAB-006**: Train Model from Scratch - Apply tensor operations

---

**Last Updated:** 2026-10-01
**Experiment:** 2101 - Tensor Algebra
**Time Estimate:** 45-60 minutes
**Difficulty:** ⭐⭐ Intermediate
