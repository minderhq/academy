---
Document ID: 6500-PRACTICE
Title: "6500: RAG MLOps - Practice"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
---

# 6500: RAG MLOps - Practice

## Exercises

### Exercise 1: Build RAG Evaluation Pipeline

```python
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

def create_evaluation_dataset(queries, retriever, generator):
    """Create dataset for RAG evaluation."""

    evaluation_data = []

    for query in queries:
        # Retrieve context
        contexts = retriever.retrieve(query, top_k=3)
        context_texts = [c["document"] for c in contexts]

        # Generate answer
        answer = generator.generate(query, context_texts)

        # Simple ground truth (in practice, use human annotations)
        ground_truth = f"Answer based on: {context_texts[0][:50]}..."

        evaluation_data.append({
            "question": query,
            "answer": answer,
            "contexts": context_texts,
            "ground_truth": ground_truth,
        })

    return Dataset.from_list(evaluation_data)

# Mock retriever and generator for testing
class MockRetriever:
    def retrieve(self, query, top_k=3):
        return [{"document": f"Context for {query}"}] * top_k

class MockGenerator:
    def generate(self, query, contexts):
        return f"Answer to '{query}' based on provided context."

# Run evaluation
test_queries = [
    "What is machine learning?",
    "How do neural networks work?",
    "Explain transformers architecture.",
]

print("Creating evaluation dataset...")
dataset = create_evaluation_dataset(
    test_queries,
    MockRetriever(),
    MockGenerator()
)

print(f"Dataset created with {len(dataset)} examples")

print("\nRunning RAGAS evaluation...")
result = evaluate(
    dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
    ]
)

print(f"\nEvaluation Results:")
for metric_name, score in result.items():
    print(f"  {metric_name}: {score:.3f}")

# Expected output:
# - Faithfulness score: 0.7-0.9 (higher is better)
# - Answer relevancy: 0.6-0.8 (higher is better)
# - Metrics measure RAG system quality
```

### Exercise 2: A/B Testing Framework

```python
class RAGABTest:
    def __init__(self, system_a, system_b):
        self.system_a = system_a
        self.system_b = system_b
        self.results = []

    def run_test(self, queries):
        """Run A/B test on queries."""

        for query in queries:
            # Get answers from both systems
            answer_a = self.system_a.query(query)
            answer_b = self.system_b.query(query)

            # Compare metrics
            metrics_a = self.evaluate_answer(query, answer_a)
            metrics_b = self.evaluate_answer(query, answer_b)

            winner = "a" if metrics_a["score"] > metrics_b["score"] else "b"

            self.results.append({
                "query": query,
                "system_a": metrics_a,
                "system_b": metrics_b,
                "winner": winner,
            })

        return self.results

    def evaluate_answer(self, query, answer):
        """Evaluate answer quality."""
        # Simple evaluation metrics
        return {
            "length": len(answer.get("text", "")),
            "has_context": "context" in answer.get("text", "").lower(),
            "latency": answer.get("latency", 0),
            "score": len(answer.get("text", "")) / 100,  # Simple score
        }

    def summarize_results(self):
        """Summarize A/B test results."""
        wins_a = sum(1 for r in self.results if r["winner"] == "a")
        wins_b = sum(1 for r in self.results if r["winner"] == "b")

        return {
            "system_a_wins": wins_a,
            "system_b_wins": wins_b,
            "win_rate_a": wins_a / len(self.results),
            "win_rate_b": wins_b / len(self.results),
        }

# Test
class MockRAGSystem:
    def __init__(self, name):
        self.name = name

    def query(self, query):
        return {"text": f"Answer from {self.name} for: {query}", "latency": 0.1}

ab_test = RAGABTest(
    MockRAGSystem("SystemA"),
    MockRAGSystem("SystemB")
)

results = ab_test.run_test(test_queries)
summary = ab_test.summarize_results()

print("A/B Test Results:")
print(f"  System A wins: {summary['system_a_wins']}")
print(f"  System B wins: {summary['system_b_wins']}")
print(f"  System A win rate: {summary['win_rate_a']:.1%}")

# Expected output:
# - Statistical comparison of two RAG systems
# - Win rate indicates which system performs better
# - Use for validating model changes
```

### Exercise 3: CI/CD for RAG Pipeline

```yaml
# .github/workflows/rag-ci.yml
name: RAG Pipeline CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Unit tests
        run: pytest tests/unit/ --cov=rag_pipeline

      - name: Integration tests
        run: pytest tests/integration/

      - name: RAG evaluation
        run: |
          python scripts/evaluate_rag.py \
            --retriever-config config/retriever.yaml \
            --generator-config config/generator.yaml \
            --eval-data data/eval_set.json

      - name: Upload coverage
        uses: codecov/codecov-action@v3

# Expected usage:
# - Runs on every push/PR
# - Unit tests verify code correctness
# - Integration tests verify end-to-end functionality
# - RAG evaluation monitors quality metrics
```

### Exercise 4: Monitoring RAG Performance

```python
from prometheus_client import Counter, Histogram, Gauge

class RAGMetrics:
    def __init__(self):
        # Define metrics
        self.requests_total = Counter('rag_requests_total', 'Total RAG requests')
        self.retrieval_latency = Histogram('rag_retrieval_latency_seconds', 'Retrieval latency')
        self.generation_latency = Histogram('rag_generation_latency_seconds', 'Generation latency')
        self.total_latency = Histogram('rag_total_latency_seconds', 'Total latency')
        self.retrieved_docs = Histogram('rag_retrieved_docs_count', 'Documents retrieved')
        self.faithfulness_score = Gauge('rag_faithfulness_score', 'Answer faithfulness')
        self.relevancy_score = Gauge('rag_relevancy_score', 'Answer relevancy')

    def record_request(self, retrieval_time, generation_time, num_docs, faithfulness, relevancy):
        """Record metrics for a request."""
        import time
        self.requests_total.inc()
        self.retrieval_latency.observe(retrieval_time)
        self.generation_latency.observe(generation_time)
        self.total_latency.observe(retrieval_time + generation_time)
        self.retrieved_docs.observe(num_docs)
        self.faithfulness_score.set(faithfulness)
        self.relevancy_score.set(relevancy)

# Use in RAG pipeline
metrics = RAGMetrics()

def rag_pipeline_with_metrics(query, retriever, generator):
    import time

    start_retrieve = time.time()
    contexts = retriever.retrieve(query, top_k=3)
    retrieval_time = time.time() - start_retrieve

    start_generate = time.time()
    answer = generator.generate(query, contexts)
    generation_time = time.time() - start_generate

    # Evaluate quality (simplified)
    faithfulness = 0.85  # In practice, calculate with RAGAS
    relevancy = 0.78

    # Record metrics
    metrics.record_request(
        retrieval_time,
        generation_time,
        len(contexts),
        faithfulness,
        relevancy,
    )

    return answer

# Test
print("Testing RAG pipeline with metrics...")
answer = rag_pipeline_with_metrics(
    "What is RAG?",
    MockRetriever(),
    MockGenerator()
)

print(f"Answer: {answer}")
print("Metrics recorded to Prometheus")

# Expected output:
# - Metrics exposed at /metrics endpoint
# - Grafana dashboards visualize performance
# - Alerts on threshold violations
```

### Exercise 5: Model Registry for RAG Components

```python
import mlflow

class RAGModelRegistry:
    def __init__(self, tracking_uri):
        mlflow.set_tracking_uri(tracking_uri)

    def log_retriever(self, retriever, config, metrics):
        """Log retriever model to registry."""
        with mlflow.start_run(run_name="retriever"):
            mlflow.log_params(config)
            mlflow.log_metrics(metrics)

            # Log model (simplified)
            mlflow.sklearn.log_model(
                retriever,
                "retriever",
                registered_model_name="rag_retriever",
            )

    def log_generator(self, generator, config, metrics):
        """Log generator model to registry."""
        with mlflow.start_run(run_name="generator"):
            mlflow.log_params(config)
            mlflow.log_metrics(metrics)

            mlflow.transformers.log_model(
                generator,
                "generator",
                registered_model_name="rag_generator",
            )

    def load_rag_pipeline(self, retriever_version, generator_version):
        """Load RAG pipeline from registry."""
        import mlflow

        retriever_uri = f"models:/rag_retriever/{retriever_version}"
        generator_uri = f"models:/rag_generator/{generator_version}"

        retriever = mlflow.sklearn.load_model(retriever_uri)
        generator = mlflow.transformers.load_model(generator_uri)

        return {"retriever": retriever, "generator": generator}

# Test
registry = RAGModelRegistry("sqlite:///mlflow.db")

print("Logging retriever model...")
registry.log_retriever(
    MockRetriever(),
    {"top_k": 3, "embedding_model": "miniLM"},
    {"precision": 0.85, "recall": 0.78}
)

print("Logging generator model...")
registry.log_generator(
    MockGenerator(),
    {"model": "gpt-4", "temperature": 0.7},
    {"latency": 0.5, "quality": 0.9}
)

print("Models logged to registry")

# Expected output:
# - Models versioned and tracked
# - Easy rollback to previous versions
# - Metadata and metrics preserved
```

### Exercise 6: Canary Deployment

```python
import random

class CanaryDeployment:
    def __init__(self, production_model, canary_model, canary_percentage=0.1):
        self.production_model = production_model
        self.canary_model = canary_model
        self.canary_percentage = canary_percentage

    def query(self, query):
        """Route query to production or canary."""

        # Route based on percentage
        if random.random() < self.canary_percentage:
            response = self.canary_model.query(query)
            source = "canary"
        else:
            response = self.production_model.query(query)
            source = "production"

        response["model_source"] = source
        return response

    def compare_metrics(self):
        """Compare metrics between production and canary."""

        # Simulated metrics
        production_metrics = {
            "avg_latency": 0.45,
            "avg_quality": 0.87,
            "error_rate": 0.01,
        }

        canary_metrics = {
            "avg_latency": 0.42,
            "avg_quality": 0.91,
            "error_rate": 0.008,
        }

        comparison = {
            "latency": {
                "production": production_metrics["avg_latency"],
                "canary": canary_metrics["avg_latency"],
                "diff": canary_metrics["avg_latency"] - production_metrics["avg_latency"],
            },
            "quality": {
                "production": production_metrics["avg_quality"],
                "canary": canary_metrics["avg_quality"],
                "diff": canary_metrics["avg_quality"] - production_metrics["avg_quality"],
            },
        }

        return comparison

# Evaluate canary promotion
def evaluate_canary_promotion(canary_deployment, threshold=0.05):
    """Decide whether to promote canary to production."""

    comparison = canary_deployment.compare_metrics()

    # Promote if latency improves and quality improves
    if (
        comparison["latency"]["diff"] < threshold and
        comparison["quality"]["diff"] > 0
    ):
        return True, "Canary performs better - promote"
    else:
        return False, "Canary not ready - keep in canary"

# Test
canary = CanaryDeployment(
    MockRAGSystem("production"),
    MockRAGSystem("canary"),
    canary_percentage=0.2
)

print(f"Routing queries: {canary.canary_percentage:.0%} to canary")

for i in range(10):
    result = canary.query(f"Query {i}")
    print(f"  Query {i}: {result['model_source']}")

# Check promotion
should_promote, reason = evaluate_canary_promotion(canary)
print(f"\nPromote canary: {should_promote}")
print(f"Reason: {reason}")

# Expected output:
# - 20% of queries go to canary
# - Gradual rollout reduces risk
# - Promote if metrics improve
```

### Exercise 7: Automated Retraining Pipeline

```python
def retrain_pipeline():
    """Automated retraining pipeline for RAG components."""

    # Check if retraining is needed
    current_metrics = {
        "faithfulness": 0.75,
        "relevancy": 0.68,
    }

    threshold_metrics = {
        "faithfulness": 0.80,
        "relevancy": 0.75,
    }

    print("Checking if retraining is needed...")

    if current_metrics["faithfulness"] < threshold_metrics["faithfulness"]:
        print("Faithfulness below threshold - triggering retraining")

        # Fetch new data
        new_data = [{"query": f"Query {i}", "context": f"Context {i}"} for i in range(100)]

        # Retrain retriever
        print("Retraining retriever...")
        new_retriever = MockRetriever()  # In practice, actual training
        retriever_metrics = {"precision": 0.88, "recall": 0.82}

        # Log new model
        print("Logging new retriever model...")
        # registry.log_retriever(new_retriever, config, retriever_metrics)

        # Retrain generator if needed
        if current_metrics["relevancy"] < threshold_metrics["relevancy"]:
            print("Relevancy below threshold - retraining generator")

            new_generator = MockGenerator()
            generator_metrics = {"latency": 0.4, "quality": 0.92}

            # registry.log_generator(new_generator, config, generator_metrics)

            print("Deploying new models...")
            # deploy_new_models(new_retriever, new_generator)

        print("Retraining complete - new models deployed")
    else:
        print("Metrics within thresholds - no retraining needed")

# Test
print("Running automated retraining check...")
retrain_pipeline()

# Schedule with cron (commented example):
# 0 2 * * * python scripts/retrain_pipeline.py

# Expected output:
# - Automated quality monitoring
# - Triggers retraining when metrics degrade
# - Deploys new models automatically
# - Scheduled to run periodically
```

---

**Last Updated:** 2026-02-05
**Status:** ✅ Complete - All tasks completed with solutions
