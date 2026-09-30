---
Document ID: 2200-QUIZ
Title: "2200: Frameworks - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'frameworks', 'pytorch']
---

# 2200: Frameworks - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. PyTorch Tensors are similar to:**

A) NumPy arrays with GPU support
B) Python lists
C) SQL tables
D) Pandas DataFrames, built for tabular data with a very different internal memory layout

**2. `requires_grad=True` enables:**

A) GPU acceleration, which comes from device placement rather than this flag
B) Model saving
C) Automatic gradient computation
D) Data loading

**3. The `backward()` function:**

A) Updates parameters
B) Computes gradients
C) Trains the model
D) Loads data

**4. A DataLoader provides:**

A) Model storage
B) Gradient computation, which autograd handles without any loader involvement
C) Visualization
D) Batched data iteration

**5. `torch.nn.Module` is the base class for:**

A) All neural network modules
B) Datasets, which follow the torch.utils.data interface instead of this base class
C) Optimizers
D) Loss functions

**6. The `optimizer.step()` function:**

A) Loads data
B) Clears gradients
C) Computes gradients, work that happens in backward() before step() ever runs
D) Updates model parameters

**7. `optimizer.zero_grad()` is used to:**

A) Initialize model, a job for the constructor and its weight setup code
B) Clear previous gradients
C) Reset learning rate
D) Stop training

**8. `model.train()` sets the model to:**

A) CPU mode
B) GPU mode
C) Training mode
D) Evaluation mode

**9. Which is NOT a PyTorch component?**

A) nn module
B) Tensors
C) DataFrames
D) autograd

**10. CUDA in PyTorch refers to:**

A) A loss function, which is a math object with nothing to do with hardware
B) A dataset format
C) NVIDIA GPU support
D) An optimizer

**11. `torch.save()` typically saves:**

A) Only the model architecture, which pickled modules lose the code for anyway
B) Model state dict (parameters)
C) Training logs
D) Only the optimizer

**12. `view()` and `reshape()` are used to:**

A) Load tensors
B) Save tensors
C) Compute gradients, which the autograd engine records during the forward pass
D) Change tensor shape

**13. A neural network layer in PyTorch is:**

A) A list
B) A function
C) A class inheriting from nn.Module
D) A dictionary, which can hold weights but cannot run a forward pass by itself

**14. `.to(device)` is used to:**

A) Save model, a persistence job that belongs to torch.save() instead
B) Move tensors/models to GPU or CPU
C) Compute gradients
D) Load data

**15. CrossEntropyLoss expects:**

A) Raw logits as input
B) Probabilities as input
C) String labels
D) One-hot encoded labels

**16. The `forward()` method in a Module defines:**

A) The computation flow
B) How parameters are updated
C) How data is loaded
D) How gradients are computed

**17. `torch.no_grad()` context manager:**

A) Stops model saving, which torch.no_grad() has no authority over whatsoever
B) Stops training
C) Stops data loading
D) Stops gradient computation

**18. Which loss function for regression?**

A) CrossEntropyLoss
B) BCELoss
C) NLLLoss
D) MSELoss

**19. Batch size affects:**

A) Only training time, leaving hardware footprint completely untouched somehow
B) Training time and memory
C) Only model accuracy
D) Only memory

**20. `torch.cuda.is_available()` checks:**

A) If a GPU is available
B) If the model is trained
C) If data is loaded
D) If CUDA is installed

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-9, 11-13, 15-19:** [2201: PyTorch Computational Graphs and Dynamic Execution](../2201-PyTorch-Computational-Graphs.md) — tensors, autograd, and the training loop
- **Questions 10, 14, 20:** [2203: CUDA Kernel Programming and GPU Architecture](../2203-CUDA-Kernel-Programming.md) — GPU device placement and CUDA

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | A | Tensors are NumPy-like n-dimensional arrays with GPU support and autograd |
| 2 | C | requires_grad=True tells autograd to track the tensor and compute its gradients |
| 3 | B | backward() runs backpropagation and fills .grad; step() applies them later |
| 4 | D | A DataLoader iterates a Dataset in batches, with shuffling and worker processes |
| 5 | A | nn.Module is the base class for all neural network modules |
| 6 | D | optimizer.step() applies the gradients to update the parameters |
| 7 | B | zero_grad() clears the gradients accumulated by the previous backward pass |
| 8 | C | model.train() enables training behavior - dropout active, batchnorm updating |
| 9 | C | DataFrames belong to pandas; PyTorch ships nn, tensors, and autograd |
| 10 | C | CUDA is NVIDIA's GPU compute stack that PyTorch targets for acceleration |
| 11 | B | torch.save() pickles the state dict - the learned parameters |
| 12 | D | view()/reshape() change a tensor's shape without copying the data |
| 13 | C | A layer is a class inheriting from nn.Module that defines forward() |
| 14 | B | .to(device) moves tensors and models between CPU and GPU |
| 15 | A | CrossEntropyLoss applies log-softmax internally, so it wants raw logits |
| 16 | A | forward() defines the computation flow from input to output |
| 17 | D | no_grad() disables gradient tracking - the context for inference and evaluation |
| 18 | D | MSELoss is the standard loss for regression |
| 19 | B | Larger batches raise both memory footprint and per-step time |
| 20 | A | is_available() checks whether a CUDA-capable GPU is present |
