---
Document ID: 6501
Title: ML Model Lifecycle Management
Phase: 6
Module: 6500
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['mlops', 'pipeline', 'ci-cd', 'model-registry', 'lifecycle']
---

# 6501: ML Model Lifecycle Management

**Project:** PROJECT-OMEGA
**Phase:** [6500] MLOps Pipelines
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 4 hours

---

## Abstract

End-to-end machine learning model lifecycle management from development to production. This document covers the complete ML lifecycle including training, validation, deployment, monitoring, and retirement.

---

## ML Lifecycle Stages

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ML Model Lifecycle Management                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │          │    │          │    │          │    │          │        │
│  │ DEVELOP  │───►│ VALIDATE │───►│ DEPLOY   │───►│ MONITOR  │        │
│  │          │    │          │    │          │    │          │        │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘        │
│       │              │              │              │                 │
│       ▼              ▼              ▼              ▼                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │Feature   │    │Model     │    │Canary    │    │Drift     │        │
│  │Engineering│  │Testing   │    │Release   │    │Detection │        │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘        │
│                                                           │            │
│                                                           ▼            │
│                                                    ┌──────────┐        │
│                                                    │ RETIRE   │        │
│                                                    └──────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Development

### 1.1 Feature Engineering Pipeline

```python
# feature_pipeline.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

class FeaturePipeline:
    """Production feature engineering pipeline"""

    def __init__(self, config):
        self.scaler = StandardScaler()
        self.config = config
        self.feature_stats = {}

    def extract_features(self, raw_data):
        """Extract features from raw data"""
        features = {}

        # Text features
        features['text_length'] = raw_data['text'].str.len()
        features['word_count'] = raw_data['text'].str.split().str.len()
        features['avg_word_length'] = (
            features['text_length'] / features['word_count']
        )

        # Embedding features
        features['embedding'] = self._get_embeddings(raw_data['text'])

        return pd.DataFrame(features)

    def transform(self, features):
        """Transform features for model input"""
        # Normalize numerical features
        numerical_cols = features.select_dtypes(include=[np.number]).columns
        features[numerical_cols] = self.scaler.fit_transform(features[numerical_cols])

        # Store statistics for monitoring
        self.feature_stats = {
            col: {
                'mean': features[col].mean(),
                'std': features[col].std(),
                'min': features[col].min(),
                'max': features[col].max()
            }
            for col in numerical_cols
        }

        return features

    def _get_embeddings(self, texts):
        """Get embeddings using LLM"""
        # Implementation depends on your embedding model
        pass
```

### 1.2 Model Training Pipeline

```python
# training_pipeline.py
import mlflow
import mlflow.sklearn
from datetime import datetime

class TrainingPipeline:
    """Production training pipeline with MLflow tracking"""

    def __init__(self, experiment_name):
        mlflow.set_experiment(experiment_name)
        self.run_id = None

    def train(self, model, X_train, y_train, params):
        """Train model with experiment tracking"""
        with mlflow.start_run() as run:
            self.run_id = run.info.run_id

            # Log parameters
            mlflow.log_params(params)

            # Train model
            model.fit(X_train, y_train)

            # Log metrics
            train_score = model.score(X_train, y_train)
            mlflow.log_metric("train_score", train_score)

            # Log model
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name=self.model_name
            )

            return model, run

    def validate(self, model, X_val, y_val):
        """Validate model and log metrics"""
        val_score = model.score(X_val, y_val)
        mlflow.log_metric("val_score", val_score)

        # Log predictions for analysis
        predictions = model.predict(X_val)
        mlflow.log_text(
            str(predictions[:10]),
            "sample_predictions.txt"
        )

        return val_score

    def register_model(self, model_name, stage="Staging"):
        """Register model for deployment"""
        model_uri = f"runs:/{self.run_id}/model"
        mlflow.register_model(
            model_uri,
            model_name,
            tags={"version": "1.0"}
        )
```

---

## Stage 2: Validation

### 2.1 Model Validation Framework

```python
# model_validation.py
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)
import numpy as np

class ModelValidator:
    """Comprehensive model validation"""

    def __init__(self, thresholds):
        self.thresholds = thresholds
        self.results = {}

    def validate(self, model, X_test, y_test):
        """Run all validation checks"""
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        # Performance metrics
        self.results['accuracy'] = accuracy_score(y_test, y_pred)
        self.results['precision'] = precision_score(y_test, y_pred)
        self.results['recall'] = recall_score(y_test, y_pred)
        self.results['f1'] = f1_score(y_test, y_pred)
        self.results['auc'] = roc_auc_score(y_test, y_proba)

        # Confusion matrix
        self.results['confusion_matrix'] = confusion_matrix(y_test, y_pred)

        # Check thresholds
        passed = self._check_thresholds()

        return passed, self.results

    def _check_thresholds(self):
        """Check if metrics meet thresholds"""
        passed = True
        for metric, threshold in self.thresholds.items():
            if self.results.get(metric, 0) < threshold:
                print(f"❌ {metric}: {self.results[metric]:.3f} < {threshold}")
                passed = False
            else:
                print(f"✅ {metric}: {self.results[metric]:.3f} >= {threshold}")

        return passed

    def generate_report(self):
        """Generate validation report"""
        report = f"""
# Model Validation Report

## Performance Metrics
- Accuracy: {self.results['accuracy']:.3f}
- Precision: {self.results['precision']:.3f}
- Recall: {self.results['recall']:.3f}
- F1 Score: {self.results['f1']:.3f}
- AUC: {self.results['auc']:.3f}

## Confusion Matrix
{self.results['confusion_matrix']}

## Recommendation
{'✅ APPROVED for deployment' if self._check_thresholds() else '❌ REJECTED - Below thresholds'}
        """
        return report
```

### 2.2 A/B Testing Framework

```python
# ab_testing.py
from scipy import stats
import pandas as pd

class ABTest:
    """A/B testing for model comparison"""

    def __init__(self, alpha=0.05):
        self.alpha = alpha
        self.results = {}

    def compare_models(self, model_a, model_b, X_test, y_test):
        """Compare two models using statistical tests"""
        # Get predictions
        pred_a = model_a.predict(X_test)
        pred_b = model_b.predict(X_test)

        # Calculate metrics
        acc_a = accuracy_score(y_test, pred_a)
        acc_b = accuracy_score(y_test, pred_b)

        # Statistical test
        stat, p_value = stats.ttest_rel(
            (pred_a == y_test),
            (pred_b == y_test)
        )

        self.results = {
            'model_a_accuracy': acc_a,
            'model_b_accuracy': acc_b,
            'difference': acc_a - acc_b,
            'p_value': p_value,
            'significant': p_value < self.alpha
        }

        return self.results

    def generate_report(self):
        """Generate A/B test report"""
        significance = "✅ Significant" if self.results['significant'] else "⚠️ Not significant"

        report = f"""
# A/B Test Results

## Model Comparison
- Model A Accuracy: {self.results['model_a_accuracy']:.3f}
- Model B Accuracy: {self.results['model_b_accuracy']:.3f}
- Difference: {self.results['difference']:.3f}
- P-value: {self.results['p_value']:.4f}

## Conclusion
{significance} ({self.results['p_value']:.4f} {'<' if self.results['significant'] else '>='} {self.alpha})

## Recommendation
{'Model A is significantly better' if self.results['difference'] > 0 and self.results['significant'] else
 'Model B is significantly better' if self.results['difference'] < 0 and self.results['significant'] else
 'No significant difference - consider other metrics'}
        """
        return report
```

---

## Stage 3: Deployment

### 3.1 Canary Deployment Strategy

```python
# canary_deployment.py
from dataclasses import dataclass
from typing import Optional
import random

@dataclass
class DeploymentConfig:
    """Canary deployment configuration"""
    model_name: str
    canary_percentage: float = 0.1  # Start with 10% traffic
    min_success_rate: float = 0.95
    max_error_rate: float = 0.05
    duration_hours: int = 24

class CanaryDeployment:
    """Progressive canary deployment"""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.traffic_split = config.canary_percentage
        self.metrics = {
            'requests': 0,
            'errors': 0,
            'success_rate': 0.0
        }

    def route_request(self, request):
        """Route request based on traffic split"""
        self.metrics['requests'] += 1

        if random.random() < self.traffic_split:
            # Route to canary (new model)
            response = self._serve_canary(request)
        else:
            # Route to production (old model)
            response = self._serve_production(request)

        if not response['success']:
            self.metrics['errors'] += 1

        self._update_metrics()

        return response

    def _update_metrics(self):
        """Update success rate"""
        if self.metrics['requests'] > 0:
            self.metrics['success_rate'] = (
                (self.metrics['requests'] - self.metrics['errors']) /
                self.metrics['requests']
            )

    def should_increase_traffic(self):
        """Check if canary traffic should be increased"""
        if self.metrics['requests'] < 100:
            return False  # Not enough data

        conditions = [
            self.metrics['success_rate'] >= self.config.min_success_rate,
            (self.metrics['errors'] / self.metrics['requests']) < self.config.max_error_rate
        ]

        return all(conditions)

    def increase_traffic(self, increment=0.1):
        """Increase canary traffic percentage"""
        if self.traffic_split < 1.0:
            self.traffic_split = min(1.0, self.traffic_split + increment)
            print(f"📈 Traffic increased to {self.traffic_split*100:.0f}%")

    def rollback(self):
        """Rollback to production model"""
        self.traffic_split = 0.0
        print("⚠️ Rolling back to production model")
```

### 3.2 Blue-Green Deployment

```python
# blue_green_deployment.py
class BlueGreenDeployment:
    """Blue-green deployment strategy"""

    def __init__(self, blue_model, green_model):
        self.blue = blue_model  # Current production
        self.green = green_model  # New version
        self.active = 'blue'

    def deploy_green(self):
        """Switch to green (new model)"""
        print("🟢 Switching to green deployment")
        self.active = 'green'

    def rollback_blue(self):
        """Rollback to blue (old model)"""
        print("🔵 Rolling back to blue deployment")
        self.active = 'blue'

    def predict(self, X):
        """Route to active model"""
        if self.active == 'blue':
            return self.blue.predict(X)
        else:
            return self.green.predict(X)

    def health_check(self):
        """Health check for active deployment"""
        active_model = self.blue if self.active == 'blue' else self.green

        # Run health checks
        checks = {
            'model_loaded': active_model is not None,
            'latency_ok': self._check_latency(),
            'memory_ok': self._check_memory()
        }

        return all(checks.values()), checks

    def _check_latency(self):
        """Check prediction latency"""
        import time
        start = time.time()
        # Make test prediction
        # active_model.predict(test_data)
        latency = time.time() - start
        return latency < 1.0  # 1 second threshold

    def _check_memory(self):
        """Check memory usage"""
        import psutil
        return psutil.virtual_memory().percent < 90
```

---

## Stage 4: Monitoring

### 4.1 Performance Monitoring Dashboard

```python
# monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
prediction_counter = Counter(
    'model_predictions_total',
    'Total number of predictions',
    ['model_name', 'status']
)

prediction_latency = Histogram(
    'model_prediction_latency_seconds',
    'Prediction latency',
    ['model_name']
)

model_accuracy = Gauge(
    'model_accuracy',
    'Current model accuracy',
    ['model_name']
)

class ModelMonitor:
    """Production model monitoring"""

    def __init__(self, model_name):
        self.model_name = model_name

    def track_prediction(self, success=True):
        """Track prediction count"""
        status = 'success' if success else 'error'
        prediction_counter.labels(
            model_name=self.model_name,
            status=status
        ).inc()

    def track_latency(self, latency):
        """Track prediction latency"""
        prediction_latency.labels(
            model_name=self.model_name
        ).observe(latency)

    def update_accuracy(self, accuracy):
        """Update model accuracy gauge"""
        model_accuracy.labels(
            model_name=self.model_name
        ).set(accuracy)

    def predict(self, model, X):
        """Predict with monitoring"""
        start = time.time()

        try:
            result = model.predict(X)
            success = True
        except Exception as e:
            print(f"Prediction error: {e}")
            result = None
            success = False

        latency = time.time() - start

        # Track metrics
        self.track_prediction(success)
        self.track_latency(latency)

        return result
```

### 4.2 Alert System

```python
# alerting.py
from dataclasses import dataclass
from enum import Enum
import smtplib

class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass
class Alert:
    severity: AlertSeverity
    message: str
    metric: str
    value: float
    threshold: float

class AlertManager:
    """Production alert management"""

    def __init__(self, config):
        self.config = config
        self.alerts = []

    def check_thresholds(self, metrics):
        """Check if metrics exceed thresholds"""
        for metric, value in metrics.items():
            threshold = self.config.get(f'{metric}_threshold')

            if threshold and value > threshold:
                alert = Alert(
                    severity=AlertSeverity.CRITICAL if value > threshold * 1.5 else AlertSeverity.WARNING,
                    message=f"{metric} exceeded threshold: {value:.3f} > {threshold:.3f}",
                    metric=metric,
                    value=value,
                    threshold=threshold
                )
                self.alerts.append(alert)
                self._send_alert(alert)

    def _send_alert(self, alert: Alert):
        """Send alert notification"""
        if alert.severity == AlertSeverity.CRITICAL:
            self._send_email(alert)
            self._send_slack(alert)

    def _send_email(self, alert: Alert):
        """Send email alert"""
        # Implementation
        pass

    def _send_slack(self, alert: Alert):
        """Send Slack alert"""
        # Implementation
        pass
```

---

## Stage 5: Retirement

### 5.1 Model Retirement Process

```python
# retirement.py
class ModelRetirement:
    """Model retirement and decommissioning"""

    def __init__(self, model_name, model_registry):
        self.model_name = model_name
        self.registry = model_registry

    def check_retirement_criteria(self):
        """Check if model should be retired"""
        criteria = {
            'age': self._check_model_age(),
            'performance': self._check_performance_degradation(),
            'usage': self._check_usage_metrics(),
            'cost': self._check_cost_efficiency()
        }

        should_retire = any(criteria.values())

        return should_retire, criteria

    def _check_model_age(self):
        """Check if model is too old"""
        # Retire models older than 6 months
        from datetime import datetime, timedelta
        max_age = timedelta(days=180)

        # Get model deployment date
        # deployment_date = self.registry.get_deployment_date(self.model_name)
        # age = datetime.now() - deployment_date

        # return age > max_age
        return False  # Placeholder

    def _check_performance_degradation(self):
        """Check if performance degraded significantly"""
        # Compare current vs baseline performance
        current_accuracy = 0.85  # Example
        baseline_accuracy = 0.90

        degradation = (baseline_accuracy - current_accuracy) / baseline_accuracy

        return degradation > 0.10  # 10% degradation threshold

    def retire_model(self):
        """Retire model from production"""
        steps = [
            "1. Stop routing new traffic to model",
            "2. Complete ongoing requests",
            "3. Archive model artifacts",
            "4. Document retirement reason",
            "5. Update model registry"
        ]

        for step in steps:
            print(f"✅ {step}")

        print(f"🏁 Model {self.model_name} retired successfully")
```

---

## Production Checklist

### Pre-Deployment Checklist
- [ ] Model validated on test set
- [ ] Performance metrics meet thresholds
- [ ] A/B test completed and significant
- [ ] Canary deployment plan ready
- [ ] Rollback plan documented
- [ ] Monitoring dashboards configured
- [ ] Alert thresholds set
- [ ] Documentation updated
- [ ] Team notified of deployment

### Post-Deployment Checklist
- [ ] Canary traffic percentage
- [ ] Error rate within threshold
- [ ] Latency within SLA
- [ ] No critical alerts
- [ ] Automated tests passing
- [ ] Stakeholder sign-off
- [ ] Incident runbook updated

---

## Best Practices

1. **Automate Everything**: Manual processes fail
2. **Version Control**: Track all model versions
3. **Feature Store**: Centralize feature management
4. **Monitoring**: Real-time metrics and alerts
5. **Testing**: Comprehensive validation before deployment
6. **Rollback Plan**: Always have a rollback strategy
7. **Documentation**: Document every decision and process
8. **Team Communication**: Keep all stakeholders informed

---

## Related Resources

- **Next:** [6502: CI/CD for ML](./6502-CI-CD-for-ML.md)
- **Experiment:** [EXP_6501: MLOps Pipeline](../../experiments/EXP_6501_MLOPS_PIPELINE.md)
- **Lab:** [LAB-007: Production RAG](../../../learning-resources/labs/LAB-007-Production-RAG.md)


---

## Next Steps

- Continue with: **[6502: Next Document](./6502-CI-CD-Pipelines.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Status:** ✅ Complete
**Next Steps:** Implement CI/CD pipeline for automated deployment
