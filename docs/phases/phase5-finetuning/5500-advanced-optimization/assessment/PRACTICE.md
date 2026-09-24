# 5500: Advanced Optimization - Practice

## Exercises

### Exercise 1: Implement Learning Rate Schedule

```python
import math

def get_lr_schedule(current_step, total_steps, warmup_steps, max_lr):
    """
    Calculate learning rate with warmup and cosine decay.

    Args:
        current_step: Current training step
        total_steps: Total training steps
        warmup_steps: Number of warmup steps
        max_lr: Maximum learning rate

    Returns:
        Learning rate for current step
    """
    if current_step < warmup_steps:
        # Linear warmup
        return max_lr * current_step / warmup_steps
    else:
        # Cosine decay
        progress = (current_step - warmup_steps) / (total_steps - warmup_steps)
        return max_lr * 0.5 * (1 + math.cos(math.pi * progress))

# Test the schedule
if __name__ == "__main__":
    total_steps = 10000
    warmup_steps = 500
    max_lr = 1e-4

    print("Learning Rate Schedule Test:")
    print(f"Total steps: {total_steps}")
    print(f"Warmup steps: {warmup_steps}")
    print(f"Max learning rate: {max_lr}\n")

    test_steps = [0, 100, 500, 1000, 5000, 10000]
    for step in test_steps:
        if step <= total_steps:
            lr = get_lr_schedule(step, total_steps, warmup_steps, max_lr)
            print(f"Step {step:5d}: LR = {lr:.6e}")

    # Plot learning rate schedule
    import matplotlib.pyplot as plt

    steps = list(range(0, total_steps + 1, 100))
    lrs = [get_lr_schedule(s, total_steps, warmup_steps, max_lr) for s in steps]

    plt.figure(figsize=(10, 5))
    plt.plot(steps, lrs)
    plt.xlabel("Training Step")
    plt.ylabel("Learning Rate")
    plt.title("Cosine Learning Rate Schedule with Warmup")
    plt.grid(True)
    plt.savefig("lr_schedule.png")
    print("\nLearning rate schedule plot saved to lr_schedule.png")

# Expected output:
# - Linear increase from 0 to max_lr during warmup
# - Cosine decay from max_lr to ~0 after warmup
# - Smooth transition without sudden jumps
# - Final LR close to 0 at end of training
```

### Exercise 2: Compare Optimizers

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt

def create_model():
    """Create a simple neural network."""
    return nn.Sequential(
        nn.Linear(784, 256),
        nn.ReLU(),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Linear(128, 10),
    )

def train_with_optimizer(optimizer_name, model, train_loader, epochs=5):
    """Train with specified optimizer and return loss curve."""

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    # Create optimizer
    if optimizer_name == "AdamW":
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
    elif optimizer_name == "Adafactor":
        from transformers import Adafactor
        optimizer = Adafactor(model.parameters(), lr=1e-3, scale_parameter=False)
    elif optimizer_name == "Adam":
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    elif optimizer_name == "SGD":
        optimizer = torch.optim.SGD(model.parameters(), lr=1e-3, momentum=0.9)
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_name}")

    criterion = nn.CrossEntropyLoss()

    loss_history = []
    step = 0

    for epoch in range(epochs):
        epoch_losses = []

        for data, target in train_loader:
            data, target = data.to(device), target.to(device)

            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            epoch_losses.append(loss.item())
            loss_history.append(loss.item())
            step += 1

        avg_loss = sum(epoch_losses) / len(epoch_losses)
        print(f"{optimizer_name} - Epoch {epoch+1}/{epochs}: Loss = {avg_loss:.4f}")

    return loss_history

# Create dummy data
torch.manual_seed(42)
train_data = torch.randn(1000, 784)
train_labels = torch.randint(0, 10, (1000,))
train_dataset = TensorDataset(train_data, train_labels)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Compare optimizers
print("Comparing Optimizers:")
print("=" * 60)

optimizers = ["AdamW", "Adafactor", "Adam", "SGD"]
results = {}

for opt_name in optimizers:
    print(f"\nTraining with {opt_name}...")
    model = create_model()
    loss_curve = train_with_optimizer(opt_name, model, train_loader, epochs=5)
    results[opt_name] = loss_curve

# Plot comparison
plt.figure(figsize=(12, 6))
for opt_name, loss_curve in results.items():
    # Smooth the loss curve with moving average
    import numpy as np
    window = 10
    smoothed = np.convolve(loss_curve, np.ones(window)/window, mode='valid')
    plt.plot(smoothed, label=opt_name, linewidth=2)

plt.xlabel("Training Step")
plt.ylabel("Loss")
plt.title("Optimizer Comparison: Loss Curves")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("optimizer_comparison.png")
print("\nOptimizer comparison plot saved to optimizer_comparison.png")

# Print final losses
print("\nFinal Losses:")
print("=" * 60)
for opt_name, loss_curve in results.items():
    final_loss = loss_curve[-1]
    print(f"{opt_name:10s}: {final_loss:.4f}")

# Expected results:
# - AdamW: Fast convergence, good final performance
# - Adafactor: Slower convergence, memory efficient for large models
# - Adam: Similar to AdamW but without weight decay
# - SGD: Slower convergence but can achieve better generalization
```

### Exercise 3: Implement Gradient Clipping

```python
import torch
import torch.nn as nn

def train_with_gradient_clipping(model, train_loader, optimizer, criterion,
                                  clip_norm=1.0, epochs=5):
    """Train with gradient clipping to prevent exploding gradients."""

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    grad_norms = []
    losses = []

    print(f"Training with gradient clipping (max_norm={clip_norm})")

    for epoch in range(epochs):
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)

            optimizer.zero_grad()

            # Forward pass
            output = model(data)
            loss = criterion(output, target)

            # Backward pass
            loss.backward()

            # Calculate gradient norm before clipping
            total_norm = 0
            for p in model.parameters():
                if p.grad is not None:
                    param_norm = p.grad.data.norm(2)
                    total_norm += param_norm.item() ** 2
            total_norm = total_norm ** 0.5
            grad_norms.append(total_norm)

            # Clip gradients at norm 1.0
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=clip_norm)

            # Update weights
            optimizer.step()

            losses.append(loss.item())

            if batch_idx % 100 == 0:
                print(f"Epoch {epoch+1}, Batch {batch_idx}: Loss={loss.item():.4f}, GradNorm={total_norm:.4f}")

    return losses, grad_norms

# Example usage
if __name__ == "__main__":
    # Create model and data
    model = nn.Sequential(
        nn.Linear(784, 256),
        nn.ReLU(),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Linear(128, 10),
    )

    from torch.utils.data import DataLoader, TensorDataset
    train_data = torch.randn(1000, 784)
    train_labels = torch.randint(0, 10, (1000,))
    train_dataset = TensorDataset(train_data, train_labels)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    # Train with gradient clipping
    losses, grad_norms = train_with_gradient_clipping(
        model, train_loader, optimizer, criterion,
        clip_norm=1.0,
        epochs=3
    )

    # Analyze gradient norms
    import numpy as np
    avg_grad_norm = np.mean(grad_norms)
    max_grad_norm = np.max(grad_norms)
    clipped_count = sum(1 for g in grad_norms if g > 1.0)

    print(f"\nGradient Statistics:")
    print(f"  Average gradient norm: {avg_grad_norm:.4f}")
    print(f"  Maximum gradient norm: {max_grad_norm:.4f}")
    print(f"  Times gradient was clipped: {clipped_count}/{len(grad_norms)}")

    # Plot gradient norms
    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 4))

    plt.subplot(1, 2, 1)
    plt.plot(losses)
    plt.xlabel("Step")
    plt.ylabel("Loss")
    plt.title("Training Loss")
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot(grad_norms)
    plt.axhline(y=1.0, color='r', linestyle='--', label='Clip threshold')
    plt.xlabel("Step")
    plt.ylabel("Gradient Norm")
    plt.title("Gradient Norms")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("gradient_clipping.png")
    print("\nPlots saved to gradient_clipping.png")

# Expected results:
# - Gradient norms clipped to max_norm (1.0)
# - Training remains stable even with occasional large gradients
# - Prevents exploding gradients in RNNs or deep networks
# - Can improve training stability for large language models
```

---

**Last Updated:** 2026-02-05
**Status:** ✅ Complete - All tasks completed with solutions
