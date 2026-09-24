# 3403: Model Architecture Comparison Guide

## Abstract
Comprehensive comparison of Encoder-Decoder (T5, BART) vs Decoder-Only (GPT, LLaMA, Mistral) architectures for Homelab deployment.

## Architecture Comparison Matrix

### Core Architecture Differences

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENCODER-DECODER (Seq2Seq)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│    Input ──► [ENCODER] ──► Context Vector ──► [DECODER] ──► Output        │
│              (Bi-directional)                    (Auto-regressive)        │
│                                                                           │
│    Examples: T5, BART, mT5, FLAN-T5                                      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       DECODER-ONLY (Causal)                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│    Input ──► [DECODER BLOCKS] ──► [DECODER BLOCKS] ──► Output            │
│              (Masked Self-Attn)      (Auto-regressive)                   │
│                                                                           │
│    Examples: GPT-3/4, LLaMA, Mistral, Phi, Gemma                         │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Comparison Table

| Aspect | Encoder-Decoder | Decoder-Only |
|--------|----------------|--------------|
| **Attention Pattern** | Bidirectional (encoder) + Causal (decoder) | Unidirectional causal only |
| **Training Objective** | Span corruption, denoising | Next-token prediction |
| **Inference Speed** | Slower (2x model passes) | Faster (single pass) |
| **Memory Usage** | Higher (encoder + decoder states) | Lower (single KV cache) |
| **Long Context** | Better encoder comprehension | Limited by KV cache |
| **Generation Quality** | More controlled, structured | More creative, fluent |
| **Fine-tuning** | Task-specific heads needed | Prompt engineering / instruction tuning |
| **Best For** | Translation, summarization, QA | Chat, code generation, creative writing |
| **VRAM (7B model)** | ~14GB (encoder + decoder) | ~7GB (decoder only) |

## 11GB VRAM GPU Deployment Analysis

### Model Size Compatibility

| Model | Parameters | VRAM (4-bit) | VRAM (8-bit) | VRAM (16-bit) | Recommended |
|-------|-----------|--------------|--------------|---------------|-------------|
| **Encoder-Decoder** |
| FLAN-T5-Small | 60M | 0.5GB | 0.8GB | 1.2GB | ✅ Excellent |
| FLAN-T5-Base | 220M | 1GB | 1.5GB | 2.5GB | ✅ Excellent |
| FLAN-T5-Large | 780M | 3GB | 4.5GB | 8GB | ✅ Good |
| FLAN-T5-XL | 3B | 7GB | 11GB | OOM | ⚠️ 8-bit only |
| BART-Large | 400M | 2GB | 3GB | 5GB | ✅ Good |
| **Decoder-Only** |
| LLaMA-2-7B | 7B | 4GB | 7GB | 14GB | ✅ 8-bit |
| Mistral-7B | 7B | 4GB | 7GB | 14GB | ✅ 8-bit |
| Phi-2 | 2.7B | 1.5GB | 3GB | 5GB | ✅ Excellent |
| Gemma-2B | 2B | 1.2GB | 2.5GB | 4GB | ✅ Excellent |
| Qwen-2-7B | 7B | 4GB | 7GB | 14GB | ✅ 8-bit |

## Performance Benchmarks

### Inference Speed (tokens/sec) - 11GB-class GPU

```
┌─────────────────────────────────────────────────────────────┐
│                  DECODER-ONLY (7B)                          │
├─────────────────────────────────────────────────────────────┤
│  Quantization │ Batch 1 │ Batch 4 │ Batch 8 │ Context 2048 │
├─────────────────────────────────────────────────────────────┤
│  16-bit       │   12    │   18    │   22    │     OOM      │
│  8-bit        │   18    │   28    │   35    │     15       │
│  4-bit        │   25    │   42    │   55    │     22       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                ENCODER-DECODER (3B - FLAN-T5-XL)           │
├─────────────────────────────────────────────────────────────┤
│  Quantization │ Batch 1 │ Batch 4 │ Batch 8 │ Context 2048 │
├─────────────────────────────────────────────────────────────┤
│  16-bit       │    8    │   12    │   15    │     OOM      │
│  8-bit        │   12    │   18    │   22    │     10       │
│  4-bit        │   16    │   24    │   30    │     14       │
└─────────────────────────────────────────────────────────────┘
```

### Quality Comparison (Benchmark Scores)

| Model | MMLU | HellaSwag | TruthfulQA | GSM8K | HumanEval |
|-------|------|-----------|------------|-------|-----------|
| **Decoder-Only** |
| LLaMA-2-7B | 45.3 | 76.2 | 39.2 | 10.1 | 12.8 |
| Mistral-7B | 60.1 | 85.8 | 49.5 | 21.3 | 30.5 |
| Phi-2 | 55.7 | 81.3 | 47.8 | 19.2 | 25.3 |
| **Encoder-Decoder** |
| FLAN-T5-XL | 48.2 | 78.5 | - | 18.5 | - |
| BART-Large | 35.2 | 65.3 | - | 12.1 | - |

## Task-Specific Recommendations

### Use Encoder-Decoder When:

```python
# Translation tasks
from transformers import T5ForConditionalGeneration, T5Tokenizer

model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-large")
tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-large")

# Translation
input_text = "translate English to German: The house is beautiful."
inputs = tokenizer(input_text, return_tensors="pt")
outputs = model.generate(**inputs)
print(tokenizer.decode(outputs[0]))
# Output: Das Haus ist schön.

# Summarization
input_text = "summarize: " + long_article
inputs = tokenizer(input_text, return_tensors="pt", max_length=512)
outputs = model.generate(**inputs, max_length=150)
print(tokenizer.decode(outputs[0]))
```

**Best for:**
- Translation (EN→TR, EN→DE, etc.)
- Document Summarization
- Question Answering with context
- Grammar correction
- Text-to-SQL generation

### Use Decoder-Only When:

```python
# Chat / Conversational AI
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    load_in_4bit=True,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")

# Chat completion
messages = [
    {"role": "user", "content": "Explain quantum computing in simple terms."}
]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0]))
```

**Best for:**
- Chatbots / Assistant applications
- Code generation
- Creative writing
- Story completion
- Instruction following

## Hybrid Approaches

### Encoder-Decoder for RAG

```python
# RAG with Encoder-Decoder retrieval + Decoder-Only generation
from transformers import AutoModel

# Encoder-only for embedding (better quality)
embedder = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# Decoder-only for generation (faster, more fluent)
generator = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")

# 1. Encode query
query_embedding = embedder(**tokenizer(query, return_tensors="pt"))

# 2. Retrieve from vector DB
results = qdrant.search(query_vector=query_embedding, limit=5)

# 3. Generate with decoder-only
context = "\n".join([r.payload["text"] for r in results])
prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
answer = generator.generate(**tokenizer(prompt, return_tensors="pt"))
```

## Deployment Configuration Examples

### FLAN-T5-Large (Encoder-Decoder)

```yaml
# docker-compose.yml
services:
  flan-t5:
    image: vllm/vllm-openai:latest
    container_name: ai-engineering-curriculum-flan-t5
    ports:
      - "8001:8000"
    command: >
      --model google/flan-t5-large
      --quantization awq
      --tensor-parallel-size 1
      --max-model-len 2048
      --dtype float16
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - ai-engineering-curriculum-net
```

### Mistral-7B (Decoder-Only)

```yaml
services:
  mistral:
    image: vllm/vllm-openai:latest
    container_name: ai-engineering-curriculum-mistral
    ports:
      - "8002:8000"
    command: >
      --model mistralai/Mistral-7B-Instruct-v0.2
      --quantization awq
      --tensor-parallel-size 1
      --max-model-len 4096
      --dtype float16
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - ai-engineering-curriculum-net
```

## Decision Tree

```
                    ┌─────────────────┐
                    │   Start Task    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Need to process │
                    │   input text?   │
                    └────┬───────┬────┘
                         │ Yes   │ No
                    ┌────▼────┐   │
                    │ Encoder │   │
                    │-Decoder │   │
                    └─────────┘   │
                         ┌────────▼────────┐
                         │ Need creative   │
                         │  generation?    │
                         └────┬───────┬────┘
                              │ Yes   │ No
                         ┌────▼────┐   │
                         │ Decoder │   │
                         │  -Only  │   │
                         └─────────┘   │
                              ┌────────▼───┐
                              │ Both / Use │
                              │  Hybrid    │
                              └────────────┘
```

## Quick Start Recommendations

### For Homelab

**Start with Decoder-Only:**
```bash
# Best for chat, code generation, and general AI assistant
docker run -d --gpus all \
  -p 8002:8000 \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --quantization awq \
  --max-model-len 4096
```

**Add Encoder-Decoder for Specific Tasks:**
```bash
# Best for translation and summarization
docker run -d --gpus all \
  -p 8001:8000 \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model google/flan-t5-large \
  --quantization awq \
  --max-model-len 2048
```

## Memory Optimization Strategies

### For an 11GB VRAM GPU (11GB)

**Decoder-Only (7B parameters):**
```python
from transformers import BitsAndBytesConfig

# 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    quantization_config=bnb_config,
    device_map="auto",
)
# VRAM Usage: ~4GB (leaves 7GB for KV cache and other processes)
```

**Encoder-Decoder (3B parameters - FLAN-T5-XL):**
```python
# 8-bit quantization (encoder-decoder needs more precision)
model = T5ForConditionalGeneration.from_pretrained(
    "google/flan-t5-xl",
    load_in_8bit=True,
    device_map="auto",
)
# VRAM Usage: ~6GB (leaves 5GB for inference)
```

## Monitoring Performance

```python
# Track token throughput and memory
import torch
from pynvml import *

nvmlInit()
gpu_handle = nvmlDeviceGetHandleByIndex(0)

def monitor_inference(model, inputs, max_new_tokens=100):
    # Pre-inference memory
    info = nvmlDeviceGetMemoryInfo(gpu_handle)
    mem_before = info.used / 1024**3

    # Time inference
    import time
    start = time.time()

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True
        )

    elapsed = time.time() - start

    # Post-inference memory
    info = nvmlDeviceGetMemoryInfo(gpu_handle)
    mem_after = info.used / 1024**3

    tokens_generated = outputs.shape[1] - inputs['input_ids'].shape[1]

    print(f"Tokens generated: {tokens_generated}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Tokens/sec: {tokens_generated/elapsed:.2f}")
    print(f"VRAM: {mem_before:.2f}GB → {mem_after:.2f}GB")
```


---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related:**
- [3401: Encoder-Decoder Architectures](../3401-Encoder-Decoder-Architectures.md)
- [3402: Decoder-Only Models](../3402-Decoder-Only-Models.md)
- [4101: GGUF Physics](../../../phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- [1402: vLLM and TGI](../../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
