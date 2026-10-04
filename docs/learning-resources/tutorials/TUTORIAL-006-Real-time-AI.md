---
Document ID: TUTORIAL-006
Title: "TUTORIAL-006: Real-time AI"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 60 minutes
Prerequisites: [PHASE-4]
Tags: ['tutorial', 'inference', 'serving']
---

# TUTORIAL-006: Real-time AI

**Streaming Responses and Real-Time Interactions**

---

## Tutorial Overview

**Time:** 60 minutes
**Difficulty:** ⭐⭐ Intermediate
**Prerequisites:**
- LAB-002: RAG Implementation
- Basic FastAPI knowledge
- Understanding of async/await

**Learning Objectives:**
- Implement streaming LLM responses
- Build WebSocket connections
- Use Server-Sent Events (SSE)
- Create real-time chat interface
- Handle production deployment

---

## Part 1: Streaming LLM Responses (15 minutes)

### Understanding Streaming

Traditional LLM API calls wait for the complete response before returning. Streaming returns tokens as they're generated, providing:
- Faster perceived response time
- Better user experience
- Real-time feedback

```python
# File: streaming_llm.py
"""
Streaming LLM Responses
========================
"""

import asyncio
from typing import AsyncGenerator
from openai import AsyncOpenAI

class StreamingLLM:
    """
    Streaming LLM client.
    """

    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key)

    async def stream_completion(
        self,
        prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion tokens.

        Args:
            prompt: User prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Individual tokens as they arrive
        """
        stream = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def stream_with_callback(
        self,
        prompt: str,
        callback: callable,
        **kwargs
    ):
        """
        Stream with callback function.

        Args:
            prompt: User prompt
            callback: Async function to call with each token
            **kwargs: Additional arguments for stream_completion
        """
        async for token in self.stream_completion(prompt, **kwargs):
            await callback(token)

# Demo
async def demo_streaming():
    """Demonstrate streaming"""
    llm = StreamingLLM()

    print("=== Streaming Response ===\n")

    full_response = ""

    async for token in llm.stream_completion(
        "Explain quantum computing in one paragraph"
    ):
        print(token, end="", flush=True)
        full_response += token

    print(f"\n\nTotal tokens: {len(full_response.split())}")

if __name__ == "__main__":
    asyncio.run(demo_streaming())
```

**Checkpoint 1:** ✅ Streaming responses working

---

## Part 2: WebSocket Real-Time Chat (20 minutes)

### Building WebSocket Interface

```python
# File: websocket_chat.py
"""
Real-time Chat with WebSockets
===============================
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import uvicorn

app = FastAPI()

class ConnectionManager:
    """
    Manage WebSocket connections.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.client_data: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect new client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_data[websocket] = {"id": client_id}

    def disconnect(self, websocket: WebSocket):
        """Disconnect client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_data:
            del self.client_data[websocket]

    async def send_personal(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)

    async def broadcast(self, message: str, exclude: WebSocket = None):
        """Broadcast message to all clients"""
        for connection in self.active_connections:
            if connection != exclude:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time chat.
    """
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Process message (you would call LLM here)
            response = {
                "type": "message",
                "from": message_data.get("from", client_id),
                "content": message_data.get("content", ""),
                "timestamp": message_data.get("timestamp")
            }

            # Broadcast to all clients
            await manager.broadcast(json.dumps(response))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(json.dumps({
            "type": "system",
            "content": f"Client {client_id} disconnected"
        }))

@app.get("/")
async def get():
    """Serve chat interface"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real-time Chat</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; }
            #messages { height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }
            .message { margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; }
            .system { background: #fff3cd; }
            #input-area { display: flex; gap: 10px; margin-top: 20px; }
            input { flex: 1; padding: 10px; }
            button { padding: 10px 20px; }
        </style>
    </head>
    <body>
        <h1>Real-time Chat</h1>
        <div id="messages"></div>
        <div id="input-area">
            <input type="text" id="message" placeholder="Type a message...">
            <button onclick="sendMessage()">Send</button>
        </div>

        <script>
            const clientId = 'user_' + Math.random().toString(36).substr(2, 9);
            const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message' + (data.type === 'system' ? ' system' : '');
                messageDiv.textContent = `${data.from || 'System'}: ${data.content}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            };

            function sendMessage() {
                const input = document.getElementById('message');
                const message = input.value.trim();
                if (message) {
                    ws.send(JSON.stringify({
                        type: 'message',
                        from: clientId,
                        content: message,
                        timestamp: new Date().toISOString()
                    }));
                    input.value = '';
                }
            }

            document.getElementById('message').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Checkpoint 2:** ✅ WebSocket chat working

---

## Part 3: Server-Sent Events (15 minutes)

### SSE Implementation

```python
# File: sse_streaming.py
"""
Server-Sent Events (SSE)
=======================
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

app = FastAPI()

# Enable CORS for SSE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def generate_streaming_response(prompt: str):
    """
    Generate SSE streaming response.

    SSE format:
    data: {"content": "Hello"}

    data: {"content": " World"}

    data: [DONE]
    """
    # Simulate LLM streaming
    response_text = f"This is a simulated response to: {prompt}. In production, this would stream from an actual LLM."

    for word in response_text.split():
        chunk = {
            "content": word + " "
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        await asyncio.sleep(0.1)  # Simulate token generation delay

    # Send completion signal
    yield "data: [DONE]\n\n"

@app.get("/")
async def root():
    """SSE demo page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SSE Demo</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; }
            #output { min-height: 200px; border: 1px solid #ccc; padding: 10px; }
            button { padding: 10px 20px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Server-Sent Events Demo</h1>
        <div id="output"></div>
        <button onclick="startStream()">Start Stream</button>

        <script>
            function startStream() {
                const output = document.getElementById('output');
                output.innerHTML = '';

                const eventSource = new EventSource('/stream?prompt=Hello');

                eventSource.onmessage = (event) => {
                    if (event.data === '[DONE]') {
                        eventSource.close();
                        output.innerHTML += '<br><strong>Stream complete!</strong>';
                    } else {
                        const data = JSON.parse(event.data);
                        output.innerHTML += data.content;
                    }
                };

                eventSource.onerror = () => {
                    eventSource.close();
                };
            }
        </script>
    </body>
    </html>
    """

@app.get("/stream")
async def stream(prompt: str = "Hello"):
    """SSE streaming endpoint"""
    return StreamingResponse(
        generate_streaming_response(prompt),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Checkpoint 3:** ✅ SSE streaming working

---

## Part 4: Production Considerations (10 minutes)

### Deployment Best Practices

```yaml
# File: docker-compose.realtime.yml

services:
  realtime-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - MODEL_NAME=gpt-4
    depends_on:
      - redis
    deploy:
      replicas: 3
    restart: unless-stopped

  redis:
    image: redis:alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - realtime-api
    restart: unless-stopped
```

**Key Production Considerations:**

1. **Connection Management**
   - Limit concurrent connections
   - Implement heartbeat/ping
   - Handle graceful disconnects

2. **Scaling**
   - Use Redis for connection state sharing
   - Load balance WebSocket connections
   - Consider serverless for auto-scaling

3. **Monitoring**
   - Track connection metrics
   - Monitor message latency
   - Log errors and disconnections

4. **Security**
   - Authenticate WebSocket connections
   - Rate limit messages
   - Validate all inputs

---

## Tutorial Completion Checklist

- [ ] Part 1: Streaming LLM responses
- [ ] Part 2: WebSocket chat
- [ ] Part 3: Server-Sent Events
- [ ] Part 4: Production deployment

---

## Summary

In this tutorial, you learned:

1. **Streaming Responses** - Token-by-token output
2. **WebSockets** - Bidirectional real-time communication
3. **Server-Sent Events** - Simple one-way streaming
4. **Production** - Deployment best practices

---

## Next Steps

1. **LAB-011: Multi-Modal AI** - Add streaming to vision systems
2. **LAB-012: Audio AI** - Real-time speech recognition
3. **PROJECT-003: Real-time Assistant** - Build complete real-time AI

---

**Tutorial:** 006 - Real-time AI
**Time Estimate:** 60 minutes
**Difficulty:** ⭐⭐ Intermediate
