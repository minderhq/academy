---
Document ID: 5406
Title: "5406: Distributed LR Scaling - The Linear Rule, the Wall, and the Warmup"
Phase: 5
Module: 5400
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Tags: ['training', 'distributed', 'optimization', 'learning-rate', 'warmup']
---

# 5406: Distributed LR Scaling - The Linear Rule, the Wall, and the Warmup

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Noise and the Wall](#the-noise-and-the-wall)
- [Warmup Is the Scaled Rate's Stabilizer](#warmup-is-the-scaled-rates-stabilizer)
- [The Critical Batch Size](#the-critical-batch-size)
- [Gradient Accumulation: Exact Math, Real Divergences](#gradient-accumulation-exact-math-real-divergences)
- [The Campaign: One Fine-Tune, Five Bills](#the-campaign-one-fine-tune-five-bills)
- [Beyond the Wall: LARS and LAMB](#beyond-the-wall-lars-and-lamb)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After reading this lesson, you will be able to:

- State the linear scaling rule and the gradient-noise mechanism underneath it: `Var[g_B] = Var[g] / B`
- Locate the stability wall `eta_max = 2 / lambda_max` and compute the amplification a scaled rate suffers next to it
- Size a warmup from `W > eta_target * lambda_early * t_sharp / 2` and show what a half-sized warmup costs
- Fit the critical-batch curve `S(B) = S_min * (1 + B_noise / B)` from a steps-to-target sweep
- Price gradient accumulation's three real divergences: optimizer-step count, warmup fraction, and clip order
- Walk one fine-tune across five distributed configs and read the campaign ledger

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)

## Abstract

This module teaches the machinery of distributed training - [5401](./5401-Data-Parallelism.md) owns DDP's communication pattern, [5403](./5403-Mixed-Precision.md) owns precision, [5404](./5404-Distributed-Optimization.md) owns optimizer-state sharding, [5405](./5405-FSDP2-and-torchao.md) owns per-parameter sharding - but the first knob every distributed run actually touches is stated nowhere in it: **what happens to the learning rate when the world size grows**. [5502](../5500-advanced-optimization/5502-Learning-Rate-Scheduling.md) names the linear scaling rule as a four-line checklist item and owns the schedule shapes; [5501](../5500-advanced-optimization/5501-Optimizer-Variants.md) owns the optimizer variants. This lesson owns the scaling decision itself: the gradient-noise mechanism that makes scaling legal, the stability wall that caps it, the warmup that lets a scaled rate survive the sharp early phase, the critical batch size that bounds what scaling can buy, gradient accumulation's exact math and its three real divergences, and a five-config campaign that prices all of it on one ledger. The rule is one line - multiply the LR by the world size - and everything else in this lesson is the fine print that line does not say.

## The Noise and the Wall

Why does growing the batch permit growing the LR at all? Because a mini-batch gradient is a noisy estimate of the true gradient, and averaging `B` independent per-sample gradients divides the noise variance by `B`: `Var[g_B] = Var[g] / B`. The *signal* (the true gradient) is unchanged; the *noise* shrinks as `1/sqrt(B)`. A step of size `eta` on a noisier gradient is a step in the right direction plus a larger random kick - so with less noise you can afford a bigger step. The linear scaling rule is the bookkeeping that keeps the noise-per-step constant: multiply the batch by `k`, multiply the LR by `k`, and the per-step noise contribution `eta * sigma / sqrt(B)` is unchanged.

But the LR cannot grow forever. On the simplest possible surface - a quadratic with curvature `lambda` - gradient descent moves the error by a factor `(1 - eta * lambda)` per step, and the iteration is stable only while `|1 - eta * lambda| < 1`, i.e. `eta < 2 / lambda`. That is the **stability wall**. Between safety and the wall the error still *oscillates* across the minimum while contracting, and the contraction factor's worst case `1 - eta*lambda/2` sets the per-oscillation amplification `1 / (1 - eta*lambda/2)` applied to whatever gradient noise survives the larger batch. The fence verifies the noise law empirically, then walks both scaling rules up to `k = 32` and watches which side of the wall each lands on:

```python
# The noise law and the wall: linear vs sqrt scaling at eta0 = 0.3, B0 = 32.
# Toy: single-weight quadratic with curvature lambda = 1, gradient noise sigma = 1.
import math
import random
import statistics

lam, sigma, w0, B0, eta0, T = 1.0, 1.0, 3.0, 32, 0.3, 2000

# --- Var[g_B] = Var[g]/B, checked empirically at w = 0 ---
rng = random.Random(7)
N = 200_000
for B in (32, 256):
    draws = [rng.gauss(0.0, sigma) / math.sqrt(B) for _ in range(N)]
    emp = statistics.pstdev(draws)
    print(f"  B={B:>4}: empirical noise std {emp:.4f}  vs sigma/sqrt(B) {sigma / math.sqrt(B):.4f}")
print(f"  wall: eta_max = 2/lam = {2.0 / lam:.1f}   (|1 - eta*lam| < 1 required)")


def walk(k, mode):
    B = B0 * k
    eta = eta0 * (k if mode == "linear" else math.sqrt(k))
    rng = random.Random(1000 + k)
    w = w0
    for _ in range(T):
        g = lam * w + rng.gauss(0.0, sigma) / math.sqrt(B)
        w -= eta * g
        if abs(w) > 100.0:
            return eta, B, None
    return eta, B, abs(w)


print(f"  {'rule':>7} {'k':>3} {'B':>5} {'eta':>6} {'2-eta':>6} {'amp':>7}  final |w-w*|")
for mode in ("linear", "sqrt"):
    for k in (1, 2, 4, 8, 16, 32):
        eta, B, err = walk(k, mode)
        amp = 1.0 / (1.0 - eta * lam / 2.0) if eta * lam < 2.0 else float("inf")
        head = 2.0 - eta * lam
        fate = "DIVERGED" if err is None else f"{err:.4f}"
        print(f"  {mode:>7} {k:>3} {B:>5} {eta:>6.3f} {head:>6.2f} {amp:>7.2f}  {fate}")
```

Read the two halves of that table as one argument. The noise law holds exactly: empirical standard deviation `0.1767` against the predicted `0.1768` at `B = 32`, and `0.0624` against `0.0625` at `B = 256`. The linear column is the cliff: the rate grows `0.300 -> 0.600 -> 1.200 -> 2.400`, the headroom `2 - eta` shrinks `1.70 -> 1.40 -> 0.80 -> -0.40`, and everything from `k = 8` on is **DIVERGED** - at `k = 32` the rate is `9.600`, nearly five times past the wall. The sqrt column never crosses: at `k = 32` the rate is `1.697`, headroom `0.30`, and the amplification column shows the price - noise near the wall is magnified `6.60x` per oscillation, which is why the surviving run's final error `0.0734` is no better than the tiny-`k` runs': sqrt scaling spends its headroom on noise, not on progress. The linear rule is the aggressive one, and it is legal exactly while `eta0 * k < 2 / lambda_max`.

This is not a toy curiosity. Goyal et al. (arXiv [1706.02677](https://arxiv.org/abs/1706.02677)) trained ResNet-50 at batch 8192 on 256 GPUs - ImageNet in about an hour - with precisely this rule (LR scaled linearly with batch) plus the warmup of the next section, reporting roughly 90% scaling efficiency from 8 to 256 GPUs. McCandlish et al. (arXiv [1812.06162](https://arxiv.org/abs/1812.06162)) then explained *when* the rule is allowed to work: every task has a **gradient noise scale** `B_noise`, and only batches well below it sit in the noise-dominated regime where scaling the batch is "free". That regime boundary is Section 3.

## Warmup Is the Scaled Rate's Stabilizer

The wall in Section 1 used one fixed curvature. Real networks do not: an *untrained* network's loss surface is violently curved in the early steps, and the curvature relaxes as the weights settle. Goyal et al. saw this directly - their batch-8192 runs diverged without a warmup period, which is why the paper introduced a linear LR ramp as part of the recipe (their "new warmup" scheme, ramping over the first 5 epochs rather than 1). Warmup is not a decoration bolted onto the schedule; it is the stability condition `eta * lambda(t) < 2` solved for a *time-varying* `lambda(t)`.

The fence makes the sharp phase explicit with a two-phase toy: curvature `lambda_early = 8.0` for the first `t_sharp = 200` steps (the untrained-network spike), then `lambda_late = 0.5` (the settled surface). The early wall is `2 / 8 = 0.25` - the target rate `1.0` sits four times above it, unreachable at step one. A linear ramp `eta(t) = eta_target * t / W` crosses the early phase safely only if the ramp is still small while `t < 200`; requiring `eta(W') * lambda_early < 2` at the worst point inside the sharp phase gives the sizing rule:

```text
W > eta_target * lambda_early * t_sharp / 2
```

The fence walks three warmup choices against that rule - none, half of it, and twice it - across 20 seeds each:

```python
# Warmup sizing on the two-phase toy: lambda_early = 8 (t < 200), lambda_late = 0.5.
# Target rate eta_t = 1.0; the ramp must stay under the early wall for all t < 200.
import math
import random
import statistics

lam_e, lam_l, t_sharp = 8.0, 0.5, 200
sigma, B, w0, eta_t, T = 0.3, 256, 1.0, 1.0, 6000
sig_eff = sigma / math.sqrt(B)
t_min = eta_t * lam_e * t_sharp / 2.0
print(f"  early wall: eta*{lam_e:.0f} < 2 -> eta < {2.0 / lam_e:.2f} during the first {t_sharp} steps")
print(f"  target eta = {eta_t:.1f}; ramp must stay under the early wall for all t < {t_sharp}")
print(f"  sizing rule: W > eta_target * lam_early * t_sharp / 2 = {t_min:.0f}")


def run(W, seed):
    rng = random.Random(seed)
    w = w0
    for t in range(T):
        eta = eta_t if t >= W else eta_t * (t + 1) / W
        lam = lam_e if t < t_sharp else lam_l
        w -= eta * (lam * w + rng.gauss(0.0, sig_eff))
        if abs(w) > 50.0:
            return None
    return abs(w)


for W in (0, 400, 1600):
    fates = [run(W, 200 + s) for s in range(20)]
    dead = sum(1 for f in fates if f is None)
    alive = [f for f in fates if f is not None]
    med = statistics.median(alive) if alive else float("nan")
    name = "constant (no warmup)" if W == 0 else f"warmup W={W}"
    print(f"  {name:>22}: diverged {dead:>2}/20   median final |w| {med:.4f}")
```

The rule is `W > 800`, and the table is unforgiving about half-measures: no warmup diverges `20/20`, a warmup of `W = 400` - *half* the rule - still diverges `20/20`, and `W = 1600`, twice the rule, survives all 20 seeds with a median final error of `0.0091`. Half the rule is not half safe; it is zero safe. The reason is arithmetic: inside the sharp phase a ramp too fast crosses `eta * lambda_early = 2` before `t = 200`, and from there the unstable factor amplifies whatever it is given - the divergence is seed-proof. Warmup length is not a taste question. It is derived from the sharpest curvature your run will see, and under-sizing it buys nothing at all.

Two consequences for distributed runs, both of which return in Section 4: first, when world size scales the target rate up, the rule scales the warmup up *with it* (`W` grows linearly in `eta_target`). Second, the rule's `W` is measured in **optimizer steps** - and gradient accumulation changes how many of those a fixed token budget buys.

## The Critical Batch Size

How much can scaling actually buy? McCandlish et al.'s answer is a curve for the number of steps `S(B)` needed to reach a fixed loss as a function of batch size:

```text
S(B) = S_min * (1 + B_noise / B)
```

Well below `B_noise` (noise-dominated), steps fall as `1/B` - doubling the batch halves the steps, and the linear rule converts that into the same wall-clock at `k` times the parallelism. Well above `B_noise` (curvature-dominated), `S(B)` flattens at `S_min` - extra machines buy almost nothing in steps. The **critical batch size** `B_noise` is the knee between the two regimes, and the fence measures it the way the paper defines it: sweep `B`, record median steps-to-target, fit the two parameters:

```python
# Critical batch size: median steps-to-target S(B) for a two-scale quadratic
# (fast mode lambda_f = 1.0, slow mode lambda_s = 0.05), fit to S = S_min * (1 + B_noise/B).
import math
import random

lam_f, lam_s = 1.0, 0.05
eta, sigma = 0.4, 1.5
w0f, w0s = 4.0, 20.0
eps, hold, cap, seeds = 0.4, 10, 5000, 120
Bs = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]


def steps_to(B, seed):
    rng = random.Random(3000 + seed)
    wf, ws = w0f, w0s
    below = 0
    for t in range(1, cap + 1):
        sf = rng.gauss(0.0, sigma) / math.sqrt(B)
        ss = rng.gauss(0.0, sigma) / math.sqrt(B)
        wf -= eta * (lam_f * wf + sf)
        ws -= eta * (lam_s * ws + ss)
        loss = 0.5 * wf * wf + 0.5 * lam_s * ws * ws
        below = below + 1 if loss < eps else 0
        if below >= hold:
            return t
    return cap


S = []
for B in Bs:
    vals = sorted(steps_to(B, s) for s in range(seeds))
    med = vals[seeds // 2]
    S.append(med)
    print(f"  B={B:>4}: median steps to loss < {eps} = {med}")

# least squares fit S = S_min * (1 + B_noise/B) == a + c*u, u = 1/B
us = [1.0 / B for B in Bs]
n = len(us)
su, ss_ = sum(us), sum(S)
suu = sum(u * u for u in us)
suS = sum(u * s for u, s in zip(us, S))
c = (n * suS - su * ss_) / (n * suu - su * su)
a = (ss_ - c * su) / n
B_noise = c / a
print()
print(f"  fit: S_min = {a:.1f}, B_noise = {B_noise:.1f}")
print(f"  at B = B_noise: S = {a * (1 + B_noise / B_noise):.1f} = 2 x S_min (the knee)")
print(f"  S({Bs[0]})/S_min = {S[0] / a:.2f}   S({Bs[-1]})/S_min = {S[-1] / a:.2f}")
```

The walk is `155 -> 114 -> 101 -> 96 -> 94 -> 91 -> 90 -> 89 -> 89 -> 89` across `B = 1` to `512`: a steep `1/B` segment that bends and flattens. The fit lands at `S_min = 88.1` and `B_noise = 0.7` in this toy's units, and the knee property checks exactly: at `B = B_noise` the predicted cost is `176.3 = 2 x S_min`, the point where scaling stops halving. The endpoints bracket the two regimes: `S(1)` is `1.76x` the floor, `S(512)` is `1.01x` - flat. Be honest about the units: this toy's `B_noise` is sub-batch, while real networks' measured noise scales run from thousands (MNIST-scale) to millions (large language models); the *shape* is the claim here, not the number. The shape is what you measure before you rent GPUs: if your job's batch already sits above *its* `B_noise`, the linear rule will scale the LR into the wall (Section 1) while buying no steps (this section) - the worst of both halves.

Smith et al. (arXiv [1711.00489](https://arxiv.org/abs/1711.00489)) close the loop from the other side: decaying the LR by a factor is equivalent to raising the batch by the same factor (`B` inversely proportional to `eta`), and momentum `m` rescales the equivalence too (`B` proportional to `1/(1-m)`). Batch size and learning rate are one knob measured in two units - which is why every LR-scaling decision in this lesson is also a batch-size decision.

## Gradient Accumulation: Exact Math, Real Divergences

The cheapest way to "scale the batch" is not more GPUs but gradient accumulation: run several micro-batches, sum or average their gradients, step once. The math is exact - the mean of micro-batch means equals the full-batch mean whenever the micro-batches are equal-sized, and the fence verifies it to `0.00e+00` difference on 1,024 samples in 8 buckets of 128. Exactness is also the trap: because the *math* cannot diverge, the real divergences live in the *bookkeeping* around it. The fence prices all three:

```python
# Gradient accumulation: mean-of-means is exact; the divergences are bookkeeping.
import math
import random

rng = random.Random(41)
samples = [rng.gauss(1.3, 2.0) for _ in range(1024)]
full = sum(samples) / len(samples)
micro = [sum(samples[i * 128:(i + 1) * 128]) / 128.0 for i in range(8)]
acc = sum(micro) / 8.0
print(f"  mean-of-means vs full-batch mean: max diff {abs(acc - full):.2e}  (exact)")

samples_1025 = samples + [rng.gauss(1.3, 2.0)]
drop = sum(samples_1025[:1024]) / 1024.0
full1025 = sum(samples_1025) / 1025.0
print(f"  drop-last (1025 samples, 8x128): shift {abs(drop - full1025):.4f} vs full-batch mean")
print()

micro_bs, accum, epoch_s, epochs, warm = 32, 8, 4096, 3, 10
steps_micro = epochs * epoch_s // micro_bs
steps_accum = epochs * epoch_s // (micro_bs * accum)
print(f"  same data, {epochs} epochs: micro-{micro_bs} -> {steps_micro} optimizer steps; "
      f"accum x{accum} -> {steps_accum}")
t_m, t_a = steps_micro / 8, steps_accum / 8
print(f"    at 12.5% of data: micro run optimizer step {t_m:>5.0f} warmup factor {min(1.0, t_m / warm):.3f}   "
      f"accum run step {t_a:>4.0f} warmup factor {min(1.0, t_a / warm):.3f}")
wm = warm / steps_micro * 100
wa = warm / steps_accum * 100
print(f"    warmup {warm} steps consumes {wm:.1f}% of training (micro) vs {wa:.1f}% (accum)")
print()


def norm(v):
    return math.sqrt(sum(x * x for x in v))


micros = [(3.2, (1.0, 0.0)), (0.4, (0.6, 0.8)), (0.9, (1.0, 0.0)), (1.1, (0.8, 0.6))]
per = []
for n_, (ux, uy) in micros:
    s = min(1.0, 1.0 / n_)
    per.append((s * n_ * ux, s * n_ * uy))
cx = sum(p[0] for p in per) / 4.0
cy = sum(p[1] for p in per) / 4.0
raw = [(n_ * ux, n_ * uy) for n_, (ux, uy) in micros]
mx = sum(r[0] for r in raw) / 4.0
my = sum(r[1] for r in raw) / 4.0
acc_norm = norm((mx, my))
sc = min(1.0, 1.0 / acc_norm)
ang = lambda v: math.degrees(math.atan2(v[1], v[0]))
print(f"  clipping, 4 micro-norms {[n_ for n_, _ in micros]} at max 1.0:")
print(f"    clip-then-average: norm {norm((cx, cy)):.3f} at {ang((cx, cy)):.1f} deg")
print(f"    average-then-clip: norm {sc * acc_norm:.3f} at {ang((mx, my)):.1f} deg")
print(f"    effective-LR ratio {norm((cx, cy)) / (sc * acc_norm):.3f}, "
      f"direction gap {abs(ang((cx, cy)) - ang((mx, my))):.1f} deg")
```

The exactness first: mean-of-means against the full-batch mean, max diff `0.00e+00` - accumulation is not an approximation of a big batch, it *is* the big batch. The drop-last row is the first divergence: with 1,025 samples in buckets of 128, the last bucket is short, and the two ways of handling it (drop the remainder, or weight the short bucket) differ by `0.0017` in the batch mean - small here, but a systematic per-step bias that a sensitive fine-tune can feel.

The second divergence is the one that bites scaled runs: **everything keyed on optimizer steps changes meaning**. The same 3-epoch token budget is `384` optimizer steps at micro-batch 32 but `48` at accumulation 8 - 8x fewer. A warmup configured as `10` steps is `2.6%` of the micro run but `20.8%` of the accumulated run; at the 12.5% mark of the data the micro run's warmup factor is already `1.000` while the accumulated run is still at `0.600`. Porting a config from a single-GPU run to an accumulated run without rescaling step-counted quantities silently re-times the schedule. PyTorch's [`LinearLR`](https://docs.pytorch.org/docs/stable/generated/torch.optim.lr_scheduler.LinearLR.html) makes no allowance for this - `total_iters` counts optimizer steps, full stop.

The third divergence is clip order. Per-micro-batch clipping rescales each micro-gradient to norm `1.0` *before* averaging; the honest accumulated gradient is the average *then* clip. On four micro-gradients with norms `3.2, 0.4, 0.9, 1.1`, clip-then-average produces a step of norm `0.770` at `17.4` degrees while average-then-clip produces norm `1.000` at `10.6` degrees - the clip-first step is `0.770x` the effective LR and `6.7` degrees off in direction. The big micro-batch dominates the direction and gets shrunk twice. This composes with DDP's own ordering: [5401](./5401-Data-Parallelism.md) clips *before* the all-reduce (per-rank), and DDP's all-reduce is a *mean* of per-rank gradients - the same double-shrink, one level up. `torch.nn.utils.clip_grad_norm_` returns the *total norm before clipping* precisely so calling code can log it; log it, and compare across your accumulation configs.

## The Campaign: One Fine-Tune, Five Bills

Everything above composes into one decision: you have a 1.2B-token fine-tune, a base rate `eta0 = 0.2` that converges at world size 1, and a cluster. Five configs, 20 seeds each - the two-phase toy of Section 2 stands in for the sharp early phase, with the same target `|w| < 0.05` held for 5 steps, and divergence is terminal (a blown-up run is killed; it does not get rescued by the later schedule). Pricing: 3,500 tokens/s per GPU at $2.50 per GPU-hour.

```python
# The campaign: five distributed configs on one 1.2B-token fine-tune.
# R1 baseline; R2 linear-scaled with the sized warmup; R3 same, no warmup;
# R4 linear at k=32 (endpoint past the late-phase wall); R5 sqrt at k=32.
import math
import random
import statistics

lam_e, lam_l, t_sharp = 8.0, 0.5, 200
sigma, B, w0, eta0 = 0.3, 32, 1.0, 0.2
sig_eff = sigma / math.sqrt(B)
T, tgt, hold = 12000, 0.05, 5


def run(eta_t, W, seed):
    rng = random.Random(seed)
    w = w0
    hit, div = None, None
    below = 0
    for t in range(1, T + 1):
        eta = eta_t if t >= W else eta_t * t / W
        lam = lam_e if t < t_sharp else lam_l
        w -= eta * (lam * w + rng.gauss(0.0, sig_eff))
        if abs(w) > 50.0:
            div = t
            break  # divergence is terminal: the run is killed, no recovery
        if hit is None:
            below = below + 1 if abs(w) < tgt else 0
            if below >= hold:
                hit = t
    return hit, div


rows = [
    ("R1 baseline k=1", 0.2, 0, 1),
    ("R2 k=8 linear+warmup", 1.6, 2560, 8),
    ("R3 k=8 linear no-warmup", 1.6, 0, 8),
    ("R4 k=32 linear+warmup", 6.4, 10240, 32),
    ("R5 k=32 sqrt+warmup", 0.2 * math.sqrt(32), 1810, 32),
]
tok, tps, usd = 1_200_000_000, 3500, 2.50
res = {}
for name, eta_t, W, world in rows:
    fates = [run(eta_t, W, 5000 + s) for s in range(20)]
    dead = sum(1 for _, d in fates if d is not None)
    hits = [h for h, _ in fates if h is not None]
    divs = sorted(d for _, d in fates if d is not None)
    med_hit = statistics.median(hits) if hits else -1
    med_div = divs[len(divs) // 2] if divs else -1
    wall = tok / (tps * world) / 3600.0
    cost = world * wall * usd
    res[name] = (med_hit, med_div, world, wall, cost)
    print(f"  {name}: diverged {dead:>2}/20  hit target {len(hits):>2}/20 (~step {med_hit:>6.0f})  "
          f"diverge ~step {med_div:>6.0f}  wall {wall:5.2f} h  ${cost:7.2f}")
print()
print(f"  pricing: {tok / 1e9:.1f}B tokens, {tps:,} tok/s/GPU, ${usd:.2f}/GPU-h")
for src, dst in (("R3 k=8 linear no-warmup", "R2 k=8 linear+warmup"),
                 ("R4 k=32 linear+warmup", "R5 k=32 sqrt+warmup")):
    _, d, world, wall, _ = res[src]
    dwall, dcost = res[dst][3], res[dst][4]
    burn = d / T * wall * world * usd
    tag = src.split()[0]
    dtag = dst.split()[0]
    print(f"  {tag} diverged -> retry as {dtag}: ${burn:6.2f} burned + ${dcost:.2f} = "
          f"${burn + dcost:.2f} in {d / T * wall + dwall:.2f} h")
```

The bill is identical across every surviving config - `$238.10` is `1.2B tokens / 3,500 tok/s * $2.50/GPU-h`, and scaling the world only divides the *wall-clock* (`95.24h` at `k=1`, `11.90h` at `k=8`, `2.98h` at `k=32`). The rows differ in whether the run exists at the end of it:

- **R1** (baseline, `k=1`): `0/20` diverged, target hit `20/20` around step `10`. Safe, slow.
- **R2** (`k=8`, linear to `1.6`, warmup `W=2560` sized at twice the rule): `0/20`, hit at `~38`. The linear rule working as designed - the warmup rides the ramp under the early wall, and the endpoint `1.6` is under every wall the toy has.
- **R3** (`k=8`, no warmup): diverged `20/20` at `~step 2`, target hit `0/20`. The unscaled-rate's failure mode from Section 2, unchanged by a bigger cluster: the same `$238.10` spent for nothing, plus the retry.
- **R4** (`k=32`, linear to `6.4`, warmup `W=10240`): the important row. Target hit `20/20` at `~step 38` - the run *converged*, the warmup did its job - and then diverged `20/20` at `~step 6551`, when the long ramp reached the late-phase wall `2 / 0.5 = 4.0` and crossed it. The warmup protects the sharp early phase; nothing in the linear rule protects the *endpoint*. `6.4 > 4.0` is the whole story: converged at step 38, dead at step 6551, `$129.98` of the `$238.10` burned for a checkpoint that never gets written.
- **R5** (`k=32`, sqrt to `0.2 * sqrt(32) = 1.13`, warmup `W=1810`): `0/20`, hit at `~38`. The sqrt endpoint `1.13` sits under the late wall with room to spare - slower growth, but a run that finishes.

The retries price the two failure modes: `R3 -> R2` costs `$0.04` burned (it died at step 2) plus the full `$238.10` - `$238.13` in `11.91h`, an annoying but cheap lesson. `R4 -> R5` costs `$129.98` burned (it died *past* convergence, halfway through the wall-clock) plus `$238.10` - `$368.08` in `4.60h`. The dangerous scaling failure is not the loud one that dies in warmup; it is the one that converges, looks healthy, and dies when the schedule's endpoint walks past a wall nobody re-checked.

## Beyond the Wall: LARS and LAMB

Both scaling rules so far scale one global LR against one wall. The wall, however, is per-layer: `eta_max = 2 / lambda_max` where `lambda_max` is a curvature, and curvatures differ wildly across a network's layers. The layer-adaptive optimizers attack exactly this. **LARS** (You et al., arXiv [1708.03888](https://arxiv.org/abs/1708.03888)) updates each layer with a step scaled by the *trust ratio* `||w|| / ||grad w||` - layers whose weights are large relative to their gradients get proportionally gentler steps - and demonstrated ResNet-50 training at batch 32K without accuracy loss. **LAMB** (You et al., arXiv [1904.00962](https://arxiv.org/abs/1904.00962), ICLR 2020) carries the trust ratio into Adam's update rule and scaled BERT training from 3 days to 76 minutes on a TPUv3 Pod at batch 32,868.

This lesson treats them in prose only, deliberately: the fences' toys are single-scale (one weight, one curvature), so they cannot exhibit layer-adaptive rates without faking it. The honest boundary: [5501](../5500-advanced-optimization/5501-Optimizer-Variants.md) owns LARS and LAMB as *optimizers* - their update rules, their hyperparameters, their failure modes. Here they appear as *answers to the wall*: when a single global rate cannot sit under every layer's `2 / lambda_max` at once, stop using a single global rate. The linear rule, the warmup, and the critical batch size still apply above them - LAMB's batch-32,868 BERT run used warmup and a schedule like any other run in this lesson.

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Loss NaNs within the first steps after raising world size | linear rule applied past the wall: `eta0 * k > 2 / lambda_max` | check the product against the wall before launching; drop to sqrt scaling or add warmup sized by Section 2's rule |
| A warmup that survives locally diverges at 8 GPUs | warmup configured in optimizer steps, and the scaled run has a *different target rate* - Section 2's `W` scales linearly with `eta_target` | re-derive `W` from the scaled rate; a warmup ported unchanged is a warmup under-sized |
| Accumulated run clips differently from the micro-batch run | clip-then-average shrinks the dominant micro-gradient twice (`0.770x` the norm, `6.7` deg off) | accumulate the raw (mean) gradient first, clip once on the result; log `clip_grad_norm_`'s returned pre-clip norm |
| LR schedule under accumulation ends its warmup "too early" | `LinearLR.total_iters` counts optimizer steps; accumulation divides them (`384 -> 48`) | multiply step-counted schedule parameters by the accumulation factor |
| Doubling GPUs buys no throughput end-to-end | batch already above the critical batch size: `S(B)` is flat, extra ranks idle in communication | measure `B_noise` for the workload first; below the knee, steps scale as `1/B` |
| The sqrt rule was assumed safe everywhere | sqrt respects the wall only while `eta0 * sqrt(k) < 2 / lambda_max` at *every phase* of training | check the endpoint against the tightest wall in the schedule (Section 5's R4/R5 contrast) |
| Dataset "shrank" after switching to accumulation | drop-last dropped the short final bucket (`1025` samples in `8 x 128`) | make the stream divisible, or weight the short bucket; mean-of-means is exact only on equal micro-batches |

## Summary

The linear scaling rule is one line with four pieces of fine print. The mechanism: batch averaging divides gradient-noise variance by `B` (`0.1767` observed against `0.1768` predicted), so the LR may grow with the batch - up to the wall `eta_max = 2 / lambda_max`, where the linear rule dies (`k >= 8` in the fence) and sqrt survives with its headroom spent on `6.60x` noise amplification. The stabilizer: warmup, sized not by taste but by `W > eta_target * lambda_early * t_sharp / 2` - where half the rule diverged `20/20` and twice the rule survived `20/20`. The bound: the critical batch size `S(B) = S_min * (1 + B_noise / B)`, whose knee marks where more machines stop buying steps. The fine print on accumulation: the gradient math is exact to `0.00e+00`, but optimizer-step counts (`384 -> 48`), warmup fractions (`2.6% -> 20.8%`), and clip order (`0.770x` the norm, `6.7` deg off) all diverge silently. And the campaign's ledger: same tokens, same `$238.10`, three different fates - the baseline that is safe and slow, the linear-with-warmup that is safe and 8x faster, the no-warmup that dies at step 2, and the k=32 linear whose endpoint `6.4` crossed the late wall `4.0` and killed a run that had already converged.

## References

### Related Minder Academy Documents

- [5401: Data Parallelism](./5401-Data-Parallelism.md) - DDP's all-reduce is a mean of per-rank grads; clip ordering composes with it
- [5403: Mixed Precision](./5403-Mixed-Precision.md) - loss scaling stabilizes fp16 gradients; it is not LR scaling
- [5404: Distributed Optimization](./5404-Distributed-Optimization.md) - ZeRO shards the optimizer state the scaled LR drives
- [5405: FSDP2 and torchao](./5405-FSDP2-and-torchao.md) - the sharding stack this lesson's rates run on top of
- [5501: Optimizer Variants](../5500-advanced-optimization/5501-Optimizer-Variants.md) - LARS and LAMB as optimizers: update rules and hyperparameters
- [5502: Learning Rate Scheduling](../5500-advanced-optimization/5502-Learning-Rate-Scheduling.md) - the schedule shapes the linear rule feeds
- [2402: Large-Scale Training](../../../phases/phase2-foundations/2400-pretraining/2402-Large-Scale-Training.md) - pretraining-scale training runs and their stability practices

### Primary Sources

- Goyal et al., "Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour" (arXiv: [1706.02677](https://arxiv.org/abs/1706.02677)) - the linear scaling rule and the warmup scheme this lesson's Section 1 and 2 mechanics come from.
- McCandlish, Kaplan, Amodei, "An Empirical Model of Large-Batch Training" (arXiv: [1812.06162](https://arxiv.org/abs/1812.06162)) - the gradient noise scale and the critical batch size curve of Section 3.
- Smith et al., "Don't Decay the Learning Rate, Increase the Batch Size" (arXiv: [1711.00489](https://arxiv.org/abs/1711.00489), ICLR 2018) - the LR/batch equivalence (`B` inversely proportional to `eta`; `B` proportional to `1/(1-m)`).
- You, Gitman, Ginsburg, "Large Batch Training of Convolutional Networks" (arXiv: [1708.03888](https://arxiv.org/abs/1708.03888)) - LARS and the layer-wise trust ratio.
- You et al., "Large Batch Optimization for Deep Learning: Training BERT in 76 minutes" (arXiv: [1904.00962](https://arxiv.org/abs/1904.00962), ICLR 2020) - LAMB, batch 32,868, the TPUv3 Pod result.
- PyTorch docs: [`LinearLR`](https://docs.pytorch.org/docs/stable/generated/torch.optim.lr_scheduler.LinearLR.html) - `start_factor`, `end_factor`, and `total_iters` counting optimizer steps.
- PyTorch docs: [`clip_grad_norm_`](https://docs.pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html) - returns the total norm of the parameters *before* clipping.
- PyTorch docs: [DistributedDataParallel](https://docs.pytorch.org/docs/stable/generated/torch.nn.parallel.DistributedDataParallel.html) - the all-reduce that averages gradients across ranks.

---

## Next Steps

- Next Module: **[5500: Advanced Optimization](../5500-advanced-optimization/README.md)**
- Continue with: **[5502: Learning Rate Scheduling](../5500-advanced-optimization/5502-Learning-Rate-Scheduling.md)** - the schedule shapes (cosine, step, polynomial) that ride on top of the rate this lesson scales
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Reproduce the campaign at your own scale: take a config that converges on one GPU, scale the world, re-derive the warmup from Section 2's rule, and check the schedule's *endpoint* - not its shape - against the wall before the first launch.
