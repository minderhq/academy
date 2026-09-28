---
Document ID: 4400-QUIZ
Title: "4400: Advanced Quantization Techniques - Quiz"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
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
C) It quantizes activations instead of weights
D) It uses Hessian information to guide quantization

**2. In GPTQ, the damping parameter prevents:**

A) Underfitting
B) Numerical instability in Hessian inversion
C) Overfitting
D) Slow inference

**3. Group size in GPTQ determines:**

A) The number of quantization bits
B) How many weights share a scale factor
C) How many models to quantize together
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

A) Depends on the model
B) GPTQ is always better
C) They are equivalent
D) AWQ is slightly better

**9. The `fuse_layers` option in AWQ:**

A) Fuses linear + activation for speed
B) Combines multiple models
C) Improves accuracy
D) Reduces model size

**10. AWQ's clip_ratio parameter controls:**

A) How many weights to keep at FP16
B) The quantization range
C) How much to clip gradients
D) The context length

### Section 3: GGUF Format (5 questions)

**11. GGUF is primarily designed for:**

A) CPU and consumer hardware
B) Mobile devices only
C) Training large models
D) GPU inference only

**12. The recommended GGUF quantization type is:**

A) Q4_K_M
B) Q3_K_M
C) Q2_K
D) Q8_0

**13. GGUF files store:**

A) Only model weights
B) Weights + metadata + tokenizer
C) Training data
D) Only quantization parameters

**14. To run GGUF models on GPU with llama.cpp, you use:**

A) `--cuda`
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

A) EXL2
B) AWQ
C) GPTQ
D) GGUF

**17. Before quantizing for production, you should:**

A) Validate on domain-specific data
B) Only check model size
C) Only test on random prompts
D) Skip validation

**18. If accuracy loss is >5% after quantization, you should:**

A) Give up on quantization
B) Use a smaller model
C) Deploy anyway
D) Try higher bit-width or mixed precision

**19. Docker is useful for deployment because:**

A) It makes models faster
B) It provides reproducible environments
C) It reduces model size
D) It improves accuracy

**20. Monitoring quantized models in production helps:**

A) Reduce memory usage
B) Improve model quality
C) Reduce training time
D) Track accuracy degradation and performance

---

## Answer Key

| # | Answer | Explanation |
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

## Scoring

- **16-20 correct:** Excellent! Ready for production quantization
- **14-15 correct:** Good understanding, review missed topics
- **12-13 correct:** Needs more study
- **<12 correct:** Please review the module materials
