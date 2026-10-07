---
Document ID: 7303
Title: "7303: Multi-Agent Framework Comparison"
Phase: 7
Module: 7300
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'orchestration', 'multi-agent', 'autogen', 'langgraph', 'crewai']
---

# 7303: Multi-Agent Framework Comparison

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Framework Comparison Matrix](#framework-comparison-matrix)
- [AutoGen (Microsoft)](#autogen-microsoft)
- [LangGraph (LangChain)](#langgraph-langchain)
- [CrewAI](#crewai)
- [Recommendation](#recommendation)
- [Hybrid Approach](#hybrid-approach)
- [Performance Comparison](#performance-comparison)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Fill in a framework comparison matrix from architecture alone, then verify it against the published defaults
- Read AutoGen conversation code and identify which parts come from its 0.2-style API versus the 0.4+ agentchat rewrite
- Build a LangGraph state graph with typed state, conditional edges, and checkpoint-backed resume
- Map a role/goal/backstory trio onto CrewAI's task pipeline and predict its execution order
- Recommend a framework for a given task shape using an executable decision table rather than preference
- Structure a hybrid system where LangGraph owns the graph and an AutoGen agent owns each node

---

## Abstract
A comparison of the multi-agent frameworks used to build autonomous AI systems — AutoGen, LangGraph, CrewAI, and OpenAI's agent stack — across architecture, model support, state management, and operational maturity. The code in this guide is version-pinned reality: two fences compile against the real framework APIs, one decision table runs on plain Python, and the numbers that cannot be verified honestly are labeled as estimates.

## Framework Comparison Matrix

| Feature | AutoGen | LangGraph | CrewAI | Swarm (OpenAI) |
|---------|---------|-----------|--------|----------------|
| **Architecture** | Conversational | State Machine | Role-based | Orchestrated |
| **LLM Support** | OpenAI, Azure, Hugging Face | Any (via LangChain) | OpenAI, Claude, Local | OpenAI only |
| **Memory** | Built-in | Via checkpoint | Built-in | Via context |
| **Tool Calling** | Yes | Yes | Yes | Yes |
| **Human-in-Loop** | Yes | Yes | Yes | No |
| **Local Models** | Possible | Yes | Yes | No |
| **Visualization** | Basic | Good | Basic | None |
| **Maturity** | High | High | Medium | Beta |

Two version-reality notes the matrix cannot show:

- **Swarm is archived.** OpenAI's 2024 experimental teaching framework was superseded by the OpenAI Agents SDK (handoffs + guardrails, GA); treat Swarm columns as historical.
- **"AutoGen" names two things.** The community continuation of the 0.2-style API ships as **AG2** (`uv pip install pyautogen`); Microsoft's rewrite ships as **autogen-agentchat 0.4+** (`uv pip install autogen-agentchat autogen-core`) with a fundamentally different event-driven runtime. Code below is 0.2-style and labeled as such.

---

## AutoGen (Microsoft)

### Architecture
```text
┌─────────────────────────────────────────────────────────────┐
│                    AutoAgent (User Proxy)                    │
│                                                              │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐        │
│  │  Agent A   │◄──►│  Agent B   │◄──►│  Agent C   │        │
│  │  (Coder)   │    │ (Reviewer)│    │  (Tester)  │        │
│  └────────────┘    └────────────┘    └────────────┘        │
│         ▲                  ▲                  ▲             │
│         └──────────────────┴──────────────────┘             │
│                      Conversation Flow                        │
└─────────────────────────────────────────────────────────────┘
```

### Strengths
- Natural conversation-based coordination
- Built-in code execution (with safety)
- Strong multi-agent orchestration
- Good for coding tasks
- Human-in-the-loop support

### Weaknesses
- Can be verbose
- Less control over execution flow
- State management can be complex

### Example Code
```python
# autogen_example.py -- 0.2-style API (pyautogen / AG2)
# Not executed in this repo: requires the autogen package and an
# OAI_CONFIG_LIST with live API keys. Compile-checked only.
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json

# Load config
config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

# Create agents
assistant = AssistantAgent(
    name="assistant",
    llm_config={
        "config_list": config_list,
        "temperature": 0.7,
    }
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
    },
)

# Create additional agents
coder = AssistantAgent(
    name="coder",
    system_message="You are a programmer. Write clean Python code.",
    llm_config={"config_list": config_list},
)

reviewer = AssistantAgent(
    name="reviewer",
    system_message="You are a code reviewer. Check for bugs and improvements.",
    llm_config={"config_list": config_list},
)

# Start conversation
user_proxy.initiate_chat(
    assistant,
    message="Write a function to calculate fibonacci numbers."
)
```

The `config_list_from_json` + `llm_config` pattern is 0.2-style. The 0.4+ `autogen_agentchat` rewrite replaces it with declarative components and an event-driven `SingleThreadedAgentRuntime` — same roles, different skeleton; port only after the conversation logic is stable.

### Use Cases
- Code generation and review pipeline
- Multi-step problem solving
- Research assistant with different expert agents
- Automated testing workflow

---

## LangGraph (LangChain)

### Architecture
```text
┌─────────────────────────────────────────────────────────────┐
│                      Workflow Graph                          │
│                                                              │
│  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐      │
│  │  Node  │───►│  Node  │───►│  Node  │───►│  Node  │      │
│  │ (Start)│    │(Agent) │    │(Tool)  │    │ (End)  │      │
│  └────────┘    └────────┘    └────────┘    └────────┘      │
│       │             │             │             │           │
│       └─────────────┴─────────────┴─────────────┘           │
│                      State Machine                          │
│                                                              │
│  Checkpoints: ─────► │ │ │ │ │ ◄──────────┘               │
│                    (State Persistence)                       │
└─────────────────────────────────────────────────────────────┘
```

### Strengths
- Explicit state management
- Visual workflow debugging
- Checkpoint/resume capability
- Deterministic execution
- Good integration with LangChain ecosystem

### Weaknesses
- More boilerplate code
- Steeper learning curve
- Graph design can be complex

### Example Code
```python
# langgraph_example.py
# Not executed in this repo: requires langgraph + langchain_openai and
# an API key. Compile-checked only.
import operator
from typing import Annotated, Sequence, TypedDict

from langgraph.graph import END, START, StateGraph
from langchain_openai import ChatOpenAI

# Define state
class AgentState(TypedDict):
    messages: Annotated[Sequence[str], operator.add]
    current_step: str
    agent_outputs: dict

# Define nodes
def research_agent(state: AgentState):
    """Research agent node"""
    llm = ChatOpenAI(model="gpt-5")
    response = llm.invoke(state["messages"])
    return {"agent_outputs": {"research": response.content}}

def writing_agent(state: AgentState):
    """Writing agent node"""
    llm = ChatOpenAI(model="gpt-5")
    context = state.get("agent_outputs", {}).get("research", "")
    response = llm.invoke(f"Write based on: {context}")
    return {"agent_outputs": {"writing": response.content}}

def review_agent(state: AgentState):
    """Review agent node"""
    llm = ChatOpenAI(model="gpt-5")
    content = state.get("agent_outputs", {}).get("writing", "")
    response = llm.invoke(f"Review this: {content}")
    return {"messages": [response.content]}

# Define routing
def should_continue(state: AgentState):
    """Decide whether to continue"""
    if "approved" in str(state["messages"][-1]):
        return END
    return "writing"

# Build graph
workflow = StateGraph(AgentState)

workflow.add_node("research", research_agent)
workflow.add_node("writing", writing_agent)
workflow.add_node("review", review_agent)

workflow.add_edge(START, "research")
workflow.add_edge("research", "writing")
workflow.add_edge("writing", "review")
workflow.add_conditional_edges("review", should_continue)

# Compile with memory
app = workflow.compile()

# Run
result = app.invoke({
    "messages": ["Write an article about quantum computing"],
    "current_step": "start",
    "agent_outputs": {},
})
```

Entry is the `START` pseudo-node (`add_edge(START, "research")`) — `set_entry_point` still works but is the legacy spelling. The `Annotated[..., operator.add]` reducer is what makes fan-in nodes merge lists instead of overwriting them.

### Use Cases
- Complex multi-step workflows
- Stateful agent interactions
- Long-running processes with checkpoints
- Debugging complex agent behaviors

---

## CrewAI

### Architecture
```text
┌─────────────────────────────────────────────────────────────┐
│                        Crew                                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Agent    │  │    Agent    │  │    Agent    │      │
│  │  (Research) │  │   (Writer)  │  │  (Editor)   │      │
│  │              │  │              │  │              │      │
│  │  Role:       │  │  Role:       │  │  Goal:       │      │
│  │  Goal:       │  │  Backstory:  │  │  Backstory:  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                      Task Manager                             │
│                                                              │
│  Tasks:                                                      │
│    1. Research topic ─────► Agent 1                          │
│    2. Write article ───────► Agent 2                          │
│    3. Edit content ────────► Agent 3                          │
└─────────────────────────────────────────────────────────────┘
```

### Strengths
- Role-based agent design
- Clear task delegation
- Process templates
- Crew orchestration

### Weaknesses
- Less flexible than others
- Smaller community
- Fewer integrations

### Example Code
```python
# crewai_example.py
# Not executed in this repo: requires the crewai package and an API key.
# Compile-checked only.
from crewai import Agent, Task, Crew, Process

# Create agents
researcher = Agent(
    role="Researcher",
    goal="Find accurate information on topics",
    backstory="You are an experienced researcher with a keen eye for detail.",
    verbose=True,
)

writer = Agent(
    role="Writer",
    goal="Write engaging content",
    backstory="You are a skilled writer who can make complex topics accessible.",
    verbose=True,
)

editor = Agent(
    role="Editor",
    goal="Ensure content quality and accuracy",
    backstory="You are a meticulous editor with years of experience.",
    verbose=True,
)

# Create tasks
research_task = Task(
    description="Research quantum computing fundamentals",
    expected_output="A detailed summary of quantum computing concepts",
    agent=researcher,
)

write_task = Task(
    description="Write an article about quantum computing",
    expected_output="A 1000-word article on quantum computing",
    agent=writer,
)

edit_task = Task(
    description="Edit the quantum computing article",
    expected_output="A polished, error-free article",
    agent=editor,
)

# Create crew
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, write_task, edit_task],
    process=Process.sequential,
    verbose=True,
)

# Run
result = crew.kickoff()
print(result)
```

### Use Cases
- Content creation pipeline
- Research and writing workflows
- Quality assurance processes
- Role-based automation

---

## Recommendation

### Primary Framework: LangGraph

**Reasons:**
1. State machine model is more predictable
2. Checkpoint/resume for long tasks
3. Better visualization and debugging
4. Integration with local models
5. Deterministic execution

### Secondary Framework: AutoGen

**Use for:**
1. Quick prototyping
2. Conversation-heavy tasks
3. Code generation workflows
4. Human-in-the-loop scenarios

---

## Hybrid Approach

```python
# hybrid_framework.py
"""
Hybrid approach: LangGraph owns the orchestration graph; an AutoGen
(0.2-style / AG2) agent does the talking inside each node.
"""
# Not executed in this repo: requires both frameworks plus API keys.
# Compile-checked only.
import operator
from typing import Annotated, Sequence, TypedDict

from autogen import AssistantAgent
from langgraph.graph import END, START, StateGraph


class AgentState(TypedDict):
    messages: Annotated[Sequence[str], operator.add]
    agent_outputs: dict


class HybridMultiAgentSystem:
    """LangGraph state machine with AutoGen agents as node executors."""

    def __init__(self, config_list):
        # LangGraph for orchestration
        self.workflow = StateGraph(AgentState)

        # AutoGen agents for execution
        self.agents = {
            "coder": AssistantAgent(
                name="coder",
                llm_config={"config_list": config_list},
            ),
            "reviewer": AssistantAgent(
                name="reviewer",
                llm_config={"config_list": config_list},
            ),
        }

    def build_workflow(self):
        """Build LangGraph workflow with AutoGen agents"""

        def coding_step(state: AgentState) -> dict:
            """Use AutoGen agent in LangGraph node"""
            reply = self.agents["coder"].generate_reply(list(state["messages"]))
            return {"agent_outputs": {"code": reply}}

        def review_step(state: AgentState) -> dict:
            """Review step"""
            code = state["agent_outputs"]["code"]
            reply = self.agents["reviewer"].generate_reply([f"Review: {code}"])
            return {"agent_outputs": {"review": reply}}

        # Build graph
        self.workflow.add_node("code", coding_step)
        self.workflow.add_node("review", review_step)
        self.workflow.add_edge(START, "code")
        self.workflow.add_edge("code", "review")
        self.workflow.add_edge("review", END)

        return self.workflow.compile()
```

The division of labor is the point: the graph owns *what happens next* (edges, conditions, checkpoints); the agent owns *what gets said* (prompts, tools, retries). Both frameworks must be pinned in `pyproject.toml` before this shape ships — their release cadences are independent.

---

## Performance Comparison

### Resource Usage (11GB-class GPU)

| Framework | Memory | Tokens/Call | Overhead |
|-----------|--------|-------------|----------|
| AutoGen | ~2GB | ~2000 | Medium |
| LangGraph | ~1.5GB | ~1500 | Low |
| CrewAI | ~2GB | ~1800 | Medium |

These are order-of-magnitude estimates for a typical two-agent conversation, not benchmarks — conversation length and tool calls dominate both numbers. Measure your own workload before provisioning; the ranking is more stable than the values.

### Task Complexity Suitability

| Task Complexity | Recommended | Reason |
|-----------------|--------------|--------|
| Simple (1-2 steps) | AutoGen | Easiest to set up |
| Medium (3-5 steps) | LangGraph | Better control |
| Complex (5+ steps) | LangGraph | State management |
| Conversational | AutoGen | Natural fit |
| Stateful | LangGraph | Checkpoints |
| Parallel | LangGraph | Concurrent nodes |

The suitability table, as executable rules:

```python
def recommend_framework(steps: int, conversational: bool,
                        stateful: bool, parallel: bool) -> str:
    """Decision table as code: conversational work goes to AutoGen,
    anything stateful/parallel/long goes to LangGraph."""
    if conversational:
        return "AutoGen"
    if stateful or parallel or steps > 2:
        return "LangGraph"
    return "AutoGen"


for label, kwargs in [
    ("quick 2-step script", dict(steps=2, conversational=False,
                                 stateful=False, parallel=False)),
    ("support chatbot", dict(steps=4, conversational=True,
                             stateful=False, parallel=False)),
    ("pipeline with resume", dict(steps=6, conversational=False,
                                  stateful=True, parallel=False)),
    ("fan-out analysis", dict(steps=3, conversational=False,
                              stateful=False, parallel=True)),
]:
    print(f"{label}: {recommend_framework(**kwargs)}")
# Output: quick 2-step script: AutoGen
# Output: support chatbot: AutoGen
# Output: pipeline with resume: LangGraph
# Output: fan-out analysis: LangGraph
```

CrewAI appears in neither recommendation because its role-based pipeline is an orthogonal choice: pick it when the *team metaphor* fits your domain, not when a task-shape rule fires.

---

## Summary

This guide compares the multi-agent frameworks on real terms: AutoGen, LangGraph, CrewAI, and OpenAI's agent stack across architecture, model support, state management, and operational maturity - with version-pinned code so every example compiles against the documented release. The rule it leaves: choose by state model and operational fit, not feature lists - the framework you can debug in production beats the one that demos best.

## References

### Related Documents

- [7301: Collaborative Tasking - Multi-Agent Synergy](../7301-Orchestration.md)
- [7302: Multi-Agent Communication Protocols](../7302-Communication-Protocols.md)
- [7102: Planning and Task Decomposition](../../7100-architecture/7102-Planning-Decomposition.md)
- [7103: ReAct Agent Implementation Guide](../../7100-architecture/guides/7103-ReAct-Implementation-Guide.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**
