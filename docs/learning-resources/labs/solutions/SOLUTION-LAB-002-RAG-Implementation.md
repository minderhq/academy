---
Document ID: SOLUTION-LAB-002
Title: "SOLUTION-LAB-002: RAG Implementation"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# SOLUTION-LAB-002: RAG Implementation

## Overview
Complete solution for building a RAG system with embeddings, vector database, and LLM.

---

## Exercise 1: Text Embeddings (20 minutes)

### Solution

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    """Generate embeddings for text chunks."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for single text."""
        return self.model.encode(text)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        return self.model.encode(texts)

# Usage
embedder = EmbeddingService()
embedding = embedder.embed("Hello, world!")
print(f"Embedding shape: {embedding.shape}")  # (384,)
```

---

## Exercise 2: Vector Database (20 minutes)

### Solution with Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class VectorStore:
    """Vector database for semantic search."""

    def __init__(self, location: str = "http://localhost:6333"):
        self.client = QdrantClient(location=location)
        self.collection_name = "documents"
        self._setup_collection()

    def _setup_collection(self):
        """Create collection if not exists."""
        from qdrant_client.models import CreateCollection

        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

    def add_documents(self, docs: list[dict]):
        """Add documents to vector store."""
        points = []
        for i, doc in enumerate(docs):
            embedding = doc["embedding"]
            points.append(PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={"text": doc["text"], "metadata": doc.get("metadata", {})}
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search(self, query_embedding: np.ndarray, top_k: int = 5):
        """Search for similar documents."""
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            limit=top_k
        ).points
        return results
```

---

## Exercise 3: RAG Pipeline (30 minutes)

### Complete Solution

```python
from typing import List, Dict
import ollama

class RAGPipeline:
    """Retrieval Augmented Generation pipeline."""

    def __init__(self, vector_store, embedder, llm_model: str = "mistral"):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_model = llm_model

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant documents."""
        query_embedding = self.embedder.embed(query)
        results = self.vector_store.search(query_embedding, top_k)

        return [hit.payload["text"] for hit in results]

    def generate(self, query: str, context: List[str]) -> str:
        """Generate response using retrieved context."""
        context_str = "\n\n".join(context)

        prompt = f"""Use the following context to answer the question:

Context:
{context_str}

Question: {query}

Answer:"""

        response = ollama.generate(model=self.llm_model, prompt=prompt)
        return response["response"]

    def query(self, question: str) -> Dict:
        """Complete RAG query."""
        # Retrieve
        docs = self.retrieve(question)

        # Generate
        answer = self.generate(question, docs)

        return {
            "question": question,
            "answer": answer,
            "sources": docs
        }

# Usage
pipeline = RAGPipeline(vector_store, embedder)
result = pipeline.query("What is RAG?")
print(result["answer"])
```

---

## Complete Working Solution

See main implementation with:
- Document chunking
- Hybrid search (keyword + semantic)
- Re-ranking
- Streaming responses

---

**Difficulty:** ⭐⭐ Intermediate
