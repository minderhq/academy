---
Document ID: 2402
Title: "2402: Large-Scale Training for Language Models"
Phase: 2
Module: 2400
Last Updated: 2026-09-26
Status: Complete
Difficulty: Advanced
Estimated Time: 6 hours
Prerequisites: See module README
Related: See module README
Tags: ['training', 'pretraining', 'distributed-training', 'fsdp', 'deepspeed']
---

# 2402: Large-Scale Training for Language Models

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: Distributed Training Architectures](#part-1-distributed-training-architectures)
- [Part 2: FSDP - Fully Sharded Data Parallel](#part-2-fsdp---fully-sharded-data-parallel)
- [Part 3: DeepSpeed](#part-3-deepspeed)
- [Part 4: Multi-Node Cluster Setup](#part-4-multi-node-cluster-setup)
- [Part 5: Fault Tolerance & Resilience](#part-5-fault-tolerance--resilience)
- [Part 6: Monitoring at Scale](#part-6-monitoring-at-scale)
- [Part 7: Cost Optimization](#part-7-cost-optimization)
- [Part 8: Complete Training Script](#part-8-complete-training-script)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After completing this lesson, you will be able to:

- Compute the per-GPU memory cost of training a model with mixed-precision AdamW (the 20 bytes/param rule) and decide which parallelism strategy fits.
- Explain the ZeRO ladder — what exactly each stage shards — and its per-GPU memory effect at any fleet size.
- Configure FSDP with the right wrap policy, sharding strategy, and mixed-precision policy.
- Write a valid DeepSpeed ZeRO-3 config with CPU offload and activation checkpointing.
- Launch multi-node training with torchrun and the c10d rendezvous.
- Build resumable training: atomic checkpoint writes, rotation, and crash recovery.
- Monitor distributed runs honestly, including the memory-vs-compute utilization trap.
- Estimate wall-clock and dollar cost of a pre-training run from 6·N·D and MFU, and explain why the bill is invariant to fleet size.

## Abstract

2401 built the single-process training loop; real pre-training runs that loop across dozens to thousands of GPUs at once. This lesson is the infrastructure layer under that scale: how model state is sharded (ZeRO/FSDP), how DeepSpeed packages the same ideas, what a cluster needs beyond one node, how runs survive the crashes that are a certainty at scale, and what the whole thing costs.

**What You'll Learn:**

- Why one GPU cannot hold a 7B model's training state (140 GB) and the sharding ladder that fixes it
- FSDP (PyTorch) and DeepSpeed (framework) side by side on the same ZeRO-3 math
- Multi-node launch, cluster software requirements, and fault-tolerance patterns you can run offline
- Honest monitoring — including the `torch.cuda.utilization()` memory-vs-compute trap — and cost estimation that matches real invoices

## Part 1: Distributed Training Architectures

Every parallelism scheme is an answer to one accounting question: what does the training state actually cost? For a model trained with mixed-precision AdamW the answer is the 20-bytes rule: 4 bytes for FP32 master weights, 4 for FP32 gradients, 12 for the two Adam moments — 20 bytes per parameter before a single activation is stored. A 7B model therefore needs 140 GB of state before activations, which no single GPU holds.

The strategies differ only in *who holds what*:

- **DDP (data parallel)** — every GPU holds everything; gradients are all-reduced. Simple, fast, capped by VRAM.
- **ZeRO-1/2/3** — progressively shard optimizer states, then gradients, then parameters.
- **Tensor / pipeline parallelism** — split individual layers (Megatron) or the layer stack (GPipe); orthogonal to the data axis, treated in the references.

```python
class ParallelismStrategy:
    """Memory math for training a 7B-parameter model with mixed-precision AdamW.

    Byte budget per parameter (the "20 bytes/param" rule of thumb):
      params (FP32 master weights): 4
      grads (FP32):                 4
      Adam states (m and v):        12   (two FP32 buffers)
    Total: 20 bytes per parameter, independent of the precision the
    forward/backward pass actually runs in.
    """

    BYTES_PER_PARAM = {"params_fp32": 4, "grads_fp32": 4, "adam_states": 12}

    def training_state_gb(self, num_params: float) -> float:
        """Full (replicated) training state in GB on one GPU."""
        bytes_total = num_params * sum(self.BYTES_PER_PARAM.values())
        return bytes_total / 1e9

    def sharded_state_gb(self, num_params: float, num_gpus: int,
                         extra_buffers_gb: float = 0.0) -> float:
        """Per-GPU state with the full state sharded across num_gpus GPUs
        (ZeRO-3 / FSDP FULL_SHARD), plus a rule-of-thumb buffer allowance."""
        if num_gpus < 1:
            raise ValueError("num_gpus must be >= 1")
        return self.training_state_gb(num_params) / num_gpus + extra_buffers_gb

    def recommend(self, gpu_vram_gb: float, num_gpus: int) -> str:
        """For the default 7B model: does ZeRO-1/2/3 fit in gpu_vram_gb?"""
        full = self.training_state_gb(7_000_000_000)
        # ZeRO-1 shards optimizer states only (12/20 of the state):
        zero1 = full - (12 / 20) * full * (1 - 1 / num_gpus)
        # ZeRO-2 also shards gradients (16/20):
        zero2 = full - (16 / 20) * full * (1 - 1 / num_gpus)
        zero3 = full / num_gpus + 10.0   # +10 GB rule-of-thumb buffers
        if zero1 <= gpu_vram_gb:
            return f"DDP or ZeRO-1 fits: {zero1:.1f} GB <= {gpu_vram_gb:g} GB per GPU"
        if zero2 <= gpu_vram_gb:
            return f"ZeRO-2 fits: {zero2:.1f} GB <= {gpu_vram_gb:g} GB per GPU"
        if zero3 <= gpu_vram_gb:
            return f"FSDP / ZeRO-3 fits: {zero3:.1f} GB <= {gpu_vram_gb:g} GB per GPU"
        return ("Neither fits: see Part 3 for CPU offload and Part 2 for "
                "tensor/pipeline parallelism")


strategy = ParallelismStrategy()
full = strategy.training_state_gb(7_000_000_000)
shard8 = strategy.sharded_state_gb(7_000_000_000, num_gpus=8)
print(f"7B model, replicated training state: {full:.1f} GB")
print(f"7B model, state sharded over 8 GPUs: {shard8:.1f} GB (before buffers)")
print(strategy.recommend(gpu_vram_gb=40, num_gpus=8))   # A100 40GB class
print(strategy.recommend(gpu_vram_gb=11, num_gpus=8))   # single-consumer class
```

**Output:**

```text
7B model, replicated training state: 140.0 GB
7B model, state sharded over 8 GPUs: 17.5 GB (before buffers)
FSDP / ZeRO-3 fits: 27.5 GB <= 40 GB per GPU
Neither fits: see Part 3 for CPU offload and Part 2 for tensor/pipeline parallelism
```

```yaml
# Parallelism cheat sheet for a 7B model (mixed-precision AdamW, 20 bytes/param)
DDP:            # replicate everything on every GPU
  full_state_per_gpu: 140 GB
  scale_limit: "0.5B params on an 11 GB GPU (0.5 * 20 = 10 GB)"
  communication: "all-reduce gradients once per step"
ZeRO-1:         # shard Adam states
  memory_per_gpu_at_8x: 66.5 GB
ZeRO-2:         # shard Adam states + gradients
  memory_per_gpu_at_8x: 42 GB
ZeRO-3_FSDP:    # shard everything (+ ~10 GB comm/activation buffers)
  memory_per_gpu_at_8x: 27.5 GB
  good_for: "7B on a 40 GB A100 node; much larger models on 80 GB"
ZeRO-3_offload: # Adam states + params live on CPU
  memory_per_gpu_at_8x: 12 GB
  cost: "PCIe transfers every step - expect a 20-40% slowdown"
```

One more architectural reality: fleets do not scale perfectly. Cross-node communication, stragglers, and pipeline bubbles typically cost 5–20% of ideal throughput even in well-tuned runs (PaLM's 6144-chip run reports model FLOP utilization around 46% — roughly half of peak). The cost model in Part 7 assumes perfect scaling on purpose; this tax is exactly what real fleets spend engineering effort to shrink.

## Part 2: FSDP - Fully Sharded Data Parallel

FSDP is ZeRO-3 built into PyTorch: parameters, gradients, and optimizer states are all sharded; each layer's full parameters are all-gathered just-in-time for its forward (and again for backward), then freed. Compared with DDP you trade extra communication for fitting models many times larger than one GPU.

Three configuration decisions matter more than the rest: where to wrap (transformer-block boundaries via the auto-wrap policy), which sharding strategy (`FULL_SHARD` = ZeRO-3), and the mixed-precision policy (`bfloat16` on Ampere and later — `fp16` needs a loss scaler and risks overflow). Note that the wrap policy is passed as a `functools.partial`, because FSDP calls it internally during wrapping — a plain call is the most common FSDP beginner error.

```python
import functools
import math
import os

import torch
import torch.nn as nn
from torch.distributed.fsdp import (
    BackwardPrefetch,
    FullyShardedDataParallel as FSDP,
    MixedPrecision,
    ShardingStrategy,
)
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy


class TransformerBlock(nn.Module):
    """Minimal self-attention block so the config below is runnable."""

    def __init__(self, d_model: int = 64):
        super().__init__()
        self.attn = nn.Linear(d_model, d_model)
        self.mlp = nn.Sequential(nn.Linear(d_model, 4 * d_model), nn.GELU(),
                                 nn.Linear(4 * d_model, d_model))

    def forward(self, x):
        return x + self.mlp(self.attn(x))


def build_tiny_model(num_layers: int = 2, d_model: int = 64) -> nn.Module:
    layers = [TransformerBlock(d_model) for _ in range(num_layers)]
    return nn.Sequential(*layers, nn.Linear(d_model, d_model))


def build_fsdp_config():
    """Arguments for torch.distributed.fsdp.FullyShardedDataParallel."""
    return dict(
        auto_wrap_policy=functools.partial(
            transformer_auto_wrap_policy,
            transformer_layer_cls={TransformerBlock}),
        sharding_strategy=ShardingStrategy.FULL_SHARD,   # ZeRO-3
        mixed_precision=MixedPrecision(
            param_dtype=torch.bfloat16,
            reduce_dtype=torch.bfloat16,
            buffer_dtype=torch.bfloat16,
        ),
        backward_prefetch=BackwardPrefetch.BACKWARD_PRE,
        forward_prefetch=True,
        use_orig_params=True,   # keeps param names; state_dict stays sharding-friendly
    )


def cosine_lr(step: int, total_steps: int, base_lr: float = 3e-4,
              warmup_steps: int = 100) -> float:
    """Linear warmup, then cosine decay - the schedule real pre-training runs."""
    if step < warmup_steps:
        return base_lr * step / warmup_steps
    progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
    return base_lr * 0.5 * (1.0 + math.cos(math.pi * progress))


class FSDPTrainer:
    """Distributed-only: every method here requires a running process
    group, so it is exercised under torchrun, not in this demo."""

    def __init__(self, model, optimizer, total_steps: int):
        self.model = model
        self.optimizer = optimizer
        self.total_steps = total_steps

    def setup_fsdp(self):
        if not torch.distributed.is_initialized():
            raise RuntimeError("FSDP needs a process group: launch with "
                               "`torchrun --nproc_per_node=8 train.py`")
        return FSDP(self.model, **build_fsdp_config())

    def train_with_fsdp(self, dataloader):
        """One pass. Real pre-training keeps the loss inside the model
        (HF-style `outputs.loss`); here it is summed so the example is
        self-contained."""
        self.model.train()
        for step, batch in enumerate(dataloader):
            self.optimizer.zero_grad(set_to_none=True)
            loss = self.model(batch).sum()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

    def save_fsdp_checkpoint(self, path: str, rank: int = 0):
        """Atomic rank-0 save (os.replace is atomic even on Windows).
        Under FULL_SHARD the state is itself sharded - full-state saves
        go through torch.distributed.checkpoint."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        state = self.model.state_dict()
        if rank == 0:
            tmp = path + ".tmp"
            torch.save(state, tmp)
            os.replace(tmp, path)

    def load_fsdp_checkpoint(self, path: str):
        return torch.load(path, map_location="cpu")


cfg = build_fsdp_config()
print("FSDP strategy:", cfg["sharding_strategy"].name)
print("use_orig_params:", cfg["use_orig_params"])
tiny = build_tiny_model()
print("tiny model params:", f"{sum(p.numel() for p in tiny.parameters()):,}")
trainer = FSDPTrainer(tiny, torch.optim.SGD(tiny.parameters(), lr=3e-4),
                      total_steps=1000)
print("lr at steps 0/50/500/950/999:",
      ", ".join(f"{cosine_lr(s, 1000):.2e}" for s in [0, 50, 500, 950, 999]))
```

**Output:**

```text
FSDP strategy: FULL_SHARD
use_orig_params: True
tiny model params: 78,656
lr at steps 0/50/500/950/999: 0.00e+00, 1.50e-04, 1.76e-04, 2.28e-06, 9.14e-10
```

```yaml
# FSDP practical notes
wrap_policy: "functools.partial(transformer_auto_wrap_policy,
  transformer_layer_cls={TransformerBlock})"
  # wrap at transformer-block boundaries - finer wrapping means more,
  # smaller all-gathers (better memory, more comm overhead)
use_orig_params: true   # keeps param names; enables torch.compile and mixed-size shards
mixed_precision:
  param_dtype: bfloat16   # fp16 on pre-Ampere hardware: needs a GradScaler
  reduce_dtype: bfloat16  # all-reduce in bf16 halves communication volume
backward_prefetch: BACKWARD_PRE   # overlap the next param all-gather with backward
cpu_offload: "offload only if ZeRO-3 still does not fit - it costs PCIe bandwidth"
checkpointing: "save with torch.distributed.checkpoint - a plain sharded
  state_dict is useless on a different world size"
```

## Part 3: DeepSpeed

DeepSpeed packages the same ZeRO ideas as a training framework: you hand it a JSON config, it wraps the model, owns the optimizer, and implements the sharding and offload plan. The config below is what a real ZeRO-3 + CPU offload run looks like — note the actual schema keys: `offload_optimizer` and `offload_param` live *inside* `zero_optimization`, and activation checkpointing is its own block there (there is no top-level `gradient_checkpointing` key in DeepSpeed).

```python
import json


def create_ds_config(micro_batch: int = 8, gpus: int = 8,
                     accum_steps: int = 8) -> dict:
    """A real DeepSpeed config: ZeRO-3 + CPU optimizer offload + activation
    checkpointing. Keys follow DeepSpeed's own schema."""
    return {
        "train_batch_size": micro_batch * gpus * accum_steps,
        "train_micro_batch_size_per_gpu": micro_batch,
        "gradient_accumulation_steps": accum_steps,
        "bf16": {"enabled": True},   # pre-Volta GPUs need "fp16" instead
        "zero_optimization": {
            "stage": 3,
            "offload_optimizer": {"device": "cpu", "pin_memory": True},
            "offload_param": {"device": "cpu", "pin_memory": True},
            "activation_checkpointing": {
                "partition_activations": True,
                "contiguous_memory_optimization": True,
                "number_checkpoints": None,
                "checkpoint_interval": 1,
            },
            "overlap_comm": True,
            "reduce_scatter": True,
        },
        "optimizer": {
            "type": "AdamW",
            "params": {"lr": 3e-4, "betas": [0.9, 0.95], "weight_decay": 0.1},
        },
    }


class DeepSpeedTrainer:
    """Definition-only until deepspeed is installed; the config above is
    runnable offline."""

    def batch_math(self, micro_batch: int, gpus: int, accum_steps: int) -> int:
        """Global batch = micro-batch per GPU * world size * accumulation."""
        return micro_batch * gpus * accum_steps

    def write_config(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(create_ds_config(), f, indent=2)   # DeepSpeed reads JSON, not YAML

    def train_with_deepspeed(self, model, dataloader):
        # lazy import: the module is only needed when actually launching
        import deepspeed
        engine, _, _, _ = deepspeed.initialize(
            model=model, config=create_ds_config())
        for batch in dataloader:
            loss = engine(batch).sum()
            engine.backward(loss)
            engine.step()


cfg = create_ds_config()
print("global batch:", cfg["train_batch_size"])
print("zero stage:", cfg["zero_optimization"]["stage"])
print("offload devices:",
      cfg["zero_optimization"]["offload_optimizer"]["device"], "+",
      cfg["zero_optimization"]["offload_param"]["device"])
print("json serializes:", bool(json.dumps(cfg)))
```

**Output:**

```text
global batch: 512
zero stage: 3
offload devices: cpu + cpu
json serializes: True
```

The batch line is worth internalizing: a global batch of 512 at 8 GPUs means each GPU ingests micro-batches of 8 and accumulates 8 of them between optimizer steps. Gradient accumulation is how memory-constrained clusters reach the large global batches pre-training wants.

The ZeRO stage ladder itself deserves a runnable form, because it is the vocabulary of every scaling conversation:

```python
class ZeROStages:
    """Per-GPU training memory under each ZeRO stage.

    Accounting follows the ZeRO paper (Rajbhandari et al., 2020) for
    mixed-precision AdamW, 20 bytes per parameter:
      stage 0 (replicated): 20 B/param on every GPU
      stage 1: optimizer states sharded -> full - (12/20)*full*(1-1/n)
      stage 2: + gradients sharded      -> full - (16/20)*full*(1-1/n)
      stage 3: + parameters sharded     -> full/n + comm/activation buffers
      3+offload: params+grads on GPU, Adam states and params live on CPU
    The buffer allowances are stated rule-of-thumb constants, not laws.
    """

    BYTES_PER_PARAM = 4 + 4 + 12   # params, grads, Adam m+v (all FP32)
    BUFFERS_GB = {3: 10.0, "3+offload": 5.0}

    def __init__(self, model_params: float = 7e9, num_gpus: int = 8):
        self.model_params = model_params
        self.num_gpus = num_gpus
        self.full = model_params * self.BYTES_PER_PARAM / 1e9

    def stage_gb(self, stage) -> float:
        full, n = self.full, self.num_gpus
        if stage == 0:
            return full
        if stage == 1:
            return full - (12 / 20) * full * (1 - 1 / n)
        if stage == 2:
            return full - (16 / 20) * full * (1 - 1 / n)
        if stage == 3:
            return full / n + self.BUFFERS_GB[3]
        if stage == "3+offload":
            return (full - 12 / 20 * full) / n + self.BUFFERS_GB["3+offload"]
        raise ValueError(f"unknown stage: {stage!r}")

    def print_table(self) -> None:
        stages = [0, 1, 2, 3, "3+offload"]
        labels = {0: "ZeRO-0 (replicated)", 1: "ZeRO-1", 2: "ZeRO-2",
                  3: "ZeRO-3 (FSDP FULL_SHARD)", "3+offload": "ZeRO-3 + CPU offload"}
        base = self.stage_gb(0)
        print(f"{'stage':<26}{'GB/GPU':>9}{'saved':>8}")
        for s in stages:
            gb = self.stage_gb(s)
            print(f"{labels[s]:<26}{gb:>9.1f}{100 * (1 - gb / base):>7.1f}%")


ZeROStages(model_params=7e9, num_gpus=8).print_table()
```

**Output:**

```text
stage                        GB/GPU   saved
ZeRO-0 (replicated)           140.0    0.0%
ZeRO-1                         66.5   52.5%
ZeRO-2                         42.0   70.0%
ZeRO-3 (FSDP FULL_SHARD)       27.5   80.4%
ZeRO-3 + CPU offload           12.0   91.4%
```

Reading the table: the big jumps come from sharding the 12 bytes of Adam states (ZeRO-1) and the 4 bytes of gradients (ZeRO-2); the last, most expensive step shards the 4 bytes of parameters themselves. Every stage after ZeRO-0 adds communication or PCIe traffic — memory saved is time spent.

## Part 4: Multi-Node Cluster Setup

Between one node and many sits a fixed checklist: identical software everywhere, a fast interconnect, shared checkpoint storage, and a launcher that agrees on world size. torchrun's c10d rendezvous lets nodes discover each other through a single endpoint instead of a rigid hostfile, which is what makes elastic restarts possible.

```python
class ClusterSetup:
    """What you need before torchrun can talk across machines."""

    def network_topology(self) -> dict:
        return {
            "nodes": 4,
            "gpus_per_node": 8,
            "interconnect_in_node": "NVLink / NVSwitch (600+ GB/s)",
            "interconnect_between_nodes": "InfiniBand HDR / RoCE (200+ Gb/s per GPU)",
            "rule_of_thumb": "keep world size a multiple of gpus per node",
        }

    def software_stack(self) -> dict:
        return {
            "driver": "matching CUDA driver on every node",
            "nccl": "2.18+ (the collective library PyTorch uses)",
            "pytorch": "same version + same CUDA build on all nodes",
            "storage": "shared filesystem (NFS/Lustre) or object store for checkpoints",
            "scheduler": "SLURM / Kubernetes for launch + retry",
        }

    def launch_multi_node_training(self, num_nodes: int = 4,
                                   gpus_per_node: int = 8) -> str:
        """torchrun launch line for node 0 of N (other nodes pass their
        own --node_rank). RDZV_ENDPOINT is the first node's host:port."""
        return (
            f"torchrun --nnodes={num_nodes} --nproc_per_node={gpus_per_node} "
            f"--rdzv_backend=c10d --rdzv_endpoint=$RDZV_ENDPOINT "
            f"--node_rank=0 train.py"
        )


setup = ClusterSetup()
topo = setup.network_topology()
print("minimum cluster:", topo["nodes"], "nodes x", topo["gpus_per_node"], "GPUs")
print("NCCL requirement:", setup.software_stack()["nccl"])
cmd = setup.launch_multi_node_training()
print("launch (node 0):", cmd)
```

**Output:**

```text
minimum cluster: 4 nodes x 8 GPUs
NCCL requirement: 2.18+ (the collective library PyTorch uses)
launch (node 0): torchrun --nnodes=4 --nproc_per_node=8 --rdzv_backend=c10d --rdzv_endpoint=$RDZV_ENDPOINT --node_rank=0 train.py
```

```yaml
# shared training cluster config (4 nodes x 8 GPUs)
topology:
  nodes: 4
  gpus_per_node: 8
  intra_node: "NVLink / NVSwitch"
  inter_node: "InfiniBand HDR (200 Gb/s per GPU)"
software:
  cuda_driver: "same version on every node"
  nccl: ">= 2.18"
  pytorch: "identical wheel on every node"
  storage: "Lustre/NFS mount for checkpoints, or object store with async upload"
launch:
  command: "torchrun --nnodes=4 --nproc_per_node=8 --rdzv_backend=c10d --rdzv_endpoint=$RDZV_ENDPOINT --node_rank=$NODE_RANK train.py"
  env:
    NCCL_DEBUG: INFO                       # first run: watch for fallback to Socket
    NCCL_IB_DISABLE: "0"                   # keep InfiniBand enabled
    TORCH_NCCL_ASYNC_ERROR_HANDLING: "1"   # a hang becomes an error, not a deadlock
```

The `NCCL_DEBUG=INFO` line is the one that saves days: if the first multi-node run is mysteriously slow, NCCL almost always fell back from InfiniBand to Socket (TCP) on some pair of nodes, and the INFO log says so explicitly.

## Part 5: Fault Tolerance & Resilience

At scale, crashes are scheduled events: long distributed runs accumulate hardware failures — a GPU drops out, a NIC flaps, a node reboots — and the training job you actually run is one that can die at any step and resume. Two implementation details separate a real checkpoint system from a toy: writes must be atomic (write to `.tmp`, then `os.replace`, which is atomic even on Windows), and old checkpoints must be rotated, or the shared filesystem fills up mid-run.

```python
import os
import shutil
import sys
import tempfile
import threading
import time

import torch
import torch.nn as nn


class ResilientTrainer:
    """Checkpointing + crash recovery + optional watchdog hooks.

    Production hooks (signal handlers, background checkpoint thread) are
    OPT-IN flags, never implicit: a trainer that forks threads in its
    constructor is a trainer that surprises everyone at 3 a.m.
    """

    def __init__(self, model, optimizer, scheduler=None, save_dir="checkpoints",
                 checkpoint_every=1000, keep_last_n=5,
                 enable_signals=False, enable_background_checkpointing=False,
                 background_interval_sec=300):
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.save_dir = save_dir
        self.checkpoint_every = checkpoint_every
        self.keep_last_n = keep_last_n
        self.current_step = 0
        if enable_signals:
            import signal
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        self._stop_background = threading.Event()
        if enable_background_checkpointing:
            t = threading.Thread(target=self._periodic_checkpoint,
                                 args=(background_interval_sec,), daemon=True)
            t.start()

    # -- production hooks (opt-in) -------------------------------------
    def _signal_handler(self, signum, frame):
        print(f"signal {signum}: saving checkpoint, exiting")
        self.save_checkpoint()
        sys.exit(1)

    def _periodic_checkpoint(self, interval_sec: int) -> None:
        while not self._stop_background.wait(interval_sec):
            self.save_checkpoint()

    # -- checkpointing --------------------------------------------------
    def save_checkpoint(self) -> str:
        os.makedirs(self.save_dir, exist_ok=True)
        path = os.path.join(self.save_dir, f"step_{self.current_step}.pt")
        tmp = path + ".tmp"
        torch.save({"step": self.current_step,
                    "model": self.model.state_dict(),
                    "optimizer": self.optimizer.state_dict()}, tmp)
        os.replace(tmp, path)          # atomic rename, even on Windows
        self._rotate()
        return path

    def _rotate(self) -> None:
        steps = sorted(
            int(f.split("_")[1].split(".")[0])
            for f in os.listdir(self.save_dir)
            if f.startswith("step_") and f.endswith(".pt"))
        for s in steps[:-self.keep_last_n]:
            os.remove(os.path.join(self.save_dir, f"step_{s}.pt"))
            print(f"Removed old checkpoint: step_{s}.pt")

    def find_latest_checkpoint(self):
        if not os.path.isdir(self.save_dir):
            return None
        steps = sorted(
            int(f.split("_")[1].split(".")[0])
            for f in os.listdir(self.save_dir)
            if f.startswith("step_") and f.endswith(".pt"))
        if not steps:
            return None
        return os.path.join(self.save_dir, f"step_{steps[-1]}.pt")

    def load_checkpoint(self, path: str) -> int:
        ckpt = torch.load(path, map_location="cpu")
        self.model.load_state_dict(ckpt["model"])
        self.optimizer.load_state_dict(ckpt["optimizer"])
        self.current_step = ckpt["step"]
        return ckpt["step"]

    # -- training ---------------------------------------------------------
    def train_step(self, batch) -> float:
        self.optimizer.zero_grad(set_to_none=True)
        loss = self.model(batch).sum()
        loss.backward()
        self.optimizer.step()
        if self.scheduler is not None:
            self.scheduler.step()
        self.current_step += 1
        return loss.item()

    def train(self, batches, total_steps: int) -> None:
        """Resume from the latest checkpoint, then run to total_steps."""
        latest = self.find_latest_checkpoint()
        if latest:
            step = self.load_checkpoint(latest)
            print(f"Loaded checkpoint {os.path.basename(latest)}, "
                  f"resuming at step: {step}")
        else:
            print("No checkpoint found, starting from scratch")
        it = iter(batches)
        while self.current_step < total_steps:
            try:
                batch = next(it)
            except StopIteration:
                it = iter(batches)
                batch = next(it)
            self.train_step(batch)
            if self.current_step % self.checkpoint_every == 0:
                print(f"Saved checkpoint: {os.path.basename(self.save_checkpoint())}")


tmpdir = tempfile.mkdtemp(prefix="omega_ckpts_")


def fresh_trainer():
    torch.manual_seed(0)
    model = nn.Linear(8, 8)
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    return ResilientTrainer(model, opt, save_dir=tmpdir, checkpoint_every=25)


trainer = fresh_trainer()
data = [torch.randn(4, 8) for _ in range(40)]
trainer.train(data, total_steps=50)          # checkpoints at 25 and 50

trainer.current_step = 30                    # simulate an out-of-band save
manual = trainer.save_checkpoint()
print("saved:", os.path.basename(manual))
print("checkpoint files:", sorted(os.listdir(tmpdir)))

trainer = fresh_trainer()                    # fresh process, fresh objects
step = trainer.load_checkpoint(trainer.find_latest_checkpoint())
print(f"Loaded checkpoint from step {step}; current_step: {trainer.current_step}")

for i in range(1, 8):                        # force rotation: 8 files -> keep 5
    trainer.current_step = 30 + i
    trainer.save_checkpoint()
print("final files:", len(os.listdir(tmpdir)))

shutil.rmtree(tmpdir, ignore_errors=True)
```

**Output:**

```text
No checkpoint found, starting from scratch
Saved checkpoint: step_25.pt
Saved checkpoint: step_50.pt
saved: step_30.pt
checkpoint files: ['step_25.pt', 'step_30.pt', 'step_50.pt']
Loaded checkpoint from step 50; current_step: 50
Removed old checkpoint: step_25.pt
Removed old checkpoint: step_30.pt
Removed old checkpoint: step_31.pt
Removed old checkpoint: step_32.pt
Removed old checkpoint: step_33.pt
final files: 5
```

Read the demo as a crash timeline: train to step 50 (auto-checkpoints at 25 and 50), an out-of-band save lands at step 30, then the "process dies" — a fresh trainer reconstructs everything from `find_latest_checkpoint` and resumes at step 50, the latest. The forced rotation at the end shows the retention policy working: eight accumulated checkpoints, `keep_last_n=5`, exactly five files survive.

## Part 6: Monitoring at Scale

Distributed runs fail in ways single-process ones do not: one rank OOMs while the others wait, token throughput silently halves after a network flap, a straggler dominates step time. A monitor cannot fix these, but it must see them — and it must not lie to you. The classic lie: `torch.cuda.utilization()` returns *memory-bandwidth* utilization percent, not the "is my GPU busy computing" number people assume; true compute utilization comes from pynvml's `util.gpu` counter. The monitor below keeps vendors out of the module — it accepts any logging sink you hand it, so TensorBoard, wandb, or your own endpoint are a constructor argument, not an import.

```python
import time

import torch


class DistributedMonitor:
    """Lightweight training monitor. `logger` is any callable(dict) -
    TensorBoard, wandb, your own sink. No vendor import at module level:
    the sink is injected, the monitor stays dependency-free."""

    def __init__(self, logger=None):
        self.logger = logger
        self.history = []
        self.start_time = time.time()
        self.avg_tokens_per_sample = 0.0

    def set_avg_tokens(self, avg_tokens_per_sample: float) -> None:
        """Feed the dataset-side number that log_data_metrics needs."""
        self.avg_tokens_per_sample = avg_tokens_per_sample

    def _log(self, metrics: dict) -> None:
        self.history.append(metrics)
        if self.logger is not None:
            self.logger(metrics)

    def log_training_metrics(self, loss: float, grad_norm: float,
                             lr: float, step: int) -> None:
        self._log({"train/loss": loss, "train/grad_norm": grad_norm,
                   "train/lr": lr, "train/step": step})
        print(f"logged: {{'train/loss': {loss}, 'train/step': {step}}}")

    def log_data_metrics(self, dataset_size: int, step: int) -> None:
        samples_seen = step * 512   # demo: global batch 512
        self._log({"data/samples_seen": samples_seen,
                   "data/epoch": samples_seen / max(1, dataset_size)})
        tokens_per_sec = samples_seen * self.avg_tokens_per_sample / (
            time.time() - self.start_time)
        print(f"samples_seen: {samples_seen}, "
              f"tokens/sec measurable: {tokens_per_sec > 0}")

    def log_gpu_metrics(self) -> None:
        if not torch.cuda.is_available():
            print("CUDA not available - skipping GPU metrics")
            return
        for gpu_id in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(gpu_id)
            used = torch.cuda.memory_allocated(gpu_id)
            mem_util_pct = 100 * used / props.total_memory
            # torch.cuda.utilization(gpu) reports MEMORY utilization percent;
            # true COMPUTE utilization needs pynvml's util.gpu counter.
            print(f"gpu {gpu_id}: {used / 1e9:.2f} GB allocated of "
                  f"{props.total_memory / 1e9:.1f} GB, mem-util {mem_util_pct:.1f}%")

    def log_communication_metrics(self):
        raise NotImplementedError(
            "per-rank allreduce timings need torch.profiler (CPU + CUDA "
            "activities) - see 5404: Distributed Optimization")


monitor = DistributedMonitor()
monitor.log_training_metrics(loss=2.71, grad_norm=1.19, lr=3e-4, step=100)
monitor.set_avg_tokens(avg_tokens_per_sample=2048)
monitor.log_data_metrics(dataset_size=10_000, step=100)
if torch.cuda.is_available():
    _hold = torch.zeros(25_000_000, device="cuda")   # 100 MB, keeps the metric non-trivial
monitor.log_gpu_metrics()
print("history entries:", len(monitor.history))
```

**Output:**

```text
logged: {'train/loss': 2.71, 'train/step': 100}
samples_seen: 51200, tokens/sec measurable: True
gpu 0: 0.10 GB allocated of 17.1 GB, mem-util 0.6%
history entries: 2
```

(The GPU line is from the machine this lesson was verified on — a 17.1 GB consumer GPU; your totals will differ, the format will not.)

## Part 7: Cost Optimization

Cost estimation is arithmetic, not folklore: 6·N·D FLOPs for N parameters over D tokens, divided by achieved FLOP/s, divided by price. At MFU 0.5 — what well-tuned runs achieve — a 7B model over 1T tokens takes ~389.5 A100-days of wall clock on 8 GPUs, exactly the number 2401 derived. This lesson generalizes it per fleet size and GPU type, and prices it from on-demand instance list prices.

```python
class TrainingCostCalculator:
    """Wall-clock and dollar cost of pre-training, from first principles.

    FLOPs = 6 * N * D   (N params, D training tokens)
    time  = FLOPs / (peak TFLOPS * MFU), per GPU, then / fleet size
    cost  = GPU-hours * $/GPU-hour
    """

    GPU_PEAK_TFLOPS = {   # dense BF16 peak (no sparsity tricks)
        "A100": 312.0,
        "H100": 990.0,
        "V100": 125.0,
        "RTX 4090": 83.0,
    }
    CLOUD_PRICING = {     # on-demand Linux list prices, 2024-2026 ballpark
        ("aws", "V100"): (24.48, 8),    # p3.16xlarge
        ("aws", "A100"): (32.77, 8),    # p4d.24xlarge
        ("aws", "H100"): (98.32, 8),    # p5.48xlarge
        ("gcp", "A100"): (35.04, 8),    # a2-highgpu-8g
    }

    def __init__(self, mfu: float = 0.5):
        self.mfu = mfu   # 50% is what well-tuned real runs achieve

    def per_gpu_hourly(self, gpu_type: str, provider: str = "aws") -> float:
        instance_hourly, gpus = self.CLOUD_PRICING[(provider, gpu_type)]
        return instance_hourly / gpus

    def calculate_cost(self, model_params: float, training_tokens: float,
                       gpu_type: str = "A100", num_gpus: int = 8) -> dict:
        total_flops = 6 * model_params * training_tokens
        peak = self.GPU_PEAK_TFLOPS[gpu_type] * 1e12
        gpu_seconds = total_flops / (peak * self.mfu)
        hours = gpu_seconds / num_gpus / 3600
        hourly = self.per_gpu_hourly(gpu_type)
        # NOTE: assumes perfect scaling; real fleets pay a 5-20% tax that
        # this teaching calculation deliberately omits.
        return {
            "training_days": hours / 24,
            "hourly_cost_per_gpu": hourly,
            "total_cost_usd": hours * hourly * num_gpus,
            "cost_per_million_tokens":
                hours * hourly * num_gpus / (training_tokens / 1e6),
        }

    def compare_options(self, model_params: float, training_tokens: float) -> None:
        print(f"{'fleet':<14}{'days':>8}{'total cost':>14}")
        for fleet in [(8, "A100"), (16, "A100"), (32, "A100"),
                      (8, "H100"), (16, "H100")]:
            c = self.calculate_cost(model_params, training_tokens,
                                    gpu_type=fleet[1], num_gpus=fleet[0])
            print(f"{fleet[0]:>3} x {fleet[1]:<6}{c['training_days']:>8.1f}"
                  f"{c['total_cost_usd']:>14,.0f}")
        a8 = self.calculate_cost(model_params, training_tokens, "A100", 8)
        a16 = self.calculate_cost(model_params, training_tokens, "A100", 16)
        print(f"detail: 7B x 1T tokens on 8 x A100 = "
              f"{a8['training_days']:.1f} days, ${a8['total_cost_usd']:,.0f}")
        print(f"bill invariant to fleet size: "
              f"{abs(a8['total_cost_usd'] - a16['total_cost_usd']) < 1e-6}")


TrainingCostCalculator().compare_options(model_params=7e9, training_tokens=1e12)
```

**Output:**

```text
fleet             days    total cost
  8 x A100     389.5       306,343
 16 x A100     194.8       306,343
 32 x A100      97.4       306,343
  8 x H100     122.8       289,663
 16 x H100      61.4       289,663
detail: 7B x 1T tokens on 8 x A100 = 389.5 days, $306,343
bill invariant to fleet size: True
```

The $306,343 differs from 2401's $224,359 for the same 7B × 1T run because the price assumptions differ, not the math: 2401 used a bare $3/GPU-hour (typical of discounted or marketplace rates), while `p4d.24xlarge` on-demand list price works out to $4.10/GPU-hour once the instance's CPUs, RAM, and networking are amortized onto its 8 GPUs. Spot and preemptible capacity on the same instances routinely discounts 60–90%, which is how published "we trained it for $X" numbers get so small. What stays invariant: the bill does not depend on fleet size — twice the GPUs, half the days, same dollars.

## Part 8: Complete Training Script

The scaffold below is the honest shape of a real FSDP training entry point: distributed setup, model wrapping, AdamW with pre-training hyperparameters, and rank-0-only logging. The two `NotImplementedError` hooks are where your model and data pipeline go — 2401 Part 10 builds both, and LAB-006 wires them end to end. Launch it with `torchrun --nproc_per_node=8 train_fsdp.py`, never with plain `python`.

```python
# Launch: torchrun --nproc_per_node=8 train_fsdp.py
import functools
import os

import torch
import torch.distributed as dist
from torch.distributed.fsdp import (
    FullyShardedDataParallel as FSDP,
    MixedPrecision,
    ShardingStrategy,
)
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy


class TransformerBlock(torch.nn.Module):
    """Placeholder - replace with your model's real transformer block."""

    def __init__(self, d_model=512):
        super().__init__()
        self.attn = torch.nn.Linear(d_model, d_model)
        self.mlp = torch.nn.Sequential(
            torch.nn.Linear(d_model, 4 * d_model), torch.nn.GELU(),
            torch.nn.Linear(4 * d_model, d_model))

    def forward(self, x):
        return x + self.mlp(self.attn(x))


def setup_distributed():
    dist.init_process_group(backend="nccl")
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    return local_rank, dist.get_world_size()


def create_transformer_model():
    raise NotImplementedError(
        "your real model here - see 2401 Part 10 and LAB-006")


def get_dataloader(batch_size: int, rank: int, world_size: int):
    # Real pre-training uses a DistributedSampler so each rank sees a
    # disjoint shard; call sampler.set_epoch(epoch) every epoch.
    raise NotImplementedError(
        "your data pipeline here - see 2401 Part 10 and LAB-006")


def main(num_epochs: int = 3):
    local_rank, world_size = setup_distributed()
    model = create_transformer_model().to(local_rank)

    mp_policy = MixedPrecision(param_dtype=torch.bfloat16,
                               reduce_dtype=torch.bfloat16,
                               buffer_dtype=torch.bfloat16)
    model = FSDP(model,
                 auto_wrap_policy=functools.partial(
                     transformer_auto_wrap_policy,
                     transformer_layer_cls={TransformerBlock}),
                 sharding_strategy=ShardingStrategy.FULL_SHARD,
                 mixed_precision=mp_policy,
                 use_orig_params=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4,
                                  betas=(0.9, 0.95), weight_decay=0.1)

    for epoch in range(num_epochs):
        for step, batch in enumerate(get_dataloader(batch_size=8,
                                                    rank=local_rank,
                                                    world_size=world_size)):
            optimizer.zero_grad(set_to_none=True)
            loss = model(batch).sum()
            loss.backward()
            model.clip_grad_norm_(max_norm=1.0)
            optimizer.step()
            if local_rank == 0 and step % 100 == 0:
                print(f"epoch {epoch} step {step}: loss {loss.item():.3f}")


if __name__ == "__main__":
    main()
```

Nothing prints here by design — this file is a scaffold meant to be launched under `torchrun`, which requires an initialized process group and the real model/data hooks filled in.

## Summary

Scale changes the physics of training less than it changes the plumbing: it is the same single-GPU loop from 2401, replicated across ranks, with state sharded until it fits and checkpoints treated as load-bearing infrastructure. Master the 20-bytes accounting and every parallelism conversation becomes arithmetic; master atomic checkpoints and a crashed 300-GPU run becomes an inconvenience instead of a rewrite.

```yaml
# 2402 in six lines
memory_rule: "mixed-precision AdamW costs 20 bytes/param before activations"
ddp_limit: "< 0.5B params per 11 GB GPU; beyond that, shard"
sharding_ladder: "ZeRO-1 (Adam states) -> ZeRO-2 (+grads) -> ZeRO-3 (+params) -> offload (CPU)"
single_gpu_reality: "7B trains on ONE 24 GB GPU with ZeRO-3 + CPU offload"
cost_physics: "6*N*D FLOPs; at MFU 0.5 a 7B x 1T run is ~390 A100-days, ~$306k on-demand"
resilience: "atomic writes + rotation + resumability is not optional at scale"
```

## References

### Related Documents

- [2400: LLM Pretraining](./README.md) — module overview, schedule, and assessment links
- [2400: LLM Pretraining - Prerequisites](./PREREQUISITES.md) — what to know before starting this module
- [2401: Pre-training Fundamentals](./2401-Pre-training-Fundamentals.md) — the single-process loop this lesson scales out
- [2403: Evaluation Frameworks for Language Models](./2403-Evaluation-Frameworks.md) — what to run when the long training finally converges
- [5404: Distributed Optimization](../../phase5-finetuning/5400-distributed-training/5404-Distributed-Optimization.md) — the fine-tuning-side view of the same infrastructure
- [LAB-006: Train a Small Language Model from Scratch](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md) — the hands-on version of Part 8

### External References

- [ZeRO: Memory Optimizations Toward Training Trillion Parameter Models](https://arxiv.org/abs/1910.02054) — the paper behind the stage ladder (Rajbhandari et al., 2020)
- [Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism](https://arxiv.org/abs/1909.08053) — intra-layer (tensor) parallelism, beyond this lesson's data-axis focus
- [GPipe: Efficient Training of Giant Neural Networks using Pipeline Parallelism](https://arxiv.org/abs/1811.06965) — the origins of pipeline parallelism
- [PaLM: Scaling Language Modeling with Pathways](https://arxiv.org/abs/2204.02311) — what a real 6144-chip run reports about MFU, failures, and restarts
- [Getting started with Fully Sharded Data Parallel (PyTorch tutorial)](https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html) — the official walkthrough of the APIs used in Part 2
- [Efficient training on multiple GPUs (Transformers docs)](https://huggingface.co/docs/transformers/perf_train_gpu_many) — a practical parallelism decision guide

## Next Steps

**Next Lesson:** [2403: Evaluation Frameworks for Language Models](./2403-Evaluation-Frameworks.md) — the training run converged; now measure whether it is actually good.

**Practical:** [LAB-006: Train a Small Language Model from Scratch](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md) — run the full pipeline end to end on hardware you own.

**Assessment:** [2400: Pretraining Fundamentals - Quiz](./assessment/QUIZ.md) and [2400: Pre-training - Practice](./assessment/PRACTICE.md).

**Related:** [5404: Distributed Optimization](../../phase5-finetuning/5400-distributed-training/5404-Distributed-Optimization.md) — the same sharding and offload ideas applied to fine-tuning.

**Experiment:** [EXP_5302: Distributed Training Experiment](../../../../experiments/EXP_5302_DISTRIBUTED.md) — the nearest-relevant hands-on lab for distributed runs (no EXP_24xx exists yet).
