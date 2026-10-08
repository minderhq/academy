---
Document ID: QUICK-REF-VOLUME-7
Title: "Volume 7: Production Systems - Quick Reference"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'agents', 'production']
---

# Volume 7: Production Systems - Quick Reference

**Deploy at Scale** - Agents, multi-agent systems, and production deployment

---

## ReAct Agent

### Concept
```python
# ReAct: Reasoning + Acting
# Loop: Thought → Action → Observation → Thought → ...

class ReActAgent:
    """ReAct agent that reasons and acts"""

    def __init__(self, model, tools):
        self.model = model
        self.tools = {tool.name: tool for tool in tools}

    def run(self, query, max_steps=10):
        """Run ReAct loop"""
        trajectory = []

        # Initial thought
        thought = self._think(query, context="")
        trajectory.append({"type": "thought", "content": thought})

        for step in range(max_steps):
            # Decide action
            action = self._decide_action(thought, query)
            trajectory.append({"type": "action", "content": action})

            # Execute action
            observation = self._execute_action(action)
            trajectory.append({"type": "observation", "content": observation})

            # Check if done
            if self._is_done(observation):
                break

            # Next thought
            thought = self._think(query, context=self._format_trajectory(trajectory))
            trajectory.append({"type": "thought", "content": thought})

        # Final answer
        answer = self._generate_answer(query, trajectory)

        return answer, trajectory

    def _think(self, query, context=""):
        """Generate thought about how to proceed"""
        prompt = f"""Question: {query}

Context: {context}

Thought:"""

        return self.model.generate(prompt)

    def _decide_action(self, thought, query):
        """Decide which action to take"""
        prompt = f"""Question: {query}
Thought: {thought}

Available tools: {list(self.tools.keys())}

Action:"""

        action_str = self.model.generate(prompt)
        # Parse: "search[Paris capital]" → ("search", "Paris capital")
        return self._parse_action(action_str)

    def _execute_action(self, action):
        """Execute action and get observation"""
        tool_name, tool_input = action
        tool = self.tools.get(tool_name)

        if tool:
            return tool.run(tool_input)
        else:
            return f"Error: Unknown tool {tool_name}"

    def _is_done(self, observation):
        """Check if we have the answer"""
        return "[DONE]" in observation or "[FINAL]" in observation

# ReAct benefits:
# - Explicit reasoning (explainable)
# - Tool use (external APIs, databases)
# - Iterative (can correct mistakes)
```

---

## Multi-Agent Systems

### AutoGen Pattern
```python
from autogen import AssistantAgent, UserProxyAgent

# Create agents
assistant = AssistantAgent(
    name="assistant",
    llm_config={
        "model": "gpt-4",
        "api_key": "your-api-key",
    }
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",  # Fully automated
    max_consecutive_auto_reply=5,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
    }
)

# Start conversation
user_proxy.initiate_chat(
    assistant,
    message="Write a Python function to calculate fibonacci numbers"
)

# AutoGen features:
# - Multiple agents with different roles
# - Automatic conversation
# - Code execution
# - Tool use
```

### LangGraph Pattern
```python
from langgraph.graph import END, START, StateGraph
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    current_agent: str

def researcher_node(state):
    """Researcher agent"""
    # Search for information
    search_result = search_tool(state["messages"][-1])

    state["messages"].append({
        "role": "researcher",
        "content": search_result
    })
    state["current_agent"] = "writer"

    return state

def writer_node(state):
    """Writer agent"""
    # Write response based on research
    response = generate_response(state["messages"])

    state["messages"].append({
        "role": "writer",
        "content": response
    })
    state["current_agent"] = END

    return state

# Build graph
workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)

workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", END)

workflow.add_edge(START, "researcher")

app = workflow.compile()

# Run
result = app.invoke({"messages": [{"role": "user", "content": "What is AI?"}]})

# LangGraph benefits:
# - Explicit state management
# - Complex workflows
# - Branching, loops
# - Easy to debug
```

### Collaborative Tasking
```python
class MultiAgentOrchestrator:
    """Orchestrate multiple specialized agents"""

    def __init__(self):
        self.agents = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
            "critic": CriticAgent(),
        }

    def solve(self, task):
        """Solve task using multiple agents"""
        results = {}

        # Phase 1: Research
        research = self.agents["researcher"].run(task)
        results["research"] = research

        # Phase 2: Analysis
        analysis = self.agents["analyst"].run(task, research)
        results["analysis"] = analysis

        # Phase 3: Draft
        draft = self.agents["writer"].run(task, research, analysis)
        results["draft"] = draft

        # Phase 4: Critique and refine
        for i in range(2):  # 2 rounds of refinement
            critique = self.agents["critic"].run(draft)
            draft = self.agents["writer"].refine(draft, critique)

        results["final"] = draft

        return results

# Specialized agents:
# - Better performance on specific tasks
# - Can run in parallel
# - Easier to maintain
```

---

## Tool Calling

### Safe Python Interpreter
```python
import ast
import sys
from io import StringIO
import contextlib

class SafePythonInterpreter:
    """Sandboxed Python execution"""

    def __init__(self, timeout=30, max_output=10000):
        self.timeout = timeout
        self.max_output = max_output

        # Allowed modules (whitelist)
        self.allowed_modules = {
            "math", "random", "datetime", "json",
            "statistics", "fractions", "decimal",
        }

    def execute(self, code):
        """Execute code safely"""
        try:
            # Parse code to check for syntax errors
            tree = ast.parse(code)

            # Check for unsafe operations
            for node in ast.walk(tree):
                # Check for imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_modules:
                            return f"Error: Module '{alias.name}' not allowed"

                # Check for file operations
                if isinstance(node, (ast.ImportFrom, ast.Exec)):
                    return "Error: Operation not allowed"

            # Capture output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()

            try:
                # Execute with timeout
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError("Execution timeout")

                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout)

                # Execute code
                exec_result = exec(code, {"__builtins__": {}}, {})

                signal.alarm(0)

                # Get output
                stdout = sys.stdout.getvalue()
                stderr = sys.stderr.getvalue()

                # Limit output size
                if len(stdout) > self.max_output:
                    stdout = stdout[:self.max_output] + "... (truncated)"

                return stdout if stdout else "Code executed successfully"

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        except TimeoutError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

# Usage
interpreter = SafePythonInterpreter()

result = interpreter.execute("""
import math
result = math.sqrt(16)
print(f"The square root of 16 is {result}")
""")

print(result)  # "The square root of 16 is 4.0"
```

### Tool Definition
```python
from typing import Callable, Any
import inspect

class Tool:
    """Base tool class"""

    def __init__(self, name: str, description: str, function: Callable):
        self.name = name
        self.description = description
        self.function = function

        # Extract function signature
        sig = inspect.signature(function)
        self.parameters = {
            name: {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "string",
                "description": f"Parameter {name}",
                "required": param.default == inspect.Parameter.empty,
            }
            for name, param in sig.parameters.items()
        }

    def run(self, **kwargs):
        """Run the tool"""
        return self.function(**kwargs)

    def to_dict(self):
        """Convert to dictionary for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": [k for k, v in self.parameters.items() if v["required"]],
            },
        }

# Example tools
def search_web(query: str, num_results: int = 5):
    """Search the web for information"""
    # Implementation
    return f"Search results for '{query}': ..."

search_tool = Tool(
    name="search_web",
    description="Search the web for current information",
    function=search_web
)

def calculate(expression: str):
    """Calculate a mathematical expression"""
    try:
        result = eval(expression, {"__builtins__": {}}, {"math": __import__("math")})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

calculate_tool = Tool(
    name="calculate",
    description="Calculate mathematical expressions",
    function=calculate
)

# Tool use in agent
class ToolUsingAgent:
    """Agent that uses tools"""

    def __init__(self, model, tools):
        self.model = model
        self.tools = {tool.name: tool for tool in tools}

    def run(self, query):
        """Run agent with tool use"""
        # Generate function call
        prompt = f"""Available tools: {[t.to_dict() for t in self.tools.values()]}

Query: {query}

Tool call:"""

        response = self.model.generate(prompt)

        # Parse tool call
        tool_name, tool_args = self._parse_tool_call(response)

        # Execute tool
        if tool_name in self.tools:
            result = self.tools[tool_name].run(**tool_args)

            # Generate final response
            final_prompt = f"""Query: {query}
Tool call: {tool_name}({tool_args})
Tool result: {result}

Answer:"""

            return self.model.generate(final_prompt)

        return "Error: Tool not found"
```

---

## Agent Memory

### Long-term Memory
```python
import chromadb
from sentence_transformers import SentenceTransformer

class AgentMemory:
    """Long-term memory for agents"""

    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("agent_memory")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def store(self, content, metadata=None):
        """Store memory"""
        # Create embedding
        embedding = self.embedding_model.encode(content)

        # Store in vector database
        self.collection.add(
            embeddings=[embedding.tolist()],
            documents=[content],
            metadatas=[metadata or {}],
            ids=[str(hash(content))]
        )

    def retrieve(self, query, k=5):
        """Retrieve relevant memories"""
        # Create query embedding
        query_embedding = self.embedding_model.encode(query)

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k
        )

        return results

    def summarize_episode(self, episode):
        """Summarize an episode (interaction)"""
        # Use LLM to summarize
        summary = self.model.generate(f"""
        Summarize the following interaction:

        {episode}

        Summary:""")

        # Store summary
        self.store(summary, metadata={"type": "summary"})

        return summary
```

### Memory Types
```python
import time
class AgentMemorySystem:
    """Complete memory system for agents"""

    def __init__(self):
        # Working memory: Current conversation
        self.working_memory = []

        # Episodic memory: Past interactions
        self.episodic_memory = AgentMemory()

        # Semantic memory: Facts and knowledge
        self.semantic_memory = AgentMemory()

        # Procedural memory: Skills and procedures
        self.procedural_memory = {}

    def add_to_working(self, message):
        """Add to working memory"""
        self.working_memory.append(message)

        # Keep only last N messages
        if len(self.working_memory) > 10:
            self.working_memory = self.working_memory[-10:]

    def store_episode(self, episode):
        """Store episode in episodic memory"""
        self.episodic_memory.store(
            content=episode,
            metadata={"type": "episode", "timestamp": time.time()}
        )

    def learn_fact(self, fact):
        """Store fact in semantic memory"""
        self.semantic_memory.store(
            content=fact,
            metadata={"type": "fact"}
        )

    def learn_skill(self, skill_name, skill_function):
        """Store skill in procedural memory"""
        self.procedural_memory[skill_name] = skill_function

    def recall(self, query):
        """Recall relevant information from all memory types"""
        # Search episodic memory
        episodic = self.episodic_memory.retrieve(query, k=3)

        # Search semantic memory
        semantic = self.semantic_memory.retrieve(query, k=3)

        return {
            "episodic": episodic,
            "semantic": semantic,
            "procedural": list(self.procedural_memory.keys()),
            "working": self.working_memory,
        }
```

---

## Production Deployment

### Kubernetes Deployment
```yaml
# agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-service
  template:
    metadata:
      labels:
        app: agent-service
    spec:
      containers:
      - name: agent
        image: your-registry/agent-service:latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
        env:
        - name: MODEL_NAME
          value: "Qwen/Qwen3-8B"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: agent-service
spec:
  selector:
    app: agent-service
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Monitoring Stack
```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:
    - job_name: 'agent-service'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: agent-service
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

    rule_files:
    - '/etc/prometheus/rules/*.yml'

    # Alert rules
    groups:
    - name: agent_alerts
      rules:
      - alert: HighErrorRate
        expr: rate(agent_errors_total[5m]) > 0.05
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(agent_latency_seconds_bucket[5m])) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }} seconds"

      - alert: GPUHighMemory
        expr: nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "GPU memory high"
          description: "GPU memory usage is {{ $value }}%"
```

### Cost Optimization
```python
# Cost optimization strategies

COST_OPTIMIZATION = {
    "model_selection": {
        "strategy": "Use smallest model that works",
        "example": "Use 7B instead of 70B for simple tasks",
        "savings": "10x cost reduction",
    },
    "quantization": {
        "strategy": "Use quantized models",
        "example": "4-bit quantization",
        "savings": "4x memory, 2x speedup",
    },
    "batching": {
        "strategy": "Batch requests",
        "example": "Process 32 requests at once",
        "savings": "5-10x throughput improvement",
    },
    "caching": {
        "strategy": "Cache common queries",
        "example": "Redis cache with 1-hour TTL",
        "savings": "50-80% cache hit rate",
    },
    "spot_instances": {
        "strategy": "Use spot instances for non-critical",
        "example": "Spot GPU instances",
        "savings": "70-90% cost reduction",
    },
    "autoscaling": {
        "strategy": "Scale based on load",
        "example": "0-10 replicas based on requests/sec",
        "savings": "Scale to zero when idle",
    },
}

# Cost calculation
def calculate_cost_per_1k_requests(
    model_size="7B",
    quantization="4bit",
    batch_size=32,
    cache_hit_rate=0.5,
):
    """
    Estimate cost per 1000 requests

    Assumptions:
    - A100 GPU: $1.50/hour
    - Throughput: 100 tokens/sec (7B, 4-bit, batch=32)
    - Average request: 500 tokens
    """
    # Throughput
    tokens_per_sec = 100
    requests_per_sec = tokens_per_sec / 500

    # Cache
    effective_requests_per_sec = requests_per_sec * (1 + cache_hit_rate)

    # Hourly requests
    requests_per_hour = effective_requests_per_sec * 3600

    # Cost per hour
    cost_per_hour = 1.50

    # Cost per 1000 requests
    cost_per_1k = (cost_per_hour / requests_per_hour) * 1000

    return {
        "cost_per_1k_requests_usd": round(cost_per_1k, 4),
        "requests_per_hour": int(requests_per_hour),
        "monthly_cost_for_1M": round(cost_per_1k * 1000, 2),
    }

# Example
print(calculate_cost_per_1k_requests())
# {'cost_per_1k_requests_usd': 0.0083, 'requests_per_hour': 180000, 'monthly_cost_for_1M': 8.30}
```

---

## Volume 7 Checklist

- [ ] Implement ReAct agent
- [ ] Build multi-agent system
- [ ] Use safe code execution
- [ ] Define tools for agents
- [ ] Implement agent memory
- [ ] Deploy to production
- [ ] Set up monitoring
- [ ] Optimize costs
- [ ] Handle errors gracefully

---

## Next Steps

1. Complete LAB-004: ReAct Agent
2. Complete LAB-008: Agent Fleet
3. Complete LAB-009: Production Deployment
4. Build production agent system

---

**Volume:** 7 - Production Systems

**Estimated Time:** 45-50 hours
