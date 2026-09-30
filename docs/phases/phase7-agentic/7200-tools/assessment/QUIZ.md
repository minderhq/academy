---
Document ID: 7200-QUIZ
Title: "7200: Tool Calling - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'agents', 'tool-calling']
---

# 7200: Tool Calling - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is tool calling in LLM context?**

A) Calling external APIs based on LLM output
B) Using external tools during pretraining to improve the model
C) Tool-assisted generation
D) All of the above

**2. What is function calling?**

A) Directly calling Python functions during generation
B) Code debugging
C) Function optimization
D) Structured output for API/function invocation

**3. What is the typical format for function calling output?**

A) Plain text with markdown links to the API docs
B) JSON with function name and parameters
C) XML envelopes defined by the SOAP protocol
D) Binary format

**4. What is OpenAI's function calling format?**

A) JSON Schema
B) Python function signature
C) OpenAPI specification
D) Custom format

**5. What is a "tool" in agent context?**

A) A code editor used by the developers building the agent
B) Any function/API the agent can use (search, calculator, code)
C) Hardware tool
D) Training utility

**6. What is required for tool definitions?**

A) Function name, description, parameters (schema)
B) Just the function name, nothing else required
C) Source code
D) Documentation link

**7. What happens when an agent calls a tool?**

A) Tool result is fed back to LLM for reasoning
B) The raw tool result is returned to the user with no further reasoning
C) Tool result is ignored
D) Model is retrained

**8. What is "parallel tool calling"?**

A) Calling tools one after another, waiting for each result before the next
B) Calling multiple tools simultaneously in one request
C) Running tools on multiple GPUs
D) Concurrent model inference

**9. What is Code Interpreter / Code Execution?**

A) Compiling the model's weights into machine code ahead of time
B) LLM generates and executes code in sandbox
C) Code optimization
D) Code review

**10. What is a common use case for tool calling?**

A) Generating text without ever touching external systems
B) Querying databases, APIs, performing calculations
C) Image generation
D) Audio processing

**11. Tool arguments should be validated because:**

A) The tokenizer would otherwise reject every JSON argument at inference time
B) LLM output can be malformed or out of range before execution
C) Every external API validates its own inputs completely with no gaps
D) Model accuracy on benchmarks improves when tool arguments are validated

**12. When a tool call fails, the standard agent pattern is to:**

A) Retry the same call forever in a silent loop until it succeeds
B) Crash the agent
C) Return the error as an observation so the model can recover
D) Ignore it and continue without data

**13. Tool descriptions matter because:**

A) The model selects tools based on them
B) They make GPU kernels run faster during inference
C) They are required by OpenAI only
D) They compress context automatically

**14. Code Interpreter executes generated code in a sandbox in order to:**

A) Improve the style and readability of the generated code
B) Contain side effects and protect the host system
C) Reduce token count
D) Avoid JSON parsing

**15. The ReAct loop is:**

A) Reason → Act → Observe, repeated until the task is done
B) A single prompt that produces the full answer in one pass
C) A tokenizer algorithm
D) A caching scheme

**16. Tool results re-enter the conversation as:**

A) Special system shutdown messages that terminate the session
B) The final user-facing answer
C) Observation messages the model can reason over
D) Training data

**17. Production tool integrations should implement:**

A) Unlimited retries with no backoff or jitter applied
B) Synchronous-only calls
C) Timeouts, retries with backoff, and rate limiting
D) No logging

**18. Destructive (write) tool actions should:**

A) Always execute silently without asking the user for approval
B) Require confirmation or scoped permissions
C) Be avoided entirely
D) Bypass validation

**19. Enum-constrained parameters help because they:**

A) Restrict the model to valid values, reducing invalid calls
B) Increase the entropy of the model's output distribution randomly
C) Remove the need for descriptions
D) Shorten the system prompt

**20. A multi-step tool chain is managed by:**

A) The agent loop, which decides the next tool until task completion
B) The database, using stored procedures to schedule every single tool call
C) The model's tokenizer
D) The user, step by step

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | A |
| 2 | D |
| 3 | B |
| 4 | A |
| 5 | B |
| 6 | A |
| 7 | A |
| 8 | B |
| 9 | B |
| 10 | B |
| 11 | B |
| 12 | C |
| 13 | A |
| 14 | B |
| 15 | A |
| 16 | C |
| 17 | C |
| 18 | B |
| 19 | A |
| 20 | A |
