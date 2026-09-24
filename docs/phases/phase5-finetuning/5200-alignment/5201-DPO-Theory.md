---
Document ID: 5201
Title: DPO (Direct Preference Optimization) Theory
Phase: 5
Module: 5200
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'alignment', 'dpo', 'rlhf', 'preference']
---

# 5201: DPO (Direct Preference Optimization) Theory

## Abstract
DPO (Direct Preference Optimization) is a simpler alternative to RLHF (Reinforcement Learning from Human Feedback) that optimizes language models directly from preference data without training a separate reward model.

## The Problem with RLHF

### RLHF Pipeline
```
Traditional RLHF requires:
1. SFT Model → Collect completions
2. Human Labeling → Rank completions
3. Train Reward Model → Predict human preferences
4. PPO Training → Optimize with reward model + KL constraint

Problems:
- Complex: Need to train and maintain reward model
- Unstable: PPO is sensitive to hyperparameters
- Expensive: Requires multiple passes through data
- Sample inefficient: Many samples per update
```

### RLHF Objective
```
RLHF maximizes:

L(π) = E[log π(y|x) × R(x, y)] - KL(π || π_ref)

Where:
- π: Policy being optimized
- π_ref: Reference policy (SFT model)
- R: Reward model (trained on human preferences)
- KL: Divergence constraint (prevent over-optimization)

Requires separate reward model training!
```

## DPO Intuition

### Key Insight
```
DPO eliminates the reward model:

RLHF: Maximize reward R(x,y) subject to KL constraint
DPO:  Directly optimize from preference pairs

Mathematical equivalence:
  The optimal policy in RLHF has a closed-form solution!

π*(y|x) = π_ref(y|x) × exp(1/β × R(x,y)) / Z(x)

Where:
- π*: Optimal policy
- π_ref: Reference policy
- R: Reward function
- β: KL constraint coefficient
- Z: Normalization constant

Take log:
  log π*(y|x) = log π_ref(y|x) + R(x,y)/β - log Z(x)

Rearrange for reward:
  R(x,y) = β × [log π*(y|x) - log π_ref(y|x) + log Z(x)]

This means: Reward = log-ratio of policy to reference!
```

### DPO Derivation
```
Given preference: (y_w preferred over y_l)

 Bradley-Terry model:
  P(y_w ≻ y_l) = σ(R(x,y_w) - R(x,y_l))

Where σ is logistic function

Substitute DPO reward expression:
  P(y_w ≻ y_l) = σ(β[log π(y_w|x) - log π(y_l|x)])

Optimization objective:
  Maximize log-likelihood of preferences
  L = E[log σ(β[log π(y_w|x) - log π(y_l|x)])]

No reward model needed!
```

## DPO Implementation

### DPO Loss Function
```python
import torch
import torch.nn.functional as F

def dpo_loss(
    policy_chosen_logps,
    policy_rejected_logps,
    reference_chosen_logps,
    reference_rejected_logps,
    beta=0.1,
    label_smoothing=0.0
):
    """
    DPO loss

    Args:
        policy_chosen_logps: Log probs of chosen samples under current policy
        policy_rejected_logps: Log probs of rejected samples under current policy
        reference_chosen_logps: Log probs of chosen samples under reference policy
        reference_rejected_logps: Log probs of rejected samples under reference policy
        beta: KL constraint coefficient
        label_smoothing: Label smoothing factor
    """
    # Compute log ratios
    policy_logratios = policy_chosen_logps - policy_rejected_logps
    reference_logratios = reference_chosen_logps - reference_rejected_logps

    # DPO preference: π is better than ref
    losses = -F.logsigmoid(
        beta * (policy_logratios - reference_logratios)
    )

    # Optional: Label smoothing
    if label_smoothing > 0:
        losses = losses * (1 - label_smoothing) + label_smoothing * 0.5

    return losses.mean()

# Example usage
policy_chosen = torch.randn(32)  # Batch of 32
policy_rejected = torch.randn(32)
ref_chosen = torch.randn(32)
ref_rejected = torch.randn(32)

loss = dpo_loss(
    policy_chosen,
    policy_rejected,
    ref_chosen,
    ref_rejected,
    beta=0.1
)
```

### Full DPO Training Loop
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
import torch

# 1. Load models
model = AutoModelForCausalLM.from_pretrained("llama-2-7b-sft")
ref_model = AutoModelForCausalLM.from_pretrained("llama-2-7b-sft")
ref_model.eval()  # Reference model is frozen

tokenizer = AutoTokenizer.from_pretrained("llama-2-7b-sft")

# 2. Load preference dataset
# Format: {"prompt": str, "chosen": str, "rejected": str}
dataset = load_dataset("Anthropic/hh-rlhf", split="train")

def compute_logprobs(model, input_ids, attention_mask):
    """
    Compute log probabilities for sequences
    """
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=input_ids,
    )
    logits = outputs.logits

    # Compute log probabilities
    log_probs = torch.log_softmax(logits, dim=-1)

    # Gather log probs for actual tokens
    token_log_probs = torch.gather(
        log_probs[:, :-1, :],
        2,
        input_ids[:, 1:].unsqueeze(-1)
    ).squeeze(-1)

    # Mask out padding
    token_log_probs = token_log_probs * attention_mask[:, 1:]

    # Sum over sequence
    return token_log_probs.sum(-1)

# 3. Training loop
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-6)
beta = 0.1

for epoch in range(3):
    for batch in dataset:
        # Tokenize
        chosen = tokenizer(
            batch["prompt"] + batch["chosen"],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )
        rejected = tokenizer(
            batch["prompt"] + batch["rejected"],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )

        # Compute log probs
        with torch.no_grad():
            ref_chosen_logps = compute_logprobs(
                ref_model,
                chosen["input_ids"],
                chosen["attention_mask"]
            )
            ref_rejected_logps = compute_logprobs(
                ref_model,
                rejected["input_ids"],
                rejected["attention_mask"]
            )

        policy_chosen_logps = compute_logprobs(
            model,
            chosen["input_ids"],
            chosen["attention_mask"]
        )
        policy_rejected_logps = compute_logprobs(
            model,
            rejected["input_ids"],
            rejected["attention_mask"]
        )

        # DPO loss
        loss = dpo_loss(
            policy_chosen_logps,
            policy_rejected_logps,
            ref_chosen_logps,
            ref_rejected_logps,
            beta=beta
        )

        # Optimize
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
```

## DPO Hyperparameters

### Beta (KL Coefficient)
```python
# Beta controls how far policy can deviate from reference

beta_effects = {
    "beta=0.01": "Tight constraint, minimal deviation",
    "beta=0.1": "Default, balanced learning",
    "beta=0.5": "Loose constraint, more deviation",
    "beta=1.0": "Very loose, risk of over-optimization",
}

# Rule of thumb: Start with beta=0.1
# If underfitting: Increase to 0.2-0.5
# If unstable: Decrease to 0.05
```

### Learning Rate
```python
# DPO requires lower learning rates than SFT

lr_schedule = {
    "SFT": 1e-4,      # Supervised fine-tuning
    "DPO": 1e-6,      # Direct preference optimization
}

# Lower LR because:
# 1. We're close to optimal (after SFT)
# 2. High LR can cause policy collapse
# 3. Log-ratios amplify gradients

# Schedule: Constant or cosine decay
```

## DPO Variants

### Identity Preference Optimization (IPO)
```python
def ipo_loss(
    policy_chosen_logps,
    policy_rejected_logps,
    reference_chosen_logps,
    reference_rejected_logps,
    beta=0.1
):
    """
    IPO: More stable for intractable normalization

    Key difference: Square the objective
    """
    policy_logratios = policy_chosen_logps - policy_rejected_logps
    reference_logratios = reference_chosen_logps - reference_rejected_logps

    losses = (policy_logratios - reference_logratios) ** 2

    return losses.mean()
```

### Kahneman-Tversky Optimization (KTO)
```python
def kto_loss(
    policy_logprobs,
    reference_logprobs,
    is_chosen,
    beta=0.1
):
    """
    KTO: Optimize without preference pairs

    Uses: Binary chosen/rejected labels
    """
    # KL divergence
    kl = policy_logprobs - reference_logprobs

    # Chosen: Reward = KL
    # Rejected: Reward = -KL
    rewards = torch.where(is_chosen, kl, -kl)

    # Loss: Push chosen KL up, rejected KL down
    losses = torch.where(is_chosen, -rewards, rewards)

    return losses.mean() * beta
```

### DPO with Label Smoothing
```python
def dpo_loss_with_label_smoothing(
    policy_chosen_logps,
    policy_rejected_logps,
    reference_chosen_logps,
    reference_rejected_logps,
    beta=0.1,
    label_smoothing=0.1  # 10% smoothing
):
    """
    Label smoothing: Prevent overconfidence
    """
    policy_logratios = policy_chosen_logps - policy_rejected_logps
    reference_logratios = reference_chosen_logps - reference_rejected_logps

    # Standard DPO
    losses = -F.logsigmoid(
        beta * (policy_logratios - reference_logratios)
    )

    # Apply label smoothing
    # Smooth: (1 - α) × loss + α × 0.5
    losses = (1 - label_smoothing) * losses + label_smoothing * 0.5

    return losses.mean()
```

## Using Libraries

### TRL (Transformer Reinforcement Learning)
```python
from trl import DPOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

# Load models
model = AutoModelForCausalLM.from_pretrained("llama-2-7b-sft")
ref_model = AutoModelForCausalLM.from_pretrained("llama-2-7b-sft")
tokenizer = AutoTokenizer.from_pretrained("llama-2-7b-sft")

# Load dataset
dataset = load_dataset("Anthropic/hh-rlhf", split="train")

# DPO Trainer
dpo_trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    beta=0.1,
    max_length=512,
    max_prompt_length=256,
    generate_during_eval=False,
)

# Train
dpo_trainer.train()
```

### Custom DPO with PEFT
```python
from peft import LoraConfig, get_peft_model
from trl import DPOTrainer

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "llama-2-7b-sft",
    quantization_config=bnb_config,  # 4-bit
)

# Add LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
)

model = get_peft_model(model, lora_config)

# DPO with LoRA
dpo_trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    beta=0.1,
    peft_config=lora_config,
)
```


---

## Next Steps

- Continue with: **[5202: Alignment Orchestration](./5202-Alignment-Orchestration.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [5202: Alignment Orchestration](./5202-Alignment-Orchestration.md)
- [5102: QLoRA Pipelines](../5100-PEFT/5102-QLoRA-Pipelines.md)
- [7002: Collaborative Tasking](../../phase7-agentic/7300-orchestration/7301-Orchestration.md)

**Experiment Template:** `experiments/EXP_5201_DPO.md`
