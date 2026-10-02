---
Document ID: 3200-EMBEDDINGS-README
Title: "[3200]: Embedding Latent Spaces"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Tags: ['module', 'transformers', 'embeddings']
---

# [3200]: Embedding Latent Spaces

## Overview

This module covers how Transformers represent text as continuous vectors - the foundation of all modern NLP. You'll learn about positional encoding (RoPE), tokenization algorithms (BPE, SentencePiece), and how these choices affect model performance.

---

## Module Documents

| Document | Description | Difficulty | Time |
|----------|-------------|------------|------|
| [3201: RoPE - Rotary Positional Embeddings](./3201-Rotary-Positional-Embeddings-RoPE.md) | Absolute vs Relative positions in sequence modeling | ⭐⭐ | 3 hrs |
| [3202: Tokenizer Sciences](./3202-Tokenizer-Sciences.md) | BPE, SentencePiece, and Tiktoken algorithms | ⭐⭐ | 3 hrs |

---

## Learning Objectives

After completing this module, you will:
- ✅ Understand the embedding space and token representations
- ✅ Explain why positional encodings are necessary
- ✅ Compare absolute vs relative position representations
- ✅ Implement RoPE (Rotary Positional Embeddings)
- ✅ Understand tokenization algorithms and their trade-offs
- ✅ Train and use custom tokenizers

---

## Prerequisites

- **Math:** Trigonometry (for RoPE), basic linear algebra
- **Programming:** Python, string manipulation
- **Previous:** [3100: Attention Architectures](../3100-attention/)

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

---

## Key Concepts

### The Embedding Problem

**Challenge:** Transformers process tokens in parallel and have no inherent sense of position or order.

```text
Input: "The cat sat on the mat"
Input: "The mat sat on the cat"

Without positional encoding → Same representation!
```

### Position Encoding Solutions

| Type | Description | Pros | Cons |
|------|-------------|------|------|
| **Absolute (Sinusoidal)** | Fixed sinusoidal patterns | Simple, deterministic | Limited to max length |
| **Learned Absolute** | Learned position vectors | Flexible | Poor extrapolation |
| **Relative (RoPE)** | Rotary position encoding | Better extrapolation | More complex |
| **ALiBi** | Attention with Linear Biases | Simple, efficient | Limited adoption |

### Tokenization Trade-offs

| Algorithm | Description | Vocabulary Size | Pros | Cons |
|-----------|-------------|------------------|------|------|
| **BPE** | Byte-Pair Encoding | 30k-50k | Proven, efficient | Suboptimal merges |
| **WordPiece** | Word-level + subword | 30k | Better coverage | Google-specific |
| **SentencePiece** | Unsupervised text segmentation | 10k-100k | Language-agnostic | Requires training |
| **Unigram** | Unigram language model | 30k | Flexible | Slower training |
| **Tiktoken** | BPE variant (OpenAI) | 100k+ | Optimized for LLMs | Proprietary |

---

## RoPE Intuition

### The Core Idea

Instead of adding position to embeddings, **rotate** the query and key vectors based on their positions:

```text
For position m (query) and n (key):
Rotate q_m by angle m*θ
Rotate k_n by angle n*θ

Dot product naturally incorporates relative distance!
```

### Mathematical Foundation

```python
import torch
def rotate_positions(x, m, theta):
    """
    Rotate vector x by position m with frequency theta

    Args:
        x: Input vector (d_model,)
        m: Position index
        theta: Frequency (precomputed per dimension)

    Returns:
        Rotated vector
    """
    x1, x2 = x.chunk(2)  # Split into pairs
    cos_m, sin_m = torch.cos(m * theta), torch.sin(m * theta)

    return torch.cat([
        x1 * cos_m - x2 * sin_m,
        x1 * sin_m + x2 * cos_m
    ])
```

---

## Tokenization Example

### BPE Merge Rules

```python
# Initial vocabulary (characters)
vocab = {'a', 'b', 'c', ...}

# Training corpus
corpus = ["hug", "pug", "puggle", "bug"]

# BPE algorithm:
# 1. Count all token pairs
# 2. Find most frequent pair
# 3. Merge into new token
# 4. Repeat until vocabulary size reached

# Iteration 1: 'u' + 'g' = 'ug' (frequency 4)
# Iteration 2: 'p' + 'ug' = 'pug' (frequency 2)
# Iteration 3: 'pug' + 'g' = 'pugg' (frequency 1)
# ...
```

### Tokenizer Comparison

```text
Input: "Tokenization is fascinating"

Word-level:
["Tokenization", "is", "fascinating"]  # 3 tokens, large vocab

BPE (30k vocab):
["Token", "ization", " is", " fasc", "inating"]  # 5 tokens

Character-level:
["T", "o", "k", "e", "n", "i", "z", "a", "t", "i", "o", "n", ...]  # Many tokens
```

---

## Related Experiments

| Experiment | Description |
|------------|-------------|
| [EXP_3201: RoPE](../../../../experiments/EXP_3201_ROPE.md) | Implement and benchmark RoPE |
| [EXP_3202: Tokenizer](../../../../experiments/EXP_3202_TOKENIZER.md) | Train custom BPE tokenizer |

---

## Implementation Example

### RoPE Implementation

```python
import torch.nn as nn
import torch
class RotaryPositionalEmbedding(nn.Module):
    def __init__(self, d_model, max_seq_len=8192):
        super().__init__()
        self.d_model = d_model

        # Create frequency tensor
        theta = 1.0 / (10000 ** (torch.arange(0, d_model, 2).float() / d_model))
        self.register_buffer('theta', theta)

    def forward(self, x, seq_len):
        """
        Apply rotary positional encoding

        Args:
            x: (batch, seq_len, d_model)
            seq_len: Current sequence length

        Returns:
            Rotated x: (batch, seq_len, d_model)
        """
        batch_size = x.size(0)

        # Position indices
        m = torch.arange(seq_len, device=x.device).float()

        # Compute rotation angles: (seq_len, d_model/2)
        angles = m[:, None] * self.theta[None, :]

        # Compute cos and sin: (seq_len, d_model/2)
        cos_pos = torch.cos(angles)
        sin_pos = torch.sin(angles)

        # Split x into pairs: (batch, seq_len, d_model/2)
        x1, x2 = x.chunk(2, dim=-1)

        # Apply rotation
        x_rotated = torch.cat([
            x1 * cos_pos - x2 * sin_pos,
            x1 * sin_pos + x2 * cos_pos
        ], dim=-1)

        return x_rotated
```

---

## Assessment

- **Quiz:** [assessment/QUIZ.md](assessment/QUIZ.md) - Test your embedding knowledge
- **Practice:** [assessment/PRACTICE.md](assessment/PRACTICE.md) - Hands-on tokenizer exercises

---

## See Also

- **Previous Module:** [3100: Attention Architectures](../3100-attention/)
- **Next Module:** [3300: The Decoding Block](../3300-decoding/) - Activation functions and normalization
- **Phase Overview:** [Phase 3 README](../README.md)

---

## Common Issues

| Issue | Solution |
|-------|----------|
| **Tokenizer OOM** | Reduce vocab size or use streaming tokenization |
| **Poor RoPE extrapolation** | Adjust theta base frequency or use YaRN |
| **Slow tokenization** | Use Rust-based tokenizers (Hugging Face tokenizers) |

---

## Quick Reference

### Position Encoding Comparison

| Method | Max Length | Extrapolation | Complexity |
|--------|------------|---------------|------------|
| Sinusoidal | Fixed | Poor | Low |
| Learned | Fixed | Poor | Medium |
| RoPE | Theoretical | Good | Medium |
| ALiBi | Unlimited | Excellent | Low |

### Tokenizer Selection Guide

| Use Case | Recommended Tokenizer | Reason |
|----------|----------------------|--------|
| General LLM | BPE (30k-50k) | Balanced efficiency |
| Code Generation | Tiktoken | Optimized for code |
| Multilingual | SentencePiece | Language-agnostic |
| Low-resource | Unigram | Better coverage |

---

**Module Difficulty:** ⭐⭐⭐ Intermediate
**Estimated Time:** 7 hours total
