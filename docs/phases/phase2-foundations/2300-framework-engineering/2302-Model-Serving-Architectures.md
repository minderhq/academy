---
Document ID: 2302
Title: "2302: Model Serving Architectures"
Phase: 2
Module: 2300
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'architecture', 'api-design', 'production']
---

# 2302: Model Serving Architectures

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Architecture 1: Request Batching](#architecture-1-request-batching)
- [Architecture 2: Model Parallelism](#architecture-2-model-parallelism)
- [Architecture 3: Load Balancing](#architecture-3-load-balancing)
- [Architecture 4: Caching Strategies](#architecture-4-caching-strategies)
- [Real-World: vLLM Architecture](#real-world-vllm-architecture)
- [Exercise: Build a Serving System](#exercise-build-a-serving-system)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Design a dynamic batching server and reason about the latency/throughput trade-off its timeout and size controls make
- Contrast pipeline parallelism (stage split across devices) with tensor parallelism (weight shards across devices) and know when each applies
- Compute per-GPU optimizer-state memory under the ZeRO stages from the 16-bytes-per-parameter rule
- Implement round-robin, least-connections, and memory-aware load balancing over serving replicas
- Add response, embedding, and KV caching at the layer where each pays off
- Explain how vLLM's PagedAttention and continuous batching turn fragmentation and head-of-line blocking into throughput

---

## Abstract

Serving machine learning models in production requires specialized architectural patterns to maximize throughput, minimize latency, and ensure reliability. This document covers the essential serving architectures used in production ML systems like OpenAI, Anthropic, and enterprise ML platforms.

**What You'll Learn:**
- Request batching for GPU optimization
- Model and data parallelism strategies
- Load balancing algorithms
- Caching strategies for ML inference
- Real-world architectures (vLLM, TGI, Triton)

---

## Architecture 1: Request Batching

### The Problem

A serving loop that handles one request at a time feeds the GPU one tiny
matrix multiplication per call. The block below issues the same 32
predictions twice: once row at a time, once as a single batched matmul.

```python
import torch

torch.manual_seed(0)

# Each row is one "request's" feature vector. Serving rows one at a time
# issues 32 separate matmul calls; one batched matmul issues a single call
# that computes the same result (to float32 rounding).
batch = torch.randn(32, 12288)
w = torch.randn(12288, 128)

calls = 0
serial = torch.empty(32, 128)
for i, row in enumerate(batch):
    serial[i] = row @ w
    calls += 1

batched = batch @ w
diff = (serial - batched).abs().max().item()
scale = batched.abs().max().item()
assert diff < 0.01 * scale              # rounding, far below the value magnitudes
print("row-at-a-time:", calls, "separate matmul calls")
print("all-at-once:   ", 1, "call ->", tuple(batched.shape))
print("max abs diff: %.2e (values reach %.1f - float32 rounding, not a bug)"
      % (diff, scale))
```

**Output:**

```text
row-at-a-time: 32 separate matmul calls
all-at-once:    1 call -> (32, 128)
max abs diff: 6.10e-04 (values reach 420.1 - float32 rounding, not a bug)
```

**Why batching wins:**
- One batched call replaces 32 separate kernel launches - less dispatch overhead
- GPUs are throughput machines: a wide matmul saturates the cores, a thin one idles them
- Batching changes how the math is scheduled, not what it computes - the results
  agree to float32 rounding
- The serial loop pays with high per-request latency and low throughput

### The Solution: Dynamic Batching

```python
import time
import threading
import uuid
import concurrent.futures
from typing import Any
from dataclasses import dataclass


@dataclass
class Request:
    """Represents a single inference request."""
    id: str
    input_data: Any
    priority: int = 0
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class BatchingModelServer:
    """
    Serves models with dynamic request batching.

    Strategies:
    1. Time-based batching: Wait max N ms for batch to form
    2. Size-based batching: Process when batch reaches N requests
    3. Priority batching: Prioritize important requests
    """

    def __init__(
        self,
        model,
        max_batch_size: int = 32,
        timeout_ms: int = 50,
        use_priority: bool = False
    ):
        self.model = model
        self.max_batch_size = max_batch_size
        self.timeout_ms = timeout_ms
        self.use_priority = use_priority

        # Request tracking
        self.pending: list[Request] = []
        self.results: dict[str, Any] = {}
        self.lock = threading.Lock()

        # Statistics
        self.stats = {
            "total_requests": 0,
            "batches_processed": 0,
            "avg_batch_size": 0.0,
            "avg_latency_ms": 0.0,
        }

    def add_request(self, input_data: Any, priority: int = 0) -> str:
        """
        Add a request to the batch queue.

        Returns:
            Request ID for tracking
        """
        request_id = str(uuid.uuid4())
        request = Request(id=request_id, input_data=input_data, priority=priority)

        with self.lock:
            self.pending.append(request)
            self.stats["total_requests"] += 1

            # Check if we should process the batch
            self._check_and_process_batch()

        return request_id

    def get_result(self, request_id: str, timeout: float = 5.0) -> Any:
        """
        Wait for and return request result.

        Args:
            request_id: ID returned by add_request()
            timeout: Max seconds to wait

        Returns:
            Model output

        Raises:
            TimeoutError: If request doesn't complete in time
        """
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                if request_id in self.results:
                    result = self.results.pop(request_id)
                    return result

                # Waiters double as the timeout flusher: batch checks only
                # run inside add_request, so a trailing partial batch would
                # otherwise sit unprocessed forever once submissions stop.
                self._check_and_process_batch()

            time.sleep(0.001)  # Sleep 1ms

        raise TimeoutError(f"Request {request_id} timed out after {timeout}s")

    def _check_and_process_batch(self):
        """
        Check if we should form and process a batch.

        Conditions to process:
        1. Batch is full (max_batch_size reached)
        2. Oldest request exceeded timeout
        """
        if not self.pending:
            return

        # Sort by priority if enabled
        if self.use_priority:
            self.pending.sort(key=lambda r: r.priority, reverse=True)

        # Check if batch is full
        if len(self.pending) >= self.max_batch_size:
            self._process_batch()
            return

        # Check timeout
        oldest = self.pending[0]
        if (time.time() - oldest.timestamp) * 1000 >= self.timeout_ms:
            self._process_batch()
            return

    def _process_batch(self):
        """
        Process current batch of requests.

        Steps:
        1. Collect pending requests
        2. Prepare batch input
        3. Run model inference
        4. Store results
        5. Update statistics
        """
        if not self.pending:
            return

        # Collect requests
        batch_requests = self.pending[:self.max_batch_size]
        self.pending = self.pending[len(batch_requests):]

        # Prepare batch
        batch_input = self._prepare_batch([r.input_data for r in batch_requests])

        # Run inference
        start = time.time()
        batch_output = self.model(batch_input)
        inference_time_ms = (time.time() - start) * 1000

        # Store results
        for request, output in zip(batch_requests, batch_output):
            self.results[request.id] = output

        # Update stats
        self.stats["batches_processed"] += 1
        self.stats["avg_batch_size"] = (
            (self.stats["avg_batch_size"] * (self.stats["batches_processed"] - 1) + len(batch_requests)) /
            self.stats["batches_processed"]
        )
        self.stats["avg_latency_ms"] = (
            (self.stats["avg_latency_ms"] * (self.stats["batches_processed"] - 1) + inference_time_ms) /
            self.stats["batches_processed"]
        )

    def _prepare_batch(self, inputs: list[Any]) -> Any:
        """
        Prepare batch input for model.

        Default: pass the list through unchanged - any model that iterates
        over its batch works with a plain list. Override this for tensor
        models, e.g. torch.stack(inputs).
        """
        return inputs

    def get_stats(self) -> dict[str, Any]:
        """Get server statistics."""
        with self.lock:
            return {
                **self.stats,
                "pending_requests": len(self.pending),
                "cached_results": len(self.results),
            }


# Usage Example
class MockModel:
    """Mock model for demonstration."""

    def __init__(self, batch_time_ms=20):
        self.batch_time_ms = batch_time_ms

    def __call__(self, batch_input):
        # Simulate inference time
        time.sleep(self.batch_time_ms / 1000.0)

        # Return mock outputs
        batch_size = len(batch_input) if hasattr(batch_input, "__len__") else 1
        return [f"output_{i}" for i in range(batch_size)]


if __name__ == "__main__":
    # Create server
    model = MockModel(batch_time_ms=20)
    server = BatchingModelServer(model, max_batch_size=8, timeout_ms=50)

    # Send multiple requests concurrently
    def send_request(i):
        request_id = server.add_request(f"input_{i}")
        result = server.get_result(request_id)
        print(f"Request {i}: {result}")

    # Send 20 requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_request, i) for i in range(20)]
        concurrent.futures.wait(futures)

    # Print stats
    print("\nServer Statistics:")
    for key, value in server.get_stats().items():
        print(f"  {key}: {value}")
```

**Output:**

```text
Request 5: output_5
Request 9: output_1
Request 0: output_0
Request 12: output_6
...16 more Request lines, interleaved...

Server Statistics:
  total_requests: 20
  batches_processed: 3
  avg_batch_size: 6.666666666666667
  avg_latency_ms: 20.30833562215169
  pending_requests: 0
  cached_results: 0
```

Line order varies with thread scheduling - requests resolve as their
batch completes, not in submission order, and each `output_N` label
pairs with the slot the request happened to occupy inside its batch,
so the request-to-output mapping differs from run to run too.
`batches_processed` and `avg_batch_size` are deterministic for this
workload (8 + 8 + 4); `avg_latency_ms` is timing-dependent and floors
near the 20 ms inference time.

### Benefits

| Metric | Without Batching | With Batching | Improvement |
|--------|------------------|---------------|-------------|
| Throughput | 50 req/sec | 400 req/sec | **8x** |
| Latency (p50) | 20ms | 25ms | +5ms |
| Latency (p99) | 20ms | 75ms | +55ms |
| GPU Utilization | 20% | 90% | **3.5x** |

### Trade-offs

**Advantages:**
- Much higher throughput
- Better GPU utilization
- Lower cost per request

**Disadvantages:**
- Increased latency for first request in batch
- More complex implementation
- Need result tracking system

---

## Architecture 2: Model Parallelism

### When to Use Model Parallelism

**Scenario:** Model is too large to fit on single GPU

```text
Model Size: 70B parameters (140GB VRAM required)
Available: 4x A100 (40GB each = 160GB total)

Solution: Distribute model across GPUs
```

### Data Parallel vs Model Parallel

```text
DATA PARALLELISM (same model on multiple GPUs):
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ GPU 0   │  │ GPU 1   │  │ GPU 2   │  │ GPU 3   │
│ Model   │  │ Model   │  │ Model   │  │ Model   │
│ Copy    │  │ Copy    │  │ Copy    │  │ Copy    │
└────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
     │            │            │            │
     └────────────┴────────────┴────────────┘
                    ↓
            Gradient Synchronization
                    ↓
            Update All Identical Models

Use case: Small model, large batch size


MODEL PARALLELISM (model split across GPUs):
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ GPU 0   │──→│ GPU 1   │──→│ GPU 2   │──→│ GPU 3   │
│ Layer   │  │ Layer   │  │ Layer   │  │ Layer   │
│ 1-17    │  │ 18-34   │  │ 35-51   │  │ 52-70   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘

Use case: Large model, limited GPU memory
```

### Implementation: Pipeline Parallelism

A pipeline splits the model into contiguous stages and pins each stage to
one device; activations flow stage to stage. The block below builds such a
pipeline at a scale that runs on any machine, placing stages round-robin
over every device PyTorch can see - one stage per GPU on a 4-GPU server,
all stages co-located on one GPU here.

```python
import torch
import torch.nn as nn

torch.manual_seed(0)


class PipelineStage(nn.Module):
    """A contiguous slice of the model, pinned to one device."""

    def __init__(self, layers, device):
        super().__init__()
        self.layers = nn.Sequential(*layers).to(device)
        self.device = device

    def forward(self, x):
        return self.layers(x.to(self.device))


def build_pipeline(num_stages, blocks_per_stage, d_model):
    """Round-robin the stages over every device PyTorch can see.

    Production scale: a Llama-2-7B-shaped stack is 70 transformer blocks
    at d_model 4096 - roughly 44 GB of parameters alone, spread as one
    stage per GPU. Here: 4 stages x 2 blocks at d_model 64 so the
    mechanics run anywhere.
    """
    n_gpu = torch.cuda.device_count()
    devices = [f"cuda:{i}" for i in range(n_gpu)] or ["cpu"]
    devices = [devices[i % len(devices)] for i in range(num_stages)]
    stages = []
    for s in range(num_stages):
        layers = [
            nn.TransformerEncoderLayer(
                d_model=d_model, nhead=4, dim_feedforward=4 * d_model,
                dropout=0.0, batch_first=True)
            for _ in range(blocks_per_stage)
        ]
        stages.append(PipelineStage(layers, devices[s]))
    return stages


stages = build_pipeline(num_stages=4, blocks_per_stage=2, d_model=64)
total = sum(p.numel() for st in stages for p in st.parameters())
print("stage devices:", [st.device for st in stages])
print("total parameters:", total)

x = torch.randn(8, 16, 64)
for st in stages:
    x = st(x)
print("output shape:", tuple(x.shape))
print("output device:", x.device.type)
```

**Output:**

```text
stage devices: ['cuda:0', 'cuda:0', 'cuda:0', 'cuda:0']
total parameters: 399872
output shape: (8, 16, 64)
output device: cuda
```

On this single-GPU machine all four stages co-locate on `cuda:0`; on a
4-GPU host the same call returns `['cuda:0', 'cuda:1', 'cuda:2', 'cuda:3']`
and each stage owns a GPU. This synchronous version drains the whole
pipeline before the next micro-batch enters - production pipelines keep
every stage busy with in-flight micro-batches instead.

### Implementation: Tensor Parallelism

Tensor parallelism splits ONE layer's weight across devices: each shard
holds a column slice of the output features, computes its partial product,
and the partials concatenate back into the full output. The block below
verifies the sharded math against the equivalent single-device layer.

```python
import torch
import torch.nn as nn

torch.manual_seed(0)


class TensorParallelLinear(nn.Module):
    """y = x @ W + b computed as concat of per-device partial products.

    W is split column-wise: every shard produces its slice of the output
    features, so no single device ever materializes the full weight.
    """

    def __init__(self, in_features, out_features, devices):
        super().__init__()
        assert out_features % len(devices) == 0, "shards must divide out_features"
        self.shard = out_features // len(devices)
        self.devices = devices
        self.weights = nn.ParameterList([
            nn.Parameter(torch.randn(in_features, self.shard, device=d) * 0.02)
            for d in devices])
        self.biases = nn.ParameterList([
            nn.Parameter(torch.zeros(self.shard, device=d))
            for d in devices])

    def forward(self, x):
        host = self.devices[0]
        parts = []
        for i, d in enumerate(self.devices):
            part = x.to(d) @ self.weights[i] + self.biases[i]
            # torch.cat cannot span devices: gather every shard on the host
            parts.append(part.to(host))
        return torch.cat(parts, dim=-1)


# One physical GPU here: two shards co-located on cuda:0 run exactly the
# math a 4-GPU host runs with devices = ["cuda:0", "cuda:1", "cuda:2", "cuda:3"].
n_gpu = torch.cuda.device_count()
n_shards = max(2, min(n_gpu, 4)) if n_gpu else 2
devices = ([f"cuda:{i % n_gpu}" for i in range(n_shards)]
           if n_gpu else ["cpu"] * n_shards)

layer = TensorParallelLinear(64, 96, devices)

# Reference: the equivalent single-device layer, weights concatenated back.
ref_w = torch.cat([p.detach().cpu() for p in layer.weights], dim=1)
ref_b = torch.cat([p.detach().cpu() for p in layer.biases])
x = torch.randn(2, 5, 64)
y = layer(x).cpu()

print("devices:", devices)
print("shard shape:", tuple(layer.weights[0].shape))
diff = (y - (x @ ref_w + ref_b)).abs().max().item()
assert diff < 1e-4                      # sharding agrees to float32 rounding
print("matches single-device math: max diff %.2e (float32 rounding)" % diff)
```

**Output:**

```text
devices: ['cuda:0', 'cuda:0']
shard shape: (64, 48)
matches single-device math: max diff 1.19e-07 (float32 rounding)
```

At production scale the point is memory: a 4096 x 4096 linear layer is
16M parameters on one device - 4M per shard across four GPUs.

### Production Framework: DeepSpeed

[DeepSpeed](https://www.deepspeed.ai/getting-started/) wraps an ordinary
training loop and shards the training state across GPUs (`uv pip install
deepspeed`). The sketch below is the entire integration surface - your
model and dataloader stay untouched:

```text
# Sketch: model and dataloader come from your training script.
import deepspeed

# Initialize DeepSpeed
model_engine, optimizer, _, _ = deepspeed.initialize(
    model=model,
    model_parameters=model.parameters(),
    config={
        "train_batch_size": 32,
        "gradient_accumulation_steps": 4,
        "fp16": {"enabled": True},
        "zero_optimization": {"stage": 3},   # ZeRO Stage 3
    }
)

for batch in dataloader:
    loss = model_engine(batch)      # forward with partitioned parameters
    model_engine.backward(loss)     # gradient sharding across GPUs
    model_engine.step()             # optimizer-state sharding
```

What each ZeRO stage buys is pure arithmetic. fp32 training state costs
16 bytes per parameter (4 weights + 4 grads + 4 Adam m + 4 Adam v); the
stages shard increasing slices of that state across the pool:

```python
def zero_stage_gb(params_billion: float, stage: int, gpus: int) -> float:
    """Per-GPU GB of parameter/grad/optimizer state under ZeRO stages 0-3.

    fp32 training state costs 16 B/param: 4 B weights + 4 B grads +
    4 B Adam m + 4 B Adam v. Stage 1 shards the optimizer states across
    GPUs, stage 2 shards the gradients too, stage 3 shards the
    parameters as well - so nothing is ever replicated.
    """
    base = params_billion * 16
    if stage == 0:
        return base
    if stage == 1:
        return base - params_billion * 8 * (1 - 1 / gpus)
    if stage == 2:
        return base - params_billion * 12 * (1 - 1 / gpus)
    return base / gpus


for stage in (0, 1, 2, 3):
    gb = zero_stage_gb(7.0, stage, 8)
    print(f"ZeRO stage {stage}: {gb:5.1f} GB per GPU (7B params, 8 GPUs)")
```

**Output:**

```text
ZeRO stage 0: 112.0 GB per GPU (7B params, 8 GPUs)
ZeRO stage 1:  63.0 GB per GPU (7B params, 8 GPUs)
ZeRO stage 2:  38.5 GB per GPU (7B params, 8 GPUs)
ZeRO stage 3:  14.0 GB per GPU (7B params, 8 GPUs)
```

Stage 1 shards optimizer states, stage 2 adds gradients, and stage 3
shards the parameters themselves - nothing is replicated anywhere, which
is how a 7B model trains on hardware that could never hold 112 GB of
state per card.

---

## Architecture 3: Load Balancing

### Strategies

#### 1. Round Robin

```python



class RoundRobinBalancer:
    """Distribute requests sequentially across servers."""

    def __init__(self, servers: list[str]):
        self.servers = servers
        self.current = 0

    def next_server(self) -> str:
        server = self.servers[self.current]
        self.current = (self.current + 1) % len(self.servers)
        return server


balancer = RoundRobinBalancer(["gpu-0", "gpu-1", "gpu-2"])
picks = [balancer.next_server() for _ in range(7)]
print(picks)
```

**Output:**

```text
['gpu-0', 'gpu-1', 'gpu-2', 'gpu-0', 'gpu-1', 'gpu-2', 'gpu-0']
```

**Pros:** Simple, fair distribution
**Cons:** Doesn't account for server load or capacity

#### 2. Least Connections

```python
from collections import defaultdict
import threading



class LeastConnectionsBalancer:
    """Route to server with fewest active connections."""

    def __init__(self, servers: list[str]):
        self.servers = servers
        self.connections = defaultdict(int)
        self.lock = threading.Lock()

    def next_server(self) -> str:
        with self.lock:
            # Find server with minimum connections
            server = min(self.servers, key=lambda s: self.connections[s])

            # Increment count
            self.connections[server] += 1

            return server

    def release(self, server: str):
        """Decrement connection count when request completes."""
        with self.lock:
            self.connections[server] = max(0, self.connections[server] - 1)


lb = LeastConnectionsBalancer(["gpu-0", "gpu-1"])
first_two = [lb.next_server() for _ in range(2)]
print("in flight:", dict(lb.connections))
lb.release(first_two[0])
print("after one release, next is:", lb.next_server())
```

**Output:**

```text
in flight: {'gpu-0': 1, 'gpu-1': 1}
after one release, next is: gpu-0
```

**Pros:** Accounts for current load
**Cons:** Doesn't predict future load

#### 3. GPU Memory Aware

Route each request to the (server, gpu) pair that currently has the most
free memory. The memory probe is injected: production passes a callable
that shells out to `nvidia-smi` over ssh (or calls
`torch.cuda.mem_get_info` locally), tests pass a dict-backed fake - the
routing logic below is exercised identically either way.

```python
import threading
import time



class GPUMemoryAwareBalancer:
    """Route to the (server, gpu) pair with the most free memory.

    The probe is injected so the routing logic is testable without
    nvidia-smi/ssh: production passes a callable that shells out (or
    calls torch.cuda.mem_get_info); tests pass a dict-backed fake.
    """

    def __init__(self, servers, probe, ttl_seconds: float = 5.0):
        self.probe = probe                     # callable() -> {(server, gpu): free_mb}
        self.ttl = ttl_seconds
        self.cache: dict[tuple[str, int], int] = {}
        self.last_update = 0.0
        self.lock = threading.Lock()

    def _refresh(self):
        now = time.time()
        if now - self.last_update < self.ttl:
            return                              # cache still fresh
        with self.lock:
            if now - self.last_update < self.ttl:   # double-checked
                return
            self.cache = dict(self.probe())
            self.last_update = now

    def next_server(self) -> tuple[str, int]:
        self._refresh()
        return max(self.cache, key=self.cache.get)


free_mb = {("gpu-a", 0): 21000, ("gpu-a", 1): 4000, ("gpu-b", 0): 15000}
balancer = GPUMemoryAwareBalancer(list(free_mb), probe=lambda: free_mb)

picks = [balancer.next_server() for _ in range(3)]
print("routes:", picks)
print("cached view:", balancer.cache)
```

**Output:**

```text
routes: [('gpu-a', 0), ('gpu-a', 0), ('gpu-a', 0)]
cached view: {('gpu-a', 0): 21000, ('gpu-a', 1): 4000, ('gpu-b', 0): 15000}
```

The TTL with a double-checked lock means concurrent requests share one
probe sweep per window instead of stampeding the fleet with nvidia-smi
calls.

**Pros:** Optimizes for GPU constraints
**Cons:** Requires GPU access, higher latency

---

## Architecture 4: Caching Strategies

### 1. Response Caching

```python
from typing import Any
import hashlib
import json
import pickle
from pathlib import Path
import time


class ModelResponseCache:
    """
    Cache model responses for identical inputs.

    Useful for:
    - Frequently repeated queries
    - Expensive computations
    - API rate limiting
    """

    def __init__(
        self,
        cache_dir: str = "./cache",
        max_size: int = 10000,
        ttl_seconds: int = 3600
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        # In-memory index
        self.index: dict[str, float] = {}

    def _hash_input(self, input_data: Any) -> str:
        """Generate hash for input data."""
        # Convert to string if needed
        if isinstance(input_data, str):
            input_str = input_data
        elif isinstance(input_data, dict):
            input_str = json.dumps(input_data, sort_keys=True)
        elif isinstance(input_data, (list, tuple)):
            input_str = str(input_data)
        else:
            input_str = str(input_data)

        return hashlib.sha256(input_str.encode()).hexdigest()

    def _get_cache_path(self, input_hash: str) -> Path:
        """Get cache file path for hash."""
        return self.cache_dir / f"{input_hash}.pkl"

    def get(self, input_data: Any) -> Any | None:
        """Get cached response if available and not expired."""
        input_hash = self._hash_input(input_data)
        cache_path = self._get_cache_path(input_hash)

        # Check if exists
        if not cache_path.exists():
            return None

        # Check if expired - use the file's mtime, not the in-memory index:
        # the index is lost on restart while the cache files persist
        if time.time() - cache_path.stat().st_mtime > self.ttl_seconds:
            cache_path.unlink(missing_ok=True)
            self.index.pop(input_hash, None)
            return None

        # Load from cache
        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def put(self, input_data: Any, response: Any):
        """Store response in cache."""
        input_hash = self._hash_input(input_data)
        cache_path = self._get_cache_path(input_hash)

        # Check cache size limit
        if len(self.index) >= self.max_size:
            self._evict_oldest()

        # Store response
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(response, f)

            self.index[input_hash] = time.time()

        except Exception as e:
            print(f"Error caching response: {e}")

    def _evict_oldest(self):
        """Remove oldest entry from cache."""
        if not self.index:
            return

        # Find oldest
        oldest_hash = min(self.index, key=self.index.get)

        # Remove files
        cache_path = self._get_cache_path(oldest_hash)
        cache_path.unlink(missing_ok=True)

        # Remove from index
        del self.index[oldest_hash]


# Usage
cache = ModelResponseCache()


class EchoModel:
    """Stand-in for an expensive model call."""

    def compute(self, input_data):
        return f"expensive_result for {input_data}"


model = EchoModel()
input_data = {"prompt": "hello"}

# Cache miss -> compute, then store
cached = cache.get(input_data)
if cached is None:
    cached = model.compute(input_data)
    cache.put(input_data, cached)

# Same input again -> cache hit, no compute
assert cache.get(input_data) == cached
print(cache.get(input_data))
```

**Output:**

```text
expensive_result for {'prompt': 'hello'}
```

The cache persists as pickle files under `./cache/`, so hits survive a
process restart - the TTL check reads each file's mtime, not an in-memory
index. Production deployments point `cache_dir` at fast local disk, or a
shared store when replicas must share the cache.

### 2. Embedding Cache (for RAG)

```python
import hashlib
from pathlib import Path
from typing import Any

import torch


class EmbeddingCache:
    """
    Cache embeddings for RAG systems.

    Embeddings are expensive to compute.
    Cache frequently queried chunks.
    """

    def __init__(self, embed_model, cache_dir: str = "./embeddings"):
        self.embed_model = embed_model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, text: str) -> Path:
        """Get cache file path for text."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.pt"

    def embed(self, text: str) -> Any:
        """Get embedding with caching."""
        cache_path = self._get_cache_path(text)

        # Check cache
        if cache_path.exists():
            return torch.load(cache_path)

        # Compute embedding
        embedding = self.embed_model.embed(text)

        # Cache it
        torch.save(embedding, cache_path)

        return embedding

    def embed_batch(self, texts: list[str]) -> Any:
        """Embed multiple texts with caching."""
        embeddings = []
        uncached_texts = []
        uncached_indices = []

        # Check cache for each
        for i, text in enumerate(texts):
            cache_path = self._get_cache_path(text)

            if cache_path.exists():
                embedding = torch.load(cache_path)
                embeddings.append((i, embedding))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Batch compute uncached
        if uncached_texts:
            new_embeddings = self.embed_model.embed_batch(uncached_texts)

            for text, emb, idx in zip(uncached_texts, new_embeddings, uncached_indices):
                # Cache
                cache_path = self._get_cache_path(text)
                torch.save(emb, cache_path)

                embeddings.append((idx, emb))

        # Sort by original index and return
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]


class MockEmbedder:
    """Stand-in for a real sentence encoder; counts compute calls."""

    def __init__(self, dim: int = 8):
        self.dim = dim
        self.calls = 0

    def _vec(self, text):
        self.calls += 1
        g = torch.Generator().manual_seed(len(text))
        return torch.randn(self.dim, generator=g)

    def embed(self, text):
        return self._vec(text)

    def embed_batch(self, texts):
        return torch.stack([self._vec(t) for t in texts])


embedder = MockEmbedder()
cache = EmbeddingCache(embedder, cache_dir="./embeddings")

texts = ["gpu serving", "kv cache", "gpu serving", "paged attention", "kv cache"]
embeddings = cache.embed_batch(texts)          # first pass: cache is cold
print("texts:", len(texts), "-> embeddings:", len(embeddings))
print("cold-cache compute calls:", embedder.calls)

cache.embed_batch(texts)                       # second pass: every text hits disk
print("warm-cache compute calls:", embedder.calls, "(repeats served from cache)")
again = cache.embed_batch(texts)
print("warm pass returns identical vectors:",
      all(torch.equal(a, b) for a, b in zip(embeddings, again)))
```

**Output:**

```text
texts: 5 -> embeddings: 5
cold-cache compute calls: 5
warm-cache compute calls: 5 (repeats served from cache)
warm pass returns identical vectors: True
```

Note the cold pass still spends one compute call per text - within a
single batch call, duplicates are not coalesced (each miss joins the
uncached list independently). The cache pays off from the second call
onward, which is exactly the RAG pattern: the same indexed chunks get
re-embedded by query after query. The demo writes `.pt` files under
`./embeddings/`.

### 3. KV Cache (for LLMs)

```python
import torch


class KVCache:
    """
    Key-Value cache for transformer attention.

    Stores computed keys and values for each token.
    Avoids recomputing for autoregressive generation.
    """

    def __init__(
        self,
        batch_size: int,
        max_seq_len: int,
        num_layers: int,
        num_heads: int,
        head_dim: int,
        device: str = ""
    ):
        self.max_seq_len = max_seq_len
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim
        # Portable default: cuda when available, else cpu
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Pre-allocate the full cache up front. The batch dimension must be
        # real allocated storage: expand() only creates a stride-0 view, so
        # writing through an expanded batch dim aliases every batch row to
        # the same memory (silent data corruption).
        # Shape: (num_layers, 2, batch, num_heads, seq_len, head_dim)
        # 2 is for keys and values
        self.cache = torch.zeros(
            num_layers,
            2,
            batch_size,
            num_heads,
            max_seq_len,
            head_dim,
            device=self.device
        )

        self.current_seq_len = 0

    def update(self, layer_idx: int, keys: torch.Tensor, values: torch.Tensor):
        """
        Update cache for a specific layer.

        Args:
            layer_idx: Which transformer layer
            keys: Key tensors (batch, num_heads, seq_len, head_dim)
            values: Value tensors (batch, num_heads, seq_len, head_dim)
        """
        batch_size, num_heads, seq_len, head_dim = keys.shape

        if batch_size != self.cache.shape[2]:
            raise ValueError(
                f"batch size {batch_size} != cache batch size "
                f"{self.cache.shape[2]} - allocate one cache per batch"
            )

        end_pos = self.current_seq_len + seq_len
        if end_pos > self.max_seq_len:
            raise ValueError("sequence exceeds max_seq_len")

        # Store in cache
        self.cache[layer_idx, 0, :, :, self.current_seq_len:end_pos, :] = keys
        self.cache[layer_idx, 1, :, :, self.current_seq_len:end_pos, :] = values

        # Advance the write position
        self.current_seq_len = end_pos

    def get(self, layer_idx: int) -> tuple:
        """Get cached keys and values for a layer (up to the current position)."""
        keys = self.cache[layer_idx, 0, :, :, :self.current_seq_len, :]
        values = self.cache[layer_idx, 1, :, :, :self.current_seq_len, :]
        return keys, values

    def reset(self):
        """Clear cache for new sequence."""
        self.current_seq_len = 0


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
kv = KVCache(batch_size=2, max_seq_len=16, num_layers=2,
             num_heads=2, head_dim=4, device=str(device))
print("cache device:", kv.device)
print("cache buffer:", tuple(kv.cache.shape), "=", kv.cache.numel(), "floats")

torch.manual_seed(0)
# Prefill: process a 5-token prompt for layer 0 in one shot
kv.update(0, torch.randn(2, 2, 5, 4), torch.randn(2, 2, 5, 4))
print("after prefill:", kv.current_seq_len, "tokens cached")

# Decode: 3 tokens, one at a time - each step reuses the cached prefix
for _ in range(3):
    kv.update(0, torch.randn(2, 2, 1, 4), torch.randn(2, 2, 1, 4))
print("after 3 decode steps:", kv.current_seq_len, "tokens cached")

k, v = kv.get(0)
print("layer-0 K/V view:", tuple(k.shape))
kv.reset()
print("after reset:", kv.current_seq_len, "tokens cached")
```

**Output:**

```text
cache device: cuda
cache buffer: (2, 2, 2, 2, 16, 4) = 1024 floats
after prefill: 5 tokens cached
after 3 decode steps: 8 tokens cached
layer-0 K/V view: (2, 2, 8, 4)
after reset: 0 tokens cached
```

This is the prefill-then-decode pattern every LLM server runs: the prompt
lands in the cache in one forward pass, then each generated token
re-attends over the cached prefix instead of recomputing it. The `get()`
view stops at `current_seq_len`, so attention never sees the zeros of
unwritten slots.

---

## Real-World: vLLM Architecture

### How vLLM Optimizes Serving

```python
"""
vLLM is a high-throughput LLM serving system.

Key optimizations:
1. PagedAttention - Efficient memory management
2. Continuous batching - Dynamic batch formation
3. KV cache optimization - Smart caching
4. Speculative decoding - Acceleration via draft models
"""




class PagedAttention:
    """
    PagedAttention manages KV cache like OS manages memory.

    Instead of contiguous allocation, uses pages.
    Allows efficient memory utilization.
    """

    def __init__(self, page_size: int = 16, num_blocks: int = 1000):
        self.page_size = page_size
        self.num_blocks = num_blocks

        # Track free and allocated blocks
        self.free_blocks = list(range(num_blocks))
        self.allocated_blocks = {}

    def allocate(self, request_id: str, num_tokens: int) -> list[int]:
        """Allocate blocks for request."""
        num_pages = (num_tokens + self.page_size - 1) // self.page_size

        if len(self.free_blocks) < num_pages:
            raise MemoryError("Not enough free blocks")

        blocks = self.free_blocks[:num_pages]
        self.free_blocks = self.free_blocks[num_pages:]
        self.allocated_blocks[request_id] = blocks

        return blocks

    def free(self, request_id: str):
        """Free blocks for request."""
        if request_id in self.allocated_blocks:
            blocks = self.allocated_blocks[request_id]
            self.free_blocks.extend(blocks)
            del self.allocated_blocks[request_id]


class ContinuousBatching:
    """
    Dynamic batching unlike static batching.

    Static batch: Wait for full batch to form
    Continuous batch: Process completed requests, add new ones immediately
    """

    def __init__(self, max_batch_size: int = 32):
        self.max_batch_size = max_batch_size
        self.active_requests = []

    def add_request(self, request):
        """Add new request to batch."""
        if len(self.active_requests) < self.max_batch_size:
            self.active_requests.append(request)
            return True
        return False

    def step(self, model):
        """
        Execute one step of all active requests.

        Key: Remove completed requests, add new ones
        """
        # Process current batch
        outputs = []
        still_active = []

        for request in self.active_requests:
            output = model.generate_one_token(request)

            if request.done:
                outputs.append(request.output)
            else:
                still_active.append(request)

        # Update active requests
        self.active_requests = still_active

        return outputs

    def can_add_more(self) -> bool:
        """Check if batch has room."""
        return len(self.active_requests) < self.max_batch_size


pa = PagedAttention(page_size=16, num_blocks=8)
b1 = pa.allocate("req-1", 40)          # 40 tokens -> 3 pages
b2 = pa.allocate("req-2", 20)          # 20 tokens -> 2 pages
print("req-1 pages:", b1)
print("req-2 pages:", b2)
print("free after two allocations:", pa.free_blocks)
pa.free("req-1")                        # pages return for reuse
print("free after req-1 completes:", pa.free_blocks)

cb = ContinuousBatching(max_batch_size=3)
admitted = [cb.add_request(f"r{i}") for i in range(4)]
print("admit up to capacity:", admitted)
print("can_add_more:", cb.can_add_more())
```

**Output:**

```text
req-1 pages: [0, 1, 2]
req-2 pages: [3, 4]
free after two allocations: [5, 6, 7]
free after req-1 completes: [5, 6, 7, 0, 1, 2]
admit up to capacity: [True, True, True, False]
can_add_more: False
```

Two ideas carry real vLLM: requests own PAGES, not contiguous regions, so
finishing requests leave usable holes (req-1's pages go straight back to
the free list) instead of fragmenting the pool; and batches admit new
requests the moment older ones finish, instead of waiting for a fixed
batch size to drain.

---

## Exercise: Build a Serving System

### Task

Implement a production-ready model server with:
1. Dynamic batching (timeout-based)
2. GPU memory monitoring
3. Response caching

### Starter Code

```python
import time
import torch
from typing import Any
from collections import defaultdict

class YourModelServer:
    def __init__(self, model, max_batch_size=32, timeout_ms=50):
        self.model = model
        self.max_batch_size = max_batch_size
        self.timeout_ms = timeout_ms

        # TODO: Implement batching logic
        self.pending = []
        self.results = {}

    def add_request(self, input_data):
        # TODO: Add to pending queue
        # TODO: Check if batch should process
        pass

    def get_result(self, request_id, timeout=5.0):
        # TODO: Wait for and return result
        pass

    def _check_and_process_batch(self):
        # TODO: Check if we should form batch
        # TODO: Process if full or timed out
        pass

    def _get_gpu_memory_mb(self) -> int:
        # TODO: Query GPU memory
        # Return free memory in MB
        pass
```

### Requirements

1. **Dynamic Batching**
   - Form batch when size reaches max_batch_size
   - Form batch when oldest request exceeds timeout
   - Track per-request latency

2. **GPU Memory Monitoring**
   - Use nvidia-smi to check free memory
   - Reject requests if insufficient memory
   - Log memory usage statistics

3. **Response Caching**
   - Cache last 1000 responses
   - Use SHA256 hash for cache keys
   - Implement LRU eviction

### Testing

A checklist to run against your implementation - each item maps to a
requirement above:

```text
server = YourModelServer(model)

# 1. Concurrency: 50 requests from 10 threads all return correct outputs
# 2. Batching: stats show fewer model calls than requests (batching happened)
# 3. Timeout: a single lone request still completes (timeout flush works)
# 4. GPU memory: _get_gpu_memory_mb returns a positive int; below the
#    threshold the server rejects instead of crashing
# 5. Caching: the same input twice triggers one model call, not two
```

### Solution Reference

See: [2306: Building a Production Framework](./guides/2306-Building-Production-Framework.md)

---

## Summary

**Key Architectures:**

1. **Request Batching** - Maximize GPU utilization
2. **Model Parallelism** - Serve large models
3. **Load Balancing** - Distribute requests effectively
4. **Caching** - Avoid redundant computation

**Production Systems:**
- vLLM (PagedAttention + Continuous Batching)
- TGI (Tensor Parallelism + Flash Attention)
- Triton Inference Server (Multi-framework support)

---

## References

### Related Documents

- [2301: Framework Design Patterns](./2301-Framework-Design-Patterns.md)
- [2303: API Design for ML Systems](./2303-API-Design-for-ML.md)
- [2304: Production Deployment Patterns](./2304-Production-Deployment-Patterns.md)

### External References

- [Welcome to vLLM - vLLM Documentation](https://docs.vllm.ai/en/latest/)
- [Efficient Memory Management for Large Language Model Serving with PagedAttention (SOSP 2023)](https://arxiv.org/abs/2309.06180)
- [DeepSpeed - Getting Started](https://www.deepspeed.ai/getting-started/)
- [NVIDIA Dynamo-Triton (formerly Triton Inference Server)](https://developer.nvidia.com/dynamo-triton)

---

## Next Steps

- Next Lesson: **[2303: API Design for ML Systems](./2303-API-Design-for-ML.md)**
- Practical: **[LAB-009: Production Deployment](../../../learning-resources/labs/LAB-009-Production-Deployment.md)**
- Assessment: **[2300: Framework Engineering - Quiz](./assessment/QUIZ.md)**

**Related:** [1401: Ollama Enterprise Deployment](../../phase1-infra/1400-llmops/1401-Ollama-Enterprise.md) — deploy and load-balance a real serving stack yourself; [1402: vLLM and TGI High-Concurrency Inference](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) — the production engines that run this lesson's batching, paging, and continuous batching at scale; [LAB-007: Production RAG System](../../../learning-resources/labs/LAB-007-Production-RAG.md) — serving a retrieval pipeline under real load

**Experiment:** [EXP_1404: vLLM Production Tuning Experiments](../../../../experiments/EXP_1404_VLLM_TUNING.md) — the nearest hands-on lab to this lesson's subject: tune real vLLM serving throughput and latency (nearest-relevant — no EXP_23xx exists yet)
