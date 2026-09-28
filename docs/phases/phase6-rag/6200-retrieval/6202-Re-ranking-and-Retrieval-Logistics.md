---
Document ID: 6202
Title: Re-ranking and Retrieval Logistics
Phase: 6
Module: 6200
Last Updated: 2026-09-27
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'retrieval', 'hybrid-search', 'reranking']
---

# 6202: Re-ranking and Retrieval Logistics

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The RAG Pipeline](#the-rag-pipeline)
- [Reranking Models](#reranking-models)
- [Retrieval Strategies](#retrieval-strategies)
- [Query Expansion](#query-expansion)
- [Evaluation](#evaluation)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Trace the two-stage pipeline trade-off — a fast retriever casts a wide net (retrieve_n=100), a slow accurate reranker shrinks it to top_k=10, and one model cannot be both fast and accurate
- Run a cross-encoder reranker — score (query, document) pairs with `CrossEncoder.predict`, sort descending, and explain why it beats a bi-encoder on precision but costs a forward pass per pair
- Score with ColBERT's MaxSim rule — Σᵢ maxⱼ (qᵢ · dⱼ) over token embeddings in numpy, and know that full PLAID indexing is offline tooling (colbert-ai / RAGatouille), not per-document calls
- Pick a retrieval strategy by failure mode — dense (paraphrases, misses exact terms), sparse/BM25 (exact terms, no semantics), hybrid = retrieve 2k from each channel and fuse ranks with RRF
- Expand a query two ways — pseudo-relevance feedback pulls the top TF-IDF terms out of first-pass documents back into the query; LLM fan-out paraphrases then dedup per document by best score before reranking
- Score a run with AP / MAP / NDCG — AP sums precision at each relevant hit over |relevant|, MAP averages it over queries, and NDCG discounts graded relevance by log₂(rank+1) against the ideal ordering

---

## Abstract
Re-ranking improves retrieval quality by taking an initial set of documents and re-ordering them using more sophisticated (but slower) models.

## The RAG Pipeline

### Standard Pipeline
```text
Query → Retriever → Reranker → Generator
         (Fast)      (Slow)      (Slow)

1. Retriever: Get top 100 documents quickly
2. Reranker: Re-rank top 100 to top 10
3. Generator: Use top 10 for generation

Why: Retriever can't be accurate + fast
Solution: Two-stage retrieval
```

### Retrieval Stages
```python
class TwoStageRetriever:
    """
    Two-stage retrieval: Fast retrieval + Slow reranking
    """
    def __init__(self, corpus, retriever, reranker):
        self.corpus = corpus
        self.retriever = retriever    # Fast: BM25 or FAISS
        self.reranker = reranker      # Slow: Cross-encoder

    def retrieve(self, query, top_k=10, retrieve_n=100):
        """
        Stage 1: Retrieve N documents (fast)
        Stage 2: Rerank to top K (slow but accurate)
        """
        # Stage 1: Fast retrieval
        initial_results = self.retriever.search(query, k=retrieve_n)
        initial_docs = [self.corpus[idx] for idx, _ in initial_results]

        # Stage 2: Rerank
        reranked_docs = self.reranker.rerank(query, initial_docs)

        # Return top k
        return reranked_docs[:top_k]

# Usage — HybridSearch is the hybrid retriever from 6201-Hybrid-Search;
# CrossEncoderReranker is defined in the next section below
retriever = HybridSearch(corpus)  # Fast
reranker = CrossEncoderReranker()  # Slow but accurate

two_stage = TwoStageRetriever(corpus, retriever, reranker)
results = two_stage.retrieve("What is machine learning?", top_k=5, retrieve_n=100)
```

## Reranking Models

### Cross-Encoder Reranking
```python
from sentence_transformers import CrossEncoder
import torch

class CrossEncoderReranker:
    """
    Cross-encoder: Takes query+document, outputs relevance score
    More accurate but slower than bi-encoder
    """
    def __init__(self, model_name='ms-marco-MiniLM-L-6-v2'):
        self.model = CrossEncoder(model_name)
        self.model.eval()

    def rerank(self, query, documents, top_k=10):
        """
        Re-rank documents by relevance to query

        Documents: List of text strings
        Returns: Top k documents (sorted)
        """
        # Create query-document pairs
        pairs = [(query, doc) for doc in documents]

        # Score each pair
        with torch.no_grad():
            scores = self.model.predict(pairs)

        # Sort by score
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Return top k
        return [doc for doc, score in scored_docs[:top_k]]

# Usage
reranker = CrossEncoderReranker()

# Initial retrieval (e.g., from BM25)
initial_docs = [
    "Machine learning is a subset of AI",
    "I like eating pizza",
    "Deep learning uses neural networks",
    "Cats are cute animals",
]

# Rerank
top_docs = reranker.rerank("What is AI?", initial_docs, top_k=2)
print(top_docs)  # ML and Deep learning docs
```

### ColBERT Reranking
```python
import numpy as np

# ColBERT's scoring rule (late interaction): every query token takes its
# best-matching document token, then the maxima are summed
def maxsim_score(query_emb, doc_emb):
    """query_emb: (n_query_tokens, dim); doc_emb: (n_doc_tokens, dim)"""
    sims = query_emb @ doc_emb.T           # all-pairs token similarities
    return float(sims.max(axis=1).sum())   # max over doc tokens, sum over query tokens

class ColBERTReranker:
    """
    Late-interaction reranking over precomputed token embeddings.

    A full ColBERT index (PLAID) is offline tooling — colbert-ai or the
    RAGatouille wrapper builds it from a whole collection; there is no
    per-document index_doc call. The scoring rule itself, MaxSim, is
    cheap to apply to a shortlist once token embeddings exist.
    """
    def __init__(self, model_name='colbert-ir/colbertv2.0'):
        # Real deployments load this checkpoint with colbert-ai /
        # RAGatouille, which emits one embedding per token; the
        # embeddings are supplied per call here so the scoring rule
        # is runnable on its own
        self.model_name = model_name

    def rerank(self, query_emb, doc_embs, top_k=10):
        """query_emb: (n_q, dim); doc_embs: list of (n_d, dim) arrays.
        Returns [(doc_position, maxsim_score)] sorted descending."""
        scored = [
            (pos, maxsim_score(query_emb, d))
            for pos, d in enumerate(doc_embs)
        ]
        return sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]

# Usage — token embeddings normally come from a ColBERT checkpoint; any
# per-token vectors demonstrate the rule:
query_emb = np.array([[1.0, 0.0], [0.0, 1.0]])      # 2 query tokens
doc_embs = [
    np.array([[1.0, 0.1], [0.9, 0.0], [0.0, 0.9]]),  # doc A: strong match per token
    np.array([[0.2, 0.0], [0.0, 0.2]]),              # doc B: weak everywhere
]
ranked = ColBERTReranker().rerank(query_emb, doc_embs, top_k=2)
# [(0, 1.9), (1, 0.4)] — doc A first: q0's best match is [1.0, 0.1] (= 1.0),
# q1's best is [0.0, 0.9] (= 0.9), sum 1.9; doc B maxes at 0.2 + 0.2
print(ranked)

# Note: unlike a cross-encoder, ColBERT precomputes document token
# embeddings — query cost is one query encode + MaxSim, not a joint
# forward pass per (query, document) pair
```

## Retrieval Strategies

### Dense Retrieval
```python
# Dense: Pure vector similarity

# model: a sentence-transformer-style encoder (encode(text) → vector);
# index: an ANN index with search(q, k) → (scores, ids), e.g. FAISS
def dense_retrieval(query, model, index, k=10):
    """
    Retrieve using semantic search only
    """
    query_embedding = model.encode(query)
    scores, indices = index.search(query_embedding, k)

    return [(idx, scores[0][i]) for i, idx in enumerate(indices[0])]

# Pros:
# - Fast with HNSW
# - Semantic understanding
# - Good for paraphrases

# Cons:
# - Misses exact terms
# - Expensive embedding computation
```

### Sparse Retrieval
```python
# Sparse: BM25 keyword matching

def sparse_retrieval(query, bm25_index, k=10):
    """
    Retrieve using BM25 only
    """
    return bm25_index.search(query, k)

# Pros:
# - Fast with inverted index
# - Exact term matching
# - Easy to implement

# Cons:
# - No semantic understanding
# - Misses paraphrases
```

### Hybrid Retrieval
```python
# reciprocal_rank_fusion: the RRF definition from 6201-Hybrid-Search
def hybrid_retrieval(query, model, dense_index, sparse_index, k=10):
    """
    Combine dense and sparse by rank fusion (no score normalization)
    """
    # Dense results — over-retrieve 2k from each channel
    dense_results = dense_retrieval(query, model, dense_index, k=k*2)

    # Sparse results
    sparse_results = sparse_retrieval(query, sparse_index, k=k*2)

    # Combine with RRF
    fused = reciprocal_rank_fusion(dense_results, sparse_results)

    return fused[:k]
```

## Query Expansion

### Pseudo-Relevance Feedback
```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def pseudo_relevance_feedback(query, initial_results, corpus, top_n=10, expand_terms=3):
    """
    Expand query using terms from top retrieved documents

    initial_results: (doc_id, score) pairs from a first-pass search;
    corpus maps the ids back to document text

    Assumes top results are relevant (pseudo-relevance)
    """
    # Get top documents — initial_results carry ids, not text
    top_docs = [corpus[idx] for idx, _ in initial_results[:top_n]]

    vectorizer = TfidfVectorizer(max_features=100)
    tfidf = vectorizer.fit_transform(top_docs)

    # Get top terms
    feature_names = vectorizer.get_feature_names_out()
    mean_scores = np.asarray(tfidf.mean(axis=0)).ravel()

    top_terms_idx = mean_scores.argsort()[-expand_terms:][::-1]
    expansion_terms = [feature_names[i] for i in top_terms_idx]

    # Expand query
    expanded_query = f"{query} {' '.join(expansion_terms)}"

    return expanded_query

# Usage — bm25: a first-pass searcher (BM25 as in 6201-Hybrid-Search)
initial_results = bm25.search("machine learning", k=100)
expanded_query = pseudo_relevance_feedback("machine learning", initial_results, corpus)
final_results = bm25.search(expanded_query, k=10)
```

### LLM Query Expansion
```python
def llm_query_expansion(query, llm_client):
    """
    Use LLM to generate query variations
    """
    prompt = f"""
    Generate 3 variations of the following search query.
    Each variation should rephrase the query while preserving intent.

    Query: {query}

    Variations (one per line):
    """

    variations = llm_client.generate(prompt)

    # Combine original + variations (drop blank lines)
    return [query] + [v.strip() for v in variations.strip().split('\n') if v.strip()]


def dedup_by_best_score(results):
    """Collapse (doc_id, score) pairs gathered across query fan-outs:
    one entry per document, keeping its best score."""
    best = {}
    for idx, score in results:
        if idx not in best or score > best[idx]:
            best[idx] = score
    return sorted(best.items(), key=lambda x: x[1], reverse=True)

# Usage — llm_client: any chat client with a .generate(prompt) facade;
# reranker: CrossEncoderReranker above; bm25: a first-pass searcher;
# corpus: the document list the searcher indexed
queries = llm_query_expansion("What is machine learning?", llm_client)

# Retrieve with all queries
all_results = []
for q in queries:
    all_results.extend(bm25.search(q, k=10))

# Deduplicate — rerank expects texts, not id/score pairs
unique_results = dedup_by_best_score(all_results)
final_results = reranker.rerank(
    queries[0],
    [corpus[idx] for idx, _ in unique_results],
)
```

## Evaluation

### Mean Average Precision (MAP)
```python
def average_precision(retrieved_docs, relevant_docs):
    """
    Average Precision: Area under precision-recall curve

    retrieved_docs: List of retrieved document indices
    relevant_docs: Set of relevant document indices
    """
    precision_scores = []
    num_relevant = 0

    for i, doc in enumerate(retrieved_docs):
        if doc in relevant_docs:
            num_relevant += 1
            precision = num_relevant / (i + 1)
            precision_scores.append(precision)

    if not precision_scores:
        return 0.0

    # Denominator is |relevant|: relevant docs never retrieved cap AP
    # below 1.0 (this is AP over the full relevance set, not AP@k)
    return sum(precision_scores) / len(relevant_docs)

def mean_average_precision(queries, retriever):
    """
    MAP across multiple queries
    """
    ap_scores = []

    for query, relevant_docs in queries:
        retrieved = retriever.search(query, k=100)
        retrieved_ids = [idx for idx, _ in retrieved]

        ap = average_precision(retrieved_ids, relevant_docs)
        ap_scores.append(ap)

    return sum(ap_scores) / len(ap_scores)
```

### Normalized Discounted Cumulative Gain (NDCG)
```python
import math

def ndcg(retrieved_docs, relevance_scores, k=10):
    """
    NDCG: Accounts for graded relevance

    retrieved_docs: List of retrieved document indices
    relevance_scores: Dict mapping doc_id → relevance (0-3)
    k: Cutoff rank
    """
    # DCG: Discounted Cumulative Gain
    dcg = 0
    for i, doc in enumerate(retrieved_docs[:k]):
        relevance = relevance_scores.get(doc, 0)
        dcg += (2**relevance - 1) / math.log2(i + 2)

    # IDCG: Ideal DCG (sorted by relevance)
    ideal_relevances = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = 0
    for i, relevance in enumerate(ideal_relevances):
        idcg += (2**relevance - 1) / math.log2(i + 2)

    if idcg == 0:
        return 0.0

    return dcg / idcg
```


---

## References

### Related PROJECT-OMEGA Documents

- [6101: HNSW Indexing - Efficient Semantic Search at Scale](../6100-vector/6101-HNSW-Indexing.md)
- [6201: Hybrid Search - Combining Keyword and Semantic Search](6201-Hybrid-Search.md)
- [6203: Advanced Retrieval Techniques](6203-Advanced-Retrieval.md)

---

## Next Steps

- Continue with: **[6301: Neo4j and Knowledge Graphs](./../6300-context/6301-Neo4j-and-Knowledge-Graphs.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_6202: Re-ranking](../../../../experiments/EXP_6202_RERANK.md)**
