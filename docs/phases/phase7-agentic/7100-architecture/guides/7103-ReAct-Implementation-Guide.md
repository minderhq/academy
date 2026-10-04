---
Document ID: 7103
Title: "7103: ReAct Agent Implementation Guide"
Phase: 7
Module: 7100
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'react', 'tool-calling']
---

# 7103: ReAct Agent Implementation Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Architecture Overview](#architecture-overview)
- [Complete Implementation](#complete-implementation)
- [Advanced Features](#advanced-features)
- [Production Deployment](#production-deployment)
- [Best Practices](#best-practices)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Walk the Thought→Action→Observation loop end-to-end: parse `Action: tool[input]` with a regex, validate it through a `ToolRegistry`, and bound the loop with `max_iterations`
- Extend the base `ReActAgent` into plan-and-execute (`MultiToolAgent`), self-correcting (`SelfCorrectingAgent`, `max_errors=3`), and hierarchical variants — and judge when each pays off
- Wire short-term and episodic memory (Qdrant) so an agent reuses context across runs without unbounded prompt growth
- Ship the agent to production on docker-compose/Kubernetes, passing model config, `QDRANT_URL`, and GPU limits explicitly
- Harden prompts, tool schemas, and error handling against the failure modes that silently break ReAct loops

---

## Abstract
Complete implementation guide for building production-ready ReAct (Reasoning + Acting) agents on Minder Academy infrastructure.

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        ReAct Agent                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Thought  │───▶│ Action   │───▶│Observation│───▶│ Thought  │ │
│  │          │    │          │    │          │    │          │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       ▲                                                    │   │
│       └────────────────────────────────────────────────────┘   │
│                         (Loop until done)                       │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Tool Registry                          │  │
│  │  - Search (Web/Vector)                                   │  │
│  │  - Calculator                                            │  │
│  │  - Code Interpreter (Sandboxed)                          │  │
│  │  - File Operations                                       │  │
│  │  - API Calls                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Memory System                           │  │
│  │  - Short-term: Current context                            │  │
│  │  - Long-term: VectorStore (Qdrant)                       │  │
│  │  - Episodic: Conversation history                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Complete Implementation

### Core ReAct Agent

```python
# react_agent.py
"""
Production-ready ReAct Agent for academy

Features:
- Tool calling with validation
- Memory integration (short + long term)
- Error handling and recovery
- Structured reasoning
- Observable execution
"""

import json
import re
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
import inspect

class ActionType(Enum):
    """Types of actions the agent can take"""
    SEARCH = "search"
    CALCULATE = "calculate"
    CODE_RUN = "code_run"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    API_CALL = "api_call"
    ANSWER = "answer"
    ERROR = "error"


@dataclass
class Thought:
    """A single reasoning step"""
    content: str
    step_number: int
    action_type: ActionType | None = None
    action_input: dict | None = None
    observation: str | None = None
    confidence: float = 0.5

    def to_dict(self) -> dict:
        return {
            "step": self.step_number,
            "thought": self.content,
            "action": self.action_type.value if self.action_type else None,
            "action_input": self.action_input,
            "observation": self.observation,
            "confidence": self.confidence,
        }


@dataclass
class Tool:
    """A tool that the agent can use"""
    name: str
    description: str
    function: Callable
    parameters: dict[str, Any] = field(default_factory=dict)

    def validate_input(self, input_data: dict) -> bool:
        """Validate input against required parameters"""
        required = self.parameters.get("required", [])
        for param in required:
            if param not in input_data:
                return False
        return True

    def execute(self, input_data: dict) -> str:
        """Execute the tool"""
        if not self.validate_input(input_data):
            return f"Error: Missing required parameters. Need: {self.parameters.get('required', [])}"

        try:
            result = self.function(**input_data)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"


class ToolRegistry:
    """Registry of available tools"""

    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> list[str]:
        """List all available tools"""
        return list(self.tools.keys())

    def get_tool_descriptions(self) -> str:
        """Get formatted descriptions for all tools"""
        descriptions = []
        for tool in self.tools.values():
            params = ", ".join(tool.parameters.get("required", []))
            desc = f"- {tool.name}({params}): {tool.description}"
            descriptions.append(desc)
        return "\n".join(descriptions)


class MemorySystem:
    """Memory system for the agent"""

    def __init__(self, qdrant_url: str = "http://192.168.1.100:6334"):
        self.short_term: list[dict] = []
        self.episodic: list[dict] = []

        # Long-term memory
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection = "agent_memory"

        # Setup collection
        self._setup_collection()

    def _setup_collection(self):
        """Setup Qdrant collection for long-term memory"""
        from qdrant_client.models import Distance, VectorParams

        try:
            self.qdrant.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        except (ValueError, UnexpectedResponse):
            pass  # Collection exists

    def add_short_term(self, content: str, metadata: dict | None = None):
        """Add to short-term memory"""
        self.short_term.append({
            "content": content,
            "metadata": metadata or {},
            "timestamp": __import__("time").time()
        })

        # Keep only last 20
        if len(self.short_term) > 20:
            self.short_term.pop(0)

    def add_episodic(self, episode: dict):
        """Add a complete episode to episodic memory"""
        self.episodic.append(episode)

    def search_long_term(self, query: str, k: int = 5) -> list[dict]:
        """Search long-term memory"""
        # This would use embeddings - simplified here
        return []


class ReActAgent:
    """
    Production ReAct Agent

    Features:
    - Structured reasoning with Thought-Action-Observation loop
    - Tool calling with validation
    - Memory integration
    - Error recovery
    - Observable execution
    """

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        max_iterations: int = 10,
        verbose: bool = True,
    ):
        self.max_iterations = max_iterations
        self.verbose = verbose

        # Load model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.float16,
            device_map="auto",
        )

        # Components
        self.tools = ToolRegistry()
        self.memory = MemorySystem()

        # Register default tools
        self._register_default_tools()

        # Execution trace
        self.trace: list[Thought] = []

    def _register_default_tools(self):
        """Register default tools"""

        # Calculator tool
        self.tools.register(Tool(
            name="calculate",
            description="Calculate mathematical expressions",
            function=self._calculate,
            parameters={"required": ["expression"]}
        ))

        # Search tool
        self.tools.register(Tool(
            name="search",
            description="Search for information",
            function=self._search,
            parameters={"required": ["query"]}
        ))

        # Code run tool
        self.tools.register(Tool(
            name="code_run",
            description="Execute Python code in a sandboxed environment",
            function=self._code_run,
            parameters={"required": ["code"]}
        ))

    def _calculate(self, expression: str) -> str:
        """Safe calculator"""
        try:
            # Only allow basic math
            allowed = set("0123456789+-*/(). ")
            if not all(c in allowed for c in expression):
                return "Error: Invalid characters in expression"
            return str(eval(expression, {"__builtins__": {}}, {}))
        except Exception as e:
            return f"Error: {str(e)}"

    def _search(self, query: str) -> str:
        """Search (simplified - would use vector search in production)"""
        return f"Search results for '{query}': [Simulated results]"

    def _code_run(self, code: str) -> str:
        """Run code in sandbox (simplified)"""
        # In production, use restricted Python environment
        try:
            result = eval(code, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    def _format_prompt(self, query: str, history: list[Thought] | None = None) -> str:
        """Format prompt for the LLM"""

        tool_descriptions = self.tools.get_tool_descriptions()

        prompt = f"""You are a helpful AI agent with access to tools.

Available tools:
{tool_descriptions}

Instructions:
1. Think step by step about the user's query
2. Decide which tool to use (if any)
3. Use the format: Thought: [your reasoning] then Action: tool_name[input]
4. After observing the result, continue thinking
5. When you have the answer, use: Action: answer[your final answer]

Query: {query}

"""

        if history:
            for thought in history[-5:]:  # Last 5 thoughts
                prompt += f"Thought: {thought.content}\n"
                if thought.action_type:
                    prompt += f"Action: {thought.action_type.value}[{thought.action_input}]\n"
                if thought.observation:
                    prompt += f"Observation: {thought.observation}\n"
                prompt += "\n"

        return prompt

    def _parse_response(self, response: str) -> Thought:
        """Parse LLM response into a Thought"""
        thought = Thought(content=response, step_number=len(self.trace) + 1)

        # Extract action
        action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response, re.DOTALL)

        if action_match:
            action_name = action_match.group(1).strip()
            action_input = action_match.group(2).strip()

            # Parse action type
            try:
                thought.action_type = ActionType(action_name)
            except ValueError:
                # Check if it's a tool
                if action_name in self.tools.list_tools():
                    thought.action_type = ActionType(action_name)
                else:
                    thought.action_type = ActionType.ERROR

            if thought.action_type == ActionType.ANSWER:
                thought.action_input = {"answer": action_input}
            elif thought.action_type != ActionType.ERROR:
                # Parse input as JSON or dict
                try:
                    thought.action_input = json.loads(action_input) if action_input else {}
                except Exception:
                    thought.action_input = {"input": action_input}

        return thought

    def run(self, query: str) -> dict:
        """
        Run the ReAct agent

        Args:
            query: User query
        Returns:
            Result with trace and final answer
        """
        self.trace = []
        self.memory.add_short_term(f"Query: {query}")

        for iteration in range(self.max_iterations):
            # Format prompt with history
            prompt = self._format_prompt(query, self.trace)

            # Generate response
            inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                do_sample=True,
            )
            response = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:],
                                            skip_special_tokens=True)

            if self.verbose:
                print(f"\n[Iteration {iteration + 1}]")
                print(f"LLM Response: {response}")

            # Parse response
            thought = self._parse_response(response)

            # Execute action if specified
            if thought.action_type:
                if thought.action_type == ActionType.ANSWER:
                    # Done!
                    answer = thought.action_input.get("answer", response)
                    thought.observation = "Final answer"
                    self.trace.append(thought)

                    return {
                        "answer": answer,
                        "trace": [t.to_dict() for t in self.trace],
                        "iterations": iteration + 1,
                    }

                elif thought.action_type == ActionType.ERROR:
                    thought.observation = "Unknown action - try again"
                    self.trace.append(thought)
                    continue

                else:
                    # Execute tool
                    tool = self.tools.get(thought.action_type.value)
                    if tool:
                        observation = tool.execute(thought.action_input or {})
                        thought.observation = observation

                        if self.verbose:
                            print(f"Action: {thought.action_type.value}")
                            print(f"Observation: {observation}")
                    else:
                        thought.observation = f"Tool '{thought.action_type.value}' not found"

            self.trace.append(thought)

            # Check if we should continue
            if thought.action_type == ActionType.ANSWER:
                break

        # Max iterations reached
        return {
            "answer": "Could not determine answer within maximum iterations",
            "trace": [t.to_dict() for t in self.trace],
            "iterations": self.max_iterations,
        }


# Example usage
def main():
    """Run the ReAct agent"""

    print("Initializing ReAct Agent...")

    agent = ReActAgent(
        model_name="mistralai/Mistral-7B-Instruct-v0.2",
        max_iterations=10,
        verbose=True,
    )

    # Test query
    query = "What is 15% of 237?"

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    result = agent.run(query)

    print(f"\n{'='*60}")
    print(f"Final Answer: {result['answer']}")
    print(f"Iterations: {result['iterations']}")
    print(f"{'='*60}")

    # Print trace
    print("\nExecution Trace:")
    for step in result['trace']:
        print(f"\nStep {step['step']}:")
        print(f"  Thought: {step['thought']}")
        if step['action']:
            print(f"  Action: {step['action']}")
        if step['observation']:
            print(f"  Observation: {step['observation']}")


if __name__ == "__main__":
    main()
```

---

## Advanced Features

### 1. Multi-Tool Collaboration

```python
class MultiToolAgent(ReActAgent):
    """Agent that can use multiple tools in sequence"""

    def plan_and_execute(self, query: str) -> dict:
        """Plan multiple steps then execute"""
        # First, create a plan
        plan_prompt = f"""Create a step-by-step plan to answer: {query}

Available tools: {', '.join(self.tools.list_tools())}

Format as:
1. [tool_name]: [description]
2. [tool_name]: [description]
...

Plan:"""

        plan = self._generate_text(plan_prompt)

        if self.verbose:
            print(f"\nPlan: {plan}")

        # Execute plan step by step
        steps = self._parse_plan(plan)
        for step in steps:
            result = self.run(step)
            if self.verbose:
                print(f"Step result: {result['answer']}")

        return result
```

### 2. Self-Correction

```python
class SelfCorrectingAgent(ReActAgent):
    """Agent that can detect and correct errors"""

    def run(self, query: str) -> dict:
        """Run with self-correction"""
        self.trace = []
        errors = 0
        max_errors = 3

        for iteration in range(self.max_iterations):
            prompt = self._format_prompt(query, self.trace)
            response = self._generate_text(prompt)

            thought = self._parse_response(response)

            # Check for errors
            if thought.action_type == ActionType.ERROR:
                errors += 1

                if errors >= max_errors:
                    # Try different approach
                    thought = self._generate_alternative(query, self.trace)

            # Execute and continue
            # ... (same as base class)

        return result
```

### 3. Hierarchical Planning

```python
class HierarchicalAgent(ReActAgent):
    """Agent with high-level and low-level reasoning"""

    def run(self, query: str) -> dict:
        """Run with hierarchical planning"""

        # High-level plan
        high_level_plan = self._create_high_level_plan(query)

        if self.verbose:
            print(f"High-level plan: {high_level_plan}")

        # Execute each sub-goal
        for sub_goal in high_level_plan:
            sub_result = self.run(sub_goal)
            self.memory.add_short_term(f"Completed: {sub_goal} -> {sub_result['answer']}")

        return self.run(query)  # Final synthesis
```

---

## Production Deployment

### Docker Compose Service

```yaml
# docker-compose-agent.yml

services:
  react-agent:
    build: ./agent
    container_name: academy-react-agent
    ports:
      - "8001:8000"
    environment:
      - MODEL_PATH=/models/mistral-7b-instruct
      - QDRANT_URL=http://qdrant:6334
      - MAX_ITERATIONS=15
      - LOG_LEVEL=INFO
    volumes:
      - ./models:/models:ro
      - ./agent/logs:/logs
    deploy:
      resources:
        limits:
          memory: 8G
    restart: unless-stopped
    networks:
      - academy-net
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: react-agent
  namespace: academy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: react-agent
  template:
    metadata:
      labels:
        app: react-agent
    spec:
      containers:
      - name: agent
        image: Minder Academy/react-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_PATH
          value: "/models/mistral-7b-instruct"
        - name: QDRANT_URL
          value: "http://qdrant:6334"
        resources:
          limits:
            nvidia.com/gpu: "1"
            memory: "10Gi"
```

---

## Best Practices

### 1. Prompt Engineering

```python
GOOD_PROMPT = """You are a helpful AI agent. Think step by step.

Question: {question}

Let me think about this..."""

BAD_PROMPT = """Answer: {question}"""
```

### 2. Tool Design

```python
# Good tool - clear, single purpose
def calculate(expression: str) -> float:
    """Calculate a mathematical expression"""
    return eval(expression, {"__builtins__": {}}, {})

# Bad tool - unclear, multi-purpose
def do_stuff(input: Any, action: str) -> Any:
    """Do various stuff"""
    # ...
```

### 3. Error Handling

```python
# Always handle tool errors gracefully
try:
    result = tool.execute(input_data)
except Exception as e:
    result = f"Tool error: {str(e)}"
    # Log and continue
```


---

## Summary

This guide takes ReAct from pattern to production on Minder Academy infrastructure: the full agent architecture, tool registry, error handling that keeps the loop alive, and the observability that shows what the agent actually did. Each section maps the loop's parts onto concrete implementation with failure paths. The rule it leaves: the difference between a demo agent and a production agent is not intelligence - it is the error handling, the trace, and the budget that stop a looped agent from looping forever.

## References

### Related Minder Academy Documents

- [7101: ReAct (Reasoning + Acting) Loop System](../7101-ReAct-Loop-System.md)
- [7102: Planning and Task Decomposition](../7102-Planning-Decomposition.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**

---

**Related:**
- [7101: ReAct Loop System](../7101-ReAct-Loop-System.md)
- [7102: Planning Decomposition](../7102-Planning-Decomposition.md)
- [7202: Code Interpreter](../../7200-tools/guides/7202-Code-Interpreter.md)
- [7401: Long-term Memory](../../7400-memory/7401-Long-term-Memory.md)
