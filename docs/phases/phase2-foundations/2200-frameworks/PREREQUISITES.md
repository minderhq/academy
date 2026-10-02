---
Document ID: 2200-PREREQUISITES
Title: "2200: Deep Learning Frameworks - Prerequisites"
Last Updated: 2026-09-26
Status: Complete
Difficulty: Intermediate
Tags: ['frameworks', 'pytorch', 'prerequisites', 'preparation']
---

# 2200: Deep Learning Frameworks - Prerequisites

Module 2200 takes frameworks apart: PyTorch's dynamic graphs, XLA's compiled graphs, and CUDA's execution model. This page checks that the machinery will make sense before you start — and every check is a small program you can run.

---

## Contents

- [Before You Start](#before-you-start)
- [Required Knowledge](#required-knowledge)
- [Quick Refresher](#quick-refresher)
- [Self-Assessment](#self-assessment)
- [Estimated Preparation Time](#estimated-preparation-time)
- [Common Gaps](#common-gaps)
- [Preparation Checklist](#preparation-checklist)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Before You Start

Module 2200 is three lessons about one stack: [2201](./2201-PyTorch-Computational-Graphs.md) (how frameworks execute), [2202](./2202-TensorFlow-XLA-Compilers.md) (how compilers optimize), and [2203](./2203-CUDA-Kernel-Programming.md) (how GPUs compute). The lessons assume you have already trained a model with PyTorch and now want to see underneath.

The five sections below test exactly what the lessons build on: Python fluency, `nn.Module` and the training loop, autograd as a graph, an intuition for kernel launches, and device awareness. Run every example — each one's output is described in the prose that follows it. All blocks run on CPU with a standard PyTorch install; a CUDA GPU is helpful but optional, and no CUDA toolchain is needed anywhere in this module.

---

## Required Knowledge

### 1. Python Fluency for Framework Code

**What you should know:**

- Decorators as functions that wrap functions, context managers as scoped behavior (`with`)
- `__call__` making an instance callable — the mechanism that lets `model(x)` invoke `forward`
- `torch.no_grad()` as both a decorator and a context manager

**Example:**

```python
import torch

# Decorators and context managers are the framework's control surface.
@torch.no_grad()
def inference_only(x, w):
    return x @ w                       # no graph is built inside here

x = torch.randn(4, requires_grad=True)
w = torch.randn(4, requires_grad=True)

y = inference_only(x, w)
print("output requires_grad:", y.requires_grad)

with torch.no_grad():
    z = x * 2
print("inside no_grad block:", z.requires_grad)

class Counter:                          # plain Python: the pattern behind nn.Module
    def __init__(self):
        self.calls = 0
    def __call__(self):                 # __call__ makes instances callable
        self.calls += 1
        return self.calls

c = Counter()
c(); c()
print("counter after two calls:", c.calls)
```

Both printed flags are `False`: inside `no_grad` no graph is recorded, so results never acquire `requires_grad`. The counter reaches `2` because the two bare `c()` calls go through `__call__` — exactly how `model(x)` reaches `model.forward(x)`.

**If you're not familiar:**

- **Review:** Python's documentation on decorators and the context manager protocol, then re-read `nn.Module`'s `__call__` in the PyTorch source
- **Practice:** Write a timing decorator and a `with`-based timer, then apply them to a small function
- **Estimated Time:** 1 hour

### 2. PyTorch Modules and the Training Loop

**What you should know:**

- `nn.Module` anatomy: submodules in `__init__`, `forward`, `parameters()`
- The four-line loop behind every optimizer: forward, `backward()`, update under `no_grad`, zero grads

**Example:**

```python
import torch
import torch.nn as nn

torch.manual_seed(0)

class TinyMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(3, 8)
        self.act = nn.ReLU()
        self.fc2 = nn.Linear(8, 2)

    def forward(self, x):
        return self.fc2(self.act(self.fc1(x)))

model = TinyMLP()
n_params = sum(p.numel() for p in model.parameters())
x = torch.randn(5, 3)
y = model(x)

print("params:", n_params)
print("output shape:", tuple(y.shape))
print("modules:", len(list(model.modules())))
```

The counts check out by hand: `fc1` holds 3·8 + 8 = 32 parameters, `fc2` holds 8·2 + 2 = 18, so 50 in total. The module tree contains 4 modules (the model itself, `fc1`, `act`, `fc2`), and a batch of 5 comes out with shape (5, 2).

**Example:**

```python
import torch

torch.manual_seed(0)

# The loop every framework runs: predict -> loss -> backward -> update.
x = torch.linspace(-1.0, 1.0, 20).reshape(-1, 1)
y_true = 3.0 * x - 1.0

w = torch.zeros(1, 1, requires_grad=True)
b = torch.zeros(1, requires_grad=True)
lr = 0.1

first = last = None
for step in range(200):
    pred = x @ w + b
    loss = ((pred - y_true) ** 2).mean()
    loss.backward()
    with torch.no_grad():
        w -= lr * w.grad
        b -= lr * b.grad
    w.grad.zero_()
    b.grad.zero_()
    if step == 0:
        first = loss.item()
    last = loss.item()

print(f"loss: {first:.4f} -> {last:.6f}")
print(f"recovered: w = {w.item():.4f}, b = {b.item():.4f}")
```

Starting from the all-zero model the first loss is about 4.3158 (just the mean of `y_true` squared), and after 200 manual SGD steps it collapses to effectively zero while the loop recovers the true line, `w = 3`, `b = -1`. If you can write this loop from memory, Lesson 2201 will feel like reading your own code with the covers taken off.

**If you're not familiar:**

- **Review:** The official PyTorch tutorials on nn.Module and optimization, plus 2102's autograd sections
- **Practice:** Re-derive this loop for a quadratic target `y = 0.5x²` (hint: keep the loop, change the data)
- **Estimated Time:** 1.5 hours

### 3. Autograd and Computational Graphs

**What you should know:**

- Each operation on a non-leaf tensor records a `grad_fn`; the chain of `.next_functions` is the graph
- Leaf tensors hold `None` in `.grad` until `backward()` runs
- The graph is rebuilt on every forward pass — that is what "dynamic" means

**Example:**

```python
import torch

torch.manual_seed(0)

# Every operation records its place in the graph via .grad_fn.
a = torch.randn(2, requires_grad=True)
b = torch.randn(2, requires_grad=True)

c = a + b            # <AddBackward0>
d = c * 2            # <MulBackward0>
loss = d.sum()       # <SumBackward0>

print("c grad_fn:", type(c.grad_fn).__name__)
print("d grad_fn:", type(d.grad_fn).__name__)
print("loss grad_fn:", type(loss.grad_fn).__name__)
print("d's graph reaches back to:", type(d.grad_fn.next_functions[0][0]).__name__)
print("leaf grads before backward:", a.grad)
loss.backward()
print("after backward, a.grad =", a.grad.tolist())
```

The chain reads `SumBackward0` ← `MulBackward0` ← `AddBackward0`, and `d`'s graph does reach back to `AddBackward0` through `next_functions`. Before `backward()` the leaf gradient is `None`; after it, `a.grad` is `[2.0, 2.0]` — the sum's gradient of ones times the multiply's constant 2. That is the whole story of backprop, told through introspection.

**If you're not familiar:**

- **Review:** CS231n's "Backpropagation, Intuitions" for the graph view of the chain rule
- **Practice:** Add a third operation (say, `e = d * d`) to the example and predict the new `grad_fn` chain before printing it
- **Estimated Time:** 1 hour

### 4. Kernel Thinking: Why Launches Matter

**What you should know:**

- Every PyTorch operation maps to (at least) one kernel launch; fewer launches means less dispatch overhead
- Mathematically identical operation sequences are not bit-identical in float32 — intermediate roundings differ

**Example:**

```python
import torch

torch.manual_seed(0)

# Why kernels and compilers exist: same math, very different execution.
x = torch.randn(1024, 1024)

def three_tiny_ops(t):
    return (t + 1.0) * 2.0 - 1.0       # three launches, intermediate roundings

def one_fused_op(t):
    return t * 2.0 + 1.0               # same math, folded by hand: one launch

a = three_tiny_ops(x)
b = one_fused_op(x)
diff = (a - b).abs().max().item()
assert diff < 1e-4                       # same math - differences are rounding only
print("max abs diff: %.2e (float32 rounding, not a bug)" % diff)
print("three_tiny_ops: 3 kernel launches per call")
print("one_fused_op:   1 kernel launch per call")
print("shape:", tuple(x.shape), "->", tuple(b.shape))
```

Both functions compute 2t + 1, yet the results differ in the last float32 bits — a maximum absolute difference around 4.8e-07 here, pure rounding from the three intermediate steps, and well under the 1e-4 the assert allows. This tiny discrepancy is the exact phenomenon XLA (Lesson 2202) exploits: fewer launches, fused work, slightly different numerics. On a GPU the launch overhead is microseconds per kernel, which is why fusion can speed up many small operations dramatically.

**If you're not familiar:**

- **Review:** Your 2101 notes on float32 representation, then skim the XLA overview for what fusion means at scale
- **Practice:** Count kernel launches for a five-operation expression, then fold it by hand to one launch and compare outputs
- **Estimated Time:** 0.5 hours

### 5. GPU and Device Awareness

**What you should know:**

- Tensors live on a device; every input to an operation must be on the same one
- `torch.device("cuda" if torch.cuda.is_available() else "cpu")` is the standard portable selection
- `.to(device)` moves tensors; results inherit the inputs' device

**Example:**

```python
import torch

# Frameworks move data between devices for you - but you need the mental model.
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
x = torch.arange(6.0).reshape(2, 3)
w = torch.tensor([[1.0, 0.0, -1.0],
                  [0.5, 2.0, 1.0],
                  [1.0, 1.0, 1.0]])

x_d, w_d = x.to(device), w.to(device)
y = x_d @ w_d                      # all tensors must live on ONE device
assert y.device.type == device.type
assert torch.allclose(y.cpu(), x @ w)
print("selected device:", device.type)
print("y = x @ w (moved back to cpu):", y.cpu().tolist())
```

The first line printed is `selected device: cuda` on a CUDA machine and `cpu` otherwise; the matmul result is the same matrix either way — `[[2.5, 4.0, 3.0], [10.0, 13.0, 6.0]]` — and the assertion that it equals the CPU-only result is what makes the block a real device test rather than decoration. Lesson 2203 builds directly on this vocabulary of devices and kernels.

**If you're not familiar:**

- **Review:** The PyTorch tutorials' device-agnostic training recipe
- **Practice:** Deliberately create a CPU/CUDA device mismatch in a scratch script and read the error message
- **Estimated Time:** 0.5 hours

---

## Quick Refresher

Two short programs that tie the sections together. The first shows that a custom autograd function is nothing magical — it is autograd with your chain rule; the second shows that `torch.optim` objects wrap exactly the update rule you wrote by hand in section 2.

```python
import torch

class Square(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return x ** 2

    @staticmethod
    def backward(ctx, grad_out):
        (x,) = ctx.saved_tensors
        return 2.0 * x * grad_out      # d(x^2)/dx, written by hand

x = torch.tensor([0.5, -1.0, 2.0], requires_grad=True)
Square.apply(x).sum().backward()
print("hand-written backward:", x.grad.tolist())

x2 = torch.tensor([0.5, -1.0, 2.0], requires_grad=True)
x2.pow(2).sum().backward()
print("autograd reference:    ", x2.grad.tolist())
assert x.grad.allclose(x2.grad)
print("they agree: a custom Function is just autograd with your chain rule")
```

Both rows print `[1.0, -2.0, 4.0]` — the derivative of x² at (0.5, -1, 2) — so the hand-written backward and PyTorch's own agree exactly, and the final line confirms it. Writing backward rules by hand is precisely what Lesson 2201's custom autograd section develops.

```python
import torch

torch.manual_seed(0)
x = torch.linspace(-1.0, 1.0, 20).reshape(-1, 1)
y = 3.0 * x - 1.0

# The manual update and torch.optim.SGD must produce IDENTICAL results.
w1 = torch.zeros(1, 1, requires_grad=True)
b1 = torch.zeros(1, requires_grad=True)
w2 = torch.zeros(1, 1, requires_grad=True)
b2 = torch.zeros(1, requires_grad=True)
opt = torch.optim.SGD([w2, b2], lr=0.1)

for _ in range(200):
    for (w, b, use_opt) in ((w1, b1, False), (w2, b2, True)):
        loss = (((x @ w + b) - y) ** 2).mean()
        loss.backward()
        if use_opt:
            opt.step()
        else:
            with torch.no_grad():
                w -= 0.1 * w.grad
                b -= 0.1 * b.grad
        w.grad.zero_()
        b.grad.zero_()

print(f"manual: w = {w1.item():.4f}, b = {b1.item():.4f}")
print(f"optim:  w = {w2.item():.4f}, b = {b2.item():.4f}")
assert abs(w1.item() - w2.item()) < 1e-6 and abs(b1.item() - b2.item()) < 1e-6
print("identical: the optimizer object wraps exactly the same update")
```

Both parameter sets land on `w = 3.0000, b = -1.0000` — the same line as section 2 — and the assertion pins the two runs to agreement within 1e-6. If any of this felt like review rather than news, you are ready for the module.

---

## Self-Assessment

- [ ] I can explain what `@torch.no_grad()` changes about a function's behavior — and show it with `requires_grad`
- [ ] I can write a `nn.Module`, count its parameters by hand, and call it on a batch
- [ ] I can write a training loop without `torch.optim` and recover a known linear model
- [ ] I can trace a `.grad_fn` chain and predict what `backward()` writes into `.grad`
- [ ] I can explain why two mathematically identical float32 expressions can differ in their last bits
- [ ] I know which device my tensors live on and what happens when devices are mixed

If any box stays unchecked, the matching section above has the fix.

---

## Estimated Preparation Time

| Situation | Time |
|-----------|------|
| Quick review (all six examples run clean on the first try) | 30 minutes |
| Section 1: Python fluency | 1 hour |
| Section 2: Modules and the training loop | 1.5 hours |
| Section 3: Autograd and graphs | 1 hour |
| Section 4: Kernel thinking | 0.5 hours |
| Section 5: Device awareness | 0.5 hours |
| **Full review** | **4.5 hours** |

---

## Common Gaps

- **"Autograd is an API I call"** — Lesson 2201 treats it as a graph you can inspect. If `.grad_fn` introspection above was new, spend the section 3 practice time before starting.
- **"Decorators and context managers are syntax I copy-paste"** — framework code (and 2201's custom-function material) reads them as behavior. Section 1's practice fixes this fastest.
- **"My mental model is NumPy"** — tensors that record history behave differently from plain arrays. The section 2 loop makes the difference concrete.
- **"GPUs are just faster"** — 2202 and 2203 rest on launches, fusion, and memory hierarchy. Sections 4 and 5 give you the vocabulary.

---

## Preparation Checklist

- [ ] PyTorch installed; `import torch; print(torch.__version__)` works
- [ ] All eight examples in this document run, and their outputs match the prose
- [ ] I can write the four-line training loop from memory
- [ ] I can trace a `.grad_fn` chain by hand and predict leaf gradients
- [ ] I know which device my tensors live on, and I have read a device-mismatch error at least once

---

## Summary

- Module 2200 needs working Python fluency, a from-memory training loop, autograd-as-a-graph, launch-count intuition, and device awareness — every one is checked by a runnable example above.
- The Quick Refresher's two programs preview the module's core ideas: custom backward rules are your chain rule, and optimizers are your update rule.
- Budget **30 minutes** for a clean review or **up to 4.5 hours** for the full pass.
- Then start [2200: Deep Learning Frameworks](./README.md) at [Lesson 2201](./2201-PyTorch-Computational-Graphs.md).

---

## References

### Related Documents

- [2200: Deep Learning Frameworks](./README.md) — the module this page prepares you for
- [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md) — builds on sections 1-3
- [2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md) — builds on section 4
- [2203: CUDA Kernel Programming and GPU Architecture](./2203-CUDA-Kernel-Programming.md) — builds on sections 4-5
- [2100: Calculus for Deep Learning](../2100-calculus/README.md) — the backward-pass math assumed throughout
- [2200: Frameworks - Quiz](./assessment/QUIZ.md) — the knowledge check waiting at the end of the module
- [2200: Frameworks - Practice](./assessment/PRACTICE.md) — the hands-on exercises waiting at the end of the module
- [EXP-2201: PyTorch Computational Graphs](../../../../experiments/EXP_2201_PYTORCH_GRAPHS.md) — the first hands-on companion

### External References

- [PyTorch Tutorials](https://docs.pytorch.org/tutorials/) — official tutorials; nn.Module and optimization walkthroughs
- [CS231n: Backpropagation, Intuitions](https://cs231n.github.io/optimization-2/) — the graph view of the chain rule
- [PyTorch Internals](https://blog.ezyang.com/2019/05/pytorch-internals/) — Edward Z. Yang on tensors, dispatch, and autograd

---

## Next Steps

1. **Run every example above** — reading is not checking; the checks are the runs.
2. **Fix the weakest section first**, using its "If you're not familiar" plan.
3. **Skim the [module overview](./README.md)** to see where each prerequisite gets used.
4. **Start the module:** [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md)

**Related:** [2200: Deep Learning Frameworks](./README.md) · [2201: PyTorch Computational Graphs and Dynamic Execution](./2201-PyTorch-Computational-Graphs.md) · [2202: TensorFlow XLA and Compiler Optimizations](./2202-TensorFlow-XLA-Compilers.md)

**Experiment:** No EXP_22xx overview exists — start from [EXP-2201: PyTorch Computational Graphs](../../../../experiments/EXP_2201_PYTORCH_GRAPHS.md) (the hands-on companion to Lesson 2201).
