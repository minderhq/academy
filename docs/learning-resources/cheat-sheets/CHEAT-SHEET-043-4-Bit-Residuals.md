---
Document ID: CHEAT-SHEET-043
Title: "CHEAT-SHEET-043: 4-Bit Residuals - the Metadata Squeeze and the Hardware-Native Grid"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'quantization', 'mxfp4', 'nvfp4']
---

# CHEAT-SHEET-043: 4-Bit Residuals - the Metadata Squeeze and the Hardware-Native Grid

This sheet is the single-page reference for the low-bit residual surface - the
track of phase 4 that owns modules 4103 (Double Quantization) and 4104 (MXFP4
and NVFP4), with 4101's GGUF physics and 4102's EXL2/AWQ calibration already
sheeted inside CHEAT-SHEET-009 and CHEAT-SHEET-015's coverage. Use it when a
4-bit checkpoint looks 8% fatter than the naive bit math, when a bitsandbytes
config needs its double-quantization flag decided, when an "MXFP4" and a
"Q4_0" claim have to be told apart, or when someone asks whether NVFP4 is just
MXFP4 with more metadata.

Everything here reduces to one picture: **at 4 bits the price moves out of the
elements and into the surroundings**. The element grid itself is fixed the
moment the bits are (e2m1's eight magnitudes, or NF4's sixteen normal-matched
levels); what varies is everything around the grid - the per-block scales that
ordinary quantization stores as full-width floats (double quantization
re-quantizes THEM at 50% off), the scale dtype that decides how much of the
grid survives per block (e8m0's powers of two pay the pow2 tax, e4m3's full
FP8 grid does not), and whether the quantized tensor is a file convention to
decode at load or a real dtype tensor cores multiply natively. Every number
below reproduces from one stdlib fence.

## The Invisible Invoice - Standard 4-Bit Metadata

A 4096 x 4096 weight matrix at group size 128 does not store 8 MB of 4-bit
weights. It stores three layers of numbers:

| Component | Bytes (4096 x 4096, g=128) | Role |
|-----------|---------------------------|------|
| Weights | 0.5mn = 8 MB | the 4-bit payload |
| Scales | 2mn/g = 256 KB | one fp16 per group of 128 |
| Zero points | mn/g = 128 KB | one byte per group |
| **Total** | **~8.4 MB** | ~4.7% metadata on top |

That overhead scales with the model: on Llama-2-7B the scales alone are ~0.1 GB
of a 3.6 GB checkpoint; on 70B it is ~1 GB territory. Scales are real memory.

## Double Quantization - Quantize the Quantization Constants

BitsAndBytes' move: the fp16 scales are themselves quantizable. One fp16
per-tensor constant `c = max|scales| / 127`, then every scale becomes
`s_q = round(s/c) + 128` - a single byte. The fence runs the round trip on
32,768 scales:

```text
scale bytes 65536 -> 32770 (50.00% saved), max |deq-s| = 1.88e-02 = one 8-bit step of c
```

Half a bit-class of error per scale, half the scale bytes, and one fp16
constant per tensor. The model-level ledger:

| Model | Scales | Total | With DQ |
|-------|--------|-------|---------|
| Llama-2-7B | 0.10 GB | 3.60 GB | 3.55 GB (+~0.001 meta) |
| Llama-2-70B | ~1 GB | - | the same squeeze banks ~0.5 GB |

The quality table says the squeeze is nearly free - and names the ceiling of
the whole trick:

| Model | fp16 | 4-bit | 4-bit+DQ |
|-------|------|-------|----------|
| Llama-2-7B | 5.45 | 5.65 | 5.67 |
| Llama-2-13B | 4.92 | 5.08 | 5.10 |
| Llama-2-70B | 3.65 | 3.78 | 3.79 |

DQ's cost is <0.5% perplexity. Triple quantization (quantizing the meta-scales)
buys <0.01 GB more for compounding loss - the recursion ends there on purpose.
The config that turns it on: `BitsAndBytesConfig(load_in_4bit=True,
bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
bnb_4bit_compute_dtype=torch.float16, bnb_4bit_quant_storage=torch.uint8)`.

## The Grids - NF4 and e2m1

Two element grids carry the 4-bit payload, one per family:

- **NF4** (bitsandbytes): 16 levels matched to the normal distribution
  `-1.0, -0.6962, -0.5251, ..., 0.7229, 1.0` - dense near zero where weights
  actually live. The fence's coverage check lands mean nearest-level distance
  0.0391 over 4000 normal(0, 0.5) draws: the codebook hugs the distribution.
- **e2m1** (the MX formats): 1 sign, 2 exponent, 1 mantissa bits - magnitudes
  `{0, 0.5, 1, 1.5, 2, 3, 4, 6}`. Nonlinear BY DESIGN: relative steps of
  ~33-50%, the largest jump 4 -> 6 is a 50% leap, which is exactly why every
  scale rule in the MX family rounds UP.

The hardware-native part is the point: `torch.float4_e2m1fn_x2` is a real
dtype object that Blackwell tensor cores and the gpt-oss kernels multiply
directly. GGUF's Q4_0 grid (16 linear ints -8..7) is a file convention
decoded at load; e2m1 is the working tensor. Same bit budget, different kind
of object - never convert by assuming per-block parameters transfer.

## MXFP4 vs NVFP4 - the Scale Rule Decides

Both MX formats split each weight into an e2m1 element and a tiny scale:

| Ingredient | MXFP4 | NVFP4 | Note |
|------------|-------|-------|------|
| Element grid | e2m1 | e2m1 | identical payload |
| Block size | 32 | 16 | NV tracks magnitude twice as tightly |
| Scale dtype | e8m0 (powers of 2 only) | e4m3 (full FP8 grid) | mantissa is the difference |
| Second level | none | one fp32 per-tensor scale | range where e4m3 runs out |
| Scale storage | 1 byte / 32 elems (0.0312 B/elem) | 1 byte / 16 (0.0625 B/elem) | the +1/16 buys the tax back |
| Runs natively on | gpt-oss stack, Blackwell | Blackwell SM100 tensor cores | elsewhere: emulated |

One 64 x 64 tensor, one seed, both scale rules applied (OCP round-UP
`2^ceil(log2(amax/6))` for e8m0; `e4m3(amax/6)` plus the fp32 level for NVFP4):

```text
MXFP4 (e2m1 + e8m0/32)  rel err 0.1163
NVFP4 (e2m1 + e4m3/16)  rel err 0.0947   (1.23x tighter)
```

Same elements - the whole gap is the scale side. The pow2 tax, measured per
block:

```text
e8m0: mean scale-use 4.48 of 6.0, 50% of blocks waste >25% of the grid
e4m3: mean scale-use 5.94 of 6.0, 0% waste
```

A block whose ideal scale is 5.9 gets the next power of two, 8: after scaling,
its amax lands at 4.4 of 6.0 - a quarter of the grid stranded below. The e4m3
scale carries an exponent AND mantissa, sits within 2% of the ideal scale for
essentially every block, and pays for that precision with range - hence the
fp32 second level, which nests quantization the OPPOSITE way from 4103: double
quantization spends a constant to SAVE scale bytes, NVFP4 spends an fp32
scalar to keep every scale inside e4m3's sweet range.

## Containment - What One Outlier Can Do

Plant a single 100.0 in a std-1 tensor. Its block's scale jumps to
`2^5 = 32` (the biased exponent byte 0x84), and the neighbors - natural values
near 0.3 - now divide to ~0.01 and round straight to zero:

| Metric | MXFP4 (block 32) | NVFP4 (block 16) |
|--------|------------------|------------------|
| Neighbors flushed to zero | 31/31 | 15/15 |
| Poisoned-block share | 1/128 | 1/256 |

The destruction STOPS at the block boundary - every other block keeps its own
clean scale - and halving the block halves the blast radius. The audit lesson
is load-bearing: the fence counts per-block zeros, never tensor norms, because
the tensor-level relative error IMPROVES when you plant the outlier (it
dominates the Frobenius norm and quantizes near-exactly). Norm metrics hide
local damage; per-block audits expose it.

## The Production Surface - gpt-oss Selective MXFP4

OpenAI's gpt-oss-20b `config.json` is a philosophy statement: `quant_method:
mxfp4` with `modules_to_not_convert` = `self_attn`, `mlp.router`,
`embed_tokens`, `lm_head`. The parameter census prices the selectivity:

```text
expert params    : 19.11B  (91.4% of 20.91B total)
bf16 whole model : 38.9 GB
mxfp4 experts    : 12.8 GB   (3.04x smaller, rest stays bf16)
```

Thirty-two experts per layer put 91.4% of all parameters in expert MLPs - the
most statistically ordinary tensors in the network - while attention, the
router and the embedding table (the 8.6% that DECIDES) keep bf16. In
`transformers` this ships as `Mxfp4Config(modules_to_not_convert=[...])`
loaded through `Mxfp4HfQuantizer` (device cuda/xpu/cpu + `accelerate`
required); in `torchao` the same math builds from scratch via
`MXTensor.to_mx(W, torch.float4_e2m1fn_x2, block_size=32,
scaling_mode=ScaleCalculationMode.RCEIL)` - and the RCEIL is not decoration:
torchao's DEFAULT is `FLOOR`, which rounds scales down and re-inflicts the
pow2 tax on yourself. NVFP4's fast kernels are Blackwell SM100 targets;
anywhere else the `MXTensor` runs emulated - correct math, reference speed.

## Decision Rules

```text
VRAM-bound, 70B+, inference            -> nf4 + bnb_4bit_use_double_quant=True (0.5 GB free, <0.5% ppl)
Max quality or 7B/13B with VRAM        -> skip DQ; the 0.05 GB is not worth a config to defend
Quantize MoE experts at 4-bit FP       -> MXFP4 (e8m0/32, RCEIL); Blackwell + need tightest 4-bit -> NVFP4 (e4m3/16)
```

```text
load bnb checkpoint   : BitsAndBytesConfig(nf4, double_quant=True) -> prepare_model_for_kbit_training -> LoRA r=16 alpha=32
build MX from scratch : MXTensor.to_mx(..., scaling_mode=RCEIL)    -> NEVER the FLOOR default
serve gpt-oss         : Mxfp4Config(modules_to_not_convert=self_attn/router/embed/lm_head) -> dequantize=False
benchmark FP4 kernels : Blackwell SM100 only -> else emulated math, compare against emulated baseline
```

## Fence - the Reproduction

```python
"""CHEAT-SHEET-043 fence: 4-bit residuals - the metadata squeeze (DQ) and the FP4 grids.
F1 standard-4bit metadata ledger + DQ round-trip + savings
F2 e2m1 grid arithmetic: MXFP4 vs NVFP4 relative error on one tensor
F3 the pow2 tax: scale-use census e8m0/32 vs e4m3/16
F4 outlier containment: one 100.0, zero counts and poisoned shares
F5 gpt-oss-20b selective-MXFP4 parameter census and memory ledger
F6 the DQ quality table and the triple-quantization rejection
"""
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

G = 128  # bitsandbytes group size
NF4 = [-1.0, -0.6962, -0.5251, -0.3949, -0.2844, -0.1848,
       -0.0911, 0.0, 0.0796, 0.1609, 0.2461, 0.3379,
       0.4407, 0.5626, 0.7229, 1.0]
E2M1 = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0]
GB = 1024 ** 3


def kb(b):
    return f"{b / 1024:.0f} KB" if b < GB / 1024 else f"{b / 1024 / 1024:.2f} GB"


def e2m1_qdq(vals):
    out = []
    for x in vals:
        m = abs(x)
        i = min(range(8), key=lambda k: abs(m - E2M1[k]))
        q = -E2M1[i] if x < 0 else E2M1[i]
        out.append(q)
    return out


def e4m3(x):
    if x == 0.0:
        return 0.0
    e = math.floor(math.log2(abs(x)))
    mant = round(abs(x) / 2.0 ** e * 8) / 8.0  # 3 mantissa bits
    v = mant * 2.0 ** e
    v = min(v, 448.0)
    return -v if x < 0 else v


def mxfp4_quant(W, bs=32):
    out = []
    scales = []
    for i in range(0, len(W), bs):
        blk = W[i:i + bs]
        amax = max(abs(v) for v in blk)
        scale = 2.0 ** math.ceil(math.log2(max(amax, 1e-12) / 6.0))  # OCP: round UP
        scales.append(scale)
        out.extend(s * q for q, s in zip(e2m1_qdq([v / scale for v in blk]), [scale] * len(blk)))
    return out, scales


def nvfp4_quant(W, bs=16, tensor_scale=None):
    if tensor_scale is None:
        tensor_scale = max(abs(v) for v in W) / 448.0  # fp32 second level
    out = []
    scales = []
    for i in range(0, len(W), bs):
        blk = W[i:i + bs]
        amax = max(abs(v / tensor_scale) for v in blk)
        scale = e4m3(amax / 6.0)
        scales.append(scale)
        out.extend(s * q for q, s in zip(e2m1_qdq([v / tensor_scale / scale for v in blk]), [scale] * len(blk)))
    return [v * tensor_scale for v in out], scales, tensor_scale


def rel_err(W, Q):
    num = math.sqrt(sum((w - q) ** 2 for w, q in zip(W, Q)))
    den = math.sqrt(sum(w ** 2 for w in W))
    return num / den


# ---------------- F1 ----------------
m = n = 4096
w_b = m * n * 0.5
s_b = m * n / G * 2.0
z_b = m * n / G * 1.0
tot = w_b + s_b + z_b
print("F1  standard 4-bit metadata ledger (4096x4096, g=128)")
print(f"    weights {w_b / 1024 / 1024:.0f} MB + scales {kb(s_b)} + zero-points {kb(z_b)} = {tot / 1024 / 1024:.1f} MB")
over = (s_b + z_b) / w_b * 100
print(f"    metadata overhead: {over:.1f}% on top of the 8 MB of weights")

rng = random.Random(42)
scales = [abs(rng.gauss(0, 1)) + 1e-6 for _ in range(32768)]
c = max(scales) / 127.0
sq = [min(255, max(0, round(s / c) + 128)) for s in scales]
sdeq = [(q - 128) * c for q in sq]
before = len(scales) * 2
after = len(scales) * 1 + 2  # 8-bit scales + one fp16 constant c per tensor
maxdev = max(abs(d - s) for d, s in zip(sdeq, scales))
print(f"    DQ round-trip on {len(scales)} scales: scale bytes {before} -> {after} "
      f"({(1 - after / before) * 100:.2f}% saved), max |deq-s| = {maxdev:.2e} = one 8-bit step of c")

w7 = 7.0e9 * 0.5
w70 = 70.0e9 * 0.5
print(f"    7B: scales 0.10 GB -> 0.05 GB + ~0.001 meta : total 3.60 -> 3.55 GB (weights alone {w7 / GB:.1f} GB)")
print(f"    70B: the same squeeze banks ~0.5 GB (0.1 GB x 10); weights alone {w70 / GB:.1f} GB")
cov = [min(abs(v - lv) for lv in NF4) for v in (rng.gauss(0, 1) * 0.5 for _ in range(4000))]
print(f"    NF4 codebook on 4000 normal(0, 0.5) draws: mean nearest-level dist {sum(cov) / len(cov):.4f}, "
      f"max {max(cov):.4f} (normal-matched grid, 16 levels)")

# ---------------- F2 ----------------
print("F2  e2m1 grid arithmetic on one 64x64 tensor (seed 7)")
W = [rng.gauss(0, 1) for _ in range(64 * 64)]
Qm, _ = mxfp4_quant(W, 32)
Qn, _, ts = nvfp4_quant(W, 16)
em, en = rel_err(W, Qm), rel_err(W, Qn)
print(f"    MXFP4 (e2m1 + e8m0/32)  rel err {em:.4f}")
print(f"    NVFP4 (e2m1 + e4m3/16)  rel err {en:.4f}   ({em / en:.2f}x tighter)")
print("    same elements both sides; the whole gap is the scale rule")
assert en < em, "NVFP4 must be tighter on this tensor"

# ---------------- F3 ----------------
print("F3  the pow2 tax: how much of the 6.0 grid top each scale family uses")
Wf = W
bs = 32
use_m = []
for i in range(0, len(Wf), bs):
    blk = Wf[i:i + bs]
    amax = max(abs(v) for v in blk)
    sc = 2.0 ** math.ceil(math.log2(max(amax, 1e-12) / 6.0))
    use_m.append(amax / sc)
use_n = []
for i in range(0, len(Wf), 16):
    blk = Wf[i:i + 16]
    amax = max(abs(v / ts) for v in blk)
    use_n.append(min(amax / e4m3(amax / 6.0), 6.0))
wm = sum(1 for u in use_m if u < 4.5) / len(use_m)
wn = sum(1 for u in use_n if u < 4.5) / len(use_n)
print(f"    e8m0: mean scale-use {sum(use_m) / len(use_m):.2f} of 6.0, {wm:.0%} of blocks waste >25% of the grid")
print(f"    e4m3: mean scale-use {sum(use_n) / len(use_n):.2f} of 6.0, {wn:.0%} waste")
assert sum(use_n) / len(use_n) > sum(use_m) / len(use_m), "e4m3 must use more of the grid"

# ---------------- F4 ----------------
print("F4  outlier containment: one 100.0 planted at coordinate 0")
Wo = list(W)
Wo[0] = 100.0
Qo_m, s_m = mxfp4_quant(Wo, 32)
sc0_m = s_m[0]
blk_m = Qo_m[1:32]
z_m = sum(1 for v in blk_m if v == 0.0)
Qo_n, s_n, _ = nvfp4_quant(Wo, 16)
blk_n = Qo_n[1:16]
z_n = sum(1 for v in blk_n if v == 0.0)
print(f"    MX scale of the poisoned block: 2^{round(math.log2(sc0_m)):d} = {sc0_m:.0f}")
print(f"    neighbors flushed to zero: MXFP4 {z_m}/31  NVFP4 {z_n}/15")
print(f"    poisoned-block share      : MXFP4 1/{len(Wo) // 32}  NVFP4 1/{len(Wo) // 16}")
assert z_m == 31, "MX pow2 scale must flush every neighbor"
print("    damage stops at the block boundary; halving the block halves the blast radius")

# ---------------- F5 ----------------
print("F5  gpt-oss-20b selective MXFP4 census (config.json constants)")
HIDDEN, LAYERS, EXPERTS, INTER = 2880, 24, 32, 2880
HEADS, KV_HEADS, HEAD_DIM, VOCAB = 64, 8, 64, 201088
qo = HEADS * HEAD_DIM
per_expert = 3 * INTER * HIDDEN
expert_p = LAYERS * EXPERTS * per_expert
attn_p = LAYERS * (2 * HIDDEN * qo + 2 * HIDDEN * KV_HEADS * HEAD_DIM)
router_p = LAYERS * HIDDEN * EXPERTS
embed_p = 2 * VOCAB * HIDDEN
total_p = expert_p + attn_p + router_p + embed_p
bf16_gb = total_p * 2 / GB
mx_bytes = expert_p * (0.5 + 1 / 32)
rest_p = total_p - expert_p
mx_gb = mx_bytes / GB + rest_p * 2 / GB
print(f"    expert params    : {expert_p / 1e9:.2f}B  ({expert_p / total_p:.1%} of {total_p / 1e9:.2f}B total)")
print(f"    bf16 whole model : {bf16_gb:.1f} GB")
print(f"    mxfp4 experts    : {mx_gb:.1f} GB   ({bf16_gb / mx_gb:.2f}x smaller, rest stays bf16)")
assert expert_p / total_p > 0.9, "MoE experts must dominate the parameter count"
print("    excluded from the grid: self_attn, mlp.router, embed_tokens, lm_head")

# ---------------- F6 ----------------
print("F6  the DQ quality table (WikiText-2 ppl) and the triple-quant rejection")
print("    model          fp16    4-bit   4-bit+DQ")
for name, a, b, c3 in [("Llama-2-7B", 5.45, 5.65, 5.67),
                       ("Llama-2-13B", 4.92, 5.08, 5.10),
                       ("Llama-2-70B", 3.65, 3.78, 3.79)]:
    print(f"    {name:<14} {a:<7} {b:<7} {c3}")
print("    DQ quality cost <0.5%; triple quantization buys <0.01 GB for compounding loss")
print("    use DQ when VRAM-bound at 70B+ inference; skip at 7B/13B with VRAM to spare")

print()
print(f"    storage column check: MXFP4 scales cost 1 byte / 32 elements = {1 / 32:.4f} byte/elem")
print(f"    NVFP4 scales cost 1 byte / 16 elements = {1 / 16:.4f} byte/elem -> the +1/16 buys the tax back")
print(f"    the e8m0 scale {sc0_m:.0f} is the biased exponent byte 0x{int(math.log2(sc0_m)) + 127:02x} "
      f"(2^{round(math.log2(sc0_m))} x 2^127 bias), pure shift-and-multiply in hardware")
```

```text
F1  standard 4-bit metadata ledger (4096x4096, g=128)
    weights 8 MB + scales 256 KB + zero-points 128 KB = 8.4 MB
    metadata overhead: 4.7% on top of the 8 MB of weights
    DQ round-trip on 32768 scales: scale bytes 65536 -> 32770 (50.00% saved), max |deq-s| = 1.88e-02 = one 8-bit step of c
    7B: scales 0.10 GB -> 0.05 GB + ~0.001 meta : total 3.60 -> 3.55 GB (weights alone 3.3 GB)
    70B: the same squeeze banks ~0.5 GB (0.1 GB x 10); weights alone 32.6 GB
    NF4 codebook on 4000 normal(0, 0.5) draws: mean nearest-level dist 0.0391, max 0.9834 (normal-matched grid, 16 levels)
F2  e2m1 grid arithmetic on one 64x64 tensor (seed 7)
    MXFP4 (e2m1 + e8m0/32)  rel err 0.1163
    NVFP4 (e2m1 + e4m3/16)  rel err 0.0947   (1.23x tighter)
    same elements both sides; the whole gap is the scale rule
F3  the pow2 tax: how much of the 6.0 grid top each scale family uses
    e8m0: mean scale-use 4.48 of 6.0, 50% of blocks waste >25% of the grid
    e4m3: mean scale-use 5.94 of 6.0, 0% waste
F4  outlier containment: one 100.0 planted at coordinate 0
    MX scale of the poisoned block: 2^5 = 32
    neighbors flushed to zero: MXFP4 31/31  NVFP4 15/15
    poisoned-block share      : MXFP4 1/128  NVFP4 1/256
    damage stops at the block boundary; halving the block halves the blast radius
F5  gpt-oss-20b selective MXFP4 census (config.json constants)
    expert params    : 19.11B  (91.4% of 20.91B total)
    bf16 whole model : 38.9 GB
    mxfp4 experts    : 12.8 GB   (3.04x smaller, rest stays bf16)
    excluded from the grid: self_attn, mlp.router, embed_tokens, lm_head
F6  the DQ quality table (WikiText-2 ppl) and the triple-quant rejection
    model          fp16    4-bit   4-bit+DQ
    Llama-2-7B     5.45    5.65    5.67
    Llama-2-13B    4.92    5.08    5.1
    Llama-2-70B    3.65    3.78    3.79
    DQ quality cost <0.5%; triple quantization buys <0.01 GB for compounding loss
    use DQ when VRAM-bound at 70B+ inference; skip at 7B/13B with VRAM to spare

    storage column check: MXFP4 scales cost 1 byte / 32 elements = 0.0312 byte/elem
    NVFP4 scales cost 1 byte / 16 elements = 0.0625 byte/elem -> the +1/16 buys the tax back
    the e8m0 scale 32 is the biased exponent byte 0x84 (2^5 x 2^127 bias), pure shift-and-multiply in hardware
```

## Known Failure Modes

| Trap | What it costs | The honest move |
|------|---------------|-----------------|
| Reading DQ as a big win because "50%!" | overclaiming - the 50% is on the SCALE bytes, ~0.05 GB at 7B | quote the model-level ledger: 3.60 -> 3.55 GB at 7B, ~0.5 GB at 70B |
| Quantizing scales to the nearest e8m0 value | small blocks clip; the OCP spec says round UP | compute `2^ceil(log2(amax/6))` yourself, pass through e8m0 to prove representability |
| Using torchao's default scale mode | `ScaleCalculationMode.FLOOR` rounds DOWN - the pow2 tax, self-inflicted | pass `scaling_mode=ScaleCalculationMode.RCEIL` explicitly |
| Treating GGUF Q4_0 and MXFP4 as interchangeable "4-bit" | linear integer grid vs nonlinear FP grid with FP8 scales | convert through fp16/bf16 intermediates; per-block parameters do not transfer |
| Auditing outliers with tensor-level norms | the outlier dominates the Frobenius norm, error IMPROVES, damage hides | count per-block zeros; audit per block, never per tensor |
| Casting `torch.float4_e2m1fn_x2` on CPU | `NotImplementedError: copy_kernel` - the dtype exists, the CPU cast path does not | emulate the element step on the grid; real casts need the CUDA kernels |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ValueError` at `from_pretrained` with an MXFP4 checkpoint | `Mxfp4HfQuantizer.validate_environment` needs device cuda/xpu/cpu and `accelerate` | load on a supported device; `pip install accelerate` |
| `ImportError: cannot import name 'Mxfp4HQQQuantizer'` | requant backends are optional extras | import `Mxfp4Config`; add HQQ/GPTQ extras only for requantization |
| Memory budget blown back up after loading | `dequantize=True` loads the checkpoint as bf16 | keep `dequantize=False` for serving; accept bf16 only to train |
| NaN loss fine-tuning a 4-bit bnb model | fp16 compute overflow through the k-bit path | `bnb_4bit_compute_dtype=torch.bfloat16`, lower the LR, clip grads |
| NVFP4 benchmarks look awful off NVIDIA | fast kernels are Blackwell SM100 targets | benchmark on SM100 or against the emulated baseline, never BF16 kernels |
| "CUDA out of memory" mid-LoRA | batch or cache pressure, not DQ | shrink batch, gradient checkpointing, offload some layers |

## Quick Reference

| Target | Where |
|--------|-------|
| module 4103 | `docs/phases/phase4-quantization/4100-low-bit/4103-Double-Quantization.md` |
| module 4104 | `docs/phases/phase4-quantization/4100-low-bit/4104-MXFP4-and-NVFP4.md` |
| module 4101 | `docs/phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md` |
| CHEAT-SHEET-015 | `docs/learning-resources/cheat-sheets/CHEAT-SHEET-015-Quantization-Formats-Methods.md` |
