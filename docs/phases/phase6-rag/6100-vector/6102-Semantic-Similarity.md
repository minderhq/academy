---
Document ID: 6102
Title: "6102: Semantic Similarity Metrics - Cosine, Dot Product, and Manifold Metrics"
Phase: 6
Module: 6100
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'vectors', 'hnsw', 'embeddings', 'similarity']
---

# 6102: Semantic Similarity Metrics - Cosine, Dot Product, and Manifold Metrics

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Distance vs Similarity](#distance-vs-similarity)
- [Cosine Similarity](#cosine-similarity)
- [Dot Product Similarity](#dot-product-similarity)
- [Euclidean Distance](#euclidean-distance)
- [Manhattan Distance](#manhattan-distance)
- [Advanced Metrics](#advanced-metrics)
- [Similarity in Practice](#similarity-in-practice)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Contrast distance vs similarity conventions — lower-vs-higher-is-closer, bounded vs unbounded ranges, and the metric-specific conversions (cosine similarity = 1 − cosine distance exactly; 1/(1+d) is just one arbitrary monotone squash)
- Compute cosine similarity in scalar and batched form — the dot-over-norms pipeline and `F.normalize`; verify scale-invariance ([1,2,3] vs [2,4,6] → 1.0 regardless of magnitude)
- Choose cosine vs dot product with the normalization rule — identical on the unit sphere; on raw vectors dot product rewards magnitude (these toy vectors tie on cosine 0.988 vs 0.983 but separate on dot: 0.88 vs 0.66)
- Derive Euclidean from cosine — ‖a−b‖² = ‖a‖² + ‖b‖² − 2·a·b (law of cosines), and why squared L2 preserves ranking without paying for the sqrt
- Place Manhattan and Minkowski — L1's robustness to outliers, and the p dial interpolating L1 → L2 → Chebyshev (p→∞)
- Run the end-to-end practice loop — encoder embeddings, vectorized similarity matrix, nearest-neighbor extraction, and sklearn ≥1.4 `AgglomerativeClustering(metric='precomputed')` on 1 − sim

---

## Abstract
Semantic similarity metrics quantify how similar two embeddings are. Different metrics suit different tasks and embedding spaces.

## Distance vs Similarity

### Key Distinction
```text
Distance: Lower = more similar
  - Euclidean distance
  - Manhattan distance
  - Cosine distance

Similarity: Higher = more similar
  - Cosine similarity
  - Dot product
  - Jaccard similarity

Conversion is metric-specific, not universal:
  - Cosine: similarity = 1 - cosine_distance  (exact, by definition)
  - 1 / (1 + distance): an arbitrary monotone squash into [0, 1] —
    fine for ranking, but the absolute values carry no meaning
```

### Normalized vs Non-Normalized Embeddings
```text
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
```text
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
import numpy as np

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

# Dot product captures both direction and magnitude.
# These toy vectors are all nearly parallel, so cosine can barely
# separate them (0.988 vs 0.983) — the dot product's magnitude term
# is what creates the gap here:
print(dot_product_similarity(king, queen))  # 0.88
print(dot_product_similarity(king, man))    # 0.66
```

### Dot Product in Attention
```python
import torch

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
```text
Normalized vectors:
  Cosine similarity = Dot product similarity
  (Both measure angular similarity)

Non-normalized vectors:
  Cosine: Only direction
  Dot product: Direction + magnitude

Example:
  v1 = [1, 1, 1], v2 = [100, 100, 100]

  Cosine similarity: 1.0 (same direction)
  Dot product: 300 — NOT because the texts are "more similar",
  but because v2's raw scale inflates the score. Dot product is
  not scale-invariant: unnormalized corpora leak magnitude in.

Recommendation: Normalize when you want pure direction (cosine
behavior); use raw dot product only when magnitude IS signal
(attention logits, recommendation scores)
```

## Euclidean Distance

### Formula and Implementation
```python
import numpy as np

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
```text
Use Euclidean Distance when:
✓ Physical distance interpretation needed
✓ Clustering (k-means uses Euclidean)
✓ Absolute differences matter
✓ Image embeddings (pixel space)

Don't Use when:
✗ Directional similarity only
✗ High-dimensional sparse data (curse of dimensionality)
✗ Semantic text similarity
```

## Manhattan Distance

### Formula and Implementation
```python
import numpy as np

def manhattan_distance(a, b):
    """
    L1 distance: Σ|a_i - b_i|
    Also called: City block distance, Taxicab geometry
    """
    return np.sum(np.abs(a - b))

# Batched PyTorch
def batch_manhattan_distance(a, b):
    import torch
    return torch.abs(a - b).sum(dim=-1)

# Example: Grid pathfinding
# (euclidean_distance comes from the Euclidean section above)
start = np.array([0, 0])
end = np.array([3, 4])

euclidean = euclidean_distance(start, end)  # 5.0 (direct line)
manhattan = manhattan_distance(start, end)  # 7.0 (city blocks)
```

### When to Use Manhattan Distance
```text
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
import numpy as np

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
import numpy as np

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
import numpy as np

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

    # A constant vector has zero variance — centered norm is 0 and
    # the division would return nan, so guard it
    denominator = np.linalg.norm(a_centered) * np.linalg.norm(b_centered)
    if denominator == 0:
        return 0.0

    return np.dot(a_centered, b_centered) / denominator

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

# embeddings / texts come from the Text Similarity Pipeline above

# 1. Compute similarity matrix
sim_matrix = cosine_similarity(embeddings)

# 2. Convert to distance for clustering
dist_matrix = 1 - sim_matrix

# 3. Cluster — the parameter is `metric` since scikit-learn 1.4
# (the old `affinity='precomputed'` was removed and raises TypeError)
clustering = AgglomerativeClustering(
    n_clusters=2,
    metric='precomputed',
    linkage='average',
)

labels = clustering.fit_predict(dist_matrix)

# 4. Results
for i, label in enumerate(labels):
    print(f"{texts[i]} → Cluster {label}")
```


---

## Summary

Semantic similarity metrics quantify how close two embeddings are, and the choice is not cosmetic: distance scales (Euclidean, Manhattan) say lower is closer, similarity scales (cosine, dot product) say higher is closer, and the embedding model's training objective decides which one it expects. This lesson covered the distance-versus-similarity distinction, the metric formulas, and matching metric to embedding space. The rule it leaves: use the metric your embedding model was trained with - the wrong metric quietly scrambles the ranking.

## References

### Related PROJECT-OMEGA Documents

- [6101: HNSW Indexing - Efficient Semantic Search at Scale](6101-HNSW-Indexing.md)

---

## Next Steps

- Continue with: **[6201: Hybrid Search](./../6200-retrieval/6201-Hybrid-Search.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_6102: Semantic Similarity](../../../../experiments/EXP_6102_SIMILARITY.md)**
