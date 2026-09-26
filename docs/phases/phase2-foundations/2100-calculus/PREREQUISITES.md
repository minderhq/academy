---
Document ID: 2100-PREREQUISITES
Title: "2100: Calculus for Deep Learning - Prerequisites"
Phase: 2
Module: 2100
Last Updated: 2026-09-26
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes (quick review) - 6.5 hours (full review)
Prerequisites: See module README
Related: See module README
Tags: math, prerequisites, preparation
---

# 2100: Calculus for Deep Learning - Prerequisites

**Verify you're ready before starting the module.**

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

Module 2100 turns math you've seen on paper into code you can run. It assumes you can:

- **Work with vectors and matrices** — dot products, matrix multiplication, shapes
- **Differentiate** — derivatives of polynomials, the chain rule on composite functions
- **Read Python** — functions, loops, list literals; NumPy exposure helps but is not required
- **(Helpful) run PyTorch** — the module teaches tensors from zero, but fluency speeds you up

Every section below has a runnable example. **Run them, don't just read them** — the lessons build directly on each one.

---

## Required Knowledge

### 1. Linear Algebra in Code

**What you should know:**

- Matrix multiplication as shape algebra: `(m, n) @ (n, k) -> (m, k)`
- The transpose identity `(A @ B)^T == B^T @ A^T` — it decides how gradient formulas are written
- Associativity `(A @ B) @ W == A @ (B @ W)` — it decides how you order big computations for speed

**Example: shapes first, identities second**

```python
import torch

# Shapes first: every tensor operation in this module is shape algebra.
a = torch.tensor([[1.0, 2.0],
                  [3.0, 4.0]])          # (2, 2)
x = torch.tensor([5.0, 6.0])            # (2,)
W = torch.tensor([[0.5, 0.0, 1.0],
                  [1.5, 2.0, 0.0]])     # (2, 3)

y = x @ a        # (2,) @ (2, 2) -> (2,)
z = a @ W        # (2, 2) @ (2, 3) -> (2, 3)
print(a.shape, x.shape, W.shape)
print("y = x @ a:", y.tolist())
print("z = a @ W shape:", tuple(z.shape))

# The one identity worth memorizing: (A @ B)^T == B^T @ A^T
b = torch.tensor([[2.0, 0.0],
                  [1.0, 3.0]])
assert torch.allclose((a @ b).T, b.T @ a.T)
print("transpose identity holds: (A @ B)^T == B^T @ A^T")

# Associativity decides how you order big computations
left = (a @ b) @ W      # (2,2) intermediate, then (2,3)
right = a @ (b @ W)     # (2,3) intermediates
assert torch.allclose(left, right)
print("associative: (A @ B) @ W == A @ (B @ W)")
```

If you can predict `y` and `z`'s shapes before running, you're ready for the shape discipline Lesson 2101 demands.

**If you're not familiar:**

- Review: [Mathematics for Machine Learning](https://mml-book.github.io/), Chapter 2 (free PDF), or the [Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) series by 3Blue1Brown
- Practice: Predict the shapes of `a @ b` and `b @ a` on paper, then check
- Estimated time: 1.5 hours

---

### 2. Derivatives: Numeric and Analytic

**What you should know:**

- The derivative as slope; closed-form rules (power rule, linearity)
- The central-difference formula: `f'(x) ≈ (f(x+h) - f(x-h)) / 2h`
- That this numeric check is how real engineers debug gradient code — Lesson 2102 uses it against autograd

**Example: closed form vs central difference**

```python
# f(x) = 3x^2 + 2x  ->  f'(x) = 6x + 2
def f(x):
    return 3 * x**2 + 2 * x

def f_prime(x):                 # the closed form
    return 6 * x + 2

def numeric_derivative(fn, x, h=1e-6):
    """Central difference: (f(x+h) - f(x-h)) / 2h."""
    return (fn(x + h) - fn(x - h)) / (2 * h)

points = (-2.0, 0.0, 1.5, 3.0)
worst = 0.0
for x in points:
    nd = numeric_derivative(f, x)
    ad = f_prime(x)
    worst = max(worst, abs(nd - ad))
    print(f"x = {x:>4}: numeric {nd:9.5f} | analytic {ad:5.2f} | err {abs(nd - ad):.1e}")
print(f"max abs error across all checks: {worst:.1e}")
```

The residual errors (~1e-9) are floating-point rounding, not math — for a quadratic the central difference is exact in real arithmetic.

**If you're not familiar:**

- Review: [Essence of Calculus](https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr) (3Blue1Brown), chapters 1-2
- Practice: Repeat the check for `f(x) = x**3` and explain why the error is larger
- Estimated time: 1 hour

---

### 3. Partial Derivatives and Gradients

**What you should know:**

- A partial derivative holds every other parameter fixed
- The gradient is the vector of partials — it points where the function rises fastest
- Loss surfaces are functions of many parameters; gradient descent follows this vector

**Example: a two-parameter loss, differentiated by hand**

```python
# A two-parameter loss on ONE sample: L(w1, w2) = (w1*x1 + w2*x2 - y)^2
x1, x2, y = 2.0, -1.0, 3.0

def loss(w1, w2):
    return (w1 * x1 + w2 * x2 - y) ** 2

w1, w2 = 0.5, 1.5
pred = w1 * x1 + w2 * x2 - y
# Closed form: dL/dw1 = 2*(pred)*x1 and dL/dw2 = 2*(pred)*x2
g1 = 2 * pred * x1
g2 = 2 * pred * x2

h = 1e-6
g1_num = (loss(w1 + h, w2) - loss(w1 - h, w2)) / (2 * h)
g2_num = (loss(w1, w2 + h) - loss(w1, w2 - h)) / (2 * h)

print(f"residual (pred - y) at w = ({w1}, {w2}): {pred}")
print(f"closed form: dL/dw1 = {g1}, dL/dw2 = {g2}")
print(f"finite diff: dL/dw1 = {g1_num:.4f}, dL/dw2 = {g2_num:.4f}")
print(f"the gradient vector [{g1}, {g2}] points where L rises fastest")
```

Note the pattern `2 * residual * input` — the same pattern that falls out of the softmax + cross-entropy derivation in Lesson 2102.

**If you're not familiar:**

- Review: [Mathematics for Machine Learning](https://mml-book.github.io/), Chapter 5 (Vector Calculus, free PDF)
- Practice: Add a third parameter `w3` multiplying `x3 = 1.0` (a bias!) and derive its gradient
- Estimated time: 1 hour

---

### 4. The Chain Rule, Three Ways

**What you should know:**

- The chain rule composes derivatives through intermediate steps
- A computational graph makes those steps explicit — each edge is one application of the rule
- Analytic, numeric, and autograd answers must all agree; when they don't, one of them has a bug

**Example: one function, three independent derivations**

```python
import torch

# The graph Lesson 2102 opens with: y = ((x + 1) * 2)^2 - 4
def y_of(x):
    return ((x + 1) * 2) ** 2 - 4

# Analytic: dy/dx = 2*((x+1)*2) * 2 = 8*(x + 1)
def dydx(x):
    return 8 * (x + 1)

x = 2.0
analytic = dydx(x)                      # 8 * 3 = 24

h = 1e-6
numeric = (y_of(x + h) - y_of(x - h)) / (2 * h)

xt = torch.tensor(2.0, requires_grad=True)
y_of(xt).backward()
autograd = xt.grad.item()

print(f"analytic: dy/dx = {analytic}")
print(f"numeric:  dy/dx = {numeric:.5f}")
print(f"autograd: dy/dx = {autograd}")
assert abs(analytic - numeric) < 1e-3
assert abs(analytic - autograd) < 1e-3
print("three methods agree: the chain rule is the engine of backprop")
```

**If you're not familiar:**

- Review: [CS231n Notes](https://cs231n.github.io/optimization-2/), "Backpropagation, Intuitions"
- Practice: Recompute `dy/dx` by hand at `x = 0` and `x = -1`, then confirm with the block
- Estimated time: 1 hour

---

### 5. PyTorch Tensor Fluency (Helpful but not required)

**What you should know:**

- Tensors carry shapes and dtypes; operations are shape-aware
- Broadcasting: `(3, 1) + (1, 4) -> (3, 4)` — the outer-product pattern everywhere in ML
- `reshape` preserves element count; float-to-int casts truncate

**Example: broadcasting and dtype discipline**

```python
import torch

# Tensors are not lists: shape-aware operations are the whole point.
rows = torch.arange(3.0).reshape(3, 1)      # column (3, 1)
cols = torch.arange(4.0).reshape(1, 4)      # row    (1, 4)

grid = rows + cols                          # broadcasting -> (3, 4)
print("broadcast grid of shape", tuple(grid.shape), ":")
print(grid)

# reshape must preserve the element count
v = torch.arange(12.0)
m = v.reshape(3, 4)
assert m.numel() == v.numel()
print(f"{v.numel()} elements -> shape {tuple(m.shape)}")

# dtype discipline: casting float -> int truncates
print("float->int cast truncates:", torch.tensor([1.7, 2.5]).to(torch.int64).tolist())
```

**If you're not familiar:**

- Review: [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md) — it starts tensor knowledge from zero
- Practice: Build a 5x5 grid where every cell holds `row + col` using only broadcasting
- Estimated time: 2 hours

---

## Quick Refresher

### MSE Gradient: Autograd vs Closed Form

```python
import torch

# Tiny regression: y = 2x + 1, model starts at w = 0, b = 0
x = torch.linspace(-1.0, 1.0, 5)
y = 2.0 * x + 1.0

w = torch.tensor(0.0, requires_grad=True)
b = torch.tensor(0.0, requires_grad=True)

pred = w * x + b
loss = ((pred - y) ** 2).mean()
loss.backward()

# Closed form at w = 0, b = 0: predictions are 0, so residual = -y
dw = (2 * (-y) * x).mean()
db = (2 * (-y)).mean()

assert torch.allclose(w.grad, dw) and torch.allclose(b.grad, db)
print(f"autograd: dL/dw = {w.grad.item():.4f}, dL/db = {b.grad.item():.4f}")
print(f"closed:   dL/dw = {dw.item():.4f}, dL/db = {db.item():.4f}")
```

One `backward()` call reproduces the full closed form — `w.grad` and `b.grad` both hold `-2.0000`.

### A Reusable Gradient Checker

```python
import torch

def grad_check(fn, tensor, h=1e-5, tol=1e-4):
    """Compare autograd gradients with central finite differences.

    The numeric pass runs in float64: float32 rounds away the
    tiny signal a central difference is built from.
    """
    t64 = tensor.detach().to(torch.float64)
    numeric = torch.zeros_like(t64)
    with torch.no_grad():
        for idx in range(t64.numel()):
            orig = t64[idx].item()
            t64[idx] = orig + h
            fp = fn(t64).item()
            t64[idx] = orig - h
            fm = fn(t64).item()
            t64[idx] = orig
            numeric[idx] = (fp - fm) / (2 * h)
    fn(tensor).backward()
    return bool(torch.allclose(tensor.grad.to(torch.float64), numeric, atol=tol))

w = torch.tensor([0.5, -1.0], requires_grad=True)
weights = torch.tensor([2.0, 4.0])
assert grad_check(lambda w: (w * weights).sum(), w)
print("grad_check passed; gradients:", w.grad.tolist())
```

The float64 detail is not cosmetic: try `h = 1e-6` on the original float32 tensor and the check reports False — float32 rounding destroys the ~1e-6 signal a central difference is built from. That's exactly why `torch.autograd.gradcheck` insists on double precision.

---

## Self-Assessment

Before starting, can you:

- [ ] Predict the shape of `x @ W` before computing it — and be right?
- [ ] Verify `(A @ B)^T == B^T @ A^T` numerically and say why it matters for gradient formulas?
- [ ] Compute a central-difference derivative and explain what limits its accuracy?
- [ ] Compute a partial derivative and assemble the gradient vector?
- [ ] Differentiate a composite function three ways — analytic, numeric, autograd — and get one answer?
- [ ] Build an outer-product grid with broadcasting?
- [ ] Check autograd gradients against finite differences in float64?

**If you answered NO to any question:**
Review the suggested materials above. Total review time: 6.5 hours

**If you answered YES to all questions:**
You're ready! Start with [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md)

---

## Estimated Preparation Time

- **If familiar with prerequisites:** 0 hours (ready to start)
- **If need review:** 6.5 hours (1.5 + 1 + 1 + 1 + 2, spread over 2-3 days)

---

## Common Gaps

### Gap 1: Matrix algebra on paper, not in code

**Symptoms:** Can multiply matrices by hand but freeze when shapes appear in code

**Fix:**
1. Run the Section 1 block and predict each shape before printing (30 minutes)
2. Write `x @ a` for five random `(2,)`/`(2, 2)` pairs, predicting the result each time (30 minutes)
3. Verify the transpose identity with your own 2x2 matrices (30 minutes)

### Gap 2: Calculus stopped at single variable

**Symptoms:** Comfortable with `f'(x)` but no reflex for gradients of multi-parameter losses

**Fix:**
1. Run the Section 3 block; trace which parameter each finite difference perturbs (30 minutes)
2. Add the `w3` bias parameter and derive its gradient by hand (30 minutes)

### Gap 3: Chain rule as a formula, not a graph

**Symptoms:** Can recite the rule but can't say which intermediate gets differentiated against which

**Fix:**
1. Run the Section 4 block; write `u = x + 1`, `v = 2u`, `w = v^2`, `y = w - 4` and differentiate edge by edge (30 minutes)
2. Compare with the computational graph Lesson 2102 opens with (30 minutes)

### Gap 4: Never used autograd or gradient checking

**Symptoms:** `backward()` feels like magic; broken gradients go unnoticed

**Fix:**
1. Run both Quick Refresher blocks (30 minutes)
2. Break the closed form on purpose (drop the factor of 2) and watch `grad_check` catch it (30 minutes)

---

## Preparation Checklist

Use this checklist to verify you're ready:

**Linear Algebra**
- [ ] Can predict matmul output shapes
- [ ] Can verify the transpose identity numerically
- [ ] Understand why associativity matters for computation order

**Derivatives**
- [ ] Can differentiate polynomials in closed form
- [ ] Can implement the central-difference formula
- [ ] Know that residual errors are float rounding, not math

**Gradients & the Chain Rule**
- [ ] Can compute partial derivatives of a two-parameter loss
- [ ] Can differentiate a composite function analytically, numerically, and with autograd
- [ ] Can check autograd gradients against finite differences in float64

**Tools**
- [ ] Can broadcast `(3, 1) + (1, 4)` and predict the result
- [ ] Know `reshape` preserves element count
- [ ] Know float-to-int casts truncate

---

## Summary

- Module 2100 assumes **linear algebra in code, derivatives both numeric and analytic, partials into gradients, and the chain rule** — plus helpful PyTorch fluency.
- Each area ships a runnable example (shape algebra with identity checks, closed-form vs central difference, a two-parameter loss gradient, one function differentiated three ways, broadcasting and dtype discipline) — run them, don't just read them.
- **Full review takes 6.5 hours** (1.5 + 1 + 1 + 1 + 2); a quick skim of this guide takes ~30 minutes.
- Use the Self-Assessment to find your gaps; Common Gaps gives a fix plan per gap.
- Everything here is reused inside the module: shapes become 2101's tensor algebra, the central difference becomes 2102's gradient checker, and the three-way chain-rule agreement becomes the autograd contract.

---

## References

### Related Documents

- [2100: Calculus for Deep Learning](./README.md) — module overview and learning path
- [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md) — where Section 1 goes deep
- [2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md) — where Sections 2-4 become the backward pass
- [2100: Calculus - Quiz](./assessment/QUIZ.md) — where this knowledge gets checked

### External References

- [Mathematics for Machine Learning](https://mml-book.github.io/) — Deisenroth, Faisal & Ong; free PDF (Sections 1, 3)
- [Deep Learning](https://www.deeplearningbook.org/) — Goodfellow, Bengio & Courville; Chapter 2 (Section 1)
- [CS231n Notes](https://cs231n.github.io/optimization-2/) — Stanford; backpropagation intuitions (Section 4)
- [The Matrix Calculus You Need For Deep Learning](https://explained.ai/matrix-calculus/) — Parr & Howard (Sections 2-3)
- [Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) — 3Blue1Brown (Section 1)
- [Essence of Calculus](https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr) — 3Blue1Brown (Sections 2, 4)

---

## Next Steps

1. **Gaps found?** Work the fix plans in [Common Gaps](#common-gaps), then re-run the [Self-Assessment](#self-assessment).
2. **Ready?** Start the module with [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md).
3. **After the module:** take the [2100: Calculus - Quiz](./assessment/QUIZ.md), then the [2100: Calculus - Practice](./assessment/PRACTICE.md).

**Related:** [2100: Calculus for Deep Learning](./README.md) · [2101: Tensor Algebra and Linear Algebra for AI](./2101-Tensor-Algebra.md) · [2102: Backpropagation and Automatic Differentiation](./2102-Backpropagation-and-Derivatives.md)

**Experiment:** No EXP_21xx prerequisites exist — nearest relevant: [EXP-2101: Tensor Algebra](../../../../experiments/EXP_2101_TENSOR_ALGEBRA.md) (the hands-on companion this guide prepares you for).
