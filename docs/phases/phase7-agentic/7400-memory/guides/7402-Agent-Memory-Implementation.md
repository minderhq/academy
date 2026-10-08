---
Document ID: 7402
Title: "7402: Agent Memory Implementation Guide"
Phase: 7
Module: 7400
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'memory', 'qdrant', 'postgresql', 'pgvector', 'embeddings']
---

# 7402: Agent Memory Implementation Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Memory Architecture](#memory-architecture)
- [Memory Types Comparison](#memory-types-comparison)
- [Implementation 1: VectorStore (Semantic Memory)](#implementation-1-vectorstore-semantic-memory)
- [Implementation 2: Memoria (Episodic Memory)](#implementation-2-memoria-episodic-memory)
- [Implementation 3: Unified Memory System](#implementation-3-unified-memory-system)
- [Memory Forgetting Strategy](#memory-forgetting-strategy)
- [Quick Start](#quick-start)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Diagram the three-tier memory architecture and name the storage backing each tier
- Read the memory-types comparison and pick the tier that satisfies a given duration, size, and retrieval requirement
- Trace a VectorStore.add_memory call from raw content to a Qdrant point (ID, embedding, payload)
- Break down how Memoria separates episodes from embeddings and when the pgvector similarity join runs
- Run the forgetting-curve math on a memory profile and predict whether it survives the forget threshold
- Decide when to consolidate short-term context into episodic storage instead of keeping it in the rolling window

---

## Abstract
Complete implementation guide for building persistent memory systems for AI agents. Covers VectorStore for semantic memory (Qdrant) and Memoria for episodic memory (PostgreSQL + pgvector), a unified three-tier system, and an Ebbinghaus-style forgetting policy — with the forgetting math verified runnable in this repo and the infrastructure-dependent fences compile-checked against their real APIs.

## Memory Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT MEMORY SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  Short-term  │◄──►│ Medium-term  │◄──►│ Long-term    │              │
│  │  (Context)   │    │ (Vector DB)  │    │ (Memoria)    │              │
│  │              │    │  (Qdrant)    │    │ (PostgreSQL) │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                   │                    │                      │
│         ▼                   ▼                    ▼                      │
│   ┌──────────┐        ┌──────────┐         ┌──────────┐                 │
│   │  Current │        │ Semantic │         │ Episodic │                 │
│   │ Session │        │  Memory  │         │  Memory  │                 │
│   │  (10K)  │        │ (10M)    │         │ (100M+)  │                 │
│   └──────────┘        └──────────┘         └──────────┘                 │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Memory Types Comparison

| Type | Duration | Size | Storage | Retrieval | Use Case |
|------|----------|------|---------|-----------|----------|
| **Short-term** | Session | ~10K tokens | In-memory | Exact | Current conversation |
| **Medium-term (Semantic)** | Days-Weeks | ~10M embeddings | Qdrant | Semantic search | Facts, concepts |
| **Long-term (Episodic)** | Months-Years | ~100M+ | PostgreSQL | Temporal + Semantic | Experiences, events |

## Implementation 1: VectorStore (Semantic Memory)

### Setup

```python
# vector_store.py
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from datetime import datetime
import hashlib

class VectorStore:
    """
    Semantic memory using Qdrant vector database
    Stores and retrieves memories by semantic similarity
    """

    def __init__(
        self,
        qdrant_url: str = "http://192.168.1.100:6333",
        collection: str = "agent_memory",
        embedder: str = "all-MiniLM-L6-v2"
    ):
        self.client = QdrantClient(url=qdrant_url)
        self.embedder = SentenceTransformer(embedder)
        self.collection = collection
        self._init_collection()

    def _init_collection(self):
        """Initialize Qdrant collection"""
        from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection not in collection_names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=384,
                    distance=Distance.COSINE,
                    hnsw_config=HnswConfigDiff(
                        m=32,
                        ef_construct=200,
                    )
                )
            )
            print(f"Created collection: {self.collection}")

        # Payload index for get_recent()'s order_by (ordered scroll requires
        # an indexed field; an unindexed order_by raises at query time).
        from qdrant_client.models import PayloadSchemaType
        self.client.create_payload_index(
            collection_name=self.collection,
            field_name="timestamp",
            field_schema=PayloadSchemaType.DATETIME,
        )

    def add_memory(
        self,
        content: str,
        metadata: dict | None = None,
        importance: float = 0.5
    ) -> str:
        """
        Add a memory to the store

        Args:
            content: Memory content
            metadata: Extra metadata (source, type, etc.)
            importance: 0.0-1.0 importance score

        Returns:
            Memory ID
        """
        # Generate ID
        memory_id = int(hashlib.md5(
            f"{content}_{datetime.now().isoformat()}".encode()
        ).hexdigest(), 16) % 10**8

        # Generate embedding
        embedding = self.embedder.encode(content).tolist()

        # Create payload
        payload = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "importance": importance,
            **(metadata or {})
        }

        # Store in Qdrant
        from qdrant_client.models import PointStruct
        self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(
                id=memory_id,
                vector=embedding,
                payload=payload
            )]
        )

        return str(memory_id)

    def add_conversation(
        self,
        user_message: str,
        agent_response: str,
        metadata: dict | None = None
    ) -> str:
        """Store a conversation turn as memory"""

        content = f"User: {user_message}\nAgent: {agent_response}"

        return self.add_memory(
            content=content,
            metadata={
                "type": "conversation",
                "user_message": user_message,
                "agent_response": agent_response,
                **(metadata or {})
            }
        )

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
        filters: dict | None = None
    ) -> list[dict]:
        """
        Retrieve relevant memories by semantic search

        Args:
            query: Search query
            limit: Max results
            score_threshold: Minimum similarity score
            filters: Extra metadata filters

        Returns:
            List of memories with scores
        """
        # Generate query embedding
        query_vector = self.embedder.encode(query).tolist()

        # Build filter
        search_filter = None
        if filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            conditions = [
                FieldCondition(
                    key=k,
                    match=MatchValue(value=v)
                )
                for k, v in filters.items()
            ]
            search_filter = Filter(must=conditions)

        # Search (qdrant-client >= 1.10: query_points replaces the
        # deprecated client.search(query_vector=...))
        response = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter,
        )

        # Format results
        memories = []
        for result in response.points:
            memories.append({
                "id": str(result.id),
                "content": result.payload.get("content"),
                "score": result.score,
                "metadata": {k: v for k, v in result.payload.items()
                            if k not in ["content", "timestamp"]},
                "timestamp": result.payload.get("timestamp")
            })

        return memories

    def get_recent(self, limit: int = 10) -> list[dict]:
        """Get most recent memories"""

        # Scroll through collection
        results, _ = self.client.scroll(
            collection_name=self.collection,
            limit=limit,
            order_by="timestamp",
            with_payload=True
        )

        return [
            {
                "id": str(r.id),
                "content": r.payload.get("content"),
                "timestamp": r.payload.get("timestamp")
            }
            for r in results
        ]

    def update_importance(self, memory_id: str, importance: float):
        """Update memory importance score"""

        self.client.set_payload(
            collection_name=self.collection,
            payload={"importance": importance},
            points=[int(memory_id)]
        )

    def delete_memory(self, memory_id: str):
        """Delete a memory"""

        self.client.delete(
            collection_name=self.collection,
            points=[int(memory_id)]
        )
```

VectorStore targets the current `qdrant-client` API (`query_points`, `delete(points=...)`, payload index backing the ordered scroll). Install with `uv pip install qdrant-client sentence-transformers`; the fence compile-checks against the real signatures but needs a live Qdrant to run.

### Usage Example

```python
# example_usage.py
from vector_store import VectorStore

# Initialize
memory = VectorStore()

# Add memories
memory.add_memory(
    "The user prefers Python over JavaScript for web development",
    metadata={"type": "preference", "category": "programming"},
    importance=0.8
)

memory.add_memory(
    "The project runs inference on an 11GB-class GPU",
    metadata={"type": "fact", "category": "infrastructure"},
    importance=0.9
)

# Store conversation
memory.add_conversation(
    user_message="What's your name?",
    agent_response="I'm an AI assistant for this project.",
    metadata={"session_id": "session_001"}
)

# Retrieve relevant memories
query = "What GPU does the project use?"
results = memory.retrieve(query, limit=3)

for r in results:
    print(f"[{r['score']:.3f}] {r['content']}")
    print(f"   Type: {r['metadata'].get('type')}")
    print()

# Get recent memories
recent = memory.get_recent(limit=5)
print("\nRecent memories:")
for r in recent:
    print(f"- {r['content'][:50]}...")
```

## Implementation 2: Memoria (Episodic Memory)

### Setup

```python
# memoria.py
import psycopg2
from datetime import datetime
import json

class Memoria:
    """
    Episodic memory using PostgreSQL
    Stores experiences with temporal and contextual information
    """

    def __init__(
        self,
        host: str = "192.168.1.100",
        port: int = 5432,
        database: str = "agent_memory",
        user: str = "postgres",
        password: str = "your_password"
    ):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        """Initialize database tables"""

        # Episodes table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id SERIAL PRIMARY KEY,
                agent_id VARCHAR(100),
                session_id VARCHAR(100),
                content TEXT,
                context JSONB,
                metadata JSONB,
                importance FLOAT DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Embeddings table (for semantic search)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_embeddings (
                episode_id INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
                embedding VECTOR(384),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (episode_id)
            );
        """)

        # Create indexes
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_agent
            ON episodes(agent_id);
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_session
            ON episodes(session_id);
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_created
            ON episodes(created_at DESC);
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_importance
            ON episodes(importance DESC);
        """)

        # Enable vector extension
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        self.conn.commit()
        print("Memoria database initialized")

    def store_episode(
        self,
        content: str,
        agent_id: str = "default",
        session_id: str | None = None,
        context: dict | None = None,
        metadata: dict | None = None,
        importance: float = 0.5
    ) -> int:
        """
        Store an episodic memory

        Args:
            content: Episode content
            agent_id: Agent identifier
            session_id: Session identifier
            context: Contextual information
            metadata: Additional metadata
            importance: 0.0-1.0 importance score

        Returns:
            Episode ID
        """

        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d')}"

        # Insert episode
        self.cursor.execute("""
            INSERT INTO episodes
            (agent_id, session_id, content, context, metadata, importance)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            agent_id,
            session_id,
            content,
            json.dumps(context or {}),
            json.dumps(metadata or {}),
            importance
        ))

        episode_id = self.cursor.fetchone()[0]
        self.conn.commit()

        return episode_id

    def store_episode_with_embedding(
        self,
        content: str,
        embedding: list[float],
        agent_id: str = "default",
        session_id: str | None = None,
        context: dict | None = None,
        metadata: dict | None = None,
        importance: float = 0.5
    ) -> int:
        """Store episode with embedding for semantic search"""

        # Store episode
        episode_id = self.store_episode(
            content=content,
            agent_id=agent_id,
            session_id=session_id,
            context=context,
            metadata=metadata,
            importance=importance
        )

        # Store embedding
        self.cursor.execute("""
            INSERT INTO episode_embeddings (episode_id, embedding)
            VALUES (%s, %s)
        """, (episode_id, str(embedding)))

        self.conn.commit()

        return episode_id

    def retrieve_by_time(
        self,
        agent_id: str = "default",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 10
    ) -> list[dict]:
        """Retrieve episodes by time range"""

        query = """
            SELECT id, content, context, metadata, importance, created_at
            FROM episodes
            WHERE agent_id = %s
        """
        params = [agent_id]

        if start_time:
            query += " AND created_at >= %s"
            params.append(start_time)

        if end_time:
            query += " AND created_at <= %s"
            params.append(end_time)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        self.cursor.execute(query, params)

        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1],
                "context": json.loads(row[2]) if row[2] else {},
                "metadata": json.loads(row[3]) if row[3] else {},
                "importance": row[4],
                "created_at": row[5].isoformat()
            })

        return results

    def retrieve_by_session(
        self,
        session_id: str,
        limit: int = 100
    ) -> list[dict]:
        """Retrieve all episodes from a session"""

        self.cursor.execute("""
            SELECT id, content, context, metadata, importance, created_at
            FROM episodes
            WHERE session_id = %s
            ORDER BY created_at ASC
            LIMIT %s
        """, (session_id, limit))

        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1],
                "context": json.loads(row[2]) if row[2] else {},
                "metadata": json.loads(row[3]) if row[3] else {},
                "importance": row[4],
                "created_at": row[5].isoformat()
            })

        return results

    def retrieve_similar(
        self,
        embedding: list[float],
        limit: int = 5,
        threshold: float = 0.7
    ) -> list[dict]:
        """Retrieve episodes by semantic similarity"""

        self.cursor.execute("""
            SELECT
                e.id, e.content, e.context, e.metadata,
                e.importance, e.created_at,
                1 - (ee.embedding <-> %s::vector) as similarity
            FROM episodes e
            JOIN episode_embeddings ee ON e.id = ee.episode_id
            WHERE 1 - (ee.embedding <-> %s::vector) > %s
            ORDER BY ee.embedding <-> %s::vector
            LIMIT %s
        """, (str(embedding), str(embedding), threshold, str(embedding), limit))

        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1],
                "context": json.loads(row[2]) if row[2] else {},
                "metadata": json.loads(row[3]) if row[3] else {},
                "importance": row[4],
                "created_at": row[5].isoformat(),
                "similarity": row[6]
            })

        return results

    def update_importance(self, episode_id: int, importance: float):
        """Update episode importance"""

        self.cursor.execute("""
            UPDATE episodes
            SET importance = %s
            WHERE id = %s
        """, (importance, episode_id))

        self.conn.commit()

    def record_access(self, episode_id: int):
        """Record episode access (for forgetting curve)"""

        self.cursor.execute("""
            UPDATE episodes
            SET access_count = access_count + 1,
                accessed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (episode_id,))

        self.conn.commit()

    def close(self):
        """Close database connection"""

        self.cursor.close()
        self.conn.close()
```

Memoria needs the pgvector extension (`CREATE EXTENSION vector` above) — plain `postgres:15` ships without it, so the Quick Start below uses the `pgvector/pgvector` image. Install the driver with `uv pip install psycopg2-binary`.

## Implementation 3: Unified Memory System

```python
# unified_memory.py
from vector_store import VectorStore
from memoria import Memoria
from sentence_transformers import SentenceTransformer

class AgentMemorySystem:
    """
    Unified memory system combining short-term, medium-term, and long-term memory
    """

    def __init__(self):
        self.semantic = VectorStore()  # Medium-term semantic memory
        self.episodic = Memoria()      # Long-term episodic memory
        self.short_term = []           # Current conversation context
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.max_context_turns = 10

    def add_conversation_turn(
        self,
        user_message: str,
        agent_response: str,
        session_id: str | None = None,
        importance: float = 0.5
    ):
        """Add a conversation turn to memory"""

        # Add to short-term
        self.short_term.append({
            "role": "user",
            "content": user_message
        })
        self.short_term.append({
            "role": "assistant",
            "content": agent_response
        })

        # Trim short-term
        if len(self.short_term) > self.max_context_turns * 2:
            self.short_term = self.short_term[-self.max_context_turns * 2:]

        # Add to semantic memory
        self.semantic.add_conversation(
            user_message=user_message,
            agent_response=agent_response,
            metadata={
                "type": "conversation",
                "session_id": session_id
            }
        )

        # Add to episodic memory
        embedding = self.embedder.encode(
            f"User: {user_message}\nAssistant: {agent_response}"
        ).tolist()

        self.episodic.store_episode_with_embedding(
            content=f"User: {user_message}\nAssistant: {agent_response}",
            embedding=embedding,
            session_id=session_id,
            metadata={"type": "conversation"},
            importance=importance
        )

    def retrieve_relevant(
        self,
        query: str,
        session_id: str | None = None,
        limit: int = 5
    ) -> dict:
        """
        Retrieve relevant memories from all systems

        Returns:
            Dictionary with short_term, semantic, and episodic memories
        """

        # Short-term (current conversation)
        short_term = {
            "context": self.short_term,
            "turns": len(self.short_term) // 2
        }

        # Semantic memory (Qdrant)
        semantic_results = self.semantic.retrieve(
            query=query,
            limit=limit
        )

        # Episodic memory (PostgreSQL)
        query_embedding = self.embedder.encode(query).tolist()
        episodic_results = self.episodic.retrieve_similar(
            embedding=query_embedding,
            limit=limit
        )

        return {
            "short_term": short_term,
            "semantic_memory": semantic_results,
            "episodic_memory": episodic_results
        }

    def get_context_string(self, query: str | None = None) -> str:
        """
        Get formatted context string for LLM prompt

        Args:
            query: The query to retrieve relevant memories

        Returns:
            Formatted context string
        """

        context_parts = []

        # Add relevant memories if query provided
        if query:
            memories = self.retrieve_relevant(query)

            if memories["semantic_memory"]:
                context_parts.append("## Relevant Past Conversations\n")
                for m in memories["semantic_memory"]:
                    context_parts.append(f"- {m['content']}\n")

            if memories["episodic_memory"]:
                context_parts.append("\n## Relevant Episodes\n")
                for m in memories["episodic_memory"]:
                    context_parts.append(
                        f"- [{m['similarity']:.2f}] {m['content']}\n"
                    )

        # Add short-term context
        if self.short_term:
            context_parts.append("\n## Current Conversation\n")
            for turn in self.short_term[-6:]:  # Last 3 turns
                role = turn["role"].capitalize()
                context_parts.append(f"{role}: {turn['content']}\n")

        return "\n".join(context_parts)

    def consolidate(self):
        """
        Consolidate short-term to long-term
        Should be called periodically
        """

        if not self.short_term:
            return

        # Combine short-term into episode
        conversation = "\n".join([
            f"{t['role']}: {t['content']}" for t in self.short_term
        ])

        embedding = self.embedder.encode(conversation).tolist()

        # Store in episodic
        self.episodic.store_episode_with_embedding(
            content=conversation,
            embedding=embedding,
            context={"source": "short_term_consolidation"},
            metadata={"type": "consolidated_conversation"}
        )

        # Clear short-term
        self.short_term = []

        print("Memory consolidated")

    def close(self):
        """Close connections"""
        self.episodic.close()
```

### Usage Example

```python
# agent_with_memory.py
from unified_memory import AgentMemorySystem
from openai import OpenAI

class MemoryEnabledAgent:
    """Agent with persistent memory"""

    def __init__(self, model: str = "Qwen/Qwen3-8B"):
        self.memory = AgentMemorySystem()
        self.client = OpenAI(
            base_url="http://192.168.1.100:8002/v1",
            api_key="dummy"
        )
        self.model = model

    def chat(self, user_message: str, session_id: str | None = None) -> str:
        """Chat with memory-enabled agent"""

        # Retrieve relevant memories
        relevant = self.memory.retrieve_relevant(
            query=user_message,
            session_id=session_id
        )

        # Build prompt with memory context
        context = self.memory.get_context_string(user_message)

        prompt = f"""You are a helpful AI assistant with persistent memory.

{context}

Current user message: {user_message}

Provide a helpful response based on the context above.
"""

        # Generate response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512
        )

        agent_response = response.choices[0].message.content

        # Store conversation in memory
        self.memory.add_conversation_turn(
            user_message=user_message,
            agent_response=agent_response,
            session_id=session_id,
            importance=0.6
        )

        return agent_response

# Usage
agent = MemoryEnabledAgent()

# First conversation
response1 = agent.chat("My name is Alice")
print(f"Agent: {response1}")

# Later conversation (remembers)
response2 = agent.chat("What's my name?")
print(f"Agent: {response2}")  # Should respond with "Alice"

# Consolidate memory
agent.memory.consolidate()
agent.memory.close()
```

## Memory Forgetting Strategy

```python
# memory_forgetting.py
from __future__ import annotations

import numpy as np
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from memoria import Memoria  # annotation-only; never imported at runtime

class MemoryForgetting:
    """
    Implement forgetting curve for memory management
    Memories decay over time based on access frequency
    """

    @staticmethod
    def calculate_importance(
        initial_importance: float,
        age_days: int,
        access_count: int,
        last_access_days: int
    ) -> float:
        """
        Calculate current importance using forgetting curve

        Ebbinghaus forgetting curve:
        R(t) = R0 * e^(-t/S)

        Where:
        - R(t) = retention at time t
        - R0 = initial retention (importance)
        - t = time since last access
        - S = stability (increases with repetitions)
        """

        # Stability increases with access count
        stability = 10 + (access_count * 5)  # Days

        # Decay since last access
        decay = np.exp(-last_access_days / stability)

        # Time decay (overall age)
        age_decay = np.exp(-age_days / (stability * 2))

        # Final importance
        current_importance = initial_importance * decay * age_decay

        # Boost from access count
        access_boost = min(access_count * 0.1, 0.5)

        return min(current_importance + access_boost, 1.0)

    @staticmethod
    def should_forget(
        importance: float,
        threshold: float = 0.1
    ) -> bool:
        """Determine if memory should be forgotten"""

        return importance < threshold

    @staticmethod
    def consolidate_episodic_memory(memoria: Memoria):
        """
        Consolidate episodic memory using forgetting curve

        Moves low-importance memories to archive or deletes them
        """

        # Get all episodes
        memoria.cursor.execute("""
            SELECT id, importance, created_at, access_count, accessed_at
            FROM episodes
        """)

        episodes = memoria.cursor.fetchall()

        for episode in episodes:
            episode_id, importance, created_at, access_count, accessed_at = episode

            # Calculate age
            age_days = (datetime.now() - created_at).days
            last_access_days = (datetime.now() - accessed_at).days

            # Calculate current importance
            current_importance = MemoryForgetting.calculate_importance(
                initial_importance=importance,
                age_days=age_days,
                access_count=access_count,
                last_access_days=last_access_days
            )

            # Update importance
            memoria.update_importance(episode_id, current_importance)

            # Archive or delete if below threshold
            if MemoryForgetting.should_forget(current_importance):
                print(f"Forgetting episode {episode_id} (importance: {current_importance:.3f})")
                # Could move to archive instead of delete
                # memoria.cursor.execute("DELETE FROM episodes WHERE id = %s", (episode_id,))

        memoria.conn.commit()


# --- runnable demo: the curve, applied to three memory profiles ---
for label, profile in [
    ("fresh, accessed 3x", dict(initial_importance=0.9, age_days=1,
                                access_count=3, last_access_days=1)),
    ("old, never accessed", dict(initial_importance=0.5, age_days=90,
                                 access_count=0, last_access_days=90)),
    ("aging, accessed 1x", dict(initial_importance=0.7, age_days=30,
                                access_count=1, last_access_days=20)),
]:
    imp = MemoryForgetting.calculate_importance(**profile)
    print(f"{label}: importance={imp:.3f}, forget={imp < 0.1}")
# Output: fresh, accessed 3x: importance=1.000, forget=False
# Output: old, never accessed: importance=0.000, forget=True
# Output: aging, accessed 1x: importance=0.168, forget=False
```

## Quick Start

```bash
# 0. Install dependencies (uv resolves and installs far faster than pip)
uv pip install qdrant-client sentence-transformers psycopg2-binary numpy

# 1. Start Qdrant
docker compose -f /srv/qdrant/docker-compose.yml up -d

# 2. Start PostgreSQL with pgvector (for Memoria)
docker run -d --name agent-memory-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=agent_memory \
  -p 5432:5432 \
  -v /srv/postgres:/var/lib/postgresql/data \
  pgvector/pgvector:pg15

# 3. Run the memory-enabled agent example
python agent_with_memory.py
```


---

## Summary

This guide builds persistent agent memory end to end: a VectorStore for semantic memory on Qdrant, an episodic store on PostgreSQL with pgvector, the unified three-tier system that routes a memory to the right tier, and an Ebbinghaus-style forgetting policy whose decay math is verified, not vibes. The rule it leaves: memory is a system with a write path, a read path, and a garbage collector - an agent that only ever remembers is an agent that eventually drowns in its own context.

## References

### Related Documents

- [7401: Long-term Memory for Agents](../7401-Long-term-Memory.md)
- [7403: Vector Memory and Embedding-Based Storage](../7403-Vector-Memory.md)
- [6101: HNSW Indexing - Efficient Semantic Search at Scale](../../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)
- [6403: Qdrant Production Deployment](../../../phase6-rag/6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md)
- [7101: ReAct (Reasoning + Acting) Loop System](../../7100-architecture/7101-ReAct-Loop-System.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**
