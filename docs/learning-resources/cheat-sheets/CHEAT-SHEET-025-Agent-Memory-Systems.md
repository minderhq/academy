---
Document ID: CHEAT-SHEET-025
Title: "CHEAT-SHEET-025: Agent Memory Systems"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'memory', 'agents', 'long-term-memory', 'retrieval']
---

# CHEAT-SHEET-025: Agent Memory Systems

**Quick Reference for:** the four-tier memory map and the two readers, the retrieval blend weights, the write/read paths of an embedding-backed store, the consolidation lifecycle, MemGPT-style context paging, the reflexion loop, TTL leases and eviction policy, and the checkpoint-store contract.

**Version:** 1.0

## The Tier Map and the Two Readers

Module 7400's taxonomy — store each kind in its native shape:

| Type | Content | Storage shape |
|---|---|---|
| Working | current conversation, in-flight task state | the context window |
| Episodic | what happened, when | event record + timestamp + entities |
| Semantic | distilled facts, preferences | atomic fact statements |
| Procedural | how to do things | checklist / playbook text |

Under the tiers sit two readers, and they answer different questions over the same bytes. The key-value store is an **address space** — a read is a hash lookup that lands on the object or misses. The vector store is a **query space** — a read scores candidates and ranks. Module 7405's canonical flip: the exact key `session:42:cart` returns `['sku-1', 'sku-7']` at 84.5 verbatim, while the same "latest cart state" intent through a similarity ranking hands back `doc:101:summary` — a refund policy — because a cart dict has no text to embed.

```text
address known   -> GET session:42:cart     -> ['sku-1', 'sku-7'] at 84.5, verbatim, O(1)
address unknown -> search "refund policy"  -> doc:101:summary (top-1)
route state reads by address, knowledge reads by query -
the error to fear is a wrong object, not a slow one
```

Two design rules fall out of 7403's taxonomy: **episodic → semantic consolidation** (recall of facts beats recall of transcripts), and **metadata is mandatory** — `type`, `timestamp`, `session_id`, `entities[]`; vector similarity alone returns stale, off-type noise, and you cannot filter on fields you never stored.

## The Retrieval Blend: Recency, Importance, Relevance

The generative-agents reference ranks every candidate as a weighted sum of three min-max-normalized components: **recency 0.5** (`0.995**i` over a most-recent-first list), **relevance 3** (cosine to the query), **importance 2** (an LLM-assigned 1-10 poignancy score). The weights are the design claim: relevance dominates, importance doubles recency.

Why recency-only ranking is destructive: the raw recency spread between the newest and oldest memory is 0.995 vs 0.961 — a 3% gap — and min-max normalization blows that up to a full 0-to-1 range. The fence below runs the canonical query ("what do we know about auth rotation?") against 8 memories, 4 fresh and trivial, 4 old and decisive: recency-only hands the top slot to the weather; the blend puts the 3-week-old key-rotation memory first at **5.212** against the freshest trivia's **3.483** — with a *mediocre* recency term (0.42), because relevance (1.00 × 3) and importance (1.00 × 2) carry the score.

```python
# Agent memory: the blend ranks, paging pays the budget, reflection learns.
from collections import Counter

# 1. retrieval blend - recency 0.5, relevance 3, importance 2 (generative-agents)
mems = ["M1 fresh weather", "M2 fresh coffee", "M3 fresh meeting", "M4 fresh news",
        "M5 key rotation", "M6 30-day window", "M7 key revoked", "M8 font gripe"]
V = [[1.0, 0.0], [0.9, 0.1], [0.2, 0.9], [0.0, 1.0],
     [1.0, 0.1], [0.95, 0.15], [1.0, 0.05], [0.1, 0.8]]
q, imp = [1.0, 0.1], [2, 2, 3, 2, 9, 8, 7, 2]

def cos(a, b):
    d = sum(x * y for x, y in zip(a, b))
    return d / ((sum(x * x for x in a) * sum(y * y for y in b)) ** 0.5)

def minmax(v):
    lo, hi = min(v), max(v)
    return [0.5] * len(v) if hi == lo else [(x - lo) / (hi - lo) for x in v]

rec = minmax([0.995 ** (i + 1) for i in range(8)])
rel = minmax([cos(q, v) for v in V])
score = [0.5 * r + 3.0 * l + 2.0 * m for r, l, m in zip(rec, rel, minmax(imp))]
best = max(range(8), key=lambda i: score[i])
print(f"blend: top-1 {mems[best]} score {score[best]:.3f} | fresh trivia M1 {score[0]:.3f}")

# 2. paging - 24 turns / 48-token budget / trigger 0.8 / minimum window 4
turns = [(6, "f:auth"), (5, None), (4, "f:cadence"), (4, None), (5, "f:reviewer"),
         (3, None), (4, "f:report"), (4, None), (4, "f:escalation"), (4, None),
         (4, "f:backup"), (3, None), (3, "f:ci"), (4, None), (3, "f:license"),
         (3, None), (4, "f:owner"), (3, None), (3, "f:sla"), (3, None),
         (3, "f:region"), (3, None), (4, "f:staging"), (4, None)]
facts = [t[1] for t in turns if t[1]]
occ = 0
for i, (tk, _) in enumerate(turns):
    occ += tk
    if occ > 48:
        print(f"keep-everything: overflow at turn {i + 1} ({occ} tokens)")
        break
occ, window, lost = 0, [], []
for tk, f in turns:
    occ += tk
    window.append((tk, f))
    while occ > 48:
        b = window.pop(0)
        occ -= b[0]
        if b[1]:
            lost.append(b[1])
print(f"drop-oldest: fits {occ}/48, {len(lost)}/{len(facts)} facts lost, "
      f"probe f:auth answerable: {'f:auth' not in lost}")
occ, window, ext, outs, backs = 0, [], {}, 0, 0
for tk, f in turns:
    occ += tk
    window.append((tk, f))
    while occ > 0.8 * 48 and len(window) > 4:
        b = window.pop(0)
        occ -= b[0]
        if b[1]:
            ext[b[1]] = True
            outs += 1
if ext.pop("f:auth", None) is not None:
    backs += 1
    occ += 6
print(f"paging: {outs} page-outs, ends {occ}/48, probe page-back {backs}, retained 100%")

# 3. reflexion - failure modes become stored verbal rules, retrying is not learning
modes = [[0], [1], [2], [0, 1], [1, 2], [0], [2], [0, 2], [1], [0, 1, 2],
         [0], [1], [2], [0, 1], [1], [2], [0, 2], [1, 2], [0], [0, 1],
         [], [], [], [], []]
first = Counter(len(m) + 1 for m in modes)
cum = 0
for trial in sorted(first):
    cum += first[trial]
    print(f"reflexion trial {trial}: cumulative {cum}/25 ({100 * cum / 25:.0f}%)")
print(f"actor without the buffer: {sum(1 for m in modes if not m)}/25 at every trial")
```

```text
blend: top-1 M5 key rotation score 5.212 | fresh trivia M1 3.483
keep-everything: overflow at turn 12 (50 tokens)
drop-oldest: fits 47/48, 5/12 facts lost, probe f:auth answerable: False
paging: 7 page-outs, ends 43/48, probe page-back 1, retained 100%
reflexion trial 1: cumulative 5/25 (20%)
reflexion trial 2: cumulative 17/25 (68%)
reflexion trial 3: cumulative 24/25 (96%)
reflexion trial 4: cumulative 25/25 (100%)
actor without the buffer: 5/25 at every trial
```

## Write and Read Paths

Module 7403's write path: LLM extraction (one small-model call per exchange, gated on importance) → **one atomic statement per memory** ("prefers TypeScript" and "uses GCP" are two memories — atomics dedup and decay independently) → embed → upsert with mandatory metadata. Never store secrets as memories — filter at write time.

The read path has three disciplines:

- **Filters before similarity** — type and recency constraints prune the candidate set; similarity ranks *within* it. Payload indexes on `type`/`entities` turn filtered search from full-scan to index-lookup.
- **Token budget** — recall text competes with retrieved documents and the task; memory gets a fixed slice (~300-500 tokens typical), newest-first until the cap.
- **Clearly-marked block** — inject memories as a labeled block, not woven into the task prompt; the model must tell memory from current instruction.

Sizing: embedding-model swaps invalidate every stored vector — version the collection (`agent_memory_v1`), record the model in metadata, plan the backfill *before* the first upgrade. A guarded create beats `recreate_collection`, which wipes the agent's memory on every re-run. Cost profile: embed 10-50 ms, filtered ANN 5-20 ms @ 1M memories, extraction 100-400 ms gated, storage ~1.5 KB/memory (1M ≈ 1.5 GB) — and 300-500 context tokens per turn, the real currency.

## The Lifecycle: Consolidation, Decay, Dedup

An episodic store only grows, and two compression moves are not interchangeable. **Pruning** deletes old episodes; **distilling** derives semantic facts first, then lets the episodes go. The canonical 12-episode / 4-topic bill: pruning to the 6 most recent lands **4/6 probes** with both auth probes dead at **0.000** — the whole auth cluster was dropped, so no amount of cosine can recover it. Distilling to 4 topic facts lands **6/6 at 0.924** mean cosine. Same **3.0x** compression, opposite outcomes: pruning is lossy by construction; consolidation is what makes compression lossless.

- **Decay** re-ranks recall by `similarity × decay × importance` with `0.5 ** (age / 90 days)` — deletion is a separate, auditable job, never an inline side effect.
- **Dedup at write**: near-identical memories (> 0.95 cosine) merge via the consolidation pass instead of accumulating.
- **Deletion policy**: memories are personal data — delete-by-user (GDPR-style), TTL per type (episodes 90d, semantic facts until superseded), and provenance so a deletion cascades to facts distilled from a deleted episode.

## Context Paging: the Window Is the Cache

MemGPT's frame: main context is RAM, external context is disk, and the context window **is not the memory — it is the cache**. The agent manages occupancy like an OS manages physical memory: proactively, with a policy, paging through function calls instead of waiting for the wall. Three policies on the same 24-turn / 90-token stream against a 48-token budget (see the fence):

| Policy | Outcome | Failure class |
|---|---|---|
| Keep-everything | overflows at turn 12 (50 tokens) | not a policy — a crash |
| Drop-oldest | fits 47/48, loses 5 of 12 facts, probe unanswerable | amnesia with a tidy occupancy number |
| Paging (trigger 0.8, page-back on demand) | 43/48, 7 page-outs, 1 page-back, 100% retained | none — exact, not lossy |

The production guard is `len(window) > 4`: paging with no minimum working window will happily evict the turn the agent is mid-way through. **Paging is exact; truncation is lossy** — different mechanisms wearing the same fit-within-budget costume.

## The Reflexion Loop: Verbal Rules as Memory

Three roles: an **actor** attempts the task, an **evaluator** scores the attempt, a **self-reflection model** converts the failure into a short verbal rule stored in an episodic buffer that is prepended to the actor's context on the next trial. No gradient moves — the buffer of verbal rules is the entire training signal, which is why the paper calls it verbal reinforcement learning (on HumanEval it lifts GPT-4 from 80.1% to 91.0% pass@1 purely by writing to memory). The fence's 25-task walk: trial 1 clears the 5 empty-mode tasks (20%), trial 2 the single-mode tasks (68%), trial 3 (96%), trial 4 (100%) — while the same actor *without* the buffer sits at 5/25 forever, because the 20 mode-tasks re-fail identically: **retrying is not learning; only the write to memory is**. The buffer's economics: it stores lessons, not traces — 3 rules cover all 20 failing tasks, so its size grows with distinct mistakes, not attempts.

## TTL Leases, Eviction, and the Checkpoint Contract

**TTL is a lease, not a timestamp.** The deadline is an absolute wall-clock reading (an NTP jump can expire healthy leases wholesale). Two enforcement mechanisms: **passive** (tested on access — a key written and never read again is dead weight forever) and **active** (sample 20 keys per pass, keep going while stale > 25%, cap 25% CPU). Passive-only leaves 396 of 678 resident keys dead-but-lingering — **58.4%** expired inventory; the active cycle drives it to 63 of 344 (**18.3%**, the algorithm's own design point, not a failure). And the bug that eats production: **a plain `SET` overwrite clears the TTL silently** — 50/50 session keys immortal in the fence; the guarded form (re-issue `SET ... EX` or `EXPIRE` after every write; `NX/XX/GT/LT` since Redis 7.0) keeps 50/50 on schedule. No error, no log — and invisible to `expired_keys`.

**Eviction aims the burden; it does not shrink it.** One shared instance, `maxmemory` bound: `noeviction` (the default) rejects 287 writes; `allkeys-lru` evicts 51 keys — **every one a checkpoint** (the LRU-cold durable keys are exactly what a TTL'd workload leaves cold); `volatile-lru` evicts 1,040 keys — **none of them checkpoints** — and once no TTL keys remain it silently degrades to `noeviction` (0/50 burst writes accepted). LRU/LFU are sampled (5 candidates), not exact. Fix: namespace discipline or separate instances — the docs' own advice; tripwires: rising `evicted_keys` on an instance holding checkpoints.

**The checkpoint store is a KV contract** — the store 7404's paging and the orchestration interrupt/resume land in. With `langgraph-checkpoint-redis`: `RedisSaver.from_conn_string(...)` plus a mandatory `setup()` (creates the RediSearch indices), RedisJSON + RediSearch required (bundled in Redis 8.0+), plain client not cluster. Three decisions price it:

- **Shape**: full history is 30 keys / 2,740 B against 1 key / 92 B shallow — a **30x** multiple, linear in run length; time travel to step 18 is served from history and gone forever from shallow.
- **Lease**: `ttl={"default_ttl": 60, "refresh_on_read": True}`. A fixed 60-minute lease on a thread that crashed at step 20 and idles 2 hours returns `None` at the t+120 resume — silent data loss; refresh-on-read extends the lease on every poll and the resume restores state.
- **The ledger** (50,000 sessions/day, 24 KB checkpoint, 10% ever resume, attempts land 1-96 h):

| Config | day-30 GB | Resume success |
|---|---|---|
| none (no TTL) | 34.33 — grows 1.14 GB/day, OOMs a 16 GB box on day 14.0 | 1.00 theoretical |
| ttl24-passive | 31.93 — the never-read 90% is never reaped | 0.25 |
| ttl24-active | 1.14 flat — the cycle buys the memory bound | 0.24 |
| ttl168-refresh (7d + refresh-on-read) | 12.59 and holding | **1.00** |

The knobs are orthogonal and all mandatory: **TTL length is the resume budget, the active cycle is the memory bound, refresh-on-read is the hot-thread insurance** — a configuration missing any one pays in exactly the column it names.

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| recall returns fresh trivia, decisive old memory buried | recency-only ranking; min-max blows a 3% spread into 0-1 | weighted blend 0.5 / 3 / 2 — keep relevance's 6x edge over recency |
| old-but-decisive memories vanish after cleanup | pruning without distilling | distill before prune — 12→6 lands 4/6, 12→4 lands 6/6 at 0.924 |
| agent ignores injected memories | block unmarked or buried mid-prompt | clearly labeled block near the top, token-budgeted, usage instructed |
| session keys immortal, store grows forever | plain `SET` overwrite clears the TTL | re-issue `SET ... EX` / `EXPIRE` after every write; alert on leaseless keys |
| writes start failing under maxmemory | `volatile-*` with no TTL keys left degrades to `noeviction` | namespace discipline or separate instances; alert on rejected writes |
| resume after idle returns `None`, no error | `default_ttl` shorter than the resume horizon, refresh off | TTL from the resume SLA + `refresh_on_read=True`; treat expiry as data loss |

## Quick Reference For

- [Module 7401: Long-term Memory for Agents](../../phases/phase7-agentic/7400-memory/7401-Long-term-Memory.md)
- [Module 7404: Reflective Memory and Context Paging](../../phases/phase7-agentic/7400-memory/7404-Reflective-Memory-and-Context-Paging.md)
- [Module 7405: Key-Value Memory and Checkpoint Stores](../../phases/phase7-agentic/7400-memory/7405-Key-Value-Memory-and-Checkpoint-Stores.md)
- [CHEAT-SHEET-024: Multi-Agent Orchestration](./CHEAT-SHEET-024-Multi-Agent-Orchestration.md)
