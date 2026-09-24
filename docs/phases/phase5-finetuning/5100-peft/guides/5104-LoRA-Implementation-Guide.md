# 5104: LoRA Implementation Guide

## Abstract
Complete implementation guide for LoRA (Low-Rank Adaptation) fine-tuning on an 11GB VRAM GPU. From theory to production deployment.

## LoRA Architecture

### Understanding LoRA

```
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
```
h = Wx
where W ∈ R^(d×d)
```

**LoRA Layer:**
```
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
        merge_weights: bool = False,
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        self.merge_weights = merge_weights

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

        # Original frozen weights
        if self.merge_weights:
            # Merge LoRA weights into original (for inference)
            merged_weight = self.weight + (self.lora_B @ self.lora_A) * self.scaling
            output = nn.functional.linear(x, merged_weight)
        else:
            # Separate computation
            output = nn.functional.linear(x, self.weight)

            # LoRA adaptation: x @ A.T @ B.T
            lora_output = nn.functional.linear(
                self.dropout(x),
                self.lora_A.T  # (in_features, rank)
            )
            lora_output = nn.functional.linear(
                lora_output,
                self.lora_B.T  # (rank, out_features)
            )
            output = output + lora_output * self.scaling

        return output

    def merge(self):
        """Merge LoRA weights into original weights"""
        delta_w = (self.lora_B @ self.lora_A) * self.scaling
        self.weight.data += delta_w
        self.merge_weights = True


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
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print(f"Parameter reduction: {total_params / trainable_params:.1f}x")

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
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
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

    # Load model in 4-bit for efficiency
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        load_in_4bit=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)

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
        fp16=True,
        logging_steps=10,
        save_steps=100,
        eval_steps=100,
        save_total_limit=2,
        load_best_model_at_end=True,
        report_to="none",
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

    # Save
    print(f"\nSaving model to: {output_dir}")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save LoRA config
    lora_config.save_pretrained(output_dir)

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
from peft import LoraConfig, get_peft_model
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
        bnb_4bit_compute_dtype=torch.float16,
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

    configs = [
        {"name": "Full Fine-tuning (7B)", "vram": "28GB", "trainable": "7B"},
        {"name": "LoRA (r=16)", "vram": "16GB", "trainable": "40M"},
        {"name": "QLoRA (r=16)", "vram": "10GB", "trainable": "40M"},
        {"name": "QLoRA (r=8)", "vram": "8GB", "trainable": "20M"},
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
from peft import PeftModel, PeftConfig
import torch


class MultiAdapterModel:
    """
    Multi-adapter LoRA model for task-specific adapters
    """

    def __init__(
        self,
        base_model_name: str,
        adapters: dict,
    ):
        """
        Args:
            base_model_name: Base model name
            adapters: Dict of {task_name: adapter_path}
        """

        # Load base model
        self.base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
        )

        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)

        # Load adapters
        self.adapters = {}
        for task_name, adapter_path in adapters.items():
            print(f"Loading adapter for {task_name}: {adapter_path}")
            self.adapters[task_name] = PeftModel.from_pretrained(
                self.base_model,
                adapter_path,
            )

        self.current_adapter = None

    def set_adapter(self, task_name: str):
        """Set active adapter"""
        if task_name not in self.adapters:
            raise ValueError(f"Adapter {task_name} not found")
        self.current_adapter = task_name

    def generate(self, prompt: str, max_new_tokens: int = 100) -> str:
        """Generate with current adapter"""

        if self.current_adapter is None:
            model = self.base_model
        else:
            model = self.adapters[self.current_adapter]

        inputs = self.tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
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

### 11GB-class GPU (11GB VRAM)

| Model | Method | VRAM | Batch Size | Speed |
|-------|--------|------|------------|-------|
| Mistral-7B | Full fine-tuning | OOM | - | - |
| Mistral-7B | LoRA (r=16) | ~14GB | 1 | Slow |
| Mistral-7B | QLoRA (r=16) | ~8GB | 2 | Fast |
| Mistral-7B | QLoRA (r=8) | ~6GB | 4 | Faster |
| Llama-2-13B | QLoRA (r=8) | ~10GB | 1 | Slow |

### LoRA Rank vs Performance

| Rank | Parameters | VRAM | Quality | Training Time |
|------|-----------|------|---------|---------------|
| 4 | 10M | 6GB | Lower | Fast |
| 8 | 20M | 7GB | Good | Medium |
| 16 | 40M | 8GB | Better | Medium |
| 32 | 80M | 10GB | Best | Slow |
| 64 | 160M | OOM | - | - |

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
# Rule of thumb: rank = sqrt(d_model) / 2
d_model = 4096  # Mistral-7B
recommended_rank = int(math.sqrt(d_model) / 2)  # = 32

# For memory constraints
rank = 8   # Minimal
rank = 16  # Balanced
rank = 32  # Best quality
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
pip install transformers peft bitsandbytes accelerate datasets

# 2. Train with QLoRA
python lora_finetuning.py \
    --data_path data.jsonl \
    --output_dir ./lora-output \
    --rank 16 \
    --batch_size 4

# 3. Merge and export
python merge_lora.py \
    --base_model mistralai/Mistral-7B-Instruct-v0.2 \
    --lora_path ./lora-output \
    --output_dir ./merged-model
```


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [5101: LoRA Logic](../5101-LoRA-Logic.md)
- [5102: QLoRA Pipelines](../5102-QLoRA-Pipelines.md)
- [4101: GGUF Physics](../../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- [EXP_5101: LoRA](../../../../../experiments/EXP_5101_LORA.md)
