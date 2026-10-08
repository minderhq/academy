---
Document ID: TUTORIAL-003
Title: "TUTORIAL-003: RAG Basics - Give Your LLM Knowledge"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 60 minutes
Prerequisites: [TUTORIAL-000, TUTORIAL-001]
Tags: ['tutorial', 'rag', 'qdrant', 'hands-on']
---

# TUTORIAL-003: RAG Basics - Give Your LLM Knowledge

**Difficulty:** ⭐⭐ Intermediate
**Time:** 60 minutes
**Prerequisites:**

- **[TUTORIAL-001: Hello LLM](TUTORIAL-001-Hello-LLM.md)** - LLM basics
- **[TUTORIAL-000: Python for AI](TUTORIAL-000-Python-for-AI.md)** - Classes, functions, error handling

ℹ️ **Not comfortable with Python classes?** Complete **TUTORIAL-000** first (Parts 3-4 cover OOP and practical skills).

---

## Learning Objectives

By the end of this tutorial, you will:

- ✅ Understand what RAG is
- ✅ Build a simple vector database
- ✅ Implement semantic search
- ✅ Create a knowledge-augmented chatbot

---

## What is RAG?

**RAG** = **Retrieval-Augmented Generation**

Think of RAG like an **open-book exam** for AI:

```text
Without RAG (Closed Book):
Question: "What is Minder Academy?"
LLM: "I don't know, my training data cutoff was earlier."

With RAG (Open Book):
Question: "What is Minder Academy?"
RAG: "Let me search the documents..."
Found: "Minder Academy is an AI infrastructure learning platform"
LLM: "Minder Academy is an AI infrastructure learning platform..."
```

### RAG Architecture:

```text
┌─────────────────────────────────────────────────────────────┐
│                     RAG Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Your Question                                         │
│     ↓                                                      │
│  2. Search Vector Database  ←→  (Find relevant docs)       │
│     ↓                                                      │
│  3. Retrieve Context                                       │
│     ↓                                                      │
│  4. Augment Prompt                                         │
│     "Use this context: {retrieved_docs}                    │
│      Answer: {question}"                                    │
│     ↓                                                      │
│  5. LLM Generates Answer                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Install Dependencies

```bash
uv pip install sentence-transformers qdrant-client fastapi uvicorn
```

### What we're installing:
- **sentence-transformers**: Converts text to vectors (embeddings)
- **qdrant-client**: Vector database client
- **fastapi**: Web framework for our API

---

## Step 2: Understanding Embeddings

**Embeddings** = Numbers that represent meaning

### Example:
```python
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Convert text to vector
text = "Artificial Intelligence is transforming the world"
embedding = model.encode(text)

print(f"Text: {text}")
print(f"Embedding shape: {embedding.shape}")  # (384,)
print(f"First 10 values: {embedding[:10]}")
```

### How it works:
```text
"cat"  → [0.1, -0.5, 0.8, ...]   (384 numbers)
"dog"  → [0.2, -0.3, 0.7, ...]   (384 numbers)

Similar concepts have similar vectors!
```

---

## Step 3: Create Your Knowledge Base

```bash
# Create project directory
mkdir rag-demo
cd rag-demo

# Create knowledge base
mkdir -p documents

# Add some documents
cat > documents/doc1.txt << 'EOF'
Minder Academy is a comprehensive learning platform for AI infrastructure.
It covers topics from basic Docker to advanced agent systems.
EOF

cat > documents/doc2.txt << 'EOF'
A GPU like the 11GB-class GPU has 11GB of VRAM and is suitable for running 7B parameter models.
It supports tensor cores for accelerated AI workloads.
EOF

cat > documents/doc3.txt << 'EOF'
Qdrant is a vector database used for semantic search and RAG applications.
It can store millions of vectors and perform fast similarity searches.
EOF
```

---

## Step 4: Build Vector Database

```python
# rag_demo/vector_store.py
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os

class VectorStore:
    """Simple vector store for RAG"""

    def __init__(self, collection_name="documents"):
        # Initialize Qdrant client
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = collection_name

        # Load embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Create collection if not exists
        self._create_collection()

    def _create_collection(self):
        """Create Qdrant collection"""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"Created collection: {self.collection_name}")

    def add_documents(self, documents):
        """Add documents to vector store"""
        points = []

        for idx, (text, metadata) in enumerate(documents):
            # Create embedding
            embedding = self.model.encode(text).tolist()

            # Create point
            point = PointStruct(
                id=idx,
                vector=embedding,
                payload={"text": text, **metadata}
            )
            points.append(point)

        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Added {len(points)} documents")

    def search(self, query, limit=3):
        """Search for similar documents"""
        # Create query embedding
        query_embedding = self.model.encode(query).tolist()

        # Search
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit
        ).points

        return results

# Test it
if __name__ == "__main__":
    # Create vector store
    vs = VectorStore()

    # Load documents
    documents = []
    for filename in os.listdir("documents"):
        if filename.endswith(".txt"):
            with open(f"documents/{filename}", "r") as f:
                text = f.read()
                documents.append((text, {"source": filename}))

    # Add to vector store
    vs.add_documents(documents)

    # Test search
    query = "What GPU should I use for AI?"
    results = vs.search(query)

    print(f"\nQuery: {query}\n")
    print("Top results:")
    for result in results:
        print(f"\nScore: {result.score:.4f}")
        print(f"Text: {result.payload['text']}")
```

### Run Qdrant with Docker:
```bash
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_data:/qdrant/storage \
  qdrant/qdrant
```

### Test the vector store:
```bash
python rag_demo/vector_store.py
```

---

## Step 5: Build RAG Application

```python
# rag_demo/rag_app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vector_store import VectorStore
import ollama

app = FastAPI(title="Simple RAG")

# Initialize components
vector_store = VectorStore()

class Query(BaseModel):
    text: str
    use_rag: bool = True

def get_llm_response(prompt: str) -> str:
    """Get response from local LLM"""
    response = ollama.chat(model='mistral', messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']

@app.post("/query")
def query(query: Query):
    """Query with or without RAG"""

    if query.use_rag:
        # RAG: Retrieve relevant documents first
        results = vector_store.search(query.text, limit=2)

        # Build context
        context = "\n".join([
            f"- {r.payload['text']}"
            for r in results
        ])

        # Augment prompt
        augmented_prompt = f"""Use the following context to answer the question:

Context:
{context}

Question: {query.text}

Answer:"""

        # Generate response
        response = get_llm_response(augmented_prompt)

        return {
            "response": response,
            "context_used": [r.payload['text'] for r in results],
            "mode": "RAG"
        }

    else:
        # No RAG: Direct query
        response = get_llm_response(query.text)

        return {
            "response": response,
            "mode": "Direct"
        }

@app.get("/")
def root():
    return {
        "message": "Simple RAG API",
        "endpoints": {
            "/query": "POST - Query with RAG",
            "/documents": "POST - Add documents"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Test the RAG app:
```bash
# Start the app
python rag_demo/rag_app.py

# Test with curl
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What GPU is recommended?", "use_rag": true}'
```

---

## Step 6: Compare RAG vs Non-RAG

```python
# Test RAG vs direct query
queries = [
    "What is Minder Academy?",
    "How much VRAM does 11GB-class GPU have?",
    "What is Qdrant used for?"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    # Without RAG
    response_no_rag = ollama.chat(model='mistral', messages=[
        {'role': 'user', 'content': query}
    ])
    print(f"\nWithout RAG:\n{response_no_rag['message']['content']}\n")

    # With RAG
    rag_results = vector_store.search(query, limit=2)
    context = "\n".join([r.payload['text'] for r in rag_results])

    rag_prompt = f"""Use this context: {context}

Question: {query}
Answer:"""

    response_rag = ollama.chat(model='mistral', messages=[
        {'role': 'user', 'content': rag_prompt}
    ])
    print(f"With RAG:\n{response_rag['message']['content']}\n")
```

---

## Step 7: RAG Best Practices

### 1. Chunking
```python
def chunk_text(text, chunk_size=512, overlap=50):
    """Split text into overlapping chunks"""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)
    return chunks
```

### 2. Hybrid Search
```python
def hybrid_search(query, alpha=0.5):
    """Combine keyword and semantic search"""
    # Semantic search
    semantic_results = vector_store.search(query)

    # Keyword search (BM25)
    keyword_results = keyword_search(query)

    # Combine scores
    combined = {}
    for result in semantic_results:
        combined[result.id] = alpha * result.score
    for result in keyword_results:
        if result.id in combined:
            combined[result.id] += (1 - alpha) * result.score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)
```

### 3. Re-ranking
```python
def rerank(results, query):
    """Re-rank results using a more sophisticated model"""
    from sentence_transformers import CrossEncoder

    reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    pairs = [[query, result.payload['text']] for result in results]
    scores = reranker.predict(pairs)

    # Sort by rerank scores
    reranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
    return [r[0] for r in reranked]
```

---

## Step 8: Advanced RAG with GraphRAG

Minder Academy also supports **GraphRAG** - combining vector search with knowledge graphs!

```text
Vector RAG:              GraphRAG:
┌─────────┐              ┌──────────────┐
│  Query  │              │    Query    │
└────┬────┘              └──────┬───────┘
     │                          │
     ▼                          ▼
┌─────────┐              ┌──────────────┐
│ Vectors │              │ Knowledge    │
│ (Qdrant)│              │ Graph        │
└────┬────┘              │ (Neo4j)      │
     │                   └──────┬───────┘
     ▼                          │
┌─────────┐                    ▼
│  LLM    │              ┌──────────────┐
└─────────┘              │ Multi-hop    │
                         │ Reasoning    │
                         └──────┬───────┘
                                ▼
                         ┌──────────────┐
                         │     LLM      │
                         └──────────────┘
```

### Learn More:
- [6304: GraphRAG Implementation](../../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md)
- [6301: Neo4j and Knowledge Graphs](../../phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md)

---

## Step 9: Common RAG Issues

### Issue: Poor Retrieval
**Symptoms:** RAG returns irrelevant documents

**Solutions:**

1. Better chunking strategy
2. Use hybrid search (keyword + semantic)
3. Add re-ranking step
4. Improve embeddings (larger model)

### Issue: Slow Response
**Symptoms:** RAG takes too long

**Solutions:**

1. Limit retrieval count (top_k=3 instead of 10)
2. Use faster embedding model
3. Cache embeddings
4. Use GPU for inference

### Issue: Hallucinations
**Symptoms:** LLM makes things up even with context

**Solutions:**

1. Improve prompt engineering
2. Add citations to sources
3. Use constrained generation
4. Verify responses

---

## Step 10: Production RAG

For production, use a dedicated compose file. The reference stack lives in
[`configs/docker-compose.yml`](../../../configs/docker-compose.yml) — add a
GraphRAG service alongside it when you need graph-aware retrieval:

```yaml
# Add to configs/docker-compose.yml (or a separate override file)
services:
  neo4j:
    image: neo4j:5.15-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/your_secure_password

  graphrag:
    build: ./services/graphrag
    environment:
      - QDRANT_URL=http://qdrant:6334
      - NEO4J_URI=bolt://neo4j:7687
      - ALPHA=0.5  # Balance vector vs graph
```

---

## Knowledge Check

1. **What does RAG stand for?**
   - Retrieval-Augmented Generation

2. **What is the main benefit of RAG?**
   - Gives LLM access to up-to-date, custom knowledge

3. **What are embeddings?**
   - Numerical representations of text meaning

4. **Why chunk documents before embedding?**
   - Embedding models have token limits, and smaller chunks improve retrieval relevance

---

## What's Next?

1. **[TUTORIAL-004: Monitoring](./TUTORIAL-004-Monitoring.md)** - Track model and system health
2. **[6201: Hybrid Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)** - Advanced retrieval
3. **[6304: GraphRAG Implementation](../../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md)** - Production RAG

---

## Complete Code Example

```python
# complete_rag.py
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import ollama

class SimpleRAG:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection = "my_docs"

    def add(self, text, metadata=None):
        emb = self.model.encode(text).tolist()
        self.client.upsert(
            collection_name=self.collection,
            points=[{
                "id": hash(text),
                "vector": emb,
                "payload": {"text": text, **(metadata or {})}
            }]
        )

    def query(self, question):
        # Retrieve
        emb = self.model.encode(question).tolist()
        results = self.client.query_points(
            collection_name=self.collection,
            query=emb,
            limit=2
        ).points

        # Augment
        context = "\n".join([r.payload['text'] for r in results])
        prompt = f"Context: {context}\n\nQuestion: {question}\nAnswer:"

        # Generate
        response = ollama.chat(model='mistral', messages=[
            {'role': 'user', 'content': prompt}
        ])

        return response['message']['content']

# Use it
rag = SimpleRAG()
rag.add("Minder Academy is a learning platform for AI infrastructure")
print(rag.query("What is Minder Academy?"))
```

---

## Next Steps

- TUTORIAL-004: [Monitoring](./TUTORIAL-004-Monitoring.md)
