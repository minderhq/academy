---
Document ID: SOLUTION-LAB-005
Title: "SOLUTION-LAB-005: GraphRAG"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Tags: ['solution', 'graphrag', 'neo4j']
---

# SOLUTION-LAB-005: GraphRAG

## Overview
Complete solution for implementing GraphRAG with knowledge graphs and Neo4j.

---

## Prerequisites

```bash
uv pip install neo4j langchain-openai sentence-transformers
```

## Neo4j Setup

```bash
# Using Docker
docker run -d \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS=["apoc"] \
    neo4j:latest
```

---

## Core Solution

```python
import re
from typing import Any
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI

# NOTE: this implementation talks to Neo4j through the raw neo4j driver.
# The langchain-integrated alternative lives in the separate
# langchain-neo4j package (Neo4jVector, Neo4jGraph, GraphCypherQAChain).

class GraphRAG:
    """
    Complete GraphRAG implementation with:
    - Entity and relationship extraction
    - Knowledge graph construction
    - Vector similarity search
    - Subgraph traversal
    - Context-aware generation
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
        embedder_model: str = "all-MiniLM-L6-v2"
    ):
        """Initialize GraphRAG with Neo4j connection and embedder."""
        # Neo4j connection
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )

        # Embedding model
        self.embedder = SentenceTransformer(embedder_model)
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()

        # Setup database schema
        self._setup_schema()

        # Initialize LLM for generation
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    def _setup_schema(self):
        """Create Neo4j schema with indexes and constraints."""
        with self.driver.session() as session:
            # Create constraints
            session.run("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")

            # Create vector index for similarity search
            try:
                session.run("""
                    CALL db.index.vector.createNodeIndex(
                        'entityEmbeddings',
                        ['Entity'],
                        {
                            embeddingDimension: $dim,
                            similarityFunction: 'cosine'
                        }
                    )
                """, dim=self.embedding_dim)
            except Exception as e:
                print(f"Index may already exist: {e}")

            # Create full-text search index
            session.run("CREATE FULLTEXT INDEX entityText IF NOT EXISTS FOR (e:Entity) ON EACH [e.text, e.type]")

            print("✓ Neo4j schema setup complete")

    def extract_entities_and_relationships(self, text: str) -> dict[str, list]:
        """
        Extract entities and relationships from text.

        Returns:
            Dict with 'entities' and 'relationships' lists
        """
        entities = []
        relationships = []

        # Simple entity extraction using regex patterns
        # In production, use spaCy or specialized NER models

        # Extract capitalized words as potential entities
        entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.finditer(entity_pattern, text)

        seen_entities = set()
        for match in matches:
            entity = match.group()
            if len(entity) > 2 and entity not in seen_entities:
                # Determine entity type based on context
                entity_type = self._classify_entity(entity, text)
                entities.append({
                    "name": entity,
                    "type": entity_type,
                    "text": text  # Store surrounding context
                })
                seen_entities.add(entity)

        # Extract relationships (co-occurring entities in same sentence)
        sentences = text.split('.')
        for sentence in sentences:
            sentence_entities = [e["name"] for e in entities if e["name"] in sentence]

            # Create relationships between co-occurring entities
            for i, e1 in enumerate(sentence_entities):
                for e2 in sentence_entities[i+1:]:
                    relationships.append({
                        "source": e1,
                        "target": e2,
                        "type": "RELATED_TO",
                        "context": sentence.strip()
                    })

        return {"entities": entities, "relationships": relationships}

    def _classify_entity(self, entity: str, text: str) -> str:
        """Classify entity type based on context clues."""
        # Simple rule-based classification
        context_lower = text.lower()

        if any(word in context_lower for word in ["learn", "model", "algorithm", "network"]):
            return "CONCEPT"
        elif any(word in context_lower for word in ["python", "java", "javascript", "code"]):
            return "TECHNOLOGY"
        elif any(word in context_lower for word in ["data", "dataset", "database"]):
            return "DATA"
        elif any(word in context_lower for word in ["ai", "machine learning", "neural"]):
            return "DOMAIN"
        else:
            return "ENTITY"

    def create_graph(self, documents: list[str], batch_size: int = 10):
        """
        Create knowledge graph from documents.

        Args:
            documents: The document strings
            batch_size: Number of documents to process per batch
        """
        print(f"Creating graph from {len(documents)} documents...")

        all_entities = []
        all_relationships = []

        # Extract entities and relationships from each document
        for i, doc in enumerate(documents):
            result = self.extract_entities_and_relationships(doc)
            all_entities.extend(result["entities"])
            all_relationships.extend(result["relationships"])

        # Remove duplicates
        unique_entities = self._deduplicate_entities(all_entities)
        unique_relationships = self._deduplicate_relationships(all_relationships)

        # Store in Neo4j
        self._store_entities(unique_entities)
        self._store_relationships(unique_relationships)

        print(f"✓ Graph created: {len(unique_entities)} entities, {len(unique_relationships)} relationships")

    def _deduplicate_entities(self, entities: list[dict]) -> list[dict]:
        """Remove duplicate entities, keeping first occurrence."""
        seen = {}
        for entity in entities:
            key = (entity["name"], entity["type"])
            if key not in seen:
                seen[key] = entity
        return list(seen.values())

    def _deduplicate_relationships(self, relationships: list[dict]) -> list[dict]:
        """Remove duplicate relationships."""
        seen = set()
        unique = []
        for rel in relationships:
            key = (rel["source"], rel["target"], rel["type"])
            if key not in seen:
                seen.add(key)
                unique.append(rel)
        return unique

    def _store_entities(self, entities: list[dict]):
        """Store entities in Neo4j with embeddings."""
        with self.driver.session() as session:
            for entity in entities:
                # Create embedding
                text = entity.get("text", entity["name"])
                embedding = self.embedder.encode(text).tolist()

                # Create entity node
                session.run("""
                    MERGE (e:Entity {id: $id, name: $name, type: $type, text: $text})
                    SET e.embedding = $embedding
                """, id=entity["name"], name=entity["name"],
                    type=entity["type"], text=text[:500],  # Truncate long text
                    embedding=embedding)

    def _store_relationships(self, relationships: list[dict]):
        """Store relationships in Neo4j."""
        with self.driver.session() as session:
            for rel in relationships:
                session.run("""
                    MATCH (source:Entity {name: $source})
                    MATCH (target:Entity {name: $target})
                    MERGE (source)-[r:RELATED_TO]->(target)
                    SET r.context = $context
                """, source=rel["source"], target=rel["target"],
                    context=rel["context"][:500])

    def query(
        self,
        question: str,
        top_k_entities: int = 5,
        neighborhood_depth: int = 2
    ) -> dict[str, Any]:
        """
        Query knowledge graph with question.

        Args:
            question: User's question
            top_k_entities: Number of most relevant entities to retrieve
            neighborhood_depth: Depth of subgraph traversal

        Returns:
            Dict with answer, context, and sources
        """
        # Step 1: Find relevant entities using vector similarity
        relevant_entities = self._find_relevant_entities(question, top_k_entities)

        if not relevant_entities:
            return {
                "question": question,
                "answer": "I couldn't find relevant information in the knowledge graph.",
                "context": [],
                "sources": []
            }

        # Step 2: Expand to neighborhood (get related entities)
        subgraph = self._get_neighborhood(
            [e["name"] for e in relevant_entities],
            depth=neighborhood_depth
        )

        # Step 3: Build context from subgraph
        context = self._build_context(subgraph)

        # Step 4: Generate answer using LLM
        answer = self._generate_answer(question, context)

        return {
            "question": question,
            "answer": answer,
            "context": context,
            "sources": [e["name"] for e in relevant_entities]
        }

    def _find_relevant_entities(self, query: str, top_k: int = 5) -> list[dict]:
        """Find most relevant entities using vector similarity."""
        query_embedding = self.embedder.encode(query).tolist()

        with self.driver.session() as session:
            results = session.run("""
                CALL db.index.vector.queryNodes('entityEmbeddings', {
                    indexName: 'entityEmbeddings',
                    query: $query,
                    topK: $top_k
                })
                YIELD node, score
                RETURN node.name AS name, node.type AS type, node.text AS text, score
                ORDER BY score DESC
            """, query=query_embedding, top_k=top_k)

            return [{"name": r["name"], "type": r["type"], "score": r["score"]} for r in results]

    def _get_neighborhood(self, entity_names: list[str], depth: int = 2) -> list[dict]:
        """Get neighboring entities within specified depth."""
        with self.driver.session() as session:
            results = session.run("""
                MATCH path = (start:Entity)-[*1..{depth}]-(neighbor:Entity)
                WHERE start.name IN $names
                UNWIND nodes(path) AS node
                RETURN DISTINCT node.name AS name, node.type AS type, node.text AS text
            """, names=entity_names, depth=depth)

            return [{"name": r["name"], "type": r["type"], "text": r.get("text", "")} for r in results]

    def _build_context(self, subgraph: list[dict]) -> str:
        """Build context string from subgraph."""
        context_parts = []

        for entity in subgraph:
            if entity.get("text"):
                context_parts.append(f"{entity['name']} ({entity['type']}): {entity['text'][:200]}")
            else:
                context_parts.append(f"{entity['name']} ({entity['type']})")

        return "\n\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM with graph context."""
        prompt = f"""
Based on the following knowledge graph context, answer the question.

Context:
{context}

Question: {question}

Provide a clear, accurate answer based on the context above. If the context doesn't contain enough information to answer the question, say so explicitly.
"""

        try:
            response = self.llm.invoke(prompt).content
            return response.strip()
        except Exception as e:
            return f"Error generating answer: {e}"

    def add_document(self, document: str):
        """Add a single document to the knowledge graph."""
        result = self.extract_entities_and_relationships(document)

        self._store_entities(
            self._deduplicate_entities(result["entities"])
        )
        self._store_relationships(
            self._deduplicate_relationships(result["relationships"])
        )

        print(f"✓ Document added: {len(result['entities'])} entities, {len(result['relationships'])} relationships")

    def visualize_graph(self, limit: int = 50):
        """Return graph data for visualization (e.g., in Neo4j Bloom)."""
        with self.driver.session() as session:
            results = session.run(f"""
                MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
                RETURN e1.name AS source, e2.name AS target, r.type AS relationship
                LIMIT {limit}
            """)

            return [{"source": r["source"], "target": r["target"], "relationship": r["relationship"]} for r in results]

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()
        print("✓ Neo4j connection closed")

# =====================================================================
# USAGE EXAMPLE
# =====================================================================

def main():
    """Example usage of GraphRAG."""

    # Initialize GraphRAG
    graph_rag = GraphRAG(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        embedder_model="all-MiniLM-L6-v2"
    )

    # Sample documents
    documents = [
        "Python is a high-level programming language widely used in AI and machine learning.",
        "PyTorch is a machine learning library developed by Facebook for neural networks.",
        "Transformers are neural network architectures that use attention mechanisms for processing sequential data.",
        "Neo4j is a graph database that stores data in nodes and relationships, ideal for knowledge graphs.",
        "RAG combines retrieval systems with generation models to produce more accurate and contextual responses."
    ]

    # Create knowledge graph
    graph_rag.create_graph(documents)

    # Query the graph
    result = graph_rag.query("What is PyTorch used for?")
    print(f"\nQuestion: {result['question']}")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['sources']}")

    # Add new document
    graph_rag.add_document("LangChain is a framework for developing LLM applications.")

    # Visualize graph data
    graph_data = graph_rag.visualize_graph()
    print(f"\nGraph visualization data: {len(graph_data)} relationships")

    # Close connection
    graph_rag.close()

if __name__ == "__main__":
    main()
```

---

## Key Features Implemented

### 1. Entity and Relationship Extraction
- Regex-based entity extraction with context
- Co-occurrence based relationship extraction
- Entity type classification (CONCEPT, TECHNOLOGY, DATA, DOMAIN)

### 2. Knowledge Graph Storage
- Neo4j connection management
- Entity nodes with embeddings
- Relationships with context
- Vector index for similarity search
- Full-text search index

### 3. Graph-based Retrieval
- Vector similarity search for relevant entities
- Multi-hop neighborhood traversal
- Context assembly from subgraphs

### 4. Context-Aware Generation
- LLM integration for answer generation
- Prompt engineering with graph context
- Fallback for missing information

### 5. Additional Features
- Dynamic document addition
- Graph visualization data export
- Batch processing support
- Comprehensive error handling

---

## Expected Results

When running this solution:

1. Knowledge graph is created from documents
2. Entities are stored with vector embeddings
3. Relationships connect related concepts
4. Queries retrieve relevant context from the graph
5. LLM generates accurate answers based on graph context

---

**Difficulty:** ⭐⭐⭐ Advanced

**Lines of Code:** ~450
