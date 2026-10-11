---
Document ID: CHEAT-SHEET-021
Title: "CHEAT-SHEET-021: RoPE Positional Encoding"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rope', 'embeddings', 'attention', 'transformers']
---

# CHEAT-SHEET-021: RoPE Positional Encoding

**Quick Reference for:** the three failure modes RoPE replaces, the rotation construction, the relative-position property, the wiring discipline, the extended-context knobs, and the method ledger.

**Version:** 1.0

---

## The Three Failure Modes RoPE Replaces

Transformers are permutation invariant - `Attention("cat chases dog")` = `Attention("dog chases cat")` - so position must be injected explicitly. What each prior approach costs:

| Approach | Parameters | Where it breaks |
|---|---|---|
| Absolute (sinusoidal / learned) | 0 / d_model | added to embeddings, fails to extrapolate past trained length, no relative structure |
| Relative bias (T5) | O(L²) | learnable bias per (j−i) pair scales quadratically, complex to wire |
| **RoPE** | **0** | nothing structural - the default from LLaMA onward |

## The Rotation Construction

Rotate the query and key vectors by their position: a 2D pair `[x, y]` rotated by angle θ becomes `[x·cosθ − y·sinθ, x·sinθ + y·cosθ]`. For head_dim D the vector splits into **D/2 2D subspaces** - `(x₀,x₁)` rotates by `m·θ₀`, `(x₂,x₃)` by `m·θ₁`, ... with frequencies `inv_freq_i = 1/θ^(2i/D)`, base θ = 10000. Positions enter only through the angle `m·θ_i`. The cos/sin tables are precomputed once as an outer product of positions × frequencies and cached LLaMA-style via `register_buffer`, so every forward pass reuses them.

```python
import math

D, THETA = 8, 10000.0
inv_freq = [THETA ** (-2 * i / D) for i in range(D // 2)]
print("subspaces=%d inv_freq[0]=%.4f inv_freq[%d]=%.4e" %
      (D // 2, inv_freq[0], D // 2 - 1, inv_freq[-1]))

def rot(v, m):
    out = []
    for i in range(D // 2):
        x, y = v[2 * i], v[2 * i + 1]
        a = m * inv_freq[i]
        out += [x * math.cos(a) - y * math.sin(a),
                x * math.sin(a) + y * math.cos(a)]
    return out

def score(m, n):
    qm = rot([1.0, 0.5, -0.3, 0.8, 0.2, -0.6, 0.4, 0.9], m)
    kn = rot([0.7, -0.2, 0.5, 0.3, -0.8, 0.6, 0.1, -0.4], n)
    return sum(a * b for a, b in zip(qm, kn))

s1, s2, s3 = score(0, 3), score(5, 8), score(100, 103)
print("offset=3 scores %.12f %.12f %.12f" % (s1, s2, s3))
print("max|same-offset diff|=%.2e (relative-only)" %
      max(abs(s1 - s2), abs(s2 - s3)))
print("offset=0 vs offset=3 at (7,7): %.6f vs %.6f" % (score(7, 7), s1))

LO, LH, D2 = 2048, 8192, 64
print("PI scale 2048->8192=%.2f YaRN base-scale=%.4f" %
      (LO / LH, (LH / LO) ** (D2 / (D2 - 2))))
```

Canonical trace: `subspaces=4 inv_freq[0]=1.0000 inv_freq[3]=1.0000e-03`; `offset=3 scores -1.113810506845 -1.113810506845 -1.113810506845` - identical to 12 decimal places across positions (0,3), (5,8), (100,103), with `max|same-offset diff|=6.66e-16` the pure float64 rounding residue: the relative-only property is mathematically exact and lands at rounding noise; `(7,7)` scores -0.150000 vs -1.113811 at offset 3, so absolute position genuinely does not leak; `PI scale 2048->8192=0.25 YaRN base-scale=4.1829`.

## The Relative-Position Property

Rotating `Q_m` by `mθ` and `K_n` by `nθ` makes their dot product depend only on **(m − n)** - the rotations compose as `R(mθ)ᵀ R(nθ) = R((n−m)θ)`. Consequences the fence proves: same relative offset → same attention score at any absolute location; the score generalizes to longer sequences; and **zero parameters are added**. The implementation form is `q_embed = q·cos + rotate_half(q)·sin` where `rotate_half` returns `[-x₂, x₁]` - the complex-multiplication trick written with real tensors.

## Wiring Discipline

Rotate **Q and K only** - after the projection and head split, **before** the score matmul. V is never rotated: V's job is to be mixed by attention weights, and rotating it would corrupt the value combination while leaving the scores (which only see Q·K) perfectly healthy - the silent-wrong-output failure. `head_dim` must be even for the subspace split.

## Extended Context

| Method | Recipe | Trade-off |
|---|---|---|
| Position Interpolation (PI) | use `m′ = m·L_orig/L_new` (2048→8192 = 0.25) | training-free but compresses high-frequency rotations; small fine-tune recovers |
| NTK-aware / YaRN | scale the base: `scale = (L_new/L_orig)^(D/(D−2))`, θ·scale = 10000·4.1829 ≈ 41829 at 4x | keeps high frequencies intact, better training-free quality |
| Sliding window (Mistral) | cap attention per token | constant memory, loses beyond-window tokens (see CHEAT-SHEET-017) |

## Method Ledger

| Method | Parameters | O(n) Extend | Relative | Complexity |
|---|---|---|---|---|
| Absolute Sinusoidal | 0 | ✗ | ✗ | Low |
| Learned Absolute | d_model | ✗ | ✗ | Low |
| Relative Bias | O(L²) | ~ | ✓ | High |
| ALiBi | 0 | ✓ | ✓ | Low |
| RoPE | 0 | ✓ | ✓ | Medium |

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| outputs ignore word order | Q/K never rotated | apply `apply_rotary_pos_emb` to Q and K before the score matmul |
| index error past trained length | cos/sin cache shorter than sequence | slice `cos[:seq_len]` only up to the cached max; extend via PI/YaRN |
| scores fine, outputs garbage | V was rotated too | rotate Q and K only - never V |
| quality collapses after PI to 8192 | high-frequency rotations compressed 4x | brief fine-tune, or YaRN base-scaling instead |
| odd-dim assert at load | `head_dim` not divisible by 2 | the D/2 subspace split requires even head_dim |
| degraded long-context quality after base swap | wrong `rope_theta` vs checkpoint's config | load-time base must match training-time base unless deliberately extending |

## Quick Reference For

- [Module 3201: Rotary Positional Embeddings (RoPE)](../../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)
- [Module 3101: Self-Attention DeepDive](../../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)
- [Module 4201: Context Window Physics](../../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [CHEAT-SHEET-020: Flash Attention](./CHEAT-SHEET-020-Flash-Attention.md)
