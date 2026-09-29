---
Document ID: 4409
Title: "4409: Hardware-Specific Quantization Optimization"
Phase: 4
Module: 4400
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'hardware', 'inference', 'deployment', 'benchmarking']
---

# 4409: Hardware-Specific Quantization Optimization

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Format × Hardware Map](#the-format--hardware-map)
- [NVIDIA GPU](#nvidia-gpu)
- [AMD GPU](#amd-gpu)
- [Apple Silicon](#apple-silicon)
- [x86 and ARM CPU](#x86-and-arm-cpu)
- [Mobile and NPU: The Reality Check](#mobile-and-npu-the-reality-check)
- [Benchmarking Across Hardware](#benchmarking-across-hardware)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Pick the quantization format AND runtime for a given deployment target from the 2026 pairing table, and say which pairings are simply unsupported
- Serve a quantized model on NVIDIA datacenter GPUs (vLLM, GPTQ/AWQ/FP8) and shard an oversized model across consumer GPUs with the correct `max_memory` API
- Build and run llama.cpp on Apple Silicon and x86/ARM CPUs with the current toolchain (cmake build, `llama-quantize`, `llama-cli`, `llama-bench`)
- Explain why mobile/NPU "INT4 LLM" claims need qualification — which stacks are real (MLC-LLM, ExecuTorch, QNN), what they actually quantize, and why Edge TPU-class parts cannot run LLMs at all
- Benchmark quantized models fairly: decode token rate, TTFT, and peak memory on the TARGET hardware, with the same harness for every candidate

---

## Abstract

The same INT4 checkpoint can be fast on one device and unusable on another, because quantization only pays when a kernel exists for that format on that silicon. This guide is the deployment-side companion to [4408](4408-Quantizing-for-Production.md): it maps every major hardware target to the format + runtime pairing that actually works in 2026 — vLLM with GPTQ/AWQ or FP8 for datacenter NVIDIA, GGUF over Metal for Apple Silicon, native-built llama.cpp for CPUs — and walks the working commands for each. It also does the unglamorous work tutorial sites skip: correcting the mobile/NPU story (which stacks are real and what they really quantize), and establishing a benchmarking harness that measures decode rate, time-to-first-token, and peak memory so hardware decisions rest on numbers rather than emoji tables.

## The Format × Hardware Map

Quantization wins are kernel wins: a format is only as fast as its runtime support on that silicon.

```text
Target                    Format              Runtime              Notes
------------------------  ------------------  -------------------  -------------------------
NVIDIA datacenter         GPTQ/AWQ W4A16      vLLM                 throughput serving
(A100/H100)               FP8 (W8A8)          vLLM                 H100-class: near-lossless
                          (GGUF does NOT run here - no kernel path)

Local NVIDIA GPU          EXL2                exllamav2            single-user, best bpw
                          GGUF                llama.cpp (CUDA)     or llama.cpp server

AMD GPU (ROCm)            GGUF                llama.cpp (ROCm)     INT4 GPTQ/AWQ kernels are
                          FP16/16-bit         vLLM (ROCm)          NVIDIA-first; check before
                                                                   planning an AMD 4-bit deploy

Apple Silicon             GGUF                llama.cpp (Metal)    unified memory = big models
                          MLX quants          MLX                  Apple's own stack

x86 CPU                   GGUF                llama.cpp            native build; NUMA servers
ARM CPU                   GGUF                llama.cpp            NEON auto-enabled

Mobile (Android/iOS)      q4f16 (MLC)         MLC-LLM              full-stack mobile compile
                          INT4 (ExecuTorch)   ExecuTorch           PyTorch edge runtime
                          8/4-bit (QNN)       Qualcomm AI Engine   SoC NPU path, hardest

Edge TPUs (Coral-class)   -                   -                    NOT an LLM target (8MB
                                                                   SRAM; vision-scale models)
```

The rest of the guide works through the rows that matter most, in that order.

## NVIDIA GPU

### Datacenter serving: vLLM owns this row

```bash
# pre-quantized GPTQ/AWQ checkpoint (made in 4408)
vllm serve ./models/llama-2-7b-w4a16-gptq --dtype float16

# tensor parallel across 4 GPUs for throughput
vllm serve ./models/llama-2-7b-w4a16-gptq --tensor-parallel-size 4

# H100-class: FP8 at load time - near-lossless W8A8, no calibration
vllm serve meta-llama/Llama-2-7b-hf --quantization fp8
```

```text
- the serving decision beats the bit decision: a W4A16 model in
  vLLM (continuous batching + paged KV) out-serves the same
  weights in any single-stream runner by an order of magnitude
  at load
- FP8 on Hopper is the format to evaluate FIRST for datacenter
  work - it keeps activations at 8 bits too, needs no
  calibration set, and lands within noise of FP16 on most
  quality gates (4408 Step 5 verifies this per model)
```

### Multi-GPU layer sharding (transformers)

```python
import torch
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto",                     # pipeline-style layer split
    max_memory={0: "20GiB", 1: "24GiB"},   # per-GPU budget
)
```

```text
device_map="auto" shreds LAYERS across GPUs (pipeline parallel):
simple, but every token traverses GPUs serially, so throughput
does not scale with card count. vLLM's --tensor-parallel-size
splits each layer across GPUs and DOES scale - prefer it
whenever you serve rather than merely load.

TF32 for Ampere+ (training/misc compute):
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
```

## AMD GPU

```text
The honest 2026 picture
- llama.cpp with ROCm (HIP) backend: the dependable AMD path for
  quantized GGUF models; Vulkan backend as the fallback for
  consumer cards
- vLLM runs on ROCm (Instinct-class parts); INT4 GPTQ/AWQ kernel
  coverage there is narrower than on NVIDIA - benchmark the
  specific format before committing
- 2:4 sparsity and FP8 are NVIDIA/other-vendor features; AMD
  MI-series has neither (4405)
Rule: on AMD, plan around GGUF + llama.cpp until you have
measured otherwise on YOUR card.
```

## Apple Silicon

### GGUF over Metal (the working path)

```bash
# build (Metal is auto-enabled on Apple Silicon; cmake is the
# current build system - the old makefile flow is gone)
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release

# convert + quantize (converter runs on the Mac fine)
python convert_hf_to_gguf.py ./Llama-2-7b-hf \
    --outfile base-f16.gguf --outtype f16
./build/bin/llama-quantize base-f16.gguf llama-2-7b-Q4_K_M.gguf Q4_K_M

# run with full GPU offload
./build/bin/llama-cli -m llama-2-7b-Q4_K_M.gguf \
    -ngl 99 -t 8
```

```text
Why Macs punch above their watts for LLMs
- unified memory: a 64GB M-series machine holds the WHOLE model
  where a 24GB NVIDIA card cannot - CPU/GPU copies disappear
- Q4_K_M is the community sweet spot; Q5_K_M when quality gates
  (4408 Step 5) are tight
- -ngl 99 offloads every layer to the GPU; partial offloads
  trade tokens/sec for memory and are worth benchmarking only
  under memory pressure
```

### Core ML / ANE: the honest note

```text
Running an LLM on the Apple NEURAL Engine is a research-grade
pipeline, not a llama.cpp one-liner: full-graph compilation
with static KV-cache shapes, per-op support checks, and Apple's
own example converters as the reference. Generic
coremltools.convert(causal_lm) does not produce a working LLM.
In practice, quantized LLMs on Macs run on the GPU via Metal -
treat ANE as a roadmap item, not a deployment option.
```

## x86 and ARM CPU

```bash
# native build: CPU feature flags (AVX2/AVX-512/NEON) are
# auto-detected for the BUILD machine - hand-tuning -DGGML_*
# vars is legacy guidance
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build && cmake --build build --config Release

# NUMA server: bind memory to the socket running the threads
numactl --cpunodebind=0 --membind=0 \
    ./build/bin/llama-server -m llama-2-7b-Q4_K_M.gguf -t 32

# memory-constrained box: lock pages, disable swap-out
./build/bin/llama-cli -m llama-2-7b-Q4_K_M.gguf \
    -t 16 --mlock

# microbenchmark formats on YOUR cpu (the llama.cpp benchmark tool)
./build/bin/llama-bench -m llama-2-7b-Q4_K_M.gguf -p 512 -n 128
```

```text
CPU decode is memory-bandwidth-bound: tokens/sec tracks model
size in bytes, which is exactly why quantization matters most
here - Q4_K_M roughly doubles the decode rate of Q8_0 on the
same DDR5 channel.
Practical knobs, in order of impact:
1. threads = PHYSICAL cores (SMT threads help prefill, often
   hurt decode)
2. one numa node's worth of cores + --membind, or --numa
   distribute for multi-socket
3. Q4_K_M over Q4_0/Q5 - the K-quants are built for CPU kernels
4. llama-bench before and after every knob change
```

## Mobile and NPU: The Reality Check

This row is where marketing and engineering diverge most. What is actually true:

```text
REAL and usable today
- MLC-LLM (TVM Unity): compiles a model INTO a phone app for
  Adreno/Mali/Apple GPUs. Flow: convert weights to the MLC
  format -> generate per-device config -> package (their CLI
  does this per target; Android and iOS both ship). q4f16
  quantization is the mobile sweet spot
- ExecuTorch: PyTorch's edge runtime; quantized (INT4
  weight-only) LLM recipes for mobile CPU/GPU delegates
- Qualcomm AI Engine Direct (QNN): 8-bit (and newer 4-bit
  weight) paths to the Hexagon NPU - the performance ceiling
  on Snapdragon, and the highest-effort integration (per-model
  graph conversion, fixed shapes)

REAL but commonly misadvertised
- "INT4 on NPU" usually means WEIGHTS at 4-bit with 8/16-bit
  compute - the activation side is not 4-bit. Compression and
  bandwidth story, not a full 4-bit datapath

NOT an LLM target
- Google Edge TPU / Coral-class parts: 8MB on-chip SRAM for
  vision-scale CNNs. No LLM has ever run there. If a guide
  lists "Edge TPU" for LLM quantization, it is wrong
- Huawei Ascend: real LLM silicon (CANN toolchain, torch_npu
  for training/inference, MindIE for serving) - but it is a
  datacenter-class stack, not a "quantize and go" edge row
```

```text
Mobile deployment triage
1. can it run in MLC-LLM's supported list? -> fastest path
2. PyTorch shop with existing model code?     -> ExecuTorch
3. Snapdragon NPU required for power budget? -> QNN, budget
   weeks for graph conversion and shape pinning
4. context length: mobile KV cache is the real memory hog -
   cap context aggressively (2-4k) and stream generation
```

## Benchmarking Across Hardware

The same harness on every candidate, three numbers, no exceptions:

```python
import time
import torch

@torch.no_grad()
def benchmark_llm(model, tokenizer, prompt,
                  new_tokens=256, warmup=3, iters=5):
    """Three numbers that describe LLM hardware fit:
    decode token rate, time-to-first-token, peak memory."""
    device = next(model.parameters()).device
    ids = tokenizer(prompt, return_tensors="pt").to(device)

    for _ in range(warmup):                     # caches, kernels
        model.generate(**ids, max_new_tokens=16)

    torch.cuda.reset_peak_memory_stats()

    t0 = time.perf_counter()
    for _ in range(iters):
        model.generate(**ids, max_new_tokens=new_tokens)
    decode_tps = iters * new_tokens / (time.perf_counter() - t0)

    t0 = time.perf_counter()
    model.generate(**ids, max_new_tokens=1)
    ttft_ms = (time.perf_counter() - t0) * 1000

    peak_gb = torch.cuda.max_memory_allocated() / 1e9
    return {"decode_tok_s": round(decode_tps, 1),
            "ttft_ms": round(ttft_ms, 1),
            "peak_mem_gb": round(peak_gb, 2)}
```

```text
Reading the three numbers
- decode_tok_s  steady-state generation speed (bandwidth-bound)
- ttft_ms       prefill cost - dominates UX on long prompts and
                scales with batch size under load
- peak_mem_gb   the number that decides WHICH GPU you can buy
All three move differently per format - a format that wins
decode can lose TTFT; measure, never assume.

Honest-comparison rules
1. same harness, same prompt lengths, same new-token counts
2. benchmark on the TARGET hardware, not "similar" hardware
3. transformers generate() numbers are NOT serving numbers -
   for production claims, use the serving stack's benchmark
   (vLLM benchmark_serving, llama-bench for llama.cpp)
4. report percentiles, not averages (p50/p95/p99 TTFT)
```

## Best Practices

```text
1. Decide format and runtime TOGETHER - a format without a
   kernel on your target silicon is a paper feature
2. Datacenter NVIDIA: vLLM first; evaluate FP8 (H100+) before
   INT4; do not put GGUF on a datacenter GPU
3. Mac/CPU/AMD: GGUF + llama.cpp is the dependable path; build
   NATIVE (auto CPU flags), benchmark with llama-bench
4. Multi-GPU: device_map="auto" loads what nothing else can;
   tensor parallel serves what throughput demands
5. Mobile: MLC-LLM or ExecuTorch for app integration, QNN for
   the NPU ceiling; "4-bit" means weights-only - cap context
   because the KV cache is the memory hog
6. Edge TPU-class parts cannot run LLMs; do not schedule work
   around them
7. Never ship a hardware decision on one number: decode rate +
   TTFT + peak memory, on target hardware, p95s included
```

---

## References

### Related PROJECT-OMEGA Documents

- [4401: GPTQ](../4401-GPTQ.md)
- [4403: GGUF Format](../4403-GGUF-Format.md)
- [4404: EXL2 Format](../4404-EXL2-Format.md)
- [4405: Sparsity + Quantization](../4405-Sparsity-Quantization.md)
- [4408: Quantizing for Production](4408-Quantizing-for-Production.md)

---

## Next Steps

- Module 4400 complete — Return to: **[Module README](../README.md)**
- Assessment: **[assessment/QUIZ.md](../assessment/QUIZ.md)**
