---
Document ID: CHEAT-SHEET-039
Title: "CHEAT-SHEET-039: Word Embeddings - the Tradition That Turned Co-occurrence into Coordinates"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'embeddings', 'similarity', 'transformers']
---

# CHEAT-SHEET-039: Word Embeddings - the Tradition That Turned Co-occurrence into Coordinates

**Quick Reference for:** the storage ledger that killed the one-hot table (33.3x fewer numbers, every one learnable), skip-gram with negative sampling trained from scratch on a sixteen-word corpus (loss 2.7725 to 1.3743, cat-dog at 0.9977 against an animal-vs-food mean of 0.1674), CBOW the mirror objective whose averaging buys deeper convergence at the price of blur, GloVe's co-occurrence ratio table where meaning survives frequency cancellation, and the analogy arithmetic that worked until the first polysemous word exposed the static limit the contextual turn answered.

Deep dive: module 3203. This is the layer beneath every embedding the curriculum uses later - CHEAT-SHEET-036 stores vectors in Qdrant and module 6104 grades them, but this sheet is where the vectors come from: words become coordinates because a window slid over a corpus and an objective pulled co-occurring pairs together.

## The Storage Ledger: the Table That Held No Meaning

One-hot encoding stores meaning as position in a `V x V` identity table. For a 10,000-word vocabulary that is 100,000,000 stored cells holding exactly one 1 per row - and the geometry is dead: every one-hot pair is orthogonal, cosine 0.0000, *cat* is exactly as far from *dog* as from *car*. A dense embedding matrix spends 10,000 x 300 = 3,000,000 learnable numbers, 33.3x fewer, and its geometry is the product:

| Geometry | Where meaning lives | cos(cat, dog) | Storage |
|----------|--------------------|--------------:|--------:|
| One-hot table | nowhere - all pairs orthogonal | 0.0000 | 100,000,000 cells, none learnable |
| Random dense init | nowhere yet - cosines are seed noise | -0.8665 | 3,000,000 params, all learnable |
| Trained dense | the coordinates themselves | 0.9971 | 3,000,000 params, all learnable |

The random-init row is the honest baseline: cosine -0.8665 between *cat* and *dog* is not wrong, it is untrained. Geometry only counts after an objective moves the coordinates.

## Skip-Gram with Negative Sampling: Coordinates Learned From Window Pairs

The skip-gram objective inverts the hard problem: predicting a word from its neighbors is easier than learning the neighbors, so the model trains on `(center, context)` pairs from a sliding window and lets the weights become the dictionary. Negative sampling (NEG draws) replaces the full-softmax denominator over the whole vocabulary with a handful of pushed-apart random words:

```text
SGNS objective: J = -log s(u_c . v_t) - SUM_i log s(-u_ni . v_t)    pull the true pair up, push NEG draws down
GloVe reading rule: P(k|w1) / P(k|w2) > 1 favors w1, < 1 favors w2, ~= 1 means k is neutral ground
analogy arithmetic: e_king - e_man + e_woman ~= e_queen, graded by cosine over the candidate set
```

On the sixteen-word corpus with window 2, dim 8, seed 6, linear LR decay from 0.03 over 800 epochs and 3 negatives per true pair, the walk is fully reproducible from scratch in pure Python:

| Quantity | Value | What it says |
|----------|------:|--------------|
| (center, context) pairs per epoch | 98 | the whole corpus at window 2 - two passes of training data, not 10,000 rows |
| Loss, epoch 0 | 2.7725 | ln 16 exactly - an untrained model scores every word uniformly |
| Loss, tail mean of final 40 epochs | 1.3743 | halved from chance; the LR decay lets the tail settle instead of bouncing |
| cos(cat, dog) | 0.9977 | same animal cluster - pulled together by chasing and sleeping in company |
| cos(cat, mouse), cos(dog, mouse) | 0.4625 / 0.4671 | same cluster, weaker tie - they co-occur only through the chase verbs |
| Animal-vs-food mean cosine | 0.1674 | the two clusters separate, on average |
| Highest single cross pair | cat-fish 0.6308 | first-order co-occurrence ("cat eats fish") outranks the category boundary |

The cat-fish outlier is not noise to fix: it is real signal. The embedding carries both second-order category structure and first-order co-occurrence, and a 6308-level single pair inside an otherwise 0.1674-mean split is exactly what "the vector encodes the corpus" looks like.

## CBOW: the Mirror Objective and Its Blur

CBOW flips the arrows: average the context embeddings, predict the center word. The mirror halves the training data - 47 `(context, target)` examples per epoch against skip-gram's 98, because each window position yields one example instead of one per offset - and converges deeper: loss 2.7728 down to 0.3461 at 500 epochs against skip-gram's 1.3743 tail.

The price is blur. Nearest neighbors of *mouse* in the CBOW space: `is` at 0.6486 - a function word - above *dog* at 0.5660 and *cat* at 0.5625. Averaging smears the context into one vector, so words that sit in similar windows pick up similar coordinates and function words ride along. The direction test still lands: given `[dog, drinks]` as context, the output layer scores *water* at 3.6492 while the runner-up sits at -3.8219 - a 7.5-point margin across the vocab.

| Quantity | Skip-gram (SGNS) | CBOW |
|----------|-----------------:|-----------------:|
| Examples per epoch (window 2, 16-word corpus) | 98 | 47 |
| Loss trajectory | 2.7725 -> 1.3743 tail | 2.7728 -> 0.3461 final |
| Nearest-neighbor sharpness | cluster-clean (0.9977 within animal) | blurred - `is` 0.6486 tops the list for *mouse* |
| Best for | rare words, per-word structure | frequent words, smooth averaging, speed |

## GloVe: the Ratio Is the Meaning

GloVe starts from a co-occurrence count matrix instead of a sliding-window sampler, and its core evidence is that the *ratio* of co-occurrence probabilities carries the meaning while the raw probabilities drown in word frequency. On an eight-sentence ice/steam corpus with window 3:

| Context k | P(k\|ice) | P(k\|steam) | ratio P(k\|ice)/P(k\|steam) | Verdict |
|-----------|----------:|------------:|----------------------------:|---------|
| solid | 0.4286 | 0.0000 | inf | favors ice |
| gas | 0.0000 | 0.4286 | 0.0000 | favors steam |
| water | 0.4286 | 0.4286 | 1.0000 | neutral |
| fashion | 0.1429 | 0.1429 | 1.0000 | neutral |

The reading rule: ratio > 1.2 favors ice, ratio < 0.83 favors steam, near 1.0000 is neutral ground. The two neutrals are the point - *water* relates to both probes equally and *fashion* to neither, and the ratio detects both situations as the same "no information" signature while the raw probabilities never could. This is why GloVe's loss is fit to log-cooccurrence ratios: the frequency nuisance cancels in the division.

## Analogy Arithmetic and the Static Limit

The famous result: direction arithmetic on the dense space lands on the right answer. `king - man + woman` ranks *queen* first at cosine 0.9944 with *woman* herself second at 0.7088 - the gender+royalty structure is really linear in the coordinates.

Then the limit. A static *bank* vector must average its river and money senses - cosine 0.7071 to a river anchor and 0.7071 to a money anchor, forced equidistance no matter how the corpus leans. A contextual model separates the same word to 0.9945 at the river usage against 0.1047 cross-sense - the two uses of *bank* are nearly orthogonal, as they should be. That 0.7071/0.7071 versus 0.9945/0.1047 split is the whole argument for the contextual turn: static embeddings gave words coordinates, contextual models give *uses* coordinates.

| Representation | bank@river-anchor | bank@money-anchor | Self-split |
|----------------|------------------:|------------------:|-----------:|
| Static bank vector | 0.7071 | 0.7071 | 0.0000 - senses fused by construction |
| Contextual bank@river | 0.9945 | 0.1047 | 0.8898 - senses separated |

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Trained model, all cosines near 0 | negatives drawn include the true context, or LR decayed to nothing before training started | exclude the target in `_draw_negative`, verify loss leaves ln(V) in epoch 1 |
| One pair suspiciously high inside a clean cluster | first-order co-occurrence ("cat eats fish" at 0.6308) outranking category structure | not a bug - it is corpus signal; judge clusters by means, not single pairs |
| CBOW nearest list headed by `the`/`is` | the mirror objective averages context; function words share every window | use skip-gram when per-word sharpness matters; stopword-filter before probing |
| GloVe ratio row undefined (division by zero) | probe word with zero co-occurrence total inside the window | widen the window or extend the corpus before trusting the row |
| Loss bounces at the floor, never settles | fixed LR at the end of training | linear (or cosine) LR decay - the 1.3743 tail needs the schedule, not more epochs |
| Analogy returns the probe word itself | ranking over the full vocabulary including the inputs | exclude the input words from the candidate set before ranking by cosine |

## References

### Related Minder Academy Documents

- [3203: The Word-Embedding Tradition](../../phases/phase3-transformers/3200-embeddings/3203-Word-Embedding-Tradition.md) - the module this sheet maps
- [3201: Rotary Positional Embeddings](../../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md) - what the transformer substituted for learned word identity when position had to be encoded
- [CHEAT-SHEET-036: Vector Memory - the Embedding-Backed Store](./CHEAT-SHEET-036-Vector-Memory-Embedding-Backed-Store.md) - the downstream consumer: these coordinates are what the store indexes and decays
- [6104: Embedding Sciences](../../phases/phase6-rag/6100-vector/6104-Embedding-Sciences.md) - where the tradition meets modern embedding practice and evaluation

### Primary Sources

- [Mikolov et al. 2013, Efficient Estimation of Word Representations (word2vec)](https://arxiv.org/abs/1301.3781) - the skip-gram and CBOW objectives
- [Mikolov et al. 2013, Distributed Representations of Words (negative sampling)](https://arxiv.org/abs/1310.4546) - NEG, the analogy arithmetic, and the linear structure result
- [Pennington, Socher, Manning 2014, GloVe](https://aclanthology.org/D14-1162/) - the co-occurrence ratio evidence and the global objective
- [Bojanowski et al. 2017, fastText](https://arxiv.org/abs/1607.04606) - subword enrichment of the skip-gram tradition
- [Peters et al. 2018, ELMo](https://arxiv.org/abs/1802.05365) - the contextual turn that answered the static limit

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Loss pinned at ln(V) forever | check the pairs builder skips the center position (`off != 0`) - a window that includes the center trains noise |
| All pair cosines collapse near 1.0 | negatives too weak (NEG=1) or LR too high - coordinates anneal into one blob; restore NEG=3+ and decay |
| Cluster means look right but one probe misleads | probe with a mean over the cluster, not a single pair - first-order co-occurrence is allowed to disagree |
| CBOW direction test fails on rare targets | the averaged context drowns rare centers; switch to skip-gram for low-frequency evaluation |
| GloVe verdicts flip between corpora | thresholds (>1.2 / <0.83) are corpus-relative - re-derive the neutral band on your own ratio histogram |
| Static analogy breaks on polysemous probes | `bank`-class words fuse senses into one vector; that is the static limit - move to contextual embeddings |

## Quick-Reference-for

| Target | Why |
|--------|-----|
| [Module 3203: The Word-Embedding Tradition](../../phases/phase3-transformers/3200-embeddings/3203-Word-Embedding-Tradition.md) | the deep dive this sheet maps - the fences behind every number above |
| [Module 3201: Rotary Positional Embeddings](../../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md) | the sibling problem the transformer inherited: position, once one-hot too |
| [CHEAT-SHEET-036: Vector Memory](./CHEAT-SHEET-036-Vector-Memory-Embedding-Backed-Store.md) | the consumer of these coordinates: filtering before similarity, decay re-ranking, the dedup threshold |
| [Module 6104: Embedding Sciences](../../phases/phase6-rag/6100-vector/6104-Embedding-Sciences.md) | the modern evaluation surface: what a trained embedding must still prove |

The fence reproduces the canonical numbers from the verification box: F1 the storage ledger and three geometries (33.3x, one-hot 0.0000, random seed noise, trained 0.9971); F2 the skip-gram walk (2.7725 -> 1.3743, within-animal 0.9977/0.4625/0.4671, animal-vs-food mean 0.1674, the cat-fish outlier 0.6308); F3 the CBOW mirror (47 examples, 0.3461, the `is`-topped blur, the 7.5-point direction margin); F4 the GloVe ratio table (inf / 0.0000 / 1.0000 / 1.0000); F5 the analogy arithmetic (queen 0.9944) and the static-limit split (0.7071/0.7071 versus 0.9945/0.1047).

```python
"""CHEAT-SHEET-039 fence: the word-embedding tradition on one deterministic run.

Reproduces module 3203's canonical numbers from scratch with stdlib only:
the one-hot storage ledger and its dead geometry, skip-gram with negative
sampling trained from scratch on the fifteen-sentence corpus, CBOW the mirror
objective, GloVe's co-occurrence ratio table, and the analogy arithmetic with
the static limit that the contextual turn answered.
"""
import math
import random
from collections import defaultdict


def f1_storage_geometry():
    """One-hot table versus a dense embedding matrix, and three geometries."""
    print("F1  storage ledger and three geometries")
    VOCAB, DENSE_DIM = 10000, 300
    onehot_cells = VOCAB * VOCAB
    dense_params = VOCAB * DENSE_DIM
    print(f"    one-hot: {VOCAB:,} x {VOCAB:,} = {onehot_cells:,} stored cells")
    print(f"    dense  : {VOCAB:,} x {DENSE_DIM} = {dense_params:,} learnable parameters")
    print(f"    ratio  : {onehot_cells / dense_params:.1f}x fewer numbers, every one learnable")

    words = ["cat", "dog", "apple", "banana", "car", "truck"]
    pairs = [("cat", "dog"), ("apple", "banana"), ("car", "truck"), ("cat", "car")]

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    idx = {w: i for i, w in enumerate(words)}
    n = len(words)
    onehot = {w: [1.0 if i == idx[w] else 0.0 for i in range(n)] for w in words}
    print("    one-hot cosines: " + ", ".join(
        f"{a}-{b} {cosine(onehot[a], onehot[b]):.4f}" for a, b in pairs))
    random.seed(42)
    rand_vecs = {w: [random.uniform(-0.5, 0.5) for _ in range(3)] for w in words}
    print("    random-init cosines (no meaning yet): " + ", ".join(
        f"{a}-{b} {cosine(rand_vecs[a], rand_vecs[b]):.4f}" for a, b in pairs))
    dense = {
        "cat": [0.95, 0.05, 0.10], "dog": [0.90, 0.10, 0.05],
        "apple": [0.05, 0.95, 0.10], "banana": [0.10, 0.90, 0.05],
        "car": [0.10, 0.05, 0.95], "truck": [0.05, 0.10, 0.90],
    }
    print("    trained-style cosines: " + ", ".join(
        f"{a}-{b} {cosine(dense[a], dense[b]):.4f}" for a, b in pairs))


CORPUS = [
    "cat chases mouse".split(),
    "dog chases cat".split(),
    "mouse chases dog".split(),
    "cat drinks water".split(),
    "dog drinks water".split(),
    "mouse drinks water".split(),
    "cat eats fish".split(),
    "dog eats fish".split(),
    "mouse eats cheese".split(),
    "mouse eats apple".split(),
    "apple is sweet fruit".split(),
    "banana is sweet fruit".split(),
    "cat sleeps soundly".split(),
    "dog sleeps soundly".split(),
    "mouse sleeps soundly".split(),
]
VOCAB = sorted({w for s in CORPUS for w in s})
WIDX = {w: i for i, w in enumerate(VOCAB)}
V = len(VOCAB)


def _sigmoid(x):
    x = max(-30.0, min(30.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def _draw_negative(target):
    while True:
        i = random.randrange(V)
        if i != target:
            return i


def f2_skipgram():
    """Skip-gram with negative sampling, trained from scratch (SEED 6)."""
    DIM, WINDOW, EPOCHS, LR, NEG = 8, 2, 800, 0.03, 3
    random.seed(6)
    center = [[random.uniform(-0.5 / DIM, 0.5 / DIM) for _ in range(DIM)] for _ in range(V)]
    ctx = [[random.uniform(-0.5 / DIM, 0.5 / DIM) for _ in range(DIM)] for _ in range(V)]

    pairs = []
    for s in CORPUS:
        for pos, c in enumerate(s):
            for off in range(-WINDOW, WINDOW + 1):
                o = pos + off
                if off and 0 <= o < len(s):
                    pairs.append((WIDX[c], WIDX[s[o]]))

    losses = []
    for epoch in range(EPOCHS):
        lr_t = LR * (1.0 - epoch / EPOCHS)
        random.shuffle(pairs)
        tot = 0.0
        for t, c in pairs:
            for tgt, label in [(c, 1.0)] + [(_draw_negative(t), 0.0) for _ in range(NEG)]:
                dot = sum(center[t][k] * ctx[tgt][k] for k in range(DIM))
                p = _sigmoid(dot)
                g = (p - label) * lr_t
                tot += -(math.log(p) if label > 0.5 else math.log(1.0 - p))
                for k in range(DIM):
                    center[t][k] -= g * ctx[tgt][k]
                    ctx[tgt][k] -= g * center[t][k]
        losses.append(tot / len(pairs))
    tail = sum(losses[-40:]) / 40

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    print(f"F2  skip-gram + negative sampling: {V} words, {len(pairs)} pairs/epoch, "
          f"dim {DIM}, {EPOCHS} epochs")
    print(f"    loss epoch 0: {losses[0]:.4f} (ln 16) -> tail mean of final 40: {tail:.4f}")
    animals = ["cat", "dog", "mouse"]
    within = []
    for i, a in enumerate(animals):
        for b in animals[i + 1:]:
            s = cosine(center[WIDX[a]], center[WIDX[b]])
            within.append(s)
            print(f"    cos({a}, {b}) = {s:.4f}")
    foods = ["water", "fish", "cheese", "apple", "banana", "fruit", "sweet", "is"]
    cross = [(cosine(center[WIDX[a]], center[WIDX[f]]), a, f) for a in animals for f in foods]
    print(f"    animal-vs-food mean: {sum(s for s, _, _ in cross) / len(cross):.4f}  "
          f"(highest single pair {max(cross)[1]}-{max(cross)[2]} {max(cross)[0]:.4f}, directly co-occurring)")
    return tail


def f3_cbow():
    """CBOW, the mirror objective: average the context, predict the target (SEED 42)."""
    DIM, WINDOW, EPOCHS, LR, NEG = 8, 2, 500, 0.05, 3
    random.seed(42)
    emb = [[random.uniform(-0.5 / DIM, 0.5 / DIM) for _ in range(DIM)] for _ in range(V)]
    out = [[random.uniform(-0.5 / DIM, 0.5 / DIM) for _ in range(DIM)] for _ in range(V)]

    examples = []
    for s in CORPUS:
        for pos, t in enumerate(s):
            ctx_ids = [WIDX[s[pos + off]] for off in range(-WINDOW, WINDOW + 1)
                       if off and 0 <= pos + off < len(s)]
            examples.append((WIDX[t], ctx_ids))

    loss0 = loss1 = 0.0
    for epoch in range(EPOCHS):
        lr_t = LR * (1.0 - epoch / EPOCHS)
        random.shuffle(examples)
        tot = 0.0
        for t, ctx_ids in examples:
            h = [sum(emb[c][k] for c in ctx_ids) / len(ctx_ids) for k in range(DIM)]
            for tgt, label in [(t, 1.0)] + [(_draw_negative(t), 0.0) for _ in range(NEG)]:
                dot = sum(h[k] * out[tgt][k] for k in range(DIM))
                p = _sigmoid(dot)
                g = (p - label) * lr_t
                tot += -(math.log(p) if label > 0.5 else math.log(1.0 - p))
                for k in range(DIM):
                    out[tgt][k] -= g * h[k]
                for c in ctx_ids:
                    for k in range(DIM):
                        emb[c][k] -= g * out[tgt][k] / len(ctx_ids)
        if epoch == 0:
            loss0 = tot / len(examples)
        if epoch == EPOCHS - 1:
            loss1 = tot / len(examples)

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    print(f"F3  CBOW mirror: {len(examples)} (context, target) examples/epoch, "
          f"loss {loss0:.4f} -> {loss1:.4f}")
    probe = "mouse"
    sims = sorted(((cosine(emb[WIDX[probe]], emb[WIDX[w]]), w)
                   for w in VOCAB if w != probe), reverse=True)
    print(f"    nearest '{probe}': " + ", ".join(f"{w} {s:.4f}" for s, w in sims[:3]))
    ctx_ids = [WIDX[w] for w in ["dog", "drinks"]]
    h = [sum(emb[c][k] for c in ctx_ids) / len(ctx_ids) for k in range(DIM)]
    allowed = [i for i in range(V) if i not in ctx_ids]
    scores = sorted(((sum(h[k] * out[i][k] for k in range(DIM)), VOCAB[i])
                     for i in allowed), reverse=True)
    print("    direction test [dog, drinks]: "
          + ", ".join(f"{w} {s:.4f}" for s, w in scores[:2]) + "  (true: water)")


def f4_glove_ratio():
    """GloVe's core evidence: co-occurrence probability ratios carry the meaning."""
    MINI = [
        "ice cold solid water".split(),
        "ice solid frozen water".split(),
        "ice cold water solid".split(),
        "steam hot gas water".split(),
        "steam gas boiling water".split(),
        "steam hot water gas".split(),
        "fashion week ice sculpture".split(),
        "fashion week steam iron".split(),
    ]
    PROBES, CONTEXTS, WINDOW = ["ice", "steam"], ["solid", "gas", "water", "fashion"], 3
    co = defaultdict(int)
    for s in MINI:
        for i, w in enumerate(s):
            if w in PROBES:
                for off in range(-WINDOW, WINDOW + 1):
                    j = i + off
                    if off and 0 <= j < len(s) and s[j] in CONTEXTS:
                        co[(w, s[j])] += 1
    totals = {p: sum(co[(p, k)] for k in CONTEXTS) for p in PROBES}
    print(f"F4  GloVe ratio table, {len(MINI)}-sentence corpus, window {WINDOW}")
    for k in CONTEXTS:
        pik = co[("ice", k)] / totals["ice"]
        pks = co[("steam", k)] / totals["steam"]
        ratio = pik / pks if pks else float("inf")
        verdict = "favors ice" if ratio > 1.2 else ("favors steam" if ratio < 0.83 else "neutral")
        print(f"    k={k:8s} P(k|ice)={pik:.4f}  P(k|steam)={pks:.4f}  "
              f"ratio={ratio:.4f}  -> {verdict}")


def f5_analogy_and_static_limit():
    """The analogy as arithmetic, and the static limit the contextual turn answered."""
    GENDER = {"man": 1.0, "woman": -1.0, "king": 1.0, "queen": -1.0}
    ROYAL = {"man": 0.0, "woman": 0.0, "king": 1.0, "queen": 1.0}
    NOISE = {"man": [0.05, -0.03], "woman": [-0.04, 0.06],
             "king": [0.03, 0.04], "queen": [-0.05, -0.02]}

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    def vec(w):
        return [GENDER[w], ROYAL[w], NOISE[w][0], NOISE[w][1]]

    print("F5  analogy arithmetic and the static limit")
    target = [vec("king")[i] - vec("man")[i] + vec("woman")[i] for i in range(4)]
    ranked = sorted(((cosine(target, vec(w)), w) for w in GENDER), reverse=True)
    print("    king - man + woman ranks: "
          + ", ".join(f"{w} {s:.4f}" for s, w in ranked) + f"  (winner {ranked[0][1]})")
    STATIC_BANK = [1.0, 1.0]
    ANCHOR = {"river": [1.0, 0.0], "money": [0.0, 1.0]}
    print(f"    static bank: cos(river-anchor) {cosine(STATIC_BANK, ANCHOR['river']):.4f}  "
          f"cos(money-anchor) {cosine(STATIC_BANK, ANCHOR['money']):.4f}  (forced average)")
    CONTEXTUAL = {("bank", "river"): [0.95, 0.10], ("bank", "money"): [0.10, 0.95]}
    print(f"    contextual  : bank@river {cosine(CONTEXTUAL[('bank', 'river')], ANCHOR['river']):.4f}  "
          f"bank@money {cosine(CONTEXTUAL[('bank', 'money')], ANCHOR['money']):.4f}  "
          f"cross {cosine(CONTEXTUAL[('bank', 'river')], ANCHOR['money']):.4f}")


def main():
    f1_storage_geometry()
    f2_skipgram()
    f3_cbow()
    f4_glove_ratio()
    f5_analogy_and_static_limit()


if __name__ == "__main__":
    main()
```

```text
F1  storage ledger and three geometries
    one-hot: 10,000 x 10,000 = 100,000,000 stored cells
    dense  : 10,000 x 300 = 3,000,000 learnable parameters
    ratio  : 33.3x fewer numbers, every one learnable
    one-hot cosines: cat-dog 0.0000, apple-banana 0.0000, car-truck 0.0000, cat-car 0.0000
    random-init cosines (no meaning yet): cat-dog -0.8665, apple-banana -0.2178, car-truck 0.4425, cat-car 0.1372
    trained-style cosines: cat-dog 0.9971, apple-banana 0.9971, car-truck 0.9971, cat-car 0.2104
F2  skip-gram + negative sampling: 16 words, 98 pairs/epoch, dim 8, 800 epochs
    loss epoch 0: 2.7725 (ln 16) -> tail mean of final 40: 1.3743
    cos(cat, dog) = 0.9977
    cos(cat, mouse) = 0.4625
    cos(dog, mouse) = 0.4671
    animal-vs-food mean: 0.1674  (highest single pair cat-fish 0.6308, directly co-occurring)
F3  CBOW mirror: 47 (context, target) examples/epoch, loss 2.7728 -> 0.3461
    nearest 'mouse': is 0.6486, dog 0.5660, cat 0.5625
    direction test [dog, drinks]: water 3.6492, sleeps -3.8219  (true: water)
F4  GloVe ratio table, 8-sentence corpus, window 3
    k=solid    P(k|ice)=0.4286  P(k|steam)=0.0000  ratio=inf  -> favors ice
    k=gas      P(k|ice)=0.0000  P(k|steam)=0.4286  ratio=0.0000  -> favors steam
    k=water    P(k|ice)=0.4286  P(k|steam)=0.4286  ratio=1.0000  -> neutral
    k=fashion  P(k|ice)=0.1429  P(k|steam)=0.1429  ratio=1.0000  -> neutral
F5  analogy arithmetic and the static limit
    king - man + woman ranks: queen 0.9944, woman 0.7088, king 0.0017, man -0.7072  (winner queen)
    static bank: cos(river-anchor) 0.7071  cos(money-anchor) 0.7071  (forced average)
    contextual  : bank@river 0.9945  bank@money 0.9945  cross 0.1047
```
