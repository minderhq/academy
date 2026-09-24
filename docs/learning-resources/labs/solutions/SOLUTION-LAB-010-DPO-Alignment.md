# SOLUTION-LAB-010: DPO Alignment

## Overview
Complete solution for Direct Preference Optimization alignment.

---

## Problem Statement

Align an LLM to prefer better responses using human preference data without training a separate reward model.

---

## Core Solution

### DPO Configuration and Training

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOTrainer, DPOConfig
import torch
from datasets import Dataset

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
tokenizer.pad_token = tokenizer.eos_token

# DPO Configuration
dpo_config = DPOConfig(
    beta=0.1,                    # Temperature for DPO loss
    learning_rate=5e-5,          # Learning rate
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    max_length=512,              # Maximum sequence length
    max_prompt_length=256,       # Maximum prompt length
    max_target_length=256,       # Maximum response length
    warmup_ratio=0.1,
    logging_steps=10,
    save_steps=100,
    num_train_epochs=3,
    output_dir="./dpo-output"
)

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    torch_dtype=torch.float16,
    device_map="auto"
)
model_ref = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    torch_dtype=torch.float16,
    device_map="auto"
)

# Prepare preference dataset
def prepare_dataset():
    """Format preference pairs for DPO."""
    data = {
        "prompt": [
            "What is machine learning?",
            "Explain quantum computing",
            # ... more examples
        ],
        "chosen": [
            "Machine learning is a subset of AI...",
            "Quantum computing uses quantum bits...",
        ],
        "rejected": [
            "ML is like computers learning stuff",
            "Quantum is fast computing with atoms",
        ]
    }
    return Dataset.from_dict(data)

train_dataset = prepare_dataset()

# DPO Trainer
trainer = DPOTrainer(
    model=model,
    ref_model=model_ref,
    args=dpo_config,
    beta=dpo_config.beta,
    train_dataset=train_dataset,
    tokenizer=tokenizer,
)

# Train
trainer.train()

# Save
trainer.save_model("./aligned-model")
tokenizer.save_pretrained("./aligned-model")
```

### Inference with Aligned Model

```python
from transformers import pipeline

# Load aligned model
generator = pipeline(
    "text-generation",
    model="./aligned-model",
    tokenizer=tokenizer,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Generate
prompt = "What is machine learning?"
outputs = generator(
    prompt,
    max_new_tokens=256,
    temperature=0.7,
    do_sample=True
)

print(outputs[0]['generated_text'])
```

---

## Key Concepts

### DPO Loss Function

```python
# DPO loss (simplified)
def dpo_loss(policy_logp, ref_logp, chosen, rejected):
    """
    policy_logp: Log probs from policy model
    ref_logp: Log probs from reference model
    """
    # Chosen reward
    chosen_reward = beta * (policy_logp_chosen - ref_logp_chosen)

    # Rejected reward
    rejected_reward = beta * (policy_logp_rejected - ref_logp_rejected)

    # DPO loss
    loss = -torch.log.sigmoid(chosen_reward - rejected_reward)
    return loss.mean()
```

### Dataset Format

```python
# Required format
{
    "prompt": "Your question here",
    "chosen": "Better response",
    "rejected": "Worse response"
}
```

---

## Common Issues

### Issue: CUDA Out of Memory

**Solution:**
```python
# Reduce batch size
per_device_train_batch_size=2

# Enable gradient checkpointing
gradient_checkpointing=True

# Use 8-bit loading
load_in_8bit=True
```

### Issue: Training Unstable

**Solution:**
```python
# Lower learning rate
learning_rate=1e-5

# Increase warmup
warmup_ratio=0.2

# Adjust beta
beta=0.05  # Lower is more stable
```

---

## Evaluation

```python
from trl import DPOTrainer

# Add evaluation dataset
eval_dataset = prepare_dataset()  # Separate test set

trainer = DPOTrainer(
    # ... other args
    eval_dataset=eval_dataset
)

# Evaluate
metrics = trainer.evaluate()
print(metrics)
```

---

## Next Steps

1. Collect more preference pairs
2. Evaluate with human raters
3. Compare with RLHF baseline
4. Deploy to production

---

**Last Updated:** 2026-02-05
**Difficulty:** ⭐⭐⭐⭐
**Estimated Time:** 2-3 hours

**Related:** [Phase 5: Alignment](../../../phases/phase5-finetuning/5200-alignment/README.md)
