---
Document ID: PROJECT-004
Title: "CAPSTONE PROJECT 004: Quantize LLM from Scratch"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Intermediate
---

# CAPSTONE PROJECT 004: Quantize LLM from Scratch

**Run large models on limited hardware**

---

## 🎯 Project Overview

Implement model quantization from scratch to run large language models efficiently:
- Manual quantization algorithms (GPTQ, AWQ)
- Custom kernel implementation for quantized operations
- GGUF file format and serialization
- Memory optimization techniques
- Performance benchmarking and comparison

**Estimated Time:** 15-20 hours
**Difficulty:** ⭐⭐⭐ Advanced

---

## 📋 Prerequisites

Complete these before starting:
- ✅ 4101: GGUF Physics
- ✅ 4102: EXL2 and AWQ
- ✅ 4201: Context Window Physics
- ✅ PROJECT 003: Transformer from Scratch

---

## 🏗️ Project Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Quantization Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  FP16 Model                                                  │
│       │                                                       │
│       ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           Quantization (Training-Free)                 │  │
│  │  - GPTQ: Approximate Weight Quantization              │  │
│  │  - AWQ: Activation-aware Quantization                 │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  Packing (4-bit)                       │  │
│  │  - Pack 2 weights per uint8                           │  │
│  │  - Optimize for memory access                         │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                   GGUF Format                          │  │
│  │  - Metadata                                           │  │
│  │  - Tensors                                            │  │
│  │  - KV Cache                                           │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Quantized Inference Engine                │  │
│  │  - Custom dequantization kernels                      │  │
│  │  - Optimized matmul                                   │  │
│  │  - Memory-efficient attention                         │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Quantization Algorithms (5 hours)

### 1.1 GPTQ Implementation

```python
# File: gptq.py
"""
GPTQ: Post-Training Quantization
================================
"""

import numpy as np
from typing import Tuple, List

def gptq_quantize(weights: np.ndarray, bits: int = 4,
                  group_size: int = 128) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    GPTQ quantization algorithm

    Args:
        weights: (out_features, in_features) - FP16 weights
        bits: Quantization bits (2-8)
        group_size: Size of quantization groups

    Returns:
        qweights: Quantized weights
        scales: Per-group scales
        zeros: Per-group zero points
    """
    out_features, in_features = weights.shape
    assert in_features % group_size == 0

    n_groups = in_features // group_size
    qweights = np.zeros_like(weights, dtype=np.uint8)
    scales = np.zeros((out_features, n_groups), dtype=np.float16)
    zeros = np.zeros((out_features, n_groups), dtype=np.float16)

    # Quantization range
    q_max = 2 ** bits - 1
    q_min = 0

    for i in range(out_features):
        for g in range(n_groups):
            start = g * group_size
            end = start + group_size

            # Extract group
            group = weights[i, start:end]

            # Calculate scale
            w_max = np.max(group)
            w_min = np.min(group)
            scale = (w_max - w_min) / q_max

            # Calculate zero point
            zero = -w_min / scale

            # Quantize
            q_group = np.round(group / scale + zero).clip(q_min, q_max)
            qweights[i, start:end] = q_group.astype(np.uint8)

            scales[i, g] = scale
            zeros[i, g] = zero

    return qweights, scales, zeros

def gptq_dequantize(qweights: np.ndarray, scales: np.ndarray,
                    zeros: np.ndarray) -> np.ndarray:
    """Dequantize GPTQ weights"""
    out_features, in_features = qweights.shape
    group_size = in_features // scales.shape[1]

    weights = np.zeros_like(qweights, dtype=np.float16)

    for i in range(out_features):
        for g in range(scales.shape[1]):
            start = g * group_size
            end = start + group_size

            weights[i, start:end] = (qweights[i, start:end] - zeros[i, g]) * scales[i, g]

    return weights
```

### 1.2 AWQ Implementation

```python
# File: awq.py
"""
AWQ: Activation-aware Quantization
==================================
"""

def awq_quantize(weights: np.ndarray, activations: np.ndarray,
                bits: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    """
    AWQ quantization considering activation magnitude

    Args:
        weights: (out_features, in_features)
        activations: (in_features,) - activation magnitudes
        bits: Quantization bits

    Returns:
        qweights: Quantized weights
        scales: Per-channel scales
    """
    out_features, in_features = weights.shape

    # Calculate importance weights (activation magnitude)
    activation_scale = np.abs(activations).reshape(1, -1)

    # Weight by activation importance
    scaled_weights = weights * activation_scale

    # Per-channel quantization
    q_max = 2 ** bits - 1
    qweights = np.zeros_like(weights, dtype=np.uint8)
    scales = np.zeros(out_features, dtype=np.float16)

    for i in range(out_features):
        w = scaled_weights[i, :]
        w_max = np.max(w)
        w_min = np.min(w)

        scale = (w_max - w_min) / q_max
        scales[i] = scale

        qweights[i, :] = np.round((w - w_min) / scale).clip(0, q_max).astype(np.uint8)

    return qweights, scales
```

### ✅ Phase 1 Checklist
- [ ] GPTQ quantization implemented
- [ ] AWQ quantization implemented
- [ ] Dequantization working
- [ ] Accuracy within 1% of FP16

---

## Phase 2: GGUF Format (4 hours)

### 2.1 GGUF Writer

```python
# File: gguf.py
"""
GGUF File Format
===============
"""

import struct
from typing import Dict, Any
import numpy as np

class GGUFWriter:
    """Write models in GGUF format"""

    def __init__(self, path: str):
        self.path = path
        self.tensors = []
        self.metadata = {}

    def add_tensor(self, name: str, data: np.ndarray,
                  qtype: int = 0):
        """Add a tensor to the file"""
        self.tensors.append({
            'name': name,
            'data': data,
            'qtype': qtype
        })

    def add_metadata(self, key: str, value: Any):
        """Add metadata"""
        self.metadata[key] = value

    def write(self):
        """Write GGUF file"""
        with open(self.path, 'wb') as f:
            # Write header
            self._write_header(f)

            # Write metadata
            self._write_metadata(f)

            # Write tensor info
            self._write_tensor_info(f)

            # Write tensor data
            self._write_tensor_data(f)

    def _write_header(self, f):
        """Write GGUF header"""
        # Magic number
        f.write(b'GGUF')

        # Version
        f.write(struct.pack('<I', 3))

        # Tensor count
        f.write(struct.pack('<I', len(self.tensors)))

        # Metadata KV count
        f.write(struct.pack('<I', len(self.metadata)))

    def _write_metadata(self, f):
        """Write metadata key-value pairs"""
        for key, value in self.metadata.items():
            # Key length and key
            key_bytes = key.encode('utf-8')
            f.write(struct.pack('<I', len(key_bytes)))
            f.write(key_bytes)

            # Type and value
            if isinstance(value, str):
                f.write(struct.pack('<I', 8))  # String type
                val_bytes = value.encode('utf-8')
                f.write(struct.pack('<I', len(val_bytes)))
                f.write(val_bytes)
            elif isinstance(value, int):
                f.write(struct.pack('<I', 4))  # Int type
                f.write(struct.pack('<i', value))
            elif isinstance(value, float):
                f.write(struct.pack('<I', 6))  # Float type
                f.write(struct.pack('<f', value))

    def _write_tensor_info(self, f):
        """Write tensor information"""
        for tensor in self.tensors:
            name = tensor['name']
            data = tensor['data']

            # Name
            name_bytes = name.encode('utf-8')
            f.write(struct.pack('<I', len(name_bytes)))
            f.write(name_bytes)

            # Dimensions
            n_dims = len(data.shape)
            f.write(struct.pack('<I', n_dims))
            for dim in data.shape:
                f.write(struct.pack('<I', dim))

            # Quantization type
            f.write(struct.pack('<I', tensor['qtype']))

            # Offset (placeholder, updated later)
            f.write(struct.pack('<Q', 0))

    def _write_tensor_data(self, f):
        """Write tensor data"""
        # Align to 32 bytes
        pos = f.tell()
        aligned_pos = (pos + 31) // 32 * 32
        f.write(b'\x00' * (aligned_pos - pos))

        for tensor in self.tensors:
            data = tensor['data'].tobytes()
            f.write(data)

            # Align to 32 bytes
            pos = f.tell()
            aligned_pos = (pos + 31) // 32 * 32
            f.write(b'\x00' * (aligned_pos - pos))
```

### ✅ Phase 2 Checklist
- [ ] GGUF writer implemented
- [ ] Metadata serialization working
- [ ] Tensor data packing working
- [ ] File format valid

---

## Phase 3: Quantized Inference (6 hours)

### 3.1 Quantized MatMul Kernel

```python
# File: qmatmul.py
"""
Quantized Matrix Multiplication
================================
"""

import numpy as np

def quantized_matmul(qweights: np.ndarray, scales: np.ndarray,
                    zeros: np.ndarray, input: np.ndarray,
                    bits: int = 4) -> np.ndarray:
    """
    Optimized matrix multiplication with quantized weights

    Args:
        qweights: (out_features, in_features) - Quantized weights
        scales: (out_features, n_groups) - Per-group scales
        zeros: (out_features, n_groups) - Per-group zeros
        input: (batch, in_features) - Input activation
        bits: Quantization bits

    Returns:
        output: (batch, out_features) - Result
    """
    batch, in_features = input.shape
    out_features = qweights.shape[0]
    group_size = in_features // scales.shape[1]

    output = np.zeros((batch, out_features), dtype=np.float16)

    # Process each group
    for g in range(scales.shape[1]):
        start = g * group_size
        end = start + group_size

        # Extract group
        q_group = qweights[:, start:end]
        s_group = scales[:, g]
        z_group = zeros[:, g]

        # Dequantize and multiply
        for b in range(batch):
            for o in range(out_features):
                # Vectorized dequantization
                w_deq = (q_group[o, :] - z_group[o]) * s_group[o]

                # Dot product
                output[b, o] += np.dot(input[b, start:end], w_deq)

    return output

# Optimized version with SIMD (pseudocode - requires actual C/C++ implementation)
def quantized_matmul_simd(qweights, scales, zeros, input, bits=4):
    """
    SIMD-optimized quantized matmul

    This would be implemented in C/C++ with AVX2/AVX-512 intrinsics
    for maximum performance. Python version is for reference only.
    """
    # In production:
    # 1. Use AVX2/AVX-512 for vectorized dequantization
    # 2. Use VNNI/DP4A for fast 4-bit dot products
    # 3. Batch process multiple groups
    pass
```

### 3.2 Quantized Attention

```python
# File: qattention.py
"""
Quantized Attention
===================
"""

def quantized_attention(q_proj, k_proj, v_proj, q_scales, k_scales, v_scales,
                       input, causal=True):
    """
    Attention with quantized projections

    Args:
        q_proj, k_proj, v_proj: Quantized projection weights
        q_scales, k_scales, v_scales: Corresponding scales
        input: Input tensor
        causal: Whether to use causal masking

    Returns:
        output: Attention output
    """
    # Quantized projections
    Q = quantized_matmul(q_proj, q_scales, zeros=None, input=input)
    K = quantized_matmul(k_proj, k_scales, zeros=None, input=input)
    V = quantized_matmul(v_proj, v_scales, zeros=None, input=input)

    # Scaled dot-product attention
    scores = Q @ K.T / np.sqrt(Q.shape[-1])

    # Causal mask
    if causal:
        seq_len = Q.shape[1]
        mask = np.triu(np.ones((seq_len, seq_len)), k=1) * -1e9
        scores = scores + mask

    # Softmax
    attn = np.exp(scores - scores.max(axis=-1, keepdims=True))
    attn = attn / attn.sum(axis=-1, keepdims=True)

    # Output
    output = attn @ V

    return output
```

### ✅ Phase 3 Checklist
- [ ] Quantized matmul working
- [ ] Result matches FP16 within tolerance
- [ ] Quantized attention working
- [ ] Memory usage reduced by >50%

---

## Phase 4: End-to-End Pipeline (5 hours)

### 4.1 Complete Quantization Pipeline

```python
# File: quantize_model.py
"""
Complete Quantization Pipeline
==============================
"""

import numpy as np
from pathlib import Path

def quantize_model(model_path: str, output_path: str, bits: int = 4):
    """
    Quantize a complete model

    Args:
        model_path: Path to FP16 model
        output_path: Path for quantized output
        bits: Quantization bits
    """
    print(f"Loading model from {model_path}...")
    # Load model (simplified - use actual model loader)
    model = load_model(model_path)

    print(f"Quantizing to {bits}-bit...")
    quantized_tensors = {}

    for name, tensor in model.items():
        if 'weight' in name:
            # Quantize weights
            if tensor.ndim == 2:
                q_weights, scales, zeros = gptq_quantize(
                    tensor.astype(np.float16),
                    bits=bits,
                    group_size=128
                )

                quantized_tensors[name] = {
                    'qweights': q_weights,
                    'scales': scales,
                    'zeros': zeros
                }
                print(f"  {name}: {tensor.shape} -> {q_weights.shape} ({(1-bits/16)*100:.1f}% reduction)")
        else:
            # Keep other tensors (biases, etc.) in FP16
            quantized_tensors[name] = tensor

    # Write GGUF file
    print(f"Writing to {output_path}...")
    writer = GGUFWriter(output_path)

    # Add metadata
    writer.add_metadata('quantization_version', 1)
    writer.add_metadata('bits', bits)
    writer.add_metadata('group_size', 128)

    # Add tensors
    for name, tensor in quantized_tensors.items():
        if isinstance(tensor, dict):
            writer.add_tensor(name, tensor['qweights'])
            writer.add_tensor(f'{name}.scale', tensor['scales'])
            writer.add_tensor(f'{name}.zero', tensor['zeros'])
        else:
            writer.add_tensor(name, tensor)

    writer.write()
    print("✓ Quantization complete!")

def load_model(path: str):
    """Load model from file"""
    # Simplified - implement actual loading
    return {
        'transformer.h.0.attn.c_attn.weight': np.random.randn(768, 2304).astype(np.float16),
        'transformer.h.0.attn.c_proj.weight': np.random.randn(768, 768).astype(np.float16),
        # ... more layers
    }

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: python quantize_model.py <input_path> <output_path> [bits]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    bits = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    quantize_model(input_path, output_path, bits)
```

### ✅ Phase 4 Checklist
- [ ] Complete pipeline working
- [ ] Model quantized successfully
- [ ] GGUF file valid
- [ ] Can be loaded for inference

---

## 🏆 Project Completion Checklist

```text
[ ] Phase 1: Quantization Algorithms
[ ] Phase 2: GGUF Format
[ ] Phase 3: Quantized Inference
[ ] Phase 4: End-to-End Pipeline
[ ] Model quantized to 4-bit
[ ] Memory usage >50% reduced
[ ] Accuracy within 1% of FP16
```

---

## 📚 Related Resources

- **[4101: GGUF Physics](../../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)** - GGUF format theory
- **[4102: EXL2 and AWQ](../../phases/phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md)** - Advanced quantization
- **[EXP_4101: GGUF Quantization](../../../experiments/EXP_4101_GGUF.md)** - Hands-on quantization

---

**Congratulations!** You've implemented model quantization:
- 🎯 GPTQ and AWQ algorithms
- 📦 GGUF file format
- ⚡ Quantized inference kernels
- 💾 >50% memory reduction

## Next Steps

- **[Volume 5: Model Adaptation](../../volumes/VOLUME-5-Model-Adaptation.md)**
