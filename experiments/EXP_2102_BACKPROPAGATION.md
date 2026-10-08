---
Document ID: EXP_2102
Title: "EXP-2102: Backpropagation Experiment"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
---

# EXP-2102: Backpropagation Experiment

**Hands-on implementation of backpropagation algorithm**

---

## 🎯 Experiment Overview

**Time:** 45-60 minutes

**Difficulty:** ⭐⭐ Intermediate

**Prerequisites:**

- 2101-Tensor-Algebra.md
- Understanding of derivatives
- Basic Python/PyTorch knowledge

**Learning Objectives:**

- Implement backpropagation from scratch
- Understand gradient flow through neural networks
- Visualize gradients during training
- Compare manual vs automatic differentiation

---

## 📚 Background

Backpropagation is the cornerstone of neural network training. It efficiently computes gradients of the loss function with respect to each weight in the network using the chain rule of calculus.

### The Chain Rule

For a composite function f(g(x)), the derivative is:

```text
df/dx = (df/dg) * (dg/dx)
```

In neural networks, this is applied recursively through layers.

---

## 🔬 Experiment 1: Manual Backpropagation (30 minutes)

### Step 1.1: Simple Linear Network

Create a 2-layer network and implement backpropagation manually.

```python
# File: manual_backprop.py
"""
Manual Backpropagation Implementation
====================================
"""

import numpy as np

class ManualBackpropNN:
    """2-layer neural network with manual backprop"""

    def __init__(self, input_size=2, hidden_size=3, output_size=1):
        # Initialize weights
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros(hidden_size)
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros(output_size)

    def sigmoid(self, x):
        """Sigmoid activation"""
        return 1 / (1 + np.exp(-x))

    def sigmoid_derivative(self, x):
        """Derivative of sigmoid"""
        s = self.sigmoid(x)
        return s * (1 - s)

    def forward(self, X):
        """Forward pass"""
        self.z1 = X @ self.W1 + self.b1
        self.a1 = self.sigmoid(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = self.sigmoid(self.z2)
        return self.a2

    def backward(self, X, y, learning_rate=0.1):
        """Backward pass - manual gradient computation"""
        # Forward
        y_pred = self.forward(X)

        # Compute loss gradient (MSE)
        # Loss = 0.5 * (y - y_pred)^2
        # dL/dy_pred = -(y - y_pred)

        batch_size = X.shape[0]

        # Output layer gradients
        # dL/dz2 = dL/da2 * da2/dz2
        # dL/da2 = -(y - y_pred)
        # da2/dz2 = sigmoid_derivative(z2)

        dL_da2 = -(y - y_pred)
        dL_dz2 = dL_da2 * self.sigmoid_derivative(self.z2)

        # Gradients for W2 and b2
        dL_dW2 = self.a1.T @ dL_dz2 / batch_size
        dL_db2 = np.sum(dL_dz2, axis=0) / batch_size

        # Hidden layer gradients
        # dL/da1 = dL/dz2 @ W2.T
        # dL/dz1 = dL/da1 * da1/dz1

        dL_da1 = dL_dz2 @ self.W2.T
        dL_dz1 = dL_da1 * self.sigmoid_derivative(self.z1)

        # Gradients for W1 and b1
        dL_dW1 = X.T @ dL_dz1 / batch_size
        dL_db1 = np.sum(dL_dz1, axis=0) / batch_size

        # Update weights
        self.W1 -= learning_rate * dL_dW1
        self.b1 -= learning_rate * dL_db1
        self.W2 -= learning_rate * dL_dW2
        self.b2 -= learning_rate * dL_db2

        # Compute loss
        loss = np.mean(0.5 * (y - y_pred) ** 2)

        return loss

    def train(self, X, y, epochs=1000, learning_rate=0.1):
        """Train network"""
        losses = []

        for epoch in range(epochs):
            loss = self.backward(X, y, learning_rate)
            losses.append(loss)

            if epoch % 100 == 0:
                print(f"Epoch {epoch}, Loss: {loss:.6f}")

        return losses

# Test data: XOR problem
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.float32)
y = np.array([[0], [1], [1], [0]], dtype=np.float32)

# Train
model = ManualBackpropNN(input_size=2, hidden_size=4, output_size=1)
print("Training manual backprop network...")
losses = model.train(X, y, epochs=5000, learning_rate=0.5)

# Test
predictions = model.forward(X)
print("\nPredictions:")
for i in range(len(X)):
    print(f"Input: {X[i]}, Target: {y[i][0]}, Predicted: {predictions[i][0]:.3f}")

print(f"\nFinal Loss: {losses[-1]:.6f}")
```

**Checkpoint 1:** ✅ Manual backpropagation working

---

## 🔬 Experiment 2: Compare with AutoGrad (15 minutes)

### Step 2.1: PyTorch Implementation

```python
# File: autograd_comparison.py
"""
Compare manual vs automatic differentiation
"""

import torch
import torch.nn as nn
import numpy as np

class AutoGradNN(nn.Module):
    """Same network using PyTorch autograd"""

    def __init__(self, input_size=2, hidden_size=3, output_size=1):
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.sigmoid(self.linear1(x))
        x = self.sigmoid(self.linear2(x))
        return x

# Convert data to tensors
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# Train with autograd
model_autograd = AutoGradNN(input_size=2, hidden_size=4, output_size=1)
criterion = nn.MSELoss()
optimizer = torch.optim.SGD(model_autograd.parameters(), lr=0.5)

print("Training autograd network...")
losses_autograd = []

for epoch in range(5000):
    optimizer.zero_grad()
    outputs = model_autograd(X_tensor)
    loss = criterion(outputs, y_tensor)
    loss.backward()
    optimizer.step()

    losses_autograd.append(loss.item())

    if epoch % 100 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.6f}")

# Compare
predictions_autograd = model_autograd(X_tensor).detach().numpy()

print("\n=== Comparison ===")
print(f"Manual final loss: {losses[-1]:.6f}")
print(f"AutoGrad final loss: {losses_autograd[-1]:.6f}")
print(f"Difference: {abs(losses[-1] - losses_autograd[-1]):.6f}")
```

---

## 🔬 Experiment 3: Visualize Gradients (15 minutes)

```python
# File: visualize_gradients.py
"""
Visualize gradient flow through network
"""

import matplotlib.pyplot as plt

# Store gradients during training
grad_w1_history = []
grad_w2_history = []

# Modified backward to track gradients
def backward_with_tracking(self, X, y, learning_rate=0.1):
    """Backward with gradient tracking"""
    # Forward
    y_pred = self.forward(X)
    batch_size = X.shape[0]

    # Same manual gradients as before
    dL_dz2 = -(y - y_pred) * self.sigmoid_derivative(self.z2)
    dL_dW2 = self.a1.T @ dL_dz2 / batch_size
    dL_db2 = np.sum(dL_dz2, axis=0) / batch_size

    dL_dz1 = (dL_dz2 @ self.W2.T) * self.sigmoid_derivative(self.z1)
    dL_dW1 = X.T @ dL_dz1 / batch_size
    dL_db1 = np.sum(dL_dz1, axis=0) / batch_size

    self.W1 -= learning_rate * dL_dW1
    self.b1 -= learning_rate * dL_db1
    self.W2 -= learning_rate * dL_dW2
    self.b2 -= learning_rate * dL_db2

    # Store gradient norms
    grad_w1_history.append(np.linalg.norm(dL_dW1))
    grad_w2_history.append(np.linalg.norm(dL_dW2))

    return np.mean(0.5 * (y - y_pred) ** 2)

# Re-train with the tracking variant
model = ManualBackpropNN(input_size=2, hidden_size=4, output_size=1)
tracked_losses = []
for epoch in range(5000):
    tracked_losses.append(model.backward_with_tracking(X, y, learning_rate=0.5))

# Plot gradient flow
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(grad_w1_history, label='W1 gradients')
plt.plot(grad_w2_history, label='W2 gradients')
plt.xlabel('Iteration')
plt.ylabel('Gradient Norm')
plt.title('Gradient Flow During Training')
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(tracked_losses, label='Training Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Loss Curve')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('backprop_results.png')
print("✓ Saved visualization to backprop_results.png")
```

---

## ✅ Experiment Checklist

- [ ] Manual backpropagation implementation
- [ ] XOR problem solved
- [ ] Comparison with AutoGrad
- [ ] Gradient visualization created
- [ ] Loss convergence verified

---

## 🎓 Key Takeaways

1. **Chain Rule is Key** - Backprop is just repeated chain rule application
2. **Gradient Flow** - Gradients must flow backward through all layers
3. **Vanishing Gradients** - Deep networks can have very small gradients in early layers
4. **AutoGrad is Efficient** - Manual computation is error-prone; use AutoGrad in production

---

## 🚀 Next Steps

1. **EXP_2201**: PyTorch Computational Graphs
2. **LAB-003**: LoRA Fine-Tuning
3. **2102-Backpropagation-and-Derivatives.md**: Full theory

---

**Last Updated:** 2026-10-08

**Experiment:** 2102 - Backpropagation

**Time Estimate:** 45-60 minutes

**Difficulty:** ⭐⭐ Intermediate
