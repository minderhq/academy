---
Document ID: 5503
Title: Advanced Optimization Techniques
Phase: 5
Module: 5500
Last Updated: 2026-02-05
Status: Review
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: 5501, 5502
Tags: ['optimization', 'training', 'advanced']
---

# 5503: Advanced Optimization Techniques

## Abstract

Advanced optimization techniques go beyond basic optimizers and learning rate schedules to improve training stability, convergence, and final model performance.

## Gradient Clipping

Prevent gradient explosion during training:

### 1. Clip by Norm

```python
import torch.nn.utils as nn_utils

# Clip gradients to maximum norm of 1.0
torch.nn.utils.clip_grad_norm_(
    model.parameters(),
    max_norm=1.0,
    norm_type=2.0,  # L2 norm (default)
)

# In training loop
for batch in dataloader:
    output = model(batch)
    loss = criterion(output, target)

    optimizer.zero_grad()
    loss.backward()

    # Clip before optimizer step
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

    optimizer.step()
```

### 2. Clip by Value

```python
# Clip individual gradient values
torch.nn.utils.clip_grad_value_(
    model.parameters(),
    clip_value=0.5,  # Clip to [-0.5, 0.5]
)
```

### 3. Adaptive Clipping (AGC)

```python
def adaptive_gradient_clip(parameters, clip_factor=0.01):
    """Adaptive Gradient Clipping."""
    for p in parameters:
        if p.grad is not None:
            # Compute clip threshold based on weight magnitude
            grad_norm = p.grad.norm()
            weight_norm = p.data.norm()
            max_grad = clip_factor * weight_norm

            # Clip if necessary
            if grad_norm > max_grad:
                p.grad.mul_(max_grad / (grad_norm + 1e-6))
```

## Regularization Techniques

### 1. Weight Decay

```python
# Built into optimizers
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-4,
    weight_decay=0.01,  # L2 regularization
)

# Decoupled weight decay (AdamW)
# Better than standard Adam with L2
```

### 2. Dropout

```python
class CustomDropout(nn.Module):
    def __init__(self, p=0.1):
        super().__init__()
        self.p = p

    def forward(self, x):
        if not self.training:
            return x

        mask = (torch.rand_like(x) > self.p).float()
        return x * mask / (1 - self.p)

# Usage
model = nn.Sequential(
    nn.Linear(768, 3072),
    nn.Dropout(0.1),
    nn.GELU(),
    nn.Linear(3072, 768),
    nn.Dropout(0.1),
)
```

### 3. Layer Normalization with Dropout

```python
class LayerNormDropout(nn.Module):
    def __init__(self, hidden_size, dropout=0.1):
        super().__init__()
        self.norm = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # Apply norm then dropout
        return self.dropout(self.norm(x))
```

## Learning Rate Warmup

Essential for stable transformer training:

### Constant Warmup

```python
class WarmupScheduler:
    def __init__(self, optimizer, warmup_steps, base_lr):
        self.optimizer = optimizer
        self.warmup_steps = warmup_steps
        self.base_lr = base_lr
        self.current_step = 0

    def step(self):
        self.current_step += 1

        if self.current_step <= self.warmup_steps:
            lr = self.base_lr * self.current_step / self.warmup_steps
        else:
            lr = self.base_lr

        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr

        return lr
```

## Advanced Optimizer Features

### 1. Layer-wise Learning Rate Decay

```python
def get_layerwise_lr_groups(model, base_lr, decay=0.95):
    """Create parameter groups with decreasing LR for earlier layers."""
    layers = [model.embeddings] + list(model.encoder.layers)

    # Create groups with decreasing LR
    optimizer_grouped_parameters = []
    for i, layer in enumerate(layers):
        lr = base_lr * (decay ** (len(layers) - i - 1))
        optimizer_grouped_parameters.append({
            'params': layer.parameters(),
            'lr': lr,
        })

    return optimizer_grouped_parameters

# Usage
optimizer = AdamW(
    get_layerwise_lr_groups(model, base_lr=5e-5, decay=0.95),
)
```

### 2. AdamW Parameter Tweaking

```python
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.999),  # Momentum parameters
    eps=1e-8,            # Numerical stability
    weight_decay=0.01,

    # Advanced settings
    amsgrad=True,        # Use AMSGrad variant
    foreach=True,        # Use fused implementation
    capturable=True,     # CUDA graphs support
)
```

### 3. Sophia Optimizer

```python
# Sophia: Second-order optimizer with Hessian approximation
class Sophia:
    def __init__(self, params, lr=1e-4, betas=(0.965, 0.99), rho=0.04):
        self.params = list(params)
        self.lr = lr
        self.betas = betas
        self.rho = rho
        self.step_count = 0

        # Initialize state
        self.m = {}  # First moment
        self.h = {}  # Hessian diagonal

    def step(self, closure=None):
        self.step_count += 1

        for p in self.params:
            if p.grad is None:
                continue

            state = self.state[p]

            # Initialize state
            if len(state) == 0:
                state['step'] = 0
                state['m'] = torch.zeros_like(p.data)
                state['h'] = torch.zeros_like(p.data)

            m, h = state['m'], state['h']
            beta1, beta2 = self.betas

            # Update biased first moment
            m.mul_(beta1).add_(p.grad, alpha=1 - beta1)

            # Update Hessian approximation (every k steps)
            if self.step_count % 16 == 0:
                hessian_diag = self._estimate_hessian_diag(p)
                h.mul_(beta2).add_(hessian_diag, alpha=1 - beta2)

            # Compute update
            update = self.lr * m / (1 - beta1 ** self.step_count)
            update.add_(self.rho * p.grad * h)

            # Apply update
            p.data.add_(-update)

    def _estimate_hessian_diag(self, p):
        """Estimate diagonal of Hessian."""
        # Simplified - use Hutchinson's method in practice
        with torch.enable_grad():
            loss = (p.grad ** 2).sum()
        return torch.autograd.grad(loss, p)[0]
```

## Gradient Accumulation

Simulate larger batch sizes:

```python
def train_with_accumulation(model, dataloader, optimizer, accumulation_steps, scaler=None):
    """Train with gradient accumulation."""
    model.train()

    for i, batch in enumerate(dataloader):
        inputs, targets = batch

        # Forward pass
        with torch.cuda.amp.autocast():
            outputs = model(inputs)
            loss = criterion(outputs, targets) / accumulation_steps

        # Backward pass (accumulate gradients)
        if scaler:
            scaler.scale(loss).backward()
        else:
            loss.backward()

        # Optimizer step every N batches
        if (i + 1) % accumulation_steps == 0:
            if scaler:
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()
            optimizer.zero_grad()
```

## Gradient Checkpointing

Trade compute for memory:

```python
from torch.utils.checkpoint import checkpoint

class CheckpointedTransformer(nn.Module):
    def __init__(self, hidden_size, num_layers):
        super().__init__()
        self.layers = nn.ModuleList([
            TransformerBlock(hidden_size)
            for _ in range(num_layers)
        ])

    def forward(self, x):
        # Checkpoint every other layer
        for i, layer in enumerate(self.layers):
            if i % 2 == 0:
                # Checkpoint this layer
                x = checkpoint(layer, x, use_reentrant=False)
            else:
                x = layer(x)

        return x

# Or use built-in
model.gradient_checkpointing_enable()
```

## Sharpness-Aware Minimization (SAM)

Optimize for flat minima:

```python
class SAMOptimizer:
    def __init__(self, model, base_optimizer, rho=0.05, **kwargs):
        self.model = model
        self.base_optimizer = base_optimizer(model.parameters(), **kwargs)
        self.param_groups = self.base_optimizer.param_groups
        self.rho = rho

    @torch.no_grad()
    def first_step(self):
        """Compute perturbed weights."""
        for group in self.param_groups:
            for p in group['params']:
                if p.grad is None:
                    continue

                # Compute perturbation
                grad_norm = torch.norm(p.grad)
                scale = self.rho / (grad_norm + 1e-12)
                p.add_(p.grad, alpha=scale)

        # Store original weights
        self.state['original_weights'] = [
            p.data.clone() for p in self.model.parameters()
        ]

    @torch.no_grad()
    def second_step(self):
        """Restore original weights and update with SAM gradient."""
        for i, p in enumerate(self.model.parameters()):
            p.data.copy_(self.state['original_weights'][i])

        self.base_optimizer.step()

    def step(self, closure=None):
        raise NotImplementedError("Use first_step() and second_step()")

# Training loop
optimizer = SAMOptimizer(model, torch.optim.SGD, lr=1e-3, momentum=0.9)

for batch in dataloader:
    inputs, targets = batch

    # First forward-backward pass
    outputs = model(inputs)
    loss = criterion(outputs, targets)

    loss.backward()
    optimizer.first_step()  # Perturb weights

    # Second forward-backward pass
    criterion(model(inputs), targets).backward()
    optimizer.second_step()  # Update with SAM gradient

    optimizer.zero_grad()
```

## Apex Learning Rate (Super-Convergence)

Find optimal learning rate:

```python
def find_lr(model, dataloader, optimizer, init_lr=1e-7, final_lr=10, num_iter=100):
    """Find optimal learning rate using LR range test."""
    model.train()

    mult = (final_lr / init_lr) ** (1 / num_iter)
    lr = init_lr
    optimizer.param_groups[0]['lr'] = lr

    losses = []
    lrs = []

    for i, batch in enumerate(dataloader):
        if i >= num_iter:
            break

        inputs, targets = batch
        optimizer.zero_grad()

        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()

        optimizer.step()

        losses.append(loss.item())
        lrs.append(lr)

        lr *= mult
        optimizer.param_groups[0]['lr'] = lr

    # Plot to find steepest descent
    import matplotlib.pyplot as plt
    plt.plot(lrs, losses)
    plt.xscale('log')
    plt.xlabel('Learning Rate')
    plt.ylabel('Loss')

    return lrs, losses
```

## Best Practices Summary

1. **Always use gradient clipping for transformers**
   - `clip_grad_norm_(model.parameters(), max_norm=1.0)`

2. **Warmup is essential**
   - 1-10% of total steps for most tasks

3. **Use AdamW over Adam**
   - Decoupled weight decay is better

4. **Layer-wise decay for fine-tuning**
   - Lower LR for earlier layers

5. **Gradient accumulation for large effective batches**
   - Effective batch size = batch_size × accumulation_steps × num_gpus

---

**Next:** [Assessment](./assessment/QUIZ.md)

**Last Updated:** 2026-02-05
