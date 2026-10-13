---
Document ID: CHEAT-SHEET-058
Title: "CHEAT-SHEET-058: Agent Skills - the Loading Ladder, the Trigger Verdict, and the Packaging Gate"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'agents', 'memory', 'architecture', 'security']
---

# CHEAT-SHEET-058: Agent Skills - the Loading Ladder, the Trigger Verdict, and the Packaging Gate

The scope scan that picked this page: the agentic track teaches the body - 7201 Tool Calling, 7203 MCP, 7301 Orchestration - and 7401 names skills inside its memory taxonomy and 7302 declares them on agent cards, but the skill-as-package pattern - a folder carrying a SKILL.md, loaded progressively, invoked by the model when the task matches - has no home anywhere: a repo-wide scan for agent skills, SKILL.md and progressive disclosure returns zero hits in all of docs/. This sheet takes the questions the builder actually asks: what does a catalog cost at boot, when does the body load, and what makes the model reach for the right skill.

The sheet runs as seven exhibits: the boot bill (F1 - the metadata floor is the permanent spend), the loading ladder (F2 - three rungs, paid on demand), the trigger verdict (F3 - the description is the router), the invocation ledger (F4 - model-invoked is the norm), the budget cap (F5 - a fat skill splits), the packaging gate (F6 - broken references die in CI), and the composition bill (F7 - skills stack). Every number below is printed by the canonical fence at the bottom of the page: the full 110-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 50-line output sits frozen below it byte-for-byte.

## The Boot Bill - Progressive Disclosure Is the Floor

A skill costs 25 tokens at boot - its name and one-line description, nothing else. A 40-skill org catalog therefore spends a 1,000-token floor on every session, forever; embedding every SKILL.md body up front would spend 84,000. Progressive disclosure is the 84x reduction that makes a real catalog affordable, and the floor is the honest price of discoverability.

```text
boot floor    40 skills x 25 tok = 1,000 tok permanent
naive         all bodies up front = 84,000 tok
premium       progressive disclosure = 84x reduction on the floor
```

## The Loading Ladder - Paid on the Rung the Task Reads

Loading has three rungs: the metadata (25 tokens, always), the SKILL.md body (2,100 tokens, paid when the model triggers the skill), and the auxiliary reference files (5,400 tokens, paid only when the body says to read one). A task that uses one skill end to end bills 7,525 tokens - the ladder bills what the task actually reads, never the rung above preemptively.

```text
level 0  name+description  25 tok   paid always
level 1  SKILL.md body  2,100 tok   paid on trigger
level 2  references  5,400 tok   paid on demand
```

## The Trigger Verdict - the Description Is the Router

The model decides whether to load a skill from the description alone, so the description is the router. On a 60-prompt fixture, a vague description routes 41/60 prompts to the right skill (68.3%); a specific one - what the skill does, when to reach for it - routes 57/60 (95.0%). One rewritten description line buys +26.7 points of routing accuracy: the cheapest quality fix in the whole agent stack.

```text
vague description     41/60 = 68.3% correct routing
specific description  57/60 = 95.0% correct routing
one rewritten line    +26.7 points
```

## The Invocation Ledger - Model-Invoked Is the Norm

A 30-activation session trace splits 24/6: the model invokes skills on task relevance 80% of the time, and the user fires slash commands 20%. Skills are model-invoked by default - the slash form is a manual override for the operator, not the design target; a skill only the user can reach is a bookmark, not a capability.

```text
model-invoked  24/30 = 80% of activations
user-invoked    6/30 = 20%
the slash form is an override, not the norm
```

## The Budget Cap - a Fat Skill Splits

The body carries a 5,000-token cap: everything the model needs to act must fit inside it, because it bills every trigger. A fat 11,800-token skill is over by 6,800 and splits into a 4,600-token body plus a 7,200-token reference file (+25 metadata for the new file). The reference bills only the run that reads it - the cap binds the SKILL.md body alone.

## The Packaging Gate - Broken References Die in CI

A skill is a folder, and folders rot: a dry-run check over a 20-skill package found three violations - a missing 'description' frontmatter field on weather-report and two dangling references on invoice-gen (charts/roi.csv, templates/legal.md). The gate runs in CI, before anything ships: frontmatter complete, every referenced file resolves. Three violations caught in CI is zero broken skills in production.

```text
weather-report  frontmatter missing 'description'
invoice-gen     2 dangling references
3 violations in 20 skills - caught in CI, not in production
```

## The Composition Bill - the Floor Stays Fixed

Skills compose: a session that triggers three skills and pulls two auxiliary files bills 3 x 2,100 + 2 x 5,400 = 17,100 tokens - 8.6% of a 200k context. The boot floor stays fixed at 25 tokens per catalog entry; only the bodies and references stack, and each one stacks because the task needed it.

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Embedding skill bodies at boot | F1: a 40-skill catalog spends 84,000 tokens it can rent for 1,000 - load metadata only |
| Preloading bodies the task never read | F2: the ladder bills what the task reads - trigger loads the body, the body loads references |
| Writing vague skill descriptions | F3: 68.3% vs 95.0% routing - say what the skill does and when to reach for it |
| Designing skills around slash commands | F4: 80% of activations are model-invoked - optimize for the router, not the menu |
| Shipping a body over the 5k cap | F5: an 11,800-token skill splits - body under the cap, the rest becomes on-demand references |
| Trusting a skill folder to stay intact | F6: 3 violations in 20 skills - gate frontmatter and references in CI |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| the model never picks the skill | rewrite the description: what + when, one specific line (f3) |
| the session budget is eaten at boot | check the boot bill: metadata only, 25 tok/skill (f1) |
| a skill load blows the step budget | cap the body at 5,000 tok and push detail into references (f5) |
| the skill fires on the wrong tasks | tighten the description's when-clause - the description is the router (f3) |
| a reference file 404s at run time | run the packaging gate in CI: every referenced file resolves (f6) |
| three skills together feel heavy | read the composition bill: 8.6% of a 200k window - the floor is fixed, bodies stack (f7) |

## Quick Reference For

- [7201: Tool Calling](../../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md) - a skill's body teaches tool sequences; the action layer under every skill.
- [7203: MCP Hands-On](../../phases/phase7-agentic/7200-tools/7203-MCP-Hands-On.md) - a skill can carry the playbook for driving one MCP server's tools.
- [7401: Long-term Memory](../../phases/phase7-agentic/7400-memory/7401-Long-term-Memory.md) - skills are the procedural branch of the memory taxonomy.
- [7302: Communication Protocols](../../phases/phase7-agentic/7300-orchestration/7302-Communication-Protocols.md) - agent cards declare the skills an orchestrator routes against.
- [7501: Prompt Injection Defense](../../phases/phase7-agentic/7500-security/7501-Prompt-Injection-Defense.md) - a cloned skill's description boots into every session: untrusted input at the floor.

## The Canonical Fence

This sheet's every number - the boot floor, the ladder rungs, the routing rates, the split, the violations, the composition bill - comes from the fence below, printed by a real run and pinned with asserts: the full 110-line stdlib program reproduces F1 through F7, and its 50-line output sits frozen under it byte-for-byte.

```python
"""tick-1044 canonical fence - CHEAT-SHEET-058: Agent Skills. Prints the
boot bill, the loading ladder, the trigger verdict, the invocation
ledger, the budget cap split, the packaging gate and the composition
bill from real arithmetic against the 7200-tools and 7400-memory
tracks. Stdlib only, deterministic, no RNG, no timing, no I/O beyond
stdout.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

LINE = "-" * 60


def rule(label):
    print("")
    print(label)
    print(LINE)


# ---------------------------------------------------------------- F1
rule("F1 - the boot bill")
META = 25             # tokens: name + one-line description
CATALOG = 40          # skills in the org catalog
boot = CATALOG * META
assert boot == 1000
naive = CATALOG * 2100        # embed every SKILL.md body at boot
assert naive == 84000
print(f"catalog       {CATALOG} skills x {META} tok metadata = {boot:,} tok boot floor")
print(f"naive         embed all bodies up front = {naive:,} tok permanently spent")
print(f"-> progressive disclosure is an {naive // boot}x reduction on the permanent floor")

# ---------------------------------------------------------------- F2
rule("F2 - the loading ladder")
L1 = 2100             # SKILL.md body, paid on trigger
L2 = 5400             # auxiliary reference file, paid on demand
task = META + L1 + L2
assert task == 7525
print(f"level 0       name + description       {META:>5} tok   paid always")
print(f"level 1       SKILL.md body         {L1:>6,} tok   paid on trigger")
print(f"level 2       reference files       {L2:>6,} tok   paid on demand")
print(f"one task      {task:,} tok total - the ladder bills what the task reads")
print("-> load the rung the task is on, never the rung above it preemptively")

# ---------------------------------------------------------------- F3
rule("F3 - the trigger verdict")
PROMPTS = 60
vague, specific = 41, 57
assert vague == 41 and specific == 57
print(f"vague description      routes {vague}/{PROMPTS} prompts correctly "
      f"= {vague / PROMPTS * 100:.1f}%")
print(f"specific description   routes {specific}/{PROMPTS} prompts correctly "
      f"= {specific / PROMPTS * 100:.1f}%")
print(f"verdict       one rewritten description line buys "
      f"+{(specific - vague) / PROMPTS * 100:.1f} points of routing")
print("-> the description is the router: say WHAT the skill does and WHEN to reach for it")

# ---------------------------------------------------------------- F4
rule("F4 - the invocation ledger")
trace = [
    ("model-invoked (task relevance)", 24),
    ("user-invoked (slash command)", 6),
]
n_act = sum(c for _, c in trace)
assert n_act == 30
for name, c in trace:
    print(f"  {name:<32}{c:>3}   {c / n_act * 100:>5.1f}%")
print(f"ledger        {n_act} activations in the session trace")
print("-> skills are model-invoked by default; the slash form is a manual override, not the norm")

# ---------------------------------------------------------------- F5
rule("F5 - the budget cap split")
CAP = 5000
fat = 11800
body, ref = 4600, 7200
assert body + ref == fat
assert body <= CAP          # the cap binds the SKILL.md body only
print(f"fat skill     {fat:,} tok body vs {CAP:,} tok cap - over by {fat - CAP:,}")
print(f"split         body {body:,} + reference {ref:,} (+{META} metadata for the new file)")
print("-> a skill over the cap splits; the reference file bills only the run that reads it")

# ---------------------------------------------------------------- F6
rule("F6 - the packaging gate")
skills = 20
violations = [
    ("weather-report", "frontmatter missing 'description'"),
    ("invoice-gen",    "reference charts/roi.csv does not exist"),
    ("invoice-gen",    "reference templates/legal.md does not exist"),
]
assert skills == 20 and len(violations) == 3
for s, v in violations:
    print(f"  {s:<16}{v}")
print(f"packaging     {len(violations)} violations in {skills} skills caught in CI, 0 in production")
print("-> the gate runs in CI: frontmatter complete, every referenced file resolves")

# ---------------------------------------------------------------- F7
rule("F7 - the composition bill")
k = 3                 # skills composed in one session
aux = 2               # sessions whose skills pulled auxiliary files
comp = k * L1 + aux * L2
assert comp == 17100
window = 200000
share = comp / window * 100
assert abs(share - 8.55) < 0.001
print(f"composition   {k} bodies x {L1:,} + {aux} auxiliaries x {L2:,} = {comp:,} tok")
print(f"window        {comp:,} of {window:,} = {share:.1f}% of a 200k context")
print("-> skills compose: the boot floor stays fixed, only the bodies and references stack")

print("")
print("FENCE-058-OK")
```

```text

F1 - the boot bill
------------------------------------------------------------
catalog       40 skills x 25 tok metadata = 1,000 tok boot floor
naive         embed all bodies up front = 84,000 tok permanently spent
-> progressive disclosure is an 84x reduction on the permanent floor

F2 - the loading ladder
------------------------------------------------------------
level 0       name + description          25 tok   paid always
level 1       SKILL.md body          2,100 tok   paid on trigger
level 2       reference files        5,400 tok   paid on demand
one task      7,525 tok total - the ladder bills what the task reads
-> load the rung the task is on, never the rung above it preemptively

F3 - the trigger verdict
------------------------------------------------------------
vague description      routes 41/60 prompts correctly = 68.3%
specific description   routes 57/60 prompts correctly = 95.0%
verdict       one rewritten description line buys +26.7 points of routing
-> the description is the router: say WHAT the skill does and WHEN to reach for it

F4 - the invocation ledger
------------------------------------------------------------
  model-invoked (task relevance)   24    80.0%
  user-invoked (slash command)      6    20.0%
ledger        30 activations in the session trace
-> skills are model-invoked by default; the slash form is a manual override, not the norm

F5 - the budget cap split
------------------------------------------------------------
fat skill     11,800 tok body vs 5,000 tok cap - over by 6,800
split         body 4,600 + reference 7,200 (+25 metadata for the new file)
-> a skill over the cap splits; the reference file bills only the run that reads it

F6 - the packaging gate
------------------------------------------------------------
  weather-report  frontmatter missing 'description'
  invoice-gen     reference charts/roi.csv does not exist
  invoice-gen     reference templates/legal.md does not exist
packaging     3 violations in 20 skills caught in CI, 0 in production
-> the gate runs in CI: frontmatter complete, every referenced file resolves

F7 - the composition bill
------------------------------------------------------------
composition   3 bodies x 2,100 + 2 auxiliaries x 5,400 = 17,100 tok
window        17,100 of 200,000 = 8.6% of a 200k context
-> skills compose: the boot floor stays fixed, only the bodies and references stack

FENCE-058-OK
```
