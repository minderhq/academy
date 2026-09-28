---
Document ID: LAB-007
Title: "LAB-007: Production RAG System"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# LAB-007: Production RAG System

**Build enterprise-grade RAG with hybrid search, re-ranking, and monitoring**

**Time:** 6-8 hours
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:**
- LAB-002: RAG Implementation
- 6101-HNSW-Indexing.md
- 6201-Hybrid-Search.md
- 6202-Re-ranking-and-Retrieval-Logistics.md
- 6401-Qdrant-Setup.md

---

## 🎯 Lab Objectives

After completing this lab, you will be able to:
- ✅ Build hybrid search (vector + keyword)
- ✅ Implement re-ranking with cross-encoders
- ✅ Create multi-tenant RAG system
- ✅ Add monitoring and observability
- ✅ Deploy production RAG with load balancing

---

## 📋 Overview

### What is Production RAG?

**Production RAG** goes beyond basic RAG with:
- **Hybrid Search:** Vector + keyword combined
- **Re-ranking:** Cross-encoder for quality
- **Multi-tenancy:** Isolated data per client
- **Monitoring:** Track performance and quality
- **Scaling:** Handle thousands of requests/sec

### Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                      Load Balancer                       │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  RAG Pod  │   │  RAG Pod  │   │  RAG Pod  │
    └───────────┘   └───────────┘   └───────────┘
            │               │               │
            └───────────────┼───────────────┘
                            ▼
    ┌───────────────────────────────────────────────┐
    │              Qdrant Cluster (3 nodes)          │
    │  - Vector Search (HNSW)                       │
    │  - Payload Filtering                           │
    └───────────────────────────────────────────────┘
                            │
    ┌───────────────────────────────────────────────┐
    │           Re-ranking Service                  │
    └───────────────────────────────────────────────┘
```

---

## 🏗️ Part 1: Setup Infrastructure (60 min)

### Step 1.1: Deploy Qdrant Cluster

```bash
# Create Qdrant cluster directory
mkdir -p qdrant-cluster/{node1,node2,node3}

# Create docker-compose for Qdrant cluster
cat > qdrant-cluster/docker-compose.yml << 'EOF'

services:
  qdrant-node1:
    image: qdrant/qdrant:v1.7.0
    container_name: qdrant-node1
    hostname: qdrant-node1
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./node1/storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=DEBUG

  qdrant-node2:
    image: qdrant/qdrant:v1.7.0
    container_name: qdrant-node2
    hostname: qdrant-node2
    ports:
      - "6335:6333"
      - "6336:6334"
    volumes:
      - ./node2/storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=DEBUG

  qdrant-node3:
    image: qdrant/qdrant:v1.7.0
    container_name: qdrant-node3
    hostname: qdrant-node3
    ports:
      - "6337:6333"
      - "6338:6334"
    volumes:
      - ./node3/storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=DEBUG

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
EOF

# Start cluster
cd qdrant-cluster
docker-compose up -d

# Verify
curl http://localhost:6333/health
curl http://localhost:6335/health
curl http://localhost:6337/health
```

### Step 1.2: Setup RAG Application

```bash
# Create RAG service directory
mkdir -p rag-service/{app,config}

# Create requirements.txt
cat > rag-service/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.24.0
qdrant-client==1.7.0
sentence-transformers==2.2.2
langchain==0.1.0
langchain-community==0.0.10
numpy==1.24.3
pydantic==2.5.0
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
redis==5.0.1
EOF

# Install dependencies
cd rag-service
uv pip install -r requirements.txt
```

---

## 📊 Part 2: Hybrid Search Implementation (120 min)

### Step 2.1: Create Embedding Service

```python
# File: rag-service/app/embeddings.py
"""
Embedding service for document indexing
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import torch

class EmbeddingService:
    """Service for creating embeddings"""

    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

        # Move to GPU if available
        if torch.cuda.is_available():
            self.model = self.model.to('cuda')
            print(f"Embedding model running on GPU")
        else:
            print(f"Embedding model running on CPU")

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) to embeddings"""
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,  # L2 normalization
            show_progress_bar=len(texts) > 100,
        )
        return embeddings

    def encode_batch(self, texts: List[str], batch_size=32) -> np.ndarray:
        """Encode large batch of texts efficiently"""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.encode(batch)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings) if all_embeddings else np.array([])

# Test embedding service
if __name__ == "__main__":
    embed_service = EmbeddingService()

    # Test single text
    embedding = embed_service.encode("Hello, world!")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding norm: {np.linalg.norm(embedding):.4f}")

    # Test batch
    texts = ["Hello", "World", "How are you?"]
    embeddings = embed_service.encode(texts)
    print(f"Batch embeddings shape: {embeddings.shape}")
```

### Step 2.2: Implement Hybrid Search

```python
# File: rag-service/app/hybrid_search.py
"""
Hybrid search combining vector and keyword search
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional, Tuple
import numpy as np

class HybridSearch:
    """Hybrid search: Vector + Keyword + Re-ranking"""

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "documents",
        embedding_dim: int = 384,
    ):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

    def create_collection(self):
        """Create Qdrant collection for hybrid search"""
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_dim,
                distance=Distance.COSINE,
                hnsw_config={
                    "m": 16,  # Number of bi-directional links
                    "ef_construct": 100,  # Index build accuracy
                },
            ),
            # Payload indexing for keyword search
            payload_schema={
                "text": "text",
                "tenant_id": "keyword",
                "category": "keyword",
                "title": "text",
            },
        )

        print(f"Collection '{self.collection_name}' created successfully")

    def index_document(
        self,
        doc_id: str,
        text: str,
        embedding: np.ndarray,
        tenant_id: str,
        metadata: Dict,
    ):
        """Index a single document"""
        point = PointStruct(
            id=doc_id,
            vector=embedding.tolist(),
            payload={
                "text": text,
                "tenant_id": tenant_id,
                "title": metadata.get("title", ""),
                "category": metadata.get("category", "general"),
                **metadata,
            },
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    def search(
        self,
        query: str,
        query_embedding: np.ndarray,
        tenant_id: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Perform hybrid search

        Args:
            query: Query text
            query_embedding: Query embedding
            tenant_id: Filter by tenant (multi-tenancy)
            category: Filter by category
            top_k: Number of results

        Returns:
            List of search results with scores
        """
        # Build filter
        filter_conditions = None
        if tenant_id or category:
            conditions = []

            if tenant_id:
                conditions.append(
                    FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
                )

            if category:
                conditions.append(
                    FieldCondition(key="category", match=MatchValue(value=category))
                )

            if conditions:
                filter_conditions = Filter(must=conditions)

        # Vector search
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            query_filter=filter_conditions,
            limit=top_k * 2,  # Get more for re-ranking
            with_payload=True,  # scores always returned on each point
        ).points

        # Convert to list of dicts
        results = []
        for result in search_results:
            results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            })

        # Re-ranking would happen here
        # (See Part 3 for re-ranking implementation)

        return results[:top_k]

    def delete_tenant_data(self, tenant_id: str):
        """Delete all data for a tenant"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
            ),
        )
        print(f"Deleted all data for tenant: {tenant_id}")

# Test hybrid search
if __name__ == "__main__":
    from embeddings import EmbeddingService

    # Initialize services
    embed_service = EmbeddingService()
    hybrid_search = HybridSearch()

    # Create collection
    try:
        hybrid_search.create_collection()
    except Exception as e:
        print(f"Collection might exist: {e}")

    # Index some test documents
    test_docs = [
        {
            "id": "doc1",
            "text": "Machine learning is a subset of AI that focuses on algorithms.",
            "tenant_id": "tenant1",
            "metadata": {"title": "ML Intro", "category": "tech"},
        },
        {
            "id": "doc2",
            "text": "Deep learning uses neural networks with multiple layers.",
            "tenant_id": "tenant1",
            "metadata": {"title": "Deep Learning", "category": "tech"},
        },
    ]

    for doc in test_docs:
        embedding = embed_service.encode(doc["text"])
        hybrid_search.index_document(
            doc_id=doc["id"],
            text=doc["text"],
            embedding=embedding,
            tenant_id=doc["tenant_id"],
            metadata=doc["metadata"],
        )

    # Search
    query = "What is machine learning?"
    query_embedding = embed_service.encode(query)

    results = hybrid_search.search(
        query=query,
        query_embedding=query_embedding,
        tenant_id="tenant1",
        top_k=5,
    )

    print(f"\nQuery: {query}")
    print(f"Results: {len(results)}")
    for i, result in enumerate(results):
        print(f"  {i+1}. [{result['payload']['title']}] {result['payload']['text'][:60]}...")
```

### Step 2.3: Add Keyword Search

```python
# File: rag-service/app/keyword_search.py
"""
Simple BM25 keyword search
"""

from typing import List, Dict
import math
from collections import Counter
import re

class BM25Search:
    """BM25 keyword search"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.doc_freqs = Counter()
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.documents = {}
        self.total_docs = 0

    def tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Lowercase and extract words
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def index_documents(self, documents: List[Dict]):
        """
        Index documents for BM25

        Args:
            documents: List of {"id": str, "text": str, "tenant_id": str, ...}
        """
        self.total_docs = len(documents)

        for doc in documents:
            doc_id = doc["id"]
            tokens = self.tokenize(doc["text"])

            self.documents[doc_id] = {
                "text": doc["text"],
                "tokens": tokens,
                "tenant_id": doc.get("tenant_id"),
                "length": len(tokens),
            }

            self.doc_lengths.append(len(tokens))

            # Count document frequency for unique terms
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1

        # Calculate average document length
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)

        print(f"Indexed {self.total_docs} documents")
        print(f"Average document length: {self.avg_doc_length:.1f} tokens")
        print(f"Unique terms: {len(self.doc_freqs)}")

    def search(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Dict]:
        """Search using BM25"""
        query_tokens = self.tokenize(query)

        # Filter by tenant if specified
        candidate_docs = [
            (doc_id, doc)
            for doc_id, doc in self.documents.items()
            if tenant_id is None or doc.get("tenant_id") == tenant_id
        ]

        scores = {}

        for doc_id, doc in candidate_docs:
            doc_tokens = doc["tokens"]
            doc_length = doc["length"]

            score = 0
            for token in query_tokens:
                if token not in doc_tokens:
                    continue

                # Term frequency in document
                tf = doc_tokens.count(token)

                # IDF
                df = self.doc_freqs.get(token, 0)
                idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)

                # BM25 score
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
                score += idf * numerator / denominator

            scores[doc_id] = score

        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Return top-k
        results = []
        for doc_id, score in sorted_results[:top_k]:
            doc = self.documents[doc_id]
            results.append({
                "id": doc_id,
                "score": score,
                "text": doc["text"],
            })

        return results

# Test BM25
if __name__ == "__main__":
    # Create index
    bm25 = BM25Search()

    documents = [
        {"id": "doc1", "text": "Machine learning uses algorithms to learn from data.", "tenant_id": "tenant1"},
        {"id": "doc2", "text": "Deep learning is a type of machine learning with neural networks.", "tenant_id": "tenant1"},
        {"id": "doc3", "text": "Python is a programming language used in AI.", "tenant_id": "tenant1"},
    ]

    bm25.index_documents(documents)

    # Search
    query = "machine learning algorithms"
    results = bm25.search(query, top_k=3)

    print(f"\nQuery: {query}")
    for result in results:
        print(f"  [{result['score']:.2f}] {result['text'][:60]}...")
```

---

## 🔄 Part 3: Re-ranking Implementation (90 min)

### Step 3.1: Cross-Encoder Re-ranker

```python
# File: rag-service/app/reranker.py
"""
Re-ranking service using cross-encoder
"""

from sentence_transformers import CrossEncoder
from typing import List, Dict
import torch

class ReRanker:
    """Re-rank search results using cross-encoder"""

    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize cross-encoder model"""
        self.model = CrossEncoder(model_name)

        # Move to GPU if available
        if torch.cuda.is_available():
            self.model = self.model.to('cuda')
            print(f"Re-ranker running on GPU")
        else:
            print(f"Re-ranker running on CPU")

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Re-rank search results

        Args:
            query: Search query
            results: Initial search results
            top_k: Number of results to return

        Returns:
            Re-ranked results
        """
        if not results:
            return []

        # Prepare query-document pairs
        pairs = []
        for result in results:
            text = result.get("payload", {}).get("text", result.get("text", ""))
            pairs.append([query, text])

        # Score with cross-encoder
        scores = self.model.predict(pairs)

        # Add scores to results
        for i, result in enumerate(results):
            result["rerank_score"] = float(scores[i])

        # Sort by re-rank score
        reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)

        return reranked[:top_k]

    def rerank_batch(
        self,
        queries: List[str],
        results_list: List[List[Dict]],
        top_k: int = 10,
    ) -> List[List[Dict]]:
        """Re-rank multiple queries (batch processing)"""
        reranked_list = []

        for query, results in zip(queries, results_list):
            reranked = self.rerank(query, results, top_k)
            reranked_list.append(reranked)

        return reranked_list

# Test re-ranker
if __name__ == "__main__":
    # Initialize re-ranker
    reranker = ReRanker()

    # Sample results
    query = "What is machine learning?"

    initial_results = [
        {"payload": {"text": "Machine learning is a subset of AI."}, "score": 0.9},
        {"payload": {"text": "I like learning new things."}, "score": 0.7},
        {"payload": {"text": "Deep learning uses neural networks."}, "score": 0.85},
    ]

    # Re-rank
    reranked = reranker.rerank(query, initial_results)

    print(f"Query: {query}\n")
    print("Initial ranking:")
    for i, r in enumerate(initial_results):
        print(f"  {i+1}. [{r['score']:.2f}] {r['payload']['text']}")

    print("\nRe-ranked:")
    for i, r in enumerate(reranked):
        print(f"  {i+1}. [{r['rerank_score']:.2f}] {r['payload']['text']}")
```

### Step 3.2: Combined Hybrid Search with Re-ranking

```python
# File: rag-service/app/production_rag.py
"""
Complete production RAG with hybrid search and re-ranking
"""

from typing import List, Dict, Optional
import time

class ProductionRAG:
    """Complete RAG system with all components"""

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "documents",
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        # Initialize components
        from embeddings import EmbeddingService
        from hybrid_search import HybridSearch
        from keyword_search import BM25Search
        from reranker import ReRanker

        self.embed_service = EmbeddingService()
        self.vector_search = HybridSearch(qdrant_url, collection_name)
        self.keyword_search = BM25Search()
        self.reranker = ReRanker(reranker_model)

    def index_documents(self, documents: List[Dict]):
        """Index documents for both vector and keyword search"""
        # Index in vector database
        for doc in documents:
            embedding = self.embed_service.encode(doc["text"])
            self.vector_search.index_document(
                doc_id=doc["id"],
                text=doc["text"],
                embedding=embedding,
                tenant_id=doc.get("tenant_id"),
                metadata=doc,
            )

        # Index for keyword search
        self.keyword_search.index_documents(documents)

    def search(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        category: Optional[str] = None,
        alpha: float = 0.5,  # Weight for vector search (0=keyword only, 1=vector only)
        top_k: int = 10,
        use_rerank: bool = True,
    ) -> Dict:
        """
        Complete search pipeline

        Args:
            query: Search query
            tenant_id: Filter by tenant
            category: Filter by category
            alpha: Hybrid weight (0-1)
            top_k: Number of results
            use_rerank: Whether to use re-ranking

        Returns:
            Dictionary with results and metrics
        """
        start_time = time.time()

        # Get query embedding
        query_embedding = self.embed_service.encode(query)

        # Vector search
        vector_results = self.vector_search.search(
            query=query,
            query_embedding=query_embedding,
            tenant_id=tenant_id,
            category=category,
            top_k=top_k * 2,
        )

        # Keyword search
        keyword_results = self.keyword_search.search(
            query=query,
            tenant_id=tenant_id,
            top_k=top_k * 2,
        )

        # Reciprocal rank fusion
        fused_results = self._reciprocal_rank_fusion(
            vector_results,
            keyword_results,
            alpha=alpha,
        )

        # Re-rank
        if use_rerank:
            final_results = self.reranker.rerank(query, fused_results, top_k)
        else:
            final_results = fused_results[:top_k]

        # Calculate metrics
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        return {
            "results": final_results,
            "metrics": {
                "latency_ms": latency_ms,
                "vector_count": len(vector_results),
                "keyword_count": len(keyword_results),
                "final_count": len(final_results),
                "used_rerank": use_rerank,
                "alpha": alpha,
            },
        }

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        alpha: float = 0.5,
        k: int = 60,
    ) -> List[Dict]:
        """Combine vector and keyword results using RRF"""
        scores = {}

        # Vector scores (weighted by alpha)
        for rank, result in enumerate(vector_results):
            doc_id = result["id"]
            score = alpha / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + score

        # Keyword scores (weighted by 1-alpha)
        for rank, result in enumerate(keyword_results):
            doc_id = result["id"]
            score = (1 - alpha) / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + score

        # Sort by fused score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Create result list
        fused_results = []
        seen_ids = set()

        for doc_id, score in sorted_results:
            if doc_id in seen_ids:
                continue

            # Find original result
            original = next(
                (r for r in vector_results if r["id"] == doc_id),
                next((r for r in keyword_results if r["id"] == doc_id), None)
            )

            if original:
                result = original.copy()
                result["fusion_score"] = score
                fused_results.append(result)
                seen_ids.add(doc_id)

        return fused_results

# Test production RAG
if __name__ == "__main__":
    # Initialize
    rag = ProductionRAG()

    # Create collection if needed
    try:
        rag.vector_search.create_collection()
    except:
        pass

    # Index documents
    documents = [
        {
            "id": "doc1",
            "text": "Machine learning algorithms learn patterns from data to make predictions.",
            "tenant_id": "tenant1",
            "title": "ML Basics",
            "category": "tech",
        },
        {
            "id": "doc2",
            "text": "Neural networks are a type of machine learning inspired by the human brain.",
            "tenant_id": "tenant1",
            "title": "Neural Networks",
            "category": "tech",
        },
        {
            "id": "doc3",
            "text": "Python is widely used for machine learning and data science.",
            "tenant_id": "tenant1",
            "title": "Python in ML",
            "category": "tech",
        },
    ]

    rag.index_documents(documents)

    # Search
    query = "machine learning algorithms"
    result = rag.search(query, alpha=0.5, use_rerank=True)

    print(f"\nQuery: {query}")
    print(f"Latency: {result['metrics']['latency_ms']:.1f}ms")
    print(f"\nResults:")

    for i, r in enumerate(result["results"]):
        text = r.get("payload", {}).get("text", "")
        print(f"  {i+1}. {text[:80]}...")
```

---

## 🌐 Part 4: FastAPI Service (60 min)

### Step 4.1: Create API Service

```python
# File: rag-service/app/main.py
"""
FastAPI service for production RAG
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST

from production_rag import ProductionRAG

# Initialize FastAPI
app = FastAPI(
    title="Production RAG API",
    description="Enterprise-grade RAG with hybrid search and re-ranking",
    version="1.0.0",
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
rag = ProductionRAG()

# Prometheus metrics
search_counter = Counter('rag_search_total', 'Total searches', ['tenant_id', 'status'])
search_duration = Histogram('rag_search_duration_seconds', 'Search duration')

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = None
    category: Optional[str] = None
    alpha: float = Query(default=0.5, ge=0, le=1)
    top_k: int = Query(default=10, ge=1, le=100)
    use_rerank: bool = True

class Document(BaseModel):
    id: str
    text: str
    tenant_id: str
    title: Optional[str] = None
    category: Optional[str] = None

class IndexResponse(BaseModel):
    success: bool
    message: str
    indexed: int

class SearchResult(BaseModel):
    id: str
    score: float
    text: str
    title: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    metrics: dict

# Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {"status": "healthy", "service": "Production RAG API"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/index", response_model=IndexResponse)
async def index_documents(documents: List[Document]):
    """Index documents for search"""
    try:
        docs = [doc.dict() for doc in documents]
        rag.index_documents(docs)

        return IndexResponse(
            success=True,
            message=f"Successfully indexed {len(docs)} documents",
            indexed=len(docs),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search documents"""
    start_time = time.time()

    try:
        # Perform search
        result = rag.search(
            query=request.query,
            tenant_id=request.tenant_id,
            category=request.category,
            alpha=request.alpha,
            top_k=request.top_k,
            use_rerank=request.use_rerank,
        )

        # Format results
        formatted_results = []
        for r in result["results"]:
            text = r.get("payload", {}).get("text", r.get("text", ""))
            title = r.get("payload", {}).get("title", "")
            score = r.get("rerank_score", r.get("score", 0))

            formatted_results.append(SearchResult(
                id=r["id"],
                score=score,
                text=text,
                title=title,
            ))

        # Record metrics
        duration = time.time() - start_time
        search_duration.observe(duration)
        search_counter.labels(
            tenant_id=request.tenant_id or "default",
            status="success"
        ).inc()

        return SearchResponse(
            results=formatted_results,
            metrics=result["metrics"],
        )

    except Exception as e:
        search_counter.labels(
            tenant_id=request.tenant_id or "default",
            status="error"
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/tenant/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """Delete all data for a tenant"""
    try:
        rag.vector_search.delete_tenant_data(tenant_id)
        return {"success": True, "message": f"Deleted data for tenant: {tenant_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 4.2: Docker Deployment

```dockerfile
# File: rag-service/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# File: rag-service/docker-compose.yml

services:
  rag-api:
    build: .
    container_name: rag-api
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant-node1:6333
      - RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
    depends_on:
      - qdrant-node1
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  # Nginx load balancer
  nginx:
    image: nginx:latest
    container_name: rag-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - rag-api
    restart: unless-stopped
```

---

## ✅ Completion Checklist

Use this checklist to track your progress:

### Infrastructure
- [ ] Qdrant cluster deployed (3 nodes)
- [ ] Prometheus and Grafana running
- [ ] RAG service containers deployed

### Search Implementation
- [ ] Embedding service working
- [ ] Vector search functional
- [ ] Keyword search (BM25) working
- [ ] Hybrid search implemented

### Re-ranking
- [ ] Cross-encoder re-ranker working
- [ ] Re-ranking improves results

### API Service
- [ ] FastAPI endpoints working
- [ ] Multi-tenancy implemented
- [ ] Metrics collection working
- [ ] Load balancing configured

### Testing
- [ ] Indexed test documents
- [ ] Search returns relevant results
- [ ] Metrics show good performance
- [ ] Load tested

---

## 📊 Expected Results

### Performance Metrics

```text
Search Latency: <200ms (P95)
Throughput: >100 queries/second per instance
Accuracy (P@10): >90% for relevant queries
Re-ranking improvement: +15-20% accuracy
```

### Monitoring Dashboard

Grafana dashboards should show:
- **Search latency:** P50, P95, P99
- **Throughput:** Queries per second
- **Error rate:** <1%
- **Resource usage:** CPU, memory, GPU

---

## 🚀 Next Steps

After completing this lab:

1. **LAB-008: Agent Fleet** - Build multi-agent systems
2. **LAB-009: Production Deployment** - Deploy to production
3. **6302-CAG-Long-Context-Architectures.md** - Advanced RAG techniques

---

**Lab Status:** ✅ Complete
**Maintainer:** PROJECT-OMEGA Team
