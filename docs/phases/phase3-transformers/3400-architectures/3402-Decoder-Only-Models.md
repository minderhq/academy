---
Document ID: 3402
Title: "3402: Decoder-Only Models (GPT, LLaMA, Mistral)"
Phase: 3
Module: 3400
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'architecture', 'encoder-decoder', 'gpt', 'llama']
---

# 3402: Decoder-Only Models (GPT, LLaMA, Mistral)

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Architecture](#architecture)
- [Model Variants](#model-variants)
- [Positional Embeddings](#positional-embeddings)
- [Training Objectives](#training-objectives)
- [Comparison](#comparison)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Assemble the decoder-only layer stack — pre-RMSNorm → causal self-attention → residual → pre-RMSNorm → SwiGLU FFN → residual — and implement `LLaMABlock`'s 8/3·d hidden-dim rule rounded to `multiple_of=256` with bias-free projections
- Read the GPT-3 scaling table (12 layers/768 d_model Small → 96 layers/12288 d_model 175B) and contrast its learned positional embeddings + GeLU against the RoPE + SwiGLU modern stack
- Implement Mistral 7B's two KV-efficiency mechanisms — Sliding Window Attention over a 4096-token window and Grouped Query Attention with 32 query heads sharing 8 KV heads
- Justify RoPE as the decoder-only default — relative positions, length extrapolation, zero added parameters — across the LLaMA/Mistral/GPT-NeoX/Falcon variants sharing base frequency 10000
- Train with autoregressive cross-entropy — flatten `(batch, seq_len, vocab)` logits, apply `F.cross_entropy` with `ignore_index` for padding — then place models on the comparison table (GPT-2 1024 ctx learned-pos → Mixtral 8x7B 32k ctx MoE)

---

## Abstract
Decoder-only models use autoregressive causally-masked attention for the entire sequence, enabling generative pre-training on unlabeled data.

## Architecture

### Core Components
```text
Input Embedding → [Layer 0] → [Layer 1] → ... → [Layer N] → LM Head
                    ↓           ↓               ↓
                 Same block structure repeated

Each Layer:
  1. Layer Normalization (RMSNorm for LLaMA)
  2. Causal Self-Attention
  3. Layer Normalization (RMSNorm for LLaMA)
  4. SwiGLU Feed-Forward
  5. Residual Connections
```

### Llama 2 Architecture
```python
import torch.nn as nn
import torch
class LLaMABlock(nn.Module):
    """
    Llama 2 transformer block
    """
    def __init__(self, dim=4096, n_heads=32, multiple_of=256):
        super().__init__()

        # RMSNorm (pre-normalization)
        self.norm1 = RMSNorm(dim)
        self.norm2 = RMSNorm(dim)

        # Causal self-attention
        self.attn = CausalSelfAttention(dim, n_heads)

        # SwiGLU FFN
        hidden_dim = 4 * dim  # 16384 for 4096
        hidden_dim = int(2 * hidden_dim / 3)
        hidden_dim = multiple_of * ((hidden_dim + multiple_of - 1) // multiple_of)

        self.gate_proj = nn.Linear(dim, hidden_dim, bias=False)
        self.up_proj = nn.Linear(dim, hidden_dim, bias=False)
        self.down_proj = nn.Linear(hidden_dim, dim, bias=False)

    def forward(self, x):
        # Pre-norm
        h = x + self.attn(self.norm1(x))
        h = h + self.down_proj(
            torch.nn.functional.silu(self.gate_proj(h)) * self.up_proj(h)
        )
        return h
```

## Model Variants

### GPT-3 Architecture
```python
# GPT-3 specifications
gpt3_configs = {
    "GPT-3 Small":  {"layers": 12, "heads": 12, "d_model": 768},
    "GPT-3 Medium": {"layers": 24, "heads": 16, "d_model": 1024},
    "GPT-3 Large":  {"layers": 24, "heads": 24, "d_model": 1536},
    "GPT-3 XL":     {"layers": 24, "heads": 32, "d_model": 2048},
    "GPT-3 175B":   {"layers": 96, "heads": 96, "d_model": 12288},
}

# GPT-3 features:
# - Learned positional embeddings (not RoPE)
# - Attention with learnable embeddings (ALiBi in later versions)
# - Pre-norm (v2 only)
# - GeLU activation (not SwiGLU)
```

### Mistral 7B Architecture
```python
import torch.nn as nn
class MistralBlock(nn.Module):
    """
    Mistral 7B: Sliding Window Attention + GQA

    Key features:
    - Sliding Window Attention (SWA): 4096 window
    - Grouped Query Attention (GQA): 4 queries share key/value
    - RoPE positional embeddings
    """
    def __init__(self, dim=4096, n_heads=32, n_kv_heads=8, window=4096):
        super().__init__()

        # RMSNorm (pre-normalization)
        self.norm1 = RMSNorm(dim)
        self.norm2 = RMSNorm(dim)

        # Grouped Query Attention
        self.n_heads = n_heads        # 32 query heads
        self.n_kv_heads = n_kv_heads  # 8 key/value heads

        # Sliding window attention
        self.attn = SlidingWindowAttention(
            dim, n_heads, n_kv_heads, window
        )

        # SwiGLU FFN (8x expansion for Mistral)
        self.ff = SwiGLUFFN(dim, dim * 8)

    def forward(self, x):
        # Mistral uses pre-norm
        h = x + self.attn(self.norm1(x))
        h = h + self.ff(self.norm2(h))
        return h
```

## Positional Embeddings

### RoPE in Decoder-Only Models
```python
# All modern decoder-only models use RoPE

rope_variants = {
    "LLaMA": {
        "base_freq": 10000,
        "type": "original"
    },
    "Mistral": {
        "base_freq": 10000,
        "type": "original"
    },
    "GPT-NeoX": {
        "base_freq": 10000,
        "type": "rotary"
    },
    "Falcon": {
        "base_freq": 10000,
        "type": "original"
    }
}

# Why RoPE?
# - Relative position encoding
# - Can extrapolate to longer sequences
# - No position embedding parameters
```

## Training Objectives

### Autoregressive Language Modeling
```python
import torch.nn.functional as F
def autoregressive_loss(logits, targets):
    """
    Standard cross-entropy loss

    logits: (batch, seq_len, vocab_size)
    targets: (batch, seq_len)
    """
    batch, seq_len, vocab = logits.shape

    # Flatten
    logits_flat = logits.view(-1, vocab)
    targets_flat = targets.view(-1)

    # Cross-entropy
    loss = F.cross_entropy(logits_flat, targets_flat, ignore_index=-1)

    return loss
```

## Comparison

| Model | Layers | Heads | d_model | Context | Features |
|-------|--------|-------|---------|---------|----------|
| GPT-2 | 12/24/36 | 12/16/20 | 768/1024/1280 | 1024 | Learned pos |
| LLaMA 7B | 32 | 32 | 4096 | 2048 | RoPE, SwiGLU |
| Llama-2-7B | 32 | 32 | 4096 | 4096 | RoPE, SwiGLU, GQA |
| Mistral-7B | 32 | 32 | 4096 | 8192 | RoPE, SwiGLU, GQA, SWA |
| Mixtral 8x7B | 32 | 32 | 4096 | 32768 | MoE, RoPE, SWA |

---

## Summary

Decoder-only models generate the entire sequence autoregressively through causally-masked attention, which is what makes generative pre-training on raw unlabeled text possible at scale. This lesson walked the GPT/LLaMA anatomy - embedding, repeated blocks of RMSNorm, causal self-attention and FFN, and the LM head - plus KV-cache inference and why pre-training plus instruction tuning became the dominant recipe. The rule it leaves: scale loves simplicity - one stack, one objective, and the whole modern LLM wave follows from that choice.

## References

### Related PROJECT-OMEGA Documents

- [3401: Encoder-Decoder Architectures](3401-Encoder-Decoder-Architectures.md)

---

## Next Steps

- Next Module: **[3500: Multimodal](../3500-multimodal/)**
- Continue with: **[3501: Vision-Language Models](../3500-multimodal/3501-Vision-Language-Models.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [3401: Encoder-Decoder](./3401-Encoder-Decoder-Architectures.md)
- [3101: Self-Attention](../3100-attention/3101-Self-Attention-DeepDive.md)
- [3201: RoPE](../3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)
