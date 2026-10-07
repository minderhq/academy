---
Document ID: 6404
Title: "6404: Vector Compression and Quantization - Scalar, Binary, and Product as Working Code"
Phase: 6
Module: 6400
Last Updated: 2026-10-07
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'vector-db', 'quantization', 'performance']
---

# 6404: Vector Compression and Quantization - Scalar, Binary, and Product as Working Code

## Abstract

This module is named "Vector Databases" and has until now taught deployment ([6401](./6401-Qdrant-Setup.md)) and vendor comparison ([6402](./6402-Pinecone-vs-Weaviate.md)) - and never the compression mechanics its own quiz tests. Question 10 asks what quantization does to a vector collection's memory, and its review map leaned on [6401](./6401-Qdrant-Setup.md)'s single ScalarQuantization config snippet; Question 20 asks for the module's performance-tuning story and leaned on the [guide 6403](./guides/6403-Qdrant-Production-Deployment.md) ops table - the module tested compression it never taught. The vocabulary proves the gap is total: "product quantization" appears in zero lessons (the guide's options table says only "Product (PQ)"), "subvector", "asymmetric distance", and "ADC" appear NOWHERE in the corpus, and "codebook" exists only in model-weight contexts ([4101](../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md), [4103](../../phase4-quantization/4100-low-bit/4103-Double-Quantization.md), [4407](../../phase4-quantization/4400-advanced-techniques/4407-Ternary-Binary.md)) - a different domain entirely. The boundary is owned honestly: [6101](../6100-vector/6101-HNSW-Indexing.md) owns the graph walk the compression feeds (and explicitly defers "the index math behind it"), [6104](../6100-vector/6104-Embedding-Sciences.md) owns embedding-side int8 calibration before storage, [6202](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) owns the same over-fetch-then-rescore shape one abstraction up at cross-encoder cost, phase 4 owns quantization of MODEL weights, [6401](./6401-Qdrant-Setup.md) owns the config knobs, [the guide](./guides/6403-Qdrant-Production-Deployment.md) owns the ops story - and 6404 owns the mechanics themselves: scalar quantization's int8 range and the quantile trap, binary quantization's sign bits and the rescore that rescues them, product quantization's codebook split and its ADC lookups, and the oversampling economics that turn a lossy index back into a useful one.

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Memory Ledger](#the-memory-ledger)
- [Scalar Quantization: the int8 Range](#scalar-quantization-the-int8-range)
- [Binary Quantization: Sign as Storage](#binary-quantization-sign-as-storage)
- [Product Quantization: the Codebook Split](#product-quantization-the-codebook-split)
- [The Oversampling and Rescore Campaign](#the-oversampling-and-rescore-campaign)
- [Where Quantization Lives in the Stack](#where-quantization-lives-in-the-stack)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After this lesson you will be able to:

- Price what one production-scale collection (5,000,000 vectors x 768 dims) costs to hold in RAM four ways - 15.36 GB raw float32 against 3.84 GB scalar int8 (4x), 0.48 GB packed binary (32x), and 0.24 GB product-quantized at m=48 (64x) - with the codebooks themselves costing 0.8 MB, rounding error against the vectors they encode
- Implement scalar quantization (float32 to uint8 with per-dim bounds and dequantization) and read its trade honestly: naive min/max bounds stretch the per-dim range 2.5x to keep planted outliers exact and land recall@5 at 0.9550, while 1%/99% quantile bounds buy finer levels (mean error 0.0011 versus 0.0014) but clip the direction-carrying dims and DROP recall to 0.7650 - the knob is a measurement decision, not a default
- Implement binary quantization end to end - per-dim median threshold, bit packing, Hamming ranking via XOR and popcount - and show both its signal (11 bits to the true top-1 versus 29.5 to a random vector at 32x compression) and its limit at 64 dimensions (recall@10 0.3900 pure, where Qdrant's own docs warn 1-bit loses significant precision below ~1000 dims)
- Implement product quantization the Jegou way - m=8 subvectors, 256-centroid codebooks trained by k-means, one byte per subvector, ADC scoring by per-query table lookups - and recover from its 0.6225 floor to 0.9900 with 40 exact rescores against the originals
- Run the oversampling x rescore campaign and read its two honest laws: rescore with oversampling=1 is a no-op that pays 10 exact scores to return the same set (0.3900 both ways), and every 2x oversample buys back recall at 2x exact rescoring work - binary 0.6250 at 20 rescores, 0.8850 at 40, 0.9950 at 80
- Name Qdrant's actual defaults from the live docs: rescoring is enabled by DEFAULT only for binary quantization (and TurboQuant's low-bit modes), the docs' own example ships oversampling=2.0, and asymmetric quantization (v1.15.0+) pairs binary stored vectors with scalar8bit queries because "every dimension contributes the same +/-1 vote" in a binary query
- Place quantization in the stack: the HNSW walk ([6101](../6100-vector/6101-HNSW-Indexing.md)) is unchanged - compression changes the bytes, not the graph - and the same over-fetch-then-rescore shape returns in [6202](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) at cross-encoder cost

## The Memory Ledger

A vector database's defining constraint is not disk - it is RAM. The float32 vectors must sit in memory for the ANN index to search them at interactive latency, and 768-dimensional embeddings at float32 cost 3,072 bytes per vector before the graph overhead [6401](./6401-Qdrant-Setup.md) teaches. One mid-size RAG collection - five million vectors, one per chunk of a real corpus - prices out at 15.36 GB of vector storage alone. That fits a gaming GPU's VRAM. It does not fit the 16 GB VPS actually running the free tier.

```python
N, DIM = 5_000_000, 768              # one production-scale RAG collection
F32 = 4                              # bytes per float32 component
M_SUB = 48                           # PQ: 48 subvectors of 16 dims each
K = 256                              # Qdrant centroids per codebook -> one byte per index

f32_b = N * DIM * F32                # float32 raw
sq_b = N * DIM * 1                   # scalar int8
bq_b = N * (DIM // 8)                # binary 1-bit packed
pq_b = N * M_SUB                     # product: one codebook byte per subvector
cb_b = M_SUB * K * (DIM // M_SUB) * F32   # codebooks themselves

def _gb(b):
    return b / 1e9

print(f"RAM ledger: {N:,} vectors x {DIM} dims")
print(f"{'form':<24}{'B/vector':>10}{'total':>11}{'ratio':>8}")
for name, per, tot in [
    ("float32 (raw)", DIM * F32, f32_b),
    ("scalar int8 (SQ)", DIM, sq_b),
    ("binary 1-bit (BQ)", DIM // 8, bq_b),
    (f"product m={M_SUB} (PQ)", M_SUB, pq_b),
]:
    print(f"{name:<24}{per:>10,}{_gb(tot):>10.2f}GB{f32_b / tot:>7.0f}x")
print(f"codebook overhead: {M_SUB} codebooks x {K} centroids x {DIM // M_SUB} dims "
      f"x {F32}B = {_gb(cb_b) * 1024:.1f} MB against {N:,} compressed vectors")
print(f"verdict: the raw index needs {_gb(f32_b):.2f} GB of RAM to search fast;")
print(f"every compressed form fits a {_gb(sq_b):.2f} GB / {_gb(bq_b):.2f} GB / {_gb(pq_b):.2f} GB budget -")
print(f"and SQ's 4x costs ~1% accuracy while PQ's 64x costs real recall (F4 measures it).")
```

Compression is not an optimization here - it is the difference between the index fitting the machine and not. The three working forms Qdrant ships are scalar quantization (4x, int8 per component), binary quantization (32x, one bit per component), and product quantization (up to 64x, one codebook byte per subvector). The rest of this lesson implements all three from scratch, measures what each costs a ranking, and prices the knob that buys the loss back.

## Scalar Quantization: the int8 Range

Scalar quantization converts each float32 component (4 bytes) to a uint8 (1 byte) against per-dim bounds - 4x storage for free in exactness terms only if the bounds are chosen well. The mechanics: for each dimension, fix a range [lo, hi], map a value linearly to 0-255, store the byte, and reconstruct the float by the inverse map when scoring. Qdrant's version (available since v1.1.0) adds two facts from its documentation: the uint8 layout lets SIMD instructions compare eight components per instruction (search gets FASTER, not just smaller), and in their experiments the conversion error "is usually less than 1%".

The knob is `quantile`. Qdrant's docs: at quantile 0.99, "1% of extreme values will be excluded from the quantization bounds", and the parameter "only affects the resulting precision and not the memory footprint". The advice reads as free precision - but the fence shows both schemes on a corpus with 1% planted outlier dims (x6 magnitude, vectors unit-normalized the way real embeddings ship), and the result inverts the brochure:

```python
import math, random

random.seed(749)
DIM, N, Q = 64, 1200, 40

def _norm(v):
    s = math.sqrt(sum(x * x for x in v))
    return [x / s for x in v]

vecs, out_mask = [], []
for i in range(N):
    v, m = [], []
    for j in range(DIM):
        x = random.gauss(0.0, 1.0)
        is_out = random.random() < 0.01          # the outlier dims SQ must survive
        if is_out:
            x *= 6.0
        v.append(x)
        m.append(is_out)
    vecs.append(_norm(v))                        # real embeddings ship normalized
    out_mask.append(m)
queries = [_norm([random.gauss(0.0, 1.0) for _ in range(DIM)]) for _ in range(Q)]

cols = [sorted(v[j] for v in vecs) for j in range(DIM)]
lo_naive = [c[0] for c in cols]
hi_naive = [c[-1] for c in cols]
lo_q = [c[N // 100] for c in cols]               # 1st percentile
hi_q = [c[-(N // 100) - 1] for c in cols]        # 99th percentile (Qdrant quantile=0.99)

def _sq_row(v, los, his):
    return [max(0, min(255, int(round((x - los[j]) * 255.0 / (his[j] - los[j])))))
            for j, x in enumerate(v)]

def _deq_row(codes, los, his):
    return [los[j] + c * (his[j] - los[j]) / 255.0 for j, c in enumerate(codes)]

def _rank(q, data, k):
    order = sorted(range(len(data)), key=lambda i: -sum(a * b for a, b in zip(q, data[i])))
    return set(order[:k])

ref = [_rank(q, vecs, 5) for q in queries]
rng_naive = sum(h - l for l, h in zip(lo_naive, hi_naive)) / DIM
rng_q = sum(h - l for l, h in zip(lo_q, hi_q)) / DIM

print(f"\nscalar quantization: {N} unit vectors x {DIM} dims, 1% outlier dims (x6)")
print(f"{'scheme':<16}{'mean|err| 99%':>14}{'err@outlier':>13}{'recall@5':>10}{'B/vector':>10}")
for name, los, his in [("float32", None, None), ("naive min/max", lo_naive, hi_naive),
                       ("quantile 1/99", lo_q, hi_q)]:
    if los is None:
        print(f"{name:<16}{'-':>14}{'-':>13}{1.0000:>10.4f}{DIM * 4:>10,}  (identity)")
        continue
    esum = en = out_e = 0.0
    for i, v in enumerate(vecs):
        dq = _deq_row(_sq_row(v, los, his), los, his)
        for j in range(DIM):
            e = abs(dq[j] - v[j])
            if not out_mask[i][j]:
                esum += e
                en += 1
            else:
                out_e = max(out_e, e)
    got = []
    for q in queries:
        deq = [_deq_row(_sq_row(v, los, his), los, his) for v in vecs]
        got.append(_rank(q, deq, 5))
    rec = sum(len(a & b) for a, b in zip(ref, got)) / (Q * 5)
    print(f"{name:<16}{esum / en:>14.4f}{out_e:>13.4f}{rec:>10.4f}{DIM:>10,}")
print(f"mean per-dim range: naive {rng_naive:.3f} vs quantile {rng_q:.3f} "
      f"({rng_naive / rng_q:.1f}x stretch)")
print("verdict: quantile bought finer levels for the 99% (0.0011 vs 0.0014) but the")
print("planted outlier dims carried the vectors' direction - recall fell 0.9550 to")
print("0.7650. The knob is a measurement decision: clip noise tails, never the dims")
print("that steer the vector - 6104's 'normalize first, then per-dim calibration'.")
```

Naive min/max bounds keep every outlier exact (err@outlier 0.0034) but stretch the per-dim range 2.5x (1.443 versus 0.576), spending the 255 int8 levels across a range where the 99% live in a sliver - recall@5 falls to 0.9550. Quantile bounds give the 99% finer levels (mean error 0.0011 versus 0.0014) and clip the outliers to the bound (err@outlier 0.6729) - and recall falls to 0.7650, because the planted outlier dims are not noise: after normalization they are the dims that steer each vector, and clipping them clips the direction. This is exactly [6104's](../6100-vector/6104-Embedding-Sciences.md) troubleshooting row - "outlier components eat the per-dim int8 range; normalize first, then quantize with per-dim calibration" - turned into numbers: whether the extremes are noise tails (clip them) or signal dims (never clip them) is a property of YOUR embedding model, and the only way to know is to measure recall on your own collection, the benchmark-before-tuning rule [6401](./6401-Qdrant-Setup.md) already teaches.

## Binary Quantization: Sign as Storage

Binary quantization is the extreme: one bit per component. Qdrant thresholds each component against the per-dim median (a balanced split, so half the collection lands on each side), packs eight components into one byte, and compares vectors with Hamming distance - XOR the two bit-packed words, count the set bits. Storage falls from 256 bytes per 64-dim float32 vector to 8 bytes: 32x. The comparison is also the fastest of any form - Qdrant cites "up to a 40x speedup" - and the query side is asymmetric by nature: the query vector does NOT have to be binarized for the rescore stage, which matters because rescoring is enabled by DEFAULT only for binary quantization (and TurboQuant's 1/1.5/2-bit modes) - the one case Qdrant turns on automatically, with the docs recommending "using binary quantization only with rescoring enabled".

```python
import math, random

DIM, N, C, Q, KTOP = 64, 500, 8, 40, 10
random.seed(64)
_centers = [[random.gauss(0.0, 1.0) for _ in range(DIM)] for _ in range(C)]

def _norm(v):
    s = math.sqrt(sum(x * x for x in v))
    return [x / s for x in v]

orig = []
for i in range(N):
    c = _centers[i % C]
    orig.append(_norm([x + random.gauss(0.0, 0.6) for x in c]))
queries = []
for i in range(Q):
    c = _centers[i % C]
    queries.append(_norm([x + random.gauss(0.0, 0.6) for x in c]))

def _rank(q, data, k):
    order = sorted(range(len(data)), key=lambda i: -sum(a * b for a, b in zip(q, data[i])))
    return set(order[:k])

gt = [_rank(q, orig, KTOP) for q in queries]

med = [sorted(v[j] for v in orig)[N // 2] for j in range(DIM)]
packed = []
for v in orig:
    b = 0
    for j in range(DIM):
        if v[j] >= med[j]:
            b |= 1 << j
    packed.append(b)

def _qb(q):
    b = 0
    for j in range(DIM):
        if q[j] >= med[j]:
            b |= 1 << j
    return b

def _topk_bq(q, k):
    qb = _qb(q)
    scored = sorted((bin(qb ^ b).count("1"), i) for i, b in enumerate(packed))
    return set(i for _, i in scored[:k])

def _topk_rescore(q, k, cand):
    approx = sorted((bin(_qb(q) ^ b).count("1"), i) for i, b in enumerate(packed))
    short = [i for _, i in approx[:cand]]
    scored = sorted((-sum(a * x for a, x in zip(q, orig[i])), i) for i in short)
    return set(i for _, i in scored[:k])

h_bq = h_rs = 0
for q, g in zip(queries, gt):
    h_bq += len(g & _topk_bq(q, KTOP))
    h_rs += len(g & _topk_rescore(q, KTOP, 40))
t1 = queries[0]
gt1 = sorted(range(N), key=lambda i: -sum(a * b for a, b in zip(t1, orig[i])))[0]
h_true = bin(_qb(t1) ^ packed[gt1]).count("1")
h_rand = sum(bin(_qb(t1) ^ packed[i]).count("1") for i in range(0, N, 50)) / len(range(0, N, 50))

print(f"\nbinary quantization: {N} vectors x {DIM} dims, {C} clusters, rescore cand=40")
print(f"storage: {DIM * 4} B/vector (float32) -> {DIM // 8} B/vector (packed bits) "
      f"= {(DIM * 4) / (DIM // 8):.0f}x")
print(f"signal check: hamming to true top-1 = {h_true} vs {h_rand:.1f} to a random vector "
      f"(dim median split)")
print(f"recall@10 pure binary ranking : {h_bq / (Q * KTOP):.4f}")
print(f"recall@10 rescore top-40      : {h_rs / (Q * KTOP):.4f}")
print("verdict: at 64 dims the sign bits alone rank badly (Qdrant warns below ~1000 dims),")
print("but 40 exact rescores against the ORIGINALS recover most of it - rescore is not optional.")
```

The signal check says the bits DO rank - 11 bits of Hamming distance to the true top-1 against 29.5 to a random vector - but 64 dimensions is far below the ~1000 where Qdrant warns "1-bit compression resulted in significant data loss and precision drops", and the pure binary ranking lands 0.3900 recall@10. Forty exact rescores against the ORIGINAL float32 vectors recover it to 0.8850: the compressed index proposes, the originals dispose. For the close-to-zero problem Qdrant ships 2-bit binary (16x compression, buckets -1/0/1 encoded as 00/01/11) and 1.5-bit (24x) since v1.15.0, and the same version added asymmetric quantization (`query_encoding: scalar8bits`) - binary stored vectors scored by scalar-quantized queries, because a binary query gives "every dimension the same +/-1 vote" even where the component's sign is noise. Note [6401](./6401-Qdrant-Setup.md) pins qdrant/qdrant:v1.12.4, which predates the v1.15.0 features; [the guide](./guides/6403-Qdrant-Production-Deployment.md) deploys v1.19.1, which has them.

## Product Quantization: the Codebook Split

Product quantization is Jegou, Douze, and Schmid's 2011 scheme (TPAMI; the paper Qdrant's own PQ article builds on). Split each vector into m subvectors, quantize EACH subvector against its own codebook of 256 centroids (one byte - Qdrant fixes k=256 "so each centroid index can be represented by a single byte"), and store only the m byte-indices. Stored size is m bytes regardless of dimension, so the compression ratio is dim/m: at 768 dims, m=48 buys 16 dims per subvector and 64x. The codebooks are trained once by k-means over a sample of the collection and shared by every vector - the fence's eight codebooks cost 64 KB, paid once. Scoring a query is the Asymmetric Distance Computation (ADC) the corpus has never named: build a table of the query's distance to all 256 centroids in each subvector (m tables of 256 entries), then score any stored vector with m table LOOKUPS - no multiplication against stored data at all.

```python
import math, random

DIM, N, C, Q, KTOP = 64, 500, 8, 40, 10
M_SUB, DS = 8, 8                    # 8 subvectors x 8 dims
K, TRAIN, ITERS = 256, 256, 2       # Qdrant's 256 centroids -> one byte per subvector
random.seed(64)
_centers = [[random.gauss(0.0, 1.0) for _ in range(DIM)] for _ in range(C)]

def _norm(v):
    s = math.sqrt(sum(x * x for x in v))
    return [x / s for x in v]

orig = []
for i in range(N):
    c = _centers[i % C]
    orig.append(_norm([x + random.gauss(0.0, 0.6) for x in c]))
queries = []
for i in range(Q):
    c = _centers[i % C]
    queries.append(_norm([x + random.gauss(0.0, 0.6) for x in c]))

def _rank(q, data, k):
    order = sorted(range(len(data)), key=lambda i: -sum(a * b for a, b in zip(q, data[i])))
    return set(order[:k])

gt = [_rank(q, orig, KTOP) for q in queries]

random.seed(7491)                   # codebook-training draw (corpus draw above untouched)
codebooks = []
for s in range(M_SUB):
    pts = [orig[i][s * DS:(s + 1) * DS] for i in random.sample(range(N), TRAIN)]
    cents = [list(p) for p in random.sample(pts, K)]
    for _ in range(ITERS):
        assign = []
        for p in pts:
            best, bd = 0, None
            for ci, c in enumerate(cents):
                d = sum((a - b) ** 2 for a, b in zip(p, c))
                if bd is None or d < bd:
                    best, bd = ci, d
            assign.append(best)
        sums = [[0.0] * DS for _ in range(K)]
        cnts = [0] * K
        for p, a in zip(pts, assign):
            cnts[a] += 1
            for j in range(DS):
                sums[a][j] += p[j]
        for ci in range(K):
            cents[ci] = ([sums[ci][j] / cnts[ci] for j in range(DS)] if cnts[ci]
                         else list(random.choice(pts)))
    codebooks.append(cents)

codes = []
for v in orig:
    row = []
    for s in range(M_SUB):
        sub = v[s * DS:(s + 1) * DS]
        best, bd = 0, None
        for ci, c in enumerate(codebooks[s]):
            d = sum((a - b) ** 2 for a, b in zip(sub, c))
            if bd is None or d < bd:
                best, bd = ci, d
        row.append(best)
    codes.append(row)

def _topk_adc(q, k):
    tables = [[sum((a - b) ** 2 for a, b in zip(q[s * DS:(s + 1) * DS], c))
               for c in codebooks[s]] for s in range(M_SUB)]
    scored = sorted((sum(tables[s][codes[i][s]] for s in range(M_SUB)), i) for i in range(N))
    return set(i for _, i in scored[:k])

def _topk_rescore(q, k, cand):
    approx = []
    tables = [[sum((a - b) ** 2 for a, b in zip(q[s * DS:(s + 1) * DS], c))
               for c in codebooks[s]] for s in range(M_SUB)]
    for i in range(N):
        approx.append((sum(tables[s][codes[i][s]] for s in range(M_SUB)), i))
    short = [i for _, i in sorted(approx)[:cand]]
    scored = sorted((-sum(a * x for a, x in zip(q, orig[i])), i) for i in short)
    return set(i for _, i in scored[:k])

h_adc = h_rs = 0
for q, g in zip(queries, gt):
    h_adc += len(g & _topk_adc(q, KTOP))
    h_rs += len(g & _topk_rescore(q, KTOP, 40))

print(f"product quantization: {N} vectors x {DIM} dims -> m={M_SUB} subvectors "
      f"x {DS} dims, k={K} centroids")
print(f"storage: {DIM * 4} B/vector -> {M_SUB} B/vector = {(DIM * 4) / M_SUB:.0f}x "
      f"(ratio = dim/m; Qdrant x4..x64 via m)")
print(f"codebooks: {M_SUB} x {K} x {DS} floats = {M_SUB * K * DS * 4 / 1024:.0f} KB "
      f"- paid once, amortized over every vector")
print(f"recall@10 pure ADC table scan : {h_adc / (Q * KTOP):.4f}")
print(f"recall@10 rescore top-40      : {h_rs / (Q * KTOP):.4f}")
print("verdict: ADC scores a query with m table lookups per vector - no SIMD mul-add,")
print("which is why Qdrant calls PQ slower than SQ and 'only for high-dimensional vectors'.")
```

The numbers: 32x storage at m=8, pure ADC ranking at 0.6225 recall@10 - better than binary's 0.3900 floor because eight centroid indices per vector carry more geometry than eight bytes of sign - and 0.9900 with 40 rescores. The costs are real: k-means training at ingest, and ADC's table lookups are not SIMD-friendly - Qdrant's docs call PQ slower than scalar and recommend it "only for high-dimensional vectors", with the comparison table's warning that it is for when "the memory footprint is the top priority and accuracy and speed are not critical". The newer alternative in the same config panel is TurboQuant (4-bit by default, 8x, with 1/1.5/2-bit modes) - the same ledger this lesson builds governs it.

## The Oversampling and Rescore Campaign

Two knobs sit between a lossy index and a useful one, and Qdrant's `QuantizationSearchParams` names both: `rescore` (re-rank the candidates against the original vectors) and `oversampling` (pre-select MORE candidates before the rescore - the docs' own arithmetic: "with oversampling 2.4 and limit 100, 240 vectors are pre-selected"). The fence runs both methods through the campaign - brute scans over the compressed forms (the HNSW candidate walk they sit inside is [6101's](../6100-vector/6101-HNSW-Indexing.md) subject; compression changes the bytes the walk scores, not the walk):

```python
import math, random

DIM, N, C, Q, KTOP = 64, 500, 8, 40, 10
M_SUB, DS = 8, 8
K, TRAIN, ITERS = 256, 256, 2
random.seed(64)
_centers = [[random.gauss(0.0, 1.0) for _ in range(DIM)] for _ in range(C)]

def _norm(v):
    s = math.sqrt(sum(x * x for x in v))
    return [x / s for x in v]

orig = []
for i in range(N):
    c = _centers[i % C]
    orig.append(_norm([x + random.gauss(0.0, 0.6) for x in c]))
queries = []
for i in range(Q):
    c = _centers[i % C]
    queries.append(_norm([x + random.gauss(0.0, 0.6) for x in c]))

def _rank(q, data, k):
    order = sorted(range(len(data)), key=lambda i: -sum(a * b for a, b in zip(q, data[i])))
    return set(order[:k])

gt = [_rank(q, orig, KTOP) for q in queries]

med = [sorted(v[j] for v in orig)[N // 2] for j in range(DIM)]
packed = []
for v in orig:
    b = 0
    for j in range(DIM):
        if v[j] >= med[j]:
            b |= 1 << j
    packed.append(b)

def _qb(q):
    b = 0
    for j in range(DIM):
        if q[j] >= med[j]:
            b |= 1 << j
    return b

def _bq_cand(q, cand):
    qb = _qb(q)
    scored = sorted((bin(qb ^ b).count("1"), i) for i, b in enumerate(packed))
    return [i for _, i in scored[:cand]]

random.seed(7491)
codebooks = []
for s in range(M_SUB):
    pts = [orig[i][s * DS:(s + 1) * DS] for i in random.sample(range(N), TRAIN)]
    cents = [list(p) for p in random.sample(pts, K)]
    for _ in range(ITERS):
        assign = []
        for p in pts:
            best, bd = 0, None
            for ci, c in enumerate(cents):
                d = sum((a - b) ** 2 for a, b in zip(p, c))
                if bd is None or d < bd:
                    best, bd = ci, d
            assign.append(best)
        sums = [[0.0] * DS for _ in range(K)]
        cnts = [0] * K
        for p, a in zip(pts, assign):
            cnts[a] += 1
            for j in range(DS):
                sums[a][j] += p[j]
        for ci in range(K):
            cents[ci] = ([sums[ci][j] / cnts[ci] for j in range(DS)] if cnts[ci]
                         else list(random.choice(pts)))
    codebooks.append(cents)

codes = []
for v in orig:
    row = []
    for s in range(M_SUB):
        sub = v[s * DS:(s + 1) * DS]
        best, bd = 0, None
        for ci, c in enumerate(codebooks[s]):
            d = sum((a - b) ** 2 for a, b in zip(sub, c))
            if bd is None or d < bd:
                best, bd = ci, d
        row.append(best)
    codes.append(row)

def _pq_cand(q, cand):
    tables = [[sum((a - b) ** 2 for a, b in zip(q[s * DS:(s + 1) * DS], c))
               for c in codebooks[s]] for s in range(M_SUB)]
    scored = sorted((sum(tables[s][codes[i][s]] for s in range(M_SUB)), i) for i in range(N))
    return [i for _, i in scored[:cand]]

def _campaign(name, cand_fn):
    print(f"{name:<5}{'mode':<14}{'recall@10':>11}{'exact-scores/query':>20}")
    hits = 0
    for q, g in zip(queries, gt):
        hits += len(g & set(cand_fn(q, KTOP)[:KTOP]))
    print(f"{'':<5}{'rescore off':<14}{hits / (Q * KTOP):>11.4f}{0:>20,}")
    for os_f in (1, 2, 4, 8):
        hits = scores = 0
        for q, g in zip(queries, gt):
            short = cand_fn(q, min(N, os_f * KTOP))
            scored = sorted((-sum(a * x for a, x in zip(q, orig[i])), i) for i in short)
            got = set(i for _, i in scored[:KTOP])
            hits += len(g & got)
            scores += len(short)
        print(f"{'':<5}{f'os={os_f} rescore':<14}{hits / (Q * KTOP):>11.4f}{scores // Q:>20,}")
    return

print(f"\noversampling x rescore campaign: {N} vectors x {DIM} dims, limit={KTOP}")
print("(approx stage = brute scan of the compressed form; HNSW's candidate walk is 6101's)")
_campaign("BQ", _bq_cand)
_campaign("PQ", _pq_cand)
print("verdict: rescore off is the floor the compression itself sets; every 2x oversample")
print("buys back recall at 2x exact rescoring work - Qdrant's example ships oversampling=2.0.")
```

Read the table's first two rows together: rescore=on with oversampling=1 re-scores the SAME ten candidates the compressed ranking already picked - recall identical to rescore=off (0.3900), ten exact scores spent for nothing. Rescoring without oversampling is a no-op; oversampling is the knob that widens the rescore pool, and each doubling buys back recall at exactly doubled exact-scoring cost - binary climbs 0.6250 at 20 rescores, 0.8850 at 40, 0.9950 at 80, product reaches 1.0000 at 80 from its higher 0.6225 floor. The floors are the compression's irreducible cost: no amount of rescoring can recover a candidate the compressed ranking never surfaced. Qdrant's own docs example ships `oversampling: 2.0` - the first rung of exactly this ladder - and this is the same over-fetch-then-rescore shape [6202](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) teaches one abstraction up at cross-encoder cost: propose wide with the cheap ranker, re-rank deep with the expensive one.

## Where Quantization Lives in the Stack

The map a reader needs when a config panel says "quantization": [6101](../6100-vector/6101-HNSW-Indexing.md) owns the HNSW graph walk the quantized scores feed - the graph is unchanged by compression, which is why quantization and HNSW tuning compose (and why [6401](./6401-Qdrant-Setup.md)'s recall-knobs ladder and this lesson's rescore ladder are different ladders on the same wall). [6104](../6100-vector/6104-Embedding-Sciences.md) owns what happens BEFORE storage - normalize, calibrate per-dim - the preparation this fence's outlier trap punishes skipping. [6202](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) owns the same over-fetch-then-rescore economics at the pipeline level with cross-encoders. Phase 4 ([4103](../../phase4-quantization/4100-low-bit/4103-Double-Quantization.md), [4407](../../phase4-quantization/4400-advanced-techniques/4407-Ternary-Binary.md)) owns quantization of MODEL WEIGHTS - the GGUF/AWQ/GPTQ domain, where the thing compressed is what computes, not what is searched; the word "codebook" in those lessons is a different object entirely. [6401](./6401-Qdrant-Setup.md) owns the collection-config surface these mechanics sit behind; [the guide](./guides/6403-Qdrant-Production-Deployment.md) owns the ops story of running it; and 6404 owns what the compression actually does to a vector.

## Summary

A 5,000,000-vector, 768-dim collection is 15.36 GB of float32 - and compression is the line between fitting the machine and not: scalar int8 takes it to 3.84 GB (4x), packed binary to 0.48 GB (32x), product quantization at m=48 to 0.24 GB (64x), with codebooks a rounding-error 0.8 MB. Scalar quantization is the near-free default (SIMD-fast, usually under 1% error) whose quantile knob is a measurement decision - the fence shows clipping direction-carrying outlier dims DROPS recall from 0.9550 to 0.7650. Binary quantization is the fastest and smallest (32x, up to 40x faster) but at 64 dims its pure ranking manages only 0.3900 - which is why Qdrant enables rescoring by default for binary and for it alone. Product quantization stores m bytes per vector regardless of dimension, scores by ADC table lookups, and trades SIMD speed for the best compressed floor (0.6225). The campaign closes the loop: rescore alone recovers nothing at oversampling=1, and every 2x oversample buys recall back at 2x exact-scoring cost - binary to 0.9950 and product to 1.0000 at 80 rescores - the economics behind every production quantization config.

## References

### Related Minder Academy Documents

- [6401: Qdrant Setup Guide](./6401-Qdrant-Setup.md) - the collection-config surface (ScalarQuantization snippet, HNSW memory rule of thumb) these mechanics sit behind.
- [6402: Pinecone vs Weaviate](./6402-Pinecone-vs-Weaviate.md) - the vendor-comparison surface; serverless tiers price the RAM this lesson compresses.
- [6403: Qdrant Production Deployment](./guides/6403-Qdrant-Production-Deployment.md) - the ops guide whose quantization options table and rescore/oversampling config this lesson gives mechanics to.
- [6101: HNSW Indexing](../6100-vector/6101-HNSW-Indexing.md) - the graph walk the quantized scores feed; its GPU list name-drops GpuIndexIVFPQ without mechanics.
- [6104: Embedding Sciences](../6100-vector/6104-Embedding-Sciences.md) - the normalize-then-calibrate row this lesson's outlier trap turns into numbers.
- [6202: Re-ranking and Retrieval Logistics](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) - the same over-fetch-then-rescore shape at cross-encoder cost.
- [4103: Double Quantization](../../phase4-quantization/4100-low-bit/4103-Double-Quantization.md) - quantization of model weights, the different domain sharing the vocabulary.

### Primary Sources

- Jegou, H., Douze, M., & Schmid, C. (2011). *Product Quantization for Nearest Neighbor Search.* IEEE Transactions on Pattern Analysis and Machine Intelligence 33(1), 117-128 (HAL inria-00514462) - the subvector split, the 256-centroid codebooks, and ADC; no arXiv version exists - cite the journal entry.
- Lloyd, S. P. (1982). *Least Squares Quantization in PCM.* IEEE Transactions on Information Theory 28(2), 129-137 - the k-means that trains the codebooks.
- Qdrant. *Quantization.* Qdrant documentation, [manage-data/quantization](https://qdrant.tech/documentation/manage-data/quantization/) (live-verified 2026-10-07) - scalar/binary/product configs, the comparison table (4x/32x/up to 64x), the quantile parameter, QuantizationSearchParams rescore/oversampling semantics, TurboQuant, and asymmetric quantization (v1.15.0+).
- Qdrant. *Scalar Quantization* and *Product Quantization* articles - the under-1%-error experiments, the SIMD uint8 comparison, and PQ's 256-centroids-one-byte design. [articles/scalar-quantization](https://qdrant.tech/articles/scalar-quantization/) and [articles/product-quantization](https://qdrant.tech/articles/product-quantization/)
- Qdrant. *Large-scale search* tutorial - the two-stage prefetch (rescore=False in RAM) over rescore=True on disk pattern at oversampling factor 20. [tutorials-operations/large-scale-search](https://qdrant.tech/documentation/tutorials-operations/large-scale-search/)

## Next Steps

- **Next Module:** continue with [assessment/QUIZ.md](assessment/QUIZ.md) - Q10 and Q20 are the questions this lesson answers; the 4x/32x/64x ledger, the 0.9550-versus-0.7650 quantile inversion, the 11-versus-29.5 Hamming signal, and the os=1 rescore no-op are the mechanics behind them.
- **Continue with:** [6101: HNSW Indexing](../6100-vector/6101-HNSW-Indexing.md) for the graph walk the compressed scores feed, or [6202: Re-ranking and Retrieval Logistics](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) for the same rescore shape with cross-encoders.
- **Assessment:** re-run the product-quantization fence with m=16 instead of 8 and state what happens to the compression ratio (8x) and the recall floor; then re-run the campaign with limit=5 and check whether the os=1 no-op row still equals the rescore-off row - and explain why it must.

**Estimated Time:** 3 hours
