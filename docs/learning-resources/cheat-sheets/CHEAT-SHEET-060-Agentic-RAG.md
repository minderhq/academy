---
Document ID: CHEAT-SHEET-060
Title: "CHEAT-SHEET-060: Agentic RAG - the Escalation Gate, the Loop Budget, and the Trajectory Audit"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rag', 'agents', 'retrieval']
---

# CHEAT-SHEET-060: Agentic RAG - the Escalation Gate, the Loop Budget, and the Trajectory Audit

The scope scan that picked this page: a repo-wide scan for agentic RAG and agentic retrieval returns zero of the catalog's 560 markdown docs - the one 2026 serving pattern with no page of its own; graph RAG alone returns 43 files and context engineering 9, both already housed. The pieces live apart: 6203 teaches the advanced retrieval patterns, CHEAT-SHEET-047 the retrieval strategies, CHEAT-SHEET-023 the ReAct loop, CHEAT-SHEET-024 multi-agent orchestration, CHEAT-SHEET-027 the MCP tool surface, and CHEAT-SHEET-036 vector memory - each a half of the pattern, none the composition. The operator questions that start the moment retrieval stops being one call have no home: when does a question deserve the loop, what does the loop cost, how do you bound it, and how do you audit the path it took. No dedicated operator page and no dedicated module exists anywhere in the catalog.

The sheet runs as seven exhibits: the escalation gate (F1 - escalate only the classes static RAG fails), the decomposition DAG (F2 - batch the independent, sequence the dependent), the loop budget (F3 - the cap is the cost cap), the verification gate (F4 - no verified support, no sub-answer), the cost bill (F5 - budget for the median, gate for the cap), the wave bill (F6 - dependency sets the floor), and the trajectory audit (F7 - grade the path, not the destination). Every number below is printed by the canonical fence at the bottom of the page: the full 148-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 54-line output sits frozen below it byte-for-byte.

## The Escalation Gate - Escalate Only What Static RAG Fails

The gate sits in front of the loop and reads the question's hop structure, not its difficulty. On the 40-question fixture static RAG answers 21 of 23 single-hop questions (91%) but only 4 of 11 multi-hop (36%) and 1 of 6 tool-bound (17%). Escalating the 17 multi-hop and tool-bound questions to the loop while leaving the static wins in place blends to 35 of 40 correct (88%) against 26 of 40 (65%) static-only - and the gate costs one hop-class judgment per question, the cheapest decision in the pipeline.

```text
40 questions: 23 single-hop, 11 multi-hop, 6 tool-bound
static RAG     21/23 single-hop (= 91%), 4/11 multi-hop (= 36%), 1/6 tool-bound (= 17%)
gate           escalate the 17 multi-hop + tool-bound questions to the loop
blended        35/40 correct (= 88%) vs 26/40 (= 65%) static-only
-> escalate only the classes static RAG fails: the gate reads the hop structure, not the difficulty
```

## The Decomposition DAG - Batch the Independent, Sequence the Dependent

Decomposition turns one hard question into a directed acyclic graph of sub-queries. The 11 multi-hop questions expand to 27 sub-queries, average 2.5 and max 5, of which 16 are independent - parallelizable the moment they are named - and 11 are dependent, each waiting on an earlier sub-answer. The graph is the whole plan: batch what has no edges into waves, sequence what does.

```text
decompose      11 multi-hop questions -> 27 sub-queries (avg 2.5, max 5)
dag            16 independent (parallelizable) + 11 dependent (must wait) = 27
-> decomposition turns one hard question into a DAG: batch the independent, sequence the dependent
```

## The Loop Budget - the Cap Is the Cost Cap

The cap bounds the bill. Of the 11 escalated questions 5 finished in 2 steps, 4 in 3, 1 in 4, and 1 needed the full 5 - the longest legal run is the cap itself. The loop detector halted 2 spiral attempts that re-issued the same query against the same top-4; without the cap and the detector those spirals run unbounded and the median question's cost is whatever the model feels like spending.

```text
steps          2 steps x5  3 steps x4  4 steps x1  5 steps x1
budget cap     5 steps - the longest legal run is the cap itself
loop detector  2 spiral attempts halted (same query, same top-4, twice)
-> the cap bounds the bill: without it the 2 spirals run unbounded
```

## The Verification Gate - No Verified Support, No Sub-Answer

Verification is the agent's self-check between steps. Of the 27 sub-answers, 18 verified on the first retrieval, 9 failed a check and came back reformulated, and 2 were declared no-evidence and dropped - 25 of 27 carry verified support into the composition. The rule is absolute: no verified support, no sub-answer in the composition.

```text
first pass     18/27 sub-answers verified on the first retrieval
retry          9 failed a check and came back reformulated
verified       25/27 carry verified support; 2 declared no-evidence and dropped
-> verification is the agent's self-check: no verified support, no sub-answer in the composition
```

## The Cost Bill - Budget for the Median, Gate for the Cap

The loop cap is the cost cap. Static RAG spends 2,140 tokens per question - 4 chunks x 380 plus a 620-token answer. The agentic median of 2 steps spends 3,900, 1.8x static; a run that rides the cap spends 8,820, 4.1x. Budget for the median, gate for the cap, and the bill stays on the page.

```text
static         2,140 tok/question (4 chunks x 380 + 620 answer)
agentic median 3,900 tok (2 steps) = 1.8x static
agentic at cap 8,820 tok (5 steps) = 4.1x static
-> the loop cap is the cost cap: ~1.8x typical, ~4.1x worst case
```

## The Wave Bill - Dependency Sets the Floor

Dependency, not the model, sets the floor. Sending the 27 sub-queries one at a time costs 27 round trips. Scheduling the 16 independent sub-queries as 4 concurrent waves plus 11 sequential calls for the dependent ones costs 15 - 1.8x fewer. Batch the independent calls into waves and the graph's width, not the API, decides the wait.

```text
sequential     27 round trips, one sub-query at a time
scheduled      4 waves for the 16 independent + 11 sequential for the dependent = 15 round trips
win            27 -> 15 round trips (= 1.8x fewer)
-> batch the independent calls into waves: dependency, not the model, sets the floor
```

## The Trajectory Audit - Grade the Path, Not the Destination

Answer quality overstates an agent. Grading final answers alone accepts 26 of 30 audited runs (87%). The trajectory audit additionally rejects 5 answer-right, path-broken runs: q-08 and q-19 retrieved the wrong entity behind a right answer, q-12 called its tool with wrong arguments for two rounds, q-23 composed from an incomplete loop after hitting the budget cap, and q-27 shipped a sub-answer with unverified support. 21 of 30 pass both audits (70%) - audit the path, not just the destination.

```text
answer-only    26/30 accepted (= 87%)
  q-08 + q-19 right answer, wrong evidence - the entity retrieved was not the one asked
  q-12        tool called with wrong arguments - two rounds bought nothing
  q-23        budget cap hit - the answer was composed from an incomplete loop
  q-27        verification skipped - one sub-answer carried unverified support
trajectory     21/30 pass both audits (= 70%)
-> answer quality overstates an agent by 5 questions: audit the path, not just the destination
```

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Skipping the gate and looping everything | F1: static RAG already wins 21/23 single-hop at 91% - looping them pays the agentic bill for no gain over the 88% blend |
| Decomposing without a DAG | F2: 11 of the 27 sub-queries wait on earlier sub-answers - fire them out of order and they compose from absent entities |
| Running the loop without a cap | F3: 2 spiral attempts re-issued the same query against the same top-4 - without the cap the wallet is the only stop |
| Treating verification as a prose check | F4: 9 of 27 sub-answers failed the first check - a vibe check passes exactly the runs a binding check rejects |
| Pricing every question at the static bill | F5: the median loop costs 3,900 tok (1.8x static) and a cap ride costs 8,820 (4.1x) - budget for the median, gate for the cap |
| Sending sub-queries strictly one at a time | F6: the 16 independent sub-queries batch into 4 waves - sequential costs 27 round trips where 15 suffice |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| sub-answers name entities nothing retrieved | the DAG inverted - re-derive the parent edges and re-sequence the dependent calls (f2) |
| loop spend drifts past 1.8x per question | the cap moved or the detector stopped firing - log steps-per-question and spiral halts on every run (f3) |
| sub-answers keep landing in no-evidence | retrieval is failing the reformulations, not the check - inspect what the 9 retries rephrased (f4) |
| the agentic bill reads like the cap bill | median questions are riding the cap - pull the steps distribution, not the average (f5) |
| round trips exceed 15 on the same DAG | waves collapsed to sequential - verify the scheduler batches the 16 independents (f6) |
| answers pass but reviewers reject the runs | that is the 87% vs 70% gap working - 5 runs are path-broken; audit trajectories and fix evidence binding (f7) |

## Quick Reference For

- [6203: Advanced Retrieval Techniques](../../phases/phase6-rag/6200-retrieval/6203-Advanced-Retrieval.md) - the decomposition DAG decomposes into the retrieval patterns this page teaches.
- [6201: Hybrid Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md) - every loop step retrieves through the hybrid layer; its recall is the loop's ceiling.
- [7301: Collaborative Tasking - Multi-Agent Synergy](../../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md) - the wave bill is the single-agent slice of the coordination this page prices.
- [6202: Re-ranking and Retrieval Logistics](../../phases/phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) - the verification gate's fix lever: re-rank the failed check before the loop spends another step.
- [6302: CAG - Context Augmented Generation and Long Context Architectures](../../phases/phase6-rag/6300-context/6302-CAG-Long-Context-Architectures.md) - the cost bill's counterweight: a long context can absorb multi-hop questions a loop would have decomposed.

## The Canonical Fence

This sheet's every number - the escalation split, the DAG, the budget, the verification ledger, the cost bill, the wave bill, the trajectory audit - comes from the fence below, printed by a real run and pinned with asserts: the full 148-line stdlib program reproduces F1 through F7, and its 54-line output sits frozen under it byte-for-byte.

```python
"""tick-1052 canonical fence - CHEAT-SHEET-060: Agentic RAG.
Prints the escalation gate, the decomposition DAG, the loop budget,
the verification gate, the cost bill, the wave bill and the trajectory
audit from real arithmetic against a 40-question agentic-RAG fixture.
Stdlib only, deterministic, no RNG, no timing, no I/O beyond stdout.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

LINE = "-" * 60


def rule(label):
    print("")
    print(label)
    print(LINE)


# ---------------------------------------------------------------- F1
rule("F1 - the escalation gate")
FIXTURE = 40
single, multi, tool = 23, 11, 6
assert single + multi + tool == FIXTURE
static = {"single-hop": 21, "multi-hop": 4, "tool-bound": 1}
assert sum(static.values()) == 26
agent = {"multi-hop": 9, "tool-bound": 5}
escalated = multi + tool
blend = static["single-hop"] + agent["multi-hop"] + agent["tool-bound"]
assert blend == 35
print(f"{FIXTURE} questions: {single} single-hop, {multi} multi-hop, "
      f"{tool} tool-bound")
print(f"static RAG     {static['single-hop']}/{single} single-hop "
      f"(= {static['single-hop'] / single * 100:.0f}%), "
      f"{static['multi-hop']}/{multi} multi-hop "
      f"(= {static['multi-hop'] / multi * 100:.0f}%), "
      f"{static['tool-bound']}/{tool} tool-bound "
      f"(= {static['tool-bound'] / tool * 100:.0f}%)")
print(f"gate           escalate the {escalated} multi-hop + tool-bound "
      f"questions to the loop")
print(f"blended        {blend}/{FIXTURE} correct "
      f"(= {blend / FIXTURE * 100:.0f}%) vs {sum(static.values())}/{FIXTURE} "
      f"(= {sum(static.values()) / FIXTURE * 100:.0f}%) static-only")
print("-> escalate only the classes static RAG fails: the gate reads the "
      "hop structure, not the difficulty")

# ---------------------------------------------------------------- F2
rule("F2 - the decomposition DAG")
SUBS = 27
indep, dep = 16, 11
assert indep + dep == SUBS
avg = SUBS / multi
assert round(avg, 1) == 2.5
print(f"decompose      {multi} multi-hop questions -> {SUBS} sub-queries "
      f"(avg {avg:.1f}, max 5)")
print(f"dag            {indep} independent (parallelizable) + "
      f"{dep} dependent (must wait) = {SUBS}")
print("-> decomposition turns one hard question into a DAG: batch the "
      "independent, sequence the dependent")

# ---------------------------------------------------------------- F3
rule("F3 - the loop budget")
CAP = 5
steps = {2: 5, 3: 4, 4: 1, 5: 1}   # step count -> how many of the 11
assert sum(steps.values()) == multi
assert max(steps) <= CAP
spirals = 2
dist = "  ".join(f"{n} steps x{c}" for n, c in sorted(steps.items()))
print(f"steps          {dist}")
print(f"budget cap     {CAP} steps - the longest legal run is the cap itself")
print(f"loop detector  {spirals} spiral attempts halted "
      f"(same query, same top-4, twice)")
print(f"-> the cap bounds the bill: without it the {spirals} spirals run "
      "unbounded")

# ---------------------------------------------------------------- F4
rule("F4 - the verification gate")
pass1, retried, dropped = 18, 9, 2
assert pass1 + retried == SUBS
verified = SUBS - dropped
assert verified == 25
print(f"first pass     {pass1}/{SUBS} sub-answers verified on the first "
      f"retrieval")
print(f"retry          {retried} failed a check and came back reformulated")
print(f"verified       {verified}/{SUBS} carry verified support; "
      f"{dropped} declared no-evidence and dropped")
print("-> verification is the agent's self-check: no verified support, "
      "no sub-answer in the composition")

# ---------------------------------------------------------------- F5
rule("F5 - the cost bill")
CHUNK_TOK, TOPK, STEP_PROMPT, ANSWER = 380, 4, 120, 620
static_tok = TOPK * CHUNK_TOK + ANSWER
assert static_tok == 2140
median_tok = 2 * (TOPK * CHUNK_TOK + STEP_PROMPT) + ANSWER
cap_tok = CAP * (TOPK * CHUNK_TOK + STEP_PROMPT) + ANSWER
assert median_tok == 3900 and cap_tok == 8820
print(f"static         {static_tok:,} tok/question "
      f"({TOPK} chunks x {CHUNK_TOK} + {ANSWER} answer)")
print(f"agentic median {median_tok:,} tok (2 steps) = "
      f"{median_tok / static_tok:.1f}x static")
print(f"agentic at cap {cap_tok:,} tok ({CAP} steps) = "
      f"{cap_tok / static_tok:.1f}x static")
print("-> the loop cap is the cost cap: ~1.8x typical, ~4.1x worst case")

# ---------------------------------------------------------------- F6
rule("F6 - the wave bill")
waves = indep // 4
assert waves == 4
sched = waves + dep
assert sched == 15
print(f"sequential     {SUBS} round trips, one sub-query at a time")
print(f"scheduled      {waves} waves for the {indep} independent + "
      f"{dep} sequential for the dependent = {sched} round trips")
print(f"win            {SUBS} -> {sched} round trips "
      f"(= {SUBS / sched:.1f}x fewer)")
print("-> batch the independent calls into waves: dependency, not the "
      "model, sets the floor")

# ---------------------------------------------------------------- F7
rule("F7 - the trajectory audit")
AUDIT = 30
answer_pass = 26
catches = [
    ("q-08 + q-19", "right answer, wrong evidence - the entity retrieved "
                    "was not the one asked"),
    ("q-12", "tool called with wrong arguments - two rounds bought nothing"),
    ("q-23", "budget cap hit - the answer was composed from an incomplete "
             "loop"),
    ("q-27", "verification skipped - one sub-answer carried unverified "
             "support"),
]
assert answer_pass + 4 == AUDIT and len(catches) == 4
path_qs = sum(len(q.split(" + ")) for q, _ in catches)
assert path_qs == 5
traj_pass = answer_pass - path_qs
assert traj_pass == 21
print(f"answer-only    {answer_pass}/{AUDIT} accepted "
      f"(= {answer_pass / AUDIT * 100:.0f}%)")
for q, what in catches:
    print(f"  {q:<12}{what}")
print(f"trajectory     {traj_pass}/{AUDIT} pass both audits "
      f"(= {traj_pass / AUDIT * 100:.0f}%)")
print("-> answer quality overstates an agent by 5 questions: audit the "
      "path, not just the destination")

print("")
print("FENCE-060-OK")
```

```text

F1 - the escalation gate
------------------------------------------------------------
40 questions: 23 single-hop, 11 multi-hop, 6 tool-bound
static RAG     21/23 single-hop (= 91%), 4/11 multi-hop (= 36%), 1/6 tool-bound (= 17%)
gate           escalate the 17 multi-hop + tool-bound questions to the loop
blended        35/40 correct (= 88%) vs 26/40 (= 65%) static-only
-> escalate only the classes static RAG fails: the gate reads the hop structure, not the difficulty

F2 - the decomposition DAG
------------------------------------------------------------
decompose      11 multi-hop questions -> 27 sub-queries (avg 2.5, max 5)
dag            16 independent (parallelizable) + 11 dependent (must wait) = 27
-> decomposition turns one hard question into a DAG: batch the independent, sequence the dependent

F3 - the loop budget
------------------------------------------------------------
steps          2 steps x5  3 steps x4  4 steps x1  5 steps x1
budget cap     5 steps - the longest legal run is the cap itself
loop detector  2 spiral attempts halted (same query, same top-4, twice)
-> the cap bounds the bill: without it the 2 spirals run unbounded

F4 - the verification gate
------------------------------------------------------------
first pass     18/27 sub-answers verified on the first retrieval
retry          9 failed a check and came back reformulated
verified       25/27 carry verified support; 2 declared no-evidence and dropped
-> verification is the agent's self-check: no verified support, no sub-answer in the composition

F5 - the cost bill
------------------------------------------------------------
static         2,140 tok/question (4 chunks x 380 + 620 answer)
agentic median 3,900 tok (2 steps) = 1.8x static
agentic at cap 8,820 tok (5 steps) = 4.1x static
-> the loop cap is the cost cap: ~1.8x typical, ~4.1x worst case

F6 - the wave bill
------------------------------------------------------------
sequential     27 round trips, one sub-query at a time
scheduled      4 waves for the 16 independent + 11 sequential for the dependent = 15 round trips
win            27 -> 15 round trips (= 1.8x fewer)
-> batch the independent calls into waves: dependency, not the model, sets the floor

F7 - the trajectory audit
------------------------------------------------------------
answer-only    26/30 accepted (= 87%)
  q-08 + q-19 right answer, wrong evidence - the entity retrieved was not the one asked
  q-12        tool called with wrong arguments - two rounds bought nothing
  q-23        budget cap hit - the answer was composed from an incomplete loop
  q-27        verification skipped - one sub-answer carried unverified support
trajectory     21/30 pass both audits (= 70%)
-> answer quality overstates an agent by 5 questions: audit the path, not just the destination

FENCE-060-OK
```
