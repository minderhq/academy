# 7100: LLM Reasoning - Practice

## Exercises

### Exercise 1: Implement Chain-of-Thought Prompting

```python
def chain_of_thought_prompt(question):
    """Generate CoT prompt for reasoning tasks."""

    prompt = f"""Let's think step by step to solve this problem.

Question: {question}

Let's approach this systematically:

Step 1: Let's understand what the question is asking.
Step 2: What information do we have?
Step 3: What's the first step to solve this?
Step 4: Let's work through the logic.
Step 5: What's the final answer?

Answer:"""

    return prompt

# SOLUTION: Test with reasoning task using mock LLM
def mock_llm(prompt):
    """
    Mock LLM function for demonstration.
    In production, replace with actual LLM API call (OpenAI, Anthropic, etc.).

    SOLUTION: Simulates chain-of-thought reasoning response.
    Shows step-by-step problem solving approach.
    """
    return """
Step 1: Understanding the question
I need to track the number of apples through multiple operations.

Step 2: Initial information
Start with 3 apples.

Step 3: First operation - eat 1 apple
3 - 1 = 2 apples remaining

Step 4: Second operation - buy 5 more
2 + 5 = 7 apples now

Step 5: Third operation - give away 2
7 - 2 = 5 apples remaining

Answer: 5 apples
"""

# Test with reasoning task
question = "If I have 3 apples and eat 1, then buy 5 more, and give away 2, how many do I have?"

prompt = chain_of_thought_prompt(question)
response = mock_llm(prompt)

print("Chain-of-Thought Reasoning Example:")
print("=" * 60)
print("Question:", question)
print("\nResponse:")
print(response)
print("=" * 60)

# Expected Output:
# Step-by-step reasoning showing:
# - Start: 3 apples
# - After eating 1: 2 apples
# - After buying 5: 7 apples
# - After giving away 2: 5 apples
# Final Answer: 5 apples
```

### Exercise 2: Self-Consistency Reasoning

```python
def self_consistency_solve(question, llm, n_samples=5):
    """Generate multiple reasoning paths and find consensus."""

    # SOLUTION: Generate multiple solutions with diversity
    solutions = []
    for i in range(n_samples):
        prompt = f"""Solve this step by step:
{question}

Provide your final answer as: "Answer: X"

(Think carefully and show your work)"""

        # SOLUTION: Use mock LLM with temperature for diversity
        response = mock_llm_with_temperature(prompt, temperature=0.7)
        solutions.append(response)

    # SOLUTION: Extract answers using regex
    import re
    answers = []
    for sol in solutions:
        match = re.search(r"Answer:\s*(.+?)(?:\.|$)", sol)
        if match:
            answers.append(match.group(1).strip())

    # SOLUTION: Find majority vote with confidence calculation
    from collections import Counter
    answer_counts = Counter(answers)

    if answer_counts:
        most_common = answer_counts.most_common(1)[0]
        final_answer = most_common[0]
        confidence = most_common[1] / len(answers)
    else:
        final_answer = "Unable to determine"
        confidence = 0

    return {
        "answer": final_answer,
        "confidence": confidence,
        "all_solutions": solutions,
        "vote_distribution": dict(answer_counts),
    }

# SOLUTION: Define mock LLM with temperature simulation
def mock_llm_with_temperature(prompt, temperature=0.7):
    """
    Mock LLM that simulates temperature-based sampling.

    SOLUTION: Returns slightly varied responses based on seed
    to simulate diverse reasoning paths.
    """
    import random
    import time

    # Use time as seed for randomness
    random.seed(int(time.time() * 1000) % 1000)

    # Different reasoning paths that might occur
    reasoning_paths = [
        """Starting: 3 apples
Eat 1: 3-1=2
Buy 5: 2+5=7
Give away 2: 7-2=5
Answer: 5""",

        """Let's track step by step:
Initial: 3 apples
After eating: 2 apples
After buying: 7 apples
After giving away: 5 apples
Answer: 5""",

        """3 apples initially
Lose 1 apple → 2 apples
Gain 5 apples → 7 apples
Lose 2 apples → 5 apples
Answer: 5""",

        """Operations: -1, +5, -2 on initial 3
3-1=2, 2+5=7, 7-2=5
Final count: 5
Answer: 5""",

        """Working backwards:
End with ?
Before giving 2: ?+2
Before buying 5: ?-5
Before eating 1: ?+1
?+2-5+1=3, so ?=5
Answer: 5"""
    ]

    return random.choice(reasoning_paths)

# SOLUTION: Test self-consistency
print("\n" + "=" * 60)
print("Self-Consistency Reasoning Test")
print("=" * 60)

question = "If I have 3 apples and eat 1, then buy 5 more, and give away 2, how many do I have?"

result = self_consistency_solve(question, mock_llm_with_temperature, n_samples=5)

print(f"\nQuestion: {question}")
print(f"\nFinal answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"\nVote distribution: {result['vote_distribution']}")
print(f"\nNumber of reasoning paths: {len(result['all_solutions'])}")

# Expected Output:
# Final answer: 5 (confidence: 100% or 1.00)
# Vote distribution: {'5': 5}
# All 5 reasoning paths converged to the same answer
```

### Exercise 3: Tree-of-Thoughts Implementation

```python
class TreeOfThoughts:
    """
    Tree-of-Thoughts reasoning implementation.

    SOLUTION: Explores multiple reasoning paths in a tree structure,
    evaluating each path and selecting the best solution.
    """
    def __init__(self, llm, max_branches=3, max_depth=3):
        self.llm = llm
        self.max_branches = max_branches
        self.max_depth = max_depth

    def solve(self, problem):
        """Solve problem using tree-of-thoughts approach."""

        # SOLUTION: Initialize root node with problem statement
        root = {
            "state": problem,
            "thought": None,
            "parent": None,
            "children": [],
            "depth": 0,
        }

        # SOLUTION: Explore tree to find all solution paths
        solutions = self._explore(root)

        # SOLUTION: Return best solution based on evaluation score
        if not solutions:
            return {"error": "No solutions found"}

        best = max(solutions, key=lambda x: x["score"])
        return best

    def _explore(self, node):
        """Explore thoughts from a node."""

        if node["depth"] >= self.max_depth:
            # Leaf node - evaluate
            score = self._evaluate(node["state"])
            return [{"node": node, "score": score}]

        # SOLUTION: Generate thoughts using LLM
        thoughts = self._generate_thoughts(node["state"])

        # SOLUTION: Create child nodes for each thought
        for thought in thoughts[:self.max_branches]:
            new_state = self._apply_thought(node["state"], thought)

            child = {
                "state": new_state,
                "thought": thought,
                "parent": node,
                "children": [],
                "depth": node["depth"] + 1,
            }

            node["children"].append(child)

        # SOLUTION: Recursively explore all branches
        solutions = []
        for child in node["children"]:
            solutions.extend(self._explore(child))

        return solutions

    def _generate_thoughts(self, state):
        """
        Generate possible next thoughts using LLM.

        SOLUTION: Creates diverse reasoning steps to explore.
        """
        prompt = f"""Given this problem state: {state}

Generate {self.max_branches} different possible next steps to solve it.
List each step on a new line starting with 'Step:'."""

        response = self.llm(prompt)
        thoughts = [t.strip() for t in response.split("\n") if t.strip() and "Step:" in t]

        # Fallback if no thoughts generated
        if not thoughts:
            thoughts = [
                "Analyze the problem components",
                "Break down into sub-problems",
                "Consider similar solved problems"
            ]

        return thoughts

    def _apply_thought(self, state, thought):
        """
        Apply a thought to get new state.

        SOLUTION: Uses LLM to reason about the state transition.
        """
        prompt = f"""Problem: {state}

Proposed step: {thought}

What is the new state after applying this step? Provide a brief update."""

        return self.llm(prompt)

    def _evaluate(self, state):
        """
        Evaluate the quality of a state.

        SOLUTION: Returns score from 1-10 based on solution quality.
        """
        prompt = f"""Evaluate this solution on a scale of 1-10:
{state}

Consider: Is it complete? Is it correct? Is it clear?

Score (just the number):"""

        response = self.llm(prompt)

        # Extract score
        import re
        match = re.search(r"(\d+)", response)
        return int(match.group(1)) if match else 5

# SOLUTION: Mock LLM for Tree-of-Thoughts
def mock_tot_llm(prompt):
    """
    Mock LLM that handles Tree-of-Thoughts prompts.

    SOLUTION: Returns contextually appropriate responses
    based on prompt type.
    """
    if "Generate" in prompt and "next steps" in prompt:
        return """Step: Break down the apple operations
Step: Track each operation separately
Step: Verify the final count"""

    if "new state" in prompt:
        return "Updated state with current apple count"

    if "Evaluate" in prompt:
        return "8"

    return "Proceeding with solution"

# SOLUTION: Test Tree-of-Thoughts
print("\n" + "=" * 60)
print("Tree-of-Thoughts Test")
print("=" * 60)

tot = TreeOfThoughts(mock_tot_llm, max_branches=3, max_depth=2)
problem = "Calculate the number of apples after operations"

result = tot.solve(problem)

print(f"\nProblem: {problem}")
print(f"Best solution score: {result.get('score', 'N/A')}")
print(f"Solution depth: {result['node']['depth']}")
print(f"Final state: {result['node']['state'][:100]}...")

# Expected Output:
# Score: 8/10
# Solution shows structured reasoning through tree branches
```

### Exercise 4: ReAct Pattern (Reasoning + Acting)

```python
class ReActAgent:
    """
    ReAct (Reasoning + Acting) Agent implementation.

    SOLUTION: Alternates between thinking, acting, and observing
    to solve problems iteratively.
    """
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}

    def run(self, query, max_steps=10):
        """Run ReAct loop: Thought -> Action -> Observation."""

        trajectory = []
        thought = None

        for step in range(max_steps):
            # SOLUTION: Generate thought about current state
            prompt = self._build_prompt(query, trajectory)

            response = self.llm(prompt)
            thought, action, action_input = self._parse_response(response)

            trajectory.append({
                "thought": thought,
                "action": action,
                "action_input": action_input,
            })

            # SOLUTION: Execute action or finish
            if action == "finish":
                print(f"\n[Step {step+1}] Finished!")
                return trajectory

            if action in self.tools:
                tool = self.tools[action]
                observation = tool.run(action_input)

                trajectory[-1]["observation"] = observation

                print(f"[Step {step+1}] Thought: {thought}")
                print(f"[Step {step+1}] Action: {action}({action_input})")
                print(f"[Step {step+1}] Observation: {observation}\n")

        return trajectory

    def _build_prompt(self, query, trajectory):
        """Build prompt from query and trajectory."""

        tools_desc = "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.tools.items()
        ])

        trajectory_str = ""
        for step in trajectory:
            trajectory_str += f"Thought: {step['thought']}\n"
            trajectory_str += f"Action: {step['action']}({step['action_input']})\n"
            if "observation" in step:
                trajectory_str += f"Observation: {step['observation']}\n"

        prompt = f"""Available tools:
{tools_desc}

Question: {query}

{trajectory_str}
Thought:"""

        return prompt

    def _parse_response(self, response):
        """Parse LLM response into thought, action, action_input."""
        import re

        # Extract thought
        thought_match = re.search(r"Thought:\s*(.+?)(?:\nAction:|$)", response, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        # Extract action
        action_match = re.search(r"Action:\s*(\w+)(?:\((.+)\))?", response)
        action = action_match.group(1) if action_match else "finish"
        action_input = action_match.group(2) if action_match and len(action_match.groups()) > 1 else ""

        return thought, action, action_input

# SOLUTION: Define simple tools for ReAct
class MockTool:
    """Mock tool for ReAct demonstrations."""
    def __init__(self, name, description, func):
        self.name = name
        self.description = description
        self.func = func

    def run(self, input_data):
        return self.func(input_data)

# Create mock tools
def calculator_tool(input_str):
    """Simple calculator that evaluates expressions."""
    try:
        result = eval(input_str)
        return f"Result: {result}"
    except:
        return "Error: Invalid expression"

def search_tool(query):
    """Mock search tool."""
    results = [
        f"Found info about: {query}",
        "Relevant result: The answer is 5",
    ]
    return "\n".join(results)

tools = [
    MockTool("calculator", "Evaluates mathematical expressions", calculator_tool),
    MockTool("search", "Searches for information", search_tool),
]

# SOLUTION: Mock LLM for ReAct
def mock_react_llm(prompt):
    """
    Mock LLM for ReAct pattern.

    SOLUTION: Returns structured responses with Thought and Action.
    """
    if "Question:" in prompt and "Thought:" in prompt:
        if "trajectory" not in prompt.lower() or len(prompt.split("Thought:")) < 3:
            return """Thought: I need to calculate the result step by step
Action: calculator(3-1+5-2)"""
        else:
            return """Thought: I have the answer now
Action: finish"""

    return "Thought: Processing\nAction: finish"

# SOLUTION: Test ReAct Agent
print("\n" + "=" * 60)
print("ReAct Agent Test")
print("=" * 60)

agent = ReActAgent(mock_react_llm, tools)
query = "If I have 3 apples and eat 1, then buy 5 more, and give away 2, how many do I have?"

print(f"Query: {query}\n")
trajectory = agent.run(query, max_steps=5)

print(f"\nTotal steps: {len(trajectory)}")
print("\nTrajectory summary:")
for i, step in enumerate(trajectory, 1):
    print(f"{i}. Thought: {step['thought'][:50]}...")
    print(f"   Action: {step['action']}")

# Expected Output:
# Step 1: Thought about calculating -> Action: calculator
# Step 2: Thought: I have the answer -> Action: finish
```

### Exercise 5: Reflexion Pattern (Self-Reflection)

```python
class ReflexionAgent:
    """
    Reflexion Agent with self-reflection capabilities.

    SOLUTION: Generates solutions, reflects on them, and iteratively
    improves through multiple refinement cycles.
    """
    def __init__(self, llm, max_reflections=3):
        self.llm = llm
        self.max_reflections = max_reflections

    def solve_with_reflection(self, problem):
        """Solve problem with self-reflection."""

        # SOLUTION: Generate initial attempt
        attempt = self._generate_solution(problem)
        trajectory = [{"attempt": attempt, "reflection": None}]

        # SOLUTION: Reflect and improve iteratively
        for i in range(self.max_reflections):
            # Generate reflection on current attempt
            reflection = self._reflect(problem, attempt)
            trajectory[-1]["reflection"] = reflection

            # Generate improved solution based on reflection
            attempt = self._improve_solution(problem, attempt, reflection)
            trajectory.append({"attempt": attempt, "reflection": None})

        return trajectory

    def _generate_solution(self, problem):
        """Generate initial solution."""
        prompt = f"""Solve this problem:
{problem}

Provide your solution:"""
        return self.llm(prompt)

    def _reflect(self, problem, solution):
        """Generate reflection on solution."""
        prompt = f"""Problem:
{problem}

Solution:
{solution}

Reflect on this solution:
1. What are potential issues or errors?
2. What could be improved?
3. What's missing?

Reflection:"""
        return self.llm(prompt)

    def _improve_solution(self, problem, previous_solution, reflection):
        """Generate improved solution."""
        prompt = f"""Problem:
{problem}

Previous solution:
{previous_solution}

Reflection on previous solution:
{reflection}

Based on the reflection, provide an improved solution:"""
        return self.llm(prompt)

# SOLUTION: Mock LLM for Reflexion
def mock_reflection_llm(prompt):
    """
    Mock LLM for Reflexion pattern.

    SOLUTION: Simulates the reflection and improvement cycle.
    """
    if "Provide your solution:" in prompt:
        return """Initial solution:
Let's calculate: 3 - 1 = 2, 2 + 5 = 7, 7 - 2 = 5
Answer: 5 apples"""

    if "Reflect on this solution:" in prompt:
        return """Reflection:
1. The calculation is correct
2. Could show more detailed steps
3. Should verify each step"""

    if "improved solution:" in prompt:
        return """Improved solution:
Step 1: Start with 3 apples
Step 2: Eat 1 → 3 - 1 = 2 apples
Step 3: Buy 5 → 2 + 5 = 7 apples
Step 4: Give away 2 → 7 - 2 = 5 apples
Verification: Operations are -1, +5, -2 = +2 net, so 3 + 2 = 5 ✓
Answer: 5 apples (verified)"""

    return "Solution"

# SOLUTION: Test Reflexion Agent
print("\n" + "=" * 60)
print("Reflexion Agent Test")
print("=" * 60)

agent = ReflexionAgent(mock_reflection_llm, max_reflections=2)
problem = "If I have 3 apples and eat 1, then buy 5 more, and give away 2, how many do I have?"

print(f"Problem: {problem}\n")
trajectory = agent.solve_with_reflection(problem)

print(f"Iterations: {len(trajectory)}")
print("\n" + "-" * 60)

for i, entry in enumerate(trajectory, 1):
    print(f"\nIteration {i}:")
    print(f"Solution:\n{entry['attempt']}")

    if entry['reflection']:
        print(f"\nReflection:\n{entry['reflection']}")

    print("-" * 60)

# Expected Output:
# Shows progressive improvement:
# Iteration 1: Basic solution
# Iteration 2: Reflection + improved solution with verification
# Iteration 3: Further refined solution
```

### Exercise 6: Multi-Step Reasoning with Planning

```python
def plan_and_solve(problem, llm):
    """
    Plan first, then execute step by step.

    SOLUTION: Separates planning from execution for better reasoning.
    """
    import re

    # SOLUTION: Generate detailed plan
    plan_prompt = f"""Break this problem down into clear steps:
{problem}

List the steps needed:

Step 1:"""

    plan = llm(plan_prompt)
    print(f"Generated Plan:\n{plan}\n")
    print("=" * 60 + "\n")

    # SOLUTION: Parse and execute plan
    steps = [s.strip() for s in plan.split("\n") if s.strip() and "Step" in s]

    execution_summary = []
    for i, step in enumerate(steps, 1):
        # Clean step description
        step_desc = re.sub(r"^Step\s*\d+:\s*", "", step)

        print(f"Executing Step {i}: {step_desc}")

        # Execute step
        execution_prompt = f"""Context: {problem}

Previous steps: {execution_summary}

Current step: {step_desc}

Execute this step and provide the result:"""

        result = llm(execution_prompt)
        execution_summary.append(f"Step {i}: {step_desc} -> {result}")

        print(f"Result: {result}\n")

    return {
        "plan": plan,
        "execution": execution_summary,
        "final_answer": execution_summary[-1] if execution_summary else None,
    }

# SOLUTION: Mock LLM for planning
def mock_planning_llm(prompt):
    """
    Mock LLM for plan-and-solve.

    SOLUTION: Returns structured plans and step executions.
    """
    if "List the steps" in prompt or "Step 1:" in prompt:
        return """Step 1: Identify the starting number of apples
Step 2: Calculate apples after eating one
Step 3: Calculate apples after buying more
Step 4: Calculate final count after giving away
Step 5: Provide final answer"""

    if "Execute this step" in prompt:
        if "Step 1" in prompt:
            return "Starting with 3 apples"
        elif "Step 2" in prompt:
            return "After eating 1: 3 - 1 = 2 apples"
        elif "Step 3" in prompt:
            return "After buying 5: 2 + 5 = 7 apples"
        elif "Step 4" in prompt:
            return "After giving away 2: 7 - 2 = 5 apples"
        elif "Step 5" in prompt:
            return "Final answer: 5 apples"

    return "Executed"

# SOLUTION: Test Plan-and-Solve
print("\n" + "=" * 60)
print("Plan-and-Solve Test")
print("=" * 60)

problem = "If I have 3 apples and eat 1, then buy 5 more, and give away 2, how many do I have?"

print(f"Problem: {problem}\n")
result = plan_and_solve(problem, mock_planning_llm)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\nPlan had {len(result['execution'])} steps")
print(f"Final answer: {result['final_answer']}")

# Expected Output:
# 5-step plan generated
# Each step executed with result
# Final answer: 5 apples
```

### Exercise 7: Evaluate Reasoning Quality

```python
def evaluate_reasoning_quality(response, ground_truth=None):
    """
    Evaluate quality of reasoning.

    SOLUTION: Checks for reasoning indicators, structure,
    conclusions, and factual correctness.
    """
    scores = {}

    # SOLUTION: Check for reasoning steps
    reasoning_indicators = ["step", "because", "therefore", "since", "first", "then", "next", "finally"]
    has_reasoning = any(indicator in response.lower() for indicator in reasoning_indicators)
    scores["has_reasoning"] = has_reasoning

    # SOLUTION: Check structure
    lines = response.split("\n")
    scores["structure_score"] = min(len(lines) / 5, 1.0)  # More lines = better structure
    scores["line_count"] = len(lines)

    # SOLUTION: Check for conclusion
    conclusion_indicators = ["answer:", "therefore", "so", "result:", "final"]
    has_conclusion = any(indicator in response.lower() for indicator in conclusion_indicators)
    scores["has_conclusion"] = has_conclusion

    # SOLUTION: Check for numerical answers
    import re
    numbers = re.findall(r"\d+", response)
    scores["has_numbers"] = len(numbers) > 0
    scores["number_count"] = len(numbers)

    # SOLUTION: Check factual correctness if ground truth provided
    if ground_truth:
        scores["correctness"] = calculate_similarity(response, ground_truth)

    # Overall score
    weights = {
        "has_reasoning": 0.3,
        "structure_score": 0.3,
        "has_conclusion": 0.2,
        "has_numbers": 0.2,
    }

    scores["overall"] = sum(
        scores.get(key, 0) * weight
        for key, weight in weights.items()
    )

    return scores

def calculate_similarity(response, ground_truth):
    """Calculate similarity between response and ground truth."""
    import re

    # Extract numbers from both
    response_numbers = re.findall(r"\d+", response)
    ground_numbers = re.findall(r"\d+", ground_truth)

    if not response_numbers or not ground_numbers:
        return 0.0

    # Check if final answer matches
    response_final = response_numbers[-1] if response_numbers else None
    ground_final = ground_numbers[-1] if ground_numbers else None

    if response_final == ground_final:
        return 1.0

    # Partial match if numbers overlap
    overlap = set(response_numbers) & set(ground_numbers)
    return len(overlap) / max(len(response_numbers), len(ground_numbers))

# SOLUTION: Batch evaluation
def evaluate_reasoning_batch(responses, ground_truths=None):
    """Evaluate multiple reasoning responses."""

    results = []
    for i, response in enumerate(responses):
        gt = ground_truths[i] if ground_truths else None
        scores = evaluate_reasoning_quality(response, gt)
        results.append(scores)

    # Aggregate
    avg_scores = {
        key: sum(r[key] for r in results) / len(results)
        for key in results[0].keys()
    }

    avg_scores["count"] = len(results)

    return avg_scores

# SOLUTION: Test reasoning quality evaluation
print("\n" + "=" * 60)
print("Reasoning Quality Evaluation Test")
print("=" * 60)

# Test cases
test_responses = [
    """Let me think step by step:
First: Start with 3
Then: Subtract 1 = 2
Next: Add 5 = 7
Finally: Subtract 2 = 5
Answer: 5""",

    """3 apples minus 1 is 2.
2 plus 5 is 7.
7 minus 2 is 5.
The answer is 5.""",

    """5 apples""",  # Minimal response

    """The answer is five.""",  # No numbers
]

ground_truths = ["5", "5", "5", "5"]

print("\nEvaluating individual responses:\n")

for i, (response, gt) in enumerate(zip(test_responses, ground_truths), 1):
    print(f"Response {i}:")
    print(response[:80] + "...")
    scores = evaluate_reasoning_quality(response, gt)
    print(f"Overall Score: {scores['overall']:.2f}")
    print(f"  Has reasoning: {scores['has_reasoning']}")
    print(f"  Structure: {scores['structure_score']:.2f}")
    print(f"  Has conclusion: {scores['has_conclusion']}")
    print(f"  Has numbers: {scores['has_numbers']}")
    print()

# Batch evaluation
print("\n" + "=" * 60)
print("Batch Evaluation Summary")
print("=" * 60)

batch_results = evaluate_reasoning_batch(test_responses, ground_truths)

print(f"\nTotal responses evaluated: {batch_results['count']}")
print(f"Average overall score: {batch_results['overall']:.2f}")
print(f"Average reasoning indicator: {batch_results['has_reasoning']:.2%}")
print(f"Average structure score: {batch_results['structure_score']:.2f}")
print(f"Average conclusion present: {batch_results['has_conclusion']:.2%}")

# Expected Output:
# Response 1: High score (has reasoning, structure, conclusion, numbers)
# Response 2: Medium-high score (has structure, conclusion, numbers)
# Response 3: Low score (minimal, no reasoning steps)
# Response 4: Low score (no numbers, minimal structure)
# Batch average shows overall quality
```

---

**Last Updated:** 2026-02-05
**Status:** ✅ Complete - All tasks completed with solutions
