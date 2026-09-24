---
Document ID: 6301
Title: Neo4j and Knowledge Graphs for Multi-Hop Reasoning
Phase: 6
Module: 6300
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'context', 'graphrag', 'neo4j', 'knowledge-graphs']
---

# 6301: Neo4j and Knowledge Graphs for Multi-Hop Reasoning

## Abstract
Knowledge graphs represent information as entities and relationships, enabling multi-hop reasoning that traditional RAG cannot handle. Neo4j is a graph database optimized for such queries.

## Knowledge Graph Fundamentals

### Graph Structure
```
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
  neo4j:latest

# Or using Docker Compose
cat > docker-compose.yml << EOF
version: '3'
services:
  neo4j:
    image: neo4j:latest
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

docker-compose up -d
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
CREATE (llama:Model {name: 'Llama-2', params: '7B'})

-- Create relationship
MATCH (meta:Company {name: 'Meta'})
MATCH (llama:Model {name: 'Llama-2'})
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
    Find companies that compete with given company's competitors
    (2-hop reasoning)
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
        self.relation_extractor = pipeline(
            "zero-shot-classification",
            model="BAAI/bge-base-en-v1.5"
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
            MERGE (e1)-[r:RELATION]->(e2)
            ON CREATE SET r.type = $relation, r.confidence = $confidence
            """
            self.neo4j.query(query, rel)

# Usage
text_to_graph = TextToGraph(neo4j)

text = """
Meta created Llama-2, a 7 billion parameter language model.
Llama-2 competes with Mistral, which was created by Mistral AI.
Google created Bard, which also competes with Llama-2.
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
def graph_retrieval(neo4j, query, k=10):
    """
    Retrieve relevant documents using knowledge graph

    Approach: Expand query through graph relationships
    """
    # 1. Extract entities from query
    entities = extract_query_entities(query)

    # 2. For each entity, find related documents
    doc_scores = {}

    for entity in entities:
        # Find documents mentioning entity or related entities
        cypher = """
        MATCH (e:Entity {name: $entity})
        OPTIONAL MATCH (e)-[:MENTIONED_IN]->(d:Document)
        OPTIONAL MATCH (e)-[r:RELATION]-(e2:Entity)-[:MENTIONED_IN]->(d2:Document)
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

# Example
query = "What companies compete with Meta's models?"
relevant_docs = graph_retrieval(neo4j, query, k=5)
```

### Multi-Hop Question Answering
```python
def multi_hop_qa(neo4j, question):
    """
    Answer complex questions requiring multi-hop reasoning
    """
    # Parse question to identify entities and relations
    entities = extract_entities(question)
    relations = extract_relations(question)

    # Build Cypher query dynamically
    query = build_cypher_query(entities, relations)

    # Execute
    results = neo4j.query(query)

    # Format answer
    answer = format_answer(results)

    return answer

def build_cypher_query(entities, relations, max_hops=3):
    """
    Build Cypher query for multi-hop reasoning
    """
    # Match starting entity
    cypher = f"MATCH (e1:Entity {{name: '{entities[0]}'}})"

    # Add hops
    for i in range(1, min(len(relations)+1, max_hops)):
        cypher += f"""
        MATCH (e1)"
        for j in range(i):
            cypher += f"-[:RELATION]->(e{j+2}"

        # Add optional relationship filter
        if i-1 < len(relations):
            cypher += f" {{RELATION.type = '{relations[i-1]}'}}"

    cypher += ")\n"

    # Return results
    cypher += "RETURN e1"
    for i in range(2, max_hops+2):
        cypher += f", e{i}"

    return cypher

# Example
# Question: "Who owns companies that compete with Ford?"
# Entities: [Ford]
# Relations: [COMPETES_WITH, OWNS]
# Result: 2-hop query
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

# Use embeddings for similarity search
model.wv['Meta']  # Embedding for Meta node
model.wv.most_similar('Meta', topn=10)  # Similar entities
```


---

## Next Steps

- Continue with: **[6401: Qdrant Setup](./../6400-vector-databases/6401-Qdrant-Setup.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [6201: Hybrid Search](../6200-retrieval/6201-Hybrid-Search.md)
- [6302: CAG Long Context](./6302-CAG-Long-Context-Architectures.md)
- [7002: Collaborative Tasking](../../phase7-agentic/7300-orchestration/7301-Orchestration.md)

**Experiment Template:** `experiments/EXP_6303_NEO4J.md"
