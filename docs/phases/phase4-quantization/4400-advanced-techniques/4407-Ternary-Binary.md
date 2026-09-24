---
Document ID: 4407
Title: Ternary & Binary Networks
Phase: 4
Module: 4400
Last Updated: 2026-09-24
Status: Review
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: 4101, 4406
Related: 4405, 4406
Tags: ['quantization', 'binary', 'ternary', 'extreme']
---

# 4407: Ternary & Binary Networks

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Binary vs Ternary Networks](#binary-vs-ternary-networks)
- [Binary Neural Networks](#binary-neural-networks)
- [Ternary Neural Networks](#ternary-neural-networks)
- [Training Binary/Ternary Networks](#training-binaryternary-networks)
- [Hardware Optimization](#hardware-optimization)
- [State of the Art Results](#state-of-the-art-results)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare Binary vs Ternary Networks
- Explain Binary Neural Networks
- Explain Ternary Neural Networks
- Explain Training Binary/Ternary Networks
- Explain Hardware Optimization
- Explain State of the Art Results

---

## Abstract

Neural networks with weights constrained to only 2 or 3 possible values, enabling extreme compression and efficient inference.

## Binary vs Ternary Networks

| Property | Binary | Ternary |
|----------|--------|---------|
| **Values** | {-1, +1} | {-1, 0, +1} |
| **Bits** | 1 | ~1.58 |
| **Sparsity** | No | Yes (~50%) |
| **Expressivity** | Limited | Better |
| **Accuracy** | Lower | Higher |
| **Speed** | Fastest | Very Fast |
| **Use Case** | Edge, extreme constraints | Balanced performance |

## Binary Neural Networks

### 1. BinaryConnect (2015)

First method for training binary networks:

```python
import torch
import torch.nn as nn

class BinaryConnectLinear(nn.Module):
    """
    BinaryConnect: Training Deep Neural Networks with Weights
    and Activations Constrained to +1 or -1.
    """

    def __init__(self, in_features, out_features):
        super().__init__()
        # Store full-precision weights
        self.weight = nn.Parameter(
            torch.randn(out_features, in_features)
        )
        self.bias = nn.Parameter(torch.zeros(out_features))

    def binarize_weights(self):
        """Binarize weights using sign function."""
        return torch.sign(self.weight)

    def forward(self, x):
        # Forward: use binary weights
        binary_w = self.binarize_weights()
        output = nn.functional.linear(x, binary_w, self.bias)

        # Backward: straight-through estimator
        # Gradients flow through the binarization
        return output

    def backward_pass(self, grad_output):
        """
        STE: Use full-precision weights for gradient computation.

        The gradient of sign(x) is 0 almost everywhere,
        so we bypass it during backprop.
        """
        # Gradient uses full-precision weight
        grad_weight = grad_output @ self.weight.T
        grad_bias = grad_output.sum(dim=0)

        return grad_weight, grad_bias
```

### 2. Binarized Neural Networks (BNN)

Both weights and activations are binary:

```python
class BNNLayer(nn.Module):
    """
    Binarized Neural Networks (BNN)

    Weights: {-1, +1}
    Activations: {-1, +1}
    """

    def __init__(self, in_features, out_features):
        super().__init__()
        self.weight = nn.Parameter(
            torch.randn(out_features, in_features)
        )
        # Batch normalization is crucial for BNNs
        self.bn = nn.BatchNorm1d(in_features)

    def binarize(self, x):
        """Deterministic binarization using sign."""
        return torch.sign(x)

    def forward(self, x):
        # Batch norm (keeps activations in good range)
        x = self.bn(x)

        # Binarize input
        binary_x = self.binarize(x)

        # Binarize weights
        binary_w = self.binarize(self.weight)

        # Binary matrix multiplication using XNOR+popcount
        output = xnor_binary_matmul(binary_x, binary_w)

        return output

def xnor_binary_matmul(a, b):
    """
    Efficient binary matrix multiplication.

    Binary matmul = XNOR + popcount
    -1 XOR -1 = 0, -1 XOR +1 = 1, +1 XOR -1 = 1, +1 XOR +1 = 0
    XNOR: 1 if same, 0 if different (NOT XOR)
    popcount: count number of 1s
    """
    # Convert to binary (0/1) representation
    a_binary = (a == 1).float()
    b_binary = (b == 1).float()

    # XNOR operation
    xnor_result = torch.eq(a_binary.unsqueeze(-1), b_binary.unsqueeze(0))

    # Popcount (sum along dimension)
    result = 2 * xnor_result.sum(dim=-1) - a.size(-1)

    return result.float()
```

### 3. Binary Weight Networks (BWN)

Only weights are binary, activations remain full precision:

```python
class BWNLinear(nn.Module):
    """
    Binary Weight Networks

    Weights: {-1, +1} scaled by factor α
    Activations: Full precision
    """

    def __init__(self, in_features, out_features):
        super().__init__()
        self.weight = nn.Parameter(
            torch.randn(out_features, in_features)
        )
        # Learnable scaling factor
        self.alpha = nn.Parameter(torch.ones(out_features, 1))

    def forward(self, x):
        # Binarize weights
        binary_w = torch.sign(self.weight)

        # Scale by learned factor
        scaled_w = self.alpha * binary_w

        # Full-precision matrix multiply
        output = nn.functional.linear(x, scaled_w)

        return output

    def compute_alpha(self):
        """Compute optimal scaling factor."""
        # α = mean(|W|) * mean(|X|) / mean(|B ⊙ X|)
        # Where B is binary weights
        with torch.no_grad():
            binary_w = torch.sign(self.weight)
            self.alpha.data = self.weight.abs().mean(dim=1, keepdim=True)
```

## Ternary Neural Networks

### 1. Trained Ternary Quantization (TTQ)

```python
class TTQLinear(nn.Module):
    """
    Trained Ternary Quantization

    Weights: {-1, 0, +1} with learnable scales
    """

    def __init__(self, in_features, out_features, sparsity=0.5):
        super().__init__()
        self.weight = nn.Parameter(
            torch.randn(out_features, in_features)
        )

        # Scaling factors for positive and negative weights
        self.delta_pos = nn.Parameter(torch.ones(1))
        self.delta_neg = nn.Parameter(torch.ones(1))

        self.sparsity = sparsity

    def ternarize_ttq(self, weight):
        """
        TTQ: Learned ternary quantization.

        w = Δ⁺ × t⁺ + Δ⁻ × t⁻
        where t ∈ {-1, 0, +1}
        """
        w = weight.data

        # Compute threshold for sparsity
        threshold = torch.quantile(
            w.abs().flatten(),
            self.sparsity
        )

        # Create ternary mask
        mask_pos = (w > threshold).float()
        mask_neg = (w < -threshold).float()
        mask_zero = (w.abs() <= threshold).float()

        # Ternary weights
        ternary_w = mask_pos - mask_neg

        # Gradients for scaling factors
        if self.training:
            # Update Δ⁺ based on positive weight magnitudes
            pos_weights = w * mask_pos
            if mask_pos.sum() > 0:
                self.delta_pos.data = pos_weights.sum() / mask_pos.sum()

            # Update Δ⁻ based on negative weight magnitudes
            neg_weights = w * mask_neg
            if mask_neg.sum() > 0:
                self.delta_neg.data = -neg_weights.sum() / mask_neg.sum()

        # Apply scaling
        scaled_w = (
            self.delta_pos * mask_pos +
            self.delta_neg * mask_neg
        )

        return scaled_w

    def forward(self, x):
        ternary_w = self.ternarize_ttq(self.weight)
        return nn.functional.linear(x, ternary_w)
```

### 2. Sparsity-Aware Ternary Networks

```python
class SparsityAwareTernary(nn.Module):
    """
    Ternary network with explicit sparsity control.
    """

    def __init__(self, in_features, out_features, target_sparsity=0.6):
        super().__init__()
        self.weight = nn.Parameter(
            torch.randn(out_features, in_features)
        )
        self.target_sparsity = target_sparsity

        # Learnable threshold
        self.threshold = nn.Parameter(
            torch.tensor(0.05) * weight.abs().max()
        )

    def forward(self, x):
        # Adaptive ternarization
        ternary_w = self.adaptive_ternarize(self.weight)
        return nn.functional.linear(x, ternary_w)

    def adaptive_ternarize(self, weight):
        """Ternarize with learned threshold."""

        # Ternarization
        ternary = torch.zeros_like(weight)
        ternary[weight > self.threshold] = 1
        ternary[weight < -self.threshold] = -1

        # Straight-through estimator
        output = (ternary - weight).detach() + weight

        # Sparsity regularization
        if self.training:
            actual_sparsity = (ternary == 0).float().mean()
            sparsity_loss = (actual_sparsity - self.target_sparsity) ** 2

            # Adjust threshold to meet sparsity target
            if actual_sparsity > self.target_sparsity:
                # Too sparse, decrease threshold
                self.threshold.data *= 0.99
            else:
                # Not sparse enough, increase threshold
                self.threshold.data *= 1.01

        return output
```

## Training Binary/Ternary Networks

### 1. Two-Stage Training

```python
def train_two_stage(model, train_loader, val_loader, epochs_stage1, epochs_stage2):
    """
    Stage 1: Train full-precision model
    Stage 2: Fine-tune binary/ternary weights
    """

    # Stage 1: Full precision pre-training
    print("Stage 1: Full-precision pre-training")
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    train_full_precision(model, train_loader, optimizer, epochs_stage1)

    # Stage 2: Binary/ternary fine-tuning
    print("Stage 2: Binary/ternary fine-tuning")
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

    for epoch in range(epochs_stage2):
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.cuda(), target.cuda()

            optimizer.zero_grad()

            # Forward pass with binary/ternary weights
            output = model(data)
            loss = criterion(output, target)

            # Backward (STE handles binary gradients)
            loss.backward()
            optimizer.step()

        # Validation
        val_acc = validate(model, val_loader)
        print(f"Epoch {epoch}: Val Acc = {val_acc:.2f}%")

    return model
```

### 2. Knowledge Distillation for Binary Networks

```python
def distill_to_binary(teacher_model, student_model, train_loader, temperature=5):
    """
    Distill knowledge from full-precision teacher to binary student.
    """

    kl_loss = nn.KLDivLoss(reduction='batchmean')
    ce_loss = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(student_model.parameters())

    for batch in train_loader:
        data, target = batch
        data, target = data.cuda(), target.cuda()

        optimizer.zero_grad()

        # Teacher soft targets
        with torch.no_grad():
            teacher_logits = teacher_model(data)
            teacher_probs = torch.softmax(teacher_logits / temperature, dim=-1)

        # Student predictions
        student_logits = student_model(data)
        student_log_probs = torch.log_softmax(student_logits / temperature, dim=-1)

        # Combined loss
        distill_loss = kl_loss(student_log_probs, teacher_probs) * (temperature ** 2)
        hard_loss = ce_loss(student_logits, target)

        loss = 0.7 * distill_loss + 0.3 * hard_loss

        loss.backward()
        optimizer.step()

    return student_model
```

## Hardware Optimization

### 1. CPU Optimization (XNOR-Net)

```python
import numpy as np

def xnor_popcount_cpu(a, b):
    """
    CPU-optimized binary matrix multiplication.

    Uses bitwise operations for maximum efficiency.
    """
    # Convert to binary representation (0/1)
    a_binary = (a > 0).astype(np.int8)
    b_binary = (b > 0).astype(np.int8)

    # XNOR using bitwise NOT XOR
    # In numpy: ~(a ^ b) but we need to handle bits carefully

    m, k = a_binary.shape
    k, n = b_binary.shape

    result = np.zeros((m, n), dtype=np.int32)

    # Manual XNOR + popcount
    for i in range(m):
        for j in range(n):
            # XNOR: 1 if bits are equal
            xnor = np.equal(a_binary[i], b_binary[:, j])
            # Popcount: count ones, convert to {-1, +1}
            result[i, j] = 2 * xnor.sum() - k

    return result.astype(np.float32)
```

### 2. GPU Optimization

```python
import torch

def binary_matmul_gpu(a, b):
    """
    GPU-optimized binary matrix multiplication.

    Uses packed bit representation for efficiency.
    """
    # Pack 32 binary values into 32-bit integer
    def pack_bits(tensor):
        batch, m, n = tensor.shape
        packed_n = (n + 31) // 32

        packed = torch.zeros(
            batch, m, packed_n,
            dtype=torch.int32,
            device=tensor.device
        )

        for i in range(packed_n):
            start_idx = i * 32
            end_idx = min(start_idx + 32, n)

            # Extract 32 bits and pack
            chunk = tensor[:, :, start_idx:end_idx]
            packed[:, :, i] = (
                chunk.view(batch, m, -1, 8) <<
                torch.arange(8, device=tensor.device)
            ).sum(dim=-1)

        return packed

    # Pack tensors
    a_packed = pack_bits((a > 0).int())
    b_packed = pack_bits((b > 0).int())

    # Efficient popcount using tensor cores
    result = torch.xor(a_packed.unsqueeze(-1), b_packed.unsqueeze(-2))
    result = result.sum(dim=-2)  # Popcount

    # Convert back to float
    result = (2 * result - a.size(-1)).float()

    return result
```

## State of the Art Results

| Model | Precision | Dataset | Accuracy Drop |
|-------|-----------|---------|---------------|
| ResNet-18 | FP32 | ImageNet | Baseline: 69.8% |
| ResNet-18 | Binary | ImageNet | 55.2% (-14.6%) |
| ResNet-18 | Ternary | ImageNet | 62.4% (-7.4%) |
| **ReActNet-A** | **Binary** | **ImageNet** | **67.1%** **(-2.7%)** |

### Best Practices

1. **Use Binary For:** Extreme edge constraints, latency-critical apps
2. **Use Ternary For:** Balanced accuracy-efficiency tradeoff
3. **Always use:** Batch normalization for stability
4. **Consider:** Knowledge distillation from full-precision models
5. **Hardware:** Check for native binary operation support

---

**Next:** [guides/4408: Quantizing for Production](./guides/4408-Quantizing-for-Production.md)

**Last Updated:** 2026-02-05

## References

### Related ai-engineering-curriculum Documents

- [4405: Sparsity + Quantization](4405-Sparsity-Quantization.md)
- [4406: 1.58-bit Quantization](4406-1.58-bit-Quantization.md)

---