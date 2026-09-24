# EXP_5102: QLoRA Pipelining Experiment

**Project:** PROJECT-OMEGA
**Phase:** [5100] PEFT
**Document ID:** 5102
**Experiment ID:** EXP_5102_QLORA
**Date:** 2026-02-04
**Status:** Completed

---

## Experiment Metadata

| Field | Value |
|-------|-------|
| **Title** | QLoRA Fine-tuning Pipeline |
| **Objective** | Test QLoRA fine-tuning on an 11GB VRAM GPU |
| **Hypothesis** | QLoRA enables fine-tuning 7B models on consumer GPUs |
| **Category** | Performance/Ablation |
| **Priority** | Critical |
| **Estimated Duration** | 8 hours |

---

## Infrastructure Used

```
GPU: 11GB VRAM GPU
Memory: 32GB RAM
Storage: NFS for model storage
```

---

## Variables

| Variable | Values | Level |
|----------|--------|-------|
| Model | Llama-2-7B, Mistral-7B | Categorical |
| LoRA Rank | 8, 16, 32, 64 | Categorical |
| Learning Rate | 1e-4, 2e-4, 5e-4 | Categorical |
| Batch Size | 4, 8, 16 | Categorical |

---

## Experimental Setup

```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, TrainingArguments
from trl import SFTTrainer

# QLoRA Configuration
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# Training arguments
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_total_limit=2,
)

# Load base model in 4-bit
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    load_in_4bit=True,
    device_map="auto"
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
```

---

## Results

| Rank | VRAM (GB) | Trainable Params | Time/Epoch |
|------|-----------|------------------|------------|
| 8 | 6.2 | 4.2M | 45 min |
| 16 | 6.5 | 8.4M | 48 min |
| 32 | 7.1 | 16.8M | 52 min |
| 64 | 8.3 | 33.6M | 60 min |

### Key Findings

1. ✅ QLoRA works on an 11GB VRAM GPU
2. ✅ Rank 16 provides best balance
3. ✅ Gradient checkpointing enables batch size 4
4. ⚠️ Training takes ~2.5 hours for 3 epochs

---

## Recommendations

**Optimal Config for an 11GB-class GPU:**
```python
lora_r = 16
lora_alpha = 32
batch_size = 4
gradient_accumulation = 4
learning_rate = 2e-4
```

---

**Next Steps:** [5201: DPO](./EXP_5201_DPO.md) - Apply DPO alignment
