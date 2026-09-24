# 2300: Framework Engineering - Quiz

**Test your knowledge of framework design patterns and deployment.**

---

## Instructions

1. Answer all questions
2. You need 80% to pass
3. Take your time - no time limit
4. Reference materials are allowed

**Passing Score:** 16/20 (80%)

---

## Multiple Choice Questions

### Question 1: Model Abstraction

**What is the primary benefit of using a model abstraction layer?**

A) Faster training
B) Framework-agnostic code
C) Better accuracy
D) Smaller model size

**Answer:** B

**Explanation:** Abstraction layers allow you to switch between PyTorch, TensorFlow, etc. without changing application code.

---

### Question 2: Design Patterns

**Which pattern allows runtime algorithm selection?**

A) Factory Pattern
B) Strategy Pattern
C) Observer Pattern
D) Registry Pattern

**Answer:** B

**Explanation:** Strategy Pattern enables selecting algorithms at runtime, like choosing between different optimizers.

---

### Question 3: Configuration Management

**Why use dataclasses for configuration?**

A) Faster execution
B) Type safety and validation
C) Lower memory usage
D) Better serialization

**Answer:** B

**Explanation:** Dataclasses provide type hints, validation, and clean serialization to/from dict.

---

### Question 4: Request Batching

**What is the main benefit of request batching?**

A) Lower latency
B) Higher throughput
C) Better accuracy
D) Smaller models

**Answer:** B

**Explanation:** Batching increases GPU utilization, resulting in much higher throughput (requests/second).

---

### Question 5: Model Parallelism

**When should you use model parallelism?**

A) Always
B) For small models
C) When model doesn't fit on one GPU
D) For faster training

**Answer:** C

**Explanation:** Model parallelism splits a large model across multiple GPUs when it won't fit on a single GPU.

---

### Question 6: Blue-Green Deployment

**What is a key advantage of blue-green deployment?**

A) Lower cost
B) Zero downtime
C) Faster deployment
D) Better performance

**Answer:** B

**Explanation:** Blue-green keeps old version (blue) running while deploying new (green), enabling instant rollback.

---

### Question 7: Canary Deployment

**What is canary deployment?**

A) Deploy to production immediately
B) Gradual rollout to small percentage of traffic
C) Deploy multiple versions simultaneously
D) Automatic deployment

**Answer:** B

**Explanation:** Canary deploys new version to small percentage (e.g., 5%) and gradually increases if metrics look good.

---

### Question 8: REST API Design

**Which HTTP method is most appropriate for model prediction?**

A) GET
B) POST
C) PUT
D) DELETE

**Answer:** B

**Explanation:** POST is used for prediction as it sends complex data that doesn't fit in URL parameters.

---

### Question 9: Rate Limiting

**Why implement rate limiting?**

A) To improve accuracy
B) To prevent abuse and manage load
C) To speed up requests
D) To reduce model size

**Answer:** B

**Explanation:** Rate limiting prevents API abuse, ensures fair access, and protects server resources.

---

### Question 10: Plugin Architecture

**What problem do plugin registries solve?**

A) Faster model training
B) Dynamic component loading
C) Better model accuracy
D) Reduced memory usage

**Answer:** B

**Explanation:** Plugin registries allow dynamic loading and discovery of components like custom layers and metrics.

---

### Question 11: A/B Testing

**What is the purpose of A/B testing ML models?**

A) To reduce training time
B) To compare model performance in production
C) To improve model accuracy
D) To reduce model size

**Answer:** B

**Explanation:** A/B testing compares two model versions in production to determine which performs better on real traffic.

---

### Question 12: Rolling Updates

**What happens during a rolling update?**

A) All instances updated at once
B) Instances updated one by one
C) Only some instances updated
D) No instances updated

**Answer:** B

**Explanation:** Rolling updates update instances one at a time (or in small groups) to maintain availability.

---

### Question 13: API Error Handling

**What HTTP status code indicates rate limiting?**

A) 400
B) 404
C) 429
D) 500

**Answer:** C

**Explanation:** 429 Too Many Requests is the standard status code for rate limiting.

---

### Question 14: Docker in ML

**Why use Docker for ML model deployment?**

A) Faster training
B) Consistent environment
C) Better models
D) Less memory usage

**Answer:** B

**Explanation:** Docker ensures consistent environments across development, testing, and production.

---

### Question 15: Streaming APIs

**When would you use Server-Sent Events (SSE)?**

A) For batch predictions
B) For real-time token generation
C) For model training
D) For data loading

**Answer:** B

**Explanation:** SSE is ideal for streaming responses like token-by-token text generation from LLMs.

---

## Coding Questions

### Question 16: Implement Abstract Base Class

**Create an abstract base class for ML models with `forward()` and `train_step()` methods.**

```python
from abc import ABC, abstractmethod

class BaseModel(ABC):
    @abstractmethod
    def forward(self, x):
        pass

    @abstractmethod
    def train_step(self, batch):
        pass
```

**Score:** __/2

---

### Question 17: Implement Configuration Class

**Create a configuration class with validation:**

```python
from dataclasses import dataclass

@dataclass
class ModelConfig:
    hidden_size: int
    learning_rate: float = 0.001

    def __post_init__(self):
        if self.hidden_size <= 0:
            raise ValueError("hidden_size must be positive")
```

**Score:** __/2

---

### Question 18: Implement Plugin Registry

**Create a simple plugin registry:**

```python
class PluginRegistry:
    def __init__(self):
        self._plugins = {}

    def register(self, name):
        def decorator(cls):
            self._plugins[name] = cls
            return cls
        return decorator

    def get(self, name):
        return self._plugins.get(name)
```

**Score:** __/2

---

### Question 19: Implement Batch Processing

**Write code to process requests in batches:**

```python
def process_batch(requests, batch_size=32):
    results = []
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i+batch_size]
        # Process batch
        batch_results = model.predict(batch)
        results.extend(batch_results)
    return results
```

**Score:** __/2

---

### Question 20: Deploy with Docker

**Write a Dockerfile for ML API:**

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Score:** __/2

---

## Scoring

### Calculate Your Score

```text
Multiple Choice: 15 questions × 1 point = 15 points
Coding Questions: 5 questions × 1 point = 5 points
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 20 points
```

### Results

- **18-20 points:** Excellent! 🌟
- **16-17 points:** Pass ✅
- **14-15 points:** Review recommended
- **Below 14:** Retake module

---

## Self-Grading

Grade your coding questions honestly:

- **2 points:** Complete and correct
- **1 point:** Mostly correct with minor issues
- **0 points:** Incomplete or incorrect

---

## Need to Review?

If you didn't pass, review these sections:

- **Questions 1-3:** [2301: Framework Design Patterns](../2301-Framework-Design-Patterns.md)
- **Questions 4-6:** [2302: Model Serving Architectures](../2302-Model-Serving-Architectures.md)
- **Questions 7-9:** [2304: Production Deployment](../2304-Production-Deployment-Patterns.md)
- **Questions 10-12:** [2301: Framework Design Patterns](../2301-Framework-Design-Patterns.md)
- **Questions 13-15:** [2303: API Design for ML](../2303-API-Design-for-ML.md)
- **Questions 16-20:** [2306: Building Production Framework](../guides/2306-Building-Production-Framework.md)

---

**Once you pass, you're ready to move on!** 🎉

**Next:** [2400: Pre-training Fundamentals](../README.md)

---

**Last Updated:** 2026-02-04
**Status:** Complete
**Time:** 30 minutes
