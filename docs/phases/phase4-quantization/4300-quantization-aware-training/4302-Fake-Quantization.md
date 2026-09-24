---
Document ID: 4302
Title: Fake Quantization
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

# 4302: Fake Quantization

## Abstract

Fake quantization is the core mechanism of QAT. It simulates quantization during forward pass while allowing gradients to flow during backward pass.

## The Challenge

**Problem:** Rounding operations are not differentiable (gradient is zero everywhere).

```
      ┌─────┐
x ───>│round│───> round(x)      Gradient = 0 almost everywhere
      └─────┘
```

**Solution:** Straight-Through Estimator (STE) pretends rounding didn't happen.

```
Forward:  round(x)     Actual computation
Backward: x            Pretend identity function
```

## Straight-Through Estimator

### Mathematical Foundation

The STE approximates the gradient of the rounding function:

```
∂round(x) / ∂x ≈ 1  (when x is in reasonable range)
```

This is incorrect but works well in practice.

### Implementation Options

#### Option 1: Identity STE (Simplest)

```python
class RoundSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        return torch.round(x)

    @staticmethod
    def backward(ctx, grad_output):
        # Identity gradient: pretend round(x) = x
        return grad_output

# Usage
x = torch.randn(10, requires_grad=True)
x_rounded = RoundSTE.apply(x)
loss = x_rounded.sum()
loss.backward()
```

#### Option 2: Clamped STE

Prevent gradients from flowing outside valid quantization range:

```python
class ClampedSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, qmin, qmax):
        return torch.clamp(torch.round(x), qmin, qmax)

    @staticmethod
    def backward(ctx, grad_output, qmin, qmax):
        # Zero gradient outside [qmin, qmax]
        return grad_output, None, None

# Usage
x_fq = ClampedSTE.apply(x / scale, -128, 127)
```

#### Option 3: Hard Tanh STE

Smoother gradient handling:

```python
class HardTanhSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, qmin, qmax):
        return torch.clamp(torch.round(x), qmin, qmax)

    @staticmethod
    def backward(ctx, grad_output, qmin, qmax):
        # Linear gradient in range [qmin-1, qmax+1], zero outside
        x = ctx.saved_tensors[0]
        mask = (x > qmin - 1) & (x < qmax + 1)
        return grad_output * mask.float(), None, None
```

## Complete Fake Quantization Module

```python
import torch
import torch.nn as nn

class FakeQuantize(nn.Module):
    """Complete fake quantization module with observer"""

    def __init__(
        self,
        bit_width=8,
        symmetric=True,
        momentum=0.01,
        per_channel=False
    ):
        super().__init__()
        self.bit_width = bit_width
        self.symmetric = symmetric
        self.momentum = momentum
        self.per_channel = per_channel

        # Quantization range
        if symmetric:
            self.qmin = -2 ** (bit_width - 1)
            self.qmax = 2 ** (bit_width - 1) - 1
        else:
            self.qmin = 0
            self.qmax = 2 ** bit_width - 1

        # Observer state
        self.register_buffer('min_val', torch.tensor(float('inf')))
        self.register_buffer('max_val', torch.tensor(float('-inf')))

    def forward(self, x):
        # Update observer statistics
        if self.training:
            self._update_observer(x)

        # Get quantization parameters
        scale, zero_point = self._get_qparams()

        # Apply fake quantization
        return self._fake_quantize(x, scale, zero_point)

    def _update_observer(self, x):
        """Update min/max with moving average"""
        if self.per_channel and x.dim() >= 2:
            # Per-channel: track stats per output channel
            reduction_dims = list(range(x.dim()))
            reduction_dims.pop(1)  # Keep channel dim
            x_min = x.amin(dim=reduction_dims)
            x_max = x.amax(dim=reduction_dims)
        else:
            # Per-tensor: global stats
            x_min = x.min()
            x_max = x.max()

        # Exponential moving average
        self.min_val = (
            self.momentum * x_min +
            (1 - self.momentum) * self.min_val
        )
        self.max_val = (
            self.momentum * x_max +
            (1 - self.momentum) * self.max_val
        )

    def _get_qparams(self):
        """Calculate scale and zero point"""
        if self.symmetric:
            scale = self.max_val.abs().max() / self.qmax
            zero_point = torch.zeros_like(scale)
        else:
            scale = (self.max_val - self.min_val) / (self.qmax - self.qmin)
            zero_point = self.qmin - self.min_val / scale

        return scale, zero_point

    def _fake_quantize(self, x, scale, zero_point):
        """Apply fake quantization with STE"""
        # Reshape for broadcasting if needed
        if self.per_channel and scale.dim() > 0:
            shape = [1] * x.dim()
            shape[1] = -1  # Channel dimension
            scale = scale.view(shape)
            zero_point = zero_point.view(shape)

        # Quantize-dequantize
        x_quant = torch.clamp(
            torch.round(x / scale) + zero_point,
            self.qmin, self.qmax
        )
        x_dequant = (x_quant - zero_point) * scale

        return x_dequant
```

## Applying Fake Quantization to Models

### Method 1: Module Insertion

```python
def insert_fake_quant(model, target_layers=['Linear', 'Conv2d']):
    """Insert fake quantization after target layers"""

    class QuantizedWrapper(nn.Module):
        def __init__(self, module):
            super().__init__()
            self.module = module
            self.weight_quant = FakeQuantize(bit_width=8)
            self.activation_quant = FakeQuantize(bit_width=8)

        def forward(self, x):
            # Quantize input
            x = self.activation_quant(x)

            # Quantize weights
            weight_q = self.weight_quant(self.module.weight)

            # Compute
            output = self._call_original(x, weight_q)

            return output

        def _call_original(self, x, weight_q):
            if isinstance(self.module, nn.Linear):
                return nn.functional.linear(x, weight_q, self.module.bias)
            elif isinstance(self.module, nn.Conv2d):
                return nn.functional.conv2d(
                    x, weight_q, self.module.bias,
                    stride=self.module.stride,
                    padding=self.module.padding,
                    dilation=self.module.dilation,
                    groups=self.module.groups
                )

    # Wrap target layers
    for name, module in list(model.named_children()):
        if any(type(module).__name__ == t for t in target_layers):
            setattr(model, name, QuantizedWrapper(module))

    return model

# Usage
model = MyModel()
model_qat = insert_fake_quant(model)
```

### Method 2: PyTorch Native QAT

```python
import torch.ao.quantization as quant

# 1. Prepare model for QAT
model.qconfig = quant.get_default_qat_qconfig('x86')
model = quant.prepare_qat(model)

# 2. Train as normal
for epoch in range(epochs):
    train_epoch(model, dataloader)

# 3. Convert to actually quantized model
model_quantized = quant.convert(model)
```

## Debugging Fake Quantization

### Check 1: Verify Quantization Simulation

```python
def check_quantization_stats(model):
    """Print quantization statistics"""
    for name, module in model.named_modules():
        if hasattr(module, 'weight_quant'):
            scale = module.weight_quant.scale.item()
            print(f"{name}: scale={scale:.6f}, "
                  f"min={module.weight_quant.min_val:.4f}, "
                  f"max={module.weight_quant.max_val:.4f}")
```

### Check 2: Gradient Flow

```python
def check_gradients(model):
    """Verify gradients are flowing through fake quant"""
    loss = model(inputs).sum()
    loss.backward()

    for name, param in model.named_parameters():
        if param.grad is not None:
            print(f"{name}: grad_norm={param.grad.norm():.6f}")
        else:
            print(f"{name}: NO GRADIENT!")
```

### Check 3: Quantization Error Distribution

```python
def analyze_quantization_error(fp32_tensor, quantized_tensor):
    """Analyze where quantization error is worst"""

    error = (fp32_tensor - quantized_tensor).abs()

    print(f"Mean Error: {error.mean():.6f}")
    print(f"Max Error: {error.max():.6f}")
    print(f"P95 Error: {error.quantile(0.95):.6f}")

    # Visualize
    import matplotlib.pyplot as plt
    plt.hist(error.flatten().numpy(), bins=100)
    plt.xlabel('Absolute Error')
    plt.ylabel('Count')
    plt.title('Quantization Error Distribution')
    plt.show()
```

## Common Pitfalls

### Pitfall 1: Forgetting to Disable Observers

**Problem:** Observers keep updating during validation/test.

**Fix:**
```python
# Set to eval mode to freeze observers
model.eval()
# Or explicitly
for module in model.modules():
    if hasattr(module, 'activation_quant'):
        module.activation_quant.momentum = 0
```

### Pitfall 2: Wrong Reduction Dimensions

**Problem:** Per-channel quantization with wrong shape causes broadcasting errors.

**Fix:**
```python
# For Linear: weight shape [out_features, in_features]
# Per-channel quantize along dim=0
scale = weight.abs().max(dim=1, keepdim=True).values / 127
# Shape: [out_features, 1]
```

### Pitfall 3: Scale Gets Too Small

**Problem:** Scale → 0 causes division by zero or extreme values.

**Fix:**
```python
# Add minimum scale clamp
scale = scale.clamp(min=1e-5)
```

## Performance Tips

1. **Use Symmetric Quantization for Weights**: Simpler, no zero-point calculation
2. **Use Asymmetric for Activations**: Better handles non-centered distributions
3. **Per-Channel for Weights**: Significantly better accuracy
4. **Per-Tensor for Activations**: Usually sufficient, faster

## Next Steps

→ **[4303: QAT for Transformers](./4303-QAT-for-Transformers.md)** - Apply QAT to transformer architectures

---

**Last Updated:** 2026-02-04
