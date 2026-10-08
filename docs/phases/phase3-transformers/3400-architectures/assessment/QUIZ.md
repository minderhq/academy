---
Document ID: 3400-QUIZ
Title: "3400: Model Architectures - Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'transformers', 'architecture']
---

# 3400: Model Architectures - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the key difference between encoder-only and decoder-only models?**

- A) Number of layers
- B) Training data size, a budget axis that shapes capability rather than the mask
- C) Vocabulary size
- D) Attention mask pattern (bidirectional vs causal)

**2. Which architecture is used by BERT?**

- A) Decoder-only
- B) Encoder-only
- C) Encoder-decoder
- D) Retrieval-augmented generation

**3. Which architecture is used by GPT-4?**

- A) Decoder-only
- B) Encoder-only
- C) Encoder-decoder
- D) Hybrid

**4. What is the main advantage of encoder-decoder models?**

- A) Better for sequence-to-sequence tasks
- B) Faster inference
- C) Lower memory usage, a saving the extra cross-attention stack does not deliver
- D) Simpler training

**5. Which model uses encoder-decoder architecture?**

- A) GPT
- B) BERT
- C) T5
- D) LLaMA

**6. What is causal masking?**

- A) Masking padding tokens
- B) Random masking for pretraining, a corruption scheme the causal family never applies
- C) Preventing tokens from attending to future tokens
- D) Masking special tokens

**7. Which attention pattern allows each token to attend to all tokens?**

- A) Causal attention
- B) Sparse attention
- C) Sliding window attention
- D) Bidirectional attention

**8. What is the primary use case for encoder-only models?**

- A) Text generation
- B) Text understanding and classification
- C) Translation, a sequence-to-sequence job this encoder stack was never built to emit
- D) Summarization

**9. What is the primary use case for decoder-only models?**

- A) Text classification
- B) Text generation
- C) Named entity recognition
- D) Sentiment analysis

**10. Why are decoder-only models dominant for LLMs?**

- A) They're easier to train
- B) Better scaling properties
- C) More efficient inference
- D) Training ease, scaling behavior and inference efficiency together

**11. In encoder-decoder models, the decoder accesses the input sequence through:**

- A) Causal self-attention over the input
- B) Cross-attention to encoder outputs
- C) A shared embedding table
- D) Position-wise feedforward layers only

**12. BERT's pretraining objectives are:**

- A) Masked language modeling (and originally next-sentence prediction)
- B) Next-token prediction
- C) Image-text contrastive learning
- D) Reinforcement learning from human feedback, a post-training alignment recipe later systems adopted

**13. The original Transformer paper (2017) used which architecture?**

- A) Decoder-only
- B) Encoder-only
- C) Encoder-decoder
- D) Mixture-of-experts

**14. In GPT-style models, tokens attend to:**

- A) Only previous positions (causal mask)
- B) All positions
- C) Only future positions
- D) Only the current position, an isolation no transformer layer could ever learn from

**15. Which task fits encoder-decoder models best?**

- A) Sentence classification
- B) Text embedding
- C) Language modeling continuation, a decoder-only job this encoder-decoder pair splits in two
- D) Translation from source to target

**16. Mixture-of-Experts (MoE) changes a transformer by:**

- A) Removing attention
- B) Routing each token to a subset of expert FFNs
- C) Replacing self-attention with convolution, a swap no mainstream MoE design has shipped
- D) Sharing one expert across all layers

**17. T5 frames every NLP task as:**

- A) A classification head
- B) A retrieval problem
- C) Text-to-text (text in, text out)
- D) An image captioning task, one vision job far outside T5's text-to-text framing

**18. Which statement about decoder-only inference is true?**

- A) The KV cache lets each step reuse keys/values instead of recomputing past positions
- B) It must re-encode the full prompt at every step, a recompute loop the KV cache eliminates
- C) It cannot reuse computation across steps
- D) It needs cross-attention to be efficient

**19. Encoder-only models output:**

- A) Autoregressive text, a decoder output the bidirectional encoder stack cannot produce
- B) Translations
- C) Audio features
- D) Contextual token representations for downstream heads

**20. A key reason decoder-only dominates modern LLMs:**

- A) It avoids attention entirely
- B) It requires no pretraining data, a claim every scaling curve ever published refutes outright
- C) A simple single-stream objective that scales well with one unified training signal
- D) It cannot be scaled

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | Encoder-only attends bidirectionally; decoder-only is causal |
| 2 | B | BERT is encoder-only |
| 3 | A | GPT-4 is decoder-only |
| 4 | A | Cross-attention between encoder and decoder fits sequence-to-sequence |
| 5 | C | T5 is the canonical encoder-decoder |
| 6 | C | Causal masking prevents tokens from attending to future tokens |
| 7 | D | Bidirectional attention lets every token see every token |
| 8 | B | Encoder-only models shine at understanding and classification |
| 9 | B | Decoder-only models generate text |
| 10 | D | Training ease, scaling behavior, and inference efficiency together |
| 11 | B | The decoder reads the input through cross-attention over encoder states |
| 12 | A | Masked language modeling (plus originally next-sentence prediction) |
| 13 | C | The 2017 paper is the full encoder-decoder Transformer |
| 14 | A | The causal mask restricts each token to previous positions |
| 15 | D | Source-to-target mapping is the seq2seq sweet spot |
| 16 | B | MoE routes each token to a small subset of expert FFNs |
| 17 | C | T5 casts every task as text-to-text |
| 18 | A | The KV cache reuses past keys/values instead of recomputing |
| 19 | D | Encoder-only models emit contextual representations for downstream heads |
| 20 | C | One unified next-token objective that scales cleanly |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-2, 4-5, 7-8, 11-13, 15, 17, 19:** [3401: Encoder-Decoder Architectures](../3401-Encoder-Decoder-Architectures.md) — the family taxonomy read from the attention mask, cross-attention, T5's text-to-text framing, span corruption vs BERT-style token masking, and the 2017 encoder-decoder original
- **Questions 3, 6, 9-10, 14, 18, 20:** [3402: Decoder-Only Models (GPT, LLaMA, Mistral)](../3402-Decoder-Only-Models.md) — causal self-attention, the GPT/LLaMA stack, scale-loves-simplicity and KV-cache inference
- **Question 16:** [3301: Activation Functions](../../3300-decoding/3301-Activation-Functions.md) — the Mixture-of-Experts router and its top-k gated expert FFNs

