---
Document ID: CHEAT-SHEET-072
Title: "CHEAT-SHEET-072: GPU Utilization and the MFU Budget - the Gauge Lie, the Weight-Stream Ladder, and the KV Re-Bind"
Last Updated: 2026-10-14
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'llmops']
---
# CHEAT-SHEET-072: GPU Utilization and the MFU Budget - the Gauge Lie, the Weight-Stream Ladder, and the KV Re-Bind

The census that picked this sheet searched model FLOPs utilization, MFU, GPU utilization, tensor core, SM occupancy, and flops per token across all 569 markdown docs and found the pattern taught everywhere except as an operator page - 153 hits across 61 files, 70 naming GPU utilization, 50 the tensor core, 30 the MFU acronym, three spelling out model flops utilization - while the operator arithmetic returns one hit in the whole catalog: the vLLM chapter's gpu_memory_utilization flag, a different utilization that budgets KV cache, not flops. The CUDA chapter teaches the TFLOPS table, the monitoring chapters alarm at 80% utilization, the serving chapters ship the concurrency flags, and the learning path's capacity estimator carries the only MFU arithmetic in the catalog - account for 50% MFU - each a part, none the operator page for what the gauge actually measures, and the questions that start the moment one fleet serves the 1,090,800-request day of sheet 070 (what does a full gauge earn, when does batching stop buying, what does KV re-bind, what does the rent buy in flops) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 268-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 68-line run sits frozen below, byte-for-byte.

## The Gauge Lie

The utilization gauge counts SMs busy, not flops earned. A 480 TFLOP/s card running decode at batch 1 streams the same 17.18 GB of weights whether the step earns 2.98 TFLOP/s or 480 - the roofline for that step is 0.62% of peak, and the gauge reports 100%. Even at the resident serving batch of 27.68 the weights-only ceiling is 17.18% (82.48 TFLOP/s). The card reports busy while it streams weights at 3.20 TB/s: utilization is what the card is doing, MFU is what you bought - a busy light, not a meter.

```text
F1  the gauge lie
the utilization gauge counts SMs busy - not flops earned:
decode batch  1.0 : gauge 100.00%  roofline 0.62%  (2.98 TFLOP/s)
decode batch 27.68 : gauge 100.00%  roofline 17.18%  (82.48 TFLOP/s)
the card reports busy while it streams weights at 3.20 TB/s -
100% busy can be 0.62% of peak earned
```

## The Weight-Stream Ladder

The ladder sweeps the batch with KV traffic aside. At batch 1 the 5.37 ms step is pure weight streaming - 0.62% earned; every added slot re-reads the same 17.18 GB but computes more against it: 4.97% at 8, 9.93% at 16, 27.32% at 44, 39.74% at 64, 62.09% at 100. The curve crosses the compute line at batch 161.06, where achieved 479.82 meets the 480 peak; past it the card is compute-bound and batch 256 caps at 480.00 = 100.00%. Below the crossover the card is a bandwidth device, and batching cannot turn a bandwidth device into a calculator.

```text
F2  the weight-stream ladder (KV traffic aside)
batch  step ms  TFLOP/s   MFU%
    1     5.37      2.98    0.62%
    8     5.37     23.84    4.97%
   16     5.37     47.68    9.93%
   44     5.37    131.13   27.32%
   64     5.37    190.73   39.74%
  100     5.37    298.02   62.09%
  161     5.37    479.82   99.96%
  256     8.53    480.00  100.00%
the ladder crosses the compute line at batch 161.06 -
below it the card is a bandwidth device, not a calculator
```

## The KV Re-Bind

Then serving's context re-binds the curve. At context 2,304 every resident token drags 131,072 bytes of KV through HBM each step, and the ladder re-binds: the resident batch 27.68 earns 11.56% at a 7.98 ms floor, batch 64 earns 18.70%, 100 earns 22.51%, and 256 - compute-bound at 100.00% in the weights-only ladder - lands at 28.90%. The asymptote is 35.32%: no batch size reaches compute-bound decode at this context. Batch is a lever with a ceiling, and the ceiling is the KV byte times the context.

```text
F3  the KV re-bind at context 2304
batch  step ms  TFLOP/s   MFU%
27.68     7.98     55.49   11.56%
64.00    11.41     89.76   18.70%
100.00    14.81    108.07   22.51%
256.00    29.53    138.72   28.90%
KV traffic re-binds the curve: the asymptote is 35.32% -
no batch size reaches compute-bound decode at this context
```

## The Serving Point

The serving point prices the gap between roofline and engine. Little's law settles the resident decode batch at 4.32 RPS x 256 tok x 25 ms = 27.68. The roofline floor there is 55.49 TFLOP/s = 11.56% MFU at a 7.98 ms step; the canon engine runs 25.00 ms steps for 17.71 TFLOP/s = 3.69%. The 3.13x gap is scheduler, sampling, sync - the MFU budget is where the engine's overhead actually lives, and it is measured off the fleet, not configured from the brochure.

```text
F4  the serving point
resident decode batch = 4.32 RPS x 256 tok x 25 ms = 27.68
roofline floor: 55.49 TFLOP/s at a 7.98 ms step = 11.56% MFU
the canon engine runs 25.00 ms steps: 17.71 TFLOP/s = 3.69%
the 3.13x gap is scheduler, sampling, sync - the MFU budget
is where the engine's overhead actually lives
```

## The Quantization Unlocks

Quantization is the only dial that moves the numbers the gauge sits on. W8A8 halves the weight stream: the resident batch earns 17.42% = 1.51x the fp16 11.56%. KV8 halves the per-token KV byte: the ceiling itself rises from 35.32% to 70.64%, and the resident batch earns 23.12%. Weight quant buys the small-batch end; KV quant raises the ceiling - and context is the third dial, because the KV term scales with it.

```text
F5  the quantization unlocks at the resident batch
fp16 weights + fp16 KV : earned  11.56%
W8A8 weights           : earned  17.42%  (1.51x)
W8A8 + KV8             : earned  23.12%
weight quant buys the small-batch end; KV quant raises the
ceiling itself - the KV8 asymptote is 70.64%, not 35.32%
```

## The Fleet Day in Flops

The warm-pool rent of sheet 070 is a flops claim. The 1,090,800-request day owes 1,090,800 x 2,304 tok x 16 GFLOP = 4.0211e+19 FLOP of useful work against 144 GPU-h x 480 TFLOP/s = 2.4883e+20 FLOP paid - a blended ceiling of 16.16% MFU for the day. Decode is 11.11% of the useful flops; if the whole day ran at the 11.56% decode-batch MFU it would need 201.31 GPU-h = 1.40x the rent. The fleet passes only because prefill rides hotter: it must earn 17.01% to cover the rest. The rent presumes a blended MFU the decode batch alone cannot deliver.

```text
F6  the fleet day in flops
useful  4.0211e+19 FLOP (1090800 requests x 2304 tok x 16 GFLOP)
paid    2.4883e+20 FLOP (144 GPU-h x 480 TFLOP/s)
blended ceiling: the rent buys 16.16% MFU for the day
decode is 11.11% of the useful flops; prefill is the rest
if the whole day ran at the 11.56% decode-batch MFU it would
need 201.31 GPU-h = 1.40x the 144 GPU-h rent - the fleet passes
only because prefill rides hotter: it must earn 17.01%
```

## The Build Ladder and the Ablation Audit

The ladder orders the build and the ablations audit it. Gauge-only is blind: 100.00% reported against 11.56% earned. +roofline makes the gap visible - floor 7.98 ms vs the measured 25.00 ms step; +batch earns the 11.56% at the resident batch; +W8A8 lifts it to 17.42%; +KV8 to 23.12% under the 70.64% ceiling. The ablations hand the deltas back in order: -roofline is blind again, -batch drops to 0.61% at batch 1, -W8A8 back to 11.56%, -KV8 back to 17.42%. Roofline first, batch second, weight-quant third, KV-quant fourth - and the only dial that raises the ceiling is a smaller KV byte or a shorter context.

```text
F7  the build ladder and the ablation audit
gauge-only    100.00% reported /  11.56% earned (blind)
+roofline     the gap visible: floor vs measured step
+batch         11.56% earned at the resident batch
+W8A8          17.42% earned
+KV8           23.12% earned (asymptote 35.32%)
ablations, each handing its delta back:
-roofline  100.00% reported / 11.56% earned - blind again
-batch       0.61% earned at batch 1
-W8A8      back to 11.56%
-KV8       back to 17.42%
order the build: roofline, batch, weight-quant, KV-quant -
and raise the ceiling by shrinking the context or the KV byte

```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| Gauge read as earned capacity | nvidia-smi reports 100% while decode at batch 1 earns 0.62% of peak - the busy light mistaken for a meter (f1) | Convert to MFU - achieved / peak - before buying or selling capacity |
| Batch sized below the crossover | The fleet sits at batch 27.68 where the weights-only ceiling is 17.18% and the KV re-bind is 11.56% (f2, f3) | Batch toward the 161.06 crossover, then re-check KV - the ceiling moves first |
| KV charged as capacity, never as bandwidth | The KV occupies the pool while its traffic hides: a 35.32% asymptote under a full gauge (f3) | Charge the KV term in the roofline: KV bytes per token x context |
| Engine step accepted as physics | The 25.00 ms step earns 3.69% where the roofline floor is 11.56% - a 3.13x gap blamed on hardware (f4) | Measure the gap, attribute it - scheduler, sampling, sync - and shave it |
| W8A8 taken as the whole quant story | Weight quant lifts 11.56% to 17.42% while the ceiling stays 35.32% (f5) | Add KV8 - the asymptote itself doubles to 70.64% |
| Rent stated without a flops claim | 144 GPU-h reads as infinite compute while the day needs 201.31 GPU-h at decode-batch MFU (f6) | State the blended MFU the rent presumes - 16.16% - and who earns the gap: prefill at 17.01% |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| GPU at 100% but tokens/s will not rise | The weight-stream ladder (f2): the batch sits below the 161.06 crossover, bandwidth-bound | Raise the batch - every added slot re-reads the same 17.18 GB against more work |
| Batch raised, throughput still capped | The KV re-bind (f3): at context 2,304 the ceiling is 35.32%, not 100% | Cut the KV byte (KV8) or the context - batch cannot pass the asymptote |
| MFU far below the roofline floor | The serving point (f4): the engine runs 25.00 ms steps against a 7.98 ms floor | Profile the gap - scheduler, sampler, sync - not the kernel |
| Weights quantized, no gain at serving batch | The unlocks (f5): W8A8 buys the small-batch end only | Quantize the KV too - the ceiling itself moves |
| Capacity plan built from peak TFLOPS | The fleet day (f6): the rent buys 16.16% blended while decode earns 11.56% | Plan in earned flops: useful / (MFU x peak x hours) |
| nvidia-smi argues the fleet is underused | The gauge lie (f1): 100% busy at 0.62% earned | Report MFU beside utilization in every capacity review |

## Quick Reference For

- [the CUDA chapter whose TFLOPS table this roofline prices](../../phases/phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Programming.md)
- [the vLLM/TGI chapter whose gpu_memory_utilization flag budgets a different utilization](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [the monitoring chapter whose 80% utilization alarms this sheet turns into MFU](../../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
- [the weight-residency sheet whose card anatomy this fixture shares](../../learning-resources/cheat-sheets/CHEAT-SHEET-068-Multi-Model-Serving-and-the-Weight-Residency-Budget.md)
- [the warm-pool fleet whose 144 GPU-h rent this flops bill prices](../../learning-resources/cheat-sheets/CHEAT-SHEET-070-Autoscaling-and-the-Warm-Pool-Budget.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 268-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the card peak, the bandwidth, the KV anatomy, and the context for your own fleet's, and the ladder re-derives.

```python
"""CHEAT-SHEET-072 canonical fence: GPU utilization and the MFU budget.
Stdlib only, no randomness, no clocks - every printed figure is computed
from the fixed fixture and pinned by an assert. Two runs must print
identical bytes. Roofline arithmetic over the 068/070 serving universe;
no RNG anywhere.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 57

# ---------------------------------------------------------------- fixture
# the 068/070 universe: 16 GiB fp16 weights on a 48 GiB card
CARD_GIB = 48
WEIGHTS_GIB = 16
GIB = 1024 ** 3
W_BYTES = WEIGHTS_GIB * GIB                       # 17.18 GB of fp16 weights
PARAMS = 8e9
FLOPS_PER_TOKEN = 2.0 * PARAMS                    # 16 GFLOP per token

# the fleet card: 48 GiB HBM, 3.20 TB/s, dense fp16 peak 480 TFLOP/s
PEAK_TFLOPS = 480.0
BW_BPS = 3.20e12

# the 068 KV anatomy: 32 layers, 8 GQA heads, head_dim 128, fp16
KV_BYTES_PER_TOKEN = 32 * 8 * 128 * 2 * 2         # 131072 B per KV token
CTX_TOKENS = 2304                                 # 2048 prompt + 256 output

# the 070 fleet: six replicas, the 144 GPU-h rent, the 1,090,800 day
FLEET = 6
RENT_GPUH = 144.0
TOTAL_REQUESTS = 1090800
PROMPT_TOKENS = 2048
OUTPUT_TOKENS = 256
REPLICA_RPS = 32 / 7.4                            # the 068 slot occupancy
STEP_MS = 25.0                                    # the canon engine step

assert W_BYTES == 17179869184
assert FLOPS_PER_TOKEN == 16e9
assert KV_BYTES_PER_TOKEN == 131072
assert CTX_TOKENS == 2304
assert TOTAL_REQUESTS == 1090800
assert KV_BYTES_PER_TOKEN * CTX_TOKENS * 32 <= 32 * GIB


# --------------------------------------------------------------- roofline
def roofline(batch, weight_bytes=W_BYTES,
             kv_per_tok=KV_BYTES_PER_TOKEN, ctx=CTX_TOKENS):
    """Decode step at `batch` resident tokens. Traffic = the weights read
    once per step + batch x context KV reads; compute = batch x 16 GFLOP.
    Returns (step ms, achieved TFLOP/s, MFU %)."""
    mem_s = (weight_bytes + batch * ctx * kv_per_tok) / BW_BPS
    comp_s = batch * FLOPS_PER_TOKEN / (PEAK_TFLOPS * 1e12)
    step_s = max(mem_s, comp_s)
    tflops = batch * FLOPS_PER_TOKEN / step_s / 1e12
    return step_s * 1000.0, tflops, tflops / PEAK_TFLOPS * 100.0


CROSSOVER_B = PEAK_TFLOPS * 1e12 * W_BYTES / (FLOPS_PER_TOKEN * BW_BPS)
KV_ASYMPTOTE_PCT = FLOPS_PER_TOKEN * BW_BPS / (KV_BYTES_PER_TOKEN
                                               * CTX_TOKENS) \
    / (PEAK_TFLOPS * 1e12) * 100.0
B_SERVE = REPLICA_RPS * OUTPUT_TOKENS * STEP_MS / 1000.0

assert abs(CROSSOVER_B - 161.06) < 5e-3
assert abs(KV_ASYMPTOTE_PCT - 35.32) < 5e-3
assert abs(B_SERVE - 27.68) < 5e-3


# ------------------------------------------------- F1  the gauge lie
def f1_gauge_lie():
    ms1, tf1, mfu1 = roofline(1.0, kv_per_tok=0.0)
    msr, tfr, mfur = roofline(B_SERVE, kv_per_tok=0.0)
    lines = [
        "F1  the gauge lie",
        "the utilization gauge counts SMs busy - not flops earned:",
        "decode batch  1.0 : gauge 100.00%%  roofline %.2f%%  (%.2f TFLOP/s)"
        % (mfu1, tf1),
        "decode batch %.2f : gauge 100.00%%  roofline %.2f%%  (%.2f TFLOP/s)"
        % (B_SERVE, mfur, tfr),
        "the card reports busy while it streams weights at %.2f TB/s -"
        % (BW_BPS / 1e12),
        "100%% busy can be %.2f%% of peak earned" % mfu1,
    ]
    assert abs(mfu1 - 0.62) < 5e-3
    assert abs(mfur - 17.18) < 5e-3
    return lines


# ---------------------------------------------- F2  the weight ladder
def f2_weight_ladder():
    lines = [
        "F2  the weight-stream ladder (KV traffic aside)",
        "batch  step ms  TFLOP/s   MFU%",
    ]
    mfu_at = {}
    for b in (1, 8, 16, 44, 64, 100, 161, 256):
        ms, tf, mfu = roofline(b, kv_per_tok=0.0)
        mfu_at[b] = mfu
        lines.append("%5.0f  %7.2f  %8.2f  %6.2f%%" % (b, ms, tf, mfu))
    lines += [
        "the ladder crosses the compute line at batch %.2f -" % CROSSOVER_B,
        "below it the card is a bandwidth device, not a calculator",
    ]
    assert abs(mfu_at[44] - 27.32) < 5e-3
    assert abs(mfu_at[161] - 99.96) < 5e-3
    assert mfu_at[256] == 100.0
    return lines


# --------------------------------------------------- F3  the KV re-bind
def f3_kv_rebind():
    lines = [
        "F3  the KV re-bind at context %d" % CTX_TOKENS,
        "batch  step ms  TFLOP/s   MFU%",
    ]
    mfu_at = {}
    for b in (B_SERVE, 64, 100, 256):
        ms, tf, mfu = roofline(b)
        mfu_at[b] = mfu
        lines.append("%5.2f  %7.2f  %8.2f  %6.2f%%" % (b, ms, tf, mfu))
    lines += [
        "KV traffic re-binds the curve: the asymptote is %.2f%% -"
        % KV_ASYMPTOTE_PCT,
        "no batch size reaches compute-bound decode at this context",
    ]
    assert abs(mfu_at[B_SERVE] - 11.56) < 5e-3
    assert abs(mfu_at[64] - 18.70) < 5e-3
    assert abs(mfu_at[100] - 22.51) < 5e-3
    assert abs(mfu_at[256] - 28.90) < 5e-3
    assert mfu_at[256] < KV_ASYMPTOTE_PCT
    return lines


# ------------------------------------------------- F4  the serving point
def f4_serving_point():
    floor_ms, pot_tf, pot_mfu = roofline(B_SERVE)
    eng_tf = B_SERVE * FLOPS_PER_TOKEN / (STEP_MS / 1000.0) / 1e12
    eng_mfu = eng_tf / PEAK_TFLOPS * 100.0
    lines = [
        "F4  the serving point",
        "resident decode batch = %.2f RPS x %d tok x %.0f ms = %.2f"
        % (REPLICA_RPS, OUTPUT_TOKENS, STEP_MS, B_SERVE),
        "roofline floor: %.2f TFLOP/s at a %.2f ms step = %.2f%% MFU"
        % (pot_tf, floor_ms, pot_mfu),
        "the canon engine runs %.2f ms steps: %.2f TFLOP/s = %.2f%%"
        % (STEP_MS, eng_tf, eng_mfu),
        "the %.2fx gap is scheduler, sampling, sync - the MFU budget"
        % (STEP_MS / floor_ms),
        "is where the engine's overhead actually lives",
    ]
    assert abs(floor_ms - 7.98) < 5e-3
    assert abs(eng_tf - 17.71) < 5e-3
    assert abs(eng_mfu - 3.69) < 5e-3
    assert abs(STEP_MS / floor_ms - 3.13) < 5e-3
    return lines


# ------------------------------------------- F5  the quantization unlocks
def f5_quant_unlocks():
    w8 = W_BYTES / 2.0
    k8 = KV_BYTES_PER_TOKEN / 2.0
    _, _, mfu_fp16 = roofline(B_SERVE)
    _, _, mfu_w8 = roofline(B_SERVE, weight_bytes=w8)
    _, _, mfu_both = roofline(B_SERVE, weight_bytes=w8, kv_per_tok=k8)
    asym8 = FLOPS_PER_TOKEN * BW_BPS / (k8 * CTX_TOKENS) \
        / (PEAK_TFLOPS * 1e12) * 100.0
    lines = [
        "F5  the quantization unlocks at the resident batch",
        "fp16 weights + fp16 KV : earned %6.2f%%" % mfu_fp16,
        "W8A8 weights           : earned %6.2f%%  (%.2fx)"
        % (mfu_w8, mfu_w8 / mfu_fp16),
        "W8A8 + KV8             : earned %6.2f%%" % mfu_both,
        "weight quant buys the small-batch end; KV quant raises the",
        "ceiling itself - the KV8 asymptote is %.2f%%, not %.2f%%"
        % (asym8, KV_ASYMPTOTE_PCT),
    ]
    assert abs(mfu_fp16 - 11.56) < 5e-3
    assert abs(mfu_w8 - 17.42) < 5e-3
    assert abs(mfu_w8 / mfu_fp16 - 1.51) < 5e-3
    assert abs(mfu_both - 23.12) < 5e-3
    assert abs(asym8 - 70.64) < 5e-3
    return lines


# -------------------------------------------- F6  the fleet day in flops
def f6_fleet_day():
    useful = TOTAL_REQUESTS * CTX_TOKENS * FLOPS_PER_TOKEN
    paid = RENT_GPUH * 3600.0 * PEAK_TFLOPS * 1e12
    blended = useful / paid * 100.0
    decode_share = OUTPUT_TOKENS / float(CTX_TOKENS) * 100.0
    _, _, mfu_serve = roofline(B_SERVE)
    gpuh_needed = useful / (mfu_serve / 100.0 * PEAK_TFLOPS * 1e12 * 3600.0)
    decode_gpuh = decode_share / 100.0 * gpuh_needed
    prefill_flops = useful * (1.0 - decode_share / 100.0)
    prefill_mfu_needed = prefill_flops / ((RENT_GPUH - decode_gpuh)
                                          * 3600.0 * PEAK_TFLOPS * 1e12) \
        * 100.0
    lines = [
        "F6  the fleet day in flops",
        "useful  %.4e FLOP (%d requests x %d tok x %.0f GFLOP)"
        % (useful, TOTAL_REQUESTS, CTX_TOKENS, FLOPS_PER_TOKEN / 1e9),
        "paid    %.4e FLOP (%.0f GPU-h x 480 TFLOP/s)" % (paid, RENT_GPUH),
        "blended ceiling: the rent buys %.2f%% MFU for the day" % blended,
        "decode is %.2f%% of the useful flops; prefill is the rest"
        % decode_share,
        "if the whole day ran at the %.2f%% decode-batch MFU it would"
        % mfu_serve,
        "need %.2f GPU-h = %.2fx the 144 GPU-h rent - the fleet passes"
        % (gpuh_needed, gpuh_needed / RENT_GPUH),
        "only because prefill rides hotter: it must earn %.2f%%"
        % prefill_mfu_needed,
    ]
    assert abs(useful - 4.0211e19) < 1e16
    assert abs(paid - 2.4883e20) < 1e17
    assert abs(blended - 16.16) < 5e-3
    assert abs(decode_share - 11.11) < 5e-3
    assert abs(gpuh_needed - 201.31) < 5e-3
    assert abs(gpuh_needed / RENT_GPUH - 1.40) < 5e-3
    assert abs(prefill_mfu_needed - 17.01) < 5e-3
    return lines


# ------------------------------------- F7  the build ladder and the audit
def f7_build_ladder():
    _, _, mfu_b1 = roofline(1.0)
    _, _, mfu_serve = roofline(B_SERVE)
    w8 = W_BYTES / 2.0
    k8 = KV_BYTES_PER_TOKEN / 2.0
    _, _, mfu_w8 = roofline(B_SERVE, weight_bytes=w8)
    _, _, mfu_both = roofline(B_SERVE, weight_bytes=w8, kv_per_tok=k8)
    lines = [
        "F7  the build ladder and the ablation audit",
        "gauge-only    100.00%% reported / %6.2f%% earned (blind)"
        % mfu_serve,
        "+roofline     the gap visible: floor vs measured step",
        "+batch        %6.2f%% earned at the resident batch" % mfu_serve,
        "+W8A8         %6.2f%% earned" % mfu_w8,
        "+KV8          %6.2f%% earned (asymptote %.2f%%)"
        % (mfu_both, KV_ASYMPTOTE_PCT),
        "ablations, each handing its delta back:",
        "-roofline  100.00%% reported / %.2f%% earned - blind again"
        % mfu_serve,
        "-batch     %6.2f%% earned at batch 1" % mfu_b1,
        "-W8A8      back to %.2f%%" % mfu_serve,
        "-KV8       back to %.2f%%" % mfu_w8,
        "order the build: roofline, batch, weight-quant, KV-quant -",
        "and raise the ceiling by shrinking the context or the KV byte",
    ]
    assert abs(mfu_b1 - 0.61) < 5e-3
    assert abs(mfu_serve - 11.56) < 5e-3
    assert abs(mfu_w8 - 17.42) < 5e-3
    assert abs(mfu_both - 23.12) < 5e-3
    return lines


exhibits = [
    f1_gauge_lie, f2_weight_ladder, f3_kv_rebind, f4_serving_point,
    f5_quant_unlocks, f6_fleet_day, f7_build_ladder,
]
for fn in exhibits:
    print(RULE)
    for line in fn():
        print(line)

print()
print("FENCE-072-OK")
```

```text
=========================================================
F1  the gauge lie
the utilization gauge counts SMs busy - not flops earned:
decode batch  1.0 : gauge 100.00%  roofline 0.62%  (2.98 TFLOP/s)
decode batch 27.68 : gauge 100.00%  roofline 17.18%  (82.48 TFLOP/s)
the card reports busy while it streams weights at 3.20 TB/s -
100% busy can be 0.62% of peak earned
=========================================================
F2  the weight-stream ladder (KV traffic aside)
batch  step ms  TFLOP/s   MFU%
    1     5.37      2.98    0.62%
    8     5.37     23.84    4.97%
   16     5.37     47.68    9.93%
   44     5.37    131.13   27.32%
   64     5.37    190.73   39.74%
  100     5.37    298.02   62.09%
  161     5.37    479.82   99.96%
  256     8.53    480.00  100.00%
the ladder crosses the compute line at batch 161.06 -
below it the card is a bandwidth device, not a calculator
=========================================================
F3  the KV re-bind at context 2304
batch  step ms  TFLOP/s   MFU%
27.68     7.98     55.49   11.56%
64.00    11.41     89.76   18.70%
100.00    14.81    108.07   22.51%
256.00    29.53    138.72   28.90%
KV traffic re-binds the curve: the asymptote is 35.32% -
no batch size reaches compute-bound decode at this context
=========================================================
F4  the serving point
resident decode batch = 4.32 RPS x 256 tok x 25 ms = 27.68
roofline floor: 55.49 TFLOP/s at a 7.98 ms step = 11.56% MFU
the canon engine runs 25.00 ms steps: 17.71 TFLOP/s = 3.69%
the 3.13x gap is scheduler, sampling, sync - the MFU budget
is where the engine's overhead actually lives
=========================================================
F5  the quantization unlocks at the resident batch
fp16 weights + fp16 KV : earned  11.56%
W8A8 weights           : earned  17.42%  (1.51x)
W8A8 + KV8             : earned  23.12%
weight quant buys the small-batch end; KV quant raises the
ceiling itself - the KV8 asymptote is 70.64%, not 35.32%
=========================================================
F6  the fleet day in flops
useful  4.0211e+19 FLOP (1090800 requests x 2304 tok x 16 GFLOP)
paid    2.4883e+20 FLOP (144 GPU-h x 480 TFLOP/s)
blended ceiling: the rent buys 16.16% MFU for the day
decode is 11.11% of the useful flops; prefill is the rest
if the whole day ran at the 11.56% decode-batch MFU it would
need 201.31 GPU-h = 1.40x the 144 GPU-h rent - the fleet passes
only because prefill rides hotter: it must earn 17.01%
=========================================================
F7  the build ladder and the ablation audit
gauge-only    100.00% reported /  11.56% earned (blind)
+roofline     the gap visible: floor vs measured step
+batch         11.56% earned at the resident batch
+W8A8          17.42% earned
+KV8           23.12% earned (asymptote 35.32%)
ablations, each handing its delta back:
-roofline  100.00% reported / 11.56% earned - blind again
-batch       0.61% earned at batch 1
-W8A8      back to 11.56%
-KV8       back to 17.42%
order the build: roofline, batch, weight-quant, KV-quant -
and raise the ceiling by shrinking the context or the KV byte

FENCE-072-OK
```
