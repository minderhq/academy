---
Document ID: PHASE3-QUIZ
Title: "Phase 3: Transformer Physics Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Tags: ['assessment', 'quiz', 'transformers']
---

# Phase 3: Transformer Physics Quiz

**25 Questions | Passing Score: 80% | Time: 45 minutes**

---

## Questions

### 1. What is the core innovation of transformer architecture?
a) Recurrent connections
b) Convolutional layers
c) Self-attention mechanism
d) Pooling layers stacked to shorten sequences

**Answer:** c

---

### 2. What is the purpose of multi-head attention?
a) Reduce memory usage
b) Simplifying the overall model architecture
c) Learning multiple attention patterns
d) Increase model speed

**Answer:** c

---

### 3. What does RoPE stand for?
a) Relative Position Encoding
b) Recursive Pattern Enhancement
c) Rotary Position Embedding
d) Random Parameter Estimation

**Answer:** c

---

### 4. What is causal masking used for?
a) Prevent attention to future tokens
b) Speed up training
c) Reduce overfitting through masked dropout schedules
d) Increase model capacity

**Answer:** a

---

### 5. What is Flash Attention?
a) Memory-efficient attention implementation
b) Improved accuracy from reordering softmax inputs
c) Smaller model size
d) Faster model training

**Answer:** a

---

### 6. What is the formula for scaled dot-product attention?
a) softmax(QK^T / √d_k)V
b) QK^TV
c) softmax(Q + K) * V
d) softmax(QK)V

**Answer:** a

---

### 7. What is a KV cache used for?
a) Training acceleration
b) Model compression applied to cached encoder states after every decode step
c) Storing computed keys and values for faster generation
d) Data augmentation

**Answer:** c

---

### 8. What is BPE (Byte Pair Encoding)?
a) Subword tokenization algorithm
b) Batch Processing Engine
c) Backward Propagation Encoder shipped with older tokenizers
d) Binary Pattern Extraction

**Answer:** a

---

### 9. What is GELU activation?
a) Generalized Linear Unit
b) Gaussian Error Linear Unit
c) Gradient Enhanced Learning Unit
d) Gated Excitation Layer Unit

**Answer:** b

---

### 10. Why is SwiGLU preferred over ReLU in transformers?
a) Less memory consumed by the gating branch during every forward sweep
b) Simpler implementation
c) Faster computation
d) Better gradient flow and no dead neurons

**Answer:** d

---

### 11. What is LayerNorm?
a) Normalization across batch
b) Normalization across features
c) Normalization across time steps within each sequence window
d) Normalization across layers

**Answer:** b

---

### 12. What is the difference between decoder-only and encoder-decoder models?
a) Decoder-only has more parameters
b) Encoder-decoder cannot generate text
c) Encoder-decoder is faster
d) Decoder-only uses causal masking for generation

**Answer:** d

---

### 13. What is ALiBi?
a) Adaptive Layer Bias
b) Attention with Linear Biases
c) Associative Learning Interface
d) Automated Linear Integration

**Answer:** b

---

### 14. What is SentencePiece?
a) Document parser
b) Text classifier
c) Language model
d) Unigram language model tokenizer

**Answer:** d

---

### 15. What is TikToken?
a) Token counting tool
b) OpenAI's tokenizer for GPT models
c) Text generation library bundled with token counting utilities
d) Token encryption method

**Answer:** b

---

### 16. What is pre-Norm vs post-Norm?
a) Training before vs after inference
b) Normalization of first vs last layers
c) Normalization before vs after residual connection
d) Early vs late stopping

**Answer:** c

---

### 17. What is a mixture of experts (MoE)?
a) Ensemble of models
b) Multi-task learning
c) Knowledge distillation
d) Model with sparse activation of expert sub-networks

**Answer:** d

---

### 18. What is the benefit of RoPE over learned positional embeddings?
a) Simpler implementation
b) Better extrapolation to longer sequences
c) Less memory
d) Faster training

**Answer:** b

---

### 19. What is cross-attention used for?
a) Self-attention within decoder
b) Attention between heads sharing cached projections across decoder layers
c) Attention across layers
d) Attending to encoder outputs in encoder-decoder models

**Answer:** d

---

### 20. What is the key difference between GPT and BERT?
a) GPT is smaller
b) BERT generates text
c) GPT classifies text while BERT drafts continuations token by token
d) GPT is decoder-only, BERT is encoder-only

**Answer:** d

---

### 21. What is the attention head dimension?
a) d_model * num_heads scaled by per-head gains
b) num_heads / d_model
c) d_model / num_heads
d) d_model + num_heads

**Answer:** c

---

### 22. What is feed-forward network (FFN) in transformers?
a) Two-layer MLP with activation
b) Attention mechanism
c) Output layer
d) Embedding layer

**Answer:** a

---

### 23. What is the purpose of residual connections?
a) Reduce parameters
b) Enable gradient flow in deep networks
c) Speed up inference
d) Improve accuracy

**Answer:** b

---

### 24. What is a vision-language model (VLM)?
a) Model that processes both images and text
b) Visual model architecture
c) Language model for vision
d) Visualization tool for models

**Answer:** a

---

### 25. What is the main advantage of decoder-only models for text generation?
a) Autoregressive generation is natural
b) Less memory
c) Simpler architecture without an encoder
d) Faster training

**Answer:** a

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

