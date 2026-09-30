---
Document ID: 5400-PRACTICE
Title: "5400: Distributed Training - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'distributed', 'ddp']
---

# 5400: Distributed Training - Practice

## Exercises

### Exercise 1: Convert Single-GPU Training to DDP

Convert this single-GPU training loop to use DDP:

```python
import os

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
    torch.cuda.set_device(rank)  # each worker must target its own GPU

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

    # Loss follows the original single-GPU script (classification task)
    criterion = torch.nn.CrossEntropyLoss()

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

# Launch training (MyModel and train_dataset come from the original
# single-GPU script above)
if __name__ == "__main__":
    world_size = torch.cuda.device_count()
    mp.spawn(train_ddp, args=(world_size, train_dataset, MyModel), nprocs=world_size)

# Expected Output:
# - Training runs across all available GPUs
# - Each GPU processes a different subset of data
# - Gradients are synchronized across GPUs
# - Speed scales nearly linearly with GPU count (for large batches)
```

### Exercise 2: Implement Gradient Accumulation

Implement gradient accumulation to simulate larger batch sizes:

```python
import torch
from torch.utils.data import DataLoader


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

# Usage (MyModel/criterion come from the original single-GPU script;
# the function derives the device from the model's parameters)
model = MyModel().cuda()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Simulate batch size of 128 with 32 per GPU and 4 accumulation steps
train_with_gradient_accumulation(
    model, train_loader, optimizer, criterion,
    accumulation_steps=4,
    epochs=10
)

# Expected Output:
# Training with gradient accumulation:
#   Per-GPU batch size: 32
#   Accumulation steps: 4
#   Effective batch size: 128
# (epoch/loss lines follow every 100 optimizer steps; loss values
# depend on MyModel and the data)

# Expected benefits:
# - Can train with larger effective batch sizes on limited GPU memory
# - Maintains training stability of larger batches
# - Trade-off: slightly longer training time due to more forward passes
```

### Exercise 3: FSDP Configuration

Configure FSDP for a large model:

```python
import torch
from functools import partial

from torch.distributed.fsdp import (
    CPUOffload,
    FullyShardedDataParallel as FSDP,
    MixedPrecision,
    ShardingStrategy,
)
from torch.distributed.fsdp.wrap import size_based_auto_wrap_policy

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

    # Auto-wrap policy: shard layers larger than 100M parameters.
    # size_based_auto_wrap_policy is the callback FSDP invokes as
    # (module, recurse, min_num_params) - partial() binds the size
    # threshold; calling it directly raises TypeError.
    auto_wrap_policy = partial(
        size_based_auto_wrap_policy, min_num_params=100_000_000
    )

    # Wrap model with FSDP
    fsdp_model = FSDP(
        model,
        mixed_precision=mixed_precision,
        auto_wrap_policy=auto_wrap_policy,
        cpu_offload=cpu_offload,
        # Pass the enum - FSDP does not coerce the "FULL_SHARD" string
        sharding_strategy=ShardingStrategy.FULL_SHARD,
    )

    return fsdp_model

# Example usage
if __name__ == "__main__":
    import torch.distributed as dist

    # Initialize distributed (torchrun sets the MASTER_* env vars)
    dist.init_process_group("nccl")
    rank = dist.get_rank()

    # Create large model (e.g., 7B parameters) and move it to this
    # rank's GPU before wrapping - FSDP shards in place and mixed
    # precision runs on CUDA
    model = LargeModel().to(rank)  # Your large model definition

    # Configure FSDP
    fsdp_model = setup_fsdp_model(model)

    # Create optimizer
    optimizer = torch.optim.AdamW(fsdp_model.parameters(), lr=1e-4)

    # Training loop mirrors Exercise 1's DDP pattern - FSDP is a
    # drop-in wrapper (same forward/backward/step). train_loader,
    # epochs and criterion come from the surrounding training script.
    # Launch with: torchrun --nproc_per_node=<num_gpus> this_file.py
    for epoch in range(epochs):
        for data, target in train_loader:
            data, target = data.to(rank), target.to(rank)

            optimizer.zero_grad()
            output = fsdp_model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

    print(f"Rank {rank}: Training complete")

# Expected Output:
# - Model parameters sharded across all GPUs
# - Significant memory savings (can train models 10x+ larger than GPU memory)
# - BF16 mixed precision reduces memory and speeds up training
# - CPU offload further reduces GPU memory usage (slower but enables training)
```

### Exercise 4: Benchmark Distributed Training

Compare single-GPU vs multi-GPU training speed:

```python
import os
import time

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.data.distributed import DistributedSampler


def create_dummy_data(samples=10000, dim=784):
    """Create dummy dataset for benchmarking."""
    data = torch.randn(samples, dim)
    labels = torch.randint(0, 10, (samples,))
    return TensorDataset(data, labels)


class BenchmarkModel(torch.nn.Module):
    """Small MLP so the benchmark runs without MyModel."""

    def __init__(self, dim=784, num_classes=10):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(dim, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.net(x)


def _ddp_bench(rank, world_size, dataset, batch_size, epochs, results):
    """Worker body: one DDP process per GPU, timed on rank 0."""
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = "12356"
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

    sampler = DistributedSampler(
        dataset, num_replicas=world_size, rank=rank, shuffle=True
    )
    loader = DataLoader(dataset, batch_size=batch_size, sampler=sampler)

    model = DDP(BenchmarkModel().to(rank), device_ids=[rank])
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.CrossEntropyLoss()

    torch.cuda.synchronize(rank)
    start_time = time.time()

    for epoch in range(epochs):
        epoch_start = time.time()
        sampler.set_epoch(epoch)

        for data, target in loader:
            data, target = data.to(rank), target.to(rank)
            optimizer.zero_grad()
            loss = criterion(model(data), target)
            loss.backward()
            optimizer.step()

        if rank == 0:
            torch.cuda.synchronize(rank)
            print(f"Epoch {epoch+1}/{epochs}: {time.time() - epoch_start:.2f}s")

    # rank 0's wall time covers the slowest rank each step (DDP
    # gradient all-reduce), so it is the honest end-to-end number
    if rank == 0:
        torch.cuda.synchronize(rank)
        total_time = time.time() - start_time
        results["total_time"] = total_time
        results["samples_per_second"] = len(dataset) * epochs / total_time
        results["memory_gb"] = torch.cuda.max_memory_allocated() / 1024**3
        torch.cuda.reset_peak_memory_stats()  # fresh peak for the next config
    dist.destroy_process_group()


def benchmark_training(gpu_count, batch_size=32, epochs=5):
    """Benchmark DDP training, one process per GPU.

    Every configuration uses its actual GPU count (capped by the
    hardware) - looping single-device code while printing "2 GPUs"
    would report a speedup of ~1.0x, not the hardware's scaling.
    """

    world_size = max(1, min(gpu_count, torch.cuda.device_count()))
    print(f"\n{'='*60}")
    print(f"Benchmarking with {world_size} GPU(s)")
    print(f"{'='*60}")

    train_dataset = create_dummy_data()

    manager = mp.Manager()
    results = manager.dict()
    mp.spawn(
        _ddp_bench,
        args=(world_size, train_dataset, batch_size, epochs, results),
        nprocs=world_size,
    )
    results = dict(results)

    print(f"\nResults:")
    print(f"  Total time: {results['total_time']:.2f}s")
    print(f"  Samples/sec: {results['samples_per_second']:,.0f}")
    print(f"  GPU memory: {results['memory_gb']:.2f} GB")

    return results


if __name__ == "__main__":
    if torch.cuda.device_count() == 0:
        raise SystemExit(
            "This benchmark needs CUDA - DDP's NCCL backend requires GPUs"
        )

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

# Expected Output:
# ============================================================
# Benchmarking with 1 GPU(s)
# ============================================================
# Epoch 1/5: ...
# ...
# Epoch 5/5: ...
#
# Results:
#   Total time: ...
#   Samples/sec: ...
#   GPU memory: ... GB
#
# (absolute numbers are hardware-dependent; the Scaling Analysis
# blocks print only when 2+/4+ GPUs are present - this benchmark
# needs a CUDA machine, DDP's NCCL backend requires GPUs)
```
