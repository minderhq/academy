# LAB-603: Production RAG Deployment

## Overview
Deploy a production-ready RAG system with FastAPI.

## Prerequisites
- LAB-601 completed
- FastAPI and Docker knowledge

## Setup

```bash
pip install fastapi uvicorn qdrant-client sentence-transformers transformers python-multipart
```

## Exercise 1: RAG Service

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import torch

# TODO: Define models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    temperature: float = 0.7

class Document(BaseModel):
    text: str
    score: float

class QueryResponse(BaseModel):
    query: str
    context: List[Document]
    answer: str

app = FastAPI(title="Production RAG API")

# TODO: Load models (at startup)
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer
from qdrant_client import QdrantClient

# Global variables
embedder = None
generator = None
tokenizer = None
qdrant = None

# TODO: Startup event
@app.on_event("startup")
async def startup():
    global embedder, generator, tokenizer, qdrant

    # Load embedder
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    # Load generator
    generator = AutoModelForCausalLM.from_pretrained('gpt2')
    tokenizer = AutoTokenizer.from_pretrained('gpt2')
    tokenizer.pad_token = tokenizer.eos_token

    # Connect to Qdrant
    qdrant = QdrantClient(url="http://localhost:6333")

    print("Models loaded!")
```

## Exercise 2: Query Endpoint

```python
# TODO: Query endpoint
@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Process RAG query."""

    try:
        # Retrieve documents
        query_vector = embedder.encode(request.query).tolist()

        results = qdrant.search(
            collection_name="rag_docs",
            query_vector=query_vector,
            limit=request.top_k
        )

        # Extract context
        context_docs = [
            Document(text=r.payload['text'], score=r.score)
            for r in results
        ]

        # Generate response
        context_str = "\n".join([doc.text for doc in context_docs])
        prompt = f"Context:\n{context_str}\n\nQuestion: {request.query}\n\nAnswer:"

        inputs = tokenizer(prompt, return_tensors='pt')
        outputs = generator.generate(
            **inputs,
            max_new_tokens=100,
            temperature=request.temperature
        )

        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        answer = answer[len(prompt):]  # Remove prompt

        return QueryResponse(
            query=request.query,
            context=context_docs,
            answer=answer.strip()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Exercise 3: Add Documents

```python
class AddDocumentRequest(BaseModel):
    text: str
    metadata: Optional[dict] = None

@app.post("/documents")
async def add_document(request: AddDocumentRequest):
    """Add document to RAG system."""

    try:
        # Embed
        vector = embedder.encode(request.text).tolist()

        # Get next ID
        from qdrant_client.models import PointStruct
        collection_info = qdrant.get_collection("rag_docs")
        next_id = collection_info.points_count + 1

        # Insert
        point = PointStruct(
            id=next_id,
            vector=vector,
            payload={"text": request.text, **(request.metadata or {})}
        )

        qdrant.upsert(
            collection_name="rag_docs",
            points=[point]
        )

        return {"id": next_id, "status": "added"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Exercise 4: Health Check

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""

    health = {
        "status": "healthy",
        "models": {
            "embedder": embedder is not None,
            "generator": generator is not None,
            "qdrant": qdrant is not None
        }
    }

    # Check Qdrant connection
    try:
        collections = qdrant.get_collections()
        health["models"]["qdrant_collections"] = len(collections.collections)
    except:
        health["status"] = "unhealthy"
        health["models"]["qdrant"] = False

    return health
```

## Exercise 5: Dockerfile

```dockerfile
# TODO: Create Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY ./app ./app

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Exercise 6: Docker Compose

```yaml
# TODO: docker-compose.yml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage

  rag-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - qdrant
    volumes:
      - ./models:/app/models
```

## Exercise 7: Run Production

```bash
# TODO: Build and run
docker-compose up -d

# TODO: Test API
curl http://localhost:8000/health

# TODO: Add document
curl -X POST http://localhost:8000/documents \
    -H "Content-Type: application/json" \
    -d '{"text": "Paris is the capital of France."}'

# TODO: Query
curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is the capital of France?", "top_k": 3}'
```

## Exercise 8: Monitoring

```python
from prometheus_client import Counter, Histogram, generate_latest

# TODO: Metrics
query_counter = Counter('rag_queries_total', 'Total RAG queries')
query_duration = Histogram('rag_query_duration_seconds', 'RAG query duration')

@app.post("/query")
async def query_rag(request: QueryRequest):
    with query_duration.time():
        # ... process query ...
        pass

    query_counter.inc()
    return response

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

## Expected Outputs

1. Exercise 1: FastAPI app structure
2. Exercise 2: Query endpoint working
3. Exercise 3: Documents addable
4. Exercise 4: Health check working
5. Exercise 5: Dockerfile created
6. Exercise 6: Docker compose configured
7. Exercise 7: System running
8. Exercise 8: Metrics exposed

## Time Estimate: 4-5 hours

---
