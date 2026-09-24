# 6303: Neo4j Deployment Guide

## Abstract
Complete guide for deploying Neo4j knowledge graph database on any Docker-capable Linux host, NAS, or VPS for PROJECT-OMEGA.

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
version: "3.8"

services:
  neo4j:
    image: neo4j:5.15-community
    container_name: project-omega-neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - ./data:/data
      - ./logs:/logs
      - ./plugins:/plugins
      - ./conf:/conf
      - ./import:/import
    environment:
      # Authentication
      - NEO4J_AUTH=neo4j/your_secure_password_here

      # Memory settings (adjust based on available RAM)
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=2G
      - NEO4J_dbms_memory_pagecache_size=1G

      # Plugins
      - NEO4J_PLUGINS=["apoc"]

      # APOC settings
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
      - NEO4J_dbms_security_procedures_allowlist=apoc.*

      # Performance tuning
      - NEO4J_dbms_connector_bolt_advertised__address=:7687
      - NEO4J_dbms_connector_http_advertised__address=:7474

      # Import settings
      - NEO4J_dbms_security_procedures_unrestricted=gds.*
      - NEO4J_dbms_security_procedures_allowlist=gds.*

    restart: unless-stopped
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "your_secure_password_here", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - project-omega-net

networks:
  project-omega-net:
    external: true
EOF

# Start Neo4j
docker-compose up -d

# Check logs
docker-compose logs -f neo4j
```

### Method 2: Portainer / NAS Container Manager (Web UI)

1. Open Portainer or Container Manager: http://localhost:9000
2. Click "Stacks" → "Add Stack"
3. Name: `neo4j`
4. Paste the docker-compose.yml content
5. Click "Deploy the stack"

## Initial Configuration

### 1. Access Neo4j Browser

```
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

// Check database size
CALL dbms.queryJmx("org.neo4j:Instance name=kernel#0,name=Store file size") YIELD attributes
RETURN attributes["MaximumFilesize"] as max_bytes

// Verify APOC
RETURN apoc.version()
```

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

# Optimize for 4GB available RAM (see "Memory Tuning by Host RAM" above)
cat >> neo4j.conf << 'EOF'

# Heap Size (for query execution)
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=2G

# Page Cache (for caching graph data)
dbms.memory.pagecache.size=1G

# Transaction state
dbms.memory.transaction.global_max_size=1G
dbms.memory.transaction.max_size=256M

# Query cache
dbms.query_cache_size=256m

# Connection limits
dbms.connector.bolt.thread_pool_max_size=400
dbms.connector.http.thread_pool_max_size=400

# Performance
dbms.connector.bolt.advertised_address=:7687
dbms.connector.http.advertised_address=:7474

# Log settings
dbms.logs.debug.level=INFO
EOF

# Restart
docker-compose restart neo4j
```

### Storage Optimization

```bash
# Create data directory on fast local storage (SSD preferred)
mkdir -p /srv/neo4j/data

# Set proper permissions
chmod 777 /srv/neo4j/data
```

## Backup Strategy

### 1. Automated Backup Script

```bash
# /srv/neo4j/backup.sh
#!/bin/bash

BACKUP_DIR="/srv/backups/neo4j"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop Neo4j
cd /srv/neo4j
docker-compose down

# Backup data
tar -czf $BACKUP_DIR/neo4j_backup_$DATE.tar.gz data/

# Start Neo4j
docker-compose up -d

# Keep only last 7 days of backups
find $BACKUP_DIR -name "neo4j_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: neo4j_backup_$DATE.tar.gz"
```

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

def check_health():
    """Check Neo4j health"""

    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "your_secure_password_here")
    )

    with driver.session() as session:
        # Check connectivity
        result = session.run("RETURN 1")
        if not result.single()[0] == 1:
            return False

        # Check database size
        result = session.run("CALL dbms.queryJmx('org.neo4j:Instance name=kernel#0,name=Store file size') YIELD attributes RETURN attributes['MaximumFilesize'] as size")
        size_mb = result.single()[0] / (1024*1024)

        # Check node count
        result = session.run("MATCH (n) RETURN count(n) as count")
        node_count = result.single()[0]

    return {
        "healthy": True,
        "size_mb": size_mb,
        "node_count": node_count
    }

if __name__ == "__main__":
    health = check_health()
    print(f"Healthy: {health['healthy']}")
    print(f"Size: {health['size_mb']:.2f} MB")
    print(f"Nodes: {health['node_count']}")
```

### 2. Prometheus Metrics (Optional)

```yaml
# Add to docker-compose.yml for Prometheus scraping
services:
  neo4j-exporter:
    image: neo4j-contrib/neo4j-prometheus-exporter:latest
    container_name: neo4j-prometheus-exporter
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=your_secure_password_here
    ports:
      - "9301:9301"
    depends_on:
      - neo4j
    networks:
      - project-omega-net
```

## Security Hardening

### 1. Change Default Password

```cypher
// In Neo4j Browser
CALL dbms.security.changePassword('neo4j', 'new_secure_password')
```

### 2. Create Limited User

```cypher
// Create user for agents (read-only)
CREATE USER agent_user SET PASSWORD 'agent_password'
SET DATABASE ROLE DEFAULT
GRANT ACCESS ON DATABASE * TO agent_user
GRANT MATCH ON GRAPH * NODES * TO agent_user
GRANT MATCH ON GRAPH * RELATIONSHIPS * TO agent_user
```

### 3. Network Isolation

```yaml
# docker-compose.yml - only expose to internal network
services:
  neo4j:
    # Remove ports section, only use internal network
    networks:
      - project-omega-net
    # Access via reverse proxy (Nginx)
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```
Error: Java heap space
```

**Solution:**
```bash
# Reduce memory settings
NEO4J_dbms_memory_heap_max__size=1G
NEO4J_dbms_memory_pagecache_size=512m
```

#### 2. Slow Queries

```cypher
// Check running queries
CALL dbms.listQueries() YIELD queryId, query, runtimeMillis
WHERE runtimeMillis > 1000
RETURN queryId, query, runtimeMillis
ORDER BY runtimeMillis DESC

// Kill long-running query
CALL dbms.terminateQuery('<query-id>')
```

#### 3. High CPU Usage

```cypher
// Check connection count
CALL dbms.listConnections() YIELD connectionCount
RETURN connectionCount

// Check active transactions
CALL dbms.listTransactions() YIELD transactionId, currentQueryId
RETURN transactionId, currentQueryId
```

## K3s Deployment (Optional)

```yaml
# k8s-neo4j.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: project-omega
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
        image: neo4j:5.15-community
        ports:
        - containerPort: 7474
          name: http
        - containerPort: 7687
          name: bolt
        env:
        - name: NEO4J_AUTH
          value: "neo4j/password"
        - name: NEO4J_dbms_memory_heap_max__size
          value: "2G"
        - name: NEO4J_dbms_memory_pagecache_size
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
  namespace: project-omega
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

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [6301: Neo4j and Knowledge Graphs](../6301-Neo4j-and-Knowledge-Graphs.md)
- [6302: CAG Long Context](../6302-CAG-Long-Context-Architectures.md)
- [6401: Qdrant Setup](../../6400-Vector-Databases/6401-Qdrant-Setup.md)
- [EXP_6301: Neo4j Knowledge Graph](../../../../../experiments/EXP_6303_NEO4J.md)

**Last Updated:** 2026-09-24
