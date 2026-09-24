---
Document ID: 4201
Title: Context Window Physics and OOM Prevention
Phase: 4
Module: 4200
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'kv-cache', 'context-window', 'speculative-decoding']
---

# 4201: Context Window Physics and OOM Prevention

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [KV Cache Memory Analysis](#kv-cache-memory-analysis)
- [KV Cache Quantization](#kv-cache-quantization)
- [Multi-Round Attention](#multi-round-attention)
- [Context Window Extension](#context-window-extension)
- [OOM Prevention Strategies](#oom-prevention-strategies)
- [Memory Optimization Techniques](#memory-optimization-techniques)
- [Monitoring KV Cache](#monitoring-kv-cache)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain KV Cache Memory Analysis
- Explain KV Cache Quantization
- Explain Multi-Round Attention
- Explain Context Window Extension
- Explain OOM Prevention Strategies
- Explain Memory Optimization Techniques

---

## Abstract
The context window determines how much text the model can "remember" during inference. Understanding KV cache memory physics is essential for preventing OOM (Out of Memory) errors when extending context length.

## KV Cache Memory Analysis

### What is KV Cache?
```yaml
During autoregressive generation, we cache:
- K (Key): What each position offers
- V (Value): The actual content at each position

This avoids recomputing attention for previous tokens!

Generation:
Token 0: Compute K[0], V[0] (cache them)
Token 1: Compute K[1], V[1]; use cached K[0], V[0]
Token 2: Compute K[2], V[2]; use cached K[0:2], V[0:2]
...
```

### Memory Calculation
```python
def calculate_kv_cache_memory(
    num_layers,
    num_heads,
    head_dim,
    seq_len,
    bytes_per_value=2  # fp16
):
    """
    Calculate KV cache memory requirements

    K and V are cached separately:
    - Shape: (batch, num_layers, num_heads, seq_len, head_dim)
    - Memory: 2 × batch × layers × heads × seq_len × dim × bytes
    """
    # Per layer
    per_layer = 2 * num_heads * seq_len * head_dim * bytes_per_value

    # Total
    total_memory = num_layers * per_layer

    return total_memory

# Example: Llama-2-7B
memory = calculate_kv_cache_memory(
    num_layers=32,
    num_heads=32,
    head_dim=128,  # 4096 / 32
    seq_len=4096,
    bytes_per_value=2,  # fp16
)

print(f"KV Cache: {memory / (1024**3):.2f} GB")
# Output: KV Cache: 2.00 GB
```

### Memory Breakdown
```text
Llama-2-7B KV Cache @ 4096 context:

Component               Memory
──────────────────────────────────────
Model weights (fp16)    14 GB
KV Cache (fp16)          2 GB
Activations             1 GB
──────────────────────────────────────
Total                   17 GB

Problem: an 11GB GPU has only 11 GB!
Solution: Quantize KV cache
```

## KV Cache Quantization

### 8-bit KV Cache
```python
# Quantize K and V to 8-bit
# Saves 50% memory with minimal quality loss

from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    load_in_8bit=True,  # Model weights
    quantization_config={
        "kv_cache_quantization": "int8",  # KV cache
    }
)

# Memory breakdown:
# Model (8-bit):    7 GB
# KV Cache (8-bit):  1 GB
# Activations:       1 GB
# Total:             9 GB ✓ (fits!)
```

### 4-bit KV Cache
```python
# More aggressive: 4-bit KV cache
# Saves 75% memory, some quality loss

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,

    # KV cache quantization
    llm_int8_threshold=6.0,
    llm_int8_has_fp16_weight=False,
    quantization_type="4bit",
)

# Memory breakdown:
# Model (4-bit):    3.5 GB
# KV Cache (4-bit):  0.5 GB
# Activations:       1 GB
# Total:             5 GB ✓ (plenty of room!)
```

## Multi-Round Attention

### Sliding Window Cache
```python
class SlidingWindowKVCache:
    """
    Only keep recent N tokens in cache
    Trade memory for limited context
    """
    def __init__(self, window_size=2048):
        self.window_size = window_size
        self.cache = {}

    def update(self, layer_idx, key, value, position):
        if layer_idx not in self.cache:
            self.cache[layer_idx] = {'k': [], 'v': []}

        cache = self.cache[layer_idx]

        # Add new tokens
        cache['k'].append(key)
        cache['v'].append(value)

        # Remove old tokens beyond window
        if len(cache['k']) > self.window_size:
            cache['k'].pop(0)
            cache['v'].pop(0)

    def get(self, layer_idx):
        if layer_idx in self.cache:
            return (
                torch.cat(self.cache[layer_idx]['k'], dim=-2),
                torch.cat(self.cache[layer_idx]['v'], dim=-2)
            )
        return None, None

# Memory usage: constant regardless of total sequence length!
# Memory = window_size × model_dim × layers × 2
```

### Chunked Attention
```python
def chunked_attention(query, key, value, chunk_size=1024):
    """
    Compute attention in chunks to reduce peak memory
    """
    seq_len = query.size(1)
    outputs = []

    for i in range(0, seq_len, chunk_size):
        # Process chunk
        q_chunk = query[:, i:i+chunk_size, :]

        # Only attend to previous chunks + current chunk
        end = min(i + chunk_size, seq_len)
        k_context = key[:, :end, :]
        v_context = value[:, :end, :]

        # Compute attention
        scores = torch.matmul(q_chunk, k_context.transpose(-2, -1))
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, v_context)

        outputs.append(output)

    return torch.cat(outputs, dim=1)

# Peak memory: O(chunk_size²) instead of O(seq_len²)
```

## Context Window Extension

### Position Interpolation
```python
def extend_context_with_interpolation(
    model,
    original_max_len=2048,
    target_max_len=8192
):
    """
    Extend context window by interpolating RoPE positions
    """
    # Scale factor
    scale = original_max_len / target_max_len

    # Modify model's RoPE scaling
    for layer in model.model.layers:
        # Access rotary embedding
        rope = layer.self_attn.rotary_emb

        # Scale frequencies
        rope.inv_freq = rope.inv_freq * scale

    return model

# Now model can handle 8192 context!
# Memory: KV cache grows by 4x (but quality remains good)
```

### YaRN Scaling
```python
# Yet another RoPE extensioN
# Better than simple interpolation

def yarn_scaling(model, target_context=8192, original_context=2048):
    """
    YaRN: NTK-aware scaling for extended context
    """
    scale = (target_context / original_context) ** (0.5 * model.config.num_attention_heads / (model.config.num_attention_heads - 2))

    for layer in model.model.layers:
        rope = layer.self_attn.rotary_emb
        # Modified base frequency calculation
        rope.inv_freq = 1.0 / (10000 ** (torch.arange(0, model.config.hidden_size, 2).float() / model.config.hidden_size)) * scale

    return model
```

## OOM Prevention Strategies

### Dynamic KV Cache Eviction
```python
class DynamicKVCache:
    """
    Dynamically evict less important KV pairs
    """
    def __init__(self, max_tokens=4096, eviction_ratio=0.1):
        self.max_tokens = max_tokens
        self.eviction_ratio = eviction_ratio
        self.cache = {}
        self.importance = {}

    def update(self, layer_idx, key, value, attention_weights):
        """
        Track importance via attention weights
        """
        if layer_idx not in self.cache:
            self.cache[layer_idx] = {'k': [], 'v': []}
            self.importance[layer_idx] = []

        # Add new
        self.cache[layer_idx]['k'].append(key)
        self.cache[layer_idx]['v'].append(value)
        self.importance[layer_idx].append(attention_weights.mean().item())

        # Evict if over limit
        total_tokens = sum(len(k) for k in self.cache[layer_idx]['k'])
        if total_tokens > self.max_tokens:
            # Find least important tokens
            num_to_evict = int(self.max_tokens * self.eviction_ratio)
            indices = self._get_least_important(layer_idx, num_to_evict)

            # Evict
            for idx in sorted(indices, reverse=True):
                self.cache[layer_idx]['k'].pop(idx)
                self.cache[layer_idx]['v'].pop(idx)
                self.importance[layer_idx].pop(idx)

    def _get_least_important(self, layer_idx, n):
        """Return indices of n least important tokens"""
        return sorted(range(len(self.importance[layer_idx])),
                     key=lambda i: self.importance[layer_idx][i])[:n]
```

### Gradient Checkpointing (for training)
```python
# Save memory by recomputing activations
from torch.utils.checkpoint import checkpoint

class CheckpointedTransformerBlock(nn.Module):
    def forward(self, x):
        # Don't store intermediate activations
        def run_block(x):
            return self.attn(self.norm1(x)) + x

        # Recompute during backward
        return checkpoint(run_block, x)

# Saves ~50% activation memory
# Cost: ~20% slower training
```

## Memory Optimization Techniques

### Shared KV Cache
```python
# For batch inference, share KV cache when prompts are similar

class SharedKVCache:
    def __init__(self):
        self.shared_cache = {}  # hash → KV cache
        self.ref_count = {}     # hash → count

    def get_or_create(self, prompt_hash, compute_fn):
        if prompt_hash in self.shared_cache:
            self.ref_count[prompt_hash] += 1
            return self.shared_cache[prompt_hash]

        # Compute and cache
        kv_cache = compute_fn()
        self.shared_cache[prompt_hash] = kv_cache
        self.ref_count[prompt_hash] = 1
        return kv_cache

    def release(self, prompt_hash):
        self.ref_count[prompt_hash] -= 1
        if self.ref_count[prompt_hash] == 0:
            del self.shared_cache[prompt_hash]
            del self.ref_count[prompt_hash]
```

### Flash Attention with KV Cache
```python
# Flash Attention + KV Cache = Long context + Low memory

from flash_attn import flash_attn_with_kvcache

def generate_with_flash_cache(model, input_ids, max_new_tokens=100):
    """
    Generate using Flash Attention with KV cache
    """
    # First pass: compute all KVs
    with torch.no_grad():
        outputs = model.model(input_ids, use_cache=True)
        past_key_values = outputs.past_key_values

    # Subsequent passes: reuse cache
    generated = input_ids
    for _ in range(max_new_tokens):
        # Only compute for new token
        with torch.no_grad():
            outputs = model.model(
                generated[:, -1:],
                past_key_values=past_key_values,
                use_cache=True
            )

        past_key_values = outputs.past_key_values
        next_token = outputs.logits[:, -1:].argmax(dim=-1)
        generated = torch.cat([generated, next_token], dim=-1)

    return generated

# Much more efficient than standard caching!
```

## Monitoring KV Cache

### Track Memory Usage
```python
import torch

def track_kv_cache_memory(model):
    """
    Monitor KV cache memory during inference
    """
    if not hasattr(model, '_kv_cache_tracker'):
        model._kv_cache_tracker = {
            'peak_memory': 0,
            'current_memory': 0,
        }

    # Check past_key_values if present
    if hasattr(model, 'past_key_values') and model.past_key_values is not None:
        total_elements = sum(
            kv[0].numel() + kv[1].numel()
            for layer_kv in model.past_key_values
            for kv in layer_kv
        )

        # fp16 = 2 bytes
        current_memory = total_elements * 2
        model._kv_cache_tracker['current_memory'] = current_memory
        model._kv_cache_tracker['peak_memory'] = max(
            model._kv_cache_tracker['peak_memory'],
            current_memory
        )

    return model._kv_cache_tracker

# Usage during generation
tracker = track_kv_cache_memory(model)
print(f"Current KV Cache: {tracker['current_memory'] / (1024**3):.2f} GB")
print(f"Peak KV Cache: {tracker['peak_memory'] / (1024**3):.2f} GB")
```

---

## References

### Related ai-engineering-curriculum Documents

- [4202: Speculative Decoding - Accelerating Large Models](4202-Speculative-Decoding.md)

---

## Next Steps

- Continue with: **[4202: Speculative Decoding](./4202-Speculative-Decoding.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [4202: Speculative Decoding](./4202-Speculative-Decoding.md)
- [4101: GGUF Physics](../4100-low-bit/4101-GGUF-Physics.md)
- [3102: Flash Attention](../../phase3-transformers/3100-attention/3102-Flash-Attention.md)

**Experiment Template:** `experiments/EXP_4201_CONTEXT.md`
