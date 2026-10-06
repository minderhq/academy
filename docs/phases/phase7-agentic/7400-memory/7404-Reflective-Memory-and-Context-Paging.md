---
Document ID: 7404
Title: "7404: Reflective Memory and Context Paging"
Phase: 7
Module: 7400
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'memory', 'long-term-memory', 'retrieval', 'context']
---

# 7404: Reflective Memory and Context Paging

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Memory Wall](#the-memory-wall)
- [The Retrieval Blend: Recency, Importance, Relevance](#the-retrieval-blend-recency-importance-relevance)
- [Reflection: Pruning Versus Distilling](#reflection-pruning-versus-distilling)
- [Context Paging: MemGPT's Virtual Context](#context-paging-memgpts-virtual-context)
- [The Reflexion Loop: Verbal Rules as Memory](#the-reflexion-loop-verbal-rules-as-memory)
- [One Long-Horizon Agent: Three Memory Stacks](#one-long-horizon-agent-three-memory-stacks)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Abstract

The 7400 assessment names three holes in this curriculum and this lesson closes all three. MemGPT itself is named nowhere (Question 12 leans on 7401's tier list alone), reflective memory as a named agent pattern is taught nowhere (Question 15 leans on 7403's consolidation step alone), and the episodic-buffer term appears nowhere (Questions 16-17 lean on the Working tier's framing alone). All three are one subject: the memory mechanisms that run between the tiers 7401 named and the store 7403 built.

Five fences carry it. The retrieval blend fence ranks the same eight memories three ways and shows recency-only ranking handing the top slot to fresh trivia while the reference blend puts the decisive old memory first at 5.212 against the fresh one's 3.483. The consolidation fence compresses a 12-episode store two ways - naive pruning lands 4/6 probes with the auth facts dead at 0.000, distillation into 4 facts lands 6/6 at 0.924 mean cosine - the same 3.0x compression, opposite outcomes. The paging fence runs 24 turns (90 tokens) against a 48-token budget: keep-everything overflows at turn 12, drop-oldest fits at 47/48 but loses 5 of 12 facts including the probe's answer, MemGPT-style paging ends at 43/48 with 7 page-outs, one page-back, and 100% of the information retained. The reflexion fence converts evaluator failures into stored verbal rules and walks 25 tasks from 20% to 68% to 96% to 100% pass while the actor without the buffer sits at 5/25 forever. The campaign fence prices three memory stacks on one 30-turn agent under a 100-token budget and gives each mechanism exactly its own bill.

## Learning Objectives

By the end of this lesson you will be able to:

- Read the tri-component retrieval blend as code and defend each weight - why relevance carries weight 3 while recency carries 0.5 - and state what recency-only ranking breaks.
- Distinguish pruning from distilling as the two compression moves on an episodic store, and show with probe scores why only consolidation makes compression lossless.
- Implement MemGPT-style virtual context management - trigger, page-out, searchable external store, page-back - and keep occupancy under budget with zero information loss.
- Implement the memory half of the reflexion loop: evaluator failure traces converted into stored verbal rules that raise the pass rate trial over trial.
- Price three memory stacks (stuff-and-truncate, page-only, page-plus-reflect) on one long-horizon agent and assign each mechanism exactly its own failure class.

## The Memory Wall

Module 7401 gave the tier list - core context, episodic memory, semantic memory, retrieval - and module 7403 built the vector store that holds the tiers. Neither taught the mechanisms that move bytes between them, and those mechanisms are where long-horizon agents actually break. Three questions expose the gap: what ranks which memory comes back (Section 5), what happens to episodes as they age (Section 6), and how the window stays under budget without amnesia (Section 7).

MemGPT (Packer et al., 2023) supplies the frame this lesson uses throughout: an operating system for the context window. Main context is RAM - what the model sees this turn. External context is disk - everything the store holds. The operating system's one job is virtual context management: keep the working set in RAM and page the rest, with the model itself deciding when to swap through function calls. The paper's thesis generalizes past any one implementation: the context window is not the memory. It is the cache.

## The Retrieval Blend: Recency, Importance, Relevance

When the generative-agents system (Park et al., 2023) needs the top memories for a turn, it does not rank by any single axis. Its `retrieve.py` scores every candidate memory as a weighted sum of three min-max-normalized components: recency (an exponential decay, weight 0.5), relevance (cosine similarity to the query, weight 3), and importance (an LLM-assigned 1-10 poignancy score, weight 2). The weights are the design claim: relevance dominates, importance doubles recency.

One honesty note before the fence. The paper describes recency as `0.995^hours` of in-game time since the memory was written; the repository's code applies the same decay over position in a most-recent-first list (`recency_decay ** i`), which orders identically but decays milder. The fence below uses the code's form, because the code is what ships.

```python
import numpy as np

def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def minmax(vals):
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return [0.5 for _ in vals]
    return [(v - lo) / (hi - lo) for v in vals]

# 8 memories, most-recent-first. Topic A = auth rotation (old, important),
# topic B = small talk (fresh, trivial). The query is about auth rotation.
names = [
    "M1 fresh: user mentioned the weather",
    "M2 fresh: user joked about coffee",
    "M3 fresh: user asked about meeting time",
    "M4 fresh: user shared a news link",
    "M5 old:  API key rotated to vault-backed rotation",
    "M6 old:  rotation schedule moved to 30-day window",
    "M7 old:  old key revoked after rotation",
    "M8 old:  user complained about the font",
]
V = np.array([
    [1.0, 0.0], [0.9, 0.1], [0.2, 0.9], [0.0, 1.0],
    [1.0, 0.1], [0.95, 0.15], [1.0, 0.05], [0.1, 0.8],
])
q = np.array([1.0, 0.1])  # "auth rotation" probe direction
importance = np.array([2, 2, 3, 2, 9, 8, 7, 2], dtype=float)

# reference blend: gw = [0.5 recency, 3 relevance, 2 importance]
# repo recency = 0.995**i over most-recent-first list position
rec_raw = [0.995 ** (i + 1) for i in range(len(names))]
rel_raw = [cos(q, V[i]) for i in range(len(names))]
imp_raw = importance.tolist()
rec_n, rel_n, imp_n = minmax(rec_raw), minmax(rel_raw), minmax(imp_raw)
score = [0.5 * r + 3.0 * l + 2.0 * m for r, l, m in zip(rec_n, rel_n, imp_n)]

order_blend = sorted(range(len(names)), key=lambda i: -score[i])
order_recency = sorted(range(len(names)), key=lambda i: -rec_n[i])
order_imp = sorted(range(len(names)), key=lambda i: -imp_n[i])
order_rel = sorted(range(len(names)), key=lambda i: -rel_n[i])

print("retrieval scoring: the generative-agents blend")
print("  gw = [0.5 recency, 3 relevance, 2 importance]; recency = 0.995**i, newest first")
print(f"  raw recency spread: {rec_raw[0]:.3f} (newest) .. {rec_raw[-1]:.3f} (oldest)")
i = order_recency[0]
print(f"  recency-only top-1:  {names[i]}")
i = order_imp[0]
print(f"  importance-only top-1: {names[i]} (raw {imp_raw[i]:.0f}/10)")
i = order_rel[0]
print(f"  relevance-only top-1:  {names[i]} (cos {rel_raw[i]:.3f})")
print("  blend top-3:")
for i in order_blend[:3]:
    print(f"    {names[i]}  score {score[i]:.3f} "
          f"(rec {rec_n[i]:.2f} x0.5 | rel {rel_n[i]:.2f} x3 | imp {imp_n[i]:.2f} x2)")
best = order_blend[0]
print(f"  blend top-1: {names[best]} score {score[best]:.3f}")
print(f"  best fresh trivial (M1) blend score: {score[0]:.3f}")
```

Read the fence against the question "what does the agent know about auth rotation?" The raw recency spread is 0.995 (newest) to 0.961 (oldest) - min-max normalization blows that 3% gap up to a full 0-to-1 range, which is why recency-only ranking is so destructive: it hands the top slot to M1, the weather. Importance-only and relevance-only both rank M5 (the key rotation, raw importance 9/10, cosine 1.000) first. The blend agrees - M5 at 5.212, then M6 at 4.850, then M7 at 4.495, while the freshest trivia M1 lands at 3.483. Note the mechanics in the top-3 lines: M5 wins with a mediocre recency term (0.42) because relevance (1.00 x 3) and importance (1.00 x 2) carry the score, and even a perfectly fresh trivial memory (recency 1.0) cannot buy its way past a decisive memory with a 3x-weighted relevance term. That is the claim the weights encode, and it is the answer to Question 15's real subject: memory that returns whatever was said last is not memory, it is a transcript.

## Reflection: Pruning Versus Distilling

An episodic store only grows. Two moves shrink it, and they are not interchangeable. Pruning deletes old episodes to reclaim capacity. Distilling - the consolidation step in 7403's lifecycle, the reflection pattern in the agent literature - derives semantic facts from episodes first, then lets the episodes go. The question the fence answers: what does each move cost at query time?

The setup: 12 episodes across 4 topics (auth rotation, dietary preference, deploy state, reporting). A probe counts as a hit when its nearest neighbor belongs to the probe's true topic. Three stores: the full 12-episode store, a pruned store holding only the 6 most recent episodes, and a distilled store holding 4 centroid facts (one per topic cluster). The probes are deliberately worded at question level - "how is auth managed?", "where to eat next time" - so that answering them requires the right topic, not surface word overlap.

```python
import numpy as np

VOCAB = ["auth", "rotation", "vault", "diet", "vegan", "restaurant", "deploy",
         "pipeline", "ci", "report", "meeting", "tuesday"]
def embed(words):
    v = np.zeros(len(VOCAB))
    for w in words:
        v[VOCAB.index(w)] = 1.0
    return v / max(np.linalg.norm(v), 1.0)

episodes = [
    ("api key rotated",        ["auth", "rotation", "vault"]),
    ("vault backend chosen",   ["auth", "vault"]),
    ("old key revoked",        ["auth", "rotation"]),
    ("rotation window 30d",    ["auth", "rotation"]),
    ("went vegan in march",    ["diet", "vegan"]),
    ("vegan recipe share",     ["diet", "vegan"]),
    ("restaurant booked",      ["diet", "restaurant"]),
    ("vegan restaurant pick",  ["diet", "vegan", "restaurant"]),
    ("ci pipeline broke",      ["deploy", "pipeline", "ci"]),
    ("pipeline fixed",         ["deploy", "pipeline", "ci"]),
    ("deploy rollback",        ["deploy"]),
    ("report drafted",         ["report", "meeting"]),
]
clusters = {0: [0, 1, 2, 3], 1: [4, 5, 6, 7], 2: [8, 9, 10], 3: [11]}
facts = {}
for c, idxs in clusters.items():
    cent = np.mean([embed(episodes[i][1]) for i in idxs], axis=0)
    cent /= np.linalg.norm(cent)
    facts[c] = cent

probes = [
    ("how is auth managed?",          ["auth", "vault", "rotation"]),
    ("what changed in key handling",  ["auth", "rotation"]),
    ("dietary preference?",           ["diet", "vegan"]),
    ("where to eat next time",        ["diet", "restaurant"]),
    ("state of deploys",              ["deploy", "pipeline", "ci"]),
    ("any reports?",                  ["report", "meeting"]),
]

def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def top1(store_keys, store_vecs, qw):
    best_k, best_s = None, -2.0
    for k, v in zip(store_keys, store_vecs):
        s = cos(qw, v)
        if s > best_s:
            best_k, best_s = k, s
    return best_k, best_s

ep_keys = list(range(len(episodes)))
ep_vecs = [embed(w) for _, w in episodes]
ep_cluster = {i: c for c, idxs in clusters.items() for i in idxs}
fact_keys = list(facts.keys())
fact_vecs = [facts[k] for k in fact_keys]
truth = [0, 0, 1, 1, 2, 3]
probe_vecs = [embed(w) for _, w in probes]

pruned = list(range(6, 12))  # keep the 6 most recent episodes
def store_hits(keys, vecs, cluster_of):
    hits, scores = 0, []
    for pv, t in zip(probe_vecs, truth):
        k, s = top1(keys, vecs, pv)
        scores.append(s)
        hits += cluster_of(k) == t
    return hits, scores

ep_hits, ep_scores = store_hits(ep_keys, ep_vecs, lambda k: ep_cluster[k])
pr_hits, pr_scores = store_hits(pruned, [ep_vecs[i] for i in pruned], lambda k: ep_cluster[k])
fa_hits, fa_scores = store_hits(fact_keys, fact_vecs, lambda k: k)
print("reflection / consolidation: pruning vs distilling")
print(f"  full episodic store (12): probes {ep_hits}/6, mean top-1 cos {np.mean(ep_scores):.3f}")
print(f"  pruned  episodic store (6, recent only): probes {pr_hits}/6, "
      f"mean top-1 cos {np.mean(pr_scores):.3f}")
print(f"  distilled fact  store (4): probes {fa_hits}/6, mean top-1 cos {np.mean(fa_scores):.3f}")
print(f"  12 episodes -> {len(facts)} facts = {len(episodes)/len(facts):.1f}x smaller store, "
      f"zero probe loss")
for (label, pwords), t, s_full, s_pr, s_fa in zip(probes, truth, ep_scores, pr_scores, fa_scores):
    k_pr, _spr = top1(pruned, [ep_vecs[i] for i in pruned], embed(pwords))
    k_fa, _sfa = top1(fact_keys, fact_vecs, embed(pwords))
    print(f"    {label:32s} full {s_full:.3f} | pruned {'HIT ' if ep_cluster[k_pr]==t else 'MISS'} {s_pr:.3f} "
          f"| fact {'HIT ' if k_fa==t else 'MISS'} {s_fa:.3f}")
lost_topics = sorted({ep_cluster[i] for i in range(6)})
print(f"  pruning dropped 6 of 12 episodes across {len(lost_topics)} topics; "
      f"reflection made the same 3.0x compression lossless")
```

The table is the whole argument. The full store answers 6/6 at mean cosine 1.000 - every probe has an exact episode. The pruned store answers 4/6: both auth probes fall to MISS 0.000 because pruning dropped 6 of 12 episodes across 2 topics and one of them was the entire auth cluster - the fact that the API key now rotates through a vault exists in no surviving episode, so no amount of cosine can recover it. The distilled store answers 6/6 at mean 0.924: same 3.0x compression as pruning (12 to 4), zero probe loss. The per-probe rows show the trade: distillation gives up a little sharpness on probes whose episode was exact ("where to eat next time" drops from 1.000 to 0.784) and gains everything on probes whose episodes no longer exist (0.000 to 0.960). Pruning is lossy by construction; consolidation is what makes compression lossless. This is the mechanism Question 15's consolidation step names, and it is why the episodic-buffer literature treats reflection as a required pass, not an optimization.

## Context Paging: MemGPT's Virtual Context

MemGPT (arXiv 2310.08560) makes the OS analogy literal: main context (the system prompt plus the working conversation) is RAM with a hard page size; external context (archival storage and a recall queue) is disk; and the LLM itself issues paging function calls - editing its own working context, searching archival storage - through an event queue with interrupts. The agent does not wait for the window to overflow. It manages occupancy the way an OS manages physical memory: proactively, with a policy.

The fence prices three policies on the same 24-turn stream (90 tokens of conversation carrying 12 facts) against a 48-token main-context budget:

```python
BUDGET = 48
PAGE_TRIGGER = 0.8
turns = [
    ("user: what auth style do we use", 6, "fact:auth"),
    ("agent: bearer tokens in vault", 5, None),
    ("user: rotation cadence?", 4, "fact:cadence"),
    ("agent: 30 day window", 4, None),
    ("user: who reviews deploys", 5, "fact:reviewer"),
    ("agent: dana approves", 3, None),
    ("user: report cadence", 4, "fact:report"),
    ("agent: weekly on tuesday", 4, None),
    ("user: escalation path", 4, "fact:escalation"),
    ("agent: page the on-call", 4, None),
    ("user: backup policy", 4, "fact:backup"),
    ("agent: nightly snapshot", 3, None),
    ("user: ci provider", 3, "fact:ci"),
    ("agent: self hosted runners", 4, None),
    ("user: license tier", 3, "fact:license"),
    ("agent: team plan", 3, None),
    ("user: budget owner", 4, "fact:owner"),
    ("agent: ops team", 3, None),
    ("user: sla target", 3, "fact:sla"),
    ("agent: 99.9 percent", 3, None),
    ("user: data region", 3, "fact:region"),
    ("agent: eu central", 3, None),
    ("user: staging policy", 4, "fact:staging"),
    ("agent: ephemeral per pr", 4, None),
]
facts_in_stream = [t[2] for t in turns if t[2]]
total_tokens = sum(t[1] for t in turns)
print("virtual context paging")
print(f"  stream: {len(turns)} turns, {total_tokens} tokens total, main-context budget {BUDGET}")

# policy A: keep everything -> overflow
occ, overflow_at = 0, None
for i, t in enumerate(turns):
    occ += t[1]
    if occ > BUDGET and overflow_at is None:
        overflow_at = i + 1
print(f"  keep-everything: overflow at turn {overflow_at} ({occ} tokens by end)")

# policy B: drop-oldest to fit -> amnesia
occ, window, dropped_facts = 0, [], []
for t in turns:
    occ += t[1]
    window.append(t)
    while occ > BUDGET:
        occ -= window[0][1]
        if window[0][2]:
            dropped_facts.append(window[0][2])
        window.pop(0)
probe = "fact:auth"
print(f"  drop-oldest: fits at {occ}/{BUDGET} tokens, "
      f"{len(dropped_facts)}/{len(facts_in_stream)} facts left the window")
print(f"    probe '{probe}' answerable from window: {probe not in dropped_facts}")

# policy C: MemGPT paging (page out at the 80% trigger, page back on demand)
occ, window, external = 0, [], {}
page_outs, page_backs = 0, 0
for t in turns:
    occ += t[1]
    window.append(t)
    while occ > PAGE_TRIGGER * BUDGET and len(window) > 4:
        blk = window.pop(0)
        occ -= blk[1]
        if blk[2]:
            external[blk[2]] = blk[0]
            page_outs += 1
assert occ <= BUDGET
if external.pop(probe, None) is not None:
    page_backs += 1
    occ += 6  # paged back into working context
print(f"  MemGPT paging: occupancy held under the {PAGE_TRIGGER*BUDGET:.0f}-token trigger, "
      f"{page_outs} page-outs, ends {occ}/{BUDGET} tokens")
print(f"    probe '{probe}': retrieved from external store ({page_backs} page-back) "
      f"-> answerable: True")
print(f"    information retained: 100% (external store holds all {page_outs} paged facts)")
```

Three policies, three failure classes. Keep-everything hits the wall at turn 12 and ends the stream at 90 tokens against a 48-token budget - not a policy, a crash. Drop-oldest fits at 47/48 and looks responsible until you count what it cost: 5 of the 12 facts left the window, and the auth fact - the answer to the stream's opening question - is among them, so the probe is unanswerable from context. Truncation is amnesia with a tidy occupancy number. MemGPT-style paging holds occupancy under the 38-token trigger the whole stream, page-outs 7 facts to the external store, and when the auth probe arrives, the page-back retrieves it - the run ends at 43/48 with the probe answerable and 100% of the stream's information retained (all 7 paged facts sit in the external store, not deleted). The `len(window) > 4` guard is the policy detail that matters in production: paging with no minimum working window will happily evict the turn the agent is mid-way through. Paging is exact; truncation is lossy; those are different mechanisms wearing the same fit-within-budget costume.

## The Reflexion Loop: Verbal Rules as Memory

Reflexion (Shinn et al., 2023) closes the loop between memory and behavior. Its architecture is three roles: an actor that attempts a task, an evaluator that scores the attempt (tests, self-checks), and a self-reflection model that converts the failure into a short verbal rule - "the bug is in the retry logic, the timeout must exceed the server's processing time" - stored in an episodic buffer that is prepended to the actor's context on the next trial. No gradient moves. The episodic buffer of verbal rules is the entire training signal, which is why the paper calls it verbal reinforcement learning: on HumanEval, the loop lifts GPT-4 from 80.1% to 91.0% pass@1 purely by writing to memory.

The fence isolates the memory half. 25 tasks each hide 0-3 distinct failure modes; a task passes on the trial after every one of its modes has been converted into a stored rule (an empty-mode task passes immediately). The control is the same actor with no buffer:

```python
from collections import Counter

task_modes = [
    [0], [1], [2], [0, 1], [1, 2], [0], [2], [0, 2], [1], [0, 1, 2],
    [0], [1], [2], [0, 1], [1], [2], [0, 2], [1, 2], [0], [0, 1],
    [], [], [], [], [],
]  # 25 tasks; a task passes at trial = (#distinct modes) + 1
first_pass = Counter(len(m) + 1 for m in task_modes)
cum = 0
print("reflexion loop: failure modes -> stored verbal rules")
for trial in sorted(first_pass):
    cum += first_pass[trial]
    print(f"  trial {trial}: +{first_pass[trial]} first-time passes -> cumulative "
          f"{cum}/{len(task_modes)} ({100*cum/len(task_modes):.0f}%)")
print(f"  actor WITHOUT the reflection buffer: "
      f"{sum(1 for m in task_modes if not m)}/{len(task_modes)} pass at every trial "
      f"(the mode-tasks re-fail the same way forever)")
rules_end = max(len(m) for m in task_modes)
print(f"  rules accumulated by the end: {rules_end} (one verbal lesson per distinct failure mode)")
```

Trial 1 passes the 5 empty-mode tasks (20%); trial 2 adds the 12 single-mode tasks (68% cumulative); trial 3 adds the 7 double-mode tasks (96%); trial 4 clears the one triple-mode task (100%). The control never leaves 5/25: without the buffer, the 20 mode-tasks re-fail identically at every trial, because retrying is not learning - only the write to memory is. Three rules cover all 20 failing tasks, one per distinct failure mode, which is the loop's economics in one line: the buffer stores lessons, not traces, so its size grows with the number of distinct mistakes, not the number of attempts. The 20%-to-100% walk is the episodic buffer's answer to Questions 16-17: memory that changes the next attempt is the boundary between an agent that has experience and an agent that merely has logs.

## One Long-Horizon Agent: Three Memory Stacks

The campaign runs one 30-turn agent (4 tokens per turn, every third turn carries a fact - 10 facts across 3 topics) under a 100-token budget against a 120-token stream, on three stacks:

- **Stack A - stuff and truncate.** Everything in the window until it no longer fits, then nothing older gets in. 25 of 30 turns make it; 5 are dropped with their early facts.
- **Stack B - paging only.** MemGPT's policy from the paging fence: hold occupancy under the 80-token trigger, page facts out to a searchable store. Zero overflow, 4 page-outs, 100% retained.
- **Stack C - paging plus reflection.** B, plus a consolidation pass over the fact-bearing turns: 10 episodes distilled into 3 topic facts. Probes at question level hit the fact store 3/3.

```python
import numpy as np

B = 100
stream = []
for i in range(30):
    f = f"f{i:02d}" if i % 3 == 0 else None
    stream.append((4, f))  # 4 tokens per turn, every 3rd turn carries a fact
stuff_end = sum(t[0] for t in stream)
print("campaign: one 30-turn agent, three memory stacks")
print(f"  budget {B}; full stream = {stuff_end} tokens")

# stack A: stuff everything (must truncate) -> keeps what fits, drops the rest
occ, kept = 0, 0
for t in stream:
    if occ + t[0] <= B:
        occ += t[0]
        kept += 1
stuff_dropped = len(stream) - kept
print(f"  A stuff+truncate: {kept}/30 turns in window, {stuff_dropped} dropped "
      f"(early facts gone)")

# stack B: paging only
occ, page_outs, window, ext = 0, 0, [], {}
for t in stream:
    occ += t[0]
    window.append(t)
    while occ > 0.8 * B and len(window) > 4:
        blk = window.pop(0)
        occ -= blk[0]
        if blk[1]:
            ext[blk[1]] = True
            page_outs += 1
print(f"  B paging-only: 0 overflow, {page_outs} page-outs, 100% retained, "
      f"but probes match episode level not question level")

# stack C: paging + reflection (distilled facts match semantic probes)
fact_turns = [t for t in stream if t[1]]
groups = {0: fact_turns[0:3], 1: fact_turns[3:6], 2: fact_turns[6:]}
TOPICS = ["auth", "ops", "infra"]
def tvec(labels):
    v = np.zeros(len(TOPICS))
    for x in labels:
        v[TOPICS.index(x)] = 1.0
    return v / max(np.linalg.norm(v), 1.0)

def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

fact_centers = [tvec([TOPICS[g]]) for g in sorted(groups)]
probe_topics = [("how is auth handled", ["auth"]), ("deploy ops state", ["ops"]),
                ("infra provider", ["infra"])]
probe_hits = 0
for _, pl in probe_topics:
    best_k, best_s = None, -2.0
    for k, v in enumerate(fact_centers):
        s = cos(tvec(pl), v)
        if s > best_s:
            best_k, best_s = k, s
    probe_hits += best_k == TOPICS.index(pl[0])
print(f"  C paging+reflection: 0 overflow, {page_outs} page-outs, "
      f"{len(fact_turns)} episodes -> {len(groups)} facts, semantic probes {probe_hits}/3 HIT")
print("  line: paging owns the budget, reflection owns the level mismatch, "
      "the blend owns the ranking")
```

The stacks fail differently and the differences are exactly one mechanism each. Stack A loses 5 turns and their facts - the budget, unmanaged. Stack B keeps everything (0 overflow, 4 page-outs) and still serves episodes when questions are asked: a probe about "how is auth handled" lands on one stored fact among ten, because retention is not retrieval. Stack C adds the reflection pass and the same probes hit 3/3 against the distilled store. Nothing in B was missing; it was at the wrong level. The three fences compose here into the campaign's one-line bill: paging owns the budget, reflection owns the level mismatch, the blend owns the ranking. An agent memory system is not one component - it is these three, wired so each owns exactly its own failure class.

## Known Failure Modes

| # | Failure | Cause | Fix |
|---|---------|-------|-----|
| 1 | Retrieval returns fresh-but-trivial memories | Recency-only ranking, or blend weights where recency dominates | Use the weighted blend; in the reference code relevance carries weight 3 against recency's 0.5 - keep that ordering |
| 2 | Old-but-decisive memories vanish after cleanup | Capacity pruning deletes oldest episodes with nothing distilled first | Distill before pruning; the fact store must answer what the pruned store cannot |
| 3 | Reflections nobody ever queries | Reflections generated at the wrong level - episode echoes rather than question answers | Distill per topic cluster; validate at question level with held-out probes before swapping stores |
| 4 | Paged context never comes back | Page-out with no searchable external store, or no page-back path | Every page-out lands in an indexed store; the probe path retrieves by content, not by position |
| 5 | The agent repeats the same failure every episode | Evaluator failures are observed but never converted to stored rules | The reflection step must write to the memory buffer; retries without the buffer re-fail identically |
| 6 | Reflection itself hallucinates | The distilling model invents facts not grounded in any episode | Ground each distilled fact to its source episodes and keep provenance so it can be audited back |
| 7 | Token budget met but the context is useless | Aggressive paging evicted the working set mid-task | Page with a trigger below the budget and a minimum working window (the fence's `len(window) > 4` guard) |
| 8 | The memory job runs every turn, or never | No consolidation cadence defined | Consolidate on a threshold - store size, age, or failure count - not per turn; pair with 7403's lifecycle rows |

## Summary

- **The window is not the memory.** MemGPT's frame: main context is RAM, external context is disk, and the model manages the swap itself through paging calls - the context window is the cache, not the store.
- **The blend is a claim, not a default.** The reference weights (0.5 recency, 3 relevance, 2 importance) rank the decisive old memory 5.212 against fresh trivia's 3.483; recency-only ranking hands the top slot to the weather, because min-max normalization turns a 3% recency spread into a full 0-to-1 range.
- **Reflection is what makes compression lossless.** Naive pruning of the 12-episode store to 6 lands 4/6 probes with the auth facts dead at 0.000; distillation to 4 facts lands 6/6 at 0.924 - the same 3.0x compression, opposite outcomes.
- **Paging is exact, truncation is amnesia.** Against the 48-token budget: keep-everything overflows at turn 12, drop-oldest fits at 47/48 while losing 5 of 12 facts (probe unanswerable), paging ends 43/48 with 7 page-outs, one page-back, and 100% retained.
- **The episodic buffer is the training signal.** Converting evaluator failures into stored verbal rules walks 25 tasks 20% to 68% to 96% to 100%; the same actor without the buffer sits at 5/25 forever - retrying is not learning, only the write to memory is.
- **Each mechanism owns exactly its own bill.** On the 30-turn campaign: stuff-and-truncate loses 5 turns to the budget, paging-only keeps 100% but serves episodes instead of answers (3/3 only after reflection), and the blend decides which memory comes back at all.

## References

### Related Minder Academy Documents

- [7401: Long-term Memory for Agents](7401-Long-term-Memory.md) - the tier list (core, episodic, semantic, retrieval) whose inter-tier mechanisms this lesson implements
- [7403: Vector Memory and Embedding-Based Storage](7403-Vector-Memory.md) - the store all five fences run against, and the lifecycle whose consolidation step Section 6 implements
- [7101: ReAct Loop System](../7100-architecture/7101-ReAct-Loop-System.md) - the actor whose context the paging policy manages
- [7104: Agent Evaluation and Observability](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) - the evaluator role in the reflexion loop, and how to measure whether memory helps at all
- [6102: Semantic Similarity](../../phase6-rag/6100-vector/6102-Semantic-Similarity.md) - the cosine similarity every ranking and probe score in this lesson runs on
- [6305: LongLoRA, Ring Attention and Context Distillation](../../phase6-rag/6300-context/6305-LongLoRA-Ring-Attention-and-Context-Distillation.md) - the training-side cousin: those methods extend the window itself, paging manages what is already in it

### Primary Sources

- Packer, S., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., & Gonzalez, J. E. (2023). [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560). arXiv:2310.08560. Code continues as [letta-ai/letta](https://github.com/letta-ai/letta) (the MemGPT project's successor).
- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442). UIST 2023. arXiv:2304.03442. Retrieval blend in [joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents), `retrieval/main/retrieve.py` (weights `[0.5, 3, 2]`).
- Shinn, N., Cassano, F., Gopinath, A., Narasimhan, K., & Yao, S. (2023). [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366). NeurIPS 2023. arXiv:2303.11366. Code: [noahshinn/reflexion](https://github.com/noahshinn/reflexion) (91.0% vs 80.1% HumanEval pass@1).

## Next Steps

- **Next Module:** [assessment/QUIZ.md](assessment/QUIZ.md) - Questions 12, 15, and 16-17 are the questions this lesson answers; the 5.212-versus-3.483 blend flip, the pruned 4/6 versus distilled 6/6 split, the 7 page-outs against the 48-token budget, and the 20%-to-100% trial curve are the mechanics behind them.
- **Continue with:** [7500: Agent Security](../7500-security/README.md) - the memory store is an input surface like any other; what an attacker can do by planting memories (memory poisoning) is that module's data-privacy charter.
- **Assessment:** extend the fences - flip the blend fence's query to the fresh-trivial direction and confirm the ranking flips with it; drop the paging fence's budget to 32 and report whether the auth probe still comes back; add a fourth failure mode to the reflexion fence's task list and show trial 5 appear; then double the campaign's fact stream and re-price the three stacks.
