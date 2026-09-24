---
Document ID: SOLUTION-LAB-004
Title: "SOLUTION-LAB-004: ReAct Agent"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Intermediate
---

# SOLUTION-LAB-004: ReAct Agent

## Overview
Complete solution for building a ReAct (Reasoning + Acting) agent.

---

## Core Solution

```python
from typing import List, Dict, Callable
import json

class Tool:
    def __init__(self, name: str, func: Callable, description: str):
        self.name = name
        self.func = func
        self.description = description

class ReActAgent:
    def __init__(self, llm, tools: List[Tool]):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}

    def run(self, query: str, max_steps: int = 10):
        prompt = query
        history = []

        for step in range(max_steps):
            # Thought
            thought = self.llm.generate(f"{prompt}\nThought:")
            history.append(f"Thought: {thought}")

            # Action
            action = self._parse_action(thought)

            if action["type"] == "finish":
                return action["answer"]

            if action["type"] == "tool":
                result = self.tools[action["tool"]].func(**action["input"])
                history.append(f"Observation: {result}")

                # Update prompt
                prompt = f"{prompt}\nThought: {thought}\nObservation: {result}\nThought:"

    def _parse_action(self, thought: str) -> Dict:
        # Parse "I should use TOOL_NAME..." or "Final answer is..."
        if "final answer" in thought.lower():
            return {"type": "finish", "answer": thought.split("is:")[-1]}
        # Parse tool call
        return {"type": "tool", "tool": "...", "input": {...}}

# Tools
def search_tool(query: str) -> str:
    return f"Search results for: {query}"

def calculator(expression: str) -> str:
    return str(eval(expression))

# Usage
agent = ReActAgent(llm, [
    Tool("search", search_tool, "Search the web"),
    Tool("calculator", calculator, "Calculate expressions")
])

result = agent.run("What is 25 * 34 + 10?")
```

---

**Last Updated:** 2026-02-04
**Difficulty:** ⭐⭐⭐⭐
