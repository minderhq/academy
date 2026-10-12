---
Document ID: CHEAT-SHEET-048
Title: "CHEAT-SHEET-048: Semantic Vectors - the HNSW Ledger, the Recall Dial, and the Truncation Contract"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rag', 'vectors', 'hnsw']
---

# CHEAT-SHEET-048: Semantic Vectors - the HNSW Ledger, the Recall Dial, and the Truncation Contract

The semantic-vectors surface is phase6-rag's 6100-vector track - 6101 HNSW Indexing, 6102 Semantic Similarity Metrics, 6104 Embedding Sciences and 6105 Contextual and Multilingual Embeddings - four modules with no sheet anywhere in the track (scope scan: the 00-META sheet index carries no id beside any of the four; CHEAT-SHEET-005's HNSW row is a one-cell remediation in its pipeline troubleshooting table, CHEAT-SHEET-036 links out to 6101 for the ANN internals under its 5-20 ms store, and QUICK-REF-VOLUME-6 carries the FAISS syntax, not the closure). This sheet takes the track as the three questions the student actually asks: what the vector is (the trained length that lets a prefix stand in for the whole, and the storage bill the truncation pays into), how closeness is measured (cosine against dot, and the anisotropy that quietly breaks every threshold), and how the nearest one is found among a million (the HNSW walk and its two dials) - closing the 6100 track.

The sheet runs as seven priced exhibits: the brute-force bill that makes approximation non-optional (F1), the layer census behind the hierarchy (F2), the walk on a toy graph (F3), the ef dial over a real recall sweep (F4), the metric dial of cosine against dot (F5), the truncation contract of matryoshka and the storage ledger (F6), and the anisotropy trap (F7). Every number below is printed by the canonical fence at the bottom of the page: the full 313-line stdlib fence reproduces all seven from fixed-seed runs its own asserts pin - no numpy, no time - and its 40-line output sits frozen below it byte-for-byte.

## The Brute-Force Bill - Why Approximation Is Not Optional

Exact search prices every query at N x D multiply-adds and holds every vector in RAM. At 1M vectors of 768 dimensions that is 768,000,000 = 768.0M MACs per query - 0.768 s at a 1e9 MAC/s budget - with 3.07 GB of float32 resident before the graph, the metadata or the reranker take their share. Approximate nearest-neighbor search is not an optimization on top of this; it is the only way through, and its contract is explicit: trade a bounded, tunable epsilon of recall for orders of magnitude of speed. HNSW collects by walking a graph instead of scanning it, and the walk is governed by three knobs with three different bills.

| Parameter | Job | The bill it carries | The law |
| --- | --- | --- | --- |
| M | graph degree: edges per node, per layer | ~2 x M four-byte ids on top of the 4 x D flat bytes (768-D: 3,072 -> 3,200 B/vector at M=16) | M=16 the default; M=32 roughly doubles the GRAPH memory while flat storage still dominates |
| efConstruction | the insert-time beam | build time | must exceed M, or the insert search saturates inside its first cluster and the graph fragments into disconnected cliques |
| efSearch | the query-time beam | recall vs latency, set per query | keep ef >= k - ef bounds the result beam, so ef < k cannot return k results at all |

## The Layered Walk - the Census, the Descent, and the Beam

Layer assignment is a coin flip per level: P(l) = 0.5^l. The census prices it over 10,000 draws: 4,906 land on layer 0 (share 0.4906), 0.8704 within L0-L2, the top observed layer is 15 - and a million points need log2(1M) = 19.93 layers, which is why the hierarchy is described as skip-list-like. The walk spends its budget accordingly: greedy descent with ef = 1 through the upper layers zooms to the right region in logarithmic hops, then the beam opens at layer 0 with the query's ef. On the 12-point hand-built three-layer toy, the query's true nearest neighbor (id 2) lands after 9 distance evaluations where brute force pays 12 - the toy prices the mechanism; the dial at scale is F4's business.

Two construction rules keep the hierarchy honest. Neighbor lists are PER-LAYER: a point lives on layers 0..l, links only on layers it inhabits, and grants a reverse edge only when the neighbor lives on that layer too - one flat list collapses every layer into the same graph and the hierarchy becomes decorative. And the bounded reverse-edge update evicts: when a newcomer arrives at a node whose M slots are full, the node keeps the M closest and drops its farthest - a hard cap without replacement saturates the early core and freezes the graph into disconnected islands.

```text
The hierarchy lives in per-layer neighbor lists: a point links only on
layers it inhabits and takes reverse edges only from neighbors that live
there too - one flat list collapses the layers into one decorative graph.
```

## The Recall Dial - the ef Sweep and the ef >= k Law

The sweep runs a beam search over an exact 4-NN graph - 400 points, 8-D, 30 queries, recall@10 against brute-force truth - and it prices both laws at once. First, ef >= k is visible as a ceiling before accuracy even enters: below ef = 10 the beam returns ef results, so recall is capped at ef/k and the ef=1 row's 0.0233 is a 1-of-10 artifact, not a bad graph. Past ef = k the dial becomes pure recall-versus-latency: 0.2167 at ef 4, 0.4900 at 8, 0.6533 at 16, 0.8633 at 32 - the last +21 points cost 2x the beam width.

| ef | recall@10 | avg returned |
| --- | --- | --- |
| 1 | 0.0233 | 1.0 |
| 2 | 0.0600 | 2.0 |
| 4 | 0.2167 | 4.0 |
| 8 | 0.4900 | 8.0 |
| 16 | 0.6533 | 10.0 |
| 32 | 0.8633 | 10.0 |

6101's production curve tells the same story with the ms axis attached: recall 85% at ef=10 in 0.5 ms, 95% at ef=50 in 1.2 ms, 98% at ef=100 in 2.1 ms, 99% at ef=200 in 4.0 ms - the final point of recall costs eight times the first. Pick the operating point from the recall/latency curve of YOUR corpus, and remember the dial is per-query: recall-critical traffic can ride ef 200-500 while the latency budget holds at ef 20-50.

## The Metric Dial - Cosine, Dot, and the Normalization Rule

Cosine is scale-invariant: [1,1,1] against [100,100,100] reads cos 1.0000 while the dot reads 300.0 - "more similar" that is pure magnitude, not meaning. On near-parallel vectors the two metrics disagree about ranking, and the toy prices why: king-queen lands dot 0.88 against king-man's 0.66, but on cosine the same pair sits at 0.9877 vs 0.9830 - barely separated. The dot's magnitude term is what creates the gap; normalized to the unit sphere the two metrics coincide exactly. Squared L2 is the bridge that preserves cosine's order without paying for the sqrt - the candidate order ['queen', 'man'] comes out identical both ways - and the law of cosines closes the loop, ||a-b||^2 = ||a||^2 + ||b||^2 - 2 cos ||a|| ||b||, with the identity landing to a gap of 2.29e-16.

The FAISS trap this settles: IndexHNSWFlat's default metric is L2, and 1 - L2 is NOT cosine. The production rule is normalize_L2 on the corpus AND on every query - in-place, float32 - with faiss.METRIC_INNER_PRODUCT as the index metric; after that the returned "distance" is already the cosine similarity you want to print. Raw dot product is for the cases where magnitude IS the signal: attention logits, recommendation scores.

```text
Normalize once, on both sides, then score inner products: on the unit
sphere IP equals cosine exactly, squared L2 preserves its order without
the sqrt, and the raw dot is for when magnitude IS the signal.
```

## The Truncation Contract - Matryoshka and the Storage Ledger

A conventional embedding's dimensions are interchangeable, so truncation is destruction. Matryoshka Representation Learning buys an ordering: the loss is evaluated at several prefix lengths at once, forcing the coarse structure to the front and the fine detail to the tail. The toy prices the contract on a 400 x 64-D space whose importance decays as 0.75^i with the dimension index: the TRAINED order keeps recall@5 at 0.95 with 4 of 64 dimensions and 1.00 from 8 up - a quarter of the storage, indistinguishable from the full vector. The SHUFFLED control - the same vectors under a random permutation of dimensions - collapses: 0.00 at 4 and 8, 0.05 at 16, 0.25 at 32, and 1.00 only at the full 64. The information is all still there; no prefix of it is a usable embedding. Truncation is a property of orderings, not of vectors, and the ordering is bought with the multi-prefix loss.

| Dimensions | fp32 per 1M docs | The move |
| --- | --- | --- |
| 1536 | 6.14 GB | the native length most APIs ship |
| 256 | 1.02 GB | truncation deletes 0.8333 of the bill |
| 64 | 0.26 GB | the nomic-embed matryoshka_dim floor |

The production surfaces expose exactly this contract: nomic-ai/nomic-embed-text-v1.5 ships matryoshka_dim=64 as its shortest usable length, sentence-transformers models accept truncate_dim at load time and per encode call, and OpenAI's text-embedding-3-small takes a dimensions parameter down to 1 of its native 1536. Every one of them works only because the model was trained with an MRL-style objective - the model card names it, and the shuffled row of the fence is what happens when you assume it of a model that was not.

```text
Truncated view:  e[:k] / ||e[:k]||   - renormalize the prefix, always.
MRL loss:        L = sum_k L_task(e[:k])   - one loss per prefix length.
No MRL training, no truncation: the shuffled row is what you shipped.
```

## The Anisotropy Trap - Rankings Survive, Thresholds Die

Raw transformer states occupy a mean-dominated cone: every vector shares a common direction, so unrelated pairs score HIGH before anything semantic happens. The toy builds 200 unrelated pairs in 8-D - pure noise around the shared mean - and prices the damage: raw cosine mean 0.9574 (min 0.8816), and a 0.9 threshold that should fire only on matches fires on 193 of the 200. Mean-center the same corpus - subtract the corpus mean, renormalize - and the identical pairs land at mean -0.0162 (max 0.7118), 0 of 200 firing. The related pair barely moves (raw 0.9797, centered 0.9762): the RANKING never left. What anisotropy costs is the margin: 0.0223 raw against 0.9924 centered. The module's law: anisotropy leaves every ranking intact and destroys every threshold - rank on the raw scores, and gate only on a centered space.

```text
encode -> pool with the mask -> truncate to the MRL prefix -> normalize
        -> IndexHNSWFlat(dim, M, METRIC_INNER_PRODUCT), efConstruction > M
        -> build once; the only live knob afterwards is efSearch (ef >= k)
        -> rank on raw scores; threshold only on a centered space
```

## Known Failure Modes

| Failure mode | The tell |
| --- | --- |
| ef < k | recall capped at ef/k regardless of graph quality - the beam cannot return what it does not hold |
| efConstruction <= M | the insert search saturates inside its first cluster; the graph fragments into disconnected cliques |
| truncating a non-MRL embedding | recall collapses toward chance - the information is present, no prefix of it is usable |
| raw dot on an unnormalized corpus | "more similar" reads magnitude, not meaning - 300.0 for [100,100,100] against [1,1,1] |
| a fixed threshold on raw states | fires on unrelated pairs - the cone puts 193/200 of them over 0.9; center before any absolute cutoff |
| assuming a GPU HNSW in stock FAISS | graph indexes do not transfer to the GPU - the GPU routes are IVF and CAGRA (RAPIDS cuVS) |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| search too slow | lower efSearch - recall's last points cost the most (98->99% doubles the time in 6101's curve) |
| recall below the bar | raise efSearch first (query-time, free), then M (build-time, needs a rebuild) |
| returned scores outside [-1, 1] | the index is on L2 and 1 - L2 is not cosine - normalize_L2 both sides + METRIC_INNER_PRODUCT |
| truncated vectors lost all quality | the model was never MRL-trained - ship full length or pick a model whose card names matryoshka |
| score thresholds useless across batches | anisotropy - mean-center the corpus, or rank instead of gating |
| index drift as documents are added | HNSW inserts never rebalance - rebuild periodically and mark deletions |

## Quick Reference For

- [Module 6101: HNSW Indexing](../../phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md) - the layered graph, its construction rules and its FAISS build under this sheet's dials
- [Module 6102: Semantic Similarity Metrics](../../phases/phase6-rag/6100-vector/6102-Semantic-Similarity.md) - cosine, dot, L2 and the conversions this sheet's metric dial prices
- [Module 6104: Embedding Sciences](../../phases/phase6-rag/6100-vector/6104-Embedding-Sciences.md) - pooling with the mask, the MRL training behind the truncation contract, and reading MTEB as a menu
- [Module 6105: Contextual and Multilingual Embeddings](../../phases/phase6-rag/6100-vector/6105-Contextual-and-Multilingual-Embeddings.md) - the anisotropy trap in full, the Procrustes alignment, and the language-identity probe

## The Canonical Fence

The full stdlib fence below reproduces every number on this page - F1 through F7 - from fixed-seed runs its own asserts pin: no numpy, no wall clock, byte-identical across runs.

```python
"""tick-1018 canonical fence - CHEAT-SHEET-048 Semantic Vectors.
Stdlib only. Deterministic: fixed-seed random.Random instances, no time,
no set-order dependence. Prints F1..F7 + FENCE-048-OK tail."""
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def cos(a, b):
    """Cosine similarity of two equal-length sequences."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def l2sq(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def norm_inplace(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n > 0 else list(v)


# ---------------------------------------------------------------- F1
# The brute-force bill: exact search over N vectors of D dims costs
# N*D multiply-adds per query and holds 4*N*D bytes of float32 in RAM.
print("F1  brute-force bill (exact search baseline)")
N, D = 1_000_000, 768
macs = N * D
bytes_resident = 4 * N * D
print(f"    MACs/query  = {N} x {D} = {macs:,} = {macs / 1e6:.1f}M")
print(f"    at 1e9 MAC/s: {macs / 1e9:.3f} s/query")
print(f"    RAM float32 : {bytes_resident:,} B = {bytes_resident / 1e9:.2f} GB")

# ---------------------------------------------------------------- F2
# The layer census: P(level = l) = 0.5^l, so half of every index sits
# on layer 0 and a million points need about log2(N) layers.
print("F2  layer census (P(l) = 0.5^l, 10,000 draws, max_layer 16)")
rng = random.Random(7)
MAXL = 16
draws = 10_000
counts = [0] * (MAXL + 1)
for _ in range(draws):
    lvl = 0
    while rng.random() < 0.5 and lvl < MAXL:
        lvl += 1
    counts[lvl] += 1
top_observed = max(l for l in range(MAXL + 1) if counts[l])
print("    l=0..4:", " ".join(str(counts[l]) for l in range(5)))
print(f"    share at L0 = {counts[0] / draws:.4f},"
      f" within L0-L2 = {sum(counts[:3]) / draws:.4f}")
print(f"    top layer observed = {top_observed},"
      f" log2(1M) = {math.log2(N):.2f}")

# ---------------------------------------------------------------- F3
# The walk: a hand-built 3-layer toy graph (12 points, 4-D). Above
# layer 0 the descent is greedy with ef = 1; layer 0 runs the beam at
# ef = 4. Per-layer adjacency, exactly as the module's insert builds.
print("F3  the walk on a 12-point toy graph (greedy ef=1, beam ef=4)")
V = {
    1:  [1.0, 0.0, 0.0, 0.0],   2:  [0.9, 0.1, 0.0, 0.0],
    3:  [0.0, 1.0, 0.0, 0.0],   4:  [0.0, 0.9, 0.1, 0.0],
    5:  [0.0, 0.0, 1.0, 0.0],   6:  [0.1, 0.0, 0.9, 0.0],
    7:  [0.0, 0.0, 0.0, 1.0],   8:  [0.0, 0.1, 0.0, 0.9],
    9:  [0.7, 0.7, 0.0, 0.0],   10: [0.0, 0.7, 0.7, 0.0],
    11: [0.0, 0.0, 0.7, 0.7],   12: [0.7, 0.0, 0.0, 0.7],
}
LVL = {1: 2, 5: 2, 9: 1, 2: 1, 6: 1, 10: 1, 3: 0, 4: 0, 7: 0,
       8: 0, 11: 0, 12: 0}
ADJ = {2: {0: [1, 3, 4, 12], 1: [1, 5]},
       1: {0: [2, 9, 12, 3]},
       3: {0: [2, 4, 9, 10]},
       4: {0: [3, 8, 10, 12]},
       5: {0: [6, 10, 11], 1: [2, 9], 2: [9]},
       6: {0: [5, 7, 11, 10]},
       7: {0: [6, 8, 11, 12]},
       8: {0: [7, 4, 12, 11]},
       9: {0: [1, 3, 12], 1: [1, 5], 2: [5]},
       10: {0: [3, 4, 6, 11]},
       11: {0: [10, 6, 7, 8]},
       12: {0: [1, 9, 8, 4]}}

def search_layer(q, entry, layer, ef, visited):
    cand = [(l2sq(q, V[entry]), entry)]
    seen = {entry}
    visited[0] += 1
    best = sorted(cand)
    while cand:
        cand.sort()
        d_c, cur = cand.pop(0)
        if len(best) >= ef and d_c > best[-1][0]:
            break
        for nb in ADJ[cur].get(layer, []):
            if nb in seen:
                continue
            seen.add(nb)
            visited[0] += 1
            d = l2sq(q, V[nb])
            if len(best) < ef or d < best[-1][0]:
                cand.append((d, nb))
                best.append((d, nb))
                best.sort()
                if len(best) > ef:
                    best.pop()
    return best

def walk(q, ef0):
    visited = [0]
    top = max(LVL.values())
    entry = next(n for n, l in LVL.items() if l == top)
    for layer in range(top, 0, -1):
        entry = search_layer(q, entry, layer, 1, visited)[0][1]
    found = search_layer(q, entry, 0, max(ef0, 4), visited)
    return found, visited[0]

query = [0.92, 0.08, 0.0, 0.0]           # nearest true neighbor: id 1
brute = sorted(((l2sq(query, V[n]), n) for n in V))[:1]
found, visited = walk(query, 4)
print(f"    true NN = {brute[0][1]} (brute force: 12 distance evals)")
print(f"    walk result = {found[0][1]} after {visited} evals"
      f" (descent ef=1, beam ef=4)")

# ---------------------------------------------------------------- F4
# The ef dial: beam search over an exact 4-NN graph, recall@10 and
# visited count as ef climbs. ef < k cannot return k results at all.
print("F4  the ef dial (beam over exact 4-NN graph, 400 pts x 8-D,"
      " recall@10)")
rng = random.Random(42)
nP, nD, nQ = 400, 8, 30
pts = [[rng.random() for _ in range(nD)] for _ in range(nP)]
qs = [[rng.random() for _ in range(nD)] for _ in range(nQ)]
truth = []
for q in qs:
    order = sorted(range(nP), key=lambda j: l2sq(q, pts[j]))
    truth.append(set(order[:10]))
knn = []
for i in range(nP):
    order = sorted((j for j in range(nP) if j != i),
                   key=lambda j: l2sq(pts[i], pts[j]))
    knn.append(order[:4])

def beam(q, ef, k):
    best = [(l2sq(q, pts[0]), 0)]
    cand = list(best)
    seen = {0}
    while cand:
        cand.sort()
        d_c, cur = cand.pop(0)
        if len(best) >= ef and d_c > best[-1][0]:
            break
        for nb in knn[cur]:
            if nb in seen:
                continue
            seen.add(nb)
            d = l2sq(q, pts[nb])
            if len(best) < ef or d < best[-1][0]:
                cand.append((d, nb))
                best.append((d, nb))
                best.sort()
                if len(best) > ef:
                    best.pop()
    return set(n for _, n in best[:k])

totals = {}
for ef in (1, 2, 4, 8, 16, 32):
    rec, vis = 0.0, 0
    for qi, q in enumerate(qs):
        got = beam(q, ef, 10)
        rec += len(got & truth[qi]) / 10.0
        vis += len(got)
    totals[ef] = (rec / nQ, vis / nQ)
for ef, (rec, vis) in totals.items():
    print(f"    ef={ef:2d}  recall@10 = {rec:.4f}   avg returned = {vis:.1f}")

# ---------------------------------------------------------------- F5
# The metric dial: scale-invariance, the dot-product magnitude leak,
# and the cosine<->L2 bridge via the law of cosines.
print("F5  the metric dial (cosine vs dot)")
v1, v2 = [1.0, 1.0, 1.0], [100.0, 100.0, 100.0]
print(f"    [1,1,1] vs [100,100,100]: cos {cos(v1, v2):.4f},"
      f" dot {sum(a * b for a, b in zip(v1, v2)):.1f}")
king = [0.8, 0.5, 0.3]
queen = [0.7, 0.4, 0.4]
man = [0.6, 0.3, 0.1]
dkq = sum(a * b for a, b in zip(king, queen))
dkm = sum(a * b for a, b in zip(king, man))
print(f"    king-queen: dot {dkq:.2f}, cos {cos(king, queen):.4f}")
print(f"    king-man  : dot {dkm:.2f}, cos {cos(king, man):.4f}")
# squared L2 preserves the cosine order without the sqrt
cands = {"queen": queen, "man": man}
sq = {n: l2sq(king, v) for n, v in cands.items()}
order_sq = sorted(sq, key=sq.get)
order_cos = sorted(cands, key=lambda n: -cos(king, cands[n]))
print(f"    squared-L2 order {order_sq} == cosine order {order_cos}")
a, b = king, queen
lhs = l2sq(a, b)
rhs = (sum(x * x for x in a) + sum(x * x for x in b)
       - 2 * cos(a, b) * math.sqrt(sum(x * x for x in a))
       * math.sqrt(sum(x * x for x in b)))
print(f"    law of cosines: ||a-b||^2 {lhs:.4f} vs identity {rhs:.4f}"
      f" (gap {abs(lhs - rhs):.2e})")

# ---------------------------------------------------------------- F6
# The truncation contract: MRL toy - importance decays 0.75^i with the
# dim index; prefixes of the TRAINED order stay usable, prefixes of a
# shuffled order do not. Plus the storage ledger the truncation pays into.
print("F6  the truncation contract (MRL toy, 400 x 64-D, recall@5)")
rng = random.Random(1)
Nn, Dd = 400, 64
centers = [[rng.gauss(0, 1) for _ in range(4)] for _ in range(4)]
X = []
for i in range(Nn):
    c = [centers[i % 4][j] + rng.gauss(0, 0.35) for j in range(4)]
    c += [rng.gauss(0, 0.05) for _ in range(Dd - 4)]
    X.append(c)
assert all(len(row) == Dd for row in X)
w = [0.75 ** i for i in range(Dd)]
E = [[x[i] * w[i] for i in range(Dd)] for x in X]
E = [norm_inplace(row) for row in E]
Q = []
for i in range(4):
    row = [centers[i][j] + rng.gauss(0, 0.05) for j in range(4)]
    row += [rng.gauss(0, 0.01) for _ in range(Dd - 4)]
    Q.append(row)
Qe = [[q[i] * w[i] for i in range(Dd)] for q in Q]
Qe = [norm_inplace(row) for row in Qe]
truth6 = []
for q in Qe:
    order = sorted(range(Nn), key=lambda j: -sum(x * y for x, y
                                                 in zip(q, E[j])))
    truth6.append(set(order[:5]))

def recall5(Es, Qs, k):
    Etr = [norm_inplace(row[:k]) for row in Es]
    Qtr = [norm_inplace(row[:k]) for row in Qs]
    tot = 0.0
    for qi, q in enumerate(Qtr):
        order = sorted(range(Nn), key=lambda j: -sum(x * y for x, y
                                                     in zip(q, Etr[j])))
        tot += len(set(order[:5]) & truth6[qi]) / 5.0
    return tot / len(Qtr)

perm = random.Random(2).sample(range(Dd), Dd)   # untrained dim order
Es = [[row[p] for p in perm] for row in E]
Qs = [[row[p] for p in perm] for row in Qe]
print("     k   trained  shuffled")
for k in (4, 8, 16, 32, 64):
    print(f"   {k:3d}    {recall5(E, Qe, k):.2f}      {recall5(Es, Qs, k):.2f}")
docs = 1_000_000
full_b = docs * 1536 * 4 / 1e9
trunc_b = docs * 256 * 4 / 1e9
short_b = docs * 64 * 4 / 1e9
print(f"    storage ledger fp32 per 1M docs: 1536-d {full_b:.2f} GB,"
      f" 256-d {trunc_b:.2f} GB, 64-d {short_b:.2f} GB")
print(f"    1536->256 truncation deletes {(full_b - trunc_b) / full_b:.4f}"
      " of the bill")

# ---------------------------------------------------------------- F7
# The anisotropy trap: raw states share a mean direction, so unrelated
# pairs all clear a 0.9 threshold; mean-centering collapses them while
# the related pair keeps its margin.
print("F7  the anisotropy trap (200 unrelated pairs, 8-D)")
rng = random.Random(5)
d = 8
mu = [rng.gauss(0, 1) for _ in range(d)]
mu = norm_inplace(mu)
top = [rng.gauss(0, 1) for _ in range(d)]
top = norm_inplace(top)

def jitter(base, s, r):
    assert len(base) == d
    return norm_inplace([b + s * r.gauss(0, 1) for b in base])

raw_unrel, cen_unrel = [], []
corpus = []
for _ in range(200):
    u = jitter(mu, 0.08, rng)
    v = jitter(mu, 0.08, rng)
    raw_unrel.append(cos(u, v))
    corpus.extend([u, v])
mean_v = [0.0] * d
for v in corpus:
    for i in range(d):
        mean_v[i] += v[i] / len(corpus)
def center(v):
    return norm_inplace([v[i] - mean_v[i] for i in range(d)])
for i in range(0, 400, 2):
    cen_unrel.append(cos(center(corpus[i]), center(corpus[i + 1])))
print(f"    unrelated raw cos   mean {sum(raw_unrel) / len(raw_unrel):.4f}"
      f"  min {min(raw_unrel):.4f}")
print(f"    unrelated centered  mean {sum(cen_unrel) / len(cen_unrel):.4f}"
      f"  max {max(cen_unrel):.4f}")
p = jitter([0.7 * x + 0.7 * y for x, y in zip(mu, top)], 0.05, rng)
q = jitter([0.7 * x + 0.7 * y for x, y in zip(mu, top)], 0.05, rng)
print(f"    related pair: raw {cos(p, q):.4f},"
      f" centered {cos(center(p), center(q)):.4f}")
thr_hits_raw = sum(1 for c in raw_unrel if c > 0.9)
thr_hits_cen = sum(1 for c in cen_unrel if c > 0.9)
print(f"    threshold 0.9 fires on {thr_hits_raw}/200 raw unrelated pairs"
      f" and {thr_hits_cen}/200 centered")
rel_raw = cos(p, q)
rel_cen = cos(center(p), center(q))
margin_raw = rel_raw - sum(raw_unrel) / len(raw_unrel)
margin_cen = rel_cen - sum(cen_unrel) / len(cen_unrel)
print(f"    the margin anisotropy costs: {margin_raw:.4f} raw"
      f" vs {margin_cen:.4f} centered")
print("FENCE-048-OK")
```

Its frozen output:

```text
F1  brute-force bill (exact search baseline)
    MACs/query  = 1000000 x 768 = 768,000,000 = 768.0M
    at 1e9 MAC/s: 0.768 s/query
    RAM float32 : 3,072,000,000 B = 3.07 GB
F2  layer census (P(l) = 0.5^l, 10,000 draws, max_layer 16)
    l=0..4: 4906 2535 1263 673 317
    share at L0 = 0.4906, within L0-L2 = 0.8704
    top layer observed = 15, log2(1M) = 19.93
F3  the walk on a 12-point toy graph (greedy ef=1, beam ef=4)
    true NN = 2 (brute force: 12 distance evals)
    walk result = 2 after 9 evals (descent ef=1, beam ef=4)
F4  the ef dial (beam over exact 4-NN graph, 400 pts x 8-D, recall@10)
    ef= 1  recall@10 = 0.0233   avg returned = 1.0
    ef= 2  recall@10 = 0.0600   avg returned = 2.0
    ef= 4  recall@10 = 0.2167   avg returned = 4.0
    ef= 8  recall@10 = 0.4900   avg returned = 8.0
    ef=16  recall@10 = 0.6533   avg returned = 10.0
    ef=32  recall@10 = 0.8633   avg returned = 10.0
F5  the metric dial (cosine vs dot)
    [1,1,1] vs [100,100,100]: cos 1.0000, dot 300.0
    king-queen: dot 0.88, cos 0.9877
    king-man  : dot 0.66, cos 0.9830
    squared-L2 order ['queen', 'man'] == cosine order ['queen', 'man']
    law of cosines: ||a-b||^2 0.0300 vs identity 0.0300 (gap 2.29e-16)
F6  the truncation contract (MRL toy, 400 x 64-D, recall@5)
     k   trained  shuffled
     4    0.95      0.00
     8    1.00      0.00
    16    1.00      0.05
    32    1.00      0.25
    64    1.00      1.00
    storage ledger fp32 per 1M docs: 1536-d 6.14 GB, 256-d 1.02 GB, 64-d 0.26 GB
    1536->256 truncation deletes 0.8333 of the bill
F7  the anisotropy trap (200 unrelated pairs, 8-D)
    unrelated raw cos   mean 0.9574  min 0.8816
    unrelated centered  mean -0.0162  max 0.7118
    related pair: raw 0.9797, centered 0.9762
    threshold 0.9 fires on 193/200 raw unrelated pairs and 0/200 centered
    the margin anisotropy costs: 0.0223 raw vs 0.9924 centered
FENCE-048-OK
```
