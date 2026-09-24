---
Document ID: 5502
Title: Learning Rate Scheduling
Phase: 5
Module: 5500
Last Updated: 2026-09-24
Status: Review
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: 5501, 5503
Tags: ['optimization', 'learning-rate', 'scheduling']
---

# 5502: Learning Rate Scheduling

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Why Schedule Learning Rate?](#why-schedule-learning-rate)
- [Common Schedulers](#common-schedulers)
- [Custom Schedulers](#custom-schedulers)
- [Choosing a Scheduler](#choosing-a-scheduler)
- [Integration with Training Loop](#integration-with-training-loop)
- [Hugging Face Integration](#hugging-face-integration)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain the reasoning behind Why Schedule Learning Rate
- Explain Common Schedulers
- Explain Custom Schedulers
- Explain Choosing a Scheduler
- Apply Integration with Training Loop
- Explain Hugging Face Integration

---

## Abstract

Learning rate scheduling adjusts the learning rate during training to improve convergence and final model performance.

## Why Schedule Learning Rate?

- **Warmup:** Avoid large gradients early in training
- **Decay:** Fine-tune weights as training progresses
- **Restarts:** Escape local minima
- **Cyclical:** Explore different regions of loss landscape

## Common Schedulers

### 1. Warmup + Linear Decay

Standard for transformer training:

```python
from torch.optim.lr_scheduler import LambdaLR

def get_lr_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps):
    """Create warmup + linear decay scheduler."""
    def lr_lambda(current_step):
        if current_step < num_warmup_steps:
            # Linear warmup
            return float(current_step) / float(max(1, num_warmup_steps))
        else:
            # Linear decay
            progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
            return max(0.0, 1.0 - progress)

    return LambdaLR(optimizer, lr_lambda)

# Usage
optimizer = AdamW(model.parameters(), lr=5e-5)
num_warmup_steps = 500
num_training_steps = 10000

scheduler = get_lr_schedule_with_warmup(
    optimizer,
    num_warmup_steps,
    num_training_steps
)
```

**Visual:**
```text
LR │
   │     ╱──────────────
   │    ╱
   │   ╱
   │  ╱
   │ ╱
   │╱─────────────────────
   └───────────────────────> Step
     Warmup   Decay
```

### 2. Cosine Decay

Smooth decay following cosine curve:

```python
from torch.optim.lr_scheduler import CosineAnnealingLR

# Cosine annealing over N epochs
scheduler = CosineAnnealingLR(
    optimizer,
    T_max=num_epochs,  # Maximum number of iterations
    eta_min=1e-6,      # Minimum learning rate
)

# Or with warmup
class CosineSchedulerWithWarmup:
    def __init__(self, optimizer, warmup_steps, max_steps, min_lr=1e-6):
        self.optimizer = optimizer
        self.warmup_steps = warmup_steps
        self.max_steps = max_steps
        self.min_lr = min_lr
        self.base_lr = optimizer.param_groups[0]['lr']
        self.current_step = 0

    def step(self):
        self.current_step += 1

        if self.current_step < self.warmup_steps:
            # Linear warmup
            lr = self.base_lr * self.current_step / self.warmup_steps
        else:
            # Cosine decay
            progress = (self.current_step - self.warmup_steps) / (self.max_steps - self.warmup_steps)
            lr = self.min_lr + (self.base_lr - self.min_lr) * 0.5 * (1 + np.cos(np.pi * progress))

        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr

        return lr
```

**Visual:**
```text
LR │
   │     ╱╲
   │    ╱  ╲
   │   ╱    ╲
   │  ╱      ╲
   │ ╱        ╲___
   │╱              ─
   └──────────────────> Step
     Warmup  Cosine Decay
```

### 3. Step Decay

Reduce LR by factor at specific intervals:

```python
from torch.optim.lr_scheduler import StepLR

# Decay LR by gamma every step_size steps
scheduler = StepLR(
    optimizer,
    step_size=1000,  # Decay every 1000 steps
    gamma=0.1,        # Multiply LR by 0.1
)

# MultiStepLR for uneven intervals
from torch.optim.lr_scheduler import MultiStepLR

scheduler = MultiStepLR(
    optimizer,
    milestones=[3000, 5000, 8000],  # Decay at these steps
    gamma=0.1,
)
```

**Visual:**
```text
LR │
   │───────────
   │           ───────
   │                  ───────
   │                         ────
   └────────────────────────────> Step
     1000    2000    3000
```

### 4. Exponential Decay

Continuous exponential decay:

```python
from torch.optim.lr_scheduler import ExponentialLR

scheduler = ExponentialLR(
    optimizer,
    gamma=0.99,  # Multiply LR by 0.99 each step
)
```

### 5. Cosine with Restarts (SGDR)

Periodic restarts for better convergence:

```python
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts

scheduler = CosineAnnealingWarmRestarts(
    optimizer,
    T_0=1000,        # First restart after 1000 steps
    T_mult=2,         # Double restart interval each time
    eta_min=1e-6,
)

# After 1000 steps, restart; after 2000 more, restart; etc.
```

**Visual:**
```text
LR │
   │     ╱╲    ╱╲    ╱╲
   │    ╱  ╲  ╱  ╲  ╱  ╲
   │   ╱    ╲╱    ╲╱    ╲___
   │  ╱
   │ ╱
   │╱─────────────────────────> Step
     T0   2*T0   4*T0
```

### 6. Cyclic LR

Oscillate between min and max LR:

```python
from torch.optim.lr_scheduler import CyclicLR

scheduler = CyclicLR(
    optimizer,
    base_lr=1e-6,      # Minimum LR
    max_lr=1e-3,       # Maximum LR
    step_size_up=1000, # Steps to reach max_lr
    mode='triangular', # or 'triangular2', 'exp_range'
    gamma=1.0,
)
```

**Visual:**
```text
LR │
   │     ╱╲    ╱╲    ╱╲
   │    ╱  ╲  ╱  ╲  ╱  ╲
   │   ╱    ╲╱    ╲╱    ╲
   │  ╱                  ╲
   │ ╱                    ╲
   │╱────────────────────────> Step
```

### 7. OneCycleLR

Increase then decrease LR in one cycle:

```python
from torch.optim.lr_scheduler import OneCycleLR

scheduler = OneCycleLR(
    optimizer,
    max_lr=1e-3,          # Peak LR
    total_steps=10000,    # Total training steps
    pct_start=0.3,        # 30% of cycle for increasing
    anneal_strategy='cos',  # 'cos' or 'linear'
    div_factor=25,        # initial_lr = max_lr / 25
    final_div_factor=1e4, # min_lr = initial_lr / 1e4
)
```

**Visual:**
```text
LR │
   │         ╱───╲
   │        ╱     ╲
   │       ╱       ╲
   │      ╱         ╲
   │   ╱╱             ╲╲
   │ ╱╱                 ╲╲_
   └────────────────────────> Step
     30% increasing, 70% decreasing
```

## Custom Schedulers

### Linear Warmup with Hold

```python
class LinearWarmupHoldDecay:
    """Linear warmup, hold, then decay."""

    def __init__(self, optimizer, warmup_steps, hold_steps, total_steps, max_lr, min_lr=0):
        self.optimizer = optimizer
        self.warmup_steps = warmup_steps
        self.hold_steps = hold_steps
        self.total_steps = total_steps
        self.max_lr = max_lr
        self.min_lr = min_lr
        self.current_step = 0

    def step(self):
        self.current_step += 1

        if self.current_step <= self.warmup_steps:
            # Warmup phase
            lr = self.max_lr * self.current_step / self.warmup_steps
        elif self.current_step <= self.warmup_steps + self.hold_steps:
            # Hold phase
            lr = self.max_lr
        elif self.current_step < self.total_steps:
            # Decay phase
            decay_steps = self.total_steps - self.warmup_steps - self.hold_steps
            progress = (self.current_step - self.warmup_steps - self.hold_steps) / decay_steps
            lr = self.max_lr - (self.max_lr - self.min_lr) * progress
        else:
            lr = self.min_lr

        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr

        return lr
```

### Polynomial Decay

```python
class PolynomialDecayScheduler:
    """Polynomial decay with warmup."""

    def __init__(self, optimizer, warmup_steps, total_steps, power=1.0, min_lr=0):
        self.optimizer = optimizer
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        self.power = power
        self.min_lr = min_lr
        self.base_lr = optimizer.param_groups[0]['lr']
        self.current_step = 0

    def step(self):
        self.current_step += 1

        if self.current_step < self.warmup_steps:
            # Warmup
            lr = self.base_lr * self.current_step / self.warmup_steps
        else:
            # Polynomial decay
            progress = min(1.0, (self.current_step - self.warmup_steps) / (self.total_steps - self.warmup_steps))
            lr = self.min_lr + (self.base_lr - self.min_lr) * (1 - progress) ** self.power

        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr

        return lr
```

## Choosing a Scheduler

| Task | Recommended Scheduler | Reason |
|------|---------------------|--------|
| **Fine-tuning** | Linear + Warmup | Stable convergence |
| **Pre-training** | Cosine + Warmup | Smooth decay, better final loss |
| **Transfer Learning** | OneCycleLR | Fast convergence |
| **Domain Adaptation** | Cosine with Restarts | Escape local minima |
| **Quick Training** | CyclicLR | Find good LR range |

## Integration with Training Loop

```python
# Training loop with scheduler
for epoch in range(num_epochs):
    for batch in dataloader:
        # Forward pass
        output = model(batch)
        loss = criterion(output, target)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Optimizer step
        optimizer.step()

        # Scheduler step (per-step)
        scheduler.step()

    # Optional: scheduler per epoch
    # scheduler.step()
```

## Hugging Face Integration

```python
from transformers import get_scheduler

# Get scheduler from HF
num_training_steps = len(train_dataloader) * num_epochs

scheduler = get_scheduler(
    name="cosine",  # "linear", "cosine", "cosine_with_restarts", "polynomial"
    optimizer=optimizer,
    num_warmup_steps=500,
    num_training_steps=num_training_steps,
)
```

## Best Practices

1. **Warmup is essential for transformers:**
   - Prevents early divergence
   - Typical: 1-10% of total steps

2. **Monitor learning rate:**
   ```python
   from torch.optim.lr_scheduler import LambdaLR

   # Add logging
   class LoggingScheduler(LambdaLR):
       def step(self):
           lr = self.get_last_lr()[0]
           if self._step_count % 100 == 0:
               print(f"Step {self._step_count}: LR = {lr:.2e}")
           super().step()
   ```

3. **Adjust for batch size:**
   - Larger batch → higher LR (linear scaling rule)
   - `LR_new = LR_base * (batch_size / 256)`

4. **Layer-wise decay:**
   ```python
   # Different LR for different layers
   optimizer = AdamW([
       {'params': model.encoder.parameters(), 'lr': 5e-5},
       {'params': model.decoder.parameters(), 'lr': 1e-4},
   ])
   ```

---

**Next:** [5503: Advanced Techniques](./5503-Advanced-Techniques.md)

**Last Updated:** 2026-02-05

## References

### Related ai-engineering-curriculum Documents

- [5501: Optimizer Variants](5501-Optimizer-Variants.md)
- [5503: Advanced Optimization Techniques](5503-Advanced-Techniques.md)

---