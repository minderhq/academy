# LAB-503: Distributed Training (DDP)

## Overview
Implement distributed data parallel training with PyTorch DDP.

## Prerequisites
- LAB-202 completed
- Multiple GPUs or multi-GPU machine

## Setup

```bash
pip install torch torchvision
```

## Exercise 1: DDP Setup

```python
import torch
import torch.nn as nn
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
import torch.multiprocessing as mp

def setup(rank, world_size):
    """Initialize distributed training."""
    # TODO: Initialize process group
    dist.init_process_group(
        backend='nccl',  # Use 'gloo' for CPU
        rank=rank,
        world_size=world_size
    )
    torch.cuda.set_device(rank)

def cleanup():
    """Cleanup distributed training."""
    dist.destroy_process_group()
```

## Exercise 2: Wrap Model with DDP

```python
def create_ddp_model(rank):
    """Create and wrap model with DDP."""

    # TODO: Create model
    model = nn.Sequential(
        nn.Linear(784, 256),
        nn.ReLU(),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Linear(128, 10)
    ).to(rank)

    # TODO: Wrap with DDP
    model = DDP(model, device_ids=[rank])

    return model
```

## Exercise 3: Distributed Sampler

```python
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

def create_distributed_dataloader(rank, world_size, batch_size=32):
    """Create dataloader with distributed sampler."""

    # TODO: Load and transform data
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)

    # TODO: Create distributed sampler
    from torch.utils.data.distributed import DistributedSampler

    train_sampler = DistributedSampler(
        train_dataset,
        num_replicas=world_size,
        rank=rank,
        shuffle=True
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        sampler=train_sampler,
        shuffle=False  # Sampler handles shuffle
    )

    return train_loader, train_sampler
```

## Exercise 4: Training Loop with DDP

```python
def train_ddp(rank, world_size, epochs=5):
    """Training function for each process."""

    # Setup
    setup(rank, world_size)

    # TODO: Create model and optimizer
    model = create_ddp_model(rank)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    # TODO: Create dataloader
    train_loader, train_sampler = create_distributed_dataloader(rank, world_size)

    # Training loop
    for epoch in range(epochs):
        # Set epoch for shuffling
        train_sampler.set_epoch(epoch)

        model.train()
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(rank), target.to(rank)

            # TODO: Forward, backward, update
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            if rank == 0 and batch_idx % 100 == 0:
                print(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")

    # Cleanup
    cleanup()
```

## Exercise 5: Launch DDP

```python
if __name__ == "__main__":
    # TODO: Get GPU count
    world_size = torch.cuda.device_count()

    if world_size > 1:
        # TODO: Launch processes
        mp.spawn(train_ddp, args=(world_size,), nprocs=world_size, join=True)
    else:
        print("DDP requires multiple GPUs. Using single GPU.")
        # Fall back to single GPU training
```

## Exercise 6: Monitor DDP Performance

```python
def benchmark_ddp(world_size):
    """Benchmark DDP training speed."""

    import time

    # Different GPU counts
    gpu_counts = [1, 2, 4] if world_size >= 4 else [1, 2]

    results = {}

    for gpus in gpu_counts:
        # Train for 1 epoch
        start = time.time()
        # ... training code ...
        end = time.time()

        results[gpus] = end - start

    # Print results
    for gpus, elapsed in results.items():
        samples_per_sec = len(train_dataset) / elapsed
        print(f"GPUs: {gpus}, Time: {elapsed:.2f}s, Samples/sec: {samples_per_sec:.2f}")
```

## Exercise 7: Gradient Accumulation

```python
def train_with_accumulation(rank, world_size, accumulation_steps=4):
    """Train with gradient accumulation."""

    setup(rank, world_size)
    model = create_ddp_model(rank)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    train_loader, train_sampler = create_distributed_dataloader(rank, world_size, batch_size=32)

    model.train()
    for epoch in range(1):
        train_sampler.set_epoch(epoch)

        optimizer.zero_grad()
        accumulated_loss = 0.0

        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(rank), target.to(rank)

            # Forward
            output = model(data)
            loss = criterion(output, target)
            loss = loss / accumulation_steps  # Normalize

            # Backward
            loss.backward()

            accumulated_loss += loss.item() * accumulation_steps

            # Update every accumulation_steps
            if (batch_idx + 1) % accumulation_steps == 0:
                optimizer.step()
                optimizer.zero_grad()

                if rank == 0:
                    print(f"Step {batch_idx // accumulation_steps}, Loss: {accumulated_loss:.4f}")
                    accumulated_loss = 0.0

    cleanup()
```

## Expected Outputs

1. Exercise 1: Process group initialized
2. Exercise 2: Model wrapped with DDP
3. Exercise 3: Distributed sampler working
4. Exercise 4: Training runs on all GPUs
5. Exercise 5: Multi-process launch working
6. Exercise 6: Speedup visible with more GPUs
7. Exercise 7: Gradient accumulation working

## Troubleshooting

**Issue:** NCCL not available
```python
# Solution: Use gloo backend for CPU
dist.init_process_group(backend='gloo', ...)
```

**Issue:** Each GPU processes all data
```python
# Solution: Ensure DistributedSampler is used
train_sampler = DistributedSampler(...)
```

## Time Estimate: 3-4 hours

---
