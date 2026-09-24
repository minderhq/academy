---
Document ID: 6502
Title: CI/CD for Machine Learning
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

# 6502: CI/CD for Machine Learning

**Project:** PROJECT-OMEGA
**Phase:** [6500] MLOps Pipelines
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2 hours

---

## Abstract

Continuous Integration and Continuous Deployment (CI/CD) pipeline specifically designed for machine learning models. This document covers automated training, testing, validation, and deployment of ML models.

---

## CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ML CI/CD Pipeline Architecture                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │          │    │          │    │          │    │          │        │
│  │   CODE   │───►│   BUILD  │───►│   TRAIN  │───►│   TEST   │        │
│  │  COMMIT  │    │          │    │          │    │          │        │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘        │
│       │              │              │              │                │
│       ▼              ▼              ▼              ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │  GitHub  │    │  Docker  │    │  MLflow  │    │  Model   │        │
│  │  Actions │    │  Build   │    │  Track   │    │ Validate │        │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘        │
│                                                     │                │
│                                                     ▼                │
│                                              ┌──────────┐           │
│                                              │  DEPLOY  │           │
│                                              │          │           │
│                                              ├──────────┤           │
│                                              │ Canary   │           │
│                                              │ Release  │           │
│                                              └──────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Configuration

### GitHub Actions Workflow

```yaml
# .github/workflows/ml-pipeline.yml
name: ML CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - 'models/**'
      - 'data/**'
      - 'training/**'
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  MODEL_NAME: sentiment-analyzer
  REGISTRY: ghcr.io

jobs:
  build-and-train:
    runs-on: [self-hosted, gpu]
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install mlflow boto3

      - name: Data validation
        run: |
          python scripts/validate_data.py

      - name: Train model
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_URI }}
        run: |
          python scripts/train.py \
            --data-dir data/ \
            --output-dir models/ \
            --experiment-name ${{ env.MODEL_NAME }}

      - name: Validate model
        run: |
          python scripts/validate_model.py \
            --model-path models/best_model.pkl \
            --test-data data/test.csv

      - name: Upload model artifacts
        uses: actions/upload-artifact@v3
        with:
          name: model-artifacts
          path: models/

  test-and-deploy:
    needs: build-and-train
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Download model artifacts
        uses: actions/download-artifact@v3
        with:
          name: model-artifacts

      - name: Run model tests
        run: |
          python tests/test_model.py

      - name: Build Docker image
        run: |
          docker build -t ${{ env.REGISTRY }}/${{ env.MODEL_NAME }}:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ${{ env.REGISTRY }}/${{ env.MODEL_NAME }}:${{ github.sha }}

      - name: Deploy to staging
        run: |
          kubectl set image deployment/${{ env.MODEL_NAME }} \
            ${{ env.MODEL_NAME }}=${{ env.REGISTRY }}/${{ env.MODEL_NAME }}:${{ github.sha }} \
            --namespace=staging

      - name: Run smoke tests
        run: |
          python tests/smoke_tests.py --environment staging

      - name: Promote to production
        if: success()
        run: |
          kubectl set image deployment/${{ env.MODEL_NAME }} \
            ${{ env.MODEL_NAME }}=${{ env.REGISTRY }}/${{ env.MODEL_NAME }}:${{ github.sha }} \
            --namespace=production
```

---

## Automated Training Pipeline

### Training Script

```python
# scripts/train.py
import argparse
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
import joblib

def train_model(data_dir, output_dir, experiment_name):
    """Train model with MLflow tracking"""

    # Load data
    train_data = pd.read_csv(f"{data_dir}/train.csv")
    val_data = pd.read_csv(f"{data_dir}/val.csv")

    X_train = train_data.drop('target', axis=1)
    y_train = train_data['target']
    X_val = val_data.drop('target', axis=1)
    y_val = val_data['target']

    # Start MLflow run
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run() as run:
        # Log parameters
        params = {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'random_state': 42
        }
        mlflow.log_params(params)

        # Train model
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)

        # Validate
        val_predictions = model.predict(X_val)
        val_accuracy = accuracy_score(y_val, val_predictions)

        # Log metrics
        mlflow.log_metric("val_accuracy", val_accuracy)

        # Log model
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name=experiment_name
        )

        # Save model locally
        joblib.dump(model, f"{output_dir}/best_model.pkl")

        # Generate classification report
        report = classification_report(y_val, val_predictions)
        mlflow.log_text(report, "classification_report.txt")

        print(f"✅ Model trained successfully")
        print(f"Validation Accuracy: {val_accuracy:.4f}")
        print(f"Run ID: {run.info.run_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--experiment-name", required=True)

    args = parser.parse_args()

    train_model(
        args.data_dir,
        args.output_dir,
        args.experiment_name
    )
```

### Data Validation Script

```python
# scripts/validate_data.py
import pandas as pd
import numpy as np
from pathlib import Path

class DataValidator:
    """Validate training data before model training"""

    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.errors = []
        self.warnings = []

    def validate(self):
        """Run all validation checks"""
        print("🔍 Starting data validation...")

        # Check file existence
        self._check_files()

        # Load and validate data
        train_data = pd.read_csv(self.data_path / "train.csv")
        val_data = pd.read_csv(self.data_path / "val.csv")

        self._check_schema(train_data, val_data)
        self._check_missing_values(train_data)
        self._check_class_distribution(train_data)
        self._check_data_leakage(train_data, val_data)

        # Generate report
        self._generate_report()

        return len(self.errors) == 0

    def _check_files(self):
        """Check if required files exist"""
        required_files = ["train.csv", "val.csv", "test.csv"]

        for file in required_files:
            file_path = self.data_path / file
            if not file_path.exists():
                self.errors.append(f"❌ Missing file: {file}")
            else:
                print(f"✅ Found: {file}")

    def _check_schema(self, train_data, val_data):
        """Check if train and validation schemas match"""
        if train_data.columns.tolist() != val_data.columns.tolist():
            self.errors.append("❌ Schema mismatch between train and val")
        else:
            print(f"✅ Schema consistent ({len(train_data.columns)} columns)")

    def _check_missing_values(self, data):
        """Check for missing values"""
        missing = data.isnull().sum()
        if missing.sum() > 0:
            self.warnings.append(f"⚠️ Missing values found: {missing[missing > 0].to_dict()}")
        else:
            print("✅ No missing values")

    def _check_class_distribution(self, data):
        """Check class distribution"""
        if 'target' in data.columns:
            class_dist = data['target'].value_counts(normalize=True)

            if class_dist.min() < 0.05:
                self.warnings.append(f"⚠️ Imbalanced classes: {class_dist.to_dict()}")
            else:
                print(f"✅ Balanced classes: {class_dist.to_dict()}")

    def _check_data_leakage(self, train_data, val_data):
        """Check for data leakage between train and validation"""
        train_ids = set(train_data.index) if 'id' in train_data.columns else set()
        val_ids = set(val_data.index) if 'id' in val_data.columns else set()

        overlap = train_ids & val_ids
        if overlap:
            self.errors.append(f"❌ Data leakage: {len(overlap)} samples in both train and val")
        else:
            print("✅ No data leakage detected")

    def _generate_report(self):
        """Generate validation report"""
        print("\n" + "="*50)
        print("DATA VALIDATION REPORT")
        print("="*50)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(error)

        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(warning)

        if not self.errors and not self.warnings:
            print("\n✅ All validation checks passed!")

        print("="*50)

if __name__ == "__main__":
    validator = DataValidator("data/")
    is_valid = validator.validate()

    if not is_valid:
        exit(1)
```

---

## Model Validation in Pipeline

### Automated Model Testing

```python
# tests/test_model.py
import pytest
import joblib
import pandas as pd
import numpy as np

class TestModel:
    """Automated model tests"""

    @pytest.fixture
    def model(self):
        """Load model for testing"""
        return joblib.load("models/best_model.pkl")

    @pytest.fixture
    def sample_data(self):
        """Load sample test data"""
        return pd.read_csv("data/test.csv")

    def test_model_loads(self, model):
        """Test that model can be loaded"""
        assert model is not None
        print("✅ Model loads successfully")

    def test_prediction_shape(self, model, sample_data):
        """Test prediction output shape"""
        X = sample_data.drop('target', axis=1)
        predictions = model.predict(X)

        assert len(predictions) == len(X)
        print(f"✅ Predictions shape correct: {predictions.shape}")

    def test_accuracy_threshold(self, model, sample_data):
        """Test model meets minimum accuracy"""
        X = sample_data.drop('target', axis=1)
        y = sample_data['target']

        accuracy = model.score(X, y)

        assert accuracy >= 0.85, f"Accuracy {accuracy:.3f} below threshold 0.85"
        print(f"✅ Accuracy {accuracy:.3f} meets threshold")

    def test_inference_speed(self, model, sample_data):
        """Test inference speed meets SLA"""
        import time

        X = sample_data.drop('target', axis=1).head(100)

        start = time.time()
        predictions = model.predict(X)
        latency = time.time() - start

        # SLA: < 1 second for 100 predictions
        assert latency < 1.0, f"Latency {latency:.3f}s exceeds SLA 1.0s"
        print(f"✅ Inference speed {latency*1000:.1f}ms meets SLA")

    def test_prediction_types(self, model, sample_data):
        """Test prediction output types"""
        X = sample_data.drop('target', axis=1)

        predictions = model.predict(X)
        probabilities = model.predict_proba(X)

        assert predictions.dtype in [np.int32, np.int64]
        assert probabilities.shape == (len(X), 2)
        assert np.allclose(probabilities.sum(axis=1), 1.0)
        print("✅ Prediction types correct")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### Smoke Tests

```python
# tests/smoke_tests.py
import requests
import argparse
import sys

class SmokeTests:
    """Smoke tests for deployed model"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0

    def run_all(self):
        """Run all smoke tests"""
        print(f"🧪 Running smoke tests against {self.base_url}")

        self.test_health()
        self.test_predict()
        self.test_batch_predict()
        self.test_model_info()

        self._print_summary()

        return self.failed == 0

    def test_health(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'

            print("✅ Health check passed")
            self.passed += 1
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            self.failed += 1

    def test_predict(self):
        """Test single prediction endpoint"""
        try:
            payload = {
                "text": "This is a test sentence for prediction"
            }

            response = requests.post(
                f"{self.base_url}/predict",
                json=payload,
                timeout=10
            )

            assert response.status_code == 200
            data = response.json()
            assert 'prediction' in data
            assert 'confidence' in data

            print("✅ Single prediction test passed")
            self.passed += 1
        except Exception as e:
            print(f"❌ Single prediction test failed: {e}")
            self.failed += 1

    def test_batch_predict(self):
        """Test batch prediction endpoint"""
        try:
            payload = {
                "texts": [
                    "First test sentence",
                    "Second test sentence",
                    "Third test sentence"
                ]
            }

            response = requests.post(
                f"{self.base_url}/batch_predict",
                json=payload,
                timeout=30
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data['predictions']) == 3

            print("✅ Batch prediction test passed")
            self.passed += 1
        except Exception as e:
            print(f"❌ Batch prediction test failed: {e}")
            self.failed += 1

    def test_model_info(self):
        """Test model info endpoint"""
        try:
            response = requests.get(f"{self.base_url}/model_info", timeout=5)

            assert response.status_code == 200
            data = response.json()
            assert 'model_name' in data
            assert 'version' in data
            assert 'trained_at' in data

            print(f"✅ Model info test passed (v{data['version']})")
            self.passed += 1
        except Exception as e:
            print(f"❌ Model info test failed: {e}")
            self.failed += 1

    def _print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"Smoke Tests: {self.passed}/{total} passed")

        if self.failed > 0:
            print(f"❌ {self.failed} tests failed")
            sys.exit(1)
        else:
            print(f"✅ All tests passed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", default="staging")

    args = parser.parse_args()

    urls = {
        "staging": "https://staging-api.example.com",
        "production": "https://api.example.com"
    }

    tests = SmokeTests(urls[args.environment])
    success = tests.run_all()

    sys.exit(0 if success else 1)
```

---

## Deployment Strategies

### Progressive Canary Deployment

```python
# deployment.py
import kubernetes
from kubernetes import client, config
from time import sleep
import requests

class ProgressiveCanary:
    """Progressive canary deployment manager"""

    def __init__(self, deployment_name, namespace):
        config.load_kube_config()
        self.apps_api = client.AppsV1Api()
        self.deployment_name = deployment_name
        self.namespace = namespace
        self.traffic_percentage = 0

    def start_canary(self, new_image):
        """Start canary deployment"""
        # Get current deployment
        deployment = self.apps_api.read_namespaced_deployment(
            name=self.deployment_name,
            namespace=self.namespace
        )

        # Create canary deployment
        canary_name = f"{self.deployment_name}-canary"

        canary_spec = deployment.spec
        canary_spec.template.spec.containers[0].image = new_image

        canary_deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=canary_name,
                namespace=self.namespace
            ),
            spec=canary_spec
        )

        # Create canary
        self.apps_api.create_namespaced_deployment(
            namespace=self.namespace,
            body=canary_deployment
        )

        print(f"✅ Canary deployment created: {canary_name}")

        # Progressive rollout
        self._progressive_rollout(canary_name)

    def _progressive_rollout(self, canary_name):
        """Progressively increase canary traffic"""
        stages = [0.10, 0.25, 0.50, 0.75, 1.00]

        for percentage in stages:
            print(f"📈 Increasing canary traffic to {percentage*100:.0f}%")

            # Update traffic split
            self._update_traffic_split(canary_name, percentage)

            # Monitor for 10 minutes
            if self._monitor_metrics(duration=600):
                print(f"✅ Stage {percentage*100:.0f}% passed")
            else:
                print(f"❌ Stage {percentage*100:.0f}% failed - rolling back")
                self._rollback()
                return

        # All stages passed - promote canary
        self._promote_canary(canary_name)

    def _update_traffic_split(self, canary_name, percentage):
        """Update traffic split between production and canary"""
        # Update service selector weights
        # Implementation depends on your service mesh
        pass

    def _monitor_metrics(self, duration):
        """Monitor metrics for duration"""
        end_time = time.time() + duration

        while time.time() < end_time:
            # Check error rate
            error_rate = self._get_error_rate()

            if error_rate > 0.05:  # 5% threshold
                return False

            # Check latency
            latency_p95 = self._get_latency_p95()

            if latency_p95 > 1000:  # 1 second threshold
                return False

            sleep(30)  # Check every 30 seconds

        return True

    def _rollback(self):
        """Rollback canary deployment"""
        canary_name = f"{self.deployment_name}-canary"

        self.apps_api.delete_namespaced_deployment(
            name=canary_name,
            namespace=self.namespace
        )

        print("⚠️ Rolled back to production")

    def _promote_canary(self, canary_name):
        """Promote canary to production"""
        # Update production deployment with new image
        print("🎉 Promoting canary to production")

        # Delete canary
        self.apps_api.delete_namespaced_deployment(
            name=canary_name,
            namespace=self.namespace
        )
```

---

## Best Practices

### CI/CD Pipeline Best Practices

1. **Fast Feedback**: Keep pipeline runs under 30 minutes
2. **Parallel Execution**: Run independent jobs in parallel
3. **Caching**: Cache dependencies and model artifacts
4. **Artifact Management**: Track all model versions
5. **Automated Testing**: Comprehensive test coverage
6. **Gradual Rollout**: Use canary deployments
7. **Monitoring**: Real-time metrics and alerts
8. **Rollback Plan**: Always have quick rollback

### Pipeline Optimization

```yaml
# Optimized pipeline with caching
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

- name: Cache model artifacts
  uses: actions/cache@v3
  with:
    path: models/
    key: model-${{ github.sha }}

- name: Run tests in parallel
  run: |
    pytest -n auto tests/  # Parallel execution

- name: Build GPU Docker image
  run: |
    docker build \
      --cache-from ${{ env.REGISTRY }}/${{ env.MODEL_NAME }}:latest \
      -t ${{ env.REGISTRY }}/${{ env.MODEL_NAME }}:${{ github.sha }} .
```

---

## Related Resources

- **Previous:** [6501: ML Lifecycle Management](./6501-ML-Lifecycle-Management.md)
- **Next:** [6503: Model Registry](./6503-Model-Registry.md)
- **Experiment:** [EXP_6501: MLOps Pipeline](../../experiments/EXP_6501_MLOPS_PIPELINE.md)


---

## Next Steps

- Phase 6 Complete! Next: **[Phase 7: Agents](../../phase7-agentic/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Status:** ✅ Complete
**Next Steps:** Implement model registry integration
