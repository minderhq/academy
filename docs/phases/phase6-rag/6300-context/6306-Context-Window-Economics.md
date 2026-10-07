---
Document ID: 6306
Title: "6306: Context Window Economics"
Phase: 6
Module: 6300
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'context', 'context-window', 'inference']
---

# 6306: Context Window Economics

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Accuracy Curve](#the-accuracy-curve)
- [Effective Versus Advertised](#effective-versus-advertised)
- [Pricing the Window](#pricing-the-window)
- [Sizing Per Query](#sizing-per-query)
- [One Context Budget Campaign](#one-context-budget-campaign)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Abstract

Window size is the one retrieval-system knob every vendor publishes and none prices. The 2026 model-window table lives in [6302](./6302-CAG-Long-Context-Architectures.md), and that lesson states the rule this lesson measures — advertised maxima are ceilings, not working memory — but accuracy's diminishing returns with window size is stated nowhere in the curriculum: this module's quiz leans on 6302's context-curation teaching at Q19 while the curve itself, its pricing, and its per-query-class budget go untaught. This lesson builds all three as working code. The accuracy curve is a product — P(found), the probability the evidence span fits inside the window, times q(w), graded relevance decaying under context dilution — and on a 100,000-token document it peaks at 0.3707 with a 100,000-token window and loses 0.0541 of that by 128,000: past the peak, marginal context is negative. Calibrated on NoLiMa (GPT-4o falls from a 99.3 short-context baseline to 69.7 at 32k), the fit puts the 95%-of-baseline effective length at 4,637 tokens against a 128,000 advertisement — a 27.6x gap. Pricing combines the live Gemini two-tier ($1.25/M input tokens up to 200k prompts, $2.50/M above) with [4201](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)'s KV ledger at 512 KB/token: a 128k window costs $160 per 1,000 queries and 62.5 GB of resident KV, and accuracy-per-dollar declines monotonically from 0.00730 to 0.00198 across the walk. Sizing per query class beats one-size at equal budget: routing near-evidence traffic to a 9,000-token window and deep traffic to 32,000 lifts weighted accuracy from 0.5638 to 0.6638. The campaign fence prices one month of 300,000 queries three ways: max-window nets $-43,250.00; one-size 16k nets $+2,456.36; the routed split nets $+3,993.96 on a smaller bill. [6305](./6305-LongLoRA-Ring-Attention-and-Context-Distillation.md) owns the training-side extension that moves the ceiling; this lesson owns the decision of where under the ceiling to stand.

## Learning Objectives

After this lesson, you will be able to:

- Decompose retrieval accuracy into P(found) x q(w) — a saturating coverage factor times a decaying dilution factor — and locate the window size where their product peaks.
- Calibrate a dilution curve against published needle-family benchmarks (RULER, NoLiMa) and derive an effective-length figure from an advertised one.
- Price a window in both ledgers that matter at serving: dollars per 1,000 queries under a two-tier price card, and resident KV gigabytes per request.
- Allocate window budget across query classes and show the routed split dominating one-size at an equal average budget.
- Read a month-long campaign ledger and defend the routed configuration against max-window and one-size alternatives.

## The Accuracy Curve

Two things happen when the window grows. The first is good: more of the document fits, so the probability that a given piece of evidence is inside the context — call it P(found) — rises. The second is bad: the model must find and use that evidence amid more competing text, and graded relevance decays — call it q(w). Retrieval accuracy is the product, not the max of the two, and the product is where intuition fails.

The fence below builds both factors. Evidence sits uniformly in a 100,000-token document with a 200-token span, so P(found) at window w is the fraction of sampled positions whose span fits. The dilution factor is q(w) = 0.95 / (1 + w / 64,000) — chosen so q(32k)/q(1k) = 0.677, within a whisker of GPT-4o's measured 69.7/99.3 = 0.702 and far kinder than the 15-model median that NoLiMa reports below 50 percent at 32k. This curve is, if anything, optimistic about big windows:

```python
import random

DOC_LEN = 100_000   # document tokens
EV_LEN = 200        # evidence span tokens
W_HALF = 64_000     # dilution half-width
Q0 = 0.95           # graded relevance as w -> 0
WINDOWS = [1_000, 2_000, 4_000, 8_000, 16_000, 32_000, 64_000, 100_000, 128_000]

rng = random.Random(7)
positions = [rng.uniform(0, DOC_LEN - EV_LEN) for _ in range(4_000)]

def quality(w):
    # graded relevance decays as competing context accumulates
    return Q0 / (1.0 + w / W_HALF)

def suite_acc(w):
    hits = sum(1 for p in positions if p + EV_LEN <= w)
    return (hits / len(positions)) * quality(w)

accs = [(w, suite_acc(w)) for w in WINDOWS]
for w, a in accs:
    print(f"w={w:>7,}  q(w)={quality(w):.4f}  acc={a:.4f}")
print("marginal acc per doubling:")
for i in range(1, len(accs)):
    print(f"  {accs[i-1][0]:>7,} -> {accs[i][0]:>7,}: {accs[i][1]-accs[i-1][1]:+.4f}")
best_w, best_a = max(accs, key=lambda t: t[1])
print(f"peak: w={best_w:,} acc={best_a:.4f}; 128k loses {accs[-1][1]-best_a:+.4f} vs peak")
print(f"q(32k)/q(1k) = {quality(32_000)/quality(1_000):.4f}")
```

Reading the output: the marginal column is the whole lesson. Every doubling from 1k to 64k pays a positive increment — the coverage factor is still finding evidence faster than dilution destroys it, with the largest step (+0.0970) from 32k to 64k where coverage is still climbing steeply. Then the curve bends: 100,000 tokens buy only +0.0646, and 128,000 takes 0.0541 BACK. The product peaks at 0.3707 with a 100,000-token window; the advertised-maximum window of this thought experiment is strictly worse than standing 28,000 tokens below it. This is the diminishing-returns shape the quiz asks about — except the honest version is sharper than "diminishing": past the peak the returns are negative, because P(found) has saturated near one and every marginal token is pure dilution.

## Effective Versus Advertised

The curve above is a model; the benchmarks are the measurement. RULER (Hsieh et al., COLM 2024) tested models that "all claim context sizes of 32K tokens or greater" and found "only half of them can maintain satisfactory performance at the length of 32K" — with near-perfect scores on the standard needle test that industry reporting quotes. NoLiMa (Modarressi et al., ICML 2025) removed the literal-overlap crutch the standard needle hides behind: under 1,000 tokens the fifteen tested models score near-perfect baselines, at 32,000 tokens eleven of them have dropped below 50 percent of those baselines, and even the strongest — GPT-4o — falls from 99.3 to 69.7.

Those two published points pin a usable model. Fit score(w) = BASE x exp(-a x w/32k) through the GPT-4o pair and read off the window where the score still holds 95 percent of the short-context baseline — an effective length a budget can actually be built on:

```python
import math

BASE = 99.3    # NoLiMa GPT-4o short-context baseline (%)
S32K = 69.7    # NoLiMa GPT-4o at 32k (%)

a_fit = math.log(BASE / S32K)   # score(w) = BASE * exp(-a_fit * w / 32k)

def score(w):
    return BASE * math.exp(-a_fit * (w / 32_000))

for w in [1_000, 4_000, 8_000, 16_000, 32_000, 64_000, 128_000]:
    print(f"w={w:>7,}  score={score(w):.1f}  ratio={score(w)/BASE:.3f}")
thr = 0.95 * BASE
w95 = 32_000 * math.log(BASE / thr) / a_fit
print(f"effective length at >=95% baseline ({thr:.1f}): {w95:,.0f} tokens")
print(f"advertised 128,000 vs effective {w95:,.0f} -> gap {128_000/w95:.1f}x")
print(f"fit check: score(32,000)={score(32_000):.1f} (target {S32K})")
```

Reading the output: the fit check lands on its target (69.7 at 32,000), and the walk shows why the advertised number misleads. Score 95.0 at 4,000 tokens, 83.2 at 16,000, 48.9 at 64,000 — by the advertised-class lengths the model is operating at a quarter of its short-context ability (24.1 at 128,000). The effective length at the 95-percent-of-baseline line is 4,637 tokens: the gap between 128,000 advertised and 4,637 effective is 27.6x. That ratio is not a property of GPT-4o specifically — RULER's half-of-models finding at 32K says the same thing corpus-wide. The engineering rule: never size a system from the datasheet; calibrate on a needle-family benchmark at the windows you plan to run, and treat the result as the real ceiling. [6302](./6302-CAG-Long-Context-Architectures.md) states this as "budget 100-200k as the reliable zone" in its model-window table commentary; this fence is the measurement behind the rule, and the two numbers to keep are 27.6x (advertised over effective) and the walk itself.

## Pricing the Window

Accuracy is one ledger. Serving runs two more, and both grow with w. The dollar ledger: providers price input tokens by prompt size, and the Gemini 2.5 Pro paid tier is the live example of the cliff — $1.25 per 1M input tokens for prompts up to 200k, $2.50 per 1M above — a doubling exactly in the region where the accuracy curve has already turned down. The memory ledger: [4201](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)'s KV formula, 2 x layers x heads x head_dim x bytes, gives 524,288 bytes — 512 KB — per token for the Llama-2-7B-class GQA fp16 configuration that lesson prices; a resident 128k request therefore holds 62.5 GB of KV cache before a single activation is allocated.

The fence prices both ledgers across the window walk and divides the accuracy curve by the bill:

```python
import random

DOC_LEN = 100_000
EV_LEN = 200
W_HALF = 64_000
Q0 = 0.95
PRICE_LOW = 1.25    # $/M input tokens, prompts <= 200k (Gemini 2.5 Pro paid tier)
PRICE_HIGH = 2.50   # $/M input tokens, prompts > 200k
KV_BYTES_PER_TOKEN = 2 * 32 * 32 * 128 * 2   # 4201: 2 x layers x heads x head_dim x bytes

rng = random.Random(7)
positions = [rng.uniform(0, DOC_LEN - EV_LEN) for _ in range(4_000)]

def quality(w):
    return Q0 / (1.0 + w / W_HALF)

def suite_acc(w):
    hits = sum(1 for p in positions if p + EV_LEN <= w)
    return (hits / len(positions)) * quality(w)

def price_for(w):
    return PRICE_HIGH if w > 200_000 else PRICE_LOW

def bill_per_1k(w):
    return w * price_for(w) / 1_000_000 * 1_000

accs = {w: suite_acc(w) for w in [1_000, 4_000, 8_000, 16_000, 32_000, 64_000, 100_000, 128_000]}
for w in [1_000, 4_000, 8_000, 16_000, 32_000, 64_000, 100_000, 128_000, 256_000, 512_000]:
    a = accs.get(w)
    a_txt = f"{a:.4f}" if a is not None else "   --"
    apd = f"{a/bill_per_1k(w):.5f}" if a is not None else "  --"
    kv_gb = w * KV_BYTES_PER_TOKEN / 1024**3
    print(f"w={w:>7,}  ${price_for(w):.2f}/M  bill/1k=${bill_per_1k(w):>7,.2f}  KV={kv_gb:>5.1f} GB  acc={a_txt}  acc/$={apd}")
print(f"KV: 2 x 32 layers x 32 heads x 128 dim x 2 bytes = {KV_BYTES_PER_TOKEN:,} B/token = {KV_BYTES_PER_TOKEN/1024:.0f} KB/token")
```

Reading the output: the dollar row grows linearly ($1.25 to $160.00 per 1,000 queries from 1k to 128k), the KV row grows linearly (0.5 GB to 62.5 GB), and the accuracy row peaks at 100k and falls — so acc/$ has nowhere to go but down: 0.00730 at 1k, 0.00688 at 4k and 8k, 0.00629 at 16k, 0.00523 at 32k, 0.00383 at 64k, 0.00297 at the peak window, 0.00198 at 128k. Monotone decline across the entire walk — every extra window token is bought at the same price for less accuracy, and the decline steepens exactly where the coverage factor saturates. The two rows the walk cannot price are the ones the tier jump and the KV row imply: at 256,000 tokens the bill is $640.00 per 1,000 queries — the $2.50 tier is the 1M-window tax, paid four times over at 512,000 ($1,280.00) — and 62.5 GB of KV per request bounds concurrency long before the dollar row binds. Price and provision from the full row, never from the advertised maximum.

## Sizing Per Query

One window size for all traffic is the quiet default — the retrieval layer ships one assembled context and the prompt template has one slot. But traffic is not homogeneous: in the running example, 70 percent of queries have their evidence within the first 8,000 tokens (near class) and 30 percent have it spread to 64,000 (deep class). A one-size window forces both classes into the same compromise, and the compromise is worse than it looks because the classes peak at different places.

The fence allocates a shared average-window budget of 16,000 tokens two ways: one-size (every query gets 16,000) versus routed (near traffic gets w_near, deep gets w_deep, 70/30 weighted average within budget). The per-class accuracy reuses the P(found) x q(w) product on each class's own evidence horizon:

```python
EV_LEN = 200
W_HALF = 64_000
Q0 = 0.95
NEAR_HI = 8_000     # near-class evidence lives in [0, 8k]
DEEP_LO, DEEP_HI = 8_000, 64_000
SHARE_NEAR, SHARE_DEEP = 0.70, 0.30
BUDGET = 16_000

def quality(w):
    return Q0 / (1.0 + w / W_HALF)

def class_acc(w, lo, hi):
    # P(found) x q(w) for one evidence item at position ~ U(lo, hi), span EV_LEN
    found = max(0.0, min(1.0, (w - EV_LEN - lo) / (hi - lo)))
    return found * quality(w)

one = SHARE_NEAR * class_acc(BUDGET, 0, NEAR_HI) + SHARE_DEEP * class_acc(BUDGET, DEEP_LO, DEEP_HI)
print(f"one-size w={BUDGET:,}: near={class_acc(BUDGET,0,NEAR_HI):.4f} deep={class_acc(BUDGET,DEEP_LO,DEEP_HI):.4f} weighted={one:.4f}")

best = None
for wn in range(2_000, 12_001, 1_000):
    for wd in range(16_000, 65_001, 2_000):
        avg = SHARE_NEAR * wn + SHARE_DEEP * wd
        if avg > BUDGET:
            continue
        acc = SHARE_NEAR * class_acc(wn, 0, NEAR_HI) + SHARE_DEEP * class_acc(wd, DEEP_LO, DEEP_HI)
        if best is None or acc > best[0]:
            best = (acc, wn, wd, avg)
acc_r, wn_r, wd_r, avg_r = best
print(f"routed: w_near={wn_r:,} w_deep={wd_r:,} avg={avg_r:,.0f} (budget {BUDGET:,})")
print(f"  near={class_acc(wn_r,0,NEAR_HI):.4f} deep={class_acc(wd_r,DEEP_LO,DEEP_HI):.4f} weighted={acc_r:.4f}")
print(f"gain at equal budget: {acc_r-one:+.4f}")
near_peak = max(((w, class_acc(w, 0, NEAR_HI)) for w in range(1_000, 65_001, 1_000)), key=lambda t: t[1])
deep_peak = max(((w, class_acc(w, DEEP_LO, DEEP_HI)) for w in range(1_000, 65_001, 1_000)), key=lambda t: t[1])
print(f"per-class peaks: near w*={near_peak[0]:,} acc={near_peak[1]:.4f}; deep w*={deep_peak[0]:,} acc={deep_peak[1]:.4f}")
```

Reading the output: one-size 16,000 serves the near class well (0.7600) and starves the deep class (0.1059 — most deep evidence does not fit), landing at 0.5638 weighted. The routed split gives the near class 9,000 and the deep class 32,000 at a 15,900 average — under budget — and lifts the weighted accuracy to 0.6638 (near 0.8329, deep 0.2692): +0.1000 for free, the same token budget doing a fifth more work. The peak lines explain where the gain comes from. The near class's own peak is at 9,000 (0.8329) — the first grid window past the 8,200-token point where coverage saturates; everything beyond that is dilution on queries that were already covered. The deep class's unconstrained peak is at 64,000 (0.4733), so its 32,000 allocation is the budget's cap, not its preference — with a larger budget the router would push it further. Note the two caps are different kinds: the near cap is evidence physics (nothing more to find), the deep cap is budget arithmetic (more would help). Conflating them is how systems end up paying peak prices for windows the traffic never needed.

## One Context Budget Campaign

The fences so far are per-query. A deployment decision needs the month. The campaign prices 300,000 queries at $0.05 of value per correct answer under the three candidate policies: max-window (the spec-sheet reflex), one-size 16k (the compromise), and the routed split (9k near / 32k deep):

```python
EV_LEN = 200
W_HALF = 64_000
Q0 = 0.95
NEAR_HI = 8_000
DEEP_LO, DEEP_HI = 8_000, 64_000
SHARE_NEAR, SHARE_DEEP = 0.70, 0.30
Q_MONTH = 300_000        # queries per month
VALUE = 0.05             # $ value per correct answer
PRICE_LOW, PRICE_HIGH = 1.25, 2.50

def quality(w):
    return Q0 / (1.0 + w / W_HALF)

def class_acc(w, lo, hi):
    found = max(0.0, min(1.0, (w - EV_LEN - lo) / (hi - lo)))
    return found * quality(w)

def cost(w):
    return w * (PRICE_HIGH if w > 200_000 else PRICE_LOW) / 1_000_000

configs = [
    ("A max-window 128k", 128_000, 128_000),
    ("B one-size 16k", 16_000, 16_000),
    ("C routed w_near=9k w_deep=32k", 9_000, 32_000),
]
for name, wn, wd in configs:
    acc = SHARE_NEAR * class_acc(wn, 0, NEAR_HI) + SHARE_DEEP * class_acc(wd, DEEP_LO, DEEP_HI)
    avg_w = SHARE_NEAR * wn + SHARE_DEEP * wd
    bill = Q_MONTH * (SHARE_NEAR * cost(wn) + SHARE_DEEP * cost(wd))
    value = Q_MONTH * acc * VALUE
    print(f"{name}: avg_w={avg_w:,.0f} acc={acc:.4f} bill=${bill:,.2f} value=${value:,.2f} net=${value-bill:+,.2f}")
print("tier check: every routed window <= 200k -> the $2.50 tier never fires")
```

Reading the output: config A is the honest price of the spec-sheet reflex — $48,000.00 of bill buying $4,750.00 of value, net $-43,250.00. A month of max-window retrieval is not a conservative choice that overspends for safety; it is a strictly dominated one that pays peak prices for the negative tail of the accuracy curve. Config B flips the sign — $6,000.00 of bill buying $8,456.36 of value, net $+2,456.36 — and config C dominates B outright: a $5,962.50 bill ($37.50 LESS than B) converting $9,956.46 of value ($1,500.10 more) for a net $+3,993.96, $1,537.60 ahead of B every month. The router wins by spending the same budget where marginal accuracy is positive and withholding it where marginal accuracy is negative, which is the entire content of the curve fence restated as an allocation. The tier line closes the loop with the pricing fence: every routed window is under 200k, so the $2.50 tier never fires — the 1M-window tax exists to be dodged, and dodging it is a per-query-class decision, not a global one.

## Known Failure Modes

| # | Failure | Cause | Fix |
|---|---------|-------|-----|
| 1 | Advertised window treated as working memory | The datasheet states the ceiling, not the usable zone; RULER finds half the 32K+-claiming models unsatisfactory at 32K | Calibrate effective length on a needle-family benchmark; size from the fit, not the spec |
| 2 | Max window for every query | Past the curve's peak the dilution factor dominates and accuracy FALLS (0.3707 at 100k to 0.3167 at 128k) | Walk the marginal-accuracy table for your traffic; stop at the peak, not the advertisement |
| 3 | One window size for all traffic | Heterogeneous evidence horizons make the shared compromise starve the deep class (0.1059 under a shared 16k) | Classify queries by evidence horizon and route window size per class |
| 4 | The >200k price tier forgotten | Prompts crossing 200k double the input price ($1.25 to $2.50 per 1M) exactly where accuracy is already negative | Price both tiers in the ledger; treat the tier boundary as an allocation constraint |
| 5 | KV memory forgotten at serving | 512 KB/token (4201's ledger) puts one 128k request at 62.5 GB resident | Concurrency-plan from the KV row; the dollar row binds later than the memory row |
| 6 | Optimizing retrieval hit-rate alone | Coverage saturates while q(w) keeps decaying; accuracy is the PRODUCT P(found) x q(w) | Report the product, never a single factor; both fences here print the product |
| 7 | Effective length assumed from advertising | 128,000 advertised against 4,637 effective at the 95-percent-of-baseline line — a 27.6x gap | Fit the decay from published benchmark points; re-fit when the model or version changes |
| 8 | Evaluating only at short contexts | Near-perfect sub-1k baselines hide the decay (NoLiMa: GPT-4o 99.3 to 69.7 by 32k) | Evaluate at the windows you plan to run, with beyond-literal-match probes |

## Summary

- **The accuracy curve is a product** — P(found) saturating, q(w) decaying — and on the 100,000-token document the product peaks at 0.3707 with a 100,000-token window; the marginal table turns NEGATIVE at 128,000 (-0.0541 vs peak). Diminishing returns is the polite name; the honest name is a peak with a downside.
- **Effective length is not advertised length** — calibrated on NoLiMa (GPT-4o 99.3 to 69.7 between short context and 32k), the exponential fit puts the 95-percent-of-baseline line at 4,637 tokens against a 128,000 advertisement: 27.6x. RULER says the corpus-wide story is the same (half the 32K-claiming models unsatisfactory at 32K).
- **Windows price in two ledgers** — the Gemini two-tier card ($1.25/M to 200k prompts, $2.50/M above) and 4201's KV ledger (512 KB/token, 62.5 GB resident at 128k) — and accuracy-per-dollar declines monotonically across the walk, 0.00730 to 0.00198.
- **Routing beats one-size at equal budget** — near class to 9,000 (its evidence-horizon cap, 0.8329), deep class to 32,000 (the budget's cap, not its 64,000 unconstrained peak) — 0.5638 to 0.6638, +0.1000 on a 15,900 average against a 16,000 budget.
- **The month ledger settles it** — max-window nets $-43,250.00, one-size 16k nets $+2,456.36, routed nets $+3,993.96 on a bill $37.50 smaller than one-size: dominance, not a trade-off.
- **The lesson's decision**: window size is a per-query-class allocation priced in dollars, KV gigabytes, and graded relevance — the curve makes it choosable, the campaign makes it checkable.

## References

### Related Minder Academy Documents

- [6302: CAG and Long-Context Architectures](./6302-CAG-Long-Context-Architectures.md) — the serving-side curation strategies and the 2026 model-window table; states the budget-100-200k reliable-zone rule this lesson measures.
- [4201: Context Window Physics and OOM Prevention](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md) — the KV-cache formula this lesson reuses at 512 KB/token and the OOM side of the 62.5 GB row.
- [6305: LongLoRA, Ring Attention, and Context Distillation](./6305-LongLoRA-Ring-Attention-and-Context-Distillation.md) — the training-side extension that moves the ceiling this lesson prices under.

### Primary Sources

- Hsieh, C.-P., et al. (2024). *RULER: What's the Real Context Size of Your Long-Context Language Models?* COLM 2024. arXiv:2404.06654 — "only half of them can maintain satisfactory performance at the length of 32K."
- Modarressi, A., et al. (2025). *NoLiMa: Long-Context Evaluation Beyond Literal Matching.* ICML 2025. arXiv:2502.05167 — eleven of fifteen models below 50 percent of baseline at 32K; GPT-4o 99.3 to 69.7.
- Liu, N. F., et al. (2024). *Lost in the Middle: How Language Models Use Long Contexts.* TACL. arXiv:2307.03172 — the positional mechanism underneath q(w); the ordering fix itself is owned by 6302.
- Google AI. *Gemini API Pricing* (ai.google.dev/gemini-api/docs/pricing) — the $1.25/$2.50 two-tier input price card, live-verified 2026-10-06.

## Next Steps

- **Next Module:** continue with [assessment/QUIZ.md](assessment/QUIZ.md) — Q19 is the question this lesson answers; the marginal-accuracy table with its -0.0541 tail, the 27.6x advertised-versus-effective gap, and the +0.1000 routing gain are the mechanics behind it.
- **Continue with:** the [6400: Vector Databases](../6400-vector-databases/README.md) module for where the retrieval layer that decides what enters the window lives in production.
- **Assessment:** extend the routing fence with a third query class — evidence spread to 128,000, 10 percent of traffic — and re-derive the allocation under the same 16,000 average budget; then re-run the campaign fence at $0.02 of value per correct answer and report which configs flip negative.
