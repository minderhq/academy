---
Document ID: 5204
Title: "5204: Preference Dataset Creation"
Phase: 5
Module: 5200
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'alignment', 'preference']
---

# 5204: Preference Dataset Creation

## Abstract

DPO and reward models are only as good as the preference data beneath them.
This document covers the full pipeline: sourcing diverse prompts, generating
response pairs, writing annotation guidelines that survive real annotators,
formatting (HH-RLHF style), quality control with inter-annotator agreement,
dataset sizing, and bootstrapping with synthetic (AI) feedback.

---

## Table of Contents

- [1. Overview](#1-overview)
- [Learning Objectives](#learning-objectives)
- [2. What a Preference Example Is](#2-what-a-preference-example-is)
- [3. Prompt Sourcing](#3-prompt-sourcing)
- [4. Response Pair Generation](#4-response-pair-generation)
- [5. Annotation Guidelines](#5-annotation-guidelines)
- [6. Dataset Formats](#6-dataset-formats)
- [7. Quality Control](#7-quality-control)
- [8. How Much Data](#8-how-much-data)
- [9. Synthetic Preferences](#9-synthetic-preferences)
- [10. Common Pitfalls](#10-common-pitfalls)
- [Summary](#summary)
- [11. References](#11-references)

---

## 1. Overview

### 1.1 Prerequisites

- [5201: DPO Theory](./5201-DPO-Theory.md) - what consumes this data
- [5203: RLHF](./5203-RLHF.md) or equivalent - reward models
- Familiarity with the Bradley-Terry preference model

## Learning Objectives
After completing this document, you will:
- ✅ Design a prompt-sourcing strategy with real coverage and diversity
- ✅ Generate comparable response pairs (the conditions for a *meaningful* preference)
- ✅ Write annotation guidelines and measure annotator agreement
- ✅ Emit validated preference data in pairwise JSON format
- ✅ Bootstrap preferences with AI feedback while controlling its biases

---

## 2. What a Preference Example Is

One training example for DPO / reward modeling is a **triple**:

```text
(p, y_w, y_l):
  p    prompt
  y_w  chosen response   (preferred)
  y_l  rejected response (dispreferred)
```

The learning signal is the *contrast*. Two properties make the contrast
informative:
- **Comparable**: responses answer the same prompt with similar scope
- **Non-degenerate**: y_l is not obviously broken (otherwise the model
  learns to avoid a trivial failure, not to prefer good behavior)

> **⚠️ Garbage-In Rule:**
> If annotators can rank the pair without reading carefully (e.g., one
> answer is truncated, the other is not), the pair teaches length/format
> shortcuts, not quality. Filter or regenerate such pairs.

---

## 3. Prompt Sourcing

| Source | Pros | Cons |
|--------|------|------|
| Real user queries (product logs, consented) | True distribution | Privacy scrubbing required |
| Open datasets (ShareGPT, LMSYS prompts) | Free, diverse | License/outdated styles |
| LLM-generated task seeds | Fills coverage gaps | Distribution mismatch risk |
| Red-team crafted (safety, refusal) | Targets edge cases | Cost per example is high |

Practical mix for a v1 dataset: **~60% real, ~30% open-dataset, ~10%
targeted red-team prompts**. Deduplicate by near-duplicate matching
(min-hash or embedding similarity > 0.95), and track a **capability
taxonomy** (reasoning, coding, writing, safety, multilingual, ...) so
coverage gaps are visible:

```python
from collections import Counter

def coverage_report(prompts, taxonomy_fn):
    counts = Counter(taxonomy_fn(p) for p in prompts)
    total = sum(counts.values())
    return {k: f"{v} ({v/total:.1%})" for k, v in counts.most_common()}
```

---

## 4. Response Pair Generation

Generate 2 (or more) candidate responses per prompt, then label the best.
Conditions for a fair comparison:

- **Vary the source**: different models, or same model at different
  temperatures/checkpoints — same-source pairs isolate quality differences
- **Match length expectations**: sample until candidates are comparable,
  or label with length explicitly normalized (see Pitfalls)
- **Keep the prompt identical**: never paraphrase between candidates

```python
candidates = []
for model, temp in [("model-a", 0.7), ("model-b", 0.7), ("model-a", 1.0)]:
    candidates.append(generate(model, prompt, temperature=temp))
# annotate: pick best of 3 -> 3 pairwise labels (a>b, a>c, b>c if strict order)
```

Ranking 3-4 candidates and exploding into pairs multiplies labels per
annotation session — cheaper per pair than judging pairs one at a time.

---

## 5. Annotation Guidelines

A guideline document annotators actually follow has: a rubric with
**prioritized criteria**, a **tie option**, and **worked examples**.

```text
Rubric (apply in order; first decisive difference wins):
1. Harmfulness / safety violation  -> reject outright
2. Factual correctness             -> prefer the correct one
3. Instruction following           -> did it do what was asked?
4. Completeness                    -> addresses all sub-questions
5. Clarity & formatting            -> only if 1-4 tie

Tie: responses are effectively equal -> label "tie" (excluded from training)
```

**Worked example discipline**: every guideline ships with ≥10 labeled
examples *including two tricky ones* (correct-but-rude vs polite-but-wrong;
long-form vs concise). Ambiguity that is not resolved in the guideline
becomes annotator noise.

---

## 6. Dataset Formats

The dominant pairwise format (HH-RLHF style):

```json
{
  "prompt": "Explain what a mutex is to a junior developer.",
  "chosen": "A mutex is a lock that ensures only one thread ...",
  "rejected": "A mutex is like a semaphore, basically the same thing ..."
}
```

Multi-turn conversations nest the turns; the preference applies to the
final assistant turn:

```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "chosen_messages": [0, 1, 2, 3],
  "rejected_messages": [0, 1, 2, 3]
}
```

Validate on ingest — a schema check catches the most common pipeline bugs
(role order, empty strings, chosen == rejected):

```python
def validate_pair(ex):
    assert ex["chosen"].strip() and ex["rejected"].strip()
    assert ex["chosen"] != ex["rejected"]
    assert isinstance(ex["prompt"], str) and ex["prompt"].strip()
    return True
```

---

## 7. Quality Control

- **Inter-annotator agreement**: have 2-3 annotators label an overlap set;
  compute Cohen's kappa. κ < 0.4 means the guidelines are ambiguous —
  fix the rubric before scaling annotation.
- **Gold (trap) questions**: seed known-answer pairs into every session;
  annotators below ~90% on golds get retrained or their labels dropped.
- **Statistical filters**: flag pairs where chosen is always much longer,
  or rejected always from the same source model (source bias).
- **Spot audits**: human review of a random 2-5% of labels after model
  training — if the trained model's wins/losses contradict labels, audit
  the data first.

```python
from sklearn.metrics import cohen_kappa_score

kappa = cohen_kappa_score(annotator_a_labels, annotator_b_labels)
# kappa > 0.6 : substantial agreement -> proceed
# 0.4 - 0.6  : moderate -> revise guidelines
# < 0.4      : stop, guidelines are broken
```

---

## 8. How Much Data

| Target | Pair count (order of magnitude) | Notes |
|--------|--------------------------------|-------|
| DPO on one style/behavior axis | 5k - 50k | Smallest viable signal |
| Reward model for PPO | 50k - 500k | RM needs broader coverage |
| General-purpose alignment | 100k - 1M+ | Frontier-lab scale |

> **📊 Rule of Thumb:**
> More *distinct prompts* beats more labels per prompt. 50k pairs over 50k
> prompts typically outperforms 50k pairs over 10k prompts — DPO's
> contrastive loss generalizes on prompt diversity, not annotation depth.

---

## 9. Synthetic Preferences

AI feedback (RLAIF, see [5202](./5202-Alignment-Orchestration.md)) replaces
human labelers with a strong judge model, guided by written principles
(Constitutional AI style):

```python
JUDGE_TMPL = """Principle: {principle}
Question: {prompt}
Response A: {a}
Response B: {b}
Which response better follows the principle? Answer A or B, then one sentence why."""

def synth_label(judge_model, prompt, a, b, principle):
    out = judge_model(JUDGE_TMPL.format(principle=principle, prompt=prompt, a=a, b=b))
    return parse_choice(out)          # "A" -> (a, b), "B" -> (b, a)
```

**Controls that make synthetic labels usable:**
- **Position-debias**: judge each pair as (A,B) and (B,A); keep only
  consistent judgments
- **Human calibration**: measure judge-vs-human agreement on a held-out
  human-labeled set before trusting the judge at scale
- **Mix ratios**: synthetic pairs are cheapest for style/format axes;
  keep humans on safety and factual axes

---

## 10. Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Length bias | Model grows verbose after DPO | Length-normalize labels or pair-match lengths |
| Sycophancy | Model agrees with wrong user claims | Add adversarial "user is wrong" prompts |
| Source bias | RM prefers one generator's style | Rotate candidate sources per prompt |
| Truncation artifacts | Labels follow which text is cut off | Filter truncated candidates at generation |
| Guideline drift | Agreement degrades over weeks | Re-run gold set + kappa check per batch |

---

## Summary

DPO and reward models are only as good as the preference data beneath them, and this lesson is the full pipeline for making that data good: sourcing diverse prompts, generating response pairs, writing annotation guidelines that survive real annotators, and formatting in HH-RLHF style. Quality control gets its own sections - inter-annotator agreement as the metric, dataset sizing to know how much is enough, synthetic AI feedback to bootstrap when humans are the bottleneck - and the common pitfalls list collects the ways datasets silently poison alignment. The rule it leaves: annotation quality beats annotation quantity, and agreement statistics are how you know which one you have.

## 11. References

### Academic Papers
- [1] Bai et al. "Training a Helpful and Harmless Assistant with RLHF". Anthropic, 2022. (HH-RLHF dataset)
- [2] Bai et al. "Constitutional AI: Harmlessness from AI Feedback". Anthropic, 2022.
- [3] Rafailov et al. "Direct Preference Optimization: Your Language Model is Secretly a Reward Model". NeurIPS, 2023.
- [4] Bradley & Terry. "Rank Analysis of Incomplete Block Designs". Biometrika, 1952.
- [5] Zheng et al. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena". NeurIPS, 2023. (position bias)

### Datasets
- [HH-RLHF (H4)](https://huggingface.co/datasets/HuggingFaceH4/hh-rlhf-h4) - reference pairwise format

### Related Minder Academy Documents
- [5201: DPO Theory](./5201-DPO-Theory.md) - trains on this data
- [5202: Alignment Orchestration](./5202-Alignment-Orchestration.md) - pipeline integration
- [5300: Synthetic Data & Advanced Methods](../5300-synthetic/README.md) - synthetic data generation

---

## Next Steps

- Continue with: **[5201: DPO Theory](./5201-DPO-Theory.md)**
- Orchestration: **[5202: Alignment Orchestration](./5202-Alignment-Orchestration.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**

---

**Document ID:** 5204
**Status:** Complete
**Related Documents:** [5201, 5202, 5300]
