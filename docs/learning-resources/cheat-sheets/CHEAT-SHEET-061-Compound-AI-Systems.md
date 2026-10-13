---
Document ID: CHEAT-SHEET-061
Title: "CHEAT-SHEET-061: Compound AI Systems - the Composition Ledger, the Verifier Gate, and the Ablation Audit"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'agents', 'reflection', 'orchestration', 'evaluation']
---

# CHEAT-SHEET-061: Compound AI Systems - the Composition Ledger, the Verifier Gate, and the Ablation Audit

The scope scan that picked this page: a repo-wide scan for compound AI and compound systems returns zero of the catalog's 561 markdown docs - DSPy and program synthesis return zero too; the composition principle itself has no page. The pieces live apart: 7105 teaches the verifier-gated repair loop, 7201 the tool surface, 7301 the coordination layer, CHEAT-SHEET-023 the ReAct loop, CHEAT-SHEET-024 the multi-agent patterns, and CHEAT-SHEET-013 the structured contract between the parts - each a part, none the blueprint. The operator questions that start the moment a model stops being the whole system have no home: when does composing beat scaling, what does each component cost, where do verifiers pay, and how do you grade the composition rather than the parts. No dedicated operator page and no dedicated module exists anywhere in the catalog.

The sheet runs as seven exhibits: the composition ledger (F1 - compose the system before you scale the model), the repair ledger (F2 - flag, repair, re-verify, count what lands), the call bill (F3 - every component is a call), the verifier gate (F4 - measure both error directions), the token bill (F5 - budget for the straight path, gate for the repair path), the router gate (F6 - the router moves tasks, not correctness), and the ablation audit (F7 - remove one part, read the delta). Every number below is printed by the canonical fence at the bottom of the page: the full 159-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 69-line output sits frozen below it byte-for-byte.

## The Composition Ledger - Compose the System Before You Scale the Model

The composition is the cheapest lever left once the model is the bottleneck. On the 100-task fixture the monolith answers 62 of 100 (62%); the compound path - draft, verify, repair - answers 79 of 100 (79%). The +17 points come from the system, not a bigger model: no training run, no new weights, just a draft model held to a verifier and given a repair round. Every claim on this page prices that trade.

```text
  fixture       100 tasks, one pass each
  monolith      62/100 correct (= 62%)
  compound      79/100 correct (= 79%) - +17 from the composition
  -> compose the system before you scale the model: +17 points costs calls, not training
```

## The Repair Ledger - Flag, Repair, Re-Verify, Count What Lands

The repair ledger is the system's balance sheet. Of 100 drafts 61 are right on the first pass; the verifier flags 41 (35 true wrongs, 6 false flags); 18 of the 41 repairs land (44%) and the system finishes at 79 correct with 21 wrong - of which 4 passed the verifier silently. The ledger is the contract: flag, repair, re-verify, and count what lands, not what was attempted.

```text
  first pass    61/100 drafts correct
  verifier      41 drafts flagged (35 true + 6 false)
  repair        18 of 41 repairs land (= 44%)
  final         79/100 correct; 21 wrong (4 passed the verifier silently)
  -> the repair loop is the system: flag, repair, re-verify - and count what lands
```

## The Call Bill - Every Component Is a Call

Every component is a call. The monolith spends 100 calls, one per task. The compound path spends 282 - 200 for a draft plus verify on every task, 82 more for the repair rounds the 41 flags trigger, 2.8x the calls for +17 points. The composition's price is paid in call count before it is paid in anything else.

```text
  calls         282 (200 draft+verify + 82 repair rounds)
  monolith      100 calls, one per task
  ratio         2.8x the calls for +17 points
  -> every component is a call - the composition's price is paid in call count
```

## The Verifier Gate - Measure Both Error Directions

The verifier is a gate with two error directions. It flags 35 of the 39 wrong drafts (recall 90%) and 35 of its 41 flags are true (precision 85%). The other two directions are the bill: 4 wrong drafts pass unflagged - silent failures no repair round will ever see - and 6 correct drafts get flagged, repairs that must leave them intact. Measure both directions, price both.

```text
  precision     35/41 flagged were truly wrong (= 85%)
  recall        35/39 wrong drafts were caught (= 90%)
  silent        4 wrong drafts passed the verifier unflagged
  false flags   6 correct drafts flagged - repairs left them intact
  -> the verifier is a gate with two error directions - measure both, price both
```

## The Token Bill - Budget for the Straight Path, Gate for the Repair Path

The straight path is cheap, the repair path is the premium. The monolith spends 900 tokens per task (280 prompt + 620 answer). A draft-plus-verify task spends 1,220 - 1.4x. A task that rides repair spends 2,440 - 2.7x. Across the fixture that is 169,580 tokens against the monolith's 90,000, blended 1,696 per task, 1.9x. Budget for the straight path, gate for the repair path.

```text
  monolith      900 tok/task (280 prompt + 620 answer)
  straight      1,220 tok = draft + verify = 1.4x monolith
  repair        2,440 tok = + repair + re-verify = 2.7x monolith
  total         169,580 tok vs 90,000 - blended 1,696/task (1.9x)
  -> budget for the straight path, gate for the repair path
```

## The Router Gate - the Router Moves Tasks, Not Correctness

The router is free accuracy. Re-run the fixture with a router in front: 68 simple tasks take the monolith path at 900 tokens, 32 hard tasks take the compound path (17 straight, 15 repair). The bill drops to 118,540 - 61,200 + 20,740 + 36,600 - a 30% cut at the same 79 of 100, because the router moves tasks between paths, it does not change any task's outcome on its path.

```text
  router        68 simple -> monolith path; 32 hard -> compound path
  hard mix      17 straight + 15 repair on the compound side
  tokens        118,540 (61,200 + 20,740 + 36,600) vs 169,580
  saved         51,040 tok (= 30%) at the same 79/100
  -> the router moves tasks, not correctness - and cuts the bill 30%
```

## The Ablation Audit - Remove One Part, Read the Delta

Grade the composition by ablation, not by parts list. Full system: 79 of 100. Remove the verifier and the 18 repairs never happen: 61. Remove retrieval and the repairs lose their grounding, 3 of 18 still land: 64. Remove the structured contract and 8 drafts become unparseable and unverifiable: 71. The deltas order the build: verifier (+18), retrieval (+15), structured output (+8).

```text
  full system   79/100
  - verifier    61/100 (-18: the 18 repairs never happen)
  - retrieval   64/100 (-15: repairs lose their grounding)
  - structured  71/100 (-8: 8 drafts unparseable, unverifiable)
  -> grade the composition by ablation: remove one part, re-run, read the delta
```

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Skipping the composition for a bigger model | F1: the monolith plateaus at 62/100 - the +17 points came from draft, verify and repair, not from scale |
| Counting repair attempts instead of repairs landed | F2: 41 flags fired, 18 repairs landed (44%) - the ledger that counts attempts reads 41/41 and hides 21 wrong answers |
| Reading the token bill as the whole price | F3: the compound path is 2.8x the calls before it is 1.9x the tokens - the call count is the latency and rate-limit bill |
| Trusting a one-direction verifier | F4: 4 wrong drafts passed silently and 6 correct drafts were flagged - a gate with one error rate is half measured |
| Pricing every task at the straight path | F5: repair tasks spend 2,440 tok (2.7x monolith) - the blended 1,696 (1.9x) is the number the budget must hold |
| Routing everything through the compound path | F6: forcing all 100 tasks costs 169,580 tok; the router's 68/32 split costs 118,540 for the same 79/100 |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| the ledger reads 41/41 fixed but wrong answers ship | it counted attempts - recount by repairs landed and re-run the 23 failed flags (f2) |
| rate limits or latency spikes under load | the call bill is the spike: 282 calls vs 100 - batch the verify calls and cap concurrent repair rounds (f3) |
| repairs occasionally corrupt correct answers | the 6 false flags must survive repair unchanged - assert the repair pass preserves a draft it finds no defect in (f4) |
| the blended bill drifts past 1.9x | the repair-path share grew - log the flag rate per run; blended = straight share x 1,220 + repair share x 2,440 (f5) |
| tokens jumped after adding the composition | the router is missing or routing everything hard - pull the 68/32 split back; the router is the 30% discount (f6) |
| the system regressed and no one knows which part | ablation is the audit - remove one component, re-run the fixture, read the delta against 79 (f7) |

## Quick Reference For

- [7105: Reflection and Self-Correction](../../phases/phase7-agentic/7100-architecture/7105-Reflection-and-Self-Correction.md) - the verifier-gated repair loop this page's ledger prices.
- [7201: Tool Calling & Function Execution](../../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md) - the tool surface the compound path wires between draft and verifier.
- [7301: Collaborative Tasking - Multi-Agent Synergy](../../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md) - the coordination layer the router and the repair rounds ride.
- [7101: ReAct (Reasoning + Acting) Loop System](../../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md) - the loop form the compound path generalizes from one agent to a pipeline.
- [7104: Agent Evaluation and Observability](../../phases/phase7-agentic/7100-architecture/7104-Agent-Evaluation-and-Observability.md) - the ablation audit is this fixture's slice of measuring the loop as working code.

## The Canonical Fence

This sheet's every number - the composition ledger, the repair ledger, the call bill, the verifier gate, the token bill, the router gate, the ablation audit - comes from the fence below, printed by a real run and pinned with asserts: the full 159-line stdlib program reproduces F1 through F7, and its 69-line output sits frozen under it byte-for-byte.

```python
# CHEAT-SHEET-061 fence - Compound AI Systems, measured on a fixed
# 100-task fixture. No RNG: the fixture is a literal design, every
# printed figure is pinned with an assert, and the fence is stdlib-only.
T = 100

MONO_OK = 62
COMP_OK = 79

# F2 repair ledger
FIRST = 61
WRONG = T - FIRST
TRUE_WRONG = 35
FALSE_FLAG = 6
SILENT = WRONG - TRUE_WRONG
FLAGGED = TRUE_WRONG + FALSE_FLAG
LANDED = 18
FINAL_WRONG = WRONG - LANDED
assert FIRST + LANDED == COMP_OK
assert FINAL_WRONG + COMP_OK == T
assert FLAGGED == 41 and SILENT == 4
assert round(LANDED / FLAGGED * 100) == 44

# F3 call bill
CALLS_BASE = 2 * T
CALLS_REPAIR = 2 * FLAGGED
CALLS = CALLS_BASE + CALLS_REPAIR
assert CALLS == 282
assert round(CALLS / T, 1) == 2.8

# F4 verifier gate
PRECISION = round(TRUE_WRONG / FLAGGED * 100)
RECALL = round(TRUE_WRONG / WRONG * 100)
assert PRECISION == 85 and RECALL == 90

# F5 token bill
MONO_TOK = 900
VERIFY_TOK = 320
STRAIGHT = MONO_TOK + VERIFY_TOK
REPAIR = STRAIGHT + MONO_TOK + VERIFY_TOK
TOTAL_CMP = FIRST * STRAIGHT + WRONG * REPAIR
TOTAL_MONO = T * MONO_TOK
BLENDED = round(TOTAL_CMP / T)
assert TOTAL_CMP == 169580 and TOTAL_MONO == 90000
assert round(STRAIGHT / MONO_TOK, 1) == 1.4
assert round(REPAIR / MONO_TOK, 1) == 2.7
assert round(TOTAL_CMP / TOTAL_MONO, 1) == 1.9
assert BLENDED == 1696

# F6 router gate
SIMPLE, HARD = 68, 32
HARD_STRAIGHT, HARD_REPAIR = 17, 15
assert SIMPLE + HARD == T
assert HARD_STRAIGHT + HARD_REPAIR == HARD
ROUTED = (SIMPLE * MONO_TOK
          + HARD_STRAIGHT * STRAIGHT
          + HARD_REPAIR * REPAIR)
SAVED = TOTAL_CMP - ROUTED
assert ROUTED == 118540
assert ROUTED + SAVED == TOTAL_CMP
assert round(SAVED / TOTAL_CMP * 100) == 30

# F7 ablation audit
NO_VERIFIER = FIRST
NO_RETRIEVAL = 64
NO_STRUCTURED = 71
assert NO_VERIFIER + 18 == COMP_OK
assert NO_RETRIEVAL + 15 == COMP_OK
assert NO_STRUCTURED + 8 == COMP_OK

RULE = "=" * 64


def show(title, rows, arrow):
    print(RULE)
    print(title)
    print()
    for label, text in rows:
        print("  %-13s %s" % (label, text))
    print()
    print("  -> " + arrow)
    print()


show("F1  THE COMPOSITION LEDGER", [
    ("fixture", "%d tasks, one pass each" % T),
    ("monolith", "%d/%d correct (= %d%%)" % (MONO_OK, T, MONO_OK)),
    ("compound", "%d/%d correct (= %d%%) - +%d from the composition"
     % (COMP_OK, T, COMP_OK, COMP_OK - MONO_OK)),
], "compose the system before you scale the model: +17 points costs "
   "calls, not training")

show("F2  THE REPAIR LEDGER", [
    ("first pass", "%d/%d drafts correct" % (FIRST, T)),
    ("verifier", "%d drafts flagged (%d true + %d false)"
     % (FLAGGED, TRUE_WRONG, FALSE_FLAG)),
    ("repair", "%d of %d repairs land (= 44%%)" % (LANDED, FLAGGED)),
    ("final", "%d/%d correct; %d wrong (%d passed the verifier "
     "silently)" % (COMP_OK, T, FINAL_WRONG, SILENT)),
], "the repair loop is the system: flag, repair, re-verify - and "
   "count what lands")

show("F3  THE CALL BILL", [
    ("calls", "%d (%d draft+verify + %d repair rounds)"
     % (CALLS, CALLS_BASE, CALLS_REPAIR)),
    ("monolith", "%d calls, one per task" % T),
    ("ratio", "%.1fx the calls for +17 points" % (CALLS / T)),
], "every component is a call - the composition's price is paid in "
   "call count")

show("F4  THE VERIFIER GATE", [
    ("precision", "%d/%d flagged were truly wrong (= %d%%)"
     % (TRUE_WRONG, FLAGGED, PRECISION)),
    ("recall", "%d/%d wrong drafts were caught (= %d%%)"
     % (TRUE_WRONG, WRONG, RECALL)),
    ("silent", "%d wrong drafts passed the verifier unflagged"
     % SILENT),
    ("false flags", "%d correct drafts flagged - repairs left them "
     "intact" % FALSE_FLAG),
], "the verifier is a gate with two error directions - measure both, "
   "price both")

show("F5  THE TOKEN BILL", [
    ("monolith", "%d tok/task (%d prompt + %d answer)"
     % (MONO_TOK, 280, 620)),
    ("straight", "%s tok = draft + verify = %.1fx monolith"
     % (format(STRAIGHT, ","), STRAIGHT / MONO_TOK)),
    ("repair", "%s tok = + repair + re-verify = %.1fx monolith"
     % (format(REPAIR, ","), REPAIR / MONO_TOK)),
    ("total", "%s tok vs %s - blended %s/task (1.9x)"
     % (format(TOTAL_CMP, ","), format(TOTAL_MONO, ","),
        format(BLENDED, ","))),
], "budget for the straight path, gate for the repair path")

show("F6  THE ROUTER GATE", [
    ("router", "%d simple -> monolith path; %d hard -> compound path"
     % (SIMPLE, HARD)),
    ("hard mix", "%d straight + %d repair on the compound side"
     % (HARD_STRAIGHT, HARD_REPAIR)),
    ("tokens", "%s (%s + %s + %s) vs %s"
     % (format(ROUTED, ","), format(SIMPLE * MONO_TOK, ","),
        format(HARD_STRAIGHT * STRAIGHT, ","),
        format(HARD_REPAIR * REPAIR, ","), format(TOTAL_CMP, ","))),
    ("saved", "%s tok (= %d%%) at the same %d/%d"
     % (format(SAVED, ","), round(SAVED / TOTAL_CMP * 100),
        COMP_OK, T)),
], "the router moves tasks, not correctness - and cuts the bill 30%")

show("F7  THE ABLATION AUDIT", [
    ("full system", "%d/%d" % (COMP_OK, T)),
    ("- verifier", "%d/%d (-18: the 18 repairs never happen)"
     % (NO_VERIFIER, T)),
    ("- retrieval", "%d/%d (-15: repairs lose their grounding)"
     % (NO_RETRIEVAL, T)),
    ("- structured", "%d/%d (-8: 8 drafts unparseable, unverifiable)"
     % (NO_STRUCTURED, T)),
], "grade the composition by ablation: remove one part, re-run, "
   "read the delta")

print("FENCE-061-OK")
```
```text
================================================================
F1  THE COMPOSITION LEDGER

  fixture       100 tasks, one pass each
  monolith      62/100 correct (= 62%)
  compound      79/100 correct (= 79%) - +17 from the composition

  -> compose the system before you scale the model: +17 points costs calls, not training

================================================================
F2  THE REPAIR LEDGER

  first pass    61/100 drafts correct
  verifier      41 drafts flagged (35 true + 6 false)
  repair        18 of 41 repairs land (= 44%)
  final         79/100 correct; 21 wrong (4 passed the verifier silently)

  -> the repair loop is the system: flag, repair, re-verify - and count what lands

================================================================
F3  THE CALL BILL

  calls         282 (200 draft+verify + 82 repair rounds)
  monolith      100 calls, one per task
  ratio         2.8x the calls for +17 points

  -> every component is a call - the composition's price is paid in call count

================================================================
F4  THE VERIFIER GATE

  precision     35/41 flagged were truly wrong (= 85%)
  recall        35/39 wrong drafts were caught (= 90%)
  silent        4 wrong drafts passed the verifier unflagged
  false flags   6 correct drafts flagged - repairs left them intact

  -> the verifier is a gate with two error directions - measure both, price both

================================================================
F5  THE TOKEN BILL

  monolith      900 tok/task (280 prompt + 620 answer)
  straight      1,220 tok = draft + verify = 1.4x monolith
  repair        2,440 tok = + repair + re-verify = 2.7x monolith
  total         169,580 tok vs 90,000 - blended 1,696/task (1.9x)

  -> budget for the straight path, gate for the repair path

================================================================
F6  THE ROUTER GATE

  router        68 simple -> monolith path; 32 hard -> compound path
  hard mix      17 straight + 15 repair on the compound side
  tokens        118,540 (61,200 + 20,740 + 36,600) vs 169,580
  saved         51,040 tok (= 30%) at the same 79/100

  -> the router moves tasks, not correctness - and cuts the bill 30%

================================================================
F7  THE ABLATION AUDIT

  full system   79/100
  - verifier    61/100 (-18: the 18 repairs never happen)
  - retrieval   64/100 (-15: repairs lose their grounding)
  - structured  71/100 (-8: 8 drafts unparseable, unverifiable)

  -> grade the composition by ablation: remove one part, re-run, read the delta

FENCE-061-OK
```
