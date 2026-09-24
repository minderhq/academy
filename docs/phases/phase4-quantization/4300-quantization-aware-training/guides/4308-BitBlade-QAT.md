# 4308: BitBlade QAT Guide

## Abstract

BitBlade is an advanced quantization library that provides state-of-the-art low-bit quantization techniques. This guide covers using BitBlade for extreme compression.

## What is BitBlade?

BitBlade combines multiple quantization techniques:
- **NF4 (NormalFloat 4)**: Optimal 4-bit data type
- **Double Quantization**: Quantizing the quantization parameters
- **Mixed Precision**: Different bits for different layers
- **Adaptive Rounding**: Smart rounding strategies

## Installation

```bash
# Install BitBlade
pip install bitblade

# Install with extras for CUDA support
pip install bitblade[cuda]

# Install development version
pip install git+https://github.com/bitblade-ai/bitblade.git
```

## Basic Usage

### Load Model with NF4 Quantization

```python
import torch
from bitblade import quantize_model, NF4Config
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "meta-llama/Llama-2-7b-hf"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load model
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Quantize with NF4
config = NF4Config(
    bits=4,
    double_quant=True,  # Quantize the quantizers
    quant_type="nf4",
)

model_quantized = quantize_model(model, config)

# Check memory
print(f"Original: {model.get_memory_footprint() / 1e9:.2f} GB")
print(f"Quantized: {model_quantized.get_memory_footprint() / 1e9:.2f} GB")
```

### Fine-tuning Quantized Model

```python
from bitblade import prepare_for_training

# Prepare model for training
model_for_training = prepare_for_training(model_quantized)

# Add trainable adapters (LoRA-style)
from bitblade import add_adapters

model_for_training = add_adapters(
    model_for_training,
    adapter_type="lora",
    r=16,
    alpha=32,
    target_modules=["q_proj", "v_proj"],
    dropout=0.1,
)

# Train
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
)

trainer = Trainer(
    model=model_for_training,
    args=training_args,
    train_dataset=train_dataset,
)

trainer.train()
```

## Advanced Configuration

### Per-Layer Quantization Config

```python
from bitblade import LayerWiseConfig

# Define different configs for different layers
layer_config = {
    'embeddings': {
        'bits': 8,
        'symmetric': True,
    },
    'layers.0-10': {  # Early layers
        'bits': 8,
        'double_quant': True,
    },
    'layers.11-20': {  # Middle layers
        'bits': 4,
        'quant_type': 'nf4',
        'double_quant': True,
    },
    'layers.21-32': {  # Late layers
        'bits': 4,
        'quant_type': 'nf4',
    },
}

config = LayerWiseConfig(layer_config)
model_quantized = quantize_model(model, config)
```

### Adaptive Precision Selection

```python
from bitblade import AutoBitConfig

# Automatically determine optimal bit-width per layer
config = AutoBitConfig(
    target_size_gb=4.0,  # Target model size
    min_bits=2,
    max_bits=8,
    metric='perplexity',  # Optimize for perplexity
    calibration_data=calibration_dataloader,
)

model_quantized = quantize_model(model, config)
```

### Custom Quantization Scheme

```python
from bitblade import CustomQuantConfig

# Define custom quantization
class MyQuantScheme:
    def __init__(self, bits=4):
        self.bits = bits

    def quantize(self, tensor):
        # Custom quantization logic
        scale = tensor.abs().max() / (2 ** (self.bits - 1) - 1)
        quantized = torch.round(tensor / scale)
        return torch.clamp(quantized, -2**3, 2**3-1) * scale

# Apply custom scheme
config = CustomQuantConfig(
    quant_scheme=MyQuantScheme(bits=4),
    layers=['model.layers.*.mlp'],
)

model_quantized = quantize_model(model, config)
```

## Mixed Precision Training

```python
from bitblade import MixedPrecisionTraining

# Configure mixed precision
mp_config = {
    'embeddings': 'fp16',
    'attention': 'int8',
    'mlp': 'nf4',
    'output': 'fp16',
}

# Prepare model
model_mp = MixedPrecisionTraining(model, mp_config)

# Training loop
optimizer = torch.optim.AdamW(model_mp.parameters(), lr=1e-4)

for epoch in range(epochs):
    for batch in dataloader:
        # Different parts run at different precision
        loss = model_mp(**batch)
        loss.backward()
        optimizer.step()
```

## Calibration

```python
from bitblade import calibrate_quantization

# Calibration data (subset of training data)
calibration_loader = get_calibration_dataloader(batch_size=8, num_samples=128)

# Calibrate quantization parameters
model_quantized = calibrate_quantization(
    model,
    calibration_loader,
    method='percentile',  # or 'entropy', 'mse'
    percentile=99.9,  # For percentile method
    num_iterations=100,
)
```

## Evaluation

### Accuracy Evaluation

```python
from bitblade.evaluation import evaluate_model

results = evaluate_model(
    model_fp32=model,
    model_quantized=model_quantized,
    eval_dataloader=test_loader,
    metrics=['perplexity', 'accuracy'],
)

print(results)
# {
#     'fp32_perplexity': 12.4,
#     'quantized_perplexity': 13.1,
#     'fp32_accuracy': 0.85,
#     'quantized_accuracy': 0.84,
#     'perplexity_loss': 0.7,
#     'accuracy_loss': 0.01,
# }
```

### Inference Benchmark

```python
from bitblade.benchmark import benchmark_inference

benchmark_results = benchmark_inference(
    model_fp32=model,
    model_quantized=model_quantized,
    input_shape=(1, 2048),  # (batch_size, sequence_length)
    num_iterations=100,
    warmup_iterations=10,
)

print(benchmark_results)
# {
#     'fp32_latency_ms': 245.3,
#     'quantized_latency_ms': 89.2,
#     'speedup': 2.75,
#     'fp32_memory_mb': 13000,
#     'quantized_memory_mb': 3500,
#     'compression_ratio': 3.71,
# }
```

## Exporting

### Export to ONNX

```python
from bitblade.export import export_to_onnx

export_to_onnx(
    model_quantized,
    output_path="model_quantized.onnx",
    opset_version=17,
    input_names=['input_ids', 'attention_mask'],
    output_names=['logits'],
    dynamic_axes={
        'input_ids': {0: 'batch_size', 1: 'sequence_length'},
        'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
        'logits': {0: 'batch_size', 1: 'sequence_length'},
    },
)
```

### Export to GGUF (llama.cpp)

```python
from bitblade.export import export_to_gguf

export_to_gguf(
    model_quantized,
    output_path="model-q4.gguf",
    quant_type="q4_k_m",  # GGUF quant type
    vocab_size=32000,
)
```

## Best Practices

### 1. Start with Double Quantization

```python
# Double quantization is almost always beneficial
config = NF4Config(
    bits=4,
    double_quant=True,  # Enable this
    quant_type="nf4",
)
```

### 2. Use Per-Channel for Weights

```python
config = NF4Config(
    bits=4,
    weight_quantization='per_channel',  # Better accuracy
    activation_quantization='per_tensor',  # Faster
)
```

### 3. Validate on Diverse Data

```python
# Test on different types of inputs
test_cases = [
    "Short text",
    "Medium length text with more details",
    "Long text " * 100,  # Very long
    "Special chars: @#$%^&*()",
    "Multiple\nlines\nof\ntext",
]

for text in test_cases:
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model_quantized.generate(**inputs, max_length=50)
    print(f"Input: {text[:50]}...")
    print(f"Output: {tokenizer.decode(outputs[0])}")
    print("-" * 50)
```

### 4. Monitor Training Stability

```python
from bitblade.monitoring import QuantizationMonitor

monitor = QuantizationMonitor(model_quantized)

# Track quantization statistics during training
for epoch in range(epochs):
    train_epoch(model_quantized)

    # Check statistics
    stats = monitor.get_statistics()
    print(f"Epoch {epoch}: {stats}")
    # {
    #     'outlier_ratio': 0.001,
    #     'zero_point_drift': 0.02,
    #     'scale_variance': 0.15,
    # }
```

## Troubleshooting

### Issue: Out of Memory During Quantization

```python
# Quantize layer by layer
from bitblade import quantize_sequential

model_quantized = quantize_sequential(
    model,
    config=NF4Config(bits=4),
    batch_size=1,
    offload_folder="./offload",
)
```

### Issue: Large Accuracy Drop

```python
# Use hybrid quantization
config = HybridConfig(
    sensitive_layers=['embeddings', 'layer.*.attention'],  # Keep at 8-bit
    other_layers=4,  # Quantize to 4-bit
)

model_quantized = quantize_model(model, config)
```

### Issue: Slow Inference

```python
# Compile model
model_quantized = torch.compile(model_quantized, mode="max-autotune")

# Or use optimized backend
from bitblade.backends import IPEXBackend

model_quantized = IPEXBackend.compile(model_quantized)
```

## Comparison with Other Libraries

| Feature | BitBlade | bitsandbytes | AutoGPTQ |
|---------|----------|--------------|----------|
| **NF4** | ✅ | ✅ | ❌ |
| **Double Quant** | ✅ | ✅ | ❌ |
| **Training** | ✅ | Limited | ❌ |
| **INT3** | ✅ | ❌ | ❌ |
| **Export** | ONNX, GGUF | Transformers | GGUF |
| **Speed** | Fastest | Fast | Medium |

## Further Resources

- **GitHub:** https://github.com/bitblade-ai/bitblade
- **Documentation:** https://docs.bitblade.ai
- **Paper:** "BitBlade: Advanced Quantization for LLMs"
- **Discord:** https://discord.gg/bitblade

## Summary

BitBlade provides the most advanced quantization techniques for LLMs:

- **NF4:** Optimal 4-bit data type
- **Double Quantization:** Compress quantization parameters
- **Mixed Precision:** Layer-wise bit-width
- **Production Ready:** Export to ONNX, GGUF

Use BitBlade when you need:
- Maximum compression
- State-of-the-art accuracy
- Easy export to production
- Active development


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Last Updated:** 2026-02-04
