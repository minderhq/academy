---
Document ID: 7100-QUIZ
Title: "7100: Agent Architecture - Quiz"
Last Updated: 2026-09-29
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
D) None of the above

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
B) Short-term and long-term memory
C) Only conversation history
D) Only long-term stores, with the running context window never consulted during execution

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

A) Neither
B) Prompt engineering only
C) Both
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

| # | Answer |
|---|--------|
| 1 | B |
| 2 | A |
| 3 | A |
| 4 | B |
| 5 | C |
| 6 | D |
| 7 | A |
| 8 | C |
| 9 | D |
| 10 | B |
| 11 | C |
| 12 | C |
| 13 | D |
| 14 | A |
| 15 | B |
| 16 | C |
| 17 | D |
| 18 | B |
| 19 | A |
| 20 | B |
