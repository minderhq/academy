---
Document ID: QUICK-REF-VOLUME-4
Title: "Volume 4: Quantization & Optimization - Quick Reference"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'quantization', 'gguf']
---

# Volume 4: Quantization & Optimization - Quick Reference

**Run Models Anywhere** - Quantization, compression, and optimization

---

## Quantization Fundamentals

### Quantization Types
```python
# FP32 (32-bit float): 4 bytes per parameter
# FP16 (16-bit float): 2 bytes per parameter (2x compression)
# BF16 (16-bit bfloat): 2 bytes, same exponent range as FP32
# INT8 (8-bit int): 1 byte per parameter (4x compression)
# INT4 (4-bit int): 0.5 bytes per parameter (8x compression)
# NF4 (4-bit normal float): Optimized 4-bit for weights

# Size comparison
params_7b = 7_000_000_000

fp32_size = params_7b * 4 / 1e9      # 28 GB
fp16_size = params_7b * 2 / 1e9      # 14 GB (2x)
int8_size = params_7b * 1 / 1e9      # 7 GB (4x)
int4_size = params_7b * 0.5 / 1e9    # 3.5 GB (8x)
```

### Quantization Formula
```python
import torch
def quantize(x, scale, zero_point, qmin=-128, qmax=127):
    """
    Quantize floating point to integer

    x: Input tensor (FP32)
    scale: Quantization scale
    zero_point: Zero point offset
    qmin, qmax: Integer range (INT8: -128 to 127)
    """
    # Quantize
    x_q = torch.round(x / scale + zero_point)

    # Clamp to range
    x_q = torch.clamp(x_q, qmin, qmax)

    return x_q.int()

def dequantize(x_q, scale, zero_point):
    """Dequantize integer to floating point"""
    return (x_q.float() - zero_point) * scale

# Determine scale and zero_point
def compute_scale_zero_point(x, qmin=-128, qmax=127):
    """Compute optimal scale and zero point"""
    x_min = x.min().item()
    x_max = x.max().item()

    # Scale
    scale = (x_max - x_min) / (qmax - qmin)

    # Zero point
    zero_point = qmin - x_min / scale

    return scale, int(round(zero_point))
```

---

## GGUF Format

### GGUF Structure
```python
# GGUF: GPT-Generated Unified Format
# Single file format for quantized models

import gguf

# Load GGUF model
reader = gguf.GGUFReader("model.gguf")

# Get metadata
metadata = reader.fields
print(f"Model architecture: {metadata['general.architecture']}")
print(f"Quantization: {metadata['general.quantization_version']}")
print(f"Context length: {metadata['llama.context_length']}")

# Load tensors
for tensor_name in reader.tensors:
    tensor = reader.tensors[tensor_name]
    print(f"{tensor_name}: {tensor.data.shape} {tensor.data.dtype}")
```

### GGUF Quantization Levels
```python
# GGUF quantization types
QUANTIZATION_LEVELS = {
    "Q4_0": {"description": "4-bit, small matrix", "bits": 4, "size_gb": 4.2},
    "Q4_1": {"description": "4-bit, medium matrix", "bits": 4, "size_gb": 4.7},
    "Q5_0": {"description": "5-bit, small matrix", "bits": 5, "size_gb": 5.1},
    "Q5_1": {"description": "5-bit, medium matrix", "bits": 5, "size_gb": 5.6},
    "Q8_0": {"description": "8-bit, almost no quality loss", "bits": 8, "size_gb": 8.5},
    "Q4_K": {"description": "4-bit, K-means (recommended)", "bits": 4, "size_gb": 4.5},
    "Q5_K": {"description": "5-bit, K-means (high quality)", "bits": 5, "size_gb": 5.5},
    "Q6_K": {"description": "6-bit, K-means (very high quality)", "bits": 6, "size_gb": 6.5},
}

# Convert to GGUF
# llama.cpp/quantize: model.gguf Q4_K_M
```

---

## EXL2 Format

### EXL2 Overview
```text
# EXL2: EXLlama 2 format
# Optimized for fast inference on NVIDIA GPUs

# Features:
- 2-8 bit quantization
- Optimized for CUDA cores
- Faster than GGUF for inference
- Requires NVIDIA GPU

# Conversion example (llama.cpp to EXL2)
# exll2av convert model.gguf --output model.exl2 --bpw 4.0
# bpw: bits per weight (2.0 to 8.0)
```

### EXL2 vs GGUF
```python
COMPARISON = {
    "inference_speed": {
        "GGUF": "1x (baseline)",
        "EXL2": "1.5-2x faster",
    },
    "memory_efficiency": {
        "GGUF": "1x (baseline)",
        "EXL2": "Similar",
    },
    "quality": {
        "GGUF": "Slightly better at 4-bit",
        "EXL2": "Slightly lower at 4-bit",
    },
    "hardware": {
        "GGUF": "CPU + GPU (any)",
        "EXL2": "NVIDIA GPU only",
    },
    "use_case": {
        "GGUF": "General use, CPU inference",
        "EXL2": "GPU-only inference",
    },
}
```

---

## Double Quantization

### Concept
```python
import torch.nn.functional as F
# Standard quantization:
# Weights are quantized once

# Double quantization:
# 1. Quantize weights to 4-bit
# 2. Quantize the quantization scales to 8-bit

# Benefits:
# - Extra compression (~0.37 bits per parameter saved)
# - Minimal quality loss
# - Standard in 4-bit quantization

class DoubleQuantization:
    """Double quantization for 4-bit weights"""

    def __init__(self):
        self.weight_q = None      # 4-bit weights
        self.scale_q = None       # 8-bit scales
        self.zero_point_q = None  # 8-bit zero points

    def quantize_weights(self, weights):
        """First quantization: weights to 4-bit"""
        # Quantize each channel/group
        scales, zero_points = compute_scales_zero_points(weights)
        weight_q = quantize_per_channel(weights, scales, zero_points)

        return weight_q, scales, zero_points

    def quantize_scales(self, scales):
        """Second quantization: scales to 8-bit"""
        # Scales are typically in small range
        # Quantize to 8-bit for additional compression
        scale_q, scale_scale, scale_zero = quantize(scales)

        return scale_q, scale_scale, scale_zero

    def forward(self, x):
        """Dequantize and compute"""
        # Dequantize scales
        scales = dequantize(self.scale_q, self.scale_scale, self.scale_zero)

        # Dequantize weights
        weights = dequantize(self.weight_q, scales, self.zero_point_q)

        # Compute
        return F.linear(x, weights)
```

---

## AWQ (Activation-aware Weight Quantization)

### Key Idea
```python
import torch
# AWQ: Optimize which weights to quantize
# Keep 1% of weights (salient weights) in higher precision

class AWQQuantization:
    """Activation-aware Weight Quantization"""

    def __init__(self, model, activation_samples):
        self.model = model
        self.activation_samples = activation_samples

    def find_salient_weights(self):
        """Find weights with large activations"""
        # Collect activations
        activations = []
        for sample in self.activation_samples:
            with torch.no_grad():
                # Collect intermediate activations
                acts = self.model.forward_intermediate(sample)
                activations.append(acts)

        # Find salient channels (large activation magnitudes)
        salient_channels = []
        for act in activations:
            # Channels with large mean activation
            mean_act = act.abs().mean(dim=(0, 1))  # (hidden_dim,)
            threshold = mean_act.quantile(0.99)    # Top 1%
            salient = mean_act > threshold
            salient_channels.append(salient)

        return salient_channels

    def quantize_with_salient(self, salient_mask):
        """Quantize while keeping salient weights in FP16"""
        for name, param in self.model.named_parameters():
            if 'weight' in name:
                # Get salient mask for this layer
                mask = salient_mask[name]

                # Create copy for quantization
                weight_q = param.data.clone()

                # Quantize non-salient weights
                weight_q[~mask] = quantize(weight_q[~mask], bits=4)

                # Keep salient weights in FP16
                weight_q[mask] = weight_q[mask].to(torch.float16)

                # Replace parameter
                param.data = weight_q

# Benefits:
# - Better quality than pure 4-bit
# - Minimal overhead (only 1% FP16)
# - Faster inference (most weights are 4-bit)
```

---

## GPTQ (Generative Perceptual Quantization)

### Overview
```python
import torch
# GPTQ: Optimize quantization to minimize output error
# Minimize ||output_full - output_quantized||^2

def gpt_quantize(layer, inputs):
    """
    GPTQ quantization for a layer

    Minimize reconstruction error on actual inputs
    """
    weight = layer.weight.data  # (out_features, in_features)

    # Get input statistics
    H = torch.zeros(in_features, in_features)
    for inp in inputs:
        # inp: (batch, in_features)
        H += inp.T @ inp
    H = H / len(inputs)  # Covariance matrix

    # Optimize quantization per row
    weight_q = torch.zeros_like(weight)
    for i in range(out_features):
        # Get row (output feature)
        w = weight[i]  # (in_features,)

        # Optimize quantization grid
        # Minimize: ||w @ x - w_q @ x||^2_H
        # where H is input covariance
        w_q = optimize_quantization(w, H, bits=4)
        weight_q[i] = w_q

    return weight_q

def optimize_quantization(w, H, bits=4):
    """Find optimal quantization for weight vector w"""
    # Initialize with uniform quantization
    # Iteratively update to minimize error

    # Algorithm (simplified):
    # 1. Compute error: E = ||w @ sqrt(H) - w_q @ sqrt(H)||^2
    # 2. Find worst channel (highest error)
    # 3. Update that channel's quantization
    # 4. Repeat convergence

    # Returns quantized weights
    return quantize(w, bits=bits)
```

---

## Context Window Optimization

### KV Cache Quantization
```python
import torch
# KV Cache: Store keys and values for autoregressive generation
# Grows with sequence length: O(seq_len * hidden_dim * num_layers * num_heads)

# Standard KV cache: FP16 (2 bytes per element)
# Quantized KV cache: INT8 or FP8 (1 byte per element)

class QuantizedKVCache:
    """Quantized KV cache for memory efficiency"""

    def __init__(self, num_layers, num_heads, head_dim, max_seq_len, dtype=torch.int8):
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.max_seq_len = max_seq_len

        # Allocate quantized cache
        # Shape: (num_layers, 2, batch, num_heads, seq_len, head_dim)
        # 2 for keys and values
        self.cache = torch.zeros(
            num_layers, 2, 1, num_heads, max_seq_len, head_dim,
            dtype=dtype, device='cuda'
        )

        # Store scales for dequantization
        # Shape: (num_layers, 2, batch, num_heads, seq_len)
        self.scales = torch.ones(
            num_layers, 2, 1, num_heads, max_seq_len,
            dtype=torch.float16, device='cuda'
        )

    def quantize_and_store(self, layer_idx, kv_type, keys_or_values, seq_pos):
        """
        Quantize and store KV

        layer_idx: Layer index
        kv_type: 0 for keys, 1 for values
        keys_or_values: (batch, num_heads, 1, head_dim)
        seq_pos: Position in sequence
        """
        # Compute scale per vector
        # max(|x|) / 127 for int8
        scale = keys_or_values.abs().max(dim=-1, keepdim=True).values / 127

        # Quantize
        kv_q = torch.round(keys_or_values / scale).to(torch.int8)

        # Store
        self.cache[layer_idx, kv_type, :, :, seq_pos:seq_pos+1, :] = kv_q
        self.scales[layer_idx, kv_type, :, :, seq_pos:seq_pos+1] = scale.squeeze(-1)

    def retrieve(self, layer_idx, kv_type, seq_start, seq_end):
        """Retrieve and dequantize KV"""
        kv_q = self.cache[layer_idx, kv_type, :, :, seq_start:seq_end, :]
        scale = self.scales[layer_idx, kv_type, :, :, seq_start:seq_end]

        # Dequantize
        kv = kv_q.float() * scale.unsqueeze(-1)

        return kv

# Memory savings:
# FP16 KV cache: 2 bytes per element
# INT8 KV cache: 1 byte per element (2x compression)
# For 8K context: Saves ~8GB for 7B model
```

---

## Speculative Decoding

### Concept
```python
import torch.nn.functional as F
import torch
# Speculative decoding: Use small model to draft, large model to verify
# Speedup: 2-3x typical

class SpeculativeDecoding:
    """Speculative decoding for faster generation"""

    def __init__(self, draft_model, target_model, k=5):
        """
        draft_model: Small model (e.g., 1B params)
        target_model: Large model (e.g., 7B params)
        k: Number of tokens to draft
        """
        self.draft_model = draft_model
        self.target_model = target_model
        self.k = k

    def generate(self, prompt, max_new_tokens=100):
        """Generate with speculative decoding"""
        # Initialize
        input_ids = prompt.clone()
        draft_position = 0

        while input_ids.size(0) < max_new_tokens:
            # Step 1: Draft k tokens with small model
            draft_tokens = []
            draft_probs = []

            draft_input = input_ids.clone()
            for i in range(self.k):
                # Draft model predicts next token
                with torch.no_grad():
                    outputs = self.draft_model(draft_input)
                    probs = F.softmax(outputs.logits[:, -1, :], dim=-1)

                # Sample next token
                next_token = torch.multinomial(probs, num_samples=1)
                draft_tokens.append(next_token)
                draft_probs.append(probs)

                # Append to draft input
                draft_input = torch.cat([draft_input, next_token], dim=-1)

            # Step 2: Verify k tokens with large model
            accept_count = 0
            verification_input = input_ids.clone()

            for i in range(self.k):
                # Target model predicts next token
                with torch.no_grad():
                    outputs = self.target_model(verification_input)
                    target_probs = F.softmax(outputs.logits[:, -1, :], dim=-1)

                # Get draft token and probability
                draft_token = draft_tokens[i]
                draft_prob = draft_probs[i].gather(1, draft_token)

                # Get target probability for draft token
                target_prob_for_draft = target_probs.gather(1, draft_token)

                # Acceptance criteria
                q = target_prob_for_draft / draft_prob
                accept_prob = torch.clamp(q, max=1.0)

                # Accept or reject
                if torch.rand(1) < accept_prob:
                    # Accept draft token
                    input_ids = torch.cat([input_ids, draft_token], dim=-1)
                    verification_input = torch.cat([verification_input, draft_token], dim=-1)
                    accept_count += 1
                else:
                    # Reject, sample from target model
                    next_token = torch.multinomial(target_probs, num_samples=1)
                    input_ids = torch.cat([input_ids, next_token], dim=-1)
                    break

            # If all k accepted, sample one more from target model
            if accept_count == self.k:
                with torch.no_grad():
                    outputs = self.target_model(input_ids)
                    probs = F.softmax(outputs.logits[:, -1, :], dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                    input_ids = torch.cat([input_ids, next_token], dim=-1)

        return input_ids

# Speedup analysis:
# Draft model: ~10ms per token (1B params)
# Target model: ~100ms per token (7B params)
# Standard: 100ms * 100 tokens = 10,000ms
# Speculative: 10ms*5 (draft) + 100ms*20 (verify) = 2,500ms
# Speedup: ~4x
```

---

## Volume 4 Checklist

- [ ] Understand quantization levels (FP32 to INT4)
- [ ] Convert model to GGUF
- [ ] Compare GGUF vs EXL2
- [ ] Apply double quantization
- [ ] Understand AWQ
- [ ] Understand GPTQ
- [ ] Implement KV cache quantization
- [ ] Use speculative decoding
- [ ] Benchmark quantization quality

---

## Next Steps

1. Complete EXP_4101: GGUF Quantization
2. Read 4201-Context-Window-Physics.md
3. Read 4202-Speculative-Decoding.md
4. Practice with EXP experiments

---

**Volume:** 4 - Quantization & Optimization

**Estimated Time:** 30-35 hours
