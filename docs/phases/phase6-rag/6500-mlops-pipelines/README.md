---
Document ID: 6500-MLOPS-PIPELINES-README
Title: "6500: MLOps Pipelines for RAG"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Prerequisites: []
Estimated Time: 18 hours
Tags: ['module', 'mlops', 'model-registry']
---

# 6500: MLOps Pipelines for RAG

## Module Overview

This module covers MLOps practices specifically for RAG systems, including lifecycle management, CI/CD, and model registries. You'll learn to build production-ready ML pipelines for retrieval-augmented generation.

**Why This Matters:**
- RAG systems require continuous updates and monitoring
- CI/CD ensures reliable model deployments
- Model registries track model versions and lineage
- Production ML needs automation and reproducibility

## Learning Objectives

After completing this module, you will be able to:

- **ML Lifecycle**: Manage the complete ML pipeline for RAG
- **CI/CD for ML**: Build automated testing and deployment
- **Model Registry**: Track and version models effectively
- **Re-Embedding Policy**: Separate churn upserts from forced full re-embeds and size the experiments that ship them
- **Response Caching and Stage Scaling**: Cache at the response boundary and scale each stage on its own signal
- **Monitoring**: Track model performance and data drift
- **Production ML**: Deploy and maintain RAG systems

## Module Contents

### [6501: ML Lifecycle Management](./6501-ML-Lifecycle-Management.md)
**End-to-End ML Pipeline**

- The complete ML lifecycle for RAG
- The five lifecycle stages in depth
- How data, training, and deployment connect
- Monitoring and feedback across stages
- The stage-by-stage checklist

**Experiments:**
- Build ML pipeline for RAG
- Implement data versioning
- Set up model evaluation
- Deploy and monitor system

### [6502: CI/CD for ML](./6502-CI-CD-for-ML.md)
**Continuous Integration and Deployment**

- CI/CD architecture for ML
- Pipeline configuration
- Job dependencies
- Automated training
- Validation gates and deployment

**Experiments:**
- Set up GitHub Actions for ML
- Implement automated testing
- Build deployment pipeline
- Test rollback procedures

### [6503: Model Registry](./6503-Model-Registry.md)
**Model Versioning and Governance**

- Model registry architecture
- Model versioning
- Metadata and lineage
- Aliases and promotion workflows
- Registries in practice: MLflow and Weights & Biases

**Experiments:**
- Set up MLflow model registry
- Track model versions
- Implement model promotion
- Build model governance

### [6504: Re-Embedding Policy and A/B Testing](./6504-Re-Embedding-Policy-and-AB-Testing.md)
**Updating Embeddings and Shipping Them Honestly**

- The churn ledger: incremental upserts vs calendar-cadence rebuilds
- Cross-space incomparability: why a model change forces the full pass
- The shadow window: dual-write economics and the cutover gate
- Sizing on discordant pairs, the peeking trap, and fixed horizons
- Human evaluation with chance-corrected kappa

**Experiments:**
- Price a re-embedding cadence for your own corpus churn
- Run the shadow-window gate on a golden set
- Size an embedder migration before opening the window

### [6505: Response Caching and Stage Scaling](./6505-Response-Caching-and-Stage-Scaling.md)
**The Fleet-Level Bill: What Not to Recompute, What to Provision**

- The four cache tiers: retrieval-only, raw-key, normalized-key, semantic
- The threshold that cuts both ways: false hits vs forfeited paraphrases
- Invalidation: query-only vs TTL vs version-keyed after the re-embedding cutover
- Per-stage autoscaling: two shortfalls, two signals, two step sizes
- The prefill/decode split and the production disaggregators
- One fleet day priced: token bill, search bill, replica bill

**Experiments:**
- Key a response cache on (query, index_version) and re-run the cutover
- Tune a semantic threshold on both error types with near-topic negatives
- Price per-stage autoscaling against peak provisioning on your own traffic curve

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 1400: [LLMOps and Model Serving](../../phase1-infra/1400-llmops/README.md) (MLOps fundamentals)
- [ ] Module 2400: [LLM Pretraining](../../phase2-foundations/2400-pretraining/README.md) (ML pipelines)
- [ ] Modules 6100–6400: [RAG components](../6100-vector/README.md) ([vector](../6100-vector/README.md) → [database](../6400-vector-databases/README.md))
- [ ] Git and CI/CD fundamentals
- [ ] Docker and deployment basics

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** ML lifecycle, CI/CD, model registry
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** MLOps pipeline projects
- **Duration:** 3 hours
- **Topics:**
  - Build complete ML pipeline
  - Set up CI/CD for RAG
  - Implement model registry
  - Deploy to production
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **[1400: LLMOps and Model Serving](../../phase1-infra/1400-llmops/README.md)** (MLOps fundamentals)
- **[2400: LLM Pretraining](../../phase2-foundations/2400-pretraining/README.md)** (training pipelines)
- **[6400: Vector Databases](../6400-vector-databases/README.md)** (data infrastructure)
- **[7300: Multi-Agent Orchestration](../../phase7-agentic/7300-orchestration/README.md)** (agent workflows)

## Time Commitment

| Activity | Time |
|----------|------|
| [6501: ML Lifecycle Management](./6501-ML-Lifecycle-Management.md) | 4 hours |
| [6502: CI/CD for ML](./6502-CI-CD-for-ML.md) | 4 hours |
| [6503: Model Registry](./6503-Model-Registry.md) | 4 hours |
| [6504: Re-Embedding Policy and A/B Testing](./6504-Re-Embedding-Policy-and-AB-Testing.md) | 3 hours |
| [6505: Response Caching and Stage Scaling](./6505-Response-Caching-and-Stage-Scaling.md) | 3 hours |
| Quiz | 30 minutes |
| Practice | 3 hours |
| **Total** | **21.5 hours** |

## Resources

**Essential Tools:**
- MLflow (experiment tracking and registry)
- GitHub Actions (CI/CD)
- Docker / Kubernetes (deployment)
- Weights & Biases (experiment tracking)
- DVC (data versioning)

**Essential Concepts:**
- Feature stores
- Model serving
- A/B testing
- Canary deployments
- Blue-green deployments

## ML Pipeline Stages

```text
┌─────────────────────────────────────────────────────┐
│                  ML Lifecycle                        │
├─────────────────────────────────────────────────────┤
│ 1. Data Collection                                   │
│    ↓                                                 │
│ 2. Data Processing & Feature Engineering             │
│    ↓                                                 │
│ 3. Model Training                                    │
│    ↓                                                 │
│ 4. Model Evaluation                                  │
│    ↓                                                 │
│ 5. Model Registry                                    │
│    ↓                                                 │
│ 6. Deployment (Staging)                              │
│    ↓                                                 │
│ 7. Testing & Validation                              │
│    ↓                                                 │
│ 8. Production Deployment                             │
│    ↓                                                 │
│ 9. Monitoring & Logging                              │
│    ↓                                                 │
│ 10. Feedback & Retraining                            │
└─────────────────────────────────────────────────────┘
```

## CI/CD Pipeline Comparison

| Stage | Traditional Software | ML Pipelines |
|-------|---------------------|--------------|
| Code | Unit tests | Unit + model tests |
| Build | Compile | Train model |
| Test | Integration tests | Evaluation on test set |
| Deploy | Push to prod | A/B test, canary |
| Monitor | Error rates | Accuracy, drift |

## Model Registry Features

| Feature | MLflow | Weights & Biases | DVC |
|---------|--------|------------------|-----|
| Version Control | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Metadata | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Deployment | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Lineage | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Open Source | ✅ | ✅ | ✅ |

## Deployment Strategies

| Strategy | Risk | Speed | Use Case |
|----------|------|-------|----------|
| Big Bang | High | Fast | Small changes |
| Blue-Green | Low | Medium | Major updates |
| Canary | Medium | Slow | Critical systems |
| A/B Testing | Low | Slow | Feature validation |

## Monitoring Metrics

| Category | Metrics |
|----------|----------|
| **System** | Latency, throughput, error rate |
| **Model** | Accuracy, F1, perplexity |
| **Data** | Drift, distribution changes |
| **Business** | User satisfaction, conversion |

## Tips for Success

1. **Start simple**: Basic CI/CD before complex MLops
2. **Version everything**: Data, models, code, configs
3. **Automate testing**: Catch issues before production
4. **Monitor continuously**: Catch degradation early
5. **Document decisions**: Reproducibility is key

## Common Pitfalls

1. **Skipping staging:** Testing in prod is dangerous
2. **No rollback plan:** deployments fail
3. **Ignoring data drift:** Models degrade over time
4. **Poor documentation:** Can't reproduce results
5. **Over-engineering:** Start simple, scale when needed

## Production Checklist

Before deploying to production:
- [ ] Automated tests passing
- [ ] Model evaluated on test set
- [ ] Performance benchmarks met
- [ ] Rollback plan documented
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Documentation complete
- [ ] Stakeholders notified

## Model Promotion Workflow

```text
Development → Staging → Production
     ↓            ↓           ↓
   Experimental  A/B Test    Full Traffic
     ↓            ↓           ↓
   Archived      Rollback    Monitor
```

## MLflow vs W&B vs DVC

| Feature | MLflow | W&B | DVC |
|---------|--------|-----|-----|
| Experiment Tracking | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Model Registry | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Data Versioning | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Collaboration | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Ease of Use | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

**Next Module:** [7100: Agent Architecture](../../phase7-agentic/7100-architecture/README.md)

**Previous Module:** [6400: Vector Databases](../6400-vector-databases/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 6 documentation.

