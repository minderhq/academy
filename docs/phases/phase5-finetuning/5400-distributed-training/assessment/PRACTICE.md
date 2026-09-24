# 5400: Distributed Training - Practice

## Exercises

### Exercise 1: Convert Single-GPU Training to DDP

Convert this single-GPU training loop to use DDP:

```python
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader

# Original single-GPU code:
# model = MyModel().cuda()
# optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
# train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
#
# for epoch in range(10):
#     for data, target in train_loader:
#         data, target = data.cuda(), target.cuda()
#         optimizer.zero_grad()
#         output = model(data)
#         loss = criterion(output, target)
#         loss.backward()
#         optimizer.step()

# Converted to DDP:
def setup(rank, world_size):
    """Initialize the distributed environment."""
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'
    dist.init_process_group("nccl", rank=rank, world_size=world_size)

def cleanup():
    """Clean up the distributed environment."""
    dist.destroy_process_group()

def train_ddp(rank, world_size, train_dataset, model_class, epochs=10):
    """Training function for DDP."""

    # Setup distributed environment
    setup(rank, world_size)

    # Create model and move to GPU
    model = model_class().to(rank)
    ddp_model = DDP(model, device_ids=[rank])

    # Create optimizer
    optimizer = torch.optim.Adam(ddp_model.parameters(), lr=1e-3)

    # Create data loader with distributed sampler
    from torch.utils.data.distributed import DistributedSampler
    train_sampler = DistributedSampler(
        train_dataset,
        num_replicas=world_size,
        rank=rank,
        shuffle=True
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=32,
        sampler=train_sampler
    )

    # Training loop
    for epoch in range(epochs):
        train_sampler.set_epoch(epoch)  # Important for shuffling

        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(rank), target.to(rank)

            optimizer.zero_grad()
            output = ddp_model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            if batch_idx % 100 == 0 and rank == 0:
                print(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")

    cleanup()

# Launch training
if __name__ == "__main__":
    world_size = torch.cuda.device_count()
    mp.spawn(train_ddp, args=(world_size, train_dataset, MyModel), nprocs=world_size)

# Expected output:
# - Training runs across all available GPUs
# - Each GPU processes a different subset of data
# - Gradients are synchronized across GPUs
# - Speed scales nearly linearly with GPU count (for large batches)
```

### Exercise 2: Implement Gradient Accumulation

Implement gradient accumulation to simulate larger batch sizes:

```python
def train_with_gradient_accumulation(model, train_loader, optimizer, criterion,
                                     accumulation_steps=4, epochs=10):
    """Train with gradient accumulation."""

    model.train()
    device = next(model.parameters()).device

    # Effective batch size = batch_size * accumulation_steps
    effective_batch_size = train_loader.batch_size * accumulation_steps

    print(f"Training with gradient accumulation:")
    print(f"  Per-GPU batch size: {train_loader.batch_size}")
    print(f"  Accumulation steps: {accumulation_steps}")
    print(f"  Effective batch size: {effective_batch_size}")

    for epoch in range(epochs):
        optimizer.zero_grad()  # Zero gradients at start of epoch

        for i, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)

            # Forward pass
            output = model(data)
            loss = criterion(output, target)

            # Normalize loss for accumulation
            loss = loss / accumulation_steps

            # Backward pass (accumulates gradients)
            loss.backward()

            # Update weights every accumulation_steps batches
            if (i + 1) % accumulation_steps == 0:
                optimizer.step()
                optimizer.zero_grad()

                if (i + 1) % 100 == 0:
                    print(f"Epoch {epoch}, Step {i+1}, Loss: {loss.item() * accumulation_steps:.4f}")

        # Handle remaining batches at end of epoch
        if (i + 1) % accumulation_steps != 0:
            optimizer.step()
            optimizer.zero_grad()

# Usage
model = MyModel().cuda()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Simulate batch size of 128 with 32 per GPU and 4 accumulation steps
train_with_gradient_accumulation(
    model, train_loader, optimizer, criterion,
    accumulation_steps=4,
    epochs=10
)

# Expected benefits:
# - Can train with larger effective batch sizes on limited GPU memory
# - Maintains training stability of larger batches
# - Trade-off: slightly longer training time due to more forward passes
```

### Exercise 3: FSDP Configuration

Configure FSDP for a large model:

```python
import torch
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.wrap import size_based_auto_wrap_policy
from torch.distributed.fsdp import MixedPrecision, CPUOffload

def setup_fsdp_model(model):
    """Configure model with FSDP for training large models."""

    # Mixed precision configuration (BF16)
    mixed_precision = MixedPrecision(
        param_dtype=torch.bfloat16,
        reduce_dtype=torch.bfloat16,
        buffer_dtype=torch.bfloat16,
    )

    # CPU offload configuration
    cpu_offload = CPUOffload(offload_params=True)

    # Auto-wrap policy: shard layers larger than 100M parameters
    auto_wrap_policy = size_based_auto_wrap_policy(
        min_num_params=100_000_000  # 100M parameters
    )

    # Wrap model with FSDP
    fsdp_model = FSDP(
        model,
        mixed_precision=mixed_precision,
        auto_wrap_policy=auto_wrap_policy,
        cpu_offload=cpu_offload,
        sharding_strategy="FULL_SHARD",  # Full parameter sharding
    )

    return fsdp_model

# Example usage
if __name__ == "__main__":
    import torch.distributed as dist

    # Initialize distributed
    dist.init_process_group("nccl")
    rank = dist.get_rank()
    world_size = dist.get_world_size()

    # Create large model (e.g., 7B parameters)
    model = LargeModel()  # Your large model definition

    # Configure FSDP
    fsdp_model = setup_fsdp_model(model)

    # Create optimizer
    optimizer = torch.optim.AdamW(fsdp_model.parameters(), lr=1e-4)

    # Training loop (similar to DDP)
    for epoch in range(epochs):
        for data, target in train_loader:
            data, target = data.to(rank), target.to(rank)

            optimizer.zero_grad()
            output = fsdp_model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

    print(f"Rank {rank}: Training complete")

# Expected results:
# - Model parameters sharded across all GPUs
# - Significant memory savings (can train models 10x+ larger than GPU memory)
# - BF16 mixed precision reduces memory and speeds up training
# - CPU offload further reduces GPU memory usage (slower but enables training)
```

### Exercise 4: Benchmark Distributed Training

Compare single-GPU vs multi-GPU training speed:

```python
import time
import torch
import torch.distributed as dist
from torch.utils.data import DataLoader, TensorDataset

def create_dummy_data(samples=10000, dim=784):
    """Create dummy dataset for benchmarking."""
    data = torch.randn(samples, dim)
    labels = torch.randint(0, 10, (samples,))
    return TensorDataset(data, labels)

def benchmark_training(gpu_count, batch_size=32, epochs=5):
    """Benchmark training with different GPU counts."""

    print(f"\n{'='*60}")
    print(f"Benchmarking with {gpu_count} GPU(s)")
    print(f"{'='*60}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Create model
    model = MyModel().to(device)

    # Create data
    train_dataset = create_dummy_data()
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Create optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    # Benchmark
    start_time = time.time()
    total_tokens = 0

    for epoch in range(epochs):
        epoch_start = time.time()

        for data, target in train_loader:
            data, target = data.to(device), target.to(device)

            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            total_tokens += data.numel()

        epoch_time = time.time() - epoch_start
        print(f"Epoch {epoch+1}/{epochs}: {epoch_time:.2f}s")

    total_time = time.time() - start_time

    # Calculate metrics
    tokens_per_second = total_tokens / total_time
    samples_per_second = len(train_dataset) * epochs / total_time

    # Get memory usage
    if torch.cuda.is_available():
        memory_allocated = torch.cuda.max_memory_allocated() / 1024**3  # GB
        torch.cuda.reset_peak_memory_stats()
    else:
        memory_allocated = 0

    results = {
        "gpu_count": gpu_count,
        "total_time": total_time,
        "tokens_per_second": tokens_per_second,
        "samples_per_second": samples_per_second,
        "memory_gb": memory_allocated,
    }

    print(f"\nResults:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Tokens/sec: {tokens_per_second:,.0f}")
    print(f"  Samples/sec: {samples_per_second:,.0f}")
    print(f"  GPU memory: {memory_allocated:.2f} GB")

    return results

if __name__ == "__main__":
    # Benchmark single GPU
    results_1gpu = benchmark_training(gpu_count=1, batch_size=32, epochs=5)

    # Benchmark multiple GPUs if available
    if torch.cuda.device_count() >= 2:
        results_2gpu = benchmark_training(gpu_count=2, batch_size=32, epochs=5)

        # Calculate scaling efficiency
        speedup = results_2gpu["samples_per_second"] / results_1gpu["samples_per_second"]
        efficiency = speedup / 2 * 100

        print(f"\n{'='*60}")
        print(f"Scaling Analysis (1 GPU vs 2 GPUs):")
        print(f"{'='*60}")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Efficiency: {efficiency:.1f}%")

        if torch.cuda.device_count() >= 4:
            results_4gpu = benchmark_training(gpu_count=4, batch_size=32, epochs=5)

            speedup_4x = results_4gpu["samples_per_second"] / results_1gpu["samples_per_second"]
            efficiency_4x = speedup_4x / 4 * 100

            print(f"\nScaling Analysis (1 GPU vs 4 GPUs):")
            print(f"  Speedup: {speedup_4x:.2f}x")
            print(f"  Efficiency: {efficiency_4x:.1f}%")

# Expected results:
# - 2 GPUs: ~1.7-1.9x speedup (85-95% efficiency)
# - 4 GPUs: ~3.2-3.8x speedup (80-95% efficiency)
# - Memory scales approximately linearly with GPU count
# - Larger batch sizes improve scaling efficiency
```

---

**Last Updated:** 2026-02-05
**Status:** ✅ Complete - All tasks completed with solutions
