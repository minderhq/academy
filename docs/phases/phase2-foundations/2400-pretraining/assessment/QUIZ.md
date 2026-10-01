---
Document ID: 2400-QUIZ
Title: "2400: Pretraining Fundamentals - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'training', 'pretraining']
---

# 2400: Pretraining Fundamentals - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the primary purpose of pretraining?**

A) To learn general representations from large datasets
B) To adapt a model to a specific task, which is exactly what fine-tuning after pretraining does
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

A) Reduced memory usage and faster computation
B) Improved model accuracy, though precision mixing usually nudges it the other way
C) Better generalization
D) Simpler code

**5. Which optimizer is most commonly used for pretraining LLMs?**

A) SGD
B) Adam
C) RMSprop, which predates the decoupled weight decay this domain settled on
D) AdamW

**6. What is gradient accumulation used for?**

A) Improving model accuracy, an effect accumulation has no direct mechanism to cause
B) Reducing overfitting
C) Speeding up training
D) Simulating larger batch sizes with limited memory

**7. What is the purpose of learning rate scheduling?**

A) To adjust learning rate during training for better convergence
B) To prevent overfitting, a regularization job the schedule itself never performs
C) To reduce training time
D) To increase model capacity

**8. What is tokenizer vocabulary size typically for LLMs?**

A) 1K - 5K tokens, a vocabulary far too small to cover any real language
B) 10K - 50K tokens
C) 50K - 200K tokens
D) 1M+ tokens

**9. What is the primary challenge of distributed training?**

A) Slower computation, an inverse of what distributed training exists to deliver
B) Communication overhead between devices
C) Reduced model accuracy
D) All of the above

**10. What does "warmup" refer to in learning rate scheduling?**

A) Cooling down the GPU, the exact opposite direction a warmup phase moves in
B) Gradually increasing learning rate at the start
C) Preheating the data pipeline
D) None of the above

**11. For GPT-style models, the standard pretraining objective is:**

A) Next-token prediction (causal language modeling)
B) Masked language modeling
C) Denoising autoencoding, a recipe tied to encoder architectures BERT grew out of
D) Contrastive learning

**12. Roughly how much text do modern LLM pretraining runs consume?**

A) Millions of tokens
B) Tens of millions of tokens, a volume even a single training day overshoots by far
C) Hundreds of billions to trillions of tokens
D) A few thousand tokens

**13. Which tokenization algorithm is most common for LLM vocabularies?**

A) Word-level tokenization
B) Byte Pair Encoding (BPE)
C) Character-level tokenization
D) Fixed hashing

**14. Scaling laws (e.g., Chinchilla) describe:**

A) How GPU memory grows over time, which is a hardware curve no scaling law charts
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
B) To reduce GPU memory, which the data audit never touches in any run
C) To speed up data loading
D) To balance the data pipeline

**17. The main trade-off of gradient checkpointing is:**

A) Lower model accuracy, a loss the recompute path does not actually impose
B) Reduced memory in exchange for extra recomputation compute
C) Larger optimizer states
D) Slower data loading

**18. Which parallelism strategy splits model layers across devices?**

A) Data parallelism
B) Gradient accumulation
C) Pipeline parallelism
D) Sequence packing

**19. ZeRO-style optimizer sharding primarily reduces:**

A) The number of attention heads, an architecture choice sharding never rewrites
B) Vocabulary size
C) Training tokens required
D) Per-GPU memory for optimizer states and gradients

**20. At the end of pretraining, the learning rate is typically:**

A) Increased sharply
B) Held at its peak value, a plateau no standard cosine or linear schedule ends with
C) Annealed (decayed) toward a small value
D) Randomized each step

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 5, 7, 8, 10-14, 16, 20:** [2401: Pre-training Fundamentals](../2401-Pre-training-Fundamentals.md) — data pipeline, tokenization, and schedules
- **Questions 2-4, 6, 9, 17-19:** [2402: Large-Scale Training for Language Models](../2402-Large-Scale-Training.md) — distributed strategies and memory
- **Question 15:** [2403: Evaluation Frameworks for Language Models](../2403-Evaluation-Frameworks.md) — perplexity and evaluation metrics

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | A | Pretraining learns general representations from massive corpora; tasks come later |
| 2 | D | Checkpointing, FSDP, and mixed precision each make multi-GPU training feasible |
| 3 | B | FSDP = Fully Sharded Data Parallel |
| 4 | A | Mixed precision keeps weights in fp16/bf16 - less memory, faster matmuls |
| 5 | D | AdamW (decoupled weight decay) is the LLM pretraining standard |
| 6 | D | Accumulation sums micro-batch gradients to simulate a larger batch under tight memory |
| 7 | A | Schedules adjust the learning rate over training for better convergence |
| 8 | C | LLM vocabularies are typically 50K-200K tokens (GPT-2 50K, Llama 32K-128K) |
| 9 | B | The dominant cost of distributed training is communication between devices |
| 10 | B | Warmup gradually raises the learning rate at the start of training |
| 11 | A | GPT-style models train on next-token prediction (causal language modeling) |
| 12 | C | Modern pretraining runs consume hundreds of billions to trillions of tokens |
| 13 | B | BPE (and variants) is the standard tokenization algorithm |
| 14 | D | Chinchilla-style scaling laws trade off model size, data, and compute |
| 15 | C | Held-out perplexity is the pretraining health metric |
| 16 | A | Decontamination keeps benchmarks out of training data so evals measure generalization |
| 17 | B | Checkpointing trades extra recomputation for reduced activation memory |
| 18 | C | Pipeline parallelism assigns different layers to different devices |
| 19 | D | ZeRO shards optimizer states and gradients across GPUs, cutting per-GPU memory |
| 20 | C | Standard schedules anneal the learning rate toward a small final value |
