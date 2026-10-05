---
Document ID: EXP_3101
Title: "EXP_3101_ATTENTION: Self-Attention Deep Dive"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# EXP_3101_ATTENTION: Self-Attention Deep Dive

## Experiment Information
- **Model:** Custom multi-head attention
- **Sequence Length:** 512
- **Heads:** 8
- **Head Dim:** 64

## Experiment: Visualization of Attention Patterns

### Setup
```python
import torch
import seaborn as sns

# Random input
batch_size = 1
seq_len = 20
d_model = 512
num_heads = 8

Q = torch.randn(batch_size, num_heads, seq_len, d_model // num_heads)
K = torch.randn(batch_size, num_heads, seq_len, d_model // num_heads)
V = torch.randn(batch_size, num_heads, seq_len, d_model // num_heads)
```

### Attention Patterns (illustrative)

The random init above cannot show structure: with Q, K and V drawn from
`torch.randn`, the softmax weights come out near uniform. The maps below
are the classic illustrative picture of what a TRAINED model's heads
develop - some specialize locally, others attend globally.

```text
Head 0: Local attention pattern
  ┌───────────────────────────────────────────────────┐
  │     Tokens →                                     │
  │ T    ▓▓▓░░░░░░░░░░                                │
  │ o    ░░░░▓▓▓▓▓░░░░                                │
  │ k    ░░░░░░░░░▓▓▓▓                                │
  │ e    ░░░░░░░░░░░░▓▓                                │
  │ n    ░░░░░░░░░░░░░░▓▓                              │
  │ s    ░░░░░░░░░░░░░░░░░▓                           │
  │ ↓    ░░░░░░░░░░░░░░░░░░▓▓                         │
  └───────────────────────────────────────────────────┘

Head 3: Global attention pattern
  ┌───────────────────────────────────────────────────┐
  │     Tokens →                                     │
  │ T    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                         │
  │ o    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                         │
  │ k    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                         │
  │ e    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                         │
  │ n    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                         │
  │ s    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                         │
  │ ↓    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                         │
  └───────────────────────────────────────────────────┘
```

## Observations (trained models)
1. Different heads learn different patterns
2. Some heads focus on local, others on global
3. This diversity improves model capacity

## Performance Comparison (representative figures)
Order-of-magnitude figures for a 512-token forward pass on one consumer
GPU - exact numbers depend on hardware, batch size and sequence length.
```text
Implementation           Time (ms)  Memory (MB)
───────────────────────────────────────────────────
Naive (no optimization)    45.2      1200
Flash Attention           18.1      850
Scaled Dot Product         28.5      950

Flash Attention: 2.5x speedup, 30% memory reduction
```

## Lessons Learned
- Attention visualization reveals model behavior
- Flash Attention is essential for long sequences
- Multi-head provides diverse representations

## Related Files
- [3101-Self-Attention-DeepDive.md](../docs/phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)
- [3102-Flash-Attention.md](../docs/phases/phase3-transformers/3100-attention/3102-Flash-Attention.md)
