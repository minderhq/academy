# LAB-202: Neural Network Training

## Overview
Train a neural network from scratch on a real dataset.

## Prerequisites
- LAB-201 completed

## Setup

```bash
pip install torch torchvision matplotlib
```

## Exercise 1: Load and Preprocess Data

```python
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# Define transforms for MNIST normalization
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

# Load MNIST dataset
train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
test_dataset = datasets.MNIST('./data', train=False, download=True, transform=transform)

# Create dataloaders for batching
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=1000, shuffle=False)

print(f"Training samples: {len(train_dataset)}")
print(f"Test samples: {len(test_dataset)}")
```

## Exercise 2: Define Network

```python
import torch.nn as nn

class MNISTNet(nn.Module):
    def __init__(self):
        super().__init__()
        # Define architecture: 3 fully connected layers with dropout
        self.fc1 = nn.Linear(28*28, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 10)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        # Forward pass: flatten -> fc1 -> relu -> dropout -> fc2 -> relu -> dropout -> fc3
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x

# Test
model = MNISTNet()
x = torch.randn(4, 1, 28, 28)
output = model(x)
print(f"Output shape: {output.shape}")  # [4, 10]
```

## Exercise 3: Training Loop with Metrics

```python
import torch.optim as optim

def train_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (data, target) in enumerate(loader):
        data, target = data.to(device), target.to(device)

        # Training step: forward, backward, update
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        # Metrics
        running_loss += loss.item()
        _, predicted = output.max(1)
        total += target.size(0)
        correct += predicted.eq(target).sum().item()

    return running_loss / len(loader), 100. * correct / total

def evaluate(model, loader, criterion, device):
    """Evaluate model."""
    model.eval()
    loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for data, target in loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss += criterion(output, target).item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

    return loss / len(loader), 100. * correct / total

# Train the model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

for epoch in range(5):
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    test_loss, test_acc = evaluate(model, test_loader, criterion, device)

    print(f"Epoch {epoch+1}/5:")
    print(f"  Train - Loss: {train_loss:.4f}, Acc: {train_acc:.2f}%")
    print(f"  Test  - Loss: {test_loss:.4f}, Acc: {test_acc:.2f}%")
```

## Exercise 4: Visualize Training

```python
import matplotlib.pyplot as plt

# Track metrics
train_losses = []
train_accs = []
test_losses = []
test_accs = []

for epoch in range(5):
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    test_loss, test_acc = evaluate(model, test_loader, criterion, device)

    train_losses.append(train_loss)
    train_accs.append(train_acc)
    test_losses.append(test_loss)
    test_accs.append(test_acc)

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

ax1.plot(train_losses, label='Train')
ax1.plot(test_losses, label='Test')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Loss')
ax1.set_title('Loss Curve')
ax1.legend()

ax2.plot(train_accs, label='Train')
ax2.plot(test_accs, label='Test')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Accuracy (%)')
ax2.set_title('Accuracy Curve')
ax2.legend()

plt.tight_layout()
plt.show()
```

## Expected Outputs

- Training accuracy > 95%
- Test accuracy > 95%
- Decreasing loss curve
- Increasing accuracy curve

## Time Estimate: 2-3 hours
