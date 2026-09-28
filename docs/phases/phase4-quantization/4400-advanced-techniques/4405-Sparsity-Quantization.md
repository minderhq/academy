---
Document ID: 4405
Title: Sparsity + Quantization
Phase: 4
Module: 4400
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'sparsity', 'pruning', 'compression', 'inference']
---

# 4405: Sparsity + Quantization

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Does Sparsity Pay? Do the Math First](#does-sparsity-pay-do-the-math-first)
- [The Three Sparsity Regimes](#the-three-sparsity-regimes)
- [Hardware Support: The Honest Table](#hardware-support-the-honest-table)
- [LLM Pruning Methods That Ship](#llm-pruning-methods-that-ship)
- [Combining with Quantization, Correctly](#combining-with-quantization-correctly)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compute the CSR storage break-even and explain why "50% sparse = 50% smaller" is false
- Choose between unstructured, semi-structured (2:4), and structured pruning from the deployment target
- Run one-shot magnitude-activation pruning (Wanda-style) on a transformer without retraining
- Implement 2:4 semi-structured sparsity and know exactly which hardware accelerates it (and which does not)
- Order a prune → recover → quantize pipeline and avoid the in-place fake-quant corruption bug

---

## Abstract

Sparsity (zeros in the weight matrix) and quantization (fewer bits per weight) attack compression from different directions, and they compose — but not as simply as "multiply the savings." This lesson does the storage math first, because the index overhead of sparse formats and the accelerating gains of low-bit formats interact in ways that flip conclusions: 50% unstructured sparsity on top of INT4 can be a net *loss*. From there: the three sparsity regimes (unstructured, 2:4 semi-structured, structured), the hardware that actually accelerates each, the LLM pruning methods that ship in production (Wanda, SparseGPT, structured depth pruning), and the correct order of operations when combining pruning with [4401](./4401-GPTQ.md)-style quantization.

## Does Sparsity Pay? Do the Math First

Sparse storage does not store zeros — it stores the nonzero values *plus indices to locate them*. That index tax is the whole story:

```text
Storage per weight

dense FP16:                 16 bits
CSR (value 16 + col 32):    48 bits PER NONZERO

break-even density d (where sparse storage = dense storage):
  d = value_bits / (value_bits + index_bits)

format           break-even density     sparsity needed to WIN
FP16 + CSR32     16/48  = 33%           > 67% sparsity
FP16 + CSR16     16/32  = 50%           > 50% sparsity
INT4  + CSR32    4/36   = 11%           > 89% sparsity
2:4 packed       ~44% effective         exactly 50% (fixed pattern)

Consequences
1. "50% unstructured sparsity = half the memory" is FALSE in
   CSR32 - you PAY MORE until past 67%
2. The better your quantization, the more sparsity has to give:
   on top of INT4 (4401), sparsity is nearly irrelevant for
   storage until ~90%
3. Sparsity's real winning card is SPEED on specific hardware
   (2:4 tensor cores) or a genuinely smaller model (structured)
   - not raw bit savings
```

```text
Speed reality, per regime

unstructured 50%     no GPU speedup (irregular access defeats
                     tiling); storage-only, and see above
2:4 semi-structured  2x math throughput on Ampere+ sparse
                     tensor cores; real-world end-to-end ~1.4-1.8x
structured (drop     genuine dense speedup - the model is
heads/layers)        literally smaller and denser
```

## The Three Sparsity Regimes

### Unstructured: Any Weights to Zero

```python
import torch
import torch.nn as nn
from torch.nn.utils import prune

model = ...  # any model with nn.Linear layers

for name, module in model.named_modules():
    if isinstance(module, nn.Linear):
        prune.l1_unstructured(module, name="weight", amount=0.5)
        # removes the 50% smallest-magnitude weights
```

```text
What you actually got
- a weight_mask buffer next to the weight (pruning in PyTorch
  is MASKED, not removed - run prune.remove(module, "weight")
  to bake it in)
- accuracy: at 50%, small models recover with fine-tuning
  (iterative magnitude pruning + rewinding); LLMs at 50%
  UNSTRUCTURED degrade badly one-shot
- deployment value: none without sparse runtime support - on
  GPUs, dense kernels beat sparse gather/scatter until very
  high sparsity
Verdict: a research baseline; skip for LLM deployment
```

### Semi-Structured 2:4: The Hardware-Aligned Pattern

Exactly 2 nonzeros per block of 4 (≤50% sparsity), which NVIDIA's sparse Tensor Cores execute at 2x math throughput:

```python
import torch

@torch.no_grad()
def apply_2to4_(weight: torch.Tensor) -> torch.Tensor:
    """Keep the 2 largest-magnitude entries of every block of 4
    along the last dim; zero the rest. In-place."""
    flat = weight.reshape(-1, 4)
    _, idx = torch.topk(flat.abs(), k=2, dim=1, largest=True)
    mask = torch.zeros_like(flat, dtype=torch.bool)
    mask.scatter_(1, idx, True)
    weight.reshape(-1, 4)[~mask] = 0
    return weight

# convert to the accelerated layout for Ampere+ execution:
# (requires a 2:4-masked tensor)
from torch.sparse import to_sparse_semi_structured

w2to4 = apply_2to4_(linear.weight)
linear.weight = torch.nn.Parameter(to_sparse_semi_structured(w2to4))
```

```text
Storage of 2:4: per block of 4 -> 2 values (full precision)
+ 2-bit index = (2*v + 2)/4 bits per weight
FP16: 8.5 bits (1.9x smaller); 2x math throughput
Caveat: the format conversion + metadata means end-to-end
speedup lands at ~1.4-1.8x, and only on Ampere (2020)+
```

### Structured: Remove Whole Units

Channels, attention heads, MLP intermediate dims, or entire **layers** — the result is a genuinely smaller dense model:

```text
Granularity ladder for transformers (coarse -> fine)
- layer / depth pruning    LLM-Pruner, Sheared-LLaMA: drop whole
                           blocks; recover with brief continued
                           pretraining. The only regime that
                           scales a 7B -> ~4-5B honestly
- head pruning             attention heads are near-independent;
                           20-40% of heads often removable with
                           light recovery
- intermediate-dim pruning FFN width is the biggest parameter
                           sink in LLMs; structured FFN slicing
                           gives real speed + real memory
Structured + quantization is THE production combination:
a structurally-pruned INT4 model beats a same-accuracy
denser-INT4 model on both size and speed.
```

## Hardware Support: The Honest Table

| Feature | NVIDIA | Intel | Apple/other |
|---|---|---|---|
| 2:4 sparse math | **Ampere+ (A100/H100/…)** — 2x tensor-core throughput | none | none |
| INT8 dot products | tensor cores | AMX / VNNI (fast INT8, **not** sparsity) | ANE |
| BF16/FP16 | tensor cores | AMX (4th-gen Xeon+) | ANE / Metal |

```text
Common misinformation, corrected
- "Intel AVX-512 VNNI accelerates 2:4 sparsity" - no. VNNI is
  INT8 dot-product throughput; it has no sparse mode
- torch.backends.cudnn.flags() has nothing to do with sparse
  execution - 2:4 runs through to_sparse_semi_structured +
  cuSPARSELt under the hood
- AMD MI-series: no 2:4 equivalent; do not build a 2:4
  deployment on hardware you do not own yet
```

## LLM Pruning Methods That Ship

The magnitude criterion that works for CNNs mostly fails on LLMs — the methods below are the ones with production traction.

### Wanda: One-Shot, Activation-Aware, No Retraining

Wanda (Sun et al., 2023) prunes by the product of weight magnitude and **input activation norm** — outlier-heavy activations make their incoming weights important regardless of magnitude:

```python
import torch

@torch.no_grad()
def wanda_prune_linear(linear, x_norms, sparsity=0.5):
    """x_norms: per-input-column ||x|| norms from a small
    calibration pass (a handful of sequences suffice)."""
    W = linear.weight                       # [out, in]
    metric = W.abs() * x_norms              # broadcast to [out, in]
    k = int(metric.numel() * sparsity)
    threshold = metric.flatten().kthvalue(k).values
    W[metric < threshold] = 0
    return linear
```

```text
Why kthvalue instead of torch.quantile
torch.quantile raises "input tensor is too large" above
16,777,216 elements - a 4096x4096 matrix is already past it.
Use kthvalue / topk on the flattened metric.
```

### SparseGPT: One-Shot at Higher Sparsity

SparseGPT (Frantar & Aichner, 2023 — same lab as GPTQ) solves a layer-wise reconstruction problem with an approximate inverse-Hessian, like GPTQ but with a sparsity mask instead of a bit-grid. It reaches 50-60% unstructured sparsity on OPT/LLaMA-class models one-shot; pair it with GPTQ for sparse+quantized checkpoints.

### Structured: LLM-Pruner and Sheared-LLaMA

```text
- LLM-Pruner: gradient+activation importance -> remove coupled
  structures (heads, FFN dims) -> brief LoRA recovery (~3% of
  pretraining data budget for usable quality)
- Sheared-LLaMA: learned structured pruning of LLaMA-2-7B to
  1.3B/2.7B with targeted continued pretraining - the reference
  result for "honestly smaller LLaMA"
Rule: structured pruning always costs a recovery-finetune
budget. One-shot structured pruning without recovery is a
random model generator.
```

## Combining with Quantization, Correctly

### Order of Operations

```text
prune -> recover -> quantize -> calibrate

1. PRUNE with the method matched to your regime (Wanda/SparseGPT
   unstructured; LLM-Pruner structured)
2. RECOVER: fine-tune briefly to heal pruning damage - pruning
   error and quantization error compound, so heal the first
   before measuring the second
3. QUANTIZE the sparse model (GPTQ 4401 / AWQ 4402 - their
   calibration handles the now-spikier weight distributions)
4. CALIBRATE end-to-end: measure the JOINT degradation, not the
   sum of individual losses - interactions are real and
   occasionally positive
```

### QAT with Masks: The Two Classic Bugs

If you go further into quantization-aware training of a pruned model, the fake-quantize step is where implementations go wrong:

```python
import torch
import torch.nn.functional as F

def fake_quant_weight(w, bits=4):
    """STE fake quant - RETURNS a new tensor, never mutates w."""
    qmax = 2 ** (bits - 1) - 1
    scale = w.abs().max() / qmax
    w_q = torch.round(w / scale).clamp(-qmax, qmax) * scale
    return w + (w_q - w).detach()      # straight-through estimator

def masked_qat_forward(x, linear, mask, bits=4):
    w = fake_quant_weight(linear.weight * mask, bits)   # apply mask
    return F.linear(x, w, linear.bias)                  # FUNCTIONAL -
                                                        # .weight untouched
```

```text
Bug 1 - in-place fake quant (the silent killer):
    module.weight.data = torch.round(w / s) * s
  overwrites the weights with their quantized selves EVERY
  forward - the model degrades step over step and gradients
  flow into rounded values. Fake quant must be FUNCTIONAL with
  a straight-through gradient (the (w_q - w).detach() term).

Bug 2 - unmasked gradients: pruned weights must stay pruned:
    mask = (w != 0)
    grad = grad * mask            # after backward, before step
  otherwise the optimizer resurrects pruned weights and your
  sparsity silently decays to zero over training.
```

### Gradual Sparsity Schedule

Jumping straight to the target sparsity wrecks accuracy; ramp it with a cubic schedule (Zhu & Gupta, 2017):

```text
s_t = s_final - (s_final - s_init) * (1 - (t - t0) / (T - t0))^3
      ramp from step t0 to T, then hold at s_final

intuition: most pruning happens in the MIDDLE of training -
early pruning removes weights the model still needs, late
pruning leaves no time to recover
```

## Best Practices

```text
1. Do the storage math before pruning: on top of INT4, only
   2:4 or structured sparsity changes anything
2. Unstructured sparsity buys NOTHING on standard GPU serving
   - choose it only with a sparse runtime (SparseGPT+GPTQ
   checkpoints on cuSPARSELt-class stacks)
3. 2:4 is the unstructured-looking option that actually
   accelerates - Ampere+ only; verify with a microbenchmark
   (to_sparse_semi_structured vs dense matmul) on your shapes
4. For a genuinely smaller LLM, prune STRUCTURED and pay the
   recovery budget - LLM-Pruner/Sheared-LLaMA-style pipelines
5. Activation-aware criteria (Wanda) >> plain magnitude for
   LLMs; keep calibration data small but IN-DISTRIBUTION
6. kthvalue/topk, never torch.quantile, on real matrices
7. Fake quant is functional + STE; masks reapply to gradients;
   measure prune+quant JOINTLY against the dense baseline
```

---

## References

### Related PROJECT-OMEGA Documents

- [4401: GPTQ](4401-GPTQ.md)
- [4402: AWQ](4402-AWQ.md)
- [4406: 1.58-bit Quantization](4406-1.58-bit-Quantization.md)

---

## Next Steps

- Continue with: **[4406: 1.58-bit Quantization](./4406-1.58-bit-Quantization.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
