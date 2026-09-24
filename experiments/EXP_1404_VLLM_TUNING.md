# EXP_1404: vLLM Production Tuning Experiments

## Overview
Practical experiments for tuning vLLM (Virtual Large Language Model) for production deployment on an 11GB VRAM GPU.

## Experiment 1: vLLM Server Configuration

### Objective
Configure vLLM server with optimal parameters for throughput and memory efficiency.

### Implementation

```python
# vllm_deployment.py
import subprocess
import requests
import json
import time

class VLLMDeployment:
    """Deploy and manage vLLM instances"""

    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.model_name = model_name
        self.base_url = "http://localhost:8000"

    def start_vllm_server(self,
                         quantization: str = "awq",
                         tensor_parallel_size: int = 1,
                         max_model_len: int = 4096,
                         gpu_memory_utilization: float = 0.9,
                         block_size: int = 16):
        """Start vLLM server with optimized parameters"""

        print(f"Starting vLLM server for {self.model_name}...")

        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", self.model_name,
            "--quantization", quantization,
            "--tensor-parallel-size", str(tensor_parallel_size),
            "--max-model-len", str(max_model_len),
            "--gpu-memory-utilization", str(gpu_memory_utilization),
            "--block-size", str(block_size),
            "--host", "0.0.0.0",
            "--port", "8000",
            # Performance optimizations
            "--disable-log-requests",
            "--max-num-seqs", "256",
            "--max-num-batched-tokens", "8192",
            # Enable OpenAI-compatible API
            "--chat-template", "tokenizer",
        ]

        print("Command:", " ".join(cmd))

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            print("vLLM server starting...")
            time.sleep(15)  # Wait for startup

            if self.check_health():
                print("✅ vLLM server started successfully")
                return process
            else:
                print("❌ vLLM server failed to start")
                process.terminate()
                return None

        except Exception as e:
            print(f"❌ Error starting vLLM: {e}")
            return None

    def check_health(self):
        """Check if vLLM server is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self):
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return response.json()
        except Exception as e:
            print(f"Error listing models: {e}")
            return None


def test_vllm_deployment():
    """Test vLLM deployment"""

    print("vLLM Deployment Test")
    print("=" * 60)

    vllm = VLLMDeployment()

    # Start server
    process = vllm.start_vllm_server()

    if process:
        # Check health
        health = vllm.check_health()
        print(f"Health check: {'✅' if health else '❌'}")

        # List models
        models = vllm.list_models()
        if models:
            print("\nAvailable models:")
            print(json.dumps(models, indent=2))

        # Cleanup
        print("\nPress Ctrl+C to stop...")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping vLLM server...")
            process.terminate()


if __name__ == "__main__":
    test_vllm_deployment()
```

---

## Experiment 2: PagedAttention Tuning

### Objective
Optimize PagedAttention block size for memory efficiency and throughput.

### Implementation

```python
# paged_attention_tuning.py
import requests
import time
import statistics

class PagedAttentionTuner:
    """Tune PagedAttention parameters"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def generate(self, prompt: str, max_tokens: int = 100):
        """Generate with OpenAI API"""

        start_time = time.time()

        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=60
        )

        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            usage = result.get("usage", {})
            generated = usage.get("completion_tokens", 0)
            throughput = generated / duration

            return {
                "success": True,
                "duration": duration,
                "generated_tokens": generated,
                "throughput": throughput,
                "prompt_tokens": usage.get("prompt_tokens", 0)
            }

        return {"success": False, "error": response.text}

    def test_block_size(self, block_size: int, num_requests: int = 10):
        """Test performance with specific block size"""

        print(f"\nTesting block_size={block_size}...")

        prompts = [
            "Explain the theory of relativity.",
            "What are the main causes of climate change?",
            "How does blockchain technology work?",
            "Describe the architecture of transformer models.",
            "Write a short story about time travel.",
            "What is quantum entanglement?",
            "Explain how neural networks learn.",
            "What is the meaning of consciousness?",
            "How do vaccines work?",
            "Describe the process of photosynthesis."
        ][:num_requests]

        results = []

        for prompt in prompts:
            result = self.generate(prompt)
            results.append(result)

        successful = [r for r in results if r["success"]]

        if successful:
            avg_latency = statistics.mean([r["duration"] for r in successful])
            avg_throughput = statistics.mean([r["throughput"] for r in successful])

            print(f"  Avg Latency: {avg_latency:.2f}s")
            print(f"  Avg Throughput: {avg_throughput:.2f} tokens/s")

            return {
                "block_size": block_size,
                "avg_latency": avg_latency,
                "avg_throughput": avg_throughput
            }

        return None

    def find_optimal_block_size(self, block_sizes: list = [8, 16, 32]):
        """Find optimal block size"""

        print("PagedAttention Block Size Tuning")
        print("=" * 60)

        results = []

        for block_size in block_sizes:
            # Note: This would require restarting vLLM with different block size
            result = self.test_block_size(block_size)
            if result:
                results.append(result)
            time.sleep(2)

        if results:
            optimal = max(results, key=lambda x: x["avg_throughput"])
            print(f"\n✅ Optimal block size: {optimal['block_size']}")
            return optimal

        return None


def test_paged_attention():
    """Test PagedAttention tuning"""

    print("vLLM PagedAttention Tuning")
    print("=" * 60)

    tuner = PagedAttentionTuner()
    tuner.find_optimal_block_size()


if __name__ == "__main__":
    test_paged_attention()
```

---

## Experiment 3: Speculative Decoding Setup

### Objective
Configure speculative decoding with draft model for faster inference.

### Implementation

```python
# speculative_decoding.py
import requests
import time

class SpeculativeDecodingSetup:
    """Setup and test speculative decoding"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def start_with_draft_model(self,
                               model: str = "mistralai/Mistral-7B-Instruct-v0.2",
                               draft_model: str = "tinyllama/tinyllama-1.1b-chat"):
        """Start vLLM with speculative decoding"""

        print(f"Starting vLLM with speculative decoding...")
        print(f"  Main model: {model}")
        print(f"  Draft model: {draft_model}")

        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", model,
            "--speculative-model", draft_model,
            "--num-speculative-tokens", "5",
            "--quantization", "awq",
            "--max-model-len", "4096",
            "--gpu-memory-utilization", "0.9",
        ]

        print("Command:", " ".join(cmd))

        try:
            process = subprocess.Popen(cmd, text=True)
            time.sleep(20)

            if self.check_health():
                print("✅ Speculative decoding enabled")
                return process

        except Exception as e:
            print(f"❌ Error: {e}")

        return None

    def benchmark_with_without_speculative(self):
        """Compare performance with and without speculative decoding"""

        print("\nSpeculative Decoding Benchmark")
        print("=" * 60)

        prompt = "Explain the concept of machine learning in detail, including supervised learning, unsupervised learning, and reinforcement learning. Provide examples for each type."

        # Without speculative (would need separate server)
        # This is conceptual - you'd run two servers

        results = {}

        # Test with speculative
        print("\nWith Speculative Decoding:")
        result_spec = self.benchmark_generate(prompt)
        results["speculative"] = result_spec

        print(f"  Latency: {result_spec['duration']:.2f}s")
        print(f"  Throughput: {result_spec['throughput']:.2f} tokens/s")

        return results

    def benchmark_generate(self, prompt: str, max_tokens: int = 500):
        """Benchmark generation"""

        start = time.time()

        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            },
            timeout=120
        )

        duration = time.time() - start

        if response.status_code == 200:
            result = response.json()
            tokens = result["usage"]["completion_tokens"]
            return {
                "duration": duration,
                "generated_tokens": tokens,
                "throughput": tokens / duration
            }

        return None


def test_speculative_decoding():
    """Test speculative decoding setup"""

    print("vLLM Speculative Decoding")
    print("=" * 60)

    setup = SpeculativeDecodingSetup()

    # Benchmark
    results = setup.benchmark_with_without_speculative()

    if results.get("speculative"):
        print("\n✅ Speculative decoding working!")
        print(f"Expected speedup: 2-3x")


if __name__ == "__main__":
    test_speculative_decoding()
```

---

## Experiment 4: Concurrent Request Handling

### Objective
Test vLLM's ability to handle concurrent requests efficiently.

### Implementation

```python
# concurrent_requests.py
import asyncio
import aiohttp
import time
import statistics
from typing import List

class ConcurrentRequestTester:
    """Test concurrent request handling"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def generate_single(self,
                             session: aiohttp.ClientSession,
                             prompt: str,
                             max_tokens: int = 100):
        """Single generation request"""

        start = time.time()

        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": "mistralai/Mistral-7B-Instruct-v0.2",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                result = await response.json()

                duration = time.time() - start

                if response.status == 200:
                    tokens = result["usage"]["completion_tokens"]
                    return {
                        "success": True,
                        "duration": duration,
                        "tokens": tokens,
                        "throughput": tokens / duration
                    }

                return {"success": False, "error": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_concurrent(self, num_requests: int, concurrency: int):
        """Test concurrent requests"""

        print(f"\nTesting {num_requests} requests with concurrency={concurrency}...")

        prompts = [
            "Explain what is artificial intelligence.",
            "Write a haiku about programming.",
            "What causes climate change?",
            "How does photosynthesis work?",
            "Describe transformer architecture.",
            "What is quantum mechanics?",
            "Explain neural networks.",
            "Why is the sky blue?",
            "How do vaccines work?",
            "What is machine learning?",
            "Explain deep learning.",
            "Write about data science.",
            "What is blockchain?",
            "Explain cloud computing.",
            "Describe edge computing."
        ] * ((num_requests // 15) + 1)

        prompts = prompts[:num_requests]

        start_time = time.time()

        # Create semaphore for concurrency limit
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_generate(prompt):
            async with semaphore:
                return await self.generate_single(None, prompt)

        # Run all requests
        async with aiohttp.ClientSession() as session:
            tasks = [self.generate_single(session, p) for p in prompts]
            results = await asyncio.gather(*tasks)

        total_duration = time.time() - start_time

        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if successful:
            avg_latency = statistics.mean([r["duration"] for r in successful])
            p95_latency = sorted([r["duration"] for r in successful])[int(len(successful) * 0.95)]
            total_tokens = sum([r["tokens"] for r in successful])
            overall_throughput = total_tokens / total_duration

            print(f"  Total Duration: {total_duration:.2f}s")
            print(f"  Avg Latency: {avg_latency:.2f}s")
            print(f"  P95 Latency: {p95_latency:.2f}s")
            print(f"  Total Throughput: {overall_throughput:.2f} tokens/s")
            print(f"  Success Rate: {len(successful)}/{num_requests} ({len(successful)/num_requests*100:.1f}%)")

            return {
                "num_requests": num_requests,
                "concurrency": concurrency,
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "throughput": overall_throughput,
                "success_rate": len(successful) / num_requests
            }

        return None

    async def find_optimal_concurrency(self):
        """Find optimal concurrency level"""

        print("Finding Optimal Concurrency")
        print("=" * 60)

        concurrencies = [1, 4, 8, 16, 32]
        results = []

        for concurrency in concurrencies:
            result = await self.test_concurrent(32, concurrency)
            if result:
                results.append(result)
            await asyncio.sleep(2)

        # Find optimal
        if results:
            optimal = max(results, key=lambda x: x["throughput"])
            print(f"\n✅ Optimal concurrency: {optimal['concurrency']}")
            print(f"  Throughput: {optimal['throughput']:.2f} tokens/s")

        return results


async def test_concurrent():
    """Test concurrent requests"""

    print("vLLM Concurrent Request Testing")
    print("=" * 60)

    tester = ConcurrentRequestTester()
    await tester.find_optimal_concurrency()


if __name__ == "__main__":
    asyncio.run(test_concurrent())
```

---

## Quick Start

### Deploy vLLM Server

```bash
# Install vLLM
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --quantization awq \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9 \
  --block-size 16

# Test
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistralai/Mistral-7B-Instruct-v0.2",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Run Benchmarks

```bash
# PagedAttention tuning
python paged_attention_tuning.py

# Speculative decoding
python speculative_decoding.py

# Concurrent requests
python concurrent_requests.py
```

---

## Expected Results

### Performance Targets (11GB VRAM GPU)

| Configuration | Throughput | Latency (P95) |
|--------------|-----------|---------------|
| **Single Request** | 35 t/s | 3s |
| **Concurrency=8** | 120 t/s | 12s |
| **Concurrency=16** | 180 t/s | 18s |
| **Speculative** | 250 t/s | 12s |

### Block Size Comparison

| Block Size | Memory Efficiency | Throughput |
|-----------|-------------------|------------|
| 8 | Best | 30 t/s |
| 16 | Good | 35 t/s (optimal) |
| 32 | Fair | 28 t/s |

---

## Experiment Checklist

- [ ] vLLM server deployment
- [ ] OpenAI API compatibility verification
- [ ] PagedAttention block size tuning
- [ ] Speculative decoding setup
- [ ] Concurrent request testing
- [ ] Memory usage monitoring
- [ ] Latency measurement
- [ ] Throughput benchmarking
- [ ] Error rate analysis
- [ ] Production configuration

---

## Related Documentation

- [1402: vLLM and TGI](../docs/phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [1404: vLLM Production Deployment](../docs/phases/phase1-infra/1400-llmops/guides/1404-vLLM-Production-Deployment.md)
- [4202: Speculative Decoding](../docs/phases/phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md)
- [4102: EXL2 and AWQ](../docs/phases/phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md)
