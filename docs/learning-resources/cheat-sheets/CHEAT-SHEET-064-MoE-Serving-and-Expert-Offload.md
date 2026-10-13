---
Document ID: CHEAT-SHEET-064
Title: "CHEAT-SHEET-064: MoE Serving and Expert Offload - the Capacity Bill, the Residency Gate, and the Quantization Flip"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'distributed']
---
# CHEAT-SHEET-064: MoE Serving and Expert Offload - the Capacity Bill, the Residency Gate, and the Quantization Flip

The census that picked this sheet searched expert parallelism, expert offload, and MoE serving across all 564 markdown docs and found the serving pattern in three aside lines - the router note inside the template module's MoE comment, the SGLang expert-parallel pin note in the SGLang section, and one trade-off line - while capacity factor, auxiliary loss, grouped GEMM, and expert-offload arithmetic return zero. The parts live apart: the activations course teaches the gating lineage, the attention course carries DeepSeek-V3's shared-expert MLA, phase4 holds the Mixtral tables, and the serving chapters carry the engine rows - each a part, none the operator page - and the questions that start the moment a 40B MoE has to live inside an 80 GB card (what does a spilled expert cost per token, what does a batch amortize, what flips residency, what order do you build the levers) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 275-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 64-line run sits frozen below, byte-for-byte.

## The Capacity Bill

The bill every MoE quote starts from. The 40B stack is 80 GB in fp16 on a card that also owes 20 GB of KV, so a dense serving streams all of it every token: 25.00 ms, 40.0 tok/s. Top-2 routing leaves 9.0B active - an 18 GB stream, 5.62 ms, 177.8 tok/s - the capacity bill pays 4.44x tokens/s on 22.5% of the parameters, if every picked expert is resident.

```text
F1 | THE CAPACITY BILL
  params: trunk 8.0B + 64 experts x 0.5B (top-2) = 40.0B total
  active per token: 8.0B + 2 x 0.5B = 9.0B (22.5% of total)
  fp16 weights: trunk 16 GB + experts 64 GB = 80 GB on an 80 GB card owing 20 GB of KV
  dense-40B stream: 80 GB/token = 25.00 ms -> 40.0 tok/s
  moe ideal stream:  18 GB/token = 5.62 ms -> 177.8 tok/s
  capacity bill:     4.44x tokens/s, paid on 22.5% of the params
  -> MoE buys capacity and pays bandwidth only on the active slice - if every picked expert is resident
```

## The Residency Bill

It is not, and the pick histogram decides the tax. The 200-pick decode concentrates: top-4 experts take 27%, top-16 62%, top-40 86%. Keeping 40 experts resident fills the card - 76 GB of the 80 with trunk and KV - and the 28 spilled picks cost 20.0 ms each over DRAM, 5.60 ms/token. fp16 decode lands at 11.14 ms, 89.8 tok/s: the 4.44x ideal pays out at 2.24x, half the multiplier spent buying spilled experts back.

```text
F2 | THE RESIDENCY BILL
  fixed histogram: top-4 27%, top-16 62%, top-40 86% of picks
  resident: 40 experts (40 GB) + trunk 16 GB + KV 20 GB = 76 GB of the 80 GB card
  spill: 28 of 200 picks fetch 1 GB back over DRAM at 50 GB/s = 20.0 ms each = 5.60 ms/token
  hbm stream: trunk 16 + 1.72 resident picks = 17.72 GB/token = 5.54 ms
  fp16 decode: 11.14 ms/token -> 89.8 tok/s = 2.24x dense
  -> the 4.44x capacity bill pays out at 2.24x - half the multiplier is spent buying spilled experts back
```

## The Quantization Gate

The gate that retires offload. int4 experts are 0.25 GB each - all 64 fit in 16 GB, 32 GB with the fp16 trunk, 28 GB spare past KV, spill zero. Decode drops to 5.16 ms, 193.9 tok/s = 4.85x dense; flipping the trunk to fp8 halves it again to 2.66 ms, 376.5 tok/s = 9.41x shipped. The quality gate holds: hot-expert int4 KL drift 0.9% against a 2% line, the router kept at fp16 - quantization is a residency flip, and offload is an fp16 problem.

```text
F3 | THE QUANTIZATION GATE
  experts at int4: 0.25 GB each -> all 64 resident in 16 GB (32 GB with the fp16 trunk; 28 GB spare past KV)
  spill: 0 of 200 picks
  int4 decode: 16.5 GB/token = 5.16 ms -> 193.9 tok/s = 4.85x dense
  trunk at fp8: 8 GB -> 8.5 GB/token = 2.66 ms -> 376.5 tok/s = 9.41x dense
  quality gate: hot-expert int4 KL drift 0.9% < 2% gate; the router stays fp16
  -> quantization flips residency: offload is an fp16 problem - the 4.44x ideal became 9.41x shipped
```

## The Batch Dispatch Bill

Batch turns per-token cost into per-step cost. B=1 wakes 2 experts and streams 8.50 GB for one token; B=64 wakes 39 and amortizes the stream 30.6x with the step at 5.55 ms; B=256 amortizes 96.7x; B=1024 wakes all 64 - the U(B) ceiling - at 0.0234 GB/token, 362.7x. The price is the step the slowest user waits on: 5.55 ms at B=64 grows to 7.50 ms at B=1024 - batch until the SLA line, not past it.

```text
F4 | THE BATCH DISPATCH BILL
  batch B wakes U(B) of 64 experts; weight stream per token = (8 + 0.25 x U(B)) / B GB
  B=1     U=2    8.50 GB/step -> 8.5000 GB/token
  B=64    U=39  17.75 GB/step -> 0.2773 GB/token (30.6x amortized)
  B=256   U=58  22.50 GB/step -> 0.0879 GB/token (96.7x amortized)
  B=1024  U=64  24.00 GB/step -> 0.0234 GB/token (362.7x amortized)
  step latency: 5.55 ms at B=64, 7.50 ms at B=1024 - the slowest stream is the step
  -> batch amortizes the expert stream toward the U(B) ceiling - past it B only buys throughput, and the step the slowest user waits on grows
```

## The Shared-Expert Lever

The lever that works while the model is still offload-bound. One always-on shared expert plus rebalanced routing flattens the histogram: top-40 coverage moves 86% to 92%, spill 28 to 16 picks, the spill bill 5.60 to 3.20 ms/token - fp16 decode lands 9.09 ms, 110.0 tok/s, +22.6% for 1 GB of rent. It buys residency headroom, not FLOPs - and the int4 flip retires it.

```text
F5 | THE SHARED-EXPERT LEVER
  +1 shared expert (1 GB fp16, every token) flattens the histogram: top-40 86% -> 92% of picks
  spill: 28 -> 16 picks; spill bill 5.60 -> 3.20 ms/token
  stream: 17.72 -> 18.84 GB/token (trunk + picks + shared) = 5.89 ms
  fp16 decode: 11.14 -> 9.09 ms/token -> 110.0 tok/s (+22.6%)
  -> in the offload-bound world the shared expert buys residency headroom, not FLOPs - it pays rent until the int4 flip retires it
```

## The Serving Ladder

The ladder the exhibits stacked: dense 25.00 -> fp16 with spill 11.14 -> int4 experts 5.16 -> fp8 trunk 2.66 ms/token, 9.41x the dense baseline on the same 80 GB card. Three levers, each owning exactly one cost - residency, expert precision, trunk precision - and each additive because they are disjoint.

```text
F6 | THE SERVING LADDER
  dense-40B fp16     25.00 ms/token (  40.0 tok/s)
  moe fp16 + spill   11.14 ms/token (  89.8 tok/s)  <- 2.24x dense
  int4 experts        5.16 ms/token ( 193.9 tok/s)  <- 4.85x dense
  +fp8 trunk          2.66 ms/token ( 376.5 tok/s)  <- 9.41x dense
  final stack: 2.66 ms/token = 9.41x the dense baseline on one 80 GB card
  -> three levers moved the token line 25.00 -> 2.66 ms; each owns one cost - residency, expert precision, trunk precision
```

## The Ablation Audit

Removal audit on the 9.41x stack: -fp8 trunk lands 4.85x (-4.56 of the multiplier), -expert int4 lands 2.24x (-7.17), -residency 40->16 lands 1.21x (-8.20). All three single removals give back more than 4.5x; none is a rounding error - the deltas order the build: residency planning first, expert quantization second, trunk precision third.

```text
F7 | THE ABLATION AUDIT
  -fp8 trunk           back to  5.16 ms/token - 4.85x dense (-4.56 of the multiplier)
  -expert int4         back to 11.14 ms/token - 2.24x dense (-7.17 of the multiplier)
  -residency 40 -> 16  back to 20.59 ms/token - 1.21x dense (-8.20 of the multiplier)
  3 of 3 single removals give back more than 4.5x; the deltas order the build: residency planning first, expert quantization second, trunk precision third
  -> no single rung carries the 9.41x - the residency plan is the biggest rung and the cheapest rung to lose
```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| Under-provisioned resident set | The router picks a spilled expert mid-generation; a DRAM fetch stalls the step (f2) | Size residency from the pick histogram, not the param count: top-N experts + trunk + KV must fit under the card |
| fp16 experts under offload | The 2.24x payout on a 4.44x bill; the spill line dominates decode (f2) | Treat offload as an fp16 problem - int4 experts flip residency before any hardware is added |
| int4-everything quality drop | Output drifts past tolerance and nobody pinned which weights moved (f3) | Gate on KL drift over hot experts against a 2% line; the router stays fp16 |
| Oversized batch | Aggregate tok/s climbs while per-user step latency climbs with it (f4) | Amortize until the SLA line - 5.55 ms at B=64 grows to 7.50 ms at B=1024 - not past it |
| Shared expert kept after the flip | 1 GB of rent per token with no residency gain once every expert is resident (f5) | Retire the shared expert when expert quantization makes the whole router resident |
| Hot-cold expert skew untracked | A few experts take most picks; a residency plan built on uniform traffic starves (f2) | Track the histogram: top-4 at 27% here means a flat residency plan is wrong before it is built |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| tok/s stuck at the fp16 number with experts nominally loaded | Count DRAM fetches per token (f2); list which experts are resident vs picked | Re-plan residency from the top-N histogram - the spill is 20 ms per spilled pick at DRAM bandwidth |
| 9.41x promised, measured near 4.85x | Expert dtype actually int4? Trunk dtype? (f3) | The fp8 trunk is a separate rung - 8 GB fp8 vs 16 GB fp16 is the missing delta |
| Quality regression after expert quantization | KL drift per hot expert vs the gate; router dtype (f3) | Keep the 2% KL gate and the fp16 router; quantize the experts that run hot |
| Step latency up at high concurrency | Awake experts U(B) vs batch size (f4) | Cap batch at the U(B) ceiling and the SLA line - past the ceiling batch adds latency, not coverage |
| The +22.6% shared-expert gain does not appear | Did the histogram flatten? Recount spill picks (f5) | The lever is residency headroom: re-measure top-40 coverage (86% to 92%) before crediting FLOPs |
| Ladder rungs refuse to compose | Run each ablation alone (f7) | Each rung owns exactly one cost - residency, expert precision, trunk precision; a rung touching two costs is misbuilt |

## Quick Reference For

- [the gating and router-math lineage (Shazeer to Switch to Mixtral)](../../phases/phase3-transformers/3300-decoding/3301-Activation-Functions.md)
- [DeepSeek-V3's shared-expert MLA, the trunk-side cousin](../../phases/phase3-transformers/3400-architectures/3404-Beyond-Attention-SSMs-and-MLA.md)
- [Mixtral and the KV bill the trunk owes](../../phases/phase4-quantization/4200-kv-cache/guides/4203-Context-Window-Optimization.md)
- [MXFP4 expert quantization, the int4 rung's production form](../../phases/phase4-quantization/4100-low-bit/4104-MXFP4-and-NVFP4.md)
- [vLLM and TGI, the serving surface MoE lands on](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 275-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the histogram for your own router logs, and the bills re-derive.

```python
"""CHEAT-SHEET-064: MoE Serving and Expert Offload - the Capacity
Bill, the Residency Gate, and the Quantization Flip.

Fixture: one 40B-parameter MoE - an 8B dense trunk carrying 64 routed
experts of 0.5B each, top-2 routing. fp16 = 2 bytes/param: the trunk is
16 GB, the experts 64 GB, 80 GB of weights on an 80 GB HBM card that
also owes a 20 GB KV budget. HBM streams 3,200 GB/s; a spilled expert
returns over DRAM at 50 GB/s. The decode fixture is 100 tokens x top-2
= 200 expert picks on a fixed histogram. All numbers below are fixture
constants or arithmetic on them - no RNG, no wall clock, two runs
print the same bytes.
"""
# ---------------------------------------------------------------- fixtures
EXPERTS = 64
TOP_K = 2
EXPERT_PARAMS = 0.5e9
TRUNK_PARAMS = 8.0e9
TOTAL = TRUNK_PARAMS + EXPERTS * EXPERT_PARAMS
ACTIVE = TRUNK_PARAMS + TOP_K * EXPERT_PARAMS
HBM_BW = 3200.0        # GB/s weight streaming on the card
DRAM_BW = 50.0         # GB/s spilled-expert fetch
HBM_GB = 80.0
KV_GB = 20.0
TOKENS = 100
PICKS = TOKENS * TOP_K
RULE = "=" * 64        # exhibit separator; the sheet slices the run on it

EXP_GB = EXPERT_PARAMS * 2 / 1e9     # fp16 bytes per expert, GB
TRUNK_GB = TRUNK_PARAMS * 2 / 1e9
TOT_GB = TOTAL * 2 / 1e9
ACT_GB = ACTIVE * 2 / 1e9
assert (EXP_GB, TRUNK_GB, TOT_GB, ACT_GB) == (1.0, 16.0, 80.0, 18.0)

# fixed pick histogram, Zipf-shaped: how often each expert is picked
HIST = ([18, 14, 12, 10, 9, 8, 7, 7, 6, 6, 5, 5, 5, 4, 4, 4]
        + [2] * 16 + [2] * 8 + [2] * 4 + [1] * 20)
assert len(HIST) == EXPERTS and sum(HIST) == PICKS
assert all(HIST[i] >= HIST[i + 1] for i in range(EXPERTS - 1))

dense_ms = TOT_GB / HBM_BW * 1000.0
ideal_ms = ACT_GB / HBM_BW * 1000.0
ideal_tps = 1000.0 / ideal_ms
ideal_mult = dense_ms / ideal_ms
assert dense_ms == 25.0 and ideal_ms == 5.625
assert abs(ideal_tps - 177.8) < 0.05
assert abs(ideal_mult - 4.4444) < 0.0005

print(RULE)
print("F1 | THE CAPACITY BILL")
print("  params: trunk 8.0B + %d experts x 0.5B (top-2) = 40.0B total"
      % EXPERTS)
print("  active per token: 8.0B + %d x 0.5B = 9.0B (%.1f%% of total)"
      % (TOP_K, 100.0 * ACTIVE / TOTAL))
print("  fp16 weights: trunk %s GB + experts %s GB = %s GB on an %s GB "
      "card owing %s GB of KV"
      % (format(TRUNK_GB, ".0f"), format(EXPERTS * EXP_GB, ".0f"),
         format(TOT_GB, ".0f"), format(HBM_GB, ".0f"),
         format(KV_GB, ".0f")))
print("  dense-40B stream: %s GB/token = %.2f ms -> %.1f tok/s"
      % (format(TOT_GB, ".0f"), dense_ms, 1000.0 / dense_ms))
print("  moe ideal stream:  %s GB/token = %.2f ms -> %.1f tok/s"
      % (format(ACT_GB, ".0f"), ideal_ms, ideal_tps))
print("  capacity bill:     %.2fx tokens/s, paid on %.1f%% of the params"
      % (ideal_mult, 100.0 * ACTIVE / TOTAL))
print("  -> MoE buys capacity and pays bandwidth only on the active slice "
      "- if every picked expert is resident")

# ---------------------------------------------------------------- F2
N_RESIDENT = 40
resident_picks = sum(HIST[:N_RESIDENT])
spill_picks = PICKS - resident_picks
assert (resident_picks, spill_picks) == (172, 28)
dram_ms = EXP_GB / DRAM_BW * 1000.0
assert dram_ms == 20.0
spill_per_tok = spill_picks / TOKENS * dram_ms
e_resident = resident_picks / TOKENS
stream_gb = TRUNK_GB + e_resident * EXP_GB
hbm_ms = stream_gb / HBM_BW * 1000.0
fp16_ms = hbm_ms + spill_per_tok
fp16_tps = 1000.0 / fp16_ms
fp16_mult = dense_ms / fp16_ms
assert abs(spill_per_tok - 5.6) < 1e-9
assert abs(fp16_ms - 11.1375) < 1e-9
assert abs(fp16_mult - 2.2445) < 0.0005
lost = 1.0 - fp16_mult / ideal_mult
assert 0.45 < lost < 0.55

print()
print(RULE)
print("F2 | THE RESIDENCY BILL")
print("  fixed histogram: top-4 %d%%, top-16 %d%%, top-%d %d%% of picks"
      % (100 * sum(HIST[:4]) // PICKS, 100 * sum(HIST[:16]) // PICKS,
         N_RESIDENT, 100 * resident_picks // PICKS))
print("  resident: %d experts (%s GB) + trunk %s GB + KV %s GB = %s GB of "
      "the %s GB card"
      % (N_RESIDENT, format(N_RESIDENT * EXP_GB, ".0f"),
         format(TRUNK_GB, ".0f"), format(KV_GB, ".0f"),
         format(N_RESIDENT * EXP_GB + TRUNK_GB + KV_GB, ".0f"),
         format(HBM_GB, ".0f")))
print("  spill: %d of %d picks fetch %s GB back over DRAM at %s GB/s = "
      "%.1f ms each = %.2f ms/token"
      % (spill_picks, PICKS, format(EXP_GB, ".0f"),
         format(DRAM_BW, ".0f"), dram_ms, spill_per_tok))
print("  hbm stream: trunk %s + %.2f resident picks = %.2f GB/token = "
      "%.2f ms" % (format(TRUNK_GB, ".0f"), e_resident, stream_gb, hbm_ms))
print("  fp16 decode: %.2f ms/token -> %.1f tok/s = %.2fx dense"
      % (fp16_ms, fp16_tps, fp16_mult))
print("  -> the 4.44x capacity bill pays out at 2.24x - half the "
      "multiplier is spent buying spilled experts back")

# ---------------------------------------------------------------- F3
EXP_GB_Q4 = EXP_GB / 4.0        # int4 experts
TRUNK_GB_Q8 = TRUNK_GB / 2.0    # fp8 trunk
assert EXP_GB_Q4 == 0.25 and TRUNK_GB_Q8 == 8.0
resident_q4 = TRUNK_GB + EXPERTS * EXP_GB_Q4
assert resident_q4 == 32.0 and resident_q4 + KV_GB <= HBM_GB
spare = HBM_GB - resident_q4 - KV_GB
assert spare == 28.0
q4_ms = (TRUNK_GB + TOP_K * EXP_GB_Q4) / HBM_BW * 1000.0
q4_tps = 1000.0 / q4_ms
q4_mult = dense_ms / q4_ms
fp8_ms = (TRUNK_GB_Q8 + TOP_K * EXP_GB_Q4) / HBM_BW * 1000.0
fp8_tps = 1000.0 / fp8_ms
fp8_mult = dense_ms / fp8_ms
assert abs(q4_ms - 5.15625) < 1e-9 and abs(q4_mult - 4.8485) < 0.0005
assert abs(fp8_ms - 2.65625) < 1e-9 and abs(fp8_mult - 9.4118) < 0.0005
KL_DRIFT = 0.9
KL_GATE = 2.0
assert KL_DRIFT < KL_GATE

print()
print(RULE)
print("F3 | THE QUANTIZATION GATE")
print("  experts at int4: %s GB each -> all %d resident in %s GB (%s GB "
      "with the fp16 trunk; %s GB spare past KV)"
      % (format(EXP_GB_Q4, ".2f"), EXPERTS,
         format(EXPERTS * EXP_GB_Q4, ".0f"), format(resident_q4, ".0f"),
         format(spare, ".0f")))
print("  spill: 0 of %d picks" % PICKS)
print("  int4 decode: %s GB/token = %.2f ms -> %.1f tok/s = %.2fx dense"
      % (format(TRUNK_GB + TOP_K * EXP_GB_Q4, ".1f"), q4_ms, q4_tps,
         q4_mult))
print("  trunk at fp8: %s GB -> %s GB/token = %.2f ms -> %.1f tok/s = "
      "%.2fx dense"
      % (format(TRUNK_GB_Q8, ".0f"),
         format(TRUNK_GB_Q8 + TOP_K * EXP_GB_Q4, ".1f"),
         fp8_ms, fp8_tps, fp8_mult))
print("  quality gate: hot-expert int4 KL drift %.1f%% < %.0f%% gate; the "
      "router stays fp16" % (KL_DRIFT, KL_GATE))
print("  -> quantization flips residency: offload is an fp16 problem - "
      "the 4.44x ideal became 9.41x shipped")

# ---------------------------------------------------------------- F4
UTAB = [(1, 2), (8, 11), (32, 27), (64, 39), (128, 50), (256, 58),
        (512, 63), (1024, 64)]
assert UTAB[0][1] == TOP_K and UTAB[-1][1] == EXPERTS
assert all(u2 > u1 for (_, u1), (_, u2) in zip(UTAB, UTAB[1:]))
base_ptok = (TRUNK_GB_Q8 + TOP_K * EXP_GB_Q4) / 1.0
assert base_ptok == 8.5
ptoks = [(TRUNK_GB_Q8 + u * EXP_GB_Q4) / b for b, u in UTAB]
assert all(x > y for x, y in zip(ptoks, ptoks[1:]))

print()
print(RULE)
print("F4 | THE BATCH DISPATCH BILL")
print("  batch B wakes U(B) of %d experts; weight stream per token = "
      "(%s + %s x U(B)) / B GB"
      % (EXPERTS, format(TRUNK_GB_Q8, ".0f"), format(EXP_GB_Q4, ".2f")))
for b, u in (UTAB[0], UTAB[3], UTAB[5], UTAB[7]):
    step_gb = TRUNK_GB_Q8 + u * EXP_GB_Q4
    ptok = step_gb / b
    line = ("  B=%-5d U=%-3d %5.2f GB/step -> %.4f GB/token"
            % (b, u, step_gb, ptok))
    if b > 1:
        line += " (%.1fx amortized)" % (base_ptok / ptok)
    print(line)
print("  step latency: %.2f ms at B=%d, %.2f ms at B=%d - the slowest "
      "stream is the step"
      % ((TRUNK_GB_Q8 + UTAB[3][1] * EXP_GB_Q4) / HBM_BW * 1000.0,
         UTAB[3][0],
         (TRUNK_GB_Q8 + UTAB[7][1] * EXP_GB_Q4) / HBM_BW * 1000.0,
         UTAB[7][0]))
print("  -> batch amortizes the expert stream toward the U(B) ceiling - "
      "past it B only buys throughput, and the step the slowest user "
      "waits on grows")

# ---------------------------------------------------------------- F5
# one always-on shared expert + rebalanced routing flattens the histogram
HIST2 = ([16, 13, 11, 10, 9, 8, 7, 7, 6, 6, 5, 5, 5, 5, 4, 4]
         + [3] * 15 + [2] + [2] * 8 + [1] * 16 + [0] * 8)
assert len(HIST2) == EXPERTS and sum(HIST2) == PICKS
assert all(HIST2[i] >= HIST2[i + 1] for i in range(EXPERTS - 1))
SHARED_GB = EXP_GB     # 1 GB fp16, every token
res2 = sum(HIST2[:N_RESIDENT])
spill2 = PICKS - res2
assert (res2, spill2) == (184, 16)
e2 = res2 / TOKENS
stream2 = TRUNK_GB + e2 * EXP_GB + SHARED_GB
hbm2_ms = stream2 / HBM_BW * 1000.0
spill2_ms = spill2 / TOKENS * dram_ms
sh_ms = hbm2_ms + spill2_ms
sh_tps = 1000.0 / sh_ms
gain_pct = (sh_tps / fp16_tps - 1.0) * 100.0
assert abs(sh_ms - 9.0875) < 1e-9
assert abs(sh_tps - 110.0) < 0.05
assert abs(gain_pct - 22.6) < 0.05

print()
print(RULE)
print("F5 | THE SHARED-EXPERT LEVER")
print("  +1 shared expert (%s GB fp16, every token) flattens the "
      "histogram: top-%d %d%% -> %d%% of picks"
      % (format(SHARED_GB, ".0f"), N_RESIDENT,
         100 * resident_picks // PICKS, 100 * res2 // PICKS))
print("  spill: %d -> %d picks; spill bill %.2f -> %.2f ms/token"
      % (spill_picks, spill2, spill_per_tok, spill2_ms))
print("  stream: %.2f -> %.2f GB/token (trunk + picks + shared) = %.2f ms"
      % (stream_gb, stream2, hbm2_ms))
print("  fp16 decode: %.2f -> %.2f ms/token -> %.1f tok/s (+%.1f%%)"
      % (fp16_ms, sh_ms, sh_tps, gain_pct))
print("  -> in the offload-bound world the shared expert buys residency "
      "headroom, not FLOPs - it pays rent until the int4 flip retires it")

# ---------------------------------------------------------------- F6
LADDER = [("dense-40B fp16", dense_ms),
          ("moe fp16 + spill", fp16_ms),
          ("int4 experts", q4_ms),
          ("+fp8 trunk", fp8_ms)]
assert ["%.2f" % ms for _, ms in LADDER] ==     ["25.00", "11.14", "5.16", "2.66"], LADDER

print()
print(RULE)
print("F6 | THE SERVING LADDER")
for name, ms in LADDER:
    tail = "" if name == "dense-40B fp16" \
        else "  <- %.2fx dense" % (dense_ms / ms)
    print("  %-18s %5.2f ms/token (%6.1f tok/s)%s"
          % (name, ms, 1000.0 / ms, tail))
print("  final stack: %.2f ms/token = %.2fx the dense baseline on one "
      "%s GB card" % (fp8_ms, fp8_mult, format(HBM_GB, ".0f")))
print("  -> three levers moved the token line 25.00 -> 2.66 ms; each "
      "owns one cost - residency, expert precision, trunk precision")

# ---------------------------------------------------------------- F7
RES16 = 16
res16_picks = sum(HIST[:RES16])
spill16 = PICKS - res16_picks
assert (res16_picks, spill16) == (124, 76)
res16_ms = ((TRUNK_GB + res16_picks / TOKENS * EXP_GB)
            / HBM_BW * 1000.0 + spill16 / TOKENS * dram_ms)
assert abs(res16_ms - 20.5875) < 1e-9
res16_mult = dense_ms / res16_ms

ABL = [("fp8 trunk", q4_ms, q4_mult),
       ("expert int4", fp16_ms, fp16_mult),
       ("residency 40 -> 16", res16_ms, res16_mult)]
losses = [(n, fp8_mult - m) for n, _, m in ABL]
assert all(l > 4.5 for _, l in losses), losses
order = sorted(losses, key=lambda t: -t[1])
assert [n for n, _ in order] == ["residency 40 -> 16", "expert int4",
                                 "fp8 trunk"], order

print()
print(RULE)
print("F7 | THE ABLATION AUDIT")
for (name, ms, mult), (_, loss) in zip(ABL, losses):
    print("  -%-19s back to %5.2f ms/token - %.2fx dense (-%.2f of the "
          "multiplier)" % (name, ms, mult, loss))
print("  3 of 3 single removals give back more than 4.5x; the deltas "
      "order the build: residency planning first, expert quantization "
      "second, trunk precision third")
print("  -> no single rung carries the 9.41x - the residency plan is "
      "the biggest rung and the cheapest rung to lose")
print()
print("FENCE-064-OK")
```

```text
================================================================
F1 | THE CAPACITY BILL
  params: trunk 8.0B + 64 experts x 0.5B (top-2) = 40.0B total
  active per token: 8.0B + 2 x 0.5B = 9.0B (22.5% of total)
  fp16 weights: trunk 16 GB + experts 64 GB = 80 GB on an 80 GB card owing 20 GB of KV
  dense-40B stream: 80 GB/token = 25.00 ms -> 40.0 tok/s
  moe ideal stream:  18 GB/token = 5.62 ms -> 177.8 tok/s
  capacity bill:     4.44x tokens/s, paid on 22.5% of the params
  -> MoE buys capacity and pays bandwidth only on the active slice - if every picked expert is resident

================================================================
F2 | THE RESIDENCY BILL
  fixed histogram: top-4 27%, top-16 62%, top-40 86% of picks
  resident: 40 experts (40 GB) + trunk 16 GB + KV 20 GB = 76 GB of the 80 GB card
  spill: 28 of 200 picks fetch 1 GB back over DRAM at 50 GB/s = 20.0 ms each = 5.60 ms/token
  hbm stream: trunk 16 + 1.72 resident picks = 17.72 GB/token = 5.54 ms
  fp16 decode: 11.14 ms/token -> 89.8 tok/s = 2.24x dense
  -> the 4.44x capacity bill pays out at 2.24x - half the multiplier is spent buying spilled experts back

================================================================
F3 | THE QUANTIZATION GATE
  experts at int4: 0.25 GB each -> all 64 resident in 16 GB (32 GB with the fp16 trunk; 28 GB spare past KV)
  spill: 0 of 200 picks
  int4 decode: 16.5 GB/token = 5.16 ms -> 193.9 tok/s = 4.85x dense
  trunk at fp8: 8 GB -> 8.5 GB/token = 2.66 ms -> 376.5 tok/s = 9.41x dense
  quality gate: hot-expert int4 KL drift 0.9% < 2% gate; the router stays fp16
  -> quantization flips residency: offload is an fp16 problem - the 4.44x ideal became 9.41x shipped

================================================================
F4 | THE BATCH DISPATCH BILL
  batch B wakes U(B) of 64 experts; weight stream per token = (8 + 0.25 x U(B)) / B GB
  B=1     U=2    8.50 GB/step -> 8.5000 GB/token
  B=64    U=39  17.75 GB/step -> 0.2773 GB/token (30.6x amortized)
  B=256   U=58  22.50 GB/step -> 0.0879 GB/token (96.7x amortized)
  B=1024  U=64  24.00 GB/step -> 0.0234 GB/token (362.7x amortized)
  step latency: 5.55 ms at B=64, 7.50 ms at B=1024 - the slowest stream is the step
  -> batch amortizes the expert stream toward the U(B) ceiling - past it B only buys throughput, and the step the slowest user waits on grows

================================================================
F5 | THE SHARED-EXPERT LEVER
  +1 shared expert (1 GB fp16, every token) flattens the histogram: top-40 86% -> 92% of picks
  spill: 28 -> 16 picks; spill bill 5.60 -> 3.20 ms/token
  stream: 17.72 -> 18.84 GB/token (trunk + picks + shared) = 5.89 ms
  fp16 decode: 11.14 -> 9.09 ms/token -> 110.0 tok/s (+22.6%)
  -> in the offload-bound world the shared expert buys residency headroom, not FLOPs - it pays rent until the int4 flip retires it

================================================================
F6 | THE SERVING LADDER
  dense-40B fp16     25.00 ms/token (  40.0 tok/s)
  moe fp16 + spill   11.14 ms/token (  89.8 tok/s)  <- 2.24x dense
  int4 experts        5.16 ms/token ( 193.9 tok/s)  <- 4.85x dense
  +fp8 trunk          2.66 ms/token ( 376.5 tok/s)  <- 9.41x dense
  final stack: 2.66 ms/token = 9.41x the dense baseline on one 80 GB card
  -> three levers moved the token line 25.00 -> 2.66 ms; each owns one cost - residency, expert precision, trunk precision

================================================================
F7 | THE ABLATION AUDIT
  -fp8 trunk           back to  5.16 ms/token - 4.85x dense (-4.56 of the multiplier)
  -expert int4         back to 11.14 ms/token - 2.24x dense (-7.17 of the multiplier)
  -residency 40 -> 16  back to 20.59 ms/token - 1.21x dense (-8.20 of the multiplier)
  3 of 3 single removals give back more than 4.5x; the deltas order the build: residency planning first, expert quantization second, trunk precision third
  -> no single rung carries the 9.41x - the residency plan is the biggest rung and the cheapest rung to lose

FENCE-064-OK
```
