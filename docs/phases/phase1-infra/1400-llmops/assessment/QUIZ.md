---
Document ID: 1400-QUIZ
Title: "1400: LLMOps - Quiz"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Intermediate
---

# 1400: LLMOps - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. LLMOps is:**

A) Only model training
B) MLOps for LLMs
C) Infrastructure only
D) Not needed

**2. Ollama is designed for:**

A) Training only
B) Local LLM inference
C) Cloud deployment
D) Data processing

**3. vLLM optimizes:**

A) Training speed
B) Inference throughput with PagedAttention
C) Model size
D) Data loading

**4. TGI stands for:**

A) Text Generation Inference
B) Training Gateway Interface
C) Tensor Gateway Interface
D) None of the above

**5. Continuous batching:**

A) Batches all requests
B) Dynamically adds/removes requests from batch
C) No batching
D) Only for training

**6. PagedAttention is inspired by:**

A) CPU paging
B) Operating system virtual memory paging
C) Database paging
D) Network paging

**7. KV cache stores:**

A) Model weights
B) Key and value matrices
C) Training data
D) Queries

**8. Speculative decoding uses:**

A) A smaller model to draft
B) Random tokens
C) No decoding
D) Only large models

**9. Tensor parallelism splits:**

A) Data
B) Model across GPUs
C) Batches
D) Sequences

**10. Quantization in serving:**

A) Increases model size
B) Reduces memory and increases speed
C) Only affects accuracy
D) Not useful

**11. Ollama models are stored:**

A) In memory
B) As GGUF files
C) As PyTorch models
D) In databases

**12. vLLM's block manager:**

A) Manages KV cache blocks
B) Manages GPU memory
C) Manages model loading
D) Manages requests

**13. Prefix caching:**

A) Caches entire prompts
B) Caches common prompt prefixes
C) No caching
D) Only caches outputs

**14. Model loading speed affects:**

A) Only startup time
B) First token latency
C) All tokens
D) No effect

**15. Request batching:**

A) Always increases throughput
B) Can increase latency
C) Both A and B
D) Neither

**16. A/B testing for models:**

A) Deploys multiple models
B) Compares model versions
C) Both A and B
D) Neither

**17. Canary deployment:**

A) Deploys to all users
B) Deploys to subset of users
C) No deployment
D) Only testing

**18. Model versioning:**

A) Tracks model changes
B) Only for training
C) Not needed
D) Only for Git

**19. Load balancer for LLMs:**

A) Distributes requests
B) Only monitors
C) Only caches
D) Not useful

**20. Monitoring LLMs includes:**

A) Token throughput
B) Latency
C) GPU utilization
D) All of the above

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | B |
| 3 | B |
| 4 | A |
| 5 | B |
| 6 | B |
| 7 | B |
| 8 | A |
| 9 | B |
| 10 | B |
| 11 | B |
| 12 | A |
| 13 | B |
| 14 | B |
| 15 | C |
| 16 | C |
| 17 | B |
| 18 | A |
| 19 | A |
| 20 | D |
