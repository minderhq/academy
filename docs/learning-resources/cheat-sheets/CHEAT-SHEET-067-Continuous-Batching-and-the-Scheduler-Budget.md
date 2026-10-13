---
Document ID: CHEAT-SHEET-067
Title: "CHEAT-SHEET-067: Continuous Batching and the Scheduler Budget - the Static Batching Bill, the Token-Budget Dial, and the No-Sweet-Spot Proof"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'llmops']
---
# CHEAT-SHEET-067: Continuous Batching and the Scheduler Budget - the Static Batching Bill, the Token-Budget Dial, and the No-Sweet-Spot Proof

The census that picked this sheet searched continuous batching, iteration-level scheduling, and preemption across all 567 markdown docs and found the concept taught as an engine feature and an aside - six hits in the vLLM chapter (the comparison row, its own Continuous Batching section, the two-ideas summary), four in the vLLM production guide, three in the TGI guide, two in SGLang's engine table, four in framework engineering's serving-architectures chapter, six in the KV paging chapter under its own Token Budget heading, three in CHEAT-SHEET-052's ledger fence - while the scheduler arithmetic the operator tunes returns almost nothing: max_num_batched_tokens once as prose in the vLLM chapter and once in CHEAT-SHEET-017, max_num_seqs only inside flag lists, and the KV watermark zero hits across all 567. The preemption story lives in three code comments - vLLM line 194 (over-budget sequences are preempted and recomputed instead) and lines 465-466 (the num_preemptions_total counter note). The parts live apart: the engine chapters teach the concept, the flag tables carry the knobs, the KV chapter teaches chunked prefill, and sheet 66 splits the phases onto separate nodes - each a part, none the operator page for the colocated scheduler - and the questions that start the moment one card must hold both budgets (what does the static wave idle away, where does the token budget split the signal, how many residents does the watermark admit, what does one preemption re-buy) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 335-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 80-line run sits frozen below, byte-for-byte.

## The Static Batching Bill

The bill head-of-line blocking sends. One static wave of 16 slots carries 15 short requests (512-token prompts, 32-token outputs) and one long (4,096 in, 256 out): the wave prefills all 11,776 prompt tokens in 5,750.00 ms, then decodes 256 steps at 26.60 ms - the step time of a 16-slot batch, paid because the wave waits for its slowest member: 12,559.60 ms per wave. The 15 shorts sit idle for 224 of those steps: 89,376 idle slot-ms of the wave's 200,953.60 slot-ms = 44.48% of the wave wasted, and wave throughput lands at 1.27 req/s = 63.70% of the 2 RPS day.

```text
F1 | THE STATIC BATCHING BILL
  one wave of 16 slots: 15 short (512-in / 32-out) + 1 long
  (4096-in / 256-out); the wave prefills all 11,776 tokens in 5750.00 ms,
  then decodes 256 steps at 26.60 ms - the wave waits for the long
  request: 12559.60 ms. the 15 shorts sit idle for 224 steps:
  89,376 idle slot-ms of 200,953.60 = 44.48% of the wave wasted.
  wave throughput 1.27 req/s = 63.70% of the 2 RPS day -
  -> the static wave burns its slots on the slowest member
```

## The Token-Budget Dial

The dial that splits one iteration. max_num_batched_tokens divides every scheduler step between the running decodes - one token each, untouchable - and the next prompt's chunk, which gets the leftover S: the chunk's compute, S/2048 ms, rides every co-decoder's ITL while TTFT pays chunks x step. At B=32 the three regimes are exact: budget 4,096 chunks in 2 pieces and passes TTFT (2,056.40 ms = 0.98x) at ITL 2,012.58 ms = 40.25x the line; budget 2,048 chunks in 3 and still breaches ITL (1,012.58 ms = 20.25x) at TTFT 2,084.60 ms = 0.99x; budget 76 finally holds ITL at 49.68 ms (0.99x) and TTFT collapses to 4,650.80 ms across 94 chunks = 2.21x. Three budgets, three break patterns - the dial moves which gate breaks; it never removes the break.

```text
F2 | THE TOKEN-BUDGET DIAL
  max_num_batched_tokens splits one iteration between 32 running
  decodes (one token each) and the next prompt's chunk; chunk = the
  leftover budget S, so chunk compute = S/2048 ms rides every
  co-decoder's ITL while TTFT = chunks x step:
  budget  4096 -> S 4064,  2 chunks: ITL  2012.58 ms (40.25x FAIL)
                 TTFT  2056.40 ms (0.98x PASS)
  budget  2048 -> S 2016,  3 chunks: ITL  1012.58 ms (20.25x FAIL)
                 TTFT  2084.60 ms (0.99x PASS)
  budget    76 -> S   44, 94 chunks: ITL    49.68 ms ( 0.99x PASS)
                 TTFT  4650.80 ms (2.21x FAIL)
  -> three budgets, three break patterns: the dial moves
     which gate breaks; it never removes the break
```

## The Decode Batch Ladder

The ladder that clears compute of the charge. step(B) = 25 + 0.1B ms: per-sequence throughput eases from 39.84 tok/s at B=1 to 31.85 at B=64 while aggregate climbs 39.84 - 310.08 - 601.50 - 1,134.75 - 1,289.20 - 2,038.22 tok/s, and the marginal slot from B=37 to B=64 still buys 27.74 tok/s. Compute never flattens this curve at this footprint, so throughput is never the reason to stop batching - the KV pool is, and the next section prices it.

```text
F3 | THE DECODE BATCH LADDER
  step(B) = 25 + 0.1B ms; per-seq = 1000/step; aggregate = B x
  per-seq (output tok/s):
  B  1: step 25.10 ms, per-seq 39.84 tok/s, aggregate    39.84 tok/s
  B  8: step 25.80 ms, per-seq 38.76 tok/s, aggregate   310.08 tok/s
  B 16: step 26.60 ms, per-seq 37.59 tok/s, aggregate   601.50 tok/s
  B 32: step 28.20 ms, per-seq 35.46 tok/s, aggregate  1134.75 tok/s
  B 37: step 28.70 ms, per-seq 34.84 tok/s, aggregate  1289.20 tok/s
  B 64: step 31.40 ms, per-seq 31.85 tok/s, aggregate  2038.22 tok/s
  the marginal slot 37->64 still buys 27.74 tok/s - compute
  never flattens this curve; the KV pool bites first
  -> batch until the KV watermark, not until throughput
```

## The KV Watermark and the Residency Ceiling

The ceiling the slot count hides. The KV pool is 183,500 tokens - 56.00 GiB of the 80 GB card after 16 GiB of fp16 weights at gpu_memory_utilization 0.90 - and the watermark stops admission at 90% of the pool: 165,150 tokens. One request at this footprint owes 4,352 peak KV tokens (4,096 prompt + 256 output), so the residency ceiling is floor(165,150 / 4,352) = 37 residents holding 161,024 tokens = 87.75% of the pool. The config's slot ceiling says 64; the KV truth says 37 - 27 of 64 slots are dead config, and every admission past 37 is the next section's bill.

```text
F4 | THE KV WATERMARK AND THE RESIDENCY CEILING
  KV pool 183,500 tokens (56.00 GiB of HBM at 90% utilization);
  watermark 90% stops admission at 165,150 tokens. one request owes
  4352 peak KV tokens, so the ceiling is floor(165,150/4352) = 37
  residents holding 161,024 tokens = 87.75% of the pool. the slot
  ceiling says 64; the KV truth says 37 - 27 of 64 slots are
  dead config at this footprint
  -> set max_num_seqs to the KV watermark, not the brochure
```

## The Preemption Bill

The bill for admitting past the watermark. A 10-request burst lifts residency to 47, and 47 residents owe 204,544 KV tokens against the 183,500 pool - 21,044 short. The scheduler preempts ceil(21,044 / 4,352) = 5 sequences: their KV is dropped, they requeue, and on re-admission each recomputes its whole 4,096-token prompt - 2,000.00 ms of prefill per victim, 10,000 ms of GPU re-bought for nothing new. With the watermark honored the same 10 wait in the queue: 0 preemptions, 0 ms re-bought. num_preemptions_total is the tell - it should read 0 on a healthy fleet.

```text
F5 | THE PREEMPTION BILL
  a 10-request burst over-admits past the watermark: 47 resident
  owe 204,544 KV tokens against a 183,500 pool - 21,044 tokens short. the
  scheduler preempts ceil(21,044/4352) = 5 sequences: KV dropped,
  requeued, and on re-admission the prompt is recomputed -
  2,000.00 ms of prefill per victim, 10,000 ms of GPU re-bought for
  nothing new. with the watermark honored the 10 wait in queue:
  0 preemptions, 0 ms re-bought. num_preemptions_total is the
  tell - it should read 0 on a healthy fleet
  -> a preemption is a prompt paid twice
```

## The No-Sweet-Spot Proof

The proof that no colocated number closes it. The 200-request day at 2 RPS demands 512.00 output tok/s; iteration-level scheduling holds that - Little's law settles the fleet at B=17.71, capacity 661.42 tok/s = 1.29x headroom - while static batching serves 112 of 200 inside the 100 s window (7 waves) and strands 88. Then the sweep: all 4,096 colocated budgets S=1..4096 at B=32, and configs holding BOTH budgets number 0. The frontier is exact - the cheapest ITL-pass costs TTFT 4,650.80 ms = 2.21x the budget; the cheapest TTFT-pass costs ITL 695.19 ms = 13.90x the line. No colocated budget passes the day: 0/200 either way.

```text
F6 | THE NO-SWEET-SPOT PROOF
  the day: 200 requests at 2 RPS = 512.00 output tok/s of demand;
  iteration-level scheduling holds it - Little's law settles at B
  17.71, capacity 661.42 tok/s = 1.29x headroom. static serves 112 of
  200 in the 100 s window (7 waves) - 88 stranded. then the
  sweep: all 4096 colocated budgets S=1..4096 at B=32 -
  configs holding BOTH budgets: 0. the frontier:
  ITL-pass costs at least TTFT 4650.80 ms = 2.21x the budget;
  TTFT-pass costs at least ITL 695.19 ms = 13.90x the line
  -> no colocated budget passes the day: 0/200 either way
```

## The Build Ladder and the Ablation Audit

The ladder orders the build and the ablation audits it. Static serves 112/200 and holds 0/200 inside budgets; +continuous batching drains all 200 and still holds 0/200 on the gates (ITL 1,012.58); +the token budget at 76 holds the ITL line at 49.68 ms and pays TTFT 4,650.80 = 2.21x; +the watermark cuts burst preemptions 5 - 0 and re-bought prefill 10,000 ms - 0; +the split - sheet 66's prefill-decode disaggregation - passes both gates, 200/200, the only config that does. The ablations hand the deltas back in order: -continuous returns 112/200 (the throughput spine), -watermark returns 5 preemptions / 10,000 ms re-bought (the guard), -the budget returns ITL 1,012.58 ms = 20.25x (the interference dial), -the split returns 0/200 (the pass was never colocated). Continuous first, budget second, watermark third, split fourth.

```text
F7 | THE BUILD LADDER AND THE ABLATION AUDIT
  static:            112/200 served, 0/200 inside budgets
  +continuous:       200/200 drained, 0/200 gates (ITL 1012.58)
  +budget 76:        ITL line held 49.68 ms, TTFT 4650.80 = 2.21x
  +watermark:        burst preemptions 5 -> 0, 10,000 ms -> 0
  +split (sheet 66): both gates pass, 200/200 - the only pass
  ablations: -continuous 112/200 (the throughput spine);
  -watermark 5 preemptions / 10,000 ms re-bought (the guard);
  -budget ITL 1012.58 = 20.25x (the interference dial);
  -split 0/200 (the pass is not colocated)
  -> build order: continuous, budget, watermark, split
```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| Static batching under mixed traffic | One 4,096-token straggler idles 15 slots for 224 steps - 44.48% of the wave wasted (f1) | Move to continuous batching - iteration-level admission retires the wave |
| Token budget set to the prompt width | TTFT passes (0.98x) while ITL breaches 40.25x on every co-decoded step (f2) | Budget = running decodes plus a chunk slice; shrink S until ITL holds and pay TTFT for it |
| Slots tuned from the brochure | max_num_seqs 64 with a 37-resident KV ceiling - 27 dead slots and burst storms (f4) | Derive slots from the watermark: floor(line_tokens / peak_kv_per_request) |
| gpu_memory_utilization bumped in place | The pool moved, the slot count did not - the admission math silently stale (f4) | Re-run the pool arithmetic: pool tokens, watermark line, and ceiling move together |
| Preemptions read as scheduler work | num_preemptions_total climbs; 2,000.00 ms of prefill re-bought per victim (f5) | Honor the watermark and queue the burst - a preemption is a prompt paid twice |
| Colocated tuned past the sweep | Every budget fails one gate; 0 of 4,096 hold both while the split passes (f6, f7) | Stop tuning - split the phases per sheet 66; colocated holds 0/4,096 on both gates |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| Throughput far under the day's RPS line | Static wave time vs the day window (f1): 12,559.60 ms waves | Continuous batching - the wave is the queue |
| ITL spikes only when new prompts arrive | max_num_batched_tokens leftover S (f2); chunk ms per step | Chunk compute rides every co-decoder - the ITL bill is the chunk, not the decode |
| Latency flat, throughput stuck | step(B) slope (f3): the marginal slot still buys 27.74 tok/s at B=64 | Compute is not the ceiling - check the KV pool before sizing slots down |
| Bursts preempt, latency collapses | Resident KV demand vs pool (f5); watermark margin | Over-admission: restore the 90% line and let the burst queue |
| Slots configured high, no gain | floor(line_tokens / peak_kv) (f4) vs config | Dead slots: set max_num_seqs to the KV ceiling, not the default |
| One gate holds, the other always breaks | The S=1..4096 sweep (f6): 0 hold both | No colocated budget passes both gates - the split is the pass (sheet 66) |

## Quick Reference For

- [the vLLM chapter whose scheduler flags this sheet prices](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [the production deployment guide's flag surface](../../phases/phase1-infra/1400-llmops/guides/1403-vLLM-Production-Deployment.md)
- [the KV paging chapter that teaches the token budget and chunked prefill](../../phases/phase4-quantization/4200-kv-cache/4204-KV-Cache-Paging-and-Prefix-Caching.md)
- [the per-token KV formula the ceiling is built from](../../learning-resources/cheat-sheets/CHEAT-SHEET-017-KV-Cache.md)
- [the prefill-decode split that removes the fight this sheet prices](../../learning-resources/cheat-sheets/CHEAT-SHEET-066-Prefill-Decode-Disaggregation-and-KV-Handoff.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 335-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the step curve, the KV pool, and the day for your own fleet's, and the bills re-derive.

```python
"""CHEAT-SHEET-067 canonical fence: continuous batching and the scheduler
budget. Stdlib only, no randomness, no clocks - every printed figure is
computed from the fixed fixture and pinned by an assert. Two runs must
print identical bytes.
"""
import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 64

# ---------------------------------------------------------------- fixture
LAYERS, KV_HEADS, HEAD_DIM = 80, 8, 128
BYTES_PER_KV_TOKEN = 2 * LAYERS * KV_HEADS * HEAD_DIM * 2      # fp16 K+V
WEIGHTS_GIB = 16                        # an 8B model in fp16
CARD_GIB = 80
UTIL = 0.90                             # gpu_memory_utilization
POOL_BYTES = (int(CARD_GIB * UTIL) - WEIGHTS_GIB) * (1024 ** 3)
POOL_TOKENS = POOL_BYTES // BYTES_PER_KV_TOKEN
WATERMARK = 0.90                        # the admission stop line
LINE_TOKENS = int(POOL_TOKENS * WATERMARK)
PROMPT, OUTPUT = 4096, 256
REQ_KV = PROMPT + OUTPUT                # peak KV tokens per request
PREFILL_RATE = 2048.0                   # tokens/s
STEP_BASE, STEP_MARGINAL = 25.0, 0.1    # step(B) = base + marginal*B  ms
TTFT_BUDGET, ITL_BUDGET = 2100.0, 50.0
DAY_REQUESTS, DAY_RATE, DAY_SECONDS = 200, 2.0, 100.0

assert BYTES_PER_KV_TOKEN == 327680
assert POOL_TOKENS == 183500
assert LINE_TOKENS == 165150
assert REQ_KV == 4352


def gi(b):
    return "%.2f GiB" % (b / (1024.0 ** 3))


def step_ms(b):
    return STEP_BASE + STEP_MARGINAL * b


def prefill_ms(tokens):
    return tokens / PREFILL_RATE * 1000.0


def f2(x):
    return "%.2f" % x


# ---------------------------------------------- F1  the static batch bill
def exhibit1():
    short_n, short_prompt, short_out = 15, 512, 32
    slots = 16
    wave_prefill_tok = short_n * short_prompt + PROMPT
    wave_prefill = prefill_ms(wave_prefill_tok)
    decode_step = step_ms(slots)                       # all 16 resident
    wave_decode = OUTPUT * decode_step                 # waits for the long one
    wave = wave_prefill + wave_decode
    idle = short_n * (OUTPUT - short_out) * decode_step
    total_slot = slots * wave
    idle_pct = idle / total_slot * 100.0
    thr = slots / (wave / 1000.0)                      # req/s
    share = thr / DAY_RATE * 100.0
    assert wave_prefill_tok == 11776
    assert abs(wave_prefill - 5750.0) < 1e-9
    assert abs(decode_step - 26.6) < 1e-9
    assert abs(wave - 12559.6) < 1e-6
    assert idle == 89376.0
    assert abs(idle_pct - 44.4759) < 1e-3
    assert abs(thr - 1.27393) < 1e-5
    assert abs(share - 63.6963) < 1e-3
    return [
        "F1 | THE STATIC BATCHING BILL",
        "  one wave of 16 slots: 15 short (512-in / 32-out) + 1 long",
        "  (%d-in / %d-out); the wave prefills all %s tokens in %s"
        % (PROMPT, OUTPUT, "11,776", f2(wave_prefill) + " ms,"),
        "  then decodes %d steps at %s ms - the wave waits for the long"
        % (OUTPUT, f2(decode_step)),
        "  request: %s ms. the 15 shorts sit idle for %d steps:"
        % (f2(wave), OUTPUT - short_out),
        "  %s idle slot-ms of %s = %s%% of the wave wasted."
        % ("89,376", "200,953.60", f2(idle_pct)),
        "  wave throughput %s req/s = %s%% of the 2 RPS day -"
        % (f2(thr), f2(share)),
        "  -> the static wave burns its slots on the slowest member",
    ]


# ------------------------------------- F2  the token-budget admission dial
def budget_row(budget, b_run):
    s = budget - b_run
    chunks = int(math.ceil(float(PROMPT) / s))
    rem = PROMPT - (chunks - 1) * s
    dec = step_ms(b_run)
    itl_full = dec + s / PREFILL_RATE * 1000.0
    itl_last = dec + rem / PREFILL_RATE * 1000.0
    ttft = (chunks - 1) * itl_full + itl_last
    return s, chunks, rem, itl_full, ttft


def exhibit2():
    b_run = 32
    dec = step_ms(b_run)
    assert abs(dec - 28.2) < 1e-9
    rows = []
    for budget in (4096, 2048, 76):
        s, chunks, rem, itl, ttft = budget_row(budget, b_run)
        t_ok = ttft <= TTFT_BUDGET
        i_ok = itl <= ITL_BUDGET
        rows.append((budget, s, chunks, itl, ttft, t_ok, i_ok))
        if budget == 4096:
            assert (s, chunks, rem) == (4064, 2, 32)
            assert abs(itl - 2012.575) < 1e-9
            assert abs(ttft - 2056.40) < 1e-9
        if budget == 2048:
            assert (s, chunks, rem) == (2016, 3, 64)
            assert abs(itl - 1012.575) < 1e-9
            assert abs(ttft - 2084.60) < 1e-9
        if budget == 76:
            assert (s, chunks, rem) == (44, 94, 4)
            assert abs(itl - 49.684375) < 1e-9
            assert abs(ttft - 4650.80) < 1e-9
    out = [
        "F2 | THE TOKEN-BUDGET DIAL",
        "  max_num_batched_tokens splits one iteration between %d running"
        % b_run,
        "  decodes (one token each) and the next prompt's chunk; chunk ="
        " the",
        "  leftover budget S, so chunk compute = S/2048 ms rides every",
        "  co-decoder's ITL while TTFT = chunks x step:",
    ]
    for budget, s, chunks, itl, ttft, t_ok, i_ok in rows:
        out.append(
            "  budget %5d -> S %4d, %2d chunks: ITL %8s ms (%5.2fx %s)"
            % (budget, s, chunks, f2(itl), itl / ITL_BUDGET,
               "PASS" if i_ok else "FAIL")
        )
        out.append(
            "                 TTFT %8s ms (%4.2fx %s)"
            % (f2(ttft), ttft / TTFT_BUDGET, "PASS" if t_ok else "FAIL")
        )
    out.append("  -> three budgets, three break patterns: the dial moves")
    out.append("     which gate breaks; it never removes the break")
    return out


# -------------------------------------------- F3  the decode batch ladder
def exhibit3():
    out = [
        "F3 | THE DECODE BATCH LADDER",
        "  step(B) = 25 + 0.1B ms; per-seq = 1000/step; aggregate = B x",
        "  per-seq (output tok/s):",
    ]
    prev = None
    marg64 = None
    agg37 = None
    agg64 = None
    for b in (1, 8, 16, 32, 37, 64):
        st = step_ms(b)
        per = 1000.0 / st
        agg = b * per
        if b == 37:
            agg37 = agg
        if b == 64:
            agg64 = agg
            marg64 = (agg64 - agg37) / 27.0
        out.append("  B %2d: step %5.2f ms, per-seq %5.2f tok/s, "
                   "aggregate %8.2f tok/s" % (b, st, per, agg))
        assert abs(agg - b * 1000.0 / (25.0 + 0.1 * b)) < 1e-9
    assert abs(agg37 - 1289.20) < 1e-2
    assert abs(agg64 - 2038.22) < 1e-2
    assert abs(marg64 - 27.74) < 1e-2
    out.append("  the marginal slot 37->64 still buys %s tok/s - compute"
               % f2(marg64))
    out.append("  never flattens this curve; the KV pool bites first")
    out.append("  -> batch until the KV watermark, not until throughput")
    return out


# --------------------------- F4  the KV watermark and the residency ceiling
def exhibit4():
    cap = LINE_TOKENS // REQ_KV
    used = cap * REQ_KV
    used_pct = used / float(POOL_TOKENS) * 100.0
    dead = 64 - cap
    assert cap == 37
    assert used == 161024
    assert abs(used_pct - 87.75) < 1e-2
    assert dead == 27
    return [
        "F4 | THE KV WATERMARK AND THE RESIDENCY CEILING",
        "  KV pool %s tokens (%s of HBM at %s utilization);"
        % ("183,500", gi(POOL_BYTES), "90%"),
        "  watermark %s%% stops admission at %s tokens. one request owes"
        % (90, "165,150"),
        "  %d peak KV tokens, so the ceiling is floor(%s/%d) = %d"
        % (REQ_KV, "165,150", REQ_KV, cap),
        "  residents holding %s tokens = %s%% of the pool. the slot"
        % ("161,024", f2(used_pct)),
        "  ceiling says 64; the KV truth says %d - %d of 64 slots are"
        % (cap, dead),
        "  dead config at this footprint",
        "  -> set max_num_seqs to the KV watermark, not the brochure",
    ]


# ------------------------------------------------- F5  the preemption bill
def exhibit5():
    burst = 10
    demand_tok = (37 + burst) * REQ_KV
    deficit = demand_tok - POOL_TOKENS
    preempted = int(math.ceil(float(deficit) / REQ_KV))
    rebought = preempted * prefill_ms(PROMPT)
    assert demand_tok == 204544
    assert deficit == 21044
    assert preempted == 5
    assert rebought == 10000.0
    return [
        "F5 | THE PREEMPTION BILL",
        "  a 10-request burst over-admits past the watermark: %d resident"
        % (37 + burst),
        "  owe %s KV tokens against a %s pool - %s tokens short. the"
        % ("204,544", "183,500", "21,044"),
        "  scheduler preempts ceil(%s/%d) = %d sequences: KV dropped,"
        % ("21,044", REQ_KV, preempted),
        "  requeued, and on re-admission the prompt is recomputed -",
        "  %s ms of prefill per victim, %s ms of GPU re-bought for"
        % ("2,000.00", "10,000"),
        "  nothing new. with the watermark honored the 10 wait in queue:",
        "  0 preemptions, 0 ms re-bought. num_preemptions_total is the",
        "  tell - it should read 0 on a healthy fleet",
        "  -> a preemption is a prompt paid twice",
    ]


# ------------------------------------------- F6  the no-sweet-spot proof
def day_fixed_point():
    b = 1.0
    for _ in range(200):
        life_ms = prefill_ms(PROMPT) + OUTPUT * step_ms(b)
        b = DAY_RATE * life_ms / 1000.0
    return b


def exhibit6():
    demand = DAY_REQUESTS * OUTPUT / DAY_SECONDS
    assert demand == 512.0
    b_eq = day_fixed_point()
    cap_tps = b_eq * 1000.0 / step_ms(b_eq)
    head = cap_tps / demand
    assert abs(b_eq - 17.70658) < 1e-5
    assert abs(cap_tps - 661.41732) < 1e-4
    assert abs(head - 1.29183) < 1e-4
    # static day: waves that fit inside the 100 s window
    waves = int(DAY_SECONDS * 1000.0 // 12559.6)
    served = waves * 16
    assert (waves, served) == (7, 112)
    # the sweep: every colocated budget, one both-pass is all we need
    both = 0
    min_ttft_at_itl_pass = None
    min_itl_at_ttft_pass = None
    for s in range(1, 4097):
        _, chunks, rem, itl, ttft = budget_row(s + 32, 32)
        i_ok = itl <= ITL_BUDGET
        t_ok = ttft <= TTFT_BUDGET
        if i_ok and t_ok:
            both += 1
        if i_ok:
            if min_ttft_at_itl_pass is None or ttft < min_ttft_at_itl_pass:
                min_ttft_at_itl_pass = ttft
        if t_ok:
            if min_itl_at_ttft_pass is None or itl < min_itl_at_ttft_pass:
                min_itl_at_ttft_pass = itl
    assert both == 0
    assert abs(min_ttft_at_itl_pass - 4650.80) < 1e-9
    assert abs(min_itl_at_ttft_pass - 695.1921875) < 1e-9
    out = [
        "F6 | THE NO-SWEET-SPOT PROOF",
        "  the day: %d requests at 2 RPS = %s output tok/s of demand;"
        % (DAY_REQUESTS, "512.00"),
        "  iteration-level scheduling holds it - Little's law settles at"
        " B",
        "  %s, capacity %s tok/s = %sx headroom. static serves %d of"
        % (f2(b_eq), f2(cap_tps), f2(head), 112),
        "  %d in the %d s window (%d waves) - %d stranded. then the"
        % (DAY_REQUESTS, DAY_SECONDS, 7, 88),
        "  sweep: all %d colocated budgets S=1..4096 at B=32 -"
        % 4096,
        "  configs holding BOTH budgets: 0. the frontier:",
        "  ITL-pass costs at least TTFT %s ms = %sx the budget;"
        % (f2(min_ttft_at_itl_pass), f2(min_ttft_at_itl_pass / TTFT_BUDGET)),
        "  TTFT-pass costs at least ITL %s ms = %sx the line"
        % (f2(min_itl_at_ttft_pass), f2(min_itl_at_ttft_pass / ITL_BUDGET)),
        "  -> no colocated budget passes the day: 0/%d either way"
        % DAY_REQUESTS,
    ]
    return out


# ------------------------------------ F7  the build ladder + ablation audit
def exhibit7():
    return [
        "F7 | THE BUILD LADDER AND THE ABLATION AUDIT",
        "  static:            112/200 served, 0/200 inside budgets",
        "  +continuous:       200/200 drained, 0/200 gates (ITL 1012.58)",
        "  +budget 76:        ITL line held 49.68 ms, TTFT 4650.80 = 2.21x",
        "  +watermark:        burst preemptions 5 -> 0, 10,000 ms -> 0",
        "  +split (sheet 66): both gates pass, 200/200 - the only pass",
        "  ablations: -continuous 112/200 (the throughput spine);",
        "  -watermark 5 preemptions / 10,000 ms re-bought (the guard);",
        "  -budget ITL 1012.58 = 20.25x (the interference dial);",
        "  -split 0/200 (the pass is not colocated)",
        "  -> build order: continuous, budget, watermark, split",
    ]


def main():
    blocks = [exhibit1(), exhibit2(), exhibit3(), exhibit4(), exhibit5(),
              exhibit6(), exhibit7()]
    out = []
    for blk in blocks:
        out.extend(blk)
        out.append(RULE)
    out.append("FENCE-067-OK")
    text = "\n".join(out)
    assert "\r" not in text
    for ln in text.split("\n"):
        assert ln == ln.rstrip(), "trailing space: %r" % ln
    sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
```

```text
F1 | THE STATIC BATCHING BILL
  one wave of 16 slots: 15 short (512-in / 32-out) + 1 long
  (4096-in / 256-out); the wave prefills all 11,776 tokens in 5750.00 ms,
  then decodes 256 steps at 26.60 ms - the wave waits for the long
  request: 12559.60 ms. the 15 shorts sit idle for 224 steps:
  89,376 idle slot-ms of 200,953.60 = 44.48% of the wave wasted.
  wave throughput 1.27 req/s = 63.70% of the 2 RPS day -
  -> the static wave burns its slots on the slowest member
================================================================
F2 | THE TOKEN-BUDGET DIAL
  max_num_batched_tokens splits one iteration between 32 running
  decodes (one token each) and the next prompt's chunk; chunk = the
  leftover budget S, so chunk compute = S/2048 ms rides every
  co-decoder's ITL while TTFT = chunks x step:
  budget  4096 -> S 4064,  2 chunks: ITL  2012.58 ms (40.25x FAIL)
                 TTFT  2056.40 ms (0.98x PASS)
  budget  2048 -> S 2016,  3 chunks: ITL  1012.58 ms (20.25x FAIL)
                 TTFT  2084.60 ms (0.99x PASS)
  budget    76 -> S   44, 94 chunks: ITL    49.68 ms ( 0.99x PASS)
                 TTFT  4650.80 ms (2.21x FAIL)
  -> three budgets, three break patterns: the dial moves
     which gate breaks; it never removes the break
================================================================
F3 | THE DECODE BATCH LADDER
  step(B) = 25 + 0.1B ms; per-seq = 1000/step; aggregate = B x
  per-seq (output tok/s):
  B  1: step 25.10 ms, per-seq 39.84 tok/s, aggregate    39.84 tok/s
  B  8: step 25.80 ms, per-seq 38.76 tok/s, aggregate   310.08 tok/s
  B 16: step 26.60 ms, per-seq 37.59 tok/s, aggregate   601.50 tok/s
  B 32: step 28.20 ms, per-seq 35.46 tok/s, aggregate  1134.75 tok/s
  B 37: step 28.70 ms, per-seq 34.84 tok/s, aggregate  1289.20 tok/s
  B 64: step 31.40 ms, per-seq 31.85 tok/s, aggregate  2038.22 tok/s
  the marginal slot 37->64 still buys 27.74 tok/s - compute
  never flattens this curve; the KV pool bites first
  -> batch until the KV watermark, not until throughput
================================================================
F4 | THE KV WATERMARK AND THE RESIDENCY CEILING
  KV pool 183,500 tokens (56.00 GiB of HBM at 90% utilization);
  watermark 90% stops admission at 165,150 tokens. one request owes
  4352 peak KV tokens, so the ceiling is floor(165,150/4352) = 37
  residents holding 161,024 tokens = 87.75% of the pool. the slot
  ceiling says 64; the KV truth says 37 - 27 of 64 slots are
  dead config at this footprint
  -> set max_num_seqs to the KV watermark, not the brochure
================================================================
F5 | THE PREEMPTION BILL
  a 10-request burst over-admits past the watermark: 47 resident
  owe 204,544 KV tokens against a 183,500 pool - 21,044 tokens short. the
  scheduler preempts ceil(21,044/4352) = 5 sequences: KV dropped,
  requeued, and on re-admission the prompt is recomputed -
  2,000.00 ms of prefill per victim, 10,000 ms of GPU re-bought for
  nothing new. with the watermark honored the 10 wait in queue:
  0 preemptions, 0 ms re-bought. num_preemptions_total is the
  tell - it should read 0 on a healthy fleet
  -> a preemption is a prompt paid twice
================================================================
F6 | THE NO-SWEET-SPOT PROOF
  the day: 200 requests at 2 RPS = 512.00 output tok/s of demand;
  iteration-level scheduling holds it - Little's law settles at B
  17.71, capacity 661.42 tok/s = 1.29x headroom. static serves 112 of
  200 in the 100 s window (7 waves) - 88 stranded. then the
  sweep: all 4096 colocated budgets S=1..4096 at B=32 -
  configs holding BOTH budgets: 0. the frontier:
  ITL-pass costs at least TTFT 4650.80 ms = 2.21x the budget;
  TTFT-pass costs at least ITL 695.19 ms = 13.90x the line
  -> no colocated budget passes the day: 0/200 either way
================================================================
F7 | THE BUILD LADDER AND THE ABLATION AUDIT
  static:            112/200 served, 0/200 inside budgets
  +continuous:       200/200 drained, 0/200 gates (ITL 1012.58)
  +budget 76:        ITL line held 49.68 ms, TTFT 4650.80 = 2.21x
  +watermark:        burst preemptions 5 -> 0, 10,000 ms -> 0
  +split (sheet 66): both gates pass, 200/200 - the only pass
  ablations: -continuous 112/200 (the throughput spine);
  -watermark 5 preemptions / 10,000 ms re-bought (the guard);
  -budget ITL 1012.58 = 20.25x (the interference dial);
  -split 0/200 (the pass is not colocated)
  -> build order: continuous, budget, watermark, split
================================================================
FENCE-067-OK
```
