# EXP-2201: PyTorch Computational Graphs

**Understanding dynamic computation graphs and autograd**

---

## 🎯 Experiment Overview

**Time:** 60-75 minutes
**Difficulty:** ⭐⭐ Intermediate
**Prerequisites:**
- EXP_2101: Tensor Algebra
- Basic PyTorch knowledge
- Understanding of backpropagation

**Learning Objectives:**
- Understand PyTorch's dynamic computation graph
- Master automatic differentiation (autograd)
- Build custom computational graphs
- Optimize graph execution
- Debug gradient flow

---

## 📚 Background

PyTorch uses **dynamic computation graphs** that are built on-the-fly during execution. This is different from TensorFlow 1.x's static graphs.

### Key Concepts

1. **Tensor** - Multi-dimensional array with gradient tracking
2. **Computational Graph** - DAG of operations
3. **Autograd** - Automatic differentiation engine
4. **Gradient Flow** - How gradients propagate backward

---

## 🔬 Experiment 1: Autograd Fundamentals (25 minutes)

### Step 1.1: Gradient Tracking

```python
# File: autograd_basics.py
"""
PyTorch Autograd Basics
=======================
"""

import torch

# Create tensors with gradient tracking
x = torch.randn(2, 3, requires_grad=True)
y = torch.randn(2, 3, requires_grad=True)
z = torch.randn(2, 3, requires_grad=False)  # No gradient tracking

print(f"x requires_grad: {x.requires_grad}")
print(f"y requires_grad: {y.requires_grad}")
print(f"z requires_grad: {z.requires_grad}")

# Computational graph
w = x + y  # Operation tracked
v = w * z  # w tracked, z not - result still tracked
loss = v.sum()

print(f"\nw requires_grad: {w.requires_grad}")
print(f"v requires_grad: {v.requires_grad}")
print(f"loss requires_grad: {loss.requires_grad}")

# Backward pass
loss.backward()

print(f"\nx.grad:\n{x.grad}")
print(f"y.grad:\n{y.grad}")
print(f"z.grad: {z.grad}")  # None - no gradient tracking

# View computation graph
print(f"\nComputational graph of loss:")
print(f"  grad_fn: {loss.grad_fn}")

# Inspect graph
def print_graph(var, level=0):
    """Recursively print computation graph"""
    print("  " * level + f"{var}: {var.grad_fn}")
    if var.grad_fn:
        for fn_input in var.grad_fn.next_functions:
            if fn_input[0] is not None:
                print_graph(fn_input[0], level + 1)

print("\nComputation graph structure:")
print_graph(loss)

# Clear gradients
x.grad.zero_()
y.grad.zero_()
print("\nGradients cleared")
print(f"x.grad: {x.grad}")
```

**Checkpoint 1:** ✅ Autograd basics working

---

## 🔬 Experiment 2: Custom Gradients (20 minutes)

### Step 2.1: Define Custom Functions

```python
# File: custom_functions.py
"""
Custom Autograd Functions
========================
"""

import torch

class MyReLU(torch.autograd.Function):
    """
    Custom ReLU with forward and backward passes
    """

    @staticmethod
    def forward(ctx, x):
        """
        Forward pass: save context for backward
        """
        ctx.save_for_backward(x)
        return x.clamp(min=0)

    @staticmethod
    def backward(ctx, grad_output):
        """
        Backward pass: compute gradient
        grad_output: Gradient from upstream
        """
        x, = ctx.saved_tensors
        grad_x = grad_output.clone()
        grad_x[x < 0] = 0
        return grad_x

# Use custom function
class CustomReLU(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.relu = MyReLU.apply

    def forward(self, x):
        return self.relu(x)

# Test
x = torch.randn(5, requires_grad=True)
relu = CustomReLU()
y = relu(x)
loss = y.sum()

loss.backward()

print("Custom ReLU test:")
print(f"Input: {x}")
print(f"Output: {y}")
print(f"Gradient: {x.grad}")
print(f"Non-zero gradient count: {(x.grad != 0).sum().item()}")
```

### Step 2.2: More Complex Custom Function

```python
# File: complex_function.py
"""
Custom Function with Multiple Inputs
====================================
"""

import torch

class BilinearFunction(torch.autograd.Function):
    """Bilinear transformation: y = x1^T W x2"""

    @staticmethod
    def forward(ctx, x1, x2, W):
        """
        Args:
            x1: (batch, in1)
            x2: (batch, in2)
            W: (in1, in2)
        """
        ctx.save_for_backward(x1, x2, W)
        return torch.einsum('bi,ij,bj->b', x1, W, x2)

    @staticmethod
    def backward(ctx, grad_output):
        x1, x2, W = ctx.saved_tensors
        grad_x1 = torch.einsum('b,ij,bj->bi', grad_output, W, x2)
        grad_x2 = torch.einsum('b,bi,ij->bj', grad_output, x1, W)
        grad_W = torch.einsum('b,bi,bj->ij', grad_output, x1, x2)
        return grad_x1, grad_x2, grad_W

# Test
batch, in1, in2 = 4, 3, 5
x1 = torch.randn(batch, in1, requires_grad=True)
x2 = torch.randn(batch, in2, requires_grad=True)
W = torch.randn(in1, in2, requires_grad=True)

# Forward
y = BilinearFunction.apply(x1, x2, W)
loss = y.sum()

# Backward
loss.backward()

print("Bilinear function test:")
print(f"Output shape: {y.shape}")
print(f"x1.grad shape: {x1.grad.shape}")
print(f"x2.grad shape: {x2.grad.shape}")
print(f"W.grad shape: {W.grad.shape}")
```

**Checkpoint 2:** ✅ Custom gradients working

---

## 🔬 Experiment 3: Graph Optimization (20 minutes)

### Step 3.1: TorchScript Compilation

```python
# File: torchscript.py
"""
TorchScript: Static Graph Compilation
=====================================
"""

import torch
import time

# Define model
class SimpleModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear1 = torch.nn.Linear(784, 256)
        self.relu = torch.nn.ReLU()
        self.linear2 = torch.nn.Linear(256, 10)

    def forward(self, x):
        x = self.linear1(x)
        x = self.relu(x)
        x = self.linear2(x)
        return x

model = SimpleModel()

# Eager mode (default)
x = torch.randn(32, 784)

# Warmup
for _ in range(10):
    _ = model(x)

# Benchmark eager
start = time.time()
for _ in range(100):
    _ = model(x)
if torch.cuda.is_available():
    torch.cuda.synchronize()
time_eager = time.time() - start

# Compile with TorchScript
model_scripted = torch.jit.script(model)

# Benchmark scripted
start = time.time()
for _ in range(100):
    _ = model_scripted(x)
if torch.cuda.is_available():
    torch.cuda.synchronize()
time_scripted = time.time() - start

print(f"Eager mode: {time_eager*1000:.2f} ms")
print(f"TorchScript: {time_scripted*1000:.2f} ms")
print(f"Speedup: {time_eager/time_scripted:.2f}x")

# Save scripted model
model_scripted.save('simple_model.pt')
print("\n✓ Model saved as TorchScript")
```

### Step 3.2: Tracing vs Scripting

```python
# File: tracing_vs_scripting.py
"""
TorchScript: Tracing vs Scripting
=================================
"""

import torch

class ControlFlowModel(torch.nn.Module):
    """Model with control flow"""

    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(10, 10)

    def forward(self, x, use_activation=True):
        x = self.linear(x)
        if use_activation:  # Control flow!
            x = torch.relu(x)
        return x

model = ControlFlowModel()

# Method 1: Tracing (doesn't capture control flow)
try:
    model_traced = torch.jit.trace(model, (torch.randn(1, 10), True))
    print("✓ Tracing successful")

    # Test with different input
    x = torch.randn(1, 10)
    out1 = model_traced(x, True)
    out2 = model_traced(x, False)  # Bug: still applies ReLU!
    print(f"Tracing bug: outputs differ? {not torch.allclose(out1, out2)}")
except Exception as e:
    print(f"Tracing error: {e}")

# Method 2: Scripting (captures control flow)
model_scripted = torch.jit.script(model)
print("\n✓ Scripting successful")

out1 = model_scripted(x, True)
out2 = model_scripted(x, False)  # Correct: no ReLU
print(f"Scripting correct: outputs differ? {not torch.allclose(out1, out2)}")
```

**Checkpoint 3:** ✅ Graph optimization working

---

## 🔬 Experiment 4: Gradient Debugging (15 minutes)

### Step 4.1: Detect Gradient Issues

```python
# File: gradient_debug.py
"""
Gradient Debugging Tools
========================
"""

import torch

def check_gradients(model):
    """Check for gradient issues"""

    issues = []

    for name, param in model.named_parameters():
        if param.grad is not None:
            # Check for NaN
            if torch.isnan(param.grad).any():
                issues.append(f"{name}: NaN gradient")

            # Check for Inf
            if torch.isinf(param.grad).any():
                issues.append(f"{name}: Inf gradient")

            # Check for zeros
            if (param.grad == 0).all():
                issues.append(f"{name}: All zeros")

            # Check gradient magnitude
            grad_norm = param.grad.norm().item()
            if grad_norm > 1000:
                issues.append(f"{name}: Exploding gradients (norm={grad_norm:.2f})")
            elif grad_norm < 1e-7:
                issues.append(f"{name}: Vanishing gradients (norm={grad_norm:.2e})")
        else:
            issues.append(f"{name}: No gradient")

    return issues

# Test with problematic model
class BadModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear1 = torch.nn.Linear(10, 50)
        self.linear2 = torch.nn.Linear(50, 10)
        # Bad initialization
        self.linear2.weight.data.fill_(1000)

    def forward(self, x):
        x = self.linear1(x)
        x = torch.relu(x)
        x = self.linear2(x)
        return x

model = BadModel()
x = torch.randn(1, 10)
y = model(x)
loss = y.sum()

loss.backward()

issues = check_gradients(model)
print("Gradient issues found:")
for issue in issues:
    print(f"  ⚠️  {issue}")

if not issues:
    print("  ✓ No issues detected")
```

### Step 4.2: Gradient Visualization

```python
# File: gradient_viz.py
"""
Gradient Flow Visualization
==========================
"""

import torch
import matplotlib.pyplot as plt

class VisualModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = torch.nn.ModuleList([
            torch.nn.Linear(10, 20),
            torch.nn.Linear(20, 20),
            torch.nn.Linear(20, 20),
            torch.nn.Linear(20, 10)
        ])

    def forward(self, x):
        for layer in self.layers:
            x = torch.relu(layer(x))
        return x

model = VisualModel()
x = torch.randn(1, 10)
y = model(x)
loss = y.sum()

loss.backward()

# Collect gradient norms
grad_norms = []
for i, layer in enumerate(model.layers):
    if layer.weight.grad is not None:
        grad_norms.append(layer.weight.grad.norm().item())

# Plot
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.bar(range(len(grad_norms)), grad_norms)
plt.xlabel('Layer')
plt.ylabel('Gradient Norm')
plt.title('Gradient Flow')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.semilogy(range(len(grad_norms)), grad_norms, 'o-')
plt.xlabel('Layer')
plt.ylabel('Gradient Norm (log scale)')
plt.title('Gradient Flow (Log Scale)')
plt.grid(True)

plt.tight_layout()
plt.savefig('gradient_flow.png')
print("✓ Saved visualization to gradient_flow.png")
```

**Checkpoint 4:** ✅ Gradient debugging working

---

## 📊 Computational Graph Insights

### Graph Construction

```text
Forward Pass:
x → [op1] → a → [op2] → b → [op3] → loss

Backward Pass:
loss.grad → ∂loss/∂b → ∂loss/∂a → ∂loss/∂x
```

### Memory vs Speed Tradeoffs

| Technique | Memory | Speed | Use Case |
|-----------|--------|-------|----------|
| Eager mode | High | Slow | Debugging, research |
| TorchScript | Medium | Fast | Production |
| gradient_checkpointing | Low | Slower | Large models |
| no_grad() | Low | Fast | Inference |

---

## ✅ Experiment Checklist

- [ ] Autograd basics understood
- [ ] Custom functions implemented
- [ ] Graph optimization working
- [ ] Gradient debugging mastered
- [ ] Visualizations created

---

## 🎓 Key Takeaways

1. **Dynamic Graphs** - Built on-the-fly during execution
2. **Autograd** - Automatic differentiation via computational graph
3. **TorchScript** - Compile to static graphs for production
4. **Gradient Debugging** - Essential for training deep networks
5. **Memory Matters** - Graph execution affects memory usage

---

## 🚀 Next Steps

1. **EXP_2102**: Backpropagation - Deeper dive into gradients
2. **2202**: TensorFlow XLA - Alternative graph optimization
3. **LAB-006**: Train Model from Scratch - Apply autograd knowledge

---

**Last Updated:** 2026-02-04
**Experiment:** 2201 - PyTorch Computational Graphs
**Time Estimate:** 60-75 minutes
**Difficulty:** ⭐⭐ Intermediate
