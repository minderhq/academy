---
Document ID: SOLUTION-LAB-001
Title: "SOLUTION-LAB-001: Docker & LLM Fundamentals"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Tags: ['solution', 'docker', 'ollama']
---

# SOLUTION-LAB-001: Docker & LLM Fundamentals

## Overview
Complete solution for LAB-001 with detailed explanations and troubleshooting.

---

## Exercise 1: Run Ollama in Docker (15 minutes)

### Task
Deploy Ollama with GPU support in a Docker container.

### Solution

```bash
# Pull the Ollama image
docker pull ollama/ollama:latest

# Run Ollama container with GPU support
docker run -d \
  --name ollama \
  --gpus all \
  -p 11434:11434 \
  -v ~/lab-001-docker-llm/data/models:/root/.ollama \
  ollama/ollama:latest

# Verify it's running
docker ps | grep ollama

# Pull a model inside the container
docker exec ollama ollama pull mistral

# Test the API
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Hello from Docker!",
  "stream": false
}'
```

### Expected Output

```json
{
  "model": "mistral",
  "created_at": "2026-02-04T10:30:00.000Z",
  "response": "Hello! How can I help you today?",
  "done": true
}
```

### Common Mistakes

#### Mistake 1: Forgetting --gpus all
**Problem:** "could not select device driver" error

**Fix:**
```bash
# Wrong - no GPU support
docker run -d --name ollama ollama/ollama

# Correct - with GPU support
docker run -d --gpus all --name ollama ollama/ollama
```

#### Mistake 2: Not mounting volume
**Problem:** Models are re-downloaded on container restart

**Fix:**
```bash
# Always mount the models directory
-v ~/lab-001-docker-llm/data/models:/root/.ollama
```

#### Mistake 3: Port already in use
**Problem:** "port is already allocated"

**Fix:**
```bash
# Check what's using the port
lsof -i :11434

# Either stop the conflicting container
docker rm -f ollama  # if old container exists

# Or use a different port
-p 11435:11434
```

---

## Exercise 2: Build LLM API Server (30 minutes)

### Task
Create a FastAPI wrapper for Ollama.

### Complete Solution

```python
# ~/lab-001-docker-llm/services/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM API Server",
    description="FastAPI wrapper for Ollama",
    version="1.0.0"
)

OLLAMA_URL = "http://ollama:11434"


# Request/Response Models
class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    model: str = Field(default="mistral", description="Model name")
    messages: list[Message] = Field(..., min_items=1)
    stream: bool = Field(default=False)
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=512, ge=1, le=4096)


class ChatResponse(BaseModel):
    model: str
    message: Message
    done: bool
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LLM API Server",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Chat with LLM",
            "GET /health": "Health check",
            "GET /models": "List available models"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        return {"status": "healthy", "ollama": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/models")
async def list_models():
    """List available models."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        return {"models": data.get("models", [])}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with LLM.

    Supports:
    - Multiple messages (conversation history)
    - Streaming responses
    - Temperature control
    - Token limits
    """
    try:
        # Build prompt from messages
        prompt_parts = []
        for msg in request.messages:
            prompt_parts.append(f"{msg.role}: {msg.content}")

        prompt = "\n".join(prompt_parts) + "\nassistant:"

        # Call Ollama API
        ollama_request = {
            "model": request.model,
            "prompt": prompt,
            "stream": request.stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }

        logger.info(f"Sending request to Ollama: {request.model}")

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=ollama_request,
            timeout=120
        )
        response.raise_for_status()

        data = response.json()

        # Parse response
        assistant_message = Message(
            role="assistant",
            content=data.get("response", "")
        )

        return ChatResponse(
            model=request.model,
            message=assistant_message,
            done=data.get("done", False),
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        )

    except requests.exceptions.Timeout:
        logger.error("Request to Ollama timed out")
        raise HTTPException(status_code=504, detail="Request timeout")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        raise HTTPException(status_code=503, detail="Failed to connect to Ollama")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Dependencies (project manifest)

```bash
# ~/lab-001-docker-llm/services/app - create the manifest
uv init --bare --python 3.13 .
uv add fastapi==0.141.1 "uvicorn[standard]==0.52.1" pydantic==2.13.5 requests==2.34.2
```

### Dockerfile for API

```dockerfile
# ~/lab-001-docker-llm/services/app/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Official uv-in-Docker pattern: copy the uv binary from the uv image
# (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependency layer: only manifest/lockfile changes rebuild this.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy application
COPY main.py .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Exercise 3: Docker Compose Orchestration (30 minutes)

### Task
Connect all services with Docker Compose.

### Complete Solution

```yaml
# ~/lab-001-docker-llm/docker-compose.yml

services:
  # Ollama LLM service
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    runtime: nvidia  # For GPU support
    ports:
      - "11434:11434"
    volumes:
      - ./data/models:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped
    networks:
      - llm-network

  # FastAPI application
  api:
    build: ./services/app
    container_name: llm-api
    ports:
      - "8000:8000"
    volumes:
      - ./data/chat:/app/data
    environment:
      - OLLAMA_URL=http://ollama:11434
      - LOG_LEVEL=info
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - llm-network

  # Nginx reverse proxy (optional)
  nginx:
    image: nginx:latest
    container_name: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - llm-network

networks:
  llm-network:
    driver: bridge

volumes:
  models:
  chat:
```

### Nginx Configuration

```nginx
# ~/lab-001-docker-llm/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # CORS headers
            add_header Access-Control-Allow-Origin * always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;

            if ($request_method = OPTIONS) {
                return 204;
            }
        }

        location /health {
            proxy_pass http://api/health;
            access_log off;
        }
    }
}
```

---

## Exercise 4: Chat History Persistence (30 minutes)

### Task
Implement persistent chat history using file-based storage.

### Complete Solution

```python
# ~/lab-001-docker-llm/services/app/storage.py
import json
import os
from datetime import datetime, timezone
from pathlib import Path

STORAGE_DIR = Path("/app/data/chats")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class ChatHistory:
    """Store and retrieve chat history."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.file_path = STORAGE_DIR / f"{session_id}.json"
        self.history = self._load_history()

    def _load_history(self) -> list[dict]:
        """Load history from file."""
        if self.file_path.exists():
            with open(self.file_path, "r") as f:
                return json.load(f)
        return []

    def _save_history(self):
        """Save history to file."""
        with open(self.file_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def add_message(self, role: str, content: str):
        """Add a message to history."""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._save_history()

    def get_history(self, limit: int = 10) -> list[dict]:
        """Get recent messages."""
        return self.history[-limit:]

    def clear_history(self):
        """Clear all history."""
        self.history = []
        self._save_history()

    def get_context(self) -> str:
        """Get formatted context for LLM."""
        context = []
        for msg in self.get_history():
            context.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(context)
```

### Updated API with History

```python
# Add to main.py
from storage import ChatHistory

@app.post("/chat/{session_id}")
async def chat_with_history(session_id: str, request: ChatRequest):
    """Chat with persistent history."""
    history = ChatHistory(session_id)

    # Add user message to history
    if request.messages:
        user_msg = request.messages[0].content
        history.add_message("user", user_msg)

    # Get context from history
    context = history.get_context()

    # Build prompt
    prompt = f"{context}\nassistant:"

    # Call Ollama
    ollama_request = {
        "model": request.model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": request.temperature,
            "num_predict": request.max_tokens
        }
    }

    response = requests.post(f"{OLLAMA_URL}/api/generate", json=ollama_request)
    response.raise_for_status()
    data = response.json()

    # Add assistant response to history
    assistant_content = data.get("response", "")
    history.add_message("assistant", assistant_content)

    return {
        "response": assistant_content,
        "session_id": session_id,
        "history_length": len(history.history)
    }


@app.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 10):
    """Get chat history."""
    history = ChatHistory(session_id)
    return {
        "session_id": session_id,
        "messages": history.get_history(limit)
    }


@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear chat history."""
    history = ChatHistory(session_id)
    history.clear_history()
    return {"message": "History cleared"}
```

---

## Complete Working Solution

### Project Structure

```text
~/lab-001-docker-llm/
├── docker-compose.yml
├── data/
│   ├── models/
│   └── chat/
├── services/
│   └── app/
│       ├── Dockerfile
│       ├── main.py
│       ├── pyproject.toml
│       ├── uv.lock
│       └── storage.py
└── nginx/
    └── nginx.conf
```

### Running the Complete Solution

```bash
# 1. Create directory structure
cd ~/lab-001-docker-llm
mkdir -p services/app data/models data/chat nginx

# 2. Create all files (copy code from above)

# 3. Start all services
docker-compose up -d

# 4. Pull model
docker exec ollama ollama pull mistral

# 5. Test the API
curl http://localhost:8000/health

# 6. Send a chat request
curl -X POST http://localhost:8000/chat/session123 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# 7. View logs
docker-compose logs -f api

# 8. Stop services
docker-compose down
```

---

## Extension Challenges

### Challenge 1: Streaming Responses
Implement SSE streaming for real-time token generation.

### Challenge 2: Multi-User Support
Add rate limiting per user and concurrent session handling.

### Challenge 3: Model Switching
Support switching between multiple models without restarting.

---

## Troubleshooting

### Issue: Ollama connection refused

**Symptoms:** API returns "Failed to connect to Ollama"

**Causes:**
1. Ollama container not running
2. Wrong URL in configuration
3. Network not set up correctly

**Solutions:**
```bash
# Check Ollama is running
docker ps | grep ollama

# Check network
docker network inspect lab-001-llm_llm-network

# Test connection
docker exec api ping -c 3 ollama
```

### Issue: Slow responses

**Symptoms:** Requests take >10 seconds

**Causes:**
1. CPU-only mode
2. Large model size
3. No batching

**Solutions:**
```bash
# Check GPU usage
nvidia-smi

# Use smaller model
docker exec ollama ollama pull phi3

# Increase batch size in code
```

---

## Learning Objectives Check

After completing this lab, you should:
- [x] Run LLMs in Docker containers
- [x] Build a custom LLM API server
- [x] Connect multiple services with Docker Compose
- [x] Persist chat history across sessions

---

**Related Topics:**
- [TUTORIAL-002: Docker Essentials](../../tutorials/TUTORIAL-002-Docker-Essentials.md)
- [TUTORIAL-003: RAG Basics](../../tutorials/TUTORIAL-003-RAG-Basics.md)
- [LAB-002: RAG Implementation](../LAB-002-RAG-Implementation.md)

---

**Difficulty:** ⭐ Beginner
**Time to Complete:** 2 hours
