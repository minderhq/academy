# Module 3400: Model Architectures Quiz

**Module:** Model Architectures
**Document ID:** 3400
**Difficulty:** Intermediate
**Time:** 30 minutes

---

## Instructions

Select the best answer for each question. Answers are provided at the bottom.

---

## Questions

### 1. What is the key difference between encoder-only and decoder-only models?

A) Number of layers
B) Attention mask pattern (bidirectional vs causal)
C) Vocabulary size
D) Training data size

### 2. Which architecture is used by BERT?

A) Decoder-only
B) Encoder-only
C) Encoder-decoder
D) None of the above

### 3. Which architecture is used by GPT-4?

A) Decoder-only
B) Encoder-only
C) Encoder-decoder
D) Hybrid

### 4. What is the main advantage of encoder-decoder models?

A) Faster inference
B) Better for sequence-to-sequence tasks
C) Lower memory usage
D) Simpler training

### 5. Which model uses encoder-decoder architecture?

A) GPT
B) BERT
C) T5
D) LLaMA

### 6. What is causal masking?

A) Masking padding tokens
B) Preventing tokens from attending to future tokens
C) Random masking for pretraining
D) Masking special tokens

### 7. Which attention pattern allows each token to attend to all tokens?

A) Causal attention
B) Bidirectional attention
C) Sliding window attention
D) Sparse attention

### 8. What is the primary use case for encoder-only models?

A) Text generation
B) Text understanding and classification
C) Translation
D) Summarization

### 9. What is the primary use case for decoder-only models?

A) Text classification
B) Text generation
C) Named entity recognition
D) Sentiment analysis

### 10. Why are decoder-only models dominant for LLMs?

A) They're easier to train
B) Better scaling properties
C) More efficient inference
D) All of the above

---

## Answers

1. **B** - Encoder uses bidirectional attention, decoder uses causal (autoregressive)
2. **B** - BERT is encoder-only (Bidirectional Encoder Representations from Transformers)
3. **A** - GPT-4 is decoder-only (like all GPT models)
4. **B** - Best for seq2seq tasks like translation, summarization
5. **C** - T5 (Text-to-Text Transfer Transformer) is encoder-decoder
6. **B** - Ensures autoregressive property (can't see future)
7. **B** - Used in encoders for full context understanding
8. **B** - Classification, NER, sentiment analysis, etc.
9. **B** - Text generation, chatbots, code generation
10. **D** - All reasons contribute to decoder dominance

---

**Score:** ___ / 10
**Passing:** 7/10

**Next:** Review [PRACTICE.md](./PRACTICE.md) for hands-on exercises
