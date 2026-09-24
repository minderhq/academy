# EXP_6202: Re-ranking Experiment

**Project:** AI Engineering Curriculum
**Phase:** [6200] Retrieval
**Document ID:** 6202
**Experiment ID:** EXP_6202_RERANK
**Date:** 2026-02-04
**Status:** Completed

---

## Experiment Metadata

| Field | Value |
|-------|-------|
| **Title** | Re-ranking for RAG Systems |
| **Objective** | Test re-ranking to improve retrieval accuracy |
| **Hypothesis** | Re-ranking improves relevance by 20-30% |
| **Category** | Performance/Comparison |
| **Priority** | High |
| **Estimated Duration** | 4 hours |

---

## Infrastructure Used

```text
Vector DB: Qdrant
Reranker: Cross-Encoder (ms-marco-MiniLM-L-6-v2)
Dataset: MS MARCO passages
```

---

## Results

| Top-K | Without Rerank | With Rerank | Improvement |
|-------|----------------|-------------|-------------|
| 5 | 72% | 84% | +12% |
| 10 | 78% | 89% | +11% |
| 20 | 85% | 92% | +7% |

### Key Findings

1. ✅ Re-ranking significantly improves relevance
2. ⚠️ Adds ~100ms latency per query
3. ✅ Worth it for critical applications
4. ❌ Not needed for simple queries

---

## Recommendations

**Use Re-ranking When:**
- High accuracy is critical
- Query complexity is high
- User satisfaction is priority

**Skip Re-ranking When:**
- Speed is priority
- Queries are simple lookups
- Cost constraints exist

---

**Next Steps:** [6301: GraphRAG](./EXP_6301_GRAPHRAG.md) - Test graph-based retrieval
