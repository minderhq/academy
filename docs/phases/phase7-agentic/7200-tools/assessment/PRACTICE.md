---
Document ID: 7200-PRACTICE
Title: "7200: Tools & Function Calling - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
---

# 7200: Tools & Function Calling - Practice

## Exercises

### Exercise 1: Define Custom Tools

```python
from langchain_core.tools import tool
from typing import Optional

# SOLUTION: Define calculator tool - Complete implementation with error handling
@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression like "2 + 2" or "5 * (3 + 2)"

    Returns:
        The result of the calculation
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# SOLUTION: Define search tool - Returns formatted results
@tool
def search_web(query: str, num_results: int = 5) -> str:
    """Search the web for information.

    Args:
        query: The search query
        num_results: Number of results to return (default: 5)

    Returns:
        Search results as formatted text
    """
    # Simplified - in production, use actual search API
    results = [
        f"Result {i+1}: {query} - relevant information here"
        for i in range(num_results)
    ]
    return "\n".join(results)

# SOLUTION: Define weather tool - Returns weather information
@tool
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get current weather for a location.

    Args:
        location: City name or coordinates
        unit: Temperature unit (celsius or fahrenheit)

    Returns:
        Current weather information
    """
    # Simplified - in production, use weather API
    return f"Weather in {location}: 22°C, Partly cloudy"

# SOLUTION: List all tools with metadata
tools = [calculator, search_web, get_weather]

for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Args: {tool.args}\n")
```

### Exercise 2: Implement Tool Calling with OpenAI

```python
import json

from openai import OpenAI

client = OpenAI()

# SOLUTION: Define tools schema for OpenAI function calling
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate",
                    },
                },
                "required": ["expression"],
            },
        },
    },
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
                        "description": "City name or coordinates",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit",
                    },
                },
                "required": ["location"],
            },
        },
    },
]

def run_with_tools(user_message):
    """Run conversation with tool calling."""

    # SOLUTION: Create initial message with user input
    messages = [{"role": "user", "content": user_message}]

    # SOLUTION: Get first completion with tool calls
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools_schema,
    )

    response_message = response.choices[0].message
    messages.append(response_message)

    # SOLUTION: Process tool calls and execute functions
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # SOLUTION: Execute the requested function. The @tool
            # decorator wraps the raw callable in .func, so invoke
            # that - calling the tool object directly is an error.
            if function_name == "calculator":
                result = calculator.func(**function_args)
            elif function_name == "get_weather":
                result = get_weather.func(**function_args)
            else:
                result = "Unknown function"

            # SOLUTION: Append function result to conversation
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": result,
            })

        # SOLUTION: Get final response after tool execution
        final_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
        )

        return final_response.choices[0].message.content

    return response_message.content

# SOLUTION: Test with complex query requiring multiple tools
result = run_with_tools("What's 15 * 23 plus the temperature in Paris?")
print(result)
```

### Exercise 3: Build Tool-Using Agent

```python
# NOTE: create_openai_functions_agent + AgentExecutor is the legacy
# LangChain 0.x API (removed in LangChain 1.x); the current path is
# langchain.agents.create_agent / LangGraph. The flow below still
# teaches the executor loop correctly.
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain import hub

# SOLUTION: Initialize ChatOpenAI with GPT-4
llm = ChatOpenAI(model="gpt-4", temperature=0)

# SOLUTION: Pull standard agent prompt from LangChain hub
prompt = hub.pull("hwchase17/openai-functions-agent")

# SOLUTION: Create OpenAI functions agent
tools = [calculator, search_web, get_weather]
agent = create_openai_functions_agent(llm, tools, prompt)

# SOLUTION: Create OpenAI functions agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True,
)

# SOLUTION: Invoke agent with test query
result = agent_executor.invoke({
    "input": "What's the square root of 144, and what's the weather in Tokyo?"
})

print(result["output"])
```

### Exercise 4: Multi-Step Tool Execution

```python
class ToolExecutor:
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}

    def execute_plan(self, plan):
        """Execute a plan with multiple tool calls."""

        results = []

        for step in plan["steps"]:
            tool_name = step["tool"]
            tool_args = step["args"]

            print(f"Executing: {tool_name}({tool_args})")

            # SOLUTION: Execute tool with error handling
            if tool_name in self.tools:
                result = self.tools[tool_name].func(**tool_args)
                results.append({
                    "step": step,
                    "result": result,
                    "success": True,
                })

                # SOLUTION: Handle step dependencies if specified
                if "depends_on" in step:
                    # Handle dependencies between steps
                    pass

            else:
                results.append({
                    "step": step,
                    "result": f"Tool {tool_name} not found",
                    "success": False,
                })

        return results

# SOLUTION: Define plan with sequential tool calls
plan = {
    "steps": [
        {
            "tool": "calculator",
            "args": {"expression": "15 * 23"},
        },
        {
            "tool": "get_weather",
            "args": {"location": "Paris"},
        },
        {
            "tool": "calculator",
            "args": {"expression": "100 + 50"},
        },
    ]
}

executor = ToolExecutor(tools)
results = executor.execute_plan(plan)
```

### Exercise 5: Tool Result Validation

```python
def validate_tool_result(tool_name, result):
    """Validate tool execution result."""

    validation = {
        "valid": True,
        "errors": [],
    }

    # SOLUTION: Validate result for errors and return structured validation
    if isinstance(result, str):
        if result.startswith("Error"):
            validation["valid"] = False
            validation["errors"].append(result)

    # SOLUTION: Add specific validation per tool type
    if tool_name == "calculator":
        try:
            float(result)
        except (ValueError, TypeError):
            validation["valid"] = False
            validation["errors"].append("Calculator should return a number")

    elif tool_name == "get_weather":
        if "weather" not in result.lower():
            validation["valid"] = False
            validation["errors"].append("Weather information missing")

    # SOLUTION: Ensure result is not empty
    if not result or (isinstance(result, str) and len(result.strip()) == 0):
        validation["valid"] = False
        validation["errors"].append("Empty result")

    return validation

# SOLUTION: Wrap tool calls with validation
def safe_tool_execution(tool, args):
    """Execute tool with validation."""

    try:
        # SOLUTION: Execute tool and catch exceptions
        result = tool.func(**args)

        # SOLUTION: Validate result before returning
        validation = validate_tool_result(tool.name, result)

        if not validation["valid"]:
            return {
                "success": False,
                "result": result,
                "errors": validation["errors"],
            }

        return {
            "success": True,
            "result": result,
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "errors": [str(e)],
        }
```

### Exercise 6: Parallel Tool Execution

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

async def execute_tools_parallel(tools_and_args):
    """Execute multiple tools in parallel."""

    results = {}

    # SOLUTION: Create parallel tasks for concurrent execution
    with ThreadPoolExecutor() as executor:
        futures = {}
        for item in tools_and_args:
            tool_name = item["tool"]
            tool_args = item["args"]

            future = executor.submit(execute_single_tool, tool_name, tool_args)
            futures[future] = tool_name

        # SOLUTION: Collect results from all tasks
        for future in as_completed(futures):
            tool_name = futures[future]
            try:
                result = future.result()
                results[tool_name] = result
            except Exception as e:
                results[tool_name] = {"error": str(e)}

    return results

def execute_single_tool(tool_name, tool_args):
    """Execute a single tool."""
    # Find and execute tool
    for tool in tools:
        if tool.name == tool_name:
            return tool.func(**tool_args)
    return f"Tool {tool_name} not found"

# SOLUTION: Execute tool and catch exceptions in parallel
parallel_tasks = [
    {"tool": "calculator", "args": {"expression": "15 * 23"}},
    {"tool": "get_weather", "args": {"location": "Paris"}},
    {"tool": "get_weather", "args": {"location": "Tokyo"}},
]

results = asyncio.run(execute_tools_parallel(parallel_tasks))
print(results)
```

### Exercise 7: Dynamic Tool Selection

```python
class ToolSelector:
    def __init__(self, tools, llm):
        self.tools = {tool.name: tool for tool in tools}
        self.llm = llm

    def select_tools(self, query):
        """Select relevant tools for a query."""

        # SOLUTION: Create formatted tool descriptions
        tool_desc = "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.tools.items()
        ])

        # SOLUTION: Prompt LLM to choose relevant tools
        prompt = f"""Given this query: "{query}"

Available tools:
{tool_desc}

Which tools are relevant? Respond as a JSON list of tool names.

Response:"""

        response = self.llm(prompt)

        # SOLUTION: Parse JSON response and validate
        try:
            selected = json.loads(response)
            if isinstance(selected, list):
                return [self.tools[name] for name in selected if name in self.tools]
        except:
            pass

        # Fallback: return all tools
        return list(self.tools.values())

# SOLUTION: Create selector and test with query
selector = ToolSelector(tools, llm)
query = "What's 25 * 34 and the weather in London?"

selected_tools = selector.select_tools(query)
print(f"Selected tools: {[t.name for t in selected_tools]}")
```
