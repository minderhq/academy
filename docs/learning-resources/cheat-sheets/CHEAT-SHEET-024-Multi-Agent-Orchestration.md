---
Document ID: CHEAT-SHEET-024
Title: "CHEAT-SHEET-024: Multi-Agent Orchestration"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'orchestration', 'multi-agent', 'agents', 'communication']
---

# CHEAT-SHEET-024: Multi-Agent Orchestration

**Quick Reference for:** the specialist roster and the plan-execute-review-synthesize flow, the three coordination topologies with their message complexity, the message envelope and handoff capsule contracts, delivery semantics and the dedup ledger, deadlock as a wait-for cycle, the mid-run human gate, and consensus by arbitration or key-voting.

**Version:** 1.0

## The Specialist Roster

Module 7301's six canonical roles — cut the ones the workload does not need, and keep the roster small so a planner cannot invent specialists outside it:

```text
Specialist roster (7301) - keep it small, fail loud on unknowns:
1. Planner      breaks down tasks, creates execution plans, monitors progress
2. Coder        writes and modifies code, debugs issues, optimizes performance
3. Researcher   gathers information, analyzes data, synthesizes findings
4. Reviewer     reviews quality; answers {"approved": bool, "feedback": str}
5. Executor     executes commands, runs scripts, manages resources
6. Communicator interfaces with users, coordinates between agents, summarizes
Cut the roles the workload does not need - the canonical demo runs four of six.
```

The flow is **plan → execute → review → retry → synthesize**: the planner emits steps tagged with a roster key, each specialist executes its step, the reviewer's `{"approved": bool, "feedback": str}` envelope drives one feedback round, and the planner synthesizes the results. Two contracts hold the whole thing up. The **roster contract is fail-loud**: a planner that assigns an unknown specialist raises `ValueError` listing the roster instead of silently skipping the step. And the plan parser **skips non-matching lines silently** — an LLM may add preamble or a trailing note, so count the returned steps against what you asked for before executing.

Module 7301's closing rule: a multi-agent system is only as good as its worst message boundary — specialize the agents, but spend the real engineering on the contracts between them.

## Topologies

| Topology | Message complexity | Best for |
|---|---|---|
| Orchestrator-worker | O(N) | **Default**; decomposable tasks — all coordination through one planner, no worker-to-worker chat |
| Peer-to-peer | O(N²) | Small symmetric fleets (N ≤ 4), e.g. debate |
| Hierarchical | O(N + T) | Plans that nest like an org chart — team leads run specialists, the top orchestrator talks to leads |

The orchestrator-worker default is traceable and bounded, but the orchestrator is a routing bottleneck and a single point of failure — budget for that in design, not in hindsight.

## The Message Envelope

Module 7302's envelope rules:

- Every request carries a fresh `message_id`; the result echoes the request's `correlation_id` — this is what makes traces reconstructable.
- `ttl_s: int = 120` — stale messages are dropped, not delivered late.
- Control lives in the envelope, content in the payload — agents never parse another agent's prose to find control information.
- The payload schema is per-`type` and versioned (`payload_schema: "1.2"`).

```text
task_request payload:
  { "goal": str, "constraints": [str], "context_refs": [str],
    "acceptance": str, "budget": { "max_steps": 10, "max_tokens": 50000 } }
task_result payload:
  { "status": "done|failed|partial", "artifacts": [ref],
    "summary": str, "telemetry": { "steps": int, "tokens": int } }
```

The budget block makes every delegated task a bounded-cost process — the multi-agent equivalent of the single agent's iteration cap.

## Handoff: The Context Capsule

When work moves between agents, the receiver must not inherit the sender's entire transcript. Package a capsule (module 7302's handoff protocol):

| Capsule field | Carries | Why it exists |
|---|---|---|
| `goal` | the task the receiver continues | same mission, new owner |
| `facts` | settled conclusions | stops receivers redoing settled work |
| `open_questions` | unresolved items | marks what still needs work |
| `artifacts` | data **by reference** (storage keys, not inlined blobs) | keeps messages small and cache-friendly |
| `decisions` | the rationale log | without it the receiver re-litigates choices and loops |

## Delivery Semantics

The bus's side of the retry contract (module 7304): what the broker does to a task whose worker dies mid-execution. **At-most-once** acks before the work — a crash loses the task. **At-least-once** acks after — a crash redelivers it. **Effectively-once** is at-least-once plus a dedup ledger at the effect site. Celery puts the choice on one flag: `acks_late=False` (the default) loses tasks on crash; `acks_late=True` redelivers — enable it only if the task is idempotent, per Celery's own docs. The industry phrase "exactly-once delivery" oversells: exactly-once **application** is what the ledger owns.

| Guarantee | Ack timing | Worker crash mid-task | World ends up with |
|---|---|---|---|
| At-most-once | before execution | task lost forever | 5 effects for 6 tasks |
| At-least-once | after execution | broker redelivers | 7 effects — the refund fired twice |
| Effectively-once | after + dedup ledger at the effect site | redelivery refused | 6 effects, 1 dup skip |

The canonical six-task trace, worker dying on `T3` before its ack:

```python
from collections import deque

# --- delivery semantics: 6 tasks, the worker running T3 dies before its ack ---
def run_delivery(mode):
    seen, effects, executed, lost, dup = set(), [], [], 0, 0
    crashed = False
    queue = deque(["T0", "T1", "T2", "T3", "T4", "T5"])
    while queue:
        task = queue.popleft()
        executed.append(task)
        if task == "T3" and not crashed:
            crashed = True
            if mode == "at-most-once":
                lost += 1          # acked before the work; the crash loses it
                continue
            effects.append(task)   # the effect hits the world, then no ack
            if mode == "idempotent":
                seen.add(task)
            queue.append(task)     # broker redelivers
            continue
        if mode == "idempotent" and task in seen:
            dup += 1               # redelivery; ledger refuses re-apply
            continue
        if mode == "idempotent":
            seen.add(task)
        effects.append(task)
    doubled = len(effects) - len(set(effects))
    return len(executed), len(effects), lost, dup, doubled

for mode in ("at-most-once", "at-least-once", "idempotent"):
    e, f, l, d, x = run_delivery(mode)
    print("%-13s executed=%d effects=%d lost=%d dup_skips=%d doubled=%d"
          % (mode, e, f, l, d, x))

# --- deadlock: a cycle in the wait-for graph; kill it with a global lock order ---
HOLDS = {"writer": "db", "analyzer": "api", "mailer": "fs"}
WANTS = {"writer": "api", "analyzer": "fs", "mailer": "db"}
owner = {lock: agent for agent, lock in HOLDS.items()}
path, node = ["writer"], owner[WANTS["writer"]]
while node != "writer":
    path.append(node)
    node = owner[WANTS[node]]
print("deadlocked set:", " -> ".join(path + [path[0]]), "(length %d)" % len(path))

# --- consensus: majority vote over proposal keys; unknown key raises; ties -> first ---
votes = {"agent_a": 0, "agent_b": 0}
for choice in ("agent_a", "agent_b", "agent_a"):
    if choice not in votes:
        raise ValueError("voter chose unknown proposal %r" % choice)
    votes[choice] += 1
print("majority:", max(votes, key=votes.get))

# --- p2p negotiation: FCFS drops the losing duplicate bid ---
bids = [("gpu", "optimize data transfer"),
        ("net", "optimize data transfer"),
        ("storage", "verify dataset mount")]
taken, dropped = {}, []
for agent, subtask in bids:
    if subtask in taken:
        dropped.append((agent, subtask))
    else:
        taken[subtask] = agent
print("dropped duplicate bids: %s" % dropped)
print("assigned: %s" % list(taken.items()))
```

```text
at-most-once  executed=6 effects=5 lost=1 dup_skips=0 doubled=0
at-least-once executed=7 effects=7 lost=0 dup_skips=0 doubled=1
idempotent    executed=7 effects=6 lost=0 dup_skips=1 doubled=0
deadlocked set: writer -> analyzer -> mailer -> writer (length 3)
majority: agent_a
dropped duplicate bids: [('net', 'optimize data transfer')]
assigned: [('optimize data transfer', 'gpu'), ('verify dataset mount', 'storage')]
```

## Deadlock and the Human Gate

**Deadlock is a cycle in the wait-for graph** — each agent holds a lock and waits for a lock another agent holds, and the holds close a loop (the fence finds `writer -> analyzer -> mailer -> writer`). The four Coffman conditions — mutual exclusion, hold-and-wait, no preemption, circular wait — are a checklist of kills: break any one and the cycle cannot form. The production pick is almost always circular wait, because it has a one-line implementation: **a global acquisition order** every agent obeys.

**The mid-run human gate** pauses the run after the plan and **before the irreversible action**. LangGraph ships it as a pair: `interrupt(payload)` raises a pause that surfaces the payload to the caller, and `Command(resume=value)` re-enters the graph at the same step with the human's answer as `interrupt`'s return value. The checkpointer persists state per `thread_id`, so the resume is a continuation of the same run, not a re-run. Approve resumes to `['plan', 'draft', 'approve', 'execute', 'report']` — the sensitive step runs on the record. Deny substitutes the fallback: `['plan', 'draft', 'deny', 'fallback', 'report']` — `execute` is never in the list, which is the whole point of putting the gate before the action rather than after. The interrupt checkpoint is 84 bytes of JSON: small enough to ship to a review queue, complete enough to reconstruct the run. Resume is keyed by `thread_id` because the checkpoint store holds many runs at once — resume against the wrong thread and you are approving someone else's refund.

## Consensus: Arbitration, Voting, Bidding

| Mechanism | Use when | Contract |
|---|---|---|
| LLM arbitration | the conflict needs judgment | prompt for a structured verdict and parse the chosen key out of it |
| Majority voting | an auditable, replayable decision | votes count proposal **keys**, never text; an unknown key raises; ties go to the first key in insertion order — documented, not random |

Peer-to-peer fleets negotiate by bidding: broadcast the task announcement, agents propose the subtask they are best at, first-come-first-served assigns. Overlapping bids must be handled explicitly — the fence's `net` agent bid on the same transfer work as `gpu` and was **dropped with a warning**; without the explicit drop, the losing bid vanishes silently or overwrites the assignment. FCFS is the simplest rule; a real swarm scores bids (capability match, current load) instead of taking insertion order.

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| a task vanishes after a worker crash | ack-before-execute (at-most-once) | ack after execution (`acks_late=True`) — and only for idempotent tasks |
| a refund fires twice | at-least-once with no ledger | dedup ledger at the effect site — effectively-once application |
| agents hang forever | circular wait on locks | one global acquisition order kills the wait-for cycle |
| receiver re-litigates settled choices and loops | handoff carried transcript, not decisions | send the decisions log in the capsule — why, not just what |
| planner assigns a specialist that does not exist | silent skip of unknown roster keys | fail-loud `ValueError` listing the roster; keep the roster small |
| run pauses at a gate and never resumes | resume without the thread's checkpoint | `Command(resume=...)` against the same `thread_id` — the gate sits before the irreversible step |

## Quick Reference For

- [Module 7301: Collaborative Tasking - Multi-Agent Synergy](../../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md)
- [Module 7302: Multi-Agent Communication Protocols](../../phases/phase7-agentic/7300-orchestration/7302-Communication-Protocols.md)
- [Module 7304: Event Buses, Deadlocks, and Human Gates](../../phases/phase7-agentic/7300-orchestration/7304-Event-Buses-Deadlocks-and-Human-Gates.md)
- [CHEAT-SHEET-023: ReAct Agent Loop](./CHEAT-SHEET-023-ReAct-Agent-Loop.md)
