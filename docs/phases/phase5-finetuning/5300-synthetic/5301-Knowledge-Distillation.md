---
Document ID: 5301
Title: Knowledge Distillation - Training Small Models Using Big Model Outputs
Phase: 5
Module: 5300
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'synthetic-data', 'distillation', 'federated']
---

# 5301: Knowledge Distillation - Training Small Models Using Big Model Outputs

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Distillation Concepts](#distillation-concepts)
- [Distillation Loss](#distillation-loss)
- [Advanced Distillation Techniques](#advanced-distillation-techniques)
- [Data Generation for Distillation](#data-generation-for-distillation)
- [Evaluating Distillation](#evaluating-distillation)
- [Practical Tips](#practical-tips)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain the reasoning behind Distillation Concepts
- Explain Distillation Loss
- Explain Advanced Distillation Techniques
- Explain Data Generation for Distillation
- Measure and evaluate Evaluating Distillation
- Explain Practical Tips

---

## Abstract
Knowledge distillation transfers knowledge from a large "teacher" model to a smaller "student" model. This enables training efficient models that retain much of the teacher's performance.

## Distillation Concepts

### Hard vs Soft Labels
```text
Hard Labels (Standard training):
  - One-hot encoded: [0, 0, 1, 0, 0]
  - Only correct class has probability
  - Loss: Cross-entropy with hard label

Soft Labels (Distillation):
  - Probability distribution: [0.01, 0.05, 0.85, 0.07, 0.02]
  - All classes have probabilities
  - Contains dark knowledge: relationships between classes

Example: "Cat" vs "Dog" classification
  Hard label: [0, 1] for [cat, dog]
  Soft label: [0.3, 0.7] - shows similarity!
  - Dog is somewhat like cat (both animals)
  - This similarity is "dark knowledge"
```

### Temperature Scaling
```text
Softmax with temperature T:

softmax_T(x_i) = exp(x_i / T) / Σ exp(x_j / T)

High temperature (T > 1):
  - Softens the distribution
  - Reveals relationships between classes

T = 1: [0.01, 0.05, 0.85, 0.07, 0.02]
T = 5: [0.15, 0.18, 0.30, 0.19, 0.18]  ← Reveals structure
T → ∞: Uniform [0.2, 0.2, 0.2, 0.2, 0.2]  ← No information
```

## Distillation Loss

### Combined Loss Function
```python
import torch
import torch.nn as nn
import torch.nn.functional as F

def distillation_loss(
    student_logits,
    teacher_logits,
    labels,
    temperature=5.0,
    alpha=0.5
):
    """
    Distillation loss = α × distillation_loss + (1-α) × student_loss

    Args:
        student_logits: Raw outputs from student model
        teacher_logits: Raw outputs from teacher model (no grad)
        labels: Ground truth labels
        temperature: Softmax temperature
        alpha: Weight between distillation and hard label loss
    """
    # 1. Distillation loss (soft targets)
    # High temperature softens distributions
    soft_student = F.log_softmax(student_logits / temperature, dim=-1)
    soft_teacher = F.softmax(teacher_logits / temperature, dim=-1)

    distillation_loss = F.kl_div(
        soft_student,
        soft_teacher,
        reduction="batchmean"
    ) * (temperature ** 2)  # Scale by T²

    # 2. Student loss (hard labels)
    student_loss = F.cross_entropy(student_logits, labels)

    # 3. Combined
    loss = alpha * distillation_loss + (1 - alpha) * student_loss

    return loss
```

### Training Loop
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. Load models
teacher_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-70b-hf")
student_model = AutoModelForCausalLM.from_pretrained("tinyllama-1b")

teacher_model.eval()  # Teacher is frozen
student_model.train()

# 2. Optimizer
optimizer = torch.optim.AdamW(student_model.parameters(), lr=1e-4)

# 3. Training
temperature = 5.0
alpha = 0.5  # Balance soft/hard targets

for batch in dataloader:
    input_ids = batch["input_ids"]
    labels = batch["labels"]

    # Teacher forward (no grad)
    with torch.no_grad():
        teacher_outputs = teacher_model(input_ids=input_ids)
        teacher_logits = teacher_outputs.logits

    # Student forward
    student_outputs = student_model(input_ids=input_ids)
    student_logits = student_outputs.logits

    # Distillation loss
    loss = distillation_loss(
        student_logits,
        teacher_logits,
        labels,
        temperature=temperature,
        alpha=alpha
    )

    # Optimize
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
```

## Advanced Distillation Techniques

### Feature-level Distillation
```python
class FeatureDistillation(nn.Module):
    """
    Distill intermediate representations, not just logits
    """
    def __init__(self, student, teacher):
        super().__init__()
        self.student = student
        self.teacher = teacher

    def forward(self, x, labels):
        # Get features from intermediate layers
        with torch.no_grad():
            teacher_features = self.teacher.get_features(x)

        student_features = self.student.get_features(x)

        # Feature-level loss (MSE between features)
        feature_loss = F.mse_loss(
            student_features["hidden_states"],
            teacher_features["hidden_states"]
        )

        # Logit-level loss
        logit_loss = F.mse_loss(
            self.student(x),
            self.teacher(x)
        )

        # Combined
        loss = feature_loss + logit_loss
        return loss
```

### Multi-Teacher Distillation
```python
def multi_teacher_distillation(student_logits, teacher_logits_list, weights):
    """
    Combine multiple teachers with weighted averaging

    Args:
        student_logits: Student outputs
        teacher_logits_list: List of teacher outputs
        weights: Weight for each teacher (sum to 1)
    """
    # Soft targets from each teacher
    soft_targets = []
    for teacher_logits, weight in zip(teacher_logits_list, weights):
        soft = F.softmax(teacher_logits / temperature, dim=-1)
        soft_targets.append(soft * weight)

    # Average soft targets
    averaged_soft = sum(soft_targets)

    # Distillation loss
    soft_student = F.log_softmax(student_logits / temperature, dim=-1)
    loss = F.kl_div(soft_student, averaged_soft, reduction="batchmean")

    return loss

# Example: Ensemble of Llama-2-70B, GPT-4, Claude
teachers = [
    llama_70b_model,
    # Could use API calls for other teachers
]
weights = [0.5, 0.3, 0.2]  # Weighted ensemble
```

### Self-Distillation
```python
class SelfDistillation(nn.Module):
    """
    Student learns from its own predictions (from previous epoch)
    """
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.teacher_state = None

    def update_teacher(self):
        """Update teacher with current student state"""
        self.teacher_state = {
            k: v.detach().clone()
            for k, v in self.model.state_dict().items()
        }

    def forward(self, x, labels):
        # Student forward
        student_logits = self.model(x)

        # Teacher forward (using cached state)
        if self.teacher_state is not None:
            teacher_model = self.model.__class__(self.model.config)
            teacher_model.load_state_dict(self.teacher_state)
            teacher_model.eval()

            with torch.no_grad():
                teacher_logits = teacher_model(x)

            # Distillation loss
            loss = distillation_loss(
                student_logits,
                teacher_logits,
                labels,
                temperature=2.0,
                alpha=0.7
            )
        else:
            # First epoch: standard training
            loss = F.cross_entropy(student_logits, labels)

        return loss
```

## Data Generation for Distillation

### Using GPT-4 as Teacher
```python
import openai

def generate_teacher_data(prompt, model="gpt-4"):
    """
    Generate training data using GPT-4 as teacher
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,  # Sample diverse outputs
    )

    return response.choices[0].message.content

def create_distillation_dataset(base_prompts, num_samples_per_prompt=5):
    """
    Create dataset by sampling from teacher
    """
    dataset = []

    for prompt in base_prompts:
        for _ in range(num_samples_per_prompt):
            teacher_output = generate_teacher_data(prompt)
            dataset.append({
                "prompt": prompt,
                "completion": teacher_output,
            })

    return dataset

# Use to train smaller model
dataset = create_distillation_dataset(my_prompts)
# Train student model on this dataset
```

### Synthetic Question-Answer Pairs
```python
def generate_qa_pairs(context, num_pairs=10):
    """
    Generate QA pairs from context using teacher model
    """
    prompt = f"""
    Given the following context, generate {num_pairs} question-answer pairs:

    Context: {context}

    Generate diverse questions that test understanding of the context.
    Format each as Q: [question] A: [answer]
    """

    response = generate_teacher_data(prompt, model="gpt-4")
    return parse_qa_pairs(response)

# Example
context = """
    Photosynthesis is the process by which plants convert sunlight,
    water, and carbon dioxide into glucose and oxygen. This occurs
    primarily in the leaves, within chloroplasts containing chlorophyll.
"""

qa_pairs = generate_qa_pairs(context)
# Output: Multiple QA pairs testing different aspects
```

## Evaluating Distillation

### Teacher-Student Performance Gap
```python
def evaluate_distillation(teacher, student, test_loader):
    """
    Compare teacher and student performance
    """
    teacher_results = []
    student_results = []

    teacher.eval()
    student.eval()

    with torch.no_grad():
        for batch in test_loader:
            inputs = batch["input_ids"]

            # Teacher predictions
            teacher_logits = teacher(inputs)
            teacher_preds = teacher_logits.argmax(dim=-1)
            teacher_results.append(teacher_preds)

            # Student predictions
            student_logits = student(inputs)
            student_preds = student_logits.argmax(dim=-1)
            student_results.append(student_preds)

    # Compute metrics
    teacher_acc = compute_accuracy(teacher_results)
    student_acc = compute_accuracy(student_results)

    # Agreement rate
    agreement = (torch.cat(teacher_results) == torch.cat(student_results)).float().mean()

    return {
        "teacher_accuracy": teacher_acc,
        "student_accuracy": student_acc,
        "performance_gap": teacher_acc - student_acc,
        "agreement_rate": agreement,
    }
```

### Distillation Quality Metrics
```python
def kl_divergence(student_dist, teacher_dist):
    """
    KL divergence between student and teacher distributions
    Lower is better
    """
    return F.kl_div(
        student_dist.log(),
        teacher_dist,
        reduction="batchmean"
    )

def cosine_similarity(student_repr, teacher_repr):
    """
    Similarity of internal representations
    """
    return F.cosine_similarity(
        student_repr.flatten(),
        teacher_repr.flatten(),
        dim=0
    )

# Comprehensive evaluation
metrics = {
    "accuracy_gap": teacher_acc - student_acc,
    "kl_divergence": kl_divergence(student_probs, teacher_probs),
    "representation_similarity": cosine_similarity(
        student_hidden_states,
        teacher_hidden_states
    ),
}
```

## Practical Tips

### Temperature Selection
```text
Temperature effects:
  T = 1: Minimal softening (close to hard labels)
  T = 3-5: Moderate softening (recommended)
  T = 10+: Heavy softening (noisy gradients)

Rule of thumb: Start with T = 3-5
  - Too low: Mostly learning hard labels
  - Too high: Gradients become noisy
```

### Alpha (Loss Weight)
```text
Alpha effects:
  α = 0: Only hard labels (no distillation)
  α = 0.3: Mostly hard labels, some distillation
  α = 0.5: Balanced
  α = 0.7: Mostly distillation, some hard labels
  α = 1.0: Only distillation (may diverge)

Rule of thumb: α = 0.5 (balanced)
  - Early training: Lower α (0.3)
  - Late training: Higher α (0.7)
```


---

## References

### Related ai-engineering-curriculum Documents

- [5302: Distributed Training Orchestration](5302-Distributed-Training.md)
- [5303: Federated Learning](5303-Federated-Learning.md)

---

## Next Steps

- Continue with: **[5401-Data-Parallelism.md](./../5400-distributed-training/5401-Data-Parallelism.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [5101: LoRA Logic](../5100-PEFT/5101-LoRA-Logic.md)
- [6202: RAG Retrieval](../../phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md)
- [7101: ReAct Loop](../../phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)

**Experiment Template:** `experiments/EXP_5301_DISTILLATION.md"
