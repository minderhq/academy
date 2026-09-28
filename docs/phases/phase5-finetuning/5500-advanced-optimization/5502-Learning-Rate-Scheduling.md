---
Document ID: 5502
Title: Learning Rate Scheduling
Phase: 5
Module: 5500
Last Updated: 2026-09-25
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['optimization', 'learning-rate', 'scheduling', 'warmup', 'training']
---

# 5502: Learning Rate Scheduling

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Why the LR Changes During Training](#why-the-lr-changes-during-training)
- [The Canonical Transformer Recipe](#the-canonical-transformer-recipe)
- [The Scheduler Catalog](#the-scheduler-catalog)
- [Choosing a Scheduler](#choosing-a-scheduler)
- [Loop Integration: Ordering Rules](#loop-integration-ordering-rules)
- [Hugging Face Schedulers](#hugging-face-schedulers)
- [Layer-Wise LR Decay](#layer-wise-lr-decay)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain why transformers need warmup (Adam variance estimates + early attention instability) and decay (annealing into the minimum)
- Implement warmup + linear decay and warmup + cosine decay with `LambdaLR` from scratch
- Choose between linear, cosine, one-cycle, and restart schedules from the task shape (fine-tune vs pretrain vs short run)
- Place `scheduler.step()` correctly in loops that use gradient accumulation and AMP `GradScaler`
- Build a layer-wise LR decay parameter-group setup for pretrained-model fine-tuning

---

## Abstract

The learning rate is the one hyperparameter that changes meaning mid-run: the value that escapes bad initialization at step 100 destroys a nearly converged model at step 100,000. Scheduling encodes that arc — warm up past the unstable early phase, hold or decay into a minimum. This lesson builds the two schedules that cover ~90% of transformer work (warmup+linear, warmup+cosine) from scratch with `LambdaLR`, tours the rest of the catalog (step, one-cycle, SGDR) with honest when-to-use notes, and nails down the integration details that silently break runs: scheduler stepping per *optimizer* step under gradient accumulation, and the `GradScaler` skip interaction.

## Why the LR Changes During Training

```text
Phase        What is happening                  LR it wants
---------    --------------------------------   ----------------
step ~0      Adam's m/v estimates are noise;    small (warm up)
             softmax attention is unstable;
             large early steps inject garbage
             the optimizer never recovers from

mid-run      loss descending a broad basin      peak - explore at
                                                full speed

late run     approaching a sharp minimum        decaying to ~0 -
             gradient noise must SHRINK or      anneal in
             the iterate bounces around it
             instead of settling

Warmup without decay: you stabilize early training then bounce
off the minimum forever. Decay without warmup: an early large
step can push activations into softmax saturation and the loss
flatlines at random. Both halves earn their place.
```

```text
Where the peak comes from (before any schedule exists)
- short sweep: train ~200 steps at 5e-6 / 1e-5 / 2e-5 / 5e-5,
  pick the largest that descends smoothly - cheaper and more
  honest than any formula
- rule of thumb across model sizes: the max stable LR shrinks
  as the model grows (a 7B model fine-tunes at 1e-5-2e-5 where
  a 125M tolerates 5e-4)
- linear scaling rule: when you multiply batch size by k,
  multiply LR by ~k (valid until large k; then sqrt(k))
```

## The Canonical Transformer Recipe

### Warmup + Linear Decay

The default for BERT-style and instruction fine-tuning:

```python
import torch
from torch.optim.lr_scheduler import LambdaLR

optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)

def linear_warmup_decay(optimizer, warmup_steps, total_steps):
    """factor goes 0 -> 1 over warmup, then 1 -> 0 over the rest."""
    def lr_lambda(step):
        if step < warmup_steps:
            return step / max(1, warmup_steps)
        progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        return max(0.0, 1.0 - progress)
    return LambdaLR(optimizer, lr_lambda)

scheduler = linear_warmup_decay(optimizer, warmup_steps=500, total_steps=10_000)
```

```text
LR
5e-5 |        *
    /         *
   /            *
  /               *
 /                  * * * *
 +----+----------------------> step
 500 warmup, 9500 linear decay to 0
```

`LambdaLR` multiplies each param group's base LR by the lambda — this composes correctly with the layer-wise groups at the end of the lesson, because each group keeps its own `lr` and the schedule scales all of them proportionally.

### Warmup + Cosine Decay

The default for pretraining and most modern LLM runs:

```python
import math
from torch.optim.lr_scheduler import LambdaLR

def cosine_warmup_decay(optimizer, warmup_steps, total_steps, min_ratio=0.1):
    """Cosine from 1.0 down to min_ratio after linear warmup."""
    def lr_lambda(step):
        if step < warmup_steps:
            return step / max(1, warmup_steps)
        progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        return min_ratio + (1.0 - min_ratio) * 0.5 * (1.0 + math.cos(math.pi * progress))
    return LambdaLR(optimizer, lr_lambda)

scheduler = cosine_warmup_decay(optimizer, warmup_steps=2000, total_steps=100_000)
```

```text
LR
peak |     *
    /        **
   /            ***
  /                 ****
 /                       ****______ <- floors at min_ratio
 +----+----------------------------> step

Why min_ratio (usually 0.05-0.1, not 0)
- late-training steps keep making real progress at 5-10% LR
- a floor also leaves the model usable if you must stop early
- cosine vs linear: cosine lingers near the peak longer, then
  eases out - empirically slightly better final loss on long
  pretraining; on 1-3 epoch fine-tunes the difference is noise
```

## The Scheduler Catalog

### Step / MultiStep Decay

Legacy vision recipe — flat LR, drop by a factor at milestones:

```python
from torch.optim.lr_scheduler import StepLR, MultiStepLR

StepLR(optimizer, step_size=30, gamma=0.1)              # x0.1 every 30 epochs
MultiStepLR(optimizer, milestones=[30, 60, 90], gamma=0.1)
```

```text
LR |-----
   |      -----
   |            -------
   |                   ---------
   +-------------------------> epoch

Still standard for CNN/image baselines. Discontinuities make it
a poor fit for transformers - the loss spikes at every drop and
attention heads partially reset.
```

### Exponential Decay

```python
from torch.optim.lr_scheduler import ExponentialLR

ExponentialLR(optimizer, gamma=0.99)   # per-STEP here; 0.999^k semantics
```

Smooth but never reaches a floor, and the decay constant is uninterpretable relative to a training budget — cosine with an explicit `total_steps` is nearly always the better-specified choice.

### OneCycleLR: Super-Convergence

Leslie Smith's schedule: warm up, peak, anneal — all in one cycle sized to the *exact* step count:

```python
from torch.optim.lr_scheduler import OneCycleLR

scheduler = OneCycleLR(
    optimizer,
    max_lr=1e-3,
    total_steps=len(loader) * num_epochs,   # must be EXACT
    pct_start=0.3,          # 30% of steps climbing, 70% annealing
    div_factor=25,          # start LR = max_lr / 25
    final_div_factor=1e4,   # end LR = start LR / 1e4
)
```

```text
LR |         ____
   |       /      \
   |     /          \
   |   /              \__
   | /                     \______
   +----+---------------------------> step
     30% up    70% cosine down

Why it works: the high-LR middle acts as a strong regularizer
(super-convergence - faster than cosine at equal steps on
vision/small-model work), and the built-in climb IS the warmup.
Caveat: total_steps is fixed at construction - any mid-run
extension restarts the schedule design.
```

### Cosine Restarts (SGDR)

```python
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts

scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=1000, T_mult=2, eta_min=1e-6)
```

```text
LR |  *      *              *
   | / \    / \            / \
   |/    \_/     \________/     ...
   +---+-----+-----------+-------> step
     T0    2*T0        4*T0      (T_mult=2)

Each restart re-explores; intervals GROW so late training is
mostly annealing. Its real production value: checkpoints taken
at cosine minima are comparably good snapshots, and restarts
give an ensemble-of-snapshots for free. Worth it for long runs
you can afford to run cyclically; overkill for a 3-epoch
fine-tune.
```

## Choosing a Scheduler

| Task shape | Schedule | Why |
|---|---|---|
| Instruction / supervised fine-tune | warmup + **linear** decay | 1-3 epochs; HF default, well-understood, decays fully to 0 |
| Pretraining (long run) | warmup + **cosine** (floor 5-10%) | best final loss at scale; floor keeps late progress |
| Short, compute-tight run | **OneCycle** | fastest convergence per step; needs exact step count |
| Vision CNN baseline | **MultiStep** | community-standard recipes are tuned in these units |
| Long run wanting snapshots | **SGDR** | checkpoint-at-minima gives free ensembling |
| Scouting the peak LR | **LR range test** (short CyclicLR-style ramp) | finds the stable ceiling empirically before committing |

```text
Warmup sizing by regime
- LLM fine-tuning:    100-500 steps or ~3-10% of total
- pretraining:        0.5-2% of total (but that is thousands
                      of steps at pretraining scale)
- LoRA / PEFT:        short or none - only the adapters
                      update and they start near zero
- RLHF/PPO:           the policy KL penalty replaces most of
                      the need; keep warmup tiny
```

## Loop Integration: Ordering Rules

The schedule itself is simple; the bugs live in *when* you step it.

```text
The order, per OPTIMIZER step

optimizer.zero_grad(set_to_none=True)
... micro-batches accumulate into .grad ...
loss.backward()
scaler.unscale_(optimizer)          # if AMP FP16
torch.nn.utils.clip_grad_norm_(...)
scaler.step(optimizer)              # plain: optimizer.step()
scheduler.step()                    # AFTER the optimizer step

1. scheduler.step() goes AFTER optimizer.step() - calling it
   before means every epoch/step trains at the PREVIOUS LR and
   PyTorch ≥1.1 warns you
2. under GRADIENT ACCUMULATION, scheduler steps once per
   optimizer step, i.e. once per K micro-batches - stepping it
   per micro-batch walks the schedule K times faster than the
   total_steps you declared, and warmup silently ends early
3. pick PER-STEP or PER-EPOCH scheduling at setup, not both:
   - step-level (transformers default): T_max/total in STEPS
   - epoch-level (vision): after each epoch; step_size/milestones
     are in epochs
```

### The AMP GradScaler Skip

```text
FP16 runs (5403): scaler.step() SKIPS the optimizer update when
gradients contain inf/nan. scheduler.step() does not know that -
the schedule advances even though nothing was learned.

- BF16 (the default on modern GPUs): no scaler, no skip, no issue
- FP16 with occasional skips: tiny drift, accept it
- FP16 with frequent skips: gate the scheduler on the scale
  actually not dropping:

    scale_before = scaler.get_scale()
    scaler.step(optimizer)
    if scaler.get_scale() >= scale_before:   # update happened
        scheduler.step()
```

## Hugging Face Schedulers

`transformers` ships the recipe above pre-assembled, plus the LambdaLR plumbing:

```python
from transformers import get_scheduler, get_linear_schedule_with_warmup

num_training_steps = len(train_dataloader) * num_epochs

scheduler = get_scheduler(
    name="linear",        # "linear", "cosine", "cosine_with_restarts",
                          # "polynomial", "constant", "constant_with_warmup"
    optimizer=optimizer,
    num_warmup_steps=500,
    num_training_steps=num_training_steps,
)

# direct aliases for the two workhorses
scheduler = get_linear_schedule_with_warmup(
    optimizer, num_warmup_steps=500, num_training_steps=num_training_steps
)
```

In `Trainer`, `lr_scheduler_type` and `warmup_steps` in `TrainingArguments` select the same machinery — the Accelerate loop already calls `scheduler.step()` per optimizer step, which is exactly why accumulation-aware stepping "just works" there and breaks when people re-implement the loop by hand.

## Layer-Wise LR Decay

Fine-tuning a pretrained model wants the top layers to move and the bottom (general) layers to barely move. LLRD multiplies the base LR by a decay factor per layer depth:

```python
def layerwise_lr_decay(model, base_lr, decay=0.95, num_layers=12):
    """Top transformer layer: base_lr. Each layer below: decay * layer above.
    Embeddings get the smallest LR of all."""
    groups: dict[float, list] = {}

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if "embeddings" in name:
            layer_id = 0
        elif ".layer." in name or "encoder.layer" in name:
            layer_id = int(name.split("layer.")[1].split(".")[0]) + 1
        else:                       # pooler / heads: treat as top
            layer_id = num_layers
        lr = base_lr * (decay ** (num_layers - layer_id))
        groups.setdefault(lr, []).append(param)

    return [{"params": params, "lr": lr} for lr, params in sorted(groups.items())]

optimizer = torch.optim.AdamW(layerwise_lr_decay(model, base_lr=5e-5, decay=0.95))
```

```text
- decay=0.95: gentle (BERT-era default). decay=0.9: aggressive,
  for small in-domain datasets where the backbone is already
  close to what you need
- because every group's lr is a multiple of base_lr, the
  LambdaLR schedule from earlier scales ALL groups in proportion -
  no extra plumbing needed
- same idea powers discriminator-style PEFT setups: new heads at
  base_lr, body layers decayed by depth
```

## Best Practices

```text
1. Write the schedule as a pure function of step (LambdaLR) -
   the hand-rolled class that mutates param_group['lr'] is where
   the off-by-one and un-imported-module bugs live
2. Log scheduler.get_last_lr()[0] every N steps to the metrics
   stream - a schedule bug is invisible in the loss curve until
   the end, and obvious in the LR curve immediately
3. total_steps must equal ACTUAL optimizer steps: len(loader)
   with drop_last, times epochs, DIVIDED by accumulation steps.
   A mismatched total silently ends the schedule early (linear
   decays to 0 at 70% of training)
4. Warmup is not optional for transformer training from scratch;
   for fine-tuning it is cheap insurance - keep it
5. Prefer cosine with a floor over cosine to zero for anything
   longer than a few epochs
6. When resuming from a checkpoint, load scheduler.state_dict()
   alongside optimizer/model - a fresh scheduler restarts warmup
   and the loss spike looks like data corruption
7. Change one of {peak LR, schedule, batch size} per experiment -
   they interact through effective step size and you cannot
   attribute a result to any of them otherwise
```

---

## References

### Related PROJECT-OMEGA Documents

- [5501: Optimizer Variants](5501-Optimizer-Variants.md)
- [5503: Advanced Optimization Techniques](5503-Advanced-Techniques.md)
- [5403: Mixed Precision Training](../5400-distributed-training/5403-Mixed-Precision.md)

---

## Next Steps

- Continue with: **[5503: Advanced Optimization Techniques](./5503-Advanced-Techniques.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
