---
Document ID: 6501
Title: ML Model Lifecycle Management
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

# 6501: ML Model Lifecycle Management

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [ML Lifecycle Stages](#ml-lifecycle-stages)
- [Stage 1: Development](#stage-1-development)
- [Stage 2: Validation](#stage-2-validation)
- [Stage 3: Deployment](#stage-3-deployment)
- [Stage 4: Monitoring](#stage-4-monitoring)
- [Stage 5: Retirement](#stage-5-retirement)
- [Production Checklist](#production-checklist)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Map the five lifecycle stages and the state machine that gates every transition between them
- Trace a model version from `registered` to `retired` through a transition map that forbids shortcuts (a candidate cannot skip the canary stage)
- Judge a challenger against a champion with McNemar's exact test on discordant prediction pairs
- Emit serving metrics (counters, histograms, gauges) in Prometheus exposition format with an isolated registry
- Apply four retirement criteria — age, performance, usage, cost — to decide archive versus keep
- Separate symptom-based paging from cause-based logging per Google SRE practice

---

## Abstract

A model's life does not end at the first deploy — it begins there. This lesson models the ML lifecycle as an explicit state machine over five stages (development, validation, deployment, monitoring, retirement), where each state transition is a gated, auditable step rather than an informal habit. The decision mechanics are runnable: a transition map that rejects shortcuts, McNemar's exact test for challenger-vs-champion decisions, real Prometheus metric emission, and a retirement review. The platform pieces — MLflow tracking and the routing-layer flip — are labeled sketches. [6502: CI/CD for Machine Learning](6502-CI-CD-for-ML.md) automates these stages; [6503: Model Registry](6503-Model-Registry.md) records where each version currently stands.

---

## ML Lifecycle Stages

```text
  registered --> candidate --> canary --> production --> shadow --> retired
                   ^             |           |
                   |   rollback  |           |  rollback (one alias write)
                   +-------------+           +--> candidate
  shortcuts are forbidden: candidate -> production must pass through canary
```

The stages map onto states, and the gates between them are the discipline:

- **registered** — training finished and the artifact is in the registry; nothing serves it yet
- **candidate** — passed offline validation; eligible for a controlled rollout
- **canary** — taking a fraction of live traffic under close watch (mechanics: [6502, Deployment Strategies](6502-CI-CD-for-ML.md))
- **production** — taking full traffic; rollback is repointing the alias, never a rebuild
- **shadow** — receiving mirrored traffic for evaluation only; the exit path to retirement

The transition map below is the lifecycle as code. Note what it forbids: after a rollback to candidate, the model must re-enter through canary — there is no direct hop back to production, because the reason it was rolled back has not changed.

```python
ALLOWED = {
    "registered": ["candidate"],
    "candidate":  ["canary", "retired"],
    "canary":     ["production", "candidate"],   # candidate = rollback
    "production": ["shadow", "candidate"],
    "shadow":     ["retired"],
    "retired":    [],
}

def transition(model, src, dst):
    if model["stage"] != src:
        print("%-11s -> %-11s REJECTED (model is in %s)" % (src, dst, model["stage"]))
        return False
    if dst not in ALLOWED.get(src, []):
        allowed = ", ".join(ALLOWED.get(src, [])) or "none (terminal)"
        print("%-11s -> %-11s REJECTED (from %s only: %s)" % (src, dst, src, allowed))
        return False
    print("%-11s -> %-11s ok" % (src, dst))
    model["stage"] = dst
    model["history"].append(dst)
    return True

model = {"name": "text-classifier", "stage": "registered",
         "history": ["registered"]}

transition(model, "registered", "candidate")
transition(model, "candidate", "canary")
transition(model, "canary", "production")
transition(model, "production", "candidate")    # rollback: repoint, not delete
transition(model, "candidate", "production")    # shortcut: must re-enter via canary
transition(model, "candidate", "canary")
transition(model, "canary", "production")
transition(model, "production", "shadow")
transition(model, "shadow", "retired")
print("final history: %s" % " -> ".join(model["history"]))
```

**Output:**

```text
registered  -> candidate   ok
candidate   -> canary      ok
canary      -> production  ok
production  -> candidate   ok
candidate   -> production  REJECTED (from candidate only: canary, retired)
candidate   -> canary      ok
canary      -> production  ok
production  -> shadow      ok
shadow      -> retired     ok
final history: registered -> candidate -> canary -> production -> candidate -> canary -> production -> shadow -> retired
```

The full history is the audit trail: when someone asks six months later why the model visited canary twice, the answer is in the transition log.

---

## Stage 1: Development

Development's deliverable is not a model file — it is a *reproducible run*: pinned parameters, logged metrics, and a registered artifact that the rest of the lifecycle can address. The sketch uses MLflow for the run + registration (needs a tracking server and data on disk):

```text
# sketch - needs `uv pip install mlflow` + a tracking server + data on disk
import mlflow
from sklearn.ensemble import GradientBoostingClassifier

params = {"n_estimators": 200, "max_depth": 4, "random_state": 42}
mlflow.set_experiment("text-classifier")
with mlflow.start_run() as run:
    mlflow.log_params(params)
    model = GradientBoostingClassifier(**params)
    model.fit(X_train, y_train)
    mlflow.log_metric("val_accuracy", model.score(X_val, y_val))
    mlflow.sklearn.log_model(model, "model",
                             registered_model_name="text-classifier")
    print("registered from run %s" % run.info.run_id)
```

The last line is the lifecycle entry point: `log_model` with `registered_model_name` puts the version into the `registered` state. Everything after — validation, rollout, retirement — operates on registry entries, not on files in someone's working directory.

---

## Stage 2: Validation

Offline metrics decide whether a model *works*; a paired comparison decides whether it *beats the champion*. The distinction matters because small accuracy differences are usually noise. McNemar's test looks only at the **discordant pairs** — the examples where the two models disagree — and, per [Wikipedia](https://en.wikipedia.org/wiki/McNemar%27s_test), "the exact test compares *b* to a binomial distribution with n = b + c and p = 0.5", which is the right tool when the disagreement count is small:

```python
from math import comb

def mcnemar_exact(b, c):
    """Two-sided exact p-value from the discordant counts.

    b = challenger right & champion wrong, c = challenger wrong & champion
    right; concordant pairs carry no signal and are discarded.
    """
    n = b + c
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)

def compare(label, b, c, alpha=0.05):
    p = mcnemar_exact(b, c)
    if p < alpha:
        winner = "challenger wins" if b > c else "champion wins"
        print("%s: b=%2d c=%2d p=%.4f -> significant, %s" % (label, b, c, p, winner))
    else:
        print("%s: b=%2d c=%2d p=%.4f -> not significant, keep champion"
              % (label, b, c, p))

compare("eval-1", 14, 3)
compare("eval-2", 5, 7)
compare("eval-3", 3, 13)
```

**Output:**

```text
eval-1: b=14 c= 3 p=0.0127 -> significant, challenger wins
eval-2: b= 5 c= 7 p=0.7744 -> not significant, keep champion
eval-3: b= 3 c=13 p=0.0213 -> significant, champion wins
```

Read the three verdicts as the full decision space: `eval-1` promotes the challenger, `eval-3` is evidence *for the champion* (a significant result can argue against the new version), and `eval-2` — the most common outcome — is an honest "not enough evidence", not a tie. No statistical library is needed here: the exact p-value is a binomial tail computed with `math.comb`.

---

## Stage 3: Deployment

Canary rollout — traffic raised in stages with metric gates and automatic rollback — is covered end to end in [6502, Deployment Strategies](6502-CI-CD-for-ML.md). The other classic pattern is **blue-green**: the new version is deployed fully but takes zero traffic until a single routing write flips it over. The trade-off is binary risk against binary rollback:

```text
# sketch - blue-green flip at the routing layer (ingress / mesh config)
#   active:  service/green   (champion, live, takes 100% of traffic)
#   standby: service/blue    (challenger, fully deployed, 0% traffic)
#
# flip sequence:
#   1. warm up blue: run the smoke suite against it directly
#   2. flip the one routing entry  green -> blue   (single atomic write)
#   3. watch p95 latency + error rate for the observation window
#   4. keep, or flip back -- rollback is the same single write
```

Choose per blast radius: canary exposes a small slice and *measures* its way to 100%; blue-green exposes everyone at once but restores the old version in one step. Both depend on the same precondition — the previous version stays warm and addressable, which is exactly what registry aliases (see [6503](6503-Model-Registry.md)) provide.

---

## Stage 4: Monitoring

Google SRE's rule is "Every page should be actionable" — alerts fire on *symptoms* the user experiences (latency, errors, accuracy on live traffic), while *causes* (disk usage, queue depth, CPU) are logged for debugging but never page a human. The serving side of that contract is standard metrics: a counter for requests, a histogram for latency, a gauge for the latest evaluated accuracy. The `prometheus_client` library is installed in this environment, so the emission side runs for real — the registry is isolated so repeated imports never collide:

```python
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

registry = CollectorRegistry()   # isolated so repeated runs never collide

predictions = Counter("model_predictions_total", "Prediction count",
                      ["model_name", "status"], registry=registry)
latency = Histogram("model_prediction_latency_seconds", "Prediction latency",
                    ["model_name"], registry=registry,
                    buckets=[0.05, 0.1, 0.25, 0.5, 1.0])
accuracy = Gauge("model_accuracy", "Latest evaluated accuracy",
                 ["model_name"], registry=registry)

for _ in range(97):
    predictions.labels("text-classifier", "success").inc()
predictions.labels("text-classifier", "error").inc(3)
for seconds in (0.042, 0.118, 0.310):
    latency.labels("text-classifier").observe(seconds)
accuracy.labels("text-classifier").set(0.891)

for line in generate_latest(registry).decode().splitlines():
    if line.startswith(("model_accuracy",
                        "model_prediction_latency_seconds_count",
                        "model_prediction_latency_seconds_sum",
                        "model_predictions_total")):
        print(line)
```

**Output:**

```text
model_predictions_total{model_name="text-classifier",status="success"} 97.0
model_predictions_total{model_name="text-classifier",status="error"} 3.0
model_prediction_latency_seconds_count{model_name="text-classifier"} 3.0
model_prediction_latency_seconds_sum{model_name="text-classifier"} 0.47
model_accuracy{model_name="text-classifier"} 0.891
```

That is the exact text format a Prometheus server scrapes. Escalation policy on top of these signals stays simple: a symptom breaching its threshold raises a **WARNING**, a breach past 1.5x the threshold raises **CRITICAL**, and anything in the "why" category writes to the debug log instead. Two of the lifecycle's monitoring inputs come from elsewhere: data drift detection ([1502: Model Drift Detection](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md)) and the quality gate re-evaluations from the [6502 pipeline](6502-CI-CD-for-ML.md).

---

## Stage 5: Retirement

Models retire for boring reasons — they got old, their accuracy slid, nobody calls them, or they cost too much per prediction. Any one criterion is enough, because the review runs periodically and false positives only cost a re-review, while a false negative keeps a decaying model on live traffic:

```python
from datetime import date

TODAY = date(2026, 9, 26)
AGE_LIMIT_DAYS = 365
DEGRADATION_LIMIT = 0.10      # 10% relative accuracy drop vs baseline
MIN_CALLS_30D = 1000
COST_LIMIT = 0.75             # dollars per 1k predictions

MODELS = [
    {"version": "1.0.0", "deployed": date(2025, 6, 15), "accuracy": 0.710,
     "baseline": 0.880, "calls_30d": 120, "cost_per_1k": 0.90},
    {"version": "1.4.2", "deployed": date(2026, 7, 1), "accuracy": 0.891,
     "baseline": 0.880, "calls_30d": 54000, "cost_per_1k": 0.40},
]

def retirement_review(rec):
    age_days = (TODAY - rec["deployed"]).days
    degradation = (rec["baseline"] - rec["accuracy"]) / rec["baseline"]
    criteria = [
        ("age", age_days > AGE_LIMIT_DAYS,
         "age %d d > %d d" % (age_days, AGE_LIMIT_DAYS)),
        ("performance", degradation > DEGRADATION_LIMIT,
         "degradation %.1f%% > %.0f%%" % (degradation * 100, DEGRADATION_LIMIT * 100)),
        ("usage", rec["calls_30d"] < MIN_CALLS_30D,
         "usage %d calls/30d < %d" % (rec["calls_30d"], MIN_CALLS_30D)),
        ("cost", rec["cost_per_1k"] > COST_LIMIT,
         "cost $%.2f/1k > $%.2f" % (rec["cost_per_1k"], COST_LIMIT)),
    ]
    hits = [name for name, breached, _why in criteria if breached]
    print("model %s:" % rec["version"])
    for name, breached, why in criteria:
        print("  %-11s %s" % (name, why if breached else "ok"))
    if hits:
        print("  verdict: RETIRE (%s) - archive artifacts, repoint alias"
              % ", ".join(hits))
    else:
        print("  verdict: KEEP - re-review next quarter")
    return bool(hits)

for rec in MODELS:
    retirement_review(rec)
```

**Output:**

```text
model 1.0.0:
  age         age 468 d > 365 d
  performance degradation 19.3% > 10%
  usage       usage 120 calls/30d < 1000
  cost        cost $0.90/1k > $0.75
  verdict: RETIRE (age, performance, usage, cost) - archive artifacts, repoint alias
model 1.4.2:
  age         ok
  performance ok
  usage       ok
  cost        ok
  verdict: KEEP - re-review next quarter
```

Retirement is *not* deletion: artifacts are archived (a retired model must remain loadable for audits and retraining comparisons), the alias is repointed, and the version's state moves to `retired` — terminal in the state machine, terminal in the registry.

---

## Production Checklist

Before a version may leave `candidate`:

- [ ] Validated on a held-out test set, metrics meet the quality floor
- [ ] Challenger beat the champion on a paired test (Stage 2), or there is no champion yet
- [ ] Rollback path verified: the previous version is warm and the alias repoint is rehearsed
- [ ] Monitoring wired: counter, latency histogram and accuracy gauge scrape before the first canary stage
- [ ] Alert thresholds set — symptom-based only, with the 1.5x CRITICAL escalation
- [ ] The transition record will be written to the version's history (state machine, ML Lifecycle Stages)

Before a version is called `production`:

- [ ] Canary stages passed their error-rate and latency limits (6502, Deployment Strategies)
- [ ] No CRITICAL alerts open during the observation window
- [ ] Drift monitors registered against the serving version (1502)
- [ ] Incident runbook names the alias to repoint and who repoints it

---

## References

### Related ai-engineering-curriculum Documents

- [6502: CI/CD for Machine Learning](6502-CI-CD-for-ML.md)
- [6503: Model Registry](6503-Model-Registry.md)
- [1502: Model Drift Detection](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md)
- [LAB-007: Production RAG](../../../learning-resources/labs/LAB-007-Production-RAG.md)

### External References

- [McNemar's test (Wikipedia)](https://en.wikipedia.org/wiki/McNemar%27s_test) — discordant-pair definition and the exact binomial p-value behind Stage 2
- [Google SRE: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) — "Every page should be actionable": symptom-based paging, cause-based logging
- [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/) — the registration and alias flow behind the registered/candidate/production states

---

## Next Steps

- The pipeline that automates these stage transitions: **[6502: CI/CD for Machine Learning](6502-CI-CD-for-ML.md)**
- Phase 6 complete! Next: **[Phase 7: Agents](../../phase7-agentic/README.md)**
- Assessment: **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** and **[assessment/QUIZ.md](./assessment/QUIZ.md)**

**Related:** [6502](6502-CI-CD-for-ML.md) — the pipeline automating these stage transitions; [6503](6503-Model-Registry.md) — where every version's current state lives; [1502](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) — the drift signal feeding Stage 4; [EXP_6501_MLOPS_PIPELINE](../../../../experiments/EXP_6501_MLOPS_PIPELINE.md)

**Experiment:** [EXP_6501_MLOPS_PIPELINE.md](../../../../experiments/EXP_6501_MLOPS_PIPELINE.md) — nearest-relevant lifecycle experiment; the state machine, McNemar test, Prometheus emission and retirement review here run in-process, while MLflow tracking and metric scraping need their servers
