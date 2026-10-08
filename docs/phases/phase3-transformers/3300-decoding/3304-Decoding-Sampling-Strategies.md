---
Document ID: 3304
Title: "3304: Decoding Sampling Strategies - Temperature, Top-k, Nucleus, Min-p, and Typical-p"
Phase: 3
Module: 3300
Last Updated: 2026-10-07
Status: Complete
Difficulty: Intermediate
Estimated Time: 2 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'inference', 'vllm']
---

# 3304: Decoding Sampling Strategies - Temperature, Top-k, Nucleus, Min-p, and Typical-p

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Sampler Stack and Who Owns What](#the-sampler-stack-and-who-owns-what)
- [Temperature Reshapes, It Does Not Reorder](#temperature-reshapes-it-does-not-reorder)
- [Top-k Truncates by Rank, Blind to Mass](#top-k-truncates-by-rank-blind-to-mass)
- [Nucleus Truncates by Mass, and Never Empties](#nucleus-truncates-by-mass-and-never-empties)
- [Min-p Adapts to Shape; Typical-p Drops the Boring Winner](#min-p-adapts-to-shape-typical-p-drops-the-boring-winner)
- [The Stack: Order Is the Mechanism](#the-stack-order-is-the-mechanism)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Abstract
The module named "decoding" teaches zero decoding strategies. Every sampling question in its QUIZ leans outward - Q3-7 and 13-15 point at 1402's production config literals, Q1-2, 8-12, 20 at 3401's search, Q16 at 4202, Q17-19 at 4201 - and the corpus nowhere explains what the knobs do: `min_p`, `typical_p`, and the word "nucleus" appear NOWHERE in the corpus, not even as config literals, and `top_p` appears only as a bare `SamplingParams(top_p=0.9)` whose mechanics no lesson owns. This lesson owns the truncation samplers themselves as working code: temperature's reshape (entropy 0.2128 to 1.8191 nats with the argmax never moving), top-k's rank-blindness (the k=1 set keeps 0.4995 and ignores 0.2244), nucleus's mass budget and its never-empty guarantee (p=0.01 still keeps one token), min-p's shape-adaptive threshold against typical-p's entropy-matching (which drops the top token and keeps two smaller ones), and the production stack where the first truncation wins (the default config's cut of 0.4196 on the flat shape is the top-k cut - top_p never fires).

---

## Learning Objectives

After completing this lesson, you will be able to:

- State what temperature does mechanically - `softmax(z/T)` rescales the logits, entropy climbs monotonically (0.2128 to 1.8191 nats over T=0.25 to 2.00), p_top falls (0.9530 to 0.3101), and the argmax never moves: temperature is shape control, not re-ranking
- Implement top-k truncation and name its blindness - rank decides and mass is ignored, so the k=1 set keeps 0.4995 while a 0.2244-mass runner-up sits untouched in the discard pile
- Implement nucleus sampling as "the smallest set of most probable tokens whose probabilities add up to `top_p` or higher" and prove the set never empties - even top_p=0.01 keeps the single top token (this is `min_tokens_to_keep=1` in the warper signature)
- Contrast min-p's shape-adaptive threshold (`min_p x p_max`: 0.0500 on the peaked shape keeps 4 of 8, 0.0153 on the flat shape keeps all 8) with typical-p's entropy-matching, which ranks by |info - H| and can drop the top token while two smaller ones close the budget
- Compose the stack in the HF warper order (temperature, then top_k, then top_p, then min_p, then typical_p - generation/utils.py L1591-1619) and read a 3x3 config/shape table, including the row where the top_k cut removes 0.4196 of mass and top_p never fires
- Map every QUIZ sampling question to the knob it actually tests, and know which of temperature/top-k/top-p/min-p/typical-p each production default exercises

---

## The Sampler Stack and Who Owns What

Every token a decoder emits passes through the same pipeline: raw logits, then temperature, then zero or more truncation rules, then renormalization and one draw. The pipeline lives in every serving stack - Hugging Face calls its stages "logits warpers" and applies them in a fixed order; vLLM calls the config object `SamplingParams`. The knobs are the same. What no lesson in this corpus teaches is what each knob does to the distribution.

The boundary, owned honestly:

- [3401: Encoder-Decoder Architectures](../3400-architectures/3401-Encoder-Decoder-Architectures.md) owns sequence-level SEARCH - greedy vs beam - where the unit of decision is the whole output sequence. This lesson owns the per-token sampler beam search samples through.
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) owns the production CONFIG surface - `SamplingParams(top_p=0.9)` as a literal. This lesson owns the mechanics that literal invokes.
- [4201: Context Window Physics](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md) owns the decode-step physics (KV cache) that makes each sampler step cost what it costs.
- [4202: Speculative Decoding](../../phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md) owns the speed technique that runs a draft sampler ahead of the verifier - a sampling consumer, not a sampler.
- [5206: Best-of-N and Rejection Sampling](../../phase5-finetuning/5200-alignment/5206-Best-of-N-and-Rejection-Sampling.md) owns sampling as a TRAINING data engine - the pool that temperature widens is its raw material, consumed N at a time.
- [7505: Temperature Zero and Deterministic Security Testing](../../phase7-agentic/7500-security/7505-Temperature-Zero-and-Deterministic-Security-Testing.md) owns what T=0 guarantees (determinism) and what it does not.
- **3304 owns the sampler math** - what each knob does to the distribution, in what order, with which invariant.

The same knob, different silences across stacks (live-verified 2026-10-07):

| Parameter | HF GenerationConfig default | vLLM SamplingParams default |
|-----------|------------------------------|------------------------------|
| temperature | 1.0 | 1.0 |
| top_k | 50 | 0 (off) |
| top_p | 1.0 (off) | 1.0 (off) |
| min_p | unset | 0.0 (off) |
| typical_p | unset (HF docs link 2202.00666) | not exposed |

Note the trap: HF's top_k defaults to 50 (a truncation is ON by default), while vLLM's defaults to 0 (off). Reading a vLLM config through HF eyes, or vice versa, silently changes what the sampler keeps.

---

## Temperature Reshapes, It Does Not Reorder

Temperature divides the logits before the softmax: `softmax(z/T)`. Small T sharpens the distribution toward its mode; large T flattens it toward uniform. The one thing it never does is change the ORDER of the tokens - dividing by a positive constant preserves rank, so the argmax is invariant at every temperature.

```python
import math

TOK = ["the", "a", "model", "runs", "fast", "on", "GPU", "day"]
LOGITS = [4.0, 3.2, 2.8, 2.0, 1.2, 0.5, 0.0, -1.0]

def softmax(logits, T):
    scaled = [x / T for x in logits]
    m = max(scaled)
    ex = [math.exp(x - m) for x in scaled]
    Z = sum(ex)
    return [e / Z for e in ex]

def entropy(p):
    return -sum(pi * math.log(pi) for pi in p if pi > 0.0)

base_p = softmax(LOGITS, 1.0)
print("base probs (T=1.00): " + " ".join(f"{x:.4f}" for x in base_p))
print(f"base entropy: {entropy(base_p):.4f} nats")
print()
print("T      p_top    H(nats)  p1/p2   argmax")
top = LOGITS.index(max(LOGITS))
for T in (0.25, 0.50, 1.00, 2.00):
    p = softmax(LOGITS, T)
    order = sorted(range(len(p)), key=lambda i: -p[i])
    ratio = p[order[0]] / p[order[1]]
    flag = "same" if order[0] == top else "MOVED"
    print(f"{T:.2f}  {p[top]:.4f}  {entropy(p):.4f}  {ratio:.3f}   {TOK[top]} ({flag})")
```

Reading the walk: at T=0.25 the top token holds 0.9530 of the mass and the entropy has collapsed to 0.2128 nats - sampling is greedy in all but name (the runner-up is 24.533x behind). At T=2.00 the top holds only 0.3101 and the entropy has grown to 1.8191 nats, with the runner-up just 1.492x behind. Entropy rises monotonically with T and p_top falls monotonically - the walk has exactly two moving parts - and the argmax column reads `the (same)` at every temperature. This is the mechanical content of [7505](../../phase7-agentic/7500-security/7505-Temperature-Zero-and-Deterministic-Security-Testing.md)'s determinism claim: T=0 is the T=0.25 row's limit, where p_top reaches 1.0 and unique outputs reach 1. Temperature changes how BROAD the samplers choices are; dethroning the top token needs a truncation rule that removes it, and no temperature does that.

---

## Top-k Truncates by Rank, Blind to Mass

Top-k keeps the k highest-probability tokens and renormalizes over them. The rule looks at exactly one thing: RANK. It never looks at how much probability mass it keeps or discards - which means the same k is generous on a peaked shape and starved on a flat one, and the discarded pile can hold serious mass.

```python
import math

TOK = ["the", "a", "model", "runs", "fast", "on", "GPU", "day"]
LOGITS = [4.0, 3.2, 2.8, 2.0, 1.2, 0.5, 0.0, -1.0]

def softmax(logits, T):
    scaled = [x / T for x in logits]
    m = max(scaled)
    ex = [math.exp(x - m) for x in scaled]
    Z = sum(ex)
    return [e / Z for e in ex]

P = softmax(LOGITS, 1.0)
order = sorted(range(len(P)), key=lambda i: -P[i])
print("probs sorted desc: " + " ".join(f"{P[i]:.4f}" for i in order))
print()
print("k    kept set              kept mass   dropped-max")
for k in (1, 2, 3, 5, 8):
    keep = order[:k]
    kept = sum(P[i] for i in keep)
    dropped = [P[i] for i in order[k:]]
    dmax = max(dropped) if dropped else 0.0
    names = [TOK[i] for i in keep]
    print(f"{k}    {str(names):<20}  {kept:.4f}    {dmax:.4f}")
print()
print("k=1 is greedy: sampling from the k=1 set always returns "
      f"'{TOK[order[0]]}' (p=1.0 after renorm)")
```

Reading the table: k=1 keeps 0.4995 of the mass and its largest discard is a 0.2244 runner-up - sampling from the k=1 set is exactly greedy search (the renormalized probability is 1.0), which is why the twoQUIZ buckets that lean on 3401's greedy-vs-beam split are answered by a truncation parameter in production. k=5 keeps 0.9724; the full set keeps 1.0000. The `dropped-max` column is the blindness made visible: the rule never asked what it was throwing away, only where the cutoff rank sat. On this peaked shape the cut is cheap. The stack section below shows the same k=4 doing 0.4196 of damage on a flat shape.

---

## Nucleus Truncates by Mass, and Never Empties

Nucleus sampling (top-p) flips the criterion from rank to mass: keep the SMALLEST set of most-probable tokens whose probabilities add up to `top_p` OR HIGHER. The definition is worth reading twice - the set stops at the first prefix that CROSSES the budget, so the kept mass is always at least top_p, never exactly it.

```python
import math

TOK = ["the", "a", "model", "runs", "fast", "on", "GPU", "day"]
LOGITS = [4.0, 3.2, 2.8, 2.0, 1.2, 0.5, 0.0, -1.0]

def softmax(logits, T):
    scaled = [x / T for x in logits]
    m = max(scaled)
    ex = [math.exp(x - m) for x in scaled]
    Z = sum(ex)
    return [e / Z for e in ex]

def nucleus(p, top_p):
    order = sorted(range(len(p)), key=lambda i: -p[i])
    keep, cum = [], 0.0
    for i in order:
        keep.append(i)
        cum += p[i]
        if cum >= top_p:
            break
    return keep, cum

P = softmax(LOGITS, 1.0)
order = sorted(range(len(P)), key=lambda i: -P[i])
print("p      kept set              kept mass")
for tp in (0.50, 0.90, 0.95, 0.99, 0.01):
    keep, cum = nucleus(P, tp)
    names = [TOK[i] for i in keep]
    print(f"{tp:.2f}  {str(names):<20}  {cum:.4f}")
print()
print(f"top_p=0.01 < p_top: the set NEVER empties - the single top token")
print(f"({TOK[order[0]]}, p={P[order[0]]:.4f}) already adds up to 0.01 or higher.")
print("this is min_tokens_to_keep=1 in the HF warper signature.")
```

Reading the table: p=0.50 keeps TWO tokens and 0.7240 of mass - the first token alone was 0.4995, short of the budget, so the rule had to take the runner-up and overshot to 0.7240. Every row's kept mass exceeds its budget for the same reason. p=0.90 settles at four tokens and 0.9420 - the canonical "top_p=0.9" of every production config, now with actual contents. And the last row is the structural guarantee: set top_p=0.01, far below the top token's own probability, and the set still contains exactly one token - it CANNOT be empty, because the first token already "adds up to 0.01 or higher". Hugging Face's warpers carry this as an explicit `min_tokens_to_keep` parameter; the never-empty property is the contract, not an accident.

---

## Min-p Adapts to Shape; Typical-p Drops the Boring Winner

Top-k and nucleus share a flaw: both are shape-blind. Top-k always keeps k; nucleus always spends the same budget. Min-p truncates by RATIO instead: a token survives if `p_i >= min_p x p_max`. When the model is confident (peaked), the threshold is high and the set tight; when the model is unsure (flat), the threshold drops and the set opens - the truncation adapts to the model's own confidence, which is exactly the property [Nguyen et al.](https://arxiv.org/abs/2407.01082) formalized for sampling at high temperature.

```python
import math

TOK = ["the", "a", "model", "runs", "fast", "on", "GPU", "day"]
LOGITS = [4.0, 3.2, 2.8, 2.0, 1.2, 0.5, 0.0, -1.0]
FLAT = [1.10, 1.05, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70]

def softmax(logits, T):
    scaled = [x / T for x in logits]
    m = max(scaled)
    ex = [math.exp(x - m) for x in scaled]
    Z = sum(ex)
    return [e / Z for e in ex]

def entropy(p):
    return -sum(pi * math.log(pi) for pi in p if pi > 0.0)

def nucleus(p, top_p):
    order = sorted(range(len(p)), key=lambda i: -p[i])
    keep, cum = [], 0.0
    for i in order:
        keep.append(i)
        cum += p[i]
        if cum >= top_p:
            break
    return keep, cum

P = softmax(LOGITS, 1.0)
flat_p = softmax(FLAT, 1.0)
print("-- min_p=0.10 on two shapes: threshold = min_p * p_max --")
for label, probs in (("peaked", P), ("flat  ", flat_p)):
    pmax = max(probs)
    thr = 0.10 * pmax
    keep = [i for i in range(len(probs)) if probs[i] >= thr]
    print(f"{label}: p_max={pmax:.4f}  threshold={thr:.4f}  kept={len(keep)}/8"
          f"  kept mass={sum(probs[i] for i in keep):.4f}")
print()
print("-- nucleus vs typical on an engineered three-peak distribution --")
PROBS3 = [0.35, 0.30, 0.28, 0.03, 0.02, 0.01, 0.007, 0.003]
H3 = entropy(PROBS3)
print("probs: " + " ".join(f"{x:.3f}" for x in PROBS3) + f"   H={H3:.4f} nats")
nkeep, ncum = nucleus(PROBS3, 0.35)
print(f"nucleus 0.35:  {[TOK[i] for i in nkeep]}  (cum {ncum:.2f})")
info = [-math.log(pi) for pi in PROBS3]
torder = sorted(range(len(PROBS3)), key=lambda i: abs(info[i] - H3))
tkeep, tcum = [], 0.0
for i in torder:
    tkeep.append(i)
    tcum += PROBS3[i]
    if tcum >= 0.35:
        break
print("typical ranks by |info - H|: " +
      " ".join(f"{TOK[i]}(|{abs(info[i]-H3):.4f}|)" for i in torder[:4]) + " ...")
print(f"typical 0.35:  {[TOK[i] for i in tkeep]}  (cum {tcum:.2f})")
print(f"the top token ({TOK[0]}, info {info[0]:.4f}) sits |{abs(info[0]-H3):.4f}| from H -")
print("two smaller tokens close the budget first, so typical drops the winner.")
```

The min-p block is the adaptivity headline: the SAME min_p=0.10 produces a 0.0500 threshold on the peaked shape (4 of 8 survive) and a 0.0153 threshold on the flat shape (all 8 survive). A fixed top-k or top-p cannot do this - their criteria never consult p_max. HF's own docs suggest "typical values are in the 0.01-0.2 range" for min_p, and vLLM carries the parameter with the same ratio semantics.

The second block is typical-p, and it is the strangest of the family. [Meister et al.](https://arxiv.org/abs/2202.00666) observed that humans communicate at an information rate near the conditional entropy H, so a good next token should carry an information content -log p close to H. Typical-p ranks tokens by that distance |info - H| and takes the smallest set crossing the mass budget - the same budget mechanics as nucleus, a completely different ORDER. On the engineered three-peak distribution the two rules disagree at the same 0.35 budget: nucleus keeps `['the']` - the biggest token alone (0.35 reaches the budget on its own) - while typical's ranking puts model(|0.0937|) and a(|0.1627|) ahead of the(|0.3169|), and those two close the budget at 0.58 before the top token is ever reached: typical keeps `['model', 'a']` and DROPS the winner. The top token is "boring" - its 1.0498 nats of information are 0.3169 away from the expected 1.3667 - and typical-p exists to skip boring. This is the mechanism behind Meister et al.'s headline result that locally typical sampling "consistently reduce[s] degenerate repetitions" against nucleus and top-k: repetitive text is over-confident, over-confident tokens are far from H, and typical-p prices them out.

---

## The Stack: Order Is the Mechanism

Production never runs one knob. Hugging Face applies its warpers in a fixed sequence - temperature, then top_k, then top_p, then min_p, then typical_p (with epsilon/eta and the newer top_h around them) at src/transformers/generation/utils.py L1591-1619 - and each stage renormalizes over the survivors of the previous one. The order is not a detail: each truncation sees only what earlier truncations left it, so the FIRST rule that cuts determines what later rules can even consider.

```python
import math
import random

TOK = ["the", "a", "model", "runs", "fast", "on", "GPU", "day"]
LOGITS = [4.0, 3.2, 2.8, 2.0, 1.2, 0.5, 0.0, -1.0]
FLAT = [1.10, 1.05, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70]
BIMOD = [4.0, 3.8, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]
SHAPES = {"peaked": LOGITS, "flat": FLAT, "bimodal": BIMOD}
CFGS = [("default T0.7 k4 p0.9", 0.7, 4, 0.90, 0.0),
        ("highT1.3 minp0.05  ", 1.3, 0, 1.0, 0.05),
        ("lowT0.2  p0.50     ", 0.2, 0, 0.50, 0.0)]

def softmax(logits, T):
    scaled = [x / T for x in logits]
    m = max(scaled)
    ex = [math.exp(x - m) for x in scaled]
    Z = sum(ex)
    return [e / Z for e in ex]

def nucleus(p, top_p):
    order = sorted(range(len(p)), key=lambda i: -p[i])
    keep, cum = [], 0.0
    for i in order:
        keep.append(i)
        cum += p[i]
        if cum >= top_p:
            break
    return keep, cum

def stack_apply(logits, T, k, top_p, min_p):
    p = softmax(logits, T)
    order = sorted(range(len(p)), key=lambda i: -p[i])
    if k > 0:
        keep = order[:k]
        p = [p[i] if i in keep else 0.0 for i in range(len(p))]
    if top_p < 1.0:
        keep, _ = nucleus(p, top_p)
        p = [p[i] if i in keep else 0.0 for i in range(len(p))]
    if min_p > 0.0:
        thr = min_p * max(p)
        p = [pi if pi >= thr else 0.0 for pi in p]
    cut = 1.0 - sum(p)
    Z = sum(p)
    return [pi / Z for pi in p], cut

def sample_counts(p, n=2000):
    r = random.Random(1234)
    total = sum(p)
    counts = [0] * len(p)
    for _ in range(n):
        u = r.random() * total
        c = 0.0
        for i, pi in enumerate(p):
            c += pi
            if c >= u:
                counts[i] += 1
                break
    return counts

print("HF order (generation/utils.py L1591-1619): T -> top_h -> top_k ->")
print("top_p -> min_p -> typical_p -> epsilon -> eta")
print()
print(f"{'config':<20} {'shape':<9} kept  cut-mass  uniq/2000  top-share")
for label, T, k, tp, mp in CFGS:
    for sname, sL in SHAPES.items():
        q, cut = stack_apply(sL, T, k, tp, mp)
        keep_n = sum(1 for x in q if x > 0)
        counts = sample_counts(q, 2000)
        uniq = sum(1 for c in counts if c > 0)
        share = max(counts) / 2000.0
        print(f"{label:<20} {sname:<9} {keep_n:>4}  {cut:>8.4f}  {uniq:>9}  {share:.4f}")
print()
print("read the table: lowT0.2/p0.50 collapses to 1 token on peaked AND bimodal")
print("(top-share 1.0000, near-greedy); highT1.3+minp0.05 stays 6/8 wide on")
print("peaked with top-share 0.4090 vs default's 0.6635; and the default's")
print("cut-mass 0.4196 on flat is the top_k=4 cut - top_p never fired (the")
print("kept four sum to 0.5806 < 0.90), first truncation in the stack wins.")
```

Three readings, one per row family. The `lowT0.2/p0.50` rows are greedy in disguise: after T=0.2 sharpens the distribution, the single top token already crosses the 0.50 budget, so kept=1 and 2,000 draws produce ONE unique token (top-share 1.0000) on peaked and bimodal - [7505](../../phase7-agentic/7500-security/7505-Temperature-Zero-and-Deterministic-Security-Testing.md)'s determinism, purchased with config knobs instead of T=0. The `highT1.3+minp0.05` rows are min-p's whole pitch: at an aggressive temperature the peaked shape still keeps 6 of 8 tokens with top-share down to 0.4090 (from the default's 0.6635) - diversity WITHOUT the incoherence tail, because the truncation scales with the model's confidence instead of ignoring it. And the `default` row on flat is the order lesson: its cut-mass of 0.4196 is entirely the top_k=4 cut, because the four survivors sum to 0.5806 - below the 0.90 budget - so top_p NEVER FIRED on that shape. A config you reason about as "top_p=0.9 keeps 90 percent" is, on a flat distribution, actually "top_k=4 keeps the top four and top_p is decorative". Read the stack in order; the first truncation wins.

---

## Known Failure Modes

| # | Failure | Cause | Fix |
|---|---------|-------|-----|
| 1 | Temperature treated as a re-ranker | `softmax(z/T)` rescales, never reorders - argmax `the (same)` at every T from 0.25 to 2.00 | Treat T as shape control (entropy 0.2128 to 1.8191); dethroning needs truncation, not heat |
| 2 | top_p read as "keep exactly this mass" | The rule is "adding up to top_p OR HIGHER" - p=0.50 keeps 0.7240 | Budget for the overshoot; kept mass is always >= top_p |
| 3 | top_k set from habit on flat shapes | Rank-blind: the stack's k=4 cut removes 0.4196 on flat while top_p never fires (survivors sum 0.5806 < 0.90) | Check which stage actually cuts; prefer shape-aware truncation (min_p) on flat shapes |
| 4 | min_p expected to behave like top_p | Threshold is a RATIO of p_max: 0.10 gives 0.0500 on peaked (4 kept) but 0.0153 on flat (8 kept) | Reason in ratios of the top token, not absolute probabilities; HF docs range 0.01-0.2 |
| 5 | typical_p read as "a better nucleus" | Different objective: ranks by \|info - H\|, which put model(\|0.0937\|) and a(\|0.1627\|) ahead of the(\|0.3169\|) and dropped the winner at the same 0.35 budget | Use typical-p for repetition control (Meister et al.), nucleus for mass control - do not swap them blindly |
| 6 | Stack order assumed irrelevant | The pipeline is sequential (HF L1591-1619); each stage renormalizes over survivors - the FIRST truncation wins | Pin and document the order you reason about; sampling configs are not commutative |

## Summary

- **Temperature is shape, not order** - entropy 0.2128 to 1.8191 nats and p_top 0.9530 to 0.3101 across T=0.25 to 2.00 with the argmax reading `the (same)` at every step; widening is all temperature can do.
- **Rank and mass are different budgets** - top-k keeps 0.4995 at k=1 blind to the 0.2244 discard; nucleus keeps the smallest set CROSSING the budget (0.7240 kept at p=0.50) and can never return an empty set (p=0.01 still keeps one token).
- **min-p is shape-adaptive where top-k and top-p are shape-blind** - the same 0.10 yields threshold 0.0500/4 kept on peaked and 0.0153/8 kept on flat, because the threshold is a ratio of p_max, not a fixed rank or budget.
- **typical-p optimizes a different target** - information content near H: on the three-peak distribution it keeps `['model', 'a']` (cum 0.58) and drops the boring winner `['the']` where nucleus keeps exactly the winner - the mechanism behind Meister et al.'s repetition reduction.
- **The stack is sequential and the first cut wins** - the default T0.7/k4/p0.9 config removes 0.4196 of mass on flat via top_k while top_p never fires; lowT0.2/p0.5 collapses to one token (top-share 1.0000) on peaked and bimodal; highT1.3+minp0.05 stays 6/8 wide at top-share 0.4090.
- **The lesson's decision**: sampling configs are composable mechanisms with readable invariants - entropy, kept mass, threshold ratio, stack order - not magic dials; every sampling question in this module's QUIZ (Q3-7, 13-15) is a question about one of these five knobs.

## References

### Related Minder Academy Documents

- [3401: Encoder-Decoder Architectures](../3400-architectures/3401-Encoder-Decoder-Architectures.md) - the sequence-level SEARCH surface (greedy vs beam) the QUIZ leans on; this lesson owns the per-token sampler underneath it.
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - the production config surface whose `SamplingParams(top_p=0.9)` literal this lesson gives mechanics to.
- [4202: Speculative Decoding](../../phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md) - the sampling-adjacent speed technique deliberately left out of this lesson's scope.
- [5206: Best-of-N and Rejection Sampling](../../phase5-finetuning/5200-alignment/5206-Best-of-N-and-Rejection-Sampling.md) - the training-side consumer of the diversity this lesson's knobs control.
- [7505: Temperature Zero and Deterministic Security Testing](../../phase7-agentic/7500-security/7505-Temperature-Zero-and-Deterministic-Security-Testing.md) - what T=0 buys (unique=1) and the residuals it does not remove.

### Primary Sources

- Meister, C., Pimentel, T., Wiher, G., & Cotterell, R. (2022). *Locally Typical Sampling.* TACL. arXiv:2202.00666 - tokens whose "information content [is] close to the expected information content, i.e., the conditional entropy"; "consistently reducing degenerate repetitions" vs nucleus and top-k sampling.
- Nguyen, M. N., Baker, A., Neo, C., Roush, A., Kirsch, A., & Shwartz-Ziv, R. (2024). *Turning Up the Heat: Min-p Sampling for Creative and Coherent LLM Outputs.* ICLR 2025 (oral). arXiv:2407.01082 - "a dynamic truncation method that adjusts the sampling threshold based on the model's confidence... using the top token's probability as a scaling factor."
- Hugging Face (2026). *Generation strategies* and GenerationConfig reference, transformers v5.19.0 - parameter defaults (temperature 1.0, top_k 50, top_p 1.0) and the min_p docstring ("Typical values are in the 0.01-0.2 range"); `src/transformers/generation/utils.py` L1591-1619 warper order, live-verified 2026-10-07.
- vLLM (2026). *SamplingParams API reference* - defaults temperature=1.0, top_p=1.0, top_k=0, min_p=0.0 and the min_p docstring: "Represents the minimum probability for a token to be considered, relative to the probability of the most likely token."

## Next Steps

- **Next Module:** continue with [assessment/QUIZ.md](assessment/QUIZ.md) - Q3-7 and 13-15 are the questions this lesson answers; the entropy walk 0.2128 to 1.8191, the never-empty nucleus at p=0.01, and the 0.4196 top_k cut on flat are the mechanics behind them.
- **Continue with:** [4202: Speculative Decoding](../../phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md) for how a draft sampler amortizes the verifier's steps, or [7505: Temperature Zero and Deterministic Security Testing](../../phase7-agentic/7500-security/7505-Temperature-Zero-and-Deterministic-Security-Testing.md) for the T=0 end of this lesson's temperature walk.
- **Assessment:** add a fourth config to the stack fence - T=1.0, top_k=0, top_p=1.0, min_p=0.15 - and predict the kept counts on all three shapes from the threshold rule BEFORE running; then extend the temperature walk to T=4.0 and state what p_top and the entropy approach.
