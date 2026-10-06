---
Document ID: 6505
Title: "6505: Response Caching and Stage Scaling"
Phase: 6
Module: 6500
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'mlops', 'performance', 'serving']
---

# 6505: Response Caching and Stage Scaling

## Abstract

The module's own QUIZ names the two serving disciplines this lesson owns: "explicit response caching is taught nowhere in the curriculum, so Q8 leans on those prompt-side levers," and "generation-stage scaling is taught nowhere in the curriculum." The two gaps are one bill. A RAG fleet pays for capacity twice — once per token it generates and once per replica-hour it runs — and every duplicate query it answers from cache is a token bill it never pays, while every replica it provisions against peak it runs whether or not the traffic shows up. Caching owns the bill you stop paying; scaling owns the bill you shape. The hinge between them is invalidation: a cache that outlives the index it was computed against serves stale answers, and the event that arms that trap is [6504's](6504-Re-Embedding-Policy-and-AB-Testing.md) re-embedding cutover — the same flip that ships a new coordinate system silently re-keys every cached response the old one produced. [1503: LLM Observability](../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) owns the meters this lesson spends (TTFT, TPOT, token and cost gauges) and the prompt-side levers it complements; [2302: Model Serving Architectures](../../phase2-foundations/2300-framework-engineering/2302-Model-Serving-Architectures.md) owns the batching and load-balancing that happen inside one server; [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) and [1405: SGLang](../../phase1-infra/1400-llmops/1405-SGLang.md) own the engine internals — PagedAttention and prefix caching — that make the generation stage cheap per request; [6403: Qdrant Production Deployment](../6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md) owns the retrieval store's own scaling. What lives here is the fleet-level policy: which layer caches what, keyed by what, invalidated by what, and how each stage scales on its own signal.

---

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [What the Cache Actually Caches](#what-the-cache-actually-caches)
- [The Threshold Cuts Both Ways](#the-threshold-cuts-both-ways)
- [The Cache Must Age with the Index](#the-cache-must-age-with-the-index)
- [Two Stages, Two Bottlenecks](#two-stages-two-bottlenecks)
- [One Fleet, Three Bills](#one-fleet-three-bills)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Split a 24-query trace across four cache tiers — identical 12,000-token generation bills under no-cache and retrieval-only caching (searches 24 to 12), 6,000 under a raw-string key, 4,500 under a normalized key, with the three rewordings worth the 1,500-token gap
- Tune a semantic-cache threshold knowing it cuts both ways — loose 0.82 lands 8/10 hits with 2 false hits serving wrong answers, tight 0.95 lands 3/10 with 0 false hits and 3 forfeited paraphrases, on cosines that straddle the cutoff (0.98 down to 0.927)
- Invalidate by index version, not by hope — a query-only key serving 3/5 stale answers after a re-embedding cutover, a 2.0-hour TTL still leaking 1/5 inside its window, the version key exact at 0 stale for all 5 recomputes
- Scale each stage on its own signal — per-stage autoscaling holding both shortfalls at zero for 530 cost units against 924 for peak-provisioning, while gen-only scaling leaves 17.0 RPS-hours of retrieval shortfall and retrieval-only leaves 29.5 of generation shortfall
- Name the two phases one generation replica averages away — 26,400 prefill tokens/s through compute against 3,300 decode steps/s reading KV from memory at the same 22 RPS peak
- Price one fleet day end to end — naive $963 against tuned $551 (43% less), with the cutover's own 7.4M-token re-bill visible as the cost of correctness

**Estimated Time:** 3 hours

---

## What the Cache Actually Caches

A serving trace is not a stream of unique work. Real query logs repeat — the same question asked again by a different user, the same question asked again by the same user with the shift key in a different position — and the QUIZ's Q8 asks where the cache sits. Its option B is the trap worth naming first: "only retrieval, leaving every generation-stage cache miss entirely unaddressed." A retrieval cache is real — it stores the chunk IDs a query retrieved, so the second arrival skips the embedding and the ANN search — but the bill is paid at the generation call, and the retrieval cache never touches it. The fence runs one 24-query support trace through four tiers and bills each.

```python
import re

# one 24-query trace through four cache tiers; every tier billed separately
trace = [
    "What is the refund policy?",
    "How do I reset my password?",
    "what is   the refund policy ?",        # rewording 1: case, spacing, punctuation
    "Where are EU shipments dispatched from?",
    "How do I reset my password?",
    "What is the refund policy?",
    "Can I change my shipping address after ordering?",
    "How do I delete my account?",
    "Where are EU shipments dispatched from",   # rewording 2: punctuation dropped
    "What is the refund policy?",
    "How do I delete my account?",
    "How long do refunds take to arrive?",
    "Can I change my shipping address after ordering?",
    "How do I reset my password?",
    "What payment methods do you accept?",
    "Do you ship to Canada?",
    "What is the refund policy?",
    "How do I contact support?",
    "Do you ship to Canada",                # rewording 3
    "How do I delete my account?",
    "What payment methods do you accept?",
    "How do I contact support?",
    "Where are EU shipments dispatched from?",
    "What is the refund policy?",
]

GEN_TOKENS = 500  # output tokens per generation call


def norm_key(q):
    s = q.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())


stats = {c: {"gen": 0, "search": 0} for c in
         ["no cache", "retrieval-only", "raw-key", "normalized-key"]}
seen_ret, seen_raw, seen_norm = set(), set(), set()
for q in trace:
    stats["no cache"]["gen"] += 1
    stats["no cache"]["search"] += 1
    if q not in seen_ret:
        seen_ret.add(q)
        stats["retrieval-only"]["search"] += 1
    stats["retrieval-only"]["gen"] += 1
    if q not in seen_raw:
        seen_raw.add(q)
        stats["raw-key"]["gen"] += 1
        stats["raw-key"]["search"] += 1
    k = norm_key(q)
    if k not in seen_norm:
        seen_norm.add(k)
        stats["normalized-key"]["gen"] += 1
        stats["normalized-key"]["search"] += 1

print("one 24-query trace through four cache tiers (generation 500 tok/call):")
print(f"  {'client':<16}{'gen calls':>10}{'searches':>10}{'tokens billed':>15}")
for c in stats:
    s = stats[c]
    print(f"  {c:<16}{s['gen']:>10}{s['search']:>10}{s['gen'] * GEN_TOKENS:>15,}")
print(f"  unique normalized queries: {len(seen_norm)}; the 3 rewordings are worth"
      f" {(stats['raw-key']['gen'] - stats['normalized-key']['gen']) * GEN_TOKENS:,} tokens"
      f" the raw key never reclaims")
print(f"  retrieval-only billed the same {stats['no cache']['gen'] * GEN_TOKENS:,} tokens"
      f" as no cache while cutting searches 24 -> {stats['retrieval-only']['search']}:"
      f" the generation bill is the bill")
```

Read the two middle rows against each other. The retrieval-only tier cut searches from 24 to 12 and billed exactly the same 12,000 tokens, because every one of the 24 arrivals still ran a generation call — the expensive stage never noticed the cache existed. The raw-key response cache halves the bill to 6,000 by serving the 12 exact repeats, and the normalized key takes it to 4,500 by catching the three rewordings the raw string never matched: `"what is   the refund policy ?"` is the same question as `"What is the refund policy?"` once case, spacing, and punctuation are folded away, and those three arrivals are worth the entire 1,500-token gap. Key discipline is not an implementation detail — it is a quarter of the bill in this trace. What no key catches is the arrival that shares no string with anything cached, which is the next section's problem.

---

## The Threshold Cuts Both Ways

A rewording that survives normalization — "When will my refund arrive?" against "How long do refunds take to arrive?" — shares no string with its cached twin, so the exact-key tier scores 0 hits on all 10 incoming queries below. The semantic cache embeds the query, finds the nearest cached entry in vector space, and serves it when the cosine clears a threshold. That threshold is a dial with a failure mode on each side, and the failure modes are not symmetric errors a dashboard weighs equally: a missed paraphrase costs one LLM call, while a false hit serves a confident answer to a question that was never asked. [GPTCache](https://github.com/zilliztech/GPTCache), the reference open-source design, is built from exactly the components the fence mirrors — an embedding generator, a vector store, and a similarity evaluator with a configurable threshold — and its own documentation concedes the trade in plain words: semantic caching "can produce false positives on hits and false negatives on misses." (The repository's headline figures — 10x cost reduction, 100x speedup — are the README's promotional numbers, not benchmark results; the fence below prices the trade at toy scale where both error columns are visible.)

```python
import numpy as np

# 8 cached entries; 10 incoming queries: 6 paraphrases of graded strength,
# 2 near-topic confusables, 2 far topics. The threshold must split BOTH bands.
rng = np.random.default_rng(17)
n_topics, d = 12, 96
T = rng.normal(size=(n_topics, d))
T /= np.linalg.norm(T, axis=1, keepdims=True)


def unit_noise(r):
    v = r.normal(size=d)
    return v / np.linalg.norm(v)


CACHED = [
    (0, "How long do refunds take to arrive?", "7 business days"),
    (1, "Do you ship to Canada?", "yes, 2-day"),
    (2, "How do I delete my account?", "settings > danger zone"),
    (3, "What payment methods do you accept?", "cards and PayPal"),
    (4, "Where are EU shipments dispatched from?", "Rotterdam"),
    (5, "How do I reset my password?", "email link, 15 min"),
    (6, "Can I change my shipping address after ordering?", "yes, before dispatch"),
    (7, "What is the warranty period?", "24 months"),
]
E = np.stack([T[t] + 0.25 * unit_noise(rng) for t, _, _ in CACHED])
E /= np.linalg.norm(E, axis=1, keepdims=True)

INCOMING = [
    ("para", 0, "When will my refund arrive?", 0.20),
    ("para", 3, "Which cards and wallets can I pay with?", 0.25),
    ("para", 2, "How can I remove my profile for good?", 0.30),
    ("para", 4, "Which EU warehouse do orders leave from?", 0.34),
    ("para", 5, "I lost my password, what now?", 0.38),
    ("para", 6, "Is it possible to edit the delivery address?", 0.42),
    ("conf", 1, "Do you deliver to Mexico?", None),
    ("conf", 0, "How long does the return window stay open?", None),
    ("far", None, "Do you offer student discounts?", None),
    ("far", None, "Can I buy gift cards in store?", None),
]

Q = []
for kind, near, _question, sigma in INCOMING:
    if kind == "para":
        v = E[near] + sigma * unit_noise(rng)
    elif kind == "conf":
        other = int(rng.integers(0, 8))
        while other == near:
            other = int(rng.integers(0, 8))
        v = 0.85 * E[near] + 0.53 * E[other]
    else:
        v = T[int(rng.integers(8, 12))] + 0.30 * unit_noise(rng)
    Q.append(v)
Q = np.stack(Q)
Q /= np.linalg.norm(Q, axis=1, keepdims=True)
S = Q @ E.T  # (10, 8) cosine against every cached entry


def run(threshold):
    hits = false_hits = forfeited = 0
    for i, (kind, _near, _question, _sig) in enumerate(INCOMING):
        j = int(np.argmax(S[i]))
        if S[i, j] >= threshold:
            hits += 1
            if kind == "conf":
                false_hits += 1
        elif kind == "para":
            forfeited += 1
    return hits, false_hits, forfeited


print("semantic cache on 10 incoming queries (6 paraphrases, 2 near-topic, 2 far):")
for name, th in [("loose 0.82", 0.82), ("tight 0.95", 0.95)]:
    h, f, g = run(th)
    print(f"  {name}: hits {h}/10, false hits {f} (wrong answer served),"
          f" forfeited paraphrases {g}")
print(f"  paraphrase cosines: {[round(float(S[i].max()), 3) for i, (k, _n, _q, _s) in enumerate(INCOMING) if k == 'para']}")
print(f"  near-topic cosines: {[round(float(S[i].max()), 3) for i, (k, _n, _q, _s) in enumerate(INCOMING) if k == 'conf']}")
print(f"  far cosines:        {[round(float(S[i].max()), 3) for i, (k, _n, _q, _s) in enumerate(INCOMING) if k == 'far']}")
print("  exact-key tier on the same 10: 0 hits (a rewording shares no string)")
```

The six paraphrase cosines walk 0.98 down to 0.927 because rewordings differ in strength — "When will my refund arrive?" is a light rewrite of its cached twin, "Is it possible to edit the delivery address?" a heavy one — and the two confusables land at 0.834 and 0.873, inside the loose threshold and outside the tight one. Loose 0.82 serves 8 of 10 from cache and two of those serves are wrong answers delivered with full confidence: "Do you deliver to Mexico?" is answered with Canada's "yes, 2-day." Tight 0.95 eliminates the false hits and forfeits the three heaviest paraphrases, each one a full-price LLM call for a question the cache could have answered. There is no threshold that wins both columns, because the paraphrase band and the confusable band overlap — the dial moves the boundary through the overlap, it does not remove it. Tune on both error types with near-topic negatives in the holdout, not on hit rate alone.

---

## The Cache Must Age with the Index

A cached answer is a claim about the corpus: this query, against this index, returns this response. [6504's](6504-Re-Embedding-Policy-and-AB-Testing.md) cutover ships a new index version — and every response cached under the old version is now an answer computed from a coordinate system nobody serves anymore. The fence caches 5 answers under index v1, runs the cutover to v2 (3 of the 5 answers legitimately change), and re-delivers the same queries after the flip under three invalidation policies.

```python
# 5 answers cached under index v1; the re-embedding cutover changes 3 of them
V1_ANS = {
    "q1": "Refunds arrive in 7 business days.",
    "q2": "EU orders ship from Rotterdam.",
    "q3": "We accept cards and PayPal.",
    "q4": "Password reset links expire in 15 minutes.",
    "q5": "Support replies within one business day.",
}
V2_ANS = dict(V1_ANS)
V2_ANS["q1"] = "Refunds arrive in 3 business days."
V2_ANS["q3"] = "We accept cards, PayPal and iDEAL."
V2_ANS["q5"] = "Support replies within four business hours."
ORDER = ["q1", "q2", "q3", "q4", "q5"]

cache_qo = {q: V1_ANS[q] for q in ORDER}
cache_ver = {(q, 1): V1_ANS[q] for q in ORDER}
cache_ttl = {q: (V1_ANS[q], 0.0) for q in ORDER}
TTL = 2.0
arrival = [1.2, 2.0, 2.5, 3.0, 3.5]  # cutover at t=1.0


def serve(policy):
    stale = correct = recompute = 0
    for q, t in zip(ORDER, arrival):
        if policy == "query-only":
            served = cache_qo[q]
        elif policy == "version-keyed":
            served = cache_ver.get((q, 2))
            if served is None:
                recompute += 1
                served = V2_ANS[q]
                cache_ver[(q, 2)] = served
        else:
            ans, t0 = cache_ttl[q]
            if t - t0 < TTL:
                served = ans
            else:
                recompute += 1
                served = V2_ANS[q]
                cache_ttl[q] = (served, t)
        if served == V2_ANS[q]:
            correct += 1
        else:
            stale += 1
    return stale, correct, recompute


print("5 answers cached under index v1; re-embedding cutover to v2 at t=1.0h"
      " changes 3 of the 5; same queries re-arrive at t=1.2..3.5h:")
for p in ["query-only", "ttl 2.0h", "version-keyed"]:
    s, c, r = serve(p)
    print(f"  {p:<14} stale {s}/5, correct {c}/5, recomputes {r}")
```

The query-only key is 0 recomputes and 3 stale answers: the cache cannot know the corpus moved under it, so it serves the old refund policy, the old payment list, and the old SLA with the confidence of a hit. The 2.0-hour TTL is better and still wrong — the t=1.2 arrival sits inside its window and gets the v1 refund answer, one staleness leak the clock cannot see. Shortening the TTL trades the leak away one recomputation at a time without ever closing it; lengthening it saves compute and leaks more. The version key is the only policy that is exact: the cutover re-keys every entry, so all 5 arrivals miss at v2, all 5 recompute, and 0 stale answers are served. The price is honest — 5 recomputes against the TTL's 4 — and it is the same price 6504's shadow window already budgeted: a coordinate-system change invalidates everything computed in the old one, caches included. Version the key with the artifact the answer was computed against.

---

## Two Stages, Two Bottlenecks

The QUIZ's Q16 answers "scale both" — and the interesting question is not *whether* but *on what signal*, because the two stages queue differently and cost differently. A retrieval replica is stateless and cheap; a generation replica is GPU-bound and expensive, and its queue is where user-visible latency dies. The fence runs one 12-step diurnal curve (peak 22 RPS) against five policies and measures each stage's shortfall — demand exceeding capacity, summed over the day in RPS-hours — alongside its replica cost.

```python
import math

# 12-step diurnal curve; retrieval 5 RPS/replica @1 u/h, generation 2.5 RPS/replica @8 u/h
LOAD = [4, 6, 9, 12, 16, 20, 22, 19, 15, 11, 7, 5]
CAP_R, COST_R = 5.0, 1.0
CAP_G, COST_G = 2.5, 8.0


def autoscale(cap, load):
    return [math.ceil(x / cap) for x in load]


mean_r = math.ceil(sum(LOAD) / 12 / CAP_R)
mean_g = math.ceil(sum(LOAD) / 12 / CAP_G)
peak_r, peak_g = math.ceil(max(LOAD) / CAP_R), math.ceil(max(LOAD) / CAP_G)
rep_r, rep_g = autoscale(CAP_R, LOAD), autoscale(CAP_G, LOAD)

policies = {
    "static (avg)": ([mean_r] * 12, [mean_g] * 12),
    "gen-only autoscale": ([mean_r] * 12, rep_g),
    "retrieval-only autoscale": (rep_r, [mean_g] * 12),
    "per-stage autoscale": (rep_r, rep_g),
    "static (peak)": ([peak_r] * 12, [peak_g] * 12),
}

print("two stages under one 12-step diurnal curve (peak 22 RPS): retrieval"
      " 5 RPS/replica @1 u/h, generation 2.5 RPS/replica @8 u/h")
print("  shortfall = demand minus capacity, summed over the 12 steps (RPS-hours)")
print(f"  {'policy':<26}{'R short':>8}{'G short':>8}{'R cost':>8}{'G cost':>8}{'total':>8}")
for name, (rs, gs) in policies.items():
    vr = sum(max(0.0, LOAD[t] - rs[t] * CAP_R) for t in range(12))
    vg = sum(max(0.0, LOAD[t] - gs[t] * CAP_G) for t in range(12))
    cr, cg = sum(COST_R * r for r in rs), sum(COST_G * g for g in gs)
    print(f"  {name:<26}{vr:>8.1f}{vg:>8.1f}{cr:>8.0f}{cg:>8.0f}{cr + cg:>8.0f}")

PROMPT, ANSWER = 1200, 150
print(f"inside one generation replica at the 22 RPS peak, the two phases the"
      f" autoscaler averages away:")
print(f"  prefill: {22 * PROMPT:,} prompt tokens/s through compute in one pass each")
print(f"  decode : {22 * ANSWER:,} steps/s, each reading the full KV from memory")
```

Exactly two policies hold both shortfalls at zero: per-stage autoscaling at 530 units and peak-provisioning at 924. The 43% gap between them is the whole scaling argument — autoscaling tracks demand, peak-provisioning pays for the peak all day. The two half-policies show why the signal must be per-stage: scaling generation only leaves 17.0 RPS-hours of retrieval shortfall behind an otherwise healthy generation fleet, and scaling retrieval only leaves 29.5 RPS-hours of generation shortfall — the queue where TTFT dies — behind an otherwise healthy retrieval fleet. "Scale both" is right and incomplete; the full answer is *each stage on its own queue, each at its own step size*, because one GPU-hour costs 8 retrieval-replica-hours and a generation queue hurts users a retrieval queue does not.

The last two lines of the fence are the split inside the generation stage itself: at the 22 RPS peak the same replica is processing 26,400 prefill tokens/s — compute-bound, one pass per prompt — and 3,300 decode steps/s — memory-bound, each step reading the full KV cache. Those are different bottlenecks wearing one replica count, which is why the production systems disaggregate them: [DistServe](https://arxiv.org/abs/2401.09670) (Zhong et al., OSDI 2024) runs prefill and decoding on separate GPUs and co-optimizes each phase's allocation against TTFT and TPOT targets, serving 7.4x more requests or 12.6x tighter SLOs than colocation; [Splitwise](https://arxiv.org/abs/2311.18677) (Patel et al., ISCA 2024) splits the compute-intensive prompt phase from the memory-intensive token-generation phase onto matched hardware for 1.4x throughput at 20% lower cost. A single autoscaler that averages the two phases into one signal is the fleet-level version of the interference those papers remove.

---

## One Fleet, Three Bills

The campaign fence runs one 12-hour fleet day through the full stack — the exact-tier hit fraction from Section 1 (9 of 24), the semantic tier's honest conversion rate from Section 2 (tight threshold: 3 of 10), the version-keyed invalidation from Section 3 clearing the cache at a mid-day re-embedding cutover, and the per-stage scaling from Section 4 — against a naive fleet with no caches and peak-provisioned replicas all day.

```python
import math

# the tuned fleet: exact cache (9/24 steady hit), semantic tier (3/10 of exact
# misses, Section 2's tight threshold), version-keyed (cutover clears at t=6),
# per-stage autoscale. The naive fleet: no caches, peak-provisioned all day.
LOAD = [4, 6, 9, 12, 16, 20, 22, 19, 15, 11, 7, 5]
CAP_R, COST_R = 5.0, 1.0
CAP_G, COST_G = 2.5, 8.0
GEN_TOKENS = 500
HIT_FULL = 9 / 24
SEM_ADD = 3 / 10
WARM = 2
CUTOVER_T = 6
PRICE = 0.15  # $ per 1M output tokens


def autoscale(cap, load):
    return [math.ceil(x / cap) for x in load]


rep_r, rep_g = autoscale(CAP_R, LOAD), autoscale(CAP_G, LOAD)
peak_r, peak_g = math.ceil(max(LOAD) / CAP_R), math.ceil(max(LOAD) / CAP_G)


def hit_at(t):
    return HIT_FULL * (t + 1) / WARM if t < WARM else HIT_FULL


naive_tokens = naive_search = tuned_tokens = tuned_search = tuned_cost = 0.0
cutover_burn = 0.0
for t, rps in enumerate(LOAD):
    naive_tokens += rps * 3600 * GEN_TOKENS
    naive_search += rps * 3600
    h = hit_at(t)
    if t >= CUTOVER_T:
        h = hit_at(t - CUTOVER_T) if t - CUTOVER_T < WARM else HIT_FULL
    miss = 1.0 - h
    sem = miss * SEM_ADD if t >= WARM and (t < CUTOVER_T or t - CUTOVER_T >= WARM) else 0.0
    served_by_gen = miss - sem
    if t >= CUTOVER_T:
        cutover_burn += (HIT_FULL - h) * rps * 3600 * GEN_TOKENS
    tuned_tokens += served_by_gen * rps * 3600 * GEN_TOKENS
    tuned_search += served_by_gen * rps * 3600
    tuned_cost += COST_R * rep_r[t] + COST_G * rep_g[t]
naive_cost = COST_R * peak_r * 12 + COST_G * peak_g * 12
print("one 12-hour fleet day: naive (no caches, peak-provisioned all day) vs tuned"
      " (exact + semantic caches, version-keyed, per-stage autoscale):")
print(f"  gen tokens billed : naive {naive_tokens / 1e6:,.1f}M  vs  tuned"
      f" {tuned_tokens / 1e6:,.1f}M  ({1 - tuned_tokens / naive_tokens:.0%} fewer)")
print(f"  retrieval searches: naive {naive_search / 1e3:,.0f}k  vs  tuned"
      f" {tuned_search / 1e3:,.0f}k  ({1 - tuned_search / naive_search:.0%} fewer)")
print(f"  replica cost      : naive ${naive_cost:,.0f}  vs  tuned ${tuned_cost:,.0f}"
      f"  ({1 - tuned_cost / naive_cost:.0%} less)")
print(f"  token bill        : naive ${naive_tokens / 1e6 * PRICE:,.2f}  vs  tuned"
      f" ${tuned_tokens / 1e6 * PRICE:,.2f}")
print(f"  the cutover's own bill: {cutover_burn / 1e6:,.1f}M tokens re-billed while the"
      f" cache re-warms after the v1->v2 key flip")
print(f"  total (tokens + replicas): naive ${naive_tokens / 1e6 * PRICE + naive_cost:,.0f}"
      f"  vs  tuned ${tuned_tokens / 1e6 * PRICE + tuned_cost:,.0f}"
      f"  ({1 - (tuned_tokens / 1e6 * PRICE + tuned_cost) / (naive_tokens / 1e6 * PRICE + naive_cost):.0%} less)")
```

Three bills, one day. The token bill: 262.8M naive against 141.0M tuned, 46% of the generation spend removed by refusing to recompute answers the fleet already owns. The search bill moves identically — 526k to 282k — because a response hit skips both stages. The replica bill: $924 against $530, the Section 4 policy applied for a full day. Together the naive fleet's day costs $963 and the tuned fleet's $551. And the fence prints the line that keeps the lesson honest: the cutover's own bill, 7.4M tokens re-billed while the emptied cache re-warms — the price of Section 3's correctness, visible in the same ledger as the savings. The three disciplines are one budget: caching deletes work, scaling shapes capacity, invalidation decides when the deletions expire.

---

## Known Failure Modes

| # | Symptom | Cause | Fix |
|---|---------|-------|-----|
| 1 | Duplicate traffic never hits, hit rate near zero despite obvious repeats | Key on the raw query string — case, spacing, and punctuation variants each miss | Normalize before keying: lowercase, strip punctuation, collapse whitespace (Section 1's 1,500-token gap) |
| 2 | Search load drops but latency and cost barely move | Retrieval-only caching — the generation call, the bill's dominant line, still runs per arrival | Cache at the response boundary, keyed on the normalized query (Section 1's identical 12,000-token rows) |
| 3 | Confident wrong answers traced to the cache | Semantic threshold tuned on hit rate alone — near-topic questions clear the bar and inherit a stranger's answer | Tune on both error types with near-topic negatives in the holdout; price false hits above forfeited hits (Section 2's two bands) |
| 4 | Stale answers after every re-embedding cutover | Cache keyed on the query only — the index version moved and no key noticed | Key on (query, index_version); the cutover re-keys, arrivals miss, correctness is exact (Section 3) |
| 5 | Staleness leaks inside the TTL window, recomputes pile up outside it | TTL used as the invalidation policy — a clock cannot see a corpus change | TTL bounds memory and residency; the version key owns correctness (Section 3's 1/5 leak at TTL 2.0h) |
| 6 | One stage queues at peak while the other idles | Uniform replica count across stages — the pinned stage holds capacity the curve outgrows | Scale each stage on its own queue signal at its own step size (Section 4's 17.0 and 29.5 RPS-hour shortfalls) |
| 7 | TTFT degrades under load though throughput targets hold | Prefill and decode colocated under one autoscaler — compute-bound and memory-bound phases averaged into one signal | Separate pools or separate signals per phase; DistServe and Splitwise are the production form of the split |
| 8 | Cache and scaling decisions made blind, disputed in retrospect | Hit rate and recompute rate absent from the dashboard — the levers priced against nothing | Export hit rate, recompute rate, and per-stage shortfall next to the TTFT/TPOT gauges 1503 already carries |

---

## Summary

A RAG fleet pays twice — per token and per replica-hour — and the two disciplines the module's QUIZ left untaught are the two that shape those bills. Response caching deletes work at the response boundary, and the deleting is all in the key: the same 24-query trace bills 12,000 tokens with no cache, still 12,000 under retrieval-only caching (the generation call never noticed), 6,000 under a raw-string key, and 4,500 once the key is normalized — the three rewordings worth the whole gap. The semantic tier extends the key into vector space, and its threshold cuts both ways on bands that genuinely overlap: 0.82 serves 8 of 10 with two confident wrong answers; 0.95 serves 3 of 10 with none. There is no winning setting, only a priced trade — GPTCache's own documentation concedes the false-positive and false-negative pair the fence displays.

Invalidation is the discipline that makes the cache truthful. A re-embedding cutover changes 3 of 5 cached answers and the query-only key serves all 3 stale; a 2.0-hour TTL still leaks 1 inside its window; the version key takes 5 recomputes and serves 0 stale answers — the same coordinate-system rule 6504's shadow window obeys, applied one layer up.

Scaling is the second half of the bill, and its answer is per-stage: two policies hold both shortfalls at zero — per-stage autoscaling at 530 units, peak-provisioning at 924 — and the half-policies show what one wrong signal costs (17.0 RPS-hours of retrieval shortfall behind a scaled generation fleet, 29.5 of generation shortfall behind a scaled retrieval fleet, the queue where TTFT dies). Inside the generation stage the same replica is two phases — 26,400 prefill tokens/s compute-bound, 3,300 decode steps/s memory-bound at the 22 RPS peak — the split DistServe disaggregates for 7.4x more requests at matched SLOs and Splitwise for 1.4x throughput at 20% lower cost. The campaign fence runs the full stack for one day: $963 naive against $551 tuned, with the cutover's own 7.4M-token re-bill in the same ledger as the savings — caching deletes work, scaling shapes capacity, invalidation decides when the deletions expire.

---

## References

### Related Minder Academy Documents

- [6504: Re-Embedding Policy and A/B Testing](6504-Re-Embedding-Policy-and-AB-Testing.md) — the cutover that arms the invalidation trap and the gate that ships it
- [1503: LLM Observability](../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) — the TTFT/TPOT and cost meters this lesson's levers move, and the prompt-side levers it complements
- [2302: Model Serving Architectures](../../phase2-foundations/2300-framework-engineering/2302-Model-Serving-Architectures.md) — the batching and load-balancing inside one server, below this lesson's fleet-level policy
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) — the engine internals (PagedAttention, continuous batching) behind the generation stage's per-request cost
- [1405: SGLang](../../phase1-infra/1400-llmops/1405-SGLang.md) — the RadixAttention prefix cache, the engine-level cache beneath the response-level one
- [6403: Qdrant Production Deployment](../6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md) — the retrieval store's own capacity tiers and replication

### Primary Sources

- Zhong, Y., Liu, S., Chen, J., Hu, J., Zhu, Y., Liu, X., Jin, X., & Zhang, H. (2024). "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving." *OSDI 2024* — arXiv:2401.09670, the TTFT/TPOT split served on separate GPUs, 7.4x more requests or 12.6x tighter SLO
- Patel, P., Choukse, E., Zhang, C., Shah, A., Goiri, Í., Maleki, S., & Bianchini, R. (2024). "Splitwise: Efficient generative LLM inference using phase splitting." *ISCA 2024* — arXiv:2311.18677, the compute-bound prompt phase and memory-bound token-generation phase on matched hardware, 1.4x throughput at 20% lower cost
- [GPTCache: An Open-Source Semantic Cache for LLMs](https://github.com/zilliztech/GPTCache) — the embedding-generator / vector-store / similarity-evaluator design this lesson's Section 2 mirrors, and the documentation's own false-positive/false-negative admission

---

## Next Steps

- **Next Module:** [7100: Agent Architecture](../../phase7-agentic/7100-architecture/README.md) — the tool calls agents make inherit every cache and queue this lesson prices
- **Continue with:** [7101: ReAct Loop System](../../phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md) — the loop whose tool-call volume the caches and stage signals absorb
- **Assessment:** [QUIZ](./assessment/QUIZ.md) — questions 8 and 16 are this lesson's, and the caching and scaling review bullets now point here
- **Hands-on:** re-run the stage-scaling fence with your own traffic curve and replica costs, then key a response cache on (query, index_version) and watch the re-embedding cutover clear it — the re-bill you observe is Section 3's arithmetic at production size
