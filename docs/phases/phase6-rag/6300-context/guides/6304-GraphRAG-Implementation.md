---
Document ID: 6304
Title: "6304: GraphRAG Implementation Guide"
Phase: 6
Module: 6300
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'graphrag', 'knowledge-graph', 'neo4j']
---

# 6304: GraphRAG Implementation Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [GraphRAG Architecture](#graphrag-architecture)
- [Implementation 1: Graph Construction](#implementation-1-graph-construction)
- [Implementation 2: Hybrid Graph + Vector RAG](#implementation-2-hybrid-graph--vector-rag)
- [Implementation 3: Multi-Hop Reasoning](#implementation-3-multi-hop-reasoning)
- [Implementation 4: Entity Extraction with LLM](#implementation-4-entity-extraction-with-llm)
- [Implementation 5: Complete GraphRAG Pipeline](#implementation-5-complete-graphrag-pipeline)
- [Production Note: Microsoft GraphRAG](#production-note-microsoft-graphrag)
- [Quick Start](#quick-start)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain the GraphRAG loop — walk the four-stage pipeline (ingestion → query processing → context building → generation) and name what graph traversal adds that pure vector RAG lacks on multi-hop questions
- Build the knowledge graph — run `KnowledgeGraphBuilder` (`create_constraints`, `add_document` upserting entities, `CONTAINS` links, and `RELATIONSHIP {type}` edges) and justify why traversals read the `RELATIONSHIP` type the write path actually creates
- Run hybrid graph + vector ranking — `GraphRAGSystem.query` fuses Qdrant `query_points` scores with graph document scores (1/(hop+1), max-aggregated over the traversal) through the `alpha` blend — `alpha=1` vector-only, `alpha=0` graph-only
- Extract reasoning paths — `MultiHopReasoner.reasoning_paths` returns shortest-first paths (names, relationship types, hop counts) between two entities, and `explain_reasoning` renders each as an `A REL B → …` chain
- Extract entities with an LLM — `EntityExtractor.extract` prompts with a JSON contract, applies the chat template, slices off the echoed prompt before `json.loads`, and returns empty lists on `JSONDecodeError`
- Assemble the pipeline — `CompleteGraphRAG` chains ingestion (LLM extraction → graph upsert) and querying (hybrid context → prompt → answer), launched against the pinned `neo4j:2026.09.0` and `qdrant/qdrant:v1.19.1` containers from Quick Start

---

## Abstract
Complete implementation guide for GraphRAG (Knowledge Graph-enhanced Retrieval Augmented Generation) on AI Engineering Curriculum infrastructure using Neo4j and vector databases.

## GraphRAG Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        GraphRAG Pipeline                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  1. Document Ingestion                                          │      │
│  │     ├── Extract entities (people, organizations, concepts)       │      │
│  │     ├── Extract relationships                                   │      │
│  │     └── Store in Neo4j                                         │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  2. Query Processing                                            │      │
│  │     ├── Extract entities from query                            │      │
│  │     ├── Graph traversal (Neo4j)                               │      │
│  │     ├── Vector search (Qdrant)                                │      │
│  │     └── Hybrid ranking                                         │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  3. Context Building                                           │      │
│  │     ├── Graph relationships                                   │      │
│  │     ├── Document chunks (vector search)                       │      │
│  │     └── Multi-hop reasoning paths                             │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  4. Generation (LLM)                                           │      │
│  │     ├── Structured prompt with graph context                  │      │
│  │     ├── Answer with citations                                 │      │
│  │     └── Update knowledge graph                                │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Implementation 1: Graph Construction

```python
# graph_construction.py
from neo4j import GraphDatabase
from typing import List, Dict, Any
import json

class KnowledgeGraphBuilder:
    """
    Build knowledge graph from documents
    """

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "your_secure_password_here"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def create_constraints(self):
        """Create graph constraints"""

        with self.driver.session() as session:
            # Node constraints
            session.run("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
            session.run("CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")

            # Indexes
            session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON e.name")
            session.run("CREATE INDEX document_title IF NOT EXISTS FOR (d:Document) ON d.title")

    def add_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
    ):
        """Add document with entities and relationships to graph"""

        with self.driver.session() as session:
            # Create document node
            session.run(
                """
                MERGE (d:Document {id: $doc_id})
                SET d.title = $title, d.content = $content
                """,
                doc_id=doc_id, title=title, content=content
            )

            # Create entities and link to document
            for entity in entities:
                session.run(
                    """
                    MATCH (d:Document {id: $doc_id})
                    MERGE (e:Entity {id: $entity_id})
                    SET e.name = $name, e.type = $type, e.description = $description
                    MERGE (d)-[:CONTAINS]->(e)
                    """,
                    doc_id=doc_id,
                    entity_id=entity["id"],
                    name=entity.get("name"),
                    type=entity.get("type"),
                    description=entity.get("description", "")
                )

            # Create relationships between entities
            for rel in relationships:
                session.run(
                    """
                    MATCH (source:Entity {id: $source_id})
                    MATCH (target:Entity {id: $target_id})
                    MERGE (source)-[r:RELATIONSHIP {type: $rel_type}]->(target)
                    SET r.description = $description
                    """,
                    source_id=rel["source"],
                    target_id=rel["target"],
                    rel_type=rel["type"],
                    description=rel.get("description", "")
                )

    def get_entity_context(self, entity_id: str, max_depth: int = 2) -> List[Dict]:
        """Get context for an entity via graph traversal"""

        # Parameters cannot set variable-length path bounds in Cypher —
        # *1..{max_depth} is a syntax error. Int-cast then interpolate:
        # int() rejects anything that isn't a number, closing the injection
        # door the f-string would otherwise open.
        hop_bound = max(1, int(max_depth))

        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (e:Entity {{id: $entity_id}})-[:RELATIONSHIP*1..{hop_bound}]-(related:Entity)
                RETURN DISTINCT related.id AS id, related.name AS name, related.type AS type
                LIMIT 20
                """,
                entity_id=entity_id
            )

            return [dict(record) for record in result]

    def close(self):
        """Close database connection"""
        self.driver.close()


# Example usage
def example_graph_construction():
    """Build knowledge graph from documents"""

    builder = KnowledgeGraphBuilder()
    builder.create_constraints()

    # Sample document
    doc = {
        "id": "doc_001",
        "title": "Introduction to Machine Learning",
        "content": "Machine learning is a subset of artificial intelligence...",
        "entities": [
            {"id": "ml", "name": "Machine Learning", "type": "Concept", "description": "AI subset"},
            {"id": "ai", "name": "Artificial Intelligence", "type": "Concept", "description": "Computer intelligence"},
            {"id": "neural_network", "name": "Neural Network", "type": "Algorithm", "description": "Learning algorithm"},
        ],
        "relationships": [
            {"source": "ml", "target": "ai", "type": "SUBSET_OF", "description": "ML is subset of AI"},
            {"source": "neural_network", "target": "ml", "type": "USED_IN", "description": "Neural networks in ML"},
        ]
    }

    builder.add_document(**doc)
    builder.close()
```

## Implementation 2: Hybrid Graph + Vector RAG

```python
# graph_rag.py
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class GraphRAGSystem:
    """
    GraphRAG: Combine Neo4j knowledge graph with Qdrant vector search
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "your_secure_password_here",
        qdrant_url: str = "http://localhost:6333",
        collection: str = "documents",
        embedder: str = "all-MiniLM-L6-v2",
    ):
        # Neo4j connection
        self.neo4j = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        # Qdrant connection
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection = collection

        # Embedder
        self.embedder = SentenceTransformer(embedder)

    def query(
        self,
        query: str,
        top_k: int = 5,
        graph_depth: int = 2,
        alpha: float = 0.5,  # 1=vector only, 0=graph only
    ) -> List[Dict]:
        """
        Hybrid graph + vector search

        Args:
            query: User query
            top_k: Number of results
            graph_depth: Graph traversal depth
            alpha: Vector weight in the blend (1 = vector only,
                0 = graph only)
        """

        # 1. Vector search (Qdrant). query_points replaced the removed
        # client.search() — qdrant-client deprecated .search() in 1.10 and
        # removed it since (see 6103/6201); results live in .points
        query_vector = self.embedder.encode(query).tolist()

        vector_results = self.qdrant.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=top_k * 2,
        ).points

        # 2. Graph search (Neo4j)
        # Extract entities from query
        query_entities = self._extract_entities(query)

        # Traverse graph to find related entities
        graph_context = self._graph_traversal(query_entities, depth=graph_depth)

        # 3. Combine and rank results
        combined_results = self._combine_results(
            vector_results,
            graph_context,
            alpha=alpha,
            top_k=top_k
        )

        return combined_results

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simplified)"""

        # In production, use NER model
        # For now, simple keyword extraction
        words = text.lower().split()
        entities = [w for w in words if len(w) > 3]  # Simple heuristic

        return entities[:5]

    def _graph_traversal(self, entities: List[str], depth: int = 2) -> Dict[str, float]:
        """
        Traverse the knowledge graph and score DOCUMENTS (not entities):
        the hybrid blend below joins on doc ids, so graph hits must be
        keyed by the same ids the vector search returns.
        """

        doc_scores = {}

        with self.neo4j.session() as session:
            for entity in entities:
                # Parameters can't set variable-length path bounds —
                # int-cast then interpolate (see get_entity_context)
                hop_bound = max(1, int(depth))
                result = session.run(
                    f"""
                    // Direct hit: the document containing a matched entity
                    MATCH (seed:Entity)<-[:CONTAINS]-(d:Document)
                    WHERE toLower(seed.name) CONTAINS toLower($entity)
                    RETURN d.id AS doc_id, 0 AS hop
                    UNION
                    // Neighborhood: documents of graph neighbors, nearest first
                    MATCH path = (seed:Entity)-[:RELATIONSHIP*1..{hop_bound}]-(neighbor:Entity)
                    WHERE toLower(seed.name) CONTAINS toLower($entity)
                    MATCH (d:Document)-[:CONTAINS]->(neighbor)
                    RETURN d.id AS doc_id, min(length(path)) AS hop
                    """,
                    entity=entity
                )

                for record in result:
                    score = 1.0 / (record["hop"] + 1)
                    doc_scores[record["doc_id"]] = max(
                        doc_scores.get(record["doc_id"], 0.0), score
                    )

        return doc_scores

    def _combine_results(
        self,
        vector_results: List,
        graph_context: Dict[str, float],
        alpha: float,
        top_k: int,
    ) -> List[Dict]:
        """Combine vector and graph results"""

        # Normalize scores
        vector_max = max([r.score for r in vector_results]) if vector_results else 1
        graph_max = max(graph_context.values()) if graph_context else 1

        # Create combined scores
        combined = {}

        # Add vector results
        for result in vector_results:
            doc_id = result.payload.get("doc_id")
            vector_score = result.score / vector_max

            if doc_id not in combined:
                combined[doc_id] = {
                    "doc_id": doc_id,
                    "content": result.payload.get("content"),
                    "vector_score": vector_score,
                    "graph_score": 0.0,
                }

        # Add graph scores — now keyed by doc id (see _graph_traversal),
        # so graph hits can actually meet their vector twins. A doc the
        # graph found but the vector store missed is seeded with a zero
        # vector score instead of being dropped
        for doc_id, score in graph_context.items():
            if doc_id not in combined:
                combined[doc_id] = {
                    "doc_id": doc_id,
                    "content": None,  # graph-only hit — no vector payload
                    "vector_score": 0.0,
                    "graph_score": 0.0,
                }
            combined[doc_id]["graph_score"] = score / graph_max

        # Calculate combined score
        for doc_id, result in combined.items():
            result["combined_score"] = (
                alpha * result["vector_score"] +
                (1 - alpha) * result["graph_score"]
            )

        # Sort by combined score
        results = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)

        return results[:top_k]

    def close(self):
        """Close connections"""
        self.neo4j.close()


# Usage
def test_graph_rag():
    """Test GraphRAG system"""

    rag = GraphRAGSystem()

    query = "How does neural network learning work?"

    results = rag.query(query, top_k=5, graph_depth=2, alpha=0.5)

    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Score: {result['combined_score']:.3f}")
        print(f"  Vector: {result['vector_score']:.3f}")
        print(f"  Graph: {result['graph_score']:.3f}")
        content = result.get("content") or "(graph-only document)"
        print(f"  Content: {content[:100]}...")

    rag.close()
```

## Implementation 3: Multi-Hop Reasoning

```python
# multi_hop_reasoning.py
from neo4j import GraphDatabase
from typing import List, Dict

class MultiHopReasoner:
    """
    Multi-hop reasoning over knowledge graph
    """

    def __init__(self, uri: str = "bolt://localhost:7687",
                 password: str = "your_secure_password_here"):
        self.driver = GraphDatabase.driver(uri, auth=("neo4j", password))

    def reasoning_paths(
        self,
        start_entity: str,
        end_entity: str,
        max_hops: int = 3,
    ) -> List[Dict]:
        """Find reasoning paths between entities"""

        # Parameters can't set variable-length path bounds — int-cast
        # then interpolate (see get_entity_context in Implementation 1)
        hop_bound = max(1, int(max_hops))

        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH path = (start:Entity {{name: $start}})-[:RELATIONSHIP*1..{hop_bound}]-(end:Entity {{name: $end}})
                RETURN [node in nodes(path) | node.name] AS path_names,
                       [rel in relationships(path) | type(rel)] AS path_types,
                       length(path) AS hops
                ORDER BY hops
                LIMIT 10
                """,
                start=start_entity,
                end=end_entity
            )

            paths = []
            for record in result:
                paths.append({
                    "path": record["path_names"],
                    "relationships": record["path_types"],
                    "hops": record["hops"]
                })

            return paths

    def explain_reasoning(self, path: Dict) -> str:
        """Generate explanation for reasoning path"""

        steps = []
        for i in range(len(path["relationships"])):
            source = path["path"][i]
            relation = path["relationships"][i]
            target = path["path"][i + 1]

            steps.append(f"{source} {relation} {target}")

        return " → ".join(steps)


# Usage
def test_multi_hop():
    """Test multi-hop reasoning"""

    reasoner = MultiHopReasoner()

    # Find paths between entities
    paths = reasoner.reasoning_paths("Machine Learning", "Neural Network", max_hops=3)

    print(f"Found {len(paths)} reasoning paths:\n")

    for i, path in enumerate(paths):
        print(f"Path {i+1} ({path['hops']} hops):")
        print(f"  {reasoner.explain_reasoning(path)}")
        print()
```

## Implementation 4: Entity Extraction with LLM

```python
# entity_extraction.py
import json

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict

class EntityExtractor:
    """
    Extract entities and relationships using LLM
    """

    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
        )

    def extract(self, text: str) -> Dict[str, List]:
        """Extract entities and relationships from text"""

        prompt = f"""Extract entities and relationships from the following text.

Text: {text}

Output JSON format:
{{
    "entities": [
        {{"id": "unique_id", "name": "entity name", "type": "PERSON|ORGANIZATION|CONCEPT", "description": "brief description"}}
    ],
    "relationships": [
        {{"source": "entity_id_1", "target": "entity_id_2", "type": "RELATIONSHIP_TYPE", "description": "description"}}
    ]
}}"""

        # Chat template turns the instruction into the format the instruct
        # model was trained on — raw generate() on the bare prompt would
        # answer an unformatted request
        inputs = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            return_tensors="pt",
            add_generation_prompt=True,
        ).to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=512,
                do_sample=False,
            )

        # Slice off the echoed prompt: generate() returns prompt plus
        # continuation, so decoding the whole tensor would re-feed the
        # instructions to the JSON parser
        response = self.tokenizer.decode(
            outputs[0][inputs.shape[1]:], skip_special_tokens=True
        )

        # Parse the first {...} block — a bare except would also swallow
        # KeyboardInterrupt and NameError silently
        try:
            return json.loads(response[response.index("{"):response.rindex("}") + 1])
        except (json.JSONDecodeError, ValueError):
            return {"entities": [], "relationships": []}


# Usage
def test_extraction():
    """Test entity extraction"""

    extractor = EntityExtractor()

    text = """
    Google DeepMind developed AlphaGo, an AI program that plays Go.
    It defeated Lee Sedol, a professional Go player, in 2016.
    AlphaGo was trained using reinforcement learning and neural networks.
    """

    result = extractor.extract(text)

    print("Entities:")
    for entity in result["entities"]:
        print(f"  - {entity['name']} ({entity['type']})")

    print("\nRelationships:")
    for rel in result["relationships"]:
        print(f"  - {rel['source']} → {rel['target']} ({rel['type']})")
```

## Implementation 5: Complete GraphRAG Pipeline

```python
# complete_graph_rag.py
import torch
from graph_construction import KnowledgeGraphBuilder
from graph_rag import GraphRAGSystem
from entity_extraction import EntityExtractor
from transformers import AutoModelForCausalLM, AutoTokenizer

class CompleteGraphRAG:
    """
    Complete GraphRAG pipeline
    """

    def __init__(self):
        self.graph_builder = KnowledgeGraphBuilder()
        self.graph_rag = GraphRAGSystem()
        self.entity_extractor = EntityExtractor()

        # LLM for generation
        self.tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
        self.llm = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.2",
            torch_dtype=torch.float16,
            device_map="auto",
        )

    def ingest_document(self, doc_id: str, title: str, content: str):
        """Ingest document into knowledge graph"""

        # Extract entities and relationships
        extraction = self.entity_extractor.extract(content)

        # Add to graph
        self.graph_builder.add_document(
            doc_id=doc_id,
            title=title,
            content=content,
            entities=extraction["entities"],
            relationships=extraction["relationships"],
        )

        print(f"Ingested document: {doc_id}")

    def query(self, query: str, top_k: int = 5) -> str:
        """Query with GraphRAG"""

        # Get relevant context
        results = self.graph_rag.query(query, top_k=top_k, graph_depth=2, alpha=0.5)

        # Build context
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(f"[Source {i+1}]")
            # Graph-only hits have no vector payload content
            context_parts.append(
                result.get("content")
                or f"(document {result['doc_id']} — reached via the graph, not in the vector store)"
            )

        context = "\n\n".join(context_parts)

        # Generate answer
        prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {query}"""

        # Chat template + prompt-slicing (see EntityExtractor.extract)
        inputs = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            return_tensors="pt",
            add_generation_prompt=True,
        ).to("cuda")

        with torch.no_grad():
            outputs = self.llm.generate(
                inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
            )

        # Slice off the echoed prompt — only the continuation is the answer
        answer = self.tokenizer.decode(
            outputs[0][inputs.shape[1]:], skip_special_tokens=True
        )

        return answer.strip()


# Usage
def test_complete_pipeline():
    """Test complete pipeline"""

    rag = CompleteGraphRAG()

    # Ingest documents
    rag.ingest_document(
        doc_id="doc_001",
        title="Introduction to GraphRAG",
        content="GraphRAG combines knowledge graphs with vector search..."
    )

    # Query
    answer = rag.query("What is GraphRAG?")

    print(f"Answer: {answer}")
```

## Production Note: Microsoft GraphRAG

The pipeline above teaches the mechanics. For corpus-scale deployments, Microsoft's [`graphrag`](https://github.com/microsoft/graphrag) package (v3.2.0, September 2026) industrializes the same ideas: LLM entity/relationship extraction at index time, Leiden community detection with pre-computed community summaries, and three query modes — **local search** (entity-neighborhood answers), **global search** (community-summary answers for corpus-wide, thematic questions), and **DRIFT search** (local expansion seeded by global priors). Reach for it when the corpus outgrows per-query traversal; keep the pipeline above when you need control over schema, storage, and the fusion step itself.

## Quick Start

```bash
# 1. Start Neo4j — calendar-versioned pin (see 6303). The
#    ${NEO4J_PASSWORD:?…} guard fails fast instead of shipping a default
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/"${NEO4J_PASSWORD:?export NEO4J_PASSWORD first}" \
  -v $PWD/neo4j/data:/data \
  neo4j:2026.09.0

# 2. Start Qdrant — pinned tag, aligned with qdrant-client 1.19 (see 6103)
docker run -d --name qdrant \
  -p 6333:6333 \
  -v $PWD/qdrant/data:/qdrant/storage \
  qdrant/qdrant:v1.19.1

# 3. Create the schema (Implementation 1)
python -c "from graph_construction import KnowledgeGraphBuilder; b = KnowledgeGraphBuilder(); b.create_constraints(); b.close(); print('schema ready')"

# 4. Run the full pipeline (Implementation 5 — needs the services above + a GPU)
python complete_graph_rag.py
```


---

## References

### Related ai-engineering-curriculum Documents

- [6301: Neo4j and Knowledge Graphs](../6301-Neo4j-and-Knowledge-Graphs.md)
- [6302: CAG - Context Augmented Generation and Long Context Architectures](../6302-CAG-Long-Context-Architectures.md)
- [6303: Neo4j Deployment Guide](6303-Neo4j-Deployment-Guide.md)
- [6201: Hybrid Search](../../6200-retrieval/6201-Hybrid-Search.md)
- [6401: Qdrant Setup](../../6400-vector-databases/6401-Qdrant-Setup.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**
- Experiment: **[EXP_6301: GraphRAG](../../../../../experiments/EXP_6301_GRAPHRAG.md)**
