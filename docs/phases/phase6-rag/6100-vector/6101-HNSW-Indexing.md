---
Document ID: 6101
Title: HNSW Indexing - Efficient Semantic Search at Scale
Phase: 6
Module: 6100
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'vectors', 'hnsw', 'embeddings', 'similarity']
---

# 6101: HNSW Indexing - Efficient Semantic Search at Scale

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
```
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
```
Small world property:
  - Most nodes reachable in few hops
  - Some long-range connections (shortcuts)
  - Like social networks (6 degrees of separation)

Example:
  1 ── 2 ── 3 ── 4 ── 5
  │                   │
  └───────────────────┘  (long-range shortcut)

With shortcut: 3 hops from 1 to 4
Without: Need 3 hops

HNSW builds this in multiple layers
```

### Hierarchical Structure
```
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
    Hierarchical Navigable Small World index
    """
    def __init__(self, dim=768, max_connections=16, max_layer=16):
        self.dim = dim
        self.max_connections = max_connections  # M parameter
        self.max_layer = max_layer

        # Each layer is a graph
        self.layers = {0: []}  # Start with layer 0

        # Points: (vector_id, vector, neighbors[])
        self.points = {}

    def insert(self, vector_id, vector):
        """
        Insert a vector into HNSW index
        """
        point = {
            'id': vector_id,
            'vector': vector,
            'neighbors': []
        }
        self.points[vector_id] = point

        # Determine layer for this point
        # Higher layers have exponentially fewer points
        layer = self._get_random_layer()
        self._ensure_layer(layer)

        # Insert into each layer up to assigned layer
        entry_point = self._get_entry_point()

        for current_layer in range(self.max_layer, layer, -1):
            # Search through higher layers (no insertion)
            entry_point = self._search_layer(
                vector, entry_point, current_layer, ef=1
            )

        # Insert into layers [layer, 0]
        for current_layer in range(min(layer, self.max_layer), -1, -1):
            # Find closest neighbors
            candidates = self._search_layer(
                vector, entry_point, current_layer, ef=self.max_connections
            )

            # Select M nearest neighbors
            neighbors = self._select_neighbors(
                vector, candidates, self.max_connections
            )

            # Add bidirectional connections
            point['neighbors'] = neighbors
            for neighbor_id in neighbors:
                neighbor = self.points[neighbor_id]
                if len(neighbor['neighbors']) < self.max_connections:
                    neighbor['neighbors'].append(vector_id)

            entry_point = point['id'] if current_layer == 0 else entry_point

    def _get_random_layer(self):
        """
        Determine layer for new point
        Higher layers: exponentially less likely
        """
        level = 0
        while np.random.rand() < 0.5 and level < self.max_layer:
            level += 1
        return level

    def search(self, query, k=10, ef=50):
        """
        Search for k nearest neighbors
        """
        # Start from entry point at top layer
        entry_point = self._get_entry_point()
        current_layer = self.max_layer

        # Search through higher layers
        while current_layer > 0:
            entry_point = self._search_layer(
                query, entry_point, current_layer, ef=1
            )
            current_layer -= 1

        # Final search at bottom layer with higher ef
        candidates = self._search_layer(
            query, entry_point, 0, ef=ef
        )

        # Return top k
        top_k = sorted(candidates, key=lambda x: x[1])[:k]
        return [(self.points[p[0]]['vector'], p[1]) for p in top_k]

    def _search_layer(self, query, entry_point, layer, ef):
        """
        Greedy search on a specific layer
        ef: number of candidates to track
        """
        visited = set()
        candidates = [(entry_point, self._distance(query, entry_point))]
        best = entry_point

        while candidates:
            # Get closest unvisited candidate
            candidates.sort(key=lambda x: x[1])

            current, dist = candidates.pop(0)

            if current in visited:
                continue

            visited.add(current)

            # Update best
            current_point = self.points[current]
            if dist < self._distance(query, best):
                best = current

            # Add neighbors
            for neighbor in current_point['neighbors']:
                if neighbor not in visited:
                    neighbor_dist = self._distance(query, neighbor)
                    candidates.append((neighbor, neighbor_dist))

            # Keep only ef closest
            if len(candidates) > ef:
                candidates = sorted(candidates, key=lambda x: x[1])[:ef]

        return [p[0] for p in candidates]

    def _distance(self, vector_a, vector_b_or_id):
        """Compute distance (cosine or Euclidean)"""
        if isinstance(vector_b_or_id, int):
            vector_b = self.points[vector_b_or_id]['vector']
        else:
            vector_b = vector_b_or_id

        # Cosine distance
        return 1 - np.dot(vector_a, vector_b) / (
            np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
        )
```

## Using FAISS (Production HNSW)

### FAISS HNSW Index
```python
import faiss
import numpy as np

# 1. Create HNSW index
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

### GPU-Accelerated HNSW
```python
# Use GPU for faster search

# 1. Transfer to GPU
res = faiss.StandardGpuResources()
gpu_index = faiss.index_cpu_to_gpu(res, 0, index)

# 2. Search on GPU
distances, indices = gpu_index.search(query, k)

# Benefits:
# - 10-50x faster than CPU
# - Essential for large-scale deployment
# - 11GB-class GPU: ~5000 queries/sec for 1M vectors
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

embeddings = encoder.encode(documents)

# 3. Build HNSW index
dim = embeddings.shape[1]
M = 16
index = faiss.IndexHNSWFlat(dim, M)
index.hnsw.efSearch = 100

index.add(embeddings.astype('float32'))

# 4. Search
query = "artificial intelligence"
query_embedding = encoder.encode([query])

distances, indices = index.search(query_embedding.astype('float32'), k=5)

# 5. Display results
for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
    print(f"{i+1}. {documents[idx]} (similarity: {1-dist:.4f})")
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

## Next Steps

- Continue with: **[6102: Next Document](./6102-Vector-Embeddings.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [6102: Semantic Similarity](./6102-Semantic-Similarity.md)
- [6201: Hybrid Search](../6200-retrieval/6201-Hybrid-Search.md)
- [6301: Neo4j GraphRAG](../6300-context/6301-Neo4j-and-Knowledge-Graphs.md)

**Experiment Template:** `experiments/EXP_6101_HNSW.md"
