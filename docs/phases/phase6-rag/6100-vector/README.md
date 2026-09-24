# 6100: Vector Embeddings

## Module Overview

This module covers vector embeddings and similarity search, the foundation of modern retrieval-augmented generation (RAG) systems. You'll learn to embed documents, find similar content, and build efficient vector indexes.

**Why This Matters:**
- Embeddings transform text into semantic meaning representations
- Vector search powers ChatGPT's browsing, code assistants, and recommendation systems
- Efficient similarity search is critical for RAG performance
- Understanding embeddings enables better semantic understanding

## Learning Objectives

After completing this module, you will be able to:

- **Embedding Fundamentals**: Understand how text becomes vectors
- **Semantic Similarity**: Measure meaning-based similarity between documents
- **HNSW Indexing**: Build fast approximate nearest neighbor indexes
- **Embedding Models**: Choose and use appropriate embedding models
- **Vector Operations**: Perform efficient similarity search at scale

## Module Contents

### 6101: HNSW Indexing
**Hierarchical Navigable Small World Graphs**

- HNSW algorithm and architecture
- Graph-based approximate nearest neighbor search
- Index construction and parameters
- Query optimization
- Memory vs accuracy tradeoffs

**Experiments:**
- Implement HNSW from scratch
- Compare HNSW vs brute force search
- Tune HNSW parameters
- Benchmark query performance

### 6102: Semantic Similarity
**Measuring Document Similarity**

- Cosine similarity and distance metrics
- Embedding model architectures
- Sentence vs document embeddings
- Multilingual embeddings
- Domain-specific embeddings

**Experiments:**
- Generate embeddings for documents
- Compare similarity metrics
- Test different embedding models
- Build semantic search engine

### 6103: HNSW Tuning Guide
**Production Vector Index Optimization** (Guide)

- HNSW parameter tuning
- Index size vs speed optimization
- Update strategies for dynamic data
- Distributed indexing
- Monitoring and maintenance

**Guide:** [guides/6103-HNSW-Tuning-Guide.md](./guides/6103-HNSW-Tuning-Guide.md)

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 2100: Calculus (vectors, dot products)
- [ ] Module 3200: Embeddings (embedding fundamentals)
- [ ] Python and NumPy proficiency
- [ ] Basic understanding of neural networks
- [ ] Familiarity with REST APIs

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** Embeddings, similarity, HNSW
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Hands-on vector search projects
- **Duration:** 6-8 hours
- **Topics:**
  - Generate and compare embeddings
  - Build HNSW index
  - Implement semantic search
  - Optimize query performance
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **3200: Embeddings** (embedding model architectures)
- **6200: Retrieval** (advanced retrieval techniques)
- **6400: Vector Databases** (production vector stores)
- **6300: Context** (knowledge graph integration)

## Time Commitment

| Activity | Time |
|----------|------|
| Reading (6101) | 3 hours |
| Experiments (6101) | 3 hours |
| Reading (6102) | 2 hours |
| Experiments (6102) | 2 hours |
| Guide (6103) | 2 hours |
| Quiz | 30 minutes |
| Practice | 6-8 hours |
| **Total** | **18-20 hours** |

## Resources

**Essential Libraries:**
- sentence-transformers
- hnswlib / faiss
- numpy / scipy
- langchain embeddings

**Essential Models:**
- all-MiniLM-L6-v2 (fast, English)
- bge-base-en-v1.5 (quality, English)
- e5-large-v2 (multilingual)
- text-embedding-3-small (OpenAI)

## Embedding Model Comparison

| Model | Dimensions | Speed | Quality | Best For |
|-------|-----------|-------|---------|----------|
| all-MiniLM-L6-v2 | 384 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Fast English search |
| bge-base-en-v1.5 | 768 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Quality English RAG |
| e5-large-v2 | 1024 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Multilingual |
| text-embedding-3-small | 1536 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Production (API) |
| jina-embeddings-v2 | 768 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Long documents |

## Distance Metrics

| Metric | Range | Use Case |
|--------|-------|----------|
| Cosine | 0-2 | Most embeddings (default) |
| Dot Product | -∞ to ∞ | Normalized vectors |
| Euclidean | 0-∞ | Physical distance |
| Manhattan | 0-∞ | Sparse vectors |

## HNSW Parameters

| Parameter | Effect | Tradeoff |
|-----------|--------|----------|
| ef_construction | Index quality | Build time |
| M | Connectivity | Memory vs recall |
| ef_search | Query accuracy | Query speed |

## Tips for Success

1. **Start with cosine similarity**: It's the standard for embeddings
2. **Choose model by use case**: Speed vs quality vs multilingual
3. **Tune HNSW carefully**: Small changes, big impact
4. **Normalize embeddings**: Required for cosine similarity
5. **Batch embeddings**: Much faster than one-by-one

## Common Pitfalls

- **Wrong embedding model**: Domain mismatch kills quality
- **Not normalizing**: Breaks cosine similarity
- **HNSW overkill**: Small datasets don't need it
- **Ignoring context**: Sentence vs document embeddings matter
- **Forgetting updates**: HNSW is expensive to update

## When to Use Vector Search

| Scenario | Recommended Approach |
|----------|---------------------|
| Semantic search | Vector embeddings |
| Keyword search | BM25 / lexical |
| Hybrid queries | Vector + keyword fusion |
| Exact matching | Lexical search |
| Fuzzy matching | Vector search |

## Embedding Workflow

```
1. Chunk Documents
   ↓
2. Generate Embeddings (batch)
   ↓
3. Build HNSW Index
   ↓
4. Query Embedding
   ↓
5. Approximate Nearest Neighbor Search
   ↓
6. Return Top-K Results
```

---

**Next Module:** [6200: Retrieval](../6200-retrieval/README.md)

**Previous Module:** [5300: Synthetic Data](../../phase5-finetuning/5300-synthetic/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 6 documentation.

---

**Last Updated:** 2026-02-04
