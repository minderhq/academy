---
Document ID: 1502
Title: "1502: Model Drift Detection"
Phase: 1
Module: 1500
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'monitoring', 'observability', 'prometheus']
---

# 1502: Model Drift Detection

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Types of Drift](#types-of-drift)
- [Drift Detection Algorithms](#drift-detection-algorithms)
- [Feature-Level Monitoring](#feature-level-monitoring)
- [Remediation Strategies](#remediation-strategies)
- [Production Deployment](#production-deployment)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Distinguish data, concept, and prediction drift, and separate label shift from concept drift
- Run KS, PSI, and chi-square tests on binned features and interpret each drift verdict
- Monitor per-feature and embedding-space drift and reason about consecutive-drift thresholds
- Decide when to retrain from 7-day drift summaries and validate the retrained model's score
- Publish drift gauges and counters from the exporter and expose them on :8001/metrics
- Wire ModelDriftDetected, ModelDriftRateHigh, and ModelConsecutiveDrifts rules into alerts.yml

---

## Abstract

Model drift occurs when model performance degrades over time due to changes in data distribution or relationships. This document covers drift detection algorithms, monitoring strategies, and remediation approaches.

---

## Types of Drift

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      Model Drift Types                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  DATA DRIFT (Covariate Shift)                                    │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Input distribution changes                                   │   │
│  │  • Features change over time                                    │   │
│  │  • New data doesn't match training data                         │   │
│  │  • Example: User demographics shift                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  CONCEPT DRIFT                                                   │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Relationship between features and labels changes              │   │
│  │  • P(Y|X) changes over time                                      │   │
│  │  • Model's learned patterns become invalid                       │   │
│  │  • Example: Spam tactics evolve                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  PREDICTION DRIFT                                                 │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Output distribution changes                                   │   │
│  │  • Model predictions shift over time                             │   │
│  │  • Can indicate upstream problems                               │   │
│  │  • Example: Model becomes biased toward one class              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

Concept drift and label shift are distinct phenomena: concept drift is a change
in **P(Y|X)**; label shift is a change in the class prior **P(Y)** while P(X|Y)
stays fixed. The statistical tests below detect input distribution change —
concept drift additionally requires comparing predictions against ground-truth
labels (see `concept_drift.py`).

---

## Drift Detection Algorithms

### Statistical Tests

```python
# drift_detection.py
import numpy as np
from scipy import stats
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DriftResult:
    """Result of drift detection"""
    is_drift: bool
    p_value: float
    statistic: float
    test_name: str
    threshold: float
    timestamp: datetime

class DriftDetector:
    """Statistical drift detection"""

    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold
        self.baseline_distribution = None

    def set_baseline(self, baseline_data: np.ndarray):
        """Set baseline distribution from training data"""
        self.baseline_distribution = baseline_data
        print(f"✅ Baseline set: {len(baseline_data)} samples")

    def ks_test(
        self,
        current_data: np.ndarray
    ) -> DriftResult:
        """Kolmogorov-Smirnov test for distribution change"""

        if self.baseline_distribution is None:
            raise ValueError("Baseline not set")

        # KS test
        statistic, p_value = stats.ks_2samp(
            self.baseline_distribution,
            current_data
        )

        is_drift = p_value < self.threshold

        return DriftResult(
            is_drift=is_drift,
            p_value=p_value,
            statistic=statistic,
            test_name="KS Test",
            threshold=self.threshold,
            timestamp=datetime.now()
        )

    def psi_test(
        self,
        current_data: np.ndarray,
        bins: int = 10
    ) -> DriftResult:
        """Population Stability Index (PSI)"""

        if self.baseline_distribution is None:
            raise ValueError("Baseline not set")

        # Calculate histograms
        baseline_hist, bin_edges = np.histogram(
            self.baseline_distribution,
            bins=bins
        )
        current_hist, _ = np.histogram(
            current_data,
            bins=bin_edges
        )

        # Normalize
        baseline_pct = baseline_hist / len(self.baseline_distribution)
        current_pct = current_hist / len(current_data)

        # Avoid division by zero
        baseline_pct = np.clip(baseline_pct, 0.0001, None)
        current_pct = np.clip(current_pct, 0.0001, None)

        # Calculate PSI
        psi = np.sum(
            (baseline_pct - current_pct) *
            np.log(baseline_pct / current_pct)
        )

        # PSI thresholds (industry standard)
        if psi < 0.1:
            is_drift = False
        elif psi < 0.2:
            is_drift = True  # Moderate drift
            print(f"⚠️ Moderate drift detected (PSI: {psi:.3f})")
        else:
            is_drift = True  # Significant drift
            print(f"🔴 Significant drift detected (PSI: {psi:.3f})")

        # PSI has no p-value; sentinel values satisfy the shared DriftResult schema
        return DriftResult(
            is_drift=is_drift,
            p_value=1.0 if psi < 0.1 else 0.0,
            statistic=psi,
            test_name="PSI",
            threshold=0.1,
            timestamp=datetime.now()
        )

    def chi_square_test(
        self,
        current_data: np.ndarray,
        bins: int = 10
    ) -> DriftResult:
        """Chi-square goodness-of-fit test on binned numeric features"""

        if self.baseline_distribution is None:
            raise ValueError("Baseline not set")

        # Calculate histograms
        baseline_hist, bin_edges = np.histogram(
            self.baseline_distribution,
            bins=bins
        )
        current_hist, _ = np.histogram(
            current_data,
            bins=bin_edges
        )

        # Scale baseline counts to the observed total: chisquare requires
        # observed and expected sums to match (raises ValueError otherwise).
        expected = baseline_hist / baseline_hist.sum() * current_hist.sum()

        # Bins with zero expected frequency make the statistic undefined;
        # drop them (standard practice for empty categories).
        mask = expected > 0
        if not mask.any():
            raise ValueError("Baseline has no samples in the bin range")

        statistic, p_value = stats.chisquare(current_hist[mask], expected[mask])

        is_drift = p_value < self.threshold

        return DriftResult(
            is_drift=is_drift,
            p_value=p_value,
            statistic=statistic,
            test_name="Chi-Square",
            threshold=self.threshold,
            timestamp=datetime.now()
        )
```

### Concept Drift Detection

```python
# concept_drift.py
import numpy as np
from datetime import datetime

class ConceptDriftDetector:
    """Detect concept drift (P(Y|X) changes)"""

    def __init__(self, window_size: int = 1000, threshold: float = 0.05):
        self.window_size = window_size
        self.threshold = threshold
        self.prediction_buffer = []
        self.label_buffer = []

    def update(
        self,
        predictions: np.ndarray,
        labels: np.ndarray
    ) -> dict:
        """Update buffers and check for drift"""

        # Add to buffers
        self.prediction_buffer.extend(predictions)
        self.label_buffer.extend(labels)

        # Keep only recent samples
        if len(self.prediction_buffer) > self.window_size:
            self.prediction_buffer = self.prediction_buffer[-self.window_size:]
            self.label_buffer = self.label_buffer[-self.window_size:]

        # Calculate accuracy
        predictions_arr = np.array(self.prediction_buffer)
        labels_arr = np.array(self.label_buffer)

        current_accuracy = (predictions_arr == labels_arr).mean()

        # Check for drift (significant accuracy drop)
        if hasattr(self, 'baseline_accuracy'):
            accuracy_change = self.baseline_accuracy - current_accuracy

            if accuracy_change > self.threshold:
                return {
                    'is_drift': True,
                    'type': 'concept_drift',
                    'baseline_accuracy': self.baseline_accuracy,
                    'current_accuracy': current_accuracy,
                    'change': accuracy_change,
                    'timestamp': datetime.now()
                }

        return {
            'is_drift': False,
            'current_accuracy': current_accuracy
        }

    def set_baseline(self, predictions: np.ndarray, labels: np.ndarray):
        """Set baseline performance"""
        self.baseline_accuracy = (predictions == labels).mean()
        print(f"✅ Baseline accuracy: {self.baseline_accuracy:.3f}")
```

### Real-Time Drift Monitoring

```python
# drift_monitor.py
import numpy as np
from datetime import datetime

from drift_detection import DriftDetector

class RealTimeDriftMonitor:
    """Real-time drift monitoring for production"""

    def __init__(self, detector: DriftDetector):
        self.detector = detector
        self.drift_history = []
        self.alert_threshold = 3  # Alert after 3 consecutive drifts
        self.consecutive_drifts = 0

    def check_drift(
        self,
        current_data: np.ndarray,
        method: str = "ks"
    ) -> dict:
        """Check for drift in current batch"""

        if method == "ks":
            result = self.detector.ks_test(current_data)
        elif method == "psi":
            result = self.detector.psi_test(current_data)
        elif method == "chi_square":
            result = self.detector.chi_square_test(current_data)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Track history
        self.drift_history.append(result)

        # Update consecutive drifts counter
        if result.is_drift:
            self.consecutive_drifts += 1
        else:
            self.consecutive_drifts = 0

        # Generate alert if threshold exceeded
        alert = None

        if self.consecutive_drifts >= self.alert_threshold:
            alert = {
                'severity': 'CRITICAL',
                'message': f"{self.consecutive_drifts} consecutive drift detections",
                'recommendation': 'Investigate data pipeline and consider retraining'
            }

        return {
            'drift_detected': result.is_drift,
            'result': result,
            'consecutive_drifts': self.consecutive_drifts,
            'alert': alert
        }

    def get_drift_summary(self, window_days: int = 30) -> dict:
        """Get drift summary for time window"""

        cutoff = datetime.now().timestamp() - (window_days * 24 * 3600)

        recent_drifts = [
            r for r in self.drift_history
            if r.timestamp.timestamp() > cutoff
        ]

        total_checks = len(recent_drifts)
        drift_count = sum(1 for r in recent_drifts if r.is_drift)
        drift_rate = drift_count / total_checks if total_checks > 0 else 0

        return {
            'window_days': window_days,
            'total_checks': total_checks,
            'drift_count': drift_count,
            'drift_rate': drift_rate,
            'consecutive_drifts': self.consecutive_drifts,
            'status': 'ALERT' if drift_rate > 0.3 else 'OK'
        }
```

---

## Feature-Level Monitoring

### Individual Feature Drift

```python
# feature_drift.py
import numpy as np


from drift_detection import DriftDetector, DriftResult

class FeatureDriftMonitor:
    """Monitor drift for individual features"""

    def __init__(self, feature_names: list[str]):
        self.feature_names = feature_names
        self.detectors = {
            name: DriftDetector(threshold=0.01)
            for name in feature_names
        }
        self.baseline_set = False

    def set_baseline(self, baseline_features: np.ndarray):
        """Set baseline for all features"""

        for i, name in enumerate(self.feature_names):
            feature_data = baseline_features[:, i]
            self.detectors[name].set_baseline(feature_data)

        self.baseline_set = True
        print(f"✅ Baseline set for {len(self.feature_names)} features")

    def check_all_features(
        self,
        current_features: np.ndarray
    ) -> dict[str, DriftResult]:
        """Check drift for all features"""

        if not self.baseline_set:
            raise ValueError("Baseline not set")

        results = {}

        for i, name in enumerate(self.feature_names):
            feature_data = current_features[:, i]
            result = self.detectors[name].ks_test(feature_data)
            results[name] = result

            if result.is_drift:
                print(f"⚠️ Drift detected in feature: {name}")

        return results

    def get_drifted_features(
        self,
        current_features: np.ndarray
    ) -> list[str]:
        """Get list of features with drift"""

        results = self.check_all_features(current_features)

        drifted = [
            name for name, result in results.items()
            if result.is_drift
        ]

        return drifted
```

### Embedding Drift Detection

```python
# embedding_drift.py
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingDriftDetector:
    """Detect drift in embedding distributions"""

    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
        self.baseline_embeddings = None

    def set_baseline(self, baseline_embeddings: np.ndarray):
        """Set baseline embeddings"""
        self.baseline_embeddings = baseline_embeddings
        self.baseline_mean = baseline_embeddings.mean(axis=0)
        print(f"✅ Baseline embeddings: {baseline_embeddings.shape}")

    def detect_drift(
        self,
        current_embeddings: np.ndarray
    ) -> dict:
        """Detect drift in embedding space"""

        if self.baseline_embeddings is None:
            raise ValueError("Baseline not set")

        current_mean = current_embeddings.mean(axis=0)

        # Cosine similarity between baseline and current mean embeddings
        baseline_2d = self.baseline_mean.reshape(1, -1)
        current_2d = current_mean.reshape(1, -1)

        similarity = cosine_similarity(baseline_2d, current_2d)[0, 0]

        # Drift if similarity drops
        drift_amount = 1.0 - similarity
        is_drift = drift_amount > self.threshold

        return {
            'is_drift': is_drift,
            'similarity': similarity,
            'drift_amount': drift_amount,
            'threshold': self.threshold
        }
```

---

## Remediation Strategies

### Retraining Pipeline

```python
# retraining_pipeline.py
import numpy as np
from datetime import datetime

from drift_monitor import RealTimeDriftMonitor

class RetrainingPipeline:
    """Automated retraining pipeline for drifted models"""

    def __init__(
        self,
        model,
        drift_monitor: RealTimeDriftMonitor,
        retraining_threshold: float = 0.3
    ):
        self.model = model
        self.drift_monitor = drift_monitor
        self.retraining_threshold = retraining_threshold
        self.retraining_history = []

    def should_retrain(self) -> tuple[bool, str]:
        """Check if model should be retrained"""

        summary = self.drift_monitor.get_drift_summary(window_days=7)

        if summary['consecutive_drifts'] >= self.drift_monitor.alert_threshold:
            return (
                True,
                f"{summary['consecutive_drifts']} consecutive drifts - retraining recommended"
            )

        if summary['drift_rate'] > self.retraining_threshold:
            return True, f"Drift rate {summary['drift_rate']:.2f} exceeds threshold"

        return False, "No retraining needed"

    def trigger_retraining(
        self,
        new_training_data: tuple[np.ndarray, np.ndarray],
        validation_split: float = 0.2
    ) -> dict:
        """Trigger model retraining

        new_training_data is an (X, y) tuple for a scikit-learn-style
        estimator (fit(X, y) / score(X, y)).
        """

        print("🔄 Starting model retraining...")

        # Split data
        X, y = new_training_data

        # max(1, ...): n_val = 0 would make X[:-0] an empty slice and put
        # every sample into validation.
        n_val = max(1, int(len(X) * validation_split))
        X_train, X_val = X[:-n_val], X[-n_val:]
        y_train, y_val = y[:-n_val], y[-n_val:]

        # Retrain model (scikit-learn estimator API)
        old_accuracy = self.model.score(X_val, y_val)

        self.model.fit(X_train, y_train)
        new_accuracy = self.model.score(X_val, y_val)

        improvement = new_accuracy - old_accuracy

        result = {
            'timestamp': datetime.now(),
            'old_accuracy': old_accuracy,
            'new_accuracy': new_accuracy,
            'improvement': improvement,
            'status': 'success' if improvement > 0 else 'failed'
        }

        self.retraining_history.append(result)

        print(f"✅ Retraining complete. Accuracy: {old_accuracy:.3f} → {new_accuracy:.3f}")

        return result
```

---

## Production Deployment

### Monitoring Dashboard Metrics

```python
# drift_dashboard.py

from prometheus_client import Gauge, Counter

from drift_detection import DriftResult

# Define metrics
drift_detection = Gauge(
    'model_drift_detected',
    'Whether drift was detected (1=yes, 0=no)',
    ['model_name', 'feature']
)

drift_rate = Gauge(
    'model_drift_rate',
    'Rate of drift detection',
    ['model_name']
)

drift_p_value = Gauge(
    'model_drift_p_value',
    'P-value from drift test',
    ['model_name', 'test_type']
)

consecutive_drifts = Gauge(
    'model_consecutive_drifts',
    'Number of consecutive drift detections',
    ['model_name']
)

# prometheus_client strips and re-appends _total on exposure; pass the bare name
retraining_triggered = Counter(
    'model_retraining_triggered',
    'Total number of retraining triggers',
    ['model_name']
)

class DriftMetricsPublisher:
    """Publish drift metrics to monitoring system"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def publish_drift_result(
        self,
        feature_name: str,
        result: DriftResult
    ):
        """Publish drift detection result"""

        drift_detection.labels(
            model_name=self.model_name,
            feature=feature_name
        ).set(1 if result.is_drift else 0)

        drift_p_value.labels(
            model_name=self.model_name,
            test_type=result.test_name
        ).set(result.p_value)

    def publish_consecutive_drifts(self, count: int):
        """Publish consecutive drift count"""

        consecutive_drifts.labels(
            model_name=self.model_name
        ).set(count)

    def publish_drift_rate(self, rate: float):
        """Publish drift rate"""

        drift_rate.labels(
            model_name=self.model_name
        ).set(rate)

    def publish_retraining(self):
        """Publish retraining event"""

        retraining_triggered.labels(
            model_name=self.model_name
        ).inc()


if __name__ == "__main__":
    from prometheus_client import start_http_server
    import time

    # Expose metrics so Prometheus actually has something to scrape
    # (scrape job: drift-dashboard, port 8001).
    start_http_server(8001)
    print("✅ Drift metrics exposed on :8001/metrics")

    while True:
        time.sleep(3600)
```

### Drift Alerts

Prometheus rules for the metrics above. Merge into the `alerts.yml` wired via
`rule_files` in [1501: Monitoring and Observability](./1501-Monitoring-and-Observability.md):

```yaml
# drift_alerts.yml
groups:
  - name: model_drift_alerts
    interval: 60s
    rules:
      # A feature drifted on the latest check
      - alert: ModelDriftDetected
        expr: model_drift_detected == 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Drift detected: {{ $labels.model_name }} / {{ $labels.feature }}"

      # Sustained drift rate above the retraining threshold
      - alert: ModelDriftRateHigh
        expr: model_drift_rate > 0.3
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Drift rate {{ $value | humanizePercentage }} on {{ $labels.model_name }}"

      # Matches the monitor's alert_threshold (consecutive drifts)
      - alert: ModelConsecutiveDrifts
        expr: model_consecutive_drifts >= 3
        labels:
          severity: critical
        annotations:
          summary: "{{ $value }} consecutive drift detections on {{ $labels.model_name }}"
```

---

## Summary

Models decay silently: as the world's data distribution drifts from training data, performance degrades without a single error being thrown. This lesson covered the types of drift, the detection algorithms that catch them, feature-level monitoring to localize where the input shifted, remediation strategies, and production deployment of the monitors themselves. The rule it leaves: drift detection is not an alert on accuracy - it is a standing comparison between the data a model was trained on and the data it is actually receiving.

## References

### Related Minder Academy Documents

- [1501: Monitoring and Observability](1501-Monitoring-and-Observability.md)
- [1503: LLM Observability](1503-LLM-Observability.md)

### External References

- [scipy.stats.ks_2samp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html)
- [scipy.stats.chisquare](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chisquare.html)
- [alibi-detect](https://github.com/SeldonIO/alibi-detect)
- [Evidently](https://github.com/evidentlyai/evidently)

---

## Next Steps

- Continue with: **[1503: LLM Observability](./1503-LLM-Observability.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [1501: Monitoring and Observability](./1501-Monitoring-and-Observability.md)
- [1402: vLLM and TGI](../1400-llmops/1402-vLLM-and-TGI.md)
- **Experiment:** [EXP_1502: Model Drift](../../../../experiments/EXP_1502_MODEL_DRIFT.md)
