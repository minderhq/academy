---
Document ID: 2301
Title: Framework Design Patterns
Phase: 2
Module: 2300
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'architecture', 'api-design', 'production']
---

# 2301: Framework Design Patterns

**Project:** PROJECT-OMEGA
**Phase:** [2300] Framework Engineering
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2 hours

---

## Abstract

Machine learning frameworks require careful architectural design to ensure flexibility, maintainability, and scalability. This document covers essential design patterns used in production ML frameworks like HuggingFace Transformers, PyTorch Lightning, and LangChain.

**What you'll learn:**
- Model abstraction layers for framework-agnostic code
- Configuration management for reproducible experiments
- Plugin architectures for extensible systems
- Version handling for model compatibility

---

## Pattern Categories

ML frameworks typically use these architectural patterns:

### 1. Architectural Patterns
- **Model Abstraction Layer** - Unified interface across different implementations
- **Configuration Management** - Reproducible, versioned experiment configs
- **Plugin System** - Dynamic loading of custom components
- **Version Handler** - Model versioning and compatibility checking

### 2. Behavioral Patterns
- **Strategy Pattern** - Runtime algorithm selection
- **Factory Pattern** - Object creation encapsulation
- **Observer Pattern** - Event-driven training callbacks
- **Registry Pattern** - Component discovery and loading

---

## Pattern 1: Model Abstraction Layer

### Purpose

Different ML frameworks (PyTorch, TensorFlow, JAX) have different APIs. An abstraction layer provides a unified interface, allowing you to:
- Switch frameworks without changing application code
- Test different implementations easily
- Standardize model interfaces across your codebase

### Implementation

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import torch
import tensorflow as tf

class BaseModel(ABC):
    """
    Abstract base class defining the interface all models must implement.
    This allows framework-agnostic code.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None

    @abstractmethod
    def forward(self, x: Any) -> Any:
        """Forward pass through the model."""
        pass

    @abstractmethod
    def train_step(self, batch: Dict[str, Any]) -> Dict[str, float]:
        """
        Single training step.

        Returns:
            Dictionary with loss and metrics
        """
        pass

    @abstractmethod
    def save(self, path: str):
        """Save model checkpoint."""
        pass

    @abstractmethod
    def load(self, path: str):
        """Load model checkpoint."""
        pass

    @abstractmethod
    def to(self, device: str):
        """Move model to device (GPU/CPU)."""
        pass


# PyTorch Implementation
class PyTorchModel(BaseModel):
    """PyTorch-specific implementation of BaseModel."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Build PyTorch model
        self.model = self._build_model()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def _build_model(self) -> torch.nn.Module:
        """Build a simple neural network."""
        hidden_size = self.config.get("hidden_size", 256)
        num_layers = self.config.get("num_layers", 3)

        layers = []
        input_size = self.config["input_size"]

        for i in range(num_layers):
            layers.extend([
                torch.nn.Linear(input_size, hidden_size),
                torch.nn.ReLU(),
                torch.nn.Dropout(0.1)
            ])
            input_size = hidden_size

        layers.append(torch.nn.Linear(hidden_size, self.config["output_size"]))
        return torch.nn.Sequential(*layers)

    def forward(self, x: Any) -> Any:
        """Forward pass."""
        return self.model(x)

    def train_step(self, batch: Dict[str, Any]) -> Dict[str, float]:
        """Single training step."""
        self.model.train()
        self.optimizer.zero_grad()

        inputs = batch["inputs"].to(self.device)
        targets = batch["targets"].to(self.device)

        # Forward pass
        outputs = self.model(inputs)

        # Calculate loss
        loss_fn = torch.nn.MSELoss()
        loss = loss_fn(outputs, targets)

        # Backward pass
        loss.backward()
        self.optimizer.step()

        return {"loss": loss.item()}

    def save(self, path: str):
        """Save model."""
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "config": self.config,
        }, path)

    def load(self, path: str):
        """Load model."""
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.config = checkpoint["config"]

    def to(self, device: str):
        """Move to device."""
        self.device = torch.device(device)
        self.model.to(self.device)


# TensorFlow Implementation
class TensorFlowModel(BaseModel):
    """TensorFlow-specific implementation of BaseModel."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = self._build_model()
        self.optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)

    def _build_model(self) -> tf.keras.Model:
        """Build a simple neural network."""
        hidden_size = self.config.get("hidden_size", 256)
        num_layers = self.config.get("num_layers", 3)

        layers = []
        input_size = self.config["input_size"]

        for i in range(num_layers):
            layers.extend([
                tf.keras.layers.Dense(hidden_size, activation="relu"),
                tf.keras.layers.Dropout(0.1)
            ])

        layers.append(tf.keras.layers.Dense(self.config["output_size"]))
        return tf.keras.Sequential(layers)

    def forward(self, x: Any) -> Any:
        """Forward pass."""
        return self.model(x, training=False)

    def train_step(self, batch: Dict[str, Any]) -> Dict[str, float]:
        """Single training step (TensorFlow 2.x style)."""
        inputs = batch["inputs"]
        targets = batch["targets"]

        with tf.GradientTape() as tape:
            predictions = self.model(inputs, training=True)
            loss = tf.keras.losses.MSE(targets, predictions)

        gradients = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.model.trainable_variables))

        return {"loss": loss.numpy()}

    def save(self, path: str):
        """Save model."""
        self.model.save_weights(path)

    def load(self, path: str):
        """Load model."""
        self.model.load_weights(path)

    def to(self, device: str):
        """TensorFlow handles device placement automatically."""
        # In TF, device placement is handled by context managers
        pass


# Framework-Agnostic Training Function
def train_model(model: BaseModel, train_data, num_epochs: int):
    """
    Train any model implementing BaseModel interface.

    This function doesn't care if it's PyTorch, TensorFlow, or JAX!
    """
    for epoch in range(num_epochs):
        total_loss = 0
        num_batches = 0

        for batch in train_data:
            result = model.train_step(batch)
            total_loss += result["loss"]
            num_batches += 1

        avg_loss = total_loss / num_batches
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")


# Usage Example - Framework Agnostic!
if __name__ == "__main__":
    config = {
        "input_size": 784,
        "hidden_size": 256,
        "num_layers": 3,
        "output_size": 10,
    }

    # Switch between frameworks by changing ONE line!
    use_pytorch = True

    if use_pytorch:
        model = PyTorchModel(config)
    else:
        model = TensorFlowModel(config)

    # Training works identically!
    # train_model(model, train_dataloader, num_epochs=10)
```

### Benefits

1. **Flexibility** - Switch frameworks without rewriting training code
2. **Testing** - Mock models for unit tests
3. **Collaboration** - Team members can use different frameworks
4. **Production** - Easy A/B testing of different implementations

### Real-World Example: HuggingFace

```python
# HuggingFace uses this pattern
from transformers import PreTrainedModel

class PreTrainedModel(ABC):
    # All models inherit from this
    @abstractmethod
    def forward(self, *args, **kwargs):
        pass

# Specific implementations
class BertModel(PreTrainedModel):
    def forward(self, *args, **kwargs):
        # BERT-specific forward
        pass

class GPT2Model(PreTrainedModel):
    def forward(self, *args, **kwargs):
        # GPT-2-specific forward
        pass
```

---

## Pattern 2: Configuration Management

### Purpose

Reproducible experiments require:
- Versioned configuration files
- Easy parameter tuning
- Clear documentation of hyperparameters
- Validation of configuration values

### Implementation

```python
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import yaml
import json
from pathlib import Path
from enum import Enum


class ActivationType(str, Enum):
    """Supported activation functions."""
    RELU = "relu"
    GELU = "gelu"
    SILU = "silu"
    TANH = "tanh"


class OptimizerType(str, Enum):
    """Supported optimizers."""
    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"
    ADAGRAD = "adagrad"


@dataclass
class ModelConfig:
    """
    Model configuration with validation and serialization.

    This class ensures:
    1. Type safety
    2. Default values
    3. Easy serialization
    4. Validation
    """

    # Model architecture
    input_size: int
    hidden_size: int = 256
    num_layers: int = 3
    output_size: int = 10
    activation: ActivationType = ActivationType.RELU
    dropout: float = 0.1

    # Training parameters
    learning_rate: float = 0.001
    batch_size: int = 32
    num_epochs: int = 10
    optimizer: OptimizerType = OptimizerType.ADAM

    # Regularization
    weight_decay: float = 0.0001
    label_smoothing: float = 0.0

    # Optional parameters
    seed: Optional[int] = None
    mixed_precision: bool = False
    gradient_clip_value: Optional[float] = None

    # Metadata
    experiment_name: str = "baseline"
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate configuration values."""
        if self.hidden_size <= 0:
            raise ValueError(f"hidden_size must be positive, got {self.hidden_size}")

        if self.num_layers <= 0:
            raise ValueError(f"num_layers must be positive, got {self.num_layers}")

        if not 0 <= self.dropout <= 1:
            raise ValueError(f"dropout must be in [0, 1], got {self.dropout}")

        if self.learning_rate <= 0:
            raise ValueError(f"learning_rate must be positive, got {self.learning_rate}")

        if self.batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {self.batch_size}")

    @classmethod
    def from_yaml(cls, path: str) -> "ModelConfig":
        """
        Load configuration from YAML file.

        Example YAML:
        ```yaml
        input_size: 784
        hidden_size: 512
        num_layers: 4
        activation: gelu
        dropout: 0.2
        learning_rate: 0.0001
        ```
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        # Convert string enums to actual enums
        if "activation" in data:
            data["activation"] = ActivationType(data["activation"])
        if "optimizer" in data:
            data["optimizer"] = OptimizerType(data["optimizer"])

        return cls(**data)

    def to_yaml(self, path: str):
        """Save configuration to YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert enums to strings for YAML
        data = asdict(self)
        if isinstance(self.activation, ActivationType):
            data["activation"] = self.activation.value
        if isinstance(self.optimizer, OptimizerType):
            data["optimizer"] = self.optimizer.value

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_json(cls, path: str) -> "ModelConfig":
        """Load configuration from JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = json.load(f)

        if "activation" in data:
            data["activation"] = ActivationType(data["activation"])
        if "optimizer" in data:
            data["optimizer"] = OptimizerType(data["optimizer"])

        return cls(**data)

    def to_json(self, path: str):
        """Save configuration to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)
        if isinstance(self.activation, ActivationType):
            data["activation"] = self.activation.value
        if isinstance(self.optimizer, OptimizerType):
            data["optimizer"] = self.optimizer.value

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if isinstance(self.activation, ActivationType):
            data["activation"] = self.activation.value
        if isinstance(self.optimizer, OptimizerType):
            data["optimizer"] = self.optimizer.value
        return data

    def update(self, **kwargs):
        """
        Create a new config with updated values.

        Example:
            new_config = config.update(learning_rate=0.0001, hidden_size=512)
        """
        data = self.to_dict()
        data.update(kwargs)

        # Convert back to enums
        if "activation" in data:
            data["activation"] = ActivationType(data["activation"])
        if "optimizer" in data:
            data["optimizer"] = OptimizerType(data["optimizer"])

        return ModelConfig(**data)

    def __str__(self) -> str:
        """Pretty print configuration."""
        lines = ["ModelConfig:"]
        for key, value in self.to_dict().items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)


# Usage Examples
if __name__ == "__main__":
    # Create config programmatically
    config1 = ModelConfig(
        input_size=784,
        hidden_size=512,
        num_layers=4,
        activation=ActivationType.GELU,
        learning_rate=0.0001,
    )

    # Save to YAML
    config1.to_yaml("configs/model.yaml")

    # Load from YAML
    config2 = ModelConfig.from_yaml("configs/model.yaml")

    # Update specific parameters
    config3 = config2.update(learning_rate=0.00001, batch_size=64)

    # Save to JSON
    config3.to_json("configs/model.json")

    # Print config
    print(config3)
```

### Best Practices

1. **Store configs separately from code** - Use `configs/` directory
2. **Version control configs** - Track experiments with git
3. **Document parameters** - Add docstrings explaining each parameter
4. **Validate on load** - Catch errors early
5. **Use meaningful defaults** - Start with sensible values

### Real-World Example: HuggingFace

```python
# HuggingFace uses this pattern
from transformers import TrainingArguments

args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    learning_rate=2e-5,
    # ... many more parameters
)

# Save/load
args.to_json("config.json")
args = TrainingArguments.from_json("config.json")
```

---

## Pattern 3: Plugin Architecture

### Purpose

ML frameworks need to be extensible:
- Custom layer types
- Different optimizers
- Data augmentation strategies
- Loss functions
- Metrics

A plugin system allows dynamic loading without modifying core code.

### Implementation

```python
from typing import Dict, Type, Callable, Any, Optional
import inspect
from pathlib import Path
import importlib.util


class PluginRegistry:
    """
    Registry for managing plugin components.

    Supports:
    - Decorator-based registration
    - Dynamic loading from files
    - Plugin discovery
    - Dependency management
    """

    def __init__(self, name: str):
        self.name = name
        self._plugins: Dict[str, Type] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, name: Optional[str] = None, **metadata):
        """
        Decorator for registering plugins.

        Usage:
            @registry.register("my_plugin", version="1.0")
            class MyPlugin:
                pass
        """
        def decorator(plugin_class: Type) -> Type:
            plugin_name = name or plugin_class.__name__

            if plugin_name in self._plugins:
                raise ValueError(f"Plugin '{plugin_name}' already registered")

            self._plugins[plugin_name] = plugin_class
            self._metadata[plugin_name] = metadata

            return plugin_class

        return decorator

    def get(self, name: str) -> Optional[Type]:
        """Get plugin by name."""
        return self._plugins.get(name)

    def create(self, name: str, *args, **kwargs):
        """Create instance of plugin."""
        plugin_class = self.get(name)
        if plugin_class is None:
            raise ValueError(f"Plugin '{name}' not found")
        return plugin_class(*args, **kwargs)

    def list_all(self) -> list:
        """List all registered plugins."""
        return list(self._plugins.keys())

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get plugin metadata."""
        return self._metadata.get(name, {})

    def unregister(self, name: str):
        """Remove plugin from registry."""
        if name in self._plugins:
            del self._plugins[name]
            del self._metadata[name]

    def load_from_file(self, path: str):
        """
        Load plugins from a Python file.

        The file should contain plugins registered with the @registry.register decorator.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {path}")

        # Import the module
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin from {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Plugins are automatically registered via decorators


# Global registries for different plugin types
LAYER_REGISTRY = PluginRegistry("layers")
OPTIMIZER_REGISTRY = PluginRegistry("optimizers")
LOSS_REGISTRY = PluginRegistry("losses")
METRIC_REGISTRY = PluginRegistry("metrics")


# Example: Layer Plugins
@LAYER_REGISTRY.register("attention", version="1.0", author="Your Name")
class AttentionLayer:
    """Multi-head attention layer plugin."""

    def __init__(self, d_model: int, num_heads: int):
        self.d_model = d_model
        self.num_heads = num_heads
        # Implementation...

    def __call__(self, x):
        # Forward pass
        return x


@LAYER_REGISTRY.register("lstm", version="1.0", author="Your Name")
class LSTMLayer:
    """LSTM layer plugin."""

    def __init__(self, hidden_size: int, num_layers: int = 1):
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        # Implementation...

    def __call__(self, x):
        # Forward pass
        return x


# Example: Optimizer Plugins
@OPTIMIZER_REGISTRY.register("custom_adam", version="1.0")
class CustomAdamOptimizer:
    """Custom Adam optimizer with special features."""

    def __init__(self, lr: float = 0.001, beta1: float = 0.9, beta2: float = 0.999):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        # Implementation...

    def step(self, params, grads):
        # Update parameters
        pass


# Example: Loss Plugins
@LOSS_REGISTRY.register("focal_loss", version="1.0")
class FocalLoss:
    """Focal loss for imbalanced classification."""

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        self.alpha = alpha
        self.gamma = gamma

    def __call__(self, predictions, targets):
        # Calculate focal loss
        pass


# Usage in a Framework
class ModelBuilder:
    """
    Build models using registered plugins.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def build_layer(self, layer_type: str, **kwargs):
        """Build layer from registry."""
        return LAYER_REGISTRY.create(layer_type, **kwargs)

    def build_optimizer(self, optimizer_type: str, **kwargs):
        """Build optimizer from registry."""
        return OPTIMIZER_REGISTRY.create(optimizer_type, **kwargs)

    def build_loss(self, loss_type: str, **kwargs):
        """Build loss function from registry."""
        return LOSS_REGISTRY.create(loss_type, **kwargs)


# Example Usage
if __name__ == "__main__":
    # List available plugins
    print("Available layers:", LAYER_REGISTRY.list_all())
    print("Available optimizers:", OPTIMIZER_REGISTRY.list_all())

    # Build model with plugins
    builder = ModelBuilder({})

    # Create attention layer
    attention = builder.build_layer("attention", d_model=512, num_heads=8)
    print(f"Created: {attention.__class__.__name__}")

    # Create LSTM layer
    lstm = builder.build_layer("lstm", hidden_size=256)
    print(f"Created: {lstm.__class__.__name__}")

    # Load plugins from external file
    # LAYER_REGISTRY.load_from_file("custom_layers.py")
```

### Real-World Example: LangChain

```python
# LangChain uses plugin pattern for tools
from langchain.tools import BaseTool
from langchain_core.tools import tool

@tool
def search_api(query: str) -> str:
    """Search the API for query."""
    # Implementation
    return "results"

# Tool is automatically registered
# Can be discovered and used dynamically
```

---

## Pattern 4: Version Handler

### Purpose

Model versioning ensures:
- Backward compatibility
- Graceful degradation
- Clear migration paths
- Reproducibility

### Implementation

```python
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from packaging import version
import json
from pathlib import Path


@dataclass
class ModelVersion:
    """Represents a model version with compatibility info."""
    version: str
    compatible_frameworks: Dict[str, str]  # framework -> min_version
    breaking_changes: List[str]
    features: List[str]
    deprecation_warnings: Optional[List[str]] = None


class VersionManager:
    """
    Manage model versions and compatibility.

    Handles:
    - Version checking
    - Compatibility validation
    - Migration between versions
    - Deprecation warnings
    """

    def __init__(self):
        self.versions: Dict[str, ModelVersion] = {}
        self._load_versions()

    def _load_versions(self):
        """Load version information."""
        # Define available versions
        self.versions = {
            "1.0": ModelVersion(
                version="1.0",
                compatible_frameworks={
                    "pytorch": ">=2.0",
                    "tensorflow": ">=2.12",
                },
                breaking_changes=[],
                features=["basic_training", "evaluation"],
            ),
            "2.0": ModelVersion(
                version="2.0",
                compatible_frameworks={
                    "pytorch": ">=2.1",
                    "tensorflow": ">=2.13",
                },
                breaking_changes=[
                    "changed config format",
                    "removed old optimizer API",
                ],
                features=["basic_training", "evaluation", "mixed_precision"],
                deprecation_warnings=[
                    "Old config format deprecated in v3.0"
                ],
            ),
            "3.0": ModelVersion(
                version="3.0",
                compatible_frameworks={
                    "pytorch": ">=2.2",
                    "tensorflow": ">=2.14",
                },
                breaking_changes=[
                    "new checkpoint format",
                    "changed model.save() signature",
                ],
                features=["basic_training", "evaluation", "mixed_precision", "distributed"],
            ),
        }

    def get_version(self, version: str) -> Optional[ModelVersion]:
        """Get version info."""
        return self.versions.get(version)

    def check_compatibility(self, model_version: str, framework: str, fw_version: str) -> Tuple[bool, List[str]]:
        """
        Check if framework version is compatible with model version.

        Returns:
            (is_compatible, list_of_issues)
        """
        model_ver = self.get_version(model_version)
        if model_ver is None:
            return False, [f"Unknown model version: {model_version}"]

        if framework not in model_ver.compatible_frameworks:
            return False, [f"Framework {framework} not supported for model version {model_version}"]

        required_ver = model_ver.compatible_frameworks[framework]

        # Parse version requirement
        if required_ver.startswith(">="):
            min_ver = required_ver[2:]
            if version.parse(fw_version) < version.parse(min_ver):
                return False, [
                    f"Framework version {fw_version} is less than required {min_ver}"
                ]

        issues = []
        if model_ver.deprecation_warnings:
            issues.extend(model_ver.deprecation_warnings)

        return True, issues

    def get_migration_guide(self, from_version: str, to_version: str) -> Optional[str]:
        """Get migration guide between versions."""
        # In a real system, this would load from markdown files
        migrations = {
            ("1.0", "2.0"): """
## Migration Guide: 1.0 → 2.0

### Breaking Changes

1. **Config Format Changed**
   Old format:
   ```yaml
   hidden_size: 256
   ```

   New format:
   ```yaml
   model:
     hidden_size: 256
   ```

2. **Optimizer API Changed**
   Old: `optimizer.optimize(model, loss)`
   New: `optimizer.step(loss, model)`

### Migration Steps

1. Update config files
2. Update optimizer calls
3. Run test suite

### Rolling Back

If issues occur, downgrade with:
```bash
pip install ml-framework==1.0.0
```
            """,
            ("2.0", "3.0"): """
## Migration Guide: 2.0 → 3.0

### Breaking Changes

1. **New Checkpoint Format**
   Old: `model.save("checkpoint.pt")`
   New: `model.save_checkpoint("checkpoint/", metadata={})`

2. **Model.save() Signature Changed**
   Additional required parameter: `metadata`

### Migration Steps

1. Update save/load calls
2. Convert old checkpoints using included script
3. Update any custom model classes

### Auto-Migration

Use included migration tool:
```bash
ml-framework migrate --from 2.0 --to 3.0 checkpoints/
```
            """
        }

        return migrations.get((from_version, to_version))

    def recommend_version(self, framework: str, fw_version: str) -> str:
        """Recommended model version for given framework."""
        # Find latest compatible version
        for ver in sorted(self.versions.keys(), reverse=True):
            compatible, _ = self.check_compatibility(ver, framework, fw_version)
            if compatible:
                return ver
        return "1.0"  # Fallback


class VersionedModel:
    """
    Model with built-in version handling.
    """

    MODEL_VERSION = "3.0"

    def __init__(self, config: Dict, framework: str = "pytorch"):
        self.config = config
        self.framework = framework
        self.version_manager = VersionManager()

        # Check compatibility
        import torch
        fw_version = torch.__version__
        compatible, issues = self.version_manager.check_compatibility(
            self.MODEL_VERSION,
            framework,
            fw_version
        )

        if not compatible:
            raise RuntimeError(f"Compatibility issues: {issues}")

        # Print warnings
        for issue in issues:
            print(f"WARNING: {issue}")

    def save(self, path: str):
        """Save with version metadata."""
        checkpoint = {
            "model_version": self.MODEL_VERSION,
            "framework": self.framework,
            "config": self.config,
            "state": self._get_state(),
        }

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(checkpoint, f, indent=2)

    def _get_state(self) -> Dict:
        """Get model state for saving."""
        # Return model weights, etc.
        return {}

    @classmethod
    def load(cls, path: str):
        """Load with version checking."""
        with open(path) as f:
            checkpoint = json.load(f)

        model_version = checkpoint.get("model_version", "unknown")

        # Check if we need migration
        if model_version != cls.MODEL_VERSION:
            print(f"WARNING: Loading model version {model_version} into {cls.MODEL_VERSION}")
            print("Consider running migration tool")

        return cls.from_checkpoint(checkpoint)

    @classmethod
    def from_checkpoint(cls, checkpoint: Dict):
        """Create model from checkpoint."""
        return cls(checkpoint["config"])


# Usage Example
if __name__ == "__main__":
    # Check compatibility
    vm = VersionManager()

    compatible, issues = vm.check_compatibility("3.0", "pytorch", "2.3.0")
    print(f"Compatible: {compatible}, Issues: {issues}")

    # Get migration guide
    guide = vm.get_migration_guide("2.0", "3.0")
    if guide:
        print(guide)

    # Save versioned model
    model = VersionedModel(config={}, framework="pytorch")
    model.save("model_checkpoint.json")
```

---

## Exercise: Build Your Own Framework

Now it's your turn to apply these patterns!

### Task

Create a mini ML framework with:
1. Model abstraction layer (BaseModel class)
2. Configuration management (ModelConfig class)
3. One plugin type (custom metrics)

### Starter Code

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

# TODO: Implement BaseModel
class BaseModel(ABC):
    @abstractmethod
    def forward(self, x):
        pass

    @abstractmethod
    def train_step(self, batch):
        pass

# TODO: Implement ModelConfig
@dataclass
class ModelConfig:
    pass

# TODO: Implement metric registry
METRIC_REGISTRY = {}

# TODO: Register 2 metrics
# 1. Accuracy metric
# 2. F1 score metric
```

### Requirements

1. **BaseModel** should have:
   - `forward()` method
   - `train_step()` method
   - `save()` and `load()` methods

2. **ModelConfig** should have:
   - At least 5 model parameters
   - `to_yaml()` and `from_yaml()` methods
   - Validation in `__post_init__()`

3. **Metric Registry** should have:
   - `register()` decorator
   - `get()` method
   - `list_all()` method
   - At least 2 metrics registered

### Expected Output

```python
# Should work like this:

# Create config
config = ModelConfig(input_size=784, hidden_size=256, num_layers=3)
config.to_yaml("config.yaml")

# Create model
model = MyModel(config)

# Use metrics
accuracy = METRIC_REGISTRY.get("accuracy")
result = accuracy(predictions, targets)
```

### Solution Reference

See: [2306: Building Production Framework](./guides/2306-Building-Production-Framework.md) for complete solution.

---

## Related Topics

- [2302: Model Serving Architectures](./2302-Model-Serving-Architectures.md) - Build on these patterns
- [2201: PyTorch Computational Graphs](../2200-frameworks/2201-PyTorch-Computational-Graphs.md) - Framework internals
- [2203: CUDA Kernels](../2200-frameworks/2203-CUDA-Kernel-Syb-Level.md) - Low-level optimization
- [EXP_2201: PyTorch Framework Experiment](../../../../experiments/EXP_2201_PYTORCH_GRAPHS.md) - Hands-on practice

---

## Summary

**Key Takeaways:**

1. **Model Abstraction** - Write framework-agnostic code
2. **Configuration Management** - Reproducible experiments
3. **Plugin Architecture** - Extensible systems
4. **Version Handling** - Manage model compatibility

**Real-World Frameworks Using These Patterns:**
- HuggingFace Transformers (model abstraction + configs)
- PyTorch Lightning (abstraction + plugins)
- LangChain (plugins + versioning)
- FastAPI (plugin middlewares)

---

## Next Steps

- Continue with: **[2302: Model Serving Architectures](./2302-Model-Serving-Architectures.md)**
- Practical: **[LAB-007: Production RAG](../../../learning-resources/labs/LAB-007-Production-RAG.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Key Takeaways:**

1. **Model Abstraction** - Write framework-agnostic code
2. **Configuration Management** - Reproducible experiments
3. **Plugin Architecture** - Extensible systems
4. **Version Handling** - Manage model compatibility

**Real-World Frameworks Using These Patterns:**
- HuggingFace Transformers (model abstraction + configs)
- PyTorch Lightning (abstraction + plugins)
- LangChain (plugins + versioning)
- FastAPI (plugin middlewares)
