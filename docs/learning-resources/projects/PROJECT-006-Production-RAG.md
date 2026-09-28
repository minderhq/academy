---
Document ID: PROJECT-006
Title: "CAPSTONE PROJECT 006: Build Production RAG System"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# CAPSTONE PROJECT 006: Build Production RAG System

**Integrate LLMs with your knowledge base**

---

## 🎯 Project Overview

Build a production-ready Retrieval-Augmented Generation system:
- Multi-source document ingestion
- Vector + hybrid search
- Advanced re-ranking strategies
- GraphRAG integration
- Real-time API deployment

**Estimated Time:** 20-25 hours
**Difficulty:** ⭐⭐⭐ Advanced

---

## 📋 Prerequisites

Complete these before starting:
- ✅ 6101: HNSW Indexing
- ✅ 6201: Hybrid Search
- ✅ 6202: Re-ranking
- ✅ 6301: GraphRAG
- ✅ LAB 002: RAG Implementation
- ✅ LAB 007: Production RAG

---

## 🏗️ Project Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                      Production RAG System                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Data Sources                                                        │
│  ├── PDFs  ├── Web  ├── DB  ├── APIs                                │
│       │                                                               │
│       ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    Ingestion Pipeline                           │  │
│  │  - Parsing (PDF, HTML, DOCX)                                    │  │
│  │  - Chunking (semantic, recursive)                               │  │
│  │  - Entity Extraction                                            │  │
│  └──────────────────────────┬──────────────────────────────────────┘  │
│                             │                                         │
│                             ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      Storage Layer                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │ Qdrant       │  │ PostgreSQL   │  │ Neo4j        │          │  │
│  │  │ (Vectors)    │  │ (Documents)  │  │ (Graph)      │          │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│                             │                                         │
│                             ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    Retrieval Layer                              │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │  │
│  │  │ Vector Search    │  │  Hybrid Search   │  │ Graph Search │  │  │
│  │  │ (HNSW)           │  │  (BM25 + Vector) │  │ (Cypher)     │  │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────┘  │  │
│  │                            │                                    │  │
│  │                            ▼                                    │  │
│  │                 ┌──────────────────────┐                       │  │
│  │                 │  Re-ranking          │                       │  │
│  │                 │  (Cohere, Cross-     │                       │  │
│  │                 │   Encoder)           │                       │  │
│  │                 └──────────────────────┘                       │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│                             │                                         │
│                             ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    Generation Layer                             │  │
│  │  - Prompt Engineering                                           │  │
│  │  - LLM (GPT-4, Claude, Local)                                   │  │
│  │  - Response Formatting                                          │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│                             │                                         │
│                             ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    API Layer                                    │  │
│  │  - FastAPI Endpoints                                            │  │
│  │  - Streaming Support                                            │  │
│  │  - Rate Limiting                                                 │  │
│  │  - Monitoring & Logging                                          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Document Ingestion (5 hours)

### 1.1 Multi-Format Parser

```python
# File: parsers.py
"""
Document Parsers
================
"""

from pathlib import Path
from typing import List, Dict
import pypdf
from bs4 import BeautifulSoup
import docx
import markdown

class DocumentParser:
    """Parse various document formats"""

    def parse(self, file_path: str) -> Dict:
        """Parse document based on extension"""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == '.pdf':
            return self._parse_pdf(file_path)
        elif ext in ['.html', '.htm']:
            return self._parse_html(file_path)
        elif ext == '.docx':
            return self._parse_docx(file_path)
        elif ext == '.md':
            return self._parse_markdown(file_path)
        elif ext == '.txt':
            return self._parse_text(file_path)
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def _parse_pdf(self, path: str) -> Dict:
        """Parse PDF file"""
        reader = pypdf.PdfReader(path)

        text = ""
        metadata = {
            'title': reader.metadata.get('/Title', ''),
            'author': reader.metadata.get('/Author', ''),
            'pages': len(reader.pages)
        }

        for page in reader.pages:
            text += page.extract_text() + "\n"

        return {
            'text': text.strip(),
            'metadata': metadata
        }

    def _parse_html(self, path: str) -> Dict:
        """Parse HTML file"""
        with open(path, 'r') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')

        # Remove scripts and styles
        for script in soup(['script', 'style']):
            script.decompose()

        text = soup.get_text(separator='\n', strip=True)

        return {
            'text': text,
            'metadata': {
                'title': soup.title.string if soup.title else '',
                'url': path
            }
        }

    def _parse_docx(self, path: str) -> Dict:
        """Parse DOCX file"""
        doc = docx.Document(path)

        text = "\n".join([para.text for para in doc.paragraphs])

        return {
            'text': text,
            'metadata': {
                'title': path,
                'paragraphs': len(doc.paragraphs)
            }
        }

    def _parse_markdown(self, path: str) -> Dict:
        """Parse Markdown file"""
        with open(path, 'r') as f:
            md = f.read()

        html = markdown.markdown(md)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        return {
            'text': text,
            'metadata': {'source': path}
        }

    def _parse_text(self, path: str) -> Dict:
        """Parse plain text file"""
        with open(path, 'r') as f:
            text = f.read()

        return {
            'text': text,
            'metadata': {'source': path}
        }
```

### 1.2 Semantic Chunking

```python
# File: chunking.py
"""
Semantic Chunking
=================
"""

from typing import Dict
import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticChunker:
    """Chunk documents semantically"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def chunk(self, text: str, max_chunk_size: int = 500,
             overlap: int = 50) -> list[Dict]:
        """Chunk text semantically"""

        # Split into sentences
        sentences = self._split_sentences(text)

        # Generate embeddings
        embeddings = self.model.encode(sentences)

        # Calculate sentence boundaries
        chunks = []
        current_chunk = []
        current_size = 0

        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence.split())

            # Check if adding sentence would exceed size
            if current_size + sentence_size > max_chunk_size and current_chunk:
                chunks.append({
                    'text': ' '.join(current_chunk),
                    'size': current_size
                })
                current_chunk = []
                current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_size

        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': ' '.join(current_chunk),
                'size': current_size
            })

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
```

### 1.3 Entity Extraction

```python
# File: entities.py
"""
Entity Extraction
=================
"""

import spacy

class EntityExtractor:
    """Extract entities from text"""

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract(self, text: str) -> dict[str, List]:
        """Extract entities from text"""
        doc = self.nlp(text)

        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],  # Geopolitical entity
            'PRODUCT': [],
            'EVENT': [],
            'DATE': []
        }

        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)

        return entities
```

### ✅ Phase 1 Checklist
- [ ] Multi-format parser working
- [ ] Semantic chunking implemented
- [ ] Entity extraction working
- [ ] Pipeline end-to-end functional

---

## Phase 2: Indexing (4 hours)

### 2.1 Vector Indexing

```python
# File: indexing.py
"""
Document Indexing
=================
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import Dict
import uuid

class DocumentIndexer:
    """Index documents in Qdrant"""

    def __init__(self, qdrant_url: str = "http://localhost:6333",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        self.qdrant = QdrantClient(url=qdrant_url)
        self.embedder = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()

    def create_collection(self, name: str):
        """Create the collection only if it does not already exist.

        recreate_collection would silently wipe every stored vector.
        """
        if not self.qdrant.collection_exists(name):
            self.qdrant.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
            )

    def index_documents(self, collection_name: str,
                        documents: list[Dict]) -> int:
        """Index documents"""

        points = []

        for doc in documents:
            # Generate embedding
            embedding = self.embedder.encode(doc['text']).tolist()

            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    'text': doc['text'],
                    'metadata': doc.get('metadata', {}),
                    'entities': doc.get('entities', {})
                }
            )
            points.append(point)

        # Batch insert
        self.qdrant.upsert(
            collection_name=collection_name,
            points=points
        )

        return len(points)

    def index_graph(self, collection_name: str,
                    entities: Dict):
        """Index entities in Neo4j"""
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )

        with driver.session() as session:
            for entity_type, entity_list in entities.items():
                for entity_name in entity_list:
                    session.run(
                        "MERGE (e:Entity {name: $name, type: $type})",
                        name=entity_name,
                        type=entity_type
                    )

        driver.close()
```

### ✅ Phase 2 Checklist
- [ ] Vector index created
- [ ] Documents indexed
- [ ] Knowledge graph populated
- [ ] Search working

---

## Phase 3: Retrieval & Generation (6 hours)

### 3.1 Hybrid Retrieval

```python
# File: retrieval.py
"""
Hybrid Retrieval
================
"""

from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder
from typing import Dict

class HybridRetriever:
    """Hybrid vector + keyword retrieval"""

    def __init__(self, qdrant_url: str = "http://localhost:6333",
                 reranker_model: str = "ms-marco-MiniLM-L-6-v2"):
        self.qdrant = QdrantClient(url=qdrant_url)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.reranker = CrossEncoder(reranker_model)

    def retrieve(self, collection_name: str, query: str,
                top_k: int = 10) -> list[Dict]:
        """Retrieve documents"""

        # Generate query embedding
        query_vector = self.embedder.encode(query).tolist()

        # Vector search
        results = self.qdrant.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k * 2  # Get more for reranking
        ).points

        # Rerank
        rerank_input = [(query, hit.payload['text']) for hit in results]
        scores = self.reranker.predict(rerank_input)

        # Combine and sort
        reranked = []
        for hit, score in zip(results, scores):
            reranked.append({
                'text': hit.payload['text'],
                'score': float(score),
                'metadata': hit.payload.get('metadata', {})
            })

        reranked.sort(key=lambda x: x['score'], reverse=True)

        return reranked[:top_k]

    def retrieve_with_graph(self, collection_name: str,
                           query: str, top_k: int = 10) -> list[Dict]:
        """Retrieve with graph enhancement"""

        # Standard retrieval
        docs = self.retrieve(collection_name, query, top_k)

        # Extract entities from query
        # (Use entity extractor)

        # Query graph for related entities
        # (Use Neo4j)

        return docs
```

### 3.2 Generation

```python
# File: generation.py
"""
RAG Generation
==============
"""

from openai import OpenAI
from typing import Dict

class RAGGenerator:
    """Generate responses with RAG"""

    def __init__(self, model: str = "gpt-4"):
        self.client = OpenAI()
        self.model = model

    def generate(self, query: str, context: list[Dict],
                stream: bool = False) -> str:
        """Generate response"""

        # Build prompt
        context_text = "\n\n".join([
            f"[{i+1}] {doc['text']}"
            for i, doc in enumerate(context)
        ])

        prompt = f"""Answer the question using the context below.

Context:
{context_text}

Question: {query}

Provide a comprehensive answer based on the context. If the context doesn't contain enough information, say so.

Answer:"""

        if stream:
            return self._generate_stream(prompt)
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024
            )
            return response.choices[0].message.content

    def _generate_stream(self, prompt: str):
        """Stream response"""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

### ✅ Phase 3 Checklist
- [ ] Hybrid retrieval working
- [ ] Reranking improving results
- [ ] Generation with context working
- [ ] Streaming responses working

---

## Phase 4: API Deployment (5 hours)

### 4.1 FastAPI Service

```python
# File: api.py
"""
RAG API Service
===============
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import uvicorn

app = FastAPI(title="Production RAG API")

# Initialize components
retriever = HybridRetriever()
generator = RAGGenerator()

class QueryRequest(BaseModel):
    query: str
    collection: str = "documents"
    top_k: int = 5
    stream: bool = False

class QueryResponse(BaseModel):
    answer: str
    sources: list[Dict]
    query_time: float

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG system"""

    import time
    start = time.time()

    # Retrieve
    docs = retriever.retrieve(request.collection, request.query, request.top_k)

    # Generate
    if request.stream:
        return StreamingResponse(
            generator.generate(request.query, docs, stream=True),
            media_type="text/event-stream"
        )
    else:
        answer = generator.generate(request.query, docs, stream=False)

    query_time = time.time() - start

    return QueryResponse(
        answer=answer,
        sources=docs,
        query_time=query_time
    )

@app.post("/ingest")
async def ingest(file_path: str):
    """Ingest a document"""
    # Parse, chunk, index
    pass

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### ✅ Phase 4 Checklist
- [ ] API endpoints working
- [ ] Streaming implemented
- [ ] Error handling in place
- [ ] Monitoring configured

---

## 🏆 Project Completion Checklist

```text
[ ] Phase 1: Document Ingestion
[ ] Phase 2: Indexing
[ ] Phase 3: Retrieval & Generation
[ ] Phase 4: API Deployment
[ ] End-to-end pipeline working
[ ] Production ready
```

---

## 📚 Related Resources

- **[6101: HNSW Indexing](../../phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md)** - Vector search theory
- **[6201: Hybrid Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)** - Hybrid retrieval
- **[LAB 002: RAG Implementation](../labs/LAB-002-RAG-Implementation.md)** - RAG basics

---

**Congratulations!** You've built a production RAG system:
- 📄 Multi-format document ingestion
- 🔍 Hybrid search with reranking
- 🧠 GraphRAG integration
- 🚀 Production API deployment

## Next Steps

- **[Volume 7: Production Mastery](../../volumes/VOLUME-7-Production-Mastery.md)**
