---
Document ID: TEMPLATE-011-Model-Merging-MoE
Title: "PROJECT TEMPLATE: Model Merging & MoE"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Beginner
---

# PROJECT TEMPLATE: Model Merging & MoE

Merge and combine LLMs for better performance.

## Project Structure

```text
model-merging-moe/
├── README.md
├── requirements.txt
├── config/
│   ├── merge_config.yaml
│   └── moe_config.yaml
├── src/
│   ├── __init__.py
│   ├── merging/
│   │   ├── __init__.py
│   │   ├── linear.py        # Linear merging
│   │   ├── task_arithmetic.py
│   │   ├── ties.py          # TIES merging
│   │   └── dare.py          # DARE merging
│   ├── moe/
│   │   ├── __init__.py
│   │   ├── layers.py        # MoE layers
│   │   ├── router.py        # Expert routing
│   │   ├── experts.py       # Expert models
│   │   └── trainer.py       # MoE training
│   ├── pruners/
│   │   ├── __init__.py
│   │   ├── magnitude.py
│   │   ├── wanda.py
│   │   └── structured.py
│   ├── converters/
│   │   ├── __init__.py
│   │   ├── to_moe.py
│   │   └── from_moe.py
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── benchmark.py
│   │   └── comparison.py
│   └── utils/
│       ├── __init__.py
│       ├── checkpoint.py
│       └── visualization.py
├── models/
│   ├── base/
│   ├── fine-tuned/
│   └── merged/
├── scripts/
│   ├── merge.py
│   ├── create_moe.py
│   ├── prune.py
│   └── evaluate.py
└── tests/
    └── test_merging.py
```

## Features

- Model merging techniques
- Mixture of Experts (MoE)
- Model pruning
- Conversion tools
- Benchmarking

## Quick Start

### Linear Merging

```python
from src.merging.linear import LinearMerger

merger = LinearMerger(
    models=["model_a", "model_b", "model_c"],
    weights=[0.5, 0.3, 0.2]
)

merged_model = merger.merge()
merged_model.save("models/merged/linear_merge.pt")
```

### Task Arithmetic

```python
from src.merging.task_arithmetic import TaskArithmeticMerger

merger = TaskArithmeticMerger(
    task_vectors={
        "math": "math_finetuned",
        "code": "code_finetuned",
        "chat": "chat_finetuned"
    },
    scaling_factor=0.5
)

merged = merger.merge(base_model="base_model")
```

### TIES Merging

```python
from src.merging.ties import TIESMerger

merger = TIESMerger(
    models=["model_a", "model_b"],
    merge_method="sign"  # or "magnitude"
)

merged = merger.merge(dense_ratio=0.5)
```

## Mixture of Experts

### Create MoE from Checkpoints

```python
from src.moe.converters.to_moe import MoEConverter

converter = MoEConverter(
    expert_models=[
        "models/math_model",
        "models/code_model",
        "models/chat_model"
    ],
    num_experts_per_token=2
)

moe_model = converter.convert(base_model="models/base")
```

### Custom MoE Layer

```python
from src.moe.layers import MoELinear

moe_layer = MoELinear(
    in_features=768,
    out_features=768,
    num_experts=4,
    top_k=2,
    capacity_factor=1.5
)

output = moe_layer(input_tensor)
```

### Train MoE Router

```python
from src.moe.trainer import MoETrainer

trainer = MoETrainer(
    model=moe_model,
    router_loss_coef=0.1,
    load_balance_coef=0.01
)

trainer.train(
    train_data=dataset,
    num_epochs=3,
    learning_rate=1e-4
)
```

## Model Pruning

### Magnitude Pruning

```python
from src.pruners.magnitude import MagnitudePruner

pruner = MagnitudePruner(
    model=model,
    sparsity=0.5  # Remove 50% of weights
)

pruned_model = pruner.prune()
```

### WANDA Pruning

```python
from src.pruners.wanda import WANDAPruner

pruner = WANDAPruner(
    model=model,
    calibration_data=calibration_dataset
)

pruned_model = pruner.prune(sparsity=0.7)
```

## Evaluation & Comparison

```bash
# Compare merged models
python scripts/evaluate.py \
  --models base,merged_a,merged_b \
  --benchmarks mmlu,gsm8k \
  --output results/comparison.json

# Benchmark MoE vs dense
python scripts/evaluate.py \
  --models dense_model,moe_model \
  --metrics latency,throughput,accuracy
```

## Visualization

```python
from src.utils.visualization import plot_expert_usage

# Visualize expert selection
plot_expert_usage(
    router_outputs=router_outputs,
    num_experts=4,
    save_path="expert_usage.png"
)
```

## Merge Strategies

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| Linear | Similar tasks | Simple | Limited expressivity |
| Task Arithmetic | Diverse tasks | Task-specific | Requires task vectors |
| TIES | Many models | Preserves signs | Complex |
| DARE | Drop-based | Fast | May lose info |

---

**Difficulty:** Advanced
**Estimated Time:** 10-15 hours
**Skills:** Model merging, MoE, Pruning
