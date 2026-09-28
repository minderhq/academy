---
Document ID: 6200-RETRIEVAL-README
Title: "6200: Retrieval Strategies"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Beginner
---

# 6200: Retrieval Strategies

## Module Overview

This module covers advanced retrieval techniques for RAG systems, including hybrid search, re-ranking, and retrieval optimization. You'll learn to build high-quality retrieval pipelines that find the most relevant context.

**Why This Matters:**
- Pure vector search misses keyword-specific information
- Re-ranking can significantly improve retrieval quality
- Hybrid search combines the best of semantic and lexical search
- Retrieval is the bottleneck for RAG quality

## Learning Objectives

After completing this module, you will be able to:

- **Hybrid Search**: Combine semantic and keyword search
- **Re-ranking**: Improve retrieved results with cross-encoders
- **Query Expansion**: Enhance queries for better retrieval
- **Retrieval Logistics**: Optimize chunk size, top-K, and overlap
- **Evaluation**: Measure retrieval quality with precision/recall

## Module Contents

### 6201: Hybrid Search
**Semantic + Lexical Search Fusion**

- Vector search vs keyword search (BM25)
- Reciprocal Rank Fusion (RRF)
- Dense vs sparse retrieval
- Learning to rank
- Query understanding and expansion

**Experiments:**
- Implement BM25 keyword search
- Build hybrid search pipeline
- Compare fusion strategies
- Measure quality improvements

### 6202: Re-ranking and Retrieval Logistics
**Two-Stage Retrieval Optimization**

- Re-ranking with cross-encoders
- Chunking strategies and window sizes
- Top-K selection and tuning
- Context window optimization
- Retrieval evaluation metrics

**Experiments:**
- Implement re-ranking pipeline
- Compare chunking strategies
- Optimize retrieval parameters
- Build evaluation framework

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 6100: Vector Embeddings (semantic search)
- [ ] Module 3200: Embeddings (embedding models)
- [ ] Python and information retrieval basics
- [ ] Understanding of RAG fundamentals
- [ ] Familiarity with search metrics

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** Hybrid search, re-ranking, retrieval optimization
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Retrieval pipeline projects
- **Duration:** 6-8 hours
- **Topics:**
  - Build hybrid search system
  - Implement re-ranking
  - Optimize chunking strategies
  - Evaluate retrieval quality
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **6100: Vector Embeddings** (semantic search)
- **6300: Context** (context window management)
- **6400: Vector Databases** (production retrieval)
- **6500: MLOps Pipelines** (retrieval at scale)

## Time Commitment

| Activity | Time |
|----------|------|
| Reading (6201) | 3 hours |
| Experiments (6201) | 3 hours |
| Reading (6202) | 3 hours |
| Experiments (6202) | 4 hours |
| Quiz | 30 minutes |
| Practice | 6-8 hours |
| **Total** | **19-21 hours** |

## Resources

**Essential Libraries:**
- LangChain (retrievers)
- LlamaIndex (hybrid search)
- rank-bm25 (keyword search)
- sentence-transformers (cross-encoders)
- ColBERT (late interaction)

**Essential Papers:**
- "Dense Passage Retrieval for Open-Domain Question Answering"
- "ColBERT: Late Interaction via BERT"
- "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning"

## Search Method Comparison

| Method | Precision | Recall | Speed | Best For |
|--------|-----------|--------|-------|----------|
| BM25 (Keyword) | High | Low | ⭐⭐⭐⭐⭐ | Exact terms |
| Dense (Vector) | Medium | High | ⭐⭐⭐⭐ | Semantic meaning |
| Hybrid (RRF) | High | High | ⭐⭐⭐⭐ | Most queries |
| Re-ranked | Very High | High | ⭐⭐⭐ | Final results |

## Fusion Strategies

| Strategy | Description | Complexity |
|----------|-------------|------------|
| RRF | Reciprocal Rank Fusion | Low |
| CC | Convex Combination | Medium |
| LRR | Learn to Rank | High |
| Hybrid + Re-rank | Two-stage approach | High |

## Re-ranking Models

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| ms-marco-MiniLM | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Fast re-ranking |
| bge-reranker-base | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | General purpose |
| cohere-rerank | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Production (API) |
| ColBERT | ⭐⭐ | ⭐⭐⭐⭐⭐ | Maximum quality |

## Chunking Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Fixed Size | Fixed length chunks | Simple documents |
| Recursive | Hierarchical splitting | Complex documents |
| Semantic | Sentence/paragraph boundaries | Natural language |
| Question-Answer | Extract Q&A pairs | FAQ content |
| Parent-Child | Small chunks, big context | Long documents |

## Retrieval Parameters

| Parameter | Range | Effect |
|-----------|-------|--------|
| Chunk Size | 256-2048 | Context vs specificity |
| Overlap | 10-25% | Boundary information |
| Top-K | 5-20 | Recall vs noise |
| Re-rank Top-K | 3-10 | Final selection |

## Tips for Success

1. **Start with hybrid search**: Best bang for buck
2. **Re-rank sparingly**: Only on top results
3. **Tune chunk size**: Critical for quality
4. **Measure retrieval accuracy**: Before end-to-end evaluation
5. **Consider your data**: Structure affects chunking strategy

## Common Pitfalls

- **Chunks too small**: Lose context
- **Chunks too large**: Lose specificity
- **No overlap**: Miss boundary information
- **Over-retrieving**: Too much noise in context
- **Under-retrieving**: Missing relevant information

## Retrieval Evaluation Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Precision@K | TP / (TP + FP) | >0.8 |
| Recall@K | TP / (TP + FN) | >0.9 |
| MRR | 1 / rank_of_first_relevant | >0.8 |
| NDCG@K | DCG / IDCG | >0.7 |

## Hybrid Search Pipeline

```text
Query
  ↓
┌─────────────┬─────────────┐
│ Vector Search │ Keyword Search │
│  (Semantic)   │    (BM25)      │
└──────┬────────┴──────┬────────┘
       ↓               ↓
    Reciprocal Rank Fusion
       ↓
    Top-K Results (e.g., 50)
       ↓
    Cross-Encoder Re-ranking
       ↓
    Top-K Results (e.g., 10)
       ↓
    Generation
```

## When to Use Each Strategy

| Scenario | Best Approach |
|-------------------------|
| Exact term matching | BM25 only |
| Semantic understanding | Vector only |
| General purpose RAG | Hybrid + Re-rank |
| Fast retrieval | Vector only |
| Maximum quality | Hybrid + Re-rank + ColBERT |

---

**Next Module:** [6300: Context Management](../6300-context/README.md)

**Previous Module:** [6100: Vector Embeddings](../6100-vector/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 6 documentation.

