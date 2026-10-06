---
Document ID: 5105
Title: "5105: Model Merging - Task Vectors, TIES, and mergekit"
Phase: 5
Module: 5100
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'peft', 'checkpoint', 'mergekit']
---

# 5105: Model Merging - Task Vectors, TIES, and mergekit

## Abstract

The [5300 assessment](../5300-synthetic/assessment/QUIZ.md) asks "What is model
merging?" and its answer key names the three canonical families — SWA, linear
merging, and task arithmetic — but no lesson anywhere in the curriculum taught
any of them. [5101](./5101-LoRA-Logic.md) uses merging as the last step (fold
the adapter, discard it) and [5103](./5103-Adapters.md) covers adapter fusion
(the learned alternative); the arithmetic of combining two full fine-tunes was
the gap. This document builds that arithmetic as working code: the task vector
as the atom of every method, the lambda dial that doses it back into the base,
TIES sign election where naive addition cancels skills, DARE's drop-and-rescale
free lunch and its exact price, SLERP's spherical geometry against the linear
chord, checkpoint soups and the same-task-only boundary that makes them work,
and the mergekit YAML surface that packages all of it.

---

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Task Vector](#the-task-vector)
- [Sign Conflicts: TIES](#sign-conflicts-ties)
- [DARE: Drop and Rescale](#dare-drop-and-rescale)
- [SLERP vs Linear Interpolation](#slerp-vs-linear-interpolation)
- [Checkpoint Soups](#checkpoint-soups)
- [The mergekit Surface](#the-mergekit-surface)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this document, you will:

- ✅ Build a task vector τ = W_finetuned − W_base and dose it with lambda
- ✅ Explain why naive weight addition destroys opposing skills, and how TIES
  trims, elects, and merges around it
- ✅ Verify DARE's expectation preservation in Monte Carlo and price its
  variance at |τ|·sqrt(p/(1−p))
- ✅ Contrast linear interpolation's chord-shrink with SLERP's fixed norm
- ✅ Average checkpoint soups and state the same-task boundary they live inside
- ✅ Read and write a mergekit YAML config, including parameter precedence

**Estimated Time:** 3 hours

---

## The Task Vector

Every merge method in this lesson is arithmetic on one object. A fine-tune
moves the base weights from W_base to W_ft; the task vector is that movement:

```text
tau = W_ft - W_base
```

Ilharco et al. (2022) framed it as model *editing*: the fine-tune did not
produce a new model, it produced a *direction* — and the direction can be
added back at any strength. The strength is the scalar lambda, and the merged
model is:

```text
W_merged = W_base + lambda * tau
```

Lambda is a dose, not a switch. The fence below builds a two-dimensional
stand-in for the operation: the base sits at [1, 1], the task's optimum at
[2, 3], and the fine-tune lands near (never exactly at) the optimum with
noise. The sweep walks lambda from 0 to 1 and prints, at each step, the loss
on the fine-tune's task and the distance from the base — the forgetting proxy.

```python
import numpy as np

w_base = np.array([1.0, 1.0])
w_star = np.array([2.0, 3.0])           # task-B optimum (the skill)
rng = np.random.default_rng(0)
noise = rng.normal(0, 0.05, size=2)     # finetune lands near, not at, w_star
w_ft = w_star + noise
tau = w_ft - w_base
print(f"w_base={w_base}  w_ft={np.round(w_ft, 4)}  tau={np.round(tau, 4)}")
for lam in (0.0, 0.25, 0.5, 0.75, 1.0):
    m = w_base + lam * tau
    loss_B = float((m - w_star) @ (m - w_star))
    dist_base = float(lam * lam * (tau @ tau))   # distance from base = forgetting proxy
    print(f"lambda={lam:<4} merged={np.round(m, 3)}  loss_B={loss_B:.3f}  dist_from_base={dist_base:.3f}")
```

The sweep is the trade in five rows. At `lambda=1.0` the merge *is* the
fine-tune — `loss_B=0.000`, but the merged point has traveled the full
`dist_from_base=4.986`, the squared length of tau, and that travel is what
catastrophic forgetting measures. At `lambda=0.25` the skill is mostly
bought (`loss_B=2.815`, down from 5.000) for a quarter of the drift
(0.312). At `lambda=0.5` both sides pay 1.253 and 1.247 — the exact
halfway point of a quadratic trade. Multi-model merging is the same dial
per model: `W_base + lambda_1 * tau_1 + lambda_2 * tau_2 + ...`, which is
mergekit's `task_arithmetic` with per-model `weight` and a global `lambda`.

---

## Sign Conflicts: TIES

Summing two task vectors coordinate-wise is the naive baseline, and it has a
failure mode no amount of lambda fixes: two skills that push the same
coordinate in opposite directions annihilate each other. Yadav et al. (2023)
called the general phenomenon *interference* and built TIES around three
steps — **T**rim, **E**lect, **M**erge:

1. **Trim**: keep the top-`density` fraction of each task vector by magnitude,
   zero the rest (fine-tunes are sparse in effect; most coordinates are noise).
2. **Elect**: per coordinate, sum the magnitude mass of the positive and
   negative survivors; the majority sign is elected and minority-sign values
   are discarded.
3. **Merge**: average the surviving agreeing values into the final vector.

The fence stages the failure honestly: two task vectors whose fourth
coordinates are +3.0 and −3.0 — two full-strength, opposite-signed skills on
the same coordinate.

```python
import numpy as np

t1 = np.array([2.0, 0.1, -1.5, 0.2, 3.0])
t2 = np.array([0.5, 0.3, -1.2, 0.1, -3.0])
naive = t1 + t2
print("tau1 =", t1)
print("tau2 =", t2)
print("naive sum =", naive, " ||naive|| =", round(float(np.linalg.norm(naive)), 3))

def ties(taus, density=0.6):
    k = max(1, int(round(density * len(taus[0]))))     # trim: keep top-k by |.|
    trimmed = []
    for t in taus:
        idx = np.argsort(-np.abs(t))[:k]
        m = np.zeros_like(t)
        m[idx] = t[idx]
        trimmed.append(m)
    mass_pos = np.sum([np.where(t > 0, np.abs(t), 0.0) for t in trimmed], axis=0)
    mass_neg = np.sum([np.where(t < 0, np.abs(t), 0.0) for t in trimmed], axis=0)
    elected = np.where(mass_pos >= mass_neg, 1.0, -1.0)  # deterministic tie-break: + wins ties
    merged = np.zeros_like(trimmed[0])
    for j in range(len(merged)):
        agree = [t[j] for t in trimmed if t[j] * elected[j] > 0]
        if agree:
            merged[j] = np.mean(agree)
    return trimmed, elected, merged

trimmed, elected, merged = ties([t1, t2])
print("trimmed1 =", trimmed[0])
print("trimmed2 =", trimmed[1])
print("elected signs =", elected)
print("ties merged =", merged, " ||ties|| =", round(float(np.linalg.norm(merged)), 3))
print("coord 4: naive =", naive[4], " ties =", merged[4])
```

Read the fourth coordinate. Naive addition prints `0.0` — the +3.0 skill and
the −3.0 skill each existed at full strength in their source models, and the
sum destroys *both*. TIES prints `3.0`: trim keeps both values (each is a
top-3 magnitude in its own vector), the election finds mass 3.0 against mass
3.0 and the implementation's `>=` resolves the tie deterministically toward
positive, the −3.0 is discarded as minority-sign, and the surviving +3.0 is
averaged — alone, so it survives at full strength. One skill preserved
deliberately beats two skills destroyed silently. Note also what the election
did elsewhere: coordinates 0 and 2 agree in sign, and TIES *means* them
(2.0 and 0.5 become 1.25; −1.5 and −1.2 become −1.35) rather than summing —
the merged update stays on the scale of one task vector, not N.

---

## DARE: Drop and Rescale

TIES trims by magnitude and elects by consensus. DARE (Yu et al., 2024) makes
a more radical claim: *most of a fine-tune's coordinates can be dropped at
random*, and if the survivors are rescaled by 1/(1−p), the expected value of
the sparsified vector equals the original:

```text
E[dare(tau, p)] = tau        for any drop rate p
```

because a coordinate survives with probability (1−p) and then reads
tau/(1−p) — the expectation is exact. The fence checks both halves of the
claim in Monte Carlo: one realization (which, at p = 0.9 over eight
coordinates, keeps a single one and rescales it 10x), then 20,000
realizations whose per-coordinate mean should recover tau.

```python
import numpy as np

tau = np.array([0.9, -0.4, 1.2, 0.3, -0.7, 0.5, -1.0, 0.2])
p = 0.9
rng = np.random.default_rng(0)
keep = rng.random(len(tau)) >= p
sample = np.where(keep, tau / (1 - p), 0.0)
print("tau          =", tau)
print("kept mask    =", keep.astype(int))
print("dare sample  =", np.round(sample, 2))

N = 20000
rng = np.random.default_rng(1)
samples = np.where(rng.random((N, len(tau))) >= p, tau / (1 - p), 0.0)
means = samples.mean(axis=0)
stds = samples.std(axis=0)
pred_std = abs(tau[0]) * np.sqrt(p / (1 - p))
print("MC means     =", np.round(means, 3), "  (tau =", tau, ")")
print(f"coord 0: mean={means[0]:.4f} vs tau={tau[0]}  std={stds[0]:.3f} vs predicted {pred_std:.3f} = |tau|*sqrt(p/(1-p))")
```

The expectation holds — every Monte Carlo mean lands on its tau (0.910
against 0.9, 1.186 against 1.2, and the rest inside sampling error), which is
why DARE merging works at drop rates as aggressive as 90%. The price is the
second print: the standard deviation of a coordinate is |tau|·sqrt(p/(1−p)),
which at p = 0.9 is **three times** the coordinate's own magnitude — the
single realization in the fence kept exactly one of eight coordinates and
inflated it to 5.0. DARE's free lunch is real on the expectation and paid in
variance; it is a bet that the *errors* of many dropped coordinates cancel
across a deep network, which they do — until the merged models' task vectors
point at genuinely different optima, where the rescaled survivors of one task
land on coordinates the other task never voted for.

---

## SLERP vs Linear Interpolation

Task arithmetic adds and TIES/DARE prune — both treat weights as a flat bag
of numbers. SLERP (spherical linear interpolation) treats two models as
*points on a hypersphere*: it walks the great-circle arc between them instead
of the straight chord. The formula for two vectors a, b separated by angle
theta:

```text
slerp(a, b, t) = sin((1-t)*theta)/sin(theta) * a  +  sin(t*theta)/sin(theta) * b
```

The geometric difference is the norm. Linear interpolation
`(1-t)*a + t*b` cuts the chord, and the chord dips inside the sphere — for
unit vectors 60 degrees apart, the midpoint's norm is cos(theta/2). The
fence prints both walks:

```python
import numpy as np

a = np.array([1.0, 0.0])
b = np.array([np.cos(np.pi / 3), np.sin(np.pi / 3)])   # 60 degrees away
theta = np.arccos(float(a @ b))
for t in (0.0, 0.25, 0.5, 0.75, 1.0):
    lin = (1 - t) * a + t * b
    slerp = (np.sin((1 - t) * theta) / np.sin(theta)) * a + (np.sin(t * theta) / np.sin(theta)) * b
    print(f"t={t:<4} |linear|={np.linalg.norm(lin):.4f}  |slerp|={np.linalg.norm(slerp):.4f}")
print(f"theta={np.degrees(theta):.0f} deg  |linear(0.5)|=cos(theta/2)={np.cos(theta/2):.4f}")
```

Linear sags to 0.8660 at the midpoint — exactly cos(30 degrees) — and
recovers at both endpoints; SLERP holds 1.0000 at every step by
construction. In weight space the sag is a systematic under-scaling of every
mid-merge: the linear midpoint of two fine-tunes applies *both* skills at
reduced magnitude, which is sometimes the desired damping and sometimes a
silent bug. This is why mergekit's `slerp` is the constrained method: a
global `t` dial where t=0 yields the `base_model` and t=1 the other model,
exactly two models, base required. For three or more ingredients the
geometry has no answer and the sparsified methods take over.

---

## Checkpoint Soups

The last family needs no arithmetic beyond the mean. A *model soup*
(Wortsman et al., 2022) averages the weights of several fine-tunes of the
**same base on the same task** — different seeds or hyperparameters — and the
average is at least as good as the typical ingredient, because independent
training noise cancels: k ingredients put the shared error down by roughly k.
SWA (Izmailov et al., 2018) is the same statistic applied to checkpoints
along one training trajectory. The fence trains sixteen same-task fine-tunes
from one base (different seeds, same optimum) and averages them; then, for
contrast, it averages two fine-tunes aimed at *different* optima:

```python
import numpy as np

def finetune(w_start, w_target, seed, steps=20, lr=0.15, sigma=0.3):
    r = np.random.default_rng(seed)
    w = w_start.copy()
    for _ in range(steps):
        grad = 2 * (w - w_target)
        w = w - lr * grad + r.normal(0, sigma, size=2)
    return w

def loss(pt, target):
    return float((pt - target) @ (pt - target))

# part 1: sixteen finetunes of the SAME base toward the SAME task, different seeds
w_base = np.array([1.0, 1.0])
w_task = np.array([2.0, 3.0])
ends = np.array([finetune(w_base, w_task, s) for s in range(16)])
ind = [loss(e, w_task) for e in ends]
soup = ends.mean(axis=0)
print("same task, 16 seeds - endpoint losses:", [round(x, 3) for x in ind])
print(f"mean individual = {np.mean(ind):.4f}   best single = {min(ind):.4f}   soup = {loss(soup, w_task):.4f}")
print(f"soup beats the AVERAGE ingredient by {np.mean(ind) / loss(soup, w_task):.1f}x - the guarantee is vs the mean, not the best")

# part 2: two finetunes toward DIFFERENT tasks - plain averaging is destructive
w_a, w_b = np.array([2.0, 3.0]), np.array([3.5, 2.0])
end_a = finetune(w_base, w_a, seed=10)
end_b = finetune(w_base, w_b, seed=11)
mid = (end_a + end_b) / 2
print(f"diff tasks - A loss={loss(end_a, w_a):.4f}  B loss={loss(end_b, w_b):.4f}  midpoint on A={loss(mid, w_a):.4f}  on B={loss(mid, w_b):.4f}")
```

Part 1 is the variance-reduction beat: sixteen ingredients scatter between
0.014 and 0.800 (mean 0.2715) and the soup lands at 0.0222 — **12.2x** better
than the average ingredient. The print also refuses the stronger claim: the
best single ingredient (0.0143) *beat* this soup. On a quadratic bowl that is
structural, not luck — averaging drives the shared error down by k while the
best of k draws is also improving with k, and "the soup beats every
ingredient" in the paper's results comes from flat high-dimensional basins
plus greedy ingredient selection, geometry this two-dimensional bowl cannot
reproduce. The guarantee you own is against the mean. Part 2 is the boundary:
averaging two *different-task* fine-tunes produces a midpoint that is bad for
both (1.0467 on A's optimum, 0.6103 on B's, against 0.0573 and 0.0181 for the
ingredients) — the midpoint sits halfway between two optima, which is nowhere.
Same-task ingredients average; cross-task skills need the task-vector
methods from the first half of this lesson.

---

## The mergekit Surface

[mergekit](https://github.com/arcee-ai/mergekit) is the toolchain that
packages all five methods behind one YAML dialect. A merge is a config file,
and the fence below is the lesson's own TIES-plus-DARE experiment written in
it — `dare_ties`, DARE's random drop replacing TIES' magnitude trim while
keeping the sign election:

```yaml
models:
  - model: org/base-model
    # the base contributes no task vector - no parameters block
  - model: org/ft-coder
    parameters:
      density: 0.6
      weight: 1.0
  - model: org/ft-math
    parameters:
      density: 0.6
      weight: 1.0
merge_method: dare_ties
base_model: org/base-model
parameters:
  lambda: 0.9
dtype: bfloat16
```

```text
mergekit-yaml config.yml ./out-merged --lazy-unpickle
```

The knobs map one-to-one onto this lesson's fences: per-model `density` is
TIES/DARE's trim-and-drop fraction ("fraction of weights to retain in each
sparsified task vector" for `ties`, "after random pruning" for the `dare_*`
family), per-model `weight` is the lambda dial inside `task_arithmetic` and
`linear`, and the global `lambda` scales the summed task vectors before they
return to the base. The full method list — `linear`, `slerp`,
`task_arithmetic`, `ties`, `dare_linear`, `dare_ties`, `della`, `breadcrumbs`,
`nuslerp`, `model_stock`, and the rest — hangs off the same schema, with
`base_model` required for every task-vector method (the vector needs its
origin) and for `slerp` (which anchors t=0 there). Two reading rules for any
config you find in the wild:

- **Parameter precedence is slice-level-wins**: `slices.*.sources.parameters`
  over `slices.*.parameters` over `models.*.parameters` over top-level
  `parameters`. A global `lambda` is silently overridden by any per-model
  block that names it.
- **`dtype`/`out_dtype` control the arithmetic, not just storage**: merging in
  `bfloat16` sums task vectors at 8 bits of mantissa; for the small values a
  lambda-dialed merge produces, that rounding is part of the result.

The implementation runs on CPU or a single ≥8 GB GPU out of core — models
stream layer by layer, so a merge never needs the full fleet resident. For
LoRA-trained work the companion command `mergekit-extract-lora` goes the
other way, distilling a full fine-tune's delta back into adapter form; the
[TEMPLATE-011](../../../learning-resources/projects/templates/TEMPLATE-011-Model-Merging-MoE.md)
project template scaffolds the whole pipeline.

---

## Known Failure Modes

| # | Symptom | Root Cause | Fix |
|---|---------|------------|-----|
| 1 | "SWA" read as Sliding Window Attention in a merging context | Same acronym, two concepts: in weight-space work SWA means Stochastic Weight Averaging — checkpoint averaging along one trajectory (Izmailov et al., 2018); [3402](../../phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md)'s SWA is a long-context attention pattern | Check the section's object of study — weights vs attention masks |
| 2 | A coordinate's skill vanishes after `task_arithmetic` with equal-strength models | Opposite-sign task-vector coordinates annihilate under addition (+3.0 and −3.0 sum to 0.0) | Switch to `ties`/`dare_ties` — sign election keeps the majority skill instead of letting both cancel |
| 3 | TIES result differs from a hand re-computation on symmetric inputs | Equal positive/negative mass is a tie; the election's tie-break is implementation-defined (this lesson's `>=` elects positive, mergekit's argmax elects first) | Never build on a tie; perturb the inputs or the `density` so the election has a majority |
| 4 | `density: 0.6` interpreted as an absolute budget shared across models | `density` is a per-model fraction of that model's own task vector — 0.6 of 5 coordinates is 3, 0.6 of 7B parameters is 4.2B kept per model | Read it as "keep top 60% by magnitude (or keep under DARE) in each vector separately" |
| 5 | DARE merge degrades at high drop rates on genuinely different tasks | E[dare(tau)] = tau holds per vector, but rescaling by 1/(1−p) multiplies variance by p/(1−p) — 9x at p=0.9 — and cross-task coordinates do not share the target the expectation averages toward | Keep p moderate (0.5–0.9) for same-base merges; drop the rate as task distance grows |
| 6 | `slerp` config with three models or a missing `base_model` rejected | SLERP is defined on an arc between exactly two points; t=0 anchors at `base_model`, t=1 at the other model | For N > 2 use `linear`/`ties`/`dare_*`; keep `slerp` to two-model, base-anchored blends |
| 7 | A soup underperforms the single best ingredient and the merge is blamed | The soup guarantee is variance reduction against the *average* ingredient (12.2x here); the best single draw can still win on a sharp bowl | Judge soups on held-out accuracy across ingredients, not against the max of one run; use greedy selection when the best-ingredient gap matters |
| 8 | Plain averaging of two task fine-tunes produces a model good at neither | The midpoint of two different optima is between optima — midpoint loss 1.0467/0.6103 vs 0.0573/0.0181 here | Average only same-task ingredients; combine cross-task skills as task vectors (`task_arithmetic`/`ties`/`dare_ties`) |

---

## Summary

- **The task vector is the atom**: every method here is arithmetic on
  τ = W_ft − W_base — dose it (`lambda`), sum it (`task_arithmetic`), prune
  and elect it (`ties`), drop and rescale it (`dare_*`), or walk arcs between
  the models it lives in (`slerp`).
- **Naive addition has a failure mode**: opposite-sign coordinates annihilate
  full-strength skills silently (the +3.0/−3.0 coordinate reading 0.0); TIES
  trim-elect-merge preserves the majority skill deliberately.
- **DARE's expectation is exact and its price is variance**: Monte Carlo
  means land on tau while coordinate std runs at |τ|·sqrt(p/(1−p)) — 3x the
  signal at p = 0.9.
- **Geometry divides the methods**: linear interpolation cuts the chord and
  sags to cos(θ/2) at the midpoint; SLERP holds the norm but only ever
  connects two models.
- **Soups are the same-task statistic**: 16 same-task ingredients averaged
  12.2x better than the typical ingredient — and the fence is explicit that
  the best single ingredient can still win; across tasks, averaging is
  destruction (1.0467/0.6103 vs 0.0573/0.0181) and task vectors are the tool.
- **mergekit is the packaging**: one YAML dialect, per-model `density`/
  `weight`, global `lambda`, slice-level parameter precedence, CPU-or-8GB
  out-of-core execution, `mergekit-extract-lora` for the reverse trip.

---

## References

### Related Minder Academy Documents

- [5101: LoRA Logic](./5101-LoRA-Logic.md) — the merge-and-discard path this
  lesson slows down: what folding an adapter into base weights actually does
- [5103: Adapters & Parameter-Efficient Adaptation Methods](./5103-Adapters.md)
  — adapter fusion, the learned routing alternative to weight merging
- [5301: Knowledge Distillation](../5300-synthetic/5301-Knowledge-Distillation.md)
  — combining model *knowledge* through outputs instead of weights
- [5405: FSDP2 and torchao](../5400-distributed-training/5405-FSDP2-and-torchao.md)
  — where sharded training checkpoints come from and what merging must read
- [TEMPLATE-011: Model Merging & MoE](../../../learning-resources/projects/templates/TEMPLATE-011-Model-Merging-MoE.md)
  — the project scaffold that operationalizes this lesson's configs
- [5300 QUIZ](../5300-synthetic/assessment/QUIZ.md) — questions 4, 5, and 18,
  whose checkpoint-merging coverage this lesson supplies

### Primary Sources

- Ilharco et al., "Editing Models with Task Arithmetic", ICLR 2023 — the task
  vector framing and the lambda dose
- Yadav et al., "TIES-Merging: Resolving Interference When Merging Models",
  NeurIPS 2023 — trim, elect, merge; the interference taxonomy
- Yu et al., "Language Models are Super Mario: Absorbing Arbitrary Skills
  from Model Merging", ICLR 2024 — DARE's drop-and-rescale and its
  90%-drop claim
- Wortsman et al., "Model soups: averaging weights of multiple fine-tuned
  models improves accuracy without increasing inference time", ICML 2022 —
  uniform and greedy soups
- Izmailov et al., "Averaging Weights Leads to Wider Optima and Better
  Generalization", UACL 2018 — SWA, the trajectory-checkpoint ancestor
- [mergekit](https://github.com/arcee-ai/mergekit) (LGPL-3.0-only) and its
  `docs/merge_methods.md` — the YAML schema, parameter precedence, and the
  method table this lesson's config fence uses

---

## Next Steps

- **Next Module**: [5200: LLM Alignment](../5200-alignment/README.md) — where
  the fine-tunes worth merging are made (DPO, RLHF, GRPO)
- **Continue with**: [5201: DPO Theory](../5200-alignment/5201-DPO-Theory.md)
- **Assessment**: [5100 QUIZ](./assessment/QUIZ.md) — and revisit the
  [5300 QUIZ](../5300-synthetic/assessment/QUIZ.md) merging questions (4, 5,
  18) after this lesson; they are now in-range
- **Hands-on**: [TEMPLATE-011](../../../learning-resources/projects/templates/TEMPLATE-011-Model-Merging-MoE.md)
  — run a real two-model merge end to end with the config dialect above
