---
Document ID: 3100-PRACTICE
Title: "3100: Attention - Practice"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
---

# 3100: Attention - Practice

## Exercises

### Exercise 1: Implement Self-Attention

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SelfAttention(nn.Module):
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        # Q, K, V projections
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)
        self.out = nn.Linear(embed_dim, embed_dim)

        # Regularization
        self.dropout = nn.Dropout(0.1)
        self.scale = self.head_dim ** -0.5

    def forward(self, x, mask=None):
        batch_size, seq_len, embed_dim = x.shape

        # 1. Project to Q, K, V
        qkv = self.qkv(x)  # (batch, seq, 3 * embed_dim)
        qkv = qkv.reshape(batch_size, seq_len, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, batch, heads, seq, head_dim)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # 2. Compute attention scores
        attn = (q @ k.transpose(-2, -1)) * self.scale  # (batch, heads, seq, seq)

        # 3. Apply mask if provided
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        # 4. Apply attention to values
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)
        output = attn @ v  # (batch, heads, seq, head_dim)

        # 5. Combine heads
        output = output.transpose(1, 2).contiguous()  # (batch, seq, heads, head_dim)
        output = output.reshape(batch_size, seq_len, embed_dim)

        # 6. Output projection
        return self.out(output)

# Test
attn = SelfAttention(embed_dim=64, num_heads=4)
x = torch.randn(2, 10, 64)  # batch=2, seq=10, dim=64
output = attn(x)
print(f"Output shape: {output.shape}")  # Should be torch.Size([2, 10, 64])

# Expected Output:
# Output shape: torch.Size([2, 10, 64])
```

**Explanation:**
- Multi-head attention allows the model to attend to different representation subspaces
- Scaled dot-product attention prevents vanishing gradients
- Output projection mixes information from all heads

**Troubleshooting Tips:**
- If embed_dim is not divisible by num_heads, you'll get an error
- For causal attention, pass a lower triangular mask
- Gradient issues: check that scale is applied correctly

---

### Exercise 2: Implement Causal Mask

```python
import torch

def create_causal_mask(seq_len, device='cpu'):
    """
    Create a causal (lower triangular) mask for autoregressive generation.

    Args:
        seq_len: Length of the sequence
        device: Tensor device ('cpu' or 'cuda')

    Returns:
        Boolean mask tensor where True means valid position

    Example:
        For seq_len=5, returns:
        tensor([[ True, False, False, False, False],
                [ True,  True, False, False, False],
                [ True,  True,  True, False, False],
                [ True,  True,  True,  True, False],
                [ True,  True,  True,  True,  True]])
    """
    mask = torch.tril(torch.ones(seq_len, seq_len, dtype=torch.bool, device=device))
    return mask

# Alternative: Returns float mask (0 for masked, 1 for valid)
def create_causal_mask_float(seq_len, device='cpu'):
    """Create causal mask with float values (1 = valid, 0 = masked)."""
    mask = torch.tril(torch.ones(seq_len, seq_len, device=device))
    return mask

# Test
print("Causal Mask (Boolean):")
mask_bool = create_causal_mask(5)
print(mask_bool)

print("\nCausal Mask (Float):")
mask_float = create_causal_mask_float(5)
print(mask_float)

# Visual verification
import matplotlib.pyplot as plt
plt.figure(figsize=(8, 6))
plt.imshow(create_causal_mask(10).int(), cmap='viridis', origin='upper')
plt.title('Causal Attention Mask')
plt.xlabel('Key Position')
plt.ylabel('Query Position')
plt.colorbar(label='Allowed (1) / Masked (0)')
plt.tight_layout()
plt.show()

# Expected Output:
# tensor([[ True, False, False, False, False],
#         [ True,  True, False, False, False],
#         [ True,  True,  True, False, False],
#         [ True,  True,  True,  True, False],
#         [ True,  True,  True,  True,  True]])
```

**Explanation:**
- Causal masking ensures each position can only attend to previous positions
- Essential for autoregressive generation (like GPT)
- Lower triangular matrix: True where row >= col

**Use Cases:**
- Language modeling
- Text generation
- Time series forecasting

---

### Exercise 3: Visualize Attention

```python
import torch
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def visualize_attention(attention_weights, tokens, head_idx=0, layer_idx=0,
                        figsize=(12, 10), cmap='viridis'):
    """
    Visualize attention weights as a heatmap.

    Args:
        attention_weights: Attention weights tensor
                          Can be (seq, seq) or (batch, heads, seq, seq)
        tokens: The token strings for labels
        head_idx: Which attention head to visualize (if multi-head)
        layer_idx: Layer identifier for title
        figsize: Figure size
        cmap: Color map for heatmap

    Returns:
        matplotlib Figure object
    """
    # Handle different input shapes
    if attention_weights.dim() == 4:
        # Shape: (batch, heads, seq, seq)
        attn = attention_weights[0, head_idx].detach().cpu().numpy()
    elif attention_weights.dim() == 3:
        # Shape: (heads, seq, seq) or (batch, seq, seq)
        if attention_weights.shape[0] == attention_weights.shape[1]:
            attn = attention_weights[head_idx].detach().cpu().numpy()
        else:
            attn = attention_weights[0].detach().cpu().numpy()
    else:
        # Shape: (seq, seq)
        attn = attention_weights.detach().cpu().numpy()

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot heatmap
    sns.heatmap(
        attn,
        xticklabels=tokens,
        yticklabels=tokens,
        cmap=cmap,
        square=True,
        linewidths=0.5,
        cbar_kws={'label': 'Attention Weight'},
        ax=ax
    )

    ax.set_title(f'Attention Weights - Layer {layer_idx}, Head {head_idx}',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Keys', fontsize=12)
    ax.set_ylabel('Queries', fontsize=12)

    # Rotate labels for better readability
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)

    plt.tight_layout()
    return fig

def visualize_multihead_attention(attention_weights, tokens, n_heads=4,
                                   layer_idx=0, figsize=(16, 12)):
    """
    Visualize all attention heads in a grid.

    Args:
        attention_weights: (batch, heads, seq, seq) tensor
        tokens: The token strings
        n_heads: Number of attention heads
        layer_idx: Layer identifier
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    if attention_weights.dim() == 4:
        attn = attention_weights[0].detach().cpu().numpy()
    else:
        attn = attention_weights.detach().cpu().numpy()

    # Calculate grid dimensions
    n_cols = min(4, n_heads)
    n_rows = (n_heads + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_heads == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for head in range(n_heads):
        ax = axes[head]
        sns.heatmap(
            attn[head],
            xticklabels=tokens if head < n_cols else [],
            yticklabels=tokens if head % n_cols == 0 else [],
            cmap='viridis',
            square=True,
            cbar=True,
            ax=ax
        )
        ax.set_title(f'Head {head}')

    # Hide extra subplots
    for head in range(n_heads, len(axes)):
        axes[head].axis('off')

    fig.suptitle(f'Multi-Head Attention - Layer {layer_idx}',
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    return fig

# Test with random attention
print("Test 1: Single Head Attention")
attn_weights = torch.softmax(torch.randn(10, 10), dim=-1)
tokens = [f"token_{i}" for i in range(10)]
fig1 = visualize_attention(attn_weights, tokens)
plt.show()

# Test with multi-head attention
print("\nTest 2: Multi-Head Attention (4 heads)")
batch_attn = torch.softmax(torch.randn(1, 4, 10, 10), dim=-1)
fig2 = visualize_multihead_attention(batch_attn, tokens, n_heads=4)
plt.show()

# Test with causal attention pattern
print("\nTest 3: Causal Attention Pattern")
causal_attn = torch.tril(torch.ones(10, 10))
# Row-normalizing gives the pattern directly: 1/(i+1) at allowed
# positions, 0 above the diagonal. Applying softmax to those equal
# values would return them unchanged, and no row is ever fully
# masked (the diagonal always survives), so no NaN guard is needed
causal_attn = causal_attn / causal_attn.sum(dim=-1, keepdim=True)
fig3 = visualize_attention(causal_attn, tokens, cmap='Reds')
plt.show()

# Expected Output:
# - Three heatmaps showing different attention patterns
# - First: Random attention pattern
# - Second: 4 different attention heads in grid
# - Third: Lower triangular (causal) pattern
```

**Explanation:**
- Attention visualization reveals what tokens the model focuses on
- Multi-head visualization shows different learned patterns
- Causal mask shows autoregressive behavior

**Interpretation Guide:**
- Brighter colors = higher attention weight
- Rows = queries (what's being predicted)
- Columns = keys (what's being attended to)
- Diagonal focus = self-attention pattern
- Off-diagonal = cross-token dependencies

---

## Bonus: Attention Mechanism Comparison

```python
def compare_attention_mechanisms():
    """Compare different attention mechanisms."""

    seq_len = 8
    d_model = 64
    n_heads = 4

    # Sample input
    x = torch.randn(1, seq_len, d_model)

    # 1. Standard Self-Attention
    class SelfAttention(nn.Module):
        def __init__(self, d_model, n_heads):
            super().__init__()
            self.n_heads = n_heads
            self.head_dim = d_model // n_heads
            self.scale = self.head_dim ** -0.5
            self.qkv = nn.Linear(d_model, 3 * d_model)
            self.out = nn.Linear(d_model, d_model)

        def forward(self, x):
            B, N, C = x.shape
            qkv = self.qkv(x).reshape(B, N, 3, self.n_heads, self.head_dim)
            qkv = qkv.permute(2, 0, 3, 1, 4)
            q, k, v = qkv[0], qkv[1], qkv[2]

            attn = (q @ k.transpose(-2, -1)) * self.scale
            attn = F.softmax(attn, dim=-1)

            out = (attn @ v).transpose(1, 2).reshape(B, N, C)
            return self.out(out), attn

    # 2. Cross-Attention
    class CrossAttention(nn.Module):
        def __init__(self, d_model, n_heads):
            super().__init__()
            self.n_heads = n_heads
            self.head_dim = d_model // n_heads
            self.scale = self.head_dim ** -0.5
            self.q = nn.Linear(d_model, d_model)
            self.kv = nn.Linear(d_model, 2 * d_model)
            self.out = nn.Linear(d_model, d_model)

        def forward(self, x, context):
            B, N, C = x.shape
            _, M, _ = context.shape

            # Heads must move to dim 1: (B, H, N, head_dim). Without the
            # transposes the matmul runs per sequence position (H x H
            # scores instead of N x M) and the output is silent nonsense
            q = self.q(x).reshape(B, N, self.n_heads, self.head_dim).transpose(1, 2)
            kv = self.kv(context).reshape(B, M, 2, self.n_heads, self.head_dim)
            k, v = kv[..., 0, :, :], kv[..., 1, :, :]
            k, v = k.transpose(1, 2), v.transpose(1, 2)

            attn = (q @ k.transpose(-2, -1)) * self.scale  # (B, H, N, M)
            attn = F.softmax(attn, dim=-1)

            out = (attn @ v).transpose(1, 2).reshape(B, N, C)
            return self.out(out), attn

    # Test both
    self_attn = SelfAttention(d_model, n_heads)
    cross_attn = CrossAttention(d_model, n_heads)

    context = torch.randn(1, seq_len, d_model)

    self_out, self_attn_weights = self_attn(x)
    cross_out, cross_attn_weights = cross_attn(x, context)

    print(f"Self-attention output shape: {self_out.shape}")
    print(f"Cross-attention output shape: {cross_out.shape}")
    print(f"Self-attention weights shape: {self_attn_weights.shape}")
    print(f"Cross-attention weights shape: {cross_attn_weights.shape}")

    return self_attn_weights, cross_attn_weights

# Run comparison
self_w, cross_w = compare_attention_mechanisms()

print("\nKey Differences:")
print("Self-Attention: Q, K, V all from same input")
print("Cross-Attention: Q from input, K,V from context")
print("Use Cases:")
print("  - Self-Attention: BERT, GPT (intra-sequence)")
print("  - Cross-Attention: Encoder-Decoder (inter-sequence)")

# Expected Output:
# Self-attention output shape: torch.Size([1, 8, 64])
# Cross-attention output shape: torch.Size([1, 8, 64])
# Self-attention weights shape: torch.Size([1, 4, 8, 8])
# Cross-attention weights shape: torch.Size([1, 4, 8, 8])
```

**Summary of Key Concepts:**

1. **Multi-Head Attention**: Allows model to attend to different representation subspaces simultaneously
2. **Scaled Dot-Product**: Prevents softmax saturation by scaling with √d_k
3. **Causal Masking**: Ensures autoregressive property for generation
4. **Attention Visualization**: Crucial for interpretability and debugging
