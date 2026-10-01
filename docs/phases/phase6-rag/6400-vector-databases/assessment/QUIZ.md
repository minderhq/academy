---
Document ID: 6400-QUIZ
Title: "6400: Vector Databases - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'rag', 'vector-db']
---

# 6400: Vector Databases - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Vector databases store:**

A) Text documents
B) Vector embeddings
C) Images
D) All of the above

**2. Qdrant uses:**

A) HNSW index
B) IVF index
C) No index
D) Both

**3. Collection in vector DB:**

A) Stores vectors
B) Stores metadata
C) Both
D) Neither

**4. Payload in Qdrant:**

A) Vector data
B) Metadata
C) Both
D) Neither

**5. Upsert operation:**

A) Only inserts
B) Only updates
C) Inserts or updates
D) Deletes

**6. Vector search returns:**

A) Exact matches
B) Nearest neighbors
C) Random vectors
D) All vectors

**7. Filtering in vector DB:**

A) Only on vectors
B) Only on metadata
C) On both
D) Not possible

**8. Hybrid search in vector DB:**

A) Vector only
B) Keyword only
C) Vector + keyword
D) No search

**9. HNSW parameter ef_construct:**

A) Index speed vs accuracy
B) Query speed
C) Memory usage
D) No effect

**10. Quantization in vector DB:**

A) Increases memory
B) Reduces memory
C) No effect
D) Increases accuracy

**11. Distance metric cosine:**

A) Euclidean distance
B) Angular distance
C) Manhattan distance
D) Dot product

**12. Weaviate uses:**

A) Only HNSW
B) Multiple index types
C) No index
D) Only flat

**13. Milvus is:**

A) A vector database
B) An embedding model
C) A training tool
D) Not related

**14. Sharding in vector DB:**

A) Distributes data
B) Replicates data
C) No distribution
D) Only for backup

**15. Replication in vector DB:**

A) Copies data
B) Distributes data
C) No copies
D) Deletes data

**16. Consistency level:**

A) Strong vs eventual
B) Only strong
C) Only eventual
D) No consistency

**17. Batch upsert:**

A) One vector at a time
B) Multiple vectors
C) No upsert
D) Only delete

**18. Scroll/search API:**

A) Returns all results
B) Paginates results
C) No pagination
D) Only first page

**19. Vector DB for RAG:**

A) Stores documents
B) Stores embeddings
C) Both
D) Neither

**20. Performance tuning:**

A) Not needed
B) Index parameters, quantization, sharding
C) Only hardware
D) Only queries

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | Vector DBs index embeddings plus their payloads and documents |
| 2 | A | Qdrant's default index is HNSW |
| 3 | C | A collection holds vectors and their metadata |
| 4 | B | Qdrant payloads carry the metadata alongside each vector |
| 5 | C | Upsert inserts new points or updates existing ones |
| 6 | B | Vector search returns nearest neighbors, not exact matches |
| 7 | C | Filtering combines vector similarity with metadata conditions |
| 8 | C | Hybrid search runs vector and keyword sides together |
| 9 | A | ef_construct trades build time against graph quality |
| 10 | B | Vector quantization shrinks memory (with some recall cost) |
| 11 | B | Cosine measures angular distance between directions |
| 12 | A | Weaviate uses HNSW; multiple index types are Milvus's strength |
| 13 | A | Milvus is an open-source vector database |
| 14 | A | Sharding distributes data across nodes |
| 15 | A | Replication copies data for availability |
| 16 | A | Consistency levels span strong to eventual |
| 17 | B | Batch upsert writes many vectors per call |
| 18 | B | Scroll APIs paginate through large result sets |
| 19 | C | RAG keeps documents and embeddings in the store |
| 20 | B | Tuning spans index params, quantization and sharding |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 8, 12-15, 17-19:** [6402: Vector Database Comparison](../6402-Pinecone-vs-Weaviate.md) — feature matrix, hybrid and batch operations, Weaviate and Milvus profiles, sharding and replication
- **Questions 2-7, 9-11, 16:** [6401: Qdrant Setup Guide](../6401-Qdrant-Setup.md) — collections, payloads, upsert, search, filtering, HNSW tuning and consistency
- **Question 20:** [6403: Qdrant Production Deployment](../guides/6403-Qdrant-Production-Deployment.md) — performance tuning spanning index params, quantization and sharding
