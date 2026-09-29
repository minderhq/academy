---
Document ID: 6502
Title: "6502: CI/CD for Machine Learning"
Phase: 6
Module: 6500
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['mlops', 'pipeline', 'ci-cd', 'model-registry', 'lifecycle']
---

# 6502: CI/CD for Machine Learning

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [CI/CD Pipeline Architecture](#cicd-pipeline-architecture)
- [Pipeline Configuration](#pipeline-configuration)
- [CI Job Dependencies](#ci-job-dependencies)
- [Automated Training Pipeline](#automated-training-pipeline)
- [Validation Gates](#validation-gates)
- [Deployment Strategies](#deployment-strategies)
- [Best Practices](#best-practices)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain how an ML pipeline differs from a software CI/CD pipeline: the build stage trains, so data and model quality gates sit inside the pipeline
- Write a GitHub Actions workflow that triggers on model-relevant paths and chains jobs with `needs` dependencies
- Simulate job DAG execution to predict exactly what gets skipped when an early job fails
- Build data validation and model quality gates that stop the pipeline before a bad model ships
- Run a canary rollout decision loop: progressive stages, metric thresholds, automatic rollback
- Pin GitHub Actions to verified major versions instead of copying stale `@v3` snippets

---

## Abstract

A machine learning CI/CD pipeline is a software pipeline with two extra failure modes: the *artifact* is produced by training (so it varies run to run), and its quality depends on data that can drift under it. This lesson walks the pipeline end to end — trigger configuration, job dependencies, training, validation gates, and progressive deployment — with every decision mechanic (schema checks, quality thresholds, canary stage evaluation, DAG skip logic) implemented as deterministic, runnable simulations, and the platform-specific parts (GitHub Actions YAML, MLflow tracking, a live endpoint) as clearly labeled sketches.

---

## CI/CD Pipeline Architecture

```text
  push to main            pipeline stages                          production
 (models/**,         +-----------------------------+            traffic
  data/**,           | data-validation             |
  training/**) ----> |   -> train                  |            promote only
                     |     -> model-quality-gate   | ---------> after canary
                     |       -> build-image        |            stages pass
                     |         -> deploy-staging   |
                     |           -> smoke-tests    |
                     |             -> promote-prod |
                     +-----------------------------+
                        one failed stage stops everything downstream
```

Two differences from classic software CI/CD shape everything below:

- **The pipeline runs *training*, which is expensive and non-deterministic.** You do not want it triggered by a docs change — hence path filters — and you do not want its output shipped unchecked — hence explicit quality gates between train and deploy.
- **The deploy target is a model version, not a binary.** Promotion means pointing an alias or deployment at a newly registered version (see [6503: Model Registry](6503-Model-Registry.md)), so rollback is a repoint, not a rebuild.

---

## Pipeline Configuration

The workflow below is a GitHub Actions sketch — it needs a repository, runners, and scripts to exist — but the keys are the real contract. Action pins are major-version tags verified against the release pages as of 2026-09: `checkout@v7` (v7.0.1), `setup-python@v7` (v7.0.0), `cache@v6` (v6.1.0), `upload-artifact@v7` (v7.0.1), `download-artifact@v8` (v8.0.1). Copying snippets with stale pins (`checkout@v3`, `setup-python@v4`, `upload-artifact@v3`) is the most common way tutorials rot — check the release page, pin the major, and let renovate/dependabot keep it current.

```text
# .github/workflows/ml-pipeline.yml (sketch - needs a repo + runners)
name: ML Pipeline

on:
  push:
    branches: [main]
    paths: ['models/**', 'data/**', 'training/**']
    # runs only if at least one changed path matches the filter
  pull_request:
    branches: [main]

jobs:
  build-and-train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: '3.13'
      - uses: actions/cache@v6
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('**/requirements.txt') }}
      - run: pip install uv
      - run: uv pip install --system -r requirements.txt
      - run: python scripts/validate_data.py     # data gate: exits non-zero on FAIL
      - run: python scripts/train.py             # training + registration
      - uses: actions/upload-artifact@v7
        with:
          name: model-artifacts
          path: models/

  test-and-deploy:
    needs: build-and-train                       # runs only after the job above succeeds
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v8
        with:
          name: model-artifacts
      - run: python -m pytest tests/ -q          # model quality gate
      - run: python deployment.py --stage staging
```

---

## CI Job Dependencies

Per the GitHub Actions docs, "a workflow run is made up of one or more `jobs`, which run in parallel by default. To run jobs sequentially, you can define dependencies on other jobs using the `jobs.<job_id>.needs` keyword." That single rule fully determines what happens on failure — predict it before burning GPU minutes. The simulation below walks the DAG the same way the runner does, in dependency order, skipping everything whose `needs` chain is broken:

```python
JOBS = {
    "data-validation":    [],
    "train":              ["data-validation"],
    "model-quality-gate": ["train"],
    "build-image":        ["model-quality-gate"],
    "deploy-staging":     ["build-image"],
    "smoke-tests":        ["deploy-staging"],
    "promote-production": ["smoke-tests"],
}

def run_pipeline(scenario, failed_jobs):
    print("scenario: %s" % scenario)
    status = {}
    for job in JOBS:                       # definition order is dependency order
        needs = JOBS[job]
        if any(status.get(dep) != "success" for dep in needs):
            status[job] = "skipped"
            reason = " (needs %s)" % ", ".join(needs) if needs else ""
        elif job in failed_jobs:
            status[job] = "failure"
            reason = ""
        else:
            status[job] = "success"
            reason = ""
        print("  %-20s -> %s%s" % (job, status[job], reason))
    return status

run_pipeline("data-validation fails", {"data-validation"})
run_pipeline("all green", set())
```

**Output:**

```text
scenario: data-validation fails
  data-validation      -> failure
  train                -> skipped (needs data-validation)
  model-quality-gate   -> skipped (needs train)
  build-image          -> skipped (needs model-quality-gate)
  deploy-staging       -> skipped (needs build-image)
  smoke-tests          -> skipped (needs deploy-staging)
  promote-production   -> skipped (needs smoke-tests)
scenario: all green
  data-validation      -> success
  train                -> success
  model-quality-gate   -> success
  build-image          -> success
  deploy-staging       -> success
  smoke-tests          -> success
  promote-production   -> success
```

One failing gate costs seconds and stops the chain; a missing gate costs a GPU training run before it stops anything. That is why the cheapest checks — schema, leakage, file existence — are always first in the DAG.

---

## Automated Training Pipeline

The training step's job in the pipeline is narrower than "train a model": it must also *register* the result and exit non-zero on failure, so the pipeline can act on it. The sketch uses MLflow for tracking + registration (MLflow is not installed in this environment, and the script needs real CSVs on disk — the structure is what matters):

```text
# sketch - scripts/train.py; needs `uv pip install mlflow` + data/ CSVs
import argparse
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

def train(data_dir, experiment_name):
    import pandas as pd
    train_data = pd.read_csv("%s/train.csv" % data_dir)
    val_data = pd.read_csv("%s/val.csv" % data_dir)

    params = {"n_estimators": 100, "max_depth": 10, "random_state": 42}
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        model = RandomForestClassifier(**params)
        model.fit(train_data.drop("target", axis=1), train_data["target"])
        val_accuracy = accuracy_score(
            val_data["target"], model.predict(val_data.drop("target", axis=1)))
        mlflow.log_metric("val_accuracy", val_accuracy)
        mlflow.sklearn.log_model(model, "model",
                                 registered_model_name=experiment_name)
        print("val_accuracy=%.4f run_id=%s" % (val_accuracy, run.info.run_id))
        if val_accuracy < 0.5:
            raise SystemExit("val_accuracy below floor - failing the pipeline")
```

The last two lines are the pipeline contract: metrics land in the tracking server *and* a bad run fails its own step, so `needs` stops the chain without extra wiring.

---

## Validation Gates

Gates are the code-encoded opinions about what may ship. Two layers, cheapest first: the **data gate** runs before training spends money; the **model quality gate** runs after training, before anything deploys.

### Data Gate

Four checks cover most training data failures: schema consistency between train and validation, missing values, class balance, and train/val ID leakage (the one that silently inflates validation scores):

```python
from dataclasses import dataclass, field

@dataclass
class ValidationReport:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

def validate_dataset(train, val):
    rep = ValidationReport()
    train_cols = list(train[0]) if train else []
    val_cols = list(val[0]) if val else []

    # 1. schema: same columns, same order
    if train_cols == val_cols:
        rep_line = "[1/4] schema check: %d cols, consistent" % len(train_cols)
    else:
        rep_line = "[1/4] schema check: MISMATCH %r vs %r" % (train_cols, val_cols)
        rep.errors.append("schema")
    print(rep_line)

    # 2. missing values
    missing = {}
    for row in train:
        for col, v in row.items():
            if v is None:
                missing[col] = missing.get(col, 0) + 1
    if missing:
        col = sorted(missing)[0]
        print("[2/4] missing values: %s has %d in train" % (col, missing[col]))
        rep.warnings.append("missing:%s" % col)
    else:
        print("[2/4] missing values: none")

    # 3. class distribution
    labels = [row["label"] for row in train]
    dist = {lab: labels.count(lab) / len(labels) for lab in sorted(set(labels))}
    print("[3/4] class distribution: {%s} - min share %.2f" % (
        ", ".join("%d: %.2f" % (k, v) for k, v in dist.items()), min(dist.values())))
    if min(dist.values()) < 0.05:
        rep.warnings.append("imbalance")

    # 4. train/val id leakage
    train_ids = {row["id"] for row in train}
    val_ids = {row["id"] for row in val}
    overlap = train_ids & val_ids
    if overlap:
        print("[4/4] train/val id overlap: %d shared id(s) -> ERROR: leakage"
              % len(overlap))
        rep.errors.append("leakage")
    else:
        print("[4/4] train/val id overlap: none")

    verdict = "FAIL" if rep.errors else ("WARN" if rep.warnings else "PASS")
    print("gate decision: %s%s" % (verdict,
          " - pipeline stops before training" if rep.errors else ""))
    return verdict

train = [
    {"id": 1, "text_len": 42, "label": 0},
    {"id": 2, "text_len": 18, "label": 1},
    {"id": 3, "text_len": None, "label": 0},
    {"id": 4, "text_len": 57, "label": 0},
]
val = [
    {"id": 2, "text_len": 20, "label": 1},   # id 2 leaked from train
    {"id": 5, "text_len": 33, "label": 0},
]
validate_dataset(train, val)
```

**Output:**

```text
[1/4] schema check: 3 cols, consistent
[2/4] missing values: text_len has 1 in train
[3/4] class distribution: {0: 0.75, 1: 0.25} - min share 0.25
[4/4] train/val id overlap: 1 shared id(s) -> ERROR: leakage
gate decision: FAIL - pipeline stops before training
```

Notice the severity split: a missing value is a *warning* (impute or drop), leakage is an *error* (the dataset is broken — validation metrics are untrustworthy, so training on it wastes the run).

### Model Quality Gate

After training, the candidate faces hard thresholds before it may deploy: accuracy floor, latency SLA, and a probability sanity check. A candidate that beats the floor but loses to the champion can still advance — as a *challenger* — while a candidate under the floor stops the pipeline outright:

```python
ACCURACY_FLOOR = 0.85
P95_SLA_MS = 100
CHAMPION_ACCURACY = 0.884

candidates = [
    {"version": "1.3.1", "accuracy": 0.851, "p95_ms": 41, "proba_err": 0.0},
    {"version": "1.4.0", "accuracy": 0.796, "p95_ms": 38, "proba_err": 0.0},
]

def quality_gate(cand):
    checks = [
        ("accuracy", cand["accuracy"] >= ACCURACY_FLOOR,
         "accuracy %.3f (floor %.2f)" % (cand["accuracy"], ACCURACY_FLOOR)),
        ("latency", cand["p95_ms"] <= P95_SLA_MS,
         "p95 %dms (SLA %dms)" % (cand["p95_ms"], P95_SLA_MS)),
        ("proba", cand["proba_err"] < 1e-6,
         "proba rows sum to 1.0"),
    ]
    parts, ok = [], True
    for name, passed, desc in checks:
        parts.append("%s %s" % (desc, "OK" if passed else "FAIL"))
        ok = ok and passed
    print("candidate %s: %s" % (cand["version"], " | ".join(parts)))
    if ok:
        print("  verdict: PASS -> register as challenger (champion stays %.3f)"
              % CHAMPION_ACCURACY)
    else:
        print("  verdict: REJECTED - pipeline stops, no deployment")
    return ok

for cand in candidates:
    quality_gate(cand)
```

**Output:**

```text
candidate 1.3.1: accuracy 0.851 (floor 0.85) OK | p95 41ms (SLA 100ms) OK | proba rows sum to 1.0 OK
  verdict: PASS -> register as challenger (champion stays 0.884)
candidate 1.4.0: accuracy 0.796 (floor 0.85) FAIL | p95 38ms (SLA 100ms) OK | proba rows sum to 1.0 OK
  verdict: REJECTED - pipeline stops, no deployment
```

The floor and the champion play different roles: the floor is a *hard* gate (below it, deploy is pointless), the champion comparison is a *soft* gate (beating the champion earns promotion; merely passing earns a challenger slot — production traffic still belongs to the champion until live evidence says otherwise).

---

## Deployment Strategies

Smoke tests probe a deployed endpoint's shape — health, predict, batch predict, model info — before promotion. The real script needs a live staging URL; the checks themselves are plain request/response assertions:

```text
# sketch - tests/smoke_tests.py; needs `uv pip install requests` + a deployed endpoint
import sys
import requests

BASE_URL = "https://staging-api.example.com"

def run_smoke_tests():
    checks = []

    r = requests.get(BASE_URL + "/health", timeout=5)
    checks.append(("health", r.status_code == 200 and
                   r.json().get("status") == "healthy"))

    r = requests.post(BASE_URL + "/predict",
                      json={"text": "smoke test sentence"}, timeout=10)
    body = r.json()
    checks.append(("predict", r.status_code == 200 and
                   "prediction" in body and "confidence" in body))

    r = requests.get(BASE_URL + "/model_info", timeout=5)
    checks.append(("model_info", r.status_code == 200 and
                   "version" in r.json()))

    for name, ok in checks:
        print("%-10s %s" % (name, "PASS" if ok else "FAIL"))
    if not all(ok for _name, ok in checks):
        sys.exit(1)
```

### Canary Rollout

A canary release is, per Martin Fowler, "a technique to reduce the risk of introducing a new software version in production by slowly rolling out the change to a small subset of users." The decision mechanic is a loop: raise traffic in stages, measure error rate and latency at each stage, roll back the moment a threshold breaks. Here is that loop, with the measurements fixed so the decision path is visible:

```python
STAGES = [10, 25, 50, 75, 100]
ERROR_LIMIT = 0.05
P95_LIMIT_MS = 1000

def rollout(name, measurements):
    print("rollout %s:" % name)
    last_ok = 0
    for pct in STAGES:
        worst_err = max(err for err, _p95 in measurements[pct])
        worst_p95 = max(p95 for _err, p95 in measurements[pct])
        if worst_err > ERROR_LIMIT or worst_p95 > P95_LIMIT_MS:
            why = []
            if worst_err > ERROR_LIMIT:
                why.append("error rate %.3f exceeds %.2f" % (worst_err, ERROR_LIMIT))
            if worst_p95 > P95_LIMIT_MS:
                why.append("p95 %dms exceeds %dms" % (worst_p95, P95_LIMIT_MS))
            print("  stage %3d%%: %s" % (pct, "; ".join(why)))
            print("  verdict: rolled back - traffic returns to the previous "
                  "version (last stable stage %d%%)" % last_ok)
            return
        print("  stage %3d%%: max error %.3f, max p95 %dms -> ok"
              % (pct, worst_err, worst_p95))
        last_ok = pct
    print("  verdict: promoted - canary is now the production version")

good = {
    10:  [(0.002, 120), (0.003, 131), (0.001, 118)],
    25:  [(0.002, 127), (0.002, 122), (0.004, 130)],
    50:  [(0.003, 126), (0.002, 119), (0.003, 124)],
    75:  [(0.004, 880), (0.002, 910), (0.003, 870)],
    100: [(0.002, 125), (0.003, 121), (0.002, 118)],
}
bad = {pct: list(ms) for pct, ms in good.items()}
bad[75] = [(0.006, 880), (0.002, 1200), (0.003, 870)]

rollout("good-candidate", good)
rollout("bad-candidate", bad)
```

**Output:**

```text
rollout good-candidate:
  stage  10%: max error 0.003, max p95 131ms -> ok
  stage  25%: max error 0.004, max p95 130ms -> ok
  stage  50%: max error 0.003, max p95 126ms -> ok
  stage  75%: max error 0.004, max p95 910ms -> ok
  stage 100%: max error 0.003, max p95 125ms -> ok
  verdict: promoted - canary is now the production version
rollout bad-candidate:
  stage  10%: max error 0.003, max p95 131ms -> ok
  stage  25%: max error 0.004, max p95 130ms -> ok
  stage  50%: max error 0.003, max p95 126ms -> ok
  stage  75%: p95 1200ms exceeds 1000ms
  verdict: rolled back - traffic returns to the previous version (last stable stage 50%)
```

Two details carry the risk reduction: thresholds are evaluated on the *worst* sample per stage (one bad window is enough to stop), and rollback returns traffic to the *previous version* — not to stage zero — so users never see the broken candidate again. In Kubernetes terms the canary is a second Deployment sharing the service; the `kubernetes` client calls are platform plumbing:

```text
# sketch - kubernetes package not installed here; the rollout step wraps:
from kubernetes import client, config

config.load_kube_config()
apps = client.AppsV1Api()
# create the canary Deployment (same spec, new image tag), then the
# traffic split itself lives in your ingress or service mesh - the
# rollout() loop above is the policy that drives it
apps.create_namespaced_deployment(namespace="staging", body=canary_spec)
```

---

## Best Practices

1. **Path filters on triggers.** A docs-only change must not trigger a training run — `on.push.paths` is the cheapest cost control you have.
2. **Cheapest gates first.** Schema and leakage checks cost milliseconds and prevent the most expensive failures; order the DAG so they run before training.
3. **Fail the step, not just the log.** A gate that prints a warning but exits 0 protects nobody. Every gate's failure must be visible to `needs`.
4. **Pin action majors from release pages.** `checkout@v7`, `setup-python@v7`, `upload-artifact@v7`, `cache@v6`, `download-artifact@v8` — verified, not copied from a stale tutorial.
5. **Cache dependencies and artifacts.** The `cache@v6` step keyed on `hashFiles('**/requirements.txt')` skips reinstall on unchanged lockfiles.
6. **Promote through evidence, not hope.** Floor gates admit a challenger; live canary stages promote it. Never wire training accuracy straight to production.
7. **Rollback is a repoint.** Because [6503: Model Registry](6503-Model-Registry.md) aliases point at versions, undoing a bad promotion is one write — design deployments to exploit that.
8. **Watch drift after promotion.** Deployment is not the end: [1502: Model Drift Detection](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) monitors the serving version and feeds findings back into the next pipeline run.

---

## References

### Related PROJECT-OMEGA Documents

- [6501: ML Model Lifecycle Management](6501-ML-Lifecycle-Management.md)
- [6503: Model Registry](6503-Model-Registry.md)
- [1502: Model Drift Detection](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md)

### External References

- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) — `needs`, `if`, and `on.paths`: "run jobs sequentially... using the `jobs.<job_id>.needs` keyword"
- [Martin Fowler: Canary Release](https://martinfowler.com/bliki/CanaryRelease.html) — the canonical definition and rollback philosophy behind the rollout loop
- [actions/checkout releases](https://github.com/actions/checkout/releases) — current major v7 (v7.0.1)
- [actions/setup-python releases](https://github.com/actions/setup-python/releases) — current major v7 (v7.0.0)
- [actions/upload-artifact releases](https://github.com/actions/upload-artifact/releases) — current major v7 (v7.0.1)
- [actions/cache releases](https://github.com/actions/cache/releases) — current major v6 (v6.1.0)
- [actions/download-artifact releases](https://github.com/actions/download-artifact/releases) — current major v8 (v8.0.1), note its major differs from upload-artifact

---

## Next Steps

- The registry these jobs promote into: **[6503: Model Registry](6503-Model-Registry.md)**
- Phase 6 complete! Next: **[Phase 7: Agents](../../phase7-agentic/README.md)**
- Assessment: **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** and **[assessment/QUIZ.md](./assessment/QUIZ.md)**

**Related:** [6501](6501-ML-Lifecycle-Management.md) — the lifecycle stage this pipeline automates; [6503](6503-Model-Registry.md) — the registry the promote job writes into; [1502](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) — post-deploy monitoring feeding the next run; [EXP_6501_MLOPS_PIPELINE](../../../../experiments/EXP_6501_MLOPS_PIPELINE.md)

**Experiment:** [EXP_6501_MLOPS_PIPELINE.md](../../../../experiments/EXP_6501_MLOPS_PIPELINE.md) — nearest-relevant pipeline experiment; the gate and rollout mechanics here run in-process, and the GitHub Actions / MLflow / smoke-test flows need a repo, a tracking server, and a deployed endpoint respectively
