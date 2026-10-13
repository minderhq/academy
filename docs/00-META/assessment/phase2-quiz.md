---
Document ID: PHASE2-QUIZ
Title: "Phase 2: AI/ML Foundations Quiz"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['assessment', 'quiz', 'pytorch']
---

# Phase 2: AI/ML Foundations Quiz

**20 Questions | Passing Score: 80% | Time: 45 minutes**

## Instructions

- **20 questions**, one best answer each
- **Passing score: 80%** (16/20 correct)
- Answers live only in the Answer Key at the end of this quiz - attempt every question before checking it
- Graded below the line? The Need to Review? map above the Answer Key links every question to its closest lesson - rework those before your next attempt
- **Practice:** [Phase 2 Practice](phase2-practice.md) - Hands-on foundations exercises

---

## Questions

### 1. What does the backward pass in neural networks compute?
- a) Gradients of loss with respect to parameters
- b) Activation values
- c) Learning rate
- d) Forward predictions replayed to refresh validation loss baselines each epoch

---

### 2. In PyTorch, what is a computational graph?
- a) Network architecture
- b) Data storage structure
- c) Dynamic representation of computations
- d) Static memory allocation graphs frozen before each forward pass

---

### 3. What is einsum notation used for?
- a) Tensor operations
- b) Data storage
- c) Model compression
- d) Network optimization

---

### 4. What does autograd in PyTorch do?
- a) Automatic differentiation
- b) Automatic data loading
- c) Automatic model selection
- d) Automatic optimization

---

### 5. What is the chain rule used for in backpropagation?
- a) Computing gradients through layered functions
- b) Optimizing learning rate schedules across successive backward sweeps
- c) Regularizing weights
- d) Normalizing inputs

---

### 6. What is XLA in TensorFlow?
- a) External Library Adapter exported for custom backend plugins
- b) Accelerated Linear Algebra compiler
- c) Extended Learning Architecture
- d) Execution Layer Abstraction

---

### 7. What is CUDA?
- a) Parallel computing platform for NVIDIA GPUs
- b) Memory management system
- c) Network protocol
- d) CPU optimization technique for scheduling CUDA-aware kernels on cores

---

### 8. What is a tensor?
- a) Vector space extended with learned basis vectors
- b) Matrix operation
- c) Multi-dimensional array
- d) Data frame

---

### 9. What is broadcasting in tensor operations?
- a) Data transmission
- b) Model deployment
- c) Expanding dimensions for arithmetic
- d) Network communication

---

### 10. What is gradient checkpointing?
- a) Speed optimization
- b) Trading computation for memory
- c) Data compression of activations between training steps
- d) Model pruning

---

### 11. What is vanishing gradient?
- a) Gradients grow uncontrollably
- b) Gradients shrink toward zero
- c) Weight decay
- d) Learning rate decay

---

### 12. What is a kernel in CUDA?
- a) Memory allocation unit
- b) Function executed on GPU
- c) Control structure
- d) Data type

---

### 13. What does JIT compilation stand for?
- a) Java Interface Technology
- b) Just-In-Time
- c) JSON Interchange Tool
- d) Joint Integration Test

---

### 14. What is momentum in optimization?
- a) Learning rate scheduling
- b) Weight initialization
- c) Accumulating past gradients
- d) Data augmentation

---

### 15. What is the purpose of a loss function?
- a) Increase model size
- b) Speed up training by shrinking the batch dimension
- c) Measure model error
- d) Reduce memory

---

### 16. What is batch normalization?
- a) Normalizing outputs
- b) Normalizing weights
- c) Normalizing gradients
- d) Normalizing layer inputs

---

### 17. What is a learning rate?
- a) Model size
- b) Batch size
- c) Data size
- d) Step size for weight updates

---

### 18. What is overfitting?
- a) Model underfitting the training set
- b) Model convergence
- c) Model stability
- d) Model memorizing training data

---

### 19. What is regularization?
- a) Speeding up training
- b) Increasing model size
- c) Reducing data
- d) Preventing overfitting

---

### 20. What is SGD?
- a) Sparse Gradient Descent
- b) Structured Grid Design
- c) Static Graph Definition
- d) Stochastic Gradient Descent

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 5, 11:** [2102: Backpropagation and Derivatives](../../phases/phase2-foundations/2100-calculus/2102-Backpropagation-and-Derivatives.md) — the backward pass, the chain rule and vanishing gradients
- **Questions 2, 4:** [2201: PyTorch Computational Graphs](../../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md) — computational graphs and autograd
- **Questions 3, 8-9:** [2101: Tensor Algebra](../../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md) — einsum notation, tensors and broadcasting
- **Questions 6, 13:** [2202: TensorFlow XLA Compilers](../../phases/phase2-foundations/2200-frameworks/2202-TensorFlow-XLA-Compilers.md) — XLA and JIT compilation
- **Questions 7, 12:** [2203: CUDA Kernel Programming](../../phases/phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Programming.md) — the CUDA platform and writing kernels
- **Question 10:** [2402: Large Scale Training](../../phases/phase2-foundations/2400-pretraining/2402-Large-Scale-Training.md) — gradient checkpointing and its memory-for-compute trade
- **Questions 14-15:** [2103: Loss Landscape Geometry](../../phases/phase2-foundations/2100-calculus/2103-Loss-Landscape-Geometry.md) — loss functions and momentum moving over the loss surface
- **Question 16:** [3302: Normalization Layers](../../phases/phase3-transformers/3300-decoding/3302-Normalization-Layers.md) — batch normalization of layer inputs
- **Question 17:** [5502: Learning Rate Scheduling](../../phases/phase5-finetuning/5500-advanced-optimization/5502-Learning-Rate-Scheduling.md) — the learning rate as the update step size
- **Questions 18-19:** [2401: Pre training Fundamentals](../../phases/phase2-foundations/2400-pretraining/2401-Pre-training-Fundamentals.md) — overfitting as memorization and the regularization answer
- **Question 20:** [5501: Optimizer Variants](../../phases/phase5-finetuning/5500-advanced-optimization/5501-Optimizer-Variants.md) — stochastic gradient descent and its variants

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | A | The backward pass computes gradients of the loss with respect to each parameter |
| 2 | C | PyTorch builds its computational graph dynamically as operations execute |
| 3 | A | einsum expresses tensor operations such as products and contractions compactly |
| 4 | A | autograd records operations and differentiates through them automatically |
| 5 | A | The chain rule multiplies local gradients through the layered functions of backpropagation |
| 6 | B | XLA is the Accelerated Linear Algebra compiler |
| 7 | A | CUDA is NVIDIA's parallel computing platform for GPUs |
| 8 | C | A tensor is a multi-dimensional array |
| 9 | C | Broadcasting expands smaller tensors' dimensions so arithmetic between shapes lines up |
| 10 | B | Gradient checkpointing trades recomputation for less stored activation memory |
| 11 | B | Vanishing gradients shrink toward zero through many layers, stalling learning early in the stack |
| 12 | B | A CUDA kernel is a function executed on the GPU by many threads at once |
| 13 | B | JIT stands for Just-In-Time compilation |
| 14 | C | Momentum accumulates past gradients to smooth and accelerate parameter updates |
| 15 | C | The loss function measures model error - the quantity training minimizes |
| 16 | D | Batch normalization normalizes each layer's inputs over the batch |
| 17 | D | The learning rate is the step size of each weight update |
| 18 | D | Overfitting is memorizing the training data at the cost of generalization |
| 19 | D | Regularization constrains the model to prevent overfitting |
| 20 | D | SGD stands for Stochastic Gradient Descent |

**Passing: 16/20 (80%)**

