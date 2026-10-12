---
Document ID: CHEAT-SHEET-050
Title: "CHEAT-SHEET-050: MLOps Pipelines - the Lifecycle State Machine, the Challenger Verdict, and the Fleet Bill"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rag', 'mlops', 'ci-cd']
---

# CHEAT-SHEET-050: MLOps Pipelines - the Lifecycle State Machine, the Challenger Verdict, and the Fleet Bill

The MLOps surface is phase6-rag's 6500-mlops-pipelines track - 6501 ML Lifecycle Management, 6502 CI/CD for ML, 6503 Model Registry, 6504 Re-Embedding Policy and AB Testing and 6505 Response Caching and Stage Scaling - five modules with no sheet anywhere in the track (scope scan: the 00-META sheet index carries no id beside any of the five; CHEAT-SHEET-036 owns the RAG pipeline overview and CHEAT-SHEET-047 the retrieval core beside it, QUICK-REF-VOLUME-6 carries the syntax, not the closure). This sheet takes the track as the three questions the student actually asks: how a model moves from registration to retirement without ever skipping evidence (the lifecycle state machine, the challenger statistics, and the retirement audit), what actually makes a pipeline stop or a rollout turn around (verified pins, the data gate, the quality floor, and the canary's last stable percent), and what the serving fleet really costs once caching, key normalization, and stage scaling enter the ledger - closing the 6500 track.

The sheet runs as seven priced exhibits: the lifecycle state machine with its rollback door and the retirement audit's four-limit verdict (F1), McNemar's exact test on the discordant pairs (F2), the registry's lexicographic lie with the bump walk and the alias flip (F3), the verified pins plus the data and quality gates (F4), the canary's promote-or-rollback contract (F5), the re-embedding churn ledger with the shadow window and the storage bill (F6), and the serving fleet's four cache tiers, version-keyed invalidation, stage-scaling arithmetic, and the campaign day (F7). Every number below is printed by the canonical fence at the bottom of the page: the full 470-line stdlib fence reproduces all seven from fixed-date runs its own asserts pin - no numpy, no wall clock - and its 84-line output sits frozen below it byte-for-byte.

## The Lifecycle State Machine - Six States, One Rollback Door, and the Retirement Audit

A model's stage is state, and the transitions are the safety contract: registered, candidate, canary, production, shadow, retired. The fence walks the nine-step life of one model - registered to candidate to canary to production, then the rollback door production to candidate opens, the shortcut candidate to production is REFUSED (from candidate the only exits are canary or retirement - a candidate that never held canary traffic has no evidence to promote), back through canary to production, then production to shadow keeps the veteran warm while traffic drains, and shadow to retired closes the loop. History lands at exactly nine entries, and the refused shortcut never joins it.

| State | Allowed next states |
| --- | --- |
| registered | candidate |
| candidate | canary, retired |
| canary | production, candidate |
| production | shadow, candidate |
| shadow | retired |
| retired | (terminal - no exits) |

Retirement is an audit, not a hunch. Four limits decide: older than 365 days, degradation past 10% against the current champion's baseline, fewer than 1,000 calls per window, and cost above $0.75 per 1,000. At the fixed audit date 2026-09-26 the fence prices two residents: v1.0.0 (deployed 2025-06-15) is 468 days old with accuracy fallen from 0.880 to 0.710 - degradation +19.3% - serving 120 calls at $0.90/1k, and all four limits fire: RETIRE (age, performance, usage, cost). v1.4.2 is 87 days old, degrading -1.2% (it beats baseline), serving 54,000 calls at $0.40/1k: KEEP on every limit.

```text
production -> candidate  is the rollback door (candidate exits only by canary or retirement)
candidate  -> production is refused - the shortcut skips the canary evidence
production -> shadow     keeps the champion warm while traffic drains to the challenger
retired    -> (nothing)  retirement is terminal; only the registry alias forgets
```

## The Challenger Verdict - McNemar's Exact Test on the Discordant Pairs

Paired evals disagree, and the disagreement is the whole signal. McNemar's exact test throws away every query both models answer the same way and counts the discordant pairs: b where the challenger is right and the champion wrong, c the reverse, p = 2 x P(X at most min(b, c)) under Binomial(b + c, 0.5). The fence prices three evals: eval-1 (b=14, c=3) lands p=0.0127 - significant, challenger wins; eval-2 (b=5, c=7) lands p=0.7744 - noise, keep the champion; eval-3 (b=3, c=13) lands p=0.0213 - significant, champion wins. The third row is the trap: a challenger that looked better on overall accuracy can carry its own refutation in the paired counts. Overall accuracy averages over the quiet pairs; only the flips vote.

## The Model Registry - Lexicographic Lies, the Bump Walk, and the Alias Flip

Version strings sort as text and lie: lexicographic order puts 1.0.0 before 1.10.0 before 1.2.0 before 1.9.2 before 2.0.0, where the tuple order (major, minor, patch) reads 1.0.0, 1.2.0, 1.9.2, 1.10.0, 2.0.0 - the registry that sorts strings will serve the wrong latest. The bump walk prices what each change is worth: a docstring fix with identical inputs is a patch (1.0.0 to 1.0.1), quality +0.05 on the held-out set is a minor (1.1.0), a tokenizer swap that changes input shapes is a major (2.0.0), and a -0.06 regression against the champion is a major that never becomes champion (3.0.0). And the whole production rollout is one alias write: aliases go from champion 1 and challenger 2 to champion 3 and challenger 2 in a single assignment - v1 loses its alias but keeps its artifact, so rollback is repointing champion, not rebuilding anything.

## The Pipeline Gates - Verified Pins, the Data Gate, and the Quality Floor

A pipeline is only as trusted as what it pins. Six workflow actions pinned to majors with the releases they resolve: actions/checkout v7 (7.0.1), actions/setup-python v7 (7.0.0), actions/cache v6 (6.1.0), actions/upload-artifact v7 (7.0.2), actions/download-artifact v8 (8.0.2), astral-sh/setup-uv v10.2.0 (10.2.0) - a floating action tag is a supply-chain hole the day its repository moves.

| Workflow action | Pinned major | Release resolved |
| --- | --- | --- |
| actions/checkout | v7 | 7.0.1 |
| actions/setup-python | v7 | 7.0.0 |
| actions/cache | v6 | 6.1.0 |
| actions/upload-artifact | v7 | 7.0.2 |
| actions/download-artifact | v8 | 8.0.2 |
| astral-sh/setup-uv | v10.2.0 | 10.2.0 |

The data gate runs four checks before a single training step: schema consistency (3 columns, matching - pass), missing values (1 absent text_len in train - a warning to impute or drop), class distribution {0: 0.75, 1: 0.25} with min share 0.25 above the 0.05 floor (no imbalance flag), and train/val id overlap - 1 shared id is an ERROR for leakage, and one ERROR fails the whole gate: FAIL. The quality gate then prices two candidates against the champion's 0.884 at a 0.85 floor: 1.3.1 (acc 0.851, p95 41ms) passes and proceeds to challenger; 1.4.0 (acc 0.796, p95 38ms) is REJECTED - the pipeline stops and nothing deploys, faster latency or not.

```text
data gate stops the pipeline before training: schema, missing, imbalance, leakage
leakage is an ERROR - one shared train/val id fails the gate even with the rest clean
quality gate: accuracy floor 0.85 against the champion's 0.884 - 0.851 passes, 0.796 stops
a rejected candidate never deploys; the champion keeps serving at 0.884
```

## The Canary Rollout - Five Stages, One Threshold, and the Last Stable Percent

The canary is the only road to full traffic: 10, 25, 50, 75, 100 percent, with error rate and p95 gates at every stage. The fence rolls out two candidates over the same stage grid. good-candidate is clean at every stage (max error 0.004, max p95 910ms at the 75% stress point) and is promoted - the canary is now the production version, one alias write. bad-candidate is byte-identical through 50%, then breaches at 75% with p95 1200ms over the 1000ms limit - the verdict is rolled back, traffic returns to the previous version, and the last stable stage 50% is where the floor lands. The contract is asymmetric by design: promotion is earned once at 100%, rollback fires at the first breach, and the breached stage never re-tries on its own.

| Stage | good-candidate | bad-candidate |
| --- | --- | --- |
| 10% | 0.003 err, 131 ms | 0.003 err, 131 ms |
| 25% | 0.004 err, 130 ms | 0.004 err, 130 ms |
| 50% | 0.003 err, 126 ms | 0.003 err, 126 ms |
| 75% | 0.004 err, 910 ms | 0.006 err, 1200 ms - breach |
| 100% | 0.003 err, 125 ms | (rolled back at 75%) |

```text
10% -> 25% -> 50% -> 75% -> 100% is the only road to full traffic
one threshold breach at 75% rolls back to the last stable stage (50%)
error rate and p95 are gates, not suggestions - 1200ms at 0.6% error is a rollback
promotion is one alias write; rollback is repointing the same alias
```

## The Re-Embedding Ledger - Churn Math, the Shadow Window, and the Storage Bill

Re-embedding on a calendar is a habit, and the habit has a price. A 1,000,000-doc corpus at 0.5%/day churn changes 5,000 docs a day - 1,825,000 a year. The daily habit re-embeds 365,000,000 docs a year, 200.0x the churn; weekly lands 52,000,000, 28.5x; monthly lands 12,000,000, 6.6x - the monthly habit still re-embeds 10,175,000 docs a year for nothing. The change-driven policy embeds exactly what changed and pays 1.0x.

The shadow window is the honest A/B: run the challenger on live queries, score it, never serve it. The fence's hand-built window is 20 queries at top-10 recall: champion sums 145 (recall 0.725), challenger sums 151 (recall 0.755); per query that is +11 improved and -5 regressed, and the gate allows at most 8 regressions - SHIP, the challenger promotes and the champion stays warm. The storage bill shadows every dual-resident policy: 1536-d fp32 vectors are 6.14 GB per 1M docs, champion plus shadow resident is 12.29 GB, and a full backfill at 50k docs a day takes 20 days - the shadow window borrows capacity the corpus has to pay for.

```text
raw keys bill 12 gen-calls for 24 queries; normalized keys bill 9 - the 3 rewordings are free
a 2.0h TTL still leaks 1 stale answer inside its window; version-keyed leaks 0
retrieval-only halves the searches (24 -> 12) but not the generation bill
the cutover's own bill: 7,425,000 tokens re-billed while the cache re-warms
```

## The Fleet Bill - Cache Tiers, Version Keys, and the Cutover's Own Token

The fence replays a 24-query trace - 12 raw strings, 9 normalized keys - through four cache policies. No cache pays 24 generation calls and 24 searches for 12,000 tokens. Retrieval-only halves the searches (24 to 12) but still pays 12,000 generation tokens - the generation bill is the bill. A raw-string key halves the generation calls (12 calls, 6,000 tokens) and misses every rewording. The normalized key (lowercase, punctuation stripped, whitespace collapsed) lands 9 calls and 4,500 tokens - the 3 rewordings are worth 1,500 tokens the raw key never reclaims.

| Policy | gen calls | searches | tokens billed |
| --- | --- | --- | --- |
| no cache | 24 | 24 | 12,000 |
| retrieval-only | 24 | 12 | 12,000 |
| raw-key | 12 | 12 | 6,000 |
| normalized-key | 9 | 9 | 4,500 |

Invalidation is where caches bite back. Five arrivals cross a v1-to-v2 cutover at t=1.0 (refund policy changes 7 days to 3, payment gains iDEAL, refund timing moves from a day to hours), with entries written at t=0 under v1. Query-only invalidation serves 3 stale answers and recomputes nothing. A 2.0-hour TTL still leaks 1 stale answer - the t=1.2 arrival falls inside a window the write clock, not the cutover clock, controls - then recomputes 4. Version-keyed (the index version baked into the key) serves 0 stale, recomputes 5, and is the only policy a re-index can trust.

Stage scaling prices the fleet: per-stage autoscale walks replica counts with the load curve (34 retrieval + 62 generation replicas summed over 12 hours) for $530 with zero shortfalls; peak-provisioning holds the peak (5 retrieval + 9 generation) for all 12 hours at $924; the static average (3R + 5G) is cheaper still at $516 but shortfalls 17.0 retrieval and 29.5 generation RPS-hours at the peaks - the cheap plan is the one that drops traffic. At the 22 RPS peak, one generation replica hides two phases: 26,400 prefill tokens/s against 3,300 decode steps/s.

The campaign day puts it together: the naive fleet generates 262,800,000 tokens and serves 525,600 searches for $963; the tuned fleet (normalized keys, routed stages) generates 140,962,500 tokens and 281,925 searches for $551 - 43% less. And the cutover itself bills: 7,425,000 tokens are re-generated while the cache re-warms after the key flip - a rollout price every migration plan should carry as a line item.

## Known Failure Modes

| Failure mode | The tell |
| --- | --- |
| promoting on overall accuracy | paired evals disagree both ways (+11 improved, -5 regressed) - only the discordant pairs vote; p=0.7744 on eval-2 is noise wearing a majority |
| skipping canary because offline eval passed | 0.851 offline becomes p95 1200ms at 75% traffic; the state machine has no candidate-to-production edge for a reason |
| sorting versions as strings | 1.10.0 sorts before 1.2.0 and becomes the wrong latest - sort by (major, minor, patch) tuples |
| re-embedding on a calendar | the monthly habit re-embeds 12M docs a year against 1.825M that changed - 10,175,000 docs re-embedded for nothing |
| trusting a TTL to invalidate a corpus | a 2.0h TTL still leaks 1 stale answer written under v1 - the clock cannot see the index version |
| scaling every stage to the peak | peak-provisioned costs $924 where per-stage autoscale costs $530 at the same zero shortfall - the decode stage is 8x the retrieval unit price |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| champion regressed after a "safe" deploy | walk the state machine (F1): the shortcut edge does not exist - re-enter through canary and let the stage gates price it |
| two evals disagree about the same challenger | count only the discordant pairs and run McNemar (F2): b=5 c=7 is p=0.7744 noise; b=14 c=3 is p=0.0127 signal |
| the registry lists 1.10.0 before 1.2.0 | lexicographic sort lie (F3): sort by integer tuples, and pin the alias write as the deploy boundary |
| the pipeline failed on clean-looking data | the data gate's leakage check (F4): one shared train/val id is an ERROR even when schema and balance pass |
| the rollout broke at 75% and traffic flatlined | the canary contract (F5): last stable stage 50% holds; the breach stage never re-tries automatically |
| the cache serves old answers after a re-index | version-keyed invalidation (F7): bake the index version into the key - a TTL leaks inside its own window |

## Quick Reference For

- [Module 6501: ML Lifecycle Management](../../phases/phase6-rag/6500-mlops-pipelines/6501-ML-Lifecycle-Management.md) - the state machine, the retirement audit and the four limits this sheet's F1 prices
- [Module 6502: CI/CD for ML](../../phases/phase6-rag/6500-mlops-pipelines/6502-CI-CD-for-ML.md) - the gate machinery behind F4 and F5, pins to production
- [Module 6503: Model Registry](../../phases/phase6-rag/6500-mlops-pipelines/6503-Model-Registry.md) - semver, aliases and the lineage the bump walk exercises
- [Module 6504: Re-Embedding Policy and AB Testing](../../phases/phase6-rag/6500-mlops-pipelines/6504-Re-Embedding-Policy-and-AB-Testing.md) - the churn ledger and the shadow window in full
- [Module 6505: Response Caching and Stage Scaling](../../phases/phase6-rag/6500-mlops-pipelines/6505-Response-Caching-and-Stage-Scaling.md) - the four tiers, the invalidation section and the campaign day this sheet's F7 condenses

## The Canonical Fence

The full stdlib fence below reproduces every number on this page - F1 through F7 - from fixed-date runs its own asserts pin: no numpy, no wall clock, byte-identical across runs.

```python
"""tick-1022 canonical fence - CHEAT-SHEET-050 MLOps Pipelines.
Stdlib only. Deterministic: fixed inputs, fixed dates, no time, no
set-order dependence. Prints F1..F7 + FENCE-050-OK tail."""
import math
import re
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- F1
print("== F1: the lifecycle state machine + the retirement audit ==")
ALLOWED = {
    "registered": ["candidate"],
    "candidate":  ["canary", "retired"],
    "canary":     ["production", "candidate"],
    "production": ["shadow", "candidate"],
    "shadow":     ["retired"],
    "retired":    [],
}


def transition(model, src, dst):
    if model["stage"] != src:
        print("%-11s -> %-11s REJECTED (model is in %s)" % (src, dst, model["stage"]))
        return False
    if dst not in ALLOWED[src]:
        print("%-11s -> %-11s REJECTED (from %s only: %s)"
              % (src, dst, src, ", ".join(ALLOWED[src])))
        return False
    print("%-11s -> %-11s ok" % (src, dst))
    model["stage"] = dst
    model["history"].append(dst)
    return True


model = {"stage": "registered", "history": ["registered"]}
transition(model, "registered", "candidate")
transition(model, "candidate", "canary")
transition(model, "canary", "production")
transition(model, "production", "candidate")   # the rollback door
transition(model, "candidate", "production")   # the shortcut: refused
transition(model, "candidate", "canary")
transition(model, "canary", "production")
transition(model, "production", "shadow")
transition(model, "shadow", "retired")
history = " -> ".join(model["history"])
print("final history: %s" % history)
assert history == ("registered -> candidate -> canary -> production -> candidate"
                   " -> canary -> production -> shadow -> retired")

TODAY = date(2026, 9, 26)
LEDGER = [
    {"v": "1.0.0", "deployed": date(2025, 6, 15), "accuracy": 0.710,
     "baseline": 0.880, "calls": 120, "cost": 0.90},
    {"v": "1.4.2", "deployed": date(2026, 7, 1), "accuracy": 0.891,
     "baseline": 0.880, "calls": 54000, "cost": 0.40},
]
lines_out = []
for rec in LEDGER:
    age = (TODAY - rec["deployed"]).days
    deg = (rec["baseline"] - rec["accuracy"]) / rec["baseline"]
    deg_pct = round(deg * 100, 2)   # pin to basis points before the %.1f render
    hits = []
    if age > 365:
        hits.append("age")
    if deg > 0.10:
        hits.append("performance")
    if rec["calls"] < 1000:
        hits.append("usage")
    if rec["cost"] > 0.75:
        hits.append("cost")
    verdict = "RETIRE (%s)" % ", ".join(hits) if hits else "KEEP"
    line = ("%s: age %3dd  degradation %+.1f%%  calls %5d  $%.2f/1k -> %s"
            % (rec["v"], age, deg_pct, rec["calls"], rec["cost"], verdict))
    print(line)
    lines_out.append(line)
assert lines_out[0] == ("1.0.0: age 468d  degradation +19.3%  calls   120"
                        "  $0.90/1k -> RETIRE (age, performance, usage, cost)")
assert lines_out[1] == ("1.4.2: age  87d  degradation -1.2%  calls 54000"
                        "  $0.40/1k -> KEEP")
assert (TODAY - date(2025, 6, 15)).days == 468
assert (TODAY - date(2026, 7, 1)).days == 87
assert abs((0.880 - 0.710) / 0.880 - 0.1931818) < 1e-6

# ---------------------------------------------------------------- F2
print("== F2: the McNemar exact test ==")


def mcnemar_exact(b, c):
    """Two-sided exact p-value for the b/c discordant-pair counts."""
    n = b + c
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


for label, b, c in [("eval-1", 14, 3), ("eval-2", 5, 7), ("eval-3", 3, 13)]:
    p = mcnemar_exact(b, c)
    if p < 0.05:
        verdict = "significant, %s wins" % ("challenger" if b > c else "champion")
    else:
        verdict = "not significant, keep champion"
    print("%s: b=%2d c=%2d p=%.4f -> %s" % (label, b, c, p, verdict))
assert abs(mcnemar_exact(14, 3) - 0.012726) < 5e-7
assert abs(mcnemar_exact(5, 7) - 0.774414) < 5e-7
assert abs(mcnemar_exact(3, 13) - 0.021271) < 5e-7

# ---------------------------------------------------------------- F3
print("== F3: the registry - semver sort, bump walk, alias flip ==")
VERSIONS = ["1.0.0", "1.10.0", "1.2.0", "1.9.2", "2.0.0"]
print("lexicographic: %s" % " < ".join(sorted(VERSIONS)))
print("tuple sort   : %s" % " < ".join(
    sorted(VERSIONS, key=lambda v: tuple(int(x) for x in v.split(".")))))


def bump(v, kind):
    a, b, c = (int(x) for x in v.split("."))
    if kind == "major":
        return "%d.0.0" % (a + 1)
    if kind == "minor":
        return "%d.%d.0" % (a, b + 1)
    return "%d.%d.%d" % (a, b, c + 1)


CHANGES = [
    ("docstring fix, same inputs", "patch"),
    ("quality +0.05 on the held-out set", "minor"),
    ("tokenizer swap - inputs change shape", "major"),
    ("regression -0.06 vs champion", "major"),
]
cur = "1.0.0"
print("bump walk from %s:" % cur)
for why, kind in CHANGES:
    nxt = bump(cur, kind)
    print("  %s --%s--> %s  (%s)" % (cur, kind, nxt, why))
    cur = nxt
assert cur == "3.0.0"

aliases = {"champion": "1", "challenger": "2"}
print("aliases before promote: %s" % aliases)
aliases["champion"] = "3"          # the whole rollout is one alias write
print("aliases after promote:  %s" % aliases)
print("v1 loses its alias, keeps its artifact: rollback is repointing champion")
assert aliases == {"champion": "3", "challenger": "2"}

# ---------------------------------------------------------------- F4
print("== F4: verified pins + data gate + quality gate ==")
PINS = [
    ("actions/checkout", "v7", "7.0.1"),
    ("actions/setup-python", "v7", "7.0.0"),
    ("actions/cache", "v6", "6.1.0"),
    ("actions/upload-artifact", "v7", "7.0.2"),
    ("actions/download-artifact", "v8", "8.0.2"),
    ("astral-sh/setup-uv", "v10.2.0", "10.2.0"),
]
for name, major, rel in PINS:
    print("  %-27s %-9s (%s)" % (name, major, rel))


def data_gate(train, val):
    errors, warnings = [], []
    if list(train[0]) == list(val[0]):
        print("  [1/4] schema check: %d cols, consistent" % len(train[0]))
    else:
        errors.append("schema")
        print("  [1/4] schema check: MISMATCH")
    missing = sum(1 for row in train for v in row.values() if v is None)
    if missing:
        warnings.append("missing")
        print("  [2/4] missing values: %d in train (warning: impute or drop)" % missing)
    else:
        print("  [2/4] missing values: none")
    labels = [row["label"] for row in train]
    dist = {lab: labels.count(lab) / len(labels) for lab in sorted(set(labels))}
    share = min(dist.values())
    print("  [3/4] class distribution: {%s} - min share %.2f"
          % (", ".join("%d: %.2f" % (k, v) for k, v in dist.items()), share))
    if share < 0.05:
        warnings.append("imbalance")
    overlap = {row["id"] for row in train} & {row["id"] for row in val}
    if overlap:
        errors.append("leakage")
        print("  [4/4] train/val id overlap: %d shared id(s) -> ERROR: leakage"
              % len(overlap))
    else:
        print("  [4/4] train/val id overlap: none")
    verdict = "FAIL" if errors else ("WARN" if warnings else "PASS")
    print("  gate decision: %s" % verdict)
    return verdict


TRAIN = [
    {"id": 1, "text_len": 42, "label": 0},
    {"id": 2, "text_len": 18, "label": 1},
    {"id": 3, "text_len": None, "label": 0},
    {"id": 4, "text_len": 57, "label": 0},
]
VAL = [
    {"id": 2, "text_len": 20, "label": 1},
    {"id": 5, "text_len": 33, "label": 0},
]
assert data_gate(TRAIN, VAL) == "FAIL"

FLOOR, CHAMPION = 0.85, 0.884
for cand in [
    {"v": "1.3.1", "acc": 0.851, "p95": 41},
    {"v": "1.4.0", "acc": 0.796, "p95": 38},
]:
    ok = cand["acc"] >= FLOOR and cand["p95"] <= 100
    verdict = ("PASS -> challenger (champion stays %.3f)" % CHAMPION if ok
               else "REJECTED - pipeline stops, nothing deploys")
    print("  %s: acc %.3f, p95 %dms -> %s" % (cand["v"], cand["acc"], cand["p95"], verdict))

# ---------------------------------------------------------------- F5
print("== F5: canary promote-or-rollback ==")
STAGES = [10, 25, 50, 75, 100]
GOOD = {10: (0.003, 131), 25: (0.004, 130), 50: (0.003, 126),
        75: (0.004, 910), 100: (0.003, 125)}
BAD = dict(GOOD)
BAD[75] = (0.006, 1200)


def rollout(name, stages):
    last_ok = 0
    for pct in STAGES:
        err, p95 = stages[pct]
        why = []
        if err > 0.05:
            why.append("error rate %.3f exceeds 0.05" % err)
        if p95 > 1000:
            why.append("p95 %dms exceeds 1000ms" % p95)
        if why:
            print("  %s stage %3d%%: %s" % (name, pct, "; ".join(why)))
            print("  %s verdict: rolled back - traffic returns to the previous"
                  " version (last stable stage %d%%)" % (name, last_ok))
            return False
        print("  %s stage %3d%%: max error %.3f, max p95 %dms -> ok"
              % (name, pct, err, p95))
        last_ok = pct
    print("  %s verdict: promoted - canary is now the production version" % name)
    return True


assert rollout("good-candidate", GOOD)
assert not rollout("bad-candidate", BAD)

# ---------------------------------------------------------------- F6
print("== F6: re-embedding churn + the shadow window ==")
N_DOCS, CHURN = 1_000_000, 0.005
changed_day = int(N_DOCS * CHURN)
changed_year = changed_day * 365
print("corpus %d docs at %.1f%%/day churn -> %d changed docs/day"
      % (N_DOCS, CHURN * 100, changed_day))
for habit, runs in [("daily", 365), ("weekly", 52), ("monthly", 12)]:
    docs = runs * N_DOCS
    print("%-8s re-embed: %9d docs = %.1fx the %d that changed"
          % (habit, docs, docs / changed_year, changed_year))
waste = 12 * N_DOCS - changed_year
print("monthly habit waste: %d docs re-embedded for nothing each year" % waste)
assert changed_day == 5000 and changed_year == 1_825_000 and waste == 10_175_000

SHADOW_N = 20
champ = [8, 6, 7, 5, 9, 10, 4, 7, 8, 9, 6, 7, 5, 8, 10, 6, 7, 9, 5, 9]
chall = [9, 7, 8, 6, 9, 10, 5, 8, 9, 10, 7, 8, 6, 7, 9, 5, 6, 8, 5, 9]
crec = sum(champ) / (SHADOW_N * 10)   # top-10 recall: at most 10 per query
xrec = sum(chall) / (SHADOW_N * 10)
up = sum(1 for a, b in zip(champ, chall) if b > a)
down = sum(1 for a, b in zip(champ, chall) if b < a)
print("hand-built shadow window: %d queries, top-10 recall each" % SHADOW_N)
print("champion   sum %d -> recall %.3f" % (sum(champ), crec))
print("challenger sum %d -> recall %.3f" % (sum(chall), xrec))
print("query deltas: +%d improved, -%d regressed (the gate allows <= 8)" % (up, down))
ship = xrec >= crec and down <= 8
print("verdict: %s" % ("SHIP - challenger promotes, champion stays warm"
                       if ship else "HOLD"))
assert sum(champ) == 145 and sum(chall) == 151
assert abs(crec - 0.725) < 1e-9 and abs(xrec - 0.755) < 1e-9
assert up == 11 and down == 5 and ship

DIM, FP32 = 1536, 4
gb1 = N_DOCS * DIM * FP32 / 1e9
print("fp32 %d-d vectors: %.2f GB per 1M docs; %.2f GB with champion + shadow resident"
      % (DIM, gb1, 2 * gb1))
print("full backfill at 50k docs/day: %d days" % (N_DOCS // 50_000))
assert abs(gb1 - 6.144) < 1e-9

# ---------------------------------------------------------------- F7
print("== F7: cache tiers, version invalidation, stage scaling, campaign ==")
trace = [
    "What is the refund policy?",
    "How do I reset my password?",
    "what is   the refund policy ?",
    "Where are EU shipments dispatched from?",
    "How do I reset my password?",
    "What is the refund policy?",
    "Can I change my shipping address after ordering?",
    "How do I delete my account?",
    "Where are EU shipments dispatched from",
    "What is the refund policy?",
    "How do I delete my account?",
    "How long do refunds take to arrive?",
    "Can I change my shipping address after ordering?",
    "How do I reset my password?",
    "What payment methods do you accept?",
    "Do you ship to Canada?",
    "What is the refund policy?",
    "How do I contact support?",
    "Do you ship to Canada",
    "How do I delete my account?",
    "What payment methods do you accept?",
    "How do I contact support?",
    "Where are EU shipments dispatched from?",
    "What is the refund policy?",
]
GEN_TOKENS = 500


def norm_key(q):
    s = q.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())


TIERS = ["no cache", "retrieval-only", "raw-key", "normalized-key"]
tiers = {c: [0, 0] for c in TIERS}
seen_ret, seen_raw, seen_norm = set(), set(), set()
for q in trace:
    tiers["no cache"][0] += 1
    tiers["no cache"][1] += 1
    tiers["retrieval-only"][0] += 1
    if q not in seen_ret:
        seen_ret.add(q)
        tiers["retrieval-only"][1] += 1
    if q not in seen_raw:
        seen_raw.add(q)
        tiers["raw-key"][0] += 1
        tiers["raw-key"][1] += 1
    k = norm_key(q)
    if k not in seen_norm:
        seen_norm.add(k)
        tiers["normalized-key"][0] += 1
        tiers["normalized-key"][1] += 1
for c in TIERS:
    gen, srch = tiers[c]
    print("  %-16s gen %2d  searches %2d  tokens %7s"
          % (c, gen, srch, format(gen * GEN_TOKENS, ",")))
print("  unique normalized keys: %d; the 3 rewordings are worth %s tokens"
      % (len(seen_norm),
         format((tiers["raw-key"][0] - tiers["normalized-key"][0]) * GEN_TOKENS, ",")))
assert tiers["no cache"] == [24, 24]
assert tiers["retrieval-only"] == [24, 12]
assert tiers["raw-key"] == [12, 12]
assert tiers["normalized-key"] == [9, 9]

ARRIVALS = [
    ("refund policy", 1.2),
    ("ship to Canada", 2.0),
    ("payment methods", 2.5),
    ("refund timing", 3.0),
    ("warranty", 3.5),
]
V1 = {"refund policy": "refunds take 7 business days",
      "ship to Canada": "yes, ships to Canada",
      "payment methods": "cards and PayPal",
      "refund timing": "one business day",
      "warranty": "24 months"}
V2 = {"refund policy": "refunds take 3 business days",
      "ship to Canada": "yes, ships to Canada",
      "payment methods": "cards, PayPal, and iDEAL",
      "refund timing": "four business hours",
      "warranty": "24 months"}
TTL = 2.0   # entries were written at t=0 under v1; the cutover lands at t=1.0


def invalidate(policy):
    stale = correct = recompute = 0
    for q, t in ARRIVALS:
        if policy == "query-only":
            cached = True
        elif policy == "ttl":
            cached = t < TTL          # the clock cannot see the corpus change
        else:                         # version-keyed: the key carries the index version
            cached = False
        served = V1[q] if cached else V2[q]
        recompute += 0 if cached else 1
        if served == V2[q]:
            correct += 1
        else:
            stale += 1
    return stale, correct, recompute


for policy in ["query-only", "ttl", "version-keyed"]:
    s, c, r = invalidate(policy)
    print("  %-13s stale %d  correct %d  recomputed %d" % (policy, s, c, r))
assert invalidate("query-only") == (3, 2, 0)
assert invalidate("ttl") == (1, 4, 4)
assert invalidate("version-keyed") == (0, 5, 5)

LOAD = [4, 6, 9, 12, 16, 20, 22, 19, 15, 11, 7, 5]
CAP_R, COST_R = 5.0, 1.0
CAP_G, COST_G = 2.5, 8.0
rep_r = [math.ceil(x / CAP_R) for x in LOAD]
rep_g = [math.ceil(x / CAP_G) for x in LOAD]
peak_r, peak_g = max(rep_r), max(rep_g)
tuned = COST_R * sum(rep_r) + COST_G * sum(rep_g)
peak = COST_R * peak_r * 12 + COST_G * peak_g * 12
stat_r, stat_g = round(sum(rep_r) / 12), round(sum(rep_g) / 12)
stat_cost = COST_R * stat_r * 12 + COST_G * stat_g * 12
short_r = sum(max(0.0, x - stat_r * CAP_R) for x in LOAD)
short_g = sum(max(0.0, x - stat_g * CAP_G) for x in LOAD)
print("  per-stage autoscale: cost %d, shortfalls 0/0" % tuned)
print("  peak-provisioned   : cost %d, shortfalls 0/0" % peak)
print("  static-average %dR/%dG: cost %d, shortfalls %.1f retrieval / %.1f generation RPS-hours"
      % (stat_r, stat_g, stat_cost, short_r, short_g))
print("  one replica hides two phases at the 22 RPS peak: prefill %s tok/s vs decode %s steps/s"
      % (format(22 * 1200, ","), format(22 * 150, ",")))
assert sum(rep_r) == 34 and sum(rep_g) == 62 and peak_r == 5 and peak_g == 9
assert tuned == 530 and peak == 924 and stat_cost == 516
assert short_r == 17.0 and short_g == 29.5

HIT_FULL = 9 / 24
SEM_ADD = 3 / 10
WARM = 2
CUTOVER_T = 6
PRICE = 0.15


def hit_at(t):
    return HIT_FULL * (t + 1) / WARM if t < WARM else HIT_FULL


naive_tokens = naive_search = tuned_tokens = tuned_search = tuned_cost = 0.0
cutover_burn = 0.0
for t, rps in enumerate(LOAD):
    naive_tokens += rps * 3600 * GEN_TOKENS
    naive_search += rps * 3600
    h = hit_at(t)
    if t >= CUTOVER_T:
        h = hit_at(t - CUTOVER_T) if t - CUTOVER_T < WARM else HIT_FULL
    miss = 1.0 - h
    sem = miss * SEM_ADD if t >= WARM and (t < CUTOVER_T or t - CUTOVER_T >= WARM) else 0.0
    served_by_gen = miss - sem
    if t >= CUTOVER_T:
        cutover_burn += (HIT_FULL - h) * rps * 3600 * GEN_TOKENS
    tuned_tokens += served_by_gen * rps * 3600 * GEN_TOKENS
    tuned_search += served_by_gen * rps * 3600
    tuned_cost += COST_R * rep_r[t] + COST_G * rep_g[t]
naive_cost = COST_R * peak_r * 12 + COST_G * peak_g * 12
naive_total = naive_tokens / 1e6 * PRICE + naive_cost
tuned_total = tuned_tokens / 1e6 * PRICE + tuned_cost
print("  naive fleet day: %s gen tokens, %s searches, $%.0f replicas + $%.2f tokens -> $%.0f"
      % (format(int(naive_tokens), ","), format(int(naive_search), ","),
         naive_cost, naive_tokens / 1e6 * PRICE, naive_total))
print("  tuned fleet day: %s gen tokens, %s searches, $%.0f replicas + $%.2f tokens -> $%.0f"
      % (format(int(tuned_tokens), ","), format(int(tuned_search), ","),
         tuned_cost, tuned_tokens / 1e6 * PRICE, tuned_total))
print("  the cutover's own bill: %s tokens re-billed while the cache re-warms"
      " after the v1->v2 key flip" % format(int(cutover_burn), ","))
assert int(naive_tokens) == 262_800_000
assert int(tuned_tokens) == 140_962_500
assert int(naive_search) == 525_600
assert int(tuned_search) == 281_925
assert tuned_cost == 530 and naive_cost == 924
assert int(cutover_burn) == 7_425_000
assert abs(naive_total - 963.42) < 1e-9
assert abs(tuned_total - 551.144375) < 1e-9

print("FENCE-050-OK")
```

Its frozen output:

```text
== F1: the lifecycle state machine + the retirement audit ==
registered  -> candidate   ok
candidate   -> canary      ok
canary      -> production  ok
production  -> candidate   ok
candidate   -> production  REJECTED (from candidate only: canary, retired)
candidate   -> canary      ok
canary      -> production  ok
production  -> shadow      ok
shadow      -> retired     ok
final history: registered -> candidate -> canary -> production -> candidate -> canary -> production -> shadow -> retired
1.0.0: age 468d  degradation +19.3%  calls   120  $0.90/1k -> RETIRE (age, performance, usage, cost)
1.4.2: age  87d  degradation -1.2%  calls 54000  $0.40/1k -> KEEP
== F2: the McNemar exact test ==
eval-1: b=14 c= 3 p=0.0127 -> significant, challenger wins
eval-2: b= 5 c= 7 p=0.7744 -> not significant, keep champion
eval-3: b= 3 c=13 p=0.0213 -> significant, champion wins
== F3: the registry - semver sort, bump walk, alias flip ==
lexicographic: 1.0.0 < 1.10.0 < 1.2.0 < 1.9.2 < 2.0.0
tuple sort   : 1.0.0 < 1.2.0 < 1.9.2 < 1.10.0 < 2.0.0
bump walk from 1.0.0:
  1.0.0 --patch--> 1.0.1  (docstring fix, same inputs)
  1.0.1 --minor--> 1.1.0  (quality +0.05 on the held-out set)
  1.1.0 --major--> 2.0.0  (tokenizer swap - inputs change shape)
  2.0.0 --major--> 3.0.0  (regression -0.06 vs champion)
aliases before promote: {'champion': '1', 'challenger': '2'}
aliases after promote:  {'champion': '3', 'challenger': '2'}
v1 loses its alias, keeps its artifact: rollback is repointing champion
== F4: verified pins + data gate + quality gate ==
  actions/checkout            v7        (7.0.1)
  actions/setup-python        v7        (7.0.0)
  actions/cache               v6        (6.1.0)
  actions/upload-artifact     v7        (7.0.2)
  actions/download-artifact   v8        (8.0.2)
  astral-sh/setup-uv          v10.2.0   (10.2.0)
  [1/4] schema check: 3 cols, consistent
  [2/4] missing values: 1 in train (warning: impute or drop)
  [3/4] class distribution: {0: 0.75, 1: 0.25} - min share 0.25
  [4/4] train/val id overlap: 1 shared id(s) -> ERROR: leakage
  gate decision: FAIL
  1.3.1: acc 0.851, p95 41ms -> PASS -> challenger (champion stays 0.884)
  1.4.0: acc 0.796, p95 38ms -> REJECTED - pipeline stops, nothing deploys
== F5: canary promote-or-rollback ==
  good-candidate stage  10%: max error 0.003, max p95 131ms -> ok
  good-candidate stage  25%: max error 0.004, max p95 130ms -> ok
  good-candidate stage  50%: max error 0.003, max p95 126ms -> ok
  good-candidate stage  75%: max error 0.004, max p95 910ms -> ok
  good-candidate stage 100%: max error 0.003, max p95 125ms -> ok
  good-candidate verdict: promoted - canary is now the production version
  bad-candidate stage  10%: max error 0.003, max p95 131ms -> ok
  bad-candidate stage  25%: max error 0.004, max p95 130ms -> ok
  bad-candidate stage  50%: max error 0.003, max p95 126ms -> ok
  bad-candidate stage  75%: p95 1200ms exceeds 1000ms
  bad-candidate verdict: rolled back - traffic returns to the previous version (last stable stage 50%)
== F6: re-embedding churn + the shadow window ==
corpus 1000000 docs at 0.5%/day churn -> 5000 changed docs/day
daily    re-embed: 365000000 docs = 200.0x the 1825000 that changed
weekly   re-embed:  52000000 docs = 28.5x the 1825000 that changed
monthly  re-embed:  12000000 docs = 6.6x the 1825000 that changed
monthly habit waste: 10175000 docs re-embedded for nothing each year
hand-built shadow window: 20 queries, top-10 recall each
champion   sum 145 -> recall 0.725
challenger sum 151 -> recall 0.755
query deltas: +11 improved, -5 regressed (the gate allows <= 8)
verdict: SHIP - challenger promotes, champion stays warm
fp32 1536-d vectors: 6.14 GB per 1M docs; 12.29 GB with champion + shadow resident
full backfill at 50k docs/day: 20 days
== F7: cache tiers, version invalidation, stage scaling, campaign ==
  no cache         gen 24  searches 24  tokens  12,000
  retrieval-only   gen 24  searches 12  tokens  12,000
  raw-key          gen 12  searches 12  tokens   6,000
  normalized-key   gen  9  searches  9  tokens   4,500
  unique normalized keys: 9; the 3 rewordings are worth 1,500 tokens
  query-only    stale 3  correct 2  recomputed 0
  ttl           stale 1  correct 4  recomputed 4
  version-keyed stale 0  correct 5  recomputed 5
  per-stage autoscale: cost 530, shortfalls 0/0
  peak-provisioned   : cost 924, shortfalls 0/0
  static-average 3R/5G: cost 516, shortfalls 17.0 retrieval / 29.5 generation RPS-hours
  one replica hides two phases at the 22 RPS peak: prefill 26,400 tok/s vs decode 3,300 steps/s
  naive fleet day: 262,800,000 gen tokens, 525,600 searches, $924 replicas + $39.42 tokens -> $963
  tuned fleet day: 140,962,500 gen tokens, 281,925 searches, $530 replicas + $21.14 tokens -> $551
  the cutover's own bill: 7,425,000 tokens re-billed while the cache re-warms after the v1->v2 key flip
FENCE-050-OK
```
