---
Document ID: 6101
Title: HNSW Indexing - Efficient Semantic Search at Scale
Phase: 6
Module: 6100
Last Updated: 2026-09-27
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'vectors', 'hnsw', 'embeddings', 'similarity']
---

# 6101: HNSW Indexing - Efficient Semantic Search at Scale

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Problem of Vector Search](#the-problem-of-vector-search)
- [HNSW Algorithm](#hnsw-algorithm)
- [Using FAISS (Production HNSW)](#using-faiss-production-hnsw)
- [HNSW Parameters](#hnsw-parameters)
- [Integration with Embedding Models](#integration-with-embedding-models)
- [Evaluation](#evaluation)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Contrast brute-force vs ANN search — O(N·D) per query at 1M×768 forces approximation; HNSW trades a bounded recall loss for orders-of-magnitude speedups
- Trace the HNSW graph — exponentially-decaying level assignment (P(l)=0.5^l), greedy descent through upper layers with ef=1, beam search on layer 0 with ef, and why neighbor lists must be PER-LAYER
- Build the production index with FAISS — IndexHNSWFlat(dim, M), efConstruction/efSearch, write/read persistence — and normalize + METRIC_INNER_PRODUCT when you want cosine
- Predict parameter effects before tuning — M sets graph degree (memory ≈ 4·D bytes/vector + ~2·M ids, accuracy and build time rise together); efSearch is the query-time recall/speed dial (keep ef ≥ k)
- Wire an end-to-end semantic search pipeline — SentenceTransformer encoder → float32 → index.add → query encode → top-k with real cosine similarity scores
- Measure recall@k against exact ground truth across ef values and read the recall/latency curve to pick the operating point

---

## Abstract
HNSW (Hierarchical Navigable Small World) graphs enable efficient approximate nearest neighbor search in high-dimensional vector spaces. This is essential for semantic search and RAG systems.

## The Problem of Vector Search

### Brute Force Search
```python
import numpy as np

def brute_force_search(query, vectors, k=10):
    """
    Exact nearest neighbor search
    Complexity: O(N × D) per query
    Where: N = number of vectors, D = dimensionality
    """
    # Compute all distances
    distances = np.linalg.norm(vectors - query, axis=1)

    # Return top k
    top_k_indices = np.argsort(distances)[:k]
    return top_k_indices, distances[top_k_indices]

# For 1M vectors of 768 dimensions:
# Time per query: ~100-200ms (too slow!)
# Memory: Need all vectors in RAM
```

### Approximate Nearest Neighbor (ANN)
```text
Goal: Fast approximate search
Trade-off: Small accuracy loss for massive speed gain

ANN Methods:
  - HNSW: Graph-based (fastest, most popular)
  - IVF: Inverted file index
  - Annoy: Forest-based trees
  - Faiss: Facebook's library (implements multiple)
```

## HNSW Algorithm

### Small World Graphs
```text
Small world property:
  - Most nodes reachable in few hops
  - Some long-range connections (shortcuts)
  - Like social networks (6 degrees of separation)

Example:
  1 ── 2 ── 3 ── 4 ── 5
  │                   │
  └───────────────────┘  (long-range shortcut 1→5)

With the 1→5 shortcut:  1 → 5 → 4 = 2 hops
Without it:             1 → 2 → 3 → 4 = 3 hops

HNSW builds this in multiple layers
```

### Hierarchical Structure
```text
HNSW builds multiple graph layers:

Layer 2:  ───○───────○───          (fewest nodes)
            │         │
Layer 1:    ○────○────○──○───      (more nodes)
           /│    │\   │    \
Layer 0:  ○○○──○○○──○○○──○○○      (all nodes)

Search:
  1. Start at top layer (few nodes)
  2. Quickly navigate to region
  3. Descend to lower layers
  4. Refine search at bottom

Result: O(log N) search instead of O(N)
```

### HNSW Construction
```python
import numpy as np

class HNSWIndex:
    """
    Hierarchical Navigable Small World index (compact teaching build).

    The one data-structure rule that makes HNSW "hierarchical": each
    point keeps PER-LAYER neighbor lists. A single flat neighbors list
    would turn every layer into the same graph — the hierarchy
    decorative — and break insertion, which links different nodes on
    different layers.
    """
    def __init__(self, dim=768, max_connections=16, max_layer=16,
                 ef_construction=100):
        self.dim = dim
        self.max_connections = max_connections  # M parameter
        self.max_layer = max_layer
        # Construction-time beam. MUST exceed M: with beam = M the
        # insert search saturates inside the first local cluster it
        # lands in, no long-range links ever form, and the graph
        # fragments into disconnected ~M-sized cliques
        self.ef_construction = ef_construction
        self.layers = {}  # layer -> [ids whose TOP layer is that layer]
        self.points = {}  # id -> {'vector': ..., 'neighbors': {layer: [ids]}}

    def _get_random_layer(self):
        """
        Determine layer for new point.
        Higher layers: exponentially less likely — P(level = l) = 0.5^l
        """
        level = 0
        while np.random.rand() < 0.5 and level < self.max_layer:
            level += 1
        return level

    def _get_entry_point(self):
        """An id on the highest populated layer (None while empty)"""
        if not self.points:
            return None
        top = max(self.layers)
        return self.layers[top][0]

    def _distance(self, vector_a, vector_b_or_id):
        """Cosine distance to a raw vector or a stored id"""
        vector_b = (self.points[vector_b_or_id]['vector']
                    if isinstance(vector_b_or_id, int) else vector_b_or_id)
        return 1 - np.dot(vector_a, vector_b) / (
            np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
        )

    def _search_layer(self, query, entry_point, layer, ef):
        """
        Greedy best-first beam search along ONE layer's edges.
        ef: beam width — candidates tracked. Returns up to ef
        (distance, id) pairs, closest first.
        """
        visited = {entry_point}
        d0 = self._distance(query, entry_point)
        candidates = [(d0, entry_point)]   # frontier to expand (min first)
        results = [(d0, entry_point)]      # best ef seen so far

        while candidates:
            candidates.sort()
            d_curr, curr = candidates.pop(0)
            # Stop when the closest frontier node is worse than the
            # ef-th best result — nothing closer is reachable from here
            if len(results) >= ef and d_curr > max(results)[0]:
                break
            for neighbor in self.points[curr]['neighbors'].get(layer, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                d = self._distance(query, neighbor)
                if len(results) < ef or d < max(results)[0]:
                    candidates.append((d, neighbor))
                    results.append((d, neighbor))
                    if len(results) > ef:
                        results.sort()   # ascending by distance...
                        results.pop()    # ...drop the worst (largest)
        return sorted(results)

    def insert(self, vector_id, vector):
        """Draw a level, descend from the top, link on layers <= level"""
        entry_point = self._get_entry_point()
        level = self._get_random_layer()

        self.points[vector_id] = {'vector': vector, 'level': level,
                                  'neighbors': {}}
        if entry_point is None:
            self.layers.setdefault(level, []).append(vector_id)
            return  # first point in the index

        old_top = max(self.layers)
        self.layers.setdefault(level, []).append(vector_id)

        # Zoom in through layers ABOVE the new point (greedy, ef=1)
        for current_layer in range(old_top, level, -1):
            entry_point = self._search_layer(
                vector, entry_point, current_layer, ef=1
            )[0][1]

        # Link on every POPULATED layer the point lives on: wide beam
        # (ef_construction) to SEE far enough, then keep the top M
        for current_layer in range(min(level, old_top), -1, -1):
            found = self._search_layer(
                vector, entry_point, current_layer, ef=self.ef_construction
            )
            neighbors = [n for _, n in found[:self.max_connections]]
            self.points[vector_id]['neighbors'][current_layer] = list(neighbors)
            for n in neighbors:
                # n gets the reverse edge ONLY if it lives on this
                # layer; phantom cross-layer edges would collapse the
                # hierarchy back into one flat graph
                if current_layer > self.points[n]['level']:
                    continue
                adj = self.points[n]['neighbors'].setdefault(current_layer, [])
                if len(adj) < self.max_connections:
                    adj.append(vector_id)
                else:
                    # Bounded update WITH eviction: a hard cap without
                    # replacement saturates the early core — its slots
                    # fill, nothing can ever attach again, and the
                    # graph freezes into disconnected islands. Keep the
                    # M CLOSEST instead: evict n's farthest neighbor
                    # when the newcomer is closer
                    dists = [self._distance(self.points[n]['vector'],
                                            self.points[m]['vector'])
                             for m in adj]
                    far_i = int(np.argmax(dists))
                    if dists[far_i] > self._distance(
                            self.points[n]['vector'], vector):
                        adj[far_i] = vector_id
            if neighbors:
                entry_point = neighbors[0]

    def search(self, query, k=10, ef=50):
        """Greedy descent, then beam search layer 0 with the query's ef"""
        entry_point = self._get_entry_point()
        if entry_point is None:
            return []

        # Search through higher layers — the CURRENT top, not max_layer
        # (most points never live above layer 0-2)
        for current_layer in range(max(self.layers), 0, -1):
            entry_point = self._search_layer(
                query, entry_point, current_layer, ef=1
            )[0][1]

        # Final beam at the bottom layer (ef >= k so k results exist)
        found = self._search_layer(query, entry_point, 0, ef=max(ef, k))
        return [(self.points[n]['vector'], d) for d, n in found[:k]]
```

## Using FAISS (Production HNSW)

### FAISS HNSW Index
```python
import faiss
import numpy as np

# 1. Create HNSW index — the default metric is L2; for cosine see
# the Integration section (normalize + METRIC_INNER_PRODUCT)
dim = 768
M = 32  # Max connections per node
index = faiss.IndexHNSWFlat(dim, M)

# Set HNSW parameters
index.hnsw.efSearch = 100  # ef parameter (higher = more accurate)
index.hnsw.efConstruction = 200  # Build parameter

# 2. Add vectors
vectors = np.random.rand(100000, dim).astype('float32')
index.add(vectors)

# 3. Search
query = np.random.rand(1, dim).astype('float32')
k = 10
distances, indices = index.search(query, k)

print(f"Top {k} neighbors: {indices[0]}")
print(f"Distances: {distances[0]}")

# 4. Save/load index
faiss.write_index(index, "hnsw.index")
index = faiss.read_index("hnsw.index")
```

### GPU-Accelerated HNSW — the honest map
```text
Stock FAISS has NO GPU HNSW: graph traversal stays on CPU, and
faiss.index_cpu_to_gpu() on an IndexHNSW* raises — graph indexes are
not supported by the GPU transfer. The real GPU paths:

  - GpuIndexIVFFlat / GpuIndexIVFPQ — the classic GPU ANN route
    (coarse quantizer partitions, then an exact or refined scan);
    10-50x over CPU at large N, but you accept IVF's recall curve
  - CAGRA (RAPIDS cuVS, integrated into recent faiss builds) — a
    GPU-native graph index; the modern choice when you want
    HNSW-like graph search with GPU throughput

Rule of thumb: keep HNSW on CPU — it already saturates a single
core, and typical RAG traffic rarely needs more. Reach for the GPU
when batch QPS demands it, and switch index type to get there.
```

## HNSW Parameters

### M (Max Connections)
```python
# M: Maximum number of connections per node
# Trade-off: Accuracy vs Memory vs Build time

M_values = {
    "M=8": {
        "memory": "Low",
        "accuracy": "Lower",
        "build_time": "Fast",
        "query_time": "Faster",
    },
    "M=16": {
        "memory": "Medium",
        "accuracy": "Good",
        "build_time": "Medium",
        "query_time": "Medium",
        "recommended": True,
    },
    "M=32": {
        "memory": "High",
        "accuracy": "High",
        "build_time": "Slow",
        "query_time": "Slower",
    },
    "M=64": {
        "memory": "Very High",
        "accuracy": "Very High",
        "build_time": "Very Slow",
        "query_time": "Slow",
    },
}

# Memory per vector ≈ 4·D bytes (flat storage) + ~2·M neighbor ids
# (bidirectional graph links, 4 bytes each) — M=32 roughly doubles the
# GRAPH memory over M=16; at 768-D the flat vectors still dominate

# Recommendation: M=16 for most cases
```

### efSearch (Search Parameter)
```python
# efSearch: Number of candidates to track during search
# Higher = More accurate but slower

ef_values = {
    "ef=10": {"speed": "Fast", "accuracy": "Lower"},
    "ef=50": {"speed": "Medium", "accuracy": "Good"},
    "ef=100": {"speed": "Slower", "accuracy": "High", "recommended": True},
    "ef=200": {"speed": "Slow", "accuracy": "Very High"},
}

# Dynamic adjustment:
# - For recall-critical: ef=200-500
# - For speed-critical: ef=20-50
# - For balanced: ef=100
# Keep ef >= k: ef bounds the result beam, so ef < k cannot return
# k neighbors at all
```

## Integration with Embedding Models

### Semantic Search Pipeline
```python
from sentence_transformers import SentenceTransformer
import faiss

# 1. Load embedding model
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Encode documents
documents = [
    "The cat sat on the mat.",
    "Dogs are loyal animals.",
    "Machine learning is a subset of AI.",
    # ... more documents
]

embeddings = encoder.encode(documents).astype('float32')

# 3. Build HNSW index — FAISS's default metric is L2, and 1 - L2
# distance is NOT cosine similarity. For cosine: normalize to the
# unit sphere and switch to inner product — after normalize_L2 the
# inner product EQUALS cosine similarity, so the returned "distance"
# is already the similarity score you want to print
dim = embeddings.shape[1]
M = 16
index = faiss.IndexHNSWFlat(dim, M, faiss.METRIC_INNER_PRODUCT)
index.hnsw.efConstruction = 200  # build quality — set before add()
index.hnsw.efSearch = 100

faiss.normalize_L2(embeddings)   # in-place; requires float32
index.add(embeddings)

# 4. Search — the query gets the same normalization as the corpus
query = "artificial intelligence"
query_embedding = encoder.encode([query]).astype('float32')
faiss.normalize_L2(query_embedding)

distances, indices = index.search(query_embedding, k=5)

# 5. Display results — with the normalized IP metric, distance IS similarity
for i, (idx, sim) in enumerate(zip(indices[0], distances[0])):
    print(f"{i+1}. {documents[idx]} (similarity: {sim:.4f})")
```

### Updating HNSW Index
```python
# HNSW supports incremental updates

# Add new documents
new_docs = [
    "Deep learning uses neural networks.",
    "NLP processes human language.",
]

new_embeddings = encoder.encode(new_docs)
index.add(new_embeddings.astype('float32'))

# Remove (requires rebuilding or marking as deleted)
# FAISS doesn't support efficient removal
# Workaround: Rebuild index periodically
```

## Evaluation

### Recall vs Speed Trade-off
```python
import time

import numpy as np

def evaluate_hnsw_index(index, test_queries, ground_truth, ef_values):
    """
    Evaluate HNSW recall at different ef values
    """
    results = {}

    for ef in ef_values:
        index.hnsw.efSearch = ef

        recalls = []
        times = []

        for query, true_neighbors in zip(test_queries, ground_truth):
            start = time.time()
            distances, indices = index.search(query, k=10)
            elapsed = time.time() - start

            # Compute recall
            retrieved = set(indices[0])
            relevant = set(true_neighbors[:10])
            recall = len(retrieved & relevant) / len(relevant)

            recalls.append(recall)
            times.append(elapsed)

        results[ef] = {
            'recall': np.mean(recalls),
            'time': np.mean(times),
        }

    return results

# Typical results:
# ef=10:  recall=85%,  time=0.5ms
# ef=50:  recall=95%,  time=1.2ms
# ef=100: recall=98%,  time=2.1ms
# ef=200: recall=99%,  time=4.0ms
```

---

## References

### Related ai-engineering-curriculum Documents

- [6102: Semantic Similarity Metrics - Cosine, Dot Product, and Manifold Metrics](6102-Semantic-Similarity.md)

---

## Next Steps

- Continue with: **[6102: Semantic Similarity](./6102-Semantic-Similarity.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_6101: HNSW](../../../../experiments/EXP_6101_HNSW.md)**
