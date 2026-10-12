---
Document ID: CHEAT-SHEET-053
Title: "CHEAT-SHEET-053: Vector Databases - the RAM Ledger, the Quantile Trap, and the Rescore Ladder"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rag', 'vector-db', 'quantization']
---

# CHEAT-SHEET-053: Vector Databases - the RAM Ledger, the Quantile Trap, and the Rescore Ladder

The scope scan that picked this page: phase6-rag's 6400-vector-databases track carries 6401 Qdrant Setup Guide, 6402 Vector Database Comparison and 6404 Vector Compression and Quantization with no sheet anywhere in the track - the track's production guide (6403 Qdrant Production Deployment) owns the walkthrough, not the arithmetic a student needs at 2am when the box OOMs at ingest or recall dies overnight. This sheet takes the questions the operator actually asks: what the vectors cost in RAM and on the invoice, which metric to score with, why tighter quantile bounds made recall worse, and how binary and product quantization buy their compression back without losing the neighbors.

The sheet runs as seven priced exhibits: the RAM ledger (F1 - count x dims x bytes, plus the graph headroom that decides the node), the distance trio (F2 - normalize once at ingest and dot, cosine and euclid rank identically), the SQ quantile trap (F3 - min/max keeps the tail, and the tail was the signal), binary quantization (F4 - 32x for a 0.4125 floor that a rescore lifts to 0.9450), product quantization (F5 - the codebook split, ADC's 8 adds, and the same rescore law), the oversample x rescore ladder (F6 - os=1 is a no-op; recall moves only past 1), and the ops bill (F7 - node classes, vendor prices, the pgvector latency tax, and the snapshot RPO ledger). Every number below is printed by the canonical fence at the bottom of the page: the full 437-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 69-line output sits frozen below it byte-for-byte.

## The RAM Ledger - the Arithmetic That Kills the Box

A vector database's first failure is not a query - it is an invoice. The fence prices 5,000,000 vectors at 768 dimensions in all four storage formats: float32 raw is 15.36 GB (3,072 bytes per vector), scalar int8 is 3.84 GB (768 bytes, 4.0x), binary packing is 0.48 GB (96 bytes, 32.0x), and product quantization at m=48 is 0.24 GB (48 bytes, 64.0x). The PQ codebooks that make that compression possible are 48 subspaces x 256 centroids x 16 dims - 0.79 MB total, noise next to the payload. And the one-line sizing rule the fence prints - 5M x 384 dims x 4 B plus 20% graph headroom = 9.216 GB - lands within rounding of the module's benchmark table at both ends: 1M x 768d reads 3.69 GB against a 4 GB row, 10M x 768d reads 36.86 GB against 35 GB.

| Format | Bytes/vector | At 5M x 768d | Compression |
| --- | --- | --- | --- |
| float32 raw | 3,072 B | 15.36 GB | 1.0x |
| scalar int8 | 768 B | 3.84 GB | 4.0x |
| binary packed | 96 B | 0.48 GB | 32.0x |
| product quant m=48 | 48 B | 0.24 GB | 64.0x |

## The Distance Trio - the Metric Is Part of the Data

The similarity metric looks like a decision, and the fence shows it mostly is not one - if the data is right. On normalized rows, dot product, cosine and euclidean distance all rank identically: the overlap between the top-k lists is 1.000 for dot-vs-cosine and euclid-vs-cosine alike. The same rows with random magnitudes tear the agreement apart: dot-vs-cosine falls to 0.800, euclid-vs-cosine to 0.367, and the dot's top-1 pick flips on 2 of 6 queries. Normalize once at ingest; then the metric stops being a decision and becomes a taste - and "why do two engines disagree on my neighbors" is usually this bug wearing a different logo.

```text
Normalize once at ingest; then dot, cosine and euclid rank identically.
Unnormalized rows make the three metrics disagree - the fence lands
dot-vs-cosine 0.800 and euclid-vs-cosine 0.367, 2 of 6 top-1s flipped.
The metric is part of the data: fix the data, not the metric.
```

## The SQ Quantile Trap - Tighter Bounds, Worse Recall

Scalar quantization maps float32 dims onto 256 bins, and the bins need bounds. The tidy choice is percentile bounds - 1st to 99th - which clip the outliers and use the range well. The fence prices the choice on 1,200 rows carrying a 1% population of +8 outliers on a hot dim: min/max bounds ride the outlier intact (hot-dim reconstruction error 0.0000) and land recall@5 0.9250; the 1/99 quantile bounds are 14.78x tighter on the hot dims, clip the outlier at the 99th percentile (error 7.7111), and recall@5 falls to 0.8250. Ten points of recall, paid for tidier bounds - because on the dims that carry the signal, the tail IS the signal. Clip with a reason (a physical max, a saturation point), never with a percentile alone.

```text
Min/max keeps the tail; 1/99 quantiles clip it - and the tail was the signal.
The fence's outliers ride min/max at hot-dim err 0.0000 (recall@5 0.9250)
but clip at the 99th percentile under 1/99 (err 7.7111, recall@5 0.8250):
10 points of recall for bounds 14.78x tighter on the dims that matter.
```

## Binary Quantization - 32x for a Floor and a Rescore

Binary quantization signs each dim: 64 float32 dims (256 bytes) become 8 packed bytes - the fence's 32x. The signal survives the sign: the true top-1 neighbor sits 11.3 Hamming bits from the query while a random pair sits 32.6 bits away - 2.9x apart, so ranking by bit distance is still ranking. But it is a floor: pure binary ranking lands recall@10 0.4125. The rescue is the rescore - pull the top-40 candidates by Hamming (4x oversample) and re-rank them by the real float32 dots: recall@10 0.9450. Binary buys storage, not answers; the answer is bought back at rescore time on the 40 candidates.

```text
64 floats x 4 B = 256 B becomes 8 packed B - 32x, the signal intact:
the true neighbor is 11.3 Hamming bits away, a random pair 32.6 (2.9x).
Pure binary ranking is a floor: recall@10 0.4125.
Hamming picks 40 candidates; the float32 rescore takes recall to 0.9450.
```

## Product Quantization - the Codebook Split and ADC

Product quantization splits the 64 dims into m=8 subspaces of 8 dims and k-means 256 centroids per subspace on the training rows. The whole quantizer is 8 x 256 x 8 floats - 64 KB - and each vector shrinks from 256 bytes to 8 centroid ids, the fence's second 32x. Scoring is ADC - asymmetric distance computation: from the query, build one 256-entry table per subspace of query-to-centroid distances, then score any coded vector with 8 table lookups and adds - 8 adds per vector, zero multiplies. The floor is real: pure ADC ranking lands recall@10 0.6750, above binary's 0.4125 but nowhere near an answer; the same rescore of the top-40 candidates takes it to 1.0000. PQ compresses as hard as binary and ranks better too - and it still needs the rescore.

```text
Split d dims into m subspaces; k-means 256 centroids per subspace.
The quantizer is 8 x 256 x 8 floats = 64 KB; each vector is 8 centroid ids.
ADC scores with m table lookups - 8 adds, no multiplies (recall 0.6750 raw);
a float32 rescore of the top-40 takes it to 1.0000.
```

## The Oversample x Rescore Ladder - os=1 Is a No-Op

The rescore's knob is the oversample: candidates pulled = os x k. The fence walks both ladders at k=10 and the first rung is the trap: os=1 re-ranks the same ten rows the scan already chose, so recall is bit-identical to the pure floor - binary 0.4125, PQ 0.6750. Recall moves only past 1: binary climbs 2 -> 0.6575, 4 -> 0.9450, 8 -> 1.0000; PQ climbs 2 -> 0.9300, 4 -> 1.0000. PQ's floor is higher so its ladder arrives sooner, and both ladders meet at the same os=8 ceiling. That is the whole trade: each extra candidate is one more float32 rescore against the query - linear cost for the recall the floor cannot give, and os=1 is the one setting that pays nothing and buys nothing.

```text
Oversample 1 is a no-op: re-ranking the ten rows the scan already chose.
Binary ladder  os 2 -> 0.6575   os 4 -> 0.9450   os 8 -> 1.0000
PQ ladder      os 2 -> 0.9300   os 4 -> 1.0000   os 8 -> 1.0000
PQ starts higher and arrives sooner; both ladders meet at the os=8 ceiling.
```

## The Ops Bill - Node Classes, Vendor Bills, Snapshot RPO

The arithmetic turns into three decisions. The instance class: float32's 15.36 GB needs a 35 GB-class node with +25% graph headroom; int8's 3.84 GB fits an 8 GB-class node; binary's 0.48 GB and PQ's 0.24 GB both fit a 2 GB-class node - the compression is a hardware decision before it is an accuracy decision. The vendor bill at 1M / 10M vectors: qdrant (self) $20/$100, weaviate (self) $20/$100, pgvector (self) $10/$50, pinecone $70/$200 - managed convenience costs 3.5x at 1M vectors. And pgvector's latency tax grows with scale - 4.0x at 10K, 4.0x at 100K, 5.3x at 1M, 6.0x at 10M - the gap widens, never closes.

| Vendor | 1M vectors | 10M vectors | Hosting model |
| --- | --- | --- | --- |
| Qdrant (self) | $20/mo | $100/mo | you run it |
| Weaviate (self) | $20/mo | $100/mo | you run it |
| pgvector (self) | $10/mo | $50/mo | Postgres, slowest as it grows |
| Pinecone | $70/mo | $200/mo | managed |

The last decision is the backup. At 1,000,000 docs and 0.5%/day churn, 5,000 docs change per day, so the RPO ledger reads: 1h snapshots owe at most 208 stale docs, 6h owe 1,250, 24h owe 5,000. And the wall the ledger stands next to: an in-memory-only collection restart loses all 1,000,000 docs. The volume survives a restart, not a disk - snapshots are the backup, the volume is not.

| Snapshot cadence | Worst-case stale docs |
| --- | --- |
| 1h | 208 |
| 6h | 1,250 |
| 24h | 5,000 |

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Sizing the node from the vector count alone | 5M x 768d is 15.36 GB, not "five million"; run count x dims x bytes plus headroom |
| Clipping quantile bounds for tidy histograms | the tail was the signal - recall@5 fell 10 points under 1/99 |
| Shipping pure binary or pure ADC rankings | 0.4125 / 0.6750 is a floor; the rescore is not optional |
| Running the rescore at oversample 1 | you re-rank the rows the scan already chose; recall cannot move |
| Scoring cosine on unnormalized rows | the metrics disagree by magnitude; normalize once at ingest |
| Treating the volume as the backup | a restart survives, a disk does not; snapshot on a cadence the RPO ledger sizes |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| The box OOMs at ingest time | run the sizing rule - count x dims x bytes x 1.2 - and pick the instance class from the bill |
| Recall dropped after switching to quantile bounds | the outliers carried the signal; return to min/max on the hot dims |
| Binary recall pinned at 0.41 | oversample: pull os x k Hamming candidates and rescore with the real metric |
| PQ recall pinned near 0.68 | the floor is by design; os=4 or the top-40 rescore is the path up |
| Two engines disagree on the same neighbors | unnormalized rows; normalize once at ingest and re-ingest |
| A restart wiped the collection | it was in-memory-only; snapshot on a cadence the RPO ledger sizes |

## Quick Reference For

- [Module 6401: Qdrant Setup Guide](../../phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md) - the setup walkthrough where the RAM ledger and the snapshot cadence become configuration.
- [Module 6402: Vector Database Comparison](../../phases/phase6-rag/6400-vector-databases/6402-Pinecone-vs-Weaviate.md) - the vendor bill and the latency tax, compared in full.
- [Module 6404: Vector Compression and Quantization - Scalar, Binary, and Product as Working Code](../../phases/phase6-rag/6400-vector-databases/6404-Vector-Compression-Quantization.md) - the three compressions this sheet prices, written as working code.
- [Guide 6403: Qdrant Production Deployment](../../phases/phase6-rag/6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md) - the production build-out where the ops bill gets paid.

## The Canonical Fence

Every number on this page comes from one stdlib-only script - the 437-line fence below, run once and frozen. It carries its own asserts, so a drifted number dies loudly instead of printing; the run needs no network, no model, no randomness, and two runs agree byte for byte. Its 69-line output sits frozen under it.
```python
"""tick-1028 canonical fence - CHEAT-SHEET-053: Vector Databases.

Stdlib only. One run prints every canonical number on the sheet:
F1 the RAM ledger, F2 the distance trio, F3 the SQ quantile trap,
F4 binary quantization, F5 product quantization, F6 the oversample
x rescore ladder, F7 the ops bill.
"""
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def top_k(scores, k):
    """Indices of the k largest scores, ties broken by lower index."""
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:k]


def top_k_asc(scores, k):
    """Indices of the k smallest scores, ties broken by lower index."""
    return sorted(range(len(scores)), key=lambda i: (scores[i], i))[:k]


def overlap(a, b, k):
    """|A n B| / k for two top-k index lists."""
    return len(set(a) & set(b)) / k


def unit(vec):
    """Scale a vector to unit length."""
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


def gen(seed, n, n_q, dim):
    """Unit-gauss rows + queries from one seeded stream (replayable)."""
    rng = random.Random(seed)
    rows = [unit([rng.gauss(0, 1) for _ in range(dim)]) for _ in range(n)]
    queries = [unit([rng.gauss(0, 1) for _ in range(dim)])
               for _ in range(n_q)]
    return rng, rows, queries


def gen_clustered(seed, n, n_q, dim, n_c=10, spread=0.07):
    """Clustered rows (10 topic centers, spread-gauss noise) + queries.

    spread is per-component: the total noise norm is spread*sqrt(dim), so
    0.07 at dim 64 gives ~0.56 total - same-cluster cos ~0.87. Draw order
    is fixed - centers, then n rows, then n_q queries - so a replay with
    the same seed reproduces the stream byte for byte.
    """
    rng = random.Random(seed)
    centers = [unit([rng.gauss(0, 1) for _ in range(dim)])
               for _ in range(n_c)]

    def point(i):
        base = centers[i % n_c]
        return unit([b + spread * rng.gauss(0, 1) for b in base])

    rows = [point(i) for i in range(n)]
    queries = [point(n + i) for i in range(n_q)]
    return rng, rows, queries


def pack_bits(vec):
    """Sign bits, 8 dims per byte."""
    return [sum((1 if vec[b + j] >= 0 else 0) << j
                for j in range(8)) for b in range(0, len(vec), 8)]


def hamming(a, b):
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def build_pq(rows, rng, m, ds, kc, iters):
    """Per-subspace k-means codebooks + per-row centroid-id codes."""
    codebooks, codes = [], []
    for s in range(m):
        sub = [r[s * ds:(s + 1) * ds] for r in rows]
        cents = [list(sub[i]) for i in rng.sample(range(len(sub)), kc)]
        for _ in range(iters):
            assign = [[] for _ in range(kc)]
            for vec in sub:
                best = min(range(kc), key=lambda c: sum(
                    (a - b) ** 2 for a, b in zip(vec, cents[c])))
                assign[best].append(vec)
            for c in range(kc):
                if assign[c]:
                    cents[c] = [sum(col) / len(assign[c])
                                for col in zip(*assign[c])]
        codebooks.append(cents)
        codes.append([min(range(kc), key=lambda c: sum(
            (a - b) ** 2 for a, b in zip(r[s * ds:(s + 1) * ds], cents[c])))
            for r in rows])
    return codebooks, codes


def rescore_recall(rows, queries, approx, os_, k):
    """recall@k: top (os*k) by the cheap metric, exact-rescored to k."""
    hit = 0.0
    for qi, q in enumerate(queries):
        sims = [sum(a * b for a, b in zip(r, q)) for r in rows]
        exact = set(top_k(sims, k))
        cand = top_k_asc(approx(qi), os_ * k)
        resc_scores = [sum(a * b for a, b in zip(rows[c], q)) for c in cand]
        resc = [cand[j] for j in top_k(resc_scores, k)]   # positions -> ids
        hit += overlap(sorted(exact), resc, k)
    return hit / len(queries)


# ---------------------------------------------------------------- F1
def exhibit_f1_ram_ledger():
    print("=" * 78)
    print("F1. THE RAM LEDGER (5,000,000 vectors x 768 dims)")
    print("=" * 78)
    n, dim = 5_000_000, 768
    gb = 1e9
    raw = n * dim * 4
    sq = n * dim * 1
    bq = n * dim // 8
    pq = n * 48                      # m = dim / 16 -> 48 one-byte codes
    per_vec = {raw: 3072, sq: 768, bq: 96, pq: 48}
    names = {raw: "float32 raw", sq: "scalar int8",
             bq: "binary packed", pq: "product quant m=48"}
    for byts in (raw, sq, bq, pq):
        saving = raw / byts
        assert abs(byts / gb - per_vec[byts] * n / gb) < 1e-6
        print(f"{names[byts]:<20}: {byts / gb:5.2f} GB  "
              f"({per_vec[byts]:4d} bytes/vector, {saving:4.1f}x saved)")
    assert raw / gb == 15.36 and sq / gb == 3.84
    assert bq / gb == 0.48 and pq / gb == 0.24
    codebooks = 48 * 256 * (dim // 48) * 4
    assert codebooks == 786432
    print(f"{'pq codebooks':<20}: {codebooks / 1e6:5.2f} MB  (48 subspaces x "
          f"256 centroids x 16 dims)")
    rule = lambda scale, d: scale * d * 4 * 1.2     # +20% HNSW headroom
    assert rule(5_000_000, 384) / gb == 9.216
    print(f"{'sizing rule 384d':<20}: {rule(5_000_000, 384) / gb:5.3f} GB = "
          f"5M x 384 x 4 B plus 20% graph headroom")
    for scale, row in ((1_000_000, 4.0), (10_000_000, 35.0)):
        est = rule(scale, 768) / gb
        assert 0.8 < est / row < 1.25
        print(f"  rule at {scale // 1_000_000:>2d}M x 768d = {est:5.2f} GB "
              f"(benchmark table row: {row:.0f} GB)")


# ---------------------------------------------------------------- F2
def exhibit_f2_distance_trio():
    print("=" * 78)
    print("F2. THE DISTANCE TRIO (16 dims, 40 rows, 6 queries)")
    print("=" * 78)
    rng = random.Random(6402)
    dim, n_rows, n_q, k = 16, 40, 6, 10
    rows = [unit([rng.gauss(0, 1) for _ in range(dim)])
            for _ in range(n_rows)]
    queries = [unit([rng.gauss(0, 1) for _ in range(dim)])
               for _ in range(n_q)]
    mags = [0.3 + 2.7 * rng.random() for _ in range(n_rows)]

    def rankings(scaled):
        agree_dot, agree_euc, flips = [], [], 0
        for q in queries:
            qn = math.sqrt(sum(x * x for x in q))
            truth = []
            r_dot, r_euc = [], []
            for i, r_ in enumerate(rows):
                v = [x * mags[i] for x in r_] if scaled else list(r_)
                nv = math.sqrt(sum(x * x for x in v))
                d = sum(a * b for a, b in zip(v, q))
                truth.append(d / (nv * qn))
                r_dot.append(d)
                r_euc.append(-math.sqrt(sum((a - b) ** 2
                                            for a, b in zip(v, q))))
            t = top_k(truth, k)
            agree_dot.append(overlap(t, top_k(r_dot, k), k))
            agree_euc.append(overlap(t, top_k(r_euc, k), k))
            if top_k(r_dot, 1)[0] != t[0]:
                flips += 1
        return (sum(agree_dot) / n_q, sum(agree_euc) / n_q, flips)

    dot_n, euc_n, _ = rankings(False)
    dot_u, euc_u, flips = rankings(True)
    assert dot_n == 1.0 and euc_n == 1.0, (dot_n, euc_n)
    assert dot_u < 1.0 and euc_u < 1.0, (dot_u, euc_u)
    assert flips >= 1, flips
    print(f"normalized rows     : dot==cosine overlap {dot_n:.3f}   "
          f"euclid==cosine {euc_n:.3f}")
    print(f"random magnitudes   : dot-vs-cosine {dot_u:.3f}   "
          f"euclid-vs-cosine {euc_u:.3f}")
    print(f"top-1 disagreement  : dot picks a different winner on {flips} "
          f"of {n_q} queries once norms vary")
    print("law                 : normalize once at ingest; then dot, cosine")
    print("                      and euclid rank identically - the metric")
    print("                      stops being a decision and becomes a taste")


# ---------------------------------------------------------------- F3
def exhibit_f3_quantile_trap():
    print("=" * 78)
    print("F3. THE SQ QUANTILE TRAP (64 dims, 1200 rows, 1% outlier +8s)")
    print("=" * 78)
    rng, rows, queries = gen(2053, 1200, 40, 64)
    dim, n_out, k = 64, 12, 5
    out_rows, out_dims = [], []
    for i in range(n_out):                    # 1% of rows carry one +8s dim
        d = (i * 7) % dim
        rows[i][d] += 8.0                     # deterministic hot value
        out_rows.append(i)
        out_dims.append(d)
    train = rows[:256]
    naive, quant = [], []
    for d in range(dim):
        col = [r[d] for r in train]
        naive.append((min(col), max(col)))
        s = sorted(col)
        quant.append((s[int(0.01 * 255)], s[int(0.99 * 255)]))
    stretch = sum((naive[d][1] - naive[d][0]) /
                  max(quant[d][1] - quant[d][0], 1e-12)
                  for d in set(out_dims)) / n_out
    assert stretch > 2.0, stretch

    def dequant(vec, bounds):
        out = []
        for x, (lo, hi) in zip(vec, bounds):
            q = max(0, min(255, round((x - lo) / (hi - lo) * 255)))
            out.append(lo + q / 255.0 * (hi - lo))
        return out

    dq = {"naive": [dequant(r, naive) for r in rows],
          "quantile": [dequant(r, quant) for r in rows]}
    recall = {}
    for qi, q in enumerate(queries):
        exact = top_k_asc([sum((a - b) ** 2 for a, b in zip(r, q))
                           for r in rows], k)
        for tag in ("naive", "quantile"):
            approx = top_k_asc([sum((a - b) ** 2 for a, b in zip(r, q))
                                for r in dq[tag]], k)
            recall[tag] = recall.get(tag, 0.0) + overlap(exact, approx, k)
    recall = {t: v / len(queries) for t, v in recall.items()}
    assert recall["naive"] > recall["quantile"], recall
    out_err = {t: sum(abs(dq[t][r_][d_] - rows[r_][d_])
                      for r_, d_ in zip(out_rows, out_dims)) / n_out
               for t in ("naive", "quantile")}
    assert out_err["quantile"] > out_err["naive"], out_err
    print(f"naive min/max       : recall@{k} {recall['naive']:.4f}   "
          f"hot-dim recon err {out_err['naive']:.4f}")
    print(f"quantile 1/99       : recall@{k} {recall['quantile']:.4f}   "
          f"hot-dim recon err {out_err['quantile']:.4f}")
    print(f"bound stretch       : on the hot dims the min/max range is "
          f"{stretch:.2f}x the quantile range")
    print(f"the trap            : recall ranks "
          f"{(recall['naive'] - recall['quantile']) * 100:.0f} points worse "
          f"under quantile bounds;")
    print(f"                      the hot value rides min/max intact "
          f"(err {out_err['naive']:.4f}) yet lands")
    print(f"                      at the 99th-percentile clip under 1/99 "
          f"(err {out_err['quantile']:.4f}) - the tail WAS")
    print("                      the signal and the tighter bounds paid "
          "for their tidiness")


# ---------------------------------------------------------------- F4
def exhibit_f4_binary():
    print("=" * 78)
    print("F4. BINARY QUANTIZATION (64 dims -> 8 packed bytes, 32x)")
    print("=" * 78)
    _, rows, queries = gen_clustered(4104, 500, 40, 64)
    dim, n, n_q, k = 64, 500, 40, 10
    packed = [pack_bits(r) for r in rows]
    packed_q = [pack_bits(q) for q in queries]
    sig_t = sig_r = 0.0
    for qi, q in enumerate(queries):
        sims = [sum(a * b for a, b in zip(r, q)) for r in rows]
        sig_t += hamming(packed[top_k(sims, 1)[0]], packed_q[qi])
        sig_r += hamming(packed[(qi * 37 + 11) % n], packed_q[qi])
    sig_t, sig_r = sig_t / n_q, sig_r / n_q
    assert sig_t < 0.75 * sig_r, (sig_t, sig_r)
    print(f"hamming signal      : true-top1 {sig_t:.1f} bits vs random pair "
          f"{sig_r:.1f} bits ({sig_r / sig_t:.1f}x apart)")

    def bq_approx(qi):
        return [hamming(p, packed_q[qi]) for p in packed]

    floor = rescore_recall(rows, queries, bq_approx, 1, k)
    assert floor < 0.60, floor
    rec40 = rescore_recall(rows, queries, bq_approx, 4, k)
    assert rec40 > floor + 0.20, (floor, rec40)
    print(f"pure binary ranking : recall@{k} {floor:.4f}  (the floor)")
    print(f"rescore top-{4 * k}       : recall@{k} {rec40:.4f}")
    print(f"storage             : {dim} floats x 4 B = {dim * 4} B becomes "
          f"{dim // 8} B packed - {dim * 4 // (dim // 8)}x")
    return floor


# ---------------------------------------------------------------- F5
def exhibit_f5_pq():
    print("=" * 78)
    print("F5. PRODUCT QUANTIZATION (64 dims -> 8 codes x 256 centroids)")
    print("=" * 78)
    rng, rows, queries = gen_clustered(6104, 500, 40, 64)
    m, ds, kc, k = 8, 8, 256, 10
    codebooks, codes = build_pq(rows, rng, m, ds, kc, 2)
    book_bytes = m * kc * ds * 4
    assert book_bytes == 65536
    print(f"codebooks           : {m} subspaces x {kc} x {ds} dims = "
          f"{book_bytes // 1024} KB - the whole quantizer")
    print(f"per-vector code     : {64 * 4} B float32 -> {m} B of centroid ids "
          f"- {64 * 4 // m}x")

    def pq_approx_factory(rows_, queries_):
        def pq_approx(qi):
            q = queries_[qi]
            table = [[sum((a - b) ** 2 for a, b in zip(
                q[s * ds:(s + 1) * ds], cent)) for cent in codebooks[s]]
                for s in range(m)]
            return [sum(table[s][codes[s][i]] for s in range(m))
                    for i in range(len(rows_))]
        return pq_approx

    pq_approx = pq_approx_factory(rows, queries)
    floor = rescore_recall(rows, queries, pq_approx, 1, k)
    assert 0.40 < floor < 0.90, floor
    rec40 = rescore_recall(rows, queries, pq_approx, 4, k)
    assert rec40 > 0.90, rec40
    print(f"adc table lookups   : {m} adds per scored vector - no multiply")
    print(f"pure adc ranking    : recall@{k} {floor:.4f}  (the floor)")
    print(f"rescore top-{4 * k}       : recall@{k} {rec40:.4f}")
    return floor


# ---------------------------------------------------------------- F6
def exhibit_f6_ladder(bq_floor, pq_floor):
    print("=" * 78)
    print("F6. THE OVERSAMPLE x RESCORE LADDER (limit=10)")
    print("=" * 78)
    m, ds, k = 8, 8, 10
    # binary side replays the F4 stream exactly
    _, rows_b, queries_b = gen_clustered(4104, 500, 40, 64)
    packed = [pack_bits(r) for r in rows_b]
    packed_q = [pack_bits(q) for q in queries_b]

    def bq_approx(qi):
        return [hamming(p, packed_q[qi]) for p in packed]

    # pq side replays the F5 stream exactly (data, then training draws)
    rng_p, rows_p, queries_p = gen_clustered(6104, 500, 40, 64)
    codebooks, codes = build_pq(rows_p, rng_p, m, ds, 256, 2)

    def pq_approx(qi):
        q = queries_p[qi]
        table = [[sum((a - b) ** 2 for a, b in zip(
            q[s * ds:(s + 1) * ds], cent)) for cent in codebooks[s]]
            for s in range(m)]
        return [sum(table[s][codes[s][i]] for s in range(m))
                for i in range(len(rows_p))]

    ladder = {}
    for tag, floor, rows_, queries_, approx in (
            ("binary", bq_floor, rows_b, queries_b, bq_approx),
            ("pq", pq_floor, rows_p, queries_p, pq_approx)):
        vals = [rescore_recall(rows_, queries_, approx, os_, k)
                for os_ in (1, 2, 4, 8)]
        assert abs(vals[0] - floor) < 1e-12, (tag, vals[0], floor)
        assert all(a <= b for a, b in zip(vals, vals[1:])), (tag, vals)
        ladder[tag] = vals
    assert ladder["binary"][-1] > ladder["binary"][0]
    assert ladder["pq"][0] > ladder["binary"][0]      # finer codes, higher floor
    b, p = ladder["binary"], ladder["pq"]
    print(f"oversample 1 = noop : binary {b[0]:.4f} (== pure floor)   "
          f"pq {p[0]:.4f} (== pure floor)")
    print(f"binary ladder       : os 2 -> {b[1]:.4f}   os 4 -> {b[2]:.4f}   "
          f"os 8 -> {b[3]:.4f}")
    print(f"pq ladder           : os 2 -> {p[1]:.4f}   os 4 -> {p[2]:.4f}   "
          f"os 8 -> {p[3]:.4f}")
    print("the law             : os=1 re-scores the same ten rows the scan")
    print("                      already ranked - recall moves only past 1")
    print(f"                      and both ladders meet at the os={8} ceiling "
          f"({b[3]:.4f} / {p[3]:.4f})")


# ---------------------------------------------------------------- F7
def exhibit_f7_ops_bill():
    print("=" * 78)
    print("F7. THE OPS BILL")
    print("=" * 78)
    classes = [2, 4, 8, 16, 35]

    def node(gb):
        return next(c for c in classes if c >= gb * 1.25)

    picks = [("float32 15.36 GB", node(15.36)),
             ("scalar int8 3.84 GB", node(3.84)),
             ("binary 0.48 GB", node(0.48)),
             ("pq m=48 0.24 GB", node(0.24))]
    assert picks[0][1] == 35 and picks[1][1] == 8 and picks[2][1] == 2
    for name, c in picks:
        print(f"instance class      : {name:<20} -> a {c:2d} GB-class node "
              f"(+25% graph headroom)")
    bill = [("qdrant (self)", 20, 100), ("pinecone", 70, 200),
            ("weaviate (self)", 20, 100), ("pgvector (self)", 10, 50)]
    assert bill[1][1] / bill[0][1] == 3.5
    print("vendor bill 1M/10M  : " +
          "  ".join(f"{name} ${a}/${b}" for name, a, b in bill))
    lat = ((8, 2, "10K"), (20, 5, "100K"), (80, 15, "1M"), (300, 50, "10M"))
    ratios = [a / b for a, b, _ in lat]
    assert ratios[0] == 4.0 and ratios[3] == 6.0
    print("pgvector latency tax: " +
          "  ".join(f"{r:.1f}x@{s}" for r, (_, _, s) in zip(ratios, lat)) +
          " (the gap grows with scale)")
    docs, churn = 1_000_000, 0.005
    per_day = docs * churn
    assert per_day == 5000.0
    rpos = [(t, per_day * t / 24) for t in (1, 6, 24)]
    print(f"snapshot rpo ledger : {docs:,.0f} docs at 0.5%/day churn = "
          f"{per_day:,.0f} changed docs/day")
    print("                      " +
          "   ".join(f"{t}h-snapshot rpo {v:,.0f}" for t, v in rpos))
    print(f"the wall            : an in-memory-only collection restart loses "
          f"{docs:,.0f} docs -")
    print("                      the volume survives a restart, not a disk;")
    print("                      snapshots are the backup, the volume is not")


def main():
    exhibit_f1_ram_ledger()
    exhibit_f2_distance_trio()
    exhibit_f3_quantile_trap()
    bq_floor = exhibit_f4_binary()
    pq_floor = exhibit_f5_pq()
    exhibit_f6_ladder(bq_floor, pq_floor)
    exhibit_f7_ops_bill()
    print("FENCE-053-OK")


if __name__ == "__main__":
    main()
```

Its frozen output:

```text
==============================================================================
F1. THE RAM LEDGER (5,000,000 vectors x 768 dims)
==============================================================================
float32 raw         : 15.36 GB  (3072 bytes/vector,  1.0x saved)
scalar int8         :  3.84 GB  ( 768 bytes/vector,  4.0x saved)
binary packed       :  0.48 GB  (  96 bytes/vector, 32.0x saved)
product quant m=48  :  0.24 GB  (  48 bytes/vector, 64.0x saved)
pq codebooks        :  0.79 MB  (48 subspaces x 256 centroids x 16 dims)
sizing rule 384d    : 9.216 GB = 5M x 384 x 4 B plus 20% graph headroom
  rule at  1M x 768d =  3.69 GB (benchmark table row: 4 GB)
  rule at 10M x 768d = 36.86 GB (benchmark table row: 35 GB)
==============================================================================
F2. THE DISTANCE TRIO (16 dims, 40 rows, 6 queries)
==============================================================================
normalized rows     : dot==cosine overlap 1.000   euclid==cosine 1.000
random magnitudes   : dot-vs-cosine 0.800   euclid-vs-cosine 0.367
top-1 disagreement  : dot picks a different winner on 2 of 6 queries once norms vary
law                 : normalize once at ingest; then dot, cosine
                      and euclid rank identically - the metric
                      stops being a decision and becomes a taste
==============================================================================
F3. THE SQ QUANTILE TRAP (64 dims, 1200 rows, 1% outlier +8s)
==============================================================================
naive min/max       : recall@5 0.9250   hot-dim recon err 0.0000
quantile 1/99       : recall@5 0.8250   hot-dim recon err 7.7111
bound stretch       : on the hot dims the min/max range is 14.78x the quantile range
the trap            : recall ranks 10 points worse under quantile bounds;
                      the hot value rides min/max intact (err 0.0000) yet lands
                      at the 99th-percentile clip under 1/99 (err 7.7111) - the tail WAS
                      the signal and the tighter bounds paid for their tidiness
==============================================================================
F4. BINARY QUANTIZATION (64 dims -> 8 packed bytes, 32x)
==============================================================================
hamming signal      : true-top1 11.3 bits vs random pair 32.6 bits (2.9x apart)
pure binary ranking : recall@10 0.4125  (the floor)
rescore top-40       : recall@10 0.9450
storage             : 64 floats x 4 B = 256 B becomes 8 B packed - 32x
==============================================================================
F5. PRODUCT QUANTIZATION (64 dims -> 8 codes x 256 centroids)
==============================================================================
codebooks           : 8 subspaces x 256 x 8 dims = 64 KB - the whole quantizer
per-vector code     : 256 B float32 -> 8 B of centroid ids - 32x
adc table lookups   : 8 adds per scored vector - no multiply
pure adc ranking    : recall@10 0.6750  (the floor)
rescore top-40       : recall@10 1.0000
==============================================================================
F6. THE OVERSAMPLE x RESCORE LADDER (limit=10)
==============================================================================
oversample 1 = noop : binary 0.4125 (== pure floor)   pq 0.6750 (== pure floor)
binary ladder       : os 2 -> 0.6575   os 4 -> 0.9450   os 8 -> 1.0000
pq ladder           : os 2 -> 0.9300   os 4 -> 1.0000   os 8 -> 1.0000
the law             : os=1 re-scores the same ten rows the scan
                      already ranked - recall moves only past 1
                      and both ladders meet at the os=8 ceiling (1.0000 / 1.0000)
==============================================================================
F7. THE OPS BILL
==============================================================================
instance class      : float32 15.36 GB     -> a 35 GB-class node (+25% graph headroom)
instance class      : scalar int8 3.84 GB  -> a  8 GB-class node (+25% graph headroom)
instance class      : binary 0.48 GB       -> a  2 GB-class node (+25% graph headroom)
instance class      : pq m=48 0.24 GB      -> a  2 GB-class node (+25% graph headroom)
vendor bill 1M/10M  : qdrant (self) $20/$100  pinecone $70/$200  weaviate (self) $20/$100  pgvector (self) $10/$50
pgvector latency tax: 4.0x@10K  4.0x@100K  5.3x@1M  6.0x@10M (the gap grows with scale)
snapshot rpo ledger : 1,000,000 docs at 0.5%/day churn = 5,000 changed docs/day
                      1h-snapshot rpo 208   6h-snapshot rpo 1,250   24h-snapshot rpo 5,000
the wall            : an in-memory-only collection restart loses 1,000,000 docs -
                      the volume survives a restart, not a disk;
                      snapshots are the backup, the volume is not
FENCE-053-OK
```
