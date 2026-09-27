---
Document ID: 3100-QUIZ
Title: "3100: Attention - Quiz"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
---

# 3100: Attention - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Self-attention allows a model to:**

A) Focus on one word at a time
B) Weigh the importance of different words relative to each other
C) Ignore context
D) Process sequentially only

**2. The query (Q), key (K), and value (V) in attention are:**

A) The same thing
B) Learned projections of the input
C) Random matrices
D) Fixed constants

**3. The attention score is computed as:**

A) Q + K
B) Q × K
C) softmax(QK^T / √d)
D) ReLU(QK^T)

**4. Multi-head attention:**

A) Runs attention multiple times in parallel
B) Runs attention sequentially
C) Is slower than single-head
D) Reduces model capacity

**5. The √d scaling factor in attention:**

A) Makes training faster
B) Prevents vanishing gradients in softmax
C) Increases the attention scores
D) Has no effect

**6. Causal masking in decoder attention:**

A) Allows all positions to attend to all others
B) Prevents positions from attending to future positions
C) Is only used during inference
D) Is not needed

**7. The original attention mechanism (for seq2seq) was introduced in:**

A) "Attention Is All You Need" (2017) - introduced self-attention and Transformers
B) "BERT: Pre-training of Deep Bidirectional Transformers" (2018)
C) "Neural Machine Translation by Jointly Learning to Align and Translate" (2015) - introduced attention for NMT
D) "GPT-3" (2020)

**8. Cross-attention connects:**

A) Tokens within the same sequence
B) Two different sequences
C) All sequences to each other
D) The model to the loss

**9. The number of attention heads is typically:**

A) 1
B) 8-16 for base models
C) 100+
D) Doesn't matter

**10. Attention weights sum to:**

A) 0
B) 1
C) The sequence length
D) Variable amounts

**11. The value of the attention softmax represents:**

A) The importance of each key
B) The learning rate
C) The gradient
D) The loss

**12. Positional encoding is needed because:**

A) Attention has no inherent notion of position
B) It improves training speed
C) It reduces memory
D) It's required by softmax

**13. Sinusoidal positional encoding:**

A) Uses learned embeddings
B) Uses fixed sine and cosine functions
C) Is not commonly used
D) Only works for short sequences

**14. Rotary Positional Embeddings (RoPE):**

A) Are the same as sinusoidal
B) Rotate keys and queries based on position
C) Don't encode position
D) Are only used in vision

**15. The attention complexity for sequence length n is:**

A) O(n)
B) O(n²)
C) O(n³)
D) O(log n)

**16. Flash Attention optimizes:**

A) Model accuracy
B) Memory access patterns for speed
C) The number of parameters
D) The learning rate

**17. Grouped Query Attention (GQA):**

A) Uses more heads
B) Shares key/value projections across heads
C) Is slower than standard attention
D) Reduces accuracy

**18. Sliding window attention:**

A) Attends to all positions
B) Attends only to nearby positions
C) Is only for vision
D) Doesn't work

**19. ALiBi positional encoding:**

A) Uses learned embeddings
B) Adds a bias based on distance
C) Uses sinusoidal functions
D) Doesn't exist

**20. In practice, multi-head attention learns:**

A) The same thing in each head
B) Different attention patterns in each head
C) Nothing (it's random)
D) Only one useful head

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | B |
| 3 | C |
| 4 | A |
| 5 | B |
| 6 | B |
| 7 | C |
| 8 | B |
| 9 | B |
| 10 | B |
| 11 | A |
| 12 | A |
| 13 | B |
| 14 | B |
| 15 | B |
| 16 | B |
| 17 | B |
| 18 | B |
| 19 | B |
| 20 | B |
