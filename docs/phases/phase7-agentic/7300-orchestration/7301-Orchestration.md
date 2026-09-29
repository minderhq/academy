---
Document ID: 7301
Title: "7301: Collaborative Tasking - Multi-Agent Synergy"
Phase: 7
Module: 7300
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'orchestration', 'multi-agent', 'autogen', 'langgraph']
---

# 7301: Collaborative Tasking - Multi-Agent Synergy

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Agent Specialization](#agent-specialization)
- [Task Decomposition with Specialists](#task-decomposition-with-specialists)
- [Agent Communication](#agent-communication)
- [Collaboration Patterns](#collaboration-patterns)
- [Conflict Resolution](#conflict-resolution)
- [Practical Implementation](#practical-implementation)
- [Related Documents](#related-documents)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare the six common specialist roles and select the subset a given workload actually needs, justifying each cut
- Decompose a task into an LLM-generated plan and parse it into validated specialist step records
- Implement structured message passing with sender/receiver/type metadata and loud unknown-receiver handling
- Contrast hierarchical and peer-to-peer orchestration and select the pattern that fits a task's coupling
- Resolve agent conflicts with LLM arbitration backed by deterministic majority voting and explicit tie-breaking
- Wire a bounded monitor → analyze → prioritize → route maintenance cycle with fail-loud issue routing

---

## Abstract
Collaborative multi-agent systems involve specialized agents working together on complex tasks, each contributing their expertise toward goals beyond individual capabilities. This lesson builds the orchestration mechanics — specialization, LLM-driven decomposition, structured messaging, hierarchical vs peer-to-peer coordination, and conflict resolution — in dependency-free Python you can run as you read. Production teams typically reach for the frameworks compared in [7303](./guides/7303-Framework-Comparison.md) (AutoGen, LangGraph, CrewAI); the mechanics here are what those frameworks do under the hood.

## Agent Specialization

### Common Agent Types
```text
Specialized Agent Roles:

1. Planner Agent
   - Breaks down tasks
   - Creates execution plans
   - Monitors progress

2. Coder Agent
   - Writes and modifies code
   - Debugs issues
   - Optimizes performance

3. Researcher Agent
   - Gathers information
   - Analyzes data
   - Synthesizes findings

4. Reviewer Agent
   - Reviews work quality
   - Identifies issues
   - Suggests improvements

5. Executor Agent
   - Executes commands
   - Runs scripts
   - Manages resources

6. Communicator Agent
   - Interfaces with users
   - Coordinates between agents
   - Summarizes results
```

### Agent Synergy
The swarm below keeps four of the six roles — the demo has no commands to execute and no user to report to, so `executor` and `communicator` are cut deliberately. Every specialist is a deterministic stand-in, but the plan → execute → review → retry → synthesize flow is the real contract:

```python
class SpecialistAgent:
    """Base specialist: executes a subtask, optionally honoring reviewer feedback."""
    role = "specialist"

    def execute(self, subtask: str, feedback: str = "") -> str:
        note = f" (after feedback: {feedback})" if feedback else ""
        return f"[{self.role}] done: {subtask}{note}"


class ResearcherAgent(SpecialistAgent):
    role = "research"


class CoderAgent(SpecialistAgent):
    role = "code"


class ReviewerAgent:
    """Stand-in reviewer: rejects the first review to exercise the retry path."""
    def __init__(self):
        self.calls = 0

    def review(self, result: str) -> dict:
        self.calls += 1
        if self.calls == 1:
            return {"approved": False, "feedback": "add error handling"}
        return {"approved": True, "feedback": ""}


class PlannerAgent:
    """Produces a fixed plan and synthesizes step results."""
    def plan(self, task: str) -> list:
        return [
            {"agent": "researcher", "task": f"Gather requirements for: {task}"},
            {"agent": "coder", "task": f"Implement: {task}"},
        ]

    def synthesize(self, results: list) -> str:
        return "Final report:\n" + "\n".join(f"- {r}" for r in results)


class AgentSwarm:
    """Swarm of specialized agents with a review-and-retry loop."""

    def __init__(self):
        self.agents = {
            "planner": PlannerAgent(),
            "coder": CoderAgent(),
            "researcher": ResearcherAgent(),
            "reviewer": ReviewerAgent(),
        }

    def collaborate(self, task: str) -> str:
        """Plan, execute each step with its specialist, review, then synthesize."""
        plan = self.agents["planner"].plan(task)

        results = []
        for step in plan:
            agent_type = step["agent"]
            if agent_type not in self.agents:
                raise ValueError(
                    f"unknown specialist {agent_type!r}; "
                    f"roster: {sorted(self.agents)}")

            subtask = step["task"]
            result = self.agents[agent_type].execute(subtask)

            review = self.agents["reviewer"].review(result)
            if not review["approved"]:
                result = self.agents[agent_type].execute(
                    subtask, review["feedback"])

            results.append(result)

        return self.agents["planner"].synthesize(results)


swarm = AgentSwarm()
print(swarm.collaborate("build an inference API"))
# Output: Final report:
# Output: - [research] done: Gather requirements for: build an inference API (after feedback: add error handling)
# Output: - [code] done: Implement: build an inference API


# The roster contract is fail-loud: a planner that assigns an unknown
# specialist stops the run instead of silently skipping the step.
class GhostPlanner(PlannerAgent):
    def plan(self, task: str) -> list:
        return [{"agent": "ghost", "task": task}]


swarm.agents["planner"] = GhostPlanner()
try:
    swarm.collaborate("anything")
except ValueError as e:
    print(e)
# Output: unknown specialist 'ghost'; roster: ['coder', 'planner', 'researcher', 'reviewer']
```

The first step needed one feedback round; the second passed review clean — the reviewer's `{"approved": bool, "feedback": str}` envelope is what makes the loop inspectable.

## Task Decomposition with Specialists

### Domain-Specific Planning
The planner's parsed `agent` field is a **roster key**: whatever executes the plan must share the specialist roster this prompt advertises, or the lookup fails. Here the roster is deployment-domain (GPU/K8s/storage/security):

```python
import re


class StubLLM:
    """Deterministic stand-in: returns a canned plan for any prompt."""
    def generate(self, prompt: str) -> str:
        return (
            "Step 1: Check GPU utilization and thermals (Agent: GPU)\n"
            "Step 2: Restart the stuck training pod (Agent: K8s)\n"
            "Step 3: Verify dataset mount permissions (Agent: Storage)\n"
            "Step 4: Harden the API key rotation policy (Agent: Security)\n"
        )


class DomainPlanner:
    """Plans task decomposition for domain-specific agents."""

    def __init__(self, llm):
        self.llm = llm

    def create_plan(self, task: str) -> list[dict]:
        """Create plan with agent assignments."""
        prompt = f"""
        Task: {task}

        Available Specialists:
        - K8s Agent: Kubernetes operations
        - GPU Agent: GPU monitoring and optimization
        - Storage Agent: NAS and file management
        - Network Agent: Network configuration
        - Security Agent: Security and permissions

        Create a step-by-step plan to accomplish this task.
        For each step, specify which agent should handle it.

        Format:
        Step 1: [description] (Agent: [specialist])
        Step 2: [description] (Agent: [specialist])

        Plan:"""

        response = self.llm.generate(prompt)
        return self._parse_plan(response)

    def _parse_plan(self, response: str) -> list[dict]:
        """Parse plan into steps with agent assignments."""
        steps = []

        for line in response.split("\n"):
            if not line.strip():
                continue

            # Expected: "Step N: description (Agent: specialist)"
            match = re.search(r"Step (\d+): (.+?) \(Agent: (\w+)\)", line)
            if match:
                step_num = int(match.group(1))
                description = match.group(2).strip()
                agent = match.group(3).strip().lower()

                steps.append({
                    "step": step_num,
                    "task": description,
                    "agent": agent,
                })

        return steps


planner = DomainPlanner(StubLLM())
for step in planner.create_plan("training job is stuck"):
    print(step)
# Output: {'step': 1, 'task': 'Check GPU utilization and thermals', 'agent': 'gpu'}
# Output: {'step': 2, 'task': 'Restart the stuck training pod', 'agent': 'k8s'}
# Output: {'step': 3, 'task': 'Verify dataset mount permissions', 'agent': 'storage'}
# Output: {'step': 4, 'task': 'Harden the API key rotation policy', 'agent': 'security'}
```

Lines that do not match the format (an LLM may add preamble or a trailing note) are skipped silently by the parser — count the returned steps against what you asked for before executing, and keep the roster small so the LLM cannot invent specialist names outside it.

## Agent Communication

### Message Passing
```python
import time


class AgentMessage:
    """Structured message passed between agents."""
    def __init__(self, sender: str, receiver: str, content: str, msg_type: str):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.msg_type = msg_type  # request, response, notification
        self.timestamp = time.time()


class LoggingAgent:
    """Test double: records every message it receives."""
    def __init__(self, name: str):
        self.name = name
        self.inbox = []

    def receive_message(self, message: AgentMessage):
        self.inbox.append(
            f"{message.sender}->{message.receiver}: {message.content}")


class Communicator:
    """Handles communication between agents."""

    def __init__(self):
        self.message_queue = []
        self.agents = {}

    def register_agent(self, name: str, agent):
        """Register agent."""
        self.agents[name] = agent

    def send_message(self, message: AgentMessage):
        """Send message to a named agent; unknown receivers fail loud."""
        receiver = self.agents.get(message.receiver)

        if receiver:
            receiver.receive_message(message)
        else:
            print(f"Error: Unknown agent {message.receiver}")

    def broadcast(self, sender: str, content: str, msg_type: str):
        """Send message to all agents except the sender."""
        for agent_name in self.agents:
            if agent_name != sender:
                message = AgentMessage(sender, agent_name, content, msg_type)
                self.send_message(message)


comms = Communicator()
for name in ("planner", "coder", "reviewer"):
    comms.register_agent(name, LoggingAgent(name))

comms.send_message(AgentMessage("system", "coder", "new task assigned", "request"))
comms.broadcast("system", "status sync at t=0", "notification")
comms.send_message(AgentMessage("system", "ghost", "lost message", "request"))

print(comms.agents["coder"].inbox)
print(comms.agents["planner"].inbox)
# Output: Error: Unknown agent ghost
# Output: ['system->coder: new task assigned', 'system->coder: status sync at t=0']
# Output: ['system->planner: status sync at t=0']
```

The coder received a direct request plus the broadcast; the planner only the broadcast. The unknown receiver prints an error instead of raising — acceptable for a demo, but in production make `send_message` raise so a typo'd agent name cannot swallow messages mid-run.

## Collaboration Patterns

### Hierarchical Collaboration
The coordinator routes whole tasks to team leaders; each leader runs its own specialists. In production these roles wrap an LLM — here they are canned so the flow stays deterministic:

```python
class CoordinatorAgent:
    """Top-level router: assigns whole tasks to team leaders."""
    def assign_teams(self, task: str) -> dict:
        return {
            "infrastructure": "size the GPU node pool",
            "application": "roll out the API service",
            "data": "mount the shared dataset",
        }

    def synthesize(self, results: dict) -> str:
        return " | ".join(f"{team}: {res}" for team, res in sorted(results.items()))


class TeamLeader:
    """Middle manager: runs its specialists and reports up."""
    tag = "team"
    outcome = "done"

    def coordinate(self, subtask: str) -> str:
        return f"[{self.tag}] {subtask}: {self.outcome}"


class InfraTeamLeader(TeamLeader):
    tag, outcome = "infra", "node pool resized"


class AppTeamLeader(TeamLeader):
    tag, outcome = "app", "rollout complete"


class DataTeamLeader(TeamLeader):
    tag, outcome = "data", "dataset mounted"


class HierarchicalSwarm:
    """Hierarchical agent organization.

    Coordinator
    +-- Team A Leader
    |   +-- Specialist A1
    |   +-- Specialist A2
    +-- Team B Leader
        +-- Specialist B1
        +-- Specialist B2
    """

    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.team_leaders = {
            "infrastructure": InfraTeamLeader(),
            "application": AppTeamLeader(),
            "data": DataTeamLeader(),
        }

    def execute(self, task: str) -> str:
        """Execute task with hierarchical coordination."""
        team_assignments = self.coordinator.assign_teams(task)

        results = {}
        for team, subtask in team_assignments.items():
            leader = self.team_leaders.get(team)
            if leader is None:
                raise ValueError(
                    f"unknown team {team!r}; teams: {sorted(self.team_leaders)}")
            results[team] = leader.coordinate(subtask)

        return self.coordinator.synthesize(results)


swarm = HierarchicalSwarm()
print(swarm.execute("deploy a fault-tolerant inference stack"))
# Output: application: [app] roll out the API service: rollout complete | data: [data] mount the shared dataset: dataset mounted | infrastructure: [infra] size the GPU node pool: node pool resized
```

Use hierarchy when work decomposes along team boundaries and you want one accountable owner per domain; the cost is that the coordinator is a routing bottleneck and a single point of failure.

### Peer-to-Peer Collaboration
No coordinator: agents bid on subtasks and first-come-first-served negotiation assigns them. The negotiation must handle **overlapping bids** — two specialists claiming the same work — explicitly, or the losing bid vanishes silently:

```python


class BiddingAgent:
    """Self-organizing agent: proposes the subtask it is best at."""

    def __init__(self, name: str, claim: str):
        self.name = name
        self.claim = claim
        self.capability = name  # demo agents are their own capability
        self.inbox = []

    def propose_subtask(self, task: str):
        return self.claim

    def execute(self, subtask: str) -> str:
        return f"done by {self.capability}: {subtask}"

    def receive_message(self, message):
        self.inbox.append(message.content)


class PeerSwarm:
    """Peer-to-peer agent collaboration: agents negotiate directly."""

    def __init__(self, agents: dict[str, BiddingAgent]):
        self.agents = agents
        self.communicator = Communicator()
        for name, agent in agents.items():
            self.communicator.register_agent(name, agent)

    def collaborate(self, task: str) -> str:
        """Agents self-organize to complete the task."""
        # 1. Announce the task to all agents
        self.communicator.broadcast(
            "system", f"New task: {task}", "task_announcement")

        # 2. Agents bid on subtasks
        bids = []
        for name, agent in self.agents.items():
            bid = agent.propose_subtask(task)
            if bid:
                bids.append({"agent": name, "subtask": bid})

        # 3. Negotiate and assign
        assignments = self._negotiate_assignments(bids)

        # 4. Execute assigned work
        results = {}
        for agent_name, assignment in assignments.items():
            agent = self.agents[agent_name]
            results[agent_name] = agent.execute(assignment["subtask"])

        # 5. Integrate results
        return self._integrate_results(results)

    def _negotiate_assignments(self, bids: list[dict]) -> dict:
        """First-come, first-served: a later bid for already-claimed work
        is dropped with a warning instead of overwriting the assignment."""
        assignments: dict[str, dict] = {}
        dropped = []

        for bid in bids:
            agent, subtask = bid["agent"], bid["subtask"]
            if subtask in [a["subtask"] for a in assignments.values()]:
                dropped.append((agent, subtask))
            else:
                assignments[agent] = {"subtask": subtask}

        if dropped:
            print(f"dropped duplicate bids: {dropped}")

        return assignments

    def _integrate_results(self, results: dict[str, str]) -> str:
        return " ; ".join(f"{agent}: {res}" for agent, res in results.items())


swarm = PeerSwarm({
    "gpu": BiddingAgent("gpu", "optimize data transfer"),
    "net": BiddingAgent("net", "optimize data transfer"),
    "storage": BiddingAgent("storage", "verify dataset mount"),
})
print(swarm.collaborate("speed up the training pipeline"))
# Output: dropped duplicate bids: [('net', 'optimize data transfer')]
# Output: gpu: done by gpu: optimize data transfer ; storage: done by storage: verify dataset mount
```

The `net` agent bid on the same transfer work as `gpu` and lost the race — FCFS is the simplest rule, but a real swarm would score bids (capability match, current load) rather than take insertion order. A dropped agent contributes nothing this round; decide whether that is acceptable or the subtask should be split.

## Conflict Resolution

### Handling Disagreements
Two mechanisms, one policy: LLM arbitration for judgment calls, majority voting as the deterministic fallback. Note the voting contract — agents vote on **proposal keys**, and an unknown choice fails loud:

```python
import re


class StubLLM:
    def generate(self, prompt: str) -> str:
        return "Resolution: choose A."


class ConflictResolver:
    """Resolve conflicts between agents."""

    def __init__(self, llm):
        self.llm = llm

    def resolve(self, conflict: dict) -> dict:
        """Arbitrate a conflict via LLM.

        Conflict format:
        {
            "agents": ["agent_a", "agent_b"],
            "issue": "description of disagreement",
            "proposals": {
                "agent_a": "proposal A",
                "agent_b": "proposal B"
            }
        }
        """
        prompt = f"""
        Conflict between agents:
        {conflict['agents']}

        Issue: {conflict['issue']}

        Proposals:
        Agent A: {conflict['proposals']['agent_a']}
        Agent B: {conflict['proposals']['agent_b']}

        Resolve this conflict by:
        1. Evaluating each proposal
        2. Choosing the better option OR creating a compromise
        3. Explaining the reasoning

        Resolution:"""

        response = self.llm.generate(prompt)

        return {
            "resolution": response,
            "chosen_proposal": self._extract_chosen(response),
        }

    def _extract_chosen(self, response: str):
        """Pull the winning key out of an '... choose KEY.' verdict."""
        m = re.search(r"choose\s+(\w+)", response, re.IGNORECASE)
        return m.group(1) if m else None

    def voting(self, proposals: dict[str, str], voters: list) -> str:
        """Deterministic fallback: majority vote over proposal keys.

        Ties go to the first key in proposals insertion order — documented,
        not random. An unknown choice raises instead of counting as a vote.
        """
        votes = {key: 0 for key in proposals}

        for voter in voters:
            choice = voter.vote(proposals)
            if choice not in votes:
                raise ValueError(
                    f"voter {voter!r} chose unknown proposal {choice!r}")
            votes[choice] += 1

        return max(votes, key=votes.get)


resolver = ConflictResolver(StubLLM())

verdict = resolver.resolve({
    "agents": ["migrator", "auditor"],
    "issue": "schema migration strategy",
    "proposals": {
        "agent_a": "backup then migrate",
        "agent_b": "drop and recreate",
    },
})
print(verdict["resolution"])
# Output: Resolution: choose A.
print(verdict["chosen_proposal"])
# Output: A


class Voter:
    def __init__(self, choice: str):
        self.choice = choice

    def vote(self, proposals: dict[str, str]) -> str:
        return self.choice


winner = resolver.voting(
    {"agent_a": "backup then migrate", "agent_b": "drop and recreate"},
    [Voter("agent_a"), Voter("agent_b"), Voter("agent_a")],
)
print(f"majority: {winner}")
# Output: majority: agent_a
```

Voting counts keys (`agent_a`), never proposal text — a voter returning free text is a contract bug this design rejects at the vote site. Use arbitration when the conflict needs judgment; use voting when you need an auditable, replayable decision.

## Practical Implementation

### Local Multi-Agent System
The maintenance loop is **bounded** (`max_cycles`) so demos and tests terminate; production runs `maintain_system()` with the default `max_cycles=0`, which loops forever. Unknown issue types fail loud — a new analyzer rule without a route stops the cycle instead of being dropped:

```python
import time


class MonitoringAgent:
    def check_status(self) -> dict:
        return {"gpu_util": 0.97, "disk_free_gb": 4.2, "failed_auths": 12}


class AnalyzerAgent:
    def analyze(self, status: dict) -> list:
        issues = []
        if status["gpu_util"] > 0.90:
            issues.append(
                {"type": "performance", "detail": "GPU saturated", "severity": 7})
        if status["disk_free_gb"] < 10:
            issues.append(
                {"type": "deployment", "detail": "log volume nearly full",
                 "severity": 9})
        if status["failed_auths"] > 5:
            issues.append(
                {"type": "security", "detail": "auth failures spiking",
                 "severity": 8})
        return issues


class ResponderAgent:
    label = "responder"

    def handle(self, issue: dict) -> str:
        return f"[{self.label}] handled {issue['detail']}"


class OptimizationAgent(ResponderAgent):
    label = "optimizer"


class SecurityAgent(ResponderAgent):
    label = "security"


class DeploymentAgent(ResponderAgent):
    label = "deployer"


class LabSwarm:
    """Multi-agent maintenance loop for a homelab."""

    ROUTERS = {
        "performance": "optimizer",
        "security": "security",
        "deployment": "deployer",
    }

    def __init__(self):
        self.agents = {
            "monitor": MonitoringAgent(),
            "analyzer": AnalyzerAgent(),
            "optimizer": OptimizationAgent(),
            "security": SecurityAgent(),
            "deployer": DeploymentAgent(),
        }

    def run_cycle(self) -> list[str]:
        """One monitor -> analyze -> prioritize -> route pass."""
        status = self.agents["monitor"].check_status()
        issues = self.agents["analyzer"].analyze(status)

        actions = []
        for issue in self._prioritize(issues):
            route = self.ROUTERS.get(issue["type"])
            if route is None:
                raise ValueError(f"no agent routes issue type {issue['type']!r}")
            actions.append(self.agents[route].handle(issue))
        return actions

    def maintain_system(self, max_cycles: int = 0, interval_s: int = 300):
        """Continuous maintenance. max_cycles=0 (default) runs forever;
        pass a positive cap for demos and tests."""
        cycles = 0
        while True:
            for action in self.run_cycle():
                print(action)
            cycles += 1
            if max_cycles and cycles >= max_cycles:
                break
            time.sleep(interval_s)

    def _prioritize(self, issues: list[dict]) -> list[dict]:
        return sorted(issues, key=lambda x: x["severity"], reverse=True)


swarm = LabSwarm()
swarm.maintain_system(max_cycles=1)  # one full cycle for the demo
# Output: [deployer] handled log volume nearly full
# Output: [security] handled auth failures spiking
# Output: [optimizer] handled GPU saturated
```

Highest severity first: the disk issue (9) outranks the auth spike (8) and GPU saturation (7). Severity numbers come from the analyzer's rules — tune thresholds to your hardware, and keep the routing table (`ROUTERS`) next to the responder roster so a new issue type cannot ship without an owner.

---

## Related Documents

- [7302: Multi-Agent Communication Protocols](7302-Communication-Protocols.md)
- [7303: Multi-Agent Framework Comparison](./guides/7303-Framework-Comparison.md)
- [7102: Planning and Task Decomposition](../7100-architecture/7102-Planning-Decomposition.md)
- [7202: Code Interpreter - Sandbox Execution for Agent Code Testing](../7200-tools/guides/7202-Code-Interpreter.md)

**Experiment Template:** [EXP_7301: Collaboration](../../../../experiments/EXP_7301_COLLABORATION.md)

---

## Next Steps

- Continue with: **[7401: Long-term Memory for Agents](./../7400-memory/7401-Long-term-Memory.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
