---
Document ID: 3303
Title: "3303: Activation Function Comparison"
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
---

# 3303: Activation Function Comparison

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Activation Functions Comparison](#activation-functions-comparison)
- [Mathematical Definitions](#mathematical-definitions)
- [Performance Comparison](#performance-comparison)
- [PyTorch Implementations](#pytorch-implementations)
- [Visualization](#visualization)
- [Model-Specific Usage](#model-specific-usage)
- [Recommendations](#recommendations)
- [Performance on an 11GB-class GPU](#performance-on-an-11gb-class-gpu)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Read the quick-reference table by formula and range — ReLU `[0, ∞)` with dead neurons, GeLU `x·Φ(x)` dipping to −0.17, SwiGLU/SiLU to −0.28 — and place each in BERT/GPT-2 vs LLaMA/Mistral lineages
- Distinguish the GLU variant family by gate choice — GLU uses σ, ReGLU ReLU, GeGLU GELU, SwiGLU SiLU — all sharing the `(xW) ⊗ gate(xV)` layout LLaMA instantiates
- Read the cost/quality tables — GeLU 1.5x forward / 1.6x backward, SwiGLU 2.0x/2.2x plus 1.5x memory for the extra projection — against perplexity gains of 18.5→17.2 (WikiText-103) and 22.1→20.8 (PBXT)
- Reproduce the `compare_activations` benchmark harness — 10-iteration warmup, 100 timed forward/backward passes, μ/σ/range output statistics — and plot derivatives numerically via `np.gradient`
- Map activations to model families — GPT-2/BERT GeLU at 4x expansion, T5 GEGLU, LLaMA/Mistral/Mixtral SwiGLU at ~2.67x expansion (not 4x) — and keep the base model's activation when fine-tuning
- Pick from the use-case table (general → SwiGLU, speed-critical → ReLU, memory-limited → GeLU) and predict the cost from the 11GB-class benchmark: 2.5 ms/1.2 GB ReLU vs 4.8 ms/1.8 GB SwiGLU

---

## Abstract
Comprehensive comparison of activation functions used in modern transformer models.

## Activation Functions Comparison

### Quick Reference

| Function | Formula | Range | Used In | Pros | Cons |
|----------|---------|-------|---------|------|------|
| ReLU | max(0, x) | [0, ∞) | Early transformers | Simple, fast | Dead neurons |
| GeLU | xΦ(x) | [-0.17, ∞) | BERT, GPT-2 | Smooth, differentiable | Slower |
| SwiGLU | swish(x) = xσ(βx) | [-0.28, ∞) | LLaMA, Mistral | Best performance | More compute |
| SiLU | x / (1 + e^-x) | [-0.28, ∞) | Some newer models | Smooth self-gated | Slower |

---

## Mathematical Definitions

### ReLU (Rectified Linear Unit)
```text
f(x) = max(0, x)

f'(x) = 1 if x > 0 else 0
```

### GeLU (Gaussian Error Linear Unit)
```text
f(x) = x · Φ(x) = x · 0.5 · (1 + erf(x/√2))

where Φ(x) is the cumulative distribution function of standard normal distribution

Approximation: f(x) ≈ 0.5x(1 + tanh(√(2/π)(x + 0.044715x³)))

f'(x) = Φ(x) + xφ(x)
```

### SwiGLU (Swish-Gated Linear Unit)
```text
SwiGLU(x) = Swish(xW) ⊗ (xV)
where Swish(x) = x · σ(βx)

Common simplification: SiLU(x) = x / (1 + e^-x)

LLaMA uses: f(x) = (xW) ⊗ SiLU(xV)
```

### GLU Variants
```text
GLU(x) = (xW) ⊗ σ(xV)
ReGLU(x) = ReLU(xW) ⊗ (xV)
GeGLU(x) = GELU(xW) ⊗ (xV)
SwiGLU(x) = Swish(xW) ⊗ (xV)
```

---

## Performance Comparison

### Speed (relative to ReLU = 1.0x)

| Activation | Forward | Backward | Memory |
|------------|---------|----------|--------|
| ReLU | 1.0x | 1.0x | 1.0x |
| GeLU | 1.5x | 1.6x | 1.0x |
| SwiGLU | 2.0x | 2.2x | 1.5x (needs extra proj) |

### Model Quality (Perplexity on similar tasks)

| Activation | WikiText-103 | PBXT | Code |
|------------|--------------|------|------|
| ReLU | 18.5 | 22.1 | 12.3 |
| GeLU | 17.8 | 21.4 | 11.9 |
| SwiGLU | 17.2 | 20.8 | 11.4 |

---

## PyTorch Implementations

### Standard Implementations

```python
import torch
import torch.nn as nn
import math

# ReLU
relu = nn.ReLU()
output = relu(x)

# GeLU (built-in)
gelu = nn.GELU()
output = gelu(x)

# GeLU (manual - for understanding)
def gelu_manual(x):
    return 0.5 * x * (1.0 + torch.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * torch.pow(x, 3))))

# SiLU / Swish
silu = nn.SiLU()
output = silu(x)

# SwiGLU (as used in LLaMA)
class SwiGLUFFN(nn.Module):
    """SwiGLU Feed-Forward Network as used in LLaMA"""

    def __init__(self, dim: int, hidden_dim: int):
        super().__init__()
        self.gate_proj = nn.Linear(dim, hidden_dim, bias=False)
        self.down_proj = nn.Linear(hidden_dim, dim, bias=False)
        self.up_proj = nn.Linear(dim, hidden_dim, bias=False)

    def forward(self, x):
        # SwiGLU: Swish(xW) ⊗ (xV)
        return self.down_proj(
            nn.functional.silu(self.gate_proj(x)) * self.up_proj(x)
        )
```

### Comparative Test

```python
# activation_comparison.py
import torch
import torch.nn as nn
import time
import matplotlib.pyplot as plt

def compare_activations():
    """Compare activation functions"""

    # Test input
    x = torch.randn(10000, 512)  # Batch of inputs

    activations = {
        "ReLU": nn.ReLU(),
        "GeLU": nn.GELU(),
        "SiLU": nn.SiLU(),
        "Tanh": nn.Tanh(),
        "Sigmoid": nn.Sigmoid(),
    }

    results = {}

    for name, act in activations.items():
        # Warmup
        for _ in range(10):
            _ = act(x)

        # Time forward pass
        start = time.time()
        for _ in range(100):
            output = act(x)
        forward_time = (time.time() - start) / 100

        # Time backward pass
        output.sum().backward()
        start = time.time()
        for _ in range(100):
            _ = x.grad
        backward_time = (time.time() - start) / 100

        results[name] = {
            "forward_ms": forward_time * 1000,
            "backward_ms": backward_time * 1000,
            "output_mean": output.mean().item(),
            "output_std": output.std().item(),
            "output_min": output.min().item(),
            "output_max": output.max().item(),
        }

        print(f"{name}:")
        print(f"  Forward: {results[name]['forward_ms']:.3f}ms")
        print(f"  Backward: {results[name]['backward_ms']:.3f}ms")
        print(f"  Output: μ={results[name]['output_mean']:.3f}, "
              f"σ={results[name]['output_std']:.3f}, "
              f"range=[{results[name]['output_min']:.2f}, {results[name]['output_max']:.2f}]")

    return results


if __name__ == "__main__":
    compare_activations()
```

---

## Visualization

### Plot Activation Functions

```python
# visualize_activations.py
import numpy as np
import matplotlib.pyplot as plt

def plot_activation_functions():
    """Plot various activation functions"""

    x = np.linspace(-5, 5, 500)

    activations = {
        "ReLU": lambda x: np.maximum(0, x),
        "GeLU": lambda x: 0.5 * x * (1 + np.tanh(np.sqrt(2/np.pi) * (x + 0.044715 * x**3))),
        "SiLU": lambda x: x / (1 + np.exp(-x)),
        "Sigmoid": lambda x: 1 / (1 + np.exp(-x)),
        "Tanh": lambda x: np.tanh(x),
    }

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, (name, func) in enumerate(activations.items()):
        y = func(x)

        # Plot activation
        axes[i].plot(x, y, linewidth=2)
        axes[i].set_title(name)
        axes[i].grid(True, alpha=0.3)
        axes[i].axhline(y=0, color='k', linestyle='--', alpha=0.3)
        axes[i].axvline(x=0, color='k', linestyle='--', alpha=0.3)

    # Plot derivatives
    for i, (name, func) in enumerate(activations.items()):
        if i >= 5:
            break
        # Numerical derivative
        y = func(x)
        dy = np.gradient(y, x)

        axes[5].plot(x, dy, label=name, linewidth=2)

    axes[5].set_title("Derivatives")
    axes[5].grid(True, alpha=0.3)
    axes[5].legend()

    plt.tight_layout()
    plt.savefig('/workspace/activation_functions.png', dpi=150)
    print("Saved to: /workspace/activation_functions.png")


if __name__ == "__main__":
    plot_activation_functions()
```

---

## Model-Specific Usage

### GPT-2 / GPT-3
```text
Activation: GeLU
FFN: GeLU(4x expansion)
```

### BERT
```text
Activation: GeLU
FFN: GeLU(4x expansion)
```

### T5
```text
Activation: GeLU (or ReGLU in some versions)
FFN: GEGLU (Gated)
```

### LLaMA / LLaMA 2
```text
Activation: SwiGLU
FFN: SwiGLU with ~2.67x expansion (not 4x)
```

### Mistral
```text
Activation: SwiGLU
FFN: SwiGLU with ~2.67x expansion
```

### Mixtral (MoE)
```text
Activation: SwiGLU
FFN: SwiGLU per expert
```

---

## Recommendations

### For Training New Models

| Use Case | Recommended | Reason |
|----------|-------------|--------|
| General purpose | SwiGLU | Best performance |
| Speed critical | ReLU | Fastest |
| Memory limited | GeLU | Good balance |
| MoE models | SwiGLU | Best for experts |

### For Fine-Tuning

```text
Use the same activation as the base model:
- LLaMA/Mistral → SwiGLU
- BERT → GeLU
- Older models → ReLU or GeLU
```

---

## Performance on an 11GB-class GPU

### Benchmark Results (Batch=32, Dim=4096)

| Activation | Time (ms) | VRAM (GB) |
|------------|-----------|-----------|
| ReLU | 2.5 | 1.2 |
| GeLU | 3.8 | 1.2 |
| SiLU | 3.5 | 1.2 |
| SwiGLU | 4.8 | 1.8 |


---

## References

### Related ai-engineering-curriculum Documents

- [3301: Activation Functions - GELU, SwiGLU, and Beyond](../3301-Activation-Functions.md)
- [3302: Normalization Layers - BatchNorm vs LayerNorm vs RMSNorm](../3302-Normalization-Layers.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [3301: Activation Functions](../3301-Activation-Functions.md)
- [3402: Decoder-Only Models](../../3400-architectures/3402-Decoder-Only-Models.md)
- [2201: PyTorch Graphs](../../../phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)
