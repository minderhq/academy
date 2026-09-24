---
Document ID: 4301
Title: QAT Foundations
Phase: 4
Module: 4300
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'qat', 'quantization-aware-training']
---

# 4301: QAT Foundations

## Abstract

Quantization Aware Training (QAT) is a technique that simulates the effects of quantization during model training, allowing the model to adapt and maintain accuracy when deployed at lower precision.

## What is QAT?

**Key Idea:** Instead of quantizing after training (PTQ), we simulate quantization during training so the model learns to handle reduced precision.

```
Training Flow:
┌─────────────────────────────────────────────────────────────┐
│  Forward Pass                                                │
│  ├─ FP32 Weights ──┬── Fake Quantize ──> INT8 (simulated)   │
│  │                  │                                         │
│  ├─ FP32 Input ─────┴── Fake Quantize ──> INT8 (simulated)   │
│  │                                                           │
│  └─> Compute in simulated INT8                              │
│      (round to INT8, but store as FP32 for backward pass)    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Backward Pass                                               │
│  └─> Straight-Through Estimator (STE)                       │
│      (gradient bypasses rounding operation)                  │
└─────────────────────────────────────────────────────────────┘
```

## QAT vs PTQ

| Aspect | PTQ (Post-Training) | QAT (Quantization Aware) |
|--------|---------------------|--------------------------|
| **Training** | Not required | Required |
| **Time** | Minutes | Hours-days |
| **Accuracy** | Good at 8-bit, degrades at 4-bit | Better at 4-bit and below |
| **Complexity** | Simple | Moderate |
| **Best For** | Fast deployment, >8-bit | Extreme compression, edge |

## How QAT Works

### 1. Fake Quantization

During forward pass, we simulate quantization:

```python
import torch

def fake_quantize(x, scale, zero_point, qmin=-128, qmax=127):
    """Simulate INT8 quantization in forward pass"""
    # Quantize
    x_quant = torch.clamp(
        torch.round(x / scale) + zero_point,
        qmin, qmax
    )
    # Dequantize back to FP32
    x_dequant = (x_quant - zero_point) * scale
    return x_dequant

# Example
weight = torch.randn(256, 256)  # FP32 weights
scale = weight.abs().max() / 127
zero_point = 0

# During training, use fake quantized version
weight_fake_q = fake_quantize(weight, scale, zero_point)
output = input @ weight_fake_q.T  # Computation
```

### 2. Straight-Through Estimator (STE)

During backward pass, gradients need to flow through the rounding operation:

```python
class FakeQuantize(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, scale, zero_point, qmin, qmax):
        # Quantize-dequantize in forward
        x_quant = torch.clamp(
            torch.round(x / scale) + zero_point,
            qmin, qmax
        )
        return (x_quant - zero_point) * scale

    @staticmethod
    def backward(ctx, grad_output):
        # STE: Pass gradient through unchanged
        # (pretend rounding didn't happen)
        return grad_output, None, None, None, None

# Usage
x = torch.randn(100, requires_grad=True)
x_fq = FakeQuantize.apply(x, scale, 0, -128, 127)
loss = x_fq.sum()
loss.backward()  # Gradient flows despite rounding
```

### 3. Moving Average for Scale/Zero-Point

Scale and zero-point use moving averages to stabilize training:

```python
class QuantizationObserver:
    def __init__(self, momentum=0.01):
        self.min_val = None
        self.max_val = None
        self.momentum = momentum

    def update(self, x):
        batch_min = x.min().item()
        batch_max = x.max().item()

        if self.min_val is None:
            self.min_val = batch_min
            self.max_val = batch_max
        else:
            # Moving average
            self.min_val = (
                self.momentum * batch_min +
                (1 - self.momentum) * self.min_val
            )
            self.max_val = (
                self.momentum * batch_max +
                (1 - self.momentum) * self.max_val
            )

    def get_qparams(self):
        scale = (self.max_val - self.min_val) / 255
        zero_point = -round(self.min_val / scale)
        return scale, zero_point
```

## When to Use QAT

### Use QAT When:

1. **Targeting 4-bit or lower**: PTQ accuracy drops significantly below 8-bit
2. **Sensitive tasks**: Translation, code generation, mathematical reasoning
3. **Edge deployment**: Need smallest possible model size
4. **Have training data**: Can afford to fine-tune

### Use PTQ When:

1. **8-bit is sufficient**: PTQ usually fine for INT8
2. **No training data**: Can't access original training data
3. **Quick deployment**: Need results in minutes
4. **Limited compute**: Don't have resources for retraining

## Common Issues

### Issue 1: Activation Outliers

**Problem:** Some activations have extreme values that distort quantization range.

**Solution:**
```python
# Clip outliers before quantization
x_clipped = torch.clamp(x, -5.0, 5.0)  # Clip to [-5, 5]
x_fq = fake_quantize(x_clipped, scale, zero_point)
```

### Issue 2: Training Instability

**Problem:** Model diverges when QAT is enabled too early.

**Solution:**
```python
# Start QAT after initial convergence
for epoch in range(num_epochs):
    if epoch > 5:  # Enable QAT after epoch 5
        enable_quantization(model)
    train_epoch(model)
```

### Issue 3: Weight Channels Need Different Scales

**Problem:** Different output channels have different ranges.

**Solution:**
```python
# Per-channel quantization (for weights)
scale = weight.abs().max(dim=[1, 2], keepdim=True) / 127
# Shape: [out_channels, 1, 1] instead of scalar
```

## Implementation Checklist

- [ ] Add fake quantization modules to model
- [ ] Implement STE for backward pass
- [ ] Add observers for scale/zero-point
- [ ] Configure per-channel vs per-tensor
- [ ] Decide which layers to quantize
- [ ] Implement gradual QAT (start after initial training)
- [ ] Evaluate accuracy vs bit-width
- [ ] Export final quantized model

## Further Reading

- **Paper:** "Quantization and Training of Neural Networks" (Jacob et al., 2018)
- **Paper:** "Training Low-bit Neural Networks" (Zhou et al., 2024)
- **Tutorial:** PyTorch QAT Documentation
- **Code:** HuggingFace `bitsandbytes` library

## Next Steps

→ **[4302: Fake Quantization](./4302-Fake-Quantization.md)** - Deep dive into STE and quantization simulation

---

**Last Updated:** 2026-02-04
