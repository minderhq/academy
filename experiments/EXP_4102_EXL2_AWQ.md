---
Document ID: EXP_4102
Title: "EXP-4102: EXL2 vs AWQ"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
---

# EXP-4102: EXL2 vs AWQ

**Comparing advanced quantization methods**

---

## 🎯 Experiment Overview

**Time:** 75-90 minutes

**Difficulty:** ⭐⭐⭐ Advanced

**Prerequisites:**

- EXP_4101: GGUF Quantization
- Understanding of model quantization

**Learning Objectives:**

- Understand EXL2 quantization
- Implement AWQ (Activation-aware Quantization)
- Compare both methods
- Benchmark performance and accuracy

---

## 📚 Background

Two popular advanced quantization formats:

### EXL2
- **Format**: Custom format for exllamav2
- **Features**: Optimized for fast inference
- **Bits**: 2-8 bit support
- **Use case**: Maximum inference speed

### AWQ
- **Format**: Activation-aware Weight Quantization
- **Features**: Preserves activation magnitudes
- **Bits**: 3-4 bit
- **Use case**: Better accuracy retention

---

## 🔬 Experiment 1: EXL2 Quantization (25 minutes)

### Step 1.1: Implement EXL2

```python
# File: exl2_quantize.py
"""
EXL2 Quantization Implementation
===============================
"""

import numpy as np
from typing import Tuple

def quantize_exl2(weights: np.ndarray, bits: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    """
    Quantize weights using EXL2 format

    Args:
        weights: (m, n) FP16 weights
        bits: Quantization bits (2-8)

    Returns:
        qweights: Quantized weights
        scales: Per-channel scales
    """
    m, n = weights.shape
    q_max = 2 ** bits - 1

    # Per-channel quantization
    qweights = np.zeros_like(weights, dtype=np.uint8)
    scales = np.zeros(m, dtype=np.float16)

    for i in range(m):
        row = weights[i, :]

        # Calculate scale - the magnitude range is halved because the top
        # bit of each code carries the sign (7 steps for 4-bit)
        w_max = np.abs(row).max()
        scale = w_max / (q_max // 2)
        scales[i] = scale

        # Quantize magnitude only
        magnitude = np.round(np.abs(row) / scale).clip(0, q_max // 2).astype(np.uint8)

        # Store sign bit
        sign = (row < 0).astype(np.uint8)
        qweights[i, :] = magnitude | (sign << (bits - 1))

    return qweights, scales

def dequantize_exl2(qweights: np.ndarray, scales: np.ndarray, bits: int) -> np.ndarray:
    """Dequantize EXL2 weights"""
    m, n = qweights.shape
    q_max = 2 ** bits - 1

    weights = np.zeros((m, n), dtype=np.float16)

    for i in range(m):
        # Extract sign and magnitude
        q_row = qweights[i, :]
        sign = (q_row >> (bits - 1)) & 1
        magnitude = q_row & (q_max // 2)

        # Dequantize
        weights[i, :] = magnitude * scales[i]
        weights[i, sign == 1] *= -1

    return weights

# Test
weights = np.random.randn(256, 512).astype(np.float16)
qweights, scales = quantize_exl2(weights, bits=4)
weights_recon = dequantize_exl2(qweights, scales, bits=4)

error = np.abs(weights - weights_recon).mean()
print(f"EXL2 quantization error: {error:.6f}")
print(f"Compression: {weights.nbytes / qweights.nbytes:.2f}x")
```

**Checkpoint 1:** ✅ EXL2 working

---

## 🔬 Experiment 2: AWQ Quantization (25 minutes)

### Step 2.1: Implement AWQ

```python
# File: awq_quantize.py
"""
AWQ Quantization Implementation
===============================
"""

import numpy as np
from typing import Tuple

def quantize_awq(weights: np.ndarray, activations: np.ndarray,
                bits: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    """
    Activation-aware Weight Quantization

    Args:
        weights: (out_features, in_features) FP16 weights
        activations: (in_features,) activation magnitudes
        bits: Quantization bits

    Returns:
        qweights: Quantized weights
        scales: Per-channel scales
    """
    out_features, in_features = weights.shape
    q_max = 2 ** bits - 1

    # Calculate importance scaling
    activation_scale = np.abs(activations).reshape(1, -1)

    # Apply activation scaling
    scaled_weights = weights * activation_scale

    # Quantize per output channel
    qweights = np.zeros_like(weights, dtype=np.uint8)
    scales = np.zeros(out_features, dtype=np.float16)

    for i in range(out_features):
        row = scaled_weights[i, :]

        # Calculate scale
        w_max = np.abs(row).max()
        scale = w_max / q_max
        scales[i] = scale

        # Quantize - clipping at -(q_max//2) keeps every code >= 0 before
        # the uint8 cast (a -1 would wrap around to 255)
        q_row = np.round(row / scale).clip(-(q_max // 2), q_max // 2)
        qweights[i, :] = (q_row + q_max // 2).astype(np.uint8)

    return qweights, scales

def dequantize_awq(qweights: np.ndarray, scales: np.ndarray, bits: int,
                   activations: np.ndarray) -> np.ndarray:
    """Dequantize AWQ weights

    Stored weights carry the activation-aware scaling, so it is undone
    here (in the real method the same factors are applied to the input
    activations at inference instead).
    """
    out_features, in_features = qweights.shape
    q_max = 2 ** bits - 1

    # Same per-channel factors used at quantize time
    activation_scale = np.abs(activations).reshape(1, -1)

    weights = np.zeros_like(qweights, dtype=np.float16)

    for i in range(out_features):
        # Dequantize
        q_row = qweights[i, :].astype(np.float32)
        deq = (q_row - q_max // 2) * scales[i]
        weights[i, :] = (deq / activation_scale).astype(np.float16)

    return weights

# Simulate activations
weights = np.random.randn(256, 512).astype(np.float16)
activations = np.random.randn(512)  # From forward pass

qweights_awq, scales_awq = quantize_awq(weights, activations, bits=4)
weights_awq_recon = dequantize_awq(qweights_awq, scales_awq, bits=4, activations=activations)

error_awq = np.abs(weights - weights_awq_recon).mean()
print(f"AWQ quantization error: {error_awq:.6f}")
print(f"Compression: {weights.nbytes / qweights_awq.nbytes:.2f}x")
```

**Checkpoint 2:** ✅ AWQ working

---

## 🔬 Experiment 3: Comparison (20 minutes)

### Step 3.1: Compare Methods

```python
# File: compare_methods.py
"""
Compare EXL2 vs AWQ
====================
"""

import numpy as np
import matplotlib.pyplot as plt

# Generate test data
weights = np.random.randn(256, 512).astype(np.float16)
activations = np.random.randn(512)

# Quantize with both methods
q_exl2, s_exl2 = quantize_exl2(weights, bits=4)
q_awq, s_awq = quantize_awq(weights, activations, bits=4)

# Dequantize
w_exl2 = dequantize_exl2(q_exl2, s_exl2, bits=4)
w_awq = dequantize_awq(q_awq, s_awq, bits=4, activations=activations)

# Calculate errors
error_exl2 = np.abs(weights - w_exl2)
error_awq = np.abs(weights - w_awq)

print("=== Quantization Comparison ===")
print(f"EXL2 Mean Error: {error_exl2.mean():.6f}")
print(f"EXL2 Max Error: {error_exl2.max():.6f}")
print(f"AWQ Mean Error: {error_awq.mean():.6f}")
print(f"AWQ Max Error: {error_awq.max():.6f}")

# Per-channel error analysis
channel_error_exl2 = error_exl2.mean(axis=1)
channel_error_awq = error_awq.mean(axis=1)

print(f"\nEXL2 Channel Error Std: {channel_error_exl2.std():.6f}")
print(f"AWQ Channel Error Std: {channel_error_awq.std():.6f}")

# Output-level error: activations weight each column's contribution,
# which is exactly what AWQ's calibration protects
x_test = np.abs(activations).astype(np.float16)
out_ref = x_test @ weights.T
out_exl2 = x_test @ w_exl2.T
out_awq = x_test @ w_awq.T

print(f"\nOutput error EXL2: {np.abs(out_ref - out_exl2).mean():.6f}")
print(f"Output error AWQ:  {np.abs(out_ref - out_awq).mean():.6f}")

# Plot comparison
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

axes[0, 0].hist(error_exl2.flatten(), bins=50, alpha=0.7, label='EXL2')
axes[0, 0].set_xlabel('Absolute Error')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('EXL2 Error Distribution')
axes[0, 0].legend()
axes[0, 0].grid(True)

axes[0, 1].hist(error_awq.flatten(), bins=50, alpha=0.7, label='AWQ', color='orange')
axes[0, 1].set_xlabel('Absolute Error')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('AWQ Error Distribution')
axes[0, 1].legend()
axes[0, 1].grid(True)

axes[1, 0].plot(channel_error_exl2, label='EXL2')
axes[1, 0].plot(channel_error_awq, label='AWQ')
axes[1, 0].set_xlabel('Channel')
axes[1, 0].set_ylabel('Mean Error')
axes[1, 0].set_title('Per-Channel Error')
axes[1, 0].legend()
axes[1, 0].grid(True)

# Error by magnitude
weight_magnitude = np.abs(weights).mean(axis=1)
axes[1, 1].scatter(weight_magnitude, channel_error_exl2, alpha=0.5, label='EXL2')
axes[1, 1].scatter(weight_magnitude, channel_error_awq, alpha=0.5, label='AWQ')
axes[1, 1].set_xlabel('Weight Magnitude')
axes[1, 1].set_ylabel('Quantization Error')
axes[1, 1].set_title('Error vs Magnitude')
axes[1, 1].legend()
axes[1, 1].grid(True)

plt.tight_layout()
plt.savefig('exl2_vs_awq.png')
print("\n✓ Saved comparison to exl2_vs_awq.png")
```

**Checkpoint 3:** ✅ Comparison complete

---

## 🔬 Experiment 4: End-to-End Test (20 minutes)

### Step 4.1: Model Layer Quantization

```python
# File: layer_quantize.py
"""
Quantize a Real Model Layer
===========================
"""

import numpy as np
import time

# Simulated layer weights (out_features, in_features) - GQA layout:
# 4096 hidden size, 8 KV heads x 128 head_dim = 1024 KV width
layer_weights = {
    'q_proj': np.random.randn(4096, 4096).astype(np.float16),
    'k_proj': np.random.randn(1024, 4096).astype(np.float16),
    'v_proj': np.random.randn(1024, 4096).astype(np.float16),
    'o_proj': np.random.randn(4096, 4096).astype(np.float16),
}

# Simulated activations (in_features per layer)
layer_activations = {
    'q_proj': np.random.randn(4096),
    'k_proj': np.random.randn(4096),
    'v_proj': np.random.randn(4096),
    'o_proj': np.random.randn(4096),
}

print("=== Layer Quantization ===")

for name, weights in layer_weights.items():
    print(f"\n{name}: {weights.shape}")

    # EXL2
    start = time.time()
    q_exl2, s_exl2 = quantize_exl2(weights, bits=4)
    time_exl2 = time.time() - start

    mem_exl2 = q_exl2.nbytes + s_exl2.nbytes

    # AWQ
    activations = layer_activations[name]
    start = time.time()
    q_awq, s_awq = quantize_awq(weights, activations, bits=4)
    time_awq = time.time() - start

    mem_awq = q_awq.nbytes + s_awq.nbytes

    mem_original = weights.nbytes

    print(f"  Original: {mem_original/1024/1024:.1f} MB")
    print(f"  EXL2: {mem_exl2/1024/1024:.1f} MB ({time_exl2*1000:.2f} ms)")
    print(f"  AWQ: {mem_awq/1024/1024:.1f} MB ({time_awq*1000:.2f} ms)")
    print(f"  EXL2 ratio: {mem_original/mem_exl2:.2f}x")
    print(f"  AWQ ratio: {mem_original/mem_awq:.2f}x")
```

**Checkpoint 4:** ✅ End-to-end test complete

---

## 📊 Results Summary

### Comparison Table

| Metric | EXL2 | AWQ | Winner |
|--------|------|-----|--------|
| **Memory** | 2x measured (4x packed) | 2x measured (4x packed) | Tie |
| **Speed** | Fast | Fast | Tie |
| **Accuracy** | Good | Better | AWQ |
| **Calibration** | None | Activations | AWQ |

### When to Use Each

**Use EXL2 when:**

- Maximum inference speed needed
- No activation data available
- Simple deployment

**Use AWQ when:**

- Better accuracy needed
- Activation data available
- Willing to trade speed for quality

---

## ✅ Experiment Checklist

- [ ] EXL2 quantization implemented
- [ ] AWQ quantization implemented
- [ ] Comparison performed
- [ ] End-to-end tested

---

## 🎓 Key Takeaways

1. **EXL2 = Speed** - Optimized for fast inference
2. **AWQ = Accuracy** - Activation-aware for better quality
3. **Both use 4-bit** - Similar compression ratios
4. **Choice depends on use case** - Speed vs accuracy
5. **Implementation complexity** - AWQ requires calibration data

---

## 🚀 Next Steps

1. **EXP_4202**: Speculative Decoding - Faster generation
2. **EXP_6201**: Hybrid Search - Combine methods
3. **LAB-009**: Production Deployment - Ship quantized models

---

**Last Updated:** 2026-10-08

**Experiment:** 4102 - EXL2 vs AWQ

**Time Estimate:** 75-90 minutes

**Difficulty:** ⭐⭐⭐ Advanced
