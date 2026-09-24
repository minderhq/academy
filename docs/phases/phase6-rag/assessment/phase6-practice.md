# Phase 6: RAG & Data Nexus Practice

## Hands-On Exercises

### Exercise 1: Implement Vector Search from Scratch

```python
import numpy as np
from typing import List, Tuple

class VectorSearch:
    """Simple vector search implementation"""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.vectors = []
        self.metadata = []

    def add(self, vector: np.ndarray, meta: dict):
        """Add vector to index"""
        if vector.shape[0] != self.dim:
            raise ValueError(f"Expected dim {self.dim}, got {vector.shape[0]}")
        self.vectors.append(vector)
        self.metadata.append(meta)

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def search(self, query: np.ndarray, k: int = 5) -> List[Tuple[dict, float]]:
        """Search for similar vectors"""
        if not self.vectors:
            return []

        # Calculate similarities
        similarities = []
        for i, vector in enumerate(self.vectors):
            sim = self.cosine_similarity(query, vector)
            similarities.append((self.metadata[i], sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:k]


def test_vector_search():
    print("=== Vector Search Test ===")

    # Create index
    index = VectorSearch(dim=384)

    # Add sample vectors
    for i in range(100):
        vector = np.random.randn(384)
        vector = vector / np.linalg.norm(vector)  # Normalize
        index.add(vector, {"id": i, "text": f"Document {i}"})

    print(f"Indexed {len(index.vectors)} vectors")

    # Search
    query = np.random.randn(384)
    query = query / np.linalg.norm(query)

    results = index.search(query, k=5)

    print(f"Top 5 results:")
    for meta, score in results:
        print(f"  {meta['text']}: {score:.4f}")

    print("✅ Vector search working!\n")


if __name__ == "__main__":
    test_vector_search()
```

### Exercise 2: Implement BM25 Search

```python
from collections import defaultdict
import math
from typing import List, Dict

class BM25:
    """BM25 keyword search implementation"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = []
        self.idf = {}
        self.doc_lens = []

    def index(self, documents: List[str]):
        """Index documents"""
        # Tokenize and count
        self.doc_freqs = []
        self.doc_lens = []

        # Build document frequencies
        for doc in documents:
            tokens = doc.lower().split()
            self.doc_lens.append(len(tokens))

            freq = defaultdict(int)
            for token in tokens:
                freq[token] += 1

            self.doc_freqs.append(dict(freq))

        # Calculate IDF
        N = len(documents)
        all_tokens = set()
        for freq in self.doc_freqs:
            all_tokens.update(freq.keys())

        for token in all_tokens:
            df = sum(1 for freq in self.doc_freqs if token in freq)
            self.idf[token] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_idx: int) -> float:
        """Calculate BM25 score for query-document pair"""
        query_tokens = query.lower().split()
        doc_freqs = self.doc_freqs[doc_idx]
        doc_len = self.doc_lens[doc_idx]
        avg_doc_len = sum(self.doc_lens) / len(self.doc_lens)

        score = 0
        for token in query_tokens:
            if token in doc_freqs:
                tf = doc_freqs[token]
                idf = self.idf.get(token, 0)

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len)

                score += idf * (numerator / denominator)

        return score

    def search(self, query: str, k: int = 5) -> List[tuple]:
        """Search for relevant documents"""
        scores = [(i, self.score(query, i)) for i in range(len(self.doc_freqs))]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


def test_bm25():
    print("=== BM25 Search Test ===")

    # Sample documents
    documents = [
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses neural networks with multiple layers",
        "Natural language processing deals with text and speech",
        "Computer vision enables machines to understand images",
        "Reinforcement learning learns through trial and error"
    ]

    # Index documents
    bm25 = BM25(k1=1.5, b=0.75)
    bm25.index(documents)

    print(f"Indexed {len(documents)} documents")

    # Search
    query = "neural networks"
    results = bm25.search(query, k=3)

    print(f"\nQuery: '{query}'")
    print(f"Top 3 results:")
    for doc_idx, score in results:
        print(f"  [{doc_idx}] {documents[doc_idx]}: {score:.4f}")

    print("✅ BM25 working!\n")


if __name__ == "__main__":
    test_bm25()
```

### Exercise 3: Hybrid Search with Rank Fusion

```python
from typing import List, Tuple
import numpy as np

class HybridSearch:
    """Hybrid search combining vector and keyword search"""

    def __init__(self, alpha: float = 0.5):
        """
        Args:
            alpha: Weight for vector search (0-1)
                   1-alpha is weight for keyword search
        """
        self.alpha = alpha

    def reciprocal_rank_fusion(
        self,
        results_list: List[List[Tuple[int, float]]],
        k: int = 60
    ) -> List[Tuple[int, float]]:
        """
        Reciprocal Rank Fusion (RRF) algorithm

        Combines multiple ranked lists by:
        score(d) = sum(1 / (k + rank(d)))

        Args:
            results_list: List of ranked result lists
            k: Constant to prevent division by small ranks

        Returns:
            Fused ranked list
        """
        fused_scores = defaultdict(float)

        for results in results_list:
            for rank, (doc_id, _) in enumerate(results):
                fused_scores[doc_id] += 1.0 / (k + rank + 1)

        # Sort by fused score
        sorted_results = sorted(
            fused_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results

    def weighted_score_fusion(
        self,
        vector_results: List[Tuple[int, float]],
        keyword_results: List[Tuple[int, float]]
    ) -> List[Tuple[int, float]]:
        """
        Weighted score fusion

        Combines scores using weighted average:
        score(d) = alpha * vector_score + (1-alpha) * keyword_score

        Args:
            vector_results: List of (doc_id, score) from vector search
            keyword_results: List of (doc_id, score) from keyword search

        Returns:
            Fused ranked list
        """
        # Normalize scores to 0-1
        def normalize(scores):
            if not scores:
                return []
            max_score = max(s for _, s in scores)
            min_score = min(s for _, s in scores)
            range_val = max_score - min_score if max_score != min_score else 1
            return [(doc_id, (score - min_score) / range_val)
                    for doc_id, score in scores]

        vector_norm = normalize(vector_results)
        keyword_norm = normalize(keyword_results)

        # Combine scores
        combined_scores = defaultdict(float)

        for doc_id, score in vector_norm:
            combined_scores[doc_id] += self.alpha * score

        for doc_id, score in keyword_norm:
            combined_scores[doc_id] += (1 - self.alpha) * score

        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results


def test_hybrid_search():
    print("=== Hybrid Search Test ===")

    # Sample results from vector and keyword search
    vector_results = [
        (1, 0.95), (3, 0.88), (5, 0.82), (2, 0.75), (8, 0.70)
    ]

    keyword_results = [
        (5, 0.92), (1, 0.85), (7, 0.78), (3, 0.72), (9, 0.68)
    ]

    print(f"Vector search results: {[r[0] for r in vector_results]}")
    print(f"Keyword search results: {[r[0] for r in keyword_results]}")

    # Test weighted score fusion
    hybrid = HybridSearch(alpha=0.5)

    fused = hybrid.weighted_score_fusion(vector_results, keyword_results)

    print(f"\nFused results (α=0.5):")
    for doc_id, score in fused[:5]:
        print(f"  Doc {doc_id}: {score:.4f}")

    # Test different alpha values
    print(f"\nAlpha comparison:")
    for alpha in [0.2, 0.5, 0.8]:
        h = HybridSearch(alpha=alpha)
        fused = h.weighted_score_fusion(vector_results, keyword_results)
        top_docs = [str(doc_id) for doc_id, _ in fused[:3]]
        print(f"  α={alpha}: Top 3 = [{', '.join(top_docs)}]")

    print("✅ Hybrid search working!\n")


if __name__ == "__main__":
    test_hybrid_search()
```

### Exercise 4: Qdrant Vector Database Operations

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

class QdrantVectorStore:
    """Qdrant vector database operations"""

    def __init__(self, location=":memory:", collection_name="documents"):
        self.client = QdrantClient(location=location)
        self.collection_name = collection_name

    def create_collection(self, vector_size=384):
        """Create a new collection"""
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        print(f"Created collection: {self.collection_name}")

    def insert_points(self, points_data):
        """Insert points into collection"""
        points = [
            PointStruct(
                id=i,
                vector=data["vector"].tolist(),
                payload=data.get("payload", {})
            )
            for i, data in enumerate(points_data)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Inserted {len(points)} points")

    def search(self, query_vector, limit=5, score_threshold=None):
        """Search for similar vectors"""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit,
            score_threshold=score_threshold
        )
        return results

    def filter_search(self, query_vector, filter_condition, limit=5):
        """Search with metadata filtering"""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            query_filter=filter_condition,
            limit=limit
        )
        return results

    def delete_collection(self):
        """Delete the collection"""
        self.client.delete_collection(self.collection_name)
        print(f"Deleted collection: {self.collection_name}")


def test_qdrant():
    print("=== Qdrant Vector Store Test ===")

    # Create store
    store = QdrantVectorStore(location=":memory:", collection_name="test_docs")

    # Create collection
    store.create_collection(vector_size=384)

    # Insert sample data
    points_data = []
    documents = [
        "AI and machine learning are transforming technology",
        "Deep learning neural networks process complex patterns",
        "Natural language understanding is improving rapidly",
        "Computer vision recognizes objects in images",
        "Reinforcement learning optimizes decision making"
    ]

    for i, doc in enumerate(documents):
        # Simulate embedding with random vector
        vector = np.random.randn(384)
        vector = vector / np.linalg.norm(vector)

        points_data.append({
            "vector": vector,
            "payload": {"text": doc, "category": "AI" if i < 3 else "ML"}
        })

    store.insert_points(points_data)

    # Search
    query = np.random.randn(384)
    query = query / np.linalg.norm(query)

    results = store.search(query, limit=3)

    print(f"\nSearch results:")
    for result in results:
        print(f"  Score: {result.score:.4f}")
        print(f"  Text: {result.payload.get('text', 'N/A')}")
        print(f"  Category: {result.payload.get('category', 'N/A')}")

    # Clean up
    store.delete_collection()

    print("✅ Qdrant operations working!\n")


if __name__ == "__main__":
    test_qdrant()
```

### Exercise 5: Neo4j Knowledge Graph

```python
from neo4j import GraphDatabase

class KnowledgeGraph:
    """Neo4j knowledge graph operations"""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_entity(self, label, name, properties=None):
        """Create an entity node"""
        with self.driver.session() as session:
            result = session.run(
                f"CREATE (n:{label} {{name: $name}}) RETURN n",
                name=name
            )
            return result.single()[0]

    def create_relationship(self, entity1, rel_type, entity2, properties=None):
        """Create a relationship between entities"""
        with self.driver.session() as session:
            query = f"""
            MATCH (a {{name: $entity1}})
            MATCH (b {{name: $entity2}})
            CREATE (a)-[r:{rel_type}]->(b)
            RETURN r
            """
            result = session.run(query, entity1=entity1, entity2=entity2)
            return result.single()

    def find_connections(self, entity_name, max_depth=2):
        """Find all connections within depth"""
        with self.driver.session() as session:
            query = f"""
            MATCH (start {{name: $name}})-[*1..{max_depth}]-(connected)
            RETURN DISTINCT connected.name AS name, labels(connected) AS labels
            LIMIT 20
            """
            result = session.run(query, name=entity_name)
            return [(record["name"], record["labels"]) for record in result]

    def find_shortest_path(self, entity1, entity2):
        """Find shortest path between entities"""
        with self.driver.session() as session:
            query = """
            MATCH path = shortestPath(
                (a {name: $entity1})-[*]-(b {name: $entity2})
            )
            RETURN [node in nodes(path) | node.name] AS path
            """
            result = session.run(query, entity1=entity1, entity2=entity2)
            record = result.single()
            return record["path"] if record else None


def test_neo4j():
    print("=== Neo4j Knowledge Graph Test ===")

    # Note: This requires a running Neo4j instance
    print("This exercise requires a running Neo4j instance.")
    print("\nTo test:")

    example_code = """
    # Connect to Neo4j
    kg = KnowledgeGraph(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="your_password"
    )

    # Create entities
    kg.create_entity("Person", "Alice")
    kg.create_entity("Person", "Bob")
    kg.create_entity("Company", "TechCorp")

    # Create relationships
    kg.create_relationship("Alice", "WORKS_AT", "TechCorp")
    kg.create_relationship("Bob", "KNOWS", "Alice")

    # Find connections
    connections = kg.find_connections("Alice", max_depth=2)
    print(f"Alice's connections: {connections}")

    # Find shortest path
    path = kg.find_shortest_path("Bob", "TechCorp")
    print(f"Path from Bob to TechCorp: {path}")

    kg.close()
    """

    print(example_code)

    print("\nExpected output:")
    print("  Alice's connections: [('Bob', ['Person']), ('TechCorp', ['Company'])]")
    print("  Path from Bob to TechCorp: ['Bob', 'Alice', 'TechCorp']")

    print("✅ Neo4j concepts demonstrated!\n")


if __name__ == "__main__":
    test_neo4j()
```

### Exercise 6: Context Building for RAG

```python
from typing import List, Dict

class ContextBuilder:
    """Build context for RAG from retrieved documents"""

    def __init__(self, max_context_length: int = 2000):
        self.max_context_length = max_context_length

    def build_context(
        self,
        retrieved_docs: List[Dict],
        query: str,
        include_sources: bool = True
    ) -> str:
        """
        Build context string from retrieved documents

        Args:
            retrieved_docs: List of retrieved documents with text and metadata
            query: Original user query
            include_sources: Whether to include source citations

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add query context
        context_parts.append(f"Query: {query}\n")

        # Add retrieved documents
        for i, doc in enumerate(retrieved_docs, 1):
            text = doc.get("text", "")
            source = doc.get("source", "Unknown")

            if include_sources:
                context_parts.append(f"[Source {i}: {source}]")
                context_parts.append(f"{text}\n")
            else:
                context_parts.append(f"{text}\n")

        # Combine and truncate if needed
        full_context = "\n".join(context_parts)

        if len(full_context) > self.max_context_length:
            # Truncate from the end
            full_context = full_context[:self.max_context_length] + "..."

        return full_context

    def format_with_citations(self, response: str, sources: List[Dict]) -> str:
        """
        Add source citations to response

        Args:
            response: Generated response
            sources: Source documents used

        Returns:
            Response with citations
        """
        if not sources:
            return response

        citations = "\n\nSources:\n"
        for i, source in enumerate(sources, 1):
            citations += f"{i}. {source.get('source', 'Unknown')}: {source.get('text', '')[:100]}...\n"

        return response + citations

    def deduplicate_context(self, contexts: List[str]) -> List[str]:
        """
        Remove duplicate or very similar contexts

        Args:
            contexts: List of context strings

        Returns:
            Deduplicated contexts
        """
        unique_contexts = []
        seen = set()

        for context in contexts:
            # Simple deduplication by exact match
            context_hash = hash(context)
            if context_hash not in seen:
                seen.add(context_hash)
                unique_contexts.append(context)

        return unique_contexts


def test_context_builder():
    print("=== Context Builder Test ===")

    # Sample retrieved documents
    retrieved_docs = [
        {
            "text": "Machine learning algorithms learn patterns from data",
            "source": "doc1.pdf",
            "score": 0.95
        },
        {
            "text": "Deep learning is a subset of machine learning",
            "source": "doc2.pdf",
            "score": 0.88
        },
        {
            "text": "Neural networks are the foundation of deep learning",
            "source": "doc3.pdf",
            "score": 0.82
        }
    ]

    query = "What is the relationship between deep learning and machine learning?"

    # Build context
    builder = ContextBuilder(max_context_length=500)
    context = builder.build_context(retrieved_docs, query, include_sources=True)

    print("Built context:")
    print(context)
    print()

    # Format with citations
    response = "Deep learning is a subset of machine learning that uses neural networks to learn patterns from data."

    formatted = builder.format_with_citations(response, retrieved_docs[:2])

    print("Response with citations:")
    print(formatted)

    print("✅ Context building working!\n")


if __name__ == "__main__":
    test_context_builder()
```

---

## Completion Checklist

- [ ] Vector search implemented
- [ ] BM25 search working
- [ ] Hybrid search with rank fusion
- [ ] Qdrant operations tested
- [ ] Neo4j knowledge graph created
- [ ] Context building functional
- [ ] RAG pipeline assembled
- [ ] Retrieval quality evaluated

---

**Last Updated:** 2026-02-05
