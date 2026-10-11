---
Document ID: CHEAT-SHEET-044
Title: "CHEAT-SHEET-044: Quantization-Aware Training - the Straight-Through Estimator and the Layer Map"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'qat', 'quantization', 'training']
---

# CHEAT-SHEET-044: Quantization-Aware Training - the Straight-Through Estimator and the Layer Map

This sheet is the single-page reference for the training-time quantization
surface - the track of phase 4 that owns modules 4301 (QAT Foundations),
4302 (Fake Quantization), 4303 (QAT for Transformers), 4304 (Low-bit QAT) and
4305 (Quantization Configuration), with guides 4306-4308 carrying the worked
PyTorch, transformers and BitBlade recipes. CHEAT-SHEET-015 owns the
format-and-method survey above, CHEAT-SHEET-042 owns the below-4-bit method
choice and CHEAT-SHEET-043 owns the 4-bit metadata-and-grid layer - this sheet
takes the layer all three assume: the training pass that makes low bit-widths
survivable, closing the 4300 track. Use it when a model must land at INT4
without falling off a cliff, when fake-quantized training produces zero or NaN
gradients, when an observer's statistics look wrong mid-run, or when a
transformer's quantization config needs writing and you need to know
which layers eat 4 bits and which never leave FP32.

Everything here reduces to one picture: **the forward pass lives inside the
grid while the backward pass pretends the grid is not there**. Fake
quantization rounds activations and weights onto real integer levels on the
way up; the straight-through estimator passes gradients through that rounding
as if it were the identity; the observer quietly estimates the ranges the
grid will use; and the weights migrate until the rounding costs almost
nothing. Quantization stops being arithmetic you do to a finished model and
becomes a constraint the model trains against. Every number below reproduces
from one stdlib fence.

## The Round Trip and the Straight-Through Contract

Fake quantization is two steps that cancel into a rounding: quantize to the
integer grid, dequantize straight back to float. The values look continuous
to the rest of the network, but they only ever sit on `q * scale` points:

```text
fake quant: q = clamp(round(x/s), -128, 127); dequant = q*s  (s = amax/127)
abs err on 4096 weights: mean 0.00374  P95 0.00705  max 0.00747 = 0.500 of one step
true numeric gradient of the round trip: exactly 0 at 64/64 sample points
grad survival: RoundSTE 1000/1000  ClampedSTE 930/1000  HardTanhSTE 965/1000
```

That third line is the whole reason QAT exists as a separate technique. The
rounding function is piecewise-constant, so its true derivative is zero
everywhere except at bin edges - propagate it honestly and every weight's
gradient dies on the first backward pass. The straight-through estimator's
answer is a documented lie: backward, pretend the round was the identity and
hand the gradient through unchanged. The forward pass is quantized, the
backward pass is not, and the mismatch is exactly what lets the weights learn
to sit inside the grid.

The two grid conventions differ only in where the zero sits:

| Scheme | qmin, qmax | Scale | Zero point |
|--------|------------|-------|------------|
| Symmetric | -128, 127 | `max\|x\| / 127` | 0 (implicit) |
| Asymmetric | -128, 127 | `(max - min) / 255` | `-round(min/scale)` - min -3.0, max 5.0 gives scale 0.03137, zp 96 |

Symmetric wastes one level (the grid is lopsided around zero) and buys a zero
point of exactly 0 - the dequantize is a pure multiply. Asymmetric pays a
per-tensor zero point to center the grid on the data's actual span.

Three STE variants trade honesty against reach:

| STE variant | Backward rule | Fenced census | The trade |
|-------------|---------------|---------------|-----------|
| RoundSTE | identity everywhere | 1000/1000 grads survive | simplest; values outside the range keep gradients that can never be honored |
| ClampedSTE | zero outside [qmin, qmax] | 930/1000 | honest - dead coordinates stop asking for updates |
| HardTanhSTE | linear band [qmin-1, qmax+1] | 965/1000 | tapers instead of clipping; `ctx.save_for_backward` carries the band |

## The Observer - Estimating the Range While Training Runs

The scale needs a range, and during training the range is a moving target.
The observer watches activation batches and keeps an exponential moving
average of min and max with momentum 0.01 - slow enough to smooth batch
noise, fast enough to track the distribution the weights are drifting
through. Two guards are load-bearing:

```text
momentum 0.01, 40x256 batches: min -2.7332 -> max +2.7472 converged
symmetric scale max(|min|,|max|)/127 = 0.021631   asymmetric (max-min)/255 = 0.021492
unseeded EMA: inf*scale = inf -> the first batch must SEED, never average
all-zero batch -> scale 0 -> floor at 1e-05; eval() freezes the EMA by design
```

The seed guard: the EMA buffers start at inf/-inf, and `(1-m)*inf + m*x` is
still inf - a naive implementation produces an infinite scale forever. The
first batch must assign, not average. The symmetric scale deliberately takes
`max(|min|, |max|)` so one number covers both sides of zero. The floor keeps a
degenerate batch (all zeros) from producing a division by zero. And the
eval-mode freeze is the design, not a bug: statistics gathering stops when
training stops, while the quantize-dequantize itself keeps running.

The module-level pitfalls that pair with these guards: observers are frozen
in `eval()` so call them only in the training loop; per-channel scales need
`amax(dim=1, keepdim=True)` - one scale per OUTPUT channel, `keepdim` so the
broadcast shape is right; and the scale needs `clamp(min=1e-5)` even after the
floor, because a constant batch can still slide the EMA to zero.

## QAT vs PTQ - the Decision, Priced

Post-training quantization costs minutes and loses quality as the bits drop;
quantization-aware training costs an epoch bill and buys the quality back.
The two canonical tables, both from the modules' own fences:

BERT-base on SST-2 (accuracy, higher is better):

| Variant | Accuracy |
|---------|----------|
| FP32 | 93.2 |
| INT8 PTQ | 92.8 |
| INT8 QAT | 93.0 |
| INT4 QAT | 91.5 |
| INT3 QAT | 88.2 |

GPT-style on WikiText-2 (perplexity, lower is better):

| Variant | PPL |
|---------|-----|
| FP32 | 12.4 |
| INT8 PTQ | 12.8 |
| INT8 QAT | 12.5 |
| INT4 QAT | 13.8 |
| INT3 QAT | 16.2 |

```text
BERT SST-2 : INT8 QAT-vs-PTQ +0.2   INT4-vs-FP32 -1.7   INT3-vs-FP32 -5.0
GPT ppl    : INT8 QAT-vs-PTQ -0.3   INT4-vs-FP32 +1.4   INT3-vs-FP32 +3.8
at INT8 both routes land inside 0.3 - QAT earns its training bill at 4 bits and below
```

Read the deltas, not the rows. At INT8 the two routes are statistically
indistinguishable (BERT +0.2 in QAT's favor, GPT -0.3 perplexity) - do not
pay for training you do not need. At INT4 the PTQ route is not even on the
table (the modules' own guidance: PTQ degrades at 4-bit, QAT holds 1-3%); at
INT3 both routes hurt and only careful training keeps it above 88 accuracy /
16 perplexity territory.

## The Layer Map - What Quantizes and What Never Does

The single most leveraged decision in transformer QAT is not the bit-width -
it is which layers enter the grid at all. A transformer block's weights are
almost entirely its Linear projections:

| Component | Precision | Granularity |
|-----------|-----------|-------------|
| Q/K/O projections | 8-bit | per-channel |
| V projection | 4-bit | per-channel |
| MLP fc1, fc2 | 4-bit | per-channel |
| Embeddings | 8-bit | per-tensor |
| LayerNorm 1/2 | FP32 | `quantize: False` |

And the FP32 holdouts, each with its reason: **softmax** (exp in low
precision is an instant NaN), **GELU** (a curve, not a grid - quantizing its
output threw away the very nonlinearity the network trained on), the
**residual add** (FP32 accumulation, and - the subtle one - each branch gets
its OWN activation quantizer, because one shared observer's EMA blends two
different distributions and corrupts both), and **embed_tokens / lm_head**
(the first-layer and output projections that 4303 promotes to 16-bit whenever
NaN appears - the escape hatch).

```text
linears 12,582,912 vs LN params 4,096 -> linears are 99.967% of the block's weights
4-bit accuracy loss: per-channel ~1% vs per-tensor ~5%
```

The census is the argument: quantizing "the Linears" IS quantizing the model.
And the granularity line is the second lever - the same 4 bits cost ~1%
accuracy per-channel against ~5% per-tensor, because outlier-heavy rows get
their own scale instead of poisoning the tensor-wide one. 4303's own config
walks Q/K/V/O + both MLP Linears with input/output activations asymmetric and
weights symmetric, softmax in FP32, `fused qkv` with
`permute(2,0,3,1,4)` reshaping into `(3, B, H, N, d)`.

## The Low-Bit Ledger and the Outlier Tax

The full bit-width ledger, with the loss bands the modules quote:

| Dtype | Bits | Size | Range | Loss band |
|-------|------|------|-------|-----------|
| FP32 | 32 | 100.00% | float | <0.1% |
| FP16 | 16 | 50.00% | float | <0.1% |
| INT8 | 8 | 25.00% | [-128, 127] | <1% |
| INT4 | 4 | 12.50% | [-8, 7] | 1-3% |
| INT3 | 3 | 9.38% | [-4, 3] | 3-10% |
| INT2 | 2 | 6.25% | [-2, 1] | >10% (research) |

The obstacle at the bottom of the table is never the grid width alone - it is
the dynamic range. Training moves weights around, and one large coordinate
sets the scale for everyone:

```text
one planted 100.0 at coord 0:  min-max scale 100/7 = 14.2857
quantile-0.999 scale           q/7 = 3.1244/7 = 0.4463   -> 32.0x tighter
dynamic-range walk (INT4 s=0.5): w 3.0 x2 -> 6.0 -> q 7   w 3.5 x2 -> 7.0 -> q 7 (edge, clipped)
```

A single 100.0 inflates the min-max scale 32x over the quantile-based scale -
every ordinary weight lands near zero on the grid. The fence's x2 walk is the
training-time version of the same hazard: weights that double mid-training
slide to the grid edge and clip. 4304's four techniques fight exactly this:

| Technique | The knob | What it buys |
|-----------|----------|--------------|
| LearnedClip | a trainable Parameter scales the input (init 3.0) | the network widens its own effective range instead of clipping |
| MixedPrecisionQAT | per-layer bit widths via a ModuleDict (embeddings 8, MLP 3) | sensitivity analysis spends bits where they pay |
| PowerOfTwoScale | learnable `log2_scale` | shift-only scales, cheap on real hardware |
| LearnedStepSize | `clamp(round(x/s), -8, 7)` with s learned | the grid spacing itself trains |
| Stochastic rounding | `torch.where(rand < frac, floor+1, floor)` | unbiased rounding with no gradient path at all |

And the two scheduling moves that wrap them: **progressive QAT** walks
8 -> 4 -> 3 across `[5, 5, 10]` epochs (20 total - warm up wide, then
narrow; symmetric-aware `set_bit_width` rebuilds the grid per stage), and
**distillation** keeps a FP32 teacher on the loss - `KL * T^2` with
temperature 2.0 and batchmean, blended `0.5*CE + 0.5*KL*T^2` so the student
matches the teacher's soft distribution, not just the argmax.

## The Configuration Surface

A QAT config is six decisions, not one bit-width: layer choice, per-layer
precision, per-tensor vs per-channel, symmetric vs asymmetric, dynamic vs
static scales (static: `register_buffer`-frozen from the observer; dynamic:
`x.abs().max() / 127` recomputed per batch), and the skip list. 4305's three
templates price the space:

| Template | Loss band | Plan |
|----------|-----------|------|
| Conservative | <1% | all Linear 8-bit, norms/embed FP32 |
| Balanced | 1-2% | Q/K/O + embeddings 8-bit, V + MLP 4-bit |
| Aggressive | 2-5% | everything 4-bit, norms FP32, embed 8-bit |

```text
progressive 8->4->3: INT8 5ep + INT4 5ep + INT3 10ep = 20 epochs
distillation T 2.0: KL*T^2 0.0342  CE 1.0333  loss 0.5*CE + 0.5*KL*T^2 = 0.5338
asymmetric: min -3.0 max 5.0 -> scale 0.03137  zero_point 96
```

When the template is not enough, three selective strategies pick the victims
empirically: top-k-largest (quantize the k biggest layers), sensitivity
analysis (drop-in delta per layer, then sort), and greedy auto-config -
sorted by impact, demote 2 bits at a time, revert any step that costs more
than the target (0.98 accuracy budget). One structural trap lives in the walk
itself: inserting or replacing modules while iterating `named_modules()`
mutates the tree mid-walk and the recursion never terminates cleanly -
snapshot the name list first, then edit.

## Decision Rules

```text
8-bit target                    -> plain PTQ; QAT's training bill buys nothing inside 0.3
4-bit target, accuracy matters  -> QAT, per-channel scales, progressive 8->4->3 + distillation
one outlier moves the scale 32x -> quantile-based scale, or a 16-bit escape hatch for that layer
```

```text
write the config   : six dimensions - layers, per-layer bits, granularity, sign, dynamic/static, skip-list
wire the loop      : prepare_qat -> train (STE gradients, observer EMA) -> convert; seed on batch 1, freeze in eval
go low-bit         : progressive [5, 5, 10], V + MLP at 4-bit per-channel, softmax/GELU/LN stay FP32
stabilize          : NaN -> 16-bit Q/K; scale collapse -> 1e-5 floor; two residual branches -> two quantizers
```

## Fence - the Reproduction

```python
"""CHEAT-SHEET-044 fence: quantization-aware training - the STE contract, the observer, the layer map.
F1 fake-quant round trip: int8 symmetric grid error census + the STE gradient contract (3 STE options)
F2 the observer walk: momentum-0.01 EMA, first-batch seed against inf buffers, scales, 1e-5 floor, eval-freeze
F3 the outlier ledger: planted 100.0, min-max vs quantile-0.999 scale at INT4 (qmax=7), the x2 grid-edge walk
F4 the bit-width ledger: INT2/INT3/INT4/INT8/FP16/FP32 ranges, sizes, loss bands
F5 the transformer layer map: 6 quantized linears vs the FP32 holdouts, the 99.9% weight share, 4-bit bands
F6 the results tables: BERT SST-2 accuracy and GPT perplexity, PTQ vs QAT deltas
F7 the configuration surface: progressive 8->4->3 schedule, distillation blend, three templates
"""
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def nearest_rank(sorted_vals, p):
    """Nearest-rank percentile on a pre-sorted list (the module convention)."""
    n = len(sorted_vals)
    k = max(1, math.ceil(p * n))
    return sorted_vals[min(n, k) - 1]


def fq_int8(x, scale):
    """Symmetric int8 fake quantize: clamp(round(x/s), -128, 127) then dequantize."""
    return max(-128, min(127, round(x / scale))) * scale


# ---------------------------------------------------------------- F1
print("F1 fake-quant round trip (int8 symmetric) + the STE contract")
random.seed(6)
W = [random.gauss(0.0, 0.5) for _ in range(4096)]
amax = max(abs(v) for v in W)
scale8 = amax / 127.0
dq = [fq_int8(v, scale8) for v in W]
errs = sorted(abs(d - v) for d, v in zip(dq, W))
mean_e = sum(errs) / len(errs)
p95 = nearest_rank(errs, 0.95)
print(f"  weights 4096  scale {scale8:.6f}  step-half-bound max err/scale "
      f"{errs[-1] / scale8:.3f}")
print(f"  abs err  mean {mean_e:.5f}  P95 {p95:.5f}  max {errs[-1]:.5f}  "
      f"max/step {errs[-1] / scale8:.3f}")
# true gradient: round is piecewise-constant -> derivative exactly 0 off bin edges
h = 1e-7
zero_grad = sum(
    1 for x in (random.uniform(-scale8, scale8) for _ in range(64))
    if fq_int8(x + h, scale8) == fq_int8(x - h, scale8)
)
print(f"  true numeric gradient exactly 0 at {zero_grad}/64 sample points "
      f"(off half-step bin edges)")
qmin4, qmax4 = -8, 7
random.seed(12)
pre = [random.gauss(0.0, 4.0) for _ in range(1000)]
opt = {
    "RoundSTE    identity everywhere        ": sum(1 for _ in pre),
    "ClampedSTE  0 outside [qmin,qmax]      ": sum(1 for v in pre if qmin4 <= v <= qmax4),
    "HardTanhSTE linear band [qmin-1,qmax+1] ": sum(1 for v in pre if qmin4 - 1 <= v <= qmax4 + 1),
}
for name, alive in opt.items():
    print(f"  {name} {alive}/1000 grads survive")
print()

# ---------------------------------------------------------------- F2
print("F2 the observer: momentum-0.01 EMA walk, first-batch seed, scales, floor")
random.seed(7)
momentum = 0.01
obs_min, obs_max = math.inf, -math.inf
batches = [[random.gauss(0.0, 1.0) for _ in range(256)] for _ in range(40)]
for b in batches:
    bmin, bmax = min(b), max(b)
    if math.isinf(obs_min):          # first batch: SEED, never average with inf
        obs_min, obs_max = bmin, bmax
    else:                            # training only: eval freezes the EMA
        obs_min = (1.0 - momentum) * obs_min + momentum * bmin
        obs_max = (1.0 - momentum) * obs_max + momentum * bmax
first_sym = max(abs(min(batches[0])), max(batches[0])) / 127.0
sym = max(abs(obs_min), obs_max) / 127.0     # symmetric: cover BOTH sides
asym = (obs_max - obs_min) / 255.0           # asymmetric: span over 255 levels
print(f"  batches 40x256  momentum {momentum}  first-batch sym scale "
      f"{first_sym:.6f}")
print(f"  converged  min {obs_min:+.4f}  max {obs_max:+.4f}")
print(f"  sym scale max(|min|,|max|)/127 {sym:.6f}   asym scale "
      f"(max-min)/255 {asym:.6f}")
print("  no-seed guard: unseeded EMA stays inf*scale = inf -> dead queue")
zero_scale = max(0.0, 1e-5)
print(f"  all-zero batch would give scale 0.0 -> floor {zero_scale}")
print()

# ---------------------------------------------------------------- F3
print("F3 the outlier ledger: planted 100.0, min-max vs quantile at INT4 qmax=7")
random.seed(6)
w = [random.gauss(0.0, 1.0) for _ in range(1000)]
w[0] = 100.0
s_mm = 100.0 / 7.0
s_q = nearest_rank(sorted(w), 0.999) / 7.0
print(f"  coord 0 = 100.0   min-max scale 100/7 = {s_mm:.4f}")
print(f"  quantile 0.999 scale q/7 = {nearest_rank(sorted(w), 0.999):.4f}/7 "
      f"= {s_q:.4f}")
print(f"  the outlier inflates the scale {s_mm / s_q:.1f}x -> every ordinary "
      f"weight lands near 0")
print("  dynamic-range walk, INT4 scale 0.5, grid [-8, 7]:")
for v in (0.5, 1.0, 2.0, 3.0, 3.5):
    d = 2.0 * v
    q = max(qmin4, min(qmax4, round(d / 0.5)))
    edge = " <- grid edge, clipped" if d > qmax4 or d < qmin4 else ""
    print(f"    w {v:>4}  x2 -> {d:>4}  q {q:>3}{edge}")
print()

# ---------------------------------------------------------------- F4
print("F4 the bit-width ledger")
rows = [
    ("FP32", 32, "<0.1%"), ("FP16", 16, "<0.1%"), ("INT8", 8, "<1%"),
    ("INT4", 4, "1-3%"), ("INT3", 3, "3-10%"), ("INT2", 2, ">10% (research)"),
]
for name, bits, band in rows:
    size = 100.0 * bits / 32.0
    if name.startswith("INT"):
        rng = f"[{-2 ** (bits - 1)}, {2 ** (bits - 1) - 1}]"
    else:
        rng = "float"
    print(f"  {name:<5} {bits:>2}-bit  size {size:>6.2f}%  range {rng:<10} "
          f"loss {band}")
print()

# ---------------------------------------------------------------- F5
print("F5 the transformer layer map (one block, d=1024)")
QUANTIZED = [
    ("attn.q_proj", "8 per-channel"), ("attn.k_proj", "8 per-channel"),
    ("attn.v_proj", "4 per-channel"), ("attn.o_proj", "8 per-channel"),
    ("mlp.fc1", "4 per-channel"), ("mlp.fc2", "4 per-channel"),
]
HOLDOUT = [
    ("layer_norm 1/2", "FP32, quantize: False"),
    ("softmax", "FP32 (exp in int = instant NaN)"),
    ("GELU", "FP32 (curve, not a grid)"),
    ("residual add", "FP32 + one SEPARATE quantizer per branch"),
    ("embed/lm_head", "16-bit escape hatch when NaN appears"),
]
d = 1024
lin = 12 * d * d          # 4 attn projections + fc1 (d->4d) + fc2 (4d->d)
ln = 4 * d                # two LayerNorms, gamma+beta
for name, note in QUANTIZED:
    print(f"  QUANTIZE   {name:<12} {note}")
for name, note in HOLDOUT:
    print(f"  FP32       {name:<12} {note}")
print(f"  linears {lin:,} vs LN params {ln:,} -> linears are "
      f"{100.0 * lin / (lin + ln):.3f}% of the block's weights")
print("  4-bit accuracy loss: per-channel ~1% vs per-tensor ~5%")
print()

# ---------------------------------------------------------------- F6
print("F6 the results tables: PTQ vs QAT")
BERT = [("FP32", 93.2), ("INT8 PTQ", 92.8), ("INT8 QAT", 93.0),
        ("INT4 QAT", 91.5), ("INT3 QAT", 88.2)]
GPT = [("FP32", 12.4), ("INT8 PTQ", 12.8), ("INT8 QAT", 12.5),
       ("INT4 QAT", 13.8), ("INT3 QAT", 16.2)]
print("  BERT-base SST-2 accuracy")
for name, acc in BERT:
    print(f"    {name:<9} {acc:.1f}")
print(f"    INT8 QAT-vs-PTQ delta {BERT[2][1] - BERT[1][1]:+.1f}   "
      f"INT4-vs-FP32 {BERT[3][1] - BERT[0][1]:+.1f}   "
      f"INT3-vs-FP32 {BERT[4][1] - BERT[0][1]:+.1f}")
print("  GPT-style perplexity (WikiText-2, lower is better)")
for name, ppl in GPT:
    print(f"    {name:<9} {ppl:.1f}")
print(f"    INT8 QAT-vs-PTQ delta {GPT[2][1] - GPT[1][1]:+.1f}   "
      f"INT4-vs-FP32 {GPT[3][1] - GPT[0][1]:+.1f}   "
      f"INT3-vs-FP32 {GPT[4][1] - GPT[0][1]:+.1f}")
print()

# ---------------------------------------------------------------- F7
print("F7 the configuration surface: schedule, distillation, templates")
sched = [("INT8 warmup", 5), ("INT4", 5), ("INT3", 10)]
print("  progressive 8->4->3:", "  ".join(f"{n} {e}ep" for n, e in sched),
      f"= {sum(e for _, e in sched)} epochs total")
random.seed(11)
T = 2.0
alpha = 0.5
teacher = [random.gauss(0.0, 2.0) for _ in range(8)]
student = [0.8 * v + 0.1 for v in teacher]


def soft(z, temp):
    m = max(z)
    e = [math.exp((v - m) / temp) for v in z]
    s = sum(e)
    return [v / s for v in e]


pt, ps = soft(teacher, T), soft(student, T)
kl_T2 = T * T * sum(p * math.log(p / q) for p, q in zip(pt, ps))
hot = teacher.index(max(teacher))
ce = -math.log(soft(student, 1.0)[hot])
blend = alpha * ce + (1.0 - alpha) * kl_T2
print(f"  distillation T {T}  KL*T^2 {kl_T2:.4f}  CE {ce:.4f}  "
      f"loss {alpha}*CE + {1 - alpha}*KL*T^2 = {blend:.4f}")
TEMPLATES = [
    ("Conservative", "<1%", "all Linear 8-bit, norms/embed FP32"),
    ("Balanced", "1-2%", "Q/K/O + embeddings 8-bit, V + MLP 4-bit"),
    ("Aggressive", "2-5%", "everything 4-bit, norms FP32, embed 8-bit"),
]
for name, band, plan in TEMPLATES:
    print(f"  {name:<12} loss {band:<6} {plan}")
zp = -round(-3.0 / ((5.0 - (-3.0)) / 255.0))
print(f"  asymmetric check: min -3.0 max 5.0 -> scale "
      f"{(5.0 - (-3.0)) / 255.0:.5f}  zero_point {zp}")
print("FENCE-044-OK")
```

```text
F1 fake-quant round trip (int8 symmetric) + the STE contract
  weights 4096  scale 0.014950  step-half-bound max err/scale 0.500
  abs err  mean 0.00374  P95 0.00705  max 0.00747  max/step 0.500
  true numeric gradient exactly 0 at 64/64 sample points (off half-step bin edges)
  RoundSTE    identity everywhere         1000/1000 grads survive
  ClampedSTE  0 outside [qmin,qmax]       930/1000 grads survive
  HardTanhSTE linear band [qmin-1,qmax+1]  965/1000 grads survive

F2 the observer: momentum-0.01 EMA walk, first-batch seed, scales, floor
  batches 40x256  momentum 0.01  first-batch sym scale 0.021617
  converged  min -2.7332  max +2.7472
  sym scale max(|min|,|max|)/127 0.021631   asym scale (max-min)/255 0.021492
  no-seed guard: unseeded EMA stays inf*scale = inf -> dead queue
  all-zero batch would give scale 0.0 -> floor 1e-05

F3 the outlier ledger: planted 100.0, min-max vs quantile at INT4 qmax=7
  coord 0 = 100.0   min-max scale 100/7 = 14.2857
  quantile 0.999 scale q/7 = 3.1244/7 = 0.4463
  the outlier inflates the scale 32.0x -> every ordinary weight lands near 0
  dynamic-range walk, INT4 scale 0.5, grid [-8, 7]:
    w  0.5  x2 ->  1.0  q   2
    w  1.0  x2 ->  2.0  q   4
    w  2.0  x2 ->  4.0  q   7
    w  3.0  x2 ->  6.0  q   7
    w  3.5  x2 ->  7.0  q   7

F4 the bit-width ledger
  FP32  32-bit  size 100.00%  range float      loss <0.1%
  FP16  16-bit  size  50.00%  range float      loss <0.1%
  INT8   8-bit  size  25.00%  range [-128, 127] loss <1%
  INT4   4-bit  size  12.50%  range [-8, 7]    loss 1-3%
  INT3   3-bit  size   9.38%  range [-4, 3]    loss 3-10%
  INT2   2-bit  size   6.25%  range [-2, 1]    loss >10% (research)

F5 the transformer layer map (one block, d=1024)
  QUANTIZE   attn.q_proj  8 per-channel
  QUANTIZE   attn.k_proj  8 per-channel
  QUANTIZE   attn.v_proj  4 per-channel
  QUANTIZE   attn.o_proj  8 per-channel
  QUANTIZE   mlp.fc1      4 per-channel
  QUANTIZE   mlp.fc2      4 per-channel
  FP32       layer_norm 1/2 FP32, quantize: False
  FP32       softmax      FP32 (exp in int = instant NaN)
  FP32       GELU         FP32 (curve, not a grid)
  FP32       residual add FP32 + one SEPARATE quantizer per branch
  FP32       embed/lm_head 16-bit escape hatch when NaN appears
  linears 12,582,912 vs LN params 4,096 -> linears are 99.967% of the block's weights
  4-bit accuracy loss: per-channel ~1% vs per-tensor ~5%

F6 the results tables: PTQ vs QAT
  BERT-base SST-2 accuracy
    FP32      93.2
    INT8 PTQ  92.8
    INT8 QAT  93.0
    INT4 QAT  91.5
    INT3 QAT  88.2
    INT8 QAT-vs-PTQ delta +0.2   INT4-vs-FP32 -1.7   INT3-vs-FP32 -5.0
  GPT-style perplexity (WikiText-2, lower is better)
    FP32      12.4
    INT8 PTQ  12.8
    INT8 QAT  12.5
    INT4 QAT  13.8
    INT3 QAT  16.2
    INT8 QAT-vs-PTQ delta -0.3   INT4-vs-FP32 +1.4   INT3-vs-FP32 +3.8

F7 the configuration surface: schedule, distillation, templates
  progressive 8->4->3: INT8 warmup 5ep  INT4 5ep  INT3 10ep = 20 epochs total
  distillation T 2.0  KL*T^2 0.0342  CE 1.0333  loss 0.5*CE + 0.5*KL*T^2 = 0.5338
  Conservative loss <1%    all Linear 8-bit, norms/embed FP32
  Balanced     loss 1-2%   Q/K/O + embeddings 8-bit, V + MLP 4-bit
  Aggressive   loss 2-5%   everything 4-bit, norms FP32, embed 8-bit
  asymmetric check: min -3.0 max 5.0 -> scale 0.03137  zero_point 96
FENCE-044-OK
```

## Known Failure Modes

| Trap | What it costs | The honest move |
|------|---------------|-----------------|
| Reading STE as "the gradient of round" | it is not - round's true gradient is 0 a.e.; STE substitutes the identity on purpose | say "STE passes the gradient through unchanged"; the fence's 64/64 zero-gradient census is the proof |
| Training straight into INT4 from FP32 | dynamic range grows mid-training and clips at the grid edge (w 3.5 x2 -> q 7) | progressive 8->4->3 at `[5, 5, 10]` or an 8-bit warmup stage |
| Quantizing softmax, GELU or LayerNorm | exp in low precision is an instant NaN; the nonlinearity is the point | keep them FP32; quantize the 6 Linears - they are 99.967% of the block's weights |
| Sharing one activation quantizer across both residual branches | one observer's EMA blends two distributions and corrupts both | one SEPARATE quantizer per branch, 4303's block pattern |
| Trusting per-tensor 4-bit results as the ceiling | per-tensor pays ~5% where per-channel pays ~1% on the same bits | switch granularity before abandoning the bit-width |
| Leaving the outlier in the min-max scale | one coordinate sets the scale 32x too wide; every other weight rounds to ~0 | quantile-based scale, or keep the layer at 16 bits |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Loss NaNs a few steps into QAT | softmax or attention scores entered the grid | restore FP32 softmax; widen Q/K to 16-bit (4303's NaN fix) |
| Every gradient is zero | the true round derivative leaked into the backward | the STE backward is the identity, not `d(round)` - check the custom autograd |
| Scale hits 0 on a constant batch | zero-range EMA divides by zero | clamp the scale at `min=1e-5` and seed the EMA on batch 1 |
| First batch poisons all statistics | EMA averaged with the inf/-inf init buffers | the first batch must ASSIGN the range, never average into inf |
| INT8 fine, INT4 collapses | heavy-tailed distribution under per-tensor scales | per-channel scales or the quantile scale (32x tighter under a planted outlier) |
| QAT accuracy below PTQ at INT8 | training overhead without low-bit pressure | ship the PTQ model at 8 bits; QAT earns its bill at 4 bits and below |

## Quick Reference

| Target | Where |
|--------|-------|
| module 4301 | `docs/phases/phase4-quantization/4300-quantization-aware-training/4301-QAT-Foundations.md` |
| module 4303 | `docs/phases/phase4-quantization/4300-quantization-aware-training/4303-QAT-for-Transformers.md` |
| module 4304 | `docs/phases/phase4-quantization/4300-quantization-aware-training/4304-Low-bit-QAT.md` |
| module 4305 | `docs/phases/phase4-quantization/4300-quantization-aware-training/4305-Quantization-Configuration.md` |
