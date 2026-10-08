---
Document ID: PHASE4-QUIZ
Title: "Phase 4: Quantization & Compression Quiz"
Last Updated: 2026-10-08
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
b) Reducing precision of model weights
c) Compressing model architecture
d) Optimizing model speed

**Answer:** b

---

### 2. What is the memory reduction from FP16 to INT4 quantization?
a) 16x reduction
b) 4x reduction
c) 2x reduction
d) 8x reduction

**Answer:** b

---

### 3. What is GGUF format?
a) Quantized model format for llama.cpp
b) Graph optimization format with fused decoder branches
c) Gradient compression format
d) GPU memory format

**Answer:** a

---

### 4. What is EXL2 format?
a) External library format
b) Quantization format optimized for GPU inference
c) Execution layer format
d) Extended learning format carrying auxiliary training heads

**Answer:** b

---

### 5. What is AWQ?
a) Activation-aware weight quantization
b) Adaptive width quantization
c) Accelerated workflow quantization
d) Automatic weight quantization that skips calibration entirely

**Answer:** a

---

### 6. What is GPTQ?
a) Accurate post-training quantization
b) Gradient-based post-training quantization
c) Global parameter transformer quantization
d) General purpose transformer quantization

**Answer:** a

---

### 7. What is double quantization?
a) Quantizing twice
b) Quantizing quantization parameters
c) Two-stage quantization
d) Dual precision quantization alternating scales every second layer

**Answer:** b

---

### 8. What is the KV cache?
a) Key-value store for models
b) Kernel verification cache
c) Knowledge verification cache reused across checkpoints and exported runs
d) Cached keys and values for faster generation

**Answer:** d

---

### 9. What is the benefit of quantizing KV cache?
a) Faster training
b) Better accuracy
c) Smaller model size achieved by pruning cached entries mid-flight
d) Reduced memory usage for long contexts

**Answer:** d

---

### 10. What is speculative decoding?
a) Using draft model for faster generation
b) Parallel decoding
c) Predicting next tokens
d) Speculative inference

**Answer:** a

---

### 11. What is QAT (Quantization Aware Training)?
a) Training with simulated quantization
b) Quality assurance testing with mocked inference endpoints
c) Quick model training
d) Quantization after training

**Answer:** a

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
d) Extending training schedules beyond the announced token budget

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
a) Smallest possible file size
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
d) Size vs speed traded against hardware uptime targets

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
b) Speed of quantization measured across sharded conversion workers
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
d) Simpler deployment on constrained devices

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
c) Simpler process once calibration curves are pre-baked offline
d) Better accuracy with same bit-width

**Answer:** d

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | B | Quantization reduces the precision of model weights (FP16 to INT4) to shrink memory |
| 2 | B | 16-bit to 4-bit weights is a 4x memory reduction |
| 3 | A | GGUF is the quantized model format used by llama.cpp |
| 4 | B | EXL2 is a quantization format optimized for GPU inference |
| 5 | A | AWQ stands for Activation-aware Weight Quantization |
| 6 | A | GPTQ is accurate post-training quantization driven by calibration |
| 7 | B | Double quantization quantizes the quantization parameters themselves for further savings |
| 8 | D | The KV cache stores computed keys and values so generation does not recompute them |
| 9 | D | Quantizing the KV cache cuts per-token memory, which matters most for long contexts |
| 10 | A | Speculative decoding drafts tokens with a small model and verifies them with the target model |
| 11 | A | QAT trains with simulated quantization in the forward pass |
| 12 | C | Fake quantization simulates quantize/dequantize during training so the model adapts to the precision |
| 13 | A | Well-tuned INT4 typically costs a few percent of accuracy (2-5%) |
| 14 | B | Context window extension increases the maximum sequence length the model handles |
| 15 | C | PagedAttention pages KV cache memory for memory-efficient long-context attention |
| 16 | C | GGUF's main benefit is CPU/GPU hybrid inference on consumer hardware |
| 17 | B | Calibration data drives the search for optimal quantization parameters |
| 18 | C | Asymmetric quantization uses a zero point; symmetric centers at zero without one |
| 19 | C | Per-channel quantization computes scales for each output channel separately |
| 20 | A | The core trade-off is memory saved versus accuracy lost |
| 21 | D | 1.58-bit quantization restricts weights to the set {-1, 0, 1} |
| 22 | D | Sparsity with quantization removes zero weights before quantizing the rest |
| 23 | A | Very large models need far more calibration data to quantize without accuracy loss |
| 24 | B | Batch quantization quantizes multiple models together in one pipeline run |
| 25 | B | Quantization cuts both memory and compute requirements on constrained edge devices |
| 26 | C | Dynamic quantization quantizes activations at inference time |
| 27 | D | Static quantization fixes scales on calibration data before deployment |
| 28 | C | INT4 kernels typically deliver a 2-4x inference speedup |
| 29 | D | Layer-wise quantization applies different quantization settings per layer |
| 30 | D | QAT reaches better accuracy than post-training quantization at the same bit-width |

**Passing: 24/30 (80%)**

