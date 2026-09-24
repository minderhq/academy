---
Document ID: 5500-QUIZ
Title: "5500: Advanced Optimization - Quiz"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
---

# 5500: Advanced Optimization - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the main advantage of AdamW over Adam?**

A) Faster training
B) Better generalization via proper weight decay
C) Lower memory usage
D) Simpler implementation

**2. Adafactor is primarily designed for:**

A) Small models
B) Very large models (memory efficiency)
C) CPU training
D) Inference only

**3. Learning rate warmup helps:**

A) Train faster
B) Avoid early training instability
C) Reduce memory usage
D) Improve generalization

**4. Cosine decay scheduling:**

A) Increases learning rate over time
B) Decreases learning rate smoothly
C) Keeps learning rate constant
D) Randomly varies learning rate

**5. Gradient clipping prevents:**

A) Slow training
B) Exploding gradients
C) Vanishing gradients
D) Overfitting

**6. Weight decay is:**

A) The same as L2 regularization
B) Different from L2 regularization (for adaptive optimizers)
C) Only used in SGD
D) Harmful for training

**7. The learning rate should typically be:**

A) As high as possible without divergence
B) Very low for best results
C) The same for all models
D) Only adjusted once

**8. AdamW combines:**

A) Adam with weight decay
B) Adam with momentum
C) Adam with learning rate decay
D) Adam with gradient clipping

**9. Which optimizer is most memory efficient?**

A) Adam
B) AdamW
C) Adafactor
D) SGD

**10. Learning rate scheduling is important because:**

A) It's required for convergence
B) High LR early, low LR later works well
C) It reduces training time
D) It's only needed for pretraining

**11. The beta parameters in Adam control:**

A) Learning rate
B) Momentum for gradients and squared gradients
C) Weight decay
D) Gradient clipping threshold

**12. For fine-tuning LLMs, the recommended optimizer is:**

A) SGD
B) Adam
C) AdamW
D) Adafactor

**13. A typical learning rate for AdamW fine-tuning is:**

A) 1e-2
B) 1e-4
C) 1e-6
D) 1e-8

**14. Polynomial decay is similar to:**

A) Constant learning rate
B) Cosine decay
C) Exponential decay
D) Linear decay

**15. The epsilon parameter in Adam prevents:**

A) Division by zero
B) Exploding gradients
C) Vanishing gradients
D) Overfitting

**16. 8-bit AdamW:**

A) Uses 8-bit parameters
B) Uses 8-bit optimizer states
C) Is slower than standard AdamW
D) Is always better

**17. For very large models (>10B), which is preferred?**

A) AdamW
B) Adafactor (memory efficiency)
C) SGD
D) RMSprop

**18. Learning rate warmup typically lasts:**

A) 1-2 steps
B) 1-10% of total training
C) 50% of training
D) The entire training

**19. Gradient clipping value typically:**

A) Is set to 1.0
B) Is set to 0.1
C) Is set to 10.0
D) Doesn't matter

**20. Which is NOT a valid learning rate schedule?**

A) Constant
B) Cosine
C) Polynomial
D) Random

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | B |
| 3 | B |
| 4 | B |
| 5 | B |
| 6 | B |
| 7 | A |
| 8 | A |
| 9 | C |
| 10 | B |
| 11 | B |
| 12 | C |
| 13 | B |
| 14 | B |
| 15 | A |
| 16 | B |
| 17 | B |
| 18 | B |
| 19 | A |
| 20 | D |

---

**Last Updated:** 2026-02-04
