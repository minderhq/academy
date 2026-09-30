---
Document ID: 3100-QUIZ
Title: "3100: Attention - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'transformers', 'attention']
---

# 3100: Attention - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Self-attention allows a model to:**

A) Ignore context entirely and never weigh any input token during any step
B) Focus on one word at a time
C) Weigh the importance of different words relative to each other
D) Process sequentially only

**2. The query (Q), key (K), and value (V) in attention are:**

A) The same thing
B) Learned projections of the input
C) Random matrices regenerated at every forward pass
D) Fixed constants

**3. The attention score is computed as:**

A) Q + K
B) softmax(QK^T / √d)
C) ReLU(QK^T)
D) The raw dot product with no softmax or scaling step

**4. Multi-head attention:**

A) Runs attention sequentially
B) Is slower than a single attention head in every configuration
C) Reduces model capacity
D) Runs attention multiple times in parallel

**5. The √d scaling factor in attention:**

A) Has no effect
B) Prevents vanishing gradients in softmax
C) Makes training faster by shrinking the parameter count
D) Increases the attention scores

**6. Causal masking in decoder attention:**

A) Allows all positions to attend to all others
B) Is only used during inference
C) Is not needed
D) Prevents positions from attending to future positions

**7. The original attention mechanism (for seq2seq) was introduced in:**

A) "GPT-3" (2020)
B) "Attention Is All You Need" (2017) - the paper that introduced self-attention and the full Transformer architecture
C) "BERT: Pre-training of Deep Bidirectional Transformers" (2018)
D) "Neural Machine Translation by Jointly Learning to Align and Translate" (2015) - introduced attention for NMT

**8. Cross-attention connects:**

A) Two different sequences
B) The model to the loss
C) All sequences to each other
D) Tokens within the same sequence

**9. The number of attention heads is typically:**

A) More than one hundred heads in every published base model
B) 1
C) 8-16 for base models
D) Doesn't matter

**10. Attention weights sum to:**

A) 1
B) The sequence length
C) 0
D) Variable amounts

**11. The value of the attention softmax represents:**

A) The gradient flowing through the attention block
B) The importance of each key
C) The learning rate
D) The loss

**12. Positional encoding is needed because:**

A) It's required by the softmax normalization inside attention
B) It reduces memory
C) It improves training speed
D) Attention has no inherent notion of position

**13. Sinusoidal positional encoding:**

A) Is not commonly used
B) Only works for short sequences
C) Uses fixed sine and cosine functions
D) Uses learned embedding tables fitted during pretraining

**14. Rotary Positional Embeddings (RoPE):**

A) Rotate keys and queries based on position
B) Are the same as sinusoidal
C) Are only used in vision transformers and nowhere else
D) Don't encode position

**15. The attention complexity for sequence length n is:**

A) O(n²)
B) O(log n)
C) O(n)
D) O(n³)

**16. Flash Attention optimizes:**

A) Model accuracy
B) The number of parameters
C) Memory access patterns for speed
D) The learning rate schedule around the attention stack

**17. Grouped Query Attention (GQA):**

A) Shares key/value projections across heads
B) Uses more heads
C) Is slower than standard attention
D) Reduces accuracy in every published evaluation

**18. Sliding window attention:**

A) Doesn't work
B) Is only for vision
C) Attends to all positions in the entire sequence
D) Attends only to nearby positions

**19. ALiBi positional encoding:**

A) Uses sinusoidal functions copied from the original Transformer
B) Doesn't exist
C) Adds a bias based on distance
D) Uses learned embeddings

**20. In practice, multi-head attention learns:**

A) Nothing (it's random)
B) Different attention patterns in each head
C) Only one useful head
D) The same thing in each head, with no specialization at all

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-15, 17-20:** [3101: Self-Attention Deep Dive](../3101-Self-Attention-DeepDive.md) — attention mechanics, heads, masking, and position
- **Question 16:** [3102: Flash Attention - IO-Aware Exact Attention](../3102-Flash-Attention.md) — IO-aware attention kernels

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Self-attention weighs how much each token matters relative to every other token |
| 2 | B | Q/K/V are learned linear projections of the same input |
| 3 | B | Scaled dot-product: softmax(QK^T / sqrt(d)) applied to V |
| 4 | D | Multi-head attention runs several heads in parallel and concatenates their outputs |
| 5 | B | The sqrt(d) scaling keeps dot products small so softmax does not saturate |
| 6 | D | Causal masking hides future positions so autoregressive decoding stays honest |
| 7 | D | Bahdanau et al. 2015 introduced attention for NMT; the 2017 paper brought self-attention |
| 8 | A | Cross-attention links two sequences - decoder queries over encoder keys/values |
| 9 | C | Base models typically use 8-16 heads |
| 10 | A | Softmax normalizes the scores, so attention weights sum to 1 |
| 11 | B | The softmax output is the importance weight of each key |
| 12 | D | Attention is permutation-invariant - position must be injected externally |
| 13 | C | Sinusoidal encoding uses fixed sine/cosine functions of position |
| 14 | A | RoPE rotates keys and queries by position-dependent angles |
| 15 | A | Every token attends to every token: O(n^2) in sequence length |
| 16 | C | FlashAttention reorders memory access patterns (tiled softmax) for speed and memory |
| 17 | A | GQA shares key/value projections across query-head groups, shrinking the KV cache |
| 18 | D | Sliding window restricts attention to a local neighborhood |
| 19 | C | ALiBi adds a distance-proportional bias to attention scores |
| 20 | B | Heads specialize - syntax, coreference, and positional patterns differ per head |
