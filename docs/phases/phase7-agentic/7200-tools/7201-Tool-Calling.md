---
Document ID: 7201
Title: "7201: Tool Calling & Function Execution"
Phase: 7
Module: 7200
Last Updated: 2026-10-07
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'tool-calling', 'function-calling', 'code-interpreter']
---

# 7201: Tool Calling & Function Execution

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [What is Tool Calling?](#what-is-tool-calling)
- [Tool Calling Mechanism](#tool-calling-mechanism)
- [Tool Types](#tool-types)
- [OpenAI Function Calling](#openai-function-calling)
- [Tool Calling Best Practices](#tool-calling-best-practices)
- [Advanced Tool Calling Patterns](#advanced-tool-calling-patterns)
- [Tool Calling Security](#tool-calling-security)
- [Tool Calling vs ReAct](#tool-calling-vs-react)
- [Minder Academy Implementation](#minder-academy-implementation)
- [Experiment](#experiment)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Describe how tool calling extends an LLM — walk the request → tool_calls response → JSON arguments → external execution → tool-result message cycle that reaches APIs and live data
- Declare function schemas — write OpenAI-style tool definitions with type, description, enum and required fields so parameter extraction stays unambiguous
- Categorize tools by capability — information retrieval, computation and system-interaction tools, each carrying a different risk profile
- Complete the OpenAI tool-call round trip — inspect message.tool_calls, json.loads the string arguments, execute locally and return the tool result for the final answer
- Constrain model output with structured outputs — pass a strict json_schema response_format so answers arrive schema-valid by construction instead of parse-and-hope
- Apply tool-calling best practices — explicit parameter schemas over vague catch-alls, structured error statuses from execute_tool, and a ToolRegistry that generates its API schemas from registrations
- Recognize advanced patterns — multi-step tool chains, parallel tool calls in one response, and streaming deltas assembled by index into complete calls

---

## Abstract

Tool calling enables Large Language Models to interact with external systems, execute functions, and perform actions beyond text generation.

---

## What is Tool Calling?

Tool calling (also called function calling) allows LLMs to:
- **Execute external functions** based on user requests
- **Interact with APIs** and databases
- **Perform computations** and data processing
- **Control systems** and devices

### Traditional LLM vs Tool-Calling LLM

```text
Traditional LLM:
User: "What's the weather in Tokyo?"
LLM:  "I cannot access real-time weather data..."

Tool-Calling LLM:
User: "What's the weather in Tokyo?"
LLM:  [Calls weather API] → "In Tokyo, it's currently 22°C with clear skies."
```

---

## Tool Calling Mechanism

### 1. Function Definition

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g., Tokyo"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
]
```

### 2. Tool Selection Process

```text
┌─────────────────────────────────────────────────────────┐
│                     LLM Processing                      │
│                                                          │
│  1. Analyze user request                               │
│  2. Match request to available tools                   │
│  3. Extract required parameters                        │
│  4. Generate tool call                                 │
│  5. Execute tool (externally)                          │
│  6. Process tool result                                │
│  7. Generate final response                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3. Response Format

```json
{
  "content": null,
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"location\": \"Tokyo\", \"unit\": \"celsius\"}"
      }
    }
  ]
}
```

---

## Tool Types

### 1. Information Retrieval Tools

```python


# Web Search
def search_web(query: str, num_results: int = 5) -> list[str]:
    """Search the web for current information"""
    pass

# Database Query
def query_database(sql: str) -> list[dict]:
    """Execute SQL query on database"""
    pass

# Vector Search
def vector_search(embedding: list[float], top_k: int = 10) -> list[dict]:
    """Search vector database for similar documents;
    each hit is a document payload dict"""
    pass
```

### 2. Computation Tools

```python


# Code Execution
def execute_code(code: str, language: str = "python") -> str:
    """Execute code in sandboxed environment"""
    pass

# Mathematical Operations
def calculate(expression: str) -> float:
    """Calculate mathematical expression"""
    pass

# Data Processing
def process_data(data: list[dict], operation: str) -> list[dict]:
    """Process data with specified operation"""
    pass
```

### 3. System Interaction Tools

```python


# File Operations
def read_file(path: str) -> str:
    """Read file contents"""
    pass

# API Calls
def call_api(url: str, method: str, headers: dict) -> dict:
    """Make HTTP request to API; returns the parsed JSON body"""
    pass

# System Commands
def run_command(command: str) -> str:
    """Execute system command (careful!)"""
    pass
```

---

## OpenAI Function Calling

### Example Implementation

```python
import json

import openai

# Any OpenAI-compatible endpoint works — the cloud API or a local server
# (e.g. Ollama exposes one at base_url="http://localhost:11434/v1")
client = openai.OpenAI()


def get_stock_price(symbol: str) -> dict:
    """Stand-in for a real market-data API"""
    return {"symbol": symbol, "price": 227.48, "currency": "USD"}


# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get current stock price",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock symbol"}
                },
                "required": ["symbol"]
            }
        }
    }
]

# Make request
response = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "user", "content": "What's the price of AAPL?"}
    ],
    tools=tools
)

# Handle tool call
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    # Execute function locally
    result = get_stock_price(arguments["symbol"])

    # Send the tool result back for the final answer
    final_response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": "What's the price of AAPL?"},
            response.choices[0].message,
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            }
        ]
    )

print(final_response.choices[0].message.content)

# Output:
# AAPL is currently trading at $227.48 USD.
```

### Structured Outputs: Constrain the Answer Itself

Every tool in this lesson ships a JSON schema, but the model's final
answer ships none. The `tool_calls` envelope above was the JSON the
model sends **you**; structured outputs are the reverse face — a
contract on the JSON the model answers you with. When the answer must
be data a program consumes next — a triage verdict, an extraction,
an eval grade — free text buys you a parse-and-hope loop. The same
schema machinery covers it: `response_format` declaring the shape,
enforced by the provider. Function calling is structured output for
invoking functions; this is structured output for the answer.

Two faces exist, and they are not equivalent. `{"type": "json_object"}`
guarantees valid JSON — any JSON. Shape stays unvalidated, so your
callers keep validating after the fact (the long-term-memory fences
later in this phase ship exactly this weak form). The strong form is
`{"type": "json_schema", "json_schema": {..., "strict": true}}`:
constrained decoding — the provider cannot emit a token sequence
that violates your schema, enum values included, and the
parse-and-retry loop disappears:

```python
import json


def triage_freeform(client, model: str, ticket: str) -> dict:
    """The weak form: json_object - valid JSON, any shape, unvalidated."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": ticket}],
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    # json.loads proves syntax; nothing proves shape - callers validate after
    return result


def triage_contract(client, model: str, ticket: str) -> dict:
    """The strong form: json_schema + strict - the provider enforces shape."""
    schema = {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["refund", "escalate", "deny"]},
            "confidence": {"type": "number"},
            "reason": {"type": "string"},
        },
        "required": ["verdict", "confidence", "reason"],
        "additionalProperties": False,
    }
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": ticket}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "ticket_triage", "strict": True, "schema": schema},
        },
    )
    return json.loads(response.choices[0].message.content)
```

The strict-mode rules are strict for a reason: every property listed
under `required` plus `additionalProperties: False` — what the
provider must guarantee admits no ambiguity. With a typing layer the
schema stops being a dict you hand-write: define the `pydantic` model,
pass the class itself as the response format, and a parsed, validated
object comes back. The boundary line: structured outputs are for
answers a program consumes next — routing decisions, extraction,
grading. Prose a human reads gains nothing from a JSON straitjacket.
One schema machinery, two directions — into the model as tool
definitions, out of the model as answer contracts; the upgrade path
from the [7401 long-term-memory lesson's](../7400-memory/7401-Long-term-Memory.md)
weak `json_object` fences runs exactly through this subsection.

---

## Tool Calling Best Practices

### 1. Parameter Extraction

```python
# Good: Clear parameter definitions
{
    "name": "send_email",
    "parameters": {
        "to": {"type": "string", "description": "Recipient email"},
        "subject": {"type": "string", "description": "Email subject"},
        "body": {"type": "string", "description": "Email body"}
    }
}

# Bad: Vague parameters
{
    "name": "send_email",
    "parameters": {
        "args": {"type": "string", "description": "All arguments"}  # Too vague!
    }
}
```

### 2. Error Handling

```python
from typing import Any


class ValidationError(Exception):
    """Raised when arguments fail schema validation"""


class ExecutionError(Exception):
    """Raised when the tool itself fails"""


tool_registry = {
    "get_weather": lambda location, unit="celsius": f"22°C in {location}",
}


def execute_tool(tool_name: str, arguments: dict) -> Any:
    # Unknown tools get a structured error, not a KeyError
    if tool_name not in tool_registry:
        return {"status": "error", "error": f"Unknown tool: {tool_name}"}

    try:
        tool = tool_registry[tool_name]
        result = tool(**arguments)
        return {"status": "success", "result": result}
    except ValidationError as e:
        return {"status": "error", "error": f"Invalid parameters: {e}"}
    except ExecutionError as e:
        return {"status": "error", "error": f"Execution failed: {e}"}
    except Exception as e:
        return {"status": "error", "error": f"Unexpected error: {e}"}


def _boom(**kwargs):
    raise ExecutionError("upstream socket closed")


tool_registry["boom"] = _boom

print(execute_tool("get_weather", {"location": "Tokyo"}))
print(execute_tool("nope", {}))
print(execute_tool("boom", {}))

# Output:
# {'status': 'success', 'result': '22°C in Tokyo'}
# {'status': 'error', 'error': 'Unknown tool: nope'}
# {'status': 'error', 'error': 'Execution failed: upstream socket closed'}
```

### 3. Tool Registry Pattern

```python
from typing import Callable


class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name: str, func: Callable, schema: dict):
        self.tools[name] = {
            "function": func,
            "schema": schema
        }

    def execute(self, name: str, **kwargs):
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return self.tools[name]["function"](**kwargs)

    def get_schemas(self) -> list[dict]:
        return [
            {"type": "function", "function": tool["schema"]}
            for tool in self.tools.values()
        ]


registry = ToolRegistry()
registry.register(
    "get_weather",
    lambda location: f"22°C in {location}",
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
)

print(registry.execute("get_weather", location="Tokyo"))
print([t["function"]["name"] for t in registry.get_schemas()])

# Output:
# 22°C in Tokyo
# ['get_weather']
```

---

## Advanced Tool Calling Patterns

### 1. Multi-Step Tool Use

```text
User: "Analyze the latest stock data and send me a report"

LLM Process:
1. Call get_stock_data() → Get data
2. Call analyze_data() → Analyze
3. Call generate_report() → Create report
4. Call send_email() → Send report
```

### 2. Parallel Tool Execution

```python
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
}

# One request — the model may return multiple tool calls at once
response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "Get weather for Tokyo, London, and NYC"}],
    tools=[weather_tool]
)

# Response includes 3 parallel tool calls — execute them concurrently,
# then send one tool-result message per tool_call_id
tool_calls = response.choices[0].message.tool_calls
# [
#   tool_call.function.name == "get_weather",
#   json.loads(tool_call.function.arguments) == {"location": "Tokyo"},
#   ... {"location": "London"}, {"location": "NYC"}
# ]
```

### 3. Streaming Tool Calls

```python
import json

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
}]

stream = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "Weather in Tokyo?"}],
    tools=tools,
    stream=True
)

# Tool-call deltas arrive fragmented — accumulate them by index until
# each call's arguments form a complete JSON string
assembled = {}
for chunk in stream:
    for delta in chunk.choices[0].delta.tool_calls or []:
        slot = assembled.setdefault(delta.index, {"arguments": ""})
        if delta.id:
            slot["id"] = delta.id
        if delta.function and delta.function.name:
            slot["name"] = delta.function.name
        if delta.function and delta.function.arguments:
            slot["arguments"] += delta.function.arguments

calls = [assembled[i] for i in sorted(assembled)]
for call in calls:
    print(call["name"], json.loads(call["arguments"]))

# Output:
# get_weather {'location': 'Tokyo'}
```

---

## Tool Calling Security

### 1. Sandboxing

```python
from RestrictedPython import compile_restricted


def safe_execute(code: str) -> dict:
    """Compile and run model-supplied code with builtins stripped.
    Builtins-stripping alone is not a hard sandbox — pair it with
    process-level isolation (containers, no network) for real defense."""
    byte_code = compile_restricted(code, '<string>', 'exec')
    namespace: dict = {}
    exec(byte_code, {'__builtins__': {}}, namespace)
    return namespace


result = safe_execute("answer = 6 * 7")
print(result["answer"])

# Output:
# 42
```

### 2. Permission System

```python
class ToolPermission:
    """Deny by default — capabilities must be granted explicitly"""

    def __init__(self):
        self.permissions = {
            "file_system": False,
            "network": False,
            "system": False
        }

    def check_permission(self, tool: str) -> bool:
        if tool.startswith("file_"):
            return self.permissions["file_system"]
        if tool.startswith("run_") or tool.startswith("exec_"):
            return self.permissions["system"]
        if tool.startswith(("call_api", "search_web", "query_")):
            return self.permissions["network"]
        return False  # unknown tools are denied, not waved through


perm = ToolPermission()
print(perm.check_permission("file_read"))      # False — not granted
perm.permissions["file_system"] = True
print(perm.check_permission("file_read"))      # True — granted
print(perm.check_permission("run_command"))    # False
print(perm.check_permission("mystery_tool"))   # False — deny by default

# Output:
# False
# True
# False
# False
```

### 3. Input Validation

```python


def validate_tool_input(tool_name: str, arguments: dict) -> bool:
    """Pre-execution validation: name shape, payload size, path safety"""
    if not tool_name or not tool_name.replace("_", "").isalnum():
        return False
    for key, value in arguments.items():
        if isinstance(value, str) and len(value) > 2000:
            return False  # resource limit
        if "path" in key and isinstance(value, str):
            if ".." in value or value.startswith("/"):
                return False  # path traversal / absolute escape
    return True


print(validate_tool_input("get_weather", {"location": "Tokyo"}))   # True
print(validate_tool_input("read_file", {"path": "../etc/passwd"})) # False
print(validate_tool_input("read_file", {"path": "/etc/passwd"}))   # False
print(validate_tool_input("bad name!", {}))                        # False

# Output:
# True
# False
# False
# False
```

---

## Tool Calling vs ReAct

| Aspect | Tool Calling | ReAct |
|--------|--------------|-------|
| **Control Flow** | LLM decides | Agent loop |
| **Transparency** | Structured | Reasoning steps |
| **Flexibility** | Framework-specific | Framework-agnostic |
| **Implementation** | API-driven | Prompt-based |

Both patterns can be combined:
```text
ReAct Agent → Uses Tool Calling → Executes Functions → Returns Result
```

---

## Minder Academy Implementation

### Local Tool Registry

```python
# /home/omni/configs/tool_registry.py
from homelab_tools import (
    get_gpu_stats,
    get_disk_space,
    k8s_list_pods,
    k8s_get_logs,
    run_llm_inference,
    quantize_model,
)

tools = {
    # System tools
    "nvidia_smi": {
        "function": get_gpu_stats,
        "description": "Get GPU utilization and memory"
    },
    "disk_usage": {
        "function": get_disk_space,
        "description": "Get disk usage across NAS"
    },

    # K8s tools
    "list_pods": {
        "function": k8s_list_pods,
        "description": "List all running pods"
    },
    "get_pod_logs": {
        "function": k8s_get_logs,
        "description": "Get logs from a specific pod"
    },

    # Model tools
    "run_inference": {
        "function": run_llm_inference,
        "description": "Run LLM inference with specified model"
    },
    "quantize_model": {
        "function": quantize_model,
        "description": "Quantize model to specified format"
    }
}
```

---

## Experiment

**Objective:** Test tool calling accuracy and parameter extraction

**Methodology:**
1. Define 10 tools with varying complexity
2. Create 50 test queries
3. Measure: tool selection accuracy, parameter extraction F1

**Expected Results:**
- Tool selection: >95% accuracy
- Parameter extraction: >90% F1 score


---

## Summary

Tool calling is how an LLM's text becomes action: the model emits a structured request - function name plus arguments - the host executes it, and the result returns as a new message. This lesson covered the request/response contract, schema design that keeps arguments valid, and the execution patterns for external systems beyond text generation. The rule it leaves: the tool schema is an API contract with a probabilistic client - design it so the model cannot be validly wrong, and validate everything anyway.

## References

### Related Minder Academy Documents

- [7200: Tool Calling and Function Execution](README.md)
- [7202: Code Interpreter](guides/7202-Code-Interpreter.md)
- [7101: ReAct (Reasoning + Acting) Loop System](../7100-architecture/7101-ReAct-Loop-System.md)

---

## Next Steps

- Continue with: **[7301: Orchestration](../7300-orchestration/7301-Orchestration.md)**
- Assessment: **[QUIZ](./assessment/QUIZ.md)**
