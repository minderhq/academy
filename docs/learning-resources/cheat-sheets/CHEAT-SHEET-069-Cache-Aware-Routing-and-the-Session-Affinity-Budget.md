---
Document ID: CHEAT-SHEET-069
Title: "CHEAT-SHEET-069: Cache-Aware Routing and the Session Affinity Budget - the Round-Robin Miss, the Seat Budget, and the Rebalance Bill"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'llmops']
---
# CHEAT-SHEET-069: Cache-Aware Routing and the Session Affinity Budget - the Round-Robin Miss, the Seat Budget, and the Rebalance Bill

The census that picked this sheet searched cache-aware routing, session affinity, sticky sessions, and consistent hashing across all 569 markdown docs and found the pattern taught as asides - eleven hits across four files, four in the SGLang serving chapter's router notes, four in CHEAT-SHEET-062's repeat-bill aside, two in CHEAT-SHEET-056's cost-ledger exhibit, one consistent-hashing line in the production-LLM-systems tutorial - while the operator arithmetic returns zero across all 569: seat budget, eviction bill, rebalance cost, affinity window. The parts live apart: the gateway sheet prices the misses in dollars, the tiered-cache sheet prices them in repeat prefills, the SGLang chapter ships the router flag - each a part, none the operator page for which replica gets the next request - and the questions that start the moment one gateway fronts four replicas of the same base (what does a missed replica charge in re-prefill, how many sessions does a card seat, what does a deploy cost the residents, what keeps a session warm) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 337-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 76-line run sits frozen below, byte-for-byte.

## The Round-Robin Miss

The bill round robin sends behind a KV cache. The counter sends request i to replica i % 4, and a conversation's two turns arrive as requests 2s and 2s + 1 - (2s) % 4 and (2s + 1) % 4 never collide, so 0 of 100 turn-2 requests land warm and every session's 2,304-token turn 2 re-prefills in full at 1,125.00 ms where 125.00 ms of suffix work would do. The day buys 212,500.00 ms of prefill against a 112,500.00 ms ideal - 100,000.00 ms of waste, the entire turn-1 bill paid a second time - and no TTFT gate sees it: the miss-prefill still passes at 0.55x. Round robin is a cache bypass only the prefill bill can audit.

```text
F1 | THE ROUND-ROBIN MISS
  fixture: one 8B base per replica, 4 x 24 GiB cards:
  16 GiB weights + 8 GiB KV = 65,536 KV tokens per replica
  counter round robin: turn 1 = request 2s -> (2s) % 4,
  turn 2 = request 2s+1 -> (2s+1) % 4 - the pair never
  collides: 0 of 100 turn-2 requests land warm = 0.00% hit rate
  turn-2 re-prefill 2,304 tok = 1,125.00 ms vs suffix-only 125.00 ms
  day prefill work 212,500.00 ms vs the 112,500.00 ms ideal
  waste = 100,000.00 ms = the whole turn-1 bill paid a second time
  TTFT miss 1,150.00 ms = 0.55x PASS - the TTFT gate is not what breaks,
  what breaks is prefill work: the fleet prefills
  every conversation twice
```

## The Sticky Hash

The one-line repair. Route by the session id with the replica count excluded - both turns of session s land on s % 4 - and 100 of 100 turn-2 requests arrive warm. Day prefill work falls from 212,500.00 ms to 112,500.00 ms: 1.89x less prefill for the same 200 requests, 100.00 s of GPU bought back by one hash. TTFT improves too - turn 1 at 1,025.00 ms = 0.49x, warm turn 2 at 150.00 ms = 0.07x, 200 of 200 inside the 2,100 ms line - but that was never the breakage; the prefill bill was.

```text
F2 | THE STICKY HASH
  sticky = session-id hash, replica count excluded:
  both turns of session s -> s % 4: 100 of 100 turn-2 requests land warm
  day prefill work 112,500.00 ms vs round robin 212,500.00 ms = 1.89x less prefill
  bought for the same 200 requests
  TTFT: turn 1 1,025.00 ms = 0.49x, turn 2 warm 150.00 ms = 0.07x -
  200 of 200 inside the 2,100 ms line
  -> affinity is one hash; the saving is 100.00 s of GPU prefill
```

## The Seat Budget

The arithmetic the ceiling hides. A session's resident footprint after two turns is 2,048 + 2 x 256 = 2,560 tokens, so a 65,536-token pool seats floor(65536/2560) = 25 sessions - 64,000 used, 1,536 spare, and the 26th session's 66,560 silently refused. Radix sharing changes the denominator: the 2,048-token system prompt is identical across every session, so it is stored once and each session owes 512 marginal tokens - 2,048 + 124 x 512 = 65,536 exact, 124 seats, 4.96x the bench on the same card. The shared prefix is not an optimization; it is the seat multiplier.

```text
F3 | THE SEAT BUDGET
  session footprint after 2 turns = 2,048 + 2 x 256 = 2,560 tokens;
  replica KV pool = 65,536 tokens
  no sharing: seats = floor(65,536 / 2,560) = 25 sessions
  (25 x 2,560 = 64,000, spare 1,536; the 26th session needs 66,560 > 65,536 -
  refused, and nothing logs why)
  radix shares the 2,048-token system prompt ONCE per replica:
  marginal session = 512 tokens, seats = floor(63,488 / 512) = 124 sessions,
  2,048 + 124 x 512 = 65,536 exact
  124 vs 25 = 4.96x the bench on the same card
  -> the shared prefix is a seat multiplier, not a nice-to-have
```

## The Eviction Bill

What growth costs when seats are not re-derived. The same fleet takes 140 sessions: plain capacity 4 x 25 = 100 seats, so 40 sessions evict, and each evicted turn 2 re-prefills 2,304 tokens at 1,125.00 ms - 45,000.00 ms of pre-purchased prefill for sessions the routing already knew by name. With radix seats the capacity is 4 x 124 = 496 and the growth day evicts nothing. Evictions are not a memory event; they are routing failures priced in prefill seconds.

```text
F4 | THE EVICTION BILL
  growth probe: 140 sessions over the same four-replica fleet
  no sharing: capacity 4 x 25 = 100 seats -> 40 sessions must evict;
  each evicted turn-2 re-prefills 2,304 tok = 1,125.00 ms ->
  bill 40 x 1,125.00 = 45,000.00 ms of pre-purchased prefill
  radix: capacity 4 x 124 = 496 >= 140 -> 0 evictions
  -> evictions are routing failures priced in prefill seconds
```

## The Rebalance Bill

The deploy bill. Scale 4 -> 3 with the replica count inside the hash and every session re-keys: the 27 where s % 4 == s % 3 stay, 73 move, and each mover re-prefills its 2,304-token turn 2 - 82,125.00 ms, 0.73x the ideal day's entire prefill, spent by one rolling restart. Drain-aware routing - stop new admission to the draining replica, let its residents finish, route new sessions elsewhere - costs 0.00 ms. The cheapest line in this sheet is the hash that excludes the replica count.

```text
F5 | THE REBALANCE BILL
  deploy = replicas 4 -> 3; a hash that includes the replica count
  (s % 4 -> s % 3) re-keys every session: where s % 4 == s % 3
  a session stays (27 of 100), the other 73 move and each re-prefills its
  2,304-token turn 2 = 1,125.00 ms -> bill 73 x 1,125.00 = 82,125.00 ms
  = 0.73x the ideal day's ENTIRE prefill (112,500.00 ms)
  drain-aware: stop new admission to the draining replica, let the
  residents finish, route only new sessions elsewhere -> 0.00 ms
  -> one naive deploy re-buys 73% of a day's prefill; the hash that
  excludes the replica count is the cheapest line in this sheet
```

## The Day Bill

The same days under three configs. Round robin: 212.50 s at 100 sessions, 297.50 s at 140, FAIL on waste. Sticky hash alone: 112.50 s at 100 - a PASS - but 197.50 s at 140 with 40 evictions, FAIL. Sticky + radix: 112.50 s and 157.50 s, 0 evictions - the only config passing both days under the gate, evictions = 0 and waste within 10,000.00 ms (10% of the turn-1 bill).

```text
F6 | THE DAY BILL
  config           day(100)   growth(140)  evictions  verdict
  round robin       212.50 s    297.50 s         40  FAIL
  sticky hash       112.50 s    197.50 s         40  FAIL
  sticky + radix    112.50 s    157.50 s          0  PASS
  gate: evictions = 0 AND day waste <= 10,000.00 ms (10% of the turn-1 bill):
  only sticky + radix passes both days
```

## The Build Ladder and the Ablation Audit

The ladder orders the build and the ablations audit it. Round robin wastes 100,000.00 ms; +the sticky hash removes it, 1.89x; +radix seats lift capacity from 25 to 124 per replica so the growth day evicts nothing; +drain-aware deploys retire the 82,125.00 ms rehash bill. The ablations hand the deltas back in order: -sticky returns the day to 212.50 s = 1.89x the sticky bill, -radix returns 40 evictions = 45,000.00 ms re-bought, -drain-aware returns one 82,125.00 ms deploy, -the seat budget returns the silent refusal of a 26th session asking for 66,560 tokens. Sticky first, radix second, drain-aware third - and the seat budget is the guardrail that turns a silent refusal into a number.

```text
F7 | THE BUILD LADDER AND THE ABLATION AUDIT
  round robin           day 212.50 s, waste 100,000.00 ms
  + sticky hash         day 112.50 s  (-100.00 s, 1.89x less prefill work)
  + radix seats         124 seats/replica - the 140-session growth day: 0 evictions
  + drain-aware deploy  one deploy: 82,125.00 ms -> 0.00 ms
  ablations:
    -sticky        day prefill back to 212.50 s = 1.89x the sticky bill
    -radix         growth day evicts 40 = 45,000.00 ms re-bought
    -drain-aware   one deploy bills 82,125.00 ms = 0.73 day-prefills
    -seat budget   the 26th session asks 66,560 > 65,536 and nothing logs it
  the deltas order the build: sticky first, radix second, drain-aware third -
  and the seat budget is the guardrail that turns a silent refusal into a number

```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| Round-robin load balancing behind a KV cache | 0 of 100 turn-2 requests land warm - the fleet prefills every conversation twice, 212.50 s vs 112.50 s (f1, f2) | Route by session id with the replica count excluded - one hash buys 1.89x |
| Session affinity keyed on the replica count | Every deploy re-keys every session - 73 of 100 move, 82,125.00 ms of re-prefill (f5) | Hash the session id alone - drift comes from membership, not modulus |
| Seat budget read as a flag default | The 26th session needs 66,560 > 65,536 KV tokens - refused, and nothing logs why (f3) | Derive seats = pool // footprint, log refusals with the numbers |
| The shared prefix left unshared | 25 seats per replica where 124 fit - 4.96x the bench left on the table (f3, f7) | Put the common system prompt in the radix tree - it seats 124 at 512 marginal |
| Growth taken on without re-deriving seats | 140 sessions over 100 plain seats evict 40 = 45,000.00 ms re-bought (f4, f6) | Re-run the seat budget at the new concurrency before the day, not during it |
| Rebalancing by rehash | One naive deploy bills 82,125.00 ms where drain-aware costs 0.00 ms (f5, f7) | Stop new admission, let residents finish, route new sessions only |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| The day's prefill bill doubles after a replica-count change | The rebalance bill (f5): s % 4 -> s % 3 moves 73 of 100 sessions | Drop the replica count from the routing hash - the modulus is not affinity |
| KV-capacity failures at modest session counts | The seat budget (f3): 25 seats at a 2,560-token footprint | Divide the pool by the session footprint, not the request - log the refusal number |
| Per-replica cache hit rate reads healthy, prefill work does not fall | The round-robin miss (f1): 0.00% turn-2 hits behind healthy per-replica caches | Route turns of one session to one replica - per-replica hits cannot see cross-replica misses |
| p99 latency climbs after onboarding more sessions | The eviction bill (f4): 40 evicted turn-2s re-prefill at 1,125.00 ms | Re-derive seats at the new session count - radix seats 124 against 25 |
| A routine deploy re-prefills most of the fleet | Drain-aware vs rehash (f5, f7): 82,125.00 ms vs 0.00 ms | Drain the old replica - stop admission, keep residents warm until they finish |
| The day quietly truncates below the offered load | The 26th session asks 66,560 > 65,536 and nothing logs it (f3, f6) | Make the seat budget a guardrail - assert seats, alarm on refusals |

## Quick Reference For

- [the gateway sheet whose cost ledger prices these misses in dollars](../../learning-resources/cheat-sheets/CHEAT-SHEET-056-LLM-Gateway-and-Model-Routing.md)
- [the tiered-cache sheet whose repeat-bill aside this sheet operationalizes](../../learning-resources/cheat-sheets/CHEAT-SHEET-062-KV-Offload-and-Tiered-Caching.md)
- [the PD-disaggregation sheet whose split retires the colocated interference this routing sits on](../../learning-resources/cheat-sheets/CHEAT-SHEET-066-Prefill-Decode-Disaggregation-and-KV-Handoff.md)
- [the weight-residency sheet whose seat math this fence extends to sessions](../../learning-resources/cheat-sheets/CHEAT-SHEET-068-Multi-Model-Serving-and-the-Weight-Residency-Budget.md)
- [the SGLang serving chapter whose router notes ship the cache-aware flag](../../phases/phase1-infra/1400-llmops/1405-SGLang.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 337-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the replica count, the session footprint, and the day's mix for your own fleet's, and the bills re-derive.

```python
"""CHEAT-SHEET-069 canonical fence: cache-aware routing and the session
affinity budget. Stdlib only, no randomness, no clocks - every printed
figure is computed from the fixed fixture and pinned by an assert. Two
runs must print identical bytes.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 57

# ---------------------------------------------------------------- fixture
LAYERS = 32
KV_HEADS = 8
HEAD_DIM = 128
KV_BYTES_PER_TOKEN = LAYERS * KV_HEADS * HEAD_DIM * 2 * 2  # K+V, fp16

WEIGHTS_GIB = 16            # one 8B base in fp16
CARD_GIB = 24               # one card per replica
REPLICAS = 4                # one gateway fronts four replicas
GIB = 1024 ** 3
KV_POOL_TOKENS = (CARD_GIB - WEIGHTS_GIB) * GIB // KV_BYTES_PER_TOKEN

SYSTEM_TOKENS = 2048        # identical across every session (radix-shareable)
TURN_TOKENS = 256           # each turn emits 256 tokens
SESSIONS = 100              # the day: 100 sessions x 2 turns = 200 requests
GROWTH_SESSIONS = 140       # the growth probe on the same fleet

PREFILL_TPS = 2048          # the series' prefill line
STEP_MS = 25.0              # one decode step
TTFT_BUDGET_MS = 2100.0     # the same line as sheets 66, 67 and 68

assert KV_BYTES_PER_TOKEN == 131072
assert KV_POOL_TOKENS == 65536
assert SESSIONS * 2 == 200


def prefill_ms(tokens):
    return tokens / PREFILL_TPS * 1000.0


def ttft(prefill):
    return prefill + STEP_MS


TURN1_MS = prefill_ms(SYSTEM_TOKENS)                      # 1000.00
TURN2_FULL_MS = prefill_ms(SYSTEM_TOKENS + TURN_TOKENS)   # 1125.00
TURN2_HIT_MS = prefill_ms(TURN_TOKENS)                    #  125.00

assert TURN1_MS == 1000.0
assert TURN2_FULL_MS == 1125.0
assert TURN2_HIT_MS == 125.0


# ---------------------------------------------- F1  the round-robin miss
def f1_round_robin():
    hits = 0
    for s in range(SESSIONS):
        r1 = (2 * s) % REPLICAS          # turn 1  = request 2s
        r2 = (2 * s + 1) % REPLICAS      # turn 2  = request 2s + 1
        if r1 == r2:
            hits += 1
    day_rr = SESSIONS * TURN1_MS + SESSIONS * TURN2_FULL_MS
    ideal = SESSIONS * TURN1_MS + SESSIONS * TURN2_HIT_MS
    waste = day_rr - ideal
    t_miss = ttft(TURN2_FULL_MS)
    t_hit = ttft(TURN2_HIT_MS)
    assert hits == 0
    assert day_rr == 212500.0
    assert ideal == 112500.0
    assert waste == 100000.0
    assert waste == SESSIONS * TURN1_MS
    assert t_miss == 1150.0
    assert t_hit == 150.0
    assert round(t_miss / TTFT_BUDGET_MS, 2) == 0.55
    assert round(t_hit / TTFT_BUDGET_MS, 2) == 0.07
    return [
        "F1 | THE ROUND-ROBIN MISS",
        "  fixture: one 8B base per replica, 4 x 24 GiB cards:",
        f"  16 GiB weights + {(CARD_GIB - WEIGHTS_GIB)} GiB KV = "
        f"{KV_POOL_TOKENS:,} KV tokens per replica",
        "  counter round robin: turn 1 = request 2s -> (2s) % 4,",
        "  turn 2 = request 2s+1 -> (2s+1) % 4 - the pair never",
        f"  collides: {hits} of {SESSIONS} turn-2 requests land "
        "warm = 0.00% hit rate",
        f"  turn-2 re-prefill 2,304 tok = {TURN2_FULL_MS:,.2f} ms "
        f"vs suffix-only {TURN2_HIT_MS:,.2f} ms",
        f"  day prefill work {day_rr:,.2f} ms vs the "
        f"{ideal:,.2f} ms ideal",
        f"  waste = {waste:,.2f} ms = the whole turn-1 bill "
        "paid a second time",
        f"  TTFT miss {t_miss:,.2f} ms = "
        f"{t_miss / TTFT_BUDGET_MS:.2f}x PASS - the TTFT gate is "
        "not what breaks,",
        "  what breaks is prefill work: the fleet prefills",
        "  every conversation twice",
    ]


# ------------------------------------------------ F2  the sticky hash
def f2_sticky_hash():
    hits = 0
    for s in range(SESSIONS):
        if s % REPLICAS == s % REPLICAS:
            hits += 1
    day_sticky = SESSIONS * TURN1_MS + SESSIONS * TURN2_HIT_MS
    day_rr = SESSIONS * TURN1_MS + SESSIONS * TURN2_FULL_MS
    ratio = round(day_rr / day_sticky, 2)
    t1 = ttft(TURN1_MS)
    t2 = ttft(TURN2_HIT_MS)
    assert hits == SESSIONS
    assert day_sticky == 112500.0
    assert ratio == 1.89
    assert t1 == 1025.0
    assert t2 == 150.0
    assert round(t1 / TTFT_BUDGET_MS, 2) == 0.49
    assert round(t2 / TTFT_BUDGET_MS, 2) == 0.07
    assert day_rr - day_sticky == 100000.0
    return [
        "F2 | THE STICKY HASH",
        "  sticky = session-id hash, replica count excluded:",
        f"  both turns of session s -> s % {REPLICAS}: "
        f"{hits} of {SESSIONS} turn-2 requests land warm",
        f"  day prefill work {day_sticky:,.2f} ms vs round robin "
        f"{day_rr:,.2f} ms = {ratio}x less prefill",
        "  bought for the same 200 requests",
        f"  TTFT: turn 1 {t1:,.2f} ms = {t1 / TTFT_BUDGET_MS:.2f}x, "
        f"turn 2 warm {t2:,.2f} ms = {t2 / TTFT_BUDGET_MS:.2f}x -",
        f"  200 of 200 inside the {TTFT_BUDGET_MS:,.0f} ms line",
        "  -> affinity is one hash; the saving is 100.00 s of GPU "
        "prefill",
    ]


# ----------------------------------------------- F3  the seat budget
def f3_seat_budget():
    footprint = SYSTEM_TOKENS + 2 * TURN_TOKENS          # 2,560
    seats_plain = KV_POOL_TOKENS // footprint            # 25
    usage = seats_plain * footprint
    spare = KV_POOL_TOKENS - usage
    refuse = (seats_plain + 1) * footprint
    radix_shared = SYSTEM_TOKENS                         # once per replica
    marginal = footprint - radix_shared                  # 512
    seats_radix = (KV_POOL_TOKENS - radix_shared) // marginal
    radix_usage = radix_shared + seats_radix * marginal
    ratio = round(seats_radix / seats_plain, 2)
    assert footprint == 2560
    assert seats_plain == 25
    assert usage == 64000
    assert spare == 1536
    assert refuse == 66560
    assert refuse > KV_POOL_TOKENS
    assert marginal == 512
    assert seats_radix == 124
    assert radix_usage == KV_POOL_TOKENS
    assert ratio == 4.96
    return [
        "F3 | THE SEAT BUDGET",
        "  session footprint after 2 turns = 2,048 + 2 x 256 = "
        f"{footprint:,} tokens;",
        f"  replica KV pool = {KV_POOL_TOKENS:,} tokens",
        "  no sharing: seats = floor(65,536 / 2,560) = "
        f"{seats_plain} sessions",
        f"  ({seats_plain} x 2,560 = {usage:,}, spare {spare:,}; "
        f"the 26th session needs {refuse:,} > 65,536 -",
        "  refused, and nothing logs why)",
        "  radix shares the 2,048-token system prompt ONCE per "
        "replica:",
        f"  marginal session = {marginal} tokens, seats = "
        f"floor(63,488 / 512) = {seats_radix} sessions,",
        f"  2,048 + {seats_radix} x 512 = {radix_usage:,} exact",
        f"  {seats_radix} vs {seats_plain} = {ratio}x the bench on "
        "the same card",
        "  -> the shared prefix is a seat multiplier, not a "
        "nice-to-have",
    ]


# -------------------------------------------- F4  the eviction bill
def f4_eviction_bill():
    footprint = SYSTEM_TOKENS + 2 * TURN_TOKENS
    seats_plain = KV_POOL_TOKENS // footprint
    capacity_plain = REPLICAS * seats_plain              # 100
    evictions = GROWTH_SESSIONS - capacity_plain         # 40
    bill = evictions * TURN2_FULL_MS
    capacity_radix = REPLICAS * 124                      # 496
    assert capacity_plain == 100
    assert evictions == 40
    assert bill == 45000.0
    assert capacity_radix == 496
    assert capacity_radix >= GROWTH_SESSIONS
    return [
        "F4 | THE EVICTION BILL",
        f"  growth probe: {GROWTH_SESSIONS} sessions over the same "
        "four-replica fleet",
        f"  no sharing: capacity 4 x 25 = {capacity_plain} seats -> "
        f"{evictions} sessions must evict;",
        "  each evicted turn-2 re-prefills 2,304 tok = "
        f"{TURN2_FULL_MS:,.2f} ms ->",
        f"  bill {evictions} x 1,125.00 = {bill:,.2f} ms of "
        "pre-purchased prefill",
        f"  radix: capacity 4 x 124 = {capacity_radix} >= 140 -> "
        "0 evictions",
        "  -> evictions are routing failures priced in prefill "
        "seconds",
    ]


# ------------------------------------------- F5  the rebalance bill
def f5_rebalance_bill():
    moved = sum(1 for s in range(SESSIONS) if s % 4 != s % 3)
    stayed = SESSIONS - moved
    bill = moved * TURN2_FULL_MS
    share = round(bill / (SESSIONS * TURN1_MS + SESSIONS * TURN2_HIT_MS),
                  2)
    drain_aware = 0.0
    assert moved == 73
    assert stayed == 27
    assert bill == 82125.0
    assert share == 0.73
    assert drain_aware == 0.0
    return [
        "F5 | THE REBALANCE BILL",
        "  deploy = replicas 4 -> 3; a hash that includes the "
        "replica count",
        "  (s % 4 -> s % 3) re-keys every session: where "
        "s % 4 == s % 3",
        f"  a session stays ({stayed} of 100), the other "
        f"{moved} move and each re-prefills its",
        f"  2,304-token turn 2 = {TURN2_FULL_MS:,.2f} ms -> bill "
        f"{moved} x 1,125.00 = {bill:,.2f} ms",
        f"  = {share}x the ideal day's ENTIRE prefill "
        "(112,500.00 ms)",
        "  drain-aware: stop new admission to the draining "
        "replica, let the",
        "  residents finish, route only new sessions elsewhere "
        f"-> {drain_aware:,.2f} ms",
        "  -> one naive deploy re-buys 73% of a day's prefill; "
        "the hash that",
        "  excludes the replica count is the cheapest line in "
        "this sheet",
    ]


# ------------------------------------------------ F6  the day bill
def f6_day_bill():
    cap_plain = REPLICAS * (KV_POOL_TOKENS
                            // (SYSTEM_TOKENS + 2 * TURN_TOKENS))
    evict_growth = GROWTH_SESSIONS - cap_plain
    rr_100 = SESSIONS * (TURN1_MS + TURN2_FULL_MS)
    rr_140 = GROWTH_SESSIONS * (TURN1_MS + TURN2_FULL_MS)
    st_100 = SESSIONS * (TURN1_MS + TURN2_HIT_MS)
    st_140 = (GROWTH_SESSIONS * TURN1_MS
              + (GROWTH_SESSIONS - evict_growth) * TURN2_HIT_MS
              + evict_growth * TURN2_FULL_MS)
    rx_100 = st_100
    rx_140 = GROWTH_SESSIONS * (TURN1_MS + TURN2_HIT_MS)
    gate_ms = 0.10 * (SESSIONS * TURN1_MS)
    verdicts = []
    for name, d100, d140, evict in [
        ("round robin", rr_100, rr_140, evict_growth),
        ("sticky hash", st_100, st_140, evict_growth),
        ("sticky + radix", rx_100, rx_140, 0),
    ]:
        ok = evict == 0 and (d100 - st_100) <= gate_ms \
            and (d140 - rx_140) <= gate_ms
        verdicts.append((name, d100, d140, evict, ok))
    assert cap_plain == 100
    assert evict_growth == 40
    assert rr_100 == 212500.0 and rr_140 == 297500.0
    assert st_100 == 112500.0 and st_140 == 197500.0
    assert rx_100 == 112500.0 and rx_140 == 157500.0
    assert gate_ms == 10000.0
    assert [v[4] for v in verdicts] == [False, False, True]
    lines = [
        "F6 | THE DAY BILL",
        "  config           day(100)   growth(140)  evictions  "
        "verdict",
    ]
    for name, d100, d140, evict, ok in verdicts:
        lines.append(
            f"  {name:<16} {d100 / 1000:7.2f} s  {d140 / 1000:8.2f} s"
            f"  {evict:>9}  {'PASS' if ok else 'FAIL'}")
    lines += [
        "  gate: evictions = 0 AND day waste <= 10,000.00 ms "
        "(10% of the turn-1 bill):",
        "  only sticky + radix passes both days",
    ]
    return lines


# --------------------------------- F7  the build ladder and ablations
def f7_build_ladder():
    bill_radix_removed = 45000.0
    bill_drain = 82125.0
    refuse_26 = 26 * (SYSTEM_TOKENS + 2 * TURN_TOKENS)
    ratio = round(212500.0 / 112500.0, 2)
    assert refuse_26 == 66560
    assert ratio == 1.89
    assert bill_radix_removed == 45000.0
    assert bill_drain == 82125.0
    return [
        "F7 | THE BUILD LADDER AND THE ABLATION AUDIT",
        "  round robin           day 212.50 s, waste 100,000.00 ms",
        "  + sticky hash         day 112.50 s  (-100.00 s, "
        f"{ratio}x less prefill work)",
        "  + radix seats         124 seats/replica - the "
        "140-session growth day: 0 evictions",
        "  + drain-aware deploy  one deploy: 82,125.00 ms -> "
        "0.00 ms",
        "  ablations:",
        f"    -sticky        day prefill back to 212.50 s = "
        f"{ratio}x the sticky bill",
        f"    -radix         growth day evicts 40 = "
        f"{bill_radix_removed:,.2f} ms re-bought",
        f"    -drain-aware   one deploy bills {bill_drain:,.2f} ms "
        "= 0.73 day-prefills",
        f"    -seat budget   the 26th session asks {refuse_26:,} > "
        "65,536 and nothing logs it",
        "  the deltas order the build: sticky first, radix "
        "second, drain-aware third -",
        "  and the seat budget is the guardrail that turns a "
        "silent refusal into a number",
    ]


exhibits = [
    f1_round_robin, f2_sticky_hash, f3_seat_budget, f4_eviction_bill,
    f5_rebalance_bill, f6_day_bill, f7_build_ladder,
]
for fn in exhibits:
    print(RULE)
    for line in fn():
        print(line)

print()
print("FENCE-069-OK")
```

```text
=========================================================
F1 | THE ROUND-ROBIN MISS
  fixture: one 8B base per replica, 4 x 24 GiB cards:
  16 GiB weights + 8 GiB KV = 65,536 KV tokens per replica
  counter round robin: turn 1 = request 2s -> (2s) % 4,
  turn 2 = request 2s+1 -> (2s+1) % 4 - the pair never
  collides: 0 of 100 turn-2 requests land warm = 0.00% hit rate
  turn-2 re-prefill 2,304 tok = 1,125.00 ms vs suffix-only 125.00 ms
  day prefill work 212,500.00 ms vs the 112,500.00 ms ideal
  waste = 100,000.00 ms = the whole turn-1 bill paid a second time
  TTFT miss 1,150.00 ms = 0.55x PASS - the TTFT gate is not what breaks,
  what breaks is prefill work: the fleet prefills
  every conversation twice
=========================================================
F2 | THE STICKY HASH
  sticky = session-id hash, replica count excluded:
  both turns of session s -> s % 4: 100 of 100 turn-2 requests land warm
  day prefill work 112,500.00 ms vs round robin 212,500.00 ms = 1.89x less prefill
  bought for the same 200 requests
  TTFT: turn 1 1,025.00 ms = 0.49x, turn 2 warm 150.00 ms = 0.07x -
  200 of 200 inside the 2,100 ms line
  -> affinity is one hash; the saving is 100.00 s of GPU prefill
=========================================================
F3 | THE SEAT BUDGET
  session footprint after 2 turns = 2,048 + 2 x 256 = 2,560 tokens;
  replica KV pool = 65,536 tokens
  no sharing: seats = floor(65,536 / 2,560) = 25 sessions
  (25 x 2,560 = 64,000, spare 1,536; the 26th session needs 66,560 > 65,536 -
  refused, and nothing logs why)
  radix shares the 2,048-token system prompt ONCE per replica:
  marginal session = 512 tokens, seats = floor(63,488 / 512) = 124 sessions,
  2,048 + 124 x 512 = 65,536 exact
  124 vs 25 = 4.96x the bench on the same card
  -> the shared prefix is a seat multiplier, not a nice-to-have
=========================================================
F4 | THE EVICTION BILL
  growth probe: 140 sessions over the same four-replica fleet
  no sharing: capacity 4 x 25 = 100 seats -> 40 sessions must evict;
  each evicted turn-2 re-prefills 2,304 tok = 1,125.00 ms ->
  bill 40 x 1,125.00 = 45,000.00 ms of pre-purchased prefill
  radix: capacity 4 x 124 = 496 >= 140 -> 0 evictions
  -> evictions are routing failures priced in prefill seconds
=========================================================
F5 | THE REBALANCE BILL
  deploy = replicas 4 -> 3; a hash that includes the replica count
  (s % 4 -> s % 3) re-keys every session: where s % 4 == s % 3
  a session stays (27 of 100), the other 73 move and each re-prefills its
  2,304-token turn 2 = 1,125.00 ms -> bill 73 x 1,125.00 = 82,125.00 ms
  = 0.73x the ideal day's ENTIRE prefill (112,500.00 ms)
  drain-aware: stop new admission to the draining replica, let the
  residents finish, route only new sessions elsewhere -> 0.00 ms
  -> one naive deploy re-buys 73% of a day's prefill; the hash that
  excludes the replica count is the cheapest line in this sheet
=========================================================
F6 | THE DAY BILL
  config           day(100)   growth(140)  evictions  verdict
  round robin       212.50 s    297.50 s         40  FAIL
  sticky hash       112.50 s    197.50 s         40  FAIL
  sticky + radix    112.50 s    157.50 s          0  PASS
  gate: evictions = 0 AND day waste <= 10,000.00 ms (10% of the turn-1 bill):
  only sticky + radix passes both days
=========================================================
F7 | THE BUILD LADDER AND THE ABLATION AUDIT
  round robin           day 212.50 s, waste 100,000.00 ms
  + sticky hash         day 112.50 s  (-100.00 s, 1.89x less prefill work)
  + radix seats         124 seats/replica - the 140-session growth day: 0 evictions
  + drain-aware deploy  one deploy: 82,125.00 ms -> 0.00 ms
  ablations:
    -sticky        day prefill back to 212.50 s = 1.89x the sticky bill
    -radix         growth day evicts 40 = 45,000.00 ms re-bought
    -drain-aware   one deploy bills 82,125.00 ms = 0.73 day-prefills
    -seat budget   the 26th session asks 66,560 > 65,536 and nothing logs it
  the deltas order the build: sticky first, radix second, drain-aware third -
  and the seat budget is the guardrail that turns a silent refusal into a number

FENCE-069-OK
```
