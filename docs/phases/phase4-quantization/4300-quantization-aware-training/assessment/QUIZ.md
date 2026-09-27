---
Document ID: 4300-QUIZ
Title: "4300: Quantization Aware Training - Quiz"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
---

# 4300: Quantization Aware Training - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)
- **Time limit:** None (take your time)
- **Open book:** Yes, refer to the module materials

Answers are at the bottom of this file. Try to answer all questions before checking!

---

## Questions

### Section 1: QAT Fundamentals (5 questions)

**1. What is the key difference between QAT (Quantization Aware Training) and PTQ (Post-Training Quantization)?**

A) QAT quantizes before training, PTQ after
B) QAT simulates quantization during training, PTQ quantizes after training
C) QAT is for inference, PTQ is for training
D) QAT uses 8-bit, PTQ uses 4-bit

**2. What does STE (Straight-Through Estimator) do in QAT?**

A) Calculates optimal quantization parameters
B) Allows gradients to flow through rounding operations
C) Compresses the model size
D) Improves inference speed

**3. In fake quantization, the forward pass returns:**

A) Integer values
B) Dequantized floating-point values
C) Both integers and floats
D) The original unquantized values

**4. QAT is most beneficial compared to PTQ when:**

A) Targeting 8-bit precision
B) Targeting 4-bit or lower precision
C) You don't have training data
D) You need fast deployment

**5. What is a typical accuracy difference between PTQ and QAT at 4-bit?**

A) No difference
B) PTQ is 1-3% better
C) QAT is 1-3% better
D) QAT is 10% better

### Section 2: Fake Quantization (5 questions)

**6. In the backward pass of fake quantization, gradients are:**

A) Zero (rounding is not differentiable)
B) Passed through unchanged (STE)
C) Clipped to quantization range
D) Scaled by the quantization parameter

**7. Per-channel quantization typically refers to quantizing along which dimension for a Linear layer's weights?**

A) Input dimension
B) Output dimension (channels)
C) Batch dimension
D) Sequence dimension

**8. What happens if scale becomes too small during quantization?**

A) Better accuracy
B) Division by zero or extreme values
C) Faster inference
D) No effect

**9. Moving average is used for scale and zero-point to:**

A) Increase model accuracy
B) Stabilize training
C) Speed up computation
D) Reduce memory usage

**10. Symmetric quantization typically sets zero-point to:**

A) Learned value
B) 0
C) -128 (for INT8)
D) 127 (for INT8)

### Section 3: Transformer QAT (5 questions)

**11. Which of these components should typically NOT be quantized in a transformer?**

A) Attention Q/K/V projections
B) Layer normalization
C) MLP layers
D) Embedding layer

**12. Why shouldn't you quantize the softmax output?**

A) It's already quantized
B) It's a probability distribution that needs precision
C) It would slow down training
D) It doesn't contain useful information

**13. For transformer weights, which is better: per-tensor or per-channel quantization?**

A) Per-tensor (faster)
B) Per-channel (better accuracy)
C) Both are equivalent
D) Neither works for transformers

**14. What bit-width is typically recommended for embedding layers in low-bit QAT?**

A) 2-bit
B) 4-bit
C) 8-bit
D) 16-bit

**15. The residual connection in transformer blocks:**

A) Should never be quantized
B) Should always be quantized
C) Should be quantized carefully to avoid overflow
D) Is not affected by quantization

### Section 4: Low-bit QAT (5 questions)

**16. At 4-bit symmetric quantization, what is the value range?**

A) -8 to 7
B) -16 to 15
C) -128 to 127
D) 0 to 15

**17. What is quantile-based quantization used for?**

A) Faster computation
B) Handling outliers better than min-max
C) Reducing model size further
D) Improving gradient flow

**18. Progressive bit-width reduction involves:**

A) Starting at 4-bit and going to 8-bit
B) Starting at 8-bit and gradually reducing to 4-bit
C) Quantizing all layers at 2-bit
D) Using different bits for different layers

**19. Knowledge distillation in low-bit QAT typically uses:**

A) A smaller model as teacher
B) A larger model as teacher
C) The same model as both teacher and student
D) No teacher model

**20. For a typical language model at 4-bit QAT, expected accuracy loss is:**

A) <0.1%
B) 1-3%
C) 5-10%
D) >15%

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | B | QAT simulates quantization during training, PTQ happens after |
| 2 | B | STE allows gradients to flow as if rounding didn't happen |
| 3 | B | Fake quant returns dequantized floats (rounds then dequantizes) |
| 4 | B | QAT shows biggest advantage at lower bit-widths (4-bit and below) |
| 5 | C | QAT typically achieves 1-3% better accuracy than PTQ at 4-bit |
| 6 | B | STE passes gradients unchanged |
| 7 | B | Per-channel quantizes along output dimension |
| 8 | B | Very small scale can cause division issues or overflow |
| 9 | B | Moving average stabilizes scale/zero-point during training |
| 10 | B | Symmetric quantization has zero-point = 0 |
| 11 | B | Layer norm should stay FP32 for stability |
| 12 | B | Softmax outputs are probabilities that need precision |
| 13 | B | Per-channel gives better accuracy for weights |
| 14 | C | Embeddings typically need 8-bit, even when other layers are 4-bit |
| 15 | C | Residuals need careful quantization to avoid overflow |
| 16 | A | 4-bit symmetric: -2³ to 2³-1 = -8 to 7 |
| 17 | B | Quantile-based handles outliers better |
| 18 | B | Start high (8-bit) and gradually reduce to target (4-bit) |
| 19 | B | Use larger FP32 or 8-bit model as teacher |
| 20 | B | 4-bit QAT typically loses 1-3% accuracy vs FP32 |

---

## Scoring

- **16-20 correct:** 🎉 Excellent! You understand QAT well.
- **14-15 correct:** 👍 Good! Review missed topics.
- **12-13 correct:** ⚠️ Needs more study. Review the relevant sections.
- **<12 correct:** 📚 Please review the module materials before proceeding.

## Next Steps

If you passed (16+), proceed to:
- **[PRACTICE.md](./PRACTICE.md)** - Hands-on exercises
- **Next module** in the learning path

If you didn't pass, review:
- Questions you missed
- Related documentation sections
- Then retake the quiz
