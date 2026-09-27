---
Document ID: 5202
Title: Alignment Orchestration - Reward Modeling vs Direct Preference
Phase: 5
Module: 5200
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'alignment', 'dpo', 'rlhf', 'preference']
---

# 5202: Alignment Orchestration - Reward Modeling vs Direct Preference

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Alignment Methods Comparison](#alignment-methods-comparison)
- [Reward Modeling (RLHF)](#reward-modeling-rlhf)
- [Direct Preference Optimization](#direct-preference-optimization)
- [KTO (Kahneman-Tversky Optimization)](#kto-kahneman-tversky-optimization)
- [Practical Alignment Pipeline](#practical-alignment-pipeline)
- [Evaluation](#evaluation)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare the method families by moving parts and failure modes — SFT baseline; PPO adds reward + value + reference models and the largest tuning surface; DPO drops the reward model; KTO drops the pairs; IPO trades a little quality for stability
- Train a Bradley–Terry reward model — `AutoModelForSequenceClassification` with `num_labels=1`, loss −log σ(R_chosen − R_rejected) — and decide when the PPO detour pays for itself (>100K preferences, reward reused across tasks)
- Frame DPO (from 5201) as the orchestration default: no reward model, π_ref = the SFT checkpoint (not the base model), `DPOConfig` + `processing_class=tokenizer`
- Run KTO on unpaired binary feedback — dataset `{prompt, completion, label: bool}` (True = desirable), `KTOConfig` carries beta/desirable_weight, lr kept in 5e-7–5e-6 for β=0.1
- Assemble the two-stage pipeline — SFT first to learn the format, preference optimization second with lr an order of magnitude lower
- Evaluate alignment: reward deltas before/after scored by a held-out reward model, plus a side-by-side human protocol (A / B / tie / both-bad)

---

## Abstract
This document compares alignment approaches: Reward Modeling (RLHF) versus Direct Preference Optimization (DPO), and when to use each.

## Alignment Methods Comparison

### Full Comparison Table
```text
Method          | Reward Model | Stability | Sample Eff | Complexity | Quality
──────────────────────────────────────────────────────────────────────────
SFT             | No           | High      | High       | Low        | Baseline
PPO (RLHF)      | Yes          | Medium    | Low        | High       | Best
DPO             | No           | High      | High       | Medium     | Very Good
KTO             | No           | High      | High       | Medium     | Good
IPO             | No           | Very High | Medium     | Medium     | Very Good
```

### Decision Tree
```text
Start → Have preference pairs?
         ├─ Yes → Use DPO or IPO
         │        ├─ Noisy / overconfident prefs? → IPO
         │        └─ Default? → DPO
         │
         └─ No → Have binary feedback?
                  ├─ Yes → Use KTO
                  └─ No → Start with SFT
```

## Reward Modeling (RLHF)

### When to Use Reward Models
```text
Use Reward Modeling when:
✓ You have extensive preference data (>100K samples)
✓ You need the absolute best quality
✓ You can afford the complexity
✓ You want to reuse reward model for other tasks

Avoid Reward Modeling when:
✗ Limited data (<10K samples)
✗ Need rapid iteration
✗ Resource constrained
✗ Preference data quality is variable
```

### Reward Model Training
```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from datasets import load_dataset

# 1. Load dataset — prompt is a string, chosen/rejected are MESSAGE
# LISTS (assistant turn last): flatten to plain text
def to_pair(example):
    return {
        "prompt": example["prompt"],
        "chosen": example["chosen"][-1]["content"],
        "rejected": example["rejected"][-1]["content"],
    }

dataset = load_dataset(
    "argilla/ultrafeedback-binarized-preferences-cleaned", split="train"
).map(to_pair).select(range(256))  # demo slice

# 2. Load reward model (classification head)
reward_model = AutoModelForSequenceClassification.from_pretrained(
    "gpt2",
    num_labels=1,  # Single scalar reward
)
tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token  # GPT-2 ships no pad token
SEP = tokenizer.eos_token                 # ...and no sep token — use EOS

# 3. Prepare data
def prepare_batch(batch):
    """Format: prompt + [SEP] + chosen/rejected"""
    chosen_texts = [f"{p}{SEP}{c}"
                    for p, c in zip(batch["prompt"], batch["chosen"])]
    rejected_texts = [f"{p}{SEP}{r}"
                      for p, r in zip(batch["prompt"], batch["rejected"])]

    chosen_inputs = tokenizer(chosen_texts, padding=True, return_tensors="pt")
    rejected_inputs = tokenizer(rejected_texts, padding=True, return_tensors="pt")

    return {
        "chosen_input_ids": chosen_inputs["input_ids"],
        "chosen_attention_mask": chosen_inputs["attention_mask"],
        "rejected_input_ids": rejected_inputs["input_ids"],
        "rejected_attention_mask": rejected_inputs["attention_mask"],
    }

# 4. Reward model loss
def reward_model_loss(chosen_rewards, rejected_rewards):
    """
    Bradley-Terry loss for reward modeling

    We want: R(chosen) > R(rejected)
    Loss: -log σ(R(chosen) - R(rejected))
    """
    return -torch.logsigmoid(chosen_rewards - rejected_rewards).mean()

# 5. Training loop
optimizer = torch.optim.AdamW(reward_model.parameters(), lr=1e-5)

for batch in dataset:
    data = prepare_batch(batch)

    # Forward pass
    chosen_rewards = reward_model(
        input_ids=data["chosen_input_ids"],
        attention_mask=data["chosen_attention_mask"],
    ).logits.squeeze(-1)

    rejected_rewards = reward_model(
        input_ids=data["rejected_input_ids"],
        attention_mask=data["rejected_attention_mask"],
    ).logits.squeeze(-1)

    # Compute loss
    loss = reward_model_loss(chosen_rewards, rejected_rewards)

    # Optimize
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
```

### PPO Training with Reward Model
```python
# PPO is the heavyweight path: policy + reference + reward model +
# value model, four moving parts per step. TRL removed it from the
# stable surface (v1.x docs have no PPO page) — it now lives in
# trl.experimental.ppo on main. The lesson's thesis: DPO/KTO give
# most of the quality for a fraction of this moving-part count.
from trl.experimental.ppo import PPOConfig, PPOTrainer  # TRL main, experimental

ppo_config = PPOConfig(
    output_dir="./ppo_output",
    learning_rate=3e-6,   # PPO default; hyperparameter-sensitive
    response_length=64,
)

# Plain causal LM models — no value-head wrapper in the modern API
ppo_trainer = PPOTrainer(
    args=ppo_config,
    model=sft_model,            # policy
    ref_model=None,             # None -> trainer copies the policy
    reward_model=reward_model,  # trained above (num_labels=1)
    value_model=value_model,    # value head for the advantage estimate
    train_dataset=prompt_dataset,
    processing_class=tokenizer,
)

ppo_trainer.train()
```

## Direct Preference Optimization

### DPO Implementation (Recap)
```python
from trl import DPOConfig, DPOTrainer

# DPO is simpler: no reward model needed! Full loss walkthrough: 5201

dpo_trainer = DPOTrainer(
    model=policy_model,
    ref_model=reference_model,  # pi_ref = the SFT policy you started from;
                                # with LoRA pass ref_model=None instead (5201)
    args=DPOConfig(output_dir="./dpo_output", beta=0.1),
    train_dataset=preference_dataset,
    processing_class=tokenizer,
)

dpo_trainer.train()
```

### DPO Pros and Cons
```text
Pros:
✓ No separate reward model training
✓ More stable (no PPO)
✓ Sample efficient
✓ Easier to implement
✓ Less hyperparameter tuning

Cons:
✗ Slightly worse than well-tuned PPO
✗ Requires preference pairs
✗ Reference model frozen (can't adapt)
```

## KTO (Kahneman-Tversky Optimization)

### KTO for Binary Feedback
```python
from datasets import load_dataset
from trl import KTOConfig, KTOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer

# KTO works with binary feedback (desirable/undesirable) — no pairs.
# Dataset format — label is a BOOLEAN, not 0/1:
# {"prompt": str, "completion": str, "label": True/False}

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2-0.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-0.5B-Instruct")

dataset = load_dataset("trl-lib/kto-mix-14k", split="train")

training_args = KTOConfig(
    output_dir="./kto_output",
    beta=0.1,
    learning_rate=1e-6,  # keep in 5e-7..5e-6 for beta=0.1 (TRL guidance)
    # Imbalanced labels? Upweight the minority via
    # desirable_weight / undesirable_weight (target ratio 1:1..4:3)
)

# ref_model=None -> the initial policy becomes the reference
kto_trainer = KTOTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    processing_class=tokenizer,
)

kto_trainer.train()
```

### When to Use KTO
```text
Use KTO when:
✓ You have binary feedback (thumbs up/down)
✓ Preference pairs not available
✓ User feedback data (likes/dislikes)
✓ Simpler than DPO

Example: Chatbot analytics
- User gave 4+ stars: positive
- User gave <3 stars: negative
- Train KTO directly!
```

## Practical Alignment Pipeline

### Recommended Pipeline
```text
Stage 1: SFT (Supervised Fine-Tuning)
  Goal: Learn task format
  Data: Instruction-response pairs
  Epochs: 1-3

Stage 2: Preference Optimization
  Goal: Align with human preferences
  Options:
    - DPO (if preference pairs available)
    - KTO (if binary feedback available)
    - IPO (if stability critical)
  Epochs: 1-2

Stage 3: Evaluation
  Metrics:
    - Human eval
    - Model-based eval (using separate reward model)
    - Side-by-side comparison
```

### Full Pipeline Implementation
```python
from transformers import AutoModelForCausalLM, Trainer, TrainingArguments
from trl import DPOConfig, DPOTrainer, SFTTrainer

# Stage 1: SFT
sft_trainer = SFTTrainer(
    model=base_model,
    train_dataset=instruction_dataset,
    tokenizer=tokenizer,
    args=TrainingArguments(
        output_dir="./sft-checkpoint",
        num_train_epochs=1,
        learning_rate=2e-4,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
    ),
)

sft_trainer.train()
sft_trainer.save_model("./sft-checkpoint")
sft_model = sft_trainer.model

# Stage 2: DPO — DPOTrainer takes a DPOConfig, not TrainingArguments
ref_model = AutoModelForCausalLM.from_pretrained("./sft-checkpoint")
ref_model.eval()  # pi_ref = the SFT policy you are diverging from,
                  # NOT the pre-SFT base model

dpo_trainer = DPOTrainer(
    model=sft_model,
    ref_model=ref_model,
    args=DPOConfig(
        output_dir="./dpo-checkpoint",
        beta=0.1,
        learning_rate=5e-7,  # an order of magnitude below SFT's 2e-4
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
    ),
    train_dataset=preference_dataset,
    processing_class=tokenizer,
)

dpo_trainer.train()
aligned_model = dpo_trainer.model
```

## Evaluation

### Reward Model Evaluation
```python
# Score with a reward model held out from training (in production,
# train it on a disjoint split — never the RM you optimized against)

eval_reward_model = reward_model  # placeholder: the RM trained above

def compute_reward(prompt, response):
    """Score a prompt-response pair (the RM is fixed — no model arg)"""
    text = f"{prompt}{SEP}{response}"
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        return eval_reward_model(**inputs).logits.item()

# Compare before/after alignment — generate() takes tokenized input
test_prompts = ["Write a poem about AI", "Explain quantum computing"]

for prompt in test_prompts:
    inputs = tokenizer(prompt, return_tensors="pt")
    before_response = tokenizer.decode(
        sft_model.generate(**inputs, max_new_tokens=64)[0]
    )
    after_response = tokenizer.decode(
        aligned_model.generate(**inputs, max_new_tokens=64)[0]
    )

    print(f"Prompt: {prompt}")
    print(f"Before: {compute_reward(prompt, before_response):.2f}")
    print(f"After: {compute_reward(prompt, after_response):.2f}")
```

### Human Evaluation
```python
# Side-by-side comparison

def human_eval(model_a, model_b, test_prompts):
    """
    Generate side-by-side comparisons for human evaluation
    """
    results = []

    for prompt in test_prompts:
        response_a = model_a.generate(prompt)
        response_b = model_b.generate(prompt)

        results.append({
            "prompt": prompt,
            "response_a": response_a,
            "response_b": response_b,
        })

    return results

# Human annotator sees:
# Prompt: ...
# Response A: ...
# Response B: ...
# Which is better? [A] [B] [Tie] [Both bad]
```

---

## References

### Related ai-engineering-curriculum Documents

- [5201: DPO (Direct Preference Optimization) Theory](5201-DPO-Theory.md)
- [5203: Reinforcement Learning from Human Feedback](5203-RLHF.md)
- [5204: Preference Dataset Creation](5204-Preference-Dataset-Creation.md)

---

## Next Steps

- Continue with: **[5301: Knowledge Distillation](./../5300-synthetic/5301-Knowledge-Distillation.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_5202: Alignment](../../../../experiments/EXP_5202_ALIGNMENT.md)**
- Practice DPO on top of QLoRA: **[5102: QLoRA Pipelines](../5100-peft/5102-QLoRA-Pipelines.md)**
