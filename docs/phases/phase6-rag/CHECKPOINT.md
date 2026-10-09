---
Document ID: PHASE6-CHECKPOINT
Title: "Progress Checkpoint: Phase 6 - Data Nexus"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['checkpoint', 'rag', 'retrieval', 'hybrid-search']
---

# Progress Checkpoint: Phase 6 - Data Nexus

**Track your progress through Phase 6 modules**

---

## Phase 6 Overview

**Phase:** [6000] Data Nexus: RAG & Memory

**Modules:** 5 (6100, 6200, 6300, 6400, 6500)

**Estimated Time:** 4-5 weeks

**Difficulty:** ⭐⭐ Intermediate

---

## Phase Completion Goal

After completing Phase 6, you will:

- Build RAG systems
- Implement GraphRAG
- Use vector databases effectively
- Set up MLOps pipelines
- Combine retrieval with generation

---

## Module Checkpoints

### Module 6100: Vector Embeddings (Required)

**Checkpoint Quiz:**

1. What is HNSW and why is it fast?
2. How does semantic similarity work?
3. When should you use vector databases?

**Practical Verification:**

- [ ] Can set up Qdrant
- [ ] Can implement vector search
- [ ] Understand embedding models

---

### Module 6200: Retrieval Strategies (Required)

**Checkpoint Quiz:**

1. What is hybrid search?
2. How does re-ranking improve results?
3. What are the RAG pipeline stages?

**Lab Verification:**

- [ ] Completed [LAB-002: RAG Implementation](../../learning-resources/labs/LAB-002-RAG-Implementation.md)
- [ ] Completed [LAB-005: GraphRAG](../../learning-resources/labs/LAB-005-GraphRAG.md)
- [ ] Can tune a hybrid retrieval pipeline and justify the re-ranker choice

---

### Module 6300: Context Augmentation (Required)

**Checkpoint Quiz:**

1. What is GraphRAG and how does it differ from RAG?
2. How do knowledge graphs enhance retrieval?
3. What is Neo4j used for?

**Practical Verification:**

- [ ] Can contrast GraphRAG with plain vector RAG
- [ ] Can explain how knowledge graphs enhance retrieval
- [ ] Has run a Cypher query against Neo4j

---

### Module 6400: Vector Databases (Required)

**Checkpoint Quiz:**

1. How do you configure Qdrant collections and indexes?
2. How do Qdrant, Pinecone, and Weaviate differ?
3. What does moving from local to production Qdrant deployment involve?

**Practical Verification:**

- [ ] Can deploy Qdrant with Docker Compose
- [ ] Can configure collections and indexes
- [ ] Understand production deployment strategies

---

### Module 6500: MLOps Pipelines for RAG (Required)

**Checkpoint Quiz:**

1. What is the ML lifecycle?
2. How does CI/CD work for ML?
3. What is model registry used for?

**Practical Verification:**

- [ ] Can map a project onto the ML lifecycle stages
- [ ] Has wired a model training job into a CI/CD pipeline
- [ ] Can explain what a model registry tracks (versions, lineage)

---

## Common Pitfalls

1. **Chunk-Size Blind Spot:** Chunks too small lose surrounding context, too big dilute the embedding signal - tune per corpus instead of accepting the default
2. **Embedding Mismatch:** Indexing with one embedding model and querying with another returns plausible-looking garbage - lock the model and version per index
3. **Hybrid Without Re-Ranking:** Combining BM25 and vector results without a re-ranker yields two noisy lists, not one good one - re-rank before cutting top-k
4. **Deploy Before Eval:** Shipping a retrieval change without a fixed evaluation set makes every quality claim anecdotal - gate deploys on the harness

---

## Phase 6 Completion Badge

**Badge:** RAG Specialist

**You've earned it when:**

- All required modules completed
- Can build RAG systems
- Can implement GraphRAG
- Have built production RAG
