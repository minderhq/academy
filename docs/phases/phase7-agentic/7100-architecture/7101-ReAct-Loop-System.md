---
Document ID: 7101
Title: "7101: ReAct (Reasoning + Acting) Loop System"
Phase: 7
Module: 7100
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: Phase 6 completion (RAG systems), Python async/await
Related: [7102, 7201, 7301, 7401]
Tags: [agents, react, reasoning, acting, tool-calling, autonomy]
Hardware: [GPU recommended for LLM inference]
Software: [Python 3.13+, LangChain, LlamaIndex]
---

# 7101: ReAct (Reasoning + Acting) Loop System

## Abstract

ReAct (Reasoning + Acting) is a foundational pattern for building AI agents that can reason through complex tasks and take actions using external tools. This document covers the Thought-Action-Observation loop structure, implementation patterns for tool calling, state management strategies, and production considerations for building robust autonomous agents.

---

## Table of Contents

- [1. Overview](#1-overview)
- [Learning Objectives](#learning-objectives)
- [2. The ReAct Pattern](#2-the-react-pattern)
- [3. Implementation](#3-implementation)
- [4. Tool Calling](#4-tool-calling)
- [5. State Management](#5-state-management)
- [6. Production Considerations](#6-production-considerations)
- [7. Advanced Patterns](#7-advanced-patterns)
- [8. References](#8-references)

---

## 1. Overview

### 1.1 Purpose

ReAct enables AI agents to:
- Break down complex tasks into reasoning steps
- Use external tools and APIs
- Observe results and adjust strategy
- Achieve goals through iterative planning

### 1.2 Prerequisites

- **Math:** Understanding of state machines, graph algorithms
- **Programming:** Python, async/await patterns
- **Previous:** [6201: Hybrid Search](../../phase6-rag/6200-retrieval/6201-Hybrid-Search.md)

## Learning Objectives
After completing this document, you will:
- ✅ Implement the ReAct loop from scratch
- ✅ Design effective tool interfaces
- ✅ Manage agent state across iterations
- ✅ Handle errors and recoveries
- ✅ Optimize for production deployment

---

## 2. The ReAct Pattern

### Basic Loop Structure
```text
ReAct Loop:
  Thought: Analyze current state and decide next action
  Action: Execute the action (tool call, query, etc.)
  Observation: Observe the result
  → Repeat until goal reached or max iterations

Example:
  Thought: I need to find the capital of France
  Action: Search[capital of France]
  Observation: Paris is the capital of France
  Thought: Now I have the answer
  Action: Finish[Paris]
```

### ReAct vs Standard Reasoning
```yaml
Standard (Chain of Thought):
  - Single forward pass
  - No intermediate actions
  - Limited to knowledge in model

ReAct:
  - Multiple iterations
  - Can use tools/external knowledge
  - Can observe and adjust
  - More robust for complex tasks
```

---

## 3. Implementation

### Basic ReAct Agent
```python
import re
from typing import Any

class ReActAgent:
    """
    ReAct: Reasoning and Acting agent
    """
    def __init__(self, llm, tools: dict[str, callable], max_iterations=10):
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations

    def run(self, query: str) -> str:
        """
        Run ReAct loop for query
        """
        # Initialize
        thought = self._initial_thought(query)
        history = [
            {"role": "user", "content": query},
            {"role": "assistant", "content": f"Thought: {thought}"}
        ]

        # Main loop
        for iteration in range(self.max_iterations):
            # Generate action based on thought
            action = self._generate_action(history)

            # Check for finish
            if action["type"] == "finish":
                return action["result"]

            # Execute action
            observation = self._execute_action(action)

            # Add to history
            history.append({
                "role": "assistant",
                "content": f"Action: {self._format_action(action)}"
            })
            history.append({
                "role": "user",
                "content": f"Observation: {observation}"
            })

            # Generate next thought
            thought = self._generate_thought(history)
            history.append({
                "role": "assistant",
                "content": f"Thought: {thought}"
            })

        return self._generate_final_response(history)

    def _generate_action(self, history: list[dict]) -> dict[str, Any]:
        """Generate next action based on history"""
        prompt = self._format_prompt(history)
        response = self.llm.generate(prompt)

        # Parse action from response
        return self._parse_action(response)

    def _execute_action(self, action: dict[str, Any]) -> str:
        """Execute action and return observation"""
        tool_name = action["tool"]
        tool_input = action["input"]

        if tool_name not in self.tools:
            return f"Error: Tool {tool_name} not found"

        try:
            result = self.tools[tool_name](**tool_input)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
```

---

## 4. Tool Calling

### Tool Interface Design
```python
from typing import Callable
from pydantic import BaseModel, Field

class ToolSchema(BaseModel):
    """Schema for tool definitions"""
    name: str
    description: str
    parameters: dict
    function: Callable

class ToolRegistry:
    """Registry for available tools"""
    def __init__(self):
        self.tools = {}

    def register(self, schema: ToolSchema):
        """Register a new tool"""
        self.tools[schema.name] = schema
        return schema

    def get_tool(self, name: str) -> ToolSchema:
        """Get tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> list[str]:
        """List all available tools"""
        return list(self.tools.keys())

# Example tools
def search_web(query: str) -> str:
    """Search the web for information"""
    # Implementation
    return f"Search results for: {query}"

def calculate(expression: str) -> str:
    """Calculate mathematical expression"""
    try:
        result = eval(expression)
        return str(result)
    except:
        return "Error: Invalid expression"

# Register tools
registry = ToolRegistry()
registry.register(ToolSchema(
    name="search",
    description="Search the web for information",
    parameters={"query": {"type": "string", "description": "Search query"}},
    function=search_web
))

registry.register(ToolSchema(
    name="calculate",
    description="Calculate mathematical expressions",
    parameters={"expression": {"type": "string", "description": "Math expression"}},
    function=calculate
))
```

---

## 5. State Management

### Agent State
```python
from dataclasses import dataclass

from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    FINISHED = "finished"
    ERROR = "error"

@dataclass
class AgentState:
    """State for ReAct agent"""
    query: str
    current_step: int
    max_steps: int
    thought: str | None = None
    last_action: dict | None = None
    last_observation: str | None = None
    history: list[dict] | None = None
    status: AgentStatus = AgentStatus.IDLE
    error: str | None = None

    def __post_init__(self):
        if self.history is None:
            self.history = []

class StateManager:
    """Manage agent state across iterations"""
    def __init__(self):
        self.states = {}

    def create_state(self, agent_id: str, query: str, max_steps: int) -> AgentState:
        """Create new state for agent"""
        state = AgentState(
            query=query,
            current_step=0,
            max_steps=max_steps,
            status=AgentStatus.IDLE
        )
        self.states[agent_id] = state
        return state

    def update_state(self, agent_id: str, **kwargs) -> AgentState:
        """Update agent state"""
        state = self.states.get(agent_id)
        if state:
            for key, value in kwargs.items():
                setattr(state, key, value)
        return state

    def get_state(self, agent_id: str) -> AgentState | None:
        """Get current state"""
        return self.states.get(agent_id)
```

---

## 6. Production Considerations

### Error Handling
```python
class ReActError(Exception):
    """Base exception for ReAct errors"""
    pass

class ToolExecutionError(ReActError):
    """Raised when tool execution fails"""
    pass

class MaxIterationsError(ReActError):
    """Raised when max iterations exceeded"""
    pass

class RobustReActAgent(ReActAgent):
    """Production-ready ReAct agent with error handling"""

    def run(self, query: str) -> str:
        """Run with comprehensive error handling"""
        try:
            state = self.state_manager.create_state("agent_1", query, self.max_iterations)

            for iteration in range(self.max_iterations):
                try:
                    # Generate and execute action
                    action = self._generate_action_with_validation(state)
                    observation = self._execute_action_with_retry(action)

                    # Update state
                    state = self.state_manager.update_state(
                        "agent_1",
                        current_step=iteration + 1,
                        last_action=action,
                        last_observation=observation,
                        status=AgentStatus.ACTING
                    )

                    # Check for completion
                    if self._is_final_answer(observation):
                        return observation

                except ToolExecutionError as e:
                    # Recover from tool errors
                    state = self.state_manager.update_state(
                        "agent_1",
                        error=str(e),
                        status=AgentStatus.ERROR
                    )
                    continue

            raise MaxIterationsError(f"Max iterations {self.max_iterations} exceeded")

        except Exception as e:
            # Log and return error response
            self._log_error(e)
            return f"Error: Unable to complete task - {str(e)}"
```

---

## 7. Advanced Patterns

### Multi-Step Reasoning
```python
class HierarchicalReActAgent:
    """Agent with planning and execution phases"""

    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.planner = None

    def run(self, query: str) -> str:
        # Phase 1: Planning
        plan = self._create_plan(query)
        self.planner = plan

        # Phase 2: Execution
        results = []
        for step in plan.steps:
            result = self._execute_step(step)
            results.append(result)

            # Adjust plan if needed
            if step.requires_replanning:
                plan = self._revise_plan(plan, results)

        # Phase 3: Synthesis
        return self._synthesize_results(query, results)

    def _create_plan(self, query: str):
        """Create execution plan"""
        prompt = f"""
        Task: {query}

        Create a step-by-step plan to solve this task.
        For each step, specify:
        1. What needs to be done
        2. Which tools to use
        3. Expected output

        Format as JSON:
        {{
            "steps": [
                {{"description": "...", "tools": [...], "output": "..." }}
            ]
        }}
        """

        response = self.llm.generate(prompt)
        return Plan.from_dict(response)
```

---

## 8. References

### Academic Papers
- [1] Yao et al. "ReAct: Synergizing Reasoning and Acting in Language Models". ICLR, 2023.

### Documentation
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/overview) - Agent framework documentation
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Stateful agent framework

### Related PROJECT-OMEGA Documents
- [7102: Planning and Decomposition](./7102-Planning-Decomposition.md) - Task breakdown strategies
- [7201: Tool Calling](../7200-tools/7201-Tool-Calling.md) - Tool implementation
- [7301: Orchestration](../7300-orchestration/7301-Orchestration.md) - Multi-agent coordination
- [7401: Long-term Memory](../7400-memory/7401-Long-term-Memory.md) - Persistent memory systems

### Experiments
- [EXP_7101: ReAct](../../../../experiments/EXP_7101_REACT.md) - Build ReAct agent from scratch

### External Resources
- [ReAct Paper](https://arxiv.org/abs/2210.03629) - Original research paper
- [LangChain Agents Reference](https://reference.langchain.com/python/langchain/agents) - Implementation guide

---

## Next Steps

- Continue with: **[7102: Planning and Decomposition](./7102-Planning-Decomposition.md)**
- Practical: **[LAB-004: ReAct Agent](../../../learning-resources/labs/LAB-004-ReAct-Agent.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**

---

**Document ID:** 7101
