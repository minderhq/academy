---
Document ID: CHEAT-SHEET-035
Title: "CHEAT-SHEET-035: Beyond Attention - SSMs and MLA"
Last Updated: 2026-10-23
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'ssm', 'mla', 'transformers']
---

# CHEAT-SHEET-035: Beyond Attention - SSMs and MLA

**Quick Reference for:** the two costs attention pays (O(L^2) scores and a KV cache that grows with context), the fixed-state SSM recurrence with its ZOH discretization, Mamba's selectivity gate where delta_t decides write versus forget, Mamba-2's SSD trade (scalar-times-identity in exchange for chunked-matmul training), the honest recall weakness that makes every production model a hybrid, the six-model hybrid landscape, and MLA - DeepSeek's compressed cache that carries a token in 576 elements where full MHA carries 32,768 (56.9x, 122.0 GB versus 2.14 GB at a 32k context on the published V3 dims). CHEAT-SHEET-020 attacks attention's compute constant and CHEAT-SHEET-021 its position scheme; this sheet owns the two architectures that attack its shape. The closing rule: choose by failure mode, not benchmark average - the recall row is why pure-attention models are not going away, and the hybrid is why pure attention is no longer the whole story.

## The Two Costs Attention Pays

A Transformer block mixes across the sequence (attention) and transforms per-position (the MLP). The mixing cost has two parts:

1. **Compute:** the score matrix is L x L - doubling the context quadruples the attention FLOPs. FlashAttention (CHEAT-SHEET-020) shrinks the constant, never the quadratic shape.
2. **State:** autoregressive inference caches K and V for every past token at every layer - linear in context and in heads x head_dim. At long context the cache, not the weights, owns the memory budget.

Post-Transformer architectures attack the shape itself: SSMs replace the pairwise score matrix with a fixed-size recurrent state (linear time, constant inference memory), and MLA keeps softmax attention but proves the cache can be far smaller than 2 x heads x head_dim.

## The Fixed-State Mixer: The SSM Recurrence

The continuous recurrence `h'(t) = A h(t) + B x(t)`, `y(t) = C h(t) + D x(t)` discretizes under zero-order-hold into a plain linear recurrence over token positions:

```text
A_bar = exp(delta * A)     B_bar ~= (delta * A) * B     (first-order ZOH step)
h_t   = A_bar * h_{t-1} + B_bar * x_t
y_t   = C * h_t + D * x_t
```

Two properties matter more than the algebra: **linear time** (L fixed-shape updates instead of O(L^2) scores - at d_model=4, d_state=8 the scan costs L x 32 state ops against L^2 x 4 attention ops, a ratio that runs 4.0x at L=32, 16.0x at L=128, 64.0x at L=512) and **constant inference memory** (the per-layer "cache" is one h of shape d_model x N - it never grows with context; negative-real-eigenvalue initialization keeps the state exponentially stable). Language models use state expansion N in [16, 256].

## Selectivity: The Mamba Recipe

Mamba makes the transition input-dependent - the model decides per token how much to write and how much to forget. `B_t = Linear(x_t)` (what to write), `C_t = Linear(x_t)` (what to read out), and `delta_t = softplus(Linear(x_t))` - the discretization step as a forget gate:

| delta_t | A_bar = exp(delta_t * A) | behavior |
|---|---|---|
| small (0.01) | 0.9925 | state persists across many tokens - write |
| moderate (0.1) | 0.9277 | still persisting, slower decay |
| large (2.0) | 0.2231 | state resets - the model ignores the token |

A time-invariant SSM can only average; a selective one can gate. The cost: a data-dependent recurrence is neither a convolution nor a dense matmul - it runs as a hardware-aware parallel scan, fused into one CUDA call in the `mamba-ssm` package (CUDA-only; the production kernel takes batch x dim x length shaped u, delta, B, C and a SiLU-gated branch z).

## Mamba-2: The SSD Trade

Mamba-2 restricts the state matrix to a scalar times identity - one decay scalar per token, broadcast over N. That restriction (the State Space Duality framework) gives the recurrence a dual form: unrolled, the readouts collapse into a semiseparable matrix computable with chunked matmuls in parallel over sequence blocks - 2-8x faster training than Mamba-1's general scan at comparable quality, and room for larger N. It is the same reorganization-for-the-memory-hierarchy trade as FlashAttention, applied to the SSM recurrence. The restriction is the tell: `ssm_cfg: {layer: Mamba2}` in a released config means the scalar form.

## The Honest Weakness: Recall and Copying

A fixed-size state is a lossy compression of history, and the loss is not uniform: tasks needing exact retrieval of an early token - associative recall (MQAR), induction-style copying - degrade sharply as sequence grows, while attention, which keeps every token, does not. The Mamba paper reports the copying gap itself. Averaged benchmarks hide recall cliffs; evaluate recall explicitly.

## Hybrids: The Production Answer

Production does not choose - it interleaves a few full-attention layers (the exact-recall scratchpad) among fixed-state layers (the bulk of sequence mixing):

| model | lab | recipe |
|---|---|---|
| Jamba | AI21 | Mamba-Transformer MoE, 52B total / 12B active |
| Zamba2 | Zyphra | shared-attention-block Mamba hybrid |
| Nemotron-H | NVIDIA | Mamba-2 hybrid, ~3x decode throughput vs equal-size Transformer |
| Granite 4.0 | IBM | Mamba-2 + MoE (Bamba): 4 full-attention layers among 40 |
| Qwen3-Next 80B-A3B | Alibaba | Gated DeltaNet (linear attention) in 3 of 4 layers, gated full attention in 1 of 4 |
| Kimi Linear | Moonshot AI | Gated DeltaNet interleaved with full attention |

Qwen3-Next and Kimi Linear pick a different linear mixer (gated delta-rule attention), but the architectural pattern is identical: fixed state for cost, a few attention layers retained because of the recall row.

## MLA: The Compressed Cache

MLA attacks attention's other cost. DeepSeek's observation: K and V across heads are highly redundant, so cache the latent they were generated from. Each token is down-projected once - `c_kv = W_DKV h_t` (7168 -> 512) and a shared positional rope key `k_pe = W_KR h_t` (7168 -> 64) - and the cache holds exactly `(c_kv, k_pe)`, 576 elements per token per layer. The 128 heads' worth of K and V are up-projected from the latent at use time; two details make it work:

- **Decoupled RoPE.** RoPE is position-dependent and cannot fold into the up-projection, so the rope component rides a dedicated shared `k_pe`, concatenated per head: the key is 128 + 64 = 192 wide.
- **Absorption.** Because `k_nope = W_UK c_kv` and the score is `q . k_nope`, absorb `W_UK` into the query projection and score against the cached latent directly - the up-projection never runs on decode, and the value side absorbs symmetrically. Without absorption MLA would trade cache for compute.

## The Cache Arithmetic

Straight from DeepSeek-V3's published config (`hidden 7168`, 128 heads, `qk_nope_head_dim 128`, `qk_rope_head_dim 64`, `kv_lora_rank 512`, 61 layers), per token per layer:

| surface | elements/token/layer | 32k context, bf16, 61 layers |
|---|---:|---:|
| full MHA (2 x 128 x 128) | 32,768 | 122.0 GB |
| GQA-8 (2 x 8 x 128) | 2,048 | 7.6 GB |
| MLA (512 latent + 64 rope key) | 576 | 2.14 GB |

**56.9x smaller than MHA** - architecture, not tuning; and **3.6x below GQA-8** without sacrificing key-value expressiveness (every head still gets a distinct value). This is why every long-context DeepSeek release trains with MLA and why vLLM and SGLang grew MLA-specific cache layouts.

## Choosing: SSM vs MLA vs Full Attention

| axis | Full MHA/GQA | MLA | SSM (Mamba-2) |
|---|---|---|---|
| Training compute | O(L^2) | O(L^2) | O(L) |
| Per-token cache | 2 x heads x head_dim | kv_lora_rank + rope_dim | O(1) fixed state |
| Exact recall of early tokens | Best | Best | Weakest (lossy state) |
| Long-context decode memory | Worst | Good | Best |
| Ecosystem maturity | Universal | DeepSeek lineage, major serving engines | Hybrids in production; kernels CUDA-only |
| When to pick | recall-critical, short/medium context | long-context quality at attention-grade recall | throughput-critical streaming, very long context |

## Known Failure Modes

| failure | lesson |
|---|---|
| Judge an SSM by average perplexity | perplexity matches attention while needle-style QA fails - recall is the hidden casualty; evaluate MQAR-style explicitly |
| Feed `selective_scan_fn` a CPU tensor | the kernel is CUDA-only - a CPU tensor reaches the kernel and crashes with a CUDA error |
| Build `mamba-ssm` from source on install | it compiles CUDA extensions and needs a matching toolchain - use a prebuilt wheel or pin a released version |
| Compute an MLA budget as 2 x heads x head_dim | reading `num_key_value_heads` off a DeepSeek config assumes MHA layout - derive from kv_lora_rank + qk_rope_head_dim; the KV-head fields are vestigial |
| Apply RoPE to the latent before caching | the latent is shared across positions and must be cached raw - rope the dedicated k_pe component, or absorb on the query side |
| Call Mamba-2 "the same thing" as Mamba-1 | SSD's chunked-matmul form exists only because of the scalar-times-identity restriction - general scan and SSD are different kernels for different A shapes |

## References

- Repository, *Module 3404: Beyond Attention - SSMs and MLA - the full lesson with runnable SSM and MLA fences*
- Gu & Dao, 2023, *Mamba: Linear-Time Sequence Modeling with Selective State Spaces* - the selective scan and the copying weakness
- Dao & Gu, 2024, *Transformers are SSMs* - State Space Duality and the scalar-times-identity form
- Arora et al., 2023, *Zoology* - MQAR and the recall gap for fixed-state models
- DeepSeek-AI, 2024, *DeepSeek-V2 / V3 Technical Reports* - MLA: latent cache, decoupled RoPE, absorption
- Repository, *CHEAT-SHEET-017: KV Cache* - the cache-side toolbox that applies to whatever mixer you kept

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Clean perplexity, failing needle QA | fixed state cannot hold exact early tokens | recall stress test; prefer a hybrid for retrieval workloads |
| CUDA error from the selective scan | CPU tensor or CPU-only build | keep every tensor on cuda; use the toy scan on CPU |
| mamba-ssm install fails compiling | CUDA-extension toolchain mismatch | prebuilt wheel or pin to a released version |
| MLA cache budget wildly too large | MHA formula applied to a latent-cache config | derive from kv_lora_rank + qk_rope_head_dim |
| Quality drop after caching with RoPE | rotated latent cached positionally | cache the raw latent; rope k_pe only |
| Mamba-2 speedup fails to reproduce | benchmarking the wrong A shape | state the scalar-times-identity restriction; compare like kernels |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 3404: Beyond Attention - SSMs and MLA](../../phases/phase3-transformers/3400-architectures/3404-Beyond-Attention-SSMs-and-MLA.md) | this sheet's source module - the full SSM and MLA lesson with runnable fences |
| [Module 3402: Decoder-Only Models (GPT, LLaMA, Mistral)](../../phases/phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md) | the canonical architecture this sheet's alternatives compete with |
| [CHEAT-SHEET-020: Flash Attention](CHEAT-SHEET-020-Flash-Attention.md) | attacks attention's compute constant - same memory-hierarchy argument as SSD |
| [CHEAT-SHEET-021: RoPE Positional Encoding](CHEAT-SHEET-021-RoPE-Positional-Encoding.md) | the position scheme behind MLA's decoupled rope key |

```python
"""CHEAT-SHEET-035 canonical numbers - stdlib only, deterministic."""
import math

print("F1  Fixed-state vs attention: the ops shape (d_model=4, d_state=8)")
D, N = 4, 8
for L in (32, 128, 512):
    state_ops = L * D * N          # one fixed-shape update per token
    attn_ops = L * L * D           # the pairwise score matrix
    print(f"    L={L:4d}  scan state ops {state_ops:7d}   attention ops"
          f" {attn_ops:8d}   ratio {attn_ops / state_ops:5.1f}x")
print("    state shape stays (4, 8) at every L - it never grows with context")

print()
print("F2  ZOH discretization and the selectivity gate (one channel, A = -0.75)")
A_CH = -0.75
for delta in (0.01, 0.1, 2.0):
    a_bar = math.exp(delta * A_CH)
    if a_bar > 0.9:
        gate = "state persists across many tokens (write)"
    elif a_bar > 0.5:
        gate = "moderate decay"
    else:
        gate = "state resets - the model ignores the token (forget)"
    print(f"    delta={delta:4.2f}  A_bar=exp({delta * A_CH:+.4f})={a_bar:.4f}  {gate}")

print()
print("F3  The MLA cache arithmetic (DeepSeek-V3 published dims)")
cfg = dict(n_layers=61, num_heads=128, qk_nope_head_dim=128,
           qk_rope_head_dim=64, kv_lora_rank=512)
ctx, dtype_bytes = 32768, 2  # bf16
mha_elems = 2 * cfg["num_heads"] * cfg["qk_nope_head_dim"]
mla_elems = cfg["kv_lora_rank"] + cfg["qk_rope_head_dim"]
gqa_elems = 2 * 8 * cfg["qk_nope_head_dim"]          # GQA with 8 KV heads
mha_gb = mha_elems * dtype_bytes * ctx * cfg["n_layers"] / 1024**3
mla_gb = mla_elems * dtype_bytes * ctx * cfg["n_layers"] / 1024**3
print(f"    per token per layer: MHA {mha_elems} elems, MLA {mla_elems}"
      f" (512 latent + 64 rope key), GQA-8 {gqa_elems} elems")
print(f"    32k-context KV cache: MHA {mha_gb:.1f} GB, MLA {mla_gb:.2f} GB"
      f" -> {mha_elems / mla_elems:.1f}x smaller")
print(f"    MLA is {gqa_elems / mla_elems:.1f}x below GQA-8 - without shared heads")

print()
print("F4  The hybrid landscape (fixed-state layers + a few attention layers)")
hybrids = [
    ("Jamba (AI21)", "Mamba-Transformer MoE, 52B total / 12B active"),
    ("Zamba2 (Zyphra)", "shared-attention-block Mamba hybrid"),
    ("Nemotron-H (NVIDIA)", "Mamba-2 hybrid, ~3x decode throughput"),
    ("Granite 4.0 (IBM)", "Mamba-2 + MoE: 4 full-attention layers in 40"),
    ("Qwen3-Next 80B (Alibaba)", "Gated DeltaNet in 3 of 4 layers"),
    ("Kimi Linear (Moonshot)", "Gated DeltaNet + full attention interleave"),
]
for name, recipe in hybrids:
    print(f"    {name:26s}  {recipe}")

print()
print("F5  Choosing by failure mode, not benchmark average")
picks = [
    ("needle-style QA, exact recall", "MLA or full attention - fixed state is lossy"),
    ("streaming, throughput-critical", "SSM-family layers - linear time, O(1) state"),
    ("very long context serving", "MLA - 576 elems/token beats every GQA layout"),
]
for workload, pick in picks:
    print(f"    {workload:32s} -> {pick}")

print("DETERMINISTIC-OK")
```

```text
F1  Fixed-state vs attention: the ops shape (d_model=4, d_state=8)
    L=  32  scan state ops    1024   attention ops     4096   ratio   4.0x
    L= 128  scan state ops    4096   attention ops    65536   ratio  16.0x
    L= 512  scan state ops   16384   attention ops  1048576   ratio  64.0x
    state shape stays (4, 8) at every L - it never grows with context

F2  ZOH discretization and the selectivity gate (one channel, A = -0.75)
    delta=0.01  A_bar=exp(-0.0075)=0.9925  state persists across many tokens (write)
    delta=0.10  A_bar=exp(-0.0750)=0.9277  state persists across many tokens (write)
    delta=2.00  A_bar=exp(-1.5000)=0.2231  state resets - the model ignores the token (forget)

F3  The MLA cache arithmetic (DeepSeek-V3 published dims)
    per token per layer: MHA 32768 elems, MLA 576 (512 latent + 64 rope key), GQA-8 2048 elems
    32k-context KV cache: MHA 122.0 GB, MLA 2.14 GB -> 56.9x smaller
    MLA is 3.6x below GQA-8 - without shared heads

F4  The hybrid landscape (fixed-state layers + a few attention layers)
    Jamba (AI21)                Mamba-Transformer MoE, 52B total / 12B active
    Zamba2 (Zyphra)             shared-attention-block Mamba hybrid
    Nemotron-H (NVIDIA)         Mamba-2 hybrid, ~3x decode throughput
    Granite 4.0 (IBM)           Mamba-2 + MoE: 4 full-attention layers in 40
    Qwen3-Next 80B (Alibaba)    Gated DeltaNet in 3 of 4 layers
    Kimi Linear (Moonshot)      Gated DeltaNet + full attention interleave

F5  Choosing by failure mode, not benchmark average
    needle-style QA, exact recall    -> MLA or full attention - fixed state is lossy
    streaming, throughput-critical   -> SSM-family layers - linear time, O(1) state
    very long context serving        -> MLA - 576 elems/token beats every GQA layout
DETERMINISTIC-OK
```
