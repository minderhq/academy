# SOLUTION-LAB-008: Agent Fleet

## Overview
Complete solution for orchestrating multiple specialized AI agents with coordination and communication protocols.

---

## Prerequisites

```bash
pip install langchain langchain-openai asyncio
```

---

## Core Solution

```python
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime
import uuid

# =====================================================================
# BASE AGENT FRAMEWORK
# =====================================================================

class AgentRole(Enum):
    """Standard agent roles."""
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"

@dataclass
class Task:
    """Represents a task to be processed by agents."""
    id: str
    type: str
    description: str
    input_data: Dict[str, Any]
    priority: int = 5
    status: str = "pending"
    assigned_to: Optional[str] = None
    result: Optional[Any] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class AgentMessage:
    """Message passed between agents."""
    id: str
    from_agent: str
    to_agent: str
    content: Dict[str, Any]
    timestamp: datetime
    reply_to: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        self.timestamp = datetime.now()

# =====================================================================
# BASE AGENT CLASS
# =====================================================================

class BaseAgent:
    """
    Base class for all agents in the fleet.
    Provides common functionality and interface.
    """

    def __init__(self, name: str, role: AgentRole, config: Dict[str, Any] = None):
        """
        Initialize base agent.

        Args:
            name: Unique agent identifier
            role: Agent's functional role
            config: Optional configuration dictionary
        """
        self.name = name
        self.role = role
        self.config = config or {}
        self.message_queue = asyncio.Queue()
        self.state = {}
        self.is_active = True

    async def process_task(self, task: Task) -> Any:
        """
        Process a task assigned to this agent.
        Override in subclasses with specific implementations.
        """
        raise NotImplementedError(f"{self.name} agent must implement process_task()")

    async def send_message(self, to_agent: str, content: Dict[str, Any], reply_to: str = None):
        """Send a message to another agent."""
        # This would interface with the fleet's communication system
        pass

    async def receive_message(self, message: AgentMessage):
        """Receive a message from another agent."""
        await self.message_queue.put(message)

    async def get_status(self) -> Dict[str, Any]:
        """Return current agent status."""
        return {
            "name": self.name,
            "role": self.role.value,
            "is_active": self.is_active,
            "state": self.state,
            "queue_size": self.message_queue.qsize()
        }

# =====================================================================
# SPECIALIZED AGENT IMPLEMENTATIONS
# =====================================================================

class ResearchAgent(BaseAgent):
    """
    Agent specialized in web research, document analysis, and information gathering.
    """

    def __init__(self, name: str = "researcher_1", config: Dict[str, Any] = None):
        super().__init__(name, AgentRole.RESEARCHER, config)

    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process research tasks like:
        - Web scraping for information
        - Document analysis
        - Data gathering from multiple sources
        """
        task_type = task.type

        if task_type == "web_search":
            return await self._web_search(task.input_data)
        elif task_type == "document_analysis":
            return await self._analyze_document(task.input_data)
        elif task_type == "data_collection":
            return await self._collect_data(task.input_data)
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def _web_search(self, query: str) -> Dict[str, Any]:
        """Perform web search and return results."""
        # Simulated web search - in production, use actual search API
        results = [
            {"title": f"Result 1 for {query}", "url": "https://example.com/1", "snippet": f"Information about {query}"},
            {"title": f"Result 2 for {query}", "url": "https://example.com/2", "snippet": f"More details about {query}"}
        ]
        return {
            "status": "completed",
            "results": results,
            "count": len(results),
            "query": query
        }

    async def _analyze_document(self, document: str) -> Dict[str, Any]:
        """Analyze document and extract key information."""
        # Simulated document analysis
        return {
            "status": "completed",
            "summary": document[:200] + "..." if len(document) > 200 else document,
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "word_count": len(document.split())
        }

    async def _collect_data(self, sources: List[str]) -> Dict[str, Any]:
        """Collect data from multiple sources."""
        collected = []
        for source in sources:
            # Simulate data collection
            collected.append({"source": source, "data": f"Data from {source}"})
        return {
            "status": "completed",
            "collected": collected,
            "count": len(collected)
        }

class CodeAgent(BaseAgent):
    """
    Agent specialized in code generation, debugging, and code review.
    """

    def __init__(self, name: str = "coder_1", config: Dict[str, Any] = None):
        super().__init__(name, AgentRole.CODER, config)
        self.supported_languages = ["python", "javascript", "java", "cpp"]
        self.code_history = []

    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process coding tasks like:
        - Code generation
        - Code debugging
        - Code review and optimization
        """
        task_type = task.type

        if task_type == "generate":
            return await self._generate_code(task.input_data)
        elif task_type == "debug":
            return await self._debug_code(task.input_data)
        elif task_type == "review":
            return await self._review_code(task.input_data)
        elif task_type == "optimize":
            return await self._optimize_code(task.input_data)
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def _generate_code(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on specification."""
        language = spec.get("language", "python")
        requirements = spec.get("requirements", [])
        description = spec.get("description", "")

        # Simulated code generation
        code = f"# Generated code for: {description}\n"
        code += f"# Language: {language}\n\n"

        if language == "python":
            code += "def solution():\n"
            for req in requirements:
                code += f"    # {req}\n"
            code += "    pass\n"
        else:
            code += f"// Code for {description}\n"

        self.code_history.append(code)

        return {
            "status": "completed",
            "code": code,
            "language": language,
            "lines": len(code.split('\n'))
        }

    async def _debug_code(self, code_info: Dict[str, Any]) -> Dict[str, Any]:
        """Debug code and identify issues."""
        code = code_info.get("code", "")
        language = code_info.get("language", "python")

        issues = []
        # Simulated debugging
        if "TODO" in code or "FIXME" in code:
            issues.append("Contains TODO/FIXME markers")
        if len(code.split('\n')) > 100:
            issues.append("Function too long, consider refactoring")

        return {
            "status": "completed",
            "issues": issues,
            "suggestions": ["Suggestion 1", "Suggestion 2"] if issues else ["No issues found"]
        }

    async def _review_code(self, code_info: Dict[str, Any]) -> Dict[str, Any]:
        """Review code for best practices and quality."""
        code = code_info.get("code", "")
        language = code_info.get("language", "python")

        return {
            "status": "completed",
            "review": "Code follows basic conventions",
            "rating": 7.5,
            "improvements": ["Add docstrings", "Add type hints"]
        }

    async def _optimize_code(self, code_info: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize code for better performance."""
        return {
            "status": "completed",
            "optimized_code": code_info.get("code", ""),
            "improvements": ["Reduced time complexity", "Improved memory usage"]
        }

class AnalystAgent(BaseAgent):
    """
    Agent specialized in data analysis, pattern recognition, and insights generation.
    """

    def __init__(self, name: str = "analyst_1", config: Dict[str, Any] = None):
        super().__init__(name, AgentRole.ANALYST, config)

    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process analysis tasks like:
        - Data analysis
        - Pattern recognition
        - Statistical analysis
        - Insights generation
        """
        task_type = task.type

        if task_type == "analyze_data":
            return await self._analyze_data(task.input_data)
        elif task_type == "find_patterns":
            return await self._find_patterns(task.input_data)
        elif task_type == "statistics":
            return await self._compute_statistics(task.input_data)
        elif task_type == "generate_insights":
            return await self._generate_insights(task.input_data)
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def _analyze_data(self, data: List[Any]) -> Dict[str, Any]:
        """Analyze data and provide summary."""
        return {
            "status": "completed",
            "summary": f"Analyzed {len(data)} data points",
            "statistics": {
                "mean": sum(data) / len(data) if isinstance(data[0], (int, float)) else "N/A",
                "count": len(data)
            }
        }

    async def _find_patterns(self, data: List[Any]) -> Dict[str, Any]:
        """Find patterns in data."""
        return {
            "status": "completed",
            "patterns": ["Pattern 1: Linear trend", "Pattern 2: Seasonal variation"],
            "confidence": 0.85
        }

    async def _compute_statistics(self, data: List[Any]) -> Dict[str, Any]:
        """Compute statistical metrics."""
        return {
            "status": "completed",
            "metrics": ["mean", "median", "std_dev", "correlation"],
            "summary": "Statistical analysis complete"
        }

    async def _generate_insights(self, data: List[Any]) -> Dict[str, Any]:
        """Generate actionable insights from data."""
        return {
            "status": "completed",
            "insights": [
                "Insight 1: Data shows positive trend",
                "Insight 2: Outliers detected in 5% of data"
            ]
        }

# =====================================================================
# COORDINATOR
# =====================================================================

class Coordinator:
    """
    Coordinates task execution across multiple agents.
    Handles task decomposition, agent selection, and result aggregation.
    """

    def __init__(self, agents: Dict[str, BaseAgent] = None):
        """
        Initialize coordinator.

        Args:
            agents: Dictionary of available agents
        """
        self.agents = agents or {}
        self.task_history = []
        self.workflow_templates = self._initialize_workflows()

    def _initialize_workflows(self) -> Dict[str, List[Dict]]:
        """Initialize workflow templates for common task types."""
        return {
            "complex_research": [
                {"agent": "researcher", "action": "gather_info"},
                {"agent": "analyst", "action": "analyze_data"},
                {"agent": "writer", "action": "create_report"}
            ],
            "code_development": [
                {"agent": "coder", "action": "write_code"},
                {"agent": "coder", "action": "review_code"},
                {"agent": "coder", "action": "optimize_code"}
            ],
            "data_analysis": [
                {"agent": "analyst", "action": "analyze"},
                {"agent": "analyst", "action": "find_patterns"},
                {"agent": "analyst", "action": "generate_insights"}
            ]
        }

    async def coordinate(self, task: Task, available_agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """
        Coordinate task execution across multiple agents.

        Args:
            task: Task to coordinate
            available_agents: Dictionary of available agents

        Returns:
            Aggregated result from all agents
        """
        # Determine execution strategy
        strategy = self._determine_strategy(task)

        if strategy == "single_agent":
            # Assign to single best agent
            agent = self._select_best_agent(task, available_agents)
            result = await agent.process_task(task)
            return {"strategy": "single", "agent": agent.name, "result": result}

        elif strategy == "workflow":
            # Execute predefined workflow
            return await self._execute_workflow(task, available_agents)

        elif strategy == "parallel":
            # Execute in parallel across multiple agents
            return await self._execute_parallel(task, available_agents)

        else:
            # Default to coordinator handling
            return await self._handle_complex_task(task, available_agents)

    def _determine_strategy(self, task: Task) -> str:
        """Determine best execution strategy for the task."""
        if task.type in ["web_search", "document_analysis", "generate_code"]:
            return "single_agent"
        elif task.type in ["complex_research", "full_report"]:
            return "workflow"
        elif task.type in ["multi_analysis"]:
            return "parallel"
        else:
            return "single_agent"

    def _select_best_agent(self, task: Task, available_agents: Dict[str, BaseAgent]) -> BaseAgent:
        """Select the best agent for a given task."""
        task_type_to_role = {
            "web_search": AgentRole.RESEARCHER,
            "document_analysis": AgentRole.RESEARCHER,
            "generate_code": AgentRole.CODER,
            "debug": AgentRole.CODER,
            "review": AgentRole.CODER,
            "analyze_data": AgentRole.ANALYST,
            "find_patterns": AgentRole.ANALYST,
            "generate_insights": AgentRole.ANALYST,
        }

        preferred_role = task_type_to_role.get(task.type)

        for agent in available_agents.values():
            if agent.role == preferred_role:
                return agent

        # Fallback to first available agent
        return next(iter(available_agents.values()))

    async def _execute_workflow(self, task: Task, available_agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Execute a predefined workflow across multiple agents."""
        workflow_name = task.input_data.get("workflow", "complex_research")
        workflow = self.workflow_templates.get(workflow_name, [])

        results = []
        for step in workflow:
            agent_name = step["agent"]
            action = step["action"]

            if agent_name in available_agents:
                agent = available_agents[agent_name]

                # Create subtask for this step
                subtask = Task(
                    id=f"{task.id}_{step['agent']}_{step['action']}",
                    type=action,
                    description=f"{action} for {task.description}",
                    input_data=task.input_data,
                    priority=task.priority
                )

                result = await agent.process_task(subtask)
                results.append({
                    "agent": agent_name,
                    "action": action,
                    "result": result
                })

        return {
            "strategy": "workflow",
            "workflow": workflow_name,
            "results": results
        }

    async def _execute_parallel(self, task: Task, available_agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Execute task in parallel across multiple agents."""
        # Create tasks for all agents
        tasks = []
        for agent_name, agent in available_agents.items():
            subtask = Task(
                id=f"{task.id}_{agent_name}",
                type=task.type,
                description=f"{task.description} by {agent_name}",
                input_data=task.input_data,
                priority=task.priority
            )
            tasks.append((agent, subtask))

        # Execute in parallel
        results = await asyncio.gather(*[agent.process_task(subtask) for agent, subtask in tasks])

        return {
            "strategy": "parallel",
            "results": [{"agent": agent.name, "result": result} for agent, result in zip([a for a, _ in tasks], results)]
        }

    async def _handle_complex_task(self, task: Task, available_agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Handle complex tasks that don't fit standard patterns."""
        # Decompose task into subtasks
        subtasks = self._decompose_task(task)

        # Execute subtasks
        results = []
        for subtask in subtasks:
            agent = self._select_best_agent(subtask, available_agents)
            result = await agent.process_task(subtask)
            results.append(result)

        # Aggregate results
        return {
            "strategy": "complex",
            "subtasks": len(subtasks),
            "results": results
        }

    def _decompose_task(self, task: Task) -> List[Task]:
        """Decompose complex task into simpler subtasks."""
        # Simplified task decomposition
        subtasks = []

        # Add research subtask
        subtasks.append(Task(
            id=f"{task.id}_research",
            type="web_search",
            description=f"Research for: {task.description}",
            input_data={"query": task.description},
            priority=task.priority
        ))

        # Add analysis subtask
        subtasks.append(Task(
            id=f"{task.id}_analysis",
            type="analyze_data",
            description=f"Analyze: {task.description}",
            input_data={"data": task.input_data},
            priority=task.priority + 1
        ))

        return subtasks

# =====================================================================
# AGENT FLEET - MAIN ORCHESTRATOR
# =====================================================================

class AgentFleet:
    """
    Main orchestrator for managing multiple specialized agents.
    Handles task routing, coordination, and inter-agent communication.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize agent fleet.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Initialize specialized agents
        self.agents = {
            "researcher_1": ResearchAgent("researcher_1", self.config.get("researcher", {})),
            "researcher_2": ResearchAgent("researcher_2", self.config.get("researcher", {})),
            "coder_1": CodeAgent("coder_1", self.config.get("coder", {})),
            "coder_2": CodeAgent("coder_2", self.config.get("coder", {})),
            "analyst_1": AnalystAgent("analyst_1", self.config.get("analyst", {})),
            "analyst_2": AnalystAgent("analyst_2", self.config.get("analyst", {})),
        }

        # Initialize coordinator
        self.coordinator = Coordinator(self.agents)

        # Message passing system
        self.message_channels = {}
        self.active_tasks = {}
        self.task_results = {}

        # Fleet metrics
        self.metrics = {
            "tasks_processed": 0,
            "tasks_by_agent": {name: 0 for name in self.agents.keys()},
            "total_execution_time": 0
        }

    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task through the agent fleet.

        Args:
            task: Task to process

        Returns:
            Processing result with metadata
        """
        start_time = datetime.now()

        # Route task to appropriate agent(s)
        task_type = task.type

        # Select execution strategy
        if task_type in ["web_search", "document_analysis"]:
            # Research task
            agent = self.agents["researcher_1"]
            result = await agent.process_task(task)
            self._update_metrics(agent.name)

        elif task_type in ["generate", "debug", "review", "optimize"]:
            # Coding task
            agent = self.agents["coder_1"]
            result = await agent.process_task(task)
            self._update_metrics(agent.name)

        elif task_type in ["analyze", "statistics", "patterns"]:
            # Analysis task
            agent = self.agents["analyst_1"]
            result = await agent.process_task(task)
            self._update_metrics(agent.name)

        elif task_type == "complex_research":
            # Multi-agent workflow
            result = await self.coordinator.coordinate(task, self.agents)

        elif task_type == "parallel_analysis":
            # Parallel execution
            result = await self.coordinator.coordinate(task, self.agents)

        else:
            # Default to coordinator
            result = await self.coordinator.coordinate(task, self.agents)

        # Update metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        self.metrics["tasks_processed"] += 1
        self.metrics["total_execution_time"] += execution_time

        # Store result
        self.task_results[task.id] = {
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now()
        }

        return {
            "task_id": task.id,
            "status": "completed",
            "result": result,
            "execution_time": execution_time,
            "fleet_metrics": self.metrics.copy()
        }

    def _update_metrics(self, agent_name: str):
        """Update agent-specific metrics."""
        if agent_name in self.metrics["tasks_by_agent"]:
            self.metrics["tasks_by_agent"][agent_name] += 1

    async def broadcast_message(self, message: Dict[str, Any]) -> List[AgentMessage]:
        """
        Broadcast message to all agents.

        Returns:
            List of sent messages
        """
        messages = []
        for agent_name, agent in self.agents.items():
            msg = AgentMessage(
                id=str(uuid.uuid4()),
                from_agent="fleet",
                to_agent=agent_name,
                content=message,
                timestamp=datetime.now()
            )
            await agent.receive_message(msg)
            messages.append(msg)
        return messages

    async def get_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents in the fleet."""
        statuses = {}
        for name, agent in self.agents.items():
            statuses[name] = await agent.get_status()
        return statuses

    def get_metrics(self) -> Dict[str, Any]:
        """Return fleet metrics."""
        return {
            **self.metrics,
            "active_agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_results)
        }

    def add_agent(self, agent: BaseAgent):
        """Add a new agent to the fleet."""
        self.agents[agent.name] = agent
        self.metrics["tasks_by_agent"][agent.name] = 0

    def remove_agent(self, agent_name: str):
        """Remove an agent from the fleet."""
        if agent_name in self.agents:
            del self.agents[agent_name]
            del self.metrics["tasks_by_agent"][agent_name]

# =====================================================================
# USAGE EXAMPLE
# =====================================================================

async def main():
    """Example usage of AgentFleet."""

    # Initialize agent fleet
    fleet = AgentFleet()

    # Example 1: Simple single-agent task
    task1 = Task(
        id="task_001",
        type="generate",
        description="Generate a Python function for sorting a list",
        input_data={
            "language": "python",
            "description": "Sort function",
            "requirements": ["Handle empty list", "Handle duplicates"]
        },
        priority=5
    )

    result1 = await fleet.process_task(task1)
    print(f"Task 1 Result:\n{result1}\n")

    # Example 2: Complex research workflow
    task2 = Task(
        id="task_002",
        type="complex_research",
        description="Research and report on latest AI trends",
        input_data={
            "topics": ["transformers", "diffusion models", "graph neural networks"],
            "workflow": "complex_research"
        },
        priority=8
    )

    result2 = await fleet.process_task(task2)
    print(f"Task 2 Result:\n{result2}\n")

    # Example 3: Parallel analysis
    task3 = Task(
        id="task_003",
        type="parallel_analysis",
        description="Analyze dataset from multiple perspectives",
        input_data={
            "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "analysis_types": ["statistics", "patterns", "insights"]
        },
        priority=6
    )

    result3 = await fleet.process_task(task3)
    print(f"Task 3 Result:\n{result3}\n")

    # Get fleet metrics
    metrics = fleet.get_metrics()
    print(f"Fleet Metrics:\n{metrics}\n")

    # Get agent statuses
    statuses = await fleet.get_agent_statuses()
    print(f"Agent Statuses:\n{statuses}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Key Features Implemented

### 1. Base Agent Framework
- Abstract base class for all agents
- Common message passing interface
- Status tracking and state management
- Async task processing

### 2. Specialized Agents
- **ResearchAgent**: Web search, document analysis, data collection
- **CodeAgent**: Code generation, debugging, review, optimization
- **AnalystAgent**: Data analysis, pattern recognition, insights generation

### 3. Coordinator
- Task decomposition strategies
- Agent selection algorithms
- Workflow template execution
- Parallel task coordination
- Result aggregation

### 4. Agent Fleet Orchestrator
- Multi-agent task routing
- Message broadcasting
- Metrics tracking
- Agent lifecycle management
- Task history tracking

### 5. Execution Strategies
- **Single Agent**: Direct routing to best agent
- **Workflow**: Sequential multi-agent workflows
- **Parallel**: Concurrent execution across agents
- **Complex**: Task decomposition with coordination

---

## Expected Results

When running this solution:
1. Fleet manages multiple specialized agents
2. Tasks are routed to appropriate agents
3. Complex tasks are decomposed and coordinated
4. Inter-agent communication enables collaboration
5. Metrics provide visibility into fleet performance

---

## Extension Points

To extend this solution:

1. **Add New Agent Types**:
   - Create subclass of BaseAgent
   - Implement process_task() method
   - Add to fleet with add_agent()

2. **Custom Workflows**:
   - Define workflow templates in Coordinator
   - Add execution logic in _execute_workflow()

3. **Advanced Communication**:
   - Implement message channels per topic
   - Add reply-to message threading
   - Create shared state management

4. **Resource Management**:
   - Add agent capacity tracking
   - Implement load balancing
   - Create agent priority queues

---

**Last Updated:** 2026-02-07
**Difficulty:** ⭐⭐⭐⭐⭐
**Lines of Code:** ~700
