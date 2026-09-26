---
Document ID: TUTORIAL-008
Title: "TUTORIAL-008: CUDA Programming for AI"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
---

# TUTORIAL-008: CUDA Programming for AI

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: GPU Architecture](#part-1-gpu-architecture)
- [Part 2: Writing CUDA Kernels with Numba](#part-2-writing-cuda-kernels-with-numba)
- [Part 3: Matrix Multiplication](#part-3-matrix-multiplication)
- [Part 4: Memory Coalescing](#part-4-memory-coalescing)
- [Part 5: Profiling and Optimization](#part-5-profiling-and-optimization)
- [Part 6: Common CUDA Patterns](#part-6-common-cuda-patterns)
- [Exercises](#exercises)
- [References](#references)
- [Next Steps](#next-steps)

---

## Abstract

This tutorial teaches you how to write custom CUDA kernels to accelerate AI workloads on NVIDIA GPUs.

**Duration:** 4 hours
**Difficulty:** Advanced
**Prerequisites:** TUTORIAL-001, Python proficiency

---

## Learning Objectives

After this tutorial, you will:
- Understand GPU architecture and memory model
- Write custom CUDA kernels with Python (Numba/CuPy)
- Optimize memory access patterns
- Profile and benchmark GPU code

---

## Part 1: GPU Architecture

### Understanding the GPU

```text
GPU (NVIDIA 11GB-class GPU):
├── 4352 CUDA cores
├── 11GB GDDR6 memory
├── Memory bandwidth: 616 GB/s
└── Compute Capability: 7.5

Execution Model:
├── Grid: Collection of blocks
├── Block: Group of threads (typically 32-1024)
└── Thread: Individual execution unit

Memory Hierarchy:
├── Global Memory: 11GB (slow, shared by all)
├── Shared Memory: ~48KB per block (fast, shared by block)
├── Registers: Per-thread (fastest)
└── Constant/Texture Memory: Read-only, cached
```

### Thread Organization

```python
# Grid and block dimensions
grid_dim = (2, 2)    # 2x2 = 4 blocks
block_dim = (16, 16)  # 16x16 = 256 threads per block

# Total threads = 4 blocks × 256 threads = 1024 threads
```

---

## Part 2: Writing CUDA Kernels with Numba

### Installation

```bash
pip install numba
```

Numba's CUDA target additionally needs an NVIDIA GPU with a recent driver — it loads the CUDA runtime itself, so a full CUDA Toolkit install is not required.

### Your First Kernel

```python
from numba import cuda
import numpy as np

@cuda.jit
def add_kernel(x, y, out):
    """Add two arrays element-wise on GPU"""
    # Get thread position
    tx = cuda.threadIdx.x
    bx = cuda.blockIdx.x
    bw = cuda.blockDim.x

    # Compute global index
    i = bx * bw + tx

    # Boundary check
    if i < out.size:
        out[i] = x[i] + y[i]

def main():
    # Allocate data
    n = 1000000
    x = np.random.randn(n).astype(np.float32)
    y = np.random.randn(n).astype(np.float32)
    out = np.zeros_like(x)

    # Copy to GPU
    d_x = cuda.to_device(x)
    d_y = cuda.to_device(y)
    d_out = cuda.to_device(out)

    # Configure launch
    threads_per_block = 256
    blocks_per_grid = (n + threads_per_block - 1) // threads_per_block

    # Launch kernel
    add_kernel[blocks_per_grid, threads_per_block](d_x, d_y, d_out)

    # Copy back
    result = d_out.copy_to_host()

    print(f"First 5 results: {result[:5]}")
    print(f"GPU result matches CPU: {np.allclose(result, x + y)}")

if __name__ == "__main__":
    main()

# Expected Output:
# First 5 results: [-0.NN, -0.NN, ...]   (random inputs, so values vary)
# GPU result matches CPU: True
```

---

## Part 3: Matrix Multiplication

### Naive Implementation

```python
@cuda.jit
def matmul_naive(A, B, C):
    """Naive matrix multiplication"""
    row = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    col = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x

    if row < C.shape[0] and col < C.shape[1]:
        tmp = 0.0
        for k in range(A.shape[1]):
            tmp += A[row, k] * B[k, col]
        C[row, col] = tmp

def benchmark_matmul(size=1024):
    A = np.random.randn(size, size).astype(np.float32)
    B = np.random.randn(size, size).astype(np.float32)
    C = np.zeros((size, size), dtype=np.float32)

    # GPU timing
    import time

    d_A = cuda.to_device(A)
    d_B = cuda.to_device(B)
    d_C = cuda.to_device(C)

    threads_per_block = (16, 16)
    blocks_per_grid = (
        (size + threads_per_block[0] - 1) // threads_per_block[0],
        (size + threads_per_block[1] - 1) // threads_per_block[1]
    )

    start = time.time()
    matmul_naive[blocks_per_grid, threads_per_block](d_A, d_B, d_C)
    cuda.synchronize()
    gpu_time = time.time() - start

    # CPU timing
    start = time.time()
    C_cpu = A @ B
    cpu_time = time.time() - start

    print(f"GPU time: {gpu_time:.4f}s")
    print(f"CPU time: {cpu_time:.4f}s")
    print(f"Speedup: {cpu_time/gpu_time:.2f}x")

# Expected Output:
# GPU time: <N>.NNNNs
# CPU time: <N>.NNNNs
# Speedup: <N>.NNx
# (times are hardware-dependent. At 1024x1024 the naive GPU kernel
#  often LOSES to the CPU: NumPy's `@` dispatches to a highly tuned
#  BLAS, while the kernel above does one global-memory load per FMA.
#  That gap is exactly what shared-memory tiling below closes.)
```

### Shared Memory Optimization

```python
# Shared memory shapes must be compile-time constants - a kernel
# argument cannot size cuda.shared.array. Module-level globals are
# frozen into the compiled kernel, so TILE_SIZE lives here.
TILE_SIZE = 16

@cuda.jit
def matmul_shared(A, B, C):
    """Matrix multiplication with shared memory tiling

    Launch with (TILE_SIZE, TILE_SIZE) threads per block - the tiling
    assumes blockDim == (TILE_SIZE, TILE_SIZE).
    """
    row = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    col = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y

    # Allocate shared memory
    tile_A = cuda.shared.array((TILE_SIZE, TILE_SIZE), dtype=np.float32)
    tile_B = cuda.shared.array((TILE_SIZE, TILE_SIZE), dtype=np.float32)

    tmp = 0.0

    # Loop over tiles
    for i in range(0, A.shape[1], TILE_SIZE):
        # Load tiles into shared memory
        if row < A.shape[0] and tx + i < A.shape[1]:
            tile_A[ty, tx] = A[row, tx + i]
        else:
            tile_A[ty, tx] = 0.0

        if ty + i < B.shape[0] and col < B.shape[1]:
            tile_B[ty, tx] = B[ty + i, col]
        else:
            tile_B[ty, tx] = 0.0

        # Synchronize to ensure tile is loaded
        cuda.syncthreads()

        # Compute partial dot product
        for k in range(TILE_SIZE):
            tmp += tile_A[ty, k] * tile_B[k, tx]

        # Synchronize before loading next tile
        cuda.syncthreads()

    if row < C.shape[0] and col < C.shape[1]:
        C[row, col] = tmp
```

---

## Part 4: Memory Coalescing

### Optimal Memory Access

```python
@cuda.jit
def good_memory_access(array):
    """Coalesced memory access - fast"""
    i = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    if i < array.size:
        # Adjacent threads access adjacent memory
        array[i] = array[i] * 2

@cuda.jit
def bad_memory_access(array):
    """Strided memory access - slow"""
    i = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    if i < array.size:
        # Threads access memory with large stride
        stride = 32
        if i * stride < array.size:
            array[i * stride] = array[i * stride] * 2
```

---

## Part 5: Profiling and Optimization

### Benchmarking Effective Bandwidth

```python
# add_kernel comes from Part 2's "Your First Kernel" block; cuda and
# np are imported there too (this tutorial's blocks run top-down).

def profile_kernel():
    # Create test data
    n = 10_000_000
    x = np.random.randn(n).astype(np.float32)
    y = np.random.randn(n).astype(np.float32)
    out = np.zeros_like(x)

    # Move to GPU
    d_x = cuda.to_device(x)
    d_y = cuda.to_device(y)
    d_out = cuda.to_device(out)

    # Get GPU info
    device = cuda.get_current_device()
    print(f"GPU: {device.name.decode()}")
    print(f"Compute Capability: {device.compute_capability}")
    print(f"Total Memory: {device.total_memory / 1e9:.2f} GB")

    # Measure performance
    threads_per_block = 256
    # Cover ALL n elements - a fixed 640-block grid would launch only
    # 163,840 threads, and the kernel's boundary check would silently
    # skip the other ~98% of the array while the prints below still
    # reported numbers as if it had been fully processed
    blocks_per_grid = (n + threads_per_block - 1) // threads_per_block

    # Warmup
    for _ in range(5):
        add_kernel[blocks_per_grid, threads_per_block](d_x, d_y, d_out)

    # Timed run
    import time
    start = time.time()
    for _ in range(100):
        add_kernel[blocks_per_grid, threads_per_block](d_x, d_y, d_out)
    cuda.synchronize()
    elapsed = time.time() - start

    elements = n * 100
    bandwidth = (elements * 4 * 3) / (elapsed * 1e9)  # 3 reads/writes, 4 bytes each

    print(f"Processed {elements/1e9:.2f}B elements")
    print(f"Time: {elapsed:.4f}s")
    print(f"Throughput: {elements/elapsed/1e6:.2f}M elements/sec")
    print(f"Effective bandwidth: {bandwidth:.2f} GB/s")

# Expected Output:
# GPU: <GPU name from device.name>
# Compute Capability: (<major>, <minor>)
# Total Memory: <N>.NN GB
# Processed 1.00B elements
# Time: <N>.NNNNs
# Throughput: <N>NNNN.NN M elements/sec
# Effective bandwidth: <N>.NN GB/s
# (each element adds two float32 reads and one write = 12 bytes, so
#  bandwidth = elements * 12 / time; expect a fraction of the peak
#  616 GB/s - the small kernel is launch-latency bound at this size)
```

---

## Part 6: Common CUDA Patterns

### Parallel Reduction

```python
# cuda.shared.array needs a compile-time constant shape, and
# cuda.blockDim.x is only known at runtime - size the buffer with a
# module-level constant and launch with exactly this many threads
# per block.
BLOCK_SIZE = 256

@cuda.jit
def sum_reduction(array, result):
    """Compute sum using parallel reduction

    Launch with BLOCK_SIZE threads per block; each block reduces
    2 * BLOCK_SIZE elements, and `result` receives one partial sum
    per block (sum `result` on the host to get the total).
    """
    tid = cuda.threadIdx.x
    i = cuda.blockIdx.x * cuda.blockDim.x * 2 + tid

    # Load two elements
    partial_sum = 0.0
    if i < array.size:
        partial_sum += array[i]
    if i + cuda.blockDim.x < array.size:
        partial_sum += array[i + cuda.blockDim.x]

    # Shared memory for block-level reduction
    s_data = cuda.shared.array(BLOCK_SIZE, dtype=np.float32)
    s_data[tid] = partial_sum
    cuda.syncthreads()

    # Reduction in shared memory
    stride = cuda.blockDim.x // 2
    while stride > 0:
        if tid < stride:
            s_data[tid] += s_data[tid + stride]
        cuda.syncthreads()
        stride //= 2

    # Write block result
    if tid == 0:
        result[cuda.blockIdx.x] = s_data[0]
```

---

## Exercises

1. **Vector Operations**: Implement vector addition, subtraction, and element-wise multiplication
2. **Convolution**: Write a 2D convolution kernel for image processing
3. **Softmax**: Implement softmax for neural network activation
4. **Matrix Transpose**: Optimize matrix transpose with shared memory

---

## Completion Checklist

- [ ] First CUDA kernel written and tested
- [ ] Matrix multiplication implemented
- [ ] Shared memory optimization applied
- [ ] Memory coalescing understood
- [ ] Profiling performed
- [ ] Performance benchmarked

---

## References

### Related ai-engineering-curriculum Documents

- [2203: CUDA Kernel Programming and GPU Architecture](../../phases/phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Programming.md)
- [LAB-006: Train Model From Scratch](../labs/LAB-006-Train-Model-From-Scratch.md)

---

## Next Steps

- Hands-on: **[2203: CUDA Kernel Programming and GPU Architecture](../../phases/phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Programming.md)**
- Practice: **[LAB-006: Train Model From Scratch](../labs/LAB-006-Train-Model-From-Scratch.md)**
