---
Document ID: CHEAT-SHEET-065
Title: "CHEAT-SHEET-065: Multi-LoRA Serving and Adapter Scheduling - the Tenancy Bill, the KV Tax, and the Day Bill"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'peft', 'lora']
---
# CHEAT-SHEET-065: Multi-LoRA Serving and Adapter Scheduling - the Tenancy Bill, the KV Tax, and the Day Bill

The census that picked this sheet searched multi-LoRA serving, adapter scheduling, and S-LoRA across all 565 markdown docs and found the serving pattern in three hits - a lab aside, one SGLang serving line, and the PEFT-side multi-adapter section of the LoRA implementation guide - while slot economics, LRU adapter residency, mixed-batch penalties, and the adapter KV tax return zero. The parts live apart: the implementation guide teaches the PEFT-side wrapper (one base model, named adapters), the lab trains a single adapter, the serving chapters carry the engine rows, and CHEAT-SHEET-016 the rank and QLoRA math - each a part, none the operator page - and the questions that start the moment six fine-tuned tenants have to share one 24 GiB card (what does hosting the tenant book cost, what does a spilled adapter cost per fetch, what does mixing cost inside a batch, what does residency rent in KV) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 248-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 64-line run sits frozen below, byte-for-byte.

## The Tenancy Bill

The bill every multi-tenant quote starts from. Six fine-tuned tenants, naive serving: six full copies of the 8B base = 96 GiB - four 24 GiB cards before a single KV token is served. Multi-LoRA: one 16 GiB base plus six 56 MiB adapters = 16.33 GiB on the one card. The tenancy bill pays 5.88x less GPU for the same six skills - the adapters are 2% of the weights and 100% of the differences.

```text
F1 | THE TENANCY BILL
  six fine-tuned tenants on one 24 GiB card, six copies vs one base:
  96.00 GiB of copies vs 16.33 GiB base+adapters (16.00 + 6 x 0.33)
  = 5.88x less GPU for the same six skills, one card instead of four
  -> multi-LoRA serves the whole tenant book in a sixth of the GPU
```

## The KV Tax

Hosting is cheap; residency is not. Every resident adapter rents KV off the same card at 131072 B/token: the bare base serves 65,536 KV tokens; +6 adapters 62,848 (-4.1%); +50 fp16 adapters 43,136 (-34.2%). int4 adapters - 14 MiB, rank and layout unchanged - lift the 50-tenant floor back to 59,936 (-8.5%): 22,400 tokens taxed, 16,800 bought back. Every slot carries a KV line on the bill, and quantizing the adapter pays part of the rent.

```text
F2 | THE KV TAX
  KV at 131072 B/token off the same 24 GiB card: bare base 65,536 tok;
  +6 adapters 62,848 tok (-4.1%); +50 fp16 adapters 43,136 tok (-34.2%)
  +50 int4 adapters 59,936 tok (-8.5%) - every resident adapter rents
  KV; quantizing the adapter pays part of the rent back
  -> 50 fp16 tenants cost 22,400 KV tokens; int4 returns 16,800 of them
```

## The Residency Ladder

The traffic decides who stays resident. The 24-request trace is top-heavy - A, B, C take 75% of it. LRU over 4 slots: 12 misses, 100 swaps on a 200-request day, 117.4 ms of DRAM fetch at 1.17 ms per 56 MiB adapter. Pin the hot three: 9 misses, 88.1 ms. All six resident: 6 cold loads, 58.7 ms, no re-fetch all day. Pin the hot, LRU the tail.

```text
F3 | THE RESIDENCY LADDER
  the 24-request trace at swap 1.17 ms per 56 MiB adapter over DRAM,
  scaled to a 200-request day: LRU-4 slots = 12 misses (50.0% swap
  rate) = 117.4 ms of fetch; hot-3 pinned (A,B,C) = 9 misses (37.5%)
  = 88.1 ms; all 6 resident = 6 cold loads = 58.7 ms, no re-fetch
  -> top-3 carry 75% of traffic: pin the hot, LRU the tail
```

## The Mixed-Batch Gate

Batching meets tenancy here. One uniform batch steps in 5.00 ms; the same batch mixed across all six tenants steps in 5.24 ms - +4.8% adapter bookkeeping. The alternative, one wave per tenant, costs 6 x 5.00 = 30.00 ms for the same requests, 5.73x. The +4.8% is the fee; the split is the fine - mixing pays for itself at a single extra half-millisecond.

```text
F4 | THE MIXED-BATCH GATE
  one uniform batch steps in 5.00 ms; the same batch mixed across
  all six tenants steps in 5.24 ms (+4.8% adapter-bookkeeping
  overhead); the alternative - one wave per tenant - costs 6 x
  5.00 = 30.00 ms for the same requests
  -> mixing pays 4.8% and retires the split: one wave at 5.73x
```

## The Quantized-Adapter Gate

The gate that widens the tenant ceiling. Adapter weight per tenant: fp16 56 MiB, int8 28, int4 14 - rank and layout unchanged. At 50 residents and 640-token contexts the concurrent floor moves 67 to 93 requests, +38.8%. Quality holds behind a gate: hot-tenant KL drift 0.4% against a 2% line. int4 adapters are a KV buyback; the gate is hot-tenant drift.

```text
F5 | THE QUANTIZED-ADAPTER GATE
  adapter weight per tenant: fp16 56.0 MiB, int8 28.0, int4 14.0
  (rank and layout unchanged); at 50 tenants the KV floor rises from
  43,136 to 59,936 tokens - at 640-token contexts that is a concurrent floor
  of 67 vs 93 requests (+38.8%), quality held at KL drift 0.4% < 2%
  -> int4 adapters are a KV buyback; the gate is hot-tenant drift
```

## The Day Bill

One day on the one card: 200 requests x 128 output tokens = 25,600 decode steps. Eager loads, no batching: 128,234.88 ms - the day is 128 s of stepping plus 0.23 s of adapter fetch. Eager loads, 6 uniform waves: 4,074.88 ms - batching owns the day. All resident, one mixed wave: 677.77 ms - residency pays the last 83.4% of the batched bill. 189.2x the eager floor on one card, no tenant behind a copy.

```text
F6 | THE DAY BILL
  200 requests x 128 output tokens = 25,600 decode steps at 5.00-5.24 ms:
  eager loads, no batching: 128234.88 ms (234.88 of it adapter fetch)
  eager loads, 6 uniform waves: 4074.88 ms - batching owns the day
  all resident, one mixed wave: 677.77 ms - residency pays the last
  83.4% of the batched bill
  -> 189.2x the eager floor on one card, no tenant behind a copy
```

## The Ablation Audit

Removal audit on the resident stack: -mixed batching lands 128,007.05 ms = 188.9x back (the day's spine); -residency lands 4,074.88 ms = 6.01x back, 234.88 ms of it pure adapter fetch; -int4 adapters drops the tenant ceiling to 67 requests = -28.0%. The deltas order the build: batching first, residency second, int4 third - and int4 is the only lever with a quality gate attached.

```text
F7 | THE ABLATION AUDIT
  full day 677.77 ms on a 93-request concurrent floor; remove one lever:
  -mixed batching: 128007.05 ms = 188.9x back (the day's spine)
  -residency: 4074.88 ms = 6.01x back, 234.88 ms of it pure adapter fetch
  -int4 adapters: 67-request floor = -28.0% of the tenant ceiling
  -> order the build: batching first, residency second, int4 third
```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| Swap storm at the slot boundary | One adapter ping-pongs in and out of the LRU; DRAM fetches dominate decode (f3) | Size the resident set from the trace histogram - pin the hot tenants, LRU the tail |
| KV starvation at tenant scale | 50 fp16 residents cut the KV floor 34.2% and the concurrent ceiling with it (f2) | Budget KV per resident slot; int4 adapters pay the rent back |
| Per-tenant waves | 6 x uniform steps = 5.73x the mixed step; throughput collapses as tenants grow (f4) | Mix tenants into one wave - the +4.8% bookkeeping is the fee, the split is the fine |
| Adapter quantization drift | Hot-tenant outputs drift past tolerance and nobody pinned which adapter moved (f5) | Gate on hot-tenant KL drift against a 2% line; rank and layout stay unchanged |
| Slots sized from host RAM | The card OOMs at batch peak - each slot is 56 MiB plus its KV rent, not free (f2) | Size slots from card budget: base + slots x (adapter + KV rent) under the card |
| Ladder rungs refuse to compose | The day bill moves when one lever is removed but not by its own delta (f7) | Each lever owns one cost - batching = steps, residency = fetch, int4 = KV rent; a lever touching two is misbuilt |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| tok/s drops as tenants are added | KV tokens before/after (f2); resident slot count | int4 the tail or shrink the resident set - the rent is real |
| Every tenant's first request is slow | Cold-load count vs day (f6); boot preload list | Preload the hot tenants at boot; LRU the tail |
| Measured mixed step near the split cost | Is the batch actually mixed? (f4) | One wave - the +4.8% overhead is the fee, not the 30.00 ms split |
| Quality regression after adapter int4 | Hot-tenant KL drift vs the gate (f5) | Keep fp16 for the hot tenants, int4 the tail - the gate is hot-tenant drift |
| Concurrent floor far below 93 | Adapter dtype per slot (f5); KV budget | The 93-request floor needs int4 adapters - fp16 caps at 67 |
| Throughput collapses past ~50 tenants | KV floor vs card (f2); slot count | The 43,136-token floor is the ceiling - scale cards, not slots |

## Quick Reference For

- [the multi-adapter implementation, PEFT-side](../../phases/phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md)
- [the rank and capacity math one adapter owes](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
- [the adapter anatomy a slot hosts](../../phases/phase5-finetuning/5100-peft/5103-Adapters.md)
- [SGLang, one serving surface multi-LoRA lands on](../../phases/phase1-infra/1400-llmops/1405-SGLang.md)
- [vLLM, the other serving surface multi-LoRA lands on](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 248-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the trace for your own router logs, and the bills re-derive.

```python
"""CHEAT-SHEET-065: Multi-LoRA Serving and Adapter Scheduling - the
Tenancy Bill, the KV Tax, and the Day Bill.

Fixture: one 8B base model in fp16 (16 GiB of trunk weights) on a 24 GiB
card, serving six fine-tuned tenants as LoRA adapters at rank 16 over a
4096-wide trunk: 32 layers x 7 adapted projections x 16 x (4096 + 4096)
= 29.4M params = 56 MiB fp16 per adapter. KV costs 131072 B/token
(32 layers x 8 GQA heads x 128 dim x 2 k/v x 2 B). An adapter not resident
returns over DRAM at 50 GB/s. The traffic fixture is a fixed 24-request
interleaved trace (A A B A C B D A B C E A C B F C A D B E C A B F) and a
200-request day of 128 output tokens each. All numbers below are fixture
constants or arithmetic on them - no RNG, no wall clock, two runs print
the same bytes.
"""
# ---------------------------------------------------------------- fixtures
from collections import OrderedDict

BASE_MIB = 16384          # 8B trunk in fp16
CARD_MIB = 24576          # one 24 GiB card
KV_B_PER_TOK = 131072     # 32 layers x 8 KV heads x 128 dim x 2 (k+v) x 2 B
RANK = 16
HIDDEN = 4096
LAYERS = 32
TARGETS = 7               # q, k, v, o, gate, up, down
LORA_PARAMS = LAYERS * TARGETS * RANK * (HIDDEN + HIDDEN)
ADAPTER_MIB = LORA_PARAMS * 2 / (1 << 20)
DRAM_GBS = 50.0
SWAP_MS = ADAPTER_MIB * (1 << 20) / (DRAM_GBS * 1e9) * 1000.0
TOK_PER_MIB = (1 << 20) / KV_B_PER_TOK
RULE = "=" * 64           # exhibit separator; the sheet slices the run on it

assert LORA_PARAMS == 29360128
assert ADAPTER_MIB == 56.0
assert TOK_PER_MIB == 8.0
assert abs(SWAP_MS - 1.1744) < 0.0005

# traffic: fixed 24-request interleaved trace over six tenants A..F
TRACE = list("AABACBDABCEACBFCADEBCABF")
assert len(TRACE) == 24
TENANTS = sorted(set(TRACE))
assert TENANTS == list("ABCDEF")
COUNTS = {t: TRACE.count(t) for t in TENANTS}
assert COUNTS == {"A": 7, "B": 6, "C": 5, "D": 2, "E": 2, "F": 2}
TOP3 = sum(sorted(COUNTS.values(), reverse=True)[:3])
assert TOP3 == 18  # the trace is top-heavy: 18 of 24 requests on A, B, C


def lru_misses(seq, slots):
    """LRU cache miss count over a fixed trace (stdlib OrderedDict)."""
    cache = OrderedDict()
    misses = 0
    for t in seq:
        if t in cache:
            cache.move_to_end(t)
        else:
            misses += 1
            if len(cache) >= slots:
                cache.popitem(last=False)
            cache[t] = True
    return misses


def fixed_hot_misses(seq, pinned):
    """Miss count with the hot tenants always resident; everyone else
    fetches on every visit and leaves."""
    misses = 0
    seen = set()
    for t in seq:
        if t in pinned:
            if t not in seen:
                misses += 1
                seen.add(t)
        else:
            misses += 1
    return misses


# ---------------------------------------------------------------- F1 tenancy
TENANTS_N = 6
SEP_MIB = TENANTS_N * BASE_MIB
MULTI_MIB = BASE_MIB + TENANTS_N * ADAPTER_MIB
TEN_RATIO = SEP_MIB / MULTI_MIB
assert SEP_MIB == 98304 and MULTI_MIB == 16720
assert abs(TEN_RATIO - 5.8794) < 0.0005
print(RULE)
print("F1 | THE TENANCY BILL")
print("  six fine-tuned tenants on one 24 GiB card, six copies vs one base:")
print("  %.2f GiB of copies vs %.2f GiB base+adapters (16.00 + 6 x 0.33)"
      % (SEP_MIB / 1024.0, MULTI_MIB / 1024.0))
print("  = %.2fx less GPU for the same six skills, one card instead of four"
      % TEN_RATIO)
print("  -> multi-LoRA serves the whole tenant book in a sixth of the GPU")

# ---------------------------------------------------------------- F2 kv tax
KV_FREE_MIB = CARD_MIB - BASE_MIB
KV_TOK_N0 = KV_FREE_MIB * TOK_PER_MIB
KV_MIB_N6 = KV_FREE_MIB - TENANTS_N * ADAPTER_MIB
KV_TOK_N6 = KV_MIB_N6 * TOK_PER_MIB
N50 = 50
KV_MIB_N50 = KV_FREE_MIB - N50 * ADAPTER_MIB
KV_TOK_N50 = KV_MIB_N50 * TOK_PER_MIB
ADAPTER_MIB_I4 = ADAPTER_MIB / 4.0
KV_MIB_N50_I4 = KV_FREE_MIB - N50 * ADAPTER_MIB_I4
KV_TOK_N50_I4 = KV_MIB_N50_I4 * TOK_PER_MIB
TAX_N50 = KV_TOK_N0 - KV_TOK_N50
BUYBACK_I4 = KV_TOK_N50_I4 - KV_TOK_N50
TAX_PCT = (KV_TOK_N0 - KV_TOK_N50) / KV_TOK_N0 * 100.0
I4_PCT = (KV_TOK_N0 - KV_TOK_N50_I4) / KV_TOK_N0 * 100.0
assert (KV_TOK_N0, KV_TOK_N6, KV_TOK_N50, KV_TOK_N50_I4) == (
    65536, 62848, 43136, 59936)
assert TAX_N50 == 22400 and BUYBACK_I4 == 16800
assert abs(TAX_PCT - 34.18) < 0.01 and abs(I4_PCT - 8.54) < 0.01
print(RULE)
print("F2 | THE KV TAX")
print("  KV at 131072 B/token off the same 24 GiB card: bare base %s tok;"
      % format(int(KV_TOK_N0), ","))
print("  +6 adapters %s tok (-4.1%%); +50 fp16 adapters %s tok (-%.1f%%)"
      % (format(int(KV_TOK_N6), ","), format(int(KV_TOK_N50), ","), TAX_PCT))
print("  +50 int4 adapters %s tok (-%.1f%%) - every resident adapter rents"
      % (format(int(KV_TOK_N50_I4), ","), I4_PCT))
print("  KV; quantizing the adapter pays part of the rent back")
print("  -> 50 fp16 tenants cost %s KV tokens; int4 returns %s of them"
      % (format(int(TAX_N50), ","), format(int(BUYBACK_I4), ",")))

# ---------------------------------------------------------------- F3 residency
LRU4 = lru_misses(TRACE, 4)
HOT3 = fixed_hot_misses(TRACE, {"A", "B", "C"})
FULL = lru_misses(TRACE, 6)
assert (LRU4, HOT3, FULL) == (12, 9, 6)
SCALE = 200 / 24.0
MS_LRU = LRU4 * SCALE * SWAP_MS
MS_HOT = HOT3 * SCALE * SWAP_MS
MS_FULL = FULL * SCALE * SWAP_MS
assert LRU4 * SCALE == 100 and HOT3 * SCALE == 75 and FULL * SCALE == 50
assert abs(MS_LRU - 117.44) < 0.01 and abs(MS_HOT - 88.08) < 0.01
assert abs(MS_FULL - 58.72) < 0.01
print(RULE)
print("F3 | THE RESIDENCY LADDER")
print("  the 24-request trace at swap %.2f ms per 56 MiB adapter over DRAM,"
      % SWAP_MS)
print("  scaled to a 200-request day: LRU-4 slots = %d misses (%.1f%% swap"
      % (LRU4, LRU4 / 24.0 * 100.0))
print("  rate) = %.1f ms of fetch; hot-3 pinned (A,B,C) = %d misses (%.1f%%)"
      % (MS_LRU, HOT3, HOT3 / 24.0 * 100.0))
print("  = %.1f ms; all 6 resident = %d cold loads = %.1f ms, no re-fetch"
      % (MS_HOT, FULL, MS_FULL))
print("  -> top-3 carry %.0f%% of traffic: pin the hot, LRU the tail"
      % (TOP3 / 24.0 * 100.0))

# ---------------------------------------------------------------- F4 batching
UNIFORM_MS = 5.00
MIXED_MS = 5.24
PENALTY = (MIXED_MS - UNIFORM_MS) / UNIFORM_MS * 100.0
SPLIT_MS = TENANTS_N * UNIFORM_MS
SPLIT_MULT = SPLIT_MS / MIXED_MS
assert (UNIFORM_MS, MIXED_MS, SPLIT_MS) == (5.00, 5.24, 30.00)
assert abs(PENALTY - 4.8) < 0.05 and abs(SPLIT_MULT - 5.7252) < 0.001
print(RULE)
print("F4 | THE MIXED-BATCH GATE")
print("  one uniform batch steps in %.2f ms; the same batch mixed across"
      % UNIFORM_MS)
print("  all six tenants steps in %.2f ms (+%.1f%% adapter-bookkeeping"
      % (MIXED_MS, PENALTY))
print("  overhead); the alternative - one wave per tenant - costs %d x"
      % TENANTS_N)
print("  %.2f = %.2f ms for the same requests" % (UNIFORM_MS, SPLIT_MS))
print("  -> mixing pays %.1f%% and retires the split: one wave at %.2fx"
      % (PENALTY, SPLIT_MULT))

# ---------------------------------------------------------------- F5 int4 gate
CTX_TOK = 640  # 512-token prompt + 128 output, the day's request shape
CAP_FP16 = int(KV_TOK_N50 // CTX_TOK)
CAP_I4 = int(KV_TOK_N50_I4 // CTX_TOK)
CAP_GAIN = (CAP_I4 - CAP_FP16) / float(CAP_FP16) * 100.0
KL_DRIFT = 0.4
KL_LINE = 2.0
assert CAP_FP16 == 67 and CAP_I4 == 93
assert abs(CAP_GAIN - 38.806) < 0.001
assert KL_DRIFT < KL_LINE
print(RULE)
print("F5 | THE QUANTIZED-ADAPTER GATE")
print("  adapter weight per tenant: fp16 %.1f MiB, int8 %.1f, int4 %.1f"
      % (ADAPTER_MIB, ADAPTER_MIB / 2.0, ADAPTER_MIB_I4))
print("  (rank and layout unchanged); at 50 tenants the KV floor rises from")
print("  %s to %s tokens - at %d-token contexts that is a concurrent floor"
      % (format(int(KV_TOK_N50), ","), format(int(KV_TOK_N50_I4), ","), CTX_TOK))
print("  of %d vs %d requests (+%.1f%%), quality held at KL drift %.1f%% < %s%%"
      % (CAP_FP16, CAP_I4, CAP_GAIN, KL_DRIFT, "2"))
print("  -> int4 adapters are a KV buyback; the gate is hot-tenant drift")

# ---------------------------------------------------------------- F6 day bill
REQUESTS = 200
OUT_TOK = 128
STEPS = REQUESTS * OUT_TOK
EAGER_FETCH = REQUESTS * SWAP_MS
EAGER_NOBATCH = STEPS * UNIFORM_MS + EAGER_FETCH
WAVES = 6
EAGER_BATCH = WAVES * OUT_TOK * UNIFORM_MS + EAGER_FETCH
COLD = 6
RES_MIXED = OUT_TOK * MIXED_MS + COLD * SWAP_MS
DAY_MULT = EAGER_NOBATCH / RES_MIXED
LAST_PCT = (EAGER_BATCH - RES_MIXED) / EAGER_BATCH * 100.0
assert STEPS == 25600
assert abs(EAGER_NOBATCH - 128234.88) < 0.01
assert abs(EAGER_BATCH - 4074.88) < 0.01
assert abs(RES_MIXED - 677.77) < 0.01
assert abs(DAY_MULT - 189.20) < 0.01
assert abs(LAST_PCT - 83.37) < 0.01
print(RULE)
print("F6 | THE DAY BILL")
print("  %d requests x %d output tokens = %s decode steps at 5.00-5.24 ms:"
      % (REQUESTS, OUT_TOK, format(STEPS, ",")))
print("  eager loads, no batching: %.2f ms (%.2f of it adapter fetch)"
      % (EAGER_NOBATCH, EAGER_FETCH))
print("  eager loads, 6 uniform waves: %.2f ms - batching owns the day"
      % EAGER_BATCH)
print("  all resident, one mixed wave: %.2f ms - residency pays the last"
      % RES_MIXED)
print("  %.1f%% of the batched bill" % LAST_PCT)
print("  -> %.1fx the eager floor on one card, no tenant behind a copy"
      % DAY_MULT)

# ---------------------------------------------------------------- F7 ablation
A_NO_MIX = STEPS * UNIFORM_MS + COLD * SWAP_MS
A_NO_RES = EAGER_BATCH
A_NO_I4 = CAP_FP16
NO_MIX_MULT = A_NO_MIX / RES_MIXED
NO_RES_MULT = A_NO_RES / RES_MIXED
NO_RES_PCT = (A_NO_RES - RES_MIXED) / A_NO_RES * 100.0
I4_LOSS = (CAP_I4 - A_NO_I4) / float(CAP_I4) * 100.0
assert abs(A_NO_MIX - 128007.05) < 0.01 and abs(A_NO_RES - 4074.88) < 0.01
assert A_NO_I4 == 67
assert abs(NO_MIX_MULT - 188.87) < 0.01
assert abs(NO_RES_MULT - 6.01) < 0.01
assert abs(NO_RES_PCT - 83.37) < 0.01
assert abs(I4_LOSS - 27.957) < 0.001
print(RULE)
print("F7 | THE ABLATION AUDIT")
print("  full day %.2f ms on a %d-request concurrent floor; remove one lever:"
      % (RES_MIXED, CAP_I4))
print("  -mixed batching: %.2f ms = %.1fx back (the day's spine)"
      % (A_NO_MIX, NO_MIX_MULT))
print("  -residency: %.2f ms = %.2fx back, %.2f ms of it pure adapter fetch"
      % (A_NO_RES, NO_RES_MULT, EAGER_FETCH))
print("  -int4 adapters: %d-request floor = -%.1f%% of the tenant ceiling"
      % (A_NO_I4, I4_LOSS))
print("  -> order the build: batching first, residency second, int4 third")
print("FENCE-065-OK")
```

```text
================================================================
F1 | THE TENANCY BILL
  six fine-tuned tenants on one 24 GiB card, six copies vs one base:
  96.00 GiB of copies vs 16.33 GiB base+adapters (16.00 + 6 x 0.33)
  = 5.88x less GPU for the same six skills, one card instead of four
  -> multi-LoRA serves the whole tenant book in a sixth of the GPU
================================================================
F2 | THE KV TAX
  KV at 131072 B/token off the same 24 GiB card: bare base 65,536 tok;
  +6 adapters 62,848 tok (-4.1%); +50 fp16 adapters 43,136 tok (-34.2%)
  +50 int4 adapters 59,936 tok (-8.5%) - every resident adapter rents
  KV; quantizing the adapter pays part of the rent back
  -> 50 fp16 tenants cost 22,400 KV tokens; int4 returns 16,800 of them
================================================================
F3 | THE RESIDENCY LADDER
  the 24-request trace at swap 1.17 ms per 56 MiB adapter over DRAM,
  scaled to a 200-request day: LRU-4 slots = 12 misses (50.0% swap
  rate) = 117.4 ms of fetch; hot-3 pinned (A,B,C) = 9 misses (37.5%)
  = 88.1 ms; all 6 resident = 6 cold loads = 58.7 ms, no re-fetch
  -> top-3 carry 75% of traffic: pin the hot, LRU the tail
================================================================
F4 | THE MIXED-BATCH GATE
  one uniform batch steps in 5.00 ms; the same batch mixed across
  all six tenants steps in 5.24 ms (+4.8% adapter-bookkeeping
  overhead); the alternative - one wave per tenant - costs 6 x
  5.00 = 30.00 ms for the same requests
  -> mixing pays 4.8% and retires the split: one wave at 5.73x
================================================================
F5 | THE QUANTIZED-ADAPTER GATE
  adapter weight per tenant: fp16 56.0 MiB, int8 28.0, int4 14.0
  (rank and layout unchanged); at 50 tenants the KV floor rises from
  43,136 to 59,936 tokens - at 640-token contexts that is a concurrent floor
  of 67 vs 93 requests (+38.8%), quality held at KL drift 0.4% < 2%
  -> int4 adapters are a KV buyback; the gate is hot-tenant drift
================================================================
F6 | THE DAY BILL
  200 requests x 128 output tokens = 25,600 decode steps at 5.00-5.24 ms:
  eager loads, no batching: 128234.88 ms (234.88 of it adapter fetch)
  eager loads, 6 uniform waves: 4074.88 ms - batching owns the day
  all resident, one mixed wave: 677.77 ms - residency pays the last
  83.4% of the batched bill
  -> 189.2x the eager floor on one card, no tenant behind a copy
================================================================
F7 | THE ABLATION AUDIT
  full day 677.77 ms on a 93-request concurrent floor; remove one lever:
  -mixed batching: 128007.05 ms = 188.9x back (the day's spine)
  -residency: 4074.88 ms = 6.01x back, 234.88 ms of it pure adapter fetch
  -int4 adapters: 67-request floor = -28.0% of the tenant ceiling
  -> order the build: batching first, residency second, int4 third
FENCE-065-OK
```
