---
Document ID: 7200-QUIZ
Title: "Module 7200: Tool Calling Quiz"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# Module 7200: Tool Calling Quiz

**Module:** Tool & Function Calling
**Document ID:** 7200
**Difficulty:** Intermediate
**Time:** 30 minutes

---

## Instructions

Select the best answer for each question. Answers are provided at the bottom.

---

## Questions

### 1. What is tool calling in LLM context?

A) Calling external APIs based on LLM output
B) Using tools to train models
C) Tool-assisted generation
D) All of the above

### 2. What is function calling?

A) Calling Python functions
B) Structured output for API/function invocation
C) Function optimization
D) Code debugging

### 3. What is the typical format for function calling output?

A) Plain text
B) JSON with function name and parameters
C) XML
D) Binary format

### 4. What is OpenAI's function calling format?

A) JSON Schema
B) Python function signature
C) OpenAPI specification
D) Custom format

### 5. What is a "tool" in agent context?

A) Development tool
B) Any function/API the agent can use (search, calculator, code)
C) Hardware tool
D) Training utility

### 6. What is required for tool definitions?

A) Function name, description, parameters (schema)
B) Just function name
C) Source code
D) Documentation link

### 7. What happens when an agent calls a tool?

A) Tool result is fed back to LLM for reasoning
B) Tool result is returned to user directly
C) Tool result is ignored
D) Model is retrained

### 8. What is "parallel tool calling"?

A) Calling tools one after another
B) Calling multiple tools simultaneously in one request
C) Running tools on multiple GPUs
D) Concurrent model inference

### 9. What is Code Interpreter / Code Execution?

A) Compiling code
B) LLM generates and executes code in sandbox
C) Code optimization
D) Code review

### 10. What is a common use case for tool calling?

A) Text generation only
B) Querying databases, APIs, performing calculations
C) Image generation
D) Audio processing

---

## Answers

1. **A** - LLM generates structured output to trigger external tool/API calls
2. **B** - Structured JSON output specifying function and arguments
3. **B** - JSON: {"name": "func", "arguments": {...}}
4. **A** - Functions defined using JSON Schema for parameters
5. **B** - Any capability the agent can invoke: web search, calculator, code execution
6. **A** - Name, description, and JSON schema for parameters
7. **A** - Tool output becomes context for LLM to continue reasoning
8. **B** - Single request can call multiple tools at once
9. **B** - Execute generated Python code in sandboxed environment
10. **B** - Real-time data access, computation, external actions

---

**Score:** ___ / 10
**Passing:** 7/10

**Next:** Review [PRACTICE.md](./PRACTICE.md) for hands-on exercises
