---
Document ID: 4407
Title: Ternary & Binary Networks
Phase: 4
Module: 4400
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'binary', 'ternary', 'bnn', 'hardware']
---

# 4407: Ternary & Binary Networks

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Design Space](#the-design-space)
- [The XNOR + Popcount Identity](#the-xnor--popcount-identity)
- [A Working Binary Layer](#a-working-binary-layer)
- [Ternary Variants: TWN and TTQ](#ternary-variants-twn-and-ttq)
- [Training Binary Networks](#training-binary-networks)
- [Hardware: What Actually Executes This](#hardware-what-actually-executes-this)
- [State of the Art](#state-of-the-art)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Classify binary/ternary methods by WHICH tensors are quantized (weights only vs weights+activations) and predict the accuracy cost of each choice
- Derive the XNOR + popcount identity that turns a ±1 matmul into bit operations
- Implement a binary linear layer with a correct straight-through estimator and latent full-precision weights
- Implement TTQ with learned scales flowing gradients through the masks — and say why the `.data`-mutation version is wrong
- State the 2026 status: where binary networks live (edge vision, FPGA), why binary activations never reached LLMs, and how that differs from the ternary-weights path of [4406](4406-1.58-bit-Quantization.md)

---

## Abstract

Binary ({-1, +1}) and ternary ({-1, 0, +1}) networks push quantization past the bit-grid methods of [4401](4401-GPTQ.md) into codebook-free discrete domains where matrix multiplication becomes pure bit arithmetic — XNOR and popcount for binary, additions for ternary. The literature here spans a decade and is easy to mix up, so this lesson organizes it by *what is quantized*: binary weights with real activations (BWN), both binary (BNN/XNOR-Net), ternary weights with fixed scales (TWN), ternary with learned scales (TTQ), and the modern branch that actually ships — ternary weights + 8-bit activations (BitNet, [4406](4406-1.58-bit-Quantization.md)). Along the way: a correct straight-through estimator, a from-first-principles XNOR derivation, packed-bit kernels for CPU and GPU, and the honest reason binary *activations* — not binary weights — is the part that never scaled to LLMs.

## The Design Space

Every method in this lesson is a point on two axes: which tensors are discretized, and whether the scales are fixed or learned.

| Method | Year | Weights | Activations | Scales | Domain |
|---|---|---|---|---|---|
| BWN | 2016 | ±1 | FP | fixed α | vision |
| BinaryConnect | 2015 | ±1 | FP | — | vision |
| BNN / XNOR-Net | 2016 | ±1 | ±1 | fixed α | vision, FPGA |
| TWN | 2016 | {-1,0,+1} | FP | fixed α | vision |
| TTQ | 2017 | {-1,0,+1} | FP | **learned** | vision |
| ReActNet line | 2020 | ±1 | ±1 | learned/reshaped | vision |
| **BitNet b1.58** | 2024 | {-1,0,+1} | **INT8** | learned | **LLM** |

```text
Two axes carry most of the insight

axis 1 - WEIGHTS vs ACTIVATIONS
  binary/ternary WEIGHTS are stored discretely but are a
  static choice - the network adapts during training
  binary/ternary ACTIVATIONS are dynamic: every layer's
  forward output must survive rounding to +-1, which destroys
  the residual stream's dynamic range. This is why binary
  activations cost far more accuracy than binary weights,
  and why BitNet (4406) kept activations at INT8

axis 2 - FIXED vs LEARNED SCALES
  BWN/TWN/BNN: one alpha = mean(|W|)-style constant per layer
  TTQ/BitNet: the non-zero VALUES are learned parameters -
  worth several accuracy points and one more moving part
```

## The XNOR + Popcount Identity

Why a ±1 matmul is bit arithmetic — derive it once and the kernels all make sense:

```text
Map the sign domain to the bit domain:
    a, b in {-1,+1}  <->  a', b' in {0,1}   (a = 2a' - 1)

Per-element product in the sign domain:
    a*b = +1  iff  a' == b'   (the bits are EQUAL)
    a*b = -1  iff  a' != b'   (the bits DIFFER)

Sum over k elements (a row . a column):
    SUM a_i*b_i = (#equal) - (#different)
                = (#equal) - (k - #equal)
                = 2*popcount(XNOR(a', b')) - k

So one dot product = pack K bits into words,
XNOR word-wise, popcount, scale by 2, shift by k.
No multiplies. K bit-ops per output element.
```

The same identity in reverse tells you the storage: ±1 packs to exactly 1 bit per weight; {-1, 0, +1} packs to 2 bits per weight (4406).

## A Working Binary Layer

The training-time form runs as a normal linear layer on straight-through-estimated ±1 tensors; the packed XNOR kernel is the *inference* primitive for the same computation:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

def sign_ste(x):
    """sign(x) with a straight-through estimator: forward sees
    +-1, backward pretends the map was the identity. x=0 -> +1."""
    s = torch.where(x >= 0, 1.0, -1.0)
    return x + (s - x).detach()

class BinaryLinear(nn.Module):
    """BNN-style layer: binary weights AND activations.
    Latent FP parameters stay trainable; BN precedes
    binarization (BN's output statistics are what makes
    +-1 rounding survivable)."""

    def __init__(self, in_features, out_features):
        super().__init__()
        self.weight = nn.Parameter(
            torch.randn(out_features, in_features) * 0.1)
        self.bn = nn.BatchNorm1d(in_features)
        self.bias = nn.Parameter(torch.zeros(out_features))

    def forward(self, x):
        x = self.bn(x)
        x_b = sign_ste(x)                      # binary activations
        w_b = sign_ste(self.weight)            # binary weights
        # TRAINING: dense +-1 matmul (autograd handles STE)
        # INFERENCE: pack x_b, w_b -> XNOR + popcount kernel
        return F.linear(x_b, w_b, self.bias)
```

```text
The three details that decide whether this trains
1. BN BEFORE binarization - unnormalized activations have
   outliers that all round to +1 and carry no information
2. sign at exactly 0: pick a side (here +1) - torch.sign(0)=0
   would silently create a THIRD state and break the kernel
3. STE on both weights and activations - sign()'s gradient is
   zero almost everywhere; without STE nothing trains
```

### The Packed Inference Kernel

```python
import torch

_BITCOUNT = torch.tensor(
    [bin(i).count("1") for i in range(256)], dtype=torch.long)

def pack_bits(t: torch.Tensor) -> torch.Tensor:
    """[..., K] of +-1 -> [..., ceil(K/64)] int64 bit-packed words."""
    b = (t > 0).long()                       # {-1,+1} -> {0,1}
    pad = (-b.shape[-1]) % 64
    if pad:
        b = torch.nn.functional.pad(b, (0, pad))
    bits = b.unflatten(-1, (-1, 64))
    weights = 1 << torch.arange(64, device=t.device, dtype=torch.long)
    return (bits * weights).sum(-1)          # one word per 64 weights

def xnor_popcount_matmul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """a [M,K], b [K,N] as +-1 -> the same result as a@b, via
    XNOR + popcount. Teaching primitive - real kernels fuse
    these ops in CUDA/SIMD; the math is the point."""
    ab = pack_bits(a)                        # [M, W]
    bb = pack_bits(b.T)                      # [N, W]
    xnor = ~(ab.unsqueeze(1) ^ bb.unsqueeze(0))     # [M, N, W]
    counts = _BITCOUNT.to(xnor.device)[
        xnor.view(torch.uint8).long()].sum(-1)      # [M, N]
    return (2 * counts - a.shape[-1]).float()
```

```text
Notes on the kernel
- int64 words with 64-bit packing: every byte of every word is
  meaningful, so a uint8 reinterpret + 256-entry lookup table
  gives the popcount with no shifts and no version hazards
- (b > 0) on the TRANSPOSE aligns output channels as rows so
  the broadcast is [M,1,W] vs [1,N,W]
- memory: the [M,N,W] intermediate is huge - production XNOR
  kernels tile in shared memory/registers. For benchmarking
  claims, measure a fused kernel, not this function
```

### CPU: NumPy (vectorized, no loops)

```python
import numpy as np

_POPCOUNT8 = np.unpackbits(
    np.arange(256, dtype=np.uint8)[:, None], axis=1).sum(1)

def pack_bits_np(t: np.ndarray) -> np.ndarray:
    """[..., K] -> [..., ceil(K/64)] uint64, little-endian bits."""
    b = (t > 0).astype(np.uint8)
    pad = (-b.shape[-1]) % 64
    if pad:
        b = np.pad(b, [(0, 0)] * (b.ndim - 1) + [(0, pad)])
    return np.packbits(b, axis=-1, bitorder="little").view(np.uint64)

def xnor_popcount_np(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ab = pack_bits_np(a)                     # [M, W]
    bb = pack_bits_np(b.T)                   # [N, W]
    xnor = ~(ab[:, None, :] ^ bb[None, :, :])       # [M, N, W]
    counts = _POPCOUNT8[xnor.view(np.uint8)].sum(-1)
    return (2.0 * counts - a.shape[-1]).astype(np.float32)
```

## Ternary Variants: TWN and TTQ

Ternary keeps a zero state, which buys expressivity back — and the two canonical methods differ exactly on the fixed-vs-learned-scale axis.

### TWN: Fixed Scale (the 4406 recipe)

```text
TWN (Li & Liu, 2016) - the rule [4406] implements:
  delta = 0.75 * mean(|W|)
  alpha = mean(|w_i| : |w_i| > delta)      per layer, fixed
  W'    = alpha * sign-ternary(W; delta)
Trained with STE from latent FP weights. No learned scales.
```

### TTQ: Learned Scales

TTQ (Zhu et al., 2017) keeps the ternary *pattern* but makes the non-zero values trainable parameters — gradients reach them through the masks:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class TTQLinear(nn.Module):
    """Trained Ternary Quantization:
    masks from a fixed threshold ratio, non-zero VALUES
    (w_p, w_n) learned by backprop through the STE masks."""

    def __init__(self, in_features, out_features, t=0.05):
        super().__init__()
        self.weight = nn.Parameter(
            torch.randn(out_features, in_features) * 0.1)
        self.w_p = nn.Parameter(torch.tensor(0.1))   # value of +1s
        self.w_n = nn.Parameter(torch.tensor(-0.1))  # value of -1s
        self.t = t                    # threshold ratio (hyperparam)

    def forward(self, x):
        delta = self.t * self.weight.abs().max()
        ternary = torch.sign(self.weight) * \
            (self.weight.abs() > delta).float()      # {-1,0,+1}
        # STE: gradient flows to latent weights through the mask
        t_ste = self.weight + (ternary - self.weight).detach()
        # non-zeros take the LEARNED scale values
        w = torch.where(
            t_ste > 0, self.w_p,
            torch.where(t_ste < 0, self.w_n, t_ste))
        return F.linear(x, w)
```

```text
Why the common shortcut is wrong
    self.w_p.data = (weight * mask_pos).sum() / mask_pos.sum()
  (computing scales as running means INSIDE forward) is not
  TTQ - it is TWN's fixed scale computed per-batch, and the
  .data write detaches it from training entirely. TTQ's whole
  point is that w_p/w_n receive GRADIENTS and converge to
  useful magnitudes per layer. (Same in-place pattern as
  Bug 1 in 4405.)
Threshold ratios in the paper: t in [0.03, 0.3], tuned per
layer; keep it a hyperparameter unless you have a reason.
```

## Training Binary Networks

### The Recipe That Works

```text
1. latent FP weights, CLIPPED: keep self.weight.data.clamp_(-1, 1)
   after optimizer steps (BinaryConnect's trick) - sign() of a
   huge latent weight saturates; clipping keeps its STE
   gradient alive
2. BN (or LN) before every binarization, including activations
3. two-stage schedule, honestly labeled:
   - stage 1: FP (or BitLinear-style low-bit) pretraining
   - stage 2: switch to binary, lower LR (10x down), fine-tune
   end-to-end binary training from step 0 also works for CNNs
   but needs careful warmup (5502) - the STE gradient is
   noisiest exactly when training is most fragile
4. distillation from the FP teacher (soft targets, T=3-5,
   KL + task loss) recovers 1-3 points on small models - the
   same recipe shown in 4406
```

### What Kills Accuracy in Practice

```text
- binary ACTIVATIONS, not weights: going weights-only to
  both-binary costs most methods 5-15 points on ImageNet.
  Every layer's output must survive sign() rounding; the
  first-layer and last-layer representations are the most
  exposed (many BNNs keep first/last layers FP for this
  reason)
- missing the residual-stream problem: transformers keep an
  additive residual stream whose dynamic range the network
  tunes - rounding it to +-1 every block destroys it. This is
  the structural reason binary activations never reached LLMs
  (BitNet quantizes the ACTIVATIONS only to INT8, 4406)
```

## Hardware: What Actually Executes This

```text
Where the bit-arithmetic story is real
- CPUs: 64-bit XNOR+popcount is 1-2 SIMD instructions per 64
  weights (VPOPCNTDQ on AVX-512, NEON cnt) - binary models
  hit their published throughput only via these packed paths
- FPGAs/microcontrollers: the classic BNN home - LUT networks
  (LogicNets-class) map binarized MLPs directly to lookup
  tables for hard real-time constraints
- GPUs: no shipped PyTorch BNN kernel; the teaching kernel
  above shows the math, production uses custom CUDA

Where the story silently downgrades
- run a binary layer through dense +-1 float matmuls (the
  training path) and you get NO speedup and NO energy win -
  same FLOPs as FP16 with worse numerics. The hardware claim
  only exists on packed kernels
- ternary follows the same rule: BitNet-class models need
  ternary-aware kernels (bitnet.cpp, 4406) - otherwise INT4
  GPTQ (4401) wins on stock GPU stacks
```

## State of the Art

Paper-reported numbers, ResNet-18 on ImageNet — the canonical benchmark lineage for this literature:

| Recipe | Weights/Acts | Top-1 (paper) | Gap |
|---|---|---|---|
| Full precision | FP/FP | 69.8% | — |
| TWN | ternary/FP | ~61-62% | ~-8 pts |
| TTQ | ternary/FP | 65.3% | ~-4.5 pts |
| ReActNet-A (2020) | **binary/binary** | 69.4% | ~-0.4 pts |

```text
Reading the lineage
- 2016: first-generation BNNs sat 10-18 points under FP;
  binary weights were cheap, binary activations were the cost
- 2017: learned scales (TTQ) close ~4 of those points on the
  ternary/FP side
- 2020: ReActNet-class methods (activation reshaping +
  training recipes) bring FULL binary to near-parity on
  ResNet-18-class CNNs - the proof that binary CAN work
- LLMs took the other fork: binary activations never scaled
  to transformers; the 1-bit-LLM branch that shipped is
  ternary weights + INT8 activations (BitNet, 4406), and it
  also chose TRAINING-TIME quantization over post-training
```

## Best Practices

```text
1. First question for any binary/ternary paper: what is
   quantized - weights, activations, or both? The accuracy
   story is decided by activations, not weights
2. STE + latent FP weights + BN-before-binarize + clip latents
   to [-1,1]: the four load-bearing training details; a
   missing one shows up as a loss that will not descend
3. Keep first and last layers FP in binary models - the
   input/output interfaces are where binary hurts most
4. Learned scales (TTQ-style) over fixed means when accuracy
   matters; they are two scalars per layer
5. Never demo "speedup" with dense +-1 float matmuls - state
   which packed kernel the claim assumes, and measure on it
6. For LLM work: this lesson is background; the deployable
   branch of 1-bit research is 4406 (ternary weights + INT8
   acts, trained in the loop). Do not post-train either
7. kthvalue/topk, never torch.quantile, on real matrices
   (same 16.7M-element limit as 4405/4406)
```

---

## References

### Related PROJECT-OMEGA Documents

- [4405: Sparsity + Quantization](4405-Sparsity-Quantization.md)
- [4406: 1.58-bit Quantization](4406-1.58-bit-Quantization.md)

---

## Next Steps

- Continue with: **[4408: Quantizing for Production](./guides/4408-Quantizing-for-Production.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
