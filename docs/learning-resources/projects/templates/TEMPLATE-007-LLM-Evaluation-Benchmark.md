---
Document ID: TEMPLATE-007-LLM-Evaluation-Benchmark
Title: "PROJECT TEMPLATE: LLM Evaluation Benchmark"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['template', 'evaluation', 'benchmarks']
---

# PROJECT TEMPLATE: LLM Evaluation Benchmark

Comprehensive evaluation framework for LLMs.

## Project Structure

```text
llm-evaluation-benchmark/
├── README.md
├── pyproject.toml
├── uv.lock
├── config/
│   ├── models_config.yaml
│   ├── benchmarks_config.yaml
│   └── metrics_config.yaml
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── huggingface.py
│   │   ├── openai.py
│   │   └── local.py
│   ├── benchmarks/
│   │   ├── __init__.py
│   │   ├── mmlu.py          # MMLU benchmark
│   │   ├── truthfulqa.py    # TruthfulQA
│   │   ├── gsm8k.py         # Math reasoning
│   │   └── custom.py        # Custom benchmarks
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── perplexity.py
│   │   ├── bleu.py
│   │   ├── rouge.py
│   │   └── accuracy.py
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── single_model.py
│   │   └── comparison.py
│   ├── reporters/
│   │   ├── __init__.py
│   │   ├── console.py
│   │   ├── html.py
│   │   └── json.py
│   └── runner.py            # Evaluation runner
├── data/
│   ├── benchmarks/
│   └── results/
├── scripts/
│   ├── run_benchmark.py
│   ├── compare_models.py
│   └── generate_report.py
└── tests/
    └── test_evaluation.py
```

## Features

- Multiple benchmark support
- Various metrics
- Model comparison
- HTML reports
- Leaderboard generation

## Quick Start

### Run Single Benchmark

```python
from src.runner import EvaluationRunner
from src.models.huggingface import HuggingFaceModel

model = HuggingFaceModel("gpt2")
runner = EvaluationRunner(model)

results = runner.run_benchmark("mmlu")
print(results)
```

### Compare Models

```bash
python scripts/compare_models.py \
  --models gpt2,phi-2,distilgpt2 \
  --benchmarks mmlu,gsm8k \
  --output results/comparison.json
```

### Custom Benchmark

```python
from src.benchmarks.custom import CustomBenchmark

benchmark = CustomBenchmark(
    name="my_benchmark",
    questions=question_list,
    evaluator=answer_checker
)

results = benchmark.evaluate(model)
```

## Available Benchmarks

- **MMLU**: General knowledge
- **TruthfulQA**: Truthfulness
- **GSM8K**: Math reasoning
- **HellaSwag**: Common sense
- **PIQA**: Physical reasoning
- **Custom**: Your own benchmarks

## Metrics

| Category | Metrics |
|----------|---------|
| Language Model | Perplexity, BPC |
| Generation | BLEU, ROUGE, METEOR |
| Classification | Accuracy, F1, Precision/Recall |
| Reasoning | Exact match, Step accuracy |

## Reports

Generate HTML report:
```bash
python scripts/generate_report.py \
  --input results/ \
  --output report.html \
  --format html
```

## Configuration

`config/models_config.yaml`:
```yaml
models:
  - name: "gpt2"
    type: "huggingface"
    path: "gpt2"

  - name: "gpt-4"
    type: "openai"
    model: "gpt-4"
```

`config/benchmarks_config.yaml`:
```yaml
benchmarks:
  mmlu:
    subjects: ["math", "cs", "history"]
    num_shots: 5

  gsm8k:
    grade_school_math: true
    show_work: true
```

## Leaderboard

```python
from src.evaluators.comparison import ModelComparison

comparison = ModelComparison(
    models=["gpt2", "phi-2", "distilgpt2"],
    benchmarks=["mmlu", "gsm8k", "truthfulqa"]
)

leaderboard = comparison.run()
comparison.print_leaderboard(leaderboard)
```

---

**Difficulty:** ⭐⭐ Intermediate

**Estimated Time:** 6-10 hours

**Skills:** Evaluation, Metrics, Benchmarking
