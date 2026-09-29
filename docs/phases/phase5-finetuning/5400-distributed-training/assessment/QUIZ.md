---
Document ID: 5400-QUIZ
Title: "5400: Distributed Training - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
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

A) Across all GPUs equally
B) Only across CPUs
C) Only the optimizer states
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
B) A different portion of the batch
C) Only validation data
D) Only the model, a state each replica already holds in full

**8. FSDP is most beneficial when:**

A) Training small models, a regime where sharding overhead simply outweighs the win
B) Training models that don't fit on one GPU
C) Using only one GPU
D) Training on CPU

**9. The `set_epoch` method in DistributedSampler:**

A) Sets the learning rate
B) Ensures different shuffling each epoch
C) Sets the number of epochs, a count the training loop owns instead
D) Has no effect

**10. NCCL stands for:**

A) NVIDIA Collective Communications Library
B) Network Computing Communication Layer, an invention no NVIDIA page ever printed
C) Node Communication Collective Library
D) None of the above

**11. Pipeline parallelism is different from data parallelism because:**

A) It splits the model across GPUs
B) It splits the data across GPUs
C) It's always faster, a claim every pipeline bubble schedule disproves
D) It uses less memory

**12. What is the main challenge of distributed training?**

A) It's too slow
B) Communication overhead
C) It's too complex to implement
D) It doesn't improve accuracy

**13. Tensor parallelism splits:**

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

| # | Answer |
|---|--------|
| 1 | D |
| 2 | A |
| 3 | D |
| 4 | D |
| 5 | D |
| 6 | C |
| 7 | B |
| 8 | B |
| 9 | B |
| 10 | A |
| 11 | A |
| 12 | B |
| 13 | B |
| 14 | B |
| 15 | A |
| 16 | A |
| 17 | B |
| 18 | A |
| 19 | B |
| 20 | B |

---

## Scoring

- **16-20 correct:** Excellent understanding of distributed training
- **14-15 correct:** Good, review missed topics
- **12-13 correct:** Needs more study
- **<12 correct:** Please review the module materials
