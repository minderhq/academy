---
Document ID: 4200-QUIZ
Title: "4200: KV Cache & Context Window - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'quantization', 'kv-cache']
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
B) The number of transformer layers in the model
C) KV cache memory usage
D) The size of the pretraining corpus in terabytes

**4. What happens to memory usage as context length increases?**

A) Stays constant
B) Decreases
C) Increases quadratically O(L²)
D) Increases linearly O(L)

**5. What is PagedAttention used for?**

A) Faster attention computation through kernel fusion
B) Model compression into fewer bits per weight
C) Efficient KV cache management
D) Training acceleration via larger batch sizes

**6. What is the main benefit of multi-query attention (MQA) for memory?**

A) Faster computation by skipping the softmax
B) Simpler architecture by removing attention layers
C) Better accuracy on every downstream benchmark
D) Shared Key/Value projections across heads

**7. What is "context window" in LLMs?**

A) The size of the pretraining dataset in tokens
B) Maximum sequence length the model can process
C) The number of attention heads per layer
D) The vocabulary size of the tokenizer

**8. Which technique allows extending context window beyond training length?**

A) RoPE scaling
B) Quantization, the standard lever for pushing context past the trained horizon
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
B) Identical to multi-head attention, a claim the KV-head counts of GQA models disprove outright
C) Removal of the value projection
D) A training optimizer

**12. KV cache memory per token scales with:**

A) Layers × KV heads × head dimension × precision bytes
B) Vocabulary size only
C) Batch size only
D) Context length squared, a scaling law that no KV-cache memory formula in production obeys

**13. In speculative decoding, the draft model:**

A) Trains the target model from scratch on fresh synthetic datasets
B) Proposes tokens that the target model verifies in parallel
C) Replaces the target model entirely once it converges
D) Quantizes the target weights to 4-bit precision

**14. Speculative decoding preserves output quality because:**

A) The draft model is larger, an inversion that would make verification pointless and slower
B) Sampling temperature is lowered
C) Tokens are cached between runs
D) The target model accepts/rejects draft tokens against its own distribution

**15. KV cache quantization aims to:**

A) Improve accuracy
B) Increase attention compute
C) Reduce cache memory footprint (e.g., 8-bit or 4-bit KV)
D) Extend the vocabulary, a job the tokenizer owns and quantization never touches

**16. During prefill (processing the prompt), inference is typically:**

A) Compute-bound; during decode it becomes memory-bandwidth-bound
B) Memory-bound on every single step of prefill and decode
C) Disk-bound because the weights stream from slow storage
D) Network-bound on every single distributed inference deployment

**17. FlashAttention primarily:**

A) Compresses the KV cache, a side effect that this exact-attention kernel has never produced
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
B) Larger batch size, a parallelism knob that leaves the trained horizon untouched
C) RoPE frequency scaling (e.g., linear or NTK scaling)
D) A reduced vocabulary

**20. Inference frameworks offload KV cache to CPU/disk in order to:**

A) Serve sequences longer than VRAM allows
B) Improve numerical accuracy of the attention scores
C) Reduce the size of the model weights on disk
D) Avoid tokenization of the input prompt entirely

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | KV cache stores Key and Value tensors so decoding never recomputes them |
| 2 | D | Roughly 2 bytes per parameter per layer at FP16 |
| 3 | C | The KV cache, not compute, is what caps practical context length |
| 4 | D | The cache grows linearly with sequence length |
| 5 | C | PagedAttention manages the KV cache in pages, like virtual memory |
| 6 | D | MQA shares one Key/Value projection across all query heads |
| 7 | B | The context window is the maximum sequence length the model can process |
| 8 | A | RoPE scaling stretches positions past the trained horizon |
| 9 | B | Longer context costs more memory and more attention compute |
| 10 | B | Each token attends only within a nearby window of tokens |
| 11 | A | GQA shares KV heads in groups - a middle ground between MHA and MQA |
| 12 | A | Per token: layers x KV heads x head dimension x precision bytes |
| 13 | B | The draft model proposes tokens; the target verifies them in parallel |
| 14 | D | The target accepts/rejects draft tokens against its own distribution |
| 15 | C | KV quantization shrinks the cache to 8-bit or 4-bit |
| 16 | A | Prefill is compute-bound; decode is memory-bandwidth-bound |
| 17 | D | FlashAttention is exact attention with IO-aware tiling |
| 18 | B | RoPE encodes positions as rotations applied to Q/K vectors |
| 19 | C | Linear or NTK scaling of RoPE frequencies extends context |
| 20 | A | Offloading serves sequences longer than VRAM alone allows |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-4, 7-10, 15, 19-20:** [4201: Context Window Physics and OOM Prevention](../4201-Context-Window-Physics.md) — what the KV cache stores, its per-token memory cost and O(L) growth, RoPE scaling (PI/YaRN) past the trained horizon, the sliding-window cache, KV quantization, and offload as the OOM escape hatch
- **Question 5:** [1402: vLLM and TGI](../../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) — PagedAttention's page-based KV cache management in vLLM
- **Questions 6, 11-12:** [4203: Context Window Optimization Guide](../guides/4203-Context-Window-Optimization.md) — the KV memory formula (2 × heads × head_dim × seq × batch × bytes × layers) and GQA's grouped KV-head sharing, the family MQA sits at the bottom of
- **Questions 13-14:** [4202: Speculative Decoding](../4202-Speculative-Decoding.md) — draft-model proposal with target-model accept/reject verification
- **Question 16:** [4101: GGUF Physics - CPU/GPU Hybrid Offloading](../../4100-low-bit/4101-GGUF-Physics.md) — the prefill-is-compute, decode-is-bandwidth phase table
- **Question 17:** [3102: Flash Attention - IO-Aware Exact Attention](../../../phase3-transformers/3100-attention/3102-Flash-Attention.md) — exact attention via IO-aware tiling that cuts GPU memory traffic
- **Question 18:** [3201: Rotary Positional Embeddings (RoPE)](../../../phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md) — positions encoded as rotations applied to Q/K vectors
