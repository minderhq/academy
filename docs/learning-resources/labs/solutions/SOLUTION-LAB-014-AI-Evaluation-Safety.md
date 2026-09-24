# SOLUTION-LAB-014: AI Evaluation & Safety

## Overview
Complete solution for evaluating and making AI systems safe.

---

## Core Solution

```python
class SafetyEvaluator:
    """Evaluate AI responses for safety."""

    def __init__(self):
        self.safety_categories = [
            "violence",
            "hate_speech",
            "sexual_content",
            "self_harm",
            "illegal_activities"
        ]

    def evaluate(self, response: str) -> dict:
        """Evaluate response for safety issues."""
        results = {}

        for category in self.safety_categories:
            # Use classifier or keyword matching
            is_safe = self._check_category(response, category)
            results[category] = {
                "safe": is_safe,
                "confidence": 0.95
            }

        # Overall safety score
        safe_count = sum(1 for r in results.values() if r["safe"])
        results["overall_safe"] = safe_count == len(self.safety_categories)
        results["safety_score"] = safe_count / len(self.safety_categories)

        return results

class ToxicityDetector:
    """Detect toxic content."""

    def __init__(self):
        from transformers import pipeline
        self.classifier = pipeline("text-classification", model="unitary/toxic-bert")

    def is_toxic(self, text: str) -> bool:
        """Check if text is toxic."""
        result = self.classifier(text)
        return any(label["label"] == "toxic" and label["score"] > 0.5 for label in result)
```

---

## Complete Evaluation Pipeline

```python
class ModelEvaluator:
    """Comprehensive model evaluation."""

    def __init__(self):
        self.safety_evaluator = SafetyEvaluator()
        self.toxicity_detector = ToxicityDetector()

    def evaluate_response(self, response: str) -> dict:
        """Evaluate a single response."""
        return {
            "safety": self.safety_evaluator.evaluate(response),
            "toxicity": self.toxicity_detector.is_toxic(response),
            "quality": self._quality_score(response)
        }
```

---

**Last Updated:** 2026-02-04
**Difficulty:** ⭐⭐⭐⭐⭐
