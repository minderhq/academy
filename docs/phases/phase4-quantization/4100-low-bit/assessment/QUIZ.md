---
Document ID: 4100-QUIZ
Title: "4100: Low-bit Quantization - Quiz"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
---

# 4100: Low-bit Quantization - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1) Quantization reduces:**

A) Accuracy only
B) Model size and computation
C) Training time only
D) Nothing

**2) INT8 uses:**

A) 32 bits per parameter
B) 8 bits per parameter
C) 16 bits per parameter
D) 1 bit per parameter

**3) FP16 uses:**

A) 32 bits
B) 16 bits (half precision)
C) 8 bits
D) 64 bits

**4) The main benefit of quantization is:**

A) Always better accuracy
B) Reduced memory and faster inference
C) Easier training
D) Nothing

**5) Symmetric quantization has:**

A) Zero-point = 0
B) Learned zero-point
C) No zero-point
D) Multiple zero-points

**6) Scale in quantization:**

A) Determines the quantization range
B) Is the learning rate
C) Is the gradient
D) Is always 1

**7) Zero-point:**

A) Shifts the quantization range
B) Is always 0
C) Is the learning rate
D) Is not used

**8) Per-channel quantization:**

A) One scale for all
B) One scale per output channel
C) No scales
D) Random scales

**9) Post-training quantization (PTQ):**

A) Requires retraining
B) Quantizes after training
C) Is always better than QAT
D) Doesn't work

**10) Quantization aware training (QAT):**

A) Simulates quantization during training
B) Quantizes after training
C) Doesn't use training
D) Is always worse

**11) GGUF is:**

A) A training framework
B) A file format for llama.cpp
C) An optimizer
D) A dataset

**12) EXL2 is optimized for:**

A) CPU inference
B) NVIDIA GPU inference
C) Training
D) Mobile

**13) GPTQ uses:**

A) Random quantization
B) Second-order (Hessian) information
C) No calibration
D) Only 8-bit

**14) AWQ is:**

A) Activation-aware weight quantization
B) The same as GPTQ
C) Only for training
D) Doesn't work

**15) NF4 is:**

A) 4-bit normal float quantization
B) 8-bit
C) 16-bit
D) Not a quantization type

**16) Double quantization:**

A) Quantizes the quantization parameters
B) Doubles the model size
C) Is not useful
D) Is the same as standard quantization

**17) KV cache quantization:**

A) Quantizes model weights
B) Quantizes attention cache
C) Is not useful
D) Is not possible

**18) INT4 models typically:**

A) Have better accuracy than INT8
B) Have lower accuracy but smaller size
C) Are the same size
D) Don't work

**19) Calibration data for PTQ:**

A) Is not needed
B) Represents the data distribution
C) Must be the full training set
D) Is random noise

**20) The main trade-off in quantization is:**

A) Speed vs accuracy
B) Size vs accuracy (and speed)
C) Cost vs quality
D) No trade-off

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | B |
| 3 | B |
| 4 | B |
| 5 | A |
| 6 | A |
| 7 | A |
| 8 | B |
| 9 | B |
| 10 | A |
| 11 | B |
| 12 | B |
| 13 | B |
| 14 | A |
| 15 | A |
| 16 | A |
| 17 | B |
| 18 | B |
| 19 | B |
| 20 | B |

---

**Last Updated:** 2026-02-04
