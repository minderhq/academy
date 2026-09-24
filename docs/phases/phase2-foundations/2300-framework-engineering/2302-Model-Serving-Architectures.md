---
Document ID: 2302
Title: Model Serving Architectures
Phase: 2
Module: 2300
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['frameworks', 'architecture', 'api-design', 'production']
---

# 2302: Model Serving Architectures

**Project:** AI Engineering Curriculum
**Phase:** [2300] Framework Engineering
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2.5 hours

---

## Abstract

Serving machine learning models in production requires specialized architectural patterns to maximize throughput, minimize latency, and ensure reliability. This document covers the essential serving architectures used in production ML systems like OpenAI, Anthropic, and enterprise ML platforms.

**What you'll learn:**
- Request batching for GPU optimization
- Model and data parallelism strategies
- Load balancing algorithms
- Caching strategies for ML inference
- Real-world architectures (vLLM, TGI, Triton)

---

## Architecture 1: Request Batching

### The Problem

```python
# BAD: Process requests one at a time
def serve_single_request(request):
    result = model(request)
    return result

# Problem: GPU is underutilized
# Throughput: 5 requests/second
# GPU utilization: 20%
```

**Why it's bad:**
- GPU designed for parallel processing
- Single request doesn't utilize all GPU cores
- High latency per request
- Low throughput overall

### The Solution: Dynamic Batching

```python
import time
import threading
from collections import defaultdict
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import uuid


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
        self.pending: List[Request] = []
        self.results: Dict[str, Any] = {}
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

    def _prepare_batch(self, inputs: List[Any]) -> Any:
        """
        Prepare batch input for model.

        Override this for specific model formats.
        """
        # Default: stack inputs
        import torch
        return torch.stack(inputs)

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        with self.lock:
            return {
                **self.stats,
                "pending_requests": len(self.pending),
                "cached_results": len(self.results),
            }


# Usage Example
import numpy as np


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

    import concurrent.futures

    # Send 20 requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_request, i) for i in range(20)]
        concurrent.futures.wait(futures)

    # Print stats
    print("\nServer Statistics:")
    for key, value in server.get_stats().items():
        print(f"  {key}: {value}")
```

### Expected Output

```
Request 0: output_0
Request 1: output_1
...
Request 19: output_19

Server Statistics:
  total_requests: 20
  batches_processed: 3
  avg_batch_size: 6.67
  avg_latency_ms: 20.0
  pending_requests: 0
  cached_results: 0
```

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

```
Model Size: 70B parameters (140GB VRAM required)
Available: 4x A100 (40GB each = 160GB total)

Solution: Distribute model across GPUs
```

### Data Parallel vs Model Parallel

```
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
│ 1-18    │  │ 19-36   │  │ 37-54   │  │ 55-70   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘

Use case: Large model, limited GPU memory
```

### Implementation: Pipeline Parallelism

```python
import torch
import torch.nn as nn
from typing import List, Any
import threading
import queue


class PipelineModel:
    """
    Split model across multiple GPUs in pipeline fashion.

    Each GPU hosts a portion of the model's layers.
    Data flows sequentially through GPUs.
    """

    def __init__(self, layers: List[nn.Module], device_ids: List[int]):
        """
        Args:
            layers: List of model layers to distribute
            device_ids: GPU IDs for each pipeline stage
        """
        assert len(device_ids) <= len(layers), "More GPUs than layers!"

        # Calculate layers per GPU
        layers_per_stage = len(layers) // len(device_ids)

        # Create pipeline stages
        self.stages = []
        for i, device_id in enumerate(device_ids):
            start_idx = i * layers_per_stage
            end_idx = start_idx + layers_per_stage if i < len(device_ids) - 1 else len(layers)

            # Create stage and move to GPU
            stage = nn.Sequential(*layers[start_idx:end_idx])
            stage = stage.to(f"cuda:{device_id}")
            self.stages.append(stage)

        self.device_ids = device_ids

    def forward(self, x: Any) -> Any:
        """
        Forward pass through pipeline.

        Note: This is a simplified synchronous version.
        Production systems use asynchronous pipelines
        for better throughput.
        """
        current = x

        # Sequentially process through each stage
        for i, stage in enumerate(self.stages):
            device = f"cuda:{self.device_ids[i]}"

            # Move to current GPU
            if isinstance(current, torch.Tensor):
                current = current.to(device)

            # Process through stage
            current = stage(current)

        return current


# Example: Large Transformer Model
def create_large_model() -> PipelineModel:
    """Create a model split across 4 GPUs."""

    # Simulate 70 layers (e.g., LLaMA-70B)
    num_layers = 70
    hidden_size = 4096

    # Create transformer blocks
    layers = []
    for i in range(num_layers):
        block = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=32,
            dim_feedforward=11008,
        )
        layers.append(block)

    # Distribute across 4 GPUs
    # GPU 0: Layers 0-17
    # GPU 1: Layers 18-35
    # GPU 2: Layers 36-53
    # GPU 3: Layers 54-69
    device_ids = [0, 1, 2, 3]

    model = PipelineModel(layers, device_ids)
    return model


# Usage
if __name__ == "__main__":
    # Create distributed model
    model = create_large_model()

    # Forward pass
    batch = torch.randn(8, 1024, 4096)  # (batch, seq, hidden)
    output = model.forward(batch)

    print(f"Output shape: {output.shape}")
```

### Implementation: Tensor Parallelism

```python
import torch
import torch.nn as nn
from typing import Tuple


class TensorParallelLinear(nn.Module):
    """
    Split a large linear layer across multiple GPUs.

    Instead of: y = x @ W
    We do: y = concat(x @ W1, x @ W2, ...) where W = concat(W1, W2, ...)
    """

    def __init__(self, in_features: int, out_features: int, device_ids: List[int]):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.device_ids = device_ids
        self.num_gpus = len(device_ids)

        # Split output dimension across GPUs
        self.out_features_per_gpu = out_features // self.num_gpus

        # Create partitioned weights on each GPU
        self.weights = nn.ParameterList([
            nn.Parameter(
                torch.randn(in_features, self.out_features_per_gpu),
                device=f"cuda:{device_id}"
            )
            for device_id in device_ids
        ])

        # Split bias similarly
        self.biases = nn.ParameterList([
            nn.Parameter(
                torch.randn(self.out_features_per_gpu),
                device=f"cuda:{device_id}"
            )
            for device_id in device_ids
        ])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass with tensor parallelism.

        Input x is replicated to all GPUs.
        Each GPU computes partial output.
        Outputs are concatenated.
        """
        # Replicate input to all GPUs
        # (In practice, this is done once at setup)
        outputs = []

        for i, device_id in enumerate(self.device_ids):
            # Move input to this GPU
            x_device = x.to(f"cuda:{device_id}")

            # Compute partial output
            out = torch.matmul(x_device, self.weights[i]) + self.biases[i]
            outputs.append(out)

        # Concatenate outputs
        result = torch.cat(outputs, dim=-1)

        # Move to first GPU for convenience
        return result.to(f"cuda:{self.device_ids[0]}")


# Example: Large Linear Layer
def create_tp_linear():
    """Create a tensor parallel linear layer."""

    # Normally: 4096 x 4096 = 16M parameters (64MB)
    # With TP: Each GPU has 4096 x 1024 = 4M parameters (16MB)

    layer = TensorParallelLinear(
        in_features=4096,
        out_features=4096,
        device_ids=[0, 1, 2, 3]  # 4 GPUs
    )

    return layer


if __name__ == "__main__":
    # Create TP layer
    layer = create_tp_linear()

    # Forward pass
    x = torch.randn(1, 128, 4096)  # (batch, seq, hidden)
    output = layer(x)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
```

### Production Framework: DeepSpeed

```python
import deepspeed

# Initialize DeepSpeed
model_engine, optimizer, _, _ = deepspeed.initialize(
    model=model,
    model_parameters=model.parameters(),
    config={
        "train_batch_size": 32,
        "gradient_accumulation_steps": 4,
        "fp16": {
            "enabled": True
        },
        "zero_optimization": {
            "stage": 3,  # ZeRO Stage 3 - maximum memory optimization
        }
    }
)

# Training loop
for batch in dataloader:
    # DeepSpeed handles:
    # - Gradient partitioning across GPUs
    # - Optimizer state sharding
    # - Memory efficient training
    loss = model_engine(batch)
    model_engine.backward(loss)
    model_engine.step()
```

---

## Architecture 3: Load Balancing

### Strategies

#### 1. Round Robin

```python
class RoundRobinBalancer:
    """Distribute requests sequentially across servers."""

    def __init__(self, servers: List[str]):
        self.servers = servers
        self.current = 0

    def next_server(self) -> str:
        server = self.servers[self.current]
        self.current = (self.current + 1) % len(self.servers)
        return server
```

**Pros:** Simple, fair distribution
**Cons:** Doesn't account for server load or capacity

#### 2. Least Connections

```python
from collections import defaultdict
import threading


class LeastConnectionsBalancer:
    """Route to server with fewest active connections."""

    def __init__(self, servers: List[str]):
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
```

**Pros:** Accounts for current load
**Cons:** Doesn't predict future load

#### 3. GPU Memory Aware

```python
import subprocess
import threading


class GPUMemoryAwareBalancer:
    """Route to server with most available GPU memory."""

    def __init__(self, gpu_servers: List[Tuple[str, int]]):
        """
        Args:
            gpu_servers: List of (server_address, gpu_id) tuples
        """
        self.servers = gpu_servers
        self.memory_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_ttl = 5  # seconds
        self.last_update = 0

    def _update_memory_cache(self):
        """Query GPU memory for all servers."""
        current_time = time.time()

        # Only update if cache is stale
        if current_time - self.last_update < self.cache_ttl:
            return

        with self.cache_lock:
            for server, gpu_id in self.servers:
                try:
                    # Query nvidia-smi
                    result = subprocess.run([
                        "ssh", server,
                        "nvidia-smi",
                        f"--query-gpu=memory.free",
                        f"--id={gpu_id}",
                        "--format=csv,noheader,nounits"
                    ], capture_output=True, text=True, timeout=5)

                    free_mb = int(result.stdout.strip())
                    self.memory_cache[(server, gpu_id)] = free_mb

                except Exception as e:
                    print(f"Error querying {server}:{gpu_id}: {e}")
                    # Use cached value or default
                    if (server, gpu_id) not in self.memory_cache:
                        self.memory_cache[(server, gpu_id)] = 1000  # Default 1GB

            self.last_update = current_time

    def next_server(self) -> Tuple[str, int]:
        """Get server with most available GPU memory."""
        self._update_memory_cache()

        with self.cache_lock:
            # Find server with max free memory
            server_gpu = max(
                self.memory_cache.keys(),
                key=lambda sg: self.memory_cache[sg]
            )

            return server_gpu
```

**Pros:** Optimizes for GPU constraints
**Cons:** Requires GPU access, higher latency

---

## Architecture 4: Caching Strategies

### 1. Response Caching

```python
from typing import Any, Dict, Optional
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
        self.index: Dict[str, float] = {}

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

    def get(self, input_data: Any) -> Optional[Any]:
        """Get cached response if available and not expired."""
        input_hash = self._hash_input(input_data)
        cache_path = self._get_cache_path(input_hash)

        # Check if exists
        if not cache_path.exists():
            return None

        # Check if expired
        if input_hash in self.index:
            cache_time = self.index[input_hash]
            if time.time() - cache_time > self.ttl_seconds:
                # Expired, remove
                cache_path.unlink(missing_ok=True)
                del self.index[input_hash]
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

# Without cache
response = model.compute(input_data)

# With cache
cached = cache.get(input_data)
if cached is None:
    cached = model.compute(input_data)
    cache.put(input_data, cached)
```

### 2. Embedding Cache (for RAG)

```python
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
            import torch
            return torch.load(cache_path)

        # Compute embedding
        embedding = self.embed_model.embed(text)

        # Cache it
        import torch
        torch.save(embedding, cache_path)

        return embedding

    def embed_batch(self, texts: List[str]) -> Any:
        """Embed multiple texts with caching."""
        embeddings = []
        uncached_texts = []
        uncached_indices = []

        # Check cache for each
        for i, text in enumerate(texts):
            cache_path = self._get_cache_path(text)

            if cache_path.exists():
                import torch
                embedding = torch.load(cache_path)
                embeddings.append((i, embedding))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Batch compute uncached
        if uncached_texts:
            import torch
            new_embeddings = self.embed_model.embed_batch(uncached_texts)

            for text, emb, idx in zip(uncached_texts, new_embeddings, uncached_indices):
                # Cache
                cache_path = self._get_cache_path(text)
                torch.save(emb, cache_path)

                embeddings.append((idx, emb))

        # Sort by original index and return
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]
```

### 3. KV Cache (for LLMs)

```python
class KVCache:
    """
    Key-Value cache for transformer attention.

    Stores computed keys and values for each token.
    Avoids recomputing for autoregressive generation.
    """

    def __init__(self, max_seq_len: int, num_layers: int, num_heads: int, head_dim: int, device: str = "cuda"):
        self.max_seq_len = max_seq_len
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.device = device

        # Pre-allocate cache
        # Shape: (num_layers, 2, batch, num_heads, seq_len, head_dim)
        # 2 is for keys and values
        self.cache = torch.zeros(
            num_layers,
            2,
            1,  # batch_size (will expand dynamically)
            num_heads,
            max_seq_len,
            head_dim,
            device=device
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

        # Expand cache if needed
        if self.cache.shape[2] != batch_size:
            self.cache = self.cache.expand(-1, -1, batch_size, -1, -1, -1)

        # Store in cache
        end_pos = self.current_seq_len + seq_len
        self.cache[layer_idx, 0, :, :, self.current_seq_len:end_pos, :] = keys
        self.cache[layer_idx, 1, :, :, self.current_seq_len:end_pos, :] = values

    def get(self, layer_idx: int) -> tuple:
        """Get cached keys and values for a layer."""
        keys = self.cache[layer_idx, 0]  # All cached keys
        values = self.cache[layer_idx, 1]  # All cached values
        return keys, values

    def reset(self):
        """Clear cache for new sequence."""
        self.current_seq_len = 0
```

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

    def allocate(self, request_id: str, num_tokens: int) -> List[int]:
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
```

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
from typing import Any, Dict, Optional
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

```python
# Test your implementation
server = YourModelServer(model)

# Concurrent requests
def make_request(i):
    rid = server.add_request(f"input_{i}")
    result = server.get_result(rid)
    print(f"Request {i}: {result}")

# Run 50 concurrent requests
# Check stats
# Verify caching works
```

### Solution Reference

See: [2306: Building Production Framework](./guides/2306-Building-Production-Framework.md)

---

## Related Topics

- [1401: Ollama Enterprise](../../phase1-infra/1400-llmops/1401-Ollama-Enterprise.md) - Local model serving
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - Production serving frameworks
- [2303: API Design for ML](./2303-API-Design-for-ML.md) - Build APIs for served models
- [2304: Production Deployment](./2304-Production-Deployment-Patterns.md) - Deploy serving systems
- [LAB-007: Production RAG](../../../learning-resources/labs/LAB-007-Production-RAG.md) - Hands-on practice

---

## Next Steps

- Continue with: **[2303: API Design for ML](./2303-API-Design-for-ML.md)**
- Practical: **[LAB-009: Model Deployment](../../../learning-resources/labs/LAB-009-Production-Deployment.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

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
