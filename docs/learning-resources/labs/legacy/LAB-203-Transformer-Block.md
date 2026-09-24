# LAB-203: Transformer Block

## Overview
Implement a complete transformer encoder block.

## Prerequisites
- LAB-301 completed

## Setup

```bash
pip install torch
```

## Exercise 1: Transformer Encoder Block

```python
import torch
import torch.nn as nn

class TransformerEncoderBlock(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()

        # Multi-head attention mechanism
        self.self_attn = nn.MultiheadAttention(d_model, num_heads, dropout=dropout)

        # Feed-forward network (2-layer MLP)
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )

        # Layer normalization and dropout for residual connections
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        # Self-attention block with residual connection and layer norm
        attn_output, _ = self.self_attn(x, x, x, attn_mask=mask)
        x = x + self.dropout1(attn_output)
        x = self.norm1(x)

        # Feed-forward block with residual connection and layer norm
        ff_output = self.feed_forward(x)
        x = x + self.dropout2(ff_output)
        x = self.norm2(x)

        return x

# Test
block = TransformerEncoderBlock(d_model=64, num_heads=4, d_ff=256)
x = torch.randn(2, 10, 64)  # [batch, seq_len, d_model]
output = block(x)
print(f"Input shape: {x.shape}")
print(f"Output shape: {output.shape}")  # [2, 10, 64]
```

## Exercise 2: Stack Multiple Blocks

```python
class TransformerEncoder(nn.Module):
    def __init__(self, num_layers, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()

        # Stack multiple transformer encoder blocks
        self.layers = nn.ModuleList([
            TransformerEncoderBlock(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])

    def forward(self, x, mask=None):
        # Pass input through each transformer block sequentially
        for layer in self.layers:
            x = layer(x, mask)
        return x

# Test
encoder = TransformerEncoder(num_layers=4, d_model=64, num_heads=4, d_ff=256)
output = encoder(x)
print(f"Stacked output shape: {output.shape}")  # [2, 10, 64]
```

## Exercise 3: Add Positional Encoding

```python
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=512):
        super().__init__()

        # Create positional encoding matrix using sine and cosine functions
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() *
                             (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        # Add positional encoding to input embeddings
        return x + self.pe[:, :x.size(1)]

# Test
pos_enc = PositionalEncoding(d_model=64, max_len=128)
x = torch.randn(2, 10, 64)
x_with_pos = pos_enc(x)
print(f"With position shape: {x_with_pos.shape}")
```

## Exercise 4: Complete Transformer

```python
class Transformer(nn.Module):
    def __init__(self, num_layers, d_model, num_heads, d_ff,
                 vocab_size, max_len=512, dropout=0.1):
        super().__init__()

        # Token embedding layer
        self.token_embedding = nn.Embedding(vocab_size, d_model)

        # Positional encoding layer
        self.pos_encoding = PositionalEncoding(d_model, max_len)

        # Stack of transformer encoder blocks
        self.encoder = TransformerEncoder(num_layers, d_model, num_heads, d_ff, dropout)

    def forward(self, x, mask=None):
        # Convert token IDs to embeddings and add positional encoding
        x = self.token_embedding(x)
        x = self.pos_encoding(x)

        # Process through transformer encoder blocks
        x = self.encoder(x, mask)

        return x

# Test
model = Transformer(
    num_layers=4,
    d_model=64,
    num_heads=4,
    d_ff=256,
    vocab_size=1000,
    max_len=128
)

# Input: token ids
x = torch.randint(0, 1000, (2, 10))  # [batch, seq_len]
output = model(x)
print(f"Final output shape: {output.shape}")  # [2, 10, 64]
```

## Expected Outputs

- Single block preserves shape
- Stacked blocks preserve shape
- Positional encoding adds position info
- Complete transformer processes tokens

## Time Estimate: 3-4 hours
