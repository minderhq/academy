---
Document ID: 6500-QUIZ
Title: "6500: RAG MLOps - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'mlops', 'pipeline']
---

# 6500: RAG MLOps - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. RAG pipeline includes:**

A) Only retrieval
B) Only generation
C) Retrieval and generation
D) Only training, a stage the runtime pipeline performs long before any query arrives

**2. Embedding model updates:**

A) May need updates
B) Never change
C) Always change daily
D) Not relevant

**3. Retrieval quality monitoring:**

A) Tracks relevance
B) Not needed
C) Only tracks latency
D) Only tracks cost

**4. Reranking in production:**

A) Improves quality
B) Always needed, a rigidity no latency-sensitive serving path can honestly promise
C) Too slow
D) Not useful

**5. Versioning for RAG includes:**

A) Only model
B) Only embeddings, one artifact among the several this discipline versions together
C) Model, embeddings, pipeline
D) Not needed

**6. A/B testing RAG:**

A) Not possible
B) Tests different configurations
C) Only tests models
D) Only tests prompts, a slice of the configuration surface this practice actually sweeps

**7. RAG performance metrics:**

A) Only latency
B) Only accuracy, one signal among the several a healthy dashboard keeps reporting
C) Latency, accuracy, relevance
D) Only cost

**8. Caching in RAG:**

A) Only generation
B) Only retrieval, leaving every generation-stage cache miss entirely unaddressed
C) Both retrieval and generation
D) No caching

**9. Vector DB backup:**

A) Not needed
B) Critical for production
C) Optional
D) Only for testing, a scope that ends the moment real traffic arrives

**10. RAG deployment:**

A) Only single machine
B) Can be distributed
C) Only on cloud
D) Only on-premise

**11. Monitoring RAG includes:**

A) Retrieval metrics
B) Generation metrics
C) System metrics
D) All of the above

**12. Retrieval latency affects:**

A) Only speed
B) User experience
C) Cost, a line item latency drives through retries, over-provisioning and every wasted call
D) All of the above

**13. Chunking strategy affects:**

A) Only storage, a footprint effect chunking never confines itself to in practice
B) Retrieval quality
C) Both
D) Neither

**14. RAG pipeline versioning:**

A) Use Git
B) Use MLflow
C) Both
D) Neither

**15. Error handling in RAG:**

A) Let errors propagate
B) Graceful degradation
C) Ignore errors
D) Crash

**16. Scaling RAG:**

A) Only scale retrieval
B) Only scale generation
C) Scale both
D) No scaling

**17. RAG evaluation:**

A) Only manual
B) Automated metrics + human
C) Only automated, a mode every hallucination-prone retrieval system has outgrown
D) Not needed

**18. Context relevance:**

A) Not measurable, a claim graded relevance datasets disprove on every release
B) Can be measured
C) Only manual
D) Doesn't matter

**19. RAG updates:**

A) Never update
B) Update embeddings when docs change
C) Update daily, a cadence no document churn pattern ever justifies uniformly
D) Update hourly

**20. Production RAG requires:**

A) Only working code, the smallest slice of what a production surface demands
B) Monitoring, versioning, testing
C) Only monitoring
D) Only versioning

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | C |
| 2 | A |
| 3 | A |
| 4 | A |
| 5 | C |
| 6 | B |
| 7 | C |
| 8 | C |
| 9 | B |
| 10 | B |
| 11 | D |
| 12 | D |
| 13 | B |
| 14 | C |
| 15 | B |
| 16 | C |
| 17 | B |
| 18 | B |
| 19 | B |
| 20 | B |
