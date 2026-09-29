---
Document ID: LAB-009
Title: "LAB-009: Production Deployment"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
---

# LAB-009: Production Deployment

**Deploy AI Systems at Scale** - Complete production deployment pipeline

---

## 📋 Lab Overview

**Time:** 8-10 hours
**Difficulty:** ⭐⭐⭐⭐ Expert
**Prerequisites:**
- LAB-001: Docker & LLM
- LAB-002: RAG Implementation
- LAB-007: Production RAG
- LAB-008: Agent Fleet
- Basic knowledge of Docker and Linux

**Learning Objectives:**
- Deploy RAG system to production with SSL
- Set up Nginx reverse proxy
- Configure CI/CD pipeline
- Deploy to Kubernetes
- Set up monitoring and observability
- Implement cost optimization
- Handle production debugging

---

## 🎯 Part 1: SSL/TLS Configuration (90 minutes)

### Step 1.0: Project Manifest (pyproject.toml + uv.lock)

**Objective:** Give every later stage - CI, Docker, Kubernetes - one reproducible dependency graph to install from.

The service you deploy is a FastAPI app that talks to the RAG stack over HTTP. Every stage in this lab installs from the manifest below; nothing installs from a hand-typed pip list.

```bash
# Create the project manifest in the repo root.
cd ~/lab-009-production

# uv-native dependency management: pyproject.toml is the source of truth,
# uv.lock pins the resolved graph. uv init --bare creates only the manifest;
# uv add records each pin and writes the lockfile in one step.
uv init --bare --python 3.13 .
uv add fastapi==0.141.1 "uvicorn[standard]==0.52.1" "httpx>=0.28" \
    prometheus-client==0.26.0 "cryptography>=46"

# Test tooling goes into the default dev group: uv sync installs it
# locally, and production images opt out with --no-dev.
uv add --dev "pytest>=8" "pytest-cov>=5"
```

**Checkpoint:** `uv.lock` exists, and `uv sync --locked` recreates the exact environment from it.

---

### Step 1.1: Understanding SSL/TLS

**Objective:** Set up HTTPS for secure API communication

```python
# File: ssl_setup.py
"""
SSL/TLS Configuration for Production API
"""

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone
import ipaddress

class SSLCertificateGenerator:
    """Generate SSL certificates for development/testing"""

    def generate_self_signed_cert(self, domain="localhost", ip_addresses=None):
        """Generate self-signed certificate"""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AI Studio"),
            x509.NameAttribute(NameOID.COMMON_NAME, domain),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(domain),
                *[x509.IPAddress(ipaddress.IPv4Address(ip)) for ip in (ip_addresses or [])]
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())

        # Serialize
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        return cert_pem, key_pem

# Usage
generator = SSLCertificateGenerator()
cert, key = generator.generate_self_signed_cert()

# Save certificates
with open("cert.pem", "wb") as f:
    f.write(cert)
with open("key.pem", "wb") as f:
    f.write(key)

print("✓ SSL certificates generated")
print("  cert.pem: Public certificate")
print("  key.pem: Private key")
```

### Step 1.2: Production SSL with Let's Encrypt

```bash
#!/bin/bash
# File: setup_letsencrypt.sh

# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run

echo "✓ Let's Encrypt SSL configured"
echo "✓ Auto-renewal enabled"
```

### Step 1.3: FastAPI with SSL

```python
# File: secure_api.py
"""
Production API with SSL configuration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

app = FastAPI(title="Production API")

# Security middleware
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.your-domain.com", "localhost"]
)

@app.get("/")
async def root():
    return {"status": "healthy", "message": "API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Development with self-signed cert
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
    )

# Production command:
# uvicorn secure_api:app --host 0.0.0.0 --port 8000 \
#   --ssl-keyfile /etc/letsencrypt/live/your-domain.com/privkey.pem \
#   --ssl-certfile /etc/letsencrypt/live/your-domain.com/fullchain.pem
```

**Checkpoint 1:** ✅ SSL certificates configured, API running on HTTPS

---

## 🔧 Part 2: Nginx Reverse Proxy (90 minutes)

### Step 2.1: Nginx Configuration

```nginx
# File: nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=search_limit:10m rate=5r/s;

    # Upstream configuration
    upstream api_backend {
        least_conn;
        server api-1:8000 weight=1 max_fails=3 fail_timeout=30s;
        server api-2:8000 weight=1 max_fails=3 fail_timeout=30s;
        server api-3:8000 weight=1 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Server configuration
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL configuration
        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Proxy settings
        location / {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;

            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
            proxy_busy_buffers_size 8k;
        }

        # Search endpoint with stricter rate limit
        location /api/search {
            limit_req zone=search_limit burst=10 nodelay;

            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_read_timeout 300s;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://api_backend/health;
            access_log off;
        }

        # WebSocket support
        location /ws {
            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;

            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
        }
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }
}
```

### Step 2.2: Docker Compose with Nginx

```yaml
# File: docker-compose.yml

services:
  api-1:
    build: ./api
    environment:
      - MODEL_NAME=${MODEL_NAME}
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./models:/models
    networks:
      - backend
    restart: unless-stopped

  api-2:
    build: ./api
    environment:
      - MODEL_NAME=${MODEL_NAME}
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./models:/models
    networks:
      - backend
    restart: unless-stopped

  api-3:
    build: ./api
    environment:
      - MODEL_NAME=${MODEL_NAME}
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./models:/models
    networks:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - api-1
      - api-2
      - api-3
    networks:
      - backend
    restart: unless-stopped

  redis:
    image: redis:alpine
    networks:
      - backend
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    networks:
      - backend
    restart: unless-stopped

networks:
  backend:
    driver: bridge

volumes:
  qdrant_storage:
```

**Checkpoint 2:** ✅ Nginx configured as reverse proxy with load balancing

---

## 🚀 Part 3: CI/CD Pipeline (120 minutes)

### Step 3.1: GitHub Actions Workflow

```yaml
# File: .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Install uv
        uses: astral-sh/setup-uv@v9

      - name: Install dependencies
        run: uv sync --locked # dev group installs by default, so pytest rides along

      - name: Run tests
        run: uv run pytest --cov=api tests/ --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v5
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v7

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          echo "Deploying to staging..."
          # Add your deployment commands here
          # kubectl set image deployment/api api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # Add your deployment commands here
```

### Step 3.2: Dockerfile with Multi-stage Build

```dockerfile
# File: Dockerfile

# Build stage
FROM python:3.13-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Official uv-in-Docker pattern: copy the uv binary from the uv image
# (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Dependency layer: only manifest/lockfile changes rebuild this.
# uv sync --locked installs exactly what uv.lock pins; --no-install-project
# skips the project itself; --no-dev keeps test tooling out of the image.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtualenv from the builder (same base image, so the
# venv's /usr/local/bin/python3.13 symlink resolves identically);
# entry points like uvicorn live in /app/.venv/bin, exposed by PATH
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY ./api /app/api

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 3.3: Application Pre-start Hook

```python
# File: api/main.py
"""
FastAPI application with pre-start validation
"""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
import httpx

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting application...")
    await startup_checks()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await cleanup()
    logger.info("Application shut down successfully")

async def startup_checks():
    """Run startup checks"""
    checks = {
        "redis": check_redis,
        "qdrant": check_qdrant,
        "model": check_model,
    }

    for name, check_fn in checks.items():
        try:
            await check_fn()
            logger.info(f"✓ {name} check passed")
        except Exception as e:
            logger.error(f"✗ {name} check failed: {e}")
            raise

async def check_redis():
    """Check Redis connection"""
    import redis.asyncio as redis
    client = redis.from_url("redis://redis:6379")
    await client.ping()
    await client.close()

async def check_qdrant():
    """Check Qdrant connection"""
    from qdrant_client import AsyncQdrantClient
    client = AsyncQdrantClient(url="http://qdrant:6333")
    await client.get_collections()
    await client.close()

async def check_model():
    """Check model availability"""
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
    assert tokenizer.vocab_size > 0

async def cleanup():
    """Cleanup resources"""
    # Close connections, etc.
    pass

# Create app
app = FastAPI(
    title="Production API",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "checks": {
            "redis": "ok",
            "qdrant": "ok",
            "model": "ok",
        }
    }

@app.get("/ready")
async def ready():
    """Readiness check"""
    # Check if all dependencies are ready
    return {"status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Checkpoint 3:** ✅ CI/CD pipeline configured with automated testing and deployment

---

## ☸️ Part 4: Kubernetes Deployment (120 minutes)

### Step 4.1: Kubernetes Deployment Manifests

```yaml
# File: k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
  labels:
    app: api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: api
        image: ghcr.io/your-org/api:latest
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: MODEL_NAME
          value: "meta-llama/Llama-2-7b-hf"
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: redis_url
        - name: QDRANT_URL
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: qdrant_url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: model-cache
          mountPath: /models
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      nodeSelector:
        gpu: "true"
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule

---
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
data:
  redis_url: "redis://redis-service:6379"
  qdrant_url: "http://qdrant-service:6333"
  log_level: "INFO"

---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
stringData:
  openai-api-key: "your-openai-api-key"
```

### Step 4.2: Service and Ingress

```yaml
# File: k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
  labels:
    app: api
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: api

---
apiVersion: v1
kind: Service
metadata:
  name: api-metrics-service
  labels:
    app: api
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: metrics
  selector:
    app: api

---
# HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max

---
# Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - your-domain.com
    secretName: api-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

### Step 4.3: Persistent Volume for Model Cache

```yaml
# File: k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache-pvc
spec:
  accessModes:
  - ReadWriteMany
  storageClassName: nfs-storage
  resources:
    requests:
      storage: 100Gi

---
# StorageClass (example for NFS)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server.example.com
  share: /models
reclaimPolicy: Retain
volumeBindingMode: Immediate
```

### Step 4.4: Deploy to Kubernetes

```bash
#!/bin/bash
# File: deploy_k8s.sh

set -e

echo "Deploying to Kubernetes..."

# Create namespace
kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMaps and Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Apply PVC
kubectl apply -f k8s/pvc.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for rollout
kubectl rollout status deployment/api-deployment -n production

echo "✓ Deployment complete"
kubectl get pods -n production
kubectl get services -n production
```

**Checkpoint 4:** ✅ Application deployed to Kubernetes with HPA and Ingress

---

## 📊 Part 5: Monitoring and Observability (120 minutes)

### Step 5.1: Prometheus Metrics

```python
# File: api/metrics.py
"""
Prometheus metrics for API monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# Request metrics
request_counter = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# RAG metrics
rag_query_counter = Counter(
    'rag_queries_total',
    'Total RAG queries',
    ['tenant_id']
)

rag_query_duration = Histogram(
    'rag_query_duration_seconds',
    'RAG query duration',
    ['tenant_id']
)

rag_results_count = Histogram(
    'rag_results_count',
    'Number of RAG results returned',
    ['tenant_id']
)

# Vector DB metrics
vector_db_latency = Histogram(
    'vector_db_latency_seconds',
    'Vector DB query latency',
    ['operation']
)

vector_db_size = Gauge(
    'vector_db_size',
    'Vector DB collection size',
    ['collection']
)

# LLM metrics
llm_request_counter = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model']
)

llm_token_usage = Histogram(
    'llm_tokens_used',
    'LLM token usage',
    ['model', 'type']
)

llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration',
    ['model']
)

# System metrics
gpu_memory_used = Gauge(
    'gpu_memory_used_bytes',
    'GPU memory used',
    ['gpu_id']
)

gpu_utilization = Gauge(
    'gpu_utilization_percent',
    'GPU utilization',
    ['gpu_id']
)

# Application info
app_info = Info(
    'api_info',
    'API application information'
)

def track_time(metric):
    """Decorator to track function execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                metric.labels(status='success').observe(time.time() - start_time)
                return result
            except Exception as e:
                metric.labels(status='error').observe(time.time() - start_time)
                raise
        return async_wrapper
    return decorator

# Initialize app info
app_info.info({
    'version': '1.0.0',
    'environment': 'production',
})
```

### Step 5.2: FastAPI with Prometheus

```python
# File: api/main.py
from fastapi import FastAPI, Request
from fastapi.responses import Response
import prometheus_client
from prometheus_client import Counter, Histogram, generate_latest

# Update metrics
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track all requests"""
    start_time = time.time()

    response = await call_next(request)

    # Record metrics
    duration = time.time() - start_time
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    request_counter.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    return response

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

### Step 5.3: Grafana Dashboard

File: `grafana-dashboard.json`:

```json
{
  "dashboard": {
    "title": "API Production Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(api_requests_total{status=~\"5..\"}[5m]) / rate(api_requests_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "RAG Query Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(rag_query_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      },
      {
        "title": "GPU Utilization",
        "targets": [
          {
            "expr": "gpu_utilization_percent"
          }
        ],
        "type": "gauge"
      }
    ]
  }
}
```

### Step 5.4: Logging Configuration

```python
# File: api/logging_config.py
"""
Structured logging configuration
"""

import logging
import json
import sys
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """JSON log formatter"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data)

# Configure logging
def setup_logging(level=logging.INFO):
    """Setup structured logging"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    return root_logger

# Usage
logger = setup_logging()
logger.info("Application started", extra={"request_id": "123"})
```

**Checkpoint 5:** ✅ Monitoring stack configured with Prometheus and Grafana

---

## 💰 Part 6: Cost Optimization (90 minutes)

### Step 6.1: Cost Analysis Script

```python
# File: cost_optimizer.py
"""
Cost optimization analysis
"""

from dataclasses import dataclass
from typing import Dict
import math

@dataclass
class InstancePricing:
    """Cloud instance pricing"""
    name: str
    hourly_cost: float
    gpu_memory: int  # GB
    vcpu: int
    ram: int  # GB

# AWS pricing (examples)
INSTANCES = {
    "g5.xlarge": InstancePricing("g5.xlarge", 1.006, 24, 4, 16),
    "g5.2xlarge": InstancePricing("g5.2xlarge", 2.012, 24, 8, 32),
    "g5.4xlarge": InstancePricing("g5.4xlarge", 4.024, 48, 16, 64),
    "g5.8xlarge": InstancePricing("g5.8xlarge", 6.368, 80, 32, 128),
    "g5.12xlarge": InstancePricing("g5.12xlarge", 9.552, 96, 48, 192),
    "g5.16xlarge": InstancePricing("g5.16xlarge", 12.736, 128, 64, 256),
    "g5.24xlarge": InstancePricing("g5.24xlarge", 19.104, 192, 96, 384),
    "p3.2xlarge": InstancePricing("p3.2xlarge", 3.06, 16, 8, 61),
    "p3.8xlarge": InstancePricing("p3.8xlarge", 12.24, 64, 32, 244),
    "p3.16xlarge": InstancePricing("p3.16xlarge", 24.48, 128, 64, 488),
}

class CostOptimizer:
    """Cost optimization calculator"""

    def __init__(self, monthly_requests: int, avg_tokens: int):
        self.monthly_requests = monthly_requests
        self.avg_tokens = avg_tokens

    def calculate_instance_count(self, instance: InstancePricing, qps: float) -> int:
        """Calculate required instance count"""
        # Assume each instance can handle ~100 tokens/sec
        tokens_per_sec_per_instance = 100

        requests_per_sec = qps
        tokens_per_sec = requests_per_sec * self.avg_tokens

        instances_needed = math.ceil(tokens_per_sec / tokens_per_sec_per_instance)
        return instances_needed

    def calculate_monthly_cost(
        self,
        instance: InstancePricing,
        instance_count: int,
        cache_hit_rate: float = 0.0,
    ) -> Dict:
        """Calculate monthly cost"""
        hours_per_month = 730  # 24 * 30.42
        base_cost = instance.hourly_cost * instance_count * hours_per_month

        # Cache savings
        effective_requests = self.monthly_requests * (1 + cache_hit_rate)
        cost_per_request = base_cost / effective_requests

        return {
            "instance": instance.name,
            "instance_count": instance_count,
            "hourly_cost": instance.hourly_cost,
            "monthly_base_cost": round(base_cost, 2),
            "cache_hit_rate": cache_hit_rate,
            "effective_requests": int(effective_requests),
            "cost_per_1k_requests": round(cost_per_request * 1000, 4),
            "monthly_cost_for_1M": round(cost_per_request * 1000000, 2),
        }

    def find_optimal_configuration(
        self,
        qps: float,
        cache_hit_rate: float = 0.0,
    ) -> Dict:
        """Find optimal configuration for given QPS"""
        results = []

        for instance in INSTANCES.values():
            instance_count = self.calculate_instance_count(instance, qps)
            cost = self.calculate_monthly_cost(instance, instance_count, cache_hit_rate)
            results.append(cost)

        # Sort by monthly cost
        results.sort(key=lambda x: x["monthly_base_cost"])

        return {
            "qps": qps,
            "monthly_requests": self.monthly_requests,
            "avg_tokens": self.avg_tokens,
            "best_option": results[0],
            "all_options": results[:5],  # Top 5
        }

# Example usage
optimizer = CostOptimizer(
    monthly_requests=1_000_000,  # 1M requests/month
    avg_tokens=500,  # 500 tokens/request
)

# Analyze for 10 QPS with 50% cache hit rate
result = optimizer.find_optimal_configuration(
    qps=10,
    cache_hit_rate=0.5,
)

print(f"Optimal configuration: {result['best_option']['instance']}")
print(f"Instance count: {result['best_option']['instance_count']}")
print(f"Monthly cost: ${result['best_option']['monthly_base_cost']}")
print(f"Cost per 1K requests: ${result['best_option']['cost_per_1k_requests']}")
```

### Step 6.2: Spot Instance Configuration

```yaml
# File: k8s/spot-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-spot-workers
spec:
  replicas: 5
  selector:
    matchLabels:
      app: api-worker
  template:
    metadata:
      labels:
        app: api-worker
    spec:
      # Use spot instances
      nodeSelector:
        spot: "true"
      tolerations:
      - key: "spot"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      containers:
      - name: api-worker
        image: ghcr.io/your-org/api:latest
        env:
        - name: WORKER_MODE
          value: "spot"
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
            nvidia.com/gpu: 1
```

### Step 6.3: Autoscaling Policy

```yaml
# File: k8s/autoscaling-policy.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: api-scaler
spec:
  scaleTargetRef:
    name: api-deployment
  minReplicaCount: 2
  maxReplicaCount: 20
  cooldownPeriod: 300
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus-service:9090
      metricName: rate(api_requests_total[2m])
      threshold: "100"
      query: rate(api_requests_total[2m])
  - type: cpu
    metadata:
      type: Utilization
      value: "70"
```

**Checkpoint 6:** ✅ Cost optimization strategies implemented

---

## 🐛 Part 7: Production Debugging (60 minutes)

### Step 7.1: Debug Middleware

```python
# File: api/debug_middleware.py
"""
Debugging middleware for production
"""

from fastapi import Request, Response
import time
import uuid
import logging

logger = logging.getLogger(__name__)

async def debug_middleware(request: Request, call_next):
    """Debug middleware to track all requests"""

    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log request
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
        }
    )

    # Track time
    start_time = time.time()

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(duration)

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Log error
        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "duration_ms": round(duration * 1000, 2),
            },
            exc_info=True,
        )

        raise
```

### Step 7.2: Performance Profiling

```python
# File: api/profiling.py
"""
Performance profiling utilities
"""

import cProfile
import pstats
import io
from functools import wraps
from contextlib import contextmanager

def profile_function(func):
    """Decorator to profile a function"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        try:
            result = await func(*args, **kwargs)
        finally:
            pr.disable()

            # Print stats
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            print(s.getvalue())

        return result
    return wrapper

@contextmanager
def profile_context():
    """Context manager for profiling"""
    pr = cProfile.Profile()
    pr.enable()
    try:
        yield
    finally:
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        print(s.getvalue())

# Usage
# @profile_function
# async def my_function():
#     ...

# or
# with profile_context():
#     my_code()
```

### Step 7.3: Common Issues and Solutions

```python
# File: troubleshooting.py
"""
Common production issues and solutions
"""

TROUBLESHOOTING_GUIDE = {
    "high_memory": {
        "symptoms": ["OOMKilled", "High memory usage"],
        "causes": [
            "Memory leak in application",
            "Insufficient memory limits",
            "Large batch sizes",
            "Model not quantized",
        ],
        "solutions": [
            "Enable gradient checkpointing",
            "Reduce batch size",
            "Use 4-bit quantization",
            "Clear cache regularly",
            "Increase memory limits",
        ],
    },
    "high_latency": {
        "symptoms": ["Slow response times", "Timeouts"],
        "causes": [
            "Insufficient replicas",
            "Cold starts",
            "Large context windows",
            "No caching",
            "Network issues",
        ],
        "solutions": [
            "Increase replica count",
            "Enable warm-up",
            "Use smaller context",
            "Implement caching",
            "Use CDN",
        ],
    },
    "gpu_utilization_low": {
        "symptoms": ["Low GPU usage", "Poor throughput"],
        "causes": [
            "CPU bottleneck",
            "Small batch sizes",
            "Data loading slow",
            "Not using tensor parallel",
        ],
        "solutions": [
            "Increase batch size",
            "Optimize data loading",
            "Use multiple GPUs",
            "Enable CUDA graphs",
        ],
    },
}

def diagnose(symptoms: list) -> list:
    """Diagnose issues based on symptoms"""
    recommendations = []

    for issue, info in TROUBLESHOOTING_GUIDE.items():
        if any(symptom in symptoms for symptom in info["symptoms"]):
            recommendations.append({
                "issue": issue,
                "possible_causes": info["causes"],
                "solutions": info["solutions"],
            })

    return recommendations
```

**Checkpoint 7:** ✅ Debugging tools and troubleshooting guide ready

---

## ✅ Lab Completion Checklist

- [ ] SSL/TLS configured with Let's Encrypt
- [ ] Nginx reverse proxy configured
- [ ] CI/CD pipeline set up with GitHub Actions
- [ ] Docker image built and pushed to registry
- [ ] Kubernetes manifests created
- [ ] Application deployed to Kubernetes
- [ ] HPA configured for auto-scaling
- [ ] Prometheus metrics exported
- [ ] Grafana dashboard configured
- [ ] Structured logging implemented
- [ ] Cost optimization strategies applied
- [ ] Debugging middleware in place

---

## 🎓 Summary

In this lab, you learned:

1. **SSL/TLS Configuration**: Setting up HTTPS with Let's Encrypt
2. **Nginx Reverse Proxy**: Load balancing and SSL termination
3. **CI/CD Pipeline**: Automated testing and deployment
4. **Kubernetes Deployment**: Scalable orchestration with HPA
5. **Monitoring**: Prometheus metrics and Grafana dashboards
6. **Cost Optimization**: Spot instances, autoscaling, caching
7. **Production Debugging**: Troubleshooting tools and techniques

---

## 🚀 Next Steps

1. **LAB-010**: Advanced Topics
2. Deploy your own production system
3. Set up comprehensive monitoring
4. Implement sophisticated cost optimization

---

**Lab:** 009 - Production Deployment
**Time Estimate:** 8-10 hours
**Difficulty:** ⭐⭐⭐⭐ Expert
