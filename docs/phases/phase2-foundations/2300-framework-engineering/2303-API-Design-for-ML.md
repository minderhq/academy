---
Document ID: 2303
Title: API Design for ML Systems
Phase: 2
Module: 2300
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'architecture', 'api-design', 'production']
---

# 2303: API Design for ML Systems

**Project:** AI Engineering Curriculum
**Phase:** [2300] Framework Engineering
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2 hours

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [API Protocol Comparison](#api-protocol-comparison)
- [REST API Design](#rest-api-design)
- [Streaming APIs](#streaming-apis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Authentication](#authentication)
- [Monitoring & Logging](#monitoring-logging)
- [Exercise: Build ML API](#exercise-build-ml-api)
- [Related Topics](#related-topics)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare API Protocol Comparison
- Explain REST API Design
- Explain Streaming APIs
- Explain Error Handling
- Explain Rate Limiting
- Explain Authentication

---

## Abstract

ML models in production need well-designed APIs that are fast, reliable, and easy to use. This document covers API design patterns specific to ML systems.

**What you'll learn:**
- REST vs GraphQL vs gRPC for ML
- Streaming APIs for real-time inference
- Error handling and rate limiting
- Authentication and authorization

---

## API Protocol Comparison

| Feature | REST | GraphQL | gRPC |
|---------|------|---------|------|
| **Protocol** | HTTP/1.1, HTTP/2 | HTTP | HTTP/2 |
| **Data Format** | JSON | JSON | Protobuf |
| **Type Safety** | Low (Pydantic helps) | Medium | High |
| **Streaming** | SSE/WebSocket | Subscription | Built-in |
| **Browser Support** | Excellent | Good | Requires gateway |
| **Performance** | Good | Good | Excellent |
| **Code Generation** | Manual | Manual | Automatic |
| **Use Case** | General purpose | Complex data | High performance |

### When to Use Each

**REST:**
- Simple ML models
- Web applications
- Mobile apps
- General purpose APIs

**GraphQL:**
- Complex nested data (RAG with sources)
- Flexible query requirements
- Multiple data sources

**gRPC:**
- High-throughput inference
- Microservices
- Internal ML pipelines
- Streaming responses

---

## REST API Design

### Standard Endpoints

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
import asyncio
import time

app = FastAPI(
    title="ML Model API",
    version="2.0.0",
    description="Production ML inference API"
)

# ========================================
# Request/Response Models
# ========================================

class PredictRequest(BaseModel):
    """Request model for predictions."""

    model_name: str = Field(
        ...,
        description="Name of the model to use",
        example="mistral-7b"
    )
    inputs: List[float] = Field(
        ...,
        description="Input features for prediction",
        example=[0.5, 0.3, 0.8, 0.1]
    )
    parameters: Dict[str, any] = Field(
        default_factory=dict,
        description="Additional model parameters",
        example={"temperature": 0.7, "max_tokens": 100}
    )

    @validator("model_name")
    def model_must_exist(cls, v):
        allowed_models = ["mistral-7b", "llama2-13b", "gpt-j-6b"]
        if v not in allowed_models:
            raise ValueError(f"Model must be one of {allowed_models}")
        return v


class PredictResponse(BaseModel):
    """Response model for predictions."""

    predictions: List[float] = Field(
        ...,
        description="Model predictions"
    )
    model_version: str = Field(
        ...,
        description="Version of model used"
    )
    processing_time_ms: float = Field(
        ...,
        description="Time taken for inference"
    )
    model_id: str = Field(
        ...,
        description="Unique model identifier"
    )


class ModelInfo(BaseModel):
    """Model information."""

    name: str
    version: str
    parameters: Dict[str, any]
    loaded_at: str
    memory_usage_mb: float


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    code: str
    details: Optional[Dict] = None
    timestamp: str


# ========================================
# API Endpoints
# ========================================

# Health Check
@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """
    Health check endpoint for load balancers.

    Returns 200 if service is healthy.
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "models_loaded": ",".join(loaded_models.keys())
    }


# List Available Models
@app.get("/models", response_model=List[str])
async def list_models():
    """List all available models."""
    return list(loaded_models.keys())


# Get Model Info
@app.get("/models/{model_name}", response_model=ModelInfo)
async def model_info(model_name: str):
    """Get detailed information about a model."""
    if model_name not in loaded_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found"
        )

    model = loaded_models[model_name]
    return ModelInfo(
        name=model_name,
        version=model.version,
        parameters=model.config,
        loaded_at=model.loaded_at.isoformat(),
        memory_usage_mb=model.get_memory_usage()
    )


# Single Prediction
@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Make a single prediction.

    - **model_name**: Which model to use
    - **inputs**: Input features
    - **parameters**: Optional model parameters
    """
    import time
    start = time.time()

    # Get model
    model = loaded_models.get(request.model_name)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{request.model_name}' not found. Available: {list(loaded_models.keys())}"
        )

    # Validate inputs
    if len(request.inputs) != model.input_size:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {model.input_size} inputs, got {len(request.inputs)}"
        )

    try:
        # Run inference
        predictions = model.predict(request.inputs, **request.parameters)

        return PredictResponse(
            predictions=predictions,
            model_version=model.version,
            processing_time_ms=(time.time() - start) * 1000,
            model_id=model.model_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {str(e)}"
        )


# Batch Prediction
@app.post("/predict/batch", response_model=List[PredictResponse])
async def predict_batch(requests: List[PredictRequest]):
    """
    Make multiple predictions efficiently.

    Processes requests for the same model in a batch.
    """
    results = []

    # Group by model
    by_model = {}
    for req in requests:
        if req.model_name not in by_model:
            by_model[req.model_name] = []
        by_model[req.model_name].append(req)

    # Process each model's batch
    for model_name, model_requests in by_model.items():
        model = loaded_models.get(model_name)
        if not model:
            for req in model_requests:
                results.append(PredictResponse(
                    predictions=[],
                    model_version="unknown",
                    processing_time_ms=0,
                    model_id="",
                    error=f"Model {model_name} not found"
                ))
            continue

        # Batch inference
        try:
            batch_predictions = model.predict_batch(
                [req.inputs for req in model_requests],
                **model_requests[0].parameters
            )

            for req, pred in zip(model_requests, batch_predictions):
                results.append(PredictResponse(
                    predictions=pred,
                    model_version=model.version,
                    processing_time_ms=0,  # Would measure in real impl
                    model_id=model.model_id
                ))

        except Exception as e:
            for req in model_requests:
                results.append(PredictResponse(
                    predictions=[],
                    model_version=model.version,
                    processing_time_ms=0,
                    model_id=model.model_id,
                    error=str(e)
                ))

    return results
```

### Best Practices

**1. Version Your APIs**

```python
# API v1
@app.post("/v1/predict")
async def predict_v1(request: PredictRequest):
    # Old implementation
    pass

# API v2
@app.post("/v2/predict")
async def predict_v2(request: PredictRequestV2):
    # New implementation with breaking changes
    pass
```

**2. Use Proper Status Codes**

```python
# 200 OK - Successful request
# 400 Bad Request - Invalid input
# 401 Unauthorized - No authentication
# 403 Forbidden - Authenticated but not authorized
# 404 Not Found - Resource doesn't exist
# 429 Too Many Requests - Rate limited
# 500 Internal Server Error - Server error
# 503 Service Unavailable - Service down for maintenance
```

**3. Request Validation**

```python
from pydantic import BaseModel, Field, validator

class Request(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=100, ge=1, le=4096)

    @validator("text")
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v
```

**4. Async Operations**

```python
import asyncio

@app.post("/predict")
async def predict(request: PredictRequest, background_tasks: BackgroundTasks):
    # Queue background task
    background_tasks.add_task(process_prediction, request)

    return {"request_id": "123", "status": "processing"}

@app.get("/predict/{request_id}")
async def get_prediction(request_id: str):
    # Check status
    result = await get_result(request_id)
    if result:
        return result
    else:
        return {"status": "processing"}
```

---

## Streaming APIs

### Server-Sent Events (SSE)

```python
from fastapi.responses import StreamingResponse
import json
import asyncio


@app.post("/generate")
async def generate_stream(prompt: str):
    """
    Stream tokens as they're generated.

    Uses Server-Sent Events (SSE) for streaming.
    """

    async def generate():
        model = loaded_models["mistral-7b"]

        # Stream tokens
        for token in model.generate_stream(prompt):
            data = json.dumps({
                "token": token,
                "done": False
            })
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.01)  # Simulate generation

        # Send completion
        data = json.dumps({
            "token": "",
            "done": True
        })
        yield f"data: {data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

### WebSocket for Real-time

```python
from fastapi import WebSocket
from typing import Dict


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time chat.

    Maintains persistent connection for interactive sessions.
    """
    await manager.connect(client_id, websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Generate response
            response = model.generate(data["message"])

            # Send response
            await manager.send_message(client_id, {
                "type": "response",
                "content": response
            })

    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.disconnect(client_id)
```

---

## Error Handling

### Standard Error Response

```python
class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, code: str, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ModelNotFoundError(APIError):
    """Model not found."""

    def __init__(self, model_name: str):
        super().__init__(
            message=f"Model '{model_name}' not found",
            code="MODEL_NOT_FOUND",
            details={"model_name": model_name}
        )


class InvalidInputError(APIError):
    """Invalid input data."""

    def __init__(self, field: str, value: any, reason: str):
        super().__init__(
            message=f"Invalid value for {field}",
            code="INVALID_INPUT",
            details={"field": field, "value": str(value), "reason": reason}
        )


class ModelOverloadedError(APIError):
    """Model too many requests."""

    def __init__(self, retry_after_seconds: int):
        super().__init__(
            message="Model is overloaded",
            code="MODEL_OVERLOADED",
            details={"retry_after": retry_after_seconds}
        )


# Exception handler
@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    from fastapi.responses import JSONResponse
    from datetime import datetime

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": exc.message,
                "code": exc.code,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_INPUT` | Malformed request | 400 |
| `MODEL_NOT_FOUND` | Model doesn't exist | 404 |
| `MODEL_OVERLOADED` | Too many requests | 429 |
| `TIMEOUT` | Request took too long | 408 |
| `RATE_LIMITED` | Rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Server error | 500 |

---

## Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Custom error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "message": "Rate limit exceeded",
                "code": "RATE_LIMITED",
                "retry_after": exc.retry_after
            }
        },
        headers={"Retry-After": str(exc.retry_after)}
    )


# Apply rate limiting
@app.post("/predict")
@limiter.limit("10/minute")  # 10 requests per minute
async def predict(request: Request, payload: PredictRequest):
    return await predict_logic(payload)


# Different limits for different endpoints
@app.post("/generate")
@limiter.limit("60/hour")  # 60 requests per hour
async def generate(request: Request, prompt: str):
    return await generate_logic(prompt)
```

### Token Bucket Rate Limiting

```python
import time
from collections import defaultdict, deque


class TokenBucket:
    """
    Token bucket rate limiter.

    Allows bursts up to capacity, then refills at rate.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = defaultdict(float)
        self.last_update = defaultdict(float)
        self.lock = asyncio.Lock()

    async def consume(self, key: str, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Returns:
            True if tokens were consumed
            False if rate limited
        """
        async with self.lock:
            now = time.time()

            # Refill tokens
            time_passed = now - self.last_update[key]
            self.tokens[key] = min(
                self.capacity,
                self.tokens[key] + time_passed * self.rate
            )
            self.last_update[key] = now

            # Check if enough tokens
            if self.tokens[key] >= tokens:
                self.tokens[key] -= tokens
                return True
            return False

    async def wait_for_tokens(self, key: str, tokens: int = 1):
        """Wait until tokens are available."""
        while not await self.consume(key, tokens):
            await asyncio.sleep(0.1)


# Usage
limiter = TokenBucket(rate=10.0, capacity=20)  # 10/sec, burst 20

@app.post("/predict")
async def predict(request: PredictRequest):
    client_id = get_client_id(request)

    if not await limiter.consume(client_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    return await predict_logic(request)
```

---

## Authentication

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
import jwt
from datetime import datetime, timedelta


# Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"


security = HTTPBearer()


def create_token(user_id: str, expires_delta: timedelta = None) -> str:
    """Create JWT token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)

    to_encode = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current user from token."""
    token = credentials.credentials
    payload = verify_token(token)
    return payload


# Protected endpoint
@app.post("/predict")
async def protected_predict(
    request: PredictRequest,
    user: dict = Depends(get_current_user)
):
    """
    Protected prediction endpoint.

    Requires valid JWT token.
    """
    # User info available in user dict
    user_id = user.get("user_id")

    # Rate limit per user
    if not await user_limiter.consume(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return await predict_logic(request)
```

---

## Monitoring & Logging

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response
import time


# Metrics
predict_counter = Counter(
    "predict_requests_total",
    "Total predict requests",
    ["model_name", "status"]
)

predict_duration = Histogram(
    "predict_duration_seconds",
    "Predict request duration",
    ["model_name"]
)


@app.post("/predict")
async def predict_with_metrics(request: PredictRequest):
    start_time = time.time()

    status = "success"

    try:
        result = await predict_logic(request)
        predict_counter.labels(
            model_name=request.model_name,
            status=status
        ).inc()
        return result

    except Exception as e:
        status = "error"
        predict_counter.labels(
            model_name=request.model_name,
            status=status
        ).inc()
        raise

    finally:
        duration = time.time() - start_time
        predict_duration.labels(
            model_name=request.model_name
        ).observe(duration)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")
```

---

## Exercise: Build ML API

### Task

Create a complete ML API with:
1. Predict endpoint (single and batch)
2. Streaming endpoint
3. Error handling
4. Rate limiting
5. Authentication

### Starter Code

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class PredictRequest(BaseModel):
    inputs: List[float]

class PredictResponse(BaseModel):
    predictions: List[float]

# TODO: Implement endpoints
# - POST /predict
# - POST /predict/batch
# - POST /generate (streaming)
# - GET /health
# - GET /models

# TODO: Add error handling
# TODO: Add rate limiting
# TODO: Add authentication
```

---

## References

### Related ai-engineering-curriculum Documents

- [2301: Framework Design Patterns](2301-Framework-Design-Patterns.md)
- [2302: Model Serving Architectures](2302-Model-Serving-Architectures.md)
- [2304: Production Deployment Patterns](2304-Production-Deployment-Patterns.md)

---

## Next Steps

- Continue with: **[2304: Production Deployment Patterns](./2304-Production-Deployment-Patterns.md)**
- Practical: **[LAB-007: Production RAG](../../../learning-resources/labs/LAB-007-Production-RAG.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

## Related Topics

- [TUTORIAL-003: RAG Basics](../../../learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md)
- [1401: Ollama Enterprise](../../phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)
- [2302: Model Serving Architectures](./2302-Model-Serving-Architectures.md)
- [6101: Vector Search](../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)
