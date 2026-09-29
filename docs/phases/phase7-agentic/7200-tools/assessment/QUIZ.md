---
Document ID: 7200-QUIZ
Title: "7200: Tool Calling - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
---

# 7200: Tool Calling - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is tool calling in LLM context?**

A) Calling external APIs based on LLM output
B) Using tools to train models
C) Tool-assisted generation
D) All of the above

**2. What is function calling?**

A) Calling Python functions
B) Code debugging
C) Function optimization
D) Structured output for API/function invocation

**3. What is the typical format for function calling output?**

A) Plain text
B) JSON with function name and parameters
C) XML
D) Binary format

**4. What is OpenAI's function calling format?**

A) JSON Schema
B) Python function signature
C) OpenAPI specification
D) Custom format

**5. What is a "tool" in agent context?**

A) Development tool
B) Any function/API the agent can use (search, calculator, code)
C) Hardware tool
D) Training utility

**6. What is required for tool definitions?**

A) Function name, description, parameters (schema)
B) Just function name
C) Source code
D) Documentation link

**7. What happens when an agent calls a tool?**

A) Tool result is fed back to LLM for reasoning
B) Tool result is returned to user directly
C) Tool result is ignored
D) Model is retrained

**8. What is "parallel tool calling"?**

A) Calling tools one after another
B) Calling multiple tools simultaneously in one request
C) Running tools on multiple GPUs
D) Concurrent model inference

**9. What is Code Interpreter / Code Execution?**

A) Compiling code
B) LLM generates and executes code in sandbox
C) Code optimization
D) Code review

**10. What is a common use case for tool calling?**

A) Text generation only
B) Querying databases, APIs, performing calculations
C) Image generation
D) Audio processing

**11. Tool arguments should be validated because:**

A) Tokenizers reject JSON
B) LLM output can be malformed or out of range before execution
C) APIs always self-validate
D) Validation improves model accuracy

**12. When a tool call fails, the standard agent pattern is to:**

A) Retry forever silently
B) Crash the agent
C) Return the error as an observation so the model can recover
D) Ignore it and continue without data

**13. Tool descriptions matter because:**

A) The model selects tools based on them
B) They speed up the GPU
C) They are required by OpenAI only
D) They compress context automatically

**14. Code Interpreter executes generated code in a sandbox in order to:**

A) Improve code style
B) Contain side effects and protect the host system
C) Reduce token count
D) Avoid JSON parsing

**15. The ReAct loop is:**

A) Reason → Act → Observe, repeated until the task is done
B) A single prompt
C) A tokenizer algorithm
D) A caching scheme

**16. Tool results re-enter the conversation as:**

A) System shutdown messages
B) The final user-facing answer
C) Observation messages the model can reason over
D) Training data

**17. Production tool integrations should implement:**

A) Unlimited retries
B) Synchronous-only calls
C) Timeouts, retries with backoff, and rate limiting
D) No logging

**18. Destructive (write) tool actions should:**

A) Always execute silently
B) Require confirmation or scoped permissions
C) Be avoided entirely
D) Bypass validation

**19. Enum-constrained parameters help because they:**

A) Restrict the model to valid values, reducing invalid calls
B) Increase output entropy
C) Remove the need for descriptions
D) Shorten the system prompt

**20. A multi-step tool chain is managed by:**

A) The agent loop, which decides the next tool until task completion
B) The database
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
