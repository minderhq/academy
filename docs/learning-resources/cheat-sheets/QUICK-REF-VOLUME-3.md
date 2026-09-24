# Volume 3: LLM Internals - Quick Reference

**Transformer Architecture Deep Dive** - Attention, embeddings, and architectures

---

## 📐 Self-Attention

### Standard Attention
```python
def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q, K, V: (batch, heads, seq_len, d_k)
    mask: (batch, 1, 1, seq_len) or (batch, 1, seq_len, seq_len)
    """
    d_k = Q.size(-1)

    # 1. Compute scores
    scores = torch.matmul(Q, K.transpose(-2, -1)) / torch.sqrt(torch.tensor(d_k, dtype=torch.float32))

    # 2. Apply mask (optional)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)

    # 3. Softmax
    attention_weights = F.softmax(scores, dim=-1)

    # 4. Apply to values
    output = torch.matmul(attention_weights, V)

    return output, attention_weights

# Shapes:
# Q: (batch, num_heads, seq_len, d_k)
# K^T: (batch, num_heads, d_k, seq_len)
# scores: (batch, num_heads, seq_len, seq_len)
# V: (batch, num_heads, seq_len, d_k)
# output: (batch, num_heads, seq_len, d_k)
```

### Multi-Head Attention
```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        # Linear projections and reshape
        Q = self.W_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        # Attention
        attn_output, _ = scaled_dot_product_attention(Q, K, V, mask)

        # Concatenate heads
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)

        # Final linear
        output = self.W_o(attn_output)

        return output

# Shapes:
# query, key, value: (batch, seq_len, d_model)
# Q, K, V: (batch, num_heads, seq_len, d_k)
# output: (batch, seq_len, d_model)
```

---

## ⚡ Flash Attention

### Key Idea: Block-wise Computation
```python
# Standard attention: O(n²) memory
# Flash attention: O(n) memory

# Standard:
# 1. Compute full attention matrix (seq_len, seq_len)
# 2. Softmax over entire matrix
# 3. Multiply by values
# Memory: O(seq_len²)

# Flash attention:
# 1. Process in blocks
# 2. Online softmax computation
# 3. Incremental output computation
# Memory: O(block_size * seq_len)

class FlashAttention(nn.Module):
    def __init__(self, d_model, num_heads, block_size=256):
        super().__init__()
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.block_size = block_size

    def forward(self, q, k, v):
        """
        q, k, v: (batch, heads, seq_len, d_k)
        """
        batch_size, num_heads, seq_len, d_k = q.shape

        # Initialize
        output = torch.zeros_like(q)
        l = torch.zeros(batch_size, num_heads, seq_len, device=q.device)
        m = torch.full((batch_size, num_heads, seq_len), -float('inf'), device=q.device)

        # Process in blocks
        for start_j in range(0, seq_len, self.block_size):
            end_j = min(start_j + self.block_size, seq_len)

            # Get block
            k_block = k[:, :, start_j:end_j, :]
            v_block = v[:, :, start_j:end_j, :]

            # Compute QK^T for this block
            qk = torch.einsum('bhsd,bhtd->bhst', q, k_block)

            # Online softmax
            m_new = torch.maximum(m, torch.max(qk, dim=-1)[0])
            alpha = torch.exp(m - m_new)
            beta = torch.exp(qk - m_new.unsqueeze(-1))

            # Update output
            l_new = alpha * l + torch.sum(beta, dim=-1)
            output = alpha.unsqueeze(-1) * output + torch.einsum('bhst,bhtd->bhsd', beta, v_block)

            # Update statistics
            l = l_new
            m = m_new

        output = output / l.unsqueeze(-1)
        return output
```

---

## 🔄 RoPE (Rotary Positional Embeddings)

### Position Encoding
```python
def apply_rotary_emb(x, cos, sin):
    """
    Apply rotary embeddings to query and key

    x: (batch, heads, seq_len, d_k)
    cos, sin: (seq_len, d_k//2)
    """
    # Split into even and odd dimensions
    x1, x2 = x.chunk(2, dim=-1)

    # Apply rotation
    # [x1; x2] -> [x1*cos - x2*sin; x1*sin + x2*cos]
    rotary_x = torch.cat([
        x1 * cos - x2 * sin,
        x1 * sin + x2 * cos
    ], dim=-1)

    return rotary_x

def precompute_freqs_cis(dim, max_seq_len, theta=10000.0):
    """
    Precompute cosine and sine for rotary embeddings

    dim: Head dimension (must be even)
    max_seq_len: Maximum sequence length
    theta: Base frequency
    """
    # Compute frequencies
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2)[: (dim // 2)].float() / dim))

    # Compute positions
    t = torch.arange(max_seq_len, device=freqs.device)

    # Outer product
    freqs = torch.outer(t, freqs)

    # Compute cos and sin
    freqs_cis = torch.polar(torch.ones_like(freqs), freqs)

    return freqs_cis

# Usage in attention
class RotaryAttention(nn.Module):
    def __init__(self, d_model, num_heads, max_seq_len=4096):
        super().__init__()
        self.d_k = d_model // num_heads

        # Precompute frequencies
        freqs_cis = precompute_freqs_cis(self.d_k, max_seq_len)
        self.register_buffer('freqs_cis', freqs_cis)

    def forward(self, q, k, v):
        seq_len = q.size(2)

        # Apply rotary to Q and K only (not V)
        cos = self.freqs_cis[:seq_len].real
        sin = self.freqs_cis[:seq_len].imag

        q_rotary = apply_rotary_emb(q, cos, sin)
        k_rotary = apply_rotary_emb(k, cos, sin)

        # Compute attention with rotated Q and K
        # ... standard attention ...
```

---

## 🧩 Normalization Layers

### Layer Normalization
```python
class LayerNorm(nn.Module):
    """Layer Normalization"""

    def __init__(self, d_model, eps=1e-6):
        super().__init__()
        self.gamma = nn.Parameter(torch.ones(d_model))
        self.beta = nn.Parameter(torch.zeros(d_model))
        self.eps = eps

    def forward(self, x):
        # x: (batch, seq_len, d_model)
        mean = x.mean(-1, keepdim=True)  # (batch, seq_len, 1)
        std = x.std(-1, keepdim=True)    # (batch, seq_len, 1)

        # Normalize
        x_norm = (x - mean) / (std + self.eps)

        # Scale and shift
        return self.gamma * x_norm + self.beta

# Used in: Transformers, BERT, GPT
# Normalizes over feature dimension (d_model)
# Stable during training
```

### RMS Normalization
```python
class RMSNorm(nn.Module):
    """Root Mean Square Normalization"""

    def __init__(self, d_model, eps=1e-8):
        super().__init__()
        self.gamma = nn.Parameter(torch.ones(d_model))
        self.eps = eps

    def forward(self, x):
        # x: (batch, seq_len, d_model)
        # RMS = sqrt(mean(x^2))
        rms = torch.sqrt(torch.mean(x.square(), dim=-1, keepdim=True) + self.eps)

        # Normalize and scale
        return self.gamma * (x / rms)

# Used in: LLaMA, Mistral, Gemma
# Simpler than LayerNorm (no beta parameter)
# More stable for large models
```

### Group Normalization
```python
class GroupNorm(nn.Module):
    """Group Normalization"""

    def __init__(self, num_groups, num_channels, eps=1e-5):
        super().__init__()
        self.num_groups = num_groups
        self.gamma = nn.Parameter(torch.ones(num_channels))
        self.beta = nn.Parameter(torch.zeros(num_channels))
        self.eps = eps

    def forward(self, x):
        # x: (batch, channels, ...)
        N, C, *other = x.shape

        # Reshape for group computation
        x = x.view(N, self.num_groups, C // self.num_groups, *other)

        # Compute mean and std over spatial dimensions and channels per group
        mean = x.mean(dim=[2, *range(3, len(other)+1)], keepdim=True)
        std = x.std(dim=[2, *range(3, len(other)+1)], keepdim=True)

        # Normalize
        x = (x - mean) / (std + self.eps)

        # Reshape back and apply gamma/beta
        x = x.view(N, C, *other)
        return self.gamma.view(1, C, *[1]*len(other)) * x + \
               self.beta.view(1, C, *[1]*len(other))

# Used in: Vision models (ViT, SAM)
# Independent of batch size (unlike BatchNorm)
# More flexible than LayerNorm
```

---

## 🔥 Activation Functions

### GELU (Gaussian Error Linear Unit)
```python
def gelu(x):
    """GELU activation"""
    # Exact: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
    return 0.5 * x * (1.0 + torch.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * torch.pow(x, 3))))

# Approximation (faster)
def gelu_approx(x):
    return x * torch.sigmoid(1.702 * x)

# Used in: BERT, GPT-2, GPT-3
# Smoother than ReLU
# Better gradients
```

### SwiGLU
```python
class SwiGLU(nn.Module):
    """SwiGLU activation (used in LLaMA)"""

    def __init__(self, d_model):
        super().__init__()
        # Split into three parts
        self.W_gate = nn.Linear(d_model, d_model * 2, bias=False)
        self.W_up = nn.Linear(d_model, d_model * 2, bias=False)
        self.W_down = nn.Linear(d_model * 2, d_model, bias=False)

    def forward(self, x):
        # SwiGLU(x) = (Swish(W_gate * x) ⊙ W_up(x)) @ W_down
        # Swish(x) = x * sigmoid(x)
        gate = torch.sigmoid(self.W_gate(x))
        up = self.W_up(x)

        # Element-wise multiplication
        activated = gate * up

        # Down projection
        return self.W_down(activated)

# Used in: LLaMA, Mistral
# Better than ReLU or GELU
# More parameters (3x projection size)
```

### GeGLU
```python
class GeGLU(nn.Module):
    """GeGLU activation"""

    def __init__(self, d_model):
        super().__init__()
        # Split into two parts
        self.W_gate = nn.Linear(d_model, d_model * 2, bias=False)
        self.W_up = nn.Linear(d_model, d_model * 2, bias=False)

    def forward(self, x):
        # GeGLU(x) = GELU(W_gate * x) ⊙ W_up(x)
        gate = gelu(self.W_gate(x))
        up = self.W_up(x)

        return gate * up

# Used in: PaLM, UL2
# Similar to SwiGLU but with GELU instead of Swish
```

---

## 🏗️ Model Architectures

### Decoder-Only Block (GPT-style)
```python
class DecoderBlock(nn.Module):
    """Transformer decoder block"""

    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()

        # Self-attention with causal mask
        self.self_attn = MultiHeadAttention(d_model, num_heads)
        self.norm1 = RMSNorm(d_model)

        # Feed-forward network
        self.ffn = SwiGLU(d_model)
        self.norm2 = RMSNorm(d_model)

        self.dropout = dropout

    def forward(self, x, mask=None):
        # x: (batch, seq_len, d_model)

        # Self-attention with residual
        attn_out = self.self_attn(x, x, x, mask)
        x = x + self.dropout(attn_out)
        x = self.norm1(x)

        # Feed-forward with residual
        ffn_out = self.ffn(x)
        x = x + self.dropout(ffn_out)
        x = self.norm2(x)

        return x

# Architecture:
# Input -> Attn -> Add & Norm -> FFN -> Add & Norm -> Output
```

### Encoder-Decoder (T5-style)
```python
class EncoderDecoderBlock(nn.Module):
    """Transformer encoder-decoder block"""

    def __init__(self, d_model, num_heads, d_ff):
        super().__init__()

        # Encoder self-attention
        self.encoder_attn = MultiHeadAttention(d_model, num_heads)
        self.norm1 = LayerNorm(d_model)

        # Cross-attention
        self.cross_attn = MultiHeadAttention(d_model, num_heads)
        self.norm2 = LayerNorm(d_model)

        # Feed-forward
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Linear(d_ff, d_model),
        )
        self.norm3 = LayerNorm(d_model)

    def forward(self, x, encoder_output, encoder_mask=None, decoder_mask=None):
        # Encoder self-attention
        attn_out = self.encoder_attn(x, x, x, encoder_mask)
        x = x + attn_out
        x = self.norm1(x)

        # Cross-attention (query from decoder, key/value from encoder)
        cross_out = self.cross_attn(x, encoder_output, encoder_output, decoder_mask)
        x = x + cross_out
        x = self.norm2(x)

        # Feed-forward
        ffn_out = self.ffn(x)
        x = x + ffn_out
        x = self.norm3(x)

        return x

# Architecture:
# Encoder: Input -> Attn -> Add & Norm -> FFN -> Add & Norm
# Decoder: Input -> EncAttn -> Add & Norm -> CrossAttn -> Add & Norm -> FFN -> Add & Norm
```

### Mixture of Experts (MoE)
```python
class MoEBlock(nn.Module):
    """Mixture of Experts block"""

    def __init__(self, d_model, num_experts, top_k=2):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k

        # Router (gating network)
        self.router = nn.Linear(d_model, num_experts, bias=False)

        # Experts (feed-forward networks)
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(d_model, d_model * 4),
                nn.GELU(),
                nn.Linear(d_model * 4, d_model),
            )
            for _ in range(num_experts)
        ])

    def forward(self, x):
        # x: (batch, seq_len, d_model)

        # Compute router logits
        router_logits = self.router(x)  # (batch, seq_len, num_experts)

        # Select top-k experts
        top_k_weights, top_k_indices = torch.topk(
            F.softmax(router_logits, dim=-1),
            self.top_k,
            dim=-1
        )

        # Normalize weights
        top_k_weights = top_k_weights / top_k_weights.sum(dim=-1, keepdim=True)

        # Apply experts
        output = torch.zeros_like(x)
        for i in range(self.num_experts):
            # Find tokens routed to this expert
            expert_mask = (top_k_indices == i).any(dim=-1)

            if expert_mask.any():
                expert_input = x[expert_mask]
                expert_output = self.experts[i](expert_input)

                # Weight and add
                for k in range(self.top_k):
                    mask = (top_k_indices[:, :, k] == i)
                    weight = top_k_weights[:, :, k].unsqueeze(-1)
                    output = output + mask.unsqueeze(-1) * weight * expert_output

        return output

# Used in: Mixtral, Switch Transformer
# Sparse activation: Only top-k experts used per token
# Scales model capacity without increasing compute proportionally
```

---

## 🔑 Tokenization

### BPE (Byte Pair Encoding)
```python
# BPE merge rules
# Example merges:
# ("e", "r") -> "er" (most common pair)
# ("er", "t") -> "ert"
# ("ert", "h") -> "erth"
# ...

# Encoding
def encode_bpe(text, vocab, merges):
    """Encode text using BPE"""
    # Start with characters
    words = text.split()
    tokens = [list(word) for word in words]

    # Apply merges greedily
    for merge in merges:
        for i, token_list in enumerate(tokens):
            j = 0
            while j < len(token_list) - 1:
                pair = (token_list[j], token_list[j+1])
                if pair == merge:
                    # Merge pair
                    merged = token_list[j] + token_list[j+1]
                    token_list[j:j+2] = [merged]
                else:
                    j += 1

    # Convert to IDs
    token_ids = [[vocab[token] for token in tokens_] for tokens_ in tokens]
    return token_ids

# Used in: GPT-2, GPT-3, LLaMA
# Subword tokenization
# Balances vocabulary size and sequence length
```

### Unigram Language Model
```python
# Unigram LM (SentencePiece)
# Each subword has probability
# Encoding: Find segmentation with highest probability

# Vocab size: ~32k (typical)
# Uses SentencePiece library

import sentencepiece as spm

# Train unigram tokenizer
spm.SentencePieceTrainer.train(
    input='corpus.txt',
    model_prefix='tokenizer',
    vocab_size=32000,
    model_type='unigram',
)

# Load tokenizer
sp = spm.SentencePieceProcessor(model_file='tokenizer.model')

# Encode
token_ids = sp.encode('Hello world', out_type=int)
# Output: [1234, 5678]

# Decode
text = sp.decode(token_ids)
# Output: "Hello world"

# Used in: T5, mT5, UL2
# Works well for multilingual
```

---

## 🎯 Volume 3 Checklist

- [ ] Understand self-attention mechanism
- [ ] Implement multi-head attention
- [ ] Understand Flash Attention
- [ ] Use RoPE for position encoding
- [ ] Compare normalization layers
- [ ] Know different activation functions
- [ ] Build decoder-only block
- [ ] Build encoder-decoder block
- [ ] Understand MoE architecture
- [ ] Tokenize text with BPE

---

## 🚀 Next Steps

1. Complete LAB-002: RAG Implementation
2. Read 3102-Flash-Attention.md
3. Read 3202-Tokenizer-Sciences.md
4. Practice implementing attention

---

**Last Updated:** 2026-02-04
**Volume:** 3 - LLM Internals
**Estimated Time:** 35-40 hours
