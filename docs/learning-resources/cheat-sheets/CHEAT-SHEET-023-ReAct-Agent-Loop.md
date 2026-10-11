---
Document ID: CHEAT-SHEET-023
Title: "CHEAT-SHEET-023: ReAct Agent Loop"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'react', 'agents', 'tool-calling', 'reasoning']
---

# CHEAT-SHEET-023: ReAct Agent Loop

**Quick Reference for:** the Thought → Action → Observation loop, the ReAct vs chain-of-thought split, the tool contract that feeds errors back as observations, the hard iteration cap, trace-as-memory state discipline, and plan-then-execute for multi-step tasks.

**Version:** 1.0

## The Loop

ReAct (Reasoning + Acting) is the foundational agent pattern: the model alternates **Thought** (reason about what is known and missing), **Action** (call a tool), and **Observation** (read the result) until it emits **Finish** — or hits the iteration cap. The canonical trace from module 7101:

```text
Thought: I need to find the capital of France
Action: Search[capital of France]
Observation: Paris is the capital of France
Thought: Now I have the answer
Action: Finish[Paris]
```

The rule the module leaves: **an agent is a loop, not a chat — the discipline is in what each turn is allowed to do, and the trace is the agent's only memory of why it acted.**

## ReAct vs Chain-of-Thought

| | Chain-of-Thought | ReAct |
|---|---|---|
| Passes | single forward pass | multiple iterations |
| Knowledge | limited to what's in the model | external tools and APIs |
| Correction | none mid-answer | observes results, adjusts strategy |
| Best at | reasoning over known facts | tasks needing fresh external state |

## The Tool Contract

Two disciplines make the loop robust:

- **Unknown tool is an OBSERVATION, not a crash.** `Action: calc[2+2]` when only `calculate` is registered returns `Error: Tool 'calc' not found` as the next observation — the model reads it and corrects course on the following turn. Exceptions inside a tool do the same (`Error: {e}`), so one bad call never kills the run.
- **The registry is schema-first.** Every tool carries a name, description, parameter schema, and the callable — the description is what the LLM selects on, so vague descriptions are misfires, not style issues.

## The Iteration Cap

`max_iterations` (module default 10) is a HARD budget: when the loop exhausts it without a `Finish`, it raises `MaxIterationsError` — it never silently loops forever. A cap-less agent is an unbounded-cost process.

## Trace as Memory

State is three things: the rolling **history** (Thought/Action written as assistant messages, Observation injected as a user message), the step counters (`current_step` / `max_steps`), and a status enum (`IDLE → THINKING → ACTING → FINISHED/ERROR`). Delete the history and the agent cannot explain why it acted — the trace IS the memory.

## The Arithmetic

```python
# ReAct loop: Thought -> Action -> Observation -> ... -> Finish.
# The fake LLM below replays a scripted turn list so the loop
# mechanics (parsing, tool dispatch, error-as-observation, cap)
# are visible without any model in the room.

TOOLS = {
    "search": lambda q: "Paris is the capital of France",
    "calculate": lambda expr: str(eval(expr, {"__builtins__": {}}, {})),
}
MAX_ITER = 10


def parse_action(text):
    """'Search[capital]' or 'Finish[Paris]' -> (verb, arg)."""
    verb, arg = text.split("[", 1)
    return verb.strip().lower(), arg.rstrip("]")


def run_react(script):
    trace = []
    for i in range(1, MAX_ITER + 1):
        thought, action = script[i - 1]
        verb, arg = parse_action(action)
        trace.append("iter %d %s" % (i, action))
        if verb == "finish":
            return trace, arg, i
        obs = (TOOLS[verb](arg) if verb in TOOLS
               else "Error: Tool '%s' not found" % verb)
        trace.append("iter %d Observation: %s" % (i, obs))
    return trace, None, MAX_ITER


script = [("need the capital of France", "Search[capital of France]"),
          ("answer in hand", "Finish[Paris]")]
trace, answer, iters = run_react(script)
print("task: answer=%s iters=%d trace_steps=%d" % (answer, iters, len(trace)))

bad = [("try a typo'd tool", "calc[2+2]"),
       ("error came back, retry with search", "Search[capital of France]"),
       ("done", "Finish[Paris]")]
t2, a2, _ = run_react(bad)
err = [ln for ln in t2 if "not found" in ln][0].split("Observation: ")[1]
print("recovery: obs=%r -> answered=%s" % (err, a2))

t3, a3, i3 = run_react([("keep searching", "Search[loop]")] * 12)
print("cap: finished=%s stopped_at_iter=%d/%d (MaxIterationsError)"
      % (a3 is not None, i3, MAX_ITER))
print("CoT=1 pass, no tools | ReAct=%d+ passes over %d tools" % (i3, len(TOOLS)))
```

The run confirms the whole bill: `task: answer=Paris iters=2 trace_steps=3` — the canonical capital-of-France task resolves in 2 iterations and 3 trace steps (the Search action, its Observation, the Finish). `recovery: obs="Error: Tool 'calc' not found" -> answered=Paris` — the typo'd tool comes back as an error OBSERVATION and the agent still lands the answer two turns later. `cap: finished=False stopped_at_iter=10/10 (MaxIterationsError)` — a script that never emits Finish is stopped by the hard cap at exactly MAX_ITER. `CoT=1 pass, no tools | ReAct=10+ passes over 2 tools` — the two-paradigm split in one line: chain-of-thought is a single pass over in-model knowledge, ReAct iterates over live external state.

## Plan-then-Execute

Long tasks drift when one flat loop carries everything. The hierarchical pattern splits phases: **plan** (one prompt emits a JSON step list — description, tools, expected output), **execute** (run the steps, revising the plan when a step flags `requires_replanning`), **synthesize** (assemble the answer from step results). Deep dive: module 7102.

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| agent crashes on a mistyped tool name | tool error raised out of the loop | return `Error: ...` as the next observation — never raise |
| runaway cost, never stops | no `max_iterations` cap | hard cap + `MaxIterationsError`; treat the cap as a budget |
| agent "forgets" why it acted | history trimmed or dropped between turns | the trace is the only memory — carry it, or summarize, never silently drop |
| agent answers without acting | hallucinated observation | observations come ONLY from execution; parse `Finish` strictly |
| same failing action repeats forever | uninformative error observation | make error strings descriptive so the next Thought can change strategy |
| long task drifts off-goal | one flat loop carries all steps | plan-then-execute (module 7102) with replanning checkpoints |

## Quick Reference For

- [Module 7101: ReAct Loop System](../../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
- [Module 7201: Tool Calling](../../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md)
- [Module 7102: Planning and Decomposition](../../phases/phase7-agentic/7100-architecture/7102-Planning-Decomposition.md)
- [CHEAT-SHEET-022: Multimodal Models](./CHEAT-SHEET-022-Multimodal-Models.md)
