---
Document ID: 5101
Title: LoRA (Low-Rank Adaptation) Logic
Phase: 5
Module: 5100
Last Updated: 2026-09-24
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

- Explain The LoRA Hypothesis
- Configure and operate LoRA Implementation
- Explain Hyperparameter Selection
- Explain LoRA Variants
- Explain Training with LoRA
- Explain LoRA for Specific Tasks

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
import torch
import torch.nn as nn

class LoRALinear(nn.Module):
    """
    LoRA-enhanced linear layer
    """
    def __init__(self, in_features, out_features, rank=8, alpha=16, dropout=0.1):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha

        # Frozen base weights
        self.weight = nn.Parameter(torch.randn(out_features, in_features))
        self.weight.requires_grad = False

        # Trainable LoRA matrices
        self.lora_A = nn.Parameter(torch.randn(rank, in_features))
        self.lora_B = nn.Parameter(torch.randn(out_features, rank))

        # Scaling
        self.scaling = alpha / rank

        # Optional dropout
        self.dropout = nn.Dropout(dropout) if dropout > 0 else None

        # Initialize
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

    def forward(self, x):
        # Base computation (frozen)
        base_output = F.linear(x, self.weight)

        # LoRA computation
        lora_output = F.linear(
            F.linear(x, self.lora_A),  # (B, in) @ (in, r) = (B, r)
            self.lora_B  # (B, r) @ (r, out) = (B, out)
        ) * self.scaling

        # Optional dropout
        if self.dropout is not None:
            lora_output = self.dropout(lora_output)

        # Combine
        return base_output + lora_output

    def merge_weights(self):
        """
        Merge LoRA weights into base weights
        Call before saving for faster inference
        """
        delta_w = (self.lora_B @ self.lora_A) * self.scaling
        self.weight.data += delta_w
        # Disable LoRA
        self.lora_A.requires_grad = False
        self.lora_B.requires_grad = False
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

            # Create LoRA-enhanced module
            lora_module = LoRALinear(
                in_features,
                out_features,
                rank=rank,
                alpha=alpha
            )

            # Copy weights
            lora_module.weight.data = module.weight.data.clone()

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
```yaml
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
# - ~0.2% of total parameters for r=8

# Config 2: All attention projections
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
# - More capacity
# - Better for style transfer
# - ~0.4% of total parameters for r=8

# Config 3: Attention + FFN
target_modules = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj"
]
# - Maximum LoRA coverage
# - Good for domain adaptation
# - ~0.8% of total parameters for r=8

# Config 4: All linear layers
target_modules = ["all-linear"]  # PEFT syntax
# - Full model LoRA
# - ~1.5% of total parameters for r=8
```

## LoRA Variants

### LoRA with Dropout
```python
class LoRALinearWithDropout(nn.Module):
    """
    Add dropout to LoRA path for regularization
    """
    def __init__(self, in_features, out_features, rank=8, alpha=16, dropout=0.1):
        super().__init__()
        self.weight = nn.Parameter(torch.randn(out_features, in_features))
        self.weight.requires_grad = False

        self.lora_A = nn.Parameter(torch.randn(rank, in_features))
        self.lora_B = nn.Parameter(torch.randn(out_features, rank))

        self.scaling = alpha / rank
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        base = F.linear(x, self.weight)
        lora = self.dropout(F.linear(F.linear(x, self.lora_A), self.lora_B))
        return base + lora * self.scaling
```

### DoRA (Weight-Decomposed LoRA)
```python
class DoRALinear(nn.Module):
    """
    DoRA: Decompose weights into magnitude and direction
    Apply LoRA to direction only
    """
    def __init__(self, in_features, out_features, rank=8, alpha=16):
        super().__init__()
        # Base weight
        self.weight = nn.Parameter(torch.randn(out_features, in_features))

        # Magnitude vector (trainable)
        self.magnitude = nn.Parameter(torch.ones(out_features, 1))

        # LoRA for direction
        self.lora_A = nn.Parameter(torch.randn(rank, in_features))
        self.lora_B = nn.Parameter(torch.randn(out_features, rank))

        self.scaling = alpha / rank

    def forward(self, x):
        # Normalize base weight to unit direction
        direction = F.normalize(self.weight, dim=-1)

        # Add LoRA to direction
        lora_delta = (self.lora_B @ self.lora_A) * self.scaling
        direction = direction + lora_delta

        # Apply magnitude
        weight = direction * self.magnitude

        return F.linear(x, weight)
```

### AdaLoRA (Adaptive Rank)
```python
class AdaLoRALayer(nn.Module):
    """
    AdaLoRA: Adaptively allocate rank across layers
    Important layers get higher rank
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
# Base model (8-bit):    ~3.5 GB
# LoRA parameters:       ~0.02 GB
# Gradients:             ~0.02 GB
# Optimizer states:      ~0.06 GB
# Activations (frozen):  ~1 GB
# ────────────────────────────────
# Total:                 ~4.6 GB (fits on an 11GB-class GPU!)
```

### Merging LoRA Weights
```python
# After training, merge LoRA into base weights
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")

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
    target_modules=["all-linear"],
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

### Related ai-engineering-curriculum Documents

- [5102: QLoRA Pipelines - 4-bit Fine-Tuning on Consumer Hardware](5102-QLoRA-Pipelines.md)
- [5103: Adapters & Parameter-Efficient Adaptation Methods](5103-Adapters.md)

---

## Next Steps

- Continue with: **[5102: Next Document](./5102-QLoRA-Pipelines.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [5102: QLoRA Pipelines](./5102-QLoRA-Pipelines.md)
- [5201: DPO Theory](../5200-alignment/5201-DPO-Theory.md)
- [4103: Double Quantization](../../phase4-quantization/4100-low-bit/4103-Double-Quantization.md)

**Experiment Template:** [EXP_5101: LoRA](../../../../experiments/EXP_5101_LORA.md)
