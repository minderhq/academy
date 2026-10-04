---
Document ID: 4203
Title: "4203: Context Window Optimization Guide"
Phase: 4
Module: 4200
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 6 hours
Prerequisites: See module README
Related: See module README
Tags: ['kv-cache', 'context-window', 'speculative-decoding']
---

# 4203: Context Window Optimization Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Context Window Architecture](#context-window-architecture)
- [KV Cache Memory Analysis](#kv-cache-memory-analysis)
- [Implementation 1: KV Cache Quantization](#implementation-1-kv-cache-quantization)
- [Implementation 2: Sliding Window Attention](#implementation-2-sliding-window-attention)
- [Implementation 3: Multi-Round Context Management](#implementation-3-multi-round-context-management)
- [Implementation 4: Streaming with Long Context](#implementation-4-streaming-with-long-context)
- [Implementation 5: Context Chunking Strategy](#implementation-5-context-chunking-strategy)
- [Memory Optimization Strategies](#memory-optimization-strategies)
- [Quick Start](#quick-start)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Place the two context budgets side by side — 4K fp16 7B at ~10 GB (7 weights + 2 KV + 1 activations) vs 32K 4-bit + int8-KV at ~5 GB (3.5 + 0.5 + 1) — and say which knob buys each factor
- Compute KV-cache memory with `calculate_kv_cache_memory` (2 × heads × head_dim × seq × batch × bytes × layers) and read the model table — Llama 2 7B 2.00 GB at 4K fp16 doubling per context doubling, Phi-2 at 1.25 GB (head_dim 80), Mixtral-8x7B at 0.50 GB via its 8 GQA KV heads
- Build `QuantizedKVCache` — int8 storage (1 byte vs fp16's 2) with per-layer `abs().max()/127` scales, `round().clamp(-128, 127)` quantize and scale-multiply dequantize — halving cache VRAM through independent per-layer write positions
- Implement `SlidingWindowAttention` at O(n·w) — windowed mask over the recent window_size tokens plus every-128th history anchor, self-inclusive window slices, cache trimmed to max_cache_size — and read the op-savings table from 1024 to 16384 seq len
- Manage multi-round conversations with `ContextManager` — timestamped, importance-scored `ContextSegment`s compressed at the 0.8 capacity threshold down to summary_ratio 0.3 by keeping the highest-importance segments
- Stream long contexts with `StreamingLLM` — single-token generate loop reusing `past_key_values`, prompt truncation at max_context_tokens, EOS break — and chunk retrieval inputs with `ContextChunker` (1024-token chunks, 128 overlap, token-offset metadata)

---

## Abstract
Practical guide for optimizing context windows in transformer models on an 11GB VRAM GPU. Covers KV cache management, memory optimization, and long-context strategies.

## Context Window Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW MEMORY ANALYSIS                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Standard Model (4K context, 7B params, FP16):                         │
│  ┌────────────────────────────────────────────────────────────────┐       │
│  │  Model Weights:    14 GB (fp32) → 7 GB (fp16)                  │       │
│  │  KV Cache (4K):      ~2 GB (fp16)                               │       │
│  │  Activations:       ~1 GB                                        │       │
│  │  Total:             ~10 GB                                       │       │
│  └────────────────────────────────────────────────────────────────┘       │
│                                                                           │
│  Memory-Optimized Model (32K context, 7B params, 4-bit + FP16):          │
│  ┌────────────────────────────────────────────────────────────────┐       │
│  │  Model Weights:    14 GB (fp32) → 3.5 GB (4-bit)               │       │
│  │  KV Cache (32K):     ~0.5 GB (8-bit quantized)                  │       │
│  │  Activations:       ~1 GB                                        │       │
│  │  Total:             ~5 GB                                        │       │
│  └────────────────────────────────────────────────────────────────┘       │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## KV Cache Memory Analysis

### Memory Calculation Formula

```python
# kv_cache_memory.py
import torch

def calculate_kv_cache_memory(
    num_layers: int,
    num_heads: int,
    head_dim: int,
    seq_len: int,
    batch_size: int = 1,
    bytes_per_element: int = 2,  # FP16 = 2, INT8 = 1
) -> float:
    """
    Calculate KV cache memory usage

    Args:
        num_layers: Number of transformer layers
        num_heads: Number of attention heads
        head_dim: Dimension per head
        seq_len: Sequence length
        batch_size: Batch size
        bytes_per_element: Bytes per element (FP16=2, INT8=1)

    Returns:
        Memory in GB
    """
    # K and V caches per layer
    kv_per_layer = 2 * num_heads * head_dim * seq_len * batch_size * bytes_per_element

    # Total KV cache across all layers
    total_kv = kv_per_layer * num_layers

    # Convert to GB
    return total_kv / (1024**3)


# Analysis for common models
models = {
    "Llama-2-7B": {"layers": 32, "heads": 32, "head_dim": 128},
    "Mistral-7B": {"layers": 32, "heads": 32, "head_dim": 128},
    "Phi-2": {"layers": 32, "heads": 32, "head_dim": 80},
    # Mixtral uses GQA: 8 KV heads per layer, not 32
    "Mixtral-8x7B": {"layers": 32, "heads": 8, "head_dim": 128},
}

print("KV Cache Memory Analysis (Batch Size: 1)")
print("="*70)
print(f"{'Model':<15} | {'4K ctx':<10} | {'8K ctx':<10} | {'16K ctx':<10} | {'32K ctx':<10}")
print("-"*70)

for model_name, config in models.items():
    mem_4k = calculate_kv_cache_memory(
        config["layers"], config["heads"], config["head_dim"], 4096, bytes_per_element=2
    )
    mem_8k = calculate_kv_cache_memory(
        config["layers"], config["heads"], config["head_dim"], 8192, bytes_per_element=2
    )
    mem_16k = calculate_kv_cache_memory(
        config["layers"], config["heads"], config["head_dim"], 16384, bytes_per_element=2
    )
    mem_32k = calculate_kv_cache_memory(
        config["layers"], config["heads"], config["head_dim"], 32768, bytes_per_element=1
    )

    print(f"{model_name:<15} | {mem_4k:<10.2f} | {mem_8k:<10.2f} | {mem_16k:<10.2f} | {mem_32k:<10.2f}")


# Output:
# KV Cache Memory Analysis (Batch Size: 1)
# ======================================================================
# Model           | 4K ctx     | 8K ctx     | 16K ctx    | 32K ctx
# ----------------------------------------------------------------------
# Llama-2-7B      | 2.00       | 4.00       | 8.00       | 8.00
# Mistral-7B      | 2.00       | 4.00       | 8.00       | 8.00
# Phi-2           | 1.25       | 2.50       | 5.00       | 5.00
# Mixtral-8x7B    | 0.50       | 1.00       | 2.00       | 2.00
```

## Implementation 1: KV Cache Quantization

### 8-bit KV Cache

```python
# kv_cache_quantization.py
import torch
import torch.nn as nn


class QuantizedKVCache:
    """
    8-bit quantized KV cache for memory efficiency

    Reduces KV cache memory by 2x with minimal quality loss
    """

    def __init__(self, num_layers: int, num_heads: int, head_dim: int, max_seq_len: int):
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.max_seq_len = max_seq_len

        # Quantized caches (int8)
        self.k_cache = torch.zeros(
            num_layers, max_seq_len, num_heads, head_dim,
            dtype=torch.int8, device="cuda"
        )
        self.v_cache = torch.zeros(
            num_layers, max_seq_len, num_heads, head_dim,
            dtype=torch.int8, device="cuda"
        )

        # Scales for dequantization (per layer)
        self.k_scales = torch.ones(num_layers, dtype=torch.float32, device="cuda")
        self.v_scales = torch.ones(num_layers, dtype=torch.float32, device="cuda")

        # Per-layer write position — all layers fill independently
        self.write_pos = [0] * num_layers

    def update(
        self,
        layer_idx: int,
        k: torch.Tensor,  # (batch, seq_len, heads, head_dim)
        v: torch.Tensor,  # (batch, seq_len, heads, head_dim)
    ):
        """Update KV cache with new keys and values"""

        seq_len = k.shape[1]

        # Calculate scale for this layer
        k_scale = k.abs().max() / 127.0
        v_scale = v.abs().max() / 127.0

        # Quantize to int8
        k_quantized = (k / k_scale).round().clamp(-128, 127).to(torch.int8)
        v_quantized = (v / v_scale).round().clamp(-128, 127).to(torch.int8)

        # Store in cache at this layer's write position
        start = self.write_pos[layer_idx]
        end = start + seq_len

        self.k_cache[layer_idx, start:end] = k_quantized[0]
        self.v_cache[layer_idx, start:end] = v_quantized[0]

        # Store scales
        self.k_scales[layer_idx] = k_scale
        self.v_scales[layer_idx] = v_scale

        self.write_pos[layer_idx] = end

    def get(
        self,
        layer_idx: int,
        start_pos: int = 0,
        end_pos: int | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Retrieve dequantized KV cache"""

        if end_pos is None:
            end_pos = self.write_pos[layer_idx]

        # Get quantized cache
        k = self.k_cache[layer_idx, start_pos:end_pos]  # (seq_len, heads, head_dim)
        v = self.v_cache[layer_idx, start_pos:end_pos]

        # Dequantize
        k_dequant = k.float() * self.k_scales[layer_idx]
        v_dequant = v.float() * self.v_scales[layer_idx]

        return k_dequant, v_dequant


# Usage example
def test_quantized_kv_cache():
    """Test quantized KV cache"""

    print("Testing Quantized KV Cache")
    print("="*60)

    # Create cache
    cache = QuantizedKVCache(
        num_layers=32,
        num_heads=32,
        head_dim=128,
        max_seq_len=8192
    )

    # Simulate attention
    batch_size = 1
    seq_len = 128

    for layer in range(32):
        # Simulate K, V from attention
        k = torch.randn(batch_size, seq_len, 32, 128, device="cuda")
        v = torch.randn(batch_size, seq_len, 32, 128, device="cuda")

        # Update cache
        cache.update(layer, k, v)

    print(f"Cache length: {cache.write_pos[0]}")
    print(f"Memory usage: {cache.k_cache.element_size() * cache.k_cache.nelement() / 1024**2:.1f} MB")

    # Retrieve
    k, v = cache.get(0)
    print(f"Retrieved K shape: {k.shape}")
    print(f"Retrieved V shape: {v.shape}")


if __name__ == "__main__":
    test_quantized_kv_cache()
```

## Implementation 2: Sliding Window Attention

```python
# sliding_window_attention.py
import torch
import torch.nn as nn
import math


class SlidingWindowAttention(nn.Module):
    """
    Sliding window attention for long context

    Only attends to local window + recent tokens
    Reduces compute from O(n²) to O(n*w) where w is window size
    """

    def __init__(
        self,
        dim: int,
        num_heads: int = 32,
        window_size: int = 512,
        max_cache_size: int = 4096,
    ):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5
        self.window_size = window_size
        self.max_cache_size = max_cache_size

        self.qkv = nn.Linear(dim, dim * 3, bias=False)
        self.out = nn.Linear(dim, dim)

    def forward(
        self,
        x: torch.Tensor,
        past_kv: tuple[torch.Tensor, torch.Tensor] | None = None,
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward with sliding window attention

        Args:
            x: Input tensor (batch, seq_len, dim)
            past_kv: Past KV cache ((batch, cache_len, heads, head_dim), same)

        Returns:
            Output and updated KV cache
        """
        batch_size, seq_len, dim = x.shape

        # Compute Q, K, V
        qkv = self.qkv(x).reshape(batch_size, seq_len, 3, self.num_heads, self.head_dim)
        q, k, v = qkv.unbind(2)  # Each: (batch, seq_len, heads, head_dim)

        # Handle past KV
        if past_kv is not None:
            past_k, past_v = past_kv
            k = torch.cat([past_k, k], dim=1)  # (batch, cache_len + seq_len, heads, head_dim)
            v = torch.cat([past_v, v], dim=1)

        cache_len = k.shape[1] - seq_len
        total_len = k.shape[1]

        # Sliding window mask
        # Attend to: window_size recent tokens + every 128th token from history
        mask = torch.ones(batch_size, self.num_heads, seq_len, total_len, device=x.device, dtype=torch.bool)

        for i in range(seq_len):
            pos = cache_len + i

            # Recent tokens (sliding window; pos+1 so the query
            # still attends to its own token)
            window_start = max(0, pos - self.window_size)
            mask[:, :, i, window_start:pos + 1] = False

            # Sparse attention to history (every 128th token)
            for j in range(0, window_start, 128):
                mask[:, :, i, j] = False

        # Compute attention with mask
        attn = (q @ k.transpose(-2, -1)) * self.scale

        # Apply mask
        attn = attn.masked_fill(mask, float('-inf'))
        attn = attn.softmax(dim=-1)

        # Compute output
        out = (attn @ v).transpose(1, 2).reshape(batch_size, seq_len, dim)
        out = self.out(out)

        # Update KV cache
        # Keep only max_cache_size most recent tokens
        if total_len > self.max_cache_size:
            k = k[:, -self.max_cache_size:]
            v = v[:, -self.max_cache_size:]

        return out, (k, v)


# Performance comparison
def compare_attention_methods():
    """Compare sliding window vs full attention"""

    seq_lengths = [1024, 2048, 4096, 8192, 16384]

    print("Attention Method Comparison")
    print("="*70)
    print(f"{'Seq Len':<10} | {'Full Attn':<12} | {'Sliding W':<12} | {'Speedup':<10}")
    print("-"*70)

    for seq_len in seq_lengths:
        # Full attention: O(n²)
        full_ops = seq_len ** 2

        # Sliding window: O(n*w) where w=512
        window_ops = seq_len * 512

        speedup = full_ops / window_ops

        print(f"{seq_len:<10} | {full_ops:<12.0e} | {window_ops:<12.0e} | {speedup:<10.1f}x")


if __name__ == "__main__":
    compare_attention_methods()
```

## Implementation 3: Multi-Round Context Management

```python
# context_management.py
import time

from dataclasses import dataclass
import torch

@dataclass
class ContextSegment:
    """A segment of context with metadata"""
    text: str
    tokens: list[int]
    importance: float
    timestamp: float


class ContextManager:
    """
    Multi-round context manager for long conversations

    Strategies:
    1. Summary compression
    2. Selective retention (keep important)
    3. Sliding window (recent N messages)
    """

    def __init__(
        self,
        max_context_tokens: int = 4096,
        compression_threshold: float = 0.8,  # Compress at 80% capacity
        summary_ratio: float = 0.3,  # Compress to 30% of original
    ):
        self.max_context_tokens = max_context_tokens
        self.compression_threshold = compression_threshold
        self.summary_ratio = summary_ratio

        self.segments: list[ContextSegment] = []
        self.current_tokens = 0

    def add_segment(
        self,
        text: str,
        tokens: list[int],
        importance: float = 0.5,
    ):
        """Add a new context segment"""

        segment = ContextSegment(
            text=text,
            tokens=tokens,
            importance=importance,
            timestamp=time.time()
        )

        self.segments.append(segment)
        self.current_tokens += len(tokens)

        # Check if compression needed
        if self.current_tokens > self.max_context_tokens * self.compression_threshold:
            self.compress()

    def compress(self):
        """Compress context to fit within limits"""

        # Sort by importance (keep most important)
        self.segments.sort(key=lambda x: x.importance, reverse=True)

        # Calculate target size
        target_tokens = int(self.max_context_tokens * self.summary_ratio)

        # Keep most important segments
        kept_tokens = 0
        kept_segments = []

        for segment in self.segments:
            if kept_tokens + len(segment.tokens) > target_tokens:
                break
            kept_segments.append(segment)
            kept_tokens += len(segment.tokens)

        self.segments = kept_segments
        self.current_tokens = kept_tokens

    def get_context(self) -> str:
        """Get formatted context string"""

        return "\n".join([s.text for s in self.segments])

    def get_token_count(self) -> int:
        """Get current token count"""

        return self.current_tokens


# Usage example
def test_context_manager():
    """Test context manager"""

    print("Testing Context Manager")
    print("="*60)

    manager = ContextManager(
        max_context_tokens=1000,
        compression_threshold=0.8,
        summary_ratio=0.3
    )

    # Add segments
    segments = [
        ("User: Hello!", 0.5),
        ("Assistant: Hi! How can I help?", 0.7),
        ("User: Tell me about AI.", 0.8),
        ("Assistant: AI is artificial intelligence...", 0.6),
        ("User: What is machine learning?", 0.9),
        ("Assistant: ML is a subset of AI...", 0.5),
    ]

    for text, importance in segments:
        tokens = text.split()  # Simplified tokenization
        manager.add_segment(text, tokens, importance)

    print(f"Token count: {manager.get_token_count()}")
    print(f"Context:\n{manager.get_context()}")
```

## Implementation 4: Streaming with Long Context

```python
# streaming_long_context.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Iterator

class StreamingLLM:
    """
    Streaming LLM with context management for long inputs

    Automatically manages context window during generation
    """

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        max_context_tokens: int = 4096,
        slide_window_size: int = 512,
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.float16,
            device_map="auto",
        )

        self.max_context_tokens = max_context_tokens
        self.slide_window_size = slide_window_size

        self.past_key_values = None
        self.context_tokens = []

    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: int = 500,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """Stream generation with automatic context management"""

        # Tokenize prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")

        # Check if context is too long
        if input_ids.shape[1] > self.max_context_tokens:
            print(f"Context too long ({input_ids.shape[1]} tokens), truncating...")
            input_ids = input_ids[:, -self.max_context_tokens:]

        generated_tokens = 0

        while generated_tokens < max_new_tokens:
            # Generate with past KV cache
            outputs = self.model.generate(
                input_ids,
                past_key_values=self.past_key_values,
                max_new_tokens=1,
                temperature=temperature,
                use_cache=True,
                return_dict_in_generate=True,
            )

            # Get new token
            new_token = outputs.sequences[0, -1].item()
            new_text = self.tokenizer.decode(new_token)

            yield new_text

            # Update for next iteration
            self.past_key_values = outputs.past_key_values
            input_ids = outputs.sequences[:, -1:]  # Last token only
            generated_tokens += 1

            # Check for EOS
            if new_token == self.tokenizer.eos_token_id:
                break

        # Reset cache
        self.past_key_values = None


# Usage
def test_streaming():
    """Test streaming with long context"""

    llm = StreamingLLM(max_context_tokens=4096)

    long_prompt = "Explain artificial intelligence in detail. " * 100

    print("Streaming response:")
    for chunk in llm.generate_stream(long_prompt, max_new_tokens=100):
        print(chunk, end="", flush=True)

    print()
```

## Implementation 5: Context Chunking Strategy

```python
# context_chunking.py
import tiktoken

class ContextChunker:
    """
    Chunk long context into overlapping segments

    Strategies:
    1. Fixed-size chunks
    2. Semantic chunks (sentence boundaries)
    3. Sliding window chunks
    """

    def __init__(
        self,
        chunk_size: int = 1024,
        overlap: int = 128,
        encoding: str = "cl100k_base",
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = tiktoken.get_encoding(encoding)

    def chunk_text(self, text: str) -> list[str]:
        """Chunk text into overlapping segments"""

        tokens = self.tokenizer.encode(text)

        chunks = []
        start = 0

        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]

            # Decode chunk
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move to next chunk with overlap
            start += (self.chunk_size - self.overlap)

        return chunks

    def chunk_with_metadata(self, text: str) -> list[dict]:
        """Chunk text with metadata for retrieval"""

        tokens = self.tokenizer.encode(text)

        chunks = []
        chunk_id = 0

        start = 0
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]

            chunk_text = self.tokenizer.decode(chunk_tokens)

            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "token_start": start,
                "token_end": end,
                "overlap_start": max(0, start - self.overlap),
            })

            chunk_id += 1
            start += (self.chunk_size - self.overlap)

        return chunks


# Usage
def test_chunking():
    """Test context chunking"""

    chunker = ContextChunker(chunk_size=512, overlap=64)

    long_text = "This is a long text. " * 200

    chunks = chunker.chunk_text(long_text)

    print(f"Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i}: {chunk[:100]}...")
```

## Memory Optimization Strategies

### Strategy Comparison

| Strategy | Memory | Quality | Complexity | Use Case |
|----------|--------|--------|------------|----------|
| **Full Context** | High | Best | Low | Short conversations |
| **Sliding Window** | Low | Medium | Low | Long documents |
| **KV Quantization** | Medium | Good | Medium | Memory-constrained |
| **Context Compression** | Low | Lower | High | Very long context |
| **Sparse Attention** | Medium | Good | High | Long sequences |

### 11GB-class GPU Recommendations

```python
# example_gpu_config.py

# Configuration for an 11GB-class GPU (11GB VRAM)

CONFIG = {
    "model": "mistralai/Mistral-7B-Instruct-v0.2",

    # Quantization
    "load_in_4bit": True,  # Reduce model VRAM to ~4GB
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_quant_type": "nf4",

    # Context
    "max_model_len": 8192,  # Maximum with 4-bit + 8-bit KV
    "max_new_tokens": 512,

    # KV Cache - there is no model-load flag for this; a quantized
    # cache is a per-generate() setting in transformers:
    #   model.generate(..., cache_implementation="quantized",
    #                  cache_config={"nbits": 8, "backend": "hqq"})

    # Attention
    "use_flash_attention_2": True,  # Faster attention
    "sliding_window": 512,  # If context > 4K

    # Memory
    "gpu_memory_utilization": 0.85,  # Leave room for KV cache
}

# Expected memory breakdown:
# - Model weights (4-bit): 3.5 GB
# - KV cache (8K tokens, 8-bit): 2 GB
# - Activations: 1 GB
# - Total: ~6.5 GB
# - Available for batching: ~4.5 GB
```

## Quick Start

```bash
# 1. Install dependencies
uv pip install transformers accelerate bitsandbytes

# 2. Run with long context
python long_context_example.py

# 3. Monitor memory usage
nvidia-smi -l 1

# 4. Adjust based on VRAM usage
# - If OOM: reduce max_model_len or enable 8-bit KV
# - If underutilized: increase max_model_len or batch size
```


---

## Summary

Long context on an 11GB card is a budgeting exercise, and this guide is its workbook: KV cache arithmetic first, then five concrete implementations - quantizing the KV cache, sliding-window attention, multi-round context management, streaming with long context, and context chunking - each trading context reach against VRAM. The memory-optimization strategies section ties them together and the quick start gets a working pipeline running before the theory matters. The through-line: you rarely get more context for free - you choose which of these five taxes to pay, then measure the bill.

## References

### Related Minder Academy Documents

- [4201: Context Window Physics and OOM Prevention](../4201-Context-Window-Physics.md)
- [4202: Speculative Decoding - Accelerating Large Models](../4202-Speculative-Decoding.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**

---

**Related:**
- [4201: Context Window Physics](../4201-Context-Window-Physics.md)
- [4202: Speculative Decoding](../4202-Speculative-Decoding.md)
- [4101: GGUF Physics](../../4100-low-bit/4101-GGUF-Physics.md)
- [1402: vLLM and TGI](../../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [EXP_4201: Context Window](../../../../../experiments/EXP_4201_CONTEXT_WINDOW.md)
