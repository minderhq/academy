---
Document ID: 5404
Title: Distributed Optimization
Phase: 5
Module: 5400
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['distributed', 'zero', 'deepspeed', 'communication', 'training']
---

# 5404: Distributed Optimization

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [All-Reduce: The Workhorse Collective](#all-reduce-the-workhorse-collective)
- [ZeRO: Sharding the Optimizer State](#zero-sharding-the-optimizer-state)
- [DeepSpeed in Practice](#deepspeed-in-practice)
- [Overlap Mechanics](#overlap-mechanics)
- [Gradient Compression](#gradient-compression)
- [Communication Backends](#communication-backends)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Derive the bandwidth cost of ring all-reduce and say why NCCL's hybrid beats hand-rolled collectives
- Compute the per-GPU memory of ZeRO stages 1, 2, and 3 from the 16N ledger
- Configure DeepSpeed ZeRO-2 and ZeRO-3 (with offloading) from a JSON config
- Explain what DDP's bucketed overlap does per-hook and when exposed communication shows up in a profile
- Describe why compression (PowerSGD, sparsification + error feedback) is rarely the answer on modern interconnects

---

## Abstract

[5401](./5401-Data-Parallelism.md) covered the DDP/FSDP mechanics and [5402](./5402-Model-Parallelism.md) the splitting axes; this lesson covers the layer underneath them — the *optimization-side* machinery of a distributed run. That means the all-reduce collective and its bandwidth math, the ZeRO stages that shard optimizer state (the 12N from the memory ledger), DeepSpeed as the production vehicle for those stages with CPU/NVMe offloading, the bucketing that hides communication inside backward, and an honest assessment of gradient compression.

## All-Reduce: The Workhorse Collective

Every data-parallel step ends with the same collective: sum (or average) one tensor across all ranks so every rank holds the identical result.

### Ring All-Reduce: The Bandwidth Math

```text
Two phases over a logical ring of N ranks, tensor split into N chunks

phase 1  REDUCE-SCATTER        N-1 steps: each rank sends one chunk
                               right, receives one from the left,
                               adds it into its local chunk
                               -> each rank ends owning ONE fully
                                  reduced chunk
phase 2  ALL-GATHER            N-1 steps: the reduced chunks walk
                               the ring until every rank has all

Data each rank SENDS: 2 * (N-1)/N * size
-> bandwidth-optimal: at N=8, each rank transmits 1.75x the
   tensor regardless of where it sits, and the ring keeps every
   link busy every step
```

```text
Tree all-reduce (recursive halving/doubling): 2 * log(N) steps
- fewer STEPS (latency-optimal) but moves more total bytes
- wins on small tensors and high-latency links

NCCL ships hybrids (ring, halving-doubling, tree per topology)
and picks per message size + topology. Never hand-roll these
collectives for training: NCCL is tuned for NVLink/NVSwitch/IB
topologies beyond what a page of code can reach. The math above
matters because it tells you WHAT you are paying per step and
WHEN the collective becomes the bottleneck.
```

## ZeRO: Sharding the Optimizer State

The optimizer is the memory hog (12 of every 16 bytes per param under AdamW mixed precision — [5501](../5500-advanced-optimization/5501-Optimizer-Variants.md)). ZeRO (Zero Redundancy Optimizer) removes the redundancy by sharding that state across data-parallel ranks instead of replicating it.

```text
Mixed-precision state (fp32 accounting):  weights 4N | grads 4N | m+v 8N

Stage   Shards                        Per-GPU memory     Comm pattern
-----   --------------------------    ----------------   ----------------------
ZeRO-1  optimizer state only          4N + 4N + 8N/W     same as DDP
        (m, v)                                           (all-reduce grads)
ZeRO-2  + gradients                   4N + 6N/W          reduce-SCATTER grads
        (each rank keeps only its                        (each rank only
        shard of grads)                                  needs its own shard)
ZeRO-3  + parameters                  16N/W              all-gather params per
        (= FSDP FULL_SHARD, 5401)                        layer fwd + bwd

Offload extensions
ZeRO-Offload    stage 2 + optimizer state/step on CPU RAM
ZeRO-Infinity   + parameters paged via NVMe (train what cannot fit
                anywhere else - bandwidth is the new currency)
```

```text
Reading the stages
- ZeRO-2 is the sweet spot when the MODEL still fits on one GPU:
  optimizer memory scales down 1/W, communication stays
  DDP-cheap, no parameter all-gathers
- ZeRO-3 (FSDP) is for when the model itself no longer fits -
  you pay per-layer all-gathers for it
- Offload trades PCIe/NVMe bandwidth for HBM: only when sharding
  alone is not enough, and expect 20-40% step slowdown
- 7B model at W=8: plain DDP 112GB -> ZeRO-2 ~53GB -> ZeRO-3 ~14GB
  (16N accounting, before activations)
```

## DeepSpeed in Practice

DeepSpeed is the production vehicle for the ZeRO stages. The whole policy lives in one JSON config:

```json
{
  "train_micro_batch_size_per_gpu": 4,
  "gradient_accumulation_steps": 8,
  "bf16": { "enabled": true },
  "zero_optimization": {
    "stage": 2,
    "contiguous_gradients": true,
    "overlap_comm": true,
    "reduce_scatter": true,
    "offload_optimizer": { "device": "none" }
  },
  "optimizer": {
    "type": "AdamW",
    "params": {
      "lr": 2e-5,
      "betas": [0.9, 0.999],
      "weight_decay": 0.01
    }
  }
}
```

```python
import deepspeed

model_engine, optimizer, _, _ = deepspeed.initialize(
    model=model,
    model_parameters=model.parameters(),
    config_path="ds_config.json",
)

for batch in loader:
    with model_engine.accumulate():        # handles grad accumulation
        loss = model_engine(batch)
        model_engine.backward(loss)
        model_engine.step()
```

Scaling up to ZeRO-3 with offloading is a config edit, not a code change:

```json
{
  "zero_optimization": {
    "stage": 3,
    "overlap_comm": true,
    "contiguous_gradients": true,
    "reduce_bucket_size": 5e8,
    "stage3_prefetch_bucket_size": 5e8,
    "stage3_param_persistence_threshold": 1e6,
    "offload_optimizer": { "device": "cpu", "pin_memory": true },
    "offload_param": { "device": "cpu", "pin_memory": true }
  }
}
```

```text
Choosing the stage (start low, escalate on OOM)

fits without ZeRO?        stage 0 (= plain DDP)
OOM in optimizer state?   stage 2        <- most fine-tuning jobs
OOM in the model itself?  stage 3        (or FSDP, same idea)
still OOM?                offload cpu, then nvme
throughput regressed?     back off one stage - every stage buys
                          memory with communication
```

## Overlap Mechanics

[5401](./5401-Data-Parallelism.md) established the principle; here is the accounting that tells you whether overlap is actually working:

```text
What DDP does per backward pass (hook-based, automatic)
1. grads finish for one bucket (~25MB default, bucket_cap_mb)
2. an ASYNC all-reduce launches on the NCCL stream
3. backward continues on the compute stream - the all-reduce
   hides under remaining compute
4. only the LAST bucket's comm is exposed (nothing left to
   hide behind)

ZeRO-2's reduce-scatter overlaps the same way (overlap_comm,
contiguous_gradients in the config above)

Tuning knob and symptom
- profile the backward pass: the gap between "gradients ready"
  and "optimizer step" is EXPOSED communication
- exposed comm > 15% of step time: bigger buckets (less latency
  overhead) OR fewer ranks in the all-reduce group OR a faster
  interconnect - never "async everything manually"
```

Manual async collectives are for special cases only — e.g., overlapping sync with unrelated work:

```python
handle = torch.distributed.all_reduce(param.grad, async_op=True)
compute_unrelated_metrics()      # genuinely independent work
handle.wait()
param.grad.div_(torch.distributed.get_world_size())
```

Chaining these per-parameter over a whole model re-implements DDP badly (many small collectives, no overlap against backward) — prefer the framework hooks.

## Gradient Compression

The bandwidth math says all-reduce moves ~2x the gradient per step. Compression attacks that 2x — and on modern clusters it almost never pays:

```text
Options, honestly rated

error feedback + sparsification   send top-k values per step,
                                  accumulate the DROPPED residual
                                  locally and add it to the next
                                  step's gradient (else top-k
                                  silently biases the model)
                                  -> 10x comm reduction possible,
                                     accuracy risk needs eval

PowerSGD                          compress via low-rank
                                  (random orthogonal) projection
                                  + error feedback; PyTorch ships
                                  it as a DDP hook
                                  (torch.distributed.algorithms.
                                   power_sgd) - the production-
                                   adjacent choice
1-bit / quantized gradients       research lineage (1-bit SGD,
                                  QSGD); fragile, rarely shipped

The verdict on NVLink/IB clusters
- compute:comm ratio is usually >10:1 per step already
- compression buys bandwidth you are not short of, and costs
  accuracy risk + debugging time
- reach for it only on Ethernet-only commodity clusters or when
  profiling proves comm-exposed time > 20%
```

## Communication Backends

| Backend | Devices | Use when | Notes |
|---|---|---|---|
| NCCL | GPU | Always, for GPU training | NVLink/NVSwitch/IB aware, auto topology detection — the default |
| Gloo | CPU (GPU fallback) | CPU training, debugging, CI | `init_process_group(backend="gloo")`; lets you smoke-test distributed code without GPUs |
| MPI | HPC | Existing MPI-managed clusters | Collective semantics, scheduler integration |

```python
import torch.distributed as dist

# GPU training (default everywhere)
dist.init_process_group(backend="nccl", init_method="env://")

# CPU-only smoke test - same code, different backend
dist.init_process_group(backend="gloo", init_method="env://")
```

## Best Practices

```text
1. Escalate ZeRO stages by SYMPTOM: optimizer OOM -> stage 2,
   model OOM -> stage 3, still OOM -> offload. Do not start at
   stage 3 "to be safe" - it costs all-gathers you may not need
2. bf16 (5403) before any offloading - offload is the most
   expensive memory lever you have
3. Keep DeepSpeed config in the repo, versioned with the run;
   reproduce failed runs from config + data hash, not memory
4. Profile exposed communication before optimizing it - the
   15% rule decides whether bucket tuning, compression, or a
   topology change is the right lever
5. Gloo backend for CI smoke tests of distributed code paths;
   NCCL for anything with real throughput claims
6. Elastic training (torchrun --max-restarts, elastic agent)
   tolerates node loss in long runs - plan for it in multi-day
   jobs
7. Skip compression until a profile demands it; when it does,
   PowerSGD with error feedback, evaluated against a loss curve,
   not vibes
```

---

## References

### Related ai-engineering-curriculum Documents

- [5401: Data Parallelism](5401-Data-Parallelism.md)
- [5402: Model Parallelism](5402-Model-Parallelism.md)
- [5403: Mixed Precision Training](5403-Mixed-Precision.md)
- [5501: Optimizer Variants](../5500-advanced-optimization/5501-Optimizer-Variants.md)

---

## Next Steps

- Module 5400 complete! Next: **[5501: Optimizer Variants](../5500-advanced-optimization/5501-Optimizer-Variants.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
