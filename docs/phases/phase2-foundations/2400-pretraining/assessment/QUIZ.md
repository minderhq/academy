---
Document ID: 2400-QUIZ
Title: "Module 2400: Pretraining Fundamentals Quiz"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# Module 2400: Pretraining Fundamentals Quiz

**Module:** Pretraining & Distributed Training
**Document ID:** 2400
**Difficulty:** Advanced
**Time:** 30 minutes

---

## Instructions

Select the best answer for each question. Answers are provided at the bottom.

---

## Questions

### 1. What is the primary purpose of pretraining?

A) To adapt a model to a specific task
B) To learn general representations from large datasets
C) To fine-tune hyperparameters
D) To reduce model size

### 2. Which technique enables training large models across multiple GPUs?

A) Gradient checkpointing
B) Fully Sharded Data Parallel (FSDP)
C) Mixed precision training
D) All of the above

### 3. What does FSDP stand for?

A) Fast Sharded Data Processing
B) Fully Sharded Data Parallel
C) Federated Sharded Distributed Parallel
D) None of the above

### 4. What is the main benefit of mixed precision training?

A) Improved model accuracy
B) Reduced memory usage and faster computation
C) Better generalization
D) Simpler code

### 5. Which optimizer is most commonly used for pretraining LLMs?

A) SGD
B) Adam
C) AdamW
D) RMSprop

### 6. What is gradient accumulation used for?

A) Improving model accuracy
B) Simulating larger batch sizes with limited memory
C) Speeding up training
D) Reducing overfitting

### 7. What is the purpose of learning rate scheduling?

A) To prevent overfitting
B) To adjust learning rate during training for better convergence
C) To reduce training time
D) To increase model capacity

### 8. What is tokenizer vocabulary size typically for LLMs?

A) 1K - 5K tokens
B) 10K - 50K tokens
C) 50K - 200K tokens
D) 1M+ tokens

### 9. What is the primary challenge of distributed training?

A) Slower computation
B) Communication overhead between devices
C) Reduced model accuracy
D) All of the above

### 10. What does "warmup" refer to in learning rate scheduling?

A) Cooling down the GPU
B) Gradually increasing learning rate at the start
C) Preheating the data pipeline
D) None of the above

---

## Answers

1. **B** - Pretraining learns general representations from large, diverse datasets
2. **D** - All techniques enable distributed training
3. **B** - Fully Sharded Data Parallel
4. **B** - Uses FP16/BF16 for faster computation and less memory
5. **C** - AdamW (Adam with decoupled weight decay)
6. **B** - Accumulates gradients over multiple steps to simulate larger batches
7. **B** - Dynamic LR adjustment improves convergence
8. **C** - Most modern LLMs use 50K-200K vocab sizes
9. **B** - Communication between GPUs/TPUs is the main bottleneck
10. **B** - Gradually increasing LR prevents instability at training start

---

**Score:** ___ / 10
**Passing:** 7/10

**Next:** Review [PRACTICE.md](./PRACTICE.md) for hands-on exercises
