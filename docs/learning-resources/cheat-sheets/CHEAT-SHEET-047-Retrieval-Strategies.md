---
Document ID: CHEAT-SHEET-047
Title: "CHEAT-SHEET-047: Retrieval Strategies - the Two-Channel Fusion, the Rerank Funnel, and the Diversity Dial"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rag', 'retrieval', 'hybrid-search']
---

# CHEAT-SHEET-047: Retrieval Strategies - the Two-Channel Fusion, the Rerank Funnel, and the Diversity Dial

The retrieval-strategies surface is phase6-rag's 6200-retrieval track - 6201 Hybrid Search, 6202 Re-ranking and Retrieval Logistics, 6203 Advanced Retrieval and 6204 Diversification and Boosting - four modules with no sheet anywhere in the track (scope scan: the 00-META sheet index carries no id beside any of the four, and the RAG overview sheet owns the pipeline around retrieval, not the retrieval core this track teaches). This sheet takes that core as the three questions the student actually asks: what joins the two channels (BM25 and dense, fused by rank or by score), what refines the candidate list (the rerank funnel and the metrics that score it), and what shapes the final list (the diversity dial and where a provenance boost belongs) - closing the 6200 track.

The sheet runs as seven priced exhibits: BM25's exact-term arithmetic and the tie that proves it deterministic (F1), RRF rank fusion without score normalization (F2), the alpha dial over per-query min-max channels (F3), the two-stage rerank funnel with ColBERT's MaxSim (F4), AP and NDCG on one labeled window (F5), the MMR diversity dial over the redundancy corpus (F6), and the provenance boost with its placement on the fused score (F7). Every number below is printed by the canonical fence at the bottom of the page: the full 245-line stdlib fence reproduces all seven in closed form - no RNG anywhere - and its 52-line output sits frozen below it byte-for-byte.

## The Two Channels and the Fusion That Joins Them

BM25 is exact-term arithmetic: idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl)) with k1 = 1.5, b = 0.75. The tie proves it deterministic: query 'cat' scores d0 0.8338 and d2 0.8338 - identical to the fourth decimal because both documents share df = 2 and dl = 6. The rare term shows the idf lever: 'pets' lands 1.5694 at df = 1, nearly double the tie score. And the blind spot is the point: the dense paraphrase 'feline found resting' shares no term with either hit and scores both at zero - a bi-encoder finds the mat, BM25 never leaves the vocabulary.

| Channel | Strength | Blind spot | Ships as |
| --- | --- | --- | --- |
| Sparse (BM25) | exact terms, rare-token idf, zero training | no paraphrase: 'feline' never meets 'cat' | any BM25 index (OpenSearch, Elasticsearch) |
| Dense bi-encoder | paraphrase and intent, ANN-fast | vocabulary-blind, domain-drift sensitive | sentence-transformers class + a vector store |
| Hybrid (fused) | both witnesses on one list | fusion is a design decision, not a default | RRF or alpha fusion over both lists |

RRF fuses ranks, never scores: each document earns 1 / (k + rank + 1) per channel with k = 60. B sits first-and-second across the two channels and wins at 0.032522 over A's first-plus-third 0.032266 - a gap of 256 millionths, but a total order. No score normalization is needed because only ranks enter the sum: BM25's open-ended scale and cosine's bounded one never meet.

Alpha fusion fuses scores, and the min-max comes first - per query, per channel - or the bigger scale owns the blend. Then the dial: at alpha 0.9 the semantic winner A holds 0.9000; at 0.5 the balanced B takes 0.6000; at 0.1 the lexical specialist D takes 0.9000. The dial moves the winner, which is exactly why 6201 says sweep it on MAP@10 instead of guessing: conceptual queries ride high alpha, exact-term queries ride low.

```text
The two channels are witnesses, not averages: BM25 holds the exact terms
the dense encoder paraphrases away. Fuse ranks only (RRF, k = 60) or
min-max per query before the alpha blend - raw scales never meet directly.
```

## The Rerank Funnel - Retrieve Wide, Score Deep, Keep the Top

The funnel is 6202's summary rule - spend compute where the context is finalized - priced: stage 1 retrieves retrieve_n = 100 with the fast bi-encoder or the hybrid fusion; stage 2 scores those 100 (query, document) pairs with the cross-encoder and keeps top_k = 10. The budget says why the split exists: embedding ~20 ms, ANN ~10-30 ms, and the cross-encoder 200-800 ms for 50 pairs - the reranker dominates the bill, doubling the candidates doubles its cost, and a MiniLM-class cross-encoder on GPU clears 100 pairs in under 100 ms.

| Reranker | What it scores | Cost at 50 pairs | Ships as |
| --- | --- | --- | --- |
| Cross-encoder (MiniLM class) | the (query, doc) pair as one sequence | 200-800 ms CPU; 100 pairs < 100 ms GPU | CrossEncoderReranker, ms-marco-MiniLM-L-6-v2 |
| ColBERT late interaction | per-token MaxSim, no joint pass | precomputed doc tokens, query-time sum | RAGatouille / PLAID |
| Bi-encoder alone | one dot product, the funnel's stage 1 | the ~20 ms baseline | the stage the funnel exists to correct |

ColBERT's MaxSim is the middle path: sum, over query tokens, of the best doc-token dot. On the two-token toy, doc A ([[1.0, 0.1], [0.9, 0.0], [0.0, 0.9]]) scores 1.9000 against doc B's 0.4000 - each query token finds its best match and the sum keeps the per-token structure a single dot product would average away.

```text
The funnel's contract: rank cheap, score expensive, keep the top -
retrieve_n = 100 through the bi-encoder or the fusion, then the
cross-encoder spends its 200-800 ms only where the context is finalized.
```

## Scoring the List - AP and NDCG on One Labeled Window

Without graded labels the funnel's knobs cannot be compared. AP divides the sum of precision-at-hit by the number of relevant documents - never by k. NDCG discounts by position, (2^rel - 1) / log2(i + 2), against the ideal order. The window prices both: the good order [d1, d3, d2, d4] lands AP 1.0000 and NDCG@4 1.0000; the bad order [d2, d1, d3, d4] finds both relevant documents and still loses - AP 0.5833 because d1's hit arrives at precision 0.5, NDCG@4 0.6653 because the grade-3 document sits one position late. 6203's acceptance bar runs on these numbers: Recall@50 >= 0.90, MRR >= 0.7, nDCG >= 0.8, P95 < 1.5 s - and the ablation chain changes one knob at a time against them.

| Metric | The price it charges | Reads |
| --- | --- | --- |
| AP | every early miss lowers every later precision | how high the relevant sit, on average |
| NDCG@k | position discount log2(i + 2), grade 2^rel - 1 | how well the top honors the graded order |
| Recall@k | nothing above k survives | whether the funnel was fed the answer at all |

## The Diversity Dial - MMR and the Redundancy Corpus

The redundancy failure is a top-5 of five paraphrases: cosine alone picks D1 D2 D3 D0 D9 - five P-facts, coverage 1/4, rel_sum 4.73, ILS 0.89. MMR's greedy argmax, lam * sim(q, d) - (1 - lam) * max-sim against the already-selected, turns the same corpus with the dial. At lam 1.0 and 0.7 nothing moves - the P cluster's self-similarity is too profitable. At 0.5 the list becomes D1 D5 D6 D4 D9: all four facts covered (PSILP), rel_sum 2.13, ILS 0.15 - over half of the relevance surrendered for the full coverage. At 0.0 relevance stops voting and D8 enters at cosine -0.661: diversity without relevance is noise.

| Dial | Top-5 | Coverage | rel_sum | ILS |
| --- | --- | --- | --- | --- |
| cosine / lam 1.0 | D1 D2 D3 D0 D9 | 1/4 | 4.73 | 0.89 |
| lam 0.7 | D1 D2 D3 D0 D9 | 1/4 | 4.73 | 0.89 |
| lam 0.5 | D1 D5 D6 D4 D9 | 4/4 | 2.13 | 0.15 |
| lam 0.0 | D1 D8 D5 D6 D4 | 5/4 | 0.67 | -0.20 |

LangChain ships the same dial as max_marginal_relevance_search(k, fetch_k, lambda_mult) with one trap of its own: fetch_k is the pool the diversity is chosen FROM, so fetch_k <= k collapses the dial - keep fetch_k at 3-5x k.

## Provenance Boost and Its Placement

The provenance case: official document D0 scores 0.979 against the paraphrase D1's 0.988 and loses by nine thousandths. The boost x1.5 moves it to 1.469 and the list flips to D0 first - but the same x1.5 on the weak D7 moves 0.205 to 0.308 and it stays unranked: a boost reorders what retrieval already surfaced, it never conjures a document the channels missed. Placement decides whether the boost means anything: applied to the fused score, X gains the full +0.30 and wins 0.90 against 0.88; applied channel-scoped - the OpenSearch / Elasticsearch clause boost - it multiplies only the lexical slice, adds (1 - a) * (w - 1) * lex = +0.25, rewrites the document's effective alpha, and X still loses at 0.85.

| Boost placement | X's score | Winner |
| --- | --- | --- |
| no boost | 0.60 | A (0.88) |
| x1.5 on the fused score | 0.90 | X |
| x1.5 on the lexical clause | 0.85 | A (0.88) |

## The Priced Pipeline and the Decision Rules

6203's production arc reads: transform the query (only on mismatch), retrieve hybrid at k 50-100, rerank to top-5, compress the context. The ~1.5 s budget sits on top of it: embedding ~20 ms, ANN ~10-30 ms, the cross-encoder 200-800 ms, and compression the remainder - each stage buys back one of the four canonical failures (query mismatch, lost-in-the-middle, chunk dilution, homogeneous noise) and the eval targets decide whether it earned its latency.

```text
Production arc: transform (on mismatch) -> retrieve hybrid k 50-100 ->
rerank to top-5 -> compress to the context window - ~1.5 s all-in,
the cross-encoder's 200-800 ms the dominant line item.
```

```text
Decide by what the list lacks: joins wrong -> hybrid and the dial,
orders wrong -> the funnel, repeats itself -> MMR lam 0.5, and provenance
always on the fused score - boost reorders, it never conjures.
```

## The Canonical Fence

The seven exhibits reproduce from one stdlib script - closed form throughout, no RNG, byte-identical on every run:

```python
"""CHEAT-SHEET-047 fence - Retrieval Strategies, the two-channel fusion,
the rerank funnel, and the diversity dial. Stdlib-only, deterministic
(tick-1002 law). Six exhibits:
F1 BM25 scoring and the exact-term tie           [6201]
F2 RRF rank fusion without score normalization    [6201]
F3 per-query min-max alpha fusion                 [6201]
F4 the rerank funnel + ColBERT MaxSim             [6202]
F5 AP and NDCG on a labeled window                [6202]
F6 the MMR dial over the redundancy corpus        [6204]
F7 provenance boost and its placement             [6204]
"""
import math
import sys

sys.stdout.reconfigure(encoding="utf-8")


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


# ================= F1: BM25 scratch =================
print("=" * 72)
print("F1  BM25 scratch (k1=1.5, b=0.75)  [6201]")
DOCS = [
    ("d0", "the cat sat on the mat"),
    ("d1", "the dog napped on the rug"),
    ("d2", "a cat and a dog played"),
    ("d3", "pets need daily walks"),
    ("d4", "the bird sings at dawn"),
]
K1, B = 1.5, 0.75
TOK = [t.split() for _, t in DOCS]
AVGDL = sum(len(t) for t in TOK) / len(DOCS)
N = len(DOCS)


def bm25(query):
    out = {}
    for i, (did, _) in enumerate(DOCS):
        s, dl = 0.0, len(TOK[i])
        for term in query.split():
            tf = TOK[i].count(term)
            if tf == 0:
                continue
            df = sum(1 for t in TOK if term in t)
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
            s += idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * dl / AVGDL))
        out[did] = s
    return out


sc = bm25("cat")
sp = bm25("pets")
print(f"  avgdl={AVGDL:.1f}  N={N}")
print(f"  query 'cat' : d0 {sc['d0']:.4f}  d2 {sc['d2']:.4f}"
      f"   <- exact TIE: same df=2, same dl=6")
print(f"  query 'pets': d3 {sp['d3']:.4f}"
      f"   <- df=1 rare term wins alone")
print("  dense paraphrase ('feline found resting') misses both hits: no shared term")

# ================= F2: RRF rank fusion =================
print("=" * 72)
print("F2  RRF rank fusion, k=60  [6201]")
DENSE = ["A", "B", "C"]
SPARSE = ["B", "D", "A"]


def rrf(rank_lists, k=60):
    acc = {}
    for ranks in rank_lists:
        for r, did in enumerate(ranks):
            acc[did] = acc.get(did, 0.0) + 1.0 / (k + r + 1)
    return sorted(acc.items(), key=lambda x: -x[1])


fused = rrf([DENSE, SPARSE])
for did, s in fused:
    print(f"  {did}: {s:.6f}")
print("  B wins: first-two in BOTH channels beats A's first + third")
print("  no score normalization needed - only ranks enter the sum")

# ================= F3: alpha fusion =================
print("=" * 72)
print("F3  hybrid alpha fusion, per-query min-max first  [6201]")
SEM = [1.0, 0.6, 0.0, 0.0]
LEX = [0.0, 0.6, 0.0, 1.0]
CNAMES = ["A", "B", "C", "D"]


def minmax(xs):
    lo, hi = min(xs), max(xs)
    return [(x - lo) / (hi - lo) for x in xs]


SEM_N, LEX_N = minmax(SEM), minmax(LEX)
for alpha in (0.9, 0.5, 0.1):
    fs = [alpha * s + (1 - alpha) * l for s, l in zip(SEM_N, LEX_N)]
    best = max(range(len(CNAMES)), key=lambda i: fs[i])
    cells = " ".join(f"{CNAMES[i]} {fs[i]:.4f}" for i in range(len(fs)))
    print(f"  alpha={alpha}: {cells}   winner {CNAMES[best]}")
print("  conceptual queries ride high alpha, exact-term queries low: sweep on MAP@10")

# ================= F4: rerank funnel + MaxSim =================
print("=" * 72)
print("F4  two-stage rerank funnel + ColBERT MaxSim  [6202]")
print("  stage 1: retrieve_n=100 (fast bi-encoder / hybrid)")
print("  stage 2: cross-encoder scores 100 (q,d) pairs, keeps top_k=10")
print("  budget: embed ~20ms + ANN ~10-30ms + CE 50-pair ~200-800ms (dominates)")
QEMB = [[1.0, 0.0], [0.0, 1.0]]
DOCEMB = [
    ("A", [[1.0, 0.1], [0.9, 0.0], [0.0, 0.9]]),
    ("B", [[0.2, 0.0], [0.0, 0.2]]),
]


def maxsim(q, d):
    return sum(max(dot(qt, dt) for dt in d) for qt in q)


scored = sorted(((name, maxsim(QEMB, d)) for name, d in DOCEMB),
                key=lambda x: -x[1])
print("  MaxSim: sum over query tokens of the best doc-token dot")
for name, s in scored:
    print(f"  doc {name}: {s:.4f}")

# ================= F5: AP and NDCG =================
print("=" * 72)
print("F5  AP and NDCG@4 on one labeled window  [6202]")


def average_precision(retrieved, relevant):
    hits, ps = 0, []
    for i, d in enumerate(retrieved):
        if d in relevant:
            hits += 1
            ps.append(hits / (i + 1))
    return sum(ps) / len(relevant) if relevant else 0.0


def ndcg(retrieved, rel_scores, k=4):
    dcg = sum((2 ** rel_scores.get(d, 0) - 1) / math.log2(i + 2)
              for i, d in enumerate(retrieved[:k]))
    ideal = sorted(rel_scores.values(), reverse=True)[:k]
    idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


REL = {"d1": 3, "d3": 2}
GOOD = ["d1", "d3", "d2", "d4"]
BAD = ["d2", "d1", "d3", "d4"]
print(f"  graded rel: {REL}")
print(f"  good {GOOD}: AP {average_precision(GOOD, REL):.4f}  NDCG@4 {ndcg(GOOD, REL):.4f}")
print(f"  bad  {BAD}: AP {average_precision(BAD, REL):.4f}  NDCG@4 {ndcg(BAD, REL):.4f}")

# ================= F6: MMR dial =================
print("=" * 72)
print("F6  MMR dial over the redundancy corpus  [6204]")
RAW = [
    ("D0", "P", [1.0, 0.0, 0.0, 0.0]), ("D1", "P", [1.0, 0.08, 0.0, 0.0]),
    ("D2", "P", [1.0, 0.0, 0.07, 0.0]), ("D3", "P", [1.0, 0.0, 0.0, 0.06]),
    ("D4", "L", [0.0, 1.0, 0.0, 0.0]), ("D5", "S", [0.0, 0.0, 1.0, 0.0]),
    ("D6", "I", [0.0, 0.0, 0.0, 1.0]), ("D7", "L", [0.06, 1.0, 0.0, 0.0]),
    ("D8", "X", [-0.5, -0.5, -0.5, -0.5]), ("D9", "P", [1.0, 1.0, 0.0, 0.0]),
]
IDS = [d[0] for d in RAW]
FACT = {d[0]: d[1] for d in RAW}
V = [unit(d[2]) for d in RAW]
Q = unit([1.0, 0.15, 0.1, 0.1])
REL6 = [dot(v, Q) for v in V]


def ils(sel):
    pairs = [dot(V[a], V[b]) for x, a in enumerate(sel) for b in sel[x + 1:]]
    return sum(pairs) / len(pairs)


def mmr(lam, k=5):
    sel = [max(range(len(IDS)), key=lambda i: REL6[i])]
    pool = [i for i in range(len(IDS)) if i != sel[0]]
    while len(sel) < k:
        best = max(pool, key=lambda i: lam * REL6[i]
                   - (1 - lam) * max(dot(V[i], V[j]) for j in sel))
        sel.append(best)
        pool.remove(best)
    return sel


def show(tag, sel):
    facts = [FACT[IDS[i]] for i in sel]
    cov = len(set(facts))
    rs = sum(REL6[i] for i in sel)
    print(f"  {tag}: {' '.join(IDS[i] for i in sel)}  facts {''.join(facts)}"
          f"  coverage {cov}/4  rel_sum {rs:.2f}  ILS {ils(sel):.2f}")


cos5 = sorted(range(len(IDS)), key=lambda i: -REL6[i])[:5]
show("cosine top-5", cos5)
for lam in (1.0, 0.7, 0.5, 0.0):
    show(f"MMR lam={lam:<3}", mmr(lam))
d8 = IDS.index("D8")
print(f"  lam=0.0 admits D8 at cosine {REL6[d8]:.3f}: diversity without relevance is noise")

# ================= F7: provenance boost =================
print("=" * 72)
print("F7  provenance boost and its placement  [6204]")
W = {"D0": 1.5, "D7": 1.5}
boosted = [REL6[i] * W.get(IDS[i], 1.0) for i in range(len(IDS))]
before = sorted(range(len(IDS)), key=lambda i: -REL6[i])[:5]
after = sorted(range(len(IDS)), key=lambda i: -boosted[i])[:5]
i0, i1 = IDS.index("D0"), IDS.index("D1")
i7 = IDS.index("D7")
print(f"  before: {' '.join(IDS[i] for i in before)}  "
      f"(D0 {REL6[i0]:.3f} loses to D1 {REL6[i1]:.3f})")
print(f"  x1.5  : {' '.join(IDS[i] for i in after)}  "
      f"(D0 -> {boosted[i0]:.3f}; D7 {REL6[i7]:.3f} -> {boosted[i7]:.3f} still unranked)")
SEM2 = [0.20, 0.95]
LEX2 = [1.00, 0.81]
AL, WT = 0.5, 1.5


def fused_pair(boost_lex):
    x = AL * SEM2[0] + (WT if boost_lex else 1.0) * (1 - AL) * LEX2[0]
    a = AL * SEM2[1] + (1 - AL) * LEX2[1]
    return x, a


bx, ba = fused_pair(False)
fx, fa = bx * WT, ba
cx, ca = fused_pair(True)
for tag, (x, a) in (("no boost     ", (bx, ba)),
                    ("x1.5 fused   ", (fx, fa)),
                    ("x1.5 channel ", (cx, ca))):
    win = "X" if x > a else "A"
    print(f"  {tag} X {x:.2f}  A {a:.2f}  winner {win}")
print("  fused boost adds +0.30 and flips; channel boost adds only (1-a)(w-1)lex = +0.25")
print("  and rewrites the document's effective alpha - place provenance on the fused score")

print("=" * 72)
print("FENCE-047-OK")
```

Its output, frozen byte-for-byte:

```text
========================================================================
F1  BM25 scratch (k1=1.5, b=0.75)  [6201]
  avgdl=5.4  N=5
  query 'cat' : d0 0.8338  d2 0.8338   <- exact TIE: same df=2, same dl=6
  query 'pets': d3 1.5694   <- df=1 rare term wins alone
  dense paraphrase ('feline found resting') misses both hits: no shared term
========================================================================
F2  RRF rank fusion, k=60  [6201]
  B: 0.032522
  A: 0.032266
  D: 0.016129
  C: 0.015873
  B wins: first-two in BOTH channels beats A's first + third
  no score normalization needed - only ranks enter the sum
========================================================================
F3  hybrid alpha fusion, per-query min-max first  [6201]
  alpha=0.9: A 0.9000 B 0.6000 C 0.0000 D 0.1000   winner A
  alpha=0.5: A 0.5000 B 0.6000 C 0.0000 D 0.5000   winner B
  alpha=0.1: A 0.1000 B 0.6000 C 0.0000 D 0.9000   winner D
  conceptual queries ride high alpha, exact-term queries low: sweep on MAP@10
========================================================================
F4  two-stage rerank funnel + ColBERT MaxSim  [6202]
  stage 1: retrieve_n=100 (fast bi-encoder / hybrid)
  stage 2: cross-encoder scores 100 (q,d) pairs, keeps top_k=10
  budget: embed ~20ms + ANN ~10-30ms + CE 50-pair ~200-800ms (dominates)
  MaxSim: sum over query tokens of the best doc-token dot
  doc A: 1.9000
  doc B: 0.4000
========================================================================
F5  AP and NDCG@4 on one labeled window  [6202]
  graded rel: {'d1': 3, 'd3': 2}
  good ['d1', 'd3', 'd2', 'd4']: AP 1.0000  NDCG@4 1.0000
  bad  ['d2', 'd1', 'd3', 'd4']: AP 0.5833  NDCG@4 0.6653
========================================================================
F6  MMR dial over the redundancy corpus  [6204]
  cosine top-5: D1 D2 D3 D0 D9  facts PPPPP  coverage 1/4  rel_sum 4.73  ILS 0.89
  MMR lam=1.0: D1 D2 D3 D0 D9  facts PPPPP  coverage 1/4  rel_sum 4.73  ILS 0.89
  MMR lam=0.7: D1 D2 D3 D0 D9  facts PPPPP  coverage 1/4  rel_sum 4.73  ILS 0.89
  MMR lam=0.5: D1 D5 D6 D4 D9  facts PSILP  coverage 4/4  rel_sum 2.13  ILS 0.15
  MMR lam=0.0: D1 D8 D5 D6 D4  facts PXSIL  coverage 5/4  rel_sum 0.67  ILS -0.20
  lam=0.0 admits D8 at cosine -0.661: diversity without relevance is noise
========================================================================
F7  provenance boost and its placement  [6204]
  before: D1 D2 D3 D0 D9  (D0 0.979 loses to D1 0.988)
  x1.5  : D0 D1 D2 D3 D9  (D0 -> 1.469; D7 0.205 -> 0.308 still unranked)
  no boost      X 0.60  A 0.88  winner A
  x1.5 fused    X 0.90  A 0.88  winner X
  x1.5 channel  X 0.85  A 0.88  winner A
  fused boost adds +0.30 and flips; channel boost adds only (1-a)(w-1)lex = +0.25
  and rewrites the document's effective alpha - place provenance on the fused score
========================================================================
FENCE-047-OK
```

## Known Failure Modes

| Trap | What it costs | The honest move |
| --- | --- | --- |
| Fusing raw scores across channels | BM25's open scale owns cosine's bounded one - the blend is one channel | min-max per query, or fuse ranks with RRF |
| Provenance boost on the clause, not the fusion | adds only (1 - a) * (w - 1) * lex = +0.25 and rewrites effective alpha: X loses 0.85 vs 0.88 | extract and boost on the fused score |
| lam 0.0 in MMR | D8 enters at cosine -0.661: junk with perfect spread | lam 0.5: coverage 4/4 at rel_sum 2.13 |
| fetch_k <= k in max_marginal_relevance_search | the candidate pool cannot express diversity | fetch_k at 3-5x k |
| Boosting to conjure a missing document | D7 at x1.5 goes 0.205 -> 0.308 and stays unranked | fix retrieval first (hybrid, transformation), then boost |
| Comparing configs without graded labels | 'it looks better' survives every ablation | AP / NDCG on a labeled window, one knob at a time |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| A paraphrase returns nothing | exact-term channel is vocabulary-blind: 'feline found resting' scores 0 | hybrid: BM25 + dense, RRF fuse |
| Top-5 is five paraphrases of one fact | redundancy: coverage 1/4, ILS 0.89 | MMR lam 0.5, fetch_k at 3-5x k |
| The right document ranked 4th | bi-encoder ceiling | the funnel: cross-encoder over retrieve_n = 100 |
| Reranking made it worse | no labels: the knob moved blind | AP / NDCG on a labeled window first |
| The winner flips between queries | the alpha dial moved: 0.9 -> A, 0.5 -> B, 0.1 -> D | sweep alpha on MAP@10, min-max per query |
| P95 blows past 1.5 s | the cross-encoder's 200-800 ms at 50 pairs dominates | cap retrieve_n, MiniLM-class CE on GPU, cache query embeddings |

## Quick Reference For

- [Module 6201: Hybrid Search - Combining Keyword and Semantic Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md) - the keyword-plus-semantic fusion this sheet's retrieval dial prices.
- [Module 6202: Re-ranking and Retrieval Logistics](../../phases/phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) - the re-rank stage and the logistics it adds to the path.
- [Module 6203: Advanced Retrieval Techniques](../../phases/phase6-rag/6200-retrieval/6203-Advanced-Retrieval.md) - the multi-hop and query-expansion moves this sheet schedules.
- [Module 6204: Diversification and Boosting](../../phases/phase6-rag/6200-retrieval/6204-Diversification-and-Boosting.md) - the diversification and boosting dials that keep the result list honest.
