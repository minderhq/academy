---
Document ID: PROJECT-002
Title: "CAPSTONE PROJECT-002: Train Neural Network from Scratch"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
---

# CAPSTONE PROJECT-002: Train Neural Network from Scratch

**Mathematics meets implementation - Train your first model**

---

## 🎯 Project Overview

Build and train a neural network completely from scratch, implementing:
- Manual backpropagation with the chain rule
- Custom tensor operations and autograd
- Training loops with optimization algorithms
- Evaluation and visualization of results
- Comparison with framework implementations

**Estimated Time:** 15-20 hours
**Difficulty:** ⭐⭐ Intermediate

---

## 📋 Prerequisites

Complete these before starting:
- ✅ EXP 2101: Tensor Algebra
- ✅ EXP 2102: Backpropagation
- ✅ EXP 2201: PyTorch Computational Graphs
- ✅ CHEAT-SHEET-002: Python AI

---

## 🏗️ Project Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Custom Deep Learning Framework            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Tensor    │  │   Autograd  │  │      Layers         │  │
│  │   Library   │  │   Engine    │  │  (Linear, Conv, etc) │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │              │
│         └────────────────┴─────────────────────┘              │
│                            │                                  │
│                            ▼                                  │
│                 ┌──────────────────┐                          │
│                 │   Neural Network │                          │
│                 │      Module      │                          │
│                 └────────┬─────────┘                          │
│                          │                                    │
│                          ▼                                    │
│                 ┌──────────────────┐                          │
│                 │    Training      │                          │
│                 │      Loop        │                          │
│                 └────────┬─────────┘                          │
│                          │                                    │
│                          ▼                                    │
│                 ┌──────────────────┐                          │
│                 │    Evaluation    │                          │
│                 │   & Visualization │                          │
│                 └──────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Tensor Library (4 hours)

### 1.1 Implement Basic Tensor Operations

```python
# File: tensor.py
"""
Custom Tensor Library with Autograd
====================================
"""

import numpy as np
from typing import Callable
import functools

class Tensor:
    """
    Custom Tensor class with automatic differentiation support
    """

    def __init__(self, data: np.ndarray, requires_grad: bool = False,
                 _children: tuple | None = None, _op: str | None = None):
        self.data = np.array(data, dtype=np.float32)
        self.requires_grad = requires_grad
        self.grad: Tensor | None = None

        # Computational graph tracking
        self._backward: Callable = lambda: None
        self._prev = set() if _children is None else set(_children)
        self._op = _op

    @property
    def shape(self):
        return self.data.shape

    @property
    def ndim(self):
        return self.data.ndim

    def __repr__(self):
        return f"Tensor(shape={self.shape}, requires_grad={self.requires_grad})"

    # ========== Basic Operations ==========

    def __add__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data + other.data,
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op='+'
        )

        def _backward():
            if self.requires_grad:
                self.grad = self.grad + out.grad if self.grad else out.grad
            if other.requires_grad:
                other.grad = other.grad + out.grad if other.grad else out.grad

        out._backward = _backward
        return out

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data * other.data,
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op='*'
        )

        def _backward():
            if self.requires_grad:
                self.grad = self.grad + other.data * out.grad.data if self.grad else other.data * out.grad.data
            if other.requires_grad:
                other.grad = other.grad + self.data * out.grad.data if other.grad else self.data * out.grad.data

        out._backward = _backward
        return out

    def __rmul__(self, other):
        return self.__mul__(other)

    def __matmul__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data @ other.data,
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op='@'
        )

        def _backward():
            if self.requires_grad:
                self.grad = self.grad + (out.grad.data @ other.data.T) if self.grad else (out.grad.data @ other.data.T)
            if other.requires_grad:
                other.grad = other.grad + (self.data.T @ out.grad.data) if other.grad else (self.data.T @ out.grad.data)

        out._backward = _backward
        return out

    def __pow__(self, power):
        assert isinstance(power, (int, float)), "Power must be scalar"
        out = Tensor(
            self.data ** power,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op=f'**{power}'
        )

        def _backward():
            if self.requires_grad:
                self.grad = self.grad + (power * self.data ** (power - 1) * out.grad.data) if self.grad else (power * self.data ** (power - 1) * out.grad.data)

        out._backward = _backward
        return out

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other)

    def __truediv__(self, other):
        return self * (other ** -1)

    # ========== Activation Functions ==========

    def relu(self):
        """ReLU activation: max(0, x)"""
        out = Tensor(
            np.maximum(0, self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='relu'
        )

        def _backward():
            if self.requires_grad:
                mask = (self.data > 0).astype(np.float32)
                grad = out.grad.data * mask if out.grad else np.zeros_like(self.data)
                self.grad = self.grad + grad if self.grad else grad

        out._backward = _backward
        return out

    def sigmoid(self):
        """Sigmoid activation: 1 / (1 + exp(-x))"""
        sig = 1 / (1 + np.exp(-self.data))
        out = Tensor(
            sig,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='sigmoid'
        )

        def _backward():
            if self.requires_grad:
                grad = sig * (1 - sig) * out.grad.data if out.grad else np.zeros_like(self.data)
                self.grad = self.grad + grad if self.grad else grad

        out._backward = _backward
        return out

    def tanh(self):
        """Tanh activation"""
        t = np.tanh(self.data)
        out = Tensor(
            t,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='tanh'
        )

        def _backward():
            if self.requires_grad:
                grad = (1 - t ** 2) * out.grad.data if out.grad else np.zeros_like(self.data)
                self.grad = self.grad + grad if self.grad else grad

        out._backward = _backward
        return out

    # ========== Reduction Operations ==========

    def sum(self):
        """Sum all elements"""
        out = Tensor(
            np.array([self.data.sum()]),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='sum'
        )

        def _backward():
            if self.requires_grad:
                grad = np.ones_like(self.data) * out.grad.data if out.grad else np.zeros_like(self.data)
                self.grad = self.grad + grad if self.grad else grad

        out._backward = _backward
        return out

    def mean(self):
        """Mean of all elements"""
        return self.sum() / self.data.size

    # ========== Utility Methods ==========

    def zero_grad(self):
        """Reset gradients to zero"""
        self.grad = None

    def backward(self):
        """Compute gradients using reverse-mode autograd"""
        if not self.requires_grad:
            raise RuntimeError("Called backward on non-requires_grad tensor")

        # Topological sort of computational graph
        topo = []
        visited = set()

        def build_topo(node):
            if node not in visited:
                visited.add(node)
                for child in node._prev:
                    build_topo(child)
                topo.append(node)

        build_topo(self)

        # Initialize gradient
        self.grad = Tensor(np.ones_like(self.data))

        # Backpropagate
        for node in reversed(topo):
            node._backward()

    @staticmethod
    def zeros(*shape):
        return Tensor(np.zeros(shape))

    @staticmethod
    def ones(*shape):
        return Tensor(np.ones(shape))

    @staticmethod
    def randn(*shape):
        return Tensor(np.random.randn(*shape) * 0.01)

    def item(self):
        """Return scalar value"""
        return self.data.item()

    def numpy(self):
        """Convert to numpy array"""
        return self.data
```

### ✅ Phase 1 Checklist
- [ ] Tensor class implemented
- [ ] Basic operations working (+, -, *, /)
- [ ] Matrix multiplication working
- [ ] Activation functions implemented
- [ ] Autograd (backward) working
- [ ] Unit tests passing

---

## Phase 2: Neural Network Module (3 hours)

### 2.1 Implement Neural Network Components

```python
# File: nn.py
"""
Neural Network Module
=====================
"""


from tensor import Tensor
import numpy as np

class Module:
    """Base class for all neural network modules"""

    def __init__(self):
        self.parameters: list[Tensor] = []
        self.training = True

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    def forward(self, *args, **kwargs):
        raise NotImplementedError

    def parameters(self) -> list[Tensor]:
        return []

    def zero_grad(self):
        for p in self.parameters:
            p.zero_grad()

    def train(self):
        self.training = True
        for m in self.modules():
            m.training = True

    def eval(self):
        self.training = False
        for m in self.modules():
            m.training = False

    def modules(self):
        """Return all child modules"""
        for name, module in self.__dict__.items():
            if isinstance(module, Module):
                yield module

class Linear(Module):
    """Linear (fully connected) layer"""

    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features

        # Xavier initialization
        std = np.sqrt(2.0 / (in_features + out_features))
        self.weight = Tensor(np.random.randn(in_features, out_features) * std, requires_grad=True)
        self.parameters = [self.weight]

        if bias:
            self.bias = Tensor(np.zeros(out_features), requires_grad=True)
            self.parameters.append(self.bias)
        else:
            self.bias = None

    def forward(self, x: Tensor) -> Tensor:
        """y = xW + b"""
        out = x @ self.weight
        if self.bias is not None:
            out = out + self.bias
        return out

    def __repr__(self):
        return f"Linear(in_features={self.in_features}, out_features={self.out_features})"

class Conv2D(Module):
    """2D Convolution layer"""

    def __init__(self, in_channels: int, out_channels: int,
                 kernel_size: int, stride: int = 1, padding: int = 0):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding

        # Initialize weights
        std = np.sqrt(2.0 / (in_channels * kernel_size * kernel_size))
        self.weight = Tensor(
            np.random.randn(out_channels, in_channels, kernel_size, kernel_size) * std,
            requires_grad=True
        )
        self.bias = Tensor(np.zeros(out_channels), requires_grad=True)
        self.parameters = [self.weight, self.bias]

    def forward(self, x: Tensor) -> Tensor:
        """Convolution operation"""
        # Simplified implementation (for educational purposes)
        # In production, use im2col or specialized libraries
        batch, in_ch, h_in, w_in = x.shape

        # Apply padding
        if self.padding > 0:
            x_padded = np.pad(x.data, ((0,0), (0,0), (self.padding, self.padding),
                                       (self.padding, self.padding)), mode='constant')
        else:
            x_padded = x.data

        h_out = (h_in + 2 * self.padding - self.kernel_size) // self.stride + 1
        w_out = (w_in + 2 * self.padding - self.kernel_size) // self.stride + 1

        # Manual convolution
        output = np.zeros((batch, self.out_channels, h_out, w_out))

        for b in range(batch):
            for oc in range(self.out_channels):
                for ic in range(self.in_channels):
                    for i in range(h_out):
                        for j in range(w_out):
                            h_start = i * self.stride
                            h_end = h_start + self.kernel_size
                            w_start = j * self.stride
                            w_end = w_start + self.kernel_size

                            patch = x_padded[b, ic, h_start:h_end, w_start:w_end]
                            output[b, oc, i, j] += np.sum(patch * self.weight.data[oc, ic])

                # Add bias
                output[b, oc] += self.bias.data[oc]

        return Tensor(output, requires_grad=x.requires_grad)

class Sequential(Module):
    """Sequential container for modules"""

    def __init__(self, *modules: Module):
        super().__init__()
        self.modules_list = list(modules)

        # Collect all parameters
        for module in self.modules_list:
            if isinstance(module, Module):
                self.parameters.extend(module.parameters)

    def forward(self, x: Tensor) -> Tensor:
        for module in self.modules_list:
            x = module(x)
        return x

    def modules(self):
        for module in self.modules_list:
            if isinstance(module, Module):
                yield module
                yield from module.modules()

    def __repr__(self):
        module_strs = [str(m) for m in self.modules_list]
        return f"Sequential(\n  " + "\n  ".join(module_strs) + "\n)"

# ========== Activation Functions as Modules ==========

class ReLU(Module):
    def forward(self, x: Tensor) -> Tensor:
        return x.relu()

class Sigmoid(Module):
    def forward(self, x: Tensor) -> Tensor:
        return x.sigmoid()

class Tanh(Module):
    def forward(self, x: Tensor) -> Tensor:
        return x.tanh()

# ========== Loss Functions ==========

class MSELoss(Module):
    """Mean Squared Error Loss"""

    def forward(self, pred: Tensor, target: Tensor) -> Tensor:
        """L = (1/n) * sum((pred - target)^2)"""
        diff = pred - target
        return (diff * diff).mean()

class CrossEntropyLoss(Module):
    """Cross Entropy Loss (with softmax)"""

    def __init__(self):
        super().__init__()

    def forward(self, logits: Tensor, target: Tensor) -> Tensor:
        """
        Args:
            logits: (batch, num_classes) raw scores
            target: (batch,) integer class labels
        """
        # Softmax
        exp_logits = Tensor(np.exp(logits.data - logits.data.max(axis=1, keepdims=True)))
        sum_exp = exp_logits.sum(axis=1).data.reshape(-1, 1)
        probs = exp_logits / Tensor(sum_exp)

        # Negative log likelihood
        batch_size = logits.shape[0]
        loss = Tensor(0.0)

        for i in range(batch_size):
            target_class = int(target.data[i])
            loss = loss - Tensor(np.log(probs.data[i, target_class] + 1e-10))

        return loss / batch_size

# ========== Optimizers ==========

class Optimizer:
    """Base optimizer class"""

    def __init__(self, parameters: list[Tensor], lr: float = 0.01):
        self.parameters = parameters
        self.lr = lr

    def zero_grad(self):
        for p in self.parameters:
            p.zero_grad()

    def step(self):
        raise NotImplementedError

class SGD(Optimizer):
    """Stochastic Gradient Descent"""

    def __init__(self, parameters: list[Tensor], lr: float = 0.01, momentum: float = 0.0):
        super().__init__(parameters, lr)
        self.momentum = momentum
        self.velocity = [None] * len(parameters)

    def step(self):
        for i, p in enumerate(self.parameters):
            if p.grad is None:
                continue

            grad = p.grad.data

            if self.momentum > 0:
                if self.velocity[i] is None:
                    self.velocity[i] = grad
                else:
                    self.velocity[i] = self.momentum * self.velocity[i] + grad
                grad = self.velocity[i]

            p.data = p.data - self.lr * grad

class Adam(Optimizer):
    """Adam optimizer"""

    def __init__(self, parameters: list[Tensor], lr: float = 0.001,
                 betas: tuple[float, float] = (0.9, 0.999), eps: float = 1e-8):
        super().__init__(parameters, lr)
        self.betas = betas
        self.eps = eps
        self.t = 0
        self.m = [None] * len(parameters)
        self.v = [None] * len(parameters)

    def step(self):
        self.t += 1

        for i, p in enumerate(self.parameters):
            if p.grad is None:
                continue

            grad = p.grad.data

            # Initialize moments
            if self.m[i] is None:
                self.m[i] = np.zeros_like(grad)
                self.v[i] = np.zeros_like(grad)

            # Update biased first and second moment estimates
            self.m[i] = self.betas[0] * self.m[i] + (1 - self.betas[0]) * grad
            self.v[i] = self.betas[1] * self.v[i] + (1 - self.betas[1]) * (grad ** 2)

            # Bias correction
            m_hat = self.m[i] / (1 - self.betas[0] ** self.t)
            v_hat = self.v[i] / (1 - self.betas[1] ** self.t)

            # Update parameters
            p.data = p.data - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)
```

### ✅ Phase 2 Checklist
- [ ] Module base class implemented
- [ ] Linear layer working
- [ ] Conv2D layer working
- [ ] Sequential container working
- [ ] Loss functions (MSE, CrossEntropy) working
- [ ] Optimizers (SGD, Adam) working

---

## Phase 3: Training Loop & Data Loading (3 hours)

### 3.1 Data Loader

```python
# File: data.py
"""
Data Loading and Preprocessing
===============================
"""


import numpy as np
from tensor import Tensor

class Dataset:
    """Base dataset class"""

    def __len__(self):
        raise NotImplementedError

    def __getitem__(self, idx):
        raise NotImplementedError

class DataLoader:
    """Data loader with batching"""

    def __init__(self, dataset: Dataset, batch_size: int = 32,
                 shuffle: bool = True):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle

    def __iter__(self):
        indices = list(range(len(self.dataset)))
        if self.shuffle:
            np.random.shuffle(indices)

        for i in range(0, len(indices), self.batch_size):
            batch_indices = indices[i:i + self.batch_size]
            batch = [self.dataset[idx] for idx in batch_indices]

            # Stack into batches
            xs, ys = zip(*batch)
            yield Tensor(np.array(xs)), Tensor(np.array(ys))

    def __len__(self):
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size

# ========== Example Datasets ==========

class XORDataset(Dataset):
    """XOR problem dataset"""

    def __init__(self, n_samples: int = 1000):
        self.n_samples = n_samples
        # Generate XOR data
        self.X = np.random.randint(0, 2, size=(n_samples, 2)).astype(np.float32)
        self.y = ((self.X[:, 0] ^ self.X[:, 1]).astype(np.float32))

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

class SyntheticDataset(Dataset):
    """Synthetic classification dataset"""

    def __init__(self, n_samples: int = 1000, n_features: int = 10, n_classes: int = 3):
        self.n_samples = n_samples
        self.X = np.random.randn(n_samples, n_features).astype(np.float32)
        # Create labels with some pattern
        self.y = (self.X[:, 0] + self.X[:, 1] > 0).astype(np.float32)

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# ========== Training Utilities ==========

def train_epoch(model: Module, dataloader: DataLoader,
                criterion: Module, optimizer: Optimizer) -> float:
    """Train for one epoch"""

    model.train()
    total_loss = 0.0
    n_batches = 0

    for x_batch, y_batch in dataloader:
        # Forward pass
        pred = model(x_batch)
        loss = criterion(pred, y_batch)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        n_batches += 1

    return total_loss / n_batches

def evaluate(model: Module, dataloader: DataLoader,
             criterion: Module) -> tuple[float, float]:
    """Evaluate model"""

    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    n_batches = 0

    for x_batch, y_batch in dataloader:
        # Forward pass
        pred = model(x_batch)
        loss = criterion(pred, y_batch)

        total_loss += loss.item()

        # Calculate accuracy (for binary classification)
        if pred.shape[-1] == 1:
            pred_labels = (pred.data > 0.5).astype(np.float32).flatten()
            correct += np.sum(pred_labels == y_batch.data)
        else:
            pred_labels = np.argmax(pred.data, axis=1)
            correct += np.sum(pred_labels == y_batch.data)

        total += len(y_batch.data)
        n_batches += 1

    avg_loss = total_loss / n_batches
    accuracy = correct / total

    return avg_loss, accuracy
```

### ✅ Phase 3 Checklist
- [ ] Dataset class implemented
- [ ] DataLoader with batching working
- [ ] Training loop implemented
- [ ] Evaluation function working
- [ ] Accuracy calculation correct

---

## Phase 4: Train Your First Model (4 hours)

### 4.1 Train XOR Network

```python
# File: train_xor.py
"""
Train XOR Problem
=================
"""

from nn import Sequential, Linear, Tanh, Sigmoid
from data import XORDataset, DataLoader
from tensor import Tensor
import matplotlib.pyplot as plt

# Create dataset
dataset = XORDataset(n_samples=1000)
train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size

# Simple split (in production, use proper train/test split)
train_dataset = XORDataset(n_samples=train_size)
test_dataset = XORDataset(n_samples=test_size)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# Create model
model = Sequential(
    Linear(2, 4),
    Tanh(),
    Linear(4, 4),
    Tanh(),
    Linear(4, 1),
    Sigmoid()
)

print("Model architecture:")
print(model)
print(f"\nTotal parameters: {sum(p.data.size for p in model.parameters)}")

# Create loss and optimizer
from nn import MSELoss, SGD

criterion = MSELoss()
optimizer = SGD(model.parameters, lr=0.1, momentum=0.9)

# Training loop
n_epochs = 100
train_losses = []
test_losses = []
test_accuracies = []

print("\nTraining...")
for epoch in range(n_epochs):
    # Train
    train_loss = train_epoch(model, train_loader, criterion, optimizer)
    train_losses.append(train_loss)

    # Evaluate
    test_loss, test_acc = evaluate(model, test_loader, criterion)
    test_losses.append(test_loss)
    test_accuracies.append(test_acc)

    if (epoch + 1) % 10 == 0 or epoch == 0:
        print(f"Epoch {epoch+1}/{n_epochs}")
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Test Loss: {test_loss:.4f}")
        print(f"  Test Accuracy: {test_acc*100:.2f}%")

# Plot results
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].plot(train_losses, label='Train')
axes[0].plot(test_losses, label='Test')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].set_title('Training Progress')
axes[0].legend()
axes[0].grid(True)

axes[1].plot(test_accuracies)
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].set_title('Test Accuracy')
axes[1].grid(True)

# Decision boundary
xx, yy = np.meshgrid(np.linspace(-0.5, 1.5, 100), np.linspace(-0.5, 1.5, 100))
grid_data = np.c_[xx.ravel(), yy.ravel()]

# Make predictions
model.eval()
grid_tensor = Tensor(grid_data)
predictions = model(grid_tensor)
zz = predictions.data.reshape(xx.shape)

axes[2].contourf(xx, yy, zz, levels=20, alpha=0.5)
axes[2].scatter(dataset.X[:, 0], dataset.X[:, 1], c=dataset.y, cmap='RdYlBu', edgecolors='k')
axes[2].set_xlabel('X1')
axes[2].set_ylabel('X2')
axes[2].set_title('Decision Boundary')

plt.tight_layout()
plt.savefig('xor_results.png')
print("\n✓ Results saved to xor_results.png")

# Test predictions
print("\nTest predictions:")
test_cases = [
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
]

for case in test_cases:
    x = Tensor(np.array([case], dtype=np.float32))
    pred = model(x).item()
    print(f"  Input: {case} -> Prediction: {pred:.3f} (Expected: {case[0] ^ case[1]})")
```

### 4.2 Compare with PyTorch

```python
# File: compare_pytorch.py
"""
Compare Custom Framework with PyTorch
======================================
"""

import torch
import torch.nn as torch_nn
from torch.utils.data import TensorDataset, DataLoader as TorchDataLoader

# Create PyTorch model
class TorchXORNet(torch_nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch_nn.Sequential(
            torch_nn.Linear(2, 4),
            torch_nn.Tanh(),
            torch_nn.Linear(4, 4),
            torch_nn.Tanh(),
            torch_nn.Linear(4, 1),
            torch_nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)

# Create data
X_train = torch.randn(800, 2)
y_train = (X_train[:, 0].xor(X_train[:, 1].long())).float().unsqueeze(1)

train_dataset = TensorDataset(X_train, y_train)
train_loader = TorchDataLoader(train_dataset, batch_size=32, shuffle=True)

# Train PyTorch model
torch_model = TorchXORNet()
criterion = torch_nn.MSELoss()
optimizer = torch.optim.SGD(torch_model.parameters(), lr=0.1, momentum=0.9)

print("Training PyTorch model...")
torch_losses = []

for epoch in range(100):
    epoch_loss = 0.0
    for x_batch, y_batch in train_loader:
        pred = torch_model(x_batch)
        loss = criterion(pred, y_batch)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    avg_loss = epoch_loss / len(train_loader)
    torch_losses.append(avg_loss)

    if (epoch + 1) % 20 == 0:
        print(f"Epoch {epoch+1}, Loss: {avg_loss:.4f}")

# Compare
print("\n=== Comparison ===")
print(f"Custom framework final loss: {train_losses[-1]:.4f}")
print(f"PyTorch final loss: {torch_losses[-1]:.4f}")
print(f"Difference: {abs(train_losses[-1] - torch_losses[-1]):.4f}")
```

### ✅ Phase 4 Checklist
- [ ] XOR model trained successfully
- [ ] Loss decreased over epochs
- [ ] Test accuracy > 95%
- [ ] Decision boundary visualized
- [ ] Comparison with PyTorch completed

---

## Phase 5: Advanced Projects (6 hours)

### 5.1 MNIST Digit Classification

```python
# File: train_mnist.py
"""
Train MNIST Classifier
======================
"""

from nn import Sequential, Linear, ReLU
from data import DataLoader
from tensor import Tensor
import numpy as np

# Load MNIST data (simplified - using sklearn for loading)
from sklearn.datasets import fetch_openml

print("Loading MNIST...")
mnist = fetch_openml('mnist_784', version=1)
X = mnist.data.astype(np.float32) / 255.0
y = mnist.target.astype(np.int64)

# One-hot encode labels
n_classes = 10
y_onehot = np.zeros((len(y), n_classes))
for i, label in enumerate(y):
    y_onehot[i, label] = 1.0

# Split data
n_train = 60000
X_train, y_train = X[:n_train], y_onehot[:n_train]
X_test, y_test = X[n_train:], y_onehot[n_train:]

# Create model
model = Sequential(
    Linear(784, 256),
    ReLU(),
    Linear(256, 128),
    ReLU(),
    Linear(128, n_classes)
)

print(f"Model: {model}")
print(f"Parameters: {sum(p.data.size for p in model.parameters)}")

# Training
from nn import CrossEntropyLoss, Adam

criterion = CrossEntropyLoss()
optimizer = Adam(model.parameters, lr=0.001)

batch_size = 128
n_epochs = 20

for epoch in range(n_epochs):
    # Mini-batch training
    indices = np.random.permutation(n_train)
    epoch_loss = 0.0
    n_batches = 0

    for i in range(0, n_train, batch_size):
        batch_indices = indices[i:i + batch_size]
        x_batch = Tensor(X_train[batch_indices])
        y_batch = Tensor(y_train[batch_indices])

        pred = model(x_batch)
        loss = criterion(pred, y_batch)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()
        n_batches += 1

    # Evaluate
    x_test = Tensor(X_test)
    y_test_tensor = Tensor(y_test)
    pred_test = model(x_test)
    pred_labels = np.argmax(pred_test.data, axis=1)
    true_labels = np.argmax(y_test, axis=1)
    accuracy = np.mean(pred_labels == true_labels)

    print(f"Epoch {epoch+1}/{n_epochs}")
    print(f"  Loss: {epoch_loss/n_batches:.4f}")
    print(f"  Test Accuracy: {accuracy*100:.2f}%")
```

### ✅ Phase 5 Checklist
- [ ] MNIST model trained
- [ ] Test accuracy > 90%
- [ ] Training visualized
- [ ] Confusion matrix analyzed

---

## 🎓 Bonus Challenges

1. **Add more layers** - Deep networks
2. **Implement dropout** - Regularization
3. **Add batch normalization** - Training stability
4. **Implement different optimizers** - RMSProp, Adagrad
5. **Add learning rate scheduling** - Decay, cosine annealing
6. **Implement early stopping** - Prevent overfitting

---

## 🏆 Project Completion Checklist

```text
[ ] Phase 1: Tensor Library
[ ] Phase 2: Neural Network Module
[ ] Phase 3: Training Loop & Data Loading
[ ] Phase 4: Train XOR Model
[ ] Phase 5: MNIST Classification
[ ] Bonus: At least one challenge completed
```

---

## 📚 Related Resources

- **[2101: Tensor Algebra](../../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)** - Tensor theory
- **[2102: Backpropagation](../../phases/phase2-foundations/2100-calculus/2102-Backpropagation-and-Derivatives.md)** - Gradient computation
- **[2201: PyTorch Graphs](../../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)** - PyTorch comparison
- **[LAB-006: Train from Scratch](../labs/LAB-006-Train-Model-From-Scratch.md)** - Advanced training

---

**Congratulations!** You've built a deep learning framework from scratch:
- 🧮 Custom tensor library with autograd
- 🧠 Neural network modules
- 📈 Training loops and optimizers
- 🎯 Working models (XOR, MNIST)

## Next Steps

- **[Volume 3: LLM Internals](../../volumes/VOLUME-3-LLM-Internals.md)**
