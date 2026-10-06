---
Document ID: 6104
Title: "6104: Embedding Sciences - Pooling, Matryoshka, and MTEB"
Phase: 6
Module: 6100
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'embeddings', 'matryoshka', 'mteb']
---

# 6104: Embedding Sciences - Pooling, Matryoshka, and MTEB

## Abstract

Between the tokenizer and the vector store stand three decisions the curriculum jumps over, and each one silently sets the ceiling on everything downstream. Pooling decides which tokens become the vector — and reading the position-0 slot because it is labeled CLS can throw away almost all of the signal a mean pool would keep. Matryoshka training decides which dimensions you may drop — a 1536-dim embedding truncated to 256 keeps its quality only because the model was trained with an importance ordering over its own dimensions; truncate an unordered embedding and recall collapses to chance. The benchmark menu decides what "better" even means — an embedding leaderboard mean is a function of the task list behind it, and one added task can flip the winner. The module's own QUIZ admits the gap this lesson fills: mean pooling, matryoshka truncation, and MTEB's task-menu benchmarking are taught nowhere in the curriculum — 6102 teaches the cosine these vectors are scored with, 6101 teaches the index they are stored in, 6202 teaches the reranker that rescores them; the vector itself, its length, and its report card live here.

---

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [Pooling: Which Tokens Become the Vector](#pooling-which-tokens-become-the-vector)
- [Matryoshka Representation Learning](#matryoshka-representation-learning)
- [Adaptive Retrieval: The Two-Stage Shortcut](#adaptive-retrieval-the-two-stage-shortcut)
- [The Storage Ledger](#the-storage-ledger)
- [Reading MTEB Without Being Fooled](#reading-mteb-without-being-fooled)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Diagnose pooling failures — a CLS-only readout scoring 6/18 on a three-topic separation the mean pool gets 18/18, because the position-0 slot carries a constant bias no downstream layer removes
- Honor the attention mask — naive mean pooling over a padded batch (divide by the padded length, count the pads as evidence) drops to 14/18 while the masked mean holds 18/18 on the identical batch
- Truncate matryoshka embeddings safely — recall@5 at 16 of 64 dims equal to the full-dim result because importance was trained into the dimension order; the shuffled-order control at 0.00 shows truncation is only free when the ordering was learned
- Run two-stage adaptive retrieval — a 16-dim shortlist over 5,000 documents losing nothing (recall@10 of 1.0 and exact top-10 agreement on all 25 queries) at 0.145 of the exhaustive multiply-adds
- Price the embedding before shipping it — the fp32/int8 ledger from 0.26 GB (64 dims) to 6.14 GB (1536 dims) per million documents, and the 0.83 of the fp32 bill that truncating 1536→256 deletes
- Read MTEB as a menu, not a verdict — the mini-benchmark where adding one task flips the winner from A to B, the arithmetic behind every leaderboard row you quote

**Estimated Time:** 3 hours

---

## Pooling: Which Tokens Become the Vector

An embedding model runs a transformer over tokens and then collapses the per-token states into one vector. The collapse rule is a modeling decision with its own failure modes, and it is printed nowhere except the model card. Three rules cover the field: the CLS readout (take the position-0 slot), mean pooling (average the token states), and the mask discipline that separates a correct mean from a quietly wrong one. The toy below separates three topics in 8 dimensions, then installs a constant bias in the position-0 slot of every document — the toy's stand-in for a CLS token whose slot carries training artifacts rather than sentence meaning:

```python
import numpy as np

rng1 = np.random.default_rng(0)
d, n_docs, n_tok = 8, 18, 5
topics = rng1.normal(size=(3, d))
topics /= np.linalg.norm(topics, axis=1, keepdims=True)

docs = np.empty((n_docs, n_tok, d))
labels = []
for i in range(n_docs):
    t = i % 3
    labels.append(t)
    docs[i] = topics[t] + 0.05 * rng1.normal(size=(n_tok, d))
labels = np.array(labels)

# the position-0 slot: a constant bias for every doc - carries no topic signal
cls_bias = rng1.normal(size=d)
docs[:, 0, :] = cls_bias + 0.01 * rng1.normal(size=(n_docs, d))

def cos(a, b):
    return a @ b.T / (np.linalg.norm(a, axis=1, keepdims=True) * np.linalg.norm(b, axis=1))

def accuracy(pooled):
    return int((cos(pooled, topics).argmax(1) == labels).sum())

cls = docs[:, 0, :]                        # CLS-only readout
mean5 = docs.mean(axis=1)                  # mean over the 5 real tokens

# a padded batch: 3 real tokens + 2 PAD tokens holding noise, as real pad
# positions do once embeddings are looked up - they are not zeros
docs_pad = np.concatenate([docs[:, :3, :], 1.0 * rng1.normal(size=(n_docs, 2, d))], axis=1)
naive = docs_pad.mean(axis=1)              # divides by 5 - pads counted
mask = np.array([1, 1, 1, 0, 0])
masked = (docs_pad * mask[None, :, None]).sum(axis=1) / mask.sum()   # divides by 3

print("CLS-only readout      :", accuracy(cls), "/", n_docs)
print("masked mean, 5 tokens :", accuracy(mean5), "/", n_docs)
print("naive padded mean     :", accuracy(naive), "/", n_docs)
print("masked padded mean    :", accuracy(masked), "/", n_docs)
```

The CLS readout classifies **6 of 18** — one worse than the 1-in-3 coin flip it should beat easily, because every document's readout is dominated by the same constant bias and the topics survive only in the 0.01 noise term. The mean pool over the same five states scores **18 of 18**: averaging washes the shared bias out of every document equally, and the topic signal, present in four of the five positions, wins the mean. Mean pooling is not a convention; it is a robustness property.

The second half of the fence is the trap that bites in production. A real batch is padded to its longest sequence, and looked-up PAD embeddings are noise, not zeros. The naive mean divides by 5 and counts two PAD tokens as evidence: **14 of 18**, three documents misrouted by noise they never contained. The masked mean multiplies by the mask, sums, and divides by the mask sum — **18 of 18** on the identical batch. Same model, same data, same code except one division.

```text
masked mean:  pooled = ( Σ_i m_i·e_i ) / Σ_i m_i          m_i ∈ {0, 1}
CLS readout:  pooled = e_0                                the position-0 slot
```

Sentence-transformers encodes this decision in each model's `modules` (a `Pooling` layer configured with `pooling_mode_mean_tokens` versus `pooling_mode_cls_token`), and `encode(..., normalize_embeddings=True)` renormalizes the pooled output onto the unit sphere — the geometry 6102's cosines assume. Check which rule your model ships with before assuming either.

---

## Matryoshka Representation Learning

Pooling fixes the vector's origin; training fixes its length. A conventional embedding's dimensions are interchangeable — position 12 is no more important than position 1200, and truncating such a vector is destruction. Matryoshka Representation Learning (Kusupati et al., 2022) trains the model so that every prefix of the embedding is a usable embedding: the loss is evaluated at several prefix lengths simultaneously, which forces importance into the dimension order — the coarse structure migrates to the front, the fine detail to the tail. The toy below builds a 64-dim space whose importance decays geometrically with the dimension index (the trained ordering) and compares truncating it against truncating the same vectors under a random permutation of dimensions (the untrained ordering):

```python
import numpy as np

rng2 = np.random.default_rng(1)
N, D = 400, 64
centers = rng2.normal(size=(4, 4))
coarse = centers[np.arange(N) % 4] + 0.35 * rng2.normal(size=(N, 4))
fine = rng2.normal(size=(N, D - 4)) * 0.05
X = np.concatenate([coarse, fine], axis=1)

w = 0.75 ** np.arange(D)                   # importance decays with dim index
E = X * w
E /= np.linalg.norm(E, axis=1, keepdims=True)

Q = centers + 0.05 * rng2.normal(size=(4, 4))
Qe = np.concatenate([Q, 0.01 * rng2.normal(size=(4, D - 4))], axis=1) * w
Qe /= np.linalg.norm(Qe, axis=1, keepdims=True)

def recall_at5(Em, Qm, k):
    Et = Em[:, :k] / np.linalg.norm(Em[:, :k], axis=1, keepdims=True)
    Qt = Qm[:, :k] / np.linalg.norm(Qm[:, :k], axis=1, keepdims=True)
    got = np.argsort(-(Qt @ Et.T), axis=1)[:, :5]
    return np.mean([len(set(got[i]) & set(truth[i])) / 5 for i in range(4)])

truth = np.argsort(-(Qe @ E.T), axis=1)[:, :5]
perm = np.random.default_rng(2).permutation(D)     # untrained dim order
print(" k    trained order   shuffled order")
for k in (4, 8, 16, 32, 64):
    print(f"{k:3d}        {recall_at5(E, Qe, k):.2f}            "
          f"{recall_at5(E[:, perm], Qe[:, perm], k):.2f}")
```

The trained order truncates for free: **0.95** recall@5 at 4 of 64 dims, **1.00** from 8 dims up — 16 dims, a quarter of the storage, is indistinguishable from the full vector on this task. The shuffled order is the control that makes the point: **0.00 at every k below 64**. The information is all still there in the permuted matrix — recall at the full 64 dims is 1.00 — but no prefix of it is a usable embedding, because importance was scattered instead of ordered. Truncation is not a property of vectors; it is a property of orderings, and the ordering is bought with the multi-prefix loss.

```text
truncated view:  e[:k] / ||e[:k]||                        renormalized prefix
MRL loss:        L = Σ_k L_task(e[:k])                    one loss per prefix
```

The production surfaces expose exactly this. `nomic-ai/nomic-embed-text-v1.5` ships with `matryoshka_dim=64` as its shortest usable length; sentence-transformers models accept `truncate_dim` both at load time and per `encode` call (the per-call value wins); OpenAI's `text-embedding-3-small` takes a `dimensions` parameter down to 1 of its native 1536. Every one of them works only because the model was trained with an MRL-style objective — the model card names it, and the shuffled row of the fence is what happens when you assume it of a model that wasn't.

---

## Adaptive Retrieval: The Two-Stage Shortcut

The ordering buys more than storage. If the front of the vector carries the coarse structure, then a cheap prefix-only similarity can nominate a shortlist that a full-dim rescore finalizes — retrieval at a fraction of the arithmetic. This is the same over-fetch-then-rescore shape 6202 teaches for cross-encoders, applied one level down, to the embedding itself:

```python
import numpy as np

rng3 = np.random.default_rng(3)
N3, d_full, d_short, shortlist = 5000, 128, 16, 100
X3 = rng3.normal(size=(N3, d_full))
w3 = 0.95 ** np.arange(d_full)             # importance decays with dim index
E3 = X3 * w3
E3 /= np.linalg.norm(E3, axis=1, keepdims=True)

q3 = E3[rng3.choice(N3, 25, replace=False)] + 0.02 * rng3.normal(size=(25, d_full))
q3 /= np.linalg.norm(q3, axis=1, keepdims=True)

truth = np.argsort(-(q3 @ E3.T), axis=1)[:, :10]          # exhaustive top-10

# stage 1: shortlist on the 16-dim prefix
Es = E3[:, :d_short] / np.linalg.norm(E3[:, :d_short], axis=1, keepdims=True)
qs = q3[:, :d_short] / np.linalg.norm(q3[:, :d_short], axis=1, keepdims=True)
short = np.argsort(-(qs @ Es.T), axis=1)[:, :shortlist]

# stage 2: full-dim rescore of the 100 survivors
final = np.empty((25, 10), dtype=int)
for i in range(25):
    scores = E3[short[i]] @ q3[i]
    final[i] = short[i][np.argsort(-scores)[:10]]

r10 = np.mean([len(set(final[i]) & set(truth[i])) / 10 for i in range(25)])
exact = np.mean([set(final[i]) == set(truth[i]) for i in range(25)])
work = (N3 * d_short + shortlist * d_full) / (N3 * d_full)
print("recall@10 vs exhaustive:", round(r10, 3))
print("exact top-10 agreement :", round(float(exact), 3))
print("work ratio             :", round(work, 3), "->", round(1 / work, 1), "x fewer multiply-adds")
```

The two-stage pipeline loses nothing on this corpus: **recall@10 of 1.0** against the exhaustive scan and **exact top-10 agreement on all 25 queries** — the final list is the exhaustive list, not a good approximation of it. The price was **0.145** of the exhaustive multiply-adds (5,000 prefix scores plus 100 full rescores against 5,000 full scores), **6.9× fewer**. The shortlist bound matters more than the prefix length here: with the shortlist at 100 of 5,000, stage 2 is a rounding error, which is why 6101's ANN indexes and this trick compose rather than compete — the index nominates the pool, the prefix narrows it, the full vector finalizes it.

---

## The Storage Ledger

Truncation and quantization are the two levers on the same bill, and the bill is linear in dimensionality. One million documents, fp32 at 4 bytes per component, int8 at 1:

```python
print("dims    fp32 (4 B/comp)   int8 (1 B/comp)")
for k in (64, 128, 256, 768, 1536):
    print(f"{k:5d}      {k*4e-3:5.2f} GB            {k*1e-3:4.2f} GB")
print("truncating 1536 -> 256 deletes", round((1536 - 256) / 1536, 2), "of the fp32 bill")
```

A 1536-dim fleet costs **6.14 GB** per million documents in fp32 — the difference between a vector column that fits beside the documents and one that needs its own storage tier. Truncating to 256 deletes **0.83 of the fp32 bill** outright; int8 quantization is an orthogonal **4×** that stacks with any dimensionality (6401's Qdrant quantization configs are this ledger with knobs). The two levers are not interchangeable: truncation requires a matryoshka-trained model and changes what the vector can express, while quantization keeps all the information and changes how precisely it is stored. The order of operations matters — truncate first (on the trained ordering), then quantize the truncated vector, then normalize if your index scores cosine.

---

## Reading MTEB Without Being Fooled

The last science is the report card. MTEB — the Massive Text Embedding Benchmark (Muennighoff et al., 2022) — scores embeddings across dozens of tasks grouped into families: STS (semantic textual similarity), clustering, retrieval, classification, pairing, reranking, summarization. Leaderboard rows publish a mean, and the mean hides the menu: which tasks were averaged is a modeling decision, and the winner can depend on it. The toy builds two embedders and a four-task menu. A reads the dims where the first three tasks live; B reads most of A's world plus the dims that carry the fourth task's labels:

```python
import numpy as np

rng5 = np.random.default_rng(5)
M = 200
feat = rng5.normal(size=(M, 32))

# two embedders with shifted feature support: A reads dims :16 (where the
# first three tasks live), B reads dims 4:24 - most of A's world plus the
# topic dims 16:20 that the fourth task's labels live in
A = feat[:, :16] @ rng5.normal(size=(16, 96))
B = feat[:, 4:24] @ rng5.normal(size=(20, 96))
A /= np.linalg.norm(A, axis=1, keepdims=True)
B /= np.linalg.norm(B, axis=1, keepdims=True)

def sts(E):
    sims = (E[0::2] * E[1::2]).sum(1)
    gold = 1.0 / (1.0 + np.linalg.norm(feat[:, :16][0::2] - feat[:, :16][1::2], axis=1))
    ra, ga = np.argsort(np.argsort(sims)), np.argsort(np.argsort(gold))
    return float(np.clip(1 - np.mean(np.abs(ra - ga)) / (M // 2 - 1) * 2, 0, 1))

def clustering(E):
    cent = np.stack([E[np.arange(M) % 4 == c].mean(0) for c in range(4)])
    cent /= np.linalg.norm(cent, axis=1, keepdims=True)
    return float(np.mean((E @ cent.T).argmax(1) == np.arange(M) % 4))

def retrieval(E):
    hits = []
    for i in range(40):
        sims = E[i] @ E.T
        sims[i] = -9
        dists = np.linalg.norm(feat[:, :16] - feat[i, :16], axis=1)
        dists[i] = 9
        rel = set(np.argsort(dists)[:10])
        hits.append(len(rel & set(np.argsort(-sims)[:10])) / 10)
    return float(np.mean(hits))

topics5 = feat[:, 16:20].argmax(1)   # the fourth task's labels live in B's extra dims
def classification(E):
    cent = np.stack([E[topics5 == c].mean(0) for c in range(4)])
    cent /= np.linalg.norm(cent, axis=1, keepdims=True)
    return float(np.mean((E @ cent.T).argmax(1) == topics5))

tasks = {"STS": sts, "Clustering": clustering,
         "Retrieval": retrieval, "Classification": classification}
sa = {t: f(A) for t, f in tasks.items()}
sb = {t: f(B) for t, f in tasks.items()}
print("task             A       B")
for t in ("STS", "Clustering", "Retrieval", "Classification"):
    print(f"{t:<15}{sa[t]:.3f}  {sb[t]:.3f}")
m3 = {m: np.mean([s[t] for t in ("STS", "Clustering", "Retrieval")]) for m, s in (("A", sa), ("B", sb))}
print("3-task mean      %.3f  %.3f  -> %s wins" % (m3["A"], m3["B"], max(m3, key=m3.get)))
m4 = {m: (m3[m] * 3 + s["Classification"]) / 4 for m, s in (("A", sa), ("B", sb))}
print("4-task mean      %.3f  %.3f  -> %s wins" % (m4["A"], m4["B"], max(m4, key=m4.get)))
```

A wins the three-task menu at **0.552 vs 0.441** — it takes STS (0.675 vs 0.594) and Retrieval outright (0.580 vs 0.305) and only concedes Clustering by a hair. Then one task joins the menu. Classification lives in dims 16:20, which A cannot see (0.355) and B reads plainly (0.810) — and the four-task mean flips the verdict to B, **0.534 vs 0.502**, even though B still loses two of the four tasks and lost the three-task mean by eleven points. Nothing about either embedder changed; the menu did. This is the arithmetic behind every "model X beats model Y" row: the mean is a function of the task list, and MTEB's value is the per-task table it forces into the open, not the single number its leaderboard sorts by. Quote means only alongside the menu that produced them, and benchmark your own task mix before letting a leaderboard pick your embedder.

---

## Known Failure Modes

| # | Symptom | Cause | Fix |
|---|---------|-------|-----|
| 1 | CLS-slot readout underperforms a trivial baseline | The position-0 slot carries training artifacts, not sentence meaning, on pooling models | Mean-pool with the mask, or read the model card's pooling config before choosing |
| 2 | Batch-size changes quality slightly | Padded batch mean-pooled without the mask — PAD rows counted as evidence | Multiply by the mask, sum, divide by `mask.sum()`; never divide by the padded length |
| 3 | Truncated a non-matryoshka embedding, recall collapsed | Dimensions are not importance-ordered; no prefix is a usable embedding (the shuffled control scores 0.00) | Truncate only models trained with an MRL-style objective; the model card names it |
| 4 | Truncated vectors score worse than they should | Prefix renormalization forgotten — the prefix's norm is below 1, distorting cosine | Renormalize `e[:k]` to unit length before any similarity computation |
| 5 | `truncate_dim` had no effect | The per-call value overrides the load-time value, but some wrappers drop the kwarg | Pass `truncate_dim` at `encode` time (it wins) and verify output shape in a test |
| 6 | int8 quantization wrecked one embedding class | Outlier components eat the per-dim int8 range | Normalize first, then quantize with per-dim calibration; 6401's scalar/binary quantization configs |
| 7 | Leaderboard mean picked the embedder, production disagrees | The mean is a function of the task menu; one added task flips the winner | Compare per-task numbers on your own task mix; treat menu choice as a modeling decision |
| 8 | Queries and documents stopped matching after a dim change | Query and document truncated to different lengths or embedded by different models | One model, one dimension policy on both sides — 6102's shared-space requirement |

---

## Summary

An embedding is three decisions stacked on a transformer. Pooling decides which token states become the vector: the CLS readout can score 6/18 where the mean pool scores 18/18, and the mask discipline is the difference between 14/18 and 18/18 on the identical padded batch — one division. Matryoshka training decides which dimensions you may drop: recall@5 holds at 1.00 from 16 of 64 dims because the multi-prefix loss bought an importance ordering, and the shuffled control's 0.00 proves the ordering, not the vector, is the property that truncates. The ordering also buys two-stage retrieval — a 16-dim shortlist and a 100-candidate rescore reproduce the exhaustive top-10 exactly at 0.145 of the multiply-adds — and the dimension count prices the fleet, 0.26 to 6.14 GB per million documents with the 1536→256 truncation deleting 0.83 of the fp32 bill before quantization's orthogonal 4×. And the benchmark mean that ranks embedders is a function of the task menu behind it: one added task flips a winner that was losing by eleven points, so MTEB's per-task table is the artifact to read, not the mean its leaderboard sorts by.

---

## References

### Related Minder Academy Documents

- [6102: Semantic Similarity Metrics](./6102-Semantic-Similarity.md) — the cosine geometry every pooled, truncated vector is scored with
- [6101: HNSW Indexing - Efficient Semantic Search at Scale](./6101-HNSW-Indexing.md) — the index that stores the truncated vectors and nominates the candidate pool
- [6103: HNSW Tuning Guide](./guides/6103-HNSW-Tuning-Guide.md) — tuning the index around the dimensionality you chose here
- [6202: Re-ranking and Retrieval Logistics](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) — the same over-fetch-then-rescore shape one abstraction up, at cross-encoder cost
- [6401: Qdrant Setup Guide](../6400-vector-databases/6401-Qdrant-Setup.md) — where the storage ledger meets a deployment: scalar and binary quantization configs
- [3202: Tokenizer Sciences - BPE, SentencePiece, and Tiktoken](../../phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md) — the token side of the same pipeline, upstream of pooling

### Primary Sources

- Kusupati, A., et al. (2022). *Matryoshka Representation Learning*. NeurIPS 2022 (arXiv:2205.13147) — the multi-prefix objective that buys importance-ordered dimensions
- Muennighoff, N., et al. (2022). *MTEB: Massive Text Embedding Benchmark* (arXiv:2210.07316) — the task families and the per-task table behind every leaderboard mean
- sentence-transformers documentation — `Pooling` module configuration, `truncate_dim` (load-time and per-`encode`), and the Matryoshka training example with `MatryoshkaLoss`
- OpenAI — Embeddings guide: the `dimensions` parameter on `text-embedding-3-small` (native 1536) and `text-embedding-3-large` (native 3072)

---

## Next Steps

- **Next Module:** [6200: Retrieval Strategies](../6200-retrieval/README.md) — hybrid fusion and the query-side levers the vectors you just sized feed
- **Continue with:** [6201: Hybrid Search - Combining Keyword and Semantic Search](../6200-retrieval/6201-Hybrid-Search.md)
- **Assessment:** [QUIZ](./assessment/QUIZ.md) — question 16 is this lesson's, and the pooling/matryoshka/MTEB review bullet now points here
- **Hands-on:** truncate your production embedder to 1/4 and 1/16 of its dims and measure recall on your own query log; put the per-task table next to every leaderboard mean you quote
