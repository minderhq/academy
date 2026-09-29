---
Document ID: PROJECT-005
Title: "CAPSTONE PROJECT-005: Fine-Tune Domain Model"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
---

# CAPSTONE PROJECT-005: Fine-Tune Domain Model

**Adapt an LLM to your specific use case**

---

## 🎯 Project Overview

Fine-tune a large language model for a specific domain using modern techniques:
- LoRA and QLoRA fine-tuning
- Custom dataset preparation and cleaning
- Training with distributed GPUs
- Evaluation and benchmarking
- Production deployment

**Estimated Time:** 15-20 hours
**Difficulty:** ⭐⭐⭐ Advanced

---

## 📋 Prerequisites

Complete these before starting:
- ✅ 5101: LoRA Logic
- ✅ 5102: QLoRA Pipelines
- ✅ 5201: DPO Theory
- ✅ LAB-003: LoRA Fine-Tuning

---

## 🏗️ Project Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Fine-Tuning Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Domain Data                                                 │
│       │                                                       │
│       ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │          Data Preparation & Cleaning                   │  │
│  │  - Format conversion                                   │  │
│  │  - Quality filtering                                   │  │
│  │  - Train/val split                                     │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           Base Model Loading (4-bit)                   │  │
│  │  - Llama-2-7B / Mistral-7B                            │  │
│  │  - 4-bit quantization                                 │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              LoRA Adapter Injection                    │  │
│  │  - Target modules: q_proj, v_proj                      │  │
│  │  - Rank: 16, Alpha: 32                                 │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                 Fine-Tuning Loop                       │  │
│  │  - Gradient accumulation: 8                           │  │
│  │  - Batch size: 2 per GPU                              │  │
│  │  - Learning rate: 1e-4                                │  │
│  │  - Epochs: 3                                          │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Evaluation & Merging                      │  │
│  │  - Perplexity                                         │  │
│  │  - Domain-specific metrics                            │  │
│  │  - Adapter merging                                    │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           Production Deployment                        │  │
│  │  - vLLM / TGI                                         │  │
│  │  - API server                                         │  │
│  │  - Monitoring                                         │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Domain Data Preparation (4 hours)

### 1.1 Dataset Creation

```python
# File: prepare_dataset.py
"""
Domain Dataset Preparation
==========================
"""

import json
from pathlib import Path
import random

class DatasetPreparator:
    """Prepare domain-specific fine-tuning dataset"""

    def __init__(self, domain: str):
        self.domain = domain
        self.samples = []

    def load_from_file(self, path: str, format: str = 'jsonl'):
        """Load data from file"""
        if format == 'jsonl':
            with open(path, 'r') as f:
                for line in f:
                    self.samples.append(json.loads(line))

    def clean_data(self):
        """Clean and filter data"""
        cleaned = []

        for sample in self.samples:
            # Remove empty samples
            if not sample.get('instruction') or not sample.get('output'):
                continue

            # Filter by length
            instruction_len = len(sample['instruction'].split())
            output_len = len(sample['output'].split())

            if instruction_len < 3 or instruction_len > 512:
                continue

            if output_len < 1 or output_len > 1024:
                continue

            cleaned.append(sample)

        self.samples = cleaned
        print(f"Cleaned: {len(cleaned)} samples ({len(cleaned)/len(self.samples)*100:.1f}% kept)")

    def format_for_training(self, template: str = 'alpaca'):
        """Format samples for training"""

        formatted = []

        for sample in self.samples:
            if template == 'alpaca':
                formatted.append({
                    'text': self._format_alpaca(sample)
                })
            elif template == 'sharegpt':
                formatted.append({
                    'text': self._format_sharegpt(sample)
                })

        self.samples = formatted
        return formatted

    def _format_alpaca(self, sample: dict) -> str:
        """Format as Alpaca style"""
        instruction = sample['instruction']
        input_text = sample.get('input', '')
        output = sample['output']

        if input_text:
            prompt = f"""### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{output}"""
        else:
            prompt = f"""### Instruction:
{instruction}

### Response:
{output}"""

        return prompt

    def train_test_split(self, test_size: float = 0.1):
        """Split into train and test sets"""
        random.shuffle(self.samples)

        split_idx = int(len(self.samples) * (1 - test_size))

        train_data = self.samples[:split_idx]
        test_data = self.samples[split_idx:]

        return train_data, test_data

    def save(self, train_path: str, test_path: str):
        """Save prepared datasets"""
        train_data, test_data = self.train_test_split()

        with open(train_path, 'w') as f:
            for sample in train_data:
                f.write(json.dumps(sample) + '\n')

        with open(test_path, 'w') as f:
            for sample in test_data:
                f.write(json.dumps(sample) + '\n')

        print(f"Saved {len(train_data)} train samples to {train_path}")
        print(f"Saved {len(test_data)} test samples to {test_path}")

# Example: Create medical domain dataset
if __name__ == '__main__':
    preparator = DatasetPreparator('medical')

    # Load data (example - use actual domain data)
    # preparator.load_from_file('medical_qa.jsonl')

    # Clean
    # preparator.clean_data()

    # Format
    # preparator.format_for_training('alpaca')

    # Save
    # preparator.save('medical_train.jsonl', 'medical_test.jsonl')

    print("Dataset preparation complete!")
```

### ✅ Phase 1 Checklist
- [ ] Domain data collected
- [ ] Data cleaned and filtered
- [ ] Formatted for training
- [ ] Train/test split created

---

## Phase 2: QLoRA Fine-Tuning (6 hours)

### 2.1 Training Script

```python
# File: finetune.py
"""
QLoRA Fine-Tuning Script
========================
"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import BitsAndBytesConfig
from datasets import load_dataset

# Configuration
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
DATA_PATH = "medical_train.jsonl"
OUTPUT_DIR = "./finetuned_model"

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# Prepare for k-bit training
model = prepare_model_for_kbit_training(model)

# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

print("Applying LoRA...")
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Load dataset
print("Loading dataset...")
dataset = load_dataset('json', data_files=DATA_PATH, split='train')

# Tokenize
def tokenize_function(examples):
    return tokenizer(
        examples['text'],
        truncation=True,
        max_length=1024,
        padding="max_length"
    )

tokenized_dataset = dataset.map(tokenize_function, batched=True)
tokenized_dataset = tokenized_dataset.remove_columns(['text'])

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=8,
    learning_rate=1e-4,
    fp16=True,
    gradient_checkpointing=True,
    logging_steps=10,
    save_steps=100,
    save_total_limit=3,
    lr_scheduler_type="cosine",
    warmup_steps=100,
    weight_decay=0.01,
    evaluation_strategy="no",
    report_to=["tensorboard"],
)

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

# Train
print("Starting training...")
trainer.train()

# Save
print(f"Saving model to {OUTPUT_DIR}...")
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("Fine-tuning complete!")
```

### ✅ Phase 2 Checklist
- [ ] Base model loaded (4-bit)
- [ ] LoRA adapters applied
- [ ] Training loop working
- [ ] Checkpointing working
- [ ] Model saved

---

## Phase 3: Evaluation (3 hours)

### 3.1 Evaluation Script

```python
# File: evaluate.py
"""
Evaluate Fine-Tuned Model
=========================
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
from tqdm import tqdm
import numpy as np

MODEL_PATH = "./finetuned_model"
TEST_DATA = "medical_test.jsonl"

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

# Load test data
test_dataset = load_dataset('json', data_files=TEST_DATA, split='train')

# Generate responses
print("Generating responses...")
predictions = []
references = []

for sample in tqdm(test_dataset):
    prompt = sample['text'].split('### Response:')[0] + '### Response:'

    inputs = tokenizer(prompt, return_tensors='pt').to('cuda')

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = generated.split('### Response:')[-1].strip()

    # Get reference
    reference = sample['text'].split('### Response:')[-1].strip()

    predictions.append(response)
    references.append(reference)

# Calculate metrics
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)

rouge1_scores = []
rouge2_scores = []
rougeL_scores = []

for pred, ref in zip(predictions, references):
    scores = scorer.score(ref, pred)
    rouge1_scores.append(scores['rouge1'].fmeasure)
    rouge2_scores.append(scores['rouge2'].fmeasure)
    rougeL_scores.append(scores['rougeL'].fmeasure)

print(f"\nROUGE-1: {np.mean(rouge1_scores):.4f}")
print(f"ROUGE-2: {np.mean(rouge2_scores):.4f}")
print(f"ROUGE-L: {np.mean(rougeL_scores):.4f}")

# Example outputs
print("\n=== Example Outputs ===")
for i in range(3):
    print(f"\nPrompt: {test_dataset[i]['text'].split('### Response:')[0]}")
    print(f"Generated: {predictions[i]}")
    print(f"Reference: {references[i]}")
```

### ✅ Phase 3 Checklist
- [ ] ROUGE scores calculated
- [ ] Example outputs reviewed
- [ ] Quality acceptable
- [ ] Comparison with baseline

---

## Phase 4: Deployment (2 hours)

### 4.1 Deploy with vLLM

```bash
# File: deploy.sh
#!/bin/bash

# Deploy fine-tuned model with vLLM

MODEL_PATH="./finetuned_model"

# Merge adapters
python merge_adapters.py \
    --base_model mistralai/Mistral-7B-Instruct-v0.2 \
    --adapter_path $MODEL_PATH \
    --output_path ./merged_model

# Deploy with vLLM
python -m vllm.entrypoints.api_server \
    --model ./merged_model \
    --host 0.0.0.0 \
    --port 8000 \
    --quantization awq \
    --max-model-len 4096 \
    --tensor-parallel-size 1

echo "Model deployed at http://localhost:8000"
```

### ✅ Phase 4 Checklist
- [ ] Adapters merged
- [ ] Model deployed with vLLM
- [ ] API endpoint accessible
- [ ] Production ready

---

## 🏆 Project Completion Checklist

```text
[ ] Phase 1: Domain Data Prepared
[ ] Phase 2: QLoRA Fine-Tuning
[ ] Phase 3: Evaluation
[ ] Phase 4: Production Deployment
[ ] Model performance verified
[ ] API deployed and accessible
```

---

## 📚 Related Resources

- **[5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)** - LoRA theory
- **[5102: QLoRA Pipelines](../../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)** - QLoRA techniques
- **[LAB-003: LoRA Fine-Tuning](../labs/LAB-003-LoRA-FineTuning.md)** - Hands-on fine-tuning

---

**Congratulations!** You've fine-tuned a domain-specific LLM:
- 📊 Domain dataset prepared
- 🎯 QLoRA fine-tuning completed
- 📈 Performance evaluated
- 🚀 Production deployment

## Next Steps

- **[Volume 6: Data Nexus](../../volumes/VOLUME-6-Data-Nexus.md)**
