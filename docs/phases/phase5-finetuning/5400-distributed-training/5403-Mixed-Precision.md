---
Document ID: 5403
Title: Mixed Precision Training
Phase: 5
Module: 5400
Last Updated: 2026-09-24
Status: Review
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: 5402, 5404
Tags: ['training', 'optimization', 'precision']
---

# 5403: Mixed Precision Training

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Precision Formats](#precision-formats)
- [Automatic Mixed Precision (AMP)](#automatic-mixed-precision-amp)
- [Loss Scaling](#loss-scaling)
- [Implementation Patterns](#implementation-patterns)
- [Best Practices](#best-practices)
- [Performance Optimization](#performance-optimization)
- [Common Issues](#common-issues)
- [Framework Support](#framework-support)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Precision Formats
- Explain Automatic Mixed Precision (AMP)
- Explain Loss Scaling
- Apply Implementation Patterns
- Explain Best Practices
- Measure and evaluate Performance Optimization

---

## Abstract

Mixed precision training uses lower precision (FP16 or BF16) for most operations while maintaining critical parts in FP32, reducing memory usage and increasing speed.

## Precision Formats

### FP16 (Half Precision)

**Spec:** 16-bit floating point
- 1 sign bit
- 5 exponent bits
- 10 mantissa bits

**Range:** ±65,504, ~3 decimal digits of precision

```python
# Convert to FP16
model_fp16 = model.half()
input_fp16 = input.half()

# Or use autocast
with torch.cuda.amp.autocast(dtype=torch.float16):
    output = model(input)
```

**Pros:**
- 2x memory reduction
- Faster computation on Tensor Cores
- Wide hardware support

**Cons:**
- Limited range (overflow/underflow risk)
- Reduced precision
- May require loss scaling

### BF16 (Brain Float)

**Spec:** 16-bit brain floating point
- 1 sign bit
- 8 exponent bits (same as FP32)
- 7 mantissa bits

**Range:** Same as FP32, ~2 decimal digits of precision

```python
# BF16 on supported hardware (Ampere+)
with torch.cuda.amp.autocast(dtype=torch.bfloat16):
    output = model(input)
```

**Pros:**
- Same dynamic range as FP32
- No loss scaling needed
- More stable training

**Cons:**
- Requires newer hardware (Ampere+)
- Lower precision than FP16
- Not all operations supported

## Automatic Mixed Precision (AMP)

PyTorch AMP automatically chooses precision for each operation:

```python
from torch.cuda.amp import autocast, GradScaler

# Create gradient scaler for FP16
scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()

    # Forward with automatic precision
    with autocast(dtype=torch.float16):
        output = model(batch)
        loss = criterion(output, target)

    # Backward with scaled gradients
    scaler.scale(loss).backward()

    # Unscale gradients before optimizer step
    scaler.step(optimizer)

    # Update scaler for next iteration
    scaler.update()
```

## Loss Scaling

FP16 has limited range, so gradients can underflow. Loss scaling helps:

```python
# Static loss scaling
scaler = GradScaler(init_scale=2.0**10)

# Dynamic loss scaling (recommended)
scaler = GradScaler(
    init_scale=2.0**16,      # Start with large scale
    growth_factor=2.0,        # Double scale each step
    backoff_factor=0.5,       # Halve on overflow
    growth_interval=2000,     # Steps between growth
)

# Check for overflow
if scaler.get_scale() == previous_scale:
    # No overflow, can increase scale
    scaler.update()
else:
    # Overflow detected, scale reduced
    pass
```

## Implementation Patterns

### Training Loop with AMP

```python
def train_amp(model, dataloader, optimizer, epochs, dtype=torch.float16):
    scaler = GradScaler()

    for epoch in range(epochs):
        for batch in dataloader:
            inputs, targets = batch

            optimizer.zero_grad()

            # Mixed precision forward
            with autocast(dtype=dtype):
                outputs = model(inputs)
                loss = criterion(outputs, targets)

            # Mixed precision backward
            scaler.scale(loss).backward()

            # Unscale before clipping
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

            # Optimizer step
            scaler.step(optimizer)
            scaler.update()
```

### Gradient Accumulation with AMP

```python
def train_with_accumulation(model, dataloader, optimizer, accumulation_steps):
    scaler = GradScaler()

    for i, batch in enumerate(dataloader):
        inputs, targets = batch

        # Forward with mixed precision
        with autocast():
            outputs = model(inputs)
            loss = criterion(outputs, targets) / accumulation_steps

        # Backward
        scaler.scale(loss).backward()

        # Step optimizer every N batches
        if (i + 1) % accumulation_steps == 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
```

## Best Practices

### Choose the Right Precision

```python
# Check hardware capability
if torch.cuda.is_bf16_supported():
    dtype = torch.bfloat16  # Preferred
    scaler = None  # No scaler needed
else:
    dtype = torch.float16
    scaler = GradScaler()
```

### Master Weights

Keep FP32 master weights for stability:

```python
from torch.cuda.amp import autocast

# Model has FP16 parameters but FP32 master weights
with autocast():
    output = model(input)

# Gradients are scaled and unscaled automatically
scaler.scale(loss).backward()
scaler.step(optimizer)  # Updates FP32 master weights
scaler.update()
```

### Convert Models Safely

```python
# Convert to mixed precision
model = model.to(device='cuda')

# Option 1: Convert entire model
model.half()  # or model.bfloat16()

# Option 2: Use autocast (recommended)
# No model conversion needed
with autocast():
    output = model(input)

# Option 3: Selective conversion
for name, module in model.named_modules():
    if 'layer_norm' not in name:
        module.half()
```

## Performance Optimization

### Memory Optimization

```python
# Enable gradient checkpointing with AMP
from torch.utils.checkpoint import checkpoint

def forward_with_checkpointing(x):
    return checkpoint(custom_layer, x)

with autocast():
    output = forward_with_checkpointing(input)
```

### Benchmark Precision

```python
import time

def benchmark_precision(model, input_size, dtype, iterations=100):
    model = model.to(dtype).cuda()
    dummy_input = torch.randn(input_size).cuda().to(dtype)

    # Warmup
    for _ in range(10):
        _ = model(dummy_input)

    # Benchmark
    torch.cuda.synchronize()
    start = time.time()

    for _ in range(iterations):
        _ = model(dummy_input)

    torch.cuda.synchronize()
    elapsed = time.time() - start

    return elapsed / iterations

# Compare
fp32_time = benchmark_precision(model, (1, 512), torch.float32)
fp16_time = benchmark_precision(model, (1, 512), torch.float16)
bf16_time = benchmark_precision(model, (1, 512), torch.bfloat16)
```

## Common Issues

### 1. NaN or Inf Loss

```python
# Enable gradient checking
torch.autograd.detect_anomaly()

# Reduce initial scale
scaler = GradScaler(init_scale=2.0**8)

# Use BF16 if available
if torch.cuda.is_bf16_supported():
    with autocast(dtype=torch.bfloat16):
        output = model(input)
```

### 2. Performance Degradation

```python
# Ensure using Tensor Cores
# Input tensors must be aligned to 8 bytes
def pad_to_eight(x):
    size = x.size(-1)
    padded_size = ((size + 7) // 8) * 8
    return torch.nn.functional.pad(x, (0, padded_size - size))
```

## Framework Support

| Framework | FP16 | BF16 | AMP |
|-----------|------|------|-----|
| **PyTorch** | ✅ | ✅ | ✅ |
| **TensorFlow** | ✅ | ✅ | ✅ |
| **JAX** | ✅ | ✅ | ✅ |
| **DeepSpeed** | ✅ | ✅ | ✅ |

---

**Next:** [5404: Distributed Optimization](./5404-Distributed-Optimization.md)

**Last Updated:** 2026-02-05

## References

### Related ai-engineering-curriculum Documents

- [5402: Model Parallelism](5402-Model-Parallelism.md)
- [5404: Distributed Optimization](5404-Distributed-Optimization.md)

---