---
Document ID: 4103
Title: Double Quantization - BitsAndBytes (bnb) Logic
Phase: 4
Module: 4100
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'gguf', 'exl2', 'awq', 'compression']
---

# 4103: Double Quantization - BitsAndBytes (bnb) Logic

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Problem with Standard Quantization](#the-problem-with-standard-quantization)
- [Double Quantization Solution](#double-quantization-solution)
- [BitsAndBytes Implementation](#bitsandbytes-implementation)
- [Memory Savings](#memory-savings)
- [Quality Impact](#quality-impact)
- [Advanced DQ Techniques](#advanced-dq-techniques)
- [BitsAndBytes Training](#bitsandbytes-training)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain The Problem with Standard Quantization
- Explain Double Quantization Solution
- Configure and operate BitsAndBytes Implementation
- Explain Memory Savings
- Explain Quality Impact
- Explain Advanced DQ Techniques

---

## Abstract
Double Quantization (DQ) is a technique introduced by bitsandbytes to further compress quantization parameters. It quantizes the quantization scales themselves, providing additional memory savings with minimal quality loss.

## The Problem with Standard Quantization

### Standard 4-bit Quantization Memory
```text
For a weight matrix W ∈ ℝ^(m×n):

Standard 4-bit:
  - Weights: m × n × 0.5 bytes = 0.5mn bytes
  - Scales: m × n/g × 2 bytes (fp16) = 2mn/g bytes
  - Zero points: m/g × 1 byte = m/g bytes

  Total: 0.5mn + 2mn/g + m/g bytes

  For g=128 (group size), m=4096, n=4096:
  - Weights: 0.5 × 16M = 8 MB
  - Scales: 2 × 16M / 128 = 256 KB
  - Zero points: 4096 / 128 = 32 B
  - Total: ~8.3 MB

The scales and zero points add overhead!
```

### Visualizing Memory Layout
```text
Weight Matrix (4096 × 4096):
┌─────────────────────────────────────────┐
│  Weights (4-bit): 8 MB                   │
├─────────────────────────────────────────┤
│  Scales (fp16): 256 KB                   │  ← Overhead
├─────────────────────────────────────────┤
│  Zero points (8-bit): 32 B               │  ← Overhead
└─────────────────────────────────────────┘
Total: 8.26 MB (~3% overhead for metadata)
```

## Double Quantization Solution

### What is Double Quantized?
```text
Key idea: The scales themselves can be quantized!

Standard:
  W → Q → (4-bit weights, fp16 scales)

Double Quantization:
  W → Q → (4-bit weights, 8-bit scales, 8-bit scale scales)

Meta-meta: scales of scales!
```

### Double Quantization Formula
```text
Let c be the quantization constant for scales:

c = max(|scales|) / 127

For each scale s:
  s_quantized = round(s / c)
  s_dequantized = s_quantized × c

Memory saved:
  - fp16 scales: 2 bytes per group
  - 8-bit quantized scales: 1 byte per group
  - Plus: one 8-bit constant c per tensor

Savings: ~50% on scale storage
```

### DQ Implementation
```python
import torch

def double_quantize(weights, group_size=128):
    """
    Double quantization: quantize weights and scales
    """
    m, n = weights.shape

    # Reshape into groups
    weights_reshaped = weights.reshape(-1, group_size)

    # First quantization: weights to 4-bit
    scales_fp16 = weights_reshaped.abs().max(dim=-1).values / 8.0
    zeros = torch.zeros_like(scales_fp16)

    # Quantize weights
    weights_q = torch.clamp(
        torch.round(weights_reshaped / scales_fp16[:, None]) + 128,
        0, 255
    ).to(torch.uint8)

    # Second quantization: scales to 8-bit
    # Compute scale for scales
    scale_scale = scales_fp16.abs().max() / 127.0
    scale_zero = 128

    # Quantize scales
    scales_q = torch.clamp(
        torch.round(scales_fp16 / scale_scale) + scale_zero,
        0, 255
    ).to(torch.uint8)

    return {
        'weights_q': weights_q,
        'scales_q': scales_q,  # Now 8-bit!
        'scale_scale': scale_scale.to(torch.float16),
        'scale_zero': scale_zero,
    }

def double_dequantize(weights_q, scales_q, scale_scale, scale_zero, group_size=128):
    """
    Dequantize double-quantized weights
    """
    # Dequantize scales
    scales_fp16 = (scales_q.float() - scale_zero) * scale_scale.float()

    # Dequantize weights
    weights = (weights_q.float() - 128) * scales_fp16[:, None]

    return weights.reshape(-1)
```

## BitsAndBytes Implementation

### NF4 (4-bit NormalFloat)
```python
# BitsAndBytes NF4 quantization
import torch
from bitsandbytes.nn import Linear4bit

# Create a quantized layer
layer = Linear4bit(
    in_features=4096,
    out_features=4096,
    compute_dtype=torch.float16,
    quant_type='nf4',  # or 'fp4'
)

# NF4 properties:
# - NormalFloat distribution
# - Optimized for normally distributed weights
# - Better than uniform quantization
```

### NF4 Distribution
```python
def nf4_quantize(weights):
    """
    NF4: Quantized weights follow normal distribution
    """
    # Normalize weights to [-1, 1]
    max_val = weights.abs().max()
    weights_norm = weights / max_val

    # NF4 quantization levels (precomputed)
    # Optimized for normal distribution
    nf4_levels = torch.tensor([
        -1.0, -0.696, -0.525, -0.394, -0.212, -0.105,
        0.0, 0.105, 0.212, 0.394, 0.525, 0.696, 1.0
    ])

    # Find closest level
    indices = torch.searchsorted(nf4_levels, weights_norm)
    quantized = nf4_levels[indices]

    # Pack into 4-bit (2 values per byte)
    packed = pack_4bit(quantized)

    return packed
```

### BNB Configuration
```python
# bitsandbytes quantization config
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    # 4-bit quantization
    load_in_4bit=True,

    # Quantization type
    bnb_4bit_quant_type="nf4",  # or "fp4"

    # Double quantization
    bnb_4bit_use_double_quant=True,

    # Compute dtype
    bnb_4bit_compute_dtype=torch.float16,

    # Group size for quantization
    bnb_4bit_quant_storage=torch.uint8,
)

# Load model with BNB quantization
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",
)
```

## Memory Savings

### Standard vs Double Quantization
```text
Llama-2-7B (4096 × 4096 weights, 32 layers):

Standard 4-bit (no DQ):
  - Weights: 7B × 0.5 bytes = ~3.5 GB
  - Scales: ~0.1 GB
  - Total: ~3.6 GB

Double Quantization:
  - Weights: 7B × 0.5 bytes = ~3.5 GB
  - Quantized scales: ~0.05 GB (50% savings!)
  - Meta scales: ~0.001 GB (negligible)
  - Total: ~3.55 GB

Savings: ~0.05 GB per model
For 70B model: ~0.5 GB savings!
```

### Visual Comparison
```text
Without DQ:
Weights  ████████████████████ 3.5 GB
Scales   ███ 0.1 GB
         ─────────────────────
Total:   3.6 GB

With DQ:
Weights  ████████████████████ 3.5 GB
Scales   ██ 0.05 GB
Meta     0.001 GB
         ─────────────────────
Total:   3.55 GB
```

## Quality Impact

### Perplexity Comparison
```text
WikiText-2 Perplexity (lower is better):

Model           fp16    4-bit    4-bit+DQ
────────────────────────────────────────
Llama-2-7B      5.45    5.65     5.67
Llama-2-13B     4.92    5.08     5.10
Llama-2-70B     3.65    3.78     3.79

Quality loss from DQ: <0.5% (negligible!)
Memory savings: ~0.5-1%
```

### When to Use DQ
```text
Use Double Quantization:
✓ Limited VRAM (saving 0.5GB matters)
✓ Large models (70B+)
✓ Inference (not training)

Skip Double Quantization:
✓ Maximum quality required
✓ Plenty of VRAM
✓ Small models (7B, 13B)
```

## Advanced DQ Techniques

### Triple Quantization?
```text
Can we quantize the meta-scales?

Theoretically: Yes!
Practically: Diminishing returns

- Additional savings: <0.01 GB
- Quality loss: Starts to compound
- Complexity: Much higher

Conclusion: Not worth it
```

### Adaptive DQ
```python
# Different quantization per layer
adaptive_dq_config = {
    # Early layers: full precision scales
    "layers.0-10": {"use_double_quant": False},

    # Middle layers: double quantization
    "layers.11-25": {"use_double_quant": True},

    # Late layers: triple quantization (if desperate)
    "layers.26-31": {"use_double_quant": True, "quantize_meta": True},
}
```

## BitsAndBytes Training

### QLoRA with BNB
```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Quantization config (double quantization enabled)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,  # Enable DQ
    bnb_4bit_compute_dtype=torch.bfloat16,
)

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",
)

# Prepare for training
model = prepare_model_for_kbit_training(model)

# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Now you can fine-tune a 4-bit quantized model!
# Only LoRA parameters are trained (~1% of total)
```

## Troubleshooting

### Common Issues
```yaml
Issue: "CUDA out of memory"
Solution:
  - Reduce batch size
  - Enable gradient checkpointing
  - Use CPU offloading for some layers

Issue: "NaN loss during training"
Solution:
  - Reduce learning rate
  - Use bfloat16 instead of float16
  - Check gradient clipping

Issue: "Slow inference"
Solution:
  - Use torch.compile
  - Enable fused kernels
  - Batch inference requests
```

---

## References

### Related ai-engineering-curriculum Documents

- [4101: GGUF Physics - CPU/GPU Hybrid Offloading](4101-GGUF-Physics.md)
- [4102: EXL2 and AWQ - Extreme Quantization](4102-EXL2-and-AWQ.md)

---

## Next Steps

- Next Module: **[4200: KV Cache](../4200-kv-cache/)**
- Continue with: **[4201: Context Window Physics](../4200-kv-cache/4201-Context-Window-Physics.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [4101: GGUF Physics](./4101-GGUF-Physics.md)
- [4102: EXL2 and AWQ](./4102-EXL2-and-AWQ.md)
- [5102: QLoRA Pipelines](../../phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)

**Experiment Template:** [EXP_4103: Double Quantization](../../../../experiments/EXP_4103_DOUBLE_QUANT.md)
