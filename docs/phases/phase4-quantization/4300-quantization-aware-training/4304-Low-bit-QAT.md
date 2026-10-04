---
Document ID: 4304
Title: "4304: Low-bit QAT"
Phase: 4
Module: 4300
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'qat', 'quantization-aware-training']
---

# 4304: Low-bit QAT

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Bit-Width Comparison](#bit-width-comparison)
- [Challenges at Low Bits](#challenges-at-low-bits)
- [Advanced Techniques](#advanced-techniques)
- [Training Strategies](#training-strategies)
- [Practical Results](#practical-results)
- [Implementation Checklist](#implementation-checklist)
- [When to Use Each Bit-Width](#when-to-use-each-bit-width)
- [Summary](#summary)
- [Further Reading](#further-reading)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare the six bit-widths from the size/accuracy table — INT4's [-8, 7] grid at 12.5% size with 1-3% loss, INT3's [-4, 3] at 9.4% with 3-10%, and INT2's >10% loss marking it research-only
- Diagnose the two low-bit failure modes — dynamic-range growth pushing weights past the [-8, 7] grid, and a single outlier destroying a min-max scale (14.3 vs the 0.999-quantile's 0.46)
- Build the four low-bit techniques — LearnedClip's learnable clamp, MixedPrecisionQAT's per-layer bit_config (embeddings 8, MLP 3), PowerOfTwoScale via a learnable log2_scale, and LearnedStepSize's clamp(round(x/s), -8, 7)
- Apply the two training strategies — progressive_qat stepping 8→4→3 across [5, 5, 10] epochs, and knowledge distillation's batchmean KL × T² blended with CE by alpha
- Contrast the practical results tables — BERT SST-2 holding 93.0 at INT8 QAT but dropping to 91.5/88.2 at INT4/INT3, and GPT perplexity rising 12.4→13.8→16.2
- Execute the 4-bit checklist — per-channel weight scales, quantile-based clipping, 8-bit embeddings, progressive bit-width reduction, distillation, and activation-range monitoring

---

## Abstract

Low-bit quantization (4-bit, 3-bit, 2-bit) pushes model compression to the extreme but requires specialized techniques.

## Bit-Width Comparison

| Bit-Width | Range | Model Size | Accuracy Loss | Use Case |
|-----------|-------|------------|---------------|----------|
| **FP32** | ±3.4E38 | 100% | 0% | Training baseline |
| **FP16** | ±6.5E4 | 50% | <0.1% | Mixed precision training |
| **INT8** | -128 to 127 | 25% | <1% | Production standard |
| **INT4** | -8 to 7 | 12.5% | 1-3% | Edge deployment |
| **INT3** | -4 to 3 | 9.4% | 3-10% | Extreme compression |
| **INT2** | -2 to 1 | 6.25% | >10% | Research/experimental |

## Challenges at Low Bits

### Challenge 1: Limited Dynamic Range

At 4-bit symmetric: values can only be -8, -7, ..., 7

```python
import torch
# Problem: Weights can grow past the INT4 grid [-8, 7]
weight = torch.randn(256, 256)
print(weight.min(), weight.max())  # -3.2 to 3.5 (OK)
print(weight[0])  # Might be 2.5 (within range)

# But after gradient updates...
weight_after_training = weight * 2  # Scale grows
print(weight_after_training.min(), weight_after_training.max())  # -6.4 to 7.0 (at the grid edge)
```

**Solution:** Learned scale clipping
```python
import torch.nn as nn
import torch
class LearnedClip(nn.Module):
    """Learn optimal clipping range"""

    def __init__(self, init_clip=3.0):
        super().__init__()
        # Learnable clipping parameter
        self.clip = nn.Parameter(torch.tensor(init_clip))

    def forward(self, x):
        return torch.clamp(x, -self.clip, self.clip)
```

### Challenge 2: Quantile-based Quantization

Min-max is sensitive to outliers. Use quantiles instead:

```python
import torch
def get_quantile_scale(x, bit_width=4, q=0.999):
    """Use quantile instead of max for scale"""

    # Use 99.9th percentile instead of max
    qmax = torch.quantile(x.abs(), q)

    # Calculate scale
    qmax_int = 2 ** (bit_width - 1) - 1
    scale = qmax / qmax_int

    return scale

# Example
weight = torch.randn(1000)
weight[0] = 100  # Outlier

# Min-max: scale = 100/7 = 14.3 (terrible)
scale_minmax = weight.abs().max() / 7

# Quantile: scale = 3.2/7 = 0.46 (good)
scale_quantile = get_quantile_scale(weight, q=0.999)
```

## Advanced Techniques

### 1. Mixed Precision QAT

Different layers use different bit-widths:

```python
from torch.ao.quantization import FakeQuantize
import torch.nn as nn
class MixedPrecisionQAT(nn.Module):
    """Assign different bit-widths per layer"""

    def __init__(self, model, bit_config):
        super().__init__()
        self.model = model
        self.bit_config = bit_config

        # Create quantizers for each layer
        self.quantizers = nn.ModuleDict()
        for name, _ in model.named_modules():
            if name in bit_config:
                # ModuleDict keys may not contain "." — sanitize the
                # dotted module path before registering
                self.quantizers[name.replace('.', '__')] = FakeQuantize(
                    bit_width=bit_config[name]
                )

    def forward(self, x):
        # Apply layer-specific quantization
        ...

# Example configuration
bit_config = {
    'embeddings': 8,      # Keep embeddings at 8-bit
    'layer.0.attn': 8,    # Early layers: 8-bit
    'layer.1.attn': 4,    # Middle layers: 4-bit
    'layer.2.attn': 4,    # Later layers: 4-bit
    'layer.2.mlp': 3,     # MLP can go lower
}
```

### 2. Power-of-Two Scale

Restrict scales to powers of 2 for faster integer arithmetic:

```python
import torch.nn as nn
import torch
class PowerOfTwoScale(nn.Module):
    """Learn scale as power of 2"""

    def __init__(self):
        super().__init__()
        # Learn log2 scale (continuous)
        self.log2_scale = nn.Parameter(torch.tensor(0.0))

    @property
    def scale(self):
        # 2^x is always power of 2
        return 2 ** self.log2_scale

    def forward(self, x):
        return torch.round(x / self.scale) * self.scale
```

### 3. Stochastic Quantization

Replace deterministic rounding with stochastic rounding:

```python
import torch
def stochastic_round(x, scale):
    """Stochastic rounding for gradients"""

    x_scaled = x / scale
    floor = torch.floor(x_scaled)
    frac = x_scaled - floor

    # Randomly round up based on fractional part
    rand = torch.rand_like(frac)
    rounded = torch.where(rand < frac, floor + 1, floor)

    return rounded * scale

# Better gradient behavior at very low bits
```

### 4. Learned Step Size Quantization

Learn optimal quantization steps:

```python
import torch.nn as nn
import torch
class LearnedStepSize(nn.Module):
    """Learn quantization step size"""

    def __init__(self, shape=()):
        super().__init__()
        # Learnable step size
        self.step_size = nn.Parameter(torch.ones(shape))

    def quantize(self, x):
        x_q = torch.round(x / self.step_size)
        return torch.clamp(x_q, -8, 7) * self.step_size
```

## Training Strategies

### Strategy 1: Progressive Bit-width Reduction

Start high, gradually reduce:

```python
from torch.ao.quantization import FakeQuantize
def progressive_qat(model, epochs_per_bit=None):
    """Train at 8-bit, then 4-bit, then 3-bit"""
    if epochs_per_bit is None:
        epochs_per_bit = [5, 5, 10]

    bit_widths = [8, 4, 3]

    epoch = 0
    for bit, num_epochs in zip(bit_widths, epochs_per_bit):
        print(f"Training at {bit}-bit for {num_epochs} epochs")

        # Set all quantizers to current bit-width
        set_bit_width(model, bit)

        # Train
        for _ in range(num_epochs):
            train_epoch(model)
            epoch += 1

def set_bit_width(model, bit_width):
    """Update all quantizers to target bit-width"""
    for module in model.modules():
        if isinstance(module, FakeQuantize):
            module.bit_width = bit_width
            # Match the range to the quantizer's own symmetry —
            # symmetric bounds would corrupt asymmetric (0..2^bw-1) ones
            if module.symmetric:
                module.qmin = -2 ** (bit_width - 1)
                module.qmax = 2 ** (bit_width - 1) - 1
            else:
                module.qmin = 0
                module.qmax = 2 ** bit_width - 1
```

### Strategy 2: Knowledge Distillation

Use a larger model as teacher:

```python
import torch.nn as nn
import torch
def distillation_loss(student_output, teacher_output, labels, alpha=0.5, T=2.0):
    """Combine KD loss with CE loss"""

    # Soft targets from teacher
    teacher_soft = torch.softmax(teacher_output / T, dim=-1)
    student_soft = torch.log_softmax(student_output / T, dim=-1)

    # KL divergence loss
    kd_loss = nn.functional.kl_div(
        student_soft, teacher_soft,
        reduction='batchmean'
    ) * (T ** 2)

    # Standard cross-entropy
    ce_loss = nn.functional.cross_entropy(student_output, labels)

    # Combined
    return alpha * kd_loss + (1 - alpha) * ce_loss

# Training loop
teacher = load_teacher_model()  # FP32 or 8-bit
teacher.eval()

student = load_student_model()  # 4-bit
student.train()

for inputs, labels in dataloader:
    with torch.no_grad():
        teacher_output = teacher(inputs)

    student_output = student(inputs)
    loss = distillation_loss(student_output, teacher_output, labels)
    loss.backward()
```

## Practical Results

### BERT-style Model (110M params)

| Quantization | SST-2 Acc | MRPC Acc | CoLA Acc |
|--------------|-----------|----------|----------|
| FP32 | 93.2% | 89.5% | 58.2% |
| INT8 PTQ | 92.8% | 88.9% | 56.1% |
| INT8 QAT | 93.0% | 89.2% | 57.4% |
| INT4 QAT | 91.5% | 86.3% | 51.2% |
| INT3 QAT | 88.2% | 82.1% | 42.5% |

### GPT-style Model (1.3B params)

| Quantization | Perplexity | Loss |
|--------------|------------|------|
| FP32 | 12.4 | 2.52 |
| INT8 PTQ | 12.8 | 2.55 |
| INT8 QAT | 12.5 | 2.53 |
| INT4 QAT | 13.8 | 2.62 |
| INT3 QAT | 16.2 | 2.78 |

## Implementation Checklist

For successful 4-bit QAT:

- [ ] Use per-channel quantization for weights
- [ ] Apply clipping for outliers
- [ ] Use quantile-based scale calculation
- [ ] Consider mixed precision (embeddings at 8-bit)
- [ ] Start with pretrained model
- [ ] Use progressive bit-width reduction
- [ ] Consider knowledge distillation
- [ ] Monitor activation ranges
- [ ] Validate extensively

## When to Use Each Bit-Width

### 8-bit (INT8)
- Default choice
- Minimal accuracy loss
- Good speedup
- Use for most production

### 4-bit (INT4)
- Need smaller models
- Can tolerate 1-3% accuracy loss
- Have training data for QAT
- Deployment on edge/mobile

### 3-bit (INT3)
- Experimental
- Have ample training data
- Can accept larger accuracy loss
- Research applications

### 2-bit (INT2)
- Research only
- Requires special techniques
- Significant accuracy degradation
- Not production-ready

## Summary

Below 4 bits, quantization stops being a free lunch: 4-bit is the practical floor for most workloads, 3-bit needs careful per-layer allocation, and 2-bit is research territory. The advanced techniques that make low bits survivable - grouping, outlier handling, and quantization-aware training strategies - each buy accuracy back at training cost. The bit-width decision table is the takeaway: match the bit-width to your accuracy budget, not your ambition.

## Further Reading

- **Paper:** "LEGO: Learned Equality Gradient Optimization for Quantization" (2024)
- **Paper:** "QAT meets LLM: Training 4-bit Large Language Models" (2024)
- **Library:** bitsandbytes `NF4` quantization
- **Library:** AutoGPTQ 4-bit mode

## References

### Related Minder Academy Documents

- [4301: QAT Foundations](4301-QAT-Foundations.md)
- [4302: Fake Quantization](4302-Fake-Quantization.md)
- [4303: QAT for Transformers](4303-QAT-for-Transformers.md)
- [4305: Quantization Configuration](4305-Quantization-Configuration.md)

---

## Next Steps

→ **[4305: Quantization Configuration](./4305-Quantization-Configuration.md)** - Designing quantization schemes
