---
Document ID: 4200-QUIZ
Title: "4200: KV Cache & Context Window - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
---

# 4200: KV Cache & Context Window - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the primary purpose of KV cache?**

A) Store the frozen weight matrices of the model in HBM
B) Store the raw training corpus on disk between epochs
C) Cache Key and Value tensors to avoid recomputation
D) Compress the model weights into a smaller checkpoint

**2. How much memory does KV cache typically use per token?**

A) Negligible - a few kilobytes for the entire conversation
B) Depends only on vocabulary size, not on model depth
C) Exactly the same footprint as the model weights
D) ~2 bytes per parameter per layer

**3. What is the main bottleneck for long context windows?**

A) Compute time for the softmax over the vocabulary
B) KV cache memory usage
C) The number of transformer layers in the model
D) The size of the pretraining corpus in terabytes

**4. What happens to memory usage as context length increases?**

A) Stays constant
B) Increases linearly O(L)
C) Increases quadratically O(L²)
D) Decreases

**5. What is PagedAttention used for?**

A) Faster attention computation through kernel fusion
B) Efficient KV cache management
C) Model compression into fewer bits per weight
D) Training acceleration via larger batch sizes

**6. What is the main benefit of multi-query attention (MQA) for memory?**

A) Faster computation by skipping the softmax
B) Shared Key/Value projections across heads
C) Better accuracy on every downstream benchmark
D) Simpler architecture by removing attention layers

**7. What is "context window" in LLMs?**

A) The size of the pretraining dataset in tokens
B) Maximum sequence length the model can process
C) The number of attention heads per layer
D) The vocabulary size of the tokenizer

**8. Which technique allows extending context window beyond training length?**

A) RoPE scaling
B) Quantization
C) Pruning
D) Distillation

**9. What is the trade-off with larger context windows?**

A) Faster inference with lower latency per token
B) Higher memory and compute
C) Better accuracy on every evaluation benchmark
D) A smaller model that fits on consumer GPUs

**10. What is sliding window attention?**

A) Processing the whole document again at every step
B) Each token attends only to nearby tokens
C) Using multiple windows in parallel across GPUs
D) Rotating the context window every few steps

**11. Grouped-Query Attention (GQA) is:**

A) Sharing KV heads in groups — a compromise between multi-head and multi-query attention
B) Identical to multi-head attention
C) Removal of the value projection
D) A training optimizer

**12. KV cache memory per token scales with:**

A) Layers × KV heads × head dimension × precision bytes
B) Vocabulary size only
C) Batch size only
D) Context length squared

**13. In speculative decoding, the draft model:**

A) Trains the target model from scratch on fresh synthetic datasets
B) Proposes tokens that the target model verifies in parallel
C) Replaces the target model entirely once it converges
D) Quantizes the target weights to 4-bit precision

**14. Speculative decoding preserves output quality because:**

A) The draft model is larger
B) Sampling temperature is lowered
C) Tokens are cached between runs
D) The target model accepts/rejects draft tokens against its own distribution

**15. KV cache quantization aims to:**

A) Improve accuracy
B) Increase attention compute
C) Reduce cache memory footprint (e.g., 8-bit or 4-bit KV)
D) Extend the vocabulary

**16. During prefill (processing the prompt), inference is typically:**

A) Compute-bound; during decode it becomes memory-bandwidth-bound
B) Memory-bound on every single step of prefill and decode
C) Disk-bound because the weights stream from slow storage
D) Network-bound on every single distributed inference deployment

**17. FlashAttention primarily:**

A) Compresses the KV cache
B) Removes attention
C) Shrinks model weights
D) Speeds up exact attention via IO-aware tiling that reduces GPU memory traffic

**18. RoPE (Rotary Position Embedding) encodes:**

A) Vocabulary IDs of each token with a one-hot position flag
B) Token positions as rotations applied to Q/K vectors
C) Attention dropout rates per transformer layer
D) Layer indices for the residual stream

**19. Extending context beyond training length is commonly done with:**

A) More layers
B) Larger batch size
C) RoPE frequency scaling (e.g., linear or NTK scaling)
D) A reduced vocabulary

**20. Inference frameworks offload KV cache to CPU/disk in order to:**

A) Serve sequences longer than VRAM allows
B) Improve numerical accuracy of the attention scores
C) Reduce the size of the model weights on disk
D) Avoid tokenization of the input prompt entirely

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | C |
| 2 | D |
| 3 | B |
| 4 | B |
| 5 | B |
| 6 | B |
| 7 | B |
| 8 | A |
| 9 | B |
| 10 | B |
| 11 | A |
| 12 | A |
| 13 | B |
| 14 | D |
| 15 | C |
| 16 | A |
| 17 | D |
| 18 | B |
| 19 | C |
| 20 | A |
