---
Document ID: 2203
Title: CUDA Kernel Programming and GPU Architecture
Phase: 2
Module: 2200
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'pytorch', 'tensorflow', 'cuda']
---

# 2203: CUDA Kernel Programming and GPU Architecture

## Abstract
CUDA (Compute Unified Device Architecture) is NVIDIA's parallel computing platform. Understanding CUDA kernel programming is essential for writing optimized deep learning code that leverages the RTX 2080 Ti's 4352 CUDA cores.

## GPU Architecture Overview

### RTX 2080 Ti Specifications
```
CUDA Architecture:   Turing TU102
CUDA Cores:         4352 (FP32)
Tensor Cores:       544 (for mixed precision)
VRAM:               11GB GDDR6
Memory Bandwidth:   616 GB/s
Base Clock:         1350 MHz
Boost Clock:        1545 MHz
TDP:                250W
L2 Cache:           5.5 MB
```

### Hardware Organization
```
┌─────────────────────────────────────────────────────────┐
│                     GPU (TU102)                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  GPC 0     │  │  GPC 1     │  │  GPC ...   │  GPCs   │
│  │  (6 SMs)   │  │  (6 SMs)   │  │            │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  Each GPC (Graphics Processing Cluster):                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  SM 0  │  SM 1  │  SM 2  │  SM 3  │  SM 4  │ SM5│   │
│  │ 64 FP32│ 64 FP32│ 64 FP32│ 64 FP32│ 64 FP32│...│   │
│  │ 8 Tensor│ 8 Tensor│ ... │                            │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  Memory Controller → GDDR6 (11GB @ 14 Gbps)             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### SM (Streaming Multiprocessor)
```
Each SM contains:
- 64 CUDA cores (FP32 units)
- 8 Tensor cores (for mixed precision)
- 4 texture units
- 1 register file (64K × 32-bit)
- Shared memory (varies, ~64-96KB)
- L1 cache
- Warp scheduler
```

## CUDA Execution Model

### Hierarchy of Execution
```
┌─────────────────────────────────────────────────────────┐
│                    Grid (Kernel Launch)                 │
│  Entire computation, contains multiple blocks          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │
│  │ Block 0 │  │ Block 1 │  │ Block 2 │  Blocks        │
│  │(Threads)│  │(Threads)│  │(Threads)│                │
│  └─────────┘  └─────────┘  └─────────┘                 │
│                                                          │
│  ┌───────────────────────────────────────┐              │
│  │ Thread 0 │ Thread 1 │ ... │ Thread N │ Threads     │
│  └───────────────────────────────────────┘              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Warps
```
A Warp = 32 threads executing in lockstep

All threads in warp execute SAME instruction
If threads diverge (if/else), they serialize!

Example:
if (threadIdx.x < 16) {
    // Threads 0-15 execute this
    // Threads 16-31 are idle
} else {
    // Threads 16-31 execute this
    // Threads 0-15 are idle
}

Performance penalty for warp divergence!
```

## CUDA Kernel Programming

### Basic Kernel Structure
```cuda
__global__ void vector_add(float* a, float* b, float* c, int n) {
    // Calculate global thread ID
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Boundary check
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

// Host code to launch kernel
int main() {
    int n = 1000000;
    int block_size = 256;
    int grid_size = (n + block_size - 1) / block_size;

    vector_add<<<grid_size, block_size>>>(d_a, d_b, d_c, n);
    cudaDeviceSynchronize();
}
```

### Kernel Launch Parameters
```cuda
// <<<grid_dim, block_dim, shared_mem, stream>>>

my_kernel<<<dim3(2, 2), dim3(16, 16), 0, 0>>>(...);

// Grid: 2×2 = 4 blocks
// Block: 16×16 = 256 threads per block
// Total threads: 4 × 256 = 1024

// shared_mem: Dynamic shared memory (bytes)
// stream: CUDA stream for async execution
```

## Memory Hierarchy

### CUDA Memory Types
```
┌─────────────────────────────────────────────────────────┐
│                    Memory Hierarchy                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Registers (fastest)                                    │
│  └─ Per-thread, limited (~64 per thread)               │
│                                                          │
│  Shared Memory (fast, block-local)                      │
│  └─ Per-block, ~64KB, programmable cache                │
│                                                          │
│  L1 Cache (fast, read-only)                             │
│  └─ Per-SM, ~128KB                                      │
│                                                          │
│  L2 Cache (medium, global)                              │
│  └─ Per-GPU, ~5.5MB                                     │
│                                                          │
│  Global Memory (slow, main GPU memory)                  │
│  └─ 11GB GDDR6, ~400-600 cycle latency                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Memory Access Patterns
```cuda
// Coalesced access (good!)
// Adjacent threads access adjacent memory
__global__ void coalesced_read(float* data) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    float value = data[idx];  // Good: coalesced
}

// Strided access (bad!)
// Threads access memory with gaps
__global__ void strided_read(float* data, int stride) {
    int idx = (blockIdx.x * blockDim.x + threadIdx.x) * stride;
    float value = data[idx];  // Bad: not coalesced
}
```

### Shared Memory Usage
```cuda
__global__ void matrix_multiply_shared(float* A, float* B, float* C, int N) {
    // Shared memory tiles
    __shared__ float tile_A[16][16];
    __shared__ float tile_B[16][16];

    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;

    float sum = 0.0f;

    // Loop over tiles
    for (int t = 0; t < N/16; ++t) {
        // Load tiles into shared memory
        tile_A[threadIdx.y][threadIdx.x] = A[row * N + t * 16 + threadIdx.x];
        tile_B[threadIdx.y][threadIdx.x] = B[(t * 16 + threadIdx.y) * N + col];

        // Sync to ensure all threads loaded
        __syncthreads();

        // Compute using shared memory (fast!)
        for (int k = 0; k < 16; ++k) {
            sum += tile_A[threadIdx.y][k] * tile_B[k][threadIdx.x];
        }

        // Sync before loading next tile
        __syncthreads();
    }

    C[row * N + col] = sum;
}
```

## PyTorch CUDA Integration

### Writing Custom CUDA Kernels for PyTorch
```cpp
// my_kernel.cu
#include <torch/extension.h>
#include <cuda_runtime.h>

__global__ void my_kernel_kernel(
    const float* __restrict__ input,
    float* __restrict__ output,
    int size
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = input[idx] * 2.0f + 1.0f;
    }
}

torch::Tensor my_kernel_forward(torch::Tensor input) {
    auto output = torch::zeros_like(input);
    int size = input.numel();

    const int block_size = 256;
    const int grid_size = (size + block_size - 1) / block_size;

    my_kernel_kernel<<<grid_size, block_size>>>(
        input.data_ptr<float>(),
        output.data_ptr<float>(),
        size
    );

    return output;
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("forward", &my_kernel_forward, "My custom kernel");
}
```

### JIT Compilation with C++/CUDA
```python
import torch
from torch.utils.cpp_extension import load

# Load custom CUDA kernel
custom_kernel = load(
    name='custom_kernel',
    sources=['my_kernel.cpp', 'my_kernel.cu'],
    extra_cuda_cflags=['-O3'],
    verbose=True
)

# Use the kernel
x = torch.randn(1000, device='cuda')
y = custom_kernel.forward(x)
```

## Tensor Cores Programming

### Matrix Multiply-Accumulate (WMMA)
```cuda
#include <mma.h>
using namespace nvcuda::wmma;

__global__ void tensor_core_mma(
    half* A, half* B, float* C, int M, int N, int K
) {
    // Tensor core requires 16x16x16 matrix multiply
    // Fragment: handle to matrix tile in tensor core

    // Load fragments
    fragment<matrix_a, 16, 16, 16, half, row_major> a_frag;
    fragment<matrix_b, 16, 16, 16, half, col_major> b_frag;
    fragment<accumulator, 16, 16, 16, float> c_frag;

    // Load matrix tiles (use shared memory for better performance)
    load_matrix_sync(a_frag, A, 16);
    load_matrix_sync(b_frag, B, 16);
    fill_fragment(c_frag, 0.0f);

    // Matrix multiply-accumulate using tensor cores
    mma_sync(c_frag, a_frag, b_frag, c_frag);

    // Store result
    store_matrix_sync(C, c_frag, 16, mem_row_major);
}
```

### Tensor Core Requirements
```
Requirements for Tensor Core usage:
1. Data types: FP16, BF16, INT8, INT4
2. Dimensions: Multiples of 16 (for mma.sync)
3. Alignment: 32-byte aligned (128-bit)
4. Architecture: Volta (Turing is Volta successor)

Performance:
- FP16: 8x faster than FP32
- INT8: 16x faster than FP32
- Only for matrix operations!
```

## Optimization Techniques

### Loop Unrolling
```cuda
__global__ void unrolled_kernel(float* data, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Manual loop unrolling (4x)
    #pragma unroll
    for (int i = 0; i < 4; ++i) {
        int pos = idx * 4 + i;
        if (pos < n) {
            data[pos] *= 2.0f;
        }
    }
}
```

### Memory Padding
```cuda
// Avoid bank conflicts by padding
// Shared memory has 32 banks
// Access pattern: shared_memory[idx * 32] causes bank conflict!

__global__ void padded_kernel() {
    __shared__ float shared[32][33];  // Pad to 33!

    int idx = threadIdx.x;
    shared[idx][0] = idx;  // No bank conflict
}
```

### Occupancy Optimization
```
Occupancy = Active Warps / Max Warps per SM

Factors affecting occupancy:
1. Registers per thread (reduce register usage)
2. Shared memory per block (use less shared mem)
3. Block size (tune for optimal occupancy)

Target: >50% occupancy for good performance
```

## Debugging CUDA

### CUDA Error Checking
```cpp
#define CUDA_CHECK(call) \
    do { \
        cudaError_t error = call; \
        if (error != cudaSuccess) { \
            fprintf(stderr, "CUDA error: %s:%d: ", __FILE__, __LINE__); \
            fprintf(stderr, "code=%d, reason=%s\n", error, \
                    cudaGetErrorString(error)); \
            exit(1); \
        } \
    } while(0)

// Usage
CUDA_CHECK(cudaMalloc(&d_ptr, size));
CUDA_CHECK(cudaMemcpy(d_ptr, h_ptr, size, cudaMemcpyHostToDevice));
```

### CUDA-GDB
```bash
# Compile with debug flags
nvcc -g -G my_kernel.cu -o my_program

# Run with cuda-gdb
cuda-gdb ./my_program

# Common commands
(gdb) break my_kernel_kernel
(gdb) info threads      # Show all threads
(gdb) thread 2         # Switch to thread 2
(gdb) print idx        # Print variable
```

### Nsight Compute
```bash
# Profile kernel
ncu --set full ./my_program

# Analyze memory bandwidth
ncu --metrics dram__throughput.avg.pct_of_peak \
    --metrics l2_cache_hit_rate ./my_program

# Key metrics:
# - Achieved Occupancy
# - Memory Throughput
# - Warp Execution Efficiency
```

---

## Next Steps

- Next Module: **[2300: Framework Engineering](../2300-framework-engineering/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1202: TB3 Passthrough](../../phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md)
- [1203: Nvidia Kernel Module](../../phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md)
- [2201: PyTorch Graphs](./2201-PyTorch-Computational-Graphs.md)

**Experiment Template:** `experiments/EXP_2203_CUDA_KERNEL.md`
