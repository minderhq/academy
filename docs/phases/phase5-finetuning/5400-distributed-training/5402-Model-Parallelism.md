---
Document ID: 5402
Title: Model Parallelism
Phase: 5
Module: 5400
Last Updated: 2026-09-24
Status: Review
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: 5401, 5403
Tags: ['distributed', 'training', 'parallelism']
---

# 5402: Model Parallelism

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Types of Model Parallelism](#types-of-model-parallelism)
- [Megatron-LM Style Parallelism](#megatron-lm-style-parallelism)
- [Implementation Patterns](#implementation-patterns)
- [When to Use Each](#when-to-use-each)
- [Best Practices](#best-practices)
- [Tools and Frameworks](#tools-and-frameworks)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Types of Model Parallelism
- Explain Megatron-LM Style Parallelism
- Apply Implementation Patterns
- Explain When to Use Each
- Explain Best Practices
- Explain Tools and Frameworks

---

## Abstract

Model parallelism splits the model itself across multiple GPUs, enabling training of models that are too large to fit on a single device.

## Types of Model Parallelism

### 1. Pipeline Parallelism

**Concept:** Split model layers across GPUs, with data flowing through them sequentially.

```python
from torch.distributed.pipeline.sync import Pipe

# Create model chunks for each GPU
model = nn.Sequential(
    nn.Linear(1024, 4096),
    nn.ReLU(),
    nn.Linear(4096, 4096),
    nn.ReLU(),
    nn.Linear(4096, 1024),
)

# Split across 4 GPUs
model = Pipe(model, chunks=4)

# Forward pass automatically pipelines
output = model(input)
```

**Advantages:**
- Load balancing across devices
- Minimal communication overhead
- Easy to implement

**Challenges:**
- Pipeline bubbles (idle time)
- Complex implementation
- Micro-batch management

### 2. Tensor Parallelism

**Concept:** Split individual tensors across GPUs, computing operations in parallel.

```python
import torch.distributed as dist

class ColumnParallelLinear(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        # Split weight matrix across GPUs column-wise
        self.rank = dist.get_rank()
        self.world_size = dist.get_world_size()

        # Each GPU gets out_features // world_size columns
        self.weight = nn.Parameter(
            torch.randn(out_features // self.world_size, in_features)
        )
        self.bias = nn.Parameter(torch.zeros(out_features // self.world_size))

    def forward(self, x):
        # Local matrix multiply
        local_out = torch.matmul(x, self.weight.t()) + self.bias

        # All-gather to combine results
        outputs = [torch.empty_like(local_out) for _ in range(self.world_size)]
        dist.all_gather(outputs, local_out)

        return torch.cat(outputs, dim=-1)
```

**Advantages:**
- No pipeline bubbles
- Better for very large models
- Synchronous computation

**Challenges:**
- More communication
- Complex implementation
- Requires careful tensor sharding

## Megatron-LM Style Parallelism

Combines tensor and pipeline parallelism:

```python
from megatron import get_args
from megatron.model import MegatronModule

class ParallelTransformerBlock(MegatronModule):
    def __init__(self):
        args = get_args()
        super().__init__()

        # Column parallel (QKV projection split across GPUs)
        self.query_key_value = ColumnParallelLinear(
            args.hidden_size,
            3 * args.kv_channels * args.num_attention_heads,
        )

        # Row parallel (output projection)
        self.dense = RowParallelLinear(
            args.kv_channels * args.num_attention_heads,
            args.hidden_size,
        )
```

## Implementation Patterns

### Pipeline Parallel with Micro-batches

```python
def pipeline_forward(model_chunks, micro_batches, devices):
    """Execute pipeline parallel forward pass."""
    results = []

    for micro_batch in micro_batches:
        # Forward through pipeline stages
        x = micro_batch
        for i, chunk in enumerate(model_chunks):
            x = chunk(x.to(devices[i]))

        results.append(x)

    # Combine micro-batch results
    return torch.cat(results, dim=0)
```

### Tensor Parallel with Attention

```python
class ParallelMultiHeadAttention(nn.Module):
    def __init__(self, hidden_size, num_heads):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads

        # Split heads across GPUs
        self.local_heads = num_heads // dist.get_world_size()

        # Column parallel QKV projection
        self.qkv = ColumnParallelLinear(hidden_size, 3 * hidden_size)

        # Row parallel output projection
        self.out_proj = RowParallelLinear(hidden_size, hidden_size)

    def forward(self, x, mask=None):
        batch_size, seq_len, _ = x.shape

        # Project QKV (tensor parallel)
        qkv = self.qkv(x)
        qkv = qkv.reshape(batch_size, seq_len, 3, self.num_heads, self.head_dim)

        # Only process local heads
        qkv = qkv[:, :, :, self.local_rank::self.world_size, :]

        # Attention computation
        attn_out = self._attention(qkv, mask)

        # Project output (row parallel)
        return self.out_proj(attn_out)
```

## When to Use Each

| Technique | Model Size | Hardware | Use Case |
|-----------|-----------|----------|----------|
| **Pipeline Parallel** | 10B+ params | Multiple GPUs | Inference, moderate training |
| **Tensor Parallel** | 100B+ params | High-bandwidth | Training very large models |
| **Hybrid** | 50B+ params | GPU clusters | Production-scale training |

## Best Practices

1. **Minimize Communication:**
   - Use high-bandwidth interconnects (NVLink)
   - Overlap communication with computation
   - Group small operations

2. **Balance Load:**
   - Distribute layers evenly in pipeline
   - Split tensors uniformly
   - Profile to find bottlenecks

3. **Handle Memory:**
   - Clear gradients timely
   - Use gradient checkpointing
   - Monitor memory per GPU

## Tools and Frameworks

- **PyTorch:** `torch.distributed.pipeline`
- **DeepSpeed:** Pipeline parallelism
- **Megatron-LM:** Tensor parallelism
- **Alpa:** Automatic parallelism

---

**Next:** [5403: Mixed Precision Training](./5403-Mixed-Precision.md)

**Last Updated:** 2026-02-05

## References

### Related ai-engineering-curriculum Documents

- [5401: Data Parallelism](5401-Data-Parallelism.md)
- [5403: Mixed Precision Training](5403-Mixed-Precision.md)

---