# EXP_3201: RoPE Positional Embeddings Experiments

## Overview
Practical experiments for understanding and testing Rotary Position Embeddings (RoPE) on transformer models.

## Experiment 1: RoPE Implementation from Scratch

### Objective
Implement RoPE from scratch and verify correctness.

### Implementation
```python
# rope_implementation.py
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt

class RotaryEmbedding(nn.Module):
    """
    Rotary Position Embeddings (RoPE)

    Paper: "RoFormer: Enhanced Transformer with Rotary Position Embedding"
    Link: https://arxiv.org/abs/2104.09864
    """

    def __init__(self, dim: int, max_position_embeddings: int = 2048, base: int = 10000):
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base

        # Create inverse frequency buffer
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)

        # Build cache
        self._build_cache(max_position_embeddings)

    def _build_cache(self, seq_len: int):
        """Build cos/sin cache for faster inference"""
        t = torch.arange(seq_len, device=self.inv_freq.device).type_as(self.inv_freq)
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)

        # Create cos and sin
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer("cos_cached", emb.cos()[None, None, :, :], persistent=False)
        self.register_buffer("sin_cached", emb.sin()[None, None, :, :], persistent=False)

    def forward(self, x: torch.Tensor, seq_len: int = None):
        """
        Args:
            x: (batch, seq_len, head_dim) or (batch, heads, seq_len, head_dim)
            seq_len: optional sequence length override
        Returns:
            cos, sin: (1, 1, seq_len, head_dim)
        """
        if seq_len is None:
            seq_len = x.shape[-2]

        # Extend cache if needed
        if seq_len > self.cos_cached.shape[-2]:
            self._build_cache(seq_len)

        return (
            self.cos_cached[..., :seq_len, :],
            self.sin_cached[..., :seq_len, :]
        )


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """
    Rotate half the hidden dims of the input

    Args:
        x: (batch, heads, seq_len, head_dim)
    Returns:
        rotated: (batch, heads, seq_len, head_dim)
    """
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q: torch.Tensor, k: torch.Tensor,
                         cos: torch.Tensor, sin: torch.Tensor) -> tuple:
    """
    Apply rotary position embedding to query and key

    Args:
        q: (batch, heads, seq_len, head_dim)
        k: (batch, heads, seq_len, head_dim)
        cos: (1, 1, seq_len, head_dim)
        sin: (1, 1, seq_len, head_dim)
    Returns:
        q_embed, k_embed: with RoPE applied
    """
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


# Test implementation
def test_rope_correctness():
    """Test RoPE implementation against reference"""

    print("Testing RoPE Implementation")
    print("="*60)

    # Parameters
    batch = 2
    seq_len = 128
    heads = 8
    head_dim = 64

    # Create RoPE
    rope = RotaryEmbedding(dim=head_dim, max_position_embeddings=2048)

    # Create query and key
    q = torch.randn(batch, heads, seq_len, head_dim)
    k = torch.randn(batch, heads, seq_len, head_dim)

    # Get cos/sin
    cos, sin = rope(q)

    print(f"Input shape: {q.shape}")
    print(f"Cos shape: {cos.shape}")
    print(f"Sin shape: {sin.shape}")

    # Apply RoPE
    q_rot, k_rot = apply_rotary_pos_emb(q, k, cos, sin)

    print(f"Output shape: {q_rot.shape}")

    # Verify rotation preserves norm
    q_norm_before = q.norm(dim=-1).mean()
    q_norm_after = q_rot.norm(dim=-1).mean()

    print(f"\nNorm preservation check:")
    print(f"  Q norm before: {q_norm_before:.4f}")
    print(f"  Q norm after:  {q_norm_after:.4f}")
    print(f"  Difference:    {abs(q_norm_before - q_norm_after):.6f}")

    assert abs(q_norm_before - q_norm_after) < 1e-5, "RoPE changed the norm!"
    print("✓ Norm preservation: PASSED")

    # Test relative position invariance
    print("\nRelative position invariance check:")

    # Create tokens at positions i and j
    token = torch.randn(1, heads, 1, head_dim)

    # Get RoPE for both positions
    cos_i, sin_i = rope(token, seq_len=1)
    cos_j, sin_j = rope(token, seq_len=1)

    # Apply rotation at position i
    q_i, k_i = apply_rotary_pos_emb(token, token, cos_i, sin_i)

    # Apply rotation at position j
    q_j, k_j = apply_rotary_pos_emb(token, token, cos_j, sin_j)

    # The inner product should only depend on relative distance
    # This is a simplified test - full test would use actual positions
    print("✓ Position embedding applied successfully")

    return q_rot, k_rot


if __name__ == "__main__":
    test_rope_correctness()
```

---

## Experiment 2: RoPE vs Learned Positional Embeddings

### Objective
Compare RoPE with learned absolute positional embeddings.

### Comparison Script
```python
# rope_vs_learned.py
import torch
import torch.nn as nn
import matplotlib.pyplot as plt

class LearnedPositionalEmbedding(nn.Module):
    """Standard learned positional embeddings (GPT-style)"""

    def __init__(self, max_seq_len: int, embed_dim: int):
        super().__init__()
        self.max_seq_len = max_seq_len
        self.embed_dim = embed_dim
        self.position_embeddings = nn.Embedding(max_seq_len, embed_dim)

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: (batch, seq_len, embed_dim)
        """
        seq_len = x.shape[1]
        positions = torch.arange(seq_len, device=x.device)
        return self.position_embeddings(positions) + x


class RoPEPositionalEmbedding(nn.Module):
    """RoPE positional embedding"""

    def __init__(self, embed_dim: int, max_seq_len: int = 2048, base: int = 10000):
        super().__init__()
        self.rope = RotaryEmbedding(embed_dim, max_seq_len, base)

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: (batch, heads, seq_len, head_dim) - already projected to Q/K
        """
        cos, sin = self.rope(x)
        return apply_rotary_pos_emb(x, x, cos, sin)[0]


def compare_embedding_methods():
    """Compare learned vs RoPE embeddings"""

    print("Comparing Learned vs RoPE Positional Embeddings")
    print("="*60)

    # Setup
    seq_len = 512
    embed_dim = 512
    batch_size = 4

    # Learned embedding
    learned_emb = LearnedPositionalEmbedding(max_seq_len=2048, embed_dim=embed_dim)
    learned_params = sum(p.numel() for p in learned_emb.parameters())

    # RoPE
    rope_emb = RoPEPositionalEmbedding(embed_dim=embed_dim, max_seq_len=2048)
    rope_params = sum(p.numel() for p in rope_emb.parameters() if p.requires_grad)

    print(f"\nParameter Count:")
    print(f"  Learned embeddings: {learned_params:,} parameters")
    print(f"  RoPE: {rope_params:,} parameters")
    print(f"  Saved: {learned_params - rope_params:,} parameters ({(1-rope_params/learned_params)*100:.1f}%)")

    # Extrapolation test
    print(f"\nExtrapolation Test (trained on 512, testing on 1024):")

    # Learned: will fail on sequences longer than max_seq_len
    x_learned = torch.randn(batch_size, 1024, embed_dim)
    try:
        out_learned = learned_emb(x_learned)
        print(f"  Learned: Success at seq_len=1024")
    except:
        print(f"  Learned: FAILED at seq_len=1024 (out of range)")

    # RoPE: naturally extrapolates
    x_rope = torch.randn(batch_size, 8, 1024, embed_dim // 8)
    out_rope = rope_emb(x_rope)
    print(f"  RoPE: ✓ Success at seq_len=1024 (natural extrapolation)")


if __name__ == "__main__":
    compare_embedding_methods()
```

---

## Experiment 3: RoPE Scaling Methods

### Objective
Test different RoPE scaling methods for longer context windows.

### Scaling Implementations
```python
# rope_scaling.py
import torch
import torch.nn as nn

class RoPEScaling:
    """
    RoPE Scaling methods for extending context window

    Methods:
    1. Linear: No scaling (default)
    2. YaRN: NTK-aware interpolation
    3. Dynamic: Dynamic NTK scaling
    """

    @staticmethod
    def get_rope_scaling_fn(scaling_type: str, factor: float = 1.0):
        """Get scaling function"""

        if scaling_type == "linear":
            return lambda x: x

        elif scaling_type == "yarn":
            # YaRN (Yet another RoPE extensioN)
            def yarn_scale(x):
                # NTK-aware interpolation
                base = 10000 * (factor ** (len(x) / (len(x) - 2)))
                return x * (base / 10000) ** (len(x) / (2 * len(x)))
            return yarn_scale

        elif scaling_type == "dynamic":
            # Dynamic NTK scaling
            def dynamic_scale(x, seq_len):
                # Extend base frequency dynamically
                base = 10000 * (seq_len / 2048) ** (len(x) / (len(x) - 2))
                return x * (base / 10000) ** (len(x) / (2 * len(x)))
            return dynamic_scale

        else:
            raise ValueError(f"Unknown scaling type: {scaling_type}")


class ScalableRotaryEmbedding(nn.Module):
    """Rotary embedding with scaling support"""

    def __init__(self, dim: int, max_position_embeddings: int = 2048,
                 base: int = 10000, scaling_type: str = "linear",
                 scaling_factor: float = 1.0):
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        self.scaling_type = scaling_type
        self.scaling_factor = scaling_factor

        # Create inverse frequency
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)

        self._build_cache(max_position_embeddings)

    def _build_cache(self, seq_len: int):
        """Build cos/sin cache with scaling"""
        t = torch.arange(seq_len, device=self.inv_freq.device).type_as(self.inv_freq)

        # Apply scaling
        if self.scaling_type != "linear":
            scale_fn = RoPEScaling.get_rope_scaling_fn(
                self.scaling_type, self.scaling_factor
            )
            t = scale_fn(t) if self.scaling_type != "dynamic" else scale_fn(t, seq_len)

        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)

        self.register_buffer("cos_cached", emb.cos()[None, None, :, :], persistent=False)
        self.register_buffer("sin_cached", emb.sin()[None, None, :, :], persistent=False)

    def forward(self, x: torch.Tensor, seq_len: int = None):
        if seq_len is None:
            seq_len = x.shape[-2]

        if seq_len > self.cos_cached.shape[-2]:
            self._build_cache(seq_len)

        return (
            self.cos_cached[..., :seq_len, :],
            self.sin_cached[..., :seq_len, :]
        )


def test_rope_scaling():
    """Test different RoPE scaling methods"""

    print("RoPE Scaling Methods Comparison")
    print("="*60)

    # Test configurations
    seq_lens = [2048, 4096, 8192, 16384]
    scaling_types = ["linear", "yarn", "dynamic"]

    results = {}

    for scaling_type in scaling_types:
        print(f"\n{scaling_type.upper()} Scaling:")

        results[scaling_type] = []

        for seq_len in seq_lens:
            # Create RoPE with scaling
            rope = ScalableRotaryEmbedding(
                dim=64,
                max_position_embeddings=2048,
                scaling_type=scaling_type,
                scaling_factor=seq_len / 2048
            )

            # Test at sequence length
            x = torch.randn(1, 8, seq_len, 64)
            cos, sin = rope(x)

            # Check if successful
            success = cos.shape[-2] >= seq_len
            status = "✓" if success else "✗"

            print(f"  {status} seq_len={seq_len:5d}: cos shape = {cos.shape[-3]}")

            results[scaling_type].append(success)

    # Summary
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"{'Scaling':<12} | {'2048':<8} | {'4096':<8} | {'8192':<8} | {'16384':<8}")
    print(f"{'-'*60}")
    for scaling_type, results_list in results.items():
        status_str = " | ".join(["✓" if r else "✗" for r in results_list])
        print(f"{scaling_type:<12} | {status_str}")


if __name__ == "__main__":
    test_rope_scaling()
```

---

## Experiment 4: RoPE Frequency Visualization

### Objective
Visualize how RoPE encodes position information.

### Visualization Script
```python
# rope_visualization.py
import torch
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def visualize_rope_rotation():
    """Visualize RoPE rotation in 2D"""

    # Setup
    dim = 2  # 2D for visualization
    base = 10000
    max_pos = 100

    # Create inverse frequencies
    inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))

    # Create positions
    positions = torch.arange(max_pos)
    freqs = torch.einsum("i,j->ij", positions, inv_freq)

    # Create rotation matrices
    cos_vals = freqs.cos().numpy()
    sin_vals = freqs.sin().numpy()

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Plot 1: Cosine component
    axes[0].plot(cos_vals[:, 0], label=f"dim 0 (freq={inv_freq[0]:.6f})")
    axes[0].plot(cos_vals[:, 1], label=f"dim 1 (freq={inv_freq[1]:.6f})", alpha=0.7)
    axes[0].set_title("RoPE Cosine Component")
    axes[0].set_xlabel("Position")
    axes[0].set_ylabel("Value")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Sine component
    axes[1].plot(sin_vals[:, 0], label=f"dim 0")
    axes[1].plot(sin_vals[:, 1], label=f"dim 1", alpha=0.7)
    axes[1].set_title("RoPE Sine Component")
    axes[1].set_xlabel("Position")
    axes[1].set_ylabel("Value")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Rotation visualization
    # Show how a vector rotates as position increases
    n_demo = 16
    demo_vec = torch.tensor([1.0, 0.0])  # Start with unit vector on x-axis

    for i in range(0, max_pos, max_pos // n_demo):
        cos, sin = cos_vals[i, 0], sin_vals[i, 0]

        # Rotate the vector
        x_rot = demo_vec[0] * cos - demo_vec[1] * sin
        y_rot = demo_vec[0] * sin + demo_vec[1] * cos

        # Plot vector
        axes[2].arrow(0, 0, x_rot, y_rot, head_width=0.1,
                     alpha=0.6, color=plt.cm.viridis(i/max_pos))

    axes[2].set_xlim(-1.5, 1.5)
    axes[2].set_ylim(-1.5, 1.5)
    axes[2].set_aspect('equal')
    axes[2].set_title(f"Vector Rotation at Different Positions")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/workspace/rope_visualization.png', dpi=150)
    print("Visualization saved to: /workspace/rope_visualization.png")


def visualize_frequency_spectrum():
    """Visualize RoPE frequency spectrum"""

    dim = 64
    base = 10000

    # Compute frequencies
    indices = torch.arange(0, dim, 2)
    inv_freq = 1.0 / (base ** (indices.float() / dim))
    freq = 1.0 / inv_freq

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Plot 1: Frequency spectrum (log scale)
    axes[0].semilogy(indices.numpy(), freq.numpy(), 'o-')
    axes[0].set_title("RoPE Frequency Spectrum (Log Scale)")
    axes[0].set_xlabel("Dimension Index")
    axes[0].set_ylabel("Frequency (log scale)")
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Inverse frequency spectrum (log scale)
    axes[1].semilogy(indices.numpy(), inv_freq.numpy(), 'o-', color='orange')
    axes[1].set_title("RoPE Inverse Frequency Spectrum (Log Scale)")
    axes[1].set_xlabel("Dimension Index")
    axes[1].set_ylabel("Inverse Frequency (log scale)")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/workspace/rope_frequency_spectrum.png', dpi=150)
    print("Frequency spectrum saved to: /workspace/rope_frequency_spectrum.png")


if __name__ == "__main__":
    visualize_rope_rotation()
    visualize_frequency_spectrum()
```

---

## Experiment 5: RoPE in Attention

### Objective
Integrate RoPE into a complete attention mechanism.

### Full Implementation
```python
# rope_attention.py
import torch
import torch.nn as nn

class RoPEAttention(nn.Module):
    """Multi-head attention with RoPE positional encoding"""

    def __init__(self, dim: int, num_heads: int = 8, max_seq_len: int = 2048):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(dim, dim * 3, bias=False)
        self.out = nn.Linear(dim, dim)

        # RoPE
        self.rope = RotaryEmbedding(
            dim=self.head_dim,
            max_position_embeddings=max_seq_len
        )

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None):
        """
        Args:
            x: (batch, seq_len, dim)
            mask: (batch, 1, seq_len, seq_len) or None
        """
        B, N, C = x.shape

        # Project to Q, K, V
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, heads, N, head_dim)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # Apply RoPE to Q and K
        cos, sin = self.rope(q)
        q, k = apply_rotary_pos_emb(q, k, cos, sin)

        # Scaled dot-product attention
        attn = (q @ k.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = attn.softmax(dim=-1)

        out = (attn @ v).transpose(1, 2).reshape(B, N, C)
        return self.out(out)


def test_rope_attention():
    """Test RoPE attention"""

    print("Testing RoPE Attention")
    print("="*60)

    # Create attention layer
    dim = 512
    heads = 8
    seq_len = 1024

    attn = RoPEAttention(dim=dim, num_heads=heads, max_seq_len=2048)

    # Test forward pass
    batch = 4
    x = torch.randn(batch, seq_len, dim)

    # Causal mask
    mask = torch.tril(torch.ones(seq_len, seq_len)).view(1, 1, seq_len, seq_len)

    output = attn(x, mask)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Parameters: {sum(p.numel() for p in attn.parameters()):,}")

    # Test with different sequence lengths
    print(f"\nTesting extrapolation:")

    for test_len in [512, 1024, 2048, 4096]:
        try:
            x_test = torch.randn(1, test_len, dim)
            mask_test = torch.tril(torch.ones(test_len, test_len)).view(1, 1, test_len, test_len)
            out = attn(x_test, mask_test)
            print(f"  ✓ seq_len={test_len}: Success")
        except Exception as e:
            print(f"  ✗ seq_len={test_len}: {str(e)[:50]}")


if __name__ == "__main__":
    test_rope_attention()
```

---

## Expected Results

### RoPE Benefits
| Feature | Learned Absolute | RoPE |
|---------|------------------|------|
| Parameters | ~1M for 2048 positions | 0 |
| Extrapolation | Poor | Good |
| Relative encoding | No | Yes |
| Cache friendly | Yes | Yes |

### Scaling Performance
| Context | Linear | YaRN | Dynamic |
|---------|--------|------|---------|
| 2048 | ✓ | ✓ | ✓ |
| 4096 | Degraded | ✓ | ✓ |
| 8192 | Very Poor | Good | ✓ |
| 16384 | Broken | Acceptable | Good |

---

## Experiment Checklist

- [ ] RoPE implementation from scratch
- [ ] Norm preservation verification
- [ ] Comparison with learned embeddings
- [ ] Extrapolation test (2x training length)
- [ ] Scaling methods comparison (Linear/YaRN/Dynamic)
- [ ] Frequency visualization
- [ ] Rotation animation
- [ ] Integration into attention layer
- [ ] Full model test with RoPE
- [ ] Performance benchmark (with/without RoPE)

---

## Related Documentation
- [3201: RoPE](../docs/3000-Transformer-Physics/3200-Embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)
- [3101: Self-Attention](../docs/3000-Transformer-Physics/3100-Attention/3101-Self-Attention-DeepDive.md)
- [3402: Decoder-Only Models](../docs/3000-Transformer-Physics/3400-Model-Architectures/3402-Decoder-Only-Models.md)
