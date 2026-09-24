# PROJECT TEMPLATE: Agent Framework

Build agentic systems with tools and memory.

## Project Structure

```
agent-framework/
├── README.md
├── requirements.txt
├── config/
│   ├── agents_config.yaml
│   ├── tools_config.yaml
│   └── memory_config.yaml
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py          # Base agent class
│   │   ├── reactive.py      # Reactive agent
│   │   └── autonomous.py    # Autonomous agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── calculator.py
│   │   ├── search.py
│   │   └── code_executor.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── short_term.py
│   │   ├── long_term.py
│   │   └── vector_store.py
│   ├── llm.py              # LLM interface
│   └── orchestrator.py     # Multi-agent coordination
├── api/
│   └── main.py
└── examples/
    ├── single_agent.py
    └── multi_agent.py
```

## Features

- Modular agent architecture
- Tool integration
- Memory systems (short/long term)
- Multi-agent orchestration
- API interface

## Quick Start

1. Define a simple agent:
```python
from src.agents.reactive import ReactiveAgent
from src.tools.calculator import CalculatorTool

agent = ReactiveAgent(
    name="math_helper",
    tools=[CalculatorTool()],
    llm_config={"model": "gpt-4"}
)

result = agent.run("What is 25 * 34?")
```

2. Run with memory:
```python
from src.agents.autonomous import AutonomousAgent
from src.memory.long_term import LongTermMemory

memory = LongTermMemory()
agent = AutonomousAgent(
    name="assistant",
    memory=memory,
    tools=[...]
)

agent.remember("user_prefers_dark_mode", True)
agent.run("Remember my preferences")
```

## Tool Creation

Create custom tools:
```python
from src.agents.base import Tool

class CustomTool(Tool):
    name = "custom_tool"
    description = "Does something useful"

    def run(self, **kwargs):
        # Tool logic here
        return result
```

## Memory Types

- Short-term: Conversation history
- Long-term: Vector embeddings
- Entity: Named entity storage
- Summary: Compressed memories

## Multi-Agent Systems

Coordinate multiple agents:
```python
from src.orchestrator import Orchestrator

orchestrator = Orchestrator()
orchestrator.add_agent(researcher)
orchestrator.add_agent(writer)
orchestrator.add_agent(critic)

result = orchestrator.delegate("Write an article about AI")
```

---

**Difficulty:** Advanced
**Estimated Time:** 10-15 hours
**Skills:** Agents, Tools, Memory, Orchestration
