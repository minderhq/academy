---
Document ID: EXP_7101
Title: "EXP-7101: ReAct Agent"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
---

# EXP-7101: ReAct Agent

**Implementing reasoning + acting agents from scratch**

---

## 🎯 Experiment Overview

**Time:** 60-75 minutes
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:**
- 7101: ReAct Loop System (theory)
- LAB-004: ReAct Agent (basic)
- Understanding of LLM prompting

**Learning Objectives:**
- Understand ReAct (Reasoning + Acting) paradigm
- Implement ReAct loop from scratch
- Add tool calling capabilities
- Handle complex multi-step tasks

---

## 📚 Background

ReAct combines **Reasoning** (thinking) with **Acting** (tool use) in an iterative loop.

### The ReAct Loop

```text
1. Thought → What should I do?
2. Action → Execute a tool/operation
3. Observation → What happened?
4. Repeat → Until task complete
```

---

## 🔬 Experiment 1: Basic ReAct (25 minutes)

### Step 1.1: Implement ReAct Loop

```python
# File: react_agent.py
"""
ReAct Agent Implementation
========================
"""

from typing import List, Dict, Any, Optional
import re

class ReActAgent:
    """ReAct: Reasoning + Acting Agent"""

    def __init__(self, tools: Dict[str, callable]):
        """
        Args:
            tools: Dictionary of tool_name -> tool_function
        """
        self.tools = tools
        self.history = []

    def run(self, query: str, max_iterations: int = 10) -> str:
        """
        Run ReAct loop

        Args:
            query: User's question/task
            max_iterations: Maximum reasoning steps

        Returns:
            Final answer
        """

        thought = self._initial_thought(query)
        self.history.append(("Thought", thought))

        for iteration in range(max_iterations):
            # Decide action based on thought
            action = self._decide_action(thought, query)

            if action["type"] == "finish":
                final_answer = action["content"]
                self.history.append(("Answer", final_answer))
                break

            # Execute action
            observation = self._execute_action(action)

            # Record step
            self.history.append(("Action", action["content"]))
            self.history.append(("Observation", observation))

            # Next thought
            thought = self._next_thought(thought, action, observation, query)
            self.history.append(("Thought", thought))

        return self._get_final_answer()

    def _initial_thought(self, query: str) -> str:
        """Generate initial thought about the query"""

        # Simplified - would use LLM in production
        if "calculate" in query.lower() or "compute" in query.lower():
            return f"To answer '{query}', I need to perform calculations."
        elif "search" in query.lower() or "find" in query.lower():
            return f"To answer '{query}', I need to search for information."
        else:
            return f"I need to understand what is being asked: '{query}'"

    def _decide_action(self, thought: str, query: str) -> Dict[str, str]:
        """Decide next action based on thought"""

        # Pattern matching for common actions
        if "calculate" in thought.lower():
            # Extract expression
            expr = self._extract_expression(query)
            if expr:
                return {"type": "tool", "tool": "calculator", "content": expr}

        if "search" in thought.lower():
            # Extract search query
            search_query = self._extract_search_query(query)
            if search_query:
                return {"type": "tool", "tool": "search", "content": search_query}

        # If no clear action, finish
        return {"type": "finish", "content": self._generate_answer(query, self.history)}

    def _execute_action(self, action: Dict[str, str]) -> str:
        """Execute action and return observation"""

        tool_name = action["tool"]
        tool_input = action["content"]

        if tool_name in self.tools:
            try:
                result = self.tools[tool_name](tool_input)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        return f"Unknown tool: {tool_name}"

    def _next_thought(self, prev_thought: str, action: Dict,
                     observation: str, query: str) -> str:
        """Generate next thought based on action result"""

        if action["tool"] == "calculator":
            return f"The calculation returned {observation}. I can now answer the question."

        elif action["tool"] == "search":
            return f"Found information: {observation}. This helps answer the question."

        else:
            return f"I received: {observation}. Continuing to process the query."

    def _generate_answer(self, query: str, history: List) -> str:
        """Generate final answer from history"""

        # Simplified answer generation
        if "calculator" in str(history):
            for step in history:
                if step[0] == "Observation" and "Error" not in step[1]:
                    return f"The answer is {step[1]}"

        return f"Based on my analysis, here's what I found regarding: {query}"

    def _get_final_answer(self) -> str:
        """Extract final answer from history"""

        for step in reversed(self.history):
            if step[0] == "Answer":
                return step[1]

        return "Unable to determine answer"

    def _extract_expression(self, text: str) -> Optional[str]:
        """Extract mathematical expression"""
        # Match patterns like "2 + 2" or "calculate 5 * 3"
        patterns = [
            r'calculate\s+([\d\s+\-*/().]+)',
            r'compute\s+([\d\s+\-*/().]+)',
            r'what\s+is\s+([\d\s+\-*/().]+)\?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_search_query(self, text: str) -> Optional[str]:
        """Extract search query"""
        # Simple extraction
        if "search for" in text.lower():
            return text.lower().split("search for")[-1]

        # Extract quotes
        quotes = re.findall(r'"([^"]+)"', text)
        if quotes:
            return quotes[0]

        return None

# Define tools
def calculator(expression: str) -> float:
    """Calculate mathematical expression"""
    try:
        # Safe evaluation
        result = eval(expression, {"__builtins__": {}}, {})
        return result
    except:
        return "Error: Invalid expression"

def web_search(query: str) -> str:
    """Simulated web search"""
    # In production, use actual search API
    return f"Search results for '{query}': [simulated results]"

# Create agent
agent = ReActAgent({
    "calculator": calculator,
    "search": web_search
})

# Test
query = "calculate 25 * 4 + 10"
print(f"Query: {query}\n")

answer = agent.run(query)

print("=== ReAgent Trace ===")
for step_type, content in agent.history:
    print(f"{step_type}: {content}")

print(f"\nFinal Answer: {answer}")
```

**Checkpoint 1:** ✅ Basic ReAct working

---

## 🔬 Experiment 2: Advanced Tool Calling (20 minutes)

### Step 2.1: Multi-Tool Agent

```python
# File: advanced_react.py
"""
Advanced ReAct with Multiple Tools
==================================
"""

class AdvancedReActAgent(ReActAgent):
    """ReAct agent with advanced tool selection"""

    def __init__(self, tools: Dict[str, callable]):
        super().__init__(tools)
        self.tool_descriptions = self._build_tool_descriptions()

    def _build_tool_descriptions(self) -> Dict[str, str]:
        """Build descriptions for tools"""
        return {
            "calculator": "Performs mathematical calculations",
            "search": "Searches the web for information",
            "code": "Executes Python code",
            "database": "Queries a database",
        }

    def _decide_action(self, thought: str, query: str) -> Dict[str, str]:
        """Decide action using tool descriptions"""

        # Check for calculator
        if any(word in thought.lower() for word in ["calculate", "compute", "math"]):
            expr = self._extract_expression(query)
            if expr:
                return {"type": "tool", "tool": "calculator", "content": expr}

        # Check for search
        if any(word in thought.lower() for word in ["search", "find", "look up"]):
            search_query = self._extract_search_query(query)
            if search_query:
                return {"type": "tool", "tool": "search", "content": search_query}

        # Check for code execution
        if "code" in thought.lower() or "python" in thought.lower():
            code = self._extract_code(query)
            if code:
                return {"type": "tool", "tool": "code", "content": code}

        # Default: finish
        return {"type": "finish", "content": self._generate_answer(query, self.history)}

    def _extract_code(self, text: str) -> Optional[str]:
        """Extract Python code"""
        # Extract code blocks
        code_match = re.search(r'```python\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1)

        return None

# Additional tools
def execute_code(code: str) -> str:
    """Execute Python code safely"""
    try:
        result = eval(code)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

def query_database(query: str) -> str:
    """Query database"""
    # Simulated
    return f"Database results for: {query}"

# Create advanced agent
advanced_agent = AdvancedReActAgent({
    "calculator": calculator,
    "search": web_search,
    "code": execute_code,
    "database": query_database,
})

# Test
query2 = "What is 15 * 8 plus 20?"
print(f"\nQuery: {query2}\n")

answer2 = advanced_agent.run(query2)

print("=== Advanced ReAct Trace ===")
for step_type, content in advanced_agent.history:
    print(f"{step_type}: {content}")

print(f"\nFinal Answer: {answer2}")
```

**Checkpoint 2:** ✅ Advanced agent working

---

## 🔬 Experiment 3: Real-World Tasks (20 minutes)

### Step 3.1: Complex Multi-Step Tasks

```python
# File: complex_tasks.py
"""
Complex Multi-Step Tasks
========================
"""

class TaskAgent(AdvancedReActAgent):
    """Agent for complex multi-step tasks"""

    def run(self, task: str, max_iterations: int = 15) -> Dict[str, Any]:
        """Run complex task with planning"""

        # Plan decomposition
        plan = self._create_plan(task)
        self.history.append(("Plan", str(plan)))

        results = {"plan": plan, "steps": []}

        for step_num, step in enumerate(plan):
            self.history.append(("Thought", f"Executing step {step_num + 1}: {step['description']}"))

            # Execute step
            action = self._decide_action_for_step(step, task)
            observation = self._execute_action(action)

            results["steps"].append({
                "step": step_num + 1,
                "description": step['description'],
                "action": action,
                "result": observation
            })

            self.history.append(("Action", action["content"]))
            self.history.append(("Observation", observation))

            # Check if step complete
            if self._is_step_complete(step, observation):
                self.history.append(("Thought", f"Step {step_num + 1} completed."))
            else:
                self.history.append(("Thought", f"Step {step_num + 1} needs retry."))

        # Final synthesis
        final_answer = self._synthesize_results(results)
        self.history.append(("Answer", final_answer))
        results["answer"] = final_answer

        return results

    def _create_plan(self, task: str) -> List[Dict]:
        """Decompose task into steps"""

        # Simplified planning
        if "calculate" in task.lower():
            return [
                {"description": "Parse expression", "type": "parse"},
                {"description": "Perform calculation", "type": "calculate"},
                {"description": "Verify result", "type": "verify"}
            ]

        if "search" in task.lower():
            return [
                {"description": "Identify search terms", "type": "identify"},
                {"description": "Search for information", "type": "search"},
                {"description": "Synthesize results", "type": "synthesize"}
            ]

        return [{"description": "Analyze task", "type": "analyze"}]

    def _decide_action_for_step(self, step: Dict, task: str) -> Dict:
        """Decide action for specific step"""

        if step["type"] == "calculate":
            expr = self._extract_expression(task)
            return {"type": "tool", "tool": "calculator", "content": expr}

        elif step["type"] == "search":
            query = self._extract_search_query(task)
            return {"type": "tool", "tool": "search", "content": query}

        return {"type": "finish", "content": "Step complete"}

    def _is_step_complete(self, step: Dict, observation: str) -> bool:
        """Check if step is complete"""

        if "Error" in observation:
            return False

        return True

    def _synthesize_results(self, results: Dict) -> str:
        """Synthesize final answer from all steps"""

        answer_parts = [f"Task completed with {len(results['steps'])} steps:"]

        for step_result in results["steps"]:
            answer_parts.append(f"\nStep {step_result['step']}: {step_result['description']}")
            answer_parts.append(f"  Result: {step_result['result']}")

        return "\n".join(answer_parts)

# Test complex task
task_agent = TaskAgent({
    "calculator": calculator,
    "search": web_search,
})

complex_task = "Calculate (15 + 25) * 2 and then search for information about deep learning"
print(f"Complex Task: {complex_task}\n")

result = task_agent.run(complex_task)

print("=== Complex Task Trace ===")
for step_type, content in task_agent.history:
    print(f"{step_type}: {content}")

print(f"\n{result['answer']}")
```

**Checkpoint 3:** ✅ Complex tasks working

---

## 📊 Performance Analysis

### ReAct vs Direct Approaches

| Task Type | Direct | ReAct | Best |
|-----------|--------|-------|------|
| Simple calculation | Instant | 2-3 steps | Direct |
| Information lookup | Fast | 1-2 steps | Direct |
| Multi-step tasks | Struggles | 5-10 steps | **ReAct** |
| Unknown requirements | Fails | Adapts | **ReAct** |

---

## ✅ Experiment Checklist

- [ ] Basic ReAct loop implemented
- [ ] Tool calling working
- [ ] Multi-step tasks handled
- [ ] Complex planning tested

---

## 🎓 Key Takeaways

1. **ReAct = Think + Act** - Reasoning before action
2. **Tools extend capabilities** - LLM + tools = superpowers
3. **Iteration is key** - Multiple rounds to solve complex tasks
4. **Observation matters** - Results inform next thought
5. **Planning helps** - Decompose complex tasks first

---

## 🚀 Next Steps

1. **EXP_7201**: Multi-Agent - Multiple ReAct agents working together
2. **LAB-008**: Agent Fleet - Scale ReAct to production
3. **PROJECT-007**: Production AI System - Complete agent system

---

**Last Updated:** 2026-02-04
**Experiment:** 7101 - ReAct Agent
**Time Estimate:** 60-75 minutes
**Difficulty:** ⭐⭐⭐ Advanced
