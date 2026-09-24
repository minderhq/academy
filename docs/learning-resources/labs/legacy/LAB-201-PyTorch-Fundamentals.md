# LAB-201: PyTorch Fundamentals

## Overview
Hands-on lab covering PyTorch tensors, autograd, and basic neural network operations.

## Prerequisites
- Python 3.8+
- PyTorch installed
- Basic Python knowledge

## Setup

```bash
# Create environment
python -m venv lab201-env
source lab201-env/bin/activate  # Linux/Mac
# or lab201-env\Scripts\activate  # Windows

pip install torch numpy jupyter
```

## Exercise 1: Tensor Operations

```python
import torch

# Create tensors
x = torch.randn(3, 4)
y = torch.randn(3, 4)

# Perform operations
# 1. Addition: z = x + y
z = x + y
print(f"Addition result shape: {z.shape}")

# 2. Matrix multiplication: x @ y.T
matmul_result = x @ y.T
print(f"Matrix multiplication result shape: {matmul_result.shape}")

# 3. Mean: x.mean()
mean_value = x.mean()
print(f"Mean of x: {mean_value.item():.4f}")

# 4. Reshape: x.view(2, 6)
reshaped = x.view(2, 6)
print(f"Reshaped x: {reshaped.shape}")

# Print shapes and values
print(f"x shape: {x.shape}")
print(f"y shape: {y.shape}")
```

## Exercise 2: Autograd

```python
# Enable gradient tracking
x = torch.randn(3, requires_grad=True)

# Operations
y = x * 2
z = y.sum()

# Compute gradients
z.backward()

# Check gradient
print(f"x.grad: {x.grad}")

# Expected: [2, 2, 2]
```

## Exercise 3: Simple Neural Network

```python
import torch.nn as nn

# TODO: Define network
class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        # Define layers
        self.fc1 = nn.Linear(10, 5)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(5, 1)

    def forward(self, x):
        # Forward pass
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# Test
model = SimpleNet()
x = torch.randn(4, 10)
output = model(x)
print(f"Output shape: {output.shape}")  # Should be [4, 1]
```

## Exercise 4: Training Loop

```python
# TODO: Complete training loop
import torch.optim as optim

# Data
inputs = torch.randn(100, 10)
labels = torch.randn(100, 1)

# Model
model = SimpleNet()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# Training loop
losses = []
for epoch in range(100):
    # Forward pass
    outputs = model(inputs)
    # Compute loss
    loss = criterion(outputs, labels)
    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    # Update parameters
    optimizer.step()

    losses.append(loss.item())
    if epoch % 10 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

# Plot loss curve
import matplotlib.pyplot as plt
plt.plot(losses)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss')
plt.show()
```

## Expected Outputs

1. Exercise 1: Various tensor operations completed
2. Exercise 2: Gradient = [2, 2, 2]
3. Exercise 3: Output shape = [4, 1]
4. Exercise 4: Decreasing loss curve

## Troubleshooting

**Issue:** CUDA out of memory
```python
# Solution: Use CPU
device = torch.device('cpu')
model = model.to(device)
inputs = inputs.to(device)
```

**Issue:** Gradients not computed
```python
# Solution: Enable requires_grad
x = torch.randn(3, requires_grad=True)
```

## Extensions

1. Try different optimizers (SGD, RMSprop)
2. Add more layers to the network
3. Implement mini-batch training
4. Add validation during training

## Time Estimate: 2-3 hours

---

**Last Updated:** 2026-02-04
