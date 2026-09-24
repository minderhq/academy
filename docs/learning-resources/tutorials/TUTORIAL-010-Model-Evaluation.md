# TUTORIAL-010: Model Evaluation and Benchmarking

## Overview

This tutorial covers comprehensive model evaluation including metrics, benchmarks, and evaluation frameworks for LLMs.

**Duration:** 4 hours
**Difficulty:** Intermediate
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

### Perplexity

```python
import torch
from torch.nn import CrossEntropyLoss
from typing import List

def calculate_perplexity(model, tokenizer, texts: List[str]) -> float:
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

            # Forward pass
            outputs = model(input_ids, labels=input_ids)
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
```

### BLEU Score

```python
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from typing import List

def calculate_bleu(
    predictions: List[str],
    references: List[List[str]]
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
```

### ROUGE Score

```python
from rouge import Rouge
from typing import List, Dict

def calculate_rouge(
    predictions: List[str],
    references: List[str]
) -> Dict[str, float]:
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
}

rouge_scores = calculate_rouge(predictions, references)
print(f"ROUGE-1: {rouge_scores['rouge-1']:.4f}")
print(f"ROUGE-2: {rouge_scores['rouge-2']:.4f}")
print(f"ROUGE-L: {rouge_scores['rouge-l']:.4f}")
```

---

## Part 2: Benchmark Datasets

### MMLU (Massive Multitask Language Understanding)

```python
import requests
import json
from typing import List, Dict

def load_mmlu(subject: str = "abstract_algebra") -> List[Dict]:
    """
    Load MMLU benchmark dataset

    Covers 57 subjects including STEM, humanities, etc.
    """
    # Download from HuggingFace
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

def evaluate_mmlu(model, tokenizer, subject: str = "abstract_algebra") -> Dict:
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

        # Get model response
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=1)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract answer (A, B, C, D)
        predicted_letter = response.strip()[-1].upper()
        predicted_answer = ord(predicted_letter) - ord('A')

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
def load_gsm8k() -> List[Dict]:
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

def evaluate_gsm8k(model, tokenizer) -> Dict:
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

        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.0
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract final answer (numeric)
        # In practice, use more sophisticated parsing
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
from typing import List, Set

class RetrievalEvaluator:
    """Evaluate retrieval quality"""

    def precision_at_k(
        self,
        retrieved: List[int],
        relevant: Set[int],
        k: int
    ) -> float:
        """Precision@K: % of retrieved that are relevant"""
        retrieved_k = retrieved[:k]
        relevant_retrieved = len(set(retrieved_k) & relevant)
        return relevant_retrieved / k

    def recall_at_k(
        self,
        retrieved: List[int],
        relevant: Set[int],
        k: int
    ) -> float:
        """Recall@K: % of relevant that are retrieved"""
        retrieved_k = retrieved[:k]
        relevant_retrieved = len(set(retrieved_k) & relevant)
        return relevant_retrieved / len(relevant) if relevant else 0

    def mrr(self, retrieved: List[int], relevant: Set[int]) -> float:
        """Mean Reciprocal Rank"""
        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant:
                return 1 / (i + 1)
        return 0

    def ndcg_at_k(
        self,
        retrieved: List[int],
        relevant: Set[int],
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

    def context_utilization(self, response: str, contexts: List[str]) -> float:
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
from typing import Any, Dict
import json

@dataclass
class EvaluationResult:
    """Container for evaluation results"""
    metrics: Dict[str, float]
    metadata: Dict[str, Any]
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

    def _evaluate_mmlu(self) -> Dict[str, float]:
        """Run MMLU evaluation"""
        subjects = ["abstract_algebra", "computer_networks", "formal_logic"]

        results = {}
        for subject in subjects:
            result = evaluate_mmlu(self.model, self.tokenizer, subject)
            results[f"{subject}_accuracy"] = result["accuracy"]

        results["average_accuracy"] = sum(results.values()) / len(results)
        return results

    def _save_results(self, result: EvaluationResult):
        """Save results to file"""
        filename = f"eval_{self.name}_{result.timestamp.replace(':', '-')}.json"
        with open(filename, 'w') as f:
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
from typing import List

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

**Next Steps:** LAB-014: AI Evaluation Safety or LAB-006: Train Model From Scratch

**Last Updated:** 2026-02-05
