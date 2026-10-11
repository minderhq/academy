---
Document ID: CHEAT-SHEET-033
Title: "CHEAT-SHEET-033: LLM Observability"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'observability', 'monitoring', 'prometheus']
---

# CHEAT-SHEET-033: LLM Observability

**Quick Reference for:** the four LLM-specific metric families and their alert thresholds, the timing trio (TTFT, TPOT, decode rate) and the formula trap that inflates the decode rate 16.7x on long prompts, the Prometheus publishing guards that keep fake samples out of the histograms, the quality heuristics with their honest limits, the hallucination indicator ladder with its 0.4/0.7 confidence steps, the nearest-rank rule that keeps p95 from being p100 on small samples, and the seven-day cost rollup with its three levers. CHEAT-SHEET-011 owns model-level benchmarks; CHEAT-SHEET-028 owns agent-level evaluation - trajectories, judges, the regression gate; this sheet owns the request-level surface: an LLM endpoint that returns HTTP 200 can still be failing, because quality drift and cost drift are failures too. The closing rule: an endpoint is healthy only when latency, tokens, cost and quality are all measured - the metric you do not record is the failure you cannot see.

## The Four Metric Families

| family | headline metrics | alert when |
|---|---|---|
| performance | TTFT, TPOT, decode rate, end-to-end latency, queue wait | p95 latency > 5 s or decode < 10 tok/s |
| tokens | input, output, total, cache-hit tokens, context utilization | context utilization > 90% or cache hit < 50% |
| cost | per request, per 1K tokens, daily total, by model | daily cost spike, one model > 70% of spend |
| quality | relevance, repetition, refusal rate, safety triggers | drift against a golden baseline |

Generic HTTP metrics answer "is the server up"; these four answer "is the LLM feature working" - an LLM system fails in LLM-specific ways, so it needs LLM-specific metrics. Error rate > 5% closes the alert set.

```text
PERFORMANCE  ttft tpot decode-rate queue-wait   alert: p95>5s tps<10
TOKENS       input output cache-hit context    alert: util>90% hit<50%
COST         per-request per-1k daily by-model alert: spike 70%-dominance
QUALITY      relevance repetition refusal      alert: drift-vs-baseline
```

## The Timing Trio: TTFT, TPOT and the Decode-Rate Trap

| metric | canonical formula | the trap |
|---|---|---|
| TTFT | first-token time minus request start | a non-streaming request has none - see the guard below |
| TPOT | generation window times 1000 / output tokens | the window starts at the first token, not the request |
| decode rate | output tokens / generation window | `total_tokens / total_duration` folds prompt processing in |

One streamed request - 11 input words, 20 output words, first token at 420 ms, done at 2920 ms - lands TTFT `420.0 ms`, TPOT `125.0 ms`, decode rate `8.00 tok/s`, cost `$0.000355` at $0.005/1K in and $0.015/1K out. The trap quantified: a 3800-token prompt with 240 output tokens over a 12.0 s generation window decodes at a true `240/12.0s = 20.0 tok/s`, but `total_tokens / total_duration` reads `4040/12.1s = 333.88 tok/s` - **16.7x inflated**, because prompt processing is not decoding. And count tokens with the model's own tokenizer (`tiktoken` for OpenAI models): whitespace splitting undercounts, because a word is often more than one BPE token.

## Publishing to Prometheus: the TTFT=0.0 Guard

Wrap generation in a generator that timestamps the first chunk, then publish: request duration to a **Histogram** with a `status` label, TTFT to a **Histogram**, decode rate to a **Gauge**, tokens to a **Counter** with a `token_type` label, cost to a **Counter**. The guard: **never observe TTFT when it is `0.0`** - a non-streaming request has no first-token timestamp, and observing the zero pollutes the histogram with fake sub-ms samples. One streamed request carries p50 = `0.420 s`; a single observed `0.0` turns that p50 into `0.000 s`. Guard, then histogram.

## Quality Heuristics and their Honest Limits

| heuristic | canonical rule | honest limit |
|---|---|---|
| relevance | prompt-word overlap ratio | `3/11` on a real answer - the plural `hallucinations` misses the match; overlap is a smoke alarm, not a score |
| repetition | `1 - unique/total` word ratio | `0.8333` on a degenerate `the the the...` loop; flags the collapse, not its cause |
| refusal screen | substring match on refusal phrases | catches `i cannot help with`; phrasing variety beats any fixed list |
| expected similarity | `difflib.SequenceMatcher` ratio | exact ordering sensitivity; use against a golden set, not production |

## The Hallucination Ladder

| indicator | fires when | honest limit |
|---|---|---|
| high_uncertainty | more than 2 hedging phrases (`i think`, `maybe`, `possibly`) | hedging is also humility - a cautious correct answer trips it |
| specific_without_sources | `\d{4}` years, percentages, `according to` with no citation pattern | `[1]`, `(Author, Year)`, `source:` count as citations |
| unsupported_by_knowledge | no knowledge-base fact appears verbatim | substring check: **absence of evidence is not contradiction** |
| implausible_numbers | percent outside 0-100, year outside 1900-2030 | `\b` anchors keep `1000000` from being read as year `1000` |

The confidence ladder: 2+ indicators flags the response at `0.7`, one indicator scores `0.4` without flagging - but `unsupported_by_knowledge` flips the verdict **by itself**, it is not a vote. The ladder's boundary is the substring check: on the response `The capital of France is Paris, but the capital of Italy is Milan` the knowledge base finds its fact verbatim, zero indicators fire, and the Milan contradiction sails through - production verification needs semantic similarity or an NLI model. `150%` in `2050` with three hedging phrases lands all three list indicators at once: flagged, confidence `0.7`.

## Context Window: Overflow and the Nearest-Rank p95

`total_needed = prompt_tokens + max_tokens`; utilization is `total_needed / max_context` and overflow is the positive remainder - `7000 + 2000` against an 8192 window overflows by 808 tokens, and utilization above 90% is the alert. The statistics trap: the naive `int(n * 0.95)` percentile index returns the **maximum** for every n up to 20 - on the three requests with utilizations averaging `0.976562`, the naive index 2 reads `1.098633`, p100 masquerading as p95 - while the nearest-rank index `max(0, int(n * 0.95) - 1)` reads `0.976562`. **On small samples, the naive index always lands on the maximum; use nearest-rank.**

## The Seven-Day Cost Rollup and its Three Levers

Roll the request log up by model: total cost, cost per 1K tokens, and the input/output cost split. A four-request week - three on `frontend-large` averaging 6850 input tokens, one on `router-small` - lands `$0.1715` total at `$0.0057` per 1K, with `frontend-large` at 99.7% of spend, and two of the three levers fire:

| lever | fires when | savings band |
|---|---|---|
| prompt_optimization | average input > 5000 tokens | 20-30% - prompt caching or summarization |
| output_limiting | average output > 2000 tokens | 10-20% - set `max_tokens` deliberately |
| model_selection | one model > 70% of spend | 40-60% - smaller models for simple requests |

The dominant-model lever is the strongest and the least used: routing simple requests off the expensive model is where the money is.

## Known Failure Modes

| failure | lesson |
|---|---|
| Count tokens by whitespace | undercounts BPE tokens - use the model's tokenizer for billing-grade numbers |
| Read `total/duration` as decode rate | folds prompt processing in - `16.7x` inflated on long prompts |
| Observe a non-streaming TTFT `0.0` | one fake sample turns p50 `0.420 s` into `0.000 s` - guard on `> 0` |
| Treat the substring check as verification | absence of evidence is not contradiction - the Milan case sails through |
| Use the naive percentile index | `int(n * 0.95)` is the maximum for n up to 20 - nearest-rank |

## References

- Repository, *Module 1503: LLM Observability - LLM-specific metrics, cost and quality monitoring*
- Prometheus, *Metric Naming Best Practices* - the naming conventions behind the `llm_*` family
- OpenTelemetry, *GenAI Semantic Conventions* - the trace-side sibling of these request metrics
- openai, *tiktoken* - the tokenizer behind billing-grade token counts

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Users wait but TPS looks great | `total/duration` folds the prompt in | decode rate = output tokens over the generation window |
| TTFT p50 collapsed to zero | non-streaming `0.0` observed | skip the observe unless `ttft > 0` |
| Fabricated numbers pass the screen | implausible check too narrow | percent and year anchors - `150%`, `2050` both fire |
| A contradiction sails through | knowledge-base substring saw the true half | semantic similarity or an NLI model, not substring matching |
| p95 equals the max | naive index on 20 samples or fewer | nearest-rank index `max(0, int(n * 0.95) - 1)` |
| One model owns the bill | no routing for simple requests | the 70%-dominance lever - smaller models where quality allows |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 1503: LLM Observability](../../phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md) | this sheet's source module - the full metric classes with runnable code |
| [Module 1502: Model Drift Detection](../../phases/phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) | what to do when the quality family drifts |
| [Module 1501: Monitoring and Observability](../../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md) | the generic Prometheus/Grafana stack underneath these metrics |
| [CHEAT-SHEET-028: Agent Evaluation and Observability](CHEAT-SHEET-028-Agent-Evaluation-and-Observability.md) | the agent-level sibling - trajectories, judges, the regression gate |

```python
"""CHEAT-SHEET-033 canonical numbers - stdlib only, deterministic."""
import re
from dataclasses import dataclass


@dataclass
class Request:
    request_id: str
    model: str
    input_tokens: int
    output_tokens: int
    ttft_ms: float
    tpot_ms: float
    latency_ms: float
    cost: float


def record(request_id, model, pricing, n_in, n_out, t_start, t_first, t_end):
    latency_ms = (t_end - t_start) * 1000.0
    ttft_ms = (t_first - t_start) * 1000.0 if t_first is not None else 0.0
    gen = t_end - (t_first if t_first is not None else t_start)
    tpot_ms = (gen * 1000.0) / n_out if n_out > 0 else 0.0
    tps = n_out / gen if gen > 0 else 0.0
    cost = (n_in / 1000.0) * pricing["in"] + (n_out / 1000.0) * pricing["out"]
    return Request(request_id, model, n_in, n_out, ttft_ms, tpot_ms, latency_ms, cost), tps


# F1 - the timing trio on one streamed request
P_FL = {"in": 0.005, "out": 0.015}
m1, tps1 = record("r-001", "frontend-large", P_FL, 11, 20, 100.000, 100.420, 102.920)
assert abs(m1.ttft_ms - 420.0) < 1e-9 and abs(m1.tpot_ms - 125.0) < 1e-9
assert abs(tps1 - 8.0) < 1e-9 and abs(m1.latency_ms - 2920.0) < 1e-9
assert abs(m1.cost - 0.000355) < 1e-12
print("F1 streamed r-001: ttft=420.0ms tpot=125.0ms tps=8.00 latency=2920.0ms cost=$0.000355")
print("   whitespace token counts undercount: a word is often more than one BPE token")

# F2 - decode-rate trap: total/duration folds prompt processing into TPS
assert len(("doc section " * 1900).split()) == 3800
m2, tps_true = record("r-002", "frontend-large", P_FL, 3800, 240, 200.000, 200.100, 212.100)
tps_naive = 4040 / 12.1
assert abs(tps_true - 20.0) < 1e-9 and abs(m2.latency_ms - 12100.0) < 1e-9
print(f"F2 decode rate: true output/gen = 240/12.0s = {tps_true:.1f} tok/s")
print(f"   naive total/duration = 4040/12.1s = {tps_naive:.2f} tok/s ({tps_naive / tps_true:.1f}x inflated)")

# F3 - the TTFT=0.0 histogram guard: one polluted sample destroys the p50
samples = [0.420]                            # one streamed request so far
clean_p50 = sorted(samples)[(len(samples) - 1) // 2]
samples.append(0.0)                          # the mistake: observing a non-stream 0.0
polluted_p50 = sorted(samples)[(len(samples) - 1) // 2]
assert clean_p50 == 0.420 and polluted_p50 == 0.0
print("F3 TTFT guard: skip the observe when ttft==0.0 (non-streaming has no first-token time)")
print(f"   streamed p50={clean_p50:.3f}s -> one fake 0.0 turns the p50 into {polluted_p50:.3f}s")

# F4 - quality heuristics: overlap relevance, repetition ratio, refusal screen
prompt = "what is retrieval augmented generation and why does it reduce hallucinations"
answer = "retrieval augmented generation grounds the model in retrieved documents so answers cite evidence instead of memorized facts reducing hallucination risk"
pw, rw = set(prompt.split()), set(answer.split())
rel = len(pw & rw) / len(pw)
words = "the the the the the the".split()
rep = 1 - len(set(words)) / len(words)
assert rel < 0.28 and rep > 0.83
refusal = "i cannot help with that request"
unsafe = any(p in refusal for p in ("i cannot help with", "i am not able"))
print(f"F4 quality: relevance={rel:.4f} (3/11 - plural 'hallucinations' missed by the overlap)")
print(f"   repetition_ratio={rep:.4f} (degenerate loop)  refusal detected: {unsafe}")


# F5 - hallucination ladder: 4 indicators, 0.4/0.7 confidence, substring limit
def hallucination(response, kb=()):
    low = response.lower()
    ind = []
    if sum(p in low for p in ("i think", "maybe", "possibly", "i believe")) > 2:
        ind.append("high_uncertainty")
    specific = any(re.search(p, low) for p in (r"\d{4}", r"\d+\.\d+%", "according to"))
    cited = any(re.search(p, low) for p in (r"\[\d+\]", r"\(\w+, \d{4}\)", "source:"))
    if specific and not cited:
        ind.append("specific_without_sources")
    for fact in kb:
        if fact.lower() in low:
            break
    else:
        if kb:
            ind.append("unsupported_by_knowledge")
    for pct in re.findall(r"\d+\.?\d*%", response):
        if not 0 <= float(pct[:-1]) <= 100:
            ind.append("implausible_numbers")
            break
    else:
        for year in re.findall(r"\b\d{4}\b", response):
            if not 1900 <= int(year) <= 2030:
                ind.append("implausible_numbers")
                break
    flags = len(ind)
    verdict = "unsupported_by_knowledge" in ind or flags >= 2
    return ind, verdict, 0.7 if flags >= 2 else (0.4 if flags == 1 else 0.0)


ia, ha, ca = hallucination("I think maybe possibly the study reported a 150% improvement in 2050")
assert ia == ["high_uncertainty", "specific_without_sources", "implausible_numbers"] and ca == 0.7 and ha
ib, hb, cb = hallucination("According to the 2019 study, accuracy improved by 8%")
assert ib == ["specific_without_sources"] and cb == 0.4 and not hb
KB = ["the capital of France is Paris"]
ic, hc, _ = hallucination("The capital of France is Paris, but the capital of Italy is Milan", KB)
assert ic == [] and not hc          # the substring saw the TRUE half - Milan sails through
idn, hd, _ = hallucination("The capital of France is Lyon", KB)
assert idn == ["unsupported_by_knowledge"] and hd
print("F5 hallucination: A 3 indicators conf=0.7 flag / B 1 indicator conf=0.4 no flag")
print("   C 'Milan' contradiction: 0 indicators (the substring saw the true half only)")
print("   D unsupported_by_knowledge alone flips the verdict - it is not a vote")


# F6 - context window + nearest-rank p95 (naive index is the maximum for n <= 20)
MAXCTX = 8192
utils = [(p + mx) / MAXCTX for p, mx in ((7000, 1000), (7000, 2000), (6000, 1000))]
overflow = sum(1 for p, mx in ((7000, 1000), (7000, 2000), (6000, 1000)) if p + mx > MAXCTX)
srt = sorted(utils)
naive_idx = int(len(utils) * 0.95)
rank_idx = max(0, naive_idx - 1)
assert srt[naive_idx] == max(utils) and abs(srt[rank_idx] - 8000 / MAXCTX) < 1e-9
assert overflow == 1
for n in (5, 10, 15, 20):
    assert int(n * 0.95) == n - 1          # always lands on the maximum
print(f"F6 context: avg={sum(utils) / 3:.6f} max={max(utils):.6f} overflows={overflow}")
print(f"   p95 nearest-rank={srt[rank_idx]:.6f} vs naive index {naive_idx} -> {srt[naive_idx]:.6f} = p100")
print("   for n in 5/10/15/20 the naive int(n*0.95) index is always n-1: the maximum")


# F7 - cost levers: 7-day rollup, dominant-model and long-prompt rules
ROWS = [("frontend-large", 9000, 800), ("frontend-large", 9200, 900),
        ("frontend-large", 8800, 700), ("router-small", 400, 150)]
PRICE = {"frontend-large": P_FL, "router-small": {"in": 0.0005, "out": 0.002}}
costs = {k: 0.0 for k in PRICE}
tin = tout = 0
for mod_, i_tok, o_tok in ROWS:
    costs[mod_] += (i_tok / 1000.0) * PRICE[mod_]["in"] + (o_tok / 1000.0) * PRICE[mod_]["out"]
    tin += i_tok
    tout += o_tok
total = sum(costs.values())
per_1k = total / (tin + tout) * 1000
share = costs["frontend-large"] / total
top = max(costs, key=costs.get)
levers = []
if tin / len(ROWS) > 5000:
    levers.append(("prompt_optimization", "20-30%"))
if tout / len(ROWS) > 2000:
    levers.append(("output_limiting", "10-20%"))
if costs[top] > total * 0.7:
    levers.append(("model_selection", "40-60%"))
assert abs(per_1k - 0.005726) < 1e-5 and share > 0.7
assert levers == [("prompt_optimization", "20-30%"), ("model_selection", "40-60%")]
print(f"F7 cost 7d: requests=4 total=${total:.4f} per_1k=${per_1k:.4f} {top} share={share:.1%}")
print(f"   levers fired: {levers}")
print("DETERMINISTIC-OK")
```

```text
F1 streamed r-001: ttft=420.0ms tpot=125.0ms tps=8.00 latency=2920.0ms cost=$0.000355
   whitespace token counts undercount: a word is often more than one BPE token
F2 decode rate: true output/gen = 240/12.0s = 20.0 tok/s
   naive total/duration = 4040/12.1s = 333.88 tok/s (16.7x inflated)
F3 TTFT guard: skip the observe when ttft==0.0 (non-streaming has no first-token time)
   streamed p50=0.420s -> one fake 0.0 turns the p50 into 0.000s
F4 quality: relevance=0.2727 (3/11 - plural 'hallucinations' missed by the overlap)
   repetition_ratio=0.8333 (degenerate loop)  refusal detected: True
F5 hallucination: A 3 indicators conf=0.7 flag / B 1 indicator conf=0.4 no flag
   C 'Milan' contradiction: 0 indicators (the substring saw the true half only)
   D unsupported_by_knowledge alone flips the verdict - it is not a vote
F6 context: avg=0.976562 max=1.098633 overflows=1
   p95 nearest-rank=0.976562 vs naive index 2 -> 1.098633 = p100
   for n in 5/10/15/20 the naive int(n*0.95) index is always n-1: the maximum
F7 cost 7d: requests=4 total=$0.1715 per_1k=$0.0057 frontend-large share=99.7%
   levers fired: [('prompt_optimization', '20-30%'), ('model_selection', '40-60%')]
DETERMINISTIC-OK
```
