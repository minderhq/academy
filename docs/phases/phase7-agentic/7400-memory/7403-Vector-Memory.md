---
Document ID: 7403
Title: "7403: Vector Memory and Embedding-Based Storage"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
---

# 7403: Vector Memory and Embedding-Based Storage

## Abstract

Agent memory becomes scalable when memories are embeddings: a fuzzy,
natural-language recall ("what did we decide about auth last week?")
turns into nearest-neighbor search. This document covers the memory
taxonomy, the write/read paths of an embedding-backed memory store, a
Qdrant integration, the memory lifecycle (consolidation, decay, dedup),
and a reference long-term memory architecture with token-budgeted recall.

---

## Table of Contents

- [1. Overview](#1-overview)
- [Learning Objectives](#learning-objectives)
- [2. Memory Taxonomy](#2-memory-taxonomy)
- [3. Write Path: Creating Memories](#3-write-path-creating-memories)
- [4. Read Path: Semantic Recall](#4-read-path-semantic-recall)
- [5. Qdrant Integration](#5-qdrant-integration)
- [6. Memory Lifecycle](#6-memory-lifecycle)
- [7. Long-Term Memory Architecture](#7-long-term-memory-architecture)
- [8. Performance & Cost](#8-performance--cost)
- [9. Troubleshooting](#9-troubleshooting)
- [10. References](#10-references)

---

## 1. Overview

### 1.1 Prerequisites

- [7401: Long-term Memory](./7401-Long-term-Memory.md) - memory fundamentals
- [6102: Semantic Similarity](../../phase6-rag/6100-vector/6102-Semantic-Similarity.md) - embeddings
- [6401: Qdrant Setup](../../phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md) - deployment

## Learning Objectives
After completing this document, you will:
- ✅ Distinguish episodic, semantic, and procedural memories and store each appropriately
- ✅ Implement the write path: consolidation → embed → metadata-indexed store
- ✅ Implement budgeted recall: embed query → filtered top-k → inject
- ✅ Run consolidation, decay, and dedup so memory stays useful over months
- ✅ Size embedding latency, storage, and token budget for production

---

## 2. Memory Taxonomy

| Type | Content | Example | Storage shape |
|------|---------|---------|---------------|
| **Working** | Current conversation context | In-flight task state | Context window |
| **Episodic** | What happened, when | "User reported 500s on /checkout on 2026-09-20" | Event record + timestamp + entities |
| **Semantic** | Distilled facts, preferences | "User prefers TypeScript; deploys to GCP" | Atomic fact statements |
| **Procedural** | How to do things | "Their release flow: tag → CI → staged rollout" | Checklist/playbook text |

Two design rules fall out of the taxonomy:
- **Episodic → semantic consolidation**: episodes are raw; periodically
  distill them into semantic facts (Section 6) — recall of facts beats
  recall of transcripts
- **Metadata is mandatory**: `type`, `timestamp`, `session_id`,
  `entities[]` — vector similarity alone returns stale and off-type noise

---

## 3. Write Path: Creating Memories

```python
from datetime import datetime, timezone

WRITE_PROMPT = """Extract durable memories from this exchange.
Return one JSON object per memory: {"type": "episodic|semantic|procedural",
"content": "<one atomic statement>", "entities": [str]}
Exchange:
{exchange}"""

def remember(llm, store, embed, exchange: str, session_id: str):
    for m in parse_json_objects(llm(WRITE_PROMPT.format(exchange=exchange))):
        mem = {
            "type": m["type"],
            "text": m["content"],
            "entities": m["entities"],
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
        }
        store.upsert(
            id=uuid4().hex,
            vector=embed(mem["text"]),
            payload=mem,
        )
```

**Where:**
- **One atomic statement per memory**: "prefers TypeScript" and "uses
  GCP" are two memories — atomic memories dedup and decay independently
- **Write-time LLM extraction** costs one small-model call per exchange;
  gate it on exchange importance (tool errors, explicit user statements,
  decisions) to control spend
- Never store secrets (keys, tokens) as memories — filter at write time

---

## 4. Read Path: Semantic Recall

```python
RECALL_TEMPLATE = """Relevant memories about this user/project:
{memories}
Use them if relevant; ignore if not."""

def recall(embed, query: str, k=5, token_budget=400,
           types=None, entities=None):
    hits = search(                      # Qdrant layer defined in section 5
        vec=embed(query),
        k=k,
        types=types,                    # e.g. ["semantic", "procedural"]
        entities=entities,
    )
    lines, used = [], 0
    for h in hits:                       # budgeted: newest-first, stop at cap
        line = f"- [{h.payload['type']}] {h.payload['text']}"
        if used + len(line.split()) > token_budget:
            break
        lines.append(line)
        used += len(line.split())
    return RECALL_TEMPLATE.format(memories="\n".join(lines)) if lines else ""
```

**Where:**
- **Filters before similarity**: type and recency constraints prune the
  candidate set; similarity ranks within it
- **Token budget cap**: recall text competes with retrieved documents and
  the task itself — memory gets a fixed slice (~300-500 tokens typical)
- Inject memories as a **clearly-marked block**, not woven into the task
  prompt — the model must be able to tell memory from current instruction

---

## 5. Qdrant Integration

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType, PointStruct, Filter, FieldCondition, MatchAny

client = QdrantClient(url="http://localhost:6333")

# one collection per agent/tenant; named vector = embedding model version.
# Guarded create - recreate_collection would wipe the agent's memory
# every time this snippet re-runs.
if not client.collection_exists("agent_memory_v1"):
    client.create_collection(
        collection_name="agent_memory_v1",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
# payload indexes make filtered recall fast
client.create_payload_index("agent_memory_v1", "type", PayloadSchemaType.KEYWORD)
client.create_payload_index("agent_memory_v1", "entities", PayloadSchemaType.KEYWORD)

def upsert(mem_id, vec, payload):
    client.upsert("agent_memory_v1", [PointStruct(id=mem_id, vector=vec, payload=payload)])

def search(vec, k=5, types=None, entities=None):
    must = []
    if types:
        must.append(FieldCondition(key="type", match=MatchAny(any=types)))
    if entities:
        must.append(FieldCondition(key="entities", match=MatchAny(any=entities)))
    return client.query_points(
        "agent_memory_v1", query=vec, limit=k,
        query_filter=Filter(must=must) if must else None,
    ).points
```

- **Named/versioned collections**: swapping embedding models means a new
  collection plus backfill — never mix vector spaces in one collection
- **Payload indexes** on `type`/`entities` turn filtered search from
  full-scan to index-lookup

---

## 6. Memory Lifecycle

Memory that only grows becomes noise. Three maintenance jobs:

### 6.1 Consolidation (episodic → semantic)

```text
nightly / per-N-sessions:
  1. Pull recent episodes for a session/user
  2. LLM distillation: merge into atomic semantic facts
     ("3 debugging sessions on /checkout" -> "recurring pain: /checkout latency")
  3. Store semantic fact; keep source episode ids in payload.provenance
  4. Mark episodes as consolidated (kept for audit, excluded from recall)
```

### 6.2 Decay & Dedup

```python
def decay_score(payload, now, half_life_days=90):
    age = (now - parse_ts(payload["ts"])).days
    return 0.5 ** (age / half_life_days)     # exponential recency

def is_duplicate(new_vec, store, threshold=0.95):
    hits = store.search(vector=new_vec, k=1)
    return hits and hits[0].score > threshold
```

- **Decay** re-ranks recall by `similarity × decay × importance` rather
  than deleting outright — deletion is a separate, auditable job
- **Dedup at write**: near-identical memories (>0.95 cosine) merge via
  the consolidation pass instead of accumulating

### 6.3 Deletion Policy

Memories are personal data. Support: delete-by-user (GDPR-style), TTL per
memory type (episodes 90d, semantic facts until superseded), and
provenance so a deletion cascades to facts distilled from a deleted
episode.

---

## 7. Long-Term Memory Architecture

```text
┌─────────────────────────── Agent Loop (7101) ───────────────────────────┐
│                                                                          │
│   turn start ──► recall() ──► inject memory block (≤400 tok)             │
│      │                                                                   │
│   turn end ───► remember() ──► extract ──► embed ──► upsert              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                          │                        ▲
                    write path                read path
                          ▼                        │
              ┌──────────────────────────────────────┐
              │        Vector store (Qdrant)          │
              │  collection: agent_memory_v1           │
              │  payload: type, ts, entities, session  │
              └──────────────────────────────────────┘
                          ▲
              ┌───────────────────────────┐
              │  Memory manager (batch)    │
              │  consolidate · decay ·     │
              │  dedup · delete · backfill │
              └───────────────────────────┘
```

- The agent loop touches memory through exactly two calls (`recall`,
  `remember`) — everything else is an offline memory-manager job
- MemGPT-style paging (self-managed memory in/out of context) is the
  dynamic variant: the agent itself decides what to pin and evict;
  start with the static budget version, add paging only when recall
  misses are demonstrably context-fit problems

---

## 8. Performance & Cost

| Component | Typical magnitude | Notes |
|-----------|-------------------|-------|
| Embed query | 10-50 ms | Same model as write path — mandatory |
| Filtered ANN search | 5-20 ms @ 1M memories | With payload indexes |
| Write extraction (small LLM) | 100-400 ms / exchange | Gate on importance |
| Consolidation batch | Nightly, ~1 LLM call / 10 episodes | Off the hot path |
| Storage | ~1.5 KB / memory incl. payload | 1M memories ≈ 1.5 GB |
| Context cost | 300-500 tokens / turn | The real currency |

> **📊 Rule of Thumb:**
> Embedding-model swaps invalidate every stored vector. Version the
> collection (`_v1`), record the model name in collection metadata, and
> plan the backfill job before the first model upgrade, not after.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Recall returns stale/irrelevant facts | No recency weighting | similarity × decay ranking; filter by ts |
| Same memory stored dozens of times | No dedup | 0.95-cosine dedup at write; consolidation pass |
| Agent ignores injected memories | Memory block unmarked or buried | Clearly labeled block near the top; instruct usage |
| Recall misses obviously relevant memory | Filter too narrow / threshold too high | Loosen type filter; tune k; check embedding domain fit |
| Context flooded by memory text | No budget | Hard token cap on recall block |
| Search slow at scale | Missing payload indexes | Index `type`/`entities`; check HNSW config ([6101](../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)) |
| Vectors nonsense after model upgrade | Mixed vector spaces | Versioned collections + backfill |

---

## 10. References

### Academic Papers / Systems
- [1] Packer et al. "MemGPT: Towards LLMs as Operating Systems". 2023.
- [2] Park et al. "Generative Agents: Interactive Simulacra of Human Behavior". UIST, 2023. (memory stream + reflection)
- [3] Zhong et al. "MemoRAG: Boosting Long-Term Memory for LLMs". 2024.

### Documentation
- [Qdrant Filtering](https://qdrant.tech/documentation/search/filtering/) - payload filters and indexes

### Related PROJECT-OMEGA Documents
- [7401: Long-term Memory](./7401-Long-term-Memory.md) - memory fundamentals
- [6101: HNSW Indexing](../../phase6-rag/6100-vector/6101-HNSW-Indexing.md) - ANN internals
- [6102: Semantic Similarity](../../phase6-rag/6100-vector/6102-Semantic-Similarity.md) - embedding fundamentals
- [6401: Qdrant Setup](../../phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md) - deployment

---

## Next Steps

- Review: **[7401: Long-term Memory](./7401-Long-term-Memory.md)**
- Retrieval: **[6203: Advanced Retrieval Techniques](../../phase6-rag/6200-retrieval/6203-Advanced-Retrieval.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**

---

**Document ID:** 7403
**Status:** Complete
**Related Documents:** [7401, 6101, 6102, 6401]
