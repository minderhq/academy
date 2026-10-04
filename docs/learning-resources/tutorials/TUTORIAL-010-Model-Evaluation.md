---
Document ID: TUTORIAL-010
Title: "TUTORIAL-010: Model Evaluation and Benchmarking"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: [PHASE-3]
Tags: ['tutorial', 'evaluation', 'benchmarks']
---

# TUTORIAL-010: Model Evaluation and Benchmarking

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: LLM Evaluation Metrics](#part-1-llm-evaluation-metrics)
- [Part 2: Benchmark Datasets](#part-2-benchmark-datasets)
- [Part 3: RAG Evaluation](#part-3-rag-evaluation)
- [Part 4: Evaluation Framework](#part-4-evaluation-framework)
- [Part 5: Tracking and Comparison](#part-5-tracking-and-comparison)
- [Exercises](#exercises)
- [Completion Checklist](#completion-checklist)
- [References](#references)
- [Next Steps](#next-steps)

---

## Abstract

This tutorial covers comprehensive model evaluation including metrics, benchmarks, and evaluation frameworks for LLMs.

**Duration:** 4 hours
**Difficulty:** ⭐⭐ Intermediate
**Prerequisites:** TUTORIAL-001 (Hello LLM), TUTORIAL-003 (RAG Basics)

---

## Learning Objectives

After this tutorial, you will:
- Understand key LLM evaluation metrics
- Implement custom evaluation pipelines
- Use benchmark datasets (MMLU, GSM8K, etc.)
- Evaluate RAG systems
- Track model performance over time

---

## Part 1: LLM Evaluation Metrics

### Installation

```bash
uv pip install torch transformers datasets nltk rouge sentence-transformers spacy pandas matplotlib
python -m spacy download en_core_web_sm
```

Part 1 needs transformers (Perplexity), nltk (BLEU), and rouge (ROUGE); Part 2 the
`datasets` library; Part 3 sentence-transformers and spaCy — the spaCy pipeline must
be downloaded once with the second command before `spacy.load("en_core_web_sm")`
will work; Part 5 pandas + matplotlib. numpy ships with the rest of the stack.

### Perplexity

```python
import torch
from torch.nn import CrossEntropyLoss
from transformers import AutoModelForCausalLM, AutoTokenizer


def calculate_perplexity(model, tokenizer, texts: list[str]) -> float:
    """
    Calculate perplexity - measures how well model predicts text

    Lower is better. GPT-4 achieves ~3 on diverse text.
    """
    model.eval()
    loss_fn = CrossEntropyLoss(reduction='mean')

    total_loss = 0
    total_tokens = 0

    with torch.no_grad():
        for text in texts:
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt")
            input_ids = inputs["input_ids"].to(model.device)

            # Forward pass - no labels argument: the loss is computed
            # manually below, so the token averaging stays explicit
            # (passing labels would make the model compute a second,
            # silently discarded loss)
            outputs = model(input_ids)
            logits = outputs.logits

            # Calculate loss
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()

            loss = loss_fn(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1)
            )

            total_loss += loss.item() * shift_labels.numel()
            total_tokens += shift_labels.numel()

    # Perplexity = exp(loss)
    avg_loss = total_loss / total_tokens
    perplexity = torch.exp(torch.tensor(avg_loss))

    return perplexity.item()

# Usage
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

texts = [
    "The capital of France is Paris.",
    "Machine learning is a subset of artificial intelligence.",
    "Python is a popular programming language."
]

perplexity = calculate_perplexity(model, tokenizer, texts)
print(f"Perplexity: {perplexity:.2f}")

# Expected Output:
# Perplexity: <N>.NN
# (lower is better; the exact value comes from the gpt2 checkpoint
#  loaded above run over these three sentences)
```

### BLEU Score

```python
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction


def calculate_bleu(
    predictions: list[str],
    references: list[list[str]]
) -> float:
    """
    BLEU score for translation/text generation

    Measures n-gram overlap between prediction and reference.
    Range: 0-1, higher is better.
    """
    smoothie = SmoothingFunction().method1
    scores = []

    for pred, refs in zip(predictions, references):
        # Tokenize
        pred_tokens = pred.split()
        ref_tokens = [r.split() for r in refs]

        # Calculate BLEU
        score = sentence_bleu(
            ref_tokens,
            pred_tokens,
            smoothing_function=smoothie,
            weights=(0.25, 0.25, 0.25, 0.25)  # BLEU-4
        )
        scores.append(score)

    return sum(scores) / len(scores)

# Usage
predictions = [
    "The cat sat on the mat.",
    "Machine learning transforms data into insights."
]
references = [
    ["A cat is sitting on the mat.", "The cat is on the mat."],
    ["ML turns data into insights.", "Machine learning extracts insights from data."]
]

bleu = calculate_bleu(predictions, references)
print(f"BLEU Score: {bleu:.4f}")

# Expected Output:
# BLEU Score: <N>.NNNN
# (predictions and references overlap only partially, so even correct
#  paraphrases score well below 1.0; NLTK's method1 smoothing keeps
#  the near-zero 4-gram precision of short sentences from collapsing
#  the whole score to 0)
```

### ROUGE Score

```python
from rouge import Rouge


def calculate_rouge(
    predictions: list[str],
    references: list[str]
) -> dict[str, float]:
    """
    ROUGE score for summarization

    Measures overlap of n-grams between prediction and reference.
    ROUGE-L: Longest common subsequence
    """
    rouge = Rouge()

    scores = rouge.get_scores(predictions, references, avg=True)

    return {
        "rouge-1": scores["rouge-1"]["f"],
        "rouge-2": scores["rouge-2"]["f"],
        "rouge-l": scores["rouge-l"]["f"]
    }

# Usage
predictions = [
    "AI is transforming healthcare through diagnostic assistance.",
    "Climate change requires global cooperation to address."
]
references = [
    "Artificial intelligence is helping doctors diagnose diseases more accurately.",
    "Global action is needed to combat climate change effectively."
]

rouge_scores = calculate_rouge(predictions, references)
print(f"ROUGE-1: {rouge_scores['rouge-1']:.4f}")
print(f"ROUGE-2: {rouge_scores['rouge-2']:.4f}")
print(f"ROUGE-L: {rouge_scores['rouge-l']:.4f}")

# Expected Output:
# ROUGE-1: <N>.NNNN
# ROUGE-2: <N>.NNNN
# ROUGE-L: <N>.NNNN
# (average F-measures over the two sentence pairs - partial overlaps,
#  so each value is a fraction rather than a near-1.0 match)
```

---

## Part 2: Benchmark Datasets

### MMLU (Massive Multitask Language Understanding)

```python
import re

def load_mmlu(subject: str = "abstract_algebra") -> list[dict]:
    """
    Load MMLU benchmark dataset

    Covers 57 subjects including STEM, humanities, etc.
    """
    # Download from Hugging Face
    from datasets import load_dataset

    dataset = load_dataset("cais/mmlu", "all", split="test")

    # Filter by subject
    subject_data = [
        {
            "question": item["question"],
            "choices": item["choices"],
            "answer": item["answer"]
        }
        for item in dataset
        if item["subject"] == subject
    ]

    return subject_data

def evaluate_mmlu(model, tokenizer, subject: str = "abstract_algebra") -> dict:
    """Evaluate model on MMLU benchmark"""
    data = load_mmlu(subject)

    correct = 0
    total = len(data)

    for item in data:
        question = item["question"]
        choices = item["choices"]
        correct_answer = item["answer"]

        # Format as multiple choice
        prompt = f"{question}\n"
        for i, choice in enumerate(choices):
            prompt += f"{chr(65+i)}. {choice}\n"

        # Get model response - generate() returns the full
        # prompt+continuation sequence, so decode only the newly
        # generated token; taking the last character of the whole
        # decode works only while the continuation happens to end in
        # a letter - a whitespace/newline token would let strip()
        # trim back into the prompt and silently read a letter from
        # the last choice instead
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=1)
        prompt_len = inputs["input_ids"].shape[-1]
        continuation = tokenizer.decode(
            outputs[0][prompt_len:], skip_special_tokens=True
        ).strip()

        # Extract answer (A, B, C, D) - the first A-D letter in the
        # continuation; anything else counts as wrong rather than
        # silently mapping an arbitrary character onto a choice index
        match = re.search(r"[A-D]", continuation.upper())
        predicted_answer = ord(match.group(0)) - ord("A") if match else -1

        if predicted_answer == correct_answer:
            correct += 1

    accuracy = correct / total

    return {
        "subject": subject,
        "accuracy": accuracy,
        "correct": correct,
        "total": total
    }
```

### GSM8K (Grade School Math)

```python
def load_gsm8k() -> list[dict]:
    """Load GSM8K math word problems"""
    from datasets import load_dataset

    dataset = load_dataset("gsm8k", "main", split="test")

    return [
        {
            "question": item["question"],
            "answer": item["answer"]
        }
        for item in dataset
    ]

# re is imported in Part 2's MMLU block above (this tutorial's blocks
# run top-down)
def extract_final_number(text: str):
    """Last number appearing anywhere in the text, or None.

    GSM8K reference answers end with '#### <number>' and a
    chain-of-thought response typically ends with its final number
    too, so the last number is the one worth comparing.
    """
    numbers = re.findall(r"-?\d+\.?\d*", text.replace(",", ""))
    return float(numbers[-1]) if numbers else None

def evaluate_gsm8k(model, tokenizer) -> dict:
    """Evaluate model on grade school math"""
    data = load_gsm8k()

    correct = 0
    total = len(data)

    for item in data:
        question = item["question"]
        answer = item["answer"]

        # Get model response
        prompt = f"Q: {question}\nA: Let's think step by step.\n"
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # Greedy decoding (the default) - deterministic, which is what
        # an eval run wants; temperature=0.0 without do_sample=True
        # only triggers a transformers warning and is ignored
        outputs = model.generate(**inputs, max_new_tokens=256)

        # Decode only the continuation - the full sequence would end
        # with the response, but a number-free response would make the
        # parser fall back to the last number inside the question
        prompt_len = inputs["input_ids"].shape[-1]
        response = tokenizer.decode(
            outputs[0][prompt_len:], skip_special_tokens=True
        )

        # Extract final answer (numeric) - a None never equals a
        # number, so unparseable responses simply count as wrong
        predicted_number = extract_final_number(response)
        correct_number = extract_final_number(answer)

        if predicted_number == correct_number:
            correct += 1

    return {
        "accuracy": correct / total,
        "correct": correct,
        "total": total
    }
```

---

## Part 3: RAG Evaluation

### Retrieval Metrics

```python
import numpy as np


class RetrievalEvaluator:
    """Evaluate retrieval quality"""

    def precision_at_k(
        self,
        retrieved: list[int],
        relevant: set[int],
        k: int
    ) -> float:
        """Precision@K: % of retrieved that are relevant"""
        retrieved_k = retrieved[:k]
        relevant_retrieved = len(set(retrieved_k) & relevant)
        return relevant_retrieved / k

    def recall_at_k(
        self,
        retrieved: list[int],
        relevant: set[int],
        k: int
    ) -> float:
        """Recall@K: % of relevant that are retrieved"""
        retrieved_k = retrieved[:k]
        relevant_retrieved = len(set(retrieved_k) & relevant)
        return relevant_retrieved / len(relevant) if relevant else 0

    def mrr(self, retrieved: list[int], relevant: set[int]) -> float:
        """Mean Reciprocal Rank"""
        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant:
                return 1 / (i + 1)
        return 0

    def ndcg_at_k(
        self,
        retrieved: list[int],
        relevant: set[int],
        k: int
    ) -> float:
        """Normalized Discounted Cumulative Gain"""
        dcg = 0
        for i, doc_id in enumerate(retrieved[:k]):
            if doc_id in relevant:
                dcg += 1 / np.log2(i + 2)

        # Ideal DCG
        idcg = sum(1 / np.log2(i + 2) for i in range(min(k, len(relevant))))

        return dcg / idcg if idcg > 0 else 0

# Usage
evaluator = RetrievalEvaluator()

retrieved_docs = [1, 5, 3, 8, 2]
relevant_docs = {2, 3, 7, 9}

print(f"Precision@5: {evaluator.precision_at_k(retrieved_docs, relevant_docs, 5):.3f}")
print(f"Recall@5: {evaluator.recall_at_k(retrieved_docs, relevant_docs, 5):.3f}")
print(f"MRR: {evaluator.mrr(retrieved_docs, relevant_docs):.3f}")
print(f"NDCG@5: {evaluator.ndcg_at_k(retrieved_docs, relevant_docs, 5):.3f}")

# Expected Output:
# Precision@5: 0.400
# Recall@5: 0.500
# MRR: 0.333
# NDCG@5: 0.346
# (docs 2 and 3 are the relevant hits among the five retrieved: 2/5
#  precision, 2/4 recall, first hit at rank 3 -> 1/3 MRR, and
#  NDCG = (1/log2(4) + 1/log2(6)) / (1/log2(2)+1/log2(3)+1/log2(4)+1/log2(5)))
```

### RAG Quality Metrics

```python
from sentence_transformers import SentenceTransformer

class RAGEvaluator:
    """Evaluate end-to-end RAG quality"""

    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def faithfulness(self, response: str, context: str) -> float:
        """
        Measure if response is grounded in context

        Uses embedding similarity between response and context
        """
        resp_emb = self.embedder.encode(response)
        ctx_emb = self.embedder.encode(context)

        similarity = np.dot(resp_emb, ctx_emb) / (
            np.linalg.norm(resp_emb) * np.linalg.norm(ctx_emb)
        )

        return similarity

    def answer_relevance(self, query: str, response: str) -> float:
        """Measure if response addresses the query"""
        query_emb = self.embedder.encode(query)
        resp_emb = self.embedder.encode(response)

        similarity = np.dot(query_emb, resp_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(resp_emb)
        )

        return similarity

    def context_utilization(self, response: str, contexts: list[str]) -> float:
        """
        Measure how much of retrieved context is used

        Checks for mention of key entities from context
        """
        import spacy
        nlp = spacy.load("en_core_web_sm")

        # Extract entities from contexts
        context_entities = set()
        for ctx in contexts:
            doc = nlp(ctx)
            context_entities.update([ent.text for ent in doc.ents])

        # Check which entities appear in response
        response_doc = nlp(response)
        response_entities = [ent.text for ent in response_doc.ents]

        used = len(set(response_entities) & context_entities)
        total = len(context_entities) if context_entities else 1

        return used / total
```

---

## Part 4: Evaluation Framework

### Comprehensive Evaluator

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any
import json

@dataclass
class EvaluationResult:
    """Container for evaluation results"""
    metrics: dict[str, float]
    metadata: dict[str, Any]
    timestamp: str

class ModelEvaluator:
    """Comprehensive model evaluation framework"""

    def __init__(self, model, tokenizer, name: str = "model"):
        self.model = model
        self.tokenizer = tokenizer
        self.name = name
        self.results = []

    def evaluate(
        self,
        dataset: str,
        split: str = "test",
        save_results: bool = True
    ) -> EvaluationResult:
        """Run evaluation on specified dataset"""

        if dataset == "mmlu":
            result = self._evaluate_mmlu()
        elif dataset == "gsm8k":
            result = self._evaluate_gsm8k()
        elif dataset == "rag":
            result = self._evaluate_rag()
        else:
            raise ValueError(f"Unknown dataset: {dataset}")

        result_obj = EvaluationResult(
            metrics=result,
            metadata={
                "model": self.name,
                "dataset": dataset,
                "split": split
            },
            timestamp=datetime.now().isoformat()
        )

        self.results.append(result_obj)

        if save_results:
            self._save_results(result_obj)

        return result_obj

    def _evaluate_mmlu(self) -> dict[str, float]:
        """Run MMLU evaluation"""
        subjects = ["abstract_algebra", "computer_networks", "formal_logic"]

        results = {}
        for subject in subjects:
            result = evaluate_mmlu(self.model, self.tokenizer, subject)
            results[f"{subject}_accuracy"] = result["accuracy"]

        results["average_accuracy"] = sum(results.values()) / len(results)
        return results

    def _evaluate_gsm8k(self) -> dict[str, float]:
        """Run GSM8K evaluation - delegates to Part 2's function"""
        return evaluate_gsm8k(self.model, self.tokenizer)

    def _evaluate_rag(self) -> dict[str, float]:
        """RAG evaluation needs a labeled QA corpus (queries, gold
        answers, retrieved contexts) that this class does not hold -
        assemble one and score it with Part 3's RAGEvaluator, or see
        the Exercises. Fail loudly rather than pretend."""
        raise NotImplementedError(
            "rag evaluation needs a labeled QA corpus; see Part 3 and the Exercises"
        )

    def _save_results(self, result: EvaluationResult):
        """Save results to file"""
        filename = f"eval_{self.name}_{result.timestamp.replace(':', '-')}.json"
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump({
                "metrics": result.metrics,
                "metadata": result.metadata,
                "timestamp": result.timestamp
            }, f, indent=2)
```

---

## Part 5: Tracking and Comparison

### Performance Tracking

```python
import pandas as pd

class EvaluationTracker:
    """Track model performance over time"""

    def __init__(self):
        self.history = []

    def add_result(self, result: EvaluationResult):
        """Add evaluation result"""
        self.history.append(result)

    def get_dataframe(self) -> pd.DataFrame:
        """Convert history to pandas DataFrame"""
        data = []
        for result in self.history:
            row = {
                "timestamp": result.timestamp,
                **result.metadata,
                **result.metrics
            }
            data.append(row)

        return pd.DataFrame(data)

    def compare_models(self, metric: str = "accuracy") -> pd.DataFrame:
        """Compare models on specific metric"""
        df = self.get_dataframe()

        # Filter for metric
        metric_cols = [col for col in df.columns if metric in col]

        return df[["model", "timestamp"] + metric_cols]

    def plot_progression(self, model: str, metric: str):
        """Plot metric progression over time"""
        import matplotlib.pyplot as plt

        df = self.get_dataframe()
        model_df = df[df["model"] == model]

        metric_cols = [col for col in df.columns if metric in col]

        plt.figure(figsize=(10, 6))
        for col in metric_cols:
            plt.plot(model_df["timestamp"], model_df[col], label=col, marker='o')

        plt.xlabel("Timestamp")
        plt.ylabel(metric)
        plt.title(f"{model} - {metric} Over Time")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{model}_{metric}_progression.png")
```

---

## Exercises

1. **Implement custom metrics** for your use case
2. **Evaluate model** on MMLU subset
3. **Build RAG evaluator** with faithfulness metrics
4. **Track performance** over multiple model versions
5. **Compare models** side-by-side

---

## Completion Checklist

- [ ] Perplexity calculated
- [ ] BLEU/ROUGE implemented
- [ ] Benchmark dataset loaded
- [ ] RAG evaluation working
- [ ] Tracking system built

---

## References

### Related PROJECT-OMEGA Documents

- [LAB-014: AI Evaluation Safety](../labs/LAB-014-AI-Evaluation-Safety.md)
- [LAB-006: Train Model From Scratch](../labs/LAB-006-Train-Model-From-Scratch.md)
- [TUTORIAL-004: Monitoring](TUTORIAL-004-Monitoring.md)

---

## Next Steps

- Hands-on: **[LAB-014: AI Evaluation Safety](../labs/LAB-014-AI-Evaluation-Safety.md)**
- Practice: **[LAB-006: Train Model From Scratch](../labs/LAB-006-Train-Model-From-Scratch.md)**
