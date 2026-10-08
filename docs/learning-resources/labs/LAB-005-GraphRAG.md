---
Document ID: LAB-005
Title: "LAB-005: GraphRAG Implementation with Neo4j & Qdrant"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Tags: ['lab', 'graphrag', 'neo4j', 'qdrant', 'hands-on']
---

# LAB-005: GraphRAG Implementation with Neo4j & Qdrant

**Prerequisites:** TUTORIAL-001 (Hello LLM), TUTORIAL-002 (Docker Essentials), LAB-001 (Docker & LLM), LAB-002 (RAG Implementation)
**Time:** 5 hours
**Difficulty:** ⭐⭐⭐ Advanced

---

## Lab Objectives

After completing this lab, you will be able to:

- ✅ Understand GraphRAG vs Vector RAG
- ✅ Deploy Neo4j graph database
- ✅ Build knowledge graphs from documents
- ✅ Implement hybrid RAG (Vector + Graph)
- ✅ Perform multi-hop reasoning
- ✅ Deploy complete GraphRAG system

---

## Setup Instructions

```bash
# Create lab directory
mkdir ~/lab-005-graphrag
cd ~/lab-005-graphrag

# Create directory structure
mkdir -p services/graphrag
mkdir -p data/graph
mkdir -p data/documents
mkdir -p scripts
```

---

## Exercise 1: Understanding GraphRAG (30 minutes)

### Task: Learn the difference between Vector RAG and GraphRAG

**Vector RAG (What you did in LAB-002):**
```text
Query → Embed → Search Vector DB → Retrieve → Generate
```
- Good for: Semantic similarity
- Limitation: Misses relationships between entities

**GraphRAG (This lab):**
```text
Query → Extract Entities → Traverse Graph → Retrieve Context → Generate
```
- Good for: Multi-hop reasoning, entity relationships
- Limitation: More complex setup

**Hybrid RAG (Best of both):**
```text
Query → Vector Search + Graph Traversal → Combine Results → Generate
```

### Example Comparison

**Question:** "What company did the CEO of Tesla found before Tesla?"

**Vector RAG:** Might retrieve documents about Tesla and CEOs, but may miss the specific connection.

**GraphRAG:** Can traverse:
```text
Tesla --[CEO]--> Elon Musk --[Founded]--> SpaceX
```

This gives the precise answer: **SpaceX**

---

## Exercise 2: Deploy Neo4j (20 minutes)

### Task: Deploy Neo4j graph database

```bash
# Run Neo4j with Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/graphrag \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v ~/lab-005-graphrag/data/graph:/data \
  neo4j:5-community

# Wait for Neo4j to start (about 30 seconds)
sleep 30

# Verify it's running
docker ps | grep neo4j

# Check Neo4j is ready
curl http://localhost:7474

# Open Neo4j Browser
# URL: http://localhost:7474
# Username: neo4j
# Password: graphrag
```

### Checkpoint: Exercise 2
**Verify:** Neo4j browser opens at [http://localhost:7474](http://localhost:7474)

---

## Exercise 3: Build Knowledge Graph (60 minutes)

### Task: Create knowledge graph from documents

```python
# ~/lab-005-graphrag/scripts/build_graph.py
from neo4j import GraphDatabase
import re

# Connect to Neo4j
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "graphrag")
)

class KnowledgeGraphBuilder:
    """Build knowledge graph from documents"""

    def __init__(self, driver):
        self.driver = driver

    def clear_graph(self):
        """Clear existing graph"""

        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Graph cleared")

    def extract_entities(self, text: str) -> list[dict]:
        """Extract entities from text"""

        entities = []

        # Domain-specific entity patterns
        patterns = {
            'Technology': [
                r'\b(Docker|Kubernetes|Python|FastAPI|Neo4j|Qdrant|Redis|Nginx)\b',
                r'\b(LLM|AI|ML|GPU|CPU|RAM|API|REST)\b'
            ],
            'Company': [
                r'\b(Google|Microsoft|OpenAI|Meta|NVIDIA|Docker Inc)\b'
            ],
            'Person': [
                r'\b(Elon Musk|Sam Altman|Guido van Rossum)\b'
            ],
            'Concept': [
                r'\b(container|orchestration|vector database|graph database)\b',
                r'\b(embedding|transformer|attention|neural network)\b'
            ]
        }

        text_lower = text.lower()

        for entity_type, regex_list in patterns.items():
            for regex in regex_list:
                matches = re.finditer(regex, text, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group().strip()
                    entities.append({
                        'name': entity_name,
                        'type': entity_type
                    })

        # Remove duplicates
        unique_entities = {}
        for entity in entities:
            key = (entity['name'].lower(), entity['type'])
            unique_entities[key] = entity

        return list(unique_entities.values())

    def extract_relationships(self, text: str, entities: list[dict]) -> list[dict]:
        """Extract relationships between entities"""

        relationships = []

        # Simple co-occurrence relationships
        entity_names = [e['name'].lower() for e in entities]

        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # Check if entities appear near each other in text
                name1_lower = entity1['name'].lower()
                name2_lower = entity2['name'].lower()

                if name1_lower in text_lower and name2_lower in text_lower:
                    # Find positions
                    pos1 = text_lower.find(name1_lower)
                    pos2 = text_lower.find(name2_lower)

                    # If within 200 characters, they're related
                    if abs(pos1 - pos2) < 200:
                        relationships.append({
                            'from': entity1['name'],
                            'to': entity2['name'],
                            'type': 'RELATED_TO',
                            'context': text[max(0, min(pos1, pos2)-50):min(len(text), max(pos1, pos2)+50)]
                        })

        return relationships

    def create_graph(self, documents: list[dict]):
        """Create graph from documents"""

        with self.driver.session() as session:
            for doc in documents:
                text = doc['content']
                source = doc.get('source', 'unknown')

                print(f"Processing: {source}")

                # Extract entities
                entities = self.extract_entities(text)
                print(f"  Found {len(entities)} entities")

                # Extract relationships
                relationships = self.extract_relationships(text, entities)
                print(f"  Found {len(relationships)} relationships")

                # Create entity nodes
                for entity in entities:
                    session.run(
                        """
                        MERGE (e:Entity {name: $name, type: $type})
                        SET e.source = $source
                        """,
                        name=entity['name'],
                        type=entity['type'],
                        source=source
                    )

                # Create relationship nodes
                for rel in relationships:
                    session.run(
                        """
                        MATCH (e1:Entity {name: $from})
                        MATCH (e2:Entity {name: $to})
                        MERGE (e1)-[r:RELATED_TO]->(e2)
                        SET r.context = $context
                        """,
                        parameters={
                            "from": rel['from'],
                            "to": rel['to'],
                            "context": rel['context']
                        }
                    )

                # Create document node and connect to entities
                session.run(
                    """
                    MERGE (d:Document {name: $source})
                    """
                    , source=source
                )

                for entity in entities:
                    session.run(
                        """
                        MATCH (d:Document {name: $source})
                        MATCH (e:Entity {name: $name})
                        MERGE (d)-[r:MENTIONS]->(e)
                        """,
                        source=source,
                        name=entity['name']
                    )

        print("Graph created successfully!")

# Sample documents
documents = [
    {
        "source": "docker.txt",
        "content": """
Docker is a containerization platform that allows developers to package
applications into containers. Containers are lightweight and portable compared
to virtual machines. Docker was founded by Solomon Hykes and later acquired
by Microsoft. Kubernetes is often used with Docker for orchestration.

Python is commonly used with Docker for building applications. FastAPI is a
modern Python web framework that works well in Docker containers.
"""
    },
    {
        "source": "kubernetes.txt",
        "content": """
Kubernetes is an open-source container orchestration platform. It was
originally developed at Google by Joe Beda, Brendan Burns, and Craig McLuckie.
Kubernetes is now maintained by the Cloud Native Computing Foundation (CNCF).

Google developed Kubernetes based on their internal system called Borg.
Kubernetes works with containers from Docker and other runtimes. It provides
automated deployment, scaling, and management of containerized applications.
"""
    },
    {
        "source": "neo4j.txt",
        "content": """
Neo4j is a graph database management system. Neo4j is developed by Neo4j, Inc.
which was founded by Emil Eifrem, Johan Svensson, and Peter Neubauer.

Graph databases like Neo4j are designed to handle highly connected data.
They are well-suited for social networks, fraud detection, and recommendation engines.
Neo4j uses the Cypher query language and can be deployed using Docker.
"""
    }
]

# Build graph
builder = KnowledgeGraphBuilder(driver)
builder.clear_graph()
builder.create_graph(documents)

driver.close()
```

### Run the script:
```bash
cd ~/lab-005-graphrag
python scripts/build_graph.py
```

### Checkpoint: Exercise 3
**Verify:** Knowledge graph created with entities and relationships

---

## Exercise 4: GraphRAG Service (90 minutes)

### Task: Create GraphRAG API service

```python
# ~/lab-005-graphrag/services/graphrag/graphrag_service.py
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import logging

app = FastAPI(title="GraphRAG Service")

# Configuration
NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "graphrag"
QDRANT_URL = "http://qdrant:6333"
VLLM_URL = "http://ollama:11434"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Initialize clients
neo4j = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
qdrant = QdrantClient(url=QDRANT_URL)
embedder = SentenceTransformer(EMBEDDING_MODEL)

logger = logging.getLogger(__name__)

class Query(BaseModel):
    question: str
    use_vector: bool = True
    use_graph: bool = True
    top_k: int = 3
    max_hops: int = 2

class GraphRAGResponse(BaseModel):
    answer: str
    vector_sources: list[dict]
    graph_sources: list[dict]
    reasoning: list[str]
    query_time: float

def extract_entities_from_query(query: str) -> list[str]:
    """Extract entities from user query"""

    # Simple keyword extraction
    entities = []

    # Common entities in our graph
    known_entities = [
        "Docker", "Kubernetes", "Python", "FastAPI", "Neo4j", "Qdrant",
        "Google", "Microsoft", "Elon Musk", "Joe Beda", "Solomon Hykes",
        "container", "orchestration", "graph database"
    ]

    query_lower = query.lower()

    for entity in known_entities:
        if entity.lower() in query_lower:
            entities.append(entity)

    return entities

def graph_search(entities: list[str], max_hops: int = 2) -> list[dict]:
    """Search knowledge graph with multi-hop reasoning"""

    if not entities:
        return []

    # $parameters cannot fill Cypher path bounds - int-cast the bound first
    max_hops = max(1, int(max_hops))

    results = []

    with neo4j.session() as session:
        for entity in entities:
            # Multi-hop search
            cypher = f"""
            MATCH path = (e1:Entity {{name: $entity}})-[*1..{max_hops}]-(related:Entity)
            RETURN e1.name as start, related.name as end,
                   [node in nodes(path) | node.name] as path_nodes,
                   [r in relationships(path) | type(r)] as path_types
            LIMIT 10
            """

            result = session.run(cypher, entity=entity)

            for record in result:
                results.append({
                    'start_entity': record['start'],
                    'end_entity': record['end'],
                    'path': ' -> '.join(record['path_nodes']),
                    'relationship_types': record['path_types']
                })

    return results

@app.get("/health")
def health():
    """Health check"""
    return {
        "status": "healthy",
        "neo4j": "connected",
        "qdrant": "connected"
    }

@app.post("/query", response_model=GraphRAGResponse)
async def query_graphrag(query: Query):
    """Hybrid GraphRAG query"""

    import time
    start = time.time()

    reasoning_steps = []

    # Step 1: Extract entities from query
    entities = extract_entities_from_query(query.question)
    reasoning_steps.append(f"Extracted entities: {', '.join(entities)}")

    # Step 2: Vector search (if enabled)
    vector_context = ""
    vector_sources = []

    if query.use_vector:
        query_vector = embedder.encode(query.question).tolist()
        vector_results = qdrant.query_points(
            collection_name="knowledge_base",
            query=query_vector,
            limit=query.top_k
        ).points

        vector_context = "\n\n".join([
            hit.payload['text'] for hit in vector_results
        ])

        vector_sources = [
            {
                "text": hit.payload['text'],
                "score": hit.score,
                "source": hit.payload.get('source', 'unknown')
            }
            for hit in vector_results
        ]

        reasoning_steps.append(f"Vector search found {len(vector_results)} relevant documents")

    # Step 3: Graph search (if enabled)
    graph_context = ""
    graph_sources = []

    if query.use_graph and entities:
        graph_results = graph_search(entities, query.max_hops)
        reasoning_steps.append(f"Graph search found {len(graph_results)} relationships")

        for result in graph_results:
            graph_context += f"\n{result['start_entity']} is connected to {result['end_entity']} via: {result['path']}\n"

        graph_sources = graph_results

    # Step 4: Combine contexts
    combined_context = ""

    if vector_context:
        combined_context += f"Relevant documents:\n{vector_context}\n\n"

    if graph_context:
        combined_context += f"Knowledge graph:\n{graph_context}\n"

    # Step 5: Generate response
    prompt = f"""You are a helpful assistant. Answer the question using the context below.

{combined_context}

Question: {query.question}

Provide a helpful answer:"""

    try:
        response = await asyncio.to_thread(requests.post,
            f"{VLLM_URL}/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        answer = response.json().get("response", "").strip()

    except Exception as e:
        logger.error(f"Generation error: {e}")
        answer = f"Based on the context, here's what I found:\n\n{combined_context}"

    query_time = time.time() - start

    reasoning_steps.append(f"Generated response in {query_time:.2f}s")

    return GraphRAGResponse(
        answer=answer,
        vector_sources=vector_sources,
        graph_sources=graph_sources,
        reasoning=reasoning_steps,
        query_time=query_time
    )

@app.get("/graph/entities")
async def list_entities():
    """List all entities in graph"""

    with neo4j.session() as session:
        result = session.run("MATCH (e:Entity) RETURN DISTINCT e.name as name, e.type as type ORDER BY e.name")

        entities = [{"name": record["name"], "type": record["type"]} for record in result]

        return {"entities": entities}

@app.get("/graph/explore")
async def explore_graph(entity: str, max_depth: int = 2):
    """Explore graph from entity"""

    # $parameters cannot fill Cypher path bounds - int-cast the bound first
    max_depth = max(1, int(max_depth))

    with neo4j.session() as session:
        cypher = f"""
        MATCH path = (e:Entity {{name: $entity}})-[*1..{max_depth}]-(related:Entity)
        RETURN e.name as start, related.name as end,
               length(path) as distance,
               [node in nodes(path) | node.name] as path_nodes
        ORDER BY distance, end
        LIMIT 50
        """

        result = session.run(cypher, entity=entity)

        paths = [
            {
                "start": record["start"],
                "end": record["end"],
                "distance": record["distance"],
                "path": " -> ".join(record["path_nodes"])
            }
            for record in result
        ]

        return {"entity": entity, "connections": paths}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
```

### Checkpoint: Exercise 4
**Verify:** GraphRAG service created with hybrid search

---

## Exercise 5: Docker Deployment (30 minutes)

### Task: Deploy with Docker Compose

```yaml
# ~/lab-005-graphrag/docker-compose.yml

services:
  # Neo4j Graph Database
  neo4j:
    image: neo4j:5-community
    container_name: neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/graphrag
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - ./data/graph:/data
    restart: unless-stopped
    networks:
      - graphrag-net

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
      - graphrag-net

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
      - graphrag-net

  # GraphRAG Service
  graphrag:
    build: ./services/graphrag
    container_name: graphrag-service
    ports:
      - "8004:8004"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=graphrag
      - QDRANT_URL=http://qdrant:6333
      - VLLM_URL=http://ollama:11434
    depends_on:
      - neo4j
      - qdrant
      - ollama
    restart: unless-stopped
    networks:
      - graphrag-net

networks:
  graphrag-net:
    driver: bridge
```

### Deploy:
```bash
cd ~/lab-005-graphrag
docker compose up -d --build
```

### Checkpoint: Exercise 5
**Verify:** All services running

---

## Exercise 6: Test GraphRAG (30 minutes)

### Task: Test various queries

```python
# ~/lab-005-graphrag/test_graphrag.py
import requests
import json

GRAPH_RAG_URL = "http://localhost:8004"

def test_query(question: str, use_vector: bool = True, use_graph: bool = True):
    """Test a query"""

    response = requests.post(
        f"{GRAPH_RAG_URL}/query",
        json={
            "question": question,
            "use_vector": use_vector,
            "use_graph": use_graph,
            "top_k": 3,
            "max_hops": 2
        }, timeout=120
    )

    result = response.json()

    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")

    print(f"Answer: {result['answer']}\n")

    if result['reasoning']:
        print("Reasoning:")
        for step in result['reasoning']:
            print(f"  - {step}")

    print(f"\nQuery time: {result['query_time']:.2f}s")

    if result['vector_sources']:
        print(f"\nVector sources: {len(result['vector_sources'])}")
        for source in result['vector_sources'][:2]:
            print(f"  - [{source['score']:.3f}] {source['text'][:80]}...")

    if result['graph_sources']:
        print(f"\nGraph sources: {len(result['graph_sources'])}")
        for source in result['graph_sources'][:3]:
            print(f"  - {source['path']}")

# Test queries
test_queries = [
    "What is Docker?",
    "How are Docker and Kubernetes related?",
    "Who founded Docker?",
    "What works well with Docker?",
    "What company acquired Docker?"
]

for query in test_queries:
    test_query(query)
```

### Checkpoint: Exercise 6
**Verify:** GraphRAG correctly answers questions

---

## Exercise 7: Visualize Graph (20 minutes)

### Task: Query and visualize graph

```python
# ~/lab-005-graphrag/scripts/visualize_graph.py
from neo4j import GraphDatabase
import json

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "graphrag")
)

def get_graph_statistics():
    """Get graph statistics"""

    with driver.session() as session:
        # Count entities
        entity_count = session.run("MATCH (e:Entity) RETURN count(e) as count").single()["count"]

        # Count relationships
        rel_count = session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count").single()["count"]

        # Entity types
        entity_types = session.run("""
            MATCH (e:Entity)
            RETURN e.type as type, count(e) as count
            ORDER BY count DESC
        """)

        types = {record["type"]: record["count"] for record in entity_types}

        # Most connected entities
        connections = session.run("""
            MATCH (e:Entity)-[r:RELATED_TO]->(related:Entity)
            WITH e, count(r) as degree
            RETURN e.name as entity, e.type as type, degree
            ORDER BY degree DESC
            LIMIT 10
        """)

        top_connected = [
            {"entity": record["entity"], "type": record["type"], "connections": record["degree"]}
            for record in connections
        ]

        return {
            "total_entities": entity_count,
            "total_relationships": rel_count,
            "entity_types": types,
            "top_connected": top_connected
        }

def find_shortest_path(entity1: str, entity2: str):
    """Find shortest path between entities"""

    with driver.session() as session:
        cypher = """
        MATCH path = shortestPath(
            (e1:Entity {name: $entity1})-[*]-(e2:Entity {name: $entity2})
        )
        RETURN [node in nodes(path) | node.name] as path,
               length(path) as length
        """

        result = session.run(cypher, entity1=entity1, entity2=entity2)

        path = result.single()

        if path:
            return {
                "path": path["path"],
                "hops": path["length"]
            }
        else:
            return None

# Get statistics
stats = get_graph_statistics()

print("📊 Graph Statistics")
print("="*60)
print(f"Total Entities: {stats['total_entities']}")
print(f"Total Relationships: {stats['total_relationships']}")
print(f"\nEntity Types:")
for entity_type, count in stats['entity_types'].items():
    print(f"  {entity_type}: {count}")

print(f"\nMost Connected Entities:")
for entity in stats['top_connected']:
    print(f"  {entity['entity']} ({entity['type']}): {entity['connections']} connections")

# Find paths
print(f"\n🔍 Shortest Paths")
print("="*60)

paths_to_find = [
    ("Docker", "Google"),
    ("Python", "Google"),
    ("Kubernetes", "Python")
]

for e1, e2 in paths_to_find:
    path = find_shortest_path(e1, e2)
    if path:
        print(f"\n{e1} → {e2}: {' → '.join(path['path'])} ({path['hops']} hops)")
    else:
        print(f"\n{e1} → {e2}: No path found")

driver.close()
```

### Checkpoint: Exercise 7
**Verify:** Graph statistics and paths displayed

---

## Final Challenge: Multi-Hop Reasoning (30 minutes)

### Task: Test complex reasoning

```python
# ~/lab-005-graphrag/test_reasoning.py

complex_questions = [
    {
        "question": "What technology was developed by the company that acquired Docker?",
        "reasoning": "Docker → acquired by → Microsoft → developed → Kubernetes"
    },
    {
        "question": "Who developed the technology that works well with Docker?",
        "reasoning": "Works with Docker → Kubernetes → developed by → Joe Beda, Brendan Burns, Craig McLuckie"
    },
    {
        "question": "What database can be deployed using Docker?",
        "reasoning": "Docker → can deploy → Neo4j (graph database)"
    }
]

for test in complex_questions:
    print(f"\n{'='*60}")
    print(f"Question: {test['question']}")
    print(f"Expected Reasoning: {test['reasoning']}")
    print(f"{'='*60}\n")

    result = test_query(test['question'])

    print(f"Actual Answer: {result['answer']}\n")
```

### Final Checkpoint
**Test:** Multi-hop reasoning works correctly

---

## Lab Completion Checklist

- [ ] Exercise 1: Understanding GraphRAG
- [ ] Exercise 2: Deploy Neo4j
- [ ] Exercise 3: Build Knowledge Graph
- [ ] Exercise 4: GraphRAG Service
- [ ] Exercise 5: Docker Deployment
- [ ] Exercise 6: Test GraphRAG
- [ ] Exercise 7: Visualize Graph
- [ ] Final Challenge: Multi-Hop Reasoning

---

## Post-Lab Reading

- **[6301: Neo4j and Knowledge Graphs](../../phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md)** - Graph database basics
- **[6302: CAG Long Context](../../phases/phase6-rag/6300-context/6302-CAG-Long-Context-Architectures.md)** - Long context as database
- **[6304: GraphRAG Implementation](../../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md)** - Complete implementation
- **[LAB-004: ReAct Agent](LAB-004-ReAct-Agent.md)** - Build reasoning agents

---

## Lab Badge

**Earned:** GraphRAG Implementation Badge 🏅

## Next Steps

- **[PROJECT-001: Build Your AI Assistant](../projects/PROJECT-001-AI-Assistant.md)** - Combine everything!
