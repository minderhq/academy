---
Document ID: 7302
Title: "7302: Multi-Agent Communication Protocols"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# 7302: Multi-Agent Communication Protocols

## Abstract

A multi-agent system is only as reliable as the contracts between its
agents. This document defines message schemas and envelopes, the main
coordination topologies (orchestrator-worker, peer-to-peer, hierarchical),
consensus and negotiation patterns, handoff protocols that preserve
context, interoperability standards (MCP, A2A), and the failure handling
that keeps a fleet of LLM agents debuggable in production.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Why Structured Messages](#2-why-structured-messages)
- [3. Message Envelope](#3-message-envelope)
- [4. Coordination Topologies](#4-coordination-topologies)
- [5. Consensus & Negotiation](#5-consensus--negotiation)
- [6. Handoff Protocol](#6-handoff-protocol)
- [7. Interoperability Standards](#7-interoperability-standards)
- [8. Failure Handling](#8-failure-handling)
- [9. Troubleshooting](#9-troubleshooting)
- [10. References](#10-references)

---

## 1. Overview

### 1.1 Prerequisites

- [7301: Orchestration](./7301-Orchestration.md) - orchestration patterns
- [7101: ReAct Loop System](../7100-architecture/7101-ReAct-Loop-System.md) - single-agent loop
- [7102: Planning and Decomposition](../7100-architecture/7102-Planning-Decomposition.md) - task graphs

### 1.2 Learning Objectives

After completing this document, you will:
- ✅ Design a typed message envelope with correlation IDs
- ✅ Choose a coordination topology from task structure, not hype
- ✅ Implement voting/debate consensus and know when it helps
- ✅ Package agent-to-agent handoffs without losing context
- ✅ Handle timeouts, retries, and dead-lettering in agent fleets

---

## 2. Why Structured Messages

The naive pattern — agents reading each other's raw prose — fails at
scale for three reasons:

```text
1. Ambiguity   : downstream agents misinterpret intent, compound errors
2. No tracing  : "who asked for this?" is unanswerable after the fact
3. Coupling    : rewording one agent's output breaks its consumers
```

The fix is treating inter-agent communication like service-to-service
communication: **typed payloads, explicit addressing, correlation IDs**.
Natural language stays *inside* the payload; the envelope is structured.

---

## 3. Message Envelope

```python
from dataclasses import dataclass, field, asdict
from uuid import uuid4

@dataclass
class Message:
    type: str                     # "task_request" | "task_result" | "query" | "error"
    sender: str                   # agent id
    recipient: str                # agent id or "broadcast"
    payload: dict                 # typed content for this message type
    correlation_id: str = ""      # links result -> request (set by requester)
    message_id: str = field(default_factory=lambda: uuid4().hex)
    reply_to: str = ""            # queue/agent for the response
    ttl_s: int = 120              # drop stale messages

    def to_dict(self):
        return asdict(self)
```

**Envelope rules:**
- Every request carries a fresh `message_id`; the result echoes the
  request's `correlation_id` — this is what makes traces reconstructable
- `payload` schema is per-`type` and versioned (`payload_schema: "1.2"`)
- Agents never parse another agent's prose to find control information —
  control lives in the envelope, content in the payload

```text
task_request payload:
  { "goal": str, "constraints": [str], "context_refs": [str],
    "acceptance": str, "budget": { "max_steps": 10, "max_tokens": 50000 } }
task_result payload:
  { "status": "done|failed|partial", "artifacts": [ref],
    "summary": str, "telemetry": { "steps": int, "tokens": int } }
```

---

## 4. Coordination Topologies

### 4.1 Orchestrator-Worker (default choice)

```text
            ┌──────────────┐
            │ Orchestrator │  decomposes, routes, aggregates
            └──────┬───────┘
      ┌────────────┼────────────┐
 ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
 │ Worker A│  │ Worker B│  │ Worker C│   no worker-to-worker chat
 └─────────┘  └─────────┘  └─────────┘
```

- All coordination flows through one planner agent ([7301](./7301-Orchestration.md))
- Pros: traceable, bounded message complexity O(N)
- Cons: orchestrator is a bottleneck and single point of failure

### 4.2 Peer-to-Peer

Agents message each other directly. Cheap latency, but message complexity
grows O(N²) and failure modes multiply. Justified only for small fleets
(N ≤ 4) with genuinely symmetric collaboration (e.g., debate).

### 4.3 Hierarchical

Teams of workers, each with a team lead; leads talk to the top
orchestrator. Matches org-chart task decomposition — use when a plan
naturally nests (e.g., "research" → sub-teams per topic).

| Topology | Message complexity | Best for |
|----------|-------------------|----------|
| Orchestrator-worker | O(N) | **Default**; decomposable tasks |
| Peer-to-peer | O(N²) | Small symmetric fleets |
| Hierarchical | O(N + T) | Deeply nested task structure |

---

## 5. Consensus & Negotiation

### 5.1 Voting

Run k independent agents on the same task and take majority:

```python
def majority_vote(answers: list[str]) -> str:
    from collections import Counter
    return Counter(answers).most_common(1)[0][0]
```

- Reliable when answers are canonicalizable (IDs, classifications, numbers)
- Useless on free-form prose — votes won't string-match; use a judge
  model to score candidates instead

### 5.2 Debate / Critique Loop

Proposer produces; critic attacks; proposer revises — bounded rounds:

```text
for round in range(max_rounds=2):
    draft    = proposer(task, critique)
    critique = critic(task, draft)          # specific, actionable flaws
    if critic_verdict == "accept":
        break
final = draft
```

- Two rounds capture most of the gain; more rounds mostly add cost
- Critics must see the *acceptance criteria*, not just the draft —
  otherwise they nitpick style

> **📊 Rule of Thumb:**
> Add consensus machinery only where a *single agent's error rate* is
> measurably high and errors are independent. Consensus on correlated
> failures (same model, same prompt) buys almost nothing.

---

## 6. Handoff Protocol

When work moves between agents, the receiver must not inherit the
sender's entire transcript. Package a **context capsule**:

```python
def handoff(from_agent, to_agent, task_state):
    return Message(
        type="handoff",
        sender=from_agent,
        recipient=to_agent,
        payload={
            "goal": task_state.goal,
            "facts": task_state.validated_facts,      # settled conclusions
            "open_questions": task_state.unresolved,
            "artifacts": task_state.artifact_refs,     # data by reference
            "decisions": task_state.decisions_log,     # why, not just what
        },
    )
```

**Where:**
- **facts vs open_questions** split stops receivers from redoing settled work
- **artifacts by reference** (storage keys, not inlined blobs) keeps
  messages small and cache-friendly
- The **decisions log** preserves rationale — without it, the receiving
  agent re-litigates choices and loops

---

## 7. Interoperability Standards

Two complementary standards matter for agent fleets:

| Standard | Scope | What it standardizes |
|----------|-------|---------------------|
| **MCP** (Model Context Protocol) | Agent ↔ tools/resources | Tool discovery, invocation, resource access over JSON-RPC |
| **A2A** (Agent-to-Agent) | Agent ↔ agent | Agent cards (capabilities), task handoffs, streaming status |

- Use MCP for the *tool layer*: one integration surface per tool, reused
  by every agent (see [7200](../7200-tools/README.md))
- Use A2A-style handoffs for the *agent layer*: capability discovery
  ("who can do X?") plus task lifecycle (submitted → working → done)
- Both reduce the N×M integration problem to N+M

---

## 8. Failure Handling

```python
import time

def send_with_retry(bus, msg: Message, retries=2, backoff=1.5):
    for attempt in range(retries + 1):
        try:
            ack = bus.send(msg, timeout_s=10)
            if ack.ok:
                return ack
        except TimeoutError:
            pass
        time.sleep(backoff ** attempt)
    bus.dead_letter(msg, reason="no_ack")   # observable, never silent
    return None
```

Fleet-level rules:
- **Timeouts everywhere**: an agent that can hang must not be able to
  hang a pipeline — per-message `ttl_s` plus per-task wall-clock budgets
- **Retry idempotently**: workers key on `message_id` so replays are safe
- **Dead-letter queue**: after retries, park the message with the error;
  a supervisor agent (or human) triages the DLQ — never drop silently
- **Circuit breaker**: N consecutive failures from one worker → route
  around it and alert, instead of burning the whole fleet's budget
- **Budget propagation**: parent task's token/step budget divides among
  children; a child that exhausts its share fails fast, and the parent
  replans

---

## 9. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Results arrive but can't be traced to requests | Missing correlation IDs | Enforce envelope schema; reject uncorrelated results |
| Two agents loop, each "fixing" the other | Unbounded critique loop | Cap rounds; require critic to output accept/reject verdict |
| Worker receives impossible tasks | Orchestrator lacks capability map | Agent cards; validate assignment against declared skills |
| Flaky workers poison consensus | Correlated failures | Diversify models; consensus only on canonicalizable answers |
| Handoff loses decisions, work is redone | Context capsule too thin | Ship facts + decisions log; log handoffs as first-class events |
| Fleet cost spikes on one workflow | No budget propagation | Per-task token budgets; enforce at the bus level |

---

## 10. References

### Specifications
- [1] Anthropic. "Model Context Protocol (MCP)" - https://modelcontextprotocol.io
- [2] Google. "Agent2Agent (A2A) Protocol" - https://a2a-protocol.org

### Academic Papers
- [3] Du et al. "Improving Factuality and Reasoning in Language Models through Multiagent Debate". ICML, 2024.
- [4] Hong et al. "MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework". ICLR, 2024.
- [5] Wu et al. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation". 2023.

### Related PROJECT-OMEGA Documents
- [7301: Orchestration](./7301-Orchestration.md) - planning and routing
- [7101: ReAct Loop System](../7100-architecture/7101-ReAct-Loop-System.md) - single-agent foundation
- [7200: Tool Calling](../7200-tools/README.md) - MCP tool layer
- [7303: Framework Comparison](./guides/7303-Framework-Comparison.md) - framework support matrix

---

## Next Steps

- Frameworks: **[7303: Framework Comparison](./guides/7303-Framework-Comparison.md)**
- Memory: **[7401: Long-term Memory](../7400-memory/7401-Long-term-Memory.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**

---

**Document ID:** 7302
**Status:** Complete
**Related Documents:** [7301, 7101, 7200, 7303]
