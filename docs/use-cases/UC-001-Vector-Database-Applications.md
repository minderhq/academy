---
Document ID: UC-001
Title: "UC-001: Vector Database Practical Use Cases"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Related: [6101, 6401]
Tags: ['use-case', 'vector-db', 'rag']
---

# UC-001: Vector Database Practical Use Cases

## Overview

This document provides comprehensive practical use cases for vector databases, explaining when and why to use them over traditional databases, with real-world implementation examples.

---

## Part 1: When to Use Vector Databases

### Decision Matrix

| Scenario | Traditional DB | Vector DB | Hybrid Approach |
|----------|---------------|-----------|-----------------|
| **Exact Match Queries** | ✅ Best Choice | ❌ Not Suitable | ❌ Overkill |
| **Semantic Search** | ❌ Poor Performance | ✅ Best Choice | ⚠️ Consider |
| **Metadata Filtering** | ✅ Excellent | ⚠️ Limited | ✅ Best Choice |
| **Similarity Matching** | ❌ Slow/Complex | ✅ Best Choice | ⚠️ Consider |
| **Transaction Integrity** | ✅ ACID Support | ⚠️ Limited | ✅ Best Choice |
| **Million+ Scale** | ⚠️ Performance Issues | ✅ Optimized | ✅ Best Choice |

---

## Part 2: Real-World Use Cases

### Use Case 1: E-Commerce Product Recommendation

**Business Problem:**
Users search for "summer wedding guest dress" but exact keyword matching fails to find relevant products described as "lightweight floral outfit for ceremonies."

**Vector Database Solution:**

```python
# Product Embedding Pipeline
from sentence_transformers import SentenceTransformer
import qdrant_client

class ProductSearch:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = qdrant_client.QdrantClient(url="localhost:6333")

    def index_products(self, products):
        """Convert product descriptions to embeddings"""
        for product in products:
            # Combine text features
            text = f"{product['name']} {product['description']} " \
                   f"{' '.join(product['tags'])}"

            # Create embedding
            vector = self.model.encode(text).tolist()

            # Store with metadata
            self.client.upsert(
                collection_name="products",
                points=[{
                    "id": product['id'],
                    "vector": vector,
                    "payload": {
                        "name": product['name'],
                        "price": product['price'],
                        "category": product['category'],
                        "in_stock": product['in_stock']
                    }
                }]
            )

    def semantic_search(self, query, filters=None):
        """Find semantically similar products"""
        query_vector = self.model.encode(query).tolist()

        search_result = self.client.query_points(
            collection_name="products",
            query=query_vector,
            query_filter=self._build_filter(filters),
            limit=10,
            score_threshold=0.7  # Only return relevant matches
        ).points

        return [
            {
                "product": hit.payload,
                "relevance": hit.score
            }
            for hit in search_result
        ]

# Real Usage
search = ProductSearch()

# User query
results = search.semantic_search(
    query="summer wedding guest dress under $100",
    filters={"price": {"lt": 100}, "in_stock": True}
)

# Results include:
# - "Lightweight Floral Midi Dress" ($89)
# - "Ceremony-Ready Chiffon Outfit" ($95)
# Even though exact words don't match!
```

**Business Impact:**
- 40% increase in conversion rate
- 60% reduction in "no results" searches
- 25% increase in average order value

**When NOT to Use:**
- Small catalog (<1000 products) → Postgres FULLTEXT is sufficient
- Pure exact match needs (SKU lookup) → Traditional DB is better

---

### Use Case 2: Document Intelligence for Legal Firms

**Business Problem:**
Lawyers need to find precedents and clauses across millions of legal documents, but keyword search misses semantically similar legal concepts expressed differently.

**Vector Database Solution:**

```python
class LegalDocumentSearch:
    """
    Find similar legal clauses, precedents, and arguments
    across millions of documents
    """

    def __init__(self):
        self.model = SentenceTransformer('nlpaueb/legal-bert-base-uncased')
        self.chunk_size = 512  # Token chunks
        self.overlap = 50      # Overlapping tokens

    def index_legal_document(self, doc_path):
        """Chunk and embed legal documents"""

        # Read document
        with open(doc_path, 'r') as f:
            text = f.read()

        # Split into chunks with overlap
        chunks = self._chunk_text(text, self.chunk_size, self.overlap)

        # Create embeddings for each chunk
        embeddings = self.model.encode(chunks)

        # Store in Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append({
                "id": f"{doc_path}_{i}",
                "vector": embedding.tolist(),
                "payload": {
                    "text": chunk,
                    "source_doc": doc_path,
                    "chunk_index": i,
                    "doc_type": self._detect_doc_type(chunk),
                    "jurisdiction": self._detect_jurisdiction(chunk),
                    "date": self._extract_date(doc_path)
                }
            })

        self.client.upsert(
            collection_name="legal_docs",
            points=points
        )

    def find_similar_clauses(self, clause_text, jurisdiction=None):
        """Find legally similar clauses"""

        query_vector = self.model.encode(clause_text)

        filters = {"jurisdiction": jurisdiction} if jurisdiction else None

        results = self.client.query_points(
            collection_name="legal_docs",
            query=query_vector.tolist(),
            query_filter=self._build_filter(filters),
            limit=20,
            score_threshold=0.75
        ).points

        return self._rank_by_relevance(results)

    def find_precedents(self, case_facts):
        """Find similar cases based on facts"""

        # Encode case facts
        facts_vector = self.model.encode(case_facts)

        # Search for similar fact patterns
        results = self.client.query_points(
            collection_name="legal_docs",
            query=facts_vector.tolist(),
            query_filter={
                "must": [
                    {"key": "doc_type", "match": {"value": "case_law"}}
                ]
            },
            limit=10
        ).points

        return results
```

**Real-World Scenario:**

```python
# Lawyer's query
query = """
Force Majeure clause covering pandemics and government
restrictions preventing performance of obligations
"""

# Results include clauses with:
# - "Act of God including epidemics"
# - "Circumstances beyond reasonable control"
# - "Government action prohibiting performance"
# Even though wording differs completely!
```

**Business Impact:**
- 80% reduction in research time
- 40% improvement in case outcome prediction
- Discovery of precedents missed by keyword search

**When NOT to Use:**
- Small firm (<10,000 documents)
- Pure citation lookup (case number search)

---

### Use Case 3: Semantic Code Search for Development

**Business Problem:**
Developers waste time finding code that solves a problem they have, but can't describe it with exact function names.

**Vector Database Solution:**

```python
import ast
import os
class CodeSearch:
    """
    Search code by functionality, not by name
    """

    def __init__(self):
        # Code-specific embedding model
        self.model = SentenceTransformer('microsoft/codebert-base')
        self.client = qdrant_client.QdrantClient(url="localhost:6333")

    def index_repository(self, repo_path):
        """Index all code in repository"""

        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py'):
                    self._index_python_file(os.path.join(root, file))

    def _index_python_file(self, file_path):
        """Index Python file with function-level granularity"""

        with open(file_path, 'r') as f:
            code = f.read()

        # Extract functions
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function code
                func_code = ast.get_source_segment(code, node)

                # Create searchable text
                searchable_text = f"""
                Function: {node.name}
                Docstring: {ast.get_docstring(node) or ''}
                Code: {func_code}
                """

                # Create embedding
                embedding = self.model.encode(searchable_text)

                # Store
                self.client.upsert(
                    collection_name="code",
                    points=[{
                        "id": f"{file_path}:{node.name}:{node.lineno}",
                        "vector": embedding.tolist(),
                        "payload": {
                            "function_name": node.name,
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "code": func_code,
                            "docstring": ast.get_docstring(node),
                            "repo": repo_path
                        }
                    }]
                )

    def search_by_intent(self, intent_query):
        """Search code by what you want to do"""

        query_vector = self.model.encode(intent_query)

        results = self.client.query_points(
            collection_name="code",
            query=query_vector.tolist(),
            limit=10,
            score_threshold=0.65
        ).points

        return [
            {
                "function": hit.payload["function_name"],
                "file": hit.payload["file_path"],
                "line": hit.payload["line_number"],
                "code": hit.payload["code"],
                "relevance": hit.score
            }
            for hit in results
        ]
```

**Real-World Usage:**

```python
# Developer query (English, not code!)
query = "parse JSON from HTTP response with error handling"

# Results find:
import requests

def fetch_json_data(url):
    """Get and parse JSON from API endpoint"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

# Even though function name doesn't contain "json" or "parse"!
```

**Business Impact:**
- 50% reduction in code duplication
- 30% faster onboarding for new developers
- Discovery of existing solutions vs reinventing

---

### Use Case 4: Customer Support Semantic Routing

**Business Problem:**
Customer support tickets need to be routed to the right department, but keyword matching fails to understand the actual issue.

**Vector Database Solution:**

```python
class SupportRouter:
    """
    Route support tickets to correct department
    using semantic understanding
    """

    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.client = qdrant_client.QdrantClient(url="localhost:6333")

        # Define department expertise
        self.departments = {
            "billing": ["payment", "refund", "invoice", "charge"],
            "technical": ["error", "crash", "bug", "not working"],
            "shipping": ["delivery", "tracking", "package", "shipped"],
            "account": ["login", "password", "account", "profile"]
        }

    def build_department_vectors(self):
        """Create semantic profiles for departments"""

        for dept, keywords in self.departments.items():
            # Create semantic profile
            profile = f"{dept} department handles: {', '.join(keywords)}"
            vector = self.model.encode(profile)

            self.client.upsert(
                collection_name="departments",
                points=[{
                    "id": dept,
                    "vector": vector.tolist(),
                    "payload": {"department": dept}
                }]
            )

    def route_ticket(self, ticket_text):
        """Route ticket to appropriate department"""

        ticket_vector = self.model.encode(ticket_text)

        # Find closest department
        results = self.client.query_points(
            collection_name="departments",
            query=ticket_vector.tolist(),
            limit=1
        ).points

        return results[0].payload["department"]
```

**Real-World Examples:**

```python
# Ticket: "I never got my order"
# Routes to: SHIPPING (not billing!)

# Ticket: "Money taken but no confirmation"
# Routes to: BILLING (understands payment intent)

# Ticket: "Can't access my account"
# Routes to: ACCOUNT (not technical!)

# Ticket: "App keeps crashing when I click checkout"
# Routes to: TECHNICAL
```

---

### Use Case 5: Plagiarism Detection

**Business Problem:**
Detect plagiarized content that has been paraphrased to avoid exact match detection.

```python
class PlagiarismDetector:
    """
    Find paraphrased plagiarism using semantic similarity
    """

    def __init__(self):
        self.model = SentenceTransformer('stsb-roberta-large')
        self.client = qdrant_client.QdrantClient(url="localhost:6333")

    def index_reference_corpus(self, documents):
        """Index all reference documents"""

        for doc in documents:
            # Split into sentences
            sentences = sent_tokenize(doc['text'])

            for i, sentence in enumerate(sentences):
                vector = self.model.encode(sentence)

                self.client.upsert(
                    collection_name="reference",
                    points=[{
                        "id": f"{doc['id']}_{i}",
                        "vector": vector.tolist(),
                        "payload": {
                            "text": sentence,
                            "source": doc['source'],
                            "doc_id": doc['id']
                        }
                    }]
                )

    def check_plagiarism(self, submission):
        """Check submission for paraphrased plagiarism"""

        sentences = sent_tokenize(submission)
        plagiarized_passages = []

        for i, sentence in enumerate(sentences):
            query_vector = self.model.encode(sentence)

            # Find similar sentences
            results = self.client.query_points(
                collection_name="reference",
                query=query_vector.tolist(),
                limit=3,
                score_threshold=0.85  # High similarity threshold
            ).points

            if results:
                plagiarized_passages.append({
                    "sentence": sentence,
                    "matches": [
                        {
                            "text": hit.payload["text"],
                            "source": hit.payload["source"],
                            "similarity": hit.score
                        }
                        for hit in results
                    ]
                })

        return plagiarized_passages
```

**Real-World Detection:**

```python
# Original: "The quick brown fox jumps over the lazy dog"
# Submission: "A fast brown fox leaps across the sleepy dog"
# Detected: 92% similarity → FLAGGED

# Original: "Machine learning is a subset of artificial intelligence"
# Submission: "ML is a type of AI"
# Detected: 89% similarity → FLAGGED
```

---

## Part 3: Industry-Specific Applications

### Healthcare

| Use Case | Vector DB Benefit | Example |
|----------|------------------|---------|
| **Medical Literature Search** | Find studies even with different terminology | "Heart attack" finds "myocardial infarction" studies |
| **Similar Case Retrieval** | Find medically similar patient histories | Search by symptoms, not exact diagnosis codes |
| **Drug Interaction Detection** | Semantic matching of drug descriptions | Find interactions even with different brand names |

### Finance

| Use Case | Vector DB Benefit | Example |
|----------|------------------|---------|
| **Fraud Detection** | Pattern matching across transaction descriptions | Find "unusual activity" even with different wording |
| **Research Document Analysis** | Semantic search across financial reports | "Revenue growth" finds "top line expansion" |
| **Compliance Checking** | Find similar regulatory issues | Match regulatory violations with different phrasing |

### Manufacturing

| Use Case | Vector DB Benefit | Example |
|----------|------------------|---------|
| **Technical Manual Search** | Find procedures by intent | "Fix leaking pump" finds correct procedure |
| **Parts Catalog** | Find similar parts | Find replacements by function, not exact match |
| **Failure Analysis** | Find similar failure patterns | Match symptoms to root causes |

---

## Part 4: Implementation Guidelines

### When Vector DB is Overkill

```python
# DON'T use Vector DB for:
exact_user_lookup = users.find_by_id(123)  # Use traditional DB

# DO use Vector DB for:
similar_users = find_users_with_similar_preferences(user_123)
```

### Hybrid Approach (Best of Both)

```python
class HybridSearch:
    """
    Combine exact match (Postgres) + semantic (Qdrant)
    """

    def search_products(self, query, category=None, price_range=None):
        # Step 1: Filter by exact metadata (Postgres)
        filtered_ids = postgres.query(
            "SELECT id FROM products WHERE category = %s "
            "AND price BETWEEN %s AND %s",
            (category, price_range[0], price_range[1])
        )

        # Step 2: Semantic search within filtered set (Qdrant)
        semantic_results = qdrant.query_points(
            collection_name="products",
            query=embed(query),
            query_filter={"must": [{"id": filtered_ids}]},
            limit=10
        ).points

        return semantic_results
```

### Performance Considerations

| Data Size | Recommended Approach |
|-----------|---------------------|
| < 10K vectors | In-memory (NumPy/FAISS) |
| 10K - 1M | Vector DB (Qdrant/Weaviate) |
| 1M - 100M | Vector DB + Sharding |
| > 100M | Distributed Vector DB (Pinecone Cloud) |

### Cost Comparison

| Solution | Setup Cost | Monthly Cost | Best For |
|----------|-----------|--------------|----------|
| **Postgres + pgvector** | $0 (existing) | $0 | < 100K vectors |
| **Qdrant Self-Hosted** | $0 (HomeLab) | $0 | < 10M vectors |
| **Pinecone Starter** | $0 | $70 | 1M-5M vectors |
| **Pinecone Production** | $0 | $500+ | 10M+ vectors |

---

## Part 5: Quick Start Templates

### Template 1: Basic Semantic Search

```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Initialize
model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(url="localhost:6333")

# Create collection
client.create_collection(
    collection_name="demo",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Index documents
documents = [
    {"id": 1, "text": "Machine learning is awesome"},
    {"id": 2, "text": "Deep learning networks"},
    {"id": 3, "text": "Natural language processing"}
]

client.upsert(
    collection_name="demo",
    points=[
        PointStruct(
            id=doc["id"],
            vector=model.encode(doc["text"]).tolist(),
            payload={"text": doc["text"]}
        )
        for doc in documents
    ]
)

# Search
query = "AI and neural networks"
results = client.query_points(
    collection_name="demo",
    query=model.encode(query).tolist(),
    limit=3
).points

for hit in results:
    print(f"{hit.payload['text']}: {hit.score:.3f}")
```

---

## Decision Tree: Should I Use a Vector Database?

```text
START
  │
  ├─ Do you need to find SIMILAR items?
  │   ├─ NO → Use Traditional DB
  │   └─ YES → Continue
  │
  ├─ Is your data TEXT/IMAGE/AUDIO?
  │   ├─ NO → Use Traditional DB
  │   └─ YES → Continue
  │
  ├─ Do users search with CONCEPTS not exact terms?
  │   ├─ NO → Use Full-Text Search (Elasticsearch)
  │   └─ YES → Continue
  │
  ├─ How many items?
  │   ├─ < 10K → Use FAISS/NumPy (In-memory)
  │   ├─ 10K - 10M → Use Vector DB (Qdrant/Weaviate)
  │   └─ > 10M → Use Pinecloud/Managed Service
  │
  └─ END
```

---

## Next Steps

- **[UC-002: RAG System Applications](./UC-002-RAG-Applications.md)**
