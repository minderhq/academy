# 7303: Multi-Agent Framework Comparison

## Abstract
Comprehensive comparison of multi-agent frameworks for building autonomous AI systems on AI Engineering Curriculum.

## Framework Comparison Matrix

| Feature | AutoGen | LangGraph | CrewAI | Swarm (OpenAI) |
|---------|---------|-----------|--------|----------------|
| **Architecture** | Conversational | State Machine | Role-based | Orchestrated |
| **LLM Support** | OpenAI, Azure, HuggingFace | Any (via LangChain) | OpenAI, Claude, Local | OpenAI only |
| **Memory** | Built-in | Via checkpoint | Built-in | Via context |
| **Tool Calling** | Yes | Yes | Yes | Yes |
| **Human-in-Loop** | Yes | Yes | Yes | No |
| **Local Models** | Possible | Yes | Yes | No |
| **Visualization** | Basic | Good | Basic | None |
| **Maturity** | High | High | Medium | Beta |

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
# autogen_example.py
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

### Use Cases for AI Engineering Curriculum
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
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, Sequence
import operator

# Define state
class AgentState(TypedDict):
    messages: Annotated[Sequence[str], operator.add]
    current_step: str
    agent_outputs: dict

# Define nodes
def research_agent(state: AgentState):
    """Research agent node"""
    llm = ChatOpenAI(model="gpt-4")
    response = llm.invoke(state["messages"])
    return {"agent_outputs": {"research": response.content}}

def writing_agent(state: AgentState):
    """Writing agent node"""
    llm = ChatOpenAI(model="gpt-4")
    context = state.get("agent_outputs", {}).get("research", "")
    response = llm.invoke(f"Write based on: {context}")
    return {"agent_outputs": {"writing": response.content}}

def review_agent(state: AgentState):
    """Review agent node"""
    llm = ChatOpenAI(model="gpt-4")
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

workflow.set_entry_point("research")
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

### Use Cases for AI Engineering Curriculum
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
│  │  Role:       │  │  Role:       │  │  Role:       │      │
│  │  Goal:       │  │  Goal:       │  │  Goal:       │      │
│  │  Backstory:  │  │  Backstory:  │  │  Backstory:  │      │
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

### Use Cases for AI Engineering Curriculum
- Content creation pipeline
- Research and writing workflows
- Quality assurance processes
- Role-based automation

---

## Recommendation for AI Engineering Curriculum

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
Hybrid approach combining LangGraph's state machine
with AutoGen's conversation model
"""

from langgraph.graph import StateGraph
from autogen import AssistantAgent

class HybridMultiAgentSystem:
    """Combine best of both frameworks"""

    def __init__(self):
        # LangGraph for orchestration
        self.workflow = StateGraph(AgentState)

        # AutoGen agents for execution
        self.agents = {
            "coder": AssistantAgent(name="coder", ...),
            "reviewer": AssistantAgent(name="reviewer", ...),
            "tester": AssistantAgent(name="tester", ...),
        }

    def build_workflow(self):
        """Build LangGraph workflow with AutoGen agents"""

        def coding_step(state):
            """Use AutoGen agent in LangGraph node"""
            agent = self.agents["coder"]
            response = agent.generate_reply(state["messages"])
            return {"agent_outputs": {"code": response}}

        def review_step(state):
            """Review step"""
            agent = self.agents["reviewer"]
            code = state["agent_outputs"]["code"]
            response = agent.generate_reply([f"Review: {code}"])
            return {"agent_outputs": {"review": response}}

        # Build graph
        self.workflow.add_node("code", coding_step)
        self.workflow.add_node("review", review_step)
        self.workflow.add_edge("code", "review")

        return self.workflow.compile()
```

---

## Performance Comparison

### Resource Usage (11GB-class GPU)

| Framework | Memory | Tokens/Call | Overhead |
|-----------|--------|-------------|----------|
| AutoGen | ~2GB | ~2000 | Medium |
| LangGraph | ~1.5GB | ~1500 | Low |
| CrewAI | ~2GB | ~1800 | Medium |

### Task Complexity Suitability

| Task Complexity | Recommended | Reason |
|-----------------|--------------|--------|
| Simple (1-2 steps) | AutoGen | Easiest to set up |
| Medium (3-5 steps) | LangGraph | Better control |
| Complex (5+ steps) | LangGraph | State management |
| Conversational | AutoGen | Natural fit |
| Stateful | LangGraph | Checkpoints |
| Parallel | LangGraph | Concurrent nodes |


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [Related Guides](7303-Framework-Comparison.md)
- [7202: Collaborative Tasking](../7301-Orchestration.md)
- [7102: Planning Decomposition](../../7100-architecture/7102-Planning-Decomposition.md)
- [7103: ReAct Implementation Guide](../../7100-architecture/guides/7103-ReAct-Implementation-Guide.md)
