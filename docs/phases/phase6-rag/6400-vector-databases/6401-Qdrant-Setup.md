---
Document ID: 6401
Title: Qdrant Setup Guide
Phase: 6
Module: 6400
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'vector-db', 'qdrant', 'pinecone', 'weaviate']
---

# 6401: Qdrant Setup Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Docker Deployment](#docker-deployment)
- [Python Client](#python-client)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Configure and operate Docker Deployment
- Explain Python Client

---

## Abstract
Qdrant is a vector database engine optimized for high-performance approximate nearest neighbor search. This guide covers deployment on any Docker-capable Linux host.

## Docker Deployment

### Installation
```bash
# Create directory
mkdir -p /srv/qdrant
cd /srv/qdrant

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3"

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - 6333:6333  # gRPC
      - 6334:6334  # HTTP
    volumes:
      - ./data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6333
      - QDRANT__SERVICE__HTTP_PORT=6334
    restart: unless-stopped
EOF

# Start Qdrant
docker-compose up -d
```

## Python Client

### Basic Operations
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect
client = QdrantClient(url="http://192.168.1.100:6333")

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
            vector=[0.1, 0.2, 0.3, ...],  # 384-dim vector
            payload={"title": "Doc 1", "text": "..."}
        )
    ]
)

# Search
results = client.search(
    collection_name="documents",
    query_vector=[0.1, 0.2, 0.3, ...],
    limit=10
)
```


---

## References

### Related ai-engineering-curriculum Documents

- [6402: Vector Database Comparison](6402-Pinecone-vs-Weaviate.md)

---

## Next Steps

- Continue with: **[6402: Pinecone vs Weaviate](./6402-Pinecone-vs-Weaviate.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related:**
- [6101: HNSW](../6100-Vector/6101-HNSW-Indexing.md)
- [6201: Hybrid Search](../6200-retrieval/6201-Hybrid-Search.md)
