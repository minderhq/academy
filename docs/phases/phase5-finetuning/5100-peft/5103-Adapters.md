---
Document ID: 5103
Title: "5103: Adapters & Parameter-Efficient Adaptation Methods"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# 5103: Adapters & Parameter-Efficient Adaptation Methods

## Abstract

LoRA ([5101](./5101-LoRA-Logic.md)) dominates the PEFT conversation, but it is
one point in a larger design space: bottleneck adapters, soft prompts, and
activation-scaling methods all adapt a frozen model by training under 1% of
its parameters — each with a different cost profile at train time and
inference time. This document maps that space, implements the core
mechanics, and gives a decision guide for picking the right method.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. The PEFT Design Space](#2-the-peft-design-space)
- [3. Bottleneck Adapters](#3-bottleneck-adapters)
- [4. Soft Prompts: Prompt & Prefix Tuning](#4-soft-prompts-prompt--prefix-tuning)
- [5. IA³: Activation Scaling](#5-ia³-activation-scaling)
- [6. Compacter](#6-compacter)
- [7. Adapter Fusion](#7-adapter-fusion)
- [8. Method Comparison](#8-method-comparison)
- [9. Choosing a Method](#9-choosing-a-method)
- [10. References](#10-references)

---

## 1. Overview

### 1.1 Prerequisites

- [5101: LoRA Logic](./5101-LoRA-Logic.md) — low-rank decomposition basics
- [5102: QLoRA Pipelines](./5102-QLoRA-Pipelines.md) — 4-bit base + adapters
- Transformer architecture ([3402](../../phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md))

### 1.2 Learning Objectives

After completing this document, you will:
- ✅ Classify PEFT methods: additive modules vs soft prompts vs activation scaling
- ✅ Implement bottleneck adapter, prefix tuning, and IA³ from first principles
- ✅ Quantify trainable-parameter and inference-latency trade-offs
- ✅ Stack multiple task adapters with fusion
- ✅ Pick a method from task, latency, and multi-task requirements

---

## 2. The PEFT Design Space

All PEFT methods keep the base model frozen and train a small delta. The
families differ in *where* the delta lives:

```text
┌─────────────────────────────────────────────────────────────┐
│                    PEFT design space                        │
├─────────────────────┬───────────────────┬───────────────────┤
│ Additive modules    │ Soft prompts      │ Reparam/scaling   │
│ (new layers)        │ (new embeddings)  │ (delta on W or a) │
├─────────────────────┼───────────────────┼───────────────────┤
│ • Bottleneck adapter│ • Prompt tuning   │ • LoRA (ΔW=BA)    │
│ • Compacter         │ • Prefix tuning   │ • IA³ (scale a)   │
│ • (IA³ is borderline│ • P-tuning v2     │ • BitFit (bias)   │
│    — see Section 5) │                   │                   │
└─────────────────────┴───────────────────┴───────────────────┘
```

The decisive question for production is **inference overhead**: adapters
and soft prompts add serial computation per token; LoRA and IA³ can be
merged into the weights for zero overhead.

---

## 3. Bottleneck Adapters

### 3.1 Structure

The original adapter (Houlsby et al., 2019) inserts a bottleneck module
inside each transformer block, after the attention and feed-forward
sublayers:

```python
import torch
import torch.nn as nn

class BottleneckAdapter(nn.Module):
    """Houlsby adapter: down-project -> nonlinearity -> up-project."""
    def __init__(self, d_model: int, reduction: int = 16):
        super().__init__()
        self.down = nn.Linear(d_model, d_model // reduction, bias=False)
        self.nonlin = nn.GELU()
        self.up = nn.Linear(d_model // reduction, d_model, bias=False)
        nn.init.zeros_(self.up.weight)   # residual starts as identity

    def forward(self, x):
        return x + self.up(self.nonlin(self.down(x)))   # residual
```

**Where:**
- **reduction (r)**: bottleneck factor; r=16 is standard
- **Zero-init up-projection**: the adapter starts as a no-op, so training
  begins from the pretrained behavior instead of a random perturbation
- Trainable parameters per adapter: `2 × d_model × d_model / r`
  (e.g. ~0.6% of a 7B model's weights across all layers at r=16)

### 3.2 The Catch: Serial Overhead

Unlike LoRA's merged `W + ΔW`, the adapter adds a **sequential** matmul pair
per layer. After merging is impossible (the nonlinearity sits in between),
every generated token pays the extra latency forever. This is the main
reason LoRA displaced adapters for decoder LLMs — adapters remain the
better fit for encoder models (BERT-style) where per-token serving latency
matters less.

---

## 4. Soft Prompts: Prompt & Prefix Tuning

### 4.1 Prompt Tuning

Train a small matrix of continuous embeddings prepended to the input —
no model surgery at all:

```python
class PromptTuning(nn.Module):
    def __init__(self, base_model, n_tokens: int = 20, d_model: int = 4096):
        super().__init__()
        self.base = base_model                        # fully frozen
        self.prompt = nn.Parameter(torch.randn(n_tokens, d_model) * 0.02)

    def forward(self, input_ids):
        emb = self.base.get_input_embeddings()(input_ids)   # [B, T, D]
        p = self.prompt.unsqueeze(0).expand(emb.size(0), -1, -1)
        return self.base(inputs_embeds=torch.cat([p, emb], dim=1))
```

- **Shallow** (input layer only): cheap, but clearly weaker than full FT
- Quality approaches full fine-tuning only at large scale (>10B base)

### 4.2 Prefix Tuning

Prefix tuning extends the idea **deep**: trainable key/value prefixes at
*every* attention layer, which steer the attention computation itself —
much stronger than input-level prompts at small scale.

```text
Per attention layer i:
  K_i = [ P_k(i) ; K ]      P_k(i): trainable prefix  [L_p, d_head]
  V_i = [ P_v(i) ; V ]      P_v(i): trainable prefix  [L_p, d_head]

Cost: 2 × L_layers × L_p × d_model parameters
      (L_p = 10..20 prefix tokens is typical)
```

**Trade-offs:**
- Steals context window (prefix tokens consume KV cache)
- Re-parameterizing the prefix through a small MLP (P-tuning v2 style)
  stabilizes optimization vs raw embeddings

> **📊 Rule of Thumb:**
> Soft prompts shine for **many tasks over one shared frozen base** —
> swap a 100 KB prompt instead of a 100 MB adapter. For single-task
> quality on 7B+ models, LoRA/QLoRA usually wins.

---

## 5. IA³: Activation Scaling

IA³ (*Infused Adapter by Inhibiting and Amplifying Inner Activations*)
learns per-channel rescaling vectors instead of weight matrices:

```text
IA³ vectors:
  l_k ∈ R^d_head   scale attention keys
  l_v ∈ R^d_head   scale attention values
  l_ff ∈ R^d_ff    scale feed-forward activations

  attention:  K = K ⊙ l_k,   V = V ⊙ l_v
  FFN:        FF(x) = FF(x) ⊙ l_ff
```

```python
class IA3Scaler(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.l = nn.Parameter(torch.ones(dim))   # init 1 = identity

    def forward(self, x):
        return x * self.l
```

| Property | IA³ | LoRA (r=8) |
|----------|-----|------------|
| Trainable params (7B) | ~0.02% | ~0.1-0.2% |
| Mergeable into weights | Yes (rescale W rows/cols) | Yes (W += BA) |
| Capacity | Low (diagonal only) | Low-rank but richer |
| Best for | Cheap multi-task, quick experiments | Default quality pick |

IA³ can be folded into the weight matrices before serving — zero overhead
like merged LoRA, at ~5-10× fewer trained parameters.

---

## 6. Compacter

Compacter compresses the bottleneck adapter further with **Kronecker
products**: each projection matrix is a sum of a few Kronecker products of
tiny factors.

```text
Standard down-projection:  W ∈ R^{d/k × d}        (d × d/k params)
Compacter:                 W = Σ_i A_i ⊗ B_i      (n_prod × (s² + s·d/k) params, s ≪ d)

Example (d=768, k=4): full = 147k params -> compacter ≈ 3.6k params
```

- Same serial-overhead caveat as Section 3
- Historically strongest on low-resource tasks and small/medium encoder
  models; on modern decoder LLMs the LoRA family dominates in practice

---

## 7. Adapter Fusion

When serving **many tasks** on one base model, train one adapter per task,
then learn a fusion layer that attends across them:

```python
class AdapterFusion(nn.Module):
    """Learned attention over N task adapters' outputs."""
    def __init__(self, adapters: nn.ModuleList, d_model: int):
        super().__init__()
        self.adapters = adapters            # frozen per-task adapters
        self.query = nn.Linear(d_model, d_model)
        self.scale = d_model ** 0.5

    def forward(self, x):
        keys = torch.stack([a.key(x) for a in self.adapters])   # [N, B, T, D]
        scores = torch.einsum("btd,ntd->btn", self.query(x), keys) / self.scale
        weights = scores.softmax(dim=1)
        outs = torch.stack([a(x) for a in self.adapters])       # [N, B, T, D]
        return x + torch.einsum("btn,ntbd->btd", weights, outs)
```

**Where:**
- Per-task adapters stay **frozen**; only the fusion attention trains
- Avoids catastrophic forgetting between tasks vs multi-task joint training
- Adds all adapters' compute at inference — the same serial-overhead caveat

---

## 8. Method Comparison

| Method | Trainable params (7B) | Inference overhead | Quality vs full FT | Sweet spot |
|--------|----------------------|--------------------|--------------------|------------|
| Bottleneck adapter | ~0.5% | +1 serial matmul pair/layer | Good | Encoder models, classification |
| Prompt tuning | ~0.01% | +20 prompt tokens | Fair (worse <10B) | Massive multi-task on huge base |
| Prefix tuning | ~0.1% | +10-20 KV tokens/layer | Good | Medium models, generation tasks |
| IA³ | ~0.02% | None (mergeable) | Good | Cheapest serving, fast iteration |
| Compacter | ~0.05% | +1 serial pair/layer | Good (low-data) | Low-resource, small models |
| LoRA / QLoRA | ~0.1-0.2% | None (mergeable) | Very good | **Default choice** |

---

## 9. Choosing a Method

```text
Decision guide:
├── Single task, want best quality?      -> QLoRA (5102) or LoRA (5101)
├── Need zero serving overhead?          -> LoRA or IA³ (merge, then discard)
├── Hundreds of tasks, one shared base?  -> per-task soft prompts or adapters + fusion
├── Encoder model, classification?       -> bottleneck adapters (well-supported in PEFT)
├── Ultra-low trainable-param budget?    -> IA³ or BitFit (biases only)
└── Researching low-data regimes?        -> Compacter, prefix tuning
```

The HuggingFace `peft` library implements all of the above behind one API
surface — swap `LoraConfig` for `IA3Config` / `PrefixTuningConfig` /
`PromptTuningConfig` and the training loop is unchanged.

---

## 10. References

### Academic Papers
- [1] Houlsby et al. "Parameter-Efficient Transfer Learning for NLP". ICML, 2019.
- [2] Lester et al. "The Power of Scale for Parameter-Efficient Prompt Tuning". EMNLP, 2021.
- [3] Li & Liang. "Prefix-Tuning: Optimizing Continuous Prompts for Generation". ACL, 2021.
- [4] Liu et al. "Few-Shot Parameter-Efficient Fine-Tuning is Better and Cheaper than In-Context Learning" (IA³ / T-Few). NeurIPS, 2022.
- [5] Mahabadi et al. "Compacter: Efficient Low-Rank Hypercomplex Adapter Layers". NeurIPS, 2021.
- [6] Pfeiffer et al. "AdapterFusion: Non-Destructive Task Composition for Transfer Learning". EACL, 2021.

### Related PROJECT-OMEGA Documents
- [5101: LoRA Logic](./5101-LoRA-Logic.md) - the default PEFT method
- [5102: QLoRA Pipelines](./5102-QLoRA-Pipelines.md) - 4-bit base + adapters
- [5104: LoRA Implementation Guide](./guides/5104-LoRA-Implementation-Guide.md) - practical guide

---

## Next Steps

- Continue with: **[5104: LoRA Implementation Guide](./guides/5104-LoRA-Implementation-Guide.md)**
- Alignment: **[5201: DPO Theory](../5200-alignment/5201-DPO-Theory.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**

---

**Document ID:** 5103
**Status:** Complete
**Related Documents:** [5101, 5102, 5201]
