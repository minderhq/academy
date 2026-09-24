# Module 5100: PEFT Methods Quiz

**Module:** Parameter-Efficient Fine-Tuning
**Document ID:** 5100
**Difficulty:** Advanced
**Time:** 30 minutes

---

## Instructions

Select the best answer for each question. Answers are provided at the bottom.

---

## Questions

### 1. What is the primary advantage of PEFT methods?

A) Faster training
B) Train only a small subset of parameters
C) Better model accuracy
D) Simpler architecture

### 2. What does LoRA stand for?

A) Low-Rank Adaptation
B) Linear Optimization for Recurrent Architectures
C) Layer-wise Optimization for Rapid Adaptation
D) None of the above

### 3. How many trainable parameters does LoRA typically add?

A) 0.1% - 3% of original model
B) 10% - 20% of original model
C) 50% of original model
D) Same as original model

### 4. What is the core idea behind LoRA?

A) Add low-rank matrices to existing weights
B) Replace weights with smaller matrices
C) Compress the model
D) Remove unnecessary layers

### 5. What is QLoRA?

A) Quantized LoRA
B) Quick LoRA
C) Quality LoRA
D) Query-based LoRA

### 6. What rank is typically used for LoRA?

A) 1-4
B) 4-64
C) 64-256
D) 256-1024

### 7. What happens during LoRA inference?

A) LoRA weights are used separately
B) LoRA weights are merged with base model
C) LoRA weights are discarded
D) Model is retrained

### 8. What is Adapter in PEFT context?

A) Data loading adapter
B) Small bottleneck layers added to transformer
C) Hardware adapter
D) Training script adapter

### 9. What is Prefix Tuning?

A) Tuning the vocabulary prefix
B) Learning virtual tokens prepended to input
C) Tuning only first N layers
D) Quick tuning method

### 10. Why is PEFT important for LLMs?

A) Only small models can be fine-tuned
B) Makes fine-tuning 70B+ models feasible
C) Required by law
D) Improves training speed only

---

## Answers

1. **B** - Only small parameter subset is trained, reducing memory/compute
2. **A** - Low-Rank Adaptation
3. **A** - Typically 0.1-3% of original parameters
4. **A** - Add trainable low-rank decomposition: W + AB where A,B are low-rank
5. **A** - Quantized LoRA (base model in 4-bit, LoRA adapters in full precision)
6. **B** - Rank 4-64 is typical (r=8, r=16, r=32 common)
7. **B** - Merge: W_new = W_frozen + (A @ B)^T for zero overhead
8. **B** - Small bottleneck layers inserted into each transformer block
9. **B** - Learn continuous prompt embeddings (virtual tokens)
10. **B** - Makes fine-tuning large models accessible with limited resources

---

**Score:** ___ / 10
**Passing:** 7/10

**Next:** Review [PRACTICE.md](./PRACTICE.md) for hands-on exercises
