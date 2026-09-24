---
Document ID: 6102
Title: Semantic Similarity Metrics - Cosine, Dot Product, and Manifold Metrics
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

# 6102: Semantic Similarity Metrics - Cosine, Dot Product, and Manifold Metrics

## Abstract
Semantic similarity metrics quantify how similar two embeddings are. Different metrics suit different tasks and embedding spaces.

## Distance vs Similarity

### Key Distinction
```
Distance: Lower = more similar
  - Euclidean distance
  - Manhattan distance
  - Cosine distance

Similarity: Higher = more similar
  - Cosine similarity
  - Dot product
  - Jaccard similarity

Conversion: similarity = 1 / (1 + distance)
```

### Normalized vs Non-Normalized Embeddings
```
Normalized embeddings (unit length):
  - All embeddings have ||v|| = 1
  - Cosine similarity = dot product
  - Used by: OpenAI, Sentence Transformers

Non-normalized embeddings:
  - Variable lengths
  - Magnitude carries information
  - Used by: Word2Vec, GloVe (sometimes)
```

## Cosine Similarity

### Formula and Implementation
```python
import numpy as np
import torch

def cosine_similarity(a, b):
    """
    Cosine similarity: cos(θ) between vectors

    Formula: (a · b) / (||a|| × ||b||)

    Range: [-1, 1]
    - 1: Same direction
    - 0: Orthogonal (unrelated)
    - -1: Opposite direction
    """
    # NumPy
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    return dot_product / (norm_a * norm_b)

# PyTorch (batched)
def batch_cosine_similarity(a, b):
    """
    a: (batch_size, dim)
    b: (batch_size, dim)
    Returns: (batch_size,) similarities
    """
    a_norm = torch.nn.functional.normalize(a, p=2, dim=-1)
    b_norm = torch.nn.functional.normalize(b, p=2, dim=-1)
    return (a_norm * b_norm).sum(dim=-1)

# Example
v1 = np.array([1, 2, 3])
v2 = np.array([2, 4, 6])  # Same direction, different magnitude
print(cosine_similarity(v1, v2))  # 1.0 (perfect similarity)
```

### When to Use Cosine Similarity
```
Use Cosine Similarity when:
✓ Comparing semantic similarity
✓ Magnitude doesn't matter (direction only)
✓ Embeddings are from sentence transformers
✓ Text similarity tasks

Don't Use when:
✗ Absolute magnitude matters
✗ Using word embeddings with frequency info
✗ Clustering requires Euclidean distance
```

## Dot Product Similarity

### Formula and Implementation
```python
def dot_product_similarity(a, b):
    """
    Dot product: a · b = Σ(a_i × b_i)

    For normalized vectors: equals cosine similarity
    For general vectors: includes magnitude
    """
    return np.dot(a, b)

# Batched PyTorch
def batch_dot_product(a, b):
    """
    a: (batch_size, dim)
    b: (batch_size, dim)
    """
    return (a * b).sum(dim=-1)

# Example: Word2Vec style
king = np.array([0.8, 0.5, 0.3])
queen = np.array([0.7, 0.4, 0.4])
man = np.array([0.6, 0.3, 0.1])

# Dot product captures both direction and magnitude
print(dot_product_similarity(king, queen))  # High similarity
print(dot_product_similarity(king, man))    # Moderate similarity
```

### Dot Product in Attention
```python
# Self-attention uses scaled dot product

def scaled_dot_product_attention(Q, K, V):
    """
    Q, K, V: (batch, heads, seq_len, dim)
    """
    # Dot product similarity (scaled)
    scores = torch.matmul(Q, K.transpose(-2, -1)) / (K.size(-1) ** 0.5)

    # Convert to similarities via softmax
    attn_weights = torch.softmax(scores, dim=-1)

    # Weight values by similarities
    output = torch.matmul(attn_weights, V)

    return output

# This is the core of transformer attention!
```

### Cosine vs Dot Product
```
Normalized vectors:
  Cosine similarity = Dot product similarity
  (Both measure angular similarity)

Non-normalized vectors:
  Cosine: Only direction
  Dot product: Direction + magnitude

Example:
  v1 = [1, 1, 1], v2 = [100, 100, 100]

  Cosine similarity: 1.0 (same direction)
  Dot product: 300 (high, but penalizes magnitude diff)

Recommendation: Use cosine for text, dot product for attention
```

## Euclidean Distance

### Formula and Implementation
```python
def euclidean_distance(a, b):
    """
    L2 distance: ||a - b|| = √(Σ(a_i - b_i)²)
    """
    return np.linalg.norm(a - b)

def squared_euclidean_distance(a, b):
    """
    Squared L2: Σ(a_i - b_i)²
    Faster (no sqrt), preserves order
    """
    return np.sum((a - b) ** 2)

# Batched PyTorch
def batch_euclidean_distance(a, b):
    """
    a: (batch_size, dim)
    b: (batch_size, dim)
    """
    return torch.norm(a - b, p=2, dim=-1)

# Relationship to cosine similarity
def cosine_to_euclidean_distance(cosine_sim, norm_a, norm_b):
    """
    Convert cosine similarity to Euclidean distance

    ||a - b||² = ||a||² + ||b||² - 2||a||×||b||×cos(θ)
    """
    return np.sqrt(norm_a**2 + norm_b**2 - 2 * norm_a * norm_b * cosine_sim)
```

### When to Use Euclidean Distance
```
Use Euclidean Distance when:
✓ Physical distance interpretation needed
✓ Clustering (k-means uses Euclidean)
✓ Absolute differences matter
✓ Image embeddings (pixel space)

Don't Use when:
✗ Directional similarity only
✓ High-dimensional sparse data (curse of dimensionality)
✗ Semantic text similarity
```

## Manhattan Distance

### Formula and Implementation
```python
def manhattan_distance(a, b):
    """
    L1 distance: Σ|a_i - b_i|
    Also called: City block distance, Taxicab geometry
    """
    return np.sum(np.abs(a - b))

# Batched PyTorch
def batch_manhattan_distance(a, b):
    return torch.abs(a - b).sum(dim=-1)

# Example: Grid pathfinding
start = np.array([0, 0])
end = np.array([3, 4])

euclidean = euclidean_distance(start, end)  # 5.0 (direct line)
manhattan = manhattan_distance(start, end)  # 7.0 (city blocks)
```

### When to Use Manhattan Distance
```
Use Manhattan Distance when:
✓ Grid-based pathfinding
✓ Robustness to outliers needed (L1 vs L2)
✓ Sparse high-dimensional data
✓ Feature selection (L1 regularization)

Don't Use when:
✗ Euclidean geometry applies
✗ Rotational invariance needed
```

## Advanced Metrics

### Minkowski Distance (Generalization)
```python
def minkowski_distance(a, b, p=2):
    """
    General distance: (Σ|a_i - b_i|^p)^(1/p)

    p=1: Manhattan distance
    p=2: Euclidean distance
    p→∞: Chebyshev distance (max of absolute differences)
    """
    return np.sum(np.abs(a - b) ** p) ** (1/p)

# Example
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

print(minkowski_distance(a, b, p=1))  # Manhattan: 9
print(minkowski_distance(a, b, p=2))  # Euclidean: ~5.2
print(minkowski_distance(a, b, p=10)) # Approaches max diff
```

### Jaccard Similarity
```python
def jaccard_similarity(a, b):
    """
    Jaccard: |A ∩ B| / |A ∪ B|

    For sets: Intersection over union
    For vectors: Applied to binary vectors
    """
    # For binary vectors
    intersection = np.sum((a > 0) & (b > 0))
    union = np.sum((a > 0) | (b > 0))

    return intersection / union if union > 0 else 0

# For continuous: Use min/max
def jaccard_similarity_continuous(a, b):
    """
    Continuous Jaccard: Σ min(a,b) / Σ max(a,b)
    """
    return np.sum(np.minimum(a, b)) / np.sum(np.maximum(a, b))

# Use case: Document overlap, set similarity
```

### Pearson Correlation
```python
def pearson_correlation(a, b):
    """
    Pearson correlation coefficient

    Measures linear correlation
    Range: [-1, 1]
    - Similar to cosine but centered (mean subtracted)
    """
    # Center the data
    a_centered = a - np.mean(a)
    b_centered = b - np.mean(b)

    # Compute correlation
    numerator = np.dot(a_centered, b_centered)
    denominator = np.linalg.norm(a_centered) * np.linalg.norm(b_centered)

    return numerator / denominator

# Difference from cosine:
# Cosine: Original vectors
# Pearson: Mean-centered vectors

# Use case: Time series, correlation analysis
```

## Similarity in Practice

### Text Similarity Pipeline
```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 1. Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Encode texts
texts = [
    "The cat sat on the mat",
    "A feline rested on a rug",
    "I love programming",
    "Coding is my passion",
]

embeddings = model.encode(texts)

# 3. Compute similarity matrix
similarity_matrix = np.zeros((len(texts), len(texts)))

for i in range(len(texts)):
    for j in range(len(texts)):
        # Cosine similarity
        similarity_matrix[i, j] = np.dot(
            embeddings[i], embeddings[j]
        ) / (
            np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
        )

# 4. Find most similar pairs
for i in range(len(texts)):
    # Get top similar (excluding self)
    similar_indices = np.argsort(similarity_matrix[i])[-2:-1]
    print(f"'{texts[i]}' is similar to '{texts[similar_indices[0]]}'")
```

### Clustering with Similarity
```python
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

# 1. Compute similarity matrix
sim_matrix = cosine_similarity(embeddings)

# 2. Convert to distance for clustering
dist_matrix = 1 - sim_matrix

# 3. Cluster
clustering = AgglomerativeClustering(
    n_clusters=2,
    affinity='precomputed',
    linkage='average',
)

labels = clustering.fit_predict(dist_matrix)

# 4. Results
for i, label in enumerate(labels):
    print(f"{texts[i]} → Cluster {label}")
```


---

## Next Steps

- Continue with: **[6201-Hybrid-Search.md](./../6200-retrieval/6201-Hybrid-Search.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [6101: HNSW Indexing](./6101-HNSW-Indexing.md)
- [6201: Hybrid Search](../6200-retrieval/6201-Hybrid-Search.md)
- [3201: RoPE](../../phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)

**Experiment Template:** `experiments/EXP_6102_SIMILARITY.md"
