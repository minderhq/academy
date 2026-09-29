---
Document ID: 5401
Title: "5401: Data Parallelism"
Phase: 5
Module: 5400
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['distributed', 'ddp', 'fsdp', 'training', 'gpu']
---

# 5401: Data Parallelism

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Data-Parallel Idea](#the-data-parallel-idea)
- [Communication Anatomy](#communication-anatomy)
- [DDP Implementation](#ddp-implementation)
- [FSDP Implementation](#fsdp-implementation)
- [Memory Ledger](#memory-ledger)
- [When to Use Each](#when-to-use-each)
- [Best Practices](#best-practices)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain how data parallelism splits batches while replicating the model
- Trace what DDP communicates (gradients, bucketed and overlapped) versus what FSDP communicates (parameters, per-layer)
- Launch a correct DDP job with torchrun, DistributedSampler, and gradient accumulation
- Configure FSDP sharding strategies, mixed precision, and transformer auto-wrapping
- Choose between DDP and FSDP from a per-GPU memory ledger

---

## Abstract

Data parallelism is the workhorse of multi-GPU training: replicate the model on every GPU, give each replica a different slice of the batch, and average the gradients so all replicas stay identical. The two PyTorch implementations you will actually use are **DDP** (each GPU holds the full model and optimizer) and **FSDP** (model, gradients, and optimizer state are sharded across GPUs and assembled on the fly). This lesson covers the communication pattern of each, working implementations with the modern torchrun launcher, the memory math that decides between them, and the practices that separate a fast distributed job from a slow one. When the model is too large even for FSDP, you need model parallelism — [5402](./5402-Model-Parallelism.md).

## The Data-Parallel Idea

```text
                     batch (global size 4B)
                              |
              split into W equal shards, one per GPU

  GPU 0          GPU 1          GPU 2          GPU 3
+--------+     +--------+     +--------+     +--------+
| model  |     | model  |     | model  |     | model  |   <- identical weights
| copy   |     | copy   |     | copy   |     | copy   |
+--------+     +--------+     +--------+     +--------+
| shard  |     | shard  |     | shard  |     | shard  |   <- B samples each
| B      |     | B      |     | B      |     | B      |
+--------+     +--------+     +--------+     +--------+
     |              |              |              |
   grad_0         grad_1         grad_2         grad_3
     |              |              |              |
     +--------- all-reduce (mean) --+--------------+
                          |
              every GPU now holds the SAME averaged gradient
                          |
                    optimizer.step()  (independent, identical)
```

Correctness requirements fall out of the picture:

```text
1. Identical start     all replicas load the same weights at init
2. Identical update    gradient all-reduce BEFORE optimizer.step()
3. Disjoint data       DistributedSampler shards the dataset;
                       set_epoch() reshuffles per epoch
4. Effective batch     global_batch = per_gpu_batch x world_size
                       x grad_accum_steps
```

## Communication Anatomy

DDP synchronizes **gradients**; FSDP communicates **parameters**. Understanding which bytes move when is the difference between a 2× and a 3.5× speedup.

### DDP: Bucketed, Overlapped All-Reduce

```text
Backward pass, layer by layer (deepest layer finishes first)

  grad(L_n) ready -> dropped into a BUCKET
  bucket full (default ~25 MB)     -> all-reduce STARTS
  all-reduce runs ON THE NCCL STREAM while
  remaining layers still compute their grads

Result: most communication hides behind compute.
Only the straggler bucket at the end of backward is exposed.
```

Practical consequences:

```text
- Fewer, larger buckets = less latency overhead, less overlap
  granularity. Tune bucket_cap_mb when profiling.
- find_unused_parameters=True disables some overlap and costs
  throughput - avoid it by pruning dead branches from the model.
```

### FSDP: All-Gather Forward, All-Gather + Reduce-Scatter Backward

```text
FSDP shards: params, grads, optimizer state (FULL_SHARD)

Forward (per FSDP unit):
  all-gather full params  -> compute -> free borrowed params
Backward (per FSDP unit):
  all-gather params again -> compute grads
  reduce-scatter grads    -> each GPU keeps only its shard

Communication volume ~= 2x DDP for params + grad reduce,
BUT peak memory per GPU ~= total / world_size.
```

## DDP Implementation

### Training Script

```python
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler

def main():
    dist.init_process_group(backend="nccl")
    rank = dist.get_rank()
    world = dist.get_world_size()
    torch.cuda.set_device(rank)

    model = build_model().cuda()
    ddp_model = DDP(model, device_ids=[rank],
                    gradient_as_bucket_view=True)   # grads alias buckets: less memory

    optimizer = torch.optim.AdamW(ddp_model.parameters(), lr=1e-4, fused=True)

    sampler = DistributedSampler(train_dataset, num_replicas=world,
                                 rank=rank, shuffle=True)
    loader = DataLoader(train_dataset, batch_size=32, sampler=sampler,
                        pin_memory=True, num_workers=4)

    epochs = 3  # demo scale
    for epoch in range(epochs):
        sampler.set_epoch(epoch)          # REQUIRED: reshuffle per epoch
        for step, batch in enumerate(loader):
            inputs = batch["x"].cuda(non_blocking=True)
            labels = batch["y"].cuda(non_blocking=True)

            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = ddp_model(inputs, labels).loss

            loss.backward()
            torch.nn.utils.clip_grad_norm_(ddp_model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)

            if rank == 0 and step % 100 == 0:
                print(f"epoch {epoch} step {step} loss {loss.item():.4f}")

    dist.destroy_process_group()

if __name__ == "__main__":
    main()
```

### Launching with torchrun

```bash
# modern launcher (replaces mp.spawn entirely)
torchrun --nproc_per_node=4 train.py

# multi-node: identical command on each machine, plus
torchrun --nproc_per_node=8 --nnodes=2 --node_rank=0 \
         --rdzv_endpoint=master:29500 train.py
```

`init_process_group` reads rank/world size from torchrun's environment — no `mp.spawn`, no hand-managed process pool, and a uniform code path from 1 to N machines.

### Gradient Accumulation Under DDP

Naive accumulation all-reduces on every micro-batch — pure waste. Skip the sync on accumulation steps:

```python
sync_context = ddp_model.no_sync() if (step % ACC) != ACC - 1 else nullcontext()
with sync_context:
    loss = loss / ACC
    loss.backward()
    if (step % ACC) == ACC - 1:
        optimizer.step(); optimizer.zero_grad(set_to_none=True)
```

## FSDP Implementation

```python
import functools
import torch
import torch.distributed as dist
from torch.distributed.fsdp import (
    FullyShardedDataParallel as FSDP,
    MixedPrecision,
    ShardingStrategy,
    StateDictType,
)
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy

# for a Hugging Face model, wrap at decoder-layer granularity
import transformers
from transformers.models.llama.modeling_llama import LlamaDecoderLayer

mp_policy = MixedPrecision(
    param_dtype=torch.bfloat16,       # compute dtype for params
    reduce_dtype=torch.float32,       # dtype for grad reduction
    buffer_dtype=torch.bfloat16,
)

auto_wrap = functools.partial(
    transformer_auto_wrap_policy,
    transformer_layer_cls={LlamaDecoderLayer},   # one FSDP unit per layer
)

model = FSDP(
    model,
    auto_wrap_policy=auto_wrap,
    mixed_precision=mp_policy,
    sharding_strategy=ShardingStrategy.FULL_SHARD,  # params+grads+optimizer
    limit_all_gathers=True,            # overlap control: prefetch only next unit
    device_id=dist.get_rank(),
)
```

```text
Sharding strategies, ranked by memory saved

FULL_SHARD        shard params, grads, optimizer state   max savings
SHARD_GRAD_OP     shard grads + optimizer only           less comm, more mem
NO_SHARD          = DDP behavior                         fallback
HYBRID_SHARD      full-shard within node, DDP across     8x-node sweet spot
```

Checkpointing is the classic FSDP footgun — shards must be gathered before saving:

```python
with FSDP.state_dict_type(model, StateDictType.FULL_STATE_DICT):
    state = model.state_dict()          # rank 0 gets full weights
    if dist.get_rank() == 0:
        torch.save(state, "ckpt.pt")
```

## Memory Ledger

Per-GPU footprint for a 7B model, bf16 compute, fp32 master/moments (from the [5501](../5500-advanced-optimization/5501-Optimizer-Variants.md) ledger):

```text
Method      params   grads    optimizer   PEAK TOTAL (7B model)
----------+--------+--------+-----------+----------------------
DP          14 GB    14 GB     84 GB      ~112 GB  (does not fit)
DDP         14 GB    14 GB     84 GB      ~112 GB  (same; DP != smaller)
FSDP        14/W GB  14/W GB   84/W GB    ~16 GB at W=8 (+activations)
```

```text
Reading the ledger
- DP vs DDP differ in SPEED, not memory - both replicate everything
- FSDP divides model state by world_size, but activations do NOT
  shard - long sequences can still OOM a fully-sharded run
- CPU offloading (shard to host RAM) trades bandwidth for memory:
  use only when sharding alone is not enough
```

## When to Use Each

| Method | Fits when | Communication | Relative speed | Complexity |
|---|---|---|---|---|
| DP (nn.DataParallel) | Never, on modern stacks | Python-thread scatter/gather, GIL-bound | Baseline (slow) | Trivial |
| DDP | Model + optimizer fit on one GPU | Grad all-reduce, overlapped | Fastest | Low |
| FSDP FULL_SHARD | Model does not fit; scale with W | Param all-gathers ×2 | ~70-85% of DDP | Medium |
| Hybrid | Multi-node, big model | Mixed | Best at 8×N | Medium |

```text
Rules of thumb
- Single node, model fits:        DDP (or FSDP NO_SHARD if you want
                                  one code path for both)
- Single node, model tight:       FSDP FULL_SHARD
- Multi-node, per-node fits:      HYBRID_SHARD
- Model >> FSDP tolerance:        tensor/pipeline parallelism (5402)
                                  or ZeRO-style sharded optimizer (5404)
```

## Best Practices

```text
1. torchrun everywhere - one launcher, local and multi-node;
   never mp.spawn in new code
2. sampler.set_epoch(epoch) every epoch, or every GPU sees the
   same data order forever (silent generalization hit)
3. bf16 autocast by default; fp32 only for the reduction
   (MixedPrecision reduce_dtype) - see 5403 for the details
4. Accumulate with no_sync(), clip after accumulation
5. profile with torch.profiler: backward-comm gap is the number
   to drive toward zero; if exposed comm > 15%, raise bucket size
   (DDP) or check limit_all_gathers (FSDP)
6. identical seeds on all ranks EXCEPT for data-order seeds;
   log from rank 0 only, with synchronized metrics
7. save checkpoints under state_dict_type context managers -
   raw state_dict() on an FSDP model returns SHARDS
```

---

## Summary

Data parallelism is the workhorse of multi-GPU training: replicate the model on every GPU, give each replica a different batch slice, and average the gradients so replicas stay identical. This lesson dissected the communication anatomy, then built the two implementations you actually use - DDP holding the full model per GPU and FSDP sharding it - and closed each with the memory ledger that shows where the bytes go. The decision is mechanical once the ledger is on the table: model fits per-GPU means DDP, it does not fit means FSDP, and best practices keep both honest.

## References

### Related PROJECT-OMEGA Documents

- [5402: Model Parallelism](5402-Model-Parallelism.md)
- [5403: Mixed Precision Training](5403-Mixed-Precision.md)
- [5404: Distributed Optimization](5404-Distributed-Optimization.md)

---

## Next Steps

- Continue with: **[5402: Model Parallelism](./5402-Model-Parallelism.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [5501: Optimizer Variants](../5500-advanced-optimization/5501-Optimizer-Variants.md)
- [5102: QLoRA Pipelines](../5100-peft/5102-QLoRA-Pipelines.md)
