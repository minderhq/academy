---
Document ID: 2201
Title: PyTorch Computational Graphs and Dynamic Execution
Phase: 2
Module: 2200
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'pytorch', 'tensorflow', 'cuda']
---

# 2201: PyTorch Computational Graphs and Dynamic Execution

## Abstract
PyTorch uses dynamic computational graphs (define-by-run), unlike TensorFlow 1.x's static graphs. This flexibility enables more intuitive code, easier debugging, and dynamic control flow within models.

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

### Static Graph (TensorFlow 1.x)
```python
# Graph must be DEFINED FIRST, then executed
# (simplified TF1.x style)
x = tf.placeholder(tf.float32)
cond = tf.reduce_sum(x) > 0
y = tf.cond(cond, lambda: x * 2, lambda: x ** 2)

# Only NOW we can run it
with tf.Session() as sess:
    result = sess.run(y, feed_dict={x: [1., 2., 3.]})
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
print(c.grad_fn)   # SumBackward0
print(c.grad_fn.next_functions[0][0])  # MulBackward0
print(c.grad_fn.next_functions[0][0].next_functions[0][0])  # AddBackward0
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
y = x.max()         # MaxBackward0

# Matrix operations
y = x @ x.t()       # MmBackward0 (matrix multiply)
y = torch.mm(x, x.t())  # Same

# Activation functions
y = torch.relu(x)   # ReluBackward0
y = torch.sigmoid(x)  # SigmoidBackward0
y = torch.tanh(x)   # TanhBackward0

# Loss functions
y = torch.nn.functional.mse_loss(x, torch.zeros_like(x))  # MseLossBackward
```

### Inspecting grad_fn
```python
x = torch.tensor([1., 2., 3.], requires_grad=True)
y = x ** 2 + 2 * x + 1

# Get the gradient function
print(y.grad_fn)
# Output: AddBackward0

# Trace back through graph
print(y.grad_fn.next_functions)
# Output: ((<AddBackward0 object>, 0), (None, 0))

# This is useful for debugging and custom autograd functions
```

## Dynamic Control Flow

### Conditional Computation
```python
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
def unroll_rnn(x, max_steps=None):
    """
    RNN that runs until a condition is met
    """
    hidden = torch.zeros(x.size(0), 128, requires_grad=True)

    for i in range(x.size(1)):
        # Process one timestep
        hidden = rnn_cell(x[:, i, :], hidden)

        # Early stopping based on condition
        if hidden.norm() < 0.01:
            break

        if max_steps and i >= max_steps:
            break

    return hidden

# The loop can have different lengths for different inputs!
# PyTorch handles this naturally.
```

### Recursive Functions
```python
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
tree = create_binary_tree()
result = binary_tree_traversal(tree, lambda x: x ** 2)
result.backward()
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
```

## Graph Optimization

### In-place Operations Warning
```python
# In-place ops can break the graph
x = torch.tensor([1., 2., 3.], requires_grad=True)
y = x + 1
z = y + 2

# Fine...
y += 1  # In-place!
# z's gradient is now undefined!

# Instead:
y = y + 1  # Creates new tensor
```

### Detaching from Graph
```python
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
from torch.utils.checkpoint import checkpoint

class VeryDeepModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.ModuleList([nn.Linear(1024, 1024) for _ in range(100)])

    def forward(self, x):
        for i, layer in enumerate(self.layers):
            # Checkpoint every 10 layers
            if i % 10 == 0:
                x = checkpoint(layer, x)
            else:
                x = layer(x)
        return x

# Memory savings: ~50%
# Time cost: ~20% slower
```

## Debugging Computational Graphs

### Detecting Graph Issues
```python
# 1. Check for None gradients
model = MyModel()
optimizer = torch.optim.Adam(model.parameters())

loss = compute_loss(inputs, targets)
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
```

### TensorBoardX Visualization
```python
from torchviz import make_dot

x = torch.randn(3, requires_grad=True)
y = x ** 2 + 2 * x + 1
y.sum().backward()

# Visualize
make_dot(y, params=dict(x=x)).render("graph", format="png")

# For models
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter()

model = MyModel()
inputs = torch.randn(1, 3, 224, 224, requires_grad=True)
writer.add_graph(model, inputs)
writer.close()
```

## Memory Management

### Graph Retention
```python
# The graph is kept until backward() is called
x = torch.randn(1000, requires_grad=True)
y = x ** 2
# Graph is in memory!

y.sum().backward()
# Graph is released (unless retain_graph=True)

# For multiple backward passes:
y1 = x ** 2
y2 = x ** 3

# Need to retain graph for second backward
(y1 + y2).sum().backward(retain_graph=True)
y1.sum().backward()  # Can still backward
```

### Gradient Accumulation
```python
model = MyModel()
optimizer = torch.optim.Adam(model.parameters())

accumulation_steps = 4

for i, (data, target) in enumerate(dataloader):
    output = model(data)
    loss = F.cross_entropy(output, target) / accumulation_steps

    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

## Advanced Patterns

### Higher-Order Gradients
```python
x = torch.tensor([2.0], requires_grad=True)
y = x ** 3

# First derivative
dy_dx = torch.autograd.grad(y, x, create_graph=True)[0]
print(dy_dx)  # [12.]  (3x² at x=2)

# Second derivative
d2y_dx2 = torch.autograd.grad(dy_dx, x)[0]
print(d2y_dx2)  # [12.]  (6x at x=2)
```

### Jacobian Computation
```python
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
```

---

## Next Steps

- Continue with: **[2202: TensorFlow XLA](./2202-TensorFlow-XLA-Compilers.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [2101: Tensor Algebra](../2100-calculus/2101-Tensor-Algebra.md)
- [2102: Backpropagation](../2100-calculus/2102-Backpropagation-and-Derivatives.md)
- [2202: TensorFlow XLA](./2202-TensorFlow-XLA-Compilers.md)

**Experiment Template:** `experiments/EXP_2201_PYTORCH_GRAPH.md`
