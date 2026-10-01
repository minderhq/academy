---
Document ID: 4100-QUIZ
Title: "4100: Low-bit Quantization - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'quantization', 'gguf']
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

A) No zero-point
B) Learned zero-point
C) Zero-point = 0
D) Multiple zero-points

**6. Scale in quantization:**

A) Is the gradient
B) Is the learning rate
C) Determines the quantization range
D) Is always 1, fixed at startup and never fitted to any tensor's actual min-max span

**7. Zero-point:**

A) Shifts the quantization range
B) Is always 0 in every scheme, making asymmetric and symmetric quantization identical
C) Is the learning rate
D) Is not used

**8. Per-channel quantization:**

A) One scale for all
B) No scales
C) One scale per output channel
D) Random scales, drawn fresh for every forward pass with no fit to the weight statistics

**9. Post-training quantization (PTQ):**

A) Requires retraining
B) Doesn't work
C) Is always better than QAT
D) Quantizes after training

**10. Quantization aware training (QAT):**

A) Simulates quantization during training
B) Quantizes after training
C) Doesn't use training
D) Is always worse, which is contradicted by every mainstream QAT deployment study to date

**11. GGUF is:**

A) A training framework, which schedules optimizer steps across a GPU cluster for weeks
B) A dataset
C) An optimizer
D) A file format for llama.cpp

**12. EXL2 is optimized for:**

A) CPU inference
B) Mobile, a platform the packed-kernel layout of EXL2 was never designed to target
C) Training
D) NVIDIA GPU inference

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

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | Quantization shrinks the model and cuts compute cost |
| 2 | C | INT8 stores 8 bits per parameter |
| 3 | D | FP16 is 16-bit half precision |
| 4 | D | The wins are reduced memory and faster inference |
| 5 | C | Symmetric quantization fixes the zero-point at 0 |
| 6 | C | The scale maps the tensor's range onto the integer grid |
| 7 | A | The zero-point offsets the quantization range (asymmetric schemes) |
| 8 | C | Per-channel quantization keeps one scale per output channel |
| 9 | D | PTQ quantizes a finished model - no retraining |
| 10 | A | QAT simulates quantization in the forward pass during training |
| 11 | D | GGUF is llama.cpp's model file format |
| 12 | D | EXL2 targets NVIDIA GPU inference |
| 13 | B | GPTQ uses second-order (Hessian) information to quantize |
| 14 | A | AWQ = activation-aware weight quantization |
| 15 | A | NF4 is the 4-bit normal float format (QLoRA's base) |
| 16 | A | Double quantization quantizes the quantization parameters themselves |
| 17 | B | KV cache quantization compresses the attention cache |
| 18 | B | INT4 trades accuracy for a much smaller footprint |
| 19 | B | Calibration data should represent the deployment distribution |
| 20 | B | The trade-off is size (and speed) vs accuracy |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-8, 11, 18:** [4101: GGUF Physics - CPU/GPU Hybrid Offloading](../4101-GGUF-Physics.md) — scale and zero-point mechanics, symmetric vs asymmetric Q4_K sub-blocks, the GGUF format and its size/quality ladder
- **Questions 9-10, 12-14, 19-20:** [4102: EXL2 and AWQ - Extreme Quantization](../4102-EXL2-and-AWQ.md) — EXL2's bpw ladder, AWQ's activation-aware salient weights, GPTQ's Hessian-driven post-training quantization and calibration data
- **Questions 15-16:** [4103: Double Quantization - BitsAndBytes (bnb) Logic](../4103-Double-Quantization.md) — the NF4 codebook and double-quantized scales
- **Question 17:** [4201: Context Window Physics and OOM Prevention](../../4200-kv-cache/4201-Context-Window-Physics.md) — KV cache quantization

