# LAB-401: Post-Training Quantization (PTQ)

## Overview
Learn post-training quantization techniques to compress LLMs.

## Prerequisites
- LAB-201 completed
- Understanding of quantization basics
- ~16GB GPU memory recommended

## Setup

```bash
pip install torch transformers accelerate bitsandbytes
```

## Exercise 1: Load Model in Different Precisions

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "gpt2"  # Smaller model for testing

# TODO: Load in FP32
model_fp32 = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Check memory
print(f"FP32 Model: {model_fp32.get_memory_footprint() / 1e9:.2f} GB")

# TODO: Load in FP16
model_fp16 = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16
)
print(f"FP16 Model: {model_fp16.get_memory_footprint() / 1e9:.2f} GB")

# TODO: Load in INT8 (using bitsandbytes)
model_int8 = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_8bit=True,
    device_map="auto"
)
print(f"INT8 Model: ~{model_fp32.get_memory_footprint() / 1e9 / 4:.2f} GB")
```

## Exercise 2: 4-bit Quantization

```python
from transformers import BitsAndBytesConfig

# TODO: Configure 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model_4bit = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)

print(f"4-bit Model: ~{model_fp32.get_memory_footprint() / 1e9 / 8:.2f} GB")
```

## Exercise 3: Compare Generation Quality

```python
import time

def benchmark_generation(model, tokenizer, prompt, max_new_tokens=50):
    """Benchmark generation speed and quality."""

    # Warmup
    _ = model.generate(**tokenizer(prompt, return_tensors="pt"), max_new_tokens=10)

    # Benchmark
    start = time.time()
    outputs = model.generate(
        **tokenizer(prompt, return_tensors="pt"),
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7
    )
    end = time.time()

    text = tokenizer.decode(outputs[0])
    tokens_per_sec = max_new_tokens / (end - start)

    return text, tokens_per_sec

# Test prompt
prompt = "The future of artificial intelligence is"

# TODO: Benchmark each precision
for name, model in [("FP32", model_fp32), ("FP16", model_fp16), ("INT8", model_int8), ("4-bit", model_4bit)]:
    text, tps = benchmark_generation(model, tokenizer, prompt)
    print(f"\n{name}:")
    print(f"  Speed: {tps:.2f} tokens/sec")
    print(f"  Output: {text[:100]}...")
```

## Exercise 4: Quantization Aware Training (QAT) Simulation

```python
from torch.ao.quantization import prepare_qat, convert

# Simple model to quantize
class TinyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 20)
        self.fc2 = nn.Linear(20, 10)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        return self.fc2(x)

# TODO: Prepare QAT
model = TinyModel()
model.qconfig = torch.ao.quantization.get_default_qat_qconfig('x86')
model = prepare_qat(model)

# TODO: Train (simulation)
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
for epoch in range(10):
    # Dummy training
    x = torch.randn(32, 10)
    loss = model(x).sum()
    loss.backward()
    optimizer.step()

# TODO: Convert to INT8
model_int8 = convert(model.eval())
print("Model converted to INT8")
```

## Exercise 5: Export to GGUF (Optional)

```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Convert to GGUF
python convert.py \
    --model ../gpt2 \
    --outfile gpt2-Q4_K_M.gguf \
    --outtype q4_k_m

# Run inference
./main -m gpt2-Q4_K_M.gguf \
    --prompt "The future of AI is" \
    -n 50
```

## Expected Outputs

1. Exercise 1: Memory reduction FP32 → FP16 → INT8 → 4-bit
2. Exercise 2: 4-bit model loaded successfully
3. Exercise 3: Speed comparison: 4-bit > INT8 > FP16 > FP32
4. Exercise 4: QAT model converted
5. Exercise 5: GGUF file created

## Troubleshooting

**Issue:** bitsandbytes not available on CPU
```python
# Solution: Use CPU or CUDA
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
```

**Issue:** Model generation too slow
```python
# Solution: Use smaller model or batch
model = AutoModelForCausalLM.from_pretrained("gpt2",  # Instead of large model
```

## Extensions

1. Try different quantization types (NF4, FP4)
2. Benchmark on larger model (Llama-2-7B)
3. Implement custom quantization
4. Compare GGUF vs EXL2

## Time Estimate: 4-5 hours

---

**Last Updated:** 2026-02-04
