---
Document ID: 7102
Title: Planning and Task Decomposition
Phase: 7
Module: 7100
Last Updated: 2026-09-24
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
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Task Decomposition
- Explain Planning Algorithms
- Explain Dynamic Replanning
- Explain Multi-Agent Planning

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
def sequential_decompose(task: str, llm) -> List[str]:
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

# Example
task = "Set up a Llama-2 model on the Homelab"
steps = sequential_decompose(task, llama_model)

# Output:
# 1. Install Ollama on the NUC
# 2. Pull the llama2 model using Ollama
# 3. Test the model locally
# 4. Create a Kubernetes deployment
# 5. Expose the service via Ingress
```

#### Hierarchical Decomposition
```python
def hierarchical_decompose(task: str, llm, max_depth=3) -> Dict:
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

# Example
task = "Deploy Llama-2 to Homelab"
tree = hierarchical_decompose(task, llama_model)

# Output:
# Deploy Llama-2 to Homelab
# ├─ Prepare infrastructure
# │  ├─ Check GPU availability
# │  ├─ Verify network connectivity
# │  └─ Prepare storage
# ├─ Install Ollama
# │  ├─ Install dependencies
# │  ├─ Download Ollama
# │  └─ Configure Ollama
# └─ Deploy model
#    ├─ Pull Llama-2 model
#    ├─ Create K8s deployment
#    └─ Configure ingress
```

## Planning Algorithms

### Forward Planning
```python
class ForwardPlanner:
    """
    Plan from initial state to goal state
    """
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def plan(self, initial_state: str, goal_state: str) -> List[Dict]:
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

    def _parse_plan(self, response: str) -> List[Dict]:
        """Parse plan into actionable steps"""
        steps = []

        for line in response.split("\n"):
            if not line.strip():
                continue

            # Expected format: 1. Action: tool_name[param1=value1, ...]
            match = re.match(r"\d+\. Action: (\w+)\[(.+)\]", line)
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

    def execute_plan(self, plan: List[Dict]) -> List[str]:
        """Execute plan and return observations"""
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
```

### Backward Planning
```python
class BackwardPlanner:
    """
    Plan from goal state back to initial state
    Useful when goal is clear but path is not
    """
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def plan(self, initial_state: str, goal_state: str) -> List[Dict]:
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

        Plan (in reverse order):" ""

        response = self.llm.generate(prompt)

        # Parse and reverse
        steps = self._parse_plan(response)
        return list(reversed(steps))
```

### Task Planning with Dependencies
```python
class TaskPlanner:
    """
    Plan tasks with dependency resolution
    """
    def __init__(self, llm):
        self.llm = llm

    def plan_with_dependencies(self, task: str) -> List[Dict]:
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

    def _parse_dependencies(self, response: str) -> List[Dict]:
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
                if match:
                    deps_str = match.group(1)
                    deps = [int(d.strip()) for d in deps_str.split(",")]
                    current_task["dependencies"] = deps

        return tasks

    def get_execution_order(self, tasks: List[Dict]) -> List[Dict]:
        """
        Topological sort for execution order
        """
        visited = set()
        order = []

        def visit(task):
            if task["id"] in visited:
                return

            # Visit dependencies first
            for dep_id in task["dependencies"]:
                dep = next(t for t in tasks if t["id"] == dep_id)
                visit(dep)

            visited.add(task["id"])
            order.append(task)

        for task in tasks:
            visit(task)

        return order
```

## Dynamic Replanning

### Replanning on Failure
```python
class Replanner:
    """
    Replan when execution fails
    """
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def execute_with_replan(self, plan: List[Dict], max_replans=3) -> List[str]:
        """
        Execute plan, replan if steps fail
        """
        observations = []
        replan_count = 0

        for i, step in enumerate(plan):
            # Try to execute step
            observation = self._execute_step(step)
            observations.append(observation)

            # Check for failure
            if "Error" in observation:
                if replan_count >= max_replans:
                    return observations + ["\nMax replans reached"]

                # Replan from this point
                remaining_plan = plan[i+1:]
                new_plan = self._replan(step, observation, remaining_plan)

                if new_plan:
                    plan = plan[:i+1] + new_plan
                    replan_count += 1
                else:
                    return observations + ["\nCould not replan"]

        return observations

    def _replan(self, failed_step: Dict, error: str, context: List[Dict]) -> List[Dict]:
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

    def _execute_step(self, step: Dict) -> str:
        """Execute a single step"""
        tool = self.tools.get(step["tool"])
        if tool is None:
            return f"Error: Unknown tool {step['tool']}"

        try:
            result = tool(**step["params"])
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
```

## Multi-Agent Planning

### Distributed Planning
```python
class DistributedPlanner:
    """
    Distribute planning across multiple specialized agents
    """
    def __init__(self, agents: Dict[str, ReActAgent]):
        self.agents = agents
        self.coordinator = CoordinatorAgent(agents)

    def plan(self, task: str) -> Dict:
        """
        Break down task and delegate to specialist agents
        """
        # Step 1: Analyze task and identify sub-domains
        subtasks = self.coordinator.decompose(task)

        # Step 2: Assign subtasks to specialist agents
        assignments = {}
        for subtask in subtasks:
            specialist = self.coordinator.assign_agent(subtask)
            assignments[specialist] = subtask

        # Step 3: Each specialist creates sub-plan
        plans = {}
        for specialist, subtask in assignments.items():
            agent = self.agents[specialist]
            plan = agent.plan(subtask)
            plans[specialist] = plan

        # Step 4: Coordinate and integrate plans
        integrated_plan = self.coordinator.integrate(plans)

        return integrated_plan

class CoordinatorAgent:
    """
    Coordinates multiple specialist agents
    """
    def decompose(self, task: str) -> List[str]:
        """Decompose task into domain-specific subtasks"""
        prompt = f"""
        Task: {task}

        Available Specialists:
        - K8s Agent: Kubernetes deployment and management
        - GPU Agent: GPU monitoring and optimization
        - Storage Agent: NAS and file system management
        - Network Agent: Network configuration and troubleshooting

        Decompose the task and assign to appropriate specialists.
        Format: "Specialist: subtask description"

        Decomposition:"""

        response = self.llm.generate(prompt)
        return self._parse_decomposition(response)

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

    def integrate(self, plans: Dict[str, List[Dict]]) -> List[Dict]:
        """Integrate sub-plans into coordinated plan"""
        # Sort plans by dependencies
        integrated = []

        # This is simplified - real implementation would resolve dependencies
        for specialist, plan in plans.items():
            integrated.extend(plan)

        return integrated
```


---

## References

### Related ai-engineering-curriculum Documents

- [7101: ReAct (Reasoning + Acting) Loop System](7101-ReAct-Loop-System.md)

---

## Next Steps

- Continue with: **[7201-Tool-Calling.md](./../7200-tools/7201-Tool-Calling.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [7101: ReAct Loop](./7101-ReAct-Loop-System.md)
- [7301: Collaborative Tasking](../7300-orchestration/7301-Orchestration.md)
- [7303: Framework Comparison](../7300-orchestration/guides/7303-Framework-Comparison.md)

**Experiment Template:** [EXP_7102: Planning](../../../../experiments/EXP_7102_PLANNING.md)
