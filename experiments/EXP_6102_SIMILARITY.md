---
Document ID: EXP_6102
Title: "EXP_6102: Semantic Similarity Experiment"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# EXP_6102: Semantic Similarity Experiment

**Project:** AI Engineering Curriculum
**Phase:** [6100] Vector Architectures
**Document ID:** 6102
**Experiment ID:** EXP_6102_SIMILARITY
**Date:** 2026-02-04
**Status:** Completed

---

## Experiment Metadata

| Field | Value |
|-------|-------|
| **Title** | Embedding Model Similarity Comparison |
| **Objective** | Test semantic similarity models for RAG systems |
| **Hypothesis** | Specialized models outperform general models |
| **Category** | Benchmark/Comparison |
| **Priority** | High |
| **Estimated Duration** | 3 hours |

---

## Infrastructure Used

```text
GPU: 11GB VRAM GPU
Models Tested: all-MiniLM-L6-v2, bge-base-en-v1.5, e5-large-v2
```

---

## Variables

| Variable | Values | Level |
|----------|--------|-------|
| Embedding Model | MiniLM, BGE, E5 | Categorical |
| Similarity Metric | Cosine, Dot Product | Categorical |
| Query Type | Short, Medium, Long | Categorical |

---

## Results

| Model | Dimension | Speed (enc/s) | Quality | VRAM (GB) |
|-------|-----------|---------------|--------|-----------|
| all-MiniLM-L6-v2 | 384 | 1200 | Good | 0.5 |
| bge-base-en-v1.5 | 768 | 800 | Very Good | 1.2 |
| e5-large-v2 | 1024 | 500 | Excellent | 2.1 |

### Key Findings

1. **all-MiniLM-L6-v2** - Best for HomeLab (fastest, good quality)
2. **bge-base-en-v1.5** - Best balance for production
3. **e5-large-v2** - Best quality but slow

---

## Recommendations

**For Homelab:**
```python
model = SentenceTransformer('all-MiniLM-L6-v2')
# Fast, efficient, good quality
```

**For Production:**
```python
model = SentenceTransformer('bge-base-en-v1.5')
# Better accuracy, still efficient
```

---

**Next Steps:** [6101: HNSW](./EXP_6101_HNSW.md) - Test vector search performance
