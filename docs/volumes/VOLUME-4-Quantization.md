# Volume 4: Quantization & Optimization

**"Bending the Brain"** - Maximize your hardware to run larger, faster models.

---

## 📚 Volume Overview

**Difficulty:** ⭐⭐⭐ Advanced
**Time:** 4-5 weeks (part-time)
**Prerequisites:** Volume 3 (LLM Internals), NVIDIA GPU recommended

### What You'll Learn

After completing this volume, you will be able to:
- ✅ Understand quantization arithmetic (FP32 → FP16 → INT8 → INT4)
- ✅ Run 70B models on 11GB VRAM using GGUF
- ✅ Optimize context windows and KV cache
- ✅ Implement speculative decoding for acceleration
- ✅ Deploy vLLM and TGI inference engines
- ✅ Choose the right quantization format for your hardware

### Why This Volume Matters

This volume is **critical for HomeLab enthusiasts** with limited VRAM. You'll learn to:

- **Run models beyond your VRAM limits** - 70B on 11GB VRAM
- **Speed up inference** - 2-4x faster with proper optimization
- **Reduce memory footprint** - Fit larger models in same space
- **Production deployment** - Efficient serving with vLLM/TGI

---

## 🗺️ Learning Path

### Week 1: Low-Bit Quantization

#### Day 1-3: GGUF and CPU/GPU Offloading
**The most accessible quantization format**

1. **[4101: GGUF Physics](../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)** (3-4 hours)
   - GGUF format explanation
   - Quantization levels (Q8_0, Q5_K_M, Q4_K_M, Q3_K, etc.)
   - CPU/GPU hybrid offloading
   - TB3 bus optimization
   - llama.cpp integration

**Key Concept:**
```
GGUF Quantization Levels:
Q8_0: 8-bit, ~90% quality, ~1.8x faster
Q5_K_M: 5-bit mixed, ~85% quality, ~2.2x faster
Q4_K_M: 4-bit mixed, ~80% quality, ~2.8x faster
Q3_K: 3-bit, ~70% quality, ~3.5x faster

Trade-off: Lower bits = Faster but less accurate
```

**Practice:**
```bash
# Convert model to GGUF
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Quantize to different levels
./quantize ../mistral-7b.gguf mistral-7b-q4_k_m.gguf Q4_K_M
./quantize ../mistral-7b.gguf mistral-7b-q5_k_m.gguf Q5_K_M

# Run with GPU offloading
./main -m mistral-7b-q4_k_m.gguf \
  -ngl 33 \
  -t 8 \
  --color
```

**Checkpoint:** You can convert and run GGUF models

---

#### Day 4-5: EXL2 and AWQ
**Extreme quantization for VRAM-only execution**

1. **[4102: EXL2 and AWQ](../phases/phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md)** (3-4 hours)
   - EXL2 format (exllamav2)
   - AWQ (Activation-aware Weight Quantization)
   - VRAM-only execution
   - Speed comparison
   - Quality benchmarks

**EXL2 Advantages:**
```
GGUF: CPU/GPU hybrid, slower TB3 bus
EXL2: VRAM-only, blazing fast
AWQ: Smart quantization, better quality

Use EXL2 when:
- Model fits in VRAM
- Speed is critical
- You have NVIDIA GPU
```

**Practice:**
```python
# Convert to EXL2
from exllamav2 import *

# Convert model
converter = ExLlamaV2Converter('/path/to/model')
converter.convert('/output/exl2')

# Load and run
model = ExLlamaV2('/output/exl2')
model.load()
tokenizer = ExLlamaV2Tokenizer(model)
generator = ExLlamaV2Generator(model, tokenizer)

# Generate
text = generator.generate("Hello, world!", max_tokens=100)
```

**Checkpoint:** You understand extreme quantization formats

---

### Week 2: Double Quantization & BitsAndBytes

#### Day 1-3: BitsAndBytes (bnb)
**4-bit quantization for fine-tuning**

1. **[4103: Double Quantization](../phases/phase4-quantization/4100-low-bit/4103-Double-Quantization.md)** (3-4 hours)
   - BitsAndBytes (bnb) library
   - 4-bit quantization types (NF4, FP4)
   - Double quantization concept
   - Quantization-aware training
   - QLoRA integration

**Double Quantization:**
```python
from transformers import BitsAndBytesConfig
from transformers import AutoModelForCausalLM

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",  # NormalFloat 4
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,  # Double quantization
)

# Load model in 4-bit
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-v0.1",
    quantization_config=bnb_config,
    device_map="auto"
)

# Memory: ~14GB → ~5GB (4-bit)
# Speed: Similar to FP16
# Quality: ~98% of FP16
```

**Double Quantization Explained:**
```
Standard Quantization:
FP32 → INT4 (quantization constants in FP32)

Double Quantization:
FP32 → INT4 (quantization constants in INT8)

Benefit: Saves ~0.5GB per 7B model
```

**Checkpoint:** You can use 4-bit quantization for training

---

### Week 3: Context Window Engineering

#### Day 1-3: Context Window Physics
**Dealing with OOM in long sequences**

1. **[4201: Context Window Physics](../phases/phase4-quantization/4200-KV-Cache/4201-Context-Window-Physics.md)** (3-4 hours)
   - KV cache memory analysis
   - Context window size vs memory
   - Sliding window attention
   - Memory optimization strategies
   - Long context techniques

**KV Cache Memory:**
```python
# Memory calculation
# KV Cache = 2 * num_layers * num_heads * seq_len * head_dim * bytes_per_param

# For Mistral 7B:
# 2 * 32 * 32 * 4096 * 128 * 2 bytes (FP16) = ~2GB per 4k context

# Longer contexts:
# 8k context = ~4GB KV cache
# 16k context = ~8GB KV cache
# 32k context = ~16GB KV cache (OOM on 11GB!)
```

**Optimization Strategies:**
```python
# 1. Sliding window
window_size = 4096
keep only last N tokens

# 2. KV cache quantization
quantize KV cache to INT8

# 3. Multi-query attention
reduce KV cache size by num_heads

# 4. Context compression
summarize older context
```

2. **[4203: Context Window Optimization](../phases/phase4-quantization/4200-KV-Cache/guides/4203-Context-Window-Optimization.md)** (2-3 hours)
   - Complete optimization guide
   - Sliding window implementation
   - KV cache quantization
   - Memory-efficient attention

**Checkpoint:** You can optimize for long contexts

---

#### Day 4-5: Speculative Decoding
**Accelerate generation with draft models**

1. **[4202: Speculative Decoding](../phases/phase4-quantization/4200-KV-Cache/4202-Speculative-Decoding.md)** (3-4 hours)
   - Speculative decoding concept
   - Draft model strategies
   - Verification process
   - Speed benchmarks
   - Implementation details

**How It Works:**
```python
# Speculative decoding process:

# 1. Draft model (small, fast) generates K tokens
draft_tokens = draft_model.generate(prompt, K=10)

# 2. Main model (large, accurate) verifies in parallel
verification = main_model.verify(prompt, draft_tokens)

# 3. Accept verified tokens, reject others
# 4. Repeat

# Speedup: 2-3x faster for same quality
```

**Practice:**
```python
from vllm import LLM, SamplingParams

# Enable speculative decoding
llm = LLM(
    model="mistralai/Mistral-7B-v0.1",
    speculative_model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    num_speculative_tokens=10,
)

# Generate (2-3x faster)
outputs = llm.generate(["Hello, world!"])
```

2. **[Experiment: Speculative Decoding](../../experiments/EXP_4202_SPECULATIVE_DECODING.md)** (2-3 hours)
   - Benchmark speculative vs normal
   - Test different draft models
   - Analyze acceptance rates
   - Optimize K value

**Checkpoint:** You understand speculative decoding

---

### Week 4: Production Inference Engines

#### Day 1-3: vLLM Production Deployment
**High-concurrency inference engine**

1. **[1402: vLLM and TGI](../phases/phase1-infra/1400-LLMOps/1402-vLLM-and-TGI.md)** (2-3 hours)
   - vLLM architecture
   - PagedAttention
   - KV cache sharding
   - Continuous batching
   - Performance comparison

2. **[1404: vLLM Production Deployment](../phases/phase1-infra/1400-LLMOps/guides/1404-vLLM-Production-Deployment.md)** (3-4 hours)
   - Production setup
   - Docker deployment
   - Kubernetes configuration
   - Monitoring integration
   - Scaling strategies

**vLLM Key Features:**
```python
from vllm import LLM, SamplingParams

# PagedAttention = Efficient KV cache management
# Continuous batching = Add requests mid-generation
# Tensor parallelism = Multi-GPU support

llm = LLM(
    model="mistralai/Mistral-7B-v0.1",
    tensor_parallel_size=2,  # 2 GPUs
    max_model_len=8192,
    gpu_memory_utilization=0.9,
)

# High concurrency (100+ simultaneous requests)
outputs = llm.generate(prompts, sampling_params)
```

**Practice:**
```bash
# Deploy vLLM with Docker
docker run --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model mistralai/Mistral-7B-v0.1 \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.9
```

**Checkpoint:** You can deploy vLLM in production

---

#### Day 4-5: TGI Deployment
**Text Generation Inference by HuggingFace**

1. **[1405: TGI Deployment Guide](../phases/phase1-infra/1400-LLMOps/guides/1405-TGI-Deployment-Guide.md)** (3-4 hours)
   - TGI architecture
   - Deployment strategies
   - Flash Attention integration
   - Quantization support
   - Performance tuning

**TGI vs vLLM:**
```
vLLM: Best for throughput, continuous batching
TGI: Best for latency, Flash Attention, ease of use

Choose vLLM when:
- High concurrency (100+ requests)
- Need continuous batching
- Multi-GPU setup

Choose TGI when:
- Low latency critical
- Want Flash Attention
- Simpler deployment
```

**Practice:**
```bash
# Deploy TGI
docker run --gpus all \
  -p 8080:80 \
  -v ~/.cache/huggingface:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-v0.1 \
  --quantize awq \
  --flash-attention
```

**Checkpoint:** You can deploy TGI in production

---

## 🎯 Volume 4 Capstone Projects

### Project A: Run 70B Model on 11GB VRAM

**Time:** 6-8 hours
**Difficulty:** ⭐⭐⭐⭐

**Tasks:**
1. Download 70B model (Llama-2-70B or similar)
2. Convert to GGUF Q4_K_M
3. Configure optimal GPU offloading
4. Benchmark quality vs speed
5. Compare with smaller models

**Skills Demonstrated:**
- GGUF conversion ✅
- Memory optimization ✅
- Performance analysis ✅

### Project B: Optimize for Long Context

**Time:** 4-6 hours
**Difficulty:** ⭐⭐⭐

**Tasks:**
1. Benchmark context window limits
2. Implement sliding window
3. Quantize KV cache
4. Test on 16k+ token inputs
5. Document memory savings

**Skills Demonstrated:**
- Context optimization ✅
- Memory management ✅
- Benchmarking ✅

### Project C: Deploy vLLM/TGI Cluster

**Time:** 8-10 hours
**Difficulty:** ⭐⭐⭐⭐⭐

**Tasks:**
1. Set up vLLM/TGI on multiple GPUs
2. Configure load balancing
3. Implement monitoring
4. Benchmark high concurrency
5. Document deployment

**Skills Demonstrated:**
- Production deployment ✅
- Multi-GPU setup ✅
- Performance optimization ✅

---

## 📋 Volume 4 Checklist

Use this checklist to track your progress:

### Core Content (Required)
- [ ] **4101: GGUF Physics** (3-4 hours)
- [ ] **4102: EXL2 and AWQ** (3-4 hours)
- [ ] **4103: Double Quantization** (3-4 hours)
- [ ] **4201: Context Window Physics** (3-4 hours)
- [ ] **4202: Speculative Decoding** (3-4 hours)
- [ ] **4203: Context Window Optimization** (2-3 hours)
- [ ] **1402: vLLM and TGI** (2-3 hours)
- [ ] **1404: vLLM Production Deployment** (3-4 hours)
- [ ] **1405: TGI Deployment Guide** (3-4 hours)
- [ ] **EXP_4201: Context Window** (2 hours)
- [ ] **EXP_4202: Speculative Decoding** (2-3 hours)

**Total Core Time:** ~35-40 hours

### Capstone Projects (Choose 1)
- [ ] **Project A: 70B on 11GB VRAM** (6-8 hours)
- [ ] **Project B: Long Context Optimization** (4-6 hours)
- [ ] **Project C: vLLM/TGI Cluster** (8-10 hours)

---

## 🔗 Cross-References

### How Volume 4 Connects to Other Volumes:

**Quantization (4101-4103) →**
- Volume 3: Understanding model internals helps quantization
- Volume 5: QLoRA uses 4-bit quantization
- Volume 6: Quantized models for RAG
- Volume 7: Production quantization strategies

**Context Window (4201, 4203) →**
- Volume 3: Attention mechanisms
- Volume 6: Long-context RAG
- Volume 7: Production context optimization

**Speculative Decoding (4202) →**
- Volume 3: Understanding generation
- Volume 7: Production acceleration

**vLLM/TGI (1402, 1404, 1405) →**
- Volume 1: Docker deployment
- Volume 7: Production monitoring, scaling

---

## 📊 Volume 4 Statistics

| Metric | Value |
|--------|-------|
| **Core Documents** | 9 files |
| **Experiments** | 2 experiments |
| **Capstone Projects** | 3 projects |
| **Estimated Time** | 35-40 hours (core) + 4-10 hours (project) |
| **Difficulty** | ⭐⭐⭐ Advanced |

---

## 💡 Key Takeaways

### Quantization Trade-offs

```
FP32 (Full precision):
- Quality: 100%
- Memory: 100% (baseline)
- Speed: 1x

FP16/BF16 (Half precision):
- Quality: ~99%
- Memory: 50%
- Speed: ~2x

INT8 (8-bit):
- Quality: ~95%
- Memory: 25%
- Speed: ~2.5x

INT4 (4-bit):
- Quality: ~85%
- Memory: 12.5%
- Speed: ~3x

Choose based on your hardware and quality requirements!
```

### GGUF vs EXL2

```
GGUF:
- CPU/GPU hybrid offloading
- Slower TB3 bus
- Works on any hardware
- Best for: Models larger than VRAM

EXL2:
- VRAM-only execution
- Blazing fast
- Requires NVIDIA GPU
- Best for: Models fitting in VRAM
```

### Context Window Memory

```
KV Cache Memory Formula:
memory = 2 × layers × heads × seq_len × head_dim × bytes

Mistral 7B @ 4k context:
2 × 32 × 32 × 4096 × 128 × 2 = ~2GB

@ 8k: ~4GB
@ 16k: ~8GB
@ 32k: ~16GB (OOM on 11GB VRAM!)

Solution: Quantize KV cache to INT8 = 50% savings
```

---

## 🆘 Troubleshooting

### Common Issues in Volume 4

**Problem:** GGUF conversion fails
- **Solution:** Check model format, convert to GGUF first

**Problem:** vLLM OOM even after quantization
- **Solution:** Reduce max_model_len, enable KV cache quantization

**Problem:** Speculative decoding slower
- **Solution:** Check draft model size, reduce num_speculative_tokens

**Problem:** TB3 bus bottleneck
- **Solution:** Use EXL2 for VRAM-only, minimize CPU offloading

For more help, see **[TROUBLESHOOTING-Common-Issues.md](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)**

---

## 🎓 After Volume 4

### You're Ready For:

**Volume 5: Fine-Tuning** - Adapt quantized models to your domain
**Volume 6: RAG** - Build retrieval systems with optimized models
**Volume 7: Production** - Deploy optimized inference at scale

### Skills You've Gained:

```python
# You can now:
✅ Quantize models to 4-bit
✅ Run 70B on 11GB VRAM
✅ Optimize context windows
✅ Implement speculative decoding
✅ Deploy vLLM/TGI in production
✅ Choose optimal quantization format
✅ Benchmark and optimize inference
```

---

## 🚀 Next Steps

1. **Track your progress** in [PROGRESS-TRACKER.md](../00-META/PROGRESS-TRACKER.md)
2. **Continue to Volume 5** to learn fine-tuning
3. **OR skip to Volume 6** for RAG systems
4. **Review the [VOLUME-GUIDE.md](../00-META/VOLUME-GUIDE.md)** for alternative learning paths

---

**Recommended Resources:**
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** - GGUF implementation
- **[vLLM Docs](https://docs.vllm.ai/)** - vLLM documentation
- **[TGI Docs](https://huggingface.co/docs/text-generation-inference)** - TGI documentation

---

**Volume 4 Status:** 🟢 Complete
**Last Updated:** 2026-02-04
**Maintainer:** AI Engineering Curriculum Team
