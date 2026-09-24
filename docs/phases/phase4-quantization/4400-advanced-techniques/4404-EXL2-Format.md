---
Document ID: 4404
Title: EXL2 Format
Phase: 4
Module: 4400
Last Updated: 2026-02-05
Status: Complete
Difficulty: Expert
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'advanced', 'optimization']
---

# 4404: EXL2 Format

## Abstract

EXL2 is the quantization format for ExLlamaV2, a highly optimized inference library for NVIDIA GPUs.

## What is EXL2?

EXL2 (ExLlamaV2 Format) is designed specifically for GPU inference:

```
EXL2 Features:
- Optimized for NVIDIA GPUs (CUDA kernels)
- Faster than GGUF on GPU
- Flexible bit-width per layer
- Streaming from disk (low VRAM)
```

## EXL2 vs Other Formats

| Format | Target | Speed (GPU) | VRAM Usage | CPU Support |
|--------|--------|-------------|------------|-------------|
| **EXL2** | GPU | Fastest | Low | No |
| **GGUF** | CPU/GPU | Fast | Medium | Yes |
| **GPTQ** | GPU | Medium | Medium | No |
| **AWQ** | GPU | Fast | Medium | No |

## Converting to EXL2

### Using ExLlamaV2

```bash
# Install ExLlamaV2
git clone https://github.com/turboderp/exllamav2
cd exllamav2
pip install -r requirements.txt

# Convert HF model to EXL2
python convert.py \
    --in_dir ./Llama-2-7b-hf \
    --out_file Llama-2-7b-exl2 \
    --output-format exl2 \
    --calibration_data ./calibration_data.txt \
    --measurement_bits 4.0 \
    --shard_size 2G
```

### Bit-width Specification

```bash
# Uniform 4-bit
python convert.py \
    --in_dir ./model \
    --out_file model-4bit.exl2 \
    --output-format exl2 \
    --bits 4

# Variable bit-width (recommended)
python convert.py \
    --in_dir ./model \
    --out_file model-mixed.exl2 \
    --output-format exl2 \
    --bits 4.0,4.5,5.0,6.0,8.0

# Custom per-layer
python convert.py \
    --in_dir ./model \
    --out_file model-custom.exl2 \
    --output-format exl2 \
    --bits blk.0-10:6.0,blk.11-32:4.0
```

## Running EXL2 Models

### Python API

```python
from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Cache,
    ExLlamaV2Tokenizer,
)

# Load config
config = ExLlamaV2Config()
config.model_dir = "./Llama-2-7b-exl2"
config.max_seq_len = 2048
config.scale_pos_emb = 1.0

# Load model
model = ExLlamaV2(config)
model.load()

# Load tokenizer
tokenizer = ExLlamaV2Tokenizer(config)

# Create cache
cache = ExLlamaV2Cache(model, max_seq_len=2048, lazy=True)

# Generate
from exllamav2.generator import ExLlamaV2Generator

generator = ExLlamaV2Generator(model, tokenizer, cache)
generator.settings.token_repetition_penalty = 1.0
generator.settings.temperature = 0.7
generator.settings.top_k = 40
generator.settings.top_p = 0.9

text = generator.generate_simple("The future of AI is", num_tokens=128)
print(text)
```

### Chat Completion

```python
from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Cache, ExLlamaV2Tokenizer
from exllamav2.generator import ExLlamaV2DynamicGenerator

# Load model (same as above)
config = ExLlamaV2Config()
config.model_dir = "./Llama-2-7b-exl2"
model = ExLlamaV2(config)
model.load()

tokenizer = ExLlamaV2Tokenizer(config)
cache = ExLlamaV2Cache(model, max_seq_len=4096, lazy=True)

# Create generator
generator = ExLlamaV2DynamicGenerator(
    model=model,
    tokenizer=tokenizer,
    cache=cache,
)

# Chat
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
]

# Add user message
generator.warmup()
for message in messages:
    generator.append_message(message["role"], message["content"])

# Generate response
response = generator.run()
print(response)
```

## Streaming Inference

```python
from exllamav2.generator import ExLlamaV2StreamingGenerator

generator = ExLlamaV2StreamingGenerator(
    model=model,
    tokenizer=tokenizer,
    cache=cache,
)

generator.warmup()
generator.set_stop_conditions(["\n", "User:"])

# Stream tokens
prompt = "The capital of France is"
generator.begin_stream(prompt)

while True:
    chunk, eos, _ = generator.stream()
    print(chunk, end="", flush=True)

    if eos:
        break

print()
```

## Low VRAM Mode

```python
# Enable disk streaming for low VRAM
config = ExLlamaV2Config()
config.model_dir = "./Llama-2-7b-exl2"
config.max_seq_len = 4096
config.low_mem = True  # Enable streaming

model = ExLlamaV2(config)
model.load()

# Cache with streaming
cache = ExLlamaV2Cache(
    model,
    max_seq_len=4096,
    lazy=True,
    max_batch_size=1,
)

# Run on 8GB GPU
generator = ExLlamaV2DynamicGenerator(model, tokenizer, cache)
response = generator.run_simple("Your prompt here", max_new_tokens=512)
```

## Performance Optimization

### Batch Size Tuning

```python
# ExL2V2 supports efficient batching
generator.settings.token_repetition_penalty = 1.0

# For single user: small batch
cache = ExLlamaV2Cache(model, max_seq_len=2048, max_batch_size=1)

# For multiple users: larger batch
cache = ExLlamaV2Cache(model, max_seq_len=2048, max_batch_size=8)
```

### Expert Quantization

```python
# Use expert-calibrated bit-widths
expert_bits = {
    'embeddings': 8.0,
    'layers.0-5': 6.0,
    'layers.6-20': 4.5,
    'layers.21-32': 4.0,
}

# Apply during conversion
bit_spec = ",".join([f"{k}:{v}" for k, v in expert_bits.items()])
```

## Benchmarking

```python
import time

def benchmark_exl2(model, tokenizer, cache, prompts):
    generator = ExLlamaV2DynamicGenerator(model, tokenizer, cache)

    times = []
    for prompt in prompts:
        start = time.time()
        _ = generator.run_simple(prompt, max_new_tokens=128)
        end = time.time()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    tokens_per_sec = 128 / avg_time

    return tokens_per_sec

prompts = ["The capital of France is"] * 10
tps = benchmark_exl2(model, tokenizer, cache, prompts)
print(f"Speed: {tps:.2f} tokens/sec")
```

## EXL2 File Structure

```
model.exl2:
├── config.json           # Model configuration
├── tokenizer.model       # Sentence piece tokenizer
├── cache.calibration     # Calibration data (optional)
├── output.safetensors    # Weights (sharded)
│   ├── shard_00001_2G.exl2
│   ├── shard_00002_2G.exl2
│   └── ...
└── output.safetensors.index  # Index for shards
```

## Troubleshooting

### Issue 1: Out of Memory

```python
# Solution: Enable low mem mode
config.low_mem = True

# Or reduce context length
config.max_seq_len = 2048  # Instead of 4096

# Or use lazy cache
cache = ExLlamaV2Cache(model, max_seq_len=2048, lazy=True)
```

### Issue 2: Slow First Generation

```python
# Solution: Warmup the generator
generator.warmup()
# Now subsequent generations will be fast
```

### Issue 3: Quality Degradation

```python
# Solution: Increase bit-width for sensitive layers
python convert.py \
    --in_dir ./model \
    --out_file model-high-quality.exl2 \
    --bits embeddings:8.0,blk.0-10:6.0,blk.11-32:4.5
```

## Best Practices

1. **Use variable bit-width:** Lower bits for later layers
2. **Enable low_mem for large models:** Allows running 70B on 24GB VRAM
3. **Warmup generator:** First call will be slow anyway
4. **Shard size 2-4GB:** Balance disk I/O and loading time
5. **Use calibration data:** Better bit-width assignment

## EXL2 vs GGUF Decision Tree

```
Need CPU inference?
└─ Yes: Use GGUF
└─ No: Have NVIDIA GPU?
    └─ Yes: Use EXL2 (faster)
    └─ No: Use GGUF
```

## Further Reading

- **GitHub:** https://github.com/turboderp/exllamav2
- **Documentation:** ExLlamaV2 repo README
- **Benchmarks:** Various comparison blogs

## Next Steps

→ **[4405: Sparsity + Quantization](./4405-Sparsity-Quantization.md)** - Combining pruning with quantization

---

**Last Updated:** 2026-02-04
