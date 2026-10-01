---
Document ID: 4307
Title: "4307: Transformers QAT Guide"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 2 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'qat', 'quantization-aware-training']
---

# 4307: Transformers QAT Guide

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Hugging Face QAT Tools](#hugging-face-qat-tools)
- [Method 1: bitsandbytes NF4 Quantization](#method-1-bitsandbytes-nf4-quantization)
- [Method 2: AutoGPTQ](#method-2-autogptq)
- [Method 3: Optimum for ONNX Quantization](#method-3-optimum-for-onnx-quantization)
- [Method 4: Training with Quantization Aware Training](#method-4-training-with-quantization-aware-training)
- [Advanced: Custom QAT for Transformers](#advanced-custom-qat-for-transformers)
- [Evaluation](#evaluation)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Summary](#summary)
- [Further Reading](#further-reading)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Map the four Hugging Face QAT tools — bitsandbytes for NF4/INT8 loading, optimum for ONNX/Habana export, auto-gptq for GPTQ, and native torch.ao QAT carried through the Trainer
- Load a 4-bit Llama with BitsAndBytesConfig — nf4 quant type, float16 compute dtype, double quant — and read the footprint from get_memory_footprint()
- Quantize a causal LM with AutoGPTQ — BaseQuantizeConfig (bits=4, group_size=128, damp_percent=0.01), 128 calibration examples through model.quantize(), save_quantized/reload via from_quantized()
- Export gpt2 to ONNX with ORTModelForCausalLM(export=True) and shrink it via ORTQuantizer + AutoQuantizationConfig.arm64(is_static=False) dynamic quantization
- Wire BERT for QAT in the Trainer — get_default_qat_qconfig('x86'), prepare_qat before training, convert(model.eval()) to a true INT8 model afterward
- Evaluate a stub-placed BertPreTrainedModel subclass — accuracy delta and ms-per-forward speedup from a 100-iteration warmed benchmark

---

## Abstract

Hugging Face Transformers provides built-in support for QAT through the `bitsandbytes` and `optimum` libraries. This guide shows how to quantize transformer models effectively.

## Hugging Face QAT Tools

```text
Transformers QAT Ecosystem
├── bitsandbytes      # NF4, INT8 quantization
├── optimum           # ONNX, Habana quantization
├── auto-gptq         # GPTQ quantization
└── transformers      # Native QAT support
```

## Method 1: bitsandbytes NF4 Quantization

### Loading a Quantized Model

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

model_name = "meta-llama/Llama-2-7b-hf"

# Canonical 4-bit loading: pass quantization_config (the bare bnb_4bit_*
# from_pretrained kwargs are legacy shortcuts)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",  # NormalFloat 4
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
)

tokenizer = AutoTokenizer.from_pretrained(model_name)

# Model is now 4-bit quantized
print(f"Model dtype: {model.dtype}")
print(f"Memory: {model.get_memory_footprint() / 1e9:.2f} GB")
```

### Fine-tuning a Quantized Model (QLoRA)

```python
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Prepare model for training
model = prepare_model_for_kbit_training(model)

# Configure LoRA
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Train
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./qlora-output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
)

trainer.train()
```

## Method 2: AutoGPTQ

### Installation

```bash
uv pip install auto-gptq
uv pip install optimum
```

### Quantizing with AutoGPTQ

```python
from transformers import AutoTokenizer
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

model_name = "meta-llama/Llama-2-7b-hf"

# Quantization configuration
quantize_config = BaseQuantizeConfig(
    bits=4,  # 4-bit
    group_size=128,  # Group size for quantization
    damp_percent=0.01,
    desc_act=False,
    sym=True,
    true_sequential=True,
)
# Model naming happens at save_quantized below, not in the config

# Load model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoGPTQForCausalLM.from_pretrained(
    model_name,
    quantize_config=quantize_config,
    trust_remote_code=True,
)

# Calibrate with example data
example_data = [
    tokenizer("Example text for calibration", return_tensors="pt")["input_ids"]
    for _ in range(128)
]

model.quantize(
    example_data,
    batch_size=1,
)

# Save quantized model
save_dir = "./llama-2-7b-gptq"
model.save_quantized(save_dir)
tokenizer.save_pretrained(save_dir)
```

### Loading GPTQ Model

```python
from auto_gptq import AutoGPTQForCausalLM

model = AutoGPTQForCausalLM.from_quantized(
    "./llama-2-7b-gptq",
    device_map="auto",
    use_safetensors=True,
)
```

## Method 3: Optimum for ONNX Quantization

### Export and Quantize to ONNX

```python
from optimum.onnxruntime import ORTModelForCausalLM
from transformers import AutoTokenizer

model_name = "gpt2"

# Export to ONNX
model = ORTModelForCausalLM.from_pretrained(
    model_name,
    export=True,
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Save ONNX model
model.save_pretrained("./gpt2-onnx")
tokenizer.save_pretrained("./gpt2-onnx")
```

### Quantize ONNX Model

```python
from optimum.onnxruntime import ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig

# Load ONNX model
quantizer = ORTQuantizer.from_pretrained("./gpt2-onnx")

# Quantization config
qconfig = AutoQuantizationConfig.arm64(
    is_static=False,  # Dynamic quantization
    per_channel=False,
)

# Quantize
quantizer.quantize(
    save_dir="./gpt2-quantized",
    quantization_config=qconfig,
)

# Load quantized model
model = ORTModelForCausalLM.from_pretrained("./gpt2-quantized")
```

## Method 4: Training with Quantization Aware Training

```python
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments
from torch.ao.quantization import prepare_qat, convert

model_name = "bert-base-uncased"

# Load model
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# Prepare for QAT
import torch.ao.quantization as quant
model.qconfig = quant.get_default_qat_qconfig('x86')
model.train()  # prepare_qat requires training mode - from_pretrained loads in eval mode
model = quant.prepare_qat(model)

# Training arguments
training_args = TrainingArguments(
    output_dir="./bert-qat",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    learning_rate=2e-5,
    eval_strategy="epoch",  # renamed from evaluation_strategy (transformers 4.41+)
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

trainer.train()

# Convert to INT8
model_int8 = quant.convert(model.eval())
```

## Advanced: Custom QAT for Transformers

```python
import torch.nn as nn
from transformers import BertPreTrainedModel, BertModel
import torch.ao.quantization as quant

class QuantizedBertForSequenceClassification(BertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.bert = BertModel(config)
        self.num_labels = config.num_labels  # forward's loss needs it
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)

        # Add quantization
        self.quant = torch.ao.quantization.QuantStub()
        self.dequant = torch.ao.quantization.DeQuantStub()
        self.post_init()  # HF custom models must finish __init__ with post_init()

    def forward(self, input_ids, attention_mask=None, labels=None):
        # Caveat: token ids must reach the embedding as Long — quantizing
        # them to float breaks word_embeddings. Real QAT moves QuantStub
        # to the embedding output (module surgery); these stubs mark the
        # boundary prepare_qat wires up.
        input_ids = self.quant(input_ids.float()).long()

        # BERT model
        outputs = self.bert(input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output

        # Classifier
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)

        # Dequantize output
        logits = self.dequant(logits)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

        return {"loss": loss, "logits": logits}

# Usage
model = QuantizedBertForSequenceClassification.from_pretrained("bert-base-uncased")
model.qconfig = quant.get_default_qat_qconfig('x86')
model.train()  # prepare_qat requires training mode
model = quant.prepare_qat(model)
```

## Evaluation

### Accuracy Comparison

```python
# datasets.load_metric was removed — accuracy lives in the evaluate library
import evaluate

metric = evaluate.load("accuracy")

def evaluate(model, dataloader):
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in dataloader:
            outputs = model(**batch)
            preds = outputs.logits.argmax(dim=-1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch["labels"].cpu().numpy())

    return metric.compute(predictions=all_preds, references=all_labels)

# Compare
acc_fp32 = evaluate(model_fp32, test_dataloader)
acc_int8 = evaluate(model_int8, test_dataloader)

print(f"FP32 Accuracy: {acc_fp32['accuracy']:.4f}")
print(f"INT8 Accuracy: {acc_int8['accuracy']:.4f}")
print(f"Loss: {acc_fp32['accuracy'] - acc_int8['accuracy']:.4f}")
```

### Inference Speed Benchmark

```python
import time

def benchmark_inference(model, inputs, num_iterations=100):
    model.eval()

    # Warmup
    for _ in range(10):
        _ = model(**inputs)

    # Time inference
    start = time.time()
    for _ in range(num_iterations):
        _ = model(**inputs)
    end = time.time()

    avg_time = (end - start) / num_iterations * 1000  # ms
    return avg_time

# Compare
time_fp32 = benchmark_inference(model_fp32, inputs)
time_int8 = benchmark_inference(model_int8, inputs)

print(f"FP32: {time_fp32:.2f} ms")
print(f"INT8: {time_int8:.2f} ms")
print(f"Speedup: {time_fp32 / time_int8:.2f}x")
```

## Best Practices

1. **Start with pretrained models:** QAT works best when fine-tuning existing models
2. **Use gradual QAT:** Train in FP32 first, then enable QAT
3. **Validate extensively:** Test on diverse data after quantization
4. **Consider layer-wise bits:** Attention layers often need higher precision than MLP
5. **Profile memory:** Ensure quantization actually reduces memory usage

## Troubleshooting

### Issue: NaN Loss

```python
# Reduce learning rate when enabling QAT
if epoch >= qat_start_epoch:
    for param_group in optimizer.param_groups:
        param_group['lr'] *= 0.1
```

### Issue: Out of Memory

```python
# Use gradient checkpointing
model.gradient_checkpointing_enable()

# Reduce batch size
training_args.per_device_train_batch_size = 4
training_args.gradient_accumulation_steps = 8
```

### Issue: Accuracy Drop

```python
from torch.ao.quantization import FakeQuantize
# Use higher bit-width for sensitive layers
def set_prefix_bit_width(model, prefix, bit_width=8):
    # FakeQuantize is defined in 4302-Fake-Quantization.md
    for module_name, module in model.named_modules():
        if module_name.startswith(prefix) and isinstance(module, FakeQuantize):
            module.bit_width = bit_width

for prefix in ['embeddings', 'encoder.layer.0']:
    set_prefix_bit_width(model, prefix)
```

## Summary

Hugging Face puts four paths to quantized transformers on the table: bitsandbytes NF4 for instant low-memory loading, AutoGPTQ for optimized 4-bit inference, Optimum for ONNX-quantized export, and true QAT training when the post-training routes cost too much accuracy. The evaluation section is the discipline that ties them together: benchmark each method on your model and workload before committing - the right answer is workload-dependent, and this guide's decision points show where each method wins.

## Further Reading

- **Library:** Hugging Face PEFT documentation
- **Library:** bitsandbytes GitHub
- **Paper:** "QLoRA: Efficient Finetuning of Quantized LLMs"
- **Paper:** "GPTQ: Accurate Post-Training Quantization"

## References

### Related PROJECT-OMEGA Documents

- [4306: PyTorch QAT Guide](4306-PyTorch-QAT.md)
- [4308: BitBlade QAT Guide](4308-BitBlade-QAT.md)

---

## Next Steps

→ **[guides/4308: BitBlade QAT](4308-BitBlade-QAT.md)** - Advanced quantization techniques
