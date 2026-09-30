---
Document ID: TEMPLATE-010-Chatbot-UI
Title: "PROJECT TEMPLATE: Chatbot UI"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Tags: ['template', 'llm', 'inference']
---

# PROJECT TEMPLATE: Chatbot UI

Build modern chat interfaces for LLMs.

## Project Structure

```text
chatbot-ui/
├── README.md
├── package.json
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py        # Chat endpoints
│   │   │   ├── models.py      # Model management
│   │   │   └── auth.py        # Authentication
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py
│   │   │   ├── rag_service.py
│   │   │   └── memory_service.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── rate_limit.py
│   │   │   └── logging.py
│   │   └── main.py
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── InputBox.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── SettingsPanel.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts
│   │   │   ├── useStreaming.ts
│   │   │   └── useDebounce.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── App.tsx
│   ├── public/
│   └── styles/
├── shared/
│   └── types/
│       └── api.yaml
└── deployment/
    ├── nginx.conf
    └── docker-compose.prod.yml
```

## Features

- Real-time chat interface
- Streaming responses
- Conversation history
- Model selection
- API and WebSocket support
- Responsive design

## Quick Start

### Backend Setup

```python
# backend/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.chat import chat_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat")
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

## Backend Endpoints

```python
# Chat endpoint
@app.post("/api/chat/completions")
async def chat_completion(request: ChatRequest):
    return await llm_service.generate(request)

# Streaming endpoint
@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        async for chunk in llm_service.generate_stream(request):
            yield f"data: {chunk.json()}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# History endpoint
@app.get("/api/chat/history")
async def get_history(user_id: str):
    return await memory_service.get_history(user_id)
```

## Frontend Components

### Chat Window

```tsx
// frontend/src/components/ChatWindow.tsx
import { useChat } from '../hooks/useChat';

export function ChatWindow() {
  const { messages, sendMessage, isStreaming } = useChat();

  return (
    <div className="chat-window">
      <MessageList messages={messages} />
      <InputBox
        onSend={sendMessage}
        disabled={isStreaming}
      />
    </div>
  );
}
```

### Streaming Hook

```tsx
// frontend/src/hooks/useStreaming.ts
export function useStreaming() {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const streamResponse = async (prompt: string) => {
    setIsStreaming(true);
    setResponse('');

    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });

    const reader = response.body?.getReader();
    // Handle streaming...
  };

  return { response, isStreaming, streamResponse };
}
```

## Features Implementation

### Conversation History

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  model?: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}
```

### Model Selection

```tsx
// frontend/src/components/ModelSelector.tsx
const MODELS = [
  { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI' },
  { id: 'claude-3', name: 'Claude 3', provider: 'Anthropic' },
  { id: 'llama-2', name: 'Llama 2', provider: 'Local' },
];
```

### WebSocket Support

```typescript
// frontend/src/services/websocket.ts
export class ChatWebSocket {
  private ws: WebSocket;

  connect(url: string) {
    this.ws = new WebSocket(url);
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Handle message
    };
  }

  send(message: string) {
    this.ws.send(JSON.stringify({ message }));
  }
}
```

## Deployment

```yaml
# deployment/docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://db:5432/chatbot
    depends_on:
      - db

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./deployment/nginx.conf:/etc/nginx/nginx.conf
```

---

**Difficulty:** Intermediate
**Estimated Time:** 8-12 hours
**Skills:** React, FastAPI, WebSocket, Docker
