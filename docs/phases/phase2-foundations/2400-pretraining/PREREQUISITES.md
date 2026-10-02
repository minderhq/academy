---
Document ID: 2400-PREREQUISITES
Title: "2400: LLM Pretraining - Prerequisites"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Advanced
Tags: ['pretraining', 'prerequisites', 'preparation']
---

# 2400: LLM Pretraining - Prerequisites

**Verify you're ready before starting the module.**

---

## Contents

- [Before You Start](#before-you-start)
- [Required Knowledge](#required-knowledge)
- [Quick Refresher](#quick-refresher)
- [Self-Assessment](#self-assessment)
- [Estimated Preparation Time](#estimated-preparation-time)
- [Common Gaps](#common-gaps)
- [Preparation Checklist](#preparation-checklist)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Before You Start

Module 2400 trains language models from scratch. It assumes you can:

- **Train a model** — loss functions, optimizers, train/validation splits, overfitting
- **Use PyTorch fluently** — tensors, autograd, `nn.Module`, training loops
- **Read an LM's objective** — what "predict the next token" means mathematically
- **Handle data** — cleaning, filtering, deduplication, formatting
- **(Helpful) reason about distributed systems** — what it means to split one training run across devices

Every section below has a runnable example. **Run them, don't just read them** — the module builds directly on each one.

---

## Required Knowledge

### 1. ML Fundamentals

**What you should know:**
- Cross-entropy loss (and why it is negative log-likelihood)
- SGD vs Adam
- Overfitting and regularization
- Training/validation/test splits — and why the split happens *before* training

**Example: a complete train/validate loop**

```python
import torch
import torch.nn as nn

torch.manual_seed(0)

# Synthetic 3-class problem: 200 samples, 8 features. Labels are the
# argmax of a random linear map, so they are linearly separable.
n, d, k = 200, 8, 3
x = torch.randn(n, d)
true_w = torch.randn(d, k)
y = (x @ true_w).argmax(dim=1)

# Split BEFORE training: the validation set must stay unseen by the
# optimizer, otherwise your validation numbers are lies.
perm = torch.randperm(n)
x_train, y_train = x[perm[:150]], y[perm[:150]]
x_val, y_val = x[perm[150:]], y[perm[150:]]

model = nn.Linear(d, k)
loss_fn = nn.CrossEntropyLoss()
# Full-batch training: one optimizer step per epoch, so "epochs" here is
# really "steps". Adam's per-step movement is ~lr, hence the larger rate.
optimizer = torch.optim.Adam(model.parameters(), lr=0.05)

first_loss = None
for epoch in range(200):
    optimizer.zero_grad()
    loss = loss_fn(model(x_train), y_train)
    loss.backward()
    optimizer.step()
    if first_loss is None:
        first_loss = loss.item()

with torch.no_grad():
    train_loss = loss_fn(model(x_train), y_train).item()
    val_loss = loss_fn(model(x_val), y_val).item()
    train_acc = (model(x_train).argmax(1) == y_train).float().mean().item()
    val_acc = (model(x_val).argmax(1) == y_val).float().mean().item()

print(f"train loss {train_loss:.3f} | val loss {val_loss:.3f}")
print(f"train acc  {train_acc:.2f} | val acc  {val_acc:.2f}")
print(f"training worked: {train_loss < first_loss}")
# Train accuracy lands at ~0.99, validation at ~0.90 - the val-loss gap
# over train-loss is overfitting in miniature. Early stopping, weight
# decay, more data: the standard responses you will use in 2401.
```

**If you're not familiar:**
- Review: [2201: PyTorch Computational Graphs and Dynamic Execution](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)
- Practice: Retrain the loop with `lr=0.1` and with SGD instead of Adam; watch what changes
- Estimated time: 2 hours

---

### 2. Tokenization Basics

**What you should know:**
- Why models consume tokens, not raw characters or words
- Vocabulary: a fixed mapping token ↔ integer id
- Encode/decode as inverse operations
- What happens to out-of-vocabulary text

**Example: a word-level tokenizer in ~20 lines**

```python
# A word-level tokenizer: build a vocabulary, encode, decode.
corpus = [
    "the model trains on text",
    "text becomes tokens",
    "tokens become ids",
    "the ids train the model",
]

# 1) Normalize and split
def tokenize(text):
    return text.lower().split()

# 2) Build the vocabulary from the corpus (id 0 reserved for <unk>)
vocab = {"<unk>": 0}
for line in corpus:
    for token in tokenize(line):
        if token not in vocab:
            vocab[token] = len(vocab)

# 3) Encode / decode
def encode(text):
    return [vocab.get(tok, vocab["<unk>"]) for tok in tokenize(text)]

def decode(ids):
    id_to_token = {i: t for t, i in vocab.items()}
    return " ".join(id_to_token[i] for i in ids)

ids = encode("the model trains on unknown words")
print(ids)                 # -> [1, 2, 3, 4, 0, 0]  ("unknown"/"words" are OOV)
print(decode(ids))         # -> "the model trains on <unk> <unk>"

# Round-trip holds only for in-vocabulary text
assert decode(encode("the model trains on text")) == "the model trains on text"
```

This word-level scheme breaks on real corpora: vocabularies explode, rare words become `<unk>`, and morphology is lost. Real LLMs use **subword** methods — BPE, SentencePiece, Unigram — which Lesson 2401 builds and trains from scratch.

**If you're not familiar:**
- Review: the [Hugging Face LLM Course](https://huggingface.co/learn/llm-course) tokenization chapter
- Practice: Add punctuation handling to `tokenize()` so "text." and "text" map to the same token
- Estimated time: 1.5 hours

---

### 3. Language Modeling Objective

**What you should know:**
- The objective: predict `tokens[t+1]` from `tokens[:t+1]`
- The causal shift — inputs drop the last token, targets drop the first
- Cross-entropy over the vocabulary at **every** position
- Perplexity = `exp(loss)` — "how many tokens the model is effectively choosing between"

**Example: the shifted next-token loss**

```python
import torch
import torch.nn as nn

torch.manual_seed(0)

# Tiny "language": vocab of 10 tokens, sequences of length 16
vocab_size, seq_len, batch, d = 10, 16, 8, 16
tokens = torch.randint(0, vocab_size, (batch, seq_len))

embedding = nn.Embedding(vocab_size, d)
head = nn.Linear(d, vocab_size)

# Language modeling = predict tokens[:, t+1] from tokens[:, :t+1] at
# EVERY position, not one prediction per sequence. The shift: inputs
# drop the last token, targets drop the first.
x, y = tokens[:, :-1], tokens[:, 1:]
logits = head(embedding(x))                      # (batch, seq_len-1, vocab)
loss = nn.functional.cross_entropy(
    logits.reshape(-1, vocab_size), y.reshape(-1)
)
print(f"loss {loss.item():.3f}   ln({vocab_size}) = "
      f"{torch.log(torch.tensor(float(vocab_size))):.3f} (random-guess baseline)")
# An untrained model scores close to ln(vocab_size); a trained LM pushes
# loss well below it. Perplexity is just exp(loss).
```

**If you're not familiar:**
- Review: the [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165) paper, Section 2 (the objective at scale)
- Practice: Compute `exp(loss)` by hand for a couple of loss values and sanity-check the "effective vocabulary" intuition
- Estimated time: 1.5 hours

---

### 4. Attention and the Transformer Block

**What you should know:**
- Queries, keys, values — three learned linear projections
- Scaled dot-product attention: `softmax(QKᵀ/√d)V`
- The causal mask: position `t` may only attend to positions `≤ t`
- A transformer block = attention + feed-forward, with residuals and normalization

**Example: single-head causal attention, with a causality proof**

```python
import torch

def causal_attention(x, Wq, Wk, Wv):
    """Single-head scaled dot-product attention with a causal mask."""
    T, d = x.shape
    q, k, v = x @ Wq, x @ Wk, x @ Wv            # (T, d) each
    scores = q @ k.T / d**0.5                   # (T, T)
    mask = torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)
    scores = scores.masked_fill(mask, float("-inf"))  # future positions banned
    weights = torch.softmax(scores, dim=-1)
    return weights @ v                          # (T, d)

T, d = 6, 8
x = torch.randn(T, d)
Wq = torch.randn(d, d) * 0.3
Wk = torch.randn(d, d) * 0.3
Wv = torch.randn(d, d) * 0.3

out = causal_attention(x, Wq, Wk, Wv)
assert out.shape == (T, d)

# The causal property, checked not claimed: changing a FUTURE token must
# not change EARLIER outputs. Position 0 sees only itself, whatever
# happens at positions 1+.
x2 = x.clone()
x2[3] = torch.randn(d)                          # corrupt a future position
out2 = causal_attention(x2, Wq, Wk, Wv)
assert torch.allclose(out[:3], out2[:3], atol=1e-6)
print("causal: outputs at positions 0-2 unchanged when token 3 changes")
```

If the `assert` surprises you, trace the mask: row `t` of the score matrix only has finite entries for columns `≤ t`. Multi-head variants, positional encodings, and the full block are 2401/Phase 3 territory — this prerequisite is the shape-and-masking intuition.

**If you're not familiar:**
- Review: [Attention Is All You Need](https://arxiv.org/abs/1706.03762), Section 3.2
- Practice: Remove the mask line and watch the causality assert fail — then explain why
- Estimated time: 2 hours

---

### 5. Data Processing Basics

**What you should know:**
- Cleaning and filtering (length, language, quality heuristics)
- Deduplication — and why duplicates bias evaluation
- Formatting text into fixed-length token blocks for training

**Example: exact-match deduplication**

```python
raw_pages = [
    "The quick brown fox jumps.",
    "The quick brown fox jumps!",       # punctuation variant
    "Contact us at 555-0100 for details.",
    "The quick brown fox jumps.",       # exact duplicate
    "Lorem ipsum dolor sit amet.",
]

def normalize(text):
    return " ".join(text.lower().split())

seen, kept, dropped = set(), [], 0
for page in raw_pages:
    key = normalize(page)
    if key in seen:
        dropped += 1
    else:
        seen.add(key)
        kept.append(page)

print(f"kept {len(kept)}, dropped {dropped}")
# -> kept 4, dropped 1
# The '!' variant survives here - exact-match dedup only catches
# identical normalized strings. Near-duplicate detection (MinHash,
# embedding similarity) is a 2401 topic, as is the full cleaning
# pipeline: length filters, language IDs, quality classifiers.
```

**If you're not familiar:**
- Review: [Speech and Language Processing](https://web.stanford.edu/~jurafsky/slp3/) (Jurafsky & Martin), the corpus-processing chapter
- Practice: Add a minimum-length filter and a near-duplicate rule (e.g. drop pages sharing 90% of tokens with an already-kept page)
- Estimated time: 1 hour

---

### 6. Distributed Training Primer (Helpful, not required)

**What you should know:**
- `rank` (this worker's id) and `world_size` (worker count)
- The backend choice: `gloo` (CPU) vs `nccl` (GPU)
- Collectives — `all_reduce`, `broadcast` — the primitives DDP/FSDP are built from

**Example: a single-process torch.distributed launch**

```python
import os
import torch
import torch.distributed as dist

# torchrun sets these env vars for each worker; for a no-hardware tour
# we fake a 1-worker launch. Works on a laptop, no GPU needed.
os.environ.setdefault("MASTER_ADDR", "127.0.0.1")
os.environ.setdefault("MASTER_PORT", "29500")
os.environ.setdefault("RANK", "0")
os.environ.setdefault("WORLD_SIZE", "1")

dist.init_process_group(backend="gloo")
print(f"rank {dist.get_rank()} of world_size {dist.get_world_size()}")

# The collective to know now: all_reduce sums a tensor across all ranks
# (gradient averaging in DDP is exactly this, per parameter).
t = torch.tensor([1.0])
dist.all_reduce(t)      # 1 worker: nothing to sum, value unchanged
dist.destroy_process_group()
```

Everything in 2402 that needs real multi-GPU hardware is marked there; the concepts (rank, world_size, collectives) are what this primer establishes.

**If you're not familiar:**
- Review: the PyTorch distributed docs (torch.distributed overview)
- Practice: Run the block, then explain what `all_reduce` would return with `world_size=4` and every rank holding `rank+1`
- Estimated time: 1 hour

---

## Quick Refresher

### Cross-entropy is negative log-likelihood

```python
import torch
import torch.nn.functional as F

logits = torch.tensor([2.0, 1.0, 0.1])
target = 0

log_probs = F.log_softmax(logits, dim=-1)
ce = -log_probs[target]
manual = torch.logsumexp(logits, dim=-1) - logits[target]
assert torch.allclose(ce, manual, atol=1e-6)
print(f"cross-entropy {ce:.4f} == logsumexp - logit[target] {manual:.4f}")
# ~0.417 here: the correct class had probability ~0.66, -ln(0.66) = 0.42
```

### Warmup + cosine decay, the default LLM schedule

```python
import math

def lr_at(step, total, warmup, peak=3e-4, min_ratio=0.1):
    """Linear warmup, then cosine decay to min_ratio * peak."""
    if step < warmup:
        return peak * (step + 1) / warmup
    progress = (step - warmup) / max(1, total - warmup)
    return peak * (min_ratio + (1 - min_ratio) * 0.5 * (1 + math.cos(math.pi * progress)))

print([f"{lr_at(s, 100, 10):.2e}" for s in (0, 9, 10, 55, 99)])
# -> ['3.00e-05', '3.00e-04', '3.00e-04', '1.65e-04', '3.01e-05']
```

### Gradient accumulation

```python
import torch

torch.manual_seed(0)
model = torch.nn.Linear(4, 1)
opt = torch.optim.SGD(model.parameters(), lr=0.1)
accum_steps = 4

micro_batches = [(torch.randn(8, 4), torch.randn(8, 1)) for _ in range(8)]
w_before = model.weight.detach().clone()

for i, (xb, yb) in enumerate(micro_batches, 1):
    loss = torch.nn.functional.mse_loss(model(xb), yb) / accum_steps
    loss.backward()                     # gradients accumulate across micro-batches
    if i % accum_steps == 0:
        opt.step()                      # one optimizer step per `accum_steps`
        opt.zero_grad()

assert not torch.equal(model.weight, w_before)
print("2 optimizer steps from 8 micro-batches; effective batch = 16")
```

---

## Self-Assessment

Before starting, can you:

- [ ] Explain what cross-entropy loss measures and compute it for a batch of logits?
- [ ] Describe how Adam differs from SGD?
- [ ] Build a vocabulary and encode/decode text with it?
- [ ] State the causal shift in next-token prediction (what the inputs and targets are)?
- [ ] Implement single-head scaled dot-product attention with a causal mask?
- [ ] Deduplicate a small corpus and say what exact dedup misses?
- [ ] Train a model with a train/val split and recognize overfitting?
- [ ] Initialize a `torch.distributed` process group and name the two backends?

**If you answered NO to any question:**
Review the suggested materials above. Total review time: 9 hours

**If you answered YES to all questions:**
You're ready! Start with [2401: Pre-training Fundamentals](./2401-Pre-training-Fundamentals.md)

---

## Estimated Preparation Time

- **If familiar with prerequisites:** 0 hours (ready to start)
- **If need review:** 9 hours (2 + 1.5 + 1.5 + 2 + 1 + 1, spread over 2-3 days)

---

## Common Gaps

### Gap 1: Never trained a model from scratch

**Symptoms:** Only ever called pretrained models; unclear on what the optimizer actually does

**Fix:**
1. Run the Section 1 loop (30 minutes)
2. Swap Adam for SGD, then tune the learning rate until it trains (1 hour)
3. Break it on purpose: shuffle the split labels, watch validation accuracy collapse

### Gap 2: Attention shapes and causality are fuzzy

**Symptoms:** Can recite "softmax(QKᵀ/√d)V" but can't say what the mask does to the score matrix

**Fix:**
1. Run the Section 4 block; print the weights matrix and find the -inf pattern (1 hour)
2. Remove the mask, watch the causality assert fail (30 minutes)
3. Rederive the (T, d) shapes for q/k/v by hand

### Gap 3: Never cleaned data at scale

**Symptoms:** Never built a dedup/filter pipeline; assume "the dataset comes clean"

**Fix:**
1. Run the Section 5 dedup (30 minutes)
2. Add a near-duplicate rule and a length filter (30 minutes)

### Gap 4: Never used torch.distributed

**Symptoms:** The words rank/world_size/all_reduce don't conjure a picture

**Fix:**
1. Run the Section 6 primer (30 minutes)
2. Answer the practice question: 4 ranks holding rank+1 → all_reduce yields 10 (30 minutes)

---

## Preparation Checklist

Use this checklist to verify you're ready:

**ML Fundamentals**
- [ ] Can train a model with CrossEntropyLoss + Adam
- [ ] Split train/val before training, and know why
- [ ] Recognize overfitting from the loss gap

**Tokenization & LM Objective**
- [ ] Can build a vocab and encode/decode with `<unk>` handling
- [ ] Know the causal shift: inputs `[:-1]`, targets `[1:]`
- [ ] Can compute perplexity from loss

**Attention**
- [ ] Can implement scaled dot-product attention
- [ ] Know what the causal mask does to the score matrix
- [ ] Can name the shapes of q, k, v and the output

**Data**
- [ ] Can deduplicate a corpus (exact match)
- [ ] Know what exact dedup misses

**Distributed (helpful)**
- [ ] Know rank vs world_size
- [ ] Know gloo vs nccl
- [ ] Know what `all_reduce` computes

---

## Summary

- Module 2400 assumes **ML fundamentals, PyTorch fluency, the LM objective, attention mechanics, and data handling** — plus helpful distributed-training vocabulary.
- Each area ships a runnable example (train/val loop, word-level tokenizer, shifted next-token loss, causal attention with a causality assert, exact dedup, single-process `torch.distributed`) — run them, don't just read them.
- **Full review takes 9 hours** (2 + 1.5 + 1.5 + 2 + 1 + 1); a quick skim of this guide takes ~30 minutes.
- Use the Self-Assessment to find your gaps; Common Gaps gives a fix plan per gap.
- Everything here is exercised again at scale in the module: tokenization becomes BPE training in 2401, the training loop becomes DDP/FSDP in 2402, and the validation discipline becomes an evaluation framework in 2403.

---

## References

### Related Documents

- [2400: LLM Pretraining](./README.md) — module overview and learning path
- [2201: PyTorch Computational Graphs and Dynamic Execution](../2200-frameworks/2201-PyTorch-Computational-Graphs.md) — deeper PyTorch review (Section 1)
- [2401: Pre-training Fundamentals](./2401-Pre-training-Fundamentals.md) — where tokenization and data pipelines go deep (Sections 2, 5)
- [2400: Pretraining Fundamentals - Quiz](./assessment/QUIZ.md) — where this knowledge gets checked
- [Quick Start Troubleshooting Guide](../../../00-META/TROUBLESHOOTING-QUICKSTART.md) — when setup problems block you

### External References

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) — Vaswani et al.; Section 3.2 is the attention reference (Section 4)
- [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165) — Brown et al.; the objective from Section 3, at scale
- [Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556) — Hoffmann et al.; token budgets worth knowing before you spend GPU-hours
- [Hugging Face LLM Course](https://huggingface.co/learn/llm-course) — tokenization chapter (Section 2)
- [Speech and Language Processing](https://web.stanford.edu/~jurafsky/slp3/) — Jurafsky & Martin, 3rd ed. draft; n-gram LMs, perplexity, corpus processing

---

## Next Steps

1. **Gaps found?** Work the fix plans in [Common Gaps](#common-gaps), then re-run the [Self-Assessment](#self-assessment).
2. **Ready?** Start the module with [2401: Pre-training Fundamentals](./2401-Pre-training-Fundamentals.md).
3. **After the module:** take the [2400: Pretraining Fundamentals - Quiz](./assessment/QUIZ.md), then the [2400: Pre-training - Practice](./assessment/PRACTICE.md).

**Related:** [2400: LLM Pretraining](./README.md) · [2201: PyTorch Computational Graphs and Dynamic Execution](../2200-frameworks/2201-PyTorch-Computational-Graphs.md) · [2401: Pre-training Fundamentals](./2401-Pre-training-Fundamentals.md)

**Experiment:** No EXP_24xx exists yet — nearest relevant: [EXP-2201: PyTorch Computational Graphs](../../../../experiments/EXP_2201_PYTORCH_GRAPHS.md) (the autograd mechanics behind every training loop above).
