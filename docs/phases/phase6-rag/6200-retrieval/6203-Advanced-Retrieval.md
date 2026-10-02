---
Document ID: 6203
Title: "6203: Advanced Retrieval Techniques"
Phase: 6
Module: 6200
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'retrieval', 'hybrid-search', 'reranking']
---

# 6203: Advanced Retrieval Techniques

## Abstract

Single-stage dense retrieval leaves accuracy on the table. This document
covers the techniques stacked on top of a base index: query transformation
(expansion, multi-query, HyDE), cross-encoder re-ranking, multi-stage
pipelines, contextual compression, and domain adaptation — plus how to
measure each stage's contribution with retrieval metrics.

---

## Table of Contents

- [1. Overview](#1-overview)
- [Learning Objectives](#learning-objectives)
- [2. Base Pipeline and Where It Fails](#2-base-pipeline-and-where-it-fails)
- [3. Query Transformation](#3-query-transformation)
- [4. Cross-Encoder Re-Ranking](#4-cross-encoder-re-ranking)
- [5. Multi-Stage Retrieval Pipeline](#5-multi-stage-retrieval-pipeline)
- [6. Contextual Compression](#6-contextual-compression)
- [7. Domain Adaptation](#7-domain-adaptation)
- [8. Evaluation](#8-evaluation)
- [9. Troubleshooting](#9-troubleshooting)
- [Summary](#summary)
- [10. References](#10-references)

---

## 1. Overview

### 1.1 Prerequisites

- [6201: Hybrid Search](./6201-Hybrid-Search.md) - dense + sparse fusion
- [6202: Re-ranking and Retrieval Logistics](./6202-Re-ranking-and-Retrieval-Logistics.md) - reranker basics
- [6101: HNSW Indexing](../6100-vector/6101-HNSW-Indexing.md) - vector index mechanics

## Learning Objectives
After completing this document, you will:
- ✅ Diagnose which pipeline stage causes bad retrieval (query vs index vs rank)
- ✅ Apply query rewriting, multi-query, and HyDE with cost awareness
- ✅ Configure a retrieve-then-rerank pipeline within a latency budget
- ✅ Compress retrieved context to fit more evidence per prompt
- ✅ Track recall@k / MRR / nDCG per stage to justify each addition

---

## 2. Base Pipeline and Where It Fails

```text
Base: query ──embed──► ANN search ──► top-k chunks ──► prompt
                     (HNSW, cosine)

Failure modes:
  1. Query mismatch   : user wording ≠ document wording (vocabulary gap)
  2. Lost in the middle: right chunk retrieved but buried at position 20
  3. Chunk dilution   : right chunk present but its key sentence is
                        diluted by boilerplate inside the chunk
  4. Homogeneous noise: k similar-but-useless chunks crowd out the useful one
```

Each advanced technique targets one failure mode: query transformation →
(1), re-ranking → (2) and (4), contextual compression → (3).

---

## 3. Query Transformation

### 3.1 Multi-Query Expansion

Generate N paraphrases, retrieve for each, fuse results (RRF, see
[6201](./6201-Hybrid-Search.md)):

```python
MULTI_QUERY = """Rewrite the question as {n} diverse search queries.
Question: {q}
Return one query per line."""

def multi_query_retrieve(llm, index, embed, q, n=4, k=20):
    variants = [q] + llm(MULTI_QUERY.format(n=n, q=q)).strip().split("\n")
    results = {}
    for v in variants:
        for rank, doc in enumerate(index.search(embed(v), k=k)):
            results.setdefault(doc.id, []).append(rank)
    # Reciprocal Rank Fusion
    return sorted(results, key=lambda i: -sum(1/(60+r) for r in results[i]))
```

- Cost: N× index queries + 1 LLM call (~200-500 ms)
- Strongest for short, ambiguous user questions

### 3.2 HyDE: Hypothetical Document Embeddings

Instead of expanding the *question*, generate a fake *answer* and embed
that — answers live closer to documents in embedding space than questions do:

```python
def hyde(llm, index, embed, q, k=10):
    fake_doc = llm(f"Write a short paragraph answering: {q}")
    return index.search(embed(fake_doc), k=k)
```

- Big win when questions and documents have systematically different
  registers (chat questions vs formal wiki)
- Watch for hallucinated premises in the fake doc steering retrieval
  wrong — combine with the original query rather than replacing it

### 3.3 Choosing Transformations

| Transformation | Cost | Best when |
|----------------|------|-----------|
| None (baseline) | 0 | Queries are already keyword-rich |
| Synonym/keyword expansion | ~0 | Domain jargon vs user wording gap |
| Multi-query + RRF | 1 LLM call | Ambiguous short questions |
| HyDE | 1 LLM call | Question/answer register mismatch |
| Step-back (abstract then specific) | 1 LLM call | "Why"-questions needing context |

---

## 4. Cross-Encoder Re-Ranking

Bi-encoder retrieval embeds the query once and compares vectors — fast but
coarse. A cross-encoder scores each (query, chunk) pair jointly, seeing
token-level interactions — accurate but O(k) model calls:

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

def rerank(query, candidates, top_n=5):
    pairs = [(query, c.text) for c in candidates]
    scores = reranker.predict(pairs)              # [k]
    ranked = sorted(zip(candidates, scores), key=lambda t: -t[1])
    return ranked[:top_n]

# pipeline: ANN top-50 -> rerank -> top-5
```

**Latency budgeting:**

```text
End-to-end budget: ~1.5 s
  embedding query        ~20 ms
  ANN top-50             ~10-30 ms
  cross-encoder 50 pairs ~200-800 ms  <- dominates; tune k_in, model size
  LLM generation         remainder
```

- Rerank depth (k_in) is the main lever: 50→100 doubles rerank time for
  a small recall gain — measure, don't assume
- Smaller cross-encoders (e.g., MiniLM-class) on GPU keep 100-pair rerank
  under ~100 ms
- Late-interaction models (ColBERT-style) sit between the two: per-token
  vectors, cheap MaxSim scoring, near-cross-encoder quality

---

## 5. Multi-Stage Retrieval Pipeline

```text
            ┌────────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐
 query ───► │ transform  │──►│ retrieve │──►│  rerank   │──►│ compress │──► prompt
            │ (§3)       │   │ hybrid,  │   │ (§4)      │   │ (§6)     │
            │            │   │ k=50-100 │   │ -> top 5  │   │          │
            └────────────┘   └──────────┘   └───────────┘   └──────────┘
             vocabulary gap   recall        precision       token budget
```

**Where:**
- **Recall stage** is deliberately loose (large k, cheap scoring) — its
  job is to not miss the answer
- **Precision stage** is expensive per item but sees few items
- Each stage should be justified by a metric delta (Section 8), not vibes

---

## 6. Contextual Compression

Retrieved chunks carry boilerplate. Compress before the prompt:

- **Extractive**: rank sentences in each chunk against the query (embed
  sentences, keep top-m) — cheap, no hallucination risk
- **LLM-based**: ask a small model to extract only query-relevant spans
  — better precision, adds latency and a failure mode
- **Token-level**: LLMLingua-style perplexity pruning, ~2-5× compression
  with modest quality loss

```python
def extractive_compress(query, chunk, embed, m=3):
    sents = split_sentences(chunk)
    qv = embed(query)
    scored = sorted(sents, key=lambda s: -cos(qv, embed(s)))
    return " ... ".join(scored[:m])
```

> **⚠️ Compression Trade-off:**
> Aggressive compression raises the chance of dropping the one fact the
> LLM needed. Keep the *original* chunk ids so the generation stage can
> fall back to full text (or a re-fetch) when the compressed answer
> cites nothing.

---

## 7. Domain Adaptation

- **Fine-tune the embedding model** on domain pairs (query → relevant
  doc) mined from click logs or LLM-synthesized pairs — usually the
  highest-ROI domain investment (see contrastive training in
  [6102](../6100-vector/6102-Semantic-Similarity.md))
- **Keyword dictionaries**: map domain abbreviations/synonyms at query
  time into the sparse leg of hybrid search
- **Structured sidecar**: extract metadata (product ids, dates, sections)
  and filter *before* vector search — metadata filtering beats any
  embedding trick when the constraint is exactly representable

---

## 8. Evaluation

Label a golden set first: **(query, relevant_doc_ids)** pairs, 100-500
rows covering your taxonomy. Then measure per stage:

| Metric | Question it answers | Typical target |
|--------|--------------------|----------------|
| Recall@k | Is the answer in the top-k at all? | ≥0.90 @ k=50 |
| MRR | How high does the first hit rank? | ≥0.7 after rerank |
| nDCG@k | Graded ranking quality | ≥0.8 after rerank |
| P95 latency | Can we afford the stages? | <1.5 s end-to-end |

```python
def recall_at_k(results, relevant, k):
    return sum(len(set(r[:k]) & rel) > 0 for r, rel in zip(results, relevant)) / len(results)

def mrr(results, relevant, k):
    def rr(r):
        for i, d in enumerate(r[:k], 1):
            if d in rel:
                return 1 / i
        return 0
    return sum(rr(r) for r in results) / len(results)
```

Ablate: baseline → +query transform → +rerank → +compression. Keep a
stage only if its metric delta survives on the golden set.

---

## 9. Troubleshooting

| Symptom | Likely Stage | Fix |
|---------|--------------|-----|
| Right doc in corpus, never retrieved | Query transformation | HyDE or multi-query; check embedding model domain fit |
| Right doc retrieved, answer still wrong | Reranking / position | Rerank into top-3-5; move best hit first |
| Slow P95 latency | Rerank depth | Lower k_in, smaller reranker, batch pairs on GPU |
| Great on easy queries, poor on jargon | Domain adaptation | Fine-tune embeddings; expand sparse dictionary |
| Compressed context loses the fact | Compression | Lower compression ratio; keep fallback re-fetch |
| Same near-duplicate chunks flood top-k | Index/dedup | Near-dup filtering at ingest or diversity re-ranking |

---

## Summary

Single-stage dense retrieval leaves accuracy on the table, and this lesson is the stack that recovers it: query transformation (expansion, multi-query, HyDE), cross-encoder re-ranking, multi-stage pipelines, contextual compression, and domain adaptation - each measured with its own retrieval metrics so every stage justifies its latency. The rule it leaves: build the baseline first, then add stages one at a time with measurement - an unmeasured pipeline stage is a latency tax with no proof of purchase.

## 10. References

### Academic Papers
- [1] Gao et al. "Precise Zero-Shot Dense Retrieval without Relevance Labels" (HyDE). ACL, 2023.
- [2] Nogueira & Cho. "Passage Re-ranking with BERT". 2019.
- [3] Khattab & Zaharia. "ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction". SIGIR, 2020.
- [4] Jiang et al. "LLMLingua: Compressing Prompts for Accelerated Inference". EMNLP, 2023.
- [5] Liu et al. "Lost in the Middle: How Language Models Use Long Contexts". TACL, 2024.

### Related PROJECT-OMEGA Documents
- [6201: Hybrid Search](./6201-Hybrid-Search.md) - fusion foundations
- [6202: Re-ranking and Retrieval Logistics](./6202-Re-ranking-and-Retrieval-Logistics.md) - reranker operations
- [6301: Neo4j and Knowledge Graphs](../6300-context/6301-Neo4j-and-Knowledge-Graphs.md) - graph-based retrieval
- [6302: CAG Long Context Architectures](../6300-context/6302-CAG-Long-Context-Architectures.md) - long-context alternative

---

## Next Steps

- Deepen: **[6301: Neo4j and Knowledge Graphs](../6300-context/6301-Neo4j-and-Knowledge-Graphs.md)**
- Alternative: **[6302: CAG Long Context Architectures](../6300-context/6302-CAG-Long-Context-Architectures.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**

---

**Document ID:** 6203
**Status:** Complete
**Related Documents:** [6201, 6202, 6301, 6302]
