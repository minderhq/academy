# 4400: Advanced Quantization Techniques - Practice

## Overview

Hands-on exercises for advanced quantization techniques.

## Exercise 1: GPTQ Quantization

**Task:** Quantize a model using GPTQ.

```python
# GPTQ: Accurate Quantization for Generative Pre-trained Transformers
# Key insight: Optimize weights to minimize quantization error in one pass

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print("GPTQ Quantization")
print("="*60)

# Note: GPTQ requires auto-gptq library
# Installation: pip install auto-gptq

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
- Inference speed: similar to FP16
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

2. Calibration data format
   calibration_data = [
       tokenizer(text, return_tensors="pt")["input_ids"]
       for text in domain_texts[domain][:100]
   ]

3. Configure AWQ
   quant_config = {
       "zero_point": True,
       "q_group_size": 128,
       "w_bit": 4,
       "q_config": {
           "zero_point": True,
           "w_bit": 4
       }
   }

4. Quantize with domain calibration
   model.quantize(
       calibration_data,
       quant_config=quant_config
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
```

---

## Exercise 3: GGUF Conversion Comparison

**Task:** Compare different GGUF quantization types.

```python
print("\nGGUF Quantization Types")
print("="*60)

gguf_types = {
    'Q4_K_M': {
        'bits': 'mostly 4-bit, some 2-3 bit',
        'size_gb': '4.0 GB (for 7B model)',
        'quality': 'Good balance',
        'speed': 'Fast'
    },
    'Q5_K_M': {
        'bits': 'mostly 5-bit, some 3-4 bit',
        'size_gb': '5.0 GB (for 7B model)',
        'quality': 'Better than Q4',
        'speed': 'Fast'
    },
    'Q8_0': {
        'bits': '8-bit',
        'size_gb': '8.0 GB (for 7B model)',
        'quality': 'Near FP16',
        'speed': 'Moderate'
    },
    'Q2_K': {
        'bits': '2-3 bit',
        'size_gb': '2.5 GB (for 7B model)',
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
""")
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

Conversion:
python convert.py \\
    --in_dir ./llama-7b \\
    --out_file llama-7b-exl2.gguf \\
    --bits 4.5 \\
    --config ./custom_bit_config.json

Custom Config Example:
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
       gen_fp16 = model_fp16.generate(prompt, max_tokens=50)
       gen_quant = model_quant.generate(prompt, max_tokens=50)
       # Compare outputs qualitatively

3. Performance Benchmark
   import time

   def benchmark_inference(model, tokenizer, prompt):
       start = time.time()
       output = model.generate(tokenizer(prompt), max_tokens=100)
       elapsed = time.time() - start
       tokens = len(output)
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
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \\
    python3.10 \\
    python3-pip \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY model/ /app/model/
COPY server.py /app/

EXPOSE 8000

CMD ["python3", "server.py"]
───────────────────────────────────────────────────────────

2. requirements.txt
───────────────────────────────────────────────────────────
torch>=2.0.0
transformers>=4.30.0
accelerate>=0.20.0
bitsandbytes>=0.41.0
fastapi>=0.100.0
uvicorn>=0.23.0
───────────────────────────────────────────────────────────

3. server.py (FastAPI)
───────────────────────────────────────────────────────────
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

model = AutoModelForCausalLM.from_pretrained(
    "./model",
    device_map="auto",
    load_in_4bit=True
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
    return {"text": tokenizer.decode(outputs[0])}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
───────────────────────────────────────────────────────────

4. docker-compose.yml
───────────────────────────────────────────────────────────
version: '3.8'
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
  → GPTQ/AWX (memory savings)

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

---

**Last Updated:** 2026-02-05
