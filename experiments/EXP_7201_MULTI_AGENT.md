# EXP-7201: Multi-Agent Systems

**Orchestrating multiple AI agents for complex tasks**

---

## 🎯 Experiment Overview

**Time:** 75-90 minutes
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:**
- 7101: ReAct Loop System
- 7201: AutoGen vs LangGraph
- EXP_7101: ReAct Agent

**Learning Objectives:**
- Understand multi-agent architectures
- Implement agent communication
- Orchestrate collaborative problem solving
- Benchmark single vs multi-agent

---

## 📚 Background

Multi-agent systems use multiple specialized agents working together on complex tasks.

### Architecture Patterns

1. **Sequential** - Agents work one after another
2. **Parallel** - Agents work simultaneously
3. **Hierarchical** - Manager agent coordinates workers
4. **Debate** - Agents discuss and vote

---

## 🔬 Experiment 1: Multi-Agent Framework (30 minutes)

### Step 1.1: Base Multi-Agent System

```python
# File: multi_agent.py
"""
Multi-Agent Framework
=====================
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import asyncio

class AgentRole(Enum):
    """Agent roles"""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    REVIEWER = "reviewer"

class Agent:
    """Base agent class"""

    def __init__(self, name: str, role: AgentRole, expertise: str):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.message_queue = []

    def receive_message(self, message: Dict[str, Any]):
        """Receive message from another agent"""
        self.message_queue.append(message)

    def process_messages(self) -> List[Dict[str, Any]]:
        """Process pending messages"""
        responses = []

        for message in self.message_queue:
            response = self._handle_message(message)
            if response:
                responses.append(response)

        self.message_queue = []
        return responses

    def _handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming message"""
        msg_type = message.get("type")

        if msg_type == "task":
            return self._perform_task(message["content"])
        elif msg_type == "query":
            return self._answer_query(message["content"])
        elif msg_type == "result":
            return self._process_result(message["content"])

        return None

    def _perform_task(self, task: str) -> Dict[str, Any]:
        """Perform assigned task"""
        return {
            "type": "result",
            "from": self.name,
            "content": f"Task '{task}' completed by {self.name}"
        }

    def _answer_query(self, query: str) -> Dict[str, Any]:
        """Answer query from another agent"""
        return {
            "type": "response",
            "from": self.name,
            "content": f"Answer from {self.name}: {query}"
        }

    def _process_result(self, result: str) -> Dict[str, Any]:
        """Process result from another agent"""
        return {
            "type": "acknowledgment",
            "from": self.name,
            "content": f"{self.name} received result: {result}"
        }

class MultiAgentOrchestrator:
    """Orchestrate multiple agents"""

    def __init__(self):
        self.agents = []
        self.task_queue = []
        self.completed_tasks = []

    def add_agent(self, agent: Agent):
        """Add agent to system"""
        self.agents.append(agent)

    def assign_task(self, task: str, role: Optional[AgentRole] = None):
        """Assign task to appropriate agent"""

        if role:
            # Find agent with role
            agents = [a for a in self.agents if a.role == role]
            if agents:
                agent = agents[0]
            else:
                agent = self.agents[0]  # Fallback
        else:
            # Find best agent for task
            agent = self._find_best_agent(task)

        message = {
            "type": "task",
            "from": "orchestrator",
            "to": agent.name,
            "content": task
        }

        agent.receive_message(message)
        return agent

    def _find_best_agent(self, task: str) -> Agent:
        """Find best agent for task"""

        # Simple keyword matching
        task_lower = task.lower()

        for agent in self.agents:
            expertise_lower = agent.expertise.lower()
            if any(word in expertise_lower for word in task_lower.split()):
                return agent

        # Default to first agent
        return self.agents[0]

    def run_round(self) -> List[Dict]:
        """Run one round of agent communication"""

        all_responses = []

        # Process messages for each agent
        for agent in self.agents:
            responses = agent.process_messages()
            all_responses.extend(responses)

        # Route responses to appropriate agents
        for response in all_responses:
            to_agent = response.get("to")
            if to_agent:
                # Find agent
                target_agent = next((a for a in self.agents if a.name == to_agent), None)
                if target_agent:
                    target_agent.receive_message(response)

        return all_responses

    def execute_task(self, task: str, max_rounds: int = 5) -> Dict[str, Any]:
        """Execute complex task using multiple agents"""

        self.task_queue.append(task)

        for round_num in range(max_rounds):
            print(f"\n=== Round {round_num + 1} ===")

            # Assign subtasks
            agent = self.assign_task(task)

            # Run communication round
            responses = self.run_round()

            # Check if task complete
            if self._is_task_complete(responses):
                break

        return {
            "task": task,
            "rounds": round_num + 1,
            "responses": responses
        }

    def _is_task_complete(self, responses: List[Dict]) -> bool:
        """Check if task is complete"""

        # Check for completion signals
        for response in responses:
            if response.get("type") == "result" and "completed" in response.get("content", ""):
                return True

        return False

# Create agents
orchestrator = MultiAgentOrchestrator()

orchestrator.add_agent(Agent("Alice", AgentRole.RESEARCHER, "information gathering and web search"))
orchestrator.add_agent(Agent("Bob", AgentRole.CODER, "programming and code execution"))
orchestrator.add_agent(Agent("Charlie", AgentRole.ANALYST, "data analysis and calculation"))

# Execute task
task = "Research quantum computing and calculate the number of qubits in IBM's latest processor"
result = orchestrator.execute_task(task)

print(f"\n=== Task Execution ===")
print(f"Task: {result['task']}")
print(f"Rounds: {result['rounds']}")
print(f"Responses: {len(result['responses'])}")
```

**Checkpoint 1:** ✅ Multi-agent framework working

---

## 🔬 Experiment 2: Specialized Agents (25 minutes)

### Step 2.1: Domain-Specific Agents

```python
# File: specialized_agents.py
"""
Specialized Multi-Agent System
==============================
"""

class ResearcherAgent(Agent):
    """Agent specialized in information gathering"""

    def _perform_task(self, task: str) -> Dict[str, Any]:
        """Perform research task"""

        # Simulate web search
        search_results = [
            f"Found article about '{task}'",
            f"Retrieved paper on '{task[:20]}...'",
            f"Gathered statistics for '{task[:20]}...'"
        ]

        return {
            "type": "result",
            "from": self.name,
            "content": search_results,
            "metadata": {"confidence": 0.85}
        }

class CoderAgent(Agent):
    """Agent specialized in programming"""

    def _perform_task(self, task: str) -> Dict[str, Any]:
        """Perform coding task"""

        # Simulate code generation
        code = f"""
# Generated code for: {task}
def solution():
    result = perform_calculation()
    return analyze(result)
"""
        return {
            "type": "result",
            "from": self.name,
            "content": code,
            "metadata": {"language": "python"}
        }

class AnalystAgent(Agent):
    """Agent specialized in analysis"""

    def _perform_task(self, task: str) -> Dict[str, Any]:
        """Perform analysis task"""

        # Simulate data analysis
        analysis = f"""
Analysis Results for: {task}
- Mean: 42.5
- Median: 38.2
- Standard deviation: 5.8
- Trend: Increasing
"""
        return {
            "type": "result",
            "from": self.name,
            "content": analysis,
            "metadata": {"confidence": 0.92}
        }

# Create specialized multi-agent system
class SpecialistOrchestrator(MultiAgentOrchestrator):
    """Orchestrator for specialized agents"""

    def execute_complex_task(self, task: str, max_rounds: int = 10):
        """Execute task requiring multiple specialists"""

        results = {"task": task, "phases": []}

        # Phase 1: Research
        print("\n--- Phase 1: Research ---")
        researcher = next(a for a in self.agents if isinstance(a, ResearcherAgent))
        researcher.receive_message({
            "type": "task",
            "content": f"Research: {task}"
        })

        research_response = researcher.process_messages()[0]
        results["phases"].append({
            "phase": "research",
            "agent": researcher.name,
            "result": research_response["content"]
        })

        # Phase 2: Analysis
        print("\n--- Phase 2: Analysis ---")
        analyst = next(a for a in self.agents if isinstance(a, AnalystAgent))
        analyst.receive_message({
            "type": "task",
            "content": f"Analyze: {task}"
        })

        analysis_response = analyst.process_messages()[0]
        results["phases"].append({
            "phase": "analysis",
            "agent": analyst.name,
            "result": analysis_response["content"]
        })

        # Phase 3: Implementation (if needed)
        if "code" in task.lower() or "implement" in task.lower():
            print("\n--- Phase 3: Implementation ---")
            coder = next(a for a in self.agents if isinstance(a, CoderAgent))
            coder.receive_message({
                "type": "task",
                "content": f"Implement: {task}"
            })

            code_response = coder.process_messages()[0]
            results["phases"].append({
                "phase": "coding",
                "agent": coder.name,
                "result": code_response["content"]
            })

        return results

# Create specialist system
specialist_orchestrator = SpecialistOrchestrator()

specialist_orchestrator.add_agent(ResearcherAgent("Alice", AgentRole.RESEARCHER, "research"))
specialist_orchestrator.add_agent(CoderAgent("Bob", AgentRole.CODER, "programming"))
specialist_orchestrator.add_agent(AnalystAgent("Charlie", AgentRole.ANALYST, "analysis"))

# Execute complex task
complex_task = "Research the current state of quantum computing and analyze the trends"
result = specialist_orchestrator.execute_complex_task(complex_task)

print(f"\n=== Specialist Results ===")
for phase in result["phases"]:
    print(f"\n{phase['phase'].upper()}:")
    print(f"  Agent: {phase['agent']}")
    print(f"  Result: {phase['result']}")
```

**Checkpoint 2:** ✅ Specialized agents working

---

## 🔬 Experiment 3: Agent Debate (20 minutes)

### Step 3.1: Implement Debate Pattern

```python
# File: agent_debate.py
"""
Agent Debate Pattern
===================
"""

class DebateAgent(Agent):
    """Agent that can debate with other agents"""

    def __init__(self, name: str, position: str):
        super().__init__(name, AgentRole.REVIEWER, position)
        self.position = position
        self.arguments = []

    def participate_in_debate(self, topic: str, round_num: int) -> Dict[str, Any]:
        """Participate in debate round"""

        # Generate argument based on position
        argument = self._generate_argument(topic, round_num)
        self.arguments.append(argument)

        return {
            "type": "argument",
            "from": self.name,
            "position": self.position,
            "content": argument,
            "round": round_num
        }

    def _generate_argument(self, topic: str, round_num: int) -> str:
        """Generate argument for position"""

        if self.position == "for":
            return f"Argument for '{topic}' (round {round_num}): This approach is beneficial because..."

        else:
            return f"Argument against '{topic}' (round {round_num}): This approach has limitations because..."

    def vote(self, all_arguments: List[Dict]) -> Dict[str, Any]:
        """Vote based on debate"""

        # Simulated voting based on argument quality
        if self.position == "for":
            confidence = 0.6 + round_num * 0.05
        else:
            confidence = 0.4 - round_num * 0.05

        return {
            "type": "vote",
            "from": self.name,
            "position": self.position,
            "confidence": confidence
        }

class DebateOrchestrator:
    """Orchestrate agent debates"""

    def __init__(self):
        self.agents_for = []
        self.agents_against = []

    def add_debater(self, agent: DebateAgent):
        """Add debater to appropriate side"""

        if agent.position == "for":
            self.agents_for.append(agent)
        else:
            self.agents_against.append(agent)

    def run_debate(self, topic: str, rounds: int = 3) -> Dict[str, Any]:
        """Run debate"""

        all_arguments = []

        for round_num in range(rounds):
            print(f"\n=== Debate Round {round_num + 1} ===")

            round_arguments = []

            # For side arguments
            for agent in self.agents_for:
                arg = agent.participate_in_debate(topic, round_num)
                round_arguments.append(arg)
                all_arguments.append(arg)

            # Against side arguments
            for agent in self.agents_against:
                arg = agent.participate_in_debate(topic, round_num)
                round_arguments.append(arg)
                all_arguments.append(arg)

        # Voting phase
        print(f"\n=== Voting Phase ===")

        votes_for = []
        votes_against = []

        for agent in self.agents_for + self.agents_against:
            vote = agent.vote(all_arguments)
            if vote["position"] == "for":
                votes_for.append(vote["confidence"])
            else:
                votes_against.append(vote["confidence"])

        # Determine winner
        avg_for = np.mean(votes_for) if votes_for else 0
        avg_against = np.mean(votes_against) if votes_against else 0

        winner = "for" if avg_for > avg_against else "against"

        return {
            "topic": topic,
            "rounds": rounds,
            "arguments": all_arguments,
            "winner": winner,
            "for_confidence": avg_for,
            "against_confidence": avg_against
        }

# Create debate
debate_orchestrator = DebateOrchestrator()

debate_orchestrator.add_debater(DebateAgent("Alice", "for"))
debate_orchestrator.add_debater(DebateAgent("Bob", "for"))
debate_orchestrator.add_debater(DebateAgent("Charlie", "against"))
debate_orchestrator.add_debater(DebateAgent("Diana", "against"))

# Run debate
debate_topic = "Should we use AI for code generation?"
debate_result = debate_orchestrator.run_debate(debate_topic, rounds=3)

print(f"\n=== Debate Results ===")
print(f"Topic: {debate_result['topic']}")
print(f"Rounds: {debate_result['rounds']}")
print(f"Winner: {debate_result['winner'].upper()}")
print(f"For confidence: {debate_result['for_confidence']:.2%}")
print(f"Against confidence: {debate_result['against_confidence']:.2%}")
```

**Checkpoint 3:** ✅ Agent debate working

---

## 📊 Results Summary

### Single vs Multi-Agent

| Aspect | Single Agent | Multi-Agent |
|--------|--------------|--------------|
| **Speed** | Faster | Slower (communication) |
| **Capability** | Limited | Specialized expertise |
| **Robustness** | Single point of failure | Redundancy |
| **Complex Tasks** | Struggles | Excels |
| **Cost** | Lower | Higher |

### Best Patterns for Different Tasks

| Task Type | Best Pattern |
|-----------|--------------|
| Simple queries | Single Agent |
| Complex problems | **Multi-Agent** |
| Peer review | Debate |
| Parallel subtasks | **Hierarchical** |
| Creative work | **Debate** |

---

## ✅ Experiment Checklist

- [ ] Multi-agent framework implemented
- [ ] Specialized agents working
- [ ] Debate pattern functional
- [ ] Communication tested

---

## 🎓 Key Takeaways

1. **Specialization matters** - Different agents excel at different tasks
2. **Communication overhead** - Trade-off speed for capability
3. **Coordination is key** - Orchestrator manages complexity
4. **Debate improves quality** - Multiple perspectives refine answers
5. **Scalability challenge** - More agents = more complexity

---

## 🚀 Next Steps

1. **LAB-008**: Agent Fleet - Scale to production
2. **PROJECT-007**: Production AI System - Complete implementation
3. **7202**: Planning Decomposition - Advanced orchestration

---

**Last Updated:** 2026-02-04
**Experiment:** 7201 - Multi-Agent Systems
**Time Estimate:** 75-90 minutes
**Difficulty:** ⭐⭐⭐ Advanced
