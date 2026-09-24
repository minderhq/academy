# EXP_3401: Encoder-Decoder Architecture Experiments

## Overview
Practical experiments for testing encoder-decoder models (T5, BART) on PROJECT-OMEGA infrastructure.

## Experiment 1: T5 Model Benchmarking

### Objective
Compare T5 model variants on seq2seq tasks with RTX 2080 Ti (11GB VRAM).

### Setup
```bash
# Install dependencies
pip install transformers datasets torch sentencepiece

# Create experiment directory
mkdir -p /workspace/exp_3401_t5
cd /workspace/exp_3401_t5
```

### Test Script
```python
# t5_benchmark.py
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from time import time
import psutil

# Models to test
models = [
    "t5-small",      # 60M params, ~230MB
    "t5-base",       # 220M params, ~890MB
    "t5-large",      # 770M params, ~3GB
]

def benchmark_t5(model_name, batch_size=4):
    """Benchmark T5 model inference speed"""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")

    # Load model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)

    # Test inputs
    inputs = [
        "translate English to German: The house is wonderful.",
        "summarize: The tower is 324 metres (1,063 ft) tall, about the same height as an 81-storey building.",
        "classify: This movie was absolutely fantastic!",
    ] * batch_size

    # Tokenize
    encoded = tokenizer(inputs, padding=True, return_tensors="pt").to(device)

    # Warmup
    for _ in range(3):
        _ = model.generate(**encoded, max_length=50)

    # Benchmark
    torch.cuda.synchronize()
    start = time()

    for _ in range(10):
        outputs = model.generate(**encoded, max_length=50)

    torch.cuda.synchronize()
    elapsed = time() - start

    # Metrics
    samples_per_sec = (len(inputs) * 10) / elapsed
    vram_used = torch.cuda.max_memory_allocated() / 1024**3
    ram_used = psutil.virtual_memory().used / 1024**3

    print(f"Throughput: {samples_per_sec:.2f} samples/sec")
    print(f"VRAM Peak:  {vram_used:.2f} GB / 11 GB")
    print(f"RAM Used:   {ram_used:.2f} GB")
    print(f"Latency:    {elapsed/10:.3f} sec/batch")

    # Clean up
    del model
    torch.cuda.empty_cache()

    return {
        "model": model_name,
        "samples_per_sec": samples_per_sec,
        "vram_gb": vram_used,
        "ram_gb": ram_used,
    }

# Run benchmarks
results = []
for model in models:
    try:
        result = benchmark_t5(model)
        results.append(result)
    except RuntimeError as e:
        if "out of memory" in str(e):
            print(f"OOM: {model} - reducing batch size")
            result = benchmark_t5(model, batch_size=2)
            results.append(result)

# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
for r in results:
    print(f"{r['model']:15} | {r['samples_per_sec']:6.2f} samples/s | {r['vram_gb']:5.2f} GB VRAM")
```

### Expected Results
| Model | Params | VRAM | Throughput | Best Batch |
|-------|--------|------|------------|------------|
| t5-small | 60M | ~1GB | ~25 samples/s | 8-16 |
| t5-base | 220M | ~2.5GB | ~12 samples/s | 4-8 |
| t5-large | 770M | ~6GB | ~4 samples/s | 2-4 |

---

## Experiment 2: BART Summarization Quality

### Objective
Test BART model summarization quality on different document lengths.

### Setup
```python
# bart_summarization_test.py
from transformers import BartForConditionalGeneration, BartTokenizer
import torch

def test_bart_summarization():
    """Test BART on various document lengths"""
    model_name = "facebook/bart-large-cnn"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = BartTokenizer.from_pretrained(model_name)
    model = BartForConditionalGeneration.from_pretrained(model_name).to(device)

    # Test documents of varying lengths
    test_docs = [
        ("Short", "AI is transforming healthcare. Doctors use machine learning to diagnose diseases more accurately and quickly."),
        ("Medium", "Artificial intelligence has revolutionized multiple industries in recent years. In healthcare, AI algorithms help radiologists detect tumors earlier than traditional methods. Finance companies use AI for fraud detection and algorithmic trading. Autonomous vehicles are becoming a reality, with companies like Tesla and Waymo testing self-driving cars on public roads."),
        ("Long", """[Paste 1000+ word document here]"""),
    ]

    for name, text in test_docs:
        inputs = tokenizer([text], max_length=1024, return_tensors="pt").to(device)

        # Generate summary
        summary_ids = model.generate(
            inputs["input_ids"],
            num_beams=4,
            max_length=200,
            early_stopping=True
        )

        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        print(f"\n{'='*60}")
        print(f"{name} Document ({len(text)} chars)")
        print(f"{'='*60}")
        print(f"Summary: {summary}")
        print(f"Compression: {len(summary) / len(text) * 100:.1f}%")
```

---

## Experiment 3: Encoder-Decoder Fine-tuning

### Objective
Fine-tune T5-small on a custom dataset using QLoRA for memory efficiency.

### Setup
```bash
pip install peft datasets bitsandbytes
```

### Fine-tuning Script
```python
# finetune_t5_qlora.py
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from datasets import load_dataset
import torch

# Load model (4-bit quantization)
model_name = "google-t5/t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load dataset (example: CNN/DailyMail for summarization)
dataset = load_dataset("cnn_dailymail", "3.0.0")

# Preprocess
def preprocess_function(examples):
    inputs = ["summarize: " + doc for doc in examples["article"]]
    model_inputs = tokenizer(inputs, max_length=512, truncation=True)

    labels = tokenizer(
        examples["highlights"],
        max_length=128,
        truncation=True
    )

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_datasets = dataset.map(
    preprocess_function,
    batched=True,
    remove_columns=dataset["train"].column_names
)

# LoRA configuration for seq2seq
lora_config = LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q", "k", "v", "o"],
)

# Load model with 4-bit
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)

# Prepare for k-bit training
model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Training
training_args = TrainingArguments(
    output_dir="./t5-qlora-checkpoint",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=1e-4,
    num_train_epochs=3,
    logging_steps=10,
    save_steps=100,
    fp16=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"].shuffle().select(range(1000)),
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model),
)

trainer.train()

# Save adapter
model.save_pretrained("./t5-qlora-adapters")
```

---

## Experiment 4: Cross-Attention Visualization

### Objective
Visualize cross-attention patterns in encoder-decoder models.

### Script
```python
# visualize_cross_attention.py
import torch
from transformers import BartForConditionalGeneration, BartTokenizer
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_cross_attention():
    """Visualize encoder-decoder attention"""
    model_name = "facebook/bart-base"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = BartForConditionalGeneration.from_pretrained(model_name).to(device)
    tokenizer = BartTokenizer.from_pretrained(model_name)

    # Input text
    text = "The quick brown fox jumps over the lazy dog."

    inputs = tokenizer(text, return_tensors="pt").to(device)

    # Generate with attention outputs
    with torch.no_grad():
        outputs = model(
            input_ids=inputs["input_ids"],
            decoder_input_ids=inputs["input_ids"],
            output_attentions=True,
            output_hidden_states=True
        )

    # Get cross-attention (encoder-decoder)
    # Shape: (batch, heads, decoder_seq, encoder_seq)
    cross_attention = outputs.cross_attentions[0][0]  # First layer, first batch

    # Average across heads
    avg_attention = cross_attention.mean(dim=0).cpu().numpy()

    # Plot
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

    plt.figure(figsize=(12, 8))
    sns.heatmap(
        avg_attention,
        xticklabels=tokens,
        yticklabels=tokens,
        cmap="viridis",
        cbar_kws={"label": "Attention Weight"}
    )
    plt.title("Encoder-Decoder Cross-Attention")
    plt.xlabel("Encoder Tokens")
    plt.ylabel("Decoder Tokens")
    plt.tight_layout()
    plt.savefig("/workspace/exp_3401_t5/cross_attention.png", dpi=150)

if __name__ == "__main__":
    visualize_cross_attention()
```

---

## Experiment Checklist

- [ ] T5-small inference baseline (verify < 1GB VRAM)
- [ ] T5-base inference baseline (verify < 3GB VRAM)
- [ ] T5-large inference baseline (verify < 7GB VRAM)
- [ ] BART summarization quality test (short/medium/long docs)
- [ ] T5 QLoRA fine-tuning (verify < 6GB VRAM during training)
- [ ] Cross-attention visualization
- [ ] Encoder-decoder vs decoder-only comparison
- [ ] Beam search vs sampling quality comparison

---

## Related Documentation
- [3401: Encoder-Decoder Architectures](../docs/3000-Transformer-Physics/3400-Model-Architectures/3401-Encoder-Decoder-Architectures.md)
- [3402: Decoder-Only Models](../docs/3000-Transformer-Physics/3400-Model-Architectures/3402-Decoder-Only-Models.md)
- [5102: QLoRA Pipelines](../docs/5000-Fine-Tuning/5100-Parameter-Efficient/5102-QLoRA-Pipelines.md)
