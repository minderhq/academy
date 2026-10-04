---
Document ID: 3302
Title: "3302: Normalization Layers - BatchNorm vs LayerNorm vs RMSNorm"
Phase: 3
Module: 3300
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'normalization']
---

# 3302: Normalization Layers - BatchNorm vs LayerNorm vs RMSNorm

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Normalization Problem](#the-normalization-problem)
- [BatchNorm](#batchnorm)
- [LayerNorm](#layernorm)
- [RMSNorm](#rmsnorm)
- [Comparison](#comparison)
- [Implementation Tips](#implementation-tips)
- [DeepNorm (Stable Deep Networks)](#deepnorm-stable-deep-networks)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Justify normalization via the general transform y = γ·((x−μ)/σ)+β and the instabilities it removes — activation-scale drift, vanishing/exploding gradients, forced-tiny learning rates
- Implement `BatchNorm1d` with `running_mean`/`running_var` EMA buffers and momentum-EMA test-time statistics, then argue why batch+spatial statistics disqualify it for transformers: batch-size dependence, train-vs-test behavior gap, variable sequence lengths
- Position the norm inside the residual branch — contrast Pre-LN (`x + Sublayer(LayerNorm(x))`, GPT-2/LLaMA) with Post-LN (`LayerNorm(x + Sublayer(x))`, original Transformer) — and explain Pre-LN's gradient-flow advantage against Post-LN's warmup requirement
- Contrast RMSNorm as LayerNorm minus mean centering — `x / RMS(x)` — and account for the ~10-20% speedup against the ~0.1-0.3% quality drop, reproducing LLaMA's fp32-upcast → `rsqrt` → cast-back pattern
- Read the selection table (BatchNorm → CNNs, LayerNorm → transformers, RMSNorm → efficient LLMs) with the +10% speed / −0.2% accuracy row to recommend RMSNorm for new models
- Apply mixed-precision hygiene — fused `nn.LayerNorm` over manual math, `SafeLayerNorm` fp32 statistics casting — then extend to DeepNorm's α=√(2N) residual scaling that stabilizes 100+ layer stacks

---

## Abstract
Normalization layers stabilize training by normalizing activations. In transformers, LayerNorm and RMSNorm are dominant, while BatchNorm is common in CNNs.

## The Normalization Problem

### Why Normalize?
```text
Without normalization:
  - Activations can grow/shrink exponentially
  - Gradients vanish or explode
  - Training becomes unstable
  - Learning rate must be very small

With normalization:
  - Activations stay in reasonable range
  - Gradients flow better
  - Higher learning rates possible
  - Faster convergence
```

### General Normalization Formula
```text
y = γ × ((x - μ) / σ) + β

Where:
- x: Input tensor
- μ: Mean (over some dimensions)
- σ: Standard deviation (over some dimensions)
- γ: Learnable scale parameter
- β: Learnable shift parameter

This is: center → scale → rescale → shift
```

## BatchNorm

### Definition
```python
import torch.nn as nn
class BatchNorm1d(nn.Module):
    def __init__(self, num_features, eps=1e-5, momentum=0.1):
        super().__init__()
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum

        # Learnable parameters
        self.gamma = nn.Parameter(torch.ones(num_features))
        self.beta = nn.Parameter(torch.zeros(num_features))

        # Running statistics (not trainable)
        self.register_buffer('running_mean', torch.zeros(num_features))
        self.register_buffer('running_var', torch.ones(num_features))

    def forward(self, x):
        """
        x: (batch, channels, length) for 1D
           (batch, channels, height, width) for 2D
        """
        if self.training:
            # Compute statistics over batch and spatial dims
            dim = [0] + list(range(2, x.ndim))
            mean = x.mean(dim=dim, keepdim=True)
            var = x.var(dim=dim, keepdim=True)

            # Update running statistics
            with torch.no_grad():
                self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * mean.squeeze()
                self.running_var = (1 - self.momentum) * self.running_var + self.momentum * var.squeeze()
        else:
            # Use running statistics
            mean = self.running_mean.view(1, -1, *([1] * (x.ndim - 2)))
            var = self.running_var.view(1, -1, *([1] * (x.ndim - 2)))

        # Normalize
        x_norm = (x - mean) / torch.sqrt(var + self.eps)

        # Scale and shift
        return self.gamma * x_norm + self.beta
```

### BatchNorm Properties
```yaml
Normalization dimensions: Over batch and spatial
Statistics computed: (B, H, W) → single value per channel

Pros:
- Reduces internal covariate shift
- Allows higher learning rates
- Regularizing effect (noise from batch statistics)

Cons:
- Batch size dependent (bad for small batches)
- Not suitable for sequential data (variable lengths)
- Different behavior train vs test
- Not compatible with online learning
```

## LayerNorm

### Definition
```python
import torch.nn as nn
class LayerNorm(nn.Module):
    def __init__(self, normalized_shape, eps=1e-5):
        super().__init__()
        self.normalized_shape = normalized_shape
        self.eps = eps

        # Learnable parameters
        self.gamma = nn.Parameter(torch.ones(normalized_shape))
        self.beta = nn.Parameter(torch.zeros(normalized_shape))

    def forward(self, x):
        """
        x: (batch, seq_len, hidden_dim)
        normalized_shape: hidden_dim
        """
        # Compute mean and variance over feature dimension
        mean = x.mean(dim=-1, keepdim=True)  # (B, L, 1)
        var = x.var(dim=-1, keepdim=True)    # (B, L, 1)

        # Normalize
        x_norm = (x - mean) / torch.sqrt(var + self.eps)

        # Scale and shift
        return self.gamma * x_norm + self.beta
```

### LayerNorm in Transformers
```python
import torch.nn as nn
# Typical transformer block with LayerNorm
class TransformerBlock(nn.Module):
    def __init__(self, d_model=512):
        super().__init__()
        self.attn = MultiHeadAttention(d_model)
        self.ff = FeedForward(d_model)

        # Pre-LN (modern): Normalize before residual
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x):
        # Pre-LN architecture (used in GPT-2, LLaMA)
        x = x + self.attn(self.norm1(x))
        x = x + self.ff(self.norm2(x))
        return x

# Post-LN (original Transformer)
class PostLNTransformerBlock(nn.Module):
    def __init__(self, d_model=512):
        super().__init__()
        self.attn = MultiHeadAttention(d_model)
        self.ff = FeedForward(d_model)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x):
        # Post-LN: Normalize after residual
        x = self.norm1(x + self.attn(x))
        x = self.norm2(x + self.ff(x))
        return x
```

### Pre-LN vs Post-LN
```text
Post-LN (original):
  x = LayerNorm(x + Sublayer(x))
  - Gradient flow issues in deep networks
  - Requires warmup

Pre-LN (modern):
  x = x + Sublayer(LayerNorm(x))
  - Better gradient flow
  - More stable training
  - Used in: GPT-2, LLaMA, most modern models
```

## RMSNorm

### Definition
```python
import torch.nn as nn
class RMSNorm(nn.Module):
    """
    Root Mean Square Normalization
    Simplified LayerNorm: remove mean centering
    """
    def __init__(self, dim, eps=1e-8):
        super().__init__()
        self.eps = eps
        self.scale = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        """
        x: (batch, seq_len, hidden_dim)
        """
        # RMS: sqrt(mean(x²))
        rms = torch.sqrt(x.pow(2).mean(dim=-1, keepdim=True) + self.eps)

        # Normalize and scale
        return x / rms * self.scale
```

### Why RMSNorm Works
```text
LayerNorm:  (x - μ) / σ
RMSNorm:    x / RMS(x)

Difference: Remove mean centering (μ)
Result:     ~0.1-0.3% performance drop
            ~10-20% speedup (no mean computation)

Used in: Llama 2, Mistral, Gemma
```

### RMSNorm Implementation (LLaMA style)
```python
import torch.nn as nn
class LlamaRMSNorm(nn.Module):
    def __init__(self, hidden_size, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.variance_epsilon = eps

    def forward(self, hidden_states):
        """
        LLaMA uses 32-bit computation for accuracy
        """
        input_dtype = hidden_states.dtype
        hidden_states = hidden_states.to(torch.float32)

        # Compute RMS
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.variance_epsilon)

        # Return to original dtype
        return self.weight * hidden_states.to(input_dtype)
```

## Comparison

### Mathematical Comparison
```python
import torch.nn as nn
import torch
import matplotlib.pyplot as plt

def compare_normalizations():
    """
    Visualize different normalization behaviors
    """
    x = torch.randn(1, 100, 128)  # Batch, seq, hidden

    # Apply different normalizations
    bn_out = BatchNorm1d(128)(x)
    ln_out = nn.LayerNorm(128)(x)
    rms_out = RMSNorm(128)(x)

    # Compare statistics
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Feature dimension distribution
    axes[0].hist(bn_out.flatten().detach().numpy(), bins=50, alpha=0.5, label='BatchNorm')
    axes[0].hist(ln_out.flatten().detach().numpy(), bins=50, alpha=0.5, label='LayerNorm')
    axes[0].set_title('Output Distribution')
    axes[0].legend()

    # Mean across sequence
    axes[1].plot(ln_out[0, :, 0].detach().numpy(), label='LayerNorm')
    axes[1].plot(rms_out[0, :, 0].detach().numpy(), label='RMSNorm')
    axes[1].set_title('Sequence-wise Mean (dim 0)')
    axes[1].legend()

    # Variance across sequence
    axes[2].plot(ln_out[0, :, :].std(dim=-1).detach().numpy(), label='LayerNorm')
    axes[2].plot(rms_out[0, :, :].std(dim=-1).detach().numpy(), label='RMSNorm')
    axes[2].set_title('Sequence-wise Std (dim -1)')
    axes[2].legend()

    plt.show()

compare_normalizations()
```

### When to Use Which?

| Normalization | Use Case | Models |
|---------------|----------|--------|
| BatchNorm | CNNs, vision | ResNet, EfficientNet |
| LayerNorm | Transformers, NLP | BERT, GPT, T5 |
| RMSNorm | Efficient transformers | Llama 2, Mistral |
| GroupNorm | Small batch CNNs | Lightweight models |
| InstanceNorm | Style transfer | StyleGAN |

### Performance Impact
```text
In transformer training:

No Norm:       Unstable, NaNs
BatchNorm:     Sequence length issues
LayerNorm:     Standard, stable
RMSNorm:       +10% speed, -0.2% accuracy

Recommendation: RMSNorm for new models
```

## Implementation Tips

### Fused Operations
```python
import torch.nn as nn
# PyTorch has fused implementations
# Faster and more numerically stable

# Slow: manual implementation
def manual_layer_norm(x, gamma, beta, eps):
    mean = x.mean(-1, keepdim=True)
    std = x.std(-1, keepdim=True)
    return gamma * (x - mean) / (std + eps) + beta

# Fast: built-in (uses optimized kernels)
layer_norm = nn.LayerNorm(x.size(-1))
output = layer_norm(x)
```

### Mixed Precision
```python
import torch.nn as nn
# RMSNorm is more stable in mixed precision
# LayerNorm can have precision issues with fp16

class SafeLayerNorm(nn.Module):
    def __init__(self, dim, eps=1e-5):
        super().__init__()
        self.gamma = nn.Parameter(torch.ones(dim))
        self.beta = nn.Parameter(torch.zeros(dim))
        self.eps = eps

    def forward(self, x):
        # Cast to fp32 for statistics
        orig_dtype = x.dtype
        mean = x.mean(dim=-1, keepdim=True).float()
        var = x.var(dim=-1, keepdim=True, unbiased=False).float()

        # Normalize in fp32
        x_norm = (x.float() - mean) / torch.sqrt(var + self.eps)

        # Scale/shift in fp32, then cast back
        out = (self.gamma.float() * x_norm + self.beta.float()).to(orig_dtype)
        return out
```

## DeepNorm (Stable Deep Networks)

### DeepNorm Formula
```text
For very deep transformers (>24 layers):

DeepNorm:   y = Sublayer(LayerNorm(α×x + Sublayer(x))) / α²

Where α = (2N)^(1/2) for N layers

This stabilizes gradients in very deep networks
```

```python
import torch.nn as nn
class DeepNormTransformerBlock(nn.Module):
    """
    DeepNorm: Train 100+ layer transformers
    """
    def __init__(self, d_model, num_layers):
        super().__init__()
        self.alpha = (2 * num_layers) ** 0.5
        self.attn = MultiHeadAttention(d_model)
        self.ff = FeedForward(d_model)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x):
        # DeepNorm residual connection
        x = self.norm1(self.alpha * x + self.attn(x)) / (self.alpha ** 2)
        x = self.norm2(self.alpha * x + self.ff(x)) / (self.alpha ** 2)
        return x
```

---

## Summary

Normalization layers keep training stable by keeping activations in a sane range: without them, activations grow or shrink exponentially and gradients vanish or explode. In transformers the fight is between LayerNorm and RMSNorm - the latter drops mean-centering for speed and pairs with pre-norm placement in modern LLMs - while BatchNorm stays a CNN tool. This lesson covered why normalization is needed, the layer-by-layer mechanics, and the placement decisions. The rule it leaves: RMSNorm pre-norm is the modern LLM default, and the reason is stability per unit of compute.

## References

### Related Minder Academy Documents

- [3301: Activation Functions - GELU, SwiGLU, and Beyond](3301-Activation-Functions.md)

---

## Next Steps

- Next Module: **[3400: Architectures](../3400-architectures/)**
- Continue with: **[3401: Encoder-Decoder Architectures](../3400-architectures/3401-Encoder-Decoder-Architectures.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [3301: Activation Functions](./3301-Activation-Functions.md)
- [3101: Self-Attention](../3100-attention/3101-Self-Attention-DeepDive.md)
- [2202: TensorFlow XLA](../../phase2-foundations/2200-frameworks/2202-TensorFlow-XLA-Compilers.md)

