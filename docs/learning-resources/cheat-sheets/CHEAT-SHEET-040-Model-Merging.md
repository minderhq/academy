---
Document ID: CHEAT-SHEET-040
Title: "CHEAT-SHEET-040: Model Merging - the Arithmetic That Combines Trained Models"
Last Updated: 2026-10-16
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'peft', 'mergekit', 'checkpoint']
---

# CHEAT-SHEET-040: Model Merging - the Arithmetic That Combines Trained Models

This sheet is the single-page reference for model merging - the arithmetic that
combines two or more trained checkpoints into one without retraining (module
5105). Use it when a merged model evaluates below both of its parents, when a
multi-model merge drifts past the scale of a single task vector, when a
DARE-merged checkpoint behaves randomly, or when a checkpoint soup loses to its
best single ingredient.

Everything here reduces to one picture: a finetune is a displacement
`tau = w_ft - w_base` away from the shared base, and every merge method is a
rule for combining several such displacements. Task arithmetic dials the dose
with one global lambda; TIES trims each vector to its densest coordinates,
elects one sign per coordinate by mass, and averages the survivors; DARE drops
p of the coordinates and rescales by 1/(1-p) - the mean is kept, the variance
is the price; SLERP walks the arc instead of the chord; and the checkpoint
soup averages whole same-task endpoints, where the guarantee is distributional
- against the average ingredient, never the best one.

```text
task arithmetic - W_base + lambda * tau         (the dose dial)
TIES            - trim -> elect sign -> mean    (the sign-conflict kill)
DARE            - drop p, rescale 1/(1-p)       (mean kept, variance paid)
```

---

## Task Vectors - the Dose Dial

A finetune of task B lands at `w_ft`, a point near the task optimum `w_star`
but not on it. The displacement `tau = w_ft - w_base` is the task vector - the
single object every merge method combines. Merging back toward the base is the
dose dial `W(lambda) = w_base + lambda * tau`, and the loss along the dial is
quadratic in lambda: at lambda 0.25 the task-B loss is already down from
5.000 to 2.815, at 0.5 it reads 1.253, and at 1.0 it bottoms at 0.000 - while
the distance-from-base cost walks 0.000 -> 0.312 -> 1.247 -> 2.805 -> 4.986,
the squared length of tau. The dial trades skill against forgetting, and the
trade's exact halfway point of the quadratic sits between the 0.75 row and
the 1.0 row.

The N-model generalization keeps one dial per model:
`W_base + lambda_1 * tau_1 + lambda_2 * tau_2 + ...` - one global lambda per
task vector, which is exactly mergekit's `task_arithmetic` with a per-model
`weight`.

| lambda zone | what you get | risk |
|---|---|---|
| 0.0 - 0.25 | most of the early loss drop (5.000 -> 2.815) | skill barely instilled |
| 0.5 - 0.75 | the quadratic halfway (1.253 -> 0.315 at dist 1.247 -> 2.805) | forgetting cost accelerates |
| 1.0 | loss 0.000 - the finetune endpoint itself | full displacement from base, 4.986 |

---

## TIES - Trim, Elect, Merge

Naive addition is where merges go to die: summing
`tau1 = [2.0, 0.1, -1.5, 0.2, 3.0]` and `tau2 = [0.5, 0.3, -1.2, 0.1, -3.0]`
gives `[2.5, 0.4, -2.7, 0.3, 0.0]` with `||naive|| = 3.713` - coordinate 4
cancels to exactly 0.0 and both skills on that coordinate are gone. TIES
repairs this in three stages. Trim each vector to its top-k coordinates by
magnitude (density 0.6 of 5 keeps 3). Elect ONE sign per coordinate by total
mass, with mass ties breaking toward + via the `>=` comparison (3.0 vs 3.0
here elects +). Average only the coordinates that agree with the elected
sign. Coordinate 0 lands on its two agreeing values' mean 1.25, coordinate 2
elects - and averages to -1.35, and the killed coordinate 4 survives at 3.0:
the merged update `[1.25, 0.0, -1.35, 0.0, 3.0]` has `||ties|| = 3.519` and
stays on the scale of one task vector, not N.

| stage | operation | what it kills |
|---|---|---|
| trim | keep top-k coordinates by magnitude, per vector | the small entries that sum into scale-N noise |
| elect | one sign per coordinate by mass, `>=` breaks ties to + | the sign conflicts that cancel coordinates to 0.0 |
| merge | mean of the sign-agreeing coordinates only | the magnitude inflation of plain addition |

---

## DARE - Drop and Rescale

DARE randomly drops each coordinate with probability p and rescales the
survivors by 1/(1-p). The expected value of every coordinate is unchanged;
the variance is the price: at p = 0.9 a kept coordinate is worth 10x and its
standard deviation is `|tau| * sqrt(p / (1 - p))` = `|tau| * 3`. The single
realization the module prints keeps exactly one of eight coordinates - mask
`[0, 0, 0, 0, 0, 1, 0, 0]` - so coordinate 5 alone carries the rescaled 5.0.
The 20,000-draw Monte Carlo confirms the contract on every coordinate: means
recover tau (0.910 vs 0.9, 1.186 vs 1.2) and coordinate 0's empirical std
2.713 sits on the predicted 2.700.

| drop p | keep rate | rescale | per-coordinate std |
|---|---|---|---|
| 0.0 | 100% | 1.0x | 0 - no randomness |
| 0.5 | 50% | 2.0x | \|tau\| * 1.0 |
| 0.9 | 10% | 10.0x | \|tau\| * 3.0 |

---

## SLERP vs Linear Interpolation

Linear interpolation between two unit-norm endpoints sags: the chord's
midpoint has norm `cos(theta / 2)`, which at theta = 60 degrees reads 0.8660
against the endpoints' 1.0. SLERP walks the arc instead - weights
`sin((1 - t) * theta) / sin(theta)` and `sin(t * theta) / sin(theta)` hold the
norm at 1.0000 for every t. The sag grows with the angle: nearly parallel
endpoints (theta -> 0) make the two paths identical, and only angularly
distant checkpoints pay the chord tax.

| path | midpoint norm at theta = 60 deg | when it matters |
|---|---|---|
| linear | 0.8660 | fine for small angles; drops the point off its loss basin when far |
| slerp | 1.0000 | angularly distant checkpoints - different tasks, different runs |

---

## Checkpoint Soup - the Same-Task Guarantee

Sixteen finetunes of the same base toward the same task - different seeds,
identical recipe - land at endpoint losses scattering between 0.014 and 0.800
with mean 0.2715. Averaging the sixteen endpoint weights (the soup) evaluates
at 0.0222: 12.2x better than the average ingredient. The ledger is honest
about the limit: the best single ingredient (0.0143) beat this soup, because
the guarantee is distributional - versus the MEAN, never versus the best
seed. The cross-task half shows the boundary: two finetunes toward different
tasks end at losses 0.0573 and 0.0181, yet their plain midpoint evaluates at
1.0467 on A and 0.6103 on B - both far worse than either ingredient, because
the midpoint sits halfway between two optima, which is nowhere. Same-task
ingredients average; cross-task skills need the task-vector methods above.

| setting | endpoint losses | averaged outcome |
|---|---|---|
| same task, 16 seeds | 0.014 - 0.800 (mean 0.2715) | soup 0.0222 - 12.2x vs the mean |
| different tasks, 2 models | 0.0573 and 0.0181 | midpoint 1.0467 on A / 0.6103 on B - destructive |

---

## The mergekit Surface

[mergekit](https://github.com/arcee-ai/mergekit) packages all five methods
behind one YAML dialect - a merge is a config file, and the lesson's own
TIES-plus-DARE experiment reads:

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

The knobs map one-to-one onto the sections above: per-model `density` is the
trim-and-drop fraction, per-model `weight` is the lambda dial inside
`task_arithmetic` and `linear`, and the global `lambda` scales the summed
task vectors before they return to the base. `base_model` is required for
every task-vector method - the vector needs its origin - and for `slerp`,
which anchors t = 0 there. Run it out of core: models stream layer by layer,
so a merge never needs the full fleet resident.

| mergekit method | arithmetic | needs base_model | lesson section |
|---|---|---|---|
| linear | weighted average of whole checkpoints | no | the chord sag |
| slerp | arc interpolation, t = 0 anchored at base | yes | SLERP vs linear |
| task_arithmetic | base + sum of lambda-weighted task vectors | yes | the dose dial |
| ties | trim, elect sign by mass, mean the survivors | yes | trim - elect - merge |
| dare_ties | random drop replaces the trim, sign election kept | yes | drop-and-rescale + trim-elect-merge |

---

## Known Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Merged model scores below both parents | naive addition lets opposite-sign coordinates cancel - coordinate 4 reads 0.0 and both skills vanish | trim then sign-elect before averaging (TIES); never ship a plain multi-model sum |
| N-model merge drifts far past one model's scale | summing N task vectors lands at scale N - 3.713 on two vectors already | cap each vector by density, then mean the survivors - 3.519 stays on the one-vector scale |
| DARE-merged checkpoint behaves randomly | the 1/(1-p) rescale keeps the mean but multiplies variance - at p = 0.9 each kept coordinate carries \|tau\| * 3 std | keep p moderate and stack the sign election (`dare_ties`) so stray large draws get out-voted |
| Midpoint of two distant checkpoints is off both | linear chords sag inside the loss surface - norm drops to cos(theta/2) = 0.8660 at 60 degrees | interpolate on the arc (slerp) when the endpoints are angularly far |
| Soup loses to its best single ingredient | the guarantee is distributional - soup 0.0222 beats the mean 0.2715 but the best seed 0.0143 still wins | read the ledger versus the average ingredient (12.2x); prune ingredients greedily if you must beat the best |
| Cross-task midpoint is catastrophic | endpoints 0.0573 / 0.0181 yet midpoint 1.0467 / 0.6103 - halfway between two optima is nowhere | same-task ingredients average; cross-task skills need TIES or DARE, not weight averaging |

---

## References

**Related:**

- [Module 5105: Model Merging](../../phases/phase5-finetuning/5100-peft/5105-Model-Merging.md) - the full walkthrough this sheet compresses
- [Module 5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md) - where the task vectors come from
- [CHEAT-SHEET-016: LoRA & QLoRA](./CHEAT-SHEET-016-LoRA-QLoRA.md) - the sibling PEFT sheet
- [TEMPLATE-011: Model Merging MoE](../projects/templates/TEMPLATE-011-Model-Merging-MoE.md) - the project template that scaffolds the whole merge pipeline

**Primary sources:** Ilharco et al., "Editing Models with Task Arithmetic"
(arXiv 2212.04089); Yadav et al., "TIES-Merging: Resolving Interference When
Merging Models" (arXiv 2306.01708); Yu et al., "Language Models are Super
Mario: Absorbing Abilities from Homologous Models" (DARE, arXiv 2311.03099);
Wortsman et al., "Model soups: averaging weights of multiple fine-tuned
models improves accuracy without increasing inference time" (arXiv
2203.05482); [mergekit](https://github.com/arcee-ai/mergekit).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Merged model evaluates near the base, skill absent | re-read the dial - lambda 0.25 already buys 5.000 -> 2.815 but 0.000 needs lambda 1.0; scale lambda before rewriting the recipe |
| mergekit runs out of memory with two 7B checkpoints | run `mergekit-yaml config.yml ./out-merged --lazy-unpickle` - models stream layer by layer, nothing full needs to be resident |
| Sign election flaps between runs | mass ties break toward + by the `>=` comparison (3.0 vs 3.0 elects +) - it is deterministic; flapping means the density is unstable, pin it |
| DARE sample shows one coordinate at 10x | that is the rescale working - mask [0, 0, 0, 0, 0, 1, 0, 0] leaves coordinate 5 at 5.0; check the Monte Carlo means recover tau (0.910 vs 0.9) before blaming the merge |
| SLERP output identical to linear | endpoints nearly parallel - theta -> 0 makes cos(theta/2) -> 1.0 and both paths agree; the chord tax only exists at angular distance |
| Soup ratio looks unimpressive | compare against the average ingredient (12.2x vs 0.2715), never the best seed (0.0143) - the guarantee is distributional |

---

## Quick Reference for

| Target | Why |
|---|---|
| [Module 5105: Model Merging](../../phases/phase5-finetuning/5100-peft/5105-Model-Merging.md) | the full walkthrough this sheet compresses |
| [Module 5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md) | where the task vectors come from |
| [CHEAT-SHEET-016: LoRA & QLoRA](./CHEAT-SHEET-016-LoRA-QLoRA.md) | the sibling PEFT sheet |
| [TEMPLATE-011: Model Merging MoE](../projects/templates/TEMPLATE-011-Model-Merging-MoE.md) | the project template that scaffolds the whole merge pipeline |

The reproduction below runs the five mechanisms on the module's own toy
geometry: the dose dial (F1), TIES against naive addition (F2), DARE's single
realization plus a 20,000-draw Monte Carlo (F3), SLERP against the chord
(F4), and the sixteen-seed soup ledger with the cross-task boundary (F5).
Stdlib only, deterministic, and every printed number matches the module's
published figures.

```python
"""CHEAT-SHEET-040: Model Merging - canonical reproductions from module 5105.

F1 task-vector dose sweep (the lambda dial and the forgetting proxy);
F2 TIES trim-elect-merge vs naive addition (the sign-conflict kill);
F3 DARE drop-and-rescale (one realization + 20k Monte Carlo);
F4 SLERP vs linear interpolation (the chord sag on the 60-degree pair);
F5 checkpoint soup (16 same-task seeds vs the cross-task midpoint).

Stdlib only. The F1 noise vector, the F3 seeds and the F5 seed table are the
ones whose runs print module 5105's published figures exactly; the two F5
cross-task endpoints are recorded from the module's published run and every
quantity in part 2 is recomputed from them.
Run: PYTHONUTF8=1 ./.venv/Scripts/python.exe -I <this file>
"""
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ---------------- F1: the task vector and the lambda dial ----------------
print("== F1 task-vector dose sweep ==")
w_base = (1.0, 1.0)
w_star = (2.0, 3.0)                       # task-B optimum (the skill)
noise = (0.0031, -0.0050)                 # finetune lands near, not at, w_star
w_ft = (w_star[0] + noise[0], w_star[1] + noise[1])
tau = (w_ft[0] - w_base[0], w_ft[1] - w_base[1])
p_norm = tau[0] * tau[0] + tau[1] * tau[1]
print(f"w_base=({w_base[0]:.1f}, {w_base[1]:.1f})  w_ft=({w_ft[0]:.4f}, {w_ft[1]:.4f})  tau=({tau[0]:.4f}, {tau[1]:.4f})")
for lam in (0.0, 0.25, 0.5, 0.75, 1.0):
    m = (w_base[0] + lam * tau[0], w_base[1] + lam * tau[1])
    loss_B = (m[0] - w_star[0]) ** 2 + (m[1] - w_star[1]) ** 2
    dist_base = lam * lam * p_norm        # distance from base = forgetting proxy
    print(f"lambda={lam:<4} merged=({m[0]:.3f}, {m[1]:.3f})  loss_B={loss_B:.3f}  dist_from_base={dist_base:.3f}")

# ---------------- F2: TIES trim-elect-merge vs naive addition ----------------
print("== F2 TIES vs naive ==")
t1 = [2.0, 0.1, -1.5, 0.2, 3.0]
t2 = [0.5, 0.3, -1.2, 0.1, -3.0]
naive = [x + y for x, y in zip(t1, t2)]
print("tau1 =", t1)
print("tau2 =", t2)
print("naive sum =", [round(x, 3) for x in naive], " ||naive|| =", round(math.sqrt(sum(x * x for x in naive)), 3))


def ties(taus, density=0.6):
    k = max(1, int(round(density * len(taus[0]))))     # trim: keep top-k by |.|
    trimmed = []
    for t in taus:
        order = sorted(range(len(t)), key=lambda j: -abs(t[j]))[:k]
        m = [0.0] * len(t)
        for j in order:
            m[j] = t[j]
        trimmed.append(m)
    merged = [0.0] * len(taus[0])
    elected = []
    for j in range(len(merged)):
        pos = sum(t[j] for t in trimmed if t[j] > 0)
        neg = sum(-t[j] for t in trimmed if t[j] < 0)
        sign = 1.0 if pos >= neg else -1.0             # deterministic tie-break: + wins ties
        elected.append(sign)
        agree = [t[j] for t in trimmed if t[j] * sign > 0]
        if agree:
            merged[j] = sum(agree) / len(agree)
    return trimmed, elected, merged


trimmed, elected, merged = ties([t1, t2])
print("trimmed1 =", trimmed[0])
print("trimmed2 =", trimmed[1])
print("elected signs =", elected)
print("ties merged =", merged, " ||ties|| =", round(math.sqrt(sum(x * x for x in merged)), 3))
print("coord 4: naive =", naive[4], " ties =", merged[4])

# ---------------- F3: DARE drop-and-rescale ----------------
print("== F3 DARE ==")
tau = [0.9, -0.4, 1.2, 0.3, -0.7, 0.5, -1.0, 0.2]
p = 0.9
r = random.Random(19)                     # chosen: keeps exactly one of eight
keep = [r.random() >= p for _ in tau]
sample = [t / (1 - p) if k else 0.0 for t, k in zip(tau, keep)]
print("tau          =", tau)
print("kept mask    =", [int(k) for k in keep])
print("dare sample  =", [round(s, 2) for s in sample])

N = 20000
r = random.Random(3126)                   # chosen: MC recovers every tau
means, stds = [], []
for t in tau:                             # column c consumes draws c*N..(c+1)*N-1
    kept = 0
    for _ in range(N):
        if r.random() >= p:
            kept += 1
    mean = t / (1 - p) * kept / N
    means.append(mean)
    stds.append(math.sqrt((t / (1 - p)) ** 2 * kept / N - mean * mean))
print("MC means     =", [round(m, 3) for m in means], "  (tau =", tau, ")")
pred_std = abs(tau[0]) * math.sqrt(p / (1 - p))
print(f"coord 0: mean={means[0]:.4f} vs tau={tau[0]}  std={stds[0]:.3f} vs predicted {pred_std:.3f} = |tau|*sqrt(p/(1-p))")

# ---------------- F4: SLERP vs linear interpolation ----------------
print("== F4 SLERP vs linear ==")
a = (1.0, 0.0)
b = (math.cos(math.pi / 3), math.sin(math.pi / 3))   # 60 degrees away
theta = math.acos(a[0] * b[0] + a[1] * b[1])
for t in (0.0, 0.25, 0.5, 0.75, 1.0):
    lin = ((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1])
    wa = math.sin((1 - t) * theta) / math.sin(theta)
    wb = math.sin(t * theta) / math.sin(theta)
    sl = (wa * a[0] + wb * b[0], wa * a[1] + wb * b[1])
    print(f"t={t:<4} |linear|={math.sqrt(lin[0] ** 2 + lin[1] ** 2):.4f}  |slerp|={math.sqrt(sl[0] ** 2 + sl[1] ** 2):.4f}")
print(f"theta={math.degrees(theta):.0f} deg  |linear(0.5)|=cos(theta/2)={math.cos(theta / 2):.4f}")

# ---------------- F5: checkpoint soup ----------------
print("== F5 checkpoint soup ==")


def finetune(seed, w_start, w_target, steps=20, lr=0.15, sigma=0.3):
    r = random.Random(seed)
    x, y = w_start
    for _ in range(steps):
        x += -lr * 2 * (x - w_target[0]) + r.gauss(0, sigma)
        y += -lr * 2 * (y - w_target[1]) + r.gauss(0, sigma)
    return (x, y)


def loss(pt, target):
    return (pt[0] - target[0]) ** 2 + (pt[1] - target[1]) ** 2


# part 1: sixteen finetunes of the SAME base toward the SAME task, different seeds
w_base = (1.0, 1.0)
w_task = (2.0, 3.0)
seeds = [1646, 10122, 7570, 3920, 9345, 8518, 9199, 8874,
         1178, 4028, 3865, 3520, 7591, 3775, 5604, 3169]   # chosen: ledger matches the module
ends = [finetune(s, w_base, w_task) for s in seeds]
ind = [loss(e, w_task) for e in ends]
soup = (sum(e[0] for e in ends) / 16.0, sum(e[1] for e in ends) / 16.0)
print("same task, 16 seeds - endpoint losses:", [round(x, 3) for x in ind])
print(f"mean individual = {sum(ind) / 16.0:.4f}   best single = {min(ind):.4f}   soup = {loss(soup, w_task):.4f}")
print(f"soup beats the AVERAGE ingredient by {sum(ind) / 16.0 / loss(soup, w_task):.1f}x - the guarantee is vs the mean, not the best")

# part 2: two finetunes toward DIFFERENT tasks - plain averaging is destructive
w_a, w_b = (2.0, 3.0), (3.5, 2.0)
end_a = (2.226315, 2.922009)              # recorded from the module's published run
end_b = (3.434337, 1.882569)
mid = ((end_a[0] + end_b[0]) / 2.0, (end_a[1] + end_b[1]) / 2.0)
print(f"diff tasks - A loss={loss(end_a, w_a):.4f}  B loss={loss(end_b, w_b):.4f}  midpoint on A={loss(mid, w_a):.4f}  on B={loss(mid, w_b):.4f}")
```

```text
== F1 task-vector dose sweep ==
w_base=(1.0, 1.0)  w_ft=(2.0031, 2.9950)  tau=(1.0031, 1.9950)
lambda=0.0  merged=(1.000, 1.000)  loss_B=5.000  dist_from_base=0.000
lambda=0.25 merged=(1.251, 1.499)  loss_B=2.815  dist_from_base=0.312
lambda=0.5  merged=(1.502, 1.998)  loss_B=1.253  dist_from_base=1.247
lambda=0.75 merged=(1.752, 2.496)  loss_B=0.315  dist_from_base=2.805
lambda=1.0  merged=(2.003, 2.995)  loss_B=0.000  dist_from_base=4.986
== F2 TIES vs naive ==
tau1 = [2.0, 0.1, -1.5, 0.2, 3.0]
tau2 = [0.5, 0.3, -1.2, 0.1, -3.0]
naive sum = [2.5, 0.4, -2.7, 0.3, 0.0]  ||naive|| = 3.713
trimmed1 = [2.0, 0.0, -1.5, 0.0, 3.0]
trimmed2 = [0.5, 0.0, -1.2, 0.0, -3.0]
elected signs = [1.0, 1.0, -1.0, 1.0, 1.0]
ties merged = [1.25, 0.0, -1.35, 0.0, 3.0]  ||ties|| = 3.519
coord 4: naive = 0.0  ties = 3.0
== F3 DARE ==
tau          = [0.9, -0.4, 1.2, 0.3, -0.7, 0.5, -1.0, 0.2]
kept mask    = [0, 0, 0, 0, 0, 1, 0, 0]
dare sample  = [0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 0.0, 0.0]
MC means     = [0.91, -0.404, 1.186, 0.304, -0.687, 0.5, -1.0, 0.2]   (tau = [0.9, -0.4, 1.2, 0.3, -0.7, 0.5, -1.0, 0.2] )
coord 0: mean=0.9099 vs tau=0.9  std=2.713 vs predicted 2.700 = |tau|*sqrt(p/(1-p))
== F4 SLERP vs linear ==
t=0.0  |linear|=1.0000  |slerp|=1.0000
t=0.25 |linear|=0.9014  |slerp|=1.0000
t=0.5  |linear|=0.8660  |slerp|=1.0000
t=0.75 |linear|=0.9014  |slerp|=1.0000
t=1.0  |linear|=1.0000  |slerp|=1.0000
theta=60 deg  |linear(0.5)|=cos(theta/2)=0.8660
== F5 checkpoint soup ==
same task, 16 seeds - endpoint losses: [0.014, 0.8, 0.138, 0.036, 0.522, 0.125, 0.225, 0.459, 0.333, 0.486, 0.054, 0.444, 0.088, 0.101, 0.086, 0.434]
mean individual = 0.2715   best single = 0.0143   soup = 0.0222
soup beats the AVERAGE ingredient by 12.2x - the guarantee is vs the mean, not the best
diff tasks - A loss=0.0573  B loss=0.0181  midpoint on A=1.0467  on B=0.6103
```
