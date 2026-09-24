---
Document ID: 2400-QUIZ
Title: "2400: Pretraining Fundamentals - Quiz"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# 2400: Pretraining Fundamentals - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the primary purpose of pretraining?**

A) To adapt a model to a specific task
B) To learn general representations from large datasets
C) To fine-tune hyperparameters
D) To reduce model size

**2. Which technique enables training large models across multiple GPUs?**

A) Gradient checkpointing
B) Fully Sharded Data Parallel (FSDP)
C) Mixed precision training
D) All of the above

**3. What does FSDP stand for?**

A) Fast Sharded Data Processing
B) Fully Sharded Data Parallel
C) Federated Sharded Distributed Parallel
D) None of the above

**4. What is the main benefit of mixed precision training?**

A) Improved model accuracy
B) Reduced memory usage and faster computation
C) Better generalization
D) Simpler code

**5. Which optimizer is most commonly used for pretraining LLMs?**

A) SGD
B) Adam
C) AdamW
D) RMSprop

**6. What is gradient accumulation used for?**

A) Improving model accuracy
B) Simulating larger batch sizes with limited memory
C) Speeding up training
D) Reducing overfitting

**7. What is the purpose of learning rate scheduling?**

A) To prevent overfitting
B) To adjust learning rate during training for better convergence
C) To reduce training time
D) To increase model capacity

**8. What is tokenizer vocabulary size typically for LLMs?**

A) 1K - 5K tokens
B) 10K - 50K tokens
C) 50K - 200K tokens
D) 1M+ tokens

**9. What is the primary challenge of distributed training?**

A) Slower computation
B) Communication overhead between devices
C) Reduced model accuracy
D) All of the above

**10. What does "warmup" refer to in learning rate scheduling?**

A) Cooling down the GPU
B) Gradually increasing learning rate at the start
C) Preheating the data pipeline
D) None of the above

**11. For GPT-style models, the standard pretraining objective is:**

A) Next-token prediction (causal language modeling)
B) Masked language modeling
C) Denoising autoencoding
D) Contrastive learning

**12. Roughly how much text do modern LLM pretraining runs consume?**

A) Millions of tokens
B) Tens of millions of tokens
C) Hundreds of billions to trillions of tokens
D) A few thousand tokens

**13. Which tokenization algorithm is most common for LLM vocabularies?**

A) Word-level tokenization
B) Byte Pair Encoding (BPE)
C) Character-level tokenization
D) Fixed hashing

**14. Scaling laws (e.g., Chinchilla) describe:**

A) How GPU memory grows over time
B) How to shrink the vocabulary
C) Hardware pricing trends
D) The optimal trade-off between model size, data, and compute

**15. Which metric is monitored during pretraining?**

A) Human preference win rate
B) BLEU score
C) Perplexity on held-out text
D) F1 on a classification benchmark

**16. Why is benchmark contamination (decontamination) checked before pretraining?**

A) So evaluations measure generalization rather than memorization
B) To reduce GPU memory
C) To speed up data loading
D) To balance the data pipeline

**17. The main trade-off of gradient checkpointing is:**

A) Lower model accuracy
B) Reduced memory in exchange for extra recomputation compute
C) Larger optimizer states
D) Slower data loading

**18. Which parallelism strategy splits model layers across devices?**

A) Data parallelism
B) Gradient accumulation
C) Pipeline parallelism
D) Sequence packing

**19. ZeRO-style optimizer sharding primarily reduces:**

A) The number of attention heads
B) Vocabulary size
C) Training tokens required
D) Per-GPU memory for optimizer states and gradients

**20. At the end of pretraining, the learning rate is typically:**

A) Increased sharply
B) Held at its peak value
C) Annealed (decayed) toward a small value
D) Randomized each step

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | D |
| 3 | B |
| 4 | B |
| 5 | C |
| 6 | B |
| 7 | B |
| 8 | C |
| 9 | B |
| 10 | B |
| 11 | A |
| 12 | C |
| 13 | B |
| 14 | D |
| 15 | C |
| 16 | A |
| 17 | B |
| 18 | C |
| 19 | D |
| 20 | C |

---

**Last Updated:** 2026-09-24
