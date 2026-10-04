---
Document ID: SOLUTION-LAB-013
Title: "SOLUTION-LAB-013: Advanced Function Calling"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Tags: ['solution', 'function-calling', 'agents']
---

# SOLUTION-LAB-013: Advanced Function Calling

## Overview
Complete solution for complex function calling with validation.

---

## Core Solution

```python
from pydantic import BaseModel, Field
from typing import Any

class WeatherTool(BaseModel):
    """Get current weather."""

    location: str = Field(..., description="City name")
    unit: str = Field(default="celsius", pattern="^(celsius|fahrenheit)$")

    def execute(self):
        # Call weather API
        return f"Weather in {self.location}: 22°C"


class CalculatorTool(BaseModel):
    """Perform calculations."""

    expression: str = Field(..., description="Math expression")

    def execute(self):
        try:
            result = eval(self.expression, {"__builtins__": {}}, {})
            return f"Result: {result}"
        except Exception:
            return "Invalid expression"


class FunctionCallingAgent:
    """Agent with multiple tools."""

    def __init__(self, llm):
        self.llm = llm
        self.tools = {
            "weather": WeatherTool,
            "calculator": CalculatorTool
        }

    def call_function(self, tool_name: str, **kwargs):
        """Call a tool by name."""
        tool_class = self.tools[tool_name]
        tool = tool_class(**kwargs)
        return tool.execute()

    def process(self, query: str):
        """Process query with function calling."""
        # 1. Determine which tool to use
        tool_decision = self.llm.generate(f"Query: {query}\nWhich tool? Options: {list(self.tools.keys())}")

        # 2. Extract parameters
        params = self._extract_params(query, tool_decision)

        # 3. Call tool
        result = self.call_function(tool_decision, **params)

        return result
```

---

**Difficulty:** ⭐⭐⭐ Advanced
