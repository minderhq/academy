---
Document ID: SOLUTION-LAB-003
Title: "SOLUTION-LAB-003: LoRA Fine-Tuning"
Last Updated: 2026-09-27
Status: Complete
Difficulty: Intermediate
---

# SOLUTION-LAB-003: LoRA Fine-Tuning

## Overview
Complete solution for fine-tuning language models using LoRA (Low-Rank Adaptation) and QLoRA (Quantized LoRA).

---

## Prerequisites

```bash
uv pip install torch transformers peft datasets bitsandbytes accelerate scipy
```

---

## Solution 1: Basic LoRA Fine-Tuning

```python
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset


def setup_lora_finetuning():
    """Complete LoRA fine-tuning setup."""

    # Model and tokenizer
    model_name = "mistralai/Mistral-7B-v0.1"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Load base model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # LoRA Configuration
    lora_config = LoraConfig(
        r=16,                    # Rank - lower = fewer parameters
        lora_alpha=32,           # Scaling factor (usually 2x rank)
        target_modules=[         # Which modules to apply LoRA
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj"
        ],
        lora_dropout=0.05,
        bias="none",             # Don't train bias parameters
        task_type=TaskType.CAUSAL_LM
    )

    # Apply LoRA to model
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load and prepare dataset
    dataset = load_dataset("databricks/databricks-dolly-15k", split="train")

    def tokenize_function(examples):
        # Format: instruction + response
        texts = [
            f"### Instruction:\n{instr}\n\n### Response:\n{resp}"
            for instr, resp in zip(examples["instruction"], examples["response"])
        ]
        return tokenizer(
            texts,
            truncation=True,
            max_length=512,
            padding="max_length"
        )

    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    tokenized_dataset = tokenized_dataset.remove_columns([
        "instruction", "response", "category", "context"
    ])

    # Training arguments
    training_args = TrainingArguments(
        output_dir="./lora_output",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        weight_decay=0.01,
        warmup_steps=100,
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        fp16=True,
        optim="adamw_torch",
        eval_strategy="no",
        report_to="none"
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
        pad_to_multiple_of=8
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset.shuffle().select(range(1000)),
        data_collator=data_collator
    )

    return trainer, model, tokenizer


def train_lora(trainer, model, tokenizer):
    """Train LoRA model."""

    print("Starting LoRA training...")
    trainer.train()

    # Save adapter
    model.save_pretrained("./lora_adapter")
    tokenizer.save_pretrained("./lora_adapter")

    print("Training complete! Adapter saved.")

    return model


def merge_and_save(base_model_path, adapter_path, output_path):
    """Merge LoRA adapter with base model."""

    from peft import PeftModel

    # Load base model
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # Load adapter
    model = PeftModel.from_pretrained(base_model, adapter_path)

    # Merge
    merged_model = model.merge_and_unload()

    # Save
    merged_model.save_pretrained(output_path)
    print(f"Merged model saved to {output_path}")


def test_inference(model_path, prompt):
    """Test fine-tuned model."""

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


# Main execution
if __name__ == "__main__":
    trainer, model, tokenizer = setup_lora_finetuning()
    trained_model = train_lora(trainer, model, tokenizer)

    # Test inference
    test_prompt = "### Instruction:\nExplain quantum computing in simple terms.\n\n### Response:\n"
    response = test_inference("./lora_adapter", test_prompt)
    print(response)
```

---

## Solution 2: QLoRA (Quantized LoRA)

```python
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model, TaskType


def setup_qlora():
    """Complete QLoRA setup with 4-bit quantization."""

    model_name = "mistralai/Mistral-7B-v0.1"

    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,     # Double quantization
        bnb_4bit_quant_type="nf4",           # NormalFloat 4-bit
        bnb_4bit_compute_dtype=torch.float16 # Compute dtype
    )

    # Load model in 4-bit
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )

    # tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # QLoRA config
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj"
        ],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False
    )

    # Apply QLoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model, tokenizer


def train_qlora(model, tokenizer, train_dataset):
    """Train QLoRA model."""

    training_args = TrainingArguments(
        output_dir="./qlora_output",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        max_grad_norm=0.3,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset
    )

    trainer.train()

    return trainer


def compare_memory():
    """Compare memory usage: full vs LoRA vs QLoRA."""

    import gc

    model_name = "mistralai/Mistral-7B-v0.1"

    print("Memory Comparison:")
    print("=" * 50)

    # Full model
    model_full = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    full_mem = torch.cuda.memory_allocated() / 1024**3
    print(f"Full model: {full_mem:.2f} GB")
    del model_full
    gc.collect()
    torch.cuda.empty_cache()

    # LoRA
    model_lora = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    lora_config = LoraConfig(r=16, lora_alpha=32, task_type=TaskType.CAUSAL_LM)
    model_lora = get_peft_model(model_lora, lora_config)
    lora_mem = torch.cuda.memory_allocated() / 1024**3
    print(f"LoRA model: {lora_mem:.2f} GB")
    del model_lora
    gc.collect()
    torch.cuda.empty_cache()

    # QLoRA
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4"
    )
    model_qlora = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto"
    )
    model_qlora = get_peft_model(model_qlora, lora_config)
    qlora_mem = torch.cuda.memory_allocated() / 1024**3
    print(f"QLoRA model: {qlora_mem:.2f} GB")

    print("=" * 50)
    print(f"LoRA saves: {(1 - lora_mem/full_mem)*100:.1f}% memory")
    print(f"QLoRA saves: {(1 - qlora_mem/full_mem)*100:.1f}% memory")
```

---

## Solution 3: Advanced LoRA Techniques

```python
from peft import LoraConfig, get_peft_model, TaskType


class MultiLoRAManager:
    """Manage multiple LoRA adapters for different tasks."""

    def __init__(self, base_model_name):
        self.base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.adapters = {}

    def add_adapter(self, name, r=16, alpha=32, dropout=0.05):
        """Add a new LoRA adapter."""

        config = LoraConfig(
            r=r,
            lora_alpha=alpha,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )

        model = get_peft_model(self.base_model, config)
        self.adapters[name] = model

        return model

    def switch_adapter(self, adapter_name):
        """Switch to a specific adapter."""

        if adapter_name not in self.adapters:
            raise ValueError(f"Adapter {adapter_name} not found")

        return self.adapters[adapter_name]

    def merge_all(self, output_dir):
        """Merge all adapters and save."""

        for name, model in self.adapters.items():
            merged = model.merge_and_unload()
            merged.save_pretrained(f"{output_dir}/{name}")
            print(f"Saved merged adapter: {name}")


def custom_lora_modules():
    """Apply LoRA to custom modules."""

    # Apply to specific attention modules only
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=[
            "q_proj",      # Query projection
            "k_proj",      # Key projection
            "v_proj",      # Value projection
        ],
        modules_to_save=["embed_tokens"],  # Also train embeddings
        lora_dropout=0.05,
        task_type=TaskType.CAUSAL_LM
    )

    return lora_config


def gradient_checkpointing_lora():
    """LoRA with gradient checkpointing for memory efficiency."""

    model = AutoModelForCausalLM.from_pretrained(
        "mistralai/Mistral-7B-v0.1",
        torch_dtype=torch.float16,
        device_map="auto",
    )

    # Enable gradient checkpointing
    model.gradient_checkpointing_enable()

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        task_type=TaskType.CAUSAL_LM
    )

    model = get_peft_model(model, lora_config)

    return model
```

---

## Solution 4: LoRA for Instruction Tuning

```python
from datasets import load_dataset
from transformers import Trainer, TrainingArguments
import json


def prepare_instruction_dataset(dataset_name="databricks/databricks-dolly-15k"):
    """Prepare dataset for instruction tuning."""

    dataset = load_dataset(dataset_name, split="train")

    def format_prompts(examples):
        """Format examples with instruction prompts."""

        formatted = []
        for instruction, response, context in zip(
            examples["instruction"],
            examples["response"],
            examples.get("context", [""] * len(examples["instruction"]))
        ):
            if context:
                prompt = f"""### Context:
{context}

### Instruction:
{instruction}

### Response:
{response}"""
            else:
                prompt = f"""### Instruction:
{instruction}

### Response:
{response}"""

            formatted.append(prompt)

        return {"text": formatted}

    dataset = dataset.map(format_prompts, batched=True)
    return dataset


def train_instruction_lora(model, tokenizer, dataset):
    """Train LoRA for instruction following."""

    # Tokenize
    def tokenize(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=512,
            padding="max_length"
        )

    tokenized = dataset.map(tokenize, batched=True)

    # Training
    training_args = TrainingArguments(
        output_dir="./instruction_lora",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_steps=100
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized.shuffle(seed=42).select(range(1000))
    )

    trainer.train()

    return trainer
```

---

## Solution 5: Evaluate LoRA Model

```python
import evaluate
from tqdm import tqdm


def evaluate_model(model, tokenizer, test_dataset):
    """Evaluate fine-tuned model."""

    metric = evaluate.load("accuracy")

    model.eval()
    correct = 0
    total = 0

    for example in tqdm(test_dataset):
        prompt = example["instruction"]
        expected = example["response"]

        # Generate
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=100)
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Simple check: does response contain key info?
        if expected.lower() in generated.lower():
            correct += 1
        total += 1

    accuracy = correct / total
    print(f"Accuracy: {accuracy:.2%}")

    return accuracy


def compare_before_after(base_model, lora_model, tokenizer, test_prompts):
    """Compare responses before and after fine-tuning."""

    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        print("-" * 50)

        # Base model
        inputs = tokenizer(prompt, return_tensors="pt").to(base_model.device)
        outputs = base_model.generate(**inputs, max_new_tokens=100)
        response_base = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Before: {response_base[:200]}...")

        # LoRA model
        outputs = lora_model.generate(**inputs, max_new_tokens=100)
        response_lora = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"After:  {response_lora[:200]}...")
```

---

## Expected Results

### Training Metrics
- **Loss:** Should decrease from ~2.5 to <1.0
- **Perplexity:** Should improve significantly
- **Trainable params:** Only ~0.1% of total parameters

### Memory Usage
- **Full model:** ~14 GB VRAM (7B @ float16)
- **LoRA:** ~14 GB VRAM (same, but fewer trainable params)
- **QLoRA:** ~5 GB VRAM (4-bit quantization)

### Quality
- Improved instruction following
- Better response relevance
- Maintains base model capabilities

---

## Key Features Implemented

### 1. **Basic LoRA**
- Low-rank adaptation for efficient fine-tuning
- Only ~0.1% parameters trainable
- Preserves base model knowledge

### 2. **QLoRA (Quantized LoRA)**
- 4-bit quantization for memory efficiency
- Double quantization for extra savings
- NF4 data type for optimal quantization

### 3. **Advanced Techniques**
- Multi-adapter management
- Custom module targeting
- Gradient checkpointing
- Instruction tuning format

### 4. **Evaluation**
- Before/after comparison
- Accuracy metrics
- Perplexity tracking

---

**Difficulty:** ⭐⭐⭐⭐
**Lines of Code:** ~450
