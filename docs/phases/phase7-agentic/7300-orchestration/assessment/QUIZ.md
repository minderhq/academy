---
Document ID: 7300-QUIZ
Title: "7300: Agent Orchestration - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
---

# 7300: Agent Orchestration - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Agent orchestration manages:**

A) Only a single agent, with no coordination or shared execution anywhere in the system
B) No agents
C) Multiple agent execution
D) Only tools

**2. LangGraph is:**

A) An orchestration framework
B) A library for agents
C) A database
D) Not related

**3. Sequential execution:**

A) Parallel execution, with every step launched at the same instant regardless of order
B) Random order
C) No execution
D) One step after another

**4. Parallel execution:**

A) One step at a time
B) Sequential only
C) Multiple steps simultaneously
D) No execution

**5. DAG (Directed Acyclic Graph) in agents:**

A) Undirected
B) No structure
C) No cycles, directed
D) Has cycles, meaning control can loop back to earlier nodes and run them again freely

**6. State in orchestration:**

A) Not tracked
B) Shared between agents
C) No state
D) Only in one agent

**7. Conditional routing:**

A) Based on state/results
B) Always same path
C) No routing
D) Random routing, picking each branch by chance with no reference to state or results

**8. Human-in-the-loop:**

A) Only at end
B) Human approval for actions
C) Only at start, with the run never pausing again for any approval after kickoff
D) No human interaction

**9. Agent handoff:**

A) Random
B) Transfer between agents
C) No handoff
D) Only to a human, with agents never passing control to their peers at any point

**10. Subtasks in orchestration:**

A) No subtasks
B) Only one task, so nothing is ever broken into parts or delegated to separate workers
C) Random tasks
D) Decompose complex tasks

**11. Error recovery in orchestration:**

A) Retry or alternative paths
B) No errors
C) Ignore errors
D) Crash on the first error, abandoning every downstream task the moment anything fails

**12. Orchestration patterns include:**

A) Sequential, parallel, hierarchical
B) Only sequential, with parallel and hierarchical layouts banned from every workflow
C) Only parallel
D) No patterns

**13. AutoGen is:**

A) An embedding model, turning agent conversations into vectors for a similarity search
B) Not related
C) A database
D) An orchestration framework

**14. CrewAI is:**

A) Not related
B) An orchestration framework
C) A training tool
D) A monitoring tool, which only watches dashboards and never coordinates any agents

**15. Event-driven orchestration:**

A) No events
B) Random
C) Triggered by events
D) Polling based, with each component re-checking a shared flag on a fixed timer forever

**16. Workflow in agents:**

A) Defined sequence of operations
B) Random sequence
C) No structure
D) Only one operation, with no order of steps defined anywhere in the agent run

**17. Coordination between agents:**

A) No coordination
B) Only competition, where agents race for a shared prize and never exchange any state
C) Independent only
D) Communication and synchronization

**18. Orchestrator agent:**

A) Same as worker agents
B) Manages other agents
C) Not needed
D) No orchestrator

**19. Deadlock in orchestration:**

A) Fast execution
B) Not possible, because every runtime guarantees at least one path always terminates
C) No waiting
D) Agents waiting forever

**20. Orchestration vs chaining:**

A) Chaining is more flexible, adapting freely at every step with no fixed plan of any kind
B) No difference
C) Orchestration is more flexible
D) Same thing

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | C |
| 2 | A |
| 3 | D |
| 4 | C |
| 5 | C |
| 6 | B |
| 7 | A |
| 8 | B |
| 9 | B |
| 10 | D |
| 11 | A |
| 12 | A |
| 13 | D |
| 14 | B |
| 15 | C |
| 16 | A |
| 17 | D |
| 18 | B |
| 19 | D |
| 20 | C |
