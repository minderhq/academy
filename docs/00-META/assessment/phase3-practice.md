---
Document ID: PHASE3-PRACTICE
Title: "Phase 3: Transformer Physics Practice"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
---

# Phase 3: Transformer Physics Practice

## Hands-On Exercises

### Exercise 1: Implement Multi-Head Attention

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiHeadAttention(nn.Module):
    """Complete multi-head attention implementation"""

    def __init__(self, d_model, num_heads, dropout=0.1):
        super().__init__()
        assert d_model % num_heads == 0

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)
        self.scale = self.d_k ** -0.5

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        # Linear projections in batch
        Q = self.W_q(query)
        K = self.W_k(key)
        V = self.W_v(value)

        # Reshape for multi-head
        Q = Q.view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = K.view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = V.view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale

        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # Apply attention to values
        context = torch.matmul(attn_weights, V)

        # Concatenate heads
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)

        # Final projection
        output = self.W_o(context)

        return output, attn_weights


def test_attention():
    print("=== Multi-Head Attention Test ===")

    # Test parameters
    batch_size = 4
    seq_len = 16
    d_model = 64
    num_heads = 4

    # Create attention layer
    mha = MultiHeadAttention(d_model, num_heads)

    # Test input
    x = torch.randn(batch_size, seq_len, d_model)
    mask = torch.tril(torch.ones(seq_len, seq_len)).unsqueeze(0).unsqueeze(0)

    # Forward pass
    output, attn = mha(x, x, x, mask)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Attention weights shape: {attn.shape}")

    assert output.shape == x.shape
    assert attn.shape == (batch_size, num_heads, seq_len, seq_len)

    print("✅ Multi-head attention working!\n")


if __name__ == "__main__":
    test_attention()
```

### Exercise 2: Implement RoPE (Rotary Position Embedding)

```python
import torch
import torch.nn as nn
import math

class RotaryPositionEmbedding(nn.Module):
    """Rotary Position Embedding implementation"""

    def __init__(self, d_model, max_seq_len=4096):
        super().__init__()
        self.d_model = d_model

        # Create rotation matrix
        theta = 1.0 / (10000 ** torch.arange(0, d_model, 2).float() / d_model)
        position = torch.arange(max_seq_len).float()
        freqs = torch.outer(position, theta)

        # Complex exponentials
        self.register_buffer('freqs', torch.polar(torch.ones_like(freqs), freqs))

    def forward(self, x):
        """Apply rotary embeddings"""
        batch_size, seq_len, _ = x.shape

        # Split into pairs for rotation
        x_complex = torch.polar(
            torch.zeros_like(x[:, :, :self.d_model//2]),
            x[:, :, :self.d_model//2]
        )

        # Apply rotation
        freqs = self.freqs[:seq_len]
        x_rotated = x_complex * freqs.unsqueeze(0)

        # Convert back to real
        x_real = torch.cat([
            torch.real(x_rotated),
            torch.imag(x_rotated)
        ], dim=-1)

        return x_real


def test_rope():
    print("=== RoPE Test ===")

    d_model = 64
    seq_len = 16

    rope = RotaryPositionEmbedding(d_model)
    x = torch.randn(2, seq_len, d_model)

    output = rope(x)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print("✅ RoPE working!\n")


if __name__ == "__main__":
    test_rope()
```

### Exercise 3: Build BPE Tokenizer

```python
from collections import defaultdict
import json

class BPETokenizer:
    """Byte Pair Encoding tokenizer"""

    def __init__(self, vocab_size=1000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.merges = []

    def train(self, text, num_merges=None):
        """Train BPE tokenizer"""
        if num_merges is None:
            num_merges = self.vocab_size

        # Start with characters
        words = [list(word) + ['</w>'] for word in text.split()]
        vocab = set([char for word in words for char in word])

        # Count pairs
        for i in range(num_merges):
            pairs = defaultdict(int)
            for word in words:
                for j in range(len(word) - 1):
                    pair = (word[j], word[j+1])
                    pairs[pair] += 1

            # Get best pair
            if not pairs:
                break

            best_pair = max(pairs, key=pairs.get)

            # Merge pair
            new_vocab = set()
            new_words = []
            for word in words:
                new_word = []
                j = 0
                while j < len(word):
                    if j < len(word) - 1 and (word[j], word[j+1]) == best_pair:
                        new_word.append(best_pair[0] + best_pair[1])
                        j += 2
                    else:
                        new_word.append(word[j])
                        j += 1
                new_words.append(new_word)
                new_vocab.update(new_word)

            words = new_words
            vocab.update(new_vocab)
            self.merges.append(best_pair)

        self.vocab = {token: i for i, token in enumerate(vocab)}

    def encode(self, text):
        """Encode text to tokens"""
        words = [list(word) + ['</w>'] for word in text.split()]

        tokens = []
        for word in words:
            # Apply merges
            while len(word) > 1:
                # Find best merge
                for pair in self.merges:
                    merged = False
                    for i in range(len(word) - 1):
                        if (word[i], word[i+1]) == pair:
                            word = word[:i] + [pair[0] + pair[1]] + word[i+2:]
                            merged = True
                            break
                    if merged:
                        break
            tokens.extend(word)

        return [self.vocab.get(t, 0) for t in tokens]


def test_bpe():
    print("=== BPE Tokenizer Test ===")

    # Training text
    text = "hello world hello test world test"

    # Train tokenizer
    tokenizer = BPETokenizer(vocab_size=20)
    tokenizer.train(text)

    # Encode
    tokens = tokenizer.encode("hello world")

    print(f"Text: hello world")
    print(f"Tokens: {tokens}")
    print(f"Vocab size: {len(tokenizer.vocab)}")
    print("✅ BPE tokenizer working!\n")


if __name__ == "__main__":
    test_bpe()
```

### Exercise 4: Implement SwiGLU Activation

```python
import torch
import torch.nn as nn

class SwiGLU(nn.Module):
    """SwiGLU activation implementation"""

    def __init__(self, dim, hidden_dim):
        super().__init__()
        self.w = nn.Linear(dim, hidden_dim, bias=False)
        self.v = nn.Linear(dim, hidden_dim, bias=False)
        self.w2 = nn.Linear(hidden_dim, dim, bias=False)

    def forward(self, x):
        return self.w2(F.silu(self.w(x)) * self.v(x))


def test_swiglu():
    print("=== SwiGLU Activation Test ===")

    # Test parameters
    batch_size = 4
    seq_len = 16
    dim = 64
    hidden_dim = 256

    # Create SwiGLU layer
    swiglu = SwiGLU(dim, hidden_dim)

    # Test input
    x = torch.randn(batch_size, seq_len, dim)
    output = swiglu(x)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Parameters: {sum(p.numel() for p in swiglu.parameters()):,}")

    # Compare with GELU
    gelu = nn.GELU()
    linear = nn.Linear(dim, hidden_dim)
    linear2 = nn.Linear(hidden_dim, dim)

    x_gelu = linear2(gelu(linear(x)))

    print(f"\nSwiGLU output mean: {output.mean():.4f}")
    print(f"GELU output mean: {x_gelu.mean():.4f}")
    print("✅ SwiGLU working!\n")


if __name__ == "__main__":
    test_swiglu()
```

---

## Completion Checklist

- [ ] Multi-head attention implemented
- [ ] RoPE position embedding working
- [ ] BPE tokenizer trained
- [ ] SwiGLU activation tested
- [ ] Flash Attention understood
- [ ] Tokenization compared
- [ ] Architecture analysis complete
