---
Document ID: 2306
Title: "2306: Building a Production Framework"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
---

# 2306: Building a Production Framework

**Project:** AI Engineering Curriculum
**Phase:** [2300] Framework Engineering
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 3 hours

---

## Abstract

This hands-on guide walks you through building a complete mini ML framework from scratch. You'll implement all the patterns covered in this module: model abstraction, configuration management, plugins, serving, and deployment.

**What you'll build:**

```text
mini-ml-framework/
├── core/
│   ├── __init__.py
│   ├── base.py          # BaseModel abstraction
│   ├── config.py        # Configuration management
│   └── registry.py      # Plugin registry
├── models/
│   ├── __init__.py
│   ├── simple.py        # Simple neural network
│   └── transformer.py   # Transformer model
├── serving/
│   ├── __init__.py
│   ├── server.py        # Batch serving
│   └── api.py           # REST API
├── plugins/
│   ├── __init__.py
│   ├── metrics.py       # Custom metrics
│   └── optimizers.py    # Custom optimizers
└── examples/
    ├── train.py
    ├── serve.py
    └── deploy.sh
```

---

## Step 1: Core Framework (30 minutes)

### 1.1 Model Abstraction

Create `core/base.py`:

```python
"""
Core framework - Model abstraction layer
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import torch
import torch.nn as nn
from pathlib import Path
import json


class BaseModel(ABC):
    """
    Abstract base class for all models.

    Provides unified interface for:
    - Forward pass
    - Training step
    - Save/load
    - Device management
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None

    @abstractmethod
    def build_model(self) -> nn.Module:
        """Build the model architecture."""
        pass

    @abstractmethod
    def forward(self, x: Any) -> Any:
        """Forward pass."""
        pass

    @abstractmethod
    def training_step(self, batch: Dict[str, Any]) -> Dict[str, float]:
        """
        Single training step.

        Returns:
            Dictionary with 'loss' and metrics
        """
        pass

    def setup(self):
        """Setup model and move to device."""
        if self.model is None:
            self.model = self.build_model()
        self.model.to(self.device)

    def save(self, path: str):
        """Save model checkpoint."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "config": self.config,
            "state_dict": self.model.state_dict(),
        }

        torch.save(checkpoint, path)
        print(f"Model saved to {path}")

    def load(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)

        if self.model is None:
            self.setup()

        self.model.load_state_dict(checkpoint["state_dict"])
        print(f"Model loaded from {path}")

    def to(self, device: str):
        """Move model to device."""
        self.device = torch.device(device)
        if self.model is not None:
            self.model.to(self.device)
```

### 1.2 Configuration Management

Create `core/config.py`:

```python
"""
Core framework - Configuration management
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, List
import yaml
import json
from pathlib import Path


@dataclass
class ModelConfig:
    """
    Model configuration with validation and serialization.

    Features:
    - Type validation
    - Default values
    - YAML/JSON save/load
    - Validation on load
    """

    # Model architecture
    input_size: int
    hidden_size: int = 256
    num_layers: int = 3
    output_size: int = 10
    dropout: float = 0.1

    # Training
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10

    # Optional
    seed: Optional[int] = None
    mixed_precision: bool = False

    def __post_init__(self):
        """Validate configuration."""
        if self.hidden_size <= 0:
            raise ValueError(f"hidden_size must be positive, got {self.hidden_size}")
        if not 0 <= self.dropout <= 1:
            raise ValueError(f"dropout must be in [0, 1], got {self.dropout}")

    @classmethod
    def from_yaml(cls, path: str) -> "ModelConfig":
        """Load from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str):
        """Save to YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(asdict(self), f, default_flow_style=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        """Create from dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
```

### 1.3 Plugin Registry

Create `core/registry.py`:

```python
"""
Core framework - Plugin registry system
"""
from typing import Dict, Type, Optional, Any
import inspect


class PluginRegistry:
    """
    Registry for managing plugins.

    Supports:
    - Decorator registration
    - Dynamic loading
    - Plugin discovery
    - Metadata management
    """

    def __init__(self, name: str):
        self.name = name
        self._plugins: Dict[str, Type] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: Optional[str] = None,
        **metadata
    ):
        """
        Decorator for registering plugins.

        Usage:
            @registry.register("my_plugin", version="1.0")
            class MyPlugin:
                pass
        """
        def decorator(plugin_class: Type) -> Type:
            plugin_name = name or plugin_class.__name__

            if plugin_name in self._plugins:
                raise ValueError(f"Plugin '{plugin_name}' already registered")

            self._plugins[plugin_name] = plugin_class
            self._metadata[plugin_name] = metadata

            return plugin_class

        return decorator

    def get(self, name: str) -> Optional[Type]:
        """Get plugin class by name."""
        return self._plugins.get(name)

    def create(self, name: str, *args, **kwargs):
        """Create plugin instance."""
        plugin_class = self.get(name)
        if plugin_class is None:
            raise ValueError(f"Plugin '{name}' not found")
        return plugin_class(*args, **kwargs)

    def list_all(self) -> List[str]:
        """List all registered plugins."""
        return list(self._plugins.keys())

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get plugin metadata."""
        return self._metadata.get(name, {})


# Global registries
LAYER_REGISTRY = PluginRegistry("layers")
METRIC_REGISTRY = PluginRegistry("metrics")
OPTIMIZER_REGISTRY = PluginRegistry("optimizers")
```

---

## Step 2: Model Implementations (45 minutes)

### 2.1 Simple Neural Network

Create `models/simple.py`:

```python
"""
Simple neural network model implementation
"""
import torch
import torch.nn as nn
from core.base import BaseModel
from core.config import ModelConfig


class SimpleNN(BaseModel):
    """Simple feedforward neural network."""

    def build_model(self) -> nn.Module:
        """Build model from config."""
        layers = []
        input_size = self.config["input_size"]
        hidden_size = self.config["hidden_size"]
        num_layers = self.config["num_layers"]
        output_size = self.config["output_size"]
        dropout = self.config["dropout"]

        # Hidden layers
        for i in range(num_layers):
            layers.append(nn.Linear(input_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            input_size = hidden_size

        # Output layer
        layers.append(nn.Linear(hidden_size, output_size))

        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.model(x)

    def training_step(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Single training step."""
        inputs = batch["inputs"].to(self.device)
        targets = batch["targets"].to(self.device)

        # Forward
        outputs = self.forward(inputs)

        # Loss
        loss_fn = nn.MSELoss()
        loss = loss_fn(outputs, targets)

        return {"loss": loss}
```

### 2.2 Transformer Model

Create `models/transformer.py`:

```python
"""
Transformer model implementation
"""
import torch
import torch.nn as nn
from core.base import BaseModel


class TransformerModel(BaseModel):
    """Simple transformer model."""

    def build_model(self) -> nn.Module:
        """Build transformer from config."""
        vocab_size = self.config.get("vocab_size", 10000)
        d_model = self.config["hidden_size"]
        nhead = self.config.get("nhead", 8)
        num_layers = self.config["num_layers"]
        dim_feedforward = self.config.get("dim_feedforward", 2048)
        dropout = self.config["dropout"]

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )

        return nn.Sequential(
            nn.Embedding(vocab_size, d_model),
            nn.TransformerEncoder(encoder_layer, num_layers=num_layers),
            nn.Linear(d_model, vocab_size)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.model(x)

    def training_step(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Training step."""
        inputs = batch["inputs"].to(self.device)
        targets = batch["targets"].to(self.device)

        outputs = self.forward(inputs)

        loss_fn = nn.CrossEntropyLoss(ignore_index=0)
        loss = loss_fn(outputs.view(-1, outputs.size(-1)), targets.view(-1))

        return {"loss": loss}
```

---

## Step 3: Serving Layer (30 minutes)

### 3.1 Batch Serving Server

Create `serving/server.py`:

```python
"""
Batch serving server for ML models
"""
import time
import threading
import uuid
from typing import Dict, Any, List
from collections import defaultdict


class BatchingServer:
    """
    Server with dynamic request batching.

    Features:
    - Time-based batching
    - Size-based batching
    - Result tracking
    - Statistics
    """

    def __init__(
        self,
        model,
        max_batch_size: int = 32,
        timeout_ms: int = 50
    ):
        self.model = model
        self.max_batch_size = max_batch_size
        self.timeout_ms = timeout_ms

        self.pending: List[Dict] = []
        self.results: Dict[str, Any] = {}
        self.lock = threading.Lock()

        self.stats = {
            "total_requests": 0,
            "batches_processed": 0,
            "avg_batch_size": 0.0,
        }

    def add_request(self, input_data: Any) -> str:
        """Add request to batch queue."""
        request_id = str(uuid.uuid4())

        with self.lock:
            self.pending.append({
                "id": request_id,
                "input": input_data,
                "timestamp": time.time()
            })
            self.stats["total_requests"] += 1

            self._check_and_process()

        return request_id

    def get_result(self, request_id: str, timeout: float = 5.0):
        """Wait for and return result."""
        start = time.time()

        while time.time() - start < timeout:
            with self.lock:
                if request_id in self.results:
                    result = self.results.pop(request_id)
                    return result
            time.sleep(0.001)

        raise TimeoutError(f"Request {request_id} timed out")

    def _check_and_process(self):
        """Check if we should process batch."""
        if not self.pending:
            return

        # Check if batch is full
        if len(self.pending) >= self.max_batch_size:
            self._process_batch()
            return

        # Check timeout
        oldest = self.pending[0]
        if (time.time() - oldest["timestamp"]) * 1000 >= self.timeout_ms:
            self._process_batch()

    def _process_batch(self):
        """Process current batch."""
        if not self.pending:
            return

        # Get batch
        batch = self.pending[:self.max_batch_size]
        self.pending = self.pending[len(batch):]

        # Prepare inputs
        inputs = [item["input"] for item in batch]

        # Run inference
        outputs = self.model.predict_batch(inputs)

        # Store results
        for item, output in zip(batch, outputs):
            self.results[item["id"]] = output

        # Update stats
        self.stats["batches_processed"] += 1
        self.stats["avg_batch_size"] = (
            (self.stats["avg_batch_size"] * (self.stats["batches_processed"] - 1) + len(batch)) /
            self.stats["batches_processed"]
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            **self.stats,
            "pending": len(self.pending),
            "cached": len(self.results),
        }
```

---

## Step 4: REST API (30 minutes)

### 4.1 FastAPI Application

Create `serving/api.py`:

```python
"""
REST API for ML model serving
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import torch

from models.simple import SimpleNN
from models.transformer import TransformerModel
from core.config import ModelConfig
from serving.server import BatchingServer


# Request/Response models
class PredictRequest(BaseModel):
    inputs: List[float]
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PredictResponse(BaseModel):
    predictions: List[float]
    model_version: str
    processing_time_ms: float


# Initialize app
app = FastAPI(title="Mini ML Framework API")

# Load model
config = ModelConfig(
    input_size=784,
    hidden_size=256,
    num_layers=3,
    output_size=10
)

model = SimpleNN(config.to_dict())
model.setup()
model.eval()

# Create batching server
server = BatchingServer(model, max_batch_size=32, timeout_ms=50)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": True
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """Make prediction."""
    import time
    start = time.time()

    # Add to batch
    request_id = server.add_request(request.inputs)

    # Get result
    result = server.get_result(request_id)

    return PredictResponse(
        predictions=result,
        model_version="1.0",
        processing_time_ms=(time.time() - start) * 1000
    )


@app.get("/stats")
async def get_stats():
    """Get server statistics."""
    return server.get_stats()
```

---

## Step 5: Deployment (30 minutes)

### 5.1 Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Expose port
EXPOSE 8000

# Run API
CMD ["uvicorn", "serving.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MODEL_PATH=/models/model.pt
    volumes:
      - ./models:/models
    deploy:
      replicas: 2

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
```

### 5.3 Deployment Script

Create `examples/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "=== Deploying Mini ML Framework ==="

# Build
echo "Building Docker image..."
docker build -t mini-ml-framework .

# Test
echo "Running tests..."
docker run mini-ml-framework pytest

# Deploy
echo "Deploying..."
docker-compose up -d

# Health check
echo "Checking health..."
sleep 10
curl http://localhost/health

echo "=== Deployment complete! ==="
```

---

## Complete Exercise

Now combine everything into a working framework!

### Task Checklist

- [ ] Create `core/` module with base, config, registry
- [ ] Implement `SimpleNN` model
- [ ] Implement `TransformerModel` model
- [ ] Create batching server
- [ ] Build REST API with FastAPI
- [ ] Add 3 custom metrics as plugins
- [ ] Create Dockerfile
- [ ] Deploy with Docker Compose

### Testing Your Framework

```bash
# 1. Install dependencies
pip install torch fastapi uvicorn pydantic pytest

# 2. Test model creation
python examples/train.py

# 3. Test serving
python examples/serve.py

# 4. Test API
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"inputs": [1.0, 2.0, 3.0]}'

# 5. Test deployment
./examples/deploy.sh
```

---

## Extension Challenges

Once you have the basics working:

1. **Add Model Versioning**
   - Track model versions
   - A/B testing support
   - Gradual rollout

2. **Add Caching**
   - Response cache
   - Embedding cache
   - LRU eviction

3. **Add Monitoring**
   - Prometheus metrics
   - Performance tracking
   - Error logging

4. **Add Authentication**
   - JWT tokens
   - API keys
   - Rate limiting per user

---

## Solution Reference

For complete implementation of all components, see the repository.

---

**Congratulations!** You've built a production ML framework from scratch. 🎉


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 3 hours
