---
Document ID: PHASE4-QUIZ
Title: "Phase 4: Quantization & Compression Quiz"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Tags: ['assessment', 'quiz', 'quantization']
---

# Phase 4: Quantization & Compression Quiz

**30 Questions | Passing Score: 80% | Time: 60 minutes**

---

## Questions

### 1. What is quantization in the context of LLMs?
a) Reducing model size by removing layers
b) Compressing model architecture
c) Reducing precision of model weights
d) Optimizing model speed

**Answer:** c

---

### 2. What is the memory reduction from FP16 to INT4 quantization?
a) 16x reduction
b) 4x reduction
c) 2x reduction
d) 8x reduction

**Answer:** b

---

### 3. What is GGUF format?
a) GPU memory format
b) Graph optimization format
c) Gradient compression format
d) Quantized model format for llama.cpp

**Answer:** d

---

### 4. What is EXL2 format?
a) External library format
b) Execution layer format
c) Quantization format optimized for GPU inference
d) Extended learning format

**Answer:** c

---

### 5. What is AWQ?
a) Automatic weight quantization
b) Adaptive width quantization
c) Accelerated workflow quantization
d) Activation-aware weight quantization

**Answer:** d

---

### 6. What is GPTQ?
a) General purpose transformer quantization
b) Gradient-based post-training quantization
c) Global parameter transformer quantization
d) Accurate post-training quantization

**Answer:** d

---

### 7. What is double quantization?
a) Quantizing twice
b) Two-stage quantization
c) Quantizing quantization parameters
d) Dual precision quantization

**Answer:** c

---

### 8. What is the KV cache?
a) Key-value store for models
b) Kernel verification cache
c) Knowledge verification cache
d) Cached keys and values for faster generation

**Answer:** d

---

### 9. What is the benefit of quantizing KV cache?
a) Faster training
b) Better accuracy
c) Smaller model size
d) Reduced memory usage for long contexts

**Answer:** d

---

### 10. What is speculative decoding?
a) Predicting next tokens
b) Parallel decoding
c) Using draft model for faster generation
d) Speculative inference

**Answer:** c

---

### 11. What is QAT (Quantization Aware Training)?
a) Quick model training
b) Quality assurance testing
c) Training with simulated quantization
d) Quantization after training

**Answer:** c

---

### 12. What is fake quantization?
a) Using fake data
b) Dummy quantization
c) Simulating quantization during training
d) Testing quantization

**Answer:** c

---

### 13. What is the typical accuracy loss from INT4 quantization?
a) 2-5%
b) 10-15%
c) No loss
d) 20-30%

**Answer:** a

---

### 14. What is context window extension?
a) Expanding vocabulary
b) Increasing maximum sequence length
c) Adding more context
d) Extending training

**Answer:** b

---

### 15. What is PagedAttention?
a) Fast attention computation
b) Parallel attention
c) Memory-efficient attention for long contexts
d) Page-based attention

**Answer:** c

---

### 16. What is the main benefit of GGUF format?
a) Smallest size
b) Fastest speed
c) CPU/GPU hybrid inference
d) Best accuracy

**Answer:** c

---

### 17. What is calibration data used for in quantization?
a) Testing accuracy
b) Determining optimal quantization parameters
c) Training models
d) Validating results

**Answer:** b

---

### 18. What is the difference between symmetric and asymmetric quantization?
a) Symmetric uses zero point, asymmetric doesn't
b) Symmetric is faster
c) Asymmetric uses zero point, symmetric doesn't
d) Asymmetric is more accurate

**Answer:** c

---

### 19. What is per-channel quantization?
a) Quantizing one channel
b) Channel-wise quantization
c) Quantizing each output channel separately
d) Partial quantization

**Answer:** c

---

### 20. What is the main trade-off in quantization?
a) Memory vs accuracy
b) Speed vs memory
c) Accuracy vs speed
d) Size vs speed

**Answer:** a

---

### 21. What is 1.58-bit quantization?
a) Almost no precision loss
b) Future quantization method
c) Theoretical concept
d) Extreme quantization to {-1, 0, 1}

**Answer:** d

---

### 22. What is sparsity combined with quantization?
a) Adding sparse connections
b) Sparse quantization
c) Partial quantization
d) Removing zero weights before quantization

**Answer:** d

---

### 23. What is the main challenge of quantizing very large models (70B+)?
a) Calibration data requirements
b) Speed of quantization
c) Memory for calibration
d) Accuracy loss

**Answer:** a

---

### 24. What is batch quantization?
a) Quantizing per batch
b) Quantizing multiple models together
c) Batch size optimization
d) Group quantization

**Answer:** b

---

### 25. What is the benefit of quantization for edge deployment?
a) Better accuracy
b) Reduced memory and compute requirements
c) Faster training
d) Easier deployment

**Answer:** b

---

### 26. What is dynamic quantization?
a) Quantizing at runtime
b) Changing quantization
c) Quantizing during inference
d) Adaptive quantization

**Answer:** c

---

### 27. What is static quantization?
a) Compile-time quantization
b) Fixed precision
c) Constant quantization
d) Quantizing after calibration with fixed data

**Answer:** d

---

### 28. What is the impact of quantization on inference speed?
a) No speedup
b) 10x speedup
c) 2-4x speedup
d) Slower inference

**Answer:** c

---

### 29. What is layer-wise quantization?
a) One layer at a time
b) Sequential quantization
c) Hierarchical quantization
d) Different quantization per layer

**Answer:** d

---

### 30. What is the main advantage of QAT over post-training quantization?
a) Faster quantization
b) No calibration needed
c) Simpler process
d) Better accuracy with same bit-width

**Answer:** d

---

## Answer Key

1. c, 2. b, 3. d, 4. c, 5. d, 6. d, 7. c, 8. d, 9. d, 10. c,
11. c, 12. c, 13. a, 14. b, 15. c, 16. c, 17. b, 18. c, 19. c, 20. a,
21. d, 22. d, 23. a, 24. b, 25. b, 26. c, 27. d, 28. c, 29. d, 30. d

**Passing: 24/30 (80%)**
