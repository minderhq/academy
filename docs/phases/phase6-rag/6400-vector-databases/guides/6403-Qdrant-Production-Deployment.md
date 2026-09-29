---
Document ID: 6403
Title: "6403: Qdrant Production Deployment"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Tags: ['rag', 'qdrant', 'vector-db', 'deployment']
Phase: 6
Module: 6400
---

# 6403: Qdrant Production Deployment

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Deployment Targets](#deployment-targets)
- [Docker Deployment](#docker-deployment)
- [Initial Configuration](#initial-configuration)
- [Performance Tuning](#performance-tuning)
- [Backup Strategy](#backup-strategy)
- [Monitoring](#monitoring)
- [Security Hardening](#security-hardening)
- [RAG Integration](#rag-integration)
- [Troubleshooting](#troubleshooting)
- [K3s Deployment (Optional)](#k3s-deployment-optional)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Stand up the pinned `qdrant/qdrant:v1.19.1` compose stack with a local `qdrant-net` bridge, memory limits, and a `/healthz` healthcheck — verifying readiness through `/readyz` once the container is up
- Size a deployment from host RAM with the sizing table — and enable int8 scalar quantization with `rescore=True` plus `oversampling=2.0` when the 8 GB budget runs out
- Create the 384-d COSINE `documents` collection with `HnswConfigDiff(m=32, ef_construct=200)` — and tune an existing one through `update_collection`, knowing `m` is create-time-only
- Snapshot collections with `POST /collections/{name}/snapshots` — and rotate 7-day-old `snapshots_*` sets in `backup.sh`, then recover through the snapshot `upload` endpoint in `restore.sh`
- Export per-collection `points_count` to Prometheus gauges with a `timeout=10`-guarded poller — and scrape Qdrant's `/metrics` endpoint from `prometheus.yml`
- Harden the service with `QDRANT__SERVICE__API_KEY` plus optional `JWT_RBAC` — using top-level `QDRANT__TLS__CERT`/`QDRANT__TLS__KEY` with `QDRANT__SERVICE__ENABLE_TLS=true`, or a ports-free internal-network compose

---

## Abstract
Complete guide for deploying the Qdrant high-performance vector database on any Docker-capable Linux host, NAS, or VPS for RAG and semantic search workloads.

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

services:
  qdrant:
    image: qdrant/qdrant:v1.19.1
    container_name: qdrant
    ports:
      - "6333:6333"  # REST API + Web UI (/dashboard)
      - "6334:6334"  # gRPC API
    volumes:
      - ./data:/qdrant/storage
    environment:
      # Service ports (the Web UI ships on the HTTP port under /dashboard;
      # 6335 is the internal cluster p2p port and must NOT be exposed here)
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__HTTP_PORT=6333

      # Performance tuning (keys per the config reference; Qdrant validates
      # its config at startup, so a mistyped key aborts boot instead of
      # silently falling back to a default)
      - QDRANT__STORAGE__OPTIMIZERS__INDEXING_THRESHOLD_KB=20000
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
      - QDRANT__STORAGE__PERFORMANCE__OPTIMIZER_CPU_BUDGET=2

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
      # The runtime image ships no curl/wget, so probe /healthz over bash's
      # /dev/tcp (a plain TCP connect would not validate the HTTP response)
      test: ["CMD-SHELL", "bash -c 'exec 3<>/dev/tcp/localhost/6333; printf \"GET /healthz HTTP/1.1\\r\\nHost: localhost\\r\\nConnection: close\\r\\n\\r\\n\" >&3; grep -q \"200 OK\" <&3'"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 15s
    networks:
      - qdrant-net

networks:
  # A local bridge Compose creates on demand — an `external: true` network
  # would abort `up` until you create it by hand
  qdrant-net:
    driver: bridge
EOF

# Start Qdrant
docker compose up -d

# Check logs
docker compose logs -f qdrant
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
Web UI: http://localhost:6333/dashboard
REST API: http://localhost:6333
gRPC API: http://localhost:6334
```

Remote clients should point `QDRANT_URL` at the host address; examples in this guide default to `http://localhost:6333`.

### 2. Verify Installation

```bash
export QDRANT_URL=${QDRANT_URL:-http://localhost:6333}

# Liveness + readiness probes (there is no /health path)
curl $QDRANT_URL/healthz
curl $QDRANT_URL/readyz

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

# `m` is create-time-only — on an existing collection update_collection
# accepts ef_construct and full_scan_threshold, and rejects a new m
client.update_collection(
    collection_name="documents",
    hnsw_config=HnswConfigDiff(
        ef_construct=200,
        full_scan_threshold=20000,
    )
)
```

### Quantization

Quantization trades a small amount of recall for large memory/storage savings — essential on entry-level (8 GB) hosts:

```python
# Enable scalar int8 quantization on an existing collection
from qdrant_client.models import ScalarQuantization, ScalarQuantizationConfig

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

# Search with quantized vectors + rescoring against originals — the
# QuantizationSearchParams ride inside SearchParams.quantization
from qdrant_client.models import QuantizationSearchParams, SearchParams

results = client.query_points(
    collection_name="documents",
    query=query_vector,
    search_params=SearchParams(
        quantization=QuantizationSearchParams(
            rescore=True,       # Re-rank against original vectors
            oversampling=2.0,   # Fetch 2x candidates before rescore
        )
    ),
    limit=10,
).points
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
    image: qdrant/qdrant:v1.19.1
    environment:
      # Reduce memory footprint (only keys that exist in the config
      # reference — there is no searcher_await_cache_timeout or
      # segment_size under storage.performance)
      - QDRANT__STORAGE__PERFORMANCE__OPTIMIZER_CPU_BUDGET=2
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=2

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
set -euo pipefail

BACKUP_DIR="/srv/backups/qdrant"
DATE=$(date +%Y%m%d_%H%M%S)
BASE_URL="${QDRANT_URL:-http://localhost:6333}"
COLLECTIONS=("documents" "embeddings" "knowledge_graph")

DEST="$BACKUP_DIR/snapshots_$DATE"
mkdir -p "$DEST"

for collection in "${COLLECTIONS[@]}"; do
    echo "Backing up collection: $collection"

    # Create a snapshot and read the generated file name from the response
    response=$(curl -fsS -X POST "$BASE_URL/collections/$collection/snapshots")
    snapshot=$(printf '%s' "$response" | sed -n 's/.*"name":"\([^"]*\)".*/\1/p')

    # ./data is bind-mounted at /qdrant/storage, so finished snapshots are
    # already on the host at data/snapshots/${COLLECTION}/ — a plain copy
    # beats a docker cp of the whole directory (which would duplicate every
    # previous collection's snapshots on each loop iteration)
    mkdir -p "$DEST/$collection"
    cp "/srv/qdrant/data/snapshots/$collection/$snapshot" "$DEST/$collection/"
done

# Keep only the last 7 days of backup sets
find "$BACKUP_DIR" -maxdepth 1 -name "snapshots_*" -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $DATE"
```

### 2. Restore from Backup

```bash
# /srv/qdrant/restore.sh
#!/bin/bash
set -euo pipefail

# Validate arguments before using them
if [ -z "${1:-}" ]; then
    echo "Usage: ./restore.sh YYYYMMDD_HHMMSS"
    echo "Example: ./restore.sh 20240115_143000"
    exit 1
fi

BACKUP_DIR="/srv/backups/qdrant/snapshots_$1"
BASE_URL="${QDRANT_URL:-http://localhost:6333}"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "No such backup set: $BACKUP_DIR"
    exit 1
fi

# Recovery goes through the API — no stop, no rm -rf of the live data dir
cd /srv/qdrant
docker compose up -d

# Re-upload every snapshot in the set to its collection
for file in "$BACKUP_DIR"/*/*.snapshot; do
    collection=$(basename "$(dirname "$file")")
    echo "Recovering $collection from $(basename "$file")"
    curl -fsS -X POST \
      "$BASE_URL/collections/$collection/snapshots/upload?priority=snapshot" \
      -F "snapshot=@$file"
done

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
import time

import requests
from prometheus_client import Counter, Gauge, start_http_server

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Setup metrics
qdrant_requests = Counter('qdrant_requests_total', 'Total Qdrant polls')
qdrant_errors = Counter('qdrant_errors_total', 'Failed Qdrant polls')
qdrant_points = Gauge('qdrant_points_total', 'Stored points', ['collection'])

def poll_collections():
    """Read every collection's point count and export it as a gauge."""
    # The list endpoint returns only names — details need a per-collection GET
    listing = requests.get(f"{QDRANT_URL}/collections", timeout=10).json()
    for entry in listing["result"]["collections"]:
        name = entry["name"]
        detail = requests.get(f"{QDRANT_URL}/collections/{name}", timeout=10).json()
        qdrant_points.labels(collection=name).set(detail["result"]["points_count"])
    qdrant_requests.inc()

def monitor_qdrant():
    """Poll Qdrant once a minute; failures are counted, never fatal."""
    while True:
        try:
            poll_collections()
        except (requests.RequestException, KeyError) as e:
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

The `qdrant:6333` target resolves only for containers on `qdrant-net` — attach Prometheus to the same network (or scrape the host port).

## Security Hardening

### 1. API Key Authentication

```yaml
# docker-compose.yml - Enable authentication
services:
  qdrant:
    environment:
      - QDRANT__SERVICE__API_KEY=your_secure_api_key_here
      # Optional: fine-grained JWT RBAC instead of the static key
      - QDRANT__SERVICE__JWT_RBAC=true
```

The config reference is explicit: an API key sent over an unencrypted channel is insecure — pair it with TLS (next section) or a reverse proxy.

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
      - qdrant-net

    # Access via reverse proxy (Nginx)
```

### 3. TLS/SSL Configuration

```yaml
# docker-compose.yml - Enable HTTPS
services:
  qdrant:
    environment:
      - QDRANT__SERVICE__ENABLE_TLS=true
      # cert/key live under the top-level tls config group, not service
      - QDRANT__TLS__CERT=/certs/cert.pem
      - QDRANT__TLS__KEY=/certs/key.pem
    volumes:
      - ./certs:/certs:ro
```

## RAG Integration

### 1. Document Ingestion Pipeline

```python
# rag_ingestion.py
import os
import uuid

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

class RAGIngestion:
    """RAG document ingestion for Qdrant"""

    def __init__(self, qdrant_url=None):
        self.client = QdrantClient(
            url=qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        )
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = "documents"

    @staticmethod
    def doc_id(text: str) -> str:
        """Deterministic UUID from the text — identical texts collapse to
        one point on upsert instead of colliding in a truncated hash space."""
        return str(uuid.uuid5(uuid.NAMESPACE_OID, text))

    def ingest_document(self, text: str, metadata: dict = None):
        """Ingest a document into Qdrant"""

        point = PointStruct(
            id=self.doc_id(text),
            vector=self.embedder.encode(text).tolist(),
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

        return point.id

    def ingest_batch(self, documents: list):
        """Ingest multiple documents in one encode + one upsert"""

        texts = [doc["text"] for doc in documents]
        # One batched encode call instead of a model round-trip per document
        embeddings = self.embedder.encode(texts, show_progress_bar=False)

        points = [
            PointStruct(
                id=self.doc_id(doc["text"]),
                vector=embedding.tolist(),
                payload={"text": doc["text"], **doc.get("metadata", {})}
            )
            for doc, embedding in zip(documents, embeddings)
        ]

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
    "Qdrant stores high-dimensional vectors for fast similarity search.",
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
        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold
        ).points

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

# Trade accuracy for speed per query via SearchParams.hnsw_ef
from qdrant_client.models import SearchParams

results = client.query_points(
    collection_name="documents",
    query=query_vector,
    search_params=SearchParams(hnsw_ef=50),  # Lower = faster, less accurate
    limit=5,
).points
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
  namespace: vector-db
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
        image: qdrant/qdrant:v1.19.1
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
        readinessProbe:
          httpGet:
            path: /readyz
            port: 6333
          initialDelaySeconds: 5
          periodSeconds: 10
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
  namespace: vector-db
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
  namespace: vector-db
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

## References

### Related PROJECT-OMEGA Documents

- [6401: Qdrant Setup Guide](../6401-Qdrant-Setup.md)
- [6402: Vector Database Comparison](../6402-Pinecone-vs-Weaviate.md)
- [6101: HNSW Indexing](../../6100-vector/6101-HNSW-Indexing.md)
- [6103: HNSW Tuning Guide](../../6100-vector/guides/6103-HNSW-Tuning-Guide.md)
- [6201: Hybrid Search](../../6200-retrieval/6201-Hybrid-Search.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**
- Experiment: **[EXP_6401: Vector DB](../../../../../experiments/EXP_6401_VECTOR_DB.md)**
