---
Document ID: 2306
Title: "2306: Building a Production Framework"
Phase: 2
Module: 2300
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: production-framework, plugin-architecture, configuration, dynamic-batching, fastapi, docker, nginx
---

# 2306: Building a Production Framework

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Project Overview](#project-overview)
- [Step 1: Core Framework Components](#step-1-core-framework-components)
  - [1.1 Configuration Management](#11-configuration-management)
  - [1.2 The Component Registry](#12-the-component-registry)
  - [1.3 Using the Plugin Registry](#13-using-the-plugin-registry)
- [Step 2: Model Implementations](#step-2-model-implementations)
- [Step 3: Serving Layer](#step-3-serving-layer)
- [Step 4: Containerization](#step-4-containerization)
- [Step 5: Deployment Script](#step-5-deployment-script)
- [Testing the Framework](#testing-the-framework)
- [Production Checklist](#production-checklist)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

By the end of this guide, you will be able to:

- **Assemble** configuration, a component registry, model implementations, and a serving layer into one coherent package — every file complete and runnable.
- **Explain** why a registry turns framework extension into *adding files* instead of *editing files*, and demonstrate it by registering three custom metrics as plugins.
- **Implement** dynamic batching with a timeout flush, and articulate why the flush must run outside `add_request` or single requests starve.
- **Serve** the framework through FastAPI (`/health`, `/predict`, `/stats`) and interpret the stats it reports.
- **Deploy** the service with Docker (non-root user, healthcheck), nginx (DNS-re-resolved upstream), and a health-gated deploy script that rolls back on failure.

## Project Overview

This guide builds a miniature production framework — small enough to hold in your head, structured like the real thing. Every design element here (config file, registry, batching server, health-gated deploy) has a full-scale counterpart in production ML systems; the guide's value is that you will have written each one yourself.

The request path through the finished system:

```text
client ──> nginx :80 ──> api replica(s) :8000 ──> BatchingServer ──> model (PyTorch)
                              │
                        config.yaml + registries decide WHAT runs and HOW
```

The complete file tree — and this time it is honest: every file shown below is built in this guide, and nothing is promised that is not delivered:

```text
framework/
├── core/
│   ├── __init__.py          # empty package markers
│   ├── registry.py          # component registries - the plugin point
│   └── config.py            # YAML config with dot-notation access
├── models/
│   ├── __init__.py
│   ├── base.py              # BaseModel contract: forward + predict_batch
│   ├── simple.py            # SimpleNN MLP, registered
│   └── transformer.py       # TransformerModel encoder, registered
├── serving/
│   ├── __init__.py
│   ├── batching.py          # BatchingServer: collect, flush, dispatch
│   ├── api.py               # FastAPI app
│   └── server.py            # uvicorn entry point
├── plugins.py               # worked example: 3 custom metrics as plugins
├── config.yaml
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── deploy.sh
└── tests/
    └── test_api.py
```

Create the directory structure (the `__init__.py` files are empty markers that make `core`, `models`, and `serving` importable packages):

```bash
mkdir -p framework/{core,models,serving,tests}
touch framework/core/__init__.py framework/models/__init__.py framework/serving/__init__.py
cd framework
```

All commands below run from inside `framework/`, so imports like `from core.registry import MODEL_REGISTRY` resolve.

## Step 1: Core Framework Components

### 1.1 Configuration Management

Production systems are configured, not edited. The `Config` class loads one YAML file and exposes nested values with dot notation; a CLI flag or environment variable can override any subtree via a deep merge.

```python
# core/config.py
"""YAML-backed configuration with dot-notation access and defaults merging."""
import copy
from typing import Any

import yaml


class Config:
    """Reads a YAML file and exposes nested values via dot notation.

    config.get("serving.batch_timeout_ms", default=10) walks the nested
    dict; a missing key returns the default (or raises when required=True),
    so callers state their fallback explicitly instead of sprinkling
    None-checks through the code.
    """

    def __init__(self, path: str | None = None, overrides: dict[str, Any] | None = None):
        self._data: dict[str, Any] = {}
        if path is not None:
            with open(path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        if overrides:
            self._deep_merge(self._data, overrides)

    @staticmethod
    def _deep_merge(base: dict[str, Any], extra: dict[str, Any]) -> None:
        """Merge `extra` into `base` recursively - dict values merge, the rest replace."""
        for key, value in extra.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, dotted: str, default: Any = None, required: bool = False) -> Any:
        node: Any = self._data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                if required:
                    raise KeyError(f"missing required config key: {dotted}")
                return default
            node = node[part]
        return node

    def as_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self._data)

    def __repr__(self) -> str:
        return f"Config({self._data!r})"
```

Two deliberate choices worth noticing: `yaml.safe_load` (never `yaml.load`, which can execute arbitrary objects from the file) and `deepcopy` on `as_dict` (callers cannot mutate the live config through a borrowed reference).

### 1.2 The Component Registry

The registry is the framework's extension point. Components register under their class name; configuration selects them by name. The core code never imports a concrete model — it asks the registry.

```python
# core/registry.py
"""Component registries: the plugin point of the framework.

Components register by class name; config files select them by name, so
new behavior ships as a NEW file instead of an edited one.
"""



class Registry:
    """Maps string names to classes. `register` doubles as a decorator."""

    def __init__(self, name: str):
        self.name = name
        self._entries: dict[str, type] = {}

    def register(self, cls: type) -> type:
        key = cls.__name__
        if key in self._entries:
            raise ValueError(f"{self.name}: duplicate registration for '{key}'")
        self._entries[key] = cls
        return cls  # returning the class makes @REGISTRY.register work as a decorator

    def create(self, key: str, *args, **kwargs):
        if key not in self._entries:
            raise KeyError(
                f"{self.name}: unknown component '{key}' (registered: {self.list_all()})"
            )
        return self._entries[key](*args, **kwargs)

    def list_all(self) -> list[str]:
        return sorted(self._entries)

    def __contains__(self, key: object) -> bool:
        return key in self._entries


# The framework's two extension points, as module-level singletons.
MODEL_REGISTRY = Registry("models")
METRIC_REGISTRY = Registry("metrics")
```

One honest correction to a common tutorial mistake: the imports at the top must cover everything used in the file. `predict_batch`'s `Any` annotation only works because `Any` is imported from `typing` — forgetting it is a `NameError` at *import time*, before any of your code runs. (Built-in generics like `list[str]` are the exception — they need no import on Python 3.9+.) Import errors from missing annotation imports are the most common first-run failure in framework-style code, and the fix is always the same shape.

### 1.3 Using the Plugin Registry

"Extend without editing" deserves proof, not assertion. `plugins.py` adds three custom metrics to `METRIC_REGISTRY` without touching any core file — exactly how a third-party plugin would:

```python
# plugins.py - extension as a dropped-in file: no core edits required
from core.registry import METRIC_REGISTRY


@METRIC_REGISTRY.register
class Accuracy:
    """Fraction of exact class matches."""

    def __call__(self, y_true: list, y_pred: list) -> float:
        correct = sum(t == p for t, p in zip(y_true, y_pred))
        return correct / max(len(y_true), 1)


@METRIC_REGISTRY.register
class MeanLatency:
    """Mean of per-request latencies (seconds)."""

    def __call__(self, latencies: list) -> float:
        return sum(latencies) / max(len(latencies), 1)


@METRIC_REGISTRY.register
class Throughput:
    """Requests per second over a measured window."""

    def __call__(self, n_requests: int, seconds: float) -> float:
        return n_requests / seconds if seconds > 0 else 0.0


if __name__ == "__main__":
    # Configuration selects plugins by name - the same registry the models use:
    #   metrics: [Accuracy, Throughput]
    print(METRIC_REGISTRY.list_all())
    accuracy = METRIC_REGISTRY.create("Accuracy")
    print(accuracy([1, 0, 1, 1], [1, 1, 1, 0]))  # -> 0.5
```

Run it: `python plugins.py`. Deleting `plugins.py` removes the three metrics; adding a new file adds more. That asymmetry — files in, files out, core untouched — is the entire argument for registries.

## Step 2: Model Implementations

`BaseModel` defines the contract: subclasses implement `forward()`, and the serving layer calls `predict_batch()`. Providing a *default* `predict_batch` is the framework's leverage — most models inherit tensorization and inference-mode handling for free and override only when their input is not a float matrix.

```python
# models/base.py
"""BaseModel: the contract every registered model fulfills."""
from abc import ABC, abstractmethod
from typing import Any

import torch
import torch.nn as nn

from core.registry import MODEL_REGISTRY  # noqa: F401  (re-exported for convenience)


class BaseModel(nn.Module, ABC):
    """Subclasses implement forward(); serving calls predict_batch().

    The default predict_batch converts raw Python inputs to a float tensor,
    runs ONE batched forward pass under no_grad, and returns plain lists -
    JSON-safe values the API layer can return directly. Override it only
    when your input is not a float matrix (see TransformerModel).
    """

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor: ...

    def eval(self) -> "BaseModel":
        # nn.Module.eval() already returns self; re-declaring just gives
        # serving code a correctly-typed call site. Keep the contract uniform.
        return super().eval()

    def predict_batch(self, inputs: list[Any]) -> list[list[float]]:
        was_training = self.training
        self.eval()  # no dropout / batchnorm updates during inference
        try:
            with torch.no_grad():  # skip autograd bookkeeping: faster, less memory
                tensor = torch.as_tensor(inputs, dtype=torch.float32)
                if tensor.ndim == 1:  # a single flat vector arrived unsqueezed
                    tensor = tensor.unsqueeze(0)
                outputs = self(tensor)
        finally:
            if was_training:
                self.train()
        return outputs.detach().cpu().tolist()
```

The first concrete model — a small MLP. Note that `training_step` lives with the model: the loss function is part of what the model *is*, not part of the serving layer.

```python
# models/simple.py
import torch
import torch.nn as nn

from core.registry import MODEL_REGISTRY
from models.base import BaseModel


@MODEL_REGISTRY.register
class SimpleNN(BaseModel):
    """Two-layer MLP for fixed-size float vectors: 3 features -> 10 logits."""

    def __init__(self, input_size: int = 3, hidden_size: int = 16, num_classes: int = 10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def training_step(self, batch) -> torch.Tensor:
        x, y = batch
        return nn.functional.cross_entropy(self(x), y)
```

The second model overrides `predict_batch` — its input is integer token ids, not floats, so the default tensorization is wrong for it:

```python
# models/transformer.py
import math


import torch
import torch.nn as nn

from core.registry import MODEL_REGISTRY
from models.base import BaseModel


@MODEL_REGISTRY.register
class TransformerModel(BaseModel):
    """A miniature next-token predictor: byte-level vocab, 2 encoder layers.

    Sized (d_model 128, 4 heads, FFN 512) to train on CPU in seconds while
    keeping the exact shape of problem a production LLM poses.
    """

    def __init__(
        self,
        vocab_size: int = 256,
        d_model: int = 128,
        nhead: int = 4,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos_embed = nn.Embedding(512, d_model)  # learned positions, max len 512
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,  # (batch, seq, feature) in/out - not (seq, batch, feature)
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.lm_head = nn.Linear(d_model, vocab_size)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        positions = torch.arange(token_ids.size(1), device=token_ids.device).unsqueeze(0)
        x = self.embed(token_ids) * math.sqrt(self.d_model) + self.pos_embed(positions)
        return self.lm_head(self.encoder(x))

    def training_step(self, token_ids: torch.Tensor) -> torch.Tensor:
        """Next-token prediction: inputs shifted by one against the targets."""
        logits = self(token_ids[:, :-1])
        targets = token_ids[:, 1:]
        return nn.functional.cross_entropy(
            logits.reshape(-1, logits.size(-1)), targets.reshape(-1)
        )

    def predict_batch(self, inputs: list[list[int]]) -> list[list[int]]:
        """Greedy next-token id per sequence. Override: ids in, one id out."""
        was_training = self.training
        self.eval()
        try:
            with torch.no_grad():
                tensor = torch.as_tensor(inputs, dtype=torch.long)
                logits = self(tensor)[:, -1, :]  # last position predicts the next token
        finally:
            if was_training:
                self.train()
        return logits.argmax(dim=-1).unsqueeze(-1).cpu().tolist()
```

Both modules call `@MODEL_REGISTRY.register` at import time — which is why [Step 3](#step-3-serving-layer) imports them with `# noqa: F401`: the import's *side effect* is the registration, the binding is unused.

## Step 3: Serving Layer

The batching server collects concurrent requests and runs them as one forward pass — the single highest-leverage latency/throughput trick in GPU serving. The critical detail is *when* a partial batch is flushed: when full, **or** when the oldest queued request has waited longer than the timeout. And the flush must be reachable from the *waiter*, not only from new arrivals — otherwise a lone request nobody follows sits in the queue until its client gives up.

```python
# serving/batching.py
"""Dynamic batching: collect concurrent requests, run them as one forward pass."""
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from models.base import BaseModel  # noqa: F401  (type reference)


class BatchTimeoutError(TimeoutError):
    """Raised to the waiting caller; the API layer maps it to HTTP 504."""


@dataclass
class BatchItem:
    """One in-flight request. `input` is a LIST of feature rows."""

    input: list[Any]
    enqueued_at: float = 0.0
    event: threading.Event = field(default_factory=threading.Event)
    result: list[Any] = field(default_factory=list)
    error: Exception | None = None


class BatchingServer:
    """Batches requests up to max_batch_size, flushing on timeout too.

    The flush runs from BOTH entry points:
    - add_request: a fresh arrival may complete a full batch immediately
    - get_result:  the WAITER keeps flushing while it waits, so a lone
      request is processed once timeout_ms passes instead of starving
    """

    def __init__(self, model: BaseModel, max_batch_size: int = 8, timeout_ms: float = 10.0):
        self.model = model
        self.max_batch_size = max_batch_size
        self.timeout_ms = timeout_ms
        self._queue: list[BatchItem] = []
        self._lock = threading.Lock()
        self.stats = {"requests": 0, "batches": 0, "batch_sizes": []}

    def add_request(self, item: BatchItem) -> None:
        item.enqueued_at = time.monotonic()  # monotonic: immune to wall-clock jumps
        with self._lock:
            self._queue.append(item)
            self.stats["requests"] += 1
            self._check_and_process()

    def get_result(self, item: BatchItem, timeout_s: float = 5.0) -> list[Any]:
        deadline = time.monotonic() + timeout_s
        while not item.event.wait(0.05):  # poll in 50ms slices; cheap and simple
            self._check_and_process()  # <- the timeout flush, driven by the waiter
            if time.monotonic() > deadline:
                with self._lock:
                    if item in self._queue:
                        self._queue.remove(item)
                raise BatchTimeoutError(f"no batch result within {timeout_s}s")
        if item.error is not None:
            raise item.error
        return item.result

    def _check_and_process(self) -> None:
        """Process a batch when full OR when the oldest item aged past timeout_ms."""
        if not self._queue:
            return
        oldest_age_ms = (time.monotonic() - self._queue[0].enqueued_at) * 1000
        if len(self._queue) < self.max_batch_size and oldest_age_ms < self.timeout_ms:
            return  # keep collecting: batch not full, nothing stale yet
        batch, self._queue = self._queue[: self.max_batch_size], self._queue[self.max_batch_size :]
        self._process(batch)

    def _process(self, batch: list[BatchItem]) -> None:
        self.stats["batches"] += 1
        self.stats["batch_sizes"].append(len(batch))
        try:
            rows = [row for item in batch for row in item.input]  # flatten to one tensor
            outputs = self.model.predict_batch(rows)
            pos = 0
            for item in batch:  # split results back by each item's row count
                item.result = outputs[pos : pos + len(item.input)]
                pos += len(item.input)
                item.event.set()
        except Exception as exc:  # fail every request in the broken batch, loudly
            for item in batch:
                item.error = exc
                item.event.set()
```

The API layer wires config → registry → batching → HTTP. Every failure mode gets a deliberate status: empty payload is `400`, a blown batch deadline is `504` (the server's upstream inference, not the client, took too long).

```python
# serving/api.py
"""FastAPI app: config -> registry -> batching -> HTTP.

Run from the framework/ directory: uvicorn serving.api:app --port 8000
"""
import os
import time


import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel  # Pydantic's BaseModel - NOT models.base.BaseModel

from core.config import Config
from core.registry import MODEL_REGISTRY
from models.simple import SimpleNN  # noqa: F401  (import = registration)
from models.transformer import TransformerModel  # noqa: F401  (import = registration)
from serving.batching import BatchItem, BatchTimeoutError, BatchingServer

CONFIG = Config(path=os.environ.get("FRAMEWORK_CONFIG", "config.yaml"))
MODEL = MODEL_REGISTRY.create(CONFIG.get("serving.model_name", default="SimpleNN"))
# create() passes no kwargs, so the class's defaults apply; the `model:` block
# in config.yaml documents those defaults for operators.

# Optional: restore trained weights saved by a training script.
WEIGHTS = os.environ.get("MODEL_PATH")
if WEIGHTS and os.path.exists(WEIGHTS):
    MODEL.load_state_dict(torch.load(WEIGHTS, map_location="cpu"))

MODEL.eval()
SERVER = BatchingServer(
    MODEL,
    max_batch_size=CONFIG.get("serving.max_batch_size", default=8),
    timeout_ms=CONFIG.get("serving.batch_timeout_ms", default=10.0),
)

app = FastAPI(title="Mini Framework API")


class PredictRequest(BaseModel):
    inputs: list[list[float]]  # rows of feature floats, one inference per row


class PredictResponse(BaseModel):
    predictions: list[list[float]]
    processing_time_ms: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": type(MODEL).__name__}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    if not req.inputs:
        raise HTTPException(status_code=400, detail="inputs must contain at least one row")
    started = time.perf_counter()  # monotonic, high-resolution: the right clock here
    item = BatchItem(input=req.inputs)
    SERVER.add_request(item)
    try:
        result = SERVER.get_result(item)
    except BatchTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    return PredictResponse(
        predictions=result,
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
    )


@app.get("/stats")
def stats() -> dict:
    sizes = SERVER.stats["batch_sizes"]
    return {
        "requests": SERVER.stats["requests"],
        "batches": SERVER.stats["batches"],
        "avg_batch_size": (sum(sizes) / len(sizes)) if sizes else 0.0,
    }
```

The configuration file both server entry points read:

```yaml
# config.yaml - operators change THIS, not the code
model:
  name: SimpleNN      # documents the registered class's defaults below
  input_size: 3
  hidden_size: 16
  num_classes: 10

serving:
  model_name: SimpleNN   # key into MODEL_REGISTRY
  max_batch_size: 8
  batch_timeout_ms: 10

api:
  host: 0.0.0.0
  port: 8000
```

And the entry point that reads `api.host`/`api.port` from it:

```python
# serving/server.py
"""Entry point: python -m serving.server  (from the framework/ directory)."""
import uvicorn

from core.config import Config

if __name__ == "__main__":
    config = Config(path="config.yaml")
    uvicorn.run(
        "serving.api:app",
        host=config.get("api.host", default="0.0.0.0"),
        port=config.get("api.port", default=8000),
    )
```

## Step 4: Containerization

Dependencies first — the Dockerfile copies the manifest before the code so the install layer survives code-only rebuilds:

```toml
# pyproject.toml - dependencies recorded by uv add
dependencies = [
    "torch>=2.12",
    "fastapi>=0.141",
    "uvicorn[standard]>=0.52",
    "pydantic>=2.13",
    "PyYAML>=6.0",
]
```

The image: pinned slim base, non-root user, one process:

```dockerfile
# Dockerfile - build from framework/:  docker build -t mini-framework .
FROM python:3.13-slim

WORKDIR /app

# Dependency layer: only manifest/lockfile changes rebuild this.
COPY pyproject.toml uv.lock ./

# Official uv-in-Docker pattern: copy the uv binary from the uv image
# (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . .

# Slim bases have no unprivileged user by default; a container that faces
# traffic should not run as root.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "serving.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Now the composition: **two API replicas behind one nginx**. The replicas publish *no host ports* — `expose` keeps 8000 internal to the compose network, because two replicas both binding host port 8000 is a startup conflict. nginx is the only entry point. The healthcheck uses Python (present in a python image; curl is not), and nginx waits for the API to be *healthy*, not merely *started*:

```yaml
# docker-compose.yml - replicas behind one nginx entry point
services:
  api:
    build: .
    expose:
      - "8000"        # internal only - nginx owns the host port
    environment:
      FRAMEWORK_CONFIG: /app/config.yaml
    deploy:
      replicas: 2
    healthcheck:
      # python:3.13-slim has python, not curl
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 15s   # model import + first forward pass take a moment

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      api:
        condition: service_healthy   # route traffic only to READY replicas
```

The nginx config carries the one genuinely non-obvious production lesson in this guide. With `deploy.replicas`, the name `api` resolves to *multiple* containers through Docker's embedded DNS — but nginx resolves static upstream entries **once at startup** and would pin all traffic to one replica. Pointing `proxy_pass` through a *variable* forces nginx to re-resolve per request via the resolver:

```nginx
# nginx.conf - balance across the `api` replicas
events {}

http {
    # Docker's embedded DNS. Re-resolving `api` per request is what makes
    # deploy.replicas actually balance: a static `upstream api { server api:8000; }`
    # block pins ONE resolved IP at config-load time and every request to it.
    resolver 127.0.0.11 valid=10s ipv6=off;

    server {
        listen 80;

        location / {
            set $api_upstream http://api:8000;
            proxy_pass $api_upstream;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## Step 5: Deployment Script

The script encodes the rollout discipline: build, **prove the app can even import**, compose up, gate on health, roll back on failure. Note the smoke test deliberately is *not* `pytest` — in a repo without collected tests pytest exits with code 5, which under `set -e` kills the script before the deploy it was supposed to precede.

```bash
#!/usr/bin/env bash
# deploy.sh - build, smoke-test, roll out with a health gate, roll back on failure.
set -euo pipefail

cd "$(dirname "$0")"

IMAGE="${1:-mini-framework:latest}"

echo "==> building ${IMAGE}"
docker build -t "${IMAGE}" .

echo "==> import smoke test (a container that cannot import cannot serve)"
docker run --rm "${IMAGE}" python -c "from serving.api import app; print('app routes:', len(app.routes))"
# Deliberately not `pytest`: an empty test collection exits 5 and, under
# set -e, would abort the rollout. The smoke test checks the real invariant.

echo "==> compose up (nginx waits for healthy replicas)"
docker compose up -d --build

echo "==> waiting for nginx (30 x 2s)"
for _ in $(seq 1 30); do
  if curl -fsS http://localhost/health > /dev/null; then
    echo "==> healthy"
    docker compose ps
    exit 0
  fi
  sleep 2
done

echo "==> FAILED: nginx never became healthy; rolling back" >&2
docker compose down
exit 1
```

Run it: `bash deploy.sh` (or `bash deploy.sh myregistry/mini-framework:v1` to tag the image). Requires Docker with the compose v2 plugin (`docker compose version` to check).

## Testing the Framework

pytest is deliberately absent from the runtime dependencies (test dependencies do not belong in the runtime image); install it separately to run these:

```python
# tests/test_api.py
from fastapi.testclient import TestClient

from serving.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_predict_shape():
    r = client.post("/predict", json={"inputs": [[0.1, 0.2, 0.3]]})
    assert r.status_code == 200
    body = r.json()
    assert len(body["predictions"][0]) == 10  # SimpleNN's default num_classes
    assert body["processing_time_ms"] >= 0


def test_predict_rejects_empty():
    r = client.post("/predict", json={"inputs": []})
    assert r.status_code == 400


def test_stats_counters_monotonic():
    before = client.get("/stats").json()["requests"]
    client.post("/predict", json={"inputs": [[0.5, 0.5, 0.5]]})
    after = client.get("/stats").json()["requests"]
    assert after == before + 1
```

### Expected Output

With `torch.manual_seed(0)` set before `serving.api` is imported (fixing the random weight init), a captured run of health → one `/predict` with `[[0.1, 0.2, 0.3]]` → `/stats`:

```json
{
  "health": {"status": "ok", "model": "SimpleNN"},
  "predict": {
    "predictions_head": [-0.2346590757369995, 0.11812016367912292, -0.34932464361190796],
    "note": "3 of 10 logits shown - untrained weights, so the values are noise by design",
    "processing_time_ms": 50.316
  },
  "stats": {"requests": 1, "batches": 1, "avg_batch_size": 1.0}
}
```

What varies and why, so the output stays interpretable: the logit values change with the random init (drop the seed line and every number differs — the *shape*, 10 logits per row, is the invariant); `processing_time_ms` includes the batch timeout floor of 10 ms plus interpreter noise, so anything from ~12 ms up is normal; and `avg_batch_size` climbs toward `max_batch_size` only under concurrent traffic — sequential requests each form their own batch of 1, flushed by the timeout, exactly the starvation-free behavior [Step 3](#step-3-serving-layer) guarantees.

## Production Checklist

Everything below is *done in this guide* — each item maps to a section you can reread:

- **Configuration is external**: one YAML file, dot-notation reads, env-var override point (`FRAMEWORK_CONFIG`). [Step 1.1](#11-configuration-management)
- **Extension is additive**: registries + decorators; three custom metrics shipped as a pure plugin file. [Steps 1.2–1.3](#12-the-component-registry)
- **Models share a contract**: `forward` + a default `predict_batch` with override points. [Step 2](#step-2-model-implementations)
- **Batching has no starvation window**: flush on full *and* on timeout, driven from the waiter too. [Step 3](#step-3-serving-layer)
- **API contract is explicit**: typed request/response, timing header-grade metric, 400/504 semantics, `/health` + `/stats`. [Step 3](#step-3-serving-layer)
- **Image is boring on purpose**: pinned slim base, cached dependency layer, non-root user. [Step 4](#step-4-containerization)
- **Replicas actually load-balance**: internal-only ports + DNS re-resolution in nginx. [Step 4](#step-4-containerization)
- **Rollout is gated**: import smoke test → health-gated compose up → automatic rollback. [Step 5](#step-5-deployment-script)

What a real framework would add beyond this guide's scope: authentication and rate limiting ([2303: API Design for ML Systems](../2303-API-Design-for-ML.md)), metrics export and tracing, blue-green or canary rollout strategies ([2304: Production Deployment Patterns](../2304-Production-Deployment-Patterns.md)), and multi-GPU scheduling.

## Summary

**A production framework is four mechanisms wearing one coat**: external configuration, a registry for additive extension, a model contract with a default inference path, and a serving layer whose failure modes have named status codes.

- Config over edits: `Config` + YAML means operators change behavior without touching code, and `safe_load` keeps the config file non-executable.
- The registry makes extension a file operation — `plugins.py` added three metrics with zero core changes, and deletion is equally clean.
- `predict_batch` as a *default* method is the leverage point: `SimpleNN` inherited inference handling; `TransformerModel` overrode only the tensorization.
- Batching must flush on timeout *from the waiter* — a flush reachable only from new arrivals starves the lone request.
- Containers and the rollout script encode discipline: non-root, healthchecks with `start_period`, DNS re-resolution for replicas, health-gated deploy with rollback.

## References

### Related Documents

- [Phase 2: Module 2300 - Framework Engineering](../README.md)
- [2301: Framework Design Patterns](../2301-Framework-Design-Patterns.md)
- [2302: Model Serving Architectures](../2302-Model-Serving-Architectures.md)
- [2304: Production Deployment Patterns](../2304-Production-Deployment-Patterns.md)
- [2305: Framework Comparison Guide](./2305-Framework-Comparison.md)

### External References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [torch.nn.TransformerEncoder - PyTorch](https://pytorch.org/docs/stable/generated/torch.nn.TransformerEncoder.html)
- [Compose file reference: `deploy` (replicas, healthcheck semantics)](https://docs.docker.com/reference/compose-file/deploy/)
- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [nginx ngx_http_upstream_module](http://nginx.org/en/docs/http/ngx_http_upstream_module.html)

## Next Steps

- **Assessment:** [2300: Framework Engineering - Quiz](../assessment/QUIZ.md)
- **Practical:** [LAB-009: Production Deployment](../../../../learning-resources/labs/LAB-009-Production-Deployment.md) — take these deployment patterns to a real service.
- **Next Module:** [2400: LLM Pretraining](../../2400-pretraining/README.md) — the training side of the systems you just learned to serve.

**Related:** [2305: Framework Comparison Guide](./2305-Framework-Comparison.md) · [1402: vLLM and TGI High-Concurrency Inference](../../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) · [6101: HNSW Indexing - Efficient Semantic Search at Scale](../../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)

**Experiment:** [EXP_1404: vLLM Production Tuning Experiments](../../../../../experiments/EXP_1404_VLLM_TUNING.md) — see how a full-scale serving framework tunes the batching you just hand-rolled.
