---
Document ID: 7505
Title: "7505: Temperature Zero and Deterministic Security Testing"
Phase: 7
Module: 7500
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Tags: ['agents', 'security', 'evaluation', 'inference']
---

# 7505: Temperature Zero and Deterministic Security Testing

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Sampler Is the Only Random Part](#the-sampler-is-the-only-random-part)
- [A Red-Team Suite That Flaps](#a-red-team-suite-that-flaps)
- [What Temperature Zero Does Not Buy](#what-temperature-zero-does-not-buy)
- [The Pass at k Fix](#the-pass-at-k-fix)
- [One Gate Priced Four Ways](#one-gate-priced-four-ways)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

By the end of this lesson, you will be able to:

- Read the temperature knob as arithmetic — softmax over logits divided by T, the argmax limit at T=0, and what each T buys inside the sampler
- Price the flapping red-team suite: 50 identical-code runs split 33 red / 17 green at T=0.7 and stand 50/50 green at T=0
- Name the two guarantees temperature zero does not give — near-tie batch noise and the provider fingerprint bump that flips decisions with zero code changes
- Estimate attack rates you can trust with pass@k and the constant `std x sqrt(k)` law
- Price four gate configs on one month of red-team CI and defend the T=0-CI plus sampled-nightly stack

## Abstract

The module's own QUIZ admits the gap this lesson fills: temperature-zero deterministic decoding for reproducible test runs is taught nowhere in the lessons (Q17), so the question leans on [7501](7501-Prompt-Injection-Defense.md)'s cheap-deterministic-first pipeline discipline instead. What that lean hides is a decoding decision every security test run makes before the first payload fires: sample, or argue. [7501](7501-Prompt-Injection-Defense.md) built the four-layer defense and its red-team regression suite, [7502](7502-PII-Redaction.md) stacked detectors for payload content, [7503](7503-Adversarial-Attacks.md) hardened against perturbed inputs, [7504](7504-Agent-Abuse-Prevention-and-Identity-Threats.md) moved the fight to the traffic; and [7104](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) already named the caveat this lesson cashes — pin sampling parameters, or score pass@k over repeats — without teaching what pinning actually means. Nothing in the curriculum teaches the fork itself: that temperature zero is argmax, that argmax is the only determinism the temperature knob buys, and that the guarantee stops at the provider's next fingerprint bump. This lesson turns that decision into working code — a sampler walk, a flapping suite, the two residual failure modes, the pass@k fix, and a four-way CI ledger.

## The Sampler Is the Only Random Part

Decoding has exactly one random component: the token draw. The model produces fixed logits for the next position, and everything else is bookkeeping. Greedy decoding skips the draw entirely — the [Transformers generation strategies docs](https://huggingface.co/docs/transformers/en/generation_strategies) define it as the default: *"Greedy search is the default decoding strategy. It selects the next most likely token at each step."* Sampling instead flattens the logits with temperature into a distribution and rolls for it:

```python
import math
import random
from collections import Counter

VOCAB = ["refuse", "comply", "ask-clarifying", "partial-answer"]
LOGITS = [2.0, 1.2, 0.6, -0.4]          # one injected-payload decision


def softmax(z, T):
    if T <= 0.0:
        m = max(z)
        return [1.0 if v == m else 0.0 for v in z]
    s = sum(math.exp(v / T) for v in z)
    return [math.exp(v / T) / s for v in z]


rng = random.Random(7)
DRAWS = 2000
for T in (0.0, 0.25, 0.5, 0.7, 1.0, 1.5):
    p = softmax(LOGITS, T)
    cnt = Counter()
    for _ in range(DRAWS):
        r, acc = rng.random(), 0.0
        for tok, pi in zip(VOCAB, p):
            acc += pi
            if r < acc:
                cnt[tok] += 1
                break
        else:
            cnt[VOCAB[-1]] += 1
    top = max(range(4), key=lambda i: p[i])
    print(f"T={T:4.2f}  unique={len(cnt):2d}  greedy_share={cnt[VOCAB[top]]/DRAWS:.4f}"
          f"  p(comply)={p[VOCAB.index('comply')]:.4f}")
```

The walk is the whole mechanism. At T=0 the 2,000-draw stream produces exactly **1** unique output — the argmax, `refuse`, with greedy share 1.0000, because softmax at T=0 puts all mass on the top logit and the draw has nothing to draw. At T=0.25 the same stream already produces 3 unique outputs (greedy share 0.9575), at T=0.7 it produces 4 with the greedy token at 0.6760, and by T=1.5 the greedy share has decayed to 0.4735. Two serving stacks make this concrete. vLLM's `SamplingParams` implements the limit directly — its source reads `if self.temperature < _SAMPLING_EPS: # Zero temperature means greedy sampling`, and forces `top_p = 1.0` at the same branch, because truncation is meaningless when one token holds all the mass. OpenAI's API takes the softer contract: the [seed-parameter cookbook](https://developers.openai.com/cookbook/examples/reproducible_outputs_with_the_seed_parameter) promises *"(mostly) deterministic outputs"* when the same seed rides along with identical parameters — mostly, because the server-side sampler is only half the story this lesson's third section tells. The security read: a payload tested at T=0 exercises the argmax path and nothing else, and p(comply)=0.2145 at T=0.7 means the same payload lands on roughly one in five sampled runs without any code change anywhere.

## A Red-Team Suite That Flaps

[7501's red-team suite](7501-Prompt-Injection-Defense.md) is a regression test: seven labeled payloads, a pass/fail per payload, a verdict for the pipeline. The suite's verdict is only as stable as the decoding under it. Run the same seven payloads against the same frozen stand-in model — fixed attack probabilities derived from fixed logit gaps — fifty times at the serving temperature most stacks default to:

```python
import math
import random
from collections import Counter

PAYLOADS = [
    ("direct-ignore", 2.6), ("roleplay-DAN", 1.9), ("conditional-trigger", 1.2),
    ("base64-encoding", 0.8), ("multilingual", 2.2), ("indirect-doc", 0.5),
    ("jailbreak-acronym", 1.6),
]
T_SERVE = 0.7


def attack_prob(delta, T):
    # Bernoulli stand-in: the sampled next token is the harmful continuation
    # with prob sigmoid(-delta / T); greedy (T=0) never takes it when delta > 0.
    if T <= 0.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(delta / T))


def run_suite(T, r):
    return sum(1 for _, d in PAYLOADS if r.random() < attack_prob(d, T))


R = 50
rngS = random.Random(101)
verdicts = Counter()
rates = []
for _ in range(R):
    a = run_suite(T_SERVE, rngS)
    verdicts["red (attack observed)"] += 1 if a > 0 else 0
    verdicts["green (0 attacks)"] += 1 if a == 0 else 0
    rates.append(a)
print(f"T=0.70 over {R} identical-code runs:")
print(f"  verdict split  : {dict(verdicts)}")
print(f"  attacks per run: min {min(rates)}, max {max(rates)}, mean {sum(rates)/len(rates):.3f}")
rngZ = random.Random(202)
z = run_suite(0.0, rngZ)
print(f"T=0.00 over {R} runs: attacks observed {z} (suite verdict {R}/{R} green)")
ps = [attack_prob(d, 0.7) for _, d in PAYLOADS]
print("per-payload attack prob @ T=0.7:")
for (name, d), p in zip(PAYLOADS, ps):
    print(f"  {name:22s} delta={d:4.2f}  p={p:.4f}")
p0 = 1.0
for p in ps:
    p0 *= (1 - p)
print(f"P(clean run) = product of (1-p) = {p0:.4f}")
```

Nothing in the code changed across the fifty runs — the model is frozen, the payloads are frozen, the decoding is frozen — and the verdict split **33 red / 17 green**. The attack count per run ranges 0 to 4 around a mean of 1.040, and the arithmetic explains the flapping: per-payload attack probabilities at T=0.7 run from 0.0238 (direct-ignore) to 0.3287 (indirect-doc), so the probability of a fully clean run is the product of seven survivals, P(clean) = 0.3436. A CI gate reading this suite is a coin with a 2:1 red bias wearing a test suit. [7104's regression-gate section](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) already said what happens next: *"a gate that fails on noise gets deleted within a week."* At T=0.0 the same fifty runs observe zero attacks and stand 50/50 green — which is the other trap, not the fix: every payload's greedy decision holds (all gaps are positive), so the suite is silent about a sampled path where the weakest payload lands a third of the time. Silence and safety are different verdicts, and the next section shows the silence is not even guaranteed.

## What Temperature Zero Does Not Buy

Temperature zero buys the argmax path. It does not buy the argmax value, because the argmax itself can move — from load-dependent numerics inside the serving stack, and from the provider changing the model under the API. Both residuals are measured, not folkloric. Thinking Machines Lab's [batch-invariance work](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) (He et al., September 2025) traced serving nondeterminism to kernels whose floating-point reduction order varies with batch size, and measured the blast radius on a frontier model: **Qwen3-235B at temperature 0 produced 80 unique outputs across 1,000 identical completions** — with batch-invariant kernels, all 1,000 were identical. And the academic record agrees at the API level: [Ouyang et al.](https://arxiv.org/abs/2308.02828) (*An Empirical Study of the Non-determinism of ChatGPT in Code Generation*, arXiv 2308.02828) state directly that *"setting the temperature to 0 does not guarantee determinism in code generation."* The fence prices both residuals on the payload suite:

```python
import math
import random
from collections import Counter

PAYLOADS = [
    ("direct-ignore", 2.6), ("roleplay-DAN", 1.9), ("conditional-trigger", 1.2),
    ("base64-encoding", 0.8), ("multilingual", 2.2), ("indirect-doc", 0.5),
    ("jailbreak-acronym", 1.6),
]


def norm(r, mu, sigma):
    u1, u2 = r.random(), r.random()
    return mu + math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2) * sigma


BATCHES = [1, 2, 4, 8, 16, 32]
TRIALS = 400
SIGMA_B32 = 0.098                                   # the B=32 batch-variant noise scale
rngB = random.Random(303)
flips = Counter()
for name, d in PAYLOADS:
    for B in BATCHES:
        sigma = 0.02 + 0.004 * B
        for _ in range(TRIALS):
            if abs(norm(rngB, 0.0, sigma)) > d:
                flips[name] += 1
print("greedy-decision stability over batch sizes", BATCHES, f"x{TRIALS} trials:")
n = len(BATCHES) * TRIALS
for name, d in PAYLOADS:
    print(f"  {name:22s} gap={d:4.2f}  argmax flips {flips[name]:4d}/{n}")
print(f"B=32 noise scale sigma = {SIGMA_B32:.3f}")

TIE_GAPS = [0.02, 0.05, 0.10, 0.20, 0.50]
rngT = random.Random(304)
tie_flips = {}
for d in TIE_GAPS:
    c = sum(1 for _ in range(TRIALS) if abs(norm(rngT, 0.0, 0.098)) > d)
    tie_flips[d] = c
print("near-tie sweep at the B=32 noise scale (sigma=0.098):")
for d in TIE_GAPS:
    print(f"  gap={d:4.2f}  flips {tie_flips[d]:3d}/{TRIALS}")

DRIFT = 1.30                                  # provider fingerprint bump moves logits
fp = [(name, d) for name, d in PAYLOADS if d < DRIFT]
print(f"fingerprint bump (drift {DRIFT}): {len(fp)} of {len(PAYLOADS)} greedy decisions flip at T=0")
for name, d in PAYLOADS:
    print(f"  {name:22s} gap={d:4.2f} -> {'FLIP' if d < DRIFT else 'hold'}")
```

Three facts come out of the fence. First, the suite's real decisions are robust to simulated batch noise: every gap is 0.50 or larger, the B=32 noise scale is sigma = 0.098, and **all seven decisions flip 0/2,400** across the batch sweep — greedy is stable exactly as long as the decision margin clears the numerics. The near-tie sweep shows where that guarantee ends: at gap 0.02, 338 of 400 decisions flip; at gap 0.10, 141; at gap 0.50, zero. Decisions do not fail uniformly — the ones close to the boundary are the ones that move, which is why the Thinking Machines fix is kernel-level (batch-invariant reductions, at roughly twenty percent slower matmul) rather than a seed parameter. Second, the provider bump is the bigger residual: modeled as a uniform compliance-pressure drift of 1.30 on every decision's gap, it flips **3 of 7** greedy decisions — conditional-trigger, base64-encoding, indirect-doc — at T=0 with zero code changes. OpenAI exposes exactly this surface as `system_fingerprint`: the [Azure reproducible-output docs](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/how-to/reproducible-output) confirm outputs can differ even with the same seed once the fingerprint moves. Third, the combination is why Ouyang et al. found what they found: temperature 0 reduces the churn and does not eliminate it, so a security suite that needs reproducibility has to engineer for the residual instead of asserting it away — record the fingerprint per run, re-run on change, and never trust a near-tie margin.

## The Pass at k Fix

Pinning to T=0 for CI answers the flapping gate, and the previous section shows why it cannot be the whole answer: the greedy path is one point in the output distribution, and it is not the point attackers sample from. The honest middle is what [7104's caveat](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) already named — score pass@k over repeats. The estimator is Codex's ([Chen et al., arXiv 2107.03374](https://arxiv.org/abs/2107.03374), the same unbiased pass@k [2403's evaluation lesson](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) era tooling standardizes), and its sampling noise obeys a law the fence can verify:

```python
import math
import random

PAYLOADS = [
    ("direct-ignore", 2.6), ("roleplay-DAN", 1.9), ("conditional-trigger", 1.2),
    ("base64-encoding", 0.8), ("multilingual", 2.2), ("indirect-doc", 0.5),
    ("jailbreak-acronym", 1.6),
]
T_SERVE = 0.7


def attack_prob(delta, T):
    if T <= 0.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(delta / T))


REPS = 400
for K in (1, 3, 5, 10):
    rngK = random.Random(500 + K)
    ests = []
    for _ in range(REPS):
        per = []
        for _, d in PAYLOADS:
            hits = sum(1 for _ in range(K) if rngK.random() < attack_prob(d, T_SERVE))
            per.append(hits / K)
        ests.append(sum(per) / len(per))
    m = sum(ests) / len(ests)
    sd = math.sqrt(sum((e - m) ** 2 for e in ests) / (len(ests) - 1))
    print(f"k={K:2d}  mean ASR estimate {m:.4f}  std {sd:.4f}  (std x sqrt(k) = {sd * math.sqrt(K):.4f})")
mean_asr = sum(1.0 / (1.0 + math.exp(d / T_SERVE)) for _, d in PAYLOADS) / len(PAYLOADS)
print(f"greedy baseline (T=0): suite ASR 0.0000 - {len(PAYLOADS)}/{len(PAYLOADS)} payloads look safe")
print(f"suite mean ASR @ T=0.7: {mean_asr:.4f} per payload ({mean_asr * len(PAYLOADS):.3f} attacks/run expected)")
```

The law holds: `std x sqrt(k)` lands at 0.1169, 0.1193, 0.1166, 0.1207 across k = 1..10 — constant, which is the 1/sqrt(k) shape saying each extra sample buys a fixed share of variance. In absolute terms, k=1 estimates the suite's attack rate with std 0.1169 (noise bigger than the signal — the suite mean is 0.1347), k=5 gets to 0.0521, and k=10 gets to 0.0382. That last number is the design constraint for any sampled gate: the alert band must clear the estimator's noise floor, or the gate re-joins the flapping suite of the previous section with extra steps. And the fence's last two lines are the argument for running both regimes: the greedy baseline reads 0.0000 — all seven payloads look safe — while the sampled path sits at 0.1347 attacks per payload per run, 0.943 per run expected. A T=0-only suite is not a conservative approximation of that number; it is a measurement of a different, safer model than the one attackers face. The deployable split the final section prices: T=0 in CI where a verdict is needed per push, sampled pass@k on a schedule where a rate is needed per release.

## One Gate Priced Four Ways

One month of red-team CI on the same frozen model and the same day-12 provider bump — four gate configs, one ledger. The cost model is deliberately lopsided the way real teams are: tokens at $0.50 per million are rounding errors, triage at 25 minutes and $75/hour per false red is the bill that lands, and an unnoticed sampled-path regression is priced at $600 of remediation:

```python
import math
import random

PAYLOADS = [
    ("direct-ignore", 2.6), ("roleplay-DAN", 1.9), ("conditional-trigger", 1.2),
    ("base64-encoding", 0.8), ("multilingual", 2.2), ("indirect-doc", 0.5),
    ("jailbreak-acronym", 1.6),
]
T_SERVE = 0.7
DRIFT = 1.30
mean_asr = sum(1.0 / (1.0 + math.exp(d / T_SERVE)) for _, d in PAYLOADS) / len(PAYLOADS)


def attack_prob(delta, T):
    if T <= 0.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(delta / T))


def run_suite(T, r):
    return sum(1 for _, d in PAYLOADS if r.random() < attack_prob(d, T))


RUNS_PER_DAY = 30
DAYS = 22
TRIAGE_MIN = 25
ENG_RATE = 75.0                  # $/h
TOK_PER_RUN = 2400
PRICE_PER_MTOK = 0.50
REGRESSION_COST = 600.0          # remediation when a sampled-path regression ships
DETECT_JUMP = 0.08               # gate trips when suite ASR estimate moves this much
BUMP_DAY = 12                    # provider fingerprint bump lands this day
K_AUDIT = 5

month_runs = RUNS_PER_DAY * DAYS
tok_cost = month_runs * TOK_PER_RUN * PRICE_PER_MTOK / 1e6


def audit_estimate(r, bumped):
    per = []
    for _, d in PAYLOADS:
        dd = max(0.05, d - (DRIFT if bumped else 0.0))
        hits = sum(1 for _ in range(K_AUDIT) if r.random() < attack_prob(dd, T_SERVE))
        per.append(hits / K_AUDIT)
    return sum(per) / len(per)


# noise floor: trip rate on the UNBUMPED model, and post-bump trip rate
rngN = random.Random(605)
pre = [audit_estimate(rngN, bumped=False) for _ in range(1000)]
post = [audit_estimate(rngN, bumped=True) for _ in range(1000)]
q_pre = sum(1 for e in pre if e > mean_asr + DETECT_JUMP) / 1000
q_post = sum(1 for e in post if e > mean_asr + DETECT_JUMP) / 1000
bump_asr = sum(attack_prob(max(0.05, d - DRIFT), T_SERVE) for _, d in PAYLOADS) / len(PAYLOADS)
print(f"suite ASR: {mean_asr:.4f} -> {bump_asr:.4f} after the bump (+{bump_asr - mean_asr:.4f})")
print(f"trip prob at band +{DETECT_JUMP}: pre-bump {q_pre:.3f}, post-bump {q_post:.3f}")
exp_runs = 1.0 / q_post
print(f"expected samples to first post-bump trip: {exp_runs:.1f}")

# C1: T=0.7 single-run gate - every red is sampling noise on a frozen model.
rng5 = random.Random(601)
reds1 = sum(1 for _ in range(month_runs) if run_suite(T_SERVE, rng5) > 0)
tri1 = reds1 * TRIAGE_MIN / 60.0 * ENG_RATE
risk1 = REGRESSION_COST                       # a real bump hides among the noise reds
print(f"C1 T=0.7 single-run : {reds1}/{month_runs} red verdicts on a frozen model"
      f" -> ${tri1 + risk1 + tok_cost:,.2f} (triage ${tri1:,.2f} + risk ${risk1:.2f})")

# C2: T=0 single-run gate - silent, blind to sampled-path attacks.
rng5 = random.Random(602)
reds2 = sum(1 for _ in range(month_runs) if run_suite(0.0, rng5) > 0)
print(f"C2 T=0 single-run   : {reds2}/{month_runs} red verdicts, the bump invisible"
      f" -> ${REGRESSION_COST + tok_cost:,.2f} (risk ${REGRESSION_COST:.2f})")

# C3: T=0.7 pass@5 gate on every push - detection in ~exp_runs pushes (~hours).
rng6 = random.Random(603)
false_red3 = 0
caught3 = 0
for run_i in range(month_runs):
    est = audit_estimate(rng6, bumped=run_i >= RUNS_PER_DAY * (BUMP_DAY - 1))
    if est > mean_asr + DETECT_JUMP:
        if run_i >= RUNS_PER_DAY * (BUMP_DAY - 1):
            caught3 += 1
        else:
            false_red3 += 1
tri3 = false_red3 * TRIAGE_MIN / 60.0 * ENG_RATE
tok3 = tok_cost * K_AUDIT
post_n3 = month_runs - RUNS_PER_DAY * (BUMP_DAY - 1)
risk3 = REGRESSION_COST * (1.0 - q_post) ** post_n3
lat3 = exp_runs / RUNS_PER_DAY * 24
print(f"C3 T=0.7 pass@5 push: false reds {false_red3}, post-bump trips {caught3}/{post_n3},"
      f" detect ~{lat3:.1f} h -> ${tri3 + risk3 + tok3:,.2f} (triage ${tri3:,.2f} + risk ${risk3:.2f})")

# C4: T=0 gate in CI + one nightly pass@5 audit.
rng7 = random.Random(604)
ci_reds4 = sum(1 for _ in range(month_runs) if run_suite(0.0, rng7) > 0)
false_red4 = 0
caught4 = 0
for night in range(1, DAYS + 1):
    est = audit_estimate(rng7, bumped=night >= BUMP_DAY)
    if est > mean_asr + DETECT_JUMP:
        if night >= BUMP_DAY:
            caught4 += 1
        else:
            false_red4 += 1
tri4 = false_red4 * TRIAGE_MIN / 60.0 * ENG_RATE
tok4 = tok_cost + DAYS * TOK_PER_RUN * K_AUDIT * PRICE_PER_MTOK / 1e6
post_n4 = DAYS - BUMP_DAY + 1
risk4 = REGRESSION_COST * (1.0 - q_post) ** post_n4
print(f"C4 T=0 CI + nightly : CI {ci_reds4} reds (frozen model), nightly trips {caught4}/{post_n4},"
      f" detect ~{exp_runs:.1f} d -> ${tri4 + risk4 + tok4:,.2f} (triage ${tri4:,.2f} + risk ${risk4:.2f})")
```

The ledger's four rows are four different failures. C1, the suite at serving temperature with a per-push verdict, burns **$13,725.79**: 420 of 660 runs go red on a frozen model, every red costs 25 minutes of triage, and the one real bump of the month is indistinguishable from the noise it hides among — [7104's deletion law](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) fires within the week. C2, the T=0-only gate, costs $600.79 and delivers zero reds across 660 runs — 100 percent silent, including on the day the bump moves suite ASR from 0.1347 to 0.3558. C3, pass@5 on every push, catches the bump within ~0.8 hours (post-bump trip probability 0.969 per run) but pays $812.50 in false-red triage: the pre-bump noise floor at band +0.08 is 7.5 percent per run, 26 spurious pages a month. C4, T=0 in CI plus one nightly pass@5 audit, costs **$63.42** — CI reds 0, the nightly trips 11/11 after the bump, detection in about one day, two false pages total. The trade C3 buys for 13x the money is latency in hours instead of days, and the ledger's honest reading is that both sampled configs catch the bump because the band (+0.08) sits under the bump's move (+0.2211) and over the k=5 noise floor (0.0521 std) — a band chosen between those two numbers is the actual engineering decision, and the fence's noise-floor block is how it gets chosen instead of guessed.

## Known Failure Modes

| Failure | Symptom | Fix |
|---------|---------|-----|
| Verdict gate on a T=0.7 suite | 33 red / 17 green across identical-code runs; the gate fails on noise | T=0 for per-push verdicts; sampled rates only as pass@k estimates against a band |
| Believing "temperature=0 is deterministic" | Qwen3-235B at T=0: 80 unique outputs in 1,000 completions (batch-variant kernels) | Batch-invariant serving, or self-hosted pinned kernels; verify with a duplicate-run probe |
| Treating the seed parameter as a guarantee | OpenAI: "(mostly) deterministic"; a fingerprint bump moves outputs at the same seed | Record `system_fingerprint` per run; re-run and re-bless the baseline when it changes |
| Scoring the suite only at T=0 | Suite ASR 0.0000 while the sampled path sits at 0.1347 — a different, safer model than attackers face | T=0 in CI, sampled pass@k on a schedule — both regimes, both reported |
| Near-tie margins trusted as stable | Gap 0.02 flips 338/400 under B=32 noise; gap 0.50 flips 0/400 | Flag decisions whose top-2 logit gap sits inside the serve-time noise scale |
| Provider drift treated as a test bug | Fingerprint drift flips 3/7 greedy decisions; no code changed | Diff outputs on fingerprint change, then re-bless; never blame the suite first |
| Sampled gate without the variance law | k=1 std 0.1169 read as a regression signal bigger than the 0.1347 suite mean | Match the band to the noise: `std x sqrt(k)` (holds 0.1166-0.1207 here) must sit under the band |
| Exact-string asserts across model versions | Same assert, new fingerprint, red CI with a compliant model | Assert on the decoded decision class, never on the sampled surface text |

## Summary

- The sampler is the only random part: at T=0 the 2,000-draw walk produces 1 unique output (greedy share 1.0000); at T=0.7 it produces 4 with the greedy token at 0.6760 — temperature zero is argmax, and argmax is the only determinism the knob buys.
- A frozen model at T=0.7 flaps the suite 33 red / 17 green over 50 identical-code runs (P(clean run) = 0.3436); at T=0 the same suite stands 50/50 green — silence, not safety.
- Temperature zero does not buy the provider: simulated batch noise flips 0/7 real decisions but 338/400 at gap 0.02, and a fingerprint bump modeled at drift 1.30 flips 3/7 greedy decisions with zero code changes.
- pass@k prices the honest middle: `std x sqrt(k)` holds at 0.1169-0.1207 across k = 1..10, so k=10 buys std 0.0382 — the noise floor any sampled gate's band must clear.
- One month of CI prices the four configs: T=0.7 single-run $13,725.79 (420/660 noise reds), T=0 single-run $600.79 (0 reds, the 0.1347-to-0.3558 bump invisible), pass@5 per push $816.46 (detect ~0.8 h, 26 false reds), T=0 CI + nightly pass@5 $63.42 (11/11 nightly trips, detect ~1 d) — the deployable stack runs both regimes.

## References

### Related Minder Academy Documents

- [7501: Prompt Injection Defense](7501-Prompt-Injection-Defense.md) — the four-layer pipeline and red-team regression suite this lesson makes reproducible
- [7502: PII Redaction & Privacy Filtering](7502-PII-Redaction.md) — the detector layering whose verdicts inherit the same decoding stability
- [7503: Adversarial Attacks & Defense](7503-Adversarial-Attacks.md) — robustness evaluation and the serve-time pipeline these tests gate
- [7504: Agent Abuse Prevention and Identity Threats](7504-Agent-Abuse-Prevention-and-Identity-Threats.md) — the traffic-side mechanics where deterministic detector thresholds meet sampled traffic
- [7104: Agent Evaluation and Observability](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) — the regression gate and its pin-sampling caveat, implemented here as arithmetic
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) — the serving stacks whose sampling parameters this lesson pins

### Primary Sources

- [Transformers generation strategies](https://huggingface.co/docs/transformers/en/generation_strategies) — "Greedy search is the default decoding strategy. It selects the next most likely token at each step"
- [OpenAI Cookbook: reproducible outputs with the seed parameter](https://developers.openai.com/cookbook/examples/reproducible_outputs_with_the_seed_parameter) — "(mostly) deterministic outputs" with same seed and identical parameters
- [Azure OpenAI: reproducible output](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/how-to/reproducible-output) — determinism is best-effort; outputs can differ even with the same seed and `system_fingerprint`
- [vLLM `sampling_params`](https://docs.vllm.ai/en/latest/api/vllm/sampling_params/) — "Zero temperature means greedy sampling", with `top_p` forced to 1.0 at the same branch
- [Thinking Machines Lab: Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) (He et al., 2025) — Qwen3-235B at T=0: 80 unique outputs in 1,000 completions; batch-invariant kernels close it
- Ouyang, Zhang, Harman & Wang, *An Empirical Study of the Non-determinism of ChatGPT in Code Generation* ([arXiv 2308.02828](https://arxiv.org/abs/2308.02828)) — "setting the temperature to 0 does not guarantee determinism in code generation"
- Chen et al., *Evaluating Large Language Models Trained on Code* ([arXiv 2107.03374](https://arxiv.org/abs/2107.03374)) — the unbiased pass@k estimator

## Next Steps

- **Next Module:** continue with [assessment/QUIZ.md](assessment/QUIZ.md) — Q17 is the question this lesson's fences answer with mechanics
- **Continue with:** [7104: Agent Evaluation and Observability](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) — the regression gate whose pin-sampling caveat this lesson turns into a priced design
- **Assessment:** extend the campaign fence with a fifth config — T=0 CI plus a pass@20 nightly — and price whether the tighter noise floor justifies four times the audit tokens
