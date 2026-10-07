---
Document ID: TUTORIAL-005
Title: "TUTORIAL-005: Production Deployment with CI/CD"
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 90 minutes
Prerequisites: [PHASE-1, TUTORIAL-002]
Tags: ['tutorial', 'deployment', 'ci-cd']
---

# TUTORIAL-005: Production Deployment with CI/CD

**Prerequisites:** TUTORIAL-001 (Hello LLM), TUTORIAL-002 (Docker Essentials), TUTORIAL-004 (Monitoring)
**Time:** 90 minutes
**Difficulty:** ⭐⭐⭐ Advanced

---

## Tutorial Goals

After this tutorial, you will:
- ✅ Deploy AI services to production
- ✅ Set up SSL/TLS encryption
- ✅ Configure Nginx reverse proxy
- ✅ Implement CI/CD pipeline
- ✅ Set up automated backups
- ✅ Configure health checks

---

## Part 1: Production Architecture (10 minutes)

### Development vs Production

**Development:**
```text
Single Docker container
No SSL
No monitoring
Manual deployment
```

**Production:**
```text
Multiple services (API, Database, Monitoring)
SSL/TLS encryption
Load balancing
Automated deployment (CI/CD)
Health checks & auto-restart
Backups & disaster recovery
```

### Architecture Overview

```text
Internet → Nginx (SSL) → Load Balancer
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
              API Service 1       API Service 2
                    ↓                   ↓
                    └─────────┬─────────┘
                              ↓
                    Shared Services:
                    - Vector DB (Qdrant)
                    - Graph DB (Neo4j)
                    - Cache (Redis)
                    - LLM Engine (vLLM)
```

---

## Part 2: SSL/TLS Setup (20 minutes)

### Task: Set up Let's Encrypt SSL

```bash
# Create production directory
mkdir ~/production-deploy
cd ~/production-deploy

# Create directory for SSL certificates
mkdir -p ssl/certs ssl/private
```

### Option 1: Let's Encrypt (Recommended for public domains)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificate (HTTP-01 challenge)
sudo certbot certonly --standalone -d api.yourdomain.com

# Certificates will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Option 2: Self-signed (For local/testing)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private/selfsigned.key \
  -out ssl/certs/selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate CA bundle
cat ssl/certs/selfsigned.crt > ssl/certs/ca-bundle.crt
```

### Checkpoint: Part 2
**Verify:** Certificate files exist

---

## Part 3: Nginx Reverse Proxy (25 minutes)

### Task: Configure Nginx with SSL

```bash
# Create Nginx configuration
mkdir -p nginx/conf.d

cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

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
    gzip_types text/plain text/css text/xml application/json application/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=llm:10m rate=5r/s;

    # Upstream servers
    upstream api_servers {
        least_conn;
        server api1:8000 max_fails=3 fail_timeout=30s;
        server api2:8000 max_fails=3 fail_timeout=30s;
    }

    # Include site configs
    include /etc/nginx/conf.d/*.conf;
}
EOF
```

### Create site configuration:

```bash
cat > nginx/conf.d/api.conf << 'EOF'
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/certs/selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/private/selfsigned.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API endpoints
    location /v1/chat/completions {
        limit_req zone=llm burst=20;
        limit_req_status 429;

        proxy_pass http://api_servers;
        proxy_http_version 1.1;

        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for LLM
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://api_servers/health;
        access_log off;
    }

    # Metrics endpoint (authenticated)
    location /metrics {
        auth_basic "Prometheus Metrics";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://api_servers/metrics;
        access_log off;
    }

    # Grafana (if needed)
    location /grafana/ {
        proxy_pass http://grafana:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF
```

### Create password file for metrics:

```bash
# Install htpasswd tool
sudo apt-get install apache2-utils

# Create user
htpasswd -c nginx/.htpasswd prometheus
# Enter password when prompted
```

### Checkpoint: Part 3
**Verify:** Nginx configuration valid

```bash
# Test configuration
docker run --rm -v $(pwd)/nginx:/etc/nginx nginx nginx -t
```

---

## Part 4: Docker Compose for Production (15 minutes)

### Task: Create production-ready compose file

```bash
cat > docker-compose.prod.yml << 'EOF'

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nginx-gateway
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./nginx/.htpasswd:/etc/nginx/.htpasswd:ro
      - nginx-logs:/var/log/nginx
    depends_on:
      - api
    restart: always
    networks:
      - production
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "localhost", "-O", "/dev/null", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # API Service (multiple instances)
  api:
    build: ./services/api
    image: llm-api:prod
    container_name: api1
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://user:pass@db:5432/llmdb
      - REDIS_URL=redis://redis:6379
    volumes:
      - api-data:/app/data
    restart: always
    networks:
      - production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # Second API instance
  api2:
    image: llm-api:prod
    container_name: api2
    ports:
      - "8001:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://user:pass@db:5432/llmdb
      - REDIS_URL=redis://redis:6379
    volumes:
      - api-data:/app/data
    restart: always
    networks:
      - production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=llmdb
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: always
    networks:
      - production
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: always
    networks:
      - production
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # vLLM Inference Engine
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm
    ports:
      - "8002:8000"
    volumes:
      - ./models:/models
    command: >
      --model /models/mistral-7b-instruct
      --gpu-memory-utilization 0.9
      --max-model-len 4096
      --enable-prefix-caching
      --port 8000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: always
    networks:
      - production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: always
    networks:
      - production

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:?export GRAFANA_PASSWORD first}
    volumes:
      - grafana-data:/var/lib/grafana
    restart: always
    networks:
      - production

networks:
  production:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  api-data:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:
  nginx-logs:
EOF
```

### Checkpoint: Part 4
**Verify:** Docker Compose configuration valid

---

## Part 5: CI/CD Pipeline (20 minutes)

### Task: Set up GitHub Actions

```bash
# Create CI/CD directory
mkdir -p .github/workflows

cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy to Production

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: llm-api

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Install uv
        uses: astral-sh/setup-uv@v9

      - name: Install dependencies
        # The repo commits pyproject.toml + uv.lock (uv init --bare + uv add).
        run: uv sync --locked # dev group installs by default, so pytest rides along

      - name: Run tests
        run: uv run pytest tests/ --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v5
        with:
          files: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v7

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ github.repository }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}
            type=ref,event=branch
            type=semver,pattern={{version}}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v6
        with:
          context: ./services/api
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          target: production

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/llm-api
            docker compose pull
            docker compose up -d
            docker system prune -f

      - name: Health check
        run: |
          sleep 30
          curl -f http://api.yourdomain.com/health || exit 1

      - name: Notify on success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment successful! 🚀'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

      - name: Notify on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment failed! ❌'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
EOF
```

### Add secrets to GitHub:

1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Add these secrets:
   - `SERVER_HOST`: Your server IP/domain
   - `SERVER_USER`: SSH username
   - `SSH_PRIVATE_KEY`: Your SSH private key
   - `SLACK_WEBHOOK`: Slack webhook URL (optional)
   - `GRAFANA_PASSWORD`: Grafana admin password

### Checkpoint: Part 5
**Verify:** GitHub Actions workflow created

---

## Summary

### Production Checklist

```text
[ ] SSL/TLS configured
[ ] Nginx reverse proxy setup
[ ] Multiple API instances
[ ] Load balancing
[ ] Health checks
[ ] Auto-restart enabled
[ ] Resource limits set
[ ] Monitoring configured
[ ] CI/CD pipeline
[ ] Automated backups
[ ] Security headers
[ ] Rate limiting
```

### Key Production Commands

```bash
# Deploy new version
git push main

# Check deployment
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f api

# Scale API
docker compose -f docker-compose.prod.yml up -d --scale api=3

# Backup data
docker exec postgres pg_dump -U user llmdb > backup.sql

# Restore data
docker exec -i postgres psql -U user llmdb < backup.sql

# Monitor performance
curl http://localhost:9090/api/v1/query?query=up
```

---

## Next Steps

- **[1402: vLLM and TGI](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)** - Production inference
- **[1404: TGI Deployment Guide](../../phases/phase1-infra/1400-llmops/guides/1404-TGI-Deployment-Guide.md)** - TGI in production
- **[PROJECT-001: AI Assistant](../projects/PROJECT-001-AI-Assistant.md)** - Complete production system

---

**You're production-ready!** 🚀
