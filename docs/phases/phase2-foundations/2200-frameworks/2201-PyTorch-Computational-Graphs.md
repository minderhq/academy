---
Document ID: 2201
Title: PyTorch Computational Graphs and Dynamic Execution
Phase: 2
Module: 2200
Last Updated: 2026-09-26
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'pytorch', 'tensorflow', 'cuda']
---

# 2201: PyTorch Computational Graphs and Dynamic Execution

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Dynamic vs Static Graphs](#dynamic-vs-static-graphs)
- [Computational Graph Construction](#computational-graph-construction)
- [Automatic Gradient Functions (grad_fn)](#automatic-gradient-functions-grad_fn)
- [Dynamic Control Flow](#dynamic-control-flow)
- [Custom Autograd Functions](#custom-autograd-functions)
- [Graph Optimization](#graph-optimization)
- [Debugging Computational Graphs](#debugging-computational-graphs)
- [Memory Management](#memory-management)
- [Advanced Patterns](#advanced-patterns)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare Dynamic vs Static Graphs
- Explain Computational Graph Construction
- Explain Automatic Gradient Functions (grad_fn)
- Explain Dynamic Control Flow
- Explain Custom Autograd Functions
- Explain Graph Optimization

---

## Abstract
PyTorch uses dynamic computational graphs (define-by-run), unlike static-graph frameworks such as TensorFlow, where `@tf.function` traces a fixed graph ahead of execution. This flexibility enables more intuitive code, easier debugging, and dynamic control flow within models.

## Dynamic vs Static Graphs

### Dynamic Graph (PyTorch)
```python
import torch

# Graph is built ON-THE-FLY during execution
def dynamic_model(x):
    if x.sum() > 0:
        return x * 2
    else:
        return x ** 2

x = torch.tensor([1., 2., 3.], requires_grad=True)
y = dynamic_model(x)
y.sum().backward()

# The graph path depends on the input value!
# Branches, loops, function calls - all work naturally
```

### Static Graph (TensorFlow)
```python
# Graph must be DEFINED FIRST, then executed.
# TensorFlow 2.x builds it by TRACING: @tf.function records the ops into a
# graph on the first call. AutoGraph rewrites a Python `if` whose condition
# is a Tensor into tf.cond — BOTH branches are baked into the graph.
import tensorflow as tf

@tf.function
def static_model(x):
    if tf.reduce_sum(x) > 0:
        return x * 2
    else:
        return x ** 2

x = tf.constant([1., 2., 3.])
result = static_model(x)  # tracing happens on this first call

# TensorFlow 1.x (legacy, removed from the main namespace in TF 2.x —
# available only as tf.compat.v1) made you assemble the graph by hand:
# x = tf.placeholder(tf.float32)
# cond = tf.reduce_sum(x) > 0
# y = tf.cond(cond, lambda: x * 2, lambda: x ** 2)
# with tf.Session() as sess:
#     result = sess.run(y, feed_dict={x: [1., 2., 3.]})
```

## Computational Graph Construction

### Graph Building Process
```python
import torch

# Start with leaf tensors (user-created)
x = torch.tensor([1., 2., 3.], requires_grad=True)

# Each operation creates a new tensor with grad_fn
a = x + 1          # grad_fn=<AddBackward0>
b = a * 2          # grad_fn=<MulBackward0>
c = torch.sum(b)   # grad_fn=<SumBackward0>

# Inspect the graph
print(c.grad_fn)   # <SumBackward0 object at 0x...>
print(c.grad_fn.next_functions[0][0])  # <MulBackward0 object at 0x...>
print(c.grad_fn.next_functions[0][0].next_functions[0][0])  # <AddBackward0 object at 0x...>
```

### Graph Structure
```text
        [x: Leaf]
           │
           ▼
      [AddBackward0]
         (+1)
           │
           ▼
      [MulBackward0]
         (×2)
           │
           ▼
      [SumBackward0]
         (Σ)
           │
           ▼
        [c: Output]
```

## Automatic Gradient Functions (grad_fn)

### Common grad_fn Types
```python
import torch

x = torch.randn(2, 3, requires_grad=True)

# Element-wise operations
y = x + 1           # AddBackward0
y = x - 1           # SubBackward0
y = x * 2           # MulBackward0
y = x / 2           # DivBackward0
y = x ** 2          # PowBackward0

# Reduction operations
y = x.sum()         # SumBackward0
y = x.mean()        # MeanBackward0
y = x.max()         # MaxBackward1 (no-dim full reduction)

# Matrix operations
y = x @ x.t()       # MmBackward0 (matrix multiply)
y = torch.mm(x, x.t())  # Same

# Activation functions
y = torch.relu(x)   # ReluBackward0
y = torch.sigmoid(x)  # SigmoidBackward0
y = torch.tanh(x)   # TanhBackward0

# Loss functions
y = torch.nn.functional.mse_loss(x, torch.zeros_like(x))  # MseLossBackward0
```

### Inspecting grad_fn
```python
import torch

x = torch.tensor([1., 2., 3.], requires_grad=True)
y = x ** 2 + 2 * x + 1

# Get the gradient function
print(y.grad_fn)
# <AddBackward0 object at 0x...>

# Trace back through graph
print(y.grad_fn.next_functions)
# ((<AddBackward0 object at 0x...>, 0), (None, 0))

# This is useful for debugging and custom autograd functions
```

## Dynamic Control Flow

### Conditional Computation
```python
import torch

def dynamic_attention(x, use_attention=True):
    """
    Attention is only computed if needed
    """
    if use_attention:
        # Self-attention branch
        q = k = v = x
        attn = torch.softmax(q @ k.T / x.size(-1)**0.5, dim=-1)
        return attn @ v
    else:
        # Simple linear branch
        return x

# Both paths work! The graph adapts to the input.
x = torch.randn(10, 512, requires_grad=True)
y = dynamic_attention(x, use_attention=True)
y.sum().backward()
```

### Loops with Dynamic Length
```python
import torch

W = torch.randn(64, 128, requires_grad=True)   # input -> hidden
U = torch.randn(128, 128, requires_grad=True)  # hidden -> hidden

def rnn_cell(x_t, h_prev):
    """One step: h_t = tanh(x_t @ W + h_prev @ U)."""
    return torch.tanh(x_t @ W + h_prev @ U)

def unroll_rnn(x, max_steps=None):
    """
    RNN that runs until a condition is met
    """
    hidden = torch.zeros(x.size(0), 128)

    for i in range(x.size(1)):
        # Process one timestep
        hidden = rnn_cell(x[:, i, :], hidden)

        # Early stopping based on condition
        if hidden.norm() < 0.01:
            break

        if max_steps and i >= max_steps:
            break

    return hidden

x = torch.randn(4, 10, 64)  # (batch, timesteps, features)
out = unroll_rnn(x, max_steps=5)
out.sum().backward()
print(out.shape)            # torch.Size([4, 128])
print(W.grad is not None)   # True - grads flowed through the unrolled loop

# The loop can have different lengths for different inputs!
# Each iteration adds nodes to the graph as it runs.
```

### Recursive Functions
```python
import torch

class Node:
    def __init__(self, value=None, left=None, right=None):
        self.is_leaf = left is None
        self.value = value
        self.left = left
        self.right = right

def binary_tree_traversal(tree, fn):
    """
    Recursively process a tree structure
    """
    if tree.is_leaf:
        return fn(tree.value)
    else:
        left = binary_tree_traversal(tree.left, fn)
        right = binary_tree_traversal(tree.right, fn)
        return fn(torch.cat([left, right]))

# Works with autograd!
leaf1 = Node(torch.tensor([1.], requires_grad=True))
leaf2 = Node(torch.tensor([2.], requires_grad=True))
leaf3 = Node(torch.tensor([3.], requires_grad=True))
tree = Node(left=leaf1, right=Node(left=leaf2, right=leaf3))

result = binary_tree_traversal(tree, lambda x: x ** 2)
print(result)  # tensor([1., 256., 6561.]) - fn applied at every level
result.sum().backward()  # non-scalar: reduce before backward
print(leaf2.value.grad)  # tensor([1024.]) - fn applied 3x: d(a^8)/da = 8a^7 = 1024
```

## Custom Autograd Functions

### Creating a Custom Function
```python
import torch
from torch.autograd import Function

class MyCustomFunction(Function):
    @staticmethod
    def forward(ctx, x, constant):
        """
        Forward pass: save data for backward
        """
        ctx.constant = constant
        ctx.save_for_backward(x)
        return x * constant

    @staticmethod
    def backward(ctx, grad_output):
        """
        Backward pass: compute gradients
        """
        x, = ctx.saved_tensors
        constant = ctx.constant

        # ∂(x*c)/∂x = c
        grad_x = grad_output * constant

        # No gradient for constant (or None)
        grad_constant = None

        return grad_x, grad_constant

# Use the custom function
x = torch.tensor([1., 2., 3.], requires_grad=True)
y = MyCustomFunction.apply(x, 2.0)
y.sum().backward()
print(x.grad)  # [2., 2., 2.]
```

### Example: ReLU with Custom Grad
```python
import torch
from torch.autograd import Function

class CustomReLU(Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return x.clamp(min=0)

    @staticmethod
    def backward(ctx, grad_output):
        x, = ctx.saved_tensors
        grad_x = grad_output * (x > 0).float()
        return grad_x

# Use it
x = torch.randn(5, requires_grad=True)
y = CustomReLU.apply(x)
y.sum().backward()
print(x.grad)  # 1.0 where x > 0, 0.0 elsewhere (matches torch.relu's gradient)
```

## Graph Optimization

### In-place Operations Warning
```python
import torch

# 1. In-place on a leaf that requires grad: always a RuntimeError.
x = torch.tensor([1., 2., 3.], requires_grad=True)
try:
    x += 1
except RuntimeError as e:
    print(e)
    # a leaf Variable that requires grad is being used in an in-place operation.

# 2. Modifying a tensor autograd SAVED for backward: caught at backward time.
x = torch.tensor([1., 2.], requires_grad=True)
y = torch.exp(x)
z = y.sum()
y += 1  # exp saved its output (d/dx exp(x) = exp(x))
try:
    z.backward()
except RuntimeError as e:
    print(e)
    # one of the variables needed for gradient computation has been modified
    # by an inplace operation: [torch.FloatTensor [2]], which is output 0 of
    # ExpBackward0, is at version ...

# 3. In-place on a non-leaf whose value nothing saved: runs silently with
# correct grads - but the pattern is fragile in larger models.
x = torch.tensor([1., 2., 3.], requires_grad=True)
y = x + 1
z = (y + 2).sum()
y += 1  # y + 2 needs dz/dy = 1, not y's value - nothing breaks here
z.backward()
print(x.grad)  # tensor([1., 1., 1.]) - dz/dx = 1 regardless

# Instead of in-place, rebind:
y = y + 1  # Creates a new tensor; the existing graph stays valid
```

### Detaching from Graph
```python
import torch

x = torch.randn(3, requires_grad=True)
y = x ** 2

# Detach: don't track gradients
z = y.detach()  # z has no grad_fn

# Or use with torch.no_grad()
with torch.no_grad():
    w = x ** 3  # No graph built

# Use for inference to save memory
```

### Gradient Checkpointing
```python
import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint

class VeryDeepModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.ModuleList([nn.Linear(1024, 1024) for _ in range(100)])

    def forward(self, x):
        for i, layer in enumerate(self.layers):
            # Checkpoint every 10 layers
            if i % 10 == 0:
                x = checkpoint(layer, x, use_reentrant=False)
            else:
                x = layer(x)
        return x

# use_reentrant=False recomputes correctly even when the checkpoint input
# does not carry requires_grad. The legacy default (use_reentrant=True)
# silently yields None gradients for the checkpointed segment in that case,
# with a warning: "None of the inputs have requires_grad=True.
# Gradients will be None."

# Trade-off: only segment inputs are stored, so peak activation memory
# drops; in exchange, backward recomputes each segment's forward math.
```

## Debugging Computational Graphs

### Detecting Graph Issues
```python
import torch
import torch.nn as nn
import torch.nn.functional as F

# 1. Check for None gradients
model = nn.Linear(16, 4)
optimizer = torch.optim.Adam(model.parameters())

inputs = torch.randn(8, 16)
targets = torch.randint(0, 4, (8,))
loss = F.cross_entropy(model(inputs), targets)
loss.backward()

# Check for missing gradients
for name, param in model.named_parameters():
    if param.grad is None:
        print(f"No gradient for: {name}")

# 2. Check for NaN/Inf gradients
for name, param in model.named_parameters():
    if param.grad is not None:
        if torch.isnan(param.grad).any():
            print(f"NaN gradient in: {name}")
        if torch.isinf(param.grad).any():
            print(f"Inf gradient in: {name}")

# 3. Gradient flow inspection
def check_gradient_flow(model):
    for name, param in model.named_parameters():
        if param.grad is not None:
            mean_grad = param.grad.mean().item()
            print(f"{name}: {mean_grad:.6f}")

check_gradient_flow(model)
```

### Graph Visualization
```python
# torchviz is third-party: pip install torchviz (Graphviz must be on PATH)
from torchviz import make_dot

x = torch.randn(3, requires_grad=True)
y = x ** 2 + 2 * x + 1

# Visualize the autograd graph as a PNG
make_dot(y, params={"x": x}).render("graph", format="png")

# TensorBoard support ships with torch - no tensorboardX needed
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter()

model = torch.nn.Sequential(
    torch.nn.Linear(3, 4),
    torch.nn.ReLU(),
    torch.nn.Linear(4, 2),
)
inputs = torch.randn(1, 3)
writer.add_graph(model, inputs)
writer.close()
```

## Memory Management

### Graph Retention
```python
import torch

# The graph is kept until backward() is called
x = torch.randn(1000, requires_grad=True)
y = x ** 2
# Graph is in memory!

y.sum().backward()
# Graph is released (unless retain_graph=True)

# For multiple backward passes:
x = torch.tensor([1., 2.], requires_grad=True)
y1 = x ** 2
y2 = x ** 3

# Need to retain graph for second backward
(y1 + y2).sum().backward(retain_graph=True)
y1.sum().backward()  # Can still backward
print(x.grad)  # tensor([7., 20.]) - accumulated 2x + 3x^2 + 2x at x=[1, 2]
```

### Gradient Accumulation
```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

model = nn.Linear(768, 10).cuda()
optimizer = torch.optim.Adam(model.parameters())

accumulation_steps = 4
dataloader = DataLoader(
    TensorDataset(
        torch.randn(16, 768).cuda(),
        torch.randint(0, 10, (16,)).cuda(),
    ),
    batch_size=2,
)

for i, (data, target) in enumerate(dataloader):
    output = model(data)
    loss = F.cross_entropy(output, target) / accumulation_steps

    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()

# 16 samples / batch 2 = 8 micro-batches -> optimizer stepped 8 / 4 = 2 times
print({int(v["step"].item()) for v in optimizer.state.values()})  # {2}
```

## Advanced Patterns

### Higher-Order Gradients
```python
import torch

x = torch.tensor([2.0], requires_grad=True)
y = x ** 3

# First derivative
dy_dx = torch.autograd.grad(y, x, create_graph=True)[0]
print(dy_dx)  # tensor([12.])  (3x² at x=2)

# Second derivative (create_graph=True made dy_dx differentiable)
d2y_dx2 = torch.autograd.grad(dy_dx, x)[0]
print(d2y_dx2)  # tensor([12.])  (6x at x=2)
```

### Jacobian Computation
```python
import torch

def jacobian(y, x):
    """Compute Jacobian matrix"""
    y_flat = y.flatten()
    jac = torch.zeros(len(y_flat), *x.shape)

    for i in range(len(y_flat)):
        grad = torch.autograd.grad(y_flat[i], x, retain_graph=True)[0]
        jac[i] = grad.flatten()

    return jac

x = torch.randn(3, requires_grad=True)
y = x ** 2 + x
J = jacobian(y, x)
# Diagonal is d/dx (x^2 + x) = 2x + 1; off-diagonal is 0 (independent inputs)
```

---

## References

### Related Documents

- [2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md)
- [2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Programming.md)
- [2102: Backpropagation and Automatic Differentiation](../2100-calculus/2102-Backpropagation-and-Derivatives.md)

### External References

- [torch.autograd — PyTorch documentation](https://docs.pytorch.org/docs/2.14/autograd.html)
- [Extending torch.autograd — PyTorch documentation](https://docs.pytorch.org/docs/2.14/notes/extending.html)
- [torch.utils.checkpoint — PyTorch documentation](https://docs.pytorch.org/docs/2.14/checkpoint.html)
- [Better performance with tf.function — TensorFlow guide](https://www.tensorflow.org/guide/function)
- [szagoruyko/pytorchviz — Visualizations of PyTorch execution graphs](https://github.com/szagoruyko/pytorchviz)

---

## Next Steps

- Continue with: **[2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md)**
- Next Module: **[2300: Framework Engineering](../2300-framework-engineering/)**
- Assessment: **[2200: Frameworks - Quiz](./assessment/QUIZ.md)**

---

**Related:**
- [2101: Tensor Algebra and Linear Algebra for AI](../2100-calculus/2101-Tensor-Algebra.md)
- [2102: Backpropagation and Automatic Differentiation](../2100-calculus/2102-Backpropagation-and-Derivatives.md)
- [2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md)

**Experiment:** [EXP-2201: PyTorch Computational Graphs](../../../../experiments/EXP_2201_PYTORCH_GRAPHS.md)
