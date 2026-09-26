---
Document ID: 5404
Title: Distributed Optimization
Phase: 5
Module: 5400
Last Updated: 2026-09-26
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
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Derive the bandwidth cost of ring all-reduce and say why NCCL's hybrid beats hand-rolled collectives — and verify both the chunk choreography and the 2(N−1)/N law with the runnable simulation below
- Compute the per-GPU memory of ZeRO stages 1, 2, and 3 from the 16N ledger with the runnable calculator below
- Configure DeepSpeed ZeRO-2 and ZeRO-3 (with offloading) from a JSON config
- Explain what DDP's bucketed overlap does per-hook and when exposed communication shows up in a profile — and run a real async all-reduce against a gloo process group
- Describe why compression (PowerSGD, sparsification + error feedback) is rarely the answer on modern interconnects, with measured evidence for what error feedback actually buys

---

## Abstract

[5401](./5401-Data-Parallelism.md) covered the DDP/FSDP mechanics and [5402](./5402-Model-Parallelism.md) the splitting axes; this lesson covers the layer underneath them — the *optimization-side* machinery of a distributed run. That means the all-reduce collective and its bandwidth math, the ZeRO stages that shard optimizer state (the 12N from the memory ledger), DeepSpeed as the production vehicle for those stages with CPU/NVMe offloading, the bucketing that hides communication inside backward, and an honest assessment of gradient compression.

## All-Reduce: The Workhorse Collective

Every data-parallel step ends with the same collective: sum (or average) one tensor across all ranks so every rank holds the identical result.

### Ring All-Reduce: The Bandwidth Math

```text
Two phases over a logical ring of N ranks, tensor split into N chunks

phase 1  REDUCE-SCATTER        N-1 steps: each rank sends one chunk
                               around the ring, receives one from
                               its neighbor, adds it into its
                               local chunk
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

The simulation below plays both ring phases chunk-by-chunk on plain lists — each rank really receives, adds, and forwards — then checks every rank ends with the full sum and prints the wire cost:

```python
def ring_reduce_scatter(chunks):
    n = len(chunks)
    for step in range(n - 1):
        outgoing = [row[:] for row in chunks]
        for r in range(n):
            src = (r - 1) % n                       # receive from the left
            idx = (r - step - 1) % n                # chunk rotating this step
            chunks[r][idx] += outgoing[src][idx]

def ring_all_gather(chunks):
    n = len(chunks)
    for step in range(n - 1):
        outgoing = [row[:] for row in chunks]
        for r in range(n):
            src = (r + 1) % n                       # receive from the right
            idx = (r + 2 + step) % n                # reduced chunk src holds
            chunks[r][idx] = outgoing[src][idx]

rows = [[1, 2, 3, 4],
        [10, 20, 30, 40],
        [100, 200, 300, 400],
        [1000, 2000, 3000, 4000]]
n = len(rows)
chunks = [row[:] for row in rows]
ring_reduce_scatter(chunks)
ring_all_gather(chunks)
truth = [sum(rows[r][c] for r in range(n)) for c in range(n)]
print("N=%d ranks | steps: %d reduce-scatter + %d all-gather = %d total"
      % (n, n - 1, n - 1, 2 * (n - 1)))
print("chunk sums:", truth)
print("all ranks hold the full result:", all(chunks[r] == truth for r in range(n)))
print("per-rank bytes on the wire (2*(W-1)/W of the tensor) vs tree steps:")
for world in (2, 4, 8, 16, 64):
    print("  W=%2d: ring %.3fx tensor, %2d steps | tree %2d steps"
          % (world, 2 * (world - 1) / world, 2 * (world - 1),
             2 * (world - 1).bit_length()))
```

**Output:**

```text
N=4 ranks | steps: 3 reduce-scatter + 3 all-gather = 6 total
chunk sums: [1111, 2222, 3333, 4444]
all ranks hold the full result: True
per-rank bytes on the wire (2*(W-1)/W of the tensor) vs tree steps:
  W= 2: ring 1.000x tensor,  2 steps | tree  2 steps
  W= 4: ring 1.500x tensor,  6 steps | tree  4 steps
  W= 8: ring 1.750x tensor, 14 steps | tree  6 steps
  W=16: ring 1.875x tensor, 30 steps | tree  8 steps
  W=64: ring 1.969x tensor, 126 steps | tree 12 steps
```

The table is the bandwidth law made concrete: ring's per-rank cost pins at 2× as W→∞ but never exceeds it, while tree halves its step count every doubling — the small-W latency win the math above predicts.

## ZeRO: Sharding the Optimizer State

The optimizer is the memory hog (12 of every 16 bytes per param under AdamW mixed precision — [5501](../5500-advanced-optimization/5501-Optimizer-Variants.md)). ZeRO (Zero Redundancy Optimizer) removes the redundancy by sharding that state across data-parallel ranks instead of replicating it.

```text
Mixed-precision state (fp32 accounting):  weights 4N | grads 4N | m+v 8N

Stage   Shards                        Per-GPU memory     Comm pattern
-----   --------------------------    ----------------   ----------------------
ZeRO-1  optimizer state only          4N + 4N + 8N/W    same as DDP
        (m, v)                                          (all-reduce grads)
ZeRO-2  + gradients                   4N + 12N/W        reduce-SCATTER grads
        (each rank keeps only its                       (each rank only
        shard of grads)                                 needs its own shard)
ZeRO-3  + parameters                  16N/W             all-gather params per
        (= FSDP FULL_SHARD, 5401)                       layer fwd + bwd

Offload extensions
ZeRO-Offload    stage 2 + optimizer state/step on CPU RAM
ZeRO-Infinity   + parameters paged via NVMe (train what cannot fit
                anywhere else - bandwidth is the new currency)
```

```text
Reading the stages
- ZeRO-2 is the sweet spot when the MODEL still fits on one GPU:
  grads + optimizer memory scale down 1/W, communication stays
  DDP-cheap, no parameter all-gathers
- ZeRO-3 (FSDP) is for when the model itself no longer fits -
  you pay per-layer all-gathers for it
- Offload trades PCIe/NVMe bandwidth for HBM: only when sharding
  alone is not enough, and expect 20-40% step slowdown
- 7B model at W=8: plain DDP 112GB -> ZeRO-1 63GB -> ZeRO-2
  38.5GB -> ZeRO-3 14GB (16N accounting, before activations -
  the runnable calculator below reproduces every row)
```

The calculator applies the ledger directly — each stage shards one more component by the world size:

```python
def zero_bytes(params, world, stage):
    """Optimizer-state memory per GPU under the 16N ledger (fp32 master)."""
    n = params
    weights, grads, optim = 4 * n, 4 * n, 8 * n   # fp32 copies
    if stage == 0:
        return weights + grads + optim            # plain DDP
    if stage == 1:
        return weights + grads + optim / world
    if stage == 2:
        return weights + (grads + optim) / world
    return (weights + grads + optim) / world      # ZeRO-3

GB = 1e9
params, world = 7e9, 8
print("7B model on %d GPUs (16N ledger, activations excluded):" % world)
for stage in range(4):
    print("  stage %d: %5.1f GB/GPU" % (stage, zero_bytes(params, world, stage) / GB))
print("stage 2 as the world grows:")
for w in (2, 4, 8, 16):
    print("  W=%2d: %5.1f GB/GPU" % (w, zero_bytes(params, w, 2) / GB))
```

**Output:**

```text
7B model on 8 GPUs (16N ledger, activations excluded):
  stage 0: 112.0 GB/GPU
  stage 1:  63.0 GB/GPU
  stage 2:  38.5 GB/GPU
  stage 3:  14.0 GB/GPU
stage 2 as the world grows:
  W= 2:  70.0 GB/GPU
  W= 4:  49.0 GB/GPU
  W= 8:  38.5 GB/GPU
  W=16:  33.2 GB/GPU
```

Note the diminishing returns in the second table: ZeRO-2's fixed 4N weights floor the savings, which is exactly why stage 2 + offload (not more ranks) is the next lever once the model weights themselves get tight.

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

DeepSpeed is not installed in this repo's environment, so the engine call is a sketch — the JSON above is the real contract, and the training loop barely changes:

```text
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

Manual async collectives are for special cases only — overlapping sync with genuinely independent work. The pattern below runs for real on a gloo process group (world_size=1 stands in for the NCCL farm; the API shape is identical):

```python
import torch
import torch.distributed as dist

# torchrun supplies env:// variables; standalone we pass them explicitly
dist.init_process_group(backend="gloo",
                        init_method="tcp://127.0.0.1:29541",
                        rank=0, world_size=1)
torch.manual_seed(0)
grad = torch.randn(4096)
snapshot = grad.clone()

handle = dist.all_reduce(grad, async_op=True)     # returns before the wire finishes
independent = sum(i * i for i in range(50_000))   # work that overlaps the transfer
handle.wait()
grad.div_(dist.get_world_size())                  # all-reduce sums; DDP then averages

print("world_size: %d | backend: %s" % (dist.get_world_size(), dist.get_backend()))
print("overlapped compute completed while the collective was in flight:", independent)
print("identity all-reduce at ws=1 (grad unchanged):", torch.equal(grad, snapshot))
dist.destroy_process_group()
```

**Output:**

```text
world_size: 1 | backend: gloo
overlapped compute completed while the collective was in flight: 41665416675000
identity all-reduce at ws=1 (grad unchanged): True
```

Chaining this per-parameter over a whole model re-implements DDP badly (many small collectives, no overlap against backward) — prefer the framework hooks.

## Gradient Compression

The bandwidth math says all-reduce moves ~2x the gradient per step. Compression attacks that 2x — and on modern clusters it almost never pays:

```text
Options, honestly rated

error feedback + sparsification   send top-k values per step,
                                  accumulate the DROPPED residual
                                  locally and add it to the next
                                  step's gradient (else top-k
                                  silently biases the model -
                                  the runnable demo below
                                  quantifies the drift)
                                  -> 10x comm reduction possible,
                                     accuracy risk needs eval

PowerSGD                          compress via low-rank
                                  (random orthogonal) projection
                                  + error feedback; PyTorch ships
                                  it as a DDP comm hook
                                  (torch.distributed.algorithms.
                                   ddp_comm_hooks.powerSGD_hook)
                                  - the production-adjacent choice
1-bit / quantized gradients       research lineage (1-bit SGD,
                                  QSGD); fragile, rarely shipped

The verdict on NVLink/IB clusters
- compute:comm ratio is usually >10:1 per step already
- compression buys bandwidth you are not short of, and costs
  accuracy risk + debugging time
- reach for it only on Ethernet-only commodity clusters or when
  profiling proves comm-exposed time > 20%
```

The demo compresses one fixed gradient repeatedly and measures how far the receiver's accumulated reconstruction drifts from the truth — plain top-k versus top-k with the residual fed back:

```python
import torch

def compress_topk(t, k):
    """Keep the k largest-magnitude entries, zero the rest."""
    idx = t.abs().topk(k).indices
    out = torch.zeros_like(t)
    out[idx] = t[idx]
    return out

torch.manual_seed(0)
g = torch.randn(4096)
k = 256                                        # 6% density
results = {}

for steps in (10, 50):
    # plain top-k: compress the raw gradient every step
    acc = sum(compress_topk(g, k) for _ in range(steps))
    plain = (acc - steps * g).norm().item()
    # error feedback: compress g + residual, keep what did not fit
    residual = torch.zeros_like(g)
    acc = torch.zeros_like(g)
    for _ in range(steps):
        to_send = g + residual
        c = compress_topk(to_send, k)
        residual = to_send - c
        acc += c
    results[steps] = (plain, (acc - steps * g).norm().item())
    print("steps %2d: plain top-k cumulative error %7.1f | error feedback %7.1f"
          % (steps, plain, results[steps][1]))

p10, p50 = results[10][0], results[50][0]
e10, e50 = results[10][1], results[50][1]
print("growing steps 10 -> 50: plain top-k error x%.1f, error feedback x%.1f"
      % (p50 / p10, e50 / e10))
```

**Output:**

```text
steps 10: plain top-k cumulative error   517.8 | error feedback   298.5
steps 50: plain top-k cumulative error  2588.9 | error feedback   420.5
growing steps 10 -> 50: plain top-k error x5.0, error feedback x1.4
```

Plain top-k's drift grows exactly linearly with steps (5x steps → x5.0 error): the same small coordinates are dropped forever, so the bias compounds. Error feedback keeps re-offering the dropped residual, holding the error sublinear (x1.4) — that is the whole point of the technique, and why shipping top-k *without* it silently corrupts training.

## Communication Backends

| Backend | Devices | Use when | Notes |
|---|---|---|---|
| NCCL | GPU | Always, for GPU training | NVLink/NVSwitch/IB aware, auto topology detection — the default |
| Gloo | CPU (GPU fallback) | CPU training, debugging, CI | `init_process_group(backend="gloo")`; lets you smoke-test distributed code without GPUs |
| MPI | HPC | Existing MPI-managed clusters | Collective semantics, scheduler integration |

`env://` reads the rank/world variables `torchrun` injects, so the two-liner below is a sketch of what runs inside a launched job — not something a bare `python` process can execute (see the Overlap section for the standalone `tcp://` equivalent that ran above):

```text
import torch.distributed as dist

# GPU training (default everywhere) - inside a torchrun job
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

### External References

- [DeepSpeed ZeRO tutorial](https://www.deepspeed.ai/tutorials/zero/) — stage 1/2/3 partitioning and the ZeRO-Offload/Infinity extension points
- [DeepSpeed getting started](https://www.deepspeed.ai/getting-started/) — installation and the first `deepspeed.initialize`
- [torch.distributed documentation](https://docs.pytorch.org/docs/2.14/distributed.html) — backend capability table, `init_process_group` init methods, collectives

---

## Next Steps

- Module 5400 complete! Next: **[5501: Optimizer Variants](../5500-advanced-optimization/5501-Optimizer-Variants.md)**
- Practical: **[LAB-006: Train a Model From Scratch](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md)**
- Assessment: **[assessment/PRACTICE.md](./assessment/PRACTICE.md)** and **[assessment/QUIZ.md](./assessment/QUIZ.md)**

**Related:** [5401](./5401-Data-Parallelism.md) — DDP/FSDP mechanics this lesson optimizes under; [5402](./5402-Model-Parallelism.md) — the splitting axes; [5403](./5403-Mixed-Precision.md) — bf16 before offload; [5501](../5500-advanced-optimization/5501-Optimizer-Variants.md) — where the 12N optimizer cost comes from; [LAB-006](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md); [EXP_5302_DISTRIBUTED](../../../../experiments/EXP_5302_DISTRIBUTED.md)

**Experiment:** [EXP_5302_DISTRIBUTED.md](../../../../experiments/EXP_5302_DISTRIBUTED.md) — nearest-relevant distributed experiment; the ring/ZeRO/overlap exercises here want multi-node hardware, which this repo's single-GPU environment approximates with the gloo world_size=1 stand-ins above
