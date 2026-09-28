---
Document ID: LAB-008
Title: "LAB-008: Multi-Agent Fleet"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
---

# LAB-008: Multi-Agent Fleet

**Build a fleet of specialized AI agents working collaboratively**

**Time:** 6-8 hours
**Difficulty:** ⭐⭐⭐⭐ Expert
**Prerequisites:**
- LAB-004: ReAct Agent
- LAB-007: Production RAG
- 7101-ReAct-Loop-System.md
- 7102-Planning-Decomposition.md
- 7303-Framework-Comparison.md
- 7301-Orchestration.md

---

## 🎯 Lab Objectives

After completing this lab, you will be able to:
- ✅ Design multi-agent systems
- ✅ Implement specialized agents
- ✅ Build agent orchestration
- ✅ Add agent memory
- ✅ Deploy agent fleet to production

---

## 📋 Overview

### What is a Multi-Agent Fleet?

**Multi-Agent Fleet** = Multiple specialized agents working together:
- **Specialization:** Each agent excels at specific tasks
- **Collaboration:** Agents work together on complex problems
- **Orchestration:** Coordinator manages agent interactions
- **Memory:** Shared memory across all agents

### Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    User Request                         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Orchestrator Agent                     │
│  - Parse request                                       │
│  - Create plan                                         │
│  - Route to agents                                     │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Researcher   │  │   Analyst     │  │    Writer     │
│  Agent        │  │   Agent       │  │    Agent      │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Shared Memory Store                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ Part 1: Design Agent System (60 min)

### Step 1.1: Define Agent Roles

```python
# File: agents/agent_types.py
"""
Define specialized agent types for the fleet
"""

from enum import Enum

from pydantic import BaseModel

class AgentRole(str, Enum):
    """Agent roles in the fleet"""
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    CODER = "coder"
    REVIEWER = "reviewer"

class AgentCapability(str, Enum):
    """Capabilities that agents can have"""
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    FILE_IO = "file_io"
    DATABASE_QUERY = "database_query"
    API_CALL = "api_call"
    CALCULATION = "calculation"

class AgentConfig(BaseModel):
    """Configuration for an agent"""
    role: AgentRole
    name: str
    model: str
    capabilities: list[AgentCapability]
    max_concurrent: int = 3
    priority: int = 5  # 1-10, higher = more important

# Define agent configurations
AGENT_CONFIGS = [
    AgentConfig(
        role=AgentRole.ORCHESTRATOR,
        name="Fleet Commander",
        model="gpt-4",
        capabilities=[
            AgentCapability.WEB_SEARCH,
            AgentCapability.API_CALL,
        ],
        max_concurrent=10,
        priority=10,
    ),
    AgentConfig(
        role=AgentRole.RESEARCHER,
        name="Web Researcher",
        model="gpt-4o-mini",
        capabilities=[
            AgentCapability.WEB_SEARCH,
            AgentCapability.API_CALL,
        ],
        max_concurrent=5,
        priority=7,
    ),
    AgentConfig(
        role=AgentRole.ANALYST,
        name="Data Analyst",
        model="gpt-4",
        capabilities=[
            AgentCapability.CODE_EXECUTION,
            AgentCapability.CALCULATION,
            AgentCapability.DATABASE_QUERY,
        ],
        max_concurrent=3,
        priority=8,
    ),
    AgentConfig(
        role=AgentRole.WRITER,
        name="Content Writer",
        model="gpt-4o-mini",
        capabilities=[
            AgentCapability.FILE_IO,
            AgentCapability.API_CALL,
        ],
        max_concurrent=5,
        priority=6,
    ),
    AgentConfig(
        role=AgentRole.CODER,
        name="Code Generator",
        model="gpt-4",
        capabilities=[
            AgentCapability.CODE_EXECUTION,
            AgentCapability.FILE_IO,
            AgentCapability.WEB_SEARCH,
        ],
        max_concurrent=3,
        priority=7,
    ),
    AgentConfig(
        role=AgentRole.REVIEWER,
        name="Quality Reviewer",
        model="gpt-4",
        capabilities=[
            AgentCapability.FILE_IO,
            AgentCapability.API_CALL,
        ],
        max_concurrent=3,
        priority=5,
    ),
]
```

### Step 1.2: Create Base Agent Class

```python
# File: agents/base_agent.py
"""
Base agent class that all specialized agents inherit from
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime
import json

class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.role = config.role
        self.name = config.name
        self.capabilities = config.capabilities
        self.memory = []  # Short-term memory
        self.current_tasks = 0

    @abstractmethod
    def process(self, task: Dict) -> Dict:
        """
        Process a task

        Args:
            task: Task dictionary with:
                - task_id: Unique identifier
                - type: Task type
                - input: Task input data
                - context: Additional context

        Returns:
            Result dictionary with:
                - task_id: Same as input
                - status: "success" | "error" | "pending"
                - output: Task output
                - metadata: Additional metadata
        """
        pass

    def can_accept_task(self, task: Dict) -> bool:
        """Check if agent can accept a new task"""
        if self.current_tasks >= self.config.max_concurrent:
            return False
        return True

    def add_to_memory(self, item: Dict):
        """Add item to agent's memory"""
        item["timestamp"] = datetime.now().isoformat()
        self.memory.append(item)

        # Keep only last 100 items
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

    def get_memory(self, last_n: int = 10) -> list[Dict]:
        """Get recent memory items"""
        return self.memory[-last_n:]

    def create_response(self, status: str, output: Any, metadata: Dict | None = None) -> Dict:
        """Create a standardized response"""
        response = {
            "task_id": None,  # Will be set by process method
            "agent": self.name,
            "role": self.role,
            "status": status,
            "output": output,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        return response

# Test base agent
class MockAgent(BaseAgent):
    """Mock agent for testing"""

    def process(self, task: Dict) -> Dict:
        """Process a mock task"""
        task_id = task.get("task_id", "unknown")

        if not self.can_accept_task(task):
            return self.create_response("pending", "Agent at capacity")

        self.current_tasks += 1

        # Simulate processing
        result = self.create_response(
            status="success",
            output=f"Mock processed: {task.get('type', 'unknown')}",
            metadata={"mock": True}
        )

        result["task_id"] = task_id
        self.add_to_memory({"task": task, "result": result})

        self.current_tasks -= 1
        return result
```

---

## 🔧 Part 2: Implement Specialized Agents (120 min)

### Step 2.1: Researcher Agent

```python
# File: agents/researcher_agent.py
"""
Research agent that searches the web and gathers information
"""

from typing import Dict
import requests
from base_agent import BaseAgent, AgentConfig

class ResearcherAgent(BaseAgent):
    """Agent specialized in web research and information gathering"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.search_api_key = None  # Set via environment variable

    def process(self, task: Dict) -> Dict:
        """Process research task"""
        task_id = task.get("task_id", "unknown")
        task_type = task.get("type", "unknown")

        response = self.create_response("pending", None)
        response["task_id"] = task_id

        try:
            if task_type == "web_search":
                query = task["input"].get("query")
                num_results = task["input"].get("num_results", 5)

                results = self._web_search(query, num_results)
                output = {
                    "query": query,
                    "results": results,
                    "count": len(results),
                }

                response["status"] = "success"
                response["output"] = output

            elif task_type == "fact_check":
                claims = task["input"].get("claims", [])
                verified = self._fact_check(claims)

                response["status"] = "success"
                response["output"] = {"verified_claims": verified}

            else:
                response["status"] = "error"
                response["output"] = f"Unknown task type: {task_type}"

            # Add to memory
            self.add_to_memory({"task": task, "response": response})

        except Exception as e:
            response["status"] = "error"
            response["output"] = str(e)

        return response

    def _web_search(self, query: str, num_results: int = 5) -> list[Dict]:
        """Perform web search"""
        # In production, use real search API (Google, Bing, etc.)
        # For this lab, we'll use a mock implementation

        mock_results = [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/{i+1}",
                "snippet": f"This is a mock search result for: {query}",
            }
            for i in range(num_results)
        ]

        return mock_results

    def _fact_check(self, claims: list[str]) -> list[Dict]:
        """Fact check claims"""
        verified = []

        for claim in claims:
            # In production, use actual fact-checking
            verified.append({
                "claim": claim,
                "verdict": "likely_true",  # or "likely_false", "uncertain"
                "confidence": 0.8,
                "sources": [],
            })

        return verified

# Test researcher agent
if __name__ == "__main__":
    from agent_types import AgentConfig, AgentRole, AgentCapability

    config = AgentConfig(
        role=AgentRole.RESEARCHER,
        name="Web Researcher",
        model="gpt-4o-mini",
        capabilities=[AgentCapability.WEB_SEARCH, AgentCapability.API_CALL],
    )

    researcher = ResearcherAgent(config)

    # Test web search
    task = {
        "task_id": "test_001",
        "type": "web_search",
        "input": {
            "query": "What is machine learning?",
            "num_results": 3,
        },
    }

    result = researcher.process(task)
    print(f"Researcher result: {result}")
```

### Step 2.2: Analyst Agent

```python
# File: agents/analyst_agent.py
"""
Analyst agent that processes data and performs calculations
"""

from typing import Dict, List
import numpy as np
import pandas as pd
from base_agent import BaseAgent, AgentConfig

class AnalystAgent(BaseAgent):
    """Agent specialized in data analysis and calculations"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, task: Dict) -> Dict:
        """Process analysis task"""
        task_id = task.get("task_id", "unknown")
        task_type = task.get("type", "unknown")

        response = self.create_response("pending", None)
        response["task_id"] = task_id

        try:
            if task_type == "calculate":
                expression = task["input"].get("expression")

                # Safe calculation
                result = self._safe_calculate(expression)

                response["status"] = "success"
                response["output"] = {
                    "expression": expression,
                    "result": result,
                }

            elif task_type == "analyze_data":
                data = task["input"].get("data", [])
                analysis_type = task["input"].get("analysis_type", "summary")

                result = self._analyze_data(data, analysis_type)

                response["status"] = "success"
                response["output"] = result

            elif task_type == "compare":
                items = task["input"].get("items", [])
                comparison = self._compare_items(items)

                response["status"] = "success"
                response["output"] = comparison

            else:
                response["status"] = "error"
                response["output"] = f"Unknown task type: {task_type}"

            self.add_to_memory({"task": task, "response": response})

        except Exception as e:
            response["status"] = "error"
            response["output"] = str(e)

        return response

    def _safe_calculate(self, expression: str) -> float:
        """Safely calculate a mathematical expression"""
        # Allow only safe operations
        allowed_names = {
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "len": len,
            "pow": pow,
            "round": round,
            "sqrt": np.sqrt,
            "log": np.log,
            "exp": np.exp,
        }

        # Add numpy functions
        allowed_names.update({
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "pi": np.pi,
            "e": np.e,
        })

        try:
            # Use eval with restricted globals
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return float(result)
        except Exception as e:
            return 0.0

    def _analyze_data(self, data: List, analysis_type: str) -> Dict:
        """Analyze data"""
        if not data:
            return {"error": "No data provided"}

        df = pd.DataFrame(data)

        result = {"data_type": analysis_type}

        if analysis_type == "summary":
            result.update({
                "count": len(data),
                "numeric_summary": df.describe().to_dict() if not df.empty else {},
            })

        elif analysis_type == "statistics":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            result["statistics"] = {}
            for col in numeric_cols:
                result["statistics"][col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                }

        return result

    def _compare_items(self, items: list[Dict]) -> Dict:
        """Compare multiple items"""
        comparison = {
            "item_count": len(items),
            "comparisons": [],
        }

        # Compare each pair
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                item1 = items[i]
                item2 = items[j]

                comparison["comparisons"].append({
                    "item1": item1,
                    "item2": item2,
                    "difference": self._compute_difference(item1, item2),
                })

        return comparison

    def _compute_difference(self, item1: Dict, item2: Dict) -> Dict:
        """Compute difference between two items"""
        diff = {}

        all_keys = set(item1.keys()) | set(item2.keys())

        for key in all_keys:
            val1 = item1.get(key)
            val2 = item2.get(key)

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff[key] = {
                    "item1_value": val1,
                    "item2_value": val2,
                    "difference": val2 - val1,
                    "percent_change": ((val2 - val1) / val1 * 100) if val1 != 0 else 0,
                }
            else:
                diff[key] = {
                    "item1_value": str(val1),
                    "item2_value": str(val2),
                    "same": val1 == val2,
                }

        return diff
```

### Step 2.3: Writer Agent

```python
# File: agents/writer_agent.py
"""
Writer agent that generates content
"""

from typing import Dict
from base_agent import BaseAgent, AgentConfig

class WriterAgent(BaseAgent):
    """Agent specialized in content generation"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, task: Dict) -> Dict:
        """Process writing task"""
        task_id = task.get("task_id", "unknown")
        task_type = task.get("type", "unknown")

        response = self.create_response("pending", None)
        response["task_id"] = task_id

        try:
            if task_type == "write_summary":
                content = task["input"].get("content")
                style = task["input"].get("style", "neutral")

                summary = self._write_summary(content, style)

                response["status"] = "success"
                response["output"] = {
                    "summary": summary,
                    "original_length": len(content),
                    "summary_length": len(summary),
                }

            elif task_type == "write_report":
                sections = task["input"].get("sections", [])
                report_type = task["input"].get("report_type", "general")

                report = self._write_report(sections, report_type)

                response["status"] = "success"
                response["output"] = {
                    "report": report,
                    "sections": len(sections),
                }

            elif task_type == "format_content":
                content = task["input"].get("content")
                format_type = task["input"].get("format_type", "markdown")

                formatted = self._format_content(content, format_type)

                response["status"] = "success"
                response["output"] = {
                    "formatted": formatted,
                    "format_type": format_type,
                }

            else:
                response["status"] = "error"
                response["output"] = f"Unknown task type: {task_type}"

            self.add_to_memory({"task": task, "response": response})

        except Exception as e:
            response["status"] = "error"
            response["output"] = str(e)

        return response

    def _write_summary(self, content: str, style: str) -> str:
        """Write a summary of content"""
        # In production, use LLM to generate summary
        # For now, return a mock summary

        sentences = content.split('.')
        summary = '. '.join(sentences[:3]) + '.'

        return summary

    def _write_report(self, sections: list[Dict], report_type: str) -> str:
        """Write a report from sections"""
        report_lines = [
            f"# {report_type.upper()} REPORT",
            "",
            f"Generated on {self._get_timestamp()}",
            "",
        ]

        for i, section in enumerate(sections):
            report_lines.append(f"## {i+1}. {section.get('title', 'Section ' + str(i+1))}")
            report_lines.append("")
            report_lines.append(section.get('content', ''))
            report_lines.append("")

        return '\n'.join(report_lines)

    def _format_content(self, content: str, format_type: str) -> str:
        """Format content according to type"""
        if format_type == "markdown":
            # Convert to markdown (simplified)
            lines = content.split('\n')
            formatted = []

            for line in lines:
                if line.strip():
                    # Add markdown formatting
                    if len(line.strip()) < 50 and not line.strip().endswith('.'):
                        formatted.append(f"### {line.strip()}")
                    else:
                        formatted.append(line.strip())

            return '\n'.join(formatted)

        elif format_type == "bullet_points":
            lines = content.split('. ')
            formatted = ["\n"]

            for line in lines:
                if line.strip():
                    formatted.append(f"- {line.strip()}.")

            return '\n'.join(formatted)

        return content

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

---

## 🎯 Part 3: Orchestration System (90 min)

### Step 3.1: Create Orchestrator

```python
# File: agents/orchestrator.py
"""
Orchestrator that manages the agent fleet
"""

from typing import Dict
from collections import deque
import threading
import queue
from datetime import datetime

from base_agent import BaseAgent
from agent_types import AgentConfig, AgentRole

class Orchestrator(BaseAgent):
    """Orchestrator that manages the agent fleet"""

    def __init__(self, config: AgentConfig, agents: list[BaseAgent]):
        super().__init__(config)
        self.agents = {agent.role: agent for agent in agents}
        self.task_queue = queue.PriorityQueue()
        self.active_tasks = {}
        self.completed_tasks = []
        self.lock = threading.Lock()

    def process(self, task: Dict) -> Dict:
        """Process a task by orchestrating through agents"""
        task_id = task.get("task_id", "unknown")

        response = self.create_response("pending", None)
        response["task_id"] = task_id

        try:
            # Step 1: Parse task
            plan = self._create_plan(task)
            response["output"] = {"plan": plan}

            # Step 2: Execute plan
            results = self._execute_plan(plan)

            # Step 3: Synthesize results
            final_result = self._synthesize_results(results)

            response["status"] = "success"
            response["output"]["final_result"] = final_result
            response["output"]["steps"] = results

        except Exception as e:
            response["status"] = "error"
            response["output"] = str(e)

        return response

    def _create_plan(self, task: Dict) -> list[Dict]:
        """Create execution plan for task"""
        task_type = task.get("type", "unknown")
        task_id = task.get("task_id", "unknown")

        plan = []

        if task_type == "research_task":
            plan = [
                {"step": 1, "agent": AgentRole.RESEARCHER, "action": "web_search", "input": task["input"]},
                {"step": 2, "agent": AgentRole.ANALYST, "action": "analyze_data", "input": "research_results"},
            ]

        elif task_type == "content_creation":
            plan = [
                {"step": 1, "agent": AgentRole.RESEARCHER, "action": "web_search", "input": task["input"]},
                {"step": 2, "agent": AgentRole.WRITER, "action": "write_summary", "input": "research_data"},
                {"step": 3, "agent": AgentRole.REVIEWER, "action": "review_content", "input": "draft_content"},
            ]

        elif task_type == "analysis_task":
            plan = [
                {"step": 1, "agent": AgentRole.ANALYST, "action": "analyze_data", "input": task["input"]},
                {"step": 2, "agent": AgentRole.WRITER, "action": "write_report", "input": "analysis_results"},
            ]

        else:
            # Default plan
            plan = [
                {"step": 1, "agent": AgentRole.ANALYST, "action": "process", "input": task["input"]},
            ]

        self.add_to_memory({"task_id": task_id, "plan": plan})
        return plan

    def _execute_plan(self, plan: list[Dict]) -> list[Dict]:
        """Execute the plan through agents"""
        results = []

        for step in plan:
            agent_role = step["agent"]
            action = step["action"]
            step_input = step["input"]

            # Get agent
            agent = self.agents.get(agent_role)
            if not agent:
                results.append({
                    "step": step["step"],
                    "status": "error",
                    "error": f"Agent not found: {agent_role}",
                })
                continue

            # Create task for agent
            agent_task = {
                "task_id": f"{plan[0].get('task_id', 'unknown')}_step{step['step']}",
                "type": action,
                "input": step_input,
                "context": {"plan": plan},
            }

            # Process with agent
            step_result = agent.process(agent_task)
            results.append({
                "step": step["step"],
                "agent": agent_role,
                "action": action,
                "result": step_result,
            })

        return results

    def _synthesize_results(self, results: list[Dict]) -> Dict:
        """Synthesize results from all agents"""
        synthesis = {
            "total_steps": len(results),
            "successful_steps": sum(1 for r in results if r.get("result", {}).get("status") == "success"),
            "failed_steps": sum(1 for r in results if r.get("result", {}).get("status") == "error"),
            "outputs": [r.get("result", {}).get("output") for r in results],
        }

        return synthesis
```

### Step 3.2: Create Agent Fleet

```python
# File: agents/fleet.py
"""
Complete agent fleet with all specialized agents
"""

from typing import Dict, List
from agent_types import AgentConfig, AgentRole, AgentCapability
from base_agent import BaseAgent
from researcher_agent import ResearcherAgent
from analyst_agent import AnalystAgent
from writer_agent import WriterAgent
from orchestrator import Orchestrator

class AgentFleet:
    """Complete fleet of specialized agents"""

    def __init__(self):
        self.agents = {}
        self.orchestrator = None
        self.initialize_fleet()

    def initialize_fleet(self):
        """Initialize all agents in the fleet"""
        # Create agent configs
        configs = {
            AgentRole.ORCHESTRATOR: AgentConfig(
                role=AgentRole.ORCHESTRATOR,
                name="Fleet Commander",
                model="gpt-4",
                capabilities=[],
                max_concurrent=10,
            ),
            AgentRole.RESEARCHER: AgentConfig(
                role=AgentRole.RESEARCHER,
                name="Web Researcher",
                model="gpt-4o-mini",
                capabilities=[
                    AgentCapability.WEB_SEARCH,
                    AgentCapability.API_CALL,
                ],
                max_concurrent=5,
            ),
            AgentRole.ANALYST: AgentConfig(
                role=AgentRole.ANALYST,
                name="Data Analyst",
                model="gpt-4",
                capabilities=[
                    AgentCapability.CODE_EXECUTION,
                    AgentCapability.CALCULATION,
                ],
                max_concurrent=3,
            ),
            AgentRole.WRITER: AgentConfig(
                role=AgentRole.WRITER,
                name="Content Writer",
                model="gpt-4o-mini",
                capabilities=[
                    AgentCapability.FILE_IO,
                    AgentCapability.API_CALL,
                ],
                max_concurrent=5,
            ),
        }

        # Create agents
        self.agents[AgentRole.RESEARCHER] = ResearcherAgent(configs[AgentRole.RESEARCHER])
        self.agents[AgentRole.ANALYST] = AnalystAgent(configs[AgentRole.ANALYST])
        self.agents[AgentRole.WRITER] = WriterAgent(configs[AgentRole.WRITER])

        # Create orchestrator
        self.orchestrator = Orchestrator(configs[AgentRole.ORCHESTRATOR], list(self.agents.values()))

        print(f"Initialized {len(self.agents)} agents:")
        for role, agent in self.agents.items():
            print(f"  - {role}: {agent.name}")

    def process_task(self, task: Dict) -> Dict:
        """Process a task through the fleet"""
        task_id = task.get("task_id", "unknown")

        # Route to orchestrator
        result = self.orchestrator.process(task)

        # Store completed task
        if result["status"] == "success":
            self.orchestrator.completed_tasks.append({
                "task_id": task_id,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            })

        return result

    def get_status(self) -> Dict:
        """Get fleet status"""
        return {
            "total_agents": len(self.agents),
            "agents": {
                role.value: {
                    "name": agent.name,
                    "current_tasks": agent.current_tasks,
                    "max_concurrent": agent.config.max_concurrent,
                }
                for role, agent in self.agents.items()
            },
            "completed_tasks": len(self.orchestrator.completed_tasks),
        }

# Test agent fleet
if __name__ == "__main__":
    fleet = AgentFleet()

    # Test task
    task = {
        "task_id": "test_001",
        "type": "research_task",
        "input": {
            "query": "What is machine learning?",
            "num_results": 3,
        },
    }

    result = fleet.process_task(task)

    print(f"\nTask Result:")
    print(f"Status: {result['status']}")
    print(f"Output: {result.get('output', {})}")

    print(f"\nFleet Status:")
    status = fleet.get_status()
    for role, info in status["agents"].items():
        print(f"  {role}: {info['name']} ({info['current_tasks']}/{info['max_concurrent']} active)")
```

---

## 🧠 Part 4: Add Memory System (60 min)

### Step 4.1: Shared Memory Store

```python
# File: agents/memory.py
"""
Shared memory store for all agents
"""

from typing import Dict
from datetime import datetime, timedelta
import json

class MemoryStore:
    """Shared memory store for agent fleet"""

    def __init__(self, max_items: int = 10000):
        self.memories = {}
        self.max_items = max_items
        self.index = 0

    def store(
        self,
        agent_id: str,
        task_id: str,
        memory_type: str,
        content: Dict,
        ttl_hours: int | None = None,
    ) -> str:
        """Store a memory"""
        memory_id = f"mem_{self.index}"

        memory = {
            "memory_id": memory_id,
            "agent_id": agent_id,
            "task_id": task_id,
            "type": memory_type,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=ttl_hours)).isoformat() if ttl_hours else None,
        }

        self.memories[memory_id] = memory
        self.index += 1

        # Cleanup old memories
        self._cleanup()

        return memory_id

    def retrieve(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        memory_type: str | None = None,
        limit: int = 10,
    ) -> list[Dict]:
        """Retrieve memories based on filters"""
        memories = list(self.memories.values())

        # Apply filters
        if agent_id:
            memories = [m for m in memories if m["agent_id"] == agent_id]

        if task_id:
            memories = [m for m in memories if m["task_id"] == task_id]

        if memory_type:
            memories = [m for m in memories if m["type"] == memory_type]

        # Filter expired
        now = datetime.now()
        memories = [
            m for m in memories
            if m["expires_at"] is None or datetime.fromisoformat(m["expires_at"]) > now
        ]

        # Sort by created time (newest first)
        memories.sort(key=lambda x: x["created_at"], reverse=True)

        return memories[:limit]

    def search(self, query: str, limit: int = 10) -> list[Dict]:
        """Search memories by content"""
        query_lower = query.lower()

        matching = []
        for memory in self.memories.values():
            content_str = json.dumps(memory["content"]).lower()
            if query_lower in content_str:
                matching.append(memory)

        matching.sort(key=lambda x: x["created_at"], reverse=True)
        return matching[:limit]

    def _cleanup(self):
        """Remove expired or old memories"""
        now = datetime.now()

        # Remove expired
        to_remove = [
            mem_id for mem_id, mem in self.memories.items()
            if mem["expires_at"] and datetime.fromisoformat(mem["expires_at"]) < now
        ]

        # Remove oldest if over limit
        if len(self.memories) - len(to_remove) > self.max_items:
            all_memories = sorted(
                self.memories.items(),
                key=lambda x: x[1]["created_at"]
            )
            excess = len(self.memories) - self.max_items
            to_remove.extend([m[0] for m in all_memories[:excess]])

        for mem_id in to_remove:
            del self.memories[mem_id]
```

### Step 4.2: Integrate Memory with Agents

```python
# File: agents/memory_agent.py
"""
Base agent with memory support
"""

from memory import MemoryStore
from typing import Dict

class MemoryEnabledAgent(BaseAgent):
    """Agent with memory capabilities"""

    def __init__(self, config: AgentConfig, memory_store: MemoryStore):
        super().__init__(config)
        self.memory_store = memory_store
        self.agent_id = config.name

    def remember(self, task_id: str, memory_type: str, content: Dict):
        """Store a memory"""
        return self.memory_store.store(
            agent_id=self.agent_id,
            task_id=task_id,
            memory_type=memory_type,
            content=content,
            ttl_hours=24,  # Default TTL
        )

    def recall(self, task_id: str, memory_type: str | None = None) -> list[Dict]:
        """Recall memories from a task"""
        return self.memory_store.retrieve(
            agent_id=self.agent_id,
            task_id=task_id,
            memory_type=memory_type,
        )

    def search_memory(self, query: str) -> list[Dict]:
        """Search all memories"""
        return self.memory_store.search(query)
```

---

## ✅ Completion Checklist

Use this checklist to track your progress:

### Design
- [ ] Agent roles defined
- [ ] Agent capabilities specified
- [ ] Configuration complete

### Implementation
- [ ] Base agent class created
- [ ] Researcher agent implemented
- [ ] Analyst agent implemented
- [ ] Writer agent implemented
- [ ] Orchestrator implemented

### Memory System
- [ ] Memory store created
- [ ] Agents integrated with memory
- [ ] Memory retrieval working

### Fleet
- [ ] Agent fleet initialized
- [ ] Task routing working
- [ ] Multi-step tasks working

### Testing
- [ ] Individual agents tested
- [ ] Orchestration tested
- [ ] Memory system tested
- [ ] End-to-end task completed

---

## 🚀 Next Steps

After completing this lab:

1. **LAB-009: Production Deployment** - Deploy agent fleet to production
2. **7401-Long-term-Memory.md** - Advanced memory systems
3. **7202-Code-Interpreter.md** - Secure code execution

---

**Lab Status:** ✅ Complete
**Maintainer:** PROJECT-OMEGA Team
