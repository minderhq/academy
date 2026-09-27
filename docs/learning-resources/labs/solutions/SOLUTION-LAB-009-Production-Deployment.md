---
Document ID: SOLUTION-LAB-009
Title: "SOLUTION-LAB-009: Production Deployment"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Intermediate
---

# SOLUTION-LAB-009: Production Deployment

## Overview
Complete solution for deploying ML models with blue-green strategy.

---

## Docker Compose Setup

```yaml

services:
  # Current version (Blue)
  app-blue:
    image: myapp:v1.0
    environment:
      - VERSION=blue
    ports:
      - "8000:8000"

  # New version (Green)
  app-green:
    image: myapp:v2.0
    environment:
      - VERSION=green
    ports:
      - "8001:8001"

  # Load balancer
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## Deployment Script

```bash
#!/bin/bash
# deploy.sh

# Deploy green
docker-compose up -d app-green

# Wait for health
./wait-for-health.sh http://localhost:8001/health

# Run smoke tests
./smoke-test.sh http://localhost:8001

# Switch traffic
./switch-to-green.sh

echo "Deployment successful!"
```

---

**Difficulty:** ⭐⭐⭐⭐
