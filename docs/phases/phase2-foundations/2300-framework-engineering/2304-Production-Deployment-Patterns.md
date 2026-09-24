---
Document ID: 2304
Title: Production Deployment Patterns
Phase: 2
Module: 2300
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'architecture', 'api-design', 'production']
---

# 2304: Production Deployment Patterns

**Project:** AI Engineering Curriculum
**Phase:** [2300] Framework Engineering
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2 hours

---

## Abstract

Deploying ML systems to production requires careful planning to ensure zero downtime, easy rollbacks, and reliable updates. This document covers industry-standard deployment patterns.

**What you'll learn:**
- Blue-green deployment for zero downtime
- Canary deployment for gradual rollouts
- Rolling updates for continuous delivery
- A/B testing for model comparison

---

## Pattern 1: Blue-Green Deployment

### Concept

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  BLUE (Current Version)        GREEN (New Version)          │
│  ┌──────────────┐              ┌──────────────┐             │
│  │  App v1.0    │              │  App v2.0    │             │
│  │  Port 8000   │              │  Port 8001   │             │
│  └──────────────┘              └──────────────┘             │
│         │                            │                       │
│         └────────┬───────────────────┘                       │
│                  ↓                                            │
│         ┌──────────────┐                                    │
│         │ Load Balancer │                                    │
│         │   (Nginx)     │                                    │
│         └───────┬───────┘                                    │
│                 │                                            │
│                 ↓                                            │
│         ┌──────────────┐                                    │
│         │    Users     │                                    │
│         └──────────────┘                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Process:
1. Deploy GREEN alongside BLUE
2. Test GREEN thoroughly
3. Switch load balancer to GREEN
4. Monitor GREEN
5. If issues: Switch back to BLUE
6. If successful: Remove BLUE
```

### Benefits

- ✅ Zero downtime deployment
- ✅ Instant rollback (switch back to BLUE)
- ✅ Full testing before going live
- ✅ Easy recovery from failures

### Implementation

**docker-compose.yml**

```yaml
version: '3.8'

services:
  # BLUE deployment (current)
  app-blue:
    image: myapp:v1.0
    container_name: app-blue
    environment:
      - DEPLOYMENT_COLOR=blue
      - PORT=8000
      - MODEL_VERSION=1.0
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # GREEN deployment (new)
  app-green:
    image: myapp:v2.0
    container_name: app-green
    environment:
      - DEPLOYMENT_COLOR=green
      - PORT=8001
      - MODEL_VERSION=2.0
    ports:
      - "8001:8001"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Load balancer
  nginx:
    image: nginx:latest
    container_name: nginx-lb
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app-blue
      - app-green
    restart: unless-stopped
```

**nginx.conf (Blue active)**

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        # Point to BLUE (current)
        server app-blue:8000;
        # server app-green:8001;  # Switch to GREEN
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # Health check endpoint
            proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        }

        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

**Deployment Script**

```bash
#!/bin/bash
# deploy-blue-green.sh

set -e

BLUE_PORT=8000
GREEN_PORT=8001
NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: ./deploy-blue-green.sh <version>"
    exit 1
fi

echo "=== Blue-Green Deployment ==="
echo "New version: $NEW_VERSION"

# 1. Build new version
echo "Step 1: Building new version..."
docker build -t myapp:$NEW_VERSION .

# 2. Deploy GREEN (alongside BLUE)
echo "Step 2: Deploying GREEN..."
docker-compose up -d app-green

# 3. Wait for GREEN to be healthy
echo "Step 3: Waiting for GREEN to be healthy..."
./wait-for-health.sh http://localhost:$GREEN_PORT/health

# 4. Run smoke tests on GREEN
echo "Step 4: Running smoke tests on GREEN..."
./smoke-test.sh http://localhost:$GREEN_PORT

# 5. Switch traffic to GREEN
echo "Step 5: Switching traffic to GREEN..."
cat > nginx.conf <<EOF
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server app-green:$GREEN_PORT;
    }

    server {
        listen 80;
        location / {
            proxy_pass http://backend;
        }
    }
}
EOF

docker-compose exec nginx nginx -s reload

# 6. Monitor GREEN
echo "Step 6: Monitoring GREEN (60 seconds)..."
sleep 60

# Check for errors
if ./check-logs.sh | grep -q "ERROR"; then
    echo "ERROR detected in GREEN! Rolling back..."
    cat > nginx.conf <<EOF
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server app-blue:$BLUE_PORT;
    }

    server {
        listen 80;
        location / {
            proxy_pass http://backend;
        }
    }
}
EOF
    docker-compose exec nginx nginx -s reload
    echo "Rolled back to BLUE"
    exit 1
fi

echo "Step 7: GREEN is healthy! Removing BLUE..."
docker-compose stop app-blue

echo "=== Deployment successful! ==="
echo "BLUE (old) removed"
echo "GREEN (new) is now active"
```

---

## Pattern 2: Canary Deployment

### Concept

```
Load Balancer
    ↓
    ├─→ 90% → BLUE (Current)  ← Production traffic
    └─→ 10% → GREEN (New)     ← Canary traffic
```

Gradually increase traffic to new version:
1. Start with 5% to GREEN
2. Monitor metrics closely
3. If good: Increase to 25%, 50%, 100%
4. If bad: Rollback immediately

### Implementation

```python
from fastapi import FastAPI, Request
import random
from typing import Optional
from prometheus_client import Counter, Histogram

app = FastAPI()

# Metrics
blue_requests = Counter('blue_requests_total', 'Requests to blue')
green_requests = Counter('green_requests_total', 'Requests to green')
green_errors = Counter('green_errors_total', 'Errors in green')
green_latency = Histogram('green_latency_seconds', 'Green latency')


class CanaryDeployment:
    """
    Manages canary deployment with gradual traffic increase.

    Features:
    - Dynamic percentage adjustment
    - Automatic rollback on high error rate
    - Metrics tracking
    """

    def __init__(
        self,
        initial_percentage: int = 5,
        max_percentage: int = 50,
        error_threshold: float = 0.05,
        increase_step: int = 5
    ):
        self.percentage = initial_percentage
        self.max_percentage = max_percentage
        self.error_threshold = error_threshold
        self.increase_step = increase_step

        # Metrics
        self.total_requests = 0
        self.green_requests = 0
        self.green_errors = 0
        self.green_latency_sum = 0.0
        self.green_latency_count = 0

    def should_route_to_green(self) -> bool:
        """
        Decide if request should go to green (canary).

        Uses percentage-based routing.
        """
        return random.randint(1, 100) <= self.percentage

    def record_green_request(self, success: bool, latency: float = 0):
        """Record metrics for green deployment."""
        self.green_requests += 1
        self.green_latency_sum += latency
        self.green_latency_count += 1

        if not success:
            self.green_errors += 1
            green_errors.inc()

    def get_error_rate(self) -> float:
        """Calculate current error rate for green."""
        if self.green_requests == 0:
            return 0.0
        return self.green_errors / self.green_requests

    def get_avg_latency(self) -> float:
        """Get average latency for green."""
        if self.green_latency_count == 0:
            return 0.0
        return self.green_latency_sum / self.green_latency_count

    def adjust_percentage(self):
        """
        Adjust canary percentage based on metrics.

        Increase if error rate is low
        Decrease if error rate is high
        """
        error_rate = self.get_error_rate()

        if error_rate < self.error_threshold * 0.5:
            # Very low error rate, increase traffic
            if self.percentage < self.max_percentage:
                self.percentage = min(
                    self.max_percentage,
                    self.percentage + self.increase_step
                )
                print(f"Increasing canary to {self.percentage}%")

        elif error_rate > self.error_threshold:
            # High error rate, rollback!
            print(f"High error rate: {error_rate:.2%}, rolling back!")
            self.percentage = 0

    def get_status(self) -> dict:
        """Get current canary status."""
        return {
            "canary_percentage": self.percentage,
            "green_requests": self.green_requests,
            "error_rate": self.get_error_rate(),
            "avg_latency": self.get_avg_latency(),
        }


# Global canary manager
canary = CanaryDeployment(
    initial_percentage=5,
    max_percentage=50,
    error_threshold=0.05  # 5% error rate threshold
)


@app.post("/predict")
async def predict(request: PredictRequest):
    """
    Prediction endpoint with canary deployment.
    """
    import time
    start = time.time()
    canary.total_requests += 1

    # Route based on canary percentage
    if canary.should_route_to_green():
        green_requests.inc()

        try:
            # Call green deployment
            result = await predict_green(request)

            # Record success
            latency = time.time() - start
            canary.record_green_request(success=True, latency=latency)
            green_latency.observe(latency)

            # Check if we should adjust percentage
            canary.adjust_percentage()

            return result

        except Exception as e:
            # Record error
            canary.record_green_request(success=False)

            # Fallback to blue on error
            print(f"Green error: {e}, falling back to blue")
            return await predict_blue(request)

    else:
        blue_requests.inc()
        return await predict_blue(request)


@app.get("/canary/status")
async def canary_status():
    """Get current canary deployment status."""
    return canary.get_status()


@app.post("/canary/adjust")
async def adjust_canary(percentage: int):
    """Manually adjust canary percentage."""
    canary.percentage = max(0, min(100, percentage))
    return {"message": f"Canary set to {canary.percentage}%"}
```

### Monitoring Canary

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
canary_percentage = Gauge('canary_percentage', 'Current canary percentage')
blue_requests = Counter('blue_requests_total', 'Requests to blue deployment')
green_requests = Counter('green_requests_total', 'Requests to green deployment')
green_errors = Counter('green_errors_total', 'Errors in green deployment')
green_latency = Histogram('green_latency_seconds', 'Green request latency')


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    from fastapi import Response

    # Update gauge
    canary_percentage.set(canary.percentage)

    return Response(content=generate_latest(), media_type="text/plain")
```

---

## Pattern 3: Rolling Updates

### Concept

Update instances one by one (or in small groups), ensuring some instances are always running.

```
Before:  [v1.0] [v1.0] [v1.0] [v1.0]
Update 1: [v2.0] [v1.0] [v1.0] [v1.0]  ← Update instance 1
Update 2: [v2.0] [v2.0] [v1.0] [v1.0]  ← Update instance 2
Update 3: [v2.0] [v2.0] [v2.0] [v1.0]  ← Update instance 3
Update 4: [v2.0] [v2.0] [v2.0] [v2.0]  ← Update instance 4
```

### Kubernetes Rolling Update

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-model
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Create 1 extra pod during update
      maxUnavailable: 0  # Don't kill any until new ones ready
  selector:
    matchLabels:
      app: ml-model
  template:
    metadata:
      labels:
        app: ml-model
        version: "1.0"  # Update this to trigger rolling update
    spec:
      containers:
      - name: model
        image: myapp:v1.0
        ports:
        - containerPort: 8000
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
```

**Deploy new version:**

```bash
# Update image version
kubectl set image deployment/ml-model model=myapp:v2.0

# Kubernetes automatically does rolling update
# Watch the rollout
kubectl rollout status deployment/ml-model

# If something goes wrong, rollback
kubectl rollout undo deployment/ml-model
```

### Docker Rolling Update

```bash
#!/bin/bash
# rolling-update.sh

set -e

IMAGE=$1
REPLICAS=4
MAX_UNAVAILABLE=1

echo "Starting rolling update to $IMAGE"

# Get current containers
CONTAINERS=$(docker ps -q --filter "label=app=mlmodel")
CURRENT_COUNT=$(echo "$CONTAINERS" | wc -l)

if [ "$CURRENT_COUNT" -ne "$REPLICAS" ]; then
    echo "Expected $REPLICAS containers, found $CURRENT_COUNT"
    exit 1
fi

# Update one by one
for i in $(seq 1 $REPLICAS); do
    echo "Updating container $i/$REPLICAS"

    # Get container to update
    CONTAINER=$(echo "$CONTAINERS" | sed -n "${i}p")

    # Start new container
    NEW_CONTAINER=$(docker run -d \
        --label "app=mlmodel" \
        --label "version=$IMAGE" \
        -p 8000 \
        $IMAGE)

    # Wait for health check
    echo "Waiting for new container to be healthy..."
    sleep 10

    if docker inspect --format='{{.State.Health.Status}}' $NEW_CONTAINER | grep -q "healthy"; then
        echo "New container healthy, stopping old one..."
        docker stop $CONTAINER
        docker rm $CONTAINER

        # Update container list
        CONTAINERS=$(docker ps -q --filter "label=app=mlmodel")
    else
        echo "New container unhealthy, rolling back..."
        docker stop $NEW_CONTAINER
        docker rm $NEW_CONTAINER
        exit 1
    fi
done

echo "Rolling update complete!"
```

---

## Pattern 4: A/B Testing

### Purpose

Compare model versions in production to determine which performs better.

```
Model A (Control)     Model B (Treatment)
    │                      │
    ├─→ 50% traffic        ├─→ 50% traffic
    │                      │
    ↓                      ↓
[Metrics Collection]  [Metrics Collection]
    │                      │
    └──────────┬───────────┘
               ↓
         [Analysis & Decision]
```

### Implementation

```python
from typing import Dict, Any
from enum import Enum
import hashlib


class ABTestModel(Enum):
    """Available models for A/B testing."""
    MODEL_A = "mistral-7b-v1.0"
    MODEL_B = "mistral-7b-v2.0"


class ABTestDeployment:
    """
    A/B testing deployment for ML models.

    Features:
    - Consistent routing (same user always gets same model)
    - Metrics collection per model
    - Statistical analysis
    """

    def __init__(
        self,
        model_a_name: str,
        model_b_name: str,
        split_percentage: int = 50
    ):
        self.model_a_name = model_a_name
        self.model_b_name = model_b_name
        self.split_percentage = split_percentage

        # Metrics
        self.metrics = {
            "model_a": {
                "requests": 0,
                "errors": 0,
                "latency_sum": 0.0,
                "user_feedback": {"positive": 0, "negative": 0}
            },
            "model_b": {
                "requests": 0,
                "errors": 0,
                "latency_sum": 0.0,
                "user_feedback": {"positive": 0, "negative": 0}
            }
        }

    def get_model_for_user(self, user_id: str) -> ABTestModel:
        """
        Get model for specific user.

        Uses hash of user_id for consistent assignment.
        """
        # Hash user ID to get number 0-99
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = hash_val % 100

        if bucket < self.split_percentage:
            return ABTestModel.MODEL_B
        else:
            return ABTestModel.MODEL_A

    def get_model_name(self, model: ABTestModel) -> str:
        """Get model name from enum."""
        if model == ABTestModel.MODEL_A:
            return self.model_a_name
        else:
            return self.model_b_name

    def record_request(self, model: ABTestModel, latency: float, success: bool):
        """Record request metrics."""
        model_key = "model_a" if model == ABTestModel.MODEL_A else "model_b"

        self.metrics[model_key]["requests"] += 1
        self.metrics[model_key]["latency_sum"] += latency

        if not success:
            self.metrics[model_key]["errors"] += 1

    def record_feedback(self, model: ABTestModel, positive: bool):
        """Record user feedback."""
        model_key = "model_a" if model == ABTestModel.MODEL_A else "model_b"

        if positive:
            self.metrics[model_key]["user_feedback"]["positive"] += 1
        else:
            self.metrics[model_key]["user_feedback"]["negative"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get A/B test summary."""
        summary = {}

        for model_key, metrics in self.metrics.items():
            requests = metrics["requests"]
            errors = metrics["errors"]
            latency_sum = metrics["latency_sum"]
            feedback = metrics["user_feedback"]

            positive = feedback["positive"]
            negative = feedback["negative"]
            total_feedback = positive + negative

            summary[model_key] = {
                "requests": requests,
                "error_rate": errors / requests if requests > 0 else 0,
                "avg_latency": latency_sum / requests if requests > 0 else 0,
                "satisfaction_rate": positive / total_feedback if total_feedback > 0 else 0,
                "total_feedback": total_feedback
            }

        return summary

    def get_winner(self) -> Dict[str, Any]:
        """
        Determine winning model based on metrics.

        Considers:
        - Lower error rate
        - Lower latency
        - Higher satisfaction rate
        """
        summary = self.get_summary()

        model_a_stats = summary["model_a"]
        model_b_stats = summary["model_b"]

        # Calculate scores (normalized)
        scores = {}

        for model_key, stats in summary.items():
            score = (
                (1 - stats["error_rate"]) * 0.4 +  # Lower error is better
                (1 / (stats["avg_latency"] + 0.001)) * 0.3 +  # Lower latency is better
                stats["satisfaction_rate"] * 0.3  # Higher satisfaction is better
            )
            scores[model_key] = score

        winner = "model_a" if scores["model_a"] > scores["model_b"] else "model_b"

        return {
            "winner": winner,
            "confidence": abs(scores["model_a"] - scores["model_b"]),
            "scores": scores,
            "summary": summary
        }


# Global A/B test manager
ab_test = ABTestDeployment(
    model_a_name="mistral-7b-v1.0",
    model_b_name="mistral-7b-v2.0",
    split_percentage=50  # 50/50 split
)


@app.post("/predict")
async def predict_ab(request: PredictRequest, user_id: str):
    """
    Prediction endpoint with A/B testing.
    """
    import time

    # Get model for this user
    model_enum = ab_test.get_model_for_user(user_id)
    model_name = ab_test.get_model_name(model_enum)

    # Run inference
    start = time.time()

    try:
        result = await predict_with_model(model_name, request)
        success = True
    except Exception as e:
        success = False
        raise

    latency = time.time() - start

    # Record metrics
    ab_test.record_request(model_enum, latency, success)

    # Add model info to response
    result["model"] = model_name
    result["ab_test"] = True

    return result


@app.post("/feedback")
async def submit_feedback(user_id: str, positive: bool):
    """
    Submit feedback for A/B testing.

    Called when user thumbs up/down a response.
    """
    # Get which model this user was assigned to
    model_enum = ab_test.get_model_for_user(user_id)

    # Record feedback
    ab_test.record_feedback(model_enum, positive)

    return {"status": "recorded"}


@app.get("/ab-test/results")
async def ab_test_results():
    """Get A/B test results and winner."""
    return ab_test.get_winner()
```

### Analyzing Results

```python
from scipy import stats

def analyze_ab_test(metrics: dict) -> dict:
    """
    Perform statistical analysis on A/B test results.

    Returns:
        Statistical significance and recommendations
    """
    model_a = metrics["model_a"]
    model_b = metrics["model_b"]

    # Compare error rates
    # (Simplified - would use proper statistical tests)
    error_rate_a = model_a["error_rate"]
    error_rate_b = model_b["error_rate"]

    # Compare satisfaction rates
    satisfaction_a = model_a["satisfaction_rate"]
    satisfaction_b = model_b["satisfaction_rate"]

    # Calculate improvement
    error_improvement = (error_rate_a - error_rate_b) / error_rate_a
    satisfaction_improvement = (satisfaction_b - satisfaction_a) / satisfaction_a

    # Determine if significant
    # (In practice, use chi-square or t-test)
    is_significant = abs(error_improvement) > 0.05 or abs(satisfaction_improvement) > 0.05

    return {
        "error_improvement": error_improvement,
        "satisfaction_improvement": satisfaction_improvement,
        "is_significant": is_significant,
        "recommendation": "model_b" if satisfaction_improvement > 0 else "model_a"
    }
```

---

## Deployment Automation

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy ML Model

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Build Docker image
        run: |
          docker build -t myapp:${{ github.sha }} .
          docker tag myapp:${{ github.sha }} myapp:latest

      - name: Run tests
        run: |
          docker run myapp:${{ github.sha }} pytest

      - name: Deploy to staging (canary)
        run: |
          # Deploy as canary
          ./deploy-canary.sh myapp:${{ github.sha }}

      - name: Run smoke tests
        run: |
          ./smoke-test.sh https://staging.example.com

      - name: Promote to production
        if: success()
        run: |
          # Gradually increase traffic
          ./promote-canary.sh
```

---

## Exercise: Deploy with Blue-Green

### Task

Implement a complete blue-green deployment system with:
1. Docker Compose setup
2. Nginx load balancer
3. Deployment script
4. Rollback capability

### Starter Code

```bash
# TODO: Create docker-compose.yml with blue and green services
# TODO: Create nginx.conf with upstream configuration
# TODO: Create deploy.sh script
# TODO: Create rollback.sh script
# TODO: Create health check script
```

---

## Related Topics

- [TUTORIAL-005: Production Deployment](../../../learning-resources/tutorials/TUTORIAL-005-Production-Deployment.md)
- [LAB-009: Production Deployment](../../../learning-resources/labs/LAB-009-Production-Deployment.md)
- [2302: Model Serving Architectures](./2302-Model-Serving-Architectures.md)
- [2303: API Design for ML](./2303-API-Design-for-ML.md)

---

## Next Steps

- Next Module: **[2400: Pretraining](../2400-pretraining/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

## Summary

**Key Deployment Patterns:**

1. **Blue-Green** - Zero downtime, instant rollback
2. **Canary** - Gradual rollout, automatic rollback
3. **Rolling** - Continuous delivery, minimal disruption
4. **A/B Testing** - Data-driven model comparison

**Best Practices:**
- Always test new deployments before switching traffic
- Monitor metrics closely during rollout
- Have automated rollback procedures
- Use feature flags for quick disabling
