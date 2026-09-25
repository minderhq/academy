---
Document ID: LAB-002
Title: "LAB 002: RAG Implementation with Qdrant & Ollama"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# LAB 002: RAG Implementation with Qdrant & Ollama

**Prerequisites:**
- **[Tutorial 001: Hello LLM](../tutorials/TUTORIAL-001-Hello-LLM.md)** - LLM basics
- **[Tutorial 002: Docker Essentials](../tutorials/TUTORIAL-002-Docker-Essentials.md)** - Docker fundamentals
- **[Tutorial 003: RAG Basics](../tutorials/TUTORIAL-003-RAG-Basics.md)** - RAG concepts
- **[LAB 001: Docker & LLM](LAB-001-Docker-LLM.md)** - Docker practice
- **[TUTORIAL-000: Python for AI](../tutorials/TUTORIAL-000-Python-for-AI.md)** - REQUIRED for RAG code

**Time:** 3 hours
**Difficulty:** ⭐⭐ Intermediate

:warning: **Python Required:** This lab involves significant Python coding (classes, async, type hints). If you haven't completed **TUTORIAL-000**, start there first.

---

## Lab Objectives

After completing this lab, you will be able to:
- ✅ Deploy Qdrant vector database in Docker
- ✅ Implement document chunking strategies
- ✅ Build a complete RAG pipeline
- ✅ Compare different embedding models
- ✅ Add re-ranking for better results
- ✅ Deploy with Docker Compose

---

## Setup Instructions

```bash
# Create lab directory
mkdir ~/lab-002-rag
cd ~/lab-002-rag

# Create directory structure
mkdir -p services/rag
mkdir -p data/documents
mkdir -p data/qdrant
```

---

## Exercise 1: Deploy Qdrant Vector Database (20 minutes)

### Task: Deploy Qdrant with persistence

```bash
# Run Qdrant with volume mount
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v ~/lab-002-rag/data/qdrant:/qdrant/storage \
  qdrant/qdrant:latest

# Verify it's running
docker ps | grep qdrant

# Check Qdrant API
curl http://localhost:6333/

# View dashboard
# Open http://localhost:6333/dashboard in your browser
```

### Create a test collection:

```bash
# Create collection with cosine similarity
curl -X PUT http://localhost:6333/collections/test_docs \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'

# Verify collection exists
curl http://localhost:6333/collections/test_docs
```

### ✅ Checkpoint: Exercise 1
**Verify:** You should see collection info with vectors configured

**Expected Output:**
```json
{
  "result": {
    "status": "green",
    "vectors_count": 0,
    "indexed_vectors_count": 0
  }
}
```

---

## Exercise 2: Document Chunking Strategies (30 minutes)

### Task: Implement different chunking methods

```python
# ~/lab-002-rag/services/rag/chunker.py
from typing import List, Dict
import re

class DocumentChunker:
    """Split documents into chunks for embedding"""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        method: str = "recursive"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.method = method

    def chunk_text(self, text: str) -> List[Dict[str, any]]:
        """Split text into chunks with metadata"""

        if self.method == "recursive":
            return self._recursive_chunk(text)
        elif self.method == "semantic":
            return self._semantic_chunk(text)
        elif self.method == "fixed":
            return self._fixed_chunk(text)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def _recursive_chunk(self, text: str) -> List[Dict[str, any]]:
        """Recursive character splitting with multiple separators"""

        # Try different separators in order
        separators = ["\n\n", "\n", ". ", " ", ""]

        chunks = []
        current_text = text

        while len(current_text) > self.chunk_size:
            # Find best split point
            split_pos = self._find_split_pos(current_text, separators)

            chunk = current_text[:split_pos].strip()
            chunks.append({
                "text": chunk,
                "metadata": {
                    "method": "recursive",
                    "length": len(chunk)
                }
            })

            # Move forward with overlap
            current_text = current_text[split_pos - self.chunk_overlap:]

        # Add remaining text
        if current_text.strip():
            chunks.append({
                "text": current_text.strip(),
                "metadata": {
                    "method": "recursive",
                    "length": len(current_text)
                }
            })

        return chunks

    def _fixed_chunk(self, text: str) -> List[Dict[str, any]]:
        """Fixed-size character chunks"""

        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            chunks.append({
                "text": chunk,
                "metadata": {
                    "method": "fixed",
                    "start": i,
                    "length": len(chunk)
                }
            })

        return chunks

    def _semantic_chunk(self, text: str) -> List[Dict[str, any]]:
        """Sentence-based semantic chunks"""

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = ""
        current_start = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": {
                            "method": "semantic",
                            "sentences": current_chunk.count('.'),
                            "start": current_start
                        }
                    })
                    current_start += len(current_chunk)
                current_chunk = sentence + " "

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": {
                    "method": "semantic",
                    "sentences": current_chunk.count('.'),
                    "start": current_start
                }
            })

        return chunks

    def _find_split_pos(self, text: str, separators: List[str]) -> int:
        """Find best position to split text"""

        for sep in separators:
            # Search for separator before chunk_size
            search_text = text[:self.chunk_size]
            last_pos = search_text.rfind(sep)

            if last_pos > self.chunk_size * 0.3:  # At least 30% of chunk
                return last_pos + len(sep)

        # Fallback to exact chunk size
        return self.chunk_size
```

### Test the chunker:

```python
# ~/lab-002-rag/test_chunker.py
from chunker import DocumentChunker

# Sample document
sample_text = """
Python is a high-level, interpreted programming language known for its simplicity
and readability. It was created by Guido van Rossum and first released in 1991.

Python supports multiple programming paradigms, including procedural, object-oriented,
and functional programming. Its design philosophy emphasizes code readability with
the use of significant indentation.

Python is dynamically typed and garbage-collected. It supports various programming
patterns such as structural, object-oriented, and functional programming.
"""

# Test different methods
chunker = DocumentChunker(chunk_size=200, chunk_overlap=30, method="recursive")
chunks = chunker.chunk_text(sample_text)

print(f"Generated {len(chunks)} chunks:")
for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i+1} ({chunk['metadata']['length']} chars) ---")
    print(chunk['text'][:100] + "...")
```

### ✅ Checkpoint: Exercise 2
**Verify:** You should see chunks with proper overlap and metadata

---

## Exercise 3: Build Complete RAG Pipeline (45 minutes)

### Task: Create RAG service with embeddings and retrieval

```python
# ~/lab-002-rag/services/rag/rag_service.py
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
import uuid

# Configuration
QDRANT_URL = "http://qdrant:6333"
OLLAMA_URL = "http://ollama:11434"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "documents"

# Initialize clients
qdrant = QdrantClient(url=QDRANT_URL)
embedder = SentenceTransformer(EMBEDDING_MODEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the Qdrant collection exists before serving traffic.

    Guarded create - recreate_collection would wipe every stored
    vector, so a service restart must never go through it.
    """
    if not qdrant.collection_exists(COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,  # all-MiniLM-L6-v2 dimension
                distance=Distance.COSINE
            )
        )
    yield


# on_event("startup") is deprecated - lifespan owns startup AND shutdown
app = FastAPI(title="RAG Service", lifespan=lifespan)

class Document(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = {}

class Query(BaseModel):
    question: str
    top_k: int = 3
    filter_metadata: Optional[Dict[str, Any]] = None

class RAGResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    query_time: float

@app.get("/")
def root():
    return {
        "service": "RAG Service",
        "endpoints": {
            "/ingest": "Add documents to knowledge base",
            "/query": "Query with RAG",
            "/search": "Vector search only",
            "/docs": "List all documents"
        }
    }

@app.post("/ingest")
async def ingest_document(doc: Document):
    """Add document to knowledge base"""

    # Generate unique ID
    doc_id = hashlib.md5(doc.text.encode()).hexdigest()

    # Chunk document
    from chunker import DocumentChunker
    chunker = DocumentChunker(
        chunk_size=512,
        chunk_overlap=50,
        method="recursive"
    )
    chunks = chunker.chunk_text(doc.text)

    # Create points for Qdrant
    points = []
    for i, chunk in enumerate(chunks):
        # Generate embedding
        embedding = embedder.encode(chunk['text']).tolist()

        # Create point
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": chunk['text'],
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}_{i}",
                **chunk['metadata'],
                **doc.metadata
            }
        )
        points.append(point)

    # Insert into Qdrant
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return {
        "status": "success",
        "doc_id": doc_id,
        "chunks_added": len(chunks)
    }

@app.post("/query", response_model=RAGResponse)
async def query_rag(query: Query):
    """Query with RAG - retrieve and generate"""

    import time
    start = time.time()

    # Generate query embedding
    query_vector = embedder.encode(query.question).tolist()

    # Search Qdrant
    search_result = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=query.top_k,
        query_filter=None  # Add metadata filter if needed
    )

    if not search_result:
        raise HTTPException(status_code=404, detail="No relevant documents found")

    # Extract context
    context = "\n\n".join([hit.payload['text'] for hit in search_result])

    # Prepare sources
    sources = [
        {
            "text": hit.payload['text'],
            "score": hit.score,
            "metadata": {k: v for k, v in hit.payload.items() if k != 'text'}
        }
        for hit in search_result
    ]

    # Generate response with Ollama
    prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {query.question}

Provide a helpful answer based on the context. If the context doesn't contain enough information, say so."""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        answer = response.json().get("response", "")

    except Exception as e:
        # Fallback: return context without generation
        answer = f"Based on the retrieved context:\n\n{context}"

    query_time = time.time() - start

    return RAGResponse(
        answer=answer,
        sources=sources,
        query_time=query_time
    )

@app.post("/search")
async def vector_search(query: Query):
    """Vector search only - no generation"""

    query_vector = embedder.encode(query.question).tolist()

    search_result = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=query.top_k
    )

    return {
        "results": [
            {
                "text": hit.payload['text'],
                "score": hit.score,
                "metadata": {k: v for k, v in hit.payload.items() if k != 'text'}
            }
            for hit in search_result
        ]
    }

@app.get("/docs")
async def list_documents():
    """List all documents in knowledge base"""

    # Get all points
    result = qdrant.scroll(
        collection_name=COLLECTION_NAME,
        limit=1000,
        with_payload=True
    )

    # Extract unique doc_ids
    doc_ids = set()
    for point in result[0]:
        doc_ids.add(point.payload.get('doc_id'))

    return {
        "total_documents": len(doc_ids),
        "total_chunks": result[1],
        "document_ids": list(doc_ids)
    }

@app.delete("/docs/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and all its chunks"""

    # Delete by filter
    qdrant.delete(
        collection_name=COLLECTION_NAME,
        points_selector={
            "filter": {
                "must": [
                    {"key": "doc_id", "match": {"value": doc_id}}
                ]
            }
        }
    )

    return {"status": "deleted", "doc_id": doc_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Create requirements.txt:

```bash
cat > ~/lab-002-rag/services/rag/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
requests==2.31.0
pydantic==2.5.3
qdrant-client==1.7.0
sentence-transformers==2.3.1
numpy==1.26.3
EOF
```

### Create Dockerfile:

```bash
cat > ~/lab-002-rag/services/rag/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download embedding model (cache in image)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application
COPY . .

EXPOSE 8001

CMD ["uvicorn", "rag_service:app", "--host", "0.0.0.0", "--port", "8001"]
EOF
```

### ✅ Checkpoint: Exercise 3
**Verify:** RAG service created with all endpoints

---

## Exercise 4: Docker Compose Deployment (30 minutes)

### Task: Deploy complete stack with Docker Compose

```bash
cat > ~/lab-002-rag/docker-compose.yml << 'EOF'

services:
  # Ollama LLM server
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
      - rag-network

  # Qdrant vector database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage
    restart: unless-stopped
    networks:
      - rag-network

  # RAG API service
  rag:
    build: ./services/rag
    container_name: rag-service
    ports:
      - "8001:8001"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - ollama
      - qdrant
    restart: unless-stopped
    networks:
      - rag-network

networks:
  rag-network:
    driver: bridge
EOF
```

### Deploy everything:

```bash
cd ~/lab-002-rag

# Pull Mistral model first (faster than in container)
docker run --rm -v ~/lab-002-rag/data/models:/root/.ollama \
  ollama/ollama:latest ollama pull mistral

# Build and start
docker-compose build
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f rag
```

### ✅ Checkpoint: Exercise 4
**Verify:** All 3 services running and healthy

---

## Exercise 5: Ingest and Query (30 minutes)

### Task: Add documents and test RAG pipeline

```bash
# Create sample documents
cat > ~/lab-002-rag/data/documents/sample.txt << 'EOF'
Docker is a platform for developing, shipping, and running applications in containers.
Containers are lightweight, standalone packages that include everything needed to run an application.

Key benefits of Docker:
- Portability: Run anywhere
- Isolation: No dependency conflicts
- Efficiency: Less overhead than VMs
- Scalability: Easy to orchestrate

Docker uses a client-server architecture with the Docker daemon, REST API, and CLI.
EOF

cat > ~/lab-002-rag/data/documents/kubernetes.txt << 'EOF'
Kubernetes (K8s) is an open-source container orchestration platform.
It automates deployment, scaling, and management of containerized applications.

Key Kubernetes concepts:
- Pods: Smallest deployable units
- Services: Network abstraction for pods
- Deployments: Declarative updates for pods
- Namespaces: Logical clusters within a cluster

Kubernetes was originally developed by Google and is now maintained by CNCF.
EOF
```

### Ingest documents:

```bash
# Ingest Docker document
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Docker is a platform for developing, shipping, and running applications in containers. Containers are lightweight, standalone packages that include everything needed to run an application. Key benefits of Docker: Portability - Run anywhere, Isolation - No dependency conflicts, Efficiency - Less overhead than VMs, Scalability - Easy to orchestrate. Docker uses a client-server architecture with the Docker daemon, REST API, and CLI.",
    "metadata": {"source": "docs/docker.txt", "topic": "docker"}
  }'

# Ingest Kubernetes document
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Kubernetes (K8s) is an open-source container orchestration platform. It automates deployment, scaling, and management of containerized applications. Key Kubernetes concepts: Pods - Smallest deployable units, Services - Network abstraction for pods, Deployments - Declarative updates for pods, Namespaces - Logical clusters within a cluster. Kubernetes was originally developed by Google and is now maintained by CNCF.",
    "metadata": {"source": "docs/k8s.txt", "topic": "kubernetes"}
  }'

# Check documents
curl http://localhost:8001/docs
```

### Query RAG system:

```bash
# Query about Docker
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the benefits of Docker?",
    "top_k": 3
  }' | jq

# Query about Kubernetes
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a pod in Kubernetes?",
    "top_k": 3
  }' | jq

# Compare vector search only
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "container orchestration",
    "top_k": 3
  }' | jq
```

### ✅ Checkpoint: Exercise 5
**Verify:** Queries return relevant answers with sources

---

## Exercise 6: Compare Embedding Models (30 minutes)

### Task: Test different embedding models for quality

```python
# ~/lab-002-rag/compare_embeddings.py
import requests
import time
from sentence_transformers import SentenceTransformer

MODELS = {
    "all-MiniLM-L6-v2": 384,      # Fast, good quality
    "all-mpnet-base-v2": 768,      # Slower, better quality
    "paraphrase-MiniLM-L6-v2": 384 # Optimized for paraphrases
}

def test_model(model_name: str, query: str):
    """Test an embedding model"""

    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")

    # Load model
    start = time.time()
    model = SentenceTransformer(model_name)
    load_time = time.time() - start
    print(f"Model load time: {load_time:.2f}s")

    # Embed query
    start = time.time()
    embedding = model.encode(query)
    embed_time = time.time() - start
    print(f"Embedding time: {embed_time:.2f}s")
    print(f"Embedding dimension: {len(embedding)}")

    # Search using custom embedding
    # Note: This would require updating the RAG service to accept custom embeddings

    return {
        "model": model_name,
        "dimension": len(embedding),
        "load_time": load_time,
        "embed_time": embed_time
    }

# Test queries
queries = [
    "What is container orchestration?",
    "How does Docker work?",
    "Explain Kubernetes pods"
]

results = {}
for model_name in MODELS:
    results[model_name] = []
    for query in queries:
        result = test_model(model_name, query)
        results[model_name].append(result)

# Compare
print(f"\n{'='*60}")
print("Model Comparison Summary")
print(f"{'='*60}")

for model_name, model_results in results.items():
    avg_embed = sum(r['embed_time'] for r in model_results) / len(model_results)
    print(f"\n{model_name}:")
    print(f"  Dimension: {model_results[0]['dimension']}")
    print(f"  Avg embed time: {avg_embed:.4f}s")
```

### ✅ Checkpoint: Exercise 6
**Verify:** Understand trade-offs between speed and quality

---

## Exercise 7: Add Re-ranking (45 minutes)

### Task: Implement re-ranking for better results

```python
# ~/lab-002-rag/services/rag/reranker.py
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import CrossEncoder

class ReRanker:
    """Re-rank search results using cross-encoder"""

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-6-v2"):
        """
        Args:
            model_name: Cross-encoder model for reranking
        """
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results using cross-encoder

        Args:
            query: Original query
            results: Initial search results
            top_k: Number of results to return

        Returns:
            Re-ranked results
        """

        if not results:
            return []

        # Prepare pairs for cross-encoder
        pairs = [[query, result['text']] for result in results]

        # Score pairs
        scores = self.model.predict(pairs)

        # Add scores to results
        for result, score in zip(results, scores):
            result['rerank_score'] = float(score)

        # Sort by rerank score
        reranked = sorted(results, key=lambda x: x['rerank_score'], reverse=True)

        return reranked[:top_k]
```

### Update RAG service to use re-ranking:

```python
# Add to ~/lab-002-rag/services/rag/rag_service.py
from reranker import ReRanker

# Initialize reranker
reranker = ReRanker()

# Update query endpoint
@app.post("/query/reranked", response_model=RAGResponse)
async def query_rag_with_reranking(query: Query):
    """Query with RAG and re-ranking"""

    import time
    start = time.time()

    # Generate query embedding
    query_vector = embedder.encode(query.question).tolist()

    # Search Qdrant (get more results for reranking)
    search_result = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=query.top_k * 2  # Get more for reranking
    )

    if not search_result:
        raise HTTPException(status_code=404, detail="No relevant documents found")

    # Prepare results for reranking
    results_for_rerank = [
        {
            "text": hit.payload['text'],
            "score": hit.score,
            "metadata": {k: v for k, v in hit.payload.items() if k != 'text'}
        }
        for hit in search_result
    ]

    # Re-rank
    reranked = reranker.rerank(query.question, results_for_rerank, top_k=query.top_k)

    # Extract context from reranked results
    context = "\n\n".join([r['text'] for r in reranked])

    # Generate response
    prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {query.question}

Provide a helpful answer based on the context."""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        answer = response.json().get("response", "")

    except Exception as e:
        answer = f"Based on the retrieved context:\n\n{context}"

    query_time = time.time() - start

    return RAGResponse(
        answer=answer,
        sources=reranked,
        query_time=query_time
    )
```

### Test re-ranking:

```bash
# Compare with and without re-ranking
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main components of Kubernetes?",
    "top_k": 3
  }'

curl -X POST http://localhost:8001/query/reranked \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main components of Kubernetes?",
    "top_k": 3
  }'
```

### ✅ Checkpoint: Exercise 7
**Verify:** Re-ranked results show better relevance

---

## Final Challenge: Build RAG Chatbot (30 minutes)

### Task: Create a conversational interface

```python
# ~/lab-002-rag/chatbot.py
import requests
import json

class RAGChatbot:
    """Conversational RAG interface"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.history = []

    def ask(self, question: str, use_reranking: bool = True):
        """Ask a question"""

        # Add to history
        self.history.append({"role": "user", "content": question})

        # Choose endpoint
        endpoint = "/query/reranked" if use_reranking else "/query"

        # Query RAG
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json={"question": question, "top_k": 3},
            timeout=120
        )

        result = response.json()
        answer = result['answer']

        # Add to history
        self.history.append({"role": "assistant", "content": answer})

        return {
            "answer": answer,
            "sources": result['sources'],
            "time": result['query_time']
        }

    def chat(self):
        """Interactive chat loop"""

        print("🤖 RAG Chatbot (type 'quit' to exit)")
        print("="*60)

        while True:
            question = input("\nYou: ").strip()

            if question.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break

            if not question:
                continue

            # Get answer
            result = self.ask(question)

            # Display answer
            print(f"\nAI: {result['answer']}")

            # Display sources
            if result['sources']:
                print("\nSources:")
                for i, source in enumerate(result['sources'], 1):
                    score = source.get('rerank_score', source['score'])
                    print(f"  {i}. [{score:.3f}] {source['text'][:80]}...")

            print(f"\n⏱️  {result['time']:.2f}s")

# Run chatbot
if __name__ == "__main__":
    chatbot = RAGChatbot()
    chatbot.chat()
```

### Run the chatbot:

```bash
python ~/lab-002-rag/chatbot.py
```

### ✅ Final Checkpoint
**Test:** Have a conversation with your RAG chatbot

---

## 🎓 Lab Completion Checklist

```text
[ ] Exercise 1: Deploy Qdrant Vector Database
[ ] Exercise 2: Document Chunking Strategies
[ ] Exercise 3: Build Complete RAG Pipeline
[ ] Exercise 4: Docker Compose Deployment
[ ] Exercise 5: Ingest and Query
[ ] Exercise 6: Compare Embedding Models
[ ] Exercise 7: Add Re-ranking
[ ] Final Challenge: RAG Chatbot
```

---

## 📚 Post-Lab Reading

- **[6101: HNSW Indexing](../../phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md)** - Vector search algorithms
- **[6201: Hybrid Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)** - Combine keyword + semantic
- **[6304: GraphRAG Implementation](../../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md)** - Add knowledge graphs

---

## 🏆 Lab Badge

**Earned:** RAG Implementation Badge 🏅

Next: **[LAB 003: LoRA Fine-Tuning](LAB-003-LoRA-FineTuning.md)**
