---
Document ID: 5100-QUIZ
Title: "5100: PEFT Methods - Quiz"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# 5100: PEFT Methods - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the primary advantage of PEFT methods?**

A) Faster training
B) Train only a small subset of parameters
C) Better model accuracy
D) Simpler architecture

**2. What does LoRA stand for?**

A) Low-Rank Adaptation
B) Linear Optimization for Recurrent Architectures
C) Layer-wise Optimization for Rapid Adaptation
D) None of the above

**3. How many trainable parameters does LoRA typically add?**

A) 0.1% - 3% of original model
B) 10% - 20% of original model
C) 50% of original model
D) Same as original model

**4. What is the core idea behind LoRA?**

A) Add low-rank matrices to existing weights
B) Replace weights with smaller matrices
C) Compress the model
D) Remove unnecessary layers

**5. What is QLoRA?**

A) Quantized LoRA
B) Quick LoRA
C) Quality LoRA
D) Query-based LoRA

**6. What rank is typically used for LoRA?**

A) 1-4
B) 4-64
C) 64-256
D) 256-1024

**7. What happens during LoRA inference?**

A) LoRA weights are used separately
B) LoRA weights are merged with base model
C) LoRA weights are discarded
D) Model is retrained

**8. What is Adapter in PEFT context?**

A) Data loading adapter
B) Small bottleneck layers added to transformer
C) Hardware adapter
D) Training script adapter

**9. What is Prefix Tuning?**

A) Tuning the vocabulary prefix
B) Learning virtual tokens prepended to input
C) Tuning only first N layers
D) Quick tuning method

**10. Why is PEFT important for LLMs?**

A) Only small models can be fine-tuned
B) Makes fine-tuning 70B+ models feasible
C) Required by law
D) Improves training speed only

**11. In LoRA, alpha controls:**

A) The scaling of the low-rank update (ΔW = α/r · BA)
B) The learning rate
C) The batch size
D) The quantization bit-width

**12. LoRA updates are most commonly applied to:**

A) Embedding tables only
B) Layer norms
C) Attention projection matrices (e.g., q_proj, v_proj)
D) The LM head only

**13. QLoRA's base model is stored in:**

A) FP32
B) 4-bit NF4
C) INT8 per-channel
D) FP16

**14. Double quantization in QLoRA:**

A) Applies quantization twice for accuracy
B) Quantizes the quantization constants themselves to save memory
C) Duplicates weights across GPUs
D) Quantizes gradients

**15. A higher LoRA rank (r) generally:**

A) Always reduces quality
B) Has no effect
C) Increases capacity and the adapter's memory footprint
D) Reduces training time proportionally

**16. Compared with full fine-tuning, LoRA saves the most memory on:**

A) Activation memory only
B) Optimizer states for the frozen weights
C) Data loading buffers
D) Logits storage

**17. Multiple task-specific LoRA adapters on one base model can be:**

A) Served by swapping adapters without storing full model copies
B) Merged into the tokenizer
C) Used only one at a time per datacenter
D) Trained simultaneously on one GPU at no cost

**18. Which PEFT method trains only continuous prompt vectors while keeping the model frozen?**

A) Full fine-tuning
B) Prompt tuning / soft prompting
C) LoRA on all layers
D) Knowledge distillation

**19. Merging LoRA as W' = W + (α/r)BA is valid because:**

A) BA has the same shape as W
B) LoRA changes the tokenizer
C) Alpha equals the learning rate
D) B and A are orthogonal by construction

**20. IA³ / BitFit-style PEFT methods differ from LoRA by:**

A) Rewriting the attention math
B) Requiring more trainable parameters than full fine-tuning
C) Tuning very small vectors/biases instead of low-rank matrices
D) Only working on encoder models

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | A |
| 3 | A |
| 4 | A |
| 5 | A |
| 6 | B |
| 7 | B |
| 8 | B |
| 9 | B |
| 10 | B |
| 11 | A |
| 12 | C |
| 13 | B |
| 14 | B |
| 15 | C |
| 16 | B |
| 17 | A |
| 18 | B |
| 19 | A |
| 20 | C |
