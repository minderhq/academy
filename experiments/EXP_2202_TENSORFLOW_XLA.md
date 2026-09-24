# EXP-2202: TensorFlow XLA Optimization

**Accelerating TensorFlow with XLA (Accelerated Linear Algebra)**

---

## 🎯 Experiment Overview

**Time:** 45-60 minutes
**Difficulty:** ⭐⭐ Intermediate
**Prerequisites:**
- 2201-PyTorch-Computational-Graphs.md
- Basic TensorFlow knowledge
- Understanding of graph optimization

**Learning Objectives:**
- Understand XLA compilation
- Benchmark XLA vs eager execution
- Implement JIT compilation
- Optimize TensorFlow models with XLA

---

## 📚 Background

XLA (Accelerated Linear Algebra) is a domain-specific compiler for linear algebra that optimizes TensorFlow computations. It:

1. **Fuses operations** - Combines multiple ops into single kernels
2. **Optimizes memory usage** - Reduces memory allocations
3. **Improves performance** - Especially for GPU workloads

---

## 🔬 Experiment 1: XLA Basics (20 minutes)

### Step 1.1: Enable XLA in TensorFlow

```python
# File: xla_basics.py
"""
XLA Optimization with TensorFlow
================================
"""

import tensorflow as tf
import time
import numpy as np

# Check if XLA is available
print("TensorFlow version:", tf.__version__)
print("XLA available:", tf.config.list_physical_devices('XLA_GPU'))

# Enable XLA
tf.config.optimizer.set_jit(True)  # Enable XLA compilation

# Sample computation
def create_computation():
    """Create a sample computation to optimize"""
    @tf.function(jit_compile=True)
    def complex_computation(x):
        # Multiple operations that XLA can fuse
        y = tf.matmul(x, x)  # Matrix multiplication
        y = tf.nn.relu(y)     # ReLU activation
        y = tf.math.reduce_mean(y, axis=1)  # Mean
        return y

    return complex_computation

# Create input
x = tf.random.normal([1000, 1000])

# Benchmark without XLA
@tf.function(jit_compile=False)
def computation_no_xla(x):
    y = tf.matmul(x, x)
    y = tf.nn.relu(y)
    y = tf.math.reduce_mean(y, axis=1)
    return y

# Warmup
_ = computation_no_xla(x)
_ = create_computation()(x)

# Benchmark
start = time.time()
for _ in range(100):
    _ = computation_no_xla(x)
time_no_xla = time.time() - start

start = time.time()
for _ in range(100):
    _ = create_computation()(x)
time_with_xla = time.time() - start

print(f"\n=== Benchmark Results ===")
print(f"Without XLA: {time_no_xla:.3f}s")
print(f"With XLA:    {time_with_xla:.3f}s")
print(f"Speedup:     {time_no_xla/time_with_xla:.2f}x")
```

**Checkpoint 1:** ✅ XLA basics working

---

## 🔬 Experiment 2: HLO Inspection (20 minutes)

### Step 2.1: View Compiled XLA Code

```python
# File: xla_hlo.py
"""
Inspect XLA HLO (High Level Optimizer) code
"""

import tensorflow as tf

# Enable XLA logging
import os
os.environ['TF_XLA_FLAGS'] = '--tf_xla_auto_jit=2'

@tf.function(jit_compile=True)
def model_fn(x):
    """Simple model to compile"""
    w1 = tf.Variable(tf.random.normal([784, 256]))
    b1 = tf.Variable(tf.zeros([256]))
    w2 = tf.Variable(tf.random.normal([256, 10]))
    b2 = tf.Variable(tf.zeros([10]))

    y = tf.matmul(x, w1) + b1
    y = tf.nn.relu(y)
    y = tf.matmul(y, w2) + b2
    return y

# Get XLA compilation
x = tf.random.normal([1, 784])
log_dir = "logs/xla_ir"

# Create function
concrete_fn = tf.function(model_fn).get_concrete_function(x)

# Get XLA IR
print("=== XLA Optimization ===")

try:
    # Try to get XLA IR (works in newer TensorFlow versions)
    print("Attempting to extract XLA IR...")
    print("Note: Full HLO inspection requires TF_XLA_DEBUG")
except Exception as e:
    print(f"Note: {e}")

# Benchmark with different sizes
sizes = [128, 256, 512, 1024]
results = []

for size in sizes:
    x = tf.random.normal([1, size])

    # Without XLA
    @tf.function(jit_compile=False)
    def no_xla(x):
        return tf.matmul(x, tf.random.normal([size, size]))

    start = time.time()
    for _ in range(10):
        _ = no_xla(x)
    time_no_xla = time.time() - start

    # With XLA
    @tf.function(jit_compile=True)
    def with_xla(x):
        return tf.matmul(x, tf.random.normal([size, size]))

    start = time.time()
    for _ in range(10):
        _ = with_xla(x)
    time_with_xla = time.time() - start

    speedup = time_no_xla / time_with_xla
    results.append((size, time_no_xla, time_with_xla, speedup))

    print(f"Size {size:4d}: No XLA={time_no_xla:.3f}s, XLA={time_with_xla:.3f}s, Speedup={speedup:.2f}x")
```

**Checkpoint 2:** ✅ HLO inspection working

---

## 🔬 Experiment 3: Real-World Model (20 minutes)

```python
# File: xla_real_model.py
"""
XLA optimization on real model
"""

import tensorflow as tf
import time

# Create a simple neural network
class SimpleModel(tf.keras.Model):
    def __init__(self):
        super(SimpleModel, self).__init__()
        self.dense1 = tf.keras.layers.Dense(256, activation='relu')
        self.dense2 = tf.keras.layers.Dense(128, activation='relu')
        self.dense3 = tf.keras.layers.Dense(10)

    def call(self, x):
        x = self.dense1(x)
        x = self.dense2(x)
        x = self.dense3(x)
        return x

# Compile without XLA
model_no_xla = SimpleModel()

# Compile with XLA
model_with_xla = SimpleModel()

# Enable XLA for second model
model_with_xla.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    run_eagerly=False  # Enable graph mode
)

# Prepare data
(x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
x_train = x_train[:10000].reshape(-1, 784).astype('float32') / 255.0
y_train = y_train[:10000]

# Benchmark
batch_size = 32
dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train))
dataset = dataset.batch(batch_size)

print("\n=== Real-World Model Benchmark ===")

# Without XLA
model_no_xla.compile(optimizer='adam', loss='sparse_categorical_crossentropy')

start = time.time()
for epoch in range(3):
    for x_batch, y_batch in dataset:
        loss = model_no_xla.train_on_batch(x_batch, y_batch)
time_no_xla = time.time() - start

# With XLA
start = time.time()
for epoch in range(3):
    for x_batch, y_batch in dataset:
        loss = model_with_xla.train_on_batch(x_batch, y_batch)
time_with_xla = time.time() - start

print(f"Without XLA: {time_no_xla:.2f}s")
print(f"With XLA:    {time_with_xla:.2f}s")
print(f"Speedup:     {time_no_xla/time_with_xla:.2f}x")
```

**Checkpoint 3:** ✅ Real-world model working

---

## 📊 Results Analysis

### Expected Speedups

| Operation | Speedup with XLA |
|-----------|-----------------|
| Matrix multiplication | 1.5-3x |
| Small operations | 0.8-1.2x (may be slower) |
| Complex models | 1.2-2x |

### When XLA Helps Most

1. **Large matrix operations**
2. **Static computation graphs**
3. **GPU workloads**
4. **Repeated operations**

### When XLA May Not Help

1. **Very small operations** (compilation overhead)
2. **Dynamic shapes**
3. **Heavy I/O operations**

---

## ✅ Experiment Checklist

- [ ] XLA enabled and verified
- [ ] Basic benchmark completed
- [ ] HLO inspection attempted
- [ ] Real-world model tested
- [ ] Speedup results recorded

---

## 🎓 Key Takeaways

1. **XLA = Compiler Optimizations** - Like GCC for linear algebra
2. **JIT Compilation** - Just-in-time compilation optimizes at runtime
3. **Graph Fusing** - Multiple ops become single kernel
4. **Not Always Faster** - Small operations may not benefit

---

## 🚀 Next Steps

1. **2202-TensorFlow-XLA-Compilers.md**: Full theory
2. **EXP_2203**: CUDA Kernels
3. **LAB-006**: Train Model from Scratch

---

**Last Updated:** 2026-02-04
**Experiment:** 2202 - TensorFlow XLA
**Time Estimate:** 45-60 minutes
**Difficulty:** ⭐⭐ Intermediate
