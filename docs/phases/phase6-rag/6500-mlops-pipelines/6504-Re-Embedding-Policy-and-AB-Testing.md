---
Document ID: 6504
Title: "6504: Re-Embedding Policy and A/B Testing"
Phase: 6
Module: 6500
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'mlops', 'evaluation', 'embeddings']
---

# 6504: Re-Embedding Policy and A/B Testing

## Abstract

A retrieval fleet never finishes updating, and the module's own QUIZ admits the two disciplines that keep the updates honest are missing: "the re-embedding policy for a changing corpus is taught nowhere in the curriculum, so Q2 and Q19 lean on versioning the new artifact," and "formal A/B testing and human evaluation are taught nowhere in the curriculum, so Q6 and Q17 lean on the paired-comparison discipline as their closest analog." The two gaps are one story. Documents change, so vectors must change — but a changed document upserted in the *same* model's space is ordinary maintenance, while a *changed model* invalidates every stored vector at once, because the model is not a component of the index, it is the coordinate system the index lives in. Shipping the new coordinate system is then an experiment, and the experiment needs the machinery this lesson builds: a shadow window that runs both indexes, an explicit cutover gate, an experiment sized for the effect it claims to detect, a horizon fixed before the first look, and a human-eval rubric whose agreement number is chance-corrected before anyone reads it. [6501: ML Lifecycle Management](6501-ML-Lifecycle-Management.md) owns McNemar's exact test and the five-stage lifecycle; [6503: Model Registry](6503-Model-Registry.md) owns where the winning version then lives; [6104: Embedding Sciences](../6100-vector/6104-Embedding-Sciences.md) owns the vector decisions this lesson operationalizes; [6403: Qdrant Production Deployment](../6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md) owns the store the shadow index lands in. What lives here is the policy and the proof.

---

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Churn Ledger](#the-churn-ledger)
- [Why a Model Change Is Different](#why-a-model-change-is-different)
- [The Shadow Window](#the-shadow-window)
- [Sizing the Ship Decision](#sizing-the-ship-decision)
- [The Peeking Trap](#the-peeking-trap)
- [The Human Half](#the-human-half)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- **Separate the two update classes**: price corpus churn as incremental upserts and reserve the full re-embed for the one event that actually forces it
- **Prove cross-space incomparability**: show why mixing vectors from two embedders into one index scores noise, and why a "minor" fine-tune still shuffles rankings
- **Run a shadow migration**: dual-write both indexes, score a golden set on each, and apply an explicit cutover gate
- **Size an experiment before running it**: compute power on discordant pairs and state how many the claim needs
- **Fix the analysis before launch**: hold the significance level at its nominal value by fixing the horizon, and name the group-sequential escape hatch
- **Grade the human half**: report chance-corrected inter-rater agreement instead of the flattering raw number

---

## The Churn Ledger

A production corpus is never finished. Pages get edited, products get delisted, policies get revised — at almost any real deployment, some fraction of the corpus is wrong at any moment. The QUIZ's Q19 offers three cadences ("daily," "hourly," "when docs change") and the temptation is to treat re-embedding as a calendar discipline. The ledger says otherwise: embedding work is proportional to documents touched, and the only cadence that pays for exactly what changed is the incremental one.

```python
import math

# corpus churn never justifies a full re-embed; the cadences price the waste
N = 1_000_000          # corpus size (documents)
churn = 0.005          # 0.5% of documents change per day
changed = int(N * churn)  # 5,000 documents per day

# naive cadences: a full rebuild every K periods costs N doc-embeds each time
daily = 365 * N
weekly = 52 * N
monthly = 12 * N
incremental = 365 * changed

print("churn ledger (doc-embeds per year, corpus 1M @ 0.5%/day churn):")
print(f"  rebuild daily   : {daily:>12,}  ({daily / incremental:.1f}x incremental)")
print(f"  rebuild weekly  : {weekly:>12,}  ({weekly / incremental:.1f}x incremental)")
print(f"  rebuild monthly : {monthly:>12,}  ({monthly / incremental:.1f}x incremental)")
print(f"  incremental     : {incremental:>12,}")
print(f"  model change    : {N:>12,}  (forced, once per model)")
print(f"  yearly waste of the monthly habit: {(monthly - incremental):,} doc-embeds")
```

The monthly habit alone burns 12,000,000 doc-embeds a year to recompute the 1,825,000 documents that actually changed — a 6.6x premium for nothing, 10,175,000 doc-embeds wasted — and the weekly and daily habits are 28.5x and 200.0x. The reason the waste buys nothing is the next section: a changed document upserted under the *same* model lands in exactly the coordinate system the index already uses. Nothing about churn touches the other 99.5% of the vectors, so a rebuild recomputes identical coordinates for identical documents.

---

## Why a Model Change Is Different

The model is not a component of the index. It is the coordinate system the index lives in, and a different model — a new checkpoint, a different fine-tune, a different vendor — is a different coordinate system. Swapping the encoder while keeping the old vectors does not degrade search; it silently changes what the query vectors mean while the stored vectors keep the old meaning.

```python
import numpy as np

# same documents, three "embedders": model A, an unrelated model B,
# and model A after a small fine-tune
rng = np.random.default_rng(11)
n_docs, d = 2000, 64
X = rng.normal(size=(n_docs, 8))                     # latent document features
W_A = rng.normal(size=(8, d))                        # model A's projection
W_B = rng.normal(size=(8, d))                        # model B (independently trained)
W_A2 = W_A + 0.75 * rng.normal(size=W_A.shape)       # model A after a small fine-tune

def norm_rows(M):
    return M / np.linalg.norm(M, axis=1, keepdims=True)

E_A, E_B, E_A2 = norm_rows(X @ W_A), norm_rows(X @ W_B), norm_rows(X @ W_A2)
probe = norm_rows((X[:100] + 0.10 * rng.normal(size=(100, 8))) @ W_A)  # near-dup queries

def top10_overlap(S_a, S_b):
    return float(np.mean([
        len(set(np.argsort(-S_a[i])[:10]) & set(np.argsort(-S_b[i])[:10]))
        for i in range(S_a.shape[0])
    ]))

print("same-document cosines across spaces (probe doc vs its own index entry):")
print(f"  A vs A  (identity)        : {np.mean([probe[i] @ E_A[i] for i in range(100)]):.3f}")
print(f"  A vs B  same doc          : {np.mean([probe[i] @ E_B[i] for i in range(100)]):+.3f}"
      "   (noise -- a mixed index scores garbage)")
print(f"  A vs A-finetuned same doc : {np.mean([probe[i] @ E_A2[i] for i in range(100)]):.3f}"
      "   ('minor update', vector half-recognizable)")
print(f"  top-10 neighbor overlap, A vs A2: {top10_overlap(probe @ E_A.T, probe @ E_A2.T):.1f}/10"
      "   (ranking shuffled anyway)")
print(f"  top-10 neighbor overlap, A vs B : {top10_overlap(probe @ E_A.T, probe @ E_B.T):.1f}/10"
      "   (independent spaces share nothing)")
```

Read the fine-tuned column as the production trap. The same-document cosine of 0.786 looks "close enough to the same space" — and the neighbor overlap tells the truth: 6.8 of the champion's top-10 results are gone under the fine-tuned encoder. The vector is half-recognizable and the ranking moved anyway, which means search quality changed with no error anywhere. Under an unrelated model the same document shares nothing — 0.1 of 10 neighbors and a +0.065 self-cosine that is pure noise. This is why the churn ledger's "model change" row is one forced full pass: every vector must be recomputed into the new space before it can be searched at all.

---

## The Shadow Window

The forced re-embed still does not force an outage or a flip of a coin. The production playbook is a window in which both indexes live: the champion keeps serving, the challenger is backfilled in parallel, a golden set of queries is scored against both, and an explicit gate — written before the window opens — decides the cutover.

```python
import math
import numpy as np

# migration gate: golden set, both indexes live, the rule written first
rng = np.random.default_rng(29)
n_q, k = 40, 10
champ_hits = rng.binomial(k, 0.72, n_q)              # champion recall slots per query
delta = rng.choice([0, 1, 2, 3, -1, -2], n_q,
                   p=[0.35, 0.30, 0.15, 0.10, 0.07, 0.03])
chall_hits = np.clip(champ_hits + delta, 0, k)       # same queries, challenger index
champ_r, chall_r = champ_hits.mean() / k, chall_hits.mean() / k
reg = int((chall_hits < champ_hits).sum())
gain = int((chall_hits > champ_hits).sum())

ledger_per_M = 6.14                                  # 6104's fp32 ledger, 1536 dims
shadow = 2 * ledger_per_M                            # both indexes live
window_days = math.ceil(1_000_000 / 50_000)          # backfill at 50k docs/day
ship = (chall_r >= champ_r) and (reg <= 8)           # the gate, written first

print(f"shadow window (golden set n={n_q}, recall@{k}, paired):")
print(f"  champion  {champ_r:.3f}   challenger {chall_r:.3f}")
print(f"  per-query: +{gain} / -{reg}   (gate: no worse overall AND regressions <= 8)")
print(f"  storage during window: {ledger_per_M:.2f} -> {shadow:.2f} GB per M docs (fp32)")
print(f"  backfill 1M docs @ 50k/day = {window_days} days of dual-write")
print(f"  CUTOVER: {'SHIP' if ship else 'HOLD'}")
```

The gate fires: +15 queries improved against 6 regressed, challenger 0.758 over champion 0.728, no worse overall with regressions inside the bound. The window's price is concrete — during the 20 backfill days the fleet pays double storage, 12.28 GB per million documents at fp32 on 6104's own ledger, plus the dual-write traffic. On Qdrant the shadow can even live inside the champion's collection: named vectors let one point carry several embeddings, and as of v1.18.0 a named vector can be added to (or removed from) an existing collection without recreating it, so the migration reads as "add the challenger vector name, backfill, gate, then drop the champion name." What the gate does *not* do is license a marginal win — +15/−6 on forty queries is an engineering check against disasters, and the difference between "no disasters" and "statistically real" is the next section.

---

## Sizing the Ship Decision

[6501](6501-ML-Lifecycle-Management.md) owns the paired test itself: McNemar's exact test compares only the *discordant* pairs — the queries where the two indexes disagree — against a fair coin. What 6501 does not own is the question a designer must answer first: *how many discordant pairs does the claim need?* A golden set of forty queries can detect a disaster, but a marginal win lives below its resolution.

```python
import math
import numpy as np

# power on discordant pairs: exact binomial, vectorized through the cdf
rng = np.random.default_rng(31)
sims = 20_000

print("power to detect a 60/40 true split on discordant pairs (alpha=0.05 exact):")
for n_disc in (25, 50, 100, 200, 400):
    wins = rng.binomial(n_disc, 0.6, sims)           # challenger wins the pair
    losses = n_disc - wins
    grid = np.arange(n_disc + 1)                     # one cdf per n, reused per sim
    pmf = np.array([math.comb(n_disc, i) for i in grid]) / 2 ** n_disc
    cdf = np.cumsum(pmf)
    pvals = np.minimum(1.0, 2.0 * cdf[np.minimum(wins, losses)])
    print(f"  n_discordant {n_disc:>3}: power {np.mean(pvals < 0.05):.3f}")
```

The curve is the design input. At the golden-set scale — 25 discordant pairs, the size 7104's bootstrap interval already flagged as nearly thirty points wide — a challenger that genuinely wins 60% of disagreements is detected 15% of the time; the experiment misses its own true effect more often than it catches it. Detecting that same split needs roughly 200 discordant pairs — 0.790 power — and at 400 the test is near-certain at 0.976. The tooling path is one import — `from statsmodels.stats.contingency_tables import mcnemar`, constructed as `mcnemar(table, exact=True, correction=True)` and read off `.pvalue` — but the table's row counts are chosen here, before the window opens, not after the results are in.

---

## The Peeking Trap

Sizing fixes how many observations the claim needs; the horizon fixes when the claim may be made. A/B dashboards tempt a daily check, and each check at the nominal 0.05 is another chance to cross the line on pure noise. The fix costs nothing: decide the look count and the final analysis time before launch.

```python
import numpy as np

# A/A experiments (true null); dashboard checked at 10 looks; alpha inflates
rng = np.random.default_rng(47)
sims, n_per_look, looks = 20_000, 400, 10
p0 = 0.10
succ_x = rng.binomial(n_per_look, p0, size=(sims, looks))   # arm X increments
succ_y = rng.binomial(n_per_look, p0, size=(sims, looks))   # arm Y increments
cum_x, cum_y = np.cumsum(succ_x, 1), np.cumsum(succ_y, 1)
n = np.arange(1, looks + 1) * n_per_look
z = (cum_x / n - cum_y / n) / np.sqrt(p0 * (1 - p0) * (2 / n))
sig = np.abs(z) > 1.96

print(f"peeking trap (A/A, n={n_per_look}/look, {looks} looks, per-look alpha=0.05):")
print(f"  false-positive rate, ONE final look : {float(sig[:, -1].mean()):.3f}")
print(f"  false-positive rate, peeking daily  : {float(sig.any(axis=1).mean()):.3f}")
```

Ten looks on accumulating data and the realized false-positive rate is 0.198 — four times the nominal level, on experiments where both arms are identical. The intuition that "more data can't hurt" fails because each look re-tests everything seen so far, so the test's guarantees apply only to the one analysis the design fixed. If the business genuinely needs interim looks, the formal escape is a group-sequential boundary — Pocock-style spending keeps the overall level at 0.05 by demanding more extreme z at every interim — and the retrieval-native alternative is interleaving, which (Radlinski & Craswell 2013) blends both rankers into one result list and reads clicks as a direct paired vote. What is not on the menu is the unadjusted daily glance.

```text
independent looks (upper bound):  alpha_overall ~= 1 - (1 - alpha_look)^k
                                   k = 10, alpha_look = 0.05  ->  0.40
accumulating-data looks (measured): 0.198  -- correlated, so smaller than the
independent bound, but four times the nominal level all the same
```

---

## The Human Half

The QUIZ's Q17 answers "automated metrics + human," and the human half is where A/B discipline most often quietly dies — not from absence but from a number that flatters. Ask five annotators to grade twenty retrieved contexts on a three-point relevance rubric and the raw all-pairs agreement will look respectable. It is respectable for a reason that has nothing to do with the raters: when the rating marginals are skewed, chance alone produces most of the agreement.

```python
import numpy as np

# five raters, twenty items, three-point rubric; kappa corrects for chance
rng = np.random.default_rng(59)
n_items, n_raters, cats = 20, 5, 3
truth = rng.choice(cats, n_items, p=[0.3, 0.5, 0.2])
votes = np.stack([
    np.clip(truth + rng.choice([-1, 0, 1], n_items, p=[0.25, 0.6, 0.15]), 0, 2)
    for _ in range(n_raters)
])

table = np.zeros((n_items, cats), dtype=int)
for i in range(n_items):
    for c in range(cats):
        table[i, c] = (votes[:, i] == c).sum()
P_i = ((table ** 2).sum(axis=1) - n_raters) / (n_raters * (n_raters - 1))
P_bar = P_i.mean()                                   # observed agreement
p_j = table.sum(axis=0) / (n_items * n_raters)
P_e = (p_j ** 2).sum()                               # agreement chance predicts
kappa = (P_bar - P_e) / (1 - P_e)                    # Fleiss' kappa

pairs = [(a, b) for a in range(n_raters) for b in range(a + 1, n_raters)]
agree = np.mean([votes[a, i] == votes[b, i] for a, b in pairs for i in range(n_items)])
print(f"human eval, {n_raters} raters x {n_items} items x {cats}-point rubric:")
print(f"  raw all-pairs agreement : {agree:.3f}   (the flattering number)")
print(f"  Fleiss' kappa           : {kappa:.3f}   (chance-corrected; ~0.4 = moderate)")
print(f"  category marginals      : {np.round(p_j, 2).tolist()}")
```

Same five raters, same twenty items: raw agreement 0.670 against a Fleiss' kappa of 0.480 — moderate, not good, and the honest number for the eval report. The marginals line explains the gap: the middle rubric point dominates, so two raters who both reach for the safe middle agree by coincidence. Chance-corrected agreement is the eval report's opening line; the raw number is what the rubric revision session reads when kappa says the instrument, not the model, is the weak link.

---

## Known Failure Modes

| # | Failure | What it looks like | Defense |
|---|---------|--------------------|---------|
| 1 | Upserting new-model vectors into the champion index | No error anywhere; rankings silently change meaning | The shadow window: the challenger writes to its own index (or its own named vector), never into the champion's |
| 2 | Treating a fine-tune as "the same model" | Same-doc cosine 0.786 reads as "close enough" | Check neighbor overlap, not self-cosine — 6.8/10 is a different retriever |
| 3 | Re-embedding on a calendar | Monthly rebuilds at 6.6x the incremental cost, recomputing identical coordinates | Churn ledger: pay per changed document; the full pass is for model changes only |
| 4 | Deleting the champion index at cutover | No rollback path if the challenger misbehaves in week two | Keep the champion through a freeze window; on Qdrant the drop is one named-vector removal |
| 5 | Backfill rate assumed, not measured | "20 days" becomes 60 when upsert throughput is a third of the estimate | Measure store upsert throughput before quoting the window; size the dual-write cost from the measured number |
| 6 | Golden-set verdicts as ship decisions | +3 queries on n=40 reads as a win | Engineering gates catch disasters; marginal wins need sized experiments (0.15 power at 25 discordant pairs) |
| 7 | The daily dashboard glance | Ten looks at nominal 0.05 realize 0.198 on identical arms | Fix horizon and look count at launch; group-sequential boundaries if interim looks are real requirements |
| 8 | Raw agreement in the eval report | 0.670 agreement on a skewed rubric reads as "annotators aligned" | Fleiss' kappa as the opening line; raw agreement only inside the rubric-revision session |

---

## Summary

A retrieval fleet faces exactly two update problems, and they have different shapes. Corpus churn is ordinary maintenance — changed documents are upserted into the space that already exists, and the churn ledger prices every calendar-cadence alternative as a premium — 6.6x for the monthly habit, 200.0x for the daily — for recomputing coordinates that were already correct. A model change is the one event that forces the full pass, because the model is the coordinate system: the fine-tuned encoder keeps a 0.786 self-cosine while deleting three of the champion's ten neighbors, and an unrelated encoder shares nothing at all.

The migration is then a controlled experiment, and the machinery is procedural: a shadow window with measured dual-write economics, a golden set scored on both indexes, a cutover gate written before the window opens. The gate is an engineering instrument — no worse overall, regressions bounded — and the statistical instrument is separate: size the experiment on discordant pairs before running it (200 discordant pairs buy 0.790 power at a 60/40 split, while the 25-pair golden set detects it 0.153 of the time), fix the horizon so peeking cannot inflate the level from 0.05 to 0.198, and grade the human arm with chance-corrected kappa, because the raw agreement number is a function of the rubric's marginals before it is a function of the raters.

Version the decision, not just the artifact: [6503](6503-Model-Registry.md) records which embedding version serves, [6501](6501-ML-Lifecycle-Management.md)'s McNemar test supplies the paired verdict, and this lesson supplies the policy that says when the question is worth asking and the machinery that makes the answer trustworthy.

---

## References

### Related Minder Academy Documents

- [6104: Embedding Sciences - Pooling, Matryoshka, and MTEB](../6100-vector/6104-Embedding-Sciences.md) — the vector decisions (pooling, truncation, benchmark menus) this lesson operationalizes
- [6501: ML Model Lifecycle Management](6501-ML-Lifecycle-Management.md) — the five-stage lifecycle and McNemar's exact test on discordant pairs
- [6502: CI/CD for Machine Learning](6502-CI-CD-for-ML.md) — the automation that runs the shadow window and the gate
- [6503: Model Registry](6503-Model-Registry.md) — where the winning embedding version is recorded and promoted
- [6403: Qdrant Production Deployment](../6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md) — the store the shadow index lands in
- [7104: Agent Evaluation and Observability](../../phase7-agentic/7100-architecture/7104-Agent-Evaluation-and-Observability.md) — the bootstrap-interval discipline behind small-n golden sets

### Primary Sources

- McNemar, Q. (1947). "Note on the sampling error of the difference between correlated proportions or percentages." *Psychometrika*, 12(2) — the exact test on discordant pairs
- Fleiss, J. L. (1971). "Measuring nominal scale agreement among many raters." *Psychological Bulletin*, 76(5) — the chance-corrected kappa this lesson's human-eval section computes
- Pocock, S. J. (1977). "Group sequential methods in the design and analysis of clinical trials." *Biometrika*, 64(2) — the boundary that keeps interim looks honest
- Radlinski, F., & Craswell, N. (2013). "Optimized interleaving for online retrieval evaluation." *WSDM 2013* — the retrieval-native alternative to arm-split A/B tests
- Kohavi, R., Tang, D., & Xu, Y. (2020). *Trustworthy Online Controlled Experiments.* Cambridge University Press — the peeking trap and experiment trustworthiness, systematized
- [Qdrant docs: Vectors](https://qdrant.tech/documentation/concepts/vectors/) — named vectors per point; add/remove on an existing collection as of v1.18.0
- [statsmodels: statsmodels.stats.contingency_tables.mcnemar](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html) — `mcnemar(table, exact=True, correction=True)`

---

## Next Steps

- **Next Module:** close phase 6 with [assessment/QUIZ.md](assessment/QUIZ.md) — Q2, Q6, Q17, and Q19 are the four questions this lesson's fences answer with arithmetic
- **Continue with:** [6503: Model Registry](6503-Model-Registry.md) — record the challenger's promotion the gate just decided, with the golden-set scores attached to the version
- **Hands-on:** re-run the shadow-window fence with your own golden set and champion/challenger hit counts; then run the sizing fence and write down the discordant-pair count your next embedder migration actually needs before you open the window
