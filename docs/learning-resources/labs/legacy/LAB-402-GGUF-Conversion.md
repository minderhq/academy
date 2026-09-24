# LAB-402: GGUF Conversion

## Overview
Convert models to GGUF format for llama.cpp inference.

## Prerequisites
- LAB-401 completed
- Docker or Linux environment

## Setup

```bash
# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

pip install torch transformers
```

## Exercise 1: Convert Model to GGUF

```bash
# TODO: Download model (or use existing)
# For this lab, we'll use GPT-2 as example

# Convert to GGUF
python convert.py \
    --model ../gpt2 \
    --outfile gpt2-f32.gguf \
    --outfile gpt2-f32.gguf \
    --outtype f32

# Check file size
ls -lh gpt2-f32.gguf
```

## Exercise 2: Quantize GGUF

```bash
# TODO: Quantize to different formats
# Q4_K_M (recommended)
./quantize gpt2-f32.gguf gpt2-Q4_K_M.gguf Q4_K_M

# Q5_K_M (better quality)
./quantize gpt2-f32.gguf gpt2-Q5_K_M.gguf Q5_K_M

# Q8_0 (best quality)
./quantize gpt2-f32.gguf gpt2-Q8_0.gguf Q8_0

# Compare sizes
echo "Size comparison:"
ls -lh gpt2-*.gguf | awk '{print $5, $9}'
```

## Exercise 3: Run Inference

```bash
# TODO: Run inference with llama.cpp
prompt="The future of artificial intelligence is"

./main -m gpt2-Q4_K_M.gguf \
    --prompt "$prompt" \
    -n 50 \
    --temp 0.7 \
    --top-k 40 \
    --top-p 0.9

# Expected: Generated text
```

## Exercise 4: Benchmark GGUF

```bash
# TODO: Benchmark different quantizations
for quant in f32 Q8_0 Q5_K_M Q4_K_M; do
    echo "Benchmarking $quant..."

    ./main -m gpt2-$quant.gguf \
        --prompt "The capital of France is" \
        -n 20 \
        --time

    echo ""
done

# Compare:
# - Tokens/second
# - Memory usage
# - File size
```

## Exercise 5: Interactive Mode

```bash
# TODO: Interactive chat
./main -m gpt2-Q4_K_M.gguf \
    --color \
    --interactive \
    --reverse-prompt "User:" \
    --prompt \
"User: Hello, how are you?
Assistant:"

# Type your messages and see responses
# Press Ctrl+D to exit
```

## Exercise 6: Python Binding

```python
# TODO: Use llama-cpp-python
pip install llama-cpp-python

from llama_cpp import Llama

# TODO: Load GGUF model
model = Llama(
    model_path="gpt2-Q4_K_M.gguf",
    n_ctx=2048,  # Context window
    n_gpu_layers=-1,  # Offload all to GPU
    verbose=False
)

# TODO: Generate
prompt = "The future of artificial intelligence is"
output = model(prompt, max_tokens=50)
print(f"Generated: {output['choices'][0]['text']}")
```

## Exercise 7: Batch Processing

```python
# TODO: Process multiple prompts
prompts = [
    "The capital of France is",
    "Python is a programming language that",
    "Machine learning is",
]

for prompt in prompts:
    output = model(prompt, max_tokens=30)
    text = output['choices'][0]['text']
    print(f"\nPrompt: {prompt}")
    print(f"Output: {text}")
```

## Exercise 8: GPU Offloading

```python
# TODO: Test different GPU layer counts
import torch

for n_gpu in [0, 10, 20, 30]:
    model = Llama(
        model_path="gpt2-Q4_K_M.gguf",
        n_ctx=512,
        n_gpu_layers=n_gpu,
        verbose=False
    )

    # Benchmark
    import time
    start = time.time()
    _ = model("Test", max_tokens=20)
    elapsed = time.time() - start

    print(f"GPU layers: {n_gpu}, Time: {elapsed:.2f}s")
```

## Expected Outputs

1. Exercise 1: GGUF file created
2. Exercise 2: Quantized files (different sizes)
3. Exercise 3: Generated text
4. Exercise 4: Performance metrics
5. Exercise 5: Interactive chat working
6. Exercise 6: Python binding works
7. Exercise 7: Batch processing working
8. Exercise 8: GPU acceleration visible

## Troubleshooting

**Issue:** Convert.py model not found
```bash
# Solution: Use correct path or download model first
# HuggingFace models use: --model gpt2
# Local models use: --model /path/to/model
```

**Issue:** Quantization too slow
```bash
# Solution: Use threads
export OMP_NUM_THREADS=8
./quantize ...
```

## Extensions

1. Convert Llama-2 or Mistral
2. Try different quantization types
3. Compare GGUF vs EXL2
4. Implement streaming responses

## Time Estimate: 3-4 hours

---
