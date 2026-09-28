---
Document ID: 2300-PREREQUISITES
Title: "2300: Framework Engineering - Prerequisites"
Phase: 2
Module: 2300
Last Updated: 2026-09-28
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes (quick review) - 12.5 hours (full review)
Prerequisites: See module README
Related: See module README
Tags: framework-engineering, prerequisites, preparation
---

# 2300: Framework Engineering - Prerequisites

**Verify you're ready before starting the module.**

---

## Contents

- [Before You Start](#before-you-start)
- [Required Knowledge](#required-knowledge)
- [Quick Refresher](#quick-refresher)
- [Self-Assessment](#self-assessment)
- [Estimated Preparation Time](#estimated-preparation-time)
- [Common Gaps](#common-gaps)
- [Preparation Checklist](#preparation-checklist)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

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
    """Interface for optimizers - interchangeable at runtime."""

    @abstractmethod
    def optimize(self, params: dict, gradients: dict) -> dict:
        """Return NEW params after one update step."""
        pass

class SGDStrategy(OptimizationStrategy):
    def __init__(self, lr: float = 0.01):
        self.lr = lr

    def optimize(self, params, gradients):
        # param := param - lr * gradient
        return {k: params[k] - self.lr * gradients[k] for k in params}

class AdamStrategy(OptimizationStrategy):
    """Illustrative simplified Adam: the step is scaled per parameter by
    gradient magnitude. Real Adam additionally tracks running first/second
    moment estimates (see torch.optim.Adam)."""

    def __init__(self, lr: float = 0.01):
        self.lr = lr

    def optimize(self, params, gradients):
        new_params = {}
        for k in params:
            adaptive = self.lr / (1.0 + abs(gradients[k]))
            new_params[k] = params[k] - adaptive * gradients[k]
        return new_params

# Usage: same call site, different algorithm behind the interface
params = {"w": 1.0}
gradients = {"w": 0.5}

optimizer = SGDStrategy(lr=0.1)
print(optimizer.optimize(params, gradients))   # {'w': 0.95}

optimizer = AdamStrategy(lr=0.1)               # swap the strategy - nothing else changes
print(optimizer.optimize(params, gradients))   # {'w': 0.9666666666666667}
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

# Minimal data setup so the training loop below is runnable: two tiny
# batches of input features (x) and targets (y). A real dataloader
# yields the same dict shape.
dataloader = [
    {"x": torch.randn(8, 784), "y": torch.randn(8, 10)},
    {"x": torch.randn(8, 784), "y": torch.randn(8, 10)},
]
loss_fn = nn.MSELoss()

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
# weights_only=True is the torch >= 2.6 default; passing it explicitly
# keeps the checkpoint load safe (no arbitrary code execution) and
# version-stable
model = SimpleModel()
model.load_state_dict(torch.load("model.pt", weights_only=True))
```

**If you're not familiar:**
- Review: [2201: PyTorch Computational Graphs and Dynamic Execution](../2200-frameworks/2201-PyTorch-Computational-Graphs.md)
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
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    prediction: str
    confidence: float

# Stand-in for your loaded model - in a real application this is where
# you load weights (e.g. model = MyModel(); model.load_state_dict(...)).
# Defining it here keeps the example self-contained.
MODEL = {"label": "positive", "score": 0.98}

@app.get("/")
async def root():
    return {"message": "ML API"}

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    # model.predict(request.text) in a real app
    result = MODEL
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
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Example: Docker Compose**

```yaml
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
- Review: [Tutorial 002: Docker Essentials for AI](../../../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md)
- Practice: Complete [LAB 001: Docker & LLM Fundamentals](../../../learning-resources/labs/LAB-001-Docker-LLM.md)
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
from typing import List
from fastapi import FastAPI

app = FastAPI()

async def process_batch(batch):
    # Simulate async processing
    await asyncio.sleep(0.1)
    return [item * 2 for item in batch]

@app.post("/predict")
async def predict(items: List[int]):
    # A typed List[int] body parameter IS the whole request body: POST
    # [1, 2, 3] as a bare JSON array. (A bare `items: list` annotation
    # behaves differently - FastAPI embeds it as {"items": [...]}.)
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
import time

def timer(func):
    def wrapper(*args, **kwargs):
        # monotonic clock: wall-clock jumps (NTP, manual changes) would
        # corrupt elapsed-time math
        start = time.monotonic()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.monotonic() - start:.2f}s")
        return result
    return wrapper

@timer
def slow_function():
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
Review the suggested materials above. Total review time: 12.5 hours

**If you answered YES to all questions:**
You're ready to start! Begin with [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md)

---

## Estimated Preparation Time

- **If familiar with prerequisites:** 0 hours (ready to start)
- **If need review:** 12.5 hours (2 + 3 + 2 + 2 + 2 + 1.5, spread over 2-3 days)

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
1. Complete Tutorial 002 (1.5 hours)
2. Complete LAB 001 (2 hours)
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

## Summary

- This module assumes **OOP, design patterns, ML basics, REST APIs, Docker** — plus helpful async Python knowledge.
- Each knowledge area ships a runnable example (abstract base class, strategy/registry patterns, a complete PyTorch train/save/load loop, a self-contained FastAPI app, Dockerfile + Compose) — run them, don't just read them.
- **Full review takes 12.5 hours** (2 + 3 + 2 + 2 + 2 + 1.5); a quick skim of this guide takes ~30 minutes.
- Use the self-assessment and checklist to find your gaps; the Common Gaps section gives a fix plan per gap.
- Every example in the module builds on these — 2301's abstraction layers are the ABC here, 2301's plugin systems are the Registry here.

---

## References

### Related Documents

- [Phase 2: Module 2300 - Framework Engineering](./README.md) — module overview and learning path
- [2201: PyTorch Computational Graphs and Dynamic Execution](../2200-frameworks/2201-PyTorch-Computational-Graphs.md) — deeper PyTorch review (Section 3)
- [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md) — where the ABC and Registry patterns pay off
- [Tutorial 002: Docker Essentials for AI](../../../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md) — Docker review (Section 5)
- [LAB 001: Docker & LLM Fundamentals](../../../learning-resources/labs/LAB-001-Docker-LLM.md) — hands-on Docker practice
- [Quick Start Troubleshooting Guide](../../../00-META/TROUBLESHOOTING-QUICKSTART.md) — when setup problems block you

### External References

- [Python OOP Tutorial](https://docs.python.org/3/tutorial/classes.html) — classes, inheritance, ABCs (Section 1)
- [Refactoring.Guru Design Patterns](https://refactoring.guru/design-patterns) — strategy, factory, observer, registry (Section 2)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/) — the API framework used throughout this module (Section 4)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/) — async/await deep dive (Section 6)

---

## Next Steps

1. **Gaps found?** Work the fix plans in [Common Gaps](#common-gaps), then re-run the [Self-Assessment](#self-assessment).
2. **Ready?** Start the module with [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md).
3. **After the module:** take the [2300: Framework Engineering - Quiz](./assessment/QUIZ.md), then the [2300: Framework Engineering - Practice Exercises](./assessment/PRACTICE.md).

**Related:** [Phase 2: Module 2300 - Framework Engineering](./README.md) · [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md) · [Tutorial 002: Docker Essentials for AI](../../../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md)

**Experiment:** No EXP_23xx exists yet — nearest relevant: [EXP_1403: TGI (Text Generation Inference) Tuning Experiments](../../../../experiments/EXP_1403_TGI_TUNING.md) (serving-stack fundamentals, the direction this module prepares you for).
