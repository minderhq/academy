---
Document ID: 7300-ORCHESTRATION-README
Title: "[7300]: Multi-Agent Orchestration"
Last Updated: 2026-10-04
Status: Complete
Difficulty: Advanced
Prerequisites: []
Estimated Time: 11 hours
Tags: ['module', 'agents', 'orchestration']
---

# [7300]: Multi-Agent Orchestration

## Overview

This module covers frameworks and patterns for orchestrating multiple AI agents that collaborate on complex tasks. You'll learn about hierarchical, sequential, and parallel agent architectures using frameworks like LangGraph, AutoGen, and CrewAI.

---

## Module Documents

| Document | Description | Difficulty | Time |
|----------|-------------|------------|------|
| [7301: Orchestration](./7301-Orchestration.md) | Multi-agent collaboration patterns | ⭐⭐⭐ | 4 hrs |
| [7302: Communication Protocols](./7302-Communication-Protocols.md) | Agent-to-agent communication patterns | ⭐⭐⭐ | 4 hrs |
| [7303: Framework Comparison](./guides/7303-Framework-Comparison.md) | AutoGen vs LangGraph vs others | ⭐⭐⭐ | 3 hrs |
| [7304: Event Buses, Deadlocks, and Human Gates](./7304-Event-Buses-Deadlocks-and-Human-Gates.md) | Delivery semantics, deadlocks, human gates | ⭐⭐⭐ | 3 hrs |

---

## Learning Objectives

After completing this module, you will:
- ✅ Understand multi-agent orchestration patterns
- ✅ Design hierarchical agent systems
- ✅ Implement sequential and parallel agent workflows
- ✅ Choose the right framework (AutoGen, LangGraph, CrewAI)
- ✅ Handle agent communication and coordination
- ✅ Debug and monitor multi-agent systems
- ✅ Read a delivery ledger, a wait-for graph, and a mid-run human gate

---

## Prerequisites

- **Programming:** Python, async/await patterns
- **Previous:** [7100: Agent Architecture](../7100-architecture/), [7200: Tool Calling](../7200-tools/)

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

---

## Key Concepts

### What is Multi-Agent Orchestration?

```text
┌─────────────────────────────────────────────────────────────┐
│                  Multi-Agent Orchestration                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Single Agent                  Multi-Agent System           │
│  ────────────                  ────────────────────          │
│                                                              │
│  ┌─────────┐                   ┌─────────────────┐            │
│  │  Agent  │                   │  Orchestrator   │            │
│  │         │                   │                 │            │
│  └────┬────┘                   └────────┬────────┘            │
│       │                               │                      │
│       │                        ┌──────┴──────┐               │
│       │                        │             │               │
│       ▼                        ▼             ▼               │
│   [All Tasks]             [Agent 1]    [Agent 2]    [Agent 3]│
│                            (Research)  (Writer)    (Reviewer) │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Orchestration Patterns

| Pattern | Description | Use Case | Example |
|---------|-------------|----------|---------|
| **Hierarchical** | Manager coordinates workers | Complex task breakdown | Research → Write → Review |
| **Sequential** | Pipeline processing | Multi-step workflows | Extract → Transform → Load |
| **Parallel** | Independent agents | Speed optimization | Analyze multiple docs simultaneously |
| **Consensus** | Voting mechanism | Decision making | Multiple agents vote on best answer |
| **Debate** | Agents critique each other | Quality improvement | Refine answers through discussion |

---

## Hierarchical Orchestration

### Structure

```text
┌─────────────────────────────────────────────────────────────┐
│                     Hierarchical Pattern                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                       User Request                          │
│                             │                               │
│                             ▼                               │
│                    ┌─────────────────┐                      │
│                    │  Manager Agent  │                      │
│                    │  (Planner)      │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│            ┌────────────────┼────────────────┐              │
│            │                │                │              │
│            ▼                ▼                ▼              │
│    ┌───────────┐     ┌───────────┐    ┌───────────┐        │
│    │ Worker 1  │     │ Worker 2  │    │ Worker 3  │        │
│    │ (Research)│     │ (Writer)  │    │ (Coder)   │        │
│    └─────┬─────┘     └─────┬─────┘    └─────┬─────┘        │
│          │                 │                 │              │
│          └─────────────────┴─────────────────┘              │
│                            │                                │
│                            ▼                                │
│                    Manager Aggregates                       │
│                            │                                │
│                            ▼                                │
│                      Final Response                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Implementation (LangGraph)

```python
from langgraph.graph import StateGraph
from typing import TypedDict

class AgentState(TypedDict):
    messages: list[str]
    current_step: str
    research_data: dict
    draft_content: str
    final_output: str

def manager_node(state: AgentState):
    """Manager decides which worker to call next"""
    if not state.get("research_data"):
        return {"current_step": "research"}
    elif not state.get("draft_content"):
        return {"current_step": "write"}
    else:
        return {"current_step": "review"}

def research_worker(state: AgentState):
    """Worker 1: Gather information"""
    # Research logic here
    return {"research_data": {...}}

def writer_worker(state: AgentState):
    """Worker 2: Create content"""
    # Writing logic here
    return {"draft_content": "..."}

def reviewer_worker(state: AgentState):
    """Worker 3: Review and refine"""
    # Review logic here
    return {"final_output": "..."}

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("manager", manager_node)
workflow.add_node("research", research_worker)
workflow.add_node("write", writer_worker)
workflow.add_node("review", reviewer_worker)

# Add edges
workflow.add_conditional_edges("manager", {
    "research": "research",
    "write": "write",
    "review": "review",
    "end": END
})

workflow.add_edge("research", "manager")
workflow.add_edge("write", "manager")
workflow.add_edge("review", END)
```

---

## Sequential Orchestration

### Structure

```text
Task → Agent 1 → Result 1 → Agent 2 → Result 2 → Agent 3 → Final Result
```

### Example: Document Processing Pipeline

```python
class SequentialWorkflow:
    def __init__(self):
        self.agents = [
            ExtractionAgent(),
            TransformationAgent(),
            LoadingAgent()
        ]

    def execute(self, document):
        result = document
        for agent in self.agents:
            result = agent.process(result)
            print(f"{agent.name} completed: {result}")
        return result
```

---

## Parallel Orchestration

### Structure

```text
                    User Request
                         │
                    ┌────┴────┐
                    ▼         ▼         ▼
               Agent 1    Agent 2   Agent 3
                    │         │         │
                    └────┬────┘         │
                         │              │
                    ┌────┴────┐         │
                    ▼         ▼         ▼
               Aggregate → Enhance → Final
```

### Implementation (AutoGen)

```python
import asyncio

import autogen

async def parallel_analysis(task: str, documents: list[str]):
    """Run multiple agents in parallel"""

    # Create specialized agents
    researcher = autogen.AssistantAgent(
        name="researcher",
        system_message="You research and extract key information."
    )

    analyst = autogen.AssistantAgent(
        name="analyst",
        system_message="You analyze and provide insights."
    )

    summarizer = autogen.AssistantAgent(
        name="summarizer",
        system_message="You summarize complex information."
    )

    # Run agents in parallel
    results = await asyncio.gather(
        researcher.run(task, documents[0]),
        analyst.run(task, documents[1]),
        summarizer.run(task, documents[2])
    )

    # Aggregate results
    aggregated = aggregate_results(results)

    return aggregated
```

### Task Discipline: Spawn, Budget, Cancel

`asyncio.gather` is the fan-out-with-a-join tool: every call must
finish before the function returns. Agent fleets also need three
disciplines gather does not cover — work with an *independent
lifetime*, a *wall-clock budget*, and a *shutdown path*.

**Spawn and hold the reference.** `asyncio.create_task` schedules a
coroutine to run concurrently, but the event loop keeps only a
*weak* reference to the task: drop every strong reference and the
garbage collector may collect the task mid-flight, and its work
silently never completes. Hold tasks in a collection that outlives
the spawn site and release each one when it finishes:

```python
import asyncio

background_tasks: set[asyncio.Task] = set()


def spawn(runner) -> asyncio.Task:
    """Independent work: create_task - and hold the reference."""
    task = asyncio.create_task(runner())
    background_tasks.add(task)                # strong ref keeps it alive
    task.add_done_callback(background_tasks.discard)   # finished -> release
    return task


async def with_budget(agent_call, budget_s: float) -> str:
    """wait_for owns the wall-clock budget and cancels on timeout."""
    return await asyncio.wait_for(agent_call(), timeout=budget_s)


async def poll(stop: asyncio.Event, out: asyncio.Queue) -> None:
    """Cooperative shutdown: cleanup, then re-raise - never swallow."""
    while not stop.is_set():
        try:
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            out.put_nowait({"event": "cancelled"})   # observable, never silent
            raise
```

**Budget every task.** Awaited work can still hang forever. The fleet
rule is *timeouts everywhere* ([7302](./7302-Communication-Protocols.md)):
`asyncio.wait_for` is the async mechanism — it cancels the
wrapped awaitable itself when the budget expires and raises
`TimeoutError`. On Python 3.11+ the scoped form
`async with asyncio.timeout(budget_s):` applies the same budget to a
whole block.

**Cancel cooperatively.** Shutdown and budget expiry both arrive as
`task.cancel()`, which raises `asyncio.CancelledError` inside the task
at its next `await`. The contract: catch it only to clean up —
flush state, release resources — then re-raise. Swallowing it
turns cancellation into a silent no-op, the same failure class the
broad-handler lesson teaches.

### Bound the Fan-Out: Semaphore Caps and gather's Error Contract

`asyncio.gather` schedules every call at once. A fleet that gathers
500 document calls makes 500 simultaneous provider requests — the
limiter trips ([7302](./7302-Communication-Protocols.md) teaches the
429 answer), latency queues, and memory balloons with every in-flight
task. The missing discipline is bounding the fan-out **before** the
limiter trips: acquire an `asyncio.Semaphore(limit)` around each
call, and at most `limit` requests are ever in flight. This is the
client-side sibling of the server-side rate limiter — the semaphore
is how you avoid needing the retry loop at all.

The second hole is gather's error contract. By default the first
exception propagates and the call raises immediately — one bad
item discards every sibling result the fleet already computed. With
`return_exceptions=True` the contract changes: failures come back in
the results list as exception objects, successes as values. That is
the shape a fan-out over N items actually wants — partial results
plus a per-item failure list the caller triages (retry, log, or
dead-letter — observable, never silent):

```python
import asyncio
from collections.abc import Awaitable, Callable


async def bounded(sem: asyncio.Semaphore, call: Callable[[], Awaitable[str]]) -> str:
    """One provider call under the concurrency cap."""
    async with sem:
        return await call()


async def fan_out(calls: list[Callable[[], Awaitable[str]]], limit: int = 8):
    """Bounded fan-out: at most `limit` in flight, failures never lose the fleet."""
    sem = asyncio.Semaphore(limit)
    results = await asyncio.gather(
        *(bounded(sem, call) for call in calls),
        return_exceptions=True,   # one bad item must not discard the rest
    )
    ok = [r for r in results if not isinstance(r, BaseException)]
    failed = [r for r in results if isinstance(r, BaseException)]
    return ok, failed
```

### Batch the Bulk: Provider Batch APIs for Latency-Tolerant Work

The fan-out you just bounded by hand is for work you need now.
Bulk work is different: classify 50k documents, generate dataset
variants, run nightly evals — latency-tolerant,
cost-dominated. Every major provider ships a **Batch API** for
exactly this shape: upload a JSONL file of requests, the provider
runs the whole fleet on its own schedule at roughly half the
per-token price (check current pricing), and every job completes
inside a 24-hour window.

The contract to learn is `custom_id` — your join key.
Each JSONL line carries the id you chose; the results file echoes
it on every line, one result per input, each holding either the
response or a per-item error. Never an all-or-nothing exception —
the same partial-results-plus-failure-list shape as `gather` with
`return_exceptions=True` above, enforced by the provider instead
of your partition. You poll for status instead of holding a
connection open; the terminal states are explicit (`completed`,
`failed`, `expired`, `cancelled`):

```python
import json
import time


def batch_line(custom_id: str, model: str, messages: list[dict]) -> str:
    """One JSONL row of a Batch input file - custom_id is the join key."""
    return json.dumps(
        {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {"model": model, "messages": messages},
        }
    )


def submit_and_poll(client, input_file_id: str, poll_s: float = 60.0):
    """Upload out-of-band, then poll - batch is async by design."""
    batch = client.batches.create(
        input_file_id=input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    while batch.status not in {"completed", "failed", "expired", "cancelled"}:
        time.sleep(poll_s)
        batch = client.batches.retrieve(batch.id)
    return batch
```

Anthropic's face of the same discipline: `client.messages.batches`,
each request carrying `custom_id` plus params, results fetched with
`.results`. The boundary line is user-visible latency: a human
waiting on an answer cannot wait 24 hours, so anything in the
request path stays on the bounded live fan-out; anything the fleet
can afford to defer moves to batch. The savings are measurable —
the [1503](../../../phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md)
observability loop watching cost per document is where the discount
shows up.

### Persistence: Checkpoint the Graph, Resume by thread_id

Every graph in this module was volatile: build the StateGraph,
invoke, done — the process ends and the state dies with it.
Long-running fleets cannot afford that. LangChain 1.x made the
decision explicit: memory is a checkpointer, and a checkpointer
changes what invoke means — after every super-step (one
round of node execution) the full state is written to a checkpoint,
keyed by the config's `thread_id`.

The `thread_id` is the durable join key. Same graph, same
`thread_id`, same thread: re-invoke with the same config and the
graph resumes where the checkpoint left off instead of starting
over — crash recovery and human-in-the-loop approval in one
mechanism (interrupt the graph for review, resume on approval):

```python
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class RunState(TypedDict):
    query: str
    answer: str


def retrieve(state: RunState) -> dict:
    return {"answer": f"answered: {state['query']}"}


builder = StateGraph(RunState)
builder.add_node("retrieve", retrieve)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", END)
graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "research-run-42"}}
first = graph.invoke({"query": "transformers"}, config=config)
# Crash, restart, re-invoke: the same thread_id resumes the same
# thread instead of starting a new conversation.
again = graph.invoke({"query": "explain attention"}, config=config)
```

The resume face is only half of the checkpointer story—the same mechanism carries approval. `interrupt()` pauses the graph mid-flight for a human decision: call it inside a node when the state reaches a gate the operator must clear, and the graph writes its checkpoint exactly as it does after every super-step and stops without reaching the end. The pause is resumable by the same `thread_id`—re-invoke with `Command(resume=...)` and the resume value arrives as `interrupt()`'s return value inside the node, so the operator's verdict flows back through the graph's own state machine:

```python
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ReviewState(TypedDict):
    query: str
    answer: str


def review(state: ReviewState) -> dict:
    answer = f"draft answer: {state['query']}"
    verdict = interrupt({"draft": answer})
    if verdict == "approve":
        return {"answer": answer}
    return {"answer": f"{answer} (revised after rejection)"}


builder = StateGraph(ReviewState)
builder.add_node("review", review)
builder.add_edge(START, "review")
builder.add_edge("review", END)
graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "review-42"}}
# First invoke pauses inside review: the checkpoint is written and
# the graph returns without reaching the end.
paused = graph.invoke({"query": "customer refund"}, config)
# Same thread_id, resume value in hand: the graph continues past
# the interrupt and the verdict becomes interrupt()'s return value.
final = graph.invoke(Command(resume="approve"), config)
print(final["answer"])
```

The verdict is ordinary data—approval, revision, or escalation route through the same graph that computed the draft, and every branch is checkpointed like any other.

`InMemorySaver` is the learning shape — it dies with the
process, which defeats the point in production; the same
`compile(checkpointer=...)` call takes SqliteSaver or PostgresSaver
for durability. The
[practice exercises](./assessment/PRACTICE.md) drive the
`create_agent` face of the same mechanism — a checkpointer
plus a `thread_id` config — so the graph API here and the
agent API there are one discipline, not two.

---

## Framework Comparison

### AutoGen (Microsoft)

**Strengths:**
- Built-in conversation patterns
- Code interpreter support
- Human-in-the-loop
- Strong multi-agent capabilities

**Weaknesses:**
- Microsoft-centric
- Less flexible state management

**Best For:**
- Conversational agents
- Code generation tasks
- Human-AI collaboration

### LangGraph (LangChain)

**Strengths:**
- Flexible state management
- Cycle detection
- Persistence and checkpoints
- Integration with LangChain ecosystem

**Weaknesses:**
- Steeper learning curve
- More boilerplate code

**Best For:**
- Complex workflows
- Stateful applications
- Production deployments

### CrewAI

**Strengths:**
- Simple, intuitive API
- Role-based agents
- Built-in tools
- Good for beginners

**Weaknesses:**
- Less flexible than LangGraph
- Smaller community

**Best For:**
- Quick prototyping
- Simple multi-agent systems
- Learning agent patterns

---

## Implementation Example

### Multi-Agent Research System

```python
from dataclasses import dataclass

@dataclass
class AgentResponse:
    agent_name: str
    content: str
    confidence: float
    metadata: dict

class MultiAgentOrchestrator:
    """
    Orchestrates multiple specialized agents for complex tasks.
    """
    def __init__(self):
        self.agents = {
            "researcher": ResearchAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
            "critic": CriticAgent()
        }

    async def execute_task(self, task: str, pattern: str = "hierarchical"):
        """
        Execute task using specified orchestration pattern.

        Args:
            task: The task to accomplish
            pattern: "hierarchical", "sequential", "parallel", "debate"

        Returns:
            Final aggregated response
        """
        if pattern == "hierarchical":
            return await self._hierarchical_execute(task)
        elif pattern == "sequential":
            return await self._sequential_execute(task)
        elif pattern == "parallel":
            return await self._parallel_execute(task)
        elif pattern == "debate":
            return await self._debate_execute(task)
        else:
            raise ValueError(f"Unknown pattern: {pattern}")

    async def _hierarchical_execute(self, task: str):
        """Manager-worker pattern"""
        # Manager plans the task
        plan = await self.agents["manager"].plan(task)

        # Workers execute subtasks
        results = []
        for subtask in plan.subtasks:
            agent = self.agents[subtask.agent_type]
            result = await agent.execute(subtask)
            results.append(result)

        # Manager aggregates results
        final = await self.agents["manager"].aggregate(results)
        return final

    async def _debate_execute(self, task: str, rounds: int = 3):
        """Agents debate and refine their answers"""
        responses = []

        for round_num in range(rounds):
            round_responses = []

            # Each agent responds
            for name, agent in self.agents.items():
                if round_num == 0:
                    # Initial response
                    response = await agent.respond(task)
                else:
                    # Response to other agents' inputs
                    context = "\n".join([
                        f"{r.agent_name}: {r.content}"
                        for r in responses[-1]
                    ])
                    response = await agent.respond(
                        f"{task}\n\nPrevious inputs:\n{context}"
                    )

                round_responses.append(response)

            responses.append(round_responses)

        # Select best response (highest confidence)
        final = max(responses[-1], key=lambda r: r.confidence)
        return final
```

---

## Related Experiments

| Experiment | Description |
|------------|-------------|
| [EXP_7201: Multi-Agent](../../../../experiments/EXP_7201_MULTI_AGENT.md) | Build multi-agent system |
| [LAB-008: Agent Fleet](../../../learning-resources/labs/LAB-008-Agent-Fleet.md) | Build production multi-agent system |

---

## Assessment

- **Quiz:** [assessment/QUIZ.md](assessment/QUIZ.md) - Test your orchestration knowledge
- **Practice:** [assessment/PRACTICE.md](assessment/PRACTICE.md) - Implement multi-agent patterns

---

## See Also

- **Previous Module:** [7200: Tool Calling](../7200-tools/)
- **Next Module:** [7400: Agent Memory](../7400-memory/) - Persistent memory systems
- **Guide:** [7303: Framework Comparison](./guides/7303-Framework-Comparison.md)
- **Phase Overview:** [Phase 7 README](../README.md)

---

## Common Issues

| Issue | Solution |
|-------|----------|
| **Agents stuck in loops** | Use LangGraph's cycle detection |
| **Poor agent coordination** | Implement clear communication protocol |
| **Slow execution** | Use parallel execution where possible |
| **Inconsistent results** | Add consensus or debate pattern |

---

## Quick Reference

### Pattern Selection Guide

| Scenario | Best Pattern | Framework |
|----------|--------------|-----------|
| Research task | Hierarchical | AutoGen |
| Document processing | Sequential | LangGraph |
| Multiple queries | Parallel | AutoGen/LangGraph |
| Content refinement | Debate | Custom |
| Production system | State graph | LangGraph |

### Communication Patterns

| Pattern | Description | Complexity |
|---------|-------------|------------|
| **Direct** | One agent calls another | Low |
| **Broadcast** | One agent → all agents | Medium |
| **Subscribe** | Agents subscribe to topics | High |
| **Shared Memory** | Agents read/write shared state | Medium |

---

**Module Difficulty:** ⭐⭐⭐⭐ Advanced
**Estimated Time:** 10 hours total

## Module Contents

- [7302: Communication Protocols](./7302-Communication-Protocols.md)
- [7304: Event Buses, Deadlocks, and Human Gates](./7304-Event-Buses-Deadlocks-and-Human-Gates.md)
