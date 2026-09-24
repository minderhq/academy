# 6403: Qdrant Vector Database Deployment for Synology NAS

## Abstract
Complete guide for deploying Qdrant high-performance vector database on Synology DS720+ for PROJECT-OMEGA RAG and semantic search operations.

## Hardware Requirements

### Synology DS720+ Specifications
```
CPU: Intel Celeron J4125 (4 cores @ 2.0 GHz)
RAM: 6GB (expandable to 18GB)
Storage: 2x 3.5" bays (supports RAID 0/1)
Network: 1GbE (internal cluster via 2.5Gbps switch)
```

### Resource Allocation
| Component | Minimum | Recommended | Notes |
|-----------|----------|-------------|-------|
| RAM | 1GB | 2GB | Vector storage + HNSW index |
| Storage | 10GB | 50GB | Collection growth + snapshots |
| CPU | 2 cores | 4 cores | Search performance |

## Docker Deployment

### Method 1: Docker Compose (Recommended)

```bash
# SSH into Synology
ssh admin@192.168.1.100

# Create directory
mkdir -p /volume1/docker/qdrant
cd /volume1/docker/qdrant

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3.8"

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: project-omega-qdrant
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
      - project-omega-net

networks:
  project-omega-net:
    external: true
EOF

# Start Qdrant
docker-compose up -d

# Check logs
docker-compose logs -f qdrant
```

### Method 2: Portainer (Web UI)

1. Open Portainer: http://192.168.1.100:9000
2. Click "Stacks" → "Add Stack"
3. Name: `qdrant`
4. Paste the docker-compose.yml content above
5. Click "Deploy the stack"

## Initial Configuration

### 1. Access Qdrant Dashboard

```
Web UI: http://192.168.1.100:6335/dashboard
REST API: http://192.168.1.100:6333
gRPC API: http://192.168.1.100:6334
```

### 2. Verify Installation

```bash
# Check health
curl http://192.168.1.100:6333/health

# Check collections
curl http://192.168.1.100:6333/collections

# Check cluster info
curl http://192.168.1.100:6333/cluster
```

### 3. Create First Collection

```python
# qdrant_setup.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, HnswConfigDiff

# Connect to Qdrant
client = QdrantClient(url="http://192.168.1.100:6333")

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
# HNSW tuning for Synology DS720+
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
# /volume1/docker/qdrant/backup.sh
#!/bin/bash

BACKUP_DIR="/volume1/backup/qdrant"
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
    docker cp project-omega-qdrant:/qdrant/storage/snapshots \
      $BACKUP_DIR/snapshots_$DATE/
done

# Keep only last 7 days of backups
find $BACKUP_DIR -name "snapshots_*" -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $DATE"
```

### 2. Restore from Backup

```bash
# /volume1/docker/qdrant/restore.sh
#!/bin/bash

BACKUP_DIR="/volume1/backup/qdrant/snapshots_$1"

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_date>"
    echo "Example: ./restore.sh 20240115_143000"
    exit 1
fi

# Stop Qdrant
cd /volume1/docker/qdrant
docker-compose down

# Restore data
rm -rf ./data/*
cp -r $BACKUP_DIR/* ./data/

# Start Qdrant
docker-compose up -d

echo "Restore completed from: $1"
```

### 3. Schedule with Synology Task Scheduler

1. Control Panel → Task Scheduler → Create → Scheduled Task → User-defined Script
2. General: "Qdrant Backup"
3. Schedule: Daily at 2:00 AM
4. Task Settings: Run as root, copy backup script
5. Settings: Send email notification on error

## Monitoring

### 1. Metrics Endpoint

```python
# qdrant_monitoring.py
import requests
from prometheus_client import Counter, Gauge, start_http_server
import time

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
            response = requests.get("http://192.168.1.100:6333/collections")
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
from qdrant_client import QdrantClient

client = QdrantClient(
    url="http://192.168.1.100:6333",
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
      - project-omega-net

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
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import hashlib

class RAGIngestion:
    """RAG document ingestion for Qdrant"""

    def __init__(self, qdrant_url="http://192.168.1.100:6333"):
        self.client = QdrantClient(url=qdrant_url)
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
    "PROJECT-OMEGA is an AI infrastructure project.",
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
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGSearch:
    """Semantic search using Qdrant"""

    def __init__(self, qdrant_url="http://192.168.1.100:6333"):
        self.client = QdrantClient(url=qdrant_url)
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

```
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
  namespace: project-omega
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
  namespace: project-omega
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: nfs-synology
  resources:
    requests:
      storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: project-omega
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
- [6401: Qdrant Setup](../../6401-Qdrant-Setup.md)
- [6101: HNSW Indexing](../../6100-Vector/6101-HNSW-Indexing.md)
- [6103: HNSW Tuning Guide](../../6100-Vector/guides/6103-HNSW-Tuning-Guide.md)
- [6201: Hybrid Search](../../6200-retrieval/6201-Hybrid-Search.md)
- [EXP_6401: Vector DB](../../../../../experiments/EXP_6401_VECTOR_DB.md)
