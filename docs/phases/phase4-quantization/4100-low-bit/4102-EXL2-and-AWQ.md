---
Document ID: 4102
Title: EXL2 and AWQ - Extreme Quantization
Phase: 4
Module: 4100
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'gguf', 'exl2', 'awq', 'compression']
---

# 4102: EXL2 and AWQ - Extreme Quantization

## Abstract
EXL2 and AWQ are advanced quantization methods optimized for GPU-only inference. They provide near-fp16 quality at 4-bit precision, making them ideal for the RTX 2080 Ti.

## EXL2 (ExLlamaV2)

### What is EXL2?
```
EXL2 is a custom quantization format for ExLlamaV2:

- Designed specifically for GPU inference
- Optimized for CUDA tensor cores
- Variable bit rate per layer
- Very fast loading and inference
- Supports 2-8 bit quantization
```

### EXL2 Architecture
```
EXL2 Format:
┌─────────────────────────────────────────┐
│  Header                                 │
│  - Tensor count                         │
│  - Tensor info (name, shape, dtype)     │
├─────────────────────────────────────────┤
│  Tensor Data (quantized)                │
│  - Variable bit rate per tensor         │
│  - Optimized for GPU memory layout      │
│  - Pre-allocated for fast loading       │
└─────────────────────────────────────────┘
```

### EXL2 Quantization Levels
```python
EXL2_QUANT_LEVELS = {
    2.0: {"description": "2-bit", "vram_7b": "~2GB", "quality": "Poor"},
    3.0: {"description": "3-bit", "vram_7b": "~3GB", "quality": "Fair"},
    4.0: {"description": "4-bit", "vram_7b": "~4GB", "quality": "Good"},
    4.125: {"description": "4.125-bit", "vram_7b": "~4.1GB", "quality": "Very Good"},
    4.5: {"description": "4.5-bit", "vram_7b": "~4.5GB", "quality": "Excellent"},
    5.0: {"description": "5-bit", "vram_7b": "~5GB", "quality": "Near fp16"},
    6.0: {"description": "6-bit", "vram_7b": "~6GB", "quality": "Almost fp16"},
    8.0: {"description": "8-bit", "vram_7b": "~8GB", "quality": "fp16"},
}

# Recommended for RTX 2080 Ti (11GB):
# - Llama-2-7B: 4.5 or 5.0 bpw
# - Llama-2-13B: 4.0 bpw
# - Mistral-7B: 4.5 bpw
# - Mixtral-8x7B: 3.5 bpw (barely fits)
```

### Converting to EXL2
```bash
# Install ExLlamaV2
git clone https://github.com/turboderp/exllamav2
cd exllamav2
pip install -r requirements.txt

# Convert model to EXL2
python convert.py \
  -i /models/llama-2-7b \
  -o /models/llama-2-7b-exl2 \
  -b 4.5  # Bits per weight

# For mixed precision (different bpw per layer)
python convert.py \
  -i /models/mixtral-8x7b \
  -o /models/mixtral-8x7b-exl2 \
  -b 4.0,3.5  # Attention: 4-bit, FFN: 3.5-bit
```

### Using EXL2 with ExLlamaV2
```python
from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Tokenizer,
    ExLlamaV2Cache,
)

# Load model
config = ExLlamaV2Config()
config.model_dir = "/models/llama-2-7b-exl2"

model = ExLlamaV2(config)
model.load()

# Tokenizer
tokenizer = ExLlamaV2Tokenizer(config)

# Cache
cache = ExLlamaV2Cache(model, max_seq_len=4096)

# Inference
from exllamav2.generator import ExLlamaV2Generator

generator = ExLlamaV2Generator(model, tokenizer, cache)
settings = ExLlamaV2Generator.Settings()
settings.temperature = 0.7
settings.top_p = 0.9
settings.top_k = 40

text = generator.generate("Once upon a time", settings=settings)
print(text)
```

### EXL2 Performance
```
RTX 2080 Ti (11GB VRAM):
Llama-2-7B @ 4.5 bpw:
  - Model size: ~4.2 GB
  - Speed: ~80-100 tokens/sec
  - Quality: Perplexity within 5% of fp16

Llama-2-13B @ 4.0 bpw:
  - Model size: ~7 GB
  - Speed: ~40-50 tokens/sec
  - Quality: Perplexity within 8% of fp16

Comparison (same hardware):
  - GGUF Q4_K: ~45 tokens/sec
  - EXL2 4.5: ~90 tokens/sec
  - Speedup: ~2x
```

## AWQ (Activation-aware Weight Quantization)

### What is AWQ?
```
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
pip install autoawq

# Quantize model
python -m awq.quantize \
  --model_path /models/llama-2-7b \
  --w_bit 4 \
  --q_group_size 128 \
  --output_dir /models/llama-2-7b-awq

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
    "/models/llama-2-7b-awq",
    fuse_layers=True,      # Fuse for speed
    max_new_tokens=512,
    batch_size=1,
)

tokenizer = AutoTokenizer.from_pretrained("/models/llama-2-7b-awq")

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
```
Llama-2-7B AWQ @ 4-bit:
  - VRAM usage: ~4.5 GB
  - Perplexity: Within 2% of fp16
  - Speed: ~60-70 tokens/sec on RTX 2080 Ti

Comparison with other 4-bit methods:
  - GPTQ: 5-7% perplexity increase
  - AWQ: 2-3% perplexity increase
  - EXL2: 3-5% perplexity increase
```

## GPTQ (Gradient-based Quantization)

### GPTQ Overview
```
GPTQ: Post-Training Quantization with Gradient Information
- Uses Hessian information for optimal quantization
- Second-order optimization
- Block-wise quantization
- Requires calibration data
```

### GPTQ Quantization
```bash
# Install GPTQ-for-LLaMa
pip install optimum

# Quantize with GPTQ
optimum-cli export llama \
  --model /models/llama-2-7b \
  --quantize \
  --format gptq \
  --bits 4 \
  --group-size 128 \
  --dataset c4 \
  --output /models/llama-2-7b-gptq
```

### Using GPTQ Models
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from optimum.bettertransformer import BetterTransformer

# Load GPTQ model
model = AutoModelForCausalLM.from_pretrained(
    "/models/llama-2-7b-gptq",
    device_map="auto",
    quantization_config={"load_in_4bit": True},
)

tokenizer = AutoTokenizer.from_pretrained("/models/llama-2-7b-gptq")

# Optional: BetterTransformer optimization
model = BetterTransformer.transform(model, keep_original_model=False)

# Inference
inputs = tokenizer("Hello, world!", return_tensors="pt").to("cuda")
output = model.generate(**inputs, max_new_tokens=100)
```

## Comparison

### Quantization Method Comparison
```
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

### Recommendation for RTX 2080 Ti
```
For 7B models:
  - Best quality: AWQ 4-bit or EXL2 4.5
  - Fastest: EXL2 4.5
  - CPU fallback: GGUF Q4_K

For 13B models:
  - Fits in VRAM: EXL2 4.0 or AWQ 4-bit
  - Hybrid: GGUF Q4_K with partial GPU offload

For 34B models:
  - Hybrid: GGUF Q4_K with CPU offload
  - Not recommended for RTX 2080 Ti
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

## Next Steps

- Continue with: **[4103: Double Quantization](./4103-Double-Quantization.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [4101: GGUF Physics](./4101-GGUF-Physics.md)
- [4103: Double Quantization](./4103-Double-Quantization.md)
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)

**Experiment Template:** `experiments/EXP_4102_EXL2_AWQ.md`
