---
Document ID: 6301
Title: "6301: Neo4j and Knowledge Graphs for Multi-Hop Reasoning"
Phase: 6
Module: 6300
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'context', 'graphrag', 'neo4j', 'knowledge-graphs']
---

# 6301: Neo4j and Knowledge Graphs for Multi-Hop Reasoning

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Knowledge Graph Fundamentals](#knowledge-graph-fundamentals)
- [Neo4j Setup](#neo4j-setup)
- [Cypher Query Language](#cypher-query-language)
- [Building Knowledge Graphs](#building-knowledge-graphs)
- [GraphRAG: Retrieval from Knowledge Graphs](#graphrag-retrieval-from-knowledge-graphs)
- [Advanced Graph Techniques](#advanced-graph-techniques)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Model a knowledge graph as typed nodes and relationships — build the AI-corpus example (Model/Company nodes, CREATED and COMPETES_WITH edges) with `KnowledgeGraph.add_node` / `add_edge`, and explain why a 2-hop question is a join chain in tables but a cheap traversal in a graph
- Stand up Neo4j in Docker — run `neo4j:2026.09.0` (calendar versioning; 5.26 is the LTS maintenance line) with Bolt 7687 + HTTP 7474, `NEO4J_AUTH`, and the APOC plugin, then execute parameterized Cypher through the Python driver session
- Read and write Cypher — distinguish CREATE (always adds) from MERGE (match-or-create) from MATCH (read-only), bind values with `$parameters`, and trace the two-hop pattern `(c:Company)-[:CREATED]->(m:Model)-[:COMPETES_WITH]->(comp:Model)`
- Build a KG from text — spaCy NER for entities plus an NLI zero-shot classifier (`facebook/bart-large-mnli` — an embedding model like bge cannot back this pipeline) for relations, and MERGE idempotent `:Entity`/`:Document` nodes with `MENTIONED_IN` edges
- Retrieve through the graph — walk `graph_retrieval`'s expansion (query entities → their documents → 1-hop neighbors' documents), rank documents by traversal frequency, and generate parameterized multi-hop Cypher with `build_cypher_query`
- Embed the graph — convert Neo4j to NetworkX, run node2vec walks, and query the embedding space (`model.wv.most_similar`) for entities close to a seed node

---

## Abstract
Knowledge graphs represent information as entities and relationships, enabling multi-hop reasoning that traditional RAG cannot handle. Neo4j is a graph database optimized for such queries.

## Knowledge Graph Fundamentals

### Graph Structure
```text
Traditional database: Tables and rows
Knowledge graph: Nodes and relationships

Example: "Elon Musk owns Tesla"
  Node: Elon Musk (Person)
  Node: Tesla (Company)
  Relationship: OWNERSHIP → (Elon)-[:OWNS]->(Tesla)

Multi-hop reasoning:
  "Who owns companies that compete with Ford?"

  (Person)-[:OWNS]->(Company)-[:COMPETES_WITH]->(Ford)
  ↑ Find companies that compete with Ford
  ↑ Find owners of those companies
```

### Graph Data Model
```python
# Knowledge graph representation
class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}      # id -> {type, properties}
        self.edges = []      # (from, to, relationship, properties)

    def add_node(self, node_id, node_type, properties):
        """Add entity node"""
        self.nodes[node_id] = {
            'type': node_type,
            'properties': properties
        }

    def add_edge(self, from_id, to_id, relation, properties=None):
        """Add relationship edge"""
        self.edges.append({
            'from': from_id,
            'to': to_id,
            'relation': relation,
            'properties': properties or {}
        })

# Example: AI knowledge graph
kg = KnowledgeGraph()

kg.add_node("llama", "Model", {"creator": "Meta", "params": "7B"})
kg.add_node("mistral", "Model", {"creator": "Mistral AI", "params": "7B"})
kg.add_node("meta", "Company", {"founded": 2004})
kg.add_node("mistral_ai", "Company", {"founded": 2023})

kg.add_edge("meta", "llama", "CREATED")
kg.add_edge("mistral_ai", "mistral", "CREATED")
kg.add_edge("llama", "mistral", "COMPETES_WITH")
```

## Neo4j Setup

### Installation with Docker
```bash
# Install Neo4j using Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -v /srv/neo4j/data:/data \
  -v /srv/neo4j/logs:/logs \
  neo4j:2026.09.0

# Or using Docker Compose
cat > docker-compose.yml << EOF
services:
  neo4j:
    image: neo4j:2026.09.0
    container_name: neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/your_password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - ./neo4j/data:/data
      - ./neo4j/logs:/logs
      - ./neo4j/plugins:/plugins
EOF

docker compose up -d
```

### Python Driver
```python
from neo4j import GraphDatabase

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        """
        Execute Cypher query
        """
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

# Usage
neo4j = Neo4jConnection("bolt://192.168.1.100:7687", "neo4j", "password")
```

## Cypher Query Language

### Basic Cypher
```cypher
-- Create nodes
CREATE (meta:Company {name: 'Meta', founded: 2004})
CREATE (llama:Model {name: 'Llama-3.1', params: '8B'})

-- Create relationship
MATCH (meta:Company {name: 'Meta'})
MATCH (llama:Model {name: 'Llama-3.1'})
CREATE (meta)-[:CREATED]->(llama)

-- Query: Find all models
MATCH (m:Model)
RETURN m

-- Query: Find companies and their models
MATCH (c:Company)-[:CREATED]->(m:Model)
RETURN c.name AS company, m.name AS model

-- Query: Multi-hop reasoning
MATCH (c:Company)-[:CREATED]->(m:Model)-[:COMPETES_WITH]->(comp:Model)
RETURN c.name AS company, comp.name AS competitor_model
```

### Multi-Hop Queries
```python
def find_competitors(neo4j, company_name):
    """
    Find companies whose models compete with the given company's models
    (2-hop: CREATED → COMPETES_WITH ← CREATED)
    """
    query = """
    MATCH (c1:Company {name: $company})-[:CREATED]->(m1:Model)
    MATCH (m1)-[:COMPETES_WITH]->(m2:Model)<-[:CREATED]-(c2:Company)
    RETURN DISTINCT c2.name AS competitor_company
    """

    result = neo4j.query(query, {"company": company_name})
    return [record["competitor_company"] for record in result]

# Example: Find companies competing with Meta's competitors
competitors = find_competitors(neo4j, "Meta")
print(competitors)  # Might include Google, Mistral AI, etc.
```

## Building Knowledge Graphs

### From Text to Graph
```python
import spacy
from transformers import pipeline

class TextToGraph:
    """
    Extract entities and relationships from text
    """
    def __init__(self, neo4j_conn):
        self.neo4j = neo4j_conn
        self.nlp = spacy.load("en_core_web_sm")
        # zero-shot-classification is an NLI task — it needs an entailment
        # head (MNLI-trained). BAAI/bge-base-en-v1.5 is an EMBEDDING model
        # and cannot back this pipeline; bge belongs in vector search.
        self.relation_extractor = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )

    def extract_entities(self, text):
        """
        Extract named entities from text
        """
        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })

        return entities

    def extract_relationships(self, text, entities):
        """
        Extract relationships between entities
        """
        relationships = []

        for i, ent1 in enumerate(entities):
            for ent2 in entities[i+1:]:
                # Get text between entities
                text_between = text[ent1['end']:ent2['start']].strip()

                if not text_between:
                    continue

                # Classify relationship
                relation = self.relation_extractor(
                    f"{ent1['text']} {text_between} {ent2['text']}",
                    candidate_labels=["OWNS", "CREATED", "COMPETES_WITH", "PARTNERS_WITH", "NONE"]
                )

                if relation['labels'][0] != "NONE":
                    relationships.append({
                        'from': ent1['text'],
                        'to': ent2['text'],
                        'relation': relation['labels'][0],
                        'confidence': relation['scores'][0]
                    })

        return relationships

    def build_graph(self, text):
        """
        Extract and build knowledge graph from text
        """
        entities = self.extract_entities(text)
        relationships = self.extract_relationships(text, entities)

        # Create nodes
        for ent in entities:
            query = """
            MERGE (e:Entity {name: $name})
            ON CREATE SET e.type = $type
            """
            self.neo4j.query(query, {
                'name': ent['text'],
                'type': ent['label']
            })

        # Create relationships
        for rel in relationships:
            query = """
            MATCH (e1:Entity {name: $from})
            MATCH (e2:Entity {name: $to})
            MERGE (e1)-[r:RELATION {type: $relation}]->(e2)
            ON CREATE SET r.confidence = $confidence
            """
            self.neo4j.query(query, rel)

# Usage
text_to_graph = TextToGraph(neo4j)

text = """
Meta created Llama-3.1, an 8 billion parameter language model.
Llama-3.1 competes with Mistral, which was created by Mistral AI.
Google created Bard, which also competes with Llama-3.1.
"""

text_to_graph.build_graph(text)
```

### From Documents to Graph
```python
def build_rag_graph(documents, neo4j_conn):
    """
    Build knowledge graph from document corpus
    """
    text_to_graph = TextToGraph(neo4j_conn)

    for doc_id, doc in enumerate(documents):
        # Extract entities and relationships
        text_to_graph.build_graph(doc)

        # Link entities to source document
        entities = text_to_graph.extract_entities(doc)

        for ent in entities:
            query = """
            MATCH (e:Entity {name: $name})
            MERGE (d:Document {id: $doc_id})
            MERGE (e)-[:MENTIONED_IN]->(d)
            """
            neo4j_conn.query(query, {
                'name': ent['text'],
                'doc_id': doc_id
            })
```

## GraphRAG: Retrieval from Knowledge Graphs

### Graph-Based Retrieval
```python
def graph_retrieval(neo4j, query_entities, k=10):
    """
    Retrieve relevant documents using knowledge graph

    Approach: expand through graph relationships

    query_entities: entity names extracted from the question BEFORE this
    call (spaCy NER as in TextToGraph above, or an LLM — 6304 does that)
    """

    # 2. For each entity, find related documents
    doc_scores = {}

    for entity in query_entities:
        # Find documents mentioning entity or related entities
        cypher = """
        MATCH (e:Entity {name: $entity})
        OPTIONAL MATCH (e)-[:MENTIONED_IN]->(d:Document)
        OPTIONAL MATCH (e)-[:RELATION]-(e2:Entity)-[:MENTIONED_IN]->(d2:Document)
        RETURN DISTINCT d.id AS doc_id, d2.id AS doc_id_2
        """

        results = neo4j.query(cypher, {"entity": entity})

        for record in results:
            for doc_key in ["doc_id", "doc_id_2"]:
                if record[doc_key] is not None:
                    doc_id = record[doc_key]
                    doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1

    # 3. Sort by frequency (relevance proxy)
    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    # 4. Return top k
    return [doc_id for doc_id, score in sorted_docs[:k]]

# Example — entities come from an extractor, not the raw question string:
query_entities = ["Meta", "Llama-3.1"]
relevant_docs = graph_retrieval(neo4j, query_entities, k=5)
```

### Multi-Hop Question Answering
```python
def build_cypher_query(entities, relations, max_hops=3):
    """
    Build a parameterized Cypher query for multi-hop reasoning.

    entities:  entity names extracted from the question (first = anchor)
    relations: relation `type` property values, one per hop

    Returns (cypher, params). Values are bound with $parameters, never
    interpolated into the string — an entity name containing quotes or
    Cypher metacharacters cannot inject the query.
    """
    hops = min(len(relations), max_hops)

    # Anchor node + one MATCH per hop:
    # (e1)-[:RELATION]->(e2)-[:RELATION]->(e3)...
    cypher = "MATCH (e1:Entity {name: $e0})"
    for i in range(hops):
        cypher += f"\nMATCH (e{i + 1})-[:RELATION {{type: $r{i}}}]->(e{i + 2})"

    # Return every node along the path (nodes are e1..e(hops+1))
    cypher += "\nRETURN " + ", ".join(f"e{i}" for i in range(1, hops + 2))

    params = {"e0": entities[0]}
    params.update({f"r{i}": rel for i, rel in enumerate(relations[:hops])})
    return cypher, params

def multi_hop_qa(neo4j, entities, relations, max_hops=3):
    """
    Answer multi-hop questions. Entity/relation extraction happens BEFORE
    this call (spaCy NER as in TextToGraph above, or an LLM — 6304 does
    exactly that); this runs the parameterized query and returns entity
    paths as tuples.
    """
    cypher, params = build_cypher_query(entities, relations, max_hops=max_hops)
    rows = neo4j.query(cypher, params)
    depth = min(len(relations), max_hops) + 1
    return [tuple(row[f"e{i}"] for i in range(1, depth + 1)) for row in rows]

# Example — build the 1-hop query for "Which models compete with Ford?":
cypher, params = build_cypher_query(["Ford"], ["COMPETES_WITH"])
print(cypher)
# MATCH (e1:Entity {name: $e0})
# MATCH (e1)-[:RELATION {type: $r0}]->(e2)
# RETURN e1, e2
print(params)
# {'e0': 'Ford', 'r0': 'COMPETES_WITH'}
```

## Advanced Graph Techniques

### Graph Embeddings
```python
# Use graph embeddings for semantic search

from node2vec import Node2Vec
import networkx as nx

def create_networkx_graph(neo4j):
    """
    Convert Neo4j graph to NetworkX
    """
    # Get all nodes and edges
    nodes_query = "MATCH (n) RETURN n.name AS id, labels(n) AS labels"
    edges_query = "MATCH (a)-[r]->(b) RETURN a.name AS source, b.name AS target, type(r) as relation"

    nodes = neo4j.query(nodes_query)
    edges = neo4j.query(edges_query)

    # Create NetworkX graph
    G = nx.DiGraph()

    for node in nodes:
        G.add_node(node['id'], labels=node['labels'])

    for edge in edges:
        G.add_edge(edge['source'], edge['target'], relation=edge['relation'])

    return G

def train_node2vec(G):
    """
    Train node embeddings using Node2Vec
    """
    node2vec = Node2Vec(
        G,
        dimensions=128,
        walk_length=30,
        num_walks=200,
        workers=4
    )

    model = node2vec.fit(window=10, min_count=1, batch_words=4)

    return model

# Usage — G comes from create_networkx_graph(neo4j) above
model = train_node2vec(G)

model.wv['Meta']  # Embedding for Meta node
model.wv.most_similar('Meta', topn=10)  # Similar entities
```


---

## Summary

Knowledge graphs represent information as entities and relationships, which is exactly the shape multi-hop reasoning needs and flat vector chunks cannot provide. This lesson walked graph fundamentals against relational tables, Cypher query patterns, and the question classes where Neo4j beats a vector store - chain-of-relationship queries that would need many retrieval rounds in RAG. The rule it leaves: vectors answer 'what is similar', graphs answer 'what connects' - and the second question is the one traditional RAG cannot touch.

## References

### Related Minder Academy Documents

- [6201: Hybrid Search](../6200-retrieval/6201-Hybrid-Search.md)
- [6302: CAG - Context Augmented Generation and Long Context Architectures](6302-CAG-Long-Context-Architectures.md)
- [7301: Collaborative Tasking](../../phase7-agentic/7300-orchestration/7301-Orchestration.md)

---

## Next Steps

- Continue with: **[6401: Qdrant Setup](./../6400-vector-databases/6401-Qdrant-Setup.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_6303: Neo4j](../../../../experiments/EXP_6303_NEO4J.md)**
