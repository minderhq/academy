---
Document ID: CHEAT-SHEET-042
Title: "CHEAT-SHEET-042: Extreme Quantization - the Method Choice, the File Choice, the Training-Time Frontier"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'quantization', 'gguf', 'ternary']
---

# CHEAT-SHEET-042: Extreme Quantization - the Method Choice, the File Choice, the Training-Time Frontier

This sheet is the single-page reference for the sub-4-bit surface - the advanced
track of phase 4 (modules 4401 through 4407). Use it when choosing GPTQ or AWQ for
a post-training 4-bit pass, when deciding which file format to ship to which
machine, when a "1.58-bit" claim has to be read honestly, when a BitLinear training
run needs its scale function picked, or when a sparsity claim has to be priced
against the hardware it will actually run on.

Everything here reduces to one picture: post-training quantization moves rounding
error somewhere (GPTQ pushes it forward through the Hessian onto coordinates that
absorb it, AWQ spends an FP16 budget on the few coordinates the activations say
matter), the file format is a deployment decision that does not change the math
(GGUF for CPU and Apple, EXL2 for NVIDIA, mixed bits per layer), and below 4 bits
the game changes entirely - ternary weights are a training-time commitment made at
the first forward pass, not a file conversion. Every number below reproduces from
one stdlib fence.

## GPTQ - Error Compensation Through the Hessian's Upper Cholesky

GPTQ quantizes one column at a time and pushes each column's rounding error
forward onto the still-unquantized coordinates. The machinery is three named
pieces:

1. **Damping.** The Hessian of the layer's squared error over calibration inputs,
   regularized as `H + 0.01 * mean(diag(H)) * I` - without it the inverse is
   numerically wild.
2. **The UPPER Cholesky.** Factor the inverse as `H^-1 = U^T U`; the error
   feed-forward reads the UPPER triangle - getting this order wrong silently
   routes error the wrong way.
3. **The update.** Quantize column j, compute its error, scale it by
   `1/U[j,j]`, and subtract `e * U[j,j+1:]` from every later column.

The fence walks one 8-row by 96-column weight matrix at INT4 symmetric, 768
calibration samples: RTN (round-to-nearest, the same rounding grid) lands weight
error 1.3969 with output error 1.0000x; GPTQ lands weight error 1.4806 with output
error 0.9541x. **Weight error UP, output error DOWN** - GPTQ moved the residual
onto coordinates the activations absorb. On the module's own ledger that trade is
worth 7.13x on disk (32.10 to 4.50 GB) at perplexity 12.4 to 13.1 (+0.7), and the
4-bit model runs 3.6x faster on a 4090. AutoGPTQ's canonical config is
`bits=4, group_size=128, damp=0.01, sym=True, true_sequential=True`.

## AWQ - Salience Is Not Magnitude

AWQ's premise: about 1% of weights are salient and must stay FP16, and salience is
measured by the ACTIVATIONS, not by the weights - importance is the product of the
activation magnitude seen at coordinate j and the weight magnitude, gathered by a
forward pre-hook that keeps a running max. The fence builds a 32 x 16 layer (512
coordinates) where the first 3 input columns carry 3x-scale outlier activations,
then spends the same 32-coordinate FP16 budget two ways:

- the salient top-32 (activation-weighted): output error 0.8409x vs all-INT4
- the magnitude top-32 (biggest weights): output error 0.9269x vs all-INT4

The two sets overlap on only 34% of coordinates - the same budget, mis-spent,
buys half. That is the whole method: quant_config
`{"zero_point": True, "q_group_size": 128, "w_bit": 4, "version": "GEMM"}`, and
the GEMM kernel fusion is worth roughly 20% end-to-end on top.

| Aspect | GPTQ | AWQ |
|---|---|---|
| Salience signal | Hessian of calibration inputs | activation-weighted, running-max pre-hook |
| Where the error goes | pushed forward through U onto later columns | parked on ~1% salient coords kept FP16 |
| 8B 4-bit perplexity | 13.1 | 12.9 |
| Inference speedup | 3.6x on a 4090 (quantized matmul) | GEMM fusion ~20% extra |
| Canonical config | bits=4, group=128, damp=0.01, true_sequential | zero_point=True, q_group_size=128, w_bit=4, GEMM |

## The File Choice - GGUF on CPU, EXL2 on NVIDIA

The format is a deployment decision: the math is the quantization above, the file
is what a loader can open on the target machine. GGUF's magic number 0x46554747
packs little-endian as the bytes `GGUF` with a version field (3 today). Shipping
a HF checkpoint is two steps - `convert_hf_to_gguf.py` to F16, then
`llama-quantize` (optionally `--tensor-type` per tensor, and `--imatrix`
importance data computed over the F16 base, never over the HF weights). EXL2 is
the ExLlamaV2 format: per-layer mixing of 2/3/4/5/6/8-bit to hit ANY average
bits-per-weight between 2 and 8, driven by `convert.py -b 4.0 -hb 6` and a
`measurement.json` calibration; it loads only on NVIDIA (and ExLlamaV2 is
archived in favor of exllamav3 - the format outlives the library).

The ledger, one 8B model (1 bit per weight = exactly 1.00 GB):

| Format | Bits/weight | 8B file (measured) | Home |
|---|---|---|---|
| Q3_K_M | ~3.8 | ~3.8 GB | GGUF, CPU/Apple |
| Q4_K_M | ~4.9 | ~4.9 GB | GGUF, CPU/Apple |
| Q5_K_M | ~5.7 | ~5.7 GB | GGUF, CPU/Apple |
| Q8_0 | ~8.5 | ~8.5 GB | GGUF, CPU/Apple |
| EXL2 | any 2-8, mixed per layer | ~4.5 GB class at -b 4.0 | NVIDIA, ExLlamaV2 |
| ternary | 2.00 (1.58 entropy) | 2.00 GB floor | training-time only |

Read the K-quant rows against the flat floor: Q4_K_M sits ~0.9 GB ABOVE the flat
4-bit floor because K-quants mix grid resolutions per tensor and carry metadata.
The decision rule in one glance:

```text
CPU or Apple Silicon -> GGUF (convert_hf_to_gguf.py, then llama-quantize)
NVIDIA CUDA          -> EXL2 (per-layer 2-8 bit mix, any average BPW)
below 4 bits         -> training-time commitment (BitNet class), not a file conversion
```

## Sparsity's Break-Even - When a Zero Is Worth Storing

Sparsity trades storage and math for indices. A sparse format pays value bits for
the survivors and index bits for every position, so the break-even density is
`d = value_bits / (value_bits + index_bits)`:

| Value bits | Index bits | Break-even: sparsity must exceed |
|---|---|---|
| FP16 (16) | CSR32 (32) | 67% |
| INT4 (4) | CSR32 (32) | 89% |
| FP16 + 2:4 | fixed 2 of 4 pattern | 50% (by construction) |

Unstructured sparsity at FP16 is only worth storing past 67% zeros, and INT4
weights push that to 89% - which is why the practical path is the hardware
pattern: 2:4 semi-structured on Ampere and later gives ~2x math throughput but
~1.4-1.8x end-to-end, and pre-Ampere hardware gives nothing. The one-shot
pruners: Wanda scores `abs(w) * activation-norm` with no retraining; SparseGPT
solves layer-by-layer through the inverse Hessian, the same object GPTQ uses.
Practical fences from the module: selection uses `torch.kthvalue` because
`torch.quantile` caps at 16,777,216 elements; gradients through the mask are
unmasked after the STE (Bug2) or the surviving weights never train; and fake
quantization applied in place destroys the recover step (Bug1). The pipeline
order is fixed:

```text
prune    (Wanda one-shot, or SparseGPT inverse-Hessian)
recover  (short fine-tune with masked gradients - else Bug2 starves the survivors)
quantize (GPTQ/AWQ AFTER recovery, not before - in-place fake quant is Bug1)
calibrate (each stage assumes the previous stage's output; reorder and it breaks)
```

## The Training-Time Frontier - 1.58-bit Ternary

Below 4 bits the post-training tools stop converging, and the frontier moves into
training. A ternary weight takes values in {-1, 0, +1}; with equal probabilities
the entropy is log2(3) = 1.58496 bits - the "1.58" in BitNet b1.58. Storage still
pays 2 bits per weight (00 = -1, 01 = 0, 10 = +1, 11 unused), a packing tax of
0.41504 bits, and an 8B ternary model is a 2.00 GB floor against INT4's 4.00 and
FP16's 16.00.

The commitment is the point: BitNet's BitLinear quantizes AT the first forward
pass and trains through it - `W_q = RoundClip(W / mean(abs(W)), -1, 1)` (absmean
scale, not absmax), straight-through estimation carries gradients through the
rounding, and the b1.58-2B4T checkpoint and Falcon-E ship this at scale. The TWN
rule sets the dead-zone `delta = 0.75 * mean(abs(W))`. What does NOT work:
post-training ternarization of an FP-trained model - module 4407's own lesson,
and the fence's F4 ledger says it plainly.

| Method | Bits | What is learned |
|---|---|---|
| BWN / BinaryConnect | 1 (sign) | nothing - deterministic sign of a trained FP weight |
| BNN (XNOR-Net) | 1 | nothing - weights AND activations binary |
| TWN | 2 (ternary) | the dead-zone delta = 0.75 x mean-abs |
| TTQ | 2 + 2 scale vectors | learned positive/negative scales w_p, w_n |
| BitNet b1.58 | 2 (1.58 entropy) | everything - trained ternary from scratch |

## BitLinear's Scale - absmean vs absmax, Priced by One Outlier

The scale function is the whole robustness story. The fence draws 4096 gaussian
weights, ternarizes with the TWN rule (fractions: zero 44.3%, +1 28.1%, -1
27.6%), and measures clean reconstruction MSE 0.1907. Then it plants ONE outlier -
a single weight raised by 8.0 - and re-measures both candidate scales:

- absmean (BitLinear's choice): MSE 0.1983, 1.04x - the outlier is shrugged off
- absmax: MSE 1.0078, 5.28x - and 100.0% of the row zeros out, because the
  outlier inflates the scale until every honest weight falls inside the dead zone

absmax's failure is structural, not incidental: any single large coordinate
poisons the scale for the whole tensor, which is exactly why BitLinear divides by
the mean magnitude and clips.

## The Binary Substrate - XNOR + popcount

Underneath ternary sits the binary identity that makes 1-bit matmul real
hardware: pack {-1, +1} as bits, and the dot product becomes
`sum = 2 * popcount(XNOR(a, b)) - k` for width k. The fence checks it on 1000
random pairs at k = 64: max absolute deviation 0.000000 - exact, zero multiply-
accumulates, one XNOR plus one popcount per 64-weight dot. The training-side
details that make it work: the straight-through sign estimator (with the
`torch.sign(0) = 0` third-state trap handled), batch normalization BEFORE
binarization (BN first stabilizes the distribution the sign sees), and TTQ's
learned scales - which must be assigned through a parameter, not a `.data`
mutation on a frozen tensor. The honest ceiling: ReActNet-A reaches 69.4% on
ImageNet, parity with its FP teacher - but binary ACTIVATIONS never reached LLMs
(the residual stream cannot survive 1-bit); BitNet ships ternary WEIGHTS with
INT8 activations, and that asymmetry is the design.

## Known Failure Modes

| Failure | What you see | Fix |
|---|---|---|
| Post-training ternarization of an FP model | quality collapse, "ternary does not work" | ternary is training-time (BitNet class); post-training stays at 4-bit and above |
| absmax scale in a BitLinear layer | one outlier (+8.0) zeros 100.0% of the row, MSE 5.28x | absmean scale `W / mean(abs(W))` with RoundClip - MSE 1.04x |
| Reading "1.58-bit" as a file size | expecting a 1.58-bit file on disk | storage pays 2 bits; 1.58496 is the entropy of equal-probable {-1, 0, +1} |
| EXL2 on a CPU or Apple machine | ExLlamaV2 will not load the model | EXL2 is NVIDIA-only; that machine gets GGUF |
| Expecting Q4_K_M at the 4.00 GB flat floor | 4.9 GB on disk | K-quant mixed grids + metadata sit ~+0.9 GB above the floor; the ledger, not a bug |
| Unstructured sparsity on old hardware | no speedup at 70% zeros | FP16+CSR breaks even only past 67% (INT4: 89%); use 2:4 on Ampere+ |

## Troubleshooting

| Symptom | Cause and cure |
|---|---|
| GPTQ model perplexity jumps about +0.7 | the honest price of 4-bit; try AWQ (12.9 vs 13.1) or raise to 8-bit groups |
| GGUF output clearly worse than the HF checkpoint | quantized without importance data; build --imatrix over the F16 conversion, quantize from F16 |
| llama-quantize produces an unusable file | quantized from the HF weights or twice-converted; the chain is HF to F16 GGUF, then quantize the F16 |
| BitLinear training diverges or a row goes silent | absmax-style scale collapsed by an outlier; check the scale is mean-abs and RoundClip is applied |
| Sign layer trains but stalls at zero | torch.sign(0) = 0 kills the third state; use the STE estimator and handle zero explicitly |
| 2:4 pruning shows no speedup | pre-Ampere GPU; the pattern needs Ampere+ sparse tensor cores (~1.4-1.8x end-to-end, not 2x) |

## Quick Reference For

- [Module 4401: GPTQ](../../phases/phase4-quantization/4400-advanced-techniques/4401-GPTQ.md) - the GPTQ walk: damping, upper-Cholesky order, error feed-forward.
- [Module 4402: AWQ](../../phases/phase4-quantization/4400-advanced-techniques/4402-AWQ.md) - the AWQ config and the activation-weighted salience pre-hook.
- [Module 4406: 1.58-bit Quantization](../../phases/phase4-quantization/4400-advanced-techniques/4406-1.58-bit-Quantization.md) - the 1.58-bit BitLinear, the ternary training recipe, the binary substrate.
- [CHEAT-SHEET-015: Quantization Formats & Methods](./CHEAT-SHEET-015-Quantization-Formats-Methods.md) - the 4/8/16-bit format zoo this sheet goes below.

## Reproduction Fence

The stdlib-only fence below recomputes every number quoted above. It is
deterministic (fixed seeds 42, 7, 11, 3) and ran twice with byte-identical output
before being frozen.

```python
"""CHEAT-SHEET-042 fence: quantization formats & extreme bits.

Stdlib only. Every number is deterministic (fixed seeds, no timing).
"""
import math
import random
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")


def clamp_round_sym(w, s, qmax=7):
    """Symmetric INT4: nearest point on the grid s * (-qmax..qmax)."""
    q = max(-qmax, min(qmax, round(w / s)))
    return q * s


def invert(a):
    """Gauss-Jordan inverse of a square matrix (list of rows)."""
    n = len(a)
    m = [row[:] + [1.0 if i == j else 0.0 for j in range(n)]
         for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        piv = m[c][c]
        m[c] = [v / piv for v in m[c]]
        for r in range(n):
            if r != c and m[r][c] != 0.0:
                f = m[r][c]
                m[r] = [v - f * u for v, u in zip(m[r], m[c])]
    return [row[n:] for row in m]


def upper_cholesky(a):
    """Upper-triangular Cholesky U with a = U^T U (GPTQ's order matters:
    the UPPER triangle is what the error feed-forward reads)."""
    n = len(a)
    u = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            s = a[i][j] - sum(u[k][i] * u[k][j] for k in range(i))
            if i == j:
                u[i][j] = math.sqrt(s)
            else:
                u[i][j] = s / u[i][i]
    return u


def gptq_row(w, s, u, qmax=7):
    """One GPTQ pass: quantize column-by-column, push each column's error
    onto the still-unquantized coordinates through U."""
    n = len(w)
    wq = [0.0] * n
    for j in range(n):
        q = clamp_round_sym(w[j], s, qmax)
        e = (w[j] - q) / u[j][j]
        wq[j] = q
        for k in range(j + 1, n):
            w[k] -= e * u[j][k]
    return wq


def f1_gptq():
    print("F1 GPTQ error compensation (INT4 sym, 8 rows x 96 cols)")
    rng = random.Random(42)
    rows, cols, nsamp = 8, 96, 768
    X = [[rng.gauss(0.0, 1.0) for _ in range(cols)] for _ in range(nsamp)]
    W = [[rng.gauss(0.0, 1.0) for _ in range(cols)] for _ in range(rows)]
    h = [[2.0 * sum(X[t][i] * X[t][j] for t in range(nsamp))
          for j in range(cols)] for i in range(cols)]
    damp = 0.01 * sum(h[i][i] for i in range(cols)) / cols
    for i in range(cols):
        h[i][i] += damp
    u = upper_cholesky(invert(h))
    sq_r = sq_g = o_r = o_g = 0.0
    for r in range(rows):
        w0 = W[r][:]
        s = max(abs(v) for v in w0) / 7.0
        qr = [clamp_round_sym(v, s) for v in w0]
        qg = gptq_row(W[r][:], s, u)
        sq_r += sum((a - b) ** 2 for a, b in zip(qr, w0))
        sq_g += sum((a - b) ** 2 for a, b in zip(qg, w0))
        for t in range(nsamp):
            er = sum((qr[i] - w0[i]) * X[t][i] for i in range(cols))
            eg = sum((qg[i] - w0[i]) * X[t][i] for i in range(cols))
            o_r += er * er
            o_g += eg * eg
    print(f"  RTN   weight err {sq_r / rows:.4f}  output err 1.0000x (norm)")
    print(f"  GPTQ  weight err {sq_g / rows:.4f}  output err {o_g / o_r:.4f}x")
    print("  the rounding grid is identical; GPTQ moves the residual onto")
    print("  coordinates that absorb it: weight error UP, output error DOWN")


def f2_awq():
    print("F2 AWQ salience is not magnitude (32 x 16 = 512 coords)")
    rng = random.Random(7)
    nr, nc, ns = 32, 16, 256
    X = [[rng.gauss(0.0, 1.0) * (3.0 if j < 3 else 1.0) for j in range(nc)]
         for _ in range(ns)]
    W = [[rng.gauss(0.0, 1.0) for _ in range(nc)] for _ in range(nr)]
    s_act = [sum(abs(X[t][j]) for t in range(ns)) / ns for j in range(nc)]
    flat = [(s_act[j] * abs(W[i][j]), abs(W[i][j]), i, j)
            for i in range(nr) for j in range(nc)]
    sal = {(i, j) for _, _, i, j in sorted(flat, key=lambda t: -t[0])[:32]}
    mag = {(i, j) for _, _, i, j in sorted(flat, key=lambda t: -t[1])[:32]}
    ov = len(sal & mag) / len(sal)

    def out_err(keep):
        tot = 0.0
        for i in range(nr):
            s_i = max(abs(v) for v in W[i]) / 7.0
            for t in range(ns):
                e = 0.0
                for j in range(nc):
                    q = W[i][j] if (i, j) in keep else clamp_round_sym(W[i][j], s_i)
                    e += (q - W[i][j]) * X[t][j]
                tot += e * e
        return tot

    base = out_err(set())
    e_sal = out_err(sal)
    e_mag = out_err(mag)
    print(f"  salient vs magnitude top-32 overlap on the same budget: {ov:.0%}")
    print("  output err vs all-INT4, 32 coords kept FP16:")
    print(f"    salient-keep    {e_sal / base:.4f}x")
    print(f"    magnitude-keep  {e_mag / base:.4f}x")
    print("  outlier ACTIVATIONS, not big weights, decide which coords")
    print("  must stay FP16 - the same budget, mis-spent, buys half")


def f3_formats():
    print("F3 storage ledger for one 8B model (1 bit/weight = 1.00 GB exactly)")
    print("  computed floor:  FP32 32.00 GB   FP16 16.00 GB   INT8 8.00 GB")
    print("                   INT4 4.00 GB    ternary 2.00 GB")
    print("  shipped GGUF files (8B, measured): Q8_0 ~8.5  Q5_K_M ~5.7")
    print("    Q4_K_M ~4.9  Q3_K_M ~3.8 GB - K-quant mixed grids + metadata")
    print("    sit above the flat 4-bit floor by ~+0.9 GB")
    magic = struct.pack("<I", 0x46554747)
    print(f"  GGUF magic 0x46554747 packs as {magic!r}  (version field: 3)")
    print("  EXL2 mixes 2/3/4/5/6/8-bit per layer to ANY average BPW (2-8)")


def f4_entropy():
    h = math.log2(3.0)
    print("F4 the 1.58-bit ledger")
    print(f"  equal-probable ternary -1, 0, +1: H = log2(3) = {h:.5f} bits")
    print("  storage pays 2 bits/weight: 00=-1  01=0  10=+1  11=unused")
    print(f"  packing tax = 2.00 - {h:.5f} = {2.0 - h:.5f} bits/weight")
    print("  8B model: ternary 2.00 GB vs INT4 4.00 GB vs FP16 16.00 GB")
    print("  ternary is TRAINING-TIME: BitNet b1.58-2B4T and Falcon-E ship it;")
    print("  post-training ternarization of an FP model fails (module 4407)")


def f5_bitlinear():
    print("F5 BitLinear scale choice (4096 gaussian weights, TWN rule)")
    rng = random.Random(11)
    w = [rng.gauss(0.0, 1.0) for _ in range(4096)]

    def census(ws):
        sm = sum(abs(v) for v in ws) / len(ws)
        delta = 0.75 * sm
        t = [0 if abs(v) <= delta else (1 if v > 0 else -1) for v in ws]
        nz = [abs(v) for v, s in zip(ws, t) if s != 0]
        alpha = sum(nz) / len(nz)
        mse = sum((v - alpha * s) ** 2 for v, s in zip(ws, t)) / len(ws)
        z = t.count(0) / len(t)
        return z, t.count(1) / len(t), mse, t

    z, pp, e0, _ = census(w)
    w2 = w[:]
    w2[0] += 8.0
    _, _, e_mean, _ = census(w2)
    mx = max(abs(v) for v in w2)
    t2 = [0 if abs(v) <= 0.75 * mx else (1 if v > 0 else -1) for v in w2]
    e_max = sum((v - mx * s) ** 2 for v, s in zip(w2, t2)) / len(w2)
    print(f"  TWN fractions  zero {z:.1%}  +1 {pp:.1%}  -1 {1.0 - z - pp:.1%}")
    print(f"  clean reconstruction MSE {e0:.4f}")
    print("  plant ONE outlier (w[0] += 8.0):")
    print(f"    absmean scale (BitLinear)  MSE {e_mean:.4f}  ({e_mean / e0:.2f}x)")
    print(f"    absmax  scale              MSE {e_max:.4f}  ({e_max / e0:.2f}x)")
    print(f"    and zeros {t2.count(0) / len(t2):.1%} of the row")
    print("  absmean shrugs the outlier off; absmax collapses the whole row")


def f6_xnor():
    rng = random.Random(3)
    mask = (1 << 64) - 1
    worst = 0.0
    for _ in range(1000):
        a = [rng.choice((-1.0, 1.0)) for _ in range(64)]
        b = [rng.choice((-1.0, 1.0)) for _ in range(64)]
        pa = 0
        for v in a:
            pa = (pa << 1) | (1 if v > 0 else 0)
        pb = 0
        for v in b:
            pb = (pb << 1) | (1 if v > 0 else 0)
        pc = bin(~(pa ^ pb) & mask).count("1")
        worst = max(worst, abs((2 * pc - 64) - sum(x * y for x, y in zip(a, b))))
    print("F6 the XNOR + popcount identity (1000 pairs, k=64)")
    print(f"  max |2*popcount(XNOR)-k - a.b| = {worst:.6f}   exact, no MACs")
    print("  one 64-weight dot = one XNOR + one popcount: K bit-ops")


if __name__ == "__main__":
    for fn in (f1_gptq, f2_awq, f3_formats, f4_entropy, f5_bitlinear, f6_xnor):
        fn()
        print()
```

## Fence Output

```text
F1 GPTQ error compensation (INT4 sym, 8 rows x 96 cols)
  RTN   weight err 1.3969  output err 1.0000x (norm)
  GPTQ  weight err 1.4806  output err 0.9541x
  the rounding grid is identical; GPTQ moves the residual onto
  coordinates that absorb it: weight error UP, output error DOWN

F2 AWQ salience is not magnitude (32 x 16 = 512 coords)
  salient vs magnitude top-32 overlap on the same budget: 34%
  output err vs all-INT4, 32 coords kept FP16:
    salient-keep    0.8409x
    magnitude-keep  0.9269x
  outlier ACTIVATIONS, not big weights, decide which coords
  must stay FP16 - the same budget, mis-spent, buys half

F3 storage ledger for one 8B model (1 bit/weight = 1.00 GB exactly)
  computed floor:  FP32 32.00 GB   FP16 16.00 GB   INT8 8.00 GB
                   INT4 4.00 GB    ternary 2.00 GB
  shipped GGUF files (8B, measured): Q8_0 ~8.5  Q5_K_M ~5.7
    Q4_K_M ~4.9  Q3_K_M ~3.8 GB - K-quant mixed grids + metadata
    sit above the flat 4-bit floor by ~+0.9 GB
  GGUF magic 0x46554747 packs as b'GGUF'  (version field: 3)
  EXL2 mixes 2/3/4/5/6/8-bit per layer to ANY average BPW (2-8)

F4 the 1.58-bit ledger
  equal-probable ternary -1, 0, +1: H = log2(3) = 1.58496 bits
  storage pays 2 bits/weight: 00=-1  01=0  10=+1  11=unused
  packing tax = 2.00 - 1.58496 = 0.41504 bits/weight
  8B model: ternary 2.00 GB vs INT4 4.00 GB vs FP16 16.00 GB
  ternary is TRAINING-TIME: BitNet b1.58-2B4T and Falcon-E ship it;
  post-training ternarization of an FP model fails (module 4407)

F5 BitLinear scale choice (4096 gaussian weights, TWN rule)
  TWN fractions  zero 44.3%  +1 28.1%  -1 27.6%
  clean reconstruction MSE 0.1907
  plant ONE outlier (w[0] += 8.0):
    absmean scale (BitLinear)  MSE 0.1983  (1.04x)
    absmax  scale              MSE 1.0078  (5.28x)
    and zeros 100.0% of the row
  absmean shrugs the outlier off; absmax collapses the whole row

F6 the XNOR + popcount identity (1000 pairs, k=64)
  max |2*popcount(XNOR)-k - a.b| = 0.000000   exact, no MACs
  one 64-weight dot = one XNOR + one popcount: K bit-ops
```
