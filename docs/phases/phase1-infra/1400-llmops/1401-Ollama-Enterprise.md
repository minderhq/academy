---
Document ID: 1401
Title: Ollama Enterprise Deployment
Phase: 1
Module: 1400
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'llmops', 'ollama', 'vllm', 'tgi']
---

# 1401: Ollama Enterprise Deployment

## Abstract
Ollama enables running large language models locally with a simple API. In PROJECT-OMEGA, Ollama serves as the model inference backend across the 2.5G star network.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Client Layer                          │
│  Python Apps, REST APIs, CLI Tools                      │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP/11434
┌─────────────────────────────────────────────────────────┐
│                   Ollama Server                         │
│  [K3s Pod → GPU Node → RTX 2080 Ti]                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Model Storage                         │
│  [Synology NFS: /volume1/ollama/models]                │
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
        accelerator: nvidia-2080ti
      containers:
      - name: ollama
        image: ollama/ollama:0.5.7  # ⚠️ PIN SPECIFIC VERSION in production! Never use :latest
        # Check https://github.com/ollama/ollama/releases for latest stable version
        # Using :latest can break production when new versions are released
        ports:
        - containerPort: 11434
          name: http
        env:
        - name: OLLAMA_HOST
          value: "0.0.0.0"
        - name: OLLAMA_MODELS
          value: "/models"
        - name: OLLAMA_GPU_MEMORY_FRACTION
          value: "0.9"
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "12Gi"
          requests:
            memory: "8Gi"
        volumeMounts:
        - name: models
          mountPath: /root/.ollama/models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: ollama-models
```

### Method 2: Native (on GPU VM)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify GPU support
ollama --version
# Should show CUDA support

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
ollama pull mixtral:8x7b
```

### Model Quantization Levels
```
Tag           Size     Context   Parameters    Memory
──────────────────────────────────────────────────────
:latest       ~4GB     2048      7B            ~6GB VRAM
:7b           ~4GB     2048      7B            ~6GB VRAM
:13b          ~8GB     2048      13B           ~10GB VRAM
:34b          ~20GB    2048      34B           >11GB (OOM)
:q4_0         ~4GB     2048      7B            ~5GB VRAM
:q4_K_M       ~4.5GB   2048      7B            ~6GB VRAM
:q5_K_M       ~5.5GB   2048      7B            ~7GB VRAM
:q8_0         ~8.5GB   2048      7B            ~9GB VRAM
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
  "name": "llama2"
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
# Environment variables
OLLAMA_HOST: "0.0.0.0:11434"          # Listen address
OLLAMA_MODELS: "/models"               # Model storage path
OLLAMA_KEEP_ALIVE: "30m"               # Keep models in memory
OLLAMA_GPU_MEMORY_FRACTION: "0.9"      # GPU memory to use
OLLAMA_LOAD_TIMEOUT: "5m"              # Model load timeout
OLLAMA_NUM_THREAD: "8"                 # CPU threads (for CPU inference)
OLLAMA_MAX_QUEUE: "512"                # Max queued requests
```

### Model Parameters
```json
{
  "temperature": 0.7,        // 0.0-1.0 (creativity)
  "top_p": 0.9,             // 0.0-1.0 (nucleus sampling)
  "top_k": 40,              // 1+ (top-k sampling)
  "repeat_penalty": 1.1,    // 1.0+ (reduce repetition)
  "num_predict": 512,       // Max tokens to generate
  "num_ctx": 2048,          // Context window size
  "seed": 42,               // Random seed
  "stop": ["\n", "User:"]   // Stop sequences
}
```

## Performance Optimization

### GPU Utilization
```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Keep model in memory
OLLAMA_KEEP_ALIVE="-1" ollama serve  # Never unload

# Preload models on startup
for model in llama2 codellama mistral; do
  ollama run $model "" &
done
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

def semantic_cache(prompt, threshold=0.95):
    prompt_embedding = encoder.encode(prompt)
    # Check against cached prompts
    # Return cached response if similarity > threshold
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
```bash
# Ollama doesn't have built-in metrics
# Use sidecar for metrics collection

apiVersion: v1
kind: Pod
metadata:
  name: ollama-metrics
spec:
  containers:
  - name: ollama-exporter
    image: your-ollama-exporter:1.0.0  # ⚠️ PIN SPECIFIC VERSION in production!
    env:
    - name: OLLAMA_URL
      value: "http://ollama:11434"
    ports:
    - containerPort: 9101
```

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
    nginx.ingress.kubernetes.io/auth-secret: ollama-auth
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
          name: ai-services
    ports:
    - protocol: TCP
      port: 11434
```

---

## Next Steps

- Continue with: **[1402: vLLM and TGI](./1402-vLLM-and-TGI.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [1302: GPU Scheduler](../1300-kubernetes/1302-GPU-Scheduler.md)
- [1402: vLLM and TGI](./1402-vLLM-and-TGI.md)
- [4101: GGUF Physics](../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)

**Experiment Template:** `experiments/EXP_1401_OLLAMA.md`
