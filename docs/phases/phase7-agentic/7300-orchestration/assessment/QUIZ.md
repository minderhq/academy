---
Document ID: 7300-QUIZ
Title: "7300: Agent Orchestration - Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'agents', 'orchestration']
---

# 7300: Agent Orchestration - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Agent orchestration manages:**

- A) Only a single agent, with no coordination or shared execution anywhere in the system
- B) No agents
- C) Multiple agent execution
- D) Only tools

**2. LangGraph is:**

- A) An orchestration framework
- B) A library for agents
- C) A database
- D) Not related

**3. Sequential execution:**

- A) Parallel execution, with every step launched at the same instant regardless of order
- B) Random order
- C) No execution
- D) One step after another

**4. Parallel execution:**

- A) One step at a time
- B) Sequential only
- C) Multiple steps simultaneously
- D) No execution

**5. DAG (Directed Acyclic Graph) in agents:**

- A) Undirected
- B) No structure
- C) No cycles, directed
- D) Has cycles, meaning control can loop back to earlier nodes and run them again freely

**6. State in orchestration:**

- A) Not tracked
- B) Shared between agents
- C) No state
- D) Only in one agent

**7. Conditional routing:**

- A) Based on state/results
- B) Always same path
- C) No routing
- D) Random routing, picking each branch by chance with no reference to state or results

**8. Human-in-the-loop:**

- A) Only at end
- B) Human approval for actions
- C) Only at start, with the run never pausing again for any approval after kickoff
- D) No human interaction

**9. Agent handoff:**

- A) Random
- B) Transfer between agents
- C) No handoff
- D) Only to a human, with agents never passing control to their peers at any point

**10. Subtasks in orchestration:**

- A) No subtasks
- B) Only one task, so nothing is ever broken into parts or delegated to separate workers
- C) Random tasks
- D) Decompose complex tasks

**11. Error recovery in orchestration:**

- A) Retry or alternative paths
- B) No errors
- C) Ignore errors
- D) Crash on the first error, abandoning every downstream task the moment anything fails

**12. Orchestration patterns include:**

- A) Sequential, parallel, hierarchical
- B) Only sequential, with parallel and hierarchical layouts banned from every workflow
- C) Only parallel
- D) No patterns

**13. AutoGen is:**

- A) An embedding model, turning agent conversations into vectors for a similarity search
- B) Not related
- C) A database
- D) An orchestration framework

**14. CrewAI is:**

- A) Not related
- B) An orchestration framework
- C) A training tool
- D) A monitoring tool, which only watches dashboards and never coordinates any agents

**15. Event-driven orchestration:**

- A) No events
- B) Random
- C) Triggered by events
- D) Polling based, with each component re-checking a shared flag on a fixed timer forever

**16. Workflow in agents:**

- A) Defined sequence of operations
- B) Random sequence
- C) No structure
- D) Only one operation, with no order of steps defined anywhere in the agent run

**17. Coordination between agents:**

- A) No coordination
- B) Only competition, where agents race for a shared prize and never exchange any state
- C) Independent only
- D) Communication and synchronization

**18. Orchestrator agent:**

- A) Same as worker agents
- B) Manages other agents
- C) Not needed
- D) No orchestrator

**19. Deadlock in orchestration:**

- A) Fast execution
- B) Not possible, because every runtime guarantees at least one path always terminates
- C) No waiting
- D) Agents waiting forever

**20. Orchestration vs chaining:**

- A) Chaining is more flexible, adapting freely at every step with no fixed plan of any kind
- B) No difference
- C) Orchestration is more flexible
- D) Same thing

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Orchestration coordinates multiple agents in one system |
| 2 | A | LangGraph is a graph-based orchestration framework |
| 3 | D | Sequential runs one step after another |
| 4 | C | Parallel runs several steps simultaneously |
| 5 | C | A DAG is directed with no cycles |
| 6 | B | State is shared between agents in the graph |
| 7 | A | Routing branches on current state and results |
| 8 | B | Human-in-the-loop pauses for human approval |
| 9 | B | Handoff transfers control between agents |
| 10 | D | Orchestration decomposes complex tasks into subtasks |
| 11 | A | Recovery retries or takes alternative paths |
| 12 | A | Patterns span sequential, parallel and hierarchical |
| 13 | D | AutoGen is a multi-agent orchestration framework |
| 14 | B | CrewAI is a role-based orchestration framework |
| 15 | C | Event-driven flows trigger on events, not polling |
| 16 | A | A workflow is a defined sequence of operations |
| 17 | D | Coordination mixes communication with synchronization |
| 18 | B | The orchestrator plans and manages worker agents |
| 19 | D | Deadlock leaves agents waiting on each other forever |
| 20 | C | Orchestration adapts dynamically, chains are fixed |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 3, 10-12, 16, 20:** [7301: Collaborative Tasking - Multi-Agent Synergy](../7301-Orchestration.md) — specialized agents coordinated in one system, the plan → execute → review → retry → synthesize flow, LLM-driven task decomposition, hierarchical-versus-peer-to-peer patterns, the defined sequence of operations, and the adaptive routing-and-retry that separates orchestration from a fixed chain
- **Questions 2, 5-6, 13-14:** [7303: Framework Comparison](../guides/7303-Framework-Comparison.md) — AutoGen, LangGraph and CrewAI as the orchestration frameworks, with LangGraph's typed state graph, conditional edges and checkpoint-backed resume; the DAG's no-cycle property as a formal definition lives in [7304](../7304-Event-Buses-Deadlocks-and-Human-Gates.md), where Kahn's stall names the exact four-node cycle set the feedback edge creates
- **Question 4:** [7201: Tool Calling & Function Execution](../../7200-tools/7201-Tool-Calling.md) — Parallel Tool Execution, the phase's only simultaneous-execution teaching
- **Questions 7, 15, 18-19:** [7304: Event Buses, Deadlocks, and Human Gates](../7304-Event-Buses-Deadlocks-and-Human-Gates.md) — the delivery ledger where the same six-task trace loses T3 under at-most-once, applies it twice under at-least-once, and skips the redelivery at the ledger under effectively-once, and the wait-for ring of length 3 that completes as six grants under a global acquisition order; the trigger-and-bound mechanics stay in [7301](../7301-Orchestration.md)
- **Question 8:** [7304: Event Buses, Deadlocks, and Human Gates](../7304-Event-Buses-Deadlocks-and-Human-Gates.md) — the mid-run gate where an interrupt checkpoints 84 bytes of run state and the resume splits approve (execute runs) from deny (fallback runs, execute never appears); quarantine as the escalation path stays in [7503](../../7500-security/7503-Adversarial-Attacks.md)
- **Question 9:** [7302: Multi-Agent Communication Protocols](../7302-Communication-Protocols.md) — the Handoff Protocol packaging agent-to-agent transfers without losing context
- **Question 17:** [7302: Multi-Agent Communication Protocols](../7302-Communication-Protocols.md) — consensus and negotiation patterns carrying the communication-and-synchronization mix
