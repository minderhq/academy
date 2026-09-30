---
Document ID: TUTORIAL-002
Title: "TUTORIAL-002: Docker Essentials for AI"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Tags: ['tutorial', 'docker', 'hands-on']
---

# TUTORIAL-002: Docker Essentials for AI

**Difficulty:** ⭐ Beginner
**Time:** 45 minutes
**Prerequisites:** Basic Linux command line

---

## Learning Objectives

By the end of this tutorial, you will:
- ✅ Understand what Docker is
- ✅ Build your first Docker image
- ✅ Run containers with GPUs
- ✅ Use Docker Compose for multi-container apps

---

## What is Docker?

**Docker** = Container platform

Think of containers like **lightweight virtual machines**:
- Share the host OS kernel (more efficient)
- Package app + dependencies together
- Run anywhere (dev = prod)

### Containers vs VMs:

```text
┌─────────────────────────────────────────────────────────────┐
│ Virtual Machine                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │   App    │  │   App    │  │   App    │                 │
│  ├──────────┤  ├──────────┤  ├──────────┤                 │
│  │   Guest  │  │   Guest  │  │   Guest  │                 │
│  │    OS    │  │    OS    │  │    OS    │                 │
│  ├──────────┤  ├──────────┤  ├──────────┤                 │
│  │         Hypervisor        │                           │
│  ├─────────────────────────────────────────────────────────┤
│  │                    Host OS                             │
│  └─────────────────────────────────────────────────────────┘
│  Heavy: Each VM needs full OS                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Docker Containers                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │   App    │  │   App    │  │   App    │                 │
│  │   +      │  │   +      │  │   +      │                 │
│  │  Deps    │  │  Deps    │  │  Deps    │                 │
│  ├──────────┤  ├──────────┤  ├──────────┤                 │
│  │                    Docker Engine                         │
│  ├─────────────────────────────────────────────────────────┤
│  │                    Host OS                             │
│  └─────────────────────────────────────────────────────────┘
│  Light: Share kernel, only package app differences          │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Install Docker

### Ubuntu/Debian:
```bash
# Update packages
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
```

### Verify:
```bash
docker --version
docker run hello-world
```

---

## Step 2: Your First Container

### Run Python in a Container:
```bash
docker run -it python:3.13 bash
```

**What happened?**
1. Downloaded `python:3.13` image
2. Started container with bash shell
3. `-it` = interactive + TTY

### Inside the container:
```bash
# Check Python version
python --version

# Install uv (the curriculum's package manager standard)
curl -LsSf https://astral.sh/uv/install.sh | sh
source /root/.local/bin/env

# Install a package
uv pip install --system numpy

# Run Python
python -c "import numpy; print(numpy.__version__)"

# Exit
exit
```

**Note:** Changes inside containers are lost when they exit!

---

## Step 3: Build Your First Image

### Create a simple Python app:

```bash
# Create project directory
mkdir docker-demo
cd docker-demo

# Create app.py
cat > app.py << 'EOF'
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Prompt(BaseModel):
    text: str

@app.post("/generate")
def generate(prompt: Prompt):
    return {"response": f"You said: {prompt.text}"}

@app.get("/")
def root():
    return {"message": "Hello AI!"}
EOF

# Create the project manifest - pyproject.toml + uv.lock ship with
# the demo and pin the dependency graph.
uv init --bare --python 3.13 .
uv add fastapi==0.141.1 uvicorn==0.52.1
```

### Create Dockerfile:

```bash
cat > Dockerfile << 'EOF'
FROM python:3.13-slim

WORKDIR /app

# Official uv-in-Docker pattern: copy the uv binary from the uv image
# (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependency layer: only manifest/lockfile changes rebuild this.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
# uv sync creates the project venv at /app/.venv - put it on PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

### Build the image:

```bash
docker build -t my-ai-app:latest .
```

### Run the container:

```bash
docker run -d -p 8000:8000 --name my-app my-ai-app:latest
```

### Test it:

```bash
curl http://localhost:8000/
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello Docker!"}'
```

---

## Step 4: Volumes (Persisting Data)

By default, container data is lost when the container stops. Volumes fix this!

### Bind Mount:
```bash
# Map local directory to container
docker run -d \
  -v $(pwd)/data:/app/data \
  my-ai-app:latest
```

### Named Volume:
```bash
# Create a named volume
docker volume create app-data

# Use it
docker run -d \
  -v app-data:/app/data \
  my-ai-app:latest
```

### Anonymous Volume:
```bash
docker run -d \
  -v /app/data \
  my-ai-app:latest
```

---

## Step 5: Docker Compose

**Docker Compose** = Multi-container orchestrator

### Create docker-compose.yml:

```bash
cat > docker-compose.yml << 'EOF'
# Note: older examples start with `version: "3.8"` - the key is
# obsolete in the Compose Spec; the modern CLI warns on it, so omit it.
services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - LOG_LEVEL=info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
EOF
```

### Run multiple services:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## Step 6: GPU Containers (AI/ML)

For AI/ML workloads, you need GPU access!

### Check GPU:
```bash
nvidia-smi
```

### Install NVIDIA Container Toolkit:
```bash
# Add NVIDIA repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
  sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker
```

### Run GPU Container:
```bash
docker run --gpus all -it --rm \
  nvidia/cuda:12.1.0-base-ubuntu22.04 \
  nvidia-smi
```

### Python with GPU:
```bash
docker run --gpus all -it --rm \
  -v $(pwd):/workspace \
  python:3.13-cuda \
  python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

---

## Step 7: Dockerfile Best Practices

### ❌ Bad Dockerfile:
```dockerfile
FROM python:3.13

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
```

**Problems:**
- Installs dependencies every time (if code changes)
- No layer caching optimization
- Uses plain `pip` instead of the uv standard (see the good Dockerfile below)

### ✅ Good Dockerfile:
```dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy manifest + lockfile first (better caching): only manifest/
# lockfile changes rebuild the dependency layer.
COPY pyproject.toml uv.lock ./

# Official uv-in-Docker pattern: copy the uv binary from the uv image
# (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy application code
COPY . .

# uv sync creates the project venv at /app/.venv - put it on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Improvements:**
- ✅ Separate dependency layer (manifest + lockfile first)
- ✅ Cleanup apt cache
- ✅ Run as non-root user (security)
- ✅ Add health check
- ✅ Smaller base image

---

## Step 8: Common Docker Commands

### Images:
```bash
# List images
docker images

# Remove image
docker rmi ${IMAGE_ID}

# Prune unused images
docker image prune
```

### Containers:
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop container
docker stop ${CONTAINER_ID}

# Remove container
docker rm ${CONTAINER_ID}

# View logs
docker logs ${CONTAINER_ID}

# Execute command in running container
docker exec -it ${CONTAINER_ID} bash
```

### System:
```bash
# Disk usage
docker system df

# Prune everything (careful!)
docker system prune -a
```

---

## Step 9: Debugging Containers

### Container won't start?
```bash
# Check logs
docker logs ${CONTAINER_ID}

# Run in foreground to see output
docker run ${IMAGE}

# Check if port is already in use
netstat -tulpn | grep ${PORT}
```

### Out of memory?
```bash
# Check container stats
docker stats

# Limit memory
docker run -m 512m ${IMAGE}
```

### Need to inspect?
```bash
# View container details
docker inspect ${CONTAINER_ID}

# View image layers
docker history ${IMAGE}
```

---

## Step 10: PROJECT-OMEGA Context

How Docker fits into PROJECT-OMEGA:

```text
┌─────────────────────────────────────────────────────────────┐
│                     PROJECT-OMEGA Stack                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  External NAS:                                              │
│  ├─ Qdrant (Vector DB)    ← Docker container              │
│  ├─ Neo4j (Graph DB)      ← Docker container              │
│  ├─ Prometheus            ← Docker container              │
│  ├─ Grafana               ← Docker container              │
│  └─ Redis                 ← Docker container              │
│                                                             │
│  GPU VM:                                                    │
│  ├─ vLLM                  ← Docker container + GPU          │
│  ├─ TGI                   ← Docker container + GPU          │
│  ├─ ReAct Agent           ← Docker container + GPU          │
│  └─ GraphRAG              ← Docker container + GPU          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 Knowledge Check

1. **What is the main benefit of containers over VMs?**
   - More efficient resource usage (shared kernel)

2. **How do you persist container data?**
   - Use volumes (bind mounts or named volumes)

3. **What's the difference between `docker run` and `docker-compose up`?**
   - `docker run` = single container
   - `docker-compose up` = multi-container orchestrator

4. **Why do we copy pyproject.toml + uv.lock before code in Dockerfile?**
   - Better layer caching (dependencies only reinstall when changed)

---

## 📚 What's Next?

1. **[1301: K3s Master-Worker Architecture](../../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md)** - Orchestrate containers at cluster scale
2. **[1405: TGI Deployment Guide](../../phases/phase1-infra/1400-llmops/guides/1405-TGI-Deployment-Guide.md)** - Serve LLMs in GPU containers
3. **[0000-LEARNING-PATH.md](../../00-META/0000-LEARNING-PATH.md)** - Full curriculum

---

## 🔗 Quick Reference

```bash
# Essential commands
docker build -t ${NAME} .           # Build image
docker run -d -p 80:80 ${NAME}      # Run container
docker ps                           # List containers
docker logs ${ID}                     # View logs
docker exec -it ${ID} bash           # Enter container
docker-compose up -d                # Start services
docker-compose down                 # Stop services
```

---

## Next Steps

- TUTORIAL-003: [RAG Basics](./TUTORIAL-003-RAG-Basics.md) - the next tutorial in the series
