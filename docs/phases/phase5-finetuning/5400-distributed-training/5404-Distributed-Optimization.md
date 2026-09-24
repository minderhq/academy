---
Document ID: 5404
Title: Distributed Optimization
Phase: 5
Module: 5400
Last Updated: 2026-09-24
Status: Review
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: 5401, 5403
Tags: ['distributed', 'optimization', 'gradients']
---

# 5404: Distributed Optimization

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Gradient Synchronization](#gradient-synchronization)
- [Gradient Compression](#gradient-compression)
- [Communication Backend](#communication-backend)
- [Overlapping Computation and Communication](#overlapping-computation-and-communication)
- [Framework Implementations](#framework-implementations)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Gradient Synchronization
- Explain Gradient Compression
- Explain Communication Backend
- Explain Overlapping Computation and Communication
- Configure and operate Framework Implementations
- Explain Best Practices

---

## Abstract

Distributed optimization coordinates gradient updates across multiple devices, requiring efficient communication and synchronization strategies.

## Gradient Synchronization

### All-Reduce Operation

The core operation for data parallel training:

```python
import torch.distributed as dist

def all_reduce_gradients(model, world_size):
    """Synchronize gradients across all processes."""
    for param in model.parameters():
        if param.grad is not None:
            # Sum gradients from all processes
            dist.all_reduce(param.grad, op=dist.ReduceOp.SUM)

            # Average by dividing by world size
            param.grad.div_(world_size)
```

### All-Reduce Algorithms

#### 1. Ring All-Reduce

**Concept:** Arrange processes in a ring, pass data sequentially.

```python
def ring_all_reduce(tensor, rank, world_size):
    """Simple ring all-reduce implementation."""
    send_buf = tensor.clone()
    recv_buf = torch.empty_like(tensor)

    for step in range(world_size - 1):
        send_to = (rank + 1) % world_size
        recv_from = (rank - 1) % world_size

        # Send and receive simultaneously
        send_req = dist.isend(send_buf, send_to)
        recv_req = dist.irecv(recv_buf, recv_from)
        recv_req.wait()

        # Accumulate
        tensor += recv_buf
        send_buf = recv_buf

    return tensor
```

**Complexity:** O(2 * (N-1)) for N processes

#### 2. Tree All-Reduce

**Concept:** Use tree topology for hierarchical reduction.

```python
def tree_all_reduce(tensor, rank, world_size):
    """Tree-based all-reduce."""
    size = tensor.numel()

    # Reduce phase
    step = 1
    while step < world_size:
        if rank % (2 * step) == 0:
            # Receive from rank + step
            if rank + step < world_size:
                recv_tensor = torch.empty_like(tensor)
                dist.recv(recv_tensor, src=rank + step)
                tensor += recv_tensor

        elif rank % step == 0:
            # Send to rank - step
            dist.send(tensor, dst=rank - step)
            return tensor

        step *= 2

    # Broadcast phase
    step = world_size // 2
    while step > 0:
        if rank + step < world_size and rank % (2 * step) == 0:
            dist.send(tensor, dst=rank + step)

        if rank >= step and rank % step == 0:
            recv_tensor = torch.empty_like(tensor)
            dist.recv(recv_tensor, src=rank - step)
            tensor = recv_tensor

        step //= 2

    return tensor
```

**Complexity:** O(2 * log(N)) for N processes

## Gradient Compression

### 1. Gradient Sparsification

Only send significant gradients:

```python
def sparsify_gradient(grad, threshold=0.01):
    """Send only gradients above threshold."""
    # Get top-k gradients
    k = int(grad.numel() * 0.1)  # Top 10%
    topk_vals, topk_indices = torch.topk(grad.abs().flatten(), k)

    # Create sparse representation
    mask = torch.zeros_like(grad).bool()
    mask.view(-1)[topk_indices] = grad.abs().flatten()[topk_indices] > threshold

    return grad * mask, mask

def densify_gradient(sparse_grad, mask):
    """Reconstruct full gradient."""
    return sparse_grad * mask
```

### 2. Quantization

Send gradients with reduced precision:

```python
def quantize_gradient(grad, bits=8):
    """Quantize gradient to specified bits."""
    # Scale to [0, 2^bits - 1]
    min_val = grad.min()
    max_val = grad.max()

    scale = (max_val - min_val) / (2**bits - 1)
    quantized = ((grad - min_val) / scale).round().clamp(0, 2**bits - 1)

    return quantized.byte(), (min_val, scale)

def dequantize_gradient(quantized, min_val, scale):
    """Dequantize gradient."""
    return quantized.float() * scale + min_val
```

### 3. Error Feedback

Correct for compression error:

```python`
class CompressedGradientOptimizer:
    def __init__(self, optimizer, compress_fn):
        self.optimizer = optimizer
        self.compress_fn = compress_fn
        self.error_accumulator = None

    def step(self):
        """Apply compressed gradients with error feedback."""
        for group in self.optimizer.param_groups:
            for p in group['params']:
                if p.grad is not None:
                    # Add accumulated error
                    if self.error_accumulator is not None:
                        p.grad += self.error_accumulator[p]

                    # Compress gradient
                    compressed_grad = self.compress_fn(p.grad)

                    # Compute residual error
                    decompressed = self.decompress_fn(compressed_grad)
                    self.error_accumulator[p] = p.grad - decompressed

                    # Apply decompressed gradient
                    p.grad = decompressed

        self.optimizer.step()
```python

## Communication Backend

### NCCL (NVIDIA Collective Communications Library)

```python
import torch.distributed as dist

# Initialize process group with NCCL backend
dist.init_process_group(
    backend='nccl',
    init_method='env://',
    world_size=world_size,
    rank=rank
)

# Use NCCL for all-reduce
dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
```

**Advantages:**
- Optimized for NVIDIA GPUs
- Uses NVLink for intra-node communication
- Automatic topology detection

### Gloo

```python
# Initialize with Gloo backend (CPU)
dist.init_process_group(
    backend='gloo',
    init_method='tcp://10.0.0.1:12345',
    world_size=world_size,
    rank=rank
)
```

**Advantages:**
- Works on CPU
- Cross-platform
- Good for heterogenous clusters

## Overlapping Computation and Communication

### Gradient Bucketing

Group gradients to overlap communication:

```python
from torch.distributed.optim import DistributedOptimizer

# Create parameter groups for different layers
layer_groups = [
    list(model.encoder.parameters()),
    list(model.decoder.parameters()),
]

# Bucket gradients for each group
optimizer = DistributedOptimizer(
    optim.SGD,
    params=layer_groups,
    bucket_size_mb=25,
)
```

### Async All-Reduce

```python
import torch.distributed as dist

def async_all_reduce(model):
    """Start all-reduce operations asynchronously."""
    handles = []

    for param in model.parameters():
        if param.grad is not None:
            # Start async all-reduce
            handle = dist.all_reduce(param.grad, op=dist.ReduceOp.SUM, async_op=True)
            handles.append((param, handle))

    return handles

# Forward pass
output = model(input)
loss = criterion(output, target)

# Backward pass
loss.backward()

# Start async gradient sync
handles = async_all_reduce(model)

# Do other work while gradients sync
metrics = compute_metrics(output, target)

# Wait for all-reduce to complete
for param, handle in handles:
    handle.wait()
    param.grad.div_(dist.get_world_size())
```

## Framework Implementations

### PyTorch DDP

```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

# Wrap model for data parallel training
model = DDP(
    model,
    device_ids=[local_rank],
    output_device=local_rank,
    bucket_cap_mb=25,  # Gradient bucket size
    find_unused_parameters=False,  # Optimization
)

# Training loop
for batch in dataloader:
    output = model(batch)
    loss = criterion(output, target)
    loss.backward()  # DDP handles gradient sync
    optimizer.step()
```

### DeepSpeed

```python
import deepspeed

# Initialize DeepSpeed
model_engine, optimizer, _, _ = deepspeed.initialize(
    model=model,
    model_parameters=model.parameters(),
    config={
        "train_batch_size": 32,
        "gradient_accumulation_steps": 4,
        "fp16": {"enabled": True},
        "communication_data_type": torch.float16,
    }
)

# Training loop
for batch in dataloader:
    loss = model_engine(batch)
    model_engine.backward(loss)
    model_engine.step()
```

## Best Practices

1. **Minimize Communication:**
   - Use gradient compression
   - Overlap with computation
   - Use efficient backends

2. **Optimize Bucket Size:**
   - Larger buckets = better bandwidth utilization
   - Too large = memory pressure
   - Typical: 10-50 MB

3. **Handle Heterogeneity:**
   - Adjust for slow workers
   - Use elastic training
   - Monitor stragglers

---

**Next:** [Assessment](./assessment/QUIZ.md)

**Last Updated:** 2026-02-05

## References

### Related ai-engineering-curriculum Documents

- [5401: Data Parallelism](5401-Data-Parallelism.md)
- [5403: Mixed Precision Training](5403-Mixed-Precision.md)

---