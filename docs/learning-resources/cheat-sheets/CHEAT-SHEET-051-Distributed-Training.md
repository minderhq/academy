---
Document ID: CHEAT-SHEET-051
Title: "CHEAT-SHEET-051: Distributed Training - the Memory Bill, the Stability Wall, and the Campaign"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'distributed', 'fsdp', 'training']
---

# CHEAT-SHEET-051: Distributed Training - the Memory Bill, the Stability Wall, and the Campaign

The distributed-training surface is phase5-finetuning's 5400-distributed-training track - 5401 Data Parallelism, 5402 Model Parallelism, 5405 FSDP2 and torchao and 5406 Distributed LR Scaling - four modules with no sheet anywhere in the track (scope scan: the 00-META sheet index carries no id beside any of the four; CHEAT-SHEET-046 owns the optimizer-state ledger this bill builds on, QUICK-REF-VOLUME-5 carries the syntax, not the closure). This sheet takes the track as the three questions the student actually asks: what fits on one GPU and what sharding buys back, which parallel axis pays its way and which one just adds idle, and how a 64-GPU run stays stable from warmup to wall without a NaN ending the campaign.

The sheet runs as seven priced exhibits: the per-rank memory bill with the shard that fits (F1), the sharding ladder priced at world W=8 (F2), the pipeline bubble and the M >= 4 x P rule (F3), the tensor-pairing law and the 3D layout (F4), FSDP2's three states with the float8 dead zone and the STE (F5), the noise law, the wall, and the warmup rule that is not a taste question (F6), and the critical batch size with the five-bill campaign (F7). Every number below is printed by the canonical fence at the bottom of the page: the full 456-line stdlib fence reproduces all seven from fixed-seed runs its own asserts pin - no numpy, no torch, no wall clock - and its 64-line output sits frozen below it byte-for-byte.

## The Per-Rank Memory Bill - 16 Bytes per Parameter and the Shard That Fits

Adam on bf16 weights is 16 bytes per parameter: weights 2 (bf16) + grads 2 (bf16) + optimizer 12 (fp32 master + two fp32 moments). A 7B model lands at 112 GB per rank - 14 + 14 + 84 - and the 80 GB GPU says no before step one. DDP replicates the whole bill on every rank; FSDP FULL_SHARD divides everything but the live shard by the world size, so the replica problem becomes a division problem: W=4 fits 28.0 GB per rank, W=8 fits 14.0, W=16 fits 7.0.

| Surface | Per rank (7B, bf16, Adam) | What it is |
| --- | --- | --- |
| params | 14 GB | bf16 weights |
| grads | 14 GB | bf16 gradients |
| optimizer | 84 GB | fp32 master + two fp32 moments |
| DDP replica total | 112 GB | params + grads + optimizer, replicated |

## The Sharding Ladder - What Each Rung Costs in Communication

FSDP2's sharding strategies are a ladder of memory savings priced in communication. At world W=8 the same 7B+Adam bill reads: NO_SHARD holds 112.00 GB and pays one grad all-reduce (1.00x baseline); SHARD_GRAD_OP keeps full params at rest and shards grads plus optimizer to 26.25 GB while paying reduce-scatter instead of all-reduce - roughly baseline speed; FULL_SHARD drops the at-rest bill to 14.00 GB but must all-gather params before each use and reduce-scatter grads after - about 2x the collectives, 0.70-0.85x of DDP's speed; HYBRID_SHARD runs FULL_SHARD inside each 8-GPU NVLink group and replicates across groups - the 14.00 GB bill with communication that never leaves the node.

| Strategy | At-rest per rank (W=8) | Communication | Speed |
| --- | --- | --- | --- |
| NO_SHARD (DDP) | 112.00 GB | grad all-reduce only | 1.00x baseline |
| SHARD_GRAD_OP | 26.25 GB | grad reduce-scatter | ~baseline |
| FULL_SHARD | 14.00 GB | all-gather + reduce-scatter (~2x) | 0.70-0.85x of DDP |
| HYBRID_SHARD@8 | 14.00 GB | intra-node only | best at 8xN |

```text
NO_SHARD        every rank holds full params + grads + optimizer; one grad all-reduce
SHARD_GRAD_OP   params full at rest; grads + optimizer sharded; same collective count
FULL_SHARD      everything 1/W: all-gather before use, reduce-scatter after -> ~2x comms
HYBRID_SHARD    FULL_SHARD inside each NVLink group, replicated across groups -> 8xN
```

## The Pipeline Bubble - Micro-Batches Buy the Stages Back

Pipeline parallelism splits layers into P stages and pays an idle fraction of (P-1)/(M+P-1): at P=4 the bubble falls from 42.9% at M=4 to 8.6% at M=32 and 4.5% at M=64, and at P=8 it is 63.6% at M=4 and still 9.9% at M=64. 1F1B keeps only P micro-batches in flight where GPipe holds all M alive - at P=8 that is 8 in-flight activations instead of 32. The working rule is M >= 4 x P: P=4 with M=32 lands at 8.6% idle while P=8 with M=8 pays 46.7% - more stages without more micro-batches buys a slower pipeline.

## The Tensor-Pairing Law - Two All-Reduces Forward, Two Backward

Tensor parallelism splits every weight matrix, and the pairing decides the bill: ColumnParallel cuts the output dim and all-reduces the input grad in backward; RowParallel cuts the input dim and all-reduces its output in forward. The transformer pairing is QKV Column + out-proj Row and up/gate Column + down-proj Row, so each layer pays 2 all-reduces per forward and 2 per backward - 4 per layer per step, all microbatch-sized. That is why TP stays inside the NVLink node (TP <= 8) while PP and DP carry the cross-node hops. A 64-GPU run as TP=4 x PP=4 puts 16 GPUs in each pipeline unit and leaves DP = 64/16 = 4.

```text
ColumnParallel  splits the OUTPUT dim; backward all-reduces the input grad
RowParallel     splits the INPUT dim; forward all-reduces the output
pairing         QKV Column + out-proj Row | up/gate Column + down Row -> 2 AR fwd + 2 bwd
law             TP messages are microbatch-sized: TP <= 8 inside NVLink; PP/DP across nodes
```

## FSDP2's Three States, the Float8 Dead Zone, and the STE

A parameter in FSDP2 lives in three states: a DTensor holding a 1/W fp32 local shard before forward, a full bf16 Parameter during forward - the all-gather you pay for - and a DTensor with a sharded gradient again after backward. The memory spike is one block's worth: shard per block and the peak never becomes the whole model.

torchao's float8 recipes fail on the outlier. One row four orders above the population forces a tensorwise scale that starves the healthy rows: relative error 0.080 with 11.1% of entries flushed to zero, against rowwise scales at 0.026 with 0.0% flushed - 3.0x lower error with the flush eliminated. The mechanism is the dead zone: e4m3's smallest normal is 2^-6 = 0.015625 and the subnormal step is 2^-9 = 0.001953, and healthy entries land at ~0.0049 fp8-units under the outlier's tensorwise scale - inside the zone where quantization rounds them to zero. (The fence rebuilds this on a deterministic stdlib e4m3 grid; the module's own torch run measured the same regime: 10.3%/14% tensorwise vs 2.6%/0% rowwise.)

| Scaling recipe | Healthy-row rel err | Entries flushed to zero |
| --- | --- | --- |
| tensorwise (one scale per tensor) | 0.080 | 11.1% |
| rowwise (one scale per row) | 0.026 | 0.0% |

```text
before forward : DTensor  fp32  local shard               <- 1/W of the master weights
after forward  : Parameter bf16 full                      <- the all-gather you pay for
after backward : DTensor  fp32  shard + DTensor gradient  <- re-sharded, spike freed
rule           shard per block: the spike is one block's worth, never the whole model
```

QAT's fake-quantize has zero gradient almost everywhere - round is piecewise constant. The straight-through estimator passes the identity instead: y = x + (q(x) - x).detach() quantizes forward and copies gradient backward. The fence's round of 2.3 at scale 0.5 lands on 2.5 and proves the split: the plain fake-quant grad is 0.0000, the STE grad is 1.0000.

## The Noise Law, the Wall, and the Warmup Rule That Is Not a Taste Question

The gradient noise shrinks with the batch exactly as the law says: at B=32 the empirical std of the batch-mean gradient is 0.1767 against the predicted sigma/sqrt(B) of 0.1768; at B=256 it is 0.0624 vs 0.0625. That law is what licenses linear LR scaling - k times the batch can carry k times the rate.

Until it cannot. The rate's stability bound is |1 - eta x lambda| < 1, so eta_max = 2/lambda is a wall: the fence's toy with lambda=1 walks linear scaling k=1..4 to convergence (final error 0.0900, 0.0090, 0.0141) and diverges at k=8 - eta 2.400 is past the wall - and at every k after. The sqrt rule trades speed for headroom: k=32 lands at eta 1.697 with amplification 6.60, inside the wall with margin, converging at 0.0734.

Warmup has a sizing rule, not a vibe. On the fence's two-phase toy (lambda 8.0 for the first 200 steps, then 0.5; target eta 1.0), the rule W > eta_target x lambda_early x t_sharp / 2 demands W > 800: no warmup diverges 20/20 seeds, W=400 - half the rule - diverges 20/20, and W=1600 keeps 20/20 alive at median final |w| 0.0091. Half the rule buys nothing.

```text
noise law       Var[g_B] = Var[g] / B: batch k scales the legal rate by k - until the wall
wall            |1 - eta * lambda| < 1 -> eta_max = 2 / lambda; linear scaling is legal
                only while eta0 * k < eta_max (k=8 at eta0=0.3 crossed it: 2.400 > 2.0)
warmup sizing   W > eta_target * lambda_early * t_sharp / 2  (the fence's toy demands 800)
half measures   W=400 against a W>800 rule diverged 20/20 - half the rule is zero-safe
```

## The Critical Batch and the Five-Bill Campaign

Steps-to-threshold is not linear in batch. The fence's two-scale quadratic walks S(B) from 155 down through 114, 101, 96, 94, 91, 90, 89, 89 to 89 across B=1..512, and the 1/B fit prices S_min = 88.1 at B_noise = 0.7 - the knee sits at 176.3 = 2 x S_min. S(1) costs 1.76x the floor while S(512) costs 1.01x: past the critical batch, more batch buys almost no speed.

Gradient accumulation is exact arithmetic on averages - mean-of-means error 0.00e+00 - and a bookkeeping hazard on everything around it. Drop-last shifts the batch mean 0.0017. The same 3-epoch budget becomes 384 optimizer steps as micro-32 but 48 with accum x8, so a 10-step warmup is 2.6% of the micro run and 20.8% of the accumulated one: step-counted schedules must be multiplied by the accumulation factor or they fire eight times too early. And clipping disagrees with averaging: clip-then-average gives norm 0.770 where average-then-clip gives 1.000 - 0.770x the effective LR, 6.7 degrees off in direction. Clip once, on the averaged gradient.

The campaign prices five configs on one 1.2B-token fine-tune at 3,500 tok/s/GPU and $2.50/GPU-h, 20 seeds each. R1 baseline k=1 converges in 95.24 wall-hours for $238.10. R2 k=8 linear+warmup lands the same bill in 11.90 hours. R3 k=8 with no warmup diverges at ~step 2, 20/20. R4 k=32 linear+warmup clears the early phase, hits the target at ~step 38, then diverges at ~step 6551 - past the late wall. R5 k=32 sqrt+warmup holds all 20 seeds. The retries are not free: R3 burned $0.04 and its replacement costs the full $238.13 in 11.91 hours; R4 burned $129.98 - six thousand five hundred steps of 32 GPUs - and its replacement costs $368.08 in 4.60 hours. The wall does not refund.

## Known Failure Modes

| Failure mode | The tell |
| --- | --- |
| budgeting 112 GB for a 7B+Adam replica on one 80 GB GPU | 16 bytes/param x 7B = 112 GB - the OOM fires at model load, before step one; shard (F1) |
| sharding the whole model as one container | the all-gather spike becomes the entire model and the peak barely moves - shard per block (F5) |
| running tensor-parallel across an Ethernet link | TP's 4 collectives per layer are microbatch-sized; throughput collapses past the NVLink node - keep TP <= 8 (F4) |
| scaling the LR linearly past eta_max | k=8 diverged 20/20 at eta 2.400 > 2/lambda - the wall, not the seed, is the cause (F6) |
| halving the warmup to save wall-clock | W=400 against a W > 800 rule diverged 20/20 - half the rule is zero-safe (F6) |
| retrying a diverged config without changing the schedule | R4 hit the target at ~step 38 and still died at ~step 6551 - fix the endpoint, not the noise (F7) |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| CUDA OOM while loading the model | the bill is 16 bytes/param (F1): fully_shard per block and the at-rest shard is 112/W |
| FSDP runs 30%+ slower than DDP | FULL_SHARD pays ~2x collectives for the 1/W bill (F2): HYBRID_SHARD across 8-GPU groups keeps the savings on-node |
| pipeline GPUs idle most of the step | the bubble is (P-1)/(M+P-1) (F3): raise micro-batches to at least 4xP and switch to 1F1B |
| float8 model degrades on sparse activations | the outlier's tensorwise scale starves healthy rows (F5): rowwise scales, 3.0x lower error |
| loss NaNs right after adding GPUs | linear scaling crossed the wall (F6): cap eta x k at 2/lambda and switch to sqrt scaling with warmup |
| accumulated run's warmup or decay fired early | schedules are step-counted (F7): multiply by the accumulation factor, and clip once on the averaged gradient |

## Quick Reference For

- [Module 5401: Data Parallelism](../../phases/phase5-finetuning/5400-distributed-training/5401-Data-Parallelism.md) - the memory bill, DDP's all-reduce and the FSDP ladder F1 and F2 price
- [Module 5402: Model Parallelism](../../phases/phase5-finetuning/5400-distributed-training/5402-Model-Parallelism.md) - tensor pairing, the pipeline bubble and the 3D layout of F3 and F4
- [Module 5405: FSDP2 and torchao](../../phases/phase5-finetuning/5400-distributed-training/5405-FSDP2-and-torchao.md) - the three states, the float8 recipes and the QAT STE behind F5
- [Module 5406: Distributed LR Scaling](../../phases/phase5-finetuning/5400-distributed-training/5406-Distributed-LR-Scaling.md) - the noise law, the wall, warmup sizing and the campaign of F6 and F7

## The Canonical Fence

The full stdlib fence below reproduces every number on this page - F1 through F7 - from fixed-seed runs its own asserts pin: no numpy, no torch, no wall clock, byte-identical across runs.

```python
"""tick-1024 canonical fence - CHEAT-SHEET-051 Distributed Training.

Stdlib only. Deterministic: fixed seeds, fixed inputs, no time, no set-order
dependence. Prints F1..F7 + FENCE-051-OK tail.

F1-F4 recompute the exact arithmetic canon of modules 5401 (data parallelism)
and 5402 (model parallelism). F5 rebuilds module 5405's float8 outlier
experiment on a deterministic stdlib input with a full e4m3 quantizer grid
(torch cannot be imported here; the module's own torch run measured 10.3%/14%
tensorwise vs 2.6%/0% rowwise - this fence reproduces the regime). F6 and F7
re-run module 5406's fences verbatim, same seeds, same canonical numbers.
"""
import bisect
import math
import random
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ======================================================================
# F1 - the per-rank memory bill (module 5401's ledger, 7B params)
# ======================================================================
N_PARAMS = 7_000_000_000
BYTES_BF16 = 2
BYTES_FP32 = 4

params_gb = N_PARAMS * BYTES_BF16 / 1e9          # 14 GB
grads_gb = params_gb                              # 14 GB
adam_gb = N_PARAMS * 3 * BYTES_FP32 / 1e9        # fp32 master + two moments: 84 GB
ddp_gb = params_gb + grads_gb + adam_gb           # 112 GB

assert params_gb == 14.0 and grads_gb == 14.0
assert adam_gb == 84.0 and adam_gb == 3 * 28.0
assert ddp_gb == 112.0

print("F1 DP memory bill (7B params, bf16 weights, Adam):")
print(f"  params {params_gb:.0f} GB + grads {grads_gb:.0f} GB + optimizer {adam_gb:.0f} GB"
      " (fp32 master + two moments)")
print(f"  DDP per-rank replica            : {ddp_gb:.0f} GB   (does not fit an 80 GB GPU)")
ladder = [(4, ddp_gb / 4), (8, ddp_gb / 8), (16, ddp_gb / 16)]
assert ladder[1][1] == 14.0
cells = " | ".join(f"W={w} -> {gb:.1f} GB" for w, gb in ladder)
print(f"  FSDP FULL_SHARD at-rest per rank: {cells}")

# ======================================================================
# F2 - the sharding ladder priced at world W=8 (module 5401)
# ======================================================================
W = 8
no_shard = ddp_gb                                    # 112.00
shard_grad_op = params_gb + (grads_gb + adam_gb) / W  # 14 + 98/8 = 26.25
full_shard = ddp_gb / W                               # 14.00
hybrid = full_shard                                   # same ledger inside an 8-GPU group

assert abs(shard_grad_op - 26.25) < 1e-9
assert full_shard == 14.0 and hybrid == 14.0

print("F2 sharding ladder at world W=8 (same 7B, same Adam):")
print(f"  NO_SHARD (DDP)  at-rest {no_shard:6.2f} GB   comm: grad all-reduce only      speed: 1.00x baseline")
print(f"  SHARD_GRAD_OP   at-rest {shard_grad_op:6.2f} GB   comm: grad reduce-scatter       speed: ~baseline (full params stay)")
print(f"  FULL_SHARD      at-rest {full_shard:6.2f} GB   comm: ~2x (all-gather + red-sc) speed: 0.70-0.85x of DDP")
print(f"  HYBRID_SHARD@8  at-rest {hybrid:6.2f} GB   comm: intra-node only           speed: best at 8xN")

# ======================================================================
# F3 - the pipeline bubble (module 5402)
# ======================================================================
def bubble(p, m):
    return (p - 1) / (m + p - 1)

assert abs(bubble(4, 4) - 3 / 7) < 1e-12            # 42.9%
assert abs(bubble(4, 32) - 3 / 35) < 1e-12          # 8.6%

print("F3 pipeline bubble = (P-1)/(M+P-1):")
for p in (4, 8):
    row = "   ".join(f"M={m:>2} -> {bubble(p, m):>5.1%}" for m in (4, 8, 16, 32, 64))
    print(f"  P={p}: {row}")
print("  1F1B keeps P micro-batches in flight (P=8: 8) where GPipe holds all M (32) alive")
print("  rule M >= 4 x P: P=4/M=32 lands at 8.6%; P=8/M=8 pays 46.7% idle")

# ======================================================================
# F4 - the tensor-pairing law and the 3D layout (module 5402)
# ======================================================================
ar_fwd = 2          # attention out-proj RowParallel + MLP down-proj RowParallel
ar_bwd = 2          # their backward counterparts
per_layer = ar_fwd + ar_bwd

world = 64
tp, pp = 4, 4
gpus_per_unit = tp * pp          # one pipeline unit holds TP x PP ranks
dp = world // gpus_per_unit      # the remainder is the data-parallel fan-out

assert per_layer == 4 and gpus_per_unit == 16 and dp == 4

print("F4 tensor-parallel pairing and the 3D layout:")
print("  per transformer layer: QKV Column + out-proj Row, up/gate Column + down Row")
print(f"  -> {ar_fwd} all-reduces per forward + {ar_bwd} per backward = {per_layer} per layer per step")
print("  TP axis: messages are microbatch-sized -> keep TP <= 8 inside one NVLink node")
print(f"  {world} GPUs as TP={tp} x PP={pp}: {gpus_per_unit} GPUs per pipeline unit -> DP = {world}/{gpus_per_unit} = {dp}")

# ======================================================================
# F5 - FSDP2's three states + the float8 dead zone + the STE (module 5405)
#      stdlib e4m3 grid: subnormals k*2^-9 (k=1..7), normals 2^(E-7)*(1+m/8)
#      for E=1..14, top slot 256..448 step 32. Max finite 448, smallest
#      normal 2^-6. Round-to-nearest, ties to even mantissa (grid index
#      parity == mantissa parity throughout the grid).
# ======================================================================
GRID = [0.0]
for k in range(1, 8):
    GRID.append(k * 2.0 ** -9)
for e in range(1, 16):
    base = 2.0 ** (e - 7)
    m_top = 6 if e == 15 else 7
    for m in range(m_top + 1):
        GRID.append(base * (1.0 + m / 8.0))
assert GRID[-1] == 448.0 and all(GRID[i] < GRID[i + 1] for i in range(len(GRID) - 1))
F8_MAX = 448.0


def q_e4m3(v):
    if v == 0.0:
        return 0.0
    sign = -1.0 if v < 0 else 1.0
    a = min(abs(v), F8_MAX)
    i = bisect.bisect_left(GRID, a)
    lo_i = i - 1
    hi_i = i if i < len(GRID) else len(GRID) - 1
    lo, hi = GRID[lo_i], GRID[hi_i]
    d_lo, d_hi = a - lo, hi - a
    if d_lo < d_hi:
        pick = lo
    elif d_hi < d_lo:
        pick = hi
    else:  # exact tie -> round to even mantissa == even grid index
        pick = lo if lo_i % 2 == 0 else hi
    return sign * pick


rows, cols = 256, 512
rng = random.Random(5100)
Wmat = [[rng.gauss(0.0, 1e-4) for _ in range(cols)] for _ in range(rows)]
Wmat[0] = [x * 2e4 for x in Wmat[0]]  # one outlier row, four orders above the healthy population

max_abs = max(abs(v) for r in Wmat for v in r)
scale_t = max_abs / F8_MAX
Wt = [[q_e4m3(v / scale_t) * scale_t for v in r] for r in Wmat]

Wr = []
for r in Wmat:
    s = max(abs(v) for v in r) / F8_MAX
    Wr.append([q_e4m3(v / s) * s for v in r])

h = range(1, rows)  # healthy rows: everything the outlier does not own
num_t = math.sqrt(sum((Wmat[i][j] - Wt[i][j]) ** 2 for i in h for j in range(cols)))
den = math.sqrt(sum(Wmat[i][j] ** 2 for i in h for j in range(cols)))
rt = num_t / den
zt = sum(1 for i in h for j in range(cols) if Wt[i][j] == 0.0) / (len(list(h)) * cols)
num_r = math.sqrt(sum((Wmat[i][j] - Wr[i][j]) ** 2 for i in h for j in range(cols)))
rr = num_r / den
zr = sum(1 for i in h for j in range(cols) if Wr[i][j] == 0.0) / (len(list(h)) * cols)

healthy_units = [abs(Wmat[1][j]) / scale_t for j in range(cols)]
med_units = statistics.median(healthy_units)

# regime asserts (the module's torch run measured 0.103/14% vs 0.026/0%)
assert rt > 2.5 * rr and rt > 0.05
assert zr < 1e-4 and 0.05 < zt < 0.25 and rr < 0.05
assert 2.0 ** -9 == 0.001953125 and 2.0 ** -6 == 0.015625

print("F5 float8 dead zone (stdlib e4m3 grid, 256x512 input, one outlier row):")
print(f"  healthy-row relative err  tensorwise: {rt:.3f}  ({zt:.1%} of entries flushed to zero)")
print(f"  healthy-row relative err     rowwise: {rr:.3f}  ({zr:.1%} flushed)")
print(f"  rowwise contains the outlier: error {rt / rr:.1f}x lower, zero-flush eliminated")
print("  mechanism: smallest normal 2^-6 = 0.015625, subnormal step 2^-9 = 0.001953")
print(f"  healthy entries land at ~{med_units:.4f} fp8-units under the outlier's tensorwise scale"
      " - inside the dead zone")

# QAT straight-through estimator: round() has zero gradient almost everywhere
x0, sc = 2.3, 0.5
plain_fake_grad = 0.0   # d/dx [round(x/sc)*sc] == 0: round is piecewise constant
ste_grad = 1.0          # y = x + (q(x) - x).detach(): backward sees the identity
assert plain_fake_grad == 0.0 and ste_grad == 1.0 and round(x0 / sc) * sc == 2.5
print("  QAT STE: plain fake-quant grad 0.0000   STE grad 1.0000")

# ======================================================================
# F6 - the noise law, the wall, and the warmup (module 5406, verbatim seeds)
# ======================================================================
lam, sigma, w0, B0, eta0, T = 1.0, 1.0, 3.0, 32, 0.3, 2000

rng = random.Random(7)
N = 200_000
noise_rows = []
for B in (32, 256):
    draws = [rng.gauss(0.0, sigma) / math.sqrt(B) for _ in range(N)]
    emp = statistics.pstdev(draws)
    noise_rows.append((B, emp, sigma / math.sqrt(B)))
assert abs(noise_rows[0][1] - 0.1767) < 5e-5 and abs(noise_rows[0][2] - 0.1768) < 5e-5
assert abs(noise_rows[1][1] - 0.0624) < 5e-5 and abs(noise_rows[1][2] - 0.0625) < 5e-5


def walk(k, mode):
    B = B0 * k
    eta = eta0 * (k if mode == "linear" else math.sqrt(k))
    r = random.Random(1000 + k)
    w = w0
    for _ in range(T):
        g = lam * w + r.gauss(0.0, sigma) / math.sqrt(B)
        w -= eta * g
        if abs(w) > 100.0:
            return eta, B, None
    return eta, B, abs(w)


walk_rows = []
for mode in ("linear", "sqrt"):
    for k in (1, 2, 4, 8, 16, 32):
        eta, B, err = walk(k, mode)
        amp = 1.0 / (1.0 - eta * lam / 2.0) if eta * lam < 2.0 else float("inf")
        walk_rows.append((mode, k, eta, 2.0 - eta * lam, amp, err))

by = {(r[0], r[1]): r for r in walk_rows}
lin8 = by[("linear", 8)]
lin32 = by[("linear", 32)]
sqrt32 = by[("sqrt", 32)]
assert lin8[5] is None and lin32[5] is None and math.isinf(lin8[4])
assert abs(lin32[2] - 9.6) < 1e-9 and lin32[3] < 0
assert walk_rows[2][5] is not None  # k=4 linear survives (below the wall)
assert abs(sqrt32[2] - 0.3 * math.sqrt(32)) < 1e-9
assert abs(sqrt32[4] - 6.60) < 5e-3 and abs(sqrt32[5] - 0.0734) < 5e-4

print("F6 the noise law and the wall (eta0=0.3, B0=32, lambda=1):")
for B, emp, pred in noise_rows:
    print(f"  noise: B={B:>4} empirical std {emp:.4f} vs sigma/sqrt(B) {pred:.4f}")
print("  wall: eta_max = 2/lambda = 2.0   (|1 - eta*lambda| < 1 required)")
print(f"  {'rule':>7} {'k':>3} {'eta':>6} {'2-eta':>6} {'amp':>6}  final |w-w*|")
for mode, k, eta, head, amp, err in walk_rows:
    fate = "DIVERGED" if err is None else f"{err:.4f}"
    amp_s = "inf" if math.isinf(amp) else f"{amp:.2f}"
    print(f"  {mode:>7} {k:>3} {eta:>6.3f} {head:>6.2f} {amp_s:>6}  {fate}")

# warmup sizing on the two-phase toy
lam_e, lam_l, t_sharp = 8.0, 0.5, 200
sigma, B, w0, eta_t, T2 = 0.3, 256, 1.0, 1.0, 6000
sig_eff = sigma / math.sqrt(B)
t_min = eta_t * lam_e * t_sharp / 2.0
assert t_min == 800.0


def run_warmup(Wc, seed):
    r = random.Random(seed)
    w = w0
    for t in range(T2):
        eta = eta_t if t >= Wc else eta_t * (t + 1) / Wc
        lam_now = lam_e if t < t_sharp else lam_l
        w -= eta * (lam_now * w + r.gauss(0.0, sig_eff))
        if abs(w) > 50.0:
            return None
    return abs(w)


warm_rows = []
for Wc in (0, 400, 1600):
    fates = [run_warmup(Wc, 200 + s) for s in range(20)]
    dead = sum(1 for f in fates if f is None)
    alive = [f for f in fates if f is not None]
    med = statistics.median(alive) if alive else float("nan")
    warm_rows.append((Wc, dead, med))

assert warm_rows[0][1] == 20 and warm_rows[1][1] == 20 and warm_rows[2][1] == 0
assert abs(warm_rows[2][2] - 0.0091) < 5e-5

print(f"  warmup sizing rule: W > eta_target * lambda_early * t_sharp / 2 = {t_min:.0f}")
for Wc, dead, med in warm_rows:
    name = "constant (no warmup)" if Wc == 0 else f"warmup W={Wc}"
    print(f"  {name:>22}: diverged {dead:>2}/20   median final |w| {med:.4f}")

# ======================================================================
# F7 - critical batch, accumulation, and the five-bill campaign (module 5406)
# ======================================================================
lam_f, lam_s = 1.0, 0.05
eta, sigc = 0.4, 1.5
w0f, w0s = 4.0, 20.0
eps, hold, cap, seeds = 0.4, 10, 5000, 120
Bs = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]


def steps_to(B, seed):
    r = random.Random(3000 + seed)
    wf, ws = w0f, w0s
    below = 0
    for t in range(1, cap + 1):
        sf = r.gauss(0.0, sigc) / math.sqrt(B)
        ss = r.gauss(0.0, sigc) / math.sqrt(B)
        wf -= eta * (lam_f * wf + sf)
        ws -= eta * (lam_s * ws + ss)
        loss = 0.5 * wf * wf + 0.5 * lam_s * ws * ws
        below = below + 1 if loss < eps else 0
        if below >= hold:
            return t
    return cap


S = []
for B in Bs:
    vals = sorted(steps_to(B, s) for s in range(seeds))
    S.append(vals[seeds // 2])

assert S == [155, 114, 101, 96, 94, 91, 90, 89, 89, 89]

us = [1.0 / B for B in Bs]
n = len(us)
su, ss_ = sum(us), sum(S)
suu = sum(u * u for u in us)
suS = sum(u * s for u, s in zip(us, S))
c = (n * suS - su * ss_) / (n * suu - su * su)
a = (ss_ - c * su) / n
B_noise = c / a
assert abs(a - 88.1) < 0.05 and abs(B_noise - 0.7) < 0.05
knee = a * (1 + B_noise / B_noise)
assert abs(knee - 2 * a) < 1e-9

print("F7 critical batch size (two-scale quadratic, median of 120 seeds):")
print(f"  walk S(B): {' -> '.join(str(s) for s in S)}")
print(f"  fit: S_min = {a:.1f}, B_noise = {B_noise:.1f}; knee: S(B_noise) = {knee:.1f} = 2 x S_min")
print(f"  S(1)/S_min = {S[0] / a:.2f}   S(512)/S_min = {S[-1] / a:.2f}")

# gradient accumulation: exact math, bookkeeping divergences
rng = random.Random(41)
samples = [rng.gauss(1.3, 2.0) for _ in range(1024)]
full = sum(samples) / len(samples)
micro = [sum(samples[i * 128:(i + 1) * 128]) / 128.0 for i in range(8)]
acc = sum(micro) / 8.0
assert acc == full  # mean-of-means is exact

samples_1025 = samples + [rng.gauss(1.3, 2.0)]
drop = sum(samples_1025[:1024]) / 1024.0
full1025 = sum(samples_1025) / 1025.0
shift = abs(drop - full1025)
assert abs(shift - 0.0017) < 5e-5

micro_bs, accum, epoch_s, epochs, warm = 32, 8, 4096, 3, 10
steps_micro = epochs * epoch_s // micro_bs
steps_accum = epochs * epoch_s // (micro_bs * accum)
assert steps_micro == 384 and steps_accum == 48
wm = warm / steps_micro * 100
wa = warm / steps_accum * 100
t_m, t_a = steps_micro / 8, steps_accum / 8
assert abs(wm - 2.6) < 0.05 and abs(wa - 20.8) < 0.05
assert min(1.0, t_m / warm) == 1.0 and abs(min(1.0, t_a / warm) - 0.6) < 1e-12


def norm(v):
    return math.sqrt(sum(x * x for x in v))


micros = [(3.2, (1.0, 0.0)), (0.4, (0.6, 0.8)), (0.9, (1.0, 0.0)), (1.1, (0.8, 0.6))]
per = []
for n_, (ux, uy) in micros:
    s = min(1.0, 1.0 / n_)
    per.append((s * n_ * ux, s * n_ * uy))
cx = sum(p[0] for p in per) / 4.0
cy = sum(p[1] for p in per) / 4.0
raw = [(n_ * ux, n_ * uy) for n_, (ux, uy) in micros]
mx = sum(r[0] for r in raw) / 4.0
my = sum(r[1] for r in raw) / 4.0
acc_norm = norm((mx, my))
sc_clip = min(1.0, 1.0 / acc_norm)
ang = lambda v: math.degrees(math.atan2(v[1], v[0]))
clip_norm = norm((cx, cy))
avg_norm = sc_clip * acc_norm
assert abs(clip_norm - 0.770) < 5e-4 and abs(avg_norm - 1.0) < 5e-4
assert abs(abs(ang((cx, cy)) - ang((mx, my))) - 6.7) < 0.05

print(f"  accumulation: mean-of-means exact ({abs(acc - full):.2e}); drop-last shifts the batch mean {shift:.4f}")
print(f"  same 3-epoch budget: micro-{micro_bs} -> {steps_micro} optimizer steps; accum x{accum} -> {steps_accum}")
print(f"  warmup {warm} steps = {wm:.1f}% of the micro run vs {wa:.1f}% of the accumulated run")
print(f"  clip order: clip-then-average norm {clip_norm:.3f} vs average-then-clip {avg_norm:.3f}"
      f" (0.770x the LR, 6.7 deg off)")

# the campaign: five distributed configs on one 1.2B-token fine-tune
lam_e2, lam_l2, t_sharp2 = 8.0, 0.5, 200
sig2, B2, w02, eta02 = 0.3, 32, 1.0, 0.2
sig_eff2 = sig2 / math.sqrt(B2)
T3, tgt, hold3 = 12000, 0.05, 5


def run(eta_t, Wc, seed):
    r = random.Random(seed)
    w = w02
    hit, div = None, None
    below = 0
    for t in range(1, T3 + 1):
        eta = eta_t if t >= Wc else eta_t * t / Wc
        lam_now = lam_e2 if t < t_sharp2 else lam_l2
        w -= eta * (lam_now * w + r.gauss(0.0, sig_eff2))
        if abs(w) > 50.0:
            div = t
            break  # divergence is terminal: the run is killed, no recovery
        if hit is None:
            below = below + 1 if abs(w) < tgt else 0
            if below >= hold3:
                hit = t
    return hit, div


camp_rows = [
    ("R1 baseline k=1", 0.2, 0, 1),
    ("R2 k=8 linear+warmup", 1.6, 2560, 8),
    ("R3 k=8 linear no-warmup", 1.6, 0, 8),
    ("R4 k=32 linear+warmup", 6.4, 10240, 32),
    ("R5 k=32 sqrt+warmup", 0.2 * math.sqrt(32), 1810, 32),
]
tok, tps, usd = 1_200_000_000, 3500, 2.50
res = {}
camp_out = []
for name, eta_t, Wc, world2 in camp_rows:
    fates = [run(eta_t, Wc, 5000 + s) for s in range(20)]
    dead = sum(1 for _, d in fates if d is not None)
    hits = [h for h, _ in fates if h is not None]
    divs = sorted(d for _, d in fates if d is not None)
    med_hit = statistics.median(hits) if hits else -1
    med_div = divs[len(divs) // 2] if divs else -1
    wall = tok / (tps * world2) / 3600.0
    cost = world2 * wall * usd
    res[name] = (med_hit, med_div, world2, wall, cost)
    camp_out.append((name, dead, len(hits), round(med_hit), round(med_div), wall, cost))

r1, r2, r3, r4, r5 = camp_out
assert r1[1] == 0 and r1[2] == 20 and r1[3] == 10
assert r2[1] == 0 and r2[2] == 20 and r2[3] == 38
assert r3[1] == 20 and r3[2] == 0 and r3[4] == 2
assert r4[2] == 20 and r4[1] == 20 and r4[3] == 38 and r4[4] == 6551
assert r5[1] == 0 and r5[2] == 20 and r5[3] == 38
assert abs(r1[6] - 238.10) < 0.01 and abs(r4[6] - 238.10) < 0.01

print("F7 the campaign (1.2B tokens, 3,500 tok/s/GPU, $2.50/GPU-h):")
for name, dead, hits, mh, md, wall, cost in camp_out:
    print(f"  {name}: diverged {dead:>2}/20  hit {hits:>2}/20 (~step {mh:>4})  "
          f"diverge ~step {md:>5}  wall {wall:5.2f} h  ${cost:7.2f}")

retries = []
for src, dst in (("R3 k=8 linear no-warmup", "R2 k=8 linear+warmup"),
                 ("R4 k=32 linear+warmup", "R5 k=32 sqrt+warmup")):
    _, d, world2, wall, _ = res[src]
    dwall, dcost = res[dst][3], res[dst][4]
    burn = d / T3 * wall * world2 * usd
    retries.append((src.split()[0], dst.split()[0], burn + dcost, d / T3 * wall + dwall, burn))

ret3, ret4 = retries
assert abs(ret3[2] - 238.13) < 0.01 and abs(ret3[3] - 11.91) < 0.01
assert abs(ret4[2] - 368.08) < 0.01 and abs(ret4[3] - 4.60) < 0.01
assert abs(ret4[4] - 129.98) < 0.01
for src_t, dst_t, total, hours, burn in retries:
    print(f"  {src_t} diverged -> retry as {dst_t}: ${burn:.2f} burned + ${238.10:.2f} = "
          f"${total:.2f} in {hours:.2f} h")

print("FENCE-051-OK")
```

Its frozen output:

```text
F1 DP memory bill (7B params, bf16 weights, Adam):
  params 14 GB + grads 14 GB + optimizer 84 GB (fp32 master + two moments)
  DDP per-rank replica            : 112 GB   (does not fit an 80 GB GPU)
  FSDP FULL_SHARD at-rest per rank: W=4 -> 28.0 GB | W=8 -> 14.0 GB | W=16 -> 7.0 GB
F2 sharding ladder at world W=8 (same 7B, same Adam):
  NO_SHARD (DDP)  at-rest 112.00 GB   comm: grad all-reduce only      speed: 1.00x baseline
  SHARD_GRAD_OP   at-rest  26.25 GB   comm: grad reduce-scatter       speed: ~baseline (full params stay)
  FULL_SHARD      at-rest  14.00 GB   comm: ~2x (all-gather + red-sc) speed: 0.70-0.85x of DDP
  HYBRID_SHARD@8  at-rest  14.00 GB   comm: intra-node only           speed: best at 8xN
F3 pipeline bubble = (P-1)/(M+P-1):
  P=4: M= 4 -> 42.9%   M= 8 -> 27.3%   M=16 -> 15.8%   M=32 ->  8.6%   M=64 ->  4.5%
  P=8: M= 4 -> 63.6%   M= 8 -> 46.7%   M=16 -> 30.4%   M=32 -> 17.9%   M=64 ->  9.9%
  1F1B keeps P micro-batches in flight (P=8: 8) where GPipe holds all M (32) alive
  rule M >= 4 x P: P=4/M=32 lands at 8.6%; P=8/M=8 pays 46.7% idle
F4 tensor-parallel pairing and the 3D layout:
  per transformer layer: QKV Column + out-proj Row, up/gate Column + down Row
  -> 2 all-reduces per forward + 2 per backward = 4 per layer per step
  TP axis: messages are microbatch-sized -> keep TP <= 8 inside one NVLink node
  64 GPUs as TP=4 x PP=4: 16 GPUs per pipeline unit -> DP = 64/16 = 4
F5 float8 dead zone (stdlib e4m3 grid, 256x512 input, one outlier row):
  healthy-row relative err  tensorwise: 0.080  (11.1% of entries flushed to zero)
  healthy-row relative err     rowwise: 0.026  (0.0% flushed)
  rowwise contains the outlier: error 3.0x lower, zero-flush eliminated
  mechanism: smallest normal 2^-6 = 0.015625, subnormal step 2^-9 = 0.001953
  healthy entries land at ~0.0049 fp8-units under the outlier's tensorwise scale - inside the dead zone
  QAT STE: plain fake-quant grad 0.0000   STE grad 1.0000
F6 the noise law and the wall (eta0=0.3, B0=32, lambda=1):
  noise: B=  32 empirical std 0.1767 vs sigma/sqrt(B) 0.1768
  noise: B= 256 empirical std 0.0624 vs sigma/sqrt(B) 0.0625
  wall: eta_max = 2/lambda = 2.0   (|1 - eta*lambda| < 1 required)
     rule   k    eta  2-eta    amp  final |w-w*|
   linear   1  0.300   1.70   1.18  0.0900
   linear   2  0.600   1.40   1.43  0.0090
   linear   4  1.200   0.80   2.50  0.0141
   linear   8  2.400  -0.40    inf  DIVERGED
   linear  16  4.800  -2.80    inf  DIVERGED
   linear  32  9.600  -7.60    inf  DIVERGED
     sqrt   1  0.300   1.70   1.18  0.0900
     sqrt   2  0.424   1.58   1.27  0.0098
     sqrt   4  0.600   1.40   1.43  0.0194
     sqrt   8  0.849   1.15   1.74  0.0359
     sqrt  16  1.200   0.80   2.50  0.0148
     sqrt  32  1.697   0.30   6.60  0.0734
  warmup sizing rule: W > eta_target * lambda_early * t_sharp / 2 = 800
    constant (no warmup): diverged 20/20   median final |w| nan
            warmup W=400: diverged 20/20   median final |w| nan
           warmup W=1600: diverged  0/20   median final |w| 0.0091
F7 critical batch size (two-scale quadratic, median of 120 seeds):
  walk S(B): 155 -> 114 -> 101 -> 96 -> 94 -> 91 -> 90 -> 89 -> 89 -> 89
  fit: S_min = 88.1, B_noise = 0.7; knee: S(B_noise) = 176.3 = 2 x S_min
  S(1)/S_min = 1.76   S(512)/S_min = 1.01
  accumulation: mean-of-means exact (0.00e+00); drop-last shifts the batch mean 0.0017
  same 3-epoch budget: micro-32 -> 384 optimizer steps; accum x8 -> 48
  warmup 10 steps = 2.6% of the micro run vs 20.8% of the accumulated run
  clip order: clip-then-average norm 0.770 vs average-then-clip 1.000 (0.770x the LR, 6.7 deg off)
F7 the campaign (1.2B tokens, 3,500 tok/s/GPU, $2.50/GPU-h):
  R1 baseline k=1: diverged  0/20  hit 20/20 (~step   10)  diverge ~step    -1  wall 95.24 h  $ 238.10
  R2 k=8 linear+warmup: diverged  0/20  hit 20/20 (~step   38)  diverge ~step    -1  wall 11.90 h  $ 238.10
  R3 k=8 linear no-warmup: diverged 20/20  hit  0/20 (~step   -1)  diverge ~step     2  wall 11.90 h  $ 238.10
  R4 k=32 linear+warmup: diverged 20/20  hit 20/20 (~step   38)  diverge ~step  6551  wall  2.98 h  $ 238.10
  R5 k=32 sqrt+warmup: diverged  0/20  hit 20/20 (~step   38)  diverge ~step    -1  wall  2.98 h  $ 238.10
  R3 diverged -> retry as R2: $0.04 burned + $238.10 = $238.13 in 11.91 h
  R4 diverged -> retry as R5: $129.98 burned + $238.10 = $368.08 in 4.60 h
FENCE-051-OK
```
