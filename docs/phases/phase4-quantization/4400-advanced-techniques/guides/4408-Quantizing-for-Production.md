# 4408: Quantizing for Production

## Abstract

This guide covers end-to-end quantization workflows for production deployment.

## Production Quantization Pipeline

```text
┌─────────────────────────────────────────────────────────────┐
│  1. Model Selection                                         │
│     ├─ Choose base model                                    │
│     └─ Verify license and usage rights                      │
├─────────────────────────────────────────────────────────────┤
│  2. Calibration Data                                        │
│     ├─ Collect domain-specific data                         │
│     └─ Prepare for quantization                             │
├─────────────────────────────────────────────────────────────┤
│  3. Quantization Method                                     │
│     ├─ Choose: GPTQ / AWQ / QAT / GGUF / EXL2              │
│     └─ Configure quantization parameters                    │
├─────────────────────────────────────────────────────────────┤
│  4. Quantization                                            │
│     ├─ Run quantization                                     │
│     └─ Monitor process                                      │
├─────────────────────────────────────────────────────────────┤
│  5. Validation                                              │
│     ├─ Accuracy benchmarks                                  │
│     ├─ Quality checks                                       │
│     └─ Performance testing                                   │
├─────────────────────────────────────────────────────────────┤
│  6. Deployment                                              │
│     ├─ Optimize for target hardware                         │
│     ├─ Create API wrapper                                   │
│     └─ Monitor in production                                │
└─────────────────────────────────────────────────────────────┘
```

## Step 1: Model Selection

```python
# Verify model compatibility
from transformers import AutoConfig

model_name = "meta-llama/Llama-2-7b-hf"

config = AutoConfig.from_pretrained(model_name)

# Check supported architectures
SUPPORTED_ARCHITECTURES = [
    "llama", "mistral", "mixtral", "qwen", "phi",
    "gemma", "gpt-neox", "falcon",
]

if config.model_type not in SUPPORTED_ARCHITECTURES:
    print(f"Warning: {config.model_type} may not be well-supported")

# Check license
if hasattr(config, 'license'):
    print(f"License: {config.license}")
    # Verify commercial use allowed
```

## Step 2: Calibration Data

```python
def prepare_calibration_data(tokenizer, domain_texts, num_samples=256):
    """
    Prepare calibration data for quantization.

    Args:
        tokenizer: Model tokenizer
        domain_texts: List of domain-specific texts
        num_samples: Number of calibration samples

    Returns:
        List of tokenized inputs
    """
    calibration_data = []

    for text in domain_texts[:num_samples]:
        # Tokenize
        tokens = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        )

        calibration_data.append(tokens["input_ids"])

    return calibration_data

# Example: Code-focused model
code_texts = open("code_samples.txt").readlines()[:256]
calib_data = prepare_calibration_data(tokenizer, code_texts)
```

## Step 3: Choose Quantization Method

### Decision Tree

```text
Target Hardware?
├─ CPU Only
│  └─ Use GGUF (Q4_K_M or Q5_K_M)
├─ NVIDIA GPU
│  └─ Use EXL2 (fastest) or AWQ (good compatibility)
└─ Multiple Platforms
   └─ Use GPTQ + GGUF (offer both)

Have Training Data?
├─ Yes
│  └─ Consider QAT (best accuracy)
└─ No
   └─ Use PTQ (GPTQ/AWQ)
```

### Configuration Template

```python
# GPTQ Configuration
GPTQ_CONFIG = {
    "bits": 4,
    "group_size": 128,
    "damp_percent": 0.01,
    "desc_act": True,
}

# AWQ Configuration
AWQ_CONFIG = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,
    "version": "GEMM",
}

# GGUF Configuration
GGUF_CONFIG = {
    "type": "Q4_K_M",  # or "Q5_K_M" for better accuracy
}

# EXL2 Configuration
EXL2_CONFIG = {
    "bits": "4.0,4.5,5.0,6.0",  # Variable bit-width
}
```

## Step 4: Run Quantization

### GPTQ Quantization

```python
from transformers import AutoTokenizer
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

model_name = "meta-llama/Llama-2-7b-hf"

# Setup
tokenizer = AutoTokenizer.from_pretrained(model_name)
quantize_config = BaseQuantizeConfig(**GPTQ_CONFIG)

# Load model
model = AutoGPTQForCausalLM.from_pretrained(
    model_name,
    quantize_config=quantize_config,
    trust_remote_code=True,
)

# Quantize
print("Starting quantization...")
model.quantize(calib_data, batch_size=1)

# Save
output_dir = "./models/llama-2-7b-gptq"
model.save_quantized(output_dir)
tokenizer.save_pretrained(output_dir)

print(f"Model saved to {output_dir}")
```

### AWQ Quantization

```python
from awq import AutoAWQForCausalLM

model = AutoAWQForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Quantize
model.quantize(calib_data, AWQ_CONFIG)

# Save
output_dir = "./models/llama-2-7b-awq"
model.save_quantized(output_dir)
tokenizer.save_pretrained(output_dir)
```

### GGUF Conversion

```bash
# Convert to GGUF
python /path/to/llama.cpp/convert.py \
    --model ./Llama-2-7b-hf \
    --outfile ./models/Llama-2-7b-Q4_K_M.gguf \
    --outtype q4_k_m
```

### EXL2 Conversion

```bash
# Convert to EXL2
python /path/to/exllamav2/convert.py \
    --in_dir ./Llama-2-7b-hf \
    --out_file ./models/Llama-2-7b-exl2 \
    --output-format exl2 \
    --bits 4.0,4.5,5.0,6.0
```

## Step 5: Validation

### Accuracy Validation

```python
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM

def evaluate_perplexity(model, tokenizer, test_data):
    """Calculate perplexity on test data."""

    model.eval()
    total_loss = 0
    total_tokens = 0

    with torch.no_grad():
        for batch in test_data:
            outputs = model(
                input_ids=batch["input_ids"],
                labels=batch["input_ids"],
            )
            total_loss += outputs.loss * batch["input_ids"].size(1)
            total_tokens += batch["input_ids"].size(1)

    perplexity = torch.exp(total_loss / total_tokens)
    return perplexity.item()

# Load test data
test_data = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")

# Compare models
model_fp32 = AutoModelForCausalLM.from_pretrained(model_name)
ppl_fp32 = evaluate_perplexity(model_fp32, tokenizer, test_data)

model_quantized = load_quantized_model("./models/llama-2-7b-gptq")
ppl_quantized = evaluate_perplexity(model_quantized, tokenizer, test_data)

print(f"FP32 Perplexity: {ppl_fp32:.2f}")
print(f"Quantized Perplexity: {ppl_quantized:.2f}")
print(f"Difference: {ppl_quantized - ppl_fp32:.2f}")
```

### Quality Validation

```python
def test_generation_quality(model, tokenizer, test_prompts):
    """Test generation on domain-specific prompts."""

    results = []

    for prompt in test_prompts:
        # Generate
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=128)
        text = tokenizer.decode(outputs[0])

        # Manual review or automated metrics
        results.append({
            "prompt": prompt,
            "output": text,
        })

    return results

# Example test prompts
test_prompts = [
    "def fibonacci(n):",
    "The capital of France is",
    "Explain quantum computing:",
]

results = test_generation_quality(model_quantized, tokenizer, test_prompts)
```

### Performance Validation

```python
import time

def benchmark_inference(model, tokenizer, batch_size=1, num_iterations=100):
    """Benchmark inference speed."""

    model.eval()
    prompt = "The future of AI is"

    # Warmup
    for _ in range(10):
        inputs = tokenizer(prompt, return_tensors="pt")
        _ = model.generate(**inputs, max_new_tokens=10)

    # Benchmark
    start = time.time()
    tokens_generated = 0

    for _ in range(num_iterations):
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=50)
        tokens_generated += 50

    end = time.time()

    avg_time = (end - start) / num_iterations * 1000  # ms
    tokens_per_sec = tokens_generated / (end - start)

    return {
        "avg_latency_ms": avg_time,
        "tokens_per_sec": tokens_per_sec,
    }

# Benchmark
stats = benchmark_inference(model_quantized, tokenizer)
print(f"Average Latency: {stats['avg_latency_ms']:.2f} ms")
print(f"Throughput: {stats['tokens_per_sec']:.2f} tokens/sec")
```

## Step 6: Deployment

### Docker Container

```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install dependencies
RUN apt-get update && apt-get install -y python3 python3-pip

# Install libraries
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy model
COPY model/ /app/model

# Expose port
EXPOSE 8000

# Run API
CMD ["python3", "api.py"]
```

### FastAPI Wrapper

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer

from awq import AutoAWQForCausalLM

app = FastAPI()

# Load model
model = AutoAWQForCausalLM.from_quantized("./model", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("./model")

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 128
    temperature: float = 0.7

class GenerationResponse(BaseModel):
    text: str

@app.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    try:
        inputs = tokenizer(request.prompt, return_tensors="pt").to(model.device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        text = tokenizer.decode(outputs[0])

        return GenerationResponse(text=text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Monitoring

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
inference_count = Counter('inference_count', 'Total inference requests')
inference_duration = Histogram('inference_duration_seconds', 'Inference duration')
token_count = Counter('token_count', 'Total tokens generated')

# Track usage
@app.post("/generate")
async def generate(request: GenerationRequest):
    inference_count.inc()

    with inference_duration.time():
        outputs = model.generate(...)
        tokens = outputs.shape[1]
        token_count.inc(tokens)

    return {"text": text}

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

## Production Checklist

- [ ] Model selected and license verified
- [ ] Calibration data prepared
- [ ] Quantization method chosen
- [ ] Quantization completed successfully
- [ ] Accuracy validated (<5% loss)
- [ ] Quality validated (manual review)
- [ ] Performance benchmarked
- [ ] Docker image created
- [ ] API wrapper tested
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Rollback plan ready

## Common Issues

### Issue 1: Accuracy Drop >5%

**Solution:** Try higher bit-width or mixed precision
```python
# Use 8-bit for embeddings and early layers
config = {"bits": "embeddings:8.0,blk.0-10:6.0,blk.11-32:4.0"}
```

### Issue 2: Slow Inference

**Solution:** Optimize for target hardware
- GPU: Use EXL2 or AWQ with layer fusion
- CPU: Use GGUF with thread optimization

### Issue 3: High Memory Usage

**Solution:** Enable streaming or offloading
```python
# EXL2: Low memory mode
config.low_mem = True

# GGUF: CPU offloading
n_gpu_layers = 20  # Partial offload
```

## Best Practices

1. **Always validate:** Test on domain-specific data
2. **Offer multiple formats:** GGUF for CPU, EXL2 for GPU
3. **Monitor in production:** Track accuracy and performance
4. **Version control:** Keep track of quantization parameters
5. **Document everything:** Calibration data, configs, results


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Last Updated:** 2026-02-04
