---
Document ID: PHASE6-QUIZ
Title: "Phase 6: Data Nexus (RAG) Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Tags: ['assessment', 'quiz', 'rag']
---

# Phase 6: Data Nexus (RAG) Quiz

**30 Questions | Passing Score: 80% | Time: 60 minutes**

---

## Questions

### 1. What does RAG stand for?
- a) Retrieval-based Generation
- b) Recursive Aggregation Generation
- c) Retrieval-Augmented Generation
- d) Recursive Augmented Generation

**Answer:** c

---

### 2. What is the main benefit of RAG?
- a) Faster generation
- b) Adding external knowledge to LLMs
- c) Smaller models
- d) Better training without touching the corpus layout

**Answer:** b

---

### 3. What is a vector database?
- a) Database of vectors
- b) Database optimized for similarity search
- c) Mathematical database storing symbolic proofs alongside embeddings
- d) Embedded database

**Answer:** b

---

### 4. What is HNSW?
- a) High Network Speed Web
- b) Hash-based Network Search Window
- c) Hierarchical Navigable Small World graph
- d) Hierarchical Node Search Window with pruned frontier levels

**Answer:** c

---

### 5. What is Qdrant?
- a) Vector database for embeddings
- b) Quantum database
- c) Quick data retrieval over compressed columnar shards
- d) Query database

**Answer:** a

---

### 6. What is semantic similarity?
- a) Word similarity
- b) Measuring meaning similarity between texts
- c) Text matching
- d) Pattern matching over character n-grams of the raw corpus

**Answer:** b

---

### 7. What is an embedding?
- a) Text compression
- b) Word encoding
- c) Numerical representation of text
- d) Character encoding

**Answer:** c

---

### 8. What is hybrid search?
- a) Fast search
- b) Mixed search blending cached suggestions into every query
- c) Combining dense and sparse retrieval
- d) Parallel search

**Answer:** c

---

### 9. What is re-ranking?
- a) Reordering retrieved results by relevance
- b) Ranking results
- c) Scoring results
- d) Searching again

**Answer:** a

---

### 10. What is GraphRAG?
- a) RAG with knowledge graphs
- b) Visual RAG
- c) Network RAG
- d) Graph-based RAG limited to visualization dashboards

**Answer:** a

---

### 11. What is Neo4j?
- a) NoSQL database
- b) Graph database
- c) Vector database
- d) Relational database

**Answer:** b

---

### 12. What is a knowledge graph?
- a) Network of entities and relationships
- b) Knowledge network
- c) Information graph
- d) Graph of knowledge

**Answer:** a

---

### 13. What is chunking in RAG?
- a) Splitting documents into smaller pieces
- b) Text segmentation
- c) Document parsing
- d) Data compression applied before every indexing pass

**Answer:** a

---

### 14. What is the optimal chunk size for RAG?
- a) 128-256 tokens
- b) 512-1024 tokens
- c) 2048-4096 tokens
- d) 64-128 tokens

**Answer:** b

---

### 15. What is the purpose of overlap in chunking?
- a) Preserve context across chunks
- b) Reduce chunk size
- c) Improve compression
- d) Increase chunk count until every chunk fits one sentence

**Answer:** a

---

### 16. What is BM25?
- a) Dense retrieval
- b) Sparse retrieval algorithm
- c) Hybrid retrieval
- d) Neural retrieval

**Answer:** b

---

### 17. What is dense retrieval?
- a) Fast retrieval
- b) Compact retrieval
- c) Using embedding similarity for retrieval
- d) Deep retrieval

**Answer:** c

---

### 18. What is sparse retrieval?
- a) Minimal retrieval
- b) Fast retrieval
- c) Using keyword matching for retrieval
- d) Light retrieval

**Answer:** c

---

### 19. What is context window?
- a) Maximum input length for model
- b) Memory window
- c) Attention window
- d) Context storage reserved on the serving host per session

**Answer:** a

---

### 20. What is the main challenge of long-context RAG?
- a) Higher memory usage and compute cost
- b) Slow retrieval
- c) Finding relevant information
- d) Poor accuracy

**Answer:** c

---

### 21. What is metadata filtering?
- a) Filtering results by attributes
- b) Metadata processing
- c) Attribute search
- d) Data cleaning of ingested records before embedding

**Answer:** a

---

### 22. What is multi-vector retrieval?
- a) Multi-modal retrieval
- b) Storing multiple embeddings per document
- c) Multiple queries
- d) Parallel retrieval

**Answer:** b

---

### 23. What is a document store?
- a) Document database
- b) File system
- c) Document cache
- d) Storage for original documents

**Answer:** d

---

### 24. What is the reranking pipeline?
- a) Rank then retrieve with a second scoring sweep appended
- b) Retrieve and rank
- c) Search and score
- d) Retrieve then rerank

**Answer:** d

---

### 25. What is cross-encoder reranking?
- a) Cross encoding
- b) Joint encoding
- c) Parallel encoding
- d) Using joint query-document encoding

**Answer:** d

---

### 26. What is query expansion?
- a) Expanding search
- b) Query enhancement macros rewritten by the serving middleware
- c) Search expansion
- d) Enriching query with related terms

**Answer:** d

---

### 27. What is fusion retrieval?
- a) Fast retrieval
- b) Mixed retrieval
- c) Hybrid retrieval
- d) Combining multiple retrieval methods

**Answer:** d

---

### 28. What is parent document retrieval?
- a) Document hierarchy snapshots reloaded whenever indexes rebuild
- b) Hierarchical retrieval
- c) Multi-level retrieval
- d) Retrieve small chunks, return parent documents

**Answer:** d

---

### 29. What is recursive retrieval?
- a) Repeated retrieval
- b) Recursive search
- c) Nested retrieval loops terminated by fixed depth quotas
- d) Hierarchical chunking and retrieval

**Answer:** d

---

### 30. What is the main advantage of GraphRAG over vector RAG?
- a) Faster retrieval
- b) Captures relationships between entities
- c) Better accuracy
- d) Simpler implementation

**Answer:** b

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | RAG stands for Retrieval-Augmented Generation |
| 2 | B | RAG grounds LLM answers in external knowledge without retraining the model |
| 3 | B | A vector database is optimized for similarity search over embeddings |
| 4 | C | HNSW stands for Hierarchical Navigable Small World graph |
| 5 | A | Qdrant is a vector database for embeddings |
| 6 | B | Semantic similarity measures meaning similarity between texts via their embeddings |
| 7 | C | An embedding is a numerical (vector) representation of text |
| 8 | C | Hybrid search combines dense vector retrieval with sparse keyword retrieval |
| 9 | A | Re-ranking reorders retrieved results by relevance using a better scorer |
| 10 | A | GraphRAG retrieves over a knowledge graph rather than flat vector collections |
| 11 | B | Neo4j is a graph database |
| 12 | A | A knowledge graph is a network of entities and their relationships |
| 13 | A | Chunking splits documents into smaller pieces that can be embedded and retrieved |
| 14 | B | 512-1024 tokens balances context carried against retrieval precision for typical corpora |
| 15 | A | Overlap preserves context that straddles chunk boundaries |
| 16 | B | BM25 is the classic sparse keyword retrieval algorithm |
| 17 | C | Dense retrieval uses embedding similarity to find related text |
| 18 | C | Sparse retrieval matches exact keywords between query and document |
| 19 | A | The context window is the maximum input length the model can read at once |
| 20 | C | Even with long contexts, finding the genuinely relevant information stays the hard part |
| 21 | A | Metadata filtering narrows search by attributes such as source or date |
| 22 | B | Multi-vector retrieval stores multiple embeddings per document |
| 23 | D | The document store keeps the original documents the vectors point back to |
| 24 | D | The reranking pipeline retrieves candidates first, then reranks them |
| 25 | D | Cross-encoder reranking encodes query and document jointly for better relevance scoring |
| 26 | D | Query expansion enriches the query with related terms before retrieval |
| 27 | D | Fusion retrieval combines the results of multiple retrieval methods |
| 28 | D | Parent-document retrieval embeds small chunks but returns their full parent documents |
| 29 | D | Recursive retrieval walks hierarchical chunks, retrieving deeper levels as needed |
| 30 | B | GraphRAG captures relationships between entities that flat vector search misses |

**Passing: 24/30 (80%)**

