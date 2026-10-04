---
Document ID: EXP_1403
Title: "EXP_1403: TGI (Text Generation Inference) Tuning Experiments"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# EXP_1403: TGI (Text Generation Inference) Tuning Experiments

## Overview
Practical experiments for optimizing TGI (Text Generation Inference) deployment for maximum throughput and minimal latency on Minder Academy infrastructure.

## Experiment 1: TGI Deployment Configuration

### Objective
Deploy and configure TGI with optimal settings for an 11GB VRAM GPU.

### Implementation

```python
# tgi_deployment.py
import subprocess
import requests
import json
import time

class TGIDeployment:
    """Deploy and manage TGI instances"""

    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.model_name = model_name
        self.base_url = "http://localhost:8080"

    def start_tgi_server(self,
                        quantization: str = "awq",
                        max_total_tokens: int = 4096,
                        max_batch_size: int = 32,
                        tensor_parallel_size: int = 1):
        """Start TGI server with optimized parameters"""

        print(f"Starting TGI server for {self.model_name}...")

        cmd = [
            "text-generation-launcher",
            "--model-name", self.model_name,
            "--quantize", quantization,
            "--max-total-tokens", str(max_total_tokens),
            "--max-batch-size", str(max_batch_size),
            "--tensor-parallel-size", str(tensor_parallel_size),
            "--hostname", "0.0.0.0",
            "--port", "8080",
            # Performance optimizations
            "--shuffle-seed", "42",
            "--disable-custom-kernels", "false",
            "--trust-remote-code",
            # Memory optimization
            "--max-batch-pretokenization", "2048",
            # Monitoring
            "--enable-monitoring",
            "--monitoring-port", "8081",
        ]

        print("Command:", " ".join(cmd))

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            print("TGI server starting...")
            time.sleep(10)  # Wait for startup

            if self.check_health():
                print("✅ TGI server started successfully")
                return process
            else:
                print("❌ TGI server failed to start")
                process.terminate()
                return None

        except Exception as e:
            print(f"❌ Error starting TGI: {e}")
            return None

    def check_health(self):
        """Check if TGI server is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_server_info(self):
        """Get TGI server information"""
        try:
            response = requests.get(f"{self.base_url}/info", timeout=5)
            return response.json()
        except Exception as e:
            print(f"Error getting info: {e}")
            return None

    def get_model_info(self):
        """Get model information"""
        try:
            response = requests.get(f"{self.base_url}/model", timeout=5)
            return response.json()
        except Exception as e:
            print(f"Error getting model info: {e}")
            return None


def test_tgi_deployment():
    """Test TGI deployment"""

    print("TGI Deployment Test")
    print("=" * 60)

    tgi = TGIDeployment()

    # Start server
    process = tgi.start_tgi_server()

    if process:
        # Check health
        health = tgi.check_health()
        print(f"Health check: {'✅' if health else '❌'}")

        # Get info
        info = tgi.get_server_info()
        if info:
            print("\nServer Info:")
            print(json.dumps(info, indent=2))

        # Get model info
        model_info = tgi.get_model_info()
        if model_info:
            print("\nModel Info:")
            print(json.dumps(model_info, indent=2))

        # Cleanup
        print("\nPress Ctrl+C to stop...")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping TGI server...")
            process.terminate()


if __name__ == "__main__":
    test_tgi_deployment()
```

---

## Experiment 2: Batch Size Optimization

### Objective
Find optimal batch size for throughput vs latency trade-off.

### Implementation

```python
# batch_optimization.py
import requests
import time
import statistics

class BatchSizeOptimizer:
    """Optimize TGI batch size for best performance"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def generate(self, prompt: str, max_tokens: int = 100, parameters: dict = None):
        """Generate text with TGI"""

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
            }
        }

        if parameters:
            payload["parameters"].update(parameters)

        start_time = time.time()

        response = requests.post(
            f"{self.base_url}/generate",
            json=payload,
            timeout=120
        )

        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            generated_tokens = result.get("details", {}).get("generated_tokens", 0)
            throughput = generated_tokens / duration

            return {
                "success": True,
                "duration": duration,
                "generated_tokens": generated_tokens,
                "throughput": throughput,
                "ttft": result.get("details", {}).get("prefill_time", 0)
            }
        else:
            return {
                "success": False,
                "error": response.text
            }

    def test_batch_size(self, batch_size: int, num_requests: int = 10):
        """Test performance with specific batch size"""

        prompts = [
            "Explain quantum computing in simple terms.",
            "Write a short story about a robot learning to love.",
            "What are the main causes of climate change?",
            "Describe the architecture of transformer models.",
            "How does blockchain technology work?",
            "What is the meaning of life according to philosophy?",
            "Explain the theory of relativity.",
            "Write a poem about artificial intelligence.",
            "What are the benefits of meditation?",
            "How do neural networks learn?"
        ][:num_requests]

        print(f"\nTesting batch_size={batch_size}...")

        start_time = time.time()
        results = []

        for prompt in prompts:
            result = self.generate(prompt)
            results.append(result)

        total_duration = time.time() - start_time

        # Calculate statistics
        successful = [r for r in results if r["success"]]

        if successful:
            avg_latency = statistics.mean([r["duration"] for r in successful])
            avg_ttft = statistics.mean([r["ttft"] for r in successful])
            avg_throughput = statistics.mean([r["throughput"] for r in successful])
            total_throughput = sum([r["generated_tokens"] for r in successful]) / total_duration

            print(f"  Avg Latency: {avg_latency:.2f}s")
            print(f"  Avg TTFT: {avg_ttft:.2f}s")
            print(f"  Avg Throughput: {avg_throughput:.2f} tokens/s")
            print(f"  Total Throughput: {total_throughput:.2f} tokens/s")

            return {
                "batch_size": batch_size,
                "avg_latency": avg_latency,
                "avg_ttft": avg_ttft,
                "avg_throughput": avg_throughput,
                "total_throughput": total_throughput
            }

        return None

    def find_optimal_batch_size(self, batch_sizes: list = [1, 4, 8, 16, 32]):
        """Find optimal batch size"""

        print("Finding Optimal Batch Size")
        print("=" * 60)

        results = []

        for batch_size in batch_sizes:
            result = self.test_batch_size(batch_size)
            if result:
                results.append(result)
            time.sleep(2)  # Cool down between tests

        # Find optimal based on throughput
        if results:
            optimal = max(results, key=lambda x: x["total_throughput"])

            print("\n" + "=" * 60)
            print(f"Optimal Batch Size: {optimal['batch_size']}")
            print(f"  Total Throughput: {optimal['total_throughput']:.2f} tokens/s")
            print(f"  Avg Latency: {optimal['avg_latency']:.2f}s")

            return optimal

        return None


def test_batch_optimization():
    """Test batch size optimization"""

    print("TGI Batch Size Optimization")
    print("=" * 60)

    optimizer = BatchSizeOptimizer()

    # Find optimal batch size
    optimal = optimizer.find_optimal_batch_size([1, 4, 8, 16, 32, 64])

    if optimal:
        print(f"\n✅ Optimal batch size found: {optimal['batch_size']}")


if __name__ == "__main__":
    test_batch_optimization()
```

---

## Experiment 3: Quantization Comparison

### Objective
Compare different quantization methods (AWQ, GPTQ, bitsandbytes) for quality and speed.

### Implementation

```python
# quantization_comparison.py
import requests
import time

class QuantizationComparison:
    """Compare different quantization methods"""

    def __init__(self):
        self.servers = {
            "awq": "http://localhost:8080",
            "gptq": "http://localhost:8081",
            "bnb": "http://localhost:8082"
        }

    def benchmark_server(self, name: str, url: str, prompts: list):
        """Benchmark a specific server"""

        print(f"\nBenchmarking {name.upper()}...")

        results = []

        for prompt in prompts:
            start_time = time.time()

            try:
                response = requests.post(
                    f"{url}/generate",
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 100,
                            "temperature": 0.7
                        }
                    },
                    timeout=30
                )

                duration = time.time() - start_time

                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "latency": duration,
                        "generated_text": result.get("generated_text", ""),
                        "tokens": result.get("details", {}).get("generated_tokens", 0)
                    })

            except Exception as e:
                print(f"  Error: {e}")

        if results:
            avg_latency = sum([r["latency"] for r in results]) / len(results)
            total_tokens = sum([r["tokens"] for r in results])
            throughput = total_tokens / sum([r["latency"] for r in results])

            print(f"  Avg Latency: {avg_latency:.2f}s")
            print(f"  Throughput: {throughput:.2f} tokens/s")

            return {
                "method": name,
                "avg_latency": avg_latency,
                "throughput": throughput
            }

        return None

    def compare_all(self):
        """Compare all quantization methods"""

        print("Quantization Method Comparison")
        print("=" * 60)

        prompts = [
            "Explain what is machine learning.",
            "Write a haiku about computers.",
            "What is the capital of France?",
            "Describe how photosynthesis works.",
            "Why is the sky blue?"
        ]

        results = []

        for name, url in self.servers.items():
            result = self.benchmark_server(name, url, prompts)
            if result:
                results.append(result)

        # Display comparison
        print("\n" + "=" * 60)
        print("Comparison Results:")
        print(f"{'Method':<10} {'Latency':<12} {'Throughput':<12}")
        print("-" * 40)

        for result in results:
            print(f"{result['method']:<10} {result['avg_latency']:<12.2f} {result['throughput']:<12.2f}")

        return results


def test_quantization():
    """Test quantization comparison"""

    print("TGI Quantization Comparison")
    print("=" * 60)

    comparison = QuantizationComparison()
    comparison.compare_all()


if __name__ == "__main__":
    test_quantization()
```

---

## Experiment 4: Memory Optimization

### Objective
Optimize memory usage for fitting larger models on an 11GB VRAM GPU.

### Implementation

```python
# memory_optimization.py
import subprocess
import requests
import json

class MemoryOptimizer:
    """Optimize TGI memory usage"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def get_gpu_memory(self):
        """Get current GPU memory usage"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                used, total = map(int, result.stdout.strip().split(','))
                return {"used": used, "total": total, "free": total - used}

        except Exception as e:
            print(f"Error getting GPU memory: {e}")

        return None

    def get_server_metrics(self):
        """Get TGI server metrics"""
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            return response.text
        except:
            return None

    def test_memory_with_config(self, config: dict):
        """Test memory usage with specific configuration"""

        print(f"\nTesting config: {config['name']}")

        # Get baseline memory
        baseline = self.get_gpu_memory()

        # Generate with config
        prompt = "Write a detailed explanation of how transformers work." * 5
        response = requests.post(
            f"{self.base_url}/generate",
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": config.get("max_tokens", 500),
                    "temperature": 0.7
                }
            },
            timeout=60
        )

        # Get peak memory
        peak_memory = self.get_gpu_memory()

        if baseline and peak_memory:
            memory_used = peak_memory["used"] - baseline["used"]
            print(f"  Memory Used: {memory_used} MB")
            print(f"  Current Usage: {peak_memory['used']} MB / {peak_memory['total']} MB")

            return {
                "config": config["name"],
                "memory_used": memory_used,
                "peak_memory": peak_memory["used"]
            }

        return None

    def optimize_memory_settings(self):
        """Find optimal memory settings"""

        print("TGI Memory Optimization")
        print("=" * 60)

        configs = [
            {"name": "conservative", "max_tokens": 100},
            {"name": "moderate", "max_tokens": 300},
            {"name": "aggressive", "max_tokens": 500},
        ]

        results = []

        for config in configs:
            result = self.test_memory_with_config(config)
            if result:
                results.append(result)
            time.sleep(2)

        # Find best config
        if results:
            print("\n" + "=" * 60)
            print("Results:")
            for result in results:
                print(f"{result['config']}: {result['memory_used']} MB")

        return results


def test_memory_optimization():
    """Test memory optimization"""

    print("TGI Memory Optimization")
    print("=" * 60)

    optimizer = MemoryOptimizer()
    optimizer.optimize_memory_settings()


if __name__ == "__main__":
    test_memory_optimization()
```

---

## Quick Start

### Deploy TGI with AWQ Quantization

```bash
# Pull TGI Docker image
docker pull ghcr.io/huggingface/text-generation-inference:latest

# Start TGI server
docker run -d --gpus all \
  -p 8080:80 \
  -v /srv/models:/models \
  --name tgi-mistral \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2 \
  --quantize awq \
  --max-total-tokens 4096

# Check health
curl http://localhost:8080/health
```

### Run Batch Size Tests

```bash
# Find optimal batch size
python batch_optimization.py
```

---

## Expected Results

### Performance Targets (11GB VRAM GPU)

| Metric | Target | Acceptable |
|--------|--------|------------|
| **TTFT** | <500ms | <1s |
| **Throughput** | 30+ tokens/s | 20+ tokens/s |
| **Memory** | <10GB | <11GB |
| **Batch Size** | 16-32 | 8-16 |

### Quantization Comparison

| Method | VRAM | Speed | Quality | Best For |
|--------|------|-------|---------|----------|
| **AWQ** | 5GB | 35 t/s | 98% | Production |
| **GPTQ** | 5GB | 32 t/s | 97% | Accuracy |
| **bitsandbytes** | 6GB | 28 t/s | 96% | Flexibility |

---

## Experiment Checklist

- [ ] TGI server deployment
- [ ] Health check verification
- [ ] Batch size optimization
- [ ] Quantization comparison
- [ ] Memory usage analysis
- [ ] Latency measurement
- [ ] Throughput benchmarking
- [ ] Concurrent request testing
- [ ] Long context testing
- [ ] Production configuration

---

## Related Documentation

- [1402: vLLM and TGI](../docs/phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [1403: vLLM Production Deployment](../docs/phases/phase1-infra/1400-llmops/guides/1403-vLLM-Production-Deployment.md)
- [4102: EXL2 and AWQ](../docs/phases/phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md)
- [4402: AWQ](../docs/phases/phase4-quantization/4400-advanced-techniques/4402-AWQ.md)
