---
Document ID: 6103
Title: "6103: HNSW Parameter Tuning Guide"
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
---

# 6103: HNSW Parameter Tuning Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [HNSW Architecture](#hnsw-architecture)
- [Parameter Deep Dive](#parameter-deep-dive)
- [Tuning Strategy](#tuning-strategy)
- [Production Configurations](#production-configurations)
- [Optimal Settings by Use Case](#optimal-settings-by-use-case)
- [Dynamic ef Adjustment](#dynamic-ef-adjustment)
- [Performance Benchmarks](#performance-benchmarks)
- [Tuning Checklist](#tuning-checklist)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Map the HNSW layer hierarchy — exponentially fewer nodes at the top, greedy descent from the sparse layers into the dense layer-0 graph, and where M, ef_construction, and ef_search act on it
- Tune M, ef_construction, and ef_search from their trade-off surfaces — graph density and the ≈2·M·4-byte link memory per vector, build speed vs build quality, query recall vs latency
- Run the two-step tuning loop — benchmark a configuration grid end-to-end (index throughput + search QPS via `query_points`), then sweep ef and plot the recall@k vs latency curve to locate the operating point
- Ship production Qdrant collections with `HnswConfigDiff` — m, ef_construct, and full_scan_threshold (KB of vector storage below which Qdrant skips HNSW for exact scan) — sized to the dataset scale
- Match preset configurations to SLAs — low-latency (M=16, ef=50), high-recall (M=32, ef=200), balanced (M=24, ef=100) — and read their expected QPS/recall envelopes
- Adapt ef at query time — double it when the previous query starved (<5 results), halve it when the result stream was rich (>50), clamped to [50, 200]

---

## Abstract
Comprehensive guide for tuning HNSW (Hierarchical Navigable Small World) index parameters for optimal vector search performance on PROJECT-OMEGA infrastructure.

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

# For very high recall (still approximate — exact = full scan)
ef_search = 200
```

## Tuning Strategy

### Step 1: Benchmark Baseline

```python
# hnsw_benchmark.py
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    HnswConfigDiff,
    PointStruct,
    SearchParams,
    VectorParams,
)
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

        # A REAL server is required: local `:memory:` mode does exact
        # brute-force search and ignores hnsw_ef — nothing to tune there
        client = QdrantClient(url="http://localhost:6333")
        collection = f"test_m{config['m']}_ef{config['ef']}"

        # Create collection
        try:
            client.delete_collection(collection)
        except Exception:
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
            # client.search() was deprecated in qdrant-client 1.10 and
            # is REMOVED by 1.19 (AttributeError) — query_points() is
            # the universal API; ef travels via SearchParams now
            client.query_points(
                collection,
                query=query.tolist(),
                limit=10,
                search_params=SearchParams(hnsw_ef=config["ef"]),
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
import time

from qdrant_client.models import SearchParams


def calculate_recall(search_results, ground_truth, k):
    """Calculate recall@k"""
    retrieved_ids = set(r.id for r in search_results[:k])
    relevant_ids = set(ground_truth)
    return len(retrieved_ids & relevant_ids) / len(relevant_ids)


def analyze_recall_vs_speed(client, collection, queries, ground_truth):
    """
    Sweep ef_search, measure recall@10 and mean latency per query.

    queries: list of query vectors (each a list of floats)
    ground_truth: list of id-lists — the exact top-10 neighbors per
    query, from a brute-force pass over the same vectors
    """
    ef_values = [10, 20, 50, 100, 150, 200]
    results = {}

    for ef in ef_values:
        recalls, times = [], []
        for query, truth in zip(queries, ground_truth):
            start = time.time()
            found = client.query_points(
                collection,
                query=query,
                limit=10,
                search_params=SearchParams(hnsw_ef=ef),
            ).points
            times.append((time.time() - start) * 1000)  # ms
            recalls.append(calculate_recall(found, truth, k=10))

        results[ef] = {
            "recall": sum(recalls) / len(recalls),
            "time_ms": sum(times) / len(times),
        }

    return results


def plot_recall_vs_speed(results, out_path="hnsw_ef_analysis.png"):
    """Two-panel plot: recall@10 and latency as functions of ef"""
    import matplotlib.pyplot as plt

    ef_list = sorted(results)
    recalls = [results[e]["recall"] for e in ef_list]
    times = [results[e]["time_ms"] for e in ef_list]

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
    plt.savefig(out_path, dpi=150)


if __name__ == "__main__":
    # client: QdrantClient(url="http://localhost:6333") against a real
    # server (local :memory: mode does exact brute-force, so ef has no
    # effect there); collection built as in Step 1; ground_truth from
    # an exact brute-force pass over the inserted vectors
    pass
```

## Production Configurations

### Qdrant HNSW Config

```python
from qdrant_client.models import Distance, HnswConfigDiff, VectorParams

# Small dataset (<100K vectors)
hnsw_config_small = HnswConfigDiff(
    m=16,
    ef_construct=100,
)

# Medium dataset (100K-1M vectors)
# full_scan_threshold is KILOBYTES of vector storage: collections
# smaller than this skip HNSW entirely and answer with exact scan
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


if __name__ == "__main__":
    # Needs a live server (local :memory: mode cannot tune HNSW)
    from qdrant_client import QdrantClient

    client = QdrantClient(url="http://localhost:6333")
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
from qdrant_client.models import HnswConfigDiff

hnsw_config = HnswConfigDiff(
    m=16,           # Sparse graph
    ef_construct=100,  # Quick indexing
)
ef_search = 50        # Fast search
```

**Expected:** 50-100 QPS, 80-85% recall

### High Quality (High Recall)

```python
from qdrant_client.models import HnswConfigDiff

hnsw_config = HnswConfigDiff(
    m=32,           # Denser graph
    ef_construct=200,  # Quality indexing
)
ef_search = 200       # Thorough search
```

**Expected:** 20-30 QPS, 95-98% recall

### Balanced (Production)

```python
from qdrant_client.models import HnswConfigDiff

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
    """Adjust ef at query time based on how many results came back."""

    def __init__(self, base_ef=100, min_ef=50, max_ef=200):
        self.base_ef = base_ef
        self.min_ef = min_ef
        self.max_ef = max_ef
        self.history = []

    def get_ef(self, results_count: int) -> int:
        """Adjust ef based on the previous query's result count"""

        # Increase ef if few results found (starved -> look harder)
        if results_count < 5:
            ef = min(self.base_ef * 2, self.max_ef)
        # Decrease ef if many results found (rich -> spend less)
        elif results_count > 50:
            ef = max(self.base_ef // 2, self.min_ef)
        else:
            ef = self.base_ef

        self.history.append((results_count, ef))
        return ef
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

HNSW adds ~2·M link ids per vector at 4 bytes each (bidirectional
graph edges); on top of that come the vectors themselves (4 bytes ×
dim — 1.5 KB at 384-D) and any payloads:

| M | Link bytes / vector (2·M × 4 B) | Total link memory (100K vectors) |
|---|---------------------------------|----------------------------------|
| 16 | 128 B | ~12.8 MB |
| 32 | 256 B | ~25.6 MB |
| 64 | 512 B | ~51.2 MB |

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

## References

### Related PROJECT-OMEGA Documents

- [6101: HNSW Indexing - Efficient Semantic Search at Scale](../6101-HNSW-Indexing.md)
- [6102: Semantic Similarity Metrics - Cosine, Dot Product, and Manifold Metrics](../6102-Semantic-Similarity.md)
- [6401: Qdrant Setup](../../6400-vector-databases/6401-Qdrant-Setup.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**
- Lessons: **[6101: HNSW Indexing](../6101-HNSW-Indexing.md)** · **[6102: Semantic Similarity](../6102-Semantic-Similarity.md)**
- Experiment: **[EXP_6101: HNSW](../../../../../experiments/EXP_6101_HNSW.md)**
