---
Document ID: CHEAT-SHEET-010
Title: "CHEAT-SHEET-010: Alignment Methods — DPO, RLHF & GRPO"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'alignment', 'dpo', 'rlhf', 'grpo']
---

# CHEAT-SHEET-010: Alignment Methods — DPO, RLHF & GRPO

## Quick Reference for Preference Optimization

**Version:** 1.0

Alignment turns a pretrained (or SFT-tuned) model into one that behaves the
way humans prefer. Three optimizer families dominate practice: **RLHF**
(preferences → learned reward model → PPO), **DPO** (preferences straight
into a supervised loss, no reward model), and **GRPO** (verifiable rewards
from group-relative advantages — the RLVR recipe behind reasoning training).

---

## Method Map

| Method | Signal | Extra models | Online sampling | Reach for it when |
| --- | --- | --- | --- | --- |
| SFT | demonstrations | — | no | you have gold outputs; always the base stage |
| RLHF (PPO) | learned reward model | RM + policy | yes | fuzzy preference quality matters and you can afford 4 models |
| DPO | pairwise preferences | frozen reference copy | no | you have `chosen/rejected` pairs and want one training job |
| GRPO | verifiable reward (RLVR) | none (ref optional) | yes | correctness is checkable (math, code, format) |

---

## Preference Dataset

```bash
# TRL DPOTrainer expects plain-text prompt/chosen/rejected columns
head -1 pairs.jsonl
# {"prompt": "Explain KV cache briefly.", "chosen": "It stores ...", "rejected": "A cache ..."}
```

Pair hygiene (see module 5204): chosen/rejected must differ in *quality*,
not just length; deduplicate prompts; keep a held-out eval split before
training starts.

---

## DPO: the Loss Core

```python
import torch

def dpo_loss(pi_c, pi_r, ref_c, ref_r, beta=0.1):
    # each input is the summed log-prob of one full response:
    # pi_* under the policy being trained, ref_* under the frozen
    # reference. The implicit reward is beta * log(pi/ref).
    logits = beta * ((pi_c - ref_c) - (pi_r - ref_r))
    return -torch.nn.functional.logsigmoid(logits).mean()

loss = dpo_loss(pi_c=-18.0, pi_r=-25.0, ref_c=-20.0, ref_r=-26.0)
print(round(loss.item(), 4))
```

Trainer-side (module 5201's API): `from trl import DPOConfig, DPOTrainer`;
`DPOConfig(beta=0.1, max_length=512)` carries the knobs, the dataset keeps
the plain-text columns, and under LoRA pass `ref_model=None` so the
reference pass just disables the adapters instead of loading a second copy.

```bash
# Install (uv-first policy)
uv pip install trl peft
```

---

## GRPO: Verifiable Rewards

```python
def exact_match_reward(completions, ground_truth, **kwargs):
    # GRPO-style verifiable reward: +1.0 exact match, else 0.0
    return [1.0 if c.strip() == g else 0.0
            for c, g in zip(completions, ground_truth)]

rewards = exact_match_reward(
    completions=[" 42 ", "41", "the result is 42"],
    ground_truth=["42", "42", "42"])
print(rewards)
```

Trainer-side (module 5205's API): `from trl import GRPOConfig, GRPOTrainer`;
each prompt produces `G` completions that are rewarded, then advantage is
computed against the group mean.

| Knob | Typical | Note |
| --- | --- | --- |
| `num_generations` (G) | 8 | effective batch must be a multiple of G |
| `max_completion_length` | 1024 | completions pile up at the ceiling when the reward is degenerate |
| `beta` | 0.001–0.04 | KL pull toward the reference; lower = more aggressive |
| `use_vllm` | `True` | generation dominates wall clock; worth it past experiment scale |

---

## RLHF in Three Stages (when DPO is not enough)

1. **SFT** — supervised warm start.
2. **Reward model** — pairwise human preferences, Bradley-Terry loss,
   `AutoModelForSequenceClassification` with a scalar head (module 5203).
3. **PPO** — optimize the policy against the RM with a KL penalty;
   four models in memory, online rollouts, hyperparameter-sensitive.

DPO replaces stages 2–3 with one closed-form loss; GRPO replaces the
learned RM with a program. Both keep stage 1.

---

## Knob Cheats

| Knob | DPO | RLHF/PPO | GRPO |
| --- | --- | --- | --- |
| β / KL strength | `beta` 0.1 typical | `kl_coef` tuned live | `beta` 0.001–0.04 |
| Extra models | frozen ref | RM + value + ref | none |
| Data | `chosen/rejected` pairs | preference pairs + prompts | prompts + verifier |
| Failure smell | loss → 0 while eval flat | reward climbs, quality drops | all group rewards equal |

---

## Troubleshooting

```bash
# DPO loss collapses toward 0 fast but eval quality flat
#   -> overfit to easy pairs; raise beta, mix in fresh pairs, cap epochs

# Reward climbs while human quality drops (RLHF)
#   -> classic reward hacking: strengthen the KL coefficient, ensemble
#      the reward model, refresh preference data

# GRPO group gives all-identical rewards -> zero advantage, no gradient
#   -> verifier too strict or prompts too easy/hard; widen the pass
#      band (partial credit) or rebalance the prompt mix

# Completions pile up at max_completion_length
#   -> degenerate length bias: penalize padding/format, or the reward
#      ignores brevity entirely

# Aligned model forgot base skills
#   -> alignment tax: lower beta, fewer epochs, or replay SFT data
#      alongside the preference batches
```

---

**Quick Reference for:**

- [Module 5201: DPO Theory](../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)
- [Module 5203: RLHF](../../phases/phase5-finetuning/5200-alignment/5203-RLHF.md)
- [Module 5205: GRPO & RLVR](../../phases/phase5-finetuning/5200-alignment/5205-GRPO-RLVR.md)
- [Module 5204: Preference Dataset Creation](../../phases/phase5-finetuning/5200-alignment/5204-Preference-Dataset-Creation.md)
