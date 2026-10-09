---
Document ID: 6500-QUIZ
Title: "6500: MLOps Pipelines for RAG - Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'mlops', 'pipeline']
---

# 6500: MLOps Pipelines for RAG - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. RAG pipeline includes:**

- A) Only retrieval
- B) Only generation
- C) Only training, a stage the runtime pipeline performs long before any query arrives
- D) Retrieval and generation

**2. Embedding model updates:**

- A) May need updates
- B) Never change
- C) Always change daily
- D) Not relevant

**3. Retrieval quality monitoring:**

- A) Tracks relevance
- B) Not needed
- C) Only tracks latency
- D) Only tracks cost

**4. Reranking in production:**

- A) Improves quality
- B) Always needed, a rigidity no latency-sensitive serving path can honestly promise
- C) Too slow
- D) Not useful

**5. Versioning for RAG includes:**

- A) Only model
- B) Only embeddings, one artifact among the several this discipline versions together
- C) Model, embeddings, pipeline
- D) Not needed

**6. A/B testing RAG:**

- A) Not possible
- B) Only tests prompts, a slice of the configuration surface this practice actually sweeps
- C) Only tests models
- D) Tests different configurations

**7. RAG performance metrics:**

- A) Only latency
- B) Only accuracy, one signal among the several a healthy dashboard keeps reporting
- C) Latency, accuracy, relevance
- D) Only cost

**8. Caching in RAG:**

- A) Only generation
- B) Only retrieval, leaving every generation-stage cache miss entirely unaddressed
- C) Both retrieval and generation
- D) No caching

**9. Vector DB backup:**

- A) Critical for production
- B) Not needed
- C) Optional
- D) Only for testing, a scope that ends the moment real traffic arrives

**10. RAG deployment:**

- A) Only single machine
- B) Only on-premise
- C) Only on cloud
- D) Can be distributed

**11. Monitoring RAG includes:**

- A) Retrieval metrics
- B) Generation metrics
- C) System metrics
- D) Retrieval, generation and system metrics together

**12. Retrieval latency affects:**

- A) Only speed
- B) User experience
- C) Cost, a line item latency drives through retries, over-provisioning and every wasted call
- D) Speed, user experience and cost together

**13. Chunking strategy affects:**

- A) Only storage, a footprint effect chunking never confines itself to in practice
- B) Retrieval quality
- C) Token count only
- D) Model weights

**14. RAG pipeline versioning:**

- A) Use Git
- B) Use MLflow
- C) Both Git and MLflow
- D) Version only the prompts

**15. Error handling in RAG:**

- A) Graceful degradation
- B) Let errors propagate
- C) Ignore errors
- D) Crash

**16. Scaling RAG:**

- A) Only scale retrieval
- B) Only scale generation
- C) Scale both
- D) No scaling

**17. RAG evaluation:**

- A) Only manual
- B) Automated metrics + human
- C) Only automated, a mode every hallucination-prone retrieval system has outgrown
- D) Not needed

**18. Context relevance:**

- A) Not measurable, a claim graded relevance datasets disprove on every release
- B) Can be measured
- C) Only manual
- D) Doesn't matter

**19. RAG updates:**

- A) Never update
- B) Update embeddings when docs change
- C) Update daily, a cadence no document churn pattern ever justifies uniformly
- D) Update hourly

**20. Production RAG requires:**

- A) Only working code, the smallest slice of what a production surface demands
- B) Monitoring, versioning, testing
- C) Only monitoring
- D) Only versioning

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | RAG pipelines pair a retrieval stage with a generation stage |
| 2 | A | Embedding models get replaced as better ones ship |
| 3 | A | Retrieval monitoring tracks how relevant fetched chunks are |
| 4 | A | Reranking lifts answer quality for a modest latency cost |
| 5 | C | RAG versioning spans model, embeddings and pipeline together |
| 6 | D | A/B tests compare full RAG configurations end to end |
| 7 | C | Dashboards track latency, accuracy and relevance together |
| 8 | C | Caching helps retrieval results and generated answers alike |
| 9 | A | Backups are critical once real traffic depends on the store |
| 10 | D | RAG serving spreads across machines when load demands it |
| 11 | D | Monitoring covers retrieval, generation and system metrics |
| 12 | D | Retrieval latency drives speed, experience and cost together |
| 13 | B | Chunk size and overlap shape retrieval quality first |
| 14 | C | Git versions pipeline code, MLflow tracks runs and models |
| 15 | A | Graceful degradation keeps partial value when stages fail |
| 16 | C | Scaling covers both retrieval and generation stages |
| 17 | B | Evaluation blends automated metrics with human judgment |
| 18 | B | Context relevance is measurable with graded datasets and judges |
| 19 | B | Embeddings refresh when documents change, not on a fixed clock |
| 20 | B | Production RAG demands monitoring, versioning and testing together |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Question 1:** [6304: GraphRAG Implementation](../../6300-context/guides/6304-GraphRAG-Implementation.md) — the four-stage pipeline (ingestion → query processing → context building → generation) assembled end to end, the closest thing the curriculum has to a full RAG pipeline walkthrough
- **Questions 2, 5, 19:** [6503: Model Registry](../6503-Model-Registry.md) — the registry's identity-lineage-promotion model with version strategy, aliases and one-auditable-write rollback, which is how a refreshed embedding model would ship; the re-embedding policy is now taught in-module by [6504: Re-Embedding Policy and A/B Testing](../6504-Re-Embedding-Policy-and-AB-Testing.md) - the churn ledger Q19 prices, the cross-space incomparability Q2 turns on, and the shadow-window gate that ships it
- **Questions 3, 6, 17, 20:** [6501: ML Model Lifecycle Management](../6501-ML-Lifecycle-Management.md) — the five-stage lifecycle's gated transitions, Stage-4 symptom alerting on live traffic (latency, errors, accuracy) with Prometheus metrics, and McNemar's challenger-vs-champion decision; formal A/B testing and human evaluation are now taught in-module by [6504: Re-Embedding Policy and A/B Testing](../6504-Re-Embedding-Policy-and-AB-Testing.md) - the sizing curve, the peeking trap, and the kappa-corrected agreement Q6 and Q17 probe; McNemar's arithmetic itself stays here
- **Question 4:** [6202: Re-ranking and Retrieval Logistics](../../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) — the two-stage pipeline where the fast retriever over-fetches and the slower cross-encoder re-scores, the quality-for-latency trade reranking makes in production
- **Questions 7-8, 11-12, 18:** [1503: LLM Observability](../../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) — TTFT, TPOT and end-to-end latency histograms, token counters and cost gauges with the prompt/output-limit/model-selection levers, and relevance, repetition and safety quality heuristics, cross-phase from this module's lifecycle lessons; explicit response caching is now taught in-module by [6505: Response Caching and Stage Scaling](../6505-Response-Caching-and-Stage-Scaling.md) - the four-tier trace where retrieval-only bills the same 12,000 tokens as no cache and the normalized key catches the 3 rewordings worth 1,500 tokens
- **Questions 9-10, 16:** [6403: Qdrant Production Deployment](../../6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md) — the snapshot backup-and-restore scripts, capacity tiers that trigger sharding/replication for HA, and resource allocation for the retrieval store; generation-stage scaling is now taught in-module by [6505: Response Caching and Stage Scaling](../6505-Response-Caching-and-Stage-Scaling.md) - the per-stage autoscaler holding both shortfalls at zero at 530 against 924 for peak provisioning, and the 26,400-token prefill versus 3,300-step decode split one replica averages away
- **Question 13:** [6302: CAG - Context Augmented Generation and Long Context Architectures](../../6300-context/6302-CAG-Long-Context-Architectures.md) — chunking long documents with overlap, which shapes what retrieval can find and how well it matches
- **Question 14:** [6502: CI/CD for Machine Learning](../6502-CI-CD-for-ML.md) — GitHub Actions workflows triggered on model-relevant paths with needs-chained jobs, while MLflow's tracking role appears in 6501's development-stage sketch and 6503's integration section
- **Question 15:** [2301: Framework Design Patterns](../../../phase2-foundations/2300-framework-engineering/2301-Framework-Design-Patterns.md) — the graceful-degradation pattern that keeps partial value when a stage fails, cross-phase from this module's MLOps lessons
