# 4100: Low-Bit Quantization - Practice

## Exercises

### Exercise 1: Manual Post-Training Quantization

```python
import torch
import torch.nn as nn

def quantize_per_tensor(tensor, dtype=torch.qint8):
    """
    Manual per-tensor quantization.

    Args:
        tensor: Input tensor to quantize
        dtype: Target quantized dtype (qint8 or quint8)

    Returns:
        Quantized tensor, scale, zero_point
    """
    # Determine quantization range
    qmin = torch.iinfo(dtype).min
    qmax = torch.iinfo(dtype).max

    # Find min and max values
    min_val = tensor.amin()
    max_val = tensor.amax()

    # Calculate scale and zero point
    scale = (max_val - min_val) / (qmax - qmin)
    zero_point = qmin - (min_val / scale)
    zero_point = torch.clamp(torch.round(zero_point), qmin, qmax).to(torch.int64)

    # Quantize
    quantized = torch.round(tensor / scale) + zero_point
    quantized = torch.clamp(quantized, qmin, qmax).to(dtype)

    return quantized, scale, zero_point

def dequantize(quantized, scale, zero_point):
    """Dequantize tensor back to float."""
    dequant = (quantized.float() - zero_point.float()) * scale
    return dequant

# Test quantization
print("Manual Post-Training Quantization")
print("="*60)

# Create a weight tensor
weight = torch.randn(256, 512)

# Quantize to int8
q_weight, scale, zp = quantize_per_tensor(weight, dtype=torch.qint8)

# Dequantize
dq_weight = dequantize(q_weight, scale, zp)

# Calculate error
error = torch.abs(weight - dq_weight).mean()
max_error = torch.abs(weight - dq_weight).max()

print(f"Original shape: {weight.shape}")
print(f"Original dtype: {weight.dtype}")
print(f"Quantized dtype: {q_weight.dtype}")
print(f"Scale: {scale:.6f}")
print(f"Zero point: {zp}")
print(f"\nQuantization error (mean): {error:.6f}")
print(f"Quantization error (max): {max_error:.6f}")

# Compression ratio
original_size = weight.numel() * weight.element_size()
quantized_size = q_weight.numel() * q_weight.element_size()
compression = original_size / quantized_size

print(f"\nOriginal size: {original_size / 1024:.2f} KB")
print(f"Quantized size: {quantized_size / 1024:.2f} KB")
print(f"Compression ratio: {compression:.2f}x")

# Expected Output:
# Error should be small (< 0.01 for good quantization)
# Compression ratio: 4x (float32 to int8)
```

**Explanation:**
- PTQ converts trained models to lower precision
- Scale and zero_point map float to int range
- Dequantization restores to float for computation
- Simple but can introduce accuracy loss

**Pros:** Fast, no retraining needed
**Cons:** Can lose accuracy at low bit-widths

---

### Exercise 2: Dynamic Quantization

```python
import torch
import torch.nn as nn
import time

# Create a simple model
class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 512)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 10)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Apply dynamic quantization
model = SimpleModel()

print("Dynamic Quantization")
print("="*60)

# Quantize dynamically
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {nn.Linear},  # Layers to quantize
    dtype=torch.qint8  # Target dtype
)

# Compare sizes
def get_model_size(model):
    """Get model size in MB."""
    torch.save(model.state_dict(), 'temp.pt')
    size = __import__('os').path.getsize('temp.pt') / (1024 * 1024)
    __import__('os').remove('temp.pt')
    return size

original_size = get_model_size(model)
quantized_size = get_model_size(quantized_model)

print(f"Original model size: {original_size:.2f} MB")
print(f"Quantized model size: {quantized_size:.2f} MB")
print(f"Compression: {original_size / quantized_size:.2f}x")

# Compare inference speed
def measure_inference_time(model, inputs, n_runs=100):
    """Measure average inference time."""
    model.eval()
    times = []

    with torch.no_grad():
        for _ in range(n_runs):
            start = time.perf_counter()
            _ = model(inputs)
            end = time.perf_counter()
            times.append(end - start)

    return sum(times) / len(times)

dummy_input = torch.randn(1, 784)

original_time = measure_inference_time(model, dummy_input)
quantized_time = measure_inference_time(quantized_model, dummy_input)

print(f"\nOriginal inference time: {original_time*1000:.2f} ms")
print(f"Quantized inference time: {quantized_time*1000:.2f} ms")
print(f"Speedup: {original_time/quantized_time:.2f}x")

# Inspect quantized layers
print("\nQuantized Layers:")
for name, module in quantized_model.named_modules():
    if isinstance(module, torch.nn.quantized.Linear):
        print(f"  {name}: {module.weight().dtype}")

# Expected Output:
# Model size reduced by ~2-4x
# Inference speedup of 1.5-3x
# Linear layers converted to qint8
```

**Explanation:**
- Dynamic quantization happens at runtime
- Weights quantized ahead of time
- Activations quantized dynamically
- Good for LSTMs, Transformers

**Best Practices:**
- Quantize Linear layers
- Leave embeddings in FP32/FP16
- Test accuracy after quantization

---

### Exercise 3: Static Quantization

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Prepare calibration data
def prepare_calibration_data(size=1000):
    """Generate dummy calibration data."""
    data = torch.randn(size, 784)
    labels = torch.randint(0, 10, (size,))
    dataset = TensorDataset(data, labels)
    return DataLoader(dataset, batch_size=32)

# Define model
class MNISTModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.quant = torch.quantization.QuantStub()
        self.fc1 = nn.Linear(784, 256)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(256, 10)
        self.dequant = torch.quantization.DeQuantStub()

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = self.quant(x)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        x = self.dequant(x)
        return x

print("Static (Post-Training) Quantization")
print("="*60)

# Create model
model = MNISTModel()
model.eval()

# Specify quantization configuration
model.qconfig = torch.quantization.get_default_qconfig('fbgemm')

# Prepare model for quantization
prepared_model = torch.quantization.prepare(model, inplace=False)

# Calibrate with representative data
calibration_data = prepare_calibration_data()

print("Calibrating with representative data...")
with torch.no_grad():
    for data, _ in calibration_data:
        prepared_model(data)

# Convert to quantized model
quantized_model = torch.quantization.convert(prepared_model, inplace=False)

print("Quantization complete!")

# Compare
original_size = get_model_size(model)
quantized_size = get_model_size(quantized_model)

print(f"\nOriginal size: {original_size:.2f} MB")
print(f"Quantized size: {quantized_size:.2f} MB")
print(f"Compression: {original_size / quantized_size:.2f}x")

# Test inference
dummy_input = torch.randn(1, 784)
original_output = model(dummy_input)
quantized_output = quantized_model(dummy_input)

output_diff = torch.abs(original_output - quantized_output).mean()
print(f"\nOutput difference: {output_diff:.6f}")

# Expected Output:
# Static quantization yields better accuracy than dynamic
# Requires calibration data
# ~4x compression
```

**Explanation:**
- Static quantization uses calibration data
- Determines activation ranges beforehand
- Better accuracy than dynamic
- Requires representative dataset

**Calibration Tips:**
- Use ~100-1000 representative samples
- Cover data distribution
- Avoid outliers in calibration set

---

### Exercise 4: BitsAndBytes 4-bit Quantization

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

print("BitsAndBytes 4-bit Quantization")
print("="*60)

# Configure 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",  # Normal Float 4
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,  # Double quantization
)

# Note: This requires a GPU and the transformers library
# Uncomment to run with actual model:
"""
model_name = "meta-llama/Llama-2-7b-hf"  # Or "gpt2" for testing

# Load model with 4-bit quantization
print(f"Loading {model_name} with 4-bit quantization...")
model_4bit = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Inspect quantized layers
print("\nQuantized Layers:")
for name, param in model_4bit.named_parameters():
    if param.dtype == torch.uint8:
        print(f"  {name}: {param.dtype} (quantized)")

# Test inference
prompt = "The future of AI is"
inputs = tokenizer(prompt, return_tensors="pt").to(model_4bit.device)

with torch.no_grad():
    outputs = model_4bit.generate(**inputs, max_new_tokens=20)

text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"\nGenerated text: {text}")

# Compare memory usage
def get_model_memory(model):
    """Get model memory usage in GB."""
    mem = 0
    for param in model.parameters():
        mem += param.numel() * param.element_size()
    return mem / (1024**3)

memory_4bit = get_model_memory(model_4bit)
print(f"\nModel memory (4-bit): {memory_4bit:.2f} GB")
"""

# Example with smaller model for demonstration
print("\nFor demonstration, using a smaller model:")
print("To use with Llama-2 or GPT-2, uncomment the code above.")
print("\nKey points:")
print("- NF4: Optimal distribution for normally distributed weights")
print("- Double quantization: Quantizes the quantization constants")
print("- Compute dtype: Use FP16 or BF16 for computations")
print("- Typical compression: ~8x (FP32 to INT4)")

# Expected Output:
# Model loaded in 4-bit precision
# Significant memory reduction (~8x for large models)
# Minimal accuracy loss with NF4
```

**Explanation:**
- BitsAndBytes enables on-the-fly 4-bit quantization
- NF4: optimal for normally distributed weights
- Double quantization: saves additional memory
- No need for pre-quantized models

**Use Cases:**
- Running large models on limited GPU memory
- LLaMA, Falcon, Mistral models
- Inference with minimal accuracy loss

---

### Exercise 5: Quantization Error Analysis

```python
import torch
import matplotlib.pyplot as plt
import numpy as np

def analyze_quantization_error(original_tensor, quantized_tensor):
    """
    Analyze quantization error in detail.
    """
    # Calculate error metrics
    abs_error = torch.abs(original_tensor - quantized_tensor)
    rel_error = abs_error / (torch.abs(original_tensor) + 1e-8)

    mse = torch.mean((original_tensor - quantized_tensor) ** 2)
    mae = torch.mean(abs_error)
    max_error = torch.max(abs_error)

    # Signal-to-quantization-noise ratio
    signal_power = torch.mean(original_tensor ** 2)
    noise_power = torch.mean((original_tensor - quantized_tensor) ** 2)
    sqnr = 10 * torch.log10(signal_power / (noise_power + 1e-8))

    results = {
        'mse': mse.item(),
        'mae': mae.item(),
        'max_error': max_error.item(),
        'sqnr_db': sqnr.item(),
        'mean_rel_error': torch.mean(rel_error).item()
    }

    return results

def compare_bit_widths(tensor, bit_widths=[4, 8, 16]):
    """Compare quantization at different bit widths."""
    results = {}

    for bits in bit_widths:
        if bits == 4:
            dtype = torch.qint8  # Approximate for 4-bit
            scale_factor = 0.1
        elif bits == 8:
            dtype = torch.qint8
            scale_factor = 1.0
        else:
            dtype = torch.qint8
            scale_factor = 1.0

        # Simple quantization simulation
        qmin = -(2 ** (bits - 1))
        qmax = 2 ** (bits - 1) - 1

        scale = tensor.max() / qmax * scale_factor
        quantized = torch.round(tensor / scale)
        quantized = torch.clamp(quantized, qmin, qmax)
        dequantized = quantized * scale

        error = analyze_quantization_error(tensor, dequantized)
        results[bits] = error

    return results

# Test error analysis
print("Quantization Error Analysis")
print("="*60)

# Create a weight tensor with normal distribution
weight = torch.randn(128, 256)

# Compare different bit widths
error_results = compare_bit_widths(weight, bit_widths=[4, 8, 16, 32])

print("\nError Metrics by Bit Width:")
print("-" * 60)
print(f"{'Bits':<8} {'MSE':<12} {'MAE':<12} {'SQNR (dB)':<12}")
print("-" * 60)

for bits, metrics in sorted(error_results.items()):
    print(f"{bits:<8} {metrics['mse']:<12.6f} {metrics['mae']:<12.6f} {metrics['sqnr_db']:<12.2f}")

# Visualize error distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Original vs quantized histogram
ax = axes[0]
ax.hist(weight.flatten().numpy(), bins=50, alpha=0.5, label='Original', density=True)
for bits in [8, 4]:
    qmin = -(2 ** (bits - 1))
    qmax = 2 ** (bits - 1) - 1
    scale = weight.max() / qmax
    quantized = torch.round(weight / scale)
    quantized = torch.clamp(quantized, qmin, qmax)
    dequantized = quantized * scale
    ax.hist(dequantized.flatten().numpy(), bins=50, alpha=0.3, label=f'{bits}-bit', density=True)

ax.set_xlabel('Value')
ax.set_ylabel('Density')
ax.set_title('Weight Distribution Comparison')
ax.legend()

# Error by bit width
ax = axes[1]
bit_widths = sorted(error_results.keys())
sqnr_values = [error_results[b]['sqnr_db'] for b in bit_widths]
ax.plot(bit_widths, sqnr_values, marker='o', linewidth=2)
ax.set_xlabel('Bit Width')
ax.set_ylabel('SQNR (dB)')
ax.set_title('Signal-to-Quantization-Noise Ratio')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Expected Output:
# Lower bits = higher error
# SQNR increases with bit width
# 16-bit usually sufficient for minimal loss
```

---

## Summary: Quantization Trade-offs

```yaml
BIT WIDTH → USE CASE:

32-bit (FP32):
  - Training, maximum precision
  - Baseline, research

16-bit (FP16/BF16):
  - Training with mixed precision
  - Faster computation, half memory
  - Minimal accuracy loss

8-bit (INT8):
  - Inference optimization
  - 4x compression
  - Small accuracy loss

4-bit (INT4):
  - Extreme compression
  - Edge deployment
  - May need QAT for good accuracy

QUANTIZATION METHODS:

Dynamic:
  - Fastest to apply
  - Weights quantized, activations dynamic
  - Good for LSTMs, Transformers

Static (PTQ):
  - Better accuracy
  - Requires calibration
  - Good for CNNs

QAT:
  - Best accuracy
  - Requires retraining
  - Needed for very low bits

TIPS:
- Start with PTQ before QAT
- Calibrate with representative data
- Test accuracy after quantization
- Consider per-channel quantization
- Keep sensitive layers in FP16
```

---

**Last Updated:** 2026-02-05
