# 6304: GraphRAG Implementation Guide

## Abstract
Complete implementation guide for GraphRAG (Knowledge Graph-enhanced Retrieval Augmented Generation) on AI Engineering Curriculum infrastructure using Neo4j and vector databases.

## GraphRAG Architecture

```
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

    def __init__(self, uri: str = "bolt://192.168.1.100:7687", user: str = "neo4j", password: str = "your_password"):
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

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = (e:Entity {id: $entity_id})-[:RELATED_TO*1..{max_depth}]-(related:Entity)
                RETURN DISTINCT related.id as id, related.name as name, related.type as type
                LIMIT 20
                """,
                entity_id=entity_id,
                max_depth=max_depth
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
        neo4j_uri: str = "bolt://192.168.1.100:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "your_password",
        qdrant_url: str = "http://192.168.1.100:6333",
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
        alpha: float = 0.5,  # 0=vector only, 1=graph only
    ) -> List[Dict]:
        """
        Hybrid graph + vector search

        Args:
            query: User query
            top_k: Number of results
            graph_depth: Graph traversal depth
            alpha: Weight between vector and graph (0-1)
        """

        # 1. Vector search (Qdrant)
        query_vector = self.embedder.encode(query).tolist()

        vector_results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k * 2,
        )

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
        """Traverse knowledge graph to find relevant context"""

        entity_scores = {}

        with self.neo4j.session() as session:
            for entity in entities:
                # Find matching entities
                result = session.run(
                    """
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($entity)
                    CALL {
                      MATCH (e)-[:RELATED_TO*1..{depth}]-(related:Entity)
                      RETURN related.id as id, related.name as name, count(*) as distance
                      } IN TRANSACTIONS
                    RETURN id, name, distance
                    """,
                    entity=entity,
                    depth=depth
                )

                for record in result:
                    entity_id = record["id"]
                    score = 1.0 / (record["distance"] + 1)
                    entity_scores[entity_id] = max(entity_scores.get(entity_id, 0), score)

        return entity_scores

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

            combined[doc_id]["vector_score"] = vector_score

        # Add graph scores
        for entity_id, score in graph_context.items():
            if entity_id in combined:
                combined[entity_id]["graph_score"] = score / graph_max

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
        print(f"  Content: {result['content'][:100]}...")

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

    def __init__(self, uri: str = "bolt://192.168.1.100:7687", password: str = "your_password"):
        self.driver = GraphDatabase.driver(uri, auth=("neo4j", password))

    def reasoning_paths(
        self,
        start_entity: str,
        end_entity: str,
        max_hops: int = 3,
    ) -> List[Dict]:
        """Find reasoning paths between entities"""

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = (start:Entity {name: $start})-[:RELATED_TO*1..{max_hops}]-(end:Entity {name: $end})
                RETURN [node in nodes(path) | node.name] as path_names,
                       [rel in relationships(path) | type(rel)] as path_types,
                       length(path) as hops
                ORDER BY hops
                LIMIT 10
                """,
                start=start_entity,
                end=end_entity,
                max_hops=max_hops
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
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict
import json

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
}}

Output:"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.1,
                do_sample=False,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Parse JSON
        try:
            data = json.loads(response.split("Output:")[-1].strip())
            return data
        except:
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
            context_parts.append(result["content"])

        context = "\n\n".join(context_parts)

        # Generate answer
        prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {query}

Answer:"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = self.llm.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
            )

        answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract answer
        answer = answer.split("Answer:")[-1].strip()

        return answer


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

## Quick Start

```bash
# 1. Start Neo4j
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -v $PWD/neo4j/data:/data \
  neo4j:5.15-community

# 2. Start Qdrant
docker run -d --name qdrant \
  -p 6333:6333 \
  -v $PWD/qdrant/data:/qdrant/storage \
  qdrant/qdrant:latest

# 3. Run GraphRAG
python graph_rag.py

# 4. Test
python -c "from complete_graph_rag import CompleteGraphRAG; rag = CompleteGraphRAG(); print(rag.query('What is AI?'))"
```


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [6301: Neo4j and Knowledge Graphs](../6301-Neo4j-and-Knowledge-Graphs.md)
- [6302: CAG Long Context Architectures](../6302-CAG-Long-Context-Architectures.md)
- [6303: Neo4j Deployment Guide](6303-Neo4j-Deployment-Guide.md)
- [6201: Hybrid Search](../../6200-retrieval/6201-Hybrid-Search.md)
- [EXP_6301: Neo4j Knowledge Graph](../../../../../experiments/EXP_6303_NEO4J.md)
