---
Document ID: 6204
Title: "6204: Diversification and Boosting"
Phase: 6
Module: 6200
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'retrieval', 'hybrid-search', 'reranking']
---

# 6204: Diversification and Boosting

## Abstract

Pure relevance ranking has a blind spot it cannot measure itself: the top five hits can be one fact five times. This lesson teaches the two levers that operate on the *selection*, not the query — diversification, which trades a little relevance for coverage of distinct information, and boosting, which multiplies scores by provenance so the source you trust outranks the paraphrase that edged it. Both are built as working code on a seeded corpus where the failure is arithmetic, not anecdotal: a five-slot window holding one distinct fact, an MMR dial that does nothing at 0.7 and everything at 0.5, a ×1.5 boost that reorders the top five and another that fails to, and the same boost flipping winners differently depending on where in the fusion pipeline it lands. The module's own QUIZ admits the gap this lesson fills: MMR's relevance-redundancy diversification and document boosting are taught nowhere in the curriculum — 6201 teaches the fusion these weights ride on, 6202 teaches the reranking stage MMR extends, 6203 teaches the query-side levers; the selection-side levers live here.

---

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Redundancy Failure](#the-redundancy-failure)
- [Maximal Marginal Relevance](#maximal-marginal-relevance)
- [The LangChain Surface](#the-langchain-surface)
- [Document Boosting](#document-boosting)
- [Boost Placement in the Fusion Pipeline](#boost-placement-in-the-fusion-pipeline)
- [Measuring Diversity](#measuring-diversity)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Diagnose the redundancy failure — a top-5 window scoring 4.73 summed cosine while covering one distinct fact out of four, with every relevance metric green
- Implement Maximal Marginal Relevance — the greedy `argmax λ·sim(q,d) − (1−λ)·max sim(d, selected)` loop over unit vectors, and read why λ = 0.7 leaves a tight paraphrase cluster untouched while λ = 0.5 breaks it
- Drive the production surface — `max_marginal_relevance_search(query, k, fetch_k, lambda_mult)` on LangChain's `InMemoryVectorStore`, where fetch_k is the over-fetch pool and lambda_mult is the same dial you just tuned by hand
- Boost by provenance without the traps — ×1.5 on the official page overtakes three near-tie paraphrases, while the same multiplier on a genuinely-irrelevant page moves 0.205 to 0.308 and surfaces nothing
- Place boosts coherently — the same ×1.5 applied after fusion names one winner and applied inside the lexical channel names another, because a channel-scoped boost rewrites the document's effective α
- Measure diversity — intra-list similarity and distinct-fact coverage as the pair of numbers relevance metrics cannot produce, with α-nDCG named as the graded-relevance-aware formalization

**Estimated Time:** 3 hours

---

## The Redundancy Failure

A pricing query against a support corpus. Ten chunks over four facts — pricing (P), latency (L), security (S), integration (I) — embedded on hand-built axes so every cosine is checkable by hand. Four chunks are paraphrases of the pricing page; the rest cover the other facts. Rank by cosine to the query and take the top five:

```python
import numpy as np

def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)

RAW = [
    ("D0", "P", [1.0, 0.0, 0.0, 0.0]),     # pricing overview
    ("D1", "P", [1.0, 0.08, 0.0, 0.0]),    # pricing paraphrase
    ("D2", "P", [1.0, 0.0, 0.07, 0.0]),    # pricing paraphrase
    ("D3", "P", [1.0, 0.0, 0.0, 0.06]),    # pricing paraphrase
    ("D4", "L", [0.0, 1.0, 0.0, 0.0]),     # latency budget
    ("D5", "S", [0.0, 0.0, 1.0, 0.0]),     # security model
    ("D6", "I", [0.0, 0.0, 0.0, 1.0]),     # integration api
    ("D7", "L", [0.06, 1.0, 0.0, 0.0]),    # latency paraphrase
    ("D8", "X", [-0.5, -0.5, -0.5, -0.5]), # off-topic churn
    ("D9", "P", [1.0, 1.0, 0.0, 0.0]),     # pricing-vs-latency comparison
]
IDS = [d[0] for d in RAW]
FACT = {d[0]: d[1] for d in RAW}
V = np.array([unit(d[2]) for d in RAW])
Q = unit([1.0, 0.15, 0.1, 0.1])
rel = V @ Q  # cosine to the query; rows of V are unit vectors

order = sorted(range(len(IDS)), key=lambda i: -rel[i])[:5]
labels = [FACT[IDS[i]] for i in order]
print("cosine top-5:", " ".join(IDS[i] for i in order))
print("facts       :", labels)
print("coverage    :", len(set(labels)), "distinct fact(s) of 4")
print("rel_sum     :", round(sum(float(rel[i]) for i in order), 2))
```

The window is spectacular by every relevance measure and useless by information: five chunks, one fact. The summed cosine is **4.73**, the top chunk scores **0.988**, and the generator reads four paraphrases of the pricing page plus the comparison post — while the latency, security, and integration chunks sit at cosines **0.147**, **0.098**, and **0.098**, below the cutoff with no vote against them. Nothing failed. This is the ranking doing exactly what it was asked: maximizing relevance, which it cannot be talked out of by tuning 6201's α or 6202's reranker, because both re-score the same redundant pool with the same relevance objective.

---

## Maximal Marginal Relevance

Maximal Marginal Relevance (Carbonell & Goldwater, 1998) changes the selection objective from "most relevant" to "most relevant given what is already picked":

```text
MMR = argmax over d not yet selected of:
      λ · sim(query, d)  −  (1 − λ) · max over s in selected of sim(d, s)
```

The first term pulls toward the query; the second pushes away from whatever the selection already covers. Greedy, one pick per round, no re-training and no second model — it is a re-*sampler* over the pool 6202's over-fetch already produces:

```python
import numpy as np

def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)

RAW = [
    ("D0", "P", [1.0, 0.0, 0.0, 0.0]), ("D1", "P", [1.0, 0.08, 0.0, 0.0]),
    ("D2", "P", [1.0, 0.0, 0.07, 0.0]), ("D3", "P", [1.0, 0.0, 0.0, 0.06]),
    ("D4", "L", [0.0, 1.0, 0.0, 0.0]), ("D5", "S", [0.0, 0.0, 1.0, 0.0]),
    ("D6", "I", [0.0, 0.0, 0.0, 1.0]), ("D7", "L", [0.06, 1.0, 0.0, 0.0]),
    ("D8", "X", [-0.5, -0.5, -0.5, -0.5]), ("D9", "P", [1.0, 1.0, 0.0, 0.0]),
]
IDS = [d[0] for d in RAW]
FACT = {d[0]: d[1] for d in RAW}
V = np.array([unit(d[2]) for d in RAW])
Q = unit([1.0, 0.15, 0.1, 0.1])
rel = V @ Q

def mmr(lam, k=5):
    sel = [int(np.argmax(rel))]
    pool = [i for i in range(len(IDS)) if i != sel[0]]
    while len(sel) < k:
        best = max(pool, key=lambda i: lam * float(rel[i])
                   - (1 - lam) * max(float(V[i] @ V[j]) for j in sel))
        sel.append(best)
        pool.remove(best)
    return sel

def ils(sel):
    pairs = [float(V[a] @ V[b]) for x, a in enumerate(sel) for b in sel[x + 1:]]
    return sum(pairs) / len(pairs)

for lam in (1.0, 0.7, 0.5, 0.0):
    sel = mmr(lam)
    labels = [FACT[IDS[i]] for i in sel]
    print(f"lambda={lam:<3} {' '.join(IDS[i] for i in sel)}  facts={labels}  "
          f"coverage={len(set(labels))}/4  rel_sum={sum(float(rel[i]) for i in sel):.2f}  ILS={ils(sel):.2f}")
```

Read the dial against the output. At **λ = 1.0** — pure relevance — the selection is the cosine list: one fact, rel_sum **4.73**, intra-list similarity **0.89**. At **λ = 0.7** nothing changes, and that is the fence's first lesson: the paraphrase cluster's self-similarity is ≈ 0.99, so the penalty term costs a cluster member about `(1 − λ) · 0.99 ≈ 0.30` while its relevance term retains `0.7 · 0.988 ≈ 0.69` — score **0.39** — against the best outsider's `0.7 · 0.205 ≈ 0.14`. A near-identical cluster defeats a 30 % penalty weight. At **λ = 0.5** the arithmetic flips: the cluster member now scores `0.494 − 0.498 ≈ 0.00` and the selection becomes **D1 D5 D6 D4 D9** — all four facts in five slots, rel_sum **2.13**, ILS **0.15**. Less than half the relevance budget buys four times the information; the generator reads facts, not cosine. At **λ = 0.0** the relevance term is gone entirely and the maximally-dissimilar junk enters: D8, cosine **−0.661**, drags rel_sum to **0.67** with ILS **−0.20**. Diversity without relevance is noise — λ = 0 is a diagnostic, not a configuration.

---

## The LangChain Surface

Every mainstream vector-store client exposes the same three knobs under the same names; LangChain's is the reference shape:

```python
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.vectorstores import InMemoryVectorStore

docs = [
    Document(page_content="pro plan pricing overview", metadata={"id": "D0"}),
    Document(page_content="pricing tiers and quotas", metadata={"id": "D1"}),
    Document(page_content="pricing faq", metadata={"id": "D2"}),
    Document(page_content="latency budget", metadata={"id": "D3"}),
    Document(page_content="security model", metadata={"id": "D4"}),
    Document(page_content="integration api", metadata={"id": "D5"}),
]
emb = DeterministicFakeEmbedding(size=32)
store = InMemoryVectorStore(emb)
store.add_texts([d.page_content for d in docs], metadatas=[d.metadata for d in docs])

greedy = store.similarity_search("pricing", k=3)
diverse = store.max_marginal_relevance_search("pricing", k=3, fetch_k=6, lambda_mult=0.2)
print("cosine k=3         :", [d.metadata["id"] for d in greedy])
print("mmr lambda=0.2 k=3 :", [d.metadata["id"] for d in diverse])
```

The fake hash embeddings carry no semantics, so the ids are arbitrary — the fence pins the *contract*: `k` results are selected from a `fetch_k` pool (over-fetch, the 6202 shape), `lambda_mult` is the dial from the previous fence in `[0, 1]`, and both calls return `Document`s with metadata. Here `cosine k=3` returns **D5, D4, D0** and `mmr lambda=0.2` returns **D5, D1, D4** — the selector traded the third cosine hit for a different pick inside the fetch_k pool. Two contract rules worth memorizing: `fetch_k = k` degenerates MMR to plain cosine (nothing to diversify against), and a pool of 3–5× `k` is the working over-fetch. The same `lambda_mult` knob is exposed by the Chroma, pgvector, and Qdrant wrappers — tune it once by hand as above and you know what the store is doing.

---

## Document Boosting

Diversification fixes *which* facts; boosting fixes *whose version* of each fact. A provenance weight multiplies relevance scores so the source you trust wins the near-ties it keeps losing by a hair:

```python
import numpy as np

def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)

RAW = [
    ("D0", "P", [1.0, 0.0, 0.0, 0.0]), ("D1", "P", [1.0, 0.08, 0.0, 0.0]),
    ("D2", "P", [1.0, 0.0, 0.07, 0.0]), ("D3", "P", [1.0, 0.0, 0.0, 0.06]),
    ("D4", "L", [0.0, 1.0, 0.0, 0.0]), ("D5", "S", [0.0, 0.0, 1.0, 0.0]),
    ("D6", "I", [0.0, 0.0, 0.0, 1.0]), ("D7", "L", [0.06, 1.0, 0.0, 0.0]),
    ("D8", "X", [-0.5, -0.5, -0.5, -0.5]), ("D9", "P", [1.0, 1.0, 0.0, 0.0]),
]
IDS = [d[0] for d in RAW]
V = np.array([unit(d[2]) for d in RAW])
Q = unit([1.0, 0.15, 0.1, 0.1])
rel = V @ Q

WEIGHTS = {"D0": 1.5, "D7": 1.5}   # official pages: pricing overview, latency budget
boosted = rel.copy()
for i, doc_id in enumerate(IDS):
    boosted[i] *= WEIGHTS.get(doc_id, 1.0)

before = sorted(range(len(IDS)), key=lambda i: -rel[i])[:5]
after = sorted(range(len(IDS)), key=lambda i: -boosted[i])[:5]
d0 = IDS.index("D0")
d7 = IDS.index("D7")
print("before:", " ".join(IDS[i] for i in before))
print("after :", " ".join(IDS[i] for i in after))
print(f"D0 {float(rel[d0]):.3f} -> {float(boosted[d0]):.3f}   "
      f"D7 {float(rel[d7]):.3f} -> {float(boosted[d7]):.3f} (still unranked)")
```

The official pricing page D0 loses the top slot to forum paraphrases by cosines of **0.979 vs 0.988** — a difference no human would call meaningful, but the argmax does. The ×1.5 provenance weight moves it to **1.469** and the order flips to **D0 D1 D2 D3 D9**: same documents, the trusted source now leads. The second line is the fence's discipline: the official latency page D7 moves **0.205 → 0.308** and remains unranked, because ×1.5 re-weights near-ties, it does not conjure relevance. When a document loses by a factor of five — an embedding gap, not a scoring tie — no boost multiplier you would dare ship closes it; fix the retrieval, not the weight.

The named production surface carries the same semantics and the same trap. In OpenSearch and Elasticsearch query DSL, `boost` sits on a query clause — and a clause *is* a channel:

```json
{
  "query": {
    "bool": {
      "should": [
        { "match": { "text": { "query": "pricing tiers", "boost": 2.0 } } },
        { "term": { "source": { "value": "docs.vendor.com", "boost": 1.5 } } }
      ],
      "minimum_should_match": 1
    }
  }
}
```

Two structural traps live here. **Stacking**: two independent rules each worth ×1.5 — a source boost and a freshness boost — compose to ×2.25 on any document both touch, silently; keep a single boost authority or log the effective per-document weight. **Unnormalized channels**: a boost multiplies whatever scale it finds; ×1.5 on a min-max-normalized lexical channel in `[0, 1]` and ×1.5 on raw BM25 scores running 1–10 are different interventions entirely, and the raw-scale one multiplies the axis that already dominates the fusion. Normalize channels first — 6201's per-query min-max — then boost.

---

## Boost Placement in the Fusion Pipeline

Where the boost enters 6201's fusion decides what it means. Fused score `α·semantic + (1−α)·lexical`; one official page X (weak semantic match, perfect lexical) against one forum thread A (strong semantic, strong lexical):

```python
sem = [0.20, 0.95]    # X, A: semantic channel (normalized)
lex = [1.00, 0.81]    # X, A: lexical channel (min-max normalized)
ALPHA, W = 0.5, 1.5

def fused(boost_lexical):
    x = ALPHA * sem[0] + (W if boost_lexical else 1.0) * (1 - ALPHA) * lex[0]
    return x, ALPHA * sem[1] + (1 - ALPHA) * lex[1]

base_x, base_a = fused(False)
after_x, after_a = base_x * W, base_a                  # boost applied to the fused score
chan_x, chan_a = fused(True)                           # boost applied inside the lexical channel
for name, (x, a) in [("no boost               ", (base_x, base_a)),
                     ("x1.5 after fusion      ", (after_x, after_a)),
                     ("x1.5 on the lex channel", (chan_x, chan_a))]:
    print(f"{name} X={x:.2f}  A={a:.2f}  winner={'X' if x > a else 'A'}")
```

Same corpus, same ×1.5, three different verdicts. Unboosted, A wins **0.88 to 0.60**. Boost applied to the *fused score* — "this document matters 50 % more" — flips the winner: X **0.90** over A **0.88**. The same ×1.5 applied *inside the lexical channel* does not flip it: X reaches only **0.85** against A's unchanged **0.88**. The mechanism is exact, not numerical noise: a fused-score boost multiplies the whole score — +0.30 for X — and clears the +0.28 needed to pass A; a channel-scoped boost multiplies only the `(1−α)`-weighted slice, adding `(1−α)·(w−1)·lex` — +0.25 for X — and falls short. What the channel-scoped variant actually rewrites is the document's *effective α* — the page's own blend of the channels — instead of the page's importance. "This source is worth more" and "this source's lexical hits are worth more" are different statements; only one of them is a provenance policy. Place boosts on the fused score (or per-channel only when channel-scoping is the intent), and read any search-DSL clause boost as the channel-scoped variant it is.

---

## Measuring Diversity

A regression you cannot score is a regression you will ship. Two numbers catch what the relevance suite cannot:

- **Intra-list similarity (ILS)** — mean pairwise cosine within the returned window. The redundant list's **0.89** versus the diversified list's **0.15** is the failure and the fix in one scalar; a window above your ILS budget is five documents doing one document's work.
- **Distinct-fact coverage** — count the independent facts the window carries (label a held-out set once). Coverage **1/4 → 4/4** across the λ sweep is the outcome metric; ILS is the mechanism metric.

The reason both must be added manually: 6202's AP/MAP and NDCG score *positions against relevance labels*, and the redundant list is genuinely relevant at every position — MRR **1.0**, NDCG@5 near-perfect, all green. α-nDCG (Clarke et al., 2008) formalizes the fix inside the metric family: each additional document covering an already-covered intent is discounted, so the fifth pricing paraphrase earns a fraction of the first. Until that is wired into the eval, coverage-and-ILS on a small labeled set is the honest minimum.

---

## Known Failure Modes

| # | Symptom | Cause | Fix |
|---|---------|-------|-----|
| 1 | λ = 0.7 leaves the redundant list untouched | The cluster's self-similarity ≈ 1.0 makes the penalty `(1−λ)·0.99` smaller than the retained relevance `λ·rel` | Compute the crossover instead of dialing by taste; here λ = 0.5 breaks the cluster (fence 2's arithmetic) |
| 2 | λ = 0.0 injects off-topic junk | Pure diversity has no relevance term; the maximally-dissimilar chunk (cosine −0.661) enters | Keep λ strictly positive in configuration; treat λ = 0 as a diagnostic run |
| 3 | Relevance metrics green, users report repetitive answers | MRR/NDCG score positions against relevance labels; redundancy is invisible to them | Add distinct-fact coverage and an ILS budget to the eval suite; consider α-nDCG |
| 4 | Boost fails to surface the page you boosted | The page lost by an embedding gap (0.205 → 0.308 still unranked), not by a tie | Fix retrieval/embedding for the fact; boosts arbitrate near-ties, not relevance gaps |
| 5 | Boosted doc's weight is not what the config says | Two ×1.5 rules (source + freshness) stack to ×2.25 silently | Single boost authority, or log the effective per-document weight |
| 6 | Post-fusion boost flips the winner; the same number as a DSL clause boost does not | Clause-level boost is channel-scoped: it multiplies only the `(1−α)` slice (+0.25 vs the fused boost's +0.30) and rewrites the document's effective α | Apply provenance weights to the fused score unless channel-scoping is the intent |
| 7 | Boost on raw BM25 dominates the fusion | Raw lexical scores are unbounded (~1–10) against cosine's [0, 1]; the multiplier scales the already-dominant axis | Per-query min-max normalize channels (6201) before boosting or fusing |
| 8 | MMR output equals plain cosine | fetch_k ≤ k leaves no pool to diversify against | Over-fetch 3–5× k; assert `fetch_k > k` where the client allows |

---

## Summary

Relevance ranking maximizes relevance, and one fact five times is the optimum. Diversification changes the selection objective — MMR's greedy `λ·rel − (1−λ)·redundancy` loop, with the dial's crossover computed against the cluster's actual self-similarity rather than guessed, the production contract being `max_marginal_relevance_search(k, fetch_k, lambda_mult)` over a 3–5× over-fetch. Boosting changes the source arithmetic — provenance weights arbitrate near-ties (0.979 vs 0.988 becomes 1.469 vs 0.988) but cannot conjure relevance (0.205 → 0.308 still unranked), stack multiplicatively when two rules touch one document, and flip different winners depending on whether they multiply the fused score or one channel — the channel-scoped variant rewriting each document's effective α. Neither lever is measurable by the relevance suite: ILS and distinct-fact coverage are the pair that catches a green-on-paper, repetitive-in-production window, with α-nDCG as the metric-family formalization.

---

## References

### Related Minder Academy Documents

- [6201: Hybrid Search - Combining Keyword and Semantic Search](./6201-Hybrid-Search.md) — the two-channel fusion and min-max normalization that boosts multiply
- [6202: Re-ranking and Retrieval Logistics](./6202-Re-ranking-and-Retrieval-Logistics.md) — the over-fetch-then-rescore two-stage pipeline MMR's pool comes from
- [6203: Advanced Retrieval Techniques](./6203-Advanced-Retrieval.md) — the query-side levers; diversification and boosting are the selection-side complements
- [6101: HNSW Indexing - Efficient Semantic Search at Scale](../6100-vector/6101-HNSW-Indexing.md) — the ANN index producing the candidate pool
- [6102: Semantic Similarity](../6100-vector/6102-Semantic-Similarity.md) — cosine similarity mechanics behind every sim term above
- [6302: CAG - Context Augmented Generation and Long Context Architectures](../6300-context/6302-CAG-Long-Context-Architectures.md) — what the diversified, boosted window feeds

### Primary Sources

- Carbonell, J., & Goldwater, J. (1998). *The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries*. SIGIR 1998 — the original formula and the argmax form taught here
- Clarke, C., Kolla, M., Cormack, G., Vechtomova, O., Ashkan, A., Büttcher, S., & MacKinnon, I. (2008). *Novelty and Diversity in Information Retrieval Evaluation*. ICTIR 2008 — α-nDCG
- LangChain — `VectorStore.max_marginal_relevance_search(query, k, fetch_k, lambda_mult)` API reference and the `InMemoryVectorStore` implementation
- OpenSearch Documentation — *Query DSL: bool query and clause-level boost*

---

## Next Steps

- **Next Module:** [6300: Context Management](../6300-context/README.md) — windowing, caching, and long-context architectures for the retrieved evidence
- **Continue with:** [6301: Neo4j and Knowledge Graphs](../6300-context/6301-Neo4j-and-Knowledge-Graphs.md)
- **Assessment:** [QUIZ](./assessment/QUIZ.md) — questions 9 and 17 are this lesson's, now taught where they live
- **Hands-on:** sweep λ on your own retrieval log, label distinct facts for one query type, and add an ILS budget alongside your NDCG gate
