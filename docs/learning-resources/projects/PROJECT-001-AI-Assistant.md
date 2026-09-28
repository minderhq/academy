---
Document ID: PROJECT-001
Title: "CAPSTONE PROJECT 001: Build Your AI Assistant"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# CAPSTONE PROJECT 001: Build Your AI Assistant

**A complete end-to-end project combining all learned concepts**

---

## 🎯 Project Overview

Build a fully-functional AI assistant that can:
- Answer questions using your own knowledge base (RAG)
- Remember previous conversations (Agent Memory)
- Perform tasks using tools (Tool Calling)
- Run efficiently on your hardware (Optimization)
- Scale to production-ready deployment (LLMOps)

**Estimated Time:** 20-30 hours
**Difficulty:** ⭐⭐⭐⭐ Advanced

---

## 📋 Prerequisites

### Required Tutorials & Labs:
- ✅ **[TUTORIAL-000: Python for AI](../tutorials/TUTORIAL-000-Python-for-AI.md)** - :rotating_light: **MANDATORY**
- ✅ **[Tutorial 001: Hello LLM](../tutorials/TUTORIAL-001-Hello-LLM.md)** - LLM basics
- ✅ **[Tutorial 002: Docker Essentials](../tutorials/TUTORIAL-002-Docker-Essentials.md)** - Docker fundamentals
- ✅ **[Tutorial 003: RAG Basics](../tutorials/TUTORIAL-003-RAG-Basics.md)** - RAG concepts
- ✅ **[LAB 001: Docker & LLM](../labs/LAB-001-Docker-LLM.md)** - Docker practice
- ✅ **[LAB 002: RAG Implementation](../labs/LAB-002-RAG-Implementation.md)** - RAG hands-on
- ✅ **[LAB 003: LoRA Fine-Tuning](../labs/LAB-003-LoRA-FineTuning.md)** - Fine-tuning basics

### Required Skills (from TUTORIAL-000):
:warning: **This project requires INTERMEDIATE Python skills:**
- Classes and OOP (`class VectorStore:`, `def __init__`)
- Async/await (`async def query()`, `await client.search()`)
- Type hints (`def query(self, text: str) -> List[dict]`)
- Error handling (`try/except`, custom exceptions)
- Working with APIs (`requests.post()`, JSON responses)

:information_source: **If you're missing these skills**, complete **TUTORIAL-000** first. It covers all required Python concepts in 6-8 hours.

---

## 🏗️ Architecture Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Web UI)                        │
│                    React / FastAPI                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Gateway (Nginx)                         │
│                 /chat, /rag, /admin                         │
└─────┬───────────────────────────┬───────────────────────────┘
      │                           │
      ▼                           ▼
┌──────────────────┐    ┌─────────────────────────────────────┐
│  ReAct Agent     │    │         RAG Service                 │
│  - Planning      │    │  - Qdrant Vector DB                │
│  - Tool Calling  │    │  - Document Processing             │
│  - Memory        │    │  - Re-ranking                      │
└────────┬─────────┘    └─────────────┬───────────────────────┘
         │                             │
         │        ┌─────────────────────┴──────────┐
         │        │                                │
         ▼        ▼                                ▼
┌──────────────────┐    ┌──────────────────┐  ┌─────────────┐
│ Tool Executor    │    │   vLLM Engine    │  │  Neo4j DB   │
│ - Python Code    │    │  - Mistral-7B    │  │  Knowledge  │
│ - Shell Commands │    │  - Fine-tuned   │  │  Graph      │
│ - HTTP Requests  │    │  - Quantized     │  │             │
└──────────────────┘    └──────────────────┘  └─────────────┘
```

---

## Phase 1: Setup & Infrastructure (2 hours)

### 1.1 Create Project Structure

```bash
# Create project directory
mkdir ~/ai-assistant
cd ~/ai-assistant

# Directory structure
mkdir -p services/{agent,rag,frontend,tools}
mkdir -p data/{vector,graph,documents,models}
mkdir - configs/{nginx,prometheus}
mkdir -p scripts
```

### 1.2 Setup Docker Compose

```yaml
# ~/ai-assistant/docker-compose.yml

services:
  # Neo4j Knowledge Graph
  neo4j:
    image: neo4j:5-community
    container_name: neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - ./data/graph:/data
    restart: unless-stopped
    networks:
      - ai-net

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./data/vector:/qdrant/storage
    restart: unless-stopped
    networks:
      - ai-net

  # vLLM Inference Engine
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm
    ports:
      - "8000:8000"
    volumes:
      - ./data/models:/models
    command: >
      --model mistralai/Mistral-7B-Instruct-v0.2
      --gpu-memory-utilization 0.9
      --max-model-len 4096
      --enable-prefix-caching
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - ai-net

  # RAG Service
  rag:
    build: ./services/rag
    container_name: rag-service
    ports:
      - "8001:8001"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - VLLM_URL=http://vllm:8000
    depends_on:
      - qdrant
      - neo4j
      - vllm
    restart: unless-stopped
    networks:
      - ai-net

  # ReAct Agent Service
  agent:
    build: ./services/agent
    container_name: agent-service
    ports:
      - "8002:8002"
    environment:
      - VLLM_URL=http://vllm:8000
      - RAG_URL=http://rag:8001
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - TOOL_EXECUTOR_URL=http://tool-executor:8003
    depends_on:
      - vllm
      - rag
      - neo4j
      - tool-executor
    restart: unless-stopped
    networks:
      - ai-net

  # Tool Executor (Sandbox)
  tool-executor:
    build: ./services/tools
    container_name: tool-executor
    ports:
      - "8003:8003"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    restart: unless-stopped
    networks:
      - ai-net

  # Frontend
  frontend:
    build: ./services/frontend
    container_name: frontend
    ports:
      - "3000:3000"
    environment:
      - AGENT_URL=http://agent:8002
      - RAG_URL=http://rag:8001
    depends_on:
      - agent
      - rag
    restart: unless-stopped
    networks:
      - ai-net

  # Nginx API Gateway
  nginx:
    image: nginx:alpine
    container_name: nginx-gateway
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./configs/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./configs/nginx/conf.d:/etc/nginx/conf.d:ro
    depends_on:
      - agent
      - rag
      - frontend
    restart: unless-stopped
    networks:
      - ai-net

networks:
  ai-net:
    driver: bridge
```

### ✅ Phase 1 Checklist
- [ ] Project structure created
- [ ] Docker Compose configured
- [ ] All services can start

---

## Phase 2: Knowledge Base Setup (3 hours)

### 2.1 Prepare Documents

```python
# ~/ai-assistant/scripts/prepare_kb.py
import os
from pathlib import Path

# Create sample knowledge base
docs = {
    "docker.txt": """
Docker is a containerization platform.
Docker images are built from Dockerfiles.
Docker containers run instances of images.
Common commands: docker run, docker build, docker ps.
Docker Compose orchestrates multi-container applications.
""",

    "kubernetes.txt": """
Kubernetes is a container orchestration platform.
Kubernetes Pods contain one or more containers.
Kubernetes Services provide stable networking.
Kubernetes Deployments manage application updates.
Common commands: kubectl get, kubectl apply, kubectl describe.
""",

    "python.txt": """
Python is a high-level programming language.
Python uses indentation for code blocks.
Python supports multiple programming paradigms.
Common frameworks: FastAPI, Django, Flask.
Package manager: pip, conda, poetry.
"""
}

# Save documents
kb_dir = Path("~/ai-assistant/data/documents").expanduser()
kb_dir.mkdir(parents=True, exist_ok=True)

for filename, content in docs.items():
    (kb_dir / filename).write_text(content)

print(f"Created {len(docs)} documents in {kb_dir}")
```

### 2.2 Build Vector Index

```python
# ~/ai-assistant/scripts/build_vector_index.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from pathlib import Path
import uuid

# Initialize
qdrant = QdrantClient(url="http://localhost:6333")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Create collection only if missing - recreate_collection would wipe
# every stored vector, so re-running this script must not use it
if not qdrant.collection_exists("knowledge_base"):
    qdrant.create_collection(
        collection_name="knowledge_base",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

# Load and index documents
docs_dir = Path("~/ai-assistant/data/documents").expanduser()
points = []

for doc_file in docs_dir.glob("*.txt"):
    text = doc_file.read_text()
    chunks = text.split('\n\n')

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue

        # Generate embedding
        embedding = embedder.encode(chunk).tolist()

        # Create point
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": chunk,
                "source": doc_file.name,
                "chunk_id": i
            }
        )
        points.append(point)

# Insert
qdrant.upsert(collection_name="knowledge_base", points=points)

print(f"Indexed {len(points)} chunks from {len(list(docs_dir.glob('*.txt')))} documents")
```

### 2.3 Build Knowledge Graph

```python
# ~/ai-assistant/scripts/build_graph.py
from neo4j import GraphDatabase
from pathlib import Path

# Connect to Neo4j
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

def create_knowledge_graph(tx, doc_name, content):
    """Create entities and relationships from document"""

    # Extract entities (simple keyword extraction)
    entities = set()
    keywords = {
        'docker': ['Docker', 'containers', 'images', 'Dockerfile', 'Compose'],
        'kubernetes': ['Kubernetes', 'K8s', 'Pods', 'Services', 'Deployments', 'kubectl'],
        'python': ['Python', 'FastAPI', 'Django', 'Flask', 'pip', 'conda']
    }

    for category, words in keywords.items():
        for word in words:
            if word.lower() in content.lower():
                entities.add((word, category))

    # Create nodes
    for entity, category in entities:
        tx.run(
            "MERGE (e:Entity {name: $name, category: $category})",
            name=entity, category=category
        )

    # Create relationships
    entity_list = list(entities)
    for i, (entity1, cat1) in enumerate(entity_list):
        for entity2, cat2 in entity_list[i+1:]:
            if cat1 == cat2:  # Same category
                tx.run(
                    """
                    MATCH (e1:Entity {name: $name1})
                    MATCH (e2:Entity {name: $name2})
                    MERGE (e1)-[:RELATED_TO]->(e2)
                    """,
                    name1=entity1, name2=entity2
                )

    # Create document node
    tx.run(
        "MERGE (d:Document {name: $name})",
        name=doc_name
    )

    # Link entities to document
    for entity, _ in entities:
        tx.run(
            """
            MATCH (d:Document {name: $doc_name})
            MATCH (e:Entity {name: $entity})
            MERGE (d)-[:CONTAINS]->(e)
            """,
            doc_name=doc_name, entity=entity
        )

# Process documents
docs_dir = Path("~/ai-assistant/data/documents").expanduser()

with driver.session() as session:
    for doc_file in docs_dir.glob("*.txt"):
        content = doc_file.read_text()
        session.execute_write(
            create_knowledge_graph,
            doc_file.name,
            content
        )

print("Knowledge graph created!")

driver.close()
```

### ✅ Phase 2 Checklist
- [ ] Documents prepared
- [ ] Vector index built in Qdrant
- [ ] Knowledge graph built in Neo4j
- [ ] Both databases accessible

---

## Phase 3: RAG Service (4 hours)

### 3.1 Create RAG Service

```python
# ~/ai-assistant/services/rag/rag_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer, CrossEncoder
import logging

app = FastAPI(title="RAG Service")

# Configuration
QDRANT_URL = "http://qdrant:6333"
NEO4J_URI = "bolt://neo4j:7687"
VLLM_URL = "http://vllm:8000"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "ms-marco-MiniLM-L-6-v2"

# Initialize clients
qdrant = QdrantClient(url=QDRANT_URL)
neo4j = GraphDatabase.driver(NEO4J_URI, auth=("neo4j", "password"))
embedder = SentenceTransformer(EMBEDDING_MODEL)
reranker = CrossEncoder(RERANKER_MODEL)

logger = logging.getLogger(__name__)

class Query(BaseModel):
    question: str
    use_graph: bool = True
    top_k: int = 3

class RAGResponse(BaseModel):
    answer: str
    vector_sources: List[dict]
    graph_sources: List[dict]
    query_time: float

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/query", response_model=RAGResponse)
async def query_rag(query: Query):
    """Hybrid RAG: Vector + Graph"""

    import time
    start = time.time()

    # 1. Vector Search
    query_vector = embedder.encode(query.question).tolist()
    vector_results = qdrant.search(
        collection_name="knowledge_base",
        query_vector=query_vector,
        limit=query.top_k * 2  # Get more for reranking
    )

    # 2. Re-rank
    rerank_input = [(query.question, hit.payload['text']) for hit in vector_results]
    scores = reranker.predict(rerank_input)

    for hit, score in zip(vector_results, scores):
        hit.score = float(score)

    vector_results = sorted(vector_results, key=lambda x: x.score, reverse=True)[:query.top_k]

    # 3. Graph Search (if enabled)
    graph_results = []
    if query.use_graph:
        with neo4j.session() as session:
            # Extract entities from question
            entities = extract_entities(query.question)

            # Query graph
            for entity in entities:
                result = session.run(
                    """
                    MATCH (e:Entity {name: $entity})
                    OPTIONAL MATCH (e)-[r:RELATED_TO]-(related:Entity)
                    OPTIONAL MATCH (d:Document)-[:CONTAINS]->(e)
                    RETURN e.name as entity, related.name as related,
                           collect(DISTINCT d.name) as documents
                    """,
                    entity=entity
                )

                for record in result:
                    graph_results.append({
                        "entity": record["entity"],
                        "related": record["related"],
                        "documents": record["documents"]
                    })

    # 4. Combine results
    vector_context = "\n\n".join([hit.payload['text'] for hit in vector_results])

    if graph_results:
        graph_context = "Related concepts: " + ", ".join([
            r['entity'] for r in graph_results if r['entity']
        ])
        context = f"{vector_context}\n\n{graph_context}"
    else:
        context = vector_context

    # 5. Generate answer
    prompt = f"""Answer the question using the context below.

Context:
{context}

Question: {query.question}

Answer:"""

    try:
        response = requests.post(
            f"{VLLM_URL}/v1/completions",
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "prompt": prompt,
                "max_tokens": 512
            },
            timeout=60
        )
        answer = response.json()["choices"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Generation error: {e}")
        answer = f"Based on the context, here's what I found:\n\n{context}"

    query_time = time.time() - start

    return RAGResponse(
        answer=answer,
        vector_sources=[
            {
                "text": hit.payload['text'],
                "score": hit.score,
                "source": hit.payload['source']
            }
            for hit in vector_results
        ],
        graph_sources=graph_results,
        query_time=query_time
    )

def extract_entities(text: str) -> List[str]:
    """Extract entity names from text"""
    # Simple keyword extraction
    keywords = ['Docker', 'Kubernetes', 'Python', 'FastAPI', 'Neo4j', 'Qdrant']
    return [kw for kw in keywords if kw.lower() in text.lower()]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 3.2 Create Dockerfile

```dockerfile
# ~/ai-assistant/services/rag/Dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cache models
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2'); \
    from sentence_transformers import CrossEncoder; \
    CrossEncoder('ms-marco-MiniLM-L-6-v2')"

COPY . .

EXPOSE 8001

CMD ["uvicorn", "rag_service:app", "--host", "0.0.0.0", "--port", "8001"]
```

### ✅ Phase 3 Checklist
- [ ] RAG service implemented
- [ ] Vector + Graph hybrid search working
- [ ] Re-ranking implemented
- [ ] Service containerized

---

## Phase 4: ReAct Agent Service (5 hours)

### 4.1 Create ReAct Agent

```python
# ~/ai-assistant/services/agent/agent_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import json
import re

app = FastAPI(title="ReAct Agent Service")

# Configuration
VLLM_URL = "http://vllm:8000"
RAG_URL = "http://rag:8001"
TOOL_EXECUTOR_URL = "http://tool-executor:8003"
NEO4J_URI = "bolt://neo4j:7687"

from neo4j import GraphDatabase
neo4j = GraphDatabase.driver(NEO4J_URI, auth=("neo4j", "password"))

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    session_id: str
    use_rag: bool = True
    use_tools: bool = True

class ChatResponse(BaseModel):
    response: str
    thought_process: List[Dict[str, Any]]
    tools_used: List[str]

class ReActAgent:
    """ReAct: Reasoning + Acting Agent"""

    def __init__(self):
        self.memory = {}  # In production, use Redis

    async def run(self, messages: List[Message], session_id: str,
                  use_rag: bool = True, use_tools: bool = True) -> ChatResponse:
        """Run ReAct loop"""

        thought_process = []
        tools_used = []

        # Load conversation history
        history = self.memory.get(session_id, [])

        # Initial thought
        last_message = messages[-1].content
        thought = await self._think(last_message, history)
        thought_process.append({"step": "initial_thought", "content": thought})

        # Check if RAG is needed
        if use_rag and self._needs_knowledge(last_message):
            thought_process.append({"step": "retrieval", "content": "Querying knowledge base..."})

            rag_response = requests.post(
                f"{RAG_URL}/query",
                json={"question": last_message, "use_graph": True, "top_k": 3},
                timeout=30
            ).json()

            knowledge = rag_response['answer']
            thought_process.append({
                "step": "knowledge_retrieved",
                "content": knowledge,
                "sources": rag_response['vector_sources']
            })
        else:
            knowledge = None

        # Plan action
        action_plan = await self._plan(last_message, thought, knowledge)
        thought_process.append({"step": "planning", "content": action_plan})

        # Execute tools if needed
        if use_tools and action_plan.get('use_tools'):
            for tool in action_plan['tools']:
                result = await self._execute_tool(tool, last_message)
                tools_used.append(tool['name'])
                thought_process.append({
                    "step": "tool_execution",
                    "tool": tool['name'],
                    "result": result
                })

        # Generate final response
        prompt = self._build_prompt(last_message, thought, knowledge, thought_process)

        response = requests.post(
            f"{VLLM_URL}/v1/completions",
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "prompt": prompt,
                "max_tokens": 768
            },
            timeout=60
        )

        final_response = response.json()["choices"][0]["text"].strip()

        # Update memory
        history.append({"role": "user", "content": last_message})
        history.append({"role": "assistant", "content": final_response})
        self.memory[session_id] = history

        return ChatResponse(
            response=final_response,
            thought_process=thought_process,
            tools_used=tools_used
        )

    async def _think(self, query: str, history: List[Dict]) -> str:
        """Initial reasoning about the query"""

        prompt = f"""You are an AI assistant. Think about what the user is asking.

User: {query}

Provide a brief thought about what information you need to answer this question.
Thought:"""

        response = requests.post(
            f"{VLLM_URL}/v1/completions",
            json={"model": "mistralai/Mistral-7B-Instruct-v0.2", "prompt": prompt, "max_tokens": 256},
            timeout=30
        )

        return response.json()["choices"][0]["text"].strip()

    def _needs_knowledge(self, query: str) -> bool:
        """Check if query needs external knowledge"""

        # Simple heuristic: questions need knowledge
        question_words = ['what', 'how', 'why', 'explain', 'describe', 'tell me']
        return any(qw in query.lower() for qw in question_words)

    async def _plan(self, query: str, thought: str, knowledge: Optional[str]) -> Dict:
        """Plan what actions to take"""

        # Check if tools are needed
        tool_keywords = {
            'run_code': ['code', 'python', 'execute', 'run', 'script'],
            'shell_command': ['command', 'bash', 'terminal', 'execute', 'run'],
            'web_search': ['search', 'find', 'lookup', 'latest', 'current'],
            'file_read': ['read', 'open', 'view', 'check', 'file']
        }

        needed_tools = []
        for tool_name, keywords in tool_keywords.items():
            if any(kw in query.lower() for kw in keywords):
                needed_tools.append({'name': tool_name})

        return {
            'use_tools': len(needed_tools) > 0,
            'tools': needed_tools
        }

    async def _execute_tool(self, tool: Dict, query: str) -> Any:
        """Execute a tool"""

        try:
            response = requests.post(
                f"{TOOL_EXECUTOR_URL}/tools/{tool['name']}",
                json={'query': query},
                timeout=60
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def _build_prompt(self, query: str, thought: str,
                     knowledge: Optional[str], thought_process: List) -> str:
        """Build final prompt"""

        prompt = f"""You are a helpful AI assistant with access to tools and knowledge.

User Question: {query}

Your initial thought: {thought}
"""

        if knowledge:
            prompt += f"\nRelevant knowledge:\n{knowledge}\n"

        if thought_process:
            prompt += "\nYour reasoning process:\n"
            for step in thought_process:
                prompt += f"- {step['step']}: {step.get('content', '')}\n"

        prompt += "\nNow provide a helpful answer to the user:\n"

        return prompt

# Initialize agent
agent = ReActAgent()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with ReAct agent"""

    return await agent.run(
        messages=request.messages,
        session_id=request.session_id,
        use_rag=request.use_rag,
        use_tools=request.use_tools
    )

@app.delete("/memory/{session_id}")
def clear_memory(session_id: str):
    """Clear session memory"""

    if session_id in agent.memory:
        del agent.memory[session_id]
        return {"status": "cleared"}

    return {"status": "not_found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

### ✅ Phase 4 Checklist
- [ ] ReAct agent implemented
- [ ] Tool calling working
- [ ] Memory system functional
- [ ] RAG integration complete

---

## Phase 5: Tool Executor (3 hours)

### 5.1 Create Tool Service

```python
# ~/ai-assistant/services/tools/tool_executor.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import subprocess
import docker
import tempfile
import os

app = FastAPI(title="Tool Executor")

docker_client = docker.from_env()

class ToolRequest(BaseModel):
    query: str

def execute_python_code(code: str) -> Dict[str, Any]:
    """Execute Python code in sandbox"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        # Run in isolated container
        result = docker_client.containers.run(
            "python:3.13-slim",
            f"python /app/code.py",
            volumes={os.path.dirname(temp_file): {'bind': '/app', 'mode': 'ro'}},
            mem_limit='512m',
            cpu_period=100000,
            cpu_quota=50000,
            network_disabled=True,
            remove=True,
            stdout=True,
            stderr=True
        )

        return {"success": True, "output": result}

    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        os.unlink(temp_file)

def execute_shell_command(command: str) -> Dict[str, Any]:
    """Execute shell command (whitelisted only)"""

    # Whitelist of safe commands
    allowed_commands = ['ls', 'pwd', 'echo', 'cat', 'grep', 'wc']

    cmd_parts = command.split()
    if cmd_parts[0] not in allowed_commands:
        return {"success": False, "error": "Command not allowed"}

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tools/run_code")
async def run_python_tool(request: ToolRequest):
    """Execute Python code"""

    # Extract code from query
    code = request.query  # In production, parse code properly

    return execute_python_code(code)

@app.post("/tools/shell_command")
async def run_shell_tool(request: ToolRequest):
    """Execute shell command"""

    return execute_shell_command(request.query)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

### ✅ Phase 5 Checklist
- [ ] Tool executor implemented
- [ ] Python code execution sandboxed
- [ ] Shell command whitelist working
- [ ] Docker isolation functional

---

## Phase 6: Frontend (3 hours)

### 6.1 Create Simple Web UI

```html
<!-- ~/ai-assistant/services/frontend/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>AI Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto p-4 max-w-4xl">
        <h1 class="text-3xl font-bold mb-4">🤖 AI Assistant</h1>

        <!-- Settings -->
        <div class="mb-4 flex gap-4">
            <label class="flex items-center gap-2">
                <input type="checkbox" id="useRag" checked>
                <span>Use Knowledge Base</span>
            </label>
            <label class="flex items-center gap-2">
                <input type="checkbox" id="useTools" checked>
                <span>Use Tools</span>
            </label>
            <button onclick="clearMemory()" class="bg-red-600 px-4 py-2 rounded">Clear Memory</button>
        </div>

        <!-- Chat -->
        <div id="chat" class="bg-gray-800 rounded-lg p-4 mb-4 h-96 overflow-y-auto"></div>

        <!-- Input -->
        <div class="flex gap-2">
            <input type="text" id="message" class="flex-1 bg-gray-700 rounded-lg px-4 py-2"
                   placeholder="Ask me anything..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button onclick="sendMessage()" class="bg-blue-600 px-6 py-2 rounded-lg">Send</button>
        </div>

        <!-- Thought Process -->
        <div id="thoughts" class="mt-4 bg-gray-800 rounded-lg p-4 hidden">
            <h3 class="font-bold mb-2">Thought Process</h3>
            <div id="thoughtContent"></div>
        </div>
    </div>

    <script>
        const sessionId = 'session-' + Math.random().toString(36).substr(2, 9);

        async function sendMessage() {
            const input = document.getElementById('message');
            const message = input.value.trim();
            if (!message) return;

            addMessage('user', message);
            input.value = '';

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    messages: [{role: 'user', content: message}],
                    session_id: sessionId,
                    use_rag: document.getElementById('useRag').checked,
                    use_tools: document.getElementById('useTools').checked
                })
            });

            const data = await response.json();
            addMessage('assistant', data.response);
            showThoughts(data.thought_process);
        }

        function addMessage(role, content) {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = `mb-4 ${role === 'user' ? 'text-right' : ''}`;
            div.innerHTML = `
                <span class="inline-block bg-${role === 'user' ? 'blue' : 'gray'}-600 rounded-lg px-4 py-2 max-w-lg">
                    ${content}
                </span>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function showThoughts(thoughts) {
            const thoughtDiv = document.getElementById('thoughts');
            const content = document.getElementById('thoughtContent');
            thoughtDiv.classList.remove('hidden');
            content.innerHTML = thoughts.map(t =>
                `<p><strong>${t.step}:</strong> ${t.content || ''}</p>`
            ).join('');
        }

        async function clearMemory() {
            await fetch(`/memory/${sessionId}`, {method: 'DELETE'});
            document.getElementById('chat').innerHTML = '';
        }
    </script>
</body>
</html>
```

### ✅ Phase 6 Checklist
- [ ] Frontend UI created
- [ ] Chat interface functional
- [ ] Settings panel working
- [ ] Thought process display

---

## Phase 7: Deployment & Testing (2 hours)

### 7.1 Deploy Everything

```bash
cd ~/ai-assistant

# Build and start all services
docker-compose build
docker-compose up -d

# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f
```

### 7.2 Test the System

```bash
# Test 1: Simple question
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What is Docker?"}],
    "session_id": "test1",
    "use_rag": true,
    "use_tools": false
  }'

# Test 2: Tool execution
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "List files in current directory"}],
    "session_id": "test2",
    "use_rag": false,
    "use_tools": true
  }'

# Test 3: Memory
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "My name is Alice"},
      {"role": "assistant", "content": "Hello Alice!"},
      {"role": "user", "content": "What is my name?"}
    ],
    "session_id": "test3",
    "use_rag": false,
    "use_tools": false
  }'
```

### ✅ Phase 7 Checklist
- [ ] All services deployed
- [ ] Knowledge retrieval working
- [ ] Tool execution working
- [ ] Memory system working
- [ ] Frontend accessible

---

## 🎓 Bonus Extensions

### Easy Extensions (1-2 hours each):
1. **Add streaming responses** - Show tokens as they generate
2. **Add voice input/output** - Use Web Speech API
3. **Add document upload** - Allow users to add new knowledge
4. **Add export chat** - Download conversation history

### Advanced Extensions (3-5 hours each):
1. **Multi-user support** - Add authentication and per-user memory
2. **Analytics dashboard** - Track usage and popular queries
3. **Fine-tune on domain** - Add LAB 003 fine-tuning
4. **Add more tools** - Calculator, weather, web search, etc.

---

## 🏆 Project Completion Checklist

```text
[ ] Phase 1: Setup & Infrastructure
[ ] Phase 2: Knowledge Base Setup
[ ] Phase 3: RAG Service
[ ] Phase 4: ReAct Agent Service
[ ] Phase 5: Tool Executor
[ ] Phase 6: Frontend
[ ] Phase 7: Deployment & Testing
[ ] Bonus: At least one extension implemented
```

---

## 📚 Related Resources

- **[7101: ReAct Loop System](../../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)** - ReAct pattern theory
- **[6201: Hybrid Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)** - Vector + Graph RAG
- **[1402: vLLM and TGI](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)** - Production inference
- **[LAB 002: RAG Implementation](../labs/LAB-002-RAG-Implementation.md)** - RAG basics
- **[Volume 1: Infrastructure Fundamentals](../../volumes/VOLUME-1-Infrastructure.md)** - Phase 1 reading guide

---

**Congratulations!** You've built a production-ready AI assistant combining:
- 🧠 Knowledge retrieval (RAG)
- 🤖 Reasoning and action (ReAct)
- 🛠️ Tool execution
- 💾 Memory system
- 🚀 Production deployment

## Next Steps

- Explore advanced topics in **[7000: Agentic Systems](../../phases/phase7-agentic/)** or build your own project!
