---
Document ID: 5501
Title: "5501: Optimizer Variants"
Phase: 5
Module: 5500
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'optimizers', 'adamw', 'memory', 'training']
---

# 5501: Optimizer Variants

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Why the Optimizer Matters at LLM Scale](#why-the-optimizer-matters-at-llm-scale)
- [AdamW: The Default](#adamw-the-default)
- [Adam vs AdamW](#adam-vs-adamw)
- [Memory-Efficient Variants](#memory-efficient-variants)
- [Sign-Based and Second-Order](#sign-based-and-second-order)
- [Choosing an Optimizer](#choosing-an-optimizer)
- [Practical Setup Recipe](#practical-setup-recipe)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compute the optimizer-state memory overhead of AdamW for a given parameter count
- Explain why decoupled weight decay (AdamW) fixes Adam's L2-coupling pathology
- Choose between 8-bit, paged, and factored optimizers using bytes-per-param budgets
- Configure LLM-appropriate AdamW hyperparameters (beta2, eps, decay exclusions)
- Build a production training step combining fused AdamW, gradient accumulation, and a scheduler

---

## Abstract

The optimizer is the quietest but largest consumer of GPU memory in a training job: Adam-family optimizers carry two moment buffers per parameter, typically doubling or tripling the footprint of the model itself. This lesson builds the mental model from the memory math outward: what AdamW actually stores, why decoupled weight decay matters, and which memory-saving variant (8-bit, paged, Adafactor) fits which budget. It closes with a decision table and a complete practical recipe. Hyperparameter scheduling is the subject of the next lesson, [5502](./5502-Learning-Rate-Scheduling.md).

## Why the Optimizer Matters at LLM Scale

### The Memory Ledger

For a model with `N` parameters trained in mixed precision with AdamW:

```text
Component                          Bytes per param
---------------------------------+----------------
Weights (bf16)                    |  2N
Gradients (bf16)                  |  2N
Master weights (fp32)             |  4N
Adam moment 1  m  (fp32)          |  4N
Adam moment 2  v  (fp32)          |  4N
---------------------------------+----------------
Total                             | 16N
Optimizer-only overhead           | 12N  (master + m + v)
```

```text
Consequence at scale (AdamW, mixed precision)

7B model  ->  7 x 16  = 112 GB  (single 80GB card: impossible)
70B model ->  70 x 16 = 1120 GB (multi-node)
LoRA ranks cut trainable params ~100x, so the optimizer
state shrinks proportionally - this is WHY PEFT works
```

Every optimizer variant below is a different answer to one question: **how do we shrink the 12N of optimizer state without wrecking convergence?**

## AdamW: The Default

### What It Stores

AdamW maintains, per parameter, an exponentially-weighted moving average of the gradient (`m`, first moment) and of the squared gradient (`v`, second moment). The update:

```text
theta  <-  theta - lr * ( m_hat / (sqrt(v_hat) + eps) + lambda * theta )

m_t = beta1 * m_{t-1} + (1 - beta1) * g_t
v_t = beta2 * v_{t-1} + (1 - beta2) * g_t^2
```

The `lambda * theta` term is applied **outside** the adaptive scaling — that single detail separates AdamW from Adam (next section).

### LLM-Appropriate Configuration

```python
import torch

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-4,               # fine-tuning; pretraining uses ~3e-4 with warmup
    betas=(0.9, 0.999),    # pretraining convention: (0.9, 0.95) - see below
    eps=1e-8,
    weight_decay=0.01,     # 0.1 common for pretraining-scale runs
    fused=True,            # CUDA fused kernel: one launch, less overhead
)
```

```text
Hyperparameter conventions

beta2 = 0.999   default; fine for small-batch fine-tuning
beta2 = 0.95    pretraining standard (GPT-3 / LLaMA recipes). Short
                memory of v -> faster adaptation to loss spikes
eps    = 1e-8   fine-tuning; 1e-6 for bf16-heavy pretraining stacks
lr     = 1e-5..3e-4  fine-tuning; scale DOWN as model size goes UP
```

### Weight-Decay Exclusions

Applying decay to norms, biases, and embeddings usually hurts. Group parameters instead:

```python
decay, no_decay = [], []
for n, p in model.named_parameters():
    if not p.requires_grad:
        continue
    if p.ndim < 2 or "norm" in n.lower() or "embed" in n.lower():
        no_decay.append(p)
    else:
        decay.append(p)

optimizer = torch.optim.AdamW(
    [{"params": decay, "weight_decay": 0.01},
     {"params": no_decay, "weight_decay": 0.0}],
    lr=1e-4, fused=True,
)
```

## Adam vs AdamW

```text
Adam (2015): weight decay is implemented as L2 regularization,
i.e. added to the GRADIENT before adaptive scaling

    g_t = g_t + lambda * theta_t      # L2, coupled
    theta -= lr * m_hat / (sqrt(v_hat) + eps)

Pathology: parameters with large historical gradients have a
large v, so the adaptive scaling ALSO shrinks the decay term.
The regularization strength therefore varies per-parameter and
shrinks exactly where it should act hardest.

AdamW (2017): decay applied DIRECTLY to the weights,
outside the adaptive term - uniform, predictable regularization.

Empirical translation: same hyperparameters, AdamW reaches
lower validation loss; Adam+L2 tends to under-regularize.
```

Rule for practice: never hand `weight_decay > 0` to `torch.optim.Adam`. If you see old tutorials doing it, they are pre-AdamW.

## Memory-Efficient Variants

### 8-bit and Paged Adam (bitsandbytes)

Store `m` and `v` in 8-bit blockwise quantization instead of fp32:

```python
import bitsandbytes as bnb

optimizer = bnb.optim.AdamW8bit(
    model.parameters(), lr=1e-4, weight_decay=0.01,
    # optim_bits=32 for the first steps is automatic ("stable embedding")
)

# Paged variant: optimizer state lives in pinned CPU memory and pages
# into GPU on demand - survives the memory spikes of long sequences
optimizer = bnb.optim.PagedAdamW8bit(model.parameters(), lr=1e-4)
```

```text
Memory ledger (per param, optimizer overhead only)

AdamW (fp32 state)      12N
AdamW8bit                2N + small blockwise scales
PagedAdamW8bit           2N effective on GPU

Cost: occasionally noisier convergence; blockwise quantization
keeps quality loss negligible in practice - this is the optimizer
behind the standard QLoRA recipe (see 5102).
```

### Adafactor: Factored Second Moment

Adafactor avoids storing the full `d x r` matrix of squared gradients for a weight matrix, keeping only row and column statistics (`O(d + r)` instead of `O(d*r)`):

```python
from transformers import Adafactor

optimizer = Adafactor(
    model.parameters(),
    lr=1e-4,
    eps=(1e-30, 1e-3),
    clip_threshold=1.0,
    decay_rate=-0.8,
    beta1=None,               # no momentum by default
    weight_decay=0.0,
    relative_step=False,      # set True for no-lr schedule-free runs
    scale_parameter=False,
    warmup_init=False,
)
```

```text
Trade-offs
+ second-moment memory drops from 4N to ~0 for matrix params
+ proven at scale: original T5 and UL2 were trained with it
- no momentum by default -> slower, less smooth convergence
- more sensitive to lr / eps; fewer modern recipes to copy from
```

Today 8-bit Adam has mostly displaced Adafactor for memory-constrained runs, because it keeps full moments (just quantized) and converges like the fp32 version.

## Sign-Based and Second-Order

### Lion

Lion replaces the adaptive machinery with a sign update on the interpolation of two gradients — only **one** moment is stored:

```python
# uv pip install lion-pytorch
from lion_pytorch import Lion

optimizer = Lion(model.parameters(), lr=3e-5, weight_decay=0.1)
```

```text
Transition rules from an AdamW recipe
- lr: 3-10x SMALLER than the AdamW value
- weight decay: ~3x LARGER to compensate
- memory: one moment, 4N total (vs 8N for Adam's m+v)

Character: stronger implicit pruning of tiny updates;
benefits vanish where batch sizes are small.
```

### Sophia

Sophia estimates a diagonal of the Hessian (via Gauss-Newton-Bartlett or shuffled minibatches) and clips the update by curvature, aiming for Adam-quality results at a fraction of the steps:

```python
# No PyTorch-core implementation; research code at:
# github.com/Liuhong99/Sophia
# Status as of this lesson: strong pretraining-paper results,
# not yet a production default.
```

Track it, benchmark it on your workload, but do not build a production pipeline on it yet.

## Choosing an Optimizer

```text
Decision tree

Full fine-tune, memory is comfortable
└─ AdamW (fused=True)

Fine-tune / small pretrain, memory tight
├─ AdamW8bit          standard choice
└─ PagedAdamW8bit     long sequences / spiky activations
                      (QLoRA pairing)

Large-scale pretraining, GPUs scarce
├─ 8-bit Adam first
└─ Adafactor if second-moment memory still dominates

Experimental pretraining, big batches
└─ Lion (retune lr/wd from AdamW recipe)
```

| Optimizer | State bytes/param | Momentum | Convergence | Maturity |
|---|---|---|---|---|
| AdamW (fp32) | 8N (+4N master) | m + v | Best-understood | Production default |
| AdamW8bit | ~2N | m + v (8-bit) | Near-identical | Production (QLoRA) |
| PagedAdamW8bit | ~2N paged | m + v (8-bit) | Near-identical | Production |
| Adafactor | ~0 for v | optional | Slower | Proven (T5-era) |
| Lion | 4N | one buffer | Needs retune | Emerging |
| Sophia | < AdamW | v + Hessian diag | Fast (papers) | Research |

## Practical Setup Recipe

A complete, defensible training step:

```python
import torch
from transformers import get_cosine_schedule_with_warmup

decay, no_decay = [], []
for n, p in model.named_parameters():
    if not p.requires_grad:
        continue
    (no_decay if (p.ndim < 2 or "norm" in n.lower()) else decay).append(p)

optimizer = torch.optim.AdamW(
    [{"params": decay, "weight_decay": 0.01},
     {"params": no_decay, "weight_decay": 0.0}],
    lr=2e-5,
    betas=(0.9, 0.999),
    eps=1e-8,
    fused=True,
)

ACC_STEPS = 8
scheduler = get_cosine_schedule_with_warmup(
    optimizer, num_warmup_steps=100, num_training_steps=total_steps
)

for step, batch in enumerate(loader):
    loss = model(**batch).loss / ACC_STEPS
    loss.backward()                      # grads accumulate across micro-batches

    if (step + 1) % ACC_STEPS == 0:
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()                 # scheduler ticks per OPTIMIZER step
        optimizer.zero_grad(set_to_none=True)
```

```text
Pitfalls checklist

- Clip AFTER accumulation, BEFORE step (clipping micro-batch
  gradients one by one distorts the true gradient norm)
- scheduler.step() must follow optimizer.step() one-to-one,
  or the effective lr schedule is wrong by the accumulation factor
- beta2=0.999 with batch size 8 and lr 2e-4 will plateau early:
  shrink batch -> shrink beta2 or raise eps
- Loss spike that recovers: usually normal. Spike + grad-norm
  explosion that does NOT recover: check data, then lower beta2
- zero_grad(set_to_none=True) is measurably faster than the
  default zero_grad()
```

---

## Summary

The optimizer is the quietest but largest consumer of GPU memory at LLM scale: Adam-family optimizers carry two moment buffers per parameter, typically doubling or tripling the model's own footprint. This lesson built the mental model from that memory math outward - what AdamW actually stores, why decoupled weight decay matters, the memory-efficient variants, and the honest status of sign-based and second-order methods. The choosing section is the practice: AdamW until memory forces otherwise, then the variant that buys back the moment buffers cheapest.

## References

### Related Minder Academy Documents

- [5502: Learning Rate Scheduling](5502-Learning-Rate-Scheduling.md)
- [5503: Advanced Optimization Techniques](5503-Advanced-Techniques.md)

---

## Next Steps

- Continue with: **[5502: Learning Rate Scheduling](./5502-Learning-Rate-Scheduling.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [5102: QLoRA Pipelines](../5100-peft/5102-QLoRA-Pipelines.md)
- [4401: GPTQ](../../phase4-quantization/4400-advanced-techniques/4401-GPTQ.md)
