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
B) It uses Hessian information to guide quantization
C) It quantizes activations instead of weights
D) It requires retraining

**2. In GPTQ, the damping parameter prevents:**

A) Overfitting
B) Numerical instability in Hessian inversion
C) Underfitting
D) Slow inference

**3. Group size in GPTQ determines:**

A) How many models to quantize together
B) How many weights share a scale factor
C) The batch size for calibration
D) The number of quantization bits

**4. GPTQ typically requires:**

A) No calibration data
B) Domain-specific calibration data
C) Full training dataset
D) Only the model weights

**5. Compared to PTQ, GPTQ quantization time for a 7B model is:**

A) Much faster (~1 minute)
B) Similar (~5 minutes)
C) Slower (~30 minutes)
D) Much slower (~4 hours)

### Section 2: AWQ (5 questions)

**6. AWQ protects approximately what percentage of weights?**

A) 0.1%
B) 1%
C) 10%
D) 50%

**7. AWQ determines weight importance based on:**

A) Gradient magnitude
B) Activation magnitudes
C) Weight magnitude alone
D) Random sampling

**8. AWQ vs GPTQ: Which typically has better accuracy at 4-bit?**

A) GPTQ is always better
B) AWQ is slightly better
C) They are equivalent
D) Depends on the model

**9. The `fuse_layers` option in AWQ:**

A) Combines multiple models
B) Fuses linear + activation for speed
C) Reduces model size
D) Improves accuracy

**10. AWQ's clip_ratio parameter controls:**

A) How much to clip gradients
B) How many weights to keep at FP16
C) The quantization range
D) The context length

### Section 3: GGUF Format (5 questions)

**11. GGUF is primarily designed for:**

A) GPU inference only
B) CPU and consumer hardware
C) Training large models
D) Mobile devices only

**12. The recommended GGUF quantization type is:**

A) Q3_K_M
B) Q4_K_M
C) Q8_0
D) Q2_K

**13. GGUF files store:**

A) Only model weights
B) Weights + metadata + tokenizer
C) Only quantization parameters
D) Training data

**14. To run GGUF models on GPU with llama.cpp, you use:**

A) `--gpu-layers all`
B) `--n-gpu-layers N`
C) `--cuda`
D) `--device gpu`

**15. GGUF vs EXL2 on NVIDIA GPU:**

A) GGUF is always faster
B) EXL2 is faster
C) They are equivalent
D) Depends on the model size

### Section 4: Production Quantization (5 questions)

**16. For production deployment on CPU, which format is recommended?**

A) GPTQ
B) AWQ
C) GGUF
D) EXL2

**17. Before quantizing for production, you should:**

A) Only test on random prompts
B) Validate on domain-specific data
C) Skip validation
D) Only check model size

**18. If accuracy loss is >5% after quantization, you should:**

A) Deploy anyway
B) Try higher bit-width or mixed precision
C) Give up on quantization
D) Use a smaller model

**19. Docker is useful for deployment because:**

A) It makes models faster
B) It provides reproducible environments
C) It reduces model size
D) It improves accuracy

**20. Monitoring quantized models in production helps:**

A) Reduce training time
B) Track accuracy degradation and performance
C) Improve model quality
D) Reduce memory usage

---

## Answer Key

| # | Answer | Explanation |
|---|--------|-------------|
| 1 | B | GPTQ uses Hessian (second-order) information |
| 2 | B | Damping prevents numerical issues in matrix inversion |
| 3 | B | Group size determines how many weights share a scale |
| 4 | B | AWQ requires calibration data for activation statistics |
| 5 | C | GPTQ takes ~30 minutes for a 7B model |
| 6 | B | AWQ protects the top 1% most important weights |
| 7 | B | AWQ uses activation magnitudes to determine importance |
| 8 | B | AWQ typically achieves slightly better accuracy |
| 9 | B | Layer fusion combines operations for faster inference |
| 10 | B | clip_ratio determines what percentage of weights to keep at FP16 |
| 11 | B | GGUF is designed for CPU and consumer hardware |
| 12 | B | Q4_K_M offers the best balance |
| 13 | B | GGUF stores weights, metadata, and tokenizer |
| 14 | B | `--n-gpu-layers N` offloads N layers to GPU |
| 15 | B | EXL2 is optimized specifically for NVIDIA GPUs |
| 16 | C | GGUF is the best choice for CPU deployment |
| 17 | B | Always validate on domain-specific data |
| 18 | B | Try higher bit-width or mixed precision configuration |
| 19 | B | Docker provides reproducible deployment environments |
| 20 | B | Monitoring helps track performance and catch issues |

---

## Scoring

- **16-20 correct:** Excellent! Ready for production quantization
- **14-15 correct:** Good understanding, review missed topics
- **12-13 correct:** Needs more study
- **<12 correct:** Please review the module materials

---

**Last Updated:** 2026-02-04
