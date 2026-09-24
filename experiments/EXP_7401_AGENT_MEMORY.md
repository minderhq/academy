# EXP_7401: Agent Memory Systems Experiments

## Overview
Practical experiments for implementing and testing long-term memory systems for AI agents on PROJECT-OMEGA infrastructure.

## Experiment 1: Qdrant VectorStore with LangChain

### Objective
Implement vector-based memory using Qdrant and LangChain for conversation persistence.

### Setup
```bash
pip install langchain langchain-community langchain-openai sentence-transformers qdrant-client
```

### Implementation
```python
# agent_memory_qdrant.py
from langchain.memory import VectorStoreMemory
from langchain.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Initialize Qdrant
qdrant_client = QdrantClient(url="http://localhost:6334")

# Create collection for memories
COLLECTION_NAME = "agent_memories"

try:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )
except Exception:
    pass  # Collection exists

# Setup embeddings
embeddings = OpenAIEmbeddings(openai_api_key="your-api-key")

# Create vector store
vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embeddings=embeddings
)

# Create memory with retrieval
memory = VectorStoreMemory(
    memory_key="chat_history",
    vectorstore=vectorstore,
    k=5,  # Retrieve top 5 relevant memories
    return_only_outputs=False
)

# Create conversation chain
llm = ChatOpenAI(model="gpt-4o", temperature=0)
conversation = ConversationChain(llm=llm, memory=memory)

# Test conversation
print("Agent with Long-term Memory")
print("=" * 50)

response1 = conversation.predict(input="Hi, I'm working on a machine learning project about image classification.")
print(f"User: Hi, I'm working on a machine learning project about image classification.")
print(f"Agent: {response1}\n")

response2 = conversation.predict(input="What's the best architecture for that?")
print(f"User: What's the best architecture for that?")
print(f"Agent: {response2}\n")

# Start new session (simulate agent restart)
print("\n--- New Session (Simulating Restart) ---\n")

# New conversation with same memory
new_conversation = ConversationChain(llm=llm, memory=memory)
response3 = new_conversation.predict(input="What did I ask you about earlier?")
print(f"User: What did I ask you about earlier?")
print(f"Agent: {response3}\n")
```

---

## Experiment 2: Memoria-style Memory System

### Objective
Implement a hierarchical memory system with short-term, working, and long-term memory.

### Implementation
```python
# memoria_memory_system.py
import json
import time
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
from sentence_transformers import SentenceTransformer

class MemoriaMemorySystem:
    """
    Hierarchical memory system inspired by Memoria

    Memory Layers:
    1. Short-term: Recent context (last N messages)
    2. Working memory: Current task/session
    3. Long-term: Persistent vector storage
    """

    def __init__(self, qdrant_url="http://192.168.1.100:6334"):
        # Embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384

        # Qdrant client
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection = "agent_longterm_memory"

        # Setup collection
        self._setup_collection()

        # Memory stores
        self.short_term: List[Dict] = []  # Last 10 messages
        self.working_memory: List[Dict] = []  # Current session
        self.session_id = None

    def _setup_collection(self):
        """Initialize Qdrant collection"""
        try:
            self.qdrant.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            print("Created long-term memory collection")
        except Exception:
            pass  # Collection exists

    def remember(self, content: str, metadata: Dict = None, importance: float = 0.5):
        """
        Store information in appropriate memory layer

        Args:
            content: Text content to remember
            metadata: Additional context (type, timestamp, etc.)
            importance: 0-1 score for long-term retention
        """
        timestamp = time.time()
        memory_entry = {
            "content": content,
            "timestamp": timestamp,
            "metadata": metadata or {},
            "importance": importance
        }

        # Always add to short-term
        self.short_term.append(memory_entry)
        if len(self.short_term) > 10:
            self.short_term.pop(0)

        # Add to working memory
        self.working_memory.append(memory_entry)

        # Store in long-term if important enough
        if importance >= 0.5:
            self._store_longterm(memory_entry)

    def _store_longterm(self, memory_entry: Dict):
        """Store in vector database"""
        # Generate embedding
        embedding = self.embedder.encode(memory_entry["content"])

        # Create point
        point = PointStruct(
            id=int(time.time() * 1000),  # Unique ID
            vector=embedding.tolist(),
            payload=memory_entry
        )

        # Store
        self.qdrant.upsert(
            collection_name=self.collection,
            points=[point]
        )

    def recall(self, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieve relevant memories from all layers

        Returns combined short-term + working + long-term memories
        """
        results = []

        # Short-term (most recent)
        results.extend(self.short_term[-k:])

        # Working memory
        results.extend(self.working_memory[-k:])

        # Long-term (semantic search)
        query_embedding = self.embedder.encode(query)

        search_results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_embedding.tolist(),
            limit=k,
            score_threshold=0.6  # Minimum similarity
        )

        for result in search_results:
            results.append(result.payload)

        return results

    def reflect(self) -> str:
        """
        Generate reflection on current working memory
        """
        if not self.working_memory:
            return "No memories to reflect upon."

        # Summarize working memory
        summary = "Reflection on current session:\n"
        for memory in self.working_memory[-5:]:
            summary += f"- {memory['content']}\n"

        # Store reflection as high-importance memory
        self.remember(summary, metadata={"type": "reflection"}, importance=0.8)

        return summary

    def consolidate(self):
        """
        Consolidate working memory into long-term storage
        """
        for memory in self.working_memory:
            if memory["importance"] >= 0.5:
                self._store_longterm(memory)

        # Clear working memory
        self.working_memory = []
        print("Working memory consolidated to long-term storage")

    def start_session(self, session_id: str):
        """Start a new session"""
        self.session_id = session_id
        self.working_memory = []
        print(f"Started session: {session_id}")

    def end_session(self):
        """End current session and consolidate"""
        self.consolidate()
        self.session_id = None

    def get_memory_stats(self) -> Dict:
        """Get statistics about memory usage"""
        count = self.qdrant.count(self.collection)

        return {
            "short_term_count": len(self.short_term),
            "working_memory_count": len(self.working_memory),
            "longterm_count": count,
            "session_id": self.session_id
        }


# Test the memory system
def test_memoria_memory():
    """Test the Memoria-style memory system"""
    memory = MemoriaMemorySystem()

    print("=" * 60)
    print("Memoria Memory System Test")
    print("=" * 60)

    # Start a session
    memory.start_session("session_001")

    # Add memories with varying importance
    print("\n--- Storing Memories ---\n")

    memories = [
        ("The user is working on image classification", 0.7, {"type": "project"}),
        ("User prefers Python over JavaScript", 0.9, {"type": "preference"}),
        ("Today is Monday and it's raining", 0.3, {"type": "context"}),
        ("User asked about CNN architectures", 0.8, {"type": "question"}),
        ("User mentioned they have 11GB-class GPU GPU", 0.9, {"type": "hardware"}),
    ]

    for content, importance, metadata in memories:
        memory.remember(content, metadata=metadata, importance=importance)
        print(f"Stored: {content} (importance: {importance})")

    # Recall relevant memories
    print("\n--- Recalling Memories ---\n")

    query = "What GPU does the user have?"
    recalled = memory.recall(query)

    print(f"Query: {query}\n")
    for i, mem in enumerate(recalled[:5], 1):
        print(f"{i}. {mem.get('content', mem.get('text', 'N/A'))}")

    # Generate reflection
    print("\n--- Reflection ---\n")
    reflection = memory.reflect()
    print(reflection)

    # End session
    print("\n--- Session Stats ---\n")
    memory.end_session()
    stats = memory.get_memory_stats()
    print(f"Memory Stats: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    test_memoria_memory()
```

---

## Experiment 3: Memory-Augmented ReAct Agent

### Objective
Build a ReAct agent that uses memory for persistent knowledge.

### Implementation
```python
# react_agent_with_memory.py
from typing import List, Tuple, Optional
import re
from memoria_memory_system import MemoriaMemorySystem

class MemoryReActAgent:
    """
    ReAct Agent with persistent memory

    Thought → Action → Observation (with memory retrieval)
    """

    def __init__(self, llm, memory_system: MemoriaMemorySystem):
        self.llm = llm
        self.memory = memory_system
        self.max_iterations = 5

    def run(self, query: str) -> str:
        """Run ReAct loop with memory"""

        # Retrieve relevant memories
        memories = self.memory.recall(query, k=3)
        memory_context = self._format_memories(memories)

        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}\n")

        thought_history = []

        for iteration in range(self.max_iterations):
            # Build prompt with memory
            prompt = self._build_prompt(query, memory_context, thought_history)

            # Get next step from LLM
            response = self.llm.generate(prompt)
            thought, action = self._parse_response(response)

            print(f"[Iteration {iteration + 1}]")
            print(f"Thought: {thought}")
            print(f"Action: {action}")

            thought_history.append({"thought": thought, "action": action})

            # Execute action
            if action.startswith("Answer"):
                # Final answer
                answer = self._extract_answer(action)
                print(f"\nFinal Answer: {answer}\n")

                # Store in memory
                self.memory.remember(
                    f"Q: {query} → A: {answer}",
                    metadata={"type": "qa"},
                    importance=0.7
                )

                return answer

            elif action.startswith("Search"):
                # Simulated search
                observation = self._execute_search(action)
                print(f"Observation: {observation}")
                thought_history[-1]["observation"] = observation

            else:
                observation = "Unknown action"
                print(f"Observation: {observation}")
                thought_history[-1]["observation"] = observation

        return "Max iterations reached"

    def _format_memories(self, memories: List[Dict]) -> str:
        """Format memories for prompt"""
        if not memories:
            return "No relevant memories found."

        formatted = "Relevant Memories:\n"
        for i, mem in enumerate(memories, 1):
            content = mem.get("content", mem.get("text", ""))
            formatted += f"{i}. {content}\n"

        return formatted

    def _build_prompt(self, query: str, memory_context: str, history: List[Dict]) -> str:
        """Build prompt with memory and conversation history"""
        prompt = f"""You are a helpful AI agent with access to past memories.

{memory_context}

Current Question: {query}

"""

        if history:
            prompt += "Previous steps:\n"
            for step in history[-3:]:
                prompt += f"Thought: {step['thought']}\n"
                prompt += f"Action: {step['action']}\n"
                if "observation" in step:
                    prompt += f"Observation: {step['observation']}\n"
                prompt += "\n"

        prompt += """Respond in the following format:
Thought: [your reasoning]
Action: [one of: Answer[your answer], Search[query]]

Your response:"""

        return prompt

    def _parse_response(self, response: str) -> Tuple[str, str]:
        """Parse LLM response into thought and action"""
        thought_match = re.search(r"Thought: (.+)", response)
        action_match = re.search(r"Action: (.+)", response)

        thought = thought_match.group(1) if thought_match else "I need to think more."
        action = action_match.group(1) if action_match else "Answer[I don't know]"

        return thought, action

    def _extract_answer(self, action: str) -> str:
        """Extract answer from Answer action"""
        match = re.search(r"Answer\[(.+)\]", action)
        return match.group(1) if match else action

    def _execute_search(self, action: str) -> str:
        """Execute search action (simulated)"""
        match = re.search(r"Search\[(.+)\]", action)
        query = match.group(1) if match else action

        # Simulated search results
        simulated_results = {
            "GPU": "NVIDIA 11GB-class GPU has 11GB VRAM, 4352 CUDA cores",
            "Python": "Python is a high-level programming language",
            "machine learning": "ML enables computers to learn from data",
        }

        for key, value in simulated_results.items():
            if key.lower() in query.lower():
                return f"Found: {value}"

        return f"No results found for '{query}'"


# Simple LLM simulator for testing
class MockLLM:
    """Mock LLM for testing without API calls"""

    def generate(self, prompt: str) -> str:
        """Generate response based on prompt patterns"""

        if "GPU" in prompt or "gpu" in prompt:
            return """Thought: I recall information about the user's GPU from memory.
Action: Answer[The user has an NVIDIA GPU with 11GB VRAM]"""
        elif "Python" in prompt:
            return """Thought: I should search for Python information.
Action: Search[Python programming language]"""
        else:
            return """Thought: I need more information to answer this question.
Action: Search[relevant information]"""


# Test the agent
def test_memory_react_agent():
    """Test MemoryReActAgent"""
    from memoria_memory_system import MemoriaMemorySystem

    # Initialize
    memory = MemoriaMemorySystem()
    memory.start_session("test_session")

    # Add some memories
    memory.remember(
        "User has NVIDIA 11GB-class GPU GPU with 11GB VRAM",
        metadata={"type": "hardware"},
        importance=0.9
    )

    memory.remember(
        "User prefers Python for machine learning",
        metadata={"type": "preference"},
        importance=0.8
    )

    # Create agent
    llm = MockLLM()
    agent = MemoryReActAgent(llm, memory)

    # Run queries
    print("\n" + "=" * 60)
    print("Testing Memory-Augmented ReAct Agent")
    print("=" * 60)

    queries = [
        "What GPU do I have?",
        "Tell me about Python",
    ]

    for query in queries:
        agent.run(query)

    # Cleanup
    memory.end_session()

if __name__ == "__main__":
    test_memory_react_agent()
```

---

## Experiment 4: Memory Retrieval Quality Test

### Objective
Measure memory recall accuracy and relevance scoring.

### Implementation
```python
# memory_quality_test.py
import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
from memoria_memory_system import MemoriaMemorySystem

def test_memory_retrieval_quality():
    """Test memory retrieval quality metrics"""

    memory = MemoriaMemorySystem()

    # Create test memories
    test_memories = [
        ("User is a machine learning engineer", 0.9, {"domain": "ml"}),
        ("User works on computer vision projects", 0.8, {"domain": "cv"}),
        ("User uses PyTorch framework", 0.7, {"tool": "pytorch"}),
        ("User has 11GB-class GPU GPU", 0.9, {"hardware": "gpu"}),
        ("User prefers Linux over Windows", 0.6, {"os": "linux"}),
    ]

    print("Storing test memories...")
    for content, importance, metadata in test_memories:
        memory.remember(content, metadata=metadata, importance=importance)

    # Test queries with expected results
    test_queries = [
        ("What does the user work on?", ["machine learning", "computer vision"]),
        ("What GPU does the user have?", ["11GB-class GPU"]),
        ("What tools does the user use?", ["PyTorch"]),
        ("What's the user's OS preference?", ["Linux"]),
    ]

    print("\nTesting retrieval quality...\n")

    results = []
    for query, expected_keywords in test_queries:
        recalled = memory.recall(query, k=5)

        # Check if expected keywords are in recalled memories
        recalled_text = " ".join([m.get("content", "") for m in recalled])

        hit = any(kw.lower() in recalled_text.lower() for kw in expected_keywords)

        results.append({
            "query": query,
            "expected": expected_keywords,
            "hit": hit,
            "recalled_count": len(recalled)
        })

        status = "✓" if hit else "✗"
        print(f"{status} Query: {query}")
        print(f"  Expected: {expected_keywords}")
        for i, mem in enumerate(recalled[:3], 1):
            print(f"  {i}. {mem.get('content', 'N/A')[:60]}...")
        print()

    # Calculate metrics
    accuracy = sum(r["hit"] for r in results) / len(results)

    print("=" * 60)
    print(f"Retrieval Accuracy: {accuracy * 100:.1f}%")
    print(f"Total Queries: {len(results)}")
    print(f"Successful Hits: {sum(r['hit'] for r in results)}")
    print("=" * 60)

if __name__ == "__main__":
    test_memory_retrieval_quality()
```

---

## Performance Benchmarks

### Expected Memory Operations (Qdrant, local deployment)

| Operation | Expected Latency | Notes |
|-----------|------------------|-------|
| Store memory | ~10-50ms | Depends on network |
| Retrieve (k=5) | ~50-200ms | Semantic search |
| Reflection generation | ~1-3s | LLM-dependent |
| Consolidation | ~100-500ms | Batch writes |

### Memory Capacity Planning

| Memory Type | Estimated Size | Max Entries (10GB storage) |
|-------------|---------------|----------------------------|
| Short-term | ~1KB per entry | N/A (in-memory) |
| Working memory | ~1KB per entry | N/A (in-memory) |
| Long-term (with 384-dim vectors) | ~2KB per entry | ~5M entries |

---

## Experiment Checklist

- [ ] Qdrant VectorStore with LangChain setup
- [ ] Memoria hierarchical memory implementation
- [ ] Short-term memory test (10 messages)
- [ ] Working memory consolidation
- [ ] Long-term semantic retrieval
- [ ] Memory-augmented ReAct agent
- [ ] Reflection generation test
- [ ] Retrieval quality benchmark
- [ ] Memory importance scoring validation
- [ ] Multi-session memory persistence

---

## Related Documentation
- [7401: Long-term Memory](../docs/phases/phase7-agentic/7400-memory/7401-Long-term-Memory.md)
- [7101: ReAct Loop System](../docs/phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
- [6401: Qdrant Setup](../docs/phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md)
- [6101: HNSW Indexing](../docs/phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md)
