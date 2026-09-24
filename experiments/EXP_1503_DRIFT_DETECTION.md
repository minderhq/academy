---
Document ID: EXP_1503
Title: "EXP_1503: Model Drift Detection Experiments"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# EXP_1503: Model Drift Detection Experiments

## Overview
Practical experiments for detecting and monitoring model drift in LLM deployments using statistical methods and metrics.

## Experiment 1: Response Distribution Analysis

### Objective
Detect shifts in LLM response distributions over time.

### Implementation

```python
# drift_detection.py
import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon
import requests
import json
from collections import Counter
import time

class ModelDriftDetector:
    """Detect model drift in LLM responses"""

    def __init__(self, model_url: str = "http://localhost:8000"):
        self.model_url = model_url
        self.baseline_responses = []
        self.current_responses = []

    def generate_response(self, prompt: str):
        """Generate response from model"""

        response = requests.post(
            f"{self.model_url}/v1/chat/completions",
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.7
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]

        return None

    def collect_baseline(self, prompts: list, samples_per_prompt: int = 10):
        """Collect baseline response distributions"""

        print("Collecting baseline responses...")

        self.baseline_responses = []

        for prompt in prompts:
            responses = []
            for _ in range(samples_per_prompt):
                response = self.generate_response(prompt)
                if response:
                    responses.append(response)
                time.sleep(0.5)

            self.baseline_responses.append({
                "prompt": prompt,
                "responses": responses
            })

        print(f"✅ Collected baseline for {len(prompts)} prompts")

    def collect_current(self, prompts: list, samples_per_prompt: int = 10):
        """Collect current response distributions"""

        print("Collecting current responses...")

        self.current_responses = []

        for prompt in prompts:
            responses = []
            for _ in range(samples_per_prompt):
                response = self.generate_response(prompt)
                if response:
                    responses.append(response)
                time.sleep(0.5)

            self.current_responses.append({
                "prompt": prompt,
                "responses": responses
            })

        print(f"✅ Collected current for {len(prompts)} prompts")

    def calculate_response_length_stats(self, responses: list):
        """Calculate response length statistics"""

        lengths = [len(r.split()) for r in responses]

        return {
            "mean": np.mean(lengths),
            "std": np.std(lengths),
            "median": np.median(lengths),
            "min": np.min(lengths),
            "max": np.max(lengths)
        }

    def kl_divergence(self, p: np.ndarray, q: np.ndarray):
        """Calculate KL divergence between distributions"""

        # Add small epsilon to avoid division by zero
        epsilon = 1e-10
        p = p + epsilon
        q = q + epsilon

        return np.sum(p * np.log(p / q))

    def js_divergence(self, p: np.ndarray, q: np.ndarray):
        """Calculate Jensen-Shannon divergence"""

        return jensenshannon(p, q)

    def compare_distributions(self):
        """Compare baseline vs current distributions"""

        print("\nDistribution Comparison")
        print("=" * 60)

        drift_detected = False

        for i, (base, curr) in enumerate(zip(self.baseline_responses, self.current_responses)):
            prompt = base["prompt"]
            print(f"\nPrompt {i+1}: {prompt[:50]}...")

            # Length distribution comparison
            base_lengths = [len(r.split()) for r in base["responses"]]
            curr_lengths = [len(r.split()) for r in curr["responses"]]

            base_stats = self.calculate_response_length_stats(base["responses"])
            curr_stats = self.calculate_response_length_stats(curr["responses"])

            print(f"  Baseline - Mean: {base_stats['mean']:.1f}, Std: {base_stats['std']:.1f}")
            print(f"  Current  - Mean: {curr_stats['mean']:.1f}, Std: {curr_stats['std']:.1f}")

            # Kolmogorov-Smirnov test
            ks_statistic, ks_pvalue = stats.ks_2samp(base_lengths, curr_lengths)

            print(f"  KS Test: statistic={ks_statistic:.3f}, p-value={ks_pvalue:.3f}")

            if ks_pvalue < 0.05:
                print(f"  ⚠️  DRIFT DETECTED (p-value < 0.05)")
                drift_detected = True
            else:
                print(f"  ✅ No significant drift")

            # T-test for means
            t_statistic, t_pvalue = stats.ttest_ind(base_lengths, curr_lengths)

            print(f"  T-Test: t={t_statistic:.3f}, p-value={t_pvalue:.3f}")

        return drift_detected

    def detect_drift(self):
        """Comprehensive drift detection"""

        print("\nModel Drift Detection Report")
        print("=" * 60)

        drift = self.compare_distributions()

        if drift:
            print("\n⚠️  Model drift detected!")
            print("Recommendation: Investigate model configuration and retraining")
        else:
            print("\n✅ No significant model drift detected")

        return drift


def test_drift_detection():
    """Test drift detection"""

    print("Model Drift Detection")
    print("=" * 60)

    detector = ModelDriftDetector()

    # Test prompts
    prompts = [
        "Explain what is machine learning.",
        "Write a short poem about AI.",
        "What are the benefits of exercise?",
        "How does the internet work?",
        "Describe your favorite food."
    ]

    # Collect baseline
    detector.collect_baseline(prompts, samples_per_prompt=5)

    # Simulate drift by changing model parameters
    # In real scenario, this would be temporal separation

    # Collect current
    detector.collect_current(prompts, samples_per_prompt=5)

    # Detect drift
    detector.detect_drift()


if __name__ == "__main__":
    test_drift_detection()
```

---

## Experiment 2: Embedding Space Drift

### Objective
Detect drift in embedding space representations.

### Implementation

```python
# embedding_drift.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests

class EmbeddingDriftDetector:
    """Detect drift in embedding representations"""

    def __init__(self, embedding_url: str = "http://localhost:8001"):
        self.embedding_url = embedding_url
        self.baseline_embeddings = []
        self.current_embeddings = []

    def get_embedding(self, text: str):
        """Get embedding from model"""

        response = requests.post(
            f"{self.embedding_url}/embeddings",
            json={"input": text},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return np.array(result["data"][0]["embedding"])

        return None

    def collect_baseline_embeddings(self, texts: list):
        """Collect baseline embeddings"""

        print("Collecting baseline embeddings...")

        self.baseline_embeddings = []

        for text in texts:
            emb = self.get_embedding(text)
            if emb is not None:
                self.baseline_embeddings.append(emb)

        self.baseline_embeddings = np.array(self.baseline_embeddings)
        print(f"✅ Collected {len(self.baseline_embeddings)} embeddings")

    def collect_current_embeddings(self, texts: list):
        """Collect current embeddings"""

        print("Collecting current embeddings...")

        self.current_embeddings = []

        for text in texts:
            emb = self.get_embedding(text)
            if emb is not None:
                self.current_embeddings.append(emb)

        self.current_embeddings = np.array(self.current_embeddings)
        print(f"✅ Collected {len(self.current_embeddings)} embeddings")

    def calculate_centroid_drift(self):
        """Calculate drift in centroid position"""

        baseline_centroid = np.mean(self.baseline_embeddings, axis=0)
        current_centroid = np.mean(self.current_embeddings, axis=0)

        # Cosine similarity between centroids
        similarity = cosine_similarity(
            [baseline_centroid],
            [current_centroid]
        )[0][0]

        print(f"\nCentroid Similarity: {similarity:.4f}")

        if similarity < 0.95:
            print("  ⚠️  Significant centroid drift detected")
            return True
        else:
            print("  ✅ Centroid stable")
            return False

    def calculate_distribution_drift(self):
        """Calculate drift in embedding distribution"""

        # Calculate mean and covariance
        baseline_mean = np.mean(self.baseline_embeddings, axis=0)
        current_mean = np.mean(self.current_embeddings, axis=0)

        baseline_cov = np.cov(self.baseline_embeddings.T)
        current_cov = np.cov(self.current_embeddings.T.T)

        # Mahalanobis distance-like metric
        diff = baseline_mean - current_mean
        pooled_cov = (baseline_cov + current_cov) / 2

        try:
            inv_cov = np.linalg.inv(pooled_cov)
            mahal_dist = np.sqrt(diff @ inv_cov @ diff)

            print(f"\nMahalanobis Distance: {mahal_dist:.4f}")

            if mahal_dist > 3.0:  # 3 sigma threshold
                print("  ⚠️  Distribution drift detected")
                return True
            else:
                print("  ✅ Distribution stable")
                return False

        except np.linalg.LinAlgError:
            print("  ⚠️  Could not calculate (singular matrix)")
            return None

    def nearest_neighbor_consistency(self):
        """Check consistency of nearest neighbors"""

        print("\nNearest Neighbor Consistency:")

        consistent = 0
        total = min(len(self.baseline_embeddings), len(self.current_embeddings))

        for i in range(total):
            # Find nearest neighbor in baseline
            base_similarities = cosine_similarity(
                [self.baseline_embeddings[i]],
                self.baseline_embeddings
            )[0]
            base_nn = np.argsort(base_similarities)[-2]  # Exclude self

            # Find nearest neighbor in current
            curr_similarities = cosine_similarity(
                [self.current_embeddings[i]],
                self.current_embeddings
            )[0]
            curr_nn = np.argsort(curr_similarities)[-2]

            # Check if same text is nearest neighbor
            if base_nn == curr_nn:
                consistent += 1

        consistency_rate = consistent / total

        print(f"  Consistency Rate: {consistency_rate:.2%}")

        if consistency_rate < 0.7:
            print("  ⚠️  Low consistency - potential drift")
            return True
        else:
            print("  ✅ Good consistency maintained")
            return False

    def detect_embedding_drift(self):
        """Comprehensive embedding drift detection"""

        print("\nEmbedding Space Drift Detection")
        print("=" * 60)

        drift_indicators = []

        # Centroid drift
        centroid_drift = self.calculate_centroid_drift()
        if centroid_drift:
            drift_indicators.append("centroid")

        # Distribution drift
        dist_drift = self.calculate_distribution_drift()
        if dist_drift:
            drift_indicators.append("distribution")

        # Nearest neighbor consistency
        nn_drift = self.nearest_neighbor_consistency()
        if nn_drift:
            drift_indicators.append("nearest_neighbor")

        if drift_indicators:
            print(f"\n⚠️  Embedding drift detected in: {', '.join(drift_indicators)}")
            return True
        else:
            print("\n✅ No significant embedding drift")
            return False


def test_embedding_drift():
    """Test embedding drift detection"""

    print("Embedding Drift Detection")
    print("=" * 60)

    detector = EmbeddingDriftDetector()

    # Test texts
    texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Neural networks learn patterns from data.",
        "Transformers use attention mechanisms.",
        "Deep learning requires large datasets.",
        "Natural language processing deals with text."
    ]

    # Collect embeddings
    detector.collect_baseline_embeddings(texts)
    detector.collect_current_embeddings(texts)

    # Detect drift
    detector.detect_embedding_drift()


if __name__ == "__main__":
    test_embedding_drift()
```

---

## Experiment 3: Performance Degradation Monitoring

### Objective
Monitor for performance degradation over time.

### Implementation

```python
# performance_monitoring.py
import time
import requests
import statistics
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Prometheus metrics
inference_latency = Histogram(
    'model_inference_latency_seconds',
    'Model inference latency',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

throughput_tps = Gauge(
    'model_throughput_tokens_per_second',
    'Model throughput in tokens/second'
)

error_rate = Counter(
    'model_errors_total',
    'Total model errors',
    ['error_type']
)

memory_usage = Gauge(
    'model_memory_usage_bytes',
    'Model memory usage in bytes'
)


class PerformanceMonitor:
    """Monitor model performance for degradation"""

    def __init__(self, model_url: str = "http://localhost:8000"):
        self.model_url = model_url
        self.baseline_metrics = {}
        self.current_metrics = {}

    def benchmark_inference(self, prompt: str, num_runs: int = 10):
        """Benchmark inference performance"""

        latencies = []
        token_counts = []
        errors = 0

        for _ in range(num_runs):
            start = time.time()

            try:
                response = requests.post(
                    f"{self.model_url}/v1/chat/completions",
                    json={
                        "model": "mistralai/Mistral-7B-Instruct-v0.2",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200
                    },
                    timeout=30
                )

                latency = time.time() - start
                latencies.append(latency)

                if response.status_code == 200:
                    result = response.json()
                    tokens = result["usage"]["completion_tokens"]
                    token_counts.append(tokens)

                    # Record metrics
                    inference_latency.observe(latency)

                else:
                    errors += 1
                    error_rate.labels(error_type="api_error").inc()

            except Exception as e:
                errors += 1
                error_rate.labels(error_type=str(type(e).__name__)).inc()

        # Calculate statistics
        metrics = {
            "avg_latency": statistics.mean(latencies) if latencies else 0,
            "p95_latency": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else 0,
            "p99_latency": sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else 0,
            "avg_tokens": statistics.mean(token_counts) if token_counts else 0,
            "throughput": sum(token_counts) / sum(latencies) if latencies and token_counts else 0,
            "error_rate": errors / num_runs
        }

        # Update throughput gauge
        if metrics["throughput"] > 0:
            throughput_tps.set(metrics["throughput"])

        return metrics

    def establish_baseline(self, prompts: list):
        """Establish performance baseline"""

        print("Establishing performance baseline...")

        all_metrics = []

        for prompt in prompts:
            metrics = self.benchmark_inference(prompt, num_runs=5)
            all_metrics.append(metrics)

        # Aggregate baseline
        self.baseline_metrics = {
            "avg_latency": statistics.mean([m["avg_latency"] for m in all_metrics]),
            "p95_latency": statistics.mean([m["p95_latency"] for m in all_metrics]),
            "throughput": statistics.mean([m["throughput"] for m in all_metrics]),
            "error_rate": statistics.mean([m["error_rate"] for m in all_metrics])
        }

        print(f"\nBaseline Metrics:")
        print(f"  Avg Latency: {self.baseline_metrics['avg_latency']:.2f}s")
        print(f"  P95 Latency: {self.baseline_metrics['p95_latency']:.2f}s")
        print(f"  Throughput: {self.baseline_metrics['throughput']:.2f} tokens/s")
        print(f"  Error Rate: {self.baseline_metrics['error_rate']:.2%}")

    def check_performance(self, prompts: list):
        """Check current performance against baseline"""

        print("\nChecking current performance...")

        all_metrics = []

        for prompt in prompts:
            metrics = self.benchmark_inference(prompt, num_runs=5)
            all_metrics.append(metrics)

        # Aggregate current
        self.current_metrics = {
            "avg_latency": statistics.mean([m["avg_latency"] for m in all_metrics]),
            "p95_latency": statistics.mean([m["p95_latency"] for m in all_metrics]),
            "throughput": statistics.mean([m["throughput"] for m in all_metrics]),
            "error_rate": statistics.mean([m["error_rate"] for m in all_metrics])
        }

        print(f"\nCurrent Metrics:")
        print(f"  Avg Latency: {self.current_metrics['avg_latency']:.2f}s")
        print(f"  P95 Latency: {self.current_metrics['p95_latency']:.2f}s")
        print(f"  Throughput: {self.current_metrics['throughput']:.2f} tokens/s")
        print(f"  Error Rate: {self.current_metrics['error_rate']:.2%}")

    def detect_degradation(self):
        """Detect performance degradation"""

        print("\nPerformance Degradation Detection")
        print("=" * 60)

        degradation_detected = False

        # Check latency increase
        latency_increase = (self.current_metrics["avg_latency"] /
                          self.baseline_metrics["avg_latency"] - 1)

        print(f"\nLatency Change: {latency_change:+.1%}")

        if latency_change > 0.2:  # 20% increase
            print("  ⚠️  Significant latency increase detected")
            degradation_detected = True
        else:
            print("  ✅ Latency stable")

        # Check throughput decrease
        throughput_change = (self.current_metrics["throughput"] /
                            self.baseline_metrics["throughput"] - 1)

        print(f"\nThroughput Change: {throughput_change:+.1%}")

        if throughput_change < -0.2:  # 20% decrease
            print("  ⚠️  Significant throughput decrease detected")
            degradation_detected = True
        else:
            print("  ✅ Throughput stable")

        # Check error rate increase
        error_rate_change = (self.current_metrics["error_rate"] -
                           self.baseline_metrics["error_rate"])

        print(f"\nError Rate Change: {error_rate_change:+.2%}")

        if error_rate_change > 0.05:  # 5% increase
            print("  ⚠️  Error rate increased significantly")
            degradation_detected = True
        else:
            print("  ✅ Error rate stable")

        if degradation_detected:
            print("\n⚠️  Performance degradation detected!")
            print("Recommendation: Investigate resource usage and model configuration")
        else:
            print("\n✅ No significant performance degradation")

        return degradation_detected


def test_performance_monitoring():
    """Test performance monitoring"""

    print("Performance Monitoring for Drift Detection")
    print("=" * 60)

    # Start metrics server
    start_http_server(8000)
    print("Prometheus metrics on http://localhost:8000/metrics")

    monitor = PerformanceMonitor()

    # Test prompts
    prompts = [
        "Explain machine learning.",
        "What is deep learning?",
        "How do transformers work?",
        "What is natural language processing?",
        "Explain neural networks."
    ]

    # Establish baseline
    monitor.establish_baseline(prompts)

    # Simulate some load
    print("\nSimulating load...")
    for _ in range(10):
        monitor.benchmark_inference("Test prompt")

    # Check performance
    monitor.check_performance(prompts)

    # Detect degradation
    monitor.detect_degradation()


if __name__ == "__main__":
    test_performance_monitoring()
```

---

## Experiment 4: Alert Configuration

### Objective
Set up alerts for model drift detection.

### Implementation

```yaml
# drift_alerts.yml
groups:
  - name: model_drift_alerts
    interval: 1h
    rules:
      - alert: HighResponseLatency
        expr: rate(model_inference_latency_seconds_sum[5m]) / rate(model_inference_latency_seconds_count[5m]) > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High model inference latency"
          description: "Average latency is {{ $value }}s"

      - alert: LowThroughput
        expr: model_throughput_tokens_per_second < 20
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low model throughput"
          description: "Throughput is {{ $value }} tokens/s"

      - alert: HighErrorRate
        expr: rate(model_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High model error rate"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighMemoryUsage
        expr: model_memory_usage_bytes / (1024^3) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High model memory usage"
          description: "Memory usage is {{ $value }}GB"
```

---

## Quick Start

### Run Drift Detection

```bash
# Response distribution analysis
python drift_detection.py

# Embedding space drift
python embedding_drift.py

# Performance monitoring
python performance_monitoring

# Check Prometheus metrics
curl http://localhost:8000/metrics
```

### Set Up Alerts

```bash
# Add alert rules to Prometheus
cp drift_alerts.yml /etc/prometheus/
promtool check rules /etc/prometheus/drift_alerts.yml
systemctl reload prometheus
```

---

## Expected Results

### Drift Detection Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| **Latency Change** | +20% | +50% |
| **Throughput Change** | -20% | -50% |
| **Error Rate Change** | +5% | +10% |
| **Centroid Similarity** | <0.95 | <0.90 |
| **Distribution Distance** | >3.0 | >5.0 |

### Performance Baselines

| Metric | Baseline | Acceptable Range |
|--------|----------|-----------------|
| **Avg Latency** | 3s | 2-4s |
| **P95 Latency** | 8s | 6-12s |
| **Throughput** | 30 t/s | 25-35 t/s |
| **Error Rate** | <1% | <2% |

---

## Experiment Checklist

- [ ] Baseline response collection
- [ ] Distribution comparison setup
- [ ] Embedding space monitoring
- [ ] Performance baseline establishment
- [ ] Prometheus metrics configuration
- [ ] Alert rules setup
- [ ] Automated drift detection
- [ ] Retraining triggers
- [ ] A/B testing framework
- [ ] Documentation of drift events

---

## Related Documentation

- [1501: Monitoring and Observability](../docs/phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
- [1502: Model Drift Detection](../docs/phases/phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md)
- [1503: LLM Observability](../docs/phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md)
