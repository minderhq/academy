---
Document ID: 7401
Title: Long-term Memory for Agents
Phase: 7
Module: 7400
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'memory', 'vector-store', 'long-term-memory', 'mem0', 'chromadb']
---

# 7401: Long-term Memory for Agents

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Memory Architectures
- Explain VectorStore Memory (LangChain)
- Explain Mem0: Production Memory System
- Explain ChromaDB Persistent Memory
- Explain Memory Hierarchies
- Configure and operate Implementation Examples

---

## Abstract

AI agents need persistent memory across sessions to maintain context, learn from experiences, and provide personalized interactions. This document covers implementing long-term memory systems using vector stores, Mem0, and ChromaDB for agent applications.

---

## Table of Contents

- [1. Memory Architectures](#1-memory-architectures)
- [2. VectorStore Memory (LangChain)](#2-vectorstore-memory-langchain)
- [3. Mem0: Production Memory System](#3-mem0-production-memory-system)
- [4. ChromaDB Persistent Memory](#4-chromadb-persistent-memory)
- [5. Memory Hierarchies](#5-memory-hierarchies)
- [6. Implementation Examples](#6-implementation-examples)
- [7. Best Practices](#7-best-practices)

---

## 1. Memory Architectures

### 1.1 Types of Memory

```text
┌─────────────────────────────────────────────────────────────┐
│                    AGENT MEMORY SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  EPISODIC MEMORY (Vector Store)                              │
│  ├─ Conversation history                                    │
│  ├─ User preferences                                        │
│  └─ Past interactions                                       │
│                                                               │
│  SEMANTIC MEMORY (Knowledge Graph)                           │
│  ├─ Facts extracted from conversations                      │
│  ├─ Entity relationships                                    │
│  └─ World knowledge                                         │
│                                                               │
│  PROCEDURAL MEMORY (Code/Tools)                              │
│  ├─ Learned skills                                          │
│  ├─ Tool usage patterns                                     │
│  └─ Workflow optimization                                   │
│                                                               │
│  WORKING MEMORY (Session Context)                            │
│  ├─ Current conversation state                              │
│  ├─ Short-term context window                               │
│  └─ Active reasoning chain                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Memory Requirements

| Requirement | Description | Implementation |
|-------------|-------------|-----------------|
| **Persistence** | Survive session restarts | Vector database on disk |
| **Retrieval** | Find relevant past info | Semantic search |
| **Scalability** | Handle millions of memories | HNSW indexing |
| **Consolidation** | Merge similar memories | Clustering + summarization |
| **Forgetting** | Remove obsolete info | TTL policies |

---

## 2. VectorStore Memory (LangChain)

### 2.1 Basic Implementation

```python
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import ConversationChain
from langchain.memory import VectorStoreMemory
from langchain.llms import OpenAI

# Initialize embeddings and vector store
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(
    texts=[
        "User prefers Python over JavaScript",
        "User is working on a RAG system",
        "User's project deadline is next week",
    ],
    embedding=embeddings
)

# Create retriever
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}  # Return top 3 memories
)

# Initialize memory
memory = VectorStoreMemory(
    memory_key="chat_history",
    retriever=retriever,
    return_docs=True  # Return retrieved documents
)

# Create conversation chain
llm = OpenAI(temperature=0)
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# Chat with memory
response = conversation.predict(
    input="What programming language do I prefer?"
)
# Output: "You prefer Python over JavaScript"
```

### 2.2 Persistent VectorStore

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import chromadb

# Persistent client (saves to disk)
client = chromadb.PersistentClient(path="./db/memory")

# Create persistent vector store
vectorstore = Chroma(
    client=client,
    collection_name="agent_memory",
    embedding_function=OpenAIEmbeddings()
)

# Add memories
vectorstore.add_texts(
    texts=[
        "User works at Example Corp",
        "User is building a chatbot",
    ],
    metadatas=[
        {"source": "user_info", "timestamp": "2024-01-15"},
        {"source": "project_info", "timestamp": "2024-01-15"}
    ]
)

# Retrieve relevant memories
results = vectorstore.similarity_search(
    query="Where does the user work?",
    k=1,
    filter={"source": "user_info"}  # Metadata filter
)
print(results[0].page_content)  # "User works at Example Corp"
```

### 2.3 Memory with Summarization

```python
from langchain.memory import VectorStoreMemory
from langchain.chains import ConversationalRetrievalChain

# Auto-summarize old memories
def summarize_old_memories(memories, max_age_hours=24):
    """Summarize memories older than threshold."""
    import datetime
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=max_age_hours)

    old_memories = [
        m for m in memories
        if datetime.datetime.fromisoformat(m.metadata["timestamp"]) < cutoff
    ]

    if len(old_memories) > 10:
        # Use LLM to summarize
        summary_prompt = f"Summarize these memories:\n" + "\n".join([m.page_content for m in old_memories])
        summary = llm.predict(summary_prompt)

        # Remove old, add summary
        vectorstore.delete([m.id for m in old_memories])
        vectorstore.add_texts(
            texts=[f"[SUMMARY] {summary}"],
            metadatas=[{"type": "summary", "memories_count": len(old_memories)}]
        )

# Use in conversation
memory = VectorStoreMemory(
    memory_key="chat_history",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    post_summarization_callback=summarize_old_memories
)
```

---

## 3. Mem0: Production Memory System

### 3.1 Installation and Setup

```bash
pip install mem0ai
# or
pip install "mem0ai[chroma]"  # With ChromaDB backend
```

### 3.2 Basic Mem0 Usage

```python
from mem0 import Memory

# Initialize with local storage
memory = Memory.from_config({
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "agent_memory",
            "path": "./db/chroma"
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text"
        }
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "mistral"
        }
    }
})

# Add memories
memory.add(
    "User prefers Python for data science projects",
    user_id="user_123",
    metadata={"category": "preference", "domain": "programming"}
)

memory.add(
    "User is working on RAG implementation with Qdrant",
    user_id="user_123",
    metadata={"category": "project", "tech": "qdrant"}
)

# Search memories
results = memory.search(
    query="What programming does the user like?",
    user_id="user_123",
    limit=3
)
for result in results:
    print(f"  {result['memory']}")
    # Output: "User prefers Python for data science projects"

# Get all memories for a user
all_memories = memory.get_all(user_id="user_123")
print(f"Total memories: {len(all_memories)}")

# Update memory
memory.update(
    memory_id="mem_456",
    new_memory="User prefers Python and Rust for systems programming"
)

# Delete memory
memory.delete(memory_id="mem_456")
```

### 3.3 Memory with Auto-Categorization

```python
from mem0 import Memory
import json

memory = Memory.from_config({
    "vector_store": {"provider": "chroma", "config": {"path": "./db/memory"}},
    "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text"}},
    "llm": {"provider": "ollama", "config": {"model": "mistral"}}
})

# Auto-categorize memories
def categorize_memory(text, llm):
    """Automatically categorize a memory."""
    categories = ["preference", "fact", "task", "goal", "relationship", "project"]

    prompt = f"""Categorize this memory into one of: {', '.join(categories)}

Memory: "{text}"

Respond with only the category name."""

    category = llm.generate(prompt).strip().lower()
    return category if category in categories else "general"

# Add memories with auto-categorization
memories_to_add = [
    "User's birthday is March 15th",
    "User wants to learn Kubernetes",
    "User dislikes coffee, prefers tea",
    "User is collaborating with Alice on ML project"
]

for mem in memories_to_add:
    category = categorize_memory(mem, memory.llm)
    memory.add(
        mem,
        user_id="user_123",
        metadata={"auto_category": category, "categorized_at": "2024-01-15"}
    )
    print(f"Added: {mem[:40]}... -> [{category}]")
```

### 3.4 Memory Consolidation

```python
def consolidate_similar_memories(user_id, threshold=0.85):
    """Merge similar memories to avoid redundancy."""
    from sklearn.cluster import AgglomerativeClustering
    import numpy as np

    # Get all memories
    memories = memory.get_all(user_id)

    if len(memories) < 2:
        return

    # Get embeddings
    texts = [m['memory'] for m in memories]
    embeddings = memory.embedder.embed(texts)

    # Cluster similar memories
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1 - threshold,
        metric='cosine'
    )

    labels = clustering.fit_predict(embeddings)

    # Process each cluster
    for cluster_id in set(labels):
        cluster_memories = [memories[i] for i in range(len(memories)) if labels[i] == cluster_id]

        if len(cluster_memories) > 1:
            # Merge cluster into single memory
            merged_text = " | ".join([m['memory'] for m in cluster_memories])

            # Delete old memories
            for mem in cluster_memories:
                memory.delete(mem['id'])

            # Add merged memory
            memory.add(
                merged_text,
                user_id=user_id,
                metadata={
                    "type": "consolidated",
                    "original_count": len(cluster_memories),
                    "consolidated_at": "2024-01-15"
                }
            )
            print(f"Consolidated {len(cluster_memories)} memories")

# Run consolidation periodically
consolidate_similar_memories("user_123", threshold=0.85)
```

---

## 4. ChromaDB Persistent Memory

### 4.1 Setup and Basic Operations

```python
import chromadb
from chromadb.config import Settings

# Persistent client (data survives restarts)
client = chromadb.PersistentClient(
    path="./db/chroma_memory",
    settings=Settings(anonymized_telemetry=False)
)

# Create collection
collection = client.get_or_create_collection(
    name="agent_memory",
    metadata={"description": "Long-term memory for AI agent"}
)

# Add memories with embeddings
collection.add(
    documents=[
        "User prefers dark mode in all applications",
        "User is allergic to peanuts",
        "User's favorite color is blue",
    ],
    metadatas=[
        {"category": "preference", "type": "ui"},
        {"category": "health", "type": "allergy"},
        {"category": "preference", "type": "color"},
    ],
    ids=["mem_1", "mem_2", "mem_3"]
)

# Query memories
results = collection.query(
    query_texts=["What are the user's preferences?"],
    n_results=5,
    where={"category": "preference"}  # Filter by metadata
)

print("Relevant memories:")
for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"  {i+1}. {doc}")
    print(f"     Category: {metadata['category']}")
```

### 4.2 Advanced ChromaDB Features

```python
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./db/chroma")
collection = client.get_or_create_collection("agent_memory")

# Use custom embedder
class CustomEmbedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input_text):
        return self.model.encode(input_text).tolist()

embedder = CustomEmbedder()

# Hybrid search (vector + keyword)
collection.add(
    documents=["User likes hiking and camping"],
    metadatas=[{"activity": "outdoor", "interests": "hiking,camping"}],
    ids=["mem_4"]
)

# Metadata-only query
results = collection.query(
    query_texts=["outdoor"],
    n_results=10,
    where={"activity": "outdoor"}
)

# Update memory
collection.update(
    ids=["mem_1"],
    documents=["User strongly prefers dark mode in all applications"],
    metadatas=[{"category": "preference", "type": "ui", "priority": "high"}]
)

# Delete old memories
old_memories = collection.get(
    where={"timestamp": {"$lt": "2024-01-01"}}
)
if old_memories['ids']:
    collection.delete(ids=old_memories['ids'])
```

### 4.3 Memory with Time-Based Decay

```python
from datetime import datetime, timedelta
import chromadb

def add_memory_with_decay(collection, text, metadata, ttl_days=365):
    """Add memory with automatic expiration."""
    expiry_date = (datetime.now() + timedelta(days=ttl_days)).isoformat()

    metadata['created_at'] = datetime.now().isoformat()
    metadata['expires_at'] = expiry_date

    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[f"mem_{datetime.now().timestamp()}"]
    )

def cleanup_expired_memories(collection):
    """Remove expired memories."""
    now = datetime.now().isoformat()

    # Get expired memories
    all_memories = collection.get()
    expired_ids = [
        mem_id for mem_id, expires_at in zip(all_memories['ids'], all_memories['metadatas'])
        if expires_at.get('expires_at', '9999-12-31') < now
    ]

    if expired_ids:
        collection.delete(ids=expired_ids)
        print(f"Cleaned up {len(expired_ids)} expired memories")

# Usage
add_memory_with_decay(
    collection,
    "User prefers tea over coffee",
    {"category": "preference", "type": "beverage"},
    ttl_days=180  # Expires in 6 months
)

# Run cleanup periodically
cleanup_expired_memories(collection)
```

---

## 5. Memory Hierarchies

### 5.1 Multi-Tier Memory Architecture

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
import chromadb

@dataclass
class MemoryItem:
    """A single memory with importance score."""
    content: str
    metadata: Dict
    importance: float  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: str = None

class HierarchicalMemory:
    """Multi-tier memory system with hot/warm/cold storage."""

    def __init__(self):
        # Hot memory: Frequently accessed (in-memory)
        self.hot_memory: Dict[str, MemoryItem] = {}
        self.hot_capacity = 100

        # Warm memory: Occasionally accessed (ChromaDB)
        self.warm_client = chromadb.PersistentClient(path="./db/warm")
        self.warm_collection = self.warm_client.get_or_create_collection("warm_memory")

        # Cold memory: Rarely accessed (archived)
        self.cold_client = chromadb.PersistentClient(path="./db/cold")
        self.cold_collection = self.cold_client.get_or_create_collection("cold_memory")

    def add(self, content: str, metadata: Dict, importance: float = 0.5):
        """Add memory with automatic tier placement."""
        memory_id = f"mem_{datetime.now().timestamp()}"

        memory = MemoryItem(
            content=content,
            metadata=metadata,
            importance=importance,
            last_accessed=datetime.now().isoformat()
        )

        # Place in appropriate tier
        if importance > 0.7 or len(self.hot_memory) < self.hot_capacity:
            self.hot_memory[memory_id] = memory
        elif importance > 0.3:
            self.warm_collection.add(
                documents=[content],
                metadatas=[{**metadata, "memory_id": memory_id}],
                ids=[memory_id]
            )
        else:
            self.cold_collection.add(
                documents=[content],
                metadatas=[{**metadata, "memory_id": memory_id}],
                ids=[memory_id]
            )

    def get(self, query: str, top_k: int = 10) -> List[MemoryItem]:
        """Retrieve memories from all tiers."""
        results = []

        # Search hot memory (exact matching for simplicity)
        query_lower = query.lower()
        for mem_id, memory in self.hot_memory.items():
            if query_lower in memory.content.lower():
                memory.access_count += 1
                memory.last_accessed = datetime.now().isoformat()
                results.append(memory)

        # Search warm memory
        warm_results = self.warm_collection.query(
            query_texts=[query],
            n_results=top_k
        )
        for doc, metadata in zip(warm_results['documents'][0], warm_results['metadatas'][0]):
            results.append(MemoryItem(
                content=doc,
                metadata=metadata,
                importance=metadata.get('importance', 0.5),
                access_count=metadata.get('access_count', 0) + 1,
                last_accessed=datetime.now().isoformat()
            ))

        # Search cold memory only if needed
        if len(results) < top_k:
            cold_results = self.cold_collection.query(
                query_texts=[query],
                n_results=top_k - len(results)
            )
            for doc, metadata in zip(cold_results['documents'][0], cold_results['metadatas'][0]):
                results.append(MemoryItem(
                    content=doc,
                    metadata=metadata,
                    importance=metadata.get('importance', 0.5),
                    access_count=1,
                    last_accessed=datetime.now().isoformat()
                ))

        # Sort by importance and access count
        results.sort(key=lambda m: (m.importance, m.access_count), reverse=True)
        return results[:top_k]

    def promote_demote(self):
        """Move memories between tiers based on access patterns."""
        # Promote frequently accessed warm memories to hot
        warm_all = self.warm_collection.get()
        for mem_id, metadata in zip(warm_all['ids'], warm_all['metadatas']):
            access_count = metadata.get('access_count', 0)
            if access_count > 10 and len(self.hot_memory) < self.hot_capacity:
                # Move to hot
                doc = self.warm_collection.get(ids=[mem_id])
                self.hot_memory[mem_id] = MemoryItem(
                    content=doc['documents'][0],
                    metadata=metadata,
                    importance=metadata.get('importance', 0.5),
                    access_count=access_count
                )
                self.warm_collection.delete(ids=[mem_id])

        # Demote infrequently accessed hot memories to warm
        for mem_id, memory in list(self.hot_memory.items()):
            if memory.access_count < 2 and memory.importance < 0.5:
                # Move to warm
                self.warm_collection.add(
                    documents=[memory.content],
                    metadatas=[{
                        **memory.metadata,
                        "memory_id": mem_id,
                        "access_count": memory.access_count
                    }],
                    ids=[mem_id]
                )
                del self.hot_memory[mem_id]
```

### 5.2 Memory Importance Scoring

```python
def calculate_importance(memory: MemoryItem) -> float:
    """Calculate memory importance score (0.0 to 1.0)."""
    score = 0.5  # Base score

    # Factor 1: Access frequency
    if memory.access_count > 10:
        score += 0.2
    elif memory.access_count > 5:
        score += 0.1

    # Factor 2: Recency
    days_since_access = (datetime.now() - datetime.fromisoformat(memory.last_accessed)).days
    if days_since_access < 7:
        score += 0.15
    elif days_since_access < 30:
        score += 0.05

    # Factor 3: Category importance
    important_categories = ["preference", "identity", "goal"]
    if any(cat in memory.metadata.get("tags", []) for cat in important_categories):
        score += 0.15

    # Factor 4: Content length (longer = more detailed)
    if len(memory.content) > 200:
        score += 0.05

    return min(score, 1.0)

# Auto-tag important memories
def auto_tag_memory(content: str, llm) -> List[str]:
    """Automatically tag memory with categories."""
    prompt = f"""Tag this memory with relevant categories.
Choose from: preference, identity, goal, task, fact, relationship, project

Memory: "{content}"

Return tags as comma-separated values."""

    response = llm.generate(prompt).strip()
    return [tag.strip() for tag in response.split(",")]
```

---

## 6. Implementation Examples

### 6.1 Complete Agent with Memory

```python
from mem0 import Memory
from openai import OpenAI
import json

class MemoryEnabledAgent:
    """AI agent with persistent long-term memory."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm = OpenAI()

        # Initialize memory
        self.memory = Memory.from_config({
            "vector_store": {"provider": "chroma", "config": {"path": f"./db/{user_id}"}},
            "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text"}},
            "llm": {"provider": "ollama", "config": {"model": "mistral"}}
        })

        # Session context (short-term memory)
        self.session_history = []

    def chat(self, user_message: str) -> str:
        """Process user message with memory."""
        # 1. Search relevant memories
        relevant_memories = self.memory.search(
            query=user_message,
            user_id=self.user_id,
            limit=5
        )

        # 2. Build context
        memory_context = "\n".join([
            f"- {m['memory']}" for m in relevant_memories
        ])

        # 3. Add to prompt
        system_prompt = f"""You are a helpful AI assistant with access to the user's past interactions.

RELEVANT MEMORIES:
{memory_context if memory_context else "No relevant memories found."}

Use these memories to provide personalized responses."""

        # 4. Generate response
        messages = [
            {"role": "system", "content": system_prompt},
            *self.session_history,
            {"role": "user", "content": user_message}
        ]

        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=messages
        )

        assistant_message = response.choices[0].message.content

        # 5. Update session history
        self.session_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ])

        # Keep session history manageable
        if len(self.session_history) > 20:
            self.session_history = self.session_history[-20:]

        # 6. Extract and store new memories
        self._extract_and_store_memories(user_message, assistant_message)

        return assistant_message

    def _extract_and_store_memories(self, user_msg: str, assistant_msg: str):
        """Extract important information from conversation."""
        extraction_prompt = f"""Extract important information to remember from this conversation.

User: {user_msg}
Assistant: {assistant_msg}

Extract information worth remembering (preferences, facts, goals, etc.).
Format as JSON list: {{"memories": ["memory 1", "memory 2"]}}"""

        try:
            response = self.llm.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": extraction_prompt}],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            for mem in result.get("memories", []):
                self.memory.add(
                    mem,
                    user_id=self.user_id,
                    metadata={"extracted_at": datetime.now().isoformat()}
                )
                print(f"Stored new memory: {mem[:50]}...")

        except Exception as e:
            print(f"Memory extraction failed: {e}")

# Usage
agent = MemoryEnabledAgent(user_id="user_123")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    response = agent.chat(user_input)
    print(f"Agent: {response}")
```

### 6.2 Memory for RAG Agents

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

class RAGAgentWithMemory:
    """RAG agent that remembers past queries and answers."""

    def __init__(self, knowledge_base_path: str):
        # Knowledge base vector store
        self.kb_store = Chroma(
            persist_directory=knowledge_base_path,
            embedding_function=OpenAIEmbeddings()
        )

        # Conversation memory
        self.memory_store = Chroma(
            persist_directory="./db/conversation_memory",
            embedding_function=OpenAIEmbeddings(),
            collection_name="conversation_history"
        )

        self.llm = OpenAI(temperature=0)

    def query(self, question: str) -> dict:
        """Query with memory-aware retrieval."""
        # 1. Retrieve relevant conversation history
        past_interactions = self.memory_store.similarity_search(
            question,
            k=3,
            filter={"interaction_type": "Q&A"}
        )

        # 2. Retrieve relevant knowledge
        knowledge_docs = self.kb_store.similarity_search(question, k=5)

        # 3. Build enriched context
        context_parts = ["RELEVANT PAST INTERACTIONS:"]
        for doc in past_interactions:
            context_parts.append(f"- {doc.page_content}")

        context_parts.append("\nKNOWLEDGE BASE:")
        for doc in knowledge_docs:
            context_parts.append(f"- {doc.page_content}")

        # 4. Generate answer
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.kb_store.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )

        result = qa_chain({"query": question})

        # 5. Store Q&A in memory
        self.memory_store.add_texts(
            texts=[
                f"Q: {question}\nA: {result['result']}"
            ],
            metadatas=[{
                "interaction_type": "Q&A",
                "timestamp": datetime.now().isoformat(),
                "sources": [doc.metadata.get("source", "unknown") for doc in result.get("source_documents", [])]
            }]
        )

        return {
            "answer": result["result"],
            "sources": [doc.metadata.get("source", "unknown") for doc in result.get("source_documents", [])],
            "past_context": [doc.page_content for doc in past_interactions]
        }
```

---

## 7. Best Practices

### 7.1 Memory Management

| Practice | Description | Implementation |
|----------|-------------|-----------------|
| **Regular consolidation** | Merge similar memories | Run clustering weekly |
| **TTL policies** | Auto-expire old memories | Set expires_at metadata |
| **Importance scoring** | Prioritize valuable memories | Track access frequency |
| **Deduplication** | Remove duplicate memories | Check similarity before adding |
| **Privacy** | Sensitive data handling | Encrypt at rest, access controls |

### 7.2 Performance Optimization

```python
# Batch memory operations for efficiency
def batch_add_memories(memory: Memory, texts: List[str], batch_size: int = 100):
    """Add memories in batches for better performance."""
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        memory.add(
            batch,
            user_id="user_123",
            metadata={"batch_id": i // batch_size}
        )
        print(f"Added batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

# Async memory operations
import asyncio
from mem0 import AsyncMemory

async def async_memory_operations():
    memory = AsyncMemory.from_config({...})

    # Concurrent operations
    await asyncio.gather(
        memory.add("Memory 1", user_id="user_123"),
        memory.add("Memory 2", user_id="user_123"),
        memory.add("Memory 3", user_id="user_123"),
    )

    results = await memory.search("preferences", user_id="user_123")
    return results
```

### 7.3 Memory Evaluation

```python
def evaluate_memory_quality(memory: Memory, test_queries: List[dict]) -> dict:
    """Evaluate memory retrieval quality."""
    metrics = {"precision": [], "recall": [], "mrr": []}

    for query in test_queries:
        results = memory.search(
            query["question"],
            user_id=query["user_id"],
            limit=10
        )

        retrieved_ids = [r.get("id") for r in results]
        relevant_ids = query["relevant_memory_ids"]

        # Precision
        precision = len(set(retrieved_ids) & set(relevant_ids)) / len(retrieved_ids)
        metrics["precision"].append(precision)

        # Recall
        recall = len(set(retrieved_ids) & set(relevant_ids)) / len(relevant_ids)
        metrics["recall"].append(recall)

        # Mean Reciprocal Rank
        for i, mem_id in enumerate(retrieved_ids):
            if mem_id in relevant_ids:
                metrics["mrr"].append(1 / (i + 1))
                break
        else:
            metrics["mrr"].append(0)

    return {
        "avg_precision": sum(metrics["precision"]) / len(metrics["precision"]),
        "avg_recall": sum(metrics["recall"]) / len(metrics["recall"]),
        "avg_mrr": sum(metrics["mrr"]) / len(metrics["mrr"])
    }

# Test queries
test_data = [
    {
        "question": "What programming does the user prefer?",
        "user_id": "user_123",
        "relevant_memory_ids": ["mem_1", "mem_5"]
    },
    # ... more test queries
]

# Evaluate
quality_scores = evaluate_memory_quality(memory, test_data)
print(f"Memory Quality: {quality_scores}")
```

---

## Summary

Long-term memory systems enable AI agents to:

1. **Maintain context** across sessions and conversations
2. **Personalize interactions** based on user history
3. **Learn from experience** to improve over time
4. **Provide continuity** in ongoing relationships

**Key Technologies:**
- **VectorStore** (LangChain) - Basic memory with vector search
- **Mem0** - Production memory system with auto-categorization
- **ChromaDB** - Persistent storage with advanced filtering

**Implementation Considerations:**
- Use hierarchical memory (hot/warm/cold) for scalability
- Implement consolidation to avoid redundancy
- Set TTL policies for automatic cleanup
- Track importance scores for prioritization

---

## References

### Related ai-engineering-curriculum Documents

- [7403: Vector Memory and Embedding-Based Storage](7403-Vector-Memory.md)

---

## Next Steps

- Continue with: **[7501-Prompt-Injection-Defense.md](./../7500-security/7501-Prompt-Injection-Defense.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Practice: **[assessment/PRACTICE.md](./assessment/PRACTICE.md)**

---

**Related:**
- [6101: HNSW](../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)
- [7101: ReAct](../7100-architecture/7101-ReAct-Loop-System.md)
- [6201: Hybrid Search](../../phase6-rag/6200-retrieval/6201-Hybrid-Search.md)
