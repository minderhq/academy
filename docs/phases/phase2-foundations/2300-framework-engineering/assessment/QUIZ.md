---
Document ID: 2300-QUIZ
Title: "2300: Framework Engineering - Quiz"
Phase: 2
Module: 2300
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['framework-engineering', 'assessment', 'quiz']
---

# 2300: Framework Engineering - Quiz

**Test your knowledge of framework design patterns and deployment.**

---

## Contents

- [Instructions](#instructions)
- [Multiple Choice Questions](#multiple-choice-questions)
- [Coding Questions](#coding-questions)
- [Scoring](#scoring)
- [Self-Grading](#self-grading)
- [Need to Review?](#need-to-review)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Instructions

1. Answer all questions
2. You need 80% to pass
3. Take your time - no time limit
4. Reference materials are allowed

**Passing Score:** 20/25 (80%)

---

## Multiple Choice Questions

### Question 1: Model Abstraction

**What is the primary benefit of using a model abstraction layer?**

A) Framework-agnostic code
B) Better accuracy
C) Faster training
D) Smaller model size

**Answer:** A

**Explanation:** Abstraction layers allow you to switch between PyTorch, TensorFlow, etc. without changing application code.

---

### Question 2: Design Patterns

**Which pattern allows runtime algorithm selection?**

A) Registry Pattern, a lookup that never swaps algorithms at runtime
B) Strategy Pattern
C) Factory Pattern
D) Observer Pattern

**Answer:** B

**Explanation:** Strategy Pattern enables selecting algorithms at runtime, like choosing between different optimizers.

---

### Question 3: Configuration Management

**Why use dataclasses for configuration?**

A) Faster execution, a speedup dataclasses have never been measured to deliver
B) Better serialization
C) Type safety and validation
D) Lower memory usage

**Answer:** C

**Explanation:** Dataclasses provide type hints, validation, and clean serialization to/from dict.

---

### Question 4: Throughput via Batching

**What is the main benefit of request batching?**

A) Smaller models, a size change batching never applies to any weights
B) Better accuracy
C) Lower latency
D) Higher throughput

**Answer:** D

**Explanation:** Batching increases GPU utilization, resulting in much higher throughput (requests/second).

---

### Question 5: Model Parallelism

**When should you use model parallelism?**

A) For small models, workloads that fit a single GPU with room to spare
B) When model doesn't fit on one GPU
C) Always
D) For faster training

**Answer:** B

**Explanation:** Model parallelism splits a large model across multiple GPUs when it won't fit on a single GPU.

---

### Question 6: Blue-Green Deployment

**What is a key advantage of blue-green deployment?**

A) Better performance
B) Lower cost
C) Zero downtime
D) Faster deployment

**Answer:** C

**Explanation:** Blue-green keeps old version (blue) running while deploying new (green), enabling instant rollback.

---

### Question 7: Canary Rollout Strategy

**What is canary deployment?**

A) Deploy to production immediately, a full-traffic jump that skips measurement entirely
B) Deploy multiple versions simultaneously
C) Gradual rollout to small percentage of traffic
D) Automatic deployment

**Answer:** C

**Explanation:** Canary deploys new version to small percentage (e.g., 5%) and gradually increases if metrics look good.

---

### Question 8: REST API Design

**Which HTTP method is most appropriate for model prediction?**

A) POST
B) GET
C) PUT
D) DELETE

**Answer:** A

**Explanation:** POST is used for prediction as it sends complex data that doesn't fit in URL parameters.

---

### Question 9: Rate Limiting

**Why implement rate limiting?**

A) To reduce model size, a footprint rate limiting has no mechanism to touch
B) To improve accuracy
C) To prevent abuse and manage load
D) To speed up requests

**Answer:** C

**Explanation:** Rate limiting prevents API abuse, ensures fair access, and protects server resources.

---

### Question 10: Plugin Architecture

**What problem do plugin registries solve?**

A) Faster model training, a speedup registration machinery has never produced
B) Reduced memory usage
C) Better model accuracy
D) Dynamic component loading

**Answer:** D

**Explanation:** Plugin registries allow dynamic loading and discovery of components like custom layers and metrics.

---

### Question 11: A/B Testing

**What is the purpose of A/B testing ML models?**

A) To reduce training time, a saving traffic splitting cannot deliver on its own
B) To compare model performance in production
C) To reduce model size
D) To improve model accuracy

**Answer:** B

**Explanation:** A/B testing compares two model versions in production to determine which performs better on real traffic.

---

### Question 12: Rolling Updates

**What happens during a rolling update?**

A) No instances updated
B) Instances updated one by one
C) All instances updated at once
D) Only some instances updated

**Answer:** B

**Explanation:** Rolling updates update instances one at a time (or in small groups) to maintain availability.

---

### Question 13: API Error Handling

**What HTTP status code indicates rate limiting?**

A) 429
B) 404, a code for missing resources rather than exhausted quotas
C) 400
D) 500

**Answer:** A

**Explanation:** 429 Too Many Requests is the standard status code for rate limiting (defined in RFC 6585).

---

### Question 14: Docker in ML

**Why use Docker for ML model deployment?**

A) Better models
B) Less memory usage
C) Faster training, a speed gain containerization itself never supplies
D) Consistent environment

**Answer:** D

**Explanation:** Docker ensures consistent environments across development, testing, and production.

---

### Question 15: Streaming APIs

**When would you use Server-Sent Events (SSE)?**

A) For real-time token generation
B) For data loading
C) For batch predictions, a workload where streamed events add overhead, not value
D) For model training

**Answer:** A

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

**Write code to process requests in batches. The model is passed in explicitly so the function has no hidden dependencies:**

```python
def process_batch(requests, model, batch_size=32):
    """Run model.predict over requests in fixed-size batches."""
    results = []
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i+batch_size]
        batch_results = model.predict(batch)
        results.extend(batch_results)
    return results
```

**Score:** __/2

---

### Question 20: Deploy with Docker

**Write a Dockerfile for ML API:**

```dockerfile
FROM python:3.13-slim
WORKDIR /app
# Official uv-in-Docker pattern: copy the uv binary from the uv image
# (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Dependency layer: only manifest/lockfile changes rebuild this.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Score:** __/2

---

## Answer Key

Multiple-choice answers for Questions 1-15. Questions 16-20 are self-graded
coding questions — score them against the model solution using the
**Self-Grading** rubric below.

| # | Answer |
|---|--------|
| 1 | A |
| 2 | B |
| 3 | C |
| 4 | D |
| 5 | B |
| 6 | C |
| 7 | C |
| 8 | A |
| 9 | C |
| 10 | D |
| 11 | B |
| 12 | B |
| 13 | A |
| 14 | D |
| 15 | A |

---

## Scoring

### Calculate Your Score

```text
Multiple Choice: 15 questions x 1 point = 15 points
Coding Questions:  5 questions x 2 points = 10 points
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 25 points
```

### Results

- **23-25 points:** Excellent! 🌟
- **20-22 points:** Pass ✅
- **18-19 points:** Review recommended
- **Below 18:** Retake module

---

## Self-Grading

Grade your coding questions honestly (each is worth up to 2 points):

- **2 points:** Complete and correct
- **1 point:** Mostly correct with minor issues
- **0 points:** Incomplete or incorrect

---

## Need to Review?

Each question maps to the lesson that teaches it:

- **Questions 1-3:** [2301: Framework Design Patterns](../2301-Framework-Design-Patterns.md) — abstraction, patterns, configuration
- **Questions 4-5:** [2302: Model Serving Architectures](../2302-Model-Serving-Architectures.md) — batching, parallelism
- **Questions 6-7:** [2304: Production Deployment Patterns](../2304-Production-Deployment-Patterns.md) — blue-green, canary
- **Questions 8-9:** [2303: API Design for ML Systems](../2303-API-Design-for-ML.md) — REST methods, rate limiting
- **Question 10:** [2301: Framework Design Patterns](../2301-Framework-Design-Patterns.md) — plugin registries
- **Questions 11-12:** [2304: Production Deployment Patterns](../2304-Production-Deployment-Patterns.md) — A/B testing, rolling updates
- **Questions 13, 15:** [2303: API Design for ML Systems](../2303-API-Design-for-ML.md) — status codes, SSE
- **Question 14:** [2304: Production Deployment Patterns](../2304-Production-Deployment-Patterns.md) — Docker deployment
- **Questions 16-20:** [2306: Building a Production Framework](../guides/2306-Building-Production-Framework.md) — hands-on framework building

---

## Summary

- **20 questions** covering all four module lessons plus the hands-on guide: model abstraction and design patterns (2301), serving and batching (2302), API design (2303), deployment strategies (2304), and end-to-end framework building (2306).
- **25 points total** — 15 multiple-choice (1 point each) plus 5 coding questions (2 points each); **20/25 (80%) passes**.
- **Self-graded**: score the coding questions against the reference code using the honest 2/1/0 scale.
- Every wrong answer points back to the exact lesson that teaches it — use the review map above before retaking.
- Once you pass, you're ready to move on! 🎉

---

## References

### Related Documents

- [Phase 2: Module 2300 - Framework Engineering](../README.md) — module overview and learning path
- [2301: Framework Design Patterns](../2301-Framework-Design-Patterns.md) — Questions 1-3, 10
- [2302: Model Serving Architectures](../2302-Model-Serving-Architectures.md) — Questions 4-5
- [2303: API Design for ML Systems](../2303-API-Design-for-ML.md) — Questions 8-9, 13, 15
- [2304: Production Deployment Patterns](../2304-Production-Deployment-Patterns.md) — Questions 6-7, 11-12, 14
- [2305: Framework Comparison Guide](../guides/2305-Framework-Comparison.md) — framework selection context
- [2306: Building a Production Framework](../guides/2306-Building-Production-Framework.md) — Questions 16-20
- [2300: Framework Engineering - Practice Exercises](./PRACTICE.md) — hands-on reinforcement for the coding questions

### External References

- [RFC 6585: Additional HTTP Status Codes](https://datatracker.ietf.org/doc/html/rfc6585) — defines 429 Too Many Requests (Question 13). Note: 429 is *not* part of RFC 9110's core status-code set.
- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) — instruction reference for Question 20.

---

## Next Steps

1. **Score below 20?** Work through the review map above, then retake.
2. **Passed?** Deepen the hands-on skills with [2300: Framework Engineering - Practice Exercises](./PRACTICE.md), then do the practical labs:
   - [LAB-007: Production RAG System](../../../../learning-resources/labs/LAB-007-Production-RAG.md)
   - [LAB-009: Production Deployment](../../../../learning-resources/labs/LAB-009-Production-Deployment.md)
3. **Next Module:** [2400: LLM Pretraining](../../2400-pretraining/README.md)

**Related:** [Phase 2: Module 2300 - Framework Engineering](../README.md) · [2304: Production Deployment Patterns](../2304-Production-Deployment-Patterns.md) · [TUTORIAL-003: RAG Basics - Give Your LLM Knowledge](../../../../learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md)

**Experiment:** No EXP_23xx exists yet — nearest relevant: [EXP_1403: TGI (Text Generation Inference) Tuning Experiments](../../../../../experiments/EXP_1403_TGI_TUNING.md) (serving-layer performance, matches this module's serving themes).
