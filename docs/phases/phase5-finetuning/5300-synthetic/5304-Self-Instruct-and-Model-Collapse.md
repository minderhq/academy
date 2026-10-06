---
Document ID: 5304
Title: "5304: Self-Instruct and Model Collapse - Growing Instruction Data Without Losing the Distribution"
Phase: 5
Module: 5300
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'synthetic-data', 'evaluation']
---

# 5304: Self-Instruct and Model Collapse - Growing Instruction Data Without Losing the Distribution

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Self-Instruct Pipeline: Growing Instructions From Seeds](#the-self-instruct-pipeline-growing-instructions-from-seeds)
- [Model Collapse: The Recursion Tax](#model-collapse-the-recursion-tax)
- [The Ten-Percent Anchor](#the-ten-percent-anchor)
- [Measuring Synthetic Data Downstream](#measuring-synthetic-data-downstream)
- [The Campaign: One 52K Run, Four Bills](#the-campaign-one-52k-run-four-bills)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After reading this lesson, you will be able to:

- Run the self-instruct bootstrap - seed tasks, pool-sampled generation prompts, and a similarity-threshold keep rule - and read its round ledger as a filter-rejection curve
- State the model collapse mechanism from arithmetic: fitting and resampling your own output is an absorbing process whose extinction front is the rare end of the distribution
- Show what the recursion costs at each generation - type coverage halved in four cycles while mass shares barely move, which is why collapse reads as blandness before it reads as brokenness
- Apply the ten-percent anchor - the paper's own control - and measure how much of the decay a fixed real-data reserve flattens per generation
- Evaluate a synthetic pool downstream instead of by inspection: train on gold, on clean synthetic, on recursively degraded synthetic, and on pure degraded synthetic, and read the four accuracies as the scheme every synthetic-data decision needs
- Price one 52K-instruction run four ways - human-written, self-instruct, anchor surcharge, and one ungated collapse's re-collection - and choose by the bill, not by the folklore

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)

## Abstract

[5301](./5301-Knowledge-Distillation.md) trains on a model's outputs but keeps the teacher fixed - the student mimics one frozen model, nothing bootstraps. [5204](../5200-alignment/5204-Preference-Dataset-Creation.md) synthesizes preference pairs but puts a judge and a held-out human calibration between the generator and the dataset. [5101](../5100-peft/5101-LoRA-Logic.md) hands you Alpaca as the canonical instruction dataset without owning the pipeline that built it. What no lesson has owned is the pair of mechanisms the module's own quiz admits are taught nowhere: the self-instruct pipeline that grew 52,445 instructions from 175 seed tasks, and model collapse - the degeneration Shumailov et al. measured when a model's training set is polluted by its own recursively generated data - plus the downstream-task evaluation scheme that tells a good synthetic pool from a poisoned one. This lesson makes all three runnable and prices each one's bill. The bootstrap's keep-rate falls 0.60 to 0.20 across four rounds as the pool densifies - the filter's rejection is the pipeline working, not failing. The recursion walk halves type coverage (1082 to 557) in four ungated cycles while the tails drain 154 to 70, and the ten-percent real-data anchor holds generation-4 coverage at 686 types against 521 without it. Downstream, the same 2000 synthetic examples are worth +0.005 at generation 1 and -0.218 at generation 3, and the campaign closes it: $1,603 to generate what would cost $524,450 to write, a $52,440 anchor that is 33x the generation bill and still 4.4x cheaper than one ungated collapse's $238,608 re-collection.

## The Self-Instruct Pipeline: Growing Instructions From Seeds

Self-Instruct (Wang et al., ACL 2023, arXiv 2212.10560) starts from 175 seed tasks - 25 classification, 150 non-classification - and grows them by prompting the model with a template that mixes one seed task with sampled pool tasks, asking for new instructions in the same format. The pipeline's quality lives in its filter: a candidate instruction is kept only if its ROUGE-L similarity with every existing instruction is below 0.7, near-duplicates are dropped before they enter the pool. The final census: 52,445 instructions (11,584 classification, 40,861 non-classification) and 82,439 input-output instances, 35,878 of which have empty inputs. Downstream, a GPT-3 fine-tuned on this pool gains +33% absolute over vanilla GPT-3 on Super-NaturalInstructions, lands roughly on par with InstructGPT_001, and stays about 5% behind models tuned on expert-written data.

The fence below reruns the pipeline's skeleton at teachable scale - 40 seed instructions, four bootstrap rounds of 60 candidates each, and the same keep rule: a candidate survives only if its similarity with every existing instruction is below 0.7. One substitution is owned up front: similarity here is Jaccard overlap over word sets, not ROUGE-L - the cheapest stand-in that keeps the rule's shape, and the fence's ledger is about the rule's dynamics, not the metric's calibration.

```python
import random

SEEDS = [
    "Rewrite this sentence in passive voice",
    "Summarize the paragraph in exactly three words",
    "Classify the review as positive or negative",
    "Translate the idiom into plain English",
    "List three uses for a paperclip",
    "Explain recursion to a ten year old",
    "Convert the date into ISO format",
    "Identify the grammatical error in the sentence",
    "Write a haiku about the ocean",
    "Given two cities compute the driving distance",
    "Extract all proper nouns from the text",
    "Rewrite the email in a formal tone",
    "Invent a name for a coffee shop",
    "Sort these numbers in descending order",
    "Predict the next word in the sequence",
    "Rate the sentiment of the tweet",
    "Paraphrase the abstract for a general audience",
    "Find the largest number in the list",
    "Explain the difference between a virus and a worm",
    "Rewrite the question as a statement",
    "Generate a password suggestion and explain its entropy",
    "Name the capital of the given country",
    "Convert the recipe from metric to imperial units",
    "Identify the logical fallacy in the argument",
    "Write a function that reverses a string",
    "Describe the painting in one sentence",
    "Turn the bullet points into a paragraph",
    "Classify the news headline by section",
    "Check whether the parentheses are balanced",
    "Rewrite the slogan to target teenagers",
    "Sum the even numbers in the list",
    "Explain why the sky is blue",
    "Give two synonyms for the adjective",
    "Draft a reply declining the invitation",
    "Label each sentence as fact or opinion",
    "Compress the paragraph into a headline",
    "Find the missing word in the sentence",
    "Estimate the cost of the grocery list",
    "Rewrite the code with better variable names",
    "State the main claim of the argument",
]
CONSTRAINTS = [
    "for a beginner audience",
    "in exactly five words",
    "without using adjectives",
    "as a numbered list",
    "in a formal tone",
    "with a worked example",
    "for a technical reviewer",
    "in plain English",
]
PREFIXES = [
    "In one paragraph, ",
    "Step by step, ",
    "As a table, ",
    "For a blog post, ",
]
VERB_SWAPS = [
    ("Rewrite", "Rephrase"),
    ("Explain", "Describe"),
    ("List", "Enumerate"),
    ("Summarize", "Condense"),
    ("Classify", "Categorize"),
    ("Convert", "Transform"),
    ("Find", "Locate"),
    ("Identify", "Pinpoint"),
]

rng = random.Random(101)

def toks(s):
    return set(s.lower().split())

def jac(a, b):
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

def mutate(instr):
    s = instr
    if rng.random() < 0.5:
        for a, b in VERB_SWAPS:
            if s.startswith(a):
                s = b + s[len(a):]
                break
    if rng.random() < 0.5:
        s = rng.choice(PREFIXES) + s[0].lower() + s[1:]
    if rng.random() < 0.5:
        s = s + " " + rng.choice(CONSTRAINTS)
    return s

POOL = list(SEEDS)
N_RND, PER_RND, THRESH = 4, 60, 0.7
total_gen = total_keep = total_dup = 0
for rnd in range(1, N_RND + 1):
    kept = dup = 0
    for _ in range(PER_RND):
        src = POOL[0] if rng.random() < 0.15 else rng.choice(POOL)
        cand = mutate(src)
        total_gen += 1
        if max(jac(cand, p) for p in POOL) < THRESH:
            POOL.append(cand)
            kept += 1
            total_keep += 1
        else:
            dup += 1
            total_dup += 1
    print(f"round {rnd}: generated {PER_RND} kept {kept} dup-dropped {dup} pool {len(POOL)}")

pool_toks = set()
for p in POOL:
    pool_toks |= toks(p)
seed_toks = set()
for p in SEEDS:
    seed_toks |= toks(p)
new_toks = pool_toks - seed_toks
print(f"final: pool {len(POOL)} instructions from {len(SEEDS)} seeds, "
      f"kept {total_keep}/{total_gen} ({total_keep/total_gen:.3f}), "
      f"dup-dropped {total_dup}/{total_gen} ({total_dup/total_gen:.3f})")
print(f"vocabulary: {len(seed_toks)} seed tokens -> {len(pool_toks)} pool tokens, "
      f"{len(new_toks)} new ({len(new_toks)/len(pool_toks):.3f} of pool vocabulary)")
```

Read the round ledger as a filter-rejection curve: 36 kept in round 1, then 22, 14, 12 - the pool starts dense with novelty and each kept instruction makes the next candidate more likely to collide with something already in it. By round 4 the filter rejects 48 of 60 candidates, and across the whole run only 84 of 240 survive (keep-rate 0.350, dup-dropped 0.650). The paper's own numbers are this same curve at model scale - 175 seeds in, 52,445 instructions out, with the filter doing the work between. The vocabulary line is the quiet finding: 40 seeds carry 157 distinct tokens, the 124-instruction pool carries only 177, and just 20 pool tokens (0.113) are new - instruction variety grows almost entirely by recombining existing words into new constraints, audiences, and formats, which is exactly why a similarity threshold can police it. The 35,878 empty-input instances in the paper's census are the same story one level down: the generator recombines instruction phrasings far more readily than it invents genuinely new task inputs.

## Model Collapse: The Recursion Tax

Model collapse (Shumailov et al., Nature 631, 755-759, 2024) is the degenerative process that starts when generated data ends up in a model's own training set and each generation trains on the previous generation's output. The paper splits the decay into early collapse - the tails of the original distribution disappear first - and late collapse, where the remaining distribution converges to a small-variance remnant of its former self. The mechanism has three error sources and the paper is explicit about their order: statistical approximation error (finite samples miss rare outcomes) is primary, functional expressivity error (the model class cannot represent what it did not see) compounds it, and functional approximation error (the learning procedure's own imperfections) finishes the job. Their LLM experiment makes the tax concrete: an OPT-125m fine-tuned on real wikitext2 reaches 34 mean perplexity against a 115 zero-shot baseline, and over five generations of training on recursively generated data with none of the original preserved, the models lose 20 to 28 perplexity points; a repetition penalty of 2.0 - the folk fix - makes the measured perplexity worse.

The fence below runs the most charitable version of the loop possible: the "model" is the previous sample's empirical distribution itself - a perfect fit with zero capacity excuse - and each generation draws a fresh sample from that fit. If collapse appears even here, it is not a modeling artifact; it is what fitting your own sample is.

```python
import random
from collections import Counter

# the paper's discrete-distribution experiment: each round fits the EMPIRICAL
# distribution of the previous round's sample and draws the next sample from it
V, N, TAIL_FROM = 2000, 5000, 1501
rng = random.Random(202)

ws = [1.0 / (i + 1) for i in range(V)]
tot = sum(ws)
ws = [w / tot for w in ws]

def sample_zipf(n, r):
    return [r.choices(range(V), weights=ws)[0] for _ in range(n)]

def resample(sample, n, r):
    cnt = Counter(sample)
    return r.choices(list(cnt), weights=list(cnt.values()), k=n)

def metrics(sample, g):
    cnt = Counter(sample)
    st = set(sample)
    tails = sum(1 for w in st if w >= TAIL_FROM)
    singles = sum(1 for w, c in cnt.items() if c == 1)
    print(f"gen {g}: types-present {len(st)} tail-types {tails} singletons {singles}")

s = sample_zipf(N, rng)
metrics(s, 0)
for g in range(1, 5):
    s = resample(s, N, rng)
    metrics(s, g)
```

The walk is the absorbing process the paper proves converges to a point mass: type coverage falls 1082 to 847 to 711 to 622 to 557 - nearly half the distribution's types gone in four ungated cycles - and the decay is fastest at the rare end, exactly as early collapse predicts. The tail's 154 types drain to 70, and the singleton count (the extinction front, types living on one supporting occurrence) falls 548 to 100 as each round kills every rare type whose single draw failed to reproduce. One honest reading the fence forces: the corpus's mass shares barely move while its type coverage halves - the frequent words keep their frequencies, the corpus just says fewer different things. That is why collapse is dangerous in production: the dataset looks normal in aggregates, passes spot checks, and has quietly stopped covering the rare inputs your users actually send. The paper's delta-function limit is where this walk ends if the loop keeps running; four cycles are enough to see the direction and the front.

## The Ten-Percent Anchor

The paper's own control points at the fix: in the regime where ten percent of the original data is preserved in every generation's training set, degradation over ten epochs is minor - the recursion loses its compounding when each round keeps a line to the true source. The anchor is not a cure; it is a floor under the slope. The fence below reruns the same walk twice with the same generator state - once with zero percent preserved, once with ten percent of each round's budget reserved for fresh draws from the true Zipf source - so the only difference between the rows is the anchor.

```python
import random
from collections import Counter

# the same recursion with a fresh-real anchor: each round keeps `preserve`
# of its budget for draws from the true Zipf source
V, N, TAIL_FROM = 2000, 5000, 1501

ws = [1.0 / (i + 1) for i in range(V)]
tot = sum(ws)
ws = [w / tot for w in ws]

def sample_zipf(n, r):
    return [r.choices(range(V), weights=ws)[0] for _ in range(n)]

def resample(sample, n, r):
    cnt = Counter(sample)
    return r.choices(list(cnt), weights=list(cnt.values()), k=n)

def walk(preserve, seed=303):
    r2 = random.Random(seed)
    s = sample_zipf(N, r2)
    rows = []
    for g in range(1, 5):
        n_real = int(N * preserve)
        s = resample(s, N - n_real, r2)
        if n_real:
            s = s + sample_zipf(n_real, r2)
        st = set(s)
        ty = sum(1 for w in st if w >= TAIL_FROM)
        rows.append((g, len(st), ty))
    return rows

for preserve in (0.0, 0.1):
    line = "  ".join(f"g{g} types-{t} tailty-{ty}" for g, t, ty in walk(preserve))
    print(f"preserve {preserve:.0%}: {line}")
```

At generation 4 the ungated walk sits at 521 types with 50 tail types; the anchored walk sits at 686 with 72 - 165 more types and 22 more tail types still alive, from a ten-percent budget line. Both rows still decay (823 to 521, 880 to 686): the anchor flattens the slope, it does not zero it, and the paper's "minor degradation" is this slope, not the absence of one. The production reading: reserving a fixed slice of every generation's budget for real data is the cheapest insurance in the synthetic-data ledger, and it is priced in section 5's campaign - the interesting question is never whether to pay it but whether the team remembers it exists before the third recursive cycle.

## Measuring Synthetic Data Downstream

The module quiz's own evaluation question has a code answer: do not inspect the pool - train on it and measure downstream. The fence builds the smallest honest version: a 3-class intent task where each example is filler words plus (60% of the time) one class-revealing keyword, a ridge classifier trained one-vs-all with per-sample regularization held constant across mixes, and a 400-example gold holdout. Four mixes get the same 600 gold examples except where stated: gold alone; gold plus 2000 generation-1 synthetic (drawn from the same clean generator as gold - more of the same); gold plus 2000 generation-3 synthetic (the recursively degraded pool: 80% of the keywords that survive into it were swapped to a wrong-class word - collapse arriving as label noise); and the generation-3 pool alone. The 2000-vs-600 volume is deliberate - synthetic pools get big, and volume is how label noise beats a clean signal.

```python
import random

CLASSES = {
    "billing": ["refund", "invoice", "charge", "payment", "subscription", "billing"],
    "tech": ["login", "password", "error", "crash", "update", "server"],
    "sales": ["pricing", "demo", "trial", "quote", "discount", "enterprise"],
}
FILLERS = ["please", "the", "about", "our", "with", "for", "my", "and", "is", "to"]
CL = list(CLASSES)
W = {c: CLASSES[c] for c in CL}
P_KW = 0.6      # gold: keyword present 60% of the time
P_FLIP = 0.8    # gen-3: present keyword swapped to a wrong-class word 80% of the time

def make_example(label, r, gen):
    kw = r.choice(W[label])
    fills = [r.choice(FILLERS) for _ in range(6)]
    has_kw = r.random() < P_KW
    if gen >= 3 and has_kw and r.random() < P_FLIP:
        other = r.choice([c for c in CL if c != label])
        kw = r.choice(W[other])
    toks_ = fills[:3] + ([kw] if has_kw else []) + fills[3:5]
    return toks_, label

GOLD_TR, GOLD_HO = 600, 400
SYN_PER = 2000

def build(n, gen, r):
    X, Y = [], []
    for _ in range(n):
        lab = r.choice(CL)
        t, l = make_example(lab, r, gen)
        X.append(t)
        Y.append(CL.index(l))
    return X, Y

vocab = sorted({w for c in CL for w in W[c]} | set(FILLERS))
vidx = {w: i for i, w in enumerate(vocab)}

def featurize(toks_):
    v = [0.0] * len(vocab)
    for t in toks_:
        if t in vidx:
            v[vidx[t]] += 1.0
    return v

def train(X, Y):
    d = len(vocab)
    A = [featurize(x) + [1.0] for x in X]
    Ws = []
    lam = 1.0 * 600.0 / len(A)  # per-sample regularization held constant across mixes
    for k in range(3):
        y = [1.0 if yy == k else -1.0 for yy in Y]
        M = [[sum(a[i] * a[j] for a in A) + (lam if i == j else 0.0) for j in range(d + 1)] for i in range(d + 1)]
        b = [sum(a[i] * yy for a, yy in zip(A, y)) for i in range(d + 1)]
        n = d + 1
        for i in range(n):
            piv = M[i][i]
            for j in range(i + 1, n):
                f = M[j][i] / piv
                for kk in range(i, n):
                    M[j][kk] -= f * M[i][kk]
                b[j] -= f * b[i]
        w = [0.0] * n
        for i in range(n - 1, -1, -1):
            s = b[i] - sum(M[i][j] * w[j] for j in range(i + 1, n))
            w[i] = s / M[i][i]
        Ws.append(w)
    return Ws

def predict(Ws, x):
    a = featurize(x) + [1.0]
    scores = [sum(wi * ai for wi, ai in zip(w, a)) for w in Ws]
    return scores.index(max(scores))

goldX, goldY = build(GOLD_TR, 1, random.Random(405))
hoX, hoY = build(GOLD_HO, 1, random.Random(406))
syn1 = build(SYN_PER, 1, random.Random(407))
syn3 = build(SYN_PER, 3, random.Random(408))

def run_mix(gold_n, syn):
    X = goldX[:gold_n] + syn[0]
    Y = goldY[:gold_n] + syn[1]
    Ws = train(X, Y)
    return sum(1 for x, y in zip(hoX, hoY) if predict(Ws, x) == y) / GOLD_HO

a_gold = run_mix(GOLD_TR, ([], []))
a_mix1 = run_mix(GOLD_TR, syn1)
a_mix3 = run_mix(GOLD_TR, syn3)
a_pure3 = run_mix(0, syn3)
print(f"gold-only {a_gold:.3f} | +gen1-syn {a_mix1:.3f} | +gen3-syn {a_mix3:.3f} | pure-gen3 {a_pure3:.3f}")
```

The four accuracies are the evaluation scheme, and each one rules on a different claim. Gold-only 0.770 against +gen1-syn 0.775: clean synthetic mixed at 3x volume is worth +0.005 - flat within the noise a 400-example holdout carries - more of the same distribution buys nothing the gold did not already say, and the case for synthetic data has to rest on coverage or cost, never on a magical accuracy lift. +gen3-syn 0.552: the same volume of recursively degraded synthetic costs -0.218, because 960 of its 2000 examples carry a keyword that names the wrong class with the original label attached - the model's keyword evidence is contradicted at close to 3:1 and the decision boundary follows the noise. Pure-gen3 0.102 is below chance on a 3-class task: trained only on the degraded pool, the classifier learns anti-correlations that misclassify even keyword-bearing gold examples. One boundary owned honestly: this is a toy proxy - the paper measured perplexity on wikitext2, not intent accuracy - and the fence's claim is the scheme (mix, train, measure on gold holdout) and the sign pattern, not the magnitudes.

## The Campaign: One 52K Run, Four Bills

Price one full self-instruct run - the paper's own census is the workload: 52,445 instructions, 82,439 instances, 175 seeds. Four bills and one tax. Human-written: the counterfactual where domain experts author the instructions at $10 each. Self-instruct: F1's keep-rate (84 kept of 240 generated, 0.350) sets the candidate volume, priced at text-davinci-era generation rates plus the filter's compute. The anchor surcharge: ten percent of the corpus commissioned as real data, the section-3 insurance line. And the collapse tax: three ungated recursion cycles on the section-2 mechanism, with the lost type coverage priced at the human rate it would take to re-collect.

```python
import random
from collections import Counter

# one 52K-instruction instruction-tuning run, priced four ways
# run facts from Self-Instruct's own census and F1's ledger (84 kept / 240 generated)
INSTR, INSTANCES, SEED_CT = 52445, 82439, 175
KEEP = 84 / 240
WRITER_USD = 10.0
FILTER_USD = 30.0

cands = INSTR / KEEP
human_bill = INSTR * WRITER_USD
si_bill = cands * 0.0105 + FILTER_USD
anchor_real = int(INSTR * 0.1)
anchor_bill = anchor_real * WRITER_USD
print(f"one {INSTR}-instruction run ({INSTANCES} instances, {SEED_CT} seeds):")
print(f"  human-written    ${human_bill:>10,.0f}  (at ${WRITER_USD:.0f}/instruction)")
print(f"  self-instruct    ${si_bill:>10,.0f}  ({cands:,.0f} candidates at {KEEP:.3f} keep-rate + filter)")
print(f"  anchor surcharge ${anchor_bill:>10,.0f}  ({anchor_real} real instructions at 10%)")
print(f"  anchor+gen       ${si_bill + anchor_bill:>10,.0f}  (the collapse-proof bill)")

# the collapse tax: three ungated recursion cycles on a 2000-type Zipf source,
# type coverage priced at the human-written rate
V, N, TAIL_FROM = 2000, 5000, 1501
ws = [1.0 / (i + 1) for i in range(V)]
tot = sum(ws)
ws = [w / tot for w in ws]

def sample_zipf(n, r):
    return [r.choices(range(V), weights=ws)[0] for _ in range(n)]

def resample(sample, n, r):
    cnt = Counter(sample)
    return r.choices(list(cnt), weights=list(cnt.values()), k=n)

r9 = random.Random(505)
s = sample_zipf(N, r9)
t0 = len(set(s))
for _ in range(3):
    s = resample(s, N, r9)
t3 = len(set(s))
lost = (t0 - t3) / t0
recollect = lost * human_bill
print(f"collapse tax: gen-0 types-present {t0} -> gen-3 {t3} -> {lost:.3f} of the type coverage gone")
print(f"  re-collection bill for the lost coverage ${recollect:>10,.0f}")
print(f"ledger: human ${human_bill:,.0f} | self-instruct ${si_bill:,.0f} | "
      f"anchor+gen ${si_bill + anchor_bill:,.0f} | ungated gen-3 recall ${recollect:,.0f}")
```

The ledger's shape is the argument. Generation is essentially free next to writing: $1,603 against $524,450 - a 327x gap, and the reason Alpaca could fine-tune LLaMA 7B on 52K demonstrations for under $600 total. The anchor surcharge is $52,440 - 33x the generation bill, and the line item teams delete first because the pipeline runs fine without it. The collapse tax is what deleting it eventually costs: three ungated cycles erase 0.455 of the type coverage, and re-collecting that coverage at human rates runs $238,608 - 4.4x the anchored pipeline's entire bill, paid after the damage instead of before. The filter and the anchor are the whole discipline: the filter (156 of 240 candidates rejected) is what keeps the pool from recycling its own paraphrases into the training set, and the anchor is what keeps the pool tethered to the distribution the users actually live in.

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| keep-rate near 1.0, pool fills with near-identical instructions | similarity threshold too loose for the generator, or the similarity does not see paraphrase (word-set overlap misses synonym swaps ROUGE-L would too) | calibrate the threshold on your own generator's similarity distribution before the run; 0.7 is Self-Instruct's ROUGE-L rule, not a universal constant |
| keep-rate near 0, pool never grows | threshold tighter than the generator's novelty, or the prompt template keeps re-sampling the same seeds | lower the threshold or force seed-pool mixing ratios; if round-2 rejections already exceed round-1 keeps, the generator is the bottleneck, not the filter |
| collapse walk looks flat - no type loss across generations | sample size large relative to vocabulary, so every type is well-supported and nothing can go extinct | collapse needs rarity to bite; cut N or widen V until singleton types exist, then re-run - the extinction front is the rare end, and a walk without rare types has no front |
| downstream eval says synthetic data lifted accuracy 10+ points | holdout leaked: drawn from the synthetic generator's distribution instead of real gold data | regenerate the holdout from the source of truth the model will actually face; a synthetic-vs-synthetic evaluation measures the generator, not the data |
| "model collapse means never train on synthetic data" | the paper misquoted - its own 10%-preserved regime degrades minor over ten epochs; collapse is the ungated-recursion limit, not the presence of generated data | cite the control: preserve a real-data slice per generation and the slope flattens; the anchor section's paired walk is the citation |
| dedup removed to save compute, pool quality decays over rounds | the filter is the pipeline - 156 of 240 candidates rejected in the lesson's run, and each rejected paraphrase would have taught the model its own echo | keep the threshold; if compute is the constraint, filter once per round against the pool, not pairwise against everything ever generated |
| Alpaca cited as arXiv 2304.03277 | wrong paper - that ID is Peng et al.'s instruction tuning with GPT-4 data (a different 52K, English+Chinese); Alpaca has no arXiv paper | cite the CRFM blog post (March 13, 2023) and the tatsu-lab/stanford_alpaca repository; the $600 bill and 52K demonstrations live there |

## Summary

Self-instruct grows a 40-seed pool to 124 instructions at a 0.350 keep-rate with the filter's rejection rising 24 to 48 per round - the dedup rule is the pipeline, and instruction variety is recombination (20 new tokens across the whole pool, 0.113) which is why a similarity threshold can police it. Model collapse is what happens when the pool trains its own successor: even with a perfect fit and zero capacity excuse, four ungated resample cycles halve type coverage (1082 to 557), drain the tails 154 to 70, and burn down the singleton front 548 to 100 - while mass shares stay flat, which is exactly why the damage passes spot checks. The ten-percent anchor holds generation-4 coverage at 686 types against 521 and the tails at 72 against 50 - a slope-flattener, not a cure, and the cheapest line in the ledger. Downstream, the measurement scheme rules on the pool: clean synthetic at 3x volume moves accuracy +0.005 (nothing), recursively degraded synthetic at the same volume costs -0.218, pure degraded data lands below chance at 0.102 - train on it and measure, never inspect and guess. The campaign prices the discipline: $1,603 to generate against $524,450 to write, a $52,440 anchor that is 33x the generation bill and still 4.4x cheaper than one ungated collapse's $238,608 re-collection.

## References

### Related Minder Academy Documents

- [5301: Knowledge Distillation](./5301-Knowledge-Distillation.md) - training on model outputs with the teacher fixed; self-instruct bootstraps the task pool itself instead
- [5204: Preference Dataset Creation](../5200-alignment/5204-Preference-Dataset-Creation.md) - judge-scored preference pairs with held-out human calibration; the alignment-side sibling of this lesson's instruction-tuple synthesis
- [5101: LoRA (Low-Rank Adaptation) Logic](../5100-peft/5101-LoRA-Logic.md) - Alpaca as the canonical instruction-tuning dataset; this lesson owns the pipeline that produced data like it
- [5303: Federated Learning](./5303-Federated-Learning.md) - the other data-never-leaves-home regime; both make data provenance the load-bearing property

### Primary Sources

- Wang et al., "Self-Instruct: Aligning Language Models with Self-Generated Instructions" (ACL 2023, arXiv 2212.10560) - 175 seed tasks (25 classification, 150 non-classification) grown to 52,445 instructions (11,584 classification, 40,861 non-classification) and 82,439 instances (35,878 with empty input) under the ROUGE-L < 0.7 keep rule; +33% absolute over vanilla GPT-3 on Super-NaturalInstructions, roughly on par with InstructGPT_001, about 5% behind expert-written data.
- Shumailov et al., "AI models collapse when trained on recursively generated data" (Nature 631, 755-759, 2024; arXiv 2305.17493) - the collapse mechanism with its three error sources (statistical approximation primary), early collapse as tail loss, late collapse as small-variance convergence; OPT-125m on wikitext2: 34 mean perplexity trained on real data against a 115 zero-shot baseline, 20-28 points lost over five generations without original data, minor degradation with 10% preserved, and the folk repetition penalty making perplexity worse.
- Taori et al., "Stanford Alpaca: An Instruction-following LLaMA Model" (CRFM blog, March 13, 2023; code at tatsu-lab/stanford_alpaca) - 52K instruction-following demonstrations, a LLaMA 7B fine-tune for under $600, qualitatively similar to text-davinci-003; no arXiv paper exists - arXiv 2304.03277 is Peng et al.'s GPT-4-generated data, a different 52K.

---

## Next Steps

- Next Module: **[5400: Distributed Training](../5400-distributed-training/README.md)**
- Continue with: **[5401: Data Parallelism](../5400-distributed-training/5401-Data-Parallelism.md)** - the training infrastructure a grown instruction pool gets consumed by
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Reproduce the campaign on your own corpus: grow a pool from 20 seed tasks with a 0.7 keep threshold for four rounds, train the tiny intent classifier on gold versus your pool's output, and record the spread; then reserve 10% of every round's budget for hand-written seeds and compare the fourth-round pool's type coverage - the difference is the anchor's bill, paid in instructions instead of dollars.
