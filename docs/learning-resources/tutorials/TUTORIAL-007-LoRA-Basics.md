---
Document ID: TUTORIAL-007
Title: LoRA Basics
Category: Tutorial
Last Updated: 2026-02-05
Status: Review
Difficulty: Intermediate
Estimated Time: 1 hour
Prerequisites: TUTORIAL-001, 2200
Related: LAB-003, 5101
Tags: ['tutorial', 'lora', 'fine-tuning', 'peft']
---

# TUTORIAL-007: LoRA Basics

## Overview

LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning method that trains only a small number of parameters while keeping the original model frozen.

## Why LoRA?

Traditional fine-tuning of a 7B parameter model requires:
- **Storage:** ~14GB for full model weights
- **Memory:** ~24GB+ GPU memory for training
- **Time:** Hours to days

With LoRA:
- **Storage:** ~100MB for adapter weights
- **Memory:** ~12GB GPU memory
- **Time:** Minutes to hours

## How LoRA Works

### The Core Idea

Instead of updating the weight matrix `W` directly, LoRA adds two small matrices `A` and `B`:

```yaml
Original:  y = Wx + b
LoRA:      y = (W + BA)x + b

Where:
- W: Original weight matrix (d × d), frozen
- A: Low-rank matrix (d × r), trainable
- B: Low-rank matrix (r × d), trainable
- r: Rank (typically 8-64), r << d
```

### Matrix Multiplication Visualized

```text
Full Weight Update (Not LoRA):
┌─────────────────────────────┐
│  Original: W (4096 × 4096)  │  = 16,777,216 parameters
└─────────────────────────────┘

LoRA Update:
┌──────────┐   ┌──────────┐
│ A (4096×16) │ × │ B (16×4096) │  = 131,072 parameters (rank=16)
└──────────┘   └──────────┘

Reduction: 131,072 / 16,777,216 = 0.78% of original!
```

## Installation

```bash
# Install required packages
pip install transformers
pip install peft
pip install datasets
pip install bitsandbytes
pip install accelerate

# For GPU optimization
pip install triton
pip install xformers
```

## Basic LoRA Implementation

### 1. Minimal LoRA Example

```python
import torch
import torch.nn as nn

class LoRALinear(nn.Module):
    """Simple LoRA linear layer."""

    def __init__(self, in_features, out_features, rank=8):
        super().__init__()
        # Original frozen weights
        self.linear = nn.Linear(in_features, out_features, bias=False)
        self.linear.weight.requires_grad = False

        # LoRA trainable matrices
        self.lora_A = nn.Parameter(torch.randn(rank, in_features) * 0.01)
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))

        self.rank = rank
        self.scaling = 1.0 / rank

    def forward(self, x):
        # Original forward pass
        result = self.linear(x)

        # Add LoRA path: BA × x × scaling
        lora_result = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling

        return result + lora_result

# Usage
original_layer = nn.Linear(4096, 4096)
lora_layer = LoRALinear(4096, 4096, rank=16)

print(f"Original params: {original_layer.weight.numel():,}")
print(f"LoRA params: {lora_layer.lora_A.numel() + lora_layer.lora_B.numel():,}")
```

### 2. Using PEFT Library (Recommended)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

# Load base model
model_name = "meta-llama/Llama-2-7b-hf"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Configure LoRA
lora_config = LoraConfig(
    r=16,                    # Rank
    lora_alpha=32,           # Alpha scaling
    target_modules=["q_proj", "v_proj"],  # Apply to attention
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# Apply LoRA to model
model = get_peft_model(model, lora_config)

# Print trainable parameters
model.print_trainable_parameters()

# Output:
# trainable params: 8,388,608 || all params: 6,738,415,616 || trainable%: 0.1245
```

## Training with LoRA

### 1. Prepare Dataset

```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("databricks/databricks-dolly-15k")

# Format for instruction tuning
def format_prompt(sample):
    return {
        "text": f"### Instruction:\n{sample['instruction']}\n\n### Response:\n{sample['response']}"
    }

dataset = dataset.map(format_prompt)

# Split
train_data = dataset["train"].train_test_split(test_size=0.1)["train"]
eval_data = dataset["train"].train_test_split(test_size=0.1)["test"]
```

### 2. Training Loop

```python
import transformers
from trl import SFTTrainer

# Training arguments
training_args = transformers.TrainingArguments(
    output_dir="./lora-output",
    learning_rate=2e-4,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_steps=10,
    save_steps=100,
    fp16=True,
    bf16=False,
    max_grad_norm=0.3,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
)

# Create trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=train_data,
    dataset_text_field="text",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=training_args,
)

# Train
trainer.train()

# Save LoRA adapters only
trainer.save_model("./lora-adapters")
```

### 3. Inference with LoRA

```python
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    torch_dtype=torch.float16,
    device_map="auto"
)

# Load LoRA adapters
model = PeftModel.from_pretrained(
    base_model,
    "./lora-adapters"
)

# Generate
prompt = "### Instruction:\nExplain quantum computing\n\n### Response:\n"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.7,
        top_p=0.9
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

## Advanced LoRA Techniques

### 1. QLoRA (4-bit Quantization + LoRA)

Train large models on consumer GPUs:

```python
from transformers import BitsAndBytesConfig

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# Load model in 4-bit
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto"
)

# Apply LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# Now you can train a 7B model on a single RTX 3090!
```

### 2. Multi-Adapter LoRA

```python
# Create multiple task-specific adapters
from peft import PeftModel

# Base model
model = AutoModelForCausalLM.from_pretrained("base-model")

# Add adapters for different tasks
model = PeftModel.from_pretrained(
    model,
    "adapters/code",
    adapter_name="code"
)

model.load_adapter("adapters/chat", adapter_name="chat")
model.load_adapter("adapters/math", adapter_name="math")

# Switch between adapters
model.set_adapter("code")
output_code = model.generate("Write Python code...")

model.set_adapter("chat")
output_chat = model.generate("Hello! How are you?")

# Combine adapters
model.set_adapter(["code", "chat"])
output_combined = model.generate("...")
```

### 3. Target Specific Modules

```python
# Fine-grained control over which modules get LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    # Target specific modules
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj"
    ],
    # Or use regex patterns
    modules_to_save=["embed_tokens", "lm_head"],  # Also train these
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
```

## LoRA Hyperparameters

| Parameter | Description | Typical Values | Effect |
|-----------|-------------|----------------|--------|
| **r (rank)** | LoRA rank | 8, 16, 32, 64 | Higher = more capacity, more params |
| **alpha** | Scaling factor | 16, 32, 64 | Controls adapter strength |
| **dropout** | Dropout rate | 0.05, 0.1 | Prevents overfitting |
| **target_modules** | Which layers to adapt | q_proj, v_proj | More modules = more capacity |

### Choosing the Right Rank

```python
# Low rank (8-16): Simple tasks, small datasets
lora_config = LoraConfig(r=16, ...)

# Medium rank (32-64): Complex tasks, medium datasets
lora_config = LoraConfig(r=64, ...)

# High rank (128+): Very complex tasks, large datasets
lora_config = LoraConfig(r=128, ...)
```

## Best Practices

### 1. Start with QLoRA
```python
# Always use 4-bit quantization for >7B models
bnb_config = BitsAndBytesConfig(load_in_4bit=True)
```

### 2. Use Cosine Learning Rate Schedule
```python
training_args = transformers.TrainingArguments(
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    ...
)
```

### 3. Monitor Gradient Clipping
```python
training_args = transformers.TrainingArguments(
    max_grad_norm=0.3,  # Prevent exploding gradients
    ...
)
```

### 4. Save Only Adapters
```python
# Small file size (~100MB)
trainer.save_model("lora-adapters")

# Instead of full model (~14GB)
trainer.save_model("full-model")  # Don't do this!
```

## Common Issues and Solutions

### Issue 1: CUDA Out of Memory
```python
# Solution: Reduce batch size, use gradient accumulation
training_args = transformers.TrainingArguments(
    per_device_train_batch_size=1,  # Reduce
    gradient_accumulation_steps=8,   # Increase
    ...
)
```

### Issue 2: Slow Training
```python
# Solution: Use Flash Attention 2
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    use_flash_attention_2=True,
    ...
)
```

### Issue 3: Poor Results
```python
# Solution: Increase rank or add more target modules
lora_config = LoraConfig(
    r=64,  # Increase from 16
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # Add more
    ...
)
```

## Next Steps

After completing this tutorial:

1. **Practice:** Complete [LAB-003: LoRA Fine-Tuning](../labs/LAB-003-LoRA-FineTuning.md)
2. **Learn More:** [5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
3. **Advanced:** [5201: DPO Theory](../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)

---

**Tutorial Duration:** 1 hour
**Difficulty:** Intermediate
**Last Updated:** 2026-02-05
