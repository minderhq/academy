---
Document ID: 7304
Title: "7304: Event Buses, Deadlocks, and Human Gates"
Phase: 7
Module: 7300
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Tags: ['agents', 'orchestration', 'multi-agent', 'distributed', 'langgraph']
---

# 7304: Event Buses, Deadlocks, and Human Gates

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [What the Bus Promises: Delivery Semantics](#what-the-bus-promises-delivery-semantics)
- [The Wait-For Graph: Deadlock as a Cycle](#the-wait-for-graph-deadlock-as-a-cycle)
- [Why Workflows Are DAGs](#why-workflows-are-dags)
- [The Mid-Run Human Gate](#the-mid-run-human-gate)
- [One Campaign Through the Runtime](#one-campaign-through-the-runtime)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

By the end of this lesson, you will be able to:

- Name the three delivery guarantees a message bus can make and compute what each one does to the same crash trace
- Explain why the industry says "effectively once" and implement the dedup ledger that earns the phrase
- Detect a deadlock as a cycle in a wait-for graph and remove it with a global acquisition order instead of a timeout guess
- Run Kahn's algorithm as a compile-time check that rejects a feedback edge with the exact cycle set named
- Pause a mid-run agent at a sensitive action with an interrupt, serialize the run state, and resume it with an approve or a deny
- Compose all four mechanics on one campaign and read the runtime ledger that proves the composition

## Abstract

The module's own QUIZ admits three gaps this lesson fills: event-bus semantics and deadlock analysis are taught nowhere in the curriculum (Q7, Q15, Q18-Q19), mid-run human-in-the-loop approval is taught nowhere in the curriculum (Q8), and the DAG's no-cycle property as a formal definition appears nowhere in the curriculum (Q5). What the answers point at is four pieces of runtime arithmetic — a delivery ledger, a wait-for graph, a topological sort, and a checkpoint-resume pair — each one small enough to run as code, and each one deciding whether the orchestration survives contact with a crash, a cyclic request, or a human. [7301](7301-Orchestration.md) teaches the collaboration patterns and [7302](7302-Communication-Protocols.md) teaches the retry-and-backoff discipline; this lesson teaches what the transport actually promises when those retries fire, why a workflow refuses to compile with a loop in it, and where the human sits in a running graph.

## What the Bus Promises: Delivery Semantics

[7302's failure-handling section](7302-Communication-Protocols.md) teaches how to retry — jitter, backoff, Retry-After. The bus's side of that contract is delivery semantics: what the broker does to a task whose worker dies mid-execution. The three guarantees are at-most-once (ack before the work — a crash loses it), at-least-once (ack after — a crash redelivers it), and effectively-once (at-least-once plus a dedup ledger at the effect site). The industry phrase is exactly-once, but the phrase oversells: Kafka's default is at-least-once; its idempotent producer (`enable.idempotence`, on by default since 3.0 when `acks=all`) deduplicates producer retries, and full end-to-end exactly-once adds transactions plus consumers reading with `isolation.level=read_committed`. Celery puts the same choice on one flag: `acks_late=False` (the default) acks before execution — a worker crash loses the task; `acks_late=True` acks after — a crash redelivers, and Celery's own docs say to enable it only if the task is idempotent.

The same six-task trace under each promise, with the worker executing `T3` and dying before its ack:

```python
from collections import deque

TRACE = ["T0", "T1", "T2", "T3", "T4", "T5"]   # one campaign's task queue
CRASH = "T3"    # the worker executing T3 dies: T0-T2 and T4-T5 run clean

def run_delivery(mode: str) -> dict:
    seen = set()        # dedup ledger -- only the idempotent mode keeps one
    effects = []        # side effects applied to the world, in order
    executed = []       # every execution the broker handed to a worker
    lost = 0            # tasks acked-then-died, never redelivered
    dup_skips = 0       # redeliveries the ledger refused to re-apply
    crashed = False     # the T3 crash happens exactly once
    queue = deque(TRACE)
    while queue:
        task = queue.popleft()
        executed.append(task)
        if task == CRASH and not crashed:
            crashed = True
            if mode == "at-most-once":
                lost += 1                # ack first, then die: gone forever
                continue
            effects.append(task)         # the effect hits the world, then no ack
            if mode == "idempotent":
                seen.add(task)           # the ledger saw this execution
            queue.append(task)           # broker redelivers
            continue
        if mode == "idempotent":
            if task in seen:
                dup_skips += 1           # redelivered, ledger says already done
                continue                 # ack and move on
            seen.add(task)
        effects.append(task)             # the effect hits the world
    return {"executed": len(executed), "effects": len(effects),
            "distinct": len(set(effects)), "lost": lost, "dup_skips": dup_skips,
            "double_applied": len(effects) - len(set(effects))}

for mode in ["at-most-once", "at-least-once", "idempotent"]:
    r = run_delivery(mode)
    print(f"{mode:13s} executed={r['executed']} effects={r['effects']} "
          f"distinct={r['distinct']} lost={r['lost']} "
          f"dup_skips={r['dup_skips']} double_applied={r['double_applied']}")
```

The ledger is the whole difference. At-most-once hands out six executions and the world keeps five effects — `T3` is gone, silently. At-least-once loses nothing but applies seven effects for six distinct tasks: `T3`'s refund fires twice, and no broker config undoes the second one. The idempotent mode executes the same seven times, but the ledger refuses the redelivery at the effect site — six effects, one `dup_skips`, nothing lost, nothing doubled. Exactly-once delivery is a marketing name for exactly-once application, and the application is what the ledger owns.

## The Wait-For Graph: Deadlock as a Cycle

The QUIZ's deadlock answer is "agents waiting forever," which is the symptom, not the mechanic. The mechanic is a cycle in the wait-for graph: each agent holds a lock and waits for one another agent holds, and the holds close a loop. Deadlock needs four conditions at once (the Coffman conditions — mutual exclusion, hold-and-wait, no preemption, circular wait), and that list is a checklist of kills: break any one and the cycle cannot form. The kill production picks is almost always circular wait, because it has a one-line implementation: a global acquisition order every agent obeys.

Three agents, three locks, each holding one and wanting the next around the ring:

```python
HOLDS = {"writer": "db", "analyzer": "api", "mailer": "fs"}   # lock each agent holds
WANTS = {"writer": "api", "analyzer": "fs", "mailer": "db"}   # lock each agent wants

def wait_for_graph():
    owner = {lock: agent for agent, lock in HOLDS.items()}
    return {agent: owner[WANTS[agent]] for agent in HOLDS}

def find_cycle(graph, start):
    path, node = [start], graph[start]
    while node != start:
        if node in path:
            return None            # entered a different cycle, not start's
        path.append(node)
        node = graph[node]
    return path

graph = wait_for_graph()
print("wait-for:", {a: f"waits on {w} (holds {HOLDS[w]})" for a, w in graph.items()})
cycle = None
for agent in graph:
    cycle = find_cycle(graph, agent)
    if cycle:
        break
print(f"deadlocked set: {' -> '.join(cycle + [cycle[0]])} (length {len(cycle)})")

# The fix: a global acquisition order removes hold-and-wait inversion.
LOCK_ORDER = {"db": 0, "fs": 1, "api": 2}   # every agent acquires in this order

def run_ordered() -> list:
    lock_owner = {}
    pending = {a: sorted([HOLDS[a], WANTS[a]], key=lambda L: LOCK_ORDER[L])
               for a in HOLDS}
    finished, grants, stuck = [], [], False
    while any(pending.values()):
        stuck = True
        for agent in sorted(pending):
            if not pending[agent]:
                continue
            lock = pending[agent][0]
            if lock not in lock_owner:      # free: grant
                lock_owner[lock] = agent
                pending[agent].pop(0)
                grants.append(f"{agent}<-{lock}")
                stuck = False
            if not pending[agent]:          # both held: run, then release
                for L in (HOLDS[agent], WANTS[agent]):
                    if lock_owner.get(L) == agent:
                        del lock_owner[L]
                finished.append(agent)
                stuck = False
        if stuck:
            raise SystemExit("livelock -- the order guarantee says impossible")
    return grants, finished

grants, finished = run_ordered()
print(f"ordered-acquisition: {len(grants)} grants in {' '.join(grants)}, "
      f"all {len(finished)} agents finished: {finished}")
```

The naive trace deadlocks as a ring of length three: `writer -> analyzer -> mailer -> writer`, each waiting on the agent to its left, forever. The fix does not add a timeout or a retry — it reorders acquisitions so no agent ever holds a higher-ranked lock while wanting a lower-ranked one, which makes a cycle in the wait-for graph impossible by construction (a cycle would need the ranks to decrease all the way around). The same three agents and six grants now run to completion: `analyzer<-fs mailer<-db analyzer<-api mailer<-fs writer<-db writer<-api`, all three finished. The deadlock monitor is then a graph walk, not a heuristic — build the wait-for graph from who-waits-on-whom and look for a back edge.

## Why Workflows Are DAGs

The QUIZ's DAG answer is "no cycles, directed" — the definition without the reason. The reason is that an orchestrator compiles a workflow into an execution order, and the compile step is a topological sort: Kahn's algorithm repeatedly takes nodes with no unmet dependencies. When the sort stalls with nodes left over, those leftovers are exactly the nodes on a cycle, so the same pass that would schedule the workflow is the pass that rejects it — at compile time, before any agent runs. LangGraph lets a graph contain cycles at runtime (the ReAct loop of [7101](../7100-architecture/7101-ReAct-Loop-System.md) is one), but the loop is expressed as a runtime edge taken conditionally; the workflow definition itself still compiles to an acyclic schedule of the steps it will definitely run.

A six-node pipeline, then the same pipeline with the feedback edge someone always asks for:

```python
from collections import deque

WORKFLOW = {"fetch": [], "clean": ["fetch"], "embed": ["clean"],
            "index": ["embed"], "gate": ["index"], "publish": ["gate"]}

def toposort(graph):
    indeg = {n: len(deps) for n, deps in graph.items()}
    succ = {n: [] for n in graph}
    for n, deps in graph.items():
        for d in deps:
            succ[d].append(n)
    ready = deque(sorted(n for n, k in indeg.items() if k == 0))
    order = []
    while ready:
        n = ready.popleft()
        order.append(n)
        for s in sorted(succ[n]):
            indeg[s] -= 1
            if indeg[s] == 0:
                ready.append(s)
    remaining = sorted(n for n in graph if n not in order)
    return order, remaining

order, rem = toposort(WORKFLOW)
print(f"compile: 6 nodes -> topo {' -> '.join(order)}")
print(f"  remaining after Kahn: {rem if rem else 'none'}")

BAD = {k: list(v) for k, v in WORKFLOW.items()}
BAD["embed"].append("publish")            # the ask: "when publish fails, redo embed"
order2, rem2 = toposort(BAD)
print(f"with publish->embed feedback edge: topo {order2 if order2 else 'REJECTED'}")
print(f"  cycle set ({len(rem2)} nodes): {rem2}")
```

Clean, the sort resolves all six nodes in dependency order: `fetch -> clean -> embed -> index -> gate -> publish`, nothing left over. Add `embed` depending on `publish` and the sort emits what it can — `['fetch', 'clean']` — then stalls, and the four stalled nodes are named precisely: `['embed', 'gate', 'index', 'publish']`. That list is the compile error, not a warning to ignore: the runtime has no order in which to run those four, so it refuses the graph before spending a token. The sanctioned way to want a retry is a wrapper that re-invokes the compiled graph — the iteration lives outside the DAG, one level up, and the compile check stays green.

## The Mid-Run Human Gate

The QUIZ's human-in-the-loop answer is "human approval for actions," which is the what without the when. The production mechanic pauses the run mid-flight — after the plan, before the irreversible action — serializes the run state, and lets a human resume it with a decision. LangGraph (1.2.13 on PyPI) ships this as a pair: `interrupt(payload)` raises a pause that surfaces the payload to the caller, and `Command(resume=value)` re-enters the graph at the same step with the human's answer as the return value of `interrupt`. The machinery that makes a pause survivable is the checkpointer: the graph state is persisted per `thread_id`, so the resumed invocation is not a re-run but a continuation of the same run.

The gate as state-machine arithmetic — approve proceeds, deny substitutes the fallback, and both resume from the same checkpoint:

```python
import json

CHECKPOINTS = {}   # thread_id -> serialized state, exactly one broker of truth

def run_agent(thread_id: str, resume_value=None):
    blob = CHECKPOINTS.get(thread_id)
    state = json.loads(blob) if blob else {"steps_done": [], "pending": None,
                                           "verdict": None}
    if state.get("pending") and resume_value is None:
        raise SystemExit(f"{thread_id}: pending gate needs Command(resume=...)")
    if state.get("pending"):
        verdict = "approve" if resume_value["approve"] else "deny"
        state["steps_done"].append(verdict)
        state["pending"] = None
        state["verdict"] = verdict
    plan = ["plan", "draft", "GATE:delete_records", "execute", "report"]
    for step in plan[len(state["steps_done"]):]:
        if state.get("verdict") == "deny" and step == "execute":
            state["steps_done"].append("fallback")   # denied: the sensitive action never runs
            continue
        if step.startswith("GATE:"):
            state["pending"] = step
            blob = json.dumps(state, sort_keys=True)
            CHECKPOINTS[thread_id] = blob
            return f"INTERRUPT at '{step}': checkpoint {len(blob)} bytes, thread '{thread_id}'"
        state["steps_done"].append(step)
    CHECKPOINTS[thread_id] = json.dumps(state, sort_keys=True)
    return f"DONE: {state['steps_done']}"

print("run 1:", run_agent("run-9"))
print("run 2 (approve):", run_agent("run-9", {"approve": True}))
del CHECKPOINTS["run-9"]
print("run 1:", run_agent("run-9b"))
print("run 2 (deny):", run_agent("run-9b", {"approve": False}))
```

The approve path resumes to `['plan', 'draft', 'approve', 'execute', 'report']` — the sensitive step runs, because a human said so, on the record. The deny path resumes to `['plan', 'draft', 'deny', 'fallback', 'report']` — `execute` is never in the list, replaced by the fallback, which is the whole point of putting the gate before the action rather than after it. The interrupt checkpoint is 84 bytes of JSON: small enough to ship to a review queue, complete enough to reconstruct the run. And the resume is keyed by `thread_id` because the checkpoint store holds many runs at once — resume against the wrong thread and you are approving someone else's refund.

## One Campaign Through the Runtime

One mechanics layer per failure class; a production run touches all of them. The composed fence runs one campaign through the bus (a crash and a redelivery), the compiler (the workflow and its topological sort), the pool (two workers contending for two locks under the global order, monitored for wait-for cycles), and the gate (the refund step pauses, a human approves, the run continues):

```python
from collections import deque

# -- the bus: one worker crash, redelivery, ledger dedup
EVENTS = [f"e{i}" for i in range(10)]
ledger, applied, dup, crashed = set(), [], 0, False
queue = deque(EVENTS)
while queue:
    ev = queue.popleft()
    if ev == "e4" and not crashed:
        crashed = True
        ledger.add(ev)          # the ledger saw the first execution
        applied.append(ev)      # effect applied, worker dies before ack
        queue.append(ev)        # broker redelivers
        continue
    if ev in ledger:
        dup += 1
        continue
    ledger.add(ev)
    applied.append(ev)

# -- the graph: compile the campaign workflow, count cycle rejections
flow = {"ingest": [], "enrich": ["ingest"], "decide": ["enrich"],
        "refund": ["decide"], "notify": ["refund"]}
indeg = {n: len(d) for n, d in flow.items()}
succ = {n: [] for n in flow}
for n, d in flow.items():
    for p in d:
        succ[p].append(n)
ready = deque(sorted(n for n, k in indeg.items() if k == 0))
order5 = []
while ready:
    n = ready.popleft()
    order5.append(n)
    for s in sorted(succ[n]):
        indeg[s] -= 1
        if indeg[s] == 0:
            ready.append(s)
rejected = len([n for n in flow if n not in order5])

# -- the pool: two workers, two locks; ordered acquisition runs it deadlock-free
holds5 = {"worker_a": "db", "worker_b": "api"}
wants5 = {"worker_a": "api", "worker_b": "db"}   # naive trace: a 2-cycle
LOCK_ORDER5 = {"db": 0, "api": 1}
lock_owner = {}
pending5 = {a: sorted([holds5[a], wants5[a]], key=lambda L: LOCK_ORDER5[L])
            for a in holds5}
waits, done5 = [], []
stuck = False
while any(pending5.values()):
    stuck = True
    for a in sorted(pending5):
        if not pending5[a]:
            continue
        lock = pending5[a][0]
        if lock not in lock_owner:
            lock_owner[lock] = a
            pending5[a].pop(0)
            stuck = False
        else:
            waits.append((a, lock_owner[lock]))   # the monitor logs a wait edge
        if not pending5[a]:
            for L in (holds5[a], wants5[a]):
                if lock_owner.get(L) == a:
                    del lock_owner[L]
            done5.append(a)
            stuck = False
    if stuck:
        raise SystemExit("livelock -- the order guarantee says impossible")

wf5 = {}
for waiter, holder in waits:
    wf5[waiter] = holder          # latest wait edge per waiter

def _reaches_self(start: str) -> bool:
    cur = start
    while cur in wf5:
        cur = wf5[cur]
        if cur == start:
            return True
    return False

pool_cycles = sum(_reaches_self(a) for a in wf5)

# -- the gate: the refund step pauses for human approval, then resumes
gate_log = []
plan5 = ["ingest", "GATE:refund", "settle"]
state5 = {"done": [], "pending": None, "verdict": None}

def advance(resume5=None):
    if state5["pending"] and resume5 is None:
        raise SystemExit("pending gate needs Command(resume=...)")
    if state5["pending"]:
        state5["verdict"] = "approve" if resume5["approve"] else "deny"
        gate_log.append(f"RESUME {state5['verdict']}d")
        state5["done"].append(state5["pending"].replace("GATE:", "run:"))
        state5["pending"] = None
    for step in plan5[len(state5["done"]):]:
        if step.startswith("GATE:"):
            state5["pending"] = step
            gate_log.append(f"INTERRUPT {step}")
            return
        state5["done"].append(step)

advance()
advance({"approve": True})

print(f"bus: {len(applied) + dup} executions -> {len(applied)} effects "
      f"for {len(EVENTS)} events, ledger skipped {dup} redelivery, lost 0")
print(f"graph: workflow compiled to {' -> '.join(order5)}, {rejected} cycle rejections; "
      f"pool monitor: {pool_cycles} cycles")
print(f"gate: {'; '.join(gate_log)} -> ran {state5['done']}")
print(f"campaign: complete")
```

The ledger reads clean on every line. The bus: 11 executions produced 10 effects for 10 events — the `e4` crash cost one redelivery and the ledger refused to double-apply it, nothing lost. The graph: the five-node workflow compiled to `ingest -> enrich -> decide -> refund -> notify` with zero cycle rejections, and the pool monitor logged wait edges under contention but counted zero cycles, because the global order holds. The gate: `INTERRUPT GATE:refund`, `RESUME approved`, and the ran-list shows `run:refund` exactly once before `settle` — the pause cost a checkpoint, not the action. Each mechanic owned its own failure class, and the campaign completed with every layer's number on the record.

## Known Failure Modes

| Failure | Symptom | Fix |
|---------|---------|-----|
| Acks before the effect, no redelivery | Worker crash silently loses the task | `acks_late=True` plus an idempotent effect — the pair, never the flag alone |
| At-least-once without a dedup ledger | The refund fires twice after one crash | Ledger the applied effects by task id; check before the effect, not after |
| Calling it "exactly-once delivery" | Team skips the dedup work and trusts the broker | It is exactly-once application — Kafka's own ladder needs idempotence plus transactions plus `read_committed` |
| Timeout as the deadlock fix | Long tasks misdiagnosed as dead; real cycles keep reforming | Detect the wait-for cycle; kill the circular-wait condition with a global lock order |
| Ordering only some acquisitions | One code path takes locks out of order; the cycle returns under load | Every acquisition site sorts by the same total order; enforce in one helper |
| Cycles as runtime edges in the workflow definition | Topological sort stalls; the leftover set is the compile error | Keep iteration outside the DAG — wrap and re-invoke the compiled graph |
| Gate after the irreversible action | Approve arrives when the refund has already settled | `interrupt()` before the effect; the checkpoint resumes with the decision |
| Resume without the checkpointer | The graph re-runs from the start, repeating paid work | Persist state per `thread_id`; resume is a continuation, not a re-invocation |

## Summary

- Delivery semantics are a decision about crashes: the same trace loses `T3` under at-most-once, applies it twice under at-least-once, and skips the redelivery at the ledger under effectively-once — the guarantee is bought at the effect site, not the broker config.
- Deadlock is a cycle in the wait-for graph, and the production kill is the global acquisition order: the three-agent ring that deadlocked at length 3 completes as six grants under one ordering, and the monitor is a graph walk, not a timeout.
- A workflow is a DAG because its compiler needs an order: Kahn's algorithm schedules the six clean nodes and names the exact four-node cycle set when the feedback edge sneaks in — rejection at compile time, iteration one level up.
- The mid-run human gate is `interrupt` before the effect plus a checkpointed resume keyed by thread: the approve path runs the sensitive step, the deny path runs the fallback, and `execute` never appears in the denied run.
- On one campaign every layer owned its own class — 11 executions collapsed to 10 effects, zero compile rejections, zero wait-for cycles, one gate pause-and-resume — and the ledger line is the run's evidence.

## References

### Related Minder Academy Documents

- [7301: Orchestration](7301-Orchestration.md) — the collaboration patterns and bounded monitor cycles these runtime mechanics execute under
- [7302: Communication Protocols](7302-Communication-Protocols.md) — the retry-and-backoff discipline whose duplicates the delivery ledger absorbs
- [7303: Framework Comparison](./guides/7303-Framework-Comparison.md) — where LangGraph's typed state graph, conditional edges and checkpoint-backed resume sit among the frameworks
- [7101: ReAct Loop System](../7100-architecture/7101-ReAct-Loop-System.md) — the runtime cycle that lives inside a compiled-acyclic workflow
- [7503: Adversarial Attacks & Defense](../7500-security/7503-Adversarial-Attacks.md) — quarantine and human review as the escalation path when the gate's answer is deny

### Primary Sources

- Apache Kafka — delivery semantics: default at-least-once, idempotent producer (`enable.idempotence`, default with `acks=all` since 3.0), transactions plus consumer `isolation.level=read_committed` for end-to-end exactly-once
- Celery 5.6.3 documentation — Tasks: `acks_late=True` acknowledges after the task returns and requires idempotent tasks; default early-ack trades loss safety for no duplicates
- LangGraph 1.2.13 (PyPI) — Human-in-the-loop: `interrupt(payload)` pauses mid-node, `Command(resume=...)` re-enters with the decision, `checkpointer` + `thread_id` make the resume a continuation
- Coffman, Elphick & Shoshani (1971), "System Deadlocks" — the four conditions (mutual exclusion, hold-and-wait, no preemption, circular wait) and the prevention strategy this lesson implements as an acquisition order

## Next Steps

- **Next Module:** continue with [assessment/QUIZ.md](assessment/QUIZ.md) — Q7, Q8, Q15, and Q19 are the questions this lesson's fences answer with mechanics
- **Continue with:** [7400: Agent Memory](../7400-memory/README.md) for the persistence layer the checkpointed run state sits beside
- **Assessment:** extend the composed fence with the naive lock acquisition (no global order), show the 2-cycle the monitor catches, and name the Coffman condition the fix removes
