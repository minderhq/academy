---
Document ID: PHASE3-CHECKPOINT
Title: "Progress Checkpoint: Phase 3 - Transformer Physics"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Tags: ['checkpoint', 'transformers', 'embeddings', 'rope']
---

# Progress Checkpoint: Phase 3 - Transformer Physics

**Track your progress through Phase 3 modules**

---

## Phase 3 Overview

**Phase:** [3000] Transformer Physics & LLM Internals
**Modules:** 5 (3100, 3200, 3300, 3400, 3500)
**Estimated Time:** 3-4 weeks
**Difficulty:** ⭐⭐⭐ Advanced

---

## Phase Completion Goal

After completing Phase 3, you will:

- Understand self-attention mechanism
- Know embedding architectures
- Understand model architectures
- Be ready for quantization

---

## Module Checkpoints

### Module 3100: Attention Architectures (Required)

**Checkpoint Quiz:**

1. What is the self-attention mechanism?
2. Explain query, key, value paradigm
3. What is multi-head attention?

**Practical Verification:**

- [ ] Can walk through scaled dot-product attention step by step
- [ ] Can explain the query, key, value roles with a concrete example
- [ ] Has traced multi-head attention tensor shapes (d_model, heads, d_k)

---

### Module 3200: Embedding Latent Spaces (Required)

**Checkpoint Quiz:**

1. What is RoPE and why is it used?
2. How do tokenizers work?
3. What are positional embeddings?

**Practical Verification:**

- [ ] Can explain how RoPE encodes position through rotation
- [ ] Has tokenized text with a BPE tokenizer and inspected the ids
- [ ] Can compare learned, sinusoidal and RoPE positional schemes

---

### Module 3300: The Decoding Block (Required)

**Checkpoint Quiz:**

1. How do GELU and SwiGLU improve on plain ReLU?
2. Why do transformers prefer LayerNorm or RMSNorm over BatchNorm?
3. How does Pre-Norm vs Post-Norm placement affect training stability?

**Practical Verification:**

- [ ] Can explain why GELU and SwiGLU beat plain ReLU in transformers
- [ ] Can justify LayerNorm or RMSNorm over BatchNorm for sequences
- [ ] Can reason about Pre-Norm vs Post-Norm stability tradeoffs

---

### Module 3400: Model Architectures (Required)

**Checkpoint Quiz:**

1. Difference between encoder-only, decoder-only, encoder-decoder
2. What makes GPT-style models unique?
3. When to use each architecture?

**Practical Verification:**

- [ ] Can classify a model as encoder-only, decoder-only or encoder-decoder
- [ ] Can explain what makes GPT-style decoder stacks distinctive
- [ ] Can pick an architecture family for a given task

---

### Module 3500: Multimodal Models (Required)

**Checkpoint Quiz:**

1. How do vision-language models combine visual and text tokens?
2. What are the building blocks of an audio model pipeline?
3. When does multimodal RAG outperform text-only RAG?

**Practical Verification:**

- [ ] Can trace how visual tokens join text tokens in a VLM
- [ ] Can sketch an audio model pipeline (tokenizer, encoder, decoder)
- [ ] Can decide when multimodal RAG beats text-only RAG

---

## Common Pitfalls

1. **Missing Scaling:** Omitting the 1/sqrt(d_k) factor lets dot products grow with dimension and pushes softmax into saturated, near-uniform gradients
2. **Causal Mask Off-By-One:** A mask that lets position i attend to i+1 trains a model that cheats on next-token prediction and fails at generation
3. **RoPE Cache Offset:** Reusing cached keys with a zero offset replays stale positions and degrades long-context generation quality
4. **Norm Placement Regret:** Switching Post-Norm to Pre-Norm mid-experiment confounds every stability comparison - fix the placement before tuning LR

---

## Phase 3 Completion Badge

**Badge:** Transformer Expert

**You've earned it when:**

- All required modules completed
- Can implement self-attention from scratch
- Understand LLM architecture
