# LAB-301: Self-Attention Implementation

## Overview
Implement self-attention mechanism from scratch using PyTorch.

## Prerequisites
- LAB-201 completed
- Understanding of matrix multiplication
- Softmax function

## Setup

```bash
pip install torch matplotlib
```

## Exercise 1: Scaled Dot-Product Attention

```python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention(query, key, value, mask=None):
    """
    Compute scaled dot-product attention.

    Args:
        query: [batch_size, seq_len, d_k]
        key: [batch_size, seq_len, d_k]
        value: [batch_size, seq_len, d_v]
        mask: [batch_size, seq_len, seq_len] or None

    Returns:
        output: [batch_size, seq_len, d_v]
        attention_weights: [batch_size, seq_len, seq_len]
    """
    # TODO: Implement
    # 1. Compute scores: Q @ K^T
    # 2. Scale by sqrt(d_k)
    # 3. Apply mask if provided
    # 4. Apply softmax
    # 5. Multiply by values

    pass

# Test
batch_size = 2
seq_len = 5
d_k = 8
d_v = 8

query = torch.randn(batch_size, seq_len, d_k)
key = torch.randn(batch_size, seq_len, d_k)
value = torch.randn(batch_size, seq_len, d_v)

output, weights = scaled_dot_product_attention(query, key, value)

print(f"Output shape: {output.shape}")  # [2, 5, 8]
print(f"Attention weights shape: {weights.shape}")  # [2, 5, 5]
print(f"Weights sum to 1: {torch.allclose(weights.sum(-1), torch.ones(batch_size, seq_len))}")
```

## Exercise 2: Multi-Head Attention

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        # TODO: Define Q, K, V projections
        # TODO: Define output projection

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        # TODO: Implement
        # 1. Project to Q, K, V
        # 2. Reshape for multi-head
        # 3. Scaled dot-product attention
        # 4. Concatenate heads
        # 5. Output projection

        pass

# Test
mha = MultiHeadAttention(d_model=64, num_heads=4)
query = torch.randn(2, 10, 64)
key = torch.randn(2, 10, 64)
value = torch.randn(2, 10, 64)

output = mha(query, key, value)
print(f"Output shape: {output.shape}")  # [2, 10, 64]
```

## Exercise 3: Causal Masking

```python
def create_causal_mask(seq_len):
    """
    Create causal (lower triangular) mask.

    Args:
        seq_len: Length of sequence

    Returns:
        mask: [seq_len, seq_len]
    """
    # TODO: Implement
    # Use torch.tril or torch.triu
    pass

# Test
mask = create_causal_mask(5)
print(mask)
# Expected:
# tensor([[1, 0, 0, 0, 0],
#         [1, 1, 0, 0, 0],
#         [1, 1, 1, 0, 0],
#         [1, 1, 1, 1, 0],
#         [1, 1, 1, 1, 1]])
```

## Exercise 4: Visualize Attention

```python
def visualize_attention(attention_weights, tokens):
    """
    Visualize attention weights as heatmap.

    Args:
        attention_weights: [seq_len, seq_len]
        tokens: list of strings
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        attention_weights.numpy(),
        xticklabels=tokens,
        yticklabels=tokens,
        cmap='viridis',
        cbar=True
    )
    plt.xlabel('Keys')
    plt.ylabel('Queries')
    plt.title('Attention Weights')
    plt.show()

# Test
tokens = ["The", "cat", "sat", "on", "mat"]
attention = F.softmax(torch.randn(5, 5), dim=-1)
visualize_attention(attention[0], tokens)
```

## Expected Outputs

1. Exercise 1: Output [2, 5, 8], weights sum to 1
2. Exercise 2: Output [2, 10, 64]
3. Exercise 3: Lower triangular mask
4. Exercise 4: Attention heatmap displayed

## Troubleshooting

**Issue:** Dimension mismatch in multi-head
```python
# Solution: Ensure d_model is divisible by num_heads
d_model = 64
num_heads = 4  # 64 % 4 = 0 ✓
```

**Issue:** NaN in attention weights
```python
# Solution: Check for very large values before softmax
scores = torch.clamp(scores, max=50)
```

## Extensions

1. Add dropout to attention
2. Implement cross-attention
3. Add positional encoding
4. Benchmark with different head counts

## Time Estimate: 3-4 hours

---

**Last Updated:** 2026-02-04
