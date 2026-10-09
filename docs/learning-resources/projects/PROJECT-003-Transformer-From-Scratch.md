---
Document ID: PROJECT-003
Title: "CAPSTONE PROJECT-003: Transformer from Scratch"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Tags: ['project', 'transformers', 'attention', 'pytorch']
---

# CAPSTONE PROJECT-003: Transformer from Scratch

**Build the architecture powering modern LLMs**

---

## Project Overview

Implement a complete Transformer model from scratch, including:

- Multi-head self-attention mechanism
- Positional encodings (sinusoidal and RoPE)
- Feed-forward networks
- Layer normalization and residual connections
- Complete encoder-decoder architecture
- Text generation and inference

**Estimated Time:** 20-25 hours

**Difficulty:** ⭐⭐⭐ Advanced

---

## Prerequisites

Complete these before starting:

- ✅ EXP 2101: Tensor Algebra
- ✅ 3101: Self-Attention Deep Dive
- ✅ 3102: Flash Attention
- ✅ 3201: Rotary Positional Embeddings
- ✅ PROJECT-002: Train Neural Network

---

## Project Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                     Transformer Architecture                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Input: "Hello world"                                             │
│       │                                                            │
│       ▼                                                            │
│  ┌─────────────┐                                                   │
│  │ Embedding + │                                                   │
│  │  Positional │                                                   │
│  │  Encoding   │                                                   │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Encoder Stack (N×)                          │  │
│  │  ┌───────────────────────────────────────────────────────┐  │  │
│  │  │  ┌────────────────────────────────────────────────┐  │  │  │
│  │  │  │         Multi-Head Self-Attention              │  │  │  │
│  │  │  │  (Scaled Dot-Product + Causal Mask)            │  │  │  │
│  │  │  └───────────────┬────────────────────────────────┘  │  │  │
│  │  │                  │                                    │  │  │
│  │  │  ┌───────────────▼────────────────────────────────┐  │  │  │
│  │  │  │     Add & Norm (Residual + LayerNorm)          │  │  │  │
│  │  │  └───────────────┬────────────────────────────────┘  │  │  │
│  │  │                  │                                    │  │  │
│  │  │  ┌───────────────▼────────────────────────────────┐  │  │  │
│  │  │  │        Feed-Forward Network (2× Linear)        │  │  │  │
│  │  │  └───────────────┬────────────────────────────────┘  │  │  │
│  │  │                  │                                    │  │  │
│  │  │  ┌───────────────▼────────────────────────────────┐  │  │  │
│  │  │  │          Add & Norm                            │  │  │  │
│  │  │  └───────────────────────────────────────────────┘  │  │  │
│  │  └───────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│                    ┌───────────────────┐                            │
│                    │  Linear + Softmax │                            │
│                    │   (Output Probs)  │                            │
│                    └───────────────────┘                            │
│                              │                                      │
│                              ▼                                      │
│  Output: Probability distribution over vocabulary                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Attention Mechanism (5 hours)

### 1.1 Scaled Dot-Product Attention

```python
# File: attention.py
"""
Attention Mechanisms
====================
"""

import numpy as np

from tensor import Tensor

def scaled_dot_product_attention(
    query: Tensor,
    key: Tensor,
    value: Tensor,
    mask: Tensor | None = None,
    dropout: float = 0.0
) -> tuple[Tensor, Tensor]:
    """
    Scaled Dot-Product Attention

    Args:
        query: (batch, seq_len, d_k)
        key: (batch, seq_len, d_k)
        value: (batch, seq_len, d_v)
        mask: (batch, seq_len, seq_len) or None
        dropout: Dropout probability

    Returns:
        output: (batch, seq_len, d_v)
        attention_weights: (batch, n_heads, seq_len, seq_len)
    """
    d_k = query.shape[-1]

    # Compute scores: Q @ K^T / sqrt(d_k)
    scores = query @ key.transpose(-2, -1) / Tensor(np.sqrt(d_k))

    # Apply mask if provided
    if mask is not None:
        # Replace masked positions with large negative value
        scores = scores + (mask * Tensor(-1e9))

    # Apply softmax
    attention_weights = softmax(scores, dim=-1)

    # Apply dropout
    if dropout > 0:
        attention_weights = dropout_layer(attention_weights, dropout)

    # Compute output: scores @ V
    output = attention_weights @ value

    return output, attention_weights

def softmax(x: Tensor, dim: int = -1) -> Tensor:
    """Numerically stable softmax"""
    # Subtract max for numerical stability
    max_vals = x.data.max(axis=dim, keepdims=True)
    exp_x = Tensor(np.exp(x.data - max_vals))
    sum_exp = exp_x.sum(axis=dim, keepdims=True)
    return exp_x / sum_exp

def dropout_layer(x: Tensor, p: float) -> Tensor:
    """Apply dropout during training"""
    if np.random.random() > p:
        mask = Tensor((np.random.rand(*x.shape) > p).astype(np.float32) / (1 - p))
        return x * mask
    return x

class AttentionMask:
    """Utilities for creating attention masks"""

    @staticmethod
    def causal_mask(seq_len: int) -> Tensor:
        """
        Create causal (autoregressive) mask
        Prevents positions from attending to future positions
        """
        mask = np.triu(np.ones((seq_len, seq_len)), k=1).astype(np.float32)
        return Tensor(mask)

    @staticmethod
    def padding_mask(seq_len: int, lengths: np.ndarray) -> Tensor:
        """
        Create padding mask
        Masks out padding tokens
        """
        batch_size = len(lengths)
        mask = np.zeros((batch_size, seq_len, seq_len), dtype=np.float32)

        for i, length in enumerate(lengths):
            # Mask positions beyond the actual sequence length
            mask[i, :, length:] = 1.0

        return Tensor(mask)
```

### 1.2 Multi-Head Attention

```python
# File: multihead_attention.py
"""
Multi-Head Attention
====================
"""


from tensor import Tensor
import numpy as np

class MultiHeadAttention:
    """
    Multi-Head Attention Mechanism

    Allows the model to attend to different representation subspaces
    """

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        """
        Args:
            d_model: Model dimension
            n_heads: Number of attention heads
            dropout: Dropout probability
        """
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads  # Dimension per head
        self.d_v = d_model // n_heads
        self.dropout = dropout

        # Linear projections for Q, K, V
        self.W_q = Tensor(np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model), requires_grad=True)
        self.W_k = Tensor(np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model), requires_grad=True)
        self.W_v = Tensor(np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model), requires_grad=True)

        # Output projection
        self.W_o = Tensor(np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model), requires_grad=True)

        self.parameters = [self.W_q, self.W_k, self.W_v, self.W_o]

    def forward(self, query: Tensor, key: Tensor, value: Tensor,
                mask: Tensor | None = None) -> Tensor:
        """
        Forward pass

        Args:
            query: (batch, seq_len, d_model)
            key: (batch, seq_len, d_model)
            value: (batch, seq_len, d_model)
            mask: (batch, seq_len, seq_len) or None

        Returns:
            output: (batch, seq_len, d_model)
        """
        batch_size = query.shape[0]

        # Linear projections
        Q = query @ self.W_q  # (batch, seq_len, d_model)
        K = key @ self.W_k
        V = value @ self.W_v

        # Split into heads and reshape
        # (batch, seq_len, n_heads, d_k)
        Q = Q.reshape(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = K.reshape(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = V.reshape(batch_size, -1, self.n_heads, self.d_v).transpose(1, 2)

        # Reshape back: (batch * n_heads, seq_len, d_k)
        Q = Q.reshape(batch_size * self.n_heads, -1, self.d_k)
        K = K.reshape(batch_size * self.n_heads, -1, self.d_k)
        V = V.reshape(batch_size * self.n_heads, -1, self.d_v)

        # Expand mask if needed
        if mask is not None:
            mask = mask.unsqueeze(1).repeat(1, self.n_heads, 1, 1)
            mask = mask.reshape(batch_size * self.n_heads, -1, -1)

        # Scaled dot-product attention
        attn_output, _ = scaled_dot_product_attention(Q, K, V, mask, self.dropout)

        # Reshape: (batch, n_heads, seq_len, d_v) -> (batch, seq_len, d_model)
        attn_output = attn_output.reshape(batch_size, self.n_heads, -1, self.d_v)
        attn_output = attn_output.transpose(1, 2)  # (batch, seq_len, n_heads, d_v)
        attn_output = attn_output.reshape(batch_size, -1, self.d_model)

        # Output projection
        output = attn_output @ self.W_o

        return output

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
```

### Phase 1 Checklist
- [ ] Scaled dot-product attention implemented
- [ ] Causal mask working
- [ ] Padding mask working
- [ ] Multi-head attention working
- [ ] Gradient flow verified

---

## Phase 2: Transformer Components (5 hours)

### 2.1 Positional Encoding

```python
# File: positional_encoding.py
"""
Positional Encodings
====================
"""

import numpy as np
from tensor import Tensor

class SinusoidalPositionalEncoding:
    """
    Sinusoidal Positional Encoding

    Uses sine and cosine functions of different frequencies
    """

    def __init__(self, d_model: int, max_len: int = 5000):
        """
        Args:
            d_model: Model dimension
            max_len: Maximum sequence length
        """
        self.d_model = d_model
        self.max_len = max_len

        # Create positional encoding matrix
        pe = np.zeros((max_len, d_model))

        # Create position indices
        position = np.arange(0, max_len, dtype=np.float32).reshape(-1, 1)

        # Create div term
        div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model))

        # Apply sin to even indices, cos to odd indices
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)

        self.pe = Tensor(pe)

    def __call__(self, x: Tensor) -> Tensor:
        """
        Add positional encoding to input

        Args:
            x: (batch, seq_len, d_model)

        Returns:
            output: (batch, seq_len, d_model)
        """
        seq_len = x.shape[1]
        return x + self.pe.data[:seq_len, :]

class RotaryPositionalEncoding:
    """
    Rotary Positional Encoding (RoPE)

    More modern approach that encodes absolute position
    """

    def __init__(self, d_model: int, max_len: int = 2048):
        """
        Args:
            d_model: Model dimension (must be even)
            max_len: Maximum sequence length
        """
        assert d_model % 2 == 0, "d_model must be even"

        self.d_model = d_model
        self.max_len = max_len

        # Create rotation angles
        theta = np.arange(0, d_model // 2)
        freqs = 1.0 / (10000 ** (theta * 2 / d_model))

        # Create position indices
        positions = np.arange(0, max_len)

        # Compute angles: outer product
        angles = positions[:, np.newaxis] * freqs[np.newaxis, :]

        # Precompute cos and sin
        self.cos = Tensor(np.cos(angles))
        self.sin = Tensor(np.sin(angles))

    def rotate(self, x: Tensor) -> Tensor:
        """
        Apply rotation to input tensor

        Args:
            x: (batch, seq_len, d_model)

        Returns:
            output: (batch, seq_len, d_model)
        """
        batch_size, seq_len, d_model = x.shape

        # Split into two halves
        x1 = x.data[:, :, :d_model // 2]
        x2 = x.data[:, :, d_model // 2:]

        # Get cos and sin for this sequence length
        cos = self.cos.data[:seq_len, :]
        sin = self.sin.data[:seq_len, :]

        # Apply rotation
        x_rotated_1 = x1 * cos - x2 * sin
        x_rotated_2 = x1 * sin + x2 * cos

        # Concatenate
        x_rotated = np.concatenate([x_rotated_1, x_rotated_2], axis=-1)

        return Tensor(x_rotated)

    def __call__(self, query: Tensor, key: Tensor) -> tuple[Tensor, Tensor]:
        """
        Apply RoPE to query and key

        Args:
            query: (batch, seq_len, d_model)
            key: (batch, seq_len, d_model)

        Returns:
            rotated_query, rotated_key
        """
        return self.rotate(query), self.rotate(key)
```

### 2.2 Feed-Forward Network

```python
# File: ffn.py
"""
Feed-Forward Network
====================
"""

from tensor import Tensor
import numpy as np

class FeedForwardNetwork:
    """
    Position-wise Feed-Forward Network

    Two linear transformations with ReLU activation
    FFN(x) = max(0, xW1 + b1)W2 + b2
    """

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        """
        Args:
            d_model: Model dimension
            d_ff: Hidden dimension (usually 4× d_model)
            dropout: Dropout probability
        """
        self.d_model = d_model
        self.d_ff = d_ff
        self.dropout = dropout

        # Linear layers
        self.W1 = Tensor(np.random.randn(d_model, d_ff) * np.sqrt(2.0 / d_model), requires_grad=True)
        self.b1 = Tensor(np.zeros(d_ff), requires_grad=True)
        self.W2 = Tensor(np.random.randn(d_ff, d_model) * np.sqrt(2.0 / d_ff), requires_grad=True)
        self.b2 = Tensor(np.zeros(d_model), requires_grad=True)

        self.parameters = [self.W1, self.b1, self.W2, self.b2]

    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass

        Args:
            x: (batch, seq_len, d_model)

        Returns:
            output: (batch, seq_len, d_model)
        """
        # First linear + ReLU
        hidden = x @ self.W1 + self.b1
        hidden = hidden.relu()

        # Dropout
        if self.dropout > 0:
            hidden = dropout_layer(hidden, self.dropout)

        # Second linear
        output = hidden @ self.W2 + self.b2

        return output

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
```

### 2.3 Layer Normalization

```python
# File: layer_norm.py
"""
Layer Normalization
===================
"""

from tensor import Tensor
import numpy as np

class LayerNormalization:
    """
    Layer Normalization

    Normalizes across the feature dimension
    """

    def __init__(self, d_model: int, eps: float = 1e-6):
        """
        Args:
            d_model: Feature dimension
            eps: Small constant for numerical stability
        """
        self.d_model = d_model
        self.eps = eps

        # Learnable parameters
        self.gamma = Tensor(np.ones(d_model), requires_grad=True)
        self.beta = Tensor(np.zeros(d_model), requires_grad=True)

        self.parameters = [self.gamma, self.beta]

    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass

        Args:
            x: (batch, seq_len, d_model)

        Returns:
            output: (batch, seq_len, d_model)
        """
        # Compute mean and variance
        mean = x.data.mean(axis=-1, keepdims=True)
        var = x.data.var(axis=-1, keepdims=True)

        # Normalize
        normalized = (x.data - mean) / np.sqrt(var + self.eps)

        # Scale and shift
        output = Tensor(normalized) * self.gamma + self.beta

        return output

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
```

### Phase 2 Checklist
- [ ] Sinusoidal positional encoding working
- [ ] RoPE implemented
- [ ] Feed-forward network working
- [ ] Layer normalization working
- [ ] All gradients flowing correctly

---

## Phase 3: Transformer Block (4 hours)

### 3.1 Transformer Encoder Layer

```python
# File: transformer_block.py
"""
Transformer Block
=================
"""

from tensor import Tensor


class TransformerEncoderLayer:
    """
    Single Transformer Encoder Layer

    Consists of:
    1. Multi-head self-attention
    2. Add & Norm (residual connection + layer norm)
    3. Feed-forward network
    4. Add & Norm
    """

    def __init__(self, d_model: int, n_heads: int, d_ff: int,
                 dropout: float = 0.1):
        """
        Args:
            d_model: Model dimension
            n_heads: Number of attention heads
            d_ff: Feed-forward hidden dimension
            dropout: Dropout probability
        """
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_ff = d_ff
        self.dropout = dropout

        # Sub-layers
        self.self_attn = MultiHeadAttention(d_model, n_heads, dropout)
        self.ffn = FeedForwardNetwork(d_model, d_ff, dropout)
        self.norm1 = LayerNormalization(d_model)
        self.norm2 = LayerNormalization(d_model)

        # Collect parameters
        self.parameters = []
        self.parameters.extend(self.self_attn.parameters)
        self.parameters.extend(self.ffn.parameters)
        self.parameters.extend(self.norm1.parameters)
        self.parameters.extend(self.norm2.parameters)

    def forward(self, x: Tensor, mask: Tensor | None = None) -> Tensor:
        """
        Forward pass

        Args:
            x: (batch, seq_len, d_model)
            mask: (batch, seq_len, seq_len) or None

        Returns:
            output: (batch, seq_len, d_model)
        """
        # Self-attention with residual
        attn_output = self.self_attn(x, x, x, mask)
        x = x + dropout_layer(attn_output, self.dropout)
        x = self.norm1(x)

        # Feed-forward with residual
        ffn_output = self.ffn(x)
        x = x + dropout_layer(ffn_output, self.dropout)
        x = self.norm2(x)

        return x

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

class TransformerEncoder:
    """
    Stack of Transformer Encoder Layers
    """

    def __init__(self, d_model: int, n_heads: int, d_ff: int,
                 n_layers: int, dropout: float = 0.1):
        """
        Args:
            d_model: Model dimension
            n_heads: Number of attention heads
            d_ff: Feed-forward hidden dimension
            n_layers: Number of encoder layers
            dropout: Dropout probability
        """
        self.layers = [
            TransformerEncoderLayer(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ]

        # Collect all parameters
        self.parameters = []
        for layer in self.layers:
            self.parameters.extend(layer.parameters)

    def forward(self, x: Tensor, mask: Tensor | None = None) -> Tensor:
        """
        Forward pass through all layers

        Args:
            x: (batch, seq_len, d_model)
            mask: (batch, seq_len, seq_len) or None

        Returns:
            output: (batch, seq_len, d_model)
        """
        for layer in self.layers:
            x = layer(x, mask)
        return x

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
```

### Phase 3 Checklist
- [ ] Encoder layer implemented
- [ ] Residual connections working
- [ ] Layer normalization in correct positions
- [ ] Multiple layers stacking correctly
- [ ] Forward pass working end-to-end

---

## Phase 4: Complete Transformer Model (4 hours)

### 4.1 GPT-Style Decoder

```python
# File: transformer.py
"""
Complete Transformer Model
===========================
"""


from tensor import Tensor
import numpy as np

class GPTModel:
    """
    GPT-style Transformer Decoder

    Autoregressive language model
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 768,
        n_heads: int = 12,
        n_layers: int = 12,
        d_ff: int = 3072,
        max_len: int = 1024,
        dropout: float = 0.1
    ):
        """
        Args:
            vocab_size: Size of vocabulary
            d_model: Model dimension
            n_heads: Number of attention heads
            n_layers: Number of transformer layers
            d_ff: Feed-forward hidden dimension
            max_len: Maximum sequence length
            dropout: Dropout probability
        """
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.max_len = max_len
        self.dropout = dropout

        # Token embeddings
        self.token_embeddings = Tensor(
            np.random.randn(vocab_size, d_model) * np.sqrt(2.0 / vocab_size),
            requires_grad=True
        )

        # Positional encoding
        self.pos_encoding = SinusoidalPositionalEncoding(d_model, max_len)

        # Transformer layers
        self.transformer = TransformerEncoder(d_model, n_heads, d_ff, n_layers, dropout)

        # Output projection
        self.lm_head = Tensor(
            np.random.randn(d_model, vocab_size) * np.sqrt(2.0 / d_model),
            requires_grad=True
        )

        # Collect parameters
        self.parameters = [self.token_embeddings, self.lm_head]
        self.parameters.extend(self.transformer.parameters)

    def forward(self, input_ids: Tensor, mask: Tensor | None = None) -> Tensor:
        """
        Forward pass

        Args:
            input_ids: (batch, seq_len) - token IDs
            mask: (batch, seq_len, seq_len) - attention mask

        Returns:
            logits: (batch, seq_len, vocab_size)
        """
        batch_size, seq_len = input_ids.shape

        # Token embeddings
        x = self.token_embeddings.data[input_ids.data]

        # Positional encoding
        x = self.pos_encoding(x)

        # Create causal mask if not provided
        if mask is None:
            mask = AttentionMask.causal_mask(seq_len)
            # Expand for batch
            mask_data = np.tile(mask.data[np.newaxis, :, :], (batch_size, 1, 1))
            mask = Tensor(mask_data)

        # Transformer
        x = self.transformer(x, mask)

        # Project to vocabulary
        logits = x @ self.lm_head

        return logits

    def generate(self, prompt: Tensor, max_new_tokens: int = 100,
                 temperature: float = 1.0) -> Tensor:
        """
        Autoregressive generation

        Args:
            prompt: (batch, seq_len) - token IDs
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature

        Returns:
            output: (batch, seq_len + max_new_tokens) - generated token IDs
        """
        batch_size, seq_len = prompt.shape
        output = prompt.data.copy()

        for _ in range(max_new_tokens):
            # Truncate to max_len if needed
            if output.shape[1] > self.max_len:
                input_ids = Tensor(output[:, -self.max_len:])
            else:
                input_ids = Tensor(output)

            # Forward pass
            logits = self.forward(input_ids)

            # Get next token logits
            next_token_logits = logits.data[:, -1, :]

            # Apply temperature
            if temperature != 1.0:
                next_token_logits = next_token_logits / temperature

            # Sample
            probs = np.exp(next_token_logits - next_token_logits.max(axis=1, keepdims=True))
            probs = probs / probs.sum(axis=1, keepdims=True)

            next_token = np.array([
                np.random.choice(len(p), p=p / p.sum())
                for p in probs
            ])

            # Append
            output = np.concatenate([output, next_token.reshape(-1, 1)], axis=1)

        return Tensor(output)

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
```

### Phase 4 Checklist
- [ ] Complete GPT model implemented
- [ ] Forward pass working
- [ ] Generation working
- [ ] All parameters connected to computation graph

---

## Phase 5: Training and Evaluation (7 hours)

### 5.1 Training Setup

```python
# File: train.py
"""
Train Transformer Model
=======================
"""

from transformer import GPTModel
from nn import CrossEntropyLoss, Adam
from tensor import Tensor
import numpy as np

# Hyperparameters
config = {
    'vocab_size': 10000,
    'd_model': 256,
    'n_heads': 8,
    'n_layers': 6,
    'd_ff': 1024,
    'max_len': 256,
    'dropout': 0.1
}

# Create model
model = GPTModel(**config)
print(f"Model parameters: {sum(p.data.size for p in model.parameters):,}")

# Create loss and optimizer
criterion = CrossEntropyLoss()
optimizer = Adam(model.parameters, lr=1e-4)

# Training data (simplified - use actual text data)
# In practice, use WikiText, BookCorpus, etc.
text_data = [
    "The quick brown fox jumps over the lazy dog.",
    "Machine learning is a subset of artificial intelligence.",
    # ... more text
]

# Create vocabulary and tokenizer
def create_vocab(texts, vocab_size):
    """Create vocabulary from texts"""
    # Simple word-level vocabulary
    word_counts = {}
    for text in texts:
        for word in text.lower().split():
            word_counts[word] = word_counts.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    # Create vocab dictionary
    vocab = {word: idx for idx, (word, _) in enumerate(sorted_words[:vocab_size-2])}
    vocab['<PAD>'] = vocab_size - 2
    vocab['<UNK>'] = vocab_size - 1

    return vocab

vocab = create_vocab(text_data, config['vocab_size'])
print(f"Vocabulary size: {len(vocab)}")

def tokenize(text, vocab, max_len):
    """Tokenize text"""
    tokens = [vocab.get(word.lower(), vocab['<UNK>']) for word in text.split()]
    tokens = tokens[:max_len]
    # Pad if needed
    tokens = tokens + [vocab['<PAD>']] * (max_len - len(tokens))
    return tokens

# Create dataset
def create_dataset(texts, vocab, max_len):
    """Create training dataset"""
    inputs = []
    targets = []

    for text in texts:
        tokens = tokenize(text, vocab, max_len)

        # Input: tokens[:-1], Target: tokens[1:]
        inputs.append(tokens[:-1])
        targets.append(tokens[1:])

    return np.array(inputs), np.array(targets)

X_train, y_train = create_dataset(text_data, vocab, config['max_len'])
print(f"Training data shape: {X_train.shape}")

# Training loop
n_epochs = 50
batch_size = 8

for epoch in range(n_epochs):
    epoch_loss = 0.0
    n_batches = 0

    # Mini-batch training
    for i in range(0, len(X_train), batch_size):
        batch_x = Tensor(X_train[i:i+batch_size])
        batch_y = Tensor(y_train[i:i+batch_size])

        # Forward pass
        logits = model(batch_x)

        # Reshape for loss: (batch * seq_len, vocab_size)
        logits_flat = logits.reshape(-1, config['vocab_size'])
        targets_flat = Tensor(batch_y.data.reshape(-1, 1))

        # Compute loss
        loss = criterion(logits_flat, targets_flat)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()
        n_batches += 1

    avg_loss = epoch_loss / n_batches

    if (epoch + 1) % 10 == 0 or epoch == 0:
        print(f"Epoch {epoch+1}/{n_epochs}, Loss: {avg_loss:.4f}")
```

### 5.2 Text Generation

```python
# File: generate.py
"""
Generate Text with Trained Model
=================================
"""

def generate_text(model, prompt, vocab, max_tokens=50, temperature=0.8):
    """Generate text from prompt"""

    # Create reverse vocab
    reverse_vocab = {idx: word for word, idx in vocab.items()}

    # Tokenize prompt
    input_tokens = tokenize(prompt, vocab, config['max_len'])
    input_tensor = Tensor(np.array([input_tokens]))

    # Generate
    output = model.generate(input_tensor, max_new_tokens=max_tokens, temperature=temperature)

    # Decode
    generated_tokens = output.data[0]
    text = ' '.join([reverse_vocab.get(token, '<UNK>') for token in generated_tokens])

    return text

# Generate after training
print("\n=== Generation ===")
prompt = "The future of artificial intelligence"
generated = generate_text(model, prompt, vocab, max_tokens=30, temperature=0.8)
print(f"Prompt: {prompt}")
print(f"Generated: {generated}")
```

### Phase 5 Checklist
- [ ] Training loop implemented
- [ ] Loss decreasing
- [ ] Text generation working
- [ ] Temperature sampling working

---

## Bonus Challenges

1. **Implement Flash Attention** - Memory-efficient attention
2. **Add Beam Search** - Better generation
3. **Implement KV-Cache** - Faster generation
4. **Add Gradient Clipping** - Training stability
5. **Implement Learning Rate Scheduling** - Warmup + decay
6. **Add Evaluation Metrics** - Perplexity, BLEU

---

## Project Completion Checklist

```text
[ ] Phase 1: Attention Mechanism
[ ] Phase 2: Transformer Components
[ ] Phase 3: Transformer Block
[ ] Phase 4: Complete Transformer Model
[ ] Phase 5: Training and Evaluation
[ ] Bonus: At least one challenge completed
```

---

## Related Resources

- **[3101: Self-Attention](../../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)** - Attention theory
- **[3201: RoPE](../../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)** - Positional encoding
- **[3302: Normalization](../../phases/phase3-transformers/3300-decoding/3302-Normalization-Layers.md)** - Layer normalization
- **[3402: Decoder-Only Models](../../phases/phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md)** - GPT architecture

---

**Congratulations!** You've built a Transformer from scratch:

- 🧠 Multi-head self-attention
- 📍 Positional encoding (sinusoidal & RoPE)
- 🏗️ Complete encoder/decoder blocks
- 📝 Text generation
- 🎯 End-to-end training

## Next Steps

- **[Volume 4: Quantization & Optimization](../../volumes/VOLUME-4-Quantization.md)**
