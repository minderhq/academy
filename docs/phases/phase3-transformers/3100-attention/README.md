---
Document ID: 3100-ATTENTION-README
Title: "[3100]: Attention Architectures"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Beginner
---

# [3100]: Attention Architectures

## Overview

This module covers the attention mechanism - the core innovation behind Transformers. You'll learn how self-attention enables models to weigh the importance of different tokens in a sequence, allowing for parallel processing and long-range dependencies.

---

## Module Documents

| Document | Description | Difficulty | Time |
|----------|-------------|------------|------|
| [3101: Self-Attention Deep Dive](./3101-Self-Attention-DeepDive.md) | Multi-head, Masked, Scaled Dot-Product Attention | ⭐⭐⭐ | 4 hrs |
| [3102: Flash Attention](./3102-Flash-Attention.md) | Memory-efficient attention calculation (IO-aware) | ⭐⭐⭐⭐ | 3 hrs |

---

## Learning Objectives

After completing this module, you will:
- ✅ Understand the mathematical foundation of scaled dot-product attention
- ✅ Implement multi-head attention from scratch
- ✅ Explain causal vs bidirectional attention
- ✅ Optimize attention with Flash Attention for memory efficiency
- ✅ Apply attention mechanisms to real-world NLP tasks

---

## Prerequisites

- **Math:** Matrix multiplication, softmax function
- **Programming:** Python, PyTorch tensors
- **Previous:** Phase 2 completion (tensor algebra, neural network fundamentals)

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

---

## Key Concepts

### Scaled Dot-Product Attention

```text
Attention(Q, K, V) = softmax(QK^T / √d_k) × V
```

- **Q (Query):** What this token is looking for
- **K (Key):** What other tokens offer
- **V (Value):** The actual content of tokens
- **d_k:** Dimension of keys (scaling factor prevents softmax saturation)

### Multi-Head Attention

```text
Single head: Each token attends to all tokens with one pattern
Multiple heads: Each token attends with multiple patterns simultaneously
```

**Why multiple heads?**
- Head 1: Subject-verb agreement ("cat" ↔ "sat")
- Head 2: Noun phrase structure ("The" ↔ "cat")
- Head 3: Preposition relationships ("sat" ↔ "on")

### Causal vs Bidirectional

| Type | Description | Use Case |
|------|-------------|----------|
| **Causal** | Token can only attend to previous tokens | Text generation (GPT) |
| **Bidirectional** | Token can attend to all tokens | Understanding (BERT) |

---

## Related Experiments

| Experiment | Description |
|------------|-------------|
| [EXP_3101: Self-Attention](../../../../experiments/EXP_3101_SELF_ATTENTION.md) | Implement attention from scratch |
| [EXP_3102: Flash Attention](../../../../experiments/EXP_3102_FLASH_ATTENTION.md) | Benchmark attention mechanisms |

---

## Implementation Example

```python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Scaled dot-product attention implementation.

    Args:
        Q, K, V: (batch, num_heads, seq_len, d_k)
        mask: (batch, 1, 1, seq_len) or (batch, 1, seq_len, seq_len)

    Returns:
        output: (batch, num_heads, seq_len, d_k)
        attn_weights: (batch, num_heads, seq_len, seq_len)
    """
    d_k = Q.size(-1)

    # 1. Compute scores (similarity between queries and keys)
    scores = torch.matmul(Q, K.transpose(-2, -1))

    # 2. Scale by √d_k
    scores = scores / (d_k ** 0.5)

    # 3. Apply mask (optional)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)

    # 4. Softmax to get attention weights
    attn_weights = F.softmax(scores, dim=-1)

    # 5. Weight values by attention weights
    output = torch.matmul(attn_weights, V)

    return output, attn_weights
```

---

## Assessment

- **Quiz:** [assessment/QUIZ.md](assessment/QUIZ.md) - Test your attention knowledge
- **Practice:** [assessment/PRACTICE.md](assessment/PRACTICE.md) - Hands-on attention exercises

---

## See Also

- **Next Module:** [3200: Embedding Latent Spaces](../3200-embeddings/)
- **Related:** [3300: The Decoding Block](../3300-decoding/) - How attention is used in Transformers
- **Phase Overview:** [Phase 3 README](../README.md)

---

## Common Issues

| Issue | Solution |
|-------|----------|
| **OOM with long sequences** | Use Flash Attention or reduce sequence length |
| **Slow attention computation** | Implement Flash Attention or use Triton kernels |
| **NaN gradients** | Check for numerical instability in softmax scaling |

---

## Quick Reference

### Attention Variants

| Variant | Formula | Use Case |
|---------|---------|----------|
| **Scaled Dot-Product** | `softmax(QK^T/√d_k)V` | Standard Transformer |
| **Multi-Head** | Parallel attention heads | Capture multiple patterns |
| **Flash Attention** | IO-aware tiling | Long sequences, memory limited |
| **Cross-Attention** | Different Q vs K,V sources | Encoder-Decoder models |
| **Sparse Attention** | Limited attention window | Efficient long sequences |

---

**Module Difficulty:** ⭐⭐⭐ Intermediate
**Estimated Time:** 7 hours total
