---
Document ID: 3301
Title: "3301: Activation Functions - GELU, SwiGLU, and Beyond"
Phase: 3
Module: 3300
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'activation', 'gelu', 'swiglu', 'normalization']
---

# 3301: Activation Functions - GELU, SwiGLU, and Beyond

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [From ReLU to Modern Activations](#from-relu-to-modern-activations)
- [GELU (Gaussian Error Linear Unit)](#gelu-gaussian-error-linear-unit)
- [SwiGLU (Swish-Gated Linear Unit)](#swiglu-swish-gated-linear-unit)
- [Comparison in Transformers](#comparison-in-transformers)
- [Other Activations](#other-activations)
- [Activation Function Properties](#activation-function-properties)
- [Choosing the Right Activation](#choosing-the-right-activation)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- List ReLU's three failure modes in transformers — dead neurons that block gradient flow, non-smoothness at x=0, non-zero-centered outputs causing zigzagging — and why each motivates a smooth replacement
- Derive exact GELU as x·Φ(x) via `torch.erf`, state the GPT-2 tanh approximation (√(2/π) scaling, 0.044715x³ term), and justify the ≈99.7%-correlation speed/accuracy trade-off
- Implement the SwiGLU FFN's three bias-free projections (`gate_proj`, `up_proj`, `down_proj`) with `silu(gate) * up` gating, including LLaMA's 8/3·d hidden-dim rule rounded to `multiple_of=256`
- Reconcile SwiGLU's 1.5x parameter count (3,145,728 vs 2,097,152 at d_model=512, d_ff=2048) against Shazeer's reported 1-2% perplexity gain for equal-compute comparisons
- Distinguish the gated variants by their gate function and chunking layout — GEGLU (BLOOM, GPT-NeoX), ReGLU — and keep them separate from MoE's routing gate: `topk` sparsity picks experts, it is not an activation
- Probe activations with the `analyze_activation` autograd-derivative harness (smoothness, monotonicity, sign, boundedness) and read the compute-vs-perplexity table to select per scenario: vanilla → GELU, LLM → SwiGLU, MoE → SwiGLU experts behind a top-k router

---

## Abstract
Activation functions introduce non-linearity into neural networks. Modern LLMs use specialized activations like GELU and SwiGLU that outperform traditional ReLU in transformer architectures.

## From ReLU to Modern Activations

### ReLU (Rectified Linear Unit)
```python
def relu(x):
    return max(0, x)

# PyTorch
import torch.nn as nn
relu = nn.ReLU()

# Properties:
# - Computationally cheap (comparison only)
# - No vanishing gradient for positive inputs
# - Dead neurons (gradient = 0 for negative inputs)
# - Non-zero centered (output always ≥ 0)
```

### ReLU Problems in Transformers
```text
1. Dead neurons:
   - If input is consistently negative, neuron never activates
   - Gradient flow is blocked

2. Non-smooth:
   - Discontinuity at x=0 causes optimization issues
   - Not suitable for attention score refinement

3. Not zero-centered:
   - Can cause zigzagging in gradient descent
```

## GELU (Gaussian Error Linear Unit)

### Definition
```text
GELU(x) = x × Φ(x)

Where Φ(x) is the cumulative distribution function
of the standard normal distribution:
Φ(x) = 0.5 × (1 + erf(x / √2))

erf is the error function
```

### Exact vs Approximate
```python
import torch
import math

def gelu_exact(x):
    """
    Exact GELU computation
    """
    return 0.5 * x * (1.0 + torch.erf(x / math.sqrt(2.0)))

def gelu_approx(x):
    """
    Approximation used in GPT-2 (faster)
    GELU(x) ≈ 0.5 × x × (1 + tanh(√(2/π) × (x + 0.044715 × x³)))
    """
    return 0.5 * x * (1.0 + torch.tanh(
        math.sqrt(2.0 / math.pi) * (x + 0.044715 * torch.pow(x, 3.0))
    ))

# PyTorch built-in
gelu = nn.GELU()

# Comparison:
# Exact: More accurate, slower
# Approx: 99.7% correlation, faster
```

### Why GELU Works Well
```text
1. Smooth everywhere:
   - No discontinuities
   - Better gradient flow

2. Self-gating:
   - Output depends on input magnitude
   - x is modulated by probability Φ(x)

3. Expected behavior:
   - Can be motivated by stochastic depth
   - Represents expected value of ReLU with noise
```

### Visualization
```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(-4, 4, 100)
relu = np.maximum(0, x)
# GPT-2 tanh approximation (np.erf does not exist in NumPy)
gelu = 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
plt.plot(x, relu, label='ReLU')
plt.title('ReLU')
plt.grid(True)

plt.subplot(1, 3, 2)
plt.plot(x, gelu, label='GELU')
plt.title('GELU')
plt.grid(True)

plt.subplot(1, 3, 3)
plt.plot(x, relu, label='ReLU')
plt.plot(x, gelu, label='GELU')
plt.title('Comparison')
plt.legend()
plt.grid(True)

plt.show()
```

## SwiGLU (Swish-Gated Linear Unit)

### Swish Activation
```python
def swish(x, beta=1.0):
    """
    Swish: x × sigmoid(βx)
    """
    return x * torch.sigmoid(beta * x)

# Properties:
# - Smooth
# - Non-monotonic (for β > 0, dips slightly below 0)
# - Self-gating like GELU
# - Outperforms ReLU in deep networks
```

### GLU (Gated Linear Unit)
```python
def glu(x, gate):
    """
    GLU: x × σ(gate)

    Commonly used in:
    - LSTMs (gates)
    - Convolutional networks
    """
    return x * torch.sigmoid(gate)

# Split input into two halves
def glu_from_single(x):
    """
    x: (batch, seq_len, 2 * hidden)
    Split into two and apply gating
    """
    a, b = x.chunk(2, dim=-1)
    return a * torch.sigmoid(b)
```

### SwiGLU (PaLM, LLaMA)
```python
def swiglu(x, W_gate, W_up, W_down):
    """
    SwiGLU activation in feed-forward network

    Architecture:
        x ──┬──► W_gate ──► SiLU ──┐
            │                     ×
            └──► W_up ────────────┘
                                 │
                                 ▼
                              W_down

    Used in: PaLM, LLaMA, Mistral
    """
    # Split into gate and up projections
    gate = torch.nn.functional.linear(x, W_gate)
    up = torch.nn.functional.linear(x, W_up)

    # SwiGLU activation
    output = torch.nn.functional.silu(gate) * up

    # Down projection
    output = torch.nn.functional.linear(output, W_down)

    return output

# In PyTorch module
class SwiGLUFFN(nn.Module):
    def __init__(self, dim, hidden_dim, multiple_of=256):
        super().__init__()
        # LLaMA formula: hidden_dim = int(2 * 4/3 * dim)
        hidden_dim = int(2 * hidden_dim / 3)
        hidden_dim = multiple_of * ((hidden_dim + multiple_of - 1) // multiple_of)

        self.gate_proj = nn.Linear(dim, hidden_dim, bias=False)
        self.up_proj = nn.Linear(dim, hidden_dim, bias=False)
        self.down_proj = nn.Linear(hidden_dim, dim, bias=False)

    def forward(self, x):
        return self.down_proj(
            torch.nn.functional.silu(self.gate_proj(x)) * self.up_proj(x)
        )
```

### Why SwiGLU Outperforms GELU
```text
Paper: "GLU Variants Improve Transformer" (Shazeer, 2020)

Key findings:
1. Gating mechanism allows more flexible transformations
2. SwiGLU ≈ GLU with SiLU activation
3. 1-2% improvement over GELU-FFN
4. Better gradient flow through gating
```

## Comparison in Transformers

### Standard FFN vs SwiGLU FFN
```python
# Standard FFN (GPT-2)
class StandardFFN(nn.Module):
    def __init__(self, d_model=512, d_ff=2048):
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)
        self.activation = nn.GELU()

    def forward(self, x):
        return self.fc2(self.activation(self.fc1(x)))

# SwiGLU FFN (LLaMA)
class SwiGLUFFN(nn.Module):
    def __init__(self, d_model=512, d_ff=2048):
        super().__init__()
        # Note: d_ff is typically different for SwiGLU
        self.gate = nn.Linear(d_model, d_ff, bias=False)
        self.up = nn.Linear(d_model, d_ff, bias=False)
        self.down = nn.Linear(d_ff, d_model, bias=False)

    def forward(self, x):
        return self.down(torch.nn.functional.silu(self.gate(x)) * self.up(x))

# Parameter comparison (d_model=512, d_ff=2048):
# Standard: 512×2048 + 2048×512 = 2,097,152
# SwiGLU:   3×512×2048 = 3,145,728 (1.5x parameters)
```

## Other Activations

### GEGLU (BLOOM, GPT-NeoX)
```python
def geglu(x):
    """
    Gated Exponential Linear Unit
    Used in: BLOOM, GPT-NeoX
    """
    a, b = x.chunk(2, dim=-1)
    return a * torch.nn.functional.gelu(b)

class GEGLUFFN(nn.Module):
    def __init__(self, d_model=512, d_ff=2048):
        super().__init__()
        # d_ff is split between gate and up
        self.gate_up = nn.Linear(d_model, 2 * d_ff, bias=False)
        self.down = nn.Linear(d_ff, d_model, bias=False)

    def forward(self, x):
        gate_up = self.gate_up(x)
        gate, up = gate_up.chunk(2, dim=-1)
        return self.down(torch.nn.functional.gelu(gate) * up)
```

### ReGLU
```python
def reglu(x):
    """
    ReLU Gated Linear Unit
    """
    a, b = x.chunk(2, dim=-1)
    return a * torch.nn.functional.relu(b)
```

### MoE Gating (Shazeer 2017 → Switch → Mixtral)

The MoE "gate" is a different animal from the GLU gates above: it is a
router that picks which expert FFN processes each token, not an
elementwise activation. Shazeer et al. (2017) — *Outrageously Large
Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer* — gave
each expert a GeLU FFN and sent each token to only its top-k experts
through a learned gate (their noise term is dropped here for clarity):

```python
import torch
import torch.nn.functional as F

def sparse_router(x, W_router, k=2):
    """
    x:        (batch, seq_len, d_model)  token hidden states
    W_router: (d_model, num_experts)     learned gate weights
    Returns per-token top-k expert weights, renormalized to sum to 1.
    """
    logits = x @ W_router                    # (batch, seq, num_experts)
    probs = torch.softmax(logits, dim=-1)
    topk_probs, topk_idx = torch.topk(probs, k=k, dim=-1)
    return topk_probs / topk_probs.sum(-1, keepdim=True), topk_idx

x = torch.randn(2, 5, 512)                   # batch 2, seq 5, d_model 512
W = torch.randn(512, 4)                      # 4 experts
probs, idx = sparse_router(x, W, k=2)
print(probs.shape, idx.shape)                # (2, 5, 2) (2, 5, 2)
```

The routing gate and the activation gate are two separate mechanisms —
keep them apart when reading MoE papers. The lineage simplified the
router while the experts' activation followed the same path as dense
models:

```text
2017  Shazeer et al.       sparsely-gated MoE   GeLU experts, noisy top-k gate
2021  Switch Transformer   (Fedus et al.)       top-1 routing, one expert/token
2024  Mixtral 8x7B         (Mistral)            SwiGLU experts, top-2 routing
```

There is no "SMGeLU" activation in the literature — the name conflates
the two gates. The sparsity lives in the router (softmax + top-k); the
activation lives inside each expert (GeLU then, SwiGLU now).

## Activation Function Properties

### Mathematical Properties
```python
# Compare activation properties
def analyze_activation(act_fn, name):
    """
    Analyze: smoothness, monotonicity, range
    """
    x = torch.linspace(-5, 5, 1000)
    y = act_fn(x)

    # Derivative
    grad = torch.autograd.grad(y.sum(), x, create_graph=True)[0]

    return {
        'name': name,
        'smooth': not torch.isnan(grad).any(),  # No discontinuities
        'monotonic': (grad >= 0).all().item(),  # Always increasing
        'negative_values': (y < 0).any().item(),  # Goes below zero
        'bounded': (y.abs() < 10).all().item(),  # Bounded range
    }

# Compare
activations = {
    'ReLU': lambda x: torch.maximum(x, torch.zeros_like(x)),
    'GELU': nn.GELU(),
    'Swish': lambda x: x * torch.sigmoid(x),
}

for name, fn in activations.items():
    props = analyze_activation(fn, name)
    print(props)
```

## Choosing the Right Activation

### Guidelines
```text
For vanilla transformer:           GELU or GeLU
For large language models:         SwiGLU (1.5% gain)
For MoE experts:                   SwiGLU + top-k router (Mixtral)
For limited compute:               ReLU or GELU
For best performance:              SwiGLU (if compute allows)
```

### Performance Trade-offs
```text
Activation    Compute  Memory    Perplexity
─────────────────────────────────────────────
ReLU          1x       1x        Baseline
GELU          1.2x     1x        -0.3
Swish         1.3x     1x        -0.5
SwiGLU        2x       1x        -0.8

All values relative to ReLU baseline
Negative perplexity = improvement
```

---

## Summary

Activation functions are where networks get their non-linearity, and the transformer generation moved on from ReLU: GELU's smooth gating replaced it in BERT and GPT-2, and SwiGLU's gated pairing became the LLM default. This lesson walked the ReLU-to-modern arc, the properties that matter (smoothness, dead-neuron behavior, cost), and where each function earns its place. The rule it leaves: the activation is a measured choice, not a default - GELU and SwiGLU win in transformers for reasons you can read off their curves, and the comparison guide makes those reasons concrete.

## References

### Related PROJECT-OMEGA Documents

- [3302: Normalization Layers - BatchNorm vs LayerNorm vs RMSNorm](3302-Normalization-Layers.md)

---

## Next Steps

- Continue with: **[3302: Normalization Layers](./3302-Normalization-Layers.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [3302: Normalization Layers](./3302-Normalization-Layers.md)
- [3101: Self-Attention](../3100-attention/3101-Self-Attention-DeepDive.md)
- [5101: LoRA Logic](../../phase5-finetuning/5100-peft/5101-LoRA-Logic.md)

