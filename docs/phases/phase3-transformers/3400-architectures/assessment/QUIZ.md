---
Document ID: 3400-QUIZ
Title: "3400: Model Architectures - Quiz"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# 3400: Model Architectures - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the key difference between encoder-only and decoder-only models?**

A) Number of layers
B) Attention mask pattern (bidirectional vs causal)
C) Vocabulary size
D) Training data size

**2. Which architecture is used by BERT?**

A) Decoder-only
B) Encoder-only
C) Encoder-decoder
D) None of the above

**3. Which architecture is used by GPT-4?**

A) Decoder-only
B) Encoder-only
C) Encoder-decoder
D) Hybrid

**4. What is the main advantage of encoder-decoder models?**

A) Faster inference
B) Better for sequence-to-sequence tasks
C) Lower memory usage
D) Simpler training

**5. Which model uses encoder-decoder architecture?**

A) GPT
B) BERT
C) T5
D) LLaMA

**6. What is causal masking?**

A) Masking padding tokens
B) Preventing tokens from attending to future tokens
C) Random masking for pretraining
D) Masking special tokens

**7. Which attention pattern allows each token to attend to all tokens?**

A) Causal attention
B) Bidirectional attention
C) Sliding window attention
D) Sparse attention

**8. What is the primary use case for encoder-only models?**

A) Text generation
B) Text understanding and classification
C) Translation
D) Summarization

**9. What is the primary use case for decoder-only models?**

A) Text classification
B) Text generation
C) Named entity recognition
D) Sentiment analysis

**10. Why are decoder-only models dominant for LLMs?**

A) They're easier to train
B) Better scaling properties
C) More efficient inference
D) All of the above

**11. In encoder-decoder models, the decoder accesses the input sequence through:**

A) Causal self-attention over the input
B) Cross-attention to encoder outputs
C) A shared embedding table
D) Position-wise feedforward layers only

**12. BERT's pretraining objectives are:**

A) Masked language modeling (and originally next-sentence prediction)
B) Next-token prediction
C) Image-text contrastive learning
D) Reinforcement learning from human feedback

**13. The original Transformer paper (2017) used which architecture?**

A) Decoder-only
B) Encoder-only
C) Encoder-decoder
D) Mixture-of-experts

**14. In GPT-style models, tokens attend to:**

A) Only previous positions (causal mask)
B) All positions
C) Only future positions
D) Only the current position

**15. Which task fits encoder-decoder models best?**

A) Sentence classification
B) Text embedding
C) Language modeling continuation
D) Translation from source to target

**16. Mixture-of-Experts (MoE) changes a transformer by:**

A) Removing attention
B) Routing each token to a subset of expert FFNs
C) Replacing self-attention with convolution
D) Sharing one expert across all layers

**17. T5 frames every NLP task as:**

A) A classification head
B) A retrieval problem
C) Text-to-text (text in, text out)
D) An image captioning task

**18. Which statement about decoder-only inference is true?**

A) The KV cache lets each step reuse keys/values instead of recomputing past positions
B) It must re-encode the full prompt at every step
C) It cannot reuse computation across steps
D) It needs cross-attention to be efficient

**19. Encoder-only models output:**

A) Autoregressive text
B) Translations
C) Audio features
D) Contextual token representations for downstream heads

**20. A key reason decoder-only dominates modern LLMs:**

A) It avoids attention entirely
B) It requires no pretraining data
C) A simple single-stream objective that scales well with one unified training signal
D) It cannot be scaled

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | B |
| 3 | A |
| 4 | B |
| 5 | C |
| 6 | B |
| 7 | B |
| 8 | B |
| 9 | B |
| 10 | D |
| 11 | B |
| 12 | A |
| 13 | C |
| 14 | A |
| 15 | D |
| 16 | B |
| 17 | C |
| 18 | A |
| 19 | D |
| 20 | C |

---

**Last Updated:** 2026-09-24
