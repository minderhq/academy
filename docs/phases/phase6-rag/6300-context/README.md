# 6300: Context Management

## Module Overview

This module covers advanced context management techniques for RAG systems, including knowledge graphs, GraphRAG, and long-context architectures. You'll learn to structure and retrieve context beyond simple vector search.

**Why This Matters:**
- Structured knowledge improves retrieval accuracy
- Knowledge graphs capture relationships vector search misses
- Long-context models require careful context organization
- GraphRAG combines the best of structured and unstructured retrieval

## Learning Objectives

After completing this module, you will be able to:

- **Knowledge Graphs**: Model entities and relationships with Neo4j
- **GraphRAG**: Combine knowledge graphs with vector retrieval
- **Long-Context Architectures**: Manage context windows effectively
- **CAG (Context-Augmented Generation)**: Optimize context for generation
- **Context Optimization**: Structure and compress context efficiently

## Module Contents

### 6301: Neo4j and Knowledge Graphs
**Graph-Based Knowledge Representation**

- Graph database fundamentals
- Neo4j and Cypher query language
- Entity and relationship extraction
- Building knowledge graphs from text
- Graph traversal and pattern matching

**Experiments:**
- Set up Neo4j database
- Extract entities from documents
- Build knowledge graph
- Query graph for context

### 6302: CAG and Long-Context Architectures
**Context Window Optimization**

- Context-Augmented Generation (CAG)
- Long-context model strategies
- Context compression techniques
- Hierarchical context organization
- Context window management

**Experiments:**
- Implement CAG pipeline
- Optimize context compression
- Build hierarchical retrieval
- Test long-context strategies

### 6303: Neo4j Deployment Guide
**Production Knowledge Graph Setup** (Guide)

- Neo4j deployment options
- Performance optimization
- Backup and scaling strategies
- Security considerations

**Guide:** [guides/6303-Neo4j-Deployment-Guide.md](./guides/6303-Neo4j-Deployment-Guide.md)

### 6304: GraphRAG Implementation
**Knowledge-Graph Enhanced RAG** (Guide)

- GraphRAG architecture
- Entity-relationship retrieval
- Hybrid vector-graph queries
- Graph-based context expansion

**Guide:** [guides/6304-GraphRAG-Implementation.md](./guides/6304-GraphRAG-Implementation.md)

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 6100: Vector Embeddings (basic retrieval)
- [ ] Module 6200: Retrieval (advanced retrieval)
- [ ] Python programming proficiency
- [ ] Basic understanding of graph databases
- [ ] Neo4j installation (or cloud access)

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** Knowledge graphs, Neo4j, GraphRAG, long context
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Context management projects
- **Duration:** 8-10 hours
- **Topics:**
  - Build knowledge graph from documents
  - Implement GraphRAG pipeline
  - Optimize long-context retrieval
  - Deploy Neo4j for production
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **6100: Vector Embeddings** (unstructured retrieval)
- **6200: Retrieval** (retrieval strategies)
- **6400: Vector Databases** (data storage)
- **7400: Memory** (agent memory systems)

## Time Commitment

| Activity | Time |
|----------|------|
| Reading (6301) | 4 hours |
| Experiments (6301) | 4 hours |
| Reading (6302) | 3 hours |
| Experiments (6302) | 4 hours |
| Guides (6303-6304) | 3 hours |
| Quiz | 30 minutes |
| Practice | 8-10 hours |
| **Total** | **26-28 hours** |

## Resources

**Essential Tools:**
- Neo4j (graph database)
- Neo4j Python Driver
- LangChain GraphCypherQAChain
- LlamaIndex KnowledgeGraphIndex
- GraphRAG (Microsoft)

**Essential Papers:**
- "GraphRAG: Enhancing Retrieval with Knowledge Graphs"
- "From Local to Global: A Graph RAG Approach"
- "Dense X Retrieval: What Retrieval Granularity"

## Knowledge Graph vs Vector Search

| Aspect | Knowledge Graph | Vector Search |
|--------|----------------|---------------|
| Relationships | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Exact Matching | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Semantic Understanding | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Flexibility | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Explanation | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Scalability | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## GraphRAG Architecture

```
Document
    ↓
┌──────────────┬──────────────┐
│ Entity       │ Relationship │
│ Extraction   │ Extraction   │
└──────┬───────┴──────┬───────┘
       ↓              ↓
    Knowledge Graph (Neo4j)
       ↓
┌──────────────┬──────────────┐
│ Graph        │ Vector       │
│ Retrieval    │ Retrieval    │
└──────┬───────┴──────┬───────┘
       ↓              ↓
       Hybrid Fusion
       ↓
    Context Generation
```

## Context Management Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Flat Context | All chunks concatenated | Short documents |
| Hierarchical | Summary → Detail | Long documents |
| Graph-Based | Entity → Context | Complex relationships |
| Compressed | Context compression | Context window limits |
| Iterative | Retrieve → Generate → Retrieve | Multi-hop reasoning |

## Neo4j Cypher Examples

**Find related entities:**
```cypher
MATCH (e1:Entity {name: $entity})-[:RELATED_TO]-(e2:Entity)
RETURN e2.name, e2.type
LIMIT 10
```

**Find path between entities:**
```cypher
MATCH path = shortestPath(
  (e1:Entity {name: $entity1})-[*..5]-(e2:Entity {name: $entity2})
)
RETURN path
```

## Long-Context Optimization

| Technique | Benefit | Complexity |
|-----------|---------|------------|
| Chunk Reordering | Group related content | Low |
| Context Compression | Fit more content | Medium |
| Hierarchical Summary | Multi-scale understanding | Medium |
| Recurrent Context | Infinite context | High |

## Tips for Success

1. **Start with vectors**: Add graphs for specific use cases
2. **Extract carefully**: Entity quality matters
3. **Use hybrid approaches**: Graph + vector is often best
4. **Optimize context length**: Not too short, not too long
5. **Test on real queries**: Synthetic benchmarks lie

## Common Pitfalls

- **Over-engineering**: Simple queries don't need graphs
- **Poor entity extraction**: Garbage in, garbage out
- **Ignoring structure**: Documents have inherent structure
- **Context stuffing**: More ≠ better
- **Skipping optimization**: Raw retrieval needs tuning

## When to Use Knowledge Graphs

| Scenario | Recommended Approach |
|----------|---------------------|
| FAQ content | Knowledge Graph |
| Technical documentation | Graph + Vector |
| General knowledge | Vector only |
| Relationship-heavy | Knowledge Graph |
| Multi-hop reasoning | Graph + Vector |

## Context Window Management

```
Available Context: 128K tokens

Distribution Strategy:
├── System Prompt: 1K tokens
├── Retrieved Context: 100K tokens
│   ├── Graph entities: 20K
│   └── Vector chunks: 80K
├── Conversation History: 20K tokens
└── Response Headroom: 7K tokens
```

---

**Next Module:** [6400: Vector Databases](../6400-vector-databases/README.md)

**Previous Module:** [6200: Retrieval](../6200-retrieval/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 6 documentation.

---

**Last Updated:** 2026-02-04
