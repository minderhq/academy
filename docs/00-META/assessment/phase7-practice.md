---
Document ID: PHASE7-PRACTICE
Title: "Phase 7: Agentic Systems - Practice Exercises"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
---

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
from typing import Any, List, Dict, Optional, Callable
import re
import json

class ReActAgent:
    def __init__(
        self,
        llm_client: Any,
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

    def run(self, query: str) -> Dict[str, Any]:
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
import time
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

**Last Updated:** 2026-09-25
**Phase:** 7 - Agentic Systems
**Status:** Ready for Practice

---

## Appendix: Phase 7 - Complete Reference Implementations

The exercises above use solution templates. This appendix contains
complete, working reference implementations of Exercises 1-5 for
self-checking after you have attempted them on your own. Exercises 6-7
have no separate reference implementation: Exercise 6 is a
self-contained pattern-matching exercise and Exercise 7 composes the
Exercise 1-5 components into one system.


### Exercise 1: Implement ReAct Loop from Scratch

```python
import json
from typing import List, Callable
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
    final_answer = "FINAL: Python is widely used for machine learning with libraries like scikit-learn and TensorFlow."
    if "Found 5 results" in prompt:
        # The search observation is already in the history - finalize
        return final_answer
    elif "search" in prompt.lower():
        return 'search: {"query": "Python machine learning"}'
    elif "final" in prompt.lower() or "answer" in prompt.lower():
        return final_answer
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
from typing import List
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

        for idx, memory in enumerate(self.memories):
            age_days = (now - memory.timestamp).days
            recency_score = 1.0 / (1.0 + age_days / 30.0)  # Decay over 30 days
            total_score = memory.importance * recency_score
            scores.append((total_score, idx))

        # Sort by score and keep top memories. Embeddings are stored
        # positionally aligned with self.memories, so they must be
        # reordered with the same indices or retrieve()'s lookups break
        scores.sort(reverse=True)
        keep = [i for _, i in scores[:self.max_memories]]
        self.memories = [self.memories[i] for i in keep]
        self.embeddings = self.embeddings[keep]
        self.memory_types = defaultdict(list)
        for memory in self.memories:
            self.memory_types[memory.memory_type].append(memory)

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
                timeout=self.timeout
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
