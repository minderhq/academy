---
Document ID: CHEAT-SHEET-005
Title: "CHEAT-SHEET-005: RAG Systems"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rag', 'retrieval']
---

# CHEAT-SHEET-005: RAG Systems
## Retrieval-Augmented Generation Quick Reference

**Version:** 1.2
**Last Updated:** 2026-10-08

---

## Quick Start

```python
# Basic RAG Pipeline - LangChain 1.x composes with LCEL instead
# of the legacy RetrievalQA wrapper.
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Setup
embeddings = OpenAIEmbeddings()
# docs: a list of LangChain Document objects
vectorstore = QdrantVectorStore.from_documents(
    docs, embeddings, url="localhost:6333", collection_name="docs"
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
llm = ChatOpenAI(model="gpt-4")

# Chain (LCEL)
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using only the provided context."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

qa = (
    RunnableParallel(
        context=retriever | format_docs,
        question=RunnablePassthrough(),
    )
    | prompt | llm | StrOutputParser()
)
result = qa.invoke("Your question here")
```

---

## 1. Embedding Models

### Popular Models

| Model | Dim | Speed | Quality | Cost |
|-------|-----:|------:|--------:|-----:|
| **text-embedding-3-small** | 1536 | ⚡⚡⚡ | ⭐⭐⭐ | $0.02 / 1M tokens |
| **text-embedding-3-large** | 3072 | ⚡⚡ | ⭐⭐⭐⭐ | $0.13 / 1M tokens |
| **all-MiniLM-L6-v2** | 384 | ⚡⚡⚡ | ⭐⭐ | Free |
| **e5-large-v2** | 1024 | ⚡⚡ | ⭐⭐⭐ | Free |

### Usage

```python
# OpenAI
from openai import OpenAI
client = OpenAI()
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Your text here"
)
embedding = response.data[0].embedding

# Sentence Transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("Your text here")
```

---

## 2. Vector Databases

### Qdrant Operations

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient("http://localhost:6333")

# Create collection
client.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Insert points
client.upsert(
    collection_name="docs",
    points=[
        PointStruct(id=1, vector=embedding, payload={"text": "..."})
    ]
)

# Search
# (client.search(query_vector=...) is deprecated since qdrant-client 1.10)
results = client.query_points(
    collection_name="docs",
    query=query_embedding,
    limit=5,
    score_threshold=0.7
).points
```

### Pinecone Operations

```python
from pinecone import Pinecone

# pinecone.init() was removed in pinecone-client 3.0
pc = Pinecone(api_key="...")
index = pc.Index("my-index")

# Upsert
index.upsert([(id, embedding, {"text": "..."})])

# Query
results = index.query(vector=query_embedding, top_k=5)
```

---

## 3. Chunking Strategies

### Fixed Size

```python
def chunk_fixed_size(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

### Semantic

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

# NOTE: langchain-experimental is being sunset (no longer maintained)
# but is still the documented home of SemanticChunker.
# Embedding-based semantic chunking (breaks at topic shifts)
splitter = SemanticChunker(OpenAIEmbeddings())
chunks = splitter.split_text(text)
```

### Markdown-Aware

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
)
chunks = splitter.split_text(markdown_text)
```

---

## 4. Retrieval Methods

### Vector Search

```python
results = vectorstore.similarity_search(query, k=5)
```

### MMR (Maximal Marginal Relevance)

```python
results = vectorstore.max_marginal_relevance_search(
    query,
    k=5,
    fetch_k=20  # Retrieve more candidates
)
```

### Similarity Score Threshold

```python
results = vectorstore.similarity_search_with_relevance_scores(
    query,
    k=5,
    score_threshold=0.7
)
```

---

## 5. Re-ranking

### Cross-Encoder

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Initial retrieval
candidates = vectorstore.similarity_search(query, k=50)

# Re-rank
pairs = [[query, doc.page_content] for doc in candidates]
scores = reranker.predict(pairs)
reranked = sorted(zip(candidates, scores),
                  key=lambda x: x[1], reverse=True)[:5]
```

### Cohere Rerank

```python
import cohere

co = cohere.Client("...")
results = co.rerank(
    model="rerank-v3.5",  # rerank-english-v2.0 is retired
    query=query,
    documents=[doc.page_content for doc in candidates],
    top_n=5
)
```

---

## 6. Hybrid Search

### Vector + BM25

```python
from rank_bm25 import BM25Okapi
import numpy as np

class HybridRetriever:
    def __init__(self, docs, embedding_model):
        self.docs = docs
        self.embedding_model = embedding_model
        self.embeddings = embedding_model.encode(docs)
        tokenized_docs = [doc.split() for doc in docs]
        self.bm25 = BM25Okapi(tokenized_docs)

    def search(self, query, alpha=0.5, k=10):
        # Vector search
        q_emb = self.embedding_model.encode(query)
        vec_scores = np.dot(q_emb, self.embeddings.T)

        # BM25 search
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Normalize and combine
        vec_scores = (vec_scores - vec_scores.min()) / (vec_scores.max() - vec_scores.min())
        bm25_scores = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min())

        combined = alpha * vec_scores + (1 - alpha) * bm25_scores
        top_indices = np.argsort(combined)[::-1][:k]

        return [(i, combined[i]) for i in top_indices]
```

### Reciprocal Rank Fusion

```python
def reciprocal_rank_fusion(results_dict, k=60):
    scores = {}
    for system, results in results_dict.items():
        for rank, (doc_id, _) in enumerate(results):
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += 1 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# Usage
rrf_results = reciprocal_rank_fusion({
    "vector": vector_results,
    "bm25": bm25_results,
    "keyword": keyword_results
})
```

---

## 7. Context Building

### Stuff (Simple Concatenation)

```python
def stuff_context(docs, query):
    context = "\n\n".join([doc.page_content for doc in docs])
    prompt = f"""Context: {context}

Question: {query}
Answer:"""
    return prompt
```

### Map-Reduce

```python
def map_reduce_context(docs, query, llm):
    # Map: Summarize each doc
    summaries = []
    for doc in docs:
        # LangChain 1.x: .predict is gone - invoke() returns a message
        summary = llm.invoke(f"Summarize: {doc.page_content}").content
        summaries.append(summary)

    # Reduce: Combine summaries
    combined = "\n\n".join(summaries)
    prompt = f"Context: {combined}\n\nQuestion: {query}\nAnswer:"
    return prompt
```

### Refine

```python
def refine_context(docs, query, llm):
    context = f"Question: {query}\n\nRelevant Context:\n{docs[0].page_content}"

    for doc in docs[1:]:
        # LangChain 1.x: .predict is gone - invoke() returns a message
        context = llm.invoke(f"""
Original Question: {query}

Current Context: {context}

New Information: {doc.page_content}

Refined Context:""").content

    return context
```

---

## 8. Prompt Templates

### Basic RAG

```python
template = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}

Question: {question}

Helpful Answer:"""
```

### With Citations

```python
template = """Answer the question using the context below. Each context item has a source ID [1], [2], etc.
Include these source IDs in your answer when referencing information.

Context:
{context}

Question: {question}

Answer (with sources):"""
```

### Multi-Query

```python
template = """You are an AI assistant. Generate 3 different search queries for the following question.
Each query should explore different aspects.

Question: {question}

Queries (one per line):"""
```

---

## 9. Evaluation Metrics

### Retrieval Metrics

```python
def precision_at_k(retrieved, relevant, k):
    retrieved_k = retrieved[:k]
    return len(set(retrieved_k) & set(relevant)) / k

def recall_at_k(retrieved, relevant, k):
    retrieved_k = retrieved[:k]
    return len(set(retrieved_k) & set(relevant)) / len(relevant)

def mrr(retrieved, relevant):
    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant:
            return 1 / (i + 1)
    return 0
```

### Generation Metrics

```python
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu

# ROUGE (the rouge-score package's API - `from rouge import Rouge`
# belongs to a different pip package)
scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
scores = scorer.score(reference, generated)
print(f"ROUGE-L: {scores['rougeL'].fmeasure:.4f}")

# BLEU
from nltk.tokenize import word_tokenize
reference = word_tokenize(reference)
generated = word_tokenize(generated)
bleu = sentence_bleu([reference], generated)
```

---

## 10. Common Issues & Solutions

### Low Retrieval Quality

| Problem | Solution |
|---------|----------|
| Irrelevant results | Increase k, use re-ranking |
| Missing info | Try hybrid search |
| Slow retrieval | Add HNSW index |
| Poor chunking | Use semantic chunking |

### Generation Issues

| Problem | Solution |
|---------|----------|
| Not using context | Improve prompt, check retrieval |
| Hallucination | Add constraints, verify sources |
| Poor formatting | Specify output format |
| Inconsistent answers | Add conversation history |

---

## 11. Performance Optimization

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text):
    return embedding_model.encode(text)
```

### Batch Processing

```python
# Batch embeddings
texts = ["text1", "text2", "text3"]
embeddings = embedding_model.encode(texts, batch_size=32)

# Batch search - VectorStore has no batch API; loop the queries
results = [vectorstore.similarity_search(q, k=5) for q in queries]
```

### Async Operations

```python
import asyncio

async def search_one(query):
    # sync vectorstore calls block the event loop - offload to a thread
    return await asyncio.to_thread(vectorstore.similarity_search, query, k=5)

async def process_queries(queries):
    tasks = [search_one(q) for q in queries]
    return await asyncio.gather(*tasks)
```

---

## 12. Production Checklist

- [ ] Vector database configured
- [ ] Embeddings cached
- [ ] Re-ranking enabled
- [ ] Context window optimized
- [ ] Prompt templates tested
- [ ] Evaluation metrics defined
- [ ] Monitoring/logging setup
- [ ] Error handling implemented
- [ ] Rate limiting configured
- [ ] Cost tracking enabled

---

## Quick Reference Commands

```bash
# Qdrant
docker run -p 6333:6333 qdrant/qdrant
uv pip install qdrant-client

# Pinecone
uv pip install pinecone-client

# OpenAI + Cohere
uv pip install openai cohere

# Sentence Transformers + BM25
uv pip install sentence-transformers rank_bm25

# LangChain
uv pip install langchain langchain-openai langchain-community \
    langchain-text-splitters langchain-experimental langchain-qdrant

# Evaluation
uv pip install rouge-score nltk

# Monitoring
uv pip install prometheus-client
```

---

**Related Cheat Sheets:**

- [CHEAT-SHEET-001: Docker](CHEAT-SHEET-001-Docker.md)
- [CHEAT-SHEET-002: Python AI](CHEAT-SHEET-002-Python-AI.md)
- [CHEAT-SHEET-004: Linux](CHEAT-SHEET-004-Linux.md)

**Next Steps:**

- [TUTORIAL-003: RAG Basics](../tutorials/TUTORIAL-003-RAG-Basics.md)
- [TUTORIAL-009: Advanced RAG Techniques](../tutorials/TUTORIAL-009-Advanced-RAG-Techniques.md)
- [LAB-002: RAG Implementation](../labs/LAB-002-RAG-Implementation.md)
- [LAB-007: Production RAG](../labs/LAB-007-Production-RAG.md)
