# LAB-502: DPO Alignment

## Overview
Implement Direct Preference Optimization for LLM alignment.

## Prerequisites
- LAB-501 completed
- Understanding of RLHF/DPO

## Setup

```bash
pip install torch transformers trl datasets
```

## Exercise 1: Prepare Preference Dataset

```python
from datasets import Dataset

# TODO: Create preference pairs
preference_data = {
    "prompt": [
        "What is the capital of France?",
        "Explain quantum computing.",
        "Write a poem about AI."
    ] * 100,

    "chosen": [
        "The capital of France is Paris, located in the northern part of the country.",
        "Quantum computing uses quantum bits (qubits) that can exist in superposition...",
        "In circuits deep and silicon bright, where dreams and data take their flight...",
    ] * 100,

    "rejected": [
        "France's capital is London.",  # Wrong
        "Quantum is fast computing.",  # Too vague
        "AI poem. AI is cool. AI is great.",  # Low quality
    ] * 100
}

# TODO: Create dataset
dataset = Dataset.from_dict(preference_data)

# Split
train_test = dataset.train_test_split(test_size=0.1)
train_dataset = train_test['train']
eval_dataset = train_test['test']

print(f"Train: {len(train_dataset)}")
print(f"Eval: {len(eval_dataset)}")
```

## Exercise 2: Load Model for DPO

```python
from transformers import AutoModelForCausalLMWithValueHead, AutoTokenizer
from trl import DPOTrainer, DPOConfig

# TODO: Load base model
model_name = "gpt2"  # or "meta-llama/Llama-2-7b-hf"

model = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# TODO: Load reference model (for DPO)
ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name,
    device_map="auto"
)
```

## Exercise 3: Configure DPO

```python
# TODO: DPO configuration
dpo_config = DPOConfig(
    output_dir="./dpo-output",
    learning_rate=1e-5,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    fp16=True,
    logging_steps=10,
    save_steps=100,
)

# TODO: Create trainer
trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    config=dpo_config,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)

print("DPO trainer configured")
```

## Exercise 4: Train DPO

```python
# TODO: Train
print("Starting DPO training...")
trainer.train()

# TODO: Save model
trainer.save_model("./dpo-final")
tokenizer.save_pretrained("./dpo-final")

print("Model saved!")
```

## Exercise 5: Compare Before/After DPO

```python
# TODO: Load fine-tuned model
from transformers import AutoModelForCausalLM

model_base = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
model_dpo = AutoModelForCausalLM.from_pretrained("./dpo-final", device_map="auto")

# Test prompts
test_prompts = [
    "What is the capital of France?",
    "Explain quantum computing in simple terms.",
    "Write a short poem about artificial intelligence."
]

for prompt in test_prompts:
    # Base model
    inputs_base = tokenizer(prompt, return_tensors="pt").to(model_base.device)
    outputs_base = model_base.generate(**inputs_base, max_new_tokens=50)
    text_base = tokenizer.decode(outputs_base[0], skip_special_tokens=True)

    # DPO model
    inputs_dpo = tokenizer(prompt, return_tensors="pt").to(model_dpo.device)
    outputs_dpo = model_dpo.generate(**inputs_dpo, max_new_tokens=50)
    text_dpo = tokenizer.decode(outputs_dpo[0], skip_special_tokens=True)

    print(f"\nPrompt: {prompt}")
    print(f"Base:   {text_base[:100]}...")
    print(f"DPO:    {text_dpo[:100]}...")
```

## Exercise 6: Evaluate Alignment

```python
# TODO: Evaluate on preference test set
# Check if DPO model prefers "chosen" over "rejected"

def evaluate_preference(model, tokenizer, prompt, chosen, rejected):
    """Evaluate if model prefers chosen response."""

    # Compute log probs for chosen
    inputs_chosen = tokenizer(prompt + chosen, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs_chosen = model(**inputs_chosen, labels=inputs_chosen['input_ids'])
    log_prob_chosen = -outputs_chosen.loss.item()

    # Compute log probs for rejected
    inputs_rejected = tokenizer(prompt + rejected, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs_rejected = model(**inputs_rejected, labels=inputs_rejected['input_ids'])
    log_prob_rejected = -outputs_rejected.loss.item()

    return log_prob_chosen, log_prob_rejected

# Test on sample
for i in range(5):
    chosen_prob, rejected_prob = evaluate_preference(
        model_dpo, tokenizer,
        eval_dataset[i]['prompt'],
        eval_dataset[i]['chosen'],
        eval_dataset[i]['rejected']
    )

    preferred = "chosen" if chosen_prob > rejected_prob else "rejected"
    print(f"Sample {i+1}: {preferred} (chosen_prob={chosen_prob:.2f}, rejected_prob={rejected_prob:.2f})")
```

## Expected Outputs

1. Exercise 1: Preference dataset created
2. Exercise 2: Models loaded
3. Exercise 3: Trainer configured
4. Exercise 4: Training completes
5. Exercise 5: DPO outputs improved
6. Exercise 6: DPO prefers chosen responses

## Troubleshooting

**Issue:** DPO training unstable
```python
# Solution: Reduce learning rate
dpo_config.learning_rate = 5e-6
```

**Issue:** Model not improving
```python
# Solution: Increase epochs or improve preference data
dpo_config.num_train_epochs = 5
```

## Time Estimate: 4-5 hours

---
