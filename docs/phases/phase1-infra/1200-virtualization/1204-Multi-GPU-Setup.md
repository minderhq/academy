---
Document ID: 1204
Title: Multi-GPU Setup for RTX 2080 Ti
Phase: 1
Module: 1200
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'virtualization', 'proxmox', 'gpu']
---

# 1204: Multi-GPU Setup for RTX 2080 Ti

## Abstract
Multi-GPU configuration for PROJECT-OMEGA. Single RTX 2080 Ti eGPU via Thunderbolt 3, with future expansion considerations.

## Current Hardware

### RTX 2080 Ti Specifications
```
GPU: NVIDIA TU102 (Turing Architecture)
VRAM: 11GB GDDR6
CUDA Cores: 4352
Tensor Cores: 544 (FP16)
Memory Bandwidth: 616 GB/s
TDP: 250W
Interface: Thunderbolt 3 (40 Gbps)
```

### Thunderbolt 3 Limitations
```
Bandwidth: 40 Gbps (effective ~32 Gbps)
Latency: ~5-10ms
Impact: 5-10% performance penalty for PCIe x16 equivalent
```

## Multi-GPU Scenarios

### Scenario 1: Single GPU (Current)
```yaml
Configuration:
  - 1x RTX 2080 Ti (eGPU via TB3)
  - 11GB VRAM total
  - Suitable for:
    - 7B models (4-bit quantization)
    - Fine-tuning (QLoRA)
    - Inference (vLLM, Ollama)
```

### Scenario 2: Dual GPU (Future)
```yaml
Configuration:
  - 1x RTX 2080 Ti (eGPU)
  - 1x RTX 3090/4090 (internal PCIe)
  - 22GB+ VRAM total
  - Suitable for:
    - 13B models (4-bit)
    - Parallel fine-tuning
    - Inference + training simultaneously
```

### Scenario 3: Multiple eGPUs
```yaml
Configuration:
  - 2x RTX 2080 Ti (dual TB3 docks)
  - 22GB VRAM total
  - Bottleneck: Single TB3 bus shared
  - Not recommended due to bandwidth limitations
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
import torch.multiprocessing as mp
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

def train(rank, world_size):
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

# Launch with torchrun
# torchrun --nproc_per_node=2 train.py
```

## Model Parallelism (Large Models)

### Pipeline Parallelism
```python
from torch.distributed.pipeline.sync import Pipe

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

# Or use Pipe for automatic pipeline
model = Pipe(
    MyModel(),
    chunks=8,  # Split batch into chunks
)
```

### Tensor Parallelism (HuggingFace Accelerate)
```python
from accelerate import infer_auto_device_map, dispatch_model

# Auto-assign layers across GPUs
device_map = infer_auto_device_map(model)

# Dispatch model
model = dispatch_model(model, device_map=device_map)

# Example device_map for 2 GPUs:
# {
#     'transformer.embed_tokens': 0,
#     'transformer.h.0': 0,
#     'transformer.h.10': 0,
#     'transformer.h.11': 1,
#     'transformer.h.21': 1,
#     'lm_head': 1,
# }
```

## Inference with Multi-GPU

### vLLM Multi-GPU
```bash
# Tensor parallelism across GPUs
python -m vllm.entrypoints.api_server \
    --model meta-llama/Llama-2-13b-hf \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --port 8000
```

### Ollama Multi-GPU (Single GPU Selection)
```bash
# Ollama uses single GPU by default
# To select specific GPU:
CUDA_VISIBLE_DEVICES=0 ollama serve

# Or set in environment:
export CUDA_VISIBLE_DEVICES=0
```

### Text Generation Inference (TGI)
```bash
# Multi-GPU inference
model=meta-llama/Llama-2-13b-hf

text-generation-launcher \
    --model-id $model \
    --num-shard 2 \
    --port 8080 \
    --trust-remote-code
```

## Fine-Tuning with Multi-GPU

### DeepSpeed ZeRO (Memory Optimization)
```python
# DeepSpeed configuration for 2 GPUs
{
    "train_batch_size": 16,
    "train_micro_batch_size_per_gpu": 2,
    "gradient_accumulation_steps": 4,
    "optimizer": {
        "type": "AdamW",
        "params": {
            "lr": 1e-4,
            "betas": [0.9, 0.95],
            "eps": 1e-8,
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
        "stage": 2,  # ZeRO Stage 2: optimizer + gradients partitioning
        "allgather_bucket_size": 5e8,
        "reduce_bucket_size": 5e8,
    },
    "gradient_clipping": 1.0,
}

# Run with:
deepspeed --num_gpus=2 train.py --deepspeed ds_config.json
```

### QLoRA Multi-GPU
```python
from transformers import AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Load model on both GPUs
device_map = {
    "transformer.embed_tokens": 0,
    "transformer.h.0": 0,
    "transformer.h.16": 1,
    "transformer.h.31": 1,
    "lm_head": 1,
}

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-13b-hf",
    device_map=device_map,
    load_in_4bit=True,
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

### RTX 2080 Ti + RTX 2080 Ti (Dual)
```
Model           | Single GPU | Dual GPU | Speedup |
----------------|------------|----------|---------|
Llama-2-7B (4-bit) | 35 t/s | 60 t/s  | 1.7x |
Llama-2-13B (4-bit) | 18 t/s | 32 t/s  | 1.8x |
Mistral-7B (4-bit)  | 40 t/s | 70 t/s  | 1.75x |
```

### Training Speedup
```
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
per_device_train_batch_size=1

# 2. Enable gradient checkpointing
gradient_checkpointing=True

# 3. Use 4-bit quantization
load_in_4bit=True

# 4. Clear cache
torch.cuda.empty_cache()

# 5. Use gradient accumulation instead of large batch
gradient_accumulation_steps=16
```

### Multi-GPU Communication Issues
```bash
# Check NCCL
NCCL_DEBUG=INFO python train.py

# Set NCCL backend
export NCCL_P2P_DISABLE=1  # Disable P2P for eGPU
export NCCL_IB_DISABLE=1   # Disable InfiniBand

# Use gloo backend instead of nccl (slower but more compatible)
torch.distributed.init_process_group(backend="gloo", ...)
```

---

## Next Steps

- Next Module: **[1300: Kubernetes](../1300-kubernetes/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [1202: TB3-UT3G Passthrough](./1202-TB3-UT3G-Passthrough.md)
- [1203: NVIDIA Kernel Module](./1203-Nvidia-Kernel-Module.md)
- [1301: K3s Architecture](../1300-kubernetes/1301-K3s-Master-Worker-Arch.md)
- [2203: CUDA Kernel](../../phase2-foundations/2200-Framework-Engineering/2203-CUDA-Kernel-Syb-Level.md)
