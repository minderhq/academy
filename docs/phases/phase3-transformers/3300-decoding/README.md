# [3300]: The Decoding Block

## Overview

This module covers the feed-forward networks, activation functions, and normalization layers that process the attended representations in Transformers. These components are crucial for model stability, training speed, and final performance.

---

## Module Documents

| Document | Description | Difficulty | Time |
|----------|-------------|------------|------|
| [3301: Activation Functions](./3301-Activation-Functions.md) | Why GELU and SwiGLU over RELU? | ⭐⭐ | 2 hrs |
| [3302: Normalization Layers](./3302-Normalization-Layers.md) | BatchNorm vs LayerNorm vs RMSNorm | ⭐⭐ | 2 hrs |
| [3303: Activation Function Comparison](./guides/3303-Activation-Function-Comparison.md) | Comparative analysis with benchmarks | ⭐⭐⭐ | 3 hrs |

---

## Learning Objectives

After completing this module, you will:
- ✅ Understand the role of activation functions in Transformers
- ✅ Compare ReLU, GELU, Swish, and SwiGLU
- ✅ Explain why LLMs use specific activation functions
- ✅ Understand normalization strategies and their impact
- ✅ Compare LayerNorm, RMSNorm, and BatchNorm
- ✅ Implement efficient activation and normalization layers

---

## Prerequisites

- **Math:** Calculus (gradients), statistics (mean, variance)
- **Programming:** PyTorch, automatic differentiation
- **Previous:** [3100: Attention](../3100-attention/), [3200: Embeddings](../3200-embeddings/)

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

---

## Key Concepts

### The Transformer Feed-Forward Block

```text
Input (from attention)
    ↓
LayerNorm
    ↓
Linear → Activation → Linear
    ↓
Residual Connection
    ↓
Output
```

### Activation Functions

| Function | Formula | Properties | Use in LLMs |
|----------|---------|------------|-------------|
| **ReLU** | `max(0, x)` | Simple, non-saturating | Rare (dead neurons) |
| **GELU** | `x * Φ(x)` | Smooth, probabilistic | Common (BERT, GPT-2) |
| **Swish** | `x * σ(βx)` | Smooth, self-gated | Some models |
| **SwiGLU** | `Swish(xW) ⊗ (xV)` | Gated, very effective | State-of-the-art (LLaMA) |

### Normalization Layers

| Type | Normalization Axis | Parameters | Use in LLMs |
|------|-------------------|------------|-------------|
| **BatchNorm** | Batch | γ, β per channel | Rare (sequence dependent) |
| **LayerNorm** | Feature | γ, β per feature | Standard (GPT, BERT) |
| **RMSNorm** | Feature | γ only | Modern (LLaMA, Mistral) |

---

## Why GELU and SwiGLU?

### The Problem with ReLU

```text
ReLU(x) = max(0, x)

Issues:
1. Dead neurons: Once negative, never recovers
2. Non-smooth: Discontinuity at 0 hurts optimization
3. Zero-centered: All positive outputs cause bias shift
```

### GELU: Smooth Approximation

```yaml
GELU(x) = x * Φ(x)
         ≈ 0.5 * x * (1 + tanh(√(2/π) * (x + 0.044715x³)))

Where Φ(x) is the standard normal CDF

Advantages:
- Smooth everywhere
- Probabilistic interpretation
- Better gradient flow
- Proven in BERT, GPT-2
```

### SwiGLU: Gated Linear Units

```yaml
SwiGLU(x) = Swish(xW) ⊗ (xV)
          = (xW * σ(xW)) ⊗ (xV)

Where ⊗ is element-wise multiplication

Advantages:
- Gating mechanism learns what to pass
- More parameters (better capacity)
- State-of-the-art in LLaMA, PaLM
- 2-3x parameters in FFN layer
```

---

## Normalization: Why and Where?

### The Normalization Problem

```text
Without normalization:
- Gradients can explode/vanish
- Training becomes unstable
- Learning rate must be very small
- Convergence is slow
```

### LayerNorm vs RMSNorm

**LayerNorm:**
```python
output = γ * (x - μ) / √(σ² + ε) + β
```

**RMSNorm (simpler, faster):**
```python
output = γ * x / RMS(x)  # No β, no mean centering
RMS(x) = √(mean(x²) + ε)
```

**Why RMSNorm?**
- Faster (no mean computation)
- Fewer parameters (no β)
- Similar performance
- Used in LLaMA, Mistral

---

## Transformer Block Comparison

### GPT-2 Style

```text
x = x + MultiHeadAttention(LayerNorm(x))
x = x + FFN(LayerNorm(x))

Activation: GELU
Normalization: LayerNorm (post-norm)
```

### LLaMA Style

```text
x = x + RMSNorm(FFN(RMSNorm(Attention(x))))
    (Pre-norm architecture)

Activation: SwiGLU
Normalization: RMSNorm (pre-norm)
```

---

## Implementation Example

### SwiGLU Implementation

```python
class SwiGLU(nn.Module):
    """
    SwiGLU activation function.
    Used in LLaMA, Mistral, and other modern LLMs.
    """
    def __init__(self, d_model, d_ff=None):
        super().__init__()
        if d_ff is None:
            d_ff = 4 * d_model  # Standard expansion

        # SwiGLU uses 3x weights instead of 2x
        self.gate = nn.Linear(d_model, d_ff, bias=False)
        self.value = nn.Linear(d_model, d_ff, bias=False)
        self.output = nn.Linear(d_ff, d_model, bias=False)

    def forward(self, x):
        """
        Args:
            x: (batch, seq_len, d_model)

        Returns:
            output: (batch, seq_len, d_model)
        """
        # Compute gate and value
        gate = F.silu(self.gate(x))  # SiLU = Swish β=1
        value = self.value(x)

        # Element-wise multiplication (gating)
        x = gate * value

        # Project back to d_model
        return self.output(x)
```

### RMSNorm Implementation

```python
class RMSNorm(nn.Module):
    """
    Root Mean Square Layer Normalization.
    Simplified LayerNorm without mean centering.
    """
    def __init__(self, d_model, eps=1e-8):
        super().__init__()
        self.eps = eps
        self.scale = nn.Parameter(torch.ones(d_model))

    def forward(self, x):
        """
        Args:
            x: (batch, seq_len, d_model)

        Returns:
            normalized: (batch, seq_len, d_model)
        """
        # Compute RMS: (batch, seq_len, 1)
        rms = torch.sqrt(torch.mean(x.square(), dim=-1, keepdim=True) + self.eps)

        # Normalize and scale
        return x / rms * self.scale
```

---

## Related Experiments

| Experiment | Description |
|------------|-------------|

---

## Assessment

- **Quiz:** [assessment/QUIZ.md](assessment/QUIZ.md) - Test your decoding knowledge
- **Practice:** [assessment/PRACTICE.md](assessment/PRACTICE.md) - Implement activation functions

---

## See Also

- **Previous Module:** [3200: Embedding Latent Spaces](../3200-embeddings/)
- **Next Module:** [3400: Model Architectures](../3400-architectures/) - Encoder-Decoder vs Decoder-only
- **Guide:** [3303: Activation Function Comparison](./guides/3303-Activation-Function-Comparison.md)
- **Phase Overview:** [Phase 3 README](../README.md)

---

## Common Issues

| Issue | Solution |
|-------|----------|
| **Training instability** | Use pre-norm architecture (norm before attention/FFN) |
| **Slow convergence** | Try SwiGLU instead of GELU |
| **Gradient explosion** | Add gradient clipping or use RMSNorm |

---

## Quick Reference

### Activation Function Selection

| Model Size | Recommended Activation | Reason |
|------------|------------------------|--------|
| < 1B params | GELU | Good enough, faster |
| 1B - 10B | SwiGLU | Better performance |
| > 10B | SwiGLU | State-of-the-art |

### Normalization Selection

| Architecture | Recommended Norm | Reason |
|--------------|------------------|--------|
| Pre-norm | RMSNorm | Faster, fewer params |
| Post-norm | LayerNorm | More stable |
| Training deep models | Pre-norm + RMSNorm | Best stability |

---

**Status:** ✅ Complete
**Last Updated:** 2026-02-05
**Module Difficulty:** ⭐⭐ Beginner-Intermediate
**Estimated Time:** 7 hours total
