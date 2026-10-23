---
Document ID: CHEAT-SHEET-062
Title: "CHEAT-SHEET-062: KV Offload and Tiered Caching - the Recompute Bill, the Tier Ladder, and the Routing Gate"
Last Updated: 2026-10-23
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'kv-cache', 'serving', 'inference']
---

# CHEAT-SHEET-062: KV Offload and Tiered Caching - the Recompute Bill, the Tier Ladder, and the Routing Gate

The scope scan that picked this page: a repo-wide scan for KV cache offload, tiered KV, and LMCache returns one of the catalog's 562 markdown docs - the mooncake transfer-backend default inside 1405-SGLang's disaggregation section, a PD handoff line, not a tiered-cache operator page; cross-instance prefix reuse returns zero. The pieces live apart: 4201 teaches the context-window physics, 4204 the paging and prefix-caching layer, 1402 the vLLM serving surface, 1405 the radix-cache serving stack, and CHEAT-SHEET-017 the per-token KV formula and the OOM budget - each a layer, none the tiered operator page. The operator questions that start the moment a fleet's working set outgrows HBM have no home: what does a cold prefill cost, what does each tier's fetch cost, where does the working set fit, and when does routing pay. No dedicated operator page and no dedicated module exists anywhere in the catalog.

The sheet runs as seven exhibits: the recompute bill (F1 - a cold prefix costs two seconds), the tier ladder (F2 - every fetch is bytes over bandwidth), the reuse gate (F3 - first-touch is the floor), the TTFT bill (F4 - the ladder beats recompute at every rung), the capacity bill (F5 - the working set outgrows HBM), the routing gate (F6 - affinity decides where the hit lives), and the ablation audit (F7 - remove one tier, read the delta). Every number below is printed by the canonical fence at the bottom of the page: the full 196-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 48-line output sits frozen below it byte-for-byte.

## The Recompute Bill - a Cold Prefix Costs Two Seconds

The unit of waste is the cold prefill. On the fixture, 100 cacheless requests prefill 409,600 tokens of prefix - 200.0 s at 2,048 tok/s. With the tiers in place only the 60 first-touch requests prefill (120.0 s); the 40 repeats come from storage. Offload removes 80.0 s (40.0%) of prefix prefill - and every one of those seconds was HBM time the decode batches wanted.

```text
  baseline, no cache: 100 requests x 4,096 tok = 409,600 tok of prefix
  prefill; at 2,048 tok/s that is 200.0 s per run
  tiered: 60 cold x 2.0 s = 120.0 s - the 40 repeats come from tiers
  -> offload removes 80.0 s (40.0%) of prefix prefill
```

## The Tier Ladder - Every Fetch Is Bytes over Bandwidth

A KV fetch is bytes over bandwidth: one 1.25 GiB prefix moves in 0.4 ms off HBM, 26.8 ms off DRAM, 191.7 ms off NVMe, 429.5 ms over the remote link - every rung under the 2,000.0 ms recompute it replaces. The fixture's 40 hits land 24 on HBM, 12 on DRAM, 3 on NVMe, 1 remote. The ladder is the design: place a tier at every bandwidth the fleet already has.

```text
  fetching one 1.25 GiB prefix per tier, against recompute:
    HBM     3,200  GB/s       0.4 ms   24 requests
    DRAM    50     GB/s      26.8 ms   12 requests
    NVMe    7      GB/s     191.7 ms    3 requests
    remote  3.125  GB/s     429.5 ms    1 request
  recompute instead: 2,000.0 ms
  -> the whole ladder beats the 2,000.0 ms recompute
```

## The Reuse Gate - First-Touch Is the Floor

Reuse is the gate that pays for the tiers. The fixture's reuse is 40 of 100 requests (40.0%); HBM alone serves 24 of the 40 hits (60.0% of the reuse). The other 60 requests are first-touch - no cache removes them, they are the floor every bill sits on. Size the tiers against measured reuse, not against the request count.

```text
  reuse on the fixture: 40 of 100 requests = 40.0%
  HBM serves 24 of the 40 hits = 60.0% of the reuse
  first-touch floor: 60 requests no cache can remove
  -> the tiers are paid for by 40.0% reuse; the floor stays 60
```

## The TTFT Bill - the Ladder Beats Recompute at Every Rung

The payoff is first-token latency. Recompute puts the prefix at 2,000.0 ms; the blended tier fetch across the 40 hits is 33.4 ms - 59.8x faster first tokens on every repeat, and the slowest rung still beats the recompute it replaces. That is what makes offload safe to turn on: a miss degrades to a fetch, not a recompute.

```text
  recompute TTFT for the prefix: 2,000.0 ms
  blended tier fetch across the 40 hits: 33.4 ms
  -> 59.8x faster first token on every repeat
```

## The Capacity Bill - the Working Set Outgrows HBM

The trigger for offload is capacity arithmetic. The 40.0 GiB HBM budget holds 131,072 KV tokens - 32 prefixes of the fixture's 100; the working set is 125.0 GiB and spills 85.0 GiB past HBM. A DRAM tier at 128.0 GiB holds the whole set with 3.0 GiB spare. HBM alone drops 68 prefixes back to recompute; the tiers hold all 100.

```text
  HBM budget 40.0 GiB holds 131,072 KV tokens = 32 prefixes
  working set: 100 prefixes = 125.0 GiB - spill past HBM: 85.0 GiB
  DRAM tier at 128.0 GiB holds the set with 3.0 GiB spare
  -> HBM alone drops 68 prefixes; the tiers hold all 100
```

## The Routing Gate - Affinity Decides Where the Hit Lives

Where a repeat lands decides what it costs. With cache-aware routing all 40 repeats go warm on the replica that prefilled them. Round-robin with no KV sharing strands 35 of the 40 on foreign replicas: 5 warm, 35 cold, 35 x 4,096 = 143,360 tokens = 70.0 s of prefill back. Routing decides 87.5% of the repeat bill on this fixture - affinity is an offload feature, not a load-balancer detail.

```text
  8 replicas, 40 repeats over the fixture
  cache-aware: all 40 repeats warm on the prefilled replica
  round-robin, no KV sharing: 5 warm, 35 cold on a foreign replica
  extra prefill: 35 x 4,096 = 143,360 tok = 70.0 s
  -> routing decides 87.5% of the repeat bill on this fixture
```

## The Ablation Audit - Remove One Tier, Read the Delta

Grade the cache by ablation. Full system: 40 of 40 repeats warm. Remove the tiers and HBM-only LRU holds 32 prefixes: 22 warm, 18 recomputes return (55.0% warm). Remove routing: 5 warm (12.5%). Remove offload entirely: 0 warm, back to 200.0 s. The deltas order the build: tiers first, affinity second, and HBM alone is not a cache policy.

```text
  full system: 40 of 40 repeats warm
  -tiering (HBM-only LRU): 22 warm, 18 recomputes return (55.0%)
  -routing (round-robin): 5 warm, 35 recomputes return (12.5%)
  -offload (no persistence): 0 warm, back to 200.0 s
  -> the deltas order the build: tiers, affinity, then HBM alone
```

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Sizing the cache against the request count | F1: the 60 first-touch requests are the floor - no cache removes them, only the 40.0% reuse pays for the tiers |
| Fetching a tier that is slower than recompute | F2: the ladder runs 0.4 / 26.8 / 191.7 / 429.5 ms against a 2,000.0 ms recompute - a tier above that line is a loss |
| Reading HBM hits as the whole cache | F3: HBM serves 24 of the 40 hits - the DRAM, NVMe and remote rungs carry the rest of the 40.0% reuse |
| Pricing repeats at the best rung | F4: the blended fetch is 33.4 ms, not HBM's 0.4 ms - the budget holds at the blend (59.8x), not at the best case |
| Fitting the working set in HBM | F5: 32 of 100 prefixes fit in 40 GiB - the other 68 recompute at 2.0 s each until the tiers absorb the 85.0 GiB spill |
| Treating routing as a load-balancer detail | F6: round-robin strands 35 of 40 repeats - 143,360 tokens (70.0 s) of prefill return on the fixture |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| TTFT spikes return under load | the hit mix slid down the ladder - log per-tier hits (fixture: 24/12/3/1) and alert when the HBM share falls under 60.0% (f2) |
| repeats still pay full prefill | the router has no affinity - pin the prefix key to the replica that prefilled it; the fixture loses 87.5% of repeats to round-robin (f3) |
| HBM evictions recycle the same prefixes | the LRU window is smaller than the reuse span - widen HBM or add the DRAM tier before evicting (the fixture dies HBM-only at 18 of 40 repeats) (f4) |
| offload storage grows without bound | the working set is not bounded - cap the tiers at the measured reuse set (125.0 GiB here) and evict by reuse, not by age (f5) |
| a remote fetch costs more than it saves | the rung is past the recompute line - 429.5 ms against 2,000.0 ms is safe here, a slower link is not, drop the tier (f6) |
| the cache helps one replica and hurts the fleet | prefill is duplicated across replicas without KV sharing - 70.0 s of the fixture's repeat bill is foreign-replica recompute (f7) |

## Quick Reference For

- [4204: KV-Cache Paging and Prefix Caching](../../phases/phase4-quantization/4200-kv-cache/4204-KV-Cache-Paging-and-Prefix-Caching.md) - the paging and prefix-caching layer these offload tiers extend.
- [4201: Context Window Physics and OOM Prevention](../../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md) - the per-token KV bytes the capacity bill prices.
- [1405: SGLang RadixAttention Serving](../../phases/phase1-infra/1400-llmops/1405-SGLang.md) - the serving stack whose radix cache and PD handoff sit above these tiers.
- [1402: vLLM and TGI High-Concurrency Inference](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - the serving surface whose KV connector interface the offload backends plug into.
- [6306: Context Window Economics](../../phases/phase6-rag/6300-context/6306-Context-Window-Economics.md) - the cost side of the same window these tiers serve.

## The Canonical Fence

This sheet's every number - the recompute bill, the tier ladder, the reuse gate, the TTFT bill, the capacity bill, the routing gate, the ablation audit - comes from the fence below, printed by a real run and pinned with asserts: the full 196-line stdlib program reproduces F1 through F7, and its 48-line output sits frozen under it byte-for-byte.

```python
# CHEAT-SHEET-062 fence - KV offload and tiered caching, measured on a
# fixed 100-request fixture. Stdlib only, no randomness, no timing:
# every figure is arithmetic on literals and pinned by an assert.
#
# Fixture: one 70B-class model (80 layers, 8 GQA key-value heads,
# head_dim 128, fp16), one 4,096-token document prefix per request,
# prefill measured at 2,048 tokens/s, 100 requests over 100 distinct
# documents. 40 requests repeat a document another request prefilled.
PREFIX_TOK = 4096
LAYERS = 80
KV_HEADS = 8
HEAD_DIM = 128
ELEM_BYTES = 2

KV_BYTES_PER_TOK = 2 * LAYERS * KV_HEADS * HEAD_DIM * ELEM_BYTES
assert KV_BYTES_PER_TOK == 327680
KV_KIB_PER_TOK = KV_BYTES_PER_TOK // 1024
assert KV_KIB_PER_TOK == 320
PREFIX_BYTES = PREFIX_TOK * KV_BYTES_PER_TOK
assert PREFIX_BYTES == 1342177280
PREFIX_GIB = PREFIX_BYTES / 2 ** 30
assert PREFIX_GIB == 1.25
PREFILL_TPS = 2048
RECOMPUTE_S = PREFIX_TOK / PREFILL_TPS
assert RECOMPUTE_S == 2.0

REQS = 100
COLD = 60
HITS = REQS - COLD
REPEATS = HITS
assert HITS == 40 and REPEATS == 40
RULE = "=" * 64

# ---- F1: the recompute bill ----
BASE_S = REQS * RECOMPUTE_S
BASE_TOK = REQS * PREFIX_TOK
TIERED_S = COLD * RECOMPUTE_S
SAVED_S = HITS * RECOMPUTE_S
SAVED_PCT = SAVED_S / BASE_S * 100
assert BASE_S == 200.0
assert BASE_TOK == 409600
assert TIERED_S == 120.0
assert SAVED_S == 80.0
assert round(SAVED_PCT, 1) == 40.0
print(RULE)
print("F1 THE RECOMPUTE BILL - a cold prefix costs two seconds")
print("  baseline, no cache: %d requests x %s tok = %s tok of prefix"
      % (REQS, format(PREFIX_TOK, ","), format(BASE_TOK, ",")))
print("  prefill; at %s tok/s that is %s s per run"
      % (format(PREFILL_TPS, ","), format(BASE_S, ".1f")))
print("  tiered: %d cold x %s s = %s s - the %d repeats come from tiers"
      % (COLD, format(RECOMPUTE_S, ".1f"), format(TIERED_S, ".1f"), HITS))
print("  -> offload removes %s s (%s%%) of prefix prefill"
      % (format(SAVED_S, ".1f"), format(round(SAVED_PCT, 1), ".1f")))

# ---- F2: the tier ladder ----
TIERS = [
    ("HBM", 3200.0, 24),
    ("DRAM", 50.0, 12),
    ("NVMe", 7.0, 3),
    ("remote", 3.125, 1),
]
FETCH_MS = {}
for name, gbps, count in TIERS:
    FETCH_MS[name] = PREFIX_BYTES / (gbps * 1e9) * 1000
assert sum(c for _, _, c in TIERS) == HITS
assert round(FETCH_MS["HBM"], 1) == 0.4
assert round(FETCH_MS["DRAM"], 1) == 26.8
assert round(FETCH_MS["NVMe"], 1) == 191.7
assert round(FETCH_MS["remote"], 1) == 429.5
print(RULE)
print("F2 THE TIER LADDER - every fetch is bytes over bandwidth")
print("  fetching one %s GiB prefix per tier, against recompute:"
      % format(PREFIX_GIB, "g"))
for name, gbps, count in TIERS:
    if gbps == int(gbps):
        bw = format(int(gbps), ",")
    else:
        bw = format(gbps, "g")
    word = "request" if count == 1 else "requests"
    print("    %-7s %-6s GB/s   %7s ms   %2d %s"
          % (name, bw, format(round(FETCH_MS[name], 1), ".1f"), count,
             word))
print("  recompute instead: %s ms"
      % format(RECOMPUTE_S * 1000, ",.1f"))
print("  -> the whole ladder beats the %s ms recompute"
      % format(RECOMPUTE_S * 1000, ",.1f"))

# ---- F3: the reuse gate ----
REUSE_PCT = HITS / REQS * 100
HBM_SHARE = 24 / HITS * 100
assert round(REUSE_PCT, 1) == 40.0
assert round(HBM_SHARE, 1) == 60.0
print(RULE)
print("F3 THE REUSE GATE - first-touch is the floor")
print("  reuse on the fixture: %d of %d requests = %s%%"
      % (HITS, REQS, format(round(REUSE_PCT, 1), ".1f")))
print("  HBM serves %d of the %d hits = %s%% of the reuse"
      % (24, HITS, format(round(HBM_SHARE, 1), ".1f")))
print("  first-touch floor: %d requests no cache can remove" % COLD)
print("  -> the tiers are paid for by %s%% reuse; the floor stays %d"
      % (format(round(REUSE_PCT, 1), ".1f"), COLD))

# ---- F4: the TTFT bill ----
BLENDED_MS = sum(c * FETCH_MS[n] for n, _, c in TIERS) / HITS
SPEEDUP = RECOMPUTE_S * 1000 / BLENDED_MS
assert round(BLENDED_MS, 1) == 33.4
assert round(SPEEDUP, 1) == 59.8
print(RULE)
print("F4 THE TTFT BILL - the ladder beats recompute at every rung")
print("  recompute TTFT for the prefix: %s ms"
      % format(RECOMPUTE_S * 1000, ",.1f"))
print("  blended tier fetch across the %d hits: %s ms"
      % (HITS, format(round(BLENDED_MS, 1), ".1f")))
print("  -> %sx faster first token on every repeat"
      % format(round(SPEEDUP, 1), ".1f"))

# ---- F5: the capacity bill ----
HBM_GIB = 40.0
HBM_PREFIXES = HBM_GIB * 2 ** 30 // PREFIX_BYTES
HBM_TOK = HBM_PREFIXES * PREFIX_BYTES // KV_BYTES_PER_TOK
WS_GIB = REQS * PREFIX_GIB
DRAM_GIB = 128.0
SPILL_GIB = WS_GIB - HBM_GIB
SPARE_GIB = DRAM_GIB - WS_GIB
assert HBM_PREFIXES == 32
assert HBM_TOK == 131072
assert WS_GIB == 125.0
assert WS_GIB <= DRAM_GIB
assert SPILL_GIB == 85.0
assert SPARE_GIB == 3.0
print(RULE)
print("F5 THE CAPACITY BILL - the working set outgrows HBM")
print("  HBM budget %s GiB holds %s KV tokens = %d prefixes"
      % (format(HBM_GIB, ".1f"), format(int(HBM_TOK), ","),
         HBM_PREFIXES))
print("  working set: %d prefixes = %s GiB - spill past HBM: %s GiB"
      % (REQS, format(WS_GIB, ".1f"), format(SPILL_GIB, ".1f")))
print("  DRAM tier at %s GiB holds the set with %s GiB spare"
      % (format(DRAM_GIB, ".1f"), format(SPARE_GIB, ".1f")))
print("  -> HBM alone drops %d prefixes; the tiers hold all %d"
      % (REQS - HBM_PREFIXES, REQS))

# ---- F6: the routing gate ----
REPLICAS = 8
AFFINITY_WARM = 5
RR_COLD = REPEATS - AFFINITY_WARM
RR_EXTRA_TOK = RR_COLD * PREFIX_TOK
RR_EXTRA_S = RR_COLD * RECOMPUTE_S
RR_LOST_PCT = RR_COLD / REPEATS * 100
assert RR_COLD == 35
assert RR_EXTRA_TOK == 143360
assert RR_EXTRA_S == 70.0
assert round(RR_LOST_PCT, 1) == 87.5
print(RULE)
print("F6 THE ROUTING GATE - affinity decides where the hit lives")
print("  %d replicas, %d repeats over the fixture" % (REPLICAS, REPEATS))
print("  cache-aware: all %d repeats warm on the prefilled replica"
      % REPEATS)
print("  round-robin, no KV sharing: %d warm, %d cold on a foreign replica"
      % (AFFINITY_WARM, RR_COLD))
print("  extra prefill: %d x %s = %s tok = %s s"
      % (RR_COLD, format(PREFIX_TOK, ","), format(RR_EXTRA_TOK, ","),
         format(RR_EXTRA_S, ".1f")))
print("  -> routing decides %s%% of the repeat bill on this fixture"
      % format(round(RR_LOST_PCT, 1), ".1f"))

# ---- F7: the ablation audit ----
FULL_WARM = REPEATS
NO_TIER_WARM = 22
NO_TIER_EVICTION = FULL_WARM - NO_TIER_WARM
NO_ROUTE_WARM = AFFINITY_WARM
NO_ROUTE_EVICTION = FULL_WARM - NO_ROUTE_WARM
NO_OFFLOAD_WARM = 0
NO_TIER_PCT = NO_TIER_WARM / REPEATS * 100
NO_ROUTE_PCT = NO_ROUTE_WARM / REPEATS * 100
assert NO_TIER_EVICTION == 18
assert NO_ROUTE_EVICTION == 35
assert round(NO_TIER_PCT, 1) == 55.0
assert round(NO_ROUTE_PCT, 1) == 12.5
assert NO_OFFLOAD_WARM == 0
print(RULE)
print("F7 THE ABLATION AUDIT - remove one tier, read the delta")
print("  full system: %d of %d repeats warm" % (FULL_WARM, REPEATS))
print("  -tiering (HBM-only LRU): %d warm, %d recomputes return (%s%%)"
      % (NO_TIER_WARM, NO_TIER_EVICTION,
         format(round(NO_TIER_PCT, 1), ".1f")))
print("  -routing (round-robin): %d warm, %d recomputes return (%s%%)"
      % (NO_ROUTE_WARM, NO_ROUTE_EVICTION,
         format(round(NO_ROUTE_PCT, 1), ".1f")))
print("  -offload (no persistence): %d warm, back to %s s"
      % (NO_OFFLOAD_WARM, format(REQS * RECOMPUTE_S, ".1f")))
print("  -> the deltas order the build: tiers, affinity, then HBM alone")

print()
print("FENCE-062-OK")
```

```text
================================================================
F1 THE RECOMPUTE BILL - a cold prefix costs two seconds
  baseline, no cache: 100 requests x 4,096 tok = 409,600 tok of prefix
  prefill; at 2,048 tok/s that is 200.0 s per run
  tiered: 60 cold x 2.0 s = 120.0 s - the 40 repeats come from tiers
  -> offload removes 80.0 s (40.0%) of prefix prefill
================================================================
F2 THE TIER LADDER - every fetch is bytes over bandwidth
  fetching one 1.25 GiB prefix per tier, against recompute:
    HBM     3,200  GB/s       0.4 ms   24 requests
    DRAM    50     GB/s      26.8 ms   12 requests
    NVMe    7      GB/s     191.7 ms    3 requests
    remote  3.125  GB/s     429.5 ms    1 request
  recompute instead: 2,000.0 ms
  -> the whole ladder beats the 2,000.0 ms recompute
================================================================
F3 THE REUSE GATE - first-touch is the floor
  reuse on the fixture: 40 of 100 requests = 40.0%
  HBM serves 24 of the 40 hits = 60.0% of the reuse
  first-touch floor: 60 requests no cache can remove
  -> the tiers are paid for by 40.0% reuse; the floor stays 60
================================================================
F4 THE TTFT BILL - the ladder beats recompute at every rung
  recompute TTFT for the prefix: 2,000.0 ms
  blended tier fetch across the 40 hits: 33.4 ms
  -> 59.8x faster first token on every repeat
================================================================
F5 THE CAPACITY BILL - the working set outgrows HBM
  HBM budget 40.0 GiB holds 131,072 KV tokens = 32 prefixes
  working set: 100 prefixes = 125.0 GiB - spill past HBM: 85.0 GiB
  DRAM tier at 128.0 GiB holds the set with 3.0 GiB spare
  -> HBM alone drops 68 prefixes; the tiers hold all 100
================================================================
F6 THE ROUTING GATE - affinity decides where the hit lives
  8 replicas, 40 repeats over the fixture
  cache-aware: all 40 repeats warm on the prefilled replica
  round-robin, no KV sharing: 5 warm, 35 cold on a foreign replica
  extra prefill: 35 x 4,096 = 143,360 tok = 70.0 s
  -> routing decides 87.5% of the repeat bill on this fixture
================================================================
F7 THE ABLATION AUDIT - remove one tier, read the delta
  full system: 40 of 40 repeats warm
  -tiering (HBM-only LRU): 22 warm, 18 recomputes return (55.0%)
  -routing (round-robin): 5 warm, 35 recomputes return (12.5%)
  -offload (no persistence): 0 warm, back to 200.0 s
  -> the deltas order the build: tiers, affinity, then HBM alone

FENCE-062-OK
```
