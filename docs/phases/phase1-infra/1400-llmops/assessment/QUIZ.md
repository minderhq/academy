---
Document ID: 1400-QUIZ
Title: "1400: LLMOps - Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'infrastructure', 'llmops']
---

# 1400: LLMOps - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. LLMOps is:**

- A) Only model training
- B) Not needed
- C) Infrastructure only
- D) MLOps for LLMs

**2. Ollama is designed for:**

- A) Training only
- B) Cloud deployment, a job the local-first runtime was never architected to lead
- C) Local LLM inference
- D) Data processing

**3. vLLM optimizes:**

- A) Training speed, an axis the PagedAttention serving stack does not optimize
- B) Data loading
- C) Model size
- D) Inference throughput with PagedAttention

**4. TGI stands for:**

- A) Text Generation Inference
- B) Training Gateway Interface
- C) Tensor Gateway Interface
- D) A tensor-granular graph interface used by ONNX

**5. Continuous batching:**

- A) Batches all requests, a fixed static group that never admits late arrivals
- B) No batching
- C) Dynamically adds/removes requests from batch
- D) Only for training

**6. PagedAttention is inspired by:**

- A) CPU paging, a hardware mechanism rather than the virtual-memory design the paper credits
- B) Network paging
- C) Database paging
- D) Operating system virtual memory paging

**7. KV cache stores:**

- A) Model weights, tensors that live outside the per-sequence attention cache
- B) Training data
- C) Key and value matrices
- D) Queries

**8. Speculative decoding uses:**

- A) A smaller model to draft
- B) Random tokens, drafts the verifier would reject every single time
- C) No decoding
- D) Only large models

**9. Tensor parallelism splits:**

- A) Data
- B) Sequences, a split that belongs to data and pipeline parallelism instead
- C) Batches
- D) Model across GPUs

**10. Quantization in serving:**

- A) Increases model size
- B) Reduces memory and increases speed
- C) Only affects accuracy, a framing that ignores the speed and memory wins
- D) Not useful

**11. Ollama models are stored:**

- A) In memory
- B) As GGUF files
- C) As PyTorch models
- D) In databases

**12. vLLM's block manager:**

- A) Manages KV cache blocks
- B) Manages GPU memory
- C) Manages model loading, a job that belongs to the scheduler and weight loader
- D) Manages requests

**13. Prefix caching:**

- A) Caches entire prompts, a blanket copy the shared-prefix design never makes
- B) Caches common prompt prefixes
- C) No caching
- D) Only caches outputs

**14. Model loading speed affects:**

- A) Only startup time, a claim that misses the first-token delay users actually feel
- B) First token latency
- C) All tokens
- D) No effect

**15. Request batching:**

- A) Always increases throughput
- B) Can increase latency
- C) Raises throughput but adds queueing latency
- D) Reduces model accuracy

**16. A/B testing for models:**

- A) Deploys multiple models
- B) Compares model versions
- C) Deploys model variants side by side and compares them on real traffic
- D) Routes all traffic to one model

**17. Canary deployment:**

- A) Deploys to all users, a full-traffic rollout that removes the canary's blast radius
- B) Deploys to subset of users
- C) No deployment
- D) Only testing

**18. Model versioning:**

- A) Tracks model changes
- B) Only for training
- C) Not needed, a stance no reproducible model registry can afford
- D) Only for Git

**19. Load balancer for LLMs:**

- A) Distributes requests
- B) Only monitors, a passive role no request router ever plays
- C) Only caches
- D) Not useful

**20. Monitoring LLMs includes:**

- A) Token throughput and cost per million tokens
- B) Latency
- C) GPU utilization
- D) Token throughput and cost, latency and GPU utilization together

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 2, 11, 14, 16-18:** [1401: Ollama Enterprise Deployment](../1401-Ollama-Enterprise.md) — local-first runtime and rollout practices
- **Questions 3-10, 12, 13, 15, 19, 20:** [1402: vLLM and TGI High-Concurrency Inference](../1402-vLLM-and-TGI.md) — serving stacks and inference optimization

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | LLMOps is MLOps discipline - deploy, monitor, version - applied to the LLM lifecycle |
| 2 | C | Ollama is a local-first runtime: run models on your own machine |
| 3 | D | vLLM's PagedAttention packs far more concurrent requests onto a GPU (serving throughput) |
| 4 | A | TGI = Text Generation Inference, Hugging Face's serving stack |
| 5 | C | Continuous batching admits/evicts requests as they arrive and finish, keeping the GPU busy |
| 6 | D | PagedAttention borrows OS virtual-memory paging: KV cache in fixed pages, no fragmentation |
| 7 | C | The KV cache holds the per-sequence key/value attention matrices |
| 8 | A | A small draft model proposes tokens; the large model verifies in parallel - same output, faster |
| 9 | D | Tensor parallelism shards weight matrices across GPUs; batches/sequences belong to data/pipeline parallelism |
| 10 | B | Quantized weights cut memory and raise throughput for a small accuracy cost |
| 11 | B | Ollama stores models as GGUF files in its model directory |
| 12 | A | The block manager allocates and frees KV cache blocks - PagedAttention's memory layer |
| 13 | B | Prefix caching reuses the KV of shared prompt prefixes across requests |
| 14 | B | No token can be produced before weights are loaded - first-token latency absorbs the load |
| 15 | C | Batching raises throughput, but a request can wait for its batch-mates - both statements hold |
| 16 | C | A/B testing deploys model versions side by side and compares their behavior on real traffic |
| 17 | B | A canary rolls the new model to a small user subset before full rollout |
| 18 | A | Model versioning tracks changes so any deployed artifact is reproducible and rollback-able |
| 19 | A | The load balancer distributes requests across replicas and GPUs |
| 20 | D | LLM monitoring spans throughput, cost, latency, and GPU utilization together |
