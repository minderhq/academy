---
Document ID: 6305
Title: "6305: LongLoRA, Ring Attention, and Context Distillation"
Phase: 6
Module: 6300
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'context', 'long-context', 'finetuning', 'distributed']
---

# 6305: LongLoRA, Ring Attention, and Context Distillation

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Scaling Wall](#the-scaling-wall)
- [LongLoRA: Shifted Sparse Attention](#longlora-shifted-sparse-attention)
- [Ring Attention: Exact Sequence Parallelism](#ring-attention-exact-sequence-parallelism)
- [The Parameter Ledger: LoRA Plus Embedding and Norm](#the-parameter-ledger-lora-plus-embedding-and-norm)
- [Context Distillation: The Context into the Weights](#context-distillation-the-context-into-the-weights)
- [One Extension Campaign](#one-extension-campaign)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Abstract

Position-level scaling — interpolation and YaRN base-frequency stretching — is taught in [3201](../../phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md), but the training-time methods that actually extend a pretrained model's context are taught nowhere in the curriculum: LongLoRA's shifted sparse attention and ring attention's sequence parallelism are named in this module's quiz answer key and admitted as untaught, and context distillation — the technique that absorbs a prompt into the weights so the prompt can be dropped at serving time — is taught nowhere either. This lesson builds all three as working code. Shifted sparse attention is simulated at the reachability level: without the shift, a token's information reach stays pinned at its 4-token group forever; with the alternating half-group shift, reach walks 4 → 8 → 12 → 16 and every token sees the full sequence by layer four. Ring attention is simulated exactly: the ring of four devices holding four tokens each reproduces full attention to a maximum absolute difference of 2.22e-16 — sequence parallelism here is an implementation identity, not an approximation. The parameter ledger prices LongLoRA's LoRA-plus recipe: plain LoRA trains 3.8% of a toy transformer and underperforms, while adding the embedding and norm layers moves it to 12.4% and closes the gap to full fine-tuning. Context distillation is trained live: a student with no access to the document drives its KL divergence against the document-conditioned teacher from 1.1956 to 0.0001 and answers all three document-dependent probes correctly, without ever seeing the document. The campaign fence prices one 65,536-token extension run end to end.

## Learning Objectives

After this lesson, you will be able to:

- Explain why context extension is a training problem, not an inference trick, and where the quadratic cost actually lives.
- Simulate shifted sparse attention and show the half-group shift's reachability effect: without it, cross-group information flow never starts.
- Simulate ring attention and verify it reproduces full attention exactly, with per-device KV memory reduced by the device count.
- Price the LongLoRA parameter ledger and state why LoRA-only underperforms while embedding-plus-norm trainable closes the gap.
- Train a context-distillation pair to convergence and read the KL curve as the prompt leaving the input and entering the weights.

## The Scaling Wall

A model pretrained at 4K tokens does not get 128K by being asked nicely. Three costs move together as the target window grows, and each method in this lesson attacks exactly one of them:

1. **Attention compute** grows with N²: the softmax matrix at 65,536 tokens is 4,294,967,296 cells — 17.2 GB in fp32 for one layer, one head, one sequence.
2. **Activation memory** grows with the sequence dimension per device: a single device holding all keys and values for 65,536 tokens cannot fit regardless of how clever the kernel is.
3. **The prompt tax** grows with serving volume: a deployment answering 1,000 questions against a 12,000-token document pays 12 million prompt tokens for answers the document could have baked into the weights.

Position interpolation and YaRN ([3201](../../phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)) fix *where positions land*; they say nothing about who computes what, on which device, or whether the context needs to be in the prompt at all. The KV-cache physics of the trained window live in [4201](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md). This lesson owns the training-time machinery.

## LongLoRA: Shifted Sparse Attention

LongLoRA (Chen et al., ICLR 2024) extends Llama2-class models from 4K to 100K+ context with one structural change during training: **shifted sparse attention (S²-Attn)**. Split the sequence into groups of `group_size` tokens, run attention *within groups only* during training, and shift the tokens by half a group in alternating layers. At inference the attention is dense again — the shift is a training-time scaffold, which is why the method is compatible with existing inference stacks and takes about two lines to implement on top of grouped attention kernels.

The shift is not an optimization detail; it is the entire method. A token that attends only within its group in *every* layer can never receive information from outside that group — not at layer two, not at layer ten. The fence below simulates information reach: each layer, a token's reachable set becomes the union of the reachable sets of every token it attends to. Without the shift the reach is pinned at the group size forever; with the alternating half-group shift it doubles its way to the full sequence:

```python
import numpy as np

N, g = 16, 4
shift = g // 2

part_plain = np.arange(N) // g                      # groups 0-3 | 4-7 | 8-11 | 12-15
part_shift = ((np.arange(N) + shift) % N) // g      # same groups, rotated by 2
alt_parts = [part_plain, part_shift]                # alternating layers

def reach(layers, parts):
    R = [frozenset([j]) for j in range(N)]
    for l in range(layers):
        part = parts[l % len(parts)]
        R = [frozenset().union(*[R[k] for k in range(N) if part[k] == part[j]])
             for j in range(N)]
    return R

for L in (1, 2, 3, 4, 6):
    rn = reach(L, [part_plain])
    ra = reach(L, alt_parts)
    print(f"L={L}: no-shift reach {min(map(len, rn))}/{max(map(len, rn))}"
          f" | alternating reach {min(map(len, ra))}/{max(map(len, ra))}")

Nr, gr = 65536, 8192
print(f"cells: full {Nr**2:,} vs grouped {Nr*gr:,} (ratio {Nr*gr/Nr**2:.3f})")
```

Reading the output: without the shift, reach stays `4/4` at every depth — layer count does not matter, because the attention pattern is the same partition every time and information from token 5 never reaches token 3 through any number of local layers. With the alternating half-group shift, reach walks `4 → 8 → 12 → 16`: by layer four every token's information can trace a path from anywhere in the sequence. That is the mechanism the paper states and this fence proves — the shift makes cross-group flow *start*; depth then finishes the job. The cost side is the point of doing it at all: grouped attention at the real shape processes 536,870,912 softmax cells instead of 4,294,967,296 — a ratio of 0.125, the group size over the sequence length, paid during training only.

The official implementation (dvlab-research/LongLoRA) ships this as the `shift_attn` flag in `train.py`, built on the FlashAttention variable-length kernels (`flash_attn_varlen_func`) — the groups become varlen segments and the shift becomes an index rotation. The paper additionally keeps the first and last 1,024 tokens in the same group, because document-opening and document-closing information is exactly what a retrieval prompt puts at the edges.

## Ring Attention: Exact Sequence Parallelism

S²-Attn reduces *compute* per token. Ring attention (Liu, Zaharia, Abbeel, NeurIPS 2023) attacks the *memory* wall: no single device ever holds the whole sequence. Devices form a ring; each holds a chunk of queries and a chunk of keys/values; for each of P ring steps a device computes its query chunk against the K/V chunk it currently holds, while its own K/V chunk moves to the next device. Two properties make it work:

- **Blockwise online softmax**: partial attention over one K/V chunk at a time, carried with a running maximum and running denominator, so numerically nothing overflows and nothing is dropped.
- **Communication/compute overlap**: the K/V transfer for the next step happens while the current step's block attention is still computing, so the ring's bandwidth cost hides under its arithmetic.

The fence runs both paths on the same tensors — full attention computed monolithically, ring attention computed as four devices × four ring steps with the online-softmax accumulation — and checks the ring against the monolith:

```python
import numpy as np

rng = np.random.default_rng(7)
P, nq, d = 4, 4, 4
Q = rng.normal(size=(P, nq, d)); K = rng.normal(size=(P, nq, d)); V = rng.normal(size=(P, nq, d))
N = P * nq

def full_attention():
    Qf, Kf, Vf = (x.reshape(N, d) for x in (Q, K, V))
    s = Qf @ Kf.T / np.sqrt(d)
    s -= s.max(axis=1, keepdims=True)
    w = np.exp(s); w /= w.sum(axis=1, keepdims=True)
    return w @ Vf

def ring_attention():
    out = [np.zeros((nq, d)) for _ in range(P)]
    m = [np.full(nq, -np.inf) for _ in range(P)]
    l = [np.zeros(nq) for _ in range(P)]
    for t in range(P):
        for p in range(P):
            src = (p - t) % P
            s = Q[p] @ K[src].T / np.sqrt(d)
            nm = np.maximum(m[p], s.max(axis=1))
            old = np.exp(m[p] - nm); new = np.exp(s - nm[:, None])
            l[p] = l[p] * old + new.sum(axis=1)
            out[p] = out[p] * old[:, None] + new @ V[src]
            m[p] = nm
    return np.stack([o / li[:, None] for o, li in zip(out, l)]).reshape(N, d)

ref, ring = full_attention(), ring_attention()
print(f"ring == full: {np.allclose(ref, ring, atol=1e-12)}"
      f"  max abs diff: {np.abs(ref - ring).max():.2e}")
print(f"KV per device: {nq}/{N} tokens ({N/nq:.1f}x less);"
      f" softmax cells: {nq*nq} vs {N*N} ({N*N/(nq*nq):.1f}x less)")
```

Reading the output: `ring == full: True` at maximum absolute difference 2.22e-16 — float noise, not approximation. This is the claim that separates ring attention from windowed or sparse schemes: it is *the same attention*, rescheduled. The ledger is the reason anyone bothers: each device holds N/P tokens of keys and values (4 of 16 — 4.0x less at this toy scale, exactly the device count at any scale), and the largest softmax ever materialized is one 4×4 block instead of the full 16×16 — 16.0x less. At the paper's scale that is the difference between a sequence that fits and one that cannot begin. The production implementations are `haoliuhl/ringattention` (the authors' JAX/Flax reference) and the `ring-flash-attn` PyPI package (zhuzilin), whose Llama-3-style variable-length API is the one recommended for most sequence-parallel workloads.

## The Parameter Ledger: LoRA Plus Embedding and Norm

Cheaper attention does not by itself make context extension affordable — the *parameter* side matters just as much, and it is where the paper's second finding lives. Plain LoRA (rank-decomposed updates on the attention projections; the mechanics live in [5104](../../phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md)) underperforms full fine-tuning on long-context extension noticeably. LongLoRA's fix, called LoRA+ in the paper, is to also make the **embedding layer and the normalization layers trainable**:

```python
Ll, d, vocab, r, f = 2, 16, 32, 2, 4
embed = vocab * d
per_layer = 4*d*d + 2*d*(f*d)
norms = Ll * 2 * d
full = embed + Ll*per_layer + norms
lora_only = Ll * 2 * (2*r*d)
longlora = lora_only + embed + norms
print(f"full FT: {full} ({100*full/full:.1f}%) | "
      f"LoRA-only: {lora_only} ({100*lora_only/full:.1f}%) | "
      f"LongLoRA(+embed+norm): {longlora} ({100*longlora/full:.1f}%)")
```

Reading the output: full fine-tuning trains 6,720 parameters — 100.0%. LoRA-only trains 256 of them, 3.8%, and in the paper's ablations this budget *loses* perplexity to full fine-tuning at long context: attention-projection updates alone cannot re-orient a model whose positional statistics just changed by an order of magnitude. LongLoRA's 832 parameters — 12.4% — buy back the gap, because the embedding rows and the norm scales are exactly the parameters that absorb a position-axis shift. At the real Llama2-7B shape the same ladder runs 7.0B against 4.2M (0.06%) against 135.5M (1.9%) — the campaign fence prices it below.

## Context Distillation: The Context into the Weights

The first two methods change how a model *trains on* long context. Context distillation (Snell et al., ICLR 2023; used earlier in Askell et al. 2021) changes where the context has to *live* at serving time. A teacher conditions on the document and produces its output distribution; a student — architecturally identical, but **never given the document** — is trained to match that distribution by KL divergence. When the student converges, the document's content has moved out of the prompt and into the weights.

The fence builds the smallest honest version of this: a document is a single vector `u`; the teacher sees `[query; u]`, the student sees `[query]` only. The student trains on the frozen teacher distributions, gradients and all, without the document anywhere in its input path:

```python
import numpy as np

rng = np.random.default_rng(11)
dv, voc, nprobe, steps, lr = 6, 6, 3, 400, 0.35
u = rng.normal(size=(dv,))
Qp = rng.normal(size=(nprobe, dv))
W_T = rng.normal(size=(2*dv, voc)) * 0.5
W_S = rng.normal(size=(dv, voc)) * 0.5

def softmax(z):
    z = z - z.max(); e = np.exp(z); return e / e.sum()

teacher = lambda q: softmax(np.concatenate([q, u]) @ W_T)
student = lambda q: softmax(q @ W_S)
T = np.stack([teacher(q) for q in Qp])

for step in range(steps):
    grad = np.zeros_like(W_S); total = 0.0
    for i in range(nprobe):
        s = student(Qp[i])
        total += float(np.sum(T[i] * (np.log(T[i] + 1e-12) - np.log(s + 1e-12))))
        grad += np.outer(Qp[i], s - T[i])
    W_S -= lr * grad / nprobe
    if step in (0, 99, 199, 399):
        print(f"step {step+1}: KL = {total/nprobe:.4f}")

agree = sum(int(np.argmax(student(q)) == np.argmax(t)) for q, t in zip(Qp, T))
print(f"argmax agreement on doc-dependent probes: {agree}/{nprobe}")
```

Reading the output: the student starts at KL 1.1956 from the document-conditioned teacher — it knows nothing the document knows. By step 100 the KL is 0.0028, by step 200 it is 0.0005, and it settles at 0.0001; all three document-dependent probes are answered with the teacher's argmax, `3/3`, by a student whose input path never contained the document. That is the technique's whole pitch, and it is why the quiz answer key phrases it as "compresses context into weights": the compression is training, not summarization. The serving arithmetic follows directly — the campaign fence prices a 1,000-query deployment against a 12,000-token document at 241.0x fewer prompt tokens. The honest boundary: the student inherits the teacher's *document-conditioned* behavior on the training distribution, not new knowledge — a probe about a fact absent from both stays unanswerable, and the capacity to absorb a document is bounded by the student's parameters, which is why production use pairs distillation with the curation discipline of [6504](../6500-mlops-pipelines/6504-Re-Embedding-Policy-and-AB-Testing.md) rather than treating it as free.

Note the cousin that this technique is *not*: fine-tuning on compressed contexts plus teacher answers — the shape this module's practice exercise sketches — keeps the context in the prompt, just shorter. Distillation removes the context from the input path entirely. The KL-on-logits formulation above is the named technique.

## One Extension Campaign

The three methods compose into one run because they attack different lines of the bill. The fence prices a single 4K → 64K extension of a Llama2-7B-class model, 1,000-query serving afterward, computing every number from named constants:

```python
N, P, g = 65536, 8, 8192
print(f"softmax cells: full {N**2:,} ({N**2*4/1e9:.1f} GB) | "
      f"S2 {N*g:,} ({N*g/(N**2):.3f}x) | ring block/step {(N//P)**2:,} "
      f"({N**2//(N//P)**2:.0f}x less per materialization), KV/device {N//P:,} ({P}x less)")

Ll, d, r, voc, nl = 32, 4096, 8, 32000, 2
D = 7.0e9
lora = Ll * 2 * 2 * r * d
plus = lora + voc*d + Ll*nl*d
print(f"7B ledger: full {D/1e9:.1f}B | LoRA-only {lora/1e6:.1f}M ({100*lora/D:.2f}%) | "
      f"LongLoRA {plus/1e6:.1f}M ({100*plus/D:.1f}%)")

doc_t, q_t, n_q = 12000, 50, 1000
print(f"prompt tokens: teacher {n_q*(doc_t+q_t):,} vs distilled {n_q*q_t:,} "
      f"({n_q*(doc_t+q_t)/(n_q*q_t):.1f}x fewer)")
```

Reading the output, line by line. Attention at 65,536 tokens monolithically materializes 4,294,967,296 softmax cells — 17.2 GB for one layer-head-sequence in fp32; S²-Attn's grouped pattern cuts that to 536,870,912 cells (0.125x, the training-time compute line); ring attention never materializes more than one 67,108,864-cell block per step (64x less per materialization) and holds 8,192 keys/values per device (8x less — the memory line). The parameter line: 7.0B full against 4.2M LoRA-only (0.06%) against 135.5M LongLoRA (1.9%) — the recipe that the paper found necessary, not optional. And the serving line: 12,050,000 teacher prompt tokens against 50,000 distilled — 241.0x fewer, the context having moved into the weights. One run, four lines of the bill, each owned by a different method.

## Known Failure Modes

| # | Failure | Cause | Fix |
|---|---------|-------|-----|
| 1 | S²-Attn model incoherent across groups at inference | Attention left grouped at serving time | The shift and grouping are **training-only**; restore dense attention before deployment |
| 2 | Grouped training converges but cross-group questions fail | No shift, or shift applied in every layer so only one partition ever exists | Alternate half-group shift layer by layer; verify information reach grows past the group size |
| 3 | Ring attention diverges or returns NaN at long context | Naive softmax per block without the running max/denominator | Blockwise online softmax: carry running maximum and denominator across ring steps |
| 4 | Ring result subtly wrong with correct-looking loss | K/V rotation off by one step, or softmax normalized per block instead of globally | Check ring == full on a small case first — exactness is a property you can and should assert |
| 5 | LongLoRA with plain LoRA underperforms full FT | Embedding and norm layers frozen while positional statistics change | LoRA+: make embedding + normalization trainable alongside the rank-decomposed projections |
| 6 | Context distillation student answers training-doc probes but nothing else | Distillation internalizes the teacher's document-conditioned behavior, not general knowledge | Pair with curation/AB discipline; do not treat the student as knowledgeable outside the distilled distribution |
| 7 | Distillation trained on compressed-context answers instead | Conflating the technique with compression-aided SFT | The student's input path must exclude the document; the loss is KL on logits, teacher-with-document vs student-without |
| 8 | Extension run OOMs at the target length despite S²-Attn | Activation memory for one full-length sequence still exceeds one device | Combine with ring/sequence parallelism — S²-Attn cuts compute, the ring cuts per-device memory; they are not substitutes |

## Summary

- **Context extension is three separate bills** — attention compute, per-device activation memory, and the serving-time prompt tax — and the position-level fixes of [3201](../../phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md) pay none of them.
- **Shifted sparse attention** splits the sequence into groups during training and rotates by half a group in alternating layers; without the shift a token's information reach is its group size forever, with it the reach walks 4 → 8 → 12 → 16 and covers the sequence by layer four, at a training-time attention cost of 0.125x.
- **Ring attention** is exact sequence parallelism: four devices × four ring steps with blockwise online softmax reproduce full attention to 2.22e-16, holding N/P tokens per device and materializing one block of softmax at a time.
- **LoRA+ is the parameter line**: LoRA-only at 3.8% of a toy transformer's parameters loses to full fine-tuning; adding the embedding and norm layers — 12.4% total — closes the gap, and 1.9% at the 7B scale.
- **Context distillation** moves the document out of the prompt entirely: the student's KL against the document-conditioned teacher falls 1.1956 → 0.0028 → 0.0005 → 0.0001 and answers 3/3 document-dependent probes without the document, which is 241.0x fewer serving tokens on the campaign's numbers.
- **The campaign fence** prices all four lines of one 64K extension in one output: 17.2 GB → 0.125x compute → 64x/8x memory → 1.9% parameters → 241.0x serving.

## References

### Related Minder Academy Documents

- [6302: CAG and Long-Context Architectures](./6302-CAG-Long-Context-Architectures.md) — the serving-side context strategies this lesson's training methods feed.
- [3201: Rotary Positional Embeddings (RoPE)](../../phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md) — the position-level extension ladder (interpolation, YaRN) these methods assume is already handled.
- [4201: Context Window Physics and OOM Prevention](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md) — the KV-cache arithmetic of the extended window at inference.
- [5301: Knowledge Distillation - Training Small Models Using Big Model Outputs](../../phase5-finetuning/5300-synthetic/5301-Knowledge-Distillation.md) — the distillation family's compress-into-a-smaller-form pattern.
- [5104: LoRA Implementation Guide](../../phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md) — the rank-decomposed update mechanics LongLoRA builds on.

### Primary Sources

- Chen, S., Wong, S., Chen, L., & Tian, Y. (2024). *LongLoRA: Efficient Fine-tuning of Long-Context Large Language Models.* ICLR 2024. arXiv:2309.12307. Official code: dvlab-research/LongLoRA (`shift_attn` flag).
- Liu, H., Zaharia, M., & Abbeel, P. (2023). *Ring Attention with Blockwise Transformers for Near Infinite Context.* NeurIPS 2023. arXiv:2310.01889. Reference code: haoliuhl/ringattention; production: zhuzilin/ring-flash-attention (PyPI `ring-flash-attn`).
- Snell, C., Klein, D., & Zhong, V. (2023). *Learning by Distilling Context.* ICLR 2023. arXiv:2209.15189.
- Askell, A., et al. (2021). *A General Language Assistant as a Laboratory for Alignment.* arXiv:2112.00861 — context distillation's earlier production use.

## Next Steps

- **Next Module:** continue with [assessment/QUIZ.md](assessment/QUIZ.md) — Q6, Q7, Q8, Q16, and Q17 are the questions this lesson answers; the shift's reachability walk, the ring's exactness check, and the distillation KL curve are the mechanics behind them.
- **Continue with:** the [6400: Vector Databases](../6400-vector-databases/README.md) module for where the extended-context pipeline's retrieval store lands in production.
- **Assessment:** extend the S²-Attn fence to `group_size = 2` and `L = 8` — confirm reach still saturates and identify which layer first covers the full sequence; then re-run the campaign fence at `N = 131072` and watch the 17.2 GB line become the argument for ring attention on its own.
