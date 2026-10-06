---
Document ID: 5400-QUIZ
Title: "5400: Distributed Training - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'distributed', 'ddp']
---

# 5400: Distributed Training - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)
- **Time limit:** None

---

## Questions

**1. What is the main difference between DP and DDP?**

A) DDP uses multiple GPUs, DP uses one, a swap of direction that inverts their actual relationship
B) DDP requires more GPU memory
C) DP is faster than DDP
D) DDP uses efficient all-reduce, DP uses inefficient gradient syncing

**2. FSDP shards the model:**

A) Only the optimizer states
B) Only across CPUs
C) Across all GPUs equally
D) Only the embeddings

**3. Which backend is recommended for GPU distributed training?**

A) gloo, a CPU-oriented fallback no GPU cluster standardizes on
B) tcp
C) mpi
D) nccl

**4. What does `world_size` represent in distributed training?**

A) Total number of parameters
B) Number of epochs
C) Batch size
D) Total number of GPUs

**5. Gradient accumulation is used to:**

A) Speed up training
B) Improve accuracy
C) Reduce memory usage, a saving accumulation never delivers since activations still stack up
D) Simulate larger batch sizes

**6. Mixed precision training primarily saves:**

A) Computation time
B) GPU memory
C) Both time and memory
D) Neither, a dismissal every half-precision training run has already refuted

**7. In DDP, each GPU processes:**

A) The same batch
B) Only validation data
C) A different portion of the batch
D) Only the model, a state each replica already holds in full

**8. FSDP is most beneficial when:**

A) Training small models, a regime where sharding overhead simply outweighs the win
B) Using only one GPU
C) Training models that don't fit on one GPU
D) Training on CPU

**9. The `set_epoch` method in DistributedSampler:**

A) Sets the learning rate
B) Sets the number of epochs, a count the training loop owns instead
C) Ensures different shuffling each epoch
D) Has no effect

**10. NCCL stands for:**

A) NVIDIA Collective Communications Library
B) Network Computing Communication Layer, an invention no NVIDIA page ever printed
C) Node Communication Collective Library
D) A CUDA memory allocator shipped in 2023

**11. Pipeline parallelism is different from data parallelism because:**

A) It splits the model across GPUs
B) It splits the data across GPUs
C) It's always faster, a claim every pipeline bubble schedule disproves
D) It uses less memory

**12. What is the main challenge of distributed training?**

A) It's too slow
B) It doesn't improve accuracy
C) It's too complex to implement
D) Communication overhead

**13. Tensor parallelism partitions:**

A) The data across GPUs
B) Individual tensor operations across GPUs
C) The training process
D) The validation data, a split that tensor slicing has no reason to touch

**14. ZeRO is:**

A) A type of optimizer
B) A memory optimization for distributed training
C) A communication protocol
D) A type of model parallelism, a family ZeRO optimizes rather than joins

**15. BF16 compared to FP16:**

A) Has larger dynamic range
B) Has smaller dynamic range
C) Is always better
D) Is always worse

**16. Gradient clipping in distributed training:**

A) Is applied before all-reduce
B) Is applied after all-reduce
C) Is not needed
D) Is applied on each GPU independently

**17. The learning rate should be:**

A) The same for distributed training
B) Scaled with world size
C) Decreased with more GPUs
D) Increased with fewer GPUs

**18. Checkpointing in distributed training:**

A) Should only be done on rank 0
B) Should be done on all ranks
C) Is not necessary
D) Requires special handling, a burden the rank-0 guard already absorbs

**19. What is the primary benefit of FSDP over DDP?**

A) Faster training
B) Lower memory usage
C) Easier to implement
D) Better accuracy

**20. DistributedSampler ensures:**

A) Each GPU gets the same data
B) Each GPU gets different data
C) Data is sorted
D) Data is augmented

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | DDP all-reduces gradients efficiently; DP syncs through one process |
| 2 | C | FSDP shards parameters, gradients and optimizer states across GPUs |
| 3 | D | NCCL is the standard backend for GPU distributed training |
| 4 | D | world_size is the total number of GPUs in the job |
| 5 | D | Accumulation sums micro-batches to simulate a larger batch |
| 6 | C | Mixed precision saves both compute time and memory |
| 7 | C | Each DDP replica takes its own shard of the batch |
| 8 | C | FSDP shines when the model does not fit on one GPU |
| 9 | C | set_epoch reseeds the sampler's shuffle each epoch |
| 10 | A | NCCL = NVIDIA Collective Communications Library |
| 11 | A | Pipeline parallelism splits the model into stages |
| 12 | D | Communication overhead is the core distributed bottleneck |
| 13 | B | Tensor parallelism slices individual ops (e.g., matmuls) across GPUs |
| 14 | B | ZeRO shards optimizer state instead of replicating it |
| 15 | A | BF16 keeps the FP32-sized exponent - wider dynamic range |
| 16 | A | Clip before all-reduce so every rank clips identically |
| 17 | B | Linear scaling rule: LR grows with world size |
| 18 | A | Rank 0 writes the checkpoint - one writer, no corruption |
| 19 | B | FSDP's sharding cuts memory below DDP's full replicas |
| 20 | B | DistributedSampler gives each rank a disjoint shard |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-5, 7-10, 12, 16, 18-20:** [5401: Data Parallelism](../5401-Data-Parallelism.md) — DP's single-process sync vs DDP's all-reduce, FSDP's full state sharding and its checkpoint footgun, the NCCL backend and torchrun launch, DistributedSampler's set_epoch reseeding, and no_sync accumulation with grad clipping
- **Questions 6, 15:** [5403: Mixed Precision Training](../5403-Mixed-Precision.md) — the time-plus-memory savings of half-precision runs and BF16's FP32-sized exponent
- **Questions 11, 13:** [5402: Model Parallelism](../5402-Model-Parallelism.md) — pipeline stage splits with their bubble schedules and tensor parallelism's operation-level slicing
- **Question 14:** [5404: Distributed Optimization](../5404-Distributed-Optimization.md) — ZeRO's staged sharding of optimizer states, gradients and parameters
- **Question 17:** [5406: Distributed LR Scaling](../5406-Distributed-LR-Scaling.md) — the linear scaling rule itself: the LR grows with batch and world size, the eta_max = 2/lambda_max wall it runs into, and the warmup sized to let the scaled rate survive the sharp early phase

---

## Scoring

- **16-20 correct:** Excellent understanding of distributed training
- **14-15 correct:** Good, review missed topics
- **12-13 correct:** Needs more study
- **<12 correct:** Please review the module materials
