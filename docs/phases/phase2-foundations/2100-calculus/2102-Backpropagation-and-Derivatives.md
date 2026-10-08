---
Document ID: 2102
Title: "2102: Backpropagation and Automatic Differentiation"
Phase: 2
Module: 2100
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['math', 'calculus', 'tensors', 'backpropagation']
---

# 2102: Backpropagation and Automatic Differentiation

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Chain Rule](#the-chain-rule)
- [Computational Graphs](#computational-graphs)
- [Automatic Differentiation (Autograd)](#automatic-differentiation-autograd)
- [Backpropagation Algorithm](#backpropagation-algorithm)
- [Common Gradient Patterns](#common-gradient-patterns)
- [Vanishing and Exploding Gradients](#vanishing-and-exploding-gradients)
- [Computational Graph Visualization](#computational-graph-visualization)
- [Second-Order Derivatives (Hessian)](#second-order-derivatives-hessian)
- [Gradient Accumulation](#gradient-accumulation)
- [Best Practices](#best-practices)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Apply the chain rule by hand to a composed function and predict the backward result of the x → +1 → ×2 → ² → −4 graph before calling `backward()`
- Trace a PyTorch autograd DAG through `grad_fn`/`is_leaf` and explain how gradients accumulate along the reverse topological order
- Derive ∂L/∂W and ∂L/∂b for a sigmoid layer with MSE loss and match each factor of the chain rule to autograd's output
- Reproduce the linear, ReLU, and softmax+cross-entropy backward formulas and state why `softmax − one_hot` is the numerically stable form
- Diagnose vanishing gradients via the (0.25)ⁿ sigmoid bound and exploding gradients via NaN/Inf, then fix each with initialization, normalization, residual connections, clipping, or checkpointing
- Train under limited GPU memory with gradient accumulation (loss normalization, step/zero_grad cadence) and compute full Hessians with `create_graph=True`

---

## Abstract
Backpropagation is the algorithm that enables neural networks to learn. It computes gradients of the loss function with respect to all parameters by applying the chain rule of calculus recursively through the computational graph.

## The Chain Rule

### Single Variable Chain Rule
```text
If y = f(g(x)), then:
dy/dx = f'(g(x)) × g'(x)

Example:
y = sin(x²)
dy/dx = cos(x²) × 2x
```

### Multivariate Chain Rule (for Tensors)
```text
If y = f(x₁, x₂, ..., xₙ), then:
∂y/∂x₁, ∂y/∂x₂, ..., ∂y/∂xₙ

Gradient: ∇ᵧ = [∂y/∂x₁, ∂y/∂x₂, ..., ∂y/∂xₙ]
```

## Computational Graphs

### Forward Pass (Building the Graph)
```python
import torch

# Define computation
x = torch.tensor(2.0, requires_grad=True)
a = x + 1      # a = 3
b = a * 2      # b = 6
c = b ** 2     # c = 36
y = c - 4      # y = 32

# Computational graph:
# x → a → b → c → y
#     ↑   ↑   ↑   ↑
#    +1  ×2  ^2  -4
```

### Backward Pass (Computing Gradients)
```python
# Compute gradients
y.backward()

# dy/dx at x = 2
print(x.grad)  # tensor(24.)

# Manual calculation:
# y = ((x + 1) × 2)² - 4
# dy/dx = 2((x+1)×2) × 2 = 4(x+1)×2 = 8(x+1)
# At x = 2: 8(3) = 24 ✓
```

## Automatic Differentiation (Autograd)

### How PyTorch Autograd Works
```text
1. Forward pass:
   - Record operations in a DAG (Directed Acyclic Graph)
   - Store the "how to compute gradient" function

2. Backward pass:
   - Traverse graph in reverse (topological sort)
   - Apply chain rule at each node
   - Accumulate gradients

Graph Structure:
┌─────────────────────────────────────────────┐
│              Computational Graph             │
├─────────────────────────────────────────────┤
│                                             │
│   x ───► (+) ───► (×) ───► (^2) ───► (-)    │
│   │       │        │        │        │      │
│   │       1        2        ┆        4      │
│   │       │        │        │        │      │
│   └───────┴────────┴────────┴────┬──────┘   │
│                                    │         │
│                              [grad_fn]       │
│         Builds up during forward pass        │
└─────────────────────────────────────────────┘
```

### Autograd Implementation Details
```python
import torch

# Example:
x = torch.tensor(2.0, requires_grad=True)
y = x ** 2
z = 2 * y

# Each tensor has:
print(x.requires_grad)   # True (need gradient?)
print(x.grad)            # None (accumulated gradient, filled by backward())
print(x.grad_fn)         # None (function that created this tensor; leaves have none)
print(x.is_leaf)         # True (leaf node, user-created)

print(y.grad_fn)         # <PowBackward0 object at 0x...>
print(z.grad_fn)         # <MulBackward0 object at 0x...>
```

## Backpropagation Algorithm

### Step-by-Step Example
```python
import torch

# Define a simple neural network layer
x = torch.tensor([1.0, 2.0], requires_grad=False)
W = torch.tensor([[0.5, 0.5], [0.5, 0.5]], requires_grad=True)
b = torch.tensor([0.1, 0.1], requires_grad=True)
y_true = torch.tensor([1.0, 0.0])

# Forward pass
h = x @ W.t() + b      # Linear: h = xW^T + b
y_pred = torch.sigmoid(h)  # Activation: y = σ(h)

# Loss: MSE
loss = ((y_pred - y_true) ** 2).mean()

print(f"Loss: {loss.item()}")

# Backward pass
loss.backward()

# Gradients
print(f"dL/dW:\n{W.grad}")
print(f"dL/db:\n{b.grad}")
```

### Mathematical Derivation
```text
Given:
  h = xW^T + b
  ŷ = σ(h)
  L = MSE(ŷ, y) = (1/n) Σ(ŷᵢ - yᵢ)²

Derivative of MSE:
  ∂L/∂ŷ = 2(ŷ - y)/n

Derivative of sigmoid:
  dσ/dz = σ(z)(1 - σ(z))

Chain rule for W:
  ∂L/∂W = ∂L/∂ŷ × ∂ŷ/∂h × ∂h/∂W
        = 2(ŷ - y)/n × σ(h)(1 - σ(h)) × x

Chain rule for b:
  ∂L/∂b = ∂L/∂ŷ × ∂ŷ/∂h × ∂h/∂b
        = 2(ŷ - y)/n × σ(h)(1 - σ(h)) × 1
```

## Common Gradient Patterns

### Linear Layer Gradient
```python
# Forward: y = xW^T + b
# ∂L/∂W = x^T @ ∂L/∂y
# ∂L/∂b = sum(∂L/∂y, dim=0)

def linear_backward(grad_output, x, W):
    """
    grad_output: (batch, out_features)
    x: (batch, in_features)
    W: (out_features, in_features)
    """
    grad_W = torch.einsum('bi,bj->ji', x, grad_output)
    grad_b = grad_output.sum(dim=0)
    grad_input = torch.einsum('bo,oi->bi', grad_output, W)  # grad_output @ W

    return grad_input, grad_W, grad_b
```

### ReLU Gradient
```python
# Forward: y = max(0, x)
# ∂L/∂x = ∂L/∂y if x > 0 else 0

def relu_backward(grad_output, x):
    grad_input = grad_output * (x > 0).float()
    return grad_input
```

### Softmax + Cross Entropy Gradient
```python
# Combined gradient (numerically stable)
# ∂L/∂logits = softmax(logits) - one_hot(labels)

def softmax_ce_backward(logits, targets):
    """
    logits: (batch, num_classes)
    targets: (batch,) - class indices
    """
    probs = torch.softmax(logits, dim=-1)
    one_hot = torch.zeros_like(probs)
    one_hot[range(len(targets)), targets] = 1

    grad_input = probs - one_hot
    grad_input = grad_input / len(targets)  # Average over batch

    return grad_input
```

## Vanishing and Exploding Gradients

### Vanishing Gradient Problem
```text
In deep networks, repeated multiplication of small gradients:
∂L/∂x₁ = ∂L/∂xₙ × ∂xₙ/∂xₙ₋₁ × ... × ∂x₂/∂x₁

If each |∂xᵢ₊₁/∂xᵢ| < 1, gradient → 0

Example with sigmoid:
  σ'(z) = σ(z)(1 - σ(z)) ≤ 0.25

  After n layers: (0.25)^n → 0
```

### Vanishing Gradient Solutions
```python
import torch
import torch.nn as nn

# 1. ReLU activation (gradient = 1 for positive)
torch.nn.ReLU()

# 2. Proper initialization (Xavier/He)
W = torch.empty(64, 64)
torch.nn.init.xavier_uniform_(W)
torch.nn.init.kaiming_normal_(W, mode='fan_in')

# 3. Batch normalization
torch.nn.BatchNorm1d(64)

# 4. Residual connections (skip connections)
class ResidualBlock(nn.Module):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def forward(self, x):
        return self.fn(x) + x  # Gradient flows directly!
```

### Exploding Gradient Problem
```text
If gradients grow too large:
  Weights updated too aggressively
  Optimization diverges

Detection: NaN or Inf in gradients
```

### Exploding Gradient Solutions
```python
import torch

model = torch.nn.Linear(16, 4)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)

# 1. Gradient clipping
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

# 2. Lower learning rate (see optimizer above)

# 3. Gradient checkpointing (trade compute for memory)
from torch.utils.checkpoint import checkpoint

def my_expensive_function(x):
    return torch.relu(x) ** 2

x = torch.randn(8, 16, requires_grad=True)
output = checkpoint(my_expensive_function, x, use_reentrant=False)
```

## Computational Graph Visualization

### Using torchviz
```python
# torchviz is a third-party package: uv pip install torchviz (requires graphviz)
# https://github.com/szagoruyko/pytorchviz
import torch
from torchviz import make_dot

x = torch.randn(2, requires_grad=True)
y = x ** 2 + 3 * x + 1
y.sum().backward()

# Visualize graph
make_dot(y, params=dict(x=x)).render("graph", format="png")
```

### Reading the Graph
```text
Each node shows:
  - Operation name (e.g., AddBackward0)
  - Gradient shape
  - Connected nodes (dependencies)

Graph structure helps with:
  - Debugging gradient flow
  - Understanding memory usage
  - Optimizing computation
```

## Second-Order Derivatives (Hessian)

### Computing Hessian
```python
import torch

x = torch.tensor([2.0, 3.0], requires_grad=True)
y = x[0] ** 2 + x[1] ** 3

# First derivatives
grad = torch.autograd.grad(y, x, create_graph=True)[0]  # [4, 27]

# Second derivatives (Hessian diagonal)
hessian_diag = torch.autograd.grad(grad.sum(), x)[0]
# = [2, 6*x[1]] at x=[2, 3] = [2, 18]

# Full Hessian matrix (row i = gradient of grad[i] w.r.t. x)
def hessian(y, x):
    """Compute full Hessian matrix"""
    grad = torch.autograd.grad(y, x, create_graph=True)[0]
    H = torch.zeros(len(x), len(x))

    for i in range(len(x)):
        grad2 = torch.autograd.grad(grad[i], x, retain_graph=True)[0]
        H[i] = grad2

    return H

print(hessian(y, x))  # tensor([[2., 0.], [0., 18.]])
```

### Applications
```text
Hessian applications:
  - Newton's method optimization
  - Uncertainty estimation
  - Network pruning
  - Sharpness of minima analysis
```

## Gradient Accumulation

### Why Accumulate Gradients?
```text
When GPU memory is limited:
  - Can't fit large batch
  - Accumulate gradients over smaller batches
  - Update weights after accumulation

Example:
  Desired batch size: 256
  GPU can fit: 64
  Accumulate 4 times → 256 equivalent
```

### Implementation
```python
import torch
import torch.nn.functional as F

model = torch.nn.Linear(768, 10).cuda()
optimizer = torch.optim.Adam(model.parameters())

accumulation_steps = 4

# Toy DataLoader stand-in: 8 batches of (data, target)
dataloader = [(torch.randn(32, 768), torch.randint(0, 10, (32,))) for _ in range(8)]

for i, (data, target) in enumerate(dataloader):
    data, target = data.cuda(), target.cuda()

    output = model(data)
    loss = F.cross_entropy(output, target)

    # Normalize loss for accumulation
    loss = loss / accumulation_steps

    loss.backward()  # Accumulate gradients

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()  # Update weights
        optimizer.zero_grad()  # Reset gradients

# 8 batches / 4 accumulation steps = 2 optimizer steps
```

## Best Practices

### 1. Gradient Zeroing
```python
import torch

model = torch.nn.Linear(4, 2)
optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

# Always zero gradients before backward
optimizer.zero_grad()
# or
model.zero_grad()

# Common bug: Forgetting to zero!
# Gradients accumulate across batches
```

### 2. Disable Gradients for Inference
```python
import torch

model = torch.nn.Linear(4, 2)

# Saves memory and computation
with torch.no_grad():
    output = model(torch.randn(3, 4))

# eval mode additionally disables dropout / BatchNorm running-stats updates
model.eval()
with torch.no_grad():
    for batch in [torch.randn(3, 4) for _ in range(2)]:
        output = model(batch)

model.train()  # Back to training mode
```

### 3. Gradient Checkpointing
```python
# For very deep models or long sequences
import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint

class DeepModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(64, 64)
        self.layer2 = nn.Linear(64, 64)
        self.layer3 = nn.Linear(64, 64)

    def forward(self, x):
        # Checkpoint middle layers.
        # use_reentrant=False is required: with the default (True) and an
        # input that doesn't require grad, backward() fails with
        # "element 0 of tensors does not require grad" (torch 2.12)
        x = checkpoint(self.layer1, x, use_reentrant=False)
        x = checkpoint(self.layer2, x, use_reentrant=False)
        x = checkpoint(self.layer3, x, use_reentrant=False)
        return x

# Trade-off: More compute, less memory
```

---

## Summary

Backpropagation is the algorithm that makes networks learn: apply the chain rule recursively through the computational graph to get the gradient of the loss with respect to every parameter. This lesson built it from first principles - the single-variable chain rule, then the multivariate tensor form with Jacobians - and walked the mechanics autograd performs behind every .backward() call. The rule it leaves: gradients are not magic, they are bookkeeping; when training misbehaves, the person who can trace the chain rule by hand is the one who finds where it breaks.

## References

### Related Documents

- [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md)

### External References

- [torch.autograd — PyTorch documentation](https://docs.pytorch.org/docs/2.14/autograd.html)
- [torch.autograd.grad — PyTorch documentation](https://docs.pytorch.org/docs/2.14/generated/torch.autograd.grad.html)
- [torch.nn.utils.clip_grad_norm_ — PyTorch documentation](https://docs.pytorch.org/docs/2.14/generated/torch.nn.utils.clip_grad_norm_.html)
- [torch.utils.checkpoint — PyTorch documentation](https://docs.pytorch.org/docs/2.14/checkpoint.html)
- [szagoruyko/pytorchviz — Visualizations of PyTorch execution graphs](https://github.com/szagoruyko/pytorchviz)

---

## Next Steps

- Next Module: **[2200: Frameworks](../2200-frameworks/)**
- Continue with: **[2201: PyTorch Computational Graphs and Dynamic Execution](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)**
- Assessment: **[2100: Calculus - Quiz](./assessment/QUIZ.md)**

---

**Related:**

- [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md)
- [2201: PyTorch Computational Graphs and Dynamic Execution](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)
- [3301: Activation Functions - GELU, SwiGLU, and Beyond](../../phase3-transformers/3300-decoding/3301-Activation-Functions.md)

**Experiment:** [EXP-2102: Backpropagation Experiment](../../../../experiments/EXP_2102_BACKPROPAGATION.md)
