---
Document ID: 4400-PRACTICE
Title: "4400: Advanced Quantization Techniques - Practice"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'quantization', 'advanced']
---

# 4400: Advanced Quantization Techniques - Practice

## Overview

Hands-on exercises for advanced quantization techniques.

## Exercise 1: GPTQ Quantization

**Task:** Quantize a model using GPTQ.

```python
# GPTQ: Accurate Quantization for Generative Pre-trained Transformers
# Key insight: Optimize weights to minimize quantization error in one pass

print("GPTQ Quantization")
print("="*60)

# Note: GPTQ requires auto-gptq library
# Installation: uv pip install auto-gptq
# (auto-gptq is deprecated - the current path is transformers' native
#  GPTQConfig or gptqmodel; the workflow below is conceptually identical)

print("""
GPTQ Workflow:

1. Create quantization config
   quantize_config = BaseQuantizeConfig(
       bits=4,              # 4-bit quantization
       group_size=128,      # Group size for quantization
       damp_percent=0.01,   # Damping factor (1% of Hessian diagonal)
       desc_act=False,      # Whether to activate columns in order
       sym=True,            # Symmetric quantization
       true_sequential=True, # Sequential quantization
       model_name_or_path="llama-7b"
   )

2. Load model
   model = AutoGPTQForCausalLM.from_pretrained(
       model_name,
       quantize_config=quantize_config
   )

3. Prepare calibration data
   examples = [
       {"text": "Example text 1"},
       {"text": "Example text 2"},
       # ... more examples
   ]

4. Quantize
   model.quantize(examples, batch_size=1)

5. Save
   model.save_quantized("./llama-7b-4bit")

Key Parameters:
- bits: 4 or 8 (4-bit = 4x compression)
- group_size: 128 or 64 (smaller = better quality, slower)
- damp_percent: 0.01 to 0.1 (prevents overfitting)

Expected Results:
- 7B model: ~4 GB (vs ~13 GB FP16)
- Perplexity increase: <10%
- Inference speed: similar to or faster than FP16 (decode is memory-bandwidth bound)
""")

# Simulated example
print("\nSimulated GPTQ Results:")
print("-" * 60)
models = ['LLaMA-7B', 'LLaMA-13B', 'LLaMA-70B']
for model in models:
    fp16_gb = {
        'LLaMA-7B': 13,
        'LLaMA-13B': 26,
        'LLaMA-70B': 140
    }[model]
    gptq_gb = fp16_gb / 3.5  # Approximate compression
    print(f"{model}: FP16={fp16_gb}GB, GPTQ-4bit={gptq_gb:.1f}GB")

# Expected Output:
# The GPTQ workflow text prints directly (no library call runs -
# GPTQ needs a GPU and a real model)
# Simulated table: LLaMA-7B 13->3.7, LLaMA-13B 26->7.4,
# LLaMA-70B 140->40.0 GB (4-bit ~ 0.5 bytes/weight plus group
# scale overhead -> ~3.5x compression)
```

---

## Exercise 2: AWQ with Custom Calibration

**Task:** Apply AWQ with domain-specific calibration data.

```python
print("\nAWQ: Activation-aware Weight Quantization")
print("="*60)

print("""
AWQ Key Idea:
- Scale weights based on activation magnitude
- Preserves large activations better than GPTQ
- Faster quantization (no Hessian computation)

Domain-Specific Calibration:

1. Prepare domain texts
   domain_texts = {
       "code": ["def func():", "class MyClass:", "import numpy"],
       "medical": ["patient symptoms", "diagnosis", "treatment"],
       "legal": ["contract terms", "liability", "jurisdiction"]
   }

2. Calibration data - raw domain texts (AutoAWQ tokenizes internally)
   calibration_data = domain_texts[domain]

3. Configure AWQ
   quant_config = {
       "zero_point": True,
       "q_group_size": 128,
       "w_bit": 4,
       "version": "GEMM"
   }

4. Quantize with domain calibration
   model.quantize(
       tokenizer=tokenizer,
       quant_config=quant_config,
       calib_data=calibration_data
   )

Benefits of Domain Calibration:
- Better accuracy on domain-specific tasks
- Activations in domain inform weight scaling
- Particularly useful for: code, medical, legal
""")

print("\nRecommended Calibration Data:")
print("-" * 60)
domains = {
    'General': 'Wikipedia, books, web text',
    'Code': 'GitHub repositories, StackOverflow',
    'Medical': 'PubMed, medical journals',
    'Legal': 'Court cases, contracts, statutes'
}

for domain, source in domains.items():
    print(f"{domain}: {source}")

# Expected Output:
# The AWQ key-idea text and the 4-step domain calibration recipe
# print directly; then the 4 recommended-source lines
# (General/Code/Medical/Legal)
```

---

## Exercise 3: GGUF Conversion Comparison

**Task:** Compare different GGUF quantization types.

```python
print("\nGGUF Quantization Types")
print("="*60)

gguf_types = {
    'Q4_K_M': {
        'bits': 'mostly 4-bit, key tensors 6-bit',
        'size_gb': '4.1 GB (for 7B model)',
        'quality': 'Good balance',
        'speed': 'Fast'
    },
    'Q5_K_M': {
        'bits': 'mostly 5-bit, key tensors 6-bit',
        'size_gb': '4.8 GB (for 7B model)',
        'quality': 'Better than Q4',
        'speed': 'Fast'
    },
    'Q8_0': {
        'bits': '8-bit',
        'size_gb': '7.2 GB (for 7B model)',
        'quality': 'Near FP16',
        'speed': 'Moderate'
    },
    'Q2_K': {
        'bits': '2-3 bit',
        'size_gb': '2.8 GB (for 7B model)',
        'quality': 'Significant degradation',
        'speed': 'Very Fast'
    }
}

print(f"{'Type':<10} {'Size (7B)':<12} {'Quality':<20} {'Speed':<12}")
print("-" * 60)
for qtype, info in gguf_types.items():
    print(f"{qtype:<10} {info['size_gb']:<12} {info['quality']:<20} {info['speed']:<12}")

print("\nConversion Commands:")
print("-" * 60)
print("""
# Convert to GGUF
python convert.py llama-7b --outfile llama-7b-f16.gguf --outtype f16

# Quantize to different formats
./quantize llama-7b-f16.gguf llama-7b-q4_k_m.gguf Q4_K_M
./quantize llama-7b-f16.gguf llama-7b-q5_k_m.gguf Q5_K_M
./quantize llama-7b-f16.gguf llama-7b-q8_0.gguf Q8_0

# Run with llama.cpp
./main -m llama-7b-q4_k_m.gguf -p "Hello, world" -n 100

# (binary names above are the classic ones - current llama.cpp
#  ships convert_hf_to_gguf.py, llama-quantize and llama-cli)
""")

# Expected Output:
# The 4-row quantization table (Q2_K 2.8 / Q4_K_M 4.1 / Q5_K_M 4.8 /
# Q8_0 7.2 GB for a 7B - llama.cpp's published sizes) and the
# conversion + inference commands print directly
```

---

## Exercise 4: EXL2 Variable Bit-width

**Task:** Create an EXL2 model with variable bit-widths.

```python
print("\nEXL2: Variable Bit-width Quantization")
print("="*60)

print("""
EXL2 Design Philosophy:
- Different layers need different precision
- Early layers: sensitive, need higher bits
- Middle layers: can use medium bits
- Late layers: can use lower bits
- Embeddings: need highest precision

Recommended Bit Configuration:

embeddings: 8.0  # Highest precision
layers.0-5:  6.0  # First few layers
layers.6-15: 5.0  # Middle layers (most of model)
layers.16-23: 4.5  # Later layers
layers.24-31: 4.0  # Last layers
lm_head: 8.0  # Output projection

Benefits:
- Better quality than uniform 4-bit
- Smaller than uniform 8-bit
- Optimal quality-size trade-off

Conversion (exllamav2 - EXL2 output is a safetensors repo, not GGUF):
python convert.py \\
    --in_dir ./llama-7b \\
    --output_dir llama-7b-exl2 \\
    --bits 4.5

Per-layer bit targets (conceptual - EXL2 measures layers and
optimizes the allocation around your average-bits target):
{
    "embeddings": 8.0,
    "layers.0.weight": 6.0,
    "layers.10.weight": 5.0,
    "layers.20.weight": 4.5,
    "lm_head": 8.0
}
""")

print("\nEstimated Sizes (7B model):")
print("-" * 60)
configs = [
    ('Uniform 4-bit', 4.0),
    ('Variable (4-8 bit)', 5.5),
    ('Uniform 8-bit', 8.0),
]

for name, avg_bits in configs:
    size_gb = 7 * (avg_bits / 16) * 2  # Approximate
    print(f"{name}: {avg_bits}b avg = {size_gb:.1f} GB")

# Expected Output:
# The philosophy/bit-config text prints directly, then:
# Uniform 4-bit: 4.0b avg = 3.5 GB
# Variable (4-8 bit): 5.5b avg = 4.8 GB
# Uniform 8-bit: 8.0b avg = 7.0 GB
# (7B params * bits/16 * 2 bytes)
```

---

## Exercise 5: Quantization Validation

```python
print("\nQuantization Validation Pipeline")
print("="*60)

print("""
Comprehensive Validation Metrics:

1. Perplexity Comparison
   from transformers import AutoModelForCausalLM
   import torch

   def compute_perplexity(model, tokenizer, text):
       inputs = tokenizer(text, return_tensors="pt")
       with torch.no_grad():
           outputs = model(**inputs, labels=inputs["input_ids"])
       return torch.exp(outputs.loss).item()

   ppl_fp16 = compute_perplexity(model_fp16, tokenizer, test_text)
   ppl_quant = compute_perplexity(model_quant, tokenizer, test_text)

   print(f"FP16 Perplexity: {ppl_fp16:.2f}")
   print(f"Quant Perplexity: {ppl_quant:.2f}")
   print(f"Ratio: {ppl_quant/ppl_fp16:.2f}x")

2. Generation Quality Test
   prompts = [
       "Write a Python function to",
       "The capital of France is",
       "Explain quantum computing"
   ]

   for prompt in prompts:
       inputs = tokenizer(prompt, return_tensors="pt")
       gen_fp16 = model_fp16.generate(**inputs, max_new_tokens=50)
       gen_quant = model_quant.generate(**inputs, max_new_tokens=50)
       # Compare outputs qualitatively

3. Performance Benchmark
   import time

   def benchmark_inference(model, tokenizer, prompt):
       inputs = tokenizer(prompt, return_tensors="pt")
       start = time.time()
       output = model.generate(**inputs, max_new_tokens=100)
       elapsed = time.time() - start
       tokens = output.shape[1] - inputs["input_ids"].shape[1]
       return tokens / elapsed

   tps_fp16 = benchmark_inference(model_fp16, tokenizer, "test")
   tps_quant = benchmark_inference(model_quant, tokenizer, "test")

   print(f"FP16: {tps_fp16:.1f} tokens/sec")
   print(f"Quant: {tps_quant:.1f} tokens/sec")

4. Memory Usage
   def get_memory_mb(model):
       return sum(p.numel() * p.element_size() for p in model.parameters()) / (1024**2)

   mem_fp16 = get_memory_mb(model_fp16)
   mem_quant = get_memory_mb(model_quant)

   print(f"Memory: {mem_fp16:.0f}MB -> {mem_quant:.0f}MB")
   print(f"Saved: {(1 - mem_quant/mem_fp16)*100:.1f}%")

Success Criteria:
- Perplexity increase < 20%
- Generation quality acceptable
- Speed: similar or faster
- Memory: significantly reduced
""")

# Expected Output:
# The four-part validation pipeline text and the sample report
# print directly - the pipeline code is illustrative (it needs a
# real fp16/quant model pair; nothing executes here)

print("\nValidation Report Template:")
print("-" * 60)
print("""
Model: LLaMA-7B
Quantization: GPTQ-4bit

┌─────────────────┬──────────┬──────────┐
│ Metric          │ FP16     │ Quantized │
├─────────────────┼──────────┼──────────┤
│ Perplexity      │ 10.5     │ 11.8     │
│ Memory (GB)     │ 13.5     │ 4.2      │
│ Tokens/sec      │ 25.3     │ 24.8     │
│ Size (GB)       │ 13.0     │ 3.8      │
└─────────────────┴──────────┴──────────┘

Verdict: ✅ Recommended
- 3.4x smaller
- 12% perplexity increase (acceptable)
- Similar inference speed
- Generation quality preserved
""")
```

---

## Exercise 6: Production Deployment

```python
print("\nProduction Deployment Package")
print("="*60)

print("""
1. Dockerfile
───────────────────────────────────────────────────────────
# python:3.13-slim matches the corpus standard; pip-installed torch
# wheels bundle the CUDA runtime (nvidia-* packages), so a CUDA base
# image is not needed for inference serving.
FROM python:3.13-slim

# Official uv-in-Docker pattern: copy the uv binary from the uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Dependency layer: only manifest/lockfile changes rebuild this.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY model/ /app/model/
COPY server.py /app/

EXPOSE 8000

CMD ["python3", "server.py"]
───────────────────────────────────────────────────────────

2. pyproject.toml
───────────────────────────────────────────────────────────
# dependencies recorded by uv add
dependencies = [
    "torch>=2.12.0",
    "transformers>=5.10.2",
    "accelerate>=1.13.0",
    "bitsandbytes>=0.50.2",
    "fastapi>=0.141.1",
    "uvicorn>=0.52.1",
]
───────────────────────────────────────────────────────────

3. server.py (FastAPI)
───────────────────────────────────────────────────────────
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

app = FastAPI()

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

model = AutoModelForCausalLM.from_pretrained(
    "./model",
    device_map="auto",
    quantization_config=bnb_config
)
tokenizer = AutoTokenizer.from_pretrained("./model")

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7

@app.post("/generate")
async def generate(req: GenerateRequest):
    inputs = tokenizer(req.prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=req.max_tokens,
        temperature=req.temperature
    )
    return {"text": tokenizer.decode(outputs[0], skip_special_tokens=True)}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
───────────────────────────────────────────────────────────

4. docker-compose.yml
───────────────────────────────────────────────────────────
services:
  api:
    build: .
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
───────────────────────────────────────────────────────────

Deployment Commands:
# Build
docker build -t quantized-llm .

# Run
docker-compose up -d

# Test
curl -X POST http://localhost:8000/generate \\
  -H "Content-Type: application/json" \\
  -d '{"prompt": "Hello, world", "max_tokens": 50}'
""")

# Expected Output:
# The four package files (Dockerfile, pyproject.toml, server.py,
# docker-compose.yml) and the build/run/test commands print
# directly - nothing here executes in the notebook itself
```

---

## Exercise 7: Compare All Methods

```python
print("\nComprehensive Quantization Method Comparison")
print("="*60)

comparison_data = {
    'Method': ['PTQ-INT8', 'GPTQ-4bit', 'AWQ-4bit', 'GGUF-Q4_K_M', 'EXL2-Variable'],
    'Quant Time (min)': [5, 30, 15, 10, 20],
    'Model Size (GB)': [6.5, 3.8, 4.0, 4.0, 4.5],
    'Tokens/sec': [22, 24, 26, 28, 30],
    'Perplexity': [10.8, 11.5, 11.2, 11.8, 11.0],
    'Quality Score': [4.8, 4.2, 4.5, 4.0, 4.6]
}

print(f"{'Method':<15} {'Time':<10} {'Size':<10} {'Speed':<10} {'PPL':<8} {'Quality':<10}")
print("-" * 70)
print("Illustrative numbers - always benchmark on your own hardware\n")

for i in range(len(comparison_data['Method'])):
    print(f"{comparison_data['Method'][i]:<15} "
          f"{comparison_data['Quant Time (min)'][i]:<10} "
          f"{comparison_data['Model Size (GB)'][i]:<10} "
          f"{comparison_data['Tokens/sec'][i]:<10} "
          f"{comparison_data['Perplexity'][i]:<8} "
          f"{comparison_data['Quality Score'][i]:<10}")

print("\n\nRecommendations:")
print("-" * 60)
print("""
Fastest Quantization:
  → PTQ-INT8 (5 minutes)
  Use when: Quick deployment needed

Best Quality:
  → EXL2-Variable or PTQ-INT8
  Use when: Accuracy is critical

Smallest Size:
  → GPTQ-4bit or AWQ-4bit
  Use when: Memory constrained

Fastest Inference:
  → EXL2 or GGUF
  Use when: Latency critical

Best Overall:
  → GPTQ-4bit (good balance)
  → AWQ-4bit (better quality)
  → EXL2 (best speed/quality)
""")

# Expected Output:
# The 5-row comparison table (illustrative, order-of-magnitude
# values) and the 5 recommendation blocks print directly
```

---

## Summary: Advanced Quantization Techniques

```text
METHOD COMPARISON:

┌────────────┬──────────┬──────────┬──────────┬──────────┐
│ Method     │ Size     │ Speed    │ Quality  │ Use Case │
├────────────┼──────────┼──────────┼──────────┼──────────┤
│ PTQ-INT8   │ 2x       │ Fast     │ Excellent │ Production│
│ GPTQ-4bit  │ 3.5x     │ Fast     │ Good     │ LLMs     │
│ AWQ-4bit   │ 3.5x     │ Fast     │ Good     │ LLMs     │
│ GGUF       │ 3.5x     │ Fastest  │ Good     │ CPU      │
│ EXL2       │ 3x       │ Fastest  │ Best     │ GPU      │
│ BnB-4bit   │ 4x       │ Moderate │ Good     │ Research │
└────────────┴──────────┴──────────┴──────────┴──────────┘

SELECTION GUIDE:

Edge Deployment:
  → GGUF (CPU optimization)
  → AWQ-4bit (activation-aware)

Server GPU:
  → EXL2 (best performance)
  → GPTQ (good balance)

Research:
  → BnB-4bit (easy to use)
  → PTQ-INT8 (baseline)

Production:
  → PTQ-INT8 (reliable)
  → GPTQ/AWQ (memory savings)

TROUBLESHOOTING:

Poor Quality:
  → Increase bit-width
  → Use domain-specific calibration
  → Try mixed precision

OOM During Quantization:
  → Reduce batch size
  → Use CPU offloading
  → Quantize in chunks

Slow Inference:
  → Use EXL2 or GGUF
  → Enable flash attention
  → Optimize batch size
```
