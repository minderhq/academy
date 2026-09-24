# 7400: Agent Memory Systems - Practice

## Exercises

### Exercise 1: Implement Short-Term Memory

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Message:
    role: str
    content: str
    timestamp: float

class ShortTermMemory:
    def __init__(self, max_messages=20):
        self.messages: List[Message] = []
        self.max_messages = max_messages

    def add_message(self, role: str, content: str):
        """
        Add a message to memory with automatic pruning.

        SOLUTION: Implements FIFO eviction when max_messages is exceeded.
        This ensures memory stays bounded while preserving recent context.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        import time
        message = Message(
            role=role,
            content=content,
            timestamp=time.time()
        )
        self.messages.append(message)

        # SOLUTION: Prune old messages if over limit
        if len(self.messages) > self.max_messages:
            # Remove oldest messages to maintain limit
            num_to_remove = len(self.messages) - self.max_messages
            self.messages = self.messages[num_to_remove:]

    def get_recent(self, n=5) -> List[Message]:
        """Get n most recent messages."""
        return self.messages[-n:]

    def get_conversation_history(self) -> str:
        """Get formatted conversation history."""
        history = []
        for msg in self.messages:
            history.append(f"{msg.role}: {msg.content}")
        return "\n".join(history)

    def search(self, keyword: str) -> List[Message]:
        """Search messages by keyword."""
        return [
            msg for msg in self.messages
            if keyword.lower() in msg.content.lower()
        ]

# SOLUTION: Use short-term memory with comprehensive example
import time

def test_short_term_memory():
    """
    Demonstrate short-term memory functionality with comprehensive testing.

    Expected Output:
        user: Hi, I'm Alice
        assistant: Hello Alice! How can I help?
        user: What's my name?
    """
    memory = ShortTermMemory(max_messages=20)

    # Add conversation
    memory.add_message("user", "Hi, I'm Alice")
    memory.add_message("assistant", "Hello Alice! How can I help?")
    memory.add_message("user", "What's my name?")

    # Retrieve context
    recent = memory.get_recent(3)
    print("Recent messages:")
    for msg in recent:
        print(f"{msg.role}: {msg.content}")

    # Test search functionality
    print("\nSearch results for 'Alice':")
    alice_msgs = memory.search("Alice")
    for msg in alice_msgs:
        print(f"  Found: {msg.role}: {msg.content[:50]}...")

    # Test conversation history
    print("\nFull conversation history:")
    print(memory.get_conversation_history())

    # Test pruning
    print(f"\nTotal messages: {len(memory.messages)}")
    print(f"Max messages: {memory.max_messages}")

# Run the test
test_short_term_memory()
```

### Exercise 2: Implement Long-Term Memory (Vector Store)

```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class LongTermMemory:
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(embedding_model)
        self.index = None
        self.documents = []
        self.metadata = []

    def add_memory(self, content: str, metadata: dict = None):
        """
        Add a memory to long-term storage with embedding and indexing.

        SOLUTION: Creates vector embeddings and maintains FAISS index for
        efficient semantic search. Handles index initialization and updates.

        Args:
            content: Memory content to store
            metadata: Optional metadata dictionary for context

        Example:
            >>> ltm = LongTermMemory()
            >>> ltm.add_memory("Alice loves hiking", {"user": "Alice"})
        """
        # SOLUTION: Create embedding using sentence transformer
        embedding = self.embedder.encode([content])[0]

        # SOLUTION: Store document and metadata
        self.documents.append(content)
        self.metadata.append(metadata or {})

        # SOLUTION: Build/update FAISS index
        if self.index is None:
            # Initialize index with correct dimension
            self.index = faiss.IndexFlatL2(embedding.shape[0])
            self.index.add(embedding.reshape(1, -1))
        else:
            # Add to existing index
            self.index.add(embedding.reshape(1, -1))

    def retrieve(self, query: str, top_k=5) -> List[Dict]:
        """
        Retrieve relevant memories using semantic search.

        SOLUTION: Embeds query and searches FAISS index for similar memories.
        Returns ranked results with distance scores and metadata.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of retrieved memories with relevance scores

        Example:
            >>> results = ltm.retrieve("What does Alice like?")
            >>> print(results[0]['content'])
            "Alice loves hiking and mountain climbing"
        """
        if self.index is None or len(self.documents) == 0:
            return []

        # SOLUTION: Create query embedding
        query_embedding = self.embedder.encode([query])[0]

        # SOLUTION: Search FAISS index for nearest neighbors
        k = min(top_k, len(self.documents))
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1),
            k
        )

        # SOLUTION: Format results with full context
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents) and idx >= 0:  # Valid index
                results.append({
                    "content": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "distance": float(dist),
                    "similarity": 1.0 / (1.0 + float(dist)),  # Convert to similarity
                })

        return results

    def search_metadata(self, key: str, value: any) -> List[Dict]:
        """Search memories by metadata."""
        results = []
        for i, meta in enumerate(self.metadata):
            if meta.get(key) == value:
                results.append({
                    "content": self.documents[i],
                    "metadata": meta,
                })
        return results

# SOLUTION: Use long-term memory with comprehensive testing
def test_long_term_memory():
    """
    Demonstrate long-term memory with vector embeddings.

    Expected Output:
        [0.123] Alice loves hiking and mountain climbing
        [0.456] Alice works as a software engineer
        [0.789] Bob enjoys playing guitar

    Note: Actual distances will vary based on embedding model.
    Lower distance = higher similarity.
    """
    print("Initializing Long-Term Memory...")
    ltm = LongTermMemory()

    # Add memories with metadata
    print("\nAdding memories to long-term storage...")
    ltm.add_memory(
        "Alice loves hiking and mountain climbing",
        {"user": "Alice", "topic": "hobbies", "timestamp": "2024-02-05"}
    )

    ltm.add_memory(
        "Alice works as a software engineer at Google",
        {"user": "Alice", "topic": "work", "timestamp": "2024-02-05"}
    )

    ltm.add_memory(
        "Bob enjoys playing guitar and piano",
        {"user": "Bob", "topic": "hobbies", "timestamp": "2024-02-05"}
    )

    ltm.add_memory(
        "Bob is a music teacher",
        {"user": "Bob", "topic": "work", "timestamp": "2024-02-05"}
    )

    # Semantic search
    print("\n--- Semantic Search ---")
    query = "What does Alice like to do?"
    print(f"Query: {query}\n")

    results = ltm.retrieve(query, top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. [Distance: {result['distance']:.3f}] {result['content']}")
        print(f"   Similarity: {result['similarity']:.3f}")
        print(f"   Metadata: {result['metadata']}\n")

    # Metadata search
    print("--- Metadata Search ---")
    alice_memories = ltm.search_metadata("user", "Alice")
    print(f"Found {len(alice_memories)} memories for Alice:")
    for mem in alice_memories:
        print(f"  - {mem['content']}")

    print(f"\nTotal memories stored: {len(ltm.documents)}")

# Run the test
test_long_term_memory()
```

### Exercise 3: Implement Entity Memory

```python
from typing import Dict, List
import re

class EntityMemory:
    def __init__(self):
        self.entities: Dict[str, Dict] = {}

    def extract_entities(self, text: str) -> List[tuple]:
        """Extract entities and their properties from text."""

        # Simplified entity extraction
        # In production, use NER model

        entities = []

        # Pattern: "X is/has/likes [something]"
        patterns = [
            r"(\w+) is (?:a|an) (\w+(?: \w+)?)",
            r"(\w+) has (.+?)(?:\.|$)",
            r"(\w+) likes (.+?)(?:\.|$)",
            r"(\w+)'s (.+?) is (.+?)(?:\.|$)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = match.group(1).capitalize()
                property_value = match.group(2) if len(match.groups()) > 1 else None

                if len(match.groups()) > 2:
                    property_key = match.group(2)
                    property_value = match.group(3)

                    entities.append((entity, property_key, property_value))
                else:
                    entities.append((entity, "description", property_value))

        return entities

    def update(self, text: str):
        """Update entity memory from text."""

        entities = self.extract_entities(text)

        for entity in entities:
            name = entity[0]
            prop = entity[1]
            value = entity[2]

            if name not in self.entities:
                self.entities[name] = {
                    "name": name,
                    "facts": [],
                }

            self.entities[name]["facts"].append({
                "property": prop,
                "value": value,
            })

    def get_entity(self, name: str) -> Dict:
        """Get all information about an entity."""
        return self.entities.get(name.capitalize(), {})

    def search_entities(self, keyword: str) -> List[Dict]:
        """Search for entities matching keyword."""
        results = []
        for name, data in self.entities.items():
            if keyword.lower() in name.lower():
                results.append(data)
        return results

# SOLUTION: Use entity memory with comprehensive testing
def test_entity_memory():
    """
    Demonstrate entity extraction and memory.

    Expected Output:
        Alice: {'name': 'Alice', 'facts': [...]}
        Found entities: ['Alice', 'Bob']
    """
    print("=== Entity Memory Test ===\n")

    entity_memory = EntityMemory()

    # Update with entity information
    print("Extracting entities from text...")
    entity_memory.update("Alice is a software engineer who loves hiking.")
    entity_memory.update("Alice's favorite color is blue.")
    entity_memory.update("Bob is a teacher who enjoys playing guitar.")
    entity_memory.update("Charlie works as a doctor in New York.")

    # Get entity info
    print("\n--- Entity Information ---")
    alice_info = entity_memory.get_entity("Alice")
    print(f"Alice: {alice_info}")

    bob_info = entity_memory.get_entity("Bob")
    print(f"Bob: {bob_info}")

    # Search entities
    print("\n--- Entity Search ---")
    results = entity_memory.search_entities("a")
    print(f"Entities matching 'a': {[e['name'] for e in results]}")

    # Show all entities
    print(f"\nTotal entities tracked: {len(entity_memory.entities)}")
    print(f"Entity names: {list(entity_memory.entities.keys())}")

# Run the test
test_entity_memory()
```

### Exercise 4: Implement Summary Memory

```python
class SummaryMemory:
    def __init__(self, max_tokens=500):
        self.max_tokens = max_tokens
        self.full_history = []
        self.summary = ""
        self.llm = ChatOpenAI(model="gpt-4")

    def add_message(self, role: str, content: str):
        """
        Add a message and trigger summarization if token limit exceeded.

        SOLUTION: Monitors token count and automatically summarizes
        conversation when approaching the limit to maintain context
        while staying within bounds.
        """
        self.full_history.append({"role": role, "content": content})

        # SOLUTION: Check if summarization needed
        current_tokens = len(self.summary.split()) + sum(
            len(msg["content"].split()) for msg in self.full_history
        )

        if current_tokens > self.max_tokens:
            self._summarize()

    def _summarize(self):
        """
        Summarize conversation history using LLM.

        SOLUTION: Builds comprehensive prompt with previous summary and
        new messages, then generates condensed summary while preserving
        key information.
        """
        # SOLUTION: Build summarization prompt with context
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.full_history
        ])

        prompt = f"""Summarize this conversation, keeping key information:

Previous summary:
{self.summary}

New messages:
{history_text}

Updated summary:"""

        # SOLUTION: Generate new summary using LLM
        response = self.llm.invoke(prompt)
        self.summary = response.content

        # Keep only recent messages for context
        self.full_history = self.full_history[-3:]

    def get_context(self) -> str:
        """Get context with summary and recent messages."""

        recent_messages = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.full_history
        ])

        context = f"""Summary of conversation:
{self.summary}

Recent messages:
{recent_messages}"""

        return context

# SOLUTION: Use summary memory with demonstration
def test_summary_memory():
    """
    Demonstrate automatic conversation summarization.

    Expected Output:
        Summary of conversation:
        The user Alice introduced herself as a software engineer...
        Recent messages:
        user: What do you know about me?

    Note: The summary will be generated by the LLM.
    """
    print("=== Summary Memory Test ===\n")

    summary_memory = SummaryMemory(max_tokens=200)

    print("Adding messages to conversation...")
    summary_memory.add_message("user", "Hi, I'm Alice and I'm a software engineer")
    summary_memory.add_message("assistant", "Nice to meet you Alice!")
    summary_memory.add_message("user", "I work at Google and I love hiking")
    summary_memory.add_message("assistant", "That's great!")

    print("\nTriggering summarization...")
    # Trigger summarization by adding more messages
    summary_memory.add_message("user", "I also enjoy playing tennis on weekends")
    summary_memory.add_message("assistant", "You have many hobbies!")

    # This should trigger summarization
    summary_memory.add_message("user", "What do you know about me?")

    print("\n--- Current Context ---")
    context = summary_memory.get_context()
    print(context)

    print(f"\nSummary length: {len(summary_memory.summary)} words")
    print(f"Recent messages: {len(summary_memory.full_history)}")

# Run the test
test_summary_memory()
```

### Exercise 5: Hybrid Memory System

```python
class HybridMemory:
    def __init__(self):
        self.short_term = ShortTermMemory(max_messages=10)
        self.long_term = LongTermMemory()
        self.entity_memory = EntityMemory()
        self.summary_memory = SummaryMemory(max_tokens=300)

    def add(self, role: str, content: str, metadata: dict = None):
        """
        Add to all memory systems with intelligent routing.

        SOLUTION: Distributes content across all memory systems based on
        importance and relevance. Short-term gets everything, long-term
        gets important content, entities are extracted, and summary is updated.
        """
        # SOLUTION: Add to short-term (always)
        self.short_term.add_message(role, content)

        # SOLUTION: Add to long-term if important
        if self._is_important(content):
            self.long_term.add_memory(content, metadata)

        # SOLUTION: Extract entities from user messages
        if role == "user":
            self.entity_memory.update(content)

        # SOLUTION: Update summary memory
        self.summary_memory.add_message(role, content)

    def _is_important(self, text: str) -> bool:
        """Determine if text is important enough for long-term storage."""

        important_keywords = [
            "important", "remember", "don't forget",
            "my name", "i work", "i live", "favorite"
        ]

        return any(
            keyword in text.lower()
            for keyword in important_keywords
        )

    def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context from all memory systems.

        SOLUTION: Aggregates context from summary, recent messages,
        long-term semantic search, and entity information to provide
        comprehensive context for query answering.

        Args:
            query: Query to retrieve context for

        Returns:
            Aggregated context string
        """
        context_parts = []

        # # SOLUTION: Include summary in context
        if self.summary_memory.summary:
            context_parts.append(f"Summary: {self.summary_memory.summary}")

        # # SOLUTION: Include recent messages
        recent = self.short_term.get_recent(3)
        if recent:
            recent_text = "\n".join([f"{m.role}: {m.content}" for m in recent])
            context_parts.append(f"Recent messages:\n{recent_text}")

        # # SOLUTION: Retrieve from long-term memory
        ltm_results = self.long_term.retrieve(query, top_k=2)
        if ltm_results:
            ltm_text = "\n".join([r["content"] for r in ltm_results])
            context_parts.append(f"Relevant memories:\n{ltm_text}")

        # # SOLUTION: Include entity information
        entities = self.entity_memory.extract_entities(query)
        if entities:
            entity_info = []
            for entity in entities[:2]:  # Top 2
                info = self.entity_memory.get_entity(entity[0])
                if info:
                    entity_info.append(f"{entity[0]}: {info}")
            if entity_info:
                context_parts.append(f"Entities:\n{', '.join(entity_info)}")

        return "\n\n".join(context_parts)

# SOLUTION: Use hybrid memory with comprehensive demonstration
def test_hybrid_memory():
    """
    Demonstrate hybrid memory combining all memory systems.

    Expected Output:
        Summary: [summary of conversation]
        Recent messages: [recent exchanges]
        Relevant memories: [semantically related long-term memories]
        Entities: [extracted entity information]

    This shows how all memory systems work together.
    """
    print("=== Hybrid Memory Test ===\n")

    hybrid = HybridMemory()

    print("Adding messages to hybrid memory system...")
    hybrid.add("user", "I'm Alice and I'm a software engineer", {"important": True})
    hybrid.add("assistant", "Hello Alice! Nice to meet you.")
    hybrid.add("user", "Remember that I love hiking", {"important": True})
    hybrid.add("assistant", "I'll remember that you enjoy hiking, Alice!")
    hybrid.add("user", "I work at Google in Mountain View")
    hybrid.add("assistant", "That's great! Google is in Mountain View, California.")

    print("\nRetrieving context for query: 'What do you know about me?'")
    context = hybrid.retrieve_context("What do you know about me?")

    print("\n--- Retrieved Context ---")
    print(context)

    print("\n--- Memory System Statistics ---")
    print(f"Short-term messages: {len(hybrid.short_term.messages)}")
    print(f"Long-term memories: {len(hybrid.long_term.documents)}")
    print(f"Entities tracked: {len(hybrid.entity_memory.entities)}")
    print(f"Summary length: {len(hybrid.summary_memory.summary)} words")

# Run the test
test_hybrid_memory()
```

### Exercise 6: Memory with Reflection

```python
class ReflectiveMemory:
    def __init__(self):
        self.memories = []
        self.reflections = []
        self.llm = ChatOpenAI(model="gpt-4")

    def add_memory(self, memory: str):
        """
        Add a new memory and trigger reflection periodically.

        SOLUTION: Automatically triggers reflection every 5 memories
        to extract insights and patterns from accumulated experiences.
        """
        import time
        self.memories.append({
            "content": memory,
            "timestamp": time.time(),
        })

        # SOLUTION: Trigger reflection if needed
        if len(self.memories) % 5 == 0:
            self._reflect()

    def _reflect(self):
        """Reflect on recent memories."""

        recent = self.memories[-5:]
        recent_text = "\n".join([m["content"] for m in recent])

        prompt = f"""Reflect on these memories and extract insights or patterns:

{recent_text}

Reflection:"""

        response = self.llm.invoke(prompt)

        self.reflections.append({
            "content": response.content,
            "based_on_memories": [m["content"] for m in recent],
            "timestamp": time.time(),
        })

    def get_insights(self) -> List[str]:
        """Get all insights from reflections."""
        return [r["content"] for r in self.reflections]

    def retrieve_with_insights(self, query: str) -> Dict:
        """Retrieve memories with relevant insights."""

        # Simple keyword matching
        relevant_memories = [
            m for m in self.memories
            if query.lower() in m["content"].lower()
        ]

        relevant_insights = [
            r for r in self.reflections
            if query.lower() in r["content"].lower()
        ]

        return {
            "memories": relevant_memories,
            "insights": relevant_insights,
        }
```

### Exercise 7: Persistent Memory Storage

```python
import json
import sqlite3
from pathlib import Path

class PersistentMemory:
    def __init__(self, db_path="./agent_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Initialize database with schema for memories and entities.

        SOLUTION: Creates SQLite tables with proper indexes for
        efficient querying and persistence of memory data.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # SOLUTION: Create tables for memories and entities
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp REAL,
                embedding BLOB
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                facts TEXT,
                last_updated REAL
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON memories(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_name
            ON entities(name)
        """)

        conn.commit()
        conn.close()

    def save_memory(self, content: str, metadata: dict = None):
        """Save memory to database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO memories (content, metadata, timestamp)
            VALUES (?, ?, ?)
        """, (
            content,
            json.dumps(metadata or {}),
            time.time(),
        ))

        conn.commit()
        conn.close()

    def load_memories(self, limit: int = 100) -> List[Dict]:
        """Load memories from database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT content, metadata, timestamp
            FROM memories
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "content": row[0],
                "metadata": json.loads(row[1]),
                "timestamp": row[2],
            }
            for row in rows
        ]

    def save_entity(self, name: str, facts: List[Dict]):
        """Save entity to database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO entities (name, facts, last_updated)
            VALUES (?, ?, ?)
        """, (
            name,
            json.dumps(facts),
            time.time(),
        ))

        conn.commit()
        conn.close()

# SOLUTION: Use persistent memory with comprehensive testing
def test_persistent_memory():
    """
    Demonstrate persistent memory storage and retrieval.

    Expected Output:
        Alice loves hiking
        Alice is a software engineer

    Note: Data persists across sessions in SQLite database.
    """
    import os
    import time

    print("=== Persistent Memory Test ===\n")

    # Use a test database
    db_path = "./test_agent_memory.db"

    # Clean up any existing test database
    if os.path.exists(db_path):
        os.remove(db_path)

    pm = PersistentMemory(db_path=db_path)

    print("Saving memories to database...")
    pm.save_memory("Alice loves hiking", {"user": "Alice", "topic": "hobbies"})
    pm.save_memory("Alice is a software engineer", {"user": "Alice", "topic": "work"})
    pm.save_memory("Bob enjoys playing guitar", {"user": "Bob", "topic": "hobbies"})

    print("\nLoading memories from database...")
    memories = pm.load_memories()

    print(f"\nRetrieved {len(memories)} memories:")
    for mem in memories:
        print(f"  - {mem['content']} (metadata: {mem['metadata']})")

    # Test entity persistence
    print("\n--- Testing Entity Persistence ---")
    pm.save_entity("Alice", [
        {"property": "profession", "value": "software engineer"},
        {"property": "hobby", "value": "hiking"}
    ])

    pm.save_entity("Bob", [
        {"property": "profession", "value": "teacher"},
        {"property": "hobby", "value": "guitar"}
    ])

    print("Saved entities: Alice, Bob")

    print("\n--- Database Statistics ---")
    print(f"Database location: {db_path}")
    print(f"Database size: {os.path.getsize(db_path)} bytes")

# Run the test
test_persistent_memory()
```

---

**Last Updated:** 2026-02-05
**Status:** ✅ Complete - All tasks completed with solutions
