---
Document ID: CHEAT-SHEET-030
Title: "CHEAT-SHEET-030: Multi-Agent Communication Protocols"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'agents', 'multi-agent', 'orchestration', 'mcp']
---

# CHEAT-SHEET-030: Multi-Agent Communication Protocols

**Quick Reference for:** the typed message envelope and its correlation contract, the three coordination topologies and their message complexity, when consensus helps and when it is unanimity theater, the context-capsule handoff, backoff with jitter and the dead-letter tripwire, and the budget-propagation rule. CHEAT-SHEET-024 owns the planning-and-routing surface of multi-agent systems; CHEAT-SHEET-027 owns the MCP tool layer and the client/registry contract; this sheet owns the wire *between* agents - the envelope, the topology, the handoff, and the failure handling that keeps a fleet of LLM agents debuggable in production. A multi-agent system is only as reliable as the contracts between its agents.

## The Envelope: Structured Messages

Agents reading each other's raw prose fails at scale for three reasons: **ambiguity** (downstream agents misinterpret intent and compound errors), **no tracing** ("who asked for this?" is unanswerable after the fact) and **coupling** (rewording one agent's output breaks its consumers). The fix is treating inter-agent communication like service-to-service communication: **typed payloads, explicit addressing, correlation IDs**. Natural language stays *inside* the payload; the envelope is structured - control lives in the envelope, content in the payload, and agents never parse another agent's prose to find control information.

Every request carries a fresh `message_id`; the result echoes the request's `correlation_id` - this is what makes traces reconstructable. `payload` schema is per-`type` and versioned (`payload_schema: "1.2"`). The envelope fields: `type` (task_request | task_result | query | error), `sender`, `recipient` (agent id or "broadcast"), `payload`, `correlation_id`, `message_id`, `reply_to`, and `ttl_s = 120` so stale messages are dropped before they mislead.

## Coordination Topologies

Topology is a reliability decision, not a diagram - pick the shape whose failure mode you can actually operate:

| topology | msgs at N=8 | complexity | best for |
|---|---|---|---|
| orchestrator-worker | 8 | O(N) | **default** - decomposable tasks, traceable, one SPOF |
| peer-to-peer | 28 | O(N^2) | small symmetric fleets (N <= 4), e.g. debate |
| hierarchical | 10 | O(N + T) | deeply nested task structure, teams with leads |

```text
topology            msgs   complexity   best for
orchestrator          8    O(N)         default - decomposable tasks, one SPOF
peer-to-peer         28    O(N^2)       small symmetric fleets (N <= 4)
hierarchical         10    O(N+T)       deeply nested task structure
```

Orchestrator-worker routes everything through one planner: message complexity O(N), fully traceable, but the orchestrator is a bottleneck and single point of failure. Peer-to-peer buys cheap latency at O(N^2) message complexity with multiplied failure modes - justified only for N <= 4 with genuinely symmetric collaboration. Hierarchical matches org-chart decomposition when a plan naturally nests ("research" -> sub-teams per topic).

## Consensus and Negotiation

| mode | works when |
|---|---|
| voting (k agents, majority) | answers are canonicalizable - IDs, classifications, numbers |
| judge model scores candidates | free-form prose - string-voting is useless |
| debate / critique loop | proposer-critic-revise, capped rounds, critic sees the acceptance criteria |

Voting is reliable exactly when answers canonicalize: five agents vote `['cat', 'cat', 'dog', 'cat', 'fox']` and majority lands `'cat' x3`. On free-form prose the same five agents produce five distinct strings - zero string agreement, x1 each - so a judge model scores candidates instead. And the deeper rule: consensus on **correlated** failures buys almost nothing - five copies of the same model on the same prompt vote 5-0 for one wrong answer, which is unanimity theater, not evidence. Add consensus machinery only where a single agent's error rate is measurably high *and* errors are independent.

The debate loop is bounded at **max_rounds = 2** - two rounds capture most of the gain, round 3+ mostly adds cost. The critic must see the *acceptance criteria*, not just the draft, otherwise it nitpicks style; and the loop terminates on an explicit accept/reject verdict, or two agents will loop forever "fixing" each other.

## Handoff: the Context Capsule

When work moves between agents the receiver must not inherit the sender's entire transcript - package a **context capsule** with five parts: the `goal`, `facts` (validated, settled conclusions), `open_questions` (what is unresolved), `artifacts` (data **by reference** - storage keys, not inlined blobs - keeps messages small and cache-friendly) and the `decisions` log (the *why*, not just the what). Without the decisions log the receiving agent re-litigates settled choices and loops; without the facts-vs-open split it redoes settled work.

```text
handoff payload (full):
  goal           "answer billing dispute"
  facts          ["user was charged twice on 10-02"]
  open_questions ["which refund policy applies"]
  artifacts      ["s3://ledger/oct.csv"]        by reference, not inlined
  decisions      ["refund route over credit route (SLA)"]
thin handoff  -> receiver redoes 4 of 4 (facts, questions, artifacts, decisions)
full handoff  -> receiver redoes 0 of 4
```

## Failure Handling: Backoff, Jitter, Dead-Letter

Retry without an escape hatch ends in a dead-letter with a reason - `bus.dead_letter(msg, reason="no_ack")` - observable, never silent; a supervisor (or human) triages the DLQ. The canonical retry ledger (backoff 1.5, ack on attempt 2): pauses `[1.0, 1.5, 2.25]`.

But every client that saw the same failure computes the same delays: N clients retry in synchronized waves at 0.5s / 1.0s / 2.0s / 4.0s and **each wave re-trips the limiter it was escaping**. **Jitter** breaks the lockstep - the same clients seeded-jittered spread to `[0.82, 1.01, 2.14, 4.11]`. Production SDKs jitter by default (`tenacity` calls the idiom `wait_random_exponential`; LLM SDK clients expose a `max_retries` budget instead of a hand-rolled loop). The second half of the discipline: **honor `Retry-After`** - the server knows its own load curve, so a 429 hinting 3.0s beats your computed 2.0s: `pause = max(hint, computed) = 3.0s`. And in async agents the wait is awaited: `time.sleep` inside an event loop blocks *every* task on it - `await asyncio.sleep`.

| fleet rule | what it buys |
|---|---|
| timeouts everywhere (per-message `ttl_s`, wall-clock budgets) | an agent that can hang cannot hang the pipeline |
| retry idempotently, key on `message_id` | replays are safe, no double-charged effects |
| dead-letter queue with reason | failures observable, triaged, never dropped silently |
| circuit breaker (N consecutive failures -> route around) | one flaky worker cannot burn the fleet's budget |
| budget propagation (parent divides among children) | a child that exhausts its share fails fast, the parent replans |

## Interop: MCP vs A2A

Two complementary standards, two layers - they compose, they do not compete:

| standard | layer | what it standardizes |
|---|---|---|
| MCP (Model Context Protocol) | agent <-> tools/resources | tool discovery, invocation, resource access over JSON-RPC |
| A2A (Agent-to-Agent) | agent <-> agent | agent cards (capabilities), task handoffs, task lifecycle, streaming status |

Both reduce the N x M integration problem to N + M. Use MCP for the *tool layer* - one integration surface per tool, reused by every agent (the deployment starts as one `mcpServers` config block; see CHEAT-SHEET-027 for the client/registry contract). Use A2A-style handoffs for the *agent layer*: capability discovery ("who can do X?" via agent cards, validated against declared skills before assignment) plus task lifecycle (submitted -> working -> done) with streaming status. MCP deliberately stops at the tool layer - agent-to-agent discovery and task lifecycle stay with A2A.

## Budget Propagation

The parent task's token/step budget **divides among its children**: 50,000 tokens across 3 children is 16,666 each, enforced at the bus level. A child that exhausts its share fails fast - and the parent **replans** instead of letting the child burn the siblings' budget. Without this rule one workflow's runaway agent spikes the whole fleet's cost; the budget is not a hope, it is an enforced division.

## Known Failure Modes

| failure | lesson |
|---|---|
| Ship consensus on correlated models | 5-0 votes for a wrong answer - unanimity is not evidence, diversify or drop |
| Trust unbounded critique loops | two agents "fixing" each other forever - cap rounds, demand a verdict |
| Broadcast full transcripts on handoff | thin/thick capsule: thin redoes 4 of 4 - ship facts + decisions log |
| Retry in lockstep | synchronized waves re-trip the limiter - jitter every delay |
| Let one child eat the parent's budget | no propagation - enforce per-child shares at the bus, replan on exhaust |

## References

- Anthropic, *Model Context Protocol (MCP)* - modelcontextprotocol.io
- Google, *Agent2Agent (A2A) Protocol* - a2a-protocol.org
- Du et al., *Improving Factuality and Reasoning through Multiagent Debate*, ICML 2024
- Hong et al., *MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework*, ICLR 2024
- Wu et al., *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation*, 2023

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Results arrive untraceable to requests | missing correlation IDs | enforce the envelope schema; reject uncorrelated results |
| Two agents loop, each "fixing" the other | unbounded critique loop | cap rounds; require an accept/reject verdict |
| Worker receives impossible tasks | orchestrator lacks a capability map | agent cards; validate assignment against declared skills |
| Flaky workers poison consensus | correlated failures | diversify models; consensus only on canonicalizable answers |
| Handoff loses decisions, work redone | context capsule too thin | ship facts + decisions log; log handoffs as first-class events |
| Fleet cost spikes on one workflow | no budget propagation | per-task token budgets enforced at the bus level |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 7302: Multi-Agent Communication Protocols](../../phases/phase7-agentic/7300-orchestration/7302-Communication-Protocols.md) | this sheet's source module - envelopes, topologies, handoffs, failure handling |
| [Module 7301: Orchestration](../../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md) | the planning-and-routing half the orchestrator-worker topology assumes |
| [Module 7204: Timeouts, Retries and Rate Limits](../../phases/phase7-agentic/7200-tools/7204-Timeouts-Retries-and-Rate-Limits.md) | the caller-side resilience stack this sheet's fleet rules extend |
| [CHEAT-SHEET-024: Multi-Agent Orchestration](CHEAT-SHEET-024-Multi-Agent-Orchestration.md) | the planning-and-routing surface; this sheet owns the wire between agents |

```python
"""Fence for CHEAT-SHEET-030: Multi-Agent Communication Protocols.

Reproduces the canonical numbers from module 7302 with a deterministic
stdlib run: envelope correlation, topology message complexity, consensus
modes, the capped debate loop, context-capsule handoffs, backoff+jitter
and the budget propagation rule.
"""

import random
from collections import Counter
from dataclasses import dataclass, field

# ---------------------------------------------------------------- F1 envelope

@dataclass
class Message:
    type: str
    sender: str
    recipient: str
    payload: dict
    correlation_id: str = ""          # requester sets; result echoes it
    message_id: str = field(default_factory=lambda: f"m-{Message._seq()}")

    _n = 0

    @classmethod
    def _seq(cls):
        cls._n += 1
        return f"{cls._n:03d}"

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}


def deliver(bus, msg, ttl_s=120):
    """Bus half: validate correlation, drop stale, route."""
    if msg.type == "task_result" and msg.correlation_id not in bus:
        return "REJECTED: uncorrelated result (no matching request)"
    return f"routed to {msg.recipient}"


print("F1 envelope")
bus = {}
req = Message("task_request", "orch", "worker-a", {"goal": "summarize corpus"})
bus[req.message_id] = req
res_ok = Message("task_result", "worker-a", "orch", {"status": "done"},
                 correlation_id=req.message_id)
res_bad = Message("task_result", "worker-a", "orch", {"status": "done"})
print(f"  fresh ids: {req.message_id} then {Message('query', 'orch', 'worker-b', {}).message_id}")
print(f"  correlated result -> {deliver(bus, res_ok)}")
print(f"  uncorrelated result -> {deliver(bus, res_bad)}")
print("  ttl_s=120 in every envelope -> stale msgs dropped; control in envelope, prose in payload")

# ------------------------------------------------------------ F2 topologies

def msg_complexity(n, teams):
    orch = n                      # every worker talks to the orchestrator
    p2p = n * (n - 1) // 2        # every pair chats once
    hier = n + teams              # workers talk to team leads, leads to the top
    return orch, p2p, hier


print("F2 topologies (N=8 workers, 2 team leads)")
orch, p2p, hier = msg_complexity(8, 2)
print(f"  orchestrator-worker {orch} msgs (O(N), default, one SPOF)")
print(f"  peer-to-peer       {p2p} msgs (O(N^2)) - justified only for N<=4 symmetric fleets")
print(f"  hierarchical       {hier} msgs (O(N+T)) - deeply nested task structure")

# ---------------------------------------------------------------- F3 consensus

def majority_vote(answers):
    top, cnt = Counter(answers).most_common(1)[0]
    return top, cnt


print("F3 consensus")
votes = ["cat", "cat", "dog", "cat", "fox"]
top, cnt = majority_vote(votes)
print(f"  canonicalizable: 5 agents, votes {votes} -> '{top}' x{cnt} majority")
prose = ["The text is mainly about pets.",
         "It discusses domestic animals.",
         "The passage covers cats and dogs.",
         "Animals, primarily felines.",
         "About animal companions."]
agree = majority_vote(prose)
print(f"  free-form prose: {len(set(prose))} distinct strings from 5 votes -> "
      f"'{agree[0]}' x{agree[1]}; string-voting is useless, use a judge model")
print("  correlated failures: 5 copies of one wrong model vote 5-0 for a wrong "
      "answer - consensus needs independent errors, else it is unanimity theater")

# ---------------------------------------------------------------- F4 debate

print("F4 debate loop (max_rounds=2, critic sees acceptance criteria)")
critic_log = []
draft, critique = "v0 draft", ""
for round_ in range(2):
    critique = f"r{round_}: missing acceptance criterion c{round_ + 1}"
    critic_log.append(critique)
    if round_ == 1:
        verdict = "accept"
    else:
        verdict = "revise"
    draft = f"v{round_ + 1} draft (fixed {critique.split(':')[1].strip()})"
    print(f"  round {round_}: verdict={verdict} -> {draft}")
    if verdict == "accept":
        break
print("  two rounds capture most of the gain; round 3+ mostly adds cost")

# ---------------------------------------------------------------- F5 handoff

@dataclass
class TaskState:
    goal: str
    validated_facts: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)
    artifact_refs: list = field(default_factory=list)
    decisions_log: list = field(default_factory=list)


def handoff(state, full):
    payload = {"goal": state.goal}
    if full:
        payload.update({
            "facts": state.validated_facts,
            "open_questions": state.unresolved,
            "artifacts": state.artifact_refs,
            "decisions": state.decisions_log,
        })
    return payload


def receiver_probes(payload):
    redone = 0
    if "facts" not in payload:
        redone += 2                 # redoes settled work
    if "decisions" not in payload:
        redone += 1                 # re-litigates choices
    if "artifacts" not in payload:
        redone += 1                 # re-fetches blobs already stored
    return redone


print("F5 context capsule")
state = TaskState(
    goal="answer billing dispute",
    validated_facts=["user was charged twice on 10-02"],
    unresolved=["which refund policy applies"],
    artifact_refs=["s3://ledger/oct.csv"],
    decisions_log=["refund route chosen over credit route (SLA)"],
)
full = receiver_probes(handoff(state, full=True))
thin = receiver_probes(handoff(state, full=False))
print(f"  full capsule  -> receiver redoes {full} of 4 things (facts/open-questions/artifacts/decisions)")
print(f"  thin capsule  -> receiver redoes {thin} of 4 things; facts-vs-open split + "
      f"artifacts-by-reference + decisions log keep handoffs lossless")

# ------------------------------------------------------------- F6 backoff

random.seed(42)


def send_with_retry(attempts=3, backoff=1.5):
    """Success on attempt 2; the ledger shows the pause that preceded it."""
    pauses = [backoff ** a for a in range(attempts)]
    return pauses, "ack on attempt 2"


print("F6 failure handling")
pauses, ack = send_with_retry()
print(f"  no ack after retries -> dead_letter(reason='no_ack'), never silent; ledger {pauses} -> {ack}")
no_jitter = [0.5 * 2 ** a for a in range(4)]
waves = [round(0.5 * 2 ** a, 2) for a in range(4)]
print(f"  8 clients, no jitter: all retry at {waves} s - four synchronized waves "
      f"re-trip the limiter they escaped")
jit = [round(random.uniform(0, 0.5) + 0.5 * 2 ** a, 2) for a in range(4)]
print(f"  seeded jitter spreads the same 8 clients: {sorted(jit)} s "
      f"(tenacity calls it wait_random_exponential; SDK max_retries covers it)")
retry_after, computed = 3.0, 0.5 * 2 ** 2
print(f"  429 Retry-After {retry_after}s vs computed {computed}s -> "
      f"pause = max() = {max(retry_after, computed)}s (server hint beats your curve)")
print("  async rule: time.sleep blocks the whole event loop - await asyncio.sleep")

# ------------------------------------------------------- F7 budget propagation

print("F7 budget propagation")
parent_tokens = 50000
children = 3
shares = parent_tokens // children
used = {f"child-{i + 1}": shares - (1200 * (i + 1)) for i in range(children)}
exhausted = [k for k, v in used.items() if v <= 0]
used["child-2"] = -800
exhausted = [k for k, v in used.items() if v < 0]
print(f"  parent {parent_tokens} tok -> {children} children x {shares:,} tok each")
print("  child-2 exhausts its share -> fails fast; parent replans instead of "
      "burning siblings' budget")
print(f"  exhausted this run: {exhausted}; budgets enforced at the bus level")
```

```text
F1 envelope
  fresh ids: m-001 then m-004
  correlated result -> routed to orch
  uncorrelated result -> REJECTED: uncorrelated result (no matching request)
  ttl_s=120 in every envelope -> stale msgs dropped; control in envelope, prose in payload
F2 topologies (N=8 workers, 2 team leads)
  orchestrator-worker 8 msgs (O(N), default, one SPOF)
  peer-to-peer       28 msgs (O(N^2)) - justified only for N<=4 symmetric fleets
  hierarchical       10 msgs (O(N+T)) - deeply nested task structure
F3 consensus
  canonicalizable: 5 agents, votes ['cat', 'cat', 'dog', 'cat', 'fox'] -> 'cat' x3 majority
  free-form prose: 5 distinct strings from 5 votes -> 'The text is mainly about pets.' x1; string-voting is useless, use a judge model
  correlated failures: 5 copies of one wrong model vote 5-0 for a wrong answer - consensus needs independent errors, else it is unanimity theater
F4 debate loop (max_rounds=2, critic sees acceptance criteria)
  round 0: verdict=revise -> v1 draft (fixed missing acceptance criterion c1)
  round 1: verdict=accept -> v2 draft (fixed missing acceptance criterion c2)
  two rounds capture most of the gain; round 3+ mostly adds cost
F5 context capsule
  full capsule  -> receiver redoes 0 of 4 things (facts/open-questions/artifacts/decisions)
  thin capsule  -> receiver redoes 4 of 4 things; facts-vs-open split + artifacts-by-reference + decisions log keep handoffs lossless
F6 failure handling
  no ack after retries -> dead_letter(reason='no_ack'), never silent; ledger [1.0, 1.5, 2.25] -> ack on attempt 2
  8 clients, no jitter: all retry at [0.5, 1.0, 2.0, 4.0] s - four synchronized waves re-trip the limiter they escaped
  seeded jitter spreads the same 8 clients: [0.82, 1.01, 2.14, 4.11] s (tenacity calls it wait_random_exponential; SDK max_retries covers it)
  429 Retry-After 3.0s vs computed 2.0s -> pause = max() = 3.0s (server hint beats your curve)
  async rule: time.sleep blocks the whole event loop - await asyncio.sleep
F7 budget propagation
  parent 50000 tok -> 3 children x 16,666 tok each
  child-2 exhausts its share -> fails fast; parent replans instead of burning siblings' budget
  exhausted this run: ['child-2']; budgets enforced at the bus level
```
