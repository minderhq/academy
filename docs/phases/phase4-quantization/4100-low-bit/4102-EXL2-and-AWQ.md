---
Document ID: 4102
Title: "4102: EXL2 and AWQ - Extreme Quantization"
Phase: 4
Module: 4100
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'gguf', 'exl2', 'awq', 'compression']
---

# 4102: EXL2 and AWQ - Extreme Quantization

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [EXL2 (ExLlamaV2)](#exl2-exllamav2)
- [AWQ (Activation-aware Weight Quantization)](#awq-activation-aware-weight-quantization)
- [GPTQ (Gradient-based Quantization)](#gptq-gradient-based-quantization)
- [Comparison](#comparison)
- [Advanced Techniques](#advanced-techniques)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Configure EXL2 conversions with `convert.py -i -o -b` — one AVERAGE-BPW target per run (the converter's measurement pass picks the per-layer mix; there is no comma-separated `-b` list and no per-layer DSL) — and read the 2.0-8.0 bpw ladder's VRAM-per-quality step
- Load EXL2 checkpoints with the ExLlamaV2 stack (Config → ExLlamaV2 → ExLlamaV2Cache → ExLlamaV2DynamicGenerator) and attribute the ~2x speedup over GGUF Q4_K (90 vs 45 tok/s at 7B) to its CUDA-tensor-core layout
- Implement AWQ's salient-weight rule — calibration activation scales × weight magnitudes select the top 1% kept in fp16 — and account for its 2-3% perplexity cost against GPTQ's 5-7%
- Quantize with GPTQ via `optimum-cli export llama --format gptq --bits 4 --group-size 128 --dataset c4`, explaining its Hessian-driven, block-wise, calibration-dependent nature
- Read the method table to select per scenario — AWQ (+3%) for quality or EXL2 4.5 (+4%) for speed at 7B, EXL2 4.0 for 13B, GGUF Q4_K hybrid for 34B (not recommended on an 11GB-class GPU) — then refine with the two real levers, the average (`-b`) and the head bits (`-hb`)

---

## Abstract
EXL2 and AWQ are advanced quantization methods optimized for GPU-only inference. They provide near-fp16 quality at 4-bit precision, making them ideal for an 11GB-class GPU.

## EXL2 (ExLlamaV2)

### What is EXL2?
```text
EXL2 is a custom quantization format for ExLlamaV2:

- Designed specifically for GPU inference
- Optimized for CUDA tensor cores
- Variable bit rate per layer
- Very fast loading and inference
- Supports 2-8 bit quantization
```

### EXL2 Output Format
```text
An EXL2 "model" is an ordinary HF-style output DIRECTORY —
there is no .exl2 container file:

llama-3.1-8b-exl2/
├── config.json             # Model config (quantization_config notes BPW)
├── tokenizer.model         # Tokenizer
├── output.safetensors      # Quantized weights (sharded when large)
└── measurement.json        # The measurement pass's per-layer
                            # sensitivity scores (reused on resume)
```

### EXL2 Quantization Levels
```python
EXL2_QUANT_LEVELS = {
    2.0: {"description": "2-bit", "vram_8b": "~2GB", "quality": "Poor"},
    3.0: {"description": "3-bit", "vram_8b": "~3GB", "quality": "Fair"},
    4.0: {"description": "4-bit", "vram_8b": "~4GB", "quality": "Good"},
    4.125: {"description": "4.125-bit", "vram_8b": "~4.1GB", "quality": "Very Good"},
    4.5: {"description": "4.5-bit", "vram_8b": "~4.5GB", "quality": "Excellent"},
    5.0: {"description": "5-bit", "vram_8b": "~5GB", "quality": "Near fp16"},
    6.0: {"description": "6-bit", "vram_8b": "~6GB", "quality": "Almost fp16"},
    8.0: {"description": "8-bit", "vram_8b": "~8GB", "quality": "fp16"},
}

# Recommended for an 11GB VRAM GPU:
# - Llama-3.1-8B: 4.5 or 5.0 bpw
# - Gemma-3-12B: 4.0 bpw
# - Mistral-7B: 4.5 bpw
# - Mixtral-8x7B: 3.5 bpw (barely fits)
```

### Converting to EXL2
```bash
# Install ExLlamaV2 (the v2 repo is archived; development continues
# on ExLlamaV3 at turboderp-org/exllamav3 — same conversion flow)
uv pip install exllamav2

# Convert model to EXL2: -i source dir, -o output dir (also the
# converter's scratch space), -b ONE average-BPW target, -c parquet
# calibration dataset (omit for the built-in default)
python convert.py \
  -i /models/llama-3.1-8b \
  -o /models/llama-3.1-8b-exl2 \
  -c calibration_data.parquet \
  -b 4.5  # Bits per weight (average)

# For a different quality/speed point, re-run with a new average and
# higher head bits — the measurement pass then redistributes the
# per-layer 2/3/4/5/6/8-bit mix to land on your target
python convert.py \
  -i /models/mixtral-8x7b \
  -o /models/mixtral-8x7b-exl2 \
  -b 3.5 -hb 8
# There is no per-layer CLI: "Attention: 4-bit, FFN: 3.5-bit" is not a
# thing you steer — no comma-separated -b list exists
```

### Using EXL2 with ExLlamaV2
```python
from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Tokenizer,
    ExLlamaV2Cache,
)
from exllamav2.generator import ExLlamaV2DynamicGenerator, ExLlamaV2Sampler

# Load model
config = ExLlamaV2Config()
config.model_dir = "/models/llama-3.1-8b-exl2"
config.max_seq_len = 4096

model = ExLlamaV2(config)
model.load()

# Tokenizer
tokenizer = ExLlamaV2Tokenizer(config)

# Cache (lazy defers allocation until the first token)
cache = ExLlamaV2Cache(model, max_seq_len=4096, lazy=True)

# Inference — keyword args in that order: model, cache, tokenizer
generator = ExLlamaV2DynamicGenerator(
    model=model,
    cache=cache,
    tokenizer=tokenizer,
)
settings = ExLlamaV2Sampler.Settings()
settings.temperature = 0.7
settings.top_p = 0.9
settings.top_k = 40

text = generator.generate(
    "Once upon a time",
    gen_settings=settings,
    max_new_tokens=256,
    add_bos=True,
)
print(text)
```

### EXL2 Performance
```text
11GB-class GPU (11GB VRAM):
Llama-3.1-8B @ 4.5 bpw:
  - Model size: ~4.5 GB
  - Speed: ~80-100 tokens/sec
  - Quality: Perplexity within 5% of fp16

Gemma-3-12B @ 4.0 bpw:
  - Model size: ~6 GB
  - Speed: ~40-50 tokens/sec
  - Quality: Perplexity within 8% of fp16

Comparison (same hardware):
  - GGUF Q4_K: ~45 tokens/sec
  - EXL2 4.5: ~90 tokens/sec
  - Speedup: ~2x
```

## AWQ (Activation-aware Weight Quantization)

### What is AWQ?
```text
AWQ (Activation-aware Weight Quantization):
- Observes activation statistics during calibration
- Only quantizes 1% of weights (salient weights)
- Keeps important weights in fp16
- Achieves near-fp16 perplexity at 4-bit

Key insight: Not all weights are equal!
- 1% of weights carry 50% of the information
- Keep those 1% in high precision
- Quantize the rest
```

### AWQ Algorithm
```python
import torch
def awq_quantize(layer, calibration_data):
    """
    Activation-aware Weight Quantization
    """
    # 1. Collect activation statistics
    activations = []
    with torch.no_grad():
        for batch in calibration_data:
            act = layer.forward_hook(batch)
            activations.append(act.abs().mean(dim=0))

    activation_scale = torch.cat(activations).mean(dim=0)

    # 2. Identify salient weights
    # Salient = high activation × high magnitude
    weight_magnitude = layer.weight.abs()
    saliency = activation_scale * weight_magnitude

    # 3. Select top 1% salient weights
    num_weights = layer.weight.numel()
    num_keep = int(num_weights * 0.01)

    _, indices = torch.topk(saliency.flatten(), num_keep)
    keep_mask = torch.zeros_like(saliency, dtype=torch.bool)
    keep_mask.view(-1)[indices] = True

    # 4. Quantize non-salient weights
    quantized = layer.weight.clone()
    quantized[~keep_mask] = quantize_4bit(quantized[~keep_mask])
    quantized[keep_mask] = quantized[keep_mask].to(torch.float16)

    return quantized, keep_mask
```

### AWQ Implementation (AutoAWQ)
```bash
# Install AutoAWQ
uv pip install autoawq

# Quantize model
python -m awq.quantize \
  --model_path /models/llama-3.1-8b \
  --w_bit 4 \
  --q_group_size 128 \
  --output_dir /models/llama-3.1-8b-awq

# Parameters:
# --w_bit: Bit width (4 recommended)
# --q_group_size: Group size for quantization (128)
```

### Using AWQ Models
```python
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

# Load quantized model
model = AutoAWQForCausalLM.from_quantized(
    "/models/llama-3.1-8b-awq",
    fuse_layers=True,      # Fuse for speed
    max_new_tokens=512,
    batch_size=1,
)

tokenizer = AutoTokenizer.from_pretrained("/models/llama-3.1-8b-awq")

# Inference
prompt = "Explain quantum computing:"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

output = model.generate(
    **inputs,
    max_new_tokens=256,
    temperature=0.7,
    top_p=0.9,
)

print(tokenizer.decode(output[0]))
```

### AWQ Performance
```text
Llama-3.1-8B AWQ @ 4-bit:
  - VRAM usage: ~4.5 GB
  - Perplexity: Within 2% of fp16
  - Speed: ~55-65 tokens/sec on an 11GB-class GPU

Comparison with other 4-bit methods:
  - GPTQ: 5-7% perplexity increase
  - AWQ: 2-3% perplexity increase
  - EXL2: 3-5% perplexity increase
```

## GPTQ (Gradient-based Quantization)

### GPTQ Overview
```text
GPTQ: Post-Training Quantization with Gradient Information
- Uses Hessian information for optimal quantization
- Second-order optimization
- Block-wise quantization
- Requires calibration data
```

### GPTQ Quantization
```python
# uv pip install auto-gptq — the classic API; GPTQModel (ModelCloud) is
# its maintained successor with the same quantize()/save_quantized() flow
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
from transformers import AutoTokenizer

# Quantization config: Hessian-damped, block-wise, calibration-driven
quantize_config = BaseQuantizeConfig(
    bits=4,             # 4-bit quantization
    group_size=128,     # Group size for quantization
    damp_percent=0.01,  # Damping factor for the Hessian
    sym=True,           # Symmetric quantization
    true_sequential=True,
)

tokenizer = AutoTokenizer.from_pretrained("/models/llama-3.1-8b")
model = AutoGPTQForCausalLM.from_pretrained(
    "/models/llama-3.1-8b",
    quantize_config=quantize_config,
)

# Calibration data (needed for Hessian estimation)
from datasets import load_dataset

dataset = load_dataset("allenai/c4", "en", split="train")
calibration_data = [
    tokenizer(example["text"], return_tensors="pt")["input_ids"]
    for example in dataset.select(range(128))
]

# Quantize and save
model.quantize(calibration_data, batch_size=1)
model.save_quantized("/models/llama-3.1-8b-gptq")
tokenizer.save_pretrained("/models/llama-3.1-8b-gptq")
```

### Using GPTQ Models
```python
from auto_gptq import AutoGPTQForCausalLM
from transformers import AutoTokenizer

# Load quantized model — no load_in_4bit kwarg: the checkpoint is
# already quantized, from_quantized rebuilds the quantized layers
model = AutoGPTQForCausalLM.from_quantized(
    "/models/llama-3.1-8b-gptq",
    device_map="auto",
    use_safetensors=True,
)
tokenizer = AutoTokenizer.from_pretrained("/models/llama-3.1-8b-gptq")

# Inference
inputs = tokenizer("Hello, world!", return_tensors="pt").to("cuda")
output = model.generate(**inputs, max_new_tokens=100)
```

## Comparison

### Quantization Method Comparison
```text
Method    Quality    Speed    VRAM    Use Case
──────────────────────────────────────────────────
fp16      Reference  Fast     14GB    Development
8-bit     +2%       Fast     8GB     Production
GPTQ 4b   +5%       Medium   4.5GB   Inference
AWQ 4b    +3%       Fast     4.5GB   Inference
EXL2 4.5  +4%       Very Fast 4.2GB Fast Inference
GGUF Q4_K +6%       Medium   4.5GB   CPU/GPU Hybrid

Perplexity increase vs fp16 (lower is better)
```

### Recommendation for an 11GB-class GPU
```text
For 7B models:
  - Best quality: AWQ 4-bit or EXL2 4.5
  - Fastest: EXL2 4.5
  - CPU fallback: GGUF Q4_K

For 13B models:
  - Fits in VRAM: EXL2 4.0 or AWQ 4-bit
  - Hybrid: GGUF Q4_K with partial GPU offload

For 34B models:
  - Hybrid: GGUF Q4_K with CPU offload
  - Not recommended for an 11GB-class GPU
```

## Advanced Techniques

### Layer-wise Quantization
```python
# Different quantization per layer
quant_config = {
    # Attention layers: higher precision
    "attn_q": 5.0,  # 5-bit
    "attn_k": 5.0,
    "attn_v": 5.0,
    "attn_o": 4.5,

    # FFN layers: lower precision
    "ffn_up": 4.0,
    "ffn_down": 4.0,
    "ffn_gate": 4.0,

    # Output: highest precision
    "lm_head": 8.0,
}
```

### Dynamic Quantization
```python
import torch
# Quantize during inference based on statistics
class DynamicQuantizer:
    def __init__(self, layer):
        self.layer = layer
        self.register_buffer('scale', torch.ones(1))
        self.register_buffer('zero_point', torch.zeros(1))

    def update_stats(self, activation):
        """Update quantization statistics"""
        self.scale = activation.abs().max() / 127
        self.zero_point = activation.mean()

    def quantize(self, x):
        return torch.round(x / self.scale) + self.zero_point
```

---

## Summary

EXL2 and AWQ are the GPU-only end of the 4-bit world: both land near-fp16 quality at 4-bit, which is what turns an 11GB-class card into a serious inference machine. This lesson covered each method's mechanics - ExLlamaV2's per-layer mixed bits and AWQ's activation-aware channel scaling - then put them next to GPTQ and each other in the comparison section. The durable rule from it: match the method to the runtime and hardware you actually have, and let measured quality per token decide, not benchmarks borrowed from someone else's GPU.

## References

### Related Minder Academy Documents

- [4101: GGUF Physics - CPU/GPU Hybrid Offloading](4101-GGUF-Physics.md)
- [4103: Double Quantization - BitsAndBytes (bnb) Logic](4103-Double-Quantization.md)

---

## Next Steps

- Continue with: **[4103: Double Quantization](./4103-Double-Quantization.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**

- [4101: GGUF Physics](./4101-GGUF-Physics.md)
- [4103: Double Quantization](./4103-Double-Quantization.md)
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)

**Experiment Template:** [EXP_4102: EXL2 & AWQ](../../../../experiments/EXP_4102_EXL2_AWQ.md)
