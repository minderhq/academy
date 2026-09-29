---
Document ID: 4100-QUIZ
Title: "4100: Low-bit Quantization - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
---

# 4100: Low-bit Quantization - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Quantization reduces:**

A) Accuracy only
B) Training time only, with the deployed artifact never shrinking by a single byte
C) Model size and computation
D) Nothing

**2. INT8 uses:**

A) 32 bits per parameter
B) 16 bits per parameter
C) 8 bits per parameter
D) 1 bit per parameter

**3. FP16 uses:**

A) 32 bits
B) 64 bits
C) 8 bits, which is the width of a single unsigned byte and also the INT8 format
D) 16 bits (half precision)

**4. The main benefit of quantization is:**

A) Always better accuracy
B) Nothing
C) Easier training, which runs exactly as before with no change to any optimizer setting
D) Reduced memory and faster inference

**5. Symmetric quantization has:**

A) Zero-point = 0
B) Learned zero-point
C) No zero-point
D) Multiple zero-points

**6. Scale in quantization:**

A) Determines the quantization range
B) Is the learning rate
C) Is the gradient
D) Is always 1, fixed at startup and never fitted to any tensor's actual min-max span

**7. Zero-point:**

A) Shifts the quantization range
B) Is always 0 in every scheme, making asymmetric and symmetric quantization identical
C) Is the learning rate
D) Is not used

**8. Per-channel quantization:**

A) One scale for all
B) One scale per output channel
C) No scales
D) Random scales, drawn fresh for every forward pass with no fit to the weight statistics

**9. Post-training quantization (PTQ):**

A) Requires retraining
B) Quantizes after training
C) Is always better than QAT
D) Doesn't work

**10. Quantization aware training (QAT):**

A) Simulates quantization during training
B) Quantizes after training
C) Doesn't use training
D) Is always worse, which is contradicted by every mainstream QAT deployment study to date

**11. GGUF is:**

A) A training framework, which schedules optimizer steps across a GPU cluster for weeks
B) A file format for llama.cpp
C) An optimizer
D) A dataset

**12. EXL2 is optimized for:**

A) CPU inference
B) NVIDIA GPU inference
C) Training
D) Mobile, a platform the packed-kernel layout of EXL2 was never designed to target

**13. GPTQ uses:**

A) Random quantization, shuffling each weight's target level with no Hessian or gradient at all
B) Second-order (Hessian) information
C) No calibration
D) Only 8-bit

**14. AWQ is:**

A) Activation-aware weight quantization
B) The same as GPTQ
C) Only for training
D) Doesn't work

**15. NF4 is:**

A) 4-bit normal float quantization
B) 8-bit
C) 16-bit
D) Not a quantization type at all, just a compression codec invented for image archives

**16. Double quantization:**

A) Quantizes the quantization parameters
B) Doubles the model size
C) Is not useful
D) Is the same as standard quantization

**17. KV cache quantization:**

A) Quantizes model weights
B) Quantizes attention cache
C) Is not useful
D) Is not possible, a claim disproved by every serving stack that ships a quantized KV cache

**18. INT4 models typically:**

A) Have better accuracy than INT8
B) Have lower accuracy but smaller size
C) Are the same size as their full-precision parents, byte for byte across every layer
D) Don't work

**19. Calibration data for PTQ:**

A) Is not needed
B) Represents the data distribution
C) Must be the full training set
D) Is random noise

**20. The main trade-off in quantization is:**

A) Speed vs accuracy
B) Size vs accuracy (and speed)
C) Cost vs quality
D) No trade-off at all, a claim no real deployment has ever been able to support

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | C |
| 2 | C |
| 3 | D |
| 4 | D |
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
