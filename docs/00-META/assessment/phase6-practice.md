---
Document ID: PHASE6-PRACTICE
Title: "Phase 6: Data Nexus - Practice Exercises"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Tags: ['assessment', 'practice', 'rag']
---

# Phase 6: Data Nexus - Practice Exercises

## Overview

This document provides hands-on practice exercises for Phase 6: Data Nexus (RAG & Vector Systems). These exercises reinforce the concepts learned in modules 6100-6500.

**Prerequisites:**
- Completed Phase 1-5 modules
- Basic understanding of vectors and embeddings
- Familiarity with Python and Docker
- Neo4j and Qdrant installed

---

## Exercise 1: Vector Similarity from Scratch

**Difficulty:** ⭐⭐⭐ Advanced
**Time:** 30 minutes
**Module:** 6100 - Vector Architectures

### Task

Implement cosine similarity calculation from scratch without using libraries like scikit-learn or sentence-transformers.

### Requirements

1. Create a function `cosine_similarity(vec1, vec2)` that:
   - Takes two numpy arrays as input
   - Returns cosine similarity score (-1 to 1)
   - Handles edge cases (zero vectors, dimension mismatch)

2. Test with:
   ```python
   vec1 = np.array([1, 2, 3, 4, 5])
   vec2 = np.array([2, 4, 6, 8, 10])  # Should be 1.0 (identical direction)
   vec3 = np.array([-1, -2, -3, -4, -5])  # Should be -1.0 (opposite)
   ```

3. Compare performance against numpy's built-in implementation

### Solution Template

```python
import numpy as np
import time

def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector (numpy array)
        vec2: Second vector (numpy array)

    Returns:
        float: Cosine similarity score (-1 to 1)
    """
    # TODO: Implement
    pass

# Test cases
def test_cosine_similarity():
    vec1 = np.array([1, 2, 3, 4, 5], dtype=float)
    vec2 = np.array([2, 4, 6, 8, 10], dtype=float)
    vec3 = np.array([-1, -2, -3, -4, -5], dtype=float)

    print(f"Similarity (vec1, vec2): {cosine_similarity(vec1, vec2):.4f}")
    print(f"Similarity (vec1, vec3): {cosine_similarity(vec1, vec3):.4f}")

if __name__ == "__main__":
    pass  # implement cosine_similarity above first, then call test_cosine_similarity() here
```

### Success Criteria

- [ ] Function returns correct values for test cases
- [ ] Handles zero-vector case gracefully
- [ ] Raises appropriate error for dimension mismatch
- [ ] Performance within 2x of numpy implementation

---

## Exercise 2: BM25 Search Implementation

**Difficulty:** Intermediate
**Time:** 45 minutes
**Module:** 6200 - Retrieval

### Task

Implement BM25 (Best Matching 25) ranking algorithm for keyword search.

### Requirements

1. Create a `BM25Retriever` class with:
   - `index(documents)`: Build index from document list
   - `search(query, k=10)`: Return top-k relevant documents
   - Configurable parameters (k1, b)

2. Use the following BM25 formula:
   ```text
   score(D,Q) = Σ IDF(qi) × (f(qi,D) × (k1 + 1)) /
                         (f(qi,D) + k1 × (1 - b + b × |D| / avgdl))
   ```

3. Test with sample documents and queries

### Solution Template

```python
import math
from collections import Counter

class BM25Retriever:
    def __init__(self, k1=1.5, b=0.75):
        """
        Initialize BM25 retriever.

        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b

    def index(self, documents: list[str]):
        """
        Build BM25 index from documents.

        Args:
            documents: The document strings
        """
        # TODO: Implement
        # 1. Tokenize documents
        # 2. Calculate document frequencies
        # 3. Calculate average document length
        pass

    def search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        """
        Search for relevant documents.

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of (doc_id, score) tuples
        """
        # TODO: Implement
        pass
```

### Success Criteria

- [ ] Correct BM25 scoring implementation
- [ ] Handles out-of-vocabulary terms
- [ ] Returns ranked results by score
- [ ] Configurable parameters work correctly

---

## Exercise 3: Hybrid Search with Rank Fusion

**Difficulty:** Intermediate
**Time:** 60 minutes
**Module:** 6200 - Retrieval

### Task

Implement a hybrid search system combining vector and keyword search using Reciprocal Rank Fusion (RRF).

### Requirements

1. Create `HybridRetriever` class with:
   - Vector search backend (using embeddings)
   - BM25 keyword search backend
   - RRF fusion algorithm

2. RRF formula:
   ```text
   fused_score(d) = Σ 1 / (k + rank_i(d))
   ```
   Where k=60 (default) and rank_i is rank in result list i

3. Implement tunable alpha parameter for result blending

### Solution Template

```python
import numpy as np

class HybridRetriever:
    def __init__(self, documents: list[str], embedding_model):
        """
        Initialize hybrid retriever.

        Args:
            documents: The document strings
            embedding_model: Embedding model for vector search
        """
        self.documents = documents
        self.embedding_model = embedding_model

        # TODO: Initialize vector and BM25 retrievers
        self.vector_retriever = None
        self.bm25_retriever = None

    def search(
        self,
        query: str,
        alpha: float = 0.5,
        k: int = 60,
        top_k: int = 10
    ) -> list[tuple[int, float]]:
        """
        Hybrid search with RRF fusion.

        Args:
            query: Search query
            alpha: Weight for interpolation (0-1)
            k: RRF constant
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples
        """
        # TODO: Implement
        # 1. Get vector search results
        # 2. Get BM25 search results
        # 3. Apply RRF fusion
        pass
```

### Success Criteria

- [ ] Vector search returns relevant results
- [ ] BM25 search returns keyword matches
- [ ] RRF fusion properly combines results
- [ ] Alpha parameter allows tuning between methods

---

## Exercise 4: Qdrant Operations

**Difficulty:** Beginner
**Time:** 30 minutes
**Module:** 6400 - Vector Databases

### Task

Set up Qdrant vector database and perform basic operations.

### Requirements

1. Start Qdrant instance (Docker):
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. Create a collection with:
   - Vector size: 1536 (OpenAI embeddings)
   - Distance: Cosine
   - HNSW index with custom parameters

3. Insert sample documents with:
   - Text payloads
   - Metadata (category, date, source)

4. Perform filtered search

### Solution Template

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

# Initialize client
client = QdrantClient(url="http://localhost:6333")

# TODO: Create collection
def create_collection(collection_name):
    pass

# TODO: Insert documents
def insert_documents(collection_name, docs):
    pass

# TODO: Search with filter
def search_with_filter(collection_name, query_vector, category=None):
    pass

# Test
sample_docs = [
    {"text": "AI transforms healthcare", "category": "healthcare", "date": "2024-01-01"},
    {"text": "Financial fraud detection", "category": "finance", "date": "2024-01-02"},
]
```

### Success Criteria

- [ ] Collection created with correct configuration
- [ ] Documents inserted successfully
- [ ] Search returns relevant results
- [ ] Filter search works correctly

---

## Exercise 5: Neo4j Knowledge Graph

**Difficulty:** Intermediate
**Time:** 45 minutes
**Module:** 6300 - Context Management

### Task

Build a knowledge graph in Neo4j and query relationships.

### Requirements

1. Start Neo4j instance (Docker):
   ```bash
   docker run -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:latest
   ```

2. Create nodes and relationships:
   - Entity nodes (Person, Organization, Concept)
   - RELATES_TO relationships
   - Properties (name, type, confidence)

3. Implement graph traversal queries

### Solution Template

```python
from neo4j import GraphDatabase

class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def create_entity(self, name, entity_type):
        """Create an entity node."""
        with self.driver.session() as session:
            result = session.run(
                "MERGE (e:Entity {name: $name, type: $type})",
                name=name, type=entity_type
            )
            return result

    def create_relationship(self, entity1, entity2, rel_type):
        """Create relationship between entities."""
        # TODO: Implement
        pass

    def find_related(self, entity_name, depth=2):
        """Find related entities within specified depth."""
        # TODO: Implement
        pass

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()
```

### Success Criteria

- [ ] Entities created successfully
- [ ] Relationships formed correctly
- [ ] Graph traversal returns connected entities
- [ ] Cypher queries work as expected

---

## Exercise 6: Context Building for RAG

**Difficulty:** Advanced
**Time:** 60 minutes
**Module:** 6300 - Context Management

### Task

Implement context building strategies for RAG applications.

### Requirements

1. Create a `ContextBuilder` class with strategies:
   - **Stuff**: Concatenate all context
   - **Map-Reduce**: Summarize then combine
   - **Refine**: Iteratively build context

2. Handle token limits and context window management

3. Implement relevance scoring for context chunks

### Solution Template

```python
import tiktoken

class ContextBuilder:
    def __init__(self, max_tokens=4000, model="gpt-4o-mini"):
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))

    def stuff_context(self, chunks: list[str], query: str) -> str:
        """
        Stuff all chunks into context.

        Args:
            chunks: The text chunks
            query: User query

        Returns:
            Formatted context string
        """
        # TODO: Implement with token limit
        pass

    def map_reduce_context(self, chunks: list[str], query: str) -> str:
        """
        Map-reduce strategy for large context.

        Args:
            chunks: The text chunks
            query: User query

        Returns:
            Summarized context string
        """
        # TODO: Implement
        # 1. Summarize each chunk
        # 2. Combine summaries
        pass

    def refine_context(self, chunks: list[str], query: str) -> str:
        """
        Iteratively refine context.

        Args:
            chunks: The text chunks
            query: User query

        Returns:
            Refined context string
        """
        # TODO: Implement
        # 1. Start with first chunk
        # 2. Iteratively add relevant chunks
        pass
```

### Success Criteria

- [ ] Stuff strategy handles token limits
- [ ] Map-reduce creates coherent summaries
- [ ] Refine strategy maintains context flow
- [ ] All strategies respect max token limit

---

## Exercise 7: Complete RAG Pipeline

**Difficulty:** Advanced
**Time:** 90 minutes
**Module:** 6100-6500 (Comprehensive)

### Task

Build an end-to-end RAG pipeline with all components.

### Requirements

1. Create a `RAGPipeline` class with:
   - Document ingestion and chunking
   - Vector indexing (Qdrant)
   - Hybrid search (vector + BM25)
   - Re-ranking
   - Context building
   - LLM generation

2. Implement evaluation metrics

### Architecture

```python
from qdrant_client import QdrantClient
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Any

class RAGPipeline:
    def __init__(self, config: dict[str, Any]):
        """
        Initialize RAG pipeline.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        # TODO: Initialize components
        self.qdrant_client = None
        self.embedding_model = None
        self.bm25_retriever = None
        self.reranker = None
        self.llm = None

    def ingest_documents(self, documents: list[str], metadata: list[dict]):
        """Ingest documents into the pipeline."""
        # TODO: Implement
        # 1. Chunk documents
        # 2. Generate embeddings
        # 3. Index in Qdrant
        # 4. Build BM25 index
        pass

    def retrieve(self, query: str, top_k: int = 20) -> list[dict]:
        """Retrieve relevant documents."""
        # TODO: Implement hybrid retrieval
        pass

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        """Re-rank retrieved documents."""
        # TODO: Implement re-ranking
        pass

    def generate(self, query: str, context: list[dict]) -> str:
        """Generate response using LLM."""
        # TODO: Implement generation
        pass

    def query(self, question: str) -> dict[str, Any]:
        """
        End-to-end query processing.

        Args:
            question: User question

        Returns:
            Dictionary with answer, sources, metadata
        """
        # TODO: Implement full pipeline
        pass
```

### Success Criteria

- [ ] Documents indexed correctly
- [ ] Retrieval returns relevant results
- [ ] Re-ranking improves result quality
- [ ] LLM generates coherent responses
- [ ] Pipeline handles edge cases gracefully

---

## Bonus Challenges

### Challenge 1: GraphRAG Implementation

Build a complete GraphRAG system combining:
- Entity extraction
- Knowledge graph construction
- Graph-augmented retrieval
- Community detection

### Challenge 2: Multi-Query RAG

Implement multi-query retrieval:
- Query decomposition
- Parallel retrieval
- Result fusion
- Answer synthesis

### Challenge 3: Adaptive Retrieval

Create adaptive retrieval system that:
- Analyzes query complexity
- Selects optimal retrieval strategy
- Adjusts context size dynamically
- Monitors performance metrics

---

## Evaluation

### Grading Criteria

| Exercise | Points | Criteria |
|----------|--------|----------|
| Ex 1: Vector Similarity | 10 | Correct implementation |
| Ex 2: BM25 | 15 | Algorithm accuracy |
| Ex 3: Hybrid Search | 20 | RRF fusion |
| Ex 4: Qdrant | 10 | Database operations |
| Ex 5: Neo4j | 15 | Graph queries |
| Ex 6: Context Building | 15 | Strategy implementation |
| Ex 7: RAG Pipeline | 25 | End-to-end functionality |
| **Total** | **110** | |

### Submission

1. Create a GitHub repository with your solutions
2. Include README with setup instructions
3. Add test cases demonstrating functionality
4. Document design decisions

---

## Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Sentence Transformers](https://www.sbert.net/)
- [LangChain RAG Tutorial](https://docs.langchain.com/oss/python/deepagents/rag)

---

**Last Updated:** 2026-09-30
**Phase:** 6 - Data Nexus
**Status:** Ready for Practice

---

## Appendix: Phase 6 - Complete Reference Implementations

The exercises above use solution templates. This appendix contains
complete, working reference implementations of Exercises 1-6 for
self-checking after you have attempted them on your own. Exercise 7
composes these building blocks into a full pipeline, so no separate
reference implementation is provided for it.


### Exercise 1: Implement Vector Search from Scratch

```python
import numpy as np


class VectorSearch:
    """Simple vector search implementation"""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.vectors = []
        self.metadata = []

    def add(self, vector: np.ndarray, meta: dict):
        """Add vector to index"""
        if vector.shape[0] != self.dim:
            raise ValueError(f"Expected dim {self.dim}, got {vector.shape[0]}")
        self.vectors.append(vector)
        self.metadata.append(meta)

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def search(self, query: np.ndarray, k: int = 5) -> list[tuple[dict, float]]:
        """Search for similar vectors"""
        if not self.vectors:
            return []

        # Calculate similarities
        similarities = []
        for i, vector in enumerate(self.vectors):
            sim = self.cosine_similarity(query, vector)
            similarities.append((self.metadata[i], sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:k]


def test_vector_search():
    print("=== Vector Search Test ===")

    # Create index
    index = VectorSearch(dim=384)

    # Add sample vectors
    for i in range(100):
        vector = np.random.randn(384)
        vector = vector / np.linalg.norm(vector)  # Normalize
        index.add(vector, {"id": i, "text": f"Document {i}"})

    print(f"Indexed {len(index.vectors)} vectors")

    # Search
    query = np.random.randn(384)
    query = query / np.linalg.norm(query)

    results = index.search(query, k=5)

    print(f"Top 5 results:")
    for meta, score in results:
        print(f"  {meta['text']}: {score:.4f}")

    print("✅ Vector search working!\n")


if __name__ == "__main__":
    test_vector_search()
```

### Exercise 2: Implement BM25 Search

```python
from collections import defaultdict
import math


class BM25:
    """BM25 keyword search implementation"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = []
        self.idf = {}
        self.doc_lens = []

    def index(self, documents: list[str]):
        """Index documents"""
        # Tokenize and count
        self.doc_freqs = []
        self.doc_lens = []

        # Build document frequencies
        for doc in documents:
            tokens = doc.lower().split()
            self.doc_lens.append(len(tokens))

            freq = defaultdict(int)
            for token in tokens:
                freq[token] += 1

            self.doc_freqs.append(dict(freq))

        # Calculate IDF
        N = len(documents)
        all_tokens = set()
        for freq in self.doc_freqs:
            all_tokens.update(freq.keys())

        for token in all_tokens:
            df = sum(1 for freq in self.doc_freqs if token in freq)
            self.idf[token] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_idx: int) -> float:
        """Calculate BM25 score for query-document pair"""
        query_tokens = query.lower().split()
        doc_freqs = self.doc_freqs[doc_idx]
        doc_len = self.doc_lens[doc_idx]
        avg_doc_len = sum(self.doc_lens) / len(self.doc_lens)

        score = 0
        for token in query_tokens:
            if token in doc_freqs:
                tf = doc_freqs[token]
                idf = self.idf.get(token, 0)

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len)

                score += idf * (numerator / denominator)

        return score

    def search(self, query: str, k: int = 5) -> list[tuple]:
        """Search for relevant documents"""
        scores = [(i, self.score(query, i)) for i in range(len(self.doc_freqs))]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


def test_bm25():
    print("=== BM25 Search Test ===")

    # Sample documents
    documents = [
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses neural networks with multiple layers",
        "Natural language processing deals with text and speech",
        "Computer vision enables machines to understand images",
        "Reinforcement learning learns through trial and error"
    ]

    # Index documents
    bm25 = BM25(k1=1.5, b=0.75)
    bm25.index(documents)

    print(f"Indexed {len(documents)} documents")

    # Search
    query = "neural networks"
    results = bm25.search(query, k=3)

    print(f"\nQuery: '{query}'")
    print(f"Top 3 results:")
    for doc_idx, score in results:
        print(f"  [{doc_idx}] {documents[doc_idx]}: {score:.4f}")

    print("✅ BM25 working!\n")


if __name__ == "__main__":
    test_bm25()
```

### Exercise 3: Hybrid Search with Rank Fusion

```python
from collections import defaultdict

class HybridSearch:
    """Hybrid search combining vector and keyword search"""

    def __init__(self, alpha: float = 0.5):
        """
        Args:
            alpha: Weight for vector search (0-1)
                   1-alpha is weight for keyword search
        """
        self.alpha = alpha

    def reciprocal_rank_fusion(
        self,
        results_list: list[list[tuple[int, float]]],
        k: int = 60
    ) -> list[tuple[int, float]]:
        """
        Reciprocal Rank Fusion (RRF) algorithm

        Combines multiple ranked lists by:
        score(d) = sum(1 / (k + rank(d)))

        Args:
            results_list: The ranked result lists
            k: Constant to prevent division by small ranks

        Returns:
            Fused ranked list
        """
        fused_scores = defaultdict(float)

        for results in results_list:
            for rank, (doc_id, _) in enumerate(results):
                fused_scores[doc_id] += 1.0 / (k + rank + 1)

        # Sort by fused score
        sorted_results = sorted(
            fused_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results

    def weighted_score_fusion(
        self,
        vector_results: list[tuple[int, float]],
        keyword_results: list[tuple[int, float]]
    ) -> list[tuple[int, float]]:
        """
        Weighted score fusion

        Combines scores using weighted average:
        score(d) = alpha * vector_score + (1-alpha) * keyword_score

        Args:
            vector_results: (doc_id, score) pairs from vector search
            keyword_results: (doc_id, score) pairs from keyword search

        Returns:
            Fused ranked list
        """
        # Normalize scores to 0-1
        def normalize(scores):
            if not scores:
                return []
            max_score = max(s for _, s in scores)
            min_score = min(s for _, s in scores)
            range_val = max_score - min_score if max_score != min_score else 1
            return [(doc_id, (score - min_score) / range_val)
                    for doc_id, score in scores]

        vector_norm = normalize(vector_results)
        keyword_norm = normalize(keyword_results)

        # Combine scores
        combined_scores = defaultdict(float)

        for doc_id, score in vector_norm:
            combined_scores[doc_id] += self.alpha * score

        for doc_id, score in keyword_norm:
            combined_scores[doc_id] += (1 - self.alpha) * score

        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results


def test_hybrid_search():
    print("=== Hybrid Search Test ===")

    # Sample results from vector and keyword search
    vector_results = [
        (1, 0.95), (3, 0.88), (5, 0.82), (2, 0.75), (8, 0.70)
    ]

    keyword_results = [
        (5, 0.92), (1, 0.85), (7, 0.78), (3, 0.72), (9, 0.68)
    ]

    print(f"Vector search results: {[r[0] for r in vector_results]}")
    print(f"Keyword search results: {[r[0] for r in keyword_results]}")

    # Test weighted score fusion
    hybrid = HybridSearch(alpha=0.5)

    fused = hybrid.weighted_score_fusion(vector_results, keyword_results)

    print(f"\nFused results (α=0.5):")
    for doc_id, score in fused[:5]:
        print(f"  Doc {doc_id}: {score:.4f}")

    # Test different alpha values
    print(f"\nAlpha comparison:")
    for alpha in [0.2, 0.5, 0.8]:
        h = HybridSearch(alpha=alpha)
        fused = h.weighted_score_fusion(vector_results, keyword_results)
        top_docs = [str(doc_id) for doc_id, _ in fused[:3]]
        print(f"  α={alpha}: Top 3 = [{', '.join(top_docs)}]")

    print("✅ Hybrid search working!\n")


if __name__ == "__main__":
    test_hybrid_search()
```

### Exercise 4: Qdrant Vector Database Operations

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

class QdrantVectorStore:
    """Qdrant vector database operations"""

    def __init__(self, location=":memory:", collection_name="documents"):
        self.client = QdrantClient(location=location)
        self.collection_name = collection_name

    def create_collection(self, vector_size=384):
        """Create a new collection"""
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        print(f"Created collection: {self.collection_name}")

    def insert_points(self, points_data):
        """Insert points into collection"""
        points = [
            PointStruct(
                id=i,
                vector=data["vector"].tolist(),
                payload=data.get("payload", {})
            )
            for i, data in enumerate(points_data)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Inserted {len(points)} points")

    def search(self, query_vector, limit=5, score_threshold=None):
        """Search for similar vectors"""
        # qdrant-client >= 1.10 removed .search(query_vector=...);
        # query_points() takes the vector as `query=` and its response
        # carries the hits in .points (same ScoredPoint shape).
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist(),
            limit=limit,
            score_threshold=score_threshold
        ).points
        return results

    def filter_search(self, query_vector, filter_condition, limit=5):
        """Search with metadata filtering"""
        # query_points() also replaces filtered .search() calls.
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist(),
            query_filter=filter_condition,
            limit=limit
        ).points
        return results

    def delete_collection(self):
        """Delete the collection"""
        self.client.delete_collection(self.collection_name)
        print(f"Deleted collection: {self.collection_name}")


def test_qdrant():
    print("=== Qdrant Vector Store Test ===")

    # Create store
    store = QdrantVectorStore(location=":memory:", collection_name="test_docs")

    # Create collection
    store.create_collection(vector_size=384)

    # Insert sample data
    points_data = []
    documents = [
        "AI and machine learning are transforming technology",
        "Deep learning neural networks process complex patterns",
        "Natural language understanding is improving rapidly",
        "Computer vision recognizes objects in images",
        "Reinforcement learning optimizes decision making"
    ]

    for i, doc in enumerate(documents):
        # Simulate embedding with random vector
        vector = np.random.randn(384)
        vector = vector / np.linalg.norm(vector)

        points_data.append({
            "vector": vector,
            "payload": {"text": doc, "category": "AI" if i < 3 else "ML"}
        })

    store.insert_points(points_data)

    # Search
    query = np.random.randn(384)
    query = query / np.linalg.norm(query)

    results = store.search(query, limit=3)

    print(f"\nSearch results:")
    for result in results:
        print(f"  Score: {result.score:.4f}")
        print(f"  Text: {result.payload.get('text', 'N/A')}")
        print(f"  Category: {result.payload.get('category', 'N/A')}")

    # Clean up
    store.delete_collection()

    print("✅ Qdrant operations working!\n")


if __name__ == "__main__":
    test_qdrant()
```

### Exercise 5: Neo4j Knowledge Graph

```python
from neo4j import GraphDatabase

class KnowledgeGraph:
    """Neo4j knowledge graph operations"""

    # $parameters cannot fill label/rel-type positions - guard schema
    # names against an allowlist before they reach the query engine
    ALLOWED_LABELS = {"Person", "Company", "Document", "Chunk"}
    ALLOWED_REL_TYPES = {"WORKS_AT", "KNOWS", "RELATED_TO", "MENTIONS"}

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_entity(self, label, name, properties=None):
        """Create an entity node"""
        if label not in self.ALLOWED_LABELS:
            raise ValueError(f"unknown label: {label}")
        with self.driver.session() as session:
            result = session.run(
                f"CREATE (n:{label} {{name: $name}}) RETURN n",
                name=name
            )
            return result.single()[0]

    def create_relationship(self, entity1, rel_type, entity2, properties=None):
        """Create a relationship between entities"""
        if rel_type not in self.ALLOWED_REL_TYPES:
            raise ValueError(f"unknown relationship type: {rel_type}")
        with self.driver.session() as session:
            query = f"""
            MATCH (a {{name: $entity1}})
            MATCH (b {{name: $entity2}})
            CREATE (a)-[r:{rel_type}]->(b)
            RETURN r
            """
            result = session.run(query, entity1=entity1, entity2=entity2)
            return result.single()

    def find_connections(self, entity_name, max_depth=2):
        """Find all connections within depth"""
        # $parameters cannot fill Cypher path bounds - int-cast the bound first
        max_depth = max(1, int(max_depth))
        with self.driver.session() as session:
            query = f"""
            MATCH (start {{name: $name}})-[*1..{max_depth}]-(connected)
            RETURN DISTINCT connected.name AS name, labels(connected) AS labels
            LIMIT 20
            """
            result = session.run(query, name=entity_name)
            return [(record["name"], record["labels"]) for record in result]

    def find_shortest_path(self, entity1, entity2):
        """Find shortest path between entities"""
        with self.driver.session() as session:
            query = """
            MATCH path = shortestPath(
                (a {name: $entity1})-[*]-(b {name: $entity2})
            )
            RETURN [node in nodes(path) | node.name] AS path
            """
            result = session.run(query, entity1=entity1, entity2=entity2)
            record = result.single()
            return record["path"] if record else None


def test_neo4j():
    print("=== Neo4j Knowledge Graph Test ===")

    # Note: This requires a running Neo4j instance
    print("This exercise requires a running Neo4j instance.")
    print("\nTo test:")

    example_code = """
    # Connect to Neo4j
    kg = KnowledgeGraph(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="your_password"
    )

    # Create entities
    kg.create_entity("Person", "Alice")
    kg.create_entity("Person", "Bob")
    kg.create_entity("Company", "TechCorp")

    # Create relationships
    kg.create_relationship("Alice", "WORKS_AT", "TechCorp")
    kg.create_relationship("Bob", "KNOWS", "Alice")

    # Find connections
    connections = kg.find_connections("Alice", max_depth=2)
    print(f"Alice's connections: {connections}")

    # Find shortest path
    path = kg.find_shortest_path("Bob", "TechCorp")
    print(f"Path from Bob to TechCorp: {path}")

    kg.close()
    """

    print(example_code)

    print("\nExpected output:")
    print("  Alice's connections: [('Bob', ['Person']), ('TechCorp', ['Company'])]")
    print("  Path from Bob to TechCorp: ['Bob', 'Alice', 'TechCorp']")

    print("✅ Neo4j concepts demonstrated!\n")


if __name__ == "__main__":
    test_neo4j()
```

### Exercise 6: Context Building for RAG

```python

class ContextBuilder:
    """Build context for RAG from retrieved documents"""

    def __init__(self, max_context_length: int = 2000):
        self.max_context_length = max_context_length

    def build_context(
        self,
        retrieved_docs: list[dict],
        query: str,
        include_sources: bool = True
    ) -> str:
        """
        Build context string from retrieved documents

        Args:
            retrieved_docs: The retrieved documents with text and metadata
            query: Original user query
            include_sources: Whether to include source citations

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add query context
        context_parts.append(f"Query: {query}\n")

        # Add retrieved documents
        for i, doc in enumerate(retrieved_docs, 1):
            text = doc.get("text", "")
            source = doc.get("source", "Unknown")

            if include_sources:
                context_parts.append(f"[Source {i}: {source}]")
                context_parts.append(f"{text}\n")
            else:
                context_parts.append(f"{text}\n")

        # Combine and truncate if needed
        full_context = "\n".join(context_parts)

        if len(full_context) > self.max_context_length:
            # Truncate from the end
            full_context = full_context[:self.max_context_length] + "..."

        return full_context

    def format_with_citations(self, response: str, sources: list[dict]) -> str:
        """
        Add source citations to response

        Args:
            response: Generated response
            sources: Source documents used

        Returns:
            Response with citations
        """
        if not sources:
            return response

        citations = "\n\nSources:\n"
        for i, source in enumerate(sources, 1):
            citations += f"{i}. {source.get('source', 'Unknown')}: {source.get('text', '')[:100]}...\n"

        return response + citations

    def deduplicate_context(self, contexts: list[str]) -> list[str]:
        """
        Remove duplicate or very similar contexts

        Args:
            contexts: The context strings

        Returns:
            Deduplicated contexts
        """
        unique_contexts = []
        seen = set()

        for context in contexts:
            # Simple deduplication by exact match
            context_hash = hash(context)
            if context_hash not in seen:
                seen.add(context_hash)
                unique_contexts.append(context)

        return unique_contexts


def test_context_builder():
    print("=== Context Builder Test ===")

    # Sample retrieved documents
    retrieved_docs = [
        {
            "text": "Machine learning algorithms learn patterns from data",
            "source": "doc1.pdf",
            "score": 0.95
        },
        {
            "text": "Deep learning is a subset of machine learning",
            "source": "doc2.pdf",
            "score": 0.88
        },
        {
            "text": "Neural networks are the foundation of deep learning",
            "source": "doc3.pdf",
            "score": 0.82
        }
    ]

    query = "What is the relationship between deep learning and machine learning?"

    # Build context
    builder = ContextBuilder(max_context_length=500)
    context = builder.build_context(retrieved_docs, query, include_sources=True)

    print("Built context:")
    print(context)
    print()

    # Format with citations
    response = "Deep learning is a subset of machine learning that uses neural networks to learn patterns from data."

    formatted = builder.format_with_citations(response, retrieved_docs[:2])

    print("Response with citations:")
    print(formatted)

    print("✅ Context building working!\n")


if __name__ == "__main__":
    test_context_builder()
```

---

## Completion Checklist

- [ ] Vector search implemented
- [ ] BM25 search working
- [ ] Hybrid search with rank fusion
- [ ] Qdrant operations tested
- [ ] Neo4j knowledge graph created
- [ ] Context building functional
- [ ] RAG pipeline assembled
- [ ] Retrieval quality evaluated
