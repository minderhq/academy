---
Document ID: 7102
Title: "7102: Planning and Task Decomposition"
Phase: 7
Module: 7100
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'react', 'planning', 'autonomy', 'cognition']
---

# 7102: Planning and Task Decomposition

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Task Decomposition](#task-decomposition)
- [Planning Algorithms](#planning-algorithms)
- [Dynamic Replanning](#dynamic-replanning)
- [Multi-Agent Planning](#multi-agent-planning)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Decompose a complex task into executable steps — implement LLM-backed sequential and hierarchical decomposition, bounding recursion with max_depth and parsing numbered responses into clean step lists
- Turn an LLM plan into tool calls — parse `N. Action: tool[param=value]` lines in ForwardPlanner and run BackwardPlanner, whose reversed step list restores forward execution order
- Recover from failing steps at runtime — splice the regenerated sub-plan into the live plan inside execute_with_replan, keeping the loop index and the max_replans cap consistent
- Coordinate specialist agents on one task — let CoordinatorAgent decompose and keyword-route subtasks, group multi-subtask assignments per specialist, and integrate the per-agent sub-plans

---

## Abstract
Planning and task decomposition enable agents to break down complex tasks into manageable sub-tasks, execute them systematically, and handle dependencies.

## Task Decomposition

### Why Decompose?
```text
Complex task: "Build a sentiment analysis service"

Without decomposition:
  - Where to start?
  - What to do first?
  - How to track progress?

With decomposition:
  1. Create project structure
  2. Install dependencies
  3. Load model
  4. Create API endpoint
  5. Test the service
  6. Deploy to K8s

Each sub-task is clear and actionable
```

### Decomposition Strategies

#### Sequential Decomposition
```python
import re



def sequential_decompose(task: str, llm) -> list[str]:
    """
    Break task into sequential steps
    Each step depends on previous completion
    """
    prompt = f"""
    Task: {task}

    Break this task down into sequential steps.
    Each step should be actionable and depend on the previous step.
    Format as a numbered list.

    Steps:"""

    response = llm.generate(prompt)

    # Parse into list
    steps = []
    for line in response.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            # Remove number/bullet
            step = re.sub(r"^[\d\-\.\)]+\s*", "", line)
            steps.append(step)

    return steps


# Example — any client exposing .generate(prompt) -> str works; the stub
# returns canned steps so the parsing is runnable as-is
class StubLLM:
    def generate(self, prompt: str) -> str:
        return (
            "1. Install Ollama on the NUC\n"
            "2. Pull the llama3.2 model\n"
            "3. Test the model locally\n"
            "4. Create a Kubernetes deployment\n"
            "5. Expose the service via Ingress"
        )


steps = sequential_decompose("Set up Llama 3.2 on the homelab", StubLLM())
print(f"{len(steps)} steps:")
for i, step in enumerate(steps, 1):
    print(f"{i}. {step}")

# Output:
# 5 steps:
# 1. Install Ollama on the NUC
# 2. Pull the llama3.2 model
# 3. Test the model locally
# 4. Create a Kubernetes deployment
# 5. Expose the service via Ingress
```

#### Hierarchical Decomposition
```python
import re


def parse_steps(response: str) -> list[str]:
    """Extract numbered/bulleted steps from an LLM response"""
    steps = []
    for line in response.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            steps.append(re.sub(r"^[\d\-\.\)]+\s*", "", line))
    return steps


def hierarchical_decompose(task: str, llm, max_depth=3) -> dict:
    """
    Break task into hierarchical sub-tasks
    Creates a tree structure of tasks
    """
    def decompose_recursive(current_task, depth):
        if depth >= max_depth:
            return {"name": current_task, "subtasks": []}

        prompt = f"""
        Task: {current_task}

        Break this into 3-5 sub-tasks.
        Return as a numbered list.
        """

        response = llm.generate(prompt)

        subtasks = parse_steps(response)

        return {
            "name": current_task,
            "subtasks": [
                decompose_recursive(subtask, depth + 1)
                for subtask in subtasks
            ]
        }

    return decompose_recursive(task, 0)


def print_tree(node: dict, indent: int = 0) -> None:
    print("  " * indent + node["name"])
    for sub in node["subtasks"]:
        print_tree(sub, indent + 1)


# Example — stub stands in for a real LLM client; max_depth=1 keeps the
# demo tree shallow (raise it to decompose recursively)
class StubLLM:
    def generate(self, prompt: str) -> str:
        return (
            "1. Prepare the infrastructure\n"
            "2. Install the runtime\n"
            "3. Deploy the model"
        )


tree = hierarchical_decompose("Deploy Llama 3.2 on the homelab", StubLLM(),
                              max_depth=1)
print_tree(tree)

# Output:
# Deploy Llama 3.2 on the homelab
#   Prepare the infrastructure
#   Install the runtime
#   Deploy the model
```

## Planning Algorithms

### Forward Planning
```python
import re


class ForwardPlanner:
    """
    Plan from initial state to goal state
    """
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def plan(self, initial_state: str, goal_state: str) -> list[dict]:
        """
        Generate plan from initial to goal state
        """
        prompt = f"""
        Initial State: {initial_state}
        Goal State: {goal_state}

        Available Tools: {list(self.tools.keys())}

        Plan a sequence of actions to reach the goal state.
        Each action should specify the tool and parameters.

        Plan:"""

        response = self.llm.generate(prompt)
        return self._parse_plan(response)

    def _parse_plan(self, response: str) -> list[dict]:
        """Parse plan into actionable steps"""
        steps = []

        for line in response.split("\n"):
            if not line.strip():
                continue

            # Expected format: 1. Action: tool_name[param1=value1, ...]
            match = re.match(r"\d+\. Action: (\w+)\[(.*)\]", line)
            if match:
                tool_name = match.group(1)
                params_str = match.group(2)

                # Parse parameters
                params = {}
                for param in params_str.split(", "):
                    if "=" in param:
                        key, value = param.split("=")
                        params[key.strip()] = value.strip()

                steps.append({
                    "tool": tool_name,
                    "params": params
                })

        return steps

    def execute_plan(self, plan: list[dict]) -> list[str]:
        """Execute plan and return observations — a tool error is an
        observation for the next planning round, not a crash"""
        observations = []

        for step in plan:
            tool = self.tools.get(step["tool"])
            if tool is None:
                observations.append(f"Error: Unknown tool {step['tool']}")
                continue

            try:
                result = tool(**step["params"])
                observations.append(str(result))
            except Exception as e:
                observations.append(f"Error: {str(e)}")

        return observations


# Example — stub LLM returns a canned plan so parsing and execution
# are runnable as-is
class StubLLM:
    def generate(self, prompt: str) -> str:
        return (
            "1. Action: check_gpu[threshold=0.5]\n"
            "2. Action: install[package=ollama]"
        )


def check_gpu(threshold):
    return f"GPU free ratio {1 - float(threshold):.0%}"


def install(package):
    return f"{package} installed"


planner = ForwardPlanner(StubLLM(),
                         {"check_gpu": check_gpu, "install": install})
plan = planner.plan("bare NUC", "serving llama3.2")
print(plan)
print(planner.execute_plan(plan))

# Output:
# [{'tool': 'check_gpu', 'params': {'threshold': '0.5'}}, {'tool': 'install', 'params': {'package': 'ollama'}}]
# ['GPU free ratio 50%', 'ollama installed']
```

### Backward Planning
```python
import re


class BackwardPlanner:
    """
    Plan from goal state back to initial state
    Useful when goal is clear but path is not
    """
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def plan(self, initial_state: str, goal_state: str) -> list[dict]:
        """
        Generate plan working backwards from goal
        """
        prompt = f"""
        Initial State: {initial_state}
        Goal State: {goal_state}

        Available Tools: {list(self.tools.keys())}

        Working backwards from the goal, what is the last action needed?
        Then what precedes that?
        Continue until you reach the initial state.

        Plan (in reverse order):"""

        response = self.llm.generate(prompt)

        # Parse and reverse — the response lists the LAST action first,
        # so reversing restores forward execution order
        steps = self._parse_plan(response)
        return list(reversed(steps))

    def _parse_plan(self, response: str) -> list[dict]:
        """Parse 'N. Action: tool[param=value]' lines into steps"""
        steps = []

        for line in response.split("\n"):
            if not line.strip():
                continue

            match = re.match(r"\d+\. Action: (\w+)\[(.*)\]", line)
            if match:
                params = {}
                for param in match.group(2).split(", "):
                    if "=" in param:
                        key, value = param.split("=")
                        params[key.strip()] = value.strip()

                steps.append({
                    "tool": match.group(1),
                    "params": params
                })

        return steps


# Example — the stub answers in reverse order (last action first)
class StubLLM:
    def generate(self, prompt: str) -> str:
        return (
            "1. Action: expose_service[port=8080]\n"
            "2. Action: deploy_model[name=llama3.2]\n"
            "3. Action: install_runtime[tool=ollama]"
        )


planner = BackwardPlanner(StubLLM(), {})
plan = planner.plan("bare NUC", "serving llama3.2")
print([step["tool"] for step in plan])

# Output:
# ['install_runtime', 'deploy_model', 'expose_service']
```

### Task Planning with Dependencies
```python
import re


class TaskPlanner:
    """
    Plan tasks with dependency resolution
    """
    def __init__(self, llm):
        self.llm = llm

    def plan_with_dependencies(self, task: str) -> list[dict]:
        """
        Create plan with explicit dependencies
        """
        prompt = f"""
        Task: {task}

        Break this into sub-tasks with dependencies.
        For each sub-task, specify what it depends on.

        Format:
        - Task 1: [description]
          Depends: [list of task numbers this depends on]

        Plan:"""

        response = self.llm.generate(prompt)
        return self._parse_dependencies(response)

    def _parse_dependencies(self, response: str) -> list[dict]:
        """Parse tasks with dependencies"""
        tasks = []
        current_task = None

        for line in response.split("\n"):
            line = line.strip()

            # Task line
            if line.startswith("- Task"):
                match = re.match(r"- Task (\d+): (.+)", line)
                if match:
                    task_id = int(match.group(1))
                    description = match.group(2)
                    current_task = {
                        "id": task_id,
                        "description": description,
                        "dependencies": []
                    }
                    tasks.append(current_task)

            # Depends line
            elif line.startswith("Depends:") and current_task:
                match = re.search(r"\[(.+)\]", line)
                if match and match.group(1).strip():
                    deps = [int(d.strip()) for d in match.group(1).split(",")]
                    current_task["dependencies"] = deps

        return tasks

    def get_execution_order(self, tasks: list[dict]) -> list[dict]:
        """
        Topological sort for execution order.
        Raises ValueError on unknown dependency references and on
        dependency cycles (which would otherwise recurse forever).
        """
        by_id = {task["id"]: task for task in tasks}
        visited = set()
        in_progress = set()
        order = []

        def visit(task):
            if task["id"] in visited:
                return
            if task["id"] in in_progress:
                raise ValueError(f"Circular dependency at task {task['id']}")

            in_progress.add(task["id"])

            # Visit dependencies first
            for dep_id in task["dependencies"]:
                if dep_id not in by_id:
                    raise ValueError(
                        f"Task {task['id']} depends on unknown task {dep_id}")
                visit(by_id[dep_id])

            in_progress.discard(task["id"])
            visited.add(task["id"])
            order.append(task)

        for task in tasks:
            visit(task)

        return order


# Example — stub response with an explicit dependency chain
class StubLLM:
    def generate(self, prompt: str) -> str:
        return (
            "- Task 1: Install the container runtime\n"
            "  Depends: []\n"
            "- Task 2: Pull the model image\n"
            "  Depends: [1]\n"
            "- Task 3: Serve the model endpoint\n"
            "  Depends: [2]"
        )


planner = TaskPlanner(StubLLM())
tasks = planner.plan_with_dependencies("Serve llama3.2 on the homelab")
print([task["id"] for task in planner.get_execution_order(tasks)])

# Output:
# [1, 2, 3]
```

## Dynamic Replanning

### Replanning on Failure
```python
import re


class Replanner:
    """
    Replan when execution fails
    """
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def execute_with_replan(self, plan: list[dict], max_replans=3) -> list[str]:
        """
        Execute plan, replan if steps fail.
        The plan is spliced and walked with an index — mutating the list
        inside `for i, step in enumerate(plan)` would keep iterating the
        ORIGINAL list object and never run the replacement steps.
        """
        observations = []
        replan_count = 0
        i = 0

        while i < len(plan):
            step = plan[i]

            # Try to execute step
            observation = self._execute_step(step)
            observations.append(observation)

            # Check for failure
            if "Error" in observation:
                if replan_count >= max_replans:
                    return observations + ["\nMax replans reached"]

                # Replan from this point — the alternative plan replaces
                # the failed step and everything after it
                new_plan = self._replan(step, observation, plan[i + 1:])

                if new_plan:
                    plan = plan[:i] + new_plan
                    replan_count += 1
                    continue
                else:
                    return observations + ["\nCould not replan"]

            i += 1

        return observations

    def _replan(self, failed_step: dict, error: str, context: list[dict]) -> list[dict]:
        """
        Generate new plan given failure
        """
        prompt = f"""
        Failed Step: {failed_step}

        Error: {error}

        Remaining Plan: {context}

        Generate an alternative plan to achieve the same goal,
        avoiding the step that failed.

        New Plan:"""

        response = self.llm.generate(prompt)
        return self._parse_plan(response)

    def _parse_plan(self, response: str) -> list[dict]:
        """Parse 'N. Action: tool[param=value]' lines into steps"""
        steps = []

        for line in response.split("\n"):
            if not line.strip():
                continue

            match = re.match(r"\d+\. Action: (\w+)\[(.*)\]", line)
            if match:
                params = {}
                for param in match.group(2).split(", "):
                    if "=" in param:
                        key, value = param.split("=")
                        params[key.strip()] = value.strip()

                steps.append({
                    "tool": match.group(1),
                    "params": params
                })

        return steps

    def _execute_step(self, step: dict) -> str:
        """Execute a single step — tool errors become observations"""
        tool = self.tools.get(step["tool"])
        if tool is None:
            return f"Error: Unknown tool {step['tool']}"

        try:
            result = tool(**step["params"])
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"


# Example — the model pull fails once; the replan LLM (stubbed) retries
# it inside the regenerated plan
class FlakyPull:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls == 1:
            raise ConnectionError("registry unreachable")
        return "model pulled"


class StubLLM:
    def generate(self, prompt: str) -> str:
        return "1. Action: pull_model[]\n2. Action: serve[]"


replanner = Replanner(StubLLM(),
                      {"pull_model": FlakyPull(), "serve": lambda: "endpoint up :8000"})
for observation in replanner.execute_with_replan(
        [{"tool": "pull_model", "params": {}},
         {"tool": "serve", "params": {}}]):
    print(observation)

# Output:
# Error: registry unreachable
# model pulled
# endpoint up :8000
```

## Multi-Agent Planning

### Distributed Planning
```python
import re


class CoordinatorAgent:
    """
    Coordinates multiple specialist agents
    """
    def __init__(self, agents: dict[str, "ReActAgent"], llm):
        # ReActAgent comes from lesson 7101; the annotation is quoted so
        # this block stays runnable without importing it
        self.agents = agents
        self.llm = llm

    def decompose(self, task: str) -> list[str]:
        """Decompose task into domain-specific subtasks"""
        prompt = f"""
        Task: {task}

        Available Specialists:
        - k8s: Kubernetes deployment and management
        - gpu: GPU monitoring and optimization
        - storage: NAS and file system management
        - network: Network configuration and troubleshooting

        Decompose the task and assign to appropriate specialists.
        Format: "Specialist: subtask description"

        Decomposition:"""

        response = self.llm.generate(prompt)
        return self._parse_decomposition(response)

    def _parse_decomposition(self, response: str) -> list[str]:
        """Extract 'specialist: subtask' lines; the prefix is kept so
        keyword routing in assign_agent can see the specialist"""
        subtasks = []

        for line in response.split("\n"):
            line = line.strip()
            if re.match(r"^[a-z][a-z0-9_]*:\s+\S", line, re.IGNORECASE):
                subtasks.append(line)

        return subtasks

    def assign_agent(self, subtask: str) -> str:
        """Assign subtask to appropriate specialist"""
        # Simple keyword matching (could be more sophisticated)
        if "kubernetes" in subtask.lower() or "k8s" in subtask.lower():
            return "k8s"
        elif "gpu" in subtask.lower():
            return "gpu"
        elif "storage" in subtask.lower() or "nas" in subtask.lower():
            return "storage"
        elif "network" in subtask.lower():
            return "network"
        else:
            return "general"

    def integrate(self, plans: dict[str, list[dict]]) -> list[dict]:
        """Integrate sub-plans into coordinated plan.
        Simplified concatenation — for dependency-aware ordering, run the
        result through TaskPlanner.get_execution_order (above)."""
        integrated = []

        for plan in plans.values():
            integrated.extend(plan)

        return integrated


class DistributedPlanner:
    """
    Distribute planning across multiple specialized agents
    """
    def __init__(self, agents: dict[str, "ReActAgent"], llm):
        self.agents = agents
        self.coordinator = CoordinatorAgent(agents, llm)

    def plan(self, task: str) -> list[dict]:
        """
        Break down task and delegate to specialist agents
        """
        # Step 1: Analyze task and identify sub-domains
        subtasks = self.coordinator.decompose(task)

        # Step 2: Assign subtasks — one specialist may receive several,
        # so group them (a plain dict would silently keep only the last);
        # unroutable subtasks fall back to the generalist
        assignments: dict[str, list[str]] = {}
        for subtask in subtasks:
            specialist = self.coordinator.assign_agent(subtask)
            if specialist not in self.agents:
                specialist = "general"
            assignments.setdefault(specialist, []).append(subtask)

        # Step 3: Each specialist sub-plans its own queue, flattened
        # into one plan list so integrate can concatenate directly
        plans = {}
        for specialist, queue in assignments.items():
            agent = self.agents[specialist]
            plans[specialist] = [
                step for subtask in queue for step in agent.plan(subtask)
            ]

        # Step 4: Coordinate and integrate plans
        return self.coordinator.integrate(plans)


# Example — stub coordinator LLM and stub specialist agents; two k8s
# subtasks prove the grouping (the old dict form kept only the last)
class StubCoordinatorLLM:
    def generate(self, prompt: str) -> str:
        return (
            "k8s: Roll out the deployment\n"
            "k8s: Verify pod health after the rollout\n"
            "gpu: Check GPU utilization during the rollout"
        )


class StubAgent:
    def __init__(self, name):
        self.name = name

    def plan(self, task: str) -> list[dict]:
        return [{"tool": f"{self.name}_plan", "params": {"task": task}}]


agents = {
    "k8s": StubAgent("k8s"),
    "gpu": StubAgent("gpu"),
    "general": StubAgent("general"),
}
planner = DistributedPlanner(agents, StubCoordinatorLLM())
for step in planner.plan("Release the new model"):
    print(step)

# Output:
# {'tool': 'k8s_plan', 'params': {'task': 'k8s: Roll out the deployment'}}
# {'tool': 'k8s_plan', 'params': {'task': 'k8s: Verify pod health after the rollout'}}
# {'tool': 'gpu_plan', 'params': {'task': 'gpu: Check GPU utilization during the rollout'}}
```


---

## Summary

Planning and task decomposition turn one impossible prompt into a tree of executable sub-tasks: break the goal down, order the sub-tasks by dependency, execute them systematically, and re-plan when reality disagrees with the plan. This lesson walked why decomposition works, the dependency handling, and the failure modes of plans that were never executable. The rule it leaves: decompose until each sub-task is one tool call with a checkable result - a plan step you cannot verify is a step you cannot recover from.

## References

### Related PROJECT-OMEGA Documents

- [7101: ReAct (Reasoning + Acting) Loop System](7101-ReAct-Loop-System.md)
- [7301: Collaborative Tasking](../7300-orchestration/7301-Orchestration.md)
- [7303: Framework Comparison](../7300-orchestration/guides/7303-Framework-Comparison.md)

---

## Next Steps

- Continue with: **[7201: Tool Calling](../7200-tools/7201-Tool-Calling.md)**
- Assessment: **[QUIZ](./assessment/QUIZ.md)**
- Experiment: **[EXP_7102: Planning](../../../../experiments/EXP_7102_PLANNING.md)**
