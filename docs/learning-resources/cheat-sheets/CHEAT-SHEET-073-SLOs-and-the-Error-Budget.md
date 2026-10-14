---
Document ID: CHEAT-SHEET-073
Title: "CHEAT-SHEET-073: SLOs and the Error Budget - the Promise in Requests, the Burn Rate, and the Deploy Gate"
Last Updated: 2026-10-14
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'serving', 'inference', 'llmops']
---
# CHEAT-SHEET-073: SLOs and the Error Budget - the Promise in Requests, the Burn Rate, and the Deploy Gate

The census that picked this sheet searched error budget, burn rate, SLO, SLA, SLI, p99, availability target, uptime, and breach handling across all 573 markdown docs and found the pattern taught everywhere except as an operator page - 306 hits across 59 files, 187 naming a breach, 26 the SLO, 26 the SLA, 20 the p99, ten an availability figure like 99.9, seven 99.99, six uptime, four the SLI - while the operator arithmetic returns zero in the whole catalog: no error-budget spend, no burn rate, no multi-window trip rule, no freeze line. Latency percentiles and SLA tables and uptime promises appear across the catalog, the serving sheets price the 2,100 ms TTFT line, the monitoring chapters alarm when it trips - each a part, none the operator page for what the next bad day spends, and the questions that start the moment one fleet signs a promise over the 1,090,800-request day of sheet 070 (what does one bad hour cost the ledger, when does the pager fire and when does it sleep, what stands between a risky deploy and an empty budget) had no home.

Every exhibit below is frozen stdout of the canonical fence at the bottom: the full 269-line stdlib fence ran twice and printed the same bytes, and each exhibit is its output sliced on the `====` rule - its 59-line run sits frozen below, byte-for-byte.

## The Promise in Requests

The promise is written in requests, not adjectives. The SLI counts the share of requests answered inside the 2,100 ms TTFT line this sheet family prices; the SLO is a number on that counter - 99.0% of the 1,090,800-request day, which is 10,908 requests allowed to answer badly. An allowance you can spend is a ledger with room, not a hope, and each extra nine divides it by ten: 99.9% buys 1,090.80, 99.99% buys 109.08.

```text
F1  the promise in requests
SLI: share of requests answering in <= 2100 ms TTFT
the 99.0% promise on the 1,090,800-request day allows
10,908.00 bad requests - a ledger with room, not a hope
each extra nine divides the allowance by ten:
99.9% -> 1,090.80    99.99% -> 109.08
```

## The Spend Ledger

Every day is priced against the same 10,908-request allowance. The ungated day of sheet 071 breaches 693,072 requests - 63.54 day-budgets spent, the allowance exhausted 22.66 minutes into the day. The admission gate breaches zero: its 187,975 refusals spend goodwill, not budget, because a refusal is a client a Retry-After can win back and a breach is a client you never see again.

```text
F2  the spend ledger
config            bad reqs   day-budgets spent
no gate            693,072   63.54x  (the 10,908 lasts 22.66 min)
admission gate           0   0.00x  (187,975 refusals, 0 breaches)
ladder gate              0   0.00x  (43,589 paid refusals, aimed)
rejections spend goodwill; breaches spend the budget
```

## The Burn Rate

The burn rate folds the ledger into one number that fits every window: bad over arrivals over the 1% allowed-bad share. The ungated day burns 63.54x; the gated day 0.00x. Duration is what prices an incident - a five-minute blip at the 48.00 RPS peak buys 9,149 bad requests, a thirty-minute stall buys 54,897, the same 63.54x burn carried for six times the time.

```text
F3  the burn rate
burn = (bad / arrivals) / 0.01 allowed-bad
ungated day  63.54x      gated day      0.00x
blip :  300 s ungated at the 48.00 RPS peak -> 9,149 bad
stall: 1,800 s ungated at the 48.00 RPS peak -> 54,897 bad
the same 63.54x burn - duration is what prices the ledger
```

## The Multi-Window Trip Rule

Page on two windows or page on noise. The rule fires when the 1-h burn reaches 14.4x AND the 6-h burn reaches 6.0x: one hour at 14.4x spends 2.14% of the 28-day budget, six hours at 6.0x spends 5.36%. The five-minute blip reads 5.29x fast, 1.35x slow - no page - yet spends 83.87% of a day's budget silently; the stall reads 31.77x and 8.11x and pages. The pager misses the blip; the ledger does not, which is why the ledger is the reviewer of record.

```text
F4  the multi-window trip rule
page when 1-h burn >= 14.4x AND 6-h burn >= 6.0x
1 h at 14.4x burns 2.14% of the 28-day budget (672 h)
6 h at 6.0x burns 5.36% of it
blip : fast 5.29x slow 1.35x -> no page (9,149 = 83.87% of the
       day's budget spent in five minutes, un-paged)
stall: fast 31.77x slow 8.11x -> PAGE
the pager misses the blip; the ledger does not
```

## The 28-Day Ledger

The budget is a calendar, not a dashboard: 28 days x 10,908 = 305,424 bad requests for the quarter. Twenty-six clean days spend nothing, day 9's blip spends 9,149, day 21's stall spends 54,897 - 64,046 spent, 20.97% of the quarter, 241,378 remaining at 79.03%, verdict SHIP. The ledger watches the quarter while the pager watches the hour - two clocks over one budget.

```text
F5  the 28-day ledger
quarter budget: 28 days x 10,908 = 305,424 bad allowed
26 clean days 0.00x    day 9 blip 9,149    day 21 stall 54,897
spent 64,046 = 20.97%    remaining 241,378 = 79.03% -> SHIP
the ledger watches the quarter; the pager watches the hour
```

## The Deploy Gate

The budget's sharpest job is standing in front of a deploy. The risky 60 s scale-in window of sheet 070 runs a 22.46% breach day: day 22 burns 244,994 bad requests, 22.46 day-budgets in one day. The 25%-remaining freeze line trips 22.44 hours into that first risky day, and without the gate the quarter's budget dies in 1.25 days. The budget is the only reviewer that reads the fleet's tail.

```text
F6  the deploy gate
the risky config (60 s scale-in, a 22.46% breach day)
rides week 4: day 22 burns 244,994 bad = 22.46 day-budgets
25%-remaining freeze trips 22.44 h into that first risky day
without the gate the quarter's budget dies in 1.25 days
the budget is the only reviewer that reads the fleet's tail
```

## The Build Ladder and the Ablation Audit

The gauge-only dashboard is green and blind - the day's mean TTFT of 1,890.00 ms sits under the 2,100 line while 693,072 requests breach. The ladder adds the SLI to count the bad, the budget to price them at 63.54 day-budgets, the burn windows to page the stall and spare the blip, and the gate to freeze deploys under 25% remaining. The ablations hand each delta back: drop the SLI and you are blind at the mean again, drop the budget and you hold a pager without a ledger, drop the burn and blips go free, drop the gate and the quarter dies in 1.25 days. Order the build: SLI, budget, burn, gate - and the rent of sheet 070 buys the 0.00% that keeps the ledger empty.

```text
F7  the build ladder and the ablation audit
gauge-only  mean 1890.00 ms under the 2100 line - green, blind
+SLI        count the bad: 693,072 breached requests
+budget     price them: 63.54 day-budgets gone by breakfast
+burn       windows: 1 page for the stall, 0 for the blip
+gate       deploys freeze at 25% remaining
ablations, each handing its delta back:
-SLI    blind at the mean again - 1890.00 ms, all green
-budget pages without accounting - a pager, not a ledger
-burn   catches the stall by alert lag alone - blips free
-gate   the quarter's budget dies in 1.25 days
order the build: SLI, budget, burn, gate - and the rent
of sheet 070 buys the 0.00% that keeps the ledger empty
```

## Known Failure Modes

| Known Failure Mode | Symptom | Repair |
| --- | --- | --- |
| The SLO as an adjective | "highly available" with no SLI counter - the ungated day breached 693,072 requests and no number moved (f1) | Write the promise in requests: the share under the 2,100 ms line, 99.0% = 10,908 bad allowed per day |
| Breaches priced as a bad day | the 63.54x spend reads as one adjective - the 10,908 allowance died 22.66 minutes in, uncounted (f2) | Divide bad requests by the allowance - day-budgets spent is the only unit that compares days |
| One burn number for every window | the 63.54x burn is read as one page while the 300 s blip and the 1,800 s stall owe 9,149 vs 54,897 (f3) | Normalize bad / arrivals / allowed-bad per window, then price duration separately |
| The pager trusted as the ledger | the blip fails both windows - 5.29x fast, 1.35x slow - and 83.87% of a day's budget vanishes un-paged (f4) | Keep the AND rule for paging and the ledger for accounting - the pager watches the hour only |
| The hour read as the quarter | 20.97% spent looks clean on a green dashboard while 64,046 of 305,424 are already gone (f5) | Keep a 28-day ledger with spent, remaining, and a verdict - SHIP / SLOW DEPLOYS / FREEZE |
| Deploys shipped against an empty budget | the 22.46% breach-day config rides week 4 and the quarter's budget dies in 1.25 days (f6) | Gate deploys on remaining budget - freeze risky changes under 25% remaining |

## Troubleshooting

| Symptom | Checks | Fix |
| --- | --- | --- |
| Dashboard green, users leaking | The SLI is the mean, not the share - mean 1,890.00 ms sits under the 2,100 line while 693,072 breach (f1) | Count the share under the line per window; alert on burn, never on the mean |
| Budget numbers nobody trusts | The allowance is not derived from the day - 1% of 1,090,800 is 10,908, recompute per window (f2) | Price every incident in day-budgets: bad / allowance, one unit across all windows |
| One burn rate, wildly different bills | Burn without duration - 9,149 for a 300 s blip vs 54,897 for a 1,800 s stall at the same 63.54x (f3) | Report burn per window and price incidents in seconds of ungated peak |
| Pager silent through a blip | One-window alerting - 5.29x fast and 1.35x slow fails the AND rule (f4) | Accept the silence for paging but read the ledger: the blip spent 83.87% of a day |
| Quarter half gone with no incident | The ledger was never kept - 64,046 of 305,424 spent across days 9 and 21 (f5) | Rebuild the ledger from breach counters, then set the verdict policy |
| Budget dies mid-quarter | A 22.46% breach-day config shipped without a gate - 1.25 days to zero (f6) | Freeze at 25% remaining and roll the risky config back before day 23 |

## Quick Reference For

- [the monitoring chapter whose latency alarms this budget accounts for](../../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
- [the LLM observability chapter whose SLI counters this budget spends](../../phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md)
- [the gateway sheet whose retry and tier bills this budget prices in goodwill](../../learning-resources/cheat-sheets/CHEAT-SHEET-056-LLM-Gateway-and-Model-Routing.md)
- [the warm-pool fleet whose risky scale-in window this deploy gate freezes](../../learning-resources/cheat-sheets/CHEAT-SHEET-070-Autoscaling-and-the-Warm-Pool-Budget.md)
- [the load-shedding gate whose refusals this ledger keeps out of the budget](../../learning-resources/cheat-sheets/CHEAT-SHEET-071-Load-Shedding-and-the-Admission-Gate.md)

## The Canonical Fence

The canonical fence is the sheet's operating script - the 269-line stdlib program above froze every exhibit, and running it twice prints the same bytes. Copy it, keep the fixture constants, swap the day, the TTFT line, the SLO, the burn thresholds, and the risky rate for your own fleet's, and the ledger re-derives.

```python
"""CHEAT-SHEET-073 canonical fence: SLOs and the error budget.
Stdlib only, no randomness, no clocks - every printed figure is computed
from the fixed fixture and pinned by an assert. Two runs must print
identical bytes. Budget arithmetic over the 070/071 fleet universe;
no RNG anywhere.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 57

# ---------------------------------------------------------------- fixture
# the 070/071 fleet universe: six warm-pool replicas, the 144 GPU-h rent
DAY_REQUESTS = 1090800
LINE_MS = 2100.0            # the TTFT line every fleet sheet prices
SLO = 0.99                  # 99.0% of requests under the line
FLEET = 6
RENT_GPUH = 144.0

# the 071 configs on the same day: breaches and refusals
NOGATE_BAD = 693072         # the ungated day's breaches
GATE_REJECT = 187975        # the admission gate's refusals, 0 breaches
LADDER_PAID = 43589         # the ladder's paid refusals, 0 breaches
RETRY_REJECT = 211715       # ladder + naive retry rejections, 0 breaches

# the day's 24 hourly rates (RPS); launch bell peaking at 48.00 in h15
RATES = [1, 1, 1, 1, 1, 2, 3, 5, 9, 13, 15, 21, 30, 39, 42, 48,
         27, 20, 12, 6, 3, 1, 1, 1]
HOUR_S = 3600
PEAK = 15

# the multi-window rule and the ledger calendar
FAST_BURN = 14.4            # 1-h page threshold
SLOW_BURN = 6.0             # 6-h page threshold
QUARTER_DAYS = 28
FREEZE_AT = 0.25            # freeze risky deploys under 25% remaining

# the risky config: the 60 s scale-in window runs a 22.46% breach day
RISKY_RATE = 0.2246

# the gauge-only dashboard: the day's mean TTFT, under the line
MEAN_TTFT_MS = 1890.0

ALLOW_DAY = round((1.0 - SLO) * DAY_REQUESTS, 2)
BURN_OK = round(1.0 - SLO, 2)                    # allowed bad share
UNGATE_SHARE = NOGATE_BAD / float(DAY_REQUESTS)  # ungated bad share
ARR = [r * HOUR_S for r in RATES]                # arrivals per hour

assert ALLOW_DAY == 10908.0
assert BURN_OK == 0.01
assert RATES[PEAK] == 48
assert sum(RATES) * HOUR_S == DAY_REQUESTS
assert ARR[PEAK] == 172800


def incident_bad(seconds):
    """Breaches during an ungated window at the peak hour."""
    arrivals = RATES[PEAK] * float(seconds)
    return int(round(arrivals * UNGATE_SHARE))


# ------------------------------------------------- F1  the promise
def f1_promise():
    a999 = round((1.0 - 0.999) * DAY_REQUESTS, 2)
    a9999 = round((1.0 - 0.9999) * DAY_REQUESTS, 2)
    lines = [
        "F1  the promise in requests",
        "SLI: share of requests answering in <= %.0f ms TTFT" % LINE_MS,
        "the 99.0%% promise on the %s-request day allows"
        % "{:,}".format(DAY_REQUESTS),
        "%s bad requests - a ledger with room, not a hope"
        % "{:,.2f}".format(ALLOW_DAY),
        "each extra nine divides the allowance by ten:",
        "99.9%% -> %s    99.99%% -> %s"
        % ("{:,.2f}".format(a999), "{:,.2f}".format(a9999)),
    ]
    assert a999 == 1090.8
    assert a9999 == 109.08
    return lines


# ------------------------------------------------- F2  the spend ledger
def f2_spend_ledger():
    mult = NOGATE_BAD / ALLOW_DAY
    exhaust_min = 24.0 * 60.0 / mult
    lines = [
        "F2  the spend ledger",
        "config            bad reqs   day-budgets spent",
        "no gate           %8s   %.2fx  (the 10,908 lasts %.2f min)"
        % ("{:,}".format(NOGATE_BAD), mult, exhaust_min),
        "admission gate           0   0.00x  (%s refusals, 0 breaches)"
        % "{:,}".format(GATE_REJECT),
        "ladder gate              0   0.00x  (%s paid refusals, aimed)"
        % "{:,}".format(LADDER_PAID),
        "rejections spend goodwill; breaches spend the budget",
    ]
    assert abs(mult - 63.54) < 5e-3
    assert abs(exhaust_min - 22.66) < 5e-3
    assert DAY_REQUESTS - GATE_REJECT == 902825
    return lines


# ------------------------------------------------- F3  the burn rate
def f3_burn_rate():
    day_burn = UNGATE_SHARE / BURN_OK
    blip_bad = incident_bad(300)
    stall_bad = incident_bad(1800)
    lines = [
        "F3  the burn rate",
        "burn = (bad / arrivals) / %.2f allowed-bad" % BURN_OK,
        "ungated day %6.2fx      gated day      0.00x" % day_burn,
        "blip :  300 s ungated at the 48.00 RPS peak -> %s bad"
        % "{:,}".format(blip_bad),
        "stall: 1,800 s ungated at the 48.00 RPS peak -> %s bad"
        % "{:,}".format(stall_bad),
        "the same 63.54x burn - duration is what prices the ledger",
    ]
    assert abs(day_burn - 63.54) < 5e-3
    assert blip_bad == 9149
    assert stall_bad == 54897
    return lines


# ------------------------------------------------- F4  the trip rule
def f4_trip_rule():
    blip_bad = incident_bad(300)
    stall_bad = incident_bad(1800)
    win1 = ARR[PEAK]
    win6 = sum(ARR[13:19])
    b1_blip = blip_bad / float(win1) / BURN_OK
    b6_blip = blip_bad / float(win6) / BURN_OK
    b1_stall = stall_bad / float(win1) / BURN_OK
    b6_stall = stall_bad / float(win6) / BURN_OK
    fast_frac = FAST_BURN / (24.0 * QUARTER_DAYS) * 100.0
    slow_frac = SLOW_BURN * 6.0 / (24.0 * QUARTER_DAYS) * 100.0
    page_blip = b1_blip >= FAST_BURN and b6_blip >= SLOW_BURN
    page_stall = b1_stall >= FAST_BURN and b6_stall >= SLOW_BURN
    day_spend = blip_bad / ALLOW_DAY * 100.0
    lines = [
        "F4  the multi-window trip rule",
        "page when 1-h burn >= %.1fx AND 6-h burn >= %.1fx"
        % (FAST_BURN, SLOW_BURN),
        "1 h at %.1fx burns %.2f%% of the %d-day budget (%d h)"
        % (FAST_BURN, fast_frac, QUARTER_DAYS, 24 * QUARTER_DAYS),
        "6 h at %.1fx burns %.2f%% of it" % (SLOW_BURN, slow_frac),
        "blip : fast %.2fx slow %.2fx -> %s (%s = %.2f%% of the"
        % (b1_blip, b6_blip, "PAGE" if page_blip else "no page",
           "{:,}".format(blip_bad), day_spend),
        "       day's budget spent in five minutes, un-paged)",
        "stall: fast %.2fx slow %.2fx -> %s"
        % (b1_stall, b6_stall, "PAGE" if page_stall else "no page"),
        "the pager misses the blip; the ledger does not",
    ]
    assert win1 == 172800
    assert win6 == 676800
    assert abs(fast_frac - 2.14) < 5e-3
    assert abs(slow_frac - 5.36) < 5e-3
    assert abs(b1_blip - 5.29) < 5e-3
    assert abs(b6_blip - 1.35) < 5e-3
    assert abs(b1_stall - 31.77) < 5e-3
    assert abs(b6_stall - 8.11) < 5e-3
    assert not page_blip and page_stall
    assert abs(day_spend - 83.87) < 5e-3
    return lines


# ------------------------------------------------- F5  the 28-day ledger
def f5_quarter_ledger():
    quarter = ALLOW_DAY * QUARTER_DAYS
    blip_bad = incident_bad(300)
    stall_bad = incident_bad(1800)
    spend = {9: blip_bad, 21: stall_bad}
    total = sum(spend.values())
    remain = quarter - total
    if remain >= 0.5 * quarter:
        verdict = "SHIP"
    elif remain >= FREEZE_AT * quarter:
        verdict = "SLOW DEPLOYS"
    else:
        verdict = "FREEZE"
    lines = [
        "F5  the 28-day ledger",
        "quarter budget: %d days x %s = %s bad allowed"
        % (QUARTER_DAYS, "{:,.0f}".format(ALLOW_DAY),
           "{:,.0f}".format(quarter)),
        "%d clean days 0.00x    day 9 blip %s    day 21 stall %s"
        % (QUARTER_DAYS - len(spend), "{:,}".format(blip_bad),
           "{:,}".format(stall_bad)),
        "spent %s = %.2f%%    remaining %s = %.2f%% -> %s"
        % ("{:,}".format(total), total / quarter * 100.0,
           "{:,.0f}".format(remain), remain / quarter * 100.0, verdict),
        "the ledger watches the quarter; the pager watches the hour",
    ]
    assert quarter == 305424.0
    assert total == 64046
    assert abs(total / quarter * 100.0 - 20.97) < 5e-3
    assert remain == 241378
    assert abs(remain / quarter * 100.0 - 79.03) < 5e-3
    assert verdict == "SHIP"
    return lines


# ------------------------------------------------- F6  the deploy gate
def f6_deploy_gate():
    quarter = ALLOW_DAY * QUARTER_DAYS
    risky_bad = int(round(DAY_REQUESTS * RISKY_RATE))
    risky_mult = risky_bad / ALLOW_DAY
    freeze_at_spend = (1.0 - FREEZE_AT) * quarter
    frac_into_day = freeze_at_spend / float(risky_bad)
    hours_into = frac_into_day * 24.0
    die_days = quarter / float(risky_bad)
    lines = [
        "F6  the deploy gate",
        "the risky config (60 s scale-in, a %.2f%% breach day)"
        % (RISKY_RATE * 100.0),
        "rides week 4: day 22 burns %s bad = %.2f day-budgets"
        % ("{:,}".format(risky_bad), risky_mult),
        "25%%-remaining freeze trips %.2f h into that first risky day"
        % hours_into,
        "without the gate the quarter's budget dies in %.2f days"
        % die_days,
        "the budget is the only reviewer that reads the fleet's tail",
    ]
    assert risky_bad == 244994
    assert abs(risky_mult - 22.46) < 5e-3
    assert abs(hours_into - 22.44) < 5e-3
    assert abs(die_days - 1.25) < 5e-3
    return lines


# ------------------------------------------------- F7  the build ladder
def f7_build_ladder():
    lines = [
        "F7  the build ladder and the ablation audit",
        "gauge-only  mean %.2f ms under the %.0f line - green, blind"
        % (MEAN_TTFT_MS, LINE_MS),
        "+SLI        count the bad: %s breached requests"
        % "{:,}".format(NOGATE_BAD),
        "+budget     price them: %.2f day-budgets gone by breakfast"
        % (NOGATE_BAD / ALLOW_DAY),
        "+burn       windows: 1 page for the stall, 0 for the blip",
        "+gate       deploys freeze at %d%% remaining"
        % (FREEZE_AT * 100.0),
        "ablations, each handing its delta back:",
        "-SLI    blind at the mean again - %.2f ms, all green"
        % MEAN_TTFT_MS,
        "-budget pages without accounting - a pager, not a ledger",
        "-burn   catches the stall by alert lag alone - blips free",
        "-gate   the quarter's budget dies in 1.25 days",
        "order the build: SLI, budget, burn, gate - and the rent",
        "of sheet 070 buys the 0.00% that keeps the ledger empty",
    ]
    assert MEAN_TTFT_MS < LINE_MS
    assert abs(NOGATE_BAD / ALLOW_DAY - 63.54) < 5e-3
    return lines


exhibits = [
    f1_promise, f2_spend_ledger, f3_burn_rate, f4_trip_rule,
    f5_quarter_ledger, f6_deploy_gate, f7_build_ladder,
]
for fn in exhibits:
    print(RULE)
    for line in fn():
        print(line)

print()
print("FENCE-073-OK")
```

```text
=========================================================
F1  the promise in requests
SLI: share of requests answering in <= 2100 ms TTFT
the 99.0% promise on the 1,090,800-request day allows
10,908.00 bad requests - a ledger with room, not a hope
each extra nine divides the allowance by ten:
99.9% -> 1,090.80    99.99% -> 109.08
=========================================================
F2  the spend ledger
config            bad reqs   day-budgets spent
no gate            693,072   63.54x  (the 10,908 lasts 22.66 min)
admission gate           0   0.00x  (187,975 refusals, 0 breaches)
ladder gate              0   0.00x  (43,589 paid refusals, aimed)
rejections spend goodwill; breaches spend the budget
=========================================================
F3  the burn rate
burn = (bad / arrivals) / 0.01 allowed-bad
ungated day  63.54x      gated day      0.00x
blip :  300 s ungated at the 48.00 RPS peak -> 9,149 bad
stall: 1,800 s ungated at the 48.00 RPS peak -> 54,897 bad
the same 63.54x burn - duration is what prices the ledger
=========================================================
F4  the multi-window trip rule
page when 1-h burn >= 14.4x AND 6-h burn >= 6.0x
1 h at 14.4x burns 2.14% of the 28-day budget (672 h)
6 h at 6.0x burns 5.36% of it
blip : fast 5.29x slow 1.35x -> no page (9,149 = 83.87% of the
       day's budget spent in five minutes, un-paged)
stall: fast 31.77x slow 8.11x -> PAGE
the pager misses the blip; the ledger does not
=========================================================
F5  the 28-day ledger
quarter budget: 28 days x 10,908 = 305,424 bad allowed
26 clean days 0.00x    day 9 blip 9,149    day 21 stall 54,897
spent 64,046 = 20.97%    remaining 241,378 = 79.03% -> SHIP
the ledger watches the quarter; the pager watches the hour
=========================================================
F6  the deploy gate
the risky config (60 s scale-in, a 22.46% breach day)
rides week 4: day 22 burns 244,994 bad = 22.46 day-budgets
25%-remaining freeze trips 22.44 h into that first risky day
without the gate the quarter's budget dies in 1.25 days
the budget is the only reviewer that reads the fleet's tail
=========================================================
F7  the build ladder and the ablation audit
gauge-only  mean 1890.00 ms under the 2100 line - green, blind
+SLI        count the bad: 693,072 breached requests
+budget     price them: 63.54 day-budgets gone by breakfast
+burn       windows: 1 page for the stall, 0 for the blip
+gate       deploys freeze at 25% remaining
ablations, each handing its delta back:
-SLI    blind at the mean again - 1890.00 ms, all green
-budget pages without accounting - a pager, not a ledger
-burn   catches the stall by alert lag alone - blips free
-gate   the quarter's budget dies in 1.25 days
order the build: SLI, budget, burn, gate - and the rent
of sheet 070 buys the 0.00% that keeps the ledger empty

FENCE-073-OK
```
