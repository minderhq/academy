---
Document ID: 2403
Title: Evaluation Frameworks for Language Models
Phase: 2
Module: 2400
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 6 hours
Prerequisites: See module README
Related: See module README
Tags: ['training', 'pretraining', 'evaluation', 'fsdp']
---

# 2403: Evaluation Frameworks for Language Models

**"Measuring Intelligence"** - Comprehensive evaluation of LLM quality and capabilities.

---

## Abstract

**Prerequisites:** [2401: Pre-training Fundamentals](2401-Pre-training-Fundamentals.md)
**Time:** 3-4 hours to read, days to implement
**Difficulty:** ⭐⭐⭐⭐ Advanced

### What You'll Learn

After this guide, you will:
- ✅ Understand standard LLM benchmarks (MMLU, HellaSwag, GSM8K, etc.)
- ✅ Implement perplexity and next-token prediction metrics
- ✅ Evaluate human preference metrics (truthfulness, helpfulness)
- ✅ Set up automated evaluation pipelines
- ✅ Compare models fairly and reproducibly
- ✅ Interpret evaluation results correctly

---

## Part 1: Perplexity & Language Modeling Metrics

### Understanding Perplexity

```python
"""
Perplexity: The fundamental metric for language models

Perplexity measures how "surprised" a model is by unseen text.
Lower perplexity = better predictions
"""

import torch
import torch.nn.functional as F
import math

def calculate_perplexity(model, dataloader, device):
    """
    Calculate perplexity on a dataset

    PPL = exp(loss)
    where loss = cross-entropy loss

    Interpretation:
    - PPL = 10: Model is 10x uncertain (like choosing among 10 words)
    - PPL = 20: Model is 20x uncertain
    - Random model: PPL = vocab_size (~10,000 for English)
    - Good model: PPL = 10-30
    """

    model.eval()
    total_loss = 0
    total_tokens = 0

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            # Forward pass
            outputs = model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits

            # Calculate loss
            # Shift for next-token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()

            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100,  # Ignore padding
                reduction='sum'
            )

            total_loss += loss.item()
            total_tokens += (shift_labels != -100).sum().item()

    # Average loss per token
    avg_loss = total_loss / total_tokens

    # Perplexity
    perplexity = math.exp(avg_loss)

    return {
        "loss": avg_loss,
        "perplexity": perplexity,
        "tokens": total_tokens
    }

# Benchmark comparison
benchmarks = {
    "GPT-2 (124M)": {
        "wikitext-103": 28.5,
        "webtext2": 18.34,
    },
    "GPT-3 (175B)": {
        "webtext2": 20.50,
    },
    "LLaMA (7B)": {
        "wikitext": 15.0,  # Estimated
    },
    "Mistral (7B)": {
        "various": 10-15,  # Better than LLaMA
    },
}

print("\nPerplexity Benchmarks:")
for model, scores in benchmarks.items():
    for dataset, ppl in scores.items():
        print(f"  {model} on {dataset}: PPL = {ppl:.2f}")
```

### Bits Per Character (BPC)

```python
def calculate_bpc(model, dataloader, device):
    """
    Bits Per Character: Alternative to perplexity

    BPC = log2(perplexity)

    Used for:
    - Character-level models
    - Multilingual models
    - Easier to interpret than PPL
    """

    ppl_result = calculate_perplexity(model, dataloader, device)
    perplexity = ppl_result["perplexity"]

    bpc = math.log2(perplexity)

    return {
        "bpc": bpc,
        "perplexity": perplexity
    }

# BPC benchmarks
bpc_benchmarks = {
    "Random baseline": {"bpc": 13.2},  # log2(10000)
    "Character-level CNN": {"bpc": 1.5},
    "Transformer (small)": {"bpc": 1.1},
    "State-of-the-art": {"bpc": 0.9},  # GPT-3 level
}
```

---

## Part 2: Standard Benchmarks

### MMLU (Massive Multitask Language Understanding)

```python
"""
MMLU: Test knowledge across 57 subjects

Subjects include:
- Humanities (Art, Philosophy, History)
- STEM (Math, Physics, Chemistry, Biology)
- Social Sciences (Psychology, Sociology, Politics)
- Other (Business, Law, Medicine)

Format: Multiple choice (4 options)
"""

from datasets import load_dataset
from typing import List, Dict
import re

def evaluate_mmlu(model, tokenizer, subjects="all"):
    """
    Evaluate model on MMLU benchmark

    Returns accuracy per subject and overall
    """

    # Load MMLU dataset
    if subjects == "all":
        dataset = load_dataset("cais/mmlu", "all", split="test")
    else:
        dataset = load_dataset("cais/mmlu", subjects, split="test")

    results = {}

    for example in dataset:
        subject = example["subject"]
        question = example["question"]
        choices = example["choices"]  # List of 4 options
        answer = example["answer"]  # Correct index (0-3)

        # Format question
        prompt = format_mmlu_prompt(question, choices)

        # Get model prediction
        prediction = model.predict_choice(prompt, choices)

        # Record result
        if subject not in results:
            results[subject] = {"correct": 0, "total": 0}

        results[subject]["total"] += 1
        if prediction == answer:
            results[subject]["correct"] += 1

    # Calculate accuracies
    accuracies = {}
    for subject, counts in results.items():
        accuracies[subject] = counts["correct"] / counts["total"]

    # Overall accuracy
    total_correct = sum(r["correct"] for r in results.values())
    total_questions = sum(r["total"] for r in results.values())
    overall_accuracy = total_correct / total_questions

    return {
        "overall": overall_accuracy,
        "by_subject": accuracies
    }

def format_mmlu_prompt(question, choices):
    """Format MMLU question for model"""
    prompt = f"Question: {question}\n"
    for i, choice in enumerate(choices):
        prompt += f"{chr(65+i)}. {choice}\n"
    prompt += "Answer:"
    return prompt

# MMLU benchmarks
mmlu_benchmarks = {
    "GPT-3 (175B)": {"5-shot": 43.9},
    "GPT-4": {"5-shot": 86.4},
    "Claude 3 Opus": {"5-shot": 86.8},
    "LLaMA-2 (7B)": {"5-shot": 45.3},
    "LLaMA-2 (70B)": {"5-shot": 67.9},
    "Mistral (7B)": {"5-shot": 60.0},  # Estimated
}
```

### HellaSwag (Common Sense Reasoning)

```python
"""
HellaSwag: Test if model can predict likely endings

Task: Given a context, choose the most likely ending
Tests: Common sense reasoning about everyday situations
"""

def evaluate_hellaswag(model, tokenizer):
    """
    Evaluate on HellaSwag dataset

    Format: Context + 2 possible endings
    Task: Choose the more plausible ending
    """

    dataset = load_dataset("hellaswag", split="validation")

    correct = 0
    total = 0

    for example in dataset:
        context = example["ctx"]
        endings = [example["endings"][0], example["endings"][1]]
        label = example["label"]  # 0 or 1

        # Format prompt
        prompt = f"Context: {context}\n"
        prompt += "What happens next?\n"
        prompt += f"A. {endings[0]}\n"
        prompt += f"B. {endings[1]}\n"

        # Get prediction
        prediction = model.predict_choice(prompt, endings)

        if prediction == label:
            correct += 1
        total += 1

    accuracy = correct / total

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total
    }

# HellaSwag benchmarks
hellaswag_benchmarks = {
    "GPT-3 (175B)": {"accuracy": 78.1},
    "GPT-4": {"accuracy": 95.3},
    "LLaMA-2 (7B)": {"accuracy": 78.0},
    "LLaMA-2 (70B)": {"accuracy": 86.0},
}
```

### GSM8K (Mathematical Reasoning)

```python
"""
GSM8K: Grade school math problems

Task: Solve word problems
Tests: Mathematical reasoning and calculation
"""

def evaluate_gsm8k(model, tokenizer):
    """
    Evaluate on GSM8K dataset

    Format: Word problem → Numerical answer
    Challenge: Requires multi-step reasoning
    """

    dataset = load_dataset("gsm8k", "main", split="test")

    results = []

    for example in dataset:
        question = example["question"]
        answer = example["answer"]  # Contains solution

        # Extract final numerical answer
        # Format: "...#### 42"
        final_answer = extract_number(answer)

        # Get model prediction
        prediction = model.solve_math_problem(question)

        # Check if correct (with tolerance)
        if abs(prediction - final_answer) < 0.01:
            results.append(1)
        else:
            results.append(0)

    accuracy = sum(results) / len(results)

    return {
        "accuracy": accuracy,
        "total": len(results)
    }

def extract_number(text):
    """Extract final number from GSM8K answer"""
    match = re.search(r'####\s*([-+]?\d*\.?\d+)', text)
    if match:
        return float(match.group(1))
    return None

# GSM8K benchmarks
gsm8k_benchmarks = {
    "GPT-3 (175B)": {"accuracy": 17.0},  # 0-shot
    "GPT-3 (175B)": {"accuracy": 33.5},  # 5-shot
    "GPT-4": {"accuracy": 92.0},
    "LLaMA-2 (70B)": {"accuracy": 56.8},
    "Claude 3 Opus": {"accuracy": 95.0},
}
```

### HumanEval (Python Code Generation)

```python
"""
HumanEval: Test Python code generation

Task: Complete Python functions
Tests: Code generation and correctness
"""

def evaluate_humaneval(model, tokenizer):
    """
    Evaluate on HumanEval dataset

    Format: Function signature + docstring → Complete function
    Evaluation: Pass unit tests
    """

    dataset = load_dataset("openai_humaneval", "test")

    results = []

    for example in dataset:
        prompt = example["prompt"]  # Function signature + docstring
        canonical_solution = example["canonical_solution"]
        test_code = example["test"]  # Unit tests

        # Generate completion
        generated_code = model.generate_code(prompt)

        # Execute tests
        passed = run_tests(generated_code, test_code)

        results.append(passed)

    pass_rate = sum(results) / len(results)

    return {
        "pass_rate": pass_rate,
        "total": len(results)
    }

def run_tests(generated_code, test_code):
    """
    Safely execute unit tests

    Returns True if all tests pass
    """
    import sys
    import io
    from contextlib import redirect_stdout

    # Combine code and tests
    full_code = generated_code + "\n" + test_code

    # Execute in sandbox
    try:
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        exec(full_code, {"__name__": "__main__"})

        # Restore stdout
        sys.stdout = old_stdout
        return True

    except Exception:
        return False
    finally:
        sys.stdout = old_stdout

# HumanEval benchmarks
humaneval_benchmarks = {
    "GPT-3 (175B)": {"pass@1": 11.6},  # Generate once, test once
    "GPT-4": {"pass@1": 67.0},
    "StarCoder (15B)": {"pass@1": 33.6},
    "CodeLLaMA (7B)": {"pass@1": 31.2},
}
```

---

## Part 3: Human Preference Metrics

### TruthfulQA (Factuality)

```python
"""
TruthfulQA: Test if model generates true answers

Problem: Models often mimic common misconceptions
Task: Answer questions while avoiding false beliefs
"""

def evaluate_truthfulqa(model, tokenizer):
    """
    Evaluate truthfulness

    Two metrics:
    1. Truthfulness: Is the answer factually correct?
    2. Informativeness: Does the answer address the question?
    """

    dataset = load_dataset("truthful_qa", "validation")

    results = []

    for example in dataset:
        question = example["question"]
        correct_answers = example["correct_answers"]
        incorrect_answers = example["incorrect_answers"]

        # Generate answer
        generated = model.generate(question, max_tokens=100)

        # Check against correct/incorrect
        is_true = check_if_true(generated, correct_answers, incorrect_answers)
        is_informative = len(generated) > 20  # Simple heuristic

        results.append({
            "truthful": is_true,
            "informative": is_informative
        })

    # Calculate metrics
    truthfulness = sum(r["truthful"] for r in results) / len(results)
    informativeness = sum(r["informative"] for r in results) / len(results)

    # Combined metric
    score = min(truthfulness, informativeness)

    return {
        "truthfulness": truthfulness,
        "informativeness": informativeness,
        "score": score
    }

def check_if_true(generated, correct, incorrect):
    """Check if generated answer matches true answers"""
    # This would use NLP similarity or exact matching
    # Simplified version
    generated_lower = generated.lower()

    # Check if contains incorrect info
    for inc in incorrect:
        if inc.lower() in generated_lower:
            return False

    # Check if contains correct info
    for cor in correct:
        if cor.lower() in generated_lower:
            return True

    return True  # Assume true if no incorrect info found

# TruthfulQA benchmarks
truthfulqa_benchmarks = {
    "GPT-3 (175B)": {"score": 0.38},  # Low truthfulness
    "GPT-4": {"score": 0.62},
    "LLaMA (7B)": {"score": 0.41},
    "Claude 3 Opus": {"score": 0.65},
}
```

### Helpful & Harmless (HH) Evaluation

```python
"""
HH (Helpful & Harmless) Evaluation

Tests:
- Helpfulness: Does the answer help the user?
- Harmlessness: Is the answer safe and ethical?
"""

def evaluate_hh(model, tokenizer):
    """
    Evaluate on HH dataset

    Two aspects:
    1. Helpfulness: Quality and usefulness of response
    2. Harmlessness: Safety and ethical alignment
    """

    dataset = load_dataset("Anthropic/hh-rlhf", "test")

    results = []

    for example in dataset:
        prompt = example["prompt"]
        chosen_response = example["chosen"]  # Preferred by humans
        rejected_response = example["rejected"]  # Less preferred

        # Generate response
        generated = model.generate(prompt)

        # Compare to chosen
        helpfulness = compare_responses(generated, chosen_response)
        harmlessness = check_safety(generated)

        results.append({
            "helpful": helpfulness,
            "harmless": harmlessness
        })

    helpful_rate = sum(r["helpful"] for r in results) / len(results)
    harmless_rate = sum(r["harmless"] for r in results) / len(results)

    return {
        "helpful": helpful_rate,
        "harmless": harmless_rate,
        "combined": (helpful + harmless) / 2
    }

def compare_responses(generated, reference):
    """Compare generated response to reference"""
    # This would use a separate reward model or human evaluation
    # Simplified: Check length and keyword overlap
    return 0.5 < len(generated) / len(reference) < 2.0

def check_safety(text):
    """Check if response is safe"""
    unsafe_keywords = [
        "violence", "harm", "illegal", "steal", "kill",
        # ... (more comprehensive list)
    ]

    text_lower = text.lower()

    for keyword in unsafe_keywords:
        if keyword in text_lower:
            return False

    return True
```

---

## Part 4: Automated Evaluation Pipeline

### Complete Evaluation System

```python
"""
Complete automated evaluation pipeline
"""

import json
from pathlib import Path
from typing import Dict, List
import wandb

class ModelEvaluator:
    """Comprehensive model evaluation"""

    def __init__(self, model, tokenizer, output_dir="./eval_results"):
        self.model = model
        self.tokenizer = tokenizer
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def evaluate_all(self, model_name: str):
        """
        Run all benchmarks and generate report

        Benchmarks:
        1. Perplexity (language modeling)
        2. MMLU (knowledge)
        3. HellaSwag (reasoning)
        4. GSM8K (math)
        5. HumanEval (code)
        6. TruthfulQA (factuality)
        """

        print(f"Evaluating {model_name}...\n")

        results = {
            "model": model_name,
            "date": str(datetime.now()),
        }

        # 1. Perplexity
        print("[1/6] Calculating perplexity...")
        ppl_result = self.evaluate_perplexity()
        results["perplexity"] = ppl_result
        print(f"  Perplexity: {ppl_result['perplexity']:.2f}")

        # 2. MMLU
        print("[2/6] Evaluating MMLU...")
        mmlu_result = self.evaluate_mmlu()
        results["mmlu"] = mmlu_result
        print(f"  MMLU Accuracy: {mmlu_result['overall']:.2%}")

        # 3. HellaSwag
        print("[3/6] Evaluating HellaSwag...")
        hellaswag_result = self.evaluate_hellaswag()
        results["hellaswag"] = hellaswag_result
        print(f"  HellaSwag Accuracy: {hellaswag_result['accuracy']:.2%}")

        # 4. GSM8K
        print("[4/6] Evaluating GSM8K...")
        gsm8k_result = self.evaluate_gsm8k()
        results["gsm8k"] = gsm8k_result
        print(f"  GSM8K Accuracy: {gsm8k_result['accuracy']:.2%}")

        # 5. HumanEval
        print("[5/6] Evaluating HumanEval...")
        humaneval_result = self.evaluate_humaneval()
        results["humaneval"] = humaneval_result
        print(f"  HumanEval Pass@1: {humaneval_result['pass_rate']:.2%}")

        # 6. TruthfulQA
        print("[6/6] Evaluating TruthfulQA...")
        truthfulqa_result = self.evaluate_truthfulqa()
        results["truthfulqa"] = truthfulqa_result
        print(f"  TruthfulQA Score: {truthfulqa_result['score']:.2%}")

        # Save results
        self.save_results(results)

        # Generate report
        self.generate_report(results)

        # Upload to W&B
        wandb.init(project="llm-evaluation", name=model_name)
        wandb.log(results)

        return results

    def save_results(self, results: Dict):
        """Save results to JSON"""
        output_path = self.output_dir / f"results_{results['model']}.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {output_path}")

    def generate_report(self, results: Dict):
        """Generate human-readable report"""

        report = f"""
# Evaluation Report: {results['model']}

Date: {results['date']}

## Summary

| Benchmark | Metric | Score |
|-----------|--------|-------|
| Perplexity | Lower is better | {results['perplexity']['perplexity']:.2f} |
| MMLU | Accuracy | {results['mmlu']['overall']:.2%} |
| HellaSwag | Accuracy | {results['hellaswag']['accuracy']:.2%} |
| GSM8K | Accuracy | {results['gsm8k']['accuracy']:.2%} |
| HumanEval | Pass@1 | {results['humaneval']['pass_rate']:.2%} |
| TruthfulQA | Score | {results['truthfulqa']['score']:.2%} |

## Detailed Results

### MMLU (Knowledge)
"""
        report += f"""
**Overall Accuracy:** {results['mmlu']['overall']:.2%}

| Subject | Accuracy |
|---------|----------|
"""
        for subject, acc in results['mmlu']['by_subject'].items():
            report += f"| {subject} | {acc:.2%} |\n"

        report += f"""

### Comparison to Baselines

| Model | MMLU | HellaSwag | GSM8K | HumanEval |
|-------|------|-----------|-------|-----------|
| GPT-3 (175B) | 43.9% | 78.1% | 33.5% | 11.6% |
| LLaMA-2 (7B) | 45.3% | 78.0% | 14.3% | 10.5% |
| Your Model | {results['mmlu']['overall']:.1%} | {results['hellaswag']['accuracy']:.1%} | {results['gsm8k']['accuracy']:.1%} | {results['humaneval']['pass_rate']:.1%} |

---

Generated by PROJECT-OMEGA Evaluation Framework
"""

        # Save report
        report_path = self.output_dir / f"report_{results['model']}.md"
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"Report saved to {report_path}")
```

---

## Part 5: Evaluation Best Practices

### Do's and Don'ts

```yaml
Evaluation Best Practices:

  DO:
    - Use consistent evaluation across models
    - Report exact dataset versions
    - Include standard error/confidence intervals
    - Evaluate on held-out test set only
    - Document hyperparameters and prompts
    - Use multiple metrics for comprehensive view
    - Compare to appropriate baselines
    - Reproduce published benchmarks when possible

  DON'T:
    - Evaluate on training data
    - Cherry-pick best results
    - Compare models on different datasets
    - Ignore model size in comparisons
    - Forget to report uncertainty
    - Use misleading visualizations
    - Over-interpret small differences
```

### Statistical Significance

```python
"""
Statistical testing for model comparison
"""

import numpy as np
from scipy import stats

def bootstrap_accuracy(predictions, labels, n_bootstrap=10000):
    """
    Calculate confidence interval for accuracy

    Bootstrap: Resample with replacement to estimate uncertainty
    """

    accuracies = []
    n = len(predictions)

    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        resampled_preds = [predictions[i] for i in indices]
        resampled_labels = [labels[i] for i in indices]

        # Calculate accuracy
        acc = sum(p == l for p, l in zip(resampled_preds, resampled_labels)) / n
        accuracies.append(acc)

    # Calculate confidence interval
    ci_lower = np.percentile(accuracies, 2.5)
    ci_upper = np.percentile(accuracies, 97.5)

    return {
        "mean": np.mean(accuracies),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "std": np.std(accuracies)
    }

def compare_models(model1_results, model2_results):
    """
    Statistical comparison between two models

    Use paired bootstrap test or McNemar's test
    """

    # Example: McNemar's test for paired binary outcomes
    #          (both models evaluated on same data)

    # Contingency table:
    #               Model2 Correct  Model2 Wrong
    # Model1 Correct      a              b
    # Model1 Wrong       c              d

    from statsmodels.stats.contingency_tables import mcnemar

    # Build contingency table
    # (Assumes paired data)
    table = [[a, b], [c, d]]

    # McNemar's test
    result = mcnemar(table, exact=True, correction=True)

    if result.pvalue < 0.05:
        print("Models are significantly different (p < 0.05)")
    else:
        print("No significant difference (p >= 0.05)")

    return result.pvalue
```

---

## Summary

### Evaluation Checklist

```yaml
Complete Evaluation:

  Core Metrics:
    [ ] Perplexity on validation set
    [ ] Token-level loss
    [ ] Training/validation curves

  Knowledge:
    [ ] MMLU (overall + by subject)
    [ ] Domain-specific benchmarks (if applicable)

  Reasoning:
    [ ] HellaSwag (common sense)
    [ ] GSM8K (math)
    [ ] LogiQA (logic) - optional

  Code:
    [ ] HumanEval (if code model)
    [ ] MBPP (if code model) - optional

  Safety:
    [ ] TruthfulQA (factuality)
    [ ] ToxiGen (toxicity) - optional
    [ ] BBQ (bias) - optional

  Human Evaluation:
    [ ] Helpfulness
    [ ] Harmlessness
    [ ] Following instructions
    [ ] Conversation quality

  Reporting:
    [ ] Compare to baselines
    [ ] Include confidence intervals
    [ ] Document all details
    [ ] Share evaluation code
```

---

## Next Steps

- Phase 2 Complete! Next: **[Phase 3: Transformers](../../phase3-transformers/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
