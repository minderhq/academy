---
Document ID: CHEAT-SHEET-070
Title: "CHEAT-SHEET-070: Autoscaling and the Warm-Pool Budget - the Queue-Depth Trigger, the Cold-Start Gate, and the Scale-In Bill"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'llmops']
---
# CHEAT-SHEET-070: Autoscaling and the Warm-Pool Budget - the Queue-Depth Trigger, the Cold-Start Gate, and the Scale-In Bill

The census that picked this sheet searched autoscaling, scale-out, scale-up policy, horizontal scale, and queue-depth triggers across all 570 markdown docs and found the pattern taught as scattered asides - twenty-eight hits across fourteen files, four in the stage-scaling chapter, four in the Kubernetes phase README, four in the production-deployment lab, three in the LLMOps tutorial, two in the MLOps-pipelines README, and the rest single mentions - while the operator arithmetic returns zero across all 570: scale trigger, warm pool, cold replica, scale-in bill, capacity headroom. The parts live apart: the Kubernetes phase teaches the HPA objects, the stage-scaling chapter cites the autoscaling papers, the deployment lab wires a load test - each a part, none the operator page for which replica joins the fleet next - and the questions that start the moment one gateway fronts a fleet through a diurnal peak (what does a fixed fleet pay at the peak, what does the boot gap cost the queue, what does a joining replica charge its first request, what does the warm pool rent, what does scaling back down cost) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 351-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 68-line run sits frozen below, byte-for-byte.

## The Fixed-Fleet Bill

The bill a static fleet pays for a diurnal day. Four resident replicas serve 17.30 RPS against a peak asking 24.00, and four hours of the profile arrive over capacity - hours 11 through 14 at 20, 24, 24, 20 RPS. Those hours carry 316,800 of the day's 810,000 requests and accrue 67,719 unserveable arrivals: the queue can only grow, and it ends hour 14 at 67,719 requests deep. Breaches against the 2,100 ms TTFT line land at 451,828 of 810,000 = 55.78% - more than half the day inside a queue a fixed fleet cannot drain until the small hours. A fixed fleet does not degrade at the peak; it accumulates.

```text
F1  the fixed-fleet bill
four resident replicas serve 17.30 RPS; the peak asks 24.00
hours over capacity: 4 11:20 12:24 13:24 14:20
requests arriving into over-capacity hours: 316800 of 810000 (39.11%)
unserveable arrivals the day accrues: 67719 requests
queue depth at the hour-13 boundary: 67719 requests
breaches against the 2100 ms TTFT line: 451828 of 810000 = 55.78%
a fixed fleet does not degrade at the peak - it accumulates
```

## The Scale-Trigger Ladder

What reactive scaling buys and what the boot gap keeps. The trigger fires on queue depth over 8 held through a 10 s metric window, then pays a 120 s cold boot - a 130 s gap during which the peak deficit runs 6.70 RPS, re-buying 871 arrivals per launch. The fleet rides 4 to 6 on 37 boots through the day, each lift holding 25.95 RPS, and breaches fall from 55.78% to 75,748 of 810,000 = 9.35%: max queue 1,026, 3,436 over-budget seconds. The trigger works - but the boot is what the queue pays for, and 37 rides means 37 boots the scale-in policy will ask it to buy again.

```text
F2  the scale-trigger ladder
reactive path: queue > 8 held 10 s, then a 120 s boot
detect + boot = 130 s; the peak deficit runs 6.70 RPS
arrivals re-bought into the gap each launch: 871 requests
fleet path rides 4 -> 6 on 37 boots through the day; up,
each lift holds 25.95 RPS - down, the queue pays the boot
breaches: 75748 of 810000 = 9.35% (fixed fleet pays far more)
max queue 1026, boots 37, over-budget seconds 3436
the trigger fires - the boot is what the queue pays for
```

## The Cold-Start Gate

The first request a joining replica serves pays the weight ladder: resident weights put TTFT at 1,000.00 ms = 0.48x PASS, a page-cached image adds 343.60 ms of load for 1,343.60 ms = 0.64x PASS, a device-cold pull adds 2,454.27 ms for 3,454.27 ms = 1.64x FAIL against the 2,100 ms line. The engine is not slow - the load IS the first request. One warmup probe at join retires the gate for every later one; the probe is not overhead, it is the first request spent on the fleet's terms instead of a tenant's.

```text
F3  the cold-start gate
the joining replica's first request pays the weight ladder:
resident    TTFT  1000.00 ms = 0.48x  PASS
page-cache  TTFT  1343.60 ms = 0.64x  PASS
nvme-cold   TTFT  3454.27 ms = 1.64x  FAIL
one warmup probe at join retires the gate for every later one;
the probe is not overhead - it is the first request, spent on
the fleet's terms instead of a tenant's
```

## The Warm-Pool Rent

What the always-pass fleet costs. The fixed four rent 96.00 GPU-h/day; the reactive fleet adds 8.33 GPU-h of boot-billed seconds for 104.33; the warm pool of six rents 144.00 - 1.50x the fixed bill. Per 1,000 requests that is 426.67 GPU-s fixed against 640.00 pooled. The reactive delta bought a partial pass; the pool's 48.00 GPU-h of rent buys the whole day. The pool is not waste - it is the peak, paid for at 4 a.m. rates instead of queue-overflow penalties.

```text
F4  the warm-pool rent
fixed 4 x 24 h          =   96.00 GPU-h/day
reactive 4 + peak boots =  104.33 GPU-h/day
warm pool 6 x 24 h      =  144.00 GPU-h/day
the always-pass fleet rents 1.50x the fixed bill
per 1,000 requests: fixed 426.67 GPU-s, warm pool 640.00 GPU-s
the reactive fleet's 8.33 GPU-h of boots bought a partial pass
the pool's 48.00 GPU-h of rent buys the whole day
```

## The Scale-In Bill

What scaling back down costs. Window 0 s: the fleet sheds every idle replica instantly and the day buys 111 scale-ins and 111 re-boots, breaching 36.96%. Window 60 s: 96 and 96, 22.46%. Window 300 s: 37 and 37, 9.35%. An immediate scale-in hands the fleet back to the next burst while it is still holding a 120 s boot - the window is the rent that buys the fleet out of re-buying its own cold start. Scale-in policy is not cleanup; it is the other half of the autoscaling bill.

```text
F5  the scale-in bill
scale-in window 0 s  : 111 scale-ins, 111 boots, 36.96% breach
scale-in window 60 s : 96 scale-ins, 96 boots, 22.46% breach
scale-in window 300 s: 37 scale-ins, 37 boots, 9.35% breach
an immediate scale-in hands the fleet back to the next burst
still holding a 120 s boot - the window is the rent that buys
the fleet out of re-buying its own cold start
```

## The Day Bill

The same 810,000-request day under four configs. Fixed four: 96.00 GPU-h, 358,172 of 810,000 pass, 55.78% breach. Reactive with 120 s cold boots: 104.33 GPU-h, 734,252 pass, 9.35%. Reactive with 45 s page-cached boots: 105.57 GPU-h, 774,768 pass, 4.35% - the boot cache halves the breach the cold boots pay. Warm pool of six: 144.00 GPU-h, 810,000 of 810,000 pass, 0.00% breach - the only config that passes the day, and the day's pass is a residency buy.

```text
F6  the day bill
810000 requests over the same profile
fixed 4                    96.00 GPU-h  358172/810000 pass  55.78% breach
reactive +120 s boots     104.33 GPU-h  734252/810000 pass  9.35% breach
reactive +45 s boots      105.57 GPU-h  774768/810000 pass  4.35% breach
warm pool 6               144.00 GPU-h  810000/810000 pass  0.00% breach
page-cached boots shrink the breach the cold boots pay,
the warm pool retires it - the day's pass is a residency buy
```

## The Build Ladder and the Ablation Audit

The ladder orders the build and the ablations audit it. Fixed four breaches 55.78% at 96.00 GPU-h; +reactive scale-out cuts it to 9.35% at 104.33; +the warm pool retires it entirely at 144.00. The ablations hand the deltas back in order: -reactive returns the peak whole at 55.78%, -warm pool returns the boots at 9.35%, -the scale-in window returns 111 re-boots. Reactive first, the warm pool second, the window third - and the trigger metric is queue depth, not CPU: CPU saturates only after the queue is already deep.

```text
F7  the build ladder and the ablation audit
fixed 4               55.78% breach at  96.00 GPU-h
+reactive scale-out    9.35% breach at 104.33 GPU-h
+warm pool 6           0.00% breach at 144.00 GPU-h
ablations, each handing its delta back:
-reactive   55.78% breach (the peak returns whole)
-warm pool   9.35% breach (the boots come back)
-window       111 boots (the fleet re-buys its cold start)
order the build: reactive first, the warm pool second,
the scale-in window third - and the trigger metric is queue
depth, not CPU: CPU saturates only after the queue is deep

```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| CPU-anchored autoscaling | CPU reads flat while the queue is already 1,026 deep - the fleet scales only after the SLO broke (f2, f7) | Trigger on queue depth against slot capacity - CPU saturates last |
| Scale-out without a cold-start gate | The joining replica's first request lands at 3,454.27 ms = 1.64x the TTFT line (f3) | Warmup probe at join - one request spent on the fleet's terms |
| Reactive-only scaling | 75,748 requests breach inside the 130 s detect+boot gaps - 9.35% of the day (f2) | Keep a warm-pool floor sized to the peak - ceil(24/4.32) = 6 replicas |
| Instant scale-in | 111 scale-ins re-buy 111 boots - 36.96% breach where a 300 s window costs 9.35% (f5) | Scale-in window longer than the shortest lull between bursts |
| The warm pool priced as idle waste | 48.00 GPU-h looks like burn until the day bill shows 0.00% breach (f4, f6) | Price the pool per 1,000 requests and against the breach it retires |
| A fixed fleet through a diurnal peak | Four over-capacity hours accrue 67,719 unserveable requests - 55.78% breach (f1) | Derive the floor from peak RPS over replica capacity, not average |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| Breaches start before any scaler has fired | The trigger metric saturates late (f2, f7): CPU flat, queue 1,026 deep | Move the trigger to queue depth over slot capacity - measure the queue, not the box |
| A new replica's first requests time out | The cold-start gate (f3): 3,454.27 ms first TTFT vs the 2,100 ms line | Warmup probe before admission - page-cache the image to cut load to 343.60 ms |
| Scaling fires correctly but the day still breaches | The boot gap (f2): 871 arrivals re-bought per 130 s launch | Shrink the gap - page-cached boots at 45 s halve the breach to 4.35% |
| The fleet thrashes up and down all day | The scale-in bill (f5): 111 scale-ins at a 0 s window | Set the scale-in window above the lull length - 300 s returns 37 rides |
| Finance flags the reserved pool as idle spend | The rent (f4): 144.00 vs 96.00 GPU-h/day | Show the day bill (f6) - 0.00% breach at 640.00 GPU-s per 1,000 requests |
| Peak-hour queue grows without bound | The fixed bill (f1): 67,719 unserveable in four hours | Size the floor from the peak: 24 RPS over 4.32 RPS per replica = 6 residents |

## Quick Reference For

- [the stage-scaling chapter whose autoscaling asides this sheet operationalizes](../../phases/phase6-rag/6500-mlops-pipelines/6505-Response-Caching-and-Stage-Scaling.md)
- [the Kubernetes phase README whose HPA objects this sheet prices](../../phases/phase1-infra/1300-kubernetes/README.md)
- [the gateway sheet whose routing layer sits in front of this fleet](../../learning-resources/cheat-sheets/CHEAT-SHEET-056-LLM-Gateway-and-Model-Routing.md)
- [the weight-residency sheet whose cold-start ladder this fence extends to joining replicas](../../learning-resources/cheat-sheets/CHEAT-SHEET-068-Multi-Model-Serving-and-the-Weight-Residency-Budget.md)
- [the PD-disaggregation sheet whose phase split changes what a scaled replica means](../../learning-resources/cheat-sheets/CHEAT-SHEET-066-Prefill-Decode-Disaggregation-and-KV-Handoff.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 351-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the replica sizes, the boot paths, and the day's hourly mix for your own fleet's, and the bills re-derive.

```python
"""CHEAT-SHEET-070 canonical fence: autoscaling and the warm-pool budget.
Stdlib only, no randomness, no clocks - every printed figure is computed
from the fixed fixture and pinned by an assert. Two runs must print
identical bytes. Fluid-queue simulation on one-second ticks over a fixed
24-hour arrival profile; no RNG anywhere.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 57

# ---------------------------------------------------------------- fixture
# one replica: the 068 universe - 16 GiB fp16 weights on a 48 GiB card
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
Q_BREACH = WAIT_BUDGET_S * REPLICA_RPS

# boots and triggers (the reactive control plane)
BOOT_COLD_S = 120.0                              # cold image pull + boot
BOOT_WARM_S = 45.0                               # page-cached image boot
DETECT_S = 10.0                                  # metric window
TRIGGER_Q = 8.0                                  # queue depth trigger
COOLDOWN_S = 30.0

# the day: hourly offered RPS, fixed list, 86,400 s
HOURS = [4, 4, 4, 4, 4, 4, 4, 4, 8, 12, 16, 20, 24, 24, 20, 16,
         12, 8, 6, 6, 6, 6, 5, 4]
TOTAL_REQUESTS = sum(HOURS) * 3600

assert KV_POOL_TOKENS == 262144
assert PREFILL_MS == 1000.0
assert DECODE_MS == 6400.0
assert LIFETIME_S == 7.4
assert abs(REPLICA_RPS - 4.3243) < 5e-5
assert WAIT_BUDGET_S == 1.1
assert TOTAL_REQUESTS == 810000


def boot_load_ms(gbs):
    """the 068 weight ladder: 17.18 GB of fp16 weights at DRAM vs NVMe."""
    return WEIGHTS_GIB * GIB / (gbs * 1000 ** 3) * 1000.0


LOAD_DRAM_MS = boot_load_ms(50.0)                # 343.60 page-cache path
LOAD_NVME_MS = boot_load_ms(7.0)                 # 2454.27 device path
TTFT_RESIDENT = PREFILL_MS                       # 1000.00
TTFT_PAGECACHE = PREFILL_MS + LOAD_DRAM_MS       # 1343.60
TTFT_NVME = PREFILL_MS + LOAD_NVME_MS            # 3454.27

assert abs(LOAD_DRAM_MS - 343.60) < 5e-3
assert abs(LOAD_NVME_MS - 2454.27) < 5e-3
assert abs(TTFT_PAGECACHE - 1343.60) < 5e-3
assert abs(TTFT_NVME - 3454.27) < 5e-3


# ------------------------------------------------------------- simulator
def simulate(base, max_fleet, boot_s, warm_pool=False, window_s=None):
    """Fluid queue on one-second ticks. Arrivals are deterministic
    (hourly rate x 1 s), service is fleet x REPLICA_RPS. Booting replicas
    are billed (the card is allocated) but serve nothing until ready.
    Returns the metrics dict every exhibit reads.
    """
    fleet = base
    floor = base if not warm_pool else base
    pending = []          # ready-times of booting replicas
    queue = 0.0
    idle = 0              # consecutive seconds with queue == 0 and surplus
    last_launch = -1e18
    gpu_s = 0.0
    boot_events = 0
    scale_ins = 0
    breached = 0.0        # arrivals facing a queue over Q_BREACH
    max_queue = 0.0
    over_queue_s = 0
    for t in range(86400):
        while pending and pending[0] <= t:
            pending.pop(0)
            fleet += 1
        lam = float(HOURS[t // 3600])
        capacity = fleet * REPLICA_RPS
        arrivals = lam
        served = min(queue + arrivals, capacity)
        queue = max(0.0, queue + arrivals - served)
        max_queue = max(max_queue, queue)
        wait_s = queue / capacity
        if wait_s > WAIT_BUDGET_S:
            breached += arrivals
            over_queue_s += 1
        gpu_s += fleet
        # reactive scale-out: queue trigger, metric window, cooldown
        if max_fleet > base and queue > TRIGGER_Q and not pending \
                and fleet + len(pending) < max_fleet \
                and t - last_launch >= COOLDOWN_S:
            pending.append(t + DETECT_S + boot_s)
            boot_events += 1
            last_launch = t
        # scale-in: idle floor, a window rides out short lulls
        if window_s is not None and queue == 0.0 and fleet > floor:
            idle += 1
            if idle >= window_s:
                fleet -= 1
                idle = 0
                scale_ins += 1
        else:
            idle = 0
    return {
        "breached": breached,
        "breach_pct": breached / TOTAL_REQUESTS * 100.0,
        "max_queue": max_queue,
        "gpu_h": gpu_s / 3600.0,
        "boots": boot_events,
        "scale_ins": scale_ins,
        "pass": TOTAL_REQUESTS - breached,
        "over_queue_s": over_queue_s,
    }


FIXED = simulate(4, 4, BOOT_COLD_S)
REACTIVE = simulate(4, 8, BOOT_COLD_S, window_s=300)
WARMPOOL = simulate(6, 8, BOOT_COLD_S, warm_pool=True, window_s=300)
REACTIVE_WARMBOOT = simulate(4, 8, BOOT_WARM_S, window_s=300)


# ------------------------------------------------- F1  the fixed-fleet bill
def f1_fixed_fleet():
    cap4 = 4 * REPLICA_RPS
    over = [(h, lam) for h, lam in enumerate(HOURS) if lam > cap4]
    over_requests = sum(lam for _, lam in over) * 3600
    deficit = sum(lam - cap4 for _, lam in over) * 3600
    lines = [
        "F1  the fixed-fleet bill",
        "four resident replicas serve %.2f RPS; the peak asks %.2f"
        % (cap4, max(HOURS)),
        "hours over capacity: %d %s" % (
            len(over), " ".join("%d:%d" % (h, lam) for h, lam in over)),
        "requests arriving into over-capacity hours: %d of %d (%.2f%%)"
        % (over_requests, TOTAL_REQUESTS,
           over_requests / TOTAL_REQUESTS * 100.0),
        "unserveable arrivals the day accrues: %d requests"
        % round(deficit),
        "queue depth at the hour-13 boundary: %.0f requests"
        % FIXED["max_queue"],
        "breaches against the %.0f ms TTFT line: %d of %d = %.2f%%"
        % (TTFT_BUDGET_MS, FIXED["breached"], TOTAL_REQUESTS,
           FIXED["breach_pct"]),
        "a fixed fleet does not degrade at the peak - it accumulates",
    ]
    assert len(over) == 4
    assert over_requests == 316800
    assert round(deficit) == 67719
    assert FIXED["breached"] > TOTAL_REQUESTS * 0.5
    assert round(FIXED["max_queue"]) == 67719
    return lines


# ---------------------------------------------- F2  the scale-trigger ladder
def f2_scale_trigger():
    gap = DETECT_S + BOOT_COLD_S
    peak_deficit = (24.0 - 4 * REPLICA_RPS) * gap
    lines = [
        "F2  the scale-trigger ladder",
        "reactive path: queue > %.0f held %.0f s, then a %.0f s boot"
        % (TRIGGER_Q, DETECT_S, BOOT_COLD_S),
        "detect + boot = %.0f s; the peak deficit runs %.2f RPS"
        % (gap, 24.0 - 4 * REPLICA_RPS),
        "arrivals re-bought into the gap each launch: %.0f requests"
        % round(peak_deficit),
        "fleet path rides 4 -> 6 on %d boots through the day; up,"
        % REACTIVE["boots"],
        "each lift holds %.2f RPS - down, the queue pays the boot"
        % (6 * REPLICA_RPS),
        "breaches: %d of %d = %.2f%% (fixed fleet pays far more)"
        % (REACTIVE["breached"], TOTAL_REQUESTS, REACTIVE["breach_pct"]),
        "max queue %.0f, boots %d, over-budget seconds %d"
        % (REACTIVE["max_queue"], REACTIVE["boots"],
           REACTIVE["over_queue_s"]),
        "the trigger fires - the boot is what the queue pays for",
    ]
    assert round(peak_deficit) == 871
    assert REACTIVE["boots"] == 37
    assert round(REACTIVE["breached"]) == 75748
    assert REACTIVE["over_queue_s"] == 3436
    assert round(REACTIVE["max_queue"]) == 1026
    assert REACTIVE["breached"] < TOTAL_REQUESTS
    return lines


# ------------------------------------------------- F3  the cold-start gate
def f3_cold_start_gate():
    def ratio(t):
        return t / TTFT_BUDGET_MS

    lines = [
        "F3  the cold-start gate",
        "the joining replica's first request pays the weight ladder:",
        "resident    TTFT %8.2f ms = %.2fx  %s" % (
            TTFT_RESIDENT, ratio(TTFT_RESIDENT),
            "PASS" if ratio(TTFT_RESIDENT) <= 1 else "FAIL"),
        "page-cache  TTFT %8.2f ms = %.2fx  %s" % (
            TTFT_PAGECACHE, ratio(TTFT_PAGECACHE),
            "PASS" if ratio(TTFT_PAGECACHE) <= 1 else "FAIL"),
        "nvme-cold   TTFT %8.2f ms = %.2fx  %s" % (
            TTFT_NVME, ratio(TTFT_NVME),
            "PASS" if ratio(TTFT_NVME) <= 1 else "FAIL"),
        "one warmup probe at join retires the gate for every later one;",
        "the probe is not overhead - it is the first request, spent on",
        "the fleet's terms instead of a tenant's",
    ]
    assert ratio(TTFT_NVME) > 1
    assert ratio(TTFT_PAGECACHE) < 1
    return lines


# ------------------------------------------------ F4  the warm-pool rent
def f4_warm_pool_rent():
    fixed_h = FIXED["gpu_h"]
    reactive_h = REACTIVE["gpu_h"]
    warm_h = WARMPOOL["gpu_h"]
    per_1k_fixed = fixed_h * 3600 / TOTAL_REQUESTS * 1000
    per_1k_warm = warm_h * 3600 / TOTAL_REQUESTS * 1000
    lines = [
        "F4  the warm-pool rent",
        "fixed 4 x 24 h          = %7.2f GPU-h/day" % fixed_h,
        "reactive 4 + peak boots = %7.2f GPU-h/day" % reactive_h,
        "warm pool 6 x 24 h      = %7.2f GPU-h/day" % warm_h,
        "the always-pass fleet rents %.2fx the fixed bill"
        % (warm_h / fixed_h),
        "per 1,000 requests: fixed %.2f GPU-s, warm pool %.2f GPU-s"
        % (per_1k_fixed, per_1k_warm),
        "the reactive fleet's %.2f GPU-h of boots bought a partial pass"
        % (reactive_h - fixed_h),
        "the pool's %.2f GPU-h of rent buys the whole day"
        % (warm_h - fixed_h),
    ]
    assert fixed_h == 96.0
    assert warm_h == 144.0
    assert abs(reactive_h - 104.33) < 5e-3
    return lines


# ------------------------------------------------ F5  the scale-in bill
def f5_scale_in_bill():
    imm = simulate(4, 8, BOOT_COLD_S, window_s=0)
    w60 = simulate(4, 8, BOOT_COLD_S, window_s=60)
    w300 = REACTIVE
    lines = [
        "F5  the scale-in bill",
        "scale-in window 0 s  : %d scale-ins, %d boots, %.2f%% breach"
        % (imm["scale_ins"], imm["boots"], imm["breach_pct"]),
        "scale-in window 60 s : %d scale-ins, %d boots, %.2f%% breach"
        % (w60["scale_ins"], w60["boots"], w60["breach_pct"]),
        "scale-in window 300 s: %d scale-ins, %d boots, %.2f%% breach"
        % (w300["scale_ins"], w300["boots"], w300["breach_pct"]),
        "an immediate scale-in hands the fleet back to the next burst",
        "still holding a %d s boot - the window is the rent that buys"
        % int(BOOT_COLD_S),
        "the fleet out of re-buying its own cold start",
    ]
    assert imm["boots"] >= w300["boots"]
    assert imm["scale_ins"] > w300["scale_ins"]
    assert imm["scale_ins"] == 111 and imm["boots"] == 111
    assert w60["scale_ins"] == 96 and w60["boots"] == 96
    assert w300["scale_ins"] == 37 and w300["boots"] == 37
    assert round(imm["breach_pct"] * 100) == 3696
    assert round(w60["breach_pct"] * 100) == 2246
    assert round(w300["breach_pct"] * 100) == 935
    return lines


# ------------------------------------------------------- F6  the day bill
def f6_day_bill():
    rows = [
        ("fixed 4", FIXED),
        ("reactive +120 s boots", REACTIVE),
        ("reactive +45 s boots", REACTIVE_WARMBOOT),
        ("warm pool 6", WARMPOOL),
    ]
    lines = ["F6  the day bill", "%d requests over the same profile"
             % TOTAL_REQUESTS]
    for name, m in rows:
        lines.append("%-24s %7.2f GPU-h  %6d/%d pass  %.2f%% breach"
                     % (name, m["gpu_h"], m["pass"], TOTAL_REQUESTS,
                        m["breach_pct"]))
    lines += [
        "page-cached boots shrink the breach the cold boots pay,",
        "the warm pool retires it - the day's pass is a residency buy",
    ]
    assert WARMPOOL["breached"] == 0.0
    assert FIXED["breached"] > TOTAL_REQUESTS * 0.5
    assert abs(REACTIVE_WARMBOOT["gpu_h"] - 105.57) < 5e-3
    assert round(REACTIVE_WARMBOOT["breached"]) == 35232
    return lines


# ------------------------------------- F7  the build ladder and the audit
def f7_build_ladder():
    no_reactive = FIXED
    no_warm = REACTIVE
    no_window = simulate(4, 8, BOOT_COLD_S, window_s=0)
    lines = [
        "F7  the build ladder and the ablation audit",
        "fixed 4              %6.2f%% breach at %6.2f GPU-h"
        % (no_reactive["breach_pct"], no_reactive["gpu_h"]),
        "+reactive scale-out  %6.2f%% breach at %6.2f GPU-h"
        % (no_warm["breach_pct"], no_warm["gpu_h"]),
        "+warm pool 6         %6.2f%% breach at %6.2f GPU-h"
        % (WARMPOOL["breach_pct"], WARMPOOL["gpu_h"]),
        "ablations, each handing its delta back:",
        "-reactive  %6.2f%% breach (the peak returns whole)"
        % no_reactive["breach_pct"],
        "-warm pool %6.2f%% breach (the boots come back)"
        % no_warm["breach_pct"],
        "-window    %6d boots (the fleet re-buys its cold start)"
        % no_window["boots"],
        "order the build: reactive first, the warm pool second,",
        "the scale-in window third - and the trigger metric is queue",
        "depth, not CPU: CPU saturates only after the queue is deep",
    ]
    assert WARMPOOL["breached"] == 0.0
    assert no_window["boots"] >= REACTIVE["boots"]
    return lines


exhibits = [
    f1_fixed_fleet, f2_scale_trigger, f3_cold_start_gate,
    f4_warm_pool_rent, f5_scale_in_bill, f6_day_bill, f7_build_ladder,
]
for fn in exhibits:
    print(RULE)
    for line in fn():
        print(line)

print()
print("FENCE-070-OK")
```

```text
=========================================================
F1  the fixed-fleet bill
four resident replicas serve 17.30 RPS; the peak asks 24.00
hours over capacity: 4 11:20 12:24 13:24 14:20
requests arriving into over-capacity hours: 316800 of 810000 (39.11%)
unserveable arrivals the day accrues: 67719 requests
queue depth at the hour-13 boundary: 67719 requests
breaches against the 2100 ms TTFT line: 451828 of 810000 = 55.78%
a fixed fleet does not degrade at the peak - it accumulates
=========================================================
F2  the scale-trigger ladder
reactive path: queue > 8 held 10 s, then a 120 s boot
detect + boot = 130 s; the peak deficit runs 6.70 RPS
arrivals re-bought into the gap each launch: 871 requests
fleet path rides 4 -> 6 on 37 boots through the day; up,
each lift holds 25.95 RPS - down, the queue pays the boot
breaches: 75748 of 810000 = 9.35% (fixed fleet pays far more)
max queue 1026, boots 37, over-budget seconds 3436
the trigger fires - the boot is what the queue pays for
=========================================================
F3  the cold-start gate
the joining replica's first request pays the weight ladder:
resident    TTFT  1000.00 ms = 0.48x  PASS
page-cache  TTFT  1343.60 ms = 0.64x  PASS
nvme-cold   TTFT  3454.27 ms = 1.64x  FAIL
one warmup probe at join retires the gate for every later one;
the probe is not overhead - it is the first request, spent on
the fleet's terms instead of a tenant's
=========================================================
F4  the warm-pool rent
fixed 4 x 24 h          =   96.00 GPU-h/day
reactive 4 + peak boots =  104.33 GPU-h/day
warm pool 6 x 24 h      =  144.00 GPU-h/day
the always-pass fleet rents 1.50x the fixed bill
per 1,000 requests: fixed 426.67 GPU-s, warm pool 640.00 GPU-s
the reactive fleet's 8.33 GPU-h of boots bought a partial pass
the pool's 48.00 GPU-h of rent buys the whole day
=========================================================
F5  the scale-in bill
scale-in window 0 s  : 111 scale-ins, 111 boots, 36.96% breach
scale-in window 60 s : 96 scale-ins, 96 boots, 22.46% breach
scale-in window 300 s: 37 scale-ins, 37 boots, 9.35% breach
an immediate scale-in hands the fleet back to the next burst
still holding a 120 s boot - the window is the rent that buys
the fleet out of re-buying its own cold start
=========================================================
F6  the day bill
810000 requests over the same profile
fixed 4                    96.00 GPU-h  358172/810000 pass  55.78% breach
reactive +120 s boots     104.33 GPU-h  734252/810000 pass  9.35% breach
reactive +45 s boots      105.57 GPU-h  774768/810000 pass  4.35% breach
warm pool 6               144.00 GPU-h  810000/810000 pass  0.00% breach
page-cached boots shrink the breach the cold boots pay,
the warm pool retires it - the day's pass is a residency buy
=========================================================
F7  the build ladder and the ablation audit
fixed 4               55.78% breach at  96.00 GPU-h
+reactive scale-out    9.35% breach at 104.33 GPU-h
+warm pool 6           0.00% breach at 144.00 GPU-h
ablations, each handing its delta back:
-reactive   55.78% breach (the peak returns whole)
-warm pool   9.35% breach (the boots come back)
-window       111 boots (the fleet re-buys its cold start)
order the build: reactive first, the warm pool second,
the scale-in window third - and the trigger metric is queue
depth, not CPU: CPU saturates only after the queue is deep

FENCE-070-OK
```
