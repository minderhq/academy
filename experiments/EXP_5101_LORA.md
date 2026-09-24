---
Document ID: EXP_5101
Title: "EXP_5101: LoRA Fine-Tuning Experiments"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# EXP_5101: LoRA Fine-Tuning Experiments

## Overview
Practical experiments for LoRA (Low-Rank Adaptation) fine-tuning on an 11GB VRAM GPU.

## Experiment 1: LoRA Implementation from Scratch

### Objective
Implement LoRA from scratch to understand the mechanics.

### Implementation
```python
# lora_implementation.py
import torch
import torch.nn as nn
import math
from typing import List, Tuple

class LoRALinear(nn.Module):
    """
    LoRA Linear Layer

    Replaces a linear layer with:
    W = W_frozen + (B @ A) * scaling
    """
    def __init__(self, in_features: int, out_features: int, rank: int = 8, alpha: float = 16.0):
        super().__init__()
        self.rank = rank
        self.scaling = alpha / rank
        self.weight = nn.Parameter(torch.randn(out_features, in_features))
        self.weight.requires_grad = False
        self.lora_A = nn.Parameter(torch.randn(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        result = torch.nn.functional.linear(x, self.weight)
        lora_result = torch.nn.functional.linear(x, self.lora_B @ self.lora_A) * self.scaling
        return result + lora_result


def test_lora_implementation():
    """Test LoRA layer"""
    print("Testing LoRA Implementation")
    in_dim, out_dim, rank = 512, 512, 8
    lora = LoRALinear(in_dim, out_dim, rank=rank)
    x = torch.randn(2, 128, in_dim)
    output = lora(x)
    print(f"Input: {x.shape}, Output: {output.shape}")
    lora_params = sum(p.numel() for p in lora.parameters() if p.requires_grad)
    original_params = in_dim * out_dim
    print(f"LoRA params: {lora_params:,} vs Original: {original_params:,}")
    print(f"Reduction: {(1 - lora_params/original_params)*100:.1f}%")


if __name__ == "__main__":
    test_lora_implementation()
```

---

## Experiment 2: LoRA Hyperparameter Sweep

### Sweep Grid
```python
# lora_sweep.py
param_grid = {
    "r": [4, 8, 16, 32, 64],
    "alpha": [8, 16, 32, 64],
    "dropout": [0.0, 0.05, 0.1],
    "target_modules": [
        ["q_proj", "v_proj"],
        ["q_proj", "k_proj", "v_proj", "o_proj"],
        ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    ],
}
```

### Expected Results

| Rank | Alpha | Target Modules | Trainable % | VRAM |
|------|-------|----------------|-------------|------|
| 4 | 8 | q,v | 0.06% | ~4 GB |
| 8 | 16 | q,v | 0.12% | ~5 GB |
| 16 | 32 | q,v | 0.24% | ~6 GB |
| 32 | 64 | q,v | 0.48% | ~7 GB |
| 16 | 32 | all | 0.60% | ~8 GB |

---

## Experiment 3: LoRA vs Full Fine-tuning

```python
# compare_lora_full.py
from peft import LoraConfig, get_peft_model

# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
```

### Comparison

| Method | Params | VRAM | Speed | Quality |
|--------|--------|------|-------|---------|
| Full FT | 100% | >24GB | 1x | 100% |
| LoRA-16 | 0.24% | ~6GB | 2-3x | ~95% |
| QLoRA-16 | 0.24% | ~4GB | Similar | ~90% |

---

## Experiment Checklist

- [ ] LoRA implementation from scratch
- [ ] Hyperparameter sweep
- [ ] LoRA vs full FT comparison
- [ ] Adapter merging test
- [ ] Multi-adapter switching
- [ ] QLoRA testing
- [ ] Quality evaluation

---

## Related Documentation
- [5101: LoRA Logic](../docs/phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
- [5102: QLoRA Pipelines](../docs/phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)
