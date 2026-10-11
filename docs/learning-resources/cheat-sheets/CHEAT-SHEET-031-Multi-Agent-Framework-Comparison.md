---
Document ID: CHEAT-SHEET-031
Title: "CHEAT-SHEET-031: Multi-Agent Framework Comparison"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'agents', 'multi-agent', 'orchestration', 'framework-comparison']
---

# CHEAT-SHEET-031: Multi-Agent Framework Comparison

**Quick Reference for:** the 8-row framework comparison matrix and the boolean scorecards inside it, the version reality (Swarm is archived; "AutoGen" names two different APIs), the executable decision table that maps task shape to framework, the hybrid split - graph owns the flow, agent owns the talk - and the honest resource ledger. CHEAT-SHEET-024 owns the planning-and-routing surface of multi-agent systems; CHEAT-SHEET-027 owns the MCP tool layer; CHEAT-SHEET-030 owns the wire between agents; this sheet owns the *build* decision underneath all of them - which framework to install for a given task shape. Choose by state model and operational fit, not feature lists: the framework you can debug in production beats the one that demos best.

## The Matrix: Four State Models

| feature | AutoGen | LangGraph | CrewAI | Swarm (OpenAI) |
|---|---|---|---|---|
| **Architecture** | Conversational | State Machine | Role-based | Orchestrated |
| **LLM Support** | OpenAI, Azure, Hugging Face | Any (via LangChain) | OpenAI, Claude, Local | OpenAI only |
| **Memory** | Built-in | Via checkpoint | Built-in | Via context |
| **Tool Calling** | Yes | Yes | Yes | Yes |
| **Human-in-Loop** | Yes | Yes | Yes | No |
| **Local Models** | Possible | Yes | Yes | No |
| **Visualization** | Basic | Good | Basic | None |
| **Maturity** | High | High | Medium | Beta |

The state model is the row that decides everything else. AutoGen's conversational architecture makes the chat between agents the control flow - natural for code-generation and review pipelines, but execution flow is harder to steer. LangGraph is a state machine - typed state, nodes, conditional edges, checkpoint/resume - so execution is deterministic and debuggable, at the price of boilerplate. CrewAI is role-based - a `role`/`goal`/`backstory` trio per agent, `Task(description, expected_output, agent)`, `Process.sequential` - the clearest pipeline when the team metaphor fits the domain. Swarm was OpenAI's 2024 teaching framework and is now archived.

The boolean rows are scorecards, not differentiators: **tool calling is a solved problem - 4/4**; **human-in-the-loop is 3/4** (Swarm: No); **local models are 3/4** (Swarm: No). The decision lives in the qualitative rows - architecture, memory model, visualization, maturity - and in the two version-reality notes below, which the matrix cannot show.

## Version Reality: Two AutoGens and an Archive

Two notes before any install command:

1. **Swarm is archived.** OpenAI's 2024 experimental teaching framework was superseded by the **OpenAI Agents SDK** (handoffs + guardrails, GA) - treat the Swarm column as historical.
2. **"AutoGen" names two things.** The community continuation of the 0.2-style API ships as **AG2**; Microsoft's rewrite ships as **autogen-agentchat 0.4+** with a fundamentally different event-driven `SingleThreadedAgentRuntime`. Same roles, different skeleton - port only after the conversation logic is stable.

```text
"AutoGen" 0.2-style  = AG2 (community)    uv pip install pyautogen
"AutoGen" 0.4+       = Microsoft rewrite  uv pip install autogen-agentchat autogen-core
Swarm (OpenAI)       = ARCHIVED           superseded by the OpenAI Agents SDK (GA)
```

## The Decision Table

The suitability table as executable rules - conversational work goes to AutoGen, anything stateful/parallel/long goes to LangGraph, and the short single-thread default is AutoGen:

| task shape | recommended | reason |
|---|---|---|
| Simple (1-2 steps) | AutoGen | easiest to set up |
| Medium (3-5 steps) | LangGraph | better control |
| Complex (5+ steps) | LangGraph | state management |
| Conversational | AutoGen | natural fit |
| Stateful | LangGraph | checkpoints |
| Parallel | LangGraph | concurrent nodes |

The four canonical recommendations this table produces: a quick 2-step script -> **AutoGen**; a support chatbot -> **AutoGen**; a pipeline with resume -> **LangGraph**; a fan-out analysis -> **LangGraph**. Sweep the full decision grid - conversational x stateful x parallel x steps in {2, 4, 6} = **24 combinations** - and the tally lands **AutoGen 13 / LangGraph 11 / CrewAI 0**. CrewAI appears nowhere because its role-based pipeline is an **orthogonal** choice: pick it when the team metaphor fits the domain, not when a task-shape rule fires.

## The Hybrid: Graph Owns the Flow, Agent Owns the Talk

The two frameworks compose. LangGraph owns the orchestration graph - edges, conditional edges, checkpoints: *what happens next*. An AutoGen agent does the talking inside each node - prompts, tools, retries: *what gets said*. The fence's minimal hybrid walks code -> review -> END: the graph takes **2 checkpoint decisions and 2 routing decisions**, the agent takes **2 turns**, and the review's accept verdict is a graph decision while the LGTM is agent output. Before this shape ships, **pin both frameworks in `pyproject.toml`** - their release cadences are independent.

## Resource Reality

| framework | memory | tokens/call | overhead |
|---|---|---|---|
| AutoGen | ~2GB | ~2000 | Medium |
| LangGraph | ~1.5GB | ~1500 | Low |
| CrewAI | ~2GB | ~1800 | Medium |

Order-of-magnitude estimates for a typical two-agent conversation, **not benchmarks** - conversation length and tool calls dominate both numbers. LangGraph lands lowest on every column; the ranking is more stable than the values. Measure your own workload before provisioning.

## Known Failure Modes

| failure | lesson |
|---|---|
| Choose by feature list | the demo-winning framework you cannot debug in production loses - pick by state model and operational fit |
| Treat "AutoGen" as one thing | AG2 (0.2-style) and autogen-agentchat 0.4+ are different runtimes - pin which one you mean |
| Build on Swarm | archived; the OpenAI Agents SDK is the successor - treat Swarm columns as historical |
| Ship a hybrid with unpinned frameworks | two independent release cadences - pin both in pyproject.toml |
| Read resource estimates as benchmarks | conversation length and tool calls dominate - trust the ranking, not the values |

## References

- Wu et al., *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation*, 2023
- LangChain, *LangGraph* - langchain-ai.github.io/langgraph
- CrewAI, *crewAI* - docs.crewai.com
- OpenAI, *OpenAI Agents SDK* - openai.github.io/openai-agents-python (Swarm's successor)

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Fan-in nodes overwrite each other's output | plain dict state | `Annotated[..., operator.add]` reducer merges lists instead of overwriting |
| Entry-point deprecation nags | legacy spelling | START/END pseudo-nodes: `add_edge(START, "research")` - set_entry_point still works but is legacy |
| CrewAI picked for a stateful pipeline | team metaphor vs task shape | run the decision table - stateful/parallel/long goes LangGraph; CrewAI when the roles fit the domain |
| 0.2 code breaks after "upgrading AutoGen" | installed the 0.4+ rewrite | different skeleton, event-driven runtime; port after conversation logic is stable, pin versions |
| Simple task drowning in graph boilerplate | wrong tool for the shape | decision table: conversational or <=2 steps goes AutoGen |
| Framework churn breaks the hybrid | unpinned dependencies | pin both in pyproject.toml; graph owns flow, agent owns talk |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 7303: Multi-Agent Framework Comparison](../../phases/phase7-agentic/7300-orchestration/guides/7303-Framework-Comparison.md) | this sheet's source module - the full comparison with version-pinned code |
| [Module 7301: Orchestration](../../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md) | the planning-and-routing layer above any framework choice |
| [Module 7302: Multi-Agent Communication Protocols](../../phases/phase7-agentic/7300-orchestration/7302-Communication-Protocols.md) | the wire protocol the framework's transport implements |
| [CHEAT-SHEET-030: Multi-Agent Communication Protocols](CHEAT-SHEET-030-Multi-Agent-Communication-Protocols.md) | the envelope/topology/handoff surface between the agents these frameworks run |

```python
"""CHEAT-SHEET-031 reproduction: the 7303 framework decision surface.

Stdlib only - no framework installs, no network, deterministic. The
comparison matrix, the version ledger, the decision table, the hybrid
ownership split and the resource ranking are all plain data plus one
routing function, so the sheet's every number comes from this run.
"""
import itertools
import sys

sys.stdout.reconfigure(encoding="utf-8")

FRAMEWORKS = ("AutoGen", "LangGraph", "CrewAI", "Swarm")

# ------------------------------------------------- F1: the comparison matrix

MATRIX = {
    "architecture":  ("Conversational", "State Machine", "Role-based", "Orchestrated"),
    "memory":        ("Built-in", "Via checkpoint", "Built-in", "Via context"),
    "tool_calling":  (True, True, True, True),
    "human_in_loop": (True, True, True, False),
    "local_models":  (True, True, True, False),
    "visualization": ("Basic", "Good", "Basic", None),
    "maturity":      ("High", "High", "Medium", "Beta"),
}

print("F1 comparison matrix")
for feat in ("tool_calling", "human_in_loop", "local_models"):
    col = MATRIX[feat]
    miss = [name for name, hit in zip(FRAMEWORKS, col) if hit is not True]
    print(f"  {feat:14s} {col.count(True)}/4  miss: {', '.join(miss) or 'none'}")
for feat in ("architecture", "memory", "visualization", "maturity"):
    cells = " | ".join(
        f"{name}: {MATRIX[feat][i] if MATRIX[feat][i] is not None else '-'}"
        for i, name in enumerate(FRAMEWORKS)
    )
    print(f"  {feat:14s} {cells}")

# ------------------------------------------------- F2: the version ledger

VERSION_LEDGER = (
    ("Swarm", "OpenAI 2024 experiment", "ARCHIVED",
     "superseded by the OpenAI Agents SDK (handoffs + guardrails, GA)"),
    ("AutoGen 0.2-style", "community continuation = AG2", "LIVE",
     "uv pip install pyautogen"),
    ("AutoGen 0.4+", "Microsoft rewrite", "LIVE",
     "uv pip install autogen-agentchat autogen-core"),
)

print("F2 version ledger")
for name, lineage, status, note in VERSION_LEDGER:
    print(f"  {name:18s} {lineage:26s} {status:8s} {note}")

# ------------------------------------------------- F3: the decision table


def recommend_framework(steps, conversational, stateful, parallel):
    """The guide's suitability table as executable rules."""
    if conversational:
        return "AutoGen"
    if stateful or parallel or steps > 2:
        return "LangGraph"
    return "AutoGen"


CASES = (
    ("quick 2-step script", dict(steps=2, conversational=False, stateful=False, parallel=False)),
    ("support chatbot", dict(steps=4, conversational=True, stateful=False, parallel=False)),
    ("pipeline with resume", dict(steps=6, conversational=False, stateful=True, parallel=False)),
    ("fan-out analysis", dict(steps=3, conversational=False, stateful=False, parallel=True)),
)

print("F3 canonical recommendations")
for label, kwargs in CASES:
    print(f"  {label}: {recommend_framework(**kwargs)}")

# ------------------------------------------------- F4: suitability rules

SUITABILITY = (
    ("Simple (1-2 steps)", dict(steps=2, conversational=False, stateful=False, parallel=False),
     "easiest to set up"),
    ("Medium (3-5 steps)", dict(steps=4, conversational=False, stateful=False, parallel=False),
     "better control"),
    ("Complex (5+ steps)", dict(steps=6, conversational=False, stateful=True, parallel=False),
     "state management"),
    ("Conversational", dict(steps=3, conversational=True, stateful=False, parallel=False),
     "natural fit"),
    ("Stateful", dict(steps=3, conversational=False, stateful=True, parallel=False),
     "checkpoints"),
    ("Parallel", dict(steps=3, conversational=False, stateful=False, parallel=True),
     "concurrent nodes"),
)

print("F4 suitability rules with their firing condition")
tally = {"AutoGen": 0, "LangGraph": 0}
for label, kwargs, why in SUITABILITY:
    pick = recommend_framework(**kwargs)
    if kwargs["conversational"]:
        fired = "conversational"
    elif kwargs["stateful"] or kwargs["parallel"] or kwargs["steps"] > 2:
        fired = "stateful or parallel or long"
    else:
        fired = "default (short, single-thread)"
    print(f"  {label:19s} [{fired:29s}] -> {pick:9s} ({why})")
    tally[pick] += 1
print(f"  tally: LangGraph {tally['LangGraph']} / AutoGen {tally['AutoGen']}")

# ------------------------------------------------- F5: hybrid ownership split

END = "END"


class Graph:
    """The half the framework owns: edges, conditional edges, checkpoints."""

    def __init__(self):
        self.edges = {}
        self.conds = {}
        self.checkpoints = []

    def add_edge(self, src, dst):
        self.edges[src] = dst

    def add_conditional(self, node, router):
        self.conds[node] = router

    def run(self, start, speak):
        node, replies = start, []
        while node != END:
            self.checkpoints.append(node)          # graph: resume point
            replies.append(speak(node))            # agent: what gets said
            if node in self.conds:                 # graph: conditional route
                node = self.conds[node](replies)
            else:                                  # graph: plain edge
                node = self.edges[node]
        return replies


SCRIPTS = {
    "code": "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)",
    "review": "LGTM: recursion is correct",
}


def hybrid_agent(node):
    """Stand-in for an AutoGen generate_reply call - deterministic."""
    return SCRIPTS[node]


hybrid = Graph()
hybrid.add_edge("code", "review")
hybrid.add_conditional("review", lambda replies: END)   # accept verdict

print("F5 hybrid ownership ledger (code -> review -> END)")
for reply in hybrid.run("code", hybrid_agent):
    print(f"  agent turn: {reply.splitlines()[0]!r}")
print(f"  graph decisions: checkpoints={len(hybrid.checkpoints)} "
      f"routes={len(hybrid.checkpoints)}")
print("  graph owns what happens next (edges, conditions, checkpoints);")
print("  the agent owns what gets said (prompts, tools, retries)")

# ------------------------------------------------- F6: resource ledger

OVERHEAD = {"Low": 0, "Medium": 1}
RESOURCES = (
    ("AutoGen", 2.0, 2000, "Medium"),
    ("LangGraph", 1.5, 1500, "Low"),
    ("CrewAI", 2.0, 1800, "Medium"),
)

print("F6 resource ledger (order-of-magnitude estimates, not benchmarks)")
for name, mem, tok, ov in RESOURCES:
    print(f"  {name:9s} ~{mem:.1f}GB  ~{tok} tokens/call  overhead {ov}")
winner = min(RESOURCES, key=lambda r: (r[1], r[2], OVERHEAD[r[3]]))
print(f"  lowest on every column: {winner[0]} - ranking more stable than the values")

# ------------------------------------------------- F7: the full decision grid

print("F7 full decision grid: 2x2x2x3 = 24 combinations")
grid = {}
for conv, st, par, steps in itertools.product(
        (False, True), (False, True), (False, True), (2, 4, 6)):
    pick = recommend_framework(steps=steps, conversational=conv,
                               stateful=st, parallel=par)
    grid[pick] = grid.get(pick, 0) + 1
for pick in sorted(grid):
    print(f"  {pick}: {grid[pick]} combos")
print(f"  CrewAI combos: {grid.get('CrewAI', 0)}"
      " - the team metaphor is orthogonal to task shape")
```

```text
F1 comparison matrix
  tool_calling   4/4  miss: none
  human_in_loop  3/4  miss: Swarm
  local_models   3/4  miss: Swarm
  architecture   AutoGen: Conversational | LangGraph: State Machine | CrewAI: Role-based | Swarm: Orchestrated
  memory         AutoGen: Built-in | LangGraph: Via checkpoint | CrewAI: Built-in | Swarm: Via context
  visualization  AutoGen: Basic | LangGraph: Good | CrewAI: Basic | Swarm: -
  maturity       AutoGen: High | LangGraph: High | CrewAI: Medium | Swarm: Beta
F2 version ledger
  Swarm              OpenAI 2024 experiment     ARCHIVED superseded by the OpenAI Agents SDK (handoffs + guardrails, GA)
  AutoGen 0.2-style  community continuation = AG2 LIVE     uv pip install pyautogen
  AutoGen 0.4+       Microsoft rewrite          LIVE     uv pip install autogen-agentchat autogen-core
F3 canonical recommendations
  quick 2-step script: AutoGen
  support chatbot: AutoGen
  pipeline with resume: LangGraph
  fan-out analysis: LangGraph
F4 suitability rules with their firing condition
  Simple (1-2 steps)  [default (short, single-thread)] -> AutoGen   (easiest to set up)
  Medium (3-5 steps)  [stateful or parallel or long ] -> LangGraph (better control)
  Complex (5+ steps)  [stateful or parallel or long ] -> LangGraph (state management)
  Conversational      [conversational               ] -> AutoGen   (natural fit)
  Stateful            [stateful or parallel or long ] -> LangGraph (checkpoints)
  Parallel            [stateful or parallel or long ] -> LangGraph (concurrent nodes)
  tally: LangGraph 4 / AutoGen 2
F5 hybrid ownership ledger (code -> review -> END)
  agent turn: 'def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)'
  agent turn: 'LGTM: recursion is correct'
  graph decisions: checkpoints=2 routes=2
  graph owns what happens next (edges, conditions, checkpoints);
  the agent owns what gets said (prompts, tools, retries)
F6 resource ledger (order-of-magnitude estimates, not benchmarks)
  AutoGen   ~2.0GB  ~2000 tokens/call  overhead Medium
  LangGraph ~1.5GB  ~1500 tokens/call  overhead Low
  CrewAI    ~2.0GB  ~1800 tokens/call  overhead Medium
  lowest on every column: LangGraph - ranking more stable than the values
F7 full decision grid: 2x2x2x3 = 24 combinations
  AutoGen: 13 combos
  LangGraph: 11 combos
  CrewAI combos: 0 - the team metaphor is orthogonal to task shape
```
