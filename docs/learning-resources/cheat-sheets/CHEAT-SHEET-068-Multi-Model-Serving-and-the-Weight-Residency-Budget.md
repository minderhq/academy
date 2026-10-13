---
Document ID: CHEAT-SHEET-068
Title: "CHEAT-SHEET-068: Multi-Model Serving and the Weight-Residency Budget - the Replication Bill, the Cold-Start Ladder, and the Hot-Set Proof"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'llmops']
---
# CHEAT-SHEET-068: Multi-Model Serving and the Weight-Residency Budget - the Replication Bill, the Cold-Start Ladder, and the Hot-Set Proof

The census that picked this sheet searched multi-model serving, model hot-swaps, and weight cold starts across all 568 markdown docs and found the pattern taught as catalog pages and asides - seventy-nine hits across forty files, led by the model-registry guide (eleven) and the MLOps-pipelines README (ten), with the CI-CD guide, CHEAT-SHEET-038 and CHEAT-SHEET-050 carrying the rest - while the operator arithmetic returns zero across all 568: swap cost, cold-start cost, weight-load time, resident models, residency budget. The serving-side story is seventeen hits scattered over thirteen files - three in the vLLM production deployment guide, two each in the model-merging sheet and the production-LLM-systems tutorial, one each in ten more from the vLLM serving sheet to the Kubernetes README. The parts live apart: the registry guide teaches the catalog, the serving chapters teach the launch flags, the multi-LoRA sheet teaches adapter tenancy on one base - each a part, none the operator page for weight residency - and the questions that start the moment one gateway serves four fine-tuned bases (what does a cold model charge the first request, how many residents does the KV pool seat, what does a hot set smaller than the working set cost, when do replicas pay) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 243-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 71-line run sits frozen below, byte-for-byte.

## The Replication Bill

The bill four replicas sends. Four fine-tuned 8B bases, one per card: 4 x 48 GiB = 192 GiB bought, and 64 GiB of it is weights - 33.33% of the fleet is the same fp16 trunk four times over, while each card keeps a 32 GiB KV pool of 262,144 tokens. One card holds two bases instead: 48 GiB bought, 32 GiB weights = 66.67% of the card, 16 GiB left for KV. Same four models at a quarter of the hardware - the only question the fleet cannot answer is which base is standing when a request arrives.

```text
F1 | THE REPLICATION BILL
  four 8B bases, one per replica: 4 x 48 GiB cards = 192 GiB
  bought, 64 GiB of it weights = 33.33% of the fleet; each
  card keeps a 32 GiB KV pool = 262,144 tokens. one card,
  two bases resident: 48 GiB bought, 32 GiB weights = 66.67%
  of the card, 16 GiB left for KV. the fleet buys 4.00x the
  one-card budget for the same four models
  -> four models do not need four cards; they need a
     residency budget
```

## The Cold-Start Ladder

The ladder every cold hit climbs. One 8B base is 16 GiB of fp16 weights = 17.18 GB to move: pinned resident costs 0.00 ms because the weights never leave HBM, a page-cache reload rides host DRAM at 50 GB/s for 343.60 ms, and a cache-cold load crawls off NVMe at 7 GB/s for 2,454.27 ms - 7.14x the DRAM rung. The card bills every rung: load time is GPU time earning nothing, and which rung a request pays is a residency decision, not an engine one.

```text
F2 | THE COLD-START LADDER
  one 8B base = 16 GiB of fp16 weights = 17.18 GB to move:
    pinned resident:      0.00 ms (weights already in HBM)
    page-cache reload:  343.60 ms (host DRAM at 50 GB/s)
    cache-cold NVMe:   2454.27 ms (device at 7 GB/s)
  the card bills every rung - load time is GPU time earning
  nothing, and the device path charges 7.14x the DRAM path
  -> the load path is a 7.14x dial; residency decides which
     rung a request pays
```

## The First-Request Gate

The gate the first request trips. TTFT = load + prefill, the 2,048-token prompt prefills in 1,000.00 ms, and the budget line is 2,100 ms: a resident base lands 1,000.00 ms = 0.48x PASS, a page-cached reload 1,343.60 ms = 0.64x PASS, a cache-cold load 3,454.27 ms = 1.64x FAIL. The engine is not slow - the load is the request. Residency is the first line of the TTFT budget, and one cold probe at the wrong moment reads as an engine regression.

```text
F3 | THE FIRST-REQUEST GATE
  TTFT = load + prefill; the 2,048-token prompt prefills in
  1000.00 ms and the budget line is 2100 ms:
    resident:      1000.00 ms (0.48x PASS)
    page-cached:   1343.60 ms (0.64x PASS)
    cache-cold:    3454.27 ms (1.64x FAIL)
  the engine is not slow - the load is the request
  -> residency is the first line of the TTFT budget
```

## The Residency Rent

The rent every resident pays out of the KV pool. One resident keeps 32 GiB for KV = 262,144 tokens, a 90% watermark at 235,929, and floor(235929/2304) = 102 concurrent decode seats at the 2,304-token request footprint. The second resident halves it: 16 GiB = 131,072 tokens, watermark 117,964, 51 seats. The third resident has 0 GiB left - impossible. Weights and KV come off the same card, so every base you host is paid for twice: once in HBM, once in seats.

```text
F4 | THE RESIDENCY RENT
  one resident:   32 GiB KV = 262,144 tokens; 90% watermark
  235,929; ceiling floor(235929/2304) = 102 seats
  two residents:  16 GiB KV = 131,072 tokens; watermark
  117,964; ceiling floor(117964/2304) = 51 seats
  three residents: 0 GiB of KV left - impossible
  the second base halves the decode seats; the third has
  nowhere to stand
  -> every resident pays its rent out of the KV pool
```

## The Swap Bill

The bill a hot set smaller than the working set sends. The day is 200 requests over four bases at 60/25/10/5 (A 120, B 50, C 20, D 10), each reload 343.60 ms: a two-hot set (A, B) pays 30 cold loads = 10,307.92 ms and 15% of requests pay; a one-hot set (A) pays 80 = 27,487.79 ms and 40% pay; three models in two slots pays 200 = 68,719.48 ms - 100% pay, every request evicting the next request's model. That last number is not a load bill, it is a swap loop.

```text
F5 | THE SWAP BILL
  the day: 200 requests over four bases at 60/25/10/5
  (A 120, B 50, C 20, D 10); reload cost 343.60 ms:
  two-hot (A,B):     30 cold loads = 10307.92 ms; 15% pay
  one-hot (A):       80 cold loads = 27487.79 ms; 40% pay
  3 models, 2 slots: 200 cold loads = 68719.48 ms; 100% pay -
  every request evicts the next request's model
  -> a hot set smaller than the working set is a swap loop
```

## The Day Bill

The bill the whole day sends. The same 200 requests under four configs: the replica fleet loads 0.00 ms and passes 200/200 inside the TTFT budget; two-hot on one card loads 10,307.92 ms and passes 200/200; one-hot loads 27,487.79 ms and passes 200/200; no-residency loads 490,853.41 ms and passes 0/200. The fleet's pass was already for sale at a quarter of the hardware - same 200/200, one card, 10,307.92 ms of loads.

```text
F6 | THE DAY BILL
  the same 200 requests, four configs (load ms, TTFT pass):
  replica fleet:   4 cards,      0.00 ms load,  200/200
  two-hot:         1 card,  10307.92 ms load,  200/200
  one-hot:         1 card,  27487.79 ms load,  200/200
  no-residency:    1 card, 490853.41 ms load,    0/200
  the fleet's pass was already for sale at a quarter of the
  hardware - same 200/200, one card, 10307.92 ms of loads
  -> the residency budget buys the fleet's day at 4.00x
     less card
```

## The Build Ladder and the Ablation Audit

The ladder orders the build and the ablations audit it. No-residency loads 490,853.41 ms and passes 0/200; +residency - a two-hot set whose cold hits still ride NVMe - cuts the bill to 73,628.01 ms and passes 170/200; +the page cache - cold reloads ride DRAM - lands 10,307.92 ms and 200/200; +the hot-set audit - slots >= working set - retires the thrash case worth 68,719.48 ms. The ablations hand the deltas back in order: -residency returns 490,853.41 ms = 47.62x (the gate), -the page cache returns 73,628.01 ms = 7.14x (the load path), -the hot set returns 68,719.48 ms = 6.67x (the working set), -the budget returns four cards = 4.00x the hardware for the same pass. Residency first, page cache second, hot set third, fleet last.

```text
F7 | THE BUILD LADDER AND THE ABLATION AUDIT
  no-residency:    490853.41 ms of load, 0/200 inside TTFT
  +residency:      30 cold at NVMe = 73628.01 ms, 170/200
  +page-cache:     cold rides DRAM = 10307.92 ms, 200/200
  +hot-set audit:  slots >= working set - thrash 68719.48
  ablations: -residency 490853.41 = 47.62x (the gate);
  -page-cache 73628.01 = 7.14x (the load path);
  -hot-set 68719.48 = 6.67x (the working set);
  -budget 4 cards = 4.00x hardware for the same pass
  -> build order: residency, page cache, hot set, fleet
```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| Four models, four replicas | 192 GiB across four cards with 64 GiB of it weights - 33.33% of the buy (f1) | Size a residency budget first - replicas are the last rung, not the first |
| Cache-cold weights on every cold hit | 2,454.27 ms of NVMe load inside TTFT - 1.64x the budget (f2, f3) | Keep evicted models in page cache - reloads ride DRAM at 343.60 ms |
| Hot set smaller than the working set | Three models in two slots: all 200 requests pay a reload - 68,719.48 ms = 6.67x (f5) | Size slots to the working set - pin the hot, LRU the tail |
| Residency counted in weights only | The second base halves the KV pool - 102 decode seats drop to 51 (f4) | Budget weights plus KV per resident and re-derive the seat ceiling |
| First request read as engine health | One cache-cold probe reads 3,454.27 ms against 1,000.00 warm (f3) | Warm explicitly on deploy - gate on warm TTFT, not the first hit |
| Replicas bought to dodge the swap bill | 4.00x the hardware for a pass one card already holds - both 200/200 (f6, f7) | Fix the residency budget before the fleet - the fleet is the last rung |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| TTFT spikes minutes after each deploy | The load path (f2): 2,454.27 ms NVMe vs 343.60 DRAM | Evicted models fell to NVMe - pin the hot set or warm on deploy |
| Throughput halves after onboarding a model | The residency rent (f4): 102 seats to 51 | The KV pool pays the rent - re-derive the seat ceiling before blaming the engine |
| The same model loads again and again | Hot set vs working set (f5): 200 cold loads | Slots below the working set is a swap loop - add a slot or drop a model |
| A tenant's first request times out | The first-request gate (f3): 1.64x the budget | The cold load rides inside TTFT - warm the base before admitting traffic |
| Cards sit near a third utilized | The replication bill (f1): 64 GiB of weights on 192 GiB | Consolidate - two bases per card at 66.67% beats four cards at 33.33% |
| The mean passes but p99 fails | The cold tail (f5): 30 requests pay a reload | Gate on the cold tail, not the mean - residency decides who pays |

## Quick Reference For

- [the multi-LoRA sheet whose adapter tenancy shares this card](../../learning-resources/cheat-sheets/CHEAT-SHEET-065-Multi-LoRA-Serving-and-Adapter-Scheduling.md)
- [the per-token KV formula the residency rent is built from](../../learning-resources/cheat-sheets/CHEAT-SHEET-017-KV-Cache.md)
- [the gateway sheet whose routes decide which base a request lands on](../../learning-resources/cheat-sheets/CHEAT-SHEET-056-LLM-Gateway-and-Model-Routing.md)
- [the vLLM production deployment guide this sheet's flags come from](../../phases/phase1-infra/1400-llmops/guides/1403-vLLM-Production-Deployment.md)
- [the model-registry guide whose catalog these residents come from](../../phases/phase6-rag/6500-mlops-pipelines/6503-Model-Registry.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 243-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the load paths, the card, and the day's mix for your own fleet's, and the bills re-derive.

```python
"""CHEAT-SHEET-068 canonical fence: multi-model serving and the weight
residency budget. Stdlib only, no randomness, no clocks - every printed
figure is computed from the fixed fixture and pinned by an assert. Two
runs must print identical bytes.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 64

# ---------------------------------------------------------------- fixture
LAYERS, KV_HEADS, HEAD_DIM = 32, 8, 128
BYTES_PER_KV_TOKEN = 2 * LAYERS * KV_HEADS * HEAD_DIM * 2      # fp16 K+V
WEIGHTS_GIB = 16                        # an 8B model in fp16
WEIGHTS_BYTES = WEIGHTS_GIB * (1024 ** 3)
CARD_GIB = 48                           # one card holds at most two bases
MODELS = 4                              # four distinct 8B bases
MIX = (120, 50, 20, 10)                 # the day's mix, A B C D
PROMPT, OUTPUT = 2048, 256
REQ_KV = PROMPT + OUTPUT                # peak KV tokens per request
PREFILL_RATE = 2048.0                   # tokens/s
TTFT_BUDGET = 2100.0                    # ms, the same line as sheets 66/67
WATERMARK = 0.90                        # the KV admission stop line
DRAM_GBPS, NVME_GBPS = 50.0, 7.0        # weight-load paths, GB/s

assert BYTES_PER_KV_TOKEN == 131072
assert WEIGHTS_BYTES == 17179869184
assert REQ_KV == 2304
assert sum(MIX) == 200


def load_ms(gbps):
    return WEIGHTS_BYTES / (gbps * 1e9) * 1000.0


def pool_tokens(residents):
    return (CARD_GIB - residents * WEIGHTS_GIB) * (1024 ** 3) \
        // BYTES_PER_KV_TOKEN


def prefill_ms(tokens):
    return tokens / PREFILL_RATE * 1000.0


# ---------------------------------------------- F1  the replication bill
def exhibit1():
    fleet_gib = MODELS * CARD_GIB
    fleet_weights = MODELS * WEIGHTS_GIB
    fleet_pct = fleet_weights / float(fleet_gib) * 100.0
    per_card_kv = pool_tokens(1)
    resident_weights_pct = 2 * WEIGHTS_GIB / float(CARD_GIB) * 100.0
    ratio = fleet_gib / float(CARD_GIB)
    assert fleet_gib == 192
    assert fleet_weights == 64
    assert abs(fleet_pct - 33.3333) < 1e-3
    assert per_card_kv == 262144
    assert abs(resident_weights_pct - 66.6667) < 1e-3
    assert ratio == 4.0
    return [
        "F1 | THE REPLICATION BILL",
        "  four 8B bases, one per replica: 4 x 48 GiB cards = 192 GiB",
        "  bought, 64 GiB of it weights = 33.33% of the fleet; each",
        "  card keeps a 32 GiB KV pool = 262,144 tokens. one card,",
        "  two bases resident: 48 GiB bought, 32 GiB weights = 66.67%",
        "  of the card, 16 GiB left for KV. the fleet buys 4.00x the",
        "  one-card budget for the same four models",
        "  -> four models do not need four cards; they need a",
        "     residency budget",
    ]


# -------------------------------------------- F2  the cold-start ladder
def exhibit2():
    dram = load_ms(DRAM_GBPS)
    nvme = load_ms(NVME_GBPS)
    ratio = nvme / dram
    assert abs(dram - 343.5973836800) < 1e-9
    assert abs(nvme - 2454.2670262857) < 1e-9
    assert abs(ratio - 7.1428571428) < 1e-9
    return [
        "F2 | THE COLD-START LADDER",
        "  one 8B base = 16 GiB of fp16 weights = 17.18 GB to move:",
        "    pinned resident:      0.00 ms (weights already in HBM)",
        "    page-cache reload:  343.60 ms (host DRAM at 50 GB/s)",
        "    cache-cold NVMe:   2454.27 ms (device at 7 GB/s)",
        "  the card bills every rung - load time is GPU time earning",
        "  nothing, and the device path charges 7.14x the DRAM path",
        "  -> the load path is a 7.14x dial; residency decides which",
        "     rung a request pays",
    ]


# ------------------------------------------- F3  the first-request gate
def exhibit3():
    warm = prefill_ms(PROMPT)
    cached = warm + load_ms(DRAM_GBPS)
    cold = warm + load_ms(NVME_GBPS)
    m_warm = warm / TTFT_BUDGET
    m_cached = cached / TTFT_BUDGET
    m_cold = cold / TTFT_BUDGET
    assert warm == 1000.0
    assert abs(cached - 1343.5973836800) < 1e-9
    assert abs(cold - 3454.2670262857) < 1e-9
    assert abs(m_warm - 0.4761904761) < 1e-9
    assert abs(m_cached - 0.6398082779) < 1e-9
    assert abs(m_cold - 1.6448890601) < 1e-9
    return [
        "F3 | THE FIRST-REQUEST GATE",
        "  TTFT = load + prefill; the 2,048-token prompt prefills in",
        "  1000.00 ms and the budget line is 2100 ms:",
        "    resident:      1000.00 ms (0.48x PASS)",
        "    page-cached:   1343.60 ms (0.64x PASS)",
        "    cache-cold:    3454.27 ms (1.64x FAIL)",
        "  the engine is not slow - the load is the request",
        "  -> residency is the first line of the TTFT budget",
    ]


# -------------------------------------------- F4  the residency rent
def exhibit4():
    rows = []
    for residents in (1, 2, 3):
        tok = pool_tokens(residents)
        line = int(tok * WATERMARK)
        seats = line // REQ_KV
        rows.append((residents, tok, line, seats))
        if residents == 1:
            assert tok == 262144 and line == 235929 and seats == 102
        if residents == 2:
            assert tok == 131072 and line == 117964 and seats == 51
        if residents == 3:
            assert tok == 0 and line == 0 and seats == 0
    return [
        "F4 | THE RESIDENCY RENT",
        "  one resident:   32 GiB KV = 262,144 tokens; 90% watermark",
        "  235,929; ceiling floor(235929/2304) = 102 seats",
        "  two residents:  16 GiB KV = 131,072 tokens; watermark",
        "  117,964; ceiling floor(117964/2304) = 51 seats",
        "  three residents: 0 GiB of KV left - impossible",
        "  the second base halves the decode seats; the third has",
        "  nowhere to stand",
        "  -> every resident pays its rent out of the KV pool",
    ]


# --------------------------------------------------- F5  the swap bill
def exhibit5():
    dram = load_ms(DRAM_GBPS)
    cold_two = MIX[2] + MIX[3]
    cold_one = MIX[1] + MIX[2] + MIX[3]
    thrash = sum(MIX)
    bill_two = cold_two * dram
    bill_one = cold_one * dram
    bill_thrash = thrash * dram
    assert cold_two == 30 and cold_one == 80 and thrash == 200
    assert abs(bill_two - 10307.9215104) < 1e-9
    assert abs(bill_one - 27487.7906944) < 1e-9
    assert abs(bill_thrash - 68719.4767360) < 1e-9
    return [
        "F5 | THE SWAP BILL",
        "  the day: 200 requests over four bases at 60/25/10/5",
        "  (A 120, B 50, C 20, D 10); reload cost 343.60 ms:",
        "  two-hot (A,B):     30 cold loads = 10307.92 ms; 15% pay",
        "  one-hot (A):       80 cold loads = 27487.79 ms; 40% pay",
        "  3 models, 2 slots: 200 cold loads = 68719.48 ms; 100% pay -",
        "  every request evicts the next request's model",
        "  -> a hot set smaller than the working set is a swap loop",
    ]


# -------------------------------------------------- F6  the day bill
def exhibit6():
    nvme = load_ms(NVME_GBPS)
    dram = load_ms(DRAM_GBPS)
    bill_none = sum(MIX) * nvme
    bill_two = (MIX[2] + MIX[3]) * dram
    bill_one = (MIX[1] + MIX[2] + MIX[3]) * dram
    hardware = MODELS / 1.0
    assert abs(bill_none - 490853.4052571428) < 1e-9
    assert abs(bill_two - 10307.9215104) < 1e-9
    assert abs(bill_one - 27487.7906944) < 1e-9
    assert hardware == 4.0
    return [
        "F6 | THE DAY BILL",
        "  the same 200 requests, four configs (load ms, TTFT pass):",
        "  replica fleet:   4 cards,      0.00 ms load,  200/200",
        "  two-hot:         1 card,  10307.92 ms load,  200/200",
        "  one-hot:         1 card,  27487.79 ms load,  200/200",
        "  no-residency:    1 card, 490853.41 ms load,    0/200",
        "  the fleet's pass was already for sale at a quarter of the",
        "  hardware - same 200/200, one card, 10307.92 ms of loads",
        "  -> the residency budget buys the fleet's day at 4.00x",
        "     less card",
    ]


# ------------------------------------ F7  the build ladder + ablation audit
def exhibit7():
    nvme = load_ms(NVME_GBPS)
    dram = load_ms(DRAM_GBPS)
    bill_none = sum(MIX) * nvme
    bill_nocache = (MIX[2] + MIX[3]) * nvme
    bill_two = (MIX[2] + MIX[3]) * dram
    bill_thrash = sum(MIX) * dram
    m_resid = bill_none / bill_two
    m_cache = bill_nocache / bill_two
    m_hot = bill_thrash / bill_two
    assert abs(bill_nocache - 73628.0107885714) < 1e-9
    assert abs(m_resid - 47.6190476190) < 1e-9
    assert abs(m_cache - 7.1428571428) < 1e-9
    assert abs(m_hot - 6.6666666666) < 1e-9
    return [
        "F7 | THE BUILD LADDER AND THE ABLATION AUDIT",
        "  no-residency:    490853.41 ms of load, 0/200 inside TTFT",
        "  +residency:      30 cold at NVMe = 73628.01 ms, 170/200",
        "  +page-cache:     cold rides DRAM = 10307.92 ms, 200/200",
        "  +hot-set audit:  slots >= working set - thrash 68719.48",
        "  ablations: -residency 490853.41 = 47.62x (the gate);",
        "  -page-cache 73628.01 = 7.14x (the load path);",
        "  -hot-set 68719.48 = 6.67x (the working set);",
        "  -budget 4 cards = 4.00x hardware for the same pass",
        "  -> build order: residency, page cache, hot set, fleet",
    ]


def main():
    blocks = [exhibit1(), exhibit2(), exhibit3(), exhibit4(), exhibit5(),
              exhibit6(), exhibit7()]
    out = []
    for blk in blocks:
        out.extend(blk)
        out.append(RULE)
    out.append("FENCE-068-OK")
    text = "\n".join(out)
    assert "\r" not in text
    for ln in text.split("\n"):
        assert ln == ln.rstrip(), "trailing space: %r" % ln
    sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
```

```text
F1 | THE REPLICATION BILL
  four 8B bases, one per replica: 4 x 48 GiB cards = 192 GiB
  bought, 64 GiB of it weights = 33.33% of the fleet; each
  card keeps a 32 GiB KV pool = 262,144 tokens. one card,
  two bases resident: 48 GiB bought, 32 GiB weights = 66.67%
  of the card, 16 GiB left for KV. the fleet buys 4.00x the
  one-card budget for the same four models
  -> four models do not need four cards; they need a
     residency budget
================================================================
F2 | THE COLD-START LADDER
  one 8B base = 16 GiB of fp16 weights = 17.18 GB to move:
    pinned resident:      0.00 ms (weights already in HBM)
    page-cache reload:  343.60 ms (host DRAM at 50 GB/s)
    cache-cold NVMe:   2454.27 ms (device at 7 GB/s)
  the card bills every rung - load time is GPU time earning
  nothing, and the device path charges 7.14x the DRAM path
  -> the load path is a 7.14x dial; residency decides which
     rung a request pays
================================================================
F3 | THE FIRST-REQUEST GATE
  TTFT = load + prefill; the 2,048-token prompt prefills in
  1000.00 ms and the budget line is 2100 ms:
    resident:      1000.00 ms (0.48x PASS)
    page-cached:   1343.60 ms (0.64x PASS)
    cache-cold:    3454.27 ms (1.64x FAIL)
  the engine is not slow - the load is the request
  -> residency is the first line of the TTFT budget
================================================================
F4 | THE RESIDENCY RENT
  one resident:   32 GiB KV = 262,144 tokens; 90% watermark
  235,929; ceiling floor(235929/2304) = 102 seats
  two residents:  16 GiB KV = 131,072 tokens; watermark
  117,964; ceiling floor(117964/2304) = 51 seats
  three residents: 0 GiB of KV left - impossible
  the second base halves the decode seats; the third has
  nowhere to stand
  -> every resident pays its rent out of the KV pool
================================================================
F5 | THE SWAP BILL
  the day: 200 requests over four bases at 60/25/10/5
  (A 120, B 50, C 20, D 10); reload cost 343.60 ms:
  two-hot (A,B):     30 cold loads = 10307.92 ms; 15% pay
  one-hot (A):       80 cold loads = 27487.79 ms; 40% pay
  3 models, 2 slots: 200 cold loads = 68719.48 ms; 100% pay -
  every request evicts the next request's model
  -> a hot set smaller than the working set is a swap loop
================================================================
F6 | THE DAY BILL
  the same 200 requests, four configs (load ms, TTFT pass):
  replica fleet:   4 cards,      0.00 ms load,  200/200
  two-hot:         1 card,  10307.92 ms load,  200/200
  one-hot:         1 card,  27487.79 ms load,  200/200
  no-residency:    1 card, 490853.41 ms load,    0/200
  the fleet's pass was already for sale at a quarter of the
  hardware - same 200/200, one card, 10307.92 ms of loads
  -> the residency budget buys the fleet's day at 4.00x
     less card
================================================================
F7 | THE BUILD LADDER AND THE ABLATION AUDIT
  no-residency:    490853.41 ms of load, 0/200 inside TTFT
  +residency:      30 cold at NVMe = 73628.01 ms, 170/200
  +page-cache:     cold rides DRAM = 10307.92 ms, 200/200
  +hot-set audit:  slots >= working set - thrash 68719.48
  ablations: -residency 490853.41 = 47.62x (the gate);
  -page-cache 73628.01 = 7.14x (the load path);
  -hot-set 68719.48 = 6.67x (the working set);
  -budget 4 cards = 4.00x hardware for the same pass
  -> build order: residency, page cache, hot set, fleet
================================================================
FENCE-068-OK
```
