---
Document ID: EXP_6303
Title: "EXP_6303: Neo4j Knowledge Graph Experiments"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# EXP_6303: Neo4j Knowledge Graph Experiments

## Overview
Practical experiments for Neo4j knowledge graph implementation on any Docker-capable Linux host, NAS, or VPS for Minder Academy.

## Experiment 1: Neo4j Deployment (Docker)

### Objective
Deploy Neo4j on a self-hosted Docker host.

### Deployment
```bash
# SSH into your host (or run locally)
ssh user@your-host

# Create directory
mkdir -p /srv/neo4j
cd /srv/neo4j

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3"

services:
  neo4j:
    image: neo4j:5.15-community
    container_name: neo4j
    ports:
      - 7474:7474  # HTTP
      - 7687:7687  # Bolt
    volumes:
      - ./data:/data
      - ./logs:/logs
      - ./plugins:/plugins
      - ./conf:/conf
    environment:
      - NEO4J_AUTH=neo4j/your_password
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_max__size=2G
      - NEO4J_dbms_memory_pagecache_size=1G
    restart: unless-stopped
EOF

# Start Neo4j
docker-compose up -d

# Verify
curl http://localhost:7474
```

---

## Experiment 2: Knowledge Graph Construction

### Objective
Build a knowledge graph from documents.

### Python Script
```python
# neo4j_kg_builder.py
from neo4j import GraphDatabase
import os

class KnowledgeGraphBuilder:
    """Build knowledge graph in Neo4j"""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="your_password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        """Create uniqueness constraints"""
        queries = [
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)
        print("✓ Constraints created")

    def add_document(self, doc_id: str, title: str, content: str):
        """Add document node"""
        with self.driver.session() as session:
            session.run(
                "CREATE (d:Document {id: $id, title: $title, content: $content})",
                id=doc_id, title=title, content=content
            )

    def add_entity(self, entity_id: str, entity_type: str, name: str):
        """Add entity node"""
        with self.driver.session() as session:
            session.run(
                "MERGE (e:Entity {id: $id}) SET e.type = $type, e.name = $name",
                id=entity_id, type=entity_type, name=name
            )

    def add_relation(self, doc_id: str, entity_id: str, relation_type: str):
        """Add relationship between document and entity"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (d:Document {id: $doc_id})
                MATCH (e:Entity {id: $entity_id})
                MERGE (d)-[r:MENTIONS]->(e)
                SET r.type = $relation_type
                """,
                doc_id=doc_id, entity_id=entity_id, relation_type=relation_type
            )

    def add_entity_relation(self, entity1_id: str, entity2_id: str, relation: str):
        """Add relationship between entities"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (e1:Entity {id: $id1})
                MATCH (e2:Entity {id: $id2})
                MERGE (e1)-[r:RELATES_TO]->(e2)
                SET r.relation = $relation
                """,
                id1=entity1_id, id2=entity2_id, relation=relation
            )


# Test the builder
def test_kg_builder():
    """Test knowledge graph builder"""
    kg = KnowledgeGraphBuilder()

    try:
        # Setup
        kg.create_constraints()

        # Add documents
        kg.add_document("doc1", "AI Basics", "Artificial intelligence is transforming healthcare.")
        kg.add_document("doc2", "ML Overview", "Machine learning is a subset of AI.")

        # Add entities
        kg.add_entity("ent1", "Technology", "Artificial Intelligence")
        kg.add_entity("ent2", "Field", "Healthcare")
        kg.add_entity("ent3", "Technology", "Machine Learning")

        # Add relations
        kg.add_relation("doc1", "ent1", "mentions")
        kg.add_relation("doc1", "ent2", "applies_to")
        kg.add_relation("doc2", "ent3", "mentions")
        kg.add_entity_relation("ent3", "ent1", "subset_of")

        print("✓ Knowledge graph populated")

    finally:
        kg.close()


if __name__ == "__main__":
    test_kg_builder()
```

---

## Experiment 3: GraphRAG Query Patterns

### Multi-Hop Reasoning
```python
# graph_rag_queries.py
from neo4j import GraphDatabase

class GraphRAG:
    """Graph-based RAG queries"""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="your_password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def find_related_documents(self, entity_name: str, max_hops: int = 2):
        """Find documents related to entity (multi-hop)"""
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH path = (d:Document)-[*1..{max_hops}]->(e:Entity {{name: $name}})
                RETURN DISTINCT d.title, d.content, [n in nodes(path) | n.name] as path
                LIMIT 10
                """,
                name=entity_name
            )
            return list(result)

    def find_connections(self, entity1: str, entity2: str):
        """Find paths between two entities"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = shortestPath(
                    (e1:Entity {name: $name1})-[*]-(e2:Entity {name: $name2})
                )
                RETURN [n in nodes(path) | n.name] as connection,
                       [r in relationships(path) | type(r)] as relations
                """,
                name1=entity1, name2=entity2
            )
            return list(result)

    def contextual_search(self, query_entities: list):
        """Find documents containing multiple related entities"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:Document)
                WHERE ALL(e IN $entities WHERE (d)-[:MENTIONS]->(:Entity {name: e}))
                RETURN d.title, d.content
                ORDER BY d.title
                LIMIT 5
                """,
                entities=query_entities
            )
            return list(result)


# Test queries
def test_graph_rag():
    """Test GraphRAG queries"""
    rag = GraphRAG()

    try:
        print("Related Documents for 'Artificial Intelligence':")
        docs = rag.find_related_documents("Artificial Intelligence", max_hops=2)
        for doc in docs:
            print(f"  - {doc['d.title']}")

        print("\nConnection between 'Machine Learning' and 'Healthcare':")
        connections = rag.find_connections("Machine Learning", "Healthcare")
        for conn in connections:
            print(f"  Path: {' -> '.join(conn['connection'])}")

    finally:
        rag.driver.close()
```

---

## Experiment 4: RAG with Knowledge Graph

### Vector + Graph Hybrid
```python
# hybrid_rag.py
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
import torch
from sentence_transformers import SentenceTransformer

class HybridRAG:
    """Combine vector search with knowledge graph"""

    def __init__(self):
        # Vector store
        self.qdrant = QdrantClient(url="http://localhost:6333")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        # Knowledge graph
        self.neo4j = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "your_password")
        )

    def search(self, query: str, alpha: float = 0.5):
        """
        Hybrid search combining vector and graph

        alpha: 0 = pure graph, 1 = pure vector
        """
        # Vector search
        query_vector = self.embedder.encode(query).tolist()
        vector_results = self.qdrant.search(
            collection_name="documents",
            query_vector=query_vector,
            limit=10
        )

        # Graph search (extract entities from query)
        entities = self.extract_entities(query)
        graph_results = []
        if entities:
            with self.neo4j.session() as session:
                for entity in entities[:3]:
                    result = session.run(
                        """
                        MATCH (d:Document)-[:MENTIONS]->(:Entity {name: $name})
                        RETURN d.id, d.content
                        LIMIT 5
                        """,
                        name=entity
                    )
                    graph_results.extend(list(result))

        # Combine scores
        combined = self.combine_results(vector_results, graph_results, alpha)
        return combined

    def extract_entities(self, text: str) -> list:
        """Simple entity extraction (use NER model in production)"""
        # Placeholder - use spaCy or similar in production
        words = text.split()
        return [w for w in words if w[0].isupper() and len(w) > 3]

    def combine_results(self, vector_results, graph_results, alpha):
        """Combine vector and graph results"""
        scores = {}

        # Vector scores
        for i, result in enumerate(vector_results):
            doc_id = result.payload.get("doc_id", str(i))
            scores[doc_id] = scores.get(doc_id, 0) + alpha * (1 - i/10)

        # Graph scores
        for result in graph_results:
            doc_id = result["d.id"]
            scores[doc_id] = scores.get(doc_id, 0) + (1 - alpha)

        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results


# Test hybrid search
def test_hybrid_rag():
    """Test hybrid RAG"""
    rag = HybridRAG()

    query = "How does machine learning apply to healthcare?"
    results = rag.search(query, alpha=0.5)

    print(f"Query: {query}")
    print("\nTop Results:")
    for doc_id, score in results[:5]:
        print(f"  {doc_id}: {score:.3f}")
```

---

## Expected Performance (entry-level 4-core host)

| Operation | Expected Latency | Notes |
|-----------|------------------|-------|
| Create entity | ~10-50ms | Depends on network |
| Simple query | ~50-200ms | Single hop |
| Multi-hop query | ~200-500ms | 2-3 hops |
| Hybrid search | ~300-800ms | Vector + Graph |

---

## Experiment Checklist

- [ ] Neo4j deployment with Docker
- [ ] Knowledge graph builder test
- [ ] Entity extraction from documents
- [ ] Multi-hop reasoning queries
- [ ] GraphRAG pattern tests
- [ ] Hybrid vector + graph search
- [ ] Performance benchmarking
- [ ] Schema design optimization
- [ ] APOC procedures usage
- [ ] Graph visualization

---

## Related Documentation
- [6301: Neo4j and Knowledge Graphs](../docs/phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md)
- [6201: Hybrid Search](../docs/phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)
- [6101: HNSW Indexing](../docs/phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md)
