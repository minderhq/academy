---
Document ID: PHASE5-QUIZ
Title: "Phase 5: Fine-Tuning & Alignment Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Tags: ['assessment', 'quiz', 'finetuning']
---

# Phase 5: Fine-Tuning & Alignment Quiz

**30 Questions | Passing Score: 80% | Time: 60 minutes**

---

## Questions

### 1. What is LoRA?
a) Learning Rate Optimization
b) Large Model Optimization
c) Linear Regression Adaptation with frozen projection heads
d) Low-Rank Adaptation for efficient fine-tuning

**Answer:** d

---

### 2. What is the main benefit of LoRA over full fine-tuning?
a) Trains fewer parameters
b) Faster training
c) Better accuracy
d) Simpler implementation

**Answer:** a

---

### 3. What does the Q in QLoRA stand for?
a) Quick LoRA
b) Quality LoRA
c) Quantum LoRA
d) Quantization-aware LoRA

**Answer:** d

---

### 4. What is the rank parameter in LoRA?
a) Dimension of low-rank matrices
b) Overall rank of the frozen base model
c) Training rank
d) Data rank

**Answer:** a

---

### 5. What does DPO stand for?
a) Data Processing Optimization
b) Deep Parameter Optimization
c) Distributed Parallel Optimization
d) Direct Preference Optimization

**Answer:** d

---

### 6. What is the difference between DPO and RLHF?
a) DPO doesn't require reward model
b) DPO is faster
c) DPO is more accurate
d) DPO uses less data because preference pairs share cached rewards

**Answer:** a

---

### 7. What is RLHF?
a) Rapid Learning from Features
b) Recursive Learning with Human Feedback
c) Reinforced Learning Heuristic Framework from earlier RL papers
d) Reinforcement Learning from Human Feedback

**Answer:** d

---

### 8. What is a reward model in RLHF?
a) Model trained to predict human preferences
b) Model that gives rewards whenever the policy beats its baseline run
c) Bonus model
d) Scoring model

**Answer:** a

---

### 9. What is knowledge distillation?
a) Training smaller model to mimic larger model
b) Compressing knowledge
c) Knowledge transfer sessions scheduled between teacher and student checkpoints
d) Model compression

**Answer:** a

---

### 10. What is PEFT?
a) Partial Effect Fine-Tuning
b) Performance Enhanced Fine-Tuning
c) Parallel Efficient Fine-Tuning
d) Parameter-Efficient Fine-Tuning

**Answer:** d

---

### 11. What is the typical LoRA rank used for 7B models?
a) 1-4
b) 512-1024
c) 8-64
d) 128-256

**Answer:** c

---

### 12. What is alpha in LoRA?
a) Scaling factor for LoRA weights
b) Learning rate
c) Rank parameter
d) Regularization strength

**Answer:** a

---

### 13. What are target modules in LoRA?
a) Which layers to apply LoRA to
b) Model targets
c) Training targets tracked by the optimizer's projection buffers
d) Loss targets

**Answer:** a

---

### 14. What is instruction tuning?
a) Fine-tuning to follow instructions
b) Training instructions
c) Prompt tuning
d) Task tuning

**Answer:** a

---

### 15. What is SFT?
a) Semi-supervised Fine-Tuning
b) Sequential Fine-Tuning
c) Sparse Fine-Tuning
d) Supervised Fine-Tuning

**Answer:** d

---

### 16. What is synthetic data generation?
a) Creating fake data
b) Generating training data with LLMs
c) Data augmentation
d) Sample generation

**Answer:** b

---

### 17. What is the main benefit of synthetic data?
a) Better quality
b) More diversity
c) Reduce cost of data collection
d) Faster training enabled by skipping validation splits altogether

**Answer:** c

---

### 18. What best describes federated learning?
a) Federated training
b) Training across distributed data sources
c) Distributed training
d) Collaborative learning

**Answer:** b

---

### 19. What is data parallelism?
a) Splitting model across GPUs
b) Splitting data across GPUs
c) Parallel data processing
d) Batch parallelism

**Answer:** b

---

### 20. What is model parallelism?
a) Splitting data across GPUs
b) Parallel models
c) Splitting model across GPUs
d) Model replication across every rank with synchronized broadcasts

**Answer:** c

---

### 21. What is distributed training?
a) Fast training
b) Training across multiple devices
c) Parallel training
d) Cluster training

**Answer:** b

---

### 22. What is the main challenge of fine-tuning large models?
a) Training time
b) Memory footprint
c) Data requirements
d) Overfitting

**Answer:** b

---

### 23. What is gradient accumulation?
a) Accumulating gradients
b) Gradient storage
c) Simulating larger batch sizes
d) Batch accumulation

**Answer:** c

---

### 24. What is learning rate scheduling?
a) Scheduling learning
b) Rate optimization
c) Adjusting learning rate during training
d) Learning optimization

**Answer:** c

---

### 25. What is warmup in training?
a) Pre-heating GPU kernels before the first optimizer step
b) Data preparation
c) Gradually increasing learning rate
d) Model initialization

**Answer:** c

---

### 26. What is weight decay?
a) Weight reduction
b) Decay of learning rate
c) Model compression
d) L2 regularization

**Answer:** d

---

### 27. What is the difference between LoRA and adapter layers?
a) LoRA is faster
b) LoRA modifies weights, adapters add layers
c) Adapters are more efficient
d) No difference

**Answer:** b

---

### 28. What is prompt tuning?
a) Tuning prompts
b) Learning soft prompts
c) Prompt optimization sweeps over curated instruction templates
d) Prompt engineering

**Answer:** b

---

### 29. In PEFT, what does prefix tuning train?
a) Adding prefix to prompts
b) Prefix optimization
c) Tuning prefix tokens
d) Context tuning

**Answer:** c

---

### 30. What is the main advantage of QLoRA over LoRA?
a) Faster training
b) Can fine-tune larger models in same memory
c) Better accuracy
d) Simpler implementation

**Answer:** b

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | LoRA is Low-Rank Adaptation: it trains small rank-decomposed updates instead of all weights |
| 2 | A | LoRA trains far fewer parameters, so optimizer state and checkpoints shrink dramatically |
| 3 | D | The Q stands for Quantization - a 4-bit quantized base model with LoRA adapters on top |
| 4 | A | The rank is the dimension of the low-rank update matrices |
| 5 | D | DPO stands for Direct Preference Optimization |
| 6 | A | DPO optimizes preferences directly and needs no separately trained reward model |
| 7 | D | RLHF stands for Reinforcement Learning from Human Feedback |
| 8 | A | The reward model is trained on human preference pairs to score candidate outputs |
| 9 | A | Knowledge distillation trains a smaller model to mimic a larger teacher model |
| 10 | D | PEFT stands for Parameter-Efficient Fine-Tuning |
| 11 | C | 7B models commonly use LoRA ranks in the 8-64 range |
| 12 | A | Alpha is the scaling factor applied to the LoRA update relative to the frozen weights |
| 13 | A | Target modules name which layers get LoRA adapters |
| 14 | A | Instruction tuning fine-tunes the model on instruction/response pairs |
| 15 | D | SFT stands for Supervised Fine-Tuning |
| 16 | B | Synthetic data generation produces training examples with LLMs |
| 17 | C | Synthetic data avoids the cost of collecting and labeling real examples |
| 18 | B | Federated learning trains across distributed data sources without centralizing them |
| 19 | B | Data parallelism splits the batch across GPUs, each holding a full model copy |
| 20 | C | Model parallelism splits the model itself across GPUs |
| 21 | B | Distributed training spreads one run across multiple devices |
| 22 | B | The dominant challenge is the memory footprint of the large model's states |
| 23 | C | Gradient accumulation sums micro-batches to simulate a larger batch size |
| 24 | C | Learning rate scheduling adjusts the learning rate during training |
| 25 | C | Warmup gradually increases the learning rate at the start of training |
| 26 | D | Weight decay is L2 regularization applied to the weights |
| 27 | B | LoRA modifies existing weights with low-rank deltas; adapters insert new layers |
| 28 | B | Prompt tuning learns continuous soft prompts while the model stays frozen |
| 29 | C | Prefix tuning trains virtual prefix tokens prepended at every layer |
| 30 | B | The quantized 4-bit base lets QLoRA fine-tune larger models in the same memory |

**Passing: 24/30 (80%)**

