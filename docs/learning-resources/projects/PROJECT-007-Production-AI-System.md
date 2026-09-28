---
Document ID: PROJECT-007
Title: "CAPSTONE PROJECT 007: Deploy Production AI System"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# CAPSTONE PROJECT 007: Deploy Production AI System

**Build and deploy a complete AI system at scale**

---

## 🎯 Project Overview

Deploy a complete AI system to production with:
- Multi-agent orchestration
- Real-time streaming responses
- Scalable microservices architecture
- Monitoring, logging, and observability
- CI/CD pipelines
- Security and safety guardrails

**Estimated Time:** 25-30 hours
**Difficulty:** ⭐⭐⭐⭐ Expert

---

## 📋 Prerequisites

Complete these before starting:
- ✅ 7101: ReAct Loop System
- ✅ 7102: Planning Decomposition
- ✅ 7201: Tool Calling
- ✅ 7301: Orchestration
- ✅ 7401: Long-term Memory
- ✅ LAB-004: ReAct Agent
- ✅ LAB-008: Agent Fleet
- ✅ LAB-009: Production Deployment

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Production AI System Architecture                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Frontend Layer                               │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ Web App      │  │ Mobile App   │  │ API Clients  │              │    │
│  │  │ (React)      │  │ (iOS/Android)│  │ (REST/WS)    │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      API Gateway (Kong/Envoy)                        │    │
│  │  - Rate Limiting  - Authentication  - SSL Termination               │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Service Mesh (Istio)                           │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                               │                                             │
│         ┌─────────────────────┼─────────────────────┐                     │
│         │                     │                     │                     │
│         ▼                     ▼                     ▼                     │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐                   │
│  │ Agent      │      │ RAG        │      │ LLM        │                   │
│  │ Service    │      │ Service    │      │ Service    │                   │
│  │            │      │            │      │            │                   │
│  │ - ReAct    │      │ - Vector   │      │ - vLLM     │                   │
│  │ - Planning │      │ - Graph    │      │ - TGI      │                   │
│  │ - Memory   │      │ - Search   │      │ - Quantize │                   │
│  └────────────┘      └────────────┘      └────────────┘                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Data & State Layer                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ PostgreSQL   │  │ Redis        │  │ Vector DB    │              │    │
│  │  │ (User/Data)  │  │ (Cache/Queue)│  │ (Qdrant)     │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   Observability & Monitoring                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ Prometheus   │  │ Grafana      │  │ ELK Stack    │              │    │
│  │  │ (Metrics)    │  │ (Dashboards) │  │ (Logs)       │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Multi-Agent System (6 hours)

### 1.1 Agent Orchestrator

```python
# File: agents/orchestrator.py
"""
Multi-Agent Orchestrator
========================
"""

from typing import List, Dict, Any
import asyncio
from langgraph.graph import StateGraph

class AgentOrchestrator:
    """Orchestrate multiple specialized agents"""

    def __init__(self):
        self.agents = {}
        # LangChain 1.x: tools are bound inside each agent via
        # create_agent (or a ToolNode when wiring a StateGraph) -
        # the 0.x standalone ToolExecutor is removed.

    def register_agent(self, name: str, agent: 'BaseAgent'):
        """Register an agent"""
        self.agents[name] = agent

    async def route(self, query: str, context: Dict) -> str:
        """Route query to appropriate agent"""

        # Analyze query
        agent_type = await self._classify_query(query)

        # Route to specialized agent
        if agent_type in self.agents:
            return await self.agents[agent_type].execute(query, context)

        # Default to general agent
        return await self.agents['general'].execute(query, context)

    async def _classify_query(self, query: str) -> str:
        """Classify query to determine agent"""

        # Simple rule-based classification
        if any(word in query.lower() for word in ['code', 'python', 'function']):
            return 'coder'
        elif any(word in query.lower() for word in ['search', 'find', 'lookup']):
            return 'researcher'
        elif any(word in query.lower() for word in ['calculate', 'compute', 'math']):
            return 'analyst'
        else:
            return 'general'

class BaseAgent:
    """Base agent class"""

    def __init__(self, name: str, tools: list[Dict]):
        self.name = name
        self.tools = tools
        self.memory = {}

    async def execute(self, query: str, context: Dict) -> str:
        """Execute agent's task"""

        # Plan
        plan = await self._plan(query, context)

        # Execute tools
        results = []
        for step in plan:
            result = await self._execute_tool(step)
            results.append(result)

        # Synthesize
        response = await self._synthesize(query, results)

        return response

    async def _plan(self, query: str, context: Dict) -> list[Dict]:
        """Plan execution steps"""
        raise NotImplementedError

    async def _execute_tool(self, tool: Dict) -> Any:
        """Execute a tool"""
        tool_name = tool['name']
        tool_args = tool.get('args', {})

        # Execute tool (with safety checks)
        return await self._safe_execute(tool_name, tool_args)

    async def _safe_execute(self, tool_name: str, args: Dict) -> Any:
        """Execute tool with safety checks"""
        # Validate inputs
        # Sandbox execution
        # Timeout handling
        pass

    async def _synthesize(self, query: str, results: List) -> str:
        """Synthesize results into response"""
        raise NotImplementedError
```

### 1.2 Specialized Agents

```python
# File: agents/specialized.py
"""
Specialized Agents
==================
"""

class CoderAgent(BaseAgent):
    """Code generation and analysis agent"""

    def __init__(self):
        tools = [
            {'name': 'execute_python', 'description': 'Execute Python code'},
            {'name': 'read_file', 'description': 'Read file contents'},
            {'name': 'write_file', 'description': 'Write to file'}
        ]
        super().__init__('coder', tools)

    async def _plan(self, query: str, context: Dict) -> list[Dict]:
        """Plan coding tasks"""

        # Analyze requirements
        requirements = await self._analyze_requirements(query)

        # Generate plan
        plan = [
            {'name': 'analyze', 'args': {'requirements': requirements}},
            {'name': 'design', 'args': {'architecture': 'modular'}},
            {'name': 'implement', 'args': {'language': 'python'}},
            {'name': 'test', 'args': {'framework': 'pytest'}}
        ]

        return plan

class ResearcherAgent(BaseAgent):
    """Information retrieval and research agent"""

    def __init__(self):
        tools = [
            {'name': 'web_search', 'description': 'Search the web'},
            {'name': 'vector_search', 'description': 'Search knowledge base'},
            {'name': 'graph_query', 'description': 'Query knowledge graph'}
        ]
        super().__init__('researcher', tools)

    async def _plan(self, query: str, context: Dict) -> list[Dict]:
        """Plan research tasks"""

        # Extract key entities
        entities = await self._extract_entities(query)

        # Generate search queries
        queries = await self._generate_queries(entities)

        plan = []
        for q in queries:
            plan.append({'name': 'web_search', 'args': {'query': q}})
            plan.append({'name': 'vector_search', 'args': {'query': q}})

        return plan
```

### ✅ Phase 1 Checklist
- [ ] Agent orchestrator implemented
- [ ] Specialized agents created
- [ ] Tool routing working
- [ ] Agent communication working

---

## Phase 2: Real-Time Streaming (4 hours)

### 2.1 Streaming Service

```python
# File: services/streaming.py
"""
Real-Time Streaming Service
============================
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json

app = FastAPI()

class StreamingService:
    """Handle streaming responses"""

    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.connections = {}

    async def stream_response(self, query: str,
                             session_id: str) -> AsyncGenerator[str, None]:
        """Stream LLM response"""

        # Get LLM stream
        async for token in self.llm_service.stream_generate(query):
            # Format for SSE
            data = json.dumps({"token": token})
            yield f"data: {data}\n\n"

            # Store in session memory
            if session_id not in self.connections:
                self.connections[session_id] = []
            self.connections[session_id].append(token)

        # Send completion
        yield "data: [DONE]\n\n"

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""

    await websocket.accept()

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)

            # Process message
            async for token in stream_response(message['query'], session_id):
                await websocket.send_json({"token": token})

    except WebSocketDisconnect:
        # Cleanup
        if session_id in streaming_service.connections:
            del streaming_service.connections[session_id]

@app.get("/stream")
async def stream_endpoint(query: str, session_id: str):
    """SSE streaming endpoint"""

    return StreamingResponse(
        streaming_service.stream_response(query, session_id),
        media_type="text/event-stream"
    )
```

### ✅ Phase 2 Checklist
- [ ] WebSocket endpoints working
- [ ] SSE streaming working
- [ ] Session management functional
- [ ] Connection cleanup working

---

## Phase 3: Scalable Infrastructure (6 hours)

### 3.1 Kubernetes Deployment

```yaml
# File: k8s/deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production-ai

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
  namespace: production-ai
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
      - name: agent-service
        image: ghcr.io/your-org/agent-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: LLM_SERVICE_URL
          value: "http://llm-service:8000"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
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
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: agent-service
  namespace: production-ai
spec:
  selector:
    app: agent-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-service-hpa
  namespace: production-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 3.2 Service Mesh

```yaml
# File: k8s/istio/virtualservice.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: agent-service
  namespace: production-ai
spec:
  hosts:
  - agent-service
  http:
  - match:
    - uri:
        prefix: /api/v1/
    route:
    - destination:
        host: agent-service
        subset: v1
      weight: 90
    - destination:
        host: agent-service
        subset: v2
      weight: 10
    retries:
      attempts: 3
      perTryTimeout: 2s
    timeout: 10s

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: agent-service
  namespace: production-ai
spec:
  host: agent-service
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
    connectionPool:
      tcp:
        maxConnections: 100
```

### ✅ Phase 3 Checklist
- [ ] Kubernetes deployment working
- [ ] HPA configured
- [ ] Service mesh configured
- [ ] Traffic management working

---

## Phase 4: Monitoring & Observability (4 hours)

### 4.1 Prometheus Metrics

```python
# File: monitoring/metrics.py
"""
Prometheus Metrics
==================
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
request_count = Counter(
    'agent_requests_total',
    'Total number of requests',
    ['agent', 'status']
)

request_duration = Histogram(
    'agent_request_duration_seconds',
    'Request duration',
    ['agent']
)

active_connections = Gauge(
    'agent_active_connections',
    'Active connections',
    ['agent']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens processed',
    ['model', 'type']  # type: input/output
)

class MetricsMiddleware:
    """Middleware to track metrics"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            # Track request
            agent = scope['path'].split('/')[1]

            with request_duration.labels(agent=agent).time():
                try:
                    await self.app(scope, receive, send)
                    request_count.labels(agent=agent, status='success').inc()
                except Exception:
                    request_count.labels(agent=agent, status='error').inc()
                    raise
        else:
            await self.app(scope, receive, send)

# Start metrics server
start_http_server(9090)
```

### 4.2 Logging

```python
# File: monitoring/logging.py
"""
Structured Logging
==================
"""

import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """JSON log formatter"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id

        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id

        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

# Configure logging
logger = logging.getLogger('production-ai')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### ✅ Phase 4 Checklist
- [ ] Prometheus metrics configured
- [ ] Logging configured
- [ ] Dashboards created
- [ ] Alerts configured

---

## Phase 5: CI/CD Pipeline (5 hours)

### 5.1 GitHub Actions

```yaml
# File: .github/workflows/deploy.yml
name: Deploy Production AI System

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        pip install uv
        uv pip install --system -r requirements.txt
        uv pip install --system -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest tests/ -v --cov=.

    - name: Security scan
      run: |
        bandit -r agents/ services/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build Docker images
      run: |
        docker build -t ghcr.io/your-org/agent-service:${{ github.sha }} ./services/agent
        docker build -t ghcr.io/your-org/llm-service:${{ github.sha }} ./services/llm

    - name: Push to registry
      run: |
        echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
        docker push ghcr.io/your-org/agent-service:${{ github.sha }}
        docker push ghcr.io/your-org/llm-service:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/agent-service \
          agent-service=ghcr.io/your-org/agent-service:${{ github.sha }} \
          -n production-ai

    - name: Verify deployment
      run: |
        kubectl rollout status deployment/agent-service -n production-ai
```

### ✅ Phase 5 Checklist
- [ ] CI pipeline working
- [ ] CD pipeline working
- [ ] Tests passing
- [ ] Automated deployment working

---

## 🏆 Project Completion Checklist

```text
[ ] Phase 1: Multi-Agent System
[ ] Phase 2: Real-Time Streaming
[ ] Phase 3: Scalable Infrastructure
[ ] Phase 4: Monitoring & Observability
[ ] Phase 5: CI/CD Pipeline
[ ] System deployed to production
[ ] Monitoring dashboards active
[ ] Load testing passed
```

---

## 📚 Related Resources

- **[7101: ReAct Loop](../../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)** - Agent pattern
- **[7301: Orchestration](../../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md)** - Multi-agent orchestration
- **[LAB-009: Production Deployment](../labs/LAB-009-Production-Deployment.md)** - Deployment

---

**Congratulations!** You've deployed a complete production AI system:
- 🤖 Multi-agent orchestration
- 🌊 Real-time streaming
- 📈 Scalable infrastructure
- 📊 Monitoring & observability
- 🚀 CI/CD automation

**You have mastered AI Systems Engineering!** 🎉
