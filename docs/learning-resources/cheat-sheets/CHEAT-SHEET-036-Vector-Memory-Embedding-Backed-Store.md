---
Document ID: CHEAT-SHEET-036
Title: "CHEAT-SHEET-036: Vector Memory - the Embedding-Backed Store"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'agents', 'memory', 'vector-store']
---

# CHEAT-SHEET-036: Vector Memory - the Embedding-Backed Store

**Quick Reference for:** the store that turns agent recall into nearest-neighbor search - the four memory types and their storage shapes, the write path that extracts one atomic statement per memory behind an importance gate, the read path that ranks by similarity x decay x importance and stops at a token budget, the Qdrant contract (guarded create, payload indexes, versioned collections), the three lifecycle jobs that keep memory useful over months, and the ledger where 1M memories cost ~1.5 GB but 300-500 recall tokens per turn are the real currency. CHEAT-SHEET-025 owns the memory system map - this sheet owns the embedding-backed store itself: the metadata schema, the two code paths the agent loop touches, and the offline jobs everything else runs on. The rule it leaves: design the metadata schema before the first memory is written, because you cannot filter on fields you never stored.

## Why Embeddings: Recall as Nearest Neighbor

A fuzzy natural-language recall - "what did we decide about auth last week?" - is unanswerable by key lookup: the answer lives in a dozen scattered memories, none carrying the query's exact words. Embed the memories and the query, and recall becomes nearest-neighbor search: similar meanings land close together in vector space. This conversion is what makes agent memory scalable - but it only works if every memory carries the metadata the recall needs: `type`, `timestamp`, `session_id`, `entities[]`. Vector similarity alone returns stale and off-type noise; the metadata is what turns a pile of embeddings into a queryable memory.

## The Four Memory Types

| type | content | storage shape |
|---|---|---|
| Working | current conversation state | context window |
| Episodic | what happened, when - event + timestamp + entities | event record |
| Semantic | distilled atomic facts, preferences | atomic fact statements |
| Procedural | how to do things | checklist / playbook text |

Two rules fall out of the taxonomy. **Episodic-to-semantic consolidation**: episodes are raw; periodically distill them into semantic facts, because recall of facts beats recall of transcripts. **Metadata is mandatory**: without `type` and `ts` you cannot filter, and without filtering, similarity search hands the agent last quarter's noise at full rank.

## The Write Path: Extract, Embed, Upsert

An LLM extraction pass per exchange turns conversation into memory candidates: one JSON object per memory with a `type`, one atomic `content` statement, and `entities`. The three write rules:

1. **One atomic statement per memory.** "Prefers TypeScript" and "deploys to GCP" are two memories - atomic memories dedup and decay independently; a compound memory decays as a blob and never merges cleanly.
2. **Gate extraction on importance.** Write-time extraction costs one small-model call per exchange (100-400 ms) - gate it on tool errors, explicit user statements, and decisions, or a chatty session burns the budget on filler.
3. **Never store secrets.** Keys and tokens are not memories; filter at write time, because memory is personal data with a deletion surface (TTL, GDPR-style delete-by-user).

## The Read Path: Budgeted Recall

Recall embeds the query, filters, ranks, and injects - in that order:

- **Filters before similarity.** Type and recency constraints prune the candidate set; similarity ranks within it. A `type in [semantic, procedural]` filter is the difference between recalled facts and recalled chatter.
- **Rank by `similarity x decay x importance`, not similarity alone.** Exponential decay (90-day half-life) sinks stale facts; importance keeps load-bearing memories afloat. Raw similarity lets a nine-month-old fact out-rank last week's decision.
- **Stop at the token budget.** The recall walk is newest-first and stops at the cap (300-500 tokens typical, ~400 default) - memory text competes with retrieved documents and the task itself for context.
- **Inject as a clearly-marked block.** Memory woven into the task prompt is memory the model cannot tell apart from the current instruction - label the block and instruct usage.

## The Qdrant Contract

Three rules the store itself imposes:

- **Guarded create.** Check `collection_exists` before `create_collection` - an unguarded `recreate_collection` wipes the agent's entire memory every time the setup script re-runs.
- **Payload indexes on `type` and `entities`.** They turn filtered search from full-scan to index-lookup - 5-20 ms at one million memories instead of a scan that degrades linearly.
- **Versioned collections.** One collection per agent/tenant, named `_v1`, with the embedding model recorded in metadata. Swapping embedding models means a new collection plus a backfill job - never mix vector spaces in one collection, because vectors from two models are not comparable distances.

## The Memory Lifecycle

Memory that only grows becomes noise. Three offline jobs run against the store; the agent loop itself touches memory through exactly two calls (`recall`, `remember`) and nothing else.

```text
decay(age)  = 0.5 ** (age / 90)      # exponential recency, 90-day half-life
recall_score = similarity x decay x importance
```

- **Consolidation** (nightly or per-N-sessions): pull recent episodes, distill them into atomic semantic facts (~1 LLM call per 10 episodes), store the fact with the source episode ids in `payload.provenance`, and mark the episodes consolidated - kept for audit, excluded from recall.
- **Decay** re-ranks recall scores rather than deleting - deletion is a separate, auditable job.
- **Dedup at write**: a new memory whose nearest neighbor exceeds 0.95 cosine is a duplicate; near-identical memories merge in the consolidation pass instead of accumulating into dozens of copies.
- **Deletion policy**: delete-by-user (GDPR-style), TTL per type (episodes 90 days, semantic facts until superseded), and provenance so a deletion cascades to facts distilled from a deleted episode.

MemGPT-style paging - the agent managing its own memory in and out of context - is the dynamic variant. Start with the static budget version; add paging only when recall misses are demonstrably context-fit problems.

## The Ledger: Performance and Cost

| component | typical magnitude | notes |
|---|---|---|
| Embed query | 10-50 ms | same model as the write path - mandatory |
| Filtered ANN search | 5-20 ms @ 1M memories | with payload indexes |
| Write extraction | 100-400 ms / exchange | small LLM, gated on importance |
| Consolidation batch | nightly, ~1 LLM call / 10 episodes | off the hot path |
| Storage | ~1.5 KB / memory incl. payload | 1M memories ~= 1.5 GB |
| Context cost | 300-500 tokens / turn | the real currency |

The storage number flatters: 1.5 GB for a million memories sounds free next to a GPU, but every turn pays 300-500 tokens of recall out of the context budget - at 50 turns a day that is a recurring tax on every conversation, which is why the budget cap and the decay re-rank matter more than the index.

## Known Failure Modes

| failure | lesson |
|---|---|
| Recreate the collection on deploy | unguarded `recreate_collection` wipes the agent's memory on every re-run - check `collection_exists` first |
| Mix embedding models in one collection | vectors from two models are not comparable distances - versioned collections + backfill |
| Rank by similarity alone | stale facts float to the top - re-rank by similarity x decay x importance |
| Store compound memories | "prefers TypeScript and uses GCP" never dedups and decays as a blob - one atomic statement per memory |
| Weave memory into the task prompt | unmarked memory gets ignored - a clearly labeled block the model can tell apart from the instruction |
| Treat storage as the cost | 1.5 GB is trivial; 300-500 recall tokens per turn is the recurring bill - budget cap and decay are the levers |

## References

- Repository, *Module 7403: Vector Memory and Embedding-Based Storage - the full lesson with the Qdrant integration and lifecycle jobs*
- Packer et al., 2023, *MemGPT: Towards LLMs as Operating Systems* - memory paging as OS-style management
- Park et al., 2023, *Generative Agents* - memory stream plus reflection
- Zhong et al., 2024, *MemoRAG* - long-term memory as a retrieval substrate
- Qdrant documentation, *Filtering* - payload filters and indexes
- Repository, *CHEAT-SHEET-025: Agent Memory Systems* - the system-level map this sheet's store implements

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Recall returns stale, irrelevant facts | no recency weighting | similarity x decay re-rank; filter by ts |
| Same memory stored dozens of times | no dedup | 0.95-cosine check at write; consolidation merge |
| Agent ignores injected memories | unmarked or buried block | clearly labeled block near the top; instruct usage |
| Recall misses obviously relevant memory | filter too narrow or threshold too high | loosen the type filter; tune k; check embedding domain fit |
| Context flooded by memory text | no budget | hard token cap on the recall block |
| Vectors return nonsense after a model upgrade | mixed vector spaces | versioned collections; backfill the new space |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 7403: Vector Memory and Embedding-Based Storage](../../phases/phase7-agentic/7400-memory/7403-Vector-Memory.md) | this sheet's source module - the full write/read paths with the Qdrant integration |
| [CHEAT-SHEET-025: Agent Memory Systems](CHEAT-SHEET-025-Agent-Memory-Systems.md) | the memory system map - this store is one layer of it |
| [Module 6101: HNSW Indexing](../../phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md) | the ANN internals under the 5-20 ms search |
| [Module 6401: Qdrant Setup](../../phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md) | the deployment behind the collection contract |

```python
"""CHEAT-SHEET-036 canonical numbers - stdlib only, deterministic."""
import math

print("F1  The four memory types and their storage shape")
tax = [
    ("Working", "current conversation state", "context window"),
    ("Episodic", "what happened, when (event + ts + entities)", "event record"),
    ("Semantic", "distilled atomic facts, preferences", "atomic statements"),
    ("Procedural", "how to do things (playbook)", "checklist text"),
]
for name, content, shape in tax:
    print(f"    {name:10s}  {content:44s} -> {shape}")
print("    rules: consolidate episodic->semantic; metadata (type/ts/session/entities) mandatory")

print()
print("F2  Exponential decay, half-life = 90 days: decay = 0.5 ** (age / 90)")
for age in (0, 30, 90, 180, 365):
    print(f"    age={age:3d}d  decay={0.5 ** (age / 90):.4f}")

print()
print("F3  Budgeted recall: score = similarity x decay x importance, then a token cap")
hits = [
    ("semantic",   0.91, 1.0,   5, 12),
    ("episodic",   0.88, 0.9,   2, 40),
    ("semantic",   0.84, 1.0,  45, 15),
    ("procedural", 0.81, 0.8,  10, 25),
    ("episodic",   0.78, 0.6, 120, 120),
]
scored = []
for htype, sim, imp, age, words in hits:
    dec = 0.5 ** (age / 90)
    scored.append((sim * dec * imp, htype, sim, dec, imp, words))
scored.sort(reverse=True)
for sc, htype, sim, dec, imp, words in scored:
    print(f"    [{htype:10s}] sim={sim:.2f} decay={dec:.4f} imp={imp:.1f}"
          f" -> score {sc:.4f}  ({words} tok)")
budget, used, kept = 90, 0, 0
for sc, htype, sim, dec, imp, words in scored:
    if used + words > budget:
        break                          # newest-first walk stops at the cap
    used += words
    kept += 1
print(f"    mini budget {budget} tok (production runs 300-500): kept {kept}, used {used},"
      f" dropped {len(scored) - kept}")

print()
print("F4  The storage ledger: ~1.5 KB per memory including payload")
for n in (100_000, 1_000_000):
    gb = n * 1.5 / 1e6
    print(f"    {n:>9,} memories x 1.5 KB = {gb:.2f} GB ({gb * 1e9 / 1024**3:.2f} GiB)")
print("    the real currency is context: 300-500 tokens of recall per turn")

print()
print("F5  Dedup at write: cosine > 0.95 merges, else store")
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb)

vec_a = [1.0, 0.0, 1.0, 1.0, 0.0]
pairs = [
    ("near-variant", vec_a, [1.0, 0.0, 1.0, 1.0, 1.0]),
    ("unrelated",    vec_a, [0.0, 1.0, 0.0, 0.0, 1.0]),
    ("exact copy",   vec_a, vec_a),
]
for label, x, y in pairs:
    c = cosine(x, y)
    verdict = "DUP - merge in consolidation" if c > 0.95 else "store as new memory"
    print(f"    {label:12s}  cos={c:.4f}  {verdict}")

print()
print("F6  Configuring recall by workload")
picks = [
    ("support agent, live chat", "types=[semantic, procedural], budget 300, k=5"),
    ("research agent over weeks", "full taxonomy, nightly consolidation, budget 500"),
    ("GDPR delete request", "delete-by-user + provenance cascade, audited"),
]
for workload, pick in picks:
    print(f"    {workload:26s} -> {pick}")

print("DETERMINISTIC-OK")
```

```text
F1  The four memory types and their storage shape
    Working     current conversation state                   -> context window
    Episodic    what happened, when (event + ts + entities)  -> event record
    Semantic    distilled atomic facts, preferences          -> atomic statements
    Procedural  how to do things (playbook)                  -> checklist text
    rules: consolidate episodic->semantic; metadata (type/ts/session/entities) mandatory

F2  Exponential decay, half-life = 90 days: decay = 0.5 ** (age / 90)
    age=  0d  decay=1.0000
    age= 30d  decay=0.7937
    age= 90d  decay=0.5000
    age=180d  decay=0.2500
    age=365d  decay=0.0601

F3  Budgeted recall: score = similarity x decay x importance, then a token cap
    [semantic  ] sim=0.91 decay=0.9622 imp=1.0 -> score 0.8756  (12 tok)
    [episodic  ] sim=0.88 decay=0.9847 imp=0.9 -> score 0.7799  (40 tok)
    [procedural] sim=0.81 decay=0.9259 imp=0.8 -> score 0.6000  (25 tok)
    [semantic  ] sim=0.84 decay=0.7071 imp=1.0 -> score 0.5940  (15 tok)
    [episodic  ] sim=0.78 decay=0.3969 imp=0.6 -> score 0.1857  (120 tok)
    mini budget 90 tok (production runs 300-500): kept 3, used 77, dropped 2

F4  The storage ledger: ~1.5 KB per memory including payload
      100,000 memories x 1.5 KB = 0.15 GB (0.14 GiB)
    1,000,000 memories x 1.5 KB = 1.50 GB (1.40 GiB)
    the real currency is context: 300-500 tokens of recall per turn

F5  Dedup at write: cosine > 0.95 merges, else store
    near-variant  cos=0.8660  store as new memory
    unrelated     cos=0.0000  store as new memory
    exact copy    cos=1.0000  DUP - merge in consolidation

F6  Configuring recall by workload
    support agent, live chat   -> types=[semantic, procedural], budget 300, k=5
    research agent over weeks  -> full taxonomy, nightly consolidation, budget 500
    GDPR delete request        -> delete-by-user + provenance cascade, audited
DETERMINISTIC-OK
```
