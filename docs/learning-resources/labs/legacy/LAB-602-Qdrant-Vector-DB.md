# LAB-602: Qdrant Vector Database

## Overview
Set up and use Qdrant vector database for RAG systems.

## Prerequisites
- LAB-601 completed
- Docker installed

## Setup

```bash
# Start Qdrant
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant

# Install client
pip install qdrant-client sentence-transformers
```

## Exercise 1: Create Collection

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# TODO: Connect to Qdrant
client = QdrantClient(url="http://localhost:6333")

# TODO: Create collection
collection_name = "demo_docs"

client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=384,  # for all-MiniLM-L6-v2
        distance=Distance.COSINE
    )
)

print(f"Collection '{collection_name}' created")
```

## Exercise 2: Insert Documents

```python
from sentence_transformers import SentenceTransformer

# TODO: Load embedder
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# TODO: Prepare documents
documents = [
    {"id": 1, "text": "Paris is the capital of France.", "category": "geography"},
    {"id": 2, "text": "London is the capital of the United Kingdom.", "category": "geography"},
    {"id": 3, "text": "Python is a high-level programming language.", "category": "programming"},
    {"id": 4, "text": "Machine learning is a subset of AI.", "category": "ai"},
    {"id": 5, "text": "Neural networks learn from data.", "category": "ai"},
]

# TODO: Create points
points = []
for doc in documents:
    # Embed
    vector = embedder.encode(doc["text"]).tolist()

    # Create point
    point = PointStruct(
        id=doc["id"],
        vector=vector,
        payload={
            "text": doc["text"],
            "category": doc["category"]
        }
    )
    points.append(point)

# TODO: Insert points
client.upsert(
    collection_name=collection_name,
    points=points
)

print(f"Inserted {len(points)} points")
```

## Exercise 3: Search

```python
# TODO: Search function
def search(query, top_k=3, category_filter=None):
    """Search for similar documents."""

    # Embed query
    query_vector = embedder.encode(query).tolist()

    # Optional: Filter
    query_filter = None
    if category_filter:
        from qdrant_client.models import FieldCondition, MatchValue
        query_filter = FieldCondition(
            key="category",
            match=MatchValue(value=category_filter)
        )

    # Search
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=query_filter
    )

    return results

# TODO: Test search
query = "What is the capital?"
results = search(query, top_k=3)

print(f"Query: {query}")
print("Results:")
for result in results:
    print(f"  [{result.score:.3f}] {result.payload['text']}")
```

## Exercise 4: Hybrid Search

```python
# TODO: Hybrid search (vector + keyword)
from qdrant_client.models import SearchRequest

def hybrid_search(query, top_k=3):
    """Hybrid search combining vector and keyword."""

    # Vector search
    query_vector = embedder.encode(query).tolist()
    vector_results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k * 2
    )

    # TODO: Combine with text match (simplified)
    # In production, use full-text search index

    return vector_results

# Test
results = hybrid_search("capital city", top_k=3)
for result in results:
    print(f"[{result.score:.3f}] {result.payload['text']}")
```

## Exercise 5: Update and Delete

```python
# TODO: Update point
updated_text = "Paris is the beautiful capital of France."
updated_vector = embedder.encode(updated_text).tolist()

client.upsert(
    collection_name=collection_name,
    points=[
        PointStruct(
            id=1,
            vector=updated_vector,
            payload={"text": updated_text, "category": "geography"}
        )
    ]
)

# TODO: Delete point
client.delete(
    collection_name=collection_name,
    points_selector=[5]  # Delete document 5
)

# Verify
results = search("neural networks")
print(f"After delete: {len(results)} results")
```

## Exercise 6: Bulk Operations

```python
# TODO: Bulk insert
def insert_batch(texts):
    """Insert multiple documents efficiently."""

    points = []
    for i, text in enumerate(texts):
        vector = embedder.encode(text).tolist()

        point = PointStruct(
            id=100 + i,  # Start from ID 100
            vector=vector,
            payload={"text": text}
        )
        points.append(point)

    client.upsert(
        collection_name=collection_name,
        points=points
    )

# Test
batch_docs = [
    "Tokyo is the capital of Japan.",
    "Canberra is the capital of Australia.",
    "Ottawa is the capital of Canada.",
]

insert_batch(batch_docs)
print("Batch insert complete")
```

## Exercise 7: Advanced Filtering

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# TODO: Complex filter
def search_with_filters(query, category=None, min_score=0.5):
    """Search with multiple filters."""

    query_vector = embedder.encode(query).tolist()

    # Build filter
    conditions = []

    if category:
        conditions.append(
            FieldCondition(
                key="category",
                match=MatchValue(value=category)
            )
        )

    # Search with score threshold (post-filter)
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=10,
        query_filter=Filter(must=conditions) if conditions else None
    )

    # Filter by score
    filtered = [r for r in results if r.score >= min_score]

    return filtered

# Test
results = search_with_filters("capital", category="geography", min_score=0.7)
print(f"Filtered results: {len(results)}")
for result in results:
    print(f"  [{result.score:.3f}] {result.payload['text']}")
```

## Expected Outputs

1. Exercise 1: Collection created
2. Exercise 2: 5 documents inserted
3. Exercise 3: Search returns relevant results
4. Exercise 4: Hybrid search working
5. Exercise 5: Update/delete working
6. Exercise 6: Batch insert working
7. Exercise 7: Advanced filtering working

## Troubleshooting

**Issue:** Connection refused
```bash
# Solution: Ensure Qdrant is running
docker ps | grep qdrant
```

**Issue:** Wrong dimension
```python
# Solution: Match embedding dimension to model size
embedder = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dims
```

## Time Estimate: 2-3 hours

---
