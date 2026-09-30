---
Document ID: 4100-PREREQUISITES
Title: "Prerequisites: GGUF & Quantization"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Tags: ['prerequisites', 'quantization', 'gguf']
---

# Prerequisites: GGUF & Quantization

**For:** [4101-GGUF-Physics.md](./4101-GGUF-Physics.md)

---

## What You Should Know Before Starting

### Essential Concepts

**1. Neural Network Basics**
- What are neural network parameters (weights)?
- How models make predictions (forward pass)
- Why large models need lots of memory

**2. Number Representation**
- Floating-point numbers (FP32, FP16, BF16)
- How computers store decimals
- Precision vs memory tradeoff

**3. Model Inference**
- What happens during inference
- GPU memory (VRAM) basics
- Bottlenecks in running large models

---

## Quick Refresher

### Model Size & Memory

```text
Model Size = Parameters × Bytes per Parameter

Example (7B model):
FP32: 7,000,000,000 × 4 bytes = 28 GB
FP16: 7,000,000,000 × 2 bytes = 14 GB
8-bit: 7,000,000,000 × 1 byte  = 7 GB
4-bit: 7,000,000,000 × 0.5 byte= 3.5 GB
```

### Why Quantize?

**Problem:** Large models don't fit in GPU memory
**Solution:** Reduce precision (quantization)
**Tradeoff:** Slight accuracy loss for huge memory savings

---

## Learning Resources

**If you're new to these concepts:**

1. **Neural Network Basics (30 min):**
   - [3 Minute Neural Network](https://www.youtube.com/watch?v=aircAruvnKk)
   - Understand layers, weights, activations

2. **Floating Point Numbers (15 min):**
   - [IEEE 754 Floating Point](https://www.youtube.com/watch?v=kO-1tMWkU6U)
   - Understand FP32 vs FP16

3. **GPU Memory (20 min):**
   - Read [1501: Monitoring and Observability](../../phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
   - Understand VRAM, bandwidth, bottlenecks

---

## What You'll Learn

After completing 4101-GGUF-Physics.md, you'll understand:

1. ✅ How GGUF file format works
2. ✅ Quantization techniques (4-bit, 5-bit, 8-bit)
3. ✅ Loading quantized models
4. ✅ Memory vs accuracy tradeoffs
5. ✅ Best practices for quantization

---

## Readiness Check

**Answer these questions:**

1. What's the difference between FP32 and FP16?
2. Why does a 7B model need ~28GB in FP32?
3. What is VRAM and why does it matter?

**If unsure:** Review the quick refresher above.

**Ready to start?** → [4101-GGUF-Physics.md](./4101-GGUF-Physics.md)

---

**Estimated Time to Complete:** 2-3 hours
**Difficulty:** ⭐⭐⭐ Advanced
