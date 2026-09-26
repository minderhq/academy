---
Document ID: CHEAT-SHEET-001
Title: "CHEAT SHEET: Docker Commands"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# CHEAT SHEET: Docker Commands

**Essential Docker commands for AI/ML development**

---

## 🐳 Container Management

### Run Containers
```bash
# Basic run
docker run nginx

# Interactive with terminal
docker run -it ubuntu bash

# Detached mode (background)
docker run -d nginx

# With port mapping
docker run -d -p 8080:80 nginx

# With volume mount
docker run -d -v $(pwd)/data:/app/data nginx

# With environment variables
docker run -e LOG_LEVEL=debug nginx

# With GPU support
docker run --gpus all nvidia/cuda:12.1.0-base

# Remove container on exit
docker run --rm nginx
```

### List & Inspect
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Inspect container details
docker inspect <container-id>

# View container logs
docker logs <container-id>

# Follow logs in real-time
docker logs -f <container-id>

# Execute command in container
docker exec -it <container-id> bash

# View container resource usage
docker stats <container-id>
```

### Stop & Remove
```bash
# Stop container
docker stop <container-id>

# Start stopped container
docker start <container-id>

# Restart container
docker restart <container-id>

# Remove container
docker rm <container-id>

# Force remove running container
docker rm -f <container-id>

# Remove all stopped containers
docker container prune
```

---

## 📦 Image Management

### Build Images
```bash
# Build from Dockerfile
docker build -t myapp:latest .

# Build with build args
docker build --build-arg VERSION=1.0 -t myapp:latest .

# Build without cache
docker build --no-cache -t myapp:latest .

# Build for specific platform
docker build --platform linux/amd64 -t myapp:latest .
```

### Pull & Push
```bash
# Pull image
docker pull nginx:latest

# Pull all tags for image
docker pull --all-tags nginx

# Push to registry
docker push myrepo/myapp:latest

# Tag image
docker tag myapp:latest myrepo/myapp:v1.0
```

### List & Remove
```bash
# List images
docker images

# List image layers
docker history myapp:latest

# Remove image
docker rmi myapp:latest

# Force remove image
docker rmi -f myapp:latest

# Remove dangling images
docker image prune

# Remove unused images
docker image prune -a
```

### Inspect Images
```bash
# Show image metadata
docker inspect myapp:latest

# Show image layers
docker history --no-trunc myapp:latest

# View image size
docker images myapp:latest
```

---

## 📊 Docker Compose

### Basic Commands
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api

# Restart services
docker-compose restart

# Rebuild and start
docker-compose up -d --build

# Scale services
docker-compose up -d --scale api=3
```

### Service Management
```bash
# Run one-off command
docker-compose run web python manage.py migrate

# Execute command in service
docker-compose exec web bash

# Show running processes
docker-compose ps

# View resource usage
docker-compose top
```

---

## 🔧 Troubleshooting

### Container Issues
```bash
# Container won't start? Check logs
docker logs <container-id>

# Container keeps restarting?
docker inspect <container-id> | jq '.[0].State.Restarting'

# Out of memory?
docker stats

# Port already in use?
netstat -tulpn | grep <port>

# Can't connect to container?
docker inspect <container-id> | jq '.[0].NetworkSettings.Ports'
```

### Image Issues
```bash
# Build fails? Check Dockerfile syntax
docker build --no-cache -t test .

# Wrong architecture?
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Disk space full?
docker system df

# Clean up unused data
docker system prune -a --volumes
```

---

## 🎯 AI/ML Specific Commands

### GPU Containers
```bash
# List available GPUs
nvidia-smi

# Run with specific GPU
docker run --gpus '"device=0"' nvidia/cuda:12.1.0-base

# Run with multiple GPUs
docker run --gpus 2 nvidia/cuda:12.1.0-base

# Run with all GPUs but limit memory
docker run --gpus all --shm-size=1g nvidia/cuda:12.1.0-base

# Check GPU inside container
docker exec <container> nvidia-smi
```

### ML Frameworks
```bash
# PyTorch with GPU
docker run --gpus all --shm-size=1g pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# TensorFlow with GPU
docker run --gpus all tensorflow/tensorflow:2.15.0-gpu

# Jupyter with GPU
docker run --gpus all -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes \
  jupyter/scipy-notebook:latest
```

### Volume Mounts for Data
```bash
# Mount local directory
docker run -v $(pwd)/data:/app/data myapp

# Mount with read-only
docker run -v $(pwd)/data:/app/data:ro myapp

# Named volume
docker volume create mydata
docker run -v mydata:/app/data myapp

# Bind mount with specific user
docker run -v $(pwd)/data:/app/data --user $(id -u):$(id -g) myapp
```

---

## 📝 Quick Reference

### Dockerfile Best Practices
```dockerfile
# Use specific version tags
FROM python:3.11-slim

# Combine RUN commands
RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Then copy source code
COPY . .

# Use non-root user
RUN useradd -m appuser
USER appuser

# Add health check
HEALTHCHECK CMD curl -f http://localhost:8000/ || exit 1
```

### Common Patterns

### Database + Application
```yaml
# version: is obsolete in the Compose Spec - omit it
services:
  db:
    image: postgres:15
    volumes:
      - db_data:/var/lib/postgresql/data
  app:
    build: .
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
volumes:
  db_data:
```

### Multi-Stage Build
```dockerfile
# Build stage
FROM golang:1.21 as builder
WORKDIR /app
COPY . .
RUN go build -o app

# Runtime stage
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/app .
CMD ["./app"]
```

---

## 🔍 Debug Commands

### View Container Processes
```bash
docker exec <container> ps aux
```

### Access Container Shell
```bash
docker exec -it <container> sh
# or
docker exec -it <container> bash
```

### Copy Files From/To Container
```bash
# Copy from container to host
docker cp <container>:/app/file.txt ./file.txt

# Copy from host to container
docker cp ./file.txt <container>:/app/file.txt
```

### View Container Environment
```bash
docker exec <container> env
```

---

## 🚀 Performance Tips

### Limit Resources
```bash
# Limit memory
docker run -m 512m myapp

# Limit CPUs
docker run --cpus="1.5" myapp

# Set CPU shares (weight)
docker run --cpu-shares=512 myapp
```

### Optimize Builds
```bash
# Use BuildKit
export DOCKER_BUILDKIT=1

# Parallel builds
docker build --parallel .

# Use cache mount
docker build --mount=type=cache,target=/root/.cache pip install -r requirements.txt
```

---

## 📚 AI Engineering Curriculum Specific

### Run AI Engineering Curriculum Stack
```bash
# From the configs/ directory
cp .env.example .env

# Start inference (vLLM) + vector database (Qdrant)
docker compose up -d

# View logs
docker compose logs -f
```

### Check GPU Utilization
```bash
# Host GPU stats
nvidia-smi

# Inside the inference container
docker exec omega-vllm nvidia-smi
```

---

## ⌨️ Keyboard Shortcuts (in container)

```bash
# Exit container
exit
# or Ctrl+D

# Detach from container (without stopping)
Ctrl+P, Ctrl+Q

# Attach to running container
docker attach <container>

# Stop container
Ctrl+C
```

---

## 🆘 Emergency Commands

### Force Kill Container
```bash
docker kill <container-id>
```

### Remove All Containers
```bash
docker rm -f $(docker ps -aq)
```

### Factory Reset Docker
```bash
# ⚠️ WARNING: Deletes all data!
docker system prune -a --volumes -f
```

---

## 🔗 Quick Links

- **[Tutorial 002: Docker Essentials](../tutorials/TUTORIAL-002-Docker-Essentials.md)** - Full tutorial
- **[Tutorial 003: RAG Basics](../tutorials/TUTORIAL-003-RAG-Basics.md)** - RAG with Docker
- **[1201: Proxmox Hypervisor SOP](../../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)** - Proxmox basics
- **[LAB 001: Docker & LLM](../labs/LAB-001-Docker-LLM.md)** - Hands-on exercises with LLM containers
- **[LAB 002: RAG Implementation](../labs/LAB-002-RAG-Implementation.md)** - Build RAG stack with Docker Compose

---

## Next Steps

- **[CHEAT SHEET: Python for AI](CHEAT-SHEET-002-Python-AI.md)**
