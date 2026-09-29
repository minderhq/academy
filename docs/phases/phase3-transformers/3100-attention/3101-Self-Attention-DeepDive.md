---
Document ID: 3101
Title: "3101: Self-Attention Deep Dive"
Phase: 3
Module: 3100
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: Phase 2 completion (tensor algebra, neural network fundamentals)
Related: [3102, 3201, 3302, 3402]
Tags: [transformers, attention, self-attention, flash-attention, multi-head]
Hardware: [GPU recommended for visualization]
Software: [Python 3.13+, PyTorch 2.0+, matplotlib]
---

# 3101: Self-Attention Deep Dive

## Abstract

Self-attention is the core mechanism that powers Transformer models. This document provides a comprehensive deep dive into the scaled dot-product attention formula, multi-head attention architectures, causal masking, and attention pattern visualization. You will learn how attention enables models to weigh token importance, capture long-range dependencies, and process sequences in parallel.

---

## Table of Contents

- [1. Overview](#1-overview)
- [Learning Objectives](#learning-objectives)
- [2. The Attention Mechanism](#2-the-attention-mechanism)
  - [2.1 Scaled Dot-Product Attention](#21-scaled-dot-product-attention)
  - [2.2 Step-by-Step Computation](#22-step-by-step-computation)
- [3. Multi-Head Attention](#3-multi-head-attention)
  - [3.1 Why Multiple Heads?](#31-why-multiple-heads)
  - [3.2 Multi-Head Architecture](#32-multi-head-architecture)
  - [3.3 Mathematical Formulation](#33-mathematical-formulation)
- [4. Attention Patterns Visualization](#4-attention-patterns-visualization)
- [5. Masked (Causal) Attention](#5-masked-causal-attention)
- [6. Attention as a Graph](#6-attention-as-a-graph)
- [7. Attention Efficiency](#7-attention-efficiency)
- [8. Attention Variants](#8-attention-variants)
- [Summary](#summary)
- [9. References](#9-references)
- [10. Next Steps](#10-next-steps)

---

## 1. Overview

### 1.1 Purpose

This document provides an in-depth exploration of self-attention—the fundamental operation that distinguishes Transformers from previous architectures. Understanding attention is essential for grasping how modern LLMs process and generate text.

### 1.2 Prerequisites

- **Math:** Matrix multiplication, softmax function, basic probability
- **Programming:** Python, PyTorch tensors
- **Previous:** [2101: Tensor Algebra](../../phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)

## Learning Objectives
After completing this document, you will:
- ✅ Understand the scaled dot-product attention formula
- ✅ Implement attention from scratch in PyTorch
- ✅ Explain why multi-head attention improves performance
- ✅ Differentiate between causal and bidirectional attention
- ✅ Analyze attention patterns and visualize them
- ✅ Understand computational complexity and optimization strategies

---

## 2. The Attention Mechanism

### 2.1 Scaled Dot-Product Attention

```text
The fundamental operation of Transformers:

Attention(Q, K, V) = softmax(QK^T / √d_k) × V

Where:
- Q (Query): What this token is looking for
- K (Key): What other tokens offer
- V (Value): The actual content of tokens
- d_k: Dimension of keys (scaling factor)
```

### 2.2 Step-by-Step Computation

```python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q, K, V: (batch, num_heads, seq_len, d_k)
    mask: (batch, 1, 1, seq_len) or (batch, 1, seq_len, seq_len)
    """
    d_k = Q.size(-1)

    # 1. Compute scores (similarity between queries and keys)
    scores = torch.matmul(Q, K.transpose(-2, -1))  # (B, H, L, L)
    # scores[b, h, i, j] = similarity between token i and j

    # 2. Scale by √d_k (prevents softmax saturation)
    scores = scores / (d_k ** 0.5)

    # 3. Apply mask (optional, for causal attention)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)

    # 4. Softmax over keys (get attention weights)
    attn_weights = F.softmax(scores, dim=-1)  # (B, H, L, L)

    # 5. Weight values by attention weights
    output = torch.matmul(attn_weights, V)  # (B, H, L, d_k)

    return output, attn_weights
```

---

## 3. Multi-Head Attention

### 3.1 Why Multiple Heads?

```text
Single head: Each token attends to all tokens with one pattern
Multiple heads: Each token attends with multiple patterns simultaneously

Example: For sentence "The cat sat on the mat"
- Head 1: Focuses on subject-verb agreement ("cat" ↔ "sat")
- Head 2: Focuses on noun phrase structure ("The" ↔ "cat")
- Head 3: Focuses on preposition relationships ("sat" ↔ "on")
```

### 3.2 Multi-Head Architecture

```python
import torch.nn as nn
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model=512, num_heads=8):
        super().__init__()
        assert d_model % num_heads == 0

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads  # 64 for d_model=512, heads=8

        # Linear projections for Q, K, V
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)

        # Output projection
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        # 1. Linear projections and reshape
        # (B, L, D) → (B, L, H, d_k) → (B, H, L, d_k)
        Q = self.W_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        # 2. Scaled dot-product attention
        attn_output, attn_weights = scaled_dot_product_attention(Q, K, V, mask)

        # 3. Concatenate heads
        # (B, H, L, d_k) → (B, L, H, d_k) → (B, L, D)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)

        # 4. Final linear projection
        output = self.W_o(attn_output)

        return output, attn_weights
```

### 3.3 Mathematical Formulation

```text
Given input X (sequence of embeddings):

MultiHead(X) = Concat(head_1, ..., head_h) × W^O

Where head_i = Attention(Q × W_i^Q, K × W_i^K, V × W_i^V)

Dimensions:
- X: (L, d_model) where L = sequence length
- W_i^Q, W_i^K, W_i^V: (d_model, d_k) where d_k = d_model / h
- Q, K, V: (L, d_k)
- head_i: (L, d_k)
- Concat: (L, d_model)
- W^O: (d_model, d_model)
- Output: (L, d_model)
```

---

## 4. Attention Patterns Visualization

### Common Attention Patterns

```python
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_attention(attn_weights, tokens, head_idx=0):
    """
    attn_weights: (num_heads, seq_len, seq_len)
    tokens: list of token strings
    head_idx: which head to visualize
    """
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        attn_weights[head_idx].detach().cpu().numpy(),
        xticklabels=tokens,
        yticklabels=tokens,
        cmap='viridis',
        cbar=True
    )
    plt.title(f'Attention Head {head_idx}')
    plt.xlabel('Keys')
    plt.ylabel('Queries')
    plt.show()

# Example usage
tokens = ['The', 'cat', 'sat', 'on', 'the', 'mat', '.']
attn_weights = torch.rand(8, len(tokens), len(tokens))
attn_weights = F.softmax(attn_weights, dim=-1)
visualize_attention(attn_weights, tokens, head_idx=0)
```

### Pattern Types

```text
1. Diagonal (Self-Attention):
   Each token attends to itself
   Use case: Positional encoding reinforcement

2. Local (Sliding Window):
   Each token attends to nearby tokens
   Use case: Efficient long sequences

3. Global (Dilated):
   Some tokens attend broadly, others locally
   Use case: Long-range dependency modeling

4. Causal (Autoregressive):
   Token i only attends to tokens < i
   Use case: Language modeling (GPT-style)
```

---

## 5. Masked (Causal) Attention

### Causal Mask

```python
def causal_mask(seq_len):
    """
    Creates a causal mask for autoregressive generation
    Token i can only attend to tokens 0 to i
    """
    mask = torch.tril(torch.ones(seq_len, seq_len))
    return mask  # (seq_len, seq_len)

# Usage in attention
seq_len = 5
mask = causal_mask(seq_len)
print(mask)
# tensor([
#   [1, 0, 0, 0, 0],  # Token 0: attends to 0
#   [1, 1, 0, 0, 0],  # Token 1: attends to 0,1
#   [1, 1, 1, 0, 0],  # Token 2: attends to 0,1,2
#   [1, 1, 1, 1, 0],  # Token 3: attends to 0,1,2,3
#   [1, 1, 1, 1, 1],  # Token 4: attends to 0,1,2,3,4
# ])
```

### Causal Attention Implementation

```python
def causal_attention(Q, K, V):
    """
    Causal (autoregressive) attention
    Used in decoder-only models (GPT, LLaMA, etc.)
    """
    seq_len = Q.size(2)
    d_k = Q.size(-1)

    scores = torch.matmul(Q, K.transpose(-2, -1)) / (d_k ** 0.5)

    # Create causal mask
    mask = torch.tril(torch.ones(seq_len, seq_len, device=Q.device))
    scores = scores.masked_fill(mask == 0, -1e9)

    attn_weights = F.softmax(scores, dim=-1)
    output = torch.matmul(attn_weights, V)

    return output, attn_weights
```

---

## 6. Attention as a Graph

### Interpretation

```text
Attention can be viewed as a directed weighted graph:

Nodes: Tokens in the sequence
Edges: Attention weights (directed from query to key)
Weights: Attention score (softmax output)

Example for "The cat sat":
  The  ──► cat   (weight: 0.6)
   │
   └──► sat    (weight: 0.3)
  cat  ──► sat   (weight: 0.8)
  sat  ──► The   (weight: 0.1)  [lower weight]
```

### Graph Properties

```python
def attention_graph_properties(attn_weights):
    """
    Analyze attention as a graph
    """
    # Average in-degree (how much each token is attended to)
    in_degree = attn_weights.mean(dim=-2)  # (seq_len,)

    # Average out-degree (how much each token attends)
    out_degree = attn_weights.mean(dim=-1)  # (seq_len,)

    # Attention entropy (measure of "focus")
    entropy = -(attn_weights * torch.log(attn_weights + 1e-9)).sum(dim=-1)

    return {
        'in_degree': in_degree,
        'out_degree': out_degree,
        'entropy': entropy
    }
```

---

## 7. Attention Efficiency

### Time and Space Complexity

```text
Standard Attention:
  Time: O(L² × d)  - L² from QK^T, d from final matmul
  Space: O(L²)     - Store attention matrix

Where:
  L = sequence length
  d = model dimension

For L = 2048, d = 512:
  Time: O(2048² × 512) ≈ 2.1B operations
  Space: O(2048²) ≈ 4M elements ≈ 16MB (float32)

This is the main bottleneck for long sequences!
```

### Memory-Efficient Attention

```python
def memory_efficient_attention(Q, K, V, chunk_size=64):
    """
    Compute attention in chunks to reduce memory usage
    Trades compute for memory
    """
    batch_size, num_heads, seq_len, d_k = Q.size()

    outputs = []

    # Process queries in chunks
    for i in range(0, seq_len, chunk_size):
        Q_chunk = Q[:, :, i:i+chunk_size, :]  # (B, H, chunk, d_k)

        # Compute attention for this chunk
        scores = torch.matmul(Q_chunk, K.transpose(-2, -1)) / (d_k ** 0.5)
        attn_weights = F.softmax(scores, dim=-1)
        output_chunk = torch.matmul(attn_weights, V)  # (B, H, chunk, d_k)

        outputs.append(output_chunk)

    return torch.cat(outputs, dim=2)  # (B, H, L, d_k)

# Memory: O(L × chunk_size) instead of O(L²)
```

---

## 8. Attention Variants

### Sparse Attention

```python
# Longformer-style sliding window attention
def sliding_window_attention(Q, K, V, window_size=64):
    """
    Each token only attends to nearby tokens (sliding window)
    Reduces complexity from O(L²) to O(L × window_size)
    """
    batch_size, num_heads, seq_len, d_k = Q.size()

    # Create sliding window mask
    mask = torch.zeros(seq_len, seq_len, device=Q.device)
    for i in range(seq_len):
        start = max(0, i - window_size // 2)
        end = min(seq_len, i + window_size // 2 + 1)
        mask[i, start:end] = 1

    # Apply mask
    scores = torch.matmul(Q, K.transpose(-2, -1)) / (d_k ** 0.5)
    scores = scores.masked_fill(mask.unsqueeze(0).unsqueeze(0) == 0, -1e9)

    attn_weights = F.softmax(scores, dim=-1)
    output = torch.matmul(attn_weights, V)

    return output, attn_weights
```

### Cross-Attention

```python
def cross_attention(Q, K, V):
    """
    Cross-attention: Q from one sequence, K and V from another
    Used in encoder-decoder architectures
    """
    # Q: (batch, seq_len_q, d_model)
    # K, V: (batch, seq_len_kv, d_model)

    # Same as self-attention, but different sources
    scores = torch.matmul(Q, K.transpose(-2, -1)) / (Q.size(-1) ** 0.5)
    attn_weights = F.softmax(scores, dim=-1)
    output = torch.matmul(attn_weights, V)

    return output, attn_weights

# Use case: Translation
# Q: Target sentence (decoded so far)
# K, V: Source sentence (fully encoded)
```

---

## Summary

Self-attention is the mechanism the Transformer is built on: the scaled dot-product formula lets every token weigh every other token, multi-head attention runs several such comparisons in parallel subspaces, and causal masking keeps autoregressive training honest. This deep dive covered the formula, multi-head architecture, attention pattern visualization, masked attention, attention as a graph, efficiency, and the variant landscape. The rule it leaves: attention is a learned, differentiable dictionary lookup - once you see it that way, its parallelism, its quadratic cost, and every efficiency fix that follows make sense.

## 9. References

### Academic Papers
- [1] Vaswani et al. "Attention Is All You Need". NeurIPS, 2017.
- [2] Dao et al. "Flash Attention: Fast and Memory-Efficient Exact Attention". ICLR, 2023.

### Documentation
- [PyTorch nn.MultiheadAttention](https://pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html) - Official implementation

### Related PROJECT-OMEGA Documents
- [3102: Flash Attention](./3102-Flash-Attention.md) - Memory-efficient attention
- [3201: RoPE](../3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md) - Positional encoding
- [3302: Normalization Layers](../3300-decoding/3302-Normalization-Layers.md) - LayerNorm, RMSNorm
- [3402: Decoder-Only Models](../3400-architectures/3402-Decoder-Only-Models.md) - GPT, LLaMA

### Experiments
- [EXP_3101: Self-Attention](../../../../experiments/EXP_3101_SELF_ATTENTION.md) - Implement attention from scratch

### External Resources
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) - Visual guide
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - Original paper

---

## 10. Next Steps

- Continue with: **[3102: Flash Attention](./3102-Flash-Attention.md)**
- Next Module: **[3200: Embedding Latent Spaces](../3200-embeddings/)**
- Practical: **[EXP_3101: Self-Attention](../../../../experiments/EXP_3101_SELF_ATTENTION.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**


---

## Next Steps

- Continue with: **[../3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md](./../3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
