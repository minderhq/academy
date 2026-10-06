---
Document ID: 7400-QUIZ
Title: "7400: Memory Systems - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'agents', 'memory']
---

# 7400: Memory Systems - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Short-term memory in agents:**

A) Persists forever across every session and restart
B) No memory
C) Current conversation
D) Long-term storage

**2. Long-term memory:**

A) No storage
B) Temporary
C) Only current conversation
D) Persistent storage

**3. Vector memory stores:**

A) Embeddings for retrieval
B) The raw conversation text with no vector step
C) Only keywords
D) No storage

**4. Key-value memory:**

A) Approximate vector search over dense embeddings
B) Direct lookup by key
C) Sequential only
D) No lookup

**5. Memory retrieval:**

A) Returns relevant memories
B) Random selection from the entire memory store
C) Returns all memories
D) No retrieval

**6. Memory importance scoring:**

A) Some memories more important
B) Random scores assigned with no signal at all
C) No scoring
D) All memories equal

**7. Memory consolidation:**

A) Only long-term stores participate in consolidation
B) No consolidation
C) Only short-term
D) Moving from short to long-term

**8. Episodic memory stores:**

A) No events at all, only raw token counts
B) Specific events/experiences
C) Only facts
D) General knowledge

**9. Semantic memory stores:**

A) Events and episodes from specific past interactions
B) Only current
C) No knowledge
D) General knowledge/facts

**10. Memory window:**

A) No history kept beyond the current single turn
B) Recent tokens only
C) All history
D) Random

**11. Retrieval Augmented Generation (RAG) for memory:**

A) Retrieve everything in the store on every single turn
B) No retrieval
C) Random retrieval
D) Retrieve relevant memories

**12. MemGPT:**

A) No memory at any layer of the architecture
B) Only long-term
C) Only short-term
D) Hierarchical memory system

**13. Memory compression:**

A) Summarize/compress old memories
B) Random deletion of records without any policy
C) Store everything
D) No compression

**14. Memory search methods:**

A) Only vector search
B) Random guessing among the available indexes
C) Vector, keyword, hybrid
D) No search

**15. Reflective memory:**

A) Only human reflection, never the agent itself
B) Not useful
C) Agent reflects on past experiences
D) No reflection

**16. Working memory:**

A) Long-term storage of every completed project
B) No memory
C) Current task information
D) Persistent

**17. Episodic buffer:**

A) Not used in any modern agent architecture
B) Temporary storage for processing
C) No buffer
D) Long-term storage

**18. Memory decay:**

A) All memories persist forever with equal accessibility
B) Random decay
C) Old memories less accessible
D) No decay

**19. Personalization through memory:**

A) No personalization of any kind is possible
B) Remembers user preferences
C) Not useful
D) Only generic

**20. Memory constraints:**

A) Limited by context/compute
B) Unlimited memory regardless of the context window
C) Only storage limits
D) No limits

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Short-term memory holds the current conversation |
| 2 | D | Long-term memory persists across sessions |
| 3 | A | Vector memory embeds records for similarity retrieval |
| 4 | B | Key-value memory looks entries up directly by key |
| 5 | A | Retrieval returns the memories relevant to the query |
| 6 | A | Importance scoring ranks some memories above others |
| 7 | D | Consolidation moves short-term memories into long-term |
| 8 | B | Episodic memory keeps specific events and experiences |
| 9 | D | Semantic memory holds general knowledge and facts |
| 10 | B | The memory window keeps recent tokens only |
| 11 | D | RAG retrieves the relevant memories per query |
| 12 | D | MemGPT layers short and long-term hierarchically |
| 13 | A | Compression summarizes old memories to save space |
| 14 | C | Search spans vector, keyword and hybrid methods |
| 15 | C | Reflective memory reviews past experiences for lessons |
| 16 | C | Working memory holds current-task information |
| 17 | B | The episodic buffer is temporary processing storage |
| 18 | C | Decay makes old memories less accessible over time |
| 19 | B | Remembering preferences personalizes responses |
| 20 | A | Memory is bounded by context and compute limits |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-2, 5, 10:** [7401: Long-term Memory for Agents](../7401-Long-term-Memory.md) — the architecture diagram's short-term context window beside the long-term stores, persistent memory across sessions opening the lesson, and the operations table's Retrieval row answered by semantic search
- **Questions 3, 11:** [7403: Vector Memory and Embedding-Based Storage](../7403-Vector-Memory.md) — memories written as embeddings and recalled by semantic similarity through the Write and Read paths, the retrieval-augmented shape the quiz describes
- **Question 4:** [7405: Key-Value Memory and Checkpoint Stores](../7405-Key-Value-Memory-and-Checkpoint-Stores.md) — the dedicated key-value store lesson: exact-key addressing landing the cart dict verbatim where the ANN top-1 hands back a refund doc, the O(1) direct lookup by key the correct answer names, and the checkpoint store whose session state lives and dies by the TTL lease
- **Question 6:** [7401: Long-term Memory for Agents](../7401-Long-term-Memory.md) — the multi-tier architecture's MemoryItem dataclass carrying an explicit importance score
- **Questions 7, 13:** [7401: Long-term Memory for Agents](../7401-Long-term-Memory.md) — the Consolidation operation merging similar memories via clustering plus summarization, and the §2.3 summarize_old_memories job compressing aged entries on a schedule
- **Questions 8-9:** [7403: Vector Memory and Embedding-Based Storage](../7403-Vector-Memory.md) — the taxonomy's Episodic row, what happened and when as timestamped event records, against its Semantic row of distilled facts and preferences
- **Question 12:** [7404: Reflective Memory and Context Paging](../7404-Reflective-Memory-and-Context-Paging.md) — MemGPT's virtual context management with main context as RAM and external context as disk; the paging fence runs 7 page-outs against a 48-token budget where keep-everything overflows at turn 12 and drop-oldest loses the probe's answer while paging retains 100%
- **Question 14:** [7401: Long-term Memory for Agents](../7401-Long-term-Memory.md) — the hybrid search example combining vector and keyword lookup over one collection
- **Question 15:** [7404: Reflective Memory and Context Paging](../7404-Reflective-Memory-and-Context-Paging.md) — reflective memory as a named pattern: the tri-component blend (recency 0.5, relevance 3, importance 2) ranking the decisive old memory 5.212 against fresh trivia's 3.483, and the pruning-versus-distilling split where naive pruning lands 4/6 probes with the auth facts dead at 0.000 while distilled facts answer 6/6 at 0.924
- **Questions 16-17:** [7404: Reflective Memory and Context Paging](../7404-Reflective-Memory-and-Context-Paging.md) — the episodic buffer as the reflexion loop's training signal, converting evaluator failures into stored verbal rules that walk 25 tasks 20% to 68% to 96% to 100% while the buffer-less actor sits at 5/25; the Working tier's window is the 48-token budget the paging fence holds
- **Question 18:** [7401: Long-term Memory for Agents](../7401-Long-term-Memory.md) — time-based decay with TTL expiry metadata and the cleanup_expired_memories sweeper, matching the operations table's Forgetting row
- **Question 19:** [7401: Long-term Memory for Agents](../7401-Long-term-Memory.md) — persistent memory existing to power personalized interactions, with the best-practices list directing personalization from user history
- **Question 20:** [7403: Vector Memory and Embedding-Based Storage](../7403-Vector-Memory.md) — the Performance and Cost table where context cost runs 300-500 tokens per turn as the real currency, beside the embedding, search and storage magnitudes that bound a memory system
