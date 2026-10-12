---
Document ID: CHEAT-SHEET-045
Title: "CHEAT-SHEET-045: Synthetic Data & Advanced Training - the Distilled Student, the Federated Fleet, and the Recursion Tax"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'synthetic-data', 'distillation', 'distributed']
---

# CHEAT-SHEET-045: Synthetic Data & Advanced Training - the Distilled Student, the Federated Fleet, and the Recursion Tax

The synthetic-and-advanced-training surface lives in phase5-finetuning's 5300-synthetic track: 5301 Knowledge Distillation, 5302 Distributed Training, 5303 Federated Learning and 5304 Self-Instruct and Model Collapse - four modules whose single-page closure is this sheet. CHEAT-SHEET-016 owns the LoRA adapter layer above; what no sheet owned yet is the two-axis question this track actually asks: what data the model is trained on (distilled teacher outputs, self-instruct recursion, the model collapse it causes, the downstream mixtures it feeds) and where the training physically happens (one box, a fleet of GPUs, a federation of private clients that can never ship raw data). Everything below is priced - every number quoted is printed by the canonical fence at the bottom of the page.

The sheet runs as seven exhibits: F1 distillation's temperature and blend, F2 federated averaging and its drift bill, F3 the fleet arithmetic, F4 DP-SGD and the adapter bandwidth, F5 the self-instruct bootstrap, F6 the model-collapse walk with its ten-percent anchor, and F7 the downstream scheme plus the four-bill campaign. Each exhibit gets a short section here with its tables and its quoted law; the full 396-line stdlib fence reproduces all seven from fixed seeds, and its 56-line output sits frozen below it byte-for-byte.

## Knowledge Distillation - the Temperature and the Blend

Distillation moves the teacher's soft distribution, not its argmax. Soften the logits [8.0, 3.5, 2.1, 0.4, -1.2] and the mass walks out with T: T=1 keeps top 0.986 with dark mass 0.014, T=5 drops top to 0.478 while dark mass rises to 0.522, T=20 flattens to top 0.259 and dark 0.741. The transfer happens in the middle regime. On the same logits the hard-label CE is 0.0143, the teacher-student KL at T=5 is 0.0108, and the canonical Hinton blend prices it as 0.5 x KL x T^2 + 0.5 x CE = 0.5 x 0.2697 + 0.5 x 0.0143 = 0.1420 - the T^2 factor restores the gradient scale the temperature flattening diluted. Multi-teacher blends average the soft distributions themselves: the 0.6/0.4 mix lands top 0.451 with dark 0.549, mass both teachers own. Self-distillation freezes the teacher as an EMA of past students: over 5 steps the live student moved +0.050 while its EMA teacher moved +0.000150 - frozen by design, exactly the drift the method forbids.

| Temperature | Top prob | Dark mass |
| --- | --- | --- |
| T=1 | 0.986 | 0.014 |
| T=5 | 0.478 | 0.522 |
| T=20 | 0.259 | 0.741 |

| Route | Signal | Priced | Use when |
| --- | --- | --- | --- |
| Hard-label CE | argmax only | CE 0.0143 | teacher labels are gold and scarce |
| Soft KL at T=5 | full distribution | KL 0.0108 x T^2 = 0.2697 | dark knowledge is the point |
| Canonical blend | both | 0.1420 at alpha 0.5 | the default Hinton recipe |
| Multi-teacher 0.6/0.4 | mixed soft | top 0.451, dark 0.549 | no single teacher dominates |

```text
The temperature law: T reshapes the teacher's mass - T=1 is the hard-label
regime (top 0.986, dark 0.014), T=5 is the transfer regime (top 0.478, dark
0.522), T=20 is the flat regime (top 0.259, dark 0.741). Distillation happens
in the transfer regime: the blend 0.5*KL*T^2 + 0.5*CE = 0.1420 carries BOTH.
```

## Federated Averaging - the Weighted Fleet and Its Drift

Federated averaging weights by samples, not by clients. Three clients at n = 500, 300 and 200 average to [1.1850, 0.8550] under n-weighting but [1.2000, 0.8833] unweighted - without the n split the 200-sample client pulls as hard as the 500. Running statistics stay integers on purpose: num_batches_tracked = 142 is carried as-is and never averaged, because averaging a count of batches is meaningless. Non-IID drift is the bill: a client at [1.32, 0.95] against the global [1.1850, 0.8550] pays the FedProx penalty (mu/2) x norm(w - wg)^2 = 0.025 x 0.02725 = 0.000681 on a local loss of 0.4000, landing 0.400681 - small mu anchors the client to the fleet, large mu detaches it, and 5303's mitigation order is FedProx mu 0.01-0.1 first, then local epochs E=1, then SCAFFOLD, then server momentum.

| Strategy | Mechanism | Non-IID answer | Cost |
| --- | --- | --- | --- |
| FedAvg | sample-weighted mean | none by itself | the drift bill above |
| FedProx | (mu/2) x prox term | mu 0.01-0.1 anchors locals | slightly slower convergence |
| SCAFFOLD | control variates | corrects client drift explicitly | 2x state on the wire |
| FedAvgM | server momentum | smooths the aggregated direction | one more hyperparameter |

```text
FedAvg weights by samples: [1.1850, 0.8550] weighted vs [1.2000, 0.8833]
unweighted - the 200-sample client pulls as hard as the 500 unless n says
otherwise. int buffers (num_batches_tracked = 142) are carried, never averaged.
```

## Distributed Training - the Fleet Arithmetic

The batch identity is checked before anything scales: 4 micro-batches x 2 accumulation steps x 4 ranks = 32 global batch, and that product must equal train_batch or the schedule silently trains a different problem. Speedup curves are Amdahl-priced, not GPU-counted: measuring 1.7x on 2 GPUs implies serial fraction s = 0.176, measuring 3.0x on 4 implies s = 0.111 - and s = 0.176 predicts N=2 at 1.70x (85% efficiency), N=4 at 2.62x (65%) and N=8 at 3.58x (45%). FSDP wrap policy is arithmetic too: at the 100,000-parameter threshold a 4-layer, d=256 model wraps 5 units - the residual attention stack at 262,144 plus four MLPs at 524,288 each - and the 2,615,296-parameter model shards to 1.31 MB of bf16 weights per GPU on 4-way FULL_SHARD. The 5302 lab numbers back the plan: the DDP-gloo smoke walk descends loss 1.2227 -> 1.1562 -> 1.0949, gradient accumulation matches the single-batch gradient to max diff 1.49e-08, and QLoRA on a single GPU pins device_map = {'': 0} - 'auto' is the answer that silently shards across the bus you meant to keep free, with PEFT's trainable census at 8,192 of 123,200 parameters = 6.6494%.

| Approach | What it splits | Watch for |
| --- | --- | --- |
| DDP | gradients only, replicated model | every rank holds every weight |
| FSDP FULL_SHARD | params, grads, optimizer states | all-gather before each forward |
| ZeRO stage 2 | optimizer + gradient partition | warmup 100 steps on the 32 batch |

| N GPUs | Predicted speedup (s=0.176) | Efficiency |
| --- | --- | --- |
| 2 | 1.70x | 85% |
| 4 | 2.62x | 65% |
| 8 | 3.58x | 45% |

```text
The fleet identity first: micro x accum x ranks must equal train_batch (4x2x4
= 32). Amdahl prices the ceiling: measured 1.7x at N=2 implies s=0.176, and
that s predicts N=8 at 3.58x - 45% efficiency is the honest quote, not 8x.
```

## Differential Privacy - the Clip, the Noise, the Adapter

DP-SGD privatizes per sample, never per batch: the five per-sample norms [2.3, 0.8, 3.1, 0.5, 1.9] clip at C=1.0 by factors [0.435, 1.0, 0.323, 1.0, 0.526] to [1.0, 0.8, 1.0, 0.5, 1.0], the noised sum lands 5.1702 = clipped 4.3 + one N(0, sigma^2 C^2) draw at +0.8702, and the average 1.0340 is the only thing that leaves the client (Abadi 2016's per-sample contract). The classic bug is clipping the batch mean: 1.72 clipped to 1.0 bounds the MEAN only - the 3.1-norm sample still enters the sum unbounded and no epsilon statement survives it. The bandwidth answer is the adapter: a rank-16 adapter over 4 projections x 36 blocks is 37,748,736 parameters = 38 MB against 14,000 MB of full fp16 - 371x less shipped per round trip, which is why FedLoRA at rank 16 moves ~40 MB while a full fine-tune moves ~14 GB.

| Step | Operation | Ledger | Trap |
| --- | --- | --- | --- |
| Clip | min(1, C/norm) per sample | factors [0.435, 1.0, 0.323, 1.0, 0.526] | batch-mean clip bounds the mean only |
| Noise | N(0, sigma^2 C^2) on the sum | +0.8702 draw on clipped 4.3 | noise scales with C, not the mean |
| Average | noised sum over the batch | 5.1702 / 5 = 1.0340 | the average leaves, never the sum |
| Ship | the adapter, not the model | 38 MB vs 14,000 MB = 371x | a full fine-tune ships everything |

```text
DP-SGD clips PER SAMPLE: factors [0.435, 1.0, 0.323, 1.0, 0.526], clipped sum
4.3, noised 5.1702 -> avg 1.0340. The batch-mean 1.72 clipped to 1.0 bounds the
MEAN only - the 3.1 sample still enters the sum unbounded. Abadi 2016.
```

## Self-Instruct - the Bootstrap and the Filter

Self-instruct bootstraps instructions from instructions: 16 seed tasks, 3 rounds x 40 candidates, each candidate a mutation of a pool member (0.15 seed-bias back to the originals, synonym swaps, prefix and constraint rolls). The filter IS the design: every candidate must clear Jaccard 0.7 against the whole pool, and the rejection curve does the curation - round 1 keeps 14 of 40 (pool 30), round 2 keeps 10 (pool 40), round 3 keeps 8 (pool 48), a keep-rate of 32/120 = 0.267. The vocabulary census says what the recursion actually creates: 74 seed tokens become 92 pool tokens, 18 new - recombination, not invention.

| Round | Candidates | Kept | Pool after |
| --- | --- | --- | --- |
| 1 | 40 | 14 | 30 |
| 2 | 40 | 10 | 40 |
| 3 | 40 | 8 | 48 |

```text
The bootstrap is a filter-rejection curve: 120 candidates keep 32 (0.267), the
pool grows 16 -> 48, the vocabulary grows 74 -> 92 (18 new) - recombination,
not invention. Below the 0.7 Jaccard bar is the ONLY thing admitted.
```

## Model Collapse - the Walk and the Ten-Percent Anchor

Model collapse is what the recursion does ungated: a 2000-vocab Zipf corpus resampled from its own empirical distribution walks types 1082 -> 847 -> 711 -> 622 -> 557 over four cycles, tail mass beyond rank 1500 walks 154 -> 121 -> 94 -> 79 -> 70, singletons 548 -> 291 -> 175 -> 127 -> 100 - Shumailov's tail-first order (Nature 631, 2024) is exactly this ledger's shape. The ten-percent anchor is the pairing experiment: at each cycle 10% of the corpus is re-drawn from the real Zipf and 90% resampled from the mix - anchored types 880 / 772 / 708 / 686 against paired control 823 / 688 / 595 / 521, tails 115 / 86 / 80 / 72 against 97 / 72 / 62 / 50. The pair-matched delta at gen 4 is +165 types and +22 tail: control loses 302 types while anchored loses 194 - the slope is flattened, never zeroed; the anchor is a rate you pay every cycle, not a one-time cure.

| Cycle | Types | Tail | Singletons |
| --- | --- | --- | --- |
| gen 0 | 1082 | 154 | 548 |
| gen 1 | 847 | 121 | 291 |
| gen 2 | 711 | 94 | 175 |
| gen 3 | 622 | 79 | 127 |
| gen 4 | 557 | 70 | 100 |

| Cycle | Anchored types | Anchored tail | Control types | Control tail |
| --- | --- | --- | --- | --- |
| gen 1 | 880 | 115 | 823 | 97 |
| gen 2 | 772 | 86 | 688 | 72 |
| gen 3 | 708 | 80 | 595 | 62 |
| gen 4 | 686 | 72 | 521 | 50 |

```text
Ungated resampling walks types 1082 -> 847 -> 711 -> 622 -> 557 and tail mass
154 -> 70 in four cycles. Ten percent real anchors buy +165 types and +22 tail
at gen 4 - the slope is flattened, never zeroed; the anchor is a rate, not a cure.
```

## The Downstream Scheme and the Four-Bill Campaign

The downstream scheme prices the data itself: 300 gold + 200 holdout on a 3-class support-ticket task with a ridge-linear classifier, and the mixtures say depth-1 synthetic is a mild win - gold-only 0.755, plus-gen1 0.760 (+0.005) - while depth-3 synthetic is a loss at 0.620 (-0.135) and pure-gen3 lands 0.130 against 3-class chance 0.333. The keyword-flip probability is the mechanism: at generation depth 3 the true keyword is swapped to a wrong class 80% of the time, so the synthetic data teaches the wrong map. The four-bill campaign on the 52,445-instruction scale: human writing $524,450 at $10 each, self-instruct generation $1,603 (149,843 candidates at the 0.350 keep Wang et al. measured, arXiv 2212.10560), the ten-percent anchor surcharge $52,440 lifting the total to $54,043, and the ungated collapse tax $238,608 - 1077 types decaying to 587 (0.455 gone) across 3 ungated cycles, re-collected at the human rate. Generation is 327x cheaper than writing, the anchor is 33x the generation bill, and skipping both costs 4.4x the anchored bill. One citation trap from 5304 travels with this ledger: the 52k-instruction dataset is Peng et al.'s self-instruct expansion reached through the Stanford CRFM blog - the Alpaca arXiv page (2304.03277) itself carries no dataset.

| Mixture | Holdout accuracy | Delta | Reading |
| --- | --- | --- | --- |
| gold only (300) | 0.755 | - | the human baseline |
| gold + gen-1 synthetic (800) | 0.760 | +0.005 | depth-1 recursion is a mild win |
| gold + gen-3 synthetic (800) | 0.620 | -0.135 | depth-3 flips keywords 80% of the time |
| pure gen-3 (800) | 0.130 | -0.625 | below 3-class chance 0.333 - the wrong map |

| Bill | Amount | Mechanism |
| --- | --- | --- |
| human-written | $524,450 | 52,445 instructions at $10 each |
| self-instruct | $1,603 | 149,843 candidates at 0.350 keep + $30 filter |
| anchored total | $54,043 | +$52,440 buys 5,244 real at the 10% anchor |
| ungated collapse | $238,608 | 1077 -> 587 types, re-collected at the human rate |

```text
The four bills: human $524,450, self-instruct $1,603 (327x), anchor $52,440
(33x generation, total $54,043), the ungated collapse $238,608 (4.4x the
anchored bill). Gating is cheaper than re-collection at every ratio quoted.
```

```text
Decision rules: distill at T=3-5 with the 0.5/0.5 blend; distribute with the
batch identity and quote Amdahl, never the GPU count; privatize per sample
with C and noise, never per batch; generate synthetically behind an anchor
and a filter - the ungated recursion costs 4.4x the anchored bill.
```

```text
Pipeline: (1) plan the fleet - micro x accum x ranks = global batch, FSDP wrap
at the 100k threshold; (2) choose the data route - distill at T=5 blend 0.5, or
self-instruct 16 seeds 3 rounds; (3) gate the recursion - 10% real anchor, 0.7
Jaccard filter, holdout delta checked every cycle; (4) bill the campaign.
```

## The Canonical Fence

The 396-line fence reproduces every number on this page from fixed seeds (F5 bootstrap 111, F6 walks 202 and 303, F4 noise 404, F7 mixtures 601-604 and the collapse tax 505) using the standard library only: softmax and KL for F1, FedAvg and the prox term for F2, the Amdahl fit and the FSDP wrap planner for F3, per-sample clipping with one Gaussian draw for F4, the Jaccard-filtered mutate loop for F5, the Zipf resample walk with and without the anchor for F6, and the ridge-linear downstream scheme with the four-bill ledger for F7. Its output ran twice under the probe environment and was asserted byte-identical before freezing; the 56 lines below are that frozen output, ending in the FENCE-045-OK tail the live probe greps for.

```python
"""CHEAT-SHEET-045 canonical fence: the 5300 synthetic-data surface in seven
priced exhibits - distillation's temperature and blend (F1), federated
averaging and its drift bill (F2), the fleet arithmetic (F3), DP-SGD and the
adapter bandwidth (F4), the self-instruct bootstrap (F5), the model-collapse
walk with its ten-percent anchor (F6), and the downstream scheme plus the
four-bill campaign (F7). Stdlib only, fixed seeds, deterministic output.
"""
import math
import random
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")


def softmax(z, t):
    m = max(v / t for v in z)
    e = [math.exp(v / t - m) for v in z]
    s = sum(e)
    return [x / s for x in e]


def kl(p, q):
    return sum(pi * math.log(pi / qi)
               for pi, qi in zip(p, q) if pi > 0.0)


# ---------------------------------------------------------------- F1
print("F1 distillation: temperature, dark knowledge, blended loss")
LOGITS = [8.0, 3.5, 2.1, 0.4, -1.2]
GOLD = 0
TEACH5 = softmax(LOGITS, 5)
for label, T in (("T=1", 1), ("T=5", 5), ("T=20", 20)):
    p = softmax(LOGITS, T)
    print(f"{label}: top {max(p):.3f} | dark mass {1.0 - max(p):.3f} "
          f"| second {sorted(p)[-2]:.3f}")
ce_hard = -math.log(softmax(LOGITS, 1)[GOLD])
STUDENT = softmax([6.8, 3.1, 2.5, 0.7, -0.5], 5)
kl5 = kl(TEACH5, STUDENT)
ALPHA, TB = 0.5, 25.0
blend = ALPHA * kl5 * TB + (1.0 - ALPHA) * ce_hard
print(f"hard-label CE {ce_hard:.4f} | KL(T=5) {kl5:.4f} x T^2 = {kl5 * TB:.4f}")
print(f"blend a=0.5: 0.5*{kl5 * TB:.4f} + 0.5*{ce_hard:.4f} = {blend:.4f}")
mix = [0.6 * a + 0.4 * b for a, b in
       zip(TEACH5, softmax([7.0, 4.2, 1.6, 0.9, -0.3], 5))]
print(f"multi-teacher 0.6/0.4 soft mix: top {max(mix):.3f}, dark "
      f"{1.0 - max(mix):.3f}")
ema = 0.5
w = 0.5
for _ in range(5):
    w += 0.01
    ema = 0.999 * ema + 0.001 * w
print(f"self-distill EMA m=0.999 over 5 steps: student moved +{w - 0.5:.3f}, "
      f"teacher moved +{ema - 0.5:.6f} (frozen by design)")

print()

# ---------------------------------------------------------------- F2
print("F2 FedAvg: sample weighting, int buffers, FedProx penalty")
CLIENTS = [([1.20, 0.85], 500), ([1.05, 0.70], 300), ([1.35, 1.10], 200)]
tot_n = sum(n for _, n in CLIENTS)
wavg = [sum(w[d] * n for w, n in CLIENTS) / tot_n for d in (0, 1)]
uavg = [sum(w[d] for w, _ in CLIENTS) / len(CLIENTS) for d in (0, 1)]
print(f"sample-weighted avg: [{wavg[0]:.4f}, {wavg[1]:.4f}] "
      f"(n split {', '.join(str(n) for _, n in CLIENTS)}/{tot_n})")
print(f"unweighted avg:      [{uavg[0]:.4f}, {uavg[1]:.4f}] - the "
      f"200-sample client pulls as hard as the 500")
print("int buffer num_batches_tracked = 142 carried as-is, never averaged")
DRIFTED = [1.32, 0.95]
MU = 0.05
prox = MU / 2.0 * sum((DRIFTED[d] - wavg[d]) ** 2 for d in (0, 1))
print(f"non-IID drift to [1.32, 0.95]: local loss 0.4000 + (mu/2)*||w-wg||^2"
      f" = 0.4000 + {prox:.6f} -> {0.4 + prox:.6f}")

print()

# ---------------------------------------------------------------- F3
print("F3 fleet arithmetic: batch identity, Amdahl, FSDP wrap planner")
micro, accum, ws_ranks = 4, 2, 4
print(f"deepspeed identity: {micro} micro x {accum} accum x {ws_ranks} ranks"
      f" = {micro * accum * ws_ranks} global batch (must equal train_batch)")


def amdahl(s, n):
    return 1.0 / (s + (1.0 - s) / n)


for label, measured in (("2x GPU", 1.7), ("4x GPU", 3.0)):
    n = int(label.split("x")[0])
    s_fit = (1.0 / measured - 1.0 / n) / (1.0 - 1.0 / n)
    print(f"{label}: measured {measured:.1f}x -> implied serial fraction "
          f"{s_fit:.3f}")
S = 0.176
for n in (2, 4, 8):
    sp = amdahl(S, n)
    print(f"predict s={S}: N={n} -> {sp:.2f}x speedup, {sp / n:.0%} efficiency")
dim, layers, n_vocab = 256, 4, 1000
attn_p = dim * dim
mlp_p = dim * 4 * dim + 4 * dim * dim
head_p = dim * n_vocab
THRESH = 100_000
total_p = layers * (attn_p + mlp_p) + head_p
resid = layers * attn_p
units = [(f"blocks.{i}.mlp", mlp_p) for i in range(layers)]
if resid >= THRESH:
    units.insert(0, ("blocks (residual attn)", resid))
print(f"wrap threshold {THRESH:,}: {len(units)} units -> "
      + ", ".join(f"{nm} {n:,}" for nm, n in units))
print(f"model {total_p:,} params | bf16 weights/GPU on 4-way FULL_SHARD: "
      f"{total_p * 2 / 4 / 1e6:.2f} MB")

print()

# ---------------------------------------------------------------- F4
print("F4 DP-SGD: per-sample clip, noised sum, the adapter bill")
G = [2.3, 0.8, 3.1, 0.5, 1.9]
C, SIGMA = 1.0, 1.0
clipped = [min(g, C) for g in G]
factors = [min(1.0, C / g) for g in G]
noise = random.Random(404).gauss(0.0, SIGMA * C)
noised = sum(clipped) + noise
print(f"per-sample norms {G}")
print(f"clip to C={C:.0f}: factors {[round(f, 3) for f in factors]} -> "
      f"clipped {clipped}")
print(f"noised sum {noised:.4f} (clipped sum {sum(clipped):.1f} + "
      f"N(0, sigma^2*C^2) draw {noise:+.4f}) -> avg {noised / len(G):.4f}")
print(f"batch-mean norm {sum(G) / len(G):.2f} clipped to 1.0 bounds the MEAN"
      f" only - the 3.1 sample still enters the sum unbounded")
params = 16 * (4096 + 4096) * 4 * 36 * 2
adapter_mb = params / 1e6
print(f"rank-16 adapter, 4 projections x 36 blocks: {params:,} params = "
      f"{adapter_mb:.0f} MB vs 14,000 MB full fp16 = "
      f"{14000 / adapter_mb:.0f}x less per round trip")

print()

# ---------------------------------------------------------------- F5
print("F5 self-instruct: the bootstrap and its filter-rejection curve")
SEEDS = [
    "Rewrite this sentence in passive voice",
    "Summarize the paragraph in three words",
    "Classify the review as positive or negative",
    "Translate the idiom into plain English",
    "List three uses for a paperclip",
    "Explain recursion to a ten year old",
    "Convert the date into ISO format",
    "Find the grammatical error in the sentence",
    "Write a haiku about the ocean",
    "Extract all proper nouns from the text",
    "Sort these numbers in descending order",
    "Rate the sentiment of the tweet",
    "Check whether the parentheses are balanced",
    "Sum the even numbers in the list",
    "Give two synonyms for the adjective",
    "Draft a reply declining the invitation",
]
PREFIXES = ["Step by step, ", "In one paragraph, ", "As a table, "]
CONSTRAINTS = ["for a beginner", "without examples", "in formal tone",
               "with a worked case"]
SWAPS = [("Rewrite", "Rephrase"), ("Explain", "Describe"),
         ("List", "Enumerate"), ("Find", "Locate"),
         ("Summarize", "Condense"), ("Classify", "Categorize")]


def toks(s):
    return set(s.lower().split())


def jac(a, b):
    ta, tb = toks(a), toks(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def mutate(s, r):
    for a, b in SWAPS:
        if s.startswith(a) and r.random() < 0.5:
            s = b + s[len(a):]
            break
    if r.random() < 0.5:
        s = r.choice(PREFIXES) + s[0].lower() + s[1:]
    if r.random() < 0.6:
        s = s + " " + r.choice(CONSTRAINTS)
    return s


rng = random.Random(111)
POOL = list(SEEDS)
THRESH_J = 0.7
tot_gen = tot_keep = 0
for rnd in (1, 2, 3):
    kept = 0
    for _ in range(40):
        src = POOL[0] if rng.random() < 0.15 else rng.choice(POOL)
        cand = mutate(src, rng)
        tot_gen += 1
        if max(jac(cand, p) for p in POOL) < THRESH_J:
            POOL.append(cand)
            kept += 1
            tot_keep += 1
    print(f"round {rnd}: 40 candidates, kept {kept}, dropped {40 - kept}, "
          f"pool {len(POOL)}")
seed_toks = set().union(*[toks(s) for s in SEEDS])
pool_toks = set().union(*[toks(s) for s in POOL])
print(f"final: {len(POOL)} instructions from {len(SEEDS)} seeds, keep-rate "
      f"{tot_keep}/{tot_gen} = {tot_keep / tot_gen:.3f}")
print(f"vocabulary: {len(seed_toks)} seed tokens -> {len(pool_toks)} pool "
      f"tokens ({len(pool_toks - seed_toks)} new) - recombination, not "
      f"invention")

print()

# ---------------------------------------------------------------- F6
print("F6 model collapse: the walk and the ten-percent anchor")
V, N, TAIL = 2000, 5000, 1501
ws_raw = [1.0 / (i + 1) for i in range(V)]
tot_w = sum(ws_raw)
ws = [w / tot_w for w in ws_raw]


def zipf(n, r):
    return [r.choices(range(V), weights=ws)[0] for _ in range(n)]


def resample(s, n, r):
    cnt = Counter(s)
    return r.choices(list(cnt), weights=list(cnt.values()), k=n)


def row(s):
    cnt = Counter(s)
    st = set(s)
    tails = sum(1 for w in st if w >= TAIL)
    singles = sum(1 for c in cnt.values() if c == 1)
    return len(st), tails, singles


rng6 = random.Random(202)
s6 = zipf(N, rng6)
walk_rows = [row(s6)]
print(f"gen 0: types {walk_rows[0][0]} tail {walk_rows[0][1]} "
      f"singletons {walk_rows[0][2]}")
for g in (1, 2, 3, 4):
    s6 = resample(s6, N, rng6)
    walk_rows.append(row(s6))
    print(f"gen {g}: types {walk_rows[g][0]} tail {walk_rows[g][1]} "
          f"singletons {walk_rows[g][2]}")


def walk(preserve, seed):
    r2 = random.Random(seed)
    s2 = zipf(N, r2)
    out = []
    for _ in (1, 2, 3, 4):
        n_real = int(N * preserve)
        s2 = resample(s2, N - n_real, r2)
        if n_real:
            s2 = s2 + zipf(n_real, r2)
        out.append(row(s2))
    return out


arows = walk(0.1, 303)
urows = walk(0.0, 303)
print("anchor 10%: " + "  ".join(
    f"g{g} types-{t[0]} tail-{t[1]}" for g, t in zip((1, 2, 3, 4), arows)))
print("paired control: " + "  ".join(
    f"g{g} types-{t[0]} tail-{t[1]}" for g, t in zip((1, 2, 3, 4), urows)))
print(f"pair-matched delta at gen 4: types {arows[3][0] - urows[3][0]:+d}, "
      f"tail {arows[3][1] - urows[3][1]:+d} (control loses "
      f"{urows[0][0] - urows[3][0]} types, anchored loses "
      f"{arows[0][0] - arows[3][0]}) - slope flattened, not zeroed")

print()

# ---------------------------------------------------------------- F7
print("F7 downstream scheme and the four-bill campaign")
CLASSES = {
    "billing": ["refund", "invoice", "charge", "payment"],
    "tech": ["login", "password", "error", "crash"],
    "sales": ["pricing", "demo", "trial", "quote"],
}
FILLERS = ["please", "the", "about", "our", "with", "for", "my", "and"]
CL = list(CLASSES)
P_KW, P_FLIP = 0.6, 0.8


def make_example(label, r, gen):
    kw = r.choice(CLASSES[label])
    fills = [r.choice(FILLERS) for _ in range(6)]
    has_kw = r.random() < P_KW
    if gen >= 3 and has_kw and r.random() < P_FLIP:
        other = r.choice([c for c in CL if c != label])
        kw = r.choice(CLASSES[other])
    toks_ = fills[:3] + ([kw] if has_kw else []) + fills[3:5]
    return toks_, label


def build(n, gen, r):
    X, Y = [], []
    for _ in range(n):
        lab = r.choice(CL)
        t, l = make_example(lab, r, gen)
        X.append(t)
        Y.append(CL.index(l))
    return X, Y


vocab = sorted({w for c in CL for w in CLASSES[c]} | set(FILLERS))
vidx = {w: i for i, w in enumerate(vocab)}


def featurize(toks_):
    v = [0.0] * (len(vocab) + 1)
    for t in toks_:
        if t in vidx:
            v[vidx[t]] += 1.0
    v[-1] = 1.0
    return v


def train(X, Y):
    F = [featurize(x) for x in X]
    d = len(vocab) + 1
    lam = 1.0 * 300.0 / len(X)
    Ws = []
    for k in range(3):
        y = [1.0 if yy == k else -1.0 for yy in Y]
        M = [[sum(a[i] * a[j] for a in F) + (lam if i == j else 0.0)
              for j in range(d)] for i in range(d)]
        b = [sum(a[i] * yy for a, yy in zip(F, y)) for i in range(d)]
        for i in range(d):
            piv = M[i][i]
            for j in range(i + 1, d):
                f = M[j][i] / piv
                for kk in range(i, d):
                    M[j][kk] -= f * M[i][kk]
                b[j] -= f * b[i]
        w = [0.0] * d
        for i in range(d - 1, -1, -1):
            w[i] = (b[i] - sum(M[i][j] * w[j]
                               for j in range(i + 1, d))) / M[i][i]
        Ws.append(w)
    return Ws


def predict(Ws, x):
    a = featurize(x)
    scores = [sum(wi * ai for wi, ai in zip(w, a)) for w in Ws]
    return scores.index(max(scores))


goldX, goldY = build(300, 1, random.Random(601))
hoX, hoY = build(200, 1, random.Random(602))
syn1 = build(800, 1, random.Random(603))
syn3 = build(800, 3, random.Random(604))


def run_mix(gold_n, syn):
    Ws = train(goldX[:gold_n] + syn[0], goldY[:gold_n] + syn[1])
    return sum(1 for x, y in zip(hoX, hoY)
               if predict(Ws, x) == y) / len(hoY)


a_gold = run_mix(300, ([], []))
a_g1 = run_mix(300, syn1)
a_g3 = run_mix(300, syn3)
a_p3 = run_mix(0, syn3)
print(f"gold-only {a_gold:.3f} | +gen1-syn {a_g1:.3f} ({a_g1 - a_gold:+.3f}) "
      f"| +gen3-syn {a_g3:.3f} ({a_g3 - a_gold:+.3f}) | pure-gen3 {a_p3:.3f}"
      f" (3-class chance 0.333)")
INSTR = 52445
KEEP_RUN = 84 / 240
WRITER, FILTER_USD = 10.0, 30.0
human = INSTR * WRITER
cands = INSTR / KEEP_RUN
si = cands * 0.0105 + FILTER_USD
anchor_n = int(INSTR * 0.1)
anchor_bill = anchor_n * WRITER
r9 = random.Random(505)
s9 = zipf(N, r9)
t0 = len(set(s9))
for _ in range(3):
    s9 = resample(s9, N, r9)
lost = (t0 - len(set(s9))) / t0
recollect = lost * human
print(f"human-written ${human:,.0f} | self-instruct ${si:,.0f} "
      f"({cands:,.0f} candidates at {KEEP_RUN:.3f} keep + filter)")
print(f"anchor surcharge ${anchor_bill:,.0f} ({anchor_n} real at 10%) -> "
      f"anchored bill ${si + anchor_bill:,.0f}")
print(f"collapse tax: {t0} types -> {len(set(s9))} in 3 ungated cycles "
      f"({lost:.3f} gone) -> re-collection ${recollect:,.0f}")
print(f"ratios: generation is {human / si:.0f}x cheaper than writing; the "
      f"anchor is {anchor_bill / si:.0f}x the generation bill but the "
      f"ungated collapse costs {recollect / (si + anchor_bill):.1f}x the "
      f"anchored bill")
print("FENCE-045-OK")
```

```text
F1 distillation: temperature, dark knowledge, blended loss
T=1: top 0.986 | dark mass 0.014 | second 0.011
T=5: top 0.478 | dark mass 0.522 | second 0.194
T=20: top 0.259 | dark mass 0.741 | second 0.207
hard-label CE 0.0143 | KL(T=5) 0.0108 x T^2 = 0.2697
blend a=0.5: 0.5*0.2697 + 0.5*0.0143 = 0.1420
multi-teacher 0.6/0.4 soft mix: top 0.451, dark 0.549
self-distill EMA m=0.999 over 5 steps: student moved +0.050, teacher moved +0.000150 (frozen by design)

F2 FedAvg: sample weighting, int buffers, FedProx penalty
sample-weighted avg: [1.1850, 0.8550] (n split 500, 300, 200/1000)
unweighted avg:      [1.2000, 0.8833] - the 200-sample client pulls as hard as the 500
int buffer num_batches_tracked = 142 carried as-is, never averaged
non-IID drift to [1.32, 0.95]: local loss 0.4000 + (mu/2)*||w-wg||^2 = 0.4000 + 0.000681 -> 0.400681

F3 fleet arithmetic: batch identity, Amdahl, FSDP wrap planner
deepspeed identity: 4 micro x 2 accum x 4 ranks = 32 global batch (must equal train_batch)
2x GPU: measured 1.7x -> implied serial fraction 0.176
4x GPU: measured 3.0x -> implied serial fraction 0.111
predict s=0.176: N=2 -> 1.70x speedup, 85% efficiency
predict s=0.176: N=4 -> 2.62x speedup, 65% efficiency
predict s=0.176: N=8 -> 3.58x speedup, 45% efficiency
wrap threshold 100,000: 5 units -> blocks (residual attn) 262,144, blocks.0.mlp 524,288, blocks.1.mlp 524,288, blocks.2.mlp 524,288, blocks.3.mlp 524,288
model 2,615,296 params | bf16 weights/GPU on 4-way FULL_SHARD: 1.31 MB

F4 DP-SGD: per-sample clip, noised sum, the adapter bill
per-sample norms [2.3, 0.8, 3.1, 0.5, 1.9]
clip to C=1: factors [0.435, 1.0, 0.323, 1.0, 0.526] -> clipped [1.0, 0.8, 1.0, 0.5, 1.0]
noised sum 5.1702 (clipped sum 4.3 + N(0, sigma^2*C^2) draw +0.8702) -> avg 1.0340
batch-mean norm 1.72 clipped to 1.0 bounds the MEAN only - the 3.1 sample still enters the sum unbounded
rank-16 adapter, 4 projections x 36 blocks: 37,748,736 params = 38 MB vs 14,000 MB full fp16 = 371x less per round trip

F5 self-instruct: the bootstrap and its filter-rejection curve
round 1: 40 candidates, kept 14, dropped 26, pool 30
round 2: 40 candidates, kept 10, dropped 30, pool 40
round 3: 40 candidates, kept 8, dropped 32, pool 48
final: 48 instructions from 16 seeds, keep-rate 32/120 = 0.267
vocabulary: 74 seed tokens -> 92 pool tokens (18 new) - recombination, not invention

F6 model collapse: the walk and the ten-percent anchor
gen 0: types 1082 tail 154 singletons 548
gen 1: types 847 tail 121 singletons 291
gen 2: types 711 tail 94 singletons 175
gen 3: types 622 tail 79 singletons 127
gen 4: types 557 tail 70 singletons 100
anchor 10%: g1 types-880 tail-115  g2 types-772 tail-86  g3 types-708 tail-80  g4 types-686 tail-72
paired control: g1 types-823 tail-97  g2 types-688 tail-72  g3 types-595 tail-62  g4 types-521 tail-50
pair-matched delta at gen 4: types +165, tail +22 (control loses 302 types, anchored loses 194) - slope flattened, not zeroed

F7 downstream scheme and the four-bill campaign
gold-only 0.755 | +gen1-syn 0.760 (+0.005) | +gen3-syn 0.620 (-0.135) | pure-gen3 0.130 (3-class chance 0.333)
human-written $524,450 | self-instruct $1,603 (149,843 candidates at 0.350 keep + filter)
anchor surcharge $52,440 (5244 real at 10%) -> anchored bill $54,043
collapse tax: 1077 types -> 587 in 3 ungated cycles (0.455 gone) -> re-collection $238,608
ratios: generation is 327x cheaper than writing; the anchor is 33x the generation bill but the ungated collapse costs 4.4x the anchored bill
FENCE-045-OK
```

## Known Failure Modes

| Trap | What it costs | The honest move |
| --- | --- | --- |
| Distilling at T=1 | the soft target is the hard label - dark mass 0.014, nothing transfers | distill at T=3-5 where dark mass exceeds 0.5 and restore the scale with KL*T^2 |
| Clipping the batch-mean gradient in DP-SGD | the 3.1-norm sample enters the sum unbounded; no epsilon statement survives | clip per sample by min(1, C/norm), then noise the SUM (Abadi 2016) |
| Averaging every buffer in FedAvg | num_batches_tracked = 142 becomes a float statistic; BN silently drifts | carry int buffers as-is; weight only float state by n |
| Reading 'auto' as the QLoRA device map | the model shards across the bus you meant to keep free | pin device_map = {'': 0} for single-GPU QLoRA per 5302 |
| Running the recursion without the anchor | 1077 types decay to 587 in 3 cycles - re-collection $238,608 | keep 10% real every cycle: +165 types at gen 4 for $52,440 |
| Admitting candidates on similarity to the source only | near-duplicates of one seed colonize the pool | Jaccard against the WHOLE pool at 0.7 - the 0.267 keep-rate is the filter working |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Student matches the teacher's argmax but nothing else | T too low - dark mass 0.014 at T=1 | raise T to 3-5; verify dark mass above 0.5 before training |
| Global batch is 64 but the schedule says 32 | the micro x accum x ranks product changed with the fleet | recompute the identity (4x2x4 = 32); assert it at startup |
| 8 GPUs bought, 3.58x delivered | Amdahl s=0.176 - 45% efficiency at N=8 is the honest ceiling | quote the prediction; attack serial work, not more GPUs |
| Federated loss diverges on one client's data | non-IID drift without a prox term | FedProx mu 0.01-0.1, then E=1, then SCAFFOLD, per 5303's order |
| Self-instruct pool fills with near-duplicates | the filter compares against the seed, not the pool | Jaccard 0.7 against every pool member; keep-rate near 0.5 means the bar is loose |
| Synthetic fine-tune drops below gold-only | generation depth 3 with keyword flips at 80% | cap recursion at depth 1 or anchor 10% real and re-measure (+0.005, not -0.135) |

## Quick Reference For

- [Module 5301: Knowledge Distillation - Training Small Models Using Big Model Outputs](../../phases/phase5-finetuning/5300-synthetic/5301-Knowledge-Distillation.md) - dark knowledge at temperature and the KL-times-T-squared blend this sheet prices.
- [Module 5302: Distributed Training Orchestration](../../phases/phase5-finetuning/5300-synthetic/5302-Distributed-Training.md) - the fleet identity (4x2x4 = 32) this sheet's Amdahl bill asserts.
- [Module 5303: Federated Learning](../../phases/phase5-finetuning/5300-synthetic/5303-Federated-Learning.md) - FedAvg's weighted mean and the FedProx escalation order.
- [Module 5304: Self-Instruct and Model Collapse - Growing Instruction Data Without Losing the Distribution](../../phases/phase5-finetuning/5300-synthetic/5304-Self-Instruct-and-Model-Collapse.md) - the self-instruct loop and the collapse tax its anchors pay.
