---
Document ID: TEMPLATE-003-RAG-System
Title: "PROJECT TEMPLATE: RAG System"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Beginner
---

# PROJECT TEMPLATE: RAG System

Build a Retrieval-Augmented Generation system from scratch.

## Project Structure

```text
rag-system/
├── README.md
├── pyproject.toml
├── uv.lock
├── config/
│   ├── embedding_config.yaml
│   ├── vectorstore_config.yaml
│   └── llm_config.yaml
├── src/
│   ├── __init__.py
│   ├── embeddings.py       # Embedding models
│   ├── vectorstore.py      # Vector database
│   ├── retriever.py        # Retrieval logic
│   ├── generator.py        # LLM generation
│   └── pipeline.py         # RAG pipeline
├── data/
│   └── documents/
│       ├── doc1.txt
│       └── doc2.txt
├── api/
│   └── main.py             # FastAPI server
└── tests/
    └── test_rag.py
```

## Features

- Document ingestion
- Embedding generation
- Vector storage (Qdrant/ChromaDB/Milvus)
- Hybrid retrieval (dense + sparse)
- Context-aware generation
- REST API

## Quick Start

1. Add documents to `data/documents/`

2. Configure vector store in `config/vectorstore_config.yaml`:
```yaml
type: "qdrant"  # or "chroma", "milvus"
collection_name: "documents"
embedding_model: "all-MiniLM-L6-v2"
```

3. Build index:
```bash
python -m src.pipeline build-index
```

4. Run API:
```bash
uvicorn api.main:app --reload
```

5. Query:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'
```

## Components

### Embeddings
- SentenceTransformers
- OpenAI embeddings
- Custom models

### Vector Stores
- Qdrant
- ChromaDB
- Milvus
- FAISS (local)

### Retrieval
- Dense search
- Sparse search
- Hybrid search
- Re-ranking

### Generation
- OpenAI GPT
- Local LLMs
- Context injection

## Advanced Features

- Multi-document retrieval
- Metadata filtering
- Query expansion
- Citation generation

---

**Difficulty:** Intermediate
**Estimated Time:** 6-10 hours
**Skills:** Vector databases, Embeddings, RAG
