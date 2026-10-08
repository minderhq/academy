---
Document ID: 4300-PRACTICE
Title: "4300: Quantization Aware Training - Practice"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'quantization', 'qat']
---

# 4300: Quantization Aware Training - Practice

## Overview

This document contains hands-on exercises to reinforce your understanding of QAT.

## Exercise 1: Implement Fake Quantization

**Task:** Implement a basic fake quantization module with STE.

```python
import torch
import torch.nn as nn

class FakeQuantizeFunc(torch.autograd.Function):
    """Fake quantization with Straight-Through Estimator."""

    @staticmethod
    def forward(ctx, x, scale, zero_point, qmin, qmax):
        """
        Quantize-dequantize in forward pass.

        Args:
            x: Input tensor
            scale: Quantization scale
            zero_point: Zero point
            qmin: Minimum quantized value
            qmax: Maximum quantized value

        Returns:
            Dequantized tensor
        """
        # Quantize
        x_quant = torch.round(x / scale) + zero_point
        x_quant = torch.clamp(x_quant, qmin, qmax)

        # Dequantize
        x_dequant = (x_quant - zero_point) * scale

        ctx.save_for_backward(x, scale, zero_point)
        ctx.qmin = qmin
        ctx.qmax = qmax

        return x_dequant

    @staticmethod
    def backward(ctx, grad_output):
        """
        Straight-Through Estimator: Pass gradients through unchanged.
        """
        x, scale, zero_point = ctx.saved_tensors

        # STE: Clamp gradients to range where input was quantized
        qmin = ctx.qmin
        qmax = ctx.qmax

        # Gradient mask: inputs inside the representable window
        # [ (qmin - zero_point) * scale, (qmax - zero_point) * scale ]
        x_lower = (qmin - zero_point) * scale
        x_upper = (qmax - zero_point) * scale

        # Pass through gradients for inputs within quantization range
        grad_input = grad_output.clone()
        mask = (x >= x_lower) & (x <= x_upper)
        grad_input = grad_input * mask.float()

        return grad_input, None, None, None, None

class FakeQuantize(nn.Module):
    """Fake quantization module."""

    def __init__(self, bit_width=8, symmetric=True):
        super().__init__()
        self.bit_width = bit_width
        self.symmetric = symmetric

        # Compute quantization range
        if symmetric:
            self.qmin = -(2 ** (bit_width - 1))
            self.qmax = 2 ** (bit_width - 1) - 1
        else:
            self.qmin = 0
            self.qmax = (2 ** bit_width) - 1

        # Learnable parameters
        self.scale = nn.Parameter(torch.ones(1))
        self.zero_point = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        # Initialize scale and zero_point based on input statistics
        if self.training and self.scale.data == 1.0:
            x_max = x.abs().max()
            self.scale.data = x_max / self.qmax * 0.8  # Leave some margin

        return FakeQuantizeFunc.apply(x, self.scale, self.zero_point, self.qmin, self.qmax)

# Test
print("Testing Fake Quantization with STE")
print("="*60)

x = torch.randn(100, requires_grad=True)
fq = FakeQuantize(bit_width=8, symmetric=True)

# Forward pass
y = fq(x)
loss = y.sum()
loss.backward()

print(f"Input range: [{x.min():.2f}, {x.max():.2f}]")
print(f"Output range: [{y.min():.2f}, {y.max():.2f}]")
print(f"Gradient norm: {x.grad.norm():.4f}")
print(f"Gradient has NaNs: {torch.isnan(x.grad).any()}")

# Expected Output:
# Output range spans ≈ ±0.8 × input max (scale = max/qmax with a
# 0.8 margin; ±127 levels at 8 bits)
# Gradient norm: ~9-10 for randn(100) - the STE passes gradients
# for every input inside the quantization window (≈95% of a
# standard normal lies within ±2), so the norm ≈ sqrt of that count
# Gradient has NaNs: tensor(False)
```

---

## Exercise 2: Apply QAT to a Simple Model

**Task:** Apply fake quantization to a neural network.

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms

# Simple MNIST classifier
class MNISTClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Quantized version with fake quantization
class QuantizedMNISTClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 10)
        self.relu = nn.ReLU()

        # Add fake quantization after each Linear layer
        self.fq1 = FakeQuantize(bit_width=8)
        self.fq2 = FakeQuantize(bit_width=8)
        self.fq3 = FakeQuantize(bit_width=8)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = self.fq1(self.fc1(x))
        x = self.relu(x)
        x = self.fq2(self.fc2(x))
        x = self.relu(x)
        x = self.fq3(self.fc3(x))
        return x

def train_model(model, epochs=2, lr=0.001):
    """Train model on MNIST."""
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    # Load MNIST data (simplified)
    transform = transforms.Compose([transforms.ToTensor()])
    train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=64, shuffle=True)

    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_idx, (data, target) in enumerate(train_loader):
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            if batch_idx % 100 == 0:
                print(f"  Batch {batch_idx}: Loss = {loss.item():.4f}")

        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch+1}/{epochs}: Average Loss = {avg_loss:.4f}")

    return model

def evaluate_model(model):
    """Full test-set accuracy check (the metric the Success
    Criteria are written on - without it QAT's payoff is unmeasured)."""
    transform = transforms.Compose([transforms.ToTensor()])
    test_dataset = datasets.MNIST('./data', train=False, download=True, transform=transform)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=256, shuffle=False)

    model.eval()
    correct = total = 0
    with torch.no_grad():
        for data, target in test_loader:
            pred = model(data).argmax(dim=1)
            correct += (pred == target).sum().item()
            total += target.size(0)

    model.train()
    return correct / total * 100

print("Training Models with and without QAT")
print("="*60)

print("\nTraining FP32 Model...")
model_fp32 = train_model(MNISTClassifier(), epochs=2)

print("\nTraining QAT Model...")
model_qat = train_model(QuantizedMNISTClassifier(), epochs=2)

acc_fp32 = evaluate_model(model_fp32)
acc_qat = evaluate_model(model_qat)

print("\nQAT training complete!")
print(f"FP32 accuracy: {acc_fp32:.2f}%")
print(f"QAT accuracy:  {acc_qat:.2f}%")
print(f"Accuracy drop: {acc_fp32 - acc_qat:.2f} percentage points")

# Expected Output:
# Each epoch prints 10 batch lines (every 100 of ~938 batches) plus
# the epoch average: loss falls from ~0.3 to ~0.1 over 2 epochs for
# an MLP on MNIST; the QAT run sits slightly above the FP32 run
# (quantization noise during training)
# Accuracy: FP32 ≈ 96-98%, QAT within ~1 point of it (8-bit QAT on
# MNIST typically loses <1%) - exact numbers vary run to run
```

**Success Criteria:**

- QAT model achieves >95% accuracy
- Accuracy loss <1% vs FP32

---

## Exercise 3: Per-Channel Quantization

**Task:** Implement per-channel quantization for Linear layers.

```python
import torch

def per_channel_quantize(weight, bit_width=8):
    """
    Quantize weight tensor per output channel.

    Args:
        weight: [out_features, in_features]
        bit_width: Target bit-width

    Returns:
        Quantized weight (same shape as input)
    """
    out_features, in_features = weight.shape

    # Quantization range
    qmin = -(2 ** (bit_width - 1))
    qmax = 2 ** (bit_width - 1) - 1

    # Compute scale and zero_point per channel
    weight_min = weight.amin(dim=1, keepdim=True)
    weight_max = weight.amax(dim=1, keepdim=True)

    scale = (weight_max - weight_min) / (qmax - qmin)
    zero_point = qmin - (weight_min / scale)
    zero_point = torch.clamp(torch.round(zero_point), qmin, qmax)

    # Quantize
    weight_quant = torch.round(weight / scale) + zero_point
    weight_quant = torch.clamp(weight_quant, qmin, qmax)

    # Dequantize
    weight_dequant = (weight_quant - zero_point) * scale

    return weight_dequant

def per_tensor_quantize(weight, bit_width=8):
    """Quantize weight tensor with single scale."""
    qmin = -(2 ** (bit_width - 1))
    qmax = 2 ** (bit_width - 1) - 1

    weight_min = weight.min()
    weight_max = weight.max()

    scale = (weight_max - weight_min) / (qmax - qmin)
    zero_point = qmin - (weight_min / scale)
    zero_point = torch.clamp(torch.round(zero_point), qmin, qmax)

    weight_quant = torch.round(weight / scale) + zero_point
    weight_quant = torch.clamp(weight_quant, qmin, qmax)
    weight_dequant = (weight_quant - zero_point) * scale

    return weight_dequant

# Test on a linear layer
print("\nPer-Channel vs Per-Tensor Quantization")
print("="*60)

weight = torch.randn(256, 128)  # [out_features, in_features]

weight_pc = per_channel_quantize(weight, bit_width=8)
weight_pt = per_tensor_quantize(weight, bit_width=8)

# Compute error with random input
inputs = torch.randn(64, 128)

original_output = inputs @ weight.t()
pc_output = inputs @ weight_pc.t()
pt_output = inputs @ weight_pt.t()

pc_error = (original_output - pc_output).abs().mean()
pt_error = (original_output - pt_output).abs().mean()

print(f"Per-channel error: {pc_error:.6f}")
print(f"Per-tensor error: {pt_error:.6f}")
print(f"Improvement: {(pt_error - pc_error) / pt_error * 100:.2f}%")

# Expected Output:
# Per-channel error is the lower of the two - each row gets its own
# step, and a row's range never exceeds the tensor's, so its step
# can only be finer. On a Gaussian tensor the gap is modest (rows
# have similar ranges); it widens when channels carry outliers
```

---

## Exercise 4: Debugging QAT

**Task:** Find and fix common QAT issues.

```python
print("\nDebugging Common QAT Issues")
print("="*60)

# Broken Code Example with bugs
bugs = """
Bug 1: FakeQuantize never initializes
  Issue: Model left in eval mode - the scale init inside
         forward() only runs when self.training
  Fix: Call model.train() before QAT training or calibration

Bug 2: Missing scale initialization
  Issue: scale not initialized based on input statistics
  Fix: set scale based on input range in first forward pass

Bug 3: Quantizing attention scores
  Issue: Applying quantization to attention weights (softmax output)
  Fix: Only quantize Q, K, V projections, not attention scores

Bug 4: Wrong placement of fake quantization
  Issue: Quantizing after residual addition
  Fix: Quantize the branch output, add the residual in higher
       precision
"""

print("Common QAT Bugs:")
print(bugs)

print("\nBest Practices:")
print("""
1. Quantize weights and activations, not intermediate values
2. Use per-channel quantization for Linear layers
3. Keep layer normalization in FP32
4. Quantize after activation functions
5. Use symmetric quantization for weights
6. Use asymmetric quantization for activations
7. Initialize scale based on calibration data
8. Monitor accuracy during training
""")

# Expected Output:
# The "Common QAT Bugs" list (4 bugs) and the 8-item "Best
# Practices" list print directly - no model runs in this exercise
```

---

## Exercise 5: PyTorch Native QAT

```python
import torch
import torch.nn as nn
import torch.ao.quantization as quant

# Define model
class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(256, 10)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

print("PyTorch Native QAT")
print("="*60)

model = SimpleModel()

# Step 1: set qconfig
model.qconfig = quant.get_default_qat_qconfig('fbgemm')

# Step 2: Prepare for QAT
model_prepared = quant.prepare_qat(model, inplace=False)

print("Model prepared for QAT")
print(f"QConfig: {model.qconfig}")

# Step 3: Train (simplified)
print("\nTraining with QAT (1 epoch)...")
optimizer = torch.optim.SGD(model_prepared.parameters(), lr=0.01)
criterion = nn.CrossEntropyLoss()

# Dummy training step
dummy_input = torch.randn(32, 784)
dummy_target = torch.randint(0, 10, (32,))

model_prepared.train()
optimizer.zero_grad()
output = model_prepared(dummy_input)
loss = criterion(output, dummy_target)
loss.backward()
optimizer.step()

print(f"Training loss: {loss.item():.4f}")

# Step 4: Convert to quantized model
model_quantized = quant.convert(model_prepared, inplace=False)

print("\nModel converted to INT8")

# Step 5: Compare size
def get_model_size(model):
    torch.save(model.state_dict(), 'temp.pt')
    size = __import__('os').path.getsize('temp.pt') / (1024 * 1024)
    __import__('os').remove('temp.pt')
    return size

size_fp32 = get_model_size(model)
size_int8 = get_model_size(model_quantized)

print(f"\nFP32 size: {size_fp32:.2f} MB")
print(f"INT8 size: {size_int8:.2f} MB")
print(f"Compression: {size_fp32 / size_int8:.2f}x")

# Expected Output:
# "Model prepared for QAT", the QConfig repr, one training loss
# ≈ 2.3 (ln 10 - a fresh 10-class head on random inputs), then
# "Model converted to INT8" and sizes ≈ 0.78 MB -> ≈ 0.20 MB
# (compression ≈ 4x - the Linear weights go FP32 -> INT8)
```

---

## Summary: QAT Workflow

```text
QUANTIZATION AWARE TRAINING STEPS:

1. Model Preparation
   - Insert FakeQuantize modules
   - Set quantization config
   - Choose symmetric/asymmetric

2. Training
   - Train with fake quantization
   - Model learns quantization-friendly weights
   - Monitor accuracy

3. Calibration
   - Run representative data
   - Determine activation ranges
   - Set scale and zero_point

4. Conversion
   - Replace FakeQuantize with real quantization
   - Convert to INT8/INT4
   - Verify accuracy

TIPS:
- Start with PTQ before QAT
- Use per-channel quantization for weights
- Keep LayerNorm in FP32
- Calibrate with representative data
- Monitor accuracy during training
- Compare with FP32 baseline
```
