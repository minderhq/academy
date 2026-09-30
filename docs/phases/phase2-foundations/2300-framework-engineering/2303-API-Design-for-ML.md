---
Document ID: 2303
Title: "2303: API Design for ML Systems"
Phase: 2
Module: 2300
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'architecture', 'api-design', 'production']
---

# 2303: API Design for ML Systems

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
- [Monitoring & Logging](#monitoring--logging)
- [Exercise: Build ML API](#exercise-build-ml-api)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Choose between REST, GraphQL, and gRPC for a given ML serving workload
- Design typed, self-documenting REST endpoints with Pydantic v2 request/response models
- Stream inference results over SSE and drive interactive sessions over WebSocket
- Map failure modes to one error envelope and the correct HTTP status codes
- Protect endpoints with rate limiting (slowapi, plus hand-rolled token bucket and sliding-window limiters)
- Authenticate requests with JWT bearer tokens and per-user limits
- Expose Prometheus metrics for request rate, latency, and errors

---

## Abstract

ML models in production need well-designed APIs that are fast, reliable, and easy to use. This document covers API design patterns specific to ML systems.

**What You'll Learn:**
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
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

# Stand-alone app for this section. Later sections each build their own small
# app so the examples stay independently runnable (redefining a route on the
# same app would silently shadow nothing - Starlette serves the FIRST match).
app = FastAPI(
    title="ML Model API",
    version="2.0.0",
    description="Production ML inference API"
)

# ========================================
# Model registry (stand-in inference backend)
# ========================================

# A real deployment loads trained weights here (see 2302: Model Serving
# Architectures for batching and pipelining). For the API-design examples we
# ship a deterministic stub so every endpoint is runnable end to end.
class LoadedModel:
    """Wraps an inference model plus the metadata the API exposes."""

    def __init__(self, model_id: str, version: str, input_size: int,
                 config: dict[str, Any] | None = None):
        self.model_id = model_id
        self.version = version
        self.input_size = input_size   # number of inputs the model expects
        self.config = config or {}
        self.loaded_at = datetime.now(timezone.utc)
        # Stub weight scale: predictions are scale * inputs, so output is
        # deterministic and easy to assert against in tests.
        self.scale = float(self.config.get("scale", 2.0))

    def predict(self, inputs: list[float], **params) -> list[float]:
        # Stub inference: swap this line for the real model call.
        return [x * self.scale for x in inputs]

    def predict_batch(self, batch: list[list[float]], **params) -> list[list[float]]:
        return [self.predict(row, **params) for row in batch]

    def get_memory_usage(self) -> float:
        # Stub: a real loader reports the resident size of the model tensors.
        return 512.0


loaded_models: dict[str, LoadedModel] = {
    name: LoadedModel(model_id=f"{name}@v1", version="1.0.0", input_size=4)
    for name in ["mistral-7b", "llama2-13b", "gpt-j-6b"]
}


# ========================================
# Request/Response Models
# ========================================

class PredictRequest(BaseModel):
    """Request model for predictions."""

    model_name: str = Field(
        ...,
        description="Name of the model to use",
        # pydantic v2: bare example= is deprecated (extra kwargs on Field);
        # single examples live in json_schema_extra, lists in examples=[...].
        json_schema_extra={"example": "mistral-7b"},
    )
    inputs: list[float] = Field(
        ...,
        description="Input features for prediction",
        json_schema_extra={"example": [0.5, 0.3, 0.8, 0.1]},
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional model parameters",
        json_schema_extra={"example": {"temperature": 0.7, "max_tokens": 100}},
    )

    @field_validator("model_name")
    @classmethod
    def model_must_exist(cls, v: str) -> str:
        # Registry keys are the source of truth - the allowed list can't drift
        # from what's actually loaded.
        allowed_models = list(loaded_models.keys())
        if v not in allowed_models:
            raise ValueError(f"Model must be one of {allowed_models}")
        return v


class PredictResponse(BaseModel):
    """Response model for predictions."""

    predictions: list[float] = Field(
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


class BatchItemResponse(BaseModel):
    """Per-request result inside a batch.

    Batch items can fail individually, so this wrapper carries an optional
    error field. The single-predict endpoint raises HTTPException instead -
    there a failure means the whole request failed.
    """

    request_index: int = Field(
        ...,
        description="Position in the incoming list; results return in input order"
    )
    predictions: list[float] | None = None
    model_version: str
    processing_time_ms: float
    model_id: str
    error: str | None = None


class ModelInfo(BaseModel):
    """Model information."""

    name: str
    version: str
    parameters: dict[str, Any]
    loaded_at: str
    memory_usage_mb: float


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    code: str
    details: dict[str, Any] | None = None
    timestamp: str


# ========================================
# API Endpoints
# ========================================

# Health Check
@app.get("/health", response_model=dict[str, str])
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
@app.get("/models", response_model=list[str])
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
    - **parameters**: The model parameters
    """
    start = time.perf_counter()  # monotonic clock: immune to wall-clock jumps

    # Get model
    model = loaded_models.get(request.model_name)
    if model is None:
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
        # The stub inference is instant; a real model call would be offloaded
        # to a worker or a batching server (see 2302) so the event loop,
        # which serves every request, is never blocked.
        predictions = model.predict(request.inputs, **request.parameters)

        return PredictResponse(
            predictions=predictions,
            model_version=model.version,
            processing_time_ms=(time.perf_counter() - start) * 1000,
            model_id=model.model_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {str(e)}"
        )


# Batch Prediction
@app.post("/predict/batch", response_model=list[BatchItemResponse])
async def predict_batch(requests: list[PredictRequest]):
    """
    Make multiple predictions efficiently.

    Processes requests for the same model in a batch. Items fail
    individually: a bad row becomes an error entry, not a failed request.
    (Unknown model names are already rejected upstream by the PredictRequest
    validator - the None branch here is defense in depth.) Results return in
    the caller's original order.
    """
    results: list[BatchItemResponse | None] = [None] * len(requests)

    # Group by model, remembering each request's original position
    by_model: dict[str, list] = {}
    for idx, req in enumerate(requests):
        by_model.setdefault(req.model_name, []).append((idx, req))

    # Process each model's batch
    for model_name, model_requests in by_model.items():
        model = loaded_models.get(model_name)
        if model is None:
            for idx, _req in model_requests:
                results[idx] = BatchItemResponse(
                    request_index=idx,
                    predictions=None,
                    model_version="unknown",
                    processing_time_ms=0.0,
                    model_id="",
                    error=f"Model {model_name} not found"
                )
            continue

        t0 = time.perf_counter()
        try:
            # Contract note: the FIRST request's parameters apply to the whole
            # batch - a real API would validate that all rows agree.
            batch_predictions = model.predict_batch(
                [req.inputs for _idx, req in model_requests],
                **model_requests[0][1].parameters
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000

            for (idx, _req), pred in zip(model_requests, batch_predictions):
                results[idx] = BatchItemResponse(
                    request_index=idx,
                    predictions=pred,
                    model_version=model.version,
                    # One batch call produced all rows: report each item's
                    # share of the measured batch time.
                    processing_time_ms=elapsed_ms / len(model_requests),
                    model_id=model.model_id
                )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            for idx, _req in model_requests:
                results[idx] = BatchItemResponse(
                    request_index=idx,
                    predictions=None,
                    model_version=model.version,
                    processing_time_ms=elapsed_ms / len(model_requests),
                    model_id=model.model_id,
                    error=str(e)
                )

    return results
```

### Best Practices

**1. Version Your APIs**

```python
# Versioning pattern: route both prefixes, keep v1 alive during migration.
# v2 adds fields ADDITIVELY (new optional fields only), so existing v1
# clients keep passing validation.

class PredictRequestV2(PredictRequest):
    """v2 request: adds optional sampling parameters without breaking v1."""
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)


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
# 504 Gateway Timeout - Upstream (inference) blew its deadline
```

**3. Request Validation**

```python
from pydantic import BaseModel, Field, field_validator

class TextGenerationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=100, ge=1, le=4096)

    @field_validator("text")  # pydantic v2: @validator is the deprecated v1 style
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v
```

**4. Async Operations**

```python
import time
import uuid

from fastapi import BackgroundTasks
from pydantic import BaseModel


# In production this store is Redis or a queue; an in-process dict keeps the
# example runnable.
results_store: dict[str, dict] = {}


def process_prediction(request_id: str, request: PredictRequest) -> None:
    """Background worker: runs inference and stores the result."""
    start = time.perf_counter()
    model = loaded_models[request.model_name]
    predictions = model.predict(request.inputs, **request.parameters)
    results_store[request_id] = {
        "predictions": predictions,
        "processing_time_ms": (time.perf_counter() - start) * 1000,
    }


@app.post("/predict/async", status_code=202)
async def submit_prediction(request: PredictRequest, background_tasks: BackgroundTasks):
    """Accept the request, queue inference, return immediately with a handle.

    202 Accepted is the correct status for "queued, not done yet".
    """
    request_id = uuid.uuid4().hex
    background_tasks.add_task(process_prediction, request_id, request)
    return {"request_id": request_id, "status": "processing"}


@app.get("/predict/async/{request_id}")
async def get_prediction(request_id: str):
    """Poll for a completed prediction."""
    result = results_store.get(request_id)
    if result is None:
        return {"request_id": request_id, "status": "processing"}
    return {"request_id": request_id, "status": "complete", **result}
```

---

## Streaming APIs

### Server-Sent Events (SSE)

```python
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI()


# Stand-in for a real streaming model call (vLLM/TGI yield tokens the same
# way - see 1402). Deterministic, so the SSE frames are assertable in tests.
async def stream_tokens(prompt: str):
    for token in prompt.split():
        yield token


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)


@app.post("/generate")
async def generate_stream(request: GenerateRequest):
    """
    Stream tokens as they're generated.

    Uses Server-Sent Events (SSE): every event is `data: <json>\\n\\n`.
    Takes a JSON body, not a query param - a prompt in the URL leaks into
    access logs and proxy caches.
    """

    async def generate():
        # Stream tokens
        async for token in stream_tokens(request.prompt):
            data = json.dumps({
                "token": token,
                "done": False
            })
            yield f"data: {data}\n\n"

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
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

### WebSocket for Real-time

```python


from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


# Stand-in inference: swap for a real generate() call (see 1402 for streaming
# backends). Deterministic, so tests can assert the reply.
async def generate_reply(message: str) -> str:
    return f"echo: {message}"


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time chat.

    Maintains a persistent connection for interactive sessions.
    Connect with /ws/chat?client_id=c1.
    """
    await manager.connect(client_id, websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            message = data.get("message")
            if not message:
                # Malformed payload: answer with an error frame instead of
                # crashing the handler with KeyError.
                await manager.send_message(client_id, {
                    "type": "error",
                    "content": "missing 'message' field"
                })
                continue

            # Generate response
            response = await generate_reply(message)

            # Send response
            await manager.send_message(client_id, {
                "type": "response",
                "content": response
            })

    except WebSocketDisconnect:
        pass  # Normal end of session - not an error
    finally:
        manager.disconnect(client_id)
```

---

## Error Handling

### Standard Error Response

```python
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Base exception for API errors.

    Each subclass carries the HTTP status the table below promises, so the
    handler can honor per-class codes instead of flattening everything to
    400 - a missing model (404) and an overloaded backend (429) mean very
    different things to a client's retry logic.
    """

    status_code: int = 400

    def __init__(self, message: str, code: str,
                 details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ModelNotFoundError(APIError):
    """Model not found -> 404."""

    status_code = 404

    def __init__(self, model_name: str):
        super().__init__(
            message=f"Model '{model_name}' not found",
            code="MODEL_NOT_FOUND",
            details={"model_name": model_name}
        )


class InvalidInputError(APIError):
    """Invalid input data -> 400."""

    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            message=f"Invalid value for {field}",
            code="INVALID_INPUT",
            details={"field": field, "value": str(value), "reason": reason}
        )


class ModelOverloadedError(APIError):
    """Model saturated -> 429, with Retry-After so clients can back off."""

    status_code = 429

    def __init__(self, retry_after_seconds: int):
        super().__init__(
            message="Model is overloaded",
            code="MODEL_OVERLOADED",
            details={"retry_after": retry_after_seconds}
        )


app = FastAPI()


# Exception handler: converts any APIError into the standard error envelope
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    headers = {}
    retry_after = exc.details.get("retry_after")
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.code,
                "details": exc.details,
                # timezone-aware UTC; datetime.utcnow() is deprecated since
                # Python 3.12 and returns a naive datetime.
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        },
        headers=headers
    )


# Demo route showing the handler in action
@app.get("/demo/missing-model")
async def demo_missing_model():
    raise ModelNotFoundError("mistral-7b")
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_INPUT` | Malformed request | 400 |
| `MODEL_NOT_FOUND` | Model doesn't exist | 404 |
| `MODEL_OVERLOADED` | Too many requests | 429 |
| `TIMEOUT` | Request took too long | 504 |
| `RATE_LIMITED` | Rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Server error | 500 |

> **408 vs 504:** `408 Request Timeout` is what a server returns when the
> **client** is too slow to send its request. When **our inference** blows a
> deadline, the correct code is `504 Gateway Timeout` - the timeout happened
> upstream of the API layer.

---

## Rate Limiting

```python


from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# headers_enabled=True makes slowapi inject Retry-After and X-RateLimit-*
# headers; without it the handler returns a bare 429 body.
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)

app = FastAPI()
app.state.limiter = limiter


# Custom handler: keep the standard error envelope, but reuse slowapi's
# header injection so clients still receive Retry-After / X-RateLimit-*.
# Note: the exception carries the matched limit as exc.detail (e.g. "10 per
# 1 minute") - the exact wait comes back in the injected Retry-After header.
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=429,
        content={
            "error": {
                "message": f"Rate limit exceeded: {exc.detail}",
                "code": "RATE_LIMITED"
            }
        }
    )
    return request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )


class PredictRequest(BaseModel):
    inputs: list[float]


# Apply rate limiting
@app.post("/predict")
@limiter.limit("10/minute")  # 10 requests per minute per client IP
# The decorator reads the client key from the Request parameter, and with
# headers_enabled=True it injects X-RateLimit-* into the `response` parameter
# FastAPI supplies - omitting either one makes the decorator raise.
async def predict(request: Request, response: Response, payload: PredictRequest):
    # Stand-in inference
    return {"predictions": [x * 2.0 for x in payload.inputs]}


# Different limits for different endpoints
@app.post("/generate")
@limiter.limit("60/hour")  # 60 requests per hour
async def generate(request: Request, response: Response, prompt: str = ""):
    return {"queued": True, "prompt": prompt}
```

### Token Bucket Rate Limiting

```python
import asyncio
import time
from collections import defaultdict


from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel


class TokenBucket:
    """
    Token bucket rate limiter.

    Allows bursts up to capacity, then refills at `rate` tokens per second.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = defaultdict(lambda: float(capacity))  # start full
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
            # monotonic clock: interval math is immune to wall-clock jumps
            now = time.monotonic()

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
            await asyncio.sleep(0.05)


def get_client_id(request: Request) -> str:
    # Key by caller identity: client IP is the fallback; prefer an API key
    # or authenticated user id when you have one (IPs collide behind NAT).
    return request.client.host if request.client else "anonymous"


# Usage
limiter = TokenBucket(rate=10.0, capacity=20)  # 10/sec sustained, burst 20

app = FastAPI()


class PredictRequest(BaseModel):
    inputs: list[float]


def predict_logic(request: PredictRequest) -> dict:
    # Stand-in inference
    return {"predictions": [x * 2.0 for x in request.inputs]}


@app.post("/predict")
async def predict(request: PredictRequest, http_request: Request):
    client_id = get_client_id(http_request)

    if not await limiter.consume(client_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    return predict_logic(request)
```

---

## Authentication

```python
import os
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


# Configuration
# Load from a secret manager / env var in production, never source control.
# HMAC keys SHOULD be at least 32 bytes - PyJWT warns
# (InsecureKeyLengthWarning) below that, per RFC 7518 section 3.2.
SECRET_KEY = os.environ.get("API_JWT_SECRET", "dev-only-secret-0123456789abcdef0123456789")
ALGORITHM = "HS256"


security = HTTPBearer()


def create_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create JWT token."""
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    now = datetime.now(timezone.utc)  # utcnow() is deprecated since Python 3.12
    to_encode = {
        "user_id": user_id,
        "exp": now + expires_delta,
        "iat": now
    }

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if "user_id" not in payload:
        # A structurally valid token without the claim we depend on
        raise HTTPException(status_code=401, detail="Token missing user_id claim")
    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict[str, Any]:
    """Get current user from token."""
    return verify_token(credentials.credentials)


# Per-user sliding-window limiter: remembers the timestamps of the last
# window and rejects when it is full. Contrast with the token bucket above,
# which smooths bursts by refilling continuously.
class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: dict[str, deque] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window = self.hits.setdefault(key, deque())
        while window and now - window[0] > self.window_seconds:
            window.popleft()
        if len(window) >= self.max_requests:
            return False
        window.append(now)
        return True


user_limiter = SlidingWindowLimiter(max_requests=5, window_seconds=60.0)


app = FastAPI()


class PredictRequest(BaseModel):
    inputs: list[float]


def predict_logic(request: PredictRequest) -> dict:
    # Stand-in inference
    return {"predictions": [x * 2.0 for x in request.inputs]}


# Protected endpoint
@app.post("/predict")
async def protected_predict(
    request: PredictRequest,
    user: dict[str, Any] = Depends(get_current_user)
):
    """
    Protected prediction endpoint.

    Requires a valid JWT token (Authorization: Bearer <token>).
    """
    # Rate limit per user
    if not user_limiter.allow(user["user_id"]):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return predict_logic(request)
```

---

## Monitoring & Logging

```python
import time


from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel

# prometheus_client keeps a process-wide default registry: metric names are
# global, so these are defined once and re-registering them raises
# Duplicated timeseries.
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


app = FastAPI()


class PredictRequest(BaseModel):
    model_name: str = "mistral-7b"
    inputs: list[float]


def predict_logic(request: PredictRequest) -> dict:
    # Stand-in inference
    return {"predictions": [x * 2.0 for x in request.inputs]}


@app.post("/predict")
async def predict_with_metrics(request: PredictRequest):
    start_time = time.perf_counter()

    status = "success"

    try:
        result = predict_logic(request)
        predict_counter.labels(
            model_name=request.model_name,
            status=status
        ).inc()
        return result

    except Exception:
        status = "error"
        predict_counter.labels(
            model_name=request.model_name,
            status=status
        ).inc()
        raise

    finally:
        predict_duration.labels(
            model_name=request.model_name
        ).observe(time.perf_counter() - start_time)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4"  # Prometheus exposition format
    )
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


app = FastAPI()

class PredictRequest(BaseModel):
    inputs: list[float]

class PredictResponse(BaseModel):
    predictions: list[float]

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

## Summary

- **Protocol choice is architectural:** REST for request/response, SSE for server-push streaming, WebSocket for bidirectional sessions, and 202 + polling for long-running inference - pick per access pattern, not per fashion.
- **Typed contracts:** pydantic v2 models (`BaseModel`, `field_validator`, `json_schema_extra`) validate every request before it reaches inference - a malformed payload is a 4xx, never a crashed worker.
- **Streaming:** SSE with `X-Accel-Buffering: no` behind nginx, WebSocket with explicit disconnect handling, and `202 Accepted` + polling for jobs longer than any client timeout.
- **Errors:** one `ErrorResponse` envelope (error / code / details) with correct status codes - 400 bad input, 404 unknown model, 429 throttled, 504 when inference blows its deadline (408 is for the client being slow).
- **Rate limiting:** slowapi for the quick win (`headers_enabled=True` plus `_inject_headers` in the custom handler), token bucket for burst smoothing, sliding window for hard per-user caps.
- **Auth and observability:** JWT bearer tokens with timezone-aware expiry, and Prometheus counters/histograms on every request path - an API you cannot measure is an API you cannot operate.

## References

### Related Documents

- [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md)
- [2302: Model Serving Architectures](./2302-Model-Serving-Architectures.md)
- [2304: Production Deployment Patterns](./2304-Production-Deployment-Patterns.md)

### External References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://pydantic.dev/docs/validation/latest/get-started/)
- [SlowAPI Documentation](https://slowapi.readthedocs.io/en/latest/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/en/stable/)

## Next Steps

- Next Lesson: **[2304: Production Deployment Patterns](./2304-Production-Deployment-Patterns.md)**
- Practical: **[LAB-007: Production RAG System](../../../learning-resources/labs/LAB-007-Production-RAG.md)**
- Assessment: **[2300: Framework Engineering - Quiz](./assessment/QUIZ.md)**

**Related:** [1402: vLLM and TGI High-Concurrency Inference](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md), [TUTORIAL-003: RAG Basics - Give Your LLM Knowledge](../../../learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md), [6101: HNSW Indexing - Efficient Semantic Search at Scale](../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)

**Experiment:** [EXP_1403: TGI (Text Generation Inference) Tuning Experiments](../../../../experiments/EXP_1403_TGI_TUNING.md) (nearest-relevant - no EXP_23xx exists; tune serving-layer throughput and concurrency limits before exposing them through an API surface)
