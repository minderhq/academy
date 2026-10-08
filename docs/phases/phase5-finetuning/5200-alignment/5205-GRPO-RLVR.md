---
Document ID: 5205
Title: "5205: GRPO and Reinforcement Learning from Verifiable Rewards"
Phase: 5
Module: 5200
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'alignment', 'grpo', 'rlhf', 'reasoning']
---

# 5205: GRPO and Reinforcement Learning from Verifiable Rewards

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [From Preferences to Verifiable Rewards](#from-preferences-to-verifiable-rewards)
- [The GRPO Algorithm](#the-grpo-algorithm)
- [Hands-On: GRPO with TRL](#hands-on-grpo-with-trl)
- [The DAPO Refinements](#the-dapo-refinements)
- [GRPO vs PPO vs DPO](#grpo-vs-ppo-vs-dpo)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain why verifiable rewards replace the learned reward model for reasoning tasks
- Derive the group-relative advantage and show why it eliminates the value function
- Write rule-based reward functions with TRL's reward-function contract
- Configure GRPOTrainer: group size, completion length, KL coefficient, and the vLLM rollout backend
- Diagnose prompt saturation, entropy collapse, and verifier-gaming from training logs
- Place the DAPO recipe's deltas (clip-higher, token-level loss, overlong punishment) on the base algorithm

---

## Abstract

GRPO (Group Relative Policy Optimization) is the reinforcement learning algorithm behind DeepSeek-R1, and the reason a reasoning model can be trained without a learned reward model or a critic network. Introduced in the DeepSeekMath paper and popularized by R1, GRPO replaces PPO's learned value baseline with a cheaper one: sample a *group* of G completions for each prompt, score them, and measure each completion's advantage relative to its own group's mean. Combined with RLVR (Reinforcement Learning from Verifiable Rewards) — reward functions that check answers programmatically instead of imitating human judgments — this collapses RLHF's four-model pipeline down to one or two models. This lesson builds the algorithm from that baseline idea, implements verifiable reward functions against TRL's live contract, runs a minimal GRPO stage, and covers the DAPO refinements that modern recipes layer on top. It is the on-policy sequel to [5203: RLHF](./5203-RLHF.md): PPO has left TRL's stable surface, and GRPO is what took its place.

## From Preferences to Verifiable Rewards

RLHF's costly ingredient is the learned reward model: an imperfect proxy trained on expensive human preference pairs, which the policy then games ([5203](./5203-RLHF.md)'s reward hacking section). For reasoning-shaped tasks there is a way out — many domains ship their own ground truth:

```text
Verifiable domains              Checker
- Math word problems            final-answer match (equivalence-aware)
- Code                          unit tests pass / compiles / runtime
- Structured output             schema validation, parseable JSON
- Tool use                      correct function called with valid args
- Constraint following          length limits, format tags present
```

A **verifiable reward** is computed by a program, not predicted by a network:

```text
Learned RM (RLHF)               Verifiable reward (RLVR)
- cost: human preference pairs  - cost: a test suite
- imperfect proxy -> gameable   - ground truth, not a proxy
- saturates with label budget   - scales with task generation
- one scalar for "good"         - decomposable (accuracy + format)
```

This is the DeepSeek-R1 recipe: R1-Zero applied RL *directly to the base model* with only rule-based rewards (answer accuracy plus a format reward for `<think>` tags) and watched reasoning emerge — long chains of thought, self-correction, "aha moments" — with no SFT stage and no reward model. The honest caveats from the same paper: R1-Zero's outputs drift into poor readability and mixed languages, which is why production R1 re-introduces a small cold-start SFT before the RL stage. RLVR trades the reward model's gaming problem for a new one — *verifier bugs* — covered in Known Failure Modes.

## The GRPO Algorithm

### The Baseline Problem

Policy-gradient methods need a baseline: raw rewards have huge variance across prompts (an easy problem and an impossible one both land in the same batch), and subtracting *something* from each reward is what makes gradients informative. PPO learns that baseline with a critic network — a second model with a value head, trained alongside the policy. GRPO's move: **the group is the baseline**.

```text
For each prompt x:
  1. Sample G completions  y_1..y_G  from the current policy
  2. Score each with the (verifiable) reward:  r_1..r_G
  3. Group-relative advantage:
        A_i = ( r_i - mean(r) ) / ( std(r) + eps )
  4. Policy-gradient update on A_i, with PPO-style clipping
```

No value head, no critic training loop, no advantage estimator to tune. The statistical price: each prompt must be sampled G times per step, so generation dominates wall-clock — the reason every serious GRPO setup attaches a fast rollout backend (vLLM) to the trainer.

### The Advantage, Computed

```python
import torch

# One prompt, G=8 sampled completions, scored by a verifiable checker
rewards = torch.tensor([0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0])

# GRPO advantage: the group IS the baseline - no critic, no value head
advantage = (rewards - rewards.mean()) / (rewards.std() + 1e-4)
print(advantage.round(decimals=3))

# Saturation: a prompt every completion solves (or every completion
# fails) carries zero signal - whitening zeroes all G advantages
saturated = torch.ones(8)
print(((saturated - saturated.mean()) / (saturated.std() + 1e-4)))
```

The zero-variance case in the second block is not an edge case — it is the central operational fact of RLVR training. A batch where every completion receives the same reward produces *no gradient at all*. As the policy improves, more and more prompts saturate, and effective batch size silently shrinks. Monitoring the fraction of zero-variance groups (and filtering saturated prompts, as DAPO's Dynamic Sampling does) is the difference between a healthy run and a plateau that looks like a learning-rate problem.

### The Clipped Objective and the KL Question

The update reuses PPO's clipped importance ratio ([5203](./5203-RLHF.md)'s PPO section), with one family difference: the importance sampling level — whether the ratio is formed per-token or per-sequence — is an exposed knob (`importance_sampling_level` in TRL), and recipes disagree about it.

```text
L = E[ min( ratio * A,  clip(ratio, 1-eps, 1+eps) * A ) ]

ratio = pi_theta(y|s) / pi_old(y|s)   per the chosen sampling level
eps = 0.2 (base)   eps_high = 0.28 (DAPO clip-higher, below)
```

The KL penalty against a frozen reference — RLHF's drift constraint — becomes a *choice* in GRPO:

- The original GRPO keeps it (`beta > 0`, an unbiased k3 estimator over the reference log-probs; DeepSeek-R1 used `beta = 0.001`).
- Modern recipes increasingly run `beta = 0.0` (DAPO's published setting): with a verifiable reward there is no learned proxy to protect from drift, and dropping the reference model saves its forward pass and its memory.

The decision rule: if your reward is a learned RM, keep the KL anchor (drift is how reward hacking begins). If your reward is a checker, you can drop it — drift shows up as falling checker scores, which the reward itself reports.

## Hands-On: GRPO with TRL

Unlike PPO — which 5203 recorded as demoted to `trl.experimental` — GRPO is on TRL's stable surface: `GRPOTrainer` and `GRPOConfig` import from the package root, the trainer ships in every release, and the R1-style reasoning recipes in TRL's own documentation are GRPO configurations. This is the on-policy trainer the corpus recommends.

### The Verifiable Reward Functions

TRL's reward-function contract: a callable that receives the batch's completions plus the dataset's extra columns as keyword arguments, and returns one float per completion. Multiple reward functions are summed.

```python
import re

def normalize(text):
    # demo-grade canonicalization; real checkers compare math
    # equivalence (sympy) or execute unit tests, not strings
    return text.strip().replace(" ", "").lower()

def accuracy_reward(completions, answer, **kwargs):
    # the dataset's `answer` column arrives as a kwarg, aligned
    # with the batch - that is how gold truth threads through TRL
    scores = []
    for completion, gold in zip(completions, answer):
        text = completion[0]["content"]        # conversational format
        match = re.search(r"\\boxed\{([^}]+)\}", text)
        if match is None:
            scores.append(0.0)                 # nothing extractable
            continue
        scores.append(
            1.0 if normalize(match.group(1)) == normalize(gold) else 0.0
        )
    return scores

def format_reward(completions, **kwargs):
    # R1's second rule: the reasoning trace must close its think tag
    return [0.5 if "</think>" in c[0]["content"] else 0.0
            for c in completions]
```

Two design points worth internalizing. First, **decompose the reward**: accuracy and format are separate functions with separate weights, so their curves log separately and a format hack cannot hide inside an accuracy score. Second, **extraction is part of the reward**: a completion that solves the problem but forgets the `\boxed{}` wrapper earns zero, which is correct behavior for the checker but trains the model to care about your format — so keep the format reward's weight small enough that it shapes, not dominates.

### The Dataset

Each row carries the prompt and every column your reward functions consume:

```json
{
  "prompt": [
    {"role": "user", "content": "Compute the integral of 3x^2 from 0 to 2."}
  ],
  "answer": "8"
}
```

The `prompt` column can be a raw string or this conversational messages form; with conversational data, completions arrive at the reward functions as message lists (`completion[0]["content"]`).

### The Training Run

```python
from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer

dataset = load_dataset("json", data_files="prompts.jsonl")["train"]
# columns: prompt (messages), answer (gold, passed to reward fns)

config = GRPOConfig(
    output_dir="grpo-ckpt",
    learning_rate=1e-6,        # PPO-era habit; Open-R1's 7B recipe
                               # runs 4e-5 - sweep this per model
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,
    num_generations=8,         # G: completions per prompt; the
                               # effective batch must divide by G
    max_completion_length=1024,
    beta=0.0,                  # DAPO's setting; R1 used 0.001 -
                               # add the reference back if outputs drift
    use_vllm=True,             # generation dominates wall clock;
                               # omit for a small single-GPU run
)

trainer = GRPOTrainer(
    model="Qwen/Qwen3-0.6B",   # ungated, Apache-2.0
    reward_funcs=[accuracy_reward, format_reward],
    args=config,
    train_dataset=dataset,
)
trainer.train()
```

The batch arithmetic is the most common first-run failure: the effective batch (per-device size × gradient accumulation × world size) must be a multiple of `num_generations`, because each prompt's G completions are sampled and trained together. `use_vllm=True` attaches a vLLM rollout backend (in-process colocate mode by default in recent TRL) and is worth the setup cost for any run longer than an experiment.

### What to Watch in the Logs

```text
1. reward mean per source   -> climbing: the stage is learning
2. reward std per group     -> shrinking toward 0 = saturation;
                               filter or refresh your prompt set
3. accuracy vs format rate  -> separately; a rising format rate
                               with flat accuracy is a format hack
4. completion length        -> monotonic growth = length hack
                               (see DAPO's overlong punishment)
5. KL vs reference          -> only when beta > 0; spiking = drift
```

## The DAPO Refinements

DAPO (Decoupled Clip and Dynamic sAmpling Policy Optimization — ByteDance Seed's open-source reasoning-RL recipe) is GRPO with four published deltas, all exposed as TRL configuration:

```text
1. Clip-Higher        epsilon_high = 0.28 > epsilon = 0.2
                      asymmetric clipping keeps low-probability
                      (exploratory) tokens improvable longer

2. Dynamic Sampling   oversample prompts, train only on groups
                      with reward variance (NOT supported in TRL -
                      filter your prompt set upstream instead)

3. Token-Level Loss   loss_type="dapo": normalize gradients by
                      total tokens, not per-sequence - long chains
                      stop being under-weighted

4. Overlong Punishment  a soft penalty shaping completions away
                      from the length ceiling instead of a hard
                      truncation cliff (TRL: get_soft_overlong_punishment)
```

Treat these as named knobs to reach for when the base run shows the specific symptom — not as defaults to apply blindly. Clip-higher helps when entropy collapses early; token-level loss matters when your completions have high length variance; the overlong punishment matters when the task rewards long reasoning.

## GRPO vs PPO vs DPO

| Dimension | GRPO + RLVR | PPO + RM ([5203](./5203-RLHF.md)) | DPO ([5201](./5201-DPO-Theory.md)) |
|---|---|---|---|
| Models in memory | 1x (beta=0) to 2x (policy + ref) | 4x: policy + ref + critic + RM | 2x: policy + ref |
| Reward source | Programmatic checker | Learned reward model | Implicit from preference pairs |
| Sampling during training | Online: G completions per prompt | Online: 1 completion per prompt | None — offline dataset |
| Value function | None — group is the baseline | Learned critic | None |
| Reward ceiling | The checker's fidelity | Human judgment (imperfect proxy) | Preference data quality |
| TRL surface | Stable: `GRPOTrainer` | Experimental: `trl.experimental.ppo` | Stable: `DPOTrainer` |
| Best at | Reasoning, code, verifiable formats | General "helpfulness" alignment | Bulk offline alignment |
| Signature failure | Verifier gaming, saturation | Reward hacking, KL blowup | Preference overfitting |

Decision heuristic:

```text
Use GRPO + RLVR when:
- Your task has programmatically checkable outcomes
- You can generate prompts at scale (saturation is coming)
- You want on-policy improvement past what SFT/DPO reach

Use PPO + RM when:
- The quality you want is real but NOT mechanically checkable
  (tone, style, nuance) and you already run a reward model

Use DPO when:
- You have preference pairs and want the cheap offline pass
  (which is also the standard first stage before any RL)
```

The production sequence for a reasoning model has stabilized around: SFT -> (optional DPO pass) -> GRPO/RLVR stage with rule-based rewards -> SFT-style polish. [5203](./5203-RLHF.md)'s "DPO for the bulk, short RLHF stage last" pattern survives, with GRPO replacing PPO in the final slot.

## Known Failure Modes

```text
1. Verifier bug (false negatives)
   Symptom: reward stays near 0; completions look correct by eye
   Fix:     audit the checker on a sample of completions; fix
            extraction and equivalence before touching the policy

2. Verifier gaming (false positives)
   Symptom: reward climbs; spot-checked completions are degenerate
   Fix:     harden the checker (unit tests > string match); add
            format constraints as a separate small reward

3. Prompt saturation
   Symptom: fraction of zero-variance groups climbs; reward flat
   Fix:     filter saturated prompts; oversample hard prompts;
            generate fresh prompts (DAPO Dynamic Sampling, upstream)

4. Entropy collapse
   Symptom: completions converge to one template early in training
   Fix:     clip-higher (epsilon_high), lower lr, entropy bonus

5. Length explosion
   Symptom: mean completion length grows monotonically; truncated
            completions pile up at max_completion_length
   Fix:     overlong punishment reward; cap and mask truncated
            completions (mask_truncated_completions)

6. Format domination
   Symptom: format reward rate near 1.0, accuracy flat
   Fix:     shrink the format weight; merge it into accuracy as a
            gate, not an additive term
```

---

## Summary

GRPO replaces PPO's learned critic with the cheapest baseline available — the mean of a group of same-prompt completions — and RLVR replaces the learned reward model with a programmatic checker. Together they are the recipe that trained DeepSeek-R1: one or two models in memory, reasoning emerging from rule-based rewards alone, and the failure surface shifted from reward hacking toward verifier bugs and prompt saturation. This lesson built the group-relative advantage from its definition, implemented TRL's reward-function contract against live API surfaces, configured a GRPO stage end-to-end on an ungated Qwen checkpoint, and placed the DAPO refinements as symptom-driven deltas. The operational core is the zero-variance group: saturation is RLVR's version of RLHF's reward hacking — the failure mode that tells you the environment, not the algorithm, needs work.

## References

### Related Minder Academy Documents

- [5201: DPO (Direct Preference Optimization) Theory](5201-DPO-Theory.md)
- [5202: Alignment Orchestration - Reward Modeling vs Direct Preference](5202-Alignment-Orchestration.md)
- [5203: Reinforcement Learning from Human Feedback](5203-RLHF.md)
- [5204: Preference Dataset Creation](5204-Preference-Dataset-Creation.md)

---

## Next Steps

- Continue with: **[5204: Preference Dataset Creation](./5204-Preference-Dataset-Creation.md)** for the data layer beneath a cold-start SFT stage
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
