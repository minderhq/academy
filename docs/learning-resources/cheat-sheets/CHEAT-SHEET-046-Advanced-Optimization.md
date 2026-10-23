---
Document ID: CHEAT-SHEET-046
Title: "CHEAT-SHEET-046: Advanced Optimization - the Optimizer Memory Ledger, the Schedule Arc, and the Failure Toolbox"
Last Updated: 2026-10-23
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'optimization', 'adamw', 'scheduling']
---

# CHEAT-SHEET-046: Advanced Optimization - the Optimizer Memory Ledger, the Schedule Arc, and the Failure Toolbox

The advanced-optimization surface is phase5-finetuning's 5500-advanced-optimization track - 5501 Optimizer Variants, 5502 Learning Rate Scheduling and 5503 Advanced Techniques - three modules with no sheet anywhere in the track (scope scan: CHEAT-SHEET-045 owns the data-and-fleet layer beside it, what the model trains on and where the training physically happens, and CHEAT-SHEET-016 owns the PEFT adapter above; nothing owned the per-step stack itself). This sheet takes that stack: what actually moves the weights (the optimizer and the 16 bytes per parameter it carries), when the step size moves (warmup, the decay arc, the layer-wise split), and which tool repairs which failure (norm clipping, gradient accumulation, SAM, the LR range test) - closing the 5500 track.

The sheet runs as seven priced exhibits: the optimizer memory ledger and the variants that shrink it (F1), Adam's scale-free first step and the L2-coupling census (F2), the schedule arc from linear to cosine plus the layer-wise split (F3), clipping and accumulation's three laws (F4), SAM's flat-minima search with its two canonical bugs (F5), the LR range test on a closed-form loss curve (F6), and the memory bill with the total-steps identity (F7). Every number below is printed by the canonical fence at the bottom of the page: the full 177-line stdlib fence reproduces all seven in closed form - no RNG anywhere - and its 63-line output sits frozen below it byte-for-byte.

## The Optimizer Memory Ledger - 16N and the Variants That Shrink It

The ledger counts 16 bytes for every trained parameter: weights bf16 at 2N and gradients bf16 at 2N are the training state itself, while the fp32 master weights at 4N and the two Adam moments m and v at 4N each are optimizer overhead - 12N against 4N, three times what the weights cost. At 7B parameters that is 112.0 GB total with 84.0 GB of overhead, and at 70B it is 1120.0 GB - multi-node territory no single card touches. The variant list is a menu of ways to attack the 12N while leaving the 4N alone: quantized moments (AdamW8bit at ~14.0 GB, PagedAdamW8bit the same but paged out to CPU on spikes), sign-only updates (Lion at 28.0 GB, it keeps m and drops v entirely), factored second moments (Adafactor at ~56.0 GB), and shrinking the trainable set itself (LoRA - the optimizer carries moments only for the adapter, 0.84 GB at 7B on the frozen base).

| Variant | Overhead at 7B | The trick | The cost | Ships as |
| --- | --- | --- | --- | --- |
| AdamW fp32 | 84.0 GB (12N) | none - the reference point | the whole bill | torch.optim.AdamW |
| AdamW8bit | ~14.0 GB (2N) | m and v quantized to 8 bits | small moment noise | bnb.optim.AdamW8bit |
| PagedAdamW8bit | ~14.0 GB (2N), paged | 8-bit moments, pages state to CPU on spikes | paging latency at the spike | bnb.optim.PagedAdamW8bit |
| Lion | 28.0 GB (4N) | keeps only m, the step is sign(m) | no second moment, retuned lr and wd | lion-pytorch |
| Adafactor | ~56.0 GB (8N) | v factored to a rank-1 pair | approximate v, T5-lineage tuning | transformers.Adafactor |

```text
The optimizer's state is three times the weights it trains: weights 2N and
grads 2N are the training state, master 4N plus m 4N plus v 4N are overhead -
16N per parameter, 84.0 GB of rent on 14.0 GB of weights at 7B.
```

## Adam Versus AdamW - the Scale-Free Step and the Decay That Lives Outside

Adam's first step is scale-free: m and v start at zero, the bias correction at t=1 makes m_hat = g and v_hat = g squared, so the update is lr * g / (norm(g) + eps) - unit direction, lr magnitude, for ANY gradient. The census prices it: gradient norm 0.3 and gradient norm 30.0 both land 0.00010000, exactly 1.0 x lr. That machinery is why weight decay has to live outside it: Adam+L2 pushes g + lambda * theta through the same normalization, so the decay's effective strength becomes lr * lambda * theta/norm(g) - 2.000e-07 per step at gradient norm 5.0 against 2.000e-05 at gradient norm 0.05, a 0.0100 ratio between the two. L2 scales itself with the gradient it rides: big-gradient coordinates are barely regularized. AdamW subtracts lr * lambda * theta AFTER the adaptive update: 1.000e-06 for every parameter, ratio 1.0000, uniform by construction.

| Aspect | Adam + L2 | AdamW (decoupled) |
| --- | --- | --- |
| Where decay lives | inside g, rides the m/v normalization | after the update, direct subtraction |
| Effective strength | lr * lambda * theta/norm(g): 2.000e-07 at norm 5.0, 2.000e-05 at 0.05 | lr * lambda = 1.000e-06, every parameter |
| Consequence | regularization shrinks where gradients are big | uniform decay by construction |

## The Schedule Arc - Linear, Cosine, and the Layer-Wise Split

Both arcs ramp linearly to the peak over 500 warmup steps and then decay across the remaining 9500 of T = 10000 - they differ in what the budget buys. Linear spends it evenly and hits zero: 0.7895 at step 2500, 0.0001 at step 9999. Cosine spends it near the peak: 0.9051 at step 2500 and floors at min_ratio 0.1 instead of 0 - 0.1000 at step 9999. The linger census turns that into a number: linear holds factor >= 0.9 for 951 post-warmup steps (10.01%), cosine for 2056 (21.64%) - 2.16x the peak linger, which is why mid-training quality prefers cosine and short runs take linear. Beneath the arc sits the layer-wise split: one base lr 5.000e-05 with decay 0.95 across 12 layers puts the embeddings at 2.702e-05 (0.5404 of the top); decay 0.9 puts them at 1.412e-05 (0.2824) - lower layers settle first, embeddings and head last.

| Task | Arc | Why |
| --- | --- | --- |
| Fine-tune | warmup then linear to zero | short run, the endgame wants a quiet lr |
| Pretrain | warmup then cosine with a floor | long run, mid-training wants the peak linger |
| Either | min_ratio 0.1 on cosine | cosine never touches 0: final factor 0.1000 vs linear 0.0001 |

| Regime | Warmup size | Reason |
| --- | --- | --- |
| Fine-tune | 100-500 steps | optimizer statistics form fast on already-trained weights |
| Pretrain | 0.5-2% of total steps | longer runway for m and v on fresh weights |
| Either | linear ramp | the ramp shape is never the interesting part |

```text
Warmup fixes the optimizer's statistics, not the loss: the first step is
scale-free and correct from t=1. The decay is a budget - linear spends it
evenly, cosine lingers at the peak 2.16x longer: 2056 steps above 0.9 vs 951.
```

## The Failure Toolbox - Clipping Preserves Direction, Accumulation Has Three Laws

Gradient clipping rescales the whole gradient vector by one scalar, min(1, C/norm(g)): on the gradient [10.0, 0.1, 0.1, 0.1] with C = 1.0 the norm is 10.0015 and the scale is 0.09999 - the cosine between original and clipped vector is 1.000000, direction kept, only magnitude trimmed. Value-clipping the same vector at 0.1 flattens it to [0.1, 0.1, 0.1, 0.1] and the cosine collapses to 0.5149 - the outlier's direction is erased. That is the whole argument for clip_grad_norm_ over per-element clamps. Gradient accumulation multiplies the batch: 4 micro-batches x 8 accumulation steps = 32 effective. It carries three laws: divide the loss by accum_steps before backward, tick the scheduler once per optimizer step and never per micro batch, and flush the tail - 101 batches give 12 full windows plus a 5-batch remainder, the naive loop silently drops 5/101 = 4.95% of every epoch, and the undivided-loss bug sums the window into a gradient 8x the average, effective lr x8.

| Tool | What it touches | What it costs |
| --- | --- | --- |
| clip_grad_norm_ | the global norm, one scale | cosine 1.000000 - direction preserved |
| Per-element clamp | every coordinate at its bound | cosine 0.5149 on the outlier vector - direction erased |
| Adaptive clipping (AGC) | each unit's norm against its weight norm | no fixed threshold to tune, more compute per step |

| Law | Statement | Breaking it |
| --- | --- | --- |
| Divide | loss / accum_steps before backward | gradient 8x the average, effective lr x8 |
| Tick | scheduler.step() once per optimizer step | the arc finishes 8x early, floors mid-run |
| Flush | run the 5-batch remainder as one last window | 4.95% of every epoch silently dropped |

```text
The canonical loop order: for each micro batch, forward and backward on
(loss / accum_steps); after the LAST micro batch, clip the accumulated
gradient once, optimizer.step(), zero_grad(set_to_none=True), then
scheduler.step() - one tick per optimizer step, never per micro batch.
```

## SAM - the Flat-Minima Search and Its Two Canonical Bugs

SAM seeks flat minima: perturb w to the edge of its rho-ball along its own gradient, w' = w + rho * g/norm(g) with the norm taken GLOBALLY, then step using the gradient at w'. The anisotropic toy prices the mechanics: a = [1.0, 25.0], w0 = [0.0, 2.0], mu = [3.0, -1.0], rho = 0.05 gives g = [-3.0000, 75.0000], norm 75.0600, perturbation e_w = [-0.00200, 0.04996], and the correct second step lands w1 = [0.3002, -5.6249]. Two canonical bugs. Per-tensor rho on tensor norms [0.1, 10.0] gives both tensors a perturbation of 0.05 where the global rule gives [0.00050, 0.05000] - the small tensor over-perturbed 100.00x, because the rho-neighborhood is global. And the missing zero_grad between the two passes trains the SUM: g+g' = [-6.0020, 151.2490] with |g+g'|/|g'| = 1.9836 at cosine 1.00000 - the step lands at w1 = [0.6002, -13.1249], twice the intended distance in exactly the same direction.

## The LR Range Test - Scouting the Peak Before the Run

The range test finds the peak before the run does: ramp the lr exponentially from 1e-7 to 10.0 over 100 iterations and record the loss at each. On the closed-form curve loss(L) = 2.2 + 1.2 * exp(-L/2e-4) + 3.0 * (L/3e-3)^6, the steepest descent sits at lr 2.057e-04 - the peak-LR candidate. The curve bottoms at 2.2122 at lr 1.097e-03, and the ceiling, where loss exceeds the minimum by 0.05, arrives at 1.592e-03 - past that the sixth-power term takes over. The steep region's upper edge, where the exponential residual drops below 0.12, is 5.214e-04: the OneCycle max_lr. The wiring falls out of the same numbers - start at max_lr/25 = 2.086e-05, end at start/1e4 = 2.086e-09.

## The Memory Bill and the Total-Steps Identity

The bill decides the route: full AdamW on a 7B is 112.0 GB - 32.0 GB over an 80 GB card; the 8-bit route (2+2+4+~2 = 10N) lands at 70.0 GB with 10.0 GB headroom; LoRA carries 0.84 GB of optimizer state on the frozen base. The total-steps identity decides the schedule's length: 101 batches, accumulation 8, 3 epochs - the flush makes it 12+1 = 13 windows per epoch, x3 = 39 real optimizer steps. The naive int(303/8) = 37 misses 2 steps the schedule never planned, and a linear schedule sits at lr 0 for exactly those steps - the endgame the model needed, spent at zero.

```text
Pick the optimizer by its ledger, the schedule by its arc: 8-bit moments or
LoRA when the 12N rent does not fit, cosine when mid-training quality matters,
linear when the run is short - and total_steps is (full_windows + 1) x epochs.
```

## The Canonical Fence

The seven exhibits reproduce from one stdlib script - closed form throughout, no RNG, byte-identical on every run:

```python
"""CHEAT-SHEET-046 canonical fence: Advanced Optimization - the Optimizer
Memory Ledger, the Schedule Arc, and the Failure Toolbox.

Seven priced exhibits, stdlib only, fully closed-form (no RNG):
F1 the optimizer memory ledger (16N and the variants that shrink it)
F2 Adam's scale-free first step and the L2-coupling census
F3 the schedule arc: linear vs cosine and the layer-wise split
F4 clipping preserves direction; accumulation's three laws
F5 SAM: the global-norm law and the two canonical bugs
F6 the LR range test on a closed-form loss curve
F7 the memory bill and the total-steps identity
"""
import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

B1 = 0.9
B2 = 0.999
EPS = 1e-8

print("F1 the optimizer memory ledger: 16N and the variants that shrink it")
N = 7_000_000_000
rows = [("weights bf16", 2), ("gradients bf16", 2), ("master weights fp32", 4),
        ("adam m fp32", 4), ("adam v fp32", 4)]
tot = sum(b for _, b in rows)
for name, b in rows:
    print(f"  {name:<22} {b}N bytes/param -> {b * 7.0:6.1f} GB at 7B")
print(f"  total {tot}N = {tot * 7.0:.1f} GB at 7B | optimizer overhead {tot - 4}N = {(tot - 4) * 7.0:.1f} GB")
print(f"  70B model: {tot * 70.0:.1f} GB - multi-node territory")
print("  overhead at 7B by variant: AdamW fp32 84.0 | AdamW8bit ~14.0 | "
      "PagedAdamW8bit ~14.0 paged | Lion 28.0 | Adafactor ~56.0")
print()

print("F2 Adam's scale-free first step and the L2-coupling census")
lr = 1e-4
for g in (0.3, 30.0):
    m = (1 - B1) * g
    v = (1 - B2) * g * g
    m_hat = m / (1 - B1)
    v_hat = v / (1 - B2)
    step = lr * m_hat / (math.sqrt(v_hat) + EPS)
    print(f"  first step, |g|={g:<5}: update {step:.8f} = {step / lr:.8f} x lr "
          "- scale-free at t=1")
LAM = 0.01
THETA = 1.0
for g in (5.0, 0.05):
    dec_l2 = lr * LAM * THETA / g
    print(f"  Adam+L2 |g|={g:<5}: L2 rides Adam's normalization -> "
          f"effective decay lr*lambda*theta/|g| = {dec_l2:.3e} per step")
dA = lr * LAM * THETA / 5.0
dB = lr * LAM * THETA / 0.05
print(f"  decay ratio big/small grad: {dA / dB:.4f} - L2 scales itself with |g|")
print(f"  AdamW both params: lr*lambda = {lr * LAM:.3e}  ratio 1.0000 "
      "- uniform by construction")
print()

print("F3 the schedule arc: linear vs cosine and the layer-wise split")
WARM, TOTAL, MINR = 500, 10_000, 0.1


def lin(step):
    if step < WARM:
        return step / WARM
    return max(0.0, 1.0 - (step - WARM) / (TOTAL - WARM))


def cos_step(step):
    if step < WARM:
        return step / WARM
    p = (step - WARM) / (TOTAL - WARM)
    return MINR + (1.0 - MINR) * 0.5 * (1.0 + math.cos(math.pi * p))


for s in (0, 250, 499, 500, 2500, 5000, 7500, 9500, 9999):
    print(f"  step {s:>5}: linear {lin(s):.4f}  cosine {cos_step(s):.4f}")
lin_ling = sum(1 for s in range(WARM, TOTAL) if lin(s) >= 0.9)
cos_ling = sum(1 for s in range(WARM, TOTAL) if cos_step(s) >= 0.9)
print(f"  linger at factor >= 0.9: linear {lin_ling} steps ({lin_ling / 95:.2f}%)  "
      f"cosine {cos_ling} ({cos_ling / 95:.2f}%) - cosine holds the peak {cos_ling / lin_ling:.2f}x longer")
print(f"  final factor: linear {lin(TOTAL - 1):.4f} vs cosine {cos_step(TOTAL - 1):.4f} (the floor)")
base_lr, NL = 5e-5, 12
for dec in (0.95, 0.9):
    emb = base_lr * dec ** NL
    print(f"  LLRD decay={dec}: top {base_lr:.3e}  embeddings {emb:.3e}  "
          f"(embedding/top {emb / base_lr:.4f})")
print()

print("F4 clipping preserves direction; accumulation's three laws")
g = [10.0, 0.1, 0.1, 0.1]
gn = math.sqrt(sum(x * x for x in g))
scale = 1.0 / gn
nclip = [x * scale for x in g]
vclip = [max(-0.1, min(0.1, x)) for x in g]


def cos(u, w):
    nu = math.sqrt(sum(x * x for x in u))
    nw = math.sqrt(sum(x * x for x in w))
    return sum(a * b for a, b in zip(u, w)) / (nu * nw)


print(f"  grad {g} global norm {gn:.4f}")
print(f"  norm-clip 1.0: scale {scale:.5f} -> {['%.4f' % x for x in nclip]} "
      f"cosine {cos(g, nclip):.6f}")
print(f"  value-clip 0.1: -> {vclip} cosine {cos(g, vclip):.4f} "
      "- the outlier's direction is erased")
micro, acc, batches = 4, 8, 101
full, rem = batches // acc, batches % acc
print(f"  accumulation: {micro} x {acc} = {micro * acc} effective batch; "
      f"{batches} batches -> {full} windows + {rem} remainder")
print(f"  naive loop drops {rem}/{batches} = {rem / batches * 100:.2f}% of every epoch; "
      f"undivided loss sums the window -> gradient {acc}x the average, "
      f"effective lr x{acc}")
print()

print("F5 SAM: the global-norm law and the two canonical bugs")
a = [1.0, 25.0]
w = [0.0, 2.0]
mu = [3.0, -1.0]
rho, lr2 = 0.05, 0.1
grad = [a[i] * (w[i] - mu[i]) for i in range(2)]
gn5 = math.sqrt(sum(x * x for x in grad))
ew = [rho * x / gn5 for x in grad]
wp = [w[i] + ew[i] for i in range(2)]
gp = [a[i] * (wp[i] - mu[i]) for i in range(2)]
w1 = [w[i] - lr2 * gp[i] for i in range(2)]
total = [grad[i] + gp[i] for i in range(2)]
w1b = [w[i] - lr2 * total[i] for i in range(2)]
print(f"  anisotropic toy a={a} w0={w} mu={mu} rho={rho}")
print(f"  g={['%.4f' % x for x in grad]} |g|={gn5:.4f} -> e_w={['%.5f' % x for x in ew]}")
print(f"  correct SAM step on g': w1={['%.4f' % x for x in w1]}")
print(f"  buggy sum g+g'={['%.4f' % x for x in total]}: w1={['%.4f' % x for x in w1b]}")
print(f"  |g+g'|/|g'| = {math.sqrt(sum(x * x for x in total)) / math.sqrt(sum(x * x for x in gp)):.4f}"
      f"  cosine {cos(total, gp):.5f} - the missing zero_grad trains the SUM")
norms = [0.1, 10.0]
gnt = math.sqrt(sum(x * x for x in norms))
eg = [rho * n / gnt for n in norms]
ep = [rho] * 2
print(f"  per-tensor vs global: norms {norms} -> global e={['%.5f' % x for x in eg]} "
      f"per-tensor e={ep}")
print(f"  small tensor over-perturbed {ep[0] / eg[0]:.2f}x by per-tensor scaling - "
      "the rho-neighborhood is GLOBAL")
print()

print("F6 the LR range test on a closed-form loss curve")
INIT, FINAL, NITER = 1e-7, 10.0, 100
mult = (FINAL / INIT) ** (1 / (NITER - 1))
lrs = [INIT * mult ** i for i in range(NITER)]
losses = [2.2 + 1.2 * math.exp(-L / 2e-4) + 3.0 * (L / 3e-3) ** 6 for L in lrs]
drops = [(losses[i - 1] - losses[i], lrs[i]) for i in range(1, NITER)]
steepest = max(drops)[1]
min_i = losses.index(min(losses))
ceiling = next(lrs[i] for i in range(min_i, NITER) if losses[i] > min(losses) + 0.05)
max_lr = next(L for L, res in zip(lrs, [1.2 * math.exp(-L / 2e-4) for L in lrs])
              if res < 0.12)
print(f"  ramp 1e-7 -> 10.0 over {NITER} iters; loss(L) = 2.2 + 1.2*exp(-L/2e-4) "
      "+ 3.0*(L/3e-3)^6")
print(f"  steepest descent at lr {steepest:.3e} - the peak-LR candidate")
print(f"  loss minimum {min(losses):.4f} at {lrs[min_i]:.3e}; ceiling (min+0.05) at {ceiling:.3e}")
print(f"  steep region's upper edge (exp-residual < 0.12): max_lr {max_lr:.3e}")
print(f"  OneCycle wiring: start max_lr/25 = {max_lr / 25:.3e}, "
      f"end start/1e4 = {max_lr / 25 / 1e4:.3e}")
print()

print("F7 the memory bill and the total-steps identity")
print(f"  7B full AdamW: {tot * 7.0:.1f} GB - {tot * 7.0 - 80.0:.1f} GB over an 80 GB card")
print(f"  7B 8-bit route (2+2+4+~2 = 10N): 70.0 GB -> {80.0 - 70.0:.1f} GB headroom")
print(f"  7B LoRA (trainable ~N/100): optimizer overhead {84.0 / 100:.2f} GB on the frozen base")
ep3 = 3
actual = (full + 1) * ep3
naive = batches * ep3 // acc
print(f"  total-steps identity: {batches} batches, accum {acc}, {ep3} epochs -> "
      f"actual {full}+1 remainder = {full + 1}/epoch, x{ep3} = {actual}")
print(f"  naive int({batches * ep3}/{acc}) = {naive} -> {actual - naive} steps the schedule "
      "never planned: linear sits at lr 0 for them")
print("FENCE-046-OK")
```

Its output, frozen byte-for-byte:

```text
F1 the optimizer memory ledger: 16N and the variants that shrink it
  weights bf16           2N bytes/param ->   14.0 GB at 7B
  gradients bf16         2N bytes/param ->   14.0 GB at 7B
  master weights fp32    4N bytes/param ->   28.0 GB at 7B
  adam m fp32            4N bytes/param ->   28.0 GB at 7B
  adam v fp32            4N bytes/param ->   28.0 GB at 7B
  total 16N = 112.0 GB at 7B | optimizer overhead 12N = 84.0 GB
  70B model: 1120.0 GB - multi-node territory
  overhead at 7B by variant: AdamW fp32 84.0 | AdamW8bit ~14.0 | PagedAdamW8bit ~14.0 paged | Lion 28.0 | Adafactor ~56.0

F2 Adam's scale-free first step and the L2-coupling census
  first step, |g|=0.3  : update 0.00010000 = 0.99999997 x lr - scale-free at t=1
  first step, |g|=30.0 : update 0.00010000 = 1.00000000 x lr - scale-free at t=1
  Adam+L2 |g|=5.0  : L2 rides Adam's normalization -> effective decay lr*lambda*theta/|g| = 2.000e-07 per step
  Adam+L2 |g|=0.05 : L2 rides Adam's normalization -> effective decay lr*lambda*theta/|g| = 2.000e-05 per step
  decay ratio big/small grad: 0.0100 - L2 scales itself with |g|
  AdamW both params: lr*lambda = 1.000e-06  ratio 1.0000 - uniform by construction

F3 the schedule arc: linear vs cosine and the layer-wise split
  step     0: linear 0.0000  cosine 0.0000
  step   250: linear 0.5000  cosine 0.5000
  step   499: linear 0.9980  cosine 0.9980
  step   500: linear 1.0000  cosine 1.0000
  step  2500: linear 0.7895  cosine 0.9051
  step  5000: linear 0.5263  cosine 0.5872
  step  7500: linear 0.2632  cosine 0.2452
  step  9500: linear 0.0526  cosine 0.1061
  step  9999: linear 0.0001  cosine 0.1000
  linger at factor >= 0.9: linear 951 steps (10.01%)  cosine 2056 (21.64%) - cosine holds the peak 2.16x longer
  final factor: linear 0.0001 vs cosine 0.1000 (the floor)
  LLRD decay=0.95: top 5.000e-05  embeddings 2.702e-05  (embedding/top 0.5404)
  LLRD decay=0.9: top 5.000e-05  embeddings 1.412e-05  (embedding/top 0.2824)

F4 clipping preserves direction; accumulation's three laws
  grad [10.0, 0.1, 0.1, 0.1] global norm 10.0015
  norm-clip 1.0: scale 0.09999 -> ['0.9999', '0.0100', '0.0100', '0.0100'] cosine 1.000000
  value-clip 0.1: -> [0.1, 0.1, 0.1, 0.1] cosine 0.5149 - the outlier's direction is erased
  accumulation: 4 x 8 = 32 effective batch; 101 batches -> 12 windows + 5 remainder
  naive loop drops 5/101 = 4.95% of every epoch; undivided loss sums the window -> gradient 8x the average, effective lr x8

F5 SAM: the global-norm law and the two canonical bugs
  anisotropic toy a=[1.0, 25.0] w0=[0.0, 2.0] mu=[3.0, -1.0] rho=0.05
  g=['-3.0000', '75.0000'] |g|=75.0600 -> e_w=['-0.00200', '0.04996']
  correct SAM step on g': w1=['0.3002', '-5.6249']
  buggy sum g+g'=['-6.0020', '151.2490']: w1=['0.6002', '-13.1249']
  |g+g'|/|g'| = 1.9836  cosine 1.00000 - the missing zero_grad trains the SUM
  per-tensor vs global: norms [0.1, 10.0] -> global e=['0.00050', '0.05000'] per-tensor e=[0.05, 0.05]
  small tensor over-perturbed 100.00x by per-tensor scaling - the rho-neighborhood is GLOBAL

F6 the LR range test on a closed-form loss curve
  ramp 1e-7 -> 10.0 over 100 iters; loss(L) = 2.2 + 1.2*exp(-L/2e-4) + 3.0*(L/3e-3)^6
  steepest descent at lr 2.057e-04 - the peak-LR candidate
  loss minimum 2.2122 at 1.097e-03; ceiling (min+0.05) at 1.592e-03
  steep region's upper edge (exp-residual < 0.12): max_lr 5.214e-04
  OneCycle wiring: start max_lr/25 = 2.086e-05, end start/1e4 = 2.086e-09

F7 the memory bill and the total-steps identity
  7B full AdamW: 112.0 GB - 32.0 GB over an 80 GB card
  7B 8-bit route (2+2+4+~2 = 10N): 70.0 GB -> 10.0 GB headroom
  7B LoRA (trainable ~N/100): optimizer overhead 0.84 GB on the frozen base
  total-steps identity: 101 batches, accum 8, 3 epochs -> actual 12+1 remainder = 13/epoch, x3 = 39
  naive int(303/8) = 37 -> 2 steps the schedule never planned: linear sits at lr 0 for them
FENCE-046-OK
```

## Known Failure Modes

| Trap | What it costs | The honest move |
| --- | --- | --- |
| L2 regularization inside Adam | decay rides the normalization: 2.000e-07 per step at norm 5.0 vs 2.000e-05 at 0.05 | decouple it: AdamW subtracts lr * lambda * theta after the update |
| scheduler.step() per micro batch | the arc finishes 8x early and floors mid-run | tick once per optimizer step, after the flush |
| Per-element value clipping | cosine collapses to 0.5149 on the outlier vector - direction erased | clip_grad_norm_: one scale, cosine 1.000000 |
| total_steps = int(303/8) | 39 real steps vs 37 planned: linear sits at lr 0 for the last 2 | compute (12 + 1) x 3 = 39 with the remainder window in |
| Per-tensor rho in SAM | small tensor over-perturbed 100.00x | the rho-neighborhood is global: normalize by the total norm |
| Missing zero_grad between SAM passes | trains the SUM at 1.9836x the perturbed norm, same direction | both zero_grad calls are load-bearing |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| First step already at full size | scale-free: update = lr * g / (norm(g) + eps) for any gradient | expected, not a fault - warmup shapes the loss, not the step |
| Loss flattens a quarter of the way in | linear already at 0.7895 while cosine holds 0.9051 | cosine with min_ratio 0.1 when mid-run quality matters |
| Gradient report shows norms 8x too big | undivided loss under accumulation | divide by accum_steps before backward() |
| Last epoch trains at lr 0 | total_steps missing the remainder window: 37 vs 39 | (full_windows + 1) x epochs, remainder included |
| Embeddings overfit while the body holds | one lr for 12 depths: embeddings deserve 0.5404x at decay 0.95 | layer-wise decay 0.95 fine-tune, 0.9 aggressive |
| Small tensors jitter under SAM | per-tensor rho over-perturbs them 100.00x | global-norm perturbation |

## Quick Reference For

- [Module 5501: Optimizer Variants](../../phases/phase5-finetuning/5500-advanced-optimization/5501-Optimizer-Variants.md) - the optimizer zoo and the scale-free step this sheet's ledger prices.
- [Module 5502: Learning Rate Scheduling](../../phases/phase5-finetuning/5500-advanced-optimization/5502-Learning-Rate-Scheduling.md) - the cosine floor, the remainder window and layer-wise decay this sheet schedules.
- [Module 5503: Advanced Optimization Techniques](../../phases/phase5-finetuning/5500-advanced-optimization/5503-Advanced-Techniques.md) - the accumulation, norm-clip and per-tensor rho fixes this sheet prices.
- [Module 5403: Mixed Precision Training](../../phases/phase5-finetuning/5400-distributed-training/5403-Mixed-Precision.md) - the mixed-precision sandwich these optimizers run on.
