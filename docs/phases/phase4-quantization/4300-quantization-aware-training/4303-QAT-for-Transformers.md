---
Document ID: 4303
Title: "4303: QAT for Transformers"
Phase: 4
Module: 4300
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'qat', 'quantization-aware-training']
---

# 4303: QAT for Transformers

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Transformer Components to Quantize](#transformer-components-to-quantize)
- [What NOT to Quantize](#what-not-to-quantize)
- [Implementation for Self-Attention](#implementation-for-self-attention)
- [Implementation for MLP/Feed-Forward](#implementation-for-mlpfeed-forward)
- [Complete Transformer Block](#complete-transformer-block)
- [Embedding Layer Quantization](#embedding-layer-quantization)
- [Per-Channel vs Per-Tensor](#per-channel-vs-per-tensor)
- [Training Considerations](#training-considerations)
- [Common Issues](#common-issues)
- [Results Expectations](#results-expectations)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Map the quantize/don't boundaries of a transformer block — Q/K/V/O projections and both MLP Linears carry quantized weights and I/O, while GELU, softmax, and both layer norms stay FP32
- Justify the three FP32 holdouts — layer norm's sensitivity on small values, non-linear activations computed on dequantized inputs, softmax probabilities preserved until `attn_weights @ v`
- Build `QuantizedAttention` — fused qkv Linear, the permute(2,0,3,1,4) head split to (B,H,N,d), per-mode quantizers (asymmetric input/output, symmetric weights), FP32 softmax over (B,H,N,N) scores
- Assemble `QuantizedMLP` — input quant, quantized fc1 into the 4x expansion, FP32 GELU, activation quant, quantized fc2 projection back
- Wire `QuantizedTransformerBlock` — pre-LN norm1/attn and norm2/mlp with residuals, a separate residual quantizer per branch so the two output distributions don't blend in one observer
- Quantize embeddings as lookup-then-fake-quant with a symmetric int8 weight quantizer, and weigh the production shortcut of INT8-from-start against QAT

---

## Abstract

Applying QAT to transformer models requires special handling for attention mechanisms, layer norms, and embeddings.

## Transformer Components to Quantize

```text
Transformer Block
├── Self-Attention
│   ├── Q projection (Linear)      ← Quantize
│   ├── K projection (Linear)      ← Quantize
│   ├── V projection (Linear)      ← Quantize
│   ├── O projection (Linear)      ← Quantize
│   └── Attention output           ← Quantize activations
│
├── Feed-Forward
│   ├── Linear 1 (expansion)       ← Quantize
│   ├── Activation                 ← Don't quantize (GELU/ReLU)
│   └── Linear 2 (projection)      ← Quantize
│
└── Layer Norms                    ← Don't quantize (FP32)
```

## What NOT to Quantize

### 1. Layer Normalization

Layer norms are intentionally kept in FP32:

```python
# WRONG: Don't quantize layer norm
x_norm = fake_quantize(layer_norm(x))  # Bad idea

# CORRECT: Keep layer norm in FP32
x_norm = layer_norm(x)  # Good
x_q = fake_quantize(x_norm)  # Quantize after
```

**Why:** Layer normalization is sensitive and operates on small values. Quantization destroys its stability.

### 2. Non-linear Activations

GELU, ReLU, etc. should operate on dequantized values:

```python
# WRONG
x_q = fake_quantize(x)
activation = gelu(x_q)

# CORRECT
x_q = fake_quantize(x)
x_dq = dequantize(x_q)
activation = gelu(x_dq)
```

### 3. Softmax

Softmax outputs are probability distributions that need precision:

```python
# WRONG
attn_weights = fake_quantize(softmax(scores))

# CORRECT
attn_weights = softmax(scores)  # Keep FP32
# Quantize the final attention output
attn_output = fake_quantize(attn_weights @ v)
```

## Implementation for Self-Attention

```python
# FakeQuantize: use the class from 4302 (torch.ao's namesake has a different constructor)
import torch
import torch.nn as nn
# FakeQuantize is defined in 4302-Fake-Quantization.md — import or paste it
# here (constructor: bit_width, symmetric, momentum, per_channel)

class QuantizedAttention(nn.Module):
    """QAT-compatible attention layer"""

    def __init__(self, embed_dim, num_heads, dropout=0.0):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        # Projections
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)
        self.proj = nn.Linear(embed_dim, embed_dim)

        # Fake quantizers
        self.input_quant = FakeQuantize(bit_width=8, symmetric=False)
        self.weight_quant = FakeQuantize(bit_width=8, symmetric=True)
        self.output_quant = FakeQuantize(bit_width=8, symmetric=False)

        self.dropout = nn.Dropout(dropout)
        self.scale = self.head_dim ** -0.5

    def forward(self, x):
        B, N, C = x.shape

        # Quantize input
        x = self.input_quant(x)

        # QKV projection with weight quantization
        qkv = self._quantized_linear(x, self.qkv)
        qkv = qkv.reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, H, N, d)
        q, k, v = qkv.unbind(0)

        # Attention (keep FP32 for stability)
        attn = (q @ k.transpose(-2, -1)) * self.scale  # (B, H, N, N)
        attn = attn.softmax(dim=-1)
        attn = self.dropout(attn)

        # Attention output
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)

        # Output projection with quantization
        x = self._quantized_linear(x, self.proj)

        # Quantize output
        x = self.output_quant(x)

        return x

    def _quantized_linear(self, x, linear_layer):
        """Apply linear with weight quantization"""
        weight_q = self.weight_quant(linear_layer.weight)
        return nn.functional.linear(x, weight_q, linear_layer.bias)
```

## Implementation for MLP/Feed-Forward

```python
# FakeQuantize: use the class from 4302 (torch.ao's namesake has a different constructor)
class QuantizedMLP(nn.Module):
    """QAT-compatible feed-forward layer"""

    def __init__(self, embed_dim, mlp_ratio=4.0):
        super().__init__()
        hidden_dim = int(embed_dim * mlp_ratio)

        self.fc1 = nn.Linear(embed_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, embed_dim)

        # Quantizers
        self.input_quant = FakeQuantize(bit_width=8, symmetric=False)
        self.weight_quant = FakeQuantize(bit_width=8, symmetric=True)
        self.activation_quant = FakeQuantize(bit_width=8, symmetric=False)

    def forward(self, x):
        # Quantize input
        x = self.input_quant(x)

        # First linear with weight quant
        x = self._quantized_linear(x, self.fc1)

        # Activation (FP32)
        x = nn.functional.gelu(x)

        # Quantize before second linear
        x = self.activation_quant(x)

        # Second linear with weight quant
        x = self._quantized_linear(x, self.fc2)

        return x

    def _quantized_linear(self, x, linear_layer):
        weight_q = self.weight_quant(linear_layer.weight)
        return nn.functional.linear(x, weight_q, linear_layer.bias)
```

## Complete Transformer Block

```python
# FakeQuantize: use the class from 4302 (torch.ao's namesake has a different constructor)
class QuantizedTransformerBlock(nn.Module):
    """QAT-compatible transformer block"""

    def __init__(self, embed_dim, num_heads, mlp_ratio=4.0, dropout=0.0):
        super().__init__()

        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = QuantizedAttention(embed_dim, num_heads, dropout)

        self.norm2 = nn.LayerNorm(embed_dim)
        self.mlp = QuantizedMLP(embed_dim, mlp_ratio)

        # Separate quantizers per branch: one shared instance would blend
        # the attention-output and MLP-output distributions in its observer
        self.residual_quant_attn = FakeQuantize(bit_width=8, symmetric=False)
        self.residual_quant_mlp = FakeQuantize(bit_width=8, symmetric=False)

    def forward(self, x):
        # Attention block with residual
        x = x + self.attn(self.norm1(x))
        x = self.residual_quant_attn(x)  # Quantize residual

        # MLP block with residual
        x = x + self.mlp(self.norm2(x))
        x = self.residual_quant_mlp(x)

        return x
```

## Embedding Layer Quantization

Embeddings are tricky because they're large lookup tables:

```python
# FakeQuantize: use the class from 4302 (torch.ao's namesake has a different constructor)
class QuantizedEmbedding(nn.Module):
    """QAT-compatible embedding layer"""

    def __init__(self, num_embeddings, embedding_dim):
        super().__init__()
        self.weight = nn.Parameter(torch.randn(num_embeddings, embedding_dim))
        self.weight_quant = FakeQuantize(bit_width=8, symmetric=True)

    def forward(self, indices):
        # Look up embeddings (FP32)
        embeddings = self.weight[indices]

        # Quantize embeddings
        embeddings_q = self.weight_quant(embeddings)

        return embeddings_q
```

**Note:** For production, consider INT8 embeddings from the start (no QAT needed).

## Per-Channel vs Per-Tensor

For transformer weights, per-channel is always better:

```python
# Linear weight: [out_features, in_features]
# Per-channel quantization along output dimension

# Per-tensor (BAD for attention)
scale = weight.abs().max() / 127  # Single scale

# Per-channel (GOOD for attention)
scale = weight.abs().max(dim=1, keepdim=True).values / 127
# Shape: [out_features, 1]
```

**Impact:**
- Per-tensor QAT: ~5% accuracy loss at 4-bit
- Per-channel QAT: ~1% accuracy loss at 4-bit

## Training Considerations

### 1. Gradual QAT Enable

```python
# FakeQuantize: use the class from 4302 (torch.ao's namesake has a different constructor)
def train_with_qat(model, epochs, qat_start_epoch=5):
    for epoch in range(epochs):
        if epoch >= qat_start_epoch:
            enable_qat(model)

        train_epoch(model)
        validate(model)

def enable_qat(model):
    """Enable fake quantization"""
    for module in model.modules():
        if isinstance(module, (FakeQuantize, QuantizedAttention)):
            module.train()  # Enable observer updates
```

### 2. Learning Rate Adjustment

QAT often needs lower learning rates:

```python
# Reduce LR when enabling QAT
if epoch == qat_start_epoch:
    for param_group in optimizer.param_groups:
        param_group['lr'] *= 0.5  # Halve learning rate
```

### 3. Accuracy Monitoring

```python
def compute_accuracy(model, dataloader):
    model.eval()
    correct = total = 0

    with torch.no_grad():
        for inputs, labels in dataloader:
            outputs = model(inputs)
            pred = outputs.argmax(dim=1)
            correct += (pred == labels).sum()
            total += labels.size(0)

    return correct / total

# Track throughout training
epochs = 3  # demo scale
for epoch in range(epochs):
    train_epoch(model)
    acc = compute_accuracy(model, val_loader)
    print(f"Epoch {epoch}: Accuracy = {acc:.4f}")
```

## Common Issues

### Issue 1: Attention NaN

**Problem:** Self-attention produces NaN after quantization.

**Diagnosis:**
```python
# Check for NaN in attention weights
if torch.isnan(attn).any():
    print("NaN in attention weights!")
    print(f"Q range: {q.min():.2f} to {q.max():.2f}")
    print(f"K range: {k.min():.2f} to {k.max():.2f}")
```

**Solution:** Increase bit-width for Q/K projections:
```python
# FakeQuantize: use the class from 4302 (torch.ao's namesake has a different constructor)
self.qkv_quant = FakeQuantize(bit_width=16)  # int16 grid (not FP16) relieves Q/K dynamic range
```

### Issue 2: Residual Connection Overflow

**Problem:** Residual addition causes overflow.

**Solution:** Quantize residual separately:
```python
residual = x  # skip path carried around the block
x_q = self.output_quant(x)
residual_q = self.residual_quant(residual)
x = x_q + residual_q  # Both in similar range
```

### Issue 3: First Layer Accuracy Loss

**Problem:** Token embedding layer quantization hurts accuracy.

**Solution:** Keep first layer in FP16:
```python
# FakeQuantize: use the class from 4302 (torch.ao's namesake has a different constructor)
self.embed_quant = FakeQuantize(bit_width=16)  # wider int16 grid for the fragile first layer
```

## Results Expectations

For a well-tuned QAT transformer at 8-bit:
- **Accuracy loss:** <1% vs FP32
- **Model size:** 4x smaller
- **Inference speed:** 2-4x faster (with optimized kernels)

For 4-bit QAT:
- **Accuracy loss:** 1-3% vs FP32
- **Model size:** 8x smaller
- **Inference speed:** 4-8x faster

## Summary

Transformers tolerate QAT well but not uniformly: the recipe this lesson built quantizes the attention and MLP projections while deliberately protecting layer norms, embeddings, and the softmax path. The QKV projections and feed-forward layers carry most of the win; embeddings and the output layer are where accuracy quietly dies. Per-channel weight quantization with per-tensor activations was the default that held up, and the results expectations gave the accuracy bands to hold your own runs against.

## References

### Related Minder Academy Documents

- [4301: QAT Foundations](4301-QAT-Foundations.md)
- [4302: Fake Quantization](4302-Fake-Quantization.md)
- [4304: Low-bit QAT](4304-Low-bit-QAT.md)
- [4305: Quantization Configuration](4305-Quantization-Configuration.md)

---

## Next Steps

→ **[4304: Low-bit QAT](./4304-Low-bit-QAT.md)** - Techniques for 4-bit and below
