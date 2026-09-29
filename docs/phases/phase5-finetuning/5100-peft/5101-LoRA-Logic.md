---
Document ID: 5101
Title: "5101: LoRA (Low-Rank Adaptation) Logic"
Phase: 5
Module: 5100
Last Updated: 2026-09-28
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'peft', 'lora', 'qlora', 'adaptation']
---

# 5101: LoRA (Low-Rank Adaptation) Logic

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The LoRA Hypothesis](#the-lora-hypothesis)
- [LoRA Implementation](#lora-implementation)
- [Hyperparameter Selection](#hyperparameter-selection)
- [LoRA Variants](#lora-variants)
- [Training with LoRA](#training-with-lora)
- [LoRA for Specific Tasks](#lora-for-specific-tasks)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Quantify the LoRA hypothesis — ΔW = BAᵀ has rank r ≪ min(d,k): at r=8 a 4096×4096 projection carries 65,536 trainable params vs 16,777,216 (256×), and the kaiming-A / zero-B init makes every adapter start as an exact identity
- Build a `LoRALinear` and merge it correctly — frozen base, A (r×in) projecting down then B (out×r) up, scaling α/r — with a `merged` flag so folding ΔW into W doesn't double-count it in the forward
- Pick the three hyperparameters from the tables — the rank 2-4 / 8-16 / 32-64 capacity ladder, α = r or α = 2r scaling, and target-module configs with their real budgets on Llama-2-7B at r=8 (q+v 0.06%, all-attention 0.12%, +FFN ~0.30%)
- Route the variants to their use cases — input-side dropout (the PEFT convention), DoRA's magnitude/direction decomposition (`use_dora=True`), AdaLoRA's adaptive rank (`AdaLoraConfig`)
- Train through PEFT — `LoraConfig` + `get_peft_model` + `print_trainable_parameters` (4,194,304 / 6,738,415,616 = 0.062% on Llama-2-7B), bf16 + gradient checkpointing, and the ~8 GB 8-bit memory table
- Match configs to tasks — instruction tuning (r=8, q+v), domain adaptation (r=16, all-linear), style transfer (r=4) — then `merge_and_unload()` for a zero-overhead deployment model

---

## Abstract
LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning method that freezes pre-trained weights and injects trainable rank decomposition matrices. It enables fine-tuning large models with minimal GPU memory.

## The LoRA Hypothesis

### Key Insight
```text
Hypothesis: During fine-tuning, weight changes have low intrinsic rank

Standard fine-tuning:
  W' = W + ΔW
  ΔW ∈ ℝ^(d×k), full rank d × k matrix

LoRA fine-tuning:
  W' = W + A × B^T
  A ∈ ℝ^(d×r), B ∈ ℝ^(k×r), where r << min(d, k)

If r=8, d=4096, k=4096:
  Standard: 4096 × 4096 = 16,777,216 parameters
  LoRA: 4096 × 8 + 8 × 4096 = 65,536 parameters
  Reduction: 256x fewer parameters!
```

### Mathematical Foundation
```yaml
Given weight matrix W ∈ ℝ^(d×k):
  Forward: h = Wx

LoRA modification:
  Forward: h = Wx + AB^T x
            = Wx + ΔW x

  Where: ΔW = AB^T is rank r approximation

Training:
  - Freeze W (no gradients)
  - Train A and B (small matrices)

Inference:
  - Can merge: W' = W + AB^T
  - No runtime overhead!
```

## LoRA Implementation

### Basic LoRA Layer
```python
import math

import torch
import torch.nn as nn
import torch.nn.functional as F

class LoRALinear(nn.Module):
    """
    LoRA-enhanced linear layer
    """
    def __init__(self, in_features, out_features, rank=8, alpha=16, dropout=0.1, bias=False):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha
        self.merged = False

        # Frozen base weights
        self.weight = nn.Parameter(torch.randn(out_features, in_features))
        self.weight.requires_grad = False
        self.bias = nn.Parameter(torch.zeros(out_features)) if bias else None

        # Trainable LoRA matrices — A projects down (in -> r), B up (r -> out)
        self.lora_A = nn.Parameter(torch.randn(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))

        # Scaling
        self.scaling = alpha / rank

        # Optional dropout — applied on the INPUT of the LoRA path
        # (the PEFT/HF convention), not on its output
        self.dropout = nn.Dropout(dropout) if dropout > 0 else None

        # Paper init: kaiming-uniform A, zeros B — ΔW = B@A = 0, so the
        # adapter starts as an exact identity
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

    def forward(self, x):
        # Base computation (frozen)
        base_output = F.linear(x, self.weight, self.bias)

        # Merged: the delta already lives in self.weight — adding the
        # LoRA path again would count ΔW TWICE
        if self.merged:
            return base_output

        # LoRA computation
        lora_in = self.dropout(x) if self.dropout is not None else x
        lora_output = F.linear(
            F.linear(lora_in, self.lora_A),  # (B, in) @ (in, r) = (B, r)
            self.lora_B  # (B, r) @ (r, out) = (B, out)
        ) * self.scaling

        # Combine
        return base_output + lora_output

    def merge_weights(self):
        """
        Merge LoRA weights into base weights — zero LoRA overhead after
        this, but the forward must skip the LoRA path (merged flag).
        """
        if self.merged:
            return
        delta_w = (self.lora_B @ self.lora_A) * self.scaling
        self.weight.data += delta_w
        self.merged = True
        # Without the flag (and with requires_grad toggles alone) the
        # forward would emit Wx + 2·ΔWx — silently wrong outputs
```

### Applying LoRA to a Model
```python
def apply_lora_to_model(model, target_modules, rank=8, alpha=16):
    """
    Apply LoRA to specific linear layers in a model
    """
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear) and any(
            target in name for target in target_modules
        ):
            # Get dimensions
            in_features = module.in_features
            out_features = module.out_features

            # Create LoRA-enhanced module (carry the bias when the
            # source layer has one — Llama-style Linears are bias-free)
            lora_module = LoRALinear(
                in_features,
                out_features,
                rank=rank,
                alpha=alpha,
                bias=module.bias is not None,
            )

            # Copy weights
            lora_module.weight.data = module.weight.data.clone()
            if module.bias is not None:
                lora_module.bias = nn.Parameter(module.bias.data.clone())

            # Replace module
            parent_name = '.'.join(name.split('.')[:-1])
            child_name = name.split('.')[-1]
            parent = model.get_submodule(parent_name)
            setattr(parent, child_name, lora_module)

    return model

# Usage: Apply LoRA to attention layers
model = apply_lora_to_model(
    llama_model,
    target_modules=["q_proj", "v_proj"],  # Common choices
    rank=8,
    alpha=16
)
```

## Hyperparameter Selection

### Rank (r)
```text
Rank determines capacity of LoRA adaptation:

Low rank (2-4):
  - Minimal memory usage
  - Good for simple tasks
  - May underfit complex tasks

Medium rank (8-16):
  - Default for most tasks
  - Good balance of capacity and memory
  - Recommended starting point

High rank (32-64+):
  - Approaches full fine-tuning capacity
  - Better for complex domain adaptation
  - Diminishing returns beyond 64

Guideline: Start with r=8, increase if underfitting
```

### Alpha (α)
```text
Alpha controls the scaling of LoRA weights:

Scaling = α / r

Common choices:
  - α = r (scaling = 1.0)
  - α = 2r (scaling = 2.0)
  - α = 16 (fixed, regardless of r)

Guideline: Set α = 2r or α = 16 (fixed)

Example:
  r=8, α=16 → scaling = 2.0
  r=16, α=16 → scaling = 1.0
  r=32, α=16 → scaling = 0.5
```

### Target Modules
```python
# Common LoRA target configurations

# Config 1: Q and V only (most common)
target_modules = ["q_proj", "v_proj"]
# - Minimal parameters
# - Good for instruction tuning
# - 4,194,304 trainable (0.06%) at r=8 on Llama-2-7B

# Config 2: All attention projections
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
# - More capacity
# - Better for style transfer
# - 8,388,608 trainable (0.12%) at r=8

# Config 3: Attention + FFN
target_modules = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj"
]
# - Maximum LoRA coverage
# - Good for domain adaptation
# - ~20M trainable (0.30%) at r=8

# Config 4: All linear layers — the STRING form is load-bearing:
# peft matches target_modules == "all-linear" exactly; a list like
# ["all-linear"] never matches a module name and silently wraps
# NOTHING. It targets every nn.Linear EXCEPT the LM head, which on a
# Llama is exactly config 3 (0.30% at r=8)
target_modules = "all-linear"
```

## LoRA Variants

### Dropout on the LoRA Path
```python
# LoRALinear above already carries this: the dropout sits on the LoRA
# path's INPUT (the PEFT/HF convention — lora_dropout=0.1 in
# LoraConfig), never on its OUTPUT, where it would scramble the
# base + delta sum the layer returns. Typical values: 0.05-0.1 for
# instruction/domain tuning; 0.0 for style transfer, where
# deterministic adaptation helps.
```

### DoRA (Weight-Decomposed LoRA)
```python
class DoRALinear(nn.Module):
    """
    DoRA: decompose weights into per-output-channel magnitude and unit
    direction; LoRA perturbs the direction only.
    """
    def __init__(self, in_features, out_features, rank=8, alpha=16):
        super().__init__()
        # Base weight — frozen, exactly as in plain LoRA
        self.weight = nn.Parameter(torch.randn(out_features, in_features))
        self.weight.requires_grad = False

        # Magnitude (trainable), seeded with the base norms so the
        # layer starts as an exact identity together with zero-B
        self.magnitude = nn.Parameter(
            self.weight.norm(dim=-1, keepdim=True).detach()
        )

        # LoRA for direction
        self.lora_A = nn.Parameter(torch.randn(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))

        self.scaling = alpha / rank

    def forward(self, x):
        # The paper's update: W' = m ⊙ (W + ΔW) / ‖W + ΔW‖ — the
        # COMBINED weight is normalized. Normalizing W first and
        # adding ΔW afterward (a tempting shortcut) produces a
        # different, unnormalized direction and changes what the
        # magnitudes mean.
        delta_w = (self.lora_B @ self.lora_A) * self.scaling
        combined = self.weight + delta_w
        direction = F.normalize(combined, dim=-1)
        weight = self.magnitude * direction

        return F.linear(x, weight)

# In practice this is one flag: LoraConfig(..., use_dora=True) builds
# PEFT's DoraLinearLayer, which normalizes the combined weight per
# output channel exactly as sketched here.
```

### AdaLoRA (Adaptive Rank)
```python
class AdaLoRALayer(nn.Module):
    """
    AdaLoRA sketch: shift rank budget toward the layers that matter.

    A real implementation needs SVD-form updates, PIMO importance
    scoring, and scheduled rank trimming — the machinery lives in
    PEFT; this sketch only shows the budget interface.
    """
    def __init__(self, base_layer, max_rank=8):
        super().__init__()
        self.base_layer = base_layer
        self.max_rank = max_rank

        # Learnable importance scores
        self.importance = nn.Parameter(torch.ones(1))

        # Rank budget (shared across layers)
        self.rank_budget = max_rank

    def get_effective_rank(self):
        """Compute effective rank based on importance"""
        # Normalize importance across all AdaLoRA layers
        # (would be done at global level)
        return int(self.importance * self.rank_budget)

    def forward(self, x):
        effective_rank = self.get_effective_rank()
        # Use effective_rank for LoRA computation
        # ...

# The trainable version is a config swap — PEFT runs the trimming
# schedule itself (budget initialized at init_r, frozen until tinit,
# pruned toward r by tfinal, stepped every deltaT):
from peft import AdaLoraConfig

adalora_config = AdaLoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,            # Final rank
    init_r=12,      # Starting rank budget
    tinit=200,      # Warmup steps (no trimming)
    tfinal=1000,    # Steps after which rank == r
    deltaT=10,      # Trim interval (steps)
    target_modules=["q_proj", "v_proj"],
)
model = get_peft_model(base_model, adalora_config)
```

## Training with LoRA

### Using PEFT Library
```python
from peft import LoraConfig, get_peft_model, TaskType

# Create LoRA config
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,                          # Rank
    lora_alpha=16,                # Alpha
    lora_dropout=0.1,             # Dropout
    target_modules=["q_proj", "v_proj"],  # Target layers
    inference_mode=False,
)

# Apply LoRA to model
model = get_peft_model(base_model, lora_config)

# Check trainable parameters
model.print_trainable_parameters()
# Output: trainable params: 4,194,304 || all params: 6,738,415,616
#         trainable%: 0.0622%

# Train normally (only LoRA parameters get gradients)
trainer.train()
```

### Memory-Efficient Training
```python
# LoRA + Gradient Checkpointing + Mixed Precision
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./lora-output",
    learning_rate=1e-4,
    per_device_train_batch_size=4,   # Small batch
    gradient_accumulation_steps=8,   # Effective batch = 32
    num_train_epochs=3,
    fp16=True,                       # Mixed precision
    gradient_checkpointing=True,     # Save activation memory
    optim="adamw_torch",
)

# Memory breakdown for Llama-2-7B:
# Base model (8-bit):    ~7.0 GB  (6.9B params × 1 byte)
# LoRA parameters:       ~0.02 GB
# Gradients:             ~0.02 GB
# Optimizer states:      ~0.03 GB
# Activations (frozen):  ~1 GB
# ────────────────────────────────
# Total:                 ~8.1 GB (fits an 11 GB-class GPU)
# Dropping the base to 4-bit — QLoRA, next lesson (5102) — removes
# ~3.5 GB and brings the whole setup to 5-6 GB.
```

### Merging LoRA Weights
```python
# After training, merge LoRA into base weights
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf", torch_dtype=torch.bfloat16
)

# Load LoRA adapter
model = PeftModel.from_pretrained(base_model, "./lora-checkpoint")

# Merge weights
merged_model = model.merge_and_unload()

# Save merged model
merged_model.save_pretrained("./merged-model")

# Now you can use it like a normal model!
# No runtime overhead
```

## LoRA for Specific Tasks

### Instruction Tuning
```python
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    task_type=TaskType.CAUSAL_LM,
)

# Dataset: Alpaca, Dolly, OpenOrca
# Output: Model that follows instructions
```

### Domain Adaptation
```python
lora_config = LoraConfig(
    r=16,  # Higher rank for domain shift
    lora_alpha=32,
    target_modules="all-linear",  # string form — see Target Modules
    lora_dropout=0.1,
    task_type=TaskType.CAUSAL_LM,
)

# Dataset: Domain-specific corpus (medical, legal, code)
# Output: Model specialized for domain
```

### Style Transfer
```python
lora_config = LoraConfig(
    r=4,  # Lower rank sufficient for style
    lora_alpha=8,
    target_modules=["o_proj", "down_proj"],  # Focus on output
    lora_dropout=0.0,  # No dropout for style
    task_type=TaskType.CAUSAL_LM,
)

# Dataset: Style-specific examples (Shakespeare, formal, etc.)
# Output: Model with different writing style
```


---

## References

### Related PROJECT-OMEGA Documents

- [5102: QLoRA Pipelines - 4-bit Fine-Tuning on Consumer Hardware](5102-QLoRA-Pipelines.md)
- [5103: Adapters & Parameter-Efficient Adaptation Methods](5103-Adapters.md)

---

## Next Steps

- Continue with: **[5102: QLoRA Pipelines](./5102-QLoRA-Pipelines.md)**
- DPO training on merged models: **[5201: DPO Theory](../5200-alignment/5201-DPO-Theory.md)**
- QLoRA's memory trick, double quantization: **[4103: Double Quantization](../../phase4-quantization/4100-low-bit/4103-Double-Quantization.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_5101: LoRA](../../../../experiments/EXP_5101_LORA.md)**
