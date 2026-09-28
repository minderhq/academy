---
Document ID: 2200-QUIZ
Title: "2200: Frameworks - Quiz"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Intermediate
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
D) Pandas DataFrames

**2. `requires_grad=True` enables:**

A) GPU acceleration
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
B) Gradient computation
C) Visualization
D) Batched data iteration

**5. `torch.nn.Module` is the base class for:**

A) All neural network modules
B) Datasets
C) Optimizers
D) Loss functions

**6. The `optimizer.step()` function:**

A) Loads data
B) Clears gradients
C) Computes gradients
D) Updates model parameters

**7. `optimizer.zero_grad()` is used to:**

A) Initialize model
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

A) A loss function
B) A dataset format
C) NVIDIA GPU support
D) An optimizer

**11. `torch.save()` typically saves:**

A) Only the model architecture
B) Model state dict (parameters)
C) Training logs
D) Only the optimizer

**12. `view()` and `reshape()` are used to:**

A) Load tensors
B) Save tensors
C) Compute gradients
D) Change tensor shape

**13. A neural network layer in PyTorch is:**

A) A list
B) A function
C) A class inheriting from nn.Module
D) A dictionary

**14. `.to(device)` is used to:**

A) Save model
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

A) Stops model saving
B) Stops training
C) Stops data loading
D) Stops gradient computation

**18. Which loss function for regression?**

A) CrossEntropyLoss
B) BCELoss
C) NLLLoss
D) MSELoss

**19. Batch size affects:**

A) Only training time
B) Training time and memory
C) Only model accuracy
D) Only memory

**20. `torch.cuda.is_available()` checks:**

A) If a GPU is available
B) If the model is trained
C) If data is loaded
D) If CUDA is installed

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | A |
| 2 | C |
| 3 | B |
| 4 | D |
| 5 | A |
| 6 | D |
| 7 | B |
| 8 | C |
| 9 | C |
| 10 | C |
| 11 | B |
| 12 | D |
| 13 | C |
| 14 | B |
| 15 | A |
| 16 | A |
| 17 | D |
| 18 | D |
| 19 | B |
| 20 | A |
