---
Document ID: 5201
Title: "5201: DPO (Direct Preference Optimization) Theory"
Phase: 5
Module: 5200
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'alignment', 'dpo', 'rlhf', 'preference']
---

# 5201: DPO (Direct Preference Optimization) Theory

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Problem with RLHF](#the-problem-with-rlhf)
- [DPO Intuition](#dpo-intuition)
- [DPO Implementation](#dpo-implementation)
- [DPO Hyperparameters](#dpo-hyperparameters)
- [DPO Variants](#dpo-variants)
- [Using Libraries](#using-libraries)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Trace the RLHF pipeline's three moving parts — SFT model, a separately-trained reward model, PPO against E[R] − β·KL(π‖π_ref) — and read the closed-form optimal policy π* = π_ref·exp(R/β)/Z that replaces all of it
- Derive DPO by substituting R = β·log(π/π_ref) + β·log Z into Bradley–Terry — the log Z cancels in the chosen−rejected difference while the reference log-probs stay in: L = −E[log σ(β·(Δ_w − Δ_l))] with Δ_y = log π(y|x) − log π_ref(y|x)
- Implement the loss and the per-sequence log-prob gather — shifted logits, token log probs, attention-masked sum — with reference logps under `torch.no_grad()` and lr ~5e-7, orders below SFT's 1e-4
- Predict what β does before tuning it: it divides the implicit reward (π* ∝ exp(R/β)), so 0.1 balances, 0.01 lets the policy drift far from π_ref, 0.5 pins it close — over-optimization raises β, underfitting lowers it
- Distinguish the variants by objective: IPO's squared hinge targets Δ = 1/(2β), not Δ = 0; KTO drops pairs for binary labels with saturating 1−σ curves around τ/β; cDPO label smoothing interpolates with the FLIPPED preference's loss, not a constant
- Run DPO through TRL — DPOConfig carries beta/max_length, `processing_class=tokenizer`, and with LoRA pass `ref_model=None` so the reference pass just disables the adapters instead of loading a second 7B

---

## Abstract
DPO (Direct Preference Optimization) is a simpler alternative to RLHF (Reinforcement Learning from Human Feedback) that optimizes language models directly from preference data without training a separate reward model.

## The Problem with RLHF

### RLHF Pipeline
```text
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
```text
RLHF maximizes (per prompt x):

  max_π  E_{y∼π(·|x)}[ R(x, y) ]  −  β · KL( π(·|x) ‖ π_ref(·|x) )

Where:
- π: Policy being optimized
- π_ref: Reference policy (frozen SFT model)
- R: Reward model (trained on human preferences)
- β: KL penalty strength

Three trained/tuned artifacts in the loop: the reward model, PPO's
hyperparameters, and β itself.

Requires separate reward model training!
```

## DPO Intuition

### Key Insight
```text
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
```text
Given preference: (y_w preferred over y_l)

 Bradley-Terry model:
  P(y_w ≻ y_l) = σ(R(x,y_w) - R(x,y_l))

Where σ is logistic function

Substitute the DPO reward — the log Z(x) terms are identical in the
chosen and rejected rewards, so they CANCEL:
  R(y_w) - R(y_l) = β[(logπ(y_w|x) - logπ_ref(y_w|x))
                    - (logπ(y_l|x) - logπ_ref(y_l|x))]

  P(y_w ≻ y_l) = σ(β[Δ_w - Δ_l])
  where Δ_y := log π(y|x) - log π_ref(y|x)

The reference terms are load-bearing — drop them and the objective
only rewards changes from the model's own past self, not quality.

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
    logits = beta * (policy_logratios - reference_logratios)

    # DPO preference: policy beats reference
    losses = -F.logsigmoid(logits)

    # Optional: cDPO label smoothing (Mitchell, 2023). NOTE: adding a
    # constant "alpha * 0.5" is NOT smoothing — constants have zero
    # gradient, so it only rescales the loss by (1 - alpha). Real
    # smoothing interpolates with the FLIPPED preference's loss:
    if label_smoothing > 0:
        losses = (1 - label_smoothing) * losses \
               + label_smoothing * -F.logsigmoid(-logits)

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

# 1. Load models (ungated SFT checkpoint — the Zephyr recipe's stage 1)
model = AutoModelForCausalLM.from_pretrained("HuggingFaceH4/mistral-7b-sft-beta")
ref_model = AutoModelForCausalLM.from_pretrained("HuggingFaceH4/mistral-7b-sft-beta")
ref_model.eval()  # Reference model is frozen

tokenizer = AutoTokenizer.from_pretrained("HuggingFaceH4/mistral-7b-sft-beta")

# 2. Load preference dataset. argilla/ultrafeedback-binarized-preferences-cleaned
# stores prompt as a string but chosen/rejected as MESSAGE LISTS (assistant
# turn last) — flatten to the {prompt, chosen, rejected} strings the loop needs
def to_pair(example):
    return {
        "prompt": example["prompt"],
        "chosen": example["chosen"][-1]["content"],
        "rejected": example["rejected"][-1]["content"],
    }

dataset = load_dataset(
    "argilla/ultrafeedback-binarized-preferences-cleaned", split="train"
).map(to_pair).select(range(256))  # demo slice

def compute_logprobs(model, input_ids, attention_mask):
    """
    Compute summed log probabilities for sequences
    """
    # No labels= here: passing labels makes HF compute an internal LM
    # loss this loop never uses — wasted loss/logits work per batch
    logits = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
    ).logits

    # Compute log probabilities
    log_probs = torch.log_softmax(logits, dim=-1)

    # Gather log probs for actual tokens — logits[t] predicts token t+1
    token_log_probs = torch.gather(
        log_probs[:, :-1, :],
        2,
        input_ids[:, 1:].unsqueeze(-1)
    ).squeeze(-1)

    # Mask out padding
    token_log_probs = token_log_probs * attention_mask[:, 1:]

    # Sum over sequence
    return token_log_probs.sum(-1)

# 3. Training loop — lr 5e-7: canonical DPO scale (Zephyr), orders
# below SFT's 1e-4; higher rates collapse the policy
optimizer = torch.optim.AdamW(model.parameters(), lr=5e-7)
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
# Beta scales the implicit reward: R(x,y) = beta * log-ratio, and the
# optimal policy is pi_ref * exp(R / beta) — a SMALL beta amplifies any
# log-ratio shift, so small beta means the WEAK constraint

beta_effects = {
    "beta=0.01": "Weak constraint — policy can drift far from the reference",
    "beta=0.1": "Default, balanced learning",
    "beta=0.5": "Strong constraint — stays close to the reference",
    "beta=1.0": "Very tight — minimal movement",
}

# Rule of thumb: Start with beta=0.1
# Over-optimization / drift: raise beta
# Underfitting (preferences ignored): lower beta
```

### Learning Rate
```python
# DPO requires lower learning rates than SFT

lr_schedule = {
    "SFT": "1e-4",         # Supervised fine-tuning
    "DPO": "5e-7 - 1e-6",  # Canonical DPO range (Zephyr used 5e-7)
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
    IPO: replaces the sigmoid with a squared hinge — bounded gradients
    (no saturation), stable when preference probabilities sit far
    from 0/1.
    """
    policy_logratios = policy_chosen_logps - policy_rejected_logps
    reference_logratios = reference_chosen_logps - reference_rejected_logps

    # The margin IS the objective: the optimum sits at a positive gap
    # delta = 1/(2*beta). Squaring bare log-ratios (no target) would
    # push delta -> 0 — i.e. the policy back ONTO the reference.
    logits = policy_logratios - reference_logratios
    losses = (logits - 1.0 / (2 * beta)) ** 2

    return losses.mean()
```

### Kahneman-Tversky Optimization (KTO)
```python
def kto_loss(
    policy_logprobs,
    reference_logprobs,
    is_chosen,
    beta=0.1,
    tau=0.5,
):
    """
    KTO: optimize without preference pairs

    Uses binary chosen/rejected labels instead of pairs. The real
    curves SATURATE — a linear push (kl for chosen, -kl for rejected)
    is unbounded and would drag the policy arbitrarily far from the
    reference.
    """
    kl = policy_logprobs - reference_logprobs  # log-ratio vs reference
    z = tau / beta                             # desired margin

    losses = torch.where(
        is_chosen,
        1 - torch.sigmoid(beta * (kl - z)),  # push chosen above z
        1 - torch.sigmoid(beta * (z - kl)),  # push rejected below z
    )

    return losses.mean()
    # (TRL's KTOTrainer adds per-class weights lambda_w/lambda_l on top)
```

### DPO with Label Smoothing
```python
# The cDPO smoothing implemented in dpo_loss() above is one config
# field in TRL — no custom loss needed. It swaps in
# (1-a)*logsigmoid(logits) + a*logsigmoid(-logits) internally
# (default 0.0 = plain DPO):
from trl import DPOConfig

training_args = DPOConfig(output_dir="./dpo_output", label_smoothing=0.1)
```

## Using Libraries

### TRL (Transformer Reinforcement Learning)
```python
from trl import DPOConfig, DPOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

# Ungated SFT checkpoint (Zephyr recipe stage 1)
model = AutoModelForCausalLM.from_pretrained("HuggingFaceH4/mistral-7b-sft-beta")
ref_model = AutoModelForCausalLM.from_pretrained("HuggingFaceH4/mistral-7b-sft-beta")
tokenizer = AutoTokenizer.from_pretrained("HuggingFaceH4/mistral-7b-sft-beta")
tokenizer.pad_token = tokenizer.eos_token  # Mistral tokenizer ships no pad

# prompt is a string, chosen/rejected are message lists — flatten to
# the plain-text columns DPOTrainer expects
def to_pair(example):
    return {
        "prompt": example["prompt"],
        "chosen": example["chosen"][-1]["content"],
        "rejected": example["rejected"][-1]["content"],
    }

dataset = load_dataset(
    "argilla/ultrafeedback-binarized-preferences-cleaned", split="train"
).map(to_pair).select(range(256))  # demo slice

# All hyperparameters live in DPOConfig (beta, max_length and
# generate_during_eval are config fields, not trainer kwargs).
# max_prompt_length no longer exists in TRL - truncate the
# prompt/completion columns during data prep instead.
training_args = DPOConfig(
    output_dir="./dpo_output",
    beta=0.1,
    learning_rate=5e-7,
    max_length=512,
    generate_during_eval=False,
)

# DPO Trainer
dpo_trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    args=training_args,
    train_dataset=dataset,
    processing_class=tokenizer,
)

# Train
dpo_trainer.train()
```

### Custom DPO with PEFT
```python
import torch
from peft import LoraConfig
from trl import DPOConfig, DPOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

model = AutoModelForCausalLM.from_pretrained(
    "HuggingFaceH4/mistral-7b-sft-beta",
    dtype=torch.bfloat16,
    # 11GB-class: add BitsAndBytesConfig 4-bit here (see 5102)
)
tokenizer = AutoTokenizer.from_pretrained("HuggingFaceH4/mistral-7b-sft-beta")
tokenizer.pad_token = tokenizer.eos_token

def to_pair(example):
    return {
        "prompt": example["prompt"],
        "chosen": example["chosen"][-1]["content"],
        "rejected": example["rejected"][-1]["content"],
    }

dataset = load_dataset(
    "argilla/ultrafeedback-binarized-preferences-cleaned", split="train"
).map(to_pair).select(range(256))

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    task_type="CAUSAL_LM",
)

# LoRA route: ref_model=None — TRL computes the reference pass by
# DISABLING the adapters, so no second 7B copy sits in VRAM.
# DPOTrainer wraps model with peft_config itself; no get_peft_model call.
dpo_trainer = DPOTrainer(
    model=model,
    ref_model=None,
    args=DPOConfig(output_dir="./dpo_peft", beta=0.1, max_length=512),
    train_dataset=dataset,
    processing_class=tokenizer,
    peft_config=lora_config,
)
```


---

## Summary

DPO's insight is that the reward model RLHF trains is a middleman you can eliminate: from preference pairs alone, the direct preference objective optimizes the policy against a reference model - no reward model, no RL loop. This lesson set up why RLHF is hard, built the DPO intuition from its loss, then the practice: implementation, the hyperparameters that decide stability, the variants that fix its known weaknesses, and the libraries that make it a config change. The rule it leaves: try DPO first, and reach for full RLHF only when DPO's ceiling shows.

## References

### Related Minder Academy Documents

- [5202: Alignment Orchestration - Reward Modeling vs Direct Preference](5202-Alignment-Orchestration.md)
- [5203: Reinforcement Learning from Human Feedback](5203-RLHF.md)
- [5204: Preference Dataset Creation](5204-Preference-Dataset-Creation.md)

---

## Next Steps

- Continue with: **[5202: Alignment Orchestration](./5202-Alignment-Orchestration.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_5201: DPO](../../../../experiments/EXP_5201_DPO.md)**
- Practice DPO on top of QLoRA: **[5102: QLoRA Pipelines](../5100-peft/5102-QLoRA-Pipelines.md)**
