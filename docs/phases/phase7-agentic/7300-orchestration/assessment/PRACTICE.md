---
Document ID: 7300-PRACTICE
Title: "7300: Agent Orchestration - Practice"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'agents', 'orchestration']
---

# 7300: Agent Orchestration - Practice

## Exercises

### Exercise 1: Single Agent with Memory

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

# LangChain 1.x: memory = a checkpointer. The same thread_id shares
# chat history across invocations (ConversationBufferMemory removed).

# Shared tools - the same @tool definitions as the 7200 Practice
# file, repeated here so this file runs standalone.
@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Simplified - in production, use an actual search API
    return f"Results for: {query}"

@tool
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get current weather for a location."""
    # Simplified - in production, use a weather API
    return f"Weather in {location}: 22°C, Partly cloudy"

# SOLUTION: Create agent with memory for conversation context
llm = ChatOpenAI(model="gpt-4", temperature=0)

agent = create_agent(
    llm,
    [calculator, search_web, get_weather],
    system_prompt="You are a helpful assistant.",
    checkpointer=InMemorySaver(),
)

# SOLUTION: Test conversation with memory - same thread_id, same memory
config = {"configurable": {"thread_id": "alice-1"}}

response1 = agent.invoke(
    {"messages": [{"role": "user", "content": "Hi, my name is Alice"}]},
    config=config,
)
print(response1["messages"][-1].text)

response2 = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    config=config,
)
print(response2["messages"][-1].text)
```

### Exercise 2: Multi-Agent Collaboration

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# Shared tools so this file runs standalone.
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

def build_agent(system_prompt: str, tools):
    """Build a specialized agent with one create_agent call."""
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    return create_agent(llm, tools, system_prompt=system_prompt)

class ResearchAgent:
    def __init__(self, topic):
        self.topic = topic
        self.agent = build_agent(
            f"You research topics thoroughly. Current topic: {topic}",
            [search_web, calculator],
        )

    def research(self, query):
        """Research a specific query."""
        full_query = f"Research this topic about {self.topic}: {query}"
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": full_query}]}
        )
        return result["messages"][-1].text

class WriterAgent:
    def __init__(self):
        self.agent = build_agent(
            "You are a skilled technical writer.",
            [calculator],  # Writing might need some tools
        )

    def write(self, research_findings):
        """Write content based on research."""
        query = f"Write an article based on these findings: {research_findings}"
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": query}]}
        )
        return result["messages"][-1].text

# SOLUTION: Coordinate multiple agents for task completion
def create_article(topic):
    """Coordinate research and writing agents."""

    # SOLUTION: Use research agent to gather data
    research_agent = ResearchAgent(topic)

    research_1 = research_agent.research(f"overview of {topic}")
    research_2 = research_agent.research(f"recent developments in {topic}")
    research_3 = research_agent.research(f"key benefits of {topic}")

    # SOLUTION: Use writer agent to create final output
    writer_agent = WriterAgent()

    article = writer_agent.write(f"""
    Research findings:
    1. {research_1}
    2. {research_2}
    3. {research_3}
    """)

    return article

# SOLUTION: Test multi-agent collaboration
article = create_article("quantum computing")
print(article)
```

### Exercise 3: Sequential Agent Pipeline

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    input: str
    research_output: Annotated[str, "Research findings"]
    analysis_output: Annotated[str, "Analysis of research"]
    final_output: Annotated[str, "Final answer"]

# SOLUTION: Define node for research agent
def research_agent_node(state: AgentState) -> AgentState:
    query = state["input"]

    research_agent = ResearchAgent(query)
    findings = research_agent.research(query)

    state["research_output"] = findings
    return state

# SOLUTION: Define node for analysis agent
def analysis_agent_node(state: AgentState) -> AgentState:
    research = state["research_output"]

    analysis_agent = WriterAgent()
    analysis = analysis_agent.write(f"Analyze this research: {research}")

    state["analysis_output"] = analysis
    return state

# SOLUTION: Define node for synthesis agent
def synthesis_agent_node(state: AgentState) -> AgentState:
    research = state["research_output"]
    analysis = state["analysis_output"]

    llm = ChatOpenAI(model="gpt-4")
    prompt = f"""Synthesize a final answer from:
    Research: {research}
    Analysis: {analysis}

    Final answer:"""

    final = llm.invoke(prompt)

    state["final_output"] = final.content
    return state

# SOLUTION: Build LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("research", research_agent_node)
workflow.add_node("analysis", analysis_agent_node)
workflow.add_node("synthesis", synthesis_agent_node)

workflow.add_edge("research", "analysis")
workflow.add_edge("analysis", "synthesis")
workflow.add_edge("synthesis", END)

workflow.set_entry_point("research")

app = workflow.compile()

# SOLUTION: Execute the sequential pipeline
result = app.invoke({"input": "What are the latest developments in AI?"})
print(result["final_output"])
```

### Exercise 4: Hierarchical Agent System

```python
class SupervisorAgent:
    def __init__(self, workers):
        self.workers = workers
        self.llm = ChatOpenAI(model="gpt-4")

    def delegate(self, task):
        """Decide which worker should handle the task."""

        # SOLUTION: Analyze task to determine best worker
        worker_descriptions = "\n".join([
            f"- {name}: {worker.description}"
            for name, worker in self.workers.items()
        ])

        prompt = f"""Task: {task}

Available workers:
{worker_descriptions}

Which worker should handle this task? Respond with just the worker name."""

        response = self.llm.invoke(prompt)
        worker_name = response.content.strip().lower()

        # SOLUTION: Delegate task to appropriate worker
        if worker_name in self.workers:
            return self.workers[worker_name].execute(task)
        else:
            return f"No worker found for task: {task}"

class WorkerAgent:
    def __init__(self, name, description, tools):
        self.name = name
        self.description = description
        self.tools = tools
        self.llm = ChatOpenAI(model="gpt-4")

        # LangChain 1.x: create_agent replaces create_openai_functions_agent
        # + AgentExecutor - system_prompt takes the place of the hub prompt.
        self.agent = create_agent(self.llm, self.tools)

    def execute(self, task):
        """Execute a task."""
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": task}],
        })
        return f"[{self.name}] {result['messages'][-1].text}"

# SOLUTION: Create supervisor and worker agents
workers = {
    "research": WorkerAgent(
        "research",
        "Handles research and information gathering tasks",
        [search_web, calculator],
    ),
    "writer": WorkerAgent(
        "writer",
        "Handles writing and content creation tasks",
        [calculator],
    ),
    "analyst": WorkerAgent(
        "analyst",
        "Handles analysis and data interpretation tasks",
        [calculator],
    ),
}

supervisor = SupervisorAgent(workers)

# SOLUTION: Test multi-agent collaboration
tasks = [
    "Research recent AI developments",
    "Write a summary of machine learning",
    "Analyze the data from our experiment",
]

for task in tasks:
    result = supervisor.delegate(task)
    print(f"\nTask: {task}\nResult: {result}\n")
```

### Exercise 5: Agent Communication Protocol

```python
import time

class Message:
    def __init__(self, sender, receiver, content, message_type="request"):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.message_type = message_type
        self.timestamp = time.time()

class CommunicatingAgent:
    def __init__(self, name, inbox, tools):
        self.name = name
        self.inbox = inbox
        self.tools = tools
        self.llm = ChatOpenAI(model="gpt-4")

    def send_message(self, receiver, content):
        """Send message to another agent."""
        message = Message(self.name, receiver, content)
        # In practice, this would use a message broker
        return message

    def receive_messages(self):
        """Receive messages from inbox."""
        messages = []
        while not self.inbox.empty():
            messages.append(self.inbox.get())
        return messages

    def process_messages(self, messages):
        """Process incoming messages."""
        responses = []

        for message in messages:
            # SOLUTION: Handle different message types
            if message.message_type == "request":
                response = self.handle_request(message.content)
                responses.append(self.send_message(
                    message.sender,
                    response
                ))

        return responses

    def handle_request(self, content):
        """Handle a request message."""
        agent = create_agent(self.llm, self.tools)

        result = agent.invoke({
            "messages": [{"role": "user", "content": content}],
        })
        return result["messages"][-1].text

# SOLUTION: Initialize agents with communication channels
import queue

inboxes = {
    "research": queue.Queue(),
    "writer": queue.Queue(),
}

agents = {
    "research": CommunicatingAgent("research", inboxes["research"], [search_web]),
    "writer": CommunicatingAgent("writer", inboxes["writer"], [calculator]),
}

# SOLUTION: Test message passing between agents
research_msg = agents["writer"].send_message("research", "Find info about AI")
agents["research"].inbox.put(research_msg)

messages = agents["research"].receive_messages()
responses = agents["research"].process_messages(messages)

print(f"Research response: {responses[0].content}")
```

### Exercise 6: Agent Team with Shared Memory

```python
import threading
import time

class SharedMemory:
    def __init__(self):
        self.memory = {}
        self.lock = threading.Lock()

    def write(self, key, value, agent_id):
        """Write to shared memory."""
        with self.lock:
            if key not in self.memory:
                self.memory[key] = []
            self.memory[key].append({
                "value": value,
                "agent": agent_id,
                "timestamp": time.time(),
            })

    def read(self, key):
        """Read from shared memory."""
        with self.lock:
            return self.memory.get(key, [])

    def get_latest(self, key):
        """Get latest value for a key."""
        values = self.read(key)
        return values[-1] if values else None

class TeamAgent:
    def __init__(self, agent_id, shared_memory, tools):
        self.agent_id = agent_id
        self.shared_memory = shared_memory
        self.tools = tools
        self.llm = ChatOpenAI(model="gpt-4")

    def execute_with_memory(self, task):
        """Execute task using shared memory."""

        # SOLUTION: Retrieve relevant info from shared memory
        relevant_info = self.shared_memory.read(task.lower())

        context = f"Relevant information from team:\n{relevant_info}\n\n" if relevant_info else ""

        # SOLUTION: Execute task with memory context
        agent = create_agent(self.llm, self.tools)

        full_prompt = context + task
        result = agent.invoke({
            "messages": [{"role": "user", "content": full_prompt}],
        })

        # SOLUTION: Store result in shared memory
        self.shared_memory.write(
            task.lower(),
            result["messages"][-1].text,
            self.agent_id,
        )

        return result["messages"][-1].text

# SOLUTION: Initialize team with shared memory
shared_memory = SharedMemory()

team = {
    "researcher": TeamAgent("researcher", shared_memory, [search_web]),
    "analyst": TeamAgent("analyst", shared_memory, [calculator]),
    "writer": TeamAgent("writer", shared_memory, [calculator]),
}

# SOLUTION: Execute coordinated team task
research_result = team["researcher"].execute_with_memory(
    "Research quantum computing applications"
)

analysis_result = team["analyst"].execute_with_memory(
    "Analyze the quantum computing research"
)

final_article = team["writer"].execute_with_memory(
    "Write an article about quantum computing"
)

print(final_article)
```

### Exercise 7: AutoGPT-style Autonomous Agent

```python
import json

class AutonomousAgent:
    def __init__(self, goal, tools):
        self.goal = goal
        self.tools = {tool.name: tool for tool in tools}
        self.llm = ChatOpenAI(model="gpt-4")
        self.history = []
        self.completed_tasks = []

    def think(self):
        """Decide next action."""

        # SOLUTION: Build comprehensive prompt for autonomous reasoning
        prompt = f"""Goal: {self.goal}

Completed tasks: {self.completed_tasks}

Decide the next action to achieve the goal.
Available tools: {list(self.tools.keys())}

Respond in JSON format:
{{
    "thought": "your reasoning",
    "tool": "tool name or 'none'",
    "input": "tool input",
    "completed": "true if goal achieved"
}}"""

        response = self.llm.invoke(prompt)

        # SOLUTION: Parse JSON response with decision
        try:
            decision = json.loads(response.content)
            return decision
        except:
            return {"thought": "Parse error", "tool": "none", "input": "", "completed": False}

    def execute(self, tool_name, tool_input):
        """Execute a tool."""
        if tool_name in self.tools:
            result = self.tools[tool_name].func(**tool_input)
            self.completed_tasks.append(f"{tool_name}: {tool_input}")
            return result
        return "Tool not found"

    def run(self, max_iterations=10):
        """Run autonomous agent loop."""

        for iteration in range(max_iterations):
            # SOLUTION: Generate next thought/action
            decision = self.think()

            print(f"\n[Iteration {iteration+1}]")
            print(f"Thought: {decision['thought']}")

            # SOLUTION: Check if goal is achieved
            if decision.get("completed"):
                print("Goal achieved!")
                break

            # SOLUTION: Execute the decided action. The model may
            # return the input as a JSON object or as a JSON string.
            if decision["tool"] != "none":
                tool_input = decision["input"]
                if isinstance(tool_input, str):
                    tool_input = json.loads(tool_input)
                result = self.execute(decision["tool"], tool_input)
                print(f"Action: {decision['tool']}({decision['input']})")
                print(f"Result: {result}")

        return self.completed_tasks

# SOLUTION: Initialize and run autonomous agent
agent = AutonomousAgent(
    goal="Research and summarize the latest developments in AI",
    tools=[search_web, calculator, get_weather],
)

tasks_completed = agent.run(max_iterations=10)
```
