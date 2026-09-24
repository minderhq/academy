---
Document ID: 1502
Title: Model Drift Detection
Phase: 1
Module: 1500
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'monitoring', 'observability', 'prometheus']
---

# 1502: Model Drift Detection

**Project:** AI Engineering Curriculum
**Phase:** [1500] Monitoring
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2 hours

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Types of Drift](#types-of-drift)
- [Drift Detection Algorithms](#drift-detection-algorithms)
- [Feature-Level Monitoring](#feature-level-monitoring)
- [Remeditation Strategies](#remeditation-strategies)
- [Production Deployment](#production-deployment)
- [Related Resources](#related-resources)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Types of Drift
- Explain Drift Detection Algorithms
- Measure and evaluate Feature-Level Monitoring
- Explain Remeditation Strategies
- Configure and operate Production Deployment
- Explain Related Resources

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
│  │  CONCEPT DRIFT (Label Shift)                                     │   │
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

---

## Drift Detection Algorithms

### Statistical Tests

```python
# drift_detection.py
import numpy as np
from scipy import stats
from typing import Tuple, Dict, List
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
            print("⚠️ Moderate drift detected (PSI:", f"{psi:.3f})")
        else:
            is_drift = True  # Significant drift
            print("🔴 Significant drift detected (PSI:", f"{psi:.3f})")

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
        """Chi-square test for categorical drift"""

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

        # Chi-square test
        statistic, p_value = stats.chisquare(
            current_hist,
            baseline_hist
        )

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
    ) -> Dict:
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
    ) -> Dict:
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

    def get_drift_summary(self, window_days: int = 30) -> Dict:
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
            'status': 'ALERT' if drift_rate > 0.3 else 'OK'
        }
```

---

## Feature-Level Monitoring

### Individual Feature Drift

```python
# feature_drift.py

class FeatureDriftMonitor:
    """Monitor drift for individual features"""

    def __init__(self, feature_names: List[str]):
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
    ) -> Dict[str, DriftResult]:
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
    ) -> List[str]:
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
    ) -> Dict:
        """Detect drift in embedding space"""

        if self.baseline_embeddings is None:
            raise ValueError("Baseline not set")

        current_mean = current_embeddings.mean(axis=0)

        # Calculate cosine similarity shift
        from sklearn.metrics.pairwise import cosine_similarity

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

## Remeditation Strategies

### Retraining Pipeline

```python
# retraining_pipeline.py

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

    def should_retrain(self) -> Tuple[bool, str]:
        """Check if model should be retrained"""

        summary = self.drift_monitor.get_drift_summary(window_days=7)

        if summary['drift_rate'] > self.retraining_threshold:
            return True, f"Drift rate {summary['drift_rate']:.2f} exceeds threshold"

        if summary['status'] == 'ALERT':
            return True, "Consecutive drifts detected - retraining recommended"

        return False, "No retraining needed"

    def trigger_retraining(
        self,
        new_training_data,
        validation_split: float = 0.2
    ) -> Dict:
        """Trigger model retraining"""

        print("🔄 Starting model retraining...")

        # Split data
        n_val = int(len(new_training_data) * validation_split)
        train_data = new_training_data[:-n_val]
        val_data = new_training_data[-n_val:]

        # Retrain model
        # (Simplified - actual implementation depends on model type)
        old_accuracy = self.model.score(val_data)

        self.model.fit(train_data)
        new_accuracy = self.model.score(val_data)

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

retraining_triggered = Counter(
    'model_retraining_triggered_total',
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
```

---

## References

### Related ai-engineering-curriculum Documents

- [1501: Monitoring and Observability for AI Engineering Curriculum](1501-Monitoring-and-Observability.md)
- [1503: LLM Observability](1503-LLM-Observability.md)

---

## Next Steps

- Continue with: **[1503: LLM Observability](./1503-LLM-Observability.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

## Related Resources

- **Related:** [1501: Monitoring and Observability](./1501-Monitoring-and-Observability.md)
- **Experiment:** [EXP_1502: Model Drift](../../../../experiments/EXP_1502_MODEL_DRIFT.md)

---

**Status:** ✅ Complete
