---
Document ID: CHEAT-SHEET-037
Title: "CHEAT-SHEET-037: Reflection & Self-Correction - the Loop That Grades Its Own Work"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'agents', 'reflection', 'self-correction']
---

# CHEAT-SHEET-037: Reflection & Self-Correction - the Loop That Grades Its Own Work

**Quick Reference for:** the in-run self-improvement family - the draft-critique-revise loop that gains only where its critique can see, the sampled majority vote that amplifies whichever mode is plural, the intrinsic-versus-informed boundary that decides whether a rewrite is a repair or a coin flip, the retry split that prices new information over re-rolls, and the campaign ledger where the same 900-call bill lands +0.130 or -0.160 depending entirely on critique discipline. CHEAT-SHEET-025 owns the cross-run memory half of reflexion and CHEAT-SHEET-028 owns the evaluation surface - this sheet owns the loop that grades its own work. The rule it leaves: correction is an information problem, not a confidence problem.

## The Three Families

[Module 7101](../../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md) built the loop and gave it a mechanical retry; [Module 7404](../../phases/phase7-agentic/7400-memory/7404-Reflective-Memory-and-Context-Paging.md) gave reflection a memory that persists across runs; GRPO trains self-correction into the weights so it emerges at inference. What module 7105 owns is the named in-run pattern family between them - and every pattern in it prices its own honesty on one split: **surface defects** (a missing field, a broken format - verifiable by looking at the output) against **logic defects** (a wrong sign, a dropped term - verifiable only by redoing the reasoning). The whole family's ledger follows from where the critique can see.

| family | mechanism | what it buys |
|---|---|---|
| Refine loop (Self-Refine) | draft -> critique -> revise, one model in all three roles | ~20% average absolute gain across 7 tasks - dominated by surface-inspectable work |
| Self-consistency (vote) | k sampled reasoning paths + majority vote over final answers | +17.9% GSM8K, +11.0% SVAMP, +12.2% AQuA - where the correct mode is plural |
| Informed correction (CRITIC) | every rewrite gated on tool output | GSM8K 72.5 -> 78.2 with tools, 77.0 even tools-free where execution checks the work |

## The Refine Loop: Critique That Sees

Self-Refine (Madaan et al., arXiv 2303.17651) makes one model play generator, feedback provider, and refiner - no training, no RL. The paper's own breadth is the tell: its seven tasks are dialogue responses, code optimization, document style - work where the defect is on the surface, inspectable by the same model that made it. The loop's walk on 300 drafts runs 0.590 -> 0.703 -> 0.777 -> 0.770 -> 0.833, and the ledger underneath it is lopsided:

| defect class | same-model critique recall | what the ledger shows |
|---|---|---|
| surface (format, missing field) | 0.80 | 139 fixes in four iterations; residual 17 |
| logic (wrong sign, dropped term) | 0.15 | 22 fixes; residual 34 of the original 60 |

The iter-3 dip to 0.770 is the loop's own revision churn - 22 fresh surface defects landed against 18 fixes, because every revision is a new chance to introduce what the loop is trying to remove. The final plateau at 0.833 is not the loop running out of turns; it is the critique's recall floor. Two rules follow: **stop on the plateau** (the remaining defects are the class the critique cannot see), and **detect-mode discipline** - revise only when the critique names a specific defect, never on a general sense that something is off.

## Self-Consistency: The Plurality Amplifier

Self-consistency (Wang et al., ICLR 2023, arXiv 2203.11171) replaces the single greedy path with k sampled paths and a majority vote over their final answers. The mechanism is an estimator, not magic: sampled paths cluster into answer modes, and the vote converges on whichever mode carries the plurality of the probability mass. K=1 calibrates everything - a single path lands 0.490 and 0.340, exactly the correct mode's mass in each regime:

| K | correct mode is plural (mass 0.50) | wrong mode is plural (correct mass 0.35) |
|---|---|---|
| 1 | 0.490 | 0.340 |
| 5 | 0.652 | 0.350 |
| 20 | 0.815 | 0.242 |
| 100 | 0.988 | 0.062 |

The vote never consults the truth; it consults the distribution. In the good regime twenty samples all but guarantee the plurality speaks (0.988); in the bad regime the same machinery converges on the wrong mode with 93.8% efficiency (0.062). The vote-share number measures the plurality, not the truth - treat unanimity as a distribution property, not a correctness certificate. And the bill is real: K paths cost K times the decode, paid in full even on items whose mode was already obviously plural. Vote where the correct mode is demonstrably dominant; cap K where the budget cannot carry it.

## The Boundary: Intrinsic vs Informed

Huang et al. (ICLR 2024, arXiv 2310.01798) priced the hunt-mode prompt - "review the answer carefully and report any serious problems" with no ground truth and no tool: GPT-4 GSM8K falls 95.5 -> 91.5 -> 89.0 across two self-correction rounds, GPT-3.5 75.9 -> 75.1 -> 74.7. The rewrites are coin flips, and because correct answers outnumber wrong ones, the coin flip costs the correct answers first. CRITIC (Gou et al., ICLR 2024, arXiv 2305.11738) gates every revision on tool output - search for factual claims, a Python interpreter for math programs - and moves ChatGPT GSM8K 72.5 -> 78.2, still 72.5 -> 77.0 with the tools removed, because executing the program is itself an external signal. Same starting batch, opposite signs:

| path | walk from 0.730 | flag ledger over two rounds |
|---|---|---|
| intrinsic rewrites (no external feedback) | 0.730 -> 0.661 -> 0.613 | flips land right/left at even odds - the loss is the thesis |
| verifier-gated repairs (tool feedback) | 0.730 -> 0.846 -> 0.907 | 119 wrong answers flagged, 77 repaired; 63 correct falsely flagged, 6 lost |

The gated path pays real taxes - 63 false flags, 6 lost to re-inspection - and still nets +0.177 where the intrinsic path loses 0.117. External information does work the model's own confidence demonstrably cannot.

## The Retry Split: Bare, Injected, Carryover

A mechanical retry re-rolls the same call at the same odds. Three policies priced over 200 tasks with up to three attempts each:

| policy | tasks succeeded | attempts consumed | attempt-2 conditional |
|---|---|---|---|
| bare re-roll | 159/200 | 388 | 0.379 |
| critique-injected (failure mode named in the retry prompt) | 186/200 | 367 | 0.597 |
| + within-run carryover (earlier failures pre-warn later tasks) | 186/200 | 311 | 0.663 |

The bare attempt-2 conditional (0.379) is indistinguishable from its attempt-1 odds: a bare retry carries no new information, it just spends another ticket on the same distribution. The named failure mode IS the new information, and it lives entirely in the retry prompt. Carryover shows up as efficiency - the same 186 successes on 56 fewer attempts - but never as ceiling: run-local knowledge dies at run end, and the ceiling itself moves only when rules persist across runs. That persistence is Module 7404's half of reflexion - its episodic buffer walked 20% -> 68% -> 96% -> 100% over 25 tasks by storing rules between tasks.

## The Campaign: One Batch, Five Bills

One 100-item batch, draft accuracy 0.710, and the five policies priced on one ledger:

| policy | calls/item | accuracy | delta |
|---|---|---|---|
| single-shot | 1 | 0.710 | +0.000 |
| intrinsic x4 (hunt-mode) | 9 | 0.550 | -0.160 |
| refine x4 (detect-mode) | 9 | 0.840 | +0.130 |
| gated x2 (verifier) | 5 | 0.902 | +0.192 |
| vote@20 | 20 | 0.740 | +0.030 |

The middle rows are the thesis priced in tokens: the same 900-call bill lands +0.130 in detect-mode and -0.160 in hunt-mode - the vibe-driven rewrite pays 11 points and then pays tokens to lose them. Vote@20 buys +0.030 at twenty times the bill. Gated x2 wins outright at +0.192 on five calls per item:

```text
spend on a verifier first - external signal is the only policy with a sane exchange rate
if none exists, refine in detect-mode only: rewrite on a named, visible defect - never hunt-mode
vote only where the correct mode is demonstrably plural, and cap K where the budget cannot carry K x decode
```

## Known Failure Modes

| failure | lesson |
|---|---|
| A self-correction pass was added and accuracy fell | hunt-mode rewriting with no external signal - flips are coin flips and correct answers pay first (Huang: 95.5 -> 89.0); gate every rewrite on a named defect or a tool signal |
| The vote returns a confident wrong answer | the wrong mode is plural; vote share measures plurality, not truth - probe the mode structure on a labeled sample before shipping the vote |
| The refine loop regresses mid-run | revision churn - rewrites introduce fresh defects faster than the critique catches them (22 fresh vs 18 fixed); cap revisions and stop on the plateau |
| The refine loop plateaus short of target | the plateau is the critique's recall floor, not the loop running out of turns - route the residual class to an external checker; more iterations buy nothing |
| The retry budget is spent and accuracy is flat | bare retries re-roll the same distribution (0.379 conditional against 0.40 first-attempt odds) - require the retry to carry new information or do not retry |
| Hints lift the failing task but not the next ones | within-run carryover buys efficiency (311 vs 367 attempts for the same successes), never ceiling - persist failure modes across runs in memory (Module 7404) |

## References

- Repository, *Module 7105: Reflection and Self-Correction - the full lesson with all five ledgers runnable*
- Madaan et al., 2023, *Self-Refine: Iterative Refinement with Self-Feedback* (arXiv 2303.17651)
- Wang et al., 2023, *Self-Consistency Improves Chain of Thought Reasoning in Language Models* (ICLR 2023, arXiv 2203.11171)
- Huang et al., 2024, *Large Language Models Cannot Self-Correct Reasoning Yet* (ICLR 2024, arXiv 2310.01798)
- Gou et al., 2024, *CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing* (ICLR 2024, arXiv 2305.11738)
- Shinn et al., 2023, *Reflexion: Language Agents with Verbal Reinforcement Learning* (arXiv 2303.11366) - the cross-run half
- Repository, *CHEAT-SHEET-025: Agent Memory Systems* - the memory map this sheet's run-local ceiling argues for

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Accuracy drops after enabling self-correction | hunt-mode prompt, no external feedback | detect-mode only: rewrite on a named defect; add a tool check before any rewrite |
| High vote confidence, wrong answer | wrong mode carries the plurality | probe the mode structure on labeled items; treat unanimity as a distribution property |
| Refine loop oscillates | revision churn introduces fresh surface defects | cap revisions per item; require each critique to name the defect before the rewrite fires |
| Iterations exhausted, one defect class untouched | critique recall floor on that class | stop iterating; route that class to an interpreter, tests, or search |
| Retries burn tokens, success rate unmoved | bare retry = same distribution, new ticket | inject the named failure mode into the retry prompt |
| Context flooded after adding voting | K paths x output tokens on every item | vote selectively on uncertain items; cap K on the batch's easy slice |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 7105: Reflection and Self-Correction](../../phases/phase7-agentic/7100-architecture/7105-Reflection-and-Self-Correction.md) | this sheet's source module - all five ledgers runnable |
| [CHEAT-SHEET-025: Agent Memory Systems](CHEAT-SHEET-025-Agent-Memory-Systems.md) | the cross-run half - where run-local carryover becomes persistent rules |
| [Module 7404: Reflective Memory and Context Paging](../../phases/phase7-agentic/7400-memory/7404-Reflective-Memory-and-Context-Paging.md) | the episodic buffer that walked 20% -> 68% -> 96% -> 100% by storing rules between tasks |
| [CHEAT-SHEET-028: Agent Evaluation and Observability](CHEAT-SHEET-028-Agent-Evaluation-and-Observability.md) | the external evaluators that make correction informed instead of intrinsic |

```python
"""CHEAT-SHEET-037 fence: in-run self-correction, every family priced - 7105 canonical ledgers."""
import random
from collections import Counter

print("F1 refine loop - surface defects drain, logic defects hold their floor")
rng = random.Random(7)
N = 300
state = [{"surface": rng.random() < 0.22, "logic": rng.random() < 0.20} for _ in range(N)]


def acc(st):
    return sum(1 for s in st if not (s["surface"] or s["logic"])) / len(st)


walk = [acc(state)]
fx_s = fx_l = 0
print(f"iter 0 (draft): accuracy {walk[0]:.3f}")
for it in range(1, 5):
    fs = fl = ns = 0
    for s in state:
        if s["surface"] and rng.random() < 0.80 and rng.random() < 0.90:
            s["surface"] = False
            fs += 1
        if s["logic"] and rng.random() < 0.15 and rng.random() < 0.90:
            s["logic"] = False
            fl += 1
        if rng.random() < 0.05:
            s["surface"] = True
            ns += 1
    fx_s += fs
    fx_l += fl
    walk.append(acc(state))
    print(f"iter {it}: accuracy {walk[-1]:.3f}  surface fixes {fs:2d}  logic fixes {fl:2d}  new surface defects {ns}")
print(f"walk: {' -> '.join(f'{a:.3f}' for a in walk)}")
res_s = sum(1 for s in state if s["surface"])
res_l = sum(1 for s in state if s["logic"])
print(f"ledger: {fx_s} surface fixes vs {fx_l} logic fixes; residual: surface {res_s}, logic {res_l}")

print()
print("F2 self-consistency - the vote amplifies whichever mode is plural")
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


GW = vote_walk((0.50, 0.30, 0.20), (1, 5, 20, 100))
BW = vote_walk((0.35, 0.50, 0.15), (1, 5, 20, 100))
print(f"correct-mode plurality {' -> '.join(f'{a:.3f}' for a in GW)}")
print(f"wrong-mode plurality  {' -> '.join(f'{a:.3f}' for a in BW)}")
print(f"K=100: vote {GW[-1]:.3f} vs {BW[-1]:.3f} - plurality wins, truth or error, at 100x the decode")

print()
print("F3 the boundary - intrinsic rewrites decay, verifier-gated repairs climb")
NB = 400
acc0 = 0.730
a = acc0
intr = [a]
for _ in range(2):
    a = a * (1 - 0.30 * 0.50) + (1 - a) * 0.30 * 0.50
    intr.append(a)
a = acc0
gated = [a]
fw_t = fr_t = rep_t = drop_t = 0
for _ in range(2):
    n_wrong = int(round((1 - a) * NB))
    fw = int(round(n_wrong * 0.70))
    fr = int(round((NB - n_wrong) * 0.10))
    rep = int(round(fw * 0.65))
    drop = fr - int(round(fr * 0.90))
    fw_t += fw
    fr_t += fr
    rep_t += rep
    drop_t += drop
    a = a * (1 - 0.10 * 0.10) + (1 - a) * 0.70 * 0.65
    gated.append(a)
print(f"intrinsic (no external feedback): {' -> '.join(f'{x:.3f}' for x in intr)}")
print(f"verifier-gated (tool feedback):   {' -> '.join(f'{x:.3f}' for x in gated)}")
print(f"flag ledger: {fw_t} wrong answers flagged, {rep_t} repaired; {fr_t} correct falsely flagged, {drop_t} lost")

print()
print("F4 the retry split - bare, critique-injected, within-run carryover")
rng = random.Random(31)
TASKS = 200


def run_policy(policy):
    succ = used = s2ok = s2tot = 0
    seen = set()
    for _ in range(TASKS):
        mode = rng.randrange(6)
        prewarn = policy == "carryover" and mode in seen
        for attempt in range(3):
            used += 1
            if attempt == 0:
                p = 0.60 if prewarn else 0.40
            else:
                p = 0.65 if policy in ("injected", "carryover") else 0.40
            hit = rng.random() < p
            if attempt == 1:
                s2tot += 1
                s2ok += hit
            if hit:
                succ += 1
                break
        seen.add(mode)
    return succ, used, s2ok, s2tot


rows4 = {}
for policy in ("bare", "injected", "carryover"):
    succ, used, s2ok, s2tot = run_policy(policy)
    rows4[policy] = (succ, used)
    print(f"{policy:9s}: {succ}/{TASKS} succeeded, {used} attempts, attempt-2 conditional {s2ok / s2tot:.3f}")
print(f"carryover: same {rows4['injected'][0]} successes on {rows4['injected'][1]} -> {rows4['carryover'][1]} attempts = "
      f"{rows4['injected'][1] - rows4['carryover'][1]} saved - efficiency, never ceiling")

print()
print("F5 the campaign - one 100-item batch, five bills")
rng = random.Random(47)
N = 100
pop = [{"surface": rng.random() < 0.22, "logic": rng.random() < 0.20} for _ in range(N)]
draft = sum(1 for s in pop if not (s["surface"] or s["logic"])) / N
st = [dict(s) for s in pop]
for _ in range(4):
    for s in st:
        if s["surface"] and rng.random() < 0.80 and rng.random() < 0.90:
            s["surface"] = False
        if s["logic"] and rng.random() < 0.15 and rng.random() < 0.90:
            s["logic"] = False
        if rng.random() < 0.05:
            s["surface"] = True
refine = sum(1 for s in st if not (s["surface"] or s["logic"])) / N
a = draft
for _ in range(4):
    a = a * 0.85 + (1 - a) * 0.15
intr5 = a
right = 0
for s in pop:
    masses = (0.50, 0.30, 0.20) if not s["logic"] else (0.35, 0.50, 0.15)
    votes = Counter(rng.choices(range(3), weights=masses, k=20))
    if votes.most_common(1)[0][0] == 0:
        right += 1
vote = right / N
a = draft
for _ in range(2):
    a = a * 0.99 + (1 - a) * 0.455
gated5 = a
print(f"draft batch accuracy {draft:.3f} on {N} items")
print("policy        calls/item  accuracy  delta")
for name, c, a5 in [("single-shot", 1, draft), ("intrinsic x4", 9, intr5), ("refine x4", 9, refine),
                    ("gated x2", 5, gated5), ("vote@20", 20, vote)]:
    print(f"{name:13s} {c:10d}  {a5:8.3f}  {a5 - draft:+.3f}")
print(f"same 900-call bill, opposite signs: refine x4 {refine - draft:+.3f} vs intrinsic x4 {intr5 - draft:+.3f}")
print(f"gated x2 nets {gated5 - draft:+.3f} on 5 calls/item; vote@20 buys {vote - draft:+.3f} for 20")
```

```text
F1 refine loop - surface defects drain, logic defects hold their floor
iter 0 (draft): accuracy 0.590
iter 1: accuracy 0.703  surface fixes 60  logic fixes  4  new surface defects 25
iter 2: accuracy 0.777  surface fixes 36  logic fixes  5  new surface defects 20
iter 3: accuracy 0.770  surface fixes 18  logic fixes  6  new surface defects 22
iter 4: accuracy 0.833  surface fixes 25  logic fixes  7  new surface defects 10
walk: 0.590 -> 0.703 -> 0.777 -> 0.770 -> 0.833
ledger: 139 surface fixes vs 22 logic fixes; residual: surface 17, logic 34

F2 self-consistency - the vote amplifies whichever mode is plural
correct-mode plurality 0.490 -> 0.652 -> 0.815 -> 0.988
wrong-mode plurality  0.340 -> 0.350 -> 0.242 -> 0.062
K=100: vote 0.988 vs 0.062 - plurality wins, truth or error, at 100x the decode

F3 the boundary - intrinsic rewrites decay, verifier-gated repairs climb
intrinsic (no external feedback): 0.730 -> 0.661 -> 0.613
verifier-gated (tool feedback):   0.730 -> 0.846 -> 0.907
flag ledger: 119 wrong answers flagged, 77 repaired; 63 correct falsely flagged, 6 lost

F4 the retry split - bare, critique-injected, within-run carryover
bare     : 159/200 succeeded, 388 attempts, attempt-2 conditional 0.379
injected : 186/200 succeeded, 367 attempts, attempt-2 conditional 0.597
carryover: 186/200 succeeded, 311 attempts, attempt-2 conditional 0.663
carryover: same 186 successes on 367 -> 311 attempts = 56 saved - efficiency, never ceiling

F5 the campaign - one 100-item batch, five bills
draft batch accuracy 0.710 on 100 items
policy        calls/item  accuracy  delta
single-shot            1     0.710  +0.000
intrinsic x4           9     0.550  -0.160
refine x4              9     0.840  +0.130
gated x2               5     0.902  +0.192
vote@20               20     0.740  +0.030
same 900-call bill, opposite signs: refine x4 +0.130 vs intrinsic x4 -0.160
gated x2 nets +0.192 on 5 calls/item; vote@20 buys +0.030 for 20
```
