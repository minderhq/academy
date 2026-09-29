---
Document ID: ML-LIFECYCLE
Title: "ML Lifecycle: From Development to Production"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Beginner
---

# ML Lifecycle: From Development to Production

**Complete Machine Learning Model Lifecycle**

---

## ML Lifecycle Stages

```mermaid
graph TB
    subgraph "Development"
        DEV[Development<br/>Experimentation]
        TRAIN[Training<br/>Fine-tuning]
        EVAL[Evaluation<br/>Validation]
    end

    subgraph "Staging"
        STAGE[Staging Deploy<br/>Test Environment]
        SMOKE[Smoke Tests<br/>Basic Checks]
        AB[A/B Testing<br/>Comparison]
    end

    subgraph "Production"
        CANARY[Canary Deploy<br/>10% Traffic]
        MONITOR[Monitor<br/>Track Metrics]
        PROMOTE[Promote<br/>100% Traffic]
    end

    subgraph "Maintenance"
        DRIFT[Monitor Drift<br/>Data/Concept]
        RETRAIN[Retrain<br/>When Needed]
        RETIRE[Retire<br/>Decommission]
    end

    DEV --> TRAIN
    TRAIN --> EVAL
    EVAL --> STAGE
    STAGE --> SMOKE
    SMOKE --> AB
    AB --> CANARY
    CANARY --> MONITOR
    MONITOR --> PROMOTE
    PROMOTE --> DRIFT
    DRIFT -->|Trigger| RETRAIN
    DRIFT -->|OK| CONTINUE[Continue]
    CONTINUE --> DRIFT
    RETRAIN --> EVAL
```

---

## CI/CD Pipeline for ML

```mermaid
graph LR
    subgraph "Continuous Integration"
        CODE[Code Commit]
        BUILD[Build & Test]
        TRAIN[Train Model]
        EVALUATE[Evaluate Model]
        REGISTRY[Model Registry]
    end

    subgraph "Continuous Deployment"
        STAGE[Deploy to Staging]
        SMOKE[Smoke Tests]
        PROD[Deploy to Production]
        MONITOR[Monitor Metrics]
    end

    CODE --> BUILD
    BUILD --> TRAIN
    TRAIN --> EVALUATE
    EVALUATE -->|Pass| REGISTRY
    EVALUATE -->|Fail| CODE

    REGISTRY --> STAGE
    STAGE --> SMOKE
    SMOKE -->|Pass| PROD
    SMOKE -->|Fail| CODE

    PROD --> MONITOR
    MONITOR -->|Drift| CODE
```

---

## Model Evaluation Framework

```mermaid
graph TD
    subgraph "Evaluation Metrics"
        PERF[Performance Metrics<br/>Accuracy, F1, AUC]
        FAIR[Fairness Metrics<br/>Bias, Equality]
        ROB[Robustness<br/>Adversarial tests]
        EFF[Efficiency<br/>Latency, Throughput]
    end

    subgraph "Validation Tests"
        UNIT[Unit Tests<br/>Code quality]
        INTEG[Integration Tests<br/>End-to-end]
        SMOKE[Smoke Tests<br/>Basic functionality]
        PERF_TEST[Performance Tests<br/>Load testing]
    end

    subgraph "Decision Gates"
        GATE1{Meets Thresholds?}
        GATE2{Approved for Prod?}
    end

    PERF --> GATE1
    FAIR --> GATE1
    ROB --> GATE1
    EFF --> GATE1

    GATE1 -->|Yes| UNIT
    UNIT --> INTEG
    INTEG --> SMOKE
    SMOKE --> PERF_TEST

    PERF_TEST --> GATE2
    GATE2 -->|Yes| DEPLOY[Ready to Deploy]
    GATE2 -->|No| REJECT[Needs Improvement]
```

---

## Canary Deployment Strategy

```mermaid
graph TB
    subgraph "Traffic Split"
        USERS[All Users]
        LB[Load Balancer]
    end

    subgraph "Model Versions"
        OLD[Old Model<br/>90% Traffic]
        NEW[New Model<br/>10% Traffic]
    end

    subgraph "Monitoring"
        METRICS[Collect Metrics<br/>Error rate, Latency]
        COMPARE[Compare Performance]
        DECISION{Better Performance?}
    end

    USERS --> LB
    LB -->|90%| OLD
    LB -->|10%| NEW

    OLD --> METRICS
    NEW --> METRICS

    METRICS --> COMPARE
    COMPARE --> DECISION

    DECISION -->|Yes| RAMP[Increase to 50%]
    DECISION -->|No| ROLLBACK[Rollback change]

    RAMP --> DECISION
```

---

## Model Drift Detection

```mermaid
graph TB
    subgraph "Drift Monitoring"
        PSI[PSI Score<br/>Population Stability]
        ACC[Accuracy Monitor<br/>Label-based]
        PRED[Prediction Drift<br/>Output distribution]
    end

    subgraph "Detection"
        CALC[Calculate Drift Metrics]
        THRESHOLD{Exceeds Threshold?}
    end

    subgraph "Response"
        ALERT[Alert Team<br/>Investigate]
        RETRAIN[Retrain Model<br/>Fresh Data]
        ROLLBACK[Rollback<br/>Previous Model]
    end

    PSI --> CALC
    ACC --> CALC
    PRED --> CALC

    CALC --> THRESHOLD
    THRESHOLD -->|Yes| ALERT
    THRESHOLD -->|No| CONTINUE[Continue Monitoring]

    ALERT --> INVESTIGATE{Root Cause?}

    INVESTIGATE -->|Data Drift| RETRAIN
    INVESTIGATE -->|Model Bug| FIX[Fix Model]
    INVESTIGATE -->|Unknown| ROLLBACK

    CONTINUE --> CALC
```

---

## Experiment Tracking

```mermaid
graph LR
    subgraph "MLflow Tracking"
        EXP[Experiments]
        PARAMS[Hyperparameters]
        METRICS[Metrics]
        ARTIFACTS[Artifacts<br/>Models, Datasets]
    end

    subgraph "Model Registry"
        REGISTRY[Registered Models]
        VERSIONS[Version Management]
        STAGES[Staging<br/>Production]
    end

    EXP --> PARAMS
    EXP --> METRICS
    EXP --> ARTIFACTS

    PARAMS --> REGISTRY
    ARTIFACTS --> REGISTRY

    REGISTRY --> VERSIONS
    VERSIONS --> STAGES
```

---

## Decision Framework: Retrain or Not

```mermaid
graph TD
    START{Model Performance Drop?} --> CHECK[Check Metrics]

    CHECK --> PSI{PSI > 0.15?}
    CHECK --> ACC{Accuracy Drop > 5%?}

    PSI -->|Yes| RETRAIN[Retrain Model]
    ACC -->|Yes| RETRAIN

    PSI -->|No| DATA{Data Distribution Changed?}
    ACC -->|No| PRED{Prediction Drift?}

    DATA -->|Yes| INVESTIGATE[Investigate Data Drift]
    PRED -->|Yes| INVESTIGATE

    INVESTIGATE --> ROOT{Root Cause Found?}

    ROOT -->|Yes| FIX[Fix Issue]
    ROOT -->|No| RETRAIN

    FIX --> VERIFY{Verify Fix}
    VERIFY -->|Success| CONTINUE[Continue Monitor]
    VERIFY -->|Failed| RETRAIN

    RETRAIN --> EVALUATE[Re-evaluate]
    EVALUATE --> DEPLOY[Deploy if Better]
```

---

## Related Documents

- [6501-ML-Lifecycle-Management.md](../phases/phase6-rag/6500-mlops-pipelines/6501-ML-Lifecycle-Management.md)
