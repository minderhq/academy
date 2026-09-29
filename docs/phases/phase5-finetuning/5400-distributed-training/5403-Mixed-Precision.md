---
Document ID: 5403
Title: "5403: Mixed Precision Training"
Phase: 5
Module: 5400
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['training', 'mixed-precision', 'bf16', 'fp16', 'gpu']
---

# 5403: Mixed Precision Training

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Precision Zoo](#the-precision-zoo)
- [What autocast Actually Does](#what-autocast-actually-does)
- [Loss Scaling: The FP16 Tax](#loss-scaling-the-fp16-tax)
- [BF16: The Default Choice](#bf16-the-default-choice)
- [The Memory and Speed Ledger](#the-memory-and-speed-ledger)
- [FP8: The Frontier](#fp8-the-frontier)
- [Common Failure Modes](#common-failure-modes)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Contrast FP16 and BF16 bit layouts and derive why only one of them needs loss scaling
- Explain what `torch.amp.autocast` casts, what it leaves alone, and why it does not halve weight memory by itself
- Run a correct AMP loop with `GradScaler`, including unscale-before-clip ordering
- Compute the real memory saving of mixed precision from the 16N ledger instead of assuming 2x
- Name the FP8 formats (E4M3/E5M2) and where each is used in the training step

---

## Abstract

Mixed precision runs most of the training step in 16-bit float while keeping the numerically fragile parts — weight updates, norms, reductions — in FP32. It is now the default for every serious training run: it halves weight/activation bytes and unlocks Tensor Core throughput. This lesson builds the mechanics from the bit layouts outward: what `autocast` actually does (and the common misconception that it shrinks your weights), why FP16 drags a loss-scaling tax that BF16 eliminates, the memory ledger that says where the 2x really lands, and a first look at FP8.

## The Precision Zoo

```text
Format   Bits (S/E/M)    Max range        Mantissa precision   Hardware
-------+---------------+----------------+--------------------+----------------
FP32     1/ 8/23         ~3.4e38          ~7 decimal digits    everywhere
FP16     1/ 5/10         ~65,504          ~3 decimal digits    all GPUs
BF16     1/ 8/ 7         ~3.4e38 (=FP32)  ~2 decimal digits    Ampere (2020)+
FP8 E4M3 1/ 4/ 3         ~448             very coarse          Hopper (2022)+
FP8 E5M2 1/ 5/ 2         ~57,344          coarser still        Hopper (2022)+

Reading the layouts
- FP16 bets bits on PRECISION (10 mantissa) and starves RANGE
  (5 exponent bits) -> overflows at 65,504, underflows gradients
  near 1e-5 -> needs loss scaling
- BF16 keeps FP32's 8 exponent bits and sacrifices precision
  -> range problems disappear; only precision is coarser
- rule of thumb: UNDERFLOW kills gradients (FP16's problem),
  PRECISION rounds small updates (BF16's cost) - training is
  far more sensitive to underflow than to rounding
```

## What autocast Actually Does

The common misconception first: `autocast` does **not** convert your model. Parameters stay FP32 on the GPU; autocast intercepts each op and casts *the tensors fed into it*, per an op whitelist.

```python
import torch

model = build_model()                      # params: FP32 (still!)

with torch.autocast("cuda", dtype=torch.bfloat16):
    out = model(x)                         # matmuls run in bf16,
                                           # params are cast on the fly
loss = criterion(out, y)

# the PARAMETER memory did not change - autocast is a compute
# precision policy, not a storage policy
```

```text
What the op policy looks like (simplified)

run in LOW precision (bf16/fp16)     matmul, conv, linear -
                                     the Tensor Core workhorses
run in FP32 (always)                 softmax, log/softmax, layer
                                     norm, reductions, loss fns,
                                     optimizer updates
                                     (norms reduce over large
                                     dims - fp32 accumulation)

Storage consequence
weights:      FP32  (unchanged by autocast)
activations:  ~halved (the big wins are the wide matmul I/O)
grads:        follow the params (FP32) unless the training
              framework says otherwise
```

This is why "I enabled autocast but memory only dropped 20%" is the normal outcome, not a bug. Halving the *weights* is a separate decision — see the ledger section.

### The Modern AMP Loop

`torch.cuda.amp.*` is deprecated since PyTorch 2.4 — use the `torch.amp` namespace:

```python
import torch

dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
scaler = torch.amp.GradScaler("cuda", enabled=(dtype == torch.float16))

for batch in loader:
    optimizer.zero_grad(set_to_none=True)

    with torch.autocast("cuda", dtype=dtype):      # forward AND loss
        out = model(batch["x"])
        loss = criterion(out, batch["y"])

    scaler.scale(loss).backward()                  # scaled backward

    scaler.unscale_(optimizer)                     # grads back to true scale
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)   # clip TRUE norms

    scaler.step(optimizer)                         # skips the step if
    scaler.update()                                # grads had inf/nan
```

```text
The three ordering rules that break silently when violated
1. unscale_ BEFORE clip_grad_norm_ - clipping scaled gradients
   clips them against the wrong norm (scale * 1.0)
2. autocast must wrap the LOSS too - computing CE in fp32 from
   bf16 logits is fine, but computing it outside autocast from
   fp16 logits can overflow
3. step() AFTER unscale_; update() every iteration regardless -
   the scaler learns the safe scale from the skip pattern
```

## Loss Scaling: The FP16 Tax

```text
Why FP16 needs it

gradient values in deep nets cluster around 1e-7 .. 1e-3
FP16 smallest normal: ~6e-5   -> most gradients UNDERFLOW to 0

Fix: multiply the loss by S, gradients scale by S exactly,
underflow moves below the representable range; divide by S
at the optimizer (unscale_)

Dynamic scaling (GradScaler's job)
- start S large (2^16)
- if any inf/nan appear in grads: halve S, SKIP the step
- if N clean steps pass: double S (growth_interval)
- equilibrium: S hovers just under the overflow threshold
```

```python
scaler = torch.amp.GradScaler(
    "cuda",
    init_scale=2.0**16,
    growth_factor=2.0,
    backoff_factor=0.5,
    growth_interval=2000,
)
```

BF16 has the FP32 exponent — its dynamic range makes all of this unnecessary. `GradScaler(enabled=False)` (or simply omitting it) is correct there; the scaler is the FP16 tax, and BF16 does not pay it.

## BF16: The Default Choice

```text
Decision rule, 2026

Hardware Ampere or newer (A100/H100/L4/4090/MI300...)
  -> BF16 autocast, NO scaler. This is the default for
     pretraining and fine-tuning alike
Hardware pre-Ampere (V100, T4)
  -> FP16 autocast + GradScaler - the range tax is the price
Inference-only on memory-bound hardware
  -> FP16 can win over BF16: same 2 bytes, more mantissa bits
     for weights that are already trained and static

if torch.cuda.is_bf16_supported():
    dtype = torch.bfloat16
else:
    dtype = torch.float16   # + scaler
```

```text
Failure signature comparison

BF16 model:  loss curves overlap FP32 within noise for
             virtually all workloads (LLaMA/GPT recipes are
             pure BF16)
FP16 model:  loss spikes when the scale hunts; NaN risk on
             long-tail activations; needs grad-norm watch
```

## The Memory and Speed Ledger

Connect autocast to the optimizer ledger from [5501](../5500-advanced-optimization/5501-Optimizer-Variants.md):

```text
Mixed-precision training state for N params (the "16N" layout)

weights fp32        4N    autocast leaves these alone
grads   fp32        4N
master  -           -     params ARE the master copy under
                            vanilla AMP (no extra copy)
Adam m+v fp32        8N
--------------------
vanilla AMP total:  16N    <- autocast ALONE gives 0 memory
                             saving on state (only activations)

TRUE "half the model" happens when weights+grads drop to 2N+2N:

FSDP MixedPrecision(param_dtype=bf16) + fp32 reduce (5401)
  weights 2N, grads 2N, reduce buffers fp32
  optimizer state can stay fp32:  2N+2N+8N = 12N
DeepSpeed-style bf16 weights + fp32 master in optimizer:
  2N + 2N + 4N(master) + 8N = 16N  (same peak, faster math)
Pure bf16 everything (risky):
  2N + 2N + 8N = 12N  (update rounding artifacts possible)
```

```text
Speed reality check
- Tensor Cores give fp16/bf16 matmuls up to 2-4x fp32 peak
- end-to-end speedup is 1.5-2.5x: launch overhead, norms,
  and data loading are not accelerated
- alignment: keep matmul dims divisible by 8 (fp16/bf16) or
  the Tensor Core fast path silently degrades
- bf16 vs fp16: same throughput on modern GPUs - choose by
  numerics, not speed
```

## FP8: The Frontier

Hopper-and-later hardware adds 8-bit float formats with hardware support, used for the *forward and linear-layer backward* passes of large-scale pretraining:

```text
E4M3  (4 exponent, 3 mantissa)  forward activations - needs
                                the range headroom but values
                                are bounded
E5M2  (5 exponent, 2 mantissa)  gradients - wider range,
                                precision matters less

The catch: FP8 has ~2 bits of mantissa - a SINGLE global scale
cannot cover a whole training run. Production stacks
(Transformer Engine) use DELAYED SCALING: per-tensor amax
history from step t chooses the scale for step t+1.
```

```python
# pattern via NVIDIA Transformer Engine (H100+)
import transformer_engine.pytorch as te
from transformer_engine.common.recipe import DelayedScaling, Format

linear = te.Linear(4096, 4096)          # drop-in for nn.Linear
recipe = DelayedScaling(fp8_format=Format.HYBRID)  # E4M3 fwd / E5M2 bwd

with te.fp8_autocast(enabled=True, fp8_recipe=recipe):
    out = linear(x)                      # FP8 matmul, fp32 accumulate
```

Treat FP8 as a pretraining-scale optimization; fine-tuning jobs rarely break even on its bookkeeping below multi-node scale.

## Common Failure Modes

```text
1. NaN loss at step ~0-200 (FP16)
   - the scale is hunting too high: GradScaler handles this
     itself, but a persistent NaN means check inputs for NaNs
     and any custom fp16-opposed ops (exp, log of small)
2. NaN loss under BF16
   - not a scaling problem: look for actual inf in activations
     (lr too high, data bug), and torch.autograd.set_detect_
     anomaly(True) to localize
3. Loss curve diverges from an fp32 reference
   - check that norms/softmax really are in fp32 (autocast
     policy), that you are not running model.half() AND
     autocast together (double-casting kills numerics)
4. Grad norm is always scale*constant
   - you clipped BEFORE unscale_: move unscale_ up
5. Memory did not drop
   - autocast only halves activations; halve state via FSDP
     param_dtype or bf16 weights (see ledger above)
6. checkpointing + autocast
   - torch.utils.checkpoint works inside autocast; ensure the
     recompute runs under the SAME autocast context or the
     saved/restored dtypes mismatch
```

## Best Practices

```text
1. BF16 + no scaler on Ampere+; FP16 + GradScaler only on
   pre-Ampere. One line of hardware detection, not a debate
2. Use torch.amp.* namespace - torch.cuda.amp.* is deprecated
3. Wrap forward AND loss in autocast; never .half() the model
   for a training run
4. unscale_ -> clip -> step -> update, in that order, every step
5. Benchmark with torch.cuda.Event + synchronize, never
   time.time() alone - kernels are async
6. Keep a short fp32 reference run as the numerics oracle when
   introducing mixed precision to a NEW architecture
7. zero_grad(set_to_none=True); fused optimizers compose with
   AMP and measurably help at scale
```

```python
import time
import torch

def bench(fn, iters=50):
    for _ in range(10):                 # warmup
        fn()
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(iters):
        fn()
    end.record()
    torch.cuda.synchronize()
    return start.elapsed_time(end) / iters      # ms per iter
```

---

## References

### Related PROJECT-OMEGA Documents

- [5402: Model Parallelism](5402-Model-Parallelism.md)
- [5404: Distributed Optimization](5404-Distributed-Optimization.md)
- [5501: Optimizer Variants](../5500-advanced-optimization/5501-Optimizer-Variants.md)

---

## Next Steps

- Continue with: **[5404: Distributed Optimization](./5404-Distributed-Optimization.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
