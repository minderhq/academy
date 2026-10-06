---
Document ID: 6105
Title: "6105: Contextual and Multilingual Embeddings - Anisotropy, Alignment, and the Shared Space"
Phase: 6
Module: 6100
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'embeddings', 'multilingual']
---

# 6105: Contextual and Multilingual Embeddings - Anisotropy, Alignment, and the Shared Space

## Abstract

Two facts about embeddings decide whether a retrieval system works across senses and across languages, and the curriculum skips both. The first is that a contextual model does not produce a vector per word type — it produces a vector per token use, and the difference is the difference between a similarity score that cannot tell which sentence it is reading and one that moves the same word pair in both directions. The second is that independently trained languages do not share a space: raw cross-lingual similarity is meaningless until the spaces are aligned, and even a properly shared space can quietly keep encoding which language every vector came from. Around both facts sits anisotropy — the mean-dominated cone that raw transformer states occupy — which leaves every ranking intact and destroys every threshold. The module's own QUIZ admits the gap this lesson fills: the contextual-vs-static distinction and multilingual embedding spaces are taught nowhere in the curriculum — 6102 teaches the static word-embedding tradition and the cosine the vectors are scored with, 6104 teaches the pooling, matryoshka, and MTEB layer above, 6101 teaches the index below; the contextual states themselves and the geometry that must hold two languages at once live here.

---

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [One Vector per Type, One Vector per Use](#one-vector-per-type-one-vector-per-use)
- [Anisotropy: The Cone and the Collapsed Margin](#anisotropy-the-cone-and-the-collapsed-margin)
- [Alignment: Building the Shared Space](#alignment-building-the-shared-space)
- [The Language-Identity Probe](#the-language-identity-probe)
- [Three Stacks, One Query Set](#three-stacks-one-query-set)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Distinguish static from contextual embeddings — cos(deposit, bank) pinned at 0.707 in both sentences under the static type vector, reading 0.505 in the geology sentence and 0.910 in the finance one under the contextual blend, with the two uses of the same token agreeing at only 0.794
- Diagnose anisotropy before it eats your thresholds — a mean-dominated cone pushing all 19,890 unrelated pairs above 0.9 raw, and mean-centering dropping them to −0.005 while related pairs hold 0.759
- Price the retrieval margin anisotropy costs — a partner-vs-competitor margin of 0.0100 raw against 0.3939 centered on the identical corpus
- Build a cross-lingual shared space — unaligned cross-lingual retrieval at 0/4 rising to 4/4 under the orthogonal Procrustes map (residual 0.4297, orthogonality error 1e-15)
- Probe a "multilingual" space for language identity — rankings that survive (6/6 and 6/6) while the score bands split 0.997 vs −0.128 and a linear probe reads the language off the vector at 12/12 (5/12, chance, without it)
- Price the three retrieval stacks — a mono index at 0/4 on foreign queries, translate-then-retrieve at 3/4 with the lost query down 0.112, the shared space at 4/4

**Estimated Time:** 3 hours

---

## One Vector per Type, One Vector per Use

6102's tradition — Word2Vec, GloVe — assigns each word type one vector, estimated from the contexts it appeared in during training and then frozen. A contextual encoder keeps the same vocabulary but emits a different vector for every occurrence: the output at each position is a function of the whole sentence, not of the type. The toy below makes the distinction measurable. Four semantic axes stand in for the space's content directions; the static type vector for *bank* is fixed halfway between the finance and river axes (both senses averaged into one point, exactly the compromise a type-level table must make), and the contextual vector of a word is its type vector blended with the mean of its sentence-mates at strength γ = 0.6:

```python
import numpy as np

# toy 4-dim semantic axes: [finance, river, leisure, formal]
AX = {
    "finance": np.array([1.0, 0.0, 0.0, 0.0]),
    "river":   np.array([0.0, 1.0, 0.0, 0.0]),
    "leisure": np.array([0.0, 0.0, 1.0, 0.0]),
    "formal":  np.array([0.0, 0.0, 0.0, 1.0]),
}
TYPE = {  # static type vectors: 'bank' sits BETWEEN its two senses
    "river":   AX["river"],
    "bank":    0.5 * AX["finance"] + 0.5 * AX["river"],
    "walk":    AX["leisure"],
    "deposit": AX["finance"],
    "loan":    AX["finance"],
}
S1 = ["river", "bank", "walk"]      # geology sentence
S2 = ["bank", "deposit", "loan"]    # finance sentence

def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

q = TYPE["deposit"]
print(f"static cos(deposit, bank) in S1  : {cos(q, TYPE['bank']):.3f}")
print(f"static cos(deposit, bank) in S2  : {cos(q, TYPE['bank']):.3f}")

GAMMA = 0.6
def ctx(word, sent):
    others = [TYPE[w] for w in sent if w != word]
    return TYPE[word] + GAMMA * np.mean(others, axis=0)

b1, b2 = ctx("bank", S1), ctx("bank", S2)
print(f"contextual cos(deposit, bank|S1) : {cos(q, b1):.3f}")
print(f"contextual cos(deposit, bank|S2) : {cos(q, b2):.3f}")
print(f"bank|S1 vs bank|S2 self-similarity: {cos(b1, b2):.3f} (the static type prints 1.000)")
```

The static type vector answers **0.707 in both sentences** — the same number twice, because the vector cannot see the query's sentence; *deposit* sits on the finance axis and *bank*'s type vector is at 45°, and that is all the geometry knows. The contextual vector splits the verdict: **0.505** in the geology sentence, where the river-mean drags *bank* away from the finance axis, and **0.910** in the finance sentence, where the deposit-and-loan mean pushes it on. The same word pair moves in both directions, and each reading is correct for its sentence. The last line is the deeper fact: the two uses of *bank* agree with each other at only **0.794** — a contextual model never emits the same vector twice for the same type, which is precisely what the static table's 1.000 forbids. Ethayarajh (2019) measured exactly this self-similarity across layers of real encoders and found it falling as depth grows — the contextualization the toy blends by hand is what the encoder's attention does at scale.

```text
static:     e(word)                            one vector per type, frozen
contextual: e(word | sent) = e(word) + γ·mean(e(sent \ word))   one per use
```

---

## Anisotropy: The Cone and the Collapsed Margin

Raw contextual states are not scattered over the sphere — they occupy a narrow cone: a dominant mean direction shared by every token plus small per-token deviations. The toy builds 200 vectors in that cone (each = one common mean + 0.15-scale noise) and marks 10 tight related pairs, then measures every pairwise cosine raw and after subtracting the mean:

```python
import numpy as np

rng = np.random.default_rng(22)
d, m = 64, 200
mu = rng.normal(size=d)
CONE = 0.15
V = mu + CONE * rng.normal(size=(m, d))          # narrow cone: common mean dominates
pairs = rng.choice(m, size=(10, 2), replace=False)
for a, b in pairs:                                # 10 tight related pairs, cone-scale noise
    V[b] = 0.9 * V[a] + 0.1 * CONE * rng.normal(size=d)

rel = set(map(frozenset, pairs))
def mean_pairwise(X):
    Xn = X / np.linalg.norm(X, axis=1, keepdims=True)
    S = Xn @ Xn.T
    iu = np.triu_indices(len(X), 1)
    return S[iu], iu

raw, iu = mean_pairwise(V)
rel_mask = np.array([frozenset((i, j)) in rel for i, j in zip(*iu)])
print(f"raw mean pairwise cosine, unrelated ({(~rel_mask).sum()} pairs): {raw[~rel_mask].mean():.3f}")
print(f"raw mean pairwise cosine, related   : {raw[rel_mask].mean():.3f}")
print(f"raw unrelated pairs above 0.9       : {(raw[~rel_mask] > 0.9).sum()}/{(~rel_mask).sum()}")

Vc = V - V.mean(axis=0)
cen, _ = mean_pairwise(Vc)
print(f"centered mean cosine, unrelated     : {cen[~rel_mask].mean():.3f}")
print(f"centered mean cosine, related       : {cen[rel_mask].mean():.3f}")
print(f"centered unrelated pairs above 0.9  : {(cen[~rel_mask] > 0.9).sum()}/{(~rel_mask).sum()}")

qidx_a, partner = pairs[0]
def sims_to_query(X, i):
    Xn = X / np.linalg.norm(X, axis=1, keepdims=True)
    return Xn @ Xn[i]

s_raw, s_cen = sims_to_query(V, qidx_a), sims_to_query(Vc, qidx_a)
s_raw[qidx_a] = s_cen[qidx_a] = -np.inf          # drop self
in_any_pair = np.zeros(m, bool)                   # competitors = vectors in NO related pair
in_any_pair[pairs.ravel()] = True
ok = ~in_any_pair; ok[qidx_a] = False; ok[partner] = False
print(f"query id {qidx_a}, true partner id {partner}, {ok.sum()} unrelated competitors")
print(f"raw     : sim(q,partner) {s_raw[partner]:.4f} vs best unrelated {s_raw[ok].max():.4f}  -> margin {s_raw[partner]-s_raw[ok].max():.4f}")
print(f"centered: sim(q,partner) {s_cen[partner]:.4f} vs best unrelated {s_cen[ok].max():.4f}  -> margin {s_cen[partner]-s_cen[ok].max():.4f}")
```

Raw, the corpus is degenerate: the mean pairwise cosine between **unrelated** vectors is **0.984**, and all **19,890** unrelated pairs sit above 0.9 — in this space, everything is similar to everything, and any absolute threshold ("score above 0.9 means related") fires on every pair in the corpus. The related pairs average 1.000 — in the same band as the noise, invisible to the scale. Mean-centering deletes the shared direction and the geometry reappears: unrelated drops to **−0.005**, related holds **0.759**, and the count of unrelated pairs above 0.9 falls from 19,890 to **0**. The margin line prices what anisotropy actually costs retrieval: the query's true partner beats its best unrelated competitor by **0.0100** raw — a hundredth-scale separation living inside the cone's own spread — and by **0.3939** centered, a tenth-scale separation with room to spare. Note what did not change: the partner was already ranked first raw. Anisotropy does not scramble rankings; it compresses the dynamic range until every threshold-based decision — dedup cutoffs, near-duplicate flags, similarity gates — is reading noise. This is why production pipelines center or whiten raw states before scoring (the all-but-the-top family: remove the mean and the top principal directions), and why 6104's pooled, normalized vectors — trained end-to-end for retrieval — are a different animal from the raw states this section models.

---

## Alignment: Building the Shared Space

Multilingual retrieval needs two models' vectors to live in one space, and two independently trained encoders give you two spaces related by nothing you can read off the architectures — in the toy, language B's space is an exact random rotation of language A's plus a little seed noise, which is the best case: a single orthogonal map *can* carry one onto the other. First the controls — monolingual retrieval inside A, and the naive cross-lingual attempt with no alignment at all:

```python
import numpy as np

rng = np.random.default_rng(33)
n_docs, d = 12, 32
E = rng.normal(size=(n_docs, d))                   # language-A embedding space
R = np.linalg.qr(rng.normal(size=(d, d)))[0]       # language-B's own pretraining rotation
B = E @ R + 0.05 * rng.normal(size=(n_docs, d))    # same 12 docs, language-B model, small seed noise

En = E / np.linalg.norm(E, axis=1, keepdims=True)
qidx = [0, 3, 5, 9]
hits = sum(int(np.argmax(En @ En[i])) == i for i in qidx)
print(f"monolingual control (A->A) top-1 : {hits}/{len(qidx)}")

Bn = B / np.linalg.norm(B, axis=1, keepdims=True)
hits = sum(int(np.argmax(En @ Bn[i])) == i for i in qidx)
print(f"cross-lingual, unaligned top-1   : {hits}/{len(qidx)}")

U, S, Vt = np.linalg.svd(E.T @ B)
W = U @ Vt                                         # orthogonal Procrustes: min ||E W - B||
print(f"Procrustes residual ||EW-B||_F   : {np.linalg.norm(E @ W - B):.4f}")
print(f"||W^T W - I|| max                : {np.abs(W.T @ W - np.eye(d)).max():.1e}")

ABn = (B @ W.T)
ABn = ABn / np.linalg.norm(ABn, axis=1, keepdims=True)   # E ~= B W^T, so W^T maps B-queries back
hits = sum(int(np.argmax(En @ ABn[i])) == i for i in qidx)
print(f"cross-lingual, aligned top-1     : {hits}/{len(qidx)}")
```

Monolingual control: **4/4** — the A space is healthy. Unaligned cross-lingual: **0/4** — A-queries against B-documents return noise, because the rotation scrambles every correspondence; nothing about raw cosine survives two independent trainings. The orthogonal Procrustes solution finds the best-fitting rotation in closed form: the SVD of EᵀB gives W = UVᵀ, the orthogonal matrix minimizing ‖EW − B‖ — here a residual of **0.4297** (the seed noise, not the rotation) and an orthogonality error of **1e-15**, machine precision. Because W is orthogonal, its inverse is its transpose: E ≈ B·Wᵀ, so B-side queries map back into A's space with one matrix multiply and retrieval recovers to **4/4**. The map is linear and rotation-only, which is both its power and its contract: it works when the two spaces are already near-isomorphic (parallel corpora give that), and it has no degrees of freedom to fix genuinely different geometries. This is the zero-training end of the multilingual spectrum; LaBSE (Feng et al., 2020) is the training-time end — a 109-language dual-encoder trained jointly with a margin-based translation-ranking objective over 8 billion translation pairs, lifting bitext retrieval precision from 65.5% (LASER, itself a fixed-mapping system) to 83.7% by building the shared space during pretraining rather than fitting a map afterward.

```text
W = argmin_{WᵀW=I} ||E W - B||  =  U Vᵀ,  SVD(Eᵀ B) = U Σ Vᵀ
A-space query x, B-space index: score = (x @ W) against B-documents
```

---

## The Language-Identity Probe

A model marketed as multilingual declares a shared space; the probe battery checks whether the space actually shares. The toy builds six meanings in two languages under two regimes: a "bad" space where every vector carries a strong additive language flag (meaning + 3.0·language-direction) and a "good" space with the flag removed. Four instruments: monolingual paraphrase retrieval (each A-document against the other A-documents and its own rephrasing twin), cross-lingual retrieval (A against B), the score bands (mean cosine of mono pairs vs cross pairs), and a linear probe — can the sign of a single direction recover each document's language?

```python
import numpy as np

rng = np.random.default_rng(44)
n_mean, d = 6, 32
mean_dirs = rng.normal(size=(n_mean, d))
lang_dirs = rng.normal(size=(2, d))

def build(beta):
    """per meaning: doc + same-language paraphrase twin; beta = language-flag strength"""
    X = []
    for mi in range(n_mean):
        for li in range(2):
            X.append(mean_dirs[mi] + beta * lang_dirs[li] + 0.2 * rng.normal(size=d))
            X.append(mean_dirs[mi] + beta * lang_dirs[li] + 0.2 * rng.normal(size=d))
    return np.array(X)

for beta, label in [(3.0, "bad"), (0.0, "good")]:
    X = build(beta)
    Xn = X / np.linalg.norm(X, axis=1, keepdims=True)
    # layout: [A-doc0, A-twin0, B-doc0, B-twin0, A-doc1, ...] -> stride 4
    mono_idx = [4 * mi + k for mi in range(n_mean) for k in (0, 1)]   # A-docs + their twins
    mono = 0
    for mi in range(n_mean):                        # query = A-doc_i, candidates = other A-docs AND twins
        base = Xn[mono_idx]
        sims = base @ base[2 * mi]
        sims[2 * mi] = -np.inf
        mono += (int(np.argmax(sims)) == 2 * mi + 1)  # its twin sits at slot 2*mi+1
    cross = 0
    for mi in range(n_mean):                        # query = A-doc_i, candidates = B docs
        A, Bq = Xn[0::4], Xn[2::4]
        sims = Bq @ A[mi]
        cross += (int(np.argmax(sims)) == mi)
    mono_band = float(np.mean([Xn[4 * mi] @ Xn[4 * mi + 1] for mi in range(n_mean)]))
    cross_band = float(np.mean([Xn[4 * mi] @ Xn[4 * mi + 2] for mi in range(n_mean)]))
    probe_lang = sum(1 for li in range(2) for mi in range(n_mean)
                     if np.sign(Xn[4 * mi + 2 * li] @ (lang_dirs[1] - lang_dirs[0])) == (2 * li - 1))
    print(f"{label:4s} model: mono-A {mono}/6 | cross-lingual {cross}/6 | "
          f"mono band {mono_band:.3f} | cross band {cross_band:.3f} | "
          f"linear language probe {probe_lang}/12")
```

The result is the trap this lesson exists to name: **every ranking survives the language flag** — 6/6 and 6/6 under the bad model, 6/6 and 6/6 under the good one. Additive identity shifts all of a language's vectors together, so relative order within each comparison is untouched. What splits is the scale: the bad model's mono band sits at **0.997** and its cross band at **−0.128** — a spread of 1.1 on a −1-to-1 scale, meaning no single threshold can serve both query families; a near-duplicate cutoff tuned on English monolingual pairs flags nothing cross-lingually, and one tuned cross-lingually flags everything monolingually. The good model's bands are **0.966** and **0.973** — one scale, calibratable once. And the linear probe reads the story's last line: a single direction classifies all **12/12** documents in the bad space — the language identity is still in there, linearly decodable, alongside whatever shared meaning the space claims to hold — and drops to **5/12** in the good one, chance (expected 6/12, and 5 is what this seed lands). This is the same failure class as Section 2 at a different cause: both leave rankings intact and break the score's meaning. It is also why the field evaluates multilingual retrieval per language — MIRACL (Zhang et al., 2022; WSDM 2023) covers 18 languages with native queries and judgments, precisely so "works in aggregate" cannot hide a band split — and why the fix for identity leakage is training-time (the contrastive translation-pair objective of Section 3's LaBSE), not a post-hoc subtraction of one measured direction.

---

## Three Stacks, One Query Set

The pricing fence: one 40-document index, four queries, three stacks. Stack (a) is a monolingual index meeting foreign queries — the query embedding never leaves its own model's space. Stack (b) is translate-then-retrieve — machine-translate the query, embed, search: the hop re-expresses the query in the index's language but adds the hop's own error (here modeled at fixed magnitude). Stack (c) is a multilingual shared space — both sides embedded by one model that maps all languages into one geometry:

```python
import numpy as np

rng = np.random.default_rng(55)
d, n_docs = 48, 40
docs = rng.normal(size=(n_docs, d))                          # shared-space doc index (4 real + 36 distractors)
q_shared = docs[:4] + 0.05 * rng.normal(size=(4, d))         # 4 queries embedded in the SHARED space
Rm = np.linalg.qr(rng.normal(size=(d, d)))[0]
q_mono = q_shared @ Rm                                       # same 4 queries as the mono model represents them
NOISE = 3.0

docs_n = docs / np.linalg.norm(docs, axis=1, keepdims=True)
def hits_at_1(Q):
    h = 0
    for i, q in enumerate(Q):
        qn = q / np.linalg.norm(q)
        h += (int(np.argmax(docs_n @ qn)) == i)
    return h

a = hits_at_1(q_mono)
hop = q_shared + NOISE * rng.normal(size=q_shared.shape)     # the translate hop re-expresses, imperfectly
b = hits_at_1(hop)
c = hits_at_1(q_shared)
print(f"(a) mono index, foreign query : {a}/4 top-1 | hops 1 | failure: the query never leaves its own space")
print(f"(b) translate-then-retrieve   : {b}/4 top-1 | hops 2 | failure: the hop's own error lands in the index space")
print(f"(c) multilingual shared space : {c}/4 top-1 | hops 1 | failure: none in this 4-query set")
margins = []
for i, q in enumerate(hop):
    qn = q / np.linalg.norm(q)
    sims = docs_n @ qn
    order = np.argsort(-sims)
    margins.append(0.0 if order[0] == i else float(sims[order[0]] - sims[i]))
print(f"(b) per-query loss margins    : {[f'{x:.3f}' for x in margins]}")
```

Stack (a) retrieves **0/4** — not occasionally-wrong but structurally-blind: the foreign query is a rotation away from every document, the same geometry Section 3 measured as 0/4 unaligned. Stack (b) retrieves **3/4** — the translate hop rescues most queries and quietly loses one, whose top-1 goes to a distractor by a margin of **0.112**; that margin is the hop's error surfacing as retrieval noise, and every query's result carries the same exposure. Stack (c) retrieves **4/4** — no hop, no hop error, the query geometry preserved end to end. The production surface for stack (c) is multilingual-e5: `intfloat/multilingual-e5-large`, initialized from XLM-RoBERTa-large (so its vocabulary and positional machinery already span 100 languages), 1024-dimensional output, trained with the E5 recipe's weak-supervision pairs, and shipped with a contract that is easy to miss — inputs must carry the `query: ` / `passage: ` prefixes or measured quality drops. The stack choice is not a detail of multilingual deployment; it decides which failure mode you own: (a) owns certain blindness, (b) owns a per-query noise floor you must measure to see, (c) owns the constraint that one model must serve every language — and Section 4's probes are how you check the claim before trusting it.

---

## Known Failure Modes

| # | Symptom | Cause | Fix |
|---|---------|-------|-----|
| 1 | Polysemous query retrieves the wrong sense | Static one-vector-per-type embedding — 0.707 in both sentences, the vector cannot see the query's context | Contextual encoder for the query side, or sense-aware indexes for ambiguous vocabularies |
| 2 | Every score crowds near the ceiling; thresholds fire on everything | Anisotropy — the mean-dominated cone (0.984 floor, 19,890/19,890 unrelated pairs above 0.9) | Mean-center or whiten raw states before scoring; the centered control (−0.005 / 0.759) is the diagnostic |
| 3 | Cross-lingual search returns noise from a "multilingual" model | The two spaces were never aligned; raw cross cosine is meaningless (0/4 unaligned) | Training-time shared space (LaBSE-style) or a Procrustes map fit on translation pairs |
| 4 | The alignment map made retrieval worse | Non-orthogonal fit or the map applied in the wrong direction | W = UVᵀ from SVD(EᵀB); map B-queries with Wᵀ; verify ‖WᵀW − I‖ at machine precision |
| 5 | One similarity threshold serves mono and cross queries, one family fails | Additive language identity splits the bands (0.997 vs −0.128) while leaving rankings intact | Per-language calibration, or a shared-space model whose bands agree (0.966 vs 0.973) |
| 6 | The "multilingual" claim was never tested | No probe battery run — rankings looked fine in smoke tests | Mono + cross retrieval, band comparison, and the linear language probe (12/12 means identity is still in there) |
| 7 | Translate-then-retrieve silently loses queries | The translation hop's own error lands in the index space (3/4, one loss by 0.112) | Price the hop against your queries; prefer a shared-space model for the query side |
| 8 | An e5-family model underperforms out of the box | The `query: ` / `passage: ` prefixes were dropped — the prefix contract is part of the input | Send the model card's prefixes on both sides; they are input syntax, not documentation flavor |

---

## Summary

A contextual model emits one vector per token use, not one per type: the static type vector scores cos(deposit, bank) at 0.707 in both sentences while the contextual blend reads 0.505 in the geology sentence and 0.910 in the finance one, and the two uses of *bank* agree at only 0.794. Raw contextual states sit in an anisotropic cone — unrelated pairs average 0.984 with all 19,890 above 0.9 — and mean-centering restores the geometry (−0.005 unrelated, 0.759 related) and the margin (0.0100 raw to 0.3939 centered) without changing a single ranking; anisotropy kills thresholds, not order. Cross-lingual retrieval is 0/4 until the spaces are aligned: the orthogonal Procrustes map (W = UVᵀ from SVD(EᵀB), residual 0.4297, orthogonality 1e-15) restores 4/4 with one matrix multiply per query, and LaBSE is what the same idea looks like when the shared space is built during training instead of fitted after. The language-identity probe is the shipping gate: a language-flagged space passes every ranking test (6/6, 6/6) while its bands split 0.997 vs −0.128 and a linear probe reads the language at 12/12 — and the priced end state is the three stacks, mono index 0/4, translate-then-retrieve 3/4 with the lost query down 0.112, shared space 4/4.

---

## References

### Related Minder Academy Documents

- [6102: Semantic Similarity Metrics](./6102-Semantic-Similarity.md) — the static word-embedding tradition (Word2Vec, GloVe) and the cosine geometry every vector here is scored with
- [6104: Embedding Sciences - Pooling, Matryoshka, and MTEB](./6104-Embedding-Sciences.md) — the pooling and truncation layer above: how per-token states become the vectors this lesson aligns
- [6101: HNSW Indexing - Efficient Semantic Search at Scale](./6101-HNSW-Indexing.md) — the index that stores whichever space you ship, shared or not
- [6103: HNSW Tuning Guide](./guides/6103-HNSW-Tuning-Guide.md) — tuning the index around a multilingual fleet's dimensionality and query mix
- [3202: Tokenizer Sciences - BPE, SentencePiece, and Tiktoken](../../phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md) — the vocabulary side of multilingual models: one SentencePiece table serving 100 languages, upstream of every shared space here

### Primary Sources

- Ethayarajh, K. (2019). *How Contextual are Contextualized Word Representations? Comparing the Geometry of BERT, ELMo, and GPT-2 Embeddings*. EMNLP-IJCNLP 2019 (arXiv:1909.00512) — anisotropy in every layer and self-similarity falling with depth, the measurements behind Sections 1-2
- Mikolov, T., Le, Q. V., & Sutskever, I. (2013). *Exploiting Similarities among Languages for Machine Translation* (arXiv:1309.4168) — the linear-map hypothesis and the least-squares translation matrix that orthogonal Procrustes constrains
- Feng, F., et al. (2020). *Language-agnostic BERT Sentence Embedding*. (arXiv:2007.01852) — LaBSE: 109 languages, margin-based translation-ranking over 8B pairs, 83.7% vs 65.5% bitext retrieval
- Zhang, X., et al. (2022). *MIRACL: A Multilingual Retrieval Dataset Covering 18 Languages and 3B+ Speakers*. WSDM 2023 (arXiv:2209.10574) — native-query evaluation, the per-language discipline Section 4 argues for
- multilingual-e5 model card (intfloat/multilingual-e5-large) — XLM-RoBERTa-large init, 100 languages, 1024 dims, and the `query: ` / `passage: ` prefix contract

---

## Next Steps

- **Next Module:** [6200: Retrieval Strategies](../6200-retrieval/README.md) — hybrid fusion and the query-side levers the shared (or unshared) space feeds
- **Continue with:** [6201: Hybrid Search - Combining Keyword and Semantic Search](../6200-retrieval/6201-Hybrid-Search.md)
- **Assessment:** [QUIZ](./assessment/QUIZ.md) — question 17 is this lesson's, and the contextual/multilingual review bullet now points here
- **Hands-on:** run the Section 4 probe battery (bands + linear language probe) on your own multilingual embedder before trusting it; drop and restore the e5 prefixes and measure what the contract is worth
