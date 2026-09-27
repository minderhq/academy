---
Document ID: 4305
Title: Quantization Configuration
Phase: 4
Module: 4300
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'qat', 'quantization-aware-training']
---

# 4305: Quantization Configuration

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Configuration Dimensions](#configuration-dimensions)
- [Layer-wise Configuration](#layer-wise-configuration)
- [Per-Tensor vs Per-Channel](#per-tensor-vs-per-channel)
- [Symmetric vs Asymmetric](#symmetric-vs-asymmetric)
- [Dynamic vs Static Scale](#dynamic-vs-static-scale)
- [Selective Quantization](#selective-quantization)
- [Configuration Templates](#configuration-templates)
- [Auto-Configuration](#auto-configuration)
- [Validation Checklist](#validation-checklist)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Apply the six configuration dimensions — layer choice, per-layer precision, per-tensor/per-channel, symmetric/asymmetric, dynamic/static scale, and the skip-list
- Configure the transformer QAT_CONFIG layer-wise — 8-bit per-channel Q/K/O, 4-bit per-channel V and both MLP Linears, 8-bit per-tensor embeddings, norm1/norm2 marked quantize: False
- Contrast per-tensor vs per-channel scales — one scalar against [out_channels, 1] channel scales; activations tolerate per-tensor at 8-bit, weights need per-channel at 4-bit
- Justify symmetric weights vs asymmetric activations — zero-point-free ranges for centered distributions, learned zero-point (INT8 [-128, 127] with zp=-10) for ReLU-non-negative outputs
- Weigh dynamic vs static scales — per-batch x.abs().max()/127 computation for varying ranges against calibration-frozen buffers on fixed-point hardware
- Drive selective quantization by layer size (top-k largest), sensitivity analysis (quantize-one-at-a-time deltas vs baseline), and greedy auto-configuration stepping down until accuracy dips

---

## Abstract

Designing effective quantization configurations requires understanding which layers to quantize, which precision to use, and how to balance accuracy vs efficiency.

## Configuration Dimensions

```text
Quantization Config = {
    ├─ Which layers to quantize?
    ├─ What precision per layer?
    ├─ Per-tensor or per-channel?
    ├─ Symmetric or asymmetric?
    ├─ Dynamic or static scale?
    └─ Which operations to skip?
}
```

## Layer-wise Configuration

### What Each Layer Prefers

| Layer Type | Recommended Config | Rationale |
|------------|-------------------|-----------|
| **Embeddings** | 8-bit per-tensor | Large, need precision |
| **Q projection** | 8-bit per-channel | Attention sensitivity |
| **K projection** | 8-bit per-channel | Attention sensitivity |
| **V projection** | 4-bit per-channel | Can tolerate lower |
| **O projection** | 8-bit per-channel | Final output |
| **MLP expansion** | 4-bit per-channel | Larger dimension |
| **MLP projection** | 4-bit per-channel | Less sensitive |
| **Layer Norm** | Don't quantize | FP32 for stability |
| **Softmax** | Don't quantize | FP32 for probabilities |

### Configuration Example

```python
QAT_CONFIG = {
    # Embeddings
    'embeddings': {
        'bit_width': 8,
        'per_channel': False,
        'symmetric': True,
    },

    # Attention layers
    'layers.*.self_attn.q_proj': {
        'bit_width': 8,
        'per_channel': True,
        'symmetric': True,
    },
    'layers.*.self_attn.k_proj': {
        'bit_width': 8,
        'per_channel': True,
        'symmetric': True,
    },
    'layers.*.self_attn.v_proj': {
        'bit_width': 4,
        'per_channel': True,
        'symmetric': True,
    },
    'layers.*.self_attn.out_proj': {
        'bit_width': 8,
        'per_channel': True,
        'symmetric': True,
    },

    # MLP layers
    'layers.*.ffn.fc1': {
        'bit_width': 4,
        'per_channel': True,
        'symmetric': True,
    },
    'layers.*.ffn.fc2': {
        'bit_width': 4,
        'per_channel': True,
        'symmetric': True,
    },

    # Skip layer norm
    'layers.*.norm1': {
        'quantize': False,
    },
    'layers.*.norm2': {
        'quantize': False,
    },
}
```

## Per-Tensor vs Per-Channel

### Per-Tensor Quantization

Single scale for entire tensor:

```text
Weight [out_channels, in_channels]
├─ Scale: scalar
└─ All elements share same scale
```

**Advantages:**
- Faster computation
- Less metadata
- Simpler implementation

**Disadvantages:**
- Lower accuracy
- Sensitive to outliers
- Not ideal for weights

**Use when:**
- Quantizing activations
- Inference speed is critical
- Target is 8-bit (higher precision)

### Per-Channel Quantization

One scale per output channel:

```text
Weight [out_channels, in_channels]
├─ Scale: [out_channels, 1]
└─ Each output channel has its own scale
```

**Advantages:**
- Better accuracy
- Handles channel variance
- Essential for low-bit QAT

**Disadvantages:**
- Slightly slower
- More metadata
- More complex implementation

**Use when:**
- Quantizing weights
- Target is 4-bit or below
- Accuracy is critical

### Implementation

```python
def configure_per_tensor(module, bit_width=8):
    """Configure per-tensor quantization"""
    module.quantizer = FakeQuantize(
        bit_width=bit_width,
        per_channel=False
    )

def configure_per_channel(module, bit_width=8):
    """Configure per-channel quantization"""
    module.quantizer = FakeQuantize(
        bit_width=bit_width,
        per_channel=True
    )

# Apply to model
for name, module in model.named_modules():
    if 'fc' in name or 'proj' in name:
        configure_per_channel(module, bit_width=8)
    elif 'activation' in name:
        configure_per_tensor(module, bit_width=8)
```

## Symmetric vs Asymmetric

### Symmetric Quantization

```text
Range: [-scale * qmax, scale * qmax]
Zero-point: Always 0
Example (INT8): [-127, 127]
```

**Advantages:**
- Simpler computation (no zero-point)
- Faster inference
- Better for weights

**Disadvantages:**
- Wastes range if data is asymmetric
- Less efficient for activations (often ReLU-activated)

### Asymmetric Quantization

```text
Range: [scale * (qmin - zp), scale * (qmax - zp)]
Zero-point: Learned/observed
Example (INT8): [-128, 127] with zp = -10
```

**Advantages:**
- Better fits data distribution
- More efficient for activations (non-negative)
- Better range utilization

**Disadvantages:**
- Extra zero-point calculation
- Slightly slower inference

**Recommendation:**
- **Weights:** Symmetric (centered around 0)
- **Activations:** Asymmetric (often non-negative after ReLU)

## Dynamic vs Static Scale

### Static Scale (Fixed)

Scale determined during calibration/frozen during training:

```python
import torch
import torch.nn as nn
# fake_quantize is defined in 4301-QAT-Foundations.md — import or paste it
# here (clamp(round(x/scale)+zero_point) then dequantize back)

class StaticScaleQuantizer(nn.Module):
    def __init__(self, scale, zero_point=0):
        super().__init__()
        # Both qparams frozen at construction: no observer, no updates
        self.register_buffer('scale', torch.tensor(scale))
        self.register_buffer('zero_point', torch.tensor(zero_point))

    def forward(self, x):
        return fake_quantize(x, self.scale, self.zero_point)
```

**Use when:**
- Data distribution is stable
- Inference speed is critical
- Deploying on fixed-point hardware

### Dynamic Scale (Online)

Scale computed per input batch:

```python
class DynamicScaleQuantizer(nn.Module):
    def __init__(self, bit_width=8):
        super().__init__()
        self.bit_width = bit_width

    def forward(self, x):
        # Compute scale per batch
        scale = x.abs().max() / (2 ** (self.bit_width - 1) - 1)
        return fake_quantize(x, scale, 0)
```

**Use when:**
- Activation ranges vary widely
- Can afford runtime computation
- Accuracy is critical

## Selective Quantization

### Strategy 1: Quantize Larger Layers First

```python
def selective_qat_by_size(model, top_k=10):
    """Only quantize top-k largest layers"""

    # Get layer sizes
    layer_sizes = []
    for name, param in model.named_parameters():
        if 'weight' in name:
            size = param.numel()
            layer_sizes.append((name, size))

    # Sort by size
    layer_sizes.sort(key=lambda x: x[1], reverse=True)

    # Quantize top-k
    for name, _ in layer_sizes[:top_k]:
        enable_quantization_for_layer(model, name)
```

### Strategy 2: Sensitivity Analysis

```python
def sensitivity_analysis(model, calib_data):
    """Measure accuracy impact of quantizing each layer"""

    baseline = evaluate(model, calib_data)
    sensitivities = {}

    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            # Quantize only this layer
            enable_quantization_for_layer(model, name)
            acc = evaluate(model, calib_data)

            # Measure impact
            sensitivities[name] = baseline - acc

            # Disable for next iteration
            disable_quantization_for_layer(model, name)

    return sensitivities

# Result: {'layer.0.fc1': 0.5%, 'layer.1.fc2': 1.2%, ...}
# Skip layers with high sensitivity
```

### Strategy 3: Layer-wise Bit-width

```python
BIT_CONFIG = {
    # Earlier layers: higher precision
    'layers.0': 8,
    'layers.1': 8,
    'layers.2': 8,

    # Middle layers: can go lower
    'layers.3': 4,
    'layers.4': 4,
    'layers.5': 4,

    # Last layers: higher precision for output
    'layers.6': 8,
    'layers.7': 8,
}

def apply_layer_config(model, config):
    """Apply layer-specific bit-widths"""
    for pattern, bit_width in config.items():
        # named_modules (not state_dict — those keys are parameter names
        # like 'layers.0.fc1.weight', not module paths)
        for name, module in model.named_modules():
            if name.startswith(pattern) and isinstance(module, FakeQuantize):
                module.bit_width = bit_width
```

## Configuration Templates

### Template 1: Conservative (High Accuracy)

```python
CONSERVATIVE_CONFIG = {
    'target_bit_width': 8,
    'per_channel_weights': True,
    'per_tensor_activations': True,
    'symmetric_weights': True,
    'asymmetric_activations': True,
    'skip_layers': ['layer_norm', 'softmax'],
}
```

**Use case:** Production when accuracy is critical

**Expected accuracy loss:** <1%

### Template 2: Aggressive (Small Model)

```python
AGGRESSIVE_CONFIG = {
    'embeddings': 8,
    'early_layers': 8,
    'middle_layers': 4,
    'late_layers': 8,
    'per_channel': True,
    'symmetric': True,
    'skip_layers': ['layer_norm', 'softmax'],
}
```

**Use case:** Edge deployment with size constraints

**Expected accuracy loss:** 2-5%

### Template 3: Balanced

```python
BALANCED_CONFIG = {
    'attention': 8,
    'mlp': 4,
    'embeddings': 8,
    'per_channel_weights': True,
    'per_tensor_activations': True,
}
```

**Use case:** General production use

**Expected accuracy loss:** 1-2%

## Auto-Configuration

```python
def auto_configure(model, calib_loader, target_accuracy=0.98):
    """Automatically find optimal configuration"""

    # Start with all layers at 8-bit
    config = {layer: 8 for layer in get_quantizable_layers(model)}

    # Evaluate
    acc = evaluate_with_config(model, config, calib_loader)

    # Greedily reduce bits until accuracy drops
    # Rank by sensitivity_analysis() impact: least sensitive layers first
    for layer in sorted(config.keys(), key=impact_on_accuracy):
        if config[layer] > 4:
            config[layer] -= 2  # Try lower precision
            new_acc = evaluate_with_config(model, config, calib_loader)

            if new_acc < target_accuracy:
                config[layer] += 2  # Revert

    return config
```

## Validation Checklist

Before finalizing configuration:

- [ ] Analyzed layer sensitivity
- [ ] Tested per-channel vs per-tensor
- [ ] Verified skip layers (norm, softmax)
- [ ] Checked activation ranges
- [ ] Validated on holdout set
- [ ] Measured inference speedup
- [ ] Confirmed memory reduction
- [ ] Tested on target hardware

## References

### Related ai-engineering-curriculum Documents

- [4301: QAT Foundations](4301-QAT-Foundations.md)
- [4302: Fake Quantization](4302-Fake-Quantization.md)
- [4303: QAT for Transformers](4303-QAT-for-Transformers.md)
- [4304: Low-bit QAT](4304-Low-bit-QAT.md)

---

## Next Steps

→ **[guides/4306: PyTorch QAT](./guides/4306-PyTorch-QAT.md)** - Implementing QAT with PyTorch
