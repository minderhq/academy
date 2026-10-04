---
Document ID: 7200-TOOLS-README
Title: "7200: Tool Calling and Function Execution"
Last Updated: 2026-10-04
Status: Complete
Difficulty: Intermediate
Prerequisites: []
Estimated Time: 3 hours
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

- What tool calling is and why agents need it
- The tool calling mechanism and tool types
- OpenAI function calling
- Best practices and advanced patterns
- Tool calling security

**Experiments:**
- Implement tool calling from scratch
- Build custom tools
- Create tool router
- Handle tool errors

### 7202: Code Interpreter
**Safe Code Execution for Agents** (Guide)

- Sandbox architecture
- Resource management
- Safe execution
- Monitoring

**Guide:** [guides/7202-Code-Interpreter.md](./guides/7202-Code-Interpreter.md)

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 7100: [Agent Architecture](../7100-architecture/README.md) (ReAct loops)
- [ ] Modules 3100–3400: [Transformer Architectures](../../phase3-transformers/3400-architectures/README.md)
- [ ] Python programming proficiency
- [ ] API integration basics
- [ ] Understanding of JSON schemas

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** Tool calling, function execution, code interpreters
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Tool implementation projects
- **Duration:** 3 hours
- **Topics:**
  - Build custom tools
  - Implement code interpreter
  - Create API integrations
  - Handle tool errors gracefully
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **[7100: Agent Architecture](../7100-architecture/README.md)** (agent loops)
- **[7300: Multi-Agent Orchestration](../7300-orchestration/README.md)** (multi-agent workflows)
- **[7400: Agent Memory Systems](../7400-memory/README.md)** (tool results storage)
- **[7500: AI Agent Security](../7500-security/README.md)** (tool safety)

## Time Commitment

| Activity | Time |
|----------|------|
| [7201: Tool Calling](./7201-Tool-Calling.md) | 3 hours |
| Guide ([7202: Code Interpreter](./guides/7202-Code-Interpreter.md)) | 5 hours |
| Quiz | 30 minutes |
| Practice | 3 hours |
| **Total** | **11.5 hours** |

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

## Authoring Tools: The @tool Decorator

The hand-written dict above is the wire contract, but production code
rarely writes it by hand. LangChain's `@tool` decorator derives the
whole schema from the function itself — the name from the
function name, the description from the docstring, the parameters
from the type hints. One source of truth: edit the hint and the
schema follows, so schema drift (hand-maintained dict, drifted
implementation) cannot happen. The practice exercises build every
tool this way, and the orchestration module reuses the same
definitions: [assessment/PRACTICE.md](./assessment/PRACTICE.md).

The decorated function stays a function you can call, and becomes a
tool object carrying its generated contract:

```python
from langchain_core.tools import tool


@tool
def search_web(query: str, num_results: int = 5) -> str:
    """Search the web for information.

    Args:
        query: The search query.
        num_results: Number of results to return.
    """
    return f"[{num_results} results for {query!r}]"  # stand-in for a real client


print(search_web.name)         # search_web - from the function name
print(search_web.description)  # the docstring - what the model reads
print(search_web.args)         # parameter schemas - from the type hints

result = search_web.invoke({"query": "llmops", "num_results": 3})
```

The quality lever is the docstring: it is not documentation for
humans here, it is the description the model reads when choosing
among tools — docstring quality is tool-selection quality, the
same discipline the design principles below call clear descriptions.
The boundary: hand-written dicts stay right for framework-free
provider calls where the JSON schema is the entire integration (the
wire-level face is the tool-calling lesson's round trip); the
decorator wins wherever the schema and the implementation must move
together.

## From Tools to Agents: The create_agent Constructor

Every tool above is inert until something drives the loop: the model
decides, a tool executes, the result feeds back, the model decides
again. The 7201 lesson built that round trip by hand with raw provider
calls. In production you do not: LangChain 1.x's `create_agent` wires
the whole loop in one constructor call — model, tools, and
system prompt in; a compiled LangGraph graph out. AgentExecutor and
the hub prompt templates it replaced are gone (the migration is
annotated in exercise comments across this corpus); this is the
construct itself:

```python
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def word_count(text: str) -> int:
    """Count the words in a text."""
    return len(text.split())


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    llm,
    [word_count],
    system_prompt="Use your tools when they answer better than you can.",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "How many words: hello agent world"}]}
)
print(result["messages"][-1].content)  # the loop's final answer
```

The call is small because the decisions are already made: which tools
(the decorator-derived contracts above are what the model reads when
choosing), what persona, which model. What comes back is a graph, not
a wrapper — the orchestration module builds graphs by hand, and
its checkpointer face makes the same loop resumable. Invoke with a
messages dict, read the last message. The boundary: the constructor
changes the wiring, not the conversation — the
[tool-calling lesson's](./7201-Tool-Calling.md)
round trip still happens inside, which is why debugging starts there;
and when one agent is not enough, the
[orchestration module](../7300-orchestration/README.md)
composes these constructors into multi-agent graphs.

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

**Next Module:** [7300: Multi-Agent Orchestration](../7300-orchestration/README.md)

**Previous Module:** [7100: Agent Architecture](../7100-architecture/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 7 documentation.

