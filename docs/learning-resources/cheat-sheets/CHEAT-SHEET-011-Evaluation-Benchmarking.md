---
Document ID: CHEAT-SHEET-011
Title: "CHEAT-SHEET-011: Evaluation & Benchmarking"
Last Updated: 2026-10-15
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'evaluation', 'benchmarks']
---

# CHEAT-SHEET-011: Evaluation & Benchmarking

## Quick Reference for LLM Measurement

**Version:** 1.0

A benchmark score is only as good as the protocol that produced it. This
sheet maps the everyday benchmark set, the lm-evaluation-harness commands
that run them, and the estimator math behind pass@k — the difference
between a number you can trust and one you can't.

---

## Benchmark Map

| Benchmark | Measures | Typical protocol |
| --- | --- | --- |
| MMLU | broad knowledge, 57 subjects | 5-shot, exact match |
| HellaSwag | commonsense continuation | 10-shot, likelihood |
| GSM8K | grade-school math | 8-shot CoT, exact match |
| HumanEval | Python coding | pass@1, unit tests |
| MT-Bench / Arena | conversational quality | LLM-as-judge |
| Perplexity | raw LM health (pretraining) | corpus likelihood, lower = better |

---

## lm-evaluation-harness

```bash
# Install (uv-first policy)
uv pip install lm-eval

# Discover task names
lm_eval --tasks list

# One run: MMLU 5-shot on a small HF checkpoint, sane sample cap
lm_eval --model hf \
  --model_args pretrained=EleutherAI/pythia-160m,dtype=float32 \
  --tasks mmlu \
  --num_fewshot 5 \
  --batch_size auto \
  --limit 200 \
  --output_path out/mmlu
```

Protocol rules of thumb: pin `dtype` explicitly (a silent fp16 load can
shift scores by points); keep `--limit` fixed when comparing two models
(the same subset both times); report `--num_fewshot` next to every number
— a 0-shot and 5-shot score are different currencies.

---

## pass@k: the Estimator Behind Coding Scores

```python
from math import comb

def pass_at_k(n, c, k):
    # Codex unbiased pass@k estimator: n samples per problem,
    # c of them correct, probability that >=1 of k drawn is correct
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)

print(round(pass_at_k(n=10, c=4, k=1), 3))   # 0.4
print(round(pass_at_k(n=10, c=4, k=10), 3))  # 1.0
```

`n=1` collapses pass@1 to raw accuracy; large `k` on a fixed `n` inflates
optimistically — compare models at the same (n, k) or not at all.

---

## LLM-as-Judge

For open-ended quality (MT-Bench style): a strong model scores responses
against a rubric on a fixed scale. Rules that keep it honest:

- Pin the judge model, its prompt template, and `temperature=0` in writing.
- Blind the judge: never leak which response came from which system.
- Watch for known biases — length (longer reads better), self-preference
  (the judge favors its own family), position (first answer wins).
- Spot-check 5% of verdicts by hand; judges disagree with humans more on
  reasoning than on style.

---

## Knob Cheats

| Knob | Default practice | Why |
| --- | --- | --- |
| temperature | 0 for benchmark runs | greedy = reproducible |
| few-shot k | benchmark's canonical (MMLU 5, GSM8K 8) | changes the task difficulty |
| --limit | fixed subset when comparing | sampling noise otherwise |
| dtype | explicit in --model_args | silent precision loss |
| runs | ≥3 seeds for small models | report mean ± spread |

---

## Troubleshooting

```bash
# Score is suspiciously high vs public leaderboards
#   -> contamination: the checkpoint saw the test set in pretraining;
#      probe with a held-out / refreshed variant before publishing

# Two runs of the same config differ by points
#   -> sampling variance: set temperature=0, pin --limit, add seeds

# Coding score high but code fails in real use
#   -> benchmark overfit: HumanEval is small and public; add a
#      fresh, private task set before shipping claims

# Judge scores alternate wildly between runs
#   -> judge instability: pin temperature=0, fix the template,
#      and swap position of the two responses as a control

# Numbers drop after a config "cleanup"
#   -> dtype or chat-template drift: diff the exact --model_args
#      and tokenizer settings, not just the task list
```

---

**Quick Reference for:**

- [Module 2403: Evaluation Frameworks](../../phases/phase2-foundations/2400-pretraining/2403-Evaluation-Frameworks.md)
- [TUTORIAL-010: Model Evaluation](../tutorials/TUTORIAL-010-Model-Evaluation.md)
- [LAB-014: AI Evaluation & Safety](../labs/LAB-014-AI-Evaluation-Safety.md)
- [CHEAT-SHEET-008: Reasoning Models & Test-Time Compute](./CHEAT-SHEET-008-Reasoning-Models.md)
