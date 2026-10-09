---
Document ID: PHASE2-CHECKPOINT
Title: "Progress Checkpoint: Phase 2 - Cognitive Science & Frameworks"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['checkpoint', 'frameworks', 'architecture', 'api-design']
---

# Progress Checkpoint: Phase 2 - Cognitive Science & Frameworks

**Track your progress through Phase 2 modules**

---

## Phase 2 Overview

**Phase:** [2000] Cognitive Science & Frameworks

**Modules:** 4 (2100, 2200, 2300, 2400)

**Estimated Time:** 3-4 weeks

**Difficulty:** ⭐⭐ Intermediate

---

## Phase Completion Goal

After completing Phase 2, you will:

- Understand tensor operations
- Implement backpropagation
- Know ML framework internals
- Understand pre-training fundamentals
- Be ready for transformer architecture

---

## Module Checkpoints

### Module 2100: Calculus for Deep Learning (Required)

**Checkpoint Quiz:**

1. What is a tensor and how does it differ from an array?
2. Explain the dot product and its geometric interpretation
3. What is gradient descent?

**Practical Verification:**

- [ ] Can implement matrix multiplication from scratch
- [ ] Understand PyTorch tensor operations
- [ ] Can compute gradients

---

### Module 2200: Deep Learning Frameworks (Required)

**Checkpoint Quiz:**

1. What is a computational graph?
2. How does PyTorch track gradients?
3. What is XLA compilation?

**Practical Verification:**

- [ ] Can build neural network in PyTorch
- [ ] Understand automatic differentiation
- [ ] Can optimize computation

---

### Module 2300: Framework Engineering (Required)

**Checkpoint Quiz:**

1. How does a reverse-mode autograd engine propagate gradients through a computational graph?
2. What bookkeeping does a Tensor class need to support backward passes?
3. How do you validate custom operations against PyTorch reference results?

**Practical Verification:**

- [ ] Can implement a minimal autograd engine from scratch
- [ ] Understand graph construction and topological sort for backward passes
- [ ] Can validate custom tensor ops against reference outputs

---

### Module 2400: Pre-training (Required)

**Checkpoint Quiz:**

1. What are the key stages of a pre-training pipeline?
2. How do data parallel and model parallel sharding differ?
3. What metrics are used to evaluate a pretrained language model?

**Practical Verification:**

- [ ] Understand the pre-training data pipeline
- [ ] Can explain distributed training strategies
- [ ] Know how to evaluate a pretrained checkpoint

---

## Common Pitfalls

1. **Stale Gradients:** Forgetting `optimizer.zero_grad()` between steps silently accumulates gradients across batches and corrupts every update
2. **Device Mismatch:** Mixing CPU and GPU tensors in one op raises a runtime error only when that branch first executes - move the whole model and batch together
3. **no_grad Blind Spot:** Running inference without `torch.no_grad()` keeps the autograd graph alive and quietly eats VRAM until OOM
4. **Leaky Normalization:** Fitting scalers or computing batch statistics on the full dataset leaks test information into training

---

## Phase 2 Completion Badge

**Badge:** Tensor Master

**You've earned it when:**

- All required modules completed
- Can implement backpropagation
- Understand framework internals
