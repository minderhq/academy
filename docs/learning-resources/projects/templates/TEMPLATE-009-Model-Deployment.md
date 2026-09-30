---
Document ID: TEMPLATE-009-Model-Deployment
Title: "PROJECT TEMPLATE: Model Deployment"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Tags: ['template', 'deployment', 'serving']
---

# PROJECT TEMPLATE: Model Deployment

Deploy LLMs to production with various serving options.

## Project Structure

```text
llm-deployment/
├── README.md
├── pyproject.toml
├── uv.lock
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── config/
│   ├── serving_config.yaml
│   ├── model_config.yaml
│   └── scaling_config.yaml
├── src/
│   ├── __init__.py
│   ├── servers/
│   │   ├── __init__.py
│   │   ├── vllm_server.py
│   │   ├── trt_llm.py
│   │   └── tgi_server.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── fastapi_app.py
│   │   ├── grpc_server.py
│   │   └── websocket_handler.py
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── logging.py
│   │   └── alerts.py
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── kv_cache.py
│   │   └── response_cache.py
│   └── utils/
│   │   ├── __init__.py
│   │   ├── load_balancer.py
│   │   └── health_check.py
├── kubernetes/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── scripts/
    ├── deploy.sh
    ├── monitor.sh
    └── scale.sh
```

## Features

- Multiple serving backends (vLLM, TGI, TensorRT-LLM)
- API servers (REST, gRPC, WebSocket)
- Kubernetes deployment
- Monitoring and logging
- Auto-scaling
- Load balancing

## Quick Start

### Docker Deployment

```bash
# Build image
docker build -t llm-serving:latest .

# Run container
docker run -p 8000:80 \
  --gpus all \
  -v ./models:/models \
  llm-serving:latest
```

### vLLM Serving

```python
from src.servers.vllm_server import vLLMServer

server = vLLMServer(
    model="meta-llama/Llama-2-7b-hf",
    tensor_parallel_size=2,
    max_model_len=4096,
    quantization="awq"
)

server.start(port=8000)
```

### TensorRT-LLM

```python
from src.servers.trt_llm import TensorRTLLMServer

server = TensorRTLLMServer(
    engine_path="./models/llama-7b.trtllm",
    max_batch_size=32,
    max_input_len=1024,
    max_output_len=512
)

server.start(port=8001)
```

## API Options

### REST (FastAPI)

```python
from src.api.fastapi_app import create_app

app = create_app(model_config)

# Generate endpoint
@app.post("/generate")
async def generate(request: GenerationRequest):
    return await model.generate(request.prompt)
```

### gRPC

```python
from src.api.grpc_server import serve

serve(
    model=model,
    port=50051,
    max_workers=4
)
```

### WebSocket

```python
from src.api.websocket_handler import WebSocketHandler

handler = WebSocketHandler(model)
handler.start(port=8002)
```

## Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-serving
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: llm
        image: llm-serving:latest
        resources:
          limits:
            nvidia.com/gpu: 1
```

Apply:
```bash
kubectl apply -f kubernetes/
```

## Monitoring

Prometheus metrics:
```python
from src.monitoring.metrics import PrometheusMetrics

metrics = PrometheusMetrics()

# Track metrics
metrics.track_request(duration=1.5, tokens_generated=100)
metrics.track_gpu_memory(gpu_id=0, memory_used=8.5)
```

Alerting rules:
```yaml
groups:
  - name: llm_alerts
    rules:
      - alert: HighLatency
        expr: latency_p95 > 5000
        for: 5m
```

## Load Balancing

```python
from src.utils.load_balancer import LoadBalancer

lb = LoadBalancer(
    backends=[
        "http://server1:8000",
        "http://server2:8000",
        "http://server3:8000"
    ],
    strategy="least_connections"
)

response = lb.forward(request)
```

## Auto-scaling

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-serving
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

---

**Difficulty:** ⭐⭐⭐ Advanced
**Estimated Time:** 10-20 hours
**Skills:** Docker, Kubernetes, GPU serving, Monitoring
