---
Document ID: 7100-QUIZ
Title: "7100: Agent Architecture - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'agents', 'react']
---

# 7100: Agent Architecture - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. ReAct pattern stands for:**

A) React JavaScript framework
B) Reasoning + Acting
C) Reactive agents
D) A vector-store indexing scheme for agent memory

**2. ReAct agent loop:**

A) Thought → Action → Observation
B) Action comes first, observation last, with the thought never opening any turn
C) No loop
D) Observation arrives before the agent acts, letting the environment drive every step

**3. Tool use allows agents to:**

A) Interact with external systems
B) Only read files
C) No external interaction
D) Only generate raw text, with every action confined to the model's own vocabulary

**4. Agent memory includes:**

A) No memory
B) Only long-term stores, with the running context window never consulted during execution
C) Only conversation history
D) Short-term and long-term memory

**5. Reflection in agents:**

A) Random
B) No thinking
C) Thinking about past actions
D) Only future planning, with each completed step forgotten before the next one begins

**6. Multi-agent systems:**

A) Competing agents only, with every run ending in one winner and no cooperation at all
B) No agents
C) Single agent
D) Multiple agents collaborating

**7. Agent planning:**

A) Decomposes tasks
B) No planning
C) Only single step
D) Random actions

**8. Self-correction in agents:**

A) Agents can't correct
B) No errors
C) Agents detect and fix errors
D) Only humans correct, so each faulty run waits for a reviewer to patch every step by hand

**9. Tool calling format:**

A) Natural language only, parsed by hand for each provider with no shared schema anywhere
B) Random
C) No format
D) Structured (function name, arguments)

**10. Agent vs chain:**

A) No difference
B) Agent has autonomy, chain is fixed
C) Same thing
D) Chain keeps the autonomy while the agent executes a frozen script, reversed from how they work

**11. Function calling in LLMs:**

A) Retraining the model from scratch for every new tool
B) Prompt engineering only
C) Both prompt engineering and special training
D) Special training

**12. Agent evaluation:**

A) Only speed
B) Not needed
C) Success rate, efficiency, safety
D) Only accuracy, with latency, cost and safety metrics banned from every evaluation report

**13. Hierarchical agents:**

A) All agents equal, with every node holding identical authority and no coordinator anywhere
B) Random structure
C) No hierarchy
D) High-level + low-level agents

**14. Agent communication:**

A) Message passing
B) Only with humans
C) No communication
D) Only with tools

**15. Agent hallucination:**

A) Only in training
B) Agents make things up
C) Only with specific models
D) Never happens

**16. Constrained generation:**

A) Not possible
B) Random output
C) Guides output format
D) No constraints of any kind, with the model free to emit any shape it happens to prefer

**17. Agent state management:**

A) Not needed
B) Only tracks tools
C) Only tracks history, so goals, plans and tool results never enter the state at any point
D) Tracks agent beliefs

**18. Robustness in agents:**

A) Crashes on the first error, halting the entire run no matter how minor the failure was
B) Handles errors gracefully
C) Always works
D) No errors

**19. Agent safety:**

A) Critical for production
B) Only for testing
C) Not important at all, since production environments forgive every mistake by default
D) Optional

**20. Agent benchmarking:**

A) No benchmarks
B) Uses standard tasks
C) Only custom tasks
D) Not possible, because agent behavior is claimed too stochastic for any repeatable suite

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | B | ReAct pairs Reasoning with Acting in interleaved steps |
| 2 | A | The loop runs Thought, then Action, then Observation |
| 3 | A | Tools connect agents to external systems and APIs |
| 4 | D | Agent memory spans short-term context and long-term stores |
| 5 | C | Reflection means reviewing past actions to improve the next |
| 6 | D | Multi-agent systems coordinate several collaborating agents |
| 7 | A | Planning decomposes a task into ordered subtasks |
| 8 | C | Self-correction detects errors and retries with fixes |
| 9 | D | Tool calls are structured: function name plus JSON arguments |
| 10 | B | Agents choose their own steps, chains follow a fixed path |
| 11 | C | Function calling rests on training plus schema-aware prompting |
| 12 | C | Agent evaluation covers success rate, efficiency and safety |
| 13 | D | Hierarchies split high-level planners from low-level executors |
| 14 | A | Agents talk through message passing between nodes |
| 15 | B | Agents can hallucinate facts and tool inputs alike |
| 16 | C | Constrained generation guides output into a required format |
| 17 | D | State tracks beliefs, goals, plans and tool results |
| 18 | B | Robustness means handling errors gracefully, not crashing |
| 19 | A | Safety gates are critical before production traffic |
| 20 | B | Benchmarks score agents on standard repeatable tasks |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-2, 5, 8, 10, 17-18:** [7101: ReAct Loop System](../7101-ReAct-Loop-System.md) — the Reasoning + Acting pattern with its Thought → Action → Observation loop, the state management that carries goals and tool results across iterations, the Thought steps reviewing each observation, RobustReActAgent's retry-on-failure execution, and the autonomous step-choosing that separates an agent from a fixed chain; named reflection and self-correction patterns are taught nowhere in the curriculum, so Q5 and Q8 lean on the loop's review-and-retry mechanics
- **Questions 3, 9, 11, 16:** [7201: Tool Calling & Function Execution](../../7200-tools/7201-Tool-Calling.md) — tools connecting agents to external systems, explicit parameter schemas with a ToolRegistry that generates API schemas from registrations, and the structured response formats behind a call; capability-specific training for function calling and constrained or grammar-based generation are taught nowhere in the curriculum, so Q11 and Q16 lean on the schema discipline
- **Question 4:** [7401: Long-term Memory for Agents](../../7400-memory/7401-Long-term-Memory.md) — working memory as the short-term session context window sitting beside the long-term stores
- **Questions 6, 13:** [7301: Collaborative Tasking - Multi-Agent Synergy](../../7300-orchestration/7301-Orchestration.md) — specialized agents collaborating toward shared goals, with hierarchical versus peer-to-peer coordination chosen by task coupling
- **Question 7:** [7102: Planning and Task Decomposition](../7102-Planning-Decomposition.md) — LLM-backed sequential and hierarchical decomposition with max_depth-bounded recursion into ordered step lists
- **Questions 12, 15, 20:** [1503: LLM Observability](../../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) — latency, token and cost metrics with quality heuristics that flag candidate hallucinations from uncertainty, citation and implausible-number indicators, cross-phase from this module's architecture lessons; agent-specific evaluation suites and standard benchmark batteries are taught nowhere in the curriculum, so Q12 and Q20 lean on the observability measurement discipline
- **Question 14:** [7302: Multi-Agent Communication Protocols](../../7300-orchestration/7302-Communication-Protocols.md) — typed message schemas and envelopes with correlation IDs as the channel between agent nodes
- **Question 19:** [7503: Adversarial Attacks & Defense](../../7500-security/7503-Adversarial-Attacks.md) — the production deployment posture of detection, quarantine and human review behind calibrated gates
