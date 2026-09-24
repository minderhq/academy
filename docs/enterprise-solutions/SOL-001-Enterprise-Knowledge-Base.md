# SOL-001: Enterprise Knowledge Base - Complete Implementation

## Overview

End-to-end implementation guide for building an enterprise knowledge base using RAG (Retrieval-Augmented Generation) with Qdrant vector database and Llama 2.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ENTERPRISE KNOWLEDGE BASE                │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│              │      │              │      │              │
│  Document    │─────▶│  Ingestion   │─────▶│   Qdrant     │
│  Sources     │      │  Pipeline    │      │  Vector DB   │
│              │      │              │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
                            │                      │
                            │                      ▼
                            │              ┌──────────────┐
                            │              │              │
                            │              │  Semantic    │
                            │              │  Search      │
                            │              │              │
                            │              └──────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐      ┌──────────────┐
                     │              │      │              │
                     │   Metadata   │      │  Retrieved   │
                     │   Store      │      │  Context     │
                     │  (Postgres)  │      │              │
                     │              │      └──────────────┘
                     └──────────────┘               │
                                                   ▼
                                            ┌──────────────┐
                                            │              │
                                            │  Llama 2 7B  │
                                            │  (4-bit)     │
                                            │              │
                                            └──────────────┘
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │              │
                                            │  Answer +    │
                                            │  Sources     │
                                            │              │
                                            └──────────────┘
```

---

## Part 1: Infrastructure Setup

### 1.1 Hardware Requirements

**Minimum (Homelab):**
- CPU: a mini-PC or equivalent (4+ cores)
- RAM: 16GB
- Storage: 500GB SSD
- GPU: 11GB VRAM GPU (for Llama 2 7B 4-bit)

**Recommended:**
- CPU: 8+ cores
- RAM: 32GB
- Storage: 1TB NVMe SSD
- GPU: RTX 3080/4070 12GB+

### 1.2 Software Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.7.0
    container_name: qdrant
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC API
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped

  # PostgreSQL for metadata
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: knowledge_base
      POSTGRES_USER: kb_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  # Redis for caching
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - ./redis_data:/data
    restart: unless-stopped
```

### 1.3 Deploy Infrastructure

```bash
# Create project directory
mkdir enterprise-kb && cd enterprise-kb

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
[yaml content from above]
EOF

# Start services
docker-compose up -d

# Verify services
docker ps
curl http://localhost:6333/health  # Qdrant health check
```

---

## Part 2: Document Ingestion Pipeline

### 2.1 Python Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

```txt
# requirements.txt
qdrant-client==1.7.0
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
langchain==0.1.0
langchain-community==0.0.10
sentence-transformers==2.3.1
transformers==4.36.0
accelerate==0.25.0
bitsandbytes==0.41.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
aiofiles==23.2.1
pypdf==3.17.4
python-docx==1.1.0
openpyxl==3.1.2
python-pptx==0.6.23
```

### 2.2 Document Processor

```python
# ingestion/document_processor.py
import os
import hashlib
from typing import List, Dict
from pathlib import Path
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    TextLoader
)
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sqlalchemy import create_engine, Column, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
Base = declarative_base()

class DocumentMetadata(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Float)
    chunk_count = Column(Float)
    checksum = Column(String, unique=True)

# Initialize components
engine = create_engine("postgresql://kb_user:secure_password@localhost:5432/knowledge_base")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

class DocumentProcessor:
    """
    Process and index documents for enterprise knowledge base
    """

    def __init__(self):
        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize Qdrant client
        self.qdrant = QdrantClient(url="http://localhost:6333")

        # Initialize text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        # Create collection if not exists
        self._create_collection()

    def _create_collection(self):
        """Create Qdrant collection for documents"""

        try:
            self.qdrant.create_collection(
                collection_name="enterprise_docs",
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 dimension
                    distance=Distance.COSINE
                )
            )
            print("✓ Created collection: enterprise_docs")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"Error creating collection: {e}")

    def process_directory(self, directory: str) -> Dict:
        """
        Process all documents in a directory

        Args:
            directory: Path to directory containing documents

        Returns:
            Summary of processed documents
        """

        results = {
            "success": [],
            "failed": [],
            "skipped": [],
            "total_chunks": 0
        }

        # Supported file types
        loaders = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".pptx": UnstructuredPowerPointLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".txt": TextLoader
        }

        # Walk through directory
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()

                # Check if file type is supported
                if file_ext not in loaders:
                    results["skipped"].append({
                        "file": file_path,
                        "reason": f"Unsupported file type: {file_ext}"
                    })
                    continue

                # Process document
                try:
                    result = self.process_document(file_path)
                    results["success"].append(result)
                    results["total_chunks"] += result["chunk_count"]
                    print(f"✓ Processed: {file_path} ({result['chunk_count']} chunks)")

                except Exception as e:
                    results["failed"].append({
                        "file": file_path,
                        "error": str(e)
                    })
                    print(f"✗ Failed: {file_path} - {e}")

        return results

    def process_document(self, file_path: str) -> Dict:
        """
        Process a single document

        Args:
            file_path: Path to document

        Returns:
            Processing result with metadata
        """

        # Calculate checksum
        checksum = self._calculate_checksum(file_path)

        # Check if already processed
        session = SessionLocal()
        existing = session.query(DocumentMetadata).filter_by(
            checksum=checksum
        ).first()

        if existing:
            session.close()
            return {
                "file_path": file_path,
                "document_id": existing.id,
                "chunk_count": existing.chunk_count,
                "status": "already_exists"
            }

        # Load document
        file_ext = Path(file_path).suffix.lower()
        loader_map = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".pptx": UnstructuredPowerPointLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".txt": TextLoader
        }

        loader = loader_map[file_ext](file_path)
        documents = loader.load()

        # Split documents into chunks
        chunks = self.splitter.split_documents(documents)

        # Create embeddings
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedder.encode(texts)

        # Generate document ID
        doc_id = hashlib.md5(file_path.encode()).hexdigest()

        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                PointStruct(
                    id=f"{doc_id}_{i}",
                    vector=embedding.tolist(),
                    payload={
                        "text": chunk.page_content,
                        "document_id": doc_id,
                        "chunk_id": i,
                        "source": file_path,
                        "filename": Path(file_path).name,
                        "file_type": file_ext.replace(".", ""),
                        "page": chunk.metadata.get("page", 0)
                    }
                )
            )

        # Insert into Qdrant
        self.qdrant.upsert(
            collection_name="enterprise_docs",
            points=points
        )

        # Store metadata in PostgreSQL
        metadata = DocumentMetadata(
            id=doc_id,
            filename=Path(file_path).name,
            file_path=file_path,
            file_type=file_ext.replace(".", ""),
            file_size=os.path.getsize(file_path),
            chunk_count=len(chunks),
            checksum=checksum
        )

        session.add(metadata)
        session.commit()
        session.close()

        return {
            "document_id": doc_id,
            "file_path": file_path,
            "chunk_count": len(chunks),
            "status": "success"
        }

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum for deduplication"""

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

# Usage
if __name__ == "__main__":
    processor = DocumentProcessor()
    results = processor.process_directory("./documents")
    print(f"\nProcessing complete:")
    print(f"  Success: {len(results['success'])}")
    print(f"  Failed: {len(results['failed'])}")
    print(f"  Skipped: {len(results['skipped'])}")
    print(f"  Total chunks: {results['total_chunks']}")
```

---

## Part 3: Query API

### 3.1 FastAPI Application

```python
# api/main.py
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from ingestion.document_processor import DocumentProcessor
from retrieval.retriever import KnowledgeRetriever

app = FastAPI(
    title="Enterprise Knowledge Base API",
    description="RAG-based enterprise knowledge base",
    version="1.0.0"
)

# Initialize components
processor = DocumentProcessor()
retriever = KnowledgeRetriever()

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    filters: Optional[dict] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    retrieval_time: float

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Query the knowledge base

    Args:
        request: Query request with question and parameters

    Returns:
        Answer with sources
    """

    try:
        result = retriever.query(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a new document

    Args:
        file: Uploaded document file

    Returns:
        Processing result
    """

    # Save file
    file_path = f"./temp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Process document
    try:
        result = processor.process_document(file_path)
        return result
    finally:
        # Cleanup temp file
        os.remove(file_path)

@app.get("/api/v1/documents")
async def list_documents():
    """List all processed documents"""

    from sqlalchemy.orm import Session
    from ingestion.document_processor import SessionLocal, DocumentMetadata

    session = SessionLocal()
    documents = session.query(DocumentMetadata).all()
    session.close()

    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "upload_date": doc.upload_date.isoformat(),
                "chunk_count": doc.chunk_count
            }
            for doc in documents
        ]
    }

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks"""

    try:
        # Delete from Qdrant
        processor.qdrant.delete(
            collection_name="enterprise_docs",
            points_selector=[f"{document_id}_*"]
        )

        # Delete from PostgreSQL
        from sqlalchemy.orm import Session
        from ingestion.document_processor import SessionLocal, DocumentMetadata

        session = SessionLocal()
        doc = session.query(DocumentMetadata).filter_by(id=document_id).first()
        if doc:
            session.delete(doc)
            session.commit()

        session.close()
        return {"status": "deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3.2 Knowledge Retriever

```python
# retrieval/retrieever.py
import time
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

class KnowledgeRetriever:
    """
    RAG-based knowledge retriever
    """

    def __init__(self):
        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize Qdrant client
        self.qdrant = QdrantClient(url="http://localhost:6333")

        # Initialize LLM
        model_id = "meta-llama/Llama-2-7b-chat-hf"
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            load_in_4bit=True
        )

        # Create generation pipeline
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=512,
            temperature=0.1,
            do_sample=True
        )

    def query(self, query: str, top_k: int = 5, filters: dict = None) -> Dict:
        """
        Query knowledge base and generate answer

        Args:
            query: User question
            top_k: Number of documents to retrieve
            filters: Optional filters for retrieval

        Returns:
            Answer with sources
        """

        start_time = time.time()

        # Step 1: Retrieve relevant documents
        query_vector = self.embedder.encode(query).tolist()
        search_results = self.qdrant.search(
            collection_name="enterprise_docs",
            query_vector=query_vector,
            query_filter=filters,
            limit=top_k,
            score_threshold=0.70
        )

        if not search_results:
            return {
                "answer": "I couldn't find relevant information to answer your question.",
                "sources": [],
                "retrieval_time": time.time() - start_time
            }

        # Step 2: Build context
        context = self._build_context(search_results)

        # Step 3: Generate answer
        prompt = self._build_prompt(query, context)
        answer = self._generate_answer(prompt)

        # Step 4: Format sources
        sources = self._format_sources(search_results)

        return {
            "answer": answer,
            "sources": sources,
            "retrieval_time": time.time() - start_time
        }

    def _build_context(self, search_results: List) -> str:
        """Build context from retrieved documents"""

        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(
                f"[Document {i}] {result.payload['text']}\n"
                f"Source: {result.payload['filename']}"
            )

        return "\n\n".join(context_parts)

    def _build_prompt(self, query: str, context: str) -> str:
        """Build prompt for LLM"""

        return f"""You are a helpful assistant for an enterprise knowledge base.
Use the following retrieved documents to answer the user's question accurately.
If the answer cannot be found in the documents, say so.

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""

    def _generate_answer(self, prompt: str) -> str:
        """Generate answer using LLM"""

        outputs = self.generator(prompt, max_new_tokens=512)
        answer = outputs[0]["generated_text"]

        # Extract just the answer part
        if "ANSWER:" in answer:
            answer = answer.split("ANSWER:")[-1].strip()

        return answer

    def _format_sources(self, search_results: List) -> List[Dict]:
        """Format sources for response"""

        sources = []
        for result in search_results:
            sources.append({
                "filename": result.payload["filename"],
                "file_type": result.payload["file_type"],
                "relevance": round(result.score, 3)
            })

        return sources
```

---

## Part 4: Frontend Interface

### 4.1 HTML/JavaScript Interface

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise Knowledge Base</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #0056b3;
        }
        .answer {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .sources {
            margin-top: 20px;
        }
        .source {
            background: #e9ecef;
            padding: 10px;
            margin-bottom: 5px;
            border-radius: 4px;
            font-size: 14px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 Enterprise Knowledge Base</h1>

        <div class="search-box">
            <input type="text" id="query" placeholder="Ask a question...">
            <button onclick="search()">Search</button>
        </div>

        <div id="results"></div>
    </div>

    <script>
        async function search() {
            const query = document.getElementById('query').value;
            const resultsDiv = document.getElementById('results');

            if (!query) return;

            resultsDiv.innerHTML = '<div class="loading">Searching...</div>';

            try {
                const response = await fetch('/api/v1/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query, top_k: 5 })
                });

                const data = await response.json();

                let html = `<div class="answer">
                    <strong>Answer:</strong><br><br>
                    ${data.answer}
                </div>`;

                if (data.sources.length > 0) {
                    html += '<div class="sources"><strong>Sources:</strong>';
                    data.sources.forEach(source => {
                        html += `<div class="source">
                            📄 ${source.filename} (${source.file_type})
                            - Relevance: ${(source.relevance * 100).toFixed(1)}%
                        </div>`;
                    });
                    html += '</div>';
                }

                html += `<div style="margin-top: 20px; color: #666; font-size: 14px;">
                    ⏱️ Retrieved in ${data.retrieval_time.toFixed(2)}s
                </div>`;

                resultsDiv.innerHTML = html;

            } catch (error) {
                resultsDiv.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            }
        }

        // Allow Enter key to search
        document.getElementById('query').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') search();
        });
    </script>
</body>
</html>
```

---

## Part 5: Deployment

### 5.1 Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_HOST=qdrant
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - qdrant
      - postgres
      - redis
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: knowledge_base
      POSTGRES_USER: kb_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/usr/share/nginx/html
    depends_on:
      - api
    restart: unless-stopped
```

### 5.2 Deploy Commands

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f api

# Scale API if needed
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

---

## Part 6: Monitoring

### 6.1 Health Checks

```python
# api/monitoring.py
from fastapi import APIRouter
from qdrant_client import QdrantClient
import psutil

router = APIRouter()

@router.get("/health")
async def health_check():
    """System health check"""

    # Check Qdrant
    qdrant = QdrantClient(url="http://localhost:6333")
    qdrant_health = qdrant.get_collections()

    # System stats
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        "status": "healthy",
        "qdrant": {
            "status": "connected",
            "collections": len(qdrant_health.collections)
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        }
    }
```

---

**Solution ID:** SOL-001
**Related:** [UC-002: RAG Applications](../use-cases/UC-002-RAG-Applications.md), [6201: Hybrid Search](../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md), [6401: Qdrant Setup](../phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md)
