---
Document ID: 5102
Title: "5102: QLoRA Pipelines - 4-bit Fine-Tuning on Consumer Hardware"
Phase: 5
Module: 5100
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'peft', 'lora', 'qlora', 'adaptation']
---

# 5102: QLoRA Pipelines - 4-bit Fine-Tuning on Consumer Hardware

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [QLoRA Architecture](#qlora-architecture)
- [QLoRA Implementation](#qlora-implementation)
- [QLoRA Hyperparameters](#qlora-hyperparameters)
- [QLoRA Training Pipeline](#qlora-training-pipeline)
- [Memory Optimization](#memory-optimization)
- [QLoRA Troubleshooting](#qlora-troubleshooting)
- [Merging QLoRA Weights](#merging-qlora-weights)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Quantify the three QLoRA innovations — NF4 (4-bit NormalFloat tuned for the normal weight distribution), double quantization (0.37 bits/param: ~3 GB per 65B, ~0.3 per 7B), and paged optimizers (CUDA unified memory) — behind the headline: a 65B fine-tunes on one 48 GB GPU, a 7B in ~5.6 GB
- Run the PEFT + bitsandbytes pipeline — `BitsAndBytesConfig(load_in_4bit, nf4, bf16 compute, double quant)` → `prepare_model_for_kbit_training` → `LoraConfig` → `get_peft_model` (r=16, all attention: 16,777,216 trainable = 0.249%)
- Pick hyperparameters from the tables — the rank ladder (r=8-16 consumer default vs the paper's r=64-on-all-linear Guanaco), α = 2r, target modules at their real r=16 budgets (0.12 / 0.25 / 0.59%), and lr 2e-4 with cosine + 3% warmup
- Wire paged optimizers through `TrainingArguments` — `optim="paged_adamw_32bit"`; the `Paged*` classes are paged by construction, and subclassing torch's AdamW buys nothing
- Cut memory further — gradient checkpointing (~50% of activations for ~20% time), CPU offload via `device_map`/`max_memory`, 8-bit optimizer state (`paged_adamw_8bit`)
- Diagnose the failure modes — NaN loss → halve lr, OOM → smaller batch + accumulation + checkpointing, slow convergence → raise rank — then merge on the 16-bit base and re-quantize for inference

---

## Abstract
QLoRA (Quantized LoRA) enables fine-tuning a 65B parameter model on a single 48GB GPU (the paper's headline claim) by combining 4-bit quantization with LoRA. On an 11GB VRAM GPU, QLoRA makes fine-tuning 7B models practical.

## QLoRA Architecture

### Key Innovations
```text
1. 4-bit NormalFloat (NF4) quantization
   - Optimized for normally distributed weights
   - Better than uniform quantization

2. Double Quantization
   - Quantize the quantization constants themselves
   - Saves 0.37 bits/param: ~3 GB per 65B (~0.3 GB per 7B)

3. Paged Optimizers
   - Page optimizer states through CPU RAM (CUDA unified memory)
   - Migrate to GPU only when needed

Result (paper): Fine-tune 65B on a single 48GB GPU
                Fine-tune 7B comfortably on 8GB
```

### QLoRA vs LoRA
```text
Standard LoRA (7B model, r=8 q+v adapters):
  Base model (fp16):  14 GB
  LoRA params:        0.02 GB
  Gradients:          0.02 GB
  Optimizer states:   0.03 GB
  Activations:        2 GB
  ─────────────────────────────
  Total:              ~16.1 GB (needs a 24GB-class GPU)

QLoRA (7B model, same adapters):
  Base model (NF4):   3.5 GB
  LoRA params:        0.02 GB
  Gradients:          0.02 GB
  Optimizer states:   0.03 GB (paged)
  Activations:        2 GB
  ─────────────────────────────
  Total:              ~5.6 GB ✓ (fits 8GB-class)
```

## QLoRA Implementation

### Using PEFT + bitsandbytes
```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 1. Configure 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",              # NF4 quantization
    bnb_4bit_compute_dtype=torch.bfloat16,  # Computation dtype
    bnb_4bit_use_double_quant=True,         # Double quantization
)

# 2. Load model in 4-bit
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",
)

# 3. Prepare for k-bit training
model = prepare_model_for_kbit_training(model)

# 4. Configure LoRA
lora_config = LoraConfig(
    r=8,                    # Rank
    lora_alpha=32,          # Alpha (higher for QLoRA)
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# 5. Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Output (r=16, all four attention projections, Llama-2-7B):
# trainable params: 16,777,216 || all params: 6,738,415,616 || trainable%: 0.2491
```

### Paged Optimizer
```python
from transformers import TrainingArguments

# Paged optimizers are a TrainingArguments string — no custom class.
# Subclassing torch.optim.AdamW buys nothing: the paging lives in
# bitsandbytes' own Optimizer2State (CUDA unified memory; state tensors
# above 100k elements migrate CPU<->GPU page by page).
#
# Direct form, if you need it: bnb.optim.PagedAdamW32bit(params, lr=...)
# — the Paged* classes are paged BY CONSTRUCTION (is_paged defines
# them; it is not an option you switch on).

training_args = TrainingArguments(
    output_dir="./qlora-output",
    optim="paged_adamw_32bit",  # Paged optimizer
    learning_rate=2e-4,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    bf16=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
)

trainer.train()
```

## QLoRA Hyperparameters

### Rank Selection for QLoRA
```python
# QLoRA typically requires higher rank than standard LoRA
# Reason: 4-bit base has less capacity

rank_guide = {
    "simple_task": {
        "r": 8,
        "alpha": 16,
        "description": "Instruction following, QA"
    },
    "domain_adaptation": {
        "r": 16,
        "alpha": 32,
        "description": "Medical, legal, code"
    },
    "full_language": {
        "r": 32,
        "alpha": 64,
        "description": "New language, significant shift"
    },
}

# Recommendation: Start with r=16, alpha=32 for QLoRA.
# (The paper's Guanaco headline runs go much bigger: r=64 on ALL
# linear layers. On consumer GPUs, r=8-16 on attention is the
# practical starting point — scale up only if underfitting.)
```

### Target Modules
```python
# QLoRA benefits from more extensive LoRA
# (trainable counts at r=16 on Llama-2-7B, 6,738,415,616 total)

qlora_configs = {
    "minimal": {
        "target_modules": ["q_proj", "v_proj"],
        "trainable": "8,388,608 (0.12%)",
        "use_case": "Simple instruction tuning"
    },
    "standard": {
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "trainable": "16,777,216 (0.25%)",
        "use_case": "Recommended default"
    },
    "full": {
        "target_modules": "all-linear",  # string form — ["all-linear"]
                                         # silently wraps nothing
        "trainable": "~40M (0.59%)",
        "use_case": "Complex domain adaptation"
    },
}
```

### Learning Rate
```python
# QLoRA requires different learning rate than standard LoRA

lr_schedule = {
    "LoRA": {
        "lr": "1e-4",
        "reasoning": "Base model fp16, stable gradients"
    },
    "QLoRA": {
        "lr": "2e-4",
        "reasoning": "Base model 4-bit, needs stronger signal"
    },
}

# Recommended: 2e-4 to 5e-4 for QLoRA
# Lower than 1e-4: Underfitting
# Higher than 5e-4: Instability

training_args = TrainingArguments(
    output_dir="./output",
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,  # 3% warmup
    num_train_epochs=3,
)
```

## QLoRA Training Pipeline

### Complete Training Script
```python
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

# 1. Load dataset
dataset = load_dataset("tatsu-lab/alpaca", split="train")

# 2. Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
tokenizer.pad_token = tokenizer.eos_token

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=512,
        padding="max_length",
    )

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# 3. Load model with 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",
)

model = prepare_model_for_kbit_training(model)

# 4. Configure LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)

# 5. Training arguments
training_args = TrainingArguments(
    output_dir="./qlora-checkpoints",
    learning_rate=2e-4,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    bf16=True,  # matches bnb_4bit_compute_dtype=torch.bfloat16 —
                # wrapping bf16 compute in fp16 AMP + grad scaler
                # is a contradiction
    optim="paged_adamw_32bit",
    logging_steps=10,
    save_steps=100,
    eval_steps=100,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    gradient_checkpointing=True,
)

# 6. Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,
)

# 7. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

# 8. Train
trainer.train()

# 9. Save LoRA adapter
model.save_pretrained("./qlora-adapter")
```

## Memory Optimization

### Gradient Checkpointing
```python
# Enable gradient checkpointing
model.gradient_checkpointing_enable()

# This:
# - Saves ~50% activation memory
# - Costs ~20% compute time
# - Worth it for limited VRAM

# In PEFT:
model = prepare_model_for_kbit_training(
    model,
    use_gradient_checkpointing=True
)
```

### CPU Offloading
```python
# Offload some layers to CPU

from accelerate import infer_auto_device_map, dispatch_model

# Device map with CPU offload
device_map = {
    "model.layers.0": "cpu",
    "model.layers.1": "cpu",
    "model.layers.2": 0,  # GPU
    "model.layers.3": 0,
    # ... etc
}

# Or automatic
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",
    max_memory={0: "10GB", "cpu": "32GB"},  # GPU + CPU
)
```

### 8-bit Optimizer States
```python
# Use 8-bit optimizer (bitsandbytes)

import bitsandbytes as bnb

optimizer = bnb.optim.PagedAdamW32bit(
    model.parameters(),
    lr=2e-4,
)
# PagedAdamW32bit is paged by construction — there is no is_paged
# flag to set. In practice TrainingArguments(optim="paged_adamw_8bit")
# wires this for you; the 8-bit state halves optimizer memory vs the
# 32-bit variant.

# Or via TrainingArguments
training_args = TrainingArguments(
    optim="paged_adamw_8bit",  # 8-bit optimizer
    # ... other args
)
```

## QLoRA Troubleshooting

### Common Issues
```python
# Issue 1: NaN loss
# Solution: Reduce learning rate, check data quality

training_args = TrainingArguments(
    learning_rate=1e-4,  # Reduce from 2e-4
    # ...
)

# Issue 2: Out of memory
# Solution: Reduce batch size, enable gradient checkpointing

training_args = TrainingArguments(
    per_device_train_batch_size=2,  # Reduce from 4
    gradient_accumulation_steps=8,  # Increase to maintain effective batch
    gradient_checkpointing=True,
    # ...
)

# Issue 3: Slow convergence
# Solution: Increase rank or alpha

lora_config = LoraConfig(
    r=32,           # Increase from 16
    lora_alpha=64,  # Increase from 32
    # ...
)
```

### Monitoring QLoRA Training
```python
from transformers import TrainerCallback

class QLoRAMonitorCallback(TrainerCallback):
    """
    Monitor QLoRA-specific metrics
    """
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            # GPU memory
            if torch.cuda.is_available():
                gpu_mem = torch.cuda.memory_allocated() / 1024**3
                logs["gpu_memory_gb"] = gpu_mem

            # Learning rate
            logs["learning_rate"] = state.log_history[-1].get("learning_rate", 0)

# Add to trainer
trainer.add_callback(QLoRAMonitorCallback())
```

## Merging QLoRA Weights

### Full Model Merge
```python
from peft import PeftModel
import torch

# 1. Load base model (16-bit for merge)
base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    torch_dtype=torch.float16,
    device_map="auto",
)

# 2. Load QLoRA adapter
model = PeftModel.from_pretrained(
    base_model,
    "./qlora-adapter",
)

# 3. Merge and unload — merging happens HERE on the 16-bit base:
# merge_and_unload on a 4-bit bnb-quantized model isn't supported,
# and the adapter was trained against dequantized weights anyway
merged_model = model.merge_and_unload()

# 4. Save the merged 16-bit model
merged_model.save_pretrained("./merged-model")

# 5. (optional) Re-quantize to 4-bit for inference
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
)

# Reload in 4-bit for inference
quantized_merged = AutoModelForCausalLM.from_pretrained(
    "./merged-model",
    quantization_config=bnb_config,
    device_map="auto",
)
```


---

## References

### Related PROJECT-OMEGA Documents

- [5101: LoRA (Low-Rank Adaptation) Logic](5101-LoRA-Logic.md)
- [5103: Adapters & Parameter-Efficient Adaptation Methods](5103-Adapters.md)

---

## Next Steps

- Continue with: **[5201: DPO Theory](./../5200-alignment/5201-DPO-Theory.md)**
- Double quantization deep-dive: **[4103: Double Quantization](../../phase4-quantization/4100-low-bit/4103-Double-Quantization.md)**
- DPO training on QLoRA adapters: **[5202: Alignment Orchestration](../5200-alignment/5202-Alignment-Orchestration.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_5102: QLoRA](../../../../experiments/EXP_5102_QLORA.md)**
