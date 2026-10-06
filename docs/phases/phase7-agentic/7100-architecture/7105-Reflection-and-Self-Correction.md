---
Document ID: 7105
Title: "7105: Reflection and Self-Correction - The Loop That Grades Its Own Work"
Phase: 7
Module: 7100
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Tags: ['agents', 'reflection', 'self-correction', 'reasoning', 'cognition']
---

# 7105: Reflection and Self-Correction - The Loop That Grades Its Own Work

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Refine Loop: Critique That Sees](#the-refine-loop-critique-that-sees)
- [Self-Consistency: The Plurality Amplifier](#self-consistency-the-plurality-amplifier)
- [The Self-Correction Boundary: Intrinsic vs Informed](#the-self-correction-boundary-intrinsic-vs-informed)
- [The Retry Split: Bare, Injected, Carryover](#the-retry-split-bare-injected-carryover)
- [The Campaign: One Batch, Five Bills](#the-campaign-one-batch-five-bills)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After reading this lesson, you will be able to:

- Separate the three in-run self-improvement families - refine loops, self-consistency voting, and informed correction - and say what each family can and cannot buy
- Run the draft-critique-revise loop in detect-mode discipline and read its accuracy walk as a defect-class ledger - surface defects drained, logic defects holding their floor
- Show that a majority vote amplifies whichever mode is plural, right or wrong, and price the K-times decode multiplier that comes with it
- Recite the self-correction boundary from arithmetic: intrinsic rewrites decay accuracy, verifier-gated repairs climb it, and the whole difference is external information
- Split a retry budget three ways - bare, critique-injected, within-run carryover - and see where within-run knowledge runs out
- Price one 100-item batch under five policies and choose by the bill, not by the folklore

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)

## Abstract

[7101](./7101-ReAct-Loop-System.md) built the loop and gave it a mechanical retry; [7404](../7400-memory/7404-Reflective-Memory-and-Context-Paging.md) gave reflection a memory that persists across runs; [5205](../../phase5-finetuning/5200-alignment/5205-GRPO-RLVR.md) trains self-correction into a model's weights so it emerges at inference time. What no lesson has owned is the named in-run pattern family the module's own quiz admits is taught nowhere: the draft-critique-revise loop of Self-Refine, the sampled majority vote of self-consistency, and the tool-informed correction that CRITIC built - plus the boundary paper that keeps all three honest. This lesson makes each pattern runnable and prices each one's bill. The refine loop gains only where its critique can see; the vote amplifies whichever mode is plural, truth or error; a rewrite with no external information is a coin flip that decays accuracy; and the same 100-item batch under five policies lands anywhere from -0.160 to +0.192 depending entirely on whether the critique was allowed to see the defect before it rewrote the answer.

## The Refine Loop: Critique That Sees

Self-Refine (Madaan et al., arXiv 2303.17651) makes one model play all three roles - generator, feedback provider, refiner - and reports roughly 20% average absolute improvement across seven tasks, with no supervised training and no RL. The pattern is three prompts in a cycle: produce a draft, critique the draft, revise on the critique, repeat until a stop condition. The paper's own breadth is the tell: its seven tasks are dominated by open-ended generation and revision - dialogue responses, code optimization, document style - work where the defect is on the surface, inspectable by the same model that made it.

That is the mechanism this lesson's first fence isolates. Split the draft's defects into two classes: **surface defects** (a missing field, a broken format, a dangling reference - verifiable by looking at the output) and **logic defects** (a wrong sign, a dropped term - verifiable only by redoing the reasoning). A same-model critique sees surface defects well and logic defects poorly, and the loop's entire ledger follows from that asymmetry:

```python
import random

rng = random.Random(7)
N = 300
P_SURFACE = 0.22   # self-inspectable defect class (format, missing field)
P_LOGIC = 0.20     # reasoning defect class - same-model critique is near-blind
SEE_SURFACE = 0.80 # critique recall on the surface class
SEE_LOGIC = 0.15   # critique recall on the logic class
FIX = 0.90         # a seen defect is actually repaired
NEW_SURFACE = 0.05 # each revision can introduce a fresh surface defect

state = [
    {"surface": rng.random() < P_SURFACE, "logic": rng.random() < P_LOGIC}
    for _ in range(N)
]

def acc(st):
    return sum(1 for s in st if not (s["surface"] or s["logic"])) / len(st)

walk = [acc(state)]
print(f"iter 0 (draft): accuracy {walk[0]:.3f}")
for it in range(1, 5):
    fixed_s = fixed_l = new_s = 0
    for s in state:
        if s["surface"] and rng.random() < SEE_SURFACE and rng.random() < FIX:
            s["surface"] = False
            fixed_s += 1
        if s["logic"] and rng.random() < SEE_LOGIC and rng.random() < FIX:
            s["logic"] = False
            fixed_l += 1
        if rng.random() < NEW_SURFACE:
            s["surface"] = True
            new_s += 1
    walk.append(acc(state))
    print(f"iter {it}: accuracy {walk[-1]:.3f}  surface fixes {fixed_s:2d}  logic fixes {fixed_l:2d}  new surface defects {new_s}")
res_s = sum(1 for s in state if s["surface"])
res_l = sum(1 for s in state if s["logic"])
print(f"walk: {' -> '.join(f'{a:.3f}' for a in walk)}")
print(f"residual after 4 iterations: surface {res_s}, logic {res_l}")
```

The walk runs 0.590 -> 0.703 -> 0.777 -> 0.770 -> 0.833 - a +0.243 gain, but the ledger underneath it is lopsided: 139 surface fixes against 22 logic fixes across four iterations, and the residuals tell the same story - 17 surface defects left against 34 logic defects, the logic class barely dented from its 60-item start. The iter-3 dip to 0.770 is the loop's own revision churn: 22 fresh surface defects landed in that round against only 18 fixes, because every revision is a new chance to introduce what the loop is trying to remove. The final plateau at 0.833 is not the loop running out of turns - it is the critique's recall floor. More iterations grind against SEE_LOGIC = 0.15 and go nowhere; the walk plateaus exactly where the model's self-inspection ends.

Two production rules fall out. First, the stop criterion is the plateau: when the walk stops moving, stop iterating, because the remaining defects are the class the critique cannot see. Second, the discipline is detect-mode: revise only when the critique names a specific defect, never on a general sense that something is off - Section 3 prices the vibe-driven rewrite, and the price is negative.

## Self-Consistency: The Plurality Amplifier

Self-consistency (Wang et al., arXiv 2203.11171, ICLR 2023) replaces the single greedy path with k sampled reasoning paths and a majority vote over their final answers - and reports +17.9% on GSM8K, +11.0% on SVAMP, +12.2% on AQuA, +6.4% on StrategyQA, and +3.9% on ARC-challenge. The mechanism looks like magic and is actually an estimator: a model's sampled paths cluster into answer modes, and the vote converges on whichever mode carries the plurality of the probability mass. When the correct mode is plural, that convergence is the gain. When it is not, the vote is a precision instrument for being consistently wrong.

The fence runs both regimes side by side - one population where the correct answer carries 50% of the mass and two wrong modes split the rest, one where a wrong mode carries 45% and the correct answer carries 35%:

```python
import random
from collections import Counter

rng = random.Random(11)
ITEMS = 400

def vote_walk(masses, ks):
    out = []
    for K in ks:
        right = 0
        for _ in range(ITEMS):
            votes = Counter(rng.choices(range(len(masses)), weights=masses, k=K))
            if votes.most_common(1)[0][0] == 0:
                right += 1
        out.append(right / ITEMS)
    return out

GOOD = (0.50, 0.30, 0.20)  # correct mode is the plurality
BAD = (0.35, 0.50, 0.15)   # wrong mode A is the plurality
KS = [1, 5, 20, 100]
gw = vote_walk(GOOD, KS)
bw = vote_walk(BAD, KS)
print(f"correct-mode plurality {' -> '.join(f'{a:.3f}' for a in gw)}")
print(f"wrong-mode plurality  {' -> '.join(f'{a:.3f}' for a in bw)}")
print(f"K=100: vote {gw[-1]:.3f} vs {bw[-1]:.3f} - the vote converges to whichever mode is plural, truth or error")
```

Read the K=1 column first, because it calibrates everything: a single sampled path lands 0.490 and 0.340 - exactly the correct mode's mass in each regime, because one sample is a draw from the model's distribution and nothing more. The vote is a variance killer around that draw. In the good regime the walk climbs 0.490 -> 0.652 -> 0.815 -> 0.988: twenty samples all but guarantee the plurality speaks. In the bad regime the same machinery walks 0.340 -> 0.350 -> 0.242 -> 0.062 - downward, deliberately, converging on the wrong mode with 93.8% efficiency. The vote never consults the truth; it consults the distribution, and at K=100 it reports 0.988 versus 0.062 purely because of where the mass sat.

The module's own [practice exercise](./assessment/PRACTICE.md) demos self-consistency with a mock whose five paths all converge on "5" at 100% confidence - the degenerate case where the distribution is a spike. Real distributions have wrong modes, and the vote's confidence number (its vote share) measures the plurality, not the truth. The bill is also real: K paths cost K times the decode tokens, paid in full even on the items where the mode was already obviously plural. Vote where the correct mode is genuinely dominant - the GSM8K regime Wang et al. measured - and cap K where the budget cannot carry it.

## The Self-Correction Boundary: Intrinsic vs Informed

The boundary paper is Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet" (arXiv 2310.01798, ICLR 2024). Give GPT-4 a reasoning answer and a three-step prompt - answer, then "Assume that this answer could be either correct or incorrect. Review the answer carefully and report any serious problems you find.", then re-answer with no ground truth and no tool - and accuracy on GSM8K falls 95.5 to 91.5 to 89.0 across two self-correction rounds. GPT-3.5 falls more gently: 75.9 to 75.1 to 74.7. The rewrites are not repairs; they are coin flips, and because correct answers outnumber wrong ones, the coin flip costs the correct answers first.

Set that against CRITIC (Gou et al., arXiv 2305.11738, ICLR 2024), which gates every revision on tool output: a web search API for factual claims (top-1 page, ~400 characters, at most 7 interactions), a Python interpreter for math programs (at most 4 correction rounds), a toxicity scorer with a stop threshold. On GSM8K with program-of-thought, ChatGPT moves 72.5 to 78.2 with the full loop - and 72.5 to 77.0 even with the tools removed, because executing the program is itself an external signal. The tools-free gain is real exactly where execution can check the work, and marginal where it cannot: on open QA without tools the same framework manages -0.03 and +2.33 F1. Correction is an information problem, not a confidence problem.

The fence puts both curves in one arithmetic - a two-state Markov walk where intrinsic rewrites flip answers with no information, and gated repairs only fire on an external checker's flag:

```python
N = 400
acc0 = 0.730
P_CHANGE = 0.30   # per round, the hunt-mode prompt rewrites its answer
FLIP = 0.50       # a rewrite lands right/left with no information

a = acc0
intrinsic = [a]
for _ in range(2):
    a = a * (1 - P_CHANGE * FLIP) + (1 - a) * P_CHANGE * FLIP
    intrinsic.append(a)
print(f"intrinsic (no external feedback): {' -> '.join(f'{x:.3f}' for x in intrinsic)}")

P_FLAG_WRONG = 0.70  # the external checker's recall on wrong answers
P_FLAG_RIGHT = 0.10  # its false-positive rate on correct answers
REPAIR = 0.65        # flagged-wrong answers become right - the tool feedback carries the fix
KEEP = 0.90          # falsely flagged correct answers survive re-inspection

a = acc0
gated = [a]
flags_w_total = flags_r_total = repaired_total = dropped_total = 0
for _ in range(2):
    n_wrong = int(round((1 - a) * N))
    n_right = N - n_wrong
    fw = int(round(n_wrong * P_FLAG_WRONG))
    fr = int(round(n_right * P_FLAG_RIGHT))
    rep = int(round(fw * REPAIR))
    drop = fr - int(round(fr * KEEP))
    flags_w_total += fw
    flags_r_total += fr
    repaired_total += rep
    dropped_total += drop
    a = a * (1 - P_FLAG_RIGHT * (1 - KEEP)) + (1 - a) * P_FLAG_WRONG * REPAIR
    gated.append(a)
print(f"verifier-gated (tool feedback):   {' -> '.join(f'{x:.3f}' for x in gated)}")
print(f"two rounds: {flags_w_total} wrong answers flagged, {repaired_total} repaired; {flags_r_total} correct answers falsely flagged, {dropped_total} lost")
```

Same starting batch, opposite signs: intrinsic walks 0.730 -> 0.661 -> 0.613 while verifier-gated walks 0.730 -> 0.846 -> 0.907. The gated path pays real taxes the ledger makes visible - 63 correct answers falsely flagged across two rounds, 6 of them lost to the re-inspection - and still nets +0.177 where the intrinsic path loses 0.117. The flag counts are the mechanism: 119 wrong answers flagged and 77 repaired is external information doing work that the model's own confidence demonstrably cannot.

## The Retry Split: Bare, Injected, Carryover

[7101](./7101-ReAct-Loop-System.md)'s `RobustReActAgent` retries on failure, but its retry is mechanical - the same call, at the same odds, re-rolled. The [guide's extension exercise](./guides/7103-ReAct-Implementation-Guide.md) sketches a `SelfCorrectingAgent` with a `max_errors` cap; this fence is the mechanism that sketch abbreviates, priced three ways over one run of 200 tasks with up to three attempts each. The bare policy re-rolls at a flat rate. The injected policy critiques the failure and injects the named failure mode into the retry prompt. The carryover policy additionally lets modes surfaced by earlier tasks pre-warn later ones - the whole run's failure history, spent within the run:

```python
import random

rng = random.Random(31)
TASKS = 200
ATTEMPTS = 3
P_FIRST = 0.40
P_HINTED = 0.65  # a critique that NAMES the failure mode lifts the next attempt
P_PREWARN = 0.60 # a mode already surfaced earlier THIS run lifts the first attempt

def run_policy(policy):
    succ = 0
    attempts_used = 0
    second_total = second_ok = 0
    for task in range(TASKS):
        mode = rng.randrange(6)
        prewarn = policy == "carryover" and mode in seen_modes
        for attempt in range(ATTEMPTS):
            attempts_used += 1
            if attempt == 0:
                p = P_PREWARN if prewarn else P_FIRST
            else:
                p = P_HINTED if policy in ("injected", "carryover") else P_FIRST
            hit = rng.random() < p
            if attempt == 1:
                second_total += 1
                second_ok += hit
            if hit:
                succ += 1
                break
        seen_modes.add(mode)
    return succ, attempts_used, second_ok, second_total

for policy in ("bare", "injected", "carryover"):
    seen_modes = set()
    succ, used, s2ok, s2tot = run_policy(policy)
    cond = s2ok / s2tot if s2tot else 0.0
    print(f"{policy:9s}: {succ}/{TASKS} tasks succeeded, {used} attempts consumed, attempt-2 conditional accuracy {cond:.3f}")
```

Bare retry lands 159/200 tasks on 388 attempts, and its attempt-2 conditional accuracy is 0.379 - indistinguishable from its attempt-1 odds, because a bare retry carries no new information, it just spends another ticket on the same distribution. Injection lands 186/200 on 367 attempts with the attempt-2 conditional at 0.597: the named failure mode is the new information, and it lives entirely in the retry prompt. The carryover row is the boundary lesson: the same 186 successes on only 311 attempts. Within-run knowledge shows up as efficiency - 56 attempts saved - but never as ceiling, because a run can re-spend its own failure modes on the tasks that already failed and the pre-warned tasks that follow; the ceiling itself moves only when rules persist across runs. That persistence is [7404](../7400-memory/7404-Reflective-Memory-and-Context-Paging.md)'s half of reflexion: its episodic buffer walked 20% to 68% to 96% to 100% over 25 tasks by storing rules between tasks. This fence's ledgers all die at run end - and the run-local ceiling at 186/200 is exactly why the memory half exists.

## The Campaign: One Batch, Five Bills

One 100-item batch, draft accuracy 0.710, and the five policies this lesson has built - single-shot, intrinsic rewrites (hunt-mode, no external signal), detect-mode refinement, verifier-gated correction, and a 20-sample vote - priced on one ledger:

```python
import random
from collections import Counter

rng = random.Random(47)
N = 100
P_S, P_L = 0.22, 0.20
SEE_SURFACE, SEE_LOGIC, FIX, NEW_SURFACE = 0.80, 0.15, 0.90, 0.05
P_CHANGE, FLIP = 0.30, 0.50
P_FLAG_WRONG, P_FLAG_RIGHT, REPAIR, KEEP = 0.70, 0.10, 0.65, 0.90
GOOD = (0.50, 0.30, 0.20)
BAD = (0.35, 0.50, 0.15)

pop = [{"surface": rng.random() < P_S, "logic": rng.random() < P_L} for _ in range(N)]

def acc5(st):
    return sum(1 for s in st if not (s["surface"] or s["logic"])) / len(st)

draft = acc5(pop)
single = draft

st = [dict(s) for s in pop]
for _ in range(4):
    for s in st:
        if s["surface"] and rng.random() < SEE_SURFACE and rng.random() < FIX:
            s["surface"] = False
        if s["logic"] and rng.random() < SEE_LOGIC and rng.random() < FIX:
            s["logic"] = False
        if rng.random() < NEW_SURFACE:
            s["surface"] = True
refine = acc5(st)

a = draft
for _ in range(4):
    a = a * (1 - P_CHANGE * FLIP) + (1 - a) * P_CHANGE * FLIP
intrinsic5 = a

right = 0
for s in pop:
    masses = GOOD if not s["logic"] else BAD
    votes = Counter(rng.choices(range(3), weights=masses, k=20))
    if votes.most_common(1)[0][0] == 0:
        right += 1
vote = right / N

a = draft
for _ in range(2):
    a = a * (1 - P_FLAG_RIGHT * (1 - KEEP)) + (1 - a) * P_FLAG_WRONG * REPAIR
gated5 = a

rows = [
    ("single-shot", 1, single),
    ("intrinsic x4", 9, intrinsic5),
    ("refine x4", 9, refine),
    ("gated x2", 5, gated5),
    ("vote@20", 20, vote),
]
print(f"draft batch accuracy {draft:.3f} on {N} items")
print("policy        calls/item  accuracy  delta")
for name, c, a5 in rows:
    print(f"{name:13s} {c:10d}  {a5:8.3f}  {a5 - draft:+.3f}")
print(f"same 900-call bill, opposite signs: refine x4 {refine - draft:+.3f} vs intrinsic x4 {intrinsic5 - draft:+.3f}")
print(f"vote@20's {vote - draft:+.3f} costs 20 calls/item; gated x2's {gated5 - draft:+.3f} costs 5")
```

The ledger's middle rows are the lesson's thesis priced in tokens. Intrinsic x4 and refine x4 bill identically - 9 calls per item, 900 for the batch - and land on opposite sides: refine +0.130, intrinsic -0.160. The only difference is critique discipline: refine rewrites when the critique names a defect it can see; intrinsic rewrites on a vibe, and the vibe flips cost it 11 points of accuracy it then pays tokens to lose. Vote@20 buys +0.030 at 20 calls per item - twenty times the bill for near-parity, because the batch's wrong-plurality items give back what the good-plurality ones gain. Gated x2 wins the batch outright at +0.192 on 5 calls per item: external signal is the only policy that buys accuracy at a sane exchange rate, and the campaign's ordering rule is exactly that - spend on a verifier first; if none exists, refine in detect-mode and never in hunt-mode; vote only where the correct mode is demonstrably plural and the budget can carry K times the decode.

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| self-correction pass added, accuracy fell | hunt-mode rewriting with no external signal - flips are coin flips, and correct answers outnumber wrong ones, so the rewrites cost the correct answers first | gate every rewrite on a named defect or a tool signal; Huang et al.'s 95.5 -> 89.0 on GPT-4/GSM8K is the citation for the review |
| vote returns a confident wrong answer | the wrong mode is plural; vote share measures plurality, not truth - the bad regime converges to 0.062 right | probe the distribution's mode structure on a labeled sample before shipping the vote; treat unanimous answers as a distribution property, not a correctness certificate |
| refine loop regresses mid-run | revision churn - each rewrite can introduce fresh surface defects faster than the critique catches them (the iter-3 dip: 18 fixes against 22 fresh) | cap revisions per item, stop on plateau, and require each critique to name the defect before the rewrite fires |
| refine loop plateaus short of target | the plateau is the critique's recall floor, not the loop running out of turns - the logic class holds its residual | stop iterating and route the residual to an external checker; more loop turns buy nothing at SEE_LOGIC-level recall |
| retry budget spent, accuracy flat | bare retries re-roll the same distribution (attempt-2 conditional 0.379 against a 0.40 first-attempt rate) | require the retry to carry new information - a named failure mode lifted the conditional to 0.597 - or do not retry at all |
| hints lift the failing task but not the following ones | within-run carryover buys efficiency (311 vs 367 attempts for the same 186 successes), never ceiling | persist failure modes across runs in long-term memory - 7404's episodic buffer - where the compounding actually lives |
| token bill multiplied after adding self-consistency | K sampled paths cost K times the decode, paid in full even on items whose mode was already plural | vote selectively - gate on items the single path flags as uncertain, or cap K on the batch's easy slice |

## Summary

The named reflection and self-correction patterns are now runnable code, and every one of them prices its own honesty. The refine loop walks 0.590 to 0.833 on 139 surface fixes against 22 logic fixes - a surface-class instrument whose plateau is its critique's recall floor, with an iter-3 dip owned by revision churn. Self-consistency walks 0.490 to 0.988 where the correct mode is plural and 0.340 down to 0.062 where it is not, because the vote amplifies the distribution, never the truth, at K times the decode bill. The Huang boundary lands in one pair of walks: intrinsic 0.730 -> 0.613 against verifier-gated 0.730 -> 0.907, with 119 flagged-wrong answers and 77 repairs doing what the model's own confidence cannot. The retry split prices the in-run half of the story - bare 159/200, injected 186/200, carryover 186/200 on 311 attempts - and hands the ceiling to 7404's cross-run memory. The campaign closes it: the same 900-call bill buys +0.130 in detect-mode and -0.160 in hunt-mode, the vote's +0.030 costs twenty calls per item, and gated correction's +0.192 costs five. The loop that grades its own work needs a grader with information - every row of every ledger in this lesson is that sentence in arithmetic.

## References

### Related Minder Academy Documents

- [7101: ReAct Loop System](./7101-ReAct-Loop-System.md) - the loop whose mechanical retry this lesson upgrades into critique-injected retries
- [7102: Planning and Decomposition](./7102-Planning-Decomposition.md) - plans are the drafts the refine loop revises
- [7104: Agent Evaluation and Observability](./7104-Agent-Evaluation-and-Observability.md) - the external evaluators and scorers that make correction informed
- [7404: Reflective Memory and Context Paging](../7400-memory/7404-Reflective-Memory-and-Context-Paging.md) - the memory-side reflexion this lesson's run-local ceiling argues for
- [ReAct Implementation Guide](./guides/7103-ReAct-Implementation-Guide.md) - the `SelfCorrectingAgent` extension exercise this lesson's retry fence implements
- [5205: GRPO and RLVR](../../phase5-finetuning/5200-alignment/5205-GRPO-RLVR.md) - training-time self-correction; where the emergent behavior at inference comes from

### Primary Sources

- Madaan et al., "Self-Refine: Iterative Refinement with Self-Feedback" (arXiv 2303.17651) - one model as generator, feedback provider, and refiner; roughly 20% average absolute improvement across 7 tasks; demo at `selfrefine.info`.
- Wang et al., "Self-Consistency Improves Chain of Thought Reasoning in Language Models" (ICLR 2023, arXiv 2203.11171) - majority vote over sampled chain-of-thought paths; +17.9% GSM8K, +11.0% SVAMP, +12.2% AQuA, +6.4% StrategyQA, +3.9% ARC-challenge.
- Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet" (ICLR 2024, arXiv 2310.01798) - GPT-4 GSM8K 95.5 -> 91.5 -> 89.0 and GPT-3.5 75.9 -> 75.1 -> 74.7 under intrinsic self-correction with the no-external-feedback three-step prompt.
- Gou et al., "CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing" (ICLR 2024, arXiv 2305.11738) - verify-then-revise with search, interpreter, and toxicity tools; ChatGPT GSM8K 72.5 -> 78.2 over program-of-thought, 77.0 with tools removed.
- Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning" (arXiv 2303.11366) - verbal rules as memory across attempts; the persistence half this lesson hands to 7404.

---

## Next Steps

- Next Module: **[7200: Tool Calling and Function Execution](../7200-tools/README.md)**
- Continue with: **[7201: Tool Calling](../7200-tools/7201-Tool-Calling.md)** - the tool outputs that turn correction from a vibe into information
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Reproduce the boundary on your own runs: take five failed agent trajectories, extract each failure mode into a one-line rule, re-run with the rule injected into the retry, and record the attempt-2 lift; then delete the rules at run end and re-run - the lift that survives nowhere is the one that needs 7404's persistent memory.
