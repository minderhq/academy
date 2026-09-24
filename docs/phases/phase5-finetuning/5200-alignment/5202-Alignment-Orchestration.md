---
Document ID: 5202
Title: Alignment Orchestration - Reward Modeling vs Direct Preference
Phase: 5
Module: 5200
Last Updated: 2026-09-24
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

- Compare Alignment Methods Comparison
- Explain Reward Modeling (RLHF)
- Explain Direct Preference Optimization
- Explain KTO (Kahneman-Tversky Optimization)
- Explain Practical Alignment Pipeline
- Measure and evaluate Evaluation

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
         │        ├─ Want best quality? → IPO
         │        └─ Want simplicity? → DPO
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
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from datasets import load_dataset

# 1. Load dataset
# Format: {"prompt": str, "chosen": str, "rejected": str}
dataset = load_dataset("Anthropic/hh-rlhf", split="train")

# 2. Load reward model (classification head)
reward_model = AutoModelForSequenceClassification.from_pretrained(
    "gpt2",
    num_labels=1,  # Single scalar reward
)
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# 3. Prepare data
def prepare_batch(batch):
    """Format: prompt + [SEP] + chosen/rejected"""
    chosen_texts = [f"{p}{tokenizer.sep_token}{c}"
                    for p, c in zip(batch["prompt"], batch["chosen"])]
    rejected_texts = [f"{p}{tokenizer.sep_token}{r}"
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
from trl import PPOTrainer, PPOConfig
from transformers import AutoModelForCausalLMWithValueHead

# 1. Load policy model with value head
policy = AutoModelForCausalLMWithValueHead.from_pretrained("llama-2-7b-sft")

# 2. Load reward model (frozen)
reward_model = AutoModelForSequenceClassification.from_pretrained("reward-model")
reward_model.eval()

# 3. PPO config
ppo_config = PPOConfig(
    learning_rate=1.41e-5,
    batch_size=128,
    mini_batch_size=32,
    gradient_accumulation_steps=4,
)

# 4. PPO Trainer
ppo_trainer = PPOTrainer(
    config=ppo_config,
    model=policy,
    ref_model=None,  # PPOTrainer handles reference model
    reward_model=reward_model,
    tokenizer=tokenizer,
)

# 5. Generate responses and optimize
for batch in dataloader:
    # Generate responses
    response_tensors = ppo_trainer.generate(
        batch["input_ids"],
        max_new_tokens=64,
    )

    # Compute rewards
    rewards = [
        reward_model(input_ids=r, attention_mask=r.attention_mask).logits.squeeze(-1)
        for r in response_tensors
    ]

    # PPO step
    stats = ppo_trainer.step(
        batch["input_ids"],
        response_tensors,
        rewards,
    )
```

## Direct Preference Optimization

### DPO Implementation (Recap)
```python
from trl import DPOTrainer

# DPO is simpler: No reward model needed!

dpo_trainer = DPOTrainer(
    model=policy_model,
    ref_model=reference_model,  # Can be shared with policy to save memory
    train_dataset=preference_dataset,
    tokenizer=tokenizer,
    beta=0.1,
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
from trl import KTOTrainer

# KTO works with binary feedback (good/bad)
# No need for preference pairs!

# Dataset format:
# {"prompt": str, "completion": str, "label": 0/1}
# 0 = rejected, 1 = accepted

kto_trainer = KTOTrainer(
    model=model,
    ref_model=ref_model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    beta=0.1,
    # No preference pairs needed!
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
from transformers import Trainer, TrainingArguments
from trl import DPOTrainer, SFTTrainer

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
sft_model = sft_trainer.model

# Stage 2: DPO
dpo_trainer = DPOTrainer(
    model=sft_model,
    ref_model=base_model,  # Use base as reference
    train_dataset=preference_dataset,
    tokenizer=tokenizer,
    beta=0.1,
    args=TrainingArguments(
        output_dir="./dpo-checkpoint",
        num_train_epochs=1,
        learning_rate=1e-6,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
    ),
)

dpo_trainer.train()
aligned_model = dpo_trainer.model
```

## Evaluation

### Reward Model Evaluation
```python
# Use held-out reward model for evaluation

eval_reward_model = AutoModelForSequenceClassification.from_pretrained(
    "separate-reward-model"
)

def compute_reward(model, prompt, response):
    """Compute reward for prompt-response pair"""
    text = f"{prompt}{tokenizer.sep_token}{response}"
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        reward = eval_reward_model(**inputs).logits.item()
    return reward

# Compare before/after alignment
test_prompts = ["Write a poem about AI", "Explain quantum computing"]

for prompt in test_prompts:
    before_response = sft_model.generate(prompt)
    after_response = aligned_model.generate(prompt)

    before_reward = compute_reward(sft_model, prompt, before_response)
    after_reward = compute_reward(aligned_model, prompt, after_response)

    print(f"Prompt: {prompt}")
    print(f"Before: {before_reward:.2f}")
    print(f"After: {after_reward:.2f}")
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

---
---

**Related Documents:**
- [5201: DPO Theory](./5201-DPO-Theory.md)
- [5102: QLoRA Pipelines](../5100-PEFT/5102-QLoRA-Pipelines.md)
- [7101: ReAct Loop](../../phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)

**Experiment Template:** `experiments/EXP_5202_ALIGNMENT.md`
