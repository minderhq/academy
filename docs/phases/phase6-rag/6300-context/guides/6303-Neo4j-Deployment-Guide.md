---
Document ID: 6303
Title: "6303: Neo4j Deployment Guide"
Phase: 6
Module: 6300
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'neo4j', 'deployment', 'docker']
---

# 6303: Neo4j Deployment Guide

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
- [Troubleshooting](#troubleshooting)
- [K3s Deployment (Optional)](#k3s-deployment-optional)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Size a deployment — pick a target (Docker host, NAS stack, VPS) from the trade-off table and derive heap + page cache from the host-RAM table, keeping page cache sized to the hot graph rather than the whole store
- Deploy with Docker Compose — pin `neo4j:2026.09.0` (calendar versioning; 5.26 is the LTS line), single-source the password through `${NEO4J_PASSWORD:-…}` substitution into both `NEO4J_AUTH` and the healthcheck, and install the APOC plugin
- Configure and verify — create `Entity`/`Document` uniqueness constraints, confirm `dbms.components()` + `apoc.version()`, and use the Neo4j 5 setting names (`server.memory.*` — the `dbms.memory.*` names configure nothing on this release)
- Run the backup loop — stop → tar → start with 7-day rotation on a cron entry, and explain why the container must stop first (store files must be quiescent for a consistent copy)
- Monitor health — run the Bolt liveness/inventory script (`RETURN 1`, `SHOW CONSTRAINTS`, node count) and name the Enterprise-only native Prometheus endpoint (:2004) versus the Community options
- Harden and troubleshoot — `ALTER CURRENT USER SET PASSWORD`, a `reader`-role limited user (fine-grained `GRANT MATCH` is Enterprise-only), and `SHOW TRANSACTIONS` / `TERMINATE TRANSACTIONS` for stuck queries

---

## Abstract
Complete guide for deploying the Neo4j knowledge graph database on any Docker-capable Linux host, NAS, or VPS: image pinning, Compose, memory sizing, backup, monitoring, and hardening.

## Deployment Targets

Neo4j Community Edition runs as a single container with one data volume, so the same compose file works on any self-hosted target:

| Target | Best For | Notes |
|--------|----------|-------|
| Linux host + Docker (recommended) | Full control, predictable performance | Mini PC, used office PC, homelab server, or VPS |
| NAS with Container Manager / Docker | Reusing existing storage hardware | Import the compose file as a project/stack |
| VPS / cloud VM | Remote access, offsite data | Size memory carefully; graph workloads are RAM-hungry |

### Resource Allocation
| Component | Minimum | Recommended | Notes |
|-----------|----------|-------------|-------|
| RAM | 2GB | 4GB | Page cache + query execution |
| Storage | 20GB | 100GB | Database growth + transactions |
| CPU | 2 cores | 4 cores | Query performance |

### Memory Tuning by Host RAM

Set heap and page cache from what is actually available after the OS and other containers take their share:

| Host RAM | Heap Max | Page Cache | Suitable Graph Size |
|----------|----------|------------|---------------------|
| 8 GB (entry-level) | 1G | 1G | Up to ~10M nodes/relationships |
| 16 GB | 2G | 2-3G | ~50M nodes/relationships |
| 32 GB+ | 4-8G | 4-8G | 100M+ nodes/relationships |

## Docker Deployment

### Method 1: Docker Compose (Recommended)

```bash
# SSH into your host (or run locally)
ssh user@your-host

# Create directory
mkdir -p /srv/neo4j
cd /srv/neo4j

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  neo4j:
    # Calendar-versioned tag; 5.26 is the LTS maintenance line (see 6301)
    image: neo4j:2026.09.0
    container_name: neo4j
    ports:
      - "7474:7474"  # HTTP (Browser)
      - "7687:7687"  # Bolt (drivers)
    volumes:
      - ./data:/data
      - ./logs:/logs
      - ./plugins:/plugins
      - ./conf:/conf
      - ./import:/import
    environment:
      # One source of truth: Compose substitutes ${NEO4J_PASSWORD:-default}
      # in BOTH NEO4J_AUTH and the healthcheck below, so the two can never
      # drift apart. Export NEO4J_PASSWORD on the host to override.
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:-change-me-strong-password}

      # Memory — Neo4j 5 renamed dbms.memory.* to server.memory.*; the old
      # dbms_memory_* env names configure nothing on this release
      - NEO4J_server_memory_heap_initial__size=512m
      - NEO4J_server_memory_heap_max__size=2G
      - NEO4J_server_memory_pagecache_size=1G

      # Plugins (apoc = core APOC; GDS would need its own plugin entry)
      - NEO4J_PLUGINS=["apoc"]

      # Procedure permissions (dbms.security.* kept its prefix in 5.x)
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
      - NEO4J_dbms_security_procedures_allowlist=apoc.*

    restart: unless-stopped
    healthcheck:
      # Reads the same substituted password — see the env block above
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p \"${NEO4J_PASSWORD:-change-me-strong-password}\" RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - neo4j-net

networks:
  neo4j-net:
    driver: bridge
EOF

# Start Neo4j (Compose v2 CLI — the hyphenated docker-compose is v1, EOL)
docker compose up -d

# Check logs
docker compose logs -f neo4j
```

### Method 2: Portainer / NAS Container Manager (Web UI)

1. Open Portainer or Container Manager: [http://localhost:9000](http://localhost:9000)
2. Click "Stacks" → "Add Stack"
3. Name: `neo4j`
4. Paste the docker-compose.yml content
5. Click "Deploy the stack"

## Initial Configuration

### 1. Access Neo4j Browser

```text
URL: http://localhost:7474
Username: neo4j
Password: your_secure_password_here
```

### 2. Verify Installation

Run in Neo4j Browser:
```cypher
// Check version
CALL dbms.components() YIELD name, versions, edition
RETURN name, versions[0] as version, edition

// Verify APOC
RETURN apoc.version()
```

Store size: the 4.x "Store file size" JMX bean shifted across majors — measure `data/` with `du -sh` on the host instead of querying an unstable bean name.

### 3. Create Schema

```cypher
// Create uniqueness constraints
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE

// Verify
SHOW CONSTRAINTS
```

## Performance Tuning

### Memory Configuration

```bash
# Edit conf/neo4j.conf
cd /srv/neo4j/conf

# Optimize for 4GB available RAM (see "Memory Tuning by Host RAM" above).
# Equivalent to the compose env vars; use the Neo4j 5 setting names — the
# dbms.* → server.* renames landed in the 5.0 migration, and removed 4.x
# settings (per-tx transaction.max_size, byte-valued query_cache_size)
# no longer exist at all
cat >> neo4j.conf << 'EOF'

# Heap Size (for query execution)
server.memory.heap.initial_size=512m
server.memory.heap.max_size=2G

# Page Cache (for caching graph data)
server.memory.pagecache.size=1G

# Transaction state (global budget)
server.memory.transaction.global_max_size=1G

# Connection limits
server.bolt.thread_pool_max_size=400

# Log settings
server.logs.debug.level=INFO
EOF

# Restart
docker compose restart neo4j
```

### Storage Optimization

```bash
# Create data directory on fast local storage (SSD preferred)
mkdir -p /srv/neo4j/data

# The official image runs as uid/gid 7474 — hand the volume to that user
# (chmod 777 would leave the store world-writable)
chown -R 7474:7474 /srv/neo4j/data
```

## Backup Strategy

### 1. Automated Backup Script

```bash
# /srv/neo4j/backup.sh
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/srv/backups/neo4j"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop Neo4j — the store files must be quiescent for a consistent copy
cd /srv/neo4j
docker compose stop neo4j

# Backup data
tar -czf "$BACKUP_DIR/neo4j_backup_$DATE.tar.gz" data/

# Start Neo4j
docker compose start neo4j

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "neo4j_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: neo4j_backup_$DATE.tar.gz"
```

The tar approach is the sledgehammer: one artifact captures store files, plugins, and conf. The database-native alternative is a dump against the stopped container — `docker compose exec neo4j neo4j-admin database dump neo4j --to-path=/backups` with a `/backups` volume mounted — which produces a single restorable snapshot instead of a directory tree.

### 2. Schedule with Cron

1. Install the backup script: `chmod +x /srv/neo4j/backup.sh`
2. Edit crontab: `crontab -e`
3. Add a daily 2:00 AM entry:

```cron
0 2 * * * /srv/neo4j/backup.sh >> /var/log/neo4j-backup.log 2>&1
```

NAS users can schedule the same script through Container Manager / Task Scheduler instead of cron.

## Monitoring

### 1. Health Check Endpoint

```python
# neo4j_health.py
from neo4j import GraphDatabase

def check_health(uri="bolt://localhost:7687", user="neo4j",
                 password="your_secure_password_here"):
    """Liveness + basic inventory over Bolt"""
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        # 1. Liveness: trivial round-trip
        if session.run("RETURN 1").single()[0] != 1:
            return {"healthy": False, "reason": "RETURN 1 failed"}

        # 2. Schema sanity: the Entity/Document constraints exist
        constraint_count = len(list(session.run("SHOW CONSTRAINTS")))

        # 3. Graph size
        node_count = session.run("MATCH (n) RETURN count(n) as count").single()[0]

    driver.close()
    return {"healthy": True, "constraints": constraint_count,
            "node_count": node_count}

if __name__ == "__main__":
    health = check_health()
    print(f"Healthy: {health['healthy']}")
    if health["healthy"]:
        print(f"Constraints: {health['constraints']}")
        print(f"Nodes: {health['node_count']}")
```

### 2. Metrics Export

Neo4j exposes Prometheus metrics natively on port 2004 — **Enterprise Edition only**. Add to the `neo4j` service in docker-compose.yml:

```yaml
    ports:
      - "2004:2004"
    environment:
      - NEO4J_server_metrics_prometheus_enabled=true
```

Community Edition has no `:2004` endpoint. Monitor it through the Bolt health script above, or enable CSV metrics (`NEO4J_server_metrics_csv_enabled=true`) and scrape the files. The 1500-monitoring Prometheus stack adds a scrape job pointing at either.

## Security Hardening

### 1. Change Default Password

```cypher
// In Neo4j Browser — the old dbms.security.changePassword procedure took
// only the CURRENT user's new password and is deprecated; 4.x+ uses ALTER
ALTER CURRENT USER SET PASSWORD FROM 'your_secure_password_here' TO 'new_secure_password'
```

### 2. Create Limited User

```cypher
// Create user for agents (read-only). SET DATABASE ROLE and fine-grained
// GRANT MATCH ON GRAPH are Enterprise-only — Community uses built-in roles
CREATE USER agent_user IF NOT EXISTS SET PASSWORD 'agent_password' CHANGE NOT REQUIRED
GRANT ROLE reader TO agent_user
```

### 3. Network Isolation

```yaml
# docker-compose.yml - only expose to internal network
services:
  neo4j:
    # Remove ports section, only use internal network
    networks:
      - neo4j-net
    # Access via reverse proxy (Nginx)
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```text
Error: Java heap space
```

**Solution:**
```bash
# Reduce memory settings (Neo4j 5 names — the dbms_memory_* spellings
# configure nothing on this release)
NEO4J_server_memory_heap_max__size=1G
NEO4J_server_memory_pagecache_size=512m
```

#### 2. Slow Queries

```cypher
// 5.x+: SHOW TRANSACTIONS / TERMINATE TRANSACTIONS replaced the 4.x
// dbms.listQueries()/dbms.terminateQuery() procedures. YIELD * is
// version-proof — column names shifted between minors
SHOW TRANSACTIONS YIELD *

// Kill a long-running transaction
TERMINATE TRANSACTIONS '<transaction-id>'
```

#### 3. High CPU Usage

```cypher
// dbms.listConnections() never existed, and dbms.listTransactions() was
// folded into SHOW TRANSACTIONS — one command covers both checks
SHOW TRANSACTIONS YIELD *

// Bolt connection pressure is governed by the thread pool:
// server.bolt.thread_pool_max_size (see Performance Tuning)
```

## K3s Deployment (Optional)

```yaml
# k8s-neo4j.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: neo4j
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:2026.09.0
        ports:
        - containerPort: 7474
          name: http
        - containerPort: 7687
          name: bolt
        env:
        - name: NEO4J_AUTH
          value: "neo4j/password"
        - name: NEO4J_server_memory_heap_max__size
          value: "2G"
        - name: NEO4J_server_memory_pagecache_size
          value: "1G"
        - name: NEO4J_PLUGINS
          value: "[\"apoc\"]"
        resources:
          requests:
            memory: "3Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: local-path
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: neo4j
spec:
  selector:
    app: neo4j
  ports:
  - port: 7474
    targetPort: 7474
    name: http
  - port: 7687
    targetPort: 7687
    name: bolt
  type: ClusterIP
```


---

## Summary

This guide deploys Neo4j on any Docker-capable Linux host, NAS or VPS: image pinning, Compose file, memory sizing for the page cache and heap, backup strategy, monitoring hooks, and hardening checklist end to end. The Community Edition runs as a single container with one data volume, so one compose file serves every target. The rule it leaves: pin the image, size the page cache before the heap, and prove the backup restores - a graph database you cannot restore is a graph you do not have.

## References

### Related PROJECT-OMEGA Documents

- [6301: Neo4j and Knowledge Graphs](../6301-Neo4j-and-Knowledge-Graphs.md)
- [6302: CAG - Context Augmented Generation and Long Context Architectures](../6302-CAG-Long-Context-Architectures.md)
- [6304: GraphRAG Implementation Guide](6304-GraphRAG-Implementation.md)
- [6401: Qdrant Setup](../../6400-vector-databases/6401-Qdrant-Setup.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**
- Experiment: **[EXP_6303: Neo4j](../../../../../experiments/EXP_6303_NEO4J.md)**

