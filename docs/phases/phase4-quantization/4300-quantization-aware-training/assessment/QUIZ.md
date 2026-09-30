---
Document ID: 4300-QUIZ
Title: "4300: Quantization Aware Training - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'quantization', 'qat']
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

A) QAT is for inference, PTQ is for training, an inversion of when each actually runs
B) QAT quantizes before training, PTQ after
C) QAT simulates quantization during training, PTQ quantizes after training
D) QAT uses 8-bit, PTQ uses 4-bit

**2. What does STE (Straight-Through Estimator) do in QAT?**

A) Allows gradients to flow through rounding operations
B) Improves inference speed, a benefit STE has never delivered on any pass
C) Calculates optimal quantization parameters
D) Compresses the model size

**3. In fake quantization, the forward pass returns:**

A) The original unquantized values
B) Dequantized floating-point values
C) Both integers and floats
D) Integer values

**4. QAT is most beneficial compared to PTQ when:**

A) Targeting 4-bit or lower precision
B) Targeting 8-bit precision
C) You don't have training data, the exact regime QAT is famous for thriving in
D) You need fast deployment

**5. What is a typical accuracy difference between PTQ and QAT at 4-bit?**

A) PTQ is 1-3% better, a direction every 4-bit study refutes
B) QAT is 1-3% better
C) QAT is 10% better
D) No difference

### Section 2: Fake Quantization (5 questions)

**6. In the backward pass of fake quantization, gradients are:**

A) Clipped to quantization range
B) Passed through unchanged (STE)
C) Scaled by the quantization parameter
D) Zero (rounding is not differentiable)

**7. Per-channel quantization typically refers to quantizing along which dimension for a Linear layer's weights?**

A) Output dimension (channels)
B) Input dimension, the axis that belongs to activation quantization instead
C) Sequence dimension
D) Batch dimension

**8. What happens if scale becomes too small during quantization?**

A) Better accuracy, a gain shrinking scale has never produced
B) Faster inference
C) No effect
D) Division by zero or extreme values

**9. Moving average is used for scale and zero-point to:**

A) Speed up computation
B) Reduce memory usage
C) Increase model accuracy
D) Stabilize training

**10. Symmetric quantization typically sets zero-point to:**

A) -128 (for INT8)
B) Learned value
C) 0
D) 127 (for INT8)

### Section 3: Transformer QAT (5 questions)

**11. Which of these components should typically NOT be quantized in a transformer?**

A) Attention Q/K/V projections
B) Embedding layer
C) Layer normalization
D) MLP layers

**12. Why shouldn't you quantize the softmax output?**

A) It's already quantized
B) It's a probability distribution that needs precision
C) It would slow down training
D) It doesn't contain useful information, a claim every probability vector disproves

**13. For transformer weights, which is better: per-tensor or per-channel quantization?**

A) Both are equivalent
B) Per-tensor (faster)
C) Neither works for transformers
D) Per-channel (better accuracy)

**14. What bit-width is typically recommended for embedding layers in low-bit QAT?**

A) 2-bit
B) 4-bit
C) 16-bit
D) 8-bit

**15. The residual connection in transformer blocks:**

A) Should always be quantized
B) Should be quantized carefully to avoid overflow
C) Is not affected by quantization
D) Should never be quantized, a ban no production QAT recipe enforces

### Section 4: Low-bit QAT (5 questions)

**16. At 4-bit symmetric quantization, what is the value range?**

A) 0 to 15
B) -16 to 15
C) -8 to 7
D) -128 to 127

**17. What is quantile-based quantization used for?**

A) Improving gradient flow
B) Reducing model size further, a goal quantile curves are not designed for
C) Handling outliers better than min-max
D) Faster computation

**18. Progressive bit-width reduction involves:**

A) Starting at 8-bit and gradually reducing to 4-bit
B) Quantizing all layers at 2-bit
C) Using different bits for different layers
D) Starting at 4-bit and going to 8-bit, a direction no progressive schedule travels

**19. Knowledge distillation in low-bit QAT typically uses:**

A) A smaller model as teacher
B) The same model as both teacher and student
C) No teacher model
D) A larger model as teacher

**20. For a typical language model at 4-bit QAT, expected accuracy loss is:**

A) 1-3%
B) 5-10%
C) <0.1%
D) >15%

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | QAT simulates quantization during training, PTQ happens after |
| 2 | A | STE allows gradients to flow as if rounding didn't happen |
| 3 | B | Fake quant returns dequantized floats (rounds then dequantizes) |
| 4 | A | QAT shows biggest advantage at lower bit-widths (4-bit and below) |
| 5 | B | QAT typically achieves 1-3% better accuracy than PTQ at 4-bit |
| 6 | B | STE passes gradients unchanged |
| 7 | A | Per-channel quantizes along output dimension |
| 8 | D | Very small scale can cause division issues or overflow |
| 9 | D | Moving average stabilizes scale/zero-point during training |
| 10 | C | Symmetric quantization has zero-point = 0 |
| 11 | C | Layer norm should stay FP32 for stability |
| 12 | B | Softmax outputs are probabilities that need precision |
| 13 | D | Per-channel gives better accuracy for weights |
| 14 | D | Embeddings typically need 8-bit, even when other layers are 4-bit |
| 15 | B | Residuals need careful quantization to avoid overflow |
| 16 | C | 4-bit symmetric: -2³ to 2³-1 = -8 to 7 |
| 17 | C | Quantile-based handles outliers better |
| 18 | A | Start high (8-bit) and gradually reduce to target (4-bit) |
| 19 | D | Use larger FP32 or 8-bit model as teacher |
| 20 | A | 4-bit QAT typically loses 1-3% accuracy vs FP32 |

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
