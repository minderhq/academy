---
Document ID: 5402
Title: Model Parallelism
Phase: 5
Module: 5400
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['distributed', 'pipeline-parallelism', 'tensor-parallelism', 'training', 'gpu']
---

# 5402: Model Parallelism

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [When Data Parallelism Runs Out](#when-data-parallelism-runs-out)
- [Pipeline Parallelism](#pipeline-parallelism)
- [Tensor Parallelism](#tensor-parallelism)
- [Combining Axes: 3D Parallelism](#combining-axes-3d-parallelism)
- [Choosing a Scheme](#choosing-a-scheme)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compute the pipeline bubble fraction from stage count and micro-batch count
- Contrast 1F1B with GPipe scheduling and say what each holds in memory
- Explain Megatron's column/row-parallel pairing and why it needs only one all-reduce per layer
- Place TP, PP, and DP degrees on a physical cluster (which axis goes intra-node, which inter-node)
- Read a per-GPU memory profile and choose which parallelism axis it actually calls for

---

## Abstract

Data parallelism (5401) replicates the model; when the model itself no longer fits, model parallelism splits it. Two axes exist: **pipeline parallelism** assigns contiguous layer ranges to different GPUs, and **tensor parallelism** splits individual weight matrices inside a layer. This lesson builds both from the bubble math and the Megatron f/g communication pattern outward, then combines them with data parallelism into the 3D-parallel layouts that train frontier models, and closes with the decision table that maps a memory profile to an axis.

## When Data Parallelism Runs Out

```text
What FSDP (5401) does NOT solve

- FSDP shards params/grads/optimizer state, but activations do
  NOT shard - peak memory is bounded by activations per layer
- the FULLY-GATHERED parameter of the live FSDP unit must still
  fit on one GPU: a 100B+ single layer block exceeds any card
- communication grows with world size: at large W the all-gather
  per unit becomes the bottleneck

Model parallelism removes the constraint instead of dividing it:
the model is PHYSICALLY SPLIT, no device ever holds one layer
complete (TP) or even a contiguous half of the stack (PP).
```

```text
The two splitting axes

pipeline (PP)    split ALONG depth: GPU0 gets layers 0-7,
                 GPU1 gets 8-15, ... one activation flows
                 through stages. Coarse-grained, cheap comms
                 (point-to-point), but stages idle in a bubble

tensor (TP)      split WITHIN a layer: one 4096x4096 matmul's
                 weight is sharded 4 ways, every GPU computes
                 a slice of every layer. Fine-grained, latency-
                 sensitive all-reduces on EVERY layer
```

## Pipeline Parallelism

### The Bubble Problem

```text
Naive schedule: one batch at a time through the stages

GPU0  [ F0        ][ idle ][ idle ][ idle ]
GPU1  [       F1   ][ B1    ][ idle ][ idle ]      B0..: backward
GPU2  [            ][    F2 ][ B2  ][ idle ]
GPU3  [            ][       ][  F3  ][ B3  ]
        ^ only one GPU busy at a time - pointless

GPipe fix: split the batch into M MICRO-BATCHES and interleave

GPU0  [F0 F1 F2 F3][B0 B1 B2 B3]
GPU1  [   F0 F1 F2 F3][B0 B1 B2 B3]
GPU2  [      F0 F1 F2 F3][B0 B1 B2 B3]
GPU3  [         F0 F1 F2 F3][B0 B1 B2 B3]
                          ^^^^^^^^^^ bubble

Bubble fraction = (P - 1) / (M + P - 1)
P = stages, M = micro-batches

P=4, M=4  -> 3/7  ~ 43% idle    (bad)
P=4, M=32 -> 3/35 ~ 8.6% idle   (acceptable)
```

The bubble shrinks with more micro-batches — but each in-flight micro-batch holds activations until its backward runs, so **GPipe memory scales with M**. That trade is what the second schedule fixes.

### 1F1B: One Forward, One Backward

```text
GPipe:      all M forwards first, then all M backwards
            -> M micro-batches of activations resident per stage

1F1B        alternate 1 forward, 1 backward per stage once warm
(PipeDream-Flush)
            -> at most P activations resident per stage,
               regardless of M

Consequence: with P=8 stages, 1F1B holds 8 in-flight
micro-batches where GPipe needed M=32 for the same bubble.
Modern default everywhere (Megatron, DeepSpeed, torch.
distributed.pipelining).
```

```text
Interleaved (virtual pipeline) schedules
- each device owns v NON-CONTIGUOUS chunks (e.g. ranks
  round-robin over layer groups) instead of one block
- micro-batches hop device-to-device more often
- bubble shrinks ~v-fold; point-to-point traffic grows ~v-fold
- Megatron default for large PP degrees
```

### Modern PyTorch Surface

The old `torch.distributed.pipeline.sync.Pipe` is **removed** from PyTorch 2.x. The maintained module is `torch.distributed.pipelining` (PyTorch 2.4+):

```python
import torch
import torch.distributed as dist
from torch.distributed.pipelining import pipeline, SplitPoint, PipelineStage, Schedule1F1B

dist.init_process_group(backend="nccl")
rank, W = dist.get_rank(), dist.get_world_size()

# 32-layer transformer; 4 split points -> 4 stages
split_spec = {f"layers.{i}": SplitPoint.BEGINNING for i in (8, 16, 24)}
pipe = pipeline(model, mb_args=(torch.randn(1, 512, 4096),), split_spec=split_spec)

stage = PipelineStage(pipe, stage_id=rank, num_stages=W, device=torch.cuda.current_device())
schedule = Schedule1F1B(stage, n_microbatches=32, loss_fn=torch.nn.functional.cross_entropy)

# training step: micro-batch slicing + stage routing are handled
# by the schedule; you feed the full batch input
loss = schedule.step(batch["input"], labels=batch["labels"])
```

APIs in this module are still evolving — pin your PyTorch version and check the docs for your release before productionizing; the *schedules* (GPipe, 1F1B, interleaved-1F1B) are stable concepts regardless of surface.

```text
Stage placement rule (balance COMPUTE, not layer count)
- stage 0 also runs the embedding table
- last stage also runs the LM head + loss (and its big softmax)
- profile per-stage step time; move layers until forward times
  are within a few percent - imbalance multiplies through every
  micro-batch
```

## Tensor Parallelism

### Column and Row Parallel: The Megatron Pairing

Tensor parallelism splits one weight matrix across ranks. The design question is what the communication pattern per layer becomes — and Megatron-LM's answer is that a transformer layer needs exactly **one all-reduce forward, one backward**, if you pair the splits correctly.

```text
ColumnParallelLinear      weight [out, in] split along OUT dim
  each rank computes its slice of the OUTPUT features
  output stays SHARDED across ranks (no gather!)
  backward: grad of the input needs an ALL-REDUCE ("f" op)

RowParallelLinear         weight [out, in] split along IN dim
  input must arrive SHARDED (it does, if the previous layer
  was column-parallel)
  forward ENDS with an ALL-REDUCE of partial outputs ("g" op)
  backward: grad flows sharded, no comm
```

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class ColumnParallelLinear(nn.Module):
    """Output stays sharded - that is the point."""
    def __init__(self, in_features, out_features, world_size):
        super().__init__()
        assert out_features % world_size == 0
        self.out_local = out_features // world_size
        self.weight = nn.Parameter(torch.empty(self.out_local, in_features))
        self.bias = nn.Parameter(torch.zeros(self.out_local))
        nn.init.kaiming_uniform_(self.weight)

    def forward(self, x):                       # x: full input
        return F.linear(x, self.weight, self.bias)   # sharded out

class RowParallelLinear(nn.Module):
    """Input sharded; output all-reduced once."""
    def __init__(self, in_features, out_features, world_size, rank):
        super().__init__()
        assert in_features % world_size == 0
        self.in_local = in_features // world_size
        self.rank = rank
        self.weight = nn.Parameter(torch.empty(out_features, self.in_local))
        self.bias = nn.Parameter(torch.zeros(out_features))
        nn.init.kaiming_uniform_(self.weight)

    def forward(self, x):                       # x: sharded input
        out = F.linear(x, self.weight)
        torch.distributed.all_reduce(out)        # the "g" operator
        return out + self.bias                   # bias added ONCE, post-reduce
```

```text
The pairing that makes transformers TP-friendly

self-attention:   QKV projection = COLUMN parallel
                  (heads split cleanly across ranks - each rank
                  runs whole heads, no communication inside)
                  out-projection = ROW parallel
                  -> exactly one all-reduce per attention block

MLP:              up/gate projection = COLUMN parallel
                  down projection = ROW parallel
                  -> exactly one all-reduce per MLP block

Between the two halves of each block: NO communication at all -
activations arrive at the row-parallel layer already sharded.
Total: 2 all-reduces per layer per forward (+2 in backward).
```

### Why TP Is Bandwidth-Hungry

```text
All-reduce is latency-sensitive at transformer layer sizes
- message sizes per all-reduce are megabytes, not gigabytes
- NCCL latency dominates small messages -> TP wants NVLink
  (intra-node), typically TP degree <= 8 (one node)
- rule of thumb: TP INTRA-NODE, everything else can cross nodes

Sequence parallelism (Megatron-SP): LayerNorm and dropout regions
keep per-rank FULL activations in plain TP; splitting THOSE
regions along the sequence dim removes that duplication and
pairs naturally with the f/g pattern.
```

## Combining Axes: 3D Parallelism

Frontier training runs use all three axes at once. The placement rules fall out of each axis's communication profile:

```text
Axis   Communication           Wants                     Typical degree
TP     all-reduce per layer    NVLink, intra-node        2-8
PP     point-to-point acts     moderate, cross-node OK   4-32
DP     grad all-reduce/step    anything left over        whatever remains

Example: 64 GPUs, TP=4, PP=4
- TP=4 x PP=4 = 16 GPUs hold one full model replica ("pipeline unit")
- DP = 64 / 16 = 4 replicas process different data
- placement: ranks of one TP group on the SAME node (NVLink),
  pipeline stages ring ACROSS nodes, the 4 replicas are
  independent except for the optimizer-step all-reduce
```

```text
Mental model
- TP is the FINE knife (splits a single matmul) - expensive comms,
  use only as much as one node's NVLink affords
- PP is the COARSE knife (splits layer ranges) - cheap comms,
  scales across nodes, costs you the bubble + schedule complexity
- DP is the THROUGHPUT dial - no memory help beyond what
  FSDP/ZeRO already give, but perfect scaling for whatever
  replica count the cluster affords
- FSDP/ZeRO (5401, 5404) composes with all of the above
```

## Choosing a Scheme

Diagnose from the memory profile, not from fashion:

| Symptom in the profile | Constraint | Reach for |
|---|---|---|
| Optimizer state dominates; model fits | Memory of state | FSDP / ZeRO (5401, 5404) — not model parallelism |
| Activations dominate at long seq len | Activation memory | Activation checkpointing + sequence parallel; PP if still OOM |
| Single layer block cannot fit one GPU | Hard capacity | Tensor parallelism (intra-node) |
| Model fits a node but not a card | Capacity + scale | TP=4-8 within node |
| Model exceeds one node | Capacity at scale | PP across nodes + TP intra-node (3D) |
| Throughput too low, memory is fine | Speed | Data parallelism (more replicas) |

```text
Order of escalation (cheapest complexity first)

1. FSDP only                       (solves 90% of "7B-70B on N GPUs")
2. + activation checkpointing      (activations are the binding
                                    constraint more often than weights)
3. + PP with 1F1B                  (stack exceeds node or activations
                                    still blow up)
4. + TP intra-node                 (single layers too big; latency
                                    budget already tight)
5. only then add MoE/EP or exotic schedules
```

## Best Practices

```text
1. Profile FIRST: per-GPU memory breakdown (weights / grads /
   optimizer / activations) tells you which axis the job needs;
   adding TP because it sounds advanced costs 10-30% throughput
2. Balance pipeline stages by measured step time, not layer
   count - embedding at the head of stage 0, LM head + loss at
   the tail of the last stage
3. M (micro-batches) >= 4x P to keep the GPipe bubble sane, and
   prefer 1F1B so activation memory does not scale with M
4. Keep TP intra-node; the moment an all-reduce crosses the
   node boundary, per-layer latency tax eats the schedule
5. Version-checkpoint every pipeline stage together - a stage-
   local checkpoint cannot restore anything
6. Validate numerics against a single-GPU reference run
   (loss curves must overlap within float noise) before scaling
   the cluster further
7. Gradient checkpointing and TP interact: recomputation adds
   forward passes but REDUCES the all-reduce pressure - re-profile
   after enabling
```

---

## References

### Related ai-engineering-curriculum Documents

- [5401: Data Parallelism](5401-Data-Parallelism.md)
- [5403: Mixed Precision Training](5403-Mixed-Precision.md)
- [5404: Distributed Optimization](5404-Distributed-Optimization.md)

---

## Next Steps

- Continue with: **[5403: Mixed Precision Training](./5403-Mixed-Precision.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
