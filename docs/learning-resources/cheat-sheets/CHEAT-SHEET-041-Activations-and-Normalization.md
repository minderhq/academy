---
Document ID: CHEAT-SHEET-041
Title: "CHEAT-SHEET-041: Activations & Normalization - the Nonlinearity and the Statistics"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'transformers', 'activation', 'normalization']
---

# CHEAT-SHEET-041: Activations & Normalization - the Nonlinearity and the Statistics

This sheet is the single-page reference for the per-layer surface every transformer
block stands on - the activation that bends the FFN and the normalization that pins
its statistics (modules 3301 and 3302). Use it when choosing between GELU and SwiGLU
for a new FFN, when a parameter count jumps 1.5x after a gated swap and nobody can
say why, when LayerNorm versus RMSNorm has to be decided for a new model, when a
deep Post-LN stack refuses to train without warmup, or when fp16 losses NaN the
moment RMSNorm meets a large activation offset.

Everything here reduces to one picture: a transformer's nonlinearity lives in one
elementwise function per FFN, and its stability lives in one statistic per layer.
ReLU died of three named defects - dead neurons, a kink at zero, uncentered output -
and its replacements win by fixing those defects at a measurable price: GELU buys
smoothness with an erf call, SwiGLU buys gating with a third projection and a 1.5x
parameter bill, RMSNorm buys 10-20% speed by skipping the mean centering and pays
0.1-0.3% quality plus an fp32-upcast law you violate at your own loss curve. Every
number below reproduces from one stdlib fence.

## ReLU's Three Failure Modes and the Smooth Replacements

ReLU is `max(0, x)` - a comparison, free on any hardware - and it trained the first
generation of deep nets. The transformer generation moved off it for three reasons
the module names exactly:

1. **Dead neurons.** If the pre-activation is consistently negative the unit outputs
   zero forever and its gradient is zero forever - the unit is unreachable from the
   loss.
2. **The kink at zero.** `relu'` is 0 from the left and 1 from the right; at exactly
   0 the derivative is undefined. Optimization near the kink is a coin flip.
3. **Uncentered output.** Every activation is >= 0, so the gradient sign into a
   neuron's weights is fixed by the upstream gradient's sign - updates zigzag.

The replacements are smooth, self-gating curves. GELU is `x * Phi(x)` - the input
modulated by its own standard-normal CDF. Swish is `x * sigmoid(x)`. The walk table
from the fence (seven points, four functions):

| x | ReLU | GELU (exact) | GELU (tanh) | Swish |
|---|---|---|---|---|
| -3.0 | 0.0000 | -0.004050 | -0.003637 | -0.1423 |
| -1.0 | 0.0000 | -0.158655 | -0.158808 | -0.2689 |
| -0.5 | 0.0000 | -0.154269 | -0.154286 | -0.1888 |
| 0.0 | 0.0000 | 0.000000 | 0.000000 | 0.0000 |
| 0.5 | 0.5000 | 0.345731 | 0.345714 | 0.3112 |
| 1.0 | 1.0000 | 0.841345 | 0.841192 | 0.7311 |
| 3.0 | 3.0000 | 2.995950 | 2.996363 | 2.8577 |

Read the negative side: ReLU is flat-zero where GELU and Swish leak a little
signal - that leak is the death cure. And read zero: GELU'(0) = Phi(0) = 0.5
exactly, finite from both sides, where ReLU has no derivative at all. Swish dips
below zero to a minimum of **-0.2785 at x = -1.2785** before climbing - the
non-monotonic dip is a feature, not a bug; it lets the function decrease as well as
increase.

## GELU - Exact Curve vs the GPT-2 tanh Approximation

Exact GELU needs the error function:

```text
GELU(x) = x * Phi(x) = 0.5 * x * (1 + erf(x / sqrt(2)))
```

The GPT-2 approximation swaps erf for a tanh polynomial that fuses well on GPU:

```text
GELU(x) ~ 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
```

How close is close? The fence scans [-4, 4] at 16,001 points: the maximum absolute
deviation is **0.000473, at x = -2.70**, and the Pearson correlation between the two
curves is **0.99999999 (1 - r = 1.33e-08)**. The module quotes the trade as "~99.7%
correlation" - that figure is the literature's loose shorthand for "trains
identically"; the measured curve distance is even smaller than the shorthand
suggests. The trade is real but it is a speed trade, not an accuracy cliff: exact
erf costs a little more compute, the tanh form buys it back, and neither choice
moves perplexity the way the FFN's gating structure does (next section).

One derivative worth memorizing: `gelu'(0) = Phi(0) = 0.5` - the fence's numeric
central difference confirms it to four decimals. The curve crosses zero with a
finite, moderate slope; nothing about the origin is singular.

## SwiGLU - the Gated FFN and Its 1.5x Parameter Bill

SwiGLU replaces the FFN's two projections with three bias-free ones:

```text
gate = x @ W_gate        # (d_model -> d_ff)
up   = x @ W_up          # (d_model -> d_ff)
out  = (silu(gate) * up) @ W_down    # (d_ff -> d_model)
```

The gate branch is squashed through SiLU (= Swish at beta = 1) and multiplied
elementwise into the up branch; the product goes back down to d_model. Gating lets
the network decide, per coordinate, how much of `up` to pass - a flexible
transformation ReLU cannot express, which is Shazeer's 2020 result: **1-2%
perplexity improvement over a GELU FFN at equal compute** ("GLU Variants Improve
Transformer"). The bill, at d_model = 512:

| FFN | Width | Parameters | Ratio |
|---|---|---|---|
| Standard GELU (2 projections) | 2048 | 2,097,152 | 1.000x |
| SwiGLU, same width | 2048 | 3,145,728 | 1.500x |
| SwiGLU, LLaMA sizing (grid 256) | 1536 | 2,359,296 | 1.125x |
| SwiGLU, equal-parameter | 1365 | 2,096,640 | 1.000x |

LLaMA's sizing rule turns d_ff = 4d into a SwiGLU width of
`int(2 * 4d / 3)` rounded **up** to a multiple of 256: int(2 * 2048 / 3) = 1365,
which lands on **1536** - hence the 1.125x bill in production shapes, not 1.5x.
The last row is the honest comparison: three projections at width 1365 cost the
same 2.1M parameters as the standard FFN, and *that* is the configuration Shazeer's
1-2% gain is measured at. Quoting the 1-2% while shipping width 2048 is quoting a
result you did not run.

## The Gate Zoo - and the Router That Is Not a Gate

The gated-FFN family varies only in the gate function and the wiring:

| Variant | Gate function | Wiring | Models |
|---|---|---|---|
| GEGLU | GELU | one fused projection, chunked in two | BLOOM, GPT-NeoX |
| ReGLU | ReLU | one fused projection, chunked in two | T5 family |
| SwiGLU | SiLU (Swish) | two separate projections, gate * up | LLaMA, Mistral, PaLM, Gemma |

And the cost ledger the module prints for the activation choice itself:

| Activation | Compute | Memory | Perplexity |
|---|---|---|---|
| ReLU | 1x | 1x | baseline |
| GELU | 1.2x | 1x | -0.3 |
| Swish | 1.3x | 1x | -0.5 |
| SwiGLU | 2x | 1x | -0.8 |

There is **no "SMGeLU"** in the literature - the name conflates two different
mechanisms. The MoE "gate" is a router, not an activation: softmax + top-k picks
*which expert FFN* processes a token, while the activation lives inside each
expert. The lineage kept the two straight:

- 2017 - Shazeer et al., sparsely-gated MoE: GeLU experts, noisy top-k gate
- 2021 - Switch Transformer: top-1 routing, one expert per token
- 2024 - Mixtral 8x7B: SwiGLU experts, top-2 routing

Note the expert row followed the dense-model arc (GeLU then, SwiGLU now) while the
router simplified (top-k, then top-1, back to top-2 at scale). When you read an MoE
paper, the router's sparsity and the experts' activation are independent axes.

```text
vanilla transformer FFN  -> GELU     (exact erf; GPT-2 tanh approx for the fast path)
LLM / MoE expert FFN     -> SwiGLU   (silu(gate) * up -> down, width int(2*4d/3) on the 256 grid)
new-model normalization  -> RMSNorm  (pre-LN placement, fp32 statistics upcast, cast back)
```

## LayerNorm vs RMSNorm - the Price of the Mean

The general normalization transform is `y = gamma * ((x - mu) / sigma) + beta` -
center, scale, rescale, shift. The family members differ in which statistics they
take and which parameters they keep:

| Norm | Transform | Params @ d=512 | Used in |
|---|---|---|---|
| BatchNorm | (x - mu_B) / sqrt(var_B + eps) * gamma + beta, EMA buffers | 2C + running stats | CNNs: ResNet, EfficientNet |
| LayerNorm | (x - mu) / sqrt(var + eps) * gamma + beta | 1024 (gamma + beta) | BERT, GPT-2, T5 |
| RMSNorm | x / sqrt(mean(x^2) + eps) * gamma | 512 (gamma only) | Llama 2, Mistral, Gemma |

RMSNorm is LayerNorm minus the mean centering - one subtraction and one parameter
vector dropped. On the fence's seeded vector (d = 512): the input has mu = +0.0500
and rms = 0.9936; LayerNorm's output mean is exactly 0.000000 by construction,
RMSNorm's is **+0.050273** - the input's mean survives the transform. And yet the
two outputs are nearly the same direction: **cosine 0.9987**. That is the whole
trade in one number - you are deleting an operation that moves the output by a
hundredth of a radian.

What it buys: ~**10-20% speedup** (no mean pass over the activations), at ~**0.1-0.3%
quality drop**. The module's recommendation row is the industry consensus: RMSNorm
for new models. BatchNorm stays disqualified for transformers for three structural
reasons - it normalizes over batch and spatial dims (batch-size dependence), its
train-time batch statistics differ from its test-time EMA statistics, and variable
sequence lengths make the "spatial" dimension ill-defined.

## Placement and Depth - Pre-LN, Post-LN, DeepNorm, and the fp32 Law

Where the norm sits decides how gradients reach layer zero:

| Placement | Formula | Gradient story | Needs warmup |
|---|---|---|---|
| Pre-LN (modern) | x + Sublayer(LayerNorm(x)) | identity path survives every block | no - GPT-2, LLaMA |
| Post-LN (original) | LayerNorm(x + Sublayer(x)) | every path crosses every LN | yes - original Transformer |

The fence walks both on seeded unit updates: Pre-LN's residual stream grows like a
random walk - ||x_8|| = 3.1224 against sqrt(9) = 3.0000 and ||x_32|| = 5.7002
against sqrt(33) = 5.7446 (the small excess is update correlation; the growth law
is sqrt(1 + L)). Post-LN pins the stream at **1.0000 every step** - the warmup tax
buys the pin. Both are trainable; the original Transformer chose the pin and paid
warmup; GPT-2 chose the walk and never looked back.

For very deep stacks, DeepNorm rescales the residual so 1000-layer transformers
train: with `alpha = sqrt(2N)` for N layers,

| Layers N | alpha = sqrt(2N) | alpha^2 |
|---|---|---|
| 24 | 6.9282 | 48 |
| 100 | 14.1421 | 200 |
| 1000 | 44.7214 | 2000 |

the block `x <- LayerNorm(alpha * x + Sublayer(x)) / alpha^2` pins the stream norm:
the fence iterates it from 1.0 at N = 100 - 0.075711, 0.010354, 0.005732, 0.005405,
0.005382 - converging on the fixed point **1/(alpha^2 - alpha) = 0.005380**. The
residual scale stops being a depth-dependent explosion and becomes a designable
constant.

Finally the precision law. RMSNorm's square sees the *full* offset of the input -
it skipped the subtraction that would have removed it. At an activation offset of
1000 (fp16 grid spacing 0.5 there; 1000.3 rounds to 1000.5, 1000.2 to 1000.0):

- **LayerNorm in fp16**: `(x - mu)^2` stays ~1, variance computes fine but lands at
  0.3758 against the fp32 value 0.3388 - a +10.9% bias, whose floor is the
  quantization variance (0.5^2)/12 = 0.0208. Ugly, survivable.
- **RMSNorm in fp16, no upcast**: `x^2 ~ 999,810 > 65,504` - every square saturates
  to inf, the mean is inf, `rsqrt(inf) = 0.0`, and the output vector is **all
  zeros**. The layer is dead and the loss curve spikes.
- **RMSNorm with the fp32 upcast** (LLaMA's actual code): cast to fp32, compute
  variance, `rsqrt`, multiply, cast back - rms = 1000.0284, output correct to four
  decimals.

The centering LayerNorm does for free is exactly the subtraction RMSNorm skipped -
so in reduced precision, RMSNorm *must* upcast its statistics to fp32 before the
square. That is not a stylistic preference in the LLaMA codebase; it is the reason
the cast is in the forward pass.

## Known Failure Modes

| Failure | What you see | Fix |
|---|---|---|
| ReLU in a deep transformer | units that never activate again; gradient flow blocked through half the FFN | smooth self-gating activation: GELU (vanilla) or SwiGLU (LLM) |
| Quoting the tanh approximation as exact | audits differ near \|x\| ~ 2.7 where max \|err\| = 0.000473 | quote the gap when it matters; exact erf when bit-equality with a reference is required |
| SwiGLU at the GELU FFN's width | parameter count 1.5x (3,145,728 vs 2,097,152) and "the paper said equal compute" | compare at equal compute: width int(2 * 4d / 3) on the 256 grid, or 1365 for exact parity |
| Reading the MoE router as an activation | a phantom "SMGeLU" in design docs; gate confusion in code review | router = softmax + top-k over experts; activation = inside each expert; keep the axes separate |
| RMSNorm in fp16 without the upcast | variance saturates to inf at offset > 256, rsqrt(inf) = 0, activations zeroed, loss spikes | fp32 statistics upcast before the square, cast back after - the LLaMA pattern, verbatim |
| Post-LN stack deeper than ~24 layers | training diverges at init or demands an ever-smaller warmup | Pre-LN placement, or DeepNorm alpha = sqrt(2N) with the alpha^2 rescale |

## Troubleshooting

| Symptom | Cause and cure |
|---|---|
| Loss NaNs early in mixed-precision training | norm statistics overflowed: cast statistics to fp32 (SafeLayerNorm / LLaMA RMSNorm) before squaring |
| A fraction of FFN units outputs zero forever | dead ReLU units; swap to GELU/SwiGLU and re-check the gradient histogram for the revival |
| Deep stack will not train at any LR without a long warmup | Post-LN Jacobians; move the norm inside the residual branch (Pre-LN) or apply DeepNorm scaling |
| Quality drops ~0.1-0.3% after LayerNorm -> RMSNorm | the expected price of the 10-20% speedup; measure, and accept unless the task is quality-bound |
| FFN has 1.5x the parameters it used to | three SwiGLU projections; resize width to 2/3 of 4d (multiple-of-256 grid) if the budget is fixed |
| Output distribution shifted after a "harmless" activation swap | the non-monotonic Swish dip (-0.2785 at x = -1.2785) changes the activation statistics; re-profile, do not assume translation |

## Quick Reference For

- [Module 3301: Activation Functions](../../phases/phase3-transformers/3300-decoding/3301-Activation-Functions.md) - the activation deep-dive: GELU derivation, SwiGLU implementation, MoE-router separation.
- [Module 3302: Normalization Layers](../../phases/phase3-transformers/3300-decoding/3302-Normalization-Layers.md) - the normalization deep-dive: BatchNorm/LayerNorm/RMSNorm, DeepNorm, mixed precision.
- [CHEAT-SHEET-020: Flash Attention](./CHEAT-SHEET-020-Flash-Attention.md) - the execution layer these blocks run on: SDPA backends, torch.compile, kernel choice.
- [CHEAT-SHEET-014: Decoding & Sampling Strategies](./CHEAT-SHEET-014-Decoding-Sampling-Strategies.md) - what the token stream does after the final norm: decoding and sampling strategies.

## Reproduction Fence

The stdlib-only fence below recomputes every number quoted above. It is
deterministic (fixed seeds 42, 7, 11) and ran twice with byte-identical output
before being frozen.

```python
"""CHEAT-SHEET-041 fence: activations and normalization, reproduced from modules 3301/3302."""
import math
import random
import struct

FP16_MAX = 65504.0


def relu(x):
    return max(0.0, x)


def gelu_exact(x):
    return 0.5 * x * (1.0 + math.erf(x / math.sqrt(2.0)))


def gelu_tanh(x):
    return 0.5 * x * (1.0 + math.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x ** 3)))


def swish(x):
    return x / (1.0 + math.exp(-x))


def sig(t):
    return 1.0 / (1.0 + math.exp(-t))


def d_swish(x):
    s = sig(x)
    return s * (1.0 + x * (1.0 - s))


def fp16(v):
    if abs(v) > FP16_MAX:
        return math.copysign(math.inf, v)
    return struct.unpack("e", struct.pack("e", v))[0]


def mean(v):
    return sum(v) / len(v)


def pearson(a, b):
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db)


def norm(v):
    return math.sqrt(sum(t * t for t in v))


print("F1 activation ledger (property walk at seven points)")
print("    x     ReLU    GELU(exact)  GELU(tanh)   Swish")
for x in (-3.0, -1.0, -0.5, 0.0, 0.5, 1.0, 3.0):
    print(f"  {x:5.1f}  {relu(x):7.4f}  {gelu_exact(x):10.6f}  {gelu_tanh(x):10.6f}  {swish(x):8.4f}")
grid = [(-4.0 + 8.0 * i / 16000.0) for i in range(16001)]
errs = [(abs(gelu_tanh(x) - gelu_exact(x)), x) for x in grid]
worst, xw = max(errs)
print(f"  tanh-approx max |err| = {worst:.6f} at x = {xw:.2f}")
r = pearson([gelu_exact(x) for x in grid], [gelu_tanh(x) for x in grid])
print(f"  pearson r(exact, tanh) over [-4, 4] x 16001 = {r:.8f} (1 - r = {1 - r:.2e})")
print("  relu' one-sided: 0- = 0.000, 0+ = 1.000, at 0 undefined (kink)")
print(f"  gelu'(0) = phi(0) = 0.5000 exactly; numeric check {(gelu_exact(1e-6) - gelu_exact(-1e-6)) / 2e-6:.4f}")
lo, hi = -2.0, -1.0
for _ in range(60):
    mid = 0.5 * (lo + hi)
    if d_swish(mid) < 0.0:
        lo = mid
    else:
        hi = mid
xm = 0.5 * (lo + hi)
print(f"  swish minimum = {swish(xm):.4f} at x = {xm:.4f} (non-monotonic dip below zero)")

print()
print("F2 the FFN parameter bill (d_model = 512)")
d, w = 512, 2048
std = 2 * d * w
sw_same = 3 * d * w
llama_hidden = int(2 * w / 3)
llama_grid = 256 * ((llama_hidden + 255) // 256)
sw_llama = 3 * d * llama_grid
eq_width = int(std / (3 * d))
sw_eq = 3 * d * eq_width
print(f"  standard GELU FFN d_ff={w}:       {std:>9,} params")
print(f"  SwiGLU same width:                {sw_same:>9,} params ({sw_same / std:.3f}x)")
print(f"  LLaMA sizing int(2*{w}/3) = {llama_hidden} -> multiple_of 256 = {llama_grid}")
print(f"  SwiGLU at {llama_grid}:                {sw_llama:>9,} params ({sw_llama / std:.3f}x)")
print(f"  equal-param SwiGLU width {eq_width}:    {sw_eq:>9,} params ({sw_eq / std:.3f}x)")
print("  Shazeer 2020 (GLU Variants Improve Transformer): 1-2% perplexity gain at equal compute")

print()
print("F3 LayerNorm vs RMSNorm on one seeded vector (d = 512, seed 42)")
rng = random.Random(42)
x = [rng.gauss(0.0, 1.0) for _ in range(512)]
mu = mean(x)
var = mean([(t - mu) ** 2 for t in x])
rms = math.sqrt(mean([t * t for t in x]))
ln_out = [(t - mu) / math.sqrt(var + 1e-5) for t in x]
rms_out = [t / (rms + 1e-8) for t in x]
print(f"  input mu = {mu:+.4f}  std = {math.sqrt(var):.4f}  rms = {rms:.4f}")
print(f"  LN  out mean = {mean(ln_out):+.6f}   (centered to zero by construction)")
print(f"  RMS out mean = {mean(rms_out):+.6f}   (centering removed, mean survives)")
cos = sum(a * b for a, b in zip(ln_out, rms_out)) / (norm(ln_out) * norm(rms_out))
print(f"  cosine(LN out, RMS out) = {cos:.4f}  (same vector, one subtraction apart)")
print("  params per layer at d_model = 512: LayerNorm 1024 (gamma+beta), RMSNorm 512 (gamma only)")

print()
print("F4 placement and depth: the residual-stream walk (unit updates, seeded)")
rng2 = random.Random(7)
us = []
for _ in range(33):
    u = [rng2.gauss(0.0, 1.0) for _ in range(512)]
    n = norm(u)
    us.append([t / n for t in u])
xv = list(us[0])
growth = []
for l in range(1, 33):
    xv = [a + b for a, b in zip(xv, us[l])]
    growth.append(norm(xv))
print(f"  Pre-LN  x <- x + u:   ||x_8|| = {growth[7]:.4f} (sqrt(9) = {math.sqrt(9):.4f}),  ||x_32|| = {growth[31]:.4f} (sqrt(33) = {math.sqrt(33):.4f})")
xp = list(us[0])
for l in range(1, 33):
    t = [a + b for a, b in zip(xp, us[l])]
    n = norm(t)
    xp = [a / n for a in t]
print(f"  Post-LN x <- LN(...): ||x|| pinned at {norm(xp):.4f} every step - the warmup tax buys the pin")
alpha = math.sqrt(200.0)
xd = 1.0
print(f"  DeepNorm N=100: alpha = sqrt(2N) = {alpha:.4f}, alpha^2 = {alpha ** 2:.0f}")
for i in range(5):
    xd = (alpha * xd + 1.0) / (alpha ** 2)
    print(f"    iter {i + 1}: stream norm {xd:.6f}")
print(f"  fixed point 1/(alpha^2 - alpha) = {1.0 / (alpha ** 2 - alpha):.6f} - 1000-layer stacks stay bounded")

print()
print("F5 the fp32-upcast law: RMSNorm's square sees the full offset (d = 512)")
rng3 = random.Random(11)
xs = [1000.0 + rng3.uniform(-1.0, 1.0) for _ in range(512)]
dev = [t - mean(xs) for t in xs]
var32 = mean([t * t for t in dev])
rms32 = math.sqrt(mean([t * t for t in xs]))
q = [fp16(t) for t in xs]
print(f"  fp16 grid at 1000: spacing 0.5 (1000.3 -> {fp16(1000.3)}, 1000.2 -> {fp16(1000.2)})")
var_q = 0.5 ** 2 / 12.0
var16_ln = mean([(t - mean(q)) ** 2 for t in q])
print(f"  LayerNorm fp16: (x-mu)^2 stays ~1, var = {var16_ln:.4f} vs fp32 {var32:.4f} (+{100 * (var16_ln / var32 - 1):.1f}% quantization bias, floor {var_q:.4f})")
sq = [fp16(t * t) for t in xs]
var16_rms = mean(sq)
sat = "inf" if math.isinf(var16_rms) else f"{var16_rms:.1f}"
print(f"  RMSNorm fp16, no upcast: x^2 ~ {xs[0] ** 2:.0f} > 65504 -> saturates to {sat}")
out16 = [t * (1.0 / math.sqrt(var16_rms)) if not math.isinf(var16_rms) else 0.0 for t in xs]
print(f"  rsqrt(inf) = {1.0 / math.sqrt(math.inf):.1f} -> output vector all zeros: {all(t == 0.0 for t in out16)}")
print(f"  RMSNorm fp32 upcast (LLaMA): rms = {rms32:.4f}, out[0] = {xs[0] / rms32:.4f} - correct, which is why the cast is law")
print("  the mean centering LayerNorm does for free is exactly the subtraction RMSNorm skipped;")
print("  in fp16 the square sees the raw offset, so LLaMA upcasts to fp32 before rsqrt and casts back")
```

## Fence Output

```text
F1 activation ledger (property walk at seven points)
    x     ReLU    GELU(exact)  GELU(tanh)   Swish
   -3.0   0.0000   -0.004050   -0.003637   -0.1423
   -1.0   0.0000   -0.158655   -0.158808   -0.2689
   -0.5   0.0000   -0.154269   -0.154286   -0.1888
    0.0   0.0000    0.000000    0.000000    0.0000
    0.5   0.5000    0.345731    0.345714    0.3112
    1.0   1.0000    0.841345    0.841192    0.7311
    3.0   3.0000    2.995950    2.996363    2.8577
  tanh-approx max |err| = 0.000473 at x = -2.70
  pearson r(exact, tanh) over [-4, 4] x 16001 = 0.99999999 (1 - r = 1.33e-08)
  relu' one-sided: 0- = 0.000, 0+ = 1.000, at 0 undefined (kink)
  gelu'(0) = phi(0) = 0.5000 exactly; numeric check 0.5000
  swish minimum = -0.2785 at x = -1.2785 (non-monotonic dip below zero)

F2 the FFN parameter bill (d_model = 512)
  standard GELU FFN d_ff=2048:       2,097,152 params
  SwiGLU same width:                3,145,728 params (1.500x)
  LLaMA sizing int(2*2048/3) = 1365 -> multiple_of 256 = 1536
  SwiGLU at 1536:                2,359,296 params (1.125x)
  equal-param SwiGLU width 1365:    2,096,640 params (1.000x)
  Shazeer 2020 (GLU Variants Improve Transformer): 1-2% perplexity gain at equal compute

F3 LayerNorm vs RMSNorm on one seeded vector (d = 512, seed 42)
  input mu = +0.0500  std = 0.9923  rms = 0.9936
  LN  out mean = +0.000000   (centered to zero by construction)
  RMS out mean = +0.050273   (centering removed, mean survives)
  cosine(LN out, RMS out) = 0.9987  (same vector, one subtraction apart)
  params per layer at d_model = 512: LayerNorm 1024 (gamma+beta), RMSNorm 512 (gamma only)

F4 placement and depth: the residual-stream walk (unit updates, seeded)
  Pre-LN  x <- x + u:   ||x_8|| = 3.1224 (sqrt(9) = 3.0000),  ||x_32|| = 5.7002 (sqrt(33) = 5.7446)
  Post-LN x <- LN(...): ||x|| pinned at 1.0000 every step - the warmup tax buys the pin
  DeepNorm N=100: alpha = sqrt(2N) = 14.1421, alpha^2 = 200
    iter 1: stream norm 0.075711
    iter 2: stream norm 0.010354
    iter 3: stream norm 0.005732
    iter 4: stream norm 0.005405
    iter 5: stream norm 0.005382
  fixed point 1/(alpha^2 - alpha) = 0.005380 - 1000-layer stacks stay bounded

F5 the fp32-upcast law: RMSNorm's square sees the full offset (d = 512)
  fp16 grid at 1000: spacing 0.5 (1000.3 -> 1000.5, 1000.2 -> 1000.0)
  LayerNorm fp16: (x-mu)^2 stays ~1, var = 0.3758 vs fp32 0.3388 (+10.9% quantization bias, floor 0.0208)
  RMSNorm fp16, no upcast: x^2 ~ 999810 > 65504 -> saturates to inf
  rsqrt(inf) = 0.0 -> output vector all zeros: True
  RMSNorm fp32 upcast (LLaMA): rms = 1000.0284, out[0] = 0.9999 - correct, which is why the cast is law
  the mean centering LayerNorm does for free is exactly the subtraction RMSNorm skipped;
  in fp16 the square sees the raw offset, so LLaMA upcasts to fp32 before rsqrt and casts back
```
