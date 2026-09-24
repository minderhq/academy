---
Document ID: 7201
Title: Tool Calling & Function Execution
Phase: 7
Module: 7200
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'tool-calling', 'function-calling', 'code-interpreter']
---

# 7201: Tool Calling & Function Execution

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

```
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

```
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
def search_web(query: str, num_results: int = 5) -> List[str]:
    """Search the web for current information"""
    pass

# Database Query
def query_database(sql: str) -> List[Dict]:
    """Execute SQL query on database"""
    pass

# Vector Search
def vector_search(embedding: List[float], top_k: int = 10) -> List[Doc]:
    """Search vector database for similar documents"""
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
def process_data(data: List[Dict], operation: str) -> List[Dict]:
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
def call_api(url: str, method: str, headers: Dict) -> Response:
    """Make HTTP request to API"""
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
import openai

client = openai.OpenAI()

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
    model="gpt-4",
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

    # Execute function
    result = get_stock_price(arguments["symbol"])

    # Get final response
    final_response = client.chat.completions.create(
        model="gpt-4",
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
```

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
def execute_tool(tool_name: str, arguments: Dict) -> Any:
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
```

### 3. Tool Registry Pattern

```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name: str, func: Callable, schema: Dict):
        self.tools[name] = {
            "function": func,
            "schema": schema
        }

    def execute(self, name: str, **kwargs):
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return self.tools[name]["function"](**kwargs)

    def get_schemas(self) -> List[Dict]:
        return [
            {"type": "function", "function": tool["schema"]}
            for tool in self.tools.values()
        ]
```

---

## Advanced Tool Calling Patterns

### 1. Multi-Step Tool Use

```
User: "Analyze the latest stock data and send me a report"

LLM Process:
1. Call get_stock_data() → Get data
2. Call analyze_data() → Analyze
3. Call generate_report() → Create report
4. Call send_email() → Send report
```

### 2. Parallel Tool Execution

```python
# LLM can call multiple tools simultaneously
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Get weather for Tokyo, London, and NYC"}],
    tools=[weather_tool]
)

# Response includes 3 parallel tool calls
tool_calls = response.choices[0].message.tool_calls
# [
#   {"name": "get_weather", "args": {"location": "Tokyo"}},
#   {"name": "get_weather", "args": {"location": "London"}},
#   {"name": "get_weather", "args": {"location": "NYC"}}
# ]
```

### 3. Streaming Tool Calls

```python
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    tools=tools,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.tool_calls:
        # Process tool call incrementally
        pass
```

---

## Tool Calling Security

### 1. Sandboxing

```python
# Restricted Python execution
import RestrictedPython
from RestrictedPython import compile_restricted

def safe_execute(code: str):
    """Execute code in restricted environment"""
    byte_code = compile_restricted(code, '<string>', 'exec')
    exec(byte_code, {'__builtins__': {}}, {})
```

### 2. Permission System

```python
class ToolPermission:
    def __init__(self):
        self.permissions = {
            "file_system": False,
            "network": False,
            "system": False
        }

    def check_permission(self, tool: str) -> bool:
        if tool.startswith("file_"):
            return self.permissions["file_system"]
        # ... other checks
        return True
```

### 3. Input Validation

```python
def validate_tool_input(tool_name: str, arguments: Dict) -> bool:
    # Validate argument types
    # Check for malicious input
    # Sanitize file paths
    # Limit resource usage
    pass
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
```
ReAct Agent → Uses Tool Calling → Executes Functions → Returns Result
```

---

## AI Engineering Curriculum Implementation

### Local Tool Registry

```python
# /home/omni/configs/tool_registry.py

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

## Next Steps

- Continue with: **[7301-Orchestration.md](./../7300-orchestration/7301-Orchestration.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Document ID:** 7201
**Related:** [7202: Code Interpreter](./guides/7202-Code-Interpreter.md), [7203: Framework Comparison](../7300-orchestration/guides/7303-Framework-Comparison.md)
**Next:** [7301: Orchestration](../7300-orchestration/7301-Orchestration.md)
