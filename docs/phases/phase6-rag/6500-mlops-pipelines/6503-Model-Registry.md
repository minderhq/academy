---
Document ID: 6503
Title: Model Registry
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

# 6503: Model Registry

**Project:** AI Engineering Curriculum
**Phase:** [6500] MLOps Pipelines
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2 hours

---

## Abstract

Model registry is the central repository for managing trained machine learning models. This document covers MLflow and Weights & Biases integration for version control, metadata tracking, and model deployment.

---

## Model Registry Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      Model Registry Architecture                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Model Registry Layer                          │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │                                                                  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │   │
│  │  │   Model    │  │   Model    │  │   Model    │  │   Model    │  │   │
│  │  │  Version   │  │  Version   │  │  Version   │  │  Version   │  │   │
│  │  │    1.0     │  │    1.1     │  │    2.0     │  │    2.1     │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │   │
│  │        │              │              │              │            │   │
│  │        └──────────────┴──────────────┴──────────────┘            │   │
│  │                             │                                 │   │
│  │  ┌────────────────────────────────────────────────────────┐   │   │
│  │  │              Model Metadata & Artifacts                │   │   │
│  │  │  - Performance metrics                                 │   │   │
│  │  │  - Training parameters                                 │   │   │
│  │  │  - Data lineage                                       │   │   │
│  │  │  - Deployment history                                  │   │   │
│  │  └────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 Backend Storage Options                         │   │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │                                                                  │   │
│  │  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐   │   │
│  │  │    MLflow     │      │   Weights &   │      │   DVC + S3    │   │   │
│  │  │  (Open Source)│      │  Biases       │      │  (Custom)     │   │   │
│  │  └──────────────┘      └──────────────┘      └──────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## MLflow Integration

### MLflow Setup

```python
# mlflow_setup.py
import mlflow
from mlflow.tracking import MlflowClient
import os

class MLflowSetup:
    """MLflow tracking server setup"""

    def __init__(self, tracking_uri, registry_uri):
        self.tracking_uri = tracking_uri
        self.registry_uri = registry_uri
        self.client = None

    def setup(self):
        """Initialize MLflow client"""
        # Set tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_registry_uri(self.registry_uri)

        # Initialize client
        self.client = MlflowClient()

        print(f"✅ MLflow connected to: {self.tracking_uri}")
        print(f"✅ Registry connected to: {self.registry_uri}")

        return self.client

# Usage
setup = MLflowSetup(
    tracking_uri="http://localhost:5000",
    registry_uri="http://localhost:5000"
)
client = setup.setup()
```

### Model Registration

```python
# model_registration.py
import mlflow
import mlflow.sklearn
from datetime import datetime
import json

class ModelRegistrar:
    """Register and manage models in MLflow"""

    def __init__(self, experiment_name, model_name):
        self.experiment_name = experiment_name
        self.model_name = model_name
        self.client = MlflowClient()

    def register_model(
        self,
        model,
        artifact_path,
        metrics,
        params,
        tags=None,
        stage="Staging"
    ):
        """Register model with metadata"""

        with mlflow.start_run() as run:
            # Log parameters
            mlflow.log_params(params)

            # Log metrics
            mlflow.log_metrics(metrics)

            # Log tags
            if tags:
                mlflow.set_tags(tags)

            # Log model
            mlflow.sklearn.log_model(
                model,
                artifact_path,
                registered_model_name=self.model_name
            )

            # Add description
            self._add_model_version_description(
                run.info.run_id,
                self._generate_description(metrics, params)
            )

            # Transition to stage
            model_version = self._get_latest_version()
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=model_version,
                stage=stage
            )

            print(f"✅ Model registered: {self.model_name} v{model_version}")
            print(f"✅ Stage: {stage}")

            return run.info.run_id, model_version

    def _get_latest_version(self):
        """Get latest model version"""
        versions = self.client.get_latest_versions(
            self.model_name,
            stages=["None"]
        )
        return versions[0].version if versions else None

    def _add_model_version_description(self, run_id, description):
        """Add description to model version"""
        model_version = self._get_latest_version()

        self.client.update_model_version(
            name=self.model_name,
            version=model_version,
            description=description
        )

    def _generate_description(self, metrics, params):
        """Generate model description"""
        desc = f"""
# Model Training Summary

**Training Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Performance Metrics
- Accuracy: {metrics.get('accuracy', 'N/A'):.4f}
- Precision: {metrics.get('precision', 'N/A'):.4f}
- Recall: {metrics.get('recall', 'N/A'):.4f}
- F1 Score: {metrics.get('f1', 'N/A'):.4f}

## Training Parameters
{json.dumps(params, indent=2)}

## Notes
This model was trained using the standard training pipeline.
        """
        return desc.strip()

    def promote_to_production(self, version, archive_current=True):
        """Promote model to production"""

        if archive_current:
            # Archive current production model
            self._archive_production_version()

        # Promote new version
        self.client.transition_model_version_stage(
            name=self.model_name,
            version=version,
            stage="Production"
        )

        print(f"✅ Model {self.model_name} v{version} promoted to Production")

    def _archive_production_version(self):
        """Archive current production model"""
        production_models = self.client.get_latest_versions(
            self.model_name,
            stages=["Production"]
        )

        for model in production_models:
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=model.version,
                stage="Archived"
            )

    def get_model_info(self, stage="Production"):
        """Get model information for stage"""
        models = self.client.get_latest_versions(
            self.model_name,
            stages=[stage]
        )

        if models:
            model = models[0]
            run = self.client.get_run(model.run_id)

            info = {
                'name': self.model_name,
                'version': model.version,
                'stage': stage,
                'run_id': model.run_id,
                'creation_timestamp': datetime.fromtimestamp(model.creation_timestamp / 1000),
                'metrics': run.data.metrics,
                'params': run.data.params,
                'tags': run.data.tags
            }

            return info

        return None
```

---

## Weights & Biases Integration

### W&B Setup

```python
# wandb_setup.py
import wandb
from wandb.keras import WandBMetricsCallback
import os

class WandBSetup:
    """Weights & Biases integration"""

    def __init__(self, project, entity=None):
        self.project = project
        self.entity = entity

    def init_run(self, config=None, tags=None):
        """Initialize W&B run"""
        run = wandb.init(
            project=self.project,
            entity=self.entity,
            config=config,
            tags=tags
        )

        print(f"✅ W&B run initialized: {run.url}")

        return run

    def log_model(self, model_path, model_name="model"):
        """Log model artifact to W&B"""
        artifact = wandb.Artifact(
            model_name,
            type="model"
        )
        artifact.add_file(model_path)

        wandb.log_artifact(artifact)

        print(f"✅ Model logged: {model_name}")

    def log_dataset(self, dataset_path, dataset_name="dataset"):
        """Log dataset artifact to W&B"""
        artifact = wandb.Artifact(
            dataset_name,
            type="dataset"
        )
        artifact.add_dir(dataset_path)

        wandb.log_artifact(artifact)

        print(f"✅ Dataset logged: {dataset_name}")

# Usage
wandb_setup = WandBSetup(project="sentiment-analysis")

run = wandb_setup.init_run(
    config={
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 10
    },
    tags=["baseline", "production"]
)
```

### W&B Model Registry

```python
# wandb_registry.py
import wandb
from pathlib import Path

class WandBModelRegistry:
    """Model registry using Weights & Biases"""

    def __init__(self, project, entity=None):
        self.project = project
        self.entity = entity

    def register_model(
        self,
        model_path,
        model_name,
        metrics,
        aliases=None
    ):
        """Register model in W&B"""

        # Create artifact
        artifact = wandb.Artifact(
            name=f"{model_name}:latest",
            type="model"
        )

        # Add model files
        if Path(model_path).is_dir():
            artifact.add_dir(model_path)
        else:
            artifact.add_file(model_path)

        # Log metrics
        wandb.log(metrics)

        # Save artifact
        wandb.log_artifact(artifact, aliases=aliases)

        print(f"✅ Model registered: {model_name}")

    def link_model_to_production(self, model_name, version):
        """Link model version to production stage"""

        # Get artifact
        api = wandb.Api()
        artifact = api.artifact(f"{self.project}/{model_name}:{version}")

        # Create production link
        artifact.aliases.append("production")
        artifact.save()

        print(f"✅ Model {model_name}:{version} linked to production")

    def get_production_model(self, model_name):
        """Get production model artifact"""

        api = wandb.Api()

        # Get latest production version
        artifacts = api.artifact_type(f"{self.project}/{model_name}", "model")
        production_artifact = None

        for artifact in artifacts.collections():
            if "production" in artifact.aliases:
                production_artifact = artifact
                break

        if production_artifact:
            # Download artifact
            downloaded_path = production_artifact.download()
            print(f"✅ Production model downloaded: {downloaded_path}")
            return downloaded_path

        return None
```

---

## Model Versioning Strategy

### Semantic Versioning for Models

```python
# versioning.py
from dataclasses import dataclass
from enum import Enum

class VersionChange(Enum):
    MAJOR = "major"  # Incompatible changes
    MINOR = "minor"  # New features, backward compatible
    PATCH = "patch"  # Bug fixes, backward compatible

@dataclass
class ModelVersion:
    """Semantic versioning for models"""
    major: int = 1
    minor: int = 0
    patch: int = 0

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def increment(self, change: VersionChange):
        """Increment version"""
        if change == VersionChange.MAJOR:
            self.major += 1
            self.minor = 0
            self.patch = 0
        elif change == VersionChange.MINOR:
            self.minor += 1
            self.patch = 0
        elif change == VersionChange.PATCH:
            self.patch += 1

        return self

class ModelVersionManager:
    """Manage model versions"""

    def __init__(self, model_name):
        self.model_name = model_name
        self.current_version = ModelVersion()

    def determine_version_change(
        self,
        old_model,
        new_model,
        performance_change
    ):
        """Determine version change type"""

        # Major version: Architecture change
        if self._architecture_changed(old_model, new_model):
            return VersionChange.MAJOR

        # Major version: Significant performance regression
        if performance_change < -0.05:
            return VersionChange.MAJOR

        # Minor version: Significant performance improvement
        if performance_change > 0.05:
            return VersionChange.MINOR

        # Minor version: New features added
        if self._features_added(old_model, new_model):
            return VersionChange.MINOR

        # Patch: Bug fix or small improvement
        return VersionChange.PATCH

    def _architecture_changed(self, old_model, new_model):
        """Check if model architecture changed"""
        # Compare model architectures
        old_params = old_model.get_params()
        new_params = new_model.get_params()

        # Check for significant architectural differences
        return old_params != new_params

    def _features_added(self, old_model, new_model):
        """Check if new features were added"""
        # Compare feature sets
        old_features = set(old_model.feature_names_in_)
        new_features = set(new_model.feature_names_in_)

        return len(new_features - old_features) > 0

    def register_new_version(
        self,
        model,
        metrics,
        change_type: VersionChange
    ):
        """Register new model version"""

        # Increment version
        self.current_version.increment(change_type)
        version_str = str(self.current_version)

        print(f"📦 Registering {self.model_name} v{version_str}")

        # Register with MLflow or W&B
        # Implementation...

        return version_str
```

---

## Model Metadata Management

### Metadata Schema

```python
# metadata.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List
import json

@dataclass
class ModelMetadata:
    """Comprehensive model metadata"""

    # Basic Info
    model_name: str
    version: str
    framework: str  # sklearn, tensorflow, pytorch

    # Training Info
    training_date: datetime
    training_duration_seconds: float
    training_samples: int
    validation_samples: int

    # Performance Metrics
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float = None

    # Model Parameters
    hyperparameters: Dict[str, Any]

    # Data Info
    feature_names: List[str]
    target_name: str
    data_hash: str  # For reproducibility

    # Deployment Info
    stage: str = "Development"  # Development, Staging, Production
    deployment_date: datetime = None
    endpoint_url: str = None

    # Monitoring
    drift_threshold: float = 0.05
    retraining_threshold: float = 0.90

    # Tags
    tags: List[str] = None

    # Notes
    notes: str = ""

    def to_dict(self):
        """Convert to dictionary"""
        data = asdict(self)
        data['training_date'] = self.training_date.isoformat()
        if self.deployment_date:
            data['deployment_date'] = self.deployment_date.isoformat()
        return data

    def to_json(self):
        """Convert to JSON"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str):
        """Create from JSON"""
        data = json.loads(json_str)
        data['training_date'] = datetime.fromisoformat(data['training_date'])
        if data.get('deployment_date'):
            data['deployment_date'] = datetime.fromisoformat(data['deployment_date'])
        return cls(**data)

class ModelMetadataRegistry:
    """Manage model metadata"""

    def __init__(self, storage_path="model_metadata.json"):
        self.storage_path = storage_path
        self.metadata_store = {}

    def register(self, metadata: ModelMetadata):
        """Register model metadata"""
        key = f"{metadata.model_name}_{metadata.version}"
        self.metadata_store[key] = metadata

        # Persist to disk
        self._save()

        print(f"✅ Metadata registered: {key}")

    def get(self, model_name: str, version: str) -> ModelMetadata:
        """Get model metadata"""
        key = f"{model_name}_{version}"
        return self.metadata_store.get(key)

    def list_versions(self, model_name: str) -> List[ModelMetadata]:
        """List all versions of a model"""
        versions = []

        for key, metadata in self.metadata_store.items():
            if metadata.model_name == model_name:
                versions.append(metadata)

        # Sort by version
        versions.sort(key=lambda m: m.version, reverse=True)

        return versions

    def get_production_model(self, model_name: str) -> ModelMetadata:
        """Get production model metadata"""
        versions = self.list_versions(model_name)

        for metadata in versions:
            if metadata.stage == "Production":
                return metadata

        return None

    def _save(self):
        """Save metadata to disk"""
        with open(self.storage_path, 'w') as f:
            json.dump({
                key: metadata.to_dict()
                for key, metadata in self.metadata_store.items()
            }, f, indent=2)

    def _load(self):
        """Load metadata from disk"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            self.metadata_store = {
                key: ModelMetadata.from_json(json.dumps(value))
                for key, value in data.items()
            }
        except FileNotFoundError:
            self.metadata_store = {}
```

---

## Production Deployment

### Load Model from Registry

```python
# load_model.py
import mlflow
import joblib
from typing import Union

class ModelLoader:
    """Load models from registry"""

    @staticmethod
    def load_production_model(model_name: str):
        """Load production model from MLflow"""

        # Get production model URI
        model_uri = f"models:/{model_name}/Production"

        # Load model
        model = mlflow.sklearn.load_model(model_uri)

        print(f"✅ Loaded production model: {model_name}")

        return model

    @staticmethod
    def load_staging_model(model_name: str):
        """Load staging model from MLflow"""

        model_uri = f"models:/{model_name}/Staging"
        model = mlflow.sklearn.load_model(model_uri)

        print(f"✅ Loaded staging model: {model_name}")

        return model

    @staticmethod
    def load_version(model_name: str, version: str):
        """Load specific model version"""

        model_uri = f"models:/{model_name}/{version}"
        model = mlflow.sklearn.load_model(model_uri)

        print(f"✅ Loaded model: {model_name} v{version}")

        return model

    @staticmethod
    def load_local_model(model_path: str):
        """Load model from local file"""

        model = joblib.load(model_path)

        print(f"✅ Loaded model from: {model_path}")

        return model
```

---

## Related Resources

- **Previous:** [6502: CI/CD for ML](./6502-CI-CD-for-ML.md)
- **Related:** [1502: Model Drift Detection](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md)
- **Experiment:** [EXP_6501: MLOps Pipeline](../../../../experiments/EXP_6501_MLOPS_PIPELINE.md)


---

## Next Steps

- Phase 6 Complete! Next: **[Phase 7: Agents](../../phase7-agentic/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Status:** ✅ Complete
**Next Steps:** Implement AI Security measures
