---
Document ID: 6503
Title: Model Registry
Phase: 6
Module: 6500
Last Updated: 2026-09-26
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['mlops', 'model-registry', 'versioning', 'aliases', 'lifecycle']
---

# 6503: Model Registry

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Model Registry Architecture](#model-registry-architecture)
- [Model Versioning Strategy](#model-versioning-strategy)
- [Model Metadata Management](#model-metadata-management)
- [Registry Aliases](#registry-aliases)
- [MLflow Integration](#mlflow-integration)
- [Weights & Biases Integration](#weights--biases-integration)
- [Production Deployment](#production-deployment)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain what a model registry adds over a folder of checkpoints: identity, lineage, and a promotion workflow
- Map training changes to MAJOR/MINOR/PATCH bumps with an explicit, mechanical decision rule
- Sort and compare version strings correctly using tuple semantics, not lexicographic order
- Promote and roll back models with aliases - one auditable write, no stage ceremony
- Persist model metadata so any registered version is auditable and reproducible
- Map registry concepts onto MLflow and Weights & Biases, and load production models through alias URIs

---

## Abstract

A model registry is the versioned, queryable index between training and serving. It gives every trained model a stable identity (name + version), attaches the metadata needed to audit it (metrics, parameters, data lineage), and provides a promotion mechanism that decides which version production traffic actually sees. This lesson builds the core registry mechanics in plain Python - version bumps, alias resolution, metadata persistence - then maps them onto the two tools you will meet in practice: MLflow and Weights & Biases.

---

## Model Registry Architecture

A shared folder of checkpoints answers none of the operational questions: which artifact is serving traffic, what data trained it, what score did it get, and how do we go back one step safely. The registry answers all four with three layers:

```text
   training job                MODEL REGISTRY                  consumers
 (run_id, params,       +----------------------------+      resolve at load:
  metrics) -----------> | versions : v1  v2  v3      | -----> models:/name@champion
                        |            (immutable)     |
                        | metadata : metrics,        |        promotion:
                        |            params,         | -----> one auditable alias
                        |            data lineage    |        write; versions stay
                        | aliases  : champion -> v3  |        untouched
                        |            challenger -> 2 |
                        +----------------------------+
```

- **Versions are immutable.** Registering produces a new version; nothing overwrites an existing one. History stays reconstructable.
- **Metadata rides with the version.** Metrics, hyperparameters, and the training run ID that produced it - stored once, queried later during audits and incident reviews.
- **Aliases are the only mutable part.** A named reference (`champion`, `challenger`, `production`) points at one version at a time. Consumers resolve through the alias, so promotion and rollback never require touching consumer code.

Backend options in practice: an MLflow tracking server (open source, self-hosted), the Weights & Biases registry (managed), or a custom store (DVC or S3 plus a metadata database) when neither fits. The mechanics this lesson simulates - versions, metadata, aliases - are the same in all three.

---

## Model Versioning Strategy

Semantic versioning maps cleanly onto model changes: **MAJOR** for an incompatible change (different architecture or estimator family, or a large quality regression), **MINOR** for a backward-compatible improvement (a new feature, a solid metric gain), **PATCH** for fixes that should not move the needle. The exact thresholds are a team convention - what matters is that the decision is mechanical, not vibes:

```python
from dataclasses import dataclass
from enum import Enum

class Change(Enum):
    MAJOR = "major"   # architecture changed, or a large regression
    MINOR = "minor"   # significant improvement, or a new feature
    PATCH = "patch"   # bug fixes and small tweaks

@dataclass
class ModelVersion:
    major: int = 1
    minor: int = 0
    patch: int = 0

    def __str__(self):
        return "%d.%d.%d" % (self.major, self.minor, self.patch)

    def bump(self, change):
        if change is Change.MAJOR:
            self.major, self.minor, self.patch = self.major + 1, 0, 0
        elif change is Change.MINOR:
            self.minor, self.patch = self.minor + 1, 0
        else:
            self.patch += 1
        return str(self)

def decide_change(old, new, delta):
    """old/new are model specs; delta is the validation-score change."""
    if old["params"] != new["params"]:
        return Change.MAJOR          # different estimator family or layout
    if delta < -0.05:
        return Change.MAJOR          # too big a regression to hide in a patch
    if delta > 0.05 or (new["features"] - old["features"]):
        return Change.MINOR
    return Change.PATCH

baseline = {"params": {"model": "logreg", "hidden": 128},
            "features": {"text_len", "lexicon_score"}}
swapped = {"params": {"model": "mlp", "hidden": 256},
           "features": {"text_len", "lexicon_score"}}
augmented = {"params": baseline["params"],
             "features": {"text_len", "lexicon_score", "bigram_counts"}}

scenarios = [
    ("bug fix, same spec, +0.001", baseline, baseline, 0.001),
    ("new feature added, +0.002", baseline, augmented, 0.002),
    ("architecture swap, +0.030", baseline, swapped, 0.030),
    ("same spec, -0.120 regression", baseline, baseline, -0.120),
]

v = ModelVersion()
print("registry head starts at", v)
for label, old, new, delta in scenarios:
    c = decide_change(old, new, delta)
    print("  %-32s %-6s -> %s" % (label, c.value, v.bump(c)))
print("final head:", v)
```

**Output:**

```text
registry head starts at 1.0.0
  bug fix, same spec, +0.001       patch  -> 1.0.1
  new feature added, +0.002        minor  -> 1.1.0
  architecture swap, +0.030        major  -> 2.0.0
  same spec, -0.120 regression     major  -> 3.0.0
final head: 3.0.0
```

The decision rule runs before registration, so the version history itself documents what changed and why. Note that the architecture swap bumps MAJOR even though the score improved - a different estimator family is a different contract, and anything downstream (feature expectations, latency profile, monitoring thresholds) may need to change with it.

One classic pitfall when you handle version strings yourself: registry versions sort badly as strings. String comparison orders `1.10.0` before `1.2.0`, because `1` sorts before `2` character by character. Compare as tuples of integers instead:

```python
versions = ["1.0.0", "1.2.0", "1.10.0", "1.9.2", "2.0.0"]

def semver_key(v):
    """'1.10.0' -> (1, 10, 0): tuple comparison is numeric per field."""
    return tuple(int(part) for part in v.split("."))

lex = sorted(versions)
semantic = sorted(versions, key=semver_key)
print("lexicographic (string) order:", ", ".join(lex))
print("  '1.10.0' lands before '1.2.0' - string order, not version order")
print("semantic (tuple) order:       ", ", ".join(semantic))
print("is 1.10.0 newer than 1.9.2:", semver_key("1.10.0") > semver_key("1.9.2"))
```

**Output:**

```text
lexicographic (string) order: 1.0.0, 1.10.0, 1.2.0, 1.9.2, 2.0.0
  '1.10.0' lands before '1.2.0' - string order, not version order
semantic (tuple) order:        1.0.0, 1.2.0, 1.9.2, 1.10.0, 2.0.0
is 1.10.0 newer than 1.9.2: True
```

Any tooling that ranks registered versions - "give me the newest", "is B newer than A" - must use the tuple key. Real registries store versions as integers (MLflow) or ordered indexes (W&B) precisely to avoid this trap.

---

## Model Metadata Management

The version number says *that* something changed; the metadata says *what*. A registration without metadata is a mystery artifact: six months later nobody can answer "which data produced this" or "why did we trust it". Store enough to reproduce and audit the model, and persist it durably - the registry's file (or database row) must survive the process that created it:

```python
import json
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ModelMetadata:
    model_name: str
    version: str
    framework: str
    training_samples: int
    accuracy: float
    f1: float
    hyperparameters: dict
    feature_names: list
    stage: str = "Development"
    training_date: datetime = None
    notes: str = ""

    def to_dict(self):
        data = dict(self.__dict__)
        if data["training_date"] is not None:
            data["training_date"] = data["training_date"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        if data.get("training_date") is not None:
            data["training_date"] = datetime.fromisoformat(data["training_date"])
        return cls(**data)

class MetadataRegistry:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.store = {}

    def register(self, md):
        key = "%s_%s" % (md.model_name, md.version)
        self.store[key] = md
        self._save()
        print("registered: %s | stage %s" % (key, md.stage))

    def get_production(self, model_name):
        for md in self.store.values():
            if md.model_name == model_name and md.stage == "Production":
                return md
        return None

    def _save(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({k: m.to_dict() for k, m in self.store.items()},
                      f, indent=2)

    def _load(self):
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: ModelMetadata.from_dict(v) for k, v in data.items()}
        except FileNotFoundError:
            return {}

trained = datetime(2026, 9, 20, 14, 30)
reg = MetadataRegistry("registry_ledger.json")
reg.register(ModelMetadata("sentiment-bow", "1.2.0", "scikit-learn", 25000,
                           0.842, 0.835, {"C": 1.0},
                           ["text_len", "lexicon_score"], "Archived", trained))
reg.register(ModelMetadata("sentiment-bow", "1.3.0", "scikit-learn", 25000,
                           0.884, 0.871, {"C": 0.5},
                           ["text_len", "lexicon_score", "bigrams"],
                           "Production", trained))
reg.register(ModelMetadata("sentiment-bow", "1.3.1", "scikit-learn", 25000,
                           0.886, 0.873, {"C": 0.5},
                           ["text_len", "lexicon_score", "bigrams"],
                           "Development", trained))

prod = reg.get_production("sentiment-bow")
print("production model: v%s (accuracy %.3f)" % (prod.version, prod.accuracy))
reloaded = reg._load()
print("reloaded %d versions from disk" % len(reloaded))
print("json roundtrip preserved all fields:",
      reloaded["sentiment-bow_1.3.0"] == reg.store["sentiment-bow_1.3.0"])
```

**Output:**

```text
registered: sentiment-bow_1.2.0 | stage Archived
registered: sentiment-bow_1.3.0 | stage Production
registered: sentiment-bow_1.3.1 | stage Development
production model: v1.3.0 (accuracy 0.884)
reloaded 3 versions from disk
json roundtrip preserved all fields: True
```

The roundtrip equality check is the point of the block: datetimes serialize to ISO strings and reconstruct exactly, so a metadata ledger written by one process reads back faithfully in another. Fields worth keeping in a real registry beyond this schema: the training run ID (links metrics to the full run log), a data hash or dataset version (reproducibility), and the deployment history (who promoted, when, under which ticket).

---

## Registry Aliases

The promotion mechanism is where registries earn their keep. The modern pattern is **aliases**: a named, mutable reference that points at one version. Promoting `v3` to `champion` is a single write; `v1` is not deleted or archived - it simply loses the alias. Rollback is the same write in reverse. A minimal simulation makes the mechanics visible:

```python
class Registry:
    """Minimal registry: integer versions plus mutable named aliases."""

    def __init__(self, name):
        self.name = name
        self._next = 1
        self.versions = {}                    # "1" -> {"aliases": set()}

    def register(self):
        key = str(self._next)
        self._next += 1
        self.versions[key] = {"aliases": set()}
        return key

    def set_alias(self, version, alias):
        """An alias points at exactly one version - reassigning is one write."""
        for meta in self.versions.values():
            meta["aliases"].discard(alias)
        self.versions[version]["aliases"].add(alias)

    def resolve(self, alias):
        hits = [v for v, meta in self.versions.items()
                if alias in meta["aliases"]]
        return hits[0] if hits else None

reg = Registry("sentiment-bow")
for _ in range(3):
    reg.register()
reg.set_alias("1", "champion")
reg.set_alias("2", "challenger")

print("registered versions:", sorted(reg.versions, key=int))
print("champion ->", reg.resolve("champion"),
      "| challenger ->", reg.resolve("challenger"))

reg.set_alias("3", "champion")                # promotion: one auditable write
print("after promoting v3:")
print("  champion ->", reg.resolve("champion"))
print("  v1 still exists, it just loses the alias:",
      ", ".join(sorted(reg.versions["1"]["aliases"])) or "(none)")
print("  alias map:", {v: sorted(m["aliases"]) for v, m
                       in sorted(reg.versions.items(), key=lambda kv: int(kv[0]))})
```

**Output:**

```text
registered versions: ['1', '2', '3']
champion -> 1 | challenger -> 2
after promoting v3:
  champion -> 3
  v1 still exists, it just loses the alias: (none)
  alias map: {'1': [], '2': ['challenger'], '3': ['champion']}
```

Two aliases to keep in every production setup: `champion` (the version serving traffic) and `challenger` (the candidate being compared against it). New versions land as `challenger`, accumulate evidence, and take `champion` only when they beat it - and because promotion is an alias write, reversing a bad promotion takes seconds, not a redeploy.

---

## MLflow Integration

MLflow ships a tracking server plus a model registry on top: training runs log params and metrics, `log_model` registers the artifact as a named model version, and aliases drive promotion. The sketch below is the full loop (this environment has no MLflow installed and no server running, so it is documentation, not a runnable block):

```text
# sketch - needs `pip install mlflow` plus a running tracking server
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

with mlflow.start_run() as run:
    mlflow.log_params({"C": 0.5, "epochs": 10})
    mlflow.log_metrics({"accuracy": 0.884, "f1": 0.871})
    mlflow.sklearn.log_model(model, artifact_path="model",
                             registered_model_name="sentiment-bow")
# a new immutable version of "sentiment-bow" now exists, linked to this run

# promotion is one auditable alias write - older versions stay intact
client.set_registered_model_alias("sentiment-bow", "champion", "3")
client.set_registered_model_alias("sentiment-bow", "production", "3")

# consumers resolve through the alias, never a hard-coded version number
model = mlflow.sklearn.load_model("models:/sentiment-bow@production")
```

A note on older code you will find in the wild: earlier MLflow workflows used named *stages* (`Staging`/`Production`/`Archived`) moved with `transition_model_version_stage` calls. The current MLflow documentation leads with aliases instead - "Model aliases allow you to assign a mutable, named reference to a particular version of a registered model", useful for "promoting models to experimental, staging, or production environments in a controlled and auditable way" - and resolves them through `models:/name@alias` URIs. The alias model is strictly more flexible (any number of named references, one write per promotion), and it is the same mechanism the `Registry` class above simulates.

---

## Weights & Biases Integration

W&B splits the job in two: **artifacts** carry the model files and their lineage inside a project run, and the **W&B Registry** is the cross-project central repository they get linked into. The flow is `log_artifact` (attach files to a run) then `link_artifact` (put that version into a registry collection); W&B creates the collection on first link (sketch - `wandb` is not installed in this environment):

```text
# sketch - needs `pip install wandb` and an authenticated project
import wandb

run = wandb.init(project="sentiment-analysis", config={"C": 0.5})

artifact = wandb.Artifact("sentiment-bow", type="model")
artifact.add_file("model.pkl")
run.log_artifact(artifact, aliases=["v3"])

# link the logged version into a registry collection; the target path is
# wandb-registry-<registry-name>/<collection> and the collection is
# created automatically on first link
run.link_artifact(artifact,
                  target_path="wandb-registry-models/sentiment-prod")
```

The registry collection then holds the curated, permission-controlled versions that other teams consume, with W&B tracking lineage from the training run through to the linked registry version. Conceptually it is the same two-layer design as before: the project artifact is the training-side record, the registry collection is the promotion-facing identity - aliases/collections stand in for the champion/challenger pattern.

---

## Production Deployment

Serving code should never name a version directly. Pin the *alias* in the serving config; the registry resolves it to a concrete version at load time. That single indirection is what makes promotion and rollback a registry operation instead of a deployment operation:

```text
# sketch - resolve the production alias; never a bare "latest"
import mlflow

model = mlflow.sklearn.load_model("models:/sentiment-bow@production")

# rollback is a one-line repoint of the same alias:
#   client.set_registered_model_alias("sentiment-bow", "production", "2")
# for air-gapped hosts, export the resolved version once:
#   mlflow.sklearn.save_model(model, "snapshots/sentiment-bow-3")
# and load the local snapshot where the registry is unreachable:
#   import joblib; model = joblib.load("snapshots/sentiment-bow-3/model.pkl")
```

Operating rules that keep this safe:

- **Pin aliases, not versions, in serving configs.** The alias indirection is the rollback mechanism; a hard-coded version number disables it.
- **Promote through evidence, not hope.** A version becomes `challenger` first; it takes `production` when its live metrics beat the champion.
- **Re-check drift signals against the registry metadata.** When [1502: Model Drift Detection](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) fires, the registry record tells you exactly which data and parameters produced the serving version.

---

## References

### Related ai-engineering-curriculum Documents

- [6501: ML Model Lifecycle Management](6501-ML-Lifecycle-Management.md)
- [6502: CI/CD for Machine Learning](6502-CI-CD-for-ML.md)

### External References

- [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/) — versions, metadata, and aliases with `models:/name@alias` resolution
- [W&B Registry guide](https://docs.wandb.ai/guides/registry/) — `log_artifact` → `link_artifact` into registry collections
- [Semantic Versioning 2.0.0](https://semver.org/) — the MAJOR/MINOR/PATCH contract the bump rules borrow from

---

## Next Steps

- Review the pipeline around the registry: **[6502: CI/CD for ML](6502-CI-CD-for-ML.md)** wires registration and promotion into the delivery flow
- Phase 6 complete! Next: **[Phase 7: Agents](../../phase7-agentic/README.md)**
- Assessment: **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** and **[assessment/QUIZ.md](./assessment/QUIZ.md)**

**Related:** [6501](6501-ML-Lifecycle-Management.md) — the lifecycle stage this registry serves; [6502](6502-CI-CD-for-ML.md) — automates registration and promotion; [1502](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) — drift signals that trigger rollbacks; [EXP_6501_MLOPS_PIPELINE](../../../../experiments/EXP_6501_MLOPS_PIPELINE.md)

**Experiment:** [EXP_6501_MLOPS_PIPELINE.md](../../../../experiments/EXP_6501_MLOPS_PIPELINE.md) — nearest-relevant pipeline experiment; the registry mechanics here are simulated in-process, and the MLflow/W&B flows above want a tracking server or an authenticated W&B project
