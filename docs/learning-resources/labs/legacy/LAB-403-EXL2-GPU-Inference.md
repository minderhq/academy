# LAB-403: EXL2 GPU Inference

## Overview
Use ExLlamaV2 for optimized GPU inference.

## Prerequisites
- LAB-401 completed
- NVIDIA GPU (8GB+ VRAM)

## Setup

```bash
# Install ExLlamaV2
git clone https://github.com/turboderp/exllamav2
cd exllamav2
pip install -r requirements.txt
```

## Exercise 1: Convert Model to EXL2

```python
from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Cache, ExLlamaV2Tokenizer

# TODO: Configure conversion
config = ExLlamaV2Config()
config.model_dir = "./Llama-2-7b-hf"  # Path to HF model
config.max_seq_len = 2048
config.auto_map = True

# TODO: Convert with variable bit-width
from exllamav2 import convert

# This would normally be done via CLI
# But we can also do it programmatically
print("Converting model...")
# Note: Use convert.py CLI for actual conversion
# python convert.py --in_dir ./Llama-2-7b-hf --out_dir ./llama-2-7b-exl2 --output-format exl2
```

## Exercise 2: Load and Run Inference

```python
# TODO: Load model
model = ExLlamaV2(config)
model.load()

# TODO: Load tokenizer
tokenizer = ExLlamaV2Tokenizer(config)

# TODO: Create cache
cache = ExLlamaV2Cache(model, max_seq_len=2048, lazy=True)

# TODO: Generate
from exllamav2.generator import ExLlamaV2DynamicGenerator

generator = ExLlamaV2DynamicGenerator(model, tokenizer, cache)
generator.warmup()

prompt = "The future of artificial intelligence is"
response = generator.generate_simple(prompt, max_new_tokens=50)

print(f"Generated: {response}")
```

## Exercise 3: Benchmarking

```python
import time

def benchmark_exl2(model, tokenizer, cache, prompts, max_tokens=50):
    """Benchmark EXL2 inference."""

    generator = ExLlamaV2DynamicGenerator(model, tokenizer, cache)
    generator.warmup()

    times = []
    for prompt in prompts:
        start = time.time()
        _ = generator.generate_simple(prompt, max_new_tokens=max_tokens)
        end = time.time()

        times.append((end - start) / max_tokens)

    avg_time = sum(times) / len(times)
    tokens_per_sec = max_tokens / avg_time

    return tokens_per_sec

# TODO: Run benchmark
prompts = ["The capital of France is"] * 10
tps = benchmark_exl2(model, tokenizer, cache, prompts)

print(f"EXL2 Speed: {tps:.2f} tokens/sec")
```

## Exercise 4: Compare with Other Formats

```python
# TODO: Compare EXL2 vs GGUF vs HF
formats = {
    "EXL2": "./llama-2-7b-exl2",
    "HF_FP16": "./Llama-2-7b-hf",
    # Add GGUF if available
}

for format_name, model_path in formats.items():
    # Load and benchmark
    # Measure: speed, memory, quality
    print(f"\n{format_name}:")
    print(f"  Speed: ...")
    print(f"  Memory: ...")
```

## Exercise 5: Streaming Inference

```python
from exllamav2.generator import ExLlamaV2StreamingGenerator

# TODO: Create streaming generator
generator = ExLlamaV2StreamingGenerator(model, tokenizer, cache)
generator.warmup()

# TODO: Stream tokens
prompt = "Tell me a story about AI"

tokens = []
full_prompt = generator.begin_stream(prompt)
text_so_far = ""

while True:
    chunk, eos, _ = generator.stream()
    if eos:
        break

    text_so_far += chunk
    print(chunk, end="", flush=True)

    if len(text_so_far) > 200:
        break

print("\n\nStreaming complete!")
```

## Exercise 6: Batch Processing

```python
# TODO: Batch inference (if supported)
# Note: EXL2V2 supports efficient batching

prompts = [
    "The capital of France is",
    "The capital of Germany is",
    "The capital of Italy is",
]

# Process and compare times
# See ExLlamaV2 documentation for batch API
```

## Expected Outputs

1. Exercise 1: Model converted to EXL2
2. Exercise 2: Generation working
3. Exercise 3: High tokens/sec (>50 on RTX 4090)
4. Exercise 4: EXL2 fastest on GPU
5. Exercise 5: Streaming tokens visible
6. Exercise 6: Batch processing working

## Troubleshooting

**Issue:** Out of memory
```python
# Solution: Use lazy cache or reduce max_seq_len
cache = ExLlamaV2Cache(model, max_seq_len=1024, lazy=True)
```

**Issue:** Slow first generation
```python
# Solution: Always warmup
generator.warmup()
```

## Time Estimate: 3-4 hours

---
