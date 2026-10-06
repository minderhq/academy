---
Document ID: 5206
Title: "5206: Best-of-N and Rejection Sampling"
Phase: 5
Module: 5200
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'alignment', 'inference', 'reranking', 'rlhf']
---

# 5206: Best-of-N and Rejection Sampling

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Best-of-N at the Endpoint](#best-of-n-at-the-endpoint)
- [The Overoptimization Curve](#the-overoptimization-curve)
- [Rejection-Sampling Fine-Tuning](#rejection-sampling-fine-tuning)
- [Renting versus Owning](#renting-versus-owning)
- [The Campaign Ledger](#the-campaign-ledger)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- **The BoN contract**: draw N completions from a frozen policy, score all N with a reward model, return the argmax — alignment with zero weight updates
- **The KL price tag**: verify the exact divergence Best-of-N buys per request, KL = log N − (N−1)/N, and the √(log N) quality law that makes doubling the budget a worse deal every time
- **Goodhart's slope**: reproduce the overoptimization curve — proxy reward rising monotonically while true quality peaks and falls — and locate the N past which reranking subtracts
- **Rejection-sampling fine-tuning**: close the loop from reranking to re-training, the sample-keep-dedup-SFT cycle Llama 2 ran for four RLHF versions before PPO ever entered
- **Rent versus own economics**: price inference-time reranking against one-time training on the same workload, and find the request count where ownership wins

---

## Abstract

Best-of-N sampling with a reward model is inference-time alignment without retraining — draw N completions, rerank them with the reward model [5203](./5203-RLHF.md) trained, serve the argmax. The alignment module's own assessment notes the pattern leans on the reward-model scoring it would reuse at inference, because no lesson in this curriculum owned the mechanism itself; this lesson owns it: the reranking contract, the exact KL divergence each request pays for it, the overoptimization curve that same contract produces when the reward model is imperfect, the rejection-sampling fine-tuning loop that converts rented quality into owned weights, and the ledger that decides between the two. The boundaries are owned up front: [5203](./5203-RLHF.md) owns the reward model's training and the three-stage pipeline, [5204](./5204-Preference-Dataset-Creation.md) owns the preference pairs beneath it, [5205](./5205-GRPO-RLVR.md) owns the training-time cousin that samples groups and takes relative advantages against verifiable rewards, and the agentic track's self-consistency [7105](../../phase7-agentic/7100-architecture/7105-Reflection-and-Self-Correction.md) owns the vote — plurality over extracted answers, no reward model at all. This lesson owns the rerank: one reward model, N draws, one argmax, and everything that follows from doing that at scale.

Five fences carry it. The KL fence verifies the identity against Monte-Carlo at six budgets — the divergence grows log N − (N−1)/N, the standardized quality gain grows like √(2 log N), and both tables print side by side. The Goodhart fence walks the same policy from N=1 to N=4096 under an imperfect reward model and watches the proxy score of the pick climb from 0.5653 to 1.1663 while its true quality peaks at N=4 and ends at −0.0202 — 0.5151 of quality destroyed past the peak by the same mechanism that built it. The RSFT fence runs the sample-keep-dedup-SFT loop for six versions inside the same world: gold at one draw climbs 0.2156 to 0.5452, and the fence's closing triple is the lesson in one line — the trained policy served raw (0.5438) beats the base policy reranked eight-way (0.4499), which beats the trained policy reranked eight-way (0.4009). The economics fence re-runs the walk under both policies and shows the same N carrying two signs — +0.2798 of gain on the base policy at N=4, −0.3195 on the trained policy at N=64 — then prices the rent: 1.2044 nats of KL per request forever against 0.3932 nats paid once, break-even at 13,166 requests a month. The campaign fence bills one 30-day API month five ways and the best row on the board is also the cheapest: the trained policy, served raw, at a 1462-dollar month against the 11,520-dollar reranked rows that serve strictly worse answers.

---

## Best-of-N at the Endpoint

The contract fits in one sentence: sample N completions from the policy, score each with the reward model, return the one with the highest score. No gradient step, no weight update, no training run — the base model is frozen and the alignment lives entirely in the selection. This is why every serving stack can switch it on with a config change, and why the module's quiz could only lean on the reward-model lesson for it: the mechanism is not RLHF's pipeline, it is an inference-time policy wrapped around [5203](./5203-RLHF.md)'s reward model.

Stiennon et al. (arXiv 2009.01325) put the contract to work before PPO entered the picture: a reward model trained on 64,832 human summary comparisons, best-of-N sampling over the TL;DR policy, and BoN tables walking N from 8 to 512 — the reranking curve was their ablation, not their headline (their headline policy trained with PPO at a KL coefficient of 0.05; the BoN tables lived in the appendix). The same paper supplied the identity this fence verifies: for a Gaussian policy reranked against itself, the KL divergence between the Best-of-N distribution and the base policy is exactly **log N − (N−1)/N**. That formula is not an analogy — it is the per-request price of the rerank, in nats, and Gao et al.'s overoptimization paper (arXiv 2210.10760) adopted it as its divergence axis for the same reason.

Two laws fall out of the fence. The KL price grows like log N — every doubling of N adds a smaller and smaller nat. The quality gain grows like the square root of that log — the expected maximum of N standard-normal scores climbs +0.5642σ by N=2, +1.4236σ by N=8, +2.3437σ by N=64, +3.6261σ by N=4096. Read the deltas: a 512x budget increase (N=8 to N=4096) buys 2.20σ more. The rerank is a logarithm wearing a serving config.

```python
import math, random

# KL(Bon_N || base) = log N - (N-1)/N   (Gaussian policy matched to itself)
# MC check: KL = E[ log N + (N-1) * log Phi(x*) ]  where x* = max of N draws

def phi(x):  # standard normal pdf
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def Phi(x):  # standard normal cdf
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def simpson(f, a, b, n=4000):
    if n % 2: n += 1
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += f(a + i * h) * (4 if i % 2 else 2)
    return s * h / 3.0

def e_max_analytic(N, lo=-8.0, hi=10.0):
    # E[max of N iid N(0,1)] = int x * N phi(x) Phi(x)^(N-1) dx
    return simpson(lambda x: x * N * phi(x) * (Phi(x) ** (N - 1)), lo, hi)

TRIALS = 20000
print("F1: Best-of-N KL against the base policy (exact Gaussian identity)")
print(f"{'N':>6} {'KL formula':>11} {'KL Monte-Carlo':>15} {'E[max]':>8} {'delta vs N=1':>13}")
base_emax = e_max_analytic(1)  # 0
for N in (1, 2, 8, 64, 512, 4096):
    trials = TRIALS if N <= 64 else (5000 if N <= 512 else 1500)
    rng = random.Random(7)
    tot = 0.0
    for _ in range(trials):
        # track max value AND its cdf value in one pass
        m = -1e18
        for _ in range(N):
            v = rng.gauss(0.0, 1.0)
            if v > m: m = v
        tot += math.log(N) + (N - 1) * math.log(Phi(m))
    kl_mc = tot / trials
    kl_f = math.log(N) - (N - 1) / N
    em = e_max_analytic(N)
    print(f"{N:>6} {kl_f:>11.4f} {kl_mc:>15.4f} {em:>8.4f} {em - base_emax:>+13.4f}")
```

The Monte-Carlo column exists to keep the formula honest — 20,000 trials at N=64 land 3.1711 against the closed form's 3.1745, and the residual shrinks where the trial count does not. The last column is the one that budgets: quality measured in sigmas is a concave function of the token bill, so the rerank budget belongs where the curve bends, not where the plateau begins.

---

## The Overoptimization Curve

Everything above assumes the reward model ranks true quality. It does not — it ranks *its opinion of* quality, learned from finite preference pairs ([5204](./5204-Preference-Dataset-Creation.md)'s data layer), and its errors are not symmetric noise. Gao, Schulman and Hilton mapped what happens when you optimize the proxy anyway: gold reward rises with the proxy, peaks, then falls, while the proxy keeps climbing — and the curve's shape depends on the optimizer, with Best-of-N and RL diverging along different functional forms (their setup: a 6B gold reward model standing in for humans, proxy reward models from 3M to 3B parameters trained on 100,000 synthetic comparisons, policies at 1.2B and 6B; the fitted BoN curves extrapolated out to N=60,000, roughly 10 nats of KL). The paper's own Table 2 holds the single most quotable artifact in the literature: at N=30,000, the proxy's top sample scored 0.9527 on the proxy and 0.5490 on gold — a riddle answer about potholes that the proxy loved and gold only liked. They also own the boundary this lesson must inherit: the human-label version of the gold curve was never measured — preference data is too expensive to collect at the KL where the decline shows.

The fence builds the smallest world that reproduces the curve. Three response modes — concise-correct, verbose-correct, jargon-wrong — each with a deviation score d measuring how far the sample stretches from its template. True quality *penalizes* deviation (PEN·d): a stretched answer is a worse answer. The reward model *rewards* deviation (BIAS·d): it was trained on tidy preference pairs, and it reads deviation as engagement. Proxy = gold + 0.45·d + noise. The argmax of N such proxies is a machine that converts reranking budget into deviation.

```python
import math, random

# three response modes; deviation d ~ half-normal(scale) drives BOTH:
#   gold  = q_mode - PEN*d      (deviation from the template really hurts)
#   proxy = gold + BIAS*d + eps (the RM rewards deviation as 'engaging')
MODES = [("concise-correct", 0.8, 0.55, 0.8),
         ("verbose-correct", 0.5, 0.25, 1.0),
         ("jargon-wrong",   -0.4, 0.20, 1.4)]
PEN, BIAS, EPS = 0.35, 0.45, 0.06
WALK = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 4096]

def one_sample(rng):
    u, v = rng.random(), rng.random()
    acc = 0.0
    for name, q, prior, dscale in MODES:
        acc += prior
        if u < acc:
            d = abs(rng.gauss(0.0, dscale))
            gold = q - PEN * d
            proxy = gold + BIAS * d + rng.gauss(0.0, EPS)
            return gold, proxy
    name, q, prior, dscale = MODES[-1]
    d = abs(rng.gauss(0.0, dscale))
    gold = q - PEN * d
    return gold, gold + BIAS * d + rng.gauss(0.0, EPS)

def walk(seed):
    rng = random.Random(seed)
    out = []
    for N in WALK:
        trials = 6000 if N <= 256 else (1500 if N <= 1024 else 400)
        gs = ps = 0.0
        for _ in range(trials):
            bg = bp = -1e18
            for _ in range(N):
                g, p = one_sample(rng)
                if p > bp: bp, bg = p, g
            gs += bg; ps += bp
        out.append((N, gs / trials, ps / trials))
    return out

print("F2: The Goodhart walk - proxy reward of the BoN pick vs its true quality")
print(f"{'N':>6} {'proxy of pick':>14} {'gold of pick':>13}")
rows = walk(11)
for N, g, p in rows:
    print(f"{N:>6} {p:>14.4f} {g:>13.4f}")
peak = max(rows, key=lambda r: r[1])
print(f"peak gold at N={peak[0]} ({peak[1]:.4f}); N=4096 gold {rows[-1][1]:.4f} "
      f"(delta {rows[-1][1]-peak[1]:+.4f}); proxy at 4096 {rows[-1][2]:.4f}")
```

Read the two columns against each other. The proxy of the pick never stops rising — 0.5653 at N=1, 1.1663 at N=4096, monotone, exactly what the serving dashboard shows. The gold of the pick rises from 0.2169 to a peak of 0.4950 at N=4 and then gives all of it back, ending at −0.0202 — 0.5151 below the peak. At small N the reward model's ranking signal dominates: it reliably prefers concise-correct over jargon-wrong, and reranking converts budget into quality. Past the peak the bias term dominates: the argmax is a contest over deviation, and the winner is a stretched, degenerate sample wearing a high proxy score. The rerank did not stop working — it started working on the wrong objective. That is the mechanism behind [5203](./5203-RLHF.md)'s reward-hacking row, and the reason "raise N" is not a default scaling knob but a budget with a peak to locate.

---

## Rejection-Sampling Fine-Tuning

Reranking rents the quality every request. The obvious next question is whether the rented picks can be kept — and they can: sample N, keep the ones that pass a verifier or clear the reward model, fine-tune on the kept set. This is rejection-sampling fine-tuning, and it is not a footnote — it is how Llama 2 (arXiv 2307.09288) actually ran its RLHF: versions V1 through V4 used **only** rejection-sampling fine-tuning, with PPO layered on top of the rejection-sampling checkpoint from V4 onward, the paper's stated reason being breadth versus depth (rejection sampling explores K samples per prompt from a frozen policy; PPO walks one sample through an online-updated policy) and simplicity. Two more Llama 2 details matter operationally: their V3 regressed on rhyming because each version trained only on the previous version's samples — fixed by pooling top-performing samples from *all* prior iterations — and the sampling temperature for a 10-to-100-sample pool needed progressive re-tuning, landing at T ∈ [1.2, 1.3]. The parallel result on the math side: Yuan et al.'s RFT (arXiv 2308.01825) took a LLaMA-7B from a 35.9% SFT baseline to 49.3% on GSM8K with rejection-sampled reasoning paths, and attributed the gain specifically to *distinct* reasoning paths — deduplicated solutions, not raw kept count.

The fence runs the loop inside the Goodhart world, so every number is on the same quality axis as the fences before and after. The verifier keeps samples with gold > 0.35 (concise-correct clears it when undeformed; verbose-correct only when barely deformed; jargon-wrong never — the threshold is doing RFT's "collect correct paths" work). The version-1 pool runs at two temperatures, per Llama 2's practice: T=1.25 stretches deviations and inflates the jargon mass, and the ledger prints what that costs — kept rate 0.572 at T=1.00 against 0.508 at T=1.25. (The world's kept paths concentrate in the same few deviation buckets at both temperatures, so the *distinct-path* effect RFT measured lives outside this world's resolution — the paper's claim is owned as a paper claim, not simulated here.) Each version's update moves the mode priors toward the kept frequencies at learning rate 0.40, six versions, 15,360 pool generations each.

```python
import math, random

# ---- the shared world (same constants as the Goodhart fence) ----
MODES = [("concise-correct", 0.8, 0.55, 0.8),
         ("verbose-correct", 0.5, 0.25, 1.0),
         ("jargon-wrong",   -0.4, 0.20, 1.4)]
PEN, BIAS, EPS = 0.35, 0.45, 0.06
THRESH = 0.35          # verifier keeps gold > THRESH
ETA = 0.40             # prior update rate
POOL = 15360           # generations per version (240 prompts x 64 samples)
VERSIONS = 6
DBIN = 0.25            # dedup bucket for d  (the 'distinct path' id)
BASE = tuple(m[2] for m in MODES)          # (0.55, 0.25, 0.20)
TPOOL = (0.55, 0.25, 0.30)                 # T=1.25 pool: jargon mass x1.5
TDMUL = 1.25                               # T=1.25 pool: deviations stretch

def draw_mode(rng, priors, tdmul=1.0):
    u = rng.random()
    acc = 0.0
    for i, (name, q, _, ds) in enumerate(MODES):
        acc += priors[i]
        if u < acc:
            d = abs(rng.gauss(0.0, ds * tdmul))
            gold = q - PEN * d
            return i, name, d, gold, gold + BIAS * d + rng.gauss(0.0, EPS)
    i = len(MODES) - 1
    name, q, _, ds = MODES[-1]
    d = abs(rng.gauss(0.0, ds * tdmul))
    gold = q - PEN * d
    return i, name, d, gold, gold + BIAS * d + rng.gauss(0.0, EPS)

def bon_gold(priors, N, trials, rng, tdmul=1.0):
    tot = 0.0
    for _ in range(trials):
        bg = bp = -1e18
        for _ in range(N):
            _, _, _, g, p = draw_mode(rng, priors, tdmul)
            if p > bp: bp, bg = p, g
        tot += bg
    return tot / trials

def pool_stats(rng, priors, tdmul, size=POOL):
    kept = 0
    buckets = set()
    freq = [0, 0, 0]
    for _ in range(size):
        mi, name, d, g, p = draw_mode(rng, priors, tdmul)
        if g > THRESH:
            kept += 1
            freq[mi] += 1
            buckets.add((name, round(d / DBIN)))
    return kept, buckets, freq

print("F3: Rejection-sampling fine-tuning inside the same world")
print()
# temperature ledger on the version-1 pool (Llama 2: optimal T in [1.2, 1.3])
k0, b0, f0 = pool_stats(random.Random(202), BASE, 1.0)
k1, b1, f1 = pool_stats(random.Random(303), TPOOL, TDMUL)
print(f"pool T=1.00: kept {k0}/{POOL} ({k0/POOL:.3f})  distinct kept {len(b0)}")
print(f"pool T=1.25: kept {k1}/{POOL} ({k1/POOL:.3f})  distinct kept {len(b1)}")
print()
print(f"{'ver':>4} {'prior A':>8} {'prior B':>8} {'prior C':>8} {'gold N=1':>9} {'verif-pass':>10}")
priors = BASE
for v in range(1, VERSIONS + 1):
    rk, rb, rf = pool_stats(random.Random(400 + v), priors, TDMUL)
    tot = sum(rf) or 1
    target = [c / tot for c in rf]
    priors = [(1 - ETA) * priors[i] + ETA * target[i] for i in range(3)]
    ev = bon_gold(priors, 1, 30000, random.Random(9000 + v))
    erng = random.Random(9500 + v)
    vp = 0.0
    for _ in range(8000):
        _, _, _, g, _ = draw_mode(erng, priors)
        vp += 1.0 if g > THRESH else 0.0
    vp /= 8000
    print(f"V{v:>3} {priors[0]:>8.3f} {priors[1]:>8.3f} {priors[2]:>8.3f} {ev:>9.4f} {vp:>10.4f}")

print()
g_base_1 = bon_gold(BASE, 1, 30000, random.Random(778))
g_base_8 = bon_gold(BASE, 8, 30000, random.Random(777))
g_v6_1 = bon_gold(priors, 1, 30000, random.Random(779))
g_v6_8 = bon_gold(priors, 8, 30000, random.Random(780))
print(f"base BoN-1 gold {g_base_1:.4f} | base BoN-8 gold {g_base_8:.4f}")
print(f"V{VERSIONS} BoN-1 gold {g_v6_1:.4f} | V{VERSIONS} BoN-8 gold {g_v6_8:.4f}")
KL = sum(p * math.log(p / q) for p, q in zip(priors, BASE) if p > 0)
print(f"discrete KL(prior_V{VERSIONS} || prior_base) = {KL:.4f} nats")
```

The climb is monotone — 0.3369, 0.4164, 0.4727, 0.5108, 0.5300, 0.5452 — with the jargon prior collapsing from 0.200 to 0.009 and the verifier-pass rate climbing to 0.8516. But the fence's last three numbers are the lesson. The trained policy served raw scores 0.5438 at one draw. The base policy reranked with the same reward model at N=8 scores 0.4499 at eight draws. And the trained policy reranked at N=8 scores 0.4009 — *below* its own raw service. The ordering is the whole argument: the trained policy at one draw beats the rented policy at eight, and the same rerank that lifted the base policy by +0.2343 *drags* the trained policy down by 0.1429. Why: the reward model's deviation-love did not go away when the policy improved — it became the only headroom left. A weak policy offers the reranker real mistakes to filter; a trained policy offers it nothing but deviation to reward. The KL column closes the loop: all of that owned quality cost 0.3932 nats of policy movement, paid once.

---

## Renting versus Owning

The last fence compared two policies at two budgets; this one walks the whole curve under both, because the sign of the rerank's marginal value is a property of the *policy*, not the knob. Then it prices both sides: the rent (BoN's per-request KL, the F1 identity) against the ownership cost (the RSFT loop's one-time KL and one-time pool bill).

```python
import math, random

MODES = [("concise-correct", 0.8, 0.55, 0.8),
         ("verbose-correct", 0.5, 0.25, 1.0),
         ("jargon-wrong",   -0.4, 0.20, 1.4)]
PEN, BIAS, EPS = 0.35, 0.45, 0.06
THRESH, ETA, POOL, VERSIONS = 0.35, 0.40, 15360, 6
BASE = tuple(m[2] for m in MODES)

def draw_mode(rng, priors, tdmul=1.0):
    u = rng.random()
    acc = 0.0
    for i, (name, q, _, ds) in enumerate(MODES):
        acc += priors[i]
        if u < acc:
            d = abs(rng.gauss(0.0, ds * tdmul))
            gold = q - PEN * d
            return i, gold, gold + BIAS * d + rng.gauss(0.0, EPS)
    i, (name, q, _, ds) = len(MODES) - 1, MODES[-1]
    d = abs(rng.gauss(0.0, ds * tdmul))
    gold = q - PEN * d
    return i, gold, gold + BIAS * d + rng.gauss(0.0, EPS)

def bon_gold(priors, N, trials, rng):
    tot = 0.0
    for _ in range(trials):
        bg = bp = -1e18
        for _ in range(N):
            _, g, p = draw_mode(rng, priors)
            if p > bp: bp, bg = p, g
        tot += bg
    return tot / trials

# --- climb to V6 (pools only; no evals here) ---
def climb():
    priors = BASE
    for v in range(1, VERSIONS + 1):
        rng = random.Random(400 + v)
        freq = [0, 0, 0]
        for _ in range(POOL):
            mi, g, p = draw_mode(rng, priors, 1.25)
            if g > THRESH: freq[mi] += 1
        tot = sum(freq) or 1
        target = [c / tot for c in freq]
        priors = [(1 - ETA) * priors[i] + ETA * target[i] for i in range(3)]
    return tuple(priors)

V6 = climb()
print(f"V6 priors {tuple(round(x,3) for x in V6)}")

# ---------- F4a: the same N, two signs ----------
WALK_N = [1, 2, 4, 8, 16, 32, 64]
print("F4: one BoN curve per policy - the same N, two signs")
print(f"{'N':>4} {'base gold':>10} {'base delta':>11} {'V6 gold':>9} {'V6 delta':>10}")
b1 = v61 = None
for N in WALK_N:
    gb = bon_gold(BASE, N, 20000, random.Random(600 + N))
    gv = bon_gold(V6, N, 20000, random.Random(700 + N))
    if N == 1: b1, v61 = gb, gv
    print(f"{N:>4} {gb:>10.4f} {gb-b1:>+11.4f} {gv:>9.4f} {gv-v61:>+10.4f}")

# ---------- F4b: KL rent vs one-time ownership ----------
def Phi(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
rng = random.Random(9)
for N in (8, 64):
    trials = 4000 if N == 8 else 1000
    tot = 0.0
    for _ in range(trials):
        m = -1e18
        for _ in range(N): m = max(m, rng.gauss(0.0, 1.0))
        tot += math.log(N) + (N - 1) * math.log(Phi(m))
    print(f"BoN-{N} per-request KL: formula {math.log(N)-(N-1)/N:.4f} | MC {tot/trials:.4f} nats")
KL_own = sum(p * math.log(p / q) for p, q in zip(V6, BASE) if p > 0)
print(f"one-time ownership KL: {KL_own:.4f} nats")
print()

# ---------- F4c: break-even ----------
TOK, PRICE = 400, 0.60 / 1e6          # $ per output token
train_gens = POOL * VERSIONS
train_cost = train_gens * TOK * PRICE
rent_per_req = 7 * TOK * PRICE
breakeven = train_cost / rent_per_req
print(f"one-time bill: {train_gens} pool generations = ${train_cost:.2f}")
print(f"BoN-8 rent: 7 extra generations/request = ${rent_per_req:.6f}/request")
print(f"break-even: {breakeven:,.0f} requests/month")
reqs = 6_000_000
print(f"at {reqs:,}/month: rent ${rent_per_req*reqs:,.0f}/month vs own ${train_cost:.2f} once "
      f"({rent_per_req*reqs/train_cost:.0f}x the first month)")
```

The walk table is the sign convention made explicit. On the base policy, the rerank's marginal gain peaks at N=4 (+0.2798) and decays toward zero — the F2 story with finer resolution. On the trained policy, the first rerank draw already subtracts (−0.0198 at N=2) and the hole deepens monotonically to −0.3195 at N=64. There is no N that helps the trained policy, and there is no N past which the base policy's curve recovers. Meanwhile the KL columns price the two routes: serving BoN-8 rents 1.2044 nats of divergence from the base policy *every request*, BoN-64 rents 3.1745, and the RSFT loop bought its entire quality climb for 0.3932 nats once. The dollar ledger uses the sim's own pool — 92,160 pool generations at 400 output tokens and $0.60/M is $22.12 paid once, against 7 extra generations per request at $0.001680: break-even at 13,166 requests a month, and at 6 million requests a month the rent is $10,080 — 456 times the one-time bill, due again next month. (Each fence re-draws its own evaluation, so the same quantity wiggles within four thousandths across fences — that wiggle is the Monte-Carlo noise floor, not a disagreement.)

Llama 2's production answer was not either/or: rejection sampling through V4, then PPO *on top of* the rejection-sampling checkpoint, with the KL penalty managed explicitly (β = 0.01 at 7B/13B, 0.005 at 34B/70B) — training-time alignment is KL *budget management*, while inference-time BoN pays an unmanaged log N rent that no dashboard line item ever questions.

---

## The Campaign Ledger

One 30-day month, 6 million requests, 400 output tokens each, $0.60/M — five configs on the board.

```python
import math, random

MODES = [("concise-correct", 0.8, 0.55, 0.8),
         ("verbose-correct", 0.5, 0.25, 1.0),
         ("jargon-wrong",   -0.4, 0.20, 1.4)]
PEN, BIAS, EPS = 0.35, 0.45, 0.06
THRESH, ETA, POOL, VERSIONS = 0.35, 0.40, 15360, 6
BASE = tuple(m[2] for m in MODES)

def draw_mode(rng, priors, tdmul=1.0):
    u = rng.random()
    acc = 0.0
    for i, (name, q, _, ds) in enumerate(MODES):
        acc += priors[i]
        if u < acc:
            d = abs(rng.gauss(0.0, ds * tdmul))
            gold = q - PEN * d
            return i, gold, gold + BIAS * d + rng.gauss(0.0, EPS)
    i, (name, q, _, ds) = len(MODES) - 1, MODES[-1]
    d = abs(rng.gauss(0.0, ds * tdmul))
    gold = q - PEN * d
    return i, gold, gold + BIAS * d + rng.gauss(0.0, EPS)

def bon_gold(priors, N, trials, rng):
    tot = 0.0
    for _ in range(trials):
        bg = bp = -1e18
        for _ in range(N):
            _, g, p = draw_mode(rng, priors)
            if p > bp: bp, bg = p, g
        tot += bg
    return tot / trials

def climb():
    priors = BASE
    for v in range(1, VERSIONS + 1):
        rng = random.Random(400 + v)
        freq = [0, 0, 0]
        for _ in range(POOL):
            mi, g, p = draw_mode(rng, priors, 1.25)
            if g > THRESH: freq[mi] += 1
        tot = sum(freq) or 1
        priors = [(1 - ETA) * priors[i] + ETA * (freq[i] / tot) for i in range(3)]
    return tuple(priors)

V6 = climb()
REQS, TOK = 6_000_000, 400
PRICE = 0.60 / 1e6
train_gens = POOL * VERSIONS

configs = [("base + BoN-1 (raw)", BASE, 1),
           ("base + BoN-4 (peak)", BASE, 4),
           ("base + BoN-8 (past peak)", BASE, 8),
           (f"V{VERSIONS} + BoN-1 (owned, raw)", V6, 1),
           (f"V{VERSIONS} + BoN-8 (owned, reranked)", V6, 8)]
print(f"F5: one 30-day API month - {REQS:,} requests x {TOK} output tokens @ $0.60/M")
print(f"{'config':<32} {'gold':>7} {'gens/req':>9} {'tokens/mo':>12} {'$/month':>10}")
train_cost = train_gens * TOK * PRICE
for label, priors, N in configs:
    g = bon_gold(priors, N, 30000, random.Random(800 + N))
    gens = REQS * N + (train_gens if N == 1 and priors is V6 else 0)
    cost = gens * TOK * PRICE
    print(f"{label:<32} {g:>7.4f} {N:>9} {gens*TOK/1e9:>10.2f}B {cost:>10,.2f}")
print()
print(f"one-time RSFT pool bill (all routes, all six versions): {train_gens} generations = ${train_cost:.2f}")
print(f"shared sunk cost of having ANY reward model: 64,832 human comparisons @ $2 = ${64832*2:,}")
best = max(configs, key=lambda c: bon_gold(c[1], c[2], 30000, random.Random(900 + c[2])))
print(f"best quality on the board: {best[0]} - also the cheapest row on the board")
```

Three verdicts fall out of the board. First, the best row is the cheapest row: the trained policy served raw (gold 0.5437, $1,462.12 with the one-time pool bill amortized in) beats everything, including every reranked row at four to eight times its bill. Second, the most expensive row is never the best row: BoN-8 costs $11,520 under *either* policy and returns 0.4499 and 0.3988 — the naive "more reranking is more alignment" scaling lands past the base policy's peak and inside the trained policy's hole. Third, the board's real fixed cost is not on it: the reward model every config leans on took 64,832 human comparisons — Stiennon's own census — and at $2 a comparison that is $129,664 paid before any of these rows exist. The marginal economics are what the ledger prices, and they are unambiguous at production volume: every reranked row costs more per month than the best row's entire bill, and the two $11,520 rows buy the third- and fourth-best answers on the board. (The quality column is the sim's gold score throughout — the scheme and the sign pattern are the claim, not the magnitudes.)

---

## Known Failure Modes

```text
1. Reranking past the peak
   Symptom: quality flat or falling while the proxy metric climbs with N
   Fix:     locate the peak by eval (the F2 walk); treat N as a budget
            with a max, not a default scaling knob

2. Reward-model bias amplified
   Symptom: BoN picks read as 'engaging' but deformed - the 0.9527-proxy/
            0.5490-gold signature
   Fix:     audit the RM on tail samples (high-draw picks); retrain on
            preference pairs covering deviation; shrink BIAS, not N

3. Verifier false negatives thinning the pool
   Symptom: kept rate collapses across RSFT versions; updates starve
   Fix:     audit the threshold against a labeled sample before blaming
            the policy (5205's verifier-bug row, data side)

4. Training on the previous version only
   Symptom: a capability regresses at some RLHF version (Llama 2's V3
            rhyming)
   Fix:     pool top samples from ALL prior iterations into each
            version's SFT set

5. Temperature drift across iterations
   Symptom: the pool's kept rate slides as the policy improves
   Fix:     re-tune sampling T per version (Llama 2 landed at 1.2-1.3
            for 10-100-sample pools)

6. BoN on a trained policy
   Symptom: the F4 table's second column - rerank subtracts at every N
   Fix:     serve raw; spend the rerank budget on the RM's calibration
            instead (its bias is the only headroom left)

7. The un-questioned rent
   Symptom: serving bill grows N x with no quality delta on the board
   Fix:     price the rerank per request (the F4c ledger); break-even
            against the one-time RSFT bill every quarter
```

---

## Summary

Best-of-N is inference-time alignment: N draws, one reward-model argmax, zero weight updates — and an exact price, log N − (N−1)/N nats per request, for a quality gain that grows only like √(log N). Because the reward model is an imperfect proxy, the same knob traces the overoptimization curve: proxy reward monotone up (0.5653 to 1.1663), true quality peaking at N=4 and falling 0.5151 past it. Rejection-sampling fine-tuning converts the rented picks into owned weights — Llama 2 ran it for four RLHF versions before adding PPO, and RFT took LLaMA-7B from 35.9 to 49.3 on GSM8K — and inside this lesson's world the trained policy served raw (0.5438) beats the base policy reranked eight-way (0.4499), which beats the trained policy reranked eight-way (0.4009): the same N carries two signs, +0.2798 on a weak policy and −0.3195 on a strong one, because a trained policy leaves the reward model nothing to rerank but its own bias. The ledger settles it at production volume: 1.2044 nats of KL rented per request against 0.3932 paid once, $10,080 a month of rent against a $22.12 one-time bill, break-even at 13,166 requests — with the reward model's 64,832 human comparisons as the sunk cost both routes share and the one row on the board that never gets questioned.

---

## References

### Related Minder Academy Documents

- [5201: DPO (Direct Preference Optimization) Theory](5201-DPO-Theory.md)
- [5202: Alignment Orchestration - Reward Modeling vs Direct Preference](5202-Alignment-Orchestration.md)
- [5203: Reinforcement Learning from Human Feedback](5203-RLHF.md)
- [5204: Preference Dataset Creation](5204-Preference-Dataset-Creation.md)
- [5205: GRPO and Reinforcement Learning from Verifiable Rewards](5205-GRPO-RLVR.md)

---

## Next Steps

- Continue with: **[5204: Preference Dataset Creation](./5204-Preference-Dataset-Creation.md)** for the preference-data layer beneath the reward model every config in the campaign ledger shares
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
