---
Document ID: 2304
Title: "2304: Production Deployment Patterns"
Phase: 2
Module: 2300
Last Updated: 2026-09-28
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'architecture', 'api-design', 'production']
---

# 2304: Production Deployment Patterns

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Pattern 1: Blue-Green Deployment](#pattern-1-blue-green-deployment)
- [Pattern 2: Canary Deployment](#pattern-2-canary-deployment)
- [Pattern 3: Rolling Updates](#pattern-3-rolling-updates)
- [Pattern 4: A/B Testing](#pattern-4-ab-testing)
- [Deployment Automation](#deployment-automation)
- [Exercise: Deploy with Blue-Green](#exercise-deploy-with-blue-green)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Execute zero-downtime releases with blue-green deployment: two full stacks, one load-balancer switch, instant rollback
- Roll models out gradually with canary releases that promote on healthy metrics and fail over to the stable variant per-request
- Perform rolling updates on Kubernetes (`maxSurge` / `maxUnavailable`, readiness vs liveness probes, `minReadySeconds`) and on plain Docker hosts
- Run production A/B tests with hash-bucketed sticky assignment and chi-square significance testing over raw outcome counts
- Wire the release path into CI/CD: build, test, canary to staging, smoke-test, promote

---

## Abstract

Deploying ML systems to production requires careful planning to ensure zero downtime, easy rollbacks, and reliable updates. This document covers industry-standard deployment patterns.

**What You'll Learn:**
- Blue-green deployment for zero downtime
- Canary deployment for gradual rollouts
- Rolling updates for continuous delivery
- A/B testing for model comparison

---

## Pattern 1: Blue-Green Deployment

### Concept

Two identical stacks run side by side. The load balancer points at one of them, and switching versions is a one-line upstream edit - not a redeploy.

```text
        ┌──────────────┐
        │    Users     │
        └──────┬───────┘
               │
        ┌──────▼───────┐
        │ Load Balancer │
        │    (nginx)   │
        └──────┬───────┘
               │  one upstream line decides the target
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ BLUE (v1.0)  │  │ GREEN (v2.0) │
│ Port 8000    │  │ Port 8001    │
│ active       │  │ standby      │
└──────────────┘  └──────────────┘
```

Process:
1. Deploy GREEN alongside BLUE
2. Test GREEN thoroughly
3. Switch load balancer to GREEN
4. Monitor GREEN
5. If issues: Switch back to BLUE
6. If successful: Remove BLUE

### Benefits

- ✅ Zero downtime deployment
- ✅ Instant rollback (switch back to BLUE)
- ✅ Full testing before going live
- ✅ Easy recovery from failures

### Implementation

**docker-compose.yml**

```yaml
services:
  # BLUE deployment (current)
  app-blue:
    # Interpolated so scripts can pin the exact build they tested; the
    # default keeps the file runnable on its own.
    image: ${BLUE_IMAGE:-myapp:v1.0}
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
      # curl must ship in the image - slim base images omit it (swap in
      # wget or a tiny native health fetcher if it does not).
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # GREEN deployment (new)
  app-green:
    image: ${GREEN_IMAGE:-myapp:v2.0}
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

            # Fail over to the other upstream member on backend errors
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
    echo "Usage: ./deploy-blue-green.sh NEW_VERSION"
    exit 1
fi

echo "=== Blue-Green Deployment ==="
echo "New version: $NEW_VERSION"

# 1. Build new version
echo "Step 1: Building new version..."
docker build -t "myapp:$NEW_VERSION" .

# 2. Deploy GREEN (alongside BLUE). docker compose = the Compose V2 CLI
# plugin (the hyphenated docker-compose v1 binary is EOL). The image is
# passed through the environment so the version under test matches the one
# we just built - compose's hardcoded image tag would silently start
# yesterday's build otherwise.
echo "Step 2: Deploying GREEN..."
GREEN_IMAGE="myapp:$NEW_VERSION" docker compose up -d app-green

# 3. Wait for GREEN to be healthy (BLUE keeps serving traffic throughout)
echo "Step 3: Waiting for GREEN to be healthy..."
healthy=""
for i in $(seq 1 30); do
    if curl -fsS "http://localhost:$GREEN_PORT/health" > /dev/null 2>&1; then
        healthy=yes
        break
    fi
    sleep 2
done
if [ "$healthy" != "yes" ]; then
    echo "GREEN never became healthy - aborting, BLUE still serves traffic"
    docker compose stop app-green
    exit 1
fi

# 4. Run smoke tests on GREEN (repo helper: fires representative requests
# against the base URL and exits non-zero on any failure)
echo "Step 4: Running smoke tests on GREEN..."
./smoke-test.sh "http://localhost:$GREEN_PORT"

# 5. Switch traffic to GREEN (one upstream edit + a hot reload)
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

docker compose exec nginx nginx -s reload

# 6. Monitor GREEN (repo helper: greps the compose logs for ERROR lines)
echo "Step 6: Monitoring GREEN (60 seconds)..."
sleep 60

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
    docker compose exec nginx nginx -s reload
    # Take the failed GREEN down too - an orphaned canary keeps burning
    # GPU memory and answering nothing.
    docker compose stop app-green
    echo "Rolled back to BLUE"
    exit 1
fi

echo "Step 7: GREEN is healthy! Removing BLUE..."
docker compose stop app-blue

echo "=== Deployment successful! ==="
echo "BLUE (old) removed"
echo "GREEN (new) is now active"
```

---

## Pattern 2: Canary Deployment

### Concept

```text
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
from fastapi import FastAPI, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge
import random
import time

# A fresh app per deployment pattern: Starlette serves the FIRST matching
# route, so piling every pattern onto one app would turn all later /predict
# definitions into dead code (same rule as 2303's middleware blocks).
app = FastAPI()


class PredictRequest(BaseModel):
    prompt: str
    max_tokens: int = 64


# Metric names live in prometheus_client's process-wide default registry -
# redefining any of these later raises "Duplicated timeseries".
blue_requests = Counter('blue_requests_total', 'Requests to blue')
green_requests = Counter('green_requests_total', 'Requests to green')
green_errors = Counter('green_errors_total', 'Errors in green')
green_latency = Histogram('green_latency_seconds', 'Green latency')
canary_percentage = Gauge('canary_percentage', 'Current canary percentage')


# Stand-ins for the two model services. In production these proxy to the
# blue/green backends from Pattern 1; locally they just echo so the block
# runs end to end.
async def predict_blue(request: PredictRequest) -> dict:
    return {"prediction": f"blue:{request.prompt[:8]}"}


async def predict_green(request: PredictRequest) -> dict:
    return {"prediction": f"green:{request.prompt[:8]}"}


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

        Uses percentage-based routing (randint is inclusive on both ends).
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
    start = time.perf_counter()  # monotonic - immune to wall-clock jumps
    canary.total_requests += 1

    # Route based on canary percentage
    if canary.should_route_to_green():
        green_requests.inc()

        try:
            result = await predict_green(request)

            # Record success
            latency = time.perf_counter() - start
            canary.record_green_request(success=True, latency=latency)
            green_latency.observe(latency)

            # Healthy canary earns more traffic
            canary.adjust_percentage()

            return result

        except Exception as e:
            # Record the failure, then fail over to blue - the canary must
            # never take users down with it.
            canary.record_green_request(success=False)
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
    """Manually adjust canary percentage (ops override; query parameter)."""
    canary.percentage = max(0, min(100, percentage))
    return {"message": f"Canary set to {canary.percentage}%"}
```

### Monitoring Canary

```python
# The /metrics route attaches to the canary app above and reads the SAME
# metric objects - redefining blue_requests and friends here would raise
# prometheus_client's Duplicated timeseries, because metric names are
# process-global.

@app.get("/metrics")
async def metrics():
    """Prometheus exposition with the canary gauge kept current."""
    from prometheus_client import generate_latest

    # Gauges are set-at-scrape: publish the live percentage here so
    # dashboards track the rollout without waiting for a /predict call.
    canary_percentage.set(canary.percentage)

    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4"  # text exposition format
    )
```

---

## Pattern 3: Rolling Updates

### Concept

Update instances one by one (or in small groups), ensuring some instances are always running.

```text
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
  # A pod must stay Ready this many seconds before the rollout counts it as
  # available and proceeds - the pause that catches crash-looping replicas
  # before they consume the whole update.
  minReadySeconds: 30
  # Fail the rollout loudly if it stops making progress (default 600s).
  progressDeadlineSeconds: 300
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Create 1 extra pod during update
      maxUnavailable: 0  # Don't kill any until new ones ready
                         # (maxSurge and maxUnavailable cannot both be 0)
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
# rolling-update.sh - one-at-a-time replacement for plain Docker hosts.
# Requires HEALTHCHECK baked into the image: a healthcheck declared in a
# compose file does NOT transfer to docker run, so without one in the image
# .State.Health would not even exist and every probe would read "unknown".

set -e

IMAGE=$1
REPLICAS=4

if [ -z "$IMAGE" ]; then
    echo "Usage: ./rolling-update.sh ${IMAGE}"
    exit 1
fi

echo "Starting rolling update to $IMAGE"

# Count via a direct pipe: '$(echo "$X" | wc -l)' reports 1 for an empty
# list because echo still emits a newline.
CURRENT_COUNT=$(docker ps -q --filter "label=app=mlmodel" | wc -l)
if [ "$CURRENT_COUNT" -ne "$REPLICAS" ]; then
    echo "Expected $REPLICAS containers, found $CURRENT_COUNT"
    exit 1
fi

# Snapshot the OLD container IDs once, before any replacement exists.
# (Refreshing the list mid-loop "works" only by accident: docker ps lists
# newest first, so every started replacement shifts the indices.)
OLD_CONTAINERS=$(docker ps -q --filter "label=app=mlmodel")

for OLD in $OLD_CONTAINERS; do
    echo "Replacing $OLD"

    # -p 8000 publishes on a random host port; the nginx upstream from
    # Pattern 1 is what actually steers traffic to these targets.
    NEW=$(docker run -d \
        --label "app=mlmodel" \
        --label "version=$IMAGE" \
        -p 8000 \
        "$IMAGE")

    # Poll instead of one fixed sleep - a model that loads weights from
    # disk can easily take longer than 10s to pass its health gate.
    healthy=""
    for i in $(seq 1 30); do
        status=$(docker inspect --format='{{.State.Health.Status}}' "$NEW" 2>/dev/null || echo "unknown")
        if [ "$status" = "healthy" ]; then
            healthy=yes
            break
        fi
        sleep 2
    done

    if [ "$healthy" = "yes" ]; then
        echo "New container healthy, draining old one..."
        docker stop "$OLD"
        docker rm "$OLD"
    else
        echo "New container unhealthy, rolling back..."
        docker stop "$NEW"
        docker rm "$NEW"
        exit 1
    fi
done

echo "Rolling update complete!"
```

---

## Pattern 4: A/B Testing

### Purpose

Compare model versions in production to determine which performs better.

```text
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
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
from enum import Enum
import hashlib
import time

# Fresh app again - same first-matching-route rule as the canary block.
app = FastAPI()


class PredictRequest(BaseModel):
    prompt: str
    max_tokens: int = 64


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

        Uses hash of user_id for consistent assignment: the same user_id
        always lands in the same bucket, so nobody sees both variants
        mid-test. (MD5 is fine here - this is bucketing, not a crypto use.)
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

    def get_summary(self) -> dict[str, Any]:
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

    def get_winner(self) -> dict[str, Any]:
        """
        Determine leading model based on metrics.

        Considers (each term bounded to [0, 1]):
        - Lower error rate
        - Lower latency
        - Higher satisfaction rate
        """
        summary = self.get_summary()

        # Calculate scores (normalized)
        scores = {}

        for model_key, stats in summary.items():
            score = (
                (1 - stats["error_rate"]) * 0.4 +        # lower error is better
                (1 / (1 + stats["avg_latency"])) * 0.3 + # lower latency is better
                stats["satisfaction_rate"] * 0.3         # higher satisfaction is better
            )
            scores[model_key] = score

        # On a tie, keep the incumbent - the control only loses on evidence.
        winner = "model_a" if scores["model_a"] >= scores["model_b"] else "model_b"

        return {
            "winner": winner,
            # Score gap, NOT statistical confidence - significance testing
            # lives in analyze_ab_test below.
            "score_gap": abs(scores["model_a"] - scores["model_b"]),
            "scores": scores,
            "summary": summary
        }


# Global A/B test manager
ab_test = ABTestDeployment(
    model_a_name="mistral-7b-v1.0",
    model_b_name="mistral-7b-v2.0",
    split_percentage=50  # 50/50 split
)


# Stand-in for the model registry (production routes to the serving stack
# from 2302; locally it echoes so the block runs end to end).
async def predict_with_model(model_name: str, request: PredictRequest) -> dict:
    return {"prediction": f"{model_name}:{request.prompt[:8]}"}


@app.post("/predict")
async def predict_ab(request: PredictRequest, user_id: str):
    """
    Prediction endpoint with A/B testing.

    user_id is a required query parameter and keys the sticky assignment.
    """
    # Get model for this user
    model_enum = ab_test.get_model_for_user(user_id)
    model_name = ab_test.get_model_name(model_enum)

    # Run inference
    start = time.perf_counter()

    try:
        result = await predict_with_model(model_name, request)
    except Exception:
        # Record BEFORE re-raising. Setting success = False and then raising
        # straight past record_request meant failed requests never entered
        # the metrics at all - silent metric loss.
        ab_test.record_request(model_enum, time.perf_counter() - start, False)
        raise

    latency = time.perf_counter() - start

    # Record metrics
    ab_test.record_request(model_enum, latency, True)

    # Add model info to response
    result["model"] = model_name
    result["ab_test"] = True

    return result


@app.post("/feedback")
async def submit_feedback(user_id: str, positive: bool):
    """
    Submit feedback for A/B testing.

    Called when a user thumbs up/down a response. The hash assignment is
    deterministic, so feedback lands on the variant that served the user -
    no session state required.
    """
    # Get which model this user was assigned to
    model_enum = ab_test.get_model_for_user(user_id)

    # Record feedback
    ab_test.record_feedback(model_enum, positive)

    return {"status": "recorded"}


@app.get("/ab-test/results")
async def ab_test_results():
    """Get A/B test results and current leader."""
    return ab_test.get_winner()
```

### Analyzing Results

```python
from scipy import stats as sps


def analyze_ab_test(metrics: dict, alpha: float = 0.05) -> dict:
    """
    Perform statistical analysis on A/B test results.

    Runs chi-square tests over the RAW counts the deployment already tracks
    (errors vs requests, positive vs negative feedback), replacing the old
    hand-rolled "improvement > 0.05" heuristic - which divided by zero on
    clean variants and ignored sample size entirely.

    Usage: analyze_ab_test(ab_test.metrics)
    """

    def chi2_p(successes_a: int, total_a: int,
               successes_b: int, total_b: int) -> float:
        """p-value for "do the two variants differ?" over a 2x2 outcome table."""
        # No observations -> no evidence either way.
        if total_a == 0 or total_b == 0:
            return 1.0
        # Every observation identical (all success or all failure) ->
        # chi2_contingency refuses the degenerate table; the honest answer
        # is "no detectable difference".
        if (successes_a + successes_b) == 0 or \
           ((total_a - successes_a) + (total_b - successes_b)) == 0:
            return 1.0
        _, p, _, _ = sps.chi2_contingency([
            [successes_a, total_a - successes_a],
            [successes_b, total_b - successes_b],
        ])
        return float(p)

    model_a, model_b = metrics["model_a"], metrics["model_b"]

    error_p = chi2_p(
        model_a["errors"], model_a["requests"],
        model_b["errors"], model_b["requests"]
    )
    pos_a = model_a["user_feedback"]["positive"]
    neg_a = model_a["user_feedback"]["negative"]
    pos_b = model_b["user_feedback"]["positive"]
    neg_b = model_b["user_feedback"]["negative"]
    satisfaction_p = chi2_p(pos_a, pos_a + neg_a, pos_b, pos_b + neg_b)

    # Descriptive effect sizes for the report (guarded against the zero
    # baselines that crashed the old version).
    def rate(part: int, total: int) -> float:
        return part / total if total else 0.0

    error_rate_a = rate(model_a["errors"], model_a["requests"])
    error_rate_b = rate(model_b["errors"], model_b["requests"])
    sat_a = rate(pos_a, pos_a + neg_a)
    sat_b = rate(pos_b, pos_b + neg_b)

    is_significant = (error_p < alpha) or (satisfaction_p < alpha)

    if satisfaction_p < alpha:
        recommendation = "model_b" if sat_b > sat_a else "model_a"
    elif error_p < alpha:
        recommendation = "model_b" if error_rate_b < error_rate_a else "model_a"
    else:
        recommendation = "keep both - no significant difference yet (collect more data)"

    return {
        "error_rate_p": error_p,
        "satisfaction_p": satisfaction_p,
        "alpha": alpha,
        "is_significant": is_significant,
        "error_improvement": error_rate_a - error_rate_b,
        "satisfaction_improvement": sat_b - sat_a,
        "recommendation": recommendation,
    }


# Worked example: variant B cuts errors 20 -> 8 per 1000 requests and lifts
# satisfaction. At n=1000 both tests flag the difference; the same rates at
# n=10 would (correctly) not.
demo_metrics = {
    "model_a": {"requests": 1000, "errors": 20, "latency_sum": 42.0,
                "user_feedback": {"positive": 640, "negative": 160}},
    "model_b": {"requests": 1000, "errors": 8, "latency_sum": 38.0,
                "user_feedback": {"positive": 740, "negative": 110}},
}
result = analyze_ab_test(demo_metrics)
# -> error_rate_p ≈ 0.036, satisfaction_p ≈ 1.4e-04, is_significant True,
#    recommendation 'model_b' (chi2_contingency applies Yates' continuity
#    correction by default on 2x2 tables)
print(result["recommendation"], "| significant:", result["is_significant"])
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
      - uses: actions/checkout@v7  # current major - @v2 was five majors stale

      - name: Build Docker image
        run: |
          docker build -t myapp:${{ github.sha }} .
          docker tag myapp:${{ github.sha }} myapp:latest

      - name: Run tests
        run: |
          # Overrides the image CMD with pytest - only sane if the image
          # ships pytest and a tolerant ENTRYPOINT; most repos run tests in
          # a separate stage or CI image instead.
          docker run myapp:${{ github.sha }} pytest

      - name: Deploy to staging (canary)
        run: |
          # Deploy as canary (repo helpers)
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
#       (interpolate the images: ${BLUE_IMAGE:-myapp:v1.0} / ${GREEN_IMAGE:-myapp:v2.0})
# TODO: Create nginx.conf with upstream configuration
# TODO: Create deploy.sh script (build -> deploy GREEN -> health gate -> switch -> monitor -> promote or roll back)
# TODO: Create rollback.sh script (upstream edit back to BLUE + nginx -s reload)
# TODO: Create health check script (curl retry loop, non-zero exit on timeout)
```

---

## Summary

- **Blue-green** trades double the footprint for the strongest guarantees: both stacks run at once, the cutover is one nginx upstream edit, and rollback is switching it back.
- **Canary** buys safety with percentages: route a slice to the new version, promote on healthy metrics, and fall back to blue per-request when the canary errors.
- **Rolling updates** replace instances one at a time - Kubernetes does it declaratively (`maxSurge` / `maxUnavailable` + probes + `minReadySeconds`), plain Docker does it with a capture-once container list and a health poll per replacement.
- **A/B testing** needs sticky assignment (hash the user id) and honest statistics (chi-square over raw counts), not raw rate comparisons - small samples lie.
- **Whatever the pattern:** health gates before traffic, monitoring during rollout, automated rollback, and CI/CD that smoke-tests before promoting.

## References

### Related Documents

- [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md)
- [2302: Model Serving Architectures](./2302-Model-Serving-Architectures.md)
- [2303: API Design for ML Systems](./2303-API-Design-for-ML.md)

### External References

- [Deployments — Kubernetes](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Module ngx_http_upstream_module — nginx](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)
- [Compose file version and name — Docker Docs](https://docs.docker.com/reference/compose-file/version-and-name/)
- [docker container ls (filters) — Docker Docs](https://docs.docker.com/reference/cli/docker/container/ls/)
- [Workflow syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)

## Next Steps

- Next Module: **[2400: LLM Pretraining](../2400-pretraining/)**
- Assessment: **[2300: Framework Engineering - Quiz](./assessment/QUIZ.md)**

**Related:** [LAB-009: Production Deployment](../../../learning-resources/labs/LAB-009-Production-Deployment.md), [TUTORIAL-005: Production Deployment with CI/CD](../../../learning-resources/tutorials/TUTORIAL-005-Production-Deployment.md), [1501: Monitoring and Observability](../../phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)

**Experiment:** [EXP_1501: Monitoring and Observability Experiments](../../../../experiments/EXP_1501_MONITORING.md) (nearest-relevant - no EXP_23xx exists; the canary and rollout sections above live or die on the metrics this experiment wires up)
