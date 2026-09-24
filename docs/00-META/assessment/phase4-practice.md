---
Document ID: PHASE4-PRACTICE
Title: "Phase 4: Quantization Practice"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
---

# Phase 4: Quantization Practice

## Hands-On Exercises

### Exercise 1: Implement 4-bit Quantization

```python
import torch
import numpy as np

def quantize_4bit(tensor):
    """Quantize tensor to 4-bit (INT4)"""

    # Find min/max
    min_val = tensor.min().item()
    max_val = tensor.max().item()
    range_val = max_val - min_val

    # Scale to [0, 15]
    scale = range_val / 15.0
    zero_point = min_val

    # Quantize
    quantized = torch.round((tensor - zero_point) / scale).clamp(0, 15).to(torch.uint8)

    return quantized, scale, zero_point

def dequantize_4bit(quantized, scale, zero_point):
    """Dequantize 4-bit tensor"""

    return quantized.to(torch.float32) * scale + zero_point

def test_quantization():
    print("=== 4-bit Quantization Test ===")

    # Create test tensor
    x = torch.randn(1000)

    # Quantize
    x_q, scale, zp = quantize_4_bit(x)

    # Dequantize
    x_dq = dequantize_4bit(x_q, scale, zp)

    # Calculate error
    mse_error = torch.mean((x - x_dq) ** 2).item()

    print(f"Original mean: {x.mean():.4f}")
    print(f"Dequantized mean: {x_dq.mean():.4f}")
    print(f"MSE error: {mse_error:.6f}")
    print(f"Compression: 16x -> 4x memory (4-bit)")

    print("✅ Quantization working!\n")


if __name__ == "__main__":
    test_quantization()
```

### Exercise 2: Compare Quantization Methods

```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

def compare_quantization():
    """Compare different quantization methods"""

    print("=== Quantization Method Comparison ===")

    model_name = "mistralai/Mistral-7B-Instruct-v0.2"

    # FP16 (baseline)
    print("Loading FP16 model...")
    model_fp16 = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    mem_fp16 = model_fp16.get_memory_footprint() / 1e9
    print(f"FP16 Memory: {mem_fp16:.2f} GB")

    # 4-bit quantization
    print("\nLoading 4-bit quantized model...")
    model_4bit = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        ),
        device_map="auto"
    )
    mem_4bit = model_4bit.get_memory_footprint() / 1e9
    print(f"4-bit Memory: {mem_4bit:.2f} GB")

    # Calculate reduction
    reduction = mem_fp16 / mem_4bit
    print(f"\nMemory reduction: {reduction:.2f}x")

    print("✅ Comparison complete!\n")


if __name__ == "__main__":
    compare_quantization()
```

### Exercise 3: Implement KV Cache Quantization

```python
import torch
import torch.nn as nn

class QuantizedKVCache(nn.Module):
    """Quantized KV cache for memory efficiency"""

    def __init__(self, cache_size, num_heads, head_dim, bits=8):
        super().__init__()
        self.cache_size = cache_size
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.bits = bits

        # Initialize cache
        self.register_buffer('k_cache', torch.zeros(cache_size, num_heads, head_dim))
        self.register_buffer('v_cache', torch.zeros(cache_size, num_heads, head_dim))

        # Scaling factors
        self.register_buffer('k_scale', torch.ones(1))
        self.register_buffer('v_scale', torch.ones(1))

    def quantize(self, tensor):
        """Quantize tensor to specified bits"""
        if self.bits == 8:
            return tensor.to(torch.uint8)
        elif self.bits == 4:
            scale = tensor.abs().max() / 7.0
            quantized = torch.clamp((tensor / scale).round().to(torch.int8) + 8, 0, 15)
            return quantized, scale
        return tensor, 1.0

    def dequantize(self, tensor, scale):
        """Dequantize tensor"""
        if self.bits == 4:
            return (tensor.to(torch.float32) - 8) * scale
        return tensor.to(torch.float32)

    def update(self, k, v, position):
        """Update KV cache at position"""

        # Quantize and store
        if self.bits == 4:
            k_q, k_scale = self.quantize(k)
            v_q, v_scale = self.quantize(v)
            self.k_cache[position] = k_q
            self.v_cache[position] = v_q
            self.k_scale = k_scale
            self.v_scale = v_scale
        else:
            self.k_cache[position] = k
            self.v_cache[position] = v


def test_kv_cache():
    print("=== Quantized KV Cache Test ===")

    # Parameters
    cache_size = 128
    num_heads = 4
    head_dim = 64

    # Create quantized cache
    kv_cache = QuantizedKVCache(cache_size, num_heads, head_dim, bits=4)

    # Simulate updates
    for i in range(10):
        k = torch.randn(1, num_heads, head_dim)
        v = torch.randn(1, num_heads, head_dim)
        kv_cache.update(k, v, i)

    print(f"Cache size: {cache_size}")
    print(f"Heads: {num_heads}")
    print(f"Head dim: {head_dim}")
    print(f"Quantization: {kv_cache.bits}-bit")

    # Calculate memory
    memory_fp16 = cache_size * num_heads * head_dim * 2 * 2 / 1e9  # K + V
    memory_4bit = cache_size * num_heads * head_dim * 1 * 2 / 1e9  # 4-bit
    print(f"\nFP16 cache: {memory_fp16:.2f} GB")
    print(f"4-bit cache: {memory_4bit:.2f} GB")
    print(f"Reduction: {memory_fp16 / memory_4bit:.2f}x")

    print("✅ KV cache working!\n")


if __name__ == "__main__":
    test_kv_cache()
```

### Exercise 4: Context Window Extension

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def test_context_window():
    """Test extended context window"""

    print("=== Context Window Extension Test ===")

    model_name = "mistralai/Mistral-7B-Instruct-v0.2"

    # Load model
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Get original context window
    orig_ctx = model.config.max_position_embeddings
    print(f"Original context window: {orig_ctx}")

    # Test with different sequence lengths
    seq_lengths = [512, 1024, 2048, 4096]

    for seq_len in seq_lengths:
        print(f"\nTesting seq_len={seq_len}...")

        # Create input
        text = "Hello " * (seq_len // 6)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        try:
            with torch.no_grad():
                outputs = model(**inputs)

            print(f"  ✅ Success! Output shape: {outputs.logits.shape}")

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}...")

    print("\n✅ Context window test complete!\n")


if __name__ == "__main__":
    test_context_window()
```

---

## Completion Checklist

- [ ] 4-bit quantization implemented
- [ ] Quantization methods compared
- [ ] KV cache quantization working
- [ ] Context window extended
- [ ] Memory usage optimized
- [ ] Speed benchmarks measured
- [ ] Quality metrics validated

---

**Last Updated:** 2026-02-05
