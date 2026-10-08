---
Document ID: 6200-QUIZ
Title: "6200: Retrieval - Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'rag', 'retrieval']
---

# 6200: Retrieval - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Hybrid search combines:**

- A) Only vector search
- B) Only keyword search
- C) Vector and keyword search
- D) No search, a stance that would empty the pipeline entirely

**2. BM25 is:**

- A) A vector search method, a family BM25 predates by decades
- B) A database
- C) An embedding model
- D) A keyword ranking algorithm

**3. Reciprocal Rank Fusion (RRF):**

- A) Filters results
- B) Ranks documents
- C) Creates embeddings, a job fusion never performs on any input
- D) Combines multiple result lists

**4. Dense retrieval uses:**

- A) Keywords
- B) Vector embeddings
- C) Character n-grams
- D) Neither, a claim every dense encoder output contradicts

**5. Sparse retrieval uses:**

- A) Embeddings, the dense-side artifact sparse lookup never touches
- B) Keywords/Terms
- C) Dense vector indexes
- D) Random vectors

**6. HNSW is:**

- A) A database
- B) A keyword index
- C) A vector index
- D) A scoring method

**7. Re-ranking:**

- A) Is not useful
- B) Replaces retrieval, a swap reranking cannot perform
- C) Improves initial retrieval
- D) Slower only

**8. Cross-encoders:**

- A) Don't encode
- B) Encode separately, a two-tower isolation this joint pass refuses
- C) Encode query and document together
- D) Are slower than bi-encoders

**9. Maximal Marginal Relevance (MMR):**

- A) Is not used
- B) Only ranks by relevance
- C) Diversifies results
- D) Reduces diversity

**10. Query expansion:**

- A) Improves recall
- B) Reduces recall
- C) Has no effect
- D) Only for keywords

**11. Hybrid search alpha parameter:**

- A) Controls dense vs sparse weight
- B) Controls top-k
- C) Controls score threshold
- D) No effect, a dismissal every weighted blend output refutes

**12. Approximate nearest neighbor:**

- A) Is exact but slow
- B) Is fast but approximate
- C) Is both fast and exact
- D) Doesn't work

**13. IVF (Inverted File Index):**

- A) Partitions vector space
- B) Only works for text
- C) Is a keyword index
- D) Doesn't scale

**14. RRF formula uses:**

- A) Sum of scores
- B) No formula
- C) Probability
- D) Rank positions

**15. Semantic search:**

- A) Uses meaning
- B) Uses keywords
- C) Uses both
- D) Uses neither

**16. Lexical search:**

- A) Uses meaning
- B) Uses neither, a denial that erases the term matching itself
- C) Uses embeddings
- D) Uses exact terms

**17. Boosting in retrieval:**

- A) Increases certain document scores
- B) Decreases scores
- C) No effect, a nullity boost factors never settle for
- D) Filters results

**18. Retrieval augmented generation (RAG) needs:**

- A) No retrieval
- B) Only training
- C) Only generation
- D) Good retrieval

**19. Context window affects:**

- A) Only speed
- B) How much retrieved info can be used
- C) No effect, an indifference every filled context disproves
- D) Only memory

**20. Fusion of retrieval methods:**

- A) Always improves
- B) Can improve if done well
- C) Always worsens, a pessimism no fusion benchmark sustains
- D) No effect

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Hybrid search blends vector and keyword retrieval |
| 2 | D | BM25 is a classic keyword ranking function |
| 3 | D | RRF merges multiple ranked lists into one |
| 4 | B | Dense retrieval matches vector embeddings |
| 5 | B | Sparse retrieval matches exact terms (BM25-style) |
| 6 | C | HNSW is a graph-based approximate vector index |
| 7 | C | Reranking refines the candidate set from first-stage retrieval |
| 8 | C | Cross-encoders jointly encode query and document |
| 9 | C | MMR trades relevance against redundancy for diversity |
| 10 | A | Query expansion adds terms to raise recall |
| 11 | A | Alpha weights the dense side against the sparse side |
| 12 | B | ANN trades exactness for sublinear search speed |
| 13 | A | IVF partitions the vector space into clusters |
| 14 | D | RRF scores by rank position, not raw scores |
| 15 | A | Semantic search retrieves by meaning |
| 16 | D | Lexical search matches exact terms |
| 17 | A | Boosting raises scores of favored documents or fields |
| 18 | D | RAG output quality is bounded by retrieval quality |
| 19 | B | The context window caps how much retrieved text fits |
| 20 | B | Fusion helps when tuned - not a guaranteed win |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-5, 11, 14-17, 20:** [6201: Hybrid Search - Combining Keyword and Semantic Search](../6201-Hybrid-Search.md) — BM25's TF-saturation and IDF ranking with lexical matching, the dense-vs-sparse retrieval split, semantic vector search, score-level α blending and rank-based Reciprocal Rank Fusion with the choose-by-failure-mode tuning; document boosting is now taught in-module by [6204: Diversification and Boosting](../6204-Diversification-and-Boosting.md) - provenance weights that arbitrate near-ties, stacking, and the fused-score-vs-channel-scoped placement question Q17 probes
- **Questions 6, 12-13:** [6101: HNSW Indexing - Efficient Semantic Search at Scale](../../6100-vector/6101-HNSW-Indexing.md) — the graph index itself, brute-force versus ANN's bounded-recall speed trade, and IVF's clustered partitions as the sibling ANN method
- **Questions 7-9, 18:** [6202: Re-ranking and Retrieval Logistics](../6202-Re-ranking-and-Retrieval-Logistics.md) — the two-stage pipeline where a fast retriever over-fetches and a slower cross-encoder re-scores into the top-k the generator actually sees; MMR's relevance-redundancy diversification is now taught in-module by [6204: Diversification and Boosting](../6204-Diversification-and-Boosting.md) - the lambda dial, the fetch_k over-fetch pool, and the ILS/coverage metrics behind Q9
- **Question 10:** [6203: Advanced Retrieval Techniques](../6203-Advanced-Retrieval.md) — query expansion via pseudo-relevance feedback and multi-query paraphrase to lift recall
- **Question 19:** [6302: CAG - Context Augmented Generation and Long Context Architectures](../../6300-context/6302-CAG-Long-Context-Architectures.md) — the context window as prompt budget that caps how much retrieved text fits
