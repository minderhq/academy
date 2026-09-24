# 4200: KV Cache Optimization - Practice

## Exercises

### Exercise 1: Implement Basic KV Cache

```python
import torch
import torch.nn as nn

class KVCache:
    """Key-Value cache for efficient transformer inference."""

    def __init__(self, batch_size, num_heads, head_dim, max_len, dtype=torch.float16):
        self.batch_size = batch_size
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.max_len = max_len
        self.dtype = dtype

        # Initialize cache tensors
        self.key_cache = torch.zeros(
            (batch_size, num_heads, max_len, head_dim),
            dtype=dtype,
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )
        self.value_cache = torch.zeros(
            (batch_size, num_heads, max_len, head_dim),
            dtype=dtype,
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )
        self.current_len = 0

    def update(self, new_keys, new_values):
        """
        Update cache with new keys and values.

        Args:
            new_keys: (batch, num_heads, seq_len, head_dim)
            new_values: (batch, num_heads, seq_len, head_dim)

        Returns:
            Cached keys and values up to current position
        """
        seq_len = new_keys.size(2)

        # Update position
        start_pos = self.current_len
        end_pos = start_pos + seq_len

        if end_pos > self.max_len:
            raise ValueError(f"Cache overflow: {end_pos} > {self.max_len}")

        # Update cache
        self.key_cache[:, :, start_pos:end_pos, :] = new_keys
        self.value_cache[:, :, start_pos:end_pos, :] = new_values

        self.current_len += seq_len

        # Return cached keys/values
        return (
            self.key_cache[:, :, :self.current_len, :],
            self.value_cache[:, :, :self.current_len, :]
        )

    def reset(self):
        """Reset cache for new sequence."""
        self.current_len = 0
        self.key_cache.zero_()
        self.value_cache.zero_()

    def get_cache(self):
        """Get current cached keys and values."""
        return (
            self.key_cache[:, :, :self.current_len, :],
            self.value_cache[:, :, :self.current_len, :]
        )

# Test KV Cache
print("Testing KV Cache Implementation")
print("="*60)

cache = KVCache(batch_size=1, num_heads=4, head_dim=64, max_len=100)

# Simulate processing tokens in chunks
chunk_size = 10
num_chunks = 5

for i in range(num_chunks):
    # Simulate new keys and values
    new_keys = torch.randn(1, 4, chunk_size, 64)
    new_values = torch.randn(1, 4, chunk_size, 64)

    # Update cache
    cached_keys, cached_values = cache.update(new_keys, new_values)

    print(f"Chunk {i+1}: Cache length = {cache.current_len}")

# Verify cache
print(f"\nFinal cache length: {cache.current_len}")
print(f"Key cache shape: {cached_keys.shape}")
print(f"Value cache shape: {cached_values.shape}")

# Expected Output:
# Cache grows with each chunk
# Final length = 50 (5 chunks * 10 tokens)
```

**Explanation:**
- KV cache stores computed keys and values during generation
- Avoids recomputing for all previous tokens at each step
- Essential for efficient autoregressive generation
- Reduces complexity from O(n²) to O(n)

**Memory Usage:**
- Proportional to batch_size × num_heads × seq_len × head_dim
- For a 7B model: ~2-3 GB for 2K sequence length

---

### Exercise 2: Multi-Query Attention with KV Cache

```python
class MultiQueryAttentionWithCache(nn.Module):
    """Multi-Query Attention with KV cache support."""

    def __init__(self, d_model, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.d_head = d_model // n_heads

        # Separate projections for Q, K, V
        self.q_proj = nn.Linear(d_model, n_heads * self.d_head)
        self.k_proj = nn.Linear(d_model, self.d_head)  # Single head for K
        self.v_proj = nn.Linear(d_model, self.d_head)  # Single head for V
        self.out_proj = nn.Linear(n_heads * self.d_head, d_model)

        self.scale = self.d_head ** -0.5

    def forward(self, x, kv_cache=None):
        """
        Args:
            x: (batch, seq_len, d_model)
            kv_cache: Optional KVCache instance

        Returns:
            (batch, seq_len, d_model)
        """
        batch_size, seq_len, _ = x.shape

        # Project Q, K, V
        q = self.q_proj(x).view(batch_size, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        k = self.k_proj(x).view(batch_size, seq_len, 1, self.d_head).transpose(1, 2)
        v = self.v_proj(x).view(batch_size, seq_len, 1, self.d_head).transpose(1, 2)

        # Update cache if provided
        if kv_cache is not None:
            k, v = kv_cache.update(k, v)

        # Expand K, V to all heads
        k = k.expand(-1, self.n_heads, -1, -1)
        v = v.expand(-1, self.n_heads, -1, -1)

        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, v)

        # Reshape and project
        output = output.transpose(1, 2).contiguous().view(batch_size, seq_len, -1)
        return self.out_proj(output)

# Test
print("\nTesting Multi-Query Attention with Cache")
print("="*60)

d_model = 256
n_heads = 4
seq_len = 10
batch_size = 1

mqa = MultiQueryAttentionWithCache(d_model, n_heads)
cache = KVCache(batch_size, n_heads, d_model // n_heads, max_len=100)

# Process in chunks
for i in range(3):
    x = torch.randn(batch_size, 5, d_model)
    output = mqa(x, kv_cache=cache)
    print(f"Chunk {i+1}: Output shape = {output.shape}, Cache length = {cache.current_len}")

# Expected Output:
# Each chunk processes new tokens
# Cache accumulates across chunks
# Multi-query uses single K/V for all heads (memory efficient)
```

**Explanation:**
- Multi-Query Attention (MQA): Single key/value head for all query heads
- Reduces cache size by factor of num_heads
- Used in PaLM, LLaMA 2, and other modern LLMs
- Trade-off: Slight quality decrease for significant memory savings

**Benefits:**
- Cache size: O(batch × seq_len × head_dim) instead of O(batch × num_heads × seq_len × head_dim)
- Faster inference due to reduced memory bandwidth
- Enables longer sequences and larger batch sizes

---

### Exercise 3: Cache Size Calculation

```python
def calculate_cache_memory(model_config, batch_size=1, seq_len=2048):
    """
    Calculate memory usage for KV cache.

    Args:
        model_config: Dictionary with model configuration
        batch_size: Batch size
        seq_len: Sequence length

    Returns:
        Memory usage in GB
    """
    n_layers = model_config.get('num_hidden_layers', 32)
    n_heads = model_config.get('num_attention_heads', 32)
    head_dim = model_config.get('hidden_size', 4096) // n_heads
    bytes_per_param = 2  # FP16

    # Single layer cache (K + V)
    cache_size_per_layer = (
        2 *  # K and V
        batch_size *
        n_heads *
        seq_len *
        head_dim *
        bytes_per_param
    )

    # Total cache size (all layers)
    total_cache_size = cache_size_per_layer * n_layers

    return total_cache_size / (1024**3)  # Convert to GB

# Calculate cache sizes for different models
models = {
    'GPT-2 Small': {'num_hidden_layers': 12, 'num_attention_heads': 12, 'hidden_size': 768},
    'GPT-2 Medium': {'num_hidden_layers': 24, 'num_attention_heads': 16, 'hidden_size': 1024},
    'GPT-2 Large': {'num_hidden_layers': 36, 'num_attention_heads': 20, 'hidden_size': 1280},
    'LLaMA-7B': {'num_hidden_layers': 32, 'num_attention_heads': 32, 'hidden_size': 4096},
    'LLaMA-13B': {'num_hidden_layers': 40, 'num_attention_heads': 40, 'hidden_size': 5120},
    'LLaMA-70B': {'num_hidden_layers': 80, 'num_attention_heads': 64, 'hidden_size': 8192},
}

print("KV Cache Memory Usage (Batch=1, Seq=2048)")
print("="*60)
print(f"{'Model':<20} {'Cache (GB)':<15}")
print("-" * 60)

for model_name, config in models.items():
    cache_gb = calculate_cache_memory(config, batch_size=1, seq_len=2048)
    print(f"{model_name:<20} {cache_gb:<15.2f}")

print("\n\nCache Memory vs Sequence Length (LLaMA-7B)")
print("="*60)

seq_lengths = [512, 1024, 2048, 4096, 8192, 16384]
for seq_len in seq_lengths:
    cache_gb = calculate_cache_memory(models['LLaMA-7B'], batch_size=1, seq_len=seq_len)
    print(f"Seq {seq_len:>5}: {cache_gb:>8.2f} GB")

# Expected Output:
# Cache grows linearly with sequence length
# LLaMA-7B at 2K: ~2 GB
# LLaMA-70B at 2K: ~8 GB
```

---

### Exercise 4: Streaming Generation with Cache

```python
def generate_with_cache(model, tokenizer, prompt, max_new_tokens=100):
    """
    Generate text with KV cache for efficiency.

    Args:
        model: Language model
        tokenizer: Tokenizer
        prompt: Input prompt
        max_new_tokens: Maximum tokens to generate

    Returns:
        Generated text
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Note: This is a simplified example
    # In practice, use model.generate() with use_cache=True
    print(f"Prompt: \"{prompt}\"")
    print(f"Generating {max_new_tokens} tokens...")

    # Using Hugging Face's built-in cache support
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return text

# Example usage
"""
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "gpt2"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

prompt = "Once upon a time"
generated = generate_with_cache(model, tokenizer, prompt, max_new_tokens=50)

print(f"\nGenerated text:\n{generated}")
"""

print("\nKey Benefits of KV Cache:")
print("="*60)
print("""
1. Speed: O(n) instead of O(n²) for generation
2. Memory: Reuse computations across tokens
3. Scalability: Enables longer sequences
4. Efficiency: Critical for production deployment

Implementation Tips:
- Use FP16 for cache (half the memory)
- Consider multi-query attention for efficiency
- Monitor memory usage during generation
- Clear cache between independent requests
""")
```

---

## Summary: KV Cache Optimization

```
KV CACHE IMPACT:

Without Cache:
  - Complexity: O(n²) per generated token
  - Memory: O(n) per step
  - Speed: Slow for long sequences

With Cache:
  - Complexity: O(1) per generated token (after prompt)
  - Memory: O(n) total
  - Speed: Much faster generation

OPTIMIZATION TECHNIQUES:

1. Multi-Query Attention (MQA)
   - Single K/V head for all query heads
   - Reduces cache size by num_heads
   - Used in LLaMA 2, PaLM

2. Grouped-Query Attention (GQA)
   - Intermediate between MHA and MQA
   - Balance between quality and speed
   - k query heads share 1 key/value head

3. Flash Attention
   - Memory-efficient attention
   - Faster computation
   - Better cache utilization

4. Paged Attention
   - vLLM-style block management
   - Dynamic cache allocation
   - Enables variable batch sizes

PRACTICAL TIPS:
- Use cache for all autoregressive generation
- Monitor memory at longer sequence lengths
- Consider KV cache quantization (8-bit)
- Use FP16/BF16 for cache storage
- Implement cache eviction for streaming
```

---

**Last Updated:** 2026-02-05
