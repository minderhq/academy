---
Document ID: 4306
Title: "4306: PyTorch QAT Guide"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 2 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'qat', 'quantization-aware-training']
---

# 4306: PyTorch QAT Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [PyTorch QAT API Overview](#pytorch-qat-api-overview)
- [Basic Workflow](#basic-workflow)
- [Advanced Configuration](#advanced-configuration)
- [Skipping Layers](#skipping-layers)
- [Training Best Practices](#training-best-practices)
- [Debugging QAT](#debugging-qat)
- [Export for Deployment](#export-for-deployment)
- [Performance Measurement](#performance-measurement)
- [Common Issues](#common-issues)
- [Further Resources](#further-resources)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Drive the `torch.ao.quantization` QAT cycle end-to-end — `prepare_qat`, train, `convert` — and explain what `MinMaxObserver` records at each stage
- Author a custom `QConfig` (per-tensor activations, per-channel symmetric weights) and apply per-layer overrides where a layer's sensitivity demands it
- Leave fragile layers (LayerNorm, Softmax) in float with `qconfig=None` and defend the accuracy trade-off
- Schedule gradual QAT correctly: `qat_start`, `disable_fake_quant` on rollback, `disable_observer` for final calibration epochs, `MultiStepLR` milestones
- Inspect a QAT model with `print_qparams` and weight histograms, and diff behavior before/after `convert` to catch silent quantization damage
- Debug the classic QAT failures — missing observer modules, observers that never update, `AssertionError` at convert — down to root cause

---

## Abstract

PyTorch provides native support for Quantization Aware Training through `torch.ao.quantization`. This guide shows how to use it effectively.

## PyTorch QAT API Overview

```text
torch.ao.quantization
├── prepare_qat()           # Insert fake quant modules
├── convert()               # Convert to actual INT8
├── get_default_qat_qconfig() # Default configurations
└── MinMaxObserver          # Scale/zero-point observer
```

## Basic Workflow

### Step 1: Define Model

```python
import torch
import torch.nn as nn

class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(256, 10)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x
```

### Step 2: Prepare for QAT

```python
import torch.ao.quantization as quant

# Create model
model = SimpleModel()

# Set quantization configuration
model.qconfig = quant.get_default_qat_qconfig('x86')

# Prepare model for QAT
model = quant.prepare_qat(model, inplace=True)

# Now model has FakeQuantize modules inserted
print(model)
```

### Step 3: Train

```python
# Train as normal
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
criterion = nn.CrossEntropyLoss()

for epoch in range(5):
    for inputs, labels in train_loader:
        outputs = model(inputs)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

### Step 4: Convert

```python
# Convert to actual INT8
model_int8 = quant.convert(model.eval(), inplace=False)

# Check weights are now INT8
print(model_int8.fc1.weight().dtype)  # torch.qint8
```

## Advanced Configuration

### Custom QConfig

```python
import torch.ao.quantization as quant
from torch.ao.quantization import MinMaxObserver, MovingAverageMinMaxObserver

# Custom configuration
my_qconfig = quant.QConfig(
    activation=quant.MinMaxObserver.with_args(
        dtype=torch.quint8,  # Unsigned for activations
        qscheme=torch.per_tensor_affine,
    ),
    weight=quant.MinMaxObserver.with_args(
        dtype=torch.qint8,  # Signed for weights
        qscheme=torch.per_channel_symmetric,
    )
)

# Apply to model
model.qconfig = my_qconfig
model = quant.prepare_qat(model)
```

### Per-Layer Configuration

```python
def set_layer_qconfig(model):
    """Configure different layers differently"""

    # Embedding: 8-bit per-tensor
    model.embeddings.qconfig = quant.QConfig(
        activation=MinMaxObserver.with_args(dtype=torch.quint8),
        weight=MinMaxObserver.with_args(dtype=torch.qint8),
    )

    # Attention: 8-bit per-channel
    for name, module in model.named_modules():
        if 'attn' in name:
            module.qconfig = quant.get_default_qat_qconfig('x86')

        # MLP: 4-bit (if supported)
        elif 'mlp' in name:
            module.qconfig = quant.QConfig(
                activation=MinMaxObserver.with_args(dtype=torch.quint8),
                weight=MinMaxObserver.with_args(
                    dtype=torch.qint8,
                    qscheme=torch.per_channel_symmetric
                ),
            )

    return model

model = set_layer_qconfig(model)
model = quant.prepare_qat(model)
```

## Skipping Layers

```python
from torch.ao.quantization import FakeQuantize

def skip_layer_quantization(model, layer_types=['LayerNorm', 'Softmax']):
    """Prevent certain layers from being quantized"""

    def _set_no_quant(module):
        if type(module).__name__ in layer_types:
            module.qconfig = None
        for child in module.children():
            _set_no_quant(child)

    _set_no_quant(model)
    return model

# Usage
model = skip_layer_quantization(model)
model = quant.prepare_qat(model)
```

## Training Best Practices

### 1. Gradual QAT Enablement

```python
def train_with_gradual_qat(model, epochs, qat_start=3):
    """Start QAT after initial training"""

    for epoch in range(epochs):
        if epoch == qat_start:
            # Enable QAT
            model.train()
            print("QAT enabled")
        elif epoch < qat_start:
            # Disable fake quant (train in FP32)
            model.apply(torch.nn.quantized.disable_fake_quant)

        train_epoch(model)
```

### 2. Freezing Observers

```python
def freeze_observers(model):
    """Stop scale/zero-point from updating"""
    for module in model.modules():
        if isinstance(module, FakeQuantize):
            if hasattr(module, 'activation_post_process'):
                module.activation_post_process.disable_observer()

# Freeze after initial QAT epochs
epochs = 15  # demo scale - passes the freeze point
for epoch in range(epochs):
    train_epoch(model)
    if epoch == 10:
        freeze_observers(model)
        print("Observers frozen")
```

### 3. Learning Rate Scheduling

```python
import torch.optim.lr_scheduler as lr_scheduler

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

# Reduce LR when QAT starts
scheduler = lr_scheduler.MultiStepLR(
    optimizer,
    milestones=[3, 10],  # Epochs to reduce LR
    gamma=0.5  # Reduce by half
)

epochs = 20  # demo scale - passes the milestone
for epoch in range(epochs):
    train_epoch(model)
    scheduler.step()
```

## Debugging QAT

### Check Quantization Parameters

```python
def print_qparams(model):
    """Print scale and zero-point for each layer"""

    for name, module in model.named_modules():
        if hasattr(module, 'weight_fake_quant') or hasattr(module, 'activation_post_process'):
            print(f"\n{name}")

            if hasattr(module, 'weight_fake_quant'):
                w_fq = module.weight_fake_quant
                print(f"  Weight scale: {w_fq.scale}")
                print(f"  Weight zero_point: {w_fq.zero_point}")

            if hasattr(module, 'activation_post_process'):
                a_fq = module.activation_post_process
                if hasattr(a_fq, 'scale'):
                    print(f"  Act scale: {a_fq.scale}")
```

### Compare Before/After Conversion

```python
# Before conversion (fake quantized)
with torch.no_grad():
    output_fp32_sim = model(inputs)
    print("QAT output:", output_fp32_sim[0][:5])

# After conversion (actual INT8)
model_int8 = quant.convert(model.eval())
with torch.no_grad():
    output_int8 = model_int8(inputs)
    print("INT8 output:", output_int8[0][:5])

# Should be very similar
```

### Visualize Weight Distribution

```python
import matplotlib.pyplot as plt

def plot_weight_distribution(model, layer_name='fc1'):
    """Compare FP32 vs quantized weight distribution"""

    layer = dict(model.named_modules())[layer_name]

    # Original FP32 weights
    weight_fp32 = layer.weight()

    # Fake quantized weights
    weight_fq = layer.weight_fake_quant(layer.weight())

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].hist(weight_fp32.flatten().numpy(), bins=100)
    axes[0].set_title('FP32 Weights')
    axes[0].set_xlabel('Value')
    axes[0].set_ylabel('Count')

    axes[1].hist(weight_fq.flatten().numpy(), bins=100)
    axes[1].set_title('Fake Quantized Weights')
    axes[1].set_xlabel('Value')
    axes[1].set_ylabel('Count')

    plt.tight_layout()
    plt.show()
```

## Export for Deployment

### TorchScript Export

```python
# Convert model
model_int8 = quant.convert(model.eval())

# Script and save
scripted_model = torch.jit.script(model_int8)
torch.jit.save(scripted_model, 'model_quantized.pt')
```

### ONNX Export

```python
# Export to ONNX
import torch.onnx

model_int8 = quant.convert(model.eval())

dummy_input = torch.randn(1, 784)

torch.onnx.export(
    model_int8,
    dummy_input,
    'model_quantized.onnx',
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'},
    }
)
```

## Performance Measurement

### Accuracy Comparison

```python
def compare_accuracy(fp32_model, int8_model, test_loader):
    """Compare accuracy between FP32 and INT8"""

    fp32_model.eval()
    int8_model.eval()

    fp32_correct = int8_correct = total = 0

    with torch.no_grad():
        for inputs, labels in test_loader:
            # FP32 predictions
            fp32_outputs = fp32_model(inputs)
            fp32_pred = fp32_outputs.argmax(dim=1)
            fp32_correct += (fp32_pred == labels).sum()

            # INT8 predictions
            int8_outputs = int8_model(inputs)
            int8_pred = int8_outputs.argmax(dim=1)
            int8_correct += (int8_pred == labels).sum()

            total += labels.size(0)

    fp32_acc = fp32_correct / total
    int8_acc = int8_correct / total

    print(f"FP32 Accuracy: {fp32_acc:.4f}")
    print(f"INT8 Accuracy: {int8_acc:.4f}")
    print(f"Accuracy Loss: {fp32_acc - int8_acc:.4f}")
```

### Model Size Comparison

```python
import os

def get_model_size(model):
    """Get model size in MB"""
    torch.save(model.state_dict(), 'temp.pt')
    size = os.path.getsize('temp.pt') / (1024 * 1024)
    os.remove('temp.pt')
    return size

fp32_size = get_model_size(model)
int8_size = get_model_size(model_int8)

print(f"FP32 Size: {fp32_size:.2f} MB")
print(f"INT8 Size: {int8_size:.2f} MB")
print(f"Compression: {fp32_size / int8_size:.2f}x")
```

## Common Issues

### Issue 1: ModuleNotFoundError

```text
# Error
ModuleNotFoundError: No module named 'torch.ao.quantization'

# Fix: Use correct import path
import torch.quantization as quant  # Older PyTorch
# OR
import torch.ao.quantization as quant  # PyTorch 2.0+
```

### Issue 2: Observators Not Updating

```python
# Ensure model is in training mode
model.train()  # Enables observer updates

# Check observer status
for name, module in model.named_modules():
    if hasattr(module, 'activation_post_process'):
        print(f"{name}: observer_enabled={module.activation_post_process.training}")
```

### Issue 3: AssertionError on Convert

```text
# Error
AssertionError: No observers found

# Fix: Ensure prepare_qat was called
model = quant.prepare_qat(model)  # Don't skip this!

# And run at least one forward pass before convert
model(dummy_input)  # Calibrate observers
model = quant.convert(model)
```

## Summary

torch.ao.quantization gives you the whole QAT pipeline in three steps: prepare inserts fake-quant modules from a qconfig mapping, training adapts the weights to the simulated precision, and convert swaps fake-quant for real quantized ops. The working pattern from this guide: start from the default config, skip layers that measurably hurt, debug observer and dtype mismatches as they surface, and treat a measured speedup as the exit criterion - quantization that does not benchmark faster did not happen.

## Further Resources

- **Documentation:** [https://pytorch.org/docs/stable/quantization.html](https://pytorch.org/docs/stable/quantization.html)
- **Tutorial:** "Quantization Aware Training" (PyTorch tutorials)
- **Examples:** PyTorch GitHub examples/quantization

## References

### Related PROJECT-OMEGA Documents

- [4307: Transformers QAT Guide](4307-Transformers-QAT.md)
- [4308: BitBlade QAT Guide](4308-BitBlade-QAT.md)

---

## Next Steps

→ **[guides/4307: Transformers QAT](4307-Transformers-QAT.md)** - QAT with Hugging Face
