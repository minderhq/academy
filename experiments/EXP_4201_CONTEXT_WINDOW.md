# EXP_4201: Context Window Physics Experiments

## Overview
Practical experiments for understanding KV cache, context window limits, and OOM prevention on RTX 2080 Ti (11GB VRAM).

## Experiment 1: KV Cache Memory Analysis

### Objective
Measure KV cache memory usage at different context lengths.

### Analysis Script
```python
# kv_cache_analysis.py
import torch
import torch.nn as nn
from dataclasses import dataclass
from typing import Optional, Tuple
import matplotlib.pyplot as plt

@dataclass
class KVCacheEntry:
    """KV Cache entry"""
    k: torch.Tensor  # (batch, heads, seq_len, head_dim)
    v: torch.Tensor  # (batch, heads, seq_len, head_dim)


class KVCache:
    """KV Cache for efficient autoregressive generation"""

    def __init__(self, batch_size: int, num_heads: int, head_dim: int,
                 max_len: int, dtype: torch.dtype = torch.float16):
        self.batch_size = batch_size
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.max_len = max_len
        self.dtype = dtype

        # Pre-allocate cache
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.k_cache = torch.zeros(
            batch_size, num_heads, max_len, head_dim,
            dtype=dtype, device=device
        )
        self.v_cache = torch.zeros(
            batch_size, num_heads, max_len, head_dim,
            dtype=dtype, device=device
        )
        self.seq_len = 0

    def update(self, k: torch.Tensor, v: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Update cache with new key/value pairs

        Args:
            k: (batch, heads, new_tokens, head_dim)
            v: (batch, heads, new_tokens, head_dim)
        Returns:
            k_cache, v_cache: (batch, heads, total_seq_len, head_dim)
        """
        new_tokens = k.shape[2]

        # Copy to cache
        self.k_cache[:, :, self.seq_len:self.seq_len + new_tokens, :] = k
        self.v_cache[:, :, self.seq_len:self.seq_len + new_tokens, :] = v

        self.seq_len += new_tokens

        return self.k_cache[:, :, :self.seq_len, :], self.v_cache[:, :, :self.seq_len, :]

    def clear(self):
        """Clear cache"""
        self.seq_len = 0
        self.k_cache.zero_()
        self.v_cache.zero_()

    def get_memory_usage(self) -> dict:
        """Get current memory usage"""
        element_size = 2 if self.dtype == torch.float16 else 4  # bytes
        total_elements = (
            self.k_cache.numel() + self.v_cache.numel()
        )
        total_bytes = total_elements * element_size

        return {
            "batch_size": self.batch_size,
            "num_heads": self.num_heads,
            "head_dim": self.head_dim,
            "max_len": self.max_len,
            "seq_len": self.seq_len,
            "total_mb": total_bytes / (1024 ** 2),
            "total_gb": total_bytes / (1024 ** 3),
            "elements_per_token": 2 * self.num_heads * self.head_dim,  # K + V
        }


def analyze_kv_cache_memory():
    """Analyze KV cache memory usage at different configurations"""

    print("KV Cache Memory Analysis")
    print("="*70)

    # Common model configurations
    configs = [
        {"name": "Llama-2-7B", "layers": 32, "heads": 32, "head_dim": 128},
        {"name": "Mistral-7B", "layers": 32, "heads": 32, "head_dim": 128},
        {"name": "Llama-2-13B", "layers": 40, "heads": 40, "head_dim": 128},
        {"name": "Mixtral-8x7B", "layers": 32, "heads": 32, "head_dim": 128},
    ]

    batch_size = 1
    context_lengths = [512, 1024, 2048, 4096, 8192, 16384, 32768]

    results = {}

    for config in configs:
        model_name = config["name"]
        num_layers = config["layers"]
        heads = config["heads"]
        head_dim = config["head_dim"]

        print(f"\n{model_name}:")
        print(f"  Layers: {num_layers}, Heads: {heads}, Head Dim: {head_dim}")

        results[model_name] = []

        for ctx_len in context_lengths:
            # Calculate KV cache size per layer
            cache = KVCache(batch_size, heads, head_dim, ctx_len)
            mem = cache.get_memory_usage()

            # Total for all layers
            total_mb = mem["total_mb"] * num_layers
            total_gb = total_mb / 1024

            # Elements per token across all layers
            elements_per_token = mem["elements_per_token"] * num_layers
            bytes_per_token = elements_per_token * 2  # FP16

            results[model_name].append({
                "ctx_len": ctx_len,
                "total_mb": total_mb,
                "total_gb": total_gb,
                "bytes_per_token": bytes_per_token,
            })

            status = "✓" if total_gb < 11 else "✗"
            print(f"  {status} ctx={ctx_len:5d}: {total_gb:6.2f} GB ({bytes_per_token} bytes/token)")

    # Plot results
    plot_kv_cache_memory(results, context_lengths)

    return results


def plot_kv_cache_memory(results: dict, context_lengths: list):
    """Plot KV cache memory usage"""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Memory vs context length
    for model_name, data in results.items():
        ctx_lens = [d["ctx_len"] for d in data]
        mem_gb = [d["total_gb"] for d in data]
        ax1.plot(ctx_lens, mem_gb, 'o-', label=model_name, linewidth=2)

    ax1.axhline(y=11, color='r', linestyle='--', label='RTX 2080 Ti VRAM')
    ax1.set_xlabel('Context Length (tokens)')
    ax1.set_ylabel('KV Cache Memory (GB)')
    ax1.set_title('KV Cache Memory vs Context Length')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')

    # Plot 2: Memory per token
    for model_name, data in results.items():
        ctx_lens = [d["ctx_len"] for d in data]
        bytes_per_token = [d["bytes_per_token"] for d in data]
        ax2.plot(ctx_lens, bytes_per_token, 'o-', label=model_name, linewidth=2)

    ax2.set_xlabel('Context Length (tokens)')
    ax2.set_ylabel('Bytes per Token')
    ax2.set_title('Memory Efficiency (should be constant)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')

    plt.tight_layout()
    plt.savefig('/workspace/kv_cache_memory_analysis.png', dpi=150)
    print("\nPlot saved to: /workspace/kv_cache_memory_analysis.png")


if __name__ == "__main__":
    analyze_kv_cache_memory()
```

---

## Experiment 2: Context Window Benchmark

### Objective
Benchmark generation speed and memory at different context lengths.

### Benchmark Script
```python
# context_window_benchmark.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import time
import json

def benchmark_context_window():
    """Benchmark model at different context lengths"""

    # Models to test
    models_to_test = [
        ("mistralai/Mistral-7B-v0.1", 8192),
        ("meta-llama/Llama-2-7b-hf", 4096),
    ]

    batch_size = 1
    max_new_tokens = 100

    results = []

    for model_name, max_ctx in models_to_test:
        print(f"\n{'='*70}")
        print(f"Testing: {model_name}")
        print(f"Max Context: {max_ctx}")
        print(f"{'='*70}\n")

        # Load model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
        )

        # Test context lengths
        test_lengths = [512, 1024, 2048, 4096]
        if max_ctx >= 8192:
            test_lengths.extend([6144, 8192])
        if max_ctx >= 16384:
            test_lengths.extend([12288, 16384])

        for ctx_len in test_lengths:
            try:
                # Create prompt of appropriate length
                prompt = "AI is transforming " * (ctx_len // 4)
                inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
                actual_ctx_len = inputs["input_ids"].shape[1]

                print(f"Context Length: {actual_ctx_len}")

                # Prefill (processing input)
                torch.cuda.synchronize()
                prefill_start = time.time()

                with torch.no_grad():
                    outputs = model(
                        **inputs,
                        max_new_tokens=1,  # Just measure prefill
                        do_sample=False
                    )

                torch.cuda.synchronize()
                prefill_time = time.time() - prefill_start

                # Decode (generation)
                inputs["input_ids"] = outputs  # Continue from prefill

                torch.cuda.synchronize()
                decode_start = time.time()

                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        do_sample=False,
                        use_cache=True
                    )

                torch.cuda.synchronize()
                decode_time = time.time() - decode_start

                # Stats
                prefill_tokens_per_sec = actual_ctx_len / prefill_time
                decode_tokens_per_sec = max_new_tokens / decode_time
                vram_used = torch.cuda.max_memory_allocated() / 1024**3

                result = {
                    "model": model_name.split("/")[-1],
                    "context_length": actual_ctx_len,
                    "prefill_time": prefill_time,
                    "prefill_tokens_per_sec": prefill_tokens_per_sec,
                    "decode_time": decode_time,
                    "decode_tokens_per_sec": decode_tokens_per_sec,
                    "vram_gb": vram_used,
                }

                results.append(result)

                print(f"  Prefill: {prefill_time:.2f}s ({prefill_tokens_per_sec:.0f} tokens/s)")
                print(f"  Decode:  {decode_time:.2f}s ({decode_tokens_per_sec:.1f} tokens/s)")
                print(f"  VRAM:    {vram_used:.2f} GB")
                print()

            except RuntimeError as e:
                if "out of memory" in str(e):
                    print(f"  ✗ OOM at context length {ctx_len}")
                    torch.cuda.empty_cache()
                    break
                else:
                    raise

        # Cleanup
        del model
        torch.cuda.empty_cache()

    # Save results
    with open("/workspace/context_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print_summary(results)

    return results


def print_summary(results: list):
    """Print benchmark summary"""

    print(f"\n{'='*70}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*70}")

    current_model = None
    for r in results:
        if r["model"] != current_model:
            current_model = r["model"]
            print(f"\n{current_model}:")
            print(f"{'Ctx':<8} | {'Prefill (t/s)':<15} | {'Decode (t/s)':<15} | {'VRAM (GB)':<10}")
            print(f"{'-'*70}")

        print(f"{r['context_length']:<8} | "
              f"{r['prefill_tokens_per_sec']:<15.0f} | "
              f"{r['decode_tokens_per_sec']:<15.1f} | "
              f"{r['vram_gb']:<10.2f}")


if __name__ == "__main__":
    benchmark_context_window()
```

---

## Experiment 3: Streaming Attention Test

### Objective
Test streaming attention (also known as Attention with Linear Biases or ALiBi) for infinite context.

### Implementation
```python
# streaming_attention.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class StreamingKVCache:
    """
    Streaming KV Cache with windowed attention

    Maintains a sliding window of recent context for memory efficiency
    """

    def __init__(self, window_size: int, batch_size: int,
                 num_heads: int, head_dim: int):
        self.window_size = window_size
        self.batch_size = batch_size
        self.num_heads = num_heads
        self.head_dim = head_dim

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Ring buffer for efficient sliding window
        self.k_cache = torch.zeros(
            batch_size, num_heads, window_size, head_dim,
            dtype=torch.float16, device=device
        )
        self.v_cache = torch.zeros(
            batch_size, num_heads, window_size, head_dim,
            dtype=torch.float16, device=device
        )

        self.position = 0  # Current write position in ring buffer
        self.total_tokens = 0  # Total tokens processed

    def update(self, k: torch.Tensor, v: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Update cache with sliding window

        Args:
            k: (batch, heads, new_tokens, head_dim)
            v: (batch, heads, new_tokens, head_dim)
        """
        new_tokens = k.shape[2]

        for i in range(new_tokens):
            # Write to ring buffer position
            pos = (self.position + i) % self.window_size
            self.k_cache[:, :, pos:pos+1, :] = k[:, :, i:i+1, :]
            self.v_cache[:, :, pos:pos+1, :] = v[:, :, i:i+1, :]

        self.position = (self.position + new_tokens) % self.window_size
        self.total_tokens += new_tokens

        # Return cached window (may be wrapped)
        if self.total_tokens < self.window_size:
            # Not filled yet
            return (
                self.k_cache[:, :, :self.total_tokens, :],
                self.v_cache[:, :, :self.total_tokens, :],
            )
        else:
            # Return full window, rotated to correct order
            k_ordered = torch.cat([
                self.k_cache[:, :, self.position:, :],
                self.k_cache[:, :, :self.position, :],
            ], dim=2)
            v_ordered = torch.cat([
                self.v_cache[:, :, self.position:, :],
                self.v_cache[:, :, :self.position, :],
            ], dim=2)
            return k_ordered, v_ordered

    def get_memory_usage(self) -> dict:
        """Get memory usage (constant regardless of total tokens)"""
        element_size = 2  # FP16
        total_bytes = (
            self.k_cache.numel() + self.v_cache.numel()
        ) * element_size

        return {
            "window_size": self.window_size,
            "total_tokens": self.total_tokens,
            "constant_mb": total_bytes / (1024 ** 2),
            "constant_gb": total_bytes / (1024 ** 3),
        }


def test_streaming_attention():
    """Test streaming attention with sliding window"""

    print("Streaming Attention (Sliding Window) Test")
    print("="*60)

    # Configuration
    window_size = 4096
    batch_size = 1
    heads = 32
    head_dim = 128
    total_tokens = 100000  # Simulate very long context

    # Create streaming cache
    cache = StreamingKVCache(window_size, batch_size, heads, head_dim)

    print(f"Window Size: {window_size}")
    print(f"Total Tokens: {total_tokens}")
    print(f"Constant Memory: {cache.get_memory_usage()['constant_gb']:.2f} GB")

    # Simulate streaming tokens
    chunk_size = 512
    num_chunks = total_tokens // chunk_size

    print(f"\nProcessing {num_chunks} chunks of {chunk_size} tokens each...")

    for i in range(num_chunks):
        # Simulate new tokens
        k = torch.randn(batch_size, heads, chunk_size, head_dim, dtype=torch.float16, device="cuda")
        v = torch.randn(batch_size, heads, chunk_size, head_dim, dtype=torch.float16, device="cuda")

        # Update cache
        k_cache, v_cache = cache.update(k, v)

        if (i + 1) % 10 == 0:
            mem = cache.get_memory_usage()
            print(f"  Chunk {i+1:3d}: Total tokens={mem['total_tokens']:6d}, "
                  f"Cache size={k_cache.shape[2]:4d}, "
                  f"VRAM={mem['constant_gb']:.2f} GB (constant)")

    print(f"\n✓ Successfully processed {total_tokens} tokens with only {window_size} token cache")


if __name__ == "__main__":
    test_streaming_attention()
```

---

## Experiment 4: Multi-Round Conversation Test

### Objective
Test KV cache behavior in multi-round conversations.

### Test Script
```python
# multi_round_conversation.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread

def test_multi_round_conversation():
    """Test conversation with KV cache management"""

    print("Multi-Round Conversation Test")
    print("="*60)

    # Load model
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    # Simulate conversation
    conversation = [
        {"role": "user", "content": "Hello! Can you help me with machine learning?"},
        {"role": "assistant", "content": "Of course! I'd be happy to help with machine learning. What specific topic would you like to discuss?"},
        {"role": "user", "content": "I want to understand how transformers work."},
        {"role": "assistant", "content": "Transformers are deep learning models that use attention mechanisms. They process all positions in parallel and learn relationships between tokens regardless of their distance."},
        {"role": "user", "content": "Can you explain attention mechanism?"},
    ]

    # Track context growth
    context_lengths = []
    vram_usage = []

    for turn in conversation:
        # Format for chat
        if turn["role"] == "user":
            prompt = tokenizer.apply_chat_template(
                conversation[:conversation.index(turn)+1],
                tokenize=False,
                add_generation_prompt=True
            )

            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            ctx_len = inputs["input_ids"].shape[1]

            print(f"\nTurn {conversation.index(turn)//2 + 1}:")
            print(f"  Context Length: {ctx_len} tokens")

            # Generate
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                use_cache=True
            )

            response = tokenizer.decode(outputs[0][ctx_len:], skip_special_tokens=True)
            print(f"  Response: {response[:100]}...")

            # Track stats
            context_lengths.append(ctx_len)
            vram_usage.append(torch.cuda.max_memory_allocated() / 1024**3)
            torch.cuda.reset_peak_memory_stats()

    # Plot context growth
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(range(1, len(context_lengths)+1), context_lengths, 'o-', linewidth=2)
    ax1.set_xlabel('Conversation Turn')
    ax1.set_ylabel('Context Length (tokens)')
    ax1.set_title('Context Growth in Conversation')
    ax1.grid(True, alpha=0.3)

    ax2.plot(range(1, len(vram_usage)+1), vram_usage, 's-', color='orange', linewidth=2)
    ax2.axhline(y=11, color='r', linestyle='--', label='RTX 2080 Ti VRAM')
    ax2.set_xlabel('Conversation Turn')
    ax2.set_ylabel('VRAM Usage (GB)')
    ax2.set_title('VRAM Usage in Conversation')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/workspace/multi_round_conversation.png', dpi=150)
    print("\nPlot saved to: /workspace/multi_round_conversation.png")


if __name__ == "__main__":
    test_multi_round_conversation()
```

---

## Expected Results (RTX 2080 Ti 11GB)

### KV Cache Memory by Context Length

| Model | 2048 tokens | 4096 tokens | 8192 tokens | 16384 tokens |
|-------|-------------|-------------|-------------|--------------|
| Llama-2-7B | ~1.5 GB | ~3 GB | ~6 GB | ~12 GB (OOM) |
| Mistral-7B | ~1.5 GB | ~3 GB | ~6 GB | ~12 GB (OOM) |
| Llama-2-13B | ~2 GB | ~4 GB | ~8 GB | OOM |
| Mixtral-8x7B | ~1.5 GB | ~3 GB | ~6 GB | ~12 GB (OOM) |

### Generation Speed by Context

| Context | Prefill (t/s) | Decode (t/s) | Notes |
|---------|---------------|--------------|-------|
| 512 | ~5000 | ~50 | Fast |
| 2048 | ~3000 | ~45 | Good |
| 4096 | ~1500 | ~40 | Acceptable |
| 8192 | ~700 | ~35 | Slow prefill |
| 16384 | ~300 | ~30 | Very slow prefill |

---

## Experiment Checklist

- [ ] KV cache memory analysis at different configurations
- [ ] Context window benchmark (prefill vs decode speed)
- [ ] Streaming attention with sliding window
- [ ] Multi-round conversation test
- [ ] OOM prevention strategies
- [ ] Quantization impact on context window
- [ ] Flash Attention impact on context window
- [ ] KV cache compression techniques
- [ ] Multi-round conversation memory management

---

## Related Documentation
- [4201: Context Window Physics](../docs/4000-Quantization/4200-KV-Cache/4201-Context-Window-Physics.md)
- [3102: Flash Attention](../docs/3000-Transformer-Physics/3100-Attention/3102-Flash-Attention.md)
- [4101: GGUF Physics](../docs/4000-Quantization/4100-Low-Bit/4101-GGUF-Physics.md)
- [1204: Multi-GPU Setup](../docs/1204-Multi-GPU-Setup.md)
