# LAB 004: Building ReAct Agents

**Prerequisites:** Tutorial 001 (Hello LLM), Tutorial 002 (Docker Essentials), LAB 001 (Docker & LLM), LAB 002 (RAG Implementation)
**Time:** 4 hours
**Difficulty:** ⭐⭐⭐ Advanced

> **⚠️ EDUCATIONAL CODE - SECURITY WARNING:**
>
> This lab builds AI agents that can **execute code and make API calls**. These are **educational examples** that:
> - **LACK sandboxing** - code execution can access your system
> - **LACK authentication** - anyone can call your agent
> - **LACK input sanitization** - prompt injection is possible
> - **LACK rate limiting** - can be abused for resource exhaustion
>
> **🚨 NEVER deploy these examples to public internet without security hardening!**
>
> **For production agents**, see:
> - **[7501: Prompt Injection Defense](../../phases/phase7-agentic/7500-security/7501-Prompt-Injection-Defense.md)**
> - **[7502: PII Redaction](../../phases/phase7-agentic/7500-security/7502-PII-Redaction.md)**
> - **[7503: Adversarial Attacks](../../phases/phase7-agentic/7500-security/7503-Adversarial-Attacks.md)**
> - **[LAB-013: Advanced Function Calling](./LAB-013-Advanced-Function-Calling.md)**
>
> Use this lab to **learn agent architecture**. Add security before deployment.

---

## Lab Objectives

After completing this lab, you will be able to:
- ✅ Understand the ReAct (Reasoning + Acting) pattern
- ✅ Build agents that can reason before acting
- ✅ Implement tool calling for agents
- ✅ Create multi-step reasoning chains
- ✅ Add memory to agents
- ✅ Deploy agents as API services

---

## Setup Instructions

```bash
# Create lab directory
mkdir ~/lab-004-react
cd ~/lab-004-react

# Create directory structure
mkdir -p services/agent
mkdir -p services/tools
mkdir -p data/memory
```

---

## Exercise 1: Understanding ReAct Pattern (30 minutes)

### Task: Learn the ReAct loop structure

**ReAct = Reasoning + Acting**

The pattern follows this loop:
1. **Thought:** Reason about what to do
2. **Action:** Choose and execute a tool
3. **Observation:** Observe the result
4. **Repeat** until you have the answer

```python
# ~/lab-004-react/examples/react_basics.py
from typing import List, Dict, Any, Optional
import requests
import json

class ReActLoop:
    """Basic ReAct loop implementation"""

    def __init__(self, llm_url: str = "http://localhost:11434"):
        self.llm_url = llm_url
        self.history = []

    def think(self, query: str) -> str:
        """Generate thought about what to do"""

        prompt = f"""You are a helpful assistant. Think step by step.

Question: {query}

Provide a brief thought about what information you need and what steps you should take.
Thought:"""

        response = requests.post(
            f"{self.llm_url}/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )

        return response.json().get("response", "").strip()

    def decide_action(self, query: str, thought: str) -> Dict[str, Any]:
        """Decide what action to take"""

        prompt = f"""Based on your thought, decide what action to take.

Question: {query}
Thought: {thought}

Available actions:
- search: Search for information online
- calculate: Perform a calculation
- code: Execute Python code
- answer: You have enough information to answer

Respond with ONLY the action name and parameters in JSON format:
{{"action": "action_name", "params": {{"param": "value"}}}}

Response:"""

        response = requests.post(
            f"{self.llm_url}/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )

        result = response.json().get("response", "").strip()

        # Parse JSON from response
        try:
            # Extract JSON from response
            start = result.find("{")
            end = result.rfind("}") + 1
            action_dict = json.loads(result[start:end])
            return action_dict
        except:
            # If parsing fails, default to answering
            return {"action": "answer", "params": {}}

    def execute_action(self, action: Dict[str, Any]) -> str:
        """Execute the chosen action"""

        action_name = action.get("action")
        params = action.get("params", {})

        if action_name == "search":
            return self._search(params.get("query", ""))
        elif action_name == "calculate":
            return self._calculate(params.get("expression", ""))
        elif action_name == "code":
            return self._execute_code(params.get("code", ""))
        elif action_name == "answer":
            return "READY_TO_ANSWER"
        else:
            return f"Unknown action: {action_name}"

    def _search(self, query: str) -> str:
        """Simulated search (in production, use real search API)"""
        return f"Search results for: {query}\n- Result 1: ...\n- Result 2: ..."

    def _calculate(self, expression: str) -> str:
        """Perform calculation"""
        try:
            result = eval(expression)
            return str(result)
        except:
            return "Error in calculation"

    def _execute_code(self, code: str) -> str:
        """Execute Python code (sandboxed using RestrictedPython)"""

        # ⚠️ SECURITY WARNING: eval() is DANGEROUS in production!
        # For educational purposes only. In production, use:
        # - RestrictedPython: https://github.com/zopefoundation/RestrictedPython
        # - PyPy sandbox: https://doc.pypy.org/en/latest/sandbox.html
        # - Docker containers with resource limits
        # - Separate microservices for code execution

        try:
            # VERY basic safety checks (NOT sufficient for production)
            dangerous = ['import', 'exec', 'eval', 'open', 'file', '__import__']
            if any(d in code for d in dangerous):
                return "Error: Code contains unsafe operations (not allowed in this demo)"

            # Create restricted globals
            safe_globals = {
                "__builtins__": {
                    "abs": abs, "min": min, "max": max, "sum": sum,
                    "pow": pow, "round": round, "int": int, "float": float,
                    "len": len, "range": range, "list": list, "dict": dict,
                    "str": str, "bool": bool, "tuple": tuple
                }
            }

            result = eval(code, safe_globals, {})
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    def run(self, query: str, max_steps: int = 5) -> str:
        """Run the ReAct loop"""

        print(f"\n{'='*60}")
        print(f"Question: {query}")
        print(f"{'='*60}\n")

        for step in range(max_steps):
            # Step 1: Think
            thought = self.think(query)
            print(f"[Step {step+1}] Thought: {thought}")

            # Step 2: Decide action
            action = self.decide_action(query, thought)
            print(f"[Step {step+1}] Action: {action['action']}")

            # Step 3: Execute
            observation = self.execute_action(action)
            print(f"[Step {step+1}] Observation: {observation}")

            # Step 4: Check if done
            if action["action"] == "answer":
                print(f"\n{'='*60}")
                return self._generate_answer(query, self.history)

            # Store in history
            self.history.append({
                "thought": thought,
                "action": action,
                "observation": observation
            })

        return "Max steps reached without answer"

    def _generate_answer(self, query: str, history: List[Dict]) -> str:
        """Generate final answer based on reasoning"""

        context = "\n".join([
            f"Thought: {h['thought']}\nObservation: {h['observation']}"
            for h in history
        ])

        prompt = f"""Based on your reasoning, answer the question.

Question: {query}

Your reasoning process:
{context}

Provide a clear, concise answer:"""

        response = requests.post(
            f"{self.llm_url}/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )

        answer = response.json().get("response", "").strip()
        print(f"Answer: {answer}")
        print(f"{'='*60}\n")

        return answer

# Test the ReAct loop
if __name__ == "__main__":
    # Start Ollama first
    # docker run -d --name ollama -p 11434:11434 ollama/ollama
    # docker exec ollama ollama pull mistral

    agent = ReActLoop(llm_url="http://localhost:11434")

    # Test questions
    questions = [
        "What is 123 multiplied by 456?",
        "Calculate 15% of 250",
        "Write a Python function to check if a number is prime"
    ]

    for question in questions:
        agent.run(question)
```

### ✅ Checkpoint: Exercise 1
**Verify:** You understand the Think → Act → Observe loop

---

## Exercise 2: Tool System (45 minutes)

### Task: Build a comprehensive tool system

```python
# ~/lab-004-react/services/tools/tool_registry.py
from typing import Dict, Any, Callable, List
from abc import ABC, abstractmethod
import subprocess
import requests
import json

class Tool(ABC):
    """Base class for all tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool"""
        pass

class CalculatorTool(Tool):
    """Perform mathematical calculations"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Perform mathematical calculations. Use 'expression' parameter."

    def execute(self, expression: str) -> str:
        try:
            # Safe evaluation (in production, use proper parser)
            allowed_names = {
                "abs": abs, "min": min, "max": max, "sum": sum,
                "pow": pow, "round": round
            }
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"Result: {result}"
        except Exception as e:
            return f"Calculation error: {str(e)}"

class WebSearchTool(Tool):
    """Search the web (simulated)"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for information. Use 'query' parameter."

    def execute(self, query: str) -> str:
        # In production, integrate with real search API
        # For now, return simulated results
        return f"""Search results for '{query}':
1. Wikipedia: {query} - Overview and information
2. Documentation: Technical details about {query}
3. Articles: Latest news and discussions about {query}"""

class CodeExecutorTool(Tool):
    """Execute Python code"""

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return "Execute Python code. Use 'code' parameter. WARNING: Limited functionality."

    def execute(self, code: str) -> str:
        try:
            # Capture output
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            # Execute (limited for safety)
            exec(code, {"__builtins__": {"print": print, "range": range, "len": len}})

            # Get output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

            return output if output else "Code executed successfully (no output)"
        except Exception as e:
            return f"Execution error: {str(e)}"

class FileReadTool(Tool):
    """Read file contents"""

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read contents of a file. Use 'path' parameter."

    def execute(self, path: str) -> str:
        try:
            with open(path, 'r') as f:
                content = f.read()
            return f"File content:\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

class DateTimeTool(Tool):
    """Get current date and time"""

    @property
    def name(self) -> str:
        return "datetime"

    @property
    def description(self) -> str:
        return "Get current date and time. No parameters needed."

    def execute(self) -> str:
        from datetime import datetime
        now = datetime.now()
        return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

class ToolRegistry:
    """Registry for all available tools"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools"""

        tools = [
            CalculatorTool(),
            WebSearchTool(),
            CodeExecutorTool(),
            FileReadTool(),
            DateTimeTool()
        ]

        for tool in tools:
            self.register(tool)

    def register(self, tool: Tool):
        """Register a new tool"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        """List all available tools"""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    def execute(self, tool_name: str, **kwargs) -> str:
        """Execute a tool"""
        tool = self.get(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found"
        return tool.execute(**kwargs)

# Test the tool system
if __name__ == "__main__":
    registry = ToolRegistry()

    print("Available tools:")
    for tool in registry.list_tools():
        print(f"- {tool['name']}: {tool['description']}")

    print("\n--- Testing tools ---\n")

    # Test calculator
    print("Calculator:")
    print(registry.execute("calculator", expression="2 * (3 + 4)"))

    # Test datetime
    print("\nDatetime:")
    print(registry.execute("datetime"))

    # Test code executor
    print("\nCode Executor:")
    print(registry.execute("code_executor", code="print(sum(range(5)))"))
```

### ✅ Checkpoint: Exercise 2
**Verify:** Tool registry can execute all tools correctly

---

## Exercise 3: Enhanced ReAct Agent (60 minutes)

### Task: Build a production-ready ReAct agent

```python
# ~/lab-004-react/services/agent/react_agent.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
import json
from tool_registry import ToolRegistry

app = FastAPI(title="ReAct Agent Service")

# Configuration
LLM_URL = "http://ollama:11434"
MAX_STEPS = 5

# Initialize tool registry
tool_registry = ToolRegistry()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    session_id: str
    max_steps: int = 5

class ToolCall(BaseModel):
    name: str
    params: Dict[str, Any]

class ReasoningStep(BaseModel):
    step: int
    thought: str
    action: str
    observation: str

class ChatResponse(BaseModel):
    response: str
    reasoning_steps: List[ReasoningStep]
    tools_used: List[str]

class ReActAgent:
    """Production ReAct Agent with memory and tools"""

    def __init__(self):
        self.memory = {}  # Session memory
        self.tool_registry = tool_registry

    def run(self, messages: List[Message], session_id: str,
             max_steps: int = MAX_STEPS) -> ChatResponse:
        """Run ReAct loop"""

        reasoning_steps = []
        tools_used = []

        # Get last message
        query = messages[-1].content

        # Load conversation history
        history = self.memory.get(session_id, messages)

        for step in range(max_steps):
            # Step 1: Think
            thought = self._think(query, reasoning_steps)
            print(f"[Step {step+1}] Thought: {thought}")

            # Step 2: Plan action
            action = self._plan_action(query, thought, reasoning_steps)
            print(f"[Step {step+1}] Action: {action['tool']}")

            # Step 3: Execute
            observation = self._execute_action(action)
            print(f"[Step {step+1}] Observation: {observation}")

            # Record step
            reasoning_steps.append(ReasoningStep(
                step=step+1,
                thought=thought,
                action=action['tool'],
                observation=observation[:200]  # Truncate for display
            ))

            # Track tools
            if action['tool'] not in tools_used and action['tool'] != 'answer':
                tools_used.append(action['tool'])

            # Step 4: Check if done
            if action['tool'] == 'answer':
                break

        # Generate final response
        response = self._generate_response(query, reasoning_steps, history)

        # Save to memory
        self.memory[session_id] = history + [
            Message(role="user", content=query),
            Message(role="assistant", content=response)
        ]

        return ChatResponse(
            response=response,
            reasoning_steps=reasoning_steps,
            tools_used=tools_used
        )

    def _think(self, query: str, previous_steps: List[ReasoningStep]) -> str:
        """Generate thought about current state"""

        context = self._build_context(query, previous_steps)

        prompt = f"""You are a helpful AI assistant. Think step by step about what to do.

{context}

Provide a brief thought about what you should do next.
Thought:"""

        response = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False}
        )

        return response.json().get("response", "").strip()

    def _plan_action(self, query: str, thought: str,
                     previous_steps: List[ReasoningStep]) -> Dict[str, Any]:
        """Plan next action"""

        tools_list = self.tool_registry.list_tools()
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in tools_list
        ])

        context = self._build_context(query, previous_steps)

        prompt = f"""You are a helpful AI assistant. Based on your thought, decide what to do next.

{context}

Available tools:
{tools_desc}

Respond with a JSON object:
{{"tool": "tool_name", "params": {{"param": "value"}}}}

If you have enough information to answer, use tool "answer" with empty params.

Response:"""

        response = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False}
        )

        result = response.json().get("response", "").strip()

        # Parse JSON
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            action = json.loads(result[start:end])
        except:
            action = {"tool": "answer", "params": {}}

        return action

    def _execute_action(self, action: Dict[str, Any]) -> str:
        """Execute the planned action"""

        tool_name = action.get("tool", "answer")
        params = action.get("params", {})

        if tool_name == "answer":
            return "READY_TO_ANSWER"

        return self.tool_registry.execute(tool_name, **params)

    def _generate_response(self, query: str,
                          reasoning_steps: List[ReasoningStep],
                          history: List[Message]) -> str:
        """Generate final response"""

        context = "\n".join([
            f"Thought: {s.thought}\nAction: {s.action}\nObservation: {s.observation}"
            for s in reasoning_steps
        ])

        prompt = f"""You are a helpful AI assistant. Based on your reasoning, answer the user's question.

Question: {query}

Your reasoning process:
{context}

Provide a clear, helpful answer:"""

        response = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False}
        )

        return response.json().get("response", "").strip()

    def _build_context(self, query: str,
                       previous_steps: List[ReasoningStep]) -> str:
        """Build context for LLM"""

        if not previous_steps:
            return f"Question: {query}"

        steps_text = "\n".join([
            f"Step {s.step}:\n  Thought: {s.thought}\n  Action: {s.action}\n  Observation: {s.observation}"
            for s in previous_steps
        ])

        return f"""Question: {query}

Previous steps:
{steps_text}"""

# Initialize agent
agent = ReActAgent()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with ReAct agent"""

    return agent.run(
        messages=request.messages,
        session_id=request.session_id,
        max_steps=request.max_steps
    )

@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {"tools": tool_registry.list_tools()}

@app.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    """Clear session memory"""
    if session_id in agent.memory:
        del agent.memory[session_id]
        return {"status": "cleared"}
    return {"status": "not_found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

### Create Dockerfile:

```dockerfile
# ~/lab-004-react/services/agent/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["uvicorn", "react_agent:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Requirements:

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
requests==2.31.0
pydantic==2.5.3
```

### ✅ Checkpoint: Exercise 3
**Verify:** ReAct agent can reason and use tools

---

## Exercise 4: Docker Deployment (30 minutes)

### Task: Deploy ReAct agent with Docker Compose

```yaml
# ~/lab-004-react/docker-compose.yml
version: "3.8"

services:
  # Ollama LLM
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./data/models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - react-net

  # ReAct Agent Service
  agent:
    build: ./services/agent
    container_name: react-agent
    ports:
      - "8002:8002"
    environment:
      - LLM_URL=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - react-net

networks:
  react-net:
    driver: bridge
```

### Deploy:

```bash
cd ~/lab-004-react

# Pull model first
docker run --rm -v ~/lab-004-react/data/models:/root/.ollama \
  ollama/ollama ollama pull mistral

# Start services
docker-compose up -d --build

# Check logs
docker-compose logs -f agent
```

### ✅ Checkpoint: Exercise 4
**Verify:** Agent service is running and accessible

---

## Exercise 5: Test the Agent (30 minutes)

### Task: Test various scenarios

```python
# ~/lab-004-react/test_agent.py
import requests
import json

AGENT_URL = "http://localhost:8002"

def chat(message: str, session_id: str = "test"):
    """Send message to agent"""

    response = requests.post(
        f"{AGENT_URL}/chat",
        json={
            "messages": [{"role": "user", "content": message}],
            "session_id": session_id,
            "max_steps": 5
        }
    )

    return response.json()

def print_result(result: dict):
    """Pretty print result"""

    print(f"\n{'='*60}")
    print(f"Response: {result['response']}")
    print(f"\nReasoning Steps ({len(result['reasoning_steps'])}):")

    for step in result['reasoning_steps']:
        print(f"\n  Step {step['step']}:")
        print(f"    Thought: {step['thought']}")
        print(f"    Action: {step['action']}")
        print(f"    Observation: {step['observation']}")

    if result['tools_used']:
        print(f"\nTools Used: {', '.join(result['tools_used'])}")

    print(f"{'='*60}\n")

# Test 1: Calculation
print("Test 1: Mathematical Calculation")
result = chat("What is 47 multiplied by 53?")
print_result(result)

# Test 2: Information seeking
print("Test 2: Information Seeking")
result = chat("What's the current date and time?")
print_result(result)

# Test 3: Multi-step reasoning
print("Test 3: Multi-step Reasoning")
result = chat("Calculate 15% of 250, then add 100 to the result")
print_result(result)

# Test 4: Code execution
print("Test 4: Code Execution")
result = chat("Write Python code to calculate the sum of numbers from 1 to 10")
print_result(result)

# Test 5: Memory test
print("Test 5: Memory Test")
chat("My favorite color is blue", session_id="memory-test")
result = chat("What is my favorite color?", session_id="memory-test")
print_result(result)
```

### ✅ Checkpoint: Exercise 5
**Verify:** Agent handles all test cases correctly

---

## Exercise 6: Advanced Features (45 minutes)

### Task: Add advanced capabilities

```python
# ~/lab-004-react/services/agent/advanced_features.py
from typing import List, Dict, Any, Optional
import hashlib
import json
from datetime import datetime

class AdvancedReActAgent(ReActAgent):
    """ReAct agent with advanced features"""

    def __init__(self):
        super().__init__()
        self.long_term_memory = {}  # Persistent memory
        self.reflections = {}  # Learned patterns

    def run_with_reflection(self, messages: List[Message], session_id: str,
                            max_steps: int = MAX_STEPS) -> ChatResponse:
        """Run with self-reflection"""

        # Run normal ReAct
        result = super().run(messages, session_id, max_steps)

        # Reflect on the result
        reflection = self._reflect(messages[-1].content, result)

        # Store learning
        query_hash = hashlib.md5(messages[-1].content.encode()).hexdigest()
        self.reflections[query_hash] = {
            "query": messages[-1].content,
            "reflection": reflection,
            "tools_used": result.tools_used,
            "timestamp": datetime.now().isoformat()
        }

        return result

    def _reflect(self, query: str, result: ChatResponse) -> str:
        """Reflect on the reasoning process"""

        prompt = f"""You just answered a question. Reflect on your reasoning.

Question: {query}

Your reasoning had {len(result.reasoning_steps)} steps and used {len(result.tools_used)} tools.

What did you do well? What could you improve?
Reflection:"""

        response = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False}
        )

        return response.json().get("response", "").strip()

    def suggest_improvements(self, session_id: str) -> List[str]:
        """Suggest improvements based on reflections"""

        suggestions = []

        for reflection in self.reflections.values():
            if "could improve" in reflection["reflection"].lower():
                suggestions.append(reflection["reflection"])

        return list(set(suggestions))[:5]

    def export_memory(self, session_id: str) -> Dict:
        """Export session memory"""

        return {
            "session_id": session_id,
            "conversation": self.memory.get(session_id, []),
            "reflections": list(self.reflections.values()),
            "timestamp": datetime.now().isoformat()
        }

    def import_memory(self, memory_data: Dict):
        """Import session memory"""

        session_id = memory_data["session_id"]
        self.memory[session_id] = [
            Message(**msg) for msg in memory_data["conversation"]
        ]

        for ref in memory_data.get("reflections", []):
            query_hash = hashlib.md5(ref["query"].encode()).hexdigest()
            self.reflections[query_hash] = ref
```

### Add API endpoints for advanced features:

```python
# Add to react_agent.py

@app.post("/chat/reflect", response_model=ChatResponse)
async def chat_with_reflection(request: ChatRequest):
    """Chat with self-reflection"""
    advanced_agent = AdvancedReActAgent()
    return advanced_agent.run_with_reflection(
        messages=request.messages,
        session_id=request.session_id,
        max_steps=request.max_steps
    )

@app.get("/memory/{session_id}/export")
async def export_memory(session_id: str):
    """Export session memory"""
    advanced_agent = AdvancedReActAgent()
    return advanced_agent.export_memory(session_id)

@app.post("/memory/import")
async def import_memory(memory_data: Dict):
    """Import session memory"""
    advanced_agent = AdvancedReActAgent()
    advanced_agent.import_memory(memory_data)
    return {"status": "imported"}

@app.get("/suggestions/{session_id}")
async def get_suggestions(session_id: str):
    """Get improvement suggestions"""
    advanced_agent = AdvancedReActAgent()
    return {"suggestions": advanced_agent.suggest_improvements(session_id)}
```

### ✅ Checkpoint: Exercise 6
**Verify:** Advanced features working correctly

---

## Final Challenge: Multi-Agent Collaboration (30 minutes)

### Task: Create multiple specialized agents

```python
# ~/lab-004-react/services/agent/multi_agent.py
from typing import List, Dict
import requests

class SpecialistAgent:
    """Specialized agent for specific domain"""

    def __init__(self, name: str, specialty: str, system_prompt: str):
        self.name = name
        self.specialty = specialty
        self.system_prompt = system_prompt

    def query(self, message: str) -> str:
        """Query this specialist agent"""

        prompt = f"""You are a specialist in {self.specialty}.
{self.system_prompt}

User question: {message}

Provide a helpful answer:"""

        response = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False}
        )

        return response.json().get("response", "").strip()

class CoordinatorAgent:
    """Coordinates multiple specialist agents"""

    def __init__(self):
        # Create specialists
        self.specialists = [
            SpecialistAgent(
                "Mathematician",
                "mathematics and calculations",
                "You excel at solving mathematical problems and performing calculations."
            ),
            SpecialistAgent(
                "Programmer",
                "programming and code",
                "You excel at writing and explaining code in various programming languages."
            ),
            SpecialistAgent(
                "Researcher",
                "information gathering and research",
                "You excel at finding and synthesizing information from various sources."
            )
        ]

    def route_query(self, query: str) -> str:
        """Route query to appropriate specialist"""

        # Classify query
        prompt = f"""You are a coordinator. Route the user's question to the appropriate specialist.

Question: {query}

Available specialists:
- Mathematician: For mathematical problems and calculations
- Programmer: For programming and code questions
- Researcher: For information and research questions

Respond with only the specialist name:"""

        response = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False}
        )

        specialist_name = response.json().get("response", "").strip().lower()

        # Find matching specialist
        for specialist in self.specialists:
            if specialist.name.lower() in specialist_name:
                print(f"Routing to: {specialist.name}")
                return specialist.query(query)

        # Fallback: use first specialist
        print(f"No exact match, using: {self.specialists[0].name}")
        return self.specialists[0].query(query)

# Test multi-agent system
if __name__ == "__main__":
    coordinator = CoordinatorAgent()

    print("Testing Multi-Agent System\n")

    questions = [
        "What is the derivative of x²?",
        "Write a function to reverse a list in Python",
        "What are the main causes of climate change?"
    ]

    for question in questions:
        print(f"\nQuestion: {question}")
        answer = coordinator.route_query(question)
        print(f"Answer: {answer}\n")
```

### ✅ Final Checkpoint
**Test:** Multi-agent system routes questions correctly

---

## 🎓 Lab Completion Checklist

```
[ ] Exercise 1: Understanding ReAct Pattern
[ ] Exercise 2: Tool System
[ ] Exercise 3: Enhanced ReAct Agent
[ ] Exercise 4: Docker Deployment
[ ] Exercise 5: Test the Agent
[ ] Exercise 6: Advanced Features
[ ] Final Challenge: Multi-Agent Collaboration
```

---

## 📚 Post-Lab Reading

- **[7101: ReAct Loop System](../../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)** - Deep dive into ReAct
- **[7102: Planning Decomposition](../../phases/phase7-agentic/7100-architecture/7102-Planning-Decomposition.md)** - Advanced planning
- **[7201: AutoGen vs LangGraph](../../phases/phase7-agentic/7200-tools/7303-Framework-Comparison.md)** - Multi-agent frameworks
- **[PROJECT 001: AI Assistant](../learning-resources/projects/PROJECT-001-AI-Assistant.md)** - Complete ReAct agent in production

---

## 🏆 Lab Badge

**Earned:** ReAct Agent Badge 🏅

Next: **[LAB 005: GraphRAG Implementation](LAB-005-GraphRAG.md)**
