---
Document ID: 3203
Title: "3203: The Word-Embedding Tradition - Skip-Gram, Negative Sampling, and GloVe"
Phase: 3
Module: 3200
Last Updated: 2026-10-07
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'embeddings', 'similarity', 'training']
---

# 3203: The Word-Embedding Tradition - Skip-Gram, Negative Sampling, and GloVe

## Abstract

This module is named "Embedding Latent Spaces" and has until now taught position (RoPE, [3201](./3201-Rotary-Positional-Embeddings-RoPE.md)) and subwords ([3202](./3202-Tokenizer-Sciences.md)) - and never the word-embedding tradition its own name and its own quiz promise. Thirteen of the module QUIZ's twenty questions lean on that tradition - Q1-6, 8-9, 11-13, 17-18 - and its review map pointed every one of them at [6102: Semantic Similarity Metrics](../../phase6-rag/6100-vector/6102-Semantic-Similarity.md), two phases later: a phase-order inversion where phase-3 questions are answered by a phase-6 lesson. The vocabulary proves the gap is total - "skip-gram" and "negative sampling" appear NOWHERE in the corpus, CBOW lives in no lesson, and Word2Vec and GloVe exist only as survey names in phase 6 - and the module's own [PREREQUISITES](./PREREQUISITES.md) admits it, listing the Word2Vec paper (Mikolov et al.) and the GloVe paper as review material and asking "Describe the training objective for Word2Vec?" as prior knowledge. The boundary is owned honestly: [3201](./3201-Rotary-Positional-Embeddings-RoPE.md) owns positional embeddings, [3202](./3202-Tokenizer-Sciences.md) owns tokenization, [6102](../../phase6-rag/6100-vector/6102-Semantic-Similarity.md) keeps the similarity METRICS that operate on trained vectors, [6104](../../phase6-rag/6100-vector/6104-Embedding-Sciences.md) keeps pooling, Matryoshka, and MTEB, [6105](../../phase6-rag/6100-vector/6105-Contextual-and-Multilingual-Embeddings.md) keeps the contextual and multilingual RAG geometry - and 3203 owns the tradition itself: one-hot's dead geometry, skip-gram with negative sampling trained from scratch, CBOW the mirror objective, GloVe's co-occurrence ratio, and the static limit the contextual turn answered.

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [One-Hot Is Not a Geometry](#one-hot-is-not-a-geometry)
- [Skip-Gram and Negative Sampling](#skip-gram-and-negative-sampling)
- [CBOW, the Mirror Objective](#cbow-the-mirror-objective)
- [GloVe and the Co-Occurrence Ratio](#glove-and-the-co-occurrence-ratio)
- [Static Limits and the Contextual Turn](#static-limits-and-the-contextual-turn)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After this lesson you will be able to:

- Price what one-hot storage costs against a dense embedding table - 10,000 x 10,000 = 100,000,000 stored cells against 10,000 x 300 = 3,000,000 learnable parameters, a 33.3x ratio - and explain why mutual orthogonality (every cosine 0.0000) means one-hot vectors carry no geometry at all
- Train skip-gram with negative sampling from scratch on a fifteen-sentence corpus and read its output honestly: loss 2.7725 to a tail mean of 1.3743, within-animal cosines 0.9977/0.4625/0.4671 against an animal-vs-food mean of 0.1674, with the 0.6308 cat-fish outlier named as first-order co-occurrence
- Implement CBOW, the mirror objective, and show both its efficiency (47 examples per epoch, loss to 0.3461) and its blur (the filler "is" topping a probe's neighbor list at 0.6486, the price of averaging contexts)
- Reproduce GloVe's ice/steam evidence in miniature - the ratio P(k|ice)/P(k|steam) separating solid (inf, favors ice) from gas (0, favors steam) while water and fashion sit neutral at 1.0 - and state why ratios carry meaning that raw counts do not
- Run the analogy arithmetic (king - man + woman lands queen at 0.9944) and prove the static limit: one "bank" vector scores both senses identically (0.7071/0.7071) where a contextual model separates them (0.9945 versus 0.1047)
- Name where every embedding layer starts (random init, cosines -0.8665/0.4425/0.1372 carrying no meaning) and what training writes into it

## One-Hot Is Not a Geometry

The tradition begins with the representation every textbook starts from and immediately abandons. A vocabulary of V words gets one slot each; a word is the vector of zeros with a single 1 at its own index. As storage this is a disaster twice over - the table is V x V cells no matter how few dimensions the words deserve, and the columns beyond the 1 are all permanent zeros:

```python
import math, random

# --- the storage ledger: one-hot table versus a dense embedding matrix ---
VOCAB = 10000          # a realistic tokenizer vocabulary
DENSE_DIM = 300        # the word2vec-era standard width, inside the 100-1000 band
onehot_cells = VOCAB * VOCAB
dense_params = VOCAB * DENSE_DIM
print(f"one-hot table: {VOCAB:,} words x {VOCAB:,} slots = {onehot_cells:,} stored cells")
print(f"dense embedding: {VOCAB:,} rows x {DENSE_DIM} cols = {dense_params:,} parameters")
print(f"ratio: {onehot_cells / dense_params:.1f}x fewer numbers, and every one of them learnable")

# --- geometry: one-hot vectors are mutually orthogonal, dense vectors are not ---
words = ["cat", "dog", "apple", "banana", "car", "truck"]
idx = {w: i for i, w in enumerate(words)}
n = len(words)

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

onehot = {w: [1.0 if i == idx[w] else 0.0 for i in range(n)] for w in words}
pairs = [("cat", "dog"), ("apple", "banana"), ("car", "truck"), ("cat", "car")]
print("one-hot cosines (every pair orthogonal):")
for a, b in pairs:
    print(f"  cos({a}, {b}) = {cosine(onehot[a], onehot[b]):.4f}")

# random dense init: the seeding every embedding layer actually starts from
random.seed(42)
rand_vecs = {w: [random.uniform(-0.5, 0.5) for _ in range(3)] for w in words}
print("random dense init cosines (no meaning yet):")
for a, b in pairs:
    print(f"  cos({a}, {b}) = {cosine(rand_vecs[a], rand_vecs[b]):.4f}")

# trained-style dense vectors: three near-orthogonal prototype axes with light noise
dense = {
    "cat":    [0.95, 0.05, 0.10],
    "dog":    [0.90, 0.10, 0.05],
    "apple":  [0.05, 0.95, 0.10],
    "banana": [0.10, 0.90, 0.05],
    "car":    [0.10, 0.05, 0.95],
    "truck":  [0.05, 0.10, 0.90],
}
print("trained-style dense cosines:")
for a, b in pairs:
    print(f"  cos({a}, {b}) = {cosine(dense[a], dense[b]):.4f}")
```

The ledger: 10,000 words x 10,000 slots = 100,000,000 stored cells, against the dense embedding's 10,000 rows x 300 columns = 3,000,000 parameters - 33.3x fewer numbers, and every one of them learnable. The 300 is the word2vec-era standard width, sitting inside the 100-1000 band the quiz asks about; modern models run 768 to 12,288, but the argument is unchanged. The geometry is the deeper indictment: every pair of one-hot vectors is orthogonal, so cos(cat, dog) = 0.0000 and cos(cat, car) = 0.0000 - the representation cannot even express that the first pair is more related than the second. The dense vectors show what training buys: three near-orthogonal prototype axes give every within-cluster pair cosine 0.9971 while cat-car drops to 0.2104. And the middle block is where every embedding layer in every model actually starts - random uniform init, cosines of -0.8665 and 0.4425 and 0.1372, no meaning yet. Initialization is not knowledge; it is the blank page the training objective writes on. The next two fences are that objective.

## Skip-Gram and Negative Sampling

The word2vec paper (Mikolov et al. 2013a) proposed two ways to train the table. Skip-gram turns every position into a supervised example: the center word predicts each context word inside a window. Full softmax over the vocabulary is too expensive, so the negative-sampling refinement (Mikolov et al. 2013b) replaces it with a discrimination game - for each true (center, context) pair, draw a few random impostors and teach the model to score the real context above them. The fence trains exactly this from scratch: two matrices (center and context), a fifteen-sentence corpus engineered so the three animals share their relation words - the chase is circular (cat chases mouse, dog chases cat, mouse chases dog), water and fish are deliberately shared across animals - while the fruits share is/sweet/fruit:

```python
import math, random

# --- skip-gram with negative sampling, trained from scratch ---
# the chase is circular (cat-mouse-dog), water and fish are shared - every relation
# word co-occurs with every animal; fruits share is/sweet/fruit
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
widx = {w: i for i, w in enumerate(VOCAB)}
V = len(VOCAB)

DIM, WINDOW, EPOCHS, LR, NEG, SEED = 8, 2, 800, 0.03, 3, 6
random.seed(SEED)

center = [[random.uniform(-0.5 / DIM, 0.5 / DIM) for _ in range(DIM)] for _ in range(V)]
ctx = [[random.uniform(-0.5 / DIM, 0.5 / DIM) for _ in range(DIM)] for _ in range(V)]

def draw_negative(target):
    while True:
        i = random.randrange(V)
        if i != target:
            return i

def sigmoid(x):
    x = max(-30.0, min(30.0, x))   # numerical clamp; keeps log() in its domain
    return 1.0 / (1.0 + math.exp(-x))

pairs = []
for s in CORPUS:
    for pos, c in enumerate(s):
        for off in range(-WINDOW, WINDOW + 1):
            o = pos + off
            if off and 0 <= o < len(s):
                pairs.append((widx[c], widx[s[o]]))

losses = []
for epoch in range(EPOCHS):
    lr_t = LR * (1.0 - epoch / EPOCHS)   # linear decay, the paper's own schedule
    random.shuffle(pairs)
    tot = 0.0
    for t, c in pairs:
        for tgt, label in [(c, 1.0)] + [(draw_negative(t), 0.0) for _ in range(NEG)]:
            dot = sum(center[t][k] * ctx[tgt][k] for k in range(DIM))
            p = sigmoid(dot)
            g = (p - label) * lr_t
            tot += -(math.log(p) if label > 0.5 else math.log(1.0 - p))
            for k in range(DIM):
                center[t][k] -= g * ctx[tgt][k]
                ctx[tgt][k] -= g * center[t][k]
    losses.append(tot / len(pairs))
tail = sum(losses[-40:]) / 40   # the final-epoch loss is one noisy sample; report the mean
print(f"vocab {V} words, {len(pairs)} center-context pairs/epoch, dim {DIM}, {EPOCHS} epochs")
print(f"loss epoch 0: {losses[0]:.4f} -> mean of final 40 epochs: {tail:.4f}")

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

animals = ["cat", "dog", "mouse"]
foods = ["water", "fish", "cheese", "apple", "banana", "fruit", "sweet", "is"]
print("within-animal cosines (words sharing relation contexts):")
for i, a in enumerate(animals):
    for b in animals[i + 1:]:
        print(f"  cos({a}, {b}) = {cosine(center[widx[a]], center[widx[b]]):.4f}")
within = [cosine(center[widx[a]], center[widx[b]]) for i, a in enumerate(animals) for b in animals[i + 1:]]
cross = [(cosine(center[widx[a]], center[widx[f]]), a, f) for a in animals for f in foods]
print(f"animal-vs-food mean: {sum(s for s, _, _ in cross) / len(cross):.4f}"
      f"  (highest single pair: {max(cross)[1]}-{max(cross)[2]} {max(cross)[0]:.4f}, directly co-occurring)")
print("fruit cosines (words sharing is/sweet/fruit):")
for pair in [("apple", "banana"), ("apple", "fruit")]:
    print(f"  cos({pair[0]}, {pair[1]}) = {cosine(center[widx[pair[0]]], center[widx[pair[1]]]):.4f}")
fcross = [cosine(center[widx[a]], center[widx[b]]) for a in ["apple", "banana"] for b in animals]
print(f"fruit-vs-animal mean: {sum(fcross) / len(fcross):.4f}")
```

Read the ledger honestly. The loss falls from 2.7725 (ln 16, exactly the random-init expectation for one positive against three uniform negatives over a 16-word vocabulary) to a mean of 1.3743 over the final 40 epochs - the tail mean, not the final epoch, because one epoch's loss is a single noisy sample over 98 shuffled pairs. The geometry is the thesis: cos(cat, dog) = 0.9977, cos(cat, mouse) = 0.4625, cos(dog, mouse) = 0.4671, against an animal-vs-food mean of 0.1674. The animals never needed to co-occur with each other to land together - they earned their cluster by sharing CONTEXTS, which is second-order similarity, the mechanism the whole tradition runs on. The fence also shows its own limit: the single highest animal-food pair is cat-fish at 0.6308, and cat and fish directly co-occur ("cat eats fish") - first-order co-occurrence similarity is trained in directly and never fully separates. A fifteen-sentence corpus buys the cluster shape, not the clean table; the clean tables in the 2013 paper are bought with billions of tokens. That is the honest scale statement of the entire tradition, made visible in miniature.

## CBOW, the Mirror Objective

CBOW reverses the arrow: the averaged context window predicts the center word. The paper's own summary of the trade: CBOW is several times faster to train (one example per position instead of one per center-context pair - this corpus yields 47 CBOW examples against skip-gram's 98 pairs per epoch) and smooths over rare words, while skip-gram is slower but sharper, especially on small corpora:

```python
import math, random

# --- CBOW: the mirror objective. Average the context, predict the target word ---
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
widx = {w: i for i, w in enumerate(VOCAB)}
V = len(VOCAB)

DIM, WINDOW, EPOCHS, LR, NEG, SEED = 8, 2, 500, 0.05, 3, 42
random.seed(SEED)

emb = [[random.uniform(-0.5 / DIM, 0.5 / DIM) for _ in range(DIM)] for _ in range(V)]
out = [[random.uniform(-0.5 / DIM, 0.5 / DIM) for _ in range(DIM)] for _ in range(V)]

def draw_negative(target):
    while True:
        i = random.randrange(V)
        if i != target:
            return i

def sigmoid(x):
    x = max(-30.0, min(30.0, x))   # numerical clamp; keeps log() in its domain
    return 1.0 / (1.0 + math.exp(-x))

examples = []   # (target id, [context ids])
for s in CORPUS:
    for pos, t in enumerate(s):
        ctx_ids = [widx[s[pos + off]] for off in range(-WINDOW, WINDOW + 1)
                   if off and 0 <= pos + off < len(s)]
        examples.append((widx[t], ctx_ids))

loss0 = loss1 = 0.0
for epoch in range(EPOCHS):
    lr_t = LR * (1.0 - epoch / EPOCHS)   # linear decay, the paper's own schedule
    random.shuffle(examples)
    tot = 0.0
    for t, ctx_ids in examples:
        h = [sum(emb[c][k] for c in ctx_ids) / len(ctx_ids) for k in range(DIM)]
        for tgt, label in [(t, 1.0)] + [(draw_negative(t), 0.0) for _ in range(NEG)]:
            dot = sum(h[k] * out[tgt][k] for k in range(DIM))
            p = sigmoid(dot)
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
print(f"CBOW: {len(examples)} (context, target) examples/epoch, loss {loss0:.4f} -> {loss1:.4f}")

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

for probe in ["cat", "mouse", "fruit"]:
    sims = sorted(((cosine(emb[widx[probe]], emb[widx[w]]), w) for w in VOCAB if w != probe), reverse=True)
    print(f"  nearest '{probe}': " + ", ".join(f"{w} {s:.4f}" for s, w in sims[:3]))

# the direction ledger: CBOW predicts the TARGET from the context window
ctx_words = ["dog", "drinks"]
ctx_ids = [widx[w] for w in ctx_words]
h = [sum(emb[c][k] for c in ctx_ids) / len(ctx_ids) for k in range(DIM)]
allowed = [i for i in range(V) if i not in ctx_ids]     # a word inside the window is not a candidate
scores = sorted(((sum(h[k] * out[i][k] for k in range(DIM)), VOCAB[i]) for i in allowed), reverse=True)
print("  given context [dog, drinks], CBOW ranks targets: "
      + ", ".join(f"{w} {s:.4f}" for s, w in scores[:3]) + "  (true: water)")
```

The mirror works: loss 2.7728 to 0.3461, a tighter fit than skip-gram's - averaging k context vectors into one hidden state is a denoiser. The direction ledger shows what the objective optimizes for: given the context [dog, drinks], CBOW ranks every candidate target and water wins at 3.6492 with the next scorer at -3.8219 (words already inside the window are excluded from their own prediction). But look at the neighbor lists and see the blur: probe "mouse" and the filler word "is" tops the list at 0.6486, above its own animals dog 0.5660 and cat 0.5625. Averaging contexts smooths the signal - CBOW's vectors are blurrier exactly because each update is spread across the whole window. Same corpus, same hyperparameters, two objectives: skip-gram bought the sharper cluster (its mouse sat at 0.4625/0.4671 from its own animals), CBOW bought speed and a tighter loss. That trade is why production codebases trained word vectors with skip-gram on small data and reached for CBOW when corpus, not quality, was the constraint.

## GloVe and the Co-Occurrence Ratio

GloVe (Pennington, Socher, Manning 2014) reached the same geometry from the opposite direction: no per-pair training loop at all, just a global co-occurrence count matrix X and a factorization of its logarithm. The paper's central exhibit is not the counts but their RATIOS. Freeze two probe words - the paper used ice and steam - and for each context word k form P(k|ice)/P(k|steam). The fence rebuilds that table from an eight-sentence corpus in the paper's shape:

```python
from collections import defaultdict

# --- GloVe's core evidence: ratios of co-occurrence probabilities carry the meaning ---
# engineered mini-corpus in the shape of the paper's ice/steam table
CORPUS = [
    "ice cold solid water".split(),
    "ice solid frozen water".split(),
    "ice cold water solid".split(),
    "steam hot gas water".split(),
    "steam gas boiling water".split(),
    "steam hot water gas".split(),
    "fashion week ice sculpture".split(),
    "fashion week steam iron".split(),
]
PROBES = ["ice", "steam"]
CONTEXTS = ["solid", "gas", "water", "fashion"]
WINDOW = 3

co = defaultdict(int)   # (probe, context) -> count
for s in CORPUS:
    for i, w in enumerate(s):
        if w in PROBES:
            for off in range(-WINDOW, WINDOW + 1):
                j = i + off
                if off and 0 <= j < len(s) and s[j] in CONTEXTS:
                    co[(w, s[j])] += 1

print(f"co-occurrence counts in a {len(CORPUS)}-sentence corpus (window {WINDOW}):")
for p in PROBES:
    print(f"  {p}: " + ", ".join(f"{k}={co[(p, k)]}" for k in CONTEXTS))

totals = {p: sum(co[(p, k)] for k in CONTEXTS) for p in PROBES}
print("P(k|probe) and the GloVe ratio P(k|ice)/P(k|steam):")
for k in CONTEXTS:
    pik = co[("ice", k)] / totals["ice"]
    pks = co[("steam", k)] / totals["steam"]
    ratio = pik / pks if pks else float("inf")
    verdict = "favors ice" if ratio > 1.2 else ("favors steam" if ratio < 0.83 else "neutral")
    print(f"  k={k:8s} P(k|ice)={pik:.4f}  P(k|steam)={pks:.4f}  ratio={ratio:.4f}  -> {verdict}")
```

The pattern is the paper's, exactly: k=solid has ratio inf - it appears with ice and never with steam, it favors ice; k=gas is the mirror at 0.0000, favoring steam; k=water co-occurs with both equally and lands neutral at 1.0000; k=fashion is equally irrelevant to both, also 1.0000. Raw counts could not draw these lines - ice and steam have nearly identical total counts, and water appears with both. The ratio isolates what DISCRIMINATES the probes from what they share. GloVe's loss function is precisely a weighted least-squares fit of log(X) that bakes this ratio logic into every pair, and the analytic argument (the paper's section 3) shows any embedding linear enough to support analogy arithmetic makes similarities expressible as ratio differences - the two traditions meet at the same geometry because they are both approximating the same co-occurrence statistics.

## Static Limits and the Contextual Turn

Two claims made the tradition famous, and both need exact reading. First, compositionality as arithmetic: if relations are consistent directions in the space, then vector subtraction isolates them. The fence builds a tiny gender x royalty factorization with noise and runs the classic query:

```python
import math

# --- part A: the analogy, as arithmetic. gender x royalty factorization ---
GENDER = {"man": 1.0, "woman": -1.0, "king": 1.0, "queen": -1.0}
ROYAL = {"man": 0.0, "woman": 0.0, "king": 1.0, "queen": 1.0}
NOISE = {"man": [0.05, -0.03], "woman": [-0.04, 0.06], "king": [0.03, 0.04], "queen": [-0.05, -0.02]}

def vec(w):
    return [GENDER[w], ROYAL[w], NOISE[w][0], NOISE[w][1]]

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

target = [vec("king")[i] - vec("man")[i] + vec("woman")[i] for i in range(4)]
print(f"king - man + woman = [{', '.join(f'{x:.2f}' for x in target)}]")
ranked = sorted(((cosine(target, vec(w)), w) for w in GENDER), reverse=True)
print("cosine ranking of the analogy target:")
for s, w in ranked:
    print(f"  {w:6s} {s:.4f}")
print(f"winner: {ranked[0][1]}")

# --- part B: the static limit. one 'bank' vector cannot tell its two senses apart ---
STATIC_BANK = [1.0, 1.0]
ANCHOR = {"river": [1.0, 0.0], "money": [0.0, 1.0]}   # sense anchors

def cos2(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

print("static 'bank' [1.0, 1.0] scores both senses identically:")
print(f"  cos(bank, river-anchor) = {cos2(STATIC_BANK, ANCHOR['river']):.4f}")
print(f"  cos(bank, money-anchor) = {cos2(STATIC_BANK, ANCHOR['money']):.4f}")

CONTEXTUAL = {
    ("bank", "river"): [0.95, 0.10],
    ("bank", "money"): [0.10, 0.95],
}
print("a contextual model emits one vector per USE, not per type:")
print(f"  cos(bank@river, river-anchor) = {cos2(CONTEXTUAL[('bank', 'river')], ANCHOR['river']):.4f}")
print(f"  cos(bank@money, money-anchor) = {cos2(CONTEXTUAL[('bank', 'money')], ANCHOR['money']):.4f}")
print(f"  cos(bank@river, money-anchor) = {cos2(CONTEXTUAL[('bank', 'river')], ANCHOR['money']):.4f}  (sense separation)")
```

king - man + woman = [-1.00, 1.00, -0.06, 0.13] lands queen at cosine 0.9944, above woman herself at 0.7088 - the analogy table of Mikolov et al. (2013b) in miniature, and Q13's answer: word embeddings capture semantic relationships, not data leakage or luck. Second, the limit that ended the static era. Every vector so far is a TYPE vector - one "bank", frozen, identical in every sentence. The fence scores a static bank against two sense anchors and gets 0.7071 against the river anchor and 0.7071 against the money anchor: a single type vector is geometrically FORCED to average its senses, identical for both. A contextual model emits one vector per USE - bank@river lands 0.9945 on its anchor and only 0.1047 on the other's. That is the contextual turn (ELMo, then BERT): same vocabulary, per-use vectors. The tradition's vectors did not become wrong; they became a documented special case - and they still own the retrieval geometry that [6102](../../phase6-rag/6100-vector/6102-Semantic-Similarity.md) measures with cosine similarity, that [6104](../../phase6-rag/6100-vector/6104-Embedding-Sciences.md) pools and matryoshka-truncates, and that [6105](../../phase6-rag/6100-vector/6105-Contextual-and-Multilingual-Embeddings.md) extends to contextual and multilingual RAG.

## Summary

- One-hot is storage without geometry: 100,000,000 cells against 3,000,000 learnable parameters (33.3x fewer), every pair orthogonal at cosine 0.0000; random init is where every embedding layer starts, carrying no meaning (-0.8665/0.4425/0.1372).
- Skip-gram with negative sampling trains a 16-word corpus from loss 2.7725 to a 1.3743 tail mean; the animals cluster through shared contexts (0.9977/0.4625/0.4671 within against 0.1674 cross mean) while the directly co-occurring cat-fish pair stays at 0.6308 - second-order similarity is the mechanism, first-order similarity is the residue.
- CBOW mirrors the arrow and averages the context: 47 examples per epoch, loss to 0.3461, water wins the [dog, drinks] direction test at 3.6492 - and the blur is visible ("is" at 0.6486 over mouse's own animals).
- GloVe's ratio table is the tradition's cleanest evidence: solid at inf favors ice, gas at 0.0000 favors steam, water and fashion neutral at 1.0000 - ratios discriminate where counts cannot.
- The analogy is arithmetic (queen at 0.9944) and the static limit is geometric law (bank 0.7071/0.7071, contextual 0.9945 versus 0.1047) - the contextual turn kept the vocabulary and replaced type vectors with per-use vectors.
- Thirteen of this module's twenty quiz questions - Q1-6, 8-9, 11-13, 17-18 - are questions about these five fences.

## References

### Related Minder Academy Documents

- [3201: Rotary Positional Embeddings (RoPE)](./3201-Rotary-Positional-Embeddings-RoPE.md) - this module's positional-embedding surface; the token embeddings this lesson trains are the vectors RoPE rotates.
- [3202: Tokenizer Sciences](./3202-Tokenizer-Sciences.md) - subword units and fastText's subword improvement; the vocabulary the tradition's tables index.
- [6102: Semantic Similarity Metrics](../../phase6-rag/6100-vector/6102-Semantic-Similarity.md) - the similarity METRICS (cosine and friends) applied to trained vectors; this lesson owns how the vectors got their geometry.
- [6104: Embedding Sciences](../../phase6-rag/6100-vector/6104-Embedding-Sciences.md) - pooling, Matryoshka, and MTEB on top of trained embeddings.
- [6105: Contextual and Multilingual Embeddings](../../phase6-rag/6100-vector/6105-Contextual-and-Multilingual-Embeddings.md) - the contextual turn continued into RAG geometry.
- [PREREQUISITES](./PREREQUISITES.md) - the module's own review list (Word2Vec paper, GloVe paper); this lesson replaces the review requirement with the material itself.

### Primary Sources

- Mikolov, T., Chen, K., Corrado, G., & Dean, J. (2013). *Efficient Estimation of Word Representations in Vector Space.* arXiv:1301.3781 - CBOW and skip-gram, the training-objective question this module's quiz asks and this lesson answers.
- Mikolov, T., Sutskever, I., Chen, K., Corrado, G. S., & Dean, J. (2013). *Distributed Representations of Words and Phrases and their Compositionality.* arXiv:1310.4546 - negative sampling, the subsampling of frequent words, and the king-queen analogy table.
- Pennington, J., Socher, R., & Manning, C. D. (2014). *GloVe: Global Vectors for Word Representation.* EMNLP 2014 (ACL Anthology D14-1162) - the co-occurrence ratio argument (ice/steam/fashion table) and the log-bilinear factorization; no arXiv version exists - cite the anthology entry.
- Bojanowski, P., Grave, E., Joulin, A., & Mikolov, T. (2017). *Enriching Word Vectors with Subword Information.* TACL. arXiv:1607.04606 - fastText's subword n-grams, the improvement Q7 attributes to [3202](./3202-Tokenizer-Sciences.md)'s surface.
- Peters, M. E., Neumann, M., Iyyer, M., Gardner, M., Clark, C., Lee, K., & Zettlemoyer, L. (2018). *Deep Contextualized Word Representations.* NAACL 2018. arXiv:1802.05365 - ELMo and the per-use vectors this lesson's static-limit fence dramatizes.

## Next Steps

- **Next Module:** continue with [assessment/QUIZ.md](assessment/QUIZ.md) - Q1-6, 8-9, 11-13, 17-18 are the questions this lesson answers; the 33.3x ledger, the 0.9977 cluster, the 3.6492 direction win, the inf/0.0000 ratio pair, and the 0.7071-versus-0.1047 sense split are the mechanics behind them.
- **Continue with:** [6102: Semantic Similarity Metrics](../../phase6-rag/6100-vector/6102-Semantic-Similarity.md) for the measurement layer that operates on these vectors, or [6104: Embedding Sciences](../../phase6-rag/6100-vector/6104-Embedding-Sciences.md) for what modern retrieval stacks build on top of them.
- **Assessment:** add a fourth relation to the F5 factorization - tense (walked/walk, saw/see) - and predict the analogy target before running; then re-run the skip-gram fence with NEG=8 instead of 3 and state what the stronger negative pressure does to the cat-fish first-order residue.

**Estimated Time:** 3 hours
