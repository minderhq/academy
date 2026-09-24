---
Document ID: 6202
Title: Re-ranking and Retrieval Logistics
Phase: 6
Module: 6200
Last Updated: 2026-09-24
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

- Explain The RAG Pipeline
- Explain Reranking Models
- Explain Retrieval Strategies
- Explain Query Expansion
- Measure and evaluate Evaluation

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

# Usage
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
# ColBERT: Late interaction model
# More accurate than cross-encoder for longer documents

class ColBERTReranker:
    """
    ColBERT: Token-level interaction between query and document
    """
    def __init__(self, model_name='colbert-ir/colbertv2.0'):
        from colbert import Indexer, Searcher
        self.model_name = model_name
        self.indexer = None

    def build_index(self, documents):
        """Build ColBERT index"""
        # This is expensive, done offline
        import os
        os.makedirs('colbert_index', exist_ok=True)

        self.indexer = Indexer(self.model_name, 'colbert_index')
        for idx, doc in enumerate(documents):
            self.indexer.index_doc(idx, doc)

    def rerank(self, query, documents, top_k=10):
        """Rerank using ColBERT"""
        from colbert import Searcher

        searcher = Searcher(self.model_name, index='colbert_index')

        # Search
        results = searcher.search(query, k=top_k)

        return [documents[r[0]] for r in results]

# Note: ColBERT is slower but more accurate than cross-encoder
# Use for: Final re-ranking stage when accuracy critical
```

## Retrieval Strategies

### Dense Retrieval
```python
# Dense: Pure vector similarity

def dense_retrieval(query, index, k=10):
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
def hybrid_retrieval(query, dense_index, sparse_index, k=10, alpha=0.5):
    """
    Combine dense and sparse
    """
    # Dense results
    dense_results = dense_retrieval(query, dense_index, k=k*2)

    # Sparse results
    sparse_results = sparse_retrieval(query, sparse_index, k=k*2)

    # Combine with RRF
    fused = reciprocal_rank_fusion(dense_results, sparse_results)

    return fused[:k]
```

## Query Expansion

### Pseudo-Relevance Feedback
```python
def pseudo_relevance_feedback(query, initial_results, top_n=10, expand_terms=3):
    """
    Expand query using terms from top retrieved documents

    Assumes top results are relevant (pseudo-relevance)
    """
    # Get top documents
    top_docs = [doc for doc, score in initial_results[:top_n]]

    # Extract important terms
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(max_features=100)
    tfidf = vectorizer.fit_transform(top_docs)

    # Get top terms
    feature_names = vectorizer.get_feature_names_out()
    mean_scores = tfidf.mean(axis=0).A1

    top_terms_idx = mean_scores.argsort()[-expand_terms:][::-1]
    expansion_terms = [feature_names[i] for i in top_terms_idx]

    # Expand query
    expanded_query = f"{query} {' '.join(expansion_terms)}"

    return expanded_query

# Usage
initial_results = bm25.search("machine learning", k=100)
expanded_query = pseudo_relevance_feedback("machine learning", initial_results)
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

    # Combine original + variations
    all_queries = [query] + variations.strip().split('\n')

    return all_queries

# Usage
queries = llm_query_expansion("What is machine learning?", gpt4)

# Retrieve with all queries
all_results = []
for q in queries:
    all_results.extend(bm25.search(q, k=10))

# Deduplicate and rerank
unique_results = deduplicate(all_results)
final_results = reranker.rerank(query, unique_results)
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

### Related ai-engineering-curriculum Documents

- [6201: Hybrid Search - Combining Keyword and Semantic Search](6201-Hybrid-Search.md)
- [6203: Advanced Retrieval Techniques](6203-Advanced-Retrieval.md)

---

## Next Steps

- Continue with: **[6301: Neo4j and Knowledge Graphs](./../6300-context/6301-Neo4j-and-Knowledge-Graphs.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [6201: Hybrid Search](./6201-Hybrid-Search.md)
- [6101: HNSW Indexing](../6100-Vector/6101-HNSW-Indexing.md)
- [6301: Neo4j GraphRAG](../6300-context/6301-Neo4j-and-Knowledge-Graphs.md)

**Experiment Template:** `experiments/EXP_6202_RERANK.md"
