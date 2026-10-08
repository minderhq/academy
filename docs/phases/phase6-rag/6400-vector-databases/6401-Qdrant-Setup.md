---
Document ID: 6401
Title: "6401: Qdrant Setup Guide"
Phase: 6
Module: 6400
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'vector-db', 'qdrant', 'docker', 'deployment']
---

# 6401: Qdrant Setup Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Why Qdrant](#why-qdrant)
- [Docker Deployment](#docker-deployment)
- [Verifying the Deployment](#verifying-the-deployment)
- [Python Client](#python-client)
- [Production Configuration](#production-configuration)
- [Snapshots and Backup](#snapshots-and-backup)
- [Troubleshooting](#troubleshooting)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Deploy Qdrant with Docker Compose including health checks and persistent storage
- Verify a deployment through the REST health endpoints and the built-in dashboard
- Create collections, upsert points, and run filtered similarity search with the modern `qdrant-client` API
- Configure HNSW parameters and scalar quantization for production workloads
- Take, list, and restore collection snapshots for backup workflows
- Diagnose the common failure modes of a self-hosted Qdrant instance

---

## Abstract

Qdrant is an open-source vector database written in Rust, optimized for high-performance approximate nearest neighbor (ANN) search with payload filtering. This guide covers deploying it on any Docker-capable Linux host, verifying the deployment, and performing core operations (collection management, upsert, filtered search) with the current Python client API. It closes with production-oriented configuration — HNSW tuning, quantization, snapshots — and a troubleshooting table for the failures you will actually hit.

## Why Qdrant

```text
Positioning among self-hosted vector stores

- Rust core: predictable latency, low GC-jitter under load
- HNSW index with payload-filter-aware traversal
  (filtered search degrades gracefully, not cliff-edge)
- Native quantization (scalar int8, binary) and on-disk vectors
- Simple ops story: single container, snapshots via REST
- gRPC + REST on separate ports; OpenAPI at :6333/docs
```

Qdrant is the default recommendation in this curriculum when you want a **self-hosted, single-binary** vector store with production features. For a managed-service comparison, see [6402: Pinecone vs Weaviate](./6402-Pinecone-vs-Weaviate.md). For the index math behind it, see [6101: HNSW Indexing](../6100-vector/6101-HNSW-Indexing.md).

## Docker Deployment

### docker-compose.yml

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"   # HTTP / REST (dashboard, OpenAPI, snapshots)
      - "6334:6334"   # gRPC (preferred by clients for throughput)
    volumes:
      - ./data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "bash -c ':> /dev/tcp/127.0.0.1/6333' || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3
```

```bash
mkdir -p /srv/qdrant && cd /srv/qdrant
# save the compose file above as docker-compose.yml
docker compose up -d
```

Port facts worth memorizing — they are the #1 source of setup confusion:

```text
6333 = HTTP / REST  (curl, dashboard, OpenAPI docs at :6333/docs)
6334 = gRPC         (qdrant-client uses this when grpc extra installed)
```

### Pinning and Resource Limits

`latest` is fine for a homelab; production images should be pinned:

```yaml
    image: qdrant/qdrant:v1.12.4
    deploy:
      resources:
        limits:
          memory: 8g
```

Rule of thumb for memory sizing: vectors resident in RAM need roughly `n_vectors × dim × 4 bytes` (float32) plus ~20% HNSW graph overhead. For 5M vectors at 384 dims that is ~9 GB; enable quantization (below) to cut this 4×.

## Verifying the Deployment

```bash
# 1. Liveness
curl -s http://localhost:6333/healthz
# -> healthz check passed

# 2. Version + telemetry root
curl -s http://localhost:6333/ | jq .

# 3. Dashboard (browser): collection browser, point inspector,
#    and a query playground — excellent for debugging payloads
#    http://localhost:6333/dashboard
```

If `healthz` responds but a client cannot connect, you are almost certainly hitting the gRPC port with an HTTP call (or vice versa) — see [Troubleshooting](#troubleshooting).

## Python Client

### Installation and Connection

```bash
uv pip install "qdrant-client[fastembed]"   # fastembed extra pulls gRPC + local encoders
```

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(
    url="http://192.168.1.100:6333",
    timeout=30,
    # api_key="...",          # only if QDRANT__SERVICE__API_KEY is set server-side
    prefer_grpc=True,          # REST fallback is automatic
)
```

### Creating a Collection

```python
client.create_collection(
    collection_name="documents",
    vectors_config=models.VectorParams(
        size=384,                    # MUST match your embedding model's output dim
        distance=models.Distance.COSINE,
        on_disk=False,               # True for collections larger than RAM
    ),
)
```

The three distance choices and when they apply:

```text
COSINE   default for sentence-transformer / OpenAI-style embeddings
         (vectors are normalized internally)
DOT      embeddings already normalized at generation time (saves a normalization)
EUCLID   image embeddings and spatial workloads
```

### Upserting Points

```python
import uuid

points = [
    models.PointStruct(
        id=str(uuid.uuid4()),               # or a deterministic int hash
        vector=embedding_384d,
        payload={
            "title": doc.title,
            "text": doc.text,
            "source": doc.source,
            "chunk_index": doc.chunk_index,
        },
    )
    for doc in chunked_docs
]

client.upsert(collection_name="documents", points=points, wait=True)
```

`wait=True` forces the write to be acknowledged by storage before returning — use it in tests and pipelines, drop it in high-throughput importers that can tolerate eventual consistency.

Batched import for large backfills:

```python
client.upsert(
    collection_name="documents",
    points=models.Batch(
        ids=[...],
        vectors=[...],
        payloads=[...],
    ),
)
```

### Search (Modern API)

The legacy `client.search(...)` method is deprecated. Use `query_points`:

```python
result = client.query_points(
    collection_name="documents",
    query=query_embedding_384d,
    limit=10,
    with_payload=True,
)

for hit in result.points:
    print(hit.score, hit.payload["title"])
```

### Filtered Search

Payload filters compose with vector similarity — Qdrant traverses the HNSW graph while respecting the filter, which is exactly the capability that degrades badly in naive "search then filter" setups:

```python
result = client.query_points(
    collection_name="documents",
    query=query_embedding,
    limit=10,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(key="source", match=models.MatchValue(value="handbook")),
            models.FieldCondition(key="chunk_index", range=models.Range(gte=0, lte=50)),
        ],
        must_not=[
            models.FieldCondition(key="title", match=models.MatchText(text="deprecated")),
        ],
    ),
)
```

## Production Configuration

### HNSW Tuning and Quantization

Create collections with explicit index and quantization settings once scale warrants it:

```python
client.create_collection(
    collection_name="documents_prod",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    hnsw_config=models.HnswConfigDiff(
        m=16,              # edges per node; 16 default, 32 = higher recall + RAM
        ef_construct=100,  # build-time search width; quality knob
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True,   # keep quantized vectors hot, originals on disk
        )
    ),
    on_disk_payload=True,
)
```

```text
Recall knobs, in query order of impact
1. hnsw_ef (query-time)    start 128; raise until recall target met
2. m / ef_construct        rebuild-time; raise only if (1) cannot reach target
3. exact=true              brute force; correctness baseline + small collections
```

Benchmark before tuning: create the same collection twice, one `exact=true`, measure recall@10 of the ANN config against it. Tuning without a recall baseline is guesswork.

### API Key and TLS

```yaml
    environment:
      - QDRANT__SERVICE__API_KEY=change-me-long-random
```

Qdrant serves plain HTTP; terminate TLS at your reverse proxy (nginx/Caddy/Traefik) rather than exposing 6333 directly. Put the instance on an internal network and expose only through the proxy.

## Snapshots and Backup

```bash
# Create a snapshot of one collection
curl -X POST http://localhost:6333/collections/documents/snapshots

# List snapshots
curl http://localhost:6333/collections/documents/snapshots | jq .

# Download it (this is your backup artifact)
curl -o docs.snap \
  http://localhost:6333/collections/documents/snapshots/${NAME}
```

Restore on a new host: mount the snapshot directory, then `PUT /collections/{name}/snapshots/upload?priority=snapshot`. Schedule snapshot creation with cron and ship the files off-host — the local `./data` volume alone is not a backup strategy.

## Troubleshooting

```text
Symptom                              Cause and fix
------------------------------------+---------------------------------------------
Connection refused on 6334           gRPC hit with HTTP client or proxy. Use 6333
                                     for REST; ensure prefer_grpc only with the
                                     grpc extra installed.

"Vector dimension error" on upsert   Embedding dim != collection size. Recreate
                                     the collection or re-embed; dims are fixed
                                     at creation.

Search returns irrelevant results    Distance metric mismatch with the embedding
                                     model (e.g. EUCLID with cosine-trained
                                     model). Check the model card.

Slow queries after large imports     HNSW still building. Check /metrics and wait,
                                     or raise build parallelism. Verify with
                                     collection info: optimizer_status.

Container OOM-killed                 RAM budget exceeded (see sizing rule above).
                                     Enable scalar quantization, set on_disk=True,
                                     raise the memory limit.

Data lost after restart              Volume not mounted; ./data recreated empty.
                                     Check `docker inspect` Mounts section.
```

---

## Summary

Qdrant is the open-source vector database this curriculum standardizes on: Rust-native ANN search with payload filtering, deployable as a single container on any Docker-capable Linux host. This lesson walked deployment, health verification, and the core operations - collection management, upsert, and filtered search - against the current REST API. The rule it leaves: a vector database is only useful when its filters are - payload filtering is what turns similarity search into production search.

## References

### Related Minder Academy Documents

- [6402: Vector Database Comparison](6402-Pinecone-vs-Weaviate.md)

---

## Next Steps

- Continue with: **[6402: Pinecone vs Weaviate](./6402-Pinecone-vs-Weaviate.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**

- [6101: HNSW](../6100-vector/6101-HNSW-Indexing.md)
- [6201: Hybrid Search](../6200-retrieval/6201-Hybrid-Search.md)
