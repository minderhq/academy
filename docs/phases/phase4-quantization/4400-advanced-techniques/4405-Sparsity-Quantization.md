---
Document ID: 4405
Title: Sparsity + Quantization
Phase: 4
Module: 4400
Last Updated: 2026-02-05
Status: Review
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: 4101, 4401
Related: 4402, 4406
Tags: ['quantization', 'sparsity', 'optimization']
---

# 4405: Sparsity + Quantization

## Abstract

Combining sparsity (pruning) with quantization achieves extreme compression while maintaining model accuracy.

## Why Combine Sparsity + Quantization?

**Synergistic Effects:**
- **Sparsity:** Removes redundant weights (0s)
- **Quantization:** Reduces bit width of remaining weights
- **Result:** 10-50x compression with minimal accuracy loss

```text
Dense FP32:      100% size, 100% accuracy
Sparse INT8:      25% size,  98% accuracy
Sparse INT4:      12% size,  95% accuracy
```

## Types of Sparsity

### 1. Unstructured Sparsity

Random individual weights become zero:

```python
import torch.nn.utils.prune as prune

def prune_model(model, sparsity=0.5):
    """Apply unstructured L1 pruning."""
    for name, module in model.named_modules():
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            prune.l1_unstructured(
                module,
                name='weight',
                amount=sparsity
            )
    return model

# 50% of weights become zero
model = prune_model(model, sparsity=0.5)
```

**Advantages:**
- Easy to implement
- Good accuracy preservation
- Flexible sparsity levels

**Challenges:**
- Irregular memory access
- No speedup without special hardware
- Difficult to quantize efficiently

### 2. Structured Sparsity

Remove entire structures (channels, heads, layers):

```python
def prune_structured(model, sparsity=0.3):
    """Remove entire output channels."""
    for module in model.modules():
        if isinstance(module, nn.Conv2d):
            prune.ln_structured(
                module,
                name='weight',
                amount=sparsity,
                n=2,  # L2 norm
                dim=0  # Prune channels
            )
    return model
```

**Types:**
- **Channel pruning:** Remove entire output channels
- **Filter pruning:** Remove convolution filters
- **Head pruning:** Remove attention heads
- **Layer pruning:** Remove entire layers

**Advantages:**
- Regular memory patterns
- Hardware acceleration possible
- Better for quantization

### 3. Semi-Structured Sparsity (2:4)

Fixed pattern: 2 zeros out of every 4 elements:

```python
import torch

def apply_2to4_sparsity(tensor):
    """Apply 2:4 semi-structured sparsity pattern."""
    # Process in blocks of 4
    original_shape = tensor.shape
    tensor = tensor.view(-1, 4)

    # Find smallest 2 values in each block of 4
    _, indices = torch.topk(torch.abs(tensor), k=2, dim=1, largest=False)

    # Create mask
    mask = torch.ones_like(tensor)
    mask.scatter_(1, indices, 0)

    # Apply mask
    result = tensor * mask
    return result.view(original_shape)
```

**Hardware Support:**
- NVIDIA Ampere+ (Tensor Cores)
- Intel AVX-512 VNNI
- Apple Neural Engine

## Quantization for Sparse Models

### 1. Post-Training Quantization

```python
def quantize_sparse_model(model, calibration_loader):
    """Quantize sparse model with calibration."""

    # 1. Identify sparse weights
    sparse_mask = {}
    for name, param in model.named_parameters():
        if 'weight' in name:
            sparse_mask[name] = (param.data == 0)

    # 2. Collect activation statistics
    activation_stats = collect_stats(model, calibration_loader)

    # 3. Compute scale factors for non-zero weights
    scales = {}
    for name, param in model.named_parameters():
        if 'weight' in name:
            # Only consider non-zero weights
            nonzero = param.data[~sparse_mask[name]]
            scales[name] = compute_scale(nonzero)

    # 4. Quantize
    for name, param in model.named_parameters():
        if 'weight' in name:
            param.data = quantize(
                param.data,
                scales[name],
                sparse_mask[name]
            )

    return model
```

### 2. Quantization-Aware Training with Sparsity

```python
class SparseQuantAwareTraining:
    def __init__(self, model, sparsity=0.5):
        self.model = model
        self.sparsity = sparsity
        self.pruning_schedule = self._create_schedule()

    def _create_schedule(self):
        """Gradual pruning schedule."""
        return {
            0: 0.0,     # Start with no pruning
            100: 0.2,   # 20% at step 100
            500: 0.5,   # 50% at step 500
            1000: 0.5   # Maintain 50%
        }

    def step(self, current_step, optimizer):
        """Training step with pruning and quantization."""

        # 1. Update sparsity level
        target_sparsity = self._get_sparsity(current_step)

        # 2. Apply pruning
        if current_step % 100 == 0:
            self._prune_model(target_sparsity)

        # 3. Forward with fake quantization
        with torch.cuda.amp.autocast():
            output = self._fake_quant_forward(self.model)

        # 4. Backward
        loss.backward()

        # 5. Zero out gradients for pruned weights
        self._mask_gradients()

        # 6. Optimizer step
        optimizer.step()

    def _prune_model(self, sparsity):
        """Apply magnitude-based pruning."""
        for name, param in self.model.named_parameters():
            if 'weight' in name:
                # Compute threshold
                weight_abs = torch.abs(param.data)
                threshold = torch.quantile(
                    weight_abs.flatten(),
                    sparsity
                )

                # Create and apply mask
                mask = (weight_abs > threshold).float()
                param.data *= mask

    def _fake_quant_forward(self, model):
        """Forward pass with fake quantization."""
        # Apply fake quantization to weights
        for name, module in model.named_modules():
            if hasattr(module, 'weight'):
                # Fake quantize
                w = module.weight.data
                scale = w.abs().max() / 127
                module.weight.data = torch.round(w / scale) * scale

        return model
```

## Sparsity-Aware Quantization Techniques

### 1. Outlier-Aware Quantization

Handle outliers in sparse distributions:

```python
def outlier_aware_quantize(tensor, bits=8):
    """Quantize with outlier handling."""

    # Flatten tensor
    t = tensor.flatten()

    # Detect outliers (> 3 std from mean)
    mean, std = t.mean(), t.std()
    outliers = (t - mean).abs() > 3 * std

    # Separate outliers
    normal_values = t[~outliers]
    outlier_values = t[outliers]

    # Quantize normal values
    scale = (normal_values.max() - normal_values.min()) / (2**bits - 1)
    zero_point = (-normal_values.min() / scale).round().clamp(0, 2**bits - 1)

    # Store outliers separately
    outlier_indices = torch.where(outliers)[0]

    return {
        'quantized': quantize(normal_values, scale, zero_point),
        'scale': scale,
        'zero_point': zero_point,
        'outliers': outlier_values,
        'outlier_indices': outlier_indices
    }
```

### 2. Group-Wise Quantization for Sparse Models

```python
def group_wise_sparse_quantize(tensor, group_size=64):
    """Quantize sparse tensors in groups."""

    # Reshape into groups
    tensor_2d = tensor.view(-1, group_size)

    # Process each group
    quantized_groups = []
    scales = []
    zero_points = []
    masks = []

    for group in tensor_2d:
        # Find non-zero elements
        mask = group != 0
        nonzero = group[mask]

        if len(nonzero) > 0:
            # Quantize non-zero values
            scale = nonzero.abs().max() / 127
            quantized = torch.round(nonzero / scale).clamp(-127, 127)
        else:
            scale = 1.0
            quantized = torch.zeros_like(group)

        quantized_groups.append(quantized)
        scales.append(scale)
        masks.append(mask)

    return {
        'quantized': quantized_groups,
        'scales': scales,
        'masks': masks
    }
```

## Hardware Acceleration

### NVIDIA Sparse Tensor Cores (Ampere+)

```python
# Automatic 2:4 sparse support
import torch

# Enable sparse support (Ampere+)
with torch.backends.cudnn.flags(enabled=True, allow_tf32=True):
    output = model(input)

# NVIDIA provides 2x speedup for 2:4 sparse matrices
```

### Intel AMX (Advanced Matrix Extensions)

```python
# Intel sparsity support (4th Gen Xeon+)
# OneAPI toolkit
import intel_extension_for_pytorch as ipex

model = ipex.optimize(model, dtype=torch.bfloat16)
```

## Best Practices

### 1. Prune Before Quantize

```python
# Wrong order: Quantize then prune
model = quantize(model)  # Loses info about small weights
model = prune(model)     # Already lost precision

# Correct order: Prune then quantize
model = prune(model)     # Remove redundant weights first
model = quantize(model)  # Quantize remaining weights
```

### 2. Iterative Refinement

```python
def iterative_prune_quantize(model, target_sparsity, bits):
    """Gradually increase sparsity and decrease bits."""

    current_sparsity = 0.3
    current_bits = 16

    while current_sparsity < target_sparsity or current_bits > bits:
        # Prune
        model = prune(model, current_sparsity)

        # Quantize-aware finetune
        model = finetune_qat(model, current_bits)

        # Increase sparsity
        current_sparsity = min(current_sparsity + 0.1, target_sparsity)

        # Decrease bits
        current_bits = max(current_bits // 2, bits)

    return model
```

### 3. Maintain Critical Weights

```python
def importance_aware_pruning(model, sparsity=0.5):
    """Preserve important weights during pruning."""

    # Compute importance scores
    importance = {}
    for name, param in model.named_parameters():
        if 'weight' in name:
            # Magnitude × gradient sensitivity
            grad = param.grad
            importance[name] = (param.data.abs() * grad.abs())

    # Protect top-k weights
    for name, param in model.named_parameters():
        if name in importance:
            imp = importance[name].flatten()
            threshold = torch.quantile(imp, sparsity)
            mask = (imp > threshold).view(param.shape)
            param.data *= mask.float()

    return model
```

## Results Reference

| Model | Method | Sparsity | Bits | Size | Accuracy |
|-------|--------|----------|------|------|----------|
| LLaMA-7B | Baseline | 0% | 16 | 13GB | - |
| LLaMA-7B | Sparse only | 50% | 16 | 6.5GB | -0.5% |
| LLaMA-7B | Quant only | 0% | 4 | 3.3GB | -1.2% |
| LLaMA-7B | **Sparse + Quant** | 50% | 4 | **1.6GB** | **-1.8%** |

---

**Next:** [4406: 1.58-bit Quantization](./4406-1.58-bit-Quantization.md)

**Last Updated:** 2026-02-05
