# 6403: Qdrant Production Deployment

## Abstract
Complete guide for deploying Qdrant high-performance vector database on any Docker-capable Linux host, NAS, or VPS for AI Engineering Curriculum RAG and semantic search operations.

## Deployment Targets

Qdrant ships as a single stateless container with one storage volume, so the same compose file works across hardware classes. Pick a target by budget and availability needs:

| Target | Best For | Notes |
|--------|----------|-------|
| Linux host + Docker (recommended) | Full control, predictable performance | Any Debian/Ubuntu/Fedora box, mini PC, or used office PC |
| NAS with Container Manager / Docker | Reusing existing storage hardware | Upload the compose file as a project/stack |
| VPS / cloud VM | Remote access, offsite data | Watch egress bandwidth for large ingest jobs |

### Sizing by Available RAM

| Host RAM | Qdrant Memory Limit | Recommended Collection Size (768d, float32) | Notes |
|----------|--------------------|----------------------------------------------|-------|
| 8 GB (entry-level) | 2 GB | Up to ~500K vectors comfortably | Enable scalar quantization beyond this |
| 16 GB | 4-6 GB | 1-3M vectors | Add on-disk payload index for large payloads |
| 32 GB+ | 8-16 GB | 5M+ vectors | Consider sharding/replication for HA |

With int8 scalar quantization (see [Quantization](#quantization)), stored vector footprint drops roughly 4x, so an 8 GB host can push past 1M vectors with a small recall trade-off.

### Resource Allocation
| Component | Minimum | Recommended | Notes |
|-----------|----------|-------------|-------|
| RAM | 1GB | 2GB | Vector storage + HNSW index |
| Storage | 10GB | 50GB | Collection growth + snapshots |
| CPU | 2 cores | 4 cores | Search performance |

## Docker Deployment

### Method 1: Docker Compose (Recommended)

```bash
# SSH into your host (or run locally)
ssh user@your-host

# Create directory
mkdir -p /srv/qdrant
cd /srv/qdrant

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3.8"

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-engineering-curriculum-qdrant
    ports:
      - "6333:6333"  # REST API
      - "6334:6334"  # gRPC API
      - "6335:6335"  # Web UI (optional)
    volumes:
      - ./data:/qdrant/storage
    environment:
      # Memory settings
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__WEB_UI_PORT=6335

      # Performance tuning
      - QDRANT__STORAGE__OPTIMIZERS__INDEXING_THRESHOLD=20000
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
      - QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZATION_THREADS=2

      # Memory limits
      - QDRANT__STORAGE__PERFORMANCE__SEARCHER_AWAIT_CACHE_TIMEOUT=30s

      # Snapshot settings
      - QDRANT__STORAGE__SNAPSHOTS_PATH=/qdrant/storage/snapshots

    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - ai-engineering-curriculum-net

networks:
  ai-engineering-curriculum-net:
    external: true
EOF

# Start Qdrant
docker-compose up -d

# Check logs
docker-compose logs -f qdrant
```

### Method 2: Portainer / NAS Container Manager (Web UI)

1. Open Portainer or Container Manager: http://localhost:9000
2. Click "Stacks" → "Add Stack" (Container Manager: "Project" → "Create")
3. Name: `qdrant`
4. Paste the docker-compose.yml content above
5. Click "Deploy the stack"

## Initial Configuration

### 1. Access Qdrant Dashboard

```text
Web UI: http://localhost:6335/dashboard
REST API: http://localhost:6333
gRPC API: http://localhost:6334
```

Remote clients should point `QDRANT_URL` at the host address; examples in this guide default to `http://localhost:6333`.

### 2. Verify Installation

```bash
export QDRANT_URL=${QDRANT_URL:-http://localhost:6333}

# Check health
curl $QDRANT_URL/health

# Check collections
curl $QDRANT_URL/collections

# Check cluster info
curl $QDRANT_URL/cluster
```

### 3. Create First Collection

```python
# qdrant_setup.py
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, HnswConfigDiff

# Connect to Qdrant
client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

# Create collection for RAG
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,  # sentence-transformers/all-MiniLM-L6-v2
        distance=Distance.COSINE,
        hnsw_config=HnswConfigDiff(
            m=32,
            ef_construct=200,
            full_scan_threshold=10000,
        )
    ),
)

# Verify
print(client.get_collection("documents"))
```

## Performance Tuning

### HNSW Configuration

```python
# HNSW tuning for self-hosted Qdrant
from qdrant_client.models import HnswConfigDiff

# For small collections (<100K vectors)
hnsw_config_small = HnswConfigDiff(
    m=16,
    ef_construct=100,
    full_scan_threshold=10000,
)

# For medium collections (100K-1M vectors)
hnsw_config_medium = HnswConfigDiff(
    m=32,
    ef_construct=200,
    full_scan_threshold=20000,
)

# For large collections (>1M vectors)
hnsw_config_large = HnswConfigDiff(
    m=64,
    ef_construct=200,
    full_scan_threshold=30000,
)

# Apply to collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE,
        hnsw_config=hnsw_config_medium
    )
)
```

### Quantization

Quantization trades a small amount of recall for large memory/storage savings — essential on entry-level (8 GB) hosts:

```python
# Enable scalar int8 quantization on an existing collection
from qdrant_client.models import ScalarQuantization, ScalarQuantizationConfig, QuantizationSearchParams

client.update_collection(
    collection_name="documents",
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type="int8",
            quantile=0.99,     # Ignore extreme outliers
            always_ram=True,   # Keep quantized vectors in RAM
        )
    ),
)

# Search with quantized vectors + rescoring against originals
results = client.search(
    collection_name="documents",
    query_vector=query_vector,
    search_params=QuantizationSearchParams(
        rescore=True,       # Re-rank against original vectors
        oversampling=2.0,   # Fetch 2x candidates before rescore
    ),
    limit=10,
)
```

Options at a glance:

| Method | Compression | Recall Impact | Use When |
|--------|-------------|---------------|----------|
| Scalar int8 | ~4x | Minimal (with rescore) | Default choice for entry-level hosts |
| Binary | ~32x | Noticeable | Huge collections, coarse filtering |
| Product (PQ) | 10-30x | Tunable | RAM is the hard constraint |

### Memory Optimization

```yaml
# docker-compose.yml - Memory optimized version
services:
  qdrant:
    image: qdrant/qdrant:latest
    environment:
      # Reduce memory footprint
      - QDRANT__STORAGE__PERFORMANCE__OPTIMIZER_CPU_BUDGET=2
      - QDRANT__STORAGE__PERFORMANCE__SEARCHER_AWAIT_CACHE_TIMEOUT=10s
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=2

      # Segment size tuning
      - QDRANT__STORAGE__PERFORMANCE__SEGMENT_SIZE=1048576  # 1MB

    deploy:
      resources:
        limits:
          memory: 1.5G
        reservations:
          memory: 512M
```

## Backup Strategy

### 1. Automated Backup Script

```bash
# /srv/qdrant/backup.sh
#!/bin/bash

BACKUP_DIR="/srv/backups/qdrant"
DATE=$(date +%Y%m%d_%H%M%S)
COLLECTIONS=("documents" "embeddings" "knowledge_graph")

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup each collection
for collection in "${COLLECTIONS[@]}"; do
    echo "Backing up collection: $collection"

    # Create snapshot
    curl -X POST "http://localhost:6333/collections/$collection/snapshots" \
      -H "Content-Type: application/json"

    # Copy snapshot to backup
    docker cp ai-engineering-curriculum-qdrant:/qdrant/storage/snapshots \
      $BACKUP_DIR/snapshots_$DATE/
done

# Keep only last 7 days of backups
find $BACKUP_DIR -name "snapshots_*" -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $DATE"
```

### 2. Restore from Backup

```bash
# /srv/qdrant/restore.sh
#!/bin/bash

BACKUP_DIR="/srv/backups/qdrant/snapshots_$1"

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_date>"
    echo "Example: ./restore.sh 20240115_143000"
    exit 1
fi

# Stop Qdrant
cd /srv/qdrant
docker-compose down

# Restore data
rm -rf ./data/*
cp -r $BACKUP_DIR/* ./data/

# Start Qdrant
docker-compose up -d

echo "Restore completed from: $1"
```

### 3. Schedule with Cron

1. Install the backup script: `chmod +x /srv/qdrant/backup.sh`
2. Edit crontab: `crontab -e`
3. Add a daily 2:00 AM entry with error logging:

```cron
0 2 * * * /srv/qdrant/backup.sh >> /var/log/qdrant-backup.log 2>&1
```

NAS users can schedule the same script through Container Manager / Task Scheduler instead of cron.

## Monitoring

### 1. Metrics Endpoint

```python
# qdrant_monitoring.py
import os
import requests
from prometheus_client import Counter, Gauge, start_http_server
import time

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Setup metrics
qdrant_requests = Counter('qdrant_requests_total', 'Total Qdrant requests')
qdrant_errors = Counter('qdrant_errors_total', 'Qdrant errors')
qdrant_vectors = Gauge('qdrant_vectors_total', 'Total vectors', ['collection'])
qdrant_memory = Gauge('qdrant_memory_bytes', 'Qdrant memory usage')

def monitor_qdrant():
    """Monitor Qdrant metrics"""

    while True:
        try:
            # Get collection info
            response = requests.get(f"{QDRANT_URL}/collections")
            collections = response.json()["result"]["collections"]

            for collection in collections:
                name = collection["name"]
                vectors_count = collection["vectors_count"]
                qdrant_vectors.labels(collection=name).set(vectors_count)

                qdrant_requests.inc()

        except Exception as e:
            qdrant_errors.inc()
            print(f"Error: {e}")

        time.sleep(60)

if __name__ == "__main__":
    # Start metrics server
    start_http_server(8000)
    print("Metrics server started on port 8000")

    # Start monitoring
    monitor_qdrant()
```

### 2. Prometheus Integration

```yaml
# Add to prometheus.yml
scrape_configs:
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    metrics_path: /metrics
```

## Security Hardening

### 1. API Key Authentication

```yaml
# docker-compose.yml - Enable authentication
services:
  qdrant:
    environment:
      - QDRANT__SERVICE__API_KEY=your_secure_api_key_here
      - QDRANT__SERVICE__JWT_RSecret=your_jwt_secret_here
```

```python
# Use API key in Python
import os
from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key="your_secure_api_key_here",
)
```

### 2. Network Isolation

```yaml
# docker-compose.yml - Internal only (no external ports)
services:
  qdrant:
    # Remove ports section, only use internal network
    networks:
      - ai-engineering-curriculum-net

    # Access via reverse proxy (Nginx)
```

### 3. TLS/SSL Configuration

```yaml
# docker-compose.yml - Enable HTTPS
services:
  qdrant:
    environment:
      - QDRANT__SERVICE__TLS_CERT=/certs/cert.pem
      - QDRANT__SERVICE__TLS_KEY=/certs/key.pem
    volumes:
      - ./certs:/certs:ro
```

## RAG Integration

### 1. Document Ingestion Pipeline

```python
# rag_ingestion.py
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import hashlib

class RAGIngestion:
    """RAG document ingestion for Qdrant"""

    def __init__(self, qdrant_url=None):
        self.client = QdrantClient(
            url=qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        )
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = "documents"

    def ingest_document(self, text: str, metadata: dict = None):
        """Ingest a document into Qdrant"""

        # Generate ID
        doc_id = int(hashlib.md5(text.encode()).hexdigest(), 16) % 10**8

        # Generate embedding
        embedding = self.embedder.encode(text).tolist()

        # Create point
        point = PointStruct(
            id=doc_id,
            vector=embedding,
            payload={
                "text": text,
                **(metadata or {})
            }
        )

        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection,
            points=[point]
        )

        return doc_id

    def ingest_batch(self, documents: list):
        """Ingest multiple documents"""

        points = []
        for doc in documents:
            text = doc.get("text")
            metadata = doc.get("metadata", {})

            doc_id = int(hashlib.md5(text.encode()).hexdigest(), 16) % 10**8
            embedding = self.embedder.encode(text).tolist()

            points.append(PointStruct(
                id=doc_id,
                vector=embedding,
                payload={"text": text, **metadata}
            ))

        # Batch upsert
        self.client.upsert(
            collection_name=self.collection,
            points=points
        )

        print(f"Ingested {len(points)} documents")

# Usage
ingestion = RAGIngestion()

# Ingest single document
ingestion.ingest_document(
    "ai-engineering-curriculum is an AI infrastructure project.",
    metadata={"source": "README", "category": "project"}
)

# Ingest batch
documents = [
    {"text": "Qdrant is a vector database.", "metadata": {"source": "docs"}},
    {"text": "RAG combines retrieval with generation.", "metadata": {"source": "docs"}},
]
ingestion.ingest_batch(documents)
```

### 2. Semantic Search

```python
# rag_search.py
import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGSearch:
    """Semantic search using Qdrant"""

    def __init__(self, qdrant_url=None):
        self.client = QdrantClient(
            url=qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        )
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = "documents"

    def search(self, query: str, limit: int = 5, score_threshold: float = 0.5):
        """Search for relevant documents"""

        # Generate query embedding
        query_vector = self.embedder.encode(query).tolist()

        # Search Qdrant
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )

        # Format results
        formatted = []
        for result in results:
            formatted.append({
                "text": result.payload.get("text"),
                "score": result.score,
                "metadata": {k: v for k, v in result.payload.items() if k != "text"}
            })

        return formatted

# Usage
search = RAGSearch()
results = search.search("What is Qdrant?")
for r in results:
    print(f"[{r['score']:.3f}] {r['text']}")
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```text
Error: Cannot allocate memory
```

**Solution:**
```yaml
# Reduce memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
```

On an 8 GB host, also enable scalar quantization (see above) to cut vector memory demand.

#### 2. Slow Search Performance

```python
# Check HNSW configuration
collection_info = client.get_collection("documents")
print(collection_info.config.params.vectors.hnsw_config)

# Adjust ef_search for faster queries
results = client.search(
    collection_name="documents",
    query_vector=query,
    hnsw_ef=50,  # Lower = faster, less accurate
)
```

#### 3. High CPU Usage

```yaml
# Limit CPU usage
deploy:
  resources:
    limits:
      cpus: '2'
```

## K3s Deployment (Optional)

```yaml
# k8s-qdrant.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: ai-engineering-curriculum
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
          name: rest
        - containerPort: 6334
          name: grpc
        env:
        - name: QDRANT__SERVICE__GRPC_PORT
          value: "6334"
        - name: QDRANT__SERVICE__HTTP_PORT
          value: "6333"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: storage
          mountPath: /qdrant/storage
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: qdrant-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qdrant-pvc
  namespace: ai-engineering-curriculum
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: local-path
  resources:
    requests:
      storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: ai-engineering-curriculum
spec:
  selector:
    app: qdrant
  ports:
  - port: 6333
    targetPort: 6333
    name: rest
  - port: 6334
    targetPort: 6334
    name: grpc
  type: ClusterIP
```


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [6401: Qdrant Setup](../6401-Qdrant-Setup.md)
- [6101: HNSW Indexing](../../6100-Vector/6101-HNSW-Indexing.md)
- [6103: HNSW Tuning Guide](../../6100-Vector/guides/6103-HNSW-Tuning-Guide.md)
- [6201: Hybrid Search](../../6200-retrieval/6201-Hybrid-Search.md)
- [EXP_6401: Vector DB](../../../../../experiments/EXP_6401_VECTOR_DB.md)

**Last Updated:** 2026-09-24
