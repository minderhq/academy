---
Document ID: 3201
Title: Rotary Positional Embeddings (RoPE)
Phase: 3
Module: 3200
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'embeddings', 'rope', 'tokenization', 'bpe']
---

# 3201: Rotary Positional Embeddings (RoPE)

## Abstract
RoPE (Rotary Positional Embeddings) is a position encoding method that injects position information into the attention mechanism through rotation. It's the dominant approach in modern LLMs (LLaMA, Mistral, etc.).

## The Problem with Positional Encodings

### Why We Need Position Information
```text
Transformers are permutation invariant:
Attention("cat chases dog") = Attention("dog chases cat")

Without position info, the model can't distinguish:
- Subject vs object
- Word order in sentences
- Sequential relationships
```

### Traditional Approaches

#### Absolute Positional Encoding (Original Transformer)
```python
def absolute_positional_encoding(seq_len, d_model):
    """
    Sinusoidal positional encoding from "Attention Is All You Need"
    """
    position = torch.arange(seq_len).unsqueeze(1)  # (L, 1)
    div_term = torch.exp(torch.arange(0, d_model, 2) * -(math.log(10000.0) / d_model))

    pe = torch.zeros(seq_len, d_model)
    pe[:, 0::2] = torch.sin(position * div_term)
    pe[:, 1::2] = torch.cos(position * div_term)

    return pe  # (L, d_model)

# Add to token embeddings
x = token_embeddings + positional_encoding

# Problem: Not generalizable to longer sequences
# Problem: Absolute positions (doesn't capture relative)
```

#### Relative Position Encoding (T5, ALiBi)
```python
# Relative position bias added to attention scores
def relative_position_bias(seq_len):
    """
    Learn relative position bias
    """
    # Learnable bias for each relative position
    # Attention[i,j] += learnable_bias[j-i]
    pass

# Problem: Requires O(L²) parameters
# Problem: More complex to implement
```

## RoPE: Rotary Positional Embeddings

### Core Intuition
```text
Instead of adding position to embeddings,
rotate the query and key vectors by their position!

Analogous to: Rotating a vector in 2D space
[x, y] rotated by θ becomes:
  [x·cos(θ) - y·sin(θ), x·sin(θ) + y·cos(θ)]
```

### Mathematical Formulation

#### 2D Rotation
```text
Given vector v = [x, y] and angle θ:
Rotated vector v' = R(θ) × v

Where R(θ) = [cos(θ)  -sin(θ)]
             [sin(θ)   cos(θ)]

So:
v' = [x·cos(θ) - y·sin(θ), x·sin(θ) + y·cos(θ)]
```

#### High-Dimensional Rotation
```text
For d-dimensional vector, rotate in 2D subspaces:
  (x₀, x₁) rotated by m·θ₀
  (x₂, x₃) rotated by m·θ₁
  (x₄, x₅) rotated by m·θ₂
  ...

Where m is the position index
```

### RoPE Implementation
```python
import torch
import math

def rotate_half(x):
    """
    Rotates half the hidden dims of the input
    x: (batch, heads, seq_len, head_dim)
    """
    x1 = x[..., :x.size(-1)//2]
    x2 = x[..., x.size(-1)//2:]

    # Rotate: [x1, x2] → [x1·cos - x2·sin, x1·sin + x2·cos]
    return torch.cat([
        -x2, x1
    ], dim=-1)

def apply_rotary_pos_emb(q, k, cos, sin):
    """
    Apply rotary positional embedding to query and key
    q, k: (batch, heads, seq_len, head_dim)
    cos, sin: (seq_len, head_dim)
    """
    # Reshape cos, sin for broadcasting
    cos = cos.unsqueeze(0).unsqueeze(0)  # (1, 1, seq_len, head_dim)
    sin = sin.unsqueeze(0).unsqueeze(0)

    # Apply rotation using complex multiplication trick
    # q_rotated = q * cos + rotate_half(q) * sin
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)

    return q_embed, k_embed
```

### Precompute Rotary Frequencies
```python
def precompute_freqs_cis(dim, max_seq_len, theta=10000.0):
    """
    Precompute frequency tensor for rotary embeddings
    dim: head dimension (must be even)
    max_seq_len: maximum sequence length
    theta: base frequency (default 10000)
    """
    # Compute frequencies
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2)[:(dim//2)] / dim))
    t = torch.arange(max_seq_len)

    # Outer product: freqs × positions
    freqs = torch.outer(t, freqs)  # (max_seq_len, dim//2)

    # Convert to complex exponential (cis = cos + i·sin)
    freqs_cis = torch.polar(torch.ones_like(freqs), freqs)
    return freqs_cis

# Or as cos/sin
def precompute_cos_sin(dim, max_seq_len, theta=10000.0):
    """
    Precompute cos and sin separately
    """
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2)[:(dim//2)] / dim))
    t = torch.arange(max_seq_len)
    freqs = torch.outer(t, freqs)

    # Compute cos and sin
    emb = torch.cat([freqs, freqs], dim=-1)
    cos = emb.cos()
    sin = emb.sin()

    return cos, sin  # (max_seq_len, dim)

# Usage
head_dim = 64
max_seq_len = 4096
cos, sin = precompute_cos_sin(head_dim, max_seq_len)

# During forward pass
cos_cached = cos[:seq_len]
sin_cached = sin[:seq_len]
q_rot, k_rot = apply_rotary_pos_emb(q, k, cos_cached, sin_cached)
```

## Why RoPE Works

### Relative Position Awareness
```text
RoPE makes attention score depend on RELATIVE position:

Attention(Q_m, K_n) depends on (m - n), not m and n separately!

Proof sketch:
  Q_m rotated by m: Q_m × R(mθ)
  K_n rotated by n: K_n × R(nθ)
  Dot product: Q_m · K_n becomes f(Q_m, K_n, m-n)

This means:
- Same relative position → same attention score
- Generalizes to longer sequences
- No extra parameters needed
```

### Visualization
```python
import matplotlib.pyplot as plt

def visualize_rope_rotation(dim=64, seq_len=100):
    """
    Visualize how vectors rotate with position
    """
    # Sample 2D rotation (first two dimensions)
    positions = torch.arange(seq_len)
    angle = positions / 10000.0

    # Create a base vector [1, 0]
    x = torch.cos(angle)
    y = torch.sin(angle)

    plt.figure(figsize=(10, 10))
    plt.plot(x, y, 'o-', markersize=3)
    plt.title('RoPE: Vector Rotation with Position')
    plt.xlabel('Dimension 0')
    plt.ylabel('Dimension 1')
    plt.grid(True)
    plt.axis('equal')
    plt.show()

visualize_rope_rotation()
```

## RoPE Variants

### LLaMA-style RoPE
```python
class LlamaRotaryEmbedding(nn.Module):
    def __init__(self, dim, max_position_embeddings=2048, base=10000):
        super().__init__()
        # LLaMA uses a different base frequency scaling
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)

        # Build cache
        self.max_seq_len_cached = max_position_embeddings
        t = torch.arange(self.max_seq_len_cached).type_as(inv_freq)
        freqs = torch.outer(t, inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer('cos_cached', emb.cos()[None, None, :, :])
        self.register_buffer('sin_cached', emb.sin()[None, None, :, :])

    def forward(self, q, k):
        # Apply cached cos/sin
        return apply_rotary_pos_emb(
            q, k,
            self.cos_cached[:, :, :q.size(2), :],
            self.sin_cached[:, :, :q.size(2), :]
        )
```

### Scaled RoPE (for longer contexts)
```python
def scaled_rope(dim, max_seq_len, scale_factor=8.0):
    """
    Extend RoPE to longer sequences by scaling
    Used in LLaMA-2-Long, CodeLlama
    """
    # Scale down frequencies for longer context
    # Effective: same pattern but stretched over more tokens
    base = 10000
    inv_freq = 1.0 / (scale_factor * (base ** (torch.arange(0, dim, 2).float() / dim)))
    # ... same as standard RoPE
```

### YaRN (Yet another RoPE extensioN)
```python
def yarn_scaling(dim, max_seq_len, original_max_seq_len=2048):
    """
    YaRN: Better interpolation for extended context
    Uses NTK-aware scaling
    """
    # Compute scale factor
    scale = (max_seq_len / original_max_seq_len) ** (dim / (dim - 2))

    # Modified base frequency
    base = 10000 * scale
    inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
    # ... same as standard RoPE
```

## RoPE in Practice

### Integration into Attention
```python
class RoPEMultiHeadAttention(nn.Module):
    def __init__(self, d_model=512, num_heads=8, max_seq_len=2048):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)

        # Precompute RoPE frequencies
        self.cos, self.sin = precompute_cos_sin(
            self.d_k, max_seq_len
        )

    def forward(self, x):
        batch_size, seq_len, _ = x.shape

        # Project to Q, K, V
        Q = self.W_q(x).view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(x).view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(x).view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)

        # Apply RoPE
        cos = self.cos[:seq_len].unsqueeze(0).unsqueeze(0)
        sin = self.sin[:seq_len].unsqueeze(0).unsqueeze(0)
        Q, K = apply_rotary_pos_emb(Q, K, cos, sin)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.d_k ** 0.5)
        attn = F.softmax(scores, dim=-1)
        output = torch.matmul(attn, V)

        return output
```

## Extended Context with RoPE

### Position Interpolation
```python
def extend_context_via_interpolation(original_max_len=2048, new_max_len=8192):
    """
    Extend context window by interpolating RoPE positions
    """
    # Instead of using position m directly, use scaled position
    # m' = m * (original_max_len / new_max_len)

    scale = original_max_len / new_max_len

    # Modified precomputation
    def precompute_scaled_freqs(dim, max_seq_len, scale=1.0):
        freqs = 1.0 / (10000.0 ** (torch.arange(0, dim, 2)[:(dim//2)] / dim))
        t = torch.arange(max_seq_len) * scale  # Scale positions!
        freqs = torch.outer(t, freqs)
        return freqs.cos(), freqs.sin()

    return precompute_scaled_freqs(64, new_max_len, scale)
```

## Comparison with Other Methods

| Method | Parameters | O(n) Extend | Relative | Complexity |
|--------|-----------|-------------|----------|------------|
| Absolute Sinusoidal | 0 | ✗ | ✗ | Low |
| Learned Absolute | d_model | ✗ | ✗ | Low |
| Relative Bias | O(L²) | ~ | ✓ | High |
| ALiBi | 0 | ✓ | ✓ | Low |
| RoPE | 0 | ✓ | ✓ | Medium |

---

## Next Steps

- Continue with: **[3202: Tokenizer Sciences](./3202-Tokenizer-Sciences.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [3101: Self-Attention](../3100-attention/3101-Self-Attention-DeepDive.md)
- [3202: Tokenizer Sciences](./3202-Tokenizer-Sciences.md)
- [4201: Context Window](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)

**Experiment Template:** `experiments/EXP_3201_ROPE.md`
