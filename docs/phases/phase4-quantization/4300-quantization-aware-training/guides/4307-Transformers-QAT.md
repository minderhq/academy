# 4307: Transformers QAT Guide

## Abstract

HuggingFace Transformers provides built-in support for QAT through the `bitsandbytes` and `optimum` libraries. This guide shows how to quantize transformer models effectively.

## HuggingFace QAT Tools

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
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "meta-llama/Llama-2-7b-hf"

# Load with 4-bit quantization
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_4bit=True,
    device_map="auto",
    bnb_4bit_quant_type="nf4",  # NormalFloat 4
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
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
pip install auto-gptq
pip install optimum
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
    model_name_base="llama-2-7b-gptq",
)

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
model = quant.prepare_qat(model)

# Training arguments
training_args = TrainingArguments(
    output_dir="./bert-qat",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    learning_rate=2e-5,
    evaluation_strategy="epoch",
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
from transformers import BertPreTrainedModel, BertModel
import torch.ao.quantization as quant

class QuantizedBertForSequenceClassification(BertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.bert = BertModel(config)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)

        # Add quantization
        self.quant = torch.ao.quantization.QuantStub()
        self.dequant = torch.ao.quantization.DeQuantStub()

    def forward(self, input_ids, attention_mask=None, labels=None):
        # Quantize input
        input_ids = self.quant(input_ids.float())

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
model = quant.prepare_qat(model)
```

## Evaluation

### Accuracy Comparison

```python
from datasets import load_metric

metric = load_metric("accuracy")

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
# Use higher bit-width for sensitive layers
sensitive_layers = ['embeddings', 'encoder.layer.0']
for name in sensitive_layers:
    set_bit_width(model, name, bit_width=8)
```

## Further Reading

- **Library:** HuggingFace PEFT documentation
- **Library:** bitsandbytes GitHub
- **Paper:** "QLoRA: Efficient Finetuning of Quantized LLMs"
- **Paper:** "GPTQ: Accurate Post-Training Quantization"

## Next Steps

→ **[guides/4308: BitBlade QAT](4308-BitBlade-QAT.md)** - Advanced quantization techniques

---

**Last Updated:** 2026-02-04
