---
Document ID: PHASE2-QUIZ
Title: "Phase 2: AI/ML Foundations Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['assessment', 'quiz', 'pytorch']
---

# Phase 2: AI/ML Foundations Quiz

**20 Questions | Passing Score: 80% | Time: 45 minutes**

---

## Questions

### 1. What does the backward pass in neural networks compute?
a) Gradients of loss with respect to parameters
b) Activation values
c) Learning rate
d) Forward predictions replayed to refresh validation loss baselines each epoch

**Answer:** a

---

### 2. In PyTorch, what is a computational graph?
a) Network architecture
b) Data storage structure
c) Dynamic representation of computations
d) Static memory allocation graphs frozen before each forward pass

**Answer:** c

---

### 3. What is einsum notation used for?
a) Tensor operations
b) Data storage
c) Model compression
d) Network optimization

**Answer:** a

---

### 4. What does autograd in PyTorch do?
a) Automatic differentiation
b) Automatic data loading
c) Automatic model selection
d) Automatic optimization

**Answer:** a

---

### 5. What is the chain rule used for in backpropagation?
a) Computing gradients through layered functions
b) Optimizing learning rate schedules across successive backward sweeps
c) Regularizing weights
d) Normalizing inputs

**Answer:** a

---

### 6. What is XLA in TensorFlow?
a) External Library Adapter exported for custom backend plugins
b) Accelerated Linear Algebra compiler
c) Extended Learning Architecture
d) Execution Layer Abstraction

**Answer:** b

---

### 7. What is CUDA?
a) Parallel computing platform for NVIDIA GPUs
b) Memory management system
c) Network protocol
d) CPU optimization technique for scheduling CUDA-aware kernels on cores

**Answer:** a

---

### 8. What is a tensor?
a) Vector space extended with learned basis vectors
b) Matrix operation
c) Multi-dimensional array
d) Data frame

**Answer:** c

---

### 9. What is broadcasting in tensor operations?
a) Data transmission
b) Model deployment
c) Expanding dimensions for arithmetic
d) Network communication

**Answer:** c

---

### 10. What is gradient checkpointing?
a) Speed optimization
b) Trading computation for memory
c) Data compression of activations between training steps
d) Model pruning

**Answer:** b

---

### 11. What is vanishing gradient?
a) Gradients grow uncontrollably
b) Gradients shrink toward zero
c) Weight decay
d) Learning rate decay

**Answer:** b

---

### 12. What is a kernel in CUDA?
a) Memory allocation unit
b) Function executed on GPU
c) Control structure
d) Data type

**Answer:** b

---

### 13. What does JIT compilation stand for?
a) Java Interface Technology
b) Just-In-Time
c) JSON Interchange Tool
d) Joint Integration Test

**Answer:** b

---

### 14. What is momentum in optimization?
a) Learning rate scheduling
b) Weight initialization
c) Accumulating past gradients
d) Data augmentation

**Answer:** c

---

### 15. What is the purpose of a loss function?
a) Increase model size
b) Speed up training by shrinking the batch dimension
c) Measure model error
d) Reduce memory

**Answer:** c

---

### 16. What is batch normalization?
a) Normalizing outputs
b) Normalizing weights
c) Normalizing gradients
d) Normalizing layer inputs

**Answer:** d

---

### 17. What is a learning rate?
a) Model size
b) Batch size
c) Data size
d) Step size for weight updates

**Answer:** d

---

### 18. What is overfitting?
a) Model underfitting the training set
b) Model convergence
c) Model stability
d) Model memorizing training data

**Answer:** d

---

### 19. What is regularization?
a) Speeding up training
b) Increasing model size
c) Reducing data
d) Preventing overfitting

**Answer:** d

---

### 20. What is SGD?
a) Sparse Gradient Descent
b) Structured Grid Design
c) Static Graph Definition
d) Stochastic Gradient Descent

**Answer:** d

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

