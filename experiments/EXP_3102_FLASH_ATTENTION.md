# EXP_3102: Flash Attention Experiments

## Overview
Practical experiments for testing Flash Attention implementation and performance on RTX 2080 Ti (11GB VRAM).

## Experiment 1: Standard vs Flash Attention Benchmark

### Objective
Compare standard attention vs Flash Attention 2 in terms of speed and memory usage.

### Setup
```bash
pip install torch flash-attn einops numpy matplotlib
```

### Benchmark Script
```python
# flash_attention_benchmark.py
import torch
import torch.nn as nn
import time
from dataclasses import dataclass
from typing import Optional

# Standard Attention Implementation
class StandardAttention(nn.Module):
    """Standard scaled dot-product attention with O(n^2) memory"""

    def __init__(self, dim: int, num_heads: int = 8):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(dim, dim * 3, bias=False)
        self.out = nn.Linear(dim, dim)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # Standard attention: compute full attention matrix
        attn = (q @ k.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = attn.softmax(dim=-1)
        out = (attn @ v).transpose(1, 2).reshape(B, N, C)

        return self.out(out)


# Flash Attention 2 Implementation
try:
    from flash_attn import flash_attn_func

    class FlashAttention(nn.Module):
        """Flash Attention 2 with O(n) memory"""

        def __init__(self, dim: int, num_heads: int = 8):
            super().__init__()
            self.num_heads = num_heads
            self.head_dim = dim // num_heads

            self.qkv = nn.Linear(dim, dim * 3, bias=False)
            self.out = nn.Linear(dim, dim)

        def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None):
            B, N, C = x.shape
            qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)

            # Flash Attention API
            q, k, v = qkv.unbind(2)  # (B, N, heads, head_dim)

            out = flash_attn_func(
                q, k, v,
                causal=False,
                softmax_scale=self.head_dim ** -0.5
            )

            out = out.reshape(B, N, C)
            return self.out(out)

    FLASH_AVAILABLE = True
except ImportError:
    print("Flash Attention not available. Install with: pip install flash-attn")
    FLASH_AVAILABLE = False


def benchmark_attention(seq_lengths: list, dim: int = 512, heads: int = 8, rounds: int = 10):
    """Benchmark attention mechanisms at different sequence lengths"""

    device = "cuda" if torch.cuda.is_available() else "cpu"
    results = {"standard": [], "flash": []}

    print(f"\n{'='*70}")
    print(f"Attention Benchmark (dim={dim}, heads={heads}, rounds={rounds})")
    print(f"Device: {device}")
    print(f"{'='*70}\n")

    for seq_len in seq_lengths:
        print(f"Sequence Length: {seq_len}")

        # Create input
        x = torch.randn(2, seq_len, dim, device=device)

        # Standard Attention
        std_attn = StandardAttention(dim, heads).to(device)
        std_attn.eval()

        # Warmup
        with torch.no_grad():
            for _ in range(3):
                _ = std_attn(x)

        # Benchmark
        torch.cuda.synchronize()
        start = time.time()

        with torch.no_grad():
            for _ in range(rounds):
                out = std_attn(x)

        torch.cuda.synchronize()
        std_time = (time.time() - start) / rounds
        std_memory = torch.cuda.max_memory_allocated() / 1024**2

        results["standard"].append({
            "seq_len": seq_len,
            "time_ms": std_time * 1000,
            "memory_mb": std_memory
        })

        print(f"  Standard: {std_time*1000:6.2f}ms | {std_memory:8.1f}MB VRAM")

        torch.cuda.reset_peak_memory_stats()

        # Flash Attention (if available)
        if FLASH_AVAILABLE:
            flash_attn = FlashAttention(dim, heads).to(device)
            flash_attn.eval()

            # Warmup
            with torch.no_grad():
                for _ in range(3):
                    _ = flash_attn(x)

            # Benchmark
            torch.cuda.synchronize()
            start = time.time()

            with torch.no_grad():
                for _ in range(rounds):
                    out = flash_attn(x)

            torch.cuda.synchronize()
            flash_time = (time.time() - start) / rounds
            flash_memory = torch.cuda.max_memory_allocated() / 1024**2

            results["flash"].append({
                "seq_len": seq_len,
                "time_ms": flash_time * 1000,
                "memory_mb": flash_memory
            })

            speedup = std_time / flash_time
            memory_saving = (std_memory - flash_memory) / std_memory * 100

            print(f"  Flash:    {flash_time*1000:6.2f}ms | {flash_memory:8.1f}MB VRAM")
            print(f"  Speedup:  {speedup:5.2f}x | Memory Saving: {memory_saving:5.1f}%")
        else:
            print(f"  Flash:    Not Available")

        torch.cuda.reset_peak_memory_stats()
        print()

    return results


# Run benchmark
if __name__ == "__main__":
    seq_lengths = [512, 1024, 2048, 4096, 8192, 16384]

    results = benchmark_attention(
        seq_lengths=seq_lengths,
        dim=512,
        heads=8,
        rounds=20
    )

    # Summary
    print(f"{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'Seq Len':<10} | {'Standard (ms)':<15} | {'Flash (ms)':<15} | {'Speedup':<10}")
    print(f"{'-'*70}")

    if results["flash"]:
        for i, seq_len in enumerate(seq_lengths):
            std = results["standard"][i]
            flash = results["flash"][i]
            speedup = std["time_ms"] / flash["time_ms"]
            print(f"{seq_len:<10} | {std['time_ms']:<15.2f} | {flash['time_ms']:<15.2f} | {speedup:<10.2f}x")
```

---

## Experiment 2: Memory Scaling Analysis

### Objective
Measure how memory scales with sequence length for standard vs Flash Attention.

### Script
```python
# memory_scaling_analysis.py
import torch
import matplotlib.pyplot as plt
from flash_attention_benchmark import benchmark_attention

def analyze_memory_scaling():
    """Analyze memory scaling characteristics"""

    seq_lengths = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768]

    results = benchmark_attention(
        seq_lengths=seq_lengths,
        dim=512,
        heads=8,
        rounds=5
    )

    # Extract memory data
    standard_memory = [r["memory_mb"] for r in results["standard"]]
    flash_memory = [r["memory_mb"] for r in results["flash"]] if results["flash"] else None

    # Plot
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.plot(seq_lengths, standard_memory, 'o-', label='Standard Attention', linewidth=2)
    if flash_memory:
        plt.plot(seq_lengths, flash_memory, 's-', label='Flash Attention', linewidth=2)
    plt.xlabel('Sequence Length')
    plt.ylabel('Peak VRAM (MB)')
    plt.title('Memory Usage vs Sequence Length')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.yscale('log')

    # Speedup
    plt.subplot(1, 2, 2)
    if flash_memory:
        speedups = [results["standard"][i]["time_ms"] / results["flash"][i]["time_ms"]
                    for i in range(len(seq_lengths))]
        plt.plot(seq_lengths, speedups, 'o-', color='green', linewidth=2)
        plt.xlabel('Sequence Length')
        plt.ylabel('Speedup (x)')
        plt.title('Flash Attention Speedup')
        plt.grid(True, alpha=0.3)
        plt.axhline(y=1, color='r', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig('/workspace/flash_attention_analysis.png', dpi=150)
    print("\nPlot saved to: /workspace/flash_attention_analysis.png")

if __name__ == "__main__":
    analyze_memory_scaling()
```

---

## Experiment 3: Causal Mask Performance

### Objective
Test Flash Attention with causal masking (for autoregressive generation).

### Script
```python
# causal_attention_test.py
import torch
from flash_attn import flash_attn_with_kvcache

def test_causal_attention():
    """Test causal (autoregressive) attention"""

    device = "cuda"
    batch_size = 2
    seq_len = 2048
    dim = 512
    heads = 8
    head_dim = dim // heads

    # Create inputs
    q = torch.randn(batch_size, seq_len, heads, head_dim, device=device, dtype=torch.float16)
    k = torch.randn(batch_size, seq_len, heads, head_dim, device=device, dtype=torch.float16)
    v = torch.randn(batch_size, seq_len, heads, head_dim, device=device, dtype=torch.float16)

    print(f"Testing Causal Attention")
    print(f"Batch: {batch_size}, Seq: {seq_len}, Heads: {heads}, Dim: {head_dim}")

    # Flash Attention with causal mask
    import time

    # Warmup
    for _ in range(5):
        out = flash_attn_with_kvcache(q, k, v, causal=True)

    # Benchmark
    torch.cuda.synchronize()
    start = time.time()

    for _ in range(50):
        out = flash_attn_with_kvcache(q, k, v, causal=True)

    torch.cuda.synchronize()
    elapsed = (time.time() - start) / 50

    print(f"Causal Attention: {elapsed*1000:.2f}ms per forward pass")
    print(f"VRAM Used: {torch.cuda.max_memory_allocated()/1024**2:.1f}MB")

    return out

if __name__ == "__main__":
    test_causal_attention()
```

---

## Experiment 4: Long Context Generation Test

### Objective
Test generation with long context windows using Flash Attention.

### Script
```python
# long_context_generation.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import time

def test_long_context_generation():
    """Test generation with various context lengths"""

    model_name = "mistralai/Mistral-7B-v0.1"

    print(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        use_flash_attention_2=True  # Enable Flash Attention 2
    )

    # Test different context lengths
    context_lengths = [1024, 2048, 4096, 6144, 8192]

    results = []

    for ctx_len in context_lengths:
        print(f"\n{'='*60}")
        print(f"Context Length: {ctx_len} tokens")
        print(f"{'='*60}")

        # Generate long prompt
        prompt = "The history of artificial intelligence " * (ctx_len // 8)
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        actual_len = inputs["input_ids"].shape[1]
        print(f"Actual input length: {actual_len} tokens")

        # Generate
        start = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=False,
                use_cache=True
            )
        elapsed = time.time() - start

        # Stats
        generated = outputs[0][actual_len:]
        text = tokenizer.decode(generated, skip_special_tokens=True)

        print(f"Generation time: {elapsed:.2f}s")
        print(f"Tokens/sec: {100/elapsed:.1f}")
        print(f"VRAM peak: {torch.cuda.max_memory_allocated()/1024**3:.2f}GB")

        results.append({
            "context_len": actual_len,
            "gen_time": elapsed,
            "tokens_per_sec": 100/elapsed,
            "vram_gb": torch.cuda.max_memory_allocated()/1024**3
        })

        torch.cuda.reset_peak_memory_stats()

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Context':<12} | {'Gen Time':<12} | {'Tokens/s':<12} | {'VRAM':<10}")
    print(f"{'-'*60}")
    for r in results:
        print(f"{r['context_len']:<12} | {r['gen_time']:<12.2f} | {r['tokens_per_sec']:<12.1f} | {r['vram_gb']:<10.2f}")

if __name__ == "__main__":
    test_long_context_generation()
```

---

## Experiment 5: Flash Attention Kernel Analysis

### Objective
Understand the kernel fusion benefits of Flash Attention.

### Analysis
```python
# flash_attention_kernel_analysis.py
"""
Flash Attention 2 Kernel Fusion Analysis

Standard Attention:
1. QK^T computation (kernel 1)
2. Scaling (kernel 2)
3. Softmax (kernel 3)
4. Softmax @ V (kernel 4)
5. Transpose/reshape (kernel 5)
Total: 5 kernel launches, 2x memory access (materialize attention matrix)

Flash Attention 2:
1. Tiled attention in shared memory (1 kernel)
2. Online softmax (fused)
3. No attention matrix materialization
Total: 1 kernel launch, 1x memory access
"""

def analyze_kernel_benefits():
    """Analyze the theoretical benefits of Flash Attention"""

    print("Flash Attention 2 Kernel Fusion Benefits")
    print("="*60)

    # Memory access analysis
    seq_len = 4096
    batch = 2
    heads = 32
    head_dim = 128

    # Standard attention memory
    attention_matrix_size = batch * heads * seq_len * seq_len * 4  # float32
    qkv_size = batch * seq_len * (3 * heads * head_dim) * 4

    print(f"\nSequence Length: {seq_len}")
    print(f"Batch Size: {batch}")
    print(f"Heads: {heads}, Head Dim: {head_dim}")

    print(f"\nStandard Attention Memory:")
    print(f"  QKV tensors: {qkv_size/1024**2:.1f} MB")
    print(f"  Attention matrix: {attention_matrix_size/1024**2:.1f} MB")
    print(f"  Total: {(qkv_size + attention_matrix_size)/1024**2:.1f} MB")

    print(f"\nFlash Attention 2 Memory:")
    print(f"  QKV tensors: {qkv_size/1024**2:.1f} MB")
    print(f"  Attention matrix: 0 MB (not materialized)")
    print(f"  Total: {qkv_size/1024**2:.1f} MB")

    memory_saved = attention_matrix_size / (qkv_size + attention_matrix_size) * 100
    print(f"\nMemory Saved: {memory_saved:.1f}%")

    # Kernel launch analysis
    print(f"\nKernel Launches:")
    print(f"  Standard Attention: ~5 kernel launches")
    print(f"  Flash Attention 2: ~1 kernel launch")
    print(f"  Reduction: 80% fewer launches")

    # HBM bandwidth utilization
    print(f"\nHBM Bandwidth Utilization:")
    print(f"  RTX 2080 Ti: 616 GB/s")
    print(f"  Standard: ~2x materialization = lower effective bandwidth")
    print(f"  Flash: ~1x pass = higher effective bandwidth")

if __name__ == "__main__":
    analyze_kernel_benefits()
```

---

## Expected Performance (RTX 2080 Ti)

| Sequence Length | Standard Time | Flash Time | Speedup | Standard VRAM | Flash VRAM |
|----------------|---------------|------------|---------|---------------|-------------|
| 512 | 5ms | 3ms | 1.7x | 500MB | 200MB |
| 1024 | 18ms | 8ms | 2.3x | 1.5GB | 400MB |
| 2048 | 70ms | 25ms | 2.8x | 4.5GB | 800MB |
| 4096 | 280ms | 85ms | 3.3x | OOM | 1.5GB |
| 8192 | OOM | 320ms | - | OOM | 3.0GB |
| 16384 | OOM | 1200ms | - | OOM | 6.0GB |

---

## Experiment Checklist

- [ ] Standard vs Flash Attention speed benchmark
- [ ] Memory scaling analysis (plot generation)
- [ ] Causal mask performance test
- [ ] Long context generation test (4k-8k tokens)
- [ ] Kernel fusion benefits analysis
- [ ] FP16 vs BF16 performance comparison
- [ ] Batch size scaling test
- [ ] Multi-head attention scaling (8, 16, 32 heads)

---

## Related Documentation
- [3101: Self-Attention](../docs/3000-Transformer-Physics/3100-Attention/3101-Self-Attention-DeepDive.md)
- [3102: Flash Attention](../docs/3000-Transformer-Physics/3100-Attention/3102-Flash-Attention.md)
- [2203: CUDA Kernels](../docs/2000-Cognitive-Science/2200-Framework-Engineering/2203-CUDA-Kernel-Syb-Level.md)
- [4201: Context Window Physics](../docs/4000-Quantization/4200-KV-Cache/4201-Context-Window-Physics.md)
