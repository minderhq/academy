---
Document ID: 6400-PRACTICE
Title: "6400: Vector Databases - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'rag', 'vector-db']
---

# 6400: Vector Databases - Practice

## Exercises

### Exercise 1: Qdrant Setup and Operations

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Initialize Qdrant client
print("Connecting to Qdrant...")
client = QdrantClient(url="http://localhost:6333")

# Create collection
collection_name = "documents"
print(f"Creating collection '{collection_name}'...")
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# Insert vectors
print("Encoding documents...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
documents = [
    "Machine learning is a subset of AI.",
    "Python is a popular programming language.",
    "Paris is the capital of France.",
    "The Earth orbits around the Sun.",
    "Water boils at 100 degrees Celsius.",
]

vectors = embedder.encode(documents).tolist()

print("Upserting points...")
client.upsert(
    collection_name=collection_name,
    points=[
        PointStruct(id=i, vector=vec, payload={"text": doc, "id": i})
        for i, (vec, doc) in enumerate(zip(vectors, documents))
    ],
)

# Search
print("\nSearching...")
query = "artificial intelligence"
query_vector = embedder.encode([query])[0].tolist()

results = client.query_points(
    collection_name=collection_name,
    query=query_vector,
    limit=3,
).points

print(f"Query: '{query}'\n")
for result in results:
    print(f"[{result.score:.3f}] {result.payload['text']}")

# Expected output:
# - "Machine learning is a subset of AI." ranked highest (score ~0.8)
# - Other documents have lower scores
# - Cosine similarity used for ranking
```

### Exercise 2: Milvus Operations

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# Connect to Milvus
print("Connecting to Milvus...")
connections.connect(host="localhost", port="19530")

# Define schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
]

schema = CollectionSchema(fields, description="Document collection")

# Create collection
print("Creating collection...")
collection = Collection(name="documents", schema=schema)

# Insert data
import numpy as np
data = [
    [vectors[i] for i in range(len(vectors))],  # embeddings
    [documents[i] for i in range(len(documents))],  # texts
]

print("Inserting data...")
collection.insert(data)
collection.flush()

# Create index
print("Creating index...")
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "params": {"nlist": 128},
}
collection.create_index(field_name="embedding", index_params=index_params)

# Search
print("\nSearching...")
collection.load()
results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=3,
)

print(f"Query: '{query}'\n")
for result in results[0]:
    print(f"[{result.distance:.3f}] {result.entity.get('text')}")

# Expected output:
# - Similar results to Qdrant
# - IVF_FLAT index enables fast approximate search
# - Cosine distance for similarity
```

### Exercise 3: ChromaDB Operations

```python
import chromadb

# Initialize ChromaDB
print("Initializing ChromaDB...")
# PersistentClient stores to disk. The old Settings(chroma_db_impl=
# "duckdb+parquet", persist_directory=...) keys were removed in
# Chroma 0.4 and raise on modern versions.
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Create collection
collection = chroma_client.create_collection(name="documents")

# Add documents
print("Adding documents...")
collection.add(
    documents=documents,
    embeddings=vectors,
    metadatas=[{"source": "wiki", "id": i} for i in range(len(documents))],
    ids=[f"doc_{i}" for i in range(len(documents))],
)

# Query
print("\nQuerying...")
results = collection.query(
    query_embeddings=[query_vector],
    n_results=3,
)

print(f"Query: '{query}'\n")
for i, (doc, score, metadata) in enumerate(zip(
    results["documents"][0],
    results["distances"][0],
    results["metadatas"][0]
), 1):
    print(f"{i}. [{score:.3f}] {doc}")
    print(f"   Metadata: {metadata}")

# Expected output:
# - Simple embedded vector database
# - Good for local development
# - Persistent storage to disk
```

### Exercise 4: Multi-Vector Collection

```python
from qdrant_client.models import (
    Distance, VectorParams, SparseVectorParams, SparseVector, PointStruct,
)
import hashlib

def toy_sparse(text, dim=10000):
    """Toy sparse encoding: hash words into a fixed-size space.

    Real pipelines use BM25/TF-IDF/SPLADE, but the API shape is the
    same: a SparseVector of unique indices and same-length values.
    """
    buckets = {}
    for word in text.lower().split():
        idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % dim
        buckets[idx] = buckets.get(idx, 0.0) + 1.0
    return SparseVector(indices=list(buckets), values=list(buckets.values()))

def create_multi_vector_collection(client):
    """Create collection with named dense and sparse vectors.

    Dense vectors live in vectors_config; sparse vectors need their
    own sparse_vectors_config with SparseVectorParams.
    """
    client.create_collection(
        collection_name="multi_vector_docs",
        vectors_config={
            "dense": VectorParams(size=384, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(),
        },
    )

    client.upsert(
        collection_name="multi_vector_docs",
        points=[
            PointStruct(
                id=i,
                vector={
                    "dense": embedder.encode([doc])[0].tolist(),
                    "sparse": toy_sparse(doc),
                },
                payload={"text": doc, "id": i},
            )
            for i, doc in enumerate(documents)
        ],
    )

# Create multi-vector collection
create_multi_vector_collection(client)

# A single query_points call targets one named vector via using=.
# Dense query: a plain vector. Sparse query: a dict of indices+values,
# e.g. query={"indices": [...], "values": [...]}, using="sparse".
def search_multi_vector(client, query_text):
    return client.query_points(
        collection_name="multi_vector_docs",
        query=embedder.encode([query_text])[0].tolist(),
        using="dense",
        limit=3,
        with_payload=["text"],
    ).points

# Test
results = search_multi_vector(client, "artificial intelligence")

print("\nMulti-vector search results:")
for result in results:
    print(f"[{result.score:.3f}] {result.payload['text']}")

# Expected output:
# - One collection serves dense and sparse embeddings side by side
# - query_points picks the vector space with using="dense"/"sparse"
# - Full dense+sparse hybrid runs both queries and fuses the ranks
```

### Exercise 5: Filtering with Metadata

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# Insert with metadata
client.upsert(
    collection_name="filtered_docs",
    points=[
        PointStruct(
            id=i,
            vector=vec.tolist(),
            payload={
                "text": doc,
                "category": "tech" if i % 2 == 0 else "general",
                "year": 2023 if i < 2 else 2024,
                "popularity": i * 10,
            },
        )
        for i, (vec, doc) in enumerate(zip(vectors, documents))
    ],
)

# Search with filter
print("Searching with category filter...")
results = client.query_points(
    collection_name="filtered_docs",
    query=query_vector,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value="tech"),
            )
        ]
    ),
    limit=3,
).points

print("Tech category results:")
for result in results:
    print(f"[{result.score:.3f}] {result.payload['text']} (category: {result.payload['category']})")

# Complex filter
print("\nSearching with year range filter...")
results = client.query_points(
    collection_name="filtered_docs",
    query=query_vector,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="year",
                range=Range(gte=2024),
            )
        ]
    ),
    limit=3,
).points

print("2024+ documents:")
for result in results:
    print(f"[{result.score:.3f}] {result.payload['text']} (year: {result.payload['year']})")

# Expected output:
# - Filters applied before vector search
# - Reduces search space efficiently
# - Combined semantic + metadata filtering
```

### Exercise 6: Hybrid Search (Vector + Keyword)

```python
def hybrid_search(client, collection_name, query_text, query_vector, alpha=0.7):
    """Combine vector search with keyword matching."""

    # Vector search
    vector_results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=10,
        with_payload=True,
    ).points

    # Keyword search (simplified - use full-text in production)
    keyword_results = client.scroll(
        collection_name=collection_name,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="text",
                    match=MatchValue(value=query_text),  # Simplified
                )
            ]
        ),
        limit=10,
        with_payload=True,
    )[0]

    # Combine and re-rank
    vector_scores = {r.id: r.score for r in vector_results}
    keyword_scores = {r.id: 0.5 for r in keyword_results}

    combined_scores = {}
    all_ids = set(vector_scores.keys()) | set(keyword_scores.keys())

    for doc_id in all_ids:
        vec_score = vector_scores.get(doc_id, 0)
        key_score = keyword_scores.get(doc_id, 0)
        combined_scores[doc_id] = alpha * vec_score + (1 - alpha) * key_score

    # Sort and return
    sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

    # Get full documents
    final_results = []
    for doc_id, score in sorted_results[:5]:
        point = client.retrieve(
            collection_name=collection_name,
            ids=[doc_id],
        )[0]
        final_results.append({
            "id": doc_id,
            "score": score,
            "text": point.payload["text"],
        })

    return final_results

# Test hybrid search
print("Hybrid search test...")
results = hybrid_search(client, "filtered_docs", "machine", query_vector, alpha=0.7)

print("\nHybrid search results:")
for result in results:
    print(f"[{result['score']:.3f}] {result['text']}")

# Expected output:
# - Combines semantic similarity with keyword matching
# - Alpha balances vector vs keyword
# - Better for exact phrase matches
```

### Exercise 7: Performance Optimization

```python
from qdrant_client.models import PayloadSchemaType

# Create optimized collection
print("Creating optimized collection...")
client.create_collection(
    collection_name="optimized_docs",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE,
        # Optimized HNSW parameters
        hnsw_config={
            "m": 16,  # Number of edges per node
            "ef_construct": 100,  # Index build speed vs accuracy
        },
    ),
    # Payload indexing for filtering: payload indexes are created with
    # separate create_payload_index calls (create_collection silently
    # ignores unknown kwargs like the old payload_schema= pattern).
)
for field, schema in [
    ("category", PayloadSchemaType.KEYWORD),
    ("year", PayloadSchemaType.INTEGER),
]:
    client.create_payload_index(
        collection_name="optimized_docs",
        field_name=field,
        field_schema=schema,
    )

# Batch upsert
def batch_upsert(client, collection_name, points, batch_size=100):
    """Upsert points in batches."""

    print(f"Upserting {len(points)} points in batches of {batch_size}...")

    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(
            collection_name=collection_name,
            points=batch,
        )
        print(f"  Batch {i//batch_size + 1} complete")

# Create large dataset for testing
import numpy as np
large_points = [
    PointStruct(
        id=i,
        vector=np.random.rand(384).tolist(),
        payload={
            "text": f"Document {i}",
            "category": ["tech", "science", "general"][i % 3],
            "year": 2023 + (i % 2),
        },
    )
    for i in range(1000)
]

# Batch insert
batch_upsert(client, "optimized_docs", large_points, batch_size=100)

# Benchmark search
import time

print("\nBenchmarking search performance...")
query_vector = np.random.rand(384).tolist()

start = time.time()
results = client.query_points(
    collection_name="optimized_docs",
    query=query_vector,
    limit=10,
).points
search_time = time.time() - start

print(f"Search time: {search_time*1000:.2f}ms")
print(f"Throughput: {len(results)/search_time:.0f} results/sec")

# Expected output:
# - Fast indexing with HNSW
# - Batch insert improves throughput
# - Single-digit ms search at this 1k-vector scale
# - Indexed payloads enable fast filtering
```
