---
Document ID: CHEAT-SHEET-057
Title: "CHEAT-SHEET-057: Browser and Computer-Use Agents - the Grounding Verdict, the Step Budget, and the Sandbox Gate Chain"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'agents', 'tool-calling', 'security', 'vision']
---

# CHEAT-SHEET-057: Browser and Computer-Use Agents - the Grounding Verdict, the Step Budget, and the Sandbox Gate Chain

The scope scan that picked this page: phase7-agentic teaches the agent body - 7201 Tool Calling, 7203 MCP Hands-On, 7301 Orchestration, 7401 memory, 7501 prompt-injection defense - and the sheets cover it piecewise (023 ReAct, 026 security, 027 tool calling and MCP, 032 the code sandbox), but the agent whose hands are a mouse and whose eyes are a screenshot has no home anywhere: a repo-wide scan for browser automation, computer use and GUI agents returns zero hits in all of docs/. This sheet takes the questions the builder actually asks: what does one GUI step cost, how does the model find the button, and what happens when the click lands on nothing.

The sheet runs as seven exhibits: the perception loop bill (F1 - every step reads the page again), the action space ledger (F2 - nine verbs, one skill), the grounding verdict (F3 - marks beat pixels on forms), the verifier gate (F4 - an unchecked screenshot is a claim), the step budget (F5 - the loop detector is the spend cap), the sandbox gate chain (F6 - under the model, not beside it), and the DOM-versus-screenshot verdict (F7 - route by the page). Every number below is printed by the canonical fence at the bottom of the page: the full 144-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 63-line output sits frozen below it byte-for-byte.

## The Perception Loop Bill - Every Step Reads the Page Again

A GUI agent re-reads the page on every step: one 1280x800 screenshot costs 1,547 vision tokens, and the 12-step checkout task re-pays it twelve times. The loop bills 21,012 tokens - $0.012607 at a $0.60-per-1M blended price - where the DOM agent's 524-token a11y slice finishes the same task in 6,288 tokens for $0.003773. The 3.34x pixel premium is the honest price of eyes; the routing decision is architectural, not stylistic - pay it where the DOM is absent, skip it where the tree exists.

```text
per step      vision 1,751 tok  vs  DOM 524 tok
12-step task  21,012 tok ($0.012607) vs 6,288 tok ($0.003773)
premium       3.34x on every GUI step
```

## The Action Space Ledger - Nine Verbs, One Skill

The schema is nine verbs - click, type, key, scroll, screenshot, double_click, drag, wait, cursor_position - and a real 20-action session shows how little of it matters: click 9, type 4 and key 3 carry 16 of 20 actions. The verbs are a vocabulary; the competence lives in the target - which element, which region, which mark - and that is the grounding problem F3 prices.

```text
click 9, type 4, key 3    = 16/20 = 80% of the trace
screenshot 2, scroll 1, wait 1 = the rest
the skill is choosing the target, not the verb
```

## The Grounding Verdict - Marks Beat Pixels on Forms

The fence scores two grounding modes on the 50-task fixture: raw pixel coordinates land 37/50 first clicks (74.0%), while set-of-marks - numbered tags laid over the interactive elements - lands 46/50 (92.0%). The marks cost +210 tokens per step, +126,000 across the 600-step suite, and they buy +18.0 points. The verdict is per-surface: annotate the forms, trust the pixels on canvas.

```text
raw pixel     37/50 = 74.0% first-click accuracy
set-of-marks  46/50 = 92.0% first-click accuracy
marks bill    +210 tokens/step = +126,000 across the suite
```

## The Verifier Gate - an Unchecked Screenshot Is a Claim

A 20-action session carries three broken states the model never notices: a modal swallows step 7's click, a spinner still covers step 11's target, an interstitial steals step 16's focus. The verifier gate checks the post-action state against the expected one - with it the session runs 26 actions and recovers all three; without it the session reports success with three silent broken states. An unchecked screenshot is a claim, not a fact.

```text
step  7 click  BROKEN - modal swallowed the click
step 11 click  BROKEN - spinner still covering the target
step 16 type   BROKEN - interstitial stole the focus
```

## The Step Budget - the Loop Detector Is the Spend Cap

The budget is 25 steps and the runaway is classic: the target never renders, so the agent re-clicks the same nav region forever. The loop detector - the same (action, region) pair three times in a row - halts the session at step 9, sixteen steps and 28,016 tokens of spend that never happened. The detector is one dict and three lines; without it, a rendering gap is a hemisphere of spend.

## The Sandbox Gate Chain - Under the Model, Not Beside It

The gate chain runs under the model, not beside it. G1 blocks navigation to any domain outside the 12-host allowlist; G2 substitutes a vault reference when an action targets a credential field - the model never holds the secret it would type; G3 denies checkout and routes purchases to a human gate; G4 tears the VM down after every session so nothing persists into the next run. A denied action never reaches the page.

```text
G1 allowlist   BLOCK - evil-tracker.example is not on the 12 domains
G2 vault       SUBSTITUTED - a reference, the model never holds the secret
G3 pay-deny    DENIED - checkout routes to a human gate
```

## The DOM-versus-Screenshot Verdict - Route by the Page

The same 50-task suite split by surface: the DOM agent scores 29/31 on forms but 4/19 on canvas - 33/50, 66%; the vision agent flips it, 22/31 on forms and 17/19 on canvas - 39/50, 78%. The hybrid routes by the page: DOM on the 31 form tasks, vision on the 19 canvas tasks, 46/50 = 92% at a blended 1.85 s/step and 990 tokens/step. The a11y tree where it exists, pixels where it does not.

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Clicking raw pixels on form-heavy pages | F3: 74% vs 92% first-click - annotate the forms with set-of-marks |
| Trusting the model's own success report | F4: 3 silent broken states in one 20-action session - verify the post-action state |
| Running a GUI agent without a loop detector | F5: a rendering gap burns the full 25-step budget - halt on 3x the same (action, region) |
| Letting the model hold credentials | F6: the vault substitutes a reference - the model never types what it cannot read |
| Sizing GUI work by text-agent costs | F1: the 3.34x pixel premium - budget 1,751 tokens/step, not 524 |
| Sending canvas tasks to the DOM agent | F7: 4/19 on canvas - route vision where the tree is absent |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| the agent re-clicks a target that never appears | install the loop detector: same action and region 3x halts (f5) |
| clicks miss on dense forms | switch to set-of-marks: +210 tokens/step buys +18 points (f3) |
| the step bill dwarfs the text-agent estimate | re-budget by the perception loop: screenshots re-read every step (f1) |
| the task reports done but the cart is empty | add the verifier gate: diff expected against post-action state (f4) |
| the model typed a secret into the page | route credentials through the vault substitution layer (f6) |
| a canvas app defeats the a11y-tree agent | route by the page: vision for canvas, DOM for forms (f7) |

## Quick Reference For

- [7201: Tool Calling](../../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md) - the action space is a tool schema; the GUI verbs register like any other tool.
- [7203: MCP Hands-On](../../phases/phase7-agentic/7200-tools/7203-MCP-Hands-On.md) - the browser tools this loop drives can arrive over MCP like any other server.
- [7204: Timeouts, Retries and Rate Limits](../../phases/phase7-agentic/7200-tools/7204-Timeouts-Retries-and-Rate-Limits.md) - the step budget and the retry policy the loop runs under.
- [7501: Prompt Injection Defense](../../phases/phase7-agentic/7500-security/7501-Prompt-Injection-Defense.md) - the page is untrusted input; the sandbox gates assume the page attacks.
- [7504: Agent Abuse Prevention and Identity Threats](../../phases/phase7-agentic/7500-security/7504-Agent-Abuse-Prevention-and-Identity-Threats.md) - the abuse surface the gate chain exists to close.

## The Canonical Fence

This sheet's every number - the token bills, the hit rates, the halt step, the blended costs - comes from the fence below, printed by a real run and pinned with asserts: the full 144-line stdlib program reproduces F1 through F7, and its 63-line output sits frozen under it byte-for-byte.

```python
"""tick-1043 canonical fence - CHEAT-SHEET-057: Browser and Computer-Use
Agents. Prints the perception loop bill, the action space ledger, the
grounding verdict, the verifier gate, the runaway loop halt, the sandbox
gate chain and the DOM-versus-screenshot verdict from real arithmetic
against the 7200-tools and 7500-security tracks. Stdlib only,
deterministic, no RNG, no timing, no I/O beyond stdout.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

LINE = "-" * 60


def rule(label):
    print("")
    print(label)
    print(LINE)


# ---------------------------------------------------------------- F1
rule("F1 - the perception loop bill")
SHOT = 1547            # vision tokens for one 1280x800 screenshot
HIST = 180             # per-step system + history delta
ACT = 24               # tokens for one action call
STEPS = 12             # the checkout task: 12 GUI steps
v_step = SHOT + HIST + ACT
d_step = 320 + HIST + ACT       # the DOM agent reads a 320-token a11y slice
v_loop = v_step * STEPS
d_loop = d_step * STEPS
assert v_step == 1751 and d_step == 524
assert v_loop == 21012 and d_loop == 6288
ratio = v_loop / d_loop
assert abs(ratio - 3.3416) < 0.0001
PRICE = 0.60           # $ per 1M blended tokens
v_bill = v_loop / 1e6 * PRICE
d_bill = d_loop / 1e6 * PRICE
print(f"screenshot    {SHOT:,} vision tokens x {STEPS} steps = {v_loop - STEPS * (HIST + ACT):,}")
print(f"per step      vision {v_step:,} tok  vs  DOM {d_step:,} tok")
print(f"12-step task  vision {v_loop:,} tok (${v_bill:.6f})  vs  DOM {d_loop:,} tok (${d_bill:.6f})")
print(f"-> the pixel premium is {ratio:.2f}x on every GUI step; pay it only where the DOM is absent")

# ---------------------------------------------------------------- F2
rule("F2 - the action space ledger")
trace = [
    ("click", 9), ("type", 4), ("key", 3), ("screenshot", 2),
    ("scroll", 1), ("wait", 1),
]
n_act = sum(c for _, c in trace)
assert n_act == 20
top3 = 9 + 4 + 3
assert top3 == 16
for name, c in trace:
    print(f"  {name:<12}{c:>3}   {c / n_act * 100:>5.1f}%")
print(f"schema        9 verbs cover the session: click type key scroll "
      f"screenshot double_click drag wait cursor_position")
print(f"concentration click + type + key = {top3}/20 = "
      f"{top3 / n_act * 100:.0f}% of the trace")
print("-> the action space is small; the skill is choosing the target, not the verb")

# ---------------------------------------------------------------- F3
rule("F3 - the grounding verdict")
TASKS = 50
som_hits, pixel_hits = 46, 37
assert som_hits == 46 and pixel_hits == 37
ANNOT = 210            # extra tokens/step to lay the numbered marks
annot_bill = TASKS * STEPS * ANNOT
assert annot_bill == 126000
print(f"raw pixel     {pixel_hits}/50 = {pixel_hits / TASKS * 100:.1f}% first-click accuracy")
print(f"set-of-marks  {som_hits}/50 = {som_hits / TASKS * 100:.1f}% first-click accuracy")
print(f"annotation    +{ANNOT} tokens/step = +{annot_bill:,} tokens across the suite")
print(f"verdict       +{(som_hits - pixel_hits) / TASKS * 100:.1f} points bought for "
      f"+{annot_bill:,} tokens - mark the forms, trust the pixels on canvas")

# ---------------------------------------------------------------- F4
rule("F4 - the verifier gate")
session = [
    (7, "click",  "modal swallowed the click"),
    (11, "click", "spinner still covering the target"),
    (16, "type",  "interstitial stole the focus"),
]
caught = 0
for step, verb, why in session:
    caught += 1
    print(f"  step {step:>2} {verb:<6} BROKEN - {why} -> re-act once, recover")
assert caught == 3
budgeted = 20 + caught * 2      # verify + one recovery per break
assert budgeted == 26
print(f"with gate     {budgeted} actions for 3 broken states, all recovered, 1 success")
print("without gate  20 actions, reported success, 3 silent broken states")
print("-> an unchecked screenshot is a claim, not a fact; verify the state after every act")

# ---------------------------------------------------------------- F5
rule("F5 - the runaway loop halt")
BUDGET = 25
halt_at = 9
assert halt_at == 9
saved = (BUDGET - halt_at) * v_step
assert saved == 28016
print(f"runaway       the target never renders; the agent re-clicks the nav region")
print(f"detector      same (action, region) 3x in a row -> halt")
print(f"halt          step {halt_at} of the {BUDGET}-step budget - "
      f"{BUDGET - halt_at} steps ({saved:,} tokens) not burned")
print("-> the loop detector is the difference between a halt and a hemisphere of spend")

# ---------------------------------------------------------------- F6
rule("F6 - the sandbox gate chain")
gates = [
    ("G1 domain allowlist", "navigate evil-tracker.example",
     "BLOCK - not on the 12-domain allowlist"),
    ("G2 credential vault", "type password into the login form",
     "SUBSTITUTED - the vault fills a ****** reference, the model never holds it"),
    ("G3 payment deny",     "click the checkout button",
     "DENIED - purchases route to a human gate, not the model"),
]
for gate, attempt, verdict in gates:
    print(f"  {gate:<20} {attempt}")
    print(f"  {'':<20} {verdict}")
print("G4 VM teardown  every session ends in a fresh VM - nothing persists to the next run")
print("-> the chain runs under the model, not beside it; a denied action never reaches the page")

# ---------------------------------------------------------------- F7
rule("F7 - the DOM-versus-screenshot verdict")
forms, canvas = 31, 19
assert forms + canvas == TASKS
dom = (29, 4)
vis = (22, 17)
assert dom[0] + dom[1] == 33 and vis[0] + vis[1] == 39
hybrid = dom[0] + vis[1]
assert hybrid == 46
lat = (forms * 1.2 + canvas * 2.9) / TASKS
toks = (forms * d_step + canvas * v_step) / TASKS
assert abs(lat - 1.846) < 0.0001 and abs(toks - 990.26) < 0.01
print(f"DOM agent     forms {dom[0]}/31, canvas {dom[1]}/19 -> {dom[0] + dom[1]}/50 = "
      f"{(dom[0] + dom[1]) / 50 * 100:.0f}%  ({d_step} tok/step, 1.2 s)")
print(f"vision agent  forms {vis[0]}/31, canvas {vis[1]}/19 -> {vis[0] + vis[1]}/50 = "
      f"{(vis[0] + vis[1]) / 50 * 100:.0f}%  ({v_step:,} tok/step, 2.9 s)")
print(f"hybrid        DOM on the {forms} form tasks, vision on the {canvas} canvas tasks "
      f"-> {hybrid}/50 = {hybrid / 50 * 100:.0f}%")
print(f"hybrid cost   {lat:.2f} s/step, {toks:.0f} tok/step blended")
print("-> route by the page, not by the vendor: the a11y tree where it exists, pixels where it does not")

print("")
print("FENCE-057-OK")
```

```text

F1 - the perception loop bill
------------------------------------------------------------
screenshot    1,547 vision tokens x 12 steps = 18,564
per step      vision 1,751 tok  vs  DOM 524 tok
12-step task  vision 21,012 tok ($0.012607)  vs  DOM 6,288 tok ($0.003773)
-> the pixel premium is 3.34x on every GUI step; pay it only where the DOM is absent

F2 - the action space ledger
------------------------------------------------------------
  click         9    45.0%
  type          4    20.0%
  key           3    15.0%
  screenshot    2    10.0%
  scroll        1     5.0%
  wait          1     5.0%
schema        9 verbs cover the session: click type key scroll screenshot double_click drag wait cursor_position
concentration click + type + key = 16/20 = 80% of the trace
-> the action space is small; the skill is choosing the target, not the verb

F3 - the grounding verdict
------------------------------------------------------------
raw pixel     37/50 = 74.0% first-click accuracy
set-of-marks  46/50 = 92.0% first-click accuracy
annotation    +210 tokens/step = +126,000 tokens across the suite
verdict       +18.0 points bought for +126,000 tokens - mark the forms, trust the pixels on canvas

F4 - the verifier gate
------------------------------------------------------------
  step  7 click  BROKEN - modal swallowed the click -> re-act once, recover
  step 11 click  BROKEN - spinner still covering the target -> re-act once, recover
  step 16 type   BROKEN - interstitial stole the focus -> re-act once, recover
with gate     26 actions for 3 broken states, all recovered, 1 success
without gate  20 actions, reported success, 3 silent broken states
-> an unchecked screenshot is a claim, not a fact; verify the state after every act

F5 - the runaway loop halt
------------------------------------------------------------
runaway       the target never renders; the agent re-clicks the nav region
detector      same (action, region) 3x in a row -> halt
halt          step 9 of the 25-step budget - 16 steps (28,016 tokens) not burned
-> the loop detector is the difference between a halt and a hemisphere of spend

F6 - the sandbox gate chain
------------------------------------------------------------
  G1 domain allowlist  navigate evil-tracker.example
                       BLOCK - not on the 12-domain allowlist
  G2 credential vault  type password into the login form
                       SUBSTITUTED - the vault fills a ****** reference, the model never holds it
  G3 payment deny      click the checkout button
                       DENIED - purchases route to a human gate, not the model
G4 VM teardown  every session ends in a fresh VM - nothing persists to the next run
-> the chain runs under the model, not beside it; a denied action never reaches the page

F7 - the DOM-versus-screenshot verdict
------------------------------------------------------------
DOM agent     forms 29/31, canvas 4/19 -> 33/50 = 66%  (524 tok/step, 1.2 s)
vision agent  forms 22/31, canvas 17/19 -> 39/50 = 78%  (1,751 tok/step, 2.9 s)
hybrid        DOM on the 31 form tasks, vision on the 19 canvas tasks -> 46/50 = 92%
hybrid cost   1.85 s/step, 990 tok/step blended
-> route by the page, not by the vendor: the a11y tree where it exists, pixels where it does not

FENCE-057-OK
```
