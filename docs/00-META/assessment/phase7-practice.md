# Phase 7: Agentic Systems - Practice Exercises

## Overview

This document provides hands-on practice exercises for Phase 7: Agentic Systems. These exercises reinforce the concepts learned in modules 7100-7500.

**Prerequisites:**
- Completed Phase 1-6 modules
- Strong Python programming skills
- Understanding of LLM APIs
- Familiarity with ReAct pattern

---

## Exercise 1: ReAct Loop from Scratch

**Difficulty:** Beginner
**Time:** 45 minutes
**Module:** 7100 - Agent Architecture

### Task

Implement a basic ReAct (Reasoning + Acting) loop from scratch.

### Requirements

1. Create a `ReActAgent` class with:
   - `think()`: Generate reasoning thoughts
   - `act()`: Execute actions
   - `observe()`: Process observations
   - `run()`: Main loop controller

2. Support these action types:
   - `SEARCH`: Look up information
   - `CALCULATE`: Perform calculations
   - `FINISH`: Return final answer

3. Use an LLM for thought generation

### Solution Template

```python
from typing import List, Dict, Optional, Callable
import re
import json

class ReActAgent:
    def __init__(
        self,
        llm_client: any,
        tools: Dict[str, Callable],
        max_steps: int = 10
    ):
        """
        Initialize ReAct agent.

        Args:
            llm_client: LLM API client
            tools: Dictionary of tool name to function
            max_steps: Maximum reasoning steps
        """
        self.llm_client = llm_client
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def think(self, query: str, observation: Optional[str] = None) -> str:
        """
        Generate next thought based on query and observation.

        Args:
            query: User query
            observation: Result of previous action

        Returns:
            Generated thought
        """
        # TODO: Implement thought generation
        # 1. Build prompt with query and history
        # 2. Call LLM
        # 3. Extract thought
        pass

    def parse_action(self, thought: str) -> tuple[str, Dict]:
        """
        Parse action from thought.

        Args:
            thought: Agent's thought

        Returns:
            Tuple of (action_type, action_params)
        """
        # TODO: Implement action parsing
        # Expected format: "Action: SEARCH[query]"
        pass

    def act(self, action_type: str, params: Dict) -> str:
        """
        Execute action.

        Args:
            action_type: Type of action to execute
            params: Action parameters

        Returns:
            Action result/observation
        """
        # TODO: Implement action execution
        pass

    def run(self, query: str) -> Dict[str, any]:
        """
        Run ReAct loop.

        Args:
            query: User query

        Returns:
            Result dictionary with answer and trace
        """
        # TODO: Implement main loop
        pass
```

### Example Usage

```python
# Define tools
def search_tool(query: str) -> str:
    # Simulated search
    return f"Search results for: {query}"

def calculate_tool(expression: str) -> str:
    try:
        result = eval(expression)
        return f"Result: {result}"
    except:
        return "Calculation error"

tools = {
    "SEARCH": search_tool,
    "CALCULATE": calculate_tool
}

# Run agent
agent = ReActAgent(llm_client, tools)
result = agent.run("What is 15% of 240 plus the population of Paris?")
print(result["answer"])
```

### Success Criteria

- [ ] Agent generates coherent thoughts
- [ ] Actions are parsed correctly
- [ ] Loop terminates appropriately
- [ ] Final answer is accurate

---

## Exercise 2: Tool Registry System

**Difficulty:** Intermediate
**Time:** 60 minutes
**Module:** 7200 - Tool Use

### Task

Implement a robust tool registry with validation, error handling, and permission management.

### Requirements

1. Create a `ToolRegistry` class with:
   - Tool registration with metadata
   - Input validation
   - Permission checking
   - Execution monitoring
   - Error recovery

2. Support tool features:
   - Schema validation
   - Rate limiting
   - Timeout handling
   - Logging

### Solution Template

```python
from typing import Callable, Dict, Any, Optional
from functools import wraps
import time
from datetime import datetime, timedelta

class Tool:
    def __init__(
        self,
        name: str,
        func: Callable,
        description: str,
        schema: Dict[str, Any],
        permissions: list = None,
        rate_limit: int = 10,
        timeout: int = 30
    ):
        """
        Tool definition.

        Args:
            name: Tool name
            func: Tool function
            description: Tool description
            schema: Input/output schema
            permissions: Required permissions
            rate_limit: Calls per minute
            timeout: Timeout in seconds
        """
        self.name = name
        self.func = func
        self.description = description
        self.schema = schema
        self.permissions = permissions or []
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.call_count = []
        self.execution_log = []

    def validate_input(self, params: Dict) -> tuple[bool, Optional[str]]:
        """Validate input parameters against schema."""
        # TODO: Implement validation
        pass

    def check_permissions(self, user_permissions: list) -> bool:
        """Check if user has required permissions."""
        # TODO: Implement permission check
        pass

    def check_rate_limit(self) -> bool:
        """Check if rate limit exceeded."""
        # TODO: Implement rate limiting
        pass

    def execute(self, params: Dict, user_permissions: list) -> Any:
        """Execute tool with all checks."""
        # TODO: Implement execution with monitoring
        pass


class ToolRegistry:
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Tool] = {}
        self.default_timeout = 30

    def register(self, tool: Tool):
        """Register a new tool."""
        # TODO: Implement registration
        pass

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self.tools.get(name)

    def list_tools(self, user_permissions: list = None) -> list:
        """List available tools based on permissions."""
        # TODO: Implement filtering
        pass

    def execute_tool(
        self,
        tool_name: str,
        params: Dict,
        user_permissions: list = None
    ) -> Any:
        """Execute a tool with all safety checks."""
        # TODO: Implement safe execution
        pass
```

### Example Tools

```python
# File system tool
def read_file(file_path: str) -> str:
    """Read file contents (whitelisted paths only)."""
    ALLOWED_PATHS = ["/tmp", "/home/user/docs"]
    if not any(file_path.startswith(p) for p in ALLOWED_PATHS):
        raise PermissionError(f"Path not allowed: {file_path}")
    with open(file_path, 'r') as f:
        return f.read()

# API tool
def call_api(endpoint: str, method: str = "GET") -> Dict:
    """Make API call to whitelisted endpoints."""
    ALLOWED_DOMAINS = ["api.example.com"]
    # TODO: Implement
    pass

# Register tools
registry = ToolRegistry()
registry.register(Tool(
    name="read_file",
    func=read_file,
    description="Read file from allowed paths",
    schema={"type": "object", "properties": {"file_path": {"type": "string"}}},
    permissions=["fs:read"],
    rate_limit=60
))
```

### Success Criteria

- [ ] Tools register correctly
- [ ] Input validation works
- [ ] Permissions are enforced
- [ ] Rate limiting prevents abuse
- [ ] Execution is logged

---

## Exercise 3: Multi-Agent System

**Difficulty:** Advanced
**Time:** 90 minutes
**Module:** 7300 - Orchestration

### Task

Implement a multi-agent system with specialized agents and coordination.

### Requirements

1. Create specialized agent types:
   - `ResearchAgent`: Information gathering
   - `AnalysisAgent`: Data analysis
   - `WriterAgent`: Content generation
   - `CoordinatorAgent`: Orchestrates others

2. Implement communication patterns:
   - Message passing
   - Task delegation
   - Result aggregation
   - Conflict resolution

### Solution Template

```python
from typing import List, Dict, Any
from enum import Enum
import uuid

class AgentRole(Enum):
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"

class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    QUERY = "query"
    RESPONSE = "response"

class Message:
    def __init__(
        self,
        sender: str,
        receiver: str,
        msg_type: MessageType,
        content: Any
    ):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.receiver = receiver
        self.type = msg_type
        self.content = content
        self.timestamp = time.time()

class Agent:
    def __init__(self, name: str, role: AgentRole, llm_client):
        self.name = name
        self.role = role
        self.llm_client = llm_client
        self.inbox = []
        self.outbox = []
        self.context = {}

    def receive(self, message: Message):
        """Receive message."""
        self.inbox.append(message)

    def send(self, receiver: str, msg_type: MessageType, content: Any):
        """Send message to another agent."""
        msg = Message(self.name, receiver, msg_type, content)
        self.outbox.append(msg)
        return msg

    def process(self) -> List[Message]:
        """Process inbox and generate responses."""
        # TODO: Implement message processing
        pass

    def think(self, prompt: str) -> str:
        """Generate thought using LLM."""
        # TODO: Implement LLM call
        pass


class MultiAgentSystem:
    def __init__(self):
        """Initialize multi-agent system."""
        self.agents: Dict[str, Agent] = {}
        self.message_log = []

    def add_agent(self, agent: Agent):
        """Add agent to system."""
        self.agents[agent.name] = agent

    def route_message(self, message: Message):
        """Route message to recipient."""
        # TODO: Implement message routing
        pass

    def broadcast(self, sender: str, msg_type: MessageType, content: Any):
        """Broadcast message to all agents."""
        # TODO: Implement broadcast
        pass

    def run_task(self, task: str, max_steps: int = 20) -> Dict:
        """
        Execute a task using the multi-agent system.

        Args:
            task: Task description
            max_steps: Maximum coordination steps

        Returns:
            Final result
        """
        # TODO: Implement task execution
        pass
```

### Example Task Flow

```python
# Create agents
coordinator = Agent("coordinator", AgentRole.COORDINATOR, llm)
researcher = Agent("researcher", AgentRole.RESEARCHER, llm)
analyst = Agent("analyst", AgentRole.ANALYST, llm)
writer = Agent("writer", AgentRole.WRITER, llm)

# Setup system
system = MultiAgentSystem()
for agent in [coordinator, researcher, analyst, writer]:
    system.add_agent(agent)

# Execute task
result = system.run_task(
    "Research the latest AI safety guidelines and write a summary"
)
print(result)
```

### Success Criteria

- [ ] Agents communicate correctly
- [ ] Coordinator delegates tasks appropriately
- [ ] Results are aggregated properly
- [ ] System completes complex tasks
- [ ] Deadlocks are avoided

---

## Exercise 4: Agent Memory System

**Difficulty:** Intermediate
**Time:** 60 minutes
**Module:** 7400 - Agent Memory

### Task

Implement a hierarchical memory system for agents with short-term, working, and long-term memory.

### Requirements

1. Create memory types:
   - **Short-term**: Recent conversations (episodic)
   - **Working**: Current task context
   - **Long-term**: Persistent knowledge (semantic)

2. Implement memory operations:
   - Store: Add information to memory
   - Retrieve: Search memory by relevance
   - Consolidate: Move short-term to long-term
   - Forget: Prune irrelevant memories

3. Use vector embeddings for semantic search

### Solution Template

```python
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

@dataclass
class Memory:
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    timestamp: datetime
    importance: float = 0.5
    access_count: int = 0

class ShortTermMemory:
    """Recent conversation history (episodic memory)."""

    def __init__(self, max_memories: int = 100):
        self.memories: List[Memory] = []
        self.max_memories = max_memories

    def add(self, content: str, embedding: np.ndarray, metadata: Dict = None):
        """Add memory to short-term storage."""
        # TODO: Implement
        pass

    def get_recent(self, k: int = 5) -> List[Memory]:
        """Get k most recent memories."""
        # TODO: Implement
        pass

    def consolidate_to_longterm(self, threshold: float = 0.7) -> List[Memory]:
        """Get memories ready for long-term storage."""
        # TODO: Implement consolidation logic
        pass


class WorkingMemory:
    """Current task context (working memory)."""

    def __init__(self, max_items: int = 10):
        self.context: Dict[str, Any] = {}
        self.stack: List[Dict] = []
        self.max_items = max_items

    def push_context(self, context: Dict[str, Any]):
        """Push new context onto stack."""
        # TODO: Implement
        pass

    def pop_context(self) -> Dict[str, Any]:
        """Pop context from stack."""
        # TODO: Implement
        pass

    def update(self, key: str, value: Any):
        """Update current context."""
        # TODO: Implement
        pass

    def get_context_window(self) -> str:
        """Get formatted context window for LLM."""
        # TODO: Implement
        pass


class LongTermMemory:
    """Persistent knowledge base (semantic memory)."""

    def __init__(self, embedding_model, vector_db_client):
        self.embedding_model = embedding_model
        self.vector_db = vector_db_client
        self.collection_name = "agent_memories"

    def store(
        self,
        content: str,
        metadata: Dict[str, Any],
        importance: float = 0.5
    ):
        """Store memory in vector database."""
        # TODO: Implement
        pass

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Dict[str, Any] = None
    ) -> List[Memory]:
        """Retrieve relevant memories."""
        # TODO: Implement vector search
        pass

    def update_importance(self, memory_id: str, delta: float):
        """Update memory importance score."""
        # TODO: Implement
        pass

    def forget_old_memories(self, age_days: int = 30, importance_threshold: float = 0.3):
        """Remove old, unimportant memories."""
        # TODO: Implement forgetting
        pass


class AgentMemorySystem:
    """Hierarchical memory system for agents."""

    def __init__(self, embedding_model, vector_db_client):
        self.short_term = ShortTermMemory()
        self.working = WorkingMemory()
        self.long_term = LongTermMemory(embedding_model, vector_db_client)

    def remember(self, content: str, context: str = "", metadata: Dict = None):
        """Store information in appropriate memory layer."""
        # TODO: Implement storage logic
        pass

    def recall(
        self,
        query: str,
        memory_types: List[str] = None
    ) -> Dict[str, List[Memory]]:
        """Retrieve information from memory layers."""
        # TODO: Implement retrieval
        pass

    def consolidate(self):
        """Consolidate short-term to long-term memory."""
        # TODO: Implement consolidation
        pass

    def get_full_context(self) -> str:
        """Get complete context for LLM prompt."""
        # TODO: Implement context building
        pass
```

### Success Criteria

- [ ] Short-term memory stores recent interactions
- [ ] Working memory maintains task context
- [ ] Long-term memory enables semantic retrieval
- [ ] Consolidation transfers important memories
- [ ] Context window is properly formatted

---

## Exercise 5: Sandboxed Code Execution

**Difficulty:** Advanced
**Time:** 75 minutes
**Module:** 7200 - Tool Use (Security)

### Task

Implement a secure, sandboxed code execution environment for agents.

### Requirements

1. Create a `SandboxExecutor` with:
   - Resource limits (CPU, memory, time)
   - Whitelisted imports
   - Filesystem isolation
   - Network restrictions
   - Output sanitization

2. Support execution of:
   - Python code snippets
   - Mathematical expressions
   - Data processing tasks

3. Implement safety measures:
   - Timeout handling
   - Memory monitoring
   - Exception capture
   - Result validation

### Solution Template

```python
import subprocess
import tempfile
import os
import resource
from typing import Dict, Any, Optional
import json

class SandboxConfig:
    """Sandbox configuration."""

    # Time limits (seconds)
    MAX_EXECUTION_TIME = 5

    # Memory limits (bytes)
    MAX_MEMORY = 100 * 1024 * 1024  # 100MB

    # Whitelisted modules
    ALLOWED_IMPORTS = [
        "math", "statistics", "datetime",
        "collections", "itertools", "fractions",
        "decimal", "random"
    ]

    # Blocked operations
    BLOCKED_PATTERNS = [
        "import os",
        "import sys",
        "import subprocess",
        "__import__",
        "eval(",
        "exec(",
        "compile(",
        "open(",
        "file(",
        "__builtins__"
    ]


class SandboxExecutor:
    """Secure code execution sandbox."""

    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        self.temp_dir = tempfile.mkdtemp()

    def validate_code(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate code for safety.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # TODO: Implement validation
        # 1. Check for blocked patterns
        # 2. Validate imports
        # 3. Check for malicious code
        pass

    def execute_python(self, code: str, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute Python code in sandbox.

        Args:
            code: Python code to execute
            inputs: Input variables

        Returns:
            Result dictionary with output, errors, execution_time
        """
        # TODO: Implement sandboxed execution
        # 1. Validate code
        # 2. Create temporary file
        # 3. Execute with resource limits
        # 4. Capture output and errors
        pass

    def execute_expression(self, expression: str) -> Any:
        """
        Execute mathematical expression safely.

        Args:
            expression: Mathematical expression

        Returns:
            Computed result
        """
        # TODO: Implement safe expression evaluation
        pass

    def execute_with_subprocess(
        self,
        code: str,
        timeout: int = None
    ) -> subprocess.CompletedProcess:
        """
        Execute code using subprocess with resource limits.

        Args:
            code: Code to execute
            timeout: Execution timeout

        Returns:
            Completed process result
        """
        # TODO: Implement subprocess execution
        pass

    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
```

### Example Usage

```python
# Initialize executor
executor = SandboxExecutor()

# Execute code
result = executor.execute_python("""
import math

def calculate_area(radius):
    return math.pi * radius ** 2

areas = [calculate_area(r) for r in range(1, 6)]
print(f"Areas: {areas}")
print(f"Total: {sum(areas)}")
""")

print(result["output"])
print(f"Execution time: {result['execution_time']}s")

# Evaluate expression
result = executor.execute_expression("2 * pi * 10^2")
print(result)  # 1256.637...
```

### Success Criteria

- [ ] Safe code execution works
- [ ] Resource limits are enforced
- [ ] Malicious code is blocked
- [ ] Output is properly captured
- [ ] Timeouts prevent infinite loops

---

## Exercise 6: Prompt Injection Defense

**Difficulty:** Advanced
**Time:** 60 minutes
**Module:** 7500 - Agent Security

### Task

Implement prompt injection detection and defense mechanisms.

### Requirements

1. Create a `PromptDefender` class with:
   - Injection pattern detection
   - Input sanitization
   - Output validation
   - Rate limiting per user

2. Detect attack types:
   - Direct injection ("Ignore previous instructions")
   - Role playing ("Pretend you're...")
   - Code injection ("Execute this...")
   - Data exfiltration ("Print all data...")

3. Implement defense strategies:
   - Delimiters and formatting
   - Instruction separation
   - Output filtering
   - Anomaly detection

### Solution Template

```python
from typing import List, Tuple, Optional
import re
from datetime import datetime, timedelta

class PromptDefender:
    """Defend against prompt injection attacks."""

    # Attack patterns
    INJECTION_PATTERNS = [
        r"ignore (all )?(previous|above) instructions",
        r"pretend (you are|you're)",
        r"act as (a|an)",
        r"execute (this|the following)",
        r"print (all )?(the )?(data|passwords|keys)",
        r"reveal (your )?(system )?prompt",
        r"(show|display) (your )?(instructions|prompt)",
        r"override",
        r"bypass",
        r"admin",
        r"root"
    ]

    def __init__(self):
        self.attack_log = []
        self.user_request_counts = {}
        self.blocked_users = set()

    def detect_injection(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Detect prompt injection attempts.

        Args:
            prompt: User input prompt

        Returns:
            Tuple of (is_injection, matched_pattern)
        """
        # TODO: Implement detection
        # 1. Check against known patterns
        # 2. Analyze linguistic patterns
        # 3. Check for encoding tricks
        pass

    def sanitize_input(self, prompt: str, user_id: str = None) -> str:
        """
        Sanitize user input.

        Args:
            prompt: User input
            user_id: User identifier

        Returns:
            Sanitized prompt
        """
        # TODO: Implement sanitization
        # 1. Check rate limits
        # 2. Remove dangerous characters
        # 3. Apply formatting rules
        pass

    def format_system_prompt(self, system_prompt: str) -> str:
        """
        Format system prompt with protection.

        Args:
            system_prompt: Original system prompt

        Returns:
            Protected system prompt
        """
        # TODO: Implement prompt hardening
        # 1. Add delimiters
        # 2. Add instruction separation
        # 3. Add output constraints
        pass

    def validate_output(self, output: str, original_task: str) -> Tuple[bool, Optional[str]]:
        """
        Validate LLM output for injection leakage.

        Args:
            output: LLM generated output
            original_task: Original user task

        Returns:
            Tuple of (is_safe, warning_message)
        """
        # TODO: Implement output validation
        # 1. Check for system prompt leakage
        # 2. Verify output relevance
        # 3. Detect formatting anomalies
        pass

    def check_rate_limit(self, user_id: str, max_requests: int = 10, window_minutes: int = 1) -> bool:
        """
        Check if user exceeded rate limit.

        Args:
            user_id: User identifier
            max_requests: Max requests per window
            window_minutes: Time window in minutes

        Returns:
            True if rate limit OK, False if exceeded
        """
        # TODO: Implement rate limiting
        pass

    def block_user(self, user_id: str, reason: str):
        """Block user for suspicious activity."""
        self.blocked_users.add(user_id)
        self.attack_log.append({
            "user_id": user_id,
            "reason": reason,
            "timestamp": datetime.now()
        })
```

### Success Criteria

- [ ] Injection patterns are detected
- [ ] False positives are minimized
- [ ] Input sanitization preserves intent
- [ ] Output validation catches leaks
- [ ] Rate limiting prevents abuse

---

## Exercise 7: Complete Agent System

**Difficulty:** Expert
**Time:** 120 minutes
**Module:** 7100-7500 (Comprehensive)

### Task

Build a complete, production-ready agent system combining all components.

### Requirements

1. Integrate all components:
   - ReAct reasoning loop
   - Tool registry with safety
   - Multi-agent coordination
   - Memory system
   - Security defenses

2. Implement features:
   - Task planning and decomposition
   - Progress tracking
   - Error recovery
   - Monitoring and logging

3. Create API interface

### Architecture

```python
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

class ProductionAgentSystem:
    """Production-ready agent system."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize agent system.

        Args:
            config: System configuration
        """
        self.config = config

        # Initialize components
        # TODO: Initialize all components
        self.react_agent = None
        self.tool_registry = None
        self.multi_agent = None
        self.memory_system = None
        self.defender = None

        # Setup logging
        self.logger = self._setup_logging()

        # Metrics
        self.metrics = {
            "requests_processed": 0,
            "errors": 0,
            "average_response_time": 0
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging system."""
        # TODO: Implement
        pass

    def plan_task(self, task: str) -> List[Dict]:
        """
        Decompose task into subtasks.

        Args:
            task: Complex task description

        Returns:
            List of subtask dictionaries
        """
        # TODO: Implement planning
        pass

    def execute_task(
        self,
        task: str,
        user_id: str = None,
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Execute task with full agent capabilities.

        Args:
            task: Task description
            user_id: User identifier
            context: Additional context

        Returns:
            Result dictionary with answer, trace, metadata
        """
        start_time = datetime.now()

        try:
            # TODO: Implement full execution flow
            # 1. Validate and sanitize input
            # 2. Plan task decomposition
            # 3. Execute using appropriate agent(s)
            # 4. Use memory for context
            # 5. Monitor and log execution
            # 6. Validate output

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "answer": "Task completed",
                "trace": [],
                "metadata": {
                    "execution_time": execution_time,
                    "tools_used": [],
                    "memory_accessed": []
                },
                "status": "success"
            }

        except Exception as e:
            self.metrics["errors"] += 1
            self.logger.error(f"Task execution failed: {e}")
            return {
                "answer": None,
                "error": str(e),
                "status": "error"
            }

    def get_status(self) -> Dict[str, Any]:
        """Get system status and metrics."""
        # TODO: Implement status reporting
        pass

    def shutdown(self):
        """Gracefully shutdown system."""
        # TODO: Implement cleanup
        pass
```

### API Endpoint Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="PROJECT-OMEGA Agent API")
agent_system = ProductionAgentSystem(config={})

class TaskRequest(BaseModel):
    task: str
    user_id: Optional[str] = None
    context: Optional[Dict] = None

@app.post("/api/v1/agent/execute")
async def execute_task(request: TaskRequest):
    """Execute agent task."""
    try:
        result = agent_system.execute_task(
            task=request.task,
            user_id=request.user_id,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agent/status")
async def get_status():
    """Get system status."""
    return agent_system.get_status()
```

### Success Criteria

- [ ] All components integrate properly
- [ ] Tasks are decomposed correctly
- [ ] Memory improves performance
- [ ] Security measures work
- [ ] API is responsive
- [ ] Errors are handled gracefully

---

## Bonus Challenges

### Challenge 1: Autonomous Research Agent

Build an agent that can:
- Research a topic autonomously
- Synthesize findings
- Generate comprehensive report
- Cite sources properly

### Challenge 2: Code Generation Agent

Create a coding assistant with:
- File system understanding
- Code generation and modification
- Test generation and execution
- Debugging capabilities

### Challenge 3: Creative Writing Agent

Implement a creative system for:
- Story generation with consistency
- Character development
- Plot construction
- Style adaptation

---

## Evaluation

### Grading Criteria

| Exercise | Points | Criteria |
|----------|--------|----------|
| Ex 1: ReAct Loop | 15 | Loop implementation |
| Ex 2: Tool Registry | 20 | Safety features |
| Ex 3: Multi-Agent | 25 | Coordination |
| Ex 4: Memory System | 20 | Memory layers |
| Ex 5: Sandboxing | 20 | Security |
| Ex 6: Prompt Defense | 15 | Detection accuracy |
| Ex 7: Complete System | 35 | Integration |
| **Total** | **150** | |

### Submission

1. Create GitHub repository
2. Document architecture
3. Include demo videos
4. Add test suite

---

## Resources

- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)
- [BabyAGI](https://github.com/yoheinakajima/babyagi)
- [Agent Protocol](https://agentprotocol.ai/)

---

**Last Updated:** 2026-02-05
**Phase:** 7 - Agentic Systems
**Status:** Ready for Practice
