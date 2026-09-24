# Module 4200: KV Cache & Context Window Quiz

**Module:** KV Cache & Context Window Physics
**Document ID:** 4200
**Difficulty:** Advanced
**Time:** 30 minutes

---

## Instructions

Select the best answer for each question. Answers are provided at the bottom.

---

## Questions

### 1. What is the primary purpose of KV cache?

A) Store model weights
B) Cache Key and Value tensors to avoid recomputation
C) Store training data
D) Compress the model

### 2. How much memory does KV cache typically use per token?

A) Negligible
B) ~2 bytes per parameter per layer
C) Same as model weights
D) Depends only on vocabulary size

### 3. What is the main bottleneck for long context windows?

A) Compute time
B) KV cache memory usage
C) Model size
D) Training data

### 4. What happens to memory usage as context length increases?

A) Stays constant
B) Increases linearly O(L)
C) Increases quadratically O(L²)
D) Decreases

### 5. What is PagedAttention used for?

A) Faster attention computation
B) Efficient KV cache management
C) Model compression
D) Training acceleration

### 6. What is the main benefit of multi-query attention (MQA) for memory?

A) Faster computation
B) Shared Key/Value projections across heads
C) Better accuracy
D) Simpler architecture

### 7. What is "context window" in LLMs?

A) Training dataset size
B) Maximum sequence length the model can process
C) Number of layers
D) Vocabulary size

### 8. Which technique allows extending context window beyond training length?

A) RoPE scaling
B) Quantization
C) Pruning
D) Distillation

### 9. What is the trade-off with larger context windows?

A) Faster inference
B) Higher memory and compute
C) Better accuracy
D) Smaller model size

### 10. What is sliding window attention?

A) Processing windows sequentially
B) Each token attends only to nearby tokens
C) Using multiple windows in parallel
D) Rotating the context window

---

## Answers

1. **B** - Caches K,V from previous tokens to avoid recomputing
2. **B** - Each token adds ~2 bytes × model dimension × num_layers
3. **B** - KV cache memory grows with context length
4. **B** - Linear growth: each new token adds K,V vectors
5. **B** - PagedAttention (vLLM) manages KV cache efficiently
6. **B** - Reduces KV cache size by sharing across attention heads
7. **B** - Maximum input sequence length (e.g., 4K, 32K, 128K)
8. **A** - Rotary Position Embedding scaling extends context
9. **B** - More memory for KV cache, more compute for attention
10. **B** - Sparse attention pattern for efficiency

---

**Score:** ___ / 10
**Passing:** 7/10

**Next:** Review [PRACTICE.md](./PRACTICE.md) for hands-on exercises
