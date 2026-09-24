---
Document ID: 6103
Title: "6103: HNSW Parameter Tuning Guide"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# 6103: HNSW Parameter Tuning Guide

## Abstract
Comprehensive guide for tuning HNSW (Hierarchical Navigable Small World) index parameters for optimal vector search performance on AI Engineering Curriculum infrastructure.

## HNSW Architecture

### Understanding the Structure

```text
Layer 2:  ┌─────┐         ┌─────┐         ┌─────┐
           │  1  │────────▶│  5  │────────▶│  9  │
           └─────┘         └─────┘         └─────┘
              │               │               │
Layer 1:  ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
           │  1  │──▶│  3  │   │  5  │──▶│  7  │
           └─────┘   └─────┘   └─────┘   └─────┘
              │         │  │  │         │
Layer 0:  ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
           │  1  │──▶│  2  │   │  5  │──▶│  6  │
           │     ├──▶│  3  │   │     ├──▶│  7  │
           │     │   └─────┘   │     │   └─────┘
           └─────┘             └─────┘
```

### Key Parameters

| Parameter | Symbol | Description | Default | Range |
|-----------|--------|-------------|---------|-------|
| M | M | Max connections per node | 16 | 2-100 |
| ef_construction | efConstruction | Index build accuracy | 100 | 40-400 |
| ef_search | ef | Search accuracy | 100 | 10-200 |

## Parameter Deep Dive

### M (Max Connections)

**Purpose:** Controls graph density in HNSW layers

**Trade-offs:**
```text
Low M (2-8):
  ✓ Faster index build
  ✓ Less memory
  ✗ Lower recall
  ✗ More layers needed

High M (16-64):
  ✓ Higher recall
  ✓ Fewer layers
  ✗ Slower index build
  ✗ More memory
```

**Recommendation:**
```python
# For small datasets (<100K vectors)
M = 16

# For medium datasets (100K-1M vectors)
M = 32

# For large datasets (>1M vectors)
M = 64
```

### ef_construction

**Purpose:** Controls quality/accuracy during index building

**Impact:**
```text
Low ef (40-100):
  ✓ Fast indexing
  ✗ Lower search accuracy

High ef (200-400):
  ✓ Better search accuracy
  ✗ Slower indexing (2-4x)
```

**Recommendation:**
```python
# For quick prototyping
ef_construction = 100

# For production
ef_construction = 200

# For highest quality
ef_construction = 400
```

### ef_search

**Purpose:** Controls search quality at query time

**Impact:**
```text
Low ef (10-50):
  ✓ Fast search
  ✗ Lower recall

High ef (100-200):
  ✓ Higher recall
  ✗ Slower search (linear)
```

**Recommendation:**
```python
# For approximate search (fast)
ef_search = 50

# For balanced search
ef_search = 100

# For exact search (slow)
ef_search = 200
```

## Tuning Strategy

### Step 1: Benchmark Baseline

```python
# hnsw_benchmark.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, HnswConfigDiff
import numpy as np
import time

def benchmark_hnsw_params():
    """Benchmark different HNSW configurations"""

    # Test data
    n_vectors = 100_000
    dim = 384

    # Generate random vectors
    vectors = np.random.randn(n_vectors, dim).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

    # Test configurations
    configs = [
        {"m": 16, "ef": 100, "ef_construction": 100},
        {"m": 16, "ef": 100, "ef_construction": 200},
        {"m": 32, "ef": 100, "ef_construction": 100},
        {"m": 32, "ef": 200, "ef_construction": 200},
        {"m": 64, "ef": 200, "ef_construction": 200},
    ]

    results = []

    for config in configs:
        print(f"\nTesting: M={config['m']}, ef={config['ef']}, ef_construction={config['ef_construction']}")

        client = QdrantClient(url="http://192.168.1.100:6334")
        collection = f"test_m{config['m']}_ef{config['ef']}"

        # Create collection
        try:
            client.delete_collection(collection)
        except:
            pass

        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(
                size=dim,
                distance=Distance.COSINE,
                hnsw_config=HnswConfigDiff(
                    m=config["m"],
                    ef_construct=config["ef_construction"],
                )
            )
        )

        # Insert vectors (measure indexing speed)
        start = time.time()

        for i in range(0, n_vectors, 1000):
            batch = vectors[i:i+1000]
            points = [
                PointStruct(
                    id=i+j,
                    vector=batch[j].tolist(),
                    payload={"text": f"doc_{i+j}"}
                )
                for j in range(len(batch))
            ]
            client.upsert(collection, points)

        index_time = time.time() - start

        # Search speed test
        n_queries = 100
        query_vectors = np.random.randn(n_queries, dim).astype(np.float32)
        query_vectors /= np.linalg.norm(query_vectors, axis=1, keepdims=True)

        start = time.time()
        for query in query_vectors:
            client.search(
                collection,
                query_vector=query.tolist(),
                limit=10,
                hnsw_ef=config["ef"]
            )
        search_time = time.time() - start

        results.append({
            "config": config,
            "index_time": index_time,
            "search_qps": n_queries / search_time,
            "index_throughput": n_vectors / index_time,
        })

        print(f"  Index: {index_time:.2f}s ({n_vectors/index_time:.0f} vec/s)")
        print(f"  Search: {search_time:.2f}s ({n_queries/search_time:.1f} QPS)")

        client.delete_collection(collection)

    return results


if __name__ == "__main__":
    benchmark_hnsw_params()
```

### Step 2: Recall vs Speed Analysis

```python
# recall_analysis.py
def calculate_recall(search_results, ground_truth, k):
    """Calculate recall@k"""
    retrieved_ids = set(r.id for r in search_results[:k])
    relevant_ids = set(ground_truth)
    return len(retrieved_ids & relevant_ids) / len(relevant_ids)

def analyze_recall_vs_speed():
    """Analyze recall-speed tradeoff"""

    ef_values = [10, 20, 50, 100, 150, 200]

    results = {}

    for ef in ef_values:
        # Search with different ef
        search_results = client.search(
            collection,
            query_vector=query,
            limit=100,
            hnsw_ef=ef
        )

        recall = calculate_recall(search_results, ground_truth, k=10)

        results[ef] = {
            "recall": recall,
            "time": measure_search_time(ef)
        }

    # Plot
    import matplotlib.pyplot as plt

    ef_list = list(results.keys())
    recalls = [results[e]["recall"] for e in ef_list]
    times = [results[e]["time"] for e in ef_list]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(ef_list, recalls, 'o-', linewidth=2)
    ax1.set_xlabel('ef_search')
    ax1.set_ylabel('Recall@10')
    ax1.set_title('Recall vs ef_search')
    ax1.grid(True, alpha=0.3)

    ax2.plot(ef_list, times, 's-', color='orange', linewidth=2)
    ax2.set_xlabel('ef_search')
    ax2.set_ylabel('Search Time (ms)')
    ax2.set_title('Speed vs ef_search')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/workspace/hnsw_ef_analysis.png', dpi=150)


if __name__ == "__main__":
    analyze_recall_vs_speed()
```

## Production Configurations

### Qdrant HNSW Config

```python
from qdrant_client.models import HnswConfigDiff

# Small dataset (<100K vectors)
hnsw_config_small = HnswConfigDiff(
    m=16,
    ef_construct=100,
)

# Medium dataset (100K-1M vectors)
hnsw_config_medium = HnswConfigDiff(
    m=32,
    ef_construct=200,
    full_scan_threshold=10000,
)

# Large dataset (>1M vectors)
hnsw_config_large = HnswConfigDiff(
    m=64,
    ef_construct=200,
    full_scan_threshold=20000,
)

# Create collection with HNSW config
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE,
        hnsw_config=hnsw_config_medium
    )
)
```

## Optimal Settings by Use Case

### Real-time Search (Low Latency)

```python
hnsw_config = HnswConfigDiff(
    m=16,           # Sparse graph
    ef_construct=100,  # Quick indexing
)
ef_search = 50        # Fast search
```

**Expected:** 50-100 QPS, 80-85% recall

### High Quality (High Recall)

```python
hnsw_config = HnswConfigDiff(
    m=32,           # Denser graph
    ef_construct=200,  # Quality indexing
)
ef_search = 200       # Thorough search
```

**Expected:** 20-30 QPS, 95-98% recall

### Balanced (Production)

```python
hnsw_config = HnswConfigDiff(
    m=24,           # Balanced density
    ef_construct=150,  # Balanced quality
)
ef_search = 100       # Balanced search
```

**Expected:** 30-50 QPS, 90-93% recall

## Dynamic ef Adjustment

```python
# dynamic_ef.py
class AdaptiveSearch:
    """Adjust ef based on query complexity"""

    def __init__(self, base_ef=100):
        self.base_ef = base_ef
        self.history = []

    def get_ef(self, query: str, results_count: int) -> int:
        """Adjust ef based on query and previous results"""

        # Increase ef if few results found
        if results_count < 5:
            return min(self.base_ef * 2, 200)

        # Decrease ef if many results found (speed up)
        if results_count > 50:
            return max(self.base_ef // 2, 50)

        return self.base_ef
```

## Performance Benchmarks

### Expected Performance (entry-level 4-core host)

| Vectors | M | ef | Index Time | Search QPS | Recall@10 |
|---------|---|---|------------|------------|-----------|
| 10K | 16 | 100 | 5s | 150 | 0.95 |
| 100K | 16 | 100 | 45s | 120 | 0.92 |
| 100K | 32 | 200 | 90s | 80 | 0.96 |
| 1M | 32 | 200 | 15min | 40 | 0.93 |
| 1M | 64 | 200 | 25min | 30 | 0.97 |

### Memory Usage

| M | Vectors | Memory per Vector | Total Memory (100K) |
|---|---------|-------------------|---------------------|
| 16 | 100K | ~0.1 KB | ~10 MB |
| 32 | 100K | ~0.2 KB | ~20 MB |
| 64 | 100K | ~0.4 KB | ~40 MB |

## Tuning Checklist

- [ ] Determine dataset size and dimensionality
- [ ] Define target recall threshold
- [ ] Define latency requirements
- [ ] Test different M values (16, 32, 64)
- [ ] Test different ef_construction values (100, 200)
- [ ] Test different ef_search values (50, 100, 200)
- [ ] Measure index build time
- [ ] Measure search throughput
- [ ] Calculate recall@k
- [ ] Plot recall vs speed tradeoff
- [ ] Select optimal configuration
- [ ] Validate with production load


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [6101: HNSW Indexing](../6101-HNSW-Indexing.md)
- [6102: Semantic Similarity](../6102-Semantic-Similarity.md)
- [6401: Qdrant Setup](../../6400-Vector-Databases/6401-Qdrant-Setup.md)
- [EXP_6101: HNSW](../../../../../experiments/EXP_6101_HNSW.md)
