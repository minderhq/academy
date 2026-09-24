---
Document ID: 2202
Title: TensorFlow XLA and Compiler Optimizations
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

# 2202: TensorFlow XLA and Compiler Optimizations

## Abstract
XLA (Accelerated Linear Algebra) is a compiler-based linear algebra executor that optimizes TensorFlow computations. It fuses operations, reduces memory bandwidth usage, and accelerates execution on the RTX 2080 Ti.

## What is XLA?

### XLA Compilation Pipeline
```
┌─────────────────────────────────────────────────────────┐
│                    TensorFlow Graph                      │
│  (High-level ops: MatMul, Add, ReLU, ...)               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    XLA HLO (High Level Optimizer)        │
│  (Lower-level ops: DotGeneral, Slice, Reduce)           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    XLA Optimizer                         │
│  - Operation fusion                                     │
│  - Buffer allocation optimization                       │
│  - Loop rewriting                                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Device-specific Backend              │
│  (PTX for NVIDIA GPUs, LLVM for CPU)                    │
└─────────────────────────────────────────────────────────┘
```

### Key Benefits
```
1. Operation Fusion: Combine multiple ops into single kernel
2. Memory Optimization: Reduce memory bandwidth usage
3. Specialization: Compile for specific input shapes
4. Cross-platform: Same code runs on CPU, GPU, TPU
```

## Enabling XLA

### In TensorFlow 2.x
```python
import tensorflow as tf

# Method 1: jit_compile decorator
@tf.function(jit_compile=True)
def my_model(x):
    x = tf.nn.dense(x, 128)
    x = tf.nn.relu(x)
    x = tf.nn.dense(x, 10)
    return x

# Method 2: Global JIT compilation
tf.config.optimizer.set_jit(True)

# Method 3: Auto-clustering (automatic XLA)
tf.config.optimizer.set_experimental_options({'auto_clustering': True})
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
def no_xla(x):
    # Each op is a separate kernel launch
    y = x + 1      # Kernel 1
    y = y * 2      # Kernel 2
    y = y ** 2     # Kernel 3
    return y

# Memory traffic:
# x → [GPU] → y → [CPU] → [GPU] → y → [CPU] → [GPU] → y
# ↑         ↑        ↑        ↑
# Read     Write    Read     Write...
```

### With XLA (Fused Kernel)
```python
@tf.function(jit_compile=True)
def with_xla(x):
    y = x + 1
    y = y * 2
    y = y ** 2
    return y

# Memory traffic:
# x → [GPU] → y (all operations in single kernel)
```

### Fusion Example Visualization
```
Original:
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│  +  │ → │  *  │ → │  ^  │ → │  +  │
└─────┘   └─────┘   └─────┘   └─────┘
GPU mem   GPU mem   GPU mem   GPU mem

XLA Fused:
┌───────────────────────────────────┐
│     (x + 1) * 2 ** 2 + 3          │
└───────────────────────────────────┘
         GPU mem (once!)
```

## HLO (High-Level Optimizer) Instructions

### Common HLO Operations
```python
import tensorflow as tf

# Compile and inspect HLO
@tf.function(jit_compile=True)
def my_function(x, y):
    return tf.matmul(x, y) + tf.reduce_sum(x, axis=1)

# Get HLO graph
log_dir = "/tmp/xla_logs"
tf.debugging.experimental.enable_dump_debug_info(
    log_dir,
    tensor_debug_mode="FULL_HEALTH"
)

# Or use XLA debugger
from tensorflow.compiler.xla import xla_data_pb2

# HLO ops include:
# - DotGeneral: General dot product
# - Slice: Array slicing
# - Reduce: Reduction operations
# - Broadcast: Broadcasting operations
```

### Manual HLO Construction
```
HLO: add {
  x = f32[100,100] parameter(0)
  y = f32[100,100] parameter(1)
  ROOT add = f32[100,100] add(x, y)
}

This gets compiled to optimized PTX for the GPU
```

## Memory Optimization

### Buffer Elimination
```python
# Without XLA: Each op creates intermediate buffer
def inefficient(x):
    a = x + 1      # Allocate buffer a
    b = a * 2      # Allocate buffer b
    c = b - 3      # Allocate buffer c
    return c

# With XLA: In-place where possible
@tf.function(jit_compile=True)
def efficient(x):
    a = x + 1      # Reuse x buffer
    b = a * 2      # Reuse a buffer
    c = b - 3      # Reuse b buffer
    return c
```

### Shape Specialization
```python
# XLA compiles for specific shapes
@tf.function(jit_compile=True)
def process_batch(x):
    return tf.nn.dense(x, 128)

# First call with shape (32, 64)
x = tf.random.normal((32, 64))
y = process_batch(x)  # Compilation triggered

# Same shape: fast
x = tf.random.normal((32, 64))
y = process_batch(x)  # Uses compiled version

# Different shape: recompile!
x = tf.random.normal((64, 64))
y = process_batch(x)  # New compilation
```

### Static Shape Recommendations
```python
# Bad: Dynamic shapes (causes recompilation)
@tf.function(jit_compile=True)
def bad_varying_batch(x):
    # Different batch sizes → recompilation
    return tf.matmul(x, x.T)

# Good: Fixed batch size or padding
@tf.function(jit_compile=True)
def good_fixed_batch(x):
    # Pad to fixed size if needed
    batch_size = tf.shape(x)[0]
    padded = tf.pad(x, [[0, 64 - batch_size], [0, 0]])
    result = tf.matmul(padded, padded.T)
    return result[:batch_size, :batch_size]
```

## XLA for Intel NUC (RTX 2080 Ti)

### GPU-Specific Optimizations
```python
# Configure TensorFlow for optimal GPU performance
gpus = tf.config.experimental.list_physical_devices('GPU')

if gpus:
    try:
        # Enable memory growth (don't allocate all VRAM)
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)

        # Enable XLA
        tf.config.optimizer.set_jit(True)

        # Set virtual device configuration
        tf.config.experimental.set_virtual_device_configuration(
            gpus[0],
            [tf.config.experimental.VirtualDeviceConfiguration(
                memory_limit=1024)]  # 1GB per virtual GPU
        )
    except RuntimeError as e:
        print(e)
```

### Tensor Core Utilization
```
XLA automatically uses Tensor Cores when:
1. Data type is FP16 or BF16
2. Dimensions are multiples of 8
3. Operations are matrix multiplications

@tf.function(jit_compile=True)
def tensor_core_friendly(x):
    x = tf.cast(x, tf.float16)  # Use FP16
    return tf.matmul(x, x, transpose_b=True)

# Ensure dimensions are multiples of 8
batch_size = 32
hidden_dim = 128  # Both divisible by 8
```

## Performance Profiling

### Using TensorBoard Profiler
```python
# Set up profiling
tf.profiler.experimental.start('/tmp/xla_profile')

# Run model
for _ in range(100):
    result = model(inputs)

tf.profiler.experimental.stop()

# View in TensorBoard
# tensorboard --logdir=/tmp/xla_profile

# Look for:
# - XLA ops (fused kernels)
# - Kernel execution time
# - Memory usage
```

### Benchmark Comparison
```python
import time

def benchmark(model, x, n_runs=100):
    # Warmup
    for _ in range(10):
        _ = model(x)

    # Time it
    start = time.time()
    for _ in range(n_runs):
        _ = model(x)
    elapsed = time.time() - start

    return elapsed / n_runs

# Compare
xla_model = tf.function(jit_compile=True)(plain_model)

no_xla_time = benchmark(plain_model, inputs)
xla_time = benchmark(xla_model, inputs)

print(f"Without XLA: {no_xla_time*1000:.2f}ms")
print(f"With XLA: {xla_time*1000:.2f}ms")
print(f"Speedup: {no_xla_time/xla_time:.2f}x")
```

## XLA Best Practices

### 1. Use tf.function
```python
# Always decorate performance-critical code
@tf.function(jit_compile=True)
def fast_layer(x):
    return tf.nn.dense(x, 256)
```

### 2. Avoid Python Control Flow
```python
# Bad: Python if statement
@tf.function
def bad(x):
    if x > 0:  # Static condition, not traced
        return x * 2
    else:
        return x * 3

# Good: TensorFlow control flow
@tf.function
def good(x):
    return tf.cond(x > 0, lambda: x * 2, lambda: x * 3)
```

### 3. Minimize tf.py_function
```python
# Bad: Python code breaks XLA
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
# Use static shapes when possible
@tf.function(jit_compile=True)
def fixed_shape(x):
    # Specify shape if known
    x = tf.ensure_shape(x, (None, 224, 224, 3))
    return tf.nn.conv2d(x, filters, strides=[1,1,1,1], padding='SAME')
```

## Troubleshooting XLA

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Recompilation overhead | Varying input shapes | Pad to fixed shape |
| Out of memory | Large intermediate buffers | Use gradient checkpointing |
| Slow compilation | Complex graph | Simplify or pre-compile |
| Incorrect results | Unsupported ops | Rewrite using supported ops |

### Checking Compilation
```python
# Check if XLA is being used
tf.debugging.set_log_device_placement(True)

# Look for "XLA" in device placement logs
# Example: "Executing op MatMul in device /job:localhost/replica:0/task:0/device:GPU:0 XLA_GPU"
```

---

## Next Steps

- Continue with: **[2203: CUDA Kernels](./2203-CUDA-Kernel-Syb-Level.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [2201: PyTorch Graphs](./2201-PyTorch-Computational-Graphs.md)
- [2203: CUDA Kernels](./2203-CUDA-Kernel-Syb-Level.md)
- [1202: TB3 Passthrough](../../phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md)

**Experiment Template:** `experiments/EXP_2202_TENSORFLOW_XLA.md`
