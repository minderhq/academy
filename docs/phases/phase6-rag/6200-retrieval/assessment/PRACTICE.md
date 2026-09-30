---
Document ID: 6200-PRACTICE
Title: "6200: Advanced Retrieval - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'rag', 'retrieval']
---

# 6200: Advanced Retrieval - Practice

## Exercises

### Exercise 1: Hybrid Search (Dense + Sparse)

```python
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class HybridRetriever:
    def __init__(self, documents):
        self.documents = documents

        # Dense retrieval
        print("Initializing dense retrieval...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.dense_embeddings = self.embedder.encode(documents)

        # Sparse retrieval
        print("Initializing sparse retrieval...")
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.sparse_embeddings = self.vectorizer.fit_transform(documents)

    def search(self, query, alpha=0.5, top_k=5):
        """Hybrid search combining dense and sparse."""

        # Dense scores
        query_embedding = self.embedder.encode([query])
        dense_scores = np.dot(self.dense_embeddings, query_embedding.T).flatten()

        # Sparse scores
        query_sparse = self.vectorizer.transform([query])
        sparse_scores = self.sparse_embeddings.dot(query_sparse.T).toarray().flatten()

        # Normalize scores to [0, 1]
        dense_scores = (dense_scores - dense_scores.min()) / (dense_scores.max() - dense_scores.min() + 1e-8)
        sparse_scores = (sparse_scores - sparse_scores.min()) / (sparse_scores.max() - sparse_scores.min() + 1e-8)

        # Combine with weighted average
        combined_scores = alpha * dense_scores + (1 - alpha) * sparse_scores

        # Get top-k indices
        top_indices = combined_scores.argsort()[-top_k:][::-1]

        return [
            {
                "document": self.documents[i],
                "score": float(combined_scores[i]),
                "dense_score": float(dense_scores[i]),
                "sparse_score": float(sparse_scores[i]),
            }
            for i in top_indices
        ]

# Test
documents = [
    "Machine learning models learn patterns from data.",
    "Deep learning uses neural networks with multiple layers.",
    "Natural language processing helps computers understand text.",
    "Computer vision enables machines to interpret visual information.",
    "Reinforcement learning trains agents through rewards.",
    "Support vector machines are used for classification tasks.",
    "Random forests combine multiple decision trees.",
    "Transformers revolutionized natural language processing.",
]

print("Creating HybridRetriever...")
retriever = HybridRetriever(documents)

# Test queries
queries = [
    "neural networks",
    "text understanding",
    "decision making",
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: '{query}'")
    print(f"{'='*60}")

    # Try different alpha values
    for alpha in [0.0, 0.5, 1.0]:
        method = "Sparse" if alpha == 0 else "Dense" if alpha == 1 else "Hybrid"
        results = retriever.search(query, alpha=alpha, top_k=3)

        print(f"\n{method} (alpha={alpha}):")
        for i, res in enumerate(results, 1):
            print(f"  {i}. [{res['score']:.3f}] {res['document'][:60]}...")

# Expected output:
# - Alpha=0 (sparse): Good for keyword matching
# - Alpha=1 (dense): Good for semantic similarity
# - Alpha=0.5 (hybrid): Best of both worlds
```

### Exercise 2: Query Expansion

```python
from transformers import pipeline

# Load query expansion model
print("Loading query expansion model...")
generator = pipeline("text2text-generation", model="t5-base")

def expand_query(query, n_expansions=3):
    """Generate query expansions for better retrieval."""

    # Generate expansions using LLM
    prompt = f"Generate {n_expansions} alternative search queries for: '{query}'"
    prompt += "\nQueries:"

    expansions = generator(
        prompt,
        max_length=100,
        num_return_sequences=n_expansions,
        temperature=0.8,
        do_sample=True
    )

    # Parse expansions
    expanded_queries = [query]  # Include original
    for exp in expansions:
        generated_text = exp["generated_text"]
        # Extract queries from generated text
        queries = [q.strip() for q in generated_text.split(",") if q.strip()]
        expanded_queries.extend(queries)

    return list(set(expanded_queries))  # Remove duplicates

def retrieve_with_expansion(retriever, query, top_k=5):
    """Retrieve using query expansion."""

    # Get expanded queries
    expanded = expand_query(query, n_expansions=2)

    print(f"Original query: '{query}'")
    print(f"Expanded queries: {expanded[1:]}\n")

    # Retrieve for each query variant
    all_results = {}
    for exp_query in expanded:
        results = retriever.search(exp_query, top_k=top_k*2)
        for res in results:
            doc = res["document"]
            score = res["score"]
            if doc not in all_results:
                all_results[doc] = score
            else:
                # Max score aggregation
                all_results[doc] = max(all_results[doc], score)

    # Re-rank and return top-k
    sorted_results = sorted(all_results.items(), key=lambda x: x[1], reverse=True)

    return sorted_results[:top_k]

# Test
query = "neural network architecture"
print(f"\nQuery Expansion Test")
print(f"{'='*60}\n")

results = retrieve_with_expansion(retriever, query, top_k=3)

print("Final Results:")
for i, (doc, score) in enumerate(results, 1):
    print(f"{i}. [{score:.3f}] {doc}")

# Expected output:
# - Expanded queries capture different aspects of the original
# - Broader coverage improves recall
# - Aggregation ensures best results rise to top
```

### Exercise 3: Cross-Encoder Re-ranking

```python
from sentence_transformers import CrossEncoder

# Load cross-encoder for re-ranking
print("Loading cross-encoder for re-ranking...")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def retrieve_and_rerank(documents, query, retriever, top_k=10, rerank_top=5):
    """Retrieve with cross-encoder re-ranking."""

    # Initial retrieval (fast)
    print(f"Initial retrieval (top {top_k})...")
    initial_results = retriever.search(query, top_k=top_k)

    # Re-rank with cross-encoder (more accurate but slower)
    print(f"Re-ranking with cross-encoder...")
    pairs = [[query, doc["document"]] for doc in initial_results]
    scores = reranker.predict(pairs)

    # Combine with original scores
    reranked = [
        {
            "document": initial_results[i]["document"],
            "rerank_score": float(scores[i]),
            "dense_score": initial_results[i]["dense_score"],
        }
        for i in range(len(initial_results))
    ]

    # Sort by rerank score
    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

    return reranked[:rerank_top]

# Test
query = "deep learning models"
print(f"\nCross-Encoder Re-ranking Test")
print(f"{'='*60}\n")

results = retrieve_and_rerank(documents, query, retriever, top_k=8, rerank_top=3)

print("Re-ranked Results:")
for i, res in enumerate(results, 1):
    print(f"{i}. [{res['rerank_score']:.3f}] {res['document']}")

# Expected output:
# - Cross-encoder provides more accurate relevance scoring
# - Re-ranking improves precision of top results
# - Trade-off: slower than pure dense retrieval
```

### Exercise 4: Query Understanding with LLM

```python
import json
import re

def analyze_query(query, llm_func):
    """Use LLM to understand and reformulate query."""

    prompt = f"""Analyze this search query and output JSON:
Query: "{query}"

Output format (valid JSON only):
{{
    "intent": "informational|navigational|transactional",
    "keywords": ["keyword1", "keyword2"],
    "entities": ["entity1", "entity2"],
    "reformulated": "improved query"
}}"""

    response = llm_func(prompt)

    # Extract JSON from response
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            analysis = json.loads(json_match.group())
            return analysis
        except json.JSONDecodeError:
            pass

    # Fallback
    return {
        "intent": "informational",
        "keywords": query.split(),
        "entities": [],
        "reformulated": query,
    }

def enhanced_retrieval(query, retriever, llm_func):
    """Enhanced retrieval with query understanding."""

    # Analyze query
    print("Analyzing query...")
    analysis = analyze_query(query, llm_func)

    print(f"Query Analysis:")
    print(f"  Intent: {analysis['intent']}")
    print(f"  Keywords: {analysis['keywords']}")
    print(f"  Entities: {analysis['entities']}")
    print(f"  Reformulated: {analysis['reformulated']}\n")

    # Multi-strategy retrieval
    results = []

    # Strategy 1: Original query
    print("Strategy 1: Original query")
    results.extend(retriever.search(query, top_k=2))

    # Strategy 2: Reformulated query
    if analysis.get("reformulated") and analysis["reformulated"] != query:
        print("Strategy 2: Reformulated query")
        results.extend(retriever.search(analysis["reformulated"], top_k=2))

    # Strategy 3: Keyword search
    if analysis.get("keywords"):
        keyword_query = " ".join(analysis["keywords"][:3])
        print(f"Strategy 3: Keywords ({keyword_query})")
        results.extend(retriever.search(keyword_query, top_k=1))

    # Aggregate and deduplicate
    seen = set()
    unique_results = []
    for res in results:
        doc = res["document"]
        if doc not in seen:
            seen.add(doc)
            unique_results.append(res)

    return unique_results[:5]

# Mock LLM function for testing
def mock_llm(prompt):
    return """{
    "intent": "informational",
    "keywords": ["neural", "networks", "learning"],
    "entities": ["neural networks"],
    "reformulated": "deep neural network architectures"
}"""

# Test
query = "neural networks"
print(f"\nQuery Understanding Test")
print(f"{'='*60}\n")

results = enhanced_retrieval(query, retriever, mock_llm)

print("\nFinal Results:")
for i, res in enumerate(results, 1):
    print(f"{i}. [{res['score']:.3f}] {res['document']}")

# Expected output:
# - Query decomposition reveals key concepts
# - Reformulated query captures semantic meaning
# - Multi-strategy retrieval improves coverage
```

### Exercise 5: Hierarchical Retrieval

```python
import numpy as np


class HierarchicalRetriever:
    def __init__(self, documents, window_size=3):
        self.window_size = window_size

        # Create document hierarchy
        self.chunks = documents
        self.parent_docs = self._create_parent_docs(window_size)

        # Index both levels
        print("Building hierarchical index...")
        self.chunk_index = self._build_index(self.chunks)
        self.parent_index = self._build_index(self.parent_docs)

    def _create_parent_docs(self, window_size):
        """Create parent documents from chunks."""
        parents = []
        for i in range(0, len(self.chunks), window_size):
            parent = " ".join(self.chunks[i:i+window_size])
            parents.append(parent)
        return parents

    def _build_index(self, docs):
        """Build search index."""
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        return embedder.encode(docs)

    def retrieve(self, query, top_k=5):
        """Retrieve with parent-child lookup."""

        # Search chunks
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        query_emb = embedder.encode([query])

        chunk_scores = np.dot(self.chunk_index, query_emb.T).flatten()

        # Get top chunks
        top_chunk_indices = chunk_scores.argsort()[-top_k:][::-1]

        # Return parent documents with aggregated scores
        results = []
        seen_parents = set()

        for chunk_idx in top_chunk_indices:
            parent_idx = chunk_idx // self.window_size
            if parent_idx not in seen_parents:
                seen_parents.add(parent_idx)
                # Aggregate scores from all chunks in this parent
                start = parent_idx * self.window_size
                parent_chunks = range(start, min(start + self.window_size, len(self.chunks)))
                aggregated_score = float(np.mean([chunk_scores[i] for i in parent_chunks]))
                results.append({
                    "document": self.parent_docs[parent_idx],
                    "score": aggregated_score,
                })

        return results

# Test
print("\nHierarchical Retrieval Test")
print(f"{'='*60}\n")

hier_retriever = HierarchicalRetriever(documents)

query = "machine learning models"
results = hier_retriever.retrieve(query, top_k=3)

print("Results (parent documents):")
for i, res in enumerate(results, 1):
    print(f"{i}. [{res['score']:.3f}] {res['document'][:80]}...")

# Expected output:
# - Returns broader context (parent docs)
# - Better for questions requiring multiple chunks
# - Maintains relevance through child chunk scoring
```

### Exercise 6: Multi-Vector Retrieval

```python
import numpy as np


def multi_vector_retrieve(documents, query, embedder, top_k=5):
    """Retrieve using multiple document representations."""

    # Create genuinely different representations: the title (first
    # sentence), the significant keywords (stopwords dropped), and the
    # full text. Two near-identical views would just double-count the
    # first sentence instead of adding signal.
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "and", "or",
        "of", "to", "in", "for", "with", "on", "from", "that", "this",
    }

    def keywords(doc):
        words = [w.strip(".,") for w in doc.lower().split()]
        return " ".join(w for w in words if w and w not in stopwords)

    representations = {
        "title": [doc.split(".")[0] for doc in documents],  # First sentence as title
        "keywords": [keywords(doc) for doc in documents],
        "full": documents,
    }

    # Embed all representations
    embedded = {}
    for key, docs in representations.items():
        embedded[key] = embedder.encode(docs)

    query_emb = embedder.encode([query])

    # Score each representation
    all_scores = []
    weights = {
        "title": 0.4,
        "keywords": 0.3,
        "full": 0.3,
    }

    for key in ["title", "keywords", "full"]:
        scores = np.dot(embedded[key], query_emb.T).flatten()
        # Normalize scores
        scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)
        weighted_scores = scores * weights[key]
        all_scores.append(weighted_scores)

    # Combine scores
    combined = np.sum(all_scores, axis=0)

    # Get top results
    top_indices = combined.argsort()[-top_k:][::-1]

    return [
        {
            "document": documents[i],
            "score": float(combined[i]),
            "title_score": float(all_scores[0][i]),
            "full_score": float(all_scores[2][i]),
        }
        for i in top_indices
    ]

# Test
print("\nMulti-Vector Retrieval Test")
print(f"{'='*60}\n")

query = "text processing"
results = multi_vector_retrieve(documents, query, retriever.embedder, top_k=3)

print("Results:")
for i, res in enumerate(results, 1):
    print(f"{i}. [{res['score']:.3f}] {res['document']}")
    print(f"   Title: {res['title_score']:.3f} | Full: {res['full_score']:.3f}")

# Expected output:
# - Multiple views capture different aspects
# - Title matching gives higher weight to key phrases
# - Full text ensures overall relevance
```

### Exercise 7: Recursive Retrieval

```python
import numpy as np


class RecursiveRetriever:
    def __init__(self, documents):
        # Build recursive index
        self.sentences = self._split_sentences(documents)
        self.chunks = documents
        self.index = self._build_index()

    def _split_sentences(self, docs):
        """Split documents into sentences."""
        sentences = []
        for doc in docs:
            sents = doc.split(". ")
            # rstrip normalizes pieces that already end in a period,
            # otherwise every sentence would end in ".."
            sentences.extend(s.rstrip(".") + "." for s in sents if s)
        return sentences

    def _build_index(self):
        """Build multi-level index."""
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        return {
            "sentence": embedder.encode(self.sentences),
            "chunk": embedder.encode(self.chunks),
            "embedder": embedder,
        }

    def retrieve(self, query, granularity="auto", top_k=5):
        """Retrieve at appropriate granularity."""

        query_emb = self.index["embedder"].encode([query])

        # Sentence-level retrieval
        sent_scores = np.dot(self.index["sentence"], query_emb.T).flatten()
        top_sents = sent_scores.argsort()[-top_k*2:][::-1]

        # Determine granularity
        if granularity == "auto":
            # Check if results are concentrated or spread out
            sent_chunk_ids = [i // 3 for i in top_sents]  # Assume 3 sents per chunk
            unique_chunks = len(set(sent_chunk_ids))

            if unique_chunks > 2:
                # Results span multiple chunks - use chunk retrieval
                granularity = "chunk"
            else:
                # Results focused - use sentence retrieval
                granularity = "sentence"

        if granularity == "chunk":
            print("Using chunk-level retrieval")
            chunk_scores = np.dot(self.index["chunk"], query_emb.T).flatten()
            top_chunks = chunk_scores.argsort()[-top_k:][::-1]
            return [
                {"document": self.chunks[i], "score": float(chunk_scores[i])}
                for i in top_chunks
            ]
        else:
            print("Using sentence-level retrieval")
            return [
                {"document": self.sentences[i], "score": float(sent_scores[i])}
                for i in top_sents[:top_k]
            ]

# Test
print("\nRecursive Retrieval Test")
print(f"{'='*60}\n")

recursive_retriever = RecursiveRetriever(documents)

query = "natural language"
results = recursive_retriever.retrieve(query, granularity="auto", top_k=3)

print("\nResults:")
for i, res in enumerate(results, 1):
    print(f"{i}. [{res['score']:.3f}] {res['document']}")

# Expected output:
# - Automatically chooses appropriate granularity
# - Focused queries return precise sentences
# - Broad queries return full chunks
```
