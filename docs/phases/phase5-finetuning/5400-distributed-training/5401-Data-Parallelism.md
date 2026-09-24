---
Document ID: 5401
Title: Data Parallelism
Phase: Unknown
Module: 5400
Last Updated: 2026-02-05
Status: Review
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['documentation']
---

# 5401: Data Parallelism

## Abstract

Data parallelism replicates the model across multiple GPUs, each processing a portion of the batch.

## Types of Data Parallelism

```
┌─────────────────────────────────────────────────────────────┐
│  Data Parallel (DP)                                          │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                       │
│  │GPU 0│  │GPU 1│  │GPU 2│  │GPU 3│                       │
│  │Model│  │Model│  │Model│  │Model│  (Each has full model)  │
│  └─────┘  └─────┘  └─────┘  └─────┘                       │
│     │         │         │         │                         │
│     └─────────┴─────────┴─────────┘                         │
│                    │                                         │
│              Gradients synced                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Distributed Data Parallel (DDP)                             │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                       │
│  │GPU 0│  │GPU 1│  │GPU 2│  │GPU 3│                       │
│  │Model│  │Model│  │Model│  │Model│  (Each has full model)  │
│  └─────┘  └─────┘  └─────┘  └─────┘                       │
│     │         │         │         │                         │
│     └─────────┴─────────┴─────────┘                         │
│              All-Reduce Gradients                            │
│           (Efficient NCCL backend)                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Fully Sharded Data Parallel (FSDP)                          │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                       │
│  │GPU 0│  │GPU 1│  │GPU 2│  │GPU 3│                       │
│  │Shard│  │Shard│  │Shard│  │Shard│  (Model sharded)       │
│  └─────┘  └─────┘  └─────┘  └─────┘                       │
│     │         │         │         │                         │
│     └─────────┴─────────┴─────────┘                         │
│            All-Gather / Reduce-Scatter                       │
└─────────────────────────────────────────────────────────────┘
```

## DDP Implementation

```python
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
import torch.multiprocessing as mp

def setup(rank, world_size):
    """Initialize distributed training."""
    dist.init_process_group(
        backend='nccl',  # Use NCCL for GPU
        rank=rank,
        world_size=world_size,
    )
    torch.cuda.set_device(rank)

def cleanup():
    """Cleanup distributed training."""
    dist.destroy_process_group()

def train_ddp(rank, world_size):
    """Training function for DDP."""

    # Setup
    setup(rank, world_size)

    # Create model and move to GPU
    model = MyModel().to(rank)
    ddp_model = DDP(model, device_ids=[rank])

    # Optimizer
    optimizer = torch.optim.Adam(ddp_model.parameters(), lr=1e-3)

    # Data loader (each GPU gets different data)
    train_sampler = torch.utils.data.distributed.DistributedSampler(
        train_dataset,
        num_replicas=world_size,
        rank=rank,
        shuffle=True,
    )
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=32,
        sampler=train_sampler,
    )

    # Training loop
    for epoch in range(epochs):
        train_sampler.set_epoch(epoch)  # Shuffle differently each epoch

        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(rank), target.to(rank)

            optimizer.zero_grad()
            output = ddp_model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            if rank == 0 and batch_idx % 100 == 0:
                print(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item()}")

    cleanup()

# Launch
if __name__ == "__main__":
    world_size = torch.cuda.device_count()
    mp.spawn(train_ddp, args=(world_size,), nprocs=world_size, join=True)
```

## FSDP Implementation

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import MixedPrecision
from torch.distributed.fsdp import ShardingStrategy

def setup_model_fsdp(rank):
    """Setup model with FSDP."""

    # Create model
    model = MyModel()

    # FSDP config
    fsdp_config = {
        'sharding_strategy': ShardingStrategy.FULL_SHARD,  # Shard everything
        'mixed_precision': MixedPrecision(param_dtype=torch.float16),
        'auto_wrap_policy': ... ,  # When to wrap layers
        'cpu_offload': ... ,  # Offload to CPU if needed
    }

    # Wrap with FSDP
    fsdp_model = FSDP(
        model,
        **fsdp_config,
    ).to(rank)

    return fsdp_model
```

## When to Use Each

| Method | Model Size | GPU Memory | Speed | Complexity |
|--------|------------|------------|-------|------------|
| **DP** | Small | Plenty | Slow | Low |
| **DDP** | Medium | Good | Fast | Medium |
| **FSDP** | Large | Limited | Medium | High |

## Best Practices

1. **Use DDP for most cases:** Best balance of speed and simplicity
2. **Use FSDP for very large models:** When model doesn't fit on one GPU
3. **Gradient accumulation:** Simulate larger batch sizes
4. **Mixed precision:** Always use FP16/BF16 with DDP/FSDP


---

## Next Steps

- Continue with: **[5501-Optimizer-Variants.md](./../5500-advanced-optimization/5501-Optimizer-Variants.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Last Updated:** 2026-02-04
