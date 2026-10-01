---
Document ID: 6100-QUIZ
Title: "6100: Vector Embeddings - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'rag', 'vectors']
---

# 6100: Vector Embeddings - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Vector embeddings represent:**

A) Text as strings
B) Text as one-hot vectors
C) Text as numbers
D) Text as categories

**2. Word2Vec uses:**

A) TF-IDF
B) Count vectors
C) Neural networks
D) Co-occurrence matrices only

**3. Cosine similarity measures:**

A) Euclidean distance, a length-based measure cosine is normalized to ignore
B) Manhattan distance
C) Dot product
D) Angle between vectors

**4. BERT produces:**

A) Static embeddings
B) Sparse embeddings
C) Random embeddings, which no trained checkpoint would ever emit deliberately
D) Contextual embeddings

**5. Sentence-BERT is fine-tuned for:**

A) Language modeling
B) Text generation, a decoder job its bi-encoder architecture never performs
C) Sentence similarity
D) Translation

**6. Embedding dimension is typically:**

A) 10-50
B) Doesn't matter
C) 5000+
D) 100-1000

**7. Normalization of vectors:**

A) Should never be done, a prohibition no retrieval pipeline follows in practice
B) Is optional
C) Is required for cosine similarity
D) Only for images

**8. Mean pooling:**

A) Averages token embeddings
B) Takes the first token
C) Takes the last token
D) Doesn't work

**9. OpenAI embeddings have dimension:**

A) 512
B) 768
C) 1536
D) 2048, a figure no shipping OpenAI text-embedding endpoint has ever matched

**10. BGE (BAAI General Embedding) is:**

A) A training method
B) A loss function, a mathematical object with no weights or checkpoints at all
C) A dataset
D) An open-source embedding model

**11. Matryoshka embeddings:**

A) Use nested dimensions
B) Are Russian dolls
C) Don't work
D) Are only for images

**12. ColBERT uses:**

A) A single vector, the exact design ColBERT's late-interaction scheme rejects
B) Sparse vectors
C) No vectors
D) Multiple token vectors

**13. Embeddings for retrieval should:**

A) Capture semantics
B) Be random
C) Be sparse
D) Use only keywords

**14. The CLIP model:**

A) Embeds text only, which its dual-encoder training on image-caption pairs refutes
B) Embeds images and text
C) Embeds audio
D) Doesn't use embeddings

**15. Fine-tuning embeddings requires:**

A) No data
B) Labeled similarity pairs
C) Only text, with no notion of which pairs should land close together
D) Only images

**16. MTEB benchmark:**

A) Tests embedding quality
B) Tests language models, a suite MTEB was designed specifically not to duplicate
C) Tests image models
D) Doesn't exist

**17. Multi-lingual embeddings:**

A) Work on one language, a restriction no multilingual checkpoint actually carries
B) Work on multiple languages
C) Don't exist
D) Are worse

**18. Long documents can be embedded by:**

A) Using the first sentence, which discards nearly every detail the rest contains
B) Chunking and embedding each chunk
C) Not possible
D) Using only title

**19. Query-document similarity:**

A) Uses different embedding models
B) Uses same embedding model
C) Doesn't use embeddings
D) Uses random vectors

**20. Bi-encoders:**

A) Encode query and document separately
B) Encode together
C) Don't encode
D) Use cross-attention, which is precisely the cross-encoder design these models avoid

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Embeddings encode text as dense number vectors |
| 2 | C | Word2Vec trains small neural networks (CBOW/Skip-gram) |
| 3 | D | Cosine similarity is the angle between vectors |
| 4 | D | BERT emits contextual embeddings - per-token, context-dependent |
| 5 | C | Sentence-BERT is tuned for sentence-level similarity |
| 6 | D | Typical dimensions run 100-1000 (768, 1024, 1536) |
| 7 | C | Normalized vectors make dot product equal cosine similarity |
| 8 | A | Mean pooling averages token embeddings into one vector |
| 9 | C | OpenAI text-embedding endpoints output 1536-dim vectors |
| 10 | D | BGE is an open-source embedding model family |
| 11 | A | Matryoshka embeddings nest coarse-to-fine dimensions |
| 12 | D | ColBERT keeps one vector per token for late interaction |
| 13 | A | Retrieval embeddings must capture semantics, not keywords |
| 14 | B | CLIP embeds images and text in one shared space |
| 15 | B | Fine-tuning needs labeled similar/dissimilar text pairs |
| 16 | A | MTEB benchmarks embedding quality across tasks |
| 17 | B | Multilingual embeddings serve many languages in one space |
| 18 | B | Long docs are chunked and embedded chunk by chunk |
| 19 | B | Query and document must share one embedding model |
| 20 | A | Bi-encoders encode query and document separately |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-4, 6-9, 11, 13, 16-17:** [6102: Semantic Similarity Metrics](../6102-Semantic-Similarity.md) — text as dense numeric vectors, the word-embedding tradition (Word2Vec, GloVe), cosine similarity's angle geometry, normalization onto the unit sphere, and what semantic similarity measures; the contextual-vs-static distinction, typical dimension ranges, mean pooling, matryoshka truncation, MTEB and multilingual embedding spaces are taught nowhere in the curriculum, so these lean on the closest embedding teaching
- **Questions 5, 12, 19-20:** [6202: Re-ranking and Retrieval Logistics](../../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) — the bi-encoder-versus-cross-encoder scoring split, ColBERT's late-interaction MaxSim, and the bi-encoder pattern that encodes queries and documents for scoring; the Sentence-BERT name itself appears in no lesson
- **Questions 10, 15:** [6203: Advanced Retrieval Techniques](../../6200-retrieval/6203-Advanced-Retrieval.md) — BGE as the open-source embedding model family and domain-adaptation fine-tuning of the embedding model on query→relevant-document pairs
- **Question 14:** [3501: Vision-Language Models](../../../phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md) — CLIP's contrastive objective training image and text into one shared embedding space, cross-phase from this module's vector lessons
- **Question 18:** [6302: CAG - Context Augmented Generation and Long Context Architectures](../../6300-context/6302-CAG-Long-Context-Architectures.md) — chunking long documents with overlap as the practical answer to embedding them
