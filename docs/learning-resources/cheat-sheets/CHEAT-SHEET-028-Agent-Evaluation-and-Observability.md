---
Document ID: CHEAT-SHEET-028
Title: "CHEAT-SHEET-028: Agent Evaluation and Observability"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'evaluation', 'observability', 'agents', 'benchmarks']
---

# CHEAT-SHEET-028: Agent Evaluation and Observability

**Quick Reference for:** the three-rung evaluation ladder, trajectories as the unit of record, the four deterministic scorers, bootstrap confidence intervals on small samples, the pairwise judge's position bias and its swap-averaging cure, the OpenTelemetry GenAI trace schema, trace-to-budget rollups with per-span attribution, and the two-tripwire regression gate that makes agents CI-able.

Every other agent sheet in this set assumes the loop works. This one answers the question that decides whether it ships: is the agent good, and did yesterday's change make it worse? Deep dive: module 7104.

## The Evaluation Ladder: Three Rungs

Every scoring method lives on one of three rungs, and the rung decides the failure mode:

| Rung | Example | Catches | Misses | Cost |
|---|---|---|---|---|
| 1 - deterministic | exact match, JSON schema, tool sequence | factual drift, format breaks, wasted calls | anything phrased differently but correct | free, reproducible |
| 2 - programmatic | rubric sums over extracted features, distance metrics | graded quality on measurable axes | properties you cannot extract | cheap, reproducible |
| 3 - LLM-as-judge | rubric prompt, pairwise comparison | fuzzy correctness, tone, reasoning quality | depends on the judge: bias, variance, self-preference | paid, noisy |

Climb only as far as needed. A tool-sequence check catches the wasted `calculator` call no judge would flag; a judge catches the subtly wrong itinerary no string comparison catches. Production suites run rungs 1 and 2 on every run and rung 3 on a sample — the judge is the expensive, noisy end of the pipeline, not the default.

## Trajectories as Data

Everything downstream consumes the same record. One agent run is one line of JSONL:

```text
{
  "task": "book-paris-trip",
  "steps": 5,
  "tool_calls": ["search", "calendar", "search", "booking"],
  "answer": "Booked Tue 09:00, 2 nights, $410",
  "success": true
}
```

The schema is deliberately boring: what was attempted, what tools fired and in what order, what came out, and — for labeled sets — whether a human grader called it a success. Two disciplines follow. **Record everything now, score later**: storage is cheap, re-running an agent on the same inputs is not — non-determinism and live services guarantee drift. Keep a **golden set**: a small hand-labeled subset of tasks that must never regress, versioned alongside the agent itself.

## Deterministic Scorers

Rung 1 is where discipline pays. Four scorers over four recorded runs:

| Scorer | This run | Blind spot |
|---|---|---|
| `exact` | 2/4 — under-credits correct-but-verbose answers | any phrasing that differs |
| `contains` | 4/4 — over-credits, the expected string rides inside answers of any quality | surface matching is a smoke test, not a scorer |
| `json_result` | 1/4 — parses and checks `result` in a dict | answers outside the contract |
| `tools_match` | 2/4 — grades *how* the agent worked | only meaningful with a golden trajectory |

The load-bearing case is `sum-short`: the answer `"42"` is right, but the run fired **no** tools where the golden trajectory requires `calculator` — `exact` and `contains` pass it, `tools_match` fails it, and that is the point. Tool-sequence scoring is the axis string scorers cannot see and the cheapest regression tripwire you own: a prompt change that breaks tool selection shows up here before any human reads an output.

## Confidence: Bootstrap the Small Sample

Aggregate the verdicts and the temptation appears: report "84% success". Twenty-five runs are what a real team has for a new agent version, and the fence refuses the point estimate — resample the runs with replacement 1,000 times, recompute the rate, take the 2.5/97.5 percentiles:

**21/25 = 84%, bootstrap 95% CI [68%, 96%] — 28 points wide.** Mean steps 4.7, tool accuracy 94%. A candidate at 78% and a baseline at 88% are statistically the same agent; any two-run comparison made without this interval is a decision made on noise. Step efficiency and tool accuracy get the same treatment when they drive a go/no-go call.

## The Pairwise Judge: Position Bias and the Swap Cure

Rung 3 asks a second model to grade; the dominant format is pairwise — two answers, which is better. The fence implements the judge's bias structure, a 0.9-point primacy bonus for whichever answer is shown first, against a 0.8-point true gap:

**Fixed order flips**: A first → A; B first → B — same answers, same judge, the verdict follows presentation order because primacy outweighs the gap. **Unanimity is not safety**: the same five judges vote `A:5 B:0` shown A-first and `A:0 B:5` shown B-first — the vote is the order, not the answers, so agreement between judges is not evidence when they share the bias. **Swap-averaging cancels it**: score both orders, average the margins, reuse the same two noise draws in both orders (the paired design) — 14 comparisons land at **+0.80 per comparison, exactly the A-minus-B gap**, winner A. Production rules: randomize or balance presentation order, report both orders, treat a judge that disagrees with itself across orders as broken. Canonical warning: Zheng et al.'s MT-Bench study — judge agreement with humans collapses exactly where order bias bites.

## The Trace Schema: OpenTelemetry GenAI

Evaluations are computed after the fact from records; observability writes those records *while the agent runs*. The GenAI semantic conventions define the span vocabulary — one `invoke_agent` span containing `chat` spans (model calls) and `execute_tool` spans (tool calls), each carrying `gen_ai.*` attributes:

```text
invoke_agent  gen_ai.agent.name="research-agent"  gen_ai.agent.version="1.4.0"
├─ chat          gen_ai.operation.name="chat"   gen_ai.provider.name="openai"
│                gen_ai.request.model="gpt-5-mini"
│                gen_ai.usage.input_tokens=820  gen_ai.usage.output_tokens=64
└─ execute_tool  gen_ai.operation.name="execute_tool"
                 gen_ai.tool.name="web_search"  gen_ai.tool.call.id="call_01"
                 gen_ai.tool.call.result="3 results"
rollup rule: usage attributes must land on every span - validate on write or the
             rollup silently fills zeros, which is worse than no rollup
```

The attribute names are the contract and they are still moving: the conventions live in their own repo at Development stability, `gen_ai.usage.input_tokens`/`output_tokens` replaced the older prompt/completion names, `gen_ai.system` is deprecated for `gen_ai.provider.name`. Pin the spec version you emit and keep attribute emission in one module so renames are a one-file change. What the conventions buy is joinability: the same spans land in Jaeger, Grafana Tempo or a vendor's LLM view — the trajectory a scorer needs is the trace the SDK already wrote. Request-level histograms (module 1503) are the alert surface; the spans are the evidence.

## From Traces to Budgets

Traces become management numbers by rolling up — and the rollup is where a slow tool hides behind a fast model. Twenty traces, p50 **7,150 ms**, p95 **28,550 ms**, **7 of 20 breach** the 15-second budget, and attribution tells the story the averages hide: every breach is `execute_tool`-owned — t01 28,350 ms run with a 21,000 ms tool span (74%), t03 49,300 ms with **42,000 ms of tool time (85% — two slow-backend calls stacked)**, t15 23,850 ms with a 21,400 ms span (90%). Model calls cost under two seconds each, so no amount of prompt tuning fixes a run whose tool span ate the budget. The fix is attribution, and attribution is only possible because the spans separate `chat` from `execute_tool` — collapse them into one latency number and the budget report blames the model. Cost rolls up the same way from `gen_ai.usage.*` tokens × unit prices; per-run cost is a first-class regression metric alongside success rate, because an agent that improves quality by tripling its tool calls has regressed.

## The Regression Gate: Two Tripwires

The gate turns evaluation from a report into the thing that blocks a merge — and one rule is not enough:

| Tripwire | Rule | This candidate |
|---|---|---|
| aggregate | pass rate may not drop more than 5 pp | 85% → 75% (-10 pp) — **FIRES** |
| golden set | a must-never-regress task may not flip | t02 flipped — **FIRES** |

The aggregate rule tolerates small churn but would sleep through a targeted break: a candidate could lose two points entirely inside the golden set and stay under any threshold, so the golden rule closes that hole — t02's single flip fails the gate regardless of totals. Both rules are cheap, deterministic, and readable in a PR comment, which is what makes agents CI-able at all. The honest caveat is variance: pin sampling parameters (or score pass@k over repeats) before letting a five-point threshold gate merges — a gate that fails on noise gets deleted within a week.

## One Run, the Whole Contract

```python
import json
import math
import random
import statistics

# ---- F1: rung-1 deterministic scorers over four recorded runs ----
RUNS = [
    {"task": "capital-fr", "answer": "The capital of France is Paris.",
     "expected": "Paris", "tools": ["search", "calculator"], "golden_tools": ["search"]},
    {"task": "sum-json", "answer": '{"result": 42}',
     "expected": '{"result": 42}', "tools": ["calculator"], "golden_tools": ["calculator"]},
    {"task": "weather-sf", "answer": "San Francisco is 62F and foggy.",
     "expected": "62F", "tools": ["search"], "golden_tools": ["search"]},
    {"task": "sum-short", "answer": "42",
     "expected": "42", "tools": [], "golden_tools": ["calculator"]},
]


def exact(run):
    return run["answer"].strip() == run["expected"]


def contains(run):
    return run["expected"] in run["answer"]


def json_result(run):
    try:
        data = json.loads(run["answer"])
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict) and "result" in data


def tools_match(run):
    return run["tools"] == run["golden_tools"]


SCORERS = {"exact": exact, "contains": contains,
           "json_result": json_result, "tools_match": tools_match}
for name, fn in SCORERS.items():
    passed = sum(fn(r) for r in RUNS)
    print(f"F1 {name:>12}: {passed}/{len(RUNS)}")
skip = next(r["task"] for r in RUNS if exact(r) and not tools_match(r))
print(f"F1 correct-answer-skipped-tools: {skip}")

# ---- F2: bootstrap CI on a small-sample success rate ----
random.seed(7)
OUTCOMES = [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1,
            1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1]  # 21 of 25 succeed

runs = []
for i, s in enumerate(OUTCOMES):
    steps = random.randint(3, 9)
    calls = random.randint(2, 6)
    ok = calls - (0 if s else random.randint(1, 2))
    runs.append((f"task-{i:02d}", bool(s), steps, calls, ok))

n = len(runs)
succ = [r[1] for r in runs]
rate = sum(succ) / n
mean_steps = statistics.mean(r[2] for r in runs)
tool_acc = sum(r[4] for r in runs) / sum(r[3] for r in runs)

BOOT = 1000
rates = []
for _ in range(BOOT):
    sample = [succ[random.randrange(n)] for _ in range(n)]
    rates.append(sum(sample) / n)
rates.sort()
lo, hi = rates[int(0.025 * BOOT)], rates[int(0.975 * BOOT)]
print(f"F2 runs={n} success={sum(succ)}/{n}={rate:.0%} "
      f"mean_steps={mean_steps:.1f} tool_acc={tool_acc:.0%}")
print(f"F2 bootstrap95CI=[{lo:.0%},{hi:.0%}] width={(hi - lo) * 100:.0f}pp")

# ---- F3: pairwise judge position bias and the swap cure ----
PRIMACY = 0.9   # judges over-score the answer shown first
GAP = 0.8       # A is truly better by 0.8 rubric points
A, B = 8.2, 7.4
print(f"F3 primacy={PRIMACY} true_gap={GAP} A={A} B={B}")
print("F3 fixed order, A first ->", "A" if A + PRIMACY > B else "B")
print("F3 fixed order, B first ->", "A" if A > B + PRIMACY else "B")

votes = []
for k in range(5):
    noise = random.Random(k).uniform(-0.3, 0.3)
    votes.append("A" if A + PRIMACY + noise >= B + noise else "B")
print("F3 5 judges, A first ->", f"A:{votes.count('A')} B:{votes.count('B')}")

votes = []
for k in range(5):
    noise = random.Random(k).uniform(-0.3, 0.3)
    votes.append("A" if A + noise >= B + PRIMACY + noise else "B")
print("F3 5 judges, B first ->", f"A:{votes.count('A')} B:{votes.count('B')}")

margin, comparisons = 0.0, 0
for k in range(7):
    n1 = random.Random(50 + k).uniform(-0.3, 0.3)
    n2 = random.Random(100 + k).uniform(-0.3, 0.3)
    margin += (A + n1) - (B + PRIMACY + n2)   # B shown first
    margin += (A + PRIMACY + n2) - (B + n1)   # A shown first, same two draws swapped
    comparisons += 2
print(f"F3 swap-averaged {comparisons} comparisons -> {margin / comparisons:+.2f} "
      f"winner {'A' if margin > 0 else 'B'}")

# ---- F4: traces to budgets, with per-operation attribution ----
random.seed(3)
PRICE_IN, PRICE_OUT = 0.15 / 1e6, 0.60 / 1e6   # $ per token
BUDGET_MS = 15000

traces = []
for tid in range(20):
    ms, tok, cost, tool_ms = 0, 0, 0.0, 0
    for _step in range(random.randint(2, 6)):
        it, ot = random.randrange(400, 1600, 10), random.randrange(40, 200, 10)
        tok += it + ot
        cost += it * PRICE_IN + ot * PRICE_OUT
        chat_ms = random.randrange(700, 1800, 50)
        ms += chat_ms
        if random.random() < 0.3:                    # execute_tool span
            slow = random.choice([400, 900, 21000])  # one slow backend lurks
            ms += slow
            tool_ms += slow
    traces.append((f"t{tid:02d}", ms, tok, round(cost, 5), tool_ms))

durs = sorted(t[1] for t in traces)


def pctl(xs, q):
    return xs[max(1, math.ceil(q * len(xs))) - 1]    # nearest-rank percentile


print(f"F4 p50={pctl(durs, 0.50)}ms p95={pctl(durs, 0.95)}ms budget={BUDGET_MS}ms")
breaches = [t for t in traces if t[1] > BUDGET_MS]
print(f"F4 over_budget={len(breaches)}/20")
for tid, ms, tok, cost, tool_ms in breaches:
    share = tool_ms / ms
    print(f"F4 {tid} {ms}ms ${cost:.4f} tool_span={tool_ms}ms ({share:.0%} of run)")
worst = max(breaches, key=lambda t: t[4]) if breaches else None
if worst:
    print(f"F4 worst_tool_span={worst[4]}ms on {worst[0]} "
          f"({worst[4] / worst[1]:.0%} of its {worst[1]}ms run)")

# ---- F5: the two-tripwire regression gate ----
BASELINE = {"t01": 1, "t02": 1, "t03": 0, "t04": 1, "t05": 1, "t06": 1, "t07": 0,
            "t08": 1, "t09": 1, "t10": 1, "t11": 1, "t12": 1, "t13": 0, "t14": 1,
            "t15": 1, "t16": 1, "t17": 1, "t18": 1, "t19": 1, "t20": 1}
CANDIDATE = {"t01": 1, "t02": 0, "t03": 0, "t04": 1, "t05": 1, "t06": 1, "t07": 0,
             "t08": 1, "t09": 1, "t10": 1, "t11": 1, "t12": 1, "t13": 0, "t14": 1,
             "t15": 1, "t16": 1, "t17": 1, "t18": 0, "t19": 1, "t20": 1}
GOLDEN = ["t02", "t09", "t14"]     # must-never-regress tasks
MAX_DROP_PP = 5                    # fail if the pass rate drops more than 5 points

rb = sum(BASELINE.values()) / len(BASELINE)
rc = sum(CANDIDATE.values()) / len(CANDIDATE)
regressed = [t for t in BASELINE if BASELINE[t] and not CANDIDATE[t]]
golden_hits = [t for t in regressed if t in GOLDEN]

print(f"F5 pass_rate {rb:.0%} -> {rc:.0%} ({(rc - rb) * 100:+.0f}pp) max_drop={MAX_DROP_PP}pp")
print("F5 regressed:", ", ".join(regressed) or "none")
print("F5 golden_regressed:", ", ".join(golden_hits) or "none")
ok = (rb - rc) * 100 <= MAX_DROP_PP and not golden_hits
agg = (rb - rc) * 100 <= MAX_DROP_PP
print(f"F5 tripwire aggregate={'FIRE' if not agg else 'hold'} "
      f"golden={'FIRE' if golden_hits else 'hold'} gate={'PASS' if ok else 'FAIL'}")
```

**Output:**

```text
F1        exact: 2/4
F1     contains: 4/4
F1  json_result: 1/4
F1  tools_match: 2/4
F1 correct-answer-skipped-tools: sum-short
F2 runs=25 success=21/25=84% mean_steps=4.7 tool_acc=94%
F2 bootstrap95CI=[68%,96%] width=28pp
F3 primacy=0.9 true_gap=0.8 A=8.2 B=7.4
F3 fixed order, A first -> A
F3 fixed order, B first -> B
F3 5 judges, A first -> A:5 B:0
F3 5 judges, B first -> A:0 B:5
F3 swap-averaged 14 comparisons -> +0.80 winner A
F4 p50=7150ms p95=28550ms budget=15000ms
F4 over_budget=7/20
F4 t01 28350ms $0.0010 tool_span=21000ms (74% of run)
F4 t03 49300ms $0.0014 tool_span=42000ms (85% of run)
F4 t04 27350ms $0.0011 tool_span=22300ms (82% of run)
F4 t11 24950ms $0.0005 tool_span=21000ms (84% of run)
F4 t13 28550ms $0.0014 tool_span=21000ms (74% of run)
F4 t15 23850ms $0.0005 tool_span=21400ms (90% of run)
F4 t19 28500ms $0.0013 tool_span=21400ms (75% of run)
F4 worst_tool_span=42000ms on t03 (85% of its 49300ms run)
F5 pass_rate 85% -> 75% (-10pp) max_drop=5pp
F5 regressed: t02, t18
F5 golden_regressed: t02
F5 tripwire aggregate=FIRE golden=FIRE gate=FAIL
```

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| "84% success" reported with no interval | n=25 point estimates carry ~28-point CIs; deltas inside the interval are noise | bootstrap the runs; report the interval next to every rate |
| the judge flips verdicts when answers swap | primacy bias larger than the true quality gap | randomize order, score both orders, swap-average; flag self-disagreeing judges |
| judge votes unanimous but wrong | shared bias looks like agreement; biased agreement is not evidence | vary judge model/order; validate against a small human-labeled set first |
| `contains` passes keyword-stuffed wrong answers | surface matching credits any answer containing the expected text | anchor scorers to task invariants (schema keys, tool sequences), not substrings |
| the budget report blames the model | rollups merge `chat` and `execute_tool` latency | roll up per operation name; attribute the breach to its span |
| the gate flakes on identical code | unpinned temperature/seeds move pass rates between runs | pin sampling params or score pass@k over repeats |

## Quick Reference For

- [Module 7104: Agent Evaluation and Observability](../../phases/phase7-agentic/7100-architecture/7104-Agent-Evaluation-and-Observability.md)
- [Module 1503: LLM Observability](../../phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md)
- [Module 7201: Tool Calling](../../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md)
- [CHEAT-SHEET-011: Evaluation Benchmarking](./CHEAT-SHEET-011-Evaluation-Benchmarking.md)
