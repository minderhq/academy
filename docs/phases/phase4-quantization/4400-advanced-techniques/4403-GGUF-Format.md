---
Document ID: 4403
Title: GGUF Format
Phase: 4
Module: 4400
Last Updated: 2026-09-27
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

- Read a GGUF file's anatomy from raw bytes — magic 0x46554747 ("GGUF", little-endian), version 3, then the KV metadata — decoding STRING fields with `bytes(field.parts[field.data[0]]).decode("utf-8")` (raw `parts[-1]` prints the padded buffer)
- Choose a K-quant from the size/accuracy table — Q4_K_M's 4-bit quants with 6-bit quantized scales (~4.08 GB at 7B), Q5_K_M ~4.78, Q8_0 ~7.16 near-FP16, Q3_K_M ~3.30
- Run the two-step conversion — convert_hf_to_gguf.py (or `--remote` a HF repo id) emits an F16/BF16 GGUF with `--outtype f16|f32|bf16|q8_0|tq1_0|tq2_0|auto`, then `llama-quantize in.gguf out.gguf Q4_K_M`; convert.py's one-step `--outtype q4_k_m` flow is gone
- Steer per-tensor bits with `--tensor-type attn_v=q5_k` (regex-based, repeatable) plus `--token-embedding-type`/`--output-tensor-type`, and lift low-bit quality with `--imatrix` from llama-imatrix
- Serve GGUF — `llama-cli` (or the unified `llama cli -hf ggml-org/...` launcher) plus the llama-cpp-python `Llama(n_ctx=…, n_gpu_layers=…)` and `create_chat_completion` APIs
- Budget GPU offload at ~200 MB per Q4_K_M 7B layer (~140 MB weights + KV-cache headroom), and avoid the phantom flags (`--gpu-layers metal` doesn't exist — Metal is built into default macOS builds)

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
- 4-bit quants + 6-bit quantized scales
- 256-weight super-blocks split into 8×32 sub-blocks
- Good balance of size and speed

Size: ~4.08 GB for Llama-2-7B
Speed: Fast on CPU, very fast on GPU
```

### Q5_K_M (High Accuracy)

```yaml
Q5_K_M:
- 5-bit quants + 6-bit quantized scales
- Same 8×32 sub-block structure as Q4_K_M
- Better accuracy, slightly larger

Size: ~4.78 GB for Llama-2-7B
Speed: Medium on CPU, fast on GPU
```

### Q8_0 (8-bit)

```yaml
Q8_0:
- 8-bit quants, one FP16 scale per 32-weight block
- Near FP16 accuracy

Size: ~7.16 GB for Llama-2-7B
Speed: Slower on CPU
```

### Comparison

| Type | Size (Llama-2-7B) | Accuracy | CPU Speed | GPU Support |
|------|-------------------|----------|-----------|-------------|
| **Q4_K_M** | 4.08 GB | Good | Fast | Full |
| **Q5_K_M** | 4.78 GB | Better | Medium | Full |
| **Q8_0** | 7.16 GB | Best | Slow | Full |
| **Q3_K_M** | 3.30 GB | OK | Fast | Full |

## Converting to GGUF

### Using llama.cpp

```bash
# Clone llama.cpp
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Build with cmake — binaries land in ./build/bin
cmake -B build
cmake --build build --config Release -j

# Download model (in HF format)
# (Assume already downloaded to ./Llama-2-7b-hf)

# Step 1: convert to GGUF at a float precision. convert.py was split
# into convert_hf_to_gguf.py (FP/BF16 output) + the llama-quantize tool
# (K-quants). --outtype accepts f32/f16/bf16/q8_0/tq1_0/tq2_0/auto —
# never a K-quant name. A local directory or --remote HF repo id works:
python convert_hf_to_gguf.py \
    ../Llama-2-7b-hf \
    --outfile Llama-2-7b-f16.gguf \
    --outtype f16

# Step 2: quantize to K-quant
./build/bin/llama-quantize Llama-2-7b-f16.gguf Llama-2-7b-Q4_K_M.gguf Q4_K_M
```

### Quantization Options

```bash
# Q4_K_M (recommended)
./build/bin/llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M

# Q5_K_M (better accuracy)
./build/bin/llama-quantize model-f16.gguf model-Q5_K_M.gguf Q5_K_M

# Q8_0 (best accuracy)
./build/bin/llama-quantize model-f16.gguf model-Q8_0.gguf Q8_0

# Q3_K_M (smaller size)
./build/bin/llama-quantize model-f16.gguf model-Q3_K_M.gguf Q3_K_M

# Per-tensor overrides: --tensor-type is regex-based and repeatable
# (q5_k attention-V and FFN-down on a Q4_K_M base; sensitive
# tensors get more headroom than the blanket default)
./build/bin/llama-quantize model-f16.gguf model-mixed.gguf Q4_K_M \
    --tensor-type attn_v=q5_k \
    --tensor-type ffn_down=q5_k \
    --token-embedding-type q8_0
```

## Running GGUF Models

### Basic Inference

```bash
# Interactive mode (the old ./main binary is now llama-cli)
llama-cli -m Llama-2-7b-Q4_K_M.gguf \
    --color \
    -p "You are a helpful assistant."

# Generate from a prompt file
llama-cli -m Llama-2-7b-Q4_K_M.gguf \
    -f prompt.txt \
    -n 512

# The unified launcher fetches + runs straight from Hugging Face
# (llama serve -hf starts an OpenAI-compatible server the same way)
llama cli -hf ggml-org/gemma-3-1b-it-GGUF
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
# Budget ~200 MB per layer for a Q4_K_M 7B: ~140 MB of weights plus
# KV-cache headroom (1 GB of VRAM buys ~5 layers)
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
from gguf import GGUFReader, GGUFValueType

reader = GGUFReader("Llama-2-7b-Q4_K_M.gguf")

def field_value(field):
    # STRING values live in byte segments: parts[-1] prints the raw
    # padded buffer — index through field.data and decode instead
    if field.types[:1] == [GGUFValueType.STRING]:
        return bytes(field.parts[field.data[0]]).decode("utf-8")
    return field.parts[field.data[0]]

# Print metadata
print("Model Metadata:")
for key, field in reader.fields.items():
    print(f"  {key}: {field_value(field)}")

# List tensors
print("\nTensors:")
for tensor in reader.tensors:
    print(f"  {tensor.name}: {tuple(tensor.shape)} ({tensor.tensor_type})")
```

### Custom Metadata

```python
# llama.cpp's converters derive the standard general.* keys themselves;
# to write custom KV pairs, use GGUFWriter programmatically
from gguf import GGUFWriter

writer = GGUFWriter("model.gguf", "llama")
writer.add_string("general.author", "Your Name")
writer.add_string("general.description", "Custom finetune")
writer.add_string("general.license", "Apache-2.0")
# ... add_tensor() calls for every weight would go here ...
writer.write_header_to_file()
writer.write_kv_data_to_file()
writer.write_tensors_to_file()
writer.close()

# Online alternative: HuggingFace's GGUF-my-repo converts HF repos to
# GGUF and GGUF-editor edits metadata without any local tooling
```

## Advanced: Quantization Configuration

### Per-Layer Quantization

```bash
# llama-quantize steers bits per TENSOR NAME (regex, repeatable) —
# there is no layer-range DSL at conversion time. Mixed bits for
# layer ranges are a GPTQ/AWQ-side concern (see 4401/4402); here,
# protect the embedding and output tensors and sensitive tensors:
./build/bin/llama-quantize model-f16.gguf model-custom.gguf Q4_K_M \
    --token-embedding-type q8_0 \
    --output-tensor-type q8_0 \
    --tensor-type 'attn_k=q5_k' \
    --tensor-type 'attn_v=q5_k'
```

### Importance Matrix Quantization (IMatrix)

```bash
# Generate importance matrix from calibration data (run it on the
# F16 GGUF, before any quantization has been applied)
./build/bin/llama-imatrix \
    -m Llama-2-7b-f16.gguf \
    -f calibration_data.txt \
    -o imatrix.dat \
    -n 100

# Use IMatrix for better quantization — the llama.cpp analogue of the
# activation-aware weighting from 4402 (AWQ)
./build/bin/llama-quantize \
    Llama-2-7b-f16.gguf model-imatrix.gguf Q4_K_M \
    --imatrix imatrix.dat
```

## Troubleshooting

### Issue 1: Model Not Loading

```bash
# Error: unknown or invalid magic number

# Solution: Verify file integrity
sha256sum Llama-2-7b-Q4_K_M.gguf

# Or re-convert/re-quantize
python convert_hf_to_gguf.py ./model --outfile model-f16.gguf --outtype f16
./build/bin/llama-quantize model-f16.gguf model.gguf Q4_K_M
```

### Issue 2: Slow Inference

```bash
# Solution: Check GPU offloading
llama-cli -m model.gguf -ngl 33  # Offload all layers

# Metal is enabled automatically in default macOS builds — there is
# no backend-selection flag; -ngl offloads whatever fits
```

### Issue 3: Poor Quality

```bash
# Solution: Use higher quantization
./build/bin/llama-quantize model-f16.gguf model-Q5_K_M.gguf Q5_K_M

# Or use IMatrix
./build/bin/llama-imatrix -m model-f16.gguf -f calib.txt -o imatrix.dat
./build/bin/llama-quantize model-f16.gguf model.gguf Q4_K_M --imatrix imatrix.dat
```

## GGUF Ecosystem

### Tools

- **llama.cpp**: Core inference engine
- **llama-cpp-python**: Python bindings
- **Ollama**: Cross-platform GGUF runner (macOS/Windows/Linux)
- **LM Studio**: GUI for GGUF models
- **text-generation-webui**: Web UI with GGUF support

### Finding GGUF Models

- HuggingFace: Search for "gguf" filter
- Official orgs + quality quantizers (bartowski, etc.) — TheBloke is archived; its uploads remain but are frozen
- Civitai: Community models

## Best Practices

1. **Use Q4_K_M for most use cases:** Best balance
2. **Q5_K_M for production:** Better accuracy
3. **Enable GPU offloading:** Even partial helps
4. **Use IMatrix for custom models:** Better quantization
5. **Validate before deploying:** Test on target tasks

## Further Reading

- **Documentation:** https://github.com/ggml-org/llama.cpp (quantization workflow in tools/quantize/README.md)
- **GGUF Spec:** https://github.com/ggml-org/ggml/blob/master/docs/gguf.md
- **Python Lib:** https://github.com/abetlen/llama-cpp-python
- **See also:** 4402 (AWQ) for the activation-aware idea behind --imatrix

## References

### Related PROJECT-OMEGA Documents

- [4401: GPTQ](4401-GPTQ.md)
- [4402: AWQ](4402-AWQ.md)
- [4404: EXL2 Format](4404-EXL2-Format.md)
- [4405: Sparsity + Quantization](4405-Sparsity-Quantization.md)
- [4406: 1.58-bit Quantization](4406-1.58-bit-Quantization.md)
- [4407: Ternary & Binary Networks](4407-Ternary-Binary.md)

---

## Next Steps

→ **[4404: EXL2 Format](./4404-EXL2-Format.md)** - GPU-optimized format
