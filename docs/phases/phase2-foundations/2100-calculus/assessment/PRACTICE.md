---
Document ID: 2100-PRACTICE
Title: "2100: Calculus - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Intermediate
---

# 2100: Calculus - Practice

## Exercises

### Exercise 1: Compute Derivatives

**Objective:** Implement derivative computation both analytically and using PyTorch autograd.

**Solution:**

```python
import torch

def f(x):
    """Function: f(x) = x³ + 2x² - 5x + 1"""
    return x**3 + 2*x**2 - 5*x + 1

# 1. Analytical derivative (by hand)
# f(x) = x³ + 2x² - 5x + 1
# df/dx = 3x² + 4x - 5

def analytical_derivative(x):
    """Analytical derivative: df/dx = 3x² + 4x - 5"""
    return 3*x**2 + 4*x - 5

# 2. Using PyTorch autograd
def autograd_derivative(x_value):
    """Compute derivative using PyTorch autograd."""
    x = torch.tensor(x_value, requires_grad=True, dtype=torch.float32)
    y = f(x)

    # Compute gradient
    y.backward()

    # Return the gradient
    return x.grad.item()

# Compute derivative at x = 2
x_value = 2.0

# Analytical computation
deriv_analytical = analytical_derivative(x_value)
print(f"Analytical derivative at x=2: df/dx = {deriv_analytical}")

# Autograd computation
deriv_autograd = autograd_derivative(x_value)
print(f"Autograd derivative at x=2: df/dx = {deriv_autograd}")

# Expected output:
# Analytical derivative at x=2: df/dx = 15.0
# Autograd derivative at x=2: df/dx = 15.0

# Explanation:
# f(x) = x³ + 2x² - 5x + 1
# At x=2: f(2) = 8 + 8 - 10 + 1 = 7
# df/dx = 3x² + 4x - 5
# At x=2: df/dx = 3(4) + 4(2) - 5 = 12 + 8 - 5 = 15
```

### Exercise 2: Gradient Descent

**Objective:** Implement gradient descent to minimize f(x) = (x-3)².

**Solution:**

```python
import torch
import matplotlib.pyplot as plt

def loss_function(x):
    """Loss function: L(x) = (x-3)²"""
    return (x - 3)**2

def gradient_descent(start_x, learning_rate, steps, print_progress=True):
    """
    Minimize f(x) = (x-3)² using gradient descent.

    Args:
        start_x: Initial value of x
        learning_rate: Step size for updates
        steps: Number of iterations
        print_progress: Whether to print progress

    Returns:
        Final value of x
    """
    x = torch.tensor(start_x, requires_grad=True, dtype=torch.float32)

    history = []

    for i in range(steps):
        # Compute loss
        loss = loss_function(x)

        # Store history
        history.append((i, x.item(), loss.item()))

        if print_progress and i % (steps // 10) == 0:
            print(f"Step {i:3d}: x = {x.item():7.4f}, loss = {loss.item():7.4f}")

        # Compute gradient (backward pass)
        loss.backward()

        # Update x using gradient descent
        with torch.no_grad():
            x -= learning_rate * x.grad

        # Zero the gradient for next iteration
        x.grad.zero_()

    final_loss = loss_function(x).item()
    print(f"\nFinal result: x = {x.item():.4f}, loss = {final_loss:.6f}")

    return x.item(), history

# Test the implementation
print("=== Gradient Descent on f(x) = (x-3)² ===\n")

# Run gradient descent
result, history = gradient_descent(
    start_x=0.0,
    learning_rate=0.1,
    steps=100
)

# Expected output:
# Final result: x = 3.0000, loss = 0.000000
# The minimum of f(x) = (x-3)² is at x = 3. The error shrinks by a
# factor of 0.8 per step at this learning rate (e' = 0.8·e), so after
# 100 steps it is ~6e-10 - below float32 resolution, which prints as
# exactly 3.0000

# Visualization
plt.figure(figsize=(12, 4))

# Plot 1: Loss landscape
plt.subplot(1, 2, 1)
x_range = torch.linspace(-1, 7, 100)
y_range = loss_function(x_range)
plt.plot(x_range.numpy(), y_range.numpy(), 'b-', linewidth=2, label='f(x) = (x-3)²')
plt.scatter([h[1] for h in history[::10]], [h[2] for h in history[::10]],
            c='red', s=50, zorder=5, label='Gradient descent steps')
plt.xlabel('x')
plt.ylabel('f(x)')
plt.title('Loss Landscape')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 2: Convergence
plt.subplot(1, 2, 2)
steps = [h[0] for h in history]
losses = [h[2] for h in history]
plt.semilogy(steps, losses, 'g-', linewidth=2)
plt.xlabel('Iteration')
plt.ylabel('Loss (log scale)')
plt.title('Convergence')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('gradient_descent_convergence.png', dpi=100)
print("\nVisualization saved to gradient_descent_convergence.png")

# Troubleshooting Tips:
# - If x doesn't converge: Try smaller learning rate (e.g., 0.01)
# - If convergence is slow: Try larger learning rate (e.g., 0.2)
# - If x oscillates: Learning rate is too high, reduce it
# - If x diverges: Learning rate is way too high, reduce significantly
```

### Exercise 3: Partial Derivatives

**Objective:** Compute partial derivatives of multivariate function f(x,y) = x² + y² + 2xy.

**Solution:**

```python
import torch

def f_multi(x, y):
    """Function: f(x,y) = x² + y² + 2xy"""
    return x**2 + y**2 + 2*x*y

# 1. Analytical computation
# f(x,y) = x² + y² + 2xy
# ∂f/∂x = 2x + 2y
# ∂f/∂y = 2y + 2x

def analytical_partial_derivatives(x, y):
    """Compute partial derivatives analytically."""
    df_dx = 2*x + 2*y  # ∂f/∂x
    df_dy = 2*y + 2*x  # ∂f/∂y
    return df_dx, df_dy

# 2. PyTorch autograd computation
def autograd_partial_derivatives(x_value, y_value):
    """Compute partial derivatives using PyTorch autograd."""
    x = torch.tensor(x_value, requires_grad=True, dtype=torch.float32)
    y = torch.tensor(y_value, requires_grad=True, dtype=torch.float32)

    z = f_multi(x, y)

    # Compute gradients
    z.backward()

    return x.grad.item(), y.grad.item()

# Compute at point (x=1, y=2)
x_val, y_val = 1.0, 2.0

print("=== Partial Derivatives of f(x,y) = x² + y² + 2xy ===\n")
print(f"Evaluating at point (x={x_val}, y={y_val})\n")

# Analytical
df_dx_analytical, df_dy_analytical = analytical_partial_derivatives(x_val, y_val)
print("Analytical computation:")
print(f"  ∂f/∂x = 2x + 2y = 2({x_val}) + 2({y_val}) = {df_dx_analytical}")
print(f"  ∂f/∂y = 2y + 2x = 2({y_val}) + 2({x_val}) = {df_dy_analytical}")

# Autograd
df_dx_autograd, df_dy_autograd = autograd_partial_derivatives(x_val, y_val)
print("\nAutograd computation:")
print(f"  ∂f/∂x = {df_dx_autograd}")
print(f"  ∂f/∂y = {df_dy_autograd}")

# Expected output:
# ∂f/∂x = 2(1) + 2(2) = 6
# ∂f/∂y = 2(2) + 2(1) = 6

print("\n" + "="*60)
print("EXPLANATION:")
print("="*60)
print("Function: f(x,y) = x² + y² + 2xy")
print(f"At point: ({x_val}, {y_val})")
print(f"Function value: f({x_val}, {y_val}) = {x_val}² + {y_val}² + 2({x_val})({y_val})")
print(f"                      = {x_val**2} + {y_val**2} + {2*x_val*y_val}")
print(f"                      = {x_val**2 + y_val**2 + 2*x_val*y_val}")
print("\nPartial derivatives:")
print(f"  ∂f/∂x = 2x + 2y = {df_dx_analytical}")
print(f"  ∂f/∂y = 2y + 2x = {df_dy_analytical}")
print("\nInterpretation:")
print(f"  - Increasing x by Δx changes f by approximately {df_dx_analytical}·Δx")
print(f"  - Increasing y by Δy changes f by approximately {df_dy_analytical}·Δy")

# Gradient vector (nabla)
gradient_magnitude = (df_dx_analytical**2 + df_dy_analytical**2)**0.5
print(f"\nGradient magnitude: ||∇f|| = {gradient_magnitude:.4f}")
print(f"Gradient direction: ∇f = ({df_dx_analytical}, {df_dy_analytical})")
```

### Exercise 4: Gradient Descent in 2D

**Objective:** Extend gradient descent to minimize multivariate function.

**Solution:**

```python
import torch
import matplotlib.pyplot as plt
import numpy as np

def loss_2d(x, y):
    """2D loss function: L(x,y) = (x-2)² + (y-3)²"""
    return (x - 2)**2 + (y - 3)**2

def gradient_descent_2d(start_x, start_y, learning_rate, steps):
    """
    Minimize L(x,y) using gradient descent.

    Args:
        start_x: Initial x value
        start_y: Initial y value
        learning_rate: Step size
        steps: Number of iterations

    Returns:
        History of (x, y, loss) values
    """
    x = torch.tensor(start_x, requires_grad=True, dtype=torch.float32)
    y = torch.tensor(start_y, requires_grad=True, dtype=torch.float32)

    history = []

    for i in range(steps):
        # Compute loss
        loss = loss_2d(x, y)

        # Store history
        history.append((x.item(), y.item(), loss.item()))

        # Compute gradients
        loss.backward()

        # Update parameters
        with torch.no_grad():
            x -= learning_rate * x.grad
            y -= learning_rate * y.grad

        # Zero gradients
        x.grad.zero_()
        y.grad.zero_()

    return history

# Run 2D gradient descent
print("=== 2D Gradient Descent on f(x,y) = (x-2)² + (y-3)² ===\n")

history = gradient_descent_2d(
    start_x=0.0,
    start_y=0.0,
    learning_rate=0.1,
    steps=100
)

# Print final result
final_x, final_y, final_loss = history[-1]
print(f"Starting point: (0.0, 0.0)")
print(f"Final point: ({final_x:.4f}, {final_y:.4f})")
print(f"Final loss: {final_loss:.6f}")
print(f"Expected minimum: (2.0, 3.0) with loss = 0.0")

# Visualization
fig = plt.figure(figsize=(14, 5))

# Plot 1: Contour plot with optimization path
ax1 = fig.add_subplot(1, 2, 1)
x_range = np.linspace(-1, 5, 100)
y_range = np.linspace(-1, 5, 100)
X, Y = np.meshgrid(x_range, y_range)
Z = (X - 2)**2 + (Y - 3)**2

contour = ax1.contour(X, Y, Z, levels=20, cmap='viridis')
ax1.clabel(contour, inline=True, fontsize=8)
ax1.plot([h[0] for h in history], [h[1] for h in history],
         'ro-', linewidth=2, markersize=4, label='Optimization path')
ax1.plot(final_x, final_y, 'g*', markersize=15, label='Final point')
ax1.plot(2, 3, 'y*', markersize=15, label='True minimum')
ax1.set_xlabel('x')
ax1.set_ylabel('y')
ax1.set_title('2D Gradient Descent Path')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Loss convergence
ax2 = fig.add_subplot(1, 2, 2)
# History tuples are (x, y, loss) - the iteration index comes from
# the list length, not h[0] (and range() yields ints, which are not
# subscriptable)
steps = list(range(len(history)))
losses = [h[2] for h in history]
ax2.plot(steps, losses, 'b-', linewidth=2)
ax2.set_xlabel('Iteration')
ax2.set_ylabel('Loss')
ax2.set_title('Loss Convergence')
ax2.grid(True, alpha=0.3)
ax2.set_yscale('log')

plt.tight_layout()
plt.savefig('gradient_descent_2d.png', dpi=100)
print("\nVisualization saved to gradient_descent_2d.png")

# Expected output:
# Final point should be close to (2.0, 3.0)
# Final loss should be close to 0.0
```

### Exercise 5: Chain Rule

**Objective:** Implement and verify the chain rule for composite functions.

**Solution:**

```python
import torch

def g(x):
    """Inner function: g(x) = x²"""
    return x**2

def h(u):
    """Outer function: h(u) = 2u + 1"""
    return 2*u + 1

def f_composite(x):
    """Composite function: f(x) = h(g(x)) = 2(x²) + 1"""
    return h(g(x))

# 1. Analytical computation using chain rule
# f(x) = h(g(x)) where g(x) = x² and h(u) = 2u + 1
# Chain rule: df/dx = (dh/du) · (dg/dx)
# dh/du = 2
# dg/dx = 2x
# df/dx = 2 · 2x = 4x

def analytical_chain_rule(x):
    """Compute derivative using chain rule analytically."""
    dg_dx = 2*x  # Derivative of g(x) = x²
    dh_du = 2    # Derivative of h(u) = 2u + 1
    return dh_du * dg_dx  # Chain rule: df/dx = (dh/du)(dg/dx)

# 2. PyTorch autograd computation
def autograd_chain_rule(x_value):
    """Compute derivative using autograd."""
    x = torch.tensor(x_value, requires_grad=True, dtype=torch.float32)
    y = f_composite(x)
    y.backward()
    return x.grad.item()

# Test at x = 3
x_value = 3.0

print("=== Chain Rule for f(x) = h(g(x)) where g(x)=x², h(u)=2u+1 ===\n")
print(f"Evaluating at x = {x_value}\n")

print("Function decomposition:")
print("  g(x) = x²")
print("  h(u) = 2u + 1")
print("  f(x) = h(g(x)) = 2(x²) + 1\n")

print("Analytical computation (Chain Rule):")
print("  dg/dx = 2x")
print("  dh/du = 2")
print(f"  df/dx = (dh/du) · (dg/dx) = 2 · 2({x_value}) = {analytical_chain_rule(x_value)}\n")

deriv_autograd = autograd_chain_rule(x_value)
print(f"Autograd computation: df/dx = {deriv_autograd}")

# Verify with direct differentiation
# f(x) = 2x² + 1
# df/dx = 4x
# At x=3: df/dx = 4(3) = 12

# Compute the expected value from x_value instead of hardcoding 12,
# so the verification stays honest if you change the evaluation point
expected = 4 * x_value
print(f"\nDirect differentiation: df/dx = 4x = 4({x_value}) = {expected}")
print(f"Result verification: {abs(analytical_chain_rule(x_value) - expected) < 1e-6}")

# Expected output:
# All methods should yield df/dx = 12 at x = 3
```

---

## Summary

This practice guide covers:

1. **Derivatives:** Computing derivatives analytically and with autograd
2. **Gradient Descent:** Implementing optimization to find minima
3. **Partial Derivatives:** Computing gradients of multivariate functions
4. **2D Gradient Descent:** Extending optimization to multiple dimensions
5. **Chain Rule:** Understanding and implementing the chain rule

**Expected Learning Outcomes:**
- Understand the mathematical foundation of derivatives and gradients
- Implement automatic differentiation using PyTorch
- Apply gradient descent for optimization
- Compute and interpret partial derivatives
- Use the chain rule for composite functions
