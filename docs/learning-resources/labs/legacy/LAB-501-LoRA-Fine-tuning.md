# LAB-501: LoRA Fine-tuning

## Overview
Fine-tune a language model using LoRA (Low-Rank Adaptation).

## Prerequisites
- LAB-201 completed
- Understanding of fine-tuning basics
- GPU with 12GB+ VRAM recommended

## Setup

```bash
pip install torch transformers peft datasets bitsandbytes
```

## Exercise 1: Load Model with LoRA

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

# Model (use smaller for testing)
model_name = "gpt2"  # or "meta-llama/Llama-2-7b-hf" for full model

# TODO: Load in 4-bit for memory efficiency
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# TODO: Configure LoRA
lora_config = LoraConfig(
    r=8,  # Rank
    lora_alpha=32,
    target_modules=["c_attn"],  # For GPT-2
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# TODO: Apply LoRA to model
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
```

## Exercise 2: Prepare Dataset

```python
# TODO: Load or create dataset
# Option 1: Use existing dataset
dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train")

# Option 2: Create custom dataset
from datasets import Dataset

train_data = {
    "text": [
        "The capital of France is Paris.",
        "Python is a programming language.",
        "Machine learning is a subset of AI.",
        # ... add more examples
    ] * 100  # Repeat for more data
}

dataset = Dataset.from_dict(train_data)

# TODO: Tokenize dataset
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=128,
        padding="max_length"
   )

tokenized_dataset = dataset.map(tokenize_function, batched=True)
```

## Exercise 3: Training Loop

```python
# TODO: Set training arguments
training_args = TrainingArguments(
    output_dir="./lora-output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_steps=100,
)

# TODO: Create trainer
def compute_metrics(eval_pred):
    # Add custom metrics if needed
    return {}

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    # eval_dataset=tokenized_dataset,  # Add if you have validation
    compute_metrics=compute_metrics,
)

# TODO: Train
print("Starting training...")
trainer.train()
```

## Exercise 4: Generate with Fine-tuned Model

```python
# TODO: Generate text
prompt = "The capital of"

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.7,
        top_p=0.9,
        do_sample=True
    )

generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"\nGenerated:\n{generated_text}")
```

## Exercise 5: Save and Load LoRA Adapter

```python
# TODO: Save LoRA adapter
model.save_pretrained("./lora-gpt2-adapter")
tokenizer.save_pretrained("./lora-gpt2-adapter")

# TODO: Load LoRA adapter for inference
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)

model = PeftModel.from_pretrained(base_model, "./lora-gpt2-adapter")

# Test loaded model
inputs = tokenizer("The capital of", return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=30)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Exercise 6: Compare Base vs Fine-tuned

```python
# TODO: Compare outputs
test_prompts = [
    "The capital of France is",
    "Python is a",
    "Machine learning is",
]

for prompt in test_prompts:
    # Base model
    base_outputs = base_model.generate(
        **tokenizer(prompt, return_tensors="pt").to(base_model.device),
        max_new_tokens=30
    )
    base_text = tokenizer.decode(base_outputs[0], skip_special_tokens=True)

    # Fine-tuned model
    ft_outputs = model.generate(
        **tokenizer(prompt, return_tensors="pt").to(model.device),
        max_new_tokens=30
    )
    ft_text = tokenizer.decode(ft_outputs[0], skip_special_tokens=True)

    print(f"\nPrompt: {prompt}")
    print(f"Base:     {base_text[:80]}...")
    print(f"Fine-tuned: {ft_text[:80]}...")
```

## Expected Outputs

1. Exercise 1: Trainable parameters <1% of total
2. Exercise 2: Dataset tokenized
3. Exercise 3: Training completes without errors
4. Exercise 4: Generated text reflects training data
5. Exercise 5: Adapter saved and loaded successfully
6. Exercise 6: Fine-tuned model shows training data influence

## Troubleshooting

**Issue:** Out of memory
```python
# Solution: Reduce batch size or gradient accumulation
training_args.per_device_train_batch_size = 2
training_args.gradient_accumulation_steps = 8
```

**Issue:** Training too slow
```python
# Solution: Use fewer epochs or smaller dataset
training_args.num_train_epochs = 1
```

**Issue:** Poor generation quality
```python
# Solution: Increase rank or training data
lora_config.r = 16
```

## Extensions

1. Try different target modules
2. Experiment with different ranks (r)
3. Use QLoRA (4-bit base + LoRA)
4. Fine-tune on domain-specific data

## Time Estimate: 5-6 hours

---

**Last Updated:** 2026-02-04
