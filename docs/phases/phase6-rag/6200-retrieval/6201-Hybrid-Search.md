---
Document ID: 6201
Title: "6201: Hybrid Search - Combining Keyword and Semantic Search"
Phase: 6
Module: 6200
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'retrieval', 'hybrid-search', 'reranking']
---

# 6201: Hybrid Search - Combining Keyword and Semantic Search

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Keyword Search (BM25)](#keyword-search-bm25)
- [Semantic Search (Vector)](#semantic-search-vector)
- [Hybrid Search](#hybrid-search)
- [Dense vs Sparse Retrieval](#dense-vs-sparse-retrieval)
- [Implementation with Qdrant](#implementation-with-qdrant)
- [Optimizing Alpha](#optimizing-alpha)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Trace the BM25 ranking — TF saturation (k1), document-length normalization (b), and the +1-guarded IDF log((N−df+0.5)/(df+0.5)+1) — and read a real tie: "cat" hits doc 0 while "pets" hits doc 3, both scoring 1.157 because the terms share one IDF
- Run dense retrieval end-to-end — SentenceTransformer encode, L2-normalize to the unit sphere, FAISS IndexFlatIP where inner product equals cosine similarity
- Fuse the two channels two ways — score-level linear combination α × semantic + (1−α) × bm25 over per-query min-max-normalized scores, and rank-based Reciprocal Rank Fusion Σ 1/(k+rank+1) that needs no score normalization at all
- Choose dense vs sparse vs hybrid by failure mode — exact terms and rare tokens favor BM25, paraphrase and synonymy favor embeddings; late fusion retrieves separately then fuses, early fusion scores both in a single pass
- Ship a true Qdrant hybrid collection — named dense + sparse vector spaces (`SparseVectorParams`), a `PointStruct` carrying BOTH vectors, and server-side RRF via `query_points` with `prefetch` + `FusionQuery(fusion=Fusion.RRF)` (client.search is REMOVED in qdrant-client 1.19)
- Tune α empirically — sweep 0.0–1.0, score each weight with MAP@10 (mean Average Precision over a labeled query set), and read the per-query-type guidance (0.3–0.5 general, higher for conceptual)

---

## Abstract
Hybrid search combines traditional keyword search (BM25) with semantic vector search to get the best of both approaches: exact term matching + conceptual understanding.

## Keyword Search (BM25)

### BM25 Algorithm
```python
import math
from collections import Counter, defaultdict
import numpy as np

class BM25:
    """
    BM25 ranking function for keyword search
    """
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.k1 = k1  # Term saturation parameter
        self.b = b    # Length normalization
        self.corpus = corpus
        self.doc_freqs = []
        self.idf = {}
        self.doc_lens = []

        # Build index
        self._build_index()

    def _build_index(self):
        """Build document frequency and IDF"""
        # Document frequency: how many docs contain each term
        df = defaultdict(int)

        for doc in self.corpus:
            tokens = self._tokenize(doc)
            self.doc_lens.append(len(tokens))
            unique_tokens = set(tokens)

            for token in unique_tokens:
                df[token] += 1

            self.doc_freqs.append(Counter(tokens))

        # Average document length
        self.avg_doc_len = sum(self.doc_lens) / len(self.doc_lens)

        # IDF: Inverse document frequency
        N = len(self.corpus)
        for token, freq in df.items():
            self.idf[token] = math.log((N - freq + 0.5) / (freq + 0.5) + 1)

    def _tokenize(self, text):
        """Simple tokenizer (replace with proper tokenizer)"""
        return text.lower().split()

    def score(self, query, doc_idx):
        """Compute BM25 score for query-document pair"""
        score = 0
        query_tokens = self._tokenize(query)
        doc_freqs = self.doc_freqs[doc_idx]
        doc_len = self.doc_lens[doc_idx]

        for token in query_tokens:
            if token in doc_freqs:
                # Term frequency in document
                tf = doc_freqs[token]

                # IDF
                idf = self.idf.get(token, 0)

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * (doc_len / self.avg_doc_len)
                )

                score += idf * (numerator / denominator)

        return score

    def search(self, query, k=10):
        """Return top k documents for query"""
        scores = [self.score(query, i) for i in range(len(self.corpus))]
        top_indices = np.argsort(scores)[::-1][:k]

        return [
            (idx, scores[idx])
            for idx in top_indices
        ]

# Usage
corpus = [
    "The cat sat on the mat",
    "Dogs are loyal and friendly",
    "Machine learning uses neural networks",
    "Cats and dogs are popular pets",
]

bm25 = BM25(corpus)
results = bm25.search("cat pets", k=3)
# [(3, 1.1567), (0, 1.1567), (2, 0.0)] — an exact tie for first: "cat"
# hits only doc 0 and "pets" only doc 3, and both terms share one IDF
# (each appears in 1 of 4 docs). Docs 1 and 2 score 0.0; a zero-score
# doc still appears in the ranking because search() scores every doc.
print(results)
```

## Semantic Search (Vector)

### Using Sentence Transformers
```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class SemanticSearch:
    """
    Semantic search using embeddings
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []

    def index_documents(self, documents):
        """Build FAISS index for documents"""
        self.documents = documents

        # Encode documents
        embeddings = self.model.encode(documents)

        # Build index
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # Inner product (dot product)

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        self.index.add(embeddings.astype('float32'))

    def search(self, query, k=10):
        """Search for similar documents"""
        # Encode query
        query_embedding = self.model.encode([query])

        # Normalize
        faiss.normalize_L2(query_embedding)

        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), k)

        return [
            (idx, scores[0][i])
            for i, idx in enumerate(indices[0])
        ]

# Usage — corpus comes from the BM25 usage in the section above
semantic_search = SemanticSearch()
semantic_search.index_documents(corpus)
results = semantic_search.search("feline animals", k=3)
```

## Hybrid Search

### Combining BM25 and Semantic
```python
# BM25 and SemanticSearch are defined in the two sections above;
# corpus comes from the BM25 usage there.

class HybridSearch:
    """
    Hybrid search: BM25 + Semantic
    """
    def __init__(self, corpus, alpha=0.5):
        self.corpus = corpus
        self.alpha = alpha  # Weight for semantic vs keyword

        # Initialize both searchers
        self.bm25 = BM25(corpus)
        self.semantic = SemanticSearch()
        self.semantic.index_documents(corpus)

    def search(self, query, k=10):
        """
        Hybrid search with score fusion

        Implemented here: linear combination α × semantic +
        (1-α) × bm25 over min-max-normalized scores. Rank-based
        fusion (RRF) is the section below — it needs no score
        normalization at all.
        """
        # BM25 scores
        bm25_results = self.bm25.search(query, k=len(self.corpus))
        bm25_scores = {idx: score for idx, score in bm25_results}

        # Semantic scores
        semantic_results = self.semantic.search(query, k=len(self.corpus))
        semantic_scores = {idx: score for idx, score in semantic_results}

        # Normalize scores
        bm25_normalized = self._normalize_scores(bm25_scores)
        semantic_normalized = self._normalize_scores(semantic_scores)

        # Combine
        combined_scores = {}
        all_indices = set(bm25_normalized.keys()) | set(semantic_normalized.keys())

        for idx in all_indices:
            bm25_score = bm25_normalized.get(idx, 0)
            semantic_score = semantic_normalized.get(idx, 0)

            # Linear combination
            combined_scores[idx] = (
                self.alpha * semantic_score +
                (1 - self.alpha) * bm25_score
            )

        # Sort and return top k
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]

        return [(idx, score) for idx, score in sorted_results]

    def _normalize_scores(self, score_dict):
        """Min-max normalization to [0, 1]"""
        if not score_dict:
            return {}

        min_score = min(score_dict.values())
        max_score = max(score_dict.values())

        if max_score == min_score:
            return {idx: 1.0 for idx in score_dict}

        return {
            idx: (score - min_score) / (max_score - min_score)
            for idx, score in score_dict.items()
        }

# Usage
hybrid = HybridSearch(corpus, alpha=0.5)
results = hybrid.search("cat pets", k=3)
for idx, score in results:
    print(f"{score:.4f}: {corpus[idx]}")
```

### Reciprocal Rank Fusion (RRF)
```python
from collections import defaultdict

def reciprocal_rank_fusion(bm25_results, semantic_results, k=60):
    """
    Reciprocal Rank Fusion: Rank-based fusion

    RRF = Σ (1 / (k + rank))

    Benefits:
    - Doesn't require score normalization
    - Robust to score scale differences
    - Works well across different retrieval methods
    """
    fused_scores = defaultdict(float)

    # BM25 ranks
    for rank, (idx, _) in enumerate(bm25_results):
        fused_scores[idx] += 1 / (k + rank + 1)

    # Semantic ranks
    for rank, (idx, _) in enumerate(semantic_results):
        fused_scores[idx] += 1 / (k + rank + 1)

    # Sort
    sorted_results = sorted(
        fused_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return sorted_results

# Usage — bm25 and semantic_search come from the sections above
bm25_results = bm25.search("cat pets", k=10)
semantic_results = semantic_search.search("cat pets", k=10)

fused = reciprocal_rank_fusion(bm25_results, semantic_results)
```

## Dense vs Sparse Retrieval

### Comparison
```yaml
Sparse Retrieval (BM25):
  - Lexical matching
  - Exact terms
  - Fast with inverted index
  - Good for: Exact phrases, specific terms

Dense Retrieval (Semantic):
  - Vector embeddings
  - Semantic similarity
  - Computationally expensive
  - Good for: Concepts, paraphrases, synonyms

Hybrid:
  - Best of both
  - Captures exact matches + concepts
  - More complex implementation
```

### Late Fusion vs Early Fusion
```python
import numpy as np

# Late Fusion (separate retrieval, then combine)
# reciprocal_rank_fusion comes from the RRF section above
def late_fusion(query, bm25, semantic, k=10):
    """Retrieve separately, then fuse"""
    bm25_docs = bm25.search(query, k=k)
    semantic_docs = semantic.search(query, k=k)

    # Combine results
    return reciprocal_rank_fusion(bm25_docs, semantic_docs)

# Early Fusion (combine representations)
class EarlyFusionIndex:
    """
    Combine BM25 and semantic in a single scoring pass
    """
    def __init__(self, corpus):
        self.corpus = corpus

        # Sparse features (BM25)
        self.bm25 = BM25(corpus)

        # Dense features (embeddings) — keep the model so the query
        # side uses the SAME encoder; normalize so dot product = cosine
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings = self.model.encode(corpus).astype('float32')
        faiss.normalize_L2(self.embeddings)

    def search(self, query, k=10, alpha=0.5):
        # Query features — same encoder, same normalization
        query_embedding = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)

        # Combine both signals
        scores = []
        for idx, doc in enumerate(self.corpus):
            # BM25 score (unbounded, typically 0-15)
            bm25_score = self.bm25.score(query, idx)

            # Semantic score (cosine, [-1, 1] after normalization)
            semantic_score = float(np.dot(
                query_embedding[0],
                self.embeddings[idx]
            ))

            # Combined — NOTE: the two channels live on different raw
            # scales; a principled fusion normalizes both (HybridSearch
            # above) or fuses ranks instead (RRF below)
            combined = alpha * semantic_score + (1 - alpha) * bm25_score
            scores.append((idx, combined))

        return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
```

## Implementation with Qdrant

### Qdrant Hybrid Search
```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Fusion,
    FusionQuery,
    PointStruct,
    Prefetch,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

# Connect to Qdrant (self-hosted Docker)
client = QdrantClient(url="http://localhost:6333")

# A true hybrid collection: a named DENSE vector space (semantic)
# plus a named SPARSE vector space (BM25-style) on the same collection
collection_name = "hybrid_docs"
client.create_collection(
    collection_name=collection_name,
    vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
    sparse_vectors_config={"text": SparseVectorParams()},
)

# BM25-style bag of words as a SparseVector. Python's hash() is salted
# per process for strings — fine here, indices only need to be
# consistent within one run; production stacks use an IDF-weighted
# tokenizer (e.g. fastembed's bm25 or a SPLADE model) instead
def tokenize(text):
    tokens = text.lower().split()
    return SparseVector(
        indices=[abs(hash(t)) % 100000 for t in tokens],
        values=[1.0] * len(tokens),
    )

# Index documents — corpus and semantic_model come from the sections
# above. ONE PointStruct carries BOTH vectors under their names.
for idx, doc in enumerate(corpus):
    client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=idx,
                vector={
                    "dense": semantic_model.encode(doc).tolist(),
                    "text": tokenize(doc),
                },
                payload={"text": doc},
            )
        ]
    )

query = "feline pets"

# Hybrid search: prefetch BOTH channels, fuse server-side with RRF.
# client.search() was deprecated in 1.10 and is REMOVED by 1.19
# (AttributeError) — query_points() with prefetch + FusionQuery is
# Qdrant's hybrid-search API
search_results = client.query_points(
    collection_name=collection_name,
    prefetch=[
        Prefetch(query=tokenize(query), using="text", limit=20),
        Prefetch(query=semantic_model.encode(query).tolist(), using="dense", limit=20),
    ],
    query=FusionQuery(fusion=Fusion.RRF),
    limit=10,
    with_payload=["text"],
).points

for point in search_results:
    print(f"{point.score:.4f}: {point.payload['text']}")
```

## Optimizing Alpha

### Finding Optimal Weight
```python
import numpy as np

def average_precision(retrieved, relevant, k=10):
    """
    Average Precision@k: mean of precision@i over each relevant hit
    in the top-k ranking
    """
    relevant = set(relevant)
    retrieved_ids = [idx for idx, _ in retrieved[:k]]
    hits, sum_precision = 0, 0.0
    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant:
            hits += 1
            sum_precision += hits / i
    return sum_precision / len(relevant) if relevant else 0.0


def optimize_alpha(corpus, ground_truth):
    """
    Find the optimal alpha by sweeping 0.0-1.0 and scoring each weight
    with MAP@10: the mean of Average Precision over the query set

    ground_truth: list of (query, relevant_doc_ids) pairs
    """
    alphas = np.linspace(0, 1, 11)  # 0.0, 0.1, ..., 1.0
    results = []

    for alpha in alphas:
        # HybridSearch comes from the Hybrid Search section above
        hybrid = HybridSearch(corpus, alpha=alpha)

        # Evaluate on queries
        map_score = 0
        for query, relevant_docs in ground_truth:
            retrieved = hybrid.search(query, k=10)
            map_score += average_precision(retrieved, relevant_docs, k=10)

        map_score /= len(ground_truth)
        results.append((float(alpha), map_score))

    # Return best alpha (and the full sweep for plotting)
    best_alpha = max(results, key=lambda x: x[1])[0]
    return best_alpha, results

# Typical findings:
# - Alpha = 0.3-0.5 for general queries
# - Alpha = 0.7-0.9 for conceptual queries
# - Alpha = 0.1-0.3 for specific term queries
```


---

## Summary

Hybrid search combines BM25 keyword retrieval with semantic vector search so exact term matching and conceptual understanding stop being a trade-off. This lesson implemented BM25 from first principles (TF-IDF saturation and length normalization), compared it with dense retrieval's failure modes - rare terms and exact identifiers for keywords, paraphrase and intent for vectors - and walked the reciprocal rank fusion that merges the two result lists. The rule it leaves: neither retriever dominates the other; fusion beats either alone because their failures are nearly disjoint.

## References

### Related Minder Academy Documents

- [6101: HNSW Indexing - Efficient Semantic Search at Scale](../6100-vector/6101-HNSW-Indexing.md)
- [6202: Re-ranking and Retrieval Logistics](6202-Re-ranking-and-Retrieval-Logistics.md)
- [6203: Advanced Retrieval Techniques](6203-Advanced-Retrieval.md)

---

## Next Steps

- Continue with: **[6202: Re-ranking](./6202-Re-ranking-and-Retrieval-Logistics.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_6201: Hybrid Search](../../../../experiments/EXP_6201_HYBRID_SEARCH.md)**
