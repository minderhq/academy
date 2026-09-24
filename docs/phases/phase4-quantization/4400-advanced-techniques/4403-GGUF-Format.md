---
Document ID: 4403
Title: GGUF Format
Phase: 4
Module: 4400
Last Updated: 2026-09-24
Status: Complete
Difficulty: Expert
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'advanced', 'optimization']
---

# 4403: GGUF Format

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [What is GGUF?](#what-is-gguf)
- [GGUF Quantization Types](#gguf-quantization-types)
- [Converting to GGUF](#converting-to-gguf)
- [Running GGUF Models](#running-gguf-models)
- [GGUF with GPU Offloading](#gguf-with-gpu-offloading)
- [GGUF Metadata](#gguf-metadata)
- [Advanced: Quantization Configuration](#advanced-quantization-configuration)
- [Troubleshooting](#troubleshooting)
- [GGUF Ecosystem](#gguf-ecosystem)
- [Best Practices](#best-practices)
- [Further Reading](#further-reading)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain What is GGUF
- Explain GGUF Quantization Types
- Configure and operate Converting to GGUF
- Explain Running GGUF Models
- Explain GGUF with GPU Offloading
- Explain GGUF Metadata

---

## Abstract

GGUF (GPT-Generated Unified Format) is the file format used by llama.cpp, enabling efficient LLM inference on CPU and consumer hardware.

## What is GGUF?

GGUF is a binary file format that stores:
- Quantized model weights
- Model metadata (architecture, hyperparameters)
- Tokenizer vocabulary
- KV cache configuration

```text
GGUF File Structure:
┌─────────────────────────────────────────────────────────────┐
│  Header                                                     │
│  ├─ Magic number (0x46554747)                              │
│  ├─ Version                                                │
│  ├─ Tensor count                                           │
│  └─ KV count                                               │
├─────────────────────────────────────────────────────────────┤
│  Key-Value Pairs (Metadata)                                │
│  ├─ architecture: llama                                     │
│  ├─ vocab_size: 32000                                      │
│  ├─ context_length: 2048                                   │
│  └─ ...                                                    │
├─────────────────────────────────────────────────────────────┤
│  Tensor Data                                                │
│  ├─ token_embd.weight (Q4_K)                              │
│  ├─ blk.0.attn_q.weight (Q4_K)                            │
│  ├─ blk.0.attn_k.weight (Q4_K)                            │
│  └─ ...                                                    │
└─────────────────────────────────────────────────────────────┘
```

## GGUF Quantization Types

### Q4_K_M (Recommended)

```yaml
Q4_K_M:
- 6-bit super-blocks
- 4-bit sub-blocks
- Good balance of size and speed

Size: ~4.5 GB for 7B model
Speed: Fast on CPU, very fast on GPU
```

### Q5_K_M (High Accuracy)

```yaml
Q5_K_M:
- 8-bit super-blocks
- 5-bit sub-blocks
- Better accuracy, slightly larger

Size: ~5.5 GB for 7B model
Speed: Medium on CPU, fast on GPU
```

### Q8_0 (8-bit)

```yaml
Q8_0:
- Pure 8-bit quantization
- Near FP32 accuracy

Size: ~8.5 GB for 7B model
Speed: Slower on CPU
```

### Comparison

| Type | Size (7B) | Accuracy | CPU Speed | GPU Support |
|------|-----------|----------|-----------|-------------|
| **Q4_K_M** | 4.5 GB | Good | Fast | Full |
| **Q5_K_M** | 5.5 GB | Better | Medium | Full |
| **Q8_0** | 8.5 GB | Best | Slow | Full |
| **Q3_K_M** | 3.5 GB | OK | Fast | Full |

## Converting to GGUF

### Using llama.cpp

```bash
# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build
make

# Download model (in HF format)
# (Assume already downloaded to ./Llama-2-7b-hf)

# Convert to GGUF
python convert.py \
    --model ../Llama-2-7b-hf \
    --outfile Llama-2-7b-Q4_K_M.gguf \
    --outtype q4_k_m

# Output:
# Sorting vocab...
# Writing GGUF...
# Model written to Llama-2-7b-Q4_K_M.gguf
```

### Quantization Options

```bash
# Q4_K_M (recommended)
python convert.py --model ./model --outfile model-Q4_K_M.gguf --outtype q4_k_m

# Q5_K_M (better accuracy)
python convert.py --model ./model --outfile model-Q5_K_M.gguf --outtype q5_k_m

# Q8_0 (best accuracy)
python convert.py --model ./model --outfile model-Q8_0.gguf --outtype q8_0

# Q3_K_M (smaller size)
python convert.py --model ./model --outfile model-Q3_K_M.gguf --outtype q3_k_m

# Mixed precision (custom)
python convert.py \
    --model ./model \
    --outfile model-mixed.gguf \
    --quantize Q4_K_M,blk.0-10:Q8_0,blk.11-32:Q4_K_M
```

## Running GGUF Models

### Basic Inference

```bash
# Interactive mode
./main -m Llama-2-7b-Q4_K_M.gguf \
    --color \
    --interactive \
    --prompt "You are a helpful assistant."

# Generate from file
./main -m Llama-2-7b-Q4_K_M.gguf \
    --file prompt.txt \
    --n-predict 512
```

### Python API

```python
from llama_cpp import Llama

# Load model
model = Llama(
    model_path="Llama-2-7b-Q4_K_M.gguf",
    n_ctx=2048,  # Context window
    n_gpu_layers=-1,  # Offload all to GPU (if available)
    verbose=False,
)

# Generate
output = model(
    "The future of AI is",
    max_tokens=128,
    stop=["\n", "User:"],
    echo=False,
)

print(output['choices'][0]['text'])
```

### Chat Completion

```python
from llama_cpp import Llama

model = Llama(model_path="Llama-2-7b-Q4_K_M.gguf", n_gpu_layers=-1)

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"},
]

response = model.create_chat_completion(
    messages=messages,
    temperature=0.7,
    max_tokens=128,
)

print(response['choices'][0]['message']['content'])
```

## GGUF with GPU Offloading

### Determine GPU Layers

```python
from llama_cpp import Llama

import torch

# Check GPU memory
gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB

# Calculate layers to offload
# Approximate: each layer ~100MB for 7B model at Q4_K_M
n_gpu_layers = min(int(gpu_memory * 5), 33)  # Conservative estimate

print(f"GPU Memory: {gpu_memory:.2f} GB")
print(f"Offloading {n_gpu_layers} layers")

model = Llama(
    model_path="Llama-2-7b-Q4_K_M.gguf",
    n_gpu_layers=n_gpu_layers,
)
```

### Benchmark CPU vs GPU

```python
import time
from llama_cpp import Llama

prompts = [
    "The capital of France is",
    "Python is a programming language that",
    "Machine learning is",
]

def benchmark(model, prompts):
    start = time.time()
    for prompt in prompts:
        _ = model(prompt, max_tokens=50)
    end = time.time()
    return (end - start) / len(prompts)

# CPU-only
model_cpu = Llama(model_path="Llama-2-7b-Q4_K_M.gguf", n_gpu_layers=0)
cpu_time = benchmark(model_cpu, prompts)

# GPU-accelerated
model_gpu = Llama(model_path="Llama-2-7b-Q4_K_M.gguf", n_gpu_layers=-1)
gpu_time = benchmark(model_gpu, prompts)

print(f"CPU: {cpu_time:.2f}s per prompt")
print(f"GPU: {gpu_time:.2f}s per prompt")
print(f"Speedup: {cpu_time / gpu_time:.2f}x")
```

## GGUF Metadata

### Reading Metadata

```python
from gguf import GGUFReader

reader = GGUFReader("Llama-2-7b-Q4_K_M.gguf")

# Print metadata
print("Model Metadata:")
for key, value in reader.fields.items():
    if hasattr(value, 'parts'):
        print(f"  {key}: {value.parts[-1]}")
    else:
        print(f"  {key}: {value}")

# List tensors
print("\nTensors:")
for tensor in reader.tensors:
    print(f"  {tensor.name}: {tensor.shape} ({tensor.type})")
```

### Custom Metadata

```python
# When converting, add custom metadata
python convert.py \
    --model ./model \
    --outfile model.gguf \
    --metadata "author=Your Name" \
    --metadata "description=Custom finetune" \
    --metadata "license=Apache-2.0"
```

## Advanced: Quantization Configuration

### Per-Layer Quantization

```python
# Create custom quantization config
quant_config = {
    'embeddings': 'Q8_0',  # Keep embeddings at 8-bit
    'layers.0-10': 'Q5_K_M',  # Early layers at 5-bit
    'layers.11-32': 'Q4_K_M',  # Later layers at 4-bit
}

# Apply during conversion
python convert.py \
    --model ./model \
    --outfile model-custom.gguf \
    --quantize embeddings:Q8_0,layers.0-10:Q5_K_M,layers.11-32:Q4_K_M
```

### Importance Matrix Quantization (IMatrix)

```bash
# Generate importance matrix from calibration data
./imatrix \
    -m Llama-2-7b-Q4_K_M.gguf \
    -f calibration_data.txt \
    -o imatrix.dat \
    -n 100

# Use IMatrix for better quantization
python convert.py \
    --model ./model \
    --outfile model-imatrix.gguf \
    --imatrix imatrix.dat \
    --outtype q4_k_m
```

## Troubleshooting

### Issue 1: Model Not Loading

```bash
# Error: unknown or invalid magic number

# Solution: Verify file integrity
sha256sum Llama-2-7b-Q4_K_M.gguf

# Or re-download/convert
python convert.py --model ./model --outfile model.gguf --outtype q4_k_m
```

### Issue 2: Slow Inference

```bash
# Solution: Check GPU offloading
./main -m model.gguf --n-gpu-layers 33  # Offload all layers

# Or use metal backend for Mac
./main -m model.gguf --n-gpu-layers 33 --gpu-layers metal
```

### Issue 3: Poor Quality

```bash
# Solution: Use higher quantization
python convert.py --model ./model --outfile model-Q5_K_M.gguf --outtype q5_k_m

# Or use IMatrix
./imatrix -m model.gguf -f calib.txt -o imatrix.dat
python convert.py --model ./model --outfile model.gguf --imatrix imatrix.dat
```

## GGUF Ecosystem

### Tools

- **llama.cpp**: Core inference engine
- **llama-cpp-python**: Python bindings
- **Ollama**: Mac app using GGUF
- **LM Studio**: GUI for GGUF models
- **text-generation-webui**: Web UI with GGUF support

### Finding GGUF Models

- HuggingFace: Search for "gguf" filter
- TheBloke: Popular quantizer on HuggingFace
- Civitai: Community models

## Best Practices

1. **Use Q4_K_M for most use cases:** Best balance
2. **Q5_K_M for production:** Better accuracy
3. **Enable GPU offloading:** Even partial helps
4. **Use IMatrix for custom models:** Better quantization
5. **Validate before deploying:** Test on target tasks

## Further Reading

- **Documentation:** https://github.com/ggerganov/llama.cpp
- **GGUF Spec:** https://github.com/ggerganov/ggml/blob/master/docs/gguf.md
- **Python Lib:** https://github.com/abetlen/llama-cpp-python

## References

### Related ai-engineering-curriculum Documents

- [4401: GPTQ](4401-GPTQ.md)
- [4402: AWQ](4402-AWQ.md)
- [4404: EXL2 Format](4404-EXL2-Format.md)
- [4405: Sparsity + Quantization](4405-Sparsity-Quantization.md)
- [4406: 1.58-bit Quantization](4406-1.58-bit-Quantization.md)
- [4407: Ternary & Binary Networks](4407-Ternary-Binary.md)

---

## Next Steps

→ **[4404: EXL2 Format](./4404-EXL2-Format.md)** - GPU-optimized format

---

**Last Updated:** 2026-02-04
