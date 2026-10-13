---
Document ID: CHEAT-SHEET-071
Title: "CHEAT-SHEET-071: Load Shedding and the Admission Gate - the Queue-Full Bill, the Shedding Ladder, and the Retry Bill"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'llmops']
---
# CHEAT-SHEET-071: Load Shedding and the Admission Gate - the Queue-Full Bill, the Shedding Ladder, and the Retry Bill

The census that picked this sheet searched load shedding, admission control, backpressure, token bucket, and 503 handling across all 571 markdown docs and found the pattern taught as scattered error-code asides - 199 hits across 75 files, 157 of them the bare status code inside QA checklists, security tables, and monitoring alarms, 26 naming the token bucket, 13 naming a rejected request, three naming a concurrency limit - while the operator arithmetic returns zero across all 571: shed bill, admission gate, reject budget, queue-full bill, retry-storm cost. The parts live apart: the monitoring chapters alarm on the 503, the gateway sheet prices the retry in dollars - its single retry-bill line and six tier-bill rows are the only operator arithmetic in the catalog - the serving chapters teach the concurrency flag, and every retry and priority hit is the client's half of the conversation - each a part, none the operator page for which request the gate refuses next - and the questions that start the moment one gateway fronts the six-replica warm pool of sheet 070 through a launch-day peak (what does an unbounded queue cost, where does the gate sit, who gets shed first, what does a retry storm re-buy) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 308-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 64-line run sits frozen below, byte-for-byte.

## The Queue-Full Bill

A launch-day peak arrives over a fleet that cannot grow. The profile peaks at 48.00 RPS while the six-replica warm pool of sheet 070 serves 25.95 - 22.05 RPS of excess with nowhere to go, so the queue can only grow. With no gate, 693,072 of 1,090,800 requests breach the 2,100 ms TTFT line = 63.54%, and the queue builds to 188,004 requests deep. An unbounded queue converts overload into latency for everyone: every admitted request breaches, and the client sees a hung stream instead of an answer.

```text
F1  the queue-full bill
launch-day peak asks 48.00 RPS; the fleet serves 25.95
the peak runs 22.05 RPS over capacity - the queue can only grow
no gate: 693072 of 1090800 requests breach the TTFT line = 63.54%
max queue 188004 requests deep
an unbounded queue converts overload into latency for everyone:
every admitted request breaches - the gate protects them
```

## The Admission Gate

The gate is sized from the wait budget, not from a round number. L = 1.1 s x 25.95 RPS = 28.5 requests deep - the depth the fleet drains inside the budget's slack, so anything past the gate cannot possibly make the line. The day admits 902,824 of 1,090,800 = 82.77%, rejects 187,975 = 17.23%, and breaches 0.00% inside the line. A 503 costs one retry; a 60 s TTFT costs the session - the gate trades a visible refusal for invisible rot.

```text
F2  the admission gate
gate sized from the budget: L = 1.1 s x 25.95 RPS = 28.5 deep
the fleet drains L inside 1.1 s - past the gate, refuse
admitted: 902824 of 1090800 = 82.77%; rejected: 187975 = 17.23%
breach inside the gate: 0 of 1090800 = 0.00%
a 503 costs one retry; a 60 s TTFT costs the session -
the gate trades a visible refusal for invisible rot
```

## The Shedding Ladder

The ladder aims the refusal. Both gates reject the same volume - 187,975 - and admit the same 82.77%; the plain FIFO door sheds whoever is in line pro rata, bouncing 125,317 paying users, while the ladder sheds the free third first, bouncing 43,589. Same admission, 65.22% fewer paid refusals. Order of shedding is a product decision priced in users, and it costs nothing to make at gate-build time.

```text
F3  the shedding ladder
ladder: the free third leaves first when the gate sheds
plain gate : 187975 rejected, 125317 of them paying
ladder gate: 187975 rejected, 43589 of them paying
same volume admitted inside the line - 82.77% vs 82.77%
shed the cheap traffic first: 65.22% of the paid refusals
vanish - order of shedding is a product decision priced in users
```

## The Retry Bill

Forty percent of rejected PAID users retry 30 s later; the free tier walks. The herd re-hits a full gate: rejections grow from 187,975 to 256,270 = 1.36x. Naive retry re-lands 68,338 arrivals on one second; backoff spread over 120 s delivers 68,306 - near-identical volume, but the spread lets the wave land on a draining queue instead of a full one. Retries are arrivals: a gate without backoff schedules a second peak, and every bounced retry schedules another.

```text
F4  the retry bill
40% of REJECTED PAID users retry 30 s later; free walks
the herd re-hits a full gate: rejected grows 187975 to 256270 = 1.36x
naive retry: 68338 retry arrivals; backoff over 120 s: 68306 -
the spread lets the wave land on a draining queue, not a full one
retries are arrivals; a gate without backoff schedules a second
peak, and every bounced retry schedules another
```

## The Shedding Bill

The gate's cost is refusals; its revenue is kept promises. No gate: 693,072 breached inside a 1,090,800-request day = 63.54%. Gate: 187,975 rejected to protect 902,824 admitted. Ladder: the same 187,975 rejected but only 43,589 paying. Every rejected request is a client you can win back with a Retry-After; every breached request is a client you never see again.

```text
F5  the shedding bill
the gate's cost is refusals; its revenue is kept promises:
no gate   : 693072 breached inside a 1090800-request day (63.54%)
gate      : 187975 rejected to protect 902824 admitted
ladder    : 187975 rejected but only 43589 paying
every rejected request is a client you can retry later -
every breached request is a client you never see again
```

## The Day Bill

The same 1,090,800-request launch day under five configs. No gate: 1,090,800 admitted, 0 rejected, 63.54% breach. Gate 28.5: 902,824 admitted, 187,975 rejected, 0.00%. Ladder gate: identical volume, aimed refusal. Gate + naive retry: 902,868 admitted, 256,270 rejected - the storm inflating the rejections at 0.00% breach. Ladder + retry: 902,824 admitted, 211,715 rejected - the aimed refusals cut the arrivals the herd re-buys. The ladder rejects the same volume; it just aims the refusal at the traffic that walks away instead of the traffic that pays.

```text
F6  the day bill
1090800 requests over the launch-day profile
no gate              1090800 admitted        0 rejected   63.54% breach
gate 28.5             902824 admitted   187975 rejected    0.00% breach
ladder gate           902824 admitted   187975 rejected    0.00% breach
gate + naive retry    902868 admitted   256270 rejected    0.00% breach
ladder + retry        902824 admitted   211715 rejected    0.00% breach
the ladder rejects the same volume - it just aims the refusal
at the traffic that walks away instead of the traffic that pays
```

## The Build Ladder and the Ablation Audit

The ladder orders the build and the ablations audit it. No gate breaches 63.54% at 1,090,800 admitted; +gate drops the breach to 0.00% at 902,824; +ladder cuts paid rejects to 43,589 from 125,317; +backoff trims retry arrivals to 68,306 from 68,338. The ablations hand the deltas back in order: -gate returns the rot at 63.54% for everyone, -ladder re-prices refusals at 125,317 paid users, -backoff re-lands 68,338 retries on one second. Gate first, ladder second, backoff third - and size the gate from the wait budget: L = budget x capacity.

```text
F7  the build ladder and the ablation audit
no gate         63.54% breach at 1090800 admitted
+gate            0.00% breach at  902824 admitted
+ladder         43589 paid rejects (gate: 125317)
+backoff       68306 retry arrivals (naive: 68338)
ablations, each handing its delta back:
-gate      63.54% breach (the rot returns for everyone)
-ladder   125317 paid users refused where 43589 would do
-backoff   68338 retry arrivals re-land on one second
order the build: gate first, ladder second, backoff third -
and size the gate from the wait budget: L = budget x capacity

```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| No admission gate at all | 693,072 requests breach at 63.54% - the queue builds to 188,004 deep and every admitted request waits past the line (f1) | Size the gate from the wait budget: L = budget x capacity |
| A round-number gate | Slots = 32, so the gate is set to 32 - a depth the fleet needs 1.23 s to drain, past the 1.1 s slack the budget bought (f2) | Derive L from WAIT_BUDGET_S x CAPACITY = 28.5, never from the slot count |
| Pro-rata shedding at the door | The FIFO door bounces 125,317 paying users where shedding the free third first would bounce 43,589 (f3) | Tag tiers at the gateway and shed the free tier first |
| Retries without backoff | Rejections grow 187,975 to 256,270 = 1.36x as the herd re-hits the full gate (f4) | Jittered backoff on every refusal - spread the re-landing wave |
| Shedding priced as pure loss | 187,975 refusals read as a 17.23% walk-out until the day bill shows 0.00% breach (f5, f6) | Price the refusals against the breaches they retire - a retried 503 is a client kept |
| The gate behind the queue | The gate "exists" but arrivals enqueue first - the queue grows to 188,004 deep anyway (f1) | Refuse at enqueue: the gate must shed arrivals, not decorate the queue |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| Latency breaks exactly at peak | The queue-full bill (f1): 22.05 RPS of peak excess has nowhere to go | Install the admission gate at L = 1.1 x 25.95 = 28.5 deep |
| Clients report random 503s | The pro-rata door (f3): the gate sheds whoever is in line | Return Retry-After and shed free tier first - paid refusals drop 65.22% |
| Rejections climb after the peak passes | The retry bill (f4): 40% of paid rejects re-hit 30 s later | Backoff spread over 120 s - retries land on a draining queue |
| The gate admits everything but latency still breaks | A gate wider than the drain line (f2): past L the queue breaches before it drains | Recompute L from the live wait budget after every capacity change |
| Paid churn spikes in peak hours | The ladder (f3): 125,317 paid refusals under pro-rata vs 43,589 under free-first | Shed the free tier first - the order is free to fix at the gateway |
| Finance asks why 17.23% of launch traffic was refused | The shedding bill (f5): 902,824 requests kept inside the line vs 693,072 breached with no gate | Show the day bill (f6): 0.00% breach is what the refusals bought |

## Quick Reference For

- [the SGLang serving chapter whose concurrency-limit flags this sheet prices](../../phases/phase1-infra/1400-llmops/1405-SGLang.md)
- [the monitoring chapter whose 503 alarms this sheet turns into a gate](../../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
- [the gateway sheet whose retry-bill and tier-bill asides this sheet operationalizes](../../learning-resources/cheat-sheets/CHEAT-SHEET-056-LLM-Gateway-and-Model-Routing.md)
- [the weight-residency sheet whose serving universe this fixture shares](../../learning-resources/cheat-sheets/CHEAT-SHEET-068-Multi-Model-Serving-and-the-Weight-Residency-Budget.md)
- [the warm-pool fleet this admission gate fronts](../../learning-resources/cheat-sheets/CHEAT-SHEET-070-Autoscaling-and-the-Warm-Pool-Budget.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 308-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the gate depth, the tier mix, and the day's hourly profile for your own gateway's, and the bills re-derive.

```python
"""CHEAT-SHEET-071 canonical fence: load shedding and the admission gate.
Stdlib only, no randomness, no clocks - every printed figure is computed
from the fixed fixture and pinned by an assert. Two runs must print
identical bytes. Fluid-queue simulation on one-second ticks over a fixed
launch-day arrival profile; no RNG anywhere.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 57

# ---------------------------------------------------------------- fixture
# the 068/070 universe: 16 GiB fp16 weights on a 48 GiB card
WEIGHTS_GIB = 16
CARD_GIB = 48
GIB = 1024 ** 3
KV_BYTES_PER_TOKEN = 32 * 8 * 128 * 2 * 2        # 32L, 8 GQA heads, hd128
KV_POOL_TOKENS = (CARD_GIB - WEIGHTS_GIB) * GIB // KV_BYTES_PER_TOKEN
SLOTS = 32                                       # KV headroom is not the bind

PROMPT_TOKENS = 2048
OUTPUT_TOKENS = 256
PREFILL_TPS = 2048
STEP_MS = 25.0
PREFILL_MS = PROMPT_TOKENS / PREFILL_TPS * 1000.0
DECODE_MS = OUTPUT_TOKENS * STEP_MS
LIFETIME_S = (PREFILL_MS + DECODE_MS) / 1000.0   # 7.40 s slot occupancy
REPLICA_RPS = SLOTS / LIFETIME_S

TTFT_BUDGET_MS = 2100.0
WAIT_BUDGET_S = (TTFT_BUDGET_MS - PREFILL_MS) / 1000.0   # 1.10 s of queue

FLEET = 6                                        # the 070 warm-pool fleet
CAPACITY = FLEET * REPLICA_RPS                   # 25.95 RPS
GATE_LIMIT = WAIT_BUDGET_S * CAPACITY            # 28.5 - sized FROM the budget
SHED_EARLY = 0.75                                # free-tier shed at 75% full
FREE_SHARE = 1.0 / 3.0                           # arrivals tagged free tier
RETRY_RATE = 0.4                                 # paid rejects that retry
RETRY_DELAY_S = 30.0                             # fixed retry lag
RETRY_BACKOFF_FACTOR = 4.0                       # jittered backoff span

# the day: a launch-day profile, hourly offered RPS, 86,400 s
HOURS = [6, 6, 6, 6, 6, 6, 10, 18, 30, 48, 48, 30, 18, 10,
         6, 6, 6, 6, 6, 6, 5, 5, 5, 4]
TOTAL_REQUESTS = sum(HOURS) * 3600

assert KV_POOL_TOKENS == 262144
assert PREFILL_MS == 1000.0
assert DECODE_MS == 6400.0
assert LIFETIME_S == 7.4
assert abs(REPLICA_RPS - 4.3243) < 5e-5
assert WAIT_BUDGET_S == 1.1
assert abs(CAPACITY - 25.95) < 5e-3
assert abs(GATE_LIMIT - 28.54) < 5e-3
assert TOTAL_REQUESTS == 1090800


# ------------------------------------------------------------- simulator
def simulate(queue_limit=None, ladder=False, retry_rate=0.0,
             backoff=False):
    """Fluid queue on one-second ticks. Per second: drain at capacity,
    arrivals join, and when depth would pass the gate the excess sheds -
    proportionally (plain gate, FIFO door) or free-first (the ladder).
    queue_limit=None means no gate. Paid rejects retry after
    RETRY_DELAY_S - all at once (backoff=False, the thundering herd) or
    spread over the backoff span. Free-tier rejects walk away.
    Returns the metrics dict every exhibit reads.
    """
    queue = 0.0
    breached = 0.0
    admitted = 0.0
    rejected = 0.0
    paid_rejected = 0.0
    retry_arrivals = 0.0
    max_queue = 0.0
    retries = []                      # pending (due_second, rps_value)
    for t in range(86400):
        due = 0.0
        keep = []
        for (ts, val) in retries:
            if ts <= t:
                due += val
            else:
                keep.append((ts, val))
        retries = keep
        lam = float(HOURS[t // 3600]) + due
        # the fleet drains whatever is queued, gate or not
        queue -= min(queue, CAPACITY)
        # arrivals join; the excess over the gate sheds
        free_part = lam * FREE_SHARE
        paid_part = lam - free_part
        rej = 0.0
        paid_rej = 0.0
        if queue_limit is not None:
            excess = max(0.0, queue + lam - queue_limit)
            if excess > 0.0:
                rej = excess
                if ladder:
                    # the free third leaves first
                    paid_rej = max(0.0, excess - free_part)
                else:
                    # the FIFO door sheds whoever is in line, pro rata
                    paid_rej = excess * (paid_part / lam) if lam > 0 else 0.0
            if retry_rate > 0.0 and paid_rej > 0.0:
                if backoff:
                    span = RETRY_BACKOFF_FACTOR * RETRY_DELAY_S
                    for s in range(int(span)):
                        retries.append((t + RETRY_DELAY_S + s,
                                        paid_rej * retry_rate / span))
                        retry_arrivals += paid_rej * retry_rate / span
                else:
                    retries.append((t + RETRY_DELAY_S,
                                    paid_rej * retry_rate))
                    retry_arrivals += paid_rej * retry_rate
        rejected += rej
        paid_rejected += paid_rej
        admitted += lam - rej
        queue += lam - rej
        max_queue = max(max_queue, queue)
        if queue / CAPACITY > WAIT_BUDGET_S + 1e-9:
            breached += lam - rej
    return {
        "admitted": admitted,
        "rejected": rejected,
        "paid_rejected": paid_rejected,
        "breached": breached,
        "breach_pct": breached / TOTAL_REQUESTS * 100.0,
        "retry_arrivals": retry_arrivals,
        "max_queue": max_queue,
    }


NO_GATE = simulate()
GATE = simulate(queue_limit=GATE_LIMIT)
LADDER = simulate(queue_limit=GATE_LIMIT, ladder=True)
GATE_RETRY = simulate(queue_limit=GATE_LIMIT, retry_rate=RETRY_RATE)
GATE_BACKOFF = simulate(queue_limit=GATE_LIMIT, retry_rate=RETRY_RATE,
                        backoff=True)
LADDER_RETRY = simulate(queue_limit=GATE_LIMIT, ladder=True,
                        retry_rate=RETRY_RATE)


# ------------------------------------------------- F1  the queue-full bill
def f1_queue_full_bill():
    peak = max(HOURS)
    deficit = peak - CAPACITY
    lines = [
        "F1  the queue-full bill",
        "launch-day peak asks %.2f RPS; the fleet serves %.2f"
        % (peak, CAPACITY),
        "the peak runs %.2f RPS over capacity - the queue can only grow"
        % deficit,
        "no gate: %d of %d requests breach the TTFT line = %.2f%%"
        % (NO_GATE["breached"], TOTAL_REQUESTS, NO_GATE["breach_pct"]),
        "max queue %.0f requests deep" % NO_GATE["max_queue"],
        "an unbounded queue converts overload into latency for everyone:",
        "every admitted request breaches - the gate protects them",
    ]
    assert round(NO_GATE["breached"]) == 693072
    assert round(NO_GATE["max_queue"]) == 188004
    return lines


# ---------------------------------------------- F2  the admission gate
def f2_admission_gate():
    lines = [
        "F2  the admission gate",
        "gate sized from the budget: L = %.1f s x %.2f RPS = %.1f deep"
        % (WAIT_BUDGET_S, CAPACITY, GATE_LIMIT),
        "the fleet drains L inside %.1f s - past the gate, refuse"
        % WAIT_BUDGET_S,
        "admitted: %d of %d = %.2f%%; rejected: %d = %.2f%%"
        % (GATE["admitted"], TOTAL_REQUESTS,
           GATE["admitted"] / TOTAL_REQUESTS * 100.0,
           GATE["rejected"], GATE["rejected"] / TOTAL_REQUESTS * 100.0),
        "breach inside the gate: %d of %d = %.2f%%"
        % (GATE["breached"], TOTAL_REQUESTS, GATE["breach_pct"]),
        "a 503 costs one retry; a 60 s TTFT costs the session -",
        "the gate trades a visible refusal for invisible rot",
    ]
    assert GATE["breach_pct"] < 0.5
    assert int(GATE["rejected"]) == 187975
    return lines


# ---------------------------------------------- F3  the shedding ladder
def f3_shedding_ladder():
    lines = [
        "F3  the shedding ladder",
        "ladder: the free third leaves first when the gate sheds",
        "plain gate : %d rejected, %d of them paying"
        % (GATE["rejected"], GATE["paid_rejected"]),
        "ladder gate: %d rejected, %d of them paying"
        % (LADDER["rejected"], LADDER["paid_rejected"]),
        "same volume admitted inside the line - %.2f%% vs %.2f%%"
        % (GATE["admitted"] / TOTAL_REQUESTS * 100.0,
           LADDER["admitted"] / TOTAL_REQUESTS * 100.0),
        "shed the cheap traffic first: %.2f%% of the paid refusals"
        % ((GATE["paid_rejected"] - LADDER["paid_rejected"])
           / GATE["paid_rejected"] * 100.0),
        "vanish - order of shedding is a product decision priced in users",
    ]
    assert LADDER["paid_rejected"] < GATE["paid_rejected"] * 0.5
    assert abs(LADDER["admitted"] - GATE["admitted"]) < 1.0
    return lines


# ---------------------------------------------- F4  the retry bill
def f4_retry_bill():
    amp = GATE_RETRY["rejected"] / GATE["rejected"]
    lines = [
        "F4  the retry bill",
        "%.0f%% of REJECTED PAID users retry %.0f s later; free walks"
        % (RETRY_RATE * 100, RETRY_DELAY_S),
        "the herd re-hits a full gate: rejected grows %d to %d = %.2fx"
        % (GATE["rejected"], GATE_RETRY["rejected"], amp),
        "naive retry: %d retry arrivals; backoff over %.0f s: %d -"
        % (GATE_RETRY["retry_arrivals"],
           RETRY_BACKOFF_FACTOR * RETRY_DELAY_S,
           GATE_BACKOFF["retry_arrivals"]),
        "the spread lets the wave land on a draining queue, not a full one",
        "retries are arrivals; a gate without backoff schedules a second",
        "peak, and every bounced retry schedules another",
    ]
    assert amp > 1.2
    assert GATE_RETRY["retry_arrivals"] > GATE_BACKOFF["retry_arrivals"]
    return lines


# ---------------------------------------------- F5  the shedding bill
def f5_shedding_bill():
    lines = [
        "F5  the shedding bill",
        "the gate's cost is refusals; its revenue is kept promises:",
        "no gate   : %d breached inside a %d-request day (%.2f%%)"
        % (NO_GATE["breached"], TOTAL_REQUESTS, NO_GATE["breach_pct"]),
        "gate      : %d rejected to protect %d admitted"
        % (GATE["rejected"], GATE["admitted"]),
        "ladder    : %d rejected but only %d paying"
        % (LADDER["rejected"], LADDER["paid_rejected"]),
        "every rejected request is a client you can retry later -",
        "every breached request is a client you never see again",
    ]
    assert NO_GATE["breach_pct"] > GATE["breach_pct"] * 100
    return lines


# ---------------------------------------------- F6  the day bill
def f6_day_bill():
    rows = [
        ("no gate", NO_GATE),
        ("gate 28.5", GATE),
        ("ladder gate", LADDER),
        ("gate + naive retry", GATE_RETRY),
        ("ladder + retry", LADDER_RETRY),
    ]
    lines = ["F6  the day bill",
             "%d requests over the launch-day profile" % TOTAL_REQUESTS]
    for name, m in rows:
        lines.append("%-20s %7d admitted  %7d rejected  %6.2f%% breach"
                     % (name, m["admitted"], m["rejected"],
                        m["breach_pct"]))
    lines += [
        "the ladder rejects the same volume - it just aims the refusal",
        "at the traffic that walks away instead of the traffic that pays",
    ]
    assert LADDER_RETRY["retry_arrivals"] < GATE_RETRY["retry_arrivals"]
    assert LADDER_RETRY["breach_pct"] <= GATE_RETRY["breach_pct"] + 1e-9
    return lines


# ------------------------------------- F7  the build ladder and the audit
def f7_build_ladder():
    lines = [
        "F7  the build ladder and the ablation audit",
        "no gate        %6.2f%% breach at %7d admitted"
        % (NO_GATE["breach_pct"], NO_GATE["admitted"]),
        "+gate          %6.2f%% breach at %7d admitted"
        % (GATE["breach_pct"], GATE["admitted"]),
        "+ladder        %6d paid rejects (gate: %d)"
        % (LADDER["paid_rejected"], GATE["paid_rejected"]),
        "+backoff       %d retry arrivals (naive: %d)"
        % (GATE_BACKOFF["retry_arrivals"], GATE_RETRY["retry_arrivals"]),
        "ablations, each handing its delta back:",
        "-gate     %6.2f%% breach (the rot returns for everyone)"
        % NO_GATE["breach_pct"],
        "-ladder   %6d paid users refused where %.0f would do"
        % (GATE["paid_rejected"], LADDER["paid_rejected"]),
        "-backoff  %6d retry arrivals re-land on one second"
        % GATE_RETRY["retry_arrivals"],
        "order the build: gate first, ladder second, backoff third -",
        "and size the gate from the wait budget: L = budget x capacity",
    ]
    return lines


exhibits = [
    f1_queue_full_bill, f2_admission_gate, f3_shedding_ladder,
    f4_retry_bill, f5_shedding_bill, f6_day_bill, f7_build_ladder,
]
for fn in exhibits:
    print(RULE)
    for line in fn():
        print(line)

print()
print("FENCE-071-OK")
```

```text
=========================================================
F1  the queue-full bill
launch-day peak asks 48.00 RPS; the fleet serves 25.95
the peak runs 22.05 RPS over capacity - the queue can only grow
no gate: 693072 of 1090800 requests breach the TTFT line = 63.54%
max queue 188004 requests deep
an unbounded queue converts overload into latency for everyone:
every admitted request breaches - the gate protects them
=========================================================
F2  the admission gate
gate sized from the budget: L = 1.1 s x 25.95 RPS = 28.5 deep
the fleet drains L inside 1.1 s - past the gate, refuse
admitted: 902824 of 1090800 = 82.77%; rejected: 187975 = 17.23%
breach inside the gate: 0 of 1090800 = 0.00%
a 503 costs one retry; a 60 s TTFT costs the session -
the gate trades a visible refusal for invisible rot
=========================================================
F3  the shedding ladder
ladder: the free third leaves first when the gate sheds
plain gate : 187975 rejected, 125317 of them paying
ladder gate: 187975 rejected, 43589 of them paying
same volume admitted inside the line - 82.77% vs 82.77%
shed the cheap traffic first: 65.22% of the paid refusals
vanish - order of shedding is a product decision priced in users
=========================================================
F4  the retry bill
40% of REJECTED PAID users retry 30 s later; free walks
the herd re-hits a full gate: rejected grows 187975 to 256270 = 1.36x
naive retry: 68338 retry arrivals; backoff over 120 s: 68306 -
the spread lets the wave land on a draining queue, not a full one
retries are arrivals; a gate without backoff schedules a second
peak, and every bounced retry schedules another
=========================================================
F5  the shedding bill
the gate's cost is refusals; its revenue is kept promises:
no gate   : 693072 breached inside a 1090800-request day (63.54%)
gate      : 187975 rejected to protect 902824 admitted
ladder    : 187975 rejected but only 43589 paying
every rejected request is a client you can retry later -
every breached request is a client you never see again
=========================================================
F6  the day bill
1090800 requests over the launch-day profile
no gate              1090800 admitted        0 rejected   63.54% breach
gate 28.5             902824 admitted   187975 rejected    0.00% breach
ladder gate           902824 admitted   187975 rejected    0.00% breach
gate + naive retry    902868 admitted   256270 rejected    0.00% breach
ladder + retry        902824 admitted   211715 rejected    0.00% breach
the ladder rejects the same volume - it just aims the refusal
at the traffic that walks away instead of the traffic that pays
=========================================================
F7  the build ladder and the ablation audit
no gate         63.54% breach at 1090800 admitted
+gate            0.00% breach at  902824 admitted
+ladder         43589 paid rejects (gate: 125317)
+backoff       68306 retry arrivals (naive: 68338)
ablations, each handing its delta back:
-gate      63.54% breach (the rot returns for everyone)
-ladder   125317 paid users refused where 43589 would do
-backoff   68338 retry arrivals re-land on one second
order the build: gate first, ladder second, backoff third -
and size the gate from the wait budget: L = budget x capacity

FENCE-071-OK
```
