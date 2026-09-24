---
Document ID: 5302
Title: Distributed Training Orchestration
Phase: 5
Module: 5300
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'synthetic-data', 'distillation', 'federated']
---

# 5302: Distributed Training Orchestration

## Abstract
Distributed training strategies for Homelab. single-GPU constraints with optional Kubernetes orchestration.

## Distributed Training Strategies

### 1. Data Parallelism (DP)
```python
"""
Data Parallelism: Each GPU has full model copy, processes different data batches
Best for: Large batch training, when model fits in single GPU
"""
import torch
import torch.nn as nn
from torch.nn.parallel import DataParallel

# DataParallel (simple, limited scaling)
model = MyLargeModel().cuda()
if torch.cuda.device_count() > 1:
    model = DataParallel(model)

# Training
outputs = model(inputs)  # Automatically splits batch across GPUs
loss = criterion(outputs, labels)
loss.backward()  # Gradients averaged across GPUs
```

### 2. Distributed Data Parallel (DDP)
```python
"""
DDP: Each GPU has its own process, more efficient than DP
Best for: Production training, better scaling
"""
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

def setup_ddp(rank, world_size):
    """Initialize DDP"""
    # Use environment variables set by torchrun
    dist.init_process_group(backend="nccl")
    torch.cuda.set_device(rank)

def cleanup_ddp():
    """Cleanup DDP"""
    dist.destroy_process_group()

class Trainer:
    def __init__(self, rank, world_size):
        self.rank = rank
        self.world_size = world_size
        setup_ddp(rank, world_size)

        # Create model on this GPU
        self.model = MyModel().to(rank)
        self.model = DDP(self.model, device_ids=[rank])

        # Distributed sampler
        self.train_sampler = DistributedSampler(
            train_dataset,
            num_replicas=world_size,
            rank=rank,
            shuffle=True
        )

        self.train_loader = DataLoader(
            train_dataset,
            batch_size=32,
            sampler=self.train_sampler
        )

    def train(self):
        optimizer = torch.optim.Adam(self.model.parameters())

        for epoch in range(epochs):
            # Set epoch for shuffling
            self.train_sampler.set_epoch(epoch)

            for batch_idx, (data, target) in enumerate(self.train_loader):
                data, target = data.to(self.rank), target.to(self.rank)

                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()

                if batch_idx % 100 == 0 and self.rank == 0:
                    print(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item()}")

        cleanup_ddp()

# Launch with:
# torchrun --nproc_per_node=2 train.py
```

### 3. Fully Sharded Data Parallel (FSDP)
```python
"""
FSDP: Shards model parameters, gradients, and optimizer states across GPUs
Best for: Very large models that don't fit in single GPU
"""
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.wrap import size_based_auto_wrap_policy

def setup_fsdp():
    """Setup FSDP for large model training"""
    model = MyVeryLargeModel()

    # Auto-wrap layers > 100M parameters
    auto_wrap_policy = size_based_auto_wrap_policy(
        min_num_params=100_000_000
    )

    # Wrap model with FSDP
    fsdp_model = FSDP(
        model,
        sharding_strategy="FULL_SHARD",  # Shard everything
        auto_wrap_policy=auto_wrap_policy,
        cpu_offload=CPUOffload(offload_params=True),  # Offload to CPU if needed
    )

    return fsdp_model

# Training with FSDP
model = setup_fsdp()
optimizer = torch.optim.Adam(model.parameters())

# Training loop same as single GPU
for data, target in dataloader:
    output = model(data)
    loss = criterion(output, target)
    loss.backward()
    optimizer.step()
```

### 4. DeepSpeed ZeRO
```python
"""
DeepSpeed ZeRO: Memory-optimized distributed training
Stages:
- Stage 1: Optimizer state partitioning
- Stage 2: + Gradient partitioning
- Stage 3: + Parameter partitioning
"""
import deepspeed

# DeepSpeed config
ds_config = {
    "train_batch_size": 32,
    "train_micro_batch_size_per_gpu": 4,
    "gradient_accumulation_steps": 2,

    "optimizer": {
        "type": "AdamW",
        "params": {
            "lr": 1e-4,
            "betas": [0.9, 0.95],
            "eps": 1e-8,
        }
    },

    "scheduler": {
        "type": "WarmupDecayLR",
        "params": {
            "total_num_steps": 1000,
            "warmup_min_lr": 0,
            "warmup_max_lr": 1e-4,
            "warmup_num_steps": 100
        }
    },

    "fp16": {
        "enabled": True,
        "loss_scale": 0,
        "initial_scale_power": 16,
        "loss_scale_window": 1000,
        "hysteresis": 2,
        "min_loss_scale": 1
    },

    "zero_optimization": {
        "stage": 2,  # ZeRO Stage 2
        "allgather_bucket_size": 5e8,
        "reduce_bucket_size": 5e8,
        "overlap_comm": True,
        "contiguous_gradients": True,
    },

    "gradient_clipping": 1.0,
    "steps_per_print": 100,
}

# Initialize
model = MyModel()
model_engine, optimizer, _, _ = deepspeed.initialize(
    model=model,
    config=ds_config
)

# Training loop
for batch in dataloader:
    loss = model_engine(batch)
    model_engine.backward(loss)
    model_engine.step()
```

## K3s Cluster Training

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
            nvidia.com/gpu: "1"  # Request 11GB-class GPU
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
```python
"""
QLoRA + DDP for efficient fine-tuning
Combines 4-bit quantization with distributed training
"""
import torch
from transformers import (
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import BitsAndBytesConfig

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",  # Automatically distribute
)

# Prepare for k-bit training
model = prepare_model_for_kbit_training(model)

# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Training arguments for DDP
training_args = TrainingArguments(
    output_dir="./qlora-checkpoint",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=8,
    learning_rate=1e-4,
    fp16=True,
    gradient_checkpointing=True,
    # DDP settings
    local_rank=-1,  # Set by torchrun
    ddp_find_unused_parameters=False,
    # Logging
    logging_steps=10,
    save_steps=100,
    save_total_limit=3,
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    ),
)

# Train
trainer.train()
```

## Orchestration with Ray

### Ray Train Integration
```python
"""
Ray Train: Distributed training orchestration
Handles resource allocation, scaling, fault tolerance
"""
import ray
from ray.train.torch import TorchTrainer
from ray.train import ScalingConfig

def train_func(config):
    """Training function for each worker"""
    import torch
    from torch.nn.parallel import DistributedDataParallel as DDP

    # Setup distributed training
    from ray.train.torch import get_device
    device = get_device()

    # Create model
    model = MyModel().to(device)
    model = DDP(model, device_ids=[device.index] if device.type == "cuda" else None)

    # Training loop
    optimizer = torch.optim.Adam(model.parameters())
    for epoch in range(config["epochs"]):
        for batch in dataloader:
            output = model(batch)
            loss = compute_loss(output)
            loss.backward()
            optimizer.step()

# Ray trainer
trainer = TorchTrainer(
    train_func,
    train_loop_config={"epochs": 10},
    scaling_config=ScalingConfig(
        num_workers=2,  # 2 GPUs
        use_gpu=True,
        resources_per_worker={"GPU": 1}
    ),
)

# Run training
result = trainer.fit()
```

## Monitoring and Logging

### Weights & Biases Integration
```python
import wandb

# Initialize wandb
wandb.init(
    project="project-omega",
    entity="your-org",
    config={
        "model": "Llama-2-7b",
        "learning_rate": 1e-4,
        "batch_size": 32,
        "epochs": 3,
    }
)

# Log metrics
wandb.log({
    "train/loss": loss.item(),
    "train/lr": optimizer.param_groups[0]["lr"],
    "train/epoch": epoch,
})

# Log model
wandb.save("./checkpoints/model.pth")
```

### TensorBoard
```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter("./logs")

# Log metrics
writer.add_scalar("Loss/train", loss.item(), global_step)
writer.add_scalar("Accuracy/train", accuracy, global_step)

# Log histograms
for name, param in model.named_parameters():
    writer.add_histogram(f"Parameters/{name}", param, global_step)
    writer.add_histogram(f"Gradients/{name}", param.grad, global_step)

# Launch TensorBoard
# tensorboard --logdir=./logs --port 6006
```

## Performance Optimization

### Mixed Precision Training
```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for data, target in dataloader:
    data, target = data.cuda(), target.cuda()

    optimizer.zero_grad()

    # Automatic mixed precision
    with autocast():
        output = model(data)
        loss = criterion(output, target)

    # Scale gradients
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### Gradient Accumulation
```python
"""
Simulate larger batch size with limited GPU memory
"""
accumulation_steps = 4
target_batch_size = 32
micro_batch_size = 8  # Fits in GPU

optimizer.zero_grad()

for i, (data, target) in enumerate(dataloader):
    output = model(data)
    loss = criterion(output, target)
    loss = loss / accumulation_steps  # Normalize loss
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

## Expected Performance

### 11GB-class GPU Single GPU
```
Task                     | Batch Size | Throughput | VRAM |
-------------------------|------------|------------|------|
Llama-2-7B QLoRA         | 2          | ~500 samples/s | ~8GB |
Llama-2-7B Full Fine-tune| 1          | ~200 samples/s | ~11GB |
Mistral-7B QLoRA         | 2          | ~450 samples/s | ~8GB |
```

### Scaling Efficiency
```
Configuration   | Speedup | Efficiency |
----------------|---------|------------|
1x 11GB GPU  | 1.0x    | 100%       |
2x 11GB GPU  | 1.7x    | 85%        |
4x 11GB GPU  | 3.0x    | 75%        |
```


---

## Next Steps

- Continue with: **[5303: 5303-Federated-Learning.md](./5303-Federated-Learning.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related:**
- [1204: Multi-GPU Setup](../phase1-infra/1204-Multi-GPU-Setup.md)
- [5101: LoRA Logic](./5100-Parameter-Efficient/5101-LoRA-Logic.md)
- [5102: QLoRA Pipelines](./5100-Parameter-Efficient/5102-QLoRA-Pipelines.md)
- [1301: K3s Architecture](../phase1-infra/1300-K3s/1301-K3s-Master-Worker-Arch.md)
