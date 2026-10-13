---
Document ID: CHEAT-SHEET-056
Title: "CHEAT-SHEET-056: LLM Gateway and Model Routing - the Fallback Cascade, the Price Ladder, and the Affinity Ledger"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'llmops', 'serving', 'inference', 'deployment']
---

# CHEAT-SHEET-056: LLM Gateway and Model Routing - the Fallback Cascade, the Price Ladder, and the Affinity Ledger

The scope scan that picked this page: phase1-infra's 1400-llmops track teaches the engines - 1401 Ollama Enterprise Deployment, 1402 vLLM and TGI High-Concurrency Inference, 1405 SGLang RadixAttention Serving, plus the 1403 and 1404 deployment guides - and the sheets already cover the engines (007 vLLM, 009 local inference, 034 SGLang), but the layer above them has no home anywhere: a repo-wide scan finds ten files that mention gateways or model routing and every hit is a side touch - a compose service name, a mermaid node, an architecture-diagram box, two sheets' stray paragraphs. This sheet takes the questions the operator actually asks at 2am: which model answers this request, what does the fallback cost when the primary misses, why is the same prefix billed full price, and what happens to the bill when the region wobbles.

The sheet runs as seven priced exhibits: the fallback cascade (F1 - the product law assumes independence, a shared region does not care), the price ladder (F2 - the router undercuts even the flat standard bill), the router verdict (F3 - the threshold is a dial, not a default), the affinity ledger (F4 - round robin pays full price for three quarters of the repeats), the 429 ledger (F5 - the spill lane has a price), the SLO downgrade ladder (F6 - order the rungs before the breach), and the shadow verdict (F7 - the gate reads agreement, not the invoice). Every number below is printed by the canonical fence at the bottom of the page: the full 310-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 86-line output sits frozen below it byte-for-byte.

## The Fallback Cascade - the Product Law Assumes Independence

A cascade is sold as multiplication: a 2% primary miss times a 5% fallback miss times a 10% emergency lane is 0.0001, a 99.99% availability promise. The fence runs 10,000 requests through a correlated cascade instead - the fallback lives in the primary's region, so when the region incident closes the primary on 200 requests, it closes the fallback on 50 of them and bleeds the emergency lane on 10. Observed availability: 99.90%, ten times worse than the promise, plus 250 extra upstream calls per 10,000 as the 2.5% retry surcharge. The fix is topological, not probabilistic: put the last hop in a failure domain the first two cannot share.

```text
independent       0.02 x 0.05 x 0.10 = 0.0001 -> 99.99% promised
correlated run    200 -> 50 -> 10 hard fails = 99.90% observed
retry bill        +250 upstream calls per 10,000 = 2.5% surcharge
```

## The Price Ladder - the Router Is the Discount

Three tiers price the same 12,000-request month - 14.4M input and 4.8M output tokens - three different ways. Send everything to the frontier tier and the bill is $576.000; flatten it onto the standard tier and it is $84.000; route by class (70% economy, 20% standard, 10% frontier) and it is $77.928. The router does not just beat the frontier bill by 86.5% - it undercuts the flat mid-tier bill outright, because the mid tier was carrying 70% of traffic that never needed it. The ladder only pays when the route table matches what each class actually requires; the shadow gate in F7 is what keeps the table honest.

```text
all-frontier  $576.000   capability 70% of traffic never asked for
all-standard  $84.000    the flat mid-tier bill
routed        $77.928    undercuts the flat bill - the mix carries it
```

## The Router Verdict - the Threshold Is a Dial

Ten prompts carry ground-truth tiers and a cheap classifier's score, and the fence sweeps the route threshold from 0.0 to 1.0. Every threshold below 0.7 routes all ten prompts to the frontier tier and overpays on six economy classes; at 0.7 exactly four prompts ride the frontier tier and nothing is misrouted or overpaid - the knee. One notch up, at 0.8, multi-hop research and code review land on the cheap tier and quality breaks; the failures only grow from there. The threshold is a measured dial per workload, not a constant inherited from the last deployment.

```text
t=0.0..0.6  overpaid 6..1, misrouted 0   money leaks, quality holds
t=0.7       misrouted 0, overpaid 0      the knee - route all right
t=0.8       misrouted 2 and growing      quality breaks, money saved
```

## The Affinity Ledger - Round Robin Bills Full Price

Six sessions of five turns each hit four replicas, every request carrying a 2,048-token prefix that a cache could serve at 10% of input price. Round robin spreads the turns evenly and perfectly blindly: a session's prefix returns to the replica that holds it exactly one turn in four, so 6 of 24 potential hits land - 25% - and the ledger bills 65,740.8 token-equivalents. Session affinity (one hash of the session id) keeps every turn of a session on its replica: 24 of 24 hits, 32,563.2 billed, 50.5% off the input bill. The cache was already deployed; round robin just kept it switched off.

```text
round robin  6/24 hits = 25.0%  -> 65,740.8 tok-equiv billed
affinity     24/24 hits = 100%  -> 32,563.2 tok-equiv billed
savings      50.5% of the input bill, one session-hash away
```

## The 429 Ledger - the Spill Lane Has a Price

A provider that holds a 60-per-minute budget meets an 80-request burst, and the gateway has two honest choices. Spill the excess twenty to the open provider at three times the price: the minute bills $0.050400 against the $0.033600 an unsized burst would have paid - a 50% premium that is the true cost of capacity planning skipped. Retry into the closed bucket first and the bill is identical, but the log carries 40 dead 429'd calls and their latency; honoring Retry-After and spilling once is the whole discipline. The spill lane is routing config, priced and pre-wired before the burst, never improvised during it.

## The SLO Downgrade Ladder - Order the Rungs Before the Breach

The end-to-end budget is a 2.0 s p95, and the frontier tier's samples sit at 2.60 s - a breach. The ladder's pre-agreed rung moves the two borderline frontier classes (multi-hop research, code review) onto the standard tier, whose p95 is 1.40 s: the budget line holds, the bill drops from $77.928 to $58.248 (-25.3%), and the frontier band's measured quality blends from 92.0 to 86.4 because three classes keep the big model. That is the shape of an honest degrade - a measured quality point traded against a written budget line - and it only works if the rung order was written before the breach, not argued during it.

```text
frontier p95 2.60 s -> BREACH of the 2.0 s budget
rung         borderline classes -> standard (p95 1.40 s)
bill         $77.928 -> $58.248 (-25.3%)
quality      92.0 -> 86.4 blended on the frontier band
```

## The Shadow Verdict - the Gate Reads Agreement, Not the Invoice

A candidate model promises -40% on the frontier bill: $57.600 becomes $34.560, a $23.040 monthly win on F2's numbers alone. The shadow gate mirrors 40 paired judgments against the incumbent and counts agreement: extraction 20/20, reasoning 10/12, safety-refusal 7/8 - 92.5% overall, with the safety category short of the 8/8 it requires. The gate reads two lines - agreement at or above 95%, safety perfect - and both fail, so the promotion is refused despite the invoice. A flipped refusal is a policy regression, and no discount prices that.

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Chaining two providers in one region | F1: the product law promises 99.99%, the correlated run lands 99.90% - split the cascade across failure domains |
| Routing every request to the frontier tier | F2: $576.000 against a routed $77.928 - 86.5% of the bill is routing, not usage |
| Copying a router threshold between workloads | F3: t=0.8 misroutes multi-hop research; the knee is measured, not inherited |
| Load-balancing chat turns round robin | F4: 25% cache hits against affinity's 100% - the prefix re-bills full price |
| Retrying into a 429'd bucket | F5: 40 dead calls for the same bill - honor Retry-After and spill once |
| Promoting the cheaper model on cost alone | F7: 92.5% agreement with safety at 7/8 - the gate says no |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| availability slo misses despite three providers | the cascade shares a region; move the last hop to an independent failure domain |
| the monthly bill jumps with no traffic growth | a routing tier shifted; re-price the mix against the f2 ladder |
| repeat sessions feel slow on long prompts | affinity is off; hash the session id onto a replica (f4) |
| provider 429s eat a burst | size the burst against the budget and pre-wire the spill lane (f5) |
| p95 breaches the latency budget at peak | pull the slo ladder rung: borderline classes to the faster tier (f6) |
| the candidate model looks free and wins in review | run the shadow gate: 95% agreement and 8/8 safety, or no promotion (f7) |

## Quick Reference For

- [1401: Ollama Enterprise Deployment](../../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md) - the local engine this cascade's last resort runs on, and the enterprise hardening around it.
- [1402: vLLM and TGI High-Concurrency Inference](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - the primary lanes the price ladder routes between, at the concurrency the 429 ledger sizes against.
- [1405: SGLang RadixAttention Serving](../../phases/phase1-infra/1400-llmops/1405-SGLang.md) - the radix cache behind the affinity ledger's prefix economics.
- [1403: vLLM Production Deployment Guide](../../phases/phase1-infra/1400-llmops/guides/1403-vLLM-Production-Deployment.md) - the production knobs the SLO ladder measures.
- [1404: Text Generation Inference (TGI) Deployment Guide](../../phases/phase1-infra/1400-llmops/guides/1404-TGI-Deployment-Guide.md) - the second engine family the spill lane falls back to.

## The Canonical Fence

This sheet's every number - the failure counts, the dollar bills, the cache hit rates, the p95 samples - comes from the fence below, printed by a real run and pinned with asserts: the full 310-line stdlib program reproduces F1 through F7, and its 86-line output sits frozen under it byte-for-byte.

```python
"""tick-1042 canonical fence - CHEAT-SHEET-056: LLM Gateway and Model
Routing. Prints the fallback cascade, the price ladder, the router
verdict, the affinity ledger, the 429 spill ledger, the SLO downgrade
ladder and the shadow verdict from real arithmetic against the
1400-llmops track. Stdlib only, deterministic, no RNG, no timing,
no I/O beyond stdout.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

LINE = "-" * 60


def rule(label):
    print("")
    print(label)
    print(LINE)


# ---------------------------------------------------------------- F1
rule("F1 - the fallback cascade")
chain = [
    ("primary", 0.02, "the main provider, eu region"),
    ("fallback", 0.05, "second provider, SAME region"),
    ("last resort", 0.10, "self-hosted emergency lane"),
]
p_indep = 1.0
for name, p, note in chain:
    p_indep *= p
assert abs(p_indep - 0.0001) < 1e-12, p_indep
print("chain            " + " -> ".join(f"{n} ({int(p*100)}% miss)" for n, p, _ in chain))
print(f"independence law {chain[0][1]} x {chain[1][1]} x {chain[2][1]} = "
      f"{p_indep:.4f} -> 99.99% availability promised")
N = 10000
primary_miss = fallback_miss = hard_fail = 0
for i in range(1, N + 1):
    if i % 50 == 0:                 # primary's region incident window
        primary_miss += 1
        if i % 200 == 0:            # the fallback shares the region
            fallback_miss += 1
            if i % 1000 == 0:       # the emergency lane bleeds too
                hard_fail += 1
assert primary_miss == 200, primary_miss
assert fallback_miss == 50, fallback_miss
assert hard_fail == 10, hard_fail
avail = (N - hard_fail) / N * 100
assert abs(avail - 99.90) < 1e-9
ratio = (hard_fail / N) / p_indep
assert abs(ratio - 10.0) < 1e-9
extra_calls = primary_miss + fallback_miss
assert extra_calls == 250
print(f"correlated run   {N:,} requests, fallback in the same region:")
print(f"  primary missed   {primary_miss} requests")
print(f"  fallback missed   {fallback_miss} of those (one incident, two tiers)")
print(f"  hard failed       {hard_fail} requests -> observed {avail:.2f}% "
      f"({ratio:.0f}x the independence promise)")
print(f"  extra upstream calls {extra_calls} per {N:,} = a 2.5% call surcharge")
print("-> the product law assumes independence; a shared region does not care")

# ---------------------------------------------------------------- F2
rule("F2 - the price ladder")
TIERS = {
    "economy":  (0.15, 0.60),
    "standard": (2.50, 10.00),
    "frontier": (15.00, 75.00),
}
REQS, TOK_IN, TOK_OUT = 12000, 1200, 400
MIX = {"economy": 8400, "standard": 2400, "frontier": 1200}
assert sum(MIX.values()) == REQS
assert MIX["economy"] == int(REQS * 0.70)
assert MIX["standard"] == int(REQS * 0.20)
assert MIX["frontier"] == int(REQS * 0.10)
min_, mout = REQS * TOK_IN / 1e6, REQS * TOK_OUT / 1e6
assert abs(min_ - 14.4) < 1e-9 and abs(mout - 4.8) < 1e-9
print("tier        in $/1M   out $/1M")
for name, (pin, pout) in TIERS.items():
    print(f"{name:<10}  {pin:<8.2f}  {pout:.2f}")
print(f"workload    {REQS:,} requests x ({TOK_IN:,} in / {TOK_OUT:,} out) "
      f"= {min_}M in, {mout}M out")
print("route mix   economy 70% (8,400) | standard 20% (2,400) | "
      "frontier 10% (1,200)")


def bill(assign):
    total = 0.0
    for name, n in assign.items():
        pin, pout = TIERS[name]
        total += n * TOK_IN / 1e6 * pin + n * TOK_OUT / 1e6 * pout
    return total


all_frontier = bill({k: MIX[k] if k == "frontier" else 0 for k in MIX}
                    | {"frontier": REQS})
all_standard = bill({k: MIX[k] if k == "standard" else 0 for k in MIX}
                    | {"standard": REQS})
routed = bill(MIX)
assert abs(all_frontier - 576.0) < 1e-6, all_frontier
assert abs(all_standard - 84.0) < 1e-6, all_standard
assert abs(routed - 77.928) < 1e-6, routed
save = (1 - routed / all_frontier) * 100
assert abs(save - 86.4708) < 0.001, save
print(f"bill all-frontier   ${all_frontier:.3f}")
print(f"bill all-standard   ${all_standard:.3f}")
print(f"bill routed         ${routed:.3f}")
print(f"savings vs frontier {save:.1f}% (assert-pinned 86.4708%)")
assert routed < all_standard
print("-> the router undercuts even the flat standard bill: "
      "70% of traffic never needed it")

# ---------------------------------------------------------------- F3
rule("F3 - the router verdict")
PROMPTS = [
    ("faq answer",           "economy", 0.15),
    ("invoice total",        "economy", 0.25),
    ("email summary",        "economy", 0.35),
    ("product blurb",        "economy", 0.45),
    ("sql from question",    "economy", 0.55),
    ("contract clause diff", "economy", 0.65),
    ("multi-hop research",   "frontier", 0.70),
    ("code review",          "frontier", 0.78),
    ("proof sketch",         "frontier", 0.86),
    ("novel proof",          "frontier", 0.94),
]
assert len(PROMPTS) == 10
truth_front = sum(1 for _, t, _ in PROMPTS if t == "frontier")
assert truth_front == 4
print("10 prompts, ground-truth tier vs a cheap classifier score; sweep t:")
print("t      frontier  misrouted  overpaid")
knee_seen = False
prev_mis = -1
for k in range(11):
    t = k / 10
    to_front = [p for p, _, s in PROMPTS if s >= t]
    mis = sum(1 for p, tr, s in PROMPTS if s < t and tr == "frontier")
    over = sum(1 for p, tr, s in PROMPTS if s >= t and tr == "economy")
    assert mis >= prev_mis          # failures never shrink as t rises
    prev_mis = mis
    mark = ""
    if t == 0.7:
        assert mis == 0 and over == 0 and len(to_front) == 4, (mis, over)
        mark = "  <- the knee"
        knee_seen = True
    if t == 0.8:
        assert mis == 2, mis
        assert len(to_front) == 2, len(to_front)
        mark = "  (multi-hop and code review land on the cheap tier)"
    print(f"t={t:.1f}  {len(to_front):>7}  {mis:>9}  {over:>8}{mark}")
assert knee_seen
print("-> the threshold is a dial, not a default: 0.7 routes every prompt right")

# ---------------------------------------------------------------- F4
rule("F4 - the affinity ledger")
REPLICAS, SESSIONS, TURNS = 4, 6, 5
PREFIX, SUFFIX = 2048, 512
CACHE_RATE = 0.10
reqs = SESSIONS * TURNS
assert reqs == 30
full_tok = PREFIX + SUFFIX
hit_tok = PREFIX * CACHE_RATE + SUFFIX
assert full_tok == 2560 and abs(hit_tok - 716.8) < 1e-9

seen = [set() for _ in range(REPLICAS)]
rr_hits = 0
for s in range(SESSIONS):
    for t in range(TURNS):
        g = s * TURNS + t
        r = g % REPLICAS            # round robin
        if s in seen[r]:
            rr_hits += 1
        seen[r].add(s)
assert rr_hits == 6, rr_hits

sticky = {s: s % REPLICAS for s in range(SESSIONS)}
seen2 = [set() for _ in range(REPLICAS)]
af_hits = 0
for s in range(SESSIONS):
    for t in range(TURNS):
        r = sticky[s]               # session affinity
        if t > 0:
            assert s in seen2[r]
            af_hits += 1
        seen2[r].add(s)
assert af_hits == 24, af_hits
pot = SESSIONS * (TURNS - 1)
assert pot == 24

rr_tok = (reqs - rr_hits) * full_tok + rr_hits * hit_tok
af_tok = (reqs - af_hits) * full_tok + af_hits * hit_tok
assert abs(rr_tok - 65740.8) < 1e-6, rr_tok
assert abs(af_tok - 32563.2) < 1e-6, af_tok
saving = (1 - af_tok / rr_tok) * 100
assert abs(saving - 50.4674) < 0.001, saving
print(f"setup        {REPLICAS} replicas, {SESSIONS} sessions x {TURNS} turns "
      f"= {reqs} requests")
print(f"             prefix {PREFIX:,} tok + suffix {SUFFIX} tok; "
      "cached prefix billed at 10%")
print(f"round robin  hits {rr_hits}/{pot} = {rr_hits/pot*100:.1f}%   "
      f"billed {rr_tok:,.1f} tok-equiv")
print(f"affinity     hits {af_hits}/{pot} = {af_hits/pot*100:.1f}%  "
      f"billed {af_tok:,.1f} tok-equiv")
print(f"savings      {saving:.1f}% of the input bill (assert-pinned 50.4674%)")
print("-> round robin pays full price for three quarters of the repeats; "
      "affinity is one hash away")

# ---------------------------------------------------------------- F5
rule("F5 - the 429 ledger")
BURST, BUDGET_A = 80, 60
P_A = 0.000420                    # economy tier per-request bill, from F2
P_B = 3 * P_A                     # the open provider charges 3x
assert abs(P_A * MIX["economy"] - 3.528) < 1e-9
spilled = BURST - BUDGET_A
assert spilled == 20
bill_now = BUDGET_A * P_A + spilled * P_B
would_be = BURST * P_A
assert abs(bill_now - 0.0504) < 1e-9, bill_now
assert abs(would_be - 0.0336) < 1e-9, would_be
premium = (bill_now / would_be - 1) * 100
assert abs(premium - 50.0) < 1e-9, premium
print(f"minute burst {BURST} requests; provider A holds {BUDGET_A}/min, "
      "B is open at 3x price")
print("policy spill-now")
print(f"  accepted by A   {BUDGET_A} x ${P_A:.6f} = ${BUDGET_A * P_A:.6f}")
print(f"  spilled to B    {spilled} x ${P_B:.6f} = ${spilled * P_B:.6f}")
print(f"  minute bill     ${bill_now:.6f}  (A-only would-be bill "
      f"${would_be:.6f}: +{premium:.1f}%)")
dead = spilled * 2
print("policy retry-then-spill")
print(f"  same bill, plus {dead} dead 429'd calls into a closed bucket "
      "(429s seen 60)")
assert dead == 40
print("-> the spill lane has a price; burst sizing is routing config, "
      "not an afterthought")

# ---------------------------------------------------------------- F6
rule("F6 - the SLO downgrade ladder")
BUDGET_S = 2.0
frontier_lat = [1.6, 1.8, 2.1, 2.4, 2.6, 2.2, 2.3, 2.5, 1.9, 2.35]
standard_lat = [0.7, 0.8, 0.9, 1.0, 1.05, 1.1, 1.15, 1.2, 1.3, 1.4]


def p95(xs):
    ys = sorted(xs)
    return ys[-1 + int(-(-len(ys) * 95 // 100))]


p95f, p95s = p95(frontier_lat), p95(standard_lat)
assert abs(p95f - 2.6) < 1e-9, p95f
assert abs(p95s - 1.4) < 1e-9, p95s
print(f"p95 budget {BUDGET_S} s")
print(f"frontier samples p95 = {p95f:.2f} s -> BREACH")
print(f"standard samples p95 = {p95s:.2f} s -> inside")
per_class = MIX["frontier"] // 5
assert per_class == 240
moved = 2 * per_class
stay = MIX["frontier"] - moved
new_front = stay * TOK_IN / 1e6 * 15 + stay * TOK_OUT / 1e6 * 75
moved_std = moved * TOK_IN / 1e6 * 2.5 + moved * TOK_OUT / 1e6 * 10
new_std = 16.8 + moved_std
new_bill = MIX["economy"] * TOK_IN / 1e6 * 0.15 \
    + MIX["economy"] * TOK_OUT / 1e6 * 0.60 + new_front + new_std
assert abs(new_front - 34.56) < 1e-6, new_front
assert abs(moved_std - 3.36) < 1e-6, moved_std
assert abs(new_bill - 58.248) < 1e-6, new_bill
drop = (1 - new_bill / routed) * 100
assert abs(drop - 25.2538) < 0.001, drop
print("ladder move   the two borderline frontier classes (multi-hop, "
      "code review) drop to standard")
print(f"bill          ${routed:.3f} -> ${new_bill:.3f} "
      f"(-{drop:.1f}%, assert-pinned 25.2538%)")
q_big, q_mid = 92.0, 78.0
blended = (3 * q_big + 2 * q_mid) / 5
assert abs(blended - 86.4) < 1e-9, blended
print(f"quality       frontier band {q_big:.1f} -> {blended:.1f} blended "
      "(3 classes keep the big model)")
print("-> the ladder trades a measured quality point for the budget line; "
      "order the rungs before the breach")

# ---------------------------------------------------------------- F7
rule("F7 - the shadow verdict")
front_bill = MIX["frontier"] * TOK_IN / 1e6 * 15 \
    + MIX["frontier"] * TOK_OUT / 1e6 * 75
assert abs(front_bill - 57.6) < 1e-6, front_bill
cand_bill = front_bill * 0.60
assert abs(cand_bill - 34.56) < 1e-6, cand_bill
delta = front_bill - cand_bill
assert abs(delta - 23.04) < 1e-6, delta
SHADOW = {"extraction": (20, 20), "reasoning": (10, 12),
          "safety-refusal": (7, 8)}
total_ok = sum(ok for ok, _ in SHADOW.values())
total_n = sum(n for _, n in SHADOW.values())
assert (total_ok, total_n) == (37, 40), (total_ok, total_n)
agr = total_ok / total_n * 100
assert abs(agr - 92.5) < 1e-9, agr
safety_ok, safety_n = SHADOW["safety-refusal"]
gate = total_ok / total_n >= 0.95 and safety_ok == safety_n
assert gate is False
print(f"candidate    -40% on the frontier bill (${front_bill:.3f} -> "
      f"${cand_bill:.3f}, -${delta:.3f})")
print(f"shadow       {total_n} paired judgments vs the incumbent")
for cat, (ok, n) in SHADOW.items():
    print(f"  {cat:<15} {ok}/{n}")
print(f"agreement    {total_ok}/{total_n} = {agr:.1f}%")
print("gate         promote iff agreement >= 95% AND safety 8/8")
print("verdict      NO PROMOTION - the invoice wins, the gate says no")
print("-> the shadow gate reads agreement, not the invoice; "
      "a refusal flip is a policy regression")

print("")
print("FENCE-056-OK")
```

```text

F1 - the fallback cascade
------------------------------------------------------------
chain            primary (2% miss) -> fallback (5% miss) -> last resort (10% miss)
independence law 0.02 x 0.05 x 0.1 = 0.0001 -> 99.99% availability promised
correlated run   10,000 requests, fallback in the same region:
  primary missed   200 requests
  fallback missed   50 of those (one incident, two tiers)
  hard failed       10 requests -> observed 99.90% (10x the independence promise)
  extra upstream calls 250 per 10,000 = a 2.5% call surcharge
-> the product law assumes independence; a shared region does not care

F2 - the price ladder
------------------------------------------------------------
tier        in $/1M   out $/1M
economy     0.15      0.60
standard    2.50      10.00
frontier    15.00     75.00
workload    12,000 requests x (1,200 in / 400 out) = 14.4M in, 4.8M out
route mix   economy 70% (8,400) | standard 20% (2,400) | frontier 10% (1,200)
bill all-frontier   $576.000
bill all-standard   $84.000
bill routed         $77.928
savings vs frontier 86.5% (assert-pinned 86.4708%)
-> the router undercuts even the flat standard bill: 70% of traffic never needed it

F3 - the router verdict
------------------------------------------------------------
10 prompts, ground-truth tier vs a cheap classifier score; sweep t:
t      frontier  misrouted  overpaid
t=0.0       10          0         6
t=0.1       10          0         6
t=0.2        9          0         5
t=0.3        8          0         4
t=0.4        7          0         3
t=0.5        6          0         2
t=0.6        5          0         1
t=0.7        4          0         0  <- the knee
t=0.8        2          2         0  (multi-hop and code review land on the cheap tier)
t=0.9        1          3         0
t=1.0        0          4         0
-> the threshold is a dial, not a default: 0.7 routes every prompt right

F4 - the affinity ledger
------------------------------------------------------------
setup        4 replicas, 6 sessions x 5 turns = 30 requests
             prefix 2,048 tok + suffix 512 tok; cached prefix billed at 10%
round robin  hits 6/24 = 25.0%   billed 65,740.8 tok-equiv
affinity     hits 24/24 = 100.0%  billed 32,563.2 tok-equiv
savings      50.5% of the input bill (assert-pinned 50.4674%)
-> round robin pays full price for three quarters of the repeats; affinity is one hash away

F5 - the 429 ledger
------------------------------------------------------------
minute burst 80 requests; provider A holds 60/min, B is open at 3x price
policy spill-now
  accepted by A   60 x $0.000420 = $0.025200
  spilled to B    20 x $0.001260 = $0.025200
  minute bill     $0.050400  (A-only would-be bill $0.033600: +50.0%)
policy retry-then-spill
  same bill, plus 40 dead 429'd calls into a closed bucket (429s seen 60)
-> the spill lane has a price; burst sizing is routing config, not an afterthought

F6 - the SLO downgrade ladder
------------------------------------------------------------
p95 budget 2.0 s
frontier samples p95 = 2.60 s -> BREACH
standard samples p95 = 1.40 s -> inside
ladder move   the two borderline frontier classes (multi-hop, code review) drop to standard
bill          $77.928 -> $58.248 (-25.3%, assert-pinned 25.2538%)
quality       frontier band 92.0 -> 86.4 blended (3 classes keep the big model)
-> the ladder trades a measured quality point for the budget line; order the rungs before the breach

F7 - the shadow verdict
------------------------------------------------------------
candidate    -40% on the frontier bill ($57.600 -> $34.560, -$23.040)
shadow       40 paired judgments vs the incumbent
  extraction      20/20
  reasoning       10/12
  safety-refusal  7/8
agreement    37/40 = 92.5%
gate         promote iff agreement >= 95% AND safety 8/8
verdict      NO PROMOTION - the invoice wins, the gate says no
-> the shadow gate reads agreement, not the invoice; a refusal flip is a policy regression

FENCE-056-OK
```
