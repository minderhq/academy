---
Document ID: CHEAT-SHEET-020
Title: "CHEAT-SHEET-020: Flash Attention"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'attention', 'flash-attention', 'gpu', 'transformers']
---

# CHEAT-SHEET-020: Flash Attention

**Quick Reference for:** the memory-hierarchy argument, the online-softmax block update, the FA1 → FA2 → FA3 ladder, the three enablement paths, the benchmark bill, and the when-not-to rules.

**Version:** 1.0

---

## The Memory Hierarchy Argument

Attention is bandwidth-bound, not FLOP-bound. The gap that decides it:

| Tier | Bandwidth | Role in attention |
|---|---|---|
| HBM (VRAM) | ~600 GB/s | where Q, K, V, S, P live in standard attention |
| SRAM (on-chip) | ~30 TB/s | where Flash keeps S and P alive, 50x faster |

Standard attention materializes `S = Q@K^T` and `P = softmax(S)`: that alone is **4·L²** extra HBM round-trips (write S, read S, write P, read P) on top of the 4·L·D of Q/K/V traffic. Flash never lets S and P touch HBM - the working set stays tiled in SRAM, cutting memory IO from quadratic to linear. Module 3102's closing rule: **memory bandwidth, not FLOPs, is usually the attention ceiling - and IO-aware algorithm design is how the ceiling moves**.

## The Online Softmax Block Update

Three running statistics per query row - running max `m`, running sum `ℓ`, running (unnormalized) output `O` - updated one key-block at a time:

```python
import math

BENCH = [("Standard", 45.0, 16.0), ("Memory-Efficient", 28.0, 8.0),
         ("Flash Attn 1", 18.0, 4.5), ("Flash Attn 2", 12.0, 3.2)]
print("A100@2048 speedup %.2fx memory %.1fx" %
      (BENCH[0][1] / BENCH[-1][1], BENCH[0][2] / BENCH[-1][2]))
std, fl = 4 * 2048 * 64 + 4 * 2048 ** 2, 3 * 2048 * 64
print("HBM units: standard=%d flash=%d ratio=%.1fx" % (std, fl, std / fl))

L, D, BS = 6, 2, 2
Q = [[0.5 * i, 1.0 - 0.2 * i] for i in range(L)]
K = [[0.3 + 0.1 * j, 0.7 - 0.05 * j] for j in range(L)]
V = [[1.0 + j, 2.0 - 0.5 * j] for j in range(L)]
scale = math.sqrt(D)
O_ref = []
for q in Q:
    s = [sum(a * b for a, b in zip(q, k)) / scale for k in K]
    p = [math.exp(x - max(s)) for x in s]
    z = sum(p)
    O_ref.append([sum(p[t] * V[t][d] for t in range(L)) / z for d in range(D)])
O, run_m, run_l = [[0.0] * D for _ in range(L)], [-math.inf] * L, [0.0] * L
for j0 in range(0, L, BS):
    Kb, Vb = K[j0:j0 + BS], V[j0:j0 + BS]
    for i0 in range(0, L, BS):
        for i in range(i0, i0 + BS):
            s = [sum(Q[i][d] * k[d] for d in range(D)) / scale for k in Kb]
            new_m = max(run_m[i], max(s))
            old = math.exp(run_m[i] - new_m)
            p = [math.exp(x - new_m) for x in s]
            run_l[i] = run_l[i] * old + sum(p)
            for d in range(D):
                O[i][d] = old * O[i][d] + sum(p[t] * Vb[t][d] for t in range(BS))
            run_m[i] = new_m
diff = max(abs(O[i][d] / run_l[i] - O_ref[i][d]) for i in range(L) for d in range(D))
print("online softmax vs plain softmax: max|diff|=%.2e (exact)" % diff)
```

Canonical trace: `A100@2048 speedup 3.75x memory 5.0x`; `HBM units: standard=17301504 flash=393216 ratio=44.0x` (that is `(4·L·D + 4·L²) / 3·L·D` at L=2048, D=64); `max|diff|=4.44e-16` - the block-update loop lands on plain softmax to float64 rounding. The three mechanics to remember: `new_m = max(m, block_max)`; the **rescaling correction** `exp(m_old − m_new)` multiplies both `ℓ` and `O` when a block raises the max; probabilities are accumulated **unnormalized**, with the single division by the final `ℓ` at the end.

## FA1 → FA2 → FA3

| Version | Target hardware | What changed | Gain |
|---|---|---|---|
| FA1 | general purpose | tiling + online softmax; S, P never materialized | 45 → 18 ms (A100, L=2048) |
| FA2 | A100 / V100 | K-outer/Q-inner loop swap, fewer non-matmul FLOPs, better work partitioning | ~2x over FA1 (18 → 12 ms) |
| FA3 | Hopper (H100) | Hopper-specific tiling, Tensor Core optimizations | up to 2x over FA2 on H100 |

## The Benchmark Bill (A100, L = 2048)

| Attention Type | Time (ms) | Memory (GB) |
|---|---|---|
| Standard | 45 | 16.0 |
| Memory-Efficient | 28 | 8.0 |
| Flash Attn 1 | 18 | 4.5 |
| Flash Attn 2 | 12 | 3.2 |

**3.75x faster, 5x less memory than standard.** Scaling is the real story: standard memory is O(L²) and doubles whenever L grows by √2, while Flash stays O(L) with a 3-4x faster constant. At L = 8192 standard attention needs 16 GB (OOM on an 11 GB-class GPU); Flash handles the same length in 4 GB.

## Three Ways to Enable

| Path | Code | Constraint |
|---|---|---|
| xFormers | `memory_efficient_attention(Q, K, V)` | causal needs `attn_bias=mask` (e.g. `torch.tril`) |
| flash-attn lib | `flash_attn_func(Q, K, V, causal=True)` | tensors shaped `(batch, heads, seq, dim)` |
| Hugging Face | `attn_implementation="flash_attention_2"` in `from_pretrained` | requires `dtype=torch.float16` (or bfloat16) |

## When NOT to Use Flash

1. **Very short sequences (< 512)** - tiling overhead outweighs the HBM savings; standard attention is fine.
2. **You need attention weights** - S/P are never materialized; compute standard attention separately for inspection.
3. **CPU inference** - Flash is GPU-only.

## Sizing and Precision

Shared memory per SM is 48 KB on Turing-class parts; with head_dim D = 64 the canonical tile lands near **block ≈ 128**. Inputs must be cast to **FP16/BF16** - Flash requires half precision (2x less memory, Tensor Core compute; bf16 preferred for training).

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| `attn_implementation="flash_attention_2"` raises at load | Flash requires half precision | pass `dtype=torch.float16` (or `torch.bfloat16`) to `from_pretrained` |
| attention map / visualization gone | S and P are never materialized | run standard attention separately when you need the weights |
| short sequence (≤ 512) got slower | tiling overhead exceeds the HBM savings | standard attention is fine below ~512 tokens |
| CPU inference fails on flash kernels | Flash is GPU-only | use standard attention on CPU |
| xFormers output is not causal | mask not passed | give `memory_efficient_attention` an `attn_bias` (e.g. `torch.tril(ones(L, L))`) |
| 11 GB card OOMs at L = 8192 on standard | the 4·L² bill (16 GB) | the Flash path holds the same length in 4 GB (linear) |

## Quick Reference For

- [Module 3102: Flash Attention](../../phases/phase3-transformers/3100-attention/3102-Flash-Attention.md)
- [Module 3101: Self-Attention DeepDive](../../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)
- [Module 4201: Context Window Physics](../../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [CHEAT-SHEET-019: Tokenizers](./CHEAT-SHEET-019-Tokenizers.md)
