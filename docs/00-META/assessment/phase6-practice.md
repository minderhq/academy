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

**Difficulty:** Beginner
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
    test_cosine_similarity()
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
   ```
   score(D,Q) = Σ IDF(qi) × (f(qi,D) × (k1 + 1)) /
                         (f(qi,D) + k1 × (1 - b + b × |D| / avgdl))
   ```

3. Test with sample documents and queries

### Solution Template

```python
import math
from collections import Counter
from typing import List, Tuple

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

    def index(self, documents: List[str]):
        """
        Build BM25 index from documents.

        Args:
            documents: List of document strings
        """
        # TODO: Implement
        # 1. Tokenize documents
        # 2. Calculate document frequencies
        # 3. Calculate average document length
        pass

    def search(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
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
   ```
   fused_score(d) = Σ 1 / (k + rank_i(d))
   ```
   Where k=60 (default) and rank_i is rank in result list i

3. Implement tunable alpha parameter for result blending

### Solution Template

```python
from typing import List, Tuple, Dict
import numpy as np

class HybridRetriever:
    def __init__(self, documents: List[str], embedding_model):
        """
        Initialize hybrid retriever.

        Args:
            documents: List of document strings
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
    ) -> List[Tuple[int, float]]:
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

# Close driver when done
def close(self):
    self.driver.close()
```

### Success Criteria

- [ ] Entities created successfully
- [ ] Relationships formed correctly
- - Graph traversal returns connected entities
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
from typing import List, Dict
import tiktoken

class ContextBuilder:
    def __init__(self, max_tokens=4000, model="gpt-3.5-turbo"):
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))

    def stuff_context(self, chunks: List[str], query: str) -> str:
        """
        Stuff all chunks into context.

        Args:
            chunks: List of text chunks
            query: User query

        Returns:
            Formatted context string
        """
        # TODO: Implement with token limit
        pass

    def map_reduce_context(self, chunks: List[str], query: str) -> str:
        """
        Map-reduce strategy for large context.

        Args:
            chunks: List of text chunks
            query: User query

        Returns:
            Summarized context string
        """
        # TODO: Implement
        # 1. Summarize each chunk
        # 2. Combine summaries
        pass

    def refine_context(self, chunks: List[str], query: str) -> str:
        """
        Iteratively refine context.

        Args:
            chunks: List of text chunks
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
from typing import List, Dict, Any

class RAGPipeline:
    def __init__(self, config: Dict[str, Any]):
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

    def ingest_documents(self, documents: List[str], metadata: List[Dict]):
        """Ingest documents into the pipeline."""
        # TODO: Implement
        # 1. Chunk documents
        # 2. Generate embeddings
        # 3. Index in Qdrant
        # 4. Build BM25 index
        pass

    def retrieve(self, query: str, top_k: int = 20) -> List[Dict]:
        """Retrieve relevant documents."""
        # TODO: Implement hybrid retrieval
        pass

    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """Re-rank retrieved documents."""
        # TODO: Implement re-ranking
        pass

    def generate(self, query: str, context: List[Dict]) -> str:
        """Generate response using LLM."""
        # TODO: Implement generation
        pass

    def query(self, question: str) -> Dict[str, Any]:
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
- [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)

---

**Last Updated:** 2026-02-05
**Phase:** 6 - Data Nexus
**Status:** Ready for Practice
