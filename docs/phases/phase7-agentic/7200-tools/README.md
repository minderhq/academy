---
Document ID: 7200-TOOLS-README
Title: "7200: Tool Calling and Function Execution"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Beginner
Tags: ['module', 'agents', 'tool-calling']
---

# 7200: Tool Calling and Function Execution

## Module Overview

This module covers tool calling and function execution for AI agents, enabling LLMs to interact with external systems, APIs, and code execution environments. You'll learn to build agents that can take real-world actions.

**Why This Matters:**
- Tool calling transforms LLMs from chatbots to agents
- Agents need to interact with APIs, databases, and systems
- Code execution enables computation and analysis
- Foundation for practical AI applications

## Learning Objectives

After completing this module, you will be able to:

- **Tool Calling**: Implement function calling with LLMs
- **Code Interpretation**: Build safe code execution environments
- **API Integration**: Connect agents to external services
- **Tool Design**: Create effective tools for agents
- **Safety**: Secure tool execution and error handling

## Module Contents

### [7201: Tool Calling](./7201-Tool-Calling.md)
**Function Calling with LLMs**

- Tool calling fundamentals
- Function schemas and descriptions
- OpenAI/Anthropic function calling
- LangChain tool integration
- Tool selection and routing

**Experiments:**
- Implement tool calling from scratch
- Build custom tools
- Create tool router
- Handle tool errors

### 7202: Code Interpreter
**Safe Code Execution for Agents** (Guide)

- Sandbox code execution
- Python REPL environments
- Error handling and debugging
- File system access
- Code execution best practices

**Guide:** [guides/7202-Code-Interpreter.md](./guides/7202-Code-Interpreter.md)

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 7100: Agent Architecture (ReAct loops)
- [ ] Module 3100-3400: Transformer architectures
- [ ] Python programming proficiency
- [ ] API integration basics
- [ ] Understanding of JSON schemas

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)
### Practice Exercises
- **Format:** Tool implementation projects
- **Duration:** 8-10 hours
- **Topics:**
  - Build custom tools
  - Implement code interpreter
  - Create API integrations
  - Handle tool errors gracefully
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **7100: Architecture** (agent loops)
- **7300: Orchestration** (multi-agent workflows)
- **7400: Memory** (tool results storage)
- **7500: Security** (tool safety)

## Time Commitment

| Activity | Time |
|----------|------|
| Reading (7201) | 3 hours |
| Experiments (7201) | 4 hours |
| Guide (7202) | 2 hours |
| Practice | 8-10 hours |
| **Total** | **17-19 hours** |

## Resources

**Essential Frameworks:**
- OpenAI Function Calling
- Anthropic Tool Use
- LangChain Tools
- CrewAI Tools

**Code Execution:**
- E2B (code interpreter)
- Pyodide (Python in browser)
- RestrictedPython (sandboxed Python)

## Tool Schema Example

```python
tool_schema = {
    "name": "search_web",
    "description": "Search the web for information",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results",
                "default": 5
            }
        },
        "required": ["query"]
    }
}
```

## Common Tool Categories

| Category | Examples | Use Cases |
|----------|----------|----------|
| Search | Web search, RAG | Information retrieval |
| Computation | Calculator, code interpreter | Math and analysis |
| Data | Database queries, API calls | Data access |
| Productivity | Email, calendar, files | Automation |
| Development | Git, code execution | Coding assistance |

## Tool Design Principles

1. **Single Responsibility**: One task per tool
2. **Clear Descriptions**: LLM needs to understand purpose
3. **Well-Defined Inputs**: Specific, typed parameters
4. **Error Handling**: Return meaningful errors
5. **Idempotent**: Same input → same output

## Safety Considerations

| Risk | Mitigation |
|------|------------|
| Code execution | Sandboxing, timeouts |
| API abuse | Rate limiting, authentication |
| Data leaks | Input validation, logging |
| System damage | Read-only, permission limits |
| Cost control | Usage limits, monitoring |

## Tool Calling Flow

```text
User Query
    ↓
Agent Thought
    ↓
Tool Selection (LLM)
    ↓
Tool Execution
    ↓
Result Observation
    ↓
Agent Thought
    ↓
Continue or Finish
```

## Tips for Success

1. **Start simple**: Basic tools before complex ones
2. **Clear descriptions**: LLM must understand tools
3. **Handle errors**: Tools fail, agents adapt
4. **Log everything**: Debugging tool use is hard
5. **Test thoroughly**: Tools have real-world impact

## Common Pitfalls

1. **Poor descriptions:** LLM won't use tools correctly
2. **Too many tools:** Confuses the LLM
3. **Vague parameters:** Leads to wrong tool calls
4. **No error handling:** Agent gets stuck
5. **Ignoring safety:** Tools can cause damage

## Tool vs Function

| Aspect | Tool | Function |
|--------|------|----------|
| Context | Agent-aware | Standalone |
| Description | Natural language | Type signatures |
| Error Handling | Agent-level | Function-level |
| State | Often stateful | Usually stateless |
| Examples | Web search, DB query | Math, string ops |

## Code Execution Safety

| Risk | Mitigation |
|------|------------|
| Infinite loops | Timeout limits |
| File system | Sandbox, chroot |
| Network | Whitelist, proxy |
| Memory | Limits, monitoring |
| Dependencies | Fixed environment |

## When to Use Tools

| Scenario | Tool Approach |
|----------|---------------|
| Get current data | API / Search |
| Perform calculations | Calculator / Code |
| Modify system | System tools |
| Access database | Database tools |
| Generate content | Generation tools |

---

**Next Module:** [7300: Orchestration](../7300-orchestration/README.md)

**Previous Module:** [7100: Agent Architecture](../7100-architecture/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 7 documentation.

