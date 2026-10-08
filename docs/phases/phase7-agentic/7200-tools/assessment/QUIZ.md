---
Document ID: 7200-QUIZ
Title: "7200: Tool Calling - Quiz"
Last Updated: 2026-10-08
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

- A) Invoking outside APIs from the model's own output
- B) Using external tools during pretraining to improve the model
- C) Tool-assisted generation
- D) A fine-tuning objective that ranks model outputs

**2. What is function calling?**

- A) Directly calling Python functions during generation
- B) Code debugging
- C) Function optimization
- D) Structured output for API/function invocation

**3. What is the typical format for function calling output?**

- A) Plain text with markdown links to the API docs
- B) Binary format
- C) XML envelopes defined by the SOAP protocol
- D) JSON with function name and parameters

**4. What is OpenAI's function calling format?**

- A) Custom format
- B) Python function signature
- C) OpenAPI specification
- D) JSON Schema

**5. What is a "tool" in agent context?**

- A) A code editor used by the developers building the agent
- B) Training utility
- C) Hardware tool
- D) Any function/API the agent can use (search, calculator, code)

**6. What is required for tool definitions?**

- A) Source code
- B) Just the function name, nothing else required
- C) Function name, description, parameters (schema)
- D) Documentation link

**7. What happens when an agent calls a tool?**

- A) Tool result is ignored
- B) The raw tool result is returned to the user with no further reasoning
- C) Tool result is fed back to LLM for reasoning
- D) Model is retrained

**8. What is "parallel tool calling"?**

- A) Calling tools one after another, waiting for each result before the next
- B) Concurrent model inference
- C) Running tools on multiple GPUs
- D) Calling multiple tools simultaneously in one request

**9. What is Code Interpreter / Code Execution?**

- A) Compiling the model's weights into machine code ahead of time
- B) LLM generates and executes code in sandbox
- C) Code optimization
- D) Code review

**10. What is a common use case for tool calling?**

- A) Generating text without ever touching external systems
- B) Querying databases, APIs, performing calculations
- C) Image generation
- D) Audio processing

**11. Tool arguments should be validated because:**

- A) The tokenizer would otherwise reject every JSON argument at inference time
- B) LLM output can be malformed or out of range before execution
- C) Every external API validates its own inputs completely with no gaps
- D) Model accuracy on benchmarks improves when tool arguments are validated

**12. When a tool call fails, the standard agent pattern is to:**

- A) Retry the same call forever in a silent loop until it succeeds
- B) Crash the agent
- C) Return the error as an observation so the model can recover
- D) Ignore it and continue without data

**13. Tool descriptions matter because:**

- A) The model selects tools based on them
- B) They make GPU kernels run faster during inference
- C) They are required by OpenAI only
- D) They compress context automatically

**14. Code Interpreter executes generated code in a sandbox in order to:**

- A) Improve the style and readability of the generated code
- B) Contain side effects and protect the host system
- C) Reduce token count
- D) Avoid JSON parsing

**15. The ReAct loop is:**

- A) Reason → Act → Observe, repeated until the task is done
- B) A single prompt that produces the full answer in one pass
- C) A tokenizer algorithm
- D) A caching scheme

**16. Tool results re-enter the conversation as:**

- A) Special system shutdown messages that terminate the session
- B) The final user-facing answer
- C) Observation messages the model can reason over
- D) Training data

**17. Production tool integrations should implement:**

- A) Unlimited retries with no backoff or jitter applied
- B) Synchronous-only calls
- C) Timeouts, retries with backoff, and rate limiting
- D) No logging

**18. Destructive (write) tool actions should:**

- A) Always execute silently without asking the user for approval
- B) Require confirmation or scoped permissions
- C) Be avoided entirely
- D) Bypass validation

**19. Enum-constrained parameters help because they:**

- A) Restrict the model to valid values, reducing invalid calls
- B) Increase the entropy of the model's output distribution randomly
- C) Remove the need for descriptions
- D) Shorten the system prompt

**20. A multi-step tool chain is managed by:**

- A) The agent loop, which decides the next tool until task completion
- B) The database, using stored procedures to schedule every single tool call
- C) The model's tokenizer
- D) The user, step by step

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | A | Tool calling invokes external APIs based on LLM output |
| 2 | D | Function calling is structured output for invoking functions |
| 3 | D | Output is JSON naming the function and its parameters |
| 4 | D | OpenAI describes callable functions with JSON Schema |
| 5 | D | A tool is any function or API the agent can call |
| 6 | C | Definitions need name, description and a parameter schema |
| 7 | C | Results feed back so the model can reason over them |
| 8 | D | Parallel calling runs several tools in one request |
| 9 | B | Code Interpreter runs generated code in a sandbox |
| 10 | B | Common uses span database queries, APIs and calculations |
| 11 | B | Validation catches malformed or out-of-range arguments |
| 12 | C | Failures return as observations the model can recover from |
| 13 | A | The model picks tools from their descriptions |
| 14 | B | Sandboxing contains side effects and protects the host |
| 15 | A | ReAct repeats Reason, Act, Observe until the task ends |
| 16 | C | Results return as observation messages to reason over |
| 17 | C | Production needs timeouts, backoff retries and rate limits |
| 18 | B | Write actions need confirmation or scoped permissions |
| 19 | A | Enums pin the model to valid values, cutting bad calls |
| 20 | A | The agent loop chains tool calls until the task completes |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-6, 8, 10, 13:** [7201: Tool Calling & Function Execution](../7201-Tool-Calling.md) — the request → tool_calls response → JSON arguments → external execution → tool-result cycle, tools as retrieval, computation and system-interaction functions and APIs, definitions carrying name, description and parameter schema, OpenAI-style JSON Schema with type, enum and required fields, the Tool Selection Process where descriptions drive the pick, and parallel tool calls executed from one response
- **Questions 7, 15-16:** [7101: ReAct Loop System](../../7100-architecture/7101-ReAct-Loop-System.md) — the Thought → Action → Observation loop repeated until the task ends, where each tool result re-enters as an observation the model reasons over
- **Questions 9, 14:** [7201: Tool Calling & Function Execution](../7201-Tool-Calling.md) — the Sandboxing section's builtins-stripping isolation that contains side effects and protects the host, with the Code Execution tool running generated code inside it
- **Questions 11, 19:** [7201: Tool Calling & Function Execution](../7201-Tool-Calling.md) — schema validation raising ValidationError on malformed or out-of-range arguments, and enum-constrained parameters pinning the model to valid values
- **Question 12:** [7201: Tool Calling & Function Execution](../7201-Tool-Calling.md) — structured error statuses from execute_tool that return the failure as data the model can recover from
- **Question 17:** [7204: Timeouts, Retries, and Rate Limits](../7204-Timeouts-Retries-and-Rate-Limits.md) — the client-side resilience triad as working code: the read budget that bounds the accepted-then-hung call (4/8-forever against 8.6s at 7/8), the idempotency-key ledger (6 entries with c2 twice against 5 receipts), jitter spreading 40 lockstep retries to a 19-of-40 peak, the caller-side bucket (41.0s of 429 taxes against 5.0s at zero), and the breaker's OPEN routing 2 calls around the brownout
- **Question 18:** [7201: Tool Calling & Function Execution](../7201-Tool-Calling.md) — the Permission System's check_permission gates ahead of sensitive tool actions
- **Question 20:** [7201: Tool Calling & Function Execution](../7201-Tool-Calling.md) — multi-step tool use where the loop decides each next call until the task completes
