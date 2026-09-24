# EXP-2203: CUDA Kernels

**Hands-on GPU Programming with CUDA**

---

## 🎯 Experiment Overview

**Time:** 60-90 minutes
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:**
- 2101-Tensor-Algebra.md
- Basic C/C++ knowledge
- NVIDIA GPU available (recommended)
- Understanding of parallel computing concepts

**Learning Objectives:**
- Write custom CUDA kernels
- Understand GPU memory hierarchy
- Implement parallel reductions
- Optimize memory access patterns
- Compare CPU vs GPU performance

---

## 📚 Background

CUDA (Compute Unified Device Architecture) is NVIDIA's parallel computing platform. It allows developers to harness GPU power for general-purpose computing (GPGPU).

### GPU Architecture Key Concepts:

1. **Threads** - Basic execution units
2. **Blocks** - Groups of threads
3. **Grids** - Groups of blocks
4. **Warp** - 32 threads executing together (NVIDIA)
5. **Memory Hierarchy** - Registers → Shared Memory → Global Memory

---

## 🔬 Experiment 1: First CUDA Kernel (25 minutes)

### Step 1.1: Basic Vector Addition

```python
# File: cuda_basics.py
"""
CUDA Kernel Programming with PyTorch
=====================================
"""

import torch
import time
import numpy as np

def check_cuda():
    """Check CUDA availability"""
    print("=== CUDA Setup ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU Count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            props = torch.cuda.get_device_properties(i)
            print(f"    Memory: {props.total_memory / 1e9:.1f} GB")
            print(f"    Compute Capability: {props.major}.{props.minor}")
            print(f"    Multiprocessors: {props.multi_processor_count}")
            print(f"    Max Threads per Multiprocessor: {props.max_threads_per_multi_processor}")
        return True
    else:
        print("⚠️  CUDA not available. Using CPU.")
        return False

# Setup
has_cuda = check_cuda()
device = torch.device('cuda' if has_cuda else 'cpu')
print(f"\nUsing device: {device}")

# Example 1: Simple CUDA kernel using torch.cuda
def vector_add_cuda(a, b):
    """
    Vector addition using CUDA (via PyTorch)
    Equivalent to: c[i] = a[i] + b[i]
    """
    # Move to GPU if available
    a_gpu = a.to(device)
    b_gpu = b.to(device)

    # Compute on GPU
    c_gpu = a_gpu + b_gpu

    # Move back to CPU
    return c_gpu.cpu()

# Test data
size = 10_000_000
a = torch.randn(size)
b = torch.randn(size)

# CPU version
start = time.time()
c_cpu = a + b
time_cpu = time.time() - start

# GPU version
if has_cuda:
    # Warmup
    _ = vector_add_cuda(a, b)

    start = time.time()
    c_gpu = vector_add_cuda(a, b)
    time_gpu = time.time() - start

    print(f"\n=== Vector Addition Performance ===")
    print(f"Size: {size:,} elements")
    print(f"CPU time: {time_cpu*1000:.3f} ms")
    print(f"GPU time: {time_gpu*1000:.3f} ms")
    print(f"Speedup: {time_cpu/time_gpu:.2f}x")

    # Verify correctness
    assert torch.allclose(c_cpu, c_gpu, rtol=1e-5)
    print("✓ Results match!")
else:
    print("\nGPU not available - skipping GPU comparison")
```

**Checkpoint 1:** ✅ Basic CUDA operations working

---

## 🔬 Experiment 2: Custom CUDA Kernel (35 minutes)

### Step 2.1: Write Custom Kernel

```python
# File: custom_kernel.py
"""
Custom CUDA Kernel Implementation
=================================
"""

import torch
from torch.utils.cpp_extension import setup, CUDAExtension
import os
import subprocess
import tempfile

# First, let's use torch.jit.script for easier custom kernels
def create_custom_kernel():
    """
    Create a custom kernel using torch operations
    that will be compiled efficiently
    """

    # Custom operation: Square each element and sum
    @torch.jit.script
    def custom_square_kernel(x: torch.Tensor) -> torch.Tensor:
        """
        Custom kernel: Square each element
        This will be compiled to efficient GPU code
        """
        return x * x

    # Custom reduction: Sum of squares
    @torch.jit.script
    def sum_of_squares(x: torch.Tensor) -> torch.Tensor:
        """
        Compute sum of squares (like L2 norm squared)
        """
        squared = x * x
        return torch.sum(squared)

    return custom_square_kernel, sum_of_squares

# Test custom kernels
square_kernel, sum_squares_kernel = create_custom_kernel()

# Create test data
if has_cuda:
    data = torch.randn(1000000, device=device)

    # Benchmark custom square kernel
    print("\n=== Custom Kernel Performance ===")

    # Warmup
    for _ in range(10):
        _ = square_kernel(data)

    # Synchronize for accurate timing
    if device.type == 'cuda':
        torch.cuda.synchronize()

    start = time.time()
    for _ in range(100):
        result = square_kernel(data)
    if device.type == 'cuda':
        torch.cuda.synchronize()
    time_custom = time.time() - start

    print(f"Custom square kernel (100 iterations): {time_custom*1000:.3f} ms")
    print(f"Result shape: {result.shape}")
    print(f"Sample values: {result[:5]}")

    # Test sum of squares
    sos = sum_squares_kernel(data)
    print(f"\nSum of squares: {sos.item():.4f}")
    print(f"Expected L2 norm: {torch.norm(data).item():.4f}")
```

### Step 2.2: Matrix Multiplication Kernel

```python
# File: matmul_kernel.py
"""
Matrix Multiplication - Understanding Memory Coalescing
=======================================================
"""

def matmul_performance_test():
    """
    Compare different matrix multiplication approaches
    to understand GPU optimization
    """

    if not has_cuda:
        print("GPU not available - skipping matmul comparison")
        return

    sizes = [256, 512, 1024, 2048, 4096]

    print("\n=== Matrix Multiplication Performance ===")
    print(f"{'Size':>6} | {'CPU (ms)':>10} | {'GPU (ms)':>10} | {'Speedup':>8}")
    print("-" * 50)

    for size in sizes:
        # Create matrices
        A = torch.randn(size, size)
        B = torch.randn(size, size)

        # CPU version
        start = time.time()
        C_cpu = torch.matmul(A, B)
        time_cpu = time.time() - start

        # GPU version
        A_gpu = A.to(device)
        B_gpu = B.to(device)

        # Warmup
        _ = torch.matmul(A_gpu, B_gpu)
        torch.cuda.synchronize()

        start = time.time()
        C_gpu = torch.matmul(A_gpu, B_gpu)
        torch.cuda.synchronize()
        time_gpu = time.time() - start

        speedup = time_cpu / time_gpu

        print(f"{size:>6} | {time_cpu*1000:>10.2f} | {time_gpu*1000:>10.2f} | {speedup:>8.2f}x")

        # Verify
        C_gpu_back = C_gpu.cpu()
        assert torch.allclose(C_cpu, C_gpu_back, rtol=1e-4)

# Run the test
matmul_performance_test()
```

**Checkpoint 2:** ✅ Custom kernels implemented

---

## 🔬 Experiment 3: Parallel Reduction (20 minutes)

### Step 3.1: Implement Reduction Operations

```python
# File: parallel_reduction.py
"""
Parallel Reduction Patterns
===========================
"""

class ParallelReduction:
    """
    Implement various reduction patterns common in GPU computing
    """

    def __init__(self, device='cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')

    def sum_reduction(self, data):
        """Parallel sum reduction"""
        data_gpu = data.to(self.device)
        return torch.sum(data_gpu).cpu()

    def max_reduction(self, data):
        """Parallel max reduction"""
        data_gpu = data.to(self.device)
        return torch.max(data_gpu).cpu()

    def min_reduction(self, data):
        """Parallel min reduction"""
        data_gpu = data.to(self.device)
        return torch.min(data_gpu).cpu()

    def argmax_reduction(self, data):
        """Parallel argmax reduction"""
        data_gpu = data.to(self.device)
        return torch.argmax(data_gpu).cpu()

    def mean_reduction(self, data):
        """Parallel mean reduction"""
        data_gpu = data.to(self.device)
        return torch.mean(data_gpu).cpu()

    def benchmark_reductions(self, size=10_000_000):
        """Benchmark various reduction operations"""
        data = torch.randn(size)

        print(f"\n=== Reduction Performance (n={size:,}) ===")

        operations = [
            ("Sum", self.sum_reduction),
            ("Mean", self.mean_reduction),
            ("Max", self.max_reduction),
            ("Min", self.min_reduction),
            ("ArgMax", self.argmax_reduction),
        ]

        for name, op in operations:
            # Warmup
            for _ in range(10):
                _ = op(data)

            if self.device.type == 'cuda':
                torch.cuda.synchronize()

            start = time.time()
            for _ in range(100):
                result = op(data)
            if self.device.type == 'cuda':
                torch.cuda.synchronize()
            elapsed = time.time() - start

            print(f"{name:>8}: {elapsed*1000:7.3f} ms | Result: {result}")

# Test reductions
if has_cuda:
    reducer = ParallelReduction('cuda')
    reducer.benchmark_reductions()
```

### Step 3.2: Memory Access Patterns

```python
# File: memory_patterns.py
"""
Memory Coalescing and Access Patterns
======================================
"""

def memory_access_analysis():
    """
    Analyze impact of memory access patterns on GPU performance
    """

    if not has_cuda:
        print("GPU not available - skipping memory analysis")
        return

    print("\n=== Memory Access Pattern Analysis ===")

    # Test different access patterns
    size = 10000000

    # Coalesced access (sequential)
    data_sequential = torch.randn(size, device=device)

    start = time.time()
    result_seq = data_sequential * 2  # Simple operation
    torch.cuda.synchronize()
    time_seq = time.time() - start

    # Strided access (non-coalesced)
    data_strided = torch.randn(size, device=device)

    start = time.time()
    result_strided = data_strided[::2] * 2  # Every other element
    torch.cuda.synchronize()
    time_strided = time.time() - start

    print(f"Sequential access: {time_seq*1000:.3f} ms")
    print(f"Strided access:    {time_strided*1000:.3f} ms")
    print(f"Performance ratio: {time_strided/time_seq:.2f}x")

    # Memory bandwidth estimation
    data_size_gb = size * 4 / 1e9  # 4 bytes per float32
    bandwidth = data_size_gb / time_seq
    print(f"\nEstimated memory bandwidth: {bandwidth:.1f} GB/s")

memory_access_analysis()
```

**Checkpoint 3:** ✅ Parallel reductions working

---

## 🔬 Experiment 4: Real-World Application (20 minutes)

### Step 4.1: K-Means Clustering on GPU

```python
# File: gpu_kmeans.py
"""
GPU-Accelerated K-Means Clustering
===================================
"""

class GPUKMeans:
    """
    K-Means clustering using GPU acceleration
    """

    def __init__(self, n_clusters=5, max_iter=100, device='cuda'):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.centroids = None

    def fit(self, X):
        """
        Fit K-Means to data X

        Args:
            X: (n_samples, n_features) data tensor
        """
        # Move to GPU
        X_gpu = X.to(self.device)

        # Initialize centroids randomly
        indices = torch.randperm(X_gpu.shape[0])[:self.n_clusters]
        self.centroids = X_gpu[indices].clone()

        for iteration in range(self.max_iter):
            # Compute distances: (n_samples, n_clusters)
            # Using broadcasting for efficiency
            distances = torch.cdist(X_gpu, self.centroids)

            # Assign to nearest centroid
            labels = torch.argmin(distances, dim=1)

            # Update centroids
            new_centroids = torch.zeros_like(self.centroids)
            for k in range(self.n_clusters):
                mask = labels == k
                if mask.sum() > 0:
                    new_centroids[k] = X_gpu[mask].mean(dim=0)

            # Check convergence
            if torch.allclose(self.centroids, new_centroids, rtol=1e-4):
                print(f"Converged at iteration {iteration}")
                break

            self.centroids = new_centroids

        return labels.cpu()

    def predict(self, X):
        """Predict cluster labels for new data"""
        X_gpu = X.to(self.device)
        distances = torch.cdist(X_gpu, self.centroids)
        return torch.argmin(distances, dim=1).cpu()

# Test GPU K-Means
if has_cuda:
    print("\n=== GPU K-Means Clustering ===")

    # Generate synthetic data
    n_samples = 100000
    n_features = 10
    n_clusters = 5

    X = torch.randn(n_samples, n_features)

    # Fit on GPU
    kmeans = GPUKMeans(n_clusters=n_clusters, max_iter=50)

    start = time.time()
    labels = kmeans.fit(X)
    if device.type == 'cuda':
        torch.cuda.synchronize()
    time_gpu = time.time() - start

    print(f"GPU K-Means: {time_gpu*1000:.2f} ms")
    print(f"Cluster distribution: {torch.bincount(labels)}")
```

**Checkpoint 4:** ✅ Real-world GPU application working

---

## 📊 Performance Analysis

### Expected Speedups

| Operation | GPU Speedup |
|-----------|-------------|
| Vector operations | 10-100x (large arrays) |
| Matrix multiplication | 5-50x (depends on size) |
| Reductions | 20-200x |
| K-Means | 10-50x |

### Optimization Tips

1. **Memory Coalescing** - Access memory sequentially
2. **Minimize Data Transfer** - Keep data on GPU
3. **Use Shared Memory** - For frequently accessed data
4. **Avoid Divergence** - Keep threads in lockstep
5. **Batch Operations** - Process multiple items together

---

## ✅ Experiment Checklist

- [ ] CUDA availability confirmed
- [ ] Basic vector addition implemented
- [ ] Custom kernels created
- [ ] Matrix multiplication benchmarked
- [ ] Parallel reductions working
- [ ] Memory patterns analyzed
- [ ] Real-world application (K-Means) working
- [ ] Performance results recorded

---

## 🎓 Key Takeaways

1. **GPU = Massive Parallelism** - Thousands of threads vs CPU's few
2. **Memory Bandwidth is Key** - GPU has much higher bandwidth than CPU
3. **Data Transfer Overhead** - Minimize CPU-GPU transfers
4. **Coalesced Access** - Sequential memory access is critical
5. **PyTorch Handles Most** - Often don't need raw CUDA for common ops

---

## 🚀 Next Steps

1. **2203-CUDA-Kernel-Syb-Level.md**: Deep CUDA theory
2. **LAB-006: Train Model from Scratch** - Apply GPU optimization
3. **2402-Large-Scale-Training.md** - Distributed GPU training

---

**Last Updated:** 2026-02-04
**Experiment:** 2203 - CUDA Kernels
**Time Estimate:** 60-90 minutes
**Difficulty:** ⭐⭐⭐ Advanced
