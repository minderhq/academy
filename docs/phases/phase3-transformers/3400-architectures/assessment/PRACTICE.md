# 3400: Architectures - Practice

## Exercises

### Exercise 1: BERT-style Encoder

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class BERTLayer(nn.Module):
    """Single BERT encoder layer with self-attention and feed-forward."""

    def __init__(self, d_model=256, n_heads=4, d_ff=512, dropout=0.1):
        super().__init__()

        # Multi-head self-attention
        self.self_attn = nn.MultiheadAttention(
            d_model, n_heads, dropout=dropout, batch_first=True
        )

        # Feed-forward network
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )

        # Layer normalization and dropout
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        """
        Args:
            x: (batch, seq_len, d_model)
            mask: Optional attention mask

        Returns:
            (batch, seq_len, d_model)
        """
        # Self-attention block with residual connection
        attn_output, attn_weights = self.self_attn(
            x, x, x,
            attn_mask=mask,
            need_weights=False
        )
        x = x + self.dropout1(attn_output)
        x = self.norm1(x)

        # Feed-forward block with residual connection
        ff_output = self.feed_forward(x)
        x = x + self.dropout2(ff_output)
        x = self.norm2(x)

        return x

# Test the layer
layer = BERTLayer(d_model=256, n_heads=4, d_ff=512)
x = torch.randn(2, 10, 256)  # (batch, seq, dim)
output = layer(x)

print(f"Input shape: {x.shape}")
print(f"Output shape: {output.shape}")

# Expected Output:
# Input shape: torch.Size([2, 10, 256])
# Output shape: torch.Size([2, 10, 256])
```

**Explanation:**
- BERT uses bidirectional attention (can see entire sequence)
- Layer normalization BEFORE residual connections (Post-LN)
- GELU activation instead of ReLU
- No causal masking - sees full context

**Key Components:**
1. Multi-head self-attention
2. Position-wise feed-forward network
3. Residual connections
4. Layer normalization
5. Dropout for regularization

---

### Exercise 2: GPT-style Decoder

```python
class CausalMultiHeadAttention(nn.Module):
    """Multi-head attention with causal masking."""

    def __init__(self, d_model, n_heads, dropout=0.1):
        super().__init__()
        self.mha = nn.MultiheadAttention(
            d_model, n_heads, dropout=dropout, batch_first=True
        )
        self.d_model = d_model

    def forward(self, x):
        """
        Args:
            x: (batch, seq_len, d_model)

        Returns:
            (batch, seq_len, d_model)
        """
        batch_size, seq_len, _ = x.shape

        # Create causal mask (lower triangular)
        causal_mask = torch.triu(
            torch.ones(seq_len, seq_len, dtype=torch.bool, device=x.device),
            diagonal=1
        )

        # Apply attention with causal mask
        attn_output, _ = self.mha(
            x, x, x,
            attn_mask=causal_mask,
            need_weights=False
        )

        return attn_output

class GPTLayer(nn.Module):
    """Single GPT decoder layer."""

    def __init__(self, d_model=256, n_heads=4, d_ff=512, dropout=0.1):
        super().__init__()

        # Causal self-attention
        self.self_attn = CausalMultiHeadAttention(d_model, n_heads, dropout)

        # Feed-forward network
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )

        # Layer normalization (Pre-LN: norm before attention/ff)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x):
        """
        Args:
            x: (batch, seq_len, d_model)

        Returns:
            (batch, seq_len, d_model)
        """
        # Self-attention block (Pre-LN)
        residual = x
        x = self.norm1(x)
        attn_output = self.self_attn(x)
        x = residual + self.dropout1(attn_output)

        # Feed-forward block (Pre-LN)
        residual = x
        x = self.norm2(x)
        ff_output = self.feed_forward(x)
        x = residual + self.dropout2(ff_output)

        return x

# Test the layer
layer = GPTLayer(d_model=256, n_heads=4, d_ff=512)
x = torch.randn(2, 10, 256)
output = layer(x)

print(f"Input shape: {x.shape}")
print(f"Output shape: {output.shape}")

# Expected Output:
# Input shape: torch.Size([2, 10, 256])
# Output shape: torch.Size([2, 10, 256])
```

**Explanation:**
- GPT uses causal (autoregressive) masking
- Pre-LN: normalization before attention/FF
- Can only attend to previous positions
- Designed for text generation

**Key Differences from BERT:**
- Causal masking (no look-ahead)
- Pre-LN instead of Post-LN
- Designed for autoregressive generation

---

### Exercise 3: Encoder-Decoder (T5-style)

```python
class EncoderDecoderLayer(nn.Module):
    """T5-style encoder-decoder layer."""

    def __init__(self, d_model=256, n_heads=4, d_ff=512, dropout=0.1):
        super().__init__()

        # Encoder (bidirectional self-attention)
        self.encoder = BERTLayer(d_model, n_heads, d_ff, dropout)

        # Decoder components
        self.self_attn = CausalMultiHeadAttention(d_model, n_heads, dropout)
        self.cross_attn = nn.MultiheadAttention(
            d_model, n_heads, dropout=dropout, batch_first=True
        )
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )

        # Layer normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.dropout3 = nn.Dropout(dropout)

    def forward(self, enc_input, dec_input):
        """
        Args:
            enc_input: (batch, enc_len, d_model)
            dec_input: (batch, dec_len, d_model)

        Returns:
            (batch, dec_len, d_model)
        """
        # Encode input
        enc_output = self.encoder(enc_input)

        # Decoder self-attention (causal)
        residual = dec_input
        x = self.norm1(dec_input)
        attn_output = self.self_attn(x)
        x = residual + self.dropout1(attn_output)

        # Cross-attention (query from decoder, key/value from encoder)
        residual = x
        x = self.norm2(x)
        cross_output, _ = self.cross_attn(
            x, enc_output, enc_output,
            need_weights=False
        )
        x = residual + self.dropout2(cross_output)

        # Feed-forward
        residual = x
        x = self.norm3(x)
        ff_output = self.feed_forward(x)
        x = residual + self.dropout3(ff_output)

        return x

# Test the layer
layer = EncoderDecoderLayer(d_model=256, n_heads=4, d_ff=512)
enc_input = torch.randn(2, 10, 256)
dec_input = torch.randn(2, 5, 256)
output = layer(enc_input, dec_input)

print(f"Encoder input shape: {enc_input.shape}")
print(f"Decoder input shape: {dec_input.shape}")
print(f"Output shape: {output.shape}")

# Expected Output:
# Encoder input shape: torch.Size([2, 10, 256])
# Decoder input shape: torch.Size([2, 5, 256])
# Output shape: torch.Size([2, 5, 256])
```

**Explanation:**
- T5 uses encoder-decoder architecture
- Encoder: bidirectional attention
- Decoder: causal self-attention + cross-attention
- Cross-attention allows decoder to attend to encoder output

**Use Cases:**
- Translation
- Summarization
- Question answering
- Seq2seq tasks

---

### Exercise 4: Build Complete Models

```python
class BERT(nn.Module):
    """Complete BERT-style encoder model."""

    def __init__(self, vocab_size=30000, d_model=256, n_heads=4, n_layers=4,
                 d_ff=512, max_len=512, dropout=0.1):
        super().__init__()

        # Token and positional embeddings
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = nn.Parameter(torch.randn(max_len, d_model))

        # Encoder layers
        self.layers = nn.ModuleList([
            BERTLayer(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])

        # Output heads
        self.lm_head = nn.Linear(d_model, vocab_size)  # For masked LM
        self.cls_head = nn.Linear(d_model, 2)  # For classification

        self.dropout = nn.Dropout(dropout)
        self.d_model = d_model

    def forward(self, input_ids):
        """
        Args:
            input_ids: (batch, seq_len)

        Returns:
            logits: (batch, seq_len, vocab_size)
            pooled: (batch, d_model)
        """
        batch_size, seq_len = input_ids.shape

        # Embeddings
        x = self.token_embedding(input_ids)
        x = x + self.pos_encoding[:seq_len, :]
        x = self.dropout(x)

        # Pass through encoder layers
        for layer in self.layers:
            x = layer(x)

        # Output projections
        logits = self.lm_head(x)
        pooled = x[:, 0, :]  # Use [CLS] token representation

        return logits, pooled

class GPT(nn.Module):
    """Complete GPT-style decoder model."""

    def __init__(self, vocab_size=30000, d_model=256, n_heads=4, n_layers=4,
                 d_ff=512, max_len=512, dropout=0.1):
        super().__init__()

        # Token and positional embeddings
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = nn.Parameter(torch.randn(max_len, d_model))

        # Decoder layers
        self.layers = nn.ModuleList([
            GPTLayer(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])

        # Output head
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

        # Weight tying
        self.lm_head.weight = self.token_embedding.weight

        self.dropout = nn.Dropout(dropout)
        self.d_model = d_model

    def forward(self, input_ids):
        """
        Args:
            input_ids: (batch, seq_len)

        Returns:
            logits: (batch, seq_len, vocab_size)
        """
        batch_size, seq_len = input_ids.shape

        # Embeddings
        x = self.token_embedding(input_ids)
        x = x + self.pos_encoding[:seq_len, :]
        x = self.dropout(x)

        # Pass through decoder layers
        for layer in self.layers:
            x = layer(x)

        # Output projection
        logits = self.lm_head(x)

        return logits

# Test the models
print("Testing BERT model")
print("="*60)

bert = BERT(vocab_size=1000, d_model=128, n_heads=4, n_layers=2, d_ff=256)
input_ids = torch.randint(0, 1000, (2, 10))

logits, pooled = bert(input_ids)
print(f"Input IDs shape: {input_ids.shape}")
print(f"LM logits shape: {logits.shape}")
print(f"Pooled output shape: {pooled.shape}")

print("\nTesting GPT model")
print("="*60)

gpt = GPT(vocab_size=1000, d_model=128, n_heads=4, n_layers=2, d_ff=256)
input_ids = torch.randint(0, 1000, (2, 10))

logits = gpt(input_ids)
print(f"Input IDs shape: {input_ids.shape}")
print(f"LM logits shape: {logits.shape}")

# Expected Output:
# BERT: logits shape (batch, seq_len, vocab_size), pooled (batch, d_model)
# GPT: logits shape (batch, seq_len, vocab_size)
```

**Explanation:**
- **BERT**: Bidirectional encoder, good for understanding tasks
- **GPT**: Autoregressive decoder, good for generation tasks
- Both use transformer layers with different masking strategies

**Architecture Comparison:**
| Feature | BERT | GPT |
|---------|------|-----|
| Attention | Bidirectional | Causal |
| Primary Use | Understanding | Generation |
| Training | Masked LM | Autoregressive |
| Inference | Single pass | Sequential generation |

---

### Exercise 5: Model Comparison & Analysis

```python
def compare_architectures():
    """Compare BERT vs GPT architectures."""

    # Create models with same capacity
    vocab_size = 1000
    d_model = 128
    n_heads = 4
    n_layers = 2
    d_ff = 256

    bert = BERT(vocab_size, d_model, n_heads, n_layers, d_ff)
    gpt = GPT(vocab_size, d_model, n_heads, n_layers, d_ff)

    # Count parameters
    bert_params = sum(p.numel() for p in bert.parameters())
    gpt_params = sum(p.numel() for p in gpt.parameters())

    print("PARAMETER COUNT")
    print("="*60)
    print(f"BERT parameters: {bert_params:,}")
    print(f"GPT parameters: {gpt_params:,}")
    print(f"Difference: {abs(bert_params - gpt_params):,}")
    print(f"Difference %: {abs(bert_params - gpt_params) / bert_params * 100:.2f}%")

    # Test forward pass
    batch_size = 2
    seq_len = 10

    input_ids = torch.randint(0, vocab_size, (batch_size, seq_len))

    print("\n\nFORWARD PASS TEST")
    print("="*60)

    # BERT forward
    bert.eval()
    with torch.no_grad():
        bert_logits, bert_pooled = bert(input_ids)

    print(f"BERT input shape: {input_ids.shape}")
    print(f"BERT LM logits shape: {bert_logits.shape}")
    print(f"BERT pooled output shape: {bert_pooled.shape}")

    # GPT forward
    gpt.eval()
    with torch.no_grad():
        gpt_logits = gpt(input_ids)

    print(f"\nGPT input shape: {input_ids.shape}")
    print(f"GPT LM logits shape: {gpt_logits.shape}")

    # Memory usage comparison
    print("\n\nMEMORY USAGE (Approximate)")
    print("="*60)

    def get_model_size(model):
        param_size = 0
        buffer_size = 0
        for param in model.parameters():
            param_size += param.numel() * param.element_size()
        for buffer in model.buffers():
            buffer_size += buffer.numel() * buffer.element_size()
        return (param_size + buffer_size) / 1024**2  # MB

    bert_size = get_model_size(bert)
    gpt_size = get_model_size(gpt)

    print(f"BERT model size: {bert_size:.2f} MB")
    print(f"GPT model size: {gpt_size:.2f} MB")

    # Architecture differences summary
    print("\n\nARCHITECTURE DIFFERENCES")
    print("="*60)
    print("""
BERT (Encoder):
  - Bidirectional attention (sees full context)
  - Post-LN normalization
  - Used for: classification, NER, QA, etc.
  - Training: Masked Language Modeling
  - Inference: Single forward pass

GPT (Decoder):
  - Causal attention (autoregressive)
  - Pre-LN normalization
  - Used for: text generation, completion
  - Training: Next token prediction
  - Inference: Sequential generation

Key Design Choices:
  - BERT: Understanding > Generation
  - GPT: Generation > Understanding
  - Both can be adapted for various tasks
    """)

    return bert, gpt

# Run comparison
bert, gpt = compare_architectures()

# Expected Output:
# Detailed comparison of parameters, shapes, and memory usage
# BERT and GPT should have similar parameter counts for same config
```

---

## Bonus: Advanced Features

### Rotary Positional Embeddings (RoPE)

```python
class RotaryEmbedding(nn.Module):
    """Rotary Position Embeddings (RoPE)."""

    def __init__(self, d_model, max_len=512):
        super().__init__()
        self.d_model = d_model

        # Create rotation matrix
        theta = 1.0 / (10000 ** torch.arange(0, d_model, 2).float() / d_model)
        pos = torch.arange(max_len).float()
        freqs = torch.outer(pos, theta)

        # Complex representation
        self.register_buffer('freqs', torch.polar(torch.ones_like(freqs), freqs))

    def forward(self, x):
        """
        Apply rotary embeddings to input.
        Args:
            x: (batch, seq_len, d_model)
        Returns:
            (batch, seq_len, d_model)
        """
        seq_len = x.shape[1]
        freqs = self.freqs[:seq_len]

        # Split into real and imaginary parts
        x_complex = torch.view_as_complex(x.reshape(*x.shape[:-1], -1, 2))
        x_rotated = x_complex * freqs.unsqueeze(0).unsqueeze(-2)

        return torch.view_as_real(x_rotated).flatten(-2)

# Test RoPE
rope = RotaryEmbedding(d_model=128, max_len=512)
x = torch.randn(2, 10, 128)
x_rotated = rope(x)
print(f"Input shape: {x.shape}")
print(f"Rotated shape: {x_rotated.shape}")
```

---

## Summary: Architecture Selection Guide

```text
TASK → ARCHITECTURE RECOMMENDATIONS:

Text Classification:
  → BERT (or similar encoder)
  → Bidirectional context understanding

Text Generation:
  → GPT (or similar decoder)
  → Autoregressive generation

Translation / Summarization:
  → Encoder-Decoder (T5, BART)
  → Encode source, decode target

Question Answering:
  → BERT for extractive QA
  → Encoder-Decoder for generative QA

Code Generation:
  → GPT-style with causal masking
  → Train on code corpora

KEY DECISION FACTORS:

1. Bidirectional vs Causal
   - Need full context? → Encoder (BERT)
   - Autoregressive generation? → Decoder (GPT)

2. Model Size
   - Small/Efficient: d_model=256-512, n_layers=4-6
   - Medium: d_model=768, n_layers=12
   - Large: d_model=1024-2048, n_layers=24-36

3. Training Objectives
   - Masked LM: BERT-style
   - Causal LM: GPT-style
   - Span corruption: T5-style
```

---

**Last Updated:** 2026-02-05
