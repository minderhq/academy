# PROJECT-OMEGA Configuration Templates

This directory contains production-ready configuration templates for deploying the PROJECT-OMEGA infrastructure on Synology NAS + Proxmox GPU VM.

## Files

### Docker Compose Files

#### `docker-compose.yml` (Original)
Basic Docker Compose configuration for deploying core services on Synology NAS:
- Qdrant (Vector Database)
- Neo4j (Knowledge Graph)
- Redis (Caching)
- Nginx (Reverse Proxy)

#### `docker-compose-complete.yml` (NEW - Recommended)
Complete Docker Compose configuration with full monitoring stack:
- Qdrant (Vector Database)
- Neo4j (Knowledge Graph)
- Redis (Caching)
- **Prometheus** (Metrics Collection)
- **Grafana** (Visualization)
- **Loki** (Log Aggregation)
- **Promtail** (Log Collector)
- **Tempo** (Distributed Tracing)
- **cAdvisor** (Container Metrics)
- **Node Exporter** (System Metrics)
- **Redis Exporter** (Redis Metrics)
- **Portainer** (Container Management)
- **Dozzle** (Log Viewer)
- **Nginx** (Reverse Proxy)

#### `docker-compose-gpu.yml` (NEW - GPU VM)
Docker Compose configuration for GPU-enabled Proxmox VM:
- **vLLM** (High-Performance Inference)
- **TGI** (Text Generation Inference)
- **Ollama** (Alternative LLM Server)
- **ReAct Agent** (AI Agent Service)
- **GraphRAG Service** (Knowledge Graph + Vector Search)
- **GPU Exporter** (GPU Metrics)

### Monitoring Configuration

#### `monitoring/prometheus/prometheus.yml`
Prometheus configuration for scraping metrics from all services.

#### `monitoring/loki/loki.yml`
Loki configuration for log aggregation and storage.

#### `monitoring/tempo/tempo.yml`
Tempo configuration for distributed tracing.

#### `monitoring/promtail/promtail.yml`
Promtail configuration for log collection from containers and system.

#### `monitoring/grafana/provisioning/datasources/datasources.yml`
Grafana datasources provisioning for automatic setup.

#### `monitoring/grafana/provisioning/dashboards/dashboards.yml`
Grafana dashboards provisioning for automatic dashboard loading.

### Kubernetes

#### `k3s-manifests.yaml`
Kubernetes manifests for deploying services on K3s cluster:
- GPU Operator setup
- Model serving deployments
- Storage classes
- Ingress configuration

### API Gateway

#### `nginx/nginx.conf`
Main Nginx configuration with upstream definitions and performance tuning.

#### `nginx/conf.d/default.conf`
Service-specific location blocks for routing all PROJECT-OMEGA services.

### CI/CD Pipeline

#### `ci-cd/.github/workflows/deploy.yml`
GitHub Actions workflow for automated testing, building, and deployment:
- Linting and testing
- Security scanning
- Docker image building
- Automated deployment to dev/prod
- Rollback on failure

### Service Dockerfiles

#### `services/react-agent/Dockerfile` + `requirements.txt`
ReAct Agent service container.

#### `services/graphrag/Dockerfile` + `requirements.txt`
GraphRAG service container.

### Scripts

#### `scripts/backup.sh`
Automated backup script for all services and data.

#### `scripts/restore.sh`
Automated restore script from backup.

### Grafana Dashboards

#### `monitoring/grafana/dashboards/project-omega-overview.json`
Main overview dashboard showing:
- Service health status (8 service status indicators)
- GPU utilization gauges
- GPU memory usage
- Container CPU usage
- Request rate by service
- Response time (p95)
- vLLM throughput metrics
- Recent error logs

#### `monitoring/grafana/dashboards/gpu-monitoring.json`
Dedicated GPU monitoring dashboard showing:
- Real-time GPU utilization
- GPU memory usage (11GB total)
- GPU temperature
- GPU power draw (250W TDP)
- GPU utilization over time
- GPU memory usage over time
- GPU temperature history
- GPU power consumption
- GPU fan speed
- GPU clock frequencies (SM and Memory)
- PCIe throughput (TB3)

### Performance Testing

#### `performance-testing/k6/load-test.js`
Load testing scripts for:
- vLLM completion API
- vLLM chat API
- Streaming completions
- ReAct Agent queries
- GraphRAG queries
- Qdrant vector search
- Neo4j graph queries

### Documentation

#### `docs/ssl-tls-setup.md`
Complete SSL/TLS certificate setup guide:
- Let's Encrypt automation
- Self-signed certificates for internal services
- Nginx SSL configuration
- OCSP stapling
- Certificate auto-renewal
- Service-specific SSL setup

### Service Mesh

#### `service-mesh/istio/values.yaml`
Istio service mesh configuration:
- Pilot and gateway settings
- mTLS configuration
- Traffic management
- Observability integration

#### `service-mesh/istio/virtualservices.yaml`
Istio virtual services and routing:
- Gateway configuration
- Virtual services for all applications
- Destination rules with load balancing
- Authorization policies
- Rate limiting
- Circuit breakers
- A/B testing configuration

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROJECT-OMEGA Infrastructure                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Synology NAS (192.168.1.100)              │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ Core Services (docker-compose-complete.yml)       │  │     │
│  │  │  - Qdrant (Vector DB)    :6333/6334              │  │     │
│  │  │  - Neo4j (Graph DB)      :7474/7687              │  │     │
│  │  │  - Redis (Cache)         :6379                   │  │     │
│  │  │  - Nginx (Proxy)         :80/443                 │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ Monitoring Stack                                 │  │     │
│  │  │  - Prometheus            :9090                   │  │     │
│  │  │  - Grafana               :3000                   │  │     │
│  │  │  - Loki                  :3100                   │  │     │
│  │  │  - Tempo                 :3200                   │  │     │
│  │  │  - cAdvisor              :8081                   │  │     │
│  │  │  - Node Exporter         :9100                   │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────┘     │
│                          │ 2.5Gbps                               │
│                          │                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         Proxmox GPU VM (192.168.1.50)                  │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ GPU Services (docker-compose-gpu.yml)            │  │     │
│  │  │  - vLLM                 :8000                    │  │     │
│  │  │  - TGI                  :8080                    │  │     │
│  │  │  - Ollama               :11434                   │  │     │
│  │  │  - ReAct Agent          :8001                    │  │     │
│  │  │  - GraphRAG Service     :8002                    │  │     │
│  │  │  - GPU Exporter         :9445                    │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ Hardware: RTX 2080 Ti (11GB VRAM) via TB3       │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Step 1: Deploy Core Services on Synology NAS

```bash
# SSH into Synology
ssh admin@192.168.1.100

# Navigate to project directory
cd /volume1/docker/project-omega

# Create monitoring directories
mkdir -p monitoring/prometheus monitoring/loki monitoring/tempo monitoring/promtail
mkdir -p monitoring/grafana/provisioning/datasources monitoring/grafana/provisioning/dashboards
mkdir -p data/{prometheus,grafana,loki,tempo,qdrant,neo4j,redis,portainer}
mkdir -p nginx/conf.d nginx/ssl nginx/logs

# Deploy complete stack with monitoring
docker-compose -f docker-compose-complete.yml up -d

# Check status
docker-compose -f docker-compose-complete.yml ps

# View logs
docker-compose -f docker-compose-complete.yml logs -f
```

### Step 2: Deploy GPU Services on Proxmox VM

```bash
# SSH into Proxmox GPU VM
ssh user@192.168.1.50

# Navigate to project directory
cd /opt/project-omega

# Install NVIDIA Container Toolkit (if not already installed)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update && apt-get install -y nvidia-container-toolkit

# Restart Docker
systemctl restart docker

# Deploy GPU services
docker-compose -f docker-compose-gpu.yml up -d

# Check GPU allocation
nvidia-smi

# Check status
docker-compose -f docker-compose-gpu.yml ps
```

### Step 3: Access Services

Open your browser and navigate to:

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://192.168.1.100:3000 | admin / omega_change_me |
| Prometheus | http://192.168.1.100:9090 | - |
| Neo4j Browser | http://192.168.1.100:7474 | neo4j / omega_change_me |
| Qdrant Console | http://192.168.1.100:6334 | - |
| Portainer | http://192.168.1.100:9000 | Setup on first visit |
| Dozzle (Logs) | http://192.168.1.100:8888 | - |
| vLLM API | http://192.168.1.50:8000 | - |
| TGI API | http://192.168.1.50:8080 | - |

## Service Endpoints

### Core Services (Synology NAS)

| Service | Port | Protocol | URL |
|---------|------|----------|-----|
| Qdrant gRPC | 6333 | gRPC | http://192.168.1.100:6333 |
| Qdrant HTTP | 6334 | HTTP | http://192.168.1.100:6334 |
| Neo4j Browser | 7474 | HTTP | http://192.168.1.100:7474 |
| Neo4j Bolt | 7687 | Bolt | bolt://192.168.1.100:7687 |
| Redis | 6379 | RESP | redis://192.168.1.100:6379 |
| Nginx HTTP | 80 | HTTP | http://192.168.1.100 |
| Nginx HTTPS | 443 | HTTPS | https://192.168.1.100 |

### Monitoring Services (Synology NAS)

| Service | Port | Protocol | URL |
|---------|------|----------|-----|
| Prometheus | 9090 | HTTP | http://192.168.1.100:9090 |
| Grafana | 3000 | HTTP | http://192.168.1.100:3000 |
| Loki | 3100 | HTTP | http://192.168.1.100:3100 |
| Tempo | 3200 | HTTP | http://192.168.1.100:3200 |
| Tempo OTLP gRPC | 4317 | gRPC | http://192.168.1.100:4317 |
| Tempo OTLP HTTP | 4318 | HTTP | http://192.168.1.100:4318 |
| cAdvisor | 8081 | HTTP | http://192.168.1.100:8081 |
| Node Exporter | 9100 | HTTP | http://192.168.1.100:9100 |
| Redis Exporter | 9121 | HTTP | http://192.168.1.100:9121 |
| Portainer | 9000 | HTTP | http://192.168.1.100:9000 |
| Dozzle | 8888 | HTTP | http://192.168.1.100:8888 |

### GPU Services (Proxmox VM)

| Service | Port | Protocol | URL |
|---------|------|----------|-----|
| vLLM | 8000 | HTTP | http://192.168.1.50:8000 |
| TGI | 8080 | HTTP | http://192.168.1.50:8080 |
| Ollama | 11434 | HTTP | http://192.168.1.50:11434 |
| ReAct Agent | 8001 | HTTP | http://192.168.1.50:8001 |
| GraphRAG | 8002 | HTTP | http://192.168.1.50:8002 |
| GPU Exporter | 9445 | HTTP | http://192.168.1.50:9445 |

## Configuration Notes

### Hardware Constraints
- **RTX 2080 Ti (11GB VRAM)**
  - Max model size: ~7B with AWQ quantization
  - Context window: 8K tokens
  - Batch size: 32 sequences
  - GPU memory utilization: 85%

- **2.5Gbps Network**
  - MTU: 9000 (Jumbo Frames)
  - Star topology from GPON modem
  - Low latency between NAS and GPU VM

### Performance Tuning
- vLLM configured for RTX 2080 Ti with AWQ quantization
- TGI with PagedAttention and Flash Attention enabled
- Prometheus 15s scrape interval
- Loki with 48h trace retention
- Tempo with probabilistic sampling (10%)

### Security
- Change default passwords in production:
  - Neo4j: `NEO4J_AUTH=neo4j/your_secure_password`
  - Grafana: `GF_SECURITY_ADMIN_PASSWORD`
  - Redis: Add `requirepass` to redis.conf
- Use SSL/TLS for external access
- Restrict network access via firewall rules

## Troubleshooting

### Check GPU Utilization
```bash
nvidia-smi
docker exec project-omega-gpu-exporter curl localhost:9445/metrics
```

### View Logs
```bash
# All logs
docker-compose -f docker-compose-complete.yml logs -f

# Specific service
docker-compose -f docker-compose-complete.yml logs -f qdrant
docker-compose -f docker-compose-complete.yml logs -f neo4j

# Via Dozzle (web UI)
open http://192.168.1.100:8888
```

### Check Metrics
```bash
# Prometheus targets
curl http://192.168.1.100:9090/api/v1/targets

# Grafana health
curl http://192.168.1.100:3000/api/health
```

### Restart Services
```bash
# Restart specific service
docker-compose -f docker-compose-complete.yml restart qdrant

# Rebuild and restart
docker-compose -f docker-compose-gpu.yml up -d --build vllm
```

## Related Documentation

- [1501: Monitoring and Observability](../../docs/phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
- [1404: vLLM Production Deployment](../../docs/phases/phase1-infra/1400-llmops/guides/1404-vLLM-Production-Deployment.md)
- [1405: TGI Deployment Guide](../../docs/phases/phase1-infra/1400-llmops/guides/1405-TGI-Deployment-Guide.md)
- [6303: Neo4j Deployment Guide](../../docs/phases/phase6-rag/6300-context/guides/6303-Neo4j-Deployment-Guide.md)
- [6403: Qdrant Synology Deployment](../../docs/phases/phase6-rag/6400-vector-databases/guides/6403-Qdrant-Synology-Deployment.md)
