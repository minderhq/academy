---
Document ID: 5503
Title: "5503: Advanced Optimization Techniques"
Phase: 5
Module: 5500
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['optimization', 'training', 'gradient-clipping', 'sam', 'memory']
---

# 5503: Advanced Optimization Techniques

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [A Map of the Toolbox](#a-map-of-the-toolbox)
- [Stability: Gradient Clipping](#stability-gradient-clipping)
- [Memory: Gradient Accumulation](#memory-gradient-accumulation)
- [Memory: Gradient Checkpointing](#memory-gradient-checkpointing)
- [Regularization in One Screen](#regularization-in-one-screen)
- [Flat Minima: SAM](#flat-minima-sam)
- [Second-Order Optimizers: The Honest Status](#second-order-optimizers-the-honest-status)
- [Scouting: The LR Range Test](#scouting-the-lr-range-test)
- [Best Practices](#best-practices)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Choose between norm clipping, value clipping, and adaptive gradient clipping from the failure you are actually seeing
- Write a gradient-accumulation loop that handles the remainder batch, AMP scaling, and scheduler placement correctly
- Enable gradient checkpointing with the non-reentrant API and predict its memory/compute trade
- Implement SAM correctly — global-norm perturbation, zero-grad between passes — and say when its 2x cost pays
- Describe what Sophia computes (diagonal Hessian estimate, clipped update) and why it has not displaced AdamW

---

## Abstract

Beyond optimizer choice ([5501](./5501-Optimizer-Variants.md)) and schedules ([5502](./5502-Learning-Rate-Scheduling.md)) sits a toolbox of techniques that fix specific failures: clipping tames exploding gradients, accumulation and checkpointing buy batch size and depth with different currencies, SAM seeks flat minima for generalization. Each tool has a precise failure it addresses and a precise cost — and each has a canonical wrong implementation circulating online (the SAM loop that sums gradients across its two backward passes is the classic). This lesson builds the correct versions, names the trade for each, and closes with the honest 2026 status of second-order optimizers.

## A Map of the Toolbox

```text
FAILURE you have          TOOL this lesson covers
------------------------  ----------------------------------------
gradients exploding       norm / value / adaptive clipping
batch too big for HBM     gradient accumulation (grads, not acts)
activations blow memory   gradient checkpointing (acts, not grads)
overfitting a fine-tune   decoupled weight decay, dropout placement
test loss > train loss    SAM: optimize the flat basin, not the point
LR guesswork              LR range test (run BEFORE the real run)
```

## Stability: Gradient Clipping

### Clip by Norm (the default)

Scales the whole gradient so its global L2 norm is at most `max_norm`:

```python
import torch

optimizer.zero_grad(set_to_none=True)
loss.backward()

torch.nn.utils.clip_grad_norm_(
    model.parameters(), max_norm=1.0, norm_type=2.0,
)                       # rescale if global norm exceeds 1.0

optimizer.step()
```

```text
- transformers + AdamW: max_norm=1.0 is the community default,
  used even when nothing explodes - it costs nothing when the
  norm is small and caps the damage when it is not
- with AMP FP16: unscale_ BEFORE clip (5403/5502) - clipping
  scaled gradients clips against the wrong norm
- log the PRE-clip norm: it is a cheap training-health signal
  (a slowly rising norm = instability forming; a spike = find
  the bad batch or lower the LR)
```

### Clip by Value

```python
torch.nn.utils.clip_grad_value_(model.parameters(), clip_value=0.5)
# every element clamped to [-0.5, 0.5] - changes the DIRECTION,
# norm clipping preserves it
```

Value clipping distorts the gradient direction (every element saturates independently), which is why it lost to norm clipping everywhere except legacy RNN recipes, where it was the standard.

### Adaptive Gradient Clipping (AGC)

AGC (Brock et al., 2021, for training CNNs *without* normalization layers) bounds each weight **unit's** gradient relative to that unit's weight norm — the clip threshold adapts per unit instead of being global:

```python
@torch.no_grad()
def agc(parameters, clip_factor=1e-2, eps=1e-3):
    """Unit-wise AGC: clip each row/unit's grad norm to
    clip_factor * that unit's weight norm."""
    for p in parameters:
        if p.grad is None:
            continue
        dims = tuple(range(1, p.dim()))          # per-unit norms
        w_norm = torch.linalg.norm(p, dim=dims, keepdim=True)
        g_norm = torch.linalg.norm(p.grad, dim=dims, keepdim=True)
        scale = (clip_factor * w_norm / (g_norm + eps)).clamp(max=1.0)
        p.grad.mul_(scale)
```

```text
Scope note: AGC exists because nets without BatchNorm/LayerNorm
produce occasional huge unit-wise gradients. Transformer
fine-tuning already has LayerNorm + global norm clipping -
AGC is for from-scratch norm-free architectures, not a
drop-in upgrade for your LLM run.
```

## Memory: Gradient Accumulation

Simulates an effective batch of `micro_batch × accum_steps × world_size` by summing micro-batch gradients before stepping:

```python
accum_steps = 8
optimizer.zero_grad(set_to_none=True)

for step, (x, y) in enumerate(loader, 1):
    with torch.autocast("cuda", dtype=torch.bfloat16):    # 5403
        loss = criterion(model(x), y) / accum_steps       # average,
                                                          # not sum
    scaler.scale(loss).backward()                         # accumulates

    if step % accum_steps == 0:
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(optimizer)
        scaler.update()
        scheduler.step()              # per OPTIMIZER step (5502)
        optimizer.zero_grad(set_to_none=True)

# remainder: flush the partial window at epoch end so the last
# few batches are not silently dropped
if len(loader) % accum_steps:
    scaler.unscale_(optimizer)
    scaler.step(optimizer)
    scaler.update()
    scheduler.step()
    optimizer.zero_grad(set_to_none=True)
```

```text
The three things every accumulation loop must get right
1. divide the LOSS by accum_steps - backward() ADDS into
   .grad, so the division turns the sum into an average and
   keeps the gradient scale (and clip threshold) meaningful
2. scheduler.step() fires once per optimizer step, not per
   micro-batch - otherwise the schedule races accum_steps
   times faster than the total_steps you declared (5502)
3. handle the remainder window - the naive
   `if (i+1) % accum == 0` pattern drops len(loader) % accum
   batches every epoch without a word of warning
```

## Memory: Gradient Checkpointing

Trades recompute for memory: discard intermediate activations in the forward pass, recompute them during backward. Peak activation memory drops toward "one layer's worth" while the step gets ~30-50% slower.

```python
import torch.nn as nn
from torch.utils.checkpoint import checkpoint

class CheckpointedBlocks(nn.Module):
    def __init__(self, blocks):
        super().__init__()
        self.blocks = blocks

    def forward(self, x):
        for i, block in enumerate(self.blocks):
            # checkpoint every block; non-reentrant API
            x = checkpoint(block, x, use_reentrant=False)
        return x
```

```text
use_reentrant=False - always, in modern PyTorch
- works with frozen inputs / PEFT setups (reentrant requires at
  least one input with requires_grad, which breaks
  LoRA-on-frozen-backbone runs; HF exposes
  model.enable_input_require_grads() as the workaround when
  you are stuck on reentrant)
- supports rng_state preservation: dropout masks are identical
  between forward and recompute (preserve_rng_state=True by
  default) - disable only with a reason

Framework surfaces
- HF transformers: model.gradient_checkpointing_enable() -
  and pass use_cache=False to the forward, or the KV cache
  defeats the memory saving
- selectivity: checkpointing every k-th block or only the
  biggest (attention) blocks gives most of the win at a
  fraction of the recompute cost
```

Accumulation and checkpointing compose: accumulation bounds **gradient** memory windows, checkpointing bounds **activation** memory. Long-sequence LLM fine-tunes typically need both.

## Regularization in One Screen

```text
Decoupled weight decay (AdamW, 5501)
- AdamW SUBTRACTS lr * wd * w after the Adam update - it is
  decoupled from the gradient, which is the whole point
  (Adam + L2 entangles the penalty with per-param adaptive
  scaling and under-regularizes high-loss params)
- wd is NOT scheduled with the LR; typical 0.01 (fine-tune)
  to 0.1 (pretrain-scale)

Dropout placement in a transformer block
- canonical: Linear -> activation -> Dropout
  (dropout AFTER the nonlinearity, before residual add)
- rate: 0.1 classic fine-tuning; 0.0 for LLM pretraining at
  scale (regularization comes from data, not dropout);
  attention dropout separate from residual dropout

LayerNorm: pre-norm (x + block(ln(x))) is the modern default -
it is listed here because "is my instability a normalization
or a gradient problem" is a clipping-vs-arch decision, and
the answer is usually: with pre-norm + norm clipping, neither.
```

## Flat Minima: SAM

Sharpness-Aware Minimization (Foret et al., 2021) optimizes the loss over a small *neighborhood* of each weight vector — a proxy for finding flat basins, which generalize better:

```text
One SAM step
1. compute gradient g at w
2. perturb:  w' = w + rho * g / ||g||_GLOBAL   (the ascent step)
3. compute gradient g' at w'
4. restore w and step the base optimizer with g'

Cost: TWO forward-backward passes per step - the price of
every SAM run is ~2x wall-clock.
```

```python
import torch

class SAM(torch.optim.Optimizer):
    def __init__(self, params, base_optimizer, rho=0.05, **kwargs):
        super().__init__(params, defaults=dict(rho=rho, **kwargs))
        self.base_optimizer = base_optimizer(self.param_groups, **kwargs)
        self.param_groups = self.base_optimizer.param_groups

    @torch.no_grad()
    def first_step(self, zero_grad=False):
        grad_norm = torch.norm(torch.stack(        # GLOBAL norm across
            [p.grad.norm() for g in self.param_groups
             for p in g["params"] if p.grad is not None]))
        for group in self.param_groups:
            scale = group["rho"] / (grad_norm + 1e-12)
            for p in group["params"]:
                if p.grad is None:
                    continue
                e_w = p.grad * scale.to(p)
                p.add_(e_w)
                self.state[p]["e_w"] = e_w
        if zero_grad:
            self.zero_grad()

    @torch.no_grad()
    def second_step(self, zero_grad=False):
        for group in self.param_groups:
            for p in group["params"]:
                if "e_w" in self.state[p]:
                    p.sub_(self.state[p]["e_w"])
        self.base_optimizer.step()
        if zero_grad:
            self.zero_grad()

# ---- loop: the two zero_grads are load-bearing ----
optimizer = SAM(model.parameters(), torch.optim.AdamW, rho=0.05, lr=1e-3)

loss = criterion(model(x), y)
loss.backward()
optimizer.first_step(zero_grad=True)     # perturb + CLEAR grads

criterion(model(x), y).backward()        # grads at perturbed point
optimizer.second_step(zero_grad=True)    # restore + real step
```

```text
The two canonical mistakes (both common in blog implementations)
1. per-tensor scaling - perturbing each tensor by ITS OWN norm
   is not SAM; the rho-neighborhood is defined by the GLOBAL
   gradient norm
2. no zero_grad between passes - backward() ACCUMULATES, so
   the "perturbed" gradient becomes g(w) + g(w'), and you
   train on the sum of two gradients from two points

When it pays: vision fine-tunes and small-model generalization
 squeezes (consistently +0.5-2% test acc). When it does not:
LLM pretraining/fine-tuning at scale - the 2x cost dwarfs the
gains. ASAM (adaptive, scale-invariant variant) is the better
tuned version if you adopt it.
```

## Second-Order Optimizers: The Honest Status

Sophia (Liu et al., 2023) is the serious recent challenger to AdamW for pretraining:

```text
The mechanism (Sophia-H)
- maintain a DIAGONAL Hessian estimate h, updated every k steps
  with a Hutchinson-style estimator: sample z from {-1,+1},
  one extra backward of (g * z) through the graph, and
  h <- beta2 * h + (1 - beta2) * |g * z|   (unbiased for |H_ii|)
- update: w <- w - lr * clip(m / (h + eps), rho)
  momentum over a Hessian-scaled denominator, clipped
  elementwise to +-rho

Why it is attractive: the paper reports ~2x fewer steps than
AdamW for equal GPT-2-scale pretraining loss.

Why it has not taken over (2026 status)
- the Hessian estimate needs an EXTRA partial backward pass
  and the gains shrink at frontier scale ( evaluated mainly
  up to GPT-2-medium scale)
- the training-stability story at 100B+ is owned by AdamW +
  the distributed stack (5401-5404), which every framework
  sharding path already supports
- if you try it: use published implementations - hand-rolled
  second-order code (h := gradient of ||g||^2, fabricated
  update rules) is the most common way this idea gets
  "disproven" wrongly
```

The practical rule from [5501](./5501-Optimizer-Variants.md) stands: AdamW (or Lion if you validated it on your task) plus the schedule from [5502](./5502-Learning-Rate-Scheduling.md) is the baseline to beat; exotic optimizers must beat it on YOUR loss curve.

## Scouting: The LR Range Test

Run before committing to any schedule from [5502](./5502-Learning-Rate-Scheduling.md): train while exponentially ramping the LR from tiny to huge, and read the curve:

```python
def lr_range_test(model, loader, optimizer, init_lr=1e-7, final_lr=10.0, num_iter=100):
    """Train with an exponentially increasing LR; loss vs LR
    shows where training is stable and where it diverges."""
    mult = (final_lr / init_lr) ** (1 / num_iter)
    lr = init_lr
    optimizer.param_groups[0]["lr"] = lr
    losses, lrs = [], []

    for i, (x, y) in enumerate(loader):
        if i >= num_iter:
            break
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()

        losses.append(loss.item())
        lrs.append(lr)
        lr *= mult
        optimizer.param_groups[0]["lr"] = lr

    return lrs, losses        # plot with log-x
```

```text
Reading the curve
- LR where loss falls STEEPEST  -> good peak-LR candidate
  (not the LR of the minimum loss - by the minimum you are
  already destabilizing)
- LR where loss turns flat/rough -> the ceiling you must
  stay under
- feed the bracket into 5502: OneCycle max_lr = the steep
  region's upper edge; warmup start = 10-100x below it
```

## Best Practices

```text
1. Clip by norm (1.0), log the pre-clip norm, and treat a
   rising norm as an early-warning system - it precedes NaNs
2. Accumulation loop checklist: loss / accum_steps, scheduler
   per optimizer step, remainder flush - audit all three, the
   naive loop gets at least one wrong
3. use_reentrant=False for checkpointing, always; with HF LLMs
   pair gradient_checkpointing_enable() with use_cache=False
4. Reach for SAM on small-model generalization work; skip it
   wherever wall-clock is the binding constraint
5. Treat Sophia/second-order as research-track: validated
   implementations only, benchmarked against AdamW on your
   loss curve, never hand-rolled
6. Run the LR range test once per (model, dataset) pair before
   scheduling experiments - it is 100 steps and kills a whole
   class of wasted sweeps
7. One instability fix at a time: clipping, LR, and batch size
   all trade against each other; changing them together makes
   the result unattributable
```

---

## Summary

Beyond optimizer and schedule sits a toolbox that fixes specific failures: gradient clipping tames explosions, accumulation and checkpointing buy batch size and depth with different currencies, SAM trades time for flatter minima, and second-order optimizers remain more promise than practice at LLM scale. This lesson mapped the toolbox one technique per screen, added the regularization essentials, and ended with the LR range test as the scouting tool that grounds every other choice in measurement. Best practices is the honest summary: reach for these one at a time, and only when the failure they fix is the one you have.

## References

### Related PROJECT-OMEGA Documents

- [5501: Optimizer Variants](5501-Optimizer-Variants.md)
- [5502: Learning Rate Scheduling](5502-Learning-Rate-Scheduling.md)
- [5403: Mixed Precision Training](../5400-distributed-training/5403-Mixed-Precision.md)

---

## Next Steps

- Module 5500 complete — Phase 5 (Fine-tuning) done! Next: **[6101: HNSW Indexing](../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
