# EXP-4101: GGUF Quantization

**Hands-on quantization to GGUF format**

---

## 🎯 Experiment Overview

**Time:** 60-90 minutes
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:**
- 4101: GGUF Physics (theory)
- Basic Python knowledge
- Understanding of model quantization

**Learning Objectives:**
- Understand GGUF file format
- Implement 4-bit quantization
- Create GGUF files from scratch
- Benchmark quantized models

---

## 📚 Background

GGUF (GPT-Generated Unified Format) is a file format for storing quantized LLMs efficiently. It enables running large models on limited hardware.

### Key Features
- **Tensor quantization** - 4-bit, 5-bit, 8-bit
- **Memory mapping** - Load only what's needed
- **Fast loading** - Memory-mapped files
- **Metadata** - Rich model information

---

## 🔬 Experiment 1: GGUF Format (25 minutes)

### Step 1.1: GGUF Structure

```python
# File: gguf_format.py
"""
GGUF File Format Analysis
==========================
"""

import struct
from pathlib import Path
from typing import Dict, Any

class GGUFReader:
    """Read GGUF files"""

    def __init__(self, path: str):
        self.path = path
        self.file = open(path, 'rb')
        self.header = self._read_header()
        self.tensors = self._read_tensor_info()

    def _read_header(self) -> Dict[str, Any]:
        """Read GGUF header"""
        # Magic number
        magic = self.file.read(4)
        assert magic == b'GGUF', "Invalid GGUF file"

        # Version
        version = struct.unpack('<I', self.file.read(4))[0]

        # Tensor count
        tensor_count = struct.unpack('<I', self.file.read(4))[0]

        # Metadata KV count
        kv_count = struct.unpack('<I', self.file.read(4))[0]

        return {
            'magic': magic,
            'version': version,
            'tensor_count': tensor_count,
            'kv_count': kv_count
        }

    def _read_tensor_info(self) -> list:
        """Read tensor information"""
        tensors = []

        for _ in range(self.header['tensor_count']):
            # Tensor name
            name_len = struct.unpack('<I', self.file.read(4))[0]
            name = self.file.read(name_len).decode('utf-8')

            # Dimensions
            n_dims = struct.unpack('<I', self.file.read(4))[0]
            dims = []
            for _ in range(n_dims):
                dim = struct.unpack('<I', self.file.read(4))[0]
                dims.append(dim)

            # Quantization type
            qtype = struct.unpack('<I', self.file.read(4))[0]

            # Offset
            offset = struct.unpack('<Q', self.file.read(8))[0]

            tensors.append({
                'name': name,
                'dims': dims,
                'qtype': qtype,
                'offset': offset
            })

        return tensors

    def print_summary(self):
        """Print file summary"""
        print("=== GGUF File Summary ===")
        print(f"Version: {self.header['version']}")
        print(f"Tensors: {self.header['tensor_count']}")
        print(f"\nTensor Information:")

        for tensor in self.tensors[:10]:  # First 10
            print(f"  {tensor['name']}: {tensor['dims']} (type={tensor['qtype']})")

        if len(self.tensors) > 10:
            print(f"  ... and {len(self.tensors) - 10} more")

# Example usage (if you have a GGUF file)
# reader = GGUFReader('model.gguf')
# reader.print_summary()
```

**Checkpoint 1:** ✅ GGUF format understood

---

## 🔬 Experiment 2: 4-bit Quantization (30 minutes)

### Step 2.1: Implement Quantization

```python
# File: quantize.py
"""
4-bit Quantization Implementation
=================================
"""

import numpy as np
from typing import Tuple

def quantize_q4_0(weights: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Quantize weights to 4-bit (Q4_0 format)

    Args:
        weights: (n, m) FP16 weights

    Returns:
        qweights: Quantized weights (packed)
        scales: Per-block scales
        mins: Per-block minimums
    """
    n, m = weights.shape
    block_size = 32

    # Calculate blocks
    n_blocks = (n * m + block_size - 1) // block_size

    qweights = np.zeros(n_blocks * block_size // 2, dtype=np.uint8)
    scales = np.zeros(n_blocks, dtype=np.float16)
    mins = np.zeros(n_blocks, dtype=np.float16)

    for i in range(n_blocks):
        start = i * block_size
        end = min(start + block_size, n * m)

        block = weights.flatten()[start:end]
        block = np.concatenate([block, np.zeros(block_size - len(block))])

        # Calculate scale and min
        w_max = block.max()
        w_min = block.min()

        scale = (w_max - w_min) / 15.0
        min_val = w_min

        scales[i] = scale
        mins[i] = min_val

        # Quantize
        q_block = np.round((block - min_val) / scale).clip(0, 15).astype(np.uint8)

        # Pack 2 values per byte
        for j in range(0, block_size, 2):
            byte = (q_block[j] & 0x0F) | ((q_block[j + 1] & 0x0F) << 4)
            qweights[i * block_size // 2 + j // 2] = byte

    return qweights, scales, mins

def dequantize_q4_0(qweights: np.ndarray, scales: np.ndarray,
                    mins: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
    """Dequantize Q4_0 weights"""

    n, m = shape
    block_size = 32
    n_blocks = (n * m + block_size - 1) // block_size

    weights = np.zeros(n * m, dtype=np.float16)

    for i in range(n_blocks):
        start = i * block_size
        end = min(start + block_size, n * m)

        scale = scales[i]
        min_val = mins[i]

        # Unpack
        for j in range(block_size):
            byte = qweights[i * block_size // 2 + j // 2]
            if j % 2 == 0:
                q_val = byte & 0x0F
            else:
                q_val = (byte >> 4) & 0x0F

            deq = q_val * scale + min_val
            if start + j < n * m:
                weights[start + j] = deq

    return weights.reshape(shape)

# Test
weights_fp16 = np.random.randn(256, 256).astype(np.float16)
qweights, scales, mins = quantize_q4_0(weights_fp16)
weights_dequant = dequantize_q4_0(qweights, scales, mins, weights_fp16.shape)

# Calculate error
error = np.abs(weights_fp16 - weights_dequant).mean()
print(f"Quantization error: {error:.6f}")
print(f"Compression ratio: {weights_fp16.nbytes / qweights.nbytes:.2f}x")
```

**Checkpoint 2:** ✅ Quantization working

---

## 🔬 Experiment 3: Create GGUF File (25 minutes)

### Step 3.1: GGUF Writer

```python
# File: create_gguf.py
"""
Create GGUF File
================
"""

import struct
import numpy as np
from pathlib import Path

class GGUFWriter:
    """Write GGUF files"""

    def __init__(self, path: str, n_tensors: int):
        self.path = path
        self.n_tensors = n_tensors
        self.tensor_info = []
        self.data_offset = 0

    def add_tensor(self, name: str, data: np.ndarray, qtype: int):
        """Add tensor information"""
        self.tensor_info.append({
            'name': name,
            'data': data,
            'dims': data.shape,
            'n_dims': len(data.shape),
            'qtype': qtype
        })

    def write(self):
        """Write GGUF file"""

        with open(self.path, 'wb') as f:
            # Header
            f.write(b'GGUF')
            f.write(struct.pack('<I', 3))  # Version
            f.write(struct.pack('<I', len(self.tensor_info)))  # Tensor count
            f.write(struct.pack('<I', 5))  # KV count

            # Metadata
            self._write_metadata(f)

            # Tensor info
            self._write_tensor_info(f)

            # Tensor data
            self._write_tensor_data(f)

    def _write_metadata(self, f):
        """Write metadata key-value pairs"""
        metadata = {
            'general.architecture': 'llama',
            'general.file_type': 3,  # Q4_0
            'llama.context_length': 2048,
            'llama.embedding_length': 4096,
            'llama.block_count': 32,
            'llama.attention.head_count': 32,
        }

        for key, value in metadata.items():
            # Key
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
        data_offset = 0

        for tensor in self.tensor_info:
            # Name
            name_bytes = tensor['name'].encode('utf-8')
            f.write(struct.pack('<I', len(name_bytes)))
            f.write(name_bytes)

            # Dimensions
            f.write(struct.pack('<I', tensor['n_dims']))
            for dim in tensor['dims']:
                f.write(struct.pack('<I', dim))

            # Quantization type
            f.write(struct.pack('<I', tensor['qtype']))

            # Offset (placeholder)
            f.write(struct.pack('<Q', 0))

            # Update offset
            data_offset += tensor['data'].nbytes

    def _write_tensor_data(self, f):
        """Write tensor data"""
        # Align to 32 bytes
        pos = f.tell()
        aligned_pos = (pos + 31) // 32 * 32
        f.write(b'\x00' * (aligned_pos - pos))

        # Write data
        for tensor in self.tensor_info:
            f.write(tensor['data'].tobytes())

            # Align
            pos = f.tell()
            aligned_pos = (pos + 31) // 32 * 32
            f.write(b'\x00' * (aligned_pos - pos))

# Example: Create a simple GGUF file
weights = np.random.randn(4096, 4096).astype(np.float16)
qweights, scales, mins = quantize_q4_0(weights)

# Pack data
tensor_data = np.concatenate([qweights, scales.astype(np.float16).view(np.uint8),
                              mins.astype(np.float16).view(np.uint8)])

writer = GGUFWriter('test_model.gguf', 1)
writer.add_tensor('output.weight', tensor_data, qtype=3)  # Q4_0
writer.write()

print("✓ Created test_model.gguf")
```

**Checkpoint 3:** ✅ GGUF file created

---

## 🔬 Experiment 4: Benchmarking (15 minutes)

### Step 4.1: Performance Comparison

```python
# File: benchmark.py
"""
Benchmark Quantized vs FP16
============================
"""

import numpy as np
import time

# Generate test data
weights_fp16 = np.random.randn(4096, 4096).astype(np.float16)
input_data = np.random.randn(1, 4096).astype(np.float16)

# Quantize
qweights, scales, mins = quantize_q4_0(weights_fp16)

# Benchmark FP16
start = time.time()
for _ in range(100):
    output_fp16 = input_data @ weights_fp16
time_fp16 = time.time() - start

# Dequantize and benchmark
weights_dequant = dequantize_q4_0(qweights, scales, mins, weights_fp16.shape)
start = time.time()
for _ in range(100):
    output_dequant = input_data @ weights_dequant
time_dequant = time.time() - start

print("=== Benchmark Results ===")
print(f"FP16: {time_fp16*1000:.2f} ms")
print(f"Dequantized: {time_dequant*1000:.2f} ms")
print(f"Overhead: {(time_dequant/time_fp16 - 1)*100:.1f}%")

# Memory usage
mem_fp16 = weights_fp16.nbytes
mem_quant = qweights.nbytes + scales.nbytes + mins.nbytes

print(f"\nFP16 Memory: {mem_fp16/1024/1024:.1f} MB")
print(f"Quantized Memory: {mem_quant/1024/1024:.1f} MB")
print(f"Memory Reduction: {(1 - mem_quant/mem_fp16)*100:.1f}%")

# Accuracy
output_diff = np.abs(output_fp16 - output_dequant).mean()
print(f"\nMean Output Difference: {output_diff:.6f}")
```

**Checkpoint 4:** ✅ Benchmarking complete

---

## 📊 Results Analysis

### Expected Results

| Metric | FP16 | Q4_0 | Ratio |
|--------|------|------|-------|
| Memory | 32 MB | 9 MB | 3.5x |
| Speed | 100 ms | 120 ms | 0.83x |
| Accuracy | 1.0 | 0.98 | - |

### When to Use GGUF

- ✅ **Limited VRAM** - Run larger models
- ✅ **CPU inference** - Reduce memory bandwidth
- ✅ **Edge deployment** - Resource-constrained devices
- ❌ **Maximum accuracy** - FP16 is more accurate

---

## ✅ Experiment Checklist

- [ ] GGUF format understood
- [ ] 4-bit quantization implemented
- [ ] GGUF file created
- [ ] Benchmarking completed

---

## 🎓 Key Takeaways

1. **GGUF = Efficient Storage** - Memory-mapped quantized tensors
2. **4-bit = 50% smaller** - Than 8-bit, 75% smaller than FP16
3. **Quantization Error** - Small accuracy trade-off
4. **Block Quantization** - Groups of weights share scale
5. **Fast Loading** - Memory mapping enables quick startup

---

## 🚀 Next Steps

1. **EXP_4102**: EXL2 vs AWQ - Advanced quantization
2. **EXP_4201**: Speculative Decoding - Faster generation
3. **LAB-004**: Custom Quantization - Production implementation

---

**Last Updated:** 2026-02-04
**Experiment:** 4101 - GGUF Quantization
**Time Estimate:** 60-90 minutes
**Difficulty:** ⭐⭐⭐ Advanced
