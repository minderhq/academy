---
Document ID: 1204
Title: "1204: Multi-GPU Setup"
Phase: 1
Module: 1200
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'virtualization', 'proxmox', 'gpu']
---

# 1204: Multi-GPU Setup

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Starting Point: A Single GPU](#starting-point-a-single-gpu)
- [Multi-GPU Scenarios](#multi-gpu-scenarios)
- [PyTorch Multi-GPU Setup](#pytorch-multi-gpu-setup)
- [Model Parallelism (Large Models)](#model-parallelism-large-models)
- [Inference with Multi-GPU](#inference-with-multi-gpu)
- [Fine-Tuning with Multi-GPU](#fine-tuning-with-multi-gpu)
- [Multi-GPU Benchmarks (Expected)](#multi-gpu-benchmarks-expected)
- [Monitoring Multi-GPU](#monitoring-multi-gpu)
- [Troubleshooting](#troubleshooting)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Read the VRAM budget of a single 11GB-class card and decide when a workload has outgrown it
- Classify the multi-GPU topologies (matched cards, mixed VRAM, eGPU) and what each means for sharding
- Launch DataParallel and torchrun-based DistributedDataParallel training and pick the right one per workload
- Shard a large model across GPUs with manual layer placement and Accelerate's infer_auto_device_map
- Serve a sharded model through vLLM tensor parallelism, Ollama's automatic layer split, and TGI num-shard
- Tune multi-GPU fine-tuning with DeepSpeed ZeRO stage 2 and QLoRA device_map sharding, and diagnose NCCL peer failures

---

## Abstract
Scaling GPU workloads from a single card to multi-GPU serving and training: device selection, data and model parallelism in PyTorch, multi-GPU inference engines (vLLM, TGI, Ollama), fine-tuning strategies, and troubleshooting.

## Starting Point: A Single GPU

### Reference Card
```text
GPU:  Any NVIDIA card with 8GB+ VRAM
      (e.g., RTX 3060 12GB, RTX 4060 Ti 16GB, RTX 5060 Ti 16GB)
VRAM: 8-16GB is the practical starting range
Role: Sufficient for 7B models (4-bit quantization), QLoRA fine-tuning,
      and single-stream inference
```

> **External GPU note:** If your host has no free PCIe slot, a GPU in an
> external enclosure is workable - the card appears as a normal PCIe device
> and everything in this document applies. Expect reduced host-to-device
> bandwidth versus a physical slot. See the original build's write-up:
> [1202 - Case Study: RTX 2080 Ti eGPU over Thunderbolt 3](./1202-TB3-UT3G-Passthrough.md#case-study-rtx-2080-ti-egpu-over-thunderbolt-3).

### Single-GPU Limits
```text
One 11GB card:
  - 7B model at 4-bit:  ~4-5 GB weights, fits with context to spare
  - 13B model at 4-bit: ~8 GB weights, tight with KV cache
  - Serving while fine-tuning on the same card: not practical
Once you hit any of these walls, a second GPU (or a bigger one) is the answer.
```

## Multi-GPU Scenarios

### Scenario 1: Single GPU (Baseline)
```yaml
Configuration:
  - GPU 0: 11GB VRAM card (example)
  - 11GB VRAM total
  - Suitable for:
    - 7B models (4-bit quantization)
    - Fine-tuning (QLoRA)
    - Inference (vLLM, Ollama)
```

### Scenario 2: Dual GPU
```yaml
Configuration:
  - GPU 0: 11GB VRAM card
  - GPU 1: 24GB+ VRAM card (RTX 3090/4090; RTX 5090 is 32GB)
  - 35GB+ VRAM total
  - Suitable for:
    - 13B models (4-bit) with long context
    - Parallel fine-tuning
    - Inference + training simultaneously (one card each)
```

### Scenario 3: Multiple Matched GPUs
```text
Configuration:
  - 2-4x identical cards on native PCIe
  - Identical VRAM simplifies tensor parallelism and pipeline stages
  - Note: mismatched cards (different VRAM) work with device_map
    sharding but the smallest card caps each layer placement
  - Prefer native PCIe slots; share the bandwidth budget accordingly
```

## PyTorch Multi-GPU Setup

### Device Selection
```python
import torch

# Check available GPUs
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"CUDA Version: {torch.version.cuda}")
print(f"GPU Count: {torch.cuda.device_count()}")
print(f"Current Device: {torch.cuda.current_device()}")
print(f"Device Name: {torch.cuda.get_device_name(0)}")

# Select device
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Test memory
x = torch.randn(10000, 10000).to(device)
print(f"VRAM Allocated: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
print(f"VRAM Reserved: {torch.cuda.memory_reserved()/1024**3:.2f} GB")
```

### DataParallel (Simple Multi-GPU)
```python
import torch.nn as nn

# Create model
model = MyModel().to(device)

# Wrap in DataParallel
if torch.cuda.device_count() > 1:
    print(f"Using {torch.cuda.device_count()} GPUs")
    model = nn.DataParallel(model)

# Forward pass (automatically splits batch)
output = model(input_data)

# Note: DataParallel has limitations:
# - Not efficient for single GPU (adds overhead)
# - Uneven load balancing
# - Use DistributedDataParallel instead for production
```

### DistributedDataParallel (Recommended)
```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def setup(rank, world_size):
    """Initialize distributed training"""
    # Initialize process group
    dist.init_process_group(
        backend="nccl",  # NVIDIA GPU communication
        rank=rank,
        world_size=world_size
    )

    # Set device for this process
    torch.cuda.set_device(rank)

def cleanup():
    """Cleanup distributed training"""
    dist.destroy_process_group()

def train(rank, world_size, epochs=10):
    """Training function for each process"""
    setup(rank, world_size)

    # Create model and move to GPU
    model = MyModel().to(rank)
    ddp_model = DDP(model, device_ids=[rank])

    # Create optimizer
    optimizer = torch.optim.Adam(ddp_model.parameters())

    # Training loop
    for epoch in range(epochs):
        for batch_idx, (data, target) in enumerate(dataloader):
            # Move data to GPU
            data, target = data.to(rank), target.to(rank)

            # Forward pass
            output = ddp_model(data)
            loss = criterion(output, target)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    cleanup()

# Launch with torchrun (it sets RANK / WORLD_SIZE / MASTER_ADDR /
# MASTER_PORT for every process):
# torchrun --nproc_per_node=2 train.py
# In train(): rank = int(os.environ["RANK"])
#             world_size = int(os.environ["WORLD_SIZE"])
```

## Model Parallelism (Large Models)

### Pipeline Parallelism

Split the model at layer boundaries and place each stage on its own GPU:

```python
import torch.nn as nn

# Split model across GPUs
# GPU 0: First half of model
# GPU 1: Second half of model

class MyModel(nn.Module):
    def __init__(self):
        super().__init__()
        # Split layers across GPUs
        self.layer1 = nn.Linear(4096, 4096).to(0)  # GPU 0
        self.layer2 = nn.Linear(4096, 2048).to(0)  # GPU 0
        self.layer3 = nn.Linear(2048, 1024).to(1)  # GPU 1
        self.layer4 = nn.Linear(1024, 512).to(1)  # GPU 1

    def forward(self, x):
        # Move between GPUs
        x = self.layer1(x)
        x = self.layer2(x)
        x = x.to(1)  # Move to GPU 1
        x = self.layer3(x)
        x = self.layer4(x)
        return x

```

For automatic micro-batch pipelining, the old
`torch.distributed.pipeline.sync.Pipe` API was removed in PyTorch 2.x -
use `torch.distributed.pipelining` (PyTorch 2.4+) or the device_map-based
sharding shown in the next section.

### Layer Sharding (Hugging Face Accelerate)
```python
from accelerate import infer_auto_device_map, dispatch_model

# Auto-assign layers across GPUs. This is NAIVE model parallelism
# (whole layers sharded, no compute overlap) - for true tensor
# parallelism, see the vLLM section below.
max_memory = {0: "10GiB", 1: "22GiB"}
device_map = infer_auto_device_map(
    model,  # your loaded model
    max_memory=max_memory,
    no_split_module_classes=["LlamaDecoderLayer"],
)

# Dispatch model
model = dispatch_model(model, device_map=device_map)

# Example output for a Llama-style model (40 layers) on 2 GPUs:
# {
#     'model.embed_tokens': 0,
#     'model.layers.0': 0,
#     ...
#     'model.layers.19': 0,
#     'model.layers.20': 1,
#     ...
#     'model.layers.39': 1,
#     'model.norm': 1,
#     'lm_head': 1,
# }
```

## Inference with Multi-GPU

### vLLM Multi-GPU
```bash
# True tensor parallelism: each layer's weight matrices are split
# across the cards. `vllm serve` replaces the long-deprecated
# python -m vllm.entrypoints.api_server entrypoint.
# Sizing note: Gemma-3-27B at fp16 needs ~27GB per shard - too big for
# two 11GB cards. The 7B below fits (~8GB per shard):
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --port 8000
```

### Ollama Multi-GPU
```bash
# Ollama splits model layers across ALL detected GPUs automatically
# (no flag needed). To pin it to a single GPU, restrict visibility:
CUDA_VISIBLE_DEVICES=0 ollama serve

# Or set in environment:
export CUDA_VISIBLE_DEVICES=0
```

### Text Generation Inference (TGI)
```bash
# Multi-GPU inference (num-shard splits the weights; the shard must
# fit - 7B fp16 = ~8GB per shard across two 11GB cards, while 13B
# needs ~13GB per shard, i.e. 24GB-class cards):
model=Qwen/Qwen2.5-7B-Instruct

text-generation-launcher \
    --model-id $model \
    --num-shard 2 \
    --port 8080 \
    --trust-remote-code
```

## Fine-Tuning with Multi-GPU

### DeepSpeed ZeRO (Memory Optimization)

DeepSpeed loads a strict-JSON config (`ds_config.json`). The batch math
below balances on 2 GPUs: 2 GPUs x 2 micro-batch x 4 accumulation = 16.

```json
{
    "train_batch_size": 16,
    "train_micro_batch_size_per_gpu": 2,
    "gradient_accumulation_steps": 4,
    "optimizer": {
        "type": "AdamW",
        "params": {
            "lr": 1e-4,
            "betas": [0.9, 0.95],
            "eps": 1e-8
        }
    },
    "scheduler": {
        "type": "WarmupLR",
        "params": {
            "warmup_min_lr": 0,
            "warmup_max_lr": 1e-4,
            "warmup_num_steps": 100
        }
    },
    "fp16": {
        "enabled": true
    },
    "zero_optimization": {
        "stage": 2,
        "allgather_bucket_size": 5e8,
        "reduce_bucket_size": 5e8
    },
    "gradient_clipping": 1.0
}
```

Run it with:

```bash
deepspeed --num_gpus=2 train.py --deepspeed ds_config.json
```

(`"stage": 2` - ZeRO Stage 2: optimizer-state + gradient partitioning.)

### QLoRA Multi-GPU
```python
from transformers import AutoModelForCausalLM, TrainingArguments, Trainer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Load the model sharded across both GPUs. Qwen2.5-7B's top-level
# modules are model.embed_tokens, model.layers.{0..27} (28 decoder
# layers), model.norm and lm_head - device_map="auto" places them by
# the per-card budget (a hand-written map would need all 28 keys):
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    device_map="auto",
    max_memory={0: "9GiB", 1: "9GiB"},
    quantization_config=BitsAndBytesConfig(load_in_4bit=True),
)

# QLoRA
model = prepare_model_for_kbit_training(model)
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)

# Training
training_args = TrainingArguments(
    output_dir="./qlora-checkpoint",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    fp16=True,
    gradient_checkpointing=True,
    ddp_find_unused_parameters=False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
)

trainer.train()
```

## Multi-GPU Benchmarks (Expected)

### Dual 11GB GPUs (example measurements)
```text
Model           | Single GPU | Dual GPU | Speedup |
----------------|------------|----------|---------|
Llama-3.1-8B (4-bit) | 35 t/s | 60 t/s  | 1.7x |
Gemma-3-12B (4-bit) | 18 t/s | 32 t/s  | 1.8x |
Mistral-7B (4-bit)  | 40 t/s | 70 t/s  | 1.75x |
```

### Training Speedup
```text
Batch Size | Single GPU | Dual GPU | Speedup |
-----------|------------|----------|---------|
2          | 100%       | 180%     | 1.8x |
4          | 100%       | 185%     | 1.85x |
8          | OOM        | 190%     | -       |
```

## Monitoring Multi-GPU

### nvidia-smi
```bash
# Watch GPU usage in real-time
watch -n 1 nvidia-smi

# Query specific GPU
nvidia-smi -i 0

# Query memory usage
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free --format=csv
```

### Python Monitoring
```python
import torch
import subprocess

def get_gpu_stats():
    """Get GPU memory stats"""
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,memory.used,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True
    )

    stats = {}
    for line in result.stdout.strip().split("\n"):
        idx, used, total = line.split(", ")
        stats[int(idx)] = {
            "used_gb": float(used) / 1024,
            "total_gb": float(total) / 1024,
            "free_gb": (float(total) - float(used)) / 1024
        }

    return stats

def print_gpu_stats():
    """Print GPU stats"""
    stats = get_gpu_stats()
    for idx, stat in stats.items():
        print(f"GPU {idx}: {stat['used_gb']:.1f}/{stat['total_gb']:.1f} GB ({stat['free_gb']:.1f} GB free)")
```

## Troubleshooting

### Out of Memory (OOM)
```python
# 1. Reduce batch size
#    per_device_train_batch_size=1

# 2. Enable gradient checkpointing
#    gradient_checkpointing=True

# 3. Use 4-bit quantization
#    quantization_config=BitsAndBytesConfig(load_in_4bit=True)

# 4. Clear cache
torch.cuda.empty_cache()

# 5. Use gradient accumulation instead of large batch
#    gradient_accumulation_steps=16
```

### Multi-GPU Communication Issues
```bash
# Check NCCL
NCCL_DEBUG=INFO python train.py

# Set NCCL backend
export NCCL_P2P_DISABLE=1  # Disable P2P (needed when GPUs cannot peer directly,
                           # e.g., across IOMMU groups or on some virtualized hosts)
export NCCL_IB_DISABLE=1   # Disable InfiniBand (no IB hardware present)

# Use gloo backend instead of nccl (slower but more compatible):
# torch.distributed.init_process_group(backend="gloo")
```

---

## Summary

Multi-GPU starts from an honest single card - 8 to 16GB of VRAM is enough for 7B models, QLoRA fine-tuning, and single-stream inference - and this lesson maps the path up from there: device selection, the multi-GPU scenarios that justify more cards, data and model parallelism in PyTorch, multi-GPU inference with vLLM, TGI, and Ollama, fine-tuning strategies, and the expected benchmarks that calibrate expectations. Monitoring and troubleshooting close it: scale when a measured bottleneck says so, not because more cards sound faster.

## References

### Related Minder Academy Documents

- [1201: Proxmox Hypervisor Standard Operating Procedures](1201-Proxmox-Hypervisor-SOP.md)
- [1202: GPU Passthrough (IOMMU/VFIO)](1202-TB3-UT3G-Passthrough.md)
- [1203: NVIDIA Kernel Module Management](1203-Nvidia-Kernel-Module.md)

---

## Next Steps

- Next Module: **[1300: Kubernetes](../1300-kubernetes/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**

- [1202: GPU Passthrough (IOMMU/VFIO)](./1202-TB3-UT3G-Passthrough.md)
- [1203: NVIDIA Kernel Module Management](./1203-Nvidia-Kernel-Module.md)
- [1301: K3s Master-Worker Architecture](../1300-kubernetes/1301-K3s-Master-Worker-Arch.md)
- [2203: CUDA Kernel Programming and GPU Architecture](../../phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Programming.md)
