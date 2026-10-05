---
Document ID: 3404
Title: "3404: Beyond Attention — SSMs and MLA"
Phase: 3
Module: 3400
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'architecture', 'attention', 'ssm', 'mla']
---

# 3404: Beyond Attention — SSMs and MLA

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Why Sequence Mixing Is a Bottleneck](#why-sequence-mixing-is-a-bottleneck)
- [State-Space Models: The Recurrent Alternative](#state-space-models-the-recurrent-alternative)
- [Selectivity: The Mamba Recipe](#selectivity-the-mamba-recipe)
- [Mamba-2: The SSD Duality](#mamba-2-the-ssd-duality)
- [Hands-On: A Discrete SSM in PyTorch](#hands-on-a-discrete-ssm-in-pytorch)
- [Hands-On: The Real Selective Scan](#hands-on-the-real-selective-scan)
- [The Honest Weakness: Recall and Copying](#the-honest-weakness-recall-and-copying)
- [Hybrids: The Pragmatic Answer](#hybrids-the-pragmatic-answer)
- [Multi-head Latent Attention](#multi-head-latent-attention)
- [Hands-On: The MLA Cache Arithmetic](#hands-on-the-mla-cache-arithmetic)
- [Hands-On: The Projection Shapes](#hands-on-the-projection-shapes)
- [Choosing: SSM vs MLA vs Full Attention](#choosing-ssm-vs-mla-vs-full-attention)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After this lesson you will be able to:

- Explain why softmax attention's O(L²) pair scores and its unbounded KV cache are the two costs that motivate post-Transformer architectures.
- Write the continuous state-space recurrence, discretize it with the zero-order-hold step, and implement the resulting recurrent scan in PyTorch.
- Describe what "selective" adds in Mamba (input-dependent B, C, and Δ) and why the parallel scan still works.
- State what changes in Mamba-2's SSD formulation (scalar-times-identity state matrices) and why it trades the general scan for faster chunked matmuls.
- Name the recall/copying weakness honestly, and explain why production SSM models (Granite 4.0, Nemotron-H, Qwen3-Next, Jamba) are hybrids that keep a few full-attention layers.
- Read DeepSeek-V3's config and derive MLA's per-token KV cache (576 elements) from `kv_lora_rank` and `qk_rope_head_dim`, and compare it against full MHA.
- Choose between SSM layers, MLA, and full attention for a given context-length and recall budget.

---

## Abstract

The Transformer won on parallelism, not efficiency. Every token attends to every
previous token: training costs O(L²) score computations, and inference carries a KV
cache that grows linearly with context and linearly with width. Two research lines
attack those costs from opposite ends. State-space models (SSMs) replace the pairwise
score matrix with a fixed-size recurrent state — linear time in sequence length,
constant memory at inference — and Mamba's selectivity plus Mamba-2's SSD formulation
made them trainable at Transformer quality on language. Multi-head latent attention
(MLA) keeps softmax attention but compresses its cache: DeepSeek's low-rank latent
carries each cached token in 576 elements where full MHA would carry 32,768.

This lesson teaches both, with runnable arithmetic. The SSM fences build a discrete
scan from scratch and then call the real CUDA kernel; the MLA fences recompute
DeepSeek-V3's cache numbers from its published config and walk the projection shapes
that produce them. It closes with the honest limitation of pure SSMs (associative
recall), the hybrid architectures that paper over it, and a decision table for
choosing between the three sequence mixers.

---

## Why Sequence Mixing Is a Bottleneck

A Transformer block does two jobs: mix information across the sequence (attention)
and transform it per-position (the MLP). Attention's mixing cost has two parts:

1. **Compute:** the score matrix is L × L for a sequence of length L. Doubling the
   context quadruples the attention FLOPs. Techniques like FlashAttention (see
   [3100: Attention](../3100-attention/)) make the constant smaller, but the
   quadratic shape stays.
2. **State:** autoregressive inference caches K and V for every past token at every
   layer. The cache grows linearly with context length and with `heads × head_dim`,
   and at long context it — not the weights — dominates the memory budget. Phase 4's
   [4200: KV Cache](../../phase4-quantization/4200-kv-cache/) module is entirely
   about shrinking that cache for a *fixed* attention shape.

Post-Transformer architectures attack the shape itself. SSMs change the mixer so the
per-token state is fixed-size: no L × L matrix, no growing cache. MLA keeps the
attention shape but proves the cache can be far smaller than `2 × heads × head_dim`
without losing quality. They are complementary: hybrids (later in this lesson) use
SSM layers for most of the network and keep a few attention layers for exact recall.

---

## State-Space Models: The Recurrent Alternative

A continuous-time state-space model evolves a hidden state h(t) driven by an input
x(t) and read out by a projection to y(t):

```text
h'(t) = A · h(t) + B · x(t)        (state update)
y(t)  = C · h(t) + D · x(t)        (readout, D = skip connection)
```

For a d_model-dimensional input, A is `d_model × N` where N is the *state expansion*
— each input channel carries an N-dimensional memory vector. Language models use
N ∈ [16, 256]; the bigger N is, the more history a fixed state can hold.

To process tokens, the continuous recurrence is discretized. With the zero-order-hold
(ZOH) assumption — input constant over one step of size Δ — each parameter maps to a
discrete step:

```text
Ā = exp(Δ · A)          B̄ = (ΔA)⁻¹(exp(ΔA) − I) · ΔB     (full ZOH)
```

and the recurrence becomes a plain linear recurrence over token positions:

```text
h_t = Ā · h_{t−1} + B̄ · x_t
y_t = C · h_t + D · x_t
```

Two properties matter more than the algebra:

- **Linear time.** Processing L tokens costs L fixed-shape state updates — O(L ·
  d_model · N) — instead of O(L² · d_model) attention scores.
- **Constant inference memory.** At generation time the "KV cache" is one h of shape
  `d_model × N` per layer. It never grows with context. This is the property MLA
  cannot match: MLA shrinks the per-token cache, SSMs eliminate it.

The lineage that made this work for language: S4 (Gu et al., 2021) fixed the
parameters and showed structured state spaces dominate the Long Range Arena;
HiPPO theory supplied the initialization that lets a fixed state compress history.
The remaining gap — every layer applying the *same* transition regardless of content
— is what Mamba closed.

---

## Selectivity: The Mamba Recipe

Mamba (Gu & Dao, 2023) makes the transition **input-dependent** — the model decides,
per token, how much to write and how much to forget:

```text
B_t = Linear_B(x_t)         (what to write)
C_t = Linear_C(x_t)         (what to read out)
Δ_t = softplus(Linear_Δ(x_t))   (the discretization step — the forget gate)
```

With Δ_t large, Ā = exp(Δ_t · A) → 0 and the state resets — the model can *ignore*
a token. With Δ_t small, state persists across many tokens. A time-invariant SSM
can only average; a selective one can gate. On the benchmark tasks that exposed the
gap (selective copying, induction heads), this is the change that closed it.

The cost: a data-dependent recurrence cannot be expressed as a convolution (S4's
training trick) or a dense matmul. Mamba's answer is a hardware-aware parallel scan —
the associative scan runs in shared memory across sequence chunks, avoiding materializing
a state history of size `batch × L × d_model × N`, which would be the memory bottleneck.
The kernel lives in the `mamba-ssm` package and is CUDA-only; the fence below calls it
directly.

---

## Mamba-2: The SSD Duality

Mamba-2 (Dao & Gu, 2024) simplifies the state matrix to a **scalar times identity**:

```text
A_t = a_t · I          (one scalar per token, broadcast over N)
```

With this restriction — the State Space Duality (SSD) framework — the recurrence has
a *dual form*. The recurrence view is O(L) sequential steps; unrolled, the readouts
collapse into a structured (semiseparable) matrix that can be computed with chunked
matmuls in parallel over sequence blocks. Training runs 2–8× faster than Mamba-1's
general scan at comparable quality, and the scalar form permits larger state
expansion N than the general kernel. The dual is the same trade you have seen twice
already in this corpus: attention's quadratic form and its linear FlashAttention form
are the same computation reorganized for the memory hierarchy — SSD is that same
reorganization for the SSM recurrence.

The scalar-times-identity restriction is also what the production hybrids adopt:
`ssm_cfg: {layer: Mamba2}` is the line in a released model's config that tells you
it is this variant (see the verified config of `state-spaces/mamba2-2.7b` in the
references).

---

## Hands-On: A Discrete SSM in PyTorch

The fence below implements the discrete recurrence — ZOH step, recurrent scan,
readout — on synthetic parameters, and measures the two claims: linear time shape
and constant state memory.

```python
import torch

torch.manual_seed(7)

L, d_model, d_state = 32, 4, 8

# continuous-space parameters, initialized the way S4 initializes them:
# negative real eigenvalues keep the state exponentially stable
A = -(0.5 + torch.rand(d_model, d_state))
B = torch.randn(d_model, d_state)
C = torch.randn(d_model, d_state)
D = torch.randn(d_model)
x = torch.randn(L, d_model)

# zero-order-hold discretization with a fixed step (Mamba makes the step
# input-dependent; the scan below is identical either way)
delta = 0.1
A_bar = torch.exp(delta * A)          # (d_model, d_state), elementwise exp
B_bar = (delta * A) * B               # first-order ZOH step

h = torch.zeros(d_model, d_state)     # the ONLY memory carried between steps
outputs = []
for t in range(L):
    h = A_bar * h + B_bar * x[t].unsqueeze(1)
    y_t = (h * C).sum(dim=1) + D * x[t]
    outputs.append(y_t)

y = torch.stack(outputs)              # (L, d_model)

state_ops = L * d_model * d_state
attn_ops = L * L * d_model
print(f"scan state shape (constant over L): {tuple(h.shape)}")
print(f"state ops {state_ops} vs attention ops {attn_ops} "
      f"-> ratio {attn_ops / state_ops:.1f}x at L={L}")
assert y.shape == (L, d_model)
assert h.shape == (d_model, d_state)  # state size is independent of L
```

Run it. The state shape printed after the loop is the same shape it had at t = 0 —
that is the whole argument. Change `L` to 512 and the state is still `4 × 8`, while
`attn_ops` grows by a factor of 256.

---

## Hands-On: The Real Selective Scan

The production kernel takes the discretization step as an input-dependent tensor and
fuses the scan into a single CUDA call. Shapes are `batch × dim × length` for u, Δ,
B and C:

```python
# pip install mamba-ssm   (compiles CUDA kernels; needs an NVIDIA GPU)
import torch
from mamba_ssm.ops.selective_scan_interface import selective_scan_fn

batch, dim, length, n_state = 2, 16, 64, 8
dev, dt = "cuda", torch.float32

u = torch.randn(batch, dim, length, device=dev, dtype=dt)            # inputs
delta = torch.rand(batch, dim, length, device=dev, dtype=dt) * 0.1   # per-token step
A = -(0.5 + torch.rand(dim, n_state, device=dev, dtype=dt))          # stable
B = torch.randn(batch, n_state, length, device=dev, dtype=dt)        # selective B
C = torch.randn(batch, n_state, length, device=dev, dtype=dt)        # selective C
D = torch.ones(dim, device=dev, dtype=dt)                            # skip

out = selective_scan_fn(u, delta, A, B, C, D, z=None, delta_bias=None)
print(out.shape)   # torch.Size([2, 16, 64])
```

Compare the signatures with the toy scan above: `u` is x, `delta` is the selective
Δ_t, and B and C are per-token tensors rather than fixed matrices — selectivity lives
entirely in the shapes. The kernel also accepts a gating branch `z` (the Mamba block's
second projection, gated by SiLU) which the toy omitted.

---

## The Honest Weakness: Recall and Copying

A fixed-size state is a lossy compression of history, and the loss is not uniform:
tasks that require *exact* retrieval of an early token — associative recall (MQAR,
Arora et al., 2023), induction-style copying — degrade sharply as sequence length
grows, while softmax attention, which keeps every token, does not. The Mamba paper
itself reports the copying gap. This is the failure mode to keep in mind whenever an
SSM benchmark looks clean: averaged metrics hide recall cliffs.

---

## Hybrids: The Pragmatic Answer

Production answer: don't choose. **Hybrid** architectures interleave a small number
of full-attention layers among SSM layers — the attention layers act as an exact-recall
scratchpad while the SSM layers carry the bulk of the sequence mixing. The verified
landscape (all on the Hub as of this writing):

| Model | Lab | Recipe |
|-------|-----|--------|
| Jamba | AI21 | Mamba-Transformer MoE (52B total / 12B active) |
| Zamba2 | Zyphra | shared-attention-block Mamba hybrid |
| Nemotron-H | NVIDIA | Mamba-2 hybrid, ~3× decode throughput vs equal-size Transformer |
| Granite 4.0 (GraniteMoeHybrid) | IBM | Mamba-2 + MoE on the Bamba architecture; e.g. 4 full-attention layers among 40 |
| Qwen3-Next 80B-A3B | Alibaba | Gated DeltaNet (linear attention) in 3 of 4 layers, gated full attention in 1 of 4 |
| Kimi Linear | Moonshot AI | Gated DeltaNet interleaved with full attention |

Granite 4.0 and Nemotron-H share lineage (IBM credits NVIDIA's hybrid work), and the
same needle-in-a-haystack weakness is what motivates the few retained attention layers
in every recipe. Note that Qwen3-Next and Kimi Linear pick a *different* linear mixer
— gated delta-rule linear attention rather than an SSM — but the architectural pattern
(fixed state, few full-attention layers retained) is identical.

---

## Multi-head Latent Attention

MLA attacks attention's other cost: the cache. DeepSeek-V2/V3's observation is that
K and V across heads are highly redundant, so cache the **latent** they were generated
from, not the heads. Each token's hidden state h_t is down-projected once:

```text
c_t = W_DKV · h_t                    (hidden_size → kv_lora_rank = 512)
k_pe = W_KR · h_t                    (hidden_size → qk_rope_head_dim = 64)
```

and the cache holds just `(c_t, k_pe)` — **576 elements per token per layer**. The
per-head keys and values are *up-projected* from the latent at use time:

```text
k_nope = reshape(W_UK · c_t)         (kv_lora_rank → heads × qk_nope_head_dim)
v      = reshape(W_UV · c_t)         (kv_lora_rank → heads × v_head_dim)
```

Two details make it work:

- **Decoupled RoPE.** RoPE is a position-dependent rotation; it cannot be folded
  into the up-projection (the rotation would have to act per position, after the
  shared latent was cached). So the rope component of the key is computed
  *positionally* (`k_pe` above, shared across heads) and concatenated to the
  content-based `k_nope` per head. The key becomes 128 + 64 = 192 wide per head.
- **Absorption.** Because `k_nope = (W_UK · c_t)` and the score is `q · k_nope`,
  you can absorb `W_UK` into the query projection and score `q' · c_t` directly —
  the up-projection never has to run on decode. The value side absorbs symmetrically
  into the output projection. Absorption is what makes up-projection-at-inference
  free; without it MLA would trade cache for compute.

The published config is the source of truth for the arithmetic, and DeepSeek-V3's is
public on the Hub: `hidden_size 7168`, `num_attention_heads 128`,
`qk_nope_head_dim 128`, `qk_rope_head_dim 64`, `v_head_dim 128`,
`kv_lora_rank 512`, 61 layers. The next fence turns those numbers into bytes.

---

## Hands-On: The MLA Cache Arithmetic

Per token per layer: MHA caches 2 × 128 × 128 = 32,768 elements; MLA caches
512 + 64 = 576. The fence computes both caches for DeepSeek-V3's shape at a 32k
context in bf16, straight from the verified config:

```python
# DeepSeek-V3 config.json, verified on the Hub (deepseek-ai/DeepSeek-V3)
cfg = dict(n_layers=61, num_heads=128, qk_nope_head_dim=128,
           qk_rope_head_dim=64, v_head_dim=128, kv_lora_rank=512)

ctx = 32768
dtype_bytes = 2  # bf16

# MHA: K and V per head (v_head_dim == qk_nope_head_dim == 128 here)
mha_elems = 2 * cfg["num_heads"] * cfg["qk_nope_head_dim"]

# MLA: one latent + one shared rope key — the ONLY things cached
mla_elems = cfg["kv_lora_rank"] + cfg["qk_rope_head_dim"]

mha_gb = mha_elems * dtype_bytes * ctx * cfg["n_layers"] / 1024**3
mla_gb = mla_elems * dtype_bytes * ctx * cfg["n_layers"] / 1024**3

print(f"per-token/layer: MHA {mha_elems} elems, MLA {mla_elems} elems")
print(f"32k-context KV cache: MHA {mha_gb:.1f} GB, MLA {mla_gb:.2f} GB "
      f"-> {mha_elems / mla_elems:.1f}x smaller")
assert mha_elems == 32768 and mla_elems == 576
```

The ratio is architecture, not tuning: `32768 / 576 ≈ 56.9×`, independent of context
length. (The DeepSeek-V2 paper headlines a 93.3% reduction against its MHA baseline;
the exact percentage depends on the baseline head count — the 56.9× figure here is
computed from V3's own published dims.) For contrast, GQA with 8 KV heads would cache
2 × 8 × 128 = 2,048 elements — MLA is another 3.6× below that, and unlike GQA it
does not sacrifice key-value expressiveness (every head still gets a distinct value).
This is why every long-context DeepSeek release trains with MLA, and why vLLM and
SGLang grew MLA-specific cache layouts.

---

## Hands-On: The Projection Shapes

The arithmetic fence treated 576 as an annotation; this fence walks the tensors that
produce it, including the decoupled rope key and the per-head shapes after
up-projection:

```python
import torch

torch.manual_seed(3)

hidden, kv_lora_rank = 7168, 512
n_heads, qk_nope, qk_rope, v_dim = 128, 128, 64, 128

h_t = torch.randn(1, hidden)

# the shared down-projections: latent + positional rope key
W_dkv = torch.nn.Linear(hidden, kv_lora_rank, bias=False)
W_kr = torch.nn.Linear(hidden, qk_rope, bias=False)
c_kv = W_dkv(h_t)                       # (1, 512)  <- cached
k_pe = W_kr(h_t)                        # (1, 64)   <- cached
print(f"cached per token: c_kv {tuple(c_kv.shape)} + k_pe {tuple(k_pe.shape)}"
      f" = {c_kv.numel() + k_pe.numel()} elems")

# up-projections run at use time, from the latent
W_uk = torch.nn.Linear(kv_lora_rank, n_heads * qk_nope, bias=False)
W_uv = torch.nn.Linear(kv_lora_rank, n_heads * v_dim, bias=False)
k_nope = W_uk(c_kv).view(n_heads, qk_nope)
v = W_uv(c_kv).view(n_heads, v_dim)

# per-head key: content part + the shared positional part
k = torch.cat([k_nope, k_pe.expand(n_heads, -1)], dim=-1)
print(f"per-head key {tuple(k.shape)}, value {tuple(v.shape)}")
assert k.shape == (n_heads, qk_nope + qk_rope) and v.shape == (n_heads, v_dim)
assert c_kv.numel() + k_pe.numel() == 576
```

Read the first `print` against the cache arithmetic: everything a layer must
remember about this token is the 512-wide latent plus the 64-wide rope key. The
128-key-by-128-value per-head tensors below it are *derived* — 128 heads' worth of
KV from 576 cached numbers, via absorption without even materializing them at decode.

---

## Choosing: SSM vs MLA vs Full Attention

| Axis | Full MHA/GQA | MLA | SSM (Mamba-2) |
|------|--------------|-----|----------------|
| Training compute | O(L²) | O(L²) | O(L) |
| Per-token cache | 2·heads·head_dim | kv_lora_rank + rope_dim | O(1) — fixed state |
| Exact recall of early tokens | Best | Best | Weakest (fixed state is lossy) |
| Long-context decode memory | Worst | Good | Best |
| Ecosystem maturity | Universal | DeepSeek lineage, major serving engines | Hybrids in production; kernels CUDA-only |
| When to pick | Recall-critical, short/medium context | Long-context quality at attention-grade recall | Throughput-critical, streaming, very long contexts where recall is approximate |

The industry's center of gravity is the hybrid: SSM-family layers for cost, a few
attention layers for recall, MLA where attention is retained at very long context.
Pure-attention models are not going away — the recall row is the reason — but the
"attention is all you need" framing has quietly become "attention is part of what
you need."

---

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| SSM perplexity matches attention but needle-style QA fails | Fixed state cannot hold exact early tokens; recall is the hidden casualty | Evaluate recall explicitly (MQAR-style tasks); prefer a hybrid for retrieval workloads |
| `selective_scan_fn` import works but the call crashes with a CUDA error | The kernel is CUDA-only; a CPU tensor or CPU-only build reaches the kernel | Keep every tensor `device="cuda"`; on CPU, teach with the toy scan from this lesson |
| `mamba-ssm` install fails while compiling | The package compiles CUDA extensions and needs a matching toolchain | Use a prebuilt wheel or the Hub-packaged kernels; pin to a released version |
| MLA cache budget computed as `2 × heads × head_dim` anyway | Reading `num_key_value_heads` off a DeepSeek config and assuming MHA layout | Derive the cache from `kv_lora_rank + qk_rope_head_dim`; the config's KV-head fields are vestigial for MLA |
| Applying RoPE to the MLA latent before caching | RoPE is positional; the latent is shared across positions and must be cached raw | Cache the unrotated latent; rope the dedicated `k_pe` component, or absorb on the query side |
| Comparing Mamba-2's speed to Mamba-1 and calling SSD "the same thing" | SSD's chunked matmul form only exists because of the scalar-times-identity restriction | State the restriction explicitly; the general scan and SSD are different kernels for different A shapes |

---

## Summary

- Attention's two costs — O(L²) scores and a linearly growing KV cache — are the
  design pressures behind both post-attention families.
- State-space models replace pairwise scoring with a fixed-size recurrent state:
  linear time, constant inference memory. ZOH discretization turns the continuous
  recurrence into a token scan; Mamba's input-dependent B, C, Δ makes it selective;
  Mamba-2's scalar-times-identity (SSD) form unlocks chunked-matmul training.
- The cost is exact recall: MQAR-style tasks show pure SSMs losing to attention as
  sequence grows, which is why every production recipe (Jamba, Zamba2, Nemotron-H,
  Granite 4.0, Qwen3-Next, Kimi Linear) is a hybrid retaining a few full-attention
  layers.
- MLA keeps attention and compresses its cache instead: one 512-wide latent plus a
  64-wide decoupled rope key per token per layer, with per-head K/V up-projected at
  use time and the projections absorbed to keep decode compute flat — 576 cached
  elements against MHA's 32,768 on DeepSeek-V3's published dims.
- Choose by failure mode, not benchmark average: recall-critical work wants
  attention (or MLA); throughput- and memory-critical streaming wants SSM-family
  layers; the hybrids exist because real workloads want both.

---

## References

- Gu, A., & Dao, T. (2023). *Mamba: Linear-Time Sequence Modeling with Selective
  State Spaces.* — the selective scan; the copying-weakness discussion.
- Dao, T., & Gu, A. (2024). *Transformers are SSMs: Generalized Models and Efficient
  Algorithms Through Structured State Space Duality.* — SSD and the scalar-times-identity form.
- Gu, A., Goel, K., & Ré, C. (2021). *Efficiently Modeling Long Sequences with
  Structured State Spaces (S4).* — the structured-state foundation; Long Range Arena.
- Arora, S., et al. (2023). *Zoology: Measuring and Improving Recall in Efficient
  Language Models.* — MQAR and the recall gap for fixed-state models.
- DeepSeek-AI (2024). *DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts
  Language Model.* — MLA: the latent cache, decoupled RoPE, absorption.
- DeepSeek-AI (2024). *DeepSeek-V3 Technical Report*; config verified on the Hub at
  `deepseek-ai/DeepSeek-V3` (`kv_lora_rank 512`, `qk_rope_head_dim 64`).
- `state-spaces/mamba2-2.7b` on the Hub — released Mamba-2 config (`ssm_cfg: {layer:
  Mamba2}`), loadable with `AutoModel.from_pretrained(..., dtype="auto")`.
- `mamba-ssm` on PyPI (2.3.x line) — `selective_scan_fn` CUDA kernel used in this lesson.
- Hub model cards verified for the hybrid table: `ai21labs/Jamba-v0.1`,
  `ibm-granite` Granite 4.0 (GraniteMoeHybrid/Bamba), `nvidia` Nemotron-H,
  `Qwen/Qwen3-Next-80B-A3B`, Moonshot AI Kimi Linear.

---

## Next Steps

- [4200: KV Cache](../../phase4-quantization/4200-kv-cache/) — the cache-side
  toolbox (quantization, paging, eviction) that applies to whatever mixer you kept.
- [3300: Decoding](../../phase3-transformers/3300-decoding/) — decode-loop
  mechanics that make the per-token cache arithmetic above binding.
- [3100: Attention](../3100-attention/) — the attention internals MLA modifies.
- Write a recall stress test: run an MQAR-style needle task over a toy fixed-state
  model and an equal-size attention model, and watch the curves cross.
