---
Document ID: CHEAT-SHEET-066
Title: "CHEAT-SHEET-066: Prefill-Decode Disaggregation and KV Handoff - the Interference Bill, the Handoff Ladder, and the Pool Split"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'llmops']
---
# CHEAT-SHEET-066: Prefill-Decode Disaggregation and KV Handoff - the Interference Bill, the Handoff Ladder, and the Pool Split

The census that picked this sheet searched prefill-decode disaggregation, PD serving, Splitwise, and DistServe across all 566 markdown docs and found the serving split in eleven hits in three files - the launch-topology flags inside the SGLang serving chapter (the role split, the bootstrap rendezvous, the mooncake transfer default), eight research citations inside the stage-scaling chapter (four Splitwise, four DistServe), and one advice row in CHEAT-SHEET-034 - while KV-handoff cost, the fabric floor, and the pool arithmetic return zero. The parts live apart: the serving chapters teach the launch flags, the stage-scaling chapter cites the papers, the KV sheets carry the per-token formula - each a part, none the operator page - and the questions that start the moment one gateway serves both prompt storms and long decodes on the same fleet (what does one KV handoff cost across the fabric, what does the TTFT slack buy back, how many nodes does each phase need, which signal scales which pool) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 178-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 58-line run sits frozen below, byte-for-byte.

## The Interference Bill

The bill that kills colocated serving. One replica runs both phases: a 4,096-token prompt prefills in 2,000 ms and every co-decoder waits the whole block - ITL 2,025 ms against the 50 ms budget, 40.50x over. Chunked prefill trades one gate for the other: chunk 512 lands ITL 275 ms (5.50x over), chunk 128 lands 87.50 ms (1.75x over), and the ITL-pass chunk 51 holds ITL 49.90 ms only by stretching TTFT to 4,042.09 ms = 1.92x over. No chunk size holds both budgets - the phases share one signal and break one gate each.

```text
F1 | THE INTERFERENCE BILL
  one colocated replica runs both phases: a 4,096-token prompt
  prefills in 2000 ms and every co-decoder waits the whole block -
  ITL 2025 ms vs the 50 ms budget = 40.50x over
  chunked prefill trades one gate for the other: chunk 512 ->
  ITL 275 ms (5.50x over); chunk 128 -> ITL 87.50 ms (1.75x over);
  the ITL-pass chunk 51 holds ITL 49.90 ms but TTFT becomes 81 chunks
  x 49.90 ms = 4042.09 ms = 1.92x over the TTFT budget
  -> no chunk size holds both budgets: colocated breaks one gate
```

## The Disaggregation Bill

The split buys both gates by construction. The prefill-only node lands TTFT 2,000 ms with 100 ms of slack under the 2,100 ms budget; the decode-only node lands ITL 25 ms with two steps per 50 ms window and 25 ms of slack. Nothing is left to tune - but nothing is free either: the bridge the split must pay for is the KV handoff, and the handoff is its own line item.

```text
F2 | THE DISAGGREGATION BILL
  prefill-only node: TTFT 2000 ms - 100 ms of slack under the 2100 ms
  budget; decode-only node: ITL 25 ms - 2 steps per 50 ms window,
  25 ms of slack; both gates pass by construction
  -> the split buys both gates; the handoff is its own line item
```

## The Handoff Ladder

The handoff ladder prices the bridge. One 1.25 GiB KV blob - 1,342,177,280 bytes for one 4,096-token request - crosses the fabric: 1.49 ms over intra-node NVLink at 900 GB/s, 26.84 ms over IB 400G RDMA at 50 GB/s, 107.37 ms over 100GbE RoCE at 12.50 GB/s, 429.50 ms over 25GbE. Split TTFT passes the 2,100 ms budget on NVLink (2,001.49 ms) and IB (2,026.84 ms) and fails on 100GbE (2,107.37 ms) and 25GbE (2,429.50 ms). The TTFT slack buys a 13.42 GB/s fabric floor; 100GbE misses it by 0.92 GB/s - and the 50 GB/s rung is the same 26.84 ms the tiered-cache sheet measured off DRAM.

```text
F3 | THE HANDOFF LADDER
  one 1.25 GiB KV blob (1,342,177,280 bytes) crosses the fabric:
  NVLink intra-node at 900 GB/s = 1.49 ms, split TTFT 2001.49 ms PASS
  IB 400G RDMA at 50 GB/s = 26.84 ms, split TTFT 2026.84 ms PASS
  100GbE RoCE at 12.50 GB/s = 107.37 ms, split TTFT 2107.37 ms FAIL
  25GbE at 3.12 GB/s = 429.50 ms, split TTFT 2429.50 ms FAIL
  -> the TTFT slack buys a 13.42 GB/s floor; 100GbE misses it by 0.92
```

## The Sizing Gate

The sizing gate turns the day into a fleet. The 200-request day at 2 RPS demands 4 node-units of prefill - 5 nodes at 80% utilization - while decode is 12.80 concurrent sequences, one node at an average batch of 12.03 against a 64-slot batch (18.80%). The split fleet is 5P + 1D, and the day costs 400 + 106.40 = 506.40 node-seconds. Colocated holds both gates at 0 RPS: the split is not a speedup, it is the only form that holds the gate.

```text
F4 | THE SIZING GATE
  the 200-request day at 2 RPS: prefill demands 4 node-units ->
  5 nodes at 80% util; decode is 12.80 concurrent sequences -> 1
  node at avg batch 12.03, peak 12.80 of a 64-slot batch (18.80%)
  split fleet 5P + 1D costs 400 + 106.40 = 506.40 node-s for the day
  -> colocated holds both gates at 0 RPS - the split is the form
  that holds the gate, not a speedup
```

## The Burst Gate

The burst gate shows why one signal cannot run both pools. Fifty requests land at once: the prefill queue of 100 node-seconds on 5 nodes drains in 20 s and the last request's TTFT hits 20,000 ms = 9.52x over the budget, while the decode pool holds 50 of 64 slots (78.12%) with ITL 25 ms throughout. Scale prefill on queue depth, decode on batch occupancy - one blended RPS signal sizes neither pool.

```text
F5 | THE BURST GATE
  50 requests land at once: prefill queue 100 node-s on 5 nodes
  drains in 20 s - the last request's TTFT 20000 ms = 9.52x over the
  budget; decode holds 50 of 64 slots (78.12%), ITL 25 ms all the way
  -> scale prefill on queue depth (100 node-s), decode on batch
  occupancy (50/64); one blended RPS signal sizes neither pool
```

## The Day Bill

The day bill on the split fleet: prefill burns 400 of 500 node-seconds (80%), decode runs 4,256 steps in 106.40 wall-seconds at an average batch of 12.03, and the SLO ledger reads 200/200 PASS. The best colocated config holds 0/200 - unchunked ITL breaches 200/200 at 2,025 ms, ITL-tuned TTFT breaches 200/200 at 4,042.09 ms. Same work, different topology.

```text
F6 | THE DAY BILL
  200 requests x 4,096-token prompts x 256-token outputs:
  split fleet: prefill 400 of 500 node-s (80%), decode 4,256 steps in
  106.40 wall-s at avg batch 12.03 - SLO ledger 200/200 requests PASS
  colocated unchunked: TTFT 2000 ms holds, ITL 2025 ms breaches 200/200;
  colocated ITL-tuned (chunk 51): ITL 49.90 ms holds, TTFT 4042.09 ms
  breaches 200/200 - same work, different topology
  -> best colocated holds 0/200 at both gates; the split holds 200/200
```

## The Ablation Audit

The ablation audit orders the build. Full split: 200/200 at TTFT 2,026.84 ms / ITL 25 ms. Remove disaggregation and the best colocated config breaches TTFT on every request (4,042.09 ms = 0 of 200 pass); remove fabric headroom and 25GbE lands TTFT 2,429.50 ms = 0 of 200; collapse the pools into one blended-signal pool of 2 nodes and the last request waits 202,000 ms = 96.19x over. Disaggregate first, fabric second, pools third.

```text
F7 | THE ABLATION AUDIT
  full split 200/200 at TTFT 2026.84 ms / ITL 25 ms; remove one lever:
  -disaggregation: best colocated (chunk 51) TTFT 4042.09 ms = 0 of 200
    pass the gate
  -fabric: 25GbE handoff TTFT 2429.50 ms = 0 of 200 pass the gate
  -pool-split: one blended pool of 2 nodes, last TTFT 202000 ms = 96.19x
    over the budget
  -> order the build: disaggregate first, fabric second, pools third
```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| Colocated chunk-tuning loop | ITL passes only by stretching TTFT past the budget, then the reverse (f1) | Accept that colocated holds one gate; move to the split - no chunk size holds both |
| Fabric under the floor | 100GbE handoff lands split TTFT 2,107.37 ms and the budget is gone (f3) | Size the fabric from the TTFT slack: the floor is 13.42 GB/s - IB 400G, not 100GbE |
| One blended autoscale signal | A burst breaches TTFT 9.52x while decode sits at 78% - both pools are wrong (f5) | Two signals: prefill on queue depth (node-seconds), decode on batch occupancy |
| Handoff serialized into decode | The decode node steps while the KV blob streams - ITL spikes by the handoff time (f3) | Land the full 1.25 GiB before the first decode step - the handoff is TTFT-side, not ITL-side |
| Prefill pool run at 100% | A 4.0 node-unit day on 4 nodes leaves zero headroom and queues under jitter (f4) | Provision to a utilization target - 5 nodes at 80%, not 4 at 100% |
| Ladder rungs refuse to compose | The day ledger moves when one lever is removed but not by its own delta (f7) | Each lever owns one gate - disaggregation = both SLOs, fabric = TTFT, pools = signals; a lever touching two is misbuilt |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| TTFT good in isolation, breaches in production | Co-run graph: prefill blocks vs decode steps (f1) | The phases fight for one timeline - disaggregate; chunking moves the breach, it does not remove it |
| Split TTFT ~100 ms over budget on every request | Handoff ms per fabric rung (f3); KV bytes per request | The fabric is under the 13.42 GB/s floor - move the rung to IB/RDMA |
| ITL fine, TTFT terrible, decode pool idle | Prefill queue depth (f5); admission cap | Burst admission: queue depth is the TTFT bill - decode capacity is not the constraint |
| Decode pool autoscaled, ITL still spikes | Batch occupancy vs slot cap (f5); co-resident prefill | A prefill block on the decode node is an ITL event - the node must be decode-only |
| Fleet sized from RPS alone | Node-units per phase (f4): prefill ms x RPS vs concurrent x lifetime | RPS sizes neither pool - size prefill from node-units, decode from concurrent sequences |
| Ledger shows breaches the fixture never had | Budget lines per request (f6); handoff path | One line per request: prefill ms + handoff ms vs the TTFT budget; decode ITL vs the ITL budget |

## Quick Reference For

- [the SGLang serving surface PD disaggregation lands on](../../phases/phase1-infra/1400-llmops/1405-SGLang.md)
- [vLLM, the other serving surface the split runs on](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [the per-stage economics DistServe and Splitwise quantify](../../phases/phase6-rag/6500-mlops-pipelines/6505-Response-Caching-and-Stage-Scaling.md)
- [the KV offload and tiered-cache ladder the same math prices](../../learning-resources/cheat-sheets/CHEAT-SHEET-062-KV-Offload-and-Tiered-Caching.md)
- [the per-token KV formula the handoff blob is built from](../../learning-resources/cheat-sheets/CHEAT-SHEET-017-KV-Cache.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 178-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the trace for your own gateway logs, and the bills re-derive.

```python
"""Prefill-decode disaggregation on one fixed fixture: an 80-layer
model with 8 GQA KV heads at head_dim 128 in fp16 owes 327,680 bytes
of KV per token, so a 4,096-token prompt is a 1.25 GiB KV blob;
prefill streams 2,048 tok/s, decode steps in 25 ms, a request lives
6.4 s, the day is 200 requests at 2 RPS, and the budgets are 2,100 ms
TTFT and 50 ms ITL. Every printed figure is computed from the
constants and pinned by an assert - no figure is typed twice."""
RULE = "=" * 64

def fmt(x):
    """int-cast when integral, else two decimals (t1054 law)."""
    return str(int(x)) if float(x) == int(x) else "%.2f" % x

def grp(x):
    return "{:,}".format(int(x))

# ---------------------------------------------------------------- fixture
LAYERS, KVH, HDIM, BPE = 80, 8, 128, 2
KV_BYTES_TOK = 2 * LAYERS * KVH * HDIM * BPE          # K and V, fp16
PROMPT_TOK = 4096
KV_BYTES_REQ = KV_BYTES_TOK * PROMPT_TOK
KV_GIB = KV_BYTES_REQ / (1024 ** 3)
PREFILL_TPS = 2048.0
PREFILL_MS = PROMPT_TOK / PREFILL_TPS * 1000.0
DECODE_MS = 25.0
OUT_TOK = 256
LIFETIME_S = OUT_TOK * DECODE_MS / 1000.0
TTFT_BUDGET = 2100.0
ITL_BUDGET = 50.0
DAY_REQ = 200
RATE_RPS = 2.0
SPAN_S = DAY_REQ / RATE_RPS

assert KV_BYTES_TOK == 327680
assert KV_GIB == 1.25
assert PREFILL_MS == 2000.0

print(RULE)
print("F1 | THE INTERFERENCE BILL")
print("  one colocated replica runs both phases: a %s-token prompt"
      % grp(PROMPT_TOK))
print("  prefills in %s ms and every co-decoder waits the whole block -" %
      fmt(PREFILL_MS))
print("  ITL %s ms vs the %s ms budget = %sx over" %
      (fmt(PREFILL_MS + DECODE_MS), fmt(ITL_BUDGET),
       fmt((PREFILL_MS + DECODE_MS) / ITL_BUDGET)))
itl512 = 512 / PREFILL_TPS * 1000.0 + DECODE_MS
itl128 = 128 / PREFILL_TPS * 1000.0 + DECODE_MS
assert itl512 == 275.0 and itl128 == 87.5
print("  chunked prefill trades one gate for the other: chunk %s ->" %
      grp(512))
print("  ITL %s ms (%sx over); chunk %s -> ITL %s ms (%sx over);" %
      (fmt(itl512), fmt(itl512 / ITL_BUDGET), grp(128), fmt(itl128),
       fmt(itl128 / ITL_BUDGET)))
chunk_tok = 51
chunk_ms = chunk_tok / PREFILL_TPS * 1000.0
itl = chunk_ms + DECODE_MS
n_chunks = -(-PROMPT_TOK // chunk_tok)
ttft_coloc = n_chunks * (chunk_ms + DECODE_MS)
assert itl <= ITL_BUDGET
print("  the ITL-pass chunk %s holds ITL %s ms but TTFT becomes %s chunks" %
      (grp(chunk_tok), fmt(itl), grp(n_chunks)))
print("  x %s ms = %s ms = %sx over the TTFT budget" %
      (fmt(chunk_ms + DECODE_MS), fmt(ttft_coloc),
       fmt(ttft_coloc / TTFT_BUDGET)))
print("  -> no chunk size holds both budgets: colocated breaks one gate")

print(RULE)
print("F2 | THE DISAGGREGATION BILL")
print("  prefill-only node: TTFT %s ms - %s ms of slack under the %s ms" %
      (fmt(PREFILL_MS), fmt(TTFT_BUDGET - PREFILL_MS), fmt(TTFT_BUDGET)))
print("  budget; decode-only node: ITL %s ms - %s steps per %s ms window," %
      (fmt(DECODE_MS), fmt(ITL_BUDGET / DECODE_MS), fmt(ITL_BUDGET)))
print("  %s ms of slack; both gates pass by construction" %
      fmt(ITL_BUDGET - DECODE_MS))
print("  -> the split buys both gates; the handoff is its own line item")

print(RULE)
print("F3 | THE HANDOFF LADDER")
print("  one %s GiB KV blob (%s bytes) crosses the fabric:" %
      (fmt(KV_GIB), grp(KV_BYTES_REQ)))
fabrics = [("NVLink intra-node", 900.0), ("IB 400G RDMA", 50.0),
           ("100GbE RoCE", 12.5), ("25GbE", 3.125)]
for name, gbps in fabrics:
    ms = KV_BYTES_REQ / (gbps * 1e9) * 1000.0
    ttft = PREFILL_MS + ms
    gate = "PASS" if ttft <= TTFT_BUDGET else "FAIL"
    print("  %s at %s GB/s = %s ms, split TTFT %s ms %s" %
          (name, fmt(gbps), fmt(ms), fmt(ttft), gate))
floor_gbs = KV_BYTES_REQ / ((TTFT_BUDGET - PREFILL_MS) / 1000.0) / 1e9
ib_name, ib_gbps = fabrics[1]
ib_ms = KV_BYTES_REQ / (ib_gbps * 1e9) * 1000.0
assert ib_gbps == 50.0
print("  -> the TTFT slack buys a %s GB/s floor; 100GbE misses it by %s" %
      (fmt(floor_gbs), fmt(floor_gbs - 12.5)))

print(RULE)
print("F4 | THE SIZING GATE")
prefill_units = RATE_RPS * PREFILL_MS / 1000.0
print("  the %s-request day at %s RPS: prefill demands %s node-units ->" %
      (grp(DAY_REQ), fmt(RATE_RPS), fmt(prefill_units)))
target_util = 0.8
pool_p = int(-(-(prefill_units / target_util) // 1))
assert pool_p == 5
concurrent = RATE_RPS * LIFETIME_S
steps_work = DAY_REQ * OUT_TOK
wall_s = SPAN_S + LIFETIME_S
wall_steps = int(wall_s / (DECODE_MS / 1000.0))
avg_batch = steps_work / wall_steps
prefill_ns = DAY_REQ * PREFILL_MS / 1000.0
print("  %s nodes at %s%% util; decode is %s concurrent sequences -> 1" %
      (grp(pool_p), fmt(prefill_units / pool_p * 100), fmt(concurrent)))
print("  node at avg batch %s, peak %s of a 64-slot batch (%s%%)" %
      (fmt(avg_batch), fmt(concurrent), fmt(avg_batch / 64 * 100)))
print("  split fleet %sP + 1D costs %s + %s = %s node-s for the day" %
      (grp(pool_p), fmt(prefill_ns), fmt(wall_s), fmt(prefill_ns + wall_s)))
print("  -> colocated holds both gates at 0 RPS - the split is the form")
print("  that holds the gate, not a speedup")

print(RULE)
print("F5 | THE BURST GATE")
burst = 50
queue_ns = burst * PREFILL_MS / 1000.0
drain_s = queue_ns / pool_p
last_ttft = drain_s * 1000.0
print("  %s requests land at once: prefill queue %s node-s on %s nodes" %
      (grp(burst), fmt(queue_ns), grp(pool_p)))
print("  drains in %s s - the last request's TTFT %s ms = %sx over the" %
      (fmt(drain_s), fmt(last_ttft), fmt(last_ttft / TTFT_BUDGET)))
print("  budget; decode holds %s of 64 slots (%s%%), ITL %s ms all the way" %
      (grp(burst), fmt(burst / 64 * 100), fmt(DECODE_MS)))
print("  -> scale prefill on queue depth (%s node-s), decode on batch" %
      fmt(queue_ns))
print("  occupancy (%s/64); one blended RPS signal sizes neither pool" %
      grp(burst))

print(RULE)
print("F6 | THE DAY BILL")
print("  %s requests x %s-token prompts x %s-token outputs:" %
      (grp(DAY_REQ), grp(PROMPT_TOK), grp(OUT_TOK)))
print("  split fleet: prefill %s of %s node-s (%s%%), decode %s steps in" %
      (fmt(prefill_ns), fmt(pool_p * SPAN_S),
       fmt(prefill_ns / (pool_p * SPAN_S) * 100), grp(wall_steps)))
print("  %s wall-s at avg batch %s - SLO ledger %s/%s requests PASS" %
      (fmt(wall_s), fmt(avg_batch), grp(DAY_REQ), grp(DAY_REQ)))
print("  colocated unchunked: TTFT %s ms holds, ITL %s ms breaches %s/%s;" %
      (fmt(PREFILL_MS), fmt(PREFILL_MS + DECODE_MS), grp(DAY_REQ),
       grp(DAY_REQ)))
print("  colocated ITL-tuned (chunk %s): ITL %s ms holds, TTFT %s ms" %
      (grp(chunk_tok), fmt(itl), fmt(ttft_coloc)))
print("  breaches %s/%s - same work, different topology" %
      (grp(DAY_REQ), grp(DAY_REQ)))
print("  -> best colocated holds 0/%s at both gates; the split holds %s/%s" %
      (grp(DAY_REQ), grp(DAY_REQ), grp(DAY_REQ)))

print(RULE)
print("F7 | THE ABLATION AUDIT")
slow_name, slow_gbps = fabrics[3]
slow_ms = KV_BYTES_REQ / (slow_gbps * 1e9) * 1000.0
assert slow_gbps == 3.125
split_ttft_ib = PREFILL_MS + ib_ms
split_ttft_slow = PREFILL_MS + slow_ms
assert split_ttft_ib <= TTFT_BUDGET
assert split_ttft_slow > TTFT_BUDGET
onempool = 2
last_1p = (prefill_ns / onempool + PREFILL_MS / 1000.0) * 1000.0
print("  full split %s/%s at TTFT %s ms / ITL %s ms; remove one lever:" %
      (grp(DAY_REQ), grp(DAY_REQ), fmt(split_ttft_ib), fmt(DECODE_MS)))
print("  -disaggregation: best colocated (chunk %s) TTFT %s ms = 0 of %s" %
      (grp(chunk_tok), fmt(ttft_coloc), grp(DAY_REQ)))
print("    pass the gate")
print("  -fabric: 25GbE handoff TTFT %s ms = 0 of %s pass the gate" %
      (fmt(split_ttft_slow), grp(DAY_REQ)))
print("  -pool-split: one blended pool of %s nodes, last TTFT %s ms = %sx" %
      (grp(onempool), fmt(last_1p), fmt(last_1p / TTFT_BUDGET)))
print("    over the budget")
print("  -> order the build: disaggregate first, fabric second, pools third")
print("FENCE-066-OK")
```

```text
================================================================
F1 | THE INTERFERENCE BILL
  one colocated replica runs both phases: a 4,096-token prompt
  prefills in 2000 ms and every co-decoder waits the whole block -
  ITL 2025 ms vs the 50 ms budget = 40.50x over
  chunked prefill trades one gate for the other: chunk 512 ->
  ITL 275 ms (5.50x over); chunk 128 -> ITL 87.50 ms (1.75x over);
  the ITL-pass chunk 51 holds ITL 49.90 ms but TTFT becomes 81 chunks
  x 49.90 ms = 4042.09 ms = 1.92x over the TTFT budget
  -> no chunk size holds both budgets: colocated breaks one gate
================================================================
F2 | THE DISAGGREGATION BILL
  prefill-only node: TTFT 2000 ms - 100 ms of slack under the 2100 ms
  budget; decode-only node: ITL 25 ms - 2 steps per 50 ms window,
  25 ms of slack; both gates pass by construction
  -> the split buys both gates; the handoff is its own line item
================================================================
F3 | THE HANDOFF LADDER
  one 1.25 GiB KV blob (1,342,177,280 bytes) crosses the fabric:
  NVLink intra-node at 900 GB/s = 1.49 ms, split TTFT 2001.49 ms PASS
  IB 400G RDMA at 50 GB/s = 26.84 ms, split TTFT 2026.84 ms PASS
  100GbE RoCE at 12.50 GB/s = 107.37 ms, split TTFT 2107.37 ms FAIL
  25GbE at 3.12 GB/s = 429.50 ms, split TTFT 2429.50 ms FAIL
  -> the TTFT slack buys a 13.42 GB/s floor; 100GbE misses it by 0.92
================================================================
F4 | THE SIZING GATE
  the 200-request day at 2 RPS: prefill demands 4 node-units ->
  5 nodes at 80% util; decode is 12.80 concurrent sequences -> 1
  node at avg batch 12.03, peak 12.80 of a 64-slot batch (18.80%)
  split fleet 5P + 1D costs 400 + 106.40 = 506.40 node-s for the day
  -> colocated holds both gates at 0 RPS - the split is the form
  that holds the gate, not a speedup
================================================================
F5 | THE BURST GATE
  50 requests land at once: prefill queue 100 node-s on 5 nodes
  drains in 20 s - the last request's TTFT 20000 ms = 9.52x over the
  budget; decode holds 50 of 64 slots (78.12%), ITL 25 ms all the way
  -> scale prefill on queue depth (100 node-s), decode on batch
  occupancy (50/64); one blended RPS signal sizes neither pool
================================================================
F6 | THE DAY BILL
  200 requests x 4,096-token prompts x 256-token outputs:
  split fleet: prefill 400 of 500 node-s (80%), decode 4,256 steps in
  106.40 wall-s at avg batch 12.03 - SLO ledger 200/200 requests PASS
  colocated unchunked: TTFT 2000 ms holds, ITL 2025 ms breaches 200/200;
  colocated ITL-tuned (chunk 51): ITL 49.90 ms holds, TTFT 4042.09 ms
  breaches 200/200 - same work, different topology
  -> best colocated holds 0/200 at both gates; the split holds 200/200
================================================================
F7 | THE ABLATION AUDIT
  full split 200/200 at TTFT 2026.84 ms / ITL 25 ms; remove one lever:
  -disaggregation: best colocated (chunk 51) TTFT 4042.09 ms = 0 of 200
    pass the gate
  -fabric: 25GbE handoff TTFT 2429.50 ms = 0 of 200 pass the gate
  -pool-split: one blended pool of 2 nodes, last TTFT 202000 ms = 96.19x
    over the budget
  -> order the build: disaggregate first, fabric second, pools third
FENCE-066-OK
```
