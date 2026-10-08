---
Document ID: PHASE4-CHECKPOINT
Title: "Progress Checkpoint: Phase 4 - Quantization & Compression"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Tags: ['checkpoint', 'quantization', 'qat', 'quantization-aware-training']
---

# Progress Checkpoint: Phase 4 - Quantization & Compression

**Track your progress through Phase 4 modules**

---

## Phase 4 Overview

**Phase:** [4000] Quantization & Compression

**Modules:** 4 (4100, 4200, 4300, 4400)

**Estimated Time:** 5-7 weeks

**Difficulty:** ⭐⭐⭐ Advanced

---

## Phase Completion Goal

After completing Phase 4, you will:

- ✅ Understand GGUF format
- ✅ Quantize models to 4-bit
- ✅ Optimize context windows
- ✅ Run large models on limited hardware
- ✅ Apply quantization-aware training when PTQ quality is not enough
- ✅ Choose the right advanced recipe (GPTQ, AWQ, GGUF, EXL2)

---

## Module Checkpoints

### Module 4100: Low-Bit Quantization (Required)

**Checkpoint Quiz:**

1. What is quantization and why do we need it?
2. Explain 4-bit vs 8-bit quantization tradeoffs
3. What is GGUF format?

**Practical Verification:**

- [ ] Can quantize model to 4-bit
- [ ] Can load GGUF models
- [ ] Can run 70B on 11GB VRAM

---

### Module 4200: KV-Cache Engineering (Required)

**Checkpoint Quiz:**

1. What is KV-cache and why does it matter?
2. How does context window size affect memory?
3. What is speculative decoding?

**Practical Verification:**

- [ ] Can explain what the KV-cache stores and why it matters
- [ ] Can estimate memory growth with context window size
- [ ] Can describe when speculative decoding pays off

---

### Module 4300: Quantization-Aware Training (Required)

**Checkpoint Quiz:**

1. What is fake quantization and how does it simulate low precision?
2. How does QAT differ from post-training quantization?
3. When does QAT justify its training cost?

**Practical Verification:**

- [ ] Can explain the fake-quantization round-trip
- [ ] Has run a PyTorch or Transformers QAT flow
- [ ] Can quantize a transformer to low bit-widths with QAT

---

### Module 4400: Advanced Quantization Techniques (Required)

**Checkpoint Quiz:**

1. How do GPTQ and AWQ differ in how they select weights?
2. What do GGUF and EXL2 each optimize for?
3. What does 1.58-bit quantization mean in practice?

**Practical Verification:**

- [ ] Has quantized a model with GPTQ or AWQ
- [ ] Can pick a format (GGUF / EXL2) for a deployment target
- [ ] Knows when sparsity or sub-1-bit methods apply

---

## Common Pitfalls

1. **Unrepresentative Calibration:** Quantizing on a handful of random samples misestimates activation ranges - calibrate on data that mirrors real inputs
2. **Observers Left On:** After QAT, observer modules must be disabled or converted - leaving them on keeps fake-quant noise in the deployed graph
3. **Optimistic Memory Math:** KV-cache size scales with layers and KV heads, not just sequence length - budget with the full formula before promising context windows
4. **Mixed-Precision Surprise:** 4-bit weights still pay FP16 activation and embedding costs - measure actual VRAM instead of assuming the weight-bit ratio

---

## Phase 4 Completion Badge

**Badge:** ⚡ Quantization Ninja

**You've earned it when:**

- All required modules completed
- Can quantize models
- Can optimize context windows
- Can run 70B on 11GB VRAM
- Can quantize with GPTQ or AWQ
