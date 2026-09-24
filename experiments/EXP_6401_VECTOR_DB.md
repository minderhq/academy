# EXP_6401: Vector Database Performance Experiments

## Overview
Practical experiments for comparing vector database performance on PROJECT-OMEGA infrastructure (Synology NAS + K3s cluster).

## Experiment 1: Qdrant Deployment and Baseline

### Objective
Deploy Qdrant on Synology NAS and establish baseline performance metrics.

### Deployment
```bash
# SSH into Synology
ssh admin@192.168.1.100

# Create project directory
mkdir -p /volume1/docker/qdrant
cd /volume1/docker/qdrant

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3"

services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: qdrant
    ports:
      - 6333:6333  # gRPC
      - 6334:6334  # HTTP
    volumes:
      - ./data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6333
      - QDRANT__SERVICE__HTTP_PORT=6334
      - QDRANT__STORAGE__OPTIMIZER_CPU_BUDGET=4
    restart: unless-stopped
EOF

# Start Qdrant
docker-compose up -d

# Verify
curl http://192.168.1.100:6334/health
```

### Python Test Script
```python
# qdrant_benchmark.py
import time
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Configuration
QDRANT_URL = "http://192.168.1.100:6334"
COLLECTION_NAME = "test_benchmark"
VECTOR_DIM = 384  # E5-small embedding dimension
N_VECTORS = 100_000

client = QdrantClient(url=QDRANT_URL)

def create_collection():
    """Create Qdrant collection"""
    client.delete_collection(COLLECTION_NAME)  # Clear if exists

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_DIM,
            distance=Distance.COSINE,
            hnsw_config={
                "m": 16,           # HNSW max connections
                "ef_construct": 100,  # HNSW build accuracy
            }
        )
    )
    print(f"Collection '{COLLECTION_NAME}' created")

def insert_vectors(n=N_VECTORS, batch_size=1000):
    """Insert vectors and measure throughput"""
    print(f"\nInserting {n} vectors (batch_size={batch_size})...")

    start = time.time()
    inserted = 0

    while inserted < n:
        batch_n = min(batch_size, n - inserted)

        # Generate random vectors (normalized for cosine)
        vectors = np.random.randn(batch_n, VECTOR_DIM).astype(np.float32)
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

        # Create points
        points = [
            PointStruct(
                id=inserted + i,
                vector=vectors[i].tolist(),
                payload={"text": f"Document {inserted + i}"}
            )
            for i in range(batch_n)
        ]

        # Insert
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        inserted += batch_n
        if inserted % 10000 == 0:
            print(f"  {inserted}/{n} vectors inserted")

    elapsed = time.time() - start
    throughput = n / elapsed

    print(f"  Inserted {n} vectors in {elapsed:.2f}s")
    print(f"  Throughput: {throughput:.0f} vectors/sec")
    print(f"  Collection size: {client.count(COLLECTION_NAME)}")

    return throughput

def search_performance(k=10, n_queries=100):
    """Test search performance"""
    print(f"\nTesting search (k={k}, queries={n_queries})...")

    # Generate query vectors
    queries = np.random.randn(n_queries, VECTOR_DIM).astype(np.float32)
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)

    # Warmup
    client.search(
        collection_name=COLLECTION_NAME,
        query_vector=queries[0].tolist(),
        limit=k
    )

    # Benchmark
    start = time.time()

    for query in queries:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query.tolist(),
            limit=k,
            score_threshold=0.7
        )

    elapsed = time.time() - start
    qps = n_queries / elapsed

    print(f"  Completed {n_queries} queries in {elapsed:.2f}s")
    print(f"  Query throughput: {qps:.1f} queries/sec")
    print(f"  Avg latency: {(elapsed/n_queries)*1000:.2f}ms")

    return qps

def filter_performance():
    """Test filtered search performance"""
    print("\nTesting filtered search...")

    # Search with metadata filter
    start = time.time()

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=np.random.randn(VECTOR_DIM).tolist(),
        query_filter={
            "must": [
                {"key": "text", "match": {"value": "Document 50"}}
            ]
        },
        limit=10
    )

    elapsed = (time.time() - start) * 1000
    print(f"  Filtered search: {elapsed:.2f}ms")

if __name__ == "__main__":
    create_collection()
    insert_speed = insert_vectors()
    search_speed = search_performance()
    filter_performance()
```

---

## Experiment 2: Vector Database Comparison

### Objective
Compare Qdrant, Weaviate, and Chroma on the same hardware.

### Unified Test Framework
```python
# vector_db_comparison.py
import time
import numpy as np
from typing import List, Dict

class VectorDBBenchmark:
    """Unified benchmark for vector databases"""

    def __init__(self, vector_dim=384, n_vectors=10_000):
        self.vector_dim = vector_dim
        self.n_vectors = n_vectors
        self.vectors = self._generate_vectors()
        self.queries = self._generate_vectors(100)

    def _generate_vectors(self, n=None):
        """Generate normalized random vectors"""
        n = n or self.n_vectors
        vectors = np.random.randn(n, self.vector_dim).astype(np.float32)
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors

    def benchmark_qdrant(self):
        """Benchmark Qdrant"""
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance, PointStruct

        client = QdrantClient(url="http://192.168.1.100:6334")
        collection = "benchmark_qdrant"

        # Setup
        client.delete_collection(collection)
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE)
        )

        # Insert benchmark
        start = time.time()
        for i in range(0, self.n_vectors, 1000):
            batch = self.vectors[i:i+1000]
            points = [
                PointStruct(id=i+j, vector=batch[j].tolist())
                for j in range(len(batch))
            ]
            client.upsert(collection, points)
        insert_time = time.time() - start

        # Search benchmark
        start = time.time()
        for query in self.queries:
            client.search(collection, query_vector=query.tolist(), limit=10)
        search_time = time.time() - start

        client.delete_collection(collection)

        return {
            "insert_time": insert_time,
            "insert_throughput": self.n_vectors / insert_time,
            "search_qps": len(self.queries) / search_time,
        }

    def benchmark_weaviate(self):
        """Benchmark Weaviate"""
        import weaviate

        client = weaviate.Client("http://192.168.1.100:8080")

        # Setup (skip if Weaviate not deployed)
        try:
            client.schema.delete_class("Benchmark")
        except:
            pass

        client.schema.create_class({
            "class": "Benchmark",
            "vectorizer": "none",
            "properties": [{"name": "text", "dataType": ["string"]}]
        })

        # Insert benchmark
        start = time.time()
        with client.batch() as batch:
            for i, vector in enumerate(self.vectors):
                batch.add_data_object(
                    data_object={"text": f"doc_{i}"},
                    class_name="Benchmark",
                    vector=vector.tolist()
                )
        insert_time = time.time() - start

        # Search benchmark
        start = time.time()
        for query in self.queries:
            client.query.get(
                "Benchmark", ["text"]
            ).with_near_vector({
                "vector": query.tolist(),
                "certainty": 0.7
            }).with_limit(10).do()
        search_time = time.time() - start

        return {
            "insert_time": insert_time,
            "insert_throughput": self.n_vectors / insert_time,
            "search_qps": len(self.queries) / search_time,
        }

    def benchmark_chroma(self):
        """Benchmark Chroma"""
        import chromadb

        client = chromadb.PersistentClient(path="./chroma_data")
        collection = client.get_or_create_collection("benchmark")

        # Insert benchmark
        start = time.time()
        collection.add(
            embeddings=self.vectors.tolist(),
            ids=[f"doc_{i}" for i in range(self.n_vectors)]
        )
        insert_time = time.time() - start

        # Search benchmark
        start = time.time()
        for query in self.queries:
            collection.query(
                query_embeddings=query.tolist(),
                n_results=10
            )
        search_time = time.time() - start

        client.delete_collection("benchmark")

        return {
            "insert_time": insert_time,
            "insert_throughput": self.n_vectors / insert_time,
            "search_qps": len(self.queries) / search_time,
        }

    def run_all(self):
        """Run all benchmarks"""
        print(f"\n{'='*60}")
        print(f"Vector DB Comparison (n={self.n_vectors}, dim={self.vector_dim})")
        print(f"{'='*60}\n")

        results = {}

        # Qdrant
        try:
            print("Testing Qdrant...")
            results["Qdrant"] = self.benchmark_qdrant()
            print(f"  Insert: {results['Qdrant']['insert_throughput']:.0f} vec/s")
            print(f"  Search: {results['Qdrant']['search_qps']:.1f} QPS")
        except Exception as e:
            print(f"  Qdrant error: {e}")

        # Weaviate
        try:
            print("\nTesting Weaviate...")
            results["Weaviate"] = self.benchmark_weaviate()
            print(f"  Insert: {results['Weaviate']['insert_throughput']:.0f} vec/s")
            print(f"  Search: {results['Weaviate']['search_qps']:.1f} QPS")
        except Exception as e:
            print(f"  Weaviate error: {e}")

        # Chroma
        try:
            print("\nTesting Chroma...")
            results["Chroma"] = self.benchmark_chroma()
            print(f"  Insert: {results['Chroma']['insert_throughput']:.0f} vec/s")
            print(f"  Search: {results['Chroma']['search_qps']:.1f} QPS")
        except Exception as e:
            print(f"  Chroma error: {e}")

        # Summary table
        print(f"\n{'='*60}")
        print("RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"{'DB':<12} | {'Insert (vec/s)':<15} | {'Search (QPS)':<12}")
        print(f"{'-'*60}")
        for db, metrics in results.items():
            print(f"{db:<12} | {metrics['insert_throughput']:<15.0f} | {metrics['search_qps']:<12.1f}")

if __name__ == "__main__":
    # Run benchmarks
    benchmark = VectorDBBenchmark(vector_dim=384, n_vectors=50_000)
    benchmark.run_all()
```

---

## Experiment 3: Embedding Model Comparison

### Objective
Compare embedding quality and speed for different models.

### Models to Test
| Model | Dim | Size | Speed |
|-------|-----|------|-------|
| E5-small | 384 | 133MB | Fastest |
| E5-base | 768 | 420MB | Fast |
| E5-large | 1024 | 1.3GB | Medium |
| bge-small | 384 | 130MB | Fastest |
| bge-base | 768 | 420MB | Fast |

### Test Script
```python
# embedding_comparison.py
import time
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

models_to_test = [
    "intfloat/multilingual-e5-small",
    "intfloat/multilingual-e5-base",
    "BAAI/bge-small-en-v1.5",
    "BAAI/bge-base-en-v1.5",
]

test_documents = [
    "Artificial intelligence is transforming healthcare.",
    "Machine learning helps doctors diagnose diseases.",
    "The quick brown fox jumps over the lazy dog.",
    "Weather today is sunny with a chance of rain.",
]

def benchmark_embeddings():
    """Compare embedding models"""
    results = []

    for model_name in models_to_test:
        print(f"\nTesting {model_name.split('/')[-1]}...")

        # Load model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer(model_name, device=device)

        # Encode
        start = time.time()
        embeddings = model.encode(test_documents, batch_size=32)
        encode_time = time.time() - start

        # Similarity
        similarities = cosine_similarity(embeddings)

        # Stats
        dim = embeddings.shape[1]
        docs_per_sec = len(test_documents) / encode_time

        print(f"  Dimension: {dim}")
        print(f"  Speed: {docs_per_sec:.1f} docs/sec")
        print(f"  VRAM: {torch.cuda.max_memory_allocated()/1024**3:.2f} GB")

        results.append({
            "model": model_name.split('/')[-1],
            "dim": dim,
            "docs_per_sec": docs_per_sec,
            "vram_gb": torch.cuda.max_memory_allocated()/1024**3,
        })

        torch.cuda.empty_cache()

    return results

if __name__ == "__main__":
    benchmark_embeddings()
```

---

## Experiment 4: HNSW Parameter Tuning

### Objective
Find optimal HNSW parameters for Qdrant on your dataset.

### Parameters to Tune
- `m`: Max connections per node (default: 16)
- `ef_construct`: Build accuracy (default: 100)
- `ef`: Search accuracy (default: None, uses k)

### Test Script
```python
# hnsw_tuning.py
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff
import numpy as np
import time

def test_hnsw_params(m_values=[8, 16, 24, 32], ef_values=[50, 100, 200]):
    """Test HNSW parameter combinations"""
    client = QdrantClient(url="http://192.168.1.100:6334")

    # Generate test data
    n_vectors = 10_000
    dim = 384
    vectors = np.random.randn(n_vectors, dim).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

    results = []

    for m in m_values:
        for ef in ef_values:
            collection = f"test_m{m}_ef{ef}"

            # Create collection
            client.delete_collection(collection)
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
                hnsw_config=HnswConfigDiff(
                    m=m,
                    ef_construct=ef,
                )
            )

            # Insert
            start = time.time()
            for i in range(0, n_vectors, 1000):
                batch = vectors[i:i+1000]
                points = [
                    PointStruct(id=i+j, vector=batch[j].tolist())
                    for j in range(len(batch))
                ]
                client.upsert(collection, points)
            insert_time = time.time() - start

            # Search
            start = time.time()
            for i in range(100):
                client.search(
                    collection,
                    query_vector=vectors[i].tolist(),
                    limit=10
                )
            search_time = time.time() - start

            results.append({
                "m": m,
                "ef": ef,
                "insert_time": insert_time,
                "search_qps": 100 / search_time,
            })

            print(f"m={m:2d}, ef={ef:3d} | Insert: {insert_time:.2f}s | Search: {100/search_time:.1f} QPS")
            client.delete_collection(collection)

    return results
```

---

## Expected Performance (entry-level NAS)

| Operation | Expected | Notes |
|-----------|----------|-------|
| Qdrant Insert | ~5,000-10,000 vec/s | Depends on batch size |
| Qdrant Search | ~100-500 QPS | With 100K vectors |
| Weaviate Insert | ~2,000-5,000 vec/s | Slower than Qdrant |
| Weaviate Search | ~50-200 QPS | Depends on RAM |
| Chroma Insert | ~1,000-3,000 vec/s | Python overhead |
| Chroma Search | ~20-100 QPS | Not optimized |

---

## Experiment Checklist

- [ ] Qdrant deployment on Synology NAS
- [ ] Baseline insert performance (100K vectors)
- [ ] Baseline search performance (100 queries)
- [ ] Weaviate deployment (optional)
- [ ] Chroma local test
- [ ] Embedding model comparison (E5 vs BGE)
- [ ] HNSW parameter tuning
- [ ] Scale test (1M vectors if storage allows)
- [ ] Filter performance comparison
- [ ] Hybrid search test (BM25 + vector)

---

## Related Documentation
- [6401: Qdrant Setup](../docs/6000-Data-Nexus/6400-Vector-Databases/6401-Qdrant-Setup.md)
- [6402: Vector DB Comparison](../docs/6000-Data-Nexus/6400-Vector-Databases/6402-Pinecone-vs-Weaviate.md)
- [6101: HNSW Indexing](../docs/6000-Data-Nexus/6100-Vector-Search/6101-HNSW-Indexing.md)
- [6201: Hybrid Search](../docs/6000-Data-Nexus/6200-RAG/6201-Hybrid-Search.md)
