---
Document ID: QUICK-REF-VOLUME-2
Title: "Volume 2: AI/ML Foundations - Quick Reference"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Intermediate
---

# Volume 2: AI/ML Foundations - Quick Reference

**The Mathematics of Intelligence** - Essential tensors, gradients, and CUDA

---

## 🧮 Tensor Operations

### Tensor Dimensions
```python
import torch

# Scalar (0D)
x = torch.tensor(5.0)
# Shape: torch.Size([])

# Vector (1D)
x = torch.tensor([1, 2, 3, 4])
# Shape: torch.Size([4])

# Matrix (2D)
x = torch.randn(3, 4)
# Shape: torch.Size([3, 4])

# Tensor (3D)
x = torch.randn(2, 3, 4)
# Shape: torch.Size([2, 3, 4]) - (batch, seq, hidden)

# 4D Tensor (batch, channels, height, width)
x = torch.randn(8, 3, 224, 224)
```

### Einstein Summation (einsum)
```python
# Matrix multiplication: 'ij,jk->ik'
A = torch.randn(3, 4)
B = torch.randn(4, 5)
C = torch.einsum('ij,jk->ik', A, B)
# Result: (3, 5)

# Batch matmul: 'bij,bjk->bik'
A = torch.randn(10, 3, 4)
B = torch.randn(10, 4, 5)
C = torch.einsum('bij,bjk->bik', A, B)
# Result: (10, 3, 5)

# Dot product: 'i,i->'
a = torch.randn(100)
b = torch.randn(100)
dot = torch.einsum('i,i->', a, b)
# Result: scalar

# Transpose: 'ij->ji'
A = torch.randn(3, 4)
AT = torch.einsum('ij->ji', A)
# Result: (4, 3)

# Sum: 'ij->'
A = torch.randn(3, 4)
total = torch.einsum('ij->', A)
# Result: scalar sum

# Outer product: 'i,j->ij'
a = torch.randn(3)
b = torch.randn(4)
outer = torch.einsum('i,j->ij', a, b)
# Result: (3, 4)
```

### Broadcasting
```python
# (3, 1) + (1, 4) = (3, 4)
A = torch.randn(3, 1)
B = torch.randn(1, 4)
C = A + B
# Broadcasting: Right-align dimensions, expand from size 1

# (3, 4) + (4,) = (3, 4)
A = torch.randn(3, 4)
b = torch.randn(4)
C = A + b
# b is broadcast to (1, 4) then to (3, 4)

# (batch, seq, hidden) + (hidden,)
A = torch.randn(10, 100, 768)
bias = torch.randn(768)
C = A + bias
# Result: (10, 100, 768) - bias added to each position
```

---

## 🔄 Backpropagation

### Chain Rule
```text
If y = f(x) and L = g(y)
Then dL/dx = dL/dy × dy/dx

Example:
y = x²
L = sin(y)

dy/dx = 2x
dL/dy = cos(y)
dL/dx = cos(y) × 2x = cos(x²) × 2x
```

### Gradient Computation
```python
import torch

# Enable gradient tracking
x = torch.randn(3, requires_grad=True)

# Forward pass
y = x * 2
z = y.mean()

# Backward pass
z.backward()

# Gradients
print(x.grad)  # dz/dx = 1/3 * 2 = 2/3 for each element
```

### Autograd from Scratch
```python
class Tensor:
    """Simple autograd implementation"""
    def __init__(self, data, requires_grad=False):
        self.data = data
        self.requires_grad = requires_grad
        self.grad = None
        self._backward = lambda: None
        self._ctx = None

    def backward(self, grad=None):
        if grad is None:
            grad = np.ones_like(self.data)

        self.grad = grad
        self._backward(grad)

    def __add__(self, other):
        out = Tensor(self.data + other.data, requires_grad=True)

        def _backward(grad):
            if self.requires_grad:
                self.grad = grad if self.grad is None else self.grad + grad
            if other.requires_grad:
                other.grad = grad if other.grad is None else other.grad + grad

        out._backward = _backward
        return out
```

---

## 🔥 PyTorch Optimization

### Gradient Checkpointing
```python
from torch.utils.checkpoint import checkpoint

def custom_forward(x, model):
    return model(x)

# Use checkpointing to save memory
# Computes forward without storing intermediate activations
# Recomputes during backward pass
output = checkpoint(custom_forward, input_tensor, model)

# Memory savings: ~50-60%
# Time cost: ~20-30% slower
```

### Mixed Precision Training
```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()

    # Forward in FP16
    with autocast():
        output = model(batch)
        loss = criterion(output, target)

    # Scale gradients and backward
    scaler.scale(loss).backward()

    # Unscale and step
    scaler.step(optimizer)
    scaler.update()
```

### Model Compilation (PyTorch 2.0+)
```python
# Compile model for faster execution
model = torch.compile(
    model,
    mode="max-autotune",  # or "default", "reduce-overhead"
    fullgraph=True,  # Capture entire graph
)

# Speedup: 30-50% typical
# Limitations: Must be deterministic, no dynamic shapes
```

---

## 📊 CUDA Programming

### Basic CUDA Kernel (Python)
```python
import torch
import triton
import triton.language as tl

@triton.jit
def matmul_kernel(
    X_ptr, Y_ptr, Z_ptr,
    M, N, K,
    stride_xm, stride_xk,
    stride_yk, stride_yn,
    stride_zm, stride_zn,
    BLOCK_SIZE: tl.constexpr,
):
    # Matrix multiplication kernel
    pid_m = tl.program_id(0)
    pid_n = tl.program_id(1)

    # Block pointers
    X_block = tl.make_block_ptr(
        X_ptr, (M, K), (stride_xm, stride_xk),
        (pid_m, 0), (BLOCK_SIZE, BLOCK_SIZE), (1, 0)
    )
    Y_block = tl.make_block_ptr(
        Y_ptr, (K, N), (stride_yk, stride_yn),
        (0, pid_n), (BLOCK_SIZE, BLOCK_SIZE), (0, 1)
    )
    Z_block = tl.make_block_ptr(
        Z_ptr, (M, N), (stride_zm, stride_zn),
        (pid_m, pid_n), (BLOCK_SIZE, BLOCK_SIZE), (1, 1)
    )

    # Accumulate
    acc = tl.zeros([BLOCK_SIZE, BLOCK_SIZE], dtype=tl.float32)
    for k in range(K, step=BLOCK_SIZE):
        x = tl.load(X_block)
        y = tl.load(Y_block)
        acc += tl.dot(x, y)
        X_block = tl.advance(X_block, (0, BLOCK_SIZE))
        Y_block = tl.advance(Y_block, (BLOCK_SIZE, 0))

    # Store result
    tl.store(Z_block, acc.to(tl.float16))
```

### Memory Hierarchy
```text
Fastest
┌────────────────────────────────────┐
│ Registers (per thread)             │ ~1KB
├────────────────────────────────────┤
│ Shared Memory (per block)          │ ~48KB
├────────────────────────────────────┤
│ L1 Cache (per SM)                  │ ~128KB
├────────────────────────────────────┤
│ L2 Cache (per GPU)                 │ ~40MB
├────────────────────────────────────┤
│ Global Memory (GPU RAM)            │ ~80GB
│ HBM (High Bandwidth Memory)        │ ~2TB/s bandwidth
└────────────────────────────────────┘
Slowest
```

### Optimization Tips
```python
# 1. Memory Coalescing
# Access consecutive memory locations
# Bad: threads[0, 1, 2, ...] access addresses[0, 1000, 2000, ...]
# Good: threads[0, 1, 2, ...] access addresses[0, 1, 2, ...]

# 2. Shared Memory
# Store frequently accessed data in shared memory
@triton.jit
def kernel(..., BLOCK_SIZE: tl.constexpr):
    x_shared = tl.shared_memory((BLOCK_SIZE,), dtype=tl.float32)
    # Load from global to shared
    tl.store(x_shared, tl.load(x_ptr))

# 3. Minimize Divergence
# Avoid conditionals within warps
# Bad: if tid < 16: do_something()
# Good: Use vectorized operations
```

---

## 🎓 Pre-training Fundamentals

### Data Pipeline
```python
# Data collection pipeline
datasets = {
    "Common Crawl": "100+ TB web data",
    "C4": "750GB cleaned web data",
    "RedPajama": "1.2T tokens (LLaMA reproduction)",
    "The Pile": "825GB curated diverse data",
    "SlimPajama": "627B tokens (cleaned RedPajama)",
}

# Pipeline stages
Collect → Filter → Deduplicate → Tokenize → Train

# Training curriculum
Stage 1 (30%): High-quality foundations (Wikipedia, Books)
Stage 2 (40%): Diverse web knowledge (C4, StackExchange)
Stage 3 (20%): Instructional data
Stage 4 (10%): Annealing on highest quality
```

### Compute Estimation
```python
def estimate_compute(model_size, tokens, gpu="A100"):
    """
    Estimate training cost

    model_size: Billions of parameters (e.g., 7 for 7B)
    tokens: Number of tokens (e.g., 1_000_000_000_000 for 1T)
    gpu: GPU model (A100, H100)
    """
    # Chinchilla scaling: 20 tokens per parameter
    flops_per_token = 6 * model_size * 1e9

    total_flops = flops_per_token * tokens

    # A100: 312 TFLOPS (FP16), H100: 989 TFLOPS
    if gpu == "A100":
        tflops = 312
        hourly_cost = 1.5  # USD
    elif gpu == "H100":
        tflops = 989
        hourly_cost = 3.0

    # Training time (hours)
    # Account for 50% MFU (Model FLOPs Utilization)
    hours = total_flops / (tflops * 1e12 * 0.5 * 3600)

    return {
        "hours": hours,
        "days": hours / 24,
        "cost_usd": hours * hourly_cost,
    }

# Example: 7B model, 1T tokens, 8x A100
estimate_compute(7, 1_000_000_000_000)
# Returns: ~500 hours (21 days), ~$12,000 with 8 GPUs
```

### Tokenization
```python
# BPE Tokenization
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer

def train_bpe_tokenizer(dataset_path, vocab_size=50000):
    """Train BPE tokenizer from scratch"""
    tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
    trainer = BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"],
    )

    # Train on dataset
    tokenizer.train(files=[dataset_path], trainer=trainer)
    tokenizer.save("tokenizer.json")

    return tokenizer

# Common tokenizers
TOKENIZERS = {
    "GPT-2/3": "BPE, 50k vocab, byte-level",
    "LLaMA": "BPE, 32k vocab, sentencepiece",
    "Mistral": "BPE, 32k vocab, sentencepiece",
    "Gemma": "BPE, 256k vocab, large vocab for multilingual",
}
```

---

## 📈 Evaluation Metrics

### Perplexity
```python
def calculate_perplexity(model, dataloader, device):
    """Calculate perplexity on validation set"""
    model.eval()
    total_loss = 0
    total_tokens = 0

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=input_ids,
            )

            total_loss += outputs.loss.item() * input_ids.size(0)
            total_tokens += attention_mask.sum().item()

    avg_loss = total_loss / total_tokens
    perplexity = torch.exp(torch.tensor(avg_loss))

    return perplexity.item()

# Interpretation
# Lower is better
# PPL = 10: Model is very confident
# PPL = 100: Moderate uncertainty
# PPL = 1000: High uncertainty
```

### MMLU (Massive Multitask Language Understanding)
```python
def evaluate_mmlu(model, tokenizer, subjects="all"):
    """
    Evaluate on MMLU benchmark

    Subjects: 57 categories including math, history, law, etc.
    Format: Multiple choice (A, B, C, D)
    """
    # Load MMLU dataset
    from datasets import load_dataset

    mmlu = load_dataset("cais/mmlu", "all")

    correct = 0
    total = 0

    for example in mmlu["test"]:
        # Format prompt with question and choices
        prompt = format_mmlu_prompt(example)

        # Generate answer
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=1)

        # Extract prediction (A, B, C, D)
        prediction = extract_choice(tokenizer.decode(outputs[0]))

        # Compare with ground truth
        if prediction == example["answer"]:
            correct += 1
        total += 1

    accuracy = correct / total
    return accuracy

# State-of-the-art MMLU scores
# GPT-4: 86.4%
# Claude 3: 86.8%
# LLaMA-3-70B: 82.0%
# Mistral-8x7B: 70.6%
```

---

## 🔧 Quick Commands

### Tensor Operations
```python
# Common operations
torch.matmul(A, B)           # Matrix multiplication
torch.bmm(batch_A, batch_B)  # Batch matmul
torch.einsum('ij,jk->ik', A, B)  # Einstein summation
torch.cat([a, b], dim=0)     # Concatenate
torch.stack([a, b], dim=0)   # Stack

# Reductions
x.sum(dim=1)                 # Sum along dimension
x.mean(dim=1)                # Mean along dimension
x.max(dim=1)                 # Max along dimension
x.argmax(dim=1)              # Index of max
```

### Gradient Management
```python
# Enable/disable gradients
x.requires_grad = True
with torch.no_grad():        # Disable temporarily
with torch.set_grad_enabled(phase == 'train'):  # Conditional

# Gradient clipping
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

# Check for gradients
for name, param in model.named_parameters():
    if param.grad is None:
        print(f"{name}: No gradient!")
```

---

## 🎯 Common Pitfalls

### Broadcasting Errors
```python
# Wrong: (3,) + (3,) - shape mismatch
# Right: (3, 1) + (1, 3) = (3, 3)

# Solution: Use .unsqueeze() or .view()
a = torch.randn(3)
b = torch.randn(3)
result = a.unsqueeze(1) + b.unsqueeze(0)  # (3, 1) + (1, 3) = (3, 3)
```

### In-place Operations
```python
# Wrong: Breaks computation graph
x = x + 1  # Creates new tensor
x += 1     # In-place, breaks autograd!

# Right: Use out= or avoid in-place
x = x.add(1)
```

### CUDA Out of Memory
```python
# Solutions:
# 1. Reduce batch size
# 2. Use gradient checkpointing
# 3. Use mixed precision
# 4. Clear cache
torch.cuda.empty_cache()

# 5. Use gradient accumulation
accumulation_steps = 4
for i, batch in enumerate(dataloader):
    loss = model(batch) / accumulation_steps
    loss.backward()
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

---

## 📦 Volume 2 Checklist

- [ ] Understand tensor shapes and dimensions
- [ ] Master einsum notation
- [ ] Implement backpropagation from scratch
- [ ] Optimize PyTorch code with mixed precision
- [ ] Use gradient checkpointing
- [ ] Write basic CUDA kernel
- [ ] Understand pre-training pipeline
- [ ] Train small model from scratch
- [ ] Evaluate with perplexity and MMLU

---

## 🚀 Next Steps

1. Complete LAB-006: Train Model from Scratch
2. Read 2402-Large-Scale-Training.md
3. Read 2403-Evaluation-Frameworks.md
4. Practice with EXP experiments

---

**Volume:** 2 - AI/ML Foundations
**Estimated Time:** 50-55 hours
