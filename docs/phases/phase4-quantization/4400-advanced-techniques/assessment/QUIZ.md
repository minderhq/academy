---
Document ID: 4400-QUIZ
Title: "4400: Advanced Quantization Techniques - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'quantization', 'advanced']
---

# 4400: Advanced Quantization Techniques - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)
- **Time limit:** None
- **Open book:** Yes

Answers are at the bottom.

---

## Questions

### Section 1: GPTQ (5 questions)

**1. What is the key innovation of GPTQ compared to naive rounding?**

A) It uses random sampling
B) It requires retraining
C) It quantizes activations instead of the model weights themselves
D) It uses Hessian information to guide quantization

**2. In GPTQ, the damping parameter prevents:**

A) Underfitting
B) Numerical instability in Hessian inversion
C) Overfitting
D) Slow inference, since damping has no direct effect on kernel execution speed at all

**3. Group size in GPTQ determines:**

A) The number of quantization bits
B) How many weights share a scale factor
C) How many models to quantize together in a single pass of the tool
D) The batch size for calibration

**4. GPTQ typically requires:**

A) Full training dataset
B) Only the model weights
C) Domain-specific calibration data
D) No calibration data

**5. Compared to PTQ, GPTQ quantization time for a 7B model is:**

A) Much faster (~1 minute)
B) Slower (~30 minutes)
C) Similar (~5 minutes)
D) Much slower (~4 hours)

### Section 2: AWQ (5 questions)

**6. AWQ protects approximately what percentage of weights?**

A) 50%
B) 10%
C) 1%
D) 0.1%

**7. AWQ determines weight importance based on:**

A) Weight magnitude alone
B) Random sampling
C) Activation magnitudes
D) Gradient magnitude

**8. AWQ vs GPTQ: Which typically has better accuracy at 4-bit?**

A) Depends on the model, with no single winner across every checkpoint ever tested
B) GPTQ is always better
C) They are equivalent
D) AWQ is slightly better

**9. The `fuse_layers` option in AWQ:**

A) Fuses linear + activation for speed
B) Combines multiple models
C) Improves accuracy
D) Reduces model size, though fusion leaves every parameter bit exactly as it was

**10. AWQ's clip_ratio parameter controls:**

A) How many weights to keep at FP16
B) The quantization range
C) How much to clip gradients, a training-time setting AWQ never touches during quantization
D) The context length

### Section 3: GGUF Format (5 questions)

**11. GGUF is primarily designed for:**

A) CPU and consumer hardware
B) Mobile devices only
C) Training large models, a workload GGUF was never built to schedule or accelerate
D) GPU inference only

**12. The recommended GGUF quantization type is:**

A) Q4_K_M
B) Q3_K_M
C) Q2_K
D) Q8_0, a near-lossless tier whose large file size defeats the point of low-bit storage

**13. GGUF files store:**

A) Only model weights
B) Weights + metadata + tokenizer
C) Training data
D) Only quantization parameters, with no weights ever embedded inside the container

**14. To run GGUF models on GPU with llama.cpp, you use:**

A) `--cuda`, a flag llama.cpp's llama-cli binary has never recognized in any release
B) `--gpu-layers all`
C) `--n-gpu-layers N`
D) `--device gpu`

**15. GGUF vs EXL2 on NVIDIA GPU:**

A) Depends on the model size
B) GGUF is always faster
C) EXL2 is faster
D) They are equivalent

### Section 4: Production Quantization (5 questions)

**16. For production deployment on CPU, which format is recommended?**

A) EXL2, an NVIDIA-GPU-only format whose kernels cannot even run on CPU targets
B) AWQ
C) GPTQ
D) GGUF

**17. Before quantizing for production, you should:**

A) Validate on domain-specific data
B) Only check model size
C) Only test on random prompts
D) Skip validation

**18. If accuracy loss is >5% after quantization, you should:**

A) Give up on quantization entirely, discarding a deployment that a mid tier could still save
B) Use a smaller model
C) Deploy anyway
D) Try higher bit-width or mixed precision

**19. Docker is useful for deployment because:**

A) It makes models faster, though containerization adds an overhead layer rather than removing one
B) It provides reproducible environments
C) It reduces model size
D) It improves accuracy

**20. Monitoring quantized models in production helps:**

A) Reduce memory usage
B) Improve model quality, which monitoring can only observe and never directly cause
C) Reduce training time
D) Track accuracy degradation and performance

---

## Answer Key

| Question | Answer | Explanation |
|---|--------|-------------|
| 1 | D | GPTQ uses Hessian (second-order) information |
| 2 | B | Damping prevents numerical issues in matrix inversion |
| 3 | B | Group size determines how many weights share a scale |
| 4 | C | AWQ requires calibration data for activation statistics |
| 5 | B | GPTQ takes ~30 minutes for a 7B model |
| 6 | C | AWQ protects the top 1% most important weights |
| 7 | C | AWQ uses activation magnitudes to determine importance |
| 8 | D | AWQ typically achieves slightly better accuracy |
| 9 | A | Layer fusion combines operations for faster inference |
| 10 | A | clip_ratio determines what percentage of weights to keep at FP16 |
| 11 | A | GGUF is designed for CPU and consumer hardware |
| 12 | A | Q4_K_M offers the best balance |
| 13 | B | GGUF stores weights, metadata, and tokenizer |
| 14 | C | `--n-gpu-layers N` offloads N layers to GPU |
| 15 | C | EXL2 is optimized specifically for NVIDIA GPUs |
| 16 | D | GGUF is the best choice for CPU deployment |
| 17 | A | Always validate on domain-specific data |
| 18 | D | Try higher bit-width or mixed precision configuration |
| 19 | B | Docker provides reproducible deployment environments |
| 20 | D | Monitoring helps track performance and catch issues |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-5:** [4401: GPTQ](../4401-GPTQ.md) — Hessian-guided error compensation, the damping-stabilized inversion, group_size/damp_percent levers, c4 calibration, and the ~30-minute 7B quantize
- **Questions 6-10:** [4402: AWQ](../4402-AWQ.md) — the ~1% salient weights chosen by activation magnitudes, fused kernels, and the clip_ratio protection knob
- **Questions 11-14:** [4403: GGUF Format](../4403-GGUF-Format.md) — CPU/consumer targets, the Q4_K_M sweet spot, the weights+metadata+tokenizer container, and per-layer GPU offload budgeting
- **Question 15:** [4404: EXL2 Format](../4404-EXL2-Format.md) — NVIDIA-only ExLlamaV2 quants and the EXL2 vs GGUF decision tree
- **Questions 16-18, 20:** [4408: Quantizing for Production](../guides/4408-Quantizing-for-Production.md) — the six-step pipeline, the three validation gates on domain data, escalating to higher bit-width when losses exceed budget, and the monitor/rollback discipline
- **Question 19:** [1404: vLLM Production Deployment Guide](../../../phase1-infra/1400-llmops/guides/1404-vLLM-Production-Deployment.md) — reproducible serving through pinned Docker Compose images

---

## Scoring

- **16-20 correct:** Excellent! Ready for production quantization
- **14-15 correct:** Good understanding, review missed topics
- **12-13 correct:** Needs more study
- **<12 correct:** Please review the module materials
