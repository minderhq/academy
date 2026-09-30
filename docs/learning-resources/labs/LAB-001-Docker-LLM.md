---
Document ID: LAB-001
Title: "LAB-001: Docker & LLM Fundamentals"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Tags: ['lab', 'docker', 'ollama', 'hands-on']
---

# LAB-001: Docker & LLM Fundamentals

**Prerequisites:**
- **[TUTORIAL-001: Hello LLM](../tutorials/TUTORIAL-001-Hello-LLM.md)** - LLM basics
- **[TUTORIAL-002: Docker Essentials](../tutorials/TUTORIAL-002-Docker-Essentials.md)** - Docker fundamentals
- **[TUTORIAL-000: Python for AI](../tutorials/TUTORIAL-000-Python-for-AI.md)** (recommended) - For custom API code

**Time:** 2 hours
**Difficulty:** ⭐ Beginner

> **⚠️ Educational Code Warning:**
>
> This lab contains **educational code examples** for learning purposes. These examples:
> - Are simplified for clarity and learning
> - **LACK production-grade security** (no authentication, rate limiting, input validation)
> - **LACK production-grade reliability** (no error handling, logging, monitoring)
> - **LACK production-grade scalability** (single-instance, no load balancing)
>
> **For production deployment**, see:
> - **[TUTORIAL-012: Production LLMOps](../tutorials/TUTORIAL-012-Production-LLMOps.md)**
> - **[LAB-009: Production Deployment](./LAB-009-Production-Deployment.md)**
> - **[1401: Ollama Enterprise](../../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)**
>
> Use these examples to **learn concepts**, then apply production patterns from later modules.

---

## Lab Objectives

After completing this lab, you will be able to:
- ✅ Run LLMs in Docker containers
- ✅ Build a custom LLM API server
- ✅ Connect multiple services with Docker Compose
- ✅ Persist LLM chat history

---

## Setup Instructions

```bash
# Create lab directory
mkdir ~/lab-001-docker-llm
cd ~/lab-001-docker-llm

# Create directory structure
mkdir -p services/app
mkdir -p data/models
mkdir -p data/chat
```

---

## Exercise 1: Run Ollama in Docker (15 minutes)

### Task: Deploy Ollama with GPU support

```bash
# Run Ollama container with GPU
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

### ✅ Checkpoint: Exercise 1
**Verify:** You should see a JSON response from Mistral

**Expected Output:**
```text
{"model": "mistral", "response": "Hello from Docker!", ...}
```

**Troubleshooting:**
- `container not found`: Make sure Ollama is running
- `no GPUs`: Remove `--gpus all` flag (CPU-only mode)

---

## Exercise 2: Build LLM API Server (30 minutes)

### Task: Create a FastAPI wrapper for Ollama

```python
# ~/lab-001-docker-llm/services/app/main.py
# NOTE: For Windows users, use: C:\lab-001-docker-llm\services\app\main.py
# For Linux/Mac users, use: ~/lab-001-docker-llm/services/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json

app = FastAPI(title="LLM API")

OLLAMA_URL = "http://ollama:11434"

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "mistral"
    messages: list[Message]
    stream: bool = False
    temperature: float | None = 0.7

class ChatResponse(BaseModel):
    message: Message
    model: str
    done: bool

@app.get("/")
def root():
    return {
        "service": "LLM API",
        "models": ["mistral", "phi3", "llama2"],
        "endpoints": {
            "/v1/chat/completions": "OpenAI-compatible chat",
            "/models": "List available models",
            "/health": "Health check"
        }
    }

@app.get("/health")
def health():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return {"status": "healthy", "ollama": response.status_code == 200}
    except:
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/v1/models")
def list_models():
    """List available models (OpenAI-compatible format)"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        models = response.json()

        return {
            "object": "list",
            "data": [
                {
                    "id": model["name"],
                    "type": "model",
                    "owned_by": "ollama"
                }
                for model in models.get("models", [])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions", response_model=ChatResponse)
def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat endpoint"""

    # Convert OpenAI format to Ollama format
    ollama_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]

    payload = {
        "model": request.model,
        "messages": ollama_messages,
        "stream": request.stream,
        "options": {
            "temperature": request.temperature
        }
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()

        return ChatResponse(
            message=Message(
                role="assistant",
                content=result.get("message", {}).get("content", "")
            ),
            model=request.model,
            done=result.get("done", False)
        )

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Create the project manifest (pyproject.toml + uv.lock):
```bash
cd ~/lab-001-docker-llm/services/app

# uv-native dependency management: pyproject.toml is the source of truth,
# uv.lock pins the resolved graph. uv init --bare creates only the manifest;
# uv add records each pin and writes the lockfile in one step.
uv init --bare --python 3.13 .
uv add fastapi==0.141.1 "uvicorn[standard]==0.52.1" requests==2.34.2 pydantic==2.13.5
```

### Create Dockerfile:
```bash
cat > ~/lab-001-docker-llm/services/app/Dockerfile << 'EOF'
FROM python:3.13-slim

WORKDIR /app

# Official uv-in-Docker pattern: copy the uv binary from the uv image
# (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependency layer: only manifest/lockfile changes rebuild this.
# uv sync --locked installs exactly what uv.lock pins; --no-install-project
# skips the project itself (dependencies change rarely - a big time-saver).
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Source layer: app-code changes rebuild only this.
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# uv sync creates the project venv at /app/.venv - put it on PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

### Build and run:
```bash
# Build the image
cd ~/lab-001-docker-llm
docker build -t llm-api:latest ./services/app

# Run the container
docker run -d \
  --name llm-api \
  -p 8000:8000 \
  --link ollama:ollama \
  llm-api:latest

# Test the API
curl http://localhost:8000/health
curl http://localhost:8000/v1/models
```

### ✅ Checkpoint: Exercise 2
**Verify:** API health check returns `{"status": "healthy", "ollama": true}`

---

## Exercise 3: Chat Completion Test (15 minutes)

```bash
# Test chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [
      {"role": "user", "content": "What is Docker?"}
    ],
    "temperature": 0.5
  }'
```

### Challenge: Multi-turn conversation
```bash
# Create a script for multi-turn chat
cat > ~/lab-001-docker-llm/test_chat.py << 'EOF'
import requests

API_URL = "http://localhost:8000/v1/chat/completions"

messages = []

while True:
    user_input = input("You: ")
    if user_input.lower() in ["bye", "exit", "quit"]:
        break

    messages.append({"role": "user", "content": user_input})

    response = requests.post(API_URL, json={
        "model": "mistral",
        "messages": messages
    })

    result = response.json()
    assistant_message = result["message"]["content"]
    messages.append({"role": "assistant", "content": assistant_message})

    print(f"AI: {assistant_message}")

print("\nConversation ended!")
EOF

python ~/lab-001-docker-llm/test_chat.py
```

### ✅ Checkpoint: Exercise 3
**Verify:** You can have a multi-turn conversation with the AI

---

## Exercise 4: Docker Compose Orchestration (30 minutes)

### Task: Create multi-container setup with Docker Compose

```bash
cat > ~/lab-001-docker-llm/docker-compose.yml << 'EOF'

services:
  # Ollama LLM server
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./data/models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - llm-network

  # LLM API server
  api:
    build: ./services/app
    container_name: llm-api
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - llm-network

  # Simple web UI
  web:
    image: nginx:alpine
    container_name: llm-web
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - llm-network

networks:
  llm-network:
    driver: bridge
EOF
```

### Create Nginx config:
```bash
cat > ~/lab-001-docker-llm/nginx.conf << 'EOF'
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
        }
    }
}
EOF
```

### Deploy everything:
```bash
cd ~/lab-001-docker-llm

# Build and start all services
docker-compose build
docker-compose up -d

# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f api
```

### ✅ Checkpoint: Exercise 4
**Verify:** All 3 containers are running and healthy

```bash
# Expected output:
# NAME      COMMAND              SERVICE   STATUS
# ollama    "/entrypoint.sh..."    ollama    running
# llm-api   "uvicorn main:app..."  api       running
# llm-web   "/docker-entrypoint..." web     running
```

---

## Exercise 5: Persistent Chat History (30 minutes)

### Task: Add Redis for storing conversation history

```bash
cat > ~/lab-001-docker-llm/docker-compose.yml << 'EOF'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./data/models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - llm-network

  api:
    build: ./services/app
    container_name: llm-api
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379
    depends_on:
      - ollama
      - redis
    restart: unless-stopped
    networks:
      - llm-network

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/chat:/data
    restart: unless-stopped
    networks:
      - llm-network

networks:
  llm-network:
    driver: bridge
EOF
```

### Update API with Redis:
```python
# ~/lab-001-docker-llm/services/app/main.py
# NOTE: For Windows users, use: C:\lab-001-docker-llm\services\app\main.py
# For Linux/Mac users, use: ~/lab-001-docker-llm/services/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import redis
import json

import os

app = FastAPI(title="LLM API with Memory")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Redis client for chat history
redis_client = redis.from_url(REDIS_URL)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "mistral"
    messages: list[Message]
    stream: bool = False
    temperature: float | None = 0.7
    session_id: str | None = None  # New: session support

@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest):
    """Chat with persistent history"""

    # Load history from Redis if session_id provided
    if request.session_id:
        try:
            history_key = f"chat:{request.session_id}"
            saved_history = redis_client.get(history_key)
            if saved_history:
                history = json.loads(saved_history)
            else:
                history = []
        except:
            history = []
    else:
        history = []

    # Combine saved history with new messages
    all_messages = history + [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]

    # Convert to Ollama format
    ollama_messages = all_messages

    payload = {
        "model": request.model,
        "messages": ollama_messages,
        "stream": request.stream,
        "options": {"temperature": request.temperature}
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        assistant_message = result.get("message", {}).get("content", "")

        # Save updated history to Redis
        if request.session_id:
            updated_history = all_messages + [
                {"role": "assistant", "content": assistant_message}
            ]
            history_key = f"chat:{request.session_id}"
            redis_client.setex(
                history_key,
                3600,  # Expire after 1 hour
                json.dumps(updated_history)
            )

        return {
            "message": {
                "role": "assistant",
                "content": assistant_message
            },
            "model": request.model,
            "done": result.get("done", False)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/v1/chat/sessions/{session_id}")
def clear_session(session_id: str):
    """Clear chat history for a session"""
    try:
        history_key = f"chat:{session_id}"
        redis_client.delete(history_key)
        return {"message": "Session cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Update dependencies:
```bash
cd ~/lab-001-docker-llm/services/app
uv add redis==8.1.0
```

### Rebuild and test:
```bash
cd ~/lab-001-docker-llm
docker-compose up -d --build

# Test persistent chat
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "Remember: My favorite color is blue"}],
    "session_id": "user123"
  }'

# Continue conversation (it should remember!)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "What is my favorite color?"}],
    "session_id": "user123"
  }'
```

### ✅ Checkpoint: Exercise 5
**Verify:** The AI remembers "blue" as the favorite color

---

## Final Challenge: Build a Chat UI (30 minutes)

### Task: Create a simple HTML chat interface

```html
<!-- ~/lab-001-docker-llm/services/app/static/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>LLM Chat</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        #chat { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; text-align: right; }
        .assistant { background: #f5f5f5; }
        #input { display: flex; gap: 10px; margin-top: 10px; }
        #input input { flex: 1; padding: 10px; }
        #input button { padding: 10px 20px; }
    </style>
</head>
<body>
    <h1>🤖 LLM Chat</h1>
    <div id="chat"></div>
    <div id="input">
        <input type="text" id="message" placeholder="Type a message...">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        const sessionId = 'session-' + Math.random().toString(36).substr(2, 9);
        const chatDiv = document.getElementById('chat');

        async function sendMessage() {
            const input = document.getElementById('message');
            const message = input.value.trim();
            if (!message) return;

            // Add user message
            addMessage('user', message);
            input.value = '';

            // Send to API
            const response = await fetch('/v1/chat/completions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    messages: [{role: 'user', content: message}],
                    session_id: sessionId
                })
            });

            const data = await response.json();
            addMessage('assistant', data.message.content);
        }

        function addMessage(role, content) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            div.textContent = content;
            chatDiv.appendChild(div);
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }

        document.getElementById('message').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

### Serve static files:
```python
# Add to main.py
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/chat")
def chat_ui():
    """Serve chat UI"""
    return FileResponse('static/index.html')
```

### ✅ Final Checkpoint
**Test:** Open [http://localhost:8000/chat](http://localhost:8000/chat) in your browser

You should have a working chat interface with memory!

---

## 🎓 Lab Completion Checklist

- [ ] Exercise 1: Run Ollama in Docker
- [ ] Exercise 2: Build LLM API Server
- [ ] Exercise 3: Chat Completion Test
- [ ] Exercise 4: Docker Compose Orchestration
- [ ] Exercise 5: Persistent Chat History
- [ ] Final Challenge: Chat UI

---

## 📚 Post-Lab Reading

- **[1401: Ollama Enterprise](../../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)** - Production Ollama deployment
- **[1402: vLLM and TGI](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)** - Advanced inference engines
- **[TUTORIAL-003: RAG Basics](../tutorials/TUTORIAL-003-RAG-Basics.md)** - Add knowledge to your LLM

---

## 🏆 Lab Badge

**Earned:** Docker & LLM Fundamentals Badge 🏅

Next: **[LAB-002: RAG Implementation](LAB-002-RAG-Implementation.md)**
