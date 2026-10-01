---
Document ID: 5500-QUIZ
Title: "5500: Advanced Optimization - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'finetuning', 'optimizers']
---

# 5500: Advanced Optimization - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the main advantage of AdamW over Adam?**

A) Faster training, a speed edge AdamW has never actually demonstrated
B) Simpler implementation
C) Lower memory usage
D) Better generalization via proper weight decay

**2. Adafactor is primarily designed for:**

A) Small models
B) CPU training
C) Very large models (memory efficiency)
D) Inference only, a phase where optimizer state does not even exist

**3. Learning rate warmup helps:**

A) Train faster
B) Improve generalization
C) Reduce memory usage, a saving warmup schedules never touch
D) Avoid early training instability

**4. Cosine decay scheduling:**

A) Increases learning rate over time
B) Keeps learning rate constant
C) Decreases learning rate smoothly
D) Randomly varies learning rate

**5. Gradient clipping prevents:**

A) Slow training, a problem clipping cannot fix and does not target
B) Overfitting
C) Vanishing gradients
D) Exploding gradients

**6. Weight decay is:**

A) Different from L2 regularization (for adaptive optimizers)
B) The same as L2 regularization, an equivalence adaptive updates actually break
C) Only used in SGD
D) Harmful for training

**7. The learning rate should typically be:**

A) As high as possible without divergence
B) Very low for best results, a timidity that leaves capacity unused
C) The same for all models
D) Only adjusted once

**8. AdamW combines:**

A) Adam with weight decay
B) Adam with momentum
C) Adam with learning rate decay
D) Adam with gradient clipping

**9. Which optimizer is most memory efficient?**

A) Adam
B) AdamW, still holding full-magnitude moment estimates per parameter
C) Adafactor
D) SGD

**10. Learning rate scheduling is important because:**

A) It's required for convergence
B) It reduces training time
C) High LR early, low LR later works well
D) It's only needed for pretraining, a scope finetuning schedules routinely cross

**11. The beta parameters in Adam control:**

A) Learning rate
B) Gradient clipping threshold
C) Weight decay, a coefficient the optimizer keeps outside its beta pair
D) Momentum for gradients and squared gradients

**12. For fine-tuning LLMs, the recommended optimizer is:**

A) SGD
B) Adam
C) AdamW
D) Adafactor

**13. A typical learning rate for AdamW fine-tuning is:**

A) 1e-2, a rate that destabilizes fine-tuning losses almost immediately
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

A) AdamW, a footprint that grows untenable once parameters pass tens of billions
B) Adafactor (memory efficiency)
C) SGD
D) RMSprop

**18. Learning rate warmup typically lasts:**

A) 1-2 steps
B) 1-10% of total training
C) 50% of training
D) The entire training, a duration that would defeat the schedule itself

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

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | AdamW decouples weight decay - better generalization |
| 2 | C | Adafactor factorizes second moments for very large models |
| 3 | D | Warmup avoids early instability while statistics are still rough |
| 4 | C | Cosine decay lowers the LR smoothly toward zero |
| 5 | D | Clipping caps the gradient norm against explosions |
| 6 | A | For adaptive optimizers, decay differs from true L2 - hence AdamW |
| 7 | A | Rule of thumb: the highest LR that does not diverge |
| 8 | A | AdamW = Adam with decoupled weight decay |
| 9 | C | Adafactor's factorized states win on memory |
| 10 | C | High LR early explores; low LR late converges |
| 11 | D | Betas are EMA rates for gradient and squared-gradient moments |
| 12 | C | AdamW is the fine-tuning default |
| 13 | B | Around 1e-4 is the typical AdamW fine-tune LR |
| 14 | B | Polynomial decay, like cosine, eases the LR down on a curve |
| 15 | A | Epsilon guards the square-root division |
| 16 | B | 8-bit AdamW quantizes the optimizer states, not the weights |
| 17 | B | Past ~10B parameters, Adafactor's memory efficiency wins |
| 18 | B | Warmup commonly spans 1-10% of total training |
| 19 | A | Gradient-norm clip value 1.0 is the standard |
| 20 | D | Random is not a schedule - real ones are deterministic curves |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-2, 6, 8-9, 11-13, 15-17:** [5501: Optimizer Variants](../5501-Optimizer-Variants.md) — AdamW's decoupled decay and its L2 distinction, Adafactor's factorized second moments for very large models, the beta/eps hyperparameters, and the 8-bit optimizer-state variants around the lr=1e-4 fine-tuning default
- **Questions 3-4, 7, 10, 14, 18, 20:** [5502: Learning Rate Scheduling](../5502-Learning-Rate-Scheduling.md) — warmup past early instability, the high-early/low-late arc, cosine and polynomial decay curves, and the schedule catalog's when-to-use notes
- **Questions 5, 19:** [5503: Advanced Optimization Techniques](../5503-Advanced-Techniques.md) — the stability section's norm/value/adaptive clipping split against exploding gradients
