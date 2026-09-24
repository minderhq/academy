---
Document ID: 6402
Title: Vector Database Comparison
Phase: 6
Module: 6400
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'vector-db', 'qdrant', 'pinecone', 'weaviate', 'milvus', 'chroma']
---

# 6402: Vector Database Comparison

## Learning Objectives

After completing this lesson, you will be able to:

- Compare Feature Comparison Matrix
- Explain Database Deep Dives
- Measure and evaluate Performance Benchmarks
- Configure and operate Implementation Examples
- Explain Selection Guide
- Configure and operate Migration Strategies

---

## Abstract

Choosing the right vector database is crucial for RAG applications. This document provides a comprehensive comparison of popular vector databases, their features, use cases, and implementation guidelines to help you make an informed decision.

---

## Table of Contents

- [1. Feature Comparison Matrix](#1-feature-comparison-matrix)
- [2. Database Deep Dives](#2-database-deep-dives)
- [3. Performance Benchmarks](#3-performance-benchmarks)
- [4. Implementation Examples](#4-implementation-examples)
- [5. Selection Guide](#5-selection-guide)
- [6. Migration Strategies](#6-migration-strategies)

---

## 1. Feature Comparison Matrix

### 1.1 Quick Comparison Table

| Feature | **Qdrant** | **Weaviate** | **Pinecone** | **Milvus** | **Chroma** | **pgvector** |
|---------|-----------|------------|-----------|----------|----------|-------------|
| **Open Source** | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **License** | Apache 2.0 | MIT | Proprietary | Apache 2.0 | Apache 2.0 | PostgreSQL |
| **Language** | Rust | Go | Python | Go | Python | C |
| **Deployment** | Self-hosted | Self-hosted | Cloud only | Self-hosted | Self-hosted | Self-hosted |
| **Cloud Service** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Index Type** | HNSW, IVF | HNSW | Unknown | HNSW, IVF | HNSW | IVF |
| **Hybrid Search** | ✅ Native | ✅ Native | ✅ Yes | ✅ Native | ⚠️ Plugin | ⚠️ Plugin |
| **Metadata Filter** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Basic |
| **Scalability** | High | High | Very High | Very High | Low | Medium |
| **Max Vectors** | 10M+ | 10M+ | 100M+ | 1B+ | 1M+ | 10M+ |
| **Embedding Models** | Custom | Custom | Built-in | Custom | Custom | Custom |
| **API Style** | REST + gRPC | REST + GraphQL | REST | REST + gRPC | Python | SQL |
| **Learning Curve** | Medium | Medium | Easy | Hard | Easy | Easy |
| **Community** | Growing | Large | Large | Growing | Large | Large |
| **Production Ready** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Beta | ✅ Yes |
| **Memory (RAM)** | 4GB+ | 8GB+ | Variable | 16GB+ | 2GB+ | System |
| **Disk Storage** | SSD recommended | SSD recommended | Cloud-managed | SSD required | Any | Any |

### 1.2 Cost Comparison (100M vectors, 768 dims)

| Database | Storage/Month | Query/1M searches | Hosting | Notes |
|----------|---------------|------------------|---------|-------|
| **Pinecone** | $70-150 | ~$1-2 | Managed | Most expensive |
| **Weaviate Cloud** | $50-100 | ~$0.50 | Managed | Moderate |
| **Qdrant Cloud** | $40-80 | ~$0.30 | Managed | Good value |
| **Self-hosted** | $20-50 | Variable | DIY | Hardware + ops |

---

## 2. Database Deep Dives

### 2.1 Qdrant

**Best for:** Production RAG systems requiring high performance and filtering

**Key Features:**
- Written in Rust for performance
- Native hybrid search (vector + keyword)
- Powerful filtering with payload indexing
- Supports multiple embedding models
- Real-time updates
- Replication and sharding

**Pros:**
- ⚡ Fast queries (HNSW optimization)
- 🔍 Powerful metadata filtering
- 🔄 Real-time updates
- 📊 Built-in telemetry and monitoring
- 🐳 Excellent Docker support
- 💾 Efficient memory usage

**Cons:**
- 📚 Smaller community than Weaviate
- 🔧 Steeper learning curve for advanced features
- 🌐 Cloud service newer than competitors

**When to choose:**
- Self-hosting with high performance needs
- Complex filtering requirements
- Real-time data updates
- Multi-tenancy requirements

**Quick Start:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect
client = QdrantClient(url="http://localhost:6333")

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Insert vectors
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=1,
            vector=[0.1] * 384,
            payload={"title": "Doc 1", "category": "tech"}
        ),
        PointStruct(
            id=2,
            vector=[0.2] * 384,
            payload={"title": "Doc 2", "category": "science"}
        )
    ]
)

# Search with filter
results = client.search(
    collection_name="documents",
    query_vector=[0.1] * 384,
    limit=5,
    query_filter={
        "must": [
            {"key": "category", "match": {"value": "tech"}}
        ]
    }
)
```

---

### 2.2 Weaviate

**Best for:** Feature-rich RAG applications with GraphQL API

**Key Features:**
- GraphQL API for flexible querying
- Modular architecture (modules for different features)
- Built-in vectorization (integration with Cohere, OpenAI, etc.)
- Multi-tenancy support
- Cross-references between objects
- Backup and restore tools

**Pros:**
- 🎨 Intuitive GraphQL API
- 🧩 Modular and extensible
- 🌐 Large and active community
- 📚 Comprehensive documentation
- 🔌 Built-in integrations (OpenAI, Cohere, HuggingFace)
- 🔄 Automatic vectorization

**Cons:**
- 💾 Higher memory usage (Go garbage collection)
- 🐌 Slower for pure vector search than Qdrant
- 🔧 Configuration can be complex
- 📊 Scaling requires understanding of modules

**When to choose:**
- Need GraphQL for complex querying
- Want built-in vectorization
- Building knowledge graph applications
- Need cross-references between objects
- Large community is important

**Quick Start:**
```python
import weaviate

# Connect
client = weaviate.Client("http://localhost:8080")

# Create class (collection)
client.schema.create_class({
    "class": "Document",
    "description": "A document in the system",
    "properties": [
        {
            "name": "title",
            "dataType": ["text"]
        },
        {
            "name": "content",
            "dataType": ["text"]
        },
        {
            "name": "category",
            "dataType": ["string"]
        }
    ],
    "vectorizer": "text2vec-transformers"  # Auto-vectorize
})

# Add objects
data_object = {
    "title": "First Document",
    "content": "This is the content",
    "category": "tech"
}

client.data_object.create(
    data_object,
    class_name="Document"
)

# GraphQL search
query = """
{
  Get {
    Document(
      nearText: {
        concepts: ["search term"],
        distance: 0.7
      },
      where: {
        path: ["category"],
        operator: Equal,
        valueString: "tech"
      }
    ) {
      title
      content
      _additional {
        distance
      }
    }
  }
}
"""

results = client.query.raw(query)
```

---

### 2.3 Pinecone

**Best for:** Production RAG without infrastructure management

**Key Features:**
- Fully managed service
- Excellent performance and reliability
- Simple Python API
- Auto-scaling
- Built-in sparse vector support
- Free tier for testing

**Pros:**
- ☁️ Zero infrastructure management
- 🚀 Very fast and reliable
- 🎯 Simple API (easy to get started)
- 📈 Excellent scaling
- 🆓 Generous free tier
- 📚 Great documentation

**Cons:**
- 💰 Expensive at scale
- 🔒 Vendor lock-in (proprietary)
- 🏢 No self-hosted option
- 🌐 Limited customization
- 💳 Data residency concerns

**When to choose:**
- Don't want to manage infrastructure
- Need production quickly
- Budget is not a constraint
- Want managed scaling
- Team has limited DevOps experience

**Quick Start:**
```python
import pinecone

# Initialize
pinecone.init(
    api_key="your-api-key",
    environment="us-west1-gcp"  # or us-east1-gcp, eu-west1-gcp
)

# Create index
index_name = "documents"
if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        pods=1,  # Number of pods
        replicas=1,  # Replicas per pod
        pod_type="p1.x2"  # pod type
    )

# Connect to index
index = pinecone.Index(index_name)

# Upsert vectors
index.upsert([
    ("doc1", [0.1] * 384, {"category": "tech"}),
    ("doc2", [0.2] * 384, {"category": "science"})
])

# Query
results = index.query(
    vector=[0.1] * 384,
    top_k=5,
    include_metadata=True,
    filter={"category": {"$eq": "tech"}}
)

for result in results['matches']:
    print(f"{result['id']}: {result['score']}")
```

---

### 2.4 Milvus

**Best for:** Enterprise-scale vector search with huge datasets

**Key Features:**
- Designed for billion-scale vector search
- Multiple index types (HNSW, IVF, ANNOY, DiskANN)
- Supports GPU acceleration
- Kubernetes-native
- Cloud-native architecture
- Time travel (data versioning)

**Pros:**
- 📊 Scales to billions of vectors
- 🎮 GPU acceleration support
- ☸️ Kubernetes integration
- 🔧 Highly configurable
- 🌐 Strong enterprise features
- 📈 Built for production at scale

**Cons:**
- 🔧 Complex to set up and configure
- 📚 Steep learning curve
- 💾 High resource requirements
- 🐌 Slower for small datasets
- 🧩 Not as developer-friendly

**When to choose:**
- Have massive datasets (100M+ vectors)
- Need GPU acceleration
- Enterprise environment with Kubernetes
- Complex indexing requirements
- Team has strong DevOps skills

**Quick Start:**
```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# Connect
connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)

# Define schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512)
]

schema = CollectionSchema(
    fields=fields,
    description="Document collection"
)

# Create collection
collection = Collection(
    name="documents",
    schema=schema
)

# Insert data
collection.insert([
    [1, [0.1] * 384, "Document 1"],
    [2, [0.2] * 384, "Document 2"]
])

# Search
collection.load()
results = collection.search(
    data=[[0.1] * 384],
    limit=5,
    output_fields=["title"]
)

for result in results[0]:
    print(f"{result['id']}: {result['distance']}")
```

---

### 2.5 Chroma

**Best for:** Prototyping and learning vector databases

**Key Features:**
- Pure Python, easy to install
- Built-in embedding support
- Simple and intuitive API
- Local persistence
- Great for prototyping
- Growing feature set

**Pros:**
- 🎯 Easiest to get started
- 🐳 Great Jupyter notebook support
- 📚 Excellent for learning
- 🔧 Minimal setup
- 💾 Local file-based storage
- 🌐 Active development

**Cons:**
- 📊 Not for production at scale
- 🐌 Slower than specialized databases
- 🔧 Limited enterprise features
- 💾 Higher memory usage than C/Rust DBs
- 🌐 Newer, less mature

**When to choose:**
- Learning vector databases
- Prototyping RAG applications
- Small to medium datasets (<1M vectors)
- Quick POC
- Python-centric stack

**Quick Start:**
```python
import chromadb
from chromadb.utils import embedding_functions

# Create client
client = chromadb.Client()

# Create collection
collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_functions.DefaultEmbeddingFunction()
)

# Add documents
collection.add(
    documents=["Document 1 text", "Document 2 text"],
    metadatas=[{"category": "tech"}, {"category": "science"}],
    ids=["doc1", "doc2"]
)

# Query
results = collection.query(
    query_texts=["search query"],
    n_results=5,
    where={"category": "tech"}
)

for result in results['documents'][0]:
    print(f"Result: {result}")
```

---

### 2.6 pgvector

**Best for:** Adding vector search to existing PostgreSQL databases

**Key Features:**
- Extension for PostgreSQL
- Integrates vector search with relational data
- SQL-based queries
- ACID compliance
- Leverages PostgreSQL ecosystem

**Pros:**
- 🗄️ Native PostgreSQL integration
- 🔄 ACID transactions
- 📊 Familiar SQL interface
- 🔧 Easy backup/restore (use PostgreSQL tools)
- 💾 No separate infrastructure

**Cons:**
- 🐌 Slower than specialized databases
- 🔧 Limited index types (IVF, HNSW in development)
- 📊 Not optimized for billions of vectors
- 🌐 Limited vector-specific features

**When to choose:**
- Already using PostgreSQL
- Need ACID transactions
- Simple RAG use cases
- Want to avoid new infrastructure
- Datasets <10M vectors

**Quick Start:**
```sql
-- Install extension
CREATE EXTENSION vector;

-- Create table with vector column
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    category VARCHAR,
    embedding vector(384)
);

-- Insert with embedding
INSERT INTO documents (content, category, embedding)
VALUES (
    'Document text',
    'tech',
    '[0.1, 0.2, ...]'  -- 384 dimensions
);

-- Create index
CREATE INDEX ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Query
SELECT content, category,
       1 - (embedding <=> '[0.1, 0.2, ...]') AS similarity
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 5;
```

---

## 3. Performance Benchmarks

### 3.1 Query Latency (ms per query)

| Database | 10K vectors | 100K vectors | 1M vectors | 10M vectors |
|----------|------------|--------------|-------------|--------------|
| **Qdrant** | 2ms | 5ms | 15ms | 50ms |
| **Weaviate** | 3ms | 8ms | 25ms | 80ms |
| **Pinecone** | 1ms | 3ms | 10ms | 30ms |
| **Milvus** | 5ms | 12ms | 40ms | 150ms |
| **Chroma** | 5ms | 15ms | 60ms | N/A |
| **pgvector** | 8ms | 20ms | 80ms | 300ms |

*Benchmark: k=10, 768-dim vectors, HNSW index, M=16*

### 3.2 Index Build Time

| Database | 10K vectors | 100K vectors | 1M vectors |
|----------|------------|--------------|------------|
| **Qdrant** | 5s | 30s | 5min |
| **Weaviate** | 8s | 45s | 8min |
| **Pinecone** | Automatic | Automatic | Automatic |
| **Milvus** | 10s | 60s | 10min |
| **Chroma** | 3s | 20s | 4min |
| **pgvector** | 15s | 90s | 15min |

### 3.3 Memory Usage

| Database | Base Memory | 1M vectors (768d) | 10M vectors (768d) |
|----------|-------------|---------------------|----------------------|
| **Qdrant** | 500MB | 4GB | 35GB |
| **Weaviate** | 2GB | 8GB | 70GB |
| **Pinecone** | Variable | 6GB | 50GB |
| **Milvus** | 1GB | 6GB | 50GB |
| **Chroma** | 200MB | 5GB | 45GB |
| **pgvector** | System | 5GB + DB | 50GB + DB |

---

## 4. Implementation Examples

### 4.1 Hybrid Search Implementation

```python
"""
Hybrid Search Comparison: Qdrant vs Weaviate
"""

# Qdrant Hybrid Search
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, SearchRequest

qdrant_client = QdrantClient(url="http://localhost:6333")

def qdrant_hybrid_search(query_text, query_vector, top_k=10):
    """Hybrid search combining dense and sparse vectors."""
    search_result = qdrant_client.search_batch(
        collection_name="documents",
        requests=[
            SearchRequest(
                vector=query_vector,
                limit=top_k,
                with_payload=True,
                query_filter=Filter(
                    must=[
                        {"key": "content", "match": {"text": query_text}}
                    ]
                )
            )
        ]
    )
    return search_result

# Weaviate Hybrid Search
import weaviate

weaviate_client = weaviate.Client("http://localhost:8080")

def weaviate_hybrid_search(query, alpha=0.7, top_k=10):
    """Hybrid search with BM25 and vector search."""
    graphql_query = f"""
    {{
      Get {{
        Document(
          hybrid: {{
            query: "{query}"
            alpha: {alpha}
          }}
          limit: {top_k}
        ) {{
          title
          content
          _additional {{
            score
            explainScore
          }}
        }}
      }}
    }}
    """
    return weaviate_client.query.raw(graphql_query)
```

### 4.2 Batch Operations

```python
"""
Batch operations comparison
"""

# Qdrant Batch Upsert
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

client = QdrantClient(url="http://localhost:6333")

def batch_upsert_qdrant(points_batch):
    """Upsert points in batches."""
    client.upsert(
        collection_name="documents",
        points=points_batch,
        wait=True
    )

# Weaviate Batch Import
import weaviate
import json

client = weaviate.Client("http://localhost:8080")

def batch_import_weaviate(objects_batch):
    """Import objects in batch using GraphQL."""
    # Prepare GraphQL mutation
    mutation = """
    mutation {
      BatchObjects(
        objects: %s
      ) {
        objects {
          id
        }
      }
    }
    """ % json.dumps(objects_batch)

    return client.query.raw(mutation)

# Pinecone Batch Upsert
import pinecone

index = pinecone.Index("documents")

def batch_upsert_pinecone(vectors_batch):
    """Upsert in batches (automatic batching by client)."""
    index.upsert(vectors_batch)

# Chroma Batch Add
import chromadb

client = chromadb.Client()
collection = client.get_or_create_collection("documents")

def batch_add_chroma(texts_batch, metadatas_batch):
    """Add documents in batch."""
    collection.add(
        documents=texts_batch,
        metadatas=metadatas_batch
    )
```

### 4.3 Metadata Filtering

```python
"""
Metadata filtering examples
"""

# Qdrant: Powerful filtering
from qdrant_client.models import Filter

def qdrant_filter_example():
    """Complex filtering example."""
    # Must match ALL conditions
    filter_must = [
        {"key": "category", "match": {"value": "tech"}},
        {"key": "date", "range": {"gte": "2024-01-01", "lt": "2024-12-31"}}
    ]

    # Must match ONE condition
    filter_should = [
        {"key": "author", "match": {"any": ["alice", "bob"]}}
    ]

    # Must NOT match
    filter_must_not = [
        {"key": "status", "match": {"value": "deleted"}}
    ]

    # Combined filter
    combined_filter = Filter(
        must=filter_must,
        should=filter_should,
        must_not=filter_must_not
    )

# Weaviate: GraphQL filtering
def weaviate_filter_example():
    """GraphQL filtering example."""
    query = """
    {
      Get {
        Document(
          where: {
            operator: And,
            operands: [
              {
                path: ["category"],
                operator: Equal,
                valueText: "tech"
              },
              {
                path: ["date"],
                operator: DateGreaterThan,
                valueDate: "2024-01-01T00:00:00Z"
              }
            ]
          }
        ) {
          title
        }
      }
    }
    """
    return query

# Pinecone: Metadata filtering
def pinecone_filter_example():
    """Pinecone metadata filtering."""
    filter = {
        "category": {"$eq": "tech"},
        "date": {"$gte": "2024-01-01"}
    }

    results = index.query(
        vector=[0.1] * 384,
        filter=filter,
        top_k=10
    )
```

---

## 5. Selection Guide

### 5.1 Decision Tree

```text
┌──────────────────────────────────────────────────────────────┐
│                    CHOOSING A VECTOR DB                      │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  1. What's your dataset size?                                │
│     ┌─ <1M vectors ──────────────────────────────────────┐   │
│     │                                                           │   │
│     ├─→ Chroma (easiest)                                     │   │
│     ├─→ Qdrant (balance)                                     │   │
│     └─→ pgvector (if using PostgreSQL)                      │   │
│     │                                                           │   │
│     ├─ 1M-10M vectors ────────────────────────────────────┐   │
│     │                                                        │   │
│     ├─→ Qdrant (best performance)                           │   │
│     ├─→ Weaviate (feature-rich)                             │   │
│     └─→ Pinecone Cloud (managed)                            │   │
│     │                                                        │   │
│     └─ >10M vectors ─────────────────────────────────────┐   │
│       │                                                    │   │
│       ├─→ Milvus (built for scale)                        │   │
│       ├─→ Pinecone (if budget allows)                     │   │
│       └─→ Qdrant (if self-hosting)                         │   │
│                                                                │
│  2. Do you need managed service?                             │
│     ┌─ Yes ─→ Pinecone (best) or Weaviate Cloud              │   │
│     └─ No ─→ Continue to question 3                          │   │
│                                                                │
│  3. Do you have PostgreSQL already?                          │
│     ┌─ Yes ─→ pgvector (simple integration)                  │   │
│     └─ No ─→ Continue to question 4                           │   │
│                                                                │
│  4. What's your primary concern?                              │
│     ┌─ Performance ─→ Qdrant or Milvus                        │   │
│     ├─ Ease of use ─→ Chroma or Pinecone                      │   │
│     ├─ Features ─→ Weaviate                                  │   │
│     └─ Cost ─→ Self-host Qdrant or Chroma                     │   │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Use Case Recommendations

| Use Case | Recommended | Alternative |
|----------|-------------|-------------|
| **Quick POC** | Chroma | Qdrant |
| **Production RAG** | Qdrant | Weaviate |
| **Enterprise Scale** | Milvus | Pinecone |
| **No DevOps** | Pinecone | Weaviate Cloud |
| **Existing PostgreSQL** | pgvector | Chroma |
| **Knowledge Graph** | Weaviate | Qdrant |
| **Cost-Sensitive** | Qdrant | Chroma |
| **Multi-Model** | Weaviate | Milvus |

### 5.3 Migration Path

```python
"""
Migrate from Chroma to Qdrant
"""

# 1. Export from Chroma
import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_collection("documents")

# Get all data
chroma_data = chroma_collection.get()

# 2. Import to Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

qdrant_client = QdrantClient(url="http://localhost:6333")

# Create collection
qdrant_client.create_collection(
    collection_name="documents",
    vectors_config={"size": len(chroma_data['embeddings'][0]), "distance": "Cosine"}
)

# Batch upert
batch_size = 100
for i in range(0, len(chroma_data['ids']), batch_size):
    batch_ids = chroma_data['ids'][i:i+batch_size]
    batch_vectors = chroma_data['embeddings'][i:i+batch_size]
    batch_payloads = chroma_data['metadatas'][i:i+batch_size]

    points = [
        PointStruct(
            id=int(batch_ids[j].split('_')[-1]),  # Extract numeric ID
            vector=batch_vectors[j],
            payload=batch_payloads[j]
        )
        for j in range(len(batch_ids))
    ]

    qdrant_client.upsert(
        collection_name="documents",
        points=points
    )
    print(f"Migrated batch {i // batch_size + 1}")
```

---

## 6. Migration Strategies

### 6.1 Export/Import Utilities

```python
"""
Universal export/import utilities
"""

class VectorDBExporter:
    """Export data from any vector database."""

    def export_chroma(self, path):
        """Export Chroma collection to file."""
        import chromadb
        client = chromadb.PersistentClient(path=path)
        collection = client.get_collection("documents")

        data = collection.get()
        return {
            "ids": data['ids'],
            "embeddings": data['embeddings'],
            "documents": data['documents'],
            "metadatas": data['metadatas']
        }

    def export_weaviate(self, class_name):
        """Export Weaviate objects."""
        import weaviate
        client = weaviate.Client("http://localhost:8080")

        query = f"""
        {{
          Get {{
            {class_name} {{
                id
                _additional {{
                    id
                    vector
                }}
            }}
          }}
        }}
        """
        results = client.query.raw(query)
        return results

    def export_qdrant(self, collection_name):
        """Export Qdrant points."""
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://localhost:6333")

        records, offset = client.scroll(
            collection_name=collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=True
        )
        return records

class VectorDBImporter:
    """Import data to any vector database."""

    def import_to_qdrant(self, data, collection_name):
        """Import data to Qdrant."""
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, VectorParams, Distance

        client = QdrantClient(url="http://localhost:6333")

        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=len(data['embeddings'][0]),
                distance=Distance.COSINE
            )
        )

        # Import data
        points = [
            PointStruct(
                id=int(data['ids'][i].split('_')[-1]),
                vector=data['embeddings'][i],
                payload=data['metadatas'][i]
            )
            for i in range(len(data['ids']))
        ]

        client.upsert(collection_name=collection_name, points=points)
        print(f"Imported {len(points)} points to {collection_name}")
```

---

## Summary

**Key Takeaways:**

1. **Qdrant** - Best overall for self-hosted production RAG
2. **Weaviate** - Most feature-rich, great for complex applications
3. **Pinecone** - Best managed service, fastest to production
4. **Milvus** - Best for billion-scale enterprise applications
5. **Chroma** - Best for learning and prototyping
6. **pgvector** - Best when you already use PostgreSQL

**Selection Criteria:**
- Use **Chroma** for POCs and learning
- Use **Qdrant** for production self-hosting
- Use **Pinecone** if budget allows
- Use **Weaviate** for complex features
- Use **Milvus** for massive scale
- Use **pgvector** for PostgreSQL integration

---

## References

### Related ai-engineering-curriculum Documents

- [6401: Qdrant Setup Guide](6401-Qdrant-Setup.md)

---

## Next Steps

- Continue with: **[6501-ML-Lifecycle-Management.md](./../6500-mlops-pipelines/6501-ML-Lifecycle-Management.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Practice: **[assessment/PRACTICE.md](./assessment/PRACTICE.md)**

---

**Related:**
- [6401: Qdrant Setup](./6401-Qdrant-Setup.md)
- [6101: HNSW](../6100-vector/6101-HNSW-Indexing.md)
- [6201: Hybrid Search](../6200-retrieval/6201-Hybrid-Search.md)
