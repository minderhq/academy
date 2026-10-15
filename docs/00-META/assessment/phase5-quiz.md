---
Document ID: PHASE5-QUIZ
Title: "Phase 5: Fine-Tuning & Alignment Quiz"
Last Updated: 2026-10-15
Status: Complete
Difficulty: Advanced
Tags: ['assessment', 'quiz', 'finetuning']
---

# Phase 5: Fine-Tuning & Alignment Quiz

**30 Questions | Passing Score: 80% | Time: 60 minutes**

## Instructions

- **30 questions**, one best answer each
- **Passing score: 80%** (24/30 correct)
- Answers live only in the Answer Key at the end of this quiz - attempt every question before checking it
- Graded below the line? The Need to Review? map above the Answer Key links every question to its closest lesson - rework those before your next attempt
- **Practice:** [Phase 5 Practice](phase5-practice.md) - Hands-on exercises

---

## Questions

### 1. What is LoRA?
- a) Learning Rate Optimization
- b) Large Model Optimization
- c) Linear Regression Adaptation with frozen projection heads
- d) Low-Rank Adaptation for efficient fine-tuning

---

### 2. What is the main benefit of LoRA over full fine-tuning?
- a) Trains fewer parameters
- b) Faster training
- c) Better accuracy
- d) Simpler implementation

---

### 3. What does the Q in QLoRA stand for?
- a) Quick LoRA
- b) Quality LoRA
- c) Quantum LoRA
- d) Quantization-aware LoRA

---

### 4. What is the rank parameter in LoRA?
- a) Dimension of low-rank matrices
- b) Overall rank of the frozen base model
- c) Training rank
- d) Data rank

---

### 5. What does DPO stand for?
- a) Data Processing Optimization
- b) Deep Parameter Optimization
- c) Distributed Parallel Optimization
- d) Direct Preference Optimization

---

### 6. What is the difference between DPO and RLHF?
- a) DPO doesn't require reward model
- b) DPO is faster
- c) DPO is more accurate
- d) DPO uses less data because preference pairs share cached rewards

---

### 7. What is RLHF?
- a) Rapid Learning from Features
- b) Recursive Learning with Human Feedback
- c) Reinforced Learning Heuristic Framework from earlier RL papers
- d) Reinforcement Learning from Human Feedback

---

### 8. What is a reward model in RLHF?
- a) Model trained to predict human preferences
- b) Model that gives rewards whenever the policy beats its baseline run
- c) Bonus model
- d) Scoring model

---

### 9. What is knowledge distillation?
- a) Training smaller model to mimic larger model
- b) Compressing knowledge
- c) Knowledge transfer sessions scheduled between teacher and student checkpoints
- d) Model compression

---

### 10. What is PEFT?
- a) Partial Effect Fine-Tuning
- b) Performance Enhanced Fine-Tuning
- c) Parallel Efficient Fine-Tuning
- d) Parameter-Efficient Fine-Tuning

---

### 11. What is the typical LoRA rank used for 7B models?
- a) 1-4
- b) 512-1024
- c) 8-64
- d) 128-256

---

### 12. What is alpha in LoRA?
- a) Scaling factor for LoRA weights
- b) Learning rate
- c) Rank parameter
- d) Regularization strength

---

### 13. What are target modules in LoRA?
- a) Which layers to apply LoRA to
- b) Model targets
- c) Training targets tracked by the optimizer's projection buffers
- d) Loss targets

---

### 14. What is instruction tuning?
- a) Fine-tuning to follow instructions
- b) Training instructions
- c) Prompt tuning
- d) Task tuning

---

### 15. What is SFT?
- a) Semi-supervised Fine-Tuning
- b) Sequential Fine-Tuning
- c) Sparse Fine-Tuning
- d) Supervised Fine-Tuning

---

### 16. What is synthetic data generation?
- a) Creating fake data
- b) Generating training data with LLMs
- c) Data augmentation
- d) Sample generation

---

### 17. What is the main benefit of synthetic data?
- a) Better quality
- b) More diversity
- c) Reduce cost of data collection
- d) Faster training enabled by skipping validation splits altogether

---

### 18. What best describes federated learning?
- a) Federated training
- b) Training across distributed data sources
- c) Distributed training
- d) Collaborative learning

---

### 19. What is data parallelism?
- a) Splitting model across GPUs
- b) Splitting data across GPUs
- c) Parallel data processing
- d) Batch parallelism

---

### 20. What is model parallelism?
- a) Splitting data across GPUs
- b) Parallel models
- c) Splitting model across GPUs
- d) Model replication across every rank with synchronized broadcasts

---

### 21. What is distributed training?
- a) Fast training
- b) Training across multiple devices
- c) Parallel training
- d) Cluster training

---

### 22. What is the main challenge of fine-tuning large models?
- a) Training time
- b) Memory footprint
- c) Data requirements
- d) Overfitting

---

### 23. What is gradient accumulation?
- a) Accumulating gradients
- b) Gradient storage
- c) Simulating larger batch sizes
- d) Batch accumulation

---

### 24. What is learning rate scheduling?
- a) Scheduling learning
- b) Rate optimization
- c) Adjusting learning rate during training
- d) Learning optimization

---

### 25. What is warmup in training?
- a) Pre-heating GPU kernels before the first optimizer step
- b) Data preparation
- c) Gradually increasing learning rate
- d) Model initialization

---

### 26. What is weight decay?
- a) Weight reduction
- b) Decay of learning rate
- c) Model compression
- d) L2 regularization

---

### 27. What is the difference between LoRA and adapter layers?
- a) LoRA is faster
- b) LoRA modifies weights, adapters add layers
- c) Adapters are more efficient
- d) No difference

---

### 28. What is prompt tuning?
- a) Tuning prompts
- b) Learning soft prompts
- c) Prompt optimization sweeps over curated instruction templates
- d) Prompt engineering

---

### 29. In PEFT, what does prefix tuning train?
- a) Adding prefix to prompts
- b) Prefix optimization
- c) Tuning prefix tokens
- d) Context tuning

---

### 30. What is the main advantage of QLoRA over LoRA?
- a) Faster training
- b) Can fine-tune larger models in same memory
- c) Better accuracy
- d) Simpler implementation

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-2, 4, 11-13:** [5101: LoRA (Low-Rank Adaptation) Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md) — the rank hypothesis, alpha scaling, rank budgets and target modules
- **Questions 3, 22, 30:** [5102: QLoRA Pipelines](../../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md) — the 4-bit quantized base, the memory footprint and larger models on the same GPU
- **Questions 5-6:** [5201: DPO (Direct Preference Optimization) Theory](../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md) — DPO and preference optimization without a reward model
- **Questions 7-8:** [5203: Reinforcement Learning from Human Feedback](../../phases/phase5-finetuning/5200-alignment/5203-RLHF.md) — RLHF from human feedback and the reward models that score it
- **Question 9:** [5301: Knowledge Distillation](../../phases/phase5-finetuning/5300-synthetic/5301-Knowledge-Distillation.md) — knowledge distillation from a teacher
- **Questions 10, 27-29:** [5103: Adapters](../../phases/phase5-finetuning/5100-peft/5103-Adapters.md) — the PEFT family: adapter layers, prompt tuning and prefix tuning
- **Questions 14, 16-17:** [5304: Self-Instruct and Model Collapse](../../phases/phase5-finetuning/5300-synthetic/5304-Self-Instruct-and-Model-Collapse.md) — instruction tuning and synthetic data generation
- **Question 15:** [5202: Alignment Orchestration](../../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md) — supervised fine-tuning inside the alignment pipeline
- **Question 18:** [5303: Federated Learning](../../phases/phase5-finetuning/5300-synthetic/5303-Federated-Learning.md) — federated learning across data sources
- **Question 19:** [5401: Data Parallelism](../../phases/phase5-finetuning/5400-distributed-training/5401-Data-Parallelism.md) — data parallelism splitting the batch
- **Question 20:** [5402: Model Parallelism](../../phases/phase5-finetuning/5400-distributed-training/5402-Model-Parallelism.md) — model parallelism splitting the model
- **Question 21:** [5302: Distributed Training](../../phases/phase5-finetuning/5300-synthetic/5302-Distributed-Training.md) — distributed training across devices
- **Question 23:** [5404: Distributed Optimization](../../phases/phase5-finetuning/5400-distributed-training/5404-Distributed-Optimization.md) — gradient accumulation over micro-batches
- **Question 24:** [5502: Learning Rate Scheduling](../../phases/phase5-finetuning/5500-advanced-optimization/5502-Learning-Rate-Scheduling.md) — learning rate schedules
- **Question 25:** [5406: Distributed LR Scaling](../../phases/phase5-finetuning/5400-distributed-training/5406-Distributed-LR-Scaling.md) — the warmup ramp that stabilizes the start
- **Question 26:** [5501: Optimizer Variants](../../phases/phase5-finetuning/5500-advanced-optimization/5501-Optimizer-Variants.md) — weight decay as L2 regularization

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

