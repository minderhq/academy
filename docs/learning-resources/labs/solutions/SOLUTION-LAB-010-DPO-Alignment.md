---
Document ID: SOLUTION-LAB-010
Title: "SOLUTION-LAB-010: DPO Alignment"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Tags: ['solution', 'dpo', 'alignment']
---

# SOLUTION-LAB-010: DPO Alignment

## Overview

Reference solution for [LAB-010: DPO Alignment](../LAB-010-DPO-Alignment.md): build a preference dataset, fine-tune with TRL's `DPOTrainer`, and evaluate whether alignment actually moved behavior. The theory (why a preference signal can replace a reward model) lives in [5201: DPO Theory](../../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md); the craft of building preference data in [5204: Preference Dataset Creation](../../../phases/phase5-finetuning/5200-alignment/5204-Preference-Dataset-Creation.md).

The solution uses the **current TRL API**: `beta`, sequence lengths, and every training knob live in `DPOConfig`; the tokenizer is passed as `processing_class`. If you have seen older examples pass `beta=...` or `max_prompt_length=...` straight to `DPOTrainer` — those parameters were moved into the config and (for the length caps) removed entirely.

---

## Exercise 1: Preference Dataset

### Solution

DPO needs triplets — a prompt, a preferred completion, and a rejected one:

```text
prompt     : "What is the capital of France?"
chosen     : "The capital of France is Paris, known for landmarks
             like the Eiffel Tower and the Louvre."
rejected   : "Paris."
```

```python
import json
from datasets import Dataset

with open("preference_pairs.json", encoding="utf-8") as f:
    pairs = json.load(f)

# DPOTrainer consumes prompt/chosen/rejected columns directly
ds = Dataset.from_list(pairs)

# ONE split, one seed - do not call train_test_split twice
split = ds.train_test_split(test_size=0.2, seed=42)
print(f"train: {len(split['train'])}, eval: {len(split['test'])}")
```

For a real run, start from an established preference corpus instead of hand-written pairs:

```python
from datasets import load_dataset

# Anthropic's helpful/harmless pairs (chosen/rejected conversations)
# datasets 5.x: select the harmless subset via data_dir (the named config was retired)
hh = load_dataset("Anthropic/hh-rlhf", data_dir="harmless-base")

# Binarized UltraFeedback (prompt/chosen/rejected + preference scores)
uf = load_dataset("argilla/ultrafeedback-binarized-preferences-cleaned")
```

**Honest expectation:** a few dozen pairs demonstrates the plumbing, not alignment. Models move visibly with hundreds to thousands of good pairs; the LAB's sample data is there to make the pipeline runnable on a laptop, not to produce a better model.

---

## Exercise 2: DPO Training

### Solution

```python
import torch
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer

model_name = "microsoft/Phi-3-mini-4k-instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # collation needs a pad token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    dtype=torch.bfloat16,
    device_map="auto",
)

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    task_type="CAUSAL_LM",
)

training_args = DPOConfig(
    output_dir="./dpo-output",
    beta=0.1,                       # KL-strength: higher = stay closer to reference
    learning_rate=5e-6,             # ~10x below LoRA-SFT; DPO degrades fast at high lr
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,  # effective batch 16
    num_train_epochs=3,
    warmup_ratio=0.1,
    logging_steps=10,
    save_steps=100,
    bf16=True,                      # fp16 on pre-Ampere GPUs
    gradient_checkpointing=True,
    max_length=512,                 # prompt+completion cap - filter long pairs in prep
    eval_strategy="steps",
    eval_steps=100,
)

trainer = DPOTrainer(
    model=model,
    ref_model=None,                 # PEFT path: frozen base acts as the reference
    args=training_args,
    train_dataset=split["train"],
    eval_dataset=split["test"],
    processing_class=tokenizer,     # current TRL API (was: tokenizer=...)
    peft_config=peft_config,
)

trainer.train()

trainer.save_model("./dpo-adapters")       # adapter only - megabytes
tokenizer.save_pretrained("./dpo-adapters")
```

### Reading the API (what changed vs older tutorials)

```text
- beta lives in DPOConfig. Passing beta= to DPOTrainer raises
  TypeError on current TRL.
- max_prompt_length / max_completion_length were removed from
  DPOConfig. Pre-truncate or filter overlong pairs in data prep;
  max_length caps the combined sequence.
- ref_model=None with a PEFT model: TRL disables the adapter when
  scoring the reference, so the frozen base model IS the reference.
  This is also the memory win - no second full model in VRAM.
- load_in_8bit=True on from_pretrained is deprecated; use
  quantization_config=BitsAndBytesConfig(load_in_8bit=True).
```

### Reading the metrics

TRL logs four DPO-specific series alongside the loss — judge training by these, not by loss alone:

| Metric | Meaning | Healthy trajectory |
|---|---|---|
| `rewards/accuracies` | fraction of eval pairs where chosen out-scores rejected | climbs above 0.6, plateaus 0.7-0.8 |
| `rewards/margins` | chosen-rejected reward gap | widens steadily |
| `rewards/chosen` | implicit reward of chosen vs reference | drifts (can go negative in absolute terms) |
| `rewards/rejected` | implicit reward of rejected | drifts below `rewards/chosen` |

Both rewards usually drift *down* together — the policy lowers its own log-probs while lowering rejected faster. That is expected; the margin is the signal.

---

## Exercise 3: Evaluating Alignment

### Solution: score held-out pairs with the implicit reward

DPO's trained objective is an explicit reward function — `beta * log(pi/pi_ref)` — so you can measure alignment without any external judge:

```python
import torch

@torch.no_grad()
def completion_logprob(model, tokenizer, prompt, completion):
    """Total log-probability of completion tokens given prompt."""
    ids_prompt = tokenizer(prompt, return_tensors="pt").to(model.device)
    ids_full = tokenizer(prompt + completion, return_tensors="pt").to(model.device)
    labels = ids_full["input_ids"].clone()
    labels[:, : ids_prompt["input_ids"].shape[1]] = -100  # score completion only
    out = model(**ids_full, labels=labels)
    # loss is mean over scored tokens; multiply back to a total log-prob
    return -out.loss * (labels != -100).sum()


@torch.no_grad()
def preference_accuracy(model, ref_model, tokenizer, pairs, beta=0.1):
    """Fraction of pairs where the implicit reward prefers chosen."""
    correct = 0
    for p in pairs:
        c = completion_logprob(model, tokenizer, p["prompt"], p["chosen"])
        r = completion_logprob(model, tokenizer, p["prompt"], p["rejected"])
        c_ref = completion_logprob(ref_model, tokenizer, p["prompt"], p["chosen"])
        r_ref = completion_logprob(ref_model, tokenizer, p["prompt"], p["rejected"])
        if beta * (c - c_ref) > beta * (r - r_ref):
            correct += 1
    return correct / len(pairs)
```

For the PEFT setup above, `ref_model` is the base model with adapters disabled — loading the base checkpoint a second time for evaluation is the simplest honest approximation:

```python
ref_model = AutoModelForCausalLM.from_pretrained(
    model_name, dtype=torch.bfloat16, device_map="auto"
)

acc = preference_accuracy(trainer.model, ref_model, tokenizer, split["test"])
print(f"held-out preference accuracy: {acc:.2%}")
```

### Solution: qualitative before/after

```python
test_prompts = [
    "What's the capital of France?",
    "Explain quantum computing.",
    "How do I bake a cake?",
]

def generate(model, tokenizer, prompt, max_new_tokens=128):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=0.7,
        do_sample=True,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

for prompt in test_prompts:
    print(f"PROMPT: {prompt}")
    print(f"BASE:    {generate(ref_model, tokenizer, prompt)}\n")
    print(f"DPO:     {generate(trainer.model, tokenizer, prompt)}\n---")
```

Automated accuracy plus eyeballing beats either alone: accuracy can climb while outputs get verbose or hedgy, and side-by-side comparison catches that instantly.

---

## Key Concepts

### The DPO loss, from scratch

```python
import torch
import torch.nn.functional as F

def dpo_loss(policy_chosen_logps, policy_rejected_logps,
             ref_chosen_logps, ref_rejected_logps, beta=0.1):
    """
    Each argument: tensor of summed completion log-probs (batch,).
    Reward = beta * log(pi/pi_ref); loss = -logsigmoid(reward gap).
    This is exactly what TRL's DPOTrainer computes (plus optional
    label smoothing).
    """
    chosen_rewards = beta * (policy_chosen_logps - ref_chosen_logps)
    rejected_rewards = beta * (policy_rejected_logps - ref_rejected_logps)
    return -F.logsigmoid(chosen_rewards - rejected_rewards).mean()
```

### What beta actually does

`beta` is the KL-strength in the equivalent RLHF objective (`max E[r] - beta * KL`). **Higher beta anchors the policy closer to the reference — more conservative. Lower beta lets the policy drift further — more aggressive.** (Zephyr's famous `beta=0.01` runs deliberately deviate hard from the reference.) If you only remember one knob: training unstable or outputs degenerating → raise beta or lower lr; model barely changes → lower beta or train longer.

---

## Common Issues

### CUDA out of memory

```text
- gradient_checkpointing=True (already set above)
- LoRA instead of full fine-tuning - adapter-only training is the
  single biggest saving
- ref_model=None (PEFT path) avoids loading a second full model
- 8-bit base: quantization_config=BitsAndBytesConfig(load_in_8bit=True)
- pre-truncate pairs to max_length in data prep
```

### Training unstable or outputs degrade

```text
- learning_rate 5e-6 -> 1e-6
- raise beta 0.1 -> 0.3 (stronger anchor to the reference)
- verify pad_token was set - unset pad tokens corrupt collated batches
- confirm the eval split exists: "loss went down but the model got
  worse" is invisible without eval metrics
```

### Preference accuracy stuck near 0.5

The pairs are probably indistinguishable (or the judge that built them was). Audit ten pairs by hand before touching hyperparameters — data quality dominates every other lever in DPO.

---

## References

### Related curriculum documents

- [LAB-010: DPO Alignment](../LAB-010-DPO-Alignment.md)
- [5201: DPO Theory](../../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)
- [5202: Alignment Orchestration](../../../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md)
- [5203: RLHF](../../../phases/phase5-finetuning/5200-alignment/5203-RLHF.md)
- [5204: Preference Dataset Creation](../../../phases/phase5-finetuning/5200-alignment/5204-Preference-Dataset-Creation.md)

### External

- [DPO paper: Direct Preference Optimization (Rafailov et al., 2023)](https://arxiv.org/abs/2305.18290)
- [TRL DPOTrainer documentation](https://huggingface.co/docs/trl/dpo_trainer)

---

## Next Steps

- Re-run [LAB-010](../LAB-010-DPO-Alignment.md) end-to-end with a real preference corpus (hundreds of pairs, not dozens)
- Scale the recipe: [5202: Alignment Orchestration](../../../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md)
- Compare against the two-model pipeline: [5203: RLHF](../../../phases/phase5-finetuning/5200-alignment/5203-RLHF.md)
