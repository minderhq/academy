---
Document ID: 5501
Title: Optimizer Variants
Phase: Unknown
Module: 5500
Last Updated: 2026-02-05
Status: Review
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['documentation']
---

# 5501: Optimizer Variants

## Abstract

Different optimizers have different strengths and weaknesses for LLM training.

## Common Optimizers

### Adam

```python
optimizer = torch.optim.Adam(
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.999),
    eps=1e-8,
    weight_decay=0.0,  # Don't use with Adam
)
```

**Pros:**
- Fast convergence
- Adaptive learning rates
- Works well out of the box

**Cons:**
- Can generalize poorly
- Memory intensive (stores moments)
- Not ideal for large-scale training

### AdamW (Recommended for LLMs)

```python
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.999),
    eps=1e-8,
    weight_decay=0.01,  # Properly decoupled
)
```

**Pros:**
- Better generalization than Adam
- Proper weight decay implementation
- Standard for LLM fine-tuning

**Cons:**
- Still memory intensive
- More hyperparameters

### Adafactor

```python
from transformers import Adafactor

optimizer = Adafactor(
    model.parameters(),
    lr=1e-4,
    eps=(1e-30, 1e-3),
    clip_threshold=1.0,
    decay_rate=-0.8,
    beta1=None,
    weight_decay=0.0,
    relative_step=False,
    scale_parameter=False,
    warmup_init=False,
)
```

**Pros:**
- Memory efficient (no per-parameter moments)
- Good for very large models
- Used in T5 and UL2 training

**Cons:**
- Slower convergence
- More sensitive to hyperparameters
- Less widely adopted

### Sophia (New)

```python
# Sophia: Second-order optimizer that's cheaper than Adam
# Not yet in PyTorch core, use custom implementation
```

**Pros:**
- Better sample efficiency
- Lower memory than Adam
- State-of-the-art results on some benchmarks

**Cons:**
- Not widely available
- Less tested
- Newer, less battle-tested

## Choosing an Optimizer

```text
Model Size < 1B:
└─ Use AdamW (simple, effective)

Model Size 1B-10B:
├─ Fine-tuning: AdamW
└─ Pretraining: Adafactor (memory efficient)

Model Size > 10B:
└─ Use Adafactor or 8-bit AdamW
```


---

## Next Steps

- Phase 5 Complete! Next: **[Phase 6: RAG](../../phase6-rag/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Last Updated:** 2026-02-04
