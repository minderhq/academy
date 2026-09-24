# Volume 6: RAG & Data Systems - Quick Reference

**Build Intelligent Data Systems** - Vector search, RAG, GraphRAG, and vector databases

---

## 🔍 Vector Search

### HNSW Index
```python
# HNSW: Hierarchical Navigable Small World
# Approximate nearest neighbor search
# Fast: O(log N) search time
# Efficient: High recall with small index

import faiss
import numpy as np

# Create HNSW index
def create_hnsw_index(embeddings, dim=1536, M=16, ef_construction=100):
    """
    Create HNSW index

    embeddings: (N, dim) array of embeddings
    M: Number of bi-directional links per node (default 16)
    ef_construction: Index build time accuracy (default 100)
    """
    index = faiss.IndexHNSWFlat(dim, M)

    # Set construction parameters
    index.hnsw.efConstruction = ef_construction
    index.hnsw.efSearch = 50  # Search time accuracy

    # Add embeddings
    index.add(embeddings.astype('float32'))

    return index

# Search
def search_hnsw(index, query_embedding, k=10):
    """
    Search HNSW index

    Returns: (distances, indices)
    """
    distances, indices = index.search(
        query_embedding.astype('float32').reshape(1, -1),
        k
    )

    return distances[0], indices[0]

# HNSW parameters
HNSW_PARAMETERS = {
    "M": {
        "description": "Number of bi-directional links",
        "typical": [8, 16, 32, 64],
        "effect": "Higher = better recall, slower search, larger index",
        "recommendation": "16 for most cases",
    },
    "efConstruction": {
        "description": "Index build time accuracy",
        "typical": [40, 100, 200, 400],
        "effect": "Higher = better recall, slower build",
        "recommendation": "100-200",
    },
    "efSearch": {
        "description": "Search time accuracy",
        "typical": [16, 32, 50, 100],
        "effect": "Higher = better recall, slower search",
        "recommendation": "50 for most cases",
    },
}
```

### Semantic Similarity
```python
from sentence_transformers import SentenceTransformer
import torch

# Load embedding model
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

# Encode sentences
sentences = [
    "The cat sits on the mat",
    "A feline is resting on the rug",
    "The sky is blue",
]

embeddings = model.encode(sentences)  # (3, 768)

# Compute similarities
def cosine_similarity(a, b):
    """Compute cosine similarity"""
    return torch.nn.functional.cosine_similarity(
        torch.tensor(a).unsqueeze(0),
        torch.tensor(b).unsqueeze(0)
    ).item()

# Pairwise similarities
similarities = np.zeros((len(sentences), len(sentences)))
for i in range(len(sentences)):
    for j in range(len(sentences)):
        similarities[i, j] = cosine_similarity(embeddings[i], embeddings[j])

# Similarity matrix:
#               cat sits   feline rug  sky blue
# cat sits      1.000      0.652       0.124
# feline rug    0.652      1.000       0.089
# sky blue      0.124      0.089       1.000
```

---

## 🔎 Hybrid Search

### Combining Vector + Keyword
```python
from typing import List, Dict
import numpy as np

class HybridSearch:
    """Hybrid search combining vector and keyword search"""

    def __init__(self, vector_index, keyword_index):
        self.vector_index = vector_index      # HNSW index
        self.keyword_index = keyword_index    # BM25 index

    def search(self, query, alpha=0.5, k=10):
        """
        Hybrid search

        alpha: Weight for vector search (0=keyword only, 1=vector only)
        k: Number of results
        """
        # Vector search
        vector_results = self.vector_index.search(query, k=k*2)

        # Keyword search
        keyword_results = self.keyword_index.search(query, k=k*2)

        # Reciprocal rank fusion
        fused_results = self.reciprocal_rank_fusion(
            vector_results,
            keyword_results,
            alpha=alpha
        )

        return fused_results[:k]

    def reciprocal_rank_fusion(self, results1, results2, alpha=0.5, k=60):
        """
        Reciprocal Rank Fusion

        Combines multiple ranked lists
        """
        scores = {}

        # Vector scores
        for rank, (doc_id, score) in enumerate(results1):
            fused_score = alpha / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + fused_score

        # Keyword scores
        for rank, (doc_id, score) in enumerate(results2):
            fused_score = (1 - alpha) / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + fused_score

        # Sort by fused score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_results

# Benefits:
# Vector search: Semantic understanding
# Keyword search: Exact match, important keywords
# Hybrid: Best of both
```

### Re-ranking
```python
from sentence_transformers import CrossEncoder

class ReRanker:
    """Re-rank search results using cross-encoder"""

    def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.model = CrossEncoder(model_name)

    def rerank(self, query, documents, top_k=10):
        """
        Re-rank documents using cross-encoder

        Slower but more accurate than bi-encoder
        """
        # Score each document
        scores = self.model.predict(
            [(query, doc) for doc in documents]
        )

        # Sort by score
        ranked_docs = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked_docs[:top_k]

# Pipeline:
# 1. Initial retrieval (bi-encoder, fast)
# 2. Re-ranking (cross-encoder, slow but accurate)
# 3. Return top-k re-ranked results

# Performance:
# Initial retrieval: ~100ms for 1000 docs
# Re-ranking: ~500ms for 100 docs
# Total: ~600ms for 1000 docs → 10 results
```

---

## 🕸️ GraphRAG

### Knowledge Graph Construction
```python
from neo4j import GraphDatabase
import re

class KnowledgeGraphBuilder:
    """Build knowledge graph from documents"""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def extract_entities(self, text):
        """Extract entities and relationships"""
        # In production, use NER model (spaCy, transformers)
        entities = []
        relationships = []

        # Simple example (use actual NER in production)
        sentences = text.split('.')
        for sent in sentences:
            # Extract entities (capitalized words)
            words = sent.split()
            ents = [w for w in words if w[0].isupper()]

            # Extract relationships
            for i in range(len(ents) - 1):
                relationships.append((ents[i], "RELATED_TO", ents[i+1]))

        return ents, relationships

    def add_document(self, doc_id, text):
        """Add document to knowledge graph"""
        entities, relationships = self.extract_entities(text)

        with self.driver.session() as session:
            # Add entities
            for entity in entities:
                session.run(
                    "MERGE (e:Entity {name: $name}) "
                    "SET e.docs = COALESCE(e.docs, []) + $doc_id",
                    name=entity, doc_id=doc_id
                )

            # Add relationships
            for subj, rel, obj in relationships:
                session.run(
                    "MATCH (s:Entity {name: $subj}) "
                    "MATCH (o:Entity {name: $obj}) "
                    "MERGE (s)-[r:RELATIONSHIP]->(o) "
                    "SET r.type = $rel, r.docs = COALESCE(r.docs, []) + $doc_id",
                    subj=subj, obj=obj, rel=rel, doc_id=doc_id
                )

    def query_graph(self, query):
        """Query knowledge graph"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e1:Entity)-[r:RELATIONSHIP]->(e2:Entity)
                WHERE e1.name CONTAINS $query OR e2.name CONTAINS $query
                RETURN e1.name, r.type, e2.name
                LIMIT 10
                """,
                query=query
            )

            return [record.values() for record in result]

# GraphRAG benefits:
# - Explicit relationships
# - Multi-hop reasoning
# - Explainable results
# - Better for complex queries
```

### Graph-enhanced Retrieval
```python
class GraphRAGRetriever:
    """Combine vector search with graph traversal"""

    def __init__(self, vector_index, knowledge_graph):
        self.vector_index = vector_index
        self.kg = knowledge_graph

    def retrieve(self, query, k=10, hops=1):
        """
        Retrieve with graph enhancement

        1. Initial vector search
        2. Expand with graph traversal
        3. Re-rank combined results
        """
        # Initial vector search
        initial_results = self.vector_index.search(query, k=k)

        # Extract entities from query
        query_entities = self.kg.extract_entities(query)

        # Graph traversal
        graph_results = []
        for entity in query_entities:
            related = self.kg.query_graph(entity)
            graph_results.extend(related)

        # Combine results
        combined = self.combine_results(initial_results, graph_results)

        # Re-rank
        reranked = self.rerank(query, combined)

        return reranked[:k]

    def combine_results(self, vector_results, graph_results):
        """Combine vector and graph results"""
        # Deduplicate
        seen = set()
        combined = []

        for doc in vector_results + graph_results:
            if doc['id'] not in seen:
                seen.add(doc['id'])
                combined.append(doc)

        return combined
```

---

## 🗄️ Vector Databases

### Qdrant
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Initialize
client = QdrantClient(url="http://localhost:6333")

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=1536,  # Embedding dimension
        distance=Distance.COSINE,
        hnsw_config={
            "m": 16,
            "ef_construct": 100,
        },
    ),
)

# Insert documents
def insert_documents(documents):
    """Insert documents into Qdrant"""
    points = []
    for i, doc in enumerate(documents):
        # Create embedding
        embedding = model.encode(doc['text'])

        # Create point
        point = PointStruct(
            id=i,
            vector=embedding.tolist(),
            payload={
                "text": doc['text'],
                "metadata": doc.get('metadata', {}),
            }
        )
        points.append(point)

    # Upsert
    client.upsert(
        collection_name="documents",
        points=points,
    )

# Search with filters
def search_with_filters(query, filters=None, top_k=10):
    """Search with optional payload filters"""
    query_embedding = model.encode(query)

    results = client.search(
        collection_name="documents",
        query_vector=query_embedding.tolist(),
        query_filter=filters,  # {"must": [{"key": "category", "match": {"value": "tech"}}]}
        limit=top_k,
    )

    return results

# Qdrant advantages:
# - Fast (written in Rust)
# - Easy to use (Python client)
# - Built-in filtering
# - Supports HNSW
```

### Pinecone
```python
import pinecone

# Initialize
pinecone.init(
    api_key="your-api-key",
    environment="us-east-1-aws"
)

# Create index
pinecone.create_index(
    name="documents",
    dimension=1536,
    metric="cosine",
    pods=1,  # Number of pods
    replicas=1,  # Replicas for high availability
    pod_type="p1.x1"  # Pod type (p1 = optimized for speed)
)

# Connect
index = pinecone.Index("documents")

# Upsert
def upsert_documents(documents):
    vectors = []
    for i, doc in enumerate(documents):
        embedding = model.encode(doc['text'])
        vectors.append((
            str(i),  # Vector ID
            embedding.tolist(),  # Vector
            doc.get('metadata', {})  # Metadata
        ))

    index.upsert(vectors)

# Query
results = index.query(
    vector=model.encode("query text").tolist(),
    top_k=10,
    include_metadata=True,
    filter={"category": {"$eq": "tech"}},  # Metadata filter
)

# Pinecone advantages:
# - Fully managed (no infrastructure)
# - Scalable
# - Fast
# - Easy to set up
```

---

## 📊 RAG Evaluation

### Retrieval Metrics
```python
import numpy as np

class RetrievalMetrics:
    """Evaluate retrieval quality"""

    @staticmethod
    def precision_at_k(retrieved_docs, relevant_docs, k):
        """
        Precision@K: % of retrieved docs that are relevant

        retrieved_docs: List of retrieved doc IDs
        relevant_docs: Set of relevant doc IDs
        k: Evaluate top-k results
        """
        top_k = retrieved_docs[:k]
        relevant_in_top_k = sum(1 for doc in top_k if doc in relevant_docs)

        return relevant_in_top_k / k

    @staticmethod
    def recall_at_k(retrieved_docs, relevant_docs, k):
        """
        Recall@K: % of relevant docs retrieved

        retrieved_docs: List of retrieved doc IDs
        relevant_docs: Set of relevant doc IDs
        k: Evaluate top-k results
        """
        top_k = retrieved_docs[:k]
        relevant_in_top_k = sum(1 for doc in top_k if doc in relevant_docs)

        return relevant_in_top_k / len(relevant_docs)

    @staticmethod
    def mean_reciprocal_rank(retrieved_docs, relevant_docs):
        """
        MRR: 1 / rank of first relevant doc

        Higher is better (max 1.0)
        """
        for i, doc in enumerate(retrieved_docs):
            if doc in relevant_docs:
                return 1.0 / (i + 1)

        return 0.0

    @staticmethod
    def mean_average_precision(retrieved_docs_list, relevant_docs_list):
        """
        MAP: Mean of Average Precision across queries

        Higher is better
        """
        average_precisions = []

        for retrieved_docs, relevant_docs in zip(retrieved_docs_list, relevant_docs_list):
            precisions = []
            num_relevant = 0

            for i, doc in enumerate(retrieved_docs):
                if doc in relevant_docs:
                    num_relevant += 1
                    precision = num_relevant / (i + 1)
                    precisions.append(precision)

            if precisions:
                average_precisions.append(np.mean(precisions))
            else:
                average_precisions.append(0.0)

        return np.mean(average_precisions)

# Example usage
retrieved = ["doc1", "doc5", "doc3", "doc8", "doc2"]
relevant = {"doc1", "doc3", "doc7"}

metrics = RetrievalMetrics()
print(f"P@5: {metrics.precision_at_k(retrieved, relevant, 5):.2f}")
print(f"R@5: {metrics.recall_at_k(retrieved, relevant, 5):.2f}")
print(f"MRR: {metrics.mean_reciprocal_rank(retrieved, relevant):.2f}")
```

### End-to-End Evaluation
```python
from ragas import evaluate
from datasets import Dataset

# Prepare evaluation dataset
evaluation_data = {
    "question": [
        "What is the capital of France?",
        "Who wrote Romeo and Juliet?",
    ],
    "answer": [
        "Paris",
        "William Shakespeare",
    ],
    "contexts": [
        ["France is a country in Europe. Its capital is Paris.", "Paris is known for the Eiffel Tower."],
        ["Romeo and Juliet was written by Shakespeare in the late 16th century."],
    ],
    "ground_truths": [
        ["Paris"],
        ["William Shakespeare", "Shakespeare"],
    ],
}

dataset = Dataset.from_dict(evaluation_data)

# Evaluate
result = evaluate(dataset)

# Metrics:
# - Faithfulness: Does the answer stick to the retrieved context?
# - Answer Relevancy: Is the answer relevant to the question?
# - Context Precision: Are the retrieved contexts relevant?
# - Context Recall: Were all relevant contexts retrieved?

print(result)
```

---

## 🎯 Volume 6 Checklist

- [ ] Understand HNSW indexing
- [ ] Implement vector search
- [ ] Combine vector + keyword search
- [ ] Use re-ranking
- [ ] Build knowledge graph
- [ ] Implement GraphRAG
- [ ] Use Qdrant or Pinecone
- [ ] Evaluate retrieval quality
- [ ] Build production RAG system

---

## 🚀 Next Steps

1. Complete LAB-007: Production RAG
2. Read 6302-CAG-Long-Context-Architectures.md
3. Practice with EXP experiments
4. Build domain-specific RAG

---

**Last Updated:** 2026-02-04
**Volume:** 6 - RAG & Data Systems
**Estimated Time:** 40-45 hours
