# 2300: Framework Engineering - Prerequisites

## Before You Start

This module assumes you have knowledge of:
- **Object-Oriented Programming** - Classes, inheritance, abstraction
- **Python Design Patterns** - Strategy, Factory, Observer patterns
- **Basic ML Concepts** - Training, inference, model evaluation
- **REST APIs** - HTTP methods, status codes, JSON
- **Docker** - Containers, images, basic commands

---

## Required Knowledge

### 1. Object-Oriented Programming in Python

**What you should know:**
- Classes and inheritance
- Abstract base classes (ABC)
- Decorators
- Context managers
- Type hints

**Example: Abstract Base Class**

```python
from abc import ABC, abstractmethod
from typing import List, Any

class Model(ABC):
    """Abstract base class for models."""

    @abstractmethod
    def forward(self, x: Any) -> Any:
        """Forward pass."""
        pass

    @abstractmethod
    def train_step(self, batch: dict) -> dict:
        """Training step."""
        pass

class MyModel(Model):
    """Concrete implementation."""

    def forward(self, x: Any) -> Any:
        return x * 2

    def train_step(self, batch: dict) -> dict:
        return {"loss": 0.5}
```

**If you're not familiar:**
- Review: [Python OOP Tutorial](https://docs.python.org/3/tutorial/classes.html)
- Practice: Create abstract base class with 2 implementations
- Estimated time: 2 hours

---

### 2. Design Patterns

**What you should know:**
- **Strategy Pattern** - Runtime algorithm selection
- **Factory Pattern** - Object creation encapsulation
- **Observer Pattern** - Event-driven callbacks
- **Registry Pattern** - Component discovery

**Example: Strategy Pattern**

```python
from abc import ABC, abstractmethod

class OptimizationStrategy(ABC):
    @abstractmethod
    def optimize(self, params, gradients):
        pass

class AdamStrategy(OptimizationStrategy):
    def optimize(self, params, gradients):
        # Adam optimization
        return updated_params

class SGDStrategy(OptimizationStrategy):
    def optimize(self, params, gradients):
        # SGD optimization
        return updated_params

# Usage
optimizer = AdamStrategy()
updated = optimizer.optimize(params, gradients)
```

**Example: Registry Pattern**

```python
class Registry:
    def __init__(self):
        self._items = {}

    def register(self, name):
        def decorator(cls):
            self._items[name] = cls
            return cls
        return decorator

    def get(self, name):
        return self._items.get(name)

# Usage
registry = Registry()

@registry.register("model1")
class Model1:
    pass

model_class = registry.get("model1")
```

**If you're not familiar:**
- Review: [Refactoring.Guru Patterns](https://refactoring.guru/design-patterns)
- Practice: Implement strategy pattern for model selection
- Estimated time: 3 hours

---

### 3. ML Model Basics

**What you should know:**
- Model training vs inference
- Batch processing
- Model serialization (save/load)
- Model versioning

**Example: PyTorch Model**

```python
import torch
import torch.nn as nn

class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(784, 10)

    def forward(self, x):
        return self.linear(x)

# Training
model = SimpleModel()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

for batch in dataloader:
    optimizer.zero_grad()
    output = model(batch["x"])
    loss = loss_fn(output, batch["y"])
    loss.backward()
    optimizer.step()

# Save
torch.save(model.state_dict(), "model.pt")

# Load
model = SimpleModel()
model.load_state_dict(torch.load("model.pt"))
```

**If you're not familiar:**
- Review: [2201: PyTorch Computational Graphs](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)
- Practice: Train and save a simple model
- Estimated time: 2 hours

---

### 4. REST API Concepts

**What you should know:**
- HTTP methods (GET, POST, PUT, DELETE)
- Status codes (200, 400, 404, 500)
- Request/response format (JSON)
- Authentication basics

**Example: FastAPI**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    prediction: str
    confidence: float

@app.get("/")
async def root():
    return {"message": "ML API"}

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    # Model inference
    result = model.predict(request.text)

    return PredictResponse(
        prediction=result["label"],
        confidence=result["score"]
    )

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**If you're not familiar:**
- Review: [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- Practice: Build a simple API with 3 endpoints
- Estimated time: 2 hours

---

### 5. Docker Fundamentals

**What you should know:**
- Docker images and containers
- Dockerfiles
- Docker Compose
- Volume mounting

**Example: Dockerfile**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Example: Docker Compose**

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MODEL_PATH=/models/mymodel.pt
    volumes:
      - ./models:/models

  redis:
    image: redis:latest
    ports:
      - "6379:6379"
```

**If you're not familiar:**
- Review: [TUTORIAL-002: Docker Essentials](../../../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md)
- Practice: Complete [LAB-001: Docker & LLM](../../../learning-resources/labs/LAB-001-Docker-LLM.md)
- Estimated time: 2 hours

---

### 6. Async Python (Helpful but not required)

**What you should know:**
- async/await syntax
- Event loops
- Concurrent execution

**Example: Async API**

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()

async def process_batch(batch):
    # Simulate async processing
    await asyncio.sleep(0.1)
    return [item * 2 for item in batch]

@app.post("/predict")
async def predict(items: list):
    results = await process_batch(items)
    return {"results": results}
```

**If you're not familiar:**
- Review: [Real Python Async](https://realpython.com/async-io-python/)
- Estimated time: 1.5 hours

---

## Quick Refresher

### Abstract Base Classes

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height
```

### Decorators

```python
def timer(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.2f}s")
        return result
    return wrapper

@timer
def slow_function():
    import time
    time.sleep(1)
    return "Done"
```

### Context Managers

```python
class ManagedResource:
    def __enter__(self):
        print("Acquiring resource")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Releasing resource")
        return False

with ManagedResource():
    print("Using resource")
```

### Type Hints

```python
from typing import List, Dict, Optional, Callable

def process(
    items: List[int],
    config: Dict[str, str],
    callback: Optional[Callable] = None
) -> List[str]:
    return [str(item) for item in items]
```

---

## Self-Assessment

Before starting, can you:

- [ ] Create an abstract base class in Python?
- [ ] Implement the strategy pattern?
- [ ] Write a simple REST API endpoint?
- [ ] Build a Docker image from a Dockerfile?
- [ ] Use type hints in Python code?
- [ ] Understand basic ML training loops?

**If you answered NO to any question:**
Review the suggested materials above. Total review time: ~10-12 hours

**If you answered YES to all questions:**
You're ready to start! Begin with [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md)

---

## Estimated Preparation Time

- **If familiar with prerequisites:** 0 hours (ready to start)
- **If need review:** 10-12 hours (spread over 2-3 days)

---

## Common Gaps

### Gap 1: Never used abstract classes

**Symptoms:** Uncomfortable with `@abstractmethod`, don't know when to use ABC

**Fix:**
1. Complete Python OOP tutorial (2 hours)
2. Practice: Create ABC for different model types
3. Implement 2-3 concrete classes

### Gap 2: Not familiar with design patterns

**Symptoms:** Haven't used strategy, factory, or registry patterns

**Fix:**
1. Read strategy pattern guide (1 hour)
2. Implement strategy for ML framework
3. Build registry for components (1 hour)

### Gap 3: No API experience

**Symptoms:** Never built REST API, don't know FastAPI/Flask

**Fix:**
1. Complete FastAPI tutorial (2 hours)
2. Build 3-endpoint API
3. Add authentication and error handling

### Gap 4: Never used Docker

**Symptoms:** Don't know how to containerize applications

**Fix:**
1. Complete TUTORIAL-002 (1.5 hours)
2. Complete LAB-001 (2 hours)
3. Build your own Dockerfile

---

## Preparation Checklist

Use this checklist to verify you're ready:

**Python OOP**
- [ ] Can create classes with inheritance
- [ ] Understand abstract base classes
- [ ] Can use decorators
- [ ] Can write context managers

**Design Patterns**
- [ ] Understand strategy pattern
- [ ] Can implement factory pattern
- [ ] Know when to use registry pattern

**ML Basics**
- [ ] Can train a simple model
- [ ] Can save/load model checkpoints
- [ ] Understand batch processing

**APIs**
- [ ] Can create FastAPI endpoints
- [ ] Understand HTTP methods
- [ ] Can handle errors properly

**Docker**
- [ ] Can write a Dockerfile
- [ ] Can use Docker Compose
- [ ] Understand volumes and networks

---

**Next:** [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md)

**Need Help?** See [TROUBLESHOOTING-QUICKSTART.md](../../../00-META/TROUBLESHOOTING-QUICKSTART.md)
