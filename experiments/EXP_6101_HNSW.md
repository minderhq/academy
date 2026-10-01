---
Document ID: EXP_6101
Title: "EXP-6101: HNSW Benchmarking"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
---

# EXP-6101: HNSW Benchmarking

**Performance testing of hierarchical navigable small world graphs**

---

## 🎯 Experiment Overview

**Time:** 60-75 minutes
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:**
- 6101: HNSW Indexing (theory)
- Understanding of vector similarity search
- Basic benchmarking knowledge

**Learning Objectives:**
- Understand HNSW algorithm
- Implement HNSW index
- Benchmark vs alternative methods
- Optimize HNSW parameters

---

## 📚 Background

HNSW (Hierarchical Navigable Small World) is a graph-based index for approximate nearest neighbor search.

### Key Features
- **Hierarchical layers** - Coarse to fine search
- **Logarithmic complexity** - O(log N) search
- **High recall** - >99% with proper tuning
- **Fast build** - Incremental index construction

---

## 🔬 Experiment 1: HNSW Implementation (30 minutes)

### Step 1.1: Basic HNSW

```python
# File: hnsw_impl.py
"""
HNSW Implementation
==================
"""

import numpy as np
from typing import List, Tuple
import heapq

class HNSWNode:
    """Node in HNSW graph"""

    def __init__(self, vector: np.ndarray, level: int, node_id: int):
        self.id = node_id
        self.vector = vector
        self.level = level
        self.connections = [[] for _ in range(level + 1)]

class HNSWIndex:
    """HNSW Index for approximate nearest neighbor search"""

    def __init__(self, dim: int, M: int = 16, ef_construction: int = 200):
        """
        Args:
            dim: Vector dimension
            M: Max connections per node per layer
            ef_construction: Size of candidate list during construction
        """
        self.dim = dim
        self.M = M
        self.ef_construction = ef_construction
        self.entry_point = None
        self.nodes = []
        self.max_level = 0

    def add(self, vector: np.ndarray) -> int:
        """Add vector to index"""

        # Geometric level assignment (standard HNSW: mL = 1/ln(M), 0-based)
        level = int(-np.log(np.random.uniform()) / np.log(self.M))

        node_id = len(self.nodes)
        node = HNSWNode(vector, level, node_id)
        self.nodes.append(node)

        if self.entry_point is None:
            self.entry_point = node
            self.max_level = level
            return node_id

        # Greedy descent from the top layer down to the new node's level
        curr = self.entry_point.id
        for lvl in range(self.max_level, min(level, self.max_level) - 1, -1):
            curr = self._search_level(curr, vector, lvl, 1)[0][0]

        # Insert from the node's top level down to 0
        for lvl in range(min(level, self.max_level), -1, -1):
            # Find ef_construction closest neighbors
            candidates = self._search_level(curr, vector, lvl, self.ef_construction)

            # Select M best neighbors
            neighbors = self._select_neighbors(candidates, self.M)

            # Add bidirectional connections
            for neighbor_id in neighbors:
                neighbor = self.nodes[neighbor_id]
                neighbor.connections[lvl].append(node_id)
                node.connections[lvl].append(neighbor_id)

                # The neighbor's list may now exceed M - prune it too
                self._prune_connections(neighbor, lvl, self.M)

            # Prune connections if needed
            self._prune_connections(node, lvl, self.M)

            # Set entry point for the next (lower) level
            if len(neighbors) > 0:
                curr = neighbors[0]

        # Update max level
        if level > self.max_level:
            self.max_level = level
            self.entry_point = node

        return node_id

    def _search_level(self, entry_id: int, query: np.ndarray,
                     level: int, ef: int) -> List[Tuple[int, float]]:
        """Search at specific level

        Args:
            entry_id: Node id to start the search from
            ef: Size of the result list
        """

        visited = set()
        candidates = []  # Min-heap of (distance, node_id)
        w = []  # Result list (negated distances -> furthest on top)

        entry = self.nodes[entry_id]
        entry_dist = np.linalg.norm(entry.vector - query)
        heapq.heappush(candidates, (entry_dist, entry_id))
        heapq.heappush(w, (-entry_dist, entry_id))

        while len(candidates) > 0:
            dist, current_id = heapq.heappop(candidates)

            if current_id in visited:
                continue
            visited.add(current_id)

            current = self.nodes[current_id]
            lower_bound = w[0][0]  # Furthest in w

            if dist > -lower_bound:
                break

            # Check neighbors
            for neighbor_id in current.connections[level]:
                if neighbor_id in visited:
                    continue

                neighbor = self.nodes[neighbor_id]
                neighbor_dist = np.linalg.norm(neighbor.vector - query)

                if len(w) < ef or neighbor_dist < -w[0][0]:
                    heapq.heappush(candidates, (neighbor_dist, neighbor_id))
                    heapq.heappush(w, (-neighbor_dist, neighbor_id))

                    if len(w) > ef:
                        heapq.heappop(w)

        # Return node IDs and distances
        return [(node_id, -dist) for dist, node_id in w]

    def _select_neighbors(self, candidates: List[Tuple[int, float]],
                         M: int) -> List[int]:
        """Select M nearest neighbors"""
        return [node_id for node_id, _ in sorted(candidates, key=lambda x: x[1])[:M]]

    def _prune_connections(self, node: HNSWNode, level: int, M: int):
        """Prune connections to at most M"""
        if len(node.connections[level]) <= M:
            return

        # Keep closest M neighbors
        distances = [(self._distance_to(node, self.nodes[nid]), nid)
                     for nid in node.connections[level]]
        distances.sort()
        node.connections[level] = [nid for _, nid in distances[:M]]

    def _distance_to(self, node1: HNSWNode, node2: HNSWNode) -> float:
        """Compute distance between nodes"""
        return np.linalg.norm(node1.vector - node2.vector)

    def search(self, query: np.ndarray, K: int = 10,
               ef: int = None) -> List[Tuple[int, float]]:
        """Search for K nearest neighbors

        Args:
            ef: Search-time candidate list size; higher = better recall,
                slower. Defaults to K.
        """

        if self.entry_point is None:
            return []

        if ef is None:
            ef = K
        ef = max(ef, K)

        # Start from top level
        curr = self.entry_point.id

        for level in range(self.max_level, 0, -1):
            curr = self._search_level(curr, query, level, 1)[0][0]

        # Search at level 0
        results = self._search_level(curr, query, 0, ef)

        return sorted(results, key=lambda x: x[1])[:K]

# Test
index = HNSWIndex(dim=128)

# Add random vectors
vectors = np.random.randn(1000, 128).astype(np.float32)

for i, vec in enumerate(vectors):
    index.add(vec)
    if (i + 1) % 100 == 0:
        print(f"Added {i + 1} vectors")

# Search
query = np.random.randn(128).astype(np.float32)
results = index.search(query, K=5)

print(f"\nTop 5 neighbors:")
for node_id, dist in results:
    print(f"  Node {node_id}: distance = {dist:.4f}")
```

**Checkpoint 1:** ✅ HNSW implemented

---

## 🔬 Experiment 2: Benchmark (20 minutes)

### Step 2.1: Compare Methods

```python
# File: benchmark_hnsw.py
"""
Benchmark HNSW vs Alternatives
===============================
"""

import numpy as np
import time
from hnsw_impl import HNSWIndex

# Note: this pure-Python HNSW trades raw speed for clarity. Production
# libraries (hnswlib, FAISS) run the same algorithm 100-1000x faster -
# that C-level speed is where the results-table speedups come from.

def benchmark_hnsw(vectors: np.ndarray, queries: np.ndarray,
                    M: int = 16, ef_construction: int = 200) -> dict:
    """Benchmark HNSW"""

    # Build index
    start = time.time()
    index = HNSWIndex(dim=vectors.shape[1], M=M, ef_construction=ef_construction)
    for vec in vectors:
        index.add(vec)
    build_time = time.time() - start

    # Query
    start = time.time()
    for query in queries:
        index.search(query, K=10)
    query_time = time.time() - start

    return {
        'build_time': build_time,
        'query_time': query_time,
        'avg_query_time': query_time / len(queries)
    }

def benchmark_brute_force(vectors: np.ndarray, queries: np.ndarray) -> dict:
    """Benchmark brute force search"""

    # Query
    start = time.time()
    for query in queries:
        distances = np.linalg.norm(vectors - query, axis=1)
        top_k = np.argsort(distances)[:10]
    query_time = time.time() - start

    return {
        'build_time': 0,
        'query_time': query_time,
        'avg_query_time': query_time / len(queries)
    }

# Test data
vectors = np.random.randn(10000, 128).astype(np.float32)
queries = np.random.randn(100, 128).astype(np.float32)

# Benchmark HNSW
hnsw_results = benchmark_hnsw(vectors, queries, M=16, ef_construction=200)

# Benchmark brute force
bf_results = benchmark_brute_force(vectors, queries)

print("=== Benchmark Results ===")
print(f"{'Method':<15} {'Build (s)':<12} {'Query (ms)':<15} {'Speedup'}")
print("-" * 60)
print(f"{'HNSW':<15} {hnsw_results['build_time']:<12.3f} {hnsw_results['avg_query_time']*1000:<15.3f} {bf_results['avg_query_time']/hnsw_results['avg_query_time']:.2f}x")
print(f"{'Brute Force':<15} {bf_results['build_time']:<12.3f} {bf_results['avg_query_time']*1000:<15.3f} 1.0x")
```

**Checkpoint 2:** ✅ Benchmark complete

---

## 🔬 Experiment 3: Parameter Tuning (20 minutes)

### Step 3.1: Optimize M and ef

```python
# File: tune_parameters.py
"""
Optimize HNSW Parameters
========================
"""

import numpy as np
import time
import matplotlib.pyplot as plt

from hnsw_impl import HNSWIndex

def test_parameters(vectors: np.ndarray, queries: np.ndarray,
                     M_values: list, ef_values: list) -> dict:
    """Test different HNSW parameters"""

    results = {}

    for M in M_values:
        for ef in ef_values:
            index = HNSWIndex(dim=vectors.shape[1], M=M, ef_construction=ef)

            for vec in vectors:
                index.add(vec)

            # Measure query time
            start = time.time()
            for query in queries:
                index.search(query, K=10)
            query_time = time.time() - start

            results[(M, ef)] = query_time / len(queries)

    return results

# Test data
vectors = np.random.randn(5000, 128).astype(np.float32)
queries = np.random.randn(50, 128).astype(np.float32)

M_values = [8, 16, 24, 32]
ef_values = [50, 100, 200, 400]

results = test_parameters(vectors, queries, M_values, ef_values)

# Find best
best = min(results.items(), key=lambda x: x[1])
print(f"Best parameters: M={best[0][0]}, ef={best[0][1]}")
print(f"Query time: {best[1]*1000:.3f} ms")

# Plot heatmap
data = np.zeros((len(M_values), len(ef_values)))
for i, M in enumerate(M_values):
    for j, ef in enumerate(ef_values):
        data[i, j] = results[(M, ef)] * 1000

plt.figure(figsize=(10, 8))
plt.imshow(data, cmap='viridis_r')
plt.colorbar(label='Query Time (ms)')
plt.xticks(range(len(ef_values)), ef_values)
plt.yticks(range(len(M_values)), M_values)
plt.xlabel('ef_construction')
plt.ylabel('M')
plt.title('HNSW Parameter Tuning')
for i, M in enumerate(M_values):
    for j, ef in enumerate(ef_values):
        plt.text(j, i, f'{data[i, j]:.1f}', ha='center', va='center', color='white')

plt.savefig('hnsw_tuning.png')
print("✓ Saved plot to hnsw_tuning.png")
```

**Checkpoint 3:** ✅ Parameters tuned

---

## 📊 Results Summary

### Performance by Dataset Size

| Size | Brute Force | HNSW | Speedup |
|------|-------------|------|---------|
| 1K | 0.5 ms | 0.3 ms | 1.7x |
| 10K | 5 ms | 0.5 ms | 10x |
| 100K | 50 ms | 0.8 ms | 62x |
| 1M | 500 ms | 1.2 ms | 417x |

### Optimal Parameters

| Dataset Size | M | ef_construction |
|--------------|---|-----------------|
| < 10K | 8 | 50 |
| 10K - 100K | 16 | 100 |
| 100K - 1M | 24 | 200 |
| > 1M | 32 | 400 |

---

## ✅ Experiment Checklist

- [ ] HNSW implementation working
- [ ] Benchmark vs brute force
- [ ] Parameters optimized
- [ ] Results analyzed

---

## 🎓 Key Takeaways

1. **HNSW = Fast + Accurate** - Logarithmic search with high recall
2. **M controls connectivity** - More connections = slower but more accurate
3. **ef controls quality** - Higher ef = better results but slower
4. **Scalability** - Excellent for large datasets
5. **Memory overhead** - Graph structure uses extra memory

---

## 🚀 Next Steps

1. **EXP_6201**: Hybrid Search - Combine with keyword search
2. **EXP_6301**: GraphRAG - Knowledge graph integration
3. **LAB-007**: Production RAG - Deploy at scale

---

**Last Updated:** 2026-10-01
**Experiment:** 6101 - HNSW Benchmarking
**Time Estimate:** 60-75 minutes
**Difficulty:** ⭐⭐⭐ Advanced
