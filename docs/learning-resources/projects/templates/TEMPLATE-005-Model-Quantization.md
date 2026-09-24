# PROJECT TEMPLATE: Model Quantization

Quantize LLMs for efficient deployment.

## Project Structure

```text
quantization-project/
├── README.md
├── requirements.txt
├── config/
│   ├── quantization_config.yaml
│   └── models_config.yaml
├── src/
│   ├── __init__.py
│   ├── quantizers/
│   │   ├── __init__.py
│   │   ├── dynamic.py       # Dynamic quantization
│   │   ├── static.py        # Post-training quantization
│   │   ├── gptq.py          # GPTQ quantization
│   │   └── awq.py           # AWQ quantization
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── perplexity.py
│   │   └── accuracy.py
│   ├── benchmark.py         # Performance benchmarking
│   └── converter.py         # Format conversion
├── models/
│   └── .gitkeep
├── scripts/
│   ├── quantize.py
│   ├── evaluate.py
│   └── benchmark.py
└── tests/
    └── test_quantization.py
```

## Features

- Multiple quantization methods
- Benchmarking tools
- Evaluation metrics
- Format conversion (GGUF, EXL2)
- Comparison tools

## Quick Start

### Dynamic Quantization

```python
from src.quantizers.dynamic import DynamicQuantizer

quantizer = DynamicQuantizer()
quantized_model = quantizer.quantize(model)
```

### GPTQ Quantization

```python
from src.quantizers.gptq import GPTQQuantizer

quantizer = GPTQQuantizer(bits=4, group_size=128)
quantized_model = quantizer.quantize(
    model,
    calibration_data=calibration_dataset
)
```

### AWQ Quantization

```python
from src.quantizers.awq import AWQQuantizer

quantizer = AWQQuantizer()
quantized_model = quantizer.quantize(model)
```

## Benchmarking

```bash
python scripts/benchmark.py \
  --model meta-llama/Llama-2-7b-hf \
  --quantization gptq \
  --bits 4
```

Compare:
- Model size
- Inference speed
- Memory usage
- Quality metrics

## Evaluation

```bash
python scripts/evaluate.py \
  --model ./models/llama-7b-gptq \
  --dataset wikitext \
  --metrics perplexity,bleu
```

## Conversion

Convert to GGUF for llama.cpp:
```bash
python src/converter.py \
  --input ./models/llama-7b-gptq \
  --output ./models/llama-7b.gguf \
  --format gguf
```

## Quantization Options

| Method | Bits | Size Reduction | Speed | Quality |
|--------|------|----------------|-------|---------|
| Dynamic | 8 | 2x | Fast | Minimal loss |
| PTQ | 4 | 4x | Medium | Small loss |
| GPTQ | 4 | 4x | Medium | Minimal loss |
| AWQ | 4 | 4x | Fast | Minimal loss |

---

**Difficulty:** Intermediate
**Estimated Time:** 4-8 hours
**Skills:** Quantization, Benchmarking, Model optimization
