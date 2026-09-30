---
Document ID: 3200-QUIZ
Title: "3200: Embeddings - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'transformers', 'embeddings']
---

# 3200: Embeddings - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Word embeddings represent words as:**

A) Sparse binary vectors
B) Dense continuous vectors
C) One-hot vectors
D) Strings, stored and compared character by character with no geometry

**2. The main idea of word2vec is:**

A) Random initialization only, with no learning signal applied at any point
B) Count word occurrences
C) Use dictionaries
D) Learn distributed representations

**3. Word2Vec has two main training approaches:**

A) RNN and CNN, the two recurrent-convolutional heads of the original paper
B) CBOW and Skip-gram
C) Attention and MLP
D) BERT and GPT

**4. CBOW predicts:**

A) The context words from the target
B) The previous word
C) The next word
D) The target word from context

**5. Skip-gram predicts:**

A) Part of speech tags, predicted through a separate morphological parser
B) The context words from the target
C) The target word from context
D) The next sentence

**6. GloVe embeddings are based on:**

A) Random initialization
B) Word co-occurrence statistics
C) Neural networks
D) Hand-crafted features, assembled by linguists for every vocabulary entry

**7. FastText improves on Word2Vec by:**

A) Using attention
B) Using larger datasets, since raw corpus size alone is what fastText changed
C) Using subword information
D) Using more layers

**8. Contextual embeddings (like BERT):**

A) Have different vectors depending on context
B) Don't use training
C) Have one vector per word type, identical in every sentence it appears in
D) Are random

**9. Static embeddings have:**

A) One vector per word type regardless of context
B) No vectors
C) Multiple vectors per word, one fresh vector sampled for every occurrence
D) Random vectors

**10. BERT uses embeddings for:**

A) Tokens, positions, and segments
B) Tokens only
C) Positions only
D) Tokens and positions only, with no segment information anywhere in the model

**11. The dimensionality of word embeddings is typically:**

A) 10-50
B) Doesn't matter
C) 100-1000
D) 10,000+

**12. Word similarity is measured by:**

A) Manhattan distance
B) Euclidean distance
C) Cosine similarity
D) Dot product only

**13. "King - Man + Woman = Queen" demonstrates:**

A) Data leakage, caused by copying test answers into the training corpus
B) Overfitting
C) Random chance
D) Word embeddings capture semantic relationships

**14. Positional embeddings encode:**

A) Word meaning, which positional embeddings are never designed to carry
B) Part of speech
C) Named entities
D) Position in sequence

**15. Rotary Position Embeddings (RoPE):**

A) Add position to embeddings
B) Both A and C
C) Rotate queries and keys
D) Replace positional embeddings

**16. ALiBi's attention bias:**

A) Adds a bias based on distance
B) Doesn't work
C) Uses sinusoidal functions, exactly as the original Transformer tables define them
D) Is learned

**17. Embedding layer initialization is typically:**

A) All zeros
B) Pre-trained only
C) Random
D) One-hot

**18. During training, embeddings are:**

A) Fixed (not updated), frozen exactly as they were at random initialization
B) Ignored
C) Updated along with other parameters
D) Removed

**19. The vocabulary size affects:**

A) Embedding layer size
B) Only training speed
C) Nothing
D) Only inference speed, with the parameter count somehow staying constant

**20. Subword tokenization (BPE):**

A) Doesn't use vocabulary
B) Uses whole words only, refusing to break rare words into smaller pieces
C) Uses characters only
D) Splits words into subword units

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | B | Embeddings are dense continuous vectors in a learned geometry |
| 2 | D | Word2vec learns distributed representations from surrounding context |
| 3 | B | The two training recipes: CBOW and Skip-gram |
| 4 | D | CBOW predicts the target word from its context |
| 5 | B | Skip-gram predicts the context words from the target |
| 6 | B | GloVe factorizes global word co-occurrence statistics |
| 7 | C | FastText adds subword (character n-gram) information |
| 8 | A | Contextual embeddings produce a different vector per context |
| 9 | A | Static embeddings keep one vector per word type in all contexts |
| 10 | A | BERT sums token, position, and segment embeddings |
| 11 | C | Typical embedding dimensions run 100-1000 |
| 12 | C | Cosine similarity measures the angle, robust to vector magnitude |
| 13 | D | The analogy shows linear semantic structure in the vector space |
| 14 | D | Positional embeddings encode where a token sits in the sequence |
| 15 | B | Rotating queries and keys injects position and replaces positional embeddings - both |
| 16 | A | ALiBi adds a distance-proportional bias to attention scores |
| 17 | C | Embedding tables start from random initialization |
| 18 | C | Embeddings are learned parameters, updated by the optimizer |
| 19 | A | Vocabulary size x dimension is the embedding layer size |
| 20 | D | BPE splits rare words into subword units |
