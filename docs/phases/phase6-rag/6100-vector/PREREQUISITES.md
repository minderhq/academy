---
Document ID: 6100-PREREQUISITES
Title: "Prerequisites: Vector Databases"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Advanced
---

# Prerequisites: Vector Databases

**For:** [6101-HNSW-Indexing.md](./6101-HNSW-Indexing.md)

---

## What You Should Know Before Starting

### Essential Concepts

**1. Information Retrieval**
- Traditional keyword search
- Why keyword search fails for semantic meaning
- Need for similarity-based search

**2. Vector Embeddings**
- Text/images → vectors
- Similarity = cosine distance
- High-dimensional vector spaces

**3. Database Basics**
- What databases do (store, retrieve, query)
- Indexing for speed
- Tradeoffs: space vs time

---

## Quick Refresher

### Semantic Search vs Keyword Search

**Keyword Search:**
```python
query = "machine learning"
matches = ["machine learning", "learning machines"]  # Fails!
```

**Semantic Search:**
```python
query = "machine learning"
matches = ["machine learning", "ML algorithms",  # Works!
           "neural networks", "AI systems"]
```

### Vector Similarity

```text
Similarity = cos(angle between vectors)

cos_sim(v1, v2) = (v1 · v2) / (||v1|| × ||v2||)

Values: -1 (opposite) to 1 (identical)
Semantic similarity ≈ 0.7-0.9
```

---

## Learning Resources

**If you're new to these concepts:**

1. **Information Retrieval (30 min):**
   - [Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/)
   - Chapters 1-3

2. **Vector Embeddings (45 min):**
   - [Vector Similarity Search Explained](https://www.pinecone.io/learn/vector-similarity/)
   - Understand embedding spaces

3. **Database Indexing (20 min):**
   - [Database Indexing Explained](https://www.youtube.com/watch?v=aOtExK-uH6Y)
   - Why indexes speed up queries

---

## What You'll Learn

After completing 6101-HNSW-Indexing.md, you'll understand:

1. ✅ HNSW (Hierarchical Navigable Small World) algorithm
2. ✅ Approximate nearest neighbor search
3. ✅ Vector database architecture
4. ✅ Performance tuning
5. ✅ When to use vector databases

---

## Readiness Check

**Answer these questions:**

1. Why do we convert text to vectors?
2. What's cosine similarity?
3. Why don't we use exact search for vectors?

**If unsure:** Review the quick refresher above.

**Ready to start?** → [6101-HNSW-Indexing.md](./6101-HNSW-Indexing.md)

---

**Estimated Time to Complete:** 2-3 hours
**Difficulty:** ⭐⭐⭐ Advanced
