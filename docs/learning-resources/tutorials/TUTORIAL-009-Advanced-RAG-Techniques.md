---
Document ID: TUTORIAL-009
Title: "TUTORIAL-009: Advanced RAG Techniques"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: [TUTORIAL-003]
Tags: ['tutorial', 'rag', 'reranking']
---

# TUTORIAL-009: Advanced RAG Techniques

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: Hybrid Search](#part-1-hybrid-search)
- [Part 2: Re-ranking](#part-2-re-ranking)
- [Part 3: GraphRAG](#part-3-graphrag)
- [Part 4: Long-Context Handling](#part-4-long-context-handling)
- [Part 5: Evaluation](#part-5-evaluation)
- [Part 6: Performance Optimization](#part-6-performance-optimization)
- [Exercises](#exercises)
- [Completion Checklist](#completion-checklist)
- [References](#references)
- [Next Steps](#next-steps)

---

## Abstract

This tutorial covers advanced Retrieval-Augmented Generation techniques including hybrid search, re-ranking, and GraphRAG.

**Duration:** 5 hours
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:** TUTORIAL-003 (RAG Basics), LAB-002 (RAG Implementation)

---

## Learning Objectives

After this tutorial, you will:

- Implement hybrid search (vector + keyword)
- Add re-ranking for better retrieval
- Build GraphRAG with Neo4j
- Optimize retrieval performance
- Handle long-context documents

---

## Part 1: Hybrid Search

### Installation

```bash
uv pip install rank-bm25 sentence-transformers neo4j spacy
python -m spacy download en_core_web_sm
```

Part 1 needs rank-bm25, Part 2 sentence-transformers, and Part 3
neo4j + spaCy — the spaCy pipeline must be downloaded once with the
second command before `spacy.load("en_core_web_sm")` will work.
The remaining parts are standard library only.

### Combining Vector and BM25 Search

```python
from rank_bm25 import BM25Okapi
import numpy as np


class HybridRetriever:
    """Hybrid search combining vector and keyword search"""

    def __init__(self, documents: list[str], embedding_model):
        self.documents = documents
        self.embedding_model = embedding_model

        # Build embeddings for vector search
        self.embeddings = embedding_model.encode(documents)

        # Build BM25 index
        tokenized_docs = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)

    def search(
        self,
        query: str,
        alpha: float = 0.5,
        k: int = 10
    ) -> list[tuple[int, float]]:
        """
        Hybrid search with configurable alpha

        Args:
            query: Search query
            alpha: Weight for vector search (0-1)
            k: Number of results to return
        """
        # Vector search
        query_embedding = self.embedding_model.encode(query)
        vector_scores = self._cosine_similarity(query_embedding, self.embeddings)

        # Keyword search
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Normalize scores
        vector_scores = self._min_max_normalize(vector_scores)
        bm25_scores = self._min_max_normalize(bm25_scores)

        # Combine scores
        combined_scores = alpha * vector_scores + (1 - alpha) * bm25_scores

        # Get top-k
        top_indices = np.argsort(combined_scores)[::-1][:k]

        return [(idx, combined_scores[idx]) for idx in top_indices]

    def _cosine_similarity(self, a, b):
        """Compute cosine similarity"""
        return np.dot(a, b.T) / (np.linalg.norm(a) * np.linalg.norm(b, axis=1))

    def _min_max_normalize(self, scores):
        """Normalize scores to 0-1 range"""
        min_score = scores.min()
        max_score = scores.max()
        if max_score - min_score == 0:
            return np.zeros_like(scores)
        return (scores - min_score) / (max_score - min_score)
```

### Reciprocal Rank Fusion (RRF)

```python
def reciprocal_rank_fusion(
    results_list: list[list[tuple[int, float]]],
    k: int = 60
) -> list[tuple[int, float]]:
    """
    Reciprocal Rank Fusion algorithm

    Combines multiple ranked lists without score normalization
    """
    fused_scores = {}

    for results in results_list:
        for rank, (doc_id, _) in enumerate(results):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (k + rank + 1)

    # Sort by fused score
    sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results

# Usage - RRF fuses ranked lists from independent retrievers, each a
# list of (doc_id, score) pairs ordered best-first. Only the ranks
# matter; the raw scores are discarded.
vector_results = [(0, 0.91), (2, 0.87), (1, 0.85)]
keyword_results = [(1, 8.2), (0, 7.9), (3, 7.1)]

fused = reciprocal_rank_fusion([vector_results, keyword_results])
print([(doc_id, round(score, 4)) for doc_id, score in fused[:3]])

# Expected Output:
# [(0, 0.0325), (1, 0.0323), (2, 0.0161)]
# (k=60: each list contributes 1/(60 + rank + 1). Docs 0 and 1 were
#  found by BOTH retrievers, so their terms add - 1/61+1/62 and
#  1/63+1/61; docs 2 and 3 were found by only one, which is exactly
#  the recall boost RRF is used for)
```

---

## Part 2: Re-ranking

### Cross-Encoder Re-ranking

```python
from sentence_transformers import CrossEncoder

class ReRanker:
    """Re-rank retrieved documents using cross-encoder"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 10
    ) -> list[dict]:
        """
        Re-rank documents using cross-encoder

        Args:
            query: User query
            documents: Retrieved documents
            top_k: Number of documents to return
        """
        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Score with cross-encoder
        scores = self.model.predict(pairs)

        # Sort by score
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)

        # Return top-k
        return [
            {"document": doc, "score": float(score)}
            for doc, score in ranked[:top_k]
        ]

# Usage in RAG pipeline
class AdvancedRAG:
    def __init__(self, vector_store, reranker=None):
        self.vector_store = vector_store
        self.reranker = reranker

    def retrieve(self, query: str, initial_k: int = 50, final_k: int = 10):
        # Initial retrieval (more than needed)
        candidates = self.vector_store.search(query, k=initial_k)

        # Re-rank if reranker available
        if self.reranker:
            documents = [c["text"] for c in candidates]
            reranked = self.reranker.rerank(query, documents, top_k=final_k)
            return reranked

        return candidates[:final_k]
```

---

## Part 3: GraphRAG

### Knowledge Graph Construction

```python
from neo4j import GraphDatabase
import spacy

class GraphRAG:
    """RAG with knowledge graph"""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.nlp = spacy.load("en_core_web_sm")

    def extract_entities(self, text: str) -> list[tuple]:
        """Extract entities and relationships"""
        doc = self.nlp(text)

        entities = []
        for ent in doc.ents:
            entities.append((ent.text, ent.label_))

        # Extract relationships (simplified)
        relationships = []
        for token in doc:
            if token.dep_ in ["nsubj", "dobj", "pobj"]:
                relationships.append((
                    token.head.text,
                    token.dep_,
                    token.text
                ))

        return entities, relationships

    def build_graph(self, documents: list[str]):
        """Build knowledge graph from documents"""
        with self.driver.session() as session:
            for doc_text in documents:
                entities, relationships = self.extract_entities(doc_text)

                # Create entity nodes
                for entity, label in entities:
                    session.run(
                        "MERGE (e:Entity {name: $name, type: $type})",
                        name=entity, type=label
                    )

                # Create relationships. MATCH (not MERGE) means pairs
                # whose endpoints were never created as Entity nodes
                # above are silently skipped - only known entities
                # get edges.
                for source, rel_type, target in relationships:
                    session.run("""
                        MATCH (s:Entity {name: $source})
                        MATCH (t:Entity {name: $target})
                        MERGE (s)-[r:RELATES {type: $rel_type}]->(t)
                        """,
                        source=source, target=target, rel_type=rel_type
                    )

    def graph_retrieve(self, query: str, k: int = 5) -> list[str]:
        """Retrieve using graph traversal"""
        with self.driver.session() as session:
            # Extract entities from query
            entities, _ = self.extract_entities(query)

            if not entities:
                return []

            # Find connected documents
            results = []
            for entity, _ in entities:
                result = session.run("""
                    MATCH (e:Entity {name: $entity})-[:RELATES]-(related:Entity)
                    RETURN DISTINCT related.name AS related_entity
                    LIMIT $k
                    """,
                    entity=entity, k=k
                )
                results.extend([r["related_entity"] for r in result])

            return results[:k]
```

---

## Part 4: Long-Context Handling

### Context Window Optimization

```python
class ContextManager:
    """Manage long context windows efficiently"""

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        # Reserve space for query and response
        self.context_budget = max_tokens - 1000

    def build_context(
        self,
        retrieved_docs: list[dict],
        query: str,
        strategy: str = "stuff"
    ) -> str:
        """
        Build context from retrieved documents

        Strategies:
        - stuff: Combine all (if fits)
        - map_reduce: Summarize then combine (needs an LLM
          summarizer - raises NotImplementedError here)
        - refine: Iteratively refine
        """
        if strategy == "stuff":
            return self._stuff_context(retrieved_docs, query)
        elif strategy == "map_reduce":
            # Requires an LLM summarizer this class does not hold -
            # left as an exercise, so fail loudly rather than pretend
            raise NotImplementedError("map_reduce needs a summarizer; see Exercises")
        elif strategy == "refine":
            return self._refine_context(retrieved_docs, query)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _stuff_context(self, docs: list[dict], query: str) -> str:
        """Simple concatenation (if fits in context)"""
        context_parts = [f"Query: {query}\n\nRelevant Context:"]

        total_tokens = 0
        for doc in docs:
            doc_text = doc["text"]
            # Word count as a rough token proxy - real tokenizers
            # yield more tokens than words for typical English prose
            tokens = len(doc_text.split())

            if total_tokens + tokens > self.context_budget:
                break

            context_parts.append(f"- {doc_text}")
            total_tokens += tokens

        return "\n".join(context_parts)

    def _refine_context(self, docs: list[dict], query: str) -> str:
        """Iteratively refine context"""
        context = f"Query: {query}\n\nContext:"

        for doc in docs:
            # In practice, would use LLM to refine
            context += f"\n- {doc['text'][:200]}..."

        return context
```

---

## Part 5: Evaluation

### RAG Evaluation Metrics

```python
# List/Dict were already imported in Parts 1-2; the old numpy import
# here was unused - every metric below is pure Python.
import math
from collections import Counter

class RAGEvaluator:
    """Evaluate RAG system performance"""

    def __init__(self, retriever, generator):
        self.retriever = retriever
        self.generator = generator

    def evaluate(
        self,
        test_queries: list[str],
        ground_truth_docs: list[list[int]],
        ground_truth_answers: list[str]
    ) -> dict:
        """Evaluate retrieval and generation"""

        retrieval_metrics = {}
        generation_metrics = {}

        for query, true_docs, true_answer in zip(
            test_queries, ground_truth_docs, ground_truth_answers
        ):
            # Evaluate retrieval - accumulate per-query values; the old
            # update() overwrote the same keys every iteration, so
            # _average_dict would have averaged a single (last-query)
            # sample
            retrieved = self.retriever.search(query, k=10)
            for name, value in {
                "precision@5": self._precision_at_k(retrieved, true_docs, k=5),
                "recall@10": self._recall_at_k(retrieved, true_docs, k=10),
                "mrr": self._mrr(retrieved, true_docs)
            }.items():
                retrieval_metrics.setdefault(name, []).append(value)

            # Evaluate generation
            context = "\n".join([d["text"] for d in retrieved[:3]])
            response = self.generator.generate(query, context)

            for name, value in {
                "bleu": self._bleu_score(response, true_answer),
                "rouge": self._rouge_score(response, true_answer)
            }.items():
                generation_metrics.setdefault(name, []).append(value)

        return {
            "retrieval": self._average_dict(retrieval_metrics),
            "generation": self._average_dict(generation_metrics)
        }

    def _precision_at_k(self, retrieved, true_docs, k):
        retrieved_ids = [r[0] for r in retrieved[:k]]
        relevant = len(set(retrieved_ids) & set(true_docs))
        return relevant / k

    def _recall_at_k(self, retrieved, true_docs, k):
        retrieved_ids = [r[0] for r in retrieved[:k]]
        relevant = len(set(retrieved_ids) & set(true_docs))
        return relevant / len(true_docs) if true_docs else 0

    def _mrr(self, retrieved, true_docs):
        for i, (doc_id, _) in enumerate(retrieved):
            if doc_id in true_docs:
                return 1 / (i + 1)
        return 0

    def _average_dict(self, metrics):
        """Mean of each metric across all evaluated queries"""
        return {
            name: sum(values) / len(values)
            for name, values in metrics.items()
        }

    def _bleu_score(self, response, reference, max_n=4):
        """Simplified BLEU-N: clipped n-gram precisions, geometric
        mean, brevity penalty. Production code should use sacrebleu."""
        resp = response.lower().split()
        ref = reference.lower().split()
        if not resp or not ref:
            return 0.0

        precisions = []
        for n in range(1, max_n + 1):
            resp_ngrams = Counter(
                tuple(resp[i:i + n]) for i in range(len(resp) - n + 1)
            )
            ref_ngrams = Counter(
                tuple(ref[i:i + n]) for i in range(len(ref) - n + 1)
            )
            clipped = sum((resp_ngrams & ref_ngrams).values())
            total = max(sum(resp_ngrams.values()), 1)
            precisions.append(clipped / total)

        if min(precisions) == 0:
            return 0.0
        geo_mean = math.exp(sum(math.log(p) for p in precisions) / max_n)
        brevity = min(1.0, math.exp(1 - len(ref) / len(resp)))
        return geo_mean * brevity

    def _rouge_score(self, response, reference):
        """ROUGE-L: F1 over the longest common subsequence.
        Production code should use the rouge-score package."""
        resp = response.lower().split()
        ref = reference.lower().split()
        if not resp or not ref:
            return 0.0

        lcs = [[0] * (len(ref) + 1) for _ in range(len(resp) + 1)]
        for i in range(1, len(resp) + 1):
            for j in range(1, len(ref) + 1):
                if resp[i - 1] == ref[j - 1]:
                    lcs[i][j] = lcs[i - 1][j - 1] + 1
                else:
                    lcs[i][j] = max(lcs[i - 1][j], lcs[i][j - 1])
        lcs_len = lcs[-1][-1]
        if lcs_len == 0:
            return 0.0
        precision = lcs_len / len(resp)
        recall = lcs_len / len(ref)
        return 2 * precision * recall / (precision + recall)
```

---

## Part 6: Performance Optimization

### Caching and Indexing

```python
import hashlib

class CachedRetriever:
    """Retriever with caching for common queries"""

    def __init__(self, base_retriever, cache_size: int = 1000):
        self.base_retriever = base_retriever
        self.cache = {}
        self.cache_size = cache_size

    def _get_cache_key(self, query: str, k: int) -> str:
        """Generate cache key"""
        content = f"{query}:{k}"
        return hashlib.md5(content.encode()).hexdigest()

    def search(self, query: str, k: int = 10):
        cache_key = self._get_cache_key(query, k)

        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Retrieve and cache
        results = self.base_retriever.search(query, k=k)

        # Evict if cache full
        if len(self.cache) >= self.cache_size:
            # Remove oldest (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[cache_key] = results
        return results
```

---

## Exercises

1. **Implement hybrid search** with tunable alpha
2. **Add re-ranking** to existing RAG pipeline
3. **Build knowledge graph** from domain documents
4. **Evaluate and optimize** retrieval performance
5. **Handle long documents** with chunking strategies

---

## Completion Checklist

- [ ] Hybrid search implemented
- [ ] Re-ranking working
- [ ] GraphRAG prototype built
- [ ] Evaluation metrics calculated
- [ ] Performance optimized

---

## References

### Related Minder Academy Documents

- [TUTORIAL-003: RAG Basics](TUTORIAL-003-RAG-Basics.md)
- [LAB-002: RAG Implementation](../labs/LAB-002-RAG-Implementation.md)
- [LAB-005: GraphRAG](../labs/LAB-005-GraphRAG.md)
- [6201: Hybrid Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)

---

## Next Steps

- Hands-on: **[6201: Hybrid Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)**
- Practice: **[LAB-005: GraphRAG](../labs/LAB-005-GraphRAG.md)**
