---
Document ID: 5301
Title: "5301: Knowledge Distillation - Training Small Models Using Big Model Outputs"
Phase: 5
Module: 5300
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'synthetic-data', 'distillation', 'federated-learning']
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
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Trace the soft-target pipeline — hard one-hot labels vs the teacher's full softmax, the dark knowledge it carries (inter-class similarity like "dog resembles cat"), and temperature's sweep (T=1 nearly hard, T→∞ uniform)
- Implement the combined loss — flatten (B,T,V) logits to (N,V) for both terms, KL(soft student ‖ soft teacher)·T² over non-padding positions, plus (1−α)·CE with ignore_index=-100
- Distinguish the advanced variants — feature-level (MSE on output_hidden_states layers, projection when depths differ), multi-teacher (weighted soft-target mixture — only from local logit-exposing teachers), self-distillation (a frozen EMA copy, not a per-forward rebuild)
- Generate distillation data from an API teacher — the modern `OpenAI()` client with `chat.completions.create`, n samples per prompt, and a Q:/A: parser for synthetic QA sets
- Evaluate the transfer — masked next-token accuracy (shifted logits vs labels) and the teacher−student gap, agreement rate between the two argmax streams, KL between output distributions
- Pick T and α from the failure modes — T=1 collapses to hard labels, T=10+ makes gradients noisy; α≈0.5 balanced, lower early (hard labels first), higher late

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
import torch.nn.functional as F

def distillation_loss(
    student_logits,
    teacher_logits,
    labels,
    temperature=5.0,
    alpha=0.5
):
    """
    Distillation loss = α × soft-target KL + (1-α) × hard-label CE

    Args:
        student_logits: (B, T, V) raw outputs from the student
        teacher_logits: (B, T, V) raw teacher outputs (computed under no_grad)
        labels: (B, T) target token ids, padding positions marked -100
        temperature: Softmax temperature (see Temperature Scaling above)
        alpha: Weight between distillation and hard label loss
    """
    # Flatten to (N, V): cross_entropy and batchmean KL both expect 2-D —
    # on a 4-D (B, T, V) input cross_entropy treats dim 1 (the SEQUENCE
    # axis) as the class axis and raises "Expected target size"
    V = student_logits.size(-1)
    flat_student = student_logits.reshape(-1, V)
    flat_teacher = teacher_logits.reshape(-1, V)
    flat_labels = labels.reshape(-1)

    # 1. Distillation loss (soft targets)
    # High temperature softens distributions; padding positions (-100)
    # must not vote
    keep = flat_labels != -100
    soft_student = F.log_softmax(flat_student[keep] / temperature, dim=-1)
    soft_teacher = F.softmax(flat_teacher[keep] / temperature, dim=-1)

    distill_loss = F.kl_div(
        soft_student,
        soft_teacher,
        reduction="batchmean"
    ) * (temperature ** 2)  # T² keeps gradient scale comparable as T moves

    # 2. Student loss (hard labels)
    student_loss = F.cross_entropy(flat_student, flat_labels, ignore_index=-100)

    # 3. Combined
    loss = alpha * distill_loss + (1 - alpha) * student_loss

    return loss
```

### Training Loop
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. Load models — a vocab-compatible pair so the KL over logits is
# meaningful (the whole Qwen2.5 family shares one 151936-token
# tokenizer). Ungated demo pair; production recipes distill big →
# tiny (e.g. 70B → 1.1B) the exact same way
teacher_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B")
student_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B")

teacher_model.eval()  # Teacher is frozen
student_model.train()

# 2. Optimizer
optimizer = torch.optim.AdamW(student_model.parameters(), lr=1e-4)

# 3. Training
temperature = 5.0
alpha = 0.5  # Balance soft/hard targets

for batch in dataloader:
    input_ids = batch["input_ids"]
    labels = batch["labels"]  # -100 on padding — distillation_loss masks it

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
import torch.nn as nn

class FeatureDistillation(nn.Module):
    """
    Distill intermediate representations, not just logits
    """
    def __init__(self, student, teacher):
        super().__init__()
        self.student = student
        self.teacher = teacher
        self.teacher.eval()  # the teacher never trains

    def forward(self, x):
        # Hidden states come from the model OUTPUT, not a get_features()
        # method: pass output_hidden_states=True and index the layer
        with torch.no_grad():
            teacher_out = self.teacher(x, output_hidden_states=True)
        student_out = self.student(x, output_hidden_states=True)

        # Feature loss: MSE on the last hidden layer. Different depths or
        # hidden sizes need a linear projection first — raw MSE raises a
        # shape error instead of "aligning" anything
        feature_loss = F.mse_loss(
            student_out.hidden_states[-1],
            teacher_out.hidden_states[-1],
        )

        # Logit-level loss on the same pass (teacher is under no_grad)
        logit_loss = F.kl_div(
            F.log_softmax(student_out.logits, dim=-1),
            F.softmax(teacher_out.logits, dim=-1),
            reduction="batchmean",
        )

        # Combined
        loss = feature_loss + logit_loss
        return loss
```

### Multi-Teacher Distillation
```python
def multi_teacher_distillation(student_logits, teacher_logits_list, weights,
                               temperature=5.0):
    """
    Combine multiple teachers into ONE soft target (weighted average of
    their distributions), then measure the student against it.

    Args:
        student_logits: Student outputs
        teacher_logits_list: The teacher outputs (same vocab!)
        weights: One weight per teacher, summing to 1 — its length MUST
            match teacher_logits_list
        temperature: Softmax temperature shared across teachers
    """
    # Soft targets from each teacher
    soft_targets = []
    for teacher_logits, weight in zip(teacher_logits_list, weights):
        soft = F.softmax(teacher_logits / temperature, dim=-1)
        soft_targets.append(soft * weight)

    # Weighted-average soft target
    averaged_soft = sum(soft_targets)

    # Distillation loss against the mixture
    soft_student = F.log_softmax(student_logits / temperature, dim=-1)
    loss = F.kl_div(soft_student, averaged_soft, reduction="batchmean")

    return loss

# Example: two LOCAL teachers with a shared tokenizer (Qwen2.5 family).
# API teachers (GPT-4, Claude) can't join this loss — their logits are
# never exposed, so distill from them via generated DATA instead
# (Data Generation section below)
teachers = [teacher_a, teacher_b]  # loaded AutoModelForCausalLM
weights = [0.6, 0.4]               # one weight per teacher
```

### Self-Distillation
```python
import copy
import torch.nn as nn

class SelfDistillation(nn.Module):
    """
    Student learns from its own earlier state (mean-teacher style):
    a frozen EMA copy built ONCE, not rebuilt per forward pass
    """
    def __init__(self, model):
        super().__init__()
        self.model = model
        # ONE frozen snapshot from init — reconstructing the teacher with
        # self.model.__class__(config) + load_state_dict inside forward
        # would copy the whole model on EVERY step
        self.teacher = copy.deepcopy(model)
        self.teacher.eval()
        for p in self.teacher.parameters():
            p.requires_grad_(False)
        self.teacher_ready = False

    def update_teacher(self):
        """EMA: the teacher slowly tracks the student's weights"""
        with torch.no_grad():
            for t, s in zip(self.teacher.parameters(), self.model.parameters()):
                t.mul_(0.999).add_(s.detach(), alpha=0.001)
        self.teacher_ready = True

    def forward(self, x, labels):
        # Student forward
        student_logits = self.model(x).logits

        # Teacher forward (frozen copy, cached since __init__)
        if self.teacher_ready:
            with torch.no_grad():
                teacher_logits = self.teacher(x).logits

            # Distillation loss
            loss = distillation_loss(
                student_logits,
                teacher_logits,
                labels,
                temperature=2.0,
                alpha=0.7
            )
        else:
            # Before the first update_teacher(): standard training
            V = student_logits.size(-1)
            loss = F.cross_entropy(
                student_logits.view(-1, V),
                labels.view(-1),
                ignore_index=-100,
            )

        return loss
```

## Data Generation for Distillation

### Using an API Teacher
```python
from openai import OpenAI  # openai>=1.0 — ChatCompletion.create is gone

client = OpenAI()  # reads OPENAI_API_KEY from the environment

def generate_teacher_data(prompt, model="gpt-5-mini", variation=0):
    """
    Generate training data using an API teacher. GPT-5 pins sampling
    (no temperature dial), so diversity comes from varying the ask.
    """
    ask = f"{prompt}\n\nVariation {variation}: cover this from a different angle."
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": ask}],
    )
    return response.choices[0].message.content

def create_distillation_dataset(base_prompts, num_samples_per_prompt=5):
    """
    Create dataset by sampling from teacher
    """
    dataset = []

    for prompt in base_prompts:
        for k in range(num_samples_per_prompt):
            teacher_output = generate_teacher_data(prompt, variation=k)
            dataset.append({
                "prompt": prompt,
                "completion": teacher_output,
            })

    return dataset

# Use to train smaller model
base_prompts = [
    "Explain how KV caches speed up autoregressive decoding.",
    "Write a pytest for a rate limiter.",
]
dataset = create_distillation_dataset(base_prompts)
# Train the student on this dataset (standard SFT — see 5100/5202)
```

### Synthetic Question-Answer Pairs
```python
import re

def parse_qa_pairs(text):
    """Parse 'Q: ... A: ...' blocks out of the teacher's reply"""
    matches = re.findall(r"Q:\s*(.+?)\s*A:\s*(.+?)(?=\n\s*Q:|\Z)", text, re.S)
    return [
        {"question": q.strip(), "answer": a.strip()}
        for q, a in matches
    ]

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

    response = generate_teacher_data(prompt, model="gpt-5-mini")
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
    Compare teacher and student next-token predictions on labeled data.
    logits[t] predicts token t+1 — SHIFT before comparing to labels.
    (Teacher and student share the tokenizer, so argmax ids are
    directly comparable.)
    """
    teacher_correct = student_correct = agreed = total = 0

    teacher.eval()
    student.eval()

    with torch.no_grad():
        for batch in test_loader:
            inputs = batch["input_ids"]
            tgt = batch["labels"][:, 1:]    # targets at positions 1..T-1
            mask = tgt != -100              # real (non-padding) targets

            # Predictions — drop the last logits row to align with tgt
            teacher_preds = teacher(inputs).logits[:, :-1].argmax(dim=-1)
            student_preds = student(inputs).logits[:, :-1].argmax(dim=-1)

            teacher_correct += (teacher_preds[mask] == tgt[mask]).sum().item()
            student_correct += (student_preds[mask] == tgt[mask]).sum().item()
            agreed += (teacher_preds == student_preds)[mask].sum().item()
            total += mask.sum().item()

    if total == 0:
        raise ValueError("no labeled positions in the test set")

    teacher_acc = teacher_correct / total
    student_acc = student_correct / total

    return {
        "teacher_accuracy": teacher_acc,
        "student_accuracy": student_acc,
        "performance_gap": teacher_acc - student_acc,
        "agreement_rate": agreed / total,
    }
```

### Distillation Quality Metrics
```python
def kl_divergence(teacher_dist, student_dist):
    """
    KL(teacher ‖ student) between the two output distributions —
    lower means the student tracks the teacher more closely.

    F.kl_div takes LOG-probs as its first argument:
    kl_div(student.log(), teacher) = Σ teacher·(log teacher − log student)
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

## Summary

Distillation compresses a large teacher into a small student by training the student on the teacher's softened output distribution - the loss carries dark knowledge plain labels do not. This lesson covered the concept, the distillation loss and its temperature, the advanced techniques, data generation from the teacher, and honest evaluation against the teacher's ceiling. The practical tips close it: distill for deployment efficiency, and measure the student on the metrics that matter to users, not just accuracy.

## References

### Related Minder Academy Documents

- [5302: Distributed Training Orchestration](5302-Distributed-Training.md)
- [5303: Federated Learning](5303-Federated-Learning.md)

---

## Next Steps

- Continue with: **[5401: Data Parallelism](./../5400-distributed-training/5401-Data-Parallelism.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_5301: Distillation](../../../../experiments/EXP_5301_DISTILLATION.md)**
