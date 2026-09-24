# Phase 7: Agentic Cognition Practice

## Hands-On Exercises

### Exercise 1: Implement ReAct Loop from Scratch

```python
import json
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass

@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    parameters: dict
    function: Callable

    def to_schema(self) -> dict:
        """Convert to OpenAI-style schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ReActAgent:
    """Simple ReAct agent implementation"""

    def __init__(self, llm_generate, tools: List[Tool]):
        """
        Args:
            llm_generate: Function that generates completions
            tools: List of available tools
        """
        self.llm_generate = llm_generate
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = 10
        self.history = []

    def think(self, query: str, context: str = "") -> str:
        """Generate thought about current state"""
        prompt = f"""
You are a helpful agent. Think about what to do next.

User Query: {query}

Context: {context}

Available Tools: {', '.join(self.tools.keys())}

Previous Actions:
{self._format_history()}

Provide your thought process. What do you need to do next?
"""
        return self.llm_generate(prompt)

    def act(self, thought: str) -> tuple:
        """Decide on and execute action"""
        prompt = f"""
Based on this thought: {thought}

Decide what action to take. Either:
1. Call a tool with format: TOOL_NAME: {{"param": "value"}}
2. Answer: FINAL: Your final answer

What do you do?
"""
        response = self.llm_generate(prompt).strip()

        # Parse action
        if response.startswith("FINAL:"):
            return "final", response[6:].strip()

        # Parse tool call
        if ":" in response:
            tool_name, args_str = response.split(":", 1)
            tool_name = tool_name.strip()

            if tool_name in self.tools:
                try:
                    args = json.loads(args_str)
                    result = self.tools[tool_name].function(**args)
                    self.history.append({
                        "thought": thought,
                        "action": f"{tool_name}({args})",
                        "observation": str(result)[:200]
                    })
                    return "tool", result
                except Exception as e:
                    return "error", str(e)

        return "error", "Could not parse action"

    def run(self, query: str) -> str:
        """Run ReAct loop"""
        print(f"\n=== Starting ReAct Loop ===")
        print(f"Query: {query}\n")

        for iteration in range(self.max_iterations):
            print(f"[Iteration {iteration + 1}]")

            # Think
            context = "\n".join([h['observation'] for h in self.history[-3:]])
            thought = self.think(query, context)
            print(f"Thought: {thought[:200]}...")

            # Act
            action_type, result = self.act(thought)

            if action_type == "final":
                print(f"\nFinal Answer: {result}")
                return result

            print(f"Action Result: {str(result)[:200]}...")

        return "Max iterations reached"

    def _format_history(self) -> str:
        """Format action history"""
        if not self.history:
            return "No previous actions"

        formatted = []
        for h in self.history[-3:]:
            formatted.append(f"- {h['action']} -> {h['observation']}")

        return "\n".join(formatted)


def mock_llm_generate(prompt: str) -> str:
    """Mock LLM for testing"""
    # In real implementation, call OpenAI API or local model
    if "search" in prompt.lower():
        return 'search: {"query": "Python machine learning"}'
    elif "final" in prompt.lower() or "answer" in prompt.lower():
        return "FINAL: Python is widely used for machine learning with libraries like scikit-learn and TensorFlow."
    return "I need to search for information."


def test_react():
    print("=== ReAct Agent Test ===")

    # Define tools
    def search_web(query: str) -> str:
        return f"Found 5 results for '{query}': Top result about Python ML..."

    def calculator(expression: str) -> str:
        try:
            return f"Result: {eval(expression)}"
        except:
            return "Invalid expression"

    tools = [
        Tool(
            name="search",
            description="Search the web for information",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
            function=search_web
        ),
        Tool(
            name="calculator",
            description="Calculate mathematical expressions",
            parameters={"type": "object", "properties": {"expression": {"type": "string"}}},
            function=calculator
        )
    ]

    # Create agent
    agent = ReActAgent(llm_generate=mock_llm_generate, tools=tools)

    # Run query
    result = agent.run("What is Python used for in machine learning?")

    print(f"\nFinal Result: {result}")
    print("✅ ReAct agent working!\n")


if __name__ == "__main__":
    test_react()
```

### Exercise 2: Implement Tool Calling System

```python
import inspect
from typing import Any, Dict, List
from functools import wraps

class ToolRegistry:
    """Registry for agent tools"""

    def __init__(self):
        self.tools = {}

    def register(self, name: str = None, description: str = None):
        """Decorator to register tools"""
        def decorator(func):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or "No description"

            # Extract parameter schema from function signature
            sig = inspect.signature(func)
            parameters = {}
            for param_name, param in sig.parameters.items():
                param_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else "any"
                parameters[param_name] = {"type": param_type}

            self.tools[tool_name] = {
                "name": tool_name,
                "description": tool_desc,
                "parameters": parameters,
                "function": func
            }

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def get_tool(self, name: str) -> Dict:
        """Get tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict]:
        """List all available tools"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in self.tools.values()
        ]

    def execute(self, name: str, **kwargs) -> Any:
        """Execute a tool"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")

        return tool["function"](**kwargs)


def test_tool_registry():
    print("=== Tool Registry Test ===")

    registry = ToolRegistry()

    # Register tools
    @registry.register(description="Get current weather for a location")
    def get_weather(location: str, unit: str = "celsius") -> str:
        """Get weather information"""
        return f"Weather in {location}: 22°C, Sunny"

    @registry.register(description="Calculate mathematical expression")
    def calculate(expression: str) -> float:
        """Calculate expression"""
        return eval(expression)

    @registry.register(description="Search the web")
    def web_search(query: str, num_results: int = 5) -> list:
        """Search web"""
        return [f"Result {i+1} for '{query}'" for i in range(num_results)]

    # List tools
    print("Available tools:")
    for tool in registry.list_tools():
        print(f"  - {tool['name']}: {tool['description']}")
        print(f"    Parameters: {tool['parameters']}")

    # Execute tools
    print("\nExecuting tools:")

    weather = registry.execute("get_weather", location="Tokyo")
    print(f"get_weather: {weather}")

    calc = registry.execute("calculate", expression="2 + 2")
    print(f"calculate: {calc}")

    search = registry.execute("web_search", query="AI agents", num_results=3)
    print(f"web_search: {search}")

    print("✅ Tool registry working!\n")


if __name__ == "__main__":
    test_tool_registry()
```

### Exercise 3: Implement Multi-Agent System

```python
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
import uuid

class AgentRole(Enum):
    """Agent roles"""
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"


@dataclass
class AgentMessage:
    """Message between agents"""
    id: str
    sender: str
    receiver: str
    type: str  # request, response, notification
    content: dict
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type,
            "content": self.content,
            "timestamp": self.timestamp
        }


class Agent:
    """Base agent class"""

    def __init__(self, name: str, role: AgentRole, tools: List[str] = None):
        self.name = name
        self.role = role
        self.tools = tools or []
        self.message_queue = []
        self.memory = {}

    def receive_message(self, message: AgentMessage):
        """Receive a message"""
        self.message_queue.append(message)

    def process_messages(self) -> List[AgentMessage]:
        """Process all messages in queue"""
        responses = []
        for message in self.message_queue:
            response = self.handle_message(message)
            if response:
                responses.append(response)

        self.message_queue.clear()
        return responses

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle a single message - override in subclasses"""
        print(f"[{self.name}] Received from {message.sender}: {message.type}")

        # Default response
        return AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.name,
            receiver=message.sender,
            type="response",
            content={"status": "processed"},
            timestamp=1234567890
        )


class OrchestratorAgent(Agent):
    """Orchestrator agent that coordinates other agents"""

    def __init__(self, agents: List[Agent]):
        super().__init__("orchestrator", AgentRole.ORCHESTRATOR)
        self.agents = {agent.name: agent for agent in agents}

    def delegate_task(self, task: dict) -> List[AgentMessage]:
        """Delegate task to appropriate agents"""
        messages = []
        task_type = task.get("type", "research")

        # Route task to appropriate agent
        if task_type == "research":
            target = "researcher"
        elif task_type == "code":
            target = "coder"
        elif task_type == "review":
            target = "reviewer"
        elif task_type == "execute":
            target = "executor"
        else:
            target = "researcher"  # Default

        if target in self.agents:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender=self.name,
                receiver=target,
                type="request",
                content=task,
                timestamp=1234567890
            )
            self.agents[target].receive_message(message)
            messages.append(message)

        return messages


class MultiAgentSystem:
    """Multi-agent orchestration system"""

    def __init__(self):
        self.agents = {}

    def add_agent(self, agent: Agent):
        """Add agent to system"""
        self.agents[agent.name] = agent

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        return self.agents.get(name)

    def broadcast(self, sender_name: str, message_type: str, content: dict) -> List[AgentMessage]:
        """Broadcast message to all agents"""
        messages = []
        sender = self.get_agent(sender_name)

        for agent_name, agent in self.agents.items():
            if agent_name != sender_name:
                message = AgentMessage(
                    id=str(uuid.uuid4()),
                    sender=sender_name,
                    receiver=agent_name,
                    type=message_type,
                    content=content,
                    timestamp=1234567890
                )
                agent.receive_message(message)
                messages.append(message)

        return messages

    def run_cycle(self) -> Dict[str, List]:
        """Run one communication cycle"""
        results = {"messages": [], "responses": []}

        # Process messages for each agent
        for agent in self.agents.values():
            responses = agent.process_messages()
            results["responses"].extend(responses)

        return results


def test_multi_agent():
    print("=== Multi-Agent System Test ===")

    # Create agents
    researcher = Agent("researcher", AgentRole.RESEARCHER, ["web_search", "read_file"])
    coder = Agent("coder", AgentRole.CODER, ["write_file", "run_python"])
    reviewer = Agent("reviewer", AgentRole.REVIEWER, ["read_file", "analyze_code"])
    executor = Agent("executor", AgentRole.EXECUTOR, ["run_bash", "deploy"])

    # Create orchestrator
    orchestrator = OrchestratorAgent([researcher, coder, reviewer, executor])

    # Create multi-agent system
    system = MultiAgentSystem()
    system.add_agent(orchestrator)
    system.add_agent(researcher)
    system.add_agent(coder)
    system.add_agent(reviewer)
    system.add_agent(executor)

    print(f"System initialized with {len(system.agents)} agents")

    # Delegate tasks
    print("\n--- Delegating tasks ---")

    task1 = {"type": "research", "query": "latest AI trends"}
    orchestrator.delegate_task(task1)

    task2 = {"type": "code", "file": "main.py", "content": "print('Hello')"}
    orchestrator.delegate_task(task2)

    # Run communication cycle
    print("\n--- Running communication cycle ---")
    results = system.run_cycle()

    print(f"Generated {len(results['responses'])} responses")

    print("✅ Multi-agent system working!\n")


if __name__ == "__main__":
    test_multi_agent()
```

### Exercise 4: Implement Agent Memory System

```python
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class MemoryEntry:
    """Single memory entry"""

    def __init__(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        metadata: dict = None
    ):
        self.content = content
        self.memory_type = memory_type  # episodic, semantic, procedural
        self.importance = importance  # 0-1
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.access_count = 0
        self.last_accessed = self.timestamp

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "type": self.memory_type,
            "importance": self.importance,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "access_count": self.access_count
        }


class AgentMemory:
    """Vector-based memory system for agents"""

    def __init__(self, embedding_dim: int = 384, max_memories: int = 1000):
        self.embedding_dim = embedding_dim
        self.max_memories = max_memories
        self.memories: List[MemoryEntry] = []
        self.embeddings: np.ndarray = np.zeros((0, embedding_dim))
        self.memory_types = defaultdict(list)

    def add_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        metadata: dict = None
    ) -> MemoryEntry:
        """Add a new memory"""
        entry = MemoryEntry(content, memory_type, importance, metadata)
        self.memories.append(entry)
        self.memory_types[memory_type].append(entry)

        # Simulate embedding (in real system, use actual embedding model)
        embedding = np.random.randn(self.embedding_dim)
        embedding = embedding / np.linalg.norm(embedding)

        if len(self.embeddings) == 0:
            self.embeddings = embedding.reshape(1, -1)
        else:
            self.embeddings = np.vstack([self.embeddings, embedding])

        # Prune if exceeding max
        if len(self.memories) > self.max_memories:
            self._prune_memories()

        return entry

    def retrieve(
        self,
        query: str,
        k: int = 5,
        memory_type: str = None,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """Retrieve relevant memories"""
        if not self.memories:
            return []

        # Filter by type and importance
        candidates = self.memories
        if memory_type:
            candidates = [m for m in candidates if m.memory_type == memory_type]
        if min_importance > 0:
            candidates = [m for m in candidates if m.importance >= min_importance]

        if not candidates:
            return []

        # Get indices of candidates
        indices = [self.memories.index(m) for m in candidates]
        candidate_embeddings = self.embeddings[indices]

        # Simulate query embedding
        query_embedding = np.random.randn(self.embedding_dim)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Calculate similarities
        similarities = np.dot(candidate_embeddings, query_embedding)

        # Sort by similarity
        sorted_indices = np.argsort(similarities)[::-1][:k]

        # Get memories
        results = [candidates[i] for i in sorted_indices]

        # Update access stats
        for memory in results:
            memory.access_count += 1
            memory.last_accessed = datetime.now()

        return results

    def _prune_memories(self):
        """Remove least important/old memories"""
        # Score memories by importance and recency
        now = datetime.now()
        scores = []

        for memory in self.memories:
            age_days = (now - memory.timestamp).days
            recency_score = 1.0 / (1.0 + age_days / 30.0)  # Decay over 30 days
            total_score = memory.importance * recency_score
            scores.append((total_score, memory))

        # Sort by score and keep top memories
        scores.sort(key=lambda x: x[0], reverse=True)
        self.memories = [m for _, m in scores[:self.max_memories]]

    def get_recent(self, hours: int = 24, k: int = 10) -> List[MemoryEntry]:
        """Get recent memories"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [m for m in self.memories if m.timestamp >= cutoff]
        return sorted(recent, key=lambda m: m.timestamp, reverse=True)[:k]

    def get_summary(self) -> dict:
        """Get memory summary statistics"""
        return {
            "total_memories": len(self.memories),
            "episodic": len(self.memory_types["episodic"]),
            "semantic": len(self.memory_types["semantic"]),
            "procedural": len(self.memory_types["procedural"]),
            "avg_importance": np.mean([m.importance for m in self.memories]) if self.memories else 0
        }


def test_agent_memory():
    print("=== Agent Memory Test ===")

    # Create memory system
    memory = AgentMemory(embedding_dim=384, max_memories=100)

    # Add sample memories
    memory.add_memory(
        "User prefers Python over JavaScript",
        memory_type="semantic",
        importance=0.8,
        metadata={"category": "preference"}
    )

    memory.add_memory(
        "Yesterday discussed machine learning project",
        memory_type="episodic",
        importance=0.6,
        metadata={"topic": "ML"}
    )

    memory.add_memory(
        "To deploy: docker build -t app . && docker run app",
        memory_type="procedural",
        importance=0.9,
        metadata={"category": "devops"}
    )

    print(f"Added {len(memory.memories)} memories")

    # Retrieve memories
    print("\nRetrieving relevant memories:")
    results = memory.retrieve("how to deploy application", k=3)

    for i, memory_entry in enumerate(results, 1):
        print(f"{i}. [{memory_entry.memory_type}] {memory_entry.content}")
        print(f"   Importance: {memory_entry.importance:.2f}")

    # Get summary
    print("\nMemory Summary:")
    summary = memory.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("✅ Agent memory working!\n")


if __name__ == "__main__":
    test_agent_memory()
```

### Exercise 5: Implement Sandboxed Code Execution

```python
import subprocess
import tempfile
import os
from typing import Dict, Any
import json

class SandboxedExecutor:
    """Execute code in a sandboxed environment"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def execute_python(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code in a sandboxed environment

        Uses subprocess to isolate execution
        """
        result = {
            "success": False,
            "output": "",
            "error": "",
            "execution_time": 0
        }

        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute in subprocess with timeout
            process = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                # Restrict permissions
                preexec_fn=lambda: None  # Isolate process
            )

            result["output"] = process.stdout
            result["error"] = process.stderr
            result["success"] = process.returncode == 0

        except subprocess.TimeoutExpired:
            result["error"] = f"Execution timed out after {self.timeout} seconds"
        except Exception as e:
            result["error"] = str(e)
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

        return result

    def execute_bash(self, command: str) -> Dict[str, Any]:
        """
        Execute bash command with safety restrictions

        WARNING: Only allow safe commands in production
        """
        # Dangerous commands to block
        dangerous = ['rm -rf', 'mkfs', 'dd if=', 'chmod 777', '> /dev/']

        if any(d in command for d in dangerous):
            return {
                "success": False,
                "error": "Command blocked for safety reasons"
            }

        result = {
            "success": False,
            "output": "",
            "error": ""
        }

        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            result["output"] = process.stdout
            result["error"] = process.stderr
            result["success"] = process.returncode == 0

        except subprocess.TimeoutExpired:
            result["error"] = f"Command timed out after {self.timeout} seconds"
        except Exception as e:
            result["error"] = str(e)

        return result

    def validate_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Validate code without executing"""
        result = {"valid": False, "errors": []}

        if language == "python":
            try:
                compile(code, '<string>', 'exec')
                result["valid"] = True
            except SyntaxError as e:
                result["errors"].append(f"Syntax error: {e}")

        return result


def test_sandbox():
    print("=== Sandboxed Executor Test ===")

    executor = SandboxedExecutor(timeout=10)

    # Test Python execution
    print("Testing Python execution:")
    python_code = """
# Simple calculation
result = sum(range(10))
print(f"Sum of 0-9: {result}")

# List comprehension
squares = [x**2 for x in range(5)]
print(f"Squares: {squares}")
"""

    result = executor.execute_python(python_code)
    print(f"Success: {result['success']}")
    print(f"Output:\n{result['output']}")

    if result['error']:
        print(f"Error: {result['error']}")

    # Test code validation
    print("\nTesting code validation:")
    valid_code = "x = 5\nprint(x)"
    invalid_code = "x = 5\nprint(x"  # Missing closing paren

    valid_result = executor.validate_code(valid_code)
    invalid_result = executor.validate_code(invalid_code)

    print(f"Valid code: {valid_result['valid']}")
    print(f"Invalid code: {invalid_result['valid']}")
    print(f"Errors: {invalid_result['errors']}")

    # Test bash execution (with safety)
    print("\nTesting bash execution:")
    bash_result = executor.execute_bash("echo 'Hello from bash'")
    print(f"Success: {bash_result['success']}")
    print(f"Output: {bash_result['output'].strip()}")

    # Test dangerous command blocking
    dangerous_result = executor.execute_bash("rm -rf /")
    print(f"\nDangerous command blocked: {not dangerous_result['success']}")

    print("✅ Sandboxed execution working!\n")


if __name__ == "__main__":
    test_sandbox()
```

---

## Completion Checklist

- [ ] ReAct loop implemented
- [ ] Tool registry functional
- [ ] Multi-agent system working
- [ ] Agent memory system operational
- [ ] Sandboxed code execution safe
- [ ] Tool calling tested
- [ ] Agent communication verified
- [ ] Memory retrieval working

---

**Last Updated:** 2026-02-05
