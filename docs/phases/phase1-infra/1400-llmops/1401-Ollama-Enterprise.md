---
Document ID: 1401
Title: Ollama Enterprise Deployment
Phase: 1
Module: 1400
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'llmops', 'ollama', 'vllm', 'tgi']
---

# 1401: Ollama Enterprise Deployment

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Architecture](#architecture)
- [Installation](#installation)
- [Model Management](#model-management)
- [API Usage](#api-usage)
- [Configuration Options](#configuration-options)
- [Performance Optimization](#performance-optimization)
- [Service Mesh Integration](#service-mesh-integration)
- [Monitoring](#monitoring)
- [Security](#security)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Diagram the client → server → model-storage chain and locate each piece on the K3s GPU node
- Deploy a pinned Ollama image on Kubernetes with GPU resources, or natively on the VM, and confirm CUDA is actually serving (ollama ps, journalctl)
- Pull models, read registry tags and sizes (7b-chat-q4_K_M-style suffixes), and build a custom model from GGUF with a Modelfile
- Call the generate / chat / show endpoints and stream responses from both curl and the Python client
- Tune the server with the env vars that exist (KEEP_ALIVE, NUM_PARALLEL, FLASH_ATTENTION, KV_CACHE_TYPE) and avoid the silently-ignored ones
- Keep one hot model resident per 11GB GPU, preload it with keep_alive, and budget KV cache as num_ctx × NUM_PARALLEL instead of guessing

---

## Abstract
Ollama enables running large language models locally with a simple API. In AI Engineering Curriculum, Ollama serves as the model inference backend across the lab network.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                   Client Layer                          │
│  Python Apps, REST APIs, CLI Tools                      │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP/11434
┌─────────────────────────────────────────────────────────┐
│                   Ollama Server                         │
│  [K3s Pod → GPU Node → 11GB-class GPU]                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Model Storage                         │
│  [NFS storage: /srv/ollama/models]                     │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Method 1: Docker/Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: ai-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      nodeSelector:
        accelerator: nvidia-gpu
      containers:
      - name: ollama
        image: ollama/ollama:0.34.4  # ⚠️ PIN SPECIFIC VERSION in production! Never use :latest
        # Check https://github.com/ollama/ollama/releases for latest stable version
        # Using :latest can break production when new versions are released
        ports:
        - containerPort: 11434
          name: http
        env:
        - name: OLLAMA_HOST
          value: "0.0.0.0"
        - name: OLLAMA_MODELS
          value: "/models"             # must match the volumeMount below
        - name: OLLAMA_KEEP_ALIVE
          value: "30m"
        - name: OLLAMA_NUM_PARALLEL
          value: "1"
        # There is no GPU-memory-fraction setting in Ollama (that is vLLM's
        # --gpu-memory-utilization). VRAM use is controlled indirectly:
        # OLLAMA_NUM_PARALLEL x num_ctx scales the KV cache, and flash
        # attention + KV-cache quantization shrink it. Ollama silently
        # ignores unknown OLLAMA_* variables, so a bogus one does nothing.
        - name: OLLAMA_FLASH_ATTENTION
          value: "1"
        - name: OLLAMA_KV_CACHE_TYPE
          value: "q8_0"                # f16 (default) | q8_0 | q4_0
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "12Gi"
          requests:
            memory: "8Gi"
        volumeMounts:
        - name: models
          mountPath: /models           # must equal OLLAMA_MODELS — a mismatch
                                       # writes to the ephemeral container layer
                                       # and models vanish on pod restart
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: ollama-models
```

### Method 2: Native (on GPU VM)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify GPU support — `ollama --version` prints only the version; GPU
# detection shows up at server startup and when a model first loads
journalctl -u ollama --no-pager | grep -i "inference compute"  # lists CUDA devices
ollama pull llama2:7b
ollama ps    # PROCESSOR column: "100% GPU" = CUDA active, "100% CPU" = fallback

# Start server
ollama serve
```

## Model Management

### Pull Models
```bash
# Pull model (auto-downloads)
ollama pull llama2:7b
ollama pull codellama:13b
ollama pull mistral:7b
ollama pull neural-chat:7b
ollama pull mixtral:8x7b   # ~26GB — will not fit an 11GB-class GPU; needs a multi-GPU host
```

### Model Quantization Levels

Sizes below are the published registry sizes for the Llama 2 family
(`ollama.com/library/llama2/tags`). Note the real tag shape: quantization
variants combine parameter size and flavor (`7b-chat-q4_K_M`) — bare
suffixes like `:q4_K_M` alone are not pullable tags.

```text
Tag (pullable)              Size     Parameters   Fits 11GB GPU?
──────────────────────────────────────────────────────────────────
llama2:latest (=7b chat)    3.8GB    7B           yes (~6GB VRAM)
llama2:7b                   3.8GB    7B           yes (~6GB VRAM)
llama2:13b                  7.4GB    13B          tight (~10-11GB VRAM)
llama2:7b-chat-q4_K_M       4.1GB    7B           yes (~6GB VRAM)
llama2:7b-chat-q5_K_M       4.8GB    7B           yes (~7GB VRAM)
llama2:7b-chat-q8_0         7.2GB    7B           yes (~9GB VRAM)
codellama:34b               ~19GB    34B          no — 34B is CodeLlama-only,
                                                  and it exceeds 11GB VRAM
```

### Custom Model from GGUF
```bash
# Create Modelfile
cat > Modelfile << EOF
FROM ./model.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
TEMPLATE """
{{- range .Messages }}
{{- if eq .Role "user" }}
User: {{ .Content }}
{{- else if eq .Role "assistant" }}
Assistant: {{ .Content }}
{{- end }}
{{- end }}
Assistant:
"""
EOF

# Build and run
ollama create my-model -f Modelfile
ollama run my-model
```

## API Usage

### REST API Endpoints
```bash
# Generate completion
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Write a Python function to calculate fibonacci",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 512
  }
}'

# Chat completion
curl http://localhost:11434/api/chat -d '{
  "model": "llama2",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}'

# List models
curl http://localhost:11434/api/tags

# Model info
curl http://localhost:11434/api/show -d '{
  "model": "llama2"
}'
```

### Python Client
```python
import ollama

# Simple generation
response = ollama.generate(model='llama2', prompt='Write a haiku about AI')
print(response['response'])

# Chat with history
messages = [
    {'role': 'user', 'content': 'What is Kubernetes?'}
]
response = ollama.chat(model='llama2', messages=messages)
print(response['message']['content'])

# Streaming
for chunk in ollama.generate(model='llama2', prompt='Tell me a story', stream=True):
    print(chunk['response'], end='', flush=True)
```

## Configuration Options

### Server Configuration
```yaml
# Environment variables (verify against `ollama serve --help` / official docs)
OLLAMA_HOST: "0.0.0.0:11434"          # Listen address
OLLAMA_MODELS: "/models"               # Model storage path
OLLAMA_KEEP_ALIVE: "30m"               # Keep models in memory (default 5m; <=0 = forever)
OLLAMA_LOAD_TIMEOUT: "5m"              # Stall-detection window during a model load
OLLAMA_MAX_QUEUE: "512"                # Max queued requests (default 512)
OLLAMA_NUM_PARALLEL: "1"               # Concurrent requests per model (scales KV cache)
OLLAMA_MAX_LOADED_MODELS: "1"          # Models held in memory (default 3x GPU count)
OLLAMA_FLASH_ATTENTION: "1"            # Flash attention — lower VRAM, faster long contexts
OLLAMA_KV_CACHE_TYPE: "q8_0"           # KV cache: f16 (default) | q8_0 | q4_0
OLLAMA_CONTEXT_LENGTH: "2048"          # Server default context window (default 4096)
```

Ollama ignores unknown `OLLAMA_*` variables **silently** — there is no
`OLLAMA_GPU_MEMORY_FRACTION` (that is vLLM's `--gpu-memory-utilization`) and
no `OLLAMA_NUM_THREAD`; CPU thread count is a per-model option
(`num_thread` in the Modelfile or API `options`), not a server env var.

### Model Parameters

Sampling options go in the Modelfile (`PARAMETER ...`), per request via the
API `options` object, or on the CLI (`ollama run --temperature 0.7`). The
API examples above use `temperature 0.7`, `num_predict 512`, `seed 42`;
defaults for reference:

| Parameter      | Default | Notes                                 |
|----------------|---------|---------------------------------------|
| temperature    | 0.8     | Higher = more random                  |
| top_p          | 0.9     | Nucleus sampling cutoff               |
| top_k          | 40      | Sample from the top-k logits          |
| repeat_penalty | 1.1     | Above 1.0 penalizes repetition        |
| num_predict    | 128     | Max generated tokens; -1 = unlimited  |
| num_ctx        | 2048    | Context window; drives KV-cache VRAM  |
| seed           | 0       | 0 = randomize each call               |
| stop           | []      | Stop sequences                        |

`num_ctx` is commonly 2048 per model, while the server-level default is
`OLLAMA_CONTEXT_LENGTH` (4096).

## Performance Optimization

### GPU Utilization
```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Keep model in memory
OLLAMA_KEEP_ALIVE="-1" ollama serve  # Never unload

# Preload one model so the first request does not pay the load cost.
# keep_alive: -1 keeps it resident until explicitly unloaded.
curl -s http://localhost:11434/api/generate \
  -d '{"model": "llama2:7b", "keep_alive": -1}' > /dev/null

# An 11GB GPU holds ONE 7B model comfortably (~6GB VRAM). Preloading
# llama2 + codellama + mistral together (~12GB of weights) forces Ollama
# to unload and reload on every model switch — pick a single hot model.
```

### Batch Processing
```python
import concurrent.futures

def process_batch(prompts):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(ollama.generate, model='llama2', prompt=p)
            for p in prompts
        ]
        return [f.result()['response'] for f in futures]

prompts = ["Prompt 1", "Prompt 2", "Prompt 3", "Prompt 4"]
results = process_batch(prompts)

# With OLLAMA_NUM_PARALLEL=1 the server queues these four requests and runs
# them serially — raising OLLAMA_NUM_PARALLEL gives true concurrency at the
# cost of a proportionally larger KV cache.
```

### Caching
```python
# Use semantic caching to reduce redundant calls
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_generate(prompt, model="llama2"):
    return ollama.generate(model=model, prompt=prompt)

# Or use semantic similarity
from sentence_transformers import SentenceTransformer
import numpy as np

encoder = SentenceTransformer('all-MiniLM-L6-v2')

_semantic_cache = []  # list of (embedding, response) tuples

def semantic_cache(prompt, model="llama2:7b", threshold=0.95):
    emb = encoder.encode(prompt, normalize_embeddings=True)
    for cached_emb, cached_response in _semantic_cache:
        if float(np.dot(emb, cached_emb)) >= threshold:
            return cached_response          # near-duplicate hit: skip the LLM
    response = ollama.generate(model=model, prompt=prompt)["response"]
    _semantic_cache.append((emb, response))
    return response

# Trade-off: cosine >= 0.95 means *similar*, not *identical* — a hit returns
# the earlier answer verbatim. Tune the threshold per workload and treat
# this as an optimization, not a correctness layer.
```

## Service Mesh Integration

### Ingress Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ollama-ingress
  namespace: ai-services
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
spec:
  rules:
  - host: ollama.omega.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ollama
            port:
              number: 11434
```

### Service Discovery
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: ai-services
spec:
  selector:
    app: ollama
  ports:
  - name: http
    port: 11434
    targetPort: 11434
  type: ClusterIP
```

## Monitoring

### Metrics Endpoint

Ollama has **no native Prometheus endpoint**, so monitoring composes two
sources:

**1. GPU metrics — dcgm-exporter** (canonical pattern from
[1302: GPU Scheduler](../1300-kubernetes/1302-GPU-Scheduler.md)):

```bash
helm repo add gpu-helm-charts https://nvidia.github.io/dcgm-exporter/helm-charts
helm repo update
helm install dcgm-exporter gpu-helm-charts/dcgm-exporter \
  --namespace monitoring --create-namespace
```

**2. Model state — poll the API** (which models are loaded, and their VRAM share):

```bash
curl -s http://localhost:11434/api/ps | python3 -m json.tool
```

Request-level metrics (latency, token throughput) need a proxy in front of
Ollama — vLLM exposes Prometheus natively instead
([1402: vLLM and TGI](./1402-vLLM-and-TGI.md)).

### Health Check
```yaml
livenessProbe:
  httpGet:
    path: /api/tags
    port: 11434
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/tags
    port: 11434
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Security

### Authentication
```yaml
# Add authentication via nginx ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ollama-auth
  annotations:
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: ollama-auth  # create the htpasswd Secret first
    nginx.ingress.kubernetes.io/auth-realm: "Ollama Authentication"
spec:
  # ... rest of ingress
```

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ollama-netpol
  namespace: ai-services
spec:
  podSelector:
    matchLabels:
      app: ollama
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: ai-services  # auto-set on every namespace (v1.21+);
                                                    # a custom "name" label matches nothing,
                                                    # which blocks ALL ingress silently
    ports:
    - protocol: TCP
      port: 11434
```

---

## References

### Related PROJECT-OMEGA Documents

- [1402: vLLM and TGI High-Concurrency Inference](1402-vLLM-and-TGI.md)

---

## Next Steps

- Continue with: **[1402: vLLM and TGI](./1402-vLLM-and-TGI.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1302: GPU Scheduler](../1300-kubernetes/1302-GPU-Scheduler.md)
- [1402: vLLM and TGI](./1402-vLLM-and-TGI.md)
- [4101: GGUF Physics](../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)

