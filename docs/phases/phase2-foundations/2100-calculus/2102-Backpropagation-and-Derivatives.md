---
Document ID: 2102
Title: Backpropagation and Automatic Differentiation
Phase: 2
Module: 2100
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['math', 'calculus', 'tensors', 'backpropagation']
---

# 2102: Backpropagation and Automatic Differentiation

## Abstract
Backpropagation is the algorithm that enables neural networks to learn. It computes gradients of the loss function with respect to all parameters by applying the chain rule of calculus recursively through the computational graph.

## The Chain Rule

### Single Variable Chain Rule
```
If y = f(g(x)), then:
dy/dx = f'(g(x)) × g'(x)

Example:
y = sin(x²)
dy/dx = cos(x²) × 2x
```

### Multivariate Chain Rule (for Tensors)
```
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
print(x.grad)  # tensor(64.)

# Manual calculation:
# y = ((x + 1) × 2)² - 4
# dy/dx = 2((x+1)×2) × 2 = 4(x+1)×2 = 8(x+1)
# At x = 2: 8(3) = 64 ✓
```

## Automatic Differentiation (Autograd)

### How PyTorch Autograd Works
```
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

# Each tensor has:
print(x.requires_grad)   # Need gradient?
print(x.grad)            # Accumulated gradient
print(x.grad_fn)         # Function that created this tensor
print(x.is_leaf)         # Is this a leaf node (user-created)?

# Example:
x = torch.tensor(2.0, requires_grad=True)
y = x ** 2
z = 2 * y

print(x.grad_fn)         # None (leaf)
print(y.grad_fn)         # <PowBackward0>
print(z.grad_fn)         # <MulBackward0>
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
```
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
    grad_input = torch.einsum('bi,ji->bj', grad_output, W)

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
```
In deep networks, repeated multiplication of small gradients:
∂L/∂x₁ = ∂L/∂xₙ × ∂xₙ/∂xₙ₋₁ × ... × ∂x₂/∂x₁

If each |∂xᵢ₊₁/∂xᵢ| < 1, gradient → 0

Example with sigmoid:
  σ'(z) = σ(z)(1 - σ(z)) ≤ 0.25

  After n layers: (0.25)^n → 0
```

### Solutions
```python
# 1. ReLU activation (gradient = 1 for positive)
torch.nn.ReLU()

# 2. Proper initialization (Xavier/He)
torch.nn.init.xavier_uniform_(W)
torch.nn.init.kaiming_normal_(W, mode='fan_in')

# 3. Batch normalization
torch.nn.BatchNorm1d(num_features)

# 4. Residual connections (skip connections)
class ResidualBlock(nn.Module):
    def __forward__(self, x):
        return self.fn(x) + x  # Gradient flows directly!
```

### Exploding Gradient Problem
```
If gradients grow too large:
  Weights updated too aggressively
  Optimization diverges

Detection: NaN or Inf in gradients
```

### Solutions
```python
# 1. Gradient clipping
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

# 2. Lower learning rate
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)

# 3. Gradient checkpointing (trade compute for memory)
from torch.utils.checkpoint import checkpoint

output = checkpoint(my_expensive_function, input)
```

## Computational Graph Visualization

### Using torchviz
```python
from torchviz import make_dot

x = torch.randn(2, requires_grad=True)
y = x ** 2 + 3 * x + 1
y.sum().backward()

# Visualize graph
make_dot(y, params=dict(x=x)).render("graph", format="png")
```

### Reading the Graph
```
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
x = torch.tensor([2.0, 3.0], requires_grad=True)
y = x[0] ** 2 + x[1] ** 3

# First derivatives
grad = torch.autograd.grad(y, x, create_graph=True)[0
# grad = [4, 27]

# Second derivatives (Hessian diagonal)
hessian_diag = torch.autograd.grad(grad.sum(), x)[0]
# = [2, 18x] at x=[2,3] = [2, 54]

# Full Hessian matrix
def hessian(y, x):
    """Compute full Hessian matrix"""
    grad = torch.autograd.grad(y, x, create_graph=True)[0]
    hessian = torch.zeros(len(x), len(x))

    for i in range(len(x)):
        grad2 = torch.autograd.grad(grad[i], x, retain_graph=True)[0]
        hessian[i] = grad2

    return hessian
```

### Applications
```
Hessian applications:
  - Newton's method optimization
  - Uncertainty estimation
  - Network pruning
  - Sharpness of minima analysis
```

## Gradient Accumulation

### Why Accumulate Gradients?
```
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
model = MyModel().cuda()
optimizer = torch.optim.Adam(model.parameters())

accumulation_steps = 4

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
```

## Best Practices

### 1. Gradient Zeroing
```python
# Always zero gradients before backward
optimizer.zero_grad()
# or
model.zero_grad()

# Common bug: Forgetting to zero!
# Gradients accumulate across batches
```

### 2. Disable Gradients for Inference
```python
# Saves memory and computation
with torch.no_grad():
    output = model(input)

# Or use eval mode
model.eval()
with torch.no_grad():
    for batch in test_loader:
        output = model(batch)

model.train()  # Back to training mode
```

### 3. Gradient Checkpointing
```python
# For very deep models or long sequences
from torch.utils.checkpoint import checkpoint

class DeepModel(nn.Module):
    def forward(self, x):
        # Checkpoint middle layers
        x = checkpoint(self.layer1, x)
        x = checkpoint(self.layer2, x)
        x = checkpoint(self.layer3, x)
        return x

# Trade-off: More compute, less memory
```

---

## Next Steps

- Next Module: **[2200: Frameworks](../2200-frameworks/)**
- Continue with: **[2201: PyTorch Graphs](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [2101: Tensor Algebra](./2101-Tensor-Algebra.md)
- [2201: PyTorch Graphs](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)
- [3301: Activation Functions](../../phase3-transformers/3300-decoding/3301-Activation-Functions.md)

**Experiment Template:** `experiments/EXP_2102_BACKPROP.md`
