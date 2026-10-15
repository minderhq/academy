---
Document ID: PHASE3-QUIZ
Title: "Phase 3: Transformer Physics Quiz"
Last Updated: 2026-10-15
Status: Complete
Difficulty: Advanced
Tags: ['assessment', 'quiz', 'transformers']
---

# Phase 3: Transformer Physics Quiz

**25 Questions | Passing Score: 80% | Time: 45 minutes**

## Instructions

- **25 questions**, one best answer each
- **Passing score: 80%** (20/25 correct)
- Answers live only in the Answer Key at the end of this quiz - attempt every question before checking it
- Graded below the line? The Need to Review? map above the Answer Key links every question to its closest lesson - rework those before your next attempt
- **Practice:** [Phase 3 Practice](phase3-practice.md) - Hands-on exercises

---

## Questions

### 1. What is the core innovation of transformer architecture?
- a) Recurrent connections
- b) Convolutional layers
- c) Self-attention mechanism
- d) Pooling layers stacked to shorten sequences

---

### 2. What is the purpose of multi-head attention?
- a) Reduce memory usage
- b) Simplifying the overall model architecture
- c) Learning multiple attention patterns
- d) Increase model speed

---

### 3. What does RoPE stand for?
- a) Relative Position Encoding
- b) Recursive Pattern Enhancement
- c) Rotary Position Embedding
- d) Random Parameter Estimation

---

### 4. What is causal masking used for?
- a) Prevent attention to future tokens
- b) Speed up training
- c) Reduce overfitting through masked dropout schedules
- d) Increase model capacity

---

### 5. What is Flash Attention?
- a) Memory-efficient attention implementation
- b) Improved accuracy from reordering softmax inputs
- c) Smaller model size
- d) Faster model training

---

### 6. What is the formula for scaled dot-product attention?
- a) softmax(QK^T / √d_k)V
- b) QK^TV
- c) softmax(Q + K) * V
- d) softmax(QK)V

---

### 7. What is a KV cache used for?
- a) Training acceleration
- b) Model compression applied to cached encoder states after every decode step
- c) Storing computed keys and values for faster generation
- d) Data augmentation

---

### 8. What is BPE (Byte Pair Encoding)?
- a) Subword tokenization algorithm
- b) Batch Processing Engine
- c) Backward Propagation Encoder shipped with older tokenizers
- d) Binary Pattern Extraction

---

### 9. What is GELU activation?
- a) Generalized Linear Unit
- b) Gaussian Error Linear Unit
- c) Gradient Enhanced Learning Unit
- d) Gated Excitation Layer Unit

---

### 10. Why is SwiGLU preferred over ReLU in transformers?
- a) Less memory consumed by the gating branch during every forward sweep
- b) Simpler implementation
- c) Faster computation
- d) Better gradient flow and no dead neurons

---

### 11. What is LayerNorm?
- a) Normalization across batch
- b) Normalization across features
- c) Normalization across time steps within each sequence window
- d) Normalization across layers

---

### 12. What is the difference between decoder-only and encoder-decoder models?
- a) Decoder-only has more parameters
- b) Encoder-decoder cannot generate text
- c) Encoder-decoder is faster
- d) Decoder-only uses causal masking for generation

---

### 13. What is ALiBi?
- a) Adaptive Layer Bias
- b) Attention with Linear Biases
- c) Associative Learning Interface
- d) Automated Linear Integration

---

### 14. What is SentencePiece?
- a) Document parser
- b) Text classifier
- c) Language model
- d) Unigram language model tokenizer

---

### 15. What is TikToken?
- a) Token counting tool
- b) OpenAI's tokenizer for GPT models
- c) Text generation library bundled with token counting utilities
- d) Token encryption method

---

### 16. What is pre-Norm vs post-Norm?
- a) Training before vs after inference
- b) Normalization of first vs last layers
- c) Normalization before vs after residual connection
- d) Early vs late stopping

---

### 17. What is a mixture of experts (MoE)?
- a) Ensemble of models
- b) Multi-task learning
- c) Knowledge distillation
- d) Model with sparse activation of expert sub-networks

---

### 18. What is the benefit of RoPE over learned positional embeddings?
- a) Simpler implementation
- b) Better extrapolation to longer sequences
- c) Less memory
- d) Faster training

---

### 19. What is cross-attention used for?
- a) Self-attention within decoder
- b) Attention between heads sharing cached projections across decoder layers
- c) Attention across layers
- d) Attending to encoder outputs in encoder-decoder models

---

### 20. What is the key difference between GPT and BERT?
- a) GPT is smaller
- b) BERT generates text
- c) GPT classifies text while BERT drafts continuations token by token
- d) GPT is decoder-only, BERT is encoder-only

---

### 21. What is the attention head dimension?
- a) d_model * num_heads scaled by per-head gains
- b) num_heads / d_model
- c) d_model / num_heads
- d) d_model + num_heads

---

### 22. What is feed-forward network (FFN) in transformers?
- a) Two-layer MLP with activation
- b) Attention mechanism
- c) Output layer
- d) Embedding layer

---

### 23. What is the purpose of residual connections?
- a) Reduce parameters
- b) Enable gradient flow in deep networks
- c) Speed up inference
- d) Improve accuracy

---

### 24. What is a vision-language model (VLM)?
- a) Model that processes both images and text
- b) Visual model architecture
- c) Language model for vision
- d) Visualization tool for models

---

### 25. What is the main advantage of decoder-only models for text generation?
- a) Autoregressive generation is natural
- b) Less memory
- c) Simpler architecture without an encoder
- d) Faster training

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-2, 4, 21:** [3101: Self-Attention DeepDive](../../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md) — the attention core, multi-head splits, causal masking and head dimensions
- **Questions 3, 13, 18:** [3201: Rotary Positional Embeddings RoPE](../../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md) — rotary embeddings, ALiBi biases and length extrapolation
- **Question 5:** [3102: Flash Attention](../../phases/phase3-transformers/3100-attention/3102-Flash-Attention.md) — Flash Attention and its memory efficiency
- **Question 6:** [3103: SDPA and torch compile](../../phases/phase3-transformers/3100-attention/3103-SDPA-and-torch-compile.md) — the scaled dot-product attention formula
- **Question 7:** [4201: Context Window Physics](../../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md) — the KV cache that pays for fast generation
- **Questions 8, 14-15:** [3202: Tokenizer Sciences](../../phases/phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md) — BPE, SentencePiece and tiktoken
- **Questions 9-10, 22:** [3301: Activation Functions](../../phases/phase3-transformers/3300-decoding/3301-Activation-Functions.md) — GELU, SwiGLU and the feed-forward block
- **Questions 11, 16, 23:** [3302: Normalization Layers](../../phases/phase3-transformers/3300-decoding/3302-Normalization-Layers.md) — LayerNorm, pre-Norm vs post-Norm ordering and residual flow
- **Questions 12, 19:** [3401: Encoder-Decoder Architectures](../../phases/phase3-transformers/3400-architectures/3401-Encoder-Decoder-Architectures.md) — cross-attention to encoder outputs
- **Question 17:** [3404: Beyond Attention SSMs and MLA](../../phases/phase3-transformers/3400-architectures/3404-Beyond-Attention-SSMs-and-MLA.md) — mixture of experts and sparse activation
- **Questions 20, 25:** [3402: Decoder-Only Models](../../phases/phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md) — GPT-style decoder-only autoregressive generation
- **Question 24:** [3501: Vision-Language Models](../../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md) — vision-language models

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Self-attention replaced recurrence, letting every token attend to every other in parallel |
| 2 | C | Multiple heads let the model learn different attention patterns in parallel |
| 3 | C | RoPE stands for Rotary Position Embedding |
| 4 | A | Causal masking hides future tokens so generation stays autoregressive |
| 5 | A | Flash Attention computes exact attention with a memory-efficient tiling, not by reordering softmax inputs |
| 6 | A | Scaled dot-product attention is softmax(QK^T / sqrt(d_k))V |
| 7 | C | The KV cache stores computed keys and values so each decode step skips recomputing them |
| 8 | A | BPE is a subword tokenization algorithm that merges frequent byte pairs |
| 9 | B | GELU stands for Gaussian Error Linear Unit |
| 10 | D | SwiGLU's gated form gives better gradient flow and avoids dead neurons |
| 11 | B | LayerNorm normalizes across the feature dimension of each token |
| 12 | D | Decoder-only models use causal masking to generate; encoder-decoder reads bidirectionally first |
| 13 | B | ALiBi stands for Attention with Linear Biases |
| 14 | D | SentencePiece is a unigram language-model tokenizer |
| 15 | B | tiktoken is OpenAI's tokenizer for its GPT models |
| 16 | C | Pre-Norm applies normalization before the residual branch, post-Norm after it |
| 17 | D | MoE is a model with sparse activation of expert sub-networks, not an ensemble |
| 18 | B | RoPE's rotary form extrapolates to longer sequences than a fixed learned embedding table |
| 19 | D | Cross-attention lets decoder queries attend to the encoder's outputs |
| 20 | D | GPT is decoder-only, BERT is encoder-only |
| 21 | C | The per-head dimension is d_model divided by num_heads |
| 22 | A | The FFN is a two-layer MLP with an activation between the layers |
| 23 | B | Residual connections give gradients a short path through deep stacks |
| 24 | A | A VLM processes both images and text |
| 25 | A | Autoregressive generation is the decoder-only architecture's native mode |

**Passing: 20/25 (80%)**

