---
Document ID: 2203
Title: CUDA Kernel Programming and GPU Architecture
Phase: 2
Module: 2200
Last Updated: 2026-09-27
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'pytorch', 'tensorflow', 'cuda']
---

# 2203: CUDA Kernel Programming and GPU Architecture

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [GPU Architecture Overview](#gpu-architecture-overview)
- [CUDA Execution Model](#cuda-execution-model)
- [CUDA Kernel Programming](#cuda-kernel-programming)
- [Memory Hierarchy](#memory-hierarchy)
- [PyTorch CUDA Integration](#pytorch-cuda-integration)
- [Tensor Cores Programming](#tensor-cores-programming)
- [Optimization Techniques](#optimization-techniques)
- [Debugging CUDA](#debugging-cuda)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Trace a kernel launch from grid/block dimensions through warp scheduling on the SM, and predict where warp divergence costs throughput
- Write and launch a custom CUDA kernel with `<<<grid, block, shared_mem, stream>>>` and validate its output against a PyTorch reference implementation
- Choose the right memory tier (global, shared, registers, constant) for a workload, then apply coalescing and tiled matmul with `__syncthreads()` to cut global-memory traffic
- Bind a custom kernel into PyTorch via a C++ extension (`PYBIND11_MODULE`, `torch.utils.cpp_extension.load`) and call it from a training loop
- Use Tensor Cores through WMMA 16x16x16 fragments, stating the tile-shape and precision requirements they impose
- Diagnose bank conflicts (and the padding-33 fix), low occupancy, and missing-sync bugs using ncu metrics, `CUDA_CHECK`, and cuda-gdb

---

## Abstract
CUDA (Compute Unified Device Architecture) is NVIDIA's parallel computing platform. Understanding CUDA kernel programming is essential for writing optimized deep learning code - the grid/block/warp model and the memory hierarchy decide how fast your GPU actually runs.

## GPU Architecture Overview

### RTX 2080 Ti (TU102) Specifications
```text
CUDA Architecture:   Turing TU102
CUDA Cores:         4352 (FP32, 64 per SM x 68 SMs)
Tensor Cores:       544 (2nd generation, 8 per SM)
VRAM:               11GB GDDR6
Memory Bandwidth:   616 GB/s
Base Clock:         1350 MHz
Boost Clock:        1545 MHz
TDP:                250W
L2 Cache:           5.5 MB
```

### Hardware Organization
```text
┌─────────────────────────────────────────────────────────┐
│                     GPU (TU102)                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  6 GPCs x 6 TPCs, 2 SMs per TPC = 72 SMs on the die    │
│  (the RTX 2080 Ti enables 68 of them)                   │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  GPC 0     │  │  GPC 1     │  │  GPC ...   │  GPCs  │
│  │ (12 SMs)   │  │ (12 SMs)   │  │            │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  Each SM: 64 FP32 cores, 8 Tensor cores,                │
│           4 texture units, 96KB unified L1/shared       │
│                                                          │
│  Memory Controller → GDDR6 (11GB @ 14 Gbps)             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### SM (Streaming Multiprocessor)
```text
Each SM contains:
- 64 FP32 CUDA cores + 64 INT32 cores
- 8 Tensor cores (2nd generation)
- 4 texture units
- 1 register file (64K x 32-bit = 256KB; up to 255
  registers per thread)
- 96KB unified L1 + shared memory - the shared/L1 split
  is configurable (e.g. 64KB shared + 32KB L1, or reverse)
- 4 warp schedulers (one per 16-core processing block)
```

## CUDA Execution Model

### Hierarchy of Execution
```text
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
```text
A Warp = 32 threads - the unit the SM schedules

Warps execute one common instruction at a time. Pre-Volta
hardware ran the whole warp in strict lockstep; since Volta
(compute capability 7.0+), Independent Thread Scheduling gives
every thread its own program counter. The warp still issues
one instruction at a time, so divergent paths serialize:

if (threadIdx.x < 16) {
    // Threads 0-15 execute this
    // Threads 16-31 are disabled here
} else {
    // Threads 16-31 execute this
    // Threads 0-15 are disabled here
}

Performance penalty for warp divergence - the two paths
run sequentially!
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
    // Ceiling division: enough blocks to cover all n elements
    int grid_size = (n + block_size - 1) / block_size;

    // d_a, d_b, d_c: device pointers from cudaMalloc(),
    // with inputs copied over via cudaMemcpy(..., HostToDevice)
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
// stream: CUDA stream for async execution (0 = default stream)
```

## Memory Hierarchy

### CUDA Memory Types
```text
┌─────────────────────────────────────────────────────────┐
│                    Memory Hierarchy                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Registers (fastest)                                    │
│  └─ Per-thread, up to 255 per thread                    │
│                                                          │
│  Shared Memory (fast, block-local)                      │
│  └─ Up to 64KB per block, programmable cache           │
│                                                          │
│  L1 Cache (fast, per-SM)                                │
│  └─ Shares the SM's unified 96KB pool with shared mem   │
│                                                          │
│  L2 Cache (medium, GPU-wide)                            │
│  └─ Per-GPU, ~5.5MB                                     │
│                                                          │
│  Global Memory (slow, main GPU memory)                  │
│  └─ 11GB GDDR6, ~400-600 cycle latency                  │
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
// Tiled matmul: launch with dim3(16, 16) blocks and a grid of
// (N/16, N/16); requires N % 16 == 0 - no boundary checks below
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
    TORCH_CHECK(input.is_cuda() && input.is_contiguous(),
                "expected a contiguous CUDA tensor");
    auto output = torch::zeros_like(input);
    int size = input.numel();

    const int block_size = 256;
    const int grid_size = (size + block_size - 1) / block_size;

    my_kernel_kernel<<<grid_size, block_size>>>(
        input.data_ptr<float>(),
        output.data_ptr<float>(),
        size
    );
    // Production code: follow the launch with
    // C10_CUDA_KERNEL_LAUNCH_CHECK() or cudaGetLastError()

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

# Build and load the extension - the .cu file carries both the
# kernel and the PYBIND11_MODULE binding; load() compiles it
# with nvcc at first call
custom_kernel = load(
    name='custom_kernel',
    sources=['my_kernel.cu'],
    extra_cuda_cflags=['-O3'],
    verbose=True,
)

# Use the kernel
x = torch.randn(1000, device='cuda')
y = custom_kernel.forward(x)
```

## Tensor Cores Programming

### Matrix Multiply-Accumulate (WMMA)
```cuda
// WMMA ops are warp-wide: a fragment is a matrix tile distributed
// across all 32 threads of a warp, and every thread must execute
// load_matrix_sync / mma_sync / store_matrix_sync with the same
// arguments. One 16x16x16 tile per warp.
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
```text
Requirements for Tensor Core usage:
1. Data types: FP16, INT8, INT4 (INT8/INT4 added with Turing;
   BF16 support requires Ampere or newer)
2. Dimensions: Multiples of 16 (the 16x16x16 wmma tile)
3. Alignment: load/store pointers 256-bit (32-byte) aligned,
   leading dimension (ldm) a multiple of 16
4. Architecture: Volta or newer (Turing = 2nd generation)

Performance, RTX 2080 Ti peak (dense):
- FP16 Tensor: ~108 TFLOPS  ~ 8x the 13.4 TFLOPS FP32 rate
- INT8 Tensor: ~215 TOPS    ~ 16x FP32
- INT4 Tensor: ~430 TOPS
- Only for matrix multiply-accumulate!
```

## Optimization Techniques

### Loop Unrolling
```cuda
__global__ void unrolled_kernel(float* data, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // A fixed trip count lets the compiler unroll; #pragma unroll
    // makes that intent explicit even if it cannot prove the count
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
// Shared memory has 32 banks; successive 32-bit words land in
// successive banks. A warp accessing a stride-32 pattern sends
// all 32 lanes to the same bank - a 32-way bank conflict that
// serializes into 32 separate accesses.

// Bad: column writes into a plain [32][32] tile
__global__ void column_write_bad() {
    __shared__ float tile[32][32];
    int idx = threadIdx.x;              // blockDim.x == 32
    tile[idx][0] = idx;
    // addresses idx*32 -> bank (idx*32) % 32 == 0 for EVERY lane
}
// 32-way bank conflict!

// Good: pad each row to 33 floats
__global__ void column_write_good() {
    __shared__ float tile[32][33];      // pad to 33!
    int idx = threadIdx.x;
    tile[idx][0] = idx;
    // addresses idx*33 -> banks (idx*33) % 32 == idx: all distinct
}
```

### Occupancy Optimization
```text
Occupancy = Active Warps / Max Warps per SM

Turing: an SM can hold up to 32 warps (1024 threads)

Factors affecting occupancy:
1. Registers per thread (up to 255 - more registers means
   fewer resident warps)
2. Shared memory per block (up to 64KB - large tiles limit
   how many blocks fit per SM)
3. Block size (tune for optimal occupancy)

Target: >50% occupancy for good performance - and measure:
a memory-bound kernel can saturate bandwidth below 100%
occupancy
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
```text
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

# Analyze memory bandwidth and cache behavior (comma-separated
# metric names; discover more with: ncu --query-metrics)
ncu --metrics dram__throughput.avg.pct_of_peak_sustained_elapsed,lts__t_sector_hit_rate.pct \
    ./my_program

# Key metrics:
# - Achieved Occupancy: sm__warps_active.avg.pct_of_peak_sustained_active
# - DRAM Throughput:    dram__throughput.avg.pct_of_peak_sustained_elapsed
# - L2 Hit Rate:        lts__t_sector_hit_rate.pct
# - Warp Execution Efficiency
```

---

## References

### Related Documents

- [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md)
- [2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md)
- [1202: GPU Passthrough (IOMMU/VFIO)](../../phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md)

### External References

- [CUDA C++ Programming Guide — NVIDIA](https://docs.nvidia.com/cuda/cuda-programming-guide/index.html)
- [NVIDIA Turing Architecture In-Depth — NVIDIA Developer Blog](https://developer.nvidia.com/blog/nvidia-turing-architecture-in-depth/)
- [torch.utils.cpp_extension — PyTorch 2.14 documentation](https://docs.pytorch.org/docs/2.14/cpp_extension.html)
- [Nsight Compute Profiling Guide — NVIDIA](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)

---

## Next Steps

- Next Module: **[2300: Framework Engineering](../2300-framework-engineering/)**
- Assessment: **[2200: Frameworks - Quiz](./assessment/QUIZ.md)**

---

**Related:**
- [2102: Backpropagation and Automatic Differentiation](../2100-calculus/2102-Backpropagation-and-Derivatives.md)
- [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md)
- [2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md)

**Experiment:** [EXP-2203: CUDA Kernels](../../../../experiments/EXP_2203_CUDA_KERNELS.md)
