---
Document ID: 3102
Title: Flash Attention - IO-Aware Exact Attention
Phase: 3
Module: 3100
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'attention', 'self-attention', 'flash-attention']
---

# 3102: Flash Attention - IO-Aware Exact Attention

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Problem with Standard Attention](#the-problem-with-standard-attention)
- [Flash Attention Algorithm](#flash-attention-algorithm)
- [Flash Attention 2](#flash-attention-2)
- [Using Flash Attention](#using-flash-attention)
- [Performance Comparison](#performance-comparison)
- [Implementation Details](#implementation-details)
- [Limitations and Considerations](#limitations-and-considerations)
- [Flash Attention 3](#flash-attention-3)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain The Problem with Standard Attention
- Explain Flash Attention Algorithm
- Explain Flash Attention 2
- Explain Using Flash Attention
- Compare Performance Comparison
- Apply Implementation Details

---

## Abstract
Flash Attention is a reorganization of the attention computation that reduces memory IO (input/output) from quadratic to linear. It's exact (not approximate), faster, and uses less memory.

## The Problem with Standard Attention

### Memory Access Pattern
```python
# Standard attention (as in PyTorch)
def standard_attention(Q, K, V):
    # Q, K, V: (B, H, L, D)
    B, H, L, D = Q.shape

    # 1. Compute S = Q @ K^T  →  O(L²) memory reads/writes
    S = torch.matmul(Q, K.transpose(-2, -1)) / (D ** 0.5)

    # 2. Compute P = softmax(S)  →  O(L²) memory for attention matrix
    P = torch.softmax(S, dim=-1)

    # 3. Compute O = P @ V  →  O(L²) memory reads
    O = torch.matmul(P, V)

    return O

# Total HBM (High Bandwidth Memory) access:
# - Read Q, K, V: 3 × B × H × L × D
# - Write S: B × H × L × L
# - Read S, write P: 2 × B × H × L × L
# - Read P, V: B × H × L × L + B × H × L × D
# Total: O(L²) HBM accesses
```

### Memory Bandwidth Bottleneck
```text
GPU Memory Hierarchy Speed Comparison:
HBM (GPU VRAM):    ~600 GB/s
SRAM (On-chip):    ~30 TB/s (50x faster!)

Standard attention:
- Loads entire attention matrix to HBM
- Multiple reads/writes to slow HBM

Flash attention:
- Keeps attention matrix in fast SRAM
- Tiled computation minimizes HBM access
```

## Flash Attention Algorithm

### Key Ideas
```text
1. Tiling: Split Q, K, V into blocks
2. Incremental softmax: Update softmax statistics online
3. No materialization: Never store full attention matrix
```

### Incremental Softmax
```python
def incremental_softmax(new_block, running_max, running_sum):
    """
    Update softmax statistics without seeing all data at once
    """
    # new_block: (block_size, block_size)
    # running_max, running_sum: scalar statistics

    # Update max
    new_max = torch.maximum(running_max, new_block.max(dim=-1, keepdim=True).values)

    # Update sum with new scaling
    correction = torch.exp(running_max - new_max)
    new_sum = running_sum * correction + torch.exp(new_block - new_max).sum(dim=-1, keepdim=True)

    return new_max, new_sum
```

### Flash Attention Pseudocode
```python
def flash_attention(Q, K, V, block_size=16):
    """
    Flash Attention: IO-aware exact attention
    """
    B, H, L, D = Q.shape
    O = torch.zeros_like(Q)

    # Initialize output statistics
    running_max = torch.full((B, H, L, 1), -float('inf'))
    running_sum = torch.full((B, H, L, 1), 0.0)

    # Loop over key blocks
    for j in range(0, L, block_size):
        K_block = K[:, :, j:j+block_size, :]  # Load to SRAM
        V_block = V[:, :, j:j+block_size, :]  # Load to SRAM

        # Loop over query blocks
        for i in range(0, L, block_size):
            Q_block = Q[:, :, i:i+block_size, :]  # Load to SRAM

            # Compute attention scores (in SRAM!)
            S_block = torch.matmul(Q_block, K_block.transpose(-2, -1)) / (D ** 0.5)

            # Update running statistics
            new_max = torch.maximum(running_max[:, :, i:i+block_size, :], S_block.max(dim=-1, keepdim=True).values)

            old_scale = torch.exp(running_max[:, :, i:i+block_size, :] - new_max)
            new_scale = torch.exp(S_block - new_max)

            running_sum[:, :, i:i+block_size, :] = running_sum[:, :, i:i+block_size, :] * old_scale + new_scale.sum(dim=-1, keepdim=True)
            running_max[:, :, i:i+block_size, :] = new_max

            # Update output (in SRAM!)
            O_block = O[:, :, i:i+block_size, :]
            O[:, :, i:i+block_size, :] = old_scale * O_block + torch.matmul(new_scale / running_sum[:, :, i:i+block_size, :], V_block)

    return O
```

## Flash Attention 2

### Improvements over Flash Attention 1
```text
Flash Attention 1:
- Better algorithm, but not fully optimized
- Used shared memory inefficiently

Flash Attention 2:
- Better work partitioning
- Reduced non-matmul FLOPs
- Optimized for specific GPU architectures
- 2x faster than FA1 on A100
```

### Algorithm Differences
```python
# FA1: Loop order (Q, K, V) blocks
for Q_block in Q_blocks:
    for K_block in K_blocks:
        compute_attention(Q_block, K_block, V_block)

# FA2: Loop order optimized for GPU
for K_block in K_blocks:
    for Q_block in Q_blocks:
        # Better memory access pattern
        # Maximizes L2 cache reuse
        compute_attention(Q_block, K_block, V_block)
```

## Using Flash Attention

### Via xFormers (Meta's library)
```bash
uv pip install xformers
```

```python
import torch
from xformers.ops import memory_efficient_attention

# Drop-in replacement for standard attention
Q = torch.randn(1, 8, 1024, 64, device='cuda')
K = torch.randn(1, 8, 1024, 64, device='cuda')
V = torch.randn(1, 8, 1024, 64, device='cuda')

# Flash attention
O = memory_efficient_attention(Q, K, V)

# With causal mask
mask = torch.tril(torch.ones(1024, 1024, device='cuda'))
O = memory_efficient_attention(Q, K, V, attn_bias=mask)
```

### Via Flash Attention Library
```bash
uv pip install flash-attn
```

```python
from flash_attn import flash_attn_func

# Flash attention with causal mask
Q = torch.randn(1, 128, 1024, 64, device='cuda')  # (batch, heads, seq, dim)
K = torch.randn(1, 128, 1024, 64, device='cuda')
V = torch.randn(1, 128, 1024, 64, device='cuda')

# causal=True for autoregressive
O = flash_attn_func(Q, K, V, causal=True)

# No softmax output (not materialized)
# Much faster and less memory!
```

### In Transformers (HuggingFace)
```python
from transformers import AutoModelForCausalLM

# Models using Flash Attention
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    attn_implementation="flash_attention_2",
    torch_dtype=torch.float16,
    device_map="auto"
)

# Uses Flash Attention 2 automatically!
```

## Performance Comparison

### Benchmarks (A100 GPU, sequence length 2048)
```text
Attention Type    Time (ms)   Memory (GB)
────────────────────────────────────────
Standard          45          16.0
Memory-Efficient  28          8.0
Flash Attn 1      18          4.5
Flash Attn 2      12          3.2

Speedup: 3.75x faster than standard
Memory: 5x less memory usage
```

### Sequence Length Scaling
```text
Standard Attention:
  Time: O(L²) - doubles when L × √2
  Memory: O(L²) - doubles when L × √2

Flash Attention:
  Time: O(L²) - but 3-4x faster constant
  Memory: O(L) - linear!

For L = 8192:
  Standard: 16GB (VRAM limit for an 11GB-class GPU)
  Flash: 4GB (can handle much longer!)
```

## Implementation Details

### Block Size Selection
```python
# Optimal block size depends on GPU
# For an 11GB VRAM GPU (Turing):
# - Shared memory: 48KB per SM
# - L2 cache: 5.5MB

import torch

def get_optimal_block_size():
    """
    Calculate optimal block size for Flash Attention
    """
    # Get GPU properties
    device = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(device)

    # Shared memory per SM
    shared_mem_per_sm = 48 * 1024  # 48KB for Turing

    # Each block needs: Q (B×H×B_r×D) + K (B×H×B_c×D) + ...
    # Estimate: ~3 × B_r × B_c × D bytes

    # For D = 64, B_r = B_c = 64:
    # Memory: 3 × 64 × 64 × 64 × 2 bytes (fp16) ≈ 1.5MB

    # Optimal: 128 for most cases
    return 128

BLOCK_SIZE = get_optimal_block_size()
```

### Half Precision (FP16/BF16)
```python
# Flash Attention requires half precision
Q = Q.to(torch.float16)
K = K.to(torch.float16)
V = V.to(torch.float16)

# Or bfloat16 (better for training)
Q = Q.to(torch.bfloat16)

# FP16 benefits:
# - 2x less memory
# - Faster compute (Tensor Cores)
# - Sufficient for inference
```

## Limitations and Considerations

### When NOT to use Flash Attention
```text
1. Very short sequences (< 512):
   - Overhead of tiling outweighs benefits
   - Standard attention is fine

2. Need attention weights:
   - Flash doesn't materialize attention matrix
   - Use standard attention or compute separately

3. CPU inference:
   - Flash is GPU-only
   - Standard attention on CPU

4. Perplexity calculation:
   - Need exact softmax values
   - Can compute separately if needed
```

### Computing Attention Weights
```python
def get_attention_weights(Q, K, V):
    """
    Compute attention weights separately if needed
    Uses more memory but gives exact values
    """
    # Compute output with Flash
    O = flash_attn_func(Q, K, V)

    # Compute attention separately if needed
    with torch.no_grad():
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (Q.size(-1) ** 0.5)
        attn_weights = torch.softmax(scores, dim=-1)

    return O, attn_weights
```

## Flash Attention 3

### Hardware-Aware Optimization
```text
Flash Attention 3 (2024):
- Optimized for Hopper (H100) architecture
- Hardware-specific tiling
- Tensor Core optimizations
- Up to 2x faster than FA2 on H100

Key insight:
- Different optimal block sizes for different GPUs
- FA3: H100 optimized
- FA2: A100, V100 optimized
- FA1: General purpose
```

---

## References

### Related ai-engineering-curriculum Documents

- [3101: Self-Attention Deep Dive](3101-Self-Attention-DeepDive.md)

---

## Next Steps

- Next Module: **[3200: Embeddings](../3200-embeddings/)**
- Continue with: **[3201: RoPE](../3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [3101: Self-Attention](./3101-Self-Attention-DeepDive.md)
- [4201: Context Window](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [2203: CUDA Kernels](../../phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Programming.md)

**Experiment Template:** [EXP_3102: Flash Attention](../../../../experiments/EXP_3102_FLASH_ATTENTION.md)
