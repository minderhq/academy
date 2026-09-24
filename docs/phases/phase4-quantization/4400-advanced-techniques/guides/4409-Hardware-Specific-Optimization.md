---
Document ID: 4409
Title: "4409: Hardware-Specific Quantization Optimization"
Phase: 4
Module: 4400
Last Updated: 2026-09-24
Status: Review
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: 4101, 4401
Related: 4408
Tags: ['quantization', 'hardware', 'optimization']
---

# 4409: Hardware-Specific Quantization Optimization

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Hardware Matrix](#hardware-matrix)
- [NVIDIA GPU Optimization](#nvidia-gpu-optimization)
- [Apple Silicon Optimization](#apple-silicon-optimization)
- [CPU Optimization](#cpu-optimization)
- [Mobile Optimization](#mobile-optimization)
- [NPU Optimization (Edge TPUs, etc.)](#npu-optimization-edge-tpus-etc)
- [Benchmarking](#benchmarking)
- [Hardware-Specific Tips](#hardware-specific-tips)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Hardware Matrix
- Explain NVIDIA GPU Optimization
- Explain Apple Silicon Optimization
- Explain CPU Optimization
- Explain Mobile Optimization
- Explain NPU Optimization (Edge TPUs, etc.)

---

## Abstract

Different hardware platforms require different quantization strategies. This guide covers CPU, GPU, NPU, and mobile optimization.

## Hardware Matrix

| Platform | Recommended Format | Tools | Speed | Memory |
|----------|-------------------|-------|-------|--------|
| **NVIDIA GPU** | INT4/INT8 GPTQ | AutoGPTQ, EXL2 | ⚡⚡⚡ | ⚡⚡⚡ |
| **AMD GPU** | INT4 GGUF | llama.cpp, Vulkan | ⚡⚡ | ⚡⚡ |
| **Apple Silicon** | INT4 GGUF | llama.cpp, Metal | ⚡⚡⚡ | ⚡⚡⚡ |
| **x86 CPU** | INT4 GGUF | llama.cpp, AVX2 | ⚡ | ⚡⚡ |
| **ARM CPU** | INT4 GGUF | llama.cpp, NEON | ⚡ | ⚡⚡ |
| **Mobile** | INT4 GGUF | MLC-LLM, QNN | ⚡⚡ | ⚡⚡⚡ |
| **NPU** | INT4/INT8 | QNN, SNPE | ⚡⚡⚡ | ⚡⚡⚡ |

## NVIDIA GPU Optimization

### 1. EXL2 Format (Best for NVIDIA)

```bash
# Convert to EXL2 for optimal NVIDIA performance
# EXL2 uses CUDA kernels specifically optimized for Tensor Cores

# Install exllamav2
pip install exllamav2

# Convert model
python -m exllamav2.convert \
    --in /path/to/model \
    --out /path/to/output \
    --bf --quant 4.0

# Run inference
python -m exllamav2.chat \
    --model-path /path/to/output \
    --gpu-split 18,18  # For dual GPU setup
```

### 2. GPTQ Format (Alternative)

```python
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
from transformers import AutoTokenizer

# Configuration for NVIDIA A100/H100
quantize_config = BaseQuantizeConfig(
    bits=4,
    group_size=128,
    damp_percent=0.01,
    desc_act=False,
    sym=True,
    true_sequential=True,
    model_name_base='llama',
)

# Load and quantize
model = AutoGPTQForCausalLM.from_pretrained(
    pretrained_model_dir,
    quantize_config=quantize_config,
    use_triton=True,  # Enable Triton kernels
    use_flash_attention_2=True,  # Flash Attention
)

# Optimize for NVIDIA
model.quantize(
    calibration_data,
    batch_size=1,
    use_triton=True,
)
```

### 3. Multi-GPU Optimization

```python
import torch
from accelerate import dispatch_model

def setup_multi_gpu(model):
    """Optimize for multi-GPU NVIDIA setup."""

    # GPU memory map (in GB for each GPU)
    gpu_memory = {
        'gpu:0': 20,  # RTX 3090
        'gpu:1': 20,  # RTX 3090
        'gpu:2': 24,  # RTX 4090
    }

    # Device map for optimal distribution
    device_map = dispatch_model(
        model,
        device_map='auto',
        gpu_memory=gpu_memory
    )

    return model.to(device_map)

# Enable CUDA optimizations
torch.backends.cudnn.enabled = True
torch.backends.cudnn.benchmark = True
torch.backends.cuda.matmul.allow_tf32 = True
```

## Apple Silicon Optimization

### 1. GGUF with Metal (M1/M2/M3)

```bash
# Build llama.cpp with Metal support
cd llama.cpp
make

# Quantize for Apple Silicon
./quantize \
    /path/to/model/ggml-model-f16.gguf \
    /path/to/output/model-q4_0.gguf \
    Q4_K_M

# Run with Metal acceleration
./main -m model-q4_0.gguf \
    -n 512 \
    -ngl 99 \  # Number of layers to offload to GPU
    --threads 8 \
    --tensor-cores
```

### 2. Core ML Optimization

```python
import coremltools as ct
from transformers import AutoModelForCausalLM

# Load model
model = AutoModelForCausalLM.from_pretrained("model-name")

# Convert to Core ML
mlmodel = ct.convert(
    model,
    source="pytorch",
    inputs=[ct.TensorType(shape=(1, 512), dtype=np.int32)],
    outputs=[ct.TensorType(shape=(1, 512, vocab_size))],
    # Optimize for Apple Neural Engine
    compute_precision=ct.precision.FLOAT16
)

# Set minimum deployment target
mlmodel.spec.description.metadata.shortDescription = (
    "Quantized LLM for Apple Silicon"
)

# Save
mlmodel.save("model.mlpackage")
```

## CPU Optimization

### 1. x86_64 with AVX-512

```bash
# Build llama.cpp with AVX-512 support
cd llama-python
CMAKE_ARGS="-DGGML_AVX512=ON" pip install llama-cpp-python

# Run with AVX-512 optimization
python -m llama_cpp \
    --model model-q4_k.gguf \
    --n-gpu-layers 0 \
    --threads 16 \
    --tensor-cores
```

### 2. ARM64 with NEON

```bash
# For Apple Silicon or ARM servers
cd llama.cpp
make LLAMA_NEON=1

# Optimize for ARM
./main -m model-q4_0.gguf \
    -n 512 \
    -ngl 0 \
    --threads 8 \
    --mlock \  # Lock memory
    --numa distribute  # NUMA-aware scheduling
```

### 3. NUMA Optimization for Servers

```bash
# For multi-socket AMD EPYC or Xeon servers
numactl --cpunodebind=0 --membind=0 \
    ./main -m model-q4_0.gguf

# Or distribute across NUMA nodes
numactl --interleave=all \
    ./main -m model-q4_0.gguf
```

## Mobile Optimization

### 1. Android with MLC-LLM

```python
# Convert to MLC format for Android
import mlc_llm

# Build for Android
mlc_llm.build(
    model="Llama-2-7b-chat-hf",
    quantization="q4f16_1",  # Mobile-optimized format
    target="android",  # or "ios"
    # Options: adreno, mali, apple-gpu
    device="adreno",
)

# Generate APK
mlc_llm.package(
    model="Llama-2-7b-chat-hf-q4f16_1",
    output="llm_chat.apk",
)
```

### 2. iOS with Core ML

```bash
# Convert model for iOS
coremltools convert \
    --source model \
    --target iOS \
    --quantize INT4 \
    --output model.mlmodel

# Integrate into iOS app
# In Swift:
import CoreML

let model = try! LLMQuantized(configuration: MLModelConfiguration())
let input = LLMQuantizedInput(tokens: tokenIds)
let output = try! model.prediction(input: input)
```

### 3. Android NPU with QNN (Qualcomm)

```python
# Qualcomm Neural Processing Engine
import snpe

# Convert to QNN DLC format
snpe.convert_to_dlc(
    model_path="model.onnx",
    input_dim="1,512",
    output_path="model.dlc"
)

# Quantize for NPU
snpe.dlc_quantize(
    input_dlc="model.dlc",
    output_dlc="model_quantized.dlc",
    quantization_level="int4"  # or "int8"
)

# Deploy on Android
adb push model_quantized.dlc /data/local/tmp/
snpe-net-run --container model_quantized.dlc
```

## NPU Optimization (Edge TPUs, etc.)

### 1. Google Edge TPU

```bash
# Convert to TFLite for Edge TPU
edgetpu_compiler \
    --model_file model.tflite \
    --output_model model_edgetpu.tflite

# Deploy on Coral Dev Board
python3 edgetpu_classify.py \
    --model model_edgetpu.tflite \
    --labels labels.txt
```

### 2. Huawei Ascend NPU

```python
# Use CANN (Compute Architecture for Neural Networks)
import torch_npu

# Convert to NPU format
model = model.to('npu:0')

# Enable NPU optimizations
torch.npu.set_option("OPT_ENABLENPUOPT", "1")

# Mixed precision for NPU
from npu_bridge.npu_model import NpuModel
npu_model = NpuModel(model, "npu:0")
```

## Benchmarking

### 1. Token Throughput Benchmark

```python
import time
import torch

def benchmark_inference(model, tokenizer, prompt, n_tokens=512):
    """Benchmark tokens per second."""

    # Warmup
    _ = model.generate(**tokenizer(prompt, return_tensors="pt"))

    # Actual benchmark
    start = time.time()

    output = model.generate(
        **tokenizer(prompt, return_tensors="pt"),
        max_new_tokens=n_tokens,
        do_sample=True
    )

    elapsed = time.time() - start
    tokens_per_second = n_tokens / elapsed

    return tokens_per_second

# Test on different hardware
for device in ['cuda', 'cpu', 'npu']:
    model = model.to(device)
    tps = benchmark_inference(model, tokenizer, "Hello world")
    print(f"{device}: {tps:.2f} tokens/sec")
```

### 2. Memory Profiling

```python
def profile_memory(model):
    """Profile memory usage by layer."""

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()

    # Get memory usage
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        reserved = torch.cuda.memory_reserved() / 1e9
        peak = torch.cuda.max_memory_allocated() / 1e9

        print(f"GPU Memory:")
        print(f"  Allocated: {allocated:.2f} GB")
        print(f"  Reserved:  {reserved:.2f} GB")
        print(f"  Peak:      {peak:.2f} GB")

    # Layer-wise memory
    for name, module in model.named_modules():
        if hasattr(module, 'weight'):
            weight_size = module.weight.numel() * module.weight.element_size()
            print(f"{name}: {weight_size / 1e6:.2f} MB")
```

## Hardware-Specific Tips

### NVIDIA GPU Best Practices
- Use EXL2 format for best performance
- Enable Flash Attention 2
- Offload all layers to GPU if memory allows
- Use Triton kernels for custom ops
- Enable TF32 for Ampere+

### Apple Silicon Best Practices
- Use GGUF Q4_K_M format
- Enable Metal acceleration (-ngl 99)
- Offload all 33 layers for M2/M3
- Use Unified Memory for large models

### CPU Best Practices
- Use AVX-512 for Intel, AVX2 for AMD
- Enable NUMA-aware scheduling
- Lock memory with mlock
- Use all physical cores
- Disable hyperthreading for memory-bound tasks

### Mobile Best Practices
- Use INT4 quantization
- Offload to NPU when available
- Reduce context window
- Use streaming generation
- Implement prompt caching

---

**Next:** [Assessment](../assessment/QUIZ.md)

**Last Updated:** 2026-02-05

## References

### Related ai-engineering-curriculum Documents

- [4408: Quantizing for Production](4408-Quantizing-for-Production.md)

---