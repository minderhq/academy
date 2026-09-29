---
Document ID: 5104
Title: "5104: LoRA Implementation Guide"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
---

# 5104: LoRA Implementation Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [LoRA Architecture](#lora-architecture)
- [Implementation 1: LoRA from Scratch](#implementation-1-lora-from-scratch)
- [Implementation 2: LoRA with transformers](#implementation-2-lora-with-transformers)
- [Implementation 3: QLoRA (4-bit LoRA)](#implementation-3-qlora-4-bit-lora)
- [Implementation 4: Multi-Adapter LoRA](#implementation-4-multi-adapter-lora)
- [Performance Benchmarks](#performance-benchmarks)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Quick Start](#quick-start)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Quantify the LoRA architecture — ΔW = BA at rank r ≪ d: at r=8 a 4096×4096 projection carries 65,536 trainable params vs 16,777,216 (256×), with kaiming-A / zero-B init making the adapter start as an exact identity
- Build `LoRALinear` from scratch — frozen base, A projects down (in→r), B up (r→out), scaling α/r, dropout on the LoRA path's input — and merge it with a `merged` flag, because folding ΔW into W and then re-running the LoRA path emits Wx + 2·ΔWx
- Fine-tune through PEFT/transformers — `LoraConfig` (r=16, α=32, the 7 Mistral target modules ≈ 42M trainable) + `Trainer` with `bf16=True`; the bf16 7B base needs ~15 GB, so 11GB-class GPUs jump to QLoRA
- Wire the QLoRA variant — `BitsAndBytesConfig` (NF4 + double quant + bf16 compute) → `prepare_model_for_kbit_training` → `get_peft_model`; attention-only r=16 on Mistral-7B is 13,631,488 trainable and the whole setup fits in ~7 GB
- Serve N tasks from ONE model — `PeftModel.from_pretrained(..., adapter_name=)` + `load_adapter(adapter_name=)` + `set_adapter()`; re-wrapping the same base N times shares one module tree and each load overwrites the previous adapter's weights
- Read the benchmark tables — VRAM vs rank vs target-module scope (all-linear ~42M ≈ 0.6% vs attention-only 13.6M ≈ 0.2% at r=16) and pick the configuration that fits the GPU before training

---

## Abstract
Complete implementation guide for LoRA (Low-Rank Adaptation) fine-tuning — from a from-scratch `LoRALinear` through PEFT/QLoRA pipelines to multi-adapter serving, benchmarked for an 11GB-class GPU.

## LoRA Architecture

### Understanding LoRA

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        STANDARD LINEAR LAYER                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│    Input (x) ──► [W (d×d)] ──► Output (h = Wx)                          │
│                                                                           │
│    Parameters: d² (for d×d weight matrix)                                │
│    Example: 4096×4096 = 16,777,216 parameters                            │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           LoRA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│    Input (x) ──┬──► [W (frozen)] ──┬──► Output (h = Wx + BAx)           │
│               │                    │                                    │
│               └──► [B (d×r)] ──► [A (r×d)] ─┘                            │
│                                                                           │
│    Parameters:                                                             │
│    - W: d² (frozen, pre-trained)                                         │
│    - B: d×r (trainable)                                                  │
│    - A: r×d (trainable)                                                  │
│    Total trainable: 2×d×r                                                │
│                                                                           │
│    Example (r=8):                                                         │
│    - Trainable: 2×4096×8 = 65,536 parameters                             │
│    - Reduction: 256x fewer parameters!                                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Mathematical Foundation

**Standard Linear Layer:**
```text
h = Wx
where W ∈ R^(d×d)
```

**LoRA Layer:**
```text
h = Wx + ΔWx = Wx + BAx
where:
  - W ∈ R^(d×d) (frozen pre-trained weights)
  - B ∈ R^(d×r) (trainable adapter)
  - A ∈ R^(r×d) (trainable adapter)
  - r << d (rank, typically 4-64)
```

**Initialization:**
- A ~ N(0, σ²) (random normal)
- B = 0 (zero initialization)
- This ensures ΔW = BA starts at zero, preserving pre-trained behavior

## Implementation 1: LoRA from Scratch

### Basic LoRA Module

```python
# lora.py
import torch
import torch.nn as nn
import math

class LoRALinear(nn.Module):
    """
    LoRA linear layer

    Replaces standard linear layer with low-rank adaptation
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        rank: int = 8,
        alpha: float = 16.0,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        self.merged = False

        # Freeze original weights
        self.weight = nn.Parameter(torch.randn(out_features, in_features))
        self.weight.requires_grad = False

        # Trainable LoRA parameters
        self.lora_A = nn.Parameter(torch.randn(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))

        # Optional dropout
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        # Initialize
        self._init_weights()

    def _init_weights(self):
        """Initialize weights"""
        # Original weights (would normally load pre-trained)
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))

        # LoRA A: random initialization
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

        # LoRA B: zero initialization
        nn.init.zeros_(self.lora_B)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # Merged: ΔW already lives in self.weight — running the LoRA
        # path again would apply it twice (Wx + 2·ΔWx, silently wrong)
        if self.merged:
            return nn.functional.linear(x, self.weight)

        # Original frozen weights
        output = nn.functional.linear(x, self.weight)

        # LoRA adaptation: F.linear transposes its weight argument, so
        # x @ A.T -> (…, r), then @ B.T -> (…, out_features)
        lora_output = nn.functional.linear(
            nn.functional.linear(
                self.dropout(x),
                self.lora_A,
            ),
            self.lora_B,
        )

        return output + lora_output * self.scaling

    def merge(self):
        """Merge LoRA weights into the frozen base — zero adapter
        overhead afterwards. The merged flag makes forward() skip the
        LoRA path; without it the folded ΔW would be applied twice."""
        if self.merged:
            return
        delta_w = (self.lora_B @ self.lora_A) * self.scaling
        self.weight.data += delta_w
        self.merged = True


class LoRAAttention(nn.Module):
    """
    LoRA-adapted multi-head attention
    """

    def __init__(
        self,
        hidden_size: int,
        num_heads: int,
        rank: int = 8,
        alpha: float = 16.0,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads

        # Q, K, V projections with LoRA
        self.q_proj = LoRALinear(hidden_size, hidden_size, rank, alpha)
        self.k_proj = LoRALinear(hidden_size, hidden_size, rank, alpha)
        self.v_proj = LoRALinear(hidden_size, hidden_size, rank, alpha)

        # Output projection with LoRA
        self.out_proj = LoRALinear(hidden_size, hidden_size, rank, alpha)

    def forward(
        self,
        x: torch.Tensor,
        attention_mask: torch.Tensor = None,
    ) -> torch.Tensor:
        """Forward pass"""

        batch_size, seq_len, hidden_size = x.shape

        # Project to Q, K, V
        Q = self.q_proj(x)
        K = self.k_proj(x)
        V = self.v_proj(x)

        # Reshape for multi-head
        Q = Q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)

        if attention_mask is not None:
            scores = scores + attention_mask

        attn_weights = torch.softmax(scores, dim=-1)
        attn_output = torch.matmul(attn_weights, V)

        # Reshape back
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, hidden_size)

        # Output projection
        output = self.out_proj(attn_output)

        return output


# Test LoRA
def test_lora():
    """Test LoRA implementation"""

    print("Testing LoRA Implementation")
    print("="*60)

    # Create LoRA layer
    lora_layer = LoRALinear(
        in_features=768,
        out_features=768,
        rank=8,
        alpha=16.0
    )

    # Count parameters
    total_params = sum(p.numel() for p in lora_layer.parameters())
    trainable_params = sum(p.numel() for p in lora_layer.parameters() if p.requires_grad)

    print(f"\nLayer: LoRALinear(768, 768, rank=8)")
    print(f"Total parameters: {total_params:,} (frozen weight + adapters)")
    print(f"Trainable parameters: {trainable_params:,} (A + B only)")
    print(f"Trainable share: {trainable_params / total_params:.2%}")

    # Forward pass
    x = torch.randn(2, 10, 768)
    output = lora_layer(x)

    print(f"\nInput shape: {x.shape}")
    print(f"Output shape: {output.shape}")

    # Test merging
    lora_layer.merge()
    print("\nLoRA weights merged into original layer")


if __name__ == "__main__":
    test_lora()
```

## Implementation 2: LoRA with transformers

### Fine-tuning Mistral-7B with LoRA

```python
# lora_finetuning.py
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model
from datasets import load_dataset
import torch


def setup_lora_model(
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
    rank: int = 16,
    alpha: float = 32.0,
    dropout: float = 0.05,
):
    """
    Setup model with LoRA adapters

    Args:
        model_name: Pre-trained model name
        rank: LoRA rank (r)
        alpha: LoRA scaling factor (alpha)
        dropout: Dropout probability
    """

    print(f"Loading model: {model_name}")

    # Plain bf16 LoRA — no quantization (that's Implementation 3)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # A 7B bf16 base is ~14-15 GB by itself: this flow fits a
    # 24GB-class GPU. On the 11GB-class target, use Implementation 3
    # (QLoRA) — and only there prepare_model_for_kbit_training().

    # LoRA configuration
    lora_config = LoraConfig(
        r=rank,                    # Rank
        lora_alpha=alpha,          # Alpha scaling
        target_modules=[           # Modules to apply LoRA
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model, tokenizer, lora_config


def train_lora(
    data_path: str,
    output_dir: str = "./lora-output",
    num_epochs: int = 3,
    batch_size: int = 4,
    gradient_accumulation: int = 4,
    learning_rate: float = 2e-4,
    rank: int = 16,
):
    """
    Train model with LoRA
    """

    # Setup model
    model, tokenizer, lora_config = setup_lora_model(rank=rank)

    # Load dataset
    print(f"\nLoading dataset from: {data_path}")
    dataset = load_dataset("json", data_files=data_path, split="train")

    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=512,
            padding="max_length",
        )

    tokenized_dataset = dataset.map(tokenize_function, batched=True)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation,
        learning_rate=learning_rate,
        bf16=True,  # matches the bf16 base — fp16 AMP + grad scaler on
                    # bf16 weights is a contradiction
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        report_to="none",
        # No eval_steps/load_best_model_at_end: the Trainer below has
        # no eval_dataset, so there is nothing to select a best
        # checkpoint from
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )

    # Train
    print("\nStarting training...")
    trainer.train()

    # Save — model.save_pretrained writes the adapter weights AND
    # adapter_config.json; saving lora_config again would duplicate it
    print(f"\nSaving model to: {output_dir}")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    return model, tokenizer


# Example usage
def example_training():
    """Example training script"""

    # Create sample dataset
    import json

    sample_data = [
        {"text": "PROJECT-OMEGA is an AI infrastructure project for homelab deployment."},
        {"text": "LoRA allows efficient fine-tuning by freezing original weights."},
        {"text": "11GB-class GPU has 11GB VRAM, suitable for 7B models with 4-bit quantization."},
    ]

    with open("sample_data.jsonl", "w") as f:
        for item in sample_data:
            f.write(json.dumps(item) + "\n")

    # Train
    model, tokenizer = train_lora(
        data_path="sample_data.jsonl",
        output_dir="./lora-mistral",
        num_epochs=1,
        rank=16,
    )

    print("\nTraining completed!")


if __name__ == "__main__":
    example_training()
```

## Implementation 3: QLoRA (4-bit LoRA)

```python
# qlora_training.py
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import torch


def setup_qlora_model(
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
    rank: int = 16,
):
    """
    Setup QLoRA (4-bit LoRA) for maximum memory efficiency
    """

    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Required for QLoRA: upcasts norms/lm_head and hooks input
    # grads — skipping it leaves the 4-bit base unstable to train
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        r=rank,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)

    # Print trainable parameters
    model.print_trainable_parameters()

    return model, tokenizer


# Memory analysis
def analyze_memory_usage():
    """Analyze memory usage for different configurations"""

    # Trainable counts, Mistral-7B (GQA: k/v project 4096 -> 1024):
    # attention-only r=16 = 13,631,488 / r=8 = 6,815,744; all-linear
    # r=16 = ~42M (~0.6% of the model). VRAM at batch 1, seq 512.
    configs = [
        {"name": "Full Fine-tuning (7B)", "vram": "60GB+", "trainable": "7B"},
        {"name": "LoRA bf16 (r=16, attention)", "vram": "~18GB", "trainable": "13.6M"},
        {"name": "QLoRA (r=16, attention)", "vram": "~7GB", "trainable": "13.6M"},
        {"name": "QLoRA (r=8, attention)", "vram": "~6GB", "trainable": "6.8M"},
    ]

    print("Memory Usage Comparison")
    print("="*60)
    print(f"{'Configuration':<30} {'VRAM':<10} {'Trainable':<15}")
    print("-"*60)

    for config in configs:
        print(f"{config['name']:<30} {config['vram']:<10} {config['trainable']:<15}")


if __name__ == "__main__":
    analyze_memory_usage()
```

## Implementation 4: Multi-Adapter LoRA

```python
# multi_adapter_lora.py
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class MultiAdapterModel:
    """
    Multi-adapter LoRA model for task-specific adapters.

    ONE PeftModel holds every adapter under its own name. The tempting
    alternative — PeftModel.from_pretrained(base, path) once per task —
    injects each new adapter into the SAME module tree under the same
    "default" name: N wrappers over one model, each load overwriting
    the previous adapter's weights.
    """

    def __init__(
        self,
        base_model_name: str,
        adapters: dict,
    ):
        """
        Args:
            base_model_name: Base model name
            adapters: Mapping of {task_name: adapter_path}
        """
        # Load base model
        self.base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )

        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)

        # First adapter wraps the base; the rest join the SAME
        # PeftModel via load_adapter
        task_names = list(adapters)
        self.model = PeftModel.from_pretrained(
            self.base_model,
            adapters[task_names[0]],
            adapter_name=task_names[0],
        )
        for task_name in task_names[1:]:
            self.model.load_adapter(adapters[task_name], adapter_name=task_name)

        self.current_adapter = task_names[0]
        self.model.set_adapter(self.current_adapter)

    def set_adapter(self, task_name: str):
        """Set active adapter"""
        if task_name not in self.model.peft_config:
            raise ValueError(
                f"Adapter {task_name} not found — loaded: {list(self.model.peft_config)}"
            )
        self.model.set_adapter(task_name)
        self.current_adapter = task_name

    def generate(self, prompt: str, max_new_tokens: int = 100) -> str:
        """Generate with the current adapter"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
            )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


# Usage example
def example_multi_adapter():
    """Example multi-adapter usage"""

    # Define adapters
    adapters = {
        "chat": "./adapters/lora-chat",
        "code": "./adapters/lora-code",
        "summary": "./adapters/lora-summary",
    }

    # Create model
    model = MultiAdapterModel(
        base_model_name="mistralai/Mistral-7B-Instruct-v0.2",
        adapters=adapters,
    )

    # Use different adapters
    model.set_adapter("chat")
    response = model.generate("Hello! How are you?")
    print(f"Chat: {response}")

    model.set_adapter("code")
    response = model.generate("Write a Python function:")
    print(f"Code: {response}")
```

## Performance Benchmarks

### 11GB-class GPU

| Model | Method | VRAM | Batch Size | Speed |
|-------|--------|------|------------|-------|
| Mistral-7B | Full fine-tuning | OOM | - | - |
| Mistral-7B | LoRA bf16 (r=16) | ~18GB | 1 | Won't fit — 24GB-class |
| Mistral-7B | QLoRA (r=16) | ~7GB | 2 | Fast |
| Mistral-7B | QLoRA (r=8) | ~6GB | 4 | Faster |
| Llama-2-13B | QLoRA (r=8) | ~10GB | 1 | Slow |

### LoRA Rank vs Performance

QLoRA, all-linear targets on Mistral-7B — trainable params scale
linearly with rank (≈ 2.62M per rank step: r × Σ(in+out) over the
targeted projections), so the VRAM ladder moves smoothly:

| Rank | Parameters | VRAM | Quality | Training Time |
|------|-----------|------|---------|---------------|
| 4 | 10.5M | ~5.5GB | Lower | Fast |
| 8 | 21M | ~6GB | Good | Medium |
| 16 | 42M | ~7GB | Better | Medium |
| 32 | 84M | ~8GB | Best | Slow |
| 64 | 168M | ~10GB | Diminishing returns | Slow |

## Best Practices

### 1. Target Module Selection

```python
# For attention-focused models
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

# For transformer models with MLP
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]

# For minimal adaptation
target_modules = ["q_proj", "v_proj"]
```

### 2. Rank Selection

```python
# Capacity ladder (see 5101) — start small, raise on underfitting
rank = 8   # Default: instruction tuning, style
rank = 16  # Domain adaptation
rank = 32  # Significant shift (new language, format)
# 64+ approaches full fine-tuning capacity; diminishing returns
```

### 3. Alpha Scaling

```python
# Typically alpha = 2 * rank
lora_alpha = 2 * rank  # Good starting point

# For more adaptation
lora_alpha = 4 * rank

# For less adaptation
lora_alpha = rank
```

### 4. Dropout

```python
# Standard dropout
lora_dropout = 0.05

# For regularization
lora_dropout = 0.1

# For small datasets
lora_dropout = 0.15
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```python
# Solutions:
# - Reduce batch size
per_device_train_batch_size = 2

# - Reduce rank
r = 8  # instead of 16

# - Enable gradient checkpointing
gradient_checkpointing = True

# - Use 4-bit (QLoRA)
load_in_4bit = True
```

#### 2. Slow Training

```python
# Solutions:
# - Increase batch size with gradient accumulation
gradient_accumulation_steps = 8

# - Use fused optimizer
optim = "adamw_bnb_8bit"

# - Reduce logging frequency
logging_steps = 50
```

#### 3. Poor Quality

```python
# Solutions:
# - Increase rank
r = 32  # instead of 16

# - Increase alpha
lora_alpha = 64  # instead of 32

# - Train longer
num_train_epochs = 5  # instead of 3

# - Add more target modules
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]
```

## Quick Start

```bash
# 1. Install dependencies
uv pip install transformers peft bitsandbytes accelerate datasets

# 2. Train — the script exposes functions, not a CLI; call them:
python -c "from lora_finetuning import train_lora; train_lora(data_path='data.jsonl', output_dir='./lora-output', rank=16)"

# 3. Merge and export — inline, no separate merge script:
python - <<'PY'
from peft import PeftModel
from transformers import AutoModelForCausalLM
import torch

base = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", torch_dtype=torch.bfloat16
)
PeftModel.from_pretrained(base, "./lora-output").merge_and_unload() \
    .save_pretrained("./merged-model")
PY
```

---

## Summary

This guide is LoRA end to end on an 11GB-class GPU: a from-scratch LoRALinear to expose the mechanics, then the production paths through PEFT and QLoRA, and finally multi-adapter serving where one base model hosts many trained adapters. The benchmarks section grounds the choice in measured memory and speed, best practices and troubleshooting keep the runs reproducible, and the quick start gets a working pipeline before the theory matters. The durable rule: LoRA is cheap to train precisely so you can afford to measure it properly - benchmark on your hardware, not the paper's.

## References

### Related PROJECT-OMEGA Documents

- [5101: LoRA (Low-Rank Adaptation) Logic](../5101-LoRA-Logic.md)
- [5102: QLoRA Pipelines - 4-bit Fine-Tuning on Consumer Hardware](../5102-QLoRA-Pipelines.md)
- [5103: Adapters & Parameter-Efficient Adaptation Methods](../5103-Adapters.md)
- [4101: GGUF Physics](../../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**
- Experiment: **[EXP_5101: LoRA](../../../../../experiments/EXP_5101_LORA.md)**
