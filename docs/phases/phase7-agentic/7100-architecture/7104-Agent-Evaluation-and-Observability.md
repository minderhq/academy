---
Document ID: 7104
Title: "7104: Agent Evaluation and Observability - Measuring the Loop as Working Code"
Phase: 7
Module: 7100
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Tags: ['agents', 'evaluation', 'observability', 'benchmarks']
---

# 7104: Agent Evaluation and Observability - Measuring the Loop as Working Code

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Evaluation Ladder](#the-evaluation-ladder)
- [Trajectories as Data](#trajectories-as-data)
- [Deterministic Scorers](#deterministic-scorers)
- [Trajectory Metrics and Confidence](#trajectory-metrics-and-confidence)
- [The Judge: LLM-as-Judge Mechanics](#the-judge-llm-as-judge-mechanics)
- [Observability: The Trace Schema](#observability-the-trace-schema)
- [From Traces to Budgets](#from-traces-to-budgets)
- [Regression Gates in CI](#regression-gates-in-ci)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After reading this lesson, you will be able to:

- Place a scoring method on the three-rung evaluation ladder - deterministic checks, programmatic scorers, LLM-as-judge - and say what each rung can and cannot catch
- Record an agent run as a trajectory (task, tool calls, final answer) and score it with exact-match, containment, schema, and tool-sequence scorers
- Put a bootstrap confidence interval on a small-sample success rate instead of quoting a point estimate
- Demonstrate pairwise position bias with arithmetic, detect it by running both orders, and cancel it by swap-averaging
- Emit agent traces carrying the OpenTelemetry GenAI semantic conventions (`invoke_agent`, `chat`, `execute_tool` spans with `gen_ai.*` attributes)
- Roll traces into per-run latency and cost budgets and gate CI on a regression rule with a golden set

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)

## Abstract

[7101](./7101-ReAct-Loop-System.md) built the loop; [7102](./7102-Planning-Decomposition.md) built the planner. Both ship without an answer to the question that decides whether they ship at all: is this agent good, and did yesterday's change make it worse? [1503](../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) taught request-level metrics - TTFT, tokens, cost per call - but an agent's unit of work is not a request, it is a **trajectory**: a sequence of model calls, tool calls, and intermediate state that ends in one verdict. This lesson makes trajectories measurable end to end. You will score recorded runs at three heights of the evaluation ladder, put confidence intervals on the small samples every agent team actually has, watch a pairwise judge flip its verdict on answer order alone and fix it with swap-averaging, emit traces in the OpenTelemetry GenAI conventions the industry is converging on, roll them into latency and cost budgets, and close with a regression gate that fails CI when the golden set moves.

## The Evaluation Ladder

Every scoring method lives on one of three rungs, and the rung decides the failure mode:

| Rung | Example | Catches | Misses | Cost |
|------|---------|---------|--------|------|
| 1 - deterministic | exact match, JSON schema, tool sequence | factual drift, format breaks, wasted calls | anything phrased differently but correct | free, reproducible |
| 2 - programmatic | rubric sums over extracted features, distance metrics | graded quality on measurable axes | properties you cannot extract | cheap, reproducible |
| 3 - LLM-as-judge | rubric prompt, pairwise comparison | fuzzy correctness, tone, reasoning quality | depends on the judge: bias, variance, self-preference | paid, noisy |

The ladder is climbed only as far as needed. A tool-sequence check catches the wasted `calculator` call that no judge would flag; a judge catches the subtly wrong itinerary that no string comparison would catch. Production suites run rungs 1 and 2 on every run and rung 3 on a sample - the judge is the expensive, noisy end of the pipeline, not the default.

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

The schema is deliberately boring: what was attempted, what tools fired and in what order, what came out, and - for labeled sets - whether a human grader called it a success. Two disciplines follow from the format. First, **record everything now, score later**: storage is cheap, re-running an agent on the same inputs is not (non-determinism and live services guarantee drift). Second, keep a **golden set**: a small, hand-labeled subset of tasks that must never regress, versioned alongside the agent itself.

The lesson's runnable fences work on in-memory fixtures standing in for that JSONL, so the arithmetic is reproducible without any live agent.

## Deterministic Scorers

Rung 1 is where discipline pays. Four scorers over four recorded runs:

```python
import json

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
    print(f"{name:>12}: {passed}/{len(RUNS)}")
```

Read the columns against each other. `contains` passes 4/4 - it over-credits, because the expected string sits inside answers of any quality; surface-string matching is a smoke test, not a scorer. `exact` passes 2/4 and under-credits correct-but-verbose answers. The interesting pair is `sum-short`: the answer `"42"` is right, but the run fired **no** tools where the golden trajectory requires `calculator` - `tools_match` fails it, and that is the point. Tool-sequence scoring grades *how* the agent worked, the axis string scorers cannot see. It is also the cheapest regression tripwire you own: a prompt change that breaks tool selection shows up here before any human ever reads an output.

## Trajectory Metrics and Confidence

Aggregate the per-run verdicts and the temptation appears: report "84% success". The fence below refuses the point estimate:

```python
import random
import statistics

random.seed(7)
# 25 recorded runs: (task, success, steps, tool_calls, correct_tool_calls)
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
print(f"runs: {n}  success: {sum(succ)}/{n} = {rate:.0%}")
print(f"mean steps: {mean_steps:.1f}   tool accuracy: {tool_acc:.0%}")
print(f"bootstrap 95% CI: [{lo:.0%}, {hi:.0%}]")
```

Twenty-five runs are what a real team has for a new agent version, and at that sample size the 95% confidence interval spans 68% to 96% - nearly thirty points wide. A candidate at 78% and a baseline at 88% are statistically the same agent. The bootstrap is ten lines: resample the runs with replacement a thousand times, recompute the rate, take the 2.5/97.5 percentiles. Any two-run comparison made without this interval is a decision made on noise. Step efficiency and tool accuracy deserve the same treatment when they drive a go/no-go call; the fence prints them so the report carries all three axes from the [module's own metrics table](./README.md#agent-evaluation-metrics).

## The Judge: LLM-as-Judge Mechanics

Rung 3 asks a second model to grade. The dominant format is **pairwise**: show the judge two answers, ask which is better. The fence implements the judge's bias structure - a primacy bonus for whichever answer is shown first - and demonstrates the three moves that make pairwise judging usable:

```python
import random

PRIMACY = 0.9   # judges over-score the answer shown first
GAP = 0.8       # A is truly better by 0.8 rubric points
A, B = 8.2, 7.4

print("fixed order, A first     ->", "A" if A + PRIMACY > B else "B")
print("fixed order, B first     ->", "A" if A > B + PRIMACY else "B")

votes = []
for k in range(5):
    noise = random.Random(k).uniform(-0.3, 0.3)
    votes.append("A" if A + PRIMACY + noise >= B + noise else "B")
print("5 judges, A shown first  ->", f"A:{votes.count('A')} B:{votes.count('B')}")

votes = []
for k in range(5):
    noise = random.Random(k).uniform(-0.3, 0.3)
    votes.append("A" if A + noise >= B + PRIMACY + noise else "B")
print("5 judges, B shown first  ->", f"A:{votes.count('A')} B:{votes.count('B')}")

margin, comparisons = 0.0, 0
for k in range(7):
    n1 = random.Random(50 + k).uniform(-0.3, 0.3)
    n2 = random.Random(100 + k).uniform(-0.3, 0.3)
    margin += (A + n1) - (B + PRIMACY + n2)   # B shown first
    margin += (A + PRIMACY + n2) - (B + n1)   # A shown first, same two draws swapped
    comparisons += 2
print(f"swap-averaged, {comparisons} comparisons -> {margin / comparisons:+.2f} points, "
      f"winner {'A' if margin > 0 else 'B'}")
```

Three results, one lesson each. The fixed-order pair **flips**: same answers, same judge, the verdict follows the presentation order, because the 0.9-point primacy bonus outweighs the 0.8-point true gap. The five-judge block shows why unanimity is not safety: shown A first the same five judges vote `A:5 B:0`, shown B first they vote `A:0 B:5` - the vote is the order, not the answers, so agreement between judges is not evidence when they share the bias. The swap-averaged margin lands at **+0.80 points per comparison**, exactly the A-minus-B gap: the bias is additive and order-symmetric, so scoring both orders and averaging cancels it, and reusing the same two noise draws in both orders (the paired design) keeps the variance from creeping back. The production rules fall out: **randomize or balance presentation order**, **report both orders**, and treat a judge that disagrees with itself across orders as broken. The canonical warning is Zheng et al.'s MT-Bench study - judge agreement with humans collapses on exactly the categories where order bias bites.

The fence's judge is a deterministic stand-in so the arithmetic is reproducible; a real judge is an API call with the same algebra underneath. Harnesses that ship this machinery - `deepeval`'s judge metrics, `inspect-ai`'s solver/scorer split, LangSmith's pairwise experiments, `promptfoo`'s assertions - all expose the same three knobs: rubric, order policy, and vote count.

## Observability: The Trace Schema

Evaluations are computed after the fact from records; observability is the discipline of writing those records *while the agent runs*. The OpenTelemetry GenAI semantic conventions define the span vocabulary - an agent run is an `invoke_agent` span containing `chat` spans (model calls) and `execute_tool` spans (tool calls), each carrying `gen_ai.*` attributes:

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
tracer = provider.get_tracer("agent-evals")

with tracer.start_as_current_span("invoke_agent", attributes={
    "gen_ai.agent.name": "research-agent",
    "gen_ai.agent.version": "1.4.0",
}) as agent:
    with tracer.start_as_current_span("chat", attributes={
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "openai",
        "gen_ai.request.model": "gpt-5-mini",
        "gen_ai.usage.input_tokens": 820,
        "gen_ai.usage.output_tokens": 64,
    }):
        pass  # one model call inside the loop
    with tracer.start_as_current_span("execute_tool", attributes={
        "gen_ai.operation.name": "execute_tool",
        "gen_ai.tool.name": "web_search",
        "gen_ai.tool.call.id": "call_01",
    }) as tool:
        tool.set_attribute("gen_ai.tool.call.result", "3 results")
    agent.set_attribute("gen_ai.usage.input_tokens", 820)
    agent.set_attribute("gen_ai.usage.output_tokens", 64)

print("trace emitted: invoke_agent -> chat + execute_tool")
```

> **Environment gap:** `opentelemetry-sdk` is an optional third-party package the QA environment does not install; this fence documents the install requirement (`pip install opentelemetry-sdk`) and is accepted as `ENV-GAP:opentelemetry` in the exec census.

The attribute names are the contract, and they are still moving: the conventions live in a dedicated repository at Development stability, `gen_ai.usage.input_tokens`/`output_tokens` replaced the older prompt/completion names, and `gen_ai.system` is deprecated in favor of `gen_ai.provider.name`. Pin the spec version you emit and validate on write - a trace missing its `gen_ai.usage.*` attributes produces rollups that are silently wrong, which is worse than no rollup. What the conventions buy is joinability: the same span names and attributes land in Jaeger, Grafana Tempo, or a vendor's LLM view, so the trajectory a scorer needs is the trace the SDK already wrote. [1503](../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) publishes request-level histograms to Prometheus; the GenAI spans are the tree those aggregates summarize - one is the alert surface, the other is the evidence.

## From Traces to Budgets

Traces become management numbers by rolling up - and the rollup is where a slow tool hides behind a fast model:

```python
import math
import random

random.seed(3)
PRICE_IN, PRICE_OUT = 0.15 / 1e6, 0.60 / 1e6   # $ per token
BUDGET_MS = 15000

traces = []
for tid in range(20):
    ms, tok, cost = 0, 0, 0.0
    for _step in range(random.randint(2, 6)):
        it, ot = random.randrange(400, 1600, 10), random.randrange(40, 200, 10)
        tok += it + ot
        cost += it * PRICE_IN + ot * PRICE_OUT
        ms += random.randrange(700, 1800, 50)
        if random.random() < 0.3:                    # execute_tool span
            ms += random.choice([400, 900, 21000])   # one slow backend lurks
    traces.append((f"t{tid:02d}", ms, tok, round(cost, 5)))

durs = sorted(t[1] for t in traces)


def pctl(xs, q):
    return xs[max(1, math.ceil(q * len(xs))) - 1]    # nearest-rank percentile


print(f"p50 {pctl(durs, 0.50)} ms   p95 {pctl(durs, 0.95)} ms")
for tid, ms, tok, cost in traces:
    if ms > BUDGET_MS:
        print(f"over budget: {tid}  {ms} ms  {tok} tok  ${cost:.4f}")
```

The percentiles are computed nearest-rank on the sorted durations; p95 of twenty runs is the nineteenth value, and it is the number users feel. Seven of the twenty runs breach the 15-second budget, and the breaches tell the story the averages hide: model calls cost under two seconds each, so no amount of prompt tuning fixes a run whose `execute_tool` span ate twenty-one seconds. The fix is attribution, and attribution is only possible because the spans separate `chat` from `execute_tool` - collapse them into one latency number and the budget report blames the model. Cost rolls up the same way from the `gen_ai.usage.*` token attributes multiplied by unit prices; per-run cost is a first-class regression metric alongside success rate, because an agent that improves quality by tripling its tool calls has regressed.

## Regression Gates in CI

The last fence turns evaluation from a report into a gate - the thing that blocks a merge:

```python
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

print(f"pass rate: {rb:.0%} -> {rc:.0%}  ({(rc - rb) * 100:+.0f} pp)")
print("regressed:", ", ".join(regressed) or "none")
print("golden regressed:", ", ".join(golden_hits) or "none")
ok = (rb - rc) * 100 <= MAX_DROP_PP and not golden_hits
print("gate:", "PASS" if ok else "FAIL")
```

Two tripwires, because one is not enough. The aggregate rule tolerates small churn but would sleep through a targeted break: this candidate loses ten points, so the first rule fires - but a candidate could lose two points entirely inside the golden set and stay under any aggregate threshold. The golden rule closes that hole: `t02` is a must-never-regress task, so its single flip fails the gate regardless of the totals. Both rules are cheap, deterministic, and readable in a PR comment, which is what makes agents CI-able at all. The honest caveat is variance: non-deterministic tasks flake, so pin sampling parameters (or score pass@k over repeated runs) before letting a five-point threshold gate merges - a gate that fails on noise gets deleted within a week.

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| "84% success" reported with no interval | point estimates at n=25 have ~20-point 95% CIs; two-run deltas inside the interval are noise | bootstrap the runs and report the interval next to every rate before comparing versions |
| pairwise judge flips verdicts when answers swap | primacy/position bias larger than the true quality gap | randomize or balance order, score both orders, and swap-average; flag judges that disagree with themselves |
| judge votes are unanimous but wrong | shared bias looks like agreement; agreement between biased judges is not evidence | vary judge model/order; validate the judge against a small human-labeled set before trusting it |
| `contains` scorer passes keyword-stuffed wrong answers | surface-string matching credits any answer containing the expected text | anchor rung-1 scorers to task-specific invariants (schema keys, tool sequences), not substrings |
| trace rollups silently understate cost/latency | `gen_ai.usage.*` attributes missing on some spans; post-processing fills gaps with zeros | set attributes at the SDK call site and validate the attribute schema on write; alert on spans missing required keys |
| `gen_ai.system` emits deprecation warnings | the attribute is deprecated for `gen_ai.provider.name`; the conventions moved to their own repo at Development stability | pin the spec version you emit; keep attribute emission in one module so renames are a one-file change |
| regression gate flakes on non-deterministic tasks | unpinned temperature/seeds make pass rates move between identical runs | pin sampling params, or score pass@k over repeats; a gate that fails on noise gets deleted within a week |
| golden set fails after an intentional prompt change | golden trajectories encode the old behavior, not just correctness | version the golden set with `gen_ai.agent.version`; update goldens in the same PR as the change, review the diff |
| budget report blames the model for slow runs | rollups merge `chat` and `execute_tool` latency into one number | roll up per operation name; attribute breaches to the span that caused them before optimizing anything |

## Summary

The loop from [7101](./7101-ReAct-Loop-System.md) becomes shippable when its runs become data: trajectories recorded as JSONL, scored on a ladder that spends deterministic checks freely and LLM judges sparingly. The fences turn the folk knowledge into arithmetic - `contains` over-credits 4/4 while the tool-sequence scorer catches the correct answer that skipped its calculator; 21/25 successes carry a 68-96% bootstrap interval that swallows most version-to-version deltas; a pairwise judge flips on answer order because a 0.9-point primacy bonus beats a 0.8-point real gap, and swap-averaging cancels the bias exactly. The OpenTelemetry GenAI conventions give the run a trace shape - `invoke_agent` over `chat` and `execute_tool` spans with `gen_ai.*` attributes - and the rollup turns traces into budgets where a 21-second tool span, not the model, owns the breach. The regression gate closes the loop: an aggregate threshold for churn and a golden set for targeted breaks, both deterministic enough to live in CI. [1503](../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) watches the requests; this lesson watches the work.

## References

### Related Minder Academy Documents

- [7101: ReAct Loop System](./7101-ReAct-Loop-System.md) - the loop whose runs this lesson scores
- [7102: Planning and Decomposition](./7102-Planning-Decomposition.md) - plan quality is a trajectory property, scored step-wise
- [7201: Tool Calling](../7200-tools/7201-Tool-Calling.md) - the tool-accuracy scorer's subject matter
- [7301: Orchestration](../7300-orchestration/7301-Orchestration.md) - nightly evals over orchestration variants
- [1503: LLM Observability](../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) - request-level metrics; the aggregates these traces explain
- [2403: Evaluation Frameworks](../../phase2-foundations/2400-pretraining/2403-Evaluation-Frameworks.md) - pretraining-era benchmark batteries; the ladder's ancestor

### Primary Sources

- OpenTelemetry GenAI semantic conventions (`github.com/open-telemetry/semantic-conventions-genai`) - Development-stability registry: `gen_ai.operation.name` (`chat`, `execute_tool`, `invoke_agent`), `gen_ai.provider.name`, `gen_ai.usage.input_tokens`/`output_tokens`, `gen_ai.tool.*`, `gen_ai.agent.*`.
- Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (NeurIPS 2023) - position bias and the swap-augmentation cure, with human-agreement data.
- `deepeval` (PyPI 4.2.8) - judge-based metrics including agent/trajectory evaluation.
- `inspect-ai` (PyPI 0.3.276, UK AI Safety Institute) - task/solver/scorer harness for agent evals.
- LangSmith documentation - datasets, experiments, and pairwise comparison for regression suites.
- `promptfoo` - CLI eval harness with deterministic assertions and model-graded checks.

---

## Next Steps

- Next Module: **[7200: Tool Calling and Function Execution](../7200-tools/README.md)**
- Continue with: **[7201: Tool Calling](../7200-tools/7201-Tool-Calling.md)** - the tool axis your scorer grades
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Reproduce the gate on your own runs: record ten trajectories of your agent, add one golden task, wire the two-tripwire gate into CI, then change a prompt on purpose and watch which rule catches it first.
