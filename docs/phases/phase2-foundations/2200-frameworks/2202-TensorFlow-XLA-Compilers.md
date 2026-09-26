---
Document ID: 2202
Title: TensorFlow XLA and Compiler Optimizations
Phase: 2
Module: 2200
Last Updated: 2026-09-26
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'pytorch', 'tensorflow', 'cuda']
---

# 2202: TensorFlow XLA and Compiler Optimizations

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [What is XLA?](#what-is-xla)
- [Enabling XLA](#enabling-xla)
- [Operation Fusion](#operation-fusion)
- [HLO (High-Level Operations) Instructions](#hlo-high-level-operations-instructions)
- [Memory Optimization](#memory-optimization)
- [GPU Compilation and Tensor Cores](#gpu-compilation-and-tensor-cores)
- [Performance Profiling](#performance-profiling)
- [XLA Best Practices](#xla-best-practices)
- [Troubleshooting XLA](#troubleshooting-xla)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain What is XLA
- Explain Enabling XLA
- Explain Operation Fusion
- Explain HLO (High-Level Operations) Instructions
- Explain Memory Optimization
- Explain GPU Compilation and Tensor Cores

---

## Abstract
XLA (Accelerated Linear Algebra) is an open-source machine-learning compiler, integrated into TensorFlow, PyTorch, and JAX. It fuses operations, optimizes buffer allocation, and lowers computations to device-specific code through LLVM.

## What is XLA?

### XLA Compilation Pipeline
```text
┌──────────────────────────────────────────────────────────┐
│              Framework graph (TF / PyTorch / JAX)         │
│  (High-level ops: MatMul, Add, ReLU, ...)                │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│            HLO (High-Level Operations) IR                 │
│  StableHLO: versioned op set — Dot, Slice, Reduce, ...   │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                    XLA Optimizer                          │
│  - Common subexpression elimination                      │
│  - Operation fusion                                      │
│  - Buffer analysis / allocation                          │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│               Device-Specific Backend Codegen             │
│  (NVIDIA GPUs via LLVM NVPTX, CPUs via LLVM)             │
└──────────────────────────────────────────────────────────┘
```

### Key Benefits
```text
1. Operation Fusion: Combine multiple ops into single kernel
2. Memory Optimization: Reduce memory bandwidth usage
3. Specialization: Compile for specific input shapes
4. Cross-platform: Same code runs on CPU, GPU, TPU
```

## Enabling XLA

### In TensorFlow 2.x
```python
import tensorflow as tf

# Method 1: compile one function with jit_compile=True
layer = tf.keras.layers.Dense(10)

@tf.function(jit_compile=True)
def my_model(x):
    return tf.nn.relu(layer(x))

# Method 2: process-wide setting, before functions are built
tf.config.optimizer.set_jit(True)
# The milder variant lets the compiler pick the clusters itself:
# tf.config.optimizer.set_experimental_options({"auto_clustering": True})
```

### In JAX
```python
import jax
import jax.numpy as jnp

# JAX uses XLA by default
def my_function(x):
    return jnp.dot(x, x.T) + jnp.sin(x)

# JIT compile
jitted_function = jax.jit(my_function)

# First call: compilation (slow)
result = jitted_function(jnp.ones((1000, 1000)))

# Subsequent calls: fast (compiled)
result = jitted_function(jnp.ones((1000, 1000)))
```

## Operation Fusion

### Without XLA (Separate Kernels)
```python
import tensorflow as tf

def no_xla(x):
    # Each op runs as its own kernel launch
    y = x + 1      # kernel 1: reads x, writes y
    y = y * 2      # kernel 2: reads y, writes a new y
    y = y ** 2     # kernel 3: reads y, writes the final y
    return y

# Device traffic: every intermediate is written to and read back
# from device memory - 3 kernel launches, 6 full passes of
# memory bandwidth across 3 temporary buffers.
```

### With XLA (Fused Kernel)
```python
import tensorflow as tf

@tf.function(jit_compile=True)
def with_xla(x):
    y = x + 1
    y = y * 2
    y = y ** 2
    return y

# One fused kernel: x is read from memory once, the result is
# written once - intermediates live in registers/shared memory.
```

### Fusion Example Visualization
```text
Original:
┌─────┐   ┌─────┐   ┌─────┐
│  +  │ → │  *  │ → │  ^  │
└─────┘   └─────┘   └─────┘
GPU mem   GPU mem   GPU mem
(x+1)      (×2)      (²)

XLA Fused:
┌─────────────────────────────┐
│     ((x + 1) * 2) ** 2      │
└─────────────────────────────┘
      GPU mem (once!)
```

## HLO (High-Level Operations) Instructions

### Inspecting Compiled HLO
```python
import tensorflow as tf

@tf.function(jit_compile=True)
def my_function(x, y):
    return tf.matmul(x, y) + tf.reduce_sum(x, axis=1)

# Get the compiler IR for concrete input shapes - works only for
# functions compiled with jit_compile=True, and only for shapes
# known at compile time
x = tf.random.normal((32, 64))
y = tf.random.normal((64, 32))

hlo = my_function.experimental_get_compiler_ir(x, y)(stage="hlo")
print(hlo.splitlines()[0])          # HLO module header

optimized = my_function.experimental_get_compiler_ir(x, y)(stage="optimized_hlo")
graphviz = my_function.experimental_get_compiler_ir(x, y)(stage="optimized_hlo_dot")

# HLO ops you will see in the dumps:
# - Dot / DotGeneral: matrix products
# - Slice: Array slicing
# - Reduce: Reduction operations
# - Broadcast: Broadcasting operations
```

### Manual HLO Example
```text
HloModule add_module

ENTRY add {
  x = f32[100,100]{1,0} parameter(0)
  y = f32[100,100]{1,0} parameter(1)
  ROOT add = f32[100,100]{1,0} add(x, y)
}

The backend lowers this HLO text through LLVM to device code -
for NVIDIA GPUs that is the LLVM NVPTX target.
```

## Memory Optimization

### Buffer Elimination
```python
import tensorflow as tf

# Without XLA: each op may materialize its own intermediate buffer
def inefficient(x):
    a = x + 1      # buffer for a
    b = a * 2      # buffer for b
    c = b - 3      # buffer for c
    return c

# With XLA: buffer analysis reuses and aliases allocations where
# it is safe, so fewer live temporaries
@tf.function(jit_compile=True)
def efficient(x):
    a = x + 1
    b = a * 2
    c = b - 3
    return c
```

### Shape Specialization
```python
import tensorflow as tf

# XLA compiles for specific input shapes
@tf.function(jit_compile=True)
def process_batch(x):
    return tf.matmul(x, x, transpose_b=True)

# First call with shape (32, 64)
x = tf.random.normal((32, 64))
y = process_batch(x)  # Compilation triggered

# Same shape: fast (cached compiled executable)
x = tf.random.normal((32, 64))
y = process_batch(x)

# Different shape: recompile!
x = tf.random.normal((64, 64))
y = process_batch(x)
```

### Static Shape Recommendations
```python
import tensorflow as tf

# Bad: the batch dimension is dynamic, so every new batch size
# triggers a fresh compilation
@tf.function(jit_compile=True)
def bad_varying_batch(x):
    return tf.matmul(x, tf.transpose(x))

# Good: pad OUTSIDE the compiled function, compile once per
# fixed shape
@tf.function(jit_compile=True)
def good_fixed_batch(x):
    # x is always (64, D) here
    return tf.matmul(x, tf.transpose(x))

def pad_to_batch(x, batch=64):
    # runs eagerly - never inside the jitted region
    deficit = batch - tf.shape(x)[0]
    return tf.pad(x, [[0, deficit], [0, 0]])
```

## GPU Compilation and Tensor Cores

### GPU-Specific Configuration
```python
import tensorflow as tf

gpus = tf.config.list_physical_devices('GPU')

if gpus:
    try:
        # Option A: memory growth - TF allocates VRAM as needed
        # instead of grabbing (nearly) all of it up front
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        # Device configuration is locked once TF initializes the
        # GPU - these calls must run before any op touches it
        print(e)

    # Option B (mutually exclusive with A): cap VRAM through a
    # virtual device instead of using memory growth
    # tf.config.experimental.set_virtual_device_configuration(
    #     gpus[0],
    #     [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=1024)]
    # )

    tf.config.optimizer.set_jit(True)   # XLA on
```

### Tensor Core Utilization
Matmuls in FP16/BF16 with dimensions divisible by 8 can run on Tensor Cores; both cuBLAS and the XLA GPU backend exploit that alignment.

```python
import tensorflow as tf

@tf.function(jit_compile=True)
def tensor_core_friendly(x):
    x = tf.cast(x, tf.float16)  # Use FP16
    return tf.matmul(x, x, transpose_b=True)

# Keep dimensions multiples of 8
batch_size = 32
hidden_dim = 128  # Both divisible by 8

x = tf.random.normal((batch_size, hidden_dim))
scores = tensor_core_friendly(x)   # (32, 32) similarity matrix
```

## Performance Profiling

### Using TensorBoard Profiler
```python
import tensorflow as tf

layer = tf.keras.layers.Dense(128)

@tf.function(jit_compile=True)
def step(x):
    return tf.nn.relu(layer(x))

inputs = tf.random.normal((128, 128))
step(inputs)  # warmup: the one-time XLA compilation lands here

tf.profiler.experimental.start('/tmp/xla_profile')
for _ in range(100):
    result = step(inputs)
tf.profiler.experimental.stop()

# View in TensorBoard
# tensorboard --logdir=/tmp/xla_profile

# Look for:
# - Fused kernels replacing many small ops
# - Per-kernel execution time
# - Memory traffic between kernels
```

### Benchmark Comparison
```python
import time
import tensorflow as tf

layer = tf.keras.layers.Dense(256)

def plain_step(x):                # eager: one kernel launch per op
    return tf.nn.relu(layer(x))

xla_step = tf.function(jit_compile=True)(plain_step)

x = tf.random.normal((256, 256))
plain_step(x)
xla_step(x)   # warmup: absorbs the one-time XLA compilation

def benchmark(fn, x, n_runs=100):
    start = time.perf_counter()
    for _ in range(n_runs):
        out = fn(x)
    out.numpy()   # sync the device queue before reading the clock
    return (time.perf_counter() - start) / n_runs

no_xla_time = benchmark(plain_step, x)
xla_time = benchmark(xla_step, x)

print(f"Without XLA: {no_xla_time*1000:.2f}ms")
print(f"With XLA: {xla_time*1000:.2f}ms")
# Tiny graphs can tie: XLA pays off on many-op graphs and
# amortized repeated calls, and costs compile time up front.
```

## XLA Best Practices

### 1. Use tf.function
```python
import tensorflow as tf

# Always compile performance-critical code
dense = tf.keras.layers.Dense(256)

@tf.function(jit_compile=True)
def fast_layer(x):
    return tf.nn.relu(dense(x))
```

### 2. Python Control Flow and AutoGraph
```python
import tensorflow as tf

# A Python `if` over a Tensor is not a plain Python branch under
# @tf.function: AutoGraph rewrites it into tf.cond and BOTH
# branches are baked into the graph - with jit_compile=True both
# are compiled too. Fine for small models; costly if the branches
# are large.
@tf.function
def autograph_branch(x):
    if x > 0:
        return x * 2
    return x * 3   # compiled as the other tf.cond branch
```

### 3. Minimize tf.py_function
```python
import tensorflow as tf

# Bad: Python code has no XLA lowering - ops after it cannot be
# clustered with ops before it
@tf.function
def bad(x):
    return tf.py_function(lambda x: x.numpy() + 1, [x], tf.float32)

# Good: Pure TensorFlow ops
@tf.function
def good(x):
    return x + 1
```

### 4. Be Careful with Shapes
```python
import tensorflow as tf

# Fully static shapes compile best - a None batch dimension is
# a different compilation for every batch size
filters = tf.random.normal((3, 3, 3, 16))  # (kH, kW, in, out)

@tf.function(jit_compile=True)
def fixed_shape(x):
    x = tf.ensure_shape(x, (32, 224, 224, 3))
    return tf.nn.conv2d(x, filters, strides=[1, 1, 1, 1], padding='SAME')
```

## Troubleshooting XLA

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Recompilation overhead | Varying input shapes | Pad to fixed shape outside the jitted function |
| Out of memory | Large intermediate buffers | Smaller batch, or tf.recompute_grad |
| Slow compilation | Complex graph | Simplify, or compile once and reuse the executable |
| Incorrect results | Unsupported ops | Rewrite using supported ops |

### Checking Compilation
```python
import tensorflow as tf

@tf.function(jit_compile=True)
def fused(x):
    return tf.reduce_sum(tf.sin(x) * tf.cos(x))

x = tf.random.normal((8, 8))

# 1. Compilation announces itself in the log:
#    "Compiled cluster using XLA!"
fused(x)

# 2. Compiler IR exists only for compiled functions - this raises
#    if jit_compile was not actually in effect
hlo = fused.experimental_get_compiler_ir(x)(stage="hlo")
print(hlo.splitlines()[0])   # HLO module header
```

---

## References

### Related Documents

- [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md)
- [2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Syb-Level.md)
- [2102: Backpropagation and Automatic Differentiation](../2100-calculus/2102-Backpropagation-and-Derivatives.md)

### External References

- [XLA — OpenXLA documentation](https://openxla.org/xla)
- [XLA Architecture — OpenXLA documentation](https://openxla.org/xla/architecture)
- [Using XLA with tf.function — OpenXLA tutorial](https://openxla.org/xla/tf2xla/tutorials/jit_compile)
- [Better performance with tf.function — TensorFlow guide](https://www.tensorflow.org/guide/function)

---

## Next Steps

- Continue with: **[2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Syb-Level.md)**
- Next Module: **[2300: Framework Engineering](../2300-framework-engineering/)**
- Assessment: **[2200: Frameworks - Quiz](./assessment/QUIZ.md)**

---

**Related:**
- [2102: Backpropagation and Automatic Differentiation](../2100-calculus/2102-Backpropagation-and-Derivatives.md)
- [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md)
- [2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Syb-Level.md)

**Experiment:** [EXP-2202: TensorFlow XLA Optimization](../../../../experiments/EXP_2202_TENSORFLOW_XLA.md)
