---
Document ID: 5302
Title: "5302: Distributed Training Orchestration"
Phase: 5
Module: 5300
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'synthetic-data', 'distillation', 'distributed']
---

# 5302: Distributed Training Orchestration

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Distributed Training Strategies](#distributed-training-strategies)
- [K3s Cluster Training](#k3s-cluster-training)
- [Fine-tuning Workflows](#fine-tuning-workflows)
- [Orchestration with Ray](#orchestration-with-ray)
- [Monitoring and Logging](#monitoring-and-logging)
- [Performance Optimization](#performance-optimization)
- [Expected Performance](#expected-performance)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain the memory and communication trade-offs between DataParallel, DDP, FSDP, and DeepSpeed ZeRO
- Smoke-test a real DDP process group on a single-GPU machine before committing to a cluster
- Plan FSDP wrap points and DeepSpeed batch arithmetic before launching a job
- Apply LoRA with the PEFT API and read its trainable-parameter report
- Predict multi-GPU scaling from a serial-fraction fit using Amdahl's law
- Choose between Weights & Biases and TensorBoard and log metrics in their shared (step, metrics) contract

---

## Abstract
Distributed training strategies for the homelab: single-GPU constraints first, with the K3s and Ray paths for scaling out when hardware allows. Every runnable block below executes on a single-GPU machine; the cluster-only paths are clearly marked as reference sketches.

## Distributed Training Strategies

### 1. Data Parallelism (DP)
DataParallel replicates the full model on every visible GPU and splits each batch across the replicas, averaging gradients during backward. It works only when the model fits on one GPU, its scaling is limited by the Python GIL on the replication path, and PyTorch now points new code at DistributedDataParallel — treat it as a legacy baseline. On a single-GPU machine there is nothing to replicate, and the guard below keeps the model in one piece:

```python
"""
Data Parallelism: every GPU holds a full model copy and processes a
different slice of the batch. Gradient all-reduce runs on every backward.
Only worth it when the model fits on a single GPU; PyTorch recommends
DistributedDataParallel (next section) for new code.
"""
import torch
import torch.nn as nn
from torch.nn.parallel import DataParallel

torch.manual_seed(0)

class SmallNet(nn.Module):
    def __init__(self, in_dim=64, hidden=128, out_dim=16):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_dim, hidden), nn.ReLU(),
                                 nn.Linear(hidden, out_dim))

    def forward(self, x):
        return self.net(x)

n_gpus = torch.cuda.device_count()
model = SmallNet().cuda()
if n_gpus > 1:
    model = DataParallel(model)   # replicates the module on every GPU
    print(f"{n_gpus} GPUs -> DataParallel wraps the module")
else:
    print(f"{n_gpus} GPU visible -> no replica possible, wrap skipped")
    print("   (the batch still flows - it simply has one slice)")

inputs = torch.randn(32, 64, device="cuda")
outputs = model(inputs)
loss = outputs.square().mean()
loss.backward()
print("input:", tuple(inputs.shape), "-> output:", tuple(outputs.shape))
print("gradients flowed:", all(p.grad is not None for p in model.parameters()))
```

**Output:**
```text
1 GPU visible -> no replica possible, wrap skipped
   (the batch still flows - it simply has one slice)
input: (32, 64) -> output: (32, 16)
gradients flowed: True
```

### 2. Distributed Data Parallel (DDP)
DDP gives every GPU its own process (a *rank*), which sidesteps the GIL, and synchronizes gradients with an all-reduce after every backward. `torchrun --nproc_per_node=N train.py` launches the workers and sets `MASTER_ADDR`, `MASTER_PORT`, `RANK`, and `WORLD_SIZE` for each. On a single-GPU machine the identical code path can be smoke-tested with `world_size=1` and the CPU `gloo` backend — every API call below is the one a multi-GPU run makes:

```python
"""
DDP: one process per GPU (rank), gradients all-reduced after each
backward. Launch multi-GPU runs with:
    torchrun --nproc_per_node=N train.py
which sets MASTER_ADDR/MASTER_PORT/RANK/WORLD_SIZE per worker. On a
single-GPU box the same API is smoke-tested below with world_size=1
and the CPU gloo backend (use nccl on real GPU nodes).
"""
import torch
import torch.nn as nn
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def setup_ddp():
    """Initialize the process group (torchrun sets these env vars)."""
    if not dist.is_initialized():
        dist.init_process_group(
            backend="gloo",                  # nccl on real GPU nodes
            init_method="tcp://127.0.0.1:29531",
            rank=0, world_size=1,            # stand-in for torchrun env
        )

def cleanup_ddp():
    dist.destroy_process_group()

setup_ddp()
torch.manual_seed(0)
print("world_size:", dist.get_world_size(), "| backend:", dist.get_backend())

model = nn.Linear(64, 16)
ddp_model = DDP(model)                       # params broadcast at construction
optimizer = torch.optim.SGD(ddp_model.parameters(), lr=0.1)
loss_fn = nn.MSELoss()
data, target = torch.randn(32, 64), torch.randn(32, 16)

for step in range(3):
    optimizer.zero_grad()
    loss = loss_fn(ddp_model(data), target)
    loss.backward()      # DDP all-reduces gradients (identity at ws=1)
    optimizer.step()
    print(f"step {step}: loss {loss.item():.4f}")

checksum = ddp_model.module.weight.grad.abs().sum().item()
print("rank-0 gradient checksum: %.4f" % checksum)
cleanup_ddp()
```

**Output:**
```text
world_size: 1 | backend: gloo
step 0: loss 1.2227
step 1: loss 1.1562
step 2: loss 1.0949
rank-0 gradient checksum: 19.0404
```

In a real training loop the dataset is wrapped in a `DistributedSampler` (one disjoint shard per rank, `set_epoch()` called every epoch so shuffling differs per epoch) — see [1204: Multi-GPU Setup](../../phase1-infra/1200-virtualization/1204-Multi-GPU-Setup.md) for the hardware side.

### 3. Fully Sharded Data Parallel (FSDP)
FSDP goes further than replication: parameters, gradients, and optimizer states are *sharded* across GPUs (roughly DeepSpeed ZeRO stage 3), and each wrapped unit is all-gathered on demand, used, and freed. The wrap policy decides the shard granularity. Note that `size_based_auto_wrap_policy` is a plain predicate function, not a factory — pass it via `functools.partial`, and `sharding_strategy` takes the enum, not a string:

```text
import functools
import torch
import torch.distributed as dist
from torch.distributed.fsdp import (
    FullyShardedDataParallel as FSDP,
    CPUOffload,
    ShardingStrategy,
)
from torch.distributed.fsdp.wrap import size_based_auto_wrap_policy

def setup_fsdp(model):
    """Run inside a torchrun worker: torchrun --nproc_per_node=N fsdp_train.py"""
    dist.init_process_group("nccl" if torch.cuda.is_available() else "gloo")
    auto_wrap_policy = functools.partial(
        size_based_auto_wrap_policy, min_num_params=100_000_000
    )
    return FSDP(
        model.cuda(),
        sharding_strategy=ShardingStrategy.FULL_SHARD,  # enum, not "FULL_SHARD"
        auto_wrap_policy=auto_wrap_policy,
        cpu_offload=CPUOffload(offload_params=True),    # optional VRAM relief
        device_id=torch.cuda.current_device(),
    )
# the training loop is unchanged: forward -> backward -> step
```

The wrap threshold is worth planning before a cluster run: it decides how many communication rounds each forward/backward makes. The calculator below replays the policy's bottom-up logic on a small model — no process group needed:

```python
"""
FSDP shard granularity comes from the wrap policy: every submodule above
the threshold becomes one all-gather/free unit. size_based_auto_wrap_
policy works bottom-up — a module's count excludes descendants that were
already wrapped, and leaves absorb into their parents. The planner below
replays that logic on a toy LM to show what the threshold selects.
"""
import torch.nn as nn

class Block(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.attn = nn.Linear(dim, dim, bias=False)
        self.mlp = nn.Sequential(nn.Linear(dim, 4 * dim, bias=False),
                                 nn.GELU(),
                                 nn.Linear(4 * dim, dim, bias=False))

class ToyLM(nn.Module):
    def __init__(self, dim=256, layers=4, vocab=1000):
        super().__init__()
        self.blocks = nn.ModuleList(Block(dim) for _ in range(layers))
        self.head = nn.Linear(dim, vocab, bias=False)

def count_params(m):
    return sum(p.numel() for p in m.parameters())

model = ToyLM()
MIN_NUM_PARAMS = 100_000        # the size_based_auto_wrap_policy knob

# Bottom-up plan, mirroring the real policy: a module's count excludes
# descendants that were already wrapped, and leaves absorb into parents.
wrap_units = {}                 # name -> own parameter count
for name, mod in reversed(list(model.named_modules())):
    if name == "" or not list(mod.children()):
        continue                                 # root or leaf
    wrapped_desc = sum(v for k, v in wrap_units.items()
                       if k.startswith(name + "."))
    own = count_params(mod) - wrapped_desc
    if own >= MIN_NUM_PARAMS:
        wrap_units[name] = own

print(f"threshold {MIN_NUM_PARAMS:,} -> {len(wrap_units)} wrap units:")
for name in sorted(wrap_units):
    print(f"  {name}: {wrap_units[name]:,} params")

total = count_params(model)
per_gpu = total * 4 / 4                          # FULL_SHARD across 4 GPUs
print(f"model total: {total:,} params | weights/GPU on 4-way sharding: "
      f"{per_gpu / 1e6:.2f} MB")
```

**Output:**
```text
threshold 100,000 -> 5 wrap units:
  blocks: 262,144 params
  blocks.0.mlp: 524,288 params
  blocks.1.mlp: 524,288 params
  blocks.2.mlp: 524,288 params
  blocks.3.mlp: 524,288 params
model total: 2,615,296 params | weights/GPU on 4-way sharding: 2.62 MB
```

Once each `mlp` is wrapped (524k params ≥ 100k), the `blocks` container's *residual* parameters — the four `attn` linears at 262k total — still clear the threshold, so the ModuleList becomes a fifth unit. Lower the threshold and the same model fragments into many small units: more parallelism in the all-gather schedule, but more communication overhead.

### 4. DeepSpeed ZeRO
ZeRO shards optimizer states (stage 1), gradients (stage 2), and parameters (stage 3) to cut per-GPU memory — see the stage-by-stage memory calculator in [2302: Model Serving Architectures](../../phase2-foundations/2300-framework-engineering/2302-Model-Serving-Architectures.md). The `deepspeed` package is not part of this lesson environment, so the engine construction is a reference sketch ([DeepSpeed - Getting Started](https://www.deepspeed.ai/getting-started/)); the config arithmetic it depends on runs fine on plain Python:

```text
import deepspeed   # uv pip install deepspeed  (CUDA + Linux toolchain)

model_engine, optimizer, _, _ = deepspeed.initialize(
    model=model,             # your torch nn.Module
    config=ds_config,        # the config validated below
)
for batch in dataloader:
    loss = model_engine(batch)
    model_engine.backward(loss)
    model_engine.step()
```

DeepSpeed enforces one identity at engine construction — if it fails on a cluster after a queue wait, the arithmetic was checkable locally all along:

```python
"""
DeepSpeed global-batch identity:
    train_batch_size == train_micro_batch_size_per_gpu
                     * gradient_accumulation_steps * world_size
The engine raises when the numbers disagree; checking before launch
saves a cluster round-trip.
"""
ds_config = {
    "train_batch_size": 32,
    "train_micro_batch_size_per_gpu": 4,
    "gradient_accumulation_steps": 2,
    "optimizer": {"type": "AdamW",
                  "params": {"lr": 1e-4, "betas": [0.9, 0.95], "eps": 1e-8}},
    "scheduler": {"type": "WarmupDecayLR",
                  "params": {"total_num_steps": 1000, "warmup_min_lr": 0,
                             "warmup_max_lr": 1e-4, "warmup_num_steps": 100}},
    "fp16": {"enabled": True},
    "zero_optimization": {"stage": 2, "overlap_comm": True},
    "gradient_clipping": 1.0,
}

world_size = 4
micro = ds_config["train_micro_batch_size_per_gpu"]
accum = ds_config["gradient_accumulation_steps"]
global_batch = ds_config["train_batch_size"]
product = micro * accum * world_size

print(f"global batch    : {global_batch}")
print(f"micro x accum x ws: {micro} x {accum} x {world_size} = {product}")
print("consistent:", product == global_batch)

epoch_samples = 10_000
steps = epoch_samples // global_batch
warmup = ds_config["scheduler"]["params"]["warmup_num_steps"]
print(f"{epoch_samples:,} samples -> {steps} optimizer steps per epoch")
print(f"warmup {warmup} steps = {warmup / steps:.0%} of one epoch")
```

**Output:**
```text
global batch    : 32
micro x accum x ws: 4 x 2 x 4 = 32
consistent: True
10,000 samples -> 312 optimizer steps per epoch
warmup 100 steps = 32% of one epoch
```

## K3s Cluster Training

Long-running training maps naturally onto Kubernetes Jobs: the scheduler places the pod on a GPU node, PVCs carry datasets and checkpoints across pod restarts, and `backoffLimit` absorbs transient failures.

### GPU Scheduling Configuration
```yaml
# gpu-training-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: llm-training
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: trainer
        image: ghcr.io/your-org/llm-trainer:latest
        resources:
          limits:
            nvidia.com/gpu: "1"  # one 11GB-class GPU per replica
        command:
          - python
          - train.py
          - --config
          - /config/train_config.yaml
        volumeMounts:
          - name: dataset
            mountPath: /data
          - name: checkpoints
            mountPath: /checkpoints
          - name: config
            mountPath: /config
      volumes:
        - name: dataset
          persistentVolumeClaim:
            claimName: dataset-pvc
        - name: checkpoints
          persistentVolumeClaim:
            claimName: checkpoints-pvc
        - name: config
          configMap:
            name: train-config
```

### Multi-Node Training Setup
For multi-node DDP, the [Kubeflow Trainer docs](https://www.kubeflow.org/docs/components/trainer/) (the Training Operator's successor) cover the `PyTorchJob` kind, which manages the master/worker processes and injects rendezvous env vars (`WORLD_SIZE` = 1 master + 2 workers here):

```yaml
# multi-node-training.yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: distributed-training
spec:
  elasticPolicy:
    minReplicas: 2
    maxReplicas: 4
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: ghcr.io/your-org/llm-trainer:latest
            resources:
              limits:
                nvidia.com/gpu: "1"
    Worker:
      replicas: 2
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: ghcr.io/your-org/llm-trainer:latest
            resources:
              limits:
                nvidia.com/gpu: "1"
            env:
            - name: MASTER_ADDR
              value: "distributed-training-master-0"
            - name: MASTER_PORT
              value: "23456"
            - name: WORLD_SIZE
              value: "3"  # 1 master + 2 workers
```

## Fine-tuning Workflows

### QLoRA Distributed Training
QLoRA freezes a 4-bit (NF4) base model and trains LoRA adapters on top — the recipe is developed in [5102: QLoRA Pipelines](../5100-peft/5102-QLoRA-Pipelines.md) and [5101: LoRA Logic](../5100-peft/5101-LoRA-Logic.md). The reference script needs `bitsandbytes` plus access to a gated 7B repo, so it cannot run in this lesson's environment; it is kept as a text reference with the two footguns that most often break it:

```text
# uv pip install bitsandbytes peft transformers  (CUDA required for NF4)
import torch
from transformers import (AutoModelForCausalLM, TrainingArguments,
                          Trainer, BitsAndBytesConfig)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-8B",        # ungated: no HF token needed
    quantization_config=bnb_config,
    device_map={"": 0},                # ONE GPU per process under DDP -
                                       # device_map="auto" sharding is
                                       # incompatible with Trainer DDP
)
model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
))
training_args = TrainingArguments(
    output_dir="./qlora-checkpoint",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,     # effective batch = 2*8*world_size
    learning_rate=1e-4,
    fp16=True,
    gradient_checkpointing=True,
    ddp_find_unused_parameters=False,  # DDP flag; torchrun sets LOCAL_RANK
                                       # and the Trainer reads it itself
    logging_steps=10, save_steps=100, save_total_limit=3,
)
trainer = Trainer(model=model, args=training_args, train_dataset=train_dataset)
trainer.train()
```

The LoRA half, though, runs anywhere — PEFT applies to a tiny locally-built model with the same API as the 7B recipe, no download required:

```python
"""
LoRA with PEFT on a locally built toy model: same API as the 7B QLoRA
recipe above (r=16, alpha=32, q/v targets) but no gated download. The
frozen base stays untouched; only the adapter matrices train.
"""
import torch
from transformers import AutoModelForCausalLM, LlamaConfig
from peft import LoraConfig, get_peft_model

torch.manual_seed(0)
config = LlamaConfig(vocab_size=256, hidden_size=64, intermediate_size=128,
                     num_hidden_layers=2, num_attention_heads=4)
base = AutoModelForCausalLM.from_config(config)   # random init, all local

lora_config = LoraConfig(
    r=16, lora_alpha=32,
    target_modules=["q_proj", "v_proj"],          # the 7B recipe adds k_proj, o_proj
    lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
)
model = get_peft_model(base, lora_config)
model.print_trainable_parameters()

trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"adapter weights: {trainable:,} | frozen base: {total - trainable:,}")
```

**Output:**
```text
trainable params: 8,192 || all params: 123,200 || trainable%: 6.6494
adapter weights: 8,192 | frozen base: 115,008
```

Adapter weights scale roughly with `r x (in_dim + out_dim)` per targeted projection — r=16 on two projections per layer costs 2,048 params per layer here, 6.6% of the model; on the 7B recipe with four targets it stays under 1%.

## Orchestration with Ray

For heterogeneous clusters (mixed GPU sizes, preemption, many concurrent jobs), Ray Train wraps the DDP loop with resource allocation, scaling, and fault tolerance. The `ray` package is not installed in this environment; the sketch is a reference ([Ray Train Documentation](https://docs.ray.io/en/latest/train/train.html)) — note the `zero_grad()` that the distributed loop must not forget:

```text
# uv pip install "ray[train]"
import ray
from ray.train import ScalingConfig
from ray.train.torch import TorchTrainer, get_device

def train_func(config):
    """Runs on every worker; Ray places the worker on a GPU and
    prepares the model/dataloader for distributed execution."""
    import torch
    from torch.nn.parallel import DistributedDataParallel as DDP

    device = get_device()
    model = build_model().to(device)
    model = DDP(model, device_ids=[device.index] if device.type == "cuda" else None)

    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"])
    for epoch in range(config["epochs"]):
        for batch in prepare_dataloader():   # Ray shards data per worker
            optimizer.zero_grad()            # required every step
            loss = compute_loss(model(batch))
            loss.backward()
            optimizer.step()

trainer = TorchTrainer(
    train_func,
    train_loop_config={"epochs": 10, "lr": 1e-4},
    scaling_config=ScalingConfig(num_workers=2, use_gpu=True,
                                 resources_per_worker={"GPU": 1}),
)
result = trainer.fit()
```

Whether that second worker is worth it is a serial-fraction question. Distributed speedup is capped by the serial part of the job — all-reduce waits, data loading, checkpointing — through Amdahl's law, `speedup(N) = 1 / (s + (1 - s) / N)`. The calculator inverts a measured speedup to recover the implied serial fraction, then predicts the next data point:

```python
"""
Amdahl's law for distributed training:
    speedup(N) = 1 / (s + (1 - s) / N)
Invert a measured speedup to recover the implied serial fraction s,
then predict the next cluster size before ordering hardware.
"""
def amdahl_speedup(serial_fraction, n):
    return 1.0 / (serial_fraction + (1.0 - serial_fraction) / n)

TABLE = [("2x GPU", 1.7), ("4x GPU", 3.0)]
for label, measured in TABLE:
    n = int(label.split("x")[0])
    s = (1.0 / measured - 1.0 / n) / (1.0 - 1.0 / n)
    print(f"{label}: measured {measured:.1f}x -> implied serial fraction {s:.3f}")

s = 0.176                                    # fit to the 2-GPU point
print(f"predicting with s = {s}:")
for n in (2, 4, 8):
    sp = amdahl_speedup(s, n)
    print(f"  N={n}: {sp:.2f}x speedup, {sp / n:.0%} efficiency")
```

**Output:**
```text
2x GPU: measured 1.7x -> implied serial fraction 0.176
4x GPU: measured 3.0x -> implied serial fraction 0.111
predicting with s = 0.176:
  N=2: 1.70x speedup, 85% efficiency
  N=4: 2.62x speedup, 65% efficiency
  N=8: 3.58x speedup, 45% efficiency
```

The 2-GPU fit predicts 2.62x at four GPUs, while the table's 3.0x target implies s dropped to 0.111 — communication overlaps better at larger scale. Plan with the conservative fit; treat better-than-predicted results as confirmation that overlap is working.

## Monitoring and Logging

Every tracker in this lesson shares one contract: append `(step, metrics)` records keyed by name. `wandb.log()` and `SummaryWriter.add_scalar()` are fancier frontends for exactly the file the minimal recorder below writes — run it to see the shape every backend produces:

```python
"""
The shared logging contract: (step, key/value metrics) records, appended
in order. wandb.log and SummaryWriter.add_scalar are production versions
of this JSONL writer.
"""
import json
import tempfile
from pathlib import Path

class MetricsRecorder:
    """The (step, metrics) contract wandb.log / SummaryWriter share."""

    def __init__(self, logdir):
        self.path = Path(logdir) / "metrics.jsonl"
        self._f = self.path.open("w", encoding="utf-8")

    def log(self, step, **metrics):
        self._f.write(json.dumps({"step": step, **metrics}) + "\n")
        self._f.flush()

    def close(self):
        self._f.close()

tmp = tempfile.mkdtemp(prefix="metrics_")
rec = MetricsRecorder(tmp)
for step, loss in enumerate([1.204, 0.841, 0.633, 0.512], start=1):
    rec.log(step, train_loss=loss, lr=1e-4 * (0.5 ** step))
rec.close()

lines = rec.path.read_text(encoding="utf-8").splitlines()
print(f"wrote {len(lines)} records -> {rec.path.name}")
print(lines[-1])
print("keys:", sorted(json.loads(lines[0]).keys()))
```

**Output:**
```text
wrote 4 records -> metrics.jsonl
{"step": 4, "train_loss": 0.512, "lr": 6.25e-06}
keys: ['lr', 'step', 'train_loss']
```

### Weights & Biases Integration
`wandb` needs an account and API key (`wandb login`), so it is a reference here ([Weights & Biases Documentation](https://docs.wandb.ai/)):

```text
# uv pip install wandb  &&  wandb login
import wandb

wandb.init(project="Minder Academy", entity="your-org", config={
    "model": "Qwen3-8B", "learning_rate": 1e-4, "batch_size": 32, "epochs": 3,
})
for step, batch in enumerate(dataloader):
    loss = train_step(batch)
    wandb.log({"train/loss": loss.item(),
               "train/lr": optimizer.param_groups[0]["lr"],
               "train/epoch": step // steps_per_epoch})
wandb.save("./checkpoints/model.pth")   # uploads an artifact; resuming a run
                                        # still needs Trainer/wandb checkpoints
```

### TensorBoard
PyTorch's `SummaryWriter` needs the `tensorboard` package installed even to write event files (it is not installed in this environment); the viewer is a separate process ([torch.utils.tensorboard - PyTorch docs](https://docs.pytorch.org/docs/2.14/tensorboard.html)):

```text
# uv pip install tensorboard     (torch.utils.tensorboard writes event files)
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter("./logs")
writer.add_scalar("Loss/train", loss.item(), global_step)
writer.add_scalar("Accuracy/train", accuracy, global_step)
for name, param in model.named_parameters():
    writer.add_histogram(f"Parameters/{name}", param, global_step)
    writer.add_histogram(f"Gradients/{name}", param.grad, global_step)
writer.close()
# view: tensorboard --logdir=./logs --port 6006
```

Rule of thumb: W&B for team-wide experiment comparison, TensorBoard for a no-account local run.

## Performance Optimization

### Mixed Precision Training
Mixed precision runs forward/backward in float16 (tensor-core friendly) while weights and the optimizer update stay float32; `GradScaler` prevents silent underflow of small gradients. The legacy spellings `torch.cuda.amp.autocast` / `torch.cuda.amp.GradScaler` are deprecated — use `torch.amp`:

```python
"""
Mixed precision: fp16 forward/backward, fp32 master weights and updates.
GradScaler rescales the loss so small gradients survive fp16 casting.
"""
# torch.cuda.amp.autocast/GradScaler are the deprecated spellings.
import torch
import torch.nn as nn

torch.manual_seed(0)
device = "cuda" if torch.cuda.is_available() else "cpu"
scaler = torch.amp.GradScaler(device, enabled=device == "cuda")
model = nn.Sequential(nn.Linear(256, 1024), nn.GELU(),
                      nn.Linear(1024, 256)).to(device)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()
data, target = torch.randn(64, 256, device=device), torch.randn(64, 256, device=device)

for step in range(3):
    opt.zero_grad()
    with torch.amp.autocast(device_type=device, enabled=device == "cuda"):
        out = model(data)
        loss = loss_fn(out, target)
    scaler.scale(loss).backward()
    scaler.step(opt)
    scaler.update()
    print(f"step {step}: loss {loss.item():.4f} | fwd dtype {out.dtype} | scale {scaler.get_scale()}")
```

**Output:**
```text
step 0: loss 1.0438 | fwd dtype torch.float16 | scale 65536.0
step 1: loss 0.9417 | fwd dtype torch.float16 | scale 65536.0
step 2: loss 0.8487 | fwd dtype torch.float16 | scale 65536.0
```

The forward output is float16 inside the autocast block; the scaler starts at 65536 and stays there because no gradients overflowed.

### Gradient Accumulation
Gradient accumulation simulates a large batch on a small GPU: scale each micro-batch loss by `1/accumulation_steps` (keeping the mean-of-means correct) and step once per window. The accumulated gradients must match a single full batch up to float32 rounding — verified below with a relative bound, the honest way to compare (see 2302's batching measurement for why bare `allclose` fails at larger magnitudes):

```python
"""
Gradient accumulation: micro-batches of size B/m with losses scaled by
1/m sum to the gradient of one B-sample batch. Verify against a full
batch with a relative bound - float32 rounding, not a bug.
"""
import torch
import torch.nn as nn

torch.manual_seed(0)
model = nn.Linear(64, 16)
full_data = torch.randn(32, 64)
full_target = torch.randn(32, 16)
loss_fn = nn.MSELoss()
opt = torch.optim.SGD(model.parameters(), lr=0.0)   # compare gradients only

opt.zero_grad()                                     # one 32-sample batch
loss_fn(model(full_data), full_target).backward()
ref = {n: p.grad.clone() for n, p in model.named_parameters()}

micro = 4                                           # 4 micro-batches of 8
opt.zero_grad()
for i in range(micro):
    sl = slice(i * 8, (i + 1) * 8)
    (loss_fn(model(full_data[sl]), full_target[sl]) / micro).backward()

max_diff = max((ref[n] - p.grad).abs().max().item()
               for n, p in model.named_parameters())
scale = max(ref[n].abs().max().item()
            for n, p in model.named_parameters())
print(f"4 micro-batches of 8 vs one batch of 32: max grad diff {max_diff:.2e}")
print(f"gradient scale {scale:.3f} -> equal to rounding: {max_diff < 0.01 * scale}")
```

**Output:**
```text
4 micro-batches of 8 vs one batch of 32: max grad diff 1.49e-08
gradient scale 0.083 -> equal to rounding: True
```

## Expected Performance

Numbers below are **planning targets**, not measurements of this lesson's environment. The VRAM column is derived from rules (bf16 + AdamW ≈ 16 B/param, NF4 base ≈ 0.5 B/param plus adapters and activations); throughput depends on sequence length, quantization, and kernel versions — benchmark your own stack (see the Experiment link at the bottom).

### 11GB-class GPU Planning Targets
```text
Task (7B model, 11 GB-class GPU)   | VRAM (rule-derived) | Feasible?
-----------------------------------|---------------------|----------------------------
QLoRA fine-tune (bs 2, 4-bit base) | ~7-9 GB             | yes
LoRA fine-tune (bf16 base, bs 1)   | ~16+ GB             | no - 2 GPUs or ZeRO offload
Full fine-tune (bf16 + AdamW)      | ~112 GB             | no - sharding territory
```

The full fine-tune row is the point of this whole lesson: a 7B model with optimizer states does not fit on an 11 GB card at any batch size, which is why the FSDP/ZeRO sections exist. QLoRA fits precisely because the frozen base shrinks ~4x and only adapters train.

### Scaling Efficiency
```text
Configuration | Target speedup | Implied serial fraction
1x 11GB GPU   | 1.0x           | -
2x 11GB GPU   | 1.7x           | ~0.18
4x 11GB GPU   | 3.0x           | ~0.11
```

The targets are representative for DDP over a 10 GbE-class cluster; the serial-fraction column comes from the Amdahl calculator above. Fit your own two-GPU data point first, then trust its prediction for the next size up.

---

## Summary

Distributed training in a homelab starts honest: single-GPU constraints first, with every runnable block executing on one machine, and the K3s and Ray scale-out paths marked clearly as reference sketches. This lesson walked the strategies that fit real hardware, the fine-tuning workflows layered on them, Ray orchestration when hardware allows, and the monitoring that makes multi-node runs debuggable. The expected-performance section sets the bar: measure your own cluster, because the numbers only mean something on the silicon you actually own.

## References

### Related Minder Academy Documents

- [5301: Knowledge Distillation - Training Small Models Using Big Model Outputs](5301-Knowledge-Distillation.md)
- [5303: Federated Learning](5303-Federated-Learning.md)

### External References

- [DeepSpeed - Getting Started](https://www.deepspeed.ai/getting-started/)
- [Ray Train Documentation](https://docs.ray.io/en/latest/train/train.html)
- [Weights & Biases Documentation](https://docs.wandb.ai/)
- [torch.utils.tensorboard - PyTorch docs](https://docs.pytorch.org/docs/2.14/tensorboard.html)
- [PEFT Documentation](https://huggingface.co/docs/peft/index)

---

## Next Steps

- Next Lesson: **[5303: Federated Learning](./5303-Federated-Learning.md)**
- Practical: **[LAB-006: Train a Model From Scratch](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md)**
- Assessment: **[5300: Synthetic Data & Advanced Training - Quiz](./assessment/QUIZ.md)**

**Related:** [1204: Multi-GPU Setup](../../phase1-infra/1200-virtualization/1204-Multi-GPU-Setup.md) — the hardware half of this lesson: multiple GPUs in one box, driver and container setup; [1301: K3s Master-Worker Architecture](../../phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md) — the cluster layer the K3s Job/PyTorchJob manifests in this lesson land on; [5101: LoRA Logic](../5100-peft/5101-LoRA-Logic.md) — the adapter math behind the LoRA half of the QLoRA recipe; [5102: QLoRA Pipelines](../5100-peft/5102-QLoRA-Pipelines.md) — the full quantized fine-tuning pipeline this lesson distributes; [LAB-003: LoRA Fine-Tuning](../../../learning-resources/labs/LAB-003-LoRA-FineTuning.md) — run a real LoRA fine-tune end to end

**Experiment:** [EXP_5302: Distributed Training Experiments](../../../../experiments/EXP_5302_DISTRIBUTED.md) — benchmark the DDP smoke-test path and the accumulation/precision blocks from this lesson on real hardware, and record your own speedup/serial-fraction table (nearest-relevant — the lesson's cluster sections need multi-node hardware)
