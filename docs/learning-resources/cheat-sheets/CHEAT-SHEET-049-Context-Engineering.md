---
Document ID: CHEAT-SHEET-049
Title: "CHEAT-SHEET-049: Context Engineering - the Dilution Curve, the Stuffing Bet, and the Distilled Prompt"
Last Updated: 2026-10-24
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rag', 'context-window', 'long-context']
---

# CHEAT-SHEET-049: Context Engineering - the Dilution Curve, the Stuffing Bet, and the Distilled Prompt

The context-engineering surface is phase6-rag's 6300-context track - 6301 Neo4j and Knowledge Graphs, 6302 CAG Long-Context Architectures, 6305 LongLoRA Ring Attention and Context Distillation and 6306 Context Window Economics - four modules with no sheet anywhere in the track (scope scan: the 00-META sheet index carries no id beside any of the four; CHEAT-SHEET-036 owns the RAG pipeline overview and CHEAT-SHEET-047 the retrieval core beside it, QUICK-REF-VOLUME-6 carries the syntax, not the closure). This sheet takes the track as the three questions the student actually asks: what a longer window actually buys (the dilution curve, the effective length hiding behind the advertised spec, and the two ledgers a window bills), when stuffing beats retrieval (the stuffing bet and the routed budget), and how the training side changes the trade (ring attention's group shift and LongLoRA's parameter ledger, then distilling the context into weights) - closing the 6300 track.

The sheet runs as seven priced exhibits: the dilution curve P(found) x q(w) with its interior peak and its negative tail marginal (F1), the NoLiMa calibration that converts an advertised window into an effective length (F2), the two-ledger price of a window (F3), the stuffing bet against retrieval (F4), the routed budget where two window sizes beat one at the same spend (F5), ring attention's group shift with the LongLoRA parameter ledger (F6), and context distillation's serving contract (F7). Every number below is printed by the canonical fence at the bottom of the page: the full 366-line stdlib fence reproduces all seven from fixed-seed runs its own asserts pin - no numpy, no wall clock - and its 81-line output sits frozen below it byte-for-byte.

## The Dilution Curve - the Accuracy Product with an Interior Peak

Long-context accuracy is a product, not a sum: the fence's suite model prices P(found) x q(w), where P(found) is the share of 4,000 uniformly drawn evidence spans that fit inside the window and q(w) = 0.95 / (1 + w/64,000) is what long context leaves of graded relevance. The shape is the lesson: the marginals RISE from +0.0093 (1k -> 2k) through +0.0970 (32k -> 64k), the last real gain lands +0.0646 into w=100,000 - and the 128,000 marginal turns NEGATIVE at -0.0541. The peak sits at w=100,000 with accuracy 0.3707, and past it the extra tokens buy nothing: P(found) saturated at the 100k document length, so every added token pays full q and retrieves nothing. Context is not a reservoir that accumulates; it is a bet whose expected value has an interior maximum. Even before the tail, decay bites: q(32,000)/q(1,000) = 0.6771 - a 32k window keeps only two thirds of the short-context quality.

## The NoLiMa Calibration - the Effective Length and the 27.6x Gap

The advertised window is a capacity spec, not a quality spec. NoLiMa prices the gap: GPT-4o holds 99.3 at short context and 69.7 at 32k, and the one-parameter fit BASE x exp(-a x w/32,000) with a = ln(99.3/69.7) reproduces every point (fit check at 32k: 69.7 against 69.7). Read at the 95% line - 94.3 - the effective length is 4,637 tokens against an advertised 128,000: a 27.6x gap. The decay is already steep where marketing stops talking: 90.9 (0.915 of baseline) at 8k, 48.9 (0.493) at 64k, 24.1 (0.243) at 128k. Every plan in this sheet is sized against 4,637, not against the spec sheet.

## The Two-Ledger Price of a Window - the Metered Bill and the KV Residency

The same window bills twice: once per token at the API, once per resident KV page on the card. KV is the hidden ledger - 2 x layers x hidden x kv-dtype-bytes = 524,288 B per token at the 32-layer, 4,096-hidden reference point - so a 128k prompt parks 62.5 GB before the weights and activations, and 512k parks 250.0 GB. The token meter tiers at 200k: $1.25/M below, $2.50/M beyond, which is why a 512k prompt costs $1,280.00 per 1,000 queries - 1,024x the 1k row's $1.25. And accuracy per dollar declines strictly monotonically across all eight accuracy-bearing rows: 0.00730 at 1k to 0.00198 at 128k. Bigger is not just worse per token; it is worse per dollar, at every step.

| Window | Tier | Bill per 1k queries | KV resident | Accuracy | Accuracy per $ |
| --- | --- | --- | --- | --- | --- |
| 1,000 | $1.25/M | $1.25 | 0.5 GB | 0.0091 | 0.00730 |
| 4,000 | $1.25/M | $5.00 | 2.0 GB | 0.0344 | 0.00688 |
| 8,000 | $1.25/M | $10.00 | 3.9 GB | 0.0688 | 0.00688 |
| 16,000 | $1.25/M | $20.00 | 7.8 GB | 0.1258 | 0.00629 |
| 32,000 | $1.25/M | $40.00 | 15.6 GB | 0.2092 | 0.00523 |
| 64,000 | $1.25/M | $80.00 | 31.2 GB | 0.3061 | 0.00383 |
| 100,000 | $1.25/M | $125.00 | 48.8 GB | 0.3707 | 0.00297 |
| 128,000 | $1.25/M | $160.00 | 62.5 GB | 0.3167 | 0.00198 |
| 256,000 | $2.50/M | $640.00 | 125.0 GB | -- | -- |
| 512,000 | $2.50/M | $1,280.00 | 250.0 GB | -- | -- |

## The Stuffing Bet - Cache Fixes the Bill, Never the Curve

CAG's route (6302) is the stuffing bet: skip retrieval, ship the corpus whole. At D=40,000 the bet prices as follows: 63.8 - 0.642 of baseline - for $50.00 per 1k and 19.5 GB resident, against retrieval into w=4,000 keeping 95.0 - 0.957 - for $5.00 and 2.0 GB. Ten times the bill for +31.2 points of relative quality. The break-even corpus at the 95% line is 4,637 tokens - F2's effective length again, because it is the same equation: ln(1/0.95)/a_fit. Stuffing only wins while the corpus fits inside what the model can actually use. What stuffing genuinely buys is the 20 ms retrieve hop, and that is real: the prompt cache keeps hot prefixes resident and serves repeated context at a fraction of the metered bill. But the cache fixes the BILL, never the CURVE - a cached dilution is still diluted.

| Route | Score (share of baseline) | Bill per 1k | KV resident |
| --- | --- | --- | --- |
| stuff D=40,000 whole | 63.8 (0.642) | $50.00 | 19.5 GB |
| retrieve into w=4,000 | 95.0 (0.957) | $5.00 | 2.0 GB |

```text
Stuff when the corpus fits inside the effective length (F2) and the
doc set is stable across queries; retrieve once the corpus is larger
than the model can actually use. The prompt cache settles the token
bill - it never touches the quality curve.
```

## The Routed Budget - Two Window Sizes Beat One at the Same Spend

Route, do not scale. Split the traffic 70/30 between near queries and deep ones: the near class peaks at w\*=9,000 (accuracy 0.8329), the deep class at w\*=64,000 (0.4733). At a 16,000-token average budget the routed split lands near=0.8329 / deep=0.2692 for a weighted 0.6638, against the one-size 16k window's weighted 0.5638 - +0.1000 for the same spend (the routed average is 15,900 tokens, 100 under budget). The month campaign, at 300,000 queries and $0.05 of value per correct answer, is the whole sheet in one ledger: the max-window 128k plan burns $48,000.00 a month to earn $4,750.00 of value - net $-43,250.00; one-size 16k nets +$2,456.36; the routed plan nets +$3,993.96. And every routed window sits at or under 200k, so the $2.50 tier never fires - the routing also dodges the price jump.

| Plan | Average window | Weighted acc | Monthly bill | Value | Net |
| --- | --- | --- | --- | --- | --- |
| A max-window 128k | 128,000 | 0.3167 | $48,000.00 | $4,750.00 | $-43,250.00 |
| B one-size 16k | 16,000 | 0.5638 | $6,000.00 | $8,456.36 | $+2,456.36 |
| C routed 9k/32k | 15,900 | 0.6638 | $5,962.50 | $9,956.46 | $+3,993.96 |

```text
Classify the query before choosing the window: near-class queries
peak near 9,000 tokens, deep-class near 64,000, and two dials beat
one at the same budget - +0.1000 weighted accuracy for 15,900 vs
16,000 average tokens. Route by query class, not by corpus size.
```

## Ring Attention - the Group-Shift Law and the Parameter Ledger

Training-time machinery widens the window differently. Ring attention splits a 16-token sequence across 4 devices into 4-token groups - and the grouping law is not an implementation detail: without the group-shift pattern every layer attends inside its own group and the reach stays 4/4 forever, at every depth. The alternating shift is what starts cross-group flow: 4/4 -> 8/8 -> 12/12 -> 16/16 by layer 4, and the reach saturates there - depth finishes what the shift starts. The ring's arithmetic is exact, not approximate: full attention and 4 ring rotations agree to max|diff| = 2.22e-16, float noise. The memory case is why the machinery exists: KV per device falls 4.0x and softmax cells per step 16.0x on the toy; at N=65,536 the full N x N census is 4,294,967,296 cells (17.2 GB) against the ring's 67,108,864 per materialization (64x less) and 8,192 KV entries per device (8x less). LongLoRA then prices the training itself: on the toy transformer the full-parameter bill is 6,720 (100.0%), LoRA-only is 256 (3.8%), and LongLoRA's LoRA-plus-unfrozen-embed-plus-norm is 832 (12.4%); at 7B the same ledger reads 7.0B against 4.2M (0.06%) against 135.5M (1.9%) - the context extension for under 2% of the parameters, about 52x fewer than full fine-tuning.

```text
The group-shift pattern is the load-bearing piece: no-shift keeps the
reach at one group no matter how deep the model goes, and the
alternating shift is what starts cross-group flow - depth then
finishes the job. The ring's arithmetic is exact (2.22e-16).
```

## Context Distillation - the 241x Serving Contract

Context distillation closes the serving problem: the teacher's doc-conditioned distribution is folded into the student's weights ONCE, and queries stop carrying the document. The stdlib fence trains a tiny student against its teacher for 400 steps at lr 0.35: KL falls 1.2046 -> 0.0272 -> 0.0082 -> 0.0024 - a 500x reduction - and argmax agreement on the doc-dependent probes holds 3/3. (The module's own numpy run traces the same curve further, to 0.0001 - the fence ships its own measurement, the module its own; the shape is the canonical fact.) One classic implementation trap is worth its own line: the weight matrix is consumed COLUMN-wise - a row-wise sweep walks the wrong axis and hands the student a distribution over the wrong vocabulary, which shows up as a negative "KL" and diverging training. The serving contract is the invoice: 1,000 queries over a 12,000-token document pay 12,050,000 prompt tokens on the teacher route and 50,000 on the distilled student - 241.0x fewer.

```text
Context distillation compresses context into weights: train the
student on the teacher's doc-conditioned distribution, then serve
the student - 50,000 prompt tokens where the teacher route pays
12,050,000 (241.0x fewer), with argmax agreement holding 3/3.
```

## Known Failure Modes

| Failure mode | The tell |
| --- | --- |
| stuffing the corpus whole | quality falls to 0.642 of baseline while the bill runs 10.0x the retrieved window - context dilutes, it does not accumulate |
| quoting the advertised window | the 128,000-token spec is 27.6x its 4,637-token effective length at the 95% line - capacity is a spec, quality is a curve |
| one window size for every query class | near queries peak at 9,000 tokens, deep at 64,000 - one size pays both curves and wins neither; +0.1000 waits for the routed split |
| ring attention without the group-shift pattern | no-shift keeps reach at one group at every depth (4/4 forever) - cross-group flow never starts without the alternating shift |
| training all 7B parameters to extend context | LongLoRA's 135.5M (1.9%) buys the same extension - full fine-tune rents about 52x the parameters for the job |
| serving the teacher prompt at query time | 12,050,000 vs 50,000 tokens per 1,000 queries - distill the context into weights, then serve the student |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| answers degrade as the prompt grows | the dilution curve - check the marginals (F1); past the 100k peak the last token is a tax, shrink to the peak |
| "128k context" but needle tasks fail | calibrate to the effective length (F2): plan around 4,637, not 128,000 |
| the monthly bill exploded with prompt size | both ledgers (F3): the token meter scales with window, KV with residency - accuracy per dollar declines strictly |
| latency fine but GPU RAM exhausted | KV residency - 250 GB at a 512k window; route short queries to small windows (F5) |
| the corpus is too long to fine-tune on | ring attention's group shift plus LongLoRA's 1.9% parameter budget (F6) |
| answers change when the doc leaves the prompt | the context was never learned - distill it (F7): 3/3 agreement at 241.0x fewer prompt tokens |

## Quick Reference For

- [Module 6301: Neo4j and Knowledge Graphs](../../phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md) - the structured alternative to stuffing: relations live in the graph and context is assembled per query
- [Module 6302: CAG Long-Context Architectures](../../phases/phase6-rag/6300-context/6302-CAG-Long-Context-Architectures.md) - the cache-and-stuff route this sheet's stuffing bet prices
- [Module 6305: LongLoRA, Ring Attention and Context Distillation](../../phases/phase6-rag/6300-context/6305-LongLoRA-Ring-Attention-and-Context-Distillation.md) - the training-time machinery behind F6 and F7, with the module's own numpy measurements
- [Module 6306: Context Window Economics](../../phases/phase6-rag/6300-context/6306-Context-Window-Economics.md) - the curve model, the two ledgers and the routed campaign in full

## The Canonical Fence

The full stdlib fence below reproduces every number on this page - F1 through F7 - from fixed-seed runs its own asserts pin: no numpy, no wall clock, byte-identical across runs.

```python
"""tick-1020 canonical fence - CHEAT-SHEET-049 Context Engineering.
Stdlib only. Deterministic: fixed-seed random.Random instances, no time,
no set-order dependence. Prints F1..F7 + FENCE-049-OK tail."""
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ---------------- F1: the accuracy product ----------------
DOC_LEN = 100_000   # document tokens
EV_LEN = 200        # evidence span tokens
W_HALF = 64_000     # dilution half-width
Q0 = 0.95           # graded relevance as w -> 0
WINDOWS = [1_000, 2_000, 4_000, 8_000, 16_000, 32_000, 64_000, 100_000, 128_000]

rng = random.Random(7)
positions = [rng.uniform(0, DOC_LEN - EV_LEN) for _ in range(4_000)]


def quality(w):
    return Q0 / (1.0 + w / W_HALF)


def suite_acc(w):
    hits = sum(1 for p in positions if p + EV_LEN <= w)
    return (hits / len(positions)) * quality(w)


print("== F1: the accuracy product P(found) x q(w) ==")
accs = [(w, suite_acc(w)) for w in WINDOWS]
for w, a in accs:
    print(f"w={w:>7,}  q(w)={quality(w):.4f}  acc={a:.4f}")
for i in range(1, len(accs)):
    print(f"marginal {accs[i-1][0]:>7,} -> {accs[i][0]:>7,}: "
          f"{accs[i][1] - accs[i-1][1]:+.4f}")
best_w, best_a = max(accs, key=lambda t: t[1])
assert abs(best_a - 0.3707) < 5e-5 and best_w == 100_000
assert abs((accs[-1][1] - best_a) - (-0.0541)) < 5e-5
print(f"peak: w={best_w:,} acc={best_a:.4f}; "
      f"128k loses {accs[-1][1] - best_a:+.4f} vs peak")
print(f"q(32k)/q(1k) = {quality(32_000) / quality(1_000):.4f}")

# ---------------- F2: effective vs advertised length ----------------
BASE = 99.3    # NoLiMa GPT-4o short-context baseline (%)
S32K = 69.7    # NoLiMa GPT-4o at 32k (%)
a_fit = math.log(BASE / S32K)


def score(w):
    return BASE * math.exp(-a_fit * (w / 32_000))


print("== F2: the NoLiMa calibration ==")
for w in [1_000, 4_000, 8_000, 16_000, 32_000, 64_000, 128_000]:
    print(f"w={w:>7,}  score={score(w):.1f}  ratio={score(w) / BASE:.3f}")
thr = 0.95 * BASE
w95 = 32_000 * math.log(BASE / thr) / a_fit
assert round(w95) == 4_637
print(f"effective length at >=95% baseline ({thr:.1f}): {w95:,.0f} tokens")
print(f"advertised 128,000 vs effective {w95:,.0f} -> gap {128_000 / w95:.1f}x")
print(f"fit check: score(32,000)={score(32_000):.1f} (target {S32K})")

# ---------------- F3: the two-ledger price ----------------
PRICE_LOW = 1.25    # $/M input tokens, prompts <= 200k
PRICE_HIGH = 2.50   # $/M input tokens, prompts > 200k
KV_BYTES_PER_TOKEN = 2 * 32 * 32 * 128 * 2   # 4201: 2 x layers x heads x head_dim x bytes
assert KV_BYTES_PER_TOKEN == 524_288

print("== F3: the two-ledger price of a window ==")
acc_map = {w: suite_acc(w) for w in [1_000, 4_000, 8_000, 16_000, 32_000,
                                     64_000, 100_000, 128_000]}


def price_for(w):
    return PRICE_HIGH if w > 200_000 else PRICE_LOW


def bill_per_1k(w):
    return w * price_for(w) / 1_000_000 * 1_000


ratios = []
for w in [1_000, 4_000, 8_000, 16_000, 32_000, 64_000, 100_000, 128_000,
          256_000, 512_000]:
    a = acc_map.get(w)
    a_txt = f"{a:.4f}" if a is not None else "    --"
    apd = a / bill_per_1k(w) if a is not None else None
    apd_txt = f"{apd:.5f}" if apd is not None else "     --"
    if apd is not None:
        ratios.append(apd)
    kv_gb = w * KV_BYTES_PER_TOKEN / 1024 ** 3
    print(f"w={w:>7,}  ${price_for(w):.2f}/M  bill/1k=${bill_per_1k(w):>8,.2f}"
          f"  KV={kv_gb:>6.1f} GB  acc={a_txt}  acc/$={apd_txt}")
assert all(ratios[i] > ratios[i + 1] for i in range(len(ratios) - 1))
assert abs(ratios[0] - 0.00730) < 5e-6 and abs(ratios[-1] - 0.00198) < 5e-6
print(f"acc/$ monotone decline: {ratios[0]:.5f} -> {ratios[-1]:.5f} "
      f"(all {len(ratios)} acc-bearing rows strictly decreasing)")

# ---------------- F4: the stuffing bet (CAG vs RAG) ----------------
print("== F4: the stuffing bet ==")
CORPUS = 40_000
stuffed_score = score(CORPUS)
stuffed_bill = bill_per_1k(CORPUS)
stuffed_kv = CORPUS * KV_BYTES_PER_TOKEN / 1024 ** 3
rag_w = 4_000
rag_score = score(rag_w)
rag_bill = bill_per_1k(rag_w)
rag_kv = rag_w * KV_BYTES_PER_TOKEN / 1024 ** 3
d95 = 32_000 * math.log(1.0 / 0.95) / a_fit
assert round(d95) == 4_637   # same equation as F2's w95
print(f"corpus stuffed whole: D={CORPUS:,} -> score={stuffed_score:.1f} "
      f"({stuffed_score / BASE:.3f} of baseline)")
print(f"  bill/1k=${stuffed_bill:,.2f}  KV resident={stuffed_kv:.1f} GB")
print(f"retrieval into w={rag_w:,}: score={rag_score:.1f} "
      f"({rag_score / BASE:.3f} of baseline)")
print(f"  bill/1k=${rag_bill:,.2f}  KV resident={rag_kv:.1f} GB")
print(f"bill ratio {stuffed_bill / rag_bill:.1f}x for "
      f"{BASE - stuffed_score - (BASE - rag_score):+.1f} points relative quality")
print(f"break-even corpus at the 95% line: {d95:,.0f} tokens "
      f"(= F2's effective length)")
ANN_MS = 20   # 6202's ANN hop, 10-30 ms band midpoint
print(f"what stuffing buys: the {ANN_MS} ms retrieve hop - cache fixes the "
      f"BILL, never the CURVE")

# ---------------- F5: the routed budget + campaign ----------------
NEAR_HI = 8_000     # near-class evidence lives in [0, 8k]
DEEP_LO, DEEP_HI = 8_000, 64_000
SHARE_NEAR, SHARE_DEEP = 0.70, 0.30
BUDGET = 16_000


def class_acc(w, lo, hi):
    found = max(0.0, min(1.0, (w - EV_LEN - lo) / (hi - lo)))
    return found * quality(w)


print("== F5: the routed budget ==")
one = SHARE_NEAR * class_acc(BUDGET, 0, NEAR_HI) + \
    SHARE_DEEP * class_acc(BUDGET, DEEP_LO, DEEP_HI)
print(f"one-size w={BUDGET:,}: near={class_acc(BUDGET, 0, NEAR_HI):.4f} "
      f"deep={class_acc(BUDGET, DEEP_LO, DEEP_HI):.4f} weighted={one:.4f}")
best = None
for wn in range(2_000, 12_001, 1_000):
    for wd in range(16_000, 65_001, 2_000):
        avg = SHARE_NEAR * wn + SHARE_DEEP * wd
        if avg > BUDGET:
            continue
        acc = SHARE_NEAR * class_acc(wn, 0, NEAR_HI) + \
            SHARE_DEEP * class_acc(wd, DEEP_LO, DEEP_HI)
        if best is None or acc > best[0]:
            best = (acc, wn, wd, avg)
acc_r, wn_r, wd_r, avg_r = best
assert abs(acc_r - 0.6638) < 5e-5 and abs(one - 0.5638) < 5e-5
print(f"routed: w_near={wn_r:,} w_deep={wd_r:,} avg={avg_r:,.0f} "
      f"(budget {BUDGET:,})")
print(f"  near={class_acc(wn_r, 0, NEAR_HI):.4f} "
      f"deep={class_acc(wd_r, DEEP_LO, DEEP_HI):.4f} weighted={acc_r:.4f}")
print(f"gain at equal budget: {acc_r - one:+.4f}")
near_peak = max(((w, class_acc(w, 0, NEAR_HI))
                 for w in range(1_000, 65_001, 1_000)), key=lambda t: t[1])
deep_peak = max(((w, class_acc(w, DEEP_LO, DEEP_HI))
                 for w in range(1_000, 65_001, 1_000)), key=lambda t: t[1])
print(f"per-class peaks: near w*={near_peak[0]:,} acc={near_peak[1]:.4f}; "
      f"deep w*={deep_peak[0]:,} acc={deep_peak[1]:.4f}")

Q_MONTH = 300_000        # queries per month
VALUE = 0.05             # $ value per correct answer


def cost(w):
    return w * (PRICE_HIGH if w > 200_000 else PRICE_LOW) / 1_000_000


print("-- the month campaign --")
nets = []
for name, wn, wd in [("A max-window 128k", 128_000, 128_000),
                     ("B one-size 16k", 16_000, 16_000),
                     ("C routed 9k/32k", 9_000, 32_000)]:
    acc = SHARE_NEAR * class_acc(wn, 0, NEAR_HI) + \
        SHARE_DEEP * class_acc(wd, DEEP_LO, DEEP_HI)
    avg_w = SHARE_NEAR * wn + SHARE_DEEP * wd
    bill = Q_MONTH * (SHARE_NEAR * cost(wn) + SHARE_DEEP * cost(wd))
    value = Q_MONTH * acc * VALUE
    nets.append(value - bill)
    print(f"{name}: avg_w={avg_w:,.0f} acc={acc:.4f} bill=${bill:,.2f} "
          f"value=${value:,.2f} net=${value - bill:+,.2f}")
assert abs(nets[0] - (-43_250.00)) < 0.005
assert abs(nets[1] - 2_456.36) < 0.005
assert abs(nets[2] - 3_993.96) < 0.005
print("tier check: every routed window <= 200k -> the $2.50 tier never fires")

# ---------------- F6: the training-side ceiling ----------------
print("== F6: ring attention, the shift, and the parameter ledger ==")
N6, G6 = 16, 4
shift = G6 // 2
part_plain = [j // G6 for j in range(N6)]
part_shift = [((j + shift) % N6) // G6 for j in range(N6)]
alt_parts = [part_plain, part_shift]   # alternating layers


def reach(layers, parts):
    R = [frozenset([j]) for j in range(N6)]
    for l in range(layers):
        part = parts[l % len(parts)]
        R = [frozenset().union(*[R[k] for k in range(N6)
                                 if part[k] == part[j]])
             for j in range(N6)]
    return R


walk = []
for L in (1, 2, 3, 4, 6):
    rn = reach(L, [part_plain])
    ra = reach(L, alt_parts)
    walk.append(min(map(len, ra)))
    assert min(map(len, rn)) == 4 and max(map(len, rn)) == 4
    print(f"L={L}: no-shift reach {min(map(len, rn))}/{max(map(len, rn))}"
          f" | alternating reach {min(map(len, ra))}/{max(map(len, ra))}")
assert walk == [4, 8, 12, 16, 16]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


P6, nq, d = 4, 4, 4
Nr = P6 * nq
rng6 = random.Random(7)
Q6 = [[[rng6.gauss(0.0, 1.0) for _ in range(d)] for _ in range(nq)]
      for _ in range(P6)]
K6 = [[[rng6.gauss(0.0, 1.0) for _ in range(d)] for _ in range(nq)]
      for _ in range(P6)]
V6 = [[[rng6.gauss(0.0, 1.0) for _ in range(d)] for _ in range(nq)]
      for _ in range(P6)]


def softmax(v):
    m = max(v)
    e = [math.exp(x - m) for x in v]
    s = sum(e)
    return [x / s for x in e]


Qf = [q for blk in Q6 for q in blk]
Kf = [k for blk in K6 for k in blk]
Vf = [v for blk in V6 for v in blk]
full = []
for i in range(Nr):
    w = softmax([dot(Qf[i], Kf[j]) / math.sqrt(d) for j in range(Nr)])
    full.append([sum(w[j] * Vf[j][k] for j in range(Nr)) for k in range(d)])

# ring: online softmax - running max m and denominator l carried across steps
out = [[0.0] * d for _ in range(Nr)]
m_run = [float("-inf")] * Nr
l_run = [0.0] * Nr
for t in range(P6):
    for p in range(P6):
        src = (p - t) % P6
        rows = range(p * nq, (p + 1) * nq)
        for ii, i in enumerate(rows):
            s = [dot(Q6[p][ii], kv) / math.sqrt(d) for kv in K6[src]]
            nm = max(m_run[i], max(s))
            old = math.exp(m_run[i] - nm)
            new = [math.exp(x - nm) for x in s]
            l_run[i] = l_run[i] * old + sum(new)
            for k in range(d):
                out[i][k] = out[i][k] * old + \
                    sum(new[jj] * V6[src][jj][k] for jj in range(nq))
            m_run[i] = nm
ring = [[out[i][k] / l_run[i] for k in range(d)] for i in range(Nr)]
diff = max(abs(full[i][k] - ring[i][k]) for i in range(Nr) for k in range(d))
assert diff < 1e-12
print(f"ring == full: True (4 devices x 4 tokens, 4 rotations) "
      f"max|diff| = {diff:.2e}")
print(f"KV per device: {nq}/{Nr} tokens ({Nr / nq:.1f}x less); "
      f"softmax cells: {nq * nq} vs {Nr * Nr} ({Nr * Nr // (nq * nq)}.0x less)")

Nc, Pc, gc = 65_536, 8, 8_192
print(f"softmax cells: full {Nc ** 2:,} ({Nc ** 2 * 4 / 1e9:.1f} GB) | "
      f"S2 {Nc * gc:,} ({Nc * gc / Nc ** 2:.3f}x) | "
      f"ring block/step {(Nc // Pc) ** 2:,} "
      f"({Nc ** 2 // (Nc // Pc) ** 2}x less per materialization), "
      f"KV/device {Nc // Pc:,} ({Pc}x less)")

Ll, dd, rr, voc, nl = 2, 16, 2, 32, 2
embed = voc * dd
per_layer = 4 * dd * dd + 2 * dd * (4 * dd)
norms = Ll * 2 * dd
toy_full = embed + Ll * per_layer + norms
toy_lora = Ll * 2 * (2 * rr * dd)
toy_plus = toy_lora + embed + norms
assert (toy_full, toy_lora, toy_plus) == (6_720, 256, 832)
print(f"toy ledger: full {toy_full} ({100 * toy_full / toy_full:.1f}%) | "
      f"LoRA-only {toy_lora} ({100 * toy_lora / toy_full:.1f}%) | "
      f"LongLoRA(+embed+norm) {toy_plus} "
      f"({100 * toy_plus / toy_full:.1f}%)")

Ll, dd, rr, voc, nl = 32, 4096, 8, 32000, 2
D7 = 7.0e9
lora7 = Ll * 2 * 2 * rr * dd
plus7 = lora7 + voc * dd + Ll * nl * dd
assert round(plus7 / 1e5) == 1_355
print(f"7B ledger: full {D7 / 1e9:.1f}B | LoRA-only {lora7 / 1e6:.1f}M "
      f"({100 * lora7 / D7:.2f}%) | LongLoRA {plus7 / 1e6:.1f}M "
      f"({100 * plus7 / D7:.1f}%)")

# ---------------- F7: the distilled prompt ----------------
print("== F7: context distillation ==")
dv, voc, nprobe, steps, lr = 6, 6, 3, 400, 0.35
rng7 = random.Random(11)
u = [rng7.gauss(0.0, 1.0) for _ in range(dv)]
Qp = [[rng7.gauss(0.0, 1.0) for _ in range(dv)] for _ in range(nprobe)]
W_T = [[rng7.gauss(0.0, 0.5) for _ in range(voc)] for _ in range(2 * dv)]
W_S = [[rng7.gauss(0.0, 0.5) for _ in range(voc)] for _ in range(dv)]


def softmax7(v):
    m = max(v)
    e = [math.exp(x - m) for x in v]
    s = sum(e)
    return [x / s for x in e]


def teacher(q):
    # W_T is (2*dv x voc): the (2*dv)-dim fused input hits each COLUMN,
    # not each row - the row form walks W_T's 12 rows and returns a
    # 12-vector, which is no distribution over the 6 vocab classes.
    return softmax7([dot(q + u, col) for col in zip(*W_T)])


def student(q):
    return softmax7([dot(q, col) for col in zip(*W_S)])


T = [teacher(q) for q in Qp]
kl_curve = []
for step in range(steps):
    total = 0.0
    grad = [[0.0] * voc for _ in range(dv)]
    for i in range(nprobe):
        s = student(Qp[i])
        total += sum(T[i][k] * (math.log(T[i][k] + 1e-12) -
                                math.log(s[k] + 1e-12)) for k in range(voc))
        for r in range(dv):
            for c in range(voc):
                grad[r][c] += Qp[i][r] * (s[c] - T[i][c])
    for r in range(dv):
        for c in range(voc):
            W_S[r][c] -= lr * grad[r][c] / nprobe
    if step in (0, 99, 199, 399):
        kl_curve.append(total / nprobe)
        print(f"step {step + 1}: KL = {total / nprobe:.4f}")
assert kl_curve[-1] < 0.005  # a 500x reduction in 400 steps
assert kl_curve[-1] < kl_curve[1] / 2.0 < kl_curve[0] / 2.0
agree = sum(1 for q, t in zip(Qp, T)
            if student(q).index(max(student(q))) == t.index(max(t)))
assert agree == 3
print(f"argmax agreement on doc-dependent probes: {agree}/{nprobe}")
doc_t, q_t, n_q = 12_000, 50, 1_000
teacher_tokens = n_q * (doc_t + q_t)
distilled_tokens = n_q * q_t
print(f"prompt tokens: teacher {teacher_tokens:,} vs distilled "
      f"{distilled_tokens:,} ({teacher_tokens / distilled_tokens:.1f}x fewer)")

print("FENCE-049-OK")
```

Its frozen output:

```text
== F1: the accuracy product P(found) x q(w) ==
w=  1,000  q(w)=0.9354  acc=0.0091
w=  2,000  q(w)=0.9212  acc=0.0184
w=  4,000  q(w)=0.8941  acc=0.0344
w=  8,000  q(w)=0.8444  acc=0.0688
w= 16,000  q(w)=0.7600  acc=0.1258
w= 32,000  q(w)=0.6333  acc=0.2092
w= 64,000  q(w)=0.4750  acc=0.3061
w=100,000  q(w)=0.3707  acc=0.3707
w=128,000  q(w)=0.3167  acc=0.3167
marginal   1,000 ->   2,000: +0.0093
marginal   2,000 ->   4,000: +0.0160
marginal   4,000 ->   8,000: +0.0344
marginal   8,000 ->  16,000: +0.0570
marginal  16,000 ->  32,000: +0.0834
marginal  32,000 ->  64,000: +0.0970
marginal  64,000 -> 100,000: +0.0646
marginal 100,000 -> 128,000: -0.0541
peak: w=100,000 acc=0.3707; 128k loses -0.0541 vs peak
q(32k)/q(1k) = 0.6771
== F2: the NoLiMa calibration ==
w=  1,000  score=98.2  ratio=0.989
w=  4,000  score=95.0  ratio=0.957
w=  8,000  score=90.9  ratio=0.915
w= 16,000  score=83.2  ratio=0.838
w= 32,000  score=69.7  ratio=0.702
w= 64,000  score=48.9  ratio=0.493
w=128,000  score=24.1  ratio=0.243
effective length at >=95% baseline (94.3): 4,637 tokens
advertised 128,000 vs effective 4,637 -> gap 27.6x
fit check: score(32,000)=69.7 (target 69.7)
== F3: the two-ledger price of a window ==
w=  1,000  $1.25/M  bill/1k=$    1.25  KV=   0.5 GB  acc=0.0091  acc/$=0.00730
w=  4,000  $1.25/M  bill/1k=$    5.00  KV=   2.0 GB  acc=0.0344  acc/$=0.00688
w=  8,000  $1.25/M  bill/1k=$   10.00  KV=   3.9 GB  acc=0.0688  acc/$=0.00688
w= 16,000  $1.25/M  bill/1k=$   20.00  KV=   7.8 GB  acc=0.1258  acc/$=0.00629
w= 32,000  $1.25/M  bill/1k=$   40.00  KV=  15.6 GB  acc=0.2092  acc/$=0.00523
w= 64,000  $1.25/M  bill/1k=$   80.00  KV=  31.2 GB  acc=0.3061  acc/$=0.00383
w=100,000  $1.25/M  bill/1k=$  125.00  KV=  48.8 GB  acc=0.3707  acc/$=0.00297
w=128,000  $1.25/M  bill/1k=$  160.00  KV=  62.5 GB  acc=0.3167  acc/$=0.00198
w=256,000  $2.50/M  bill/1k=$  640.00  KV= 125.0 GB  acc=    --  acc/$=     --
w=512,000  $2.50/M  bill/1k=$1,280.00  KV= 250.0 GB  acc=    --  acc/$=     --
acc/$ monotone decline: 0.00730 -> 0.00198 (all 8 acc-bearing rows strictly decreasing)
== F4: the stuffing bet ==
corpus stuffed whole: D=40,000 -> score=63.8 (0.642 of baseline)
  bill/1k=$50.00  KV resident=19.5 GB
retrieval into w=4,000: score=95.0 (0.957 of baseline)
  bill/1k=$5.00  KV resident=2.0 GB
bill ratio 10.0x for +31.2 points relative quality
break-even corpus at the 95% line: 4,637 tokens (= F2's effective length)
what stuffing buys: the 20 ms retrieve hop - cache fixes the BILL, never the CURVE
== F5: the routed budget ==
one-size w=16,000: near=0.7600 deep=0.1059 weighted=0.5638
routed: w_near=9,000 w_deep=32,000 avg=15,900 (budget 16,000)
  near=0.8329 deep=0.2692 weighted=0.6638
gain at equal budget: +0.1000
per-class peaks: near w*=9,000 acc=0.8329; deep w*=64,000 acc=0.4733
-- the month campaign --
A max-window 128k: avg_w=128,000 acc=0.3167 bill=$48,000.00 value=$4,750.00 net=$-43,250.00
B one-size 16k: avg_w=16,000 acc=0.5638 bill=$6,000.00 value=$8,456.36 net=$+2,456.36
C routed 9k/32k: avg_w=15,900 acc=0.6638 bill=$5,962.50 value=$9,956.46 net=$+3,993.96
tier check: every routed window <= 200k -> the $2.50 tier never fires
== F6: ring attention, the shift, and the parameter ledger ==
L=1: no-shift reach 4/4 | alternating reach 4/4
L=2: no-shift reach 4/4 | alternating reach 8/8
L=3: no-shift reach 4/4 | alternating reach 12/12
L=4: no-shift reach 4/4 | alternating reach 16/16
L=6: no-shift reach 4/4 | alternating reach 16/16
ring == full: True (4 devices x 4 tokens, 4 rotations) max|diff| = 2.22e-16
KV per device: 4/16 tokens (4.0x less); softmax cells: 16 vs 256 (16.0x less)
softmax cells: full 4,294,967,296 (17.2 GB) | S2 536,870,912 (0.125x) | ring block/step 67,108,864 (64x less per materialization), KV/device 8,192 (8x less)
toy ledger: full 6720 (100.0%) | LoRA-only 256 (3.8%) | LongLoRA(+embed+norm) 832 (12.4%)
7B ledger: full 7.0B | LoRA-only 4.2M (0.06%) | LongLoRA 135.5M (1.9%)
== F7: context distillation ==
step 1: KL = 1.2046
step 100: KL = 0.0272
step 200: KL = 0.0082
step 400: KL = 0.0024
argmax agreement on doc-dependent probes: 3/3
prompt tokens: teacher 12,050,000 vs distilled 50,000 (241.0x fewer)
FENCE-049-OK
```
