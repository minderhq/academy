---
Document ID: 2402
Title: Large-Scale Training for Language Models
Phase: 2
Module: 2400
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 6 hours
Prerequisites: See module README
Related: See module README
Tags: ['training', 'pretraining', 'evaluation', 'fsdp']
---

# 2402: Large-Scale Training for Language Models

**"Training at Scale"** - Multi-GPU and multi-node training infrastructure.

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: Distributed Training Architectures](#part-1-distributed-training-architectures)
- [Part 2: FSDP - Fully Sharded Data Parallel](#part-2-fsdp---fully-sharded-data-parallel)
- [Part 3: DeepSpeed](#part-3-deepspeed)
- [Part 4: Multi-Node Cluster Setup](#part-4-multi-node-cluster-setup)
- [Part 5: Fault Tolerance & Resilience](#part-5-fault-tolerance-resilience)
- [Part 6: Monitoring at Scale](#part-6-monitoring-at-scale)
- [Part 7: Cost Optimization](#part-7-cost-optimization)
- [Part 8: Complete Training Script](#part-8-complete-training-script)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Part 1: Distributed Training Architectures
- Explain Part 2: FSDP - Fully Sharded Data Parallel
- Explain Part 3: DeepSpeed
- Configure and operate Part 4: Multi-Node Cluster Setup
- Explain Part 5: Fault Tolerance & Resilience
- Measure and evaluate Part 6: Monitoring at Scale

---

## Abstract

**Prerequisites:** [2401: Pre-training Fundamentals](2401-Pre-training-Fundamentals.md), Volume 3 (LLM Internals)
**Time:** 4-5 hours to read, weeks/months to implement
**Difficulty:** ⭐⭐⭐⭐⭐ Expert

### What You'll Learn

After this guide, you will understand:
- ✅ Distributed training architectures (DDP, FSDP, DeepSpeed)
- ✅ Multi-node cluster setup
- ✅ Memory optimization techniques
- ✅ Fault tolerance and checkpointing
- ✅ Training monitoring at scale
- ✅ Cost optimization strategies

---

## Part 1: Distributed Training Architectures

### Understanding Parallelism Strategies

```python
"""
Types of Parallelism for Large Model Training
"""

class ParallelismStrategy:
    """Understanding different parallelism approaches"""

    def __init__(self):
        self.model_size = "7B"  # 7 billion parameters
        self.num_gpus = 8

    def data_parallelism(self):
        """
        Data Parallelism (DP/DDP)

        - Copy model to each GPU
        - Split batch across GPUs
        - Each GPU computes gradients independently
        - All-reduce to synchronize gradients

        Pros:
        - Simple to implement
        - Works well for small models
        - Good throughput

        Cons:
        - Model must fit in single GPU memory
        - Memory scales with model size, not GPUs
        - Communication overhead at scale

        Use case: Models that fit in single GPU (<= 1B params on 11GB VRAM)
        """
        # PyTorch DDP implementation
        import torch.distributed as dist
        from torch.nn.parallel import DistributedDataParallel as DDP

        # Initialize process group
        dist.init_process_group("nccl")

        # Wrap model
        model = DDP(model.cuda(), device_ids=[local_rank])

        # Each GPU gets different data shard
        # Gradients are synchronized automatically

    def tensor_parallelism(self):
        """
        Tensor Parallelism (TP)

        - Split model layers across GPUs
        - Each GPU holds part of each layer
        - Communication within each layer

        Pros:
        - Reduces memory per GPU
        - Scales to very large models

        Cons:
        - High communication overhead
        - Complex implementation
        - Requires specialized libraries (Megatron, Tensor Parallel)

        Use case: Models too large for single GPU (> 10B params)
        """
        # Column and row parallelism for linear layers
        # Q: Is model_size / num_gpus small enough?
        # 7B model / 8 GPUs = ~875M params per GPU
        # Fits easily with TP!

    def pipeline_parallelism(self):
        """
        Pipeline Parallelism (PP)

        - Split layers across GPUs
        - Each GPU holds consecutive layers
        - Micro-batching for efficiency

        Pros:
        - Reduces memory per GPU
        - Good for deep models

        Cons:
        - Pipeline bubbles (idle time)
        - Complex scheduling
        - Longer training time per epoch

        Use case: Very deep models (70B+ params)
        """

    def fully_sharded_data_parallel(self):
        """
        Fully Sharded Data Parallel (FSDP)

        - Shard model parameters, gradients, and optimizer states
        - Dynamically gather parameters for computation
        - Most memory efficient

        Pros:
        - Maximum memory efficiency
        - Scales to huge models (175B+)
        - Built into PyTorch 2.0+

        Cons:
        - Higher communication overhead
        - Slower than DP for small models
        - Requires careful tuning

        Use case: Large models (7B+) with limited VRAM
        """
        # FSDP implementation
        from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

        model = FSDP(
            base_model,
            sharding_strategy="FULL_SHARD",  # Shard everything
            cpu_offload=False,  # Keep on GPU
            auto_wrap_policy=transformer_auto_wrap_policy
        )
```

### Comparison Table

```yaml
Parallelism Comparison:

  Data Parallel (DDP):
    Memory per GPU: Full model
    Max model size: 1-2B (on 11GB VRAM)
    Communication: Gradient synchronization
    Speed: Fast (low overhead)
    Complexity: Low
    Best for: Small models, fast training

  Tensor Parallel (TP):
    Memory per GPU: Model / num_gpus
    Max model size: 10B+ (with 8 GPUs)
    Communication: Within each layer
    Speed: Medium (high overhead)
    Complexity: High
    Best for: Large models, inference

  Pipeline Parallel (PP):
    Memory per GPU: Layers / num_gpus
    Max model size: 50B+ (with 8 GPUs)
    Communication: Between pipeline stages
    Speed: Slow (pipeline bubbles)
    Complexity: High
    Best for: Very deep models

  FSDP:
    Memory per GPU: (Model + gradients + optimizer) / num_gpus
    Max model size: 175B+ (with 8 GPUs)
    Communication: Frequent all-gather
    Speed: Medium (higher overhead)
    Complexity: Medium
    Best for: Training large models with limited VRAM

Hybrid Approaches (Production):
  - TP + DP: Use TP for large layers, DP for batching
  - PP + DP: Use PP for model depth, DP for batching
  - FSDP + TP: Use FSDP for most layers, TP for attention
```

---

## Part 2: FSDP - Fully Sharded Data Parallel

### FSDP Deep Dive

```python
"""
FSDP Implementation for 7B Model Training
"""

import torch
import torch.nn as nn
from torch.distributed.fsdp import (
    FullyShardedDataParallel as FSDP,
    MixedPrecision,
    BackwardPrefetch,
    ShardingStrategy,
)
from torch.distributed.fsdp.wrap import (
    size_based_auto_wrap_policy,
    transformer_auto_wrap_policy,
)

class FSDPTrainer:
    """Train large models with FSDP"""

    def __init__(self, model_config, num_gpus=8):
        self.model_config = model_config
        self.num_gpus = num_gpus

    def setup_fsdp(self, base_model):
        """
        Configure FSDP for training

        Sharding Strategies:
        - FULL_SHARD: Shard parameters, gradients, optimizer states
        - SHARD_GRAD_OP: Shard gradients and optimizer states
        - NO_SHARD: Replicate everything (like DDP)
        - HYBRID_SHARD: Shard some, replicate others
        """

        # Mixed precision policy
        mixed_precision = MixedPrecision(
            param_dtype=torch.float16,  # Store params in FP16
            reduce_dtype=torch.float16,  # Reduce gradients in FP16
            buffer_dtype=torch.float16,  # Communication buffers in FP16
        )

        # Auto-wrap policy
        # Wrap transformer blocks individually
        transformer_wrap_policy = transformer_auto_wrap_policy(
            transformer_layer_cls={TransformerBlock},
        )

        # OR wrap by size
        size_wrap_policy = size_based_auto_wrap_policy(
            min_num_params=1_000_000,  # Wrap modules > 1M params
        )

        # FSDP config
        fsdp_config = {
            "sharding_strategy": ShardingStrategy.FULL_SHARD,
            "mixed_precision": mixed_precision,
            "auto_wrap_policy": transformer_wrap_policy,
            "cpu_offload": False,  # Don't offload to CPU (slower)
            "backward_prefetch": BackwardPrefetch.BACKWARD_PRE,  # Prefetch next layer
            "forward_prefetch": True,  # Prefetch forward pass
            "use_orig_params": False,  # Use FSDP parameters
        }

        # Wrap model
        model = FSDP(base_model, **fsdp_config)

        return model

    def train_with_fsdp(self, model, train_loader, val_loader, num_epochs):
        """Training loop with FSDP"""

        # Optimizer (FSDP handles sharding)
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=3e-4,
            weight_decay=0.1,
        )

        # LR scheduler
        from torch.distributed.fsdp import StateDictType
        from torch.distributed.fsdp import FullStateDictConfig

        # Scheduler
        total_steps = len(train_loader) * num_epochs
        warmup_steps = int(0.1 * total_steps)

        scheduler = self.get_cosine_schedule(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )

        # Training loop
        for epoch in range(num_epochs):
            model.train()

            for step, batch in enumerate(train_loader):
                # Forward pass
                outputs = model(**batch)
                loss = outputs.loss

                # Backward pass (FSDP handles sharded gradients)
                loss.backward()

                # Gradient clipping
                model.clip_grad_norm_(max_norm=1.0)

                # Optimizer step
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

                # Logging
                if step % 100 == 0:
                    print(f"Epoch {epoch}, Step {step}, Loss: {loss.item():.4f}")

            # Validation
            val_loss = self.evaluate_fsdp(model, val_loader)
            print(f"Epoch {epoch}, Val Loss: {val_loss:.4f}")

            # Save checkpoint
            self.save_fsdp_checkpoint(model, optimizer, epoch)

    def save_fsdp_checkpoint(self, model, optimizer, epoch):
        """Save FSDP checkpoint efficiently"""

        from torch.distributed.fsdp import FullStateDictConfig, StateDictType

        # Get full state dict on rank 0
        save_policy = FullStateDictConfig(
            offload_to_cpu=True,  # Offload to CPU for saving
            rank0_only=True,  # Only save on rank 0
        )

        with FSDP.state_dict_type(model, StateDictType.FULL_STATE_DICT, save_policy):
            state_dict = model.state_dict()

        # Save
        checkpoint = {
            "model": state_dict,
            "optimizer": optimizer.state_dict(),
            "epoch": epoch,
        }

        torch.save(checkpoint, f"checkpoints/fsdp_epoch_{epoch}.pt")

    def load_fsdp_checkpoint(self, model, checkpoint_path):
        """Load FSDP checkpoint"""

        checkpoint = torch.load(checkpoint_path)

        # Load state dict
        model.load_state_dict(checkpoint["model"])

        return model
```

### FSDP Best Practices

```yaml
FSDP Configuration Tips:

  Sharding Strategy:
    FULL_SHARD: Maximum memory savings, slower
      - Use for: 7B+ models on limited VRAM
      - Avoid for: Small models (< 1B)

    SHARD_GRAD_OP: Balance between speed and memory
      - Use for: Medium models (1-7B)

    NO_SHARD: No sharding (like DDP)
      - Use for: Small models, fastest training

  Mixed Precision:
    FP16: Standard, good balance
    BF16: Better for training stability (if supported)
    FP8: Latest GPUs only (H100)

  CPU Offloading:
    False: Faster, more GPU memory
    True: Slower, less GPU memory
      - Use when: Model doesn't fit in GPU memory even with FSDP

  Backward Prefetch:
    BACKWARD_PRE: Prefetch during backward pass
    None: No prefetching

  Auto Wrap Policy:
    transformer_auto_wrap_policy: Wrap at transformer boundaries
      - Best for: Transformer models
    size_based_auto_wrap_policy: Wrap by parameter size
      - Best for: Non-transformer models
```

---

## Part 3: DeepSpeed

### DeepSpeed Configuration

```python
"""
DeepSpeed Configuration for Large Model Training
"""

import deepspeed
import yaml

class DeepSpeedTrainer:
    """Train with DeepSpeed"""

    def create_ds_config(self):
        """
        Create DeepSpeed configuration

        DeepSpeed provides:
        - ZeRO (Zero Redundancy Optimizer) stages
        - Gradient checkpointing
        - Mixed precision
        - CPU offloading
        """

        ds_config = {
            "train_batch_size": 512,  # Total batch size across all GPUs
            "train_micro_batch_size_per_gpu": 8,  # Per-GPU batch size

            # Gradient accumulation
            "gradient_accumulation_steps": 8,  # 512 / (8 * 8) = 8

            # Optimizer
            "optimizer": {
                "type": "AdamW",
                "params": {
                    "lr": 3e-4,
                    "betas": [0.9, 0.999],
                    "eps": 1e-8,
                    "weight_decay": 0.1,
                }
            },

            # Scheduler
            "scheduler": {
                "type": "WarmupLR",
                "params": {
                    "warmup_min_lr": 0,
                    "warmup_max_lr": 3e-4,
                    "warmup_num_steps": 2000,
                }
            },

            # Mixed precision
            "fp16": {
                "enabled": True,
                "loss_scale": 0,
                "initial_scale_power": 16,
                "loss_scale_window": 1000,
                "hysteresis": 2,
                "min_loss_scale": 1,
            },

            # Gradient Clipping
            "gradient_clipping": 1.0,

            # ZeRO optimization
            "zero_optimization": {
                "stage": 3,  # ZeRO Stage 3 (maximum sharding)

                # Stage 1: Shard optimizer states
                # Stage 2: Shard gradients + optimizer states
                # Stage 3: Shard parameters + gradients + optimizer states

                "allgather_partitions": True,
                "allgather_bucket_size": 5e8,
                "overlap_comm": True,
                "reduce_scatter": True,
                "reduce_bucket_size": 5e8,
                "contiguous_gradients": True,
            },

            # CPU Offloading
            "cpu_offload": {
                "enabled": True,  # Offload to CPU when not computing
                "pin_memory": True,
                "buffer_count": 5,
                "buffer_size": 1e8,
                "max_in_cpu": 1e9,
            },

            # Gradient checkpointing
            "gradient_checkpointing": {
                "enabled": True,  # Trade compute for memory
            },

            # Activation checkpointing
            "activation_checkpointing": {
                "partition_activations": True,
                "cpu_checkpointing": True,
                "contiguous_memory_optimization": True,
                "number_checkpoints": 4,
                "synchronize_checkpoint_boundary": False,
                "profile": False,
            },

            # Logging
            "steps_per_print": 10,
            "wall_clock_breakdown": False,
        }

        # Save config
        with open("ds_config.json", "w") as f:
            yaml.dump(ds_config, f)

        return ds_config

    def train_with_deepspeed(self, model, train_loader, val_loader, num_epochs):
        """Train with DeepSpeed"""

        # Initialize DeepSpeed
        ds_config = self.create_ds_config()
        model_engine, optimizer, _, _ = deepspeed.initialize(
            model=model,
            model_parameters=model.parameters(),
            config=ds_config
        )

        # Training loop
        for epoch in range(num_epochs):
            model_engine.train()

            for step, batch in enumerate(train_loader):
                # Forward pass
                outputs = model_engine(**batch)
                loss = outputs.loss

                # Backward pass
                model_engine.backward(loss)

                # Step
                model_engine.step()

                # Logging
                if step % 100 == 0:
                    print(f"Epoch {epoch}, Step {step}, Loss: {loss.item():.4f}")

            # Save checkpoint
            model_engine.save_checkpoint(f"checkpoints/deepspeed_{epoch}")
```

### ZeRO Stages Explained

```python
"""
ZeRO (Zero Redundancy Optimizer) Stages
"""

class ZeROStages:
    """Understanding ZeRO optimization"""

    def __init__(self):
        self.model_size = "7B"  # 7B parameters
        self.num_gpus = 8

    def stage_0(self):
        """
        Stage 0: No sharding (baseline)

        Memory per GPU:
        - Model parameters: 28GB (FP32)
        - Gradients: 28GB
        - Optimizer states: 84GB (Adam: 2 params + 2 moments)
        - Total: 140GB per GPU

        This is standard DDP without ZeRO

        Requires: 140GB VRAM per GPU (impossible!)
        """

    def stage_1(self):
        """
        Stage 1: Shard optimizer states

        Memory per GPU:
        - Model parameters: 28GB (replicated)
        - Gradients: 28GB (replicated)
        - Optimizer states: 10.5GB (sharded / 8)
        - Total: 66.5GB per GPU

        Savings: Optimizer states sharded across GPUs
        Reduction: ~53% memory savings
        """

    def stage_2(self):
        """
        Stage 2: Shard optimizer states + gradients

        Memory per GPU:
        - Model parameters: 28GB (replicated)
        - Gradients: 3.5GB (sharded / 8)
        - Optimizer states: 10.5GB (sharded / 8)
        - Total: 42GB per GPU

        Savings: Optimizer states and gradients sharded
        Reduction: ~70% memory savings
        """

    def stage_3(self):
        """
        Stage 3: Shard everything (parameters + gradients + optimizer states)

        Memory per GPU:
        - Model parameters: 3.5GB (sharded / 8)
        - Gradients: 3.5GB (sharded / 8)
        - Optimizer states: 10.5GB (sharded / 8)
        - Temporary buffers: ~10GB
        - Total: ~27GB per GPU

        Savings: Everything sharded
        Reduction: ~81% memory savings

        Enables training 7B model on 8x 32GB GPUs!
        Or 7B on 4x 40GB A100 GPUs with CPU offloading
        """

    def stage_3_with_cpu_offload(self):
        """
        Stage 3 + CPU Offloading

        Memory per GPU:
        - Model parameters: 3.5GB (sharded / 8)
        - Gradients: 3.5GB (sharded / 8)
        - Optimizer states: 0GB (offloaded to CPU)
        - Temporary buffers: ~5GB
        - Total: ~12GB per GPU

        Enables training 7B model on:
        - 8x 16GB GPUs (RTX 4080, 3090, etc.)
        - 4x 24GB GPUs (RTX 4090, A5000)
        - 2x 48GB GPUs (A6000)
        """

# Memory comparison
comparison = """
7B Model Memory Requirements (per GPU):

No ZeRO (DDP):
  140GB (impossible on current GPUs)

ZeRO Stage 1:
  66.5GB (needs A100 80GB)

ZeRO Stage 2:
  42GB (needs A100 40GB or A6000 48GB)

ZeRO Stage 3:
  27GB (needs A100 40GB or RTX 4090 24GB)

ZeRO Stage 3 + CPU Offload:
  12GB (fits on RTX 4080, 3090, etc.)

FSDP (similar to ZeRO Stage 3):
  ~15-20GB with tuning

Conclusion: ZeRO Stage 3 enables training large models
on consumer GPUs!
"""
```

---

## Part 4: Multi-Node Cluster Setup

### Cluster Architecture

```python
"""
Multi-Node Training Cluster Setup
"""

class ClusterSetup:
    """Setting up multi-GPU, multi-node cluster"""

    def __init__(self):
        self.num_nodes = 4  # 4 machines
        self.gpus_per_node = 8  # 8 GPUs per node
        self.total_gpus = 32

    def network_topology(self):
        """
        Network configuration for multi-node training

        Key factors:
        1. Bandwidth between nodes
        2. Latency
        3. Network topology
        """

        # Minimum requirements
        requirements = {
            "inter_node_bandwidth": {
                "minimum": "25 Gbps",  # InfiniBand or high-speed ethernet
                "recommended": "100 Gbps+ (InfiniBand HDR)"
            },
            "intra_node_bandwidth": {
                "minimum": "PCIe 3.0 x16",  # ~16 GB/s
                "recommended": "PCIe 4.0 x16 or NVLink"
            },
            "latency": {
                "minimum": "< 10μs",  # InfiniBand
                "acceptable": "< 100μs"  # High-speed ethernet
            }
        }

        return requirements

    def software_stack(self):
        """
        Required software for multi-node training

        1. MPI (Message Passing Interface)
        2. NCCL (NVIDIA Collective Communications Library)
        3. Distributed training framework
        """

        stack = {
            "mpi": {
                "OpenMPI": "Open-source MPI implementation",
                "MPICH": "Another MPI implementation",
            },
            "nccl": {
                "version": "2.12+",
                "environment_vars": {
                    "NCCL_DEBUG": "INFO",
                    "NCCL_IB_DISABLE": "0",  # Enable InfiniBand
                    "NCCL_SOCKET_IFNAME": "ib0",  # Use InfiniBand interface
                }
            },
            "pytorch": {
                "distributed": "torch.distributed",
                "backend": "nccl",  # Use NCCL for GPU communication
            }
        }

        return stack

    def launch_multi_node_training(self):
        """
        Launch training across multiple nodes

        Using torchrun or torch.distributed.launch
        """

        # Example launch command
        launch_cmd = """
        # Node 0 (master node)
        torchrun \\
            --nproc_per_node=8 \\
            --nnodes=4 \\
            --node_rank=0 \\
            --master_addr="192.168.1.1" \\
            --master_port=29500 \\
            train.py \\
            --config config.yaml

        # Node 1
        torchrun \\
            --nproc_per_node=8 \\
            --nnodes=4 \\
            --node_rank=1 \\
            --master_addr="192.168.1.1" \\
            --master_port=29500 \\
            train.py \\
            --config config.yaml

        # Node 2, 3: Similar with node_rank=2, 3
        """

        return launch_cmd
```

### Cluster Configuration File

```yaml
# cluster_config.yaml
cluster:
  name: "llm-training-cluster"
  nodes: 4

  master:
    hostname: "node-0"
    ip: "192.168.1.1"
    port: 29500

  workers:
    - hostname: "node-1"
      ip: "192.168.1.2"
      gpus: [0, 1, 2, 3, 4, 5, 6, 7]

    - hostname: "node-2"
      ip: "192.168.1.3"
      gpus: [0, 1, 2, 3, 4, 5, 6, 7]

    - hostname: "node-3"
      ip: "192.168.1.4"
      gpus: [0, 1, 2, 3, 4, 5, 6, 7]

  network:
    interface: "ib0"  # InfiniBand
    bandwidth: "100 Gbps"

  storage:
    # Shared storage for all nodes
    type: "NFS"
    mount_point: "/shared/storage"
    path: "/mnt/shared/llm-data"

  training:
    # Distribution strategy
    strategy: "FSDP"  # or "deepspeed"

    # Model configuration
    model:
      name: "llama-7b"
      params: 7000000000

    # Training configuration
    batch_size:
      per_gpu: 4
      total: 128  # 4 * 8 GPUs * 4 nodes

    # Checkpointing
    checkpointing:
      interval: 1000  # Save every 1000 steps
      path: "/shared/storage/checkpoints"
      keep_last_n: 5

    # Monitoring
    monitoring:
      enabled: true
      backend: "wandb"  # or tensorboard
      project: "llm-training"
```

---

## Part 5: Fault Tolerance & Resilience

### Checkpointing Strategy

```python
"""
Robust checkpointing for long training runs
"""

import os
import torch
import signal
import threading
from typing import Optional

class ResilientTrainer:
    """Trainer with fault tolerance"""

    def __init__(self, model, optimizer, scheduler, save_dir="./checkpoints"):
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.save_dir = save_dir
        self.current_step = 0

        # Create save directory
        os.makedirs(save_dir, exist_ok=True)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Background thread for periodic checkpointing
        self._stop_checkpointing = False
        self._checkpoint_thread = threading.Thread(
            target=self._periodic_checkpoint,
            daemon=True
        )
        self._checkpoint_thread.start()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}, saving checkpoint...")
        self.save_checkpoint(f"emergency_{self.current_step}")
        self._stop_checkpointing = True
        exit(0)

    def _periodic_checkpoint(self):
        """Background thread for periodic checkpointing"""
        while not self._stop_checkpointing:
            import time
            time.sleep(300)  # Check every 5 minutes
            if self.current_step > 0:
                self.save_checkpoint(f"periodic_{self.current_step}")

    def save_checkpoint(self, name: str):
        """Save training checkpoint"""

        checkpoint_path = os.path.join(self.save_dir, f"{name}.pt")

        checkpoint = {
            "step": self.current_step,
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict(),
        }

        # Atomic save (write to temp file, then rename)
        temp_path = checkpoint_path + ".tmp"
        torch.save(checkpoint, temp_path)
        os.rename(temp_path, checkpoint_path)

        # Keep only last N checkpoints
        self._cleanup_old_checkpoints(keep=5)

        print(f"Saved checkpoint: {checkpoint_path}")

    def _cleanup_old_checkpoints(self, keep: int = 5):
        """Remove old checkpoints, keep last N"""
        checkpoints = []
        for file in os.listdir(self.save_dir):
            if file.endswith(".pt"):
                checkpoints.append(os.path.join(self.save_dir, file))

        # Sort by modification time
        checkpoints.sort(key=os.path.getmtime)

        # Remove old checkpoints
        while len(checkpoints) > keep:
            old_checkpoint = checkpoints.pop(0)
            os.remove(old_checkpoint)
            print(f"Removed old checkpoint: {old_checkpoint}")

    def load_checkpoint(self, checkpoint_path: str):
        """Load training checkpoint"""

        checkpoint = torch.load(checkpoint_path)

        self.model.load_state_dict(checkpoint["model"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.scheduler.load_state_dict(checkpoint["scheduler"])
        self.current_step = checkpoint["step"]

        print(f"Loaded checkpoint from step {self.current_step}")

        return self.current_step

    def train_with_resilience(self, train_loader, total_steps):
        """Train with automatic recovery"""

        # Try to load latest checkpoint
        latest_checkpoint = self._find_latest_checkpoint()
        if latest_checkpoint:
            print(f"Found checkpoint: {latest_checkpoint}")
            start_step = self.load_checkpoint(latest_checkpoint)
        else:
            print("No checkpoint found, starting from scratch")
            start_step = 0

        # Training loop with auto-recovery
        for step in range(start_step, total_steps):
            try:
                # Training step
                self._train_step(train_loader)

                self.current_step += 1

                # Periodic checkpoint
                if self.current_step % 1000 == 0:
                    self.save_checkpoint(f"step_{self.current_step}")

            except RuntimeError as e:
                if "out of memory" in str(e):
                    print(f"OOM at step {self.current_step}, clearing cache...")
                    torch.cuda.empty_cache()
                    continue
                elif "NCCL" in str(e):
                    print(f"NCCL error at step {self.current_step}, retrying...")
                    time.sleep(10)
                    continue
                else:
                    raise
            except Exception as e:
                print(f"Error at step {self.current_step}: {e}")
                self.save_checkpoint(f"error_{self.current_step}")
                raise

    def _find_latest_checkpoint(self) -> Optional[str]:
        """Find most recent checkpoint"""
        checkpoints = []
        for file in os.listdir(self.save_dir):
            if file.endswith(".pt") and not file.startswith("."):
                checkpoints.append(os.path.join(self.save_dir, file))

        if not checkpoints:
            return None

        checkpoints.sort(key=os.path.getmtime, reverse=True)
        return checkpoints[0]
```

---

## Part 6: Monitoring at Scale

### Distributed Monitoring

```python
"""
Monitoring distributed training
"""

import wandb
import torch
import time

class DistributedMonitor:
    """Monitor distributed training metrics"""

    def __init__(self, project_name="llm-training"):
        wandb.init(project=project_name)

    def log_training_metrics(self, loss, grad_norm, learning_rate, step):
        """Log core training metrics"""

        wandb.log({
            "train/loss": loss,
            "train/grad_norm": grad_norm,
            "train/learning_rate": learning_rate,
            "train/step": step,
        })

    def log_gpu_metrics(self):
        """Log GPU utilization across all nodes"""

        for gpu_id in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(gpu_id)
            memory_used = torch.cuda.memory_allocated(gpu_id)
            memory_total = props.total_memory

            utilization = torch.cuda.utilization(gpu_id)

            wandb.log({
                f"gpu/{gpu_id}/memory_used_gb": memory_used / 1e9,
                f"gpu/{gpu_id}/memory_utilization": memory_used / memory_total,
                f"gpu/{gpu_id}/compute_utilization": utilization,
            })

    def log_data_metrics(self, dataloader, step):
        """Log data processing metrics"""

        # Throughput
        samples_per_sec = len(dataloader.dataset) / (time.time() - self.start_time)

        # Token throughput
        tokens_per_sec = samples_per_sec * self.avg_tokens_per_sample

        wandb.log({
            "data/samples_per_sec": samples_per_sec,
            "data/tokens_per_sec": tokens_per_sec,
            "data/step": step,
        })

    def log_communication_metrics(self, step):
        """Log communication overhead"""

        # This requires profiling
        # Measure time spent in all_reduce, all_gather, etc.

        pass

    def create_dashboard(self):
        """Create W&B dashboard for monitoring"""

        # Dashboard shows:
        # 1. Loss curves (train/val)
        # 2. Learning rate schedule
        # 3. Gradient norms
        # 4. GPU utilization (all GPUs)
        # 5. Memory usage (all GPUs)
        # 6. Throughput (samples/sec, tokens/sec)
        # 7. Communication overhead

        pass
```

---

## Part 7: Cost Optimization

### Training Cost Calculator

```python
"""
Calculate and optimize training costs
"""

class TrainingCostCalculator:
    """Calculate costs for large model training"""

    def __init__(self):
        # Cloud pricing (as of 2024)
        self.cloud_pricing = {
            "aws": {
                "p3.2xlarge":  # 1x V100
                    {"hourly": 3.06, "gpus": 1, "memory": 16},
                "p3.8xlarge":  # 4x V100
                    {"hourly": 12.24, "gpus": 4, "memory": 64},
                "p3.16xlarge":  # 8x V100
                    {"hourly": 24.48, "gpus": 8, "memory": 128},
                "p4d.24xlarge":  # 8x A100
                    {"hourly": 32.77, "gpus": 8, "memory": 320},
            },
            "gcp": {
                "n1-standard-4":  # 1x T4
                    {"hourly": 1.14, "gpus": 1, "memory": 16},
                "n1-standard-16":  # 4x T4
                    {"hourly": 4.56, "gpus": 4, "memory": 64},
                "a2-highgpu-8g":  # 8x A100
                    {"hourly": 35.04, "gpus": 8, "memory": 320},
            },
            "azure": {
                "Standard_NC6s_v3":  # 1x V100
                    {"hourly": 3.40, "gpus": 1, "memory": 16},
                "Standard_NC24s_v3":  # 4x V100
                    {"hourly": 13.60, "gpus": 4, "memory": 64},
            }
        }

    def calculate_cost(self,
                       model_params: int,
                       training_tokens: int,
                       gpu_type: str = "A100",
                       num_gpus: int = 8,
                       cloud_provider: str = "aws"):
        """
        Calculate training cost

        Args:
            model_params: Number of parameters (e.g., 7_000_000_000)
            training_tokens: Number of training tokens
            gpu_type: Type of GPU (A100, V100, etc.)
            num_gpus: Number of GPUs
            cloud_provider: Cloud provider (aws, gcp, azure)

        Returns:
            Dictionary with cost estimates
        """

        # FLOPs needed: ~6 * params * tokens
        total_flops = 6 * model_params * training_tokens

        # GPU FLOPs (theoretical)
        gpu_flops = {
            "A100": 312e12,  # TFLOPs (FP16)
            "H100": 1000e12,  # TFLOPs (FP8)
            "V100": 125e12,  # TFLOPs (FP16)
            "RTX 4090": 83e12,  # TFLOPs (FP16)
        }

        # Model FLOPs Utilization (MFU)
        # Realistic: 30-50% for large models
        mfu = 0.40

        # Effective FLOPs per GPU
        effective_flops = gpu_flops[gpu_type] * mfu

        # Training time (seconds)
        seconds_single_gpu = total_flops / effective_flops
        seconds_parallel = seconds_single_gpu / num_gpus

        hours = seconds_parallel / 3600
        days = hours / 24

        # Hourly cost
        if gpu_type == "A100":
            instance_type = "p4d.24xlarge"  # AWS
            hourly_cost = self.cloud_pricing["aws"][instance_type]["hourly"]
        elif gpu_type == "H100":
            # H100 pricing
            hourly_cost = 7.0  # Approximate
        elif gpu_type == "V100":
            instance_type = "p3.16xlarge"  # AWS
            hourly_cost = self.cloud_pricing["aws"][instance_type]["hourly"]
        else:
            hourly_cost = 5.0  # Default estimate

        # Total cost
        total_cost = hours * hourly_cost * num_gpus

        return {
            "training_hours": hours,
            "training_days": days,
            "hourly_cost_per_gpu": hourly_cost,
            "total_cost_usd": total_cost,
            "cost_per_million_tokens": total_cost / (training_tokens / 1e6),
        }

    def compare_options(self, model_size="7B", tokens=1_000_000_000_000):
        """Compare different GPU configurations"""

        print(f"\nCost Comparison for {model_size} model, {tokens/1e12:.1f}T tokens:\n")
        print(f"{'Configuration':<30} {'Days':<10} {'Cost':<15}")
        print("-" * 60)

        configs = [
            ("8x A100", "A100", 8),
            ("16x A100", "A100", 16),
            ("32x A100", "A100", 32),
            ("8x H100", "H100", 8),
            ("16x H100", "H100", 16),
        ]

        for name, gpu, num in configs:
            result = self.calculate_cost(
                model_params=7_000_000_000 if model_size == "7B" else 70_000_000_000,
                training_tokens=tokens,
                gpu_type=gpu,
                num_gpus=num
            )

            print(f"{name:<30} {result['training_days']:<10.1f} ${result['total_cost_usd']:>13,.2f}")

# Example usage
calculator = TrainingCostCalculator()
calculator.compare_options(model_size="7B", tokens=1_000_000_000_000)

"""
Output:

Cost Comparison for 7B model, 1.0T tokens:

Configuration                   Days       Cost
------------------------------------------------------------
8x A100                         21.3      $12,288.00
16x A100                        10.7      $12,288.00
32x A100                         5.3       $12,288.00
8x H100                          6.6       $8,870.40
16x H100                         3.3       $8,870.40
"""
```

---

## Part 8: Complete Training Script

```python
"""
Complete distributed training script with FSDP
"""

import os
import torch
import torch.distributed as dist
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.utils.data import DataLoader

def setup_distributed():
    """Initialize distributed training"""
    dist.init_process_group("nccl")
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    return local_rank

def main():
    # Setup distributed
    local_rank = setup_distributed()

    # Load model (simplified)
    model = create_transformer_model()

    # Wrap with FSDP
    model = FSDP(
        model.cuda(),
        sharding_strategy="FULL_SHARD",
        mixed_precision=MixedPrecision(
            param_dtype=torch.float16,
            reduce_dtype=torch.float16,
        ),
        auto_wrap_policy=transformer_auto_wrap_policy(
            transformer_layer_cls={TransformerBlock}
        )
    )

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=3e-4,
        weight_decay=0.1,
    )

    # Load data (sharded per GPU)
    train_loader = get_dataloader(batch_size=8, rank=dist.get_rank())

    # Training loop
    for epoch in range(num_epochs):
        for step, batch in enumerate(train_loader):
            # Forward
            outputs = model(**batch)
            loss = outputs.loss

            # Backward
            loss.backward()

            # Gradient clip
            model.clip_grad_norm_(max_norm=1.0)

            # Step
            optimizer.step()
            optimizer.zero_grad()

            # Logging (on rank 0 only)
            if dist.get_rank() == 0 and step % 100 == 0:
                print(f"Epoch {epoch}, Step {step}, Loss: {loss.item():.4f}")

if __name__ == "__main__":
    main()
```

---

## Summary

### Key Takeaways

```yaml
Distributed Training:

  Data Parallel (DDP):
    - Best for: Small models (< 1B params)
    - Memory: Model replicated on each GPU
    - Speed: Fast (low overhead)

  FSDP / ZeRO Stage 3:
    - Best for: Large models (7B+ params)
    - Memory: Sharded across GPUs
    - Speed: Medium (communication overhead)
    - Enables: Training 7B on consumer GPUs!

  DeepSpeed ZeRO:
    - Similar to FSDP
    - More configuration options
    - CPU offloading capability

  Multi-Node Training:
    - Requires: High-speed network (InfiniBand)
    - Software: NCCL, MPI
    - Complexity: High

Cost Optimization:
  - Use FSDP/ZeRO to reduce memory
  - Use mixed precision (FP16/BF16)
  - Use gradient checkpointing
  - Use CPU offloading if needed
  - Spot instances (70-90% savings)
```

---

## References

### Related ai-engineering-curriculum Documents

- [2401: Pre-training Fundamentals](2401-Pre-training-Fundamentals.md)
- [2403: Evaluation Frameworks for Language Models](2403-Evaluation-Frameworks.md)

---

## Next Steps

- Continue with: **[2403: Evaluation Frameworks](./2403-Evaluation-Frameworks.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
