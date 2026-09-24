# LAB-005: DPO Alignment

**Align language models with human preferences using Direct Preference Optimization**

**Time:** 5-6 hours
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:**
- LAB-003: LoRA Fine-Tuning
- 5201-DPO-Theory.md
- 5202-Alignment-Orchestration.md

---

## 🎯 Lab Objectives

After completing this lab, you will be able to:
- ✅ Understand DPO (Direct Preference Optimization) algorithm
- ✅ Create preference datasets from model outputs
- ✅ Train models with DPO alignment
- ✅ Evaluate alignment quality
- ✅ Compare DPO vs RLHF approaches

---

## 📋 Overview

### What is DPO?

**DPO (Direct Preference Optimization)** is a method for aligning language models with human preferences without training a separate reward model. It's simpler and more stable than traditional RLHF (PPO).

**Key advantages:**
- No reward model needed
- More stable training
- Simpler implementation
- Better sample efficiency

### DPO vs RLHF

```text
Traditional RLHF:
Data → Train Reward Model → PPO with Reward Model → Aligned Model
(Complex, unstable, many hyperparameters)

DPO:
Data → Direct Preference Optimization → Aligned Model
(Simple, stable, fewer hyperparameters)
```

---

## 🏗️ Part 1: Environment Setup (30 min)

### Step 1.1: Install Dependencies

```bash
# Create virtual environment
python -m venv dpo-env
source dpo-env/bin/activate  # On Windows: dpo-env\Scripts\activate

# Install required packages
pip install torch transformers trl peft datasets
pip install wandb  # For experiment tracking

# Verify installation
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import trl; print(f'TRL: {trl.__version__}')"
```

### Step 1.2: Download Base Model

```bash
# We'll use a smaller model for this lab
# Options: Phi-3-mini (3.8B), Llama-3.2-3B, or Mistral-7B

# Using Hugging Face CLI
pip install huggingface_hub

# Login if you need access to gated models
huggingface-cli login

# Download model (will be done automatically during training)
# Or pre-download:
# huggingface-cli download microsoft/Phi-3-mini-4k-instruct --local-dir ./models/phi-3
```

---

## 📊 Part 2: Create Preference Dataset (90 min)

### Understanding Preference Data

DPO requires paired examples:
- **Chosen:** Better response
- **Rejected:** Worse response

```text
Example:
Prompt: "What's the capital of France?"
Chosen: "The capital of France is Paris, known for the Eiffel Tower."
Rejected: "Paris."
```

### Step 2.1: Generate Candidate Responses

```python
# File: generate_candidates.py
"""
Generate multiple candidate responses for DPO dataset
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from datasets import load_dataset
import json

# Load model and tokenizer
model_name = "microsoft/Phi-3-mini-4k-instruct"  # or your preferred model

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Load prompt dataset
# Using a sample dataset - replace with your domain data
prompts = [
    "Explain quantum computing in simple terms.",
    "What are the benefits of regular exercise?",
    "How does photosynthesis work?",
    "Write a short poem about nature.",
    "Explain the difference between Python and JavaScript.",
    # Add more prompts...
]

def generate_response(prompt, temperature=0.8, max_length=256):
    """Generate a response from the model"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response

# Generate multiple responses per prompt
candidates = []

for prompt in prompts:
    print(f"Generating responses for: {prompt[:50]}...")

    # Generate 3 different responses
    responses = []
    for i in range(3):
        response = generate_response(prompt, temperature=0.7 + i * 0.1)
        responses.append(response)
        print(f"  Response {i+1}: {response[:100]}...")

    candidates.append({
        "prompt": prompt,
        "responses": responses,
    })

# Save candidates
with open("candidates.json", "w") as f:
    json.dump(candidates, f, indent=2)

print(f"\nGenerated {len(candidates)} prompt groups with {len(prompts)} responses each")
```

### Step 2.2: Rank and Create Pairs

```python
# File: create_pairs.py
"""
Rank responses and create preference pairs
"""

import json
from typing import List, Dict

# Method 1: Manual ranking (recommended for learning)
def manual_ranking(candidates):
    """
    Manually rank responses to create high-quality pairs
    """
    pairs = []

    for item in candidates:
        prompt = item["prompt"]
        responses = item["responses"]

        print(f"\n{'='*60}")
        print(f"Prompt: {prompt}")
        print(f"{'='*60}")

        for i, resp in enumerate(responses):
            print(f"\n[{i+1}] {resp}")

        # Get human ranking
        print("\nRank the responses (best to worst, e.g., '2 1 3'):")
        ranking = input("> ").strip()

        try:
            ranked_indices = [int(x) - 1 for x in ranking.split()]
            if len(ranked_indices) < 2:
                print("Need at least 2 rankings, skipping...")
                continue

            # Create pairs: best vs second best, best vs worst
            best_idx = ranked_indices[0]

            for worse_idx in ranked_indices[1:]:
                pairs.append({
                    "prompt": prompt,
                    "chosen": responses[best_idx],
                    "rejected": responses[worse_idx],
                })

        except (ValueError, IndexError):
            print("Invalid ranking, skipping...")
            continue

    return pairs

# Method 2: AI-assisted ranking
def ai_ranking(candidates, judge_model_name="gpt-4"):
    """
    Use an AI model to rank responses
    (Requires API access to GPT-4 or similar)
    """
    import openai

    pairs = []

    for item in candidates:
        prompt = item["prompt"]
        responses = item["responses"]

        # Create ranking prompt
        rank_prompt = f"""
        Rank the following responses to this prompt from best to worst.
        Consider: accuracy, clarity, completeness, and helpfulness.

        Prompt: {prompt}

        Responses:
        {chr(10).join([f'{i+1}. {resp}' for i, resp in enumerate(responses)])}

        Respond only with the ranking numbers (e.g., '2 1 3'):
        """

        # Get ranking
        response = openai.ChatCompletion.create(
            model=judge_model_name,
            messages=[{"role": "user", "content": rank_prompt}],
            max_tokens=50,
        )

        ranking_str = response.choices[0].message.content.strip()

        try:
            ranked_indices = [int(x) - 1 for x in ranking_str.split()]

            if len(ranked_indices) >= 2:
                best_idx = ranked_indices[0]

                for worse_idx in ranked_indices[1:]:
                    pairs.append({
                        "prompt": prompt,
                        "chosen": responses[best_idx],
                        "rejected": responses[worse_idx],
                    })

        except (ValueError, IndexError):
            continue

    return pairs

# Load candidates and create pairs
with open("candidates.json", "r") as f:
    candidates = json.load(f)

# Create preference pairs
print("Creating preference pairs...")
print("Choose method:")
print("1. Manual ranking (recommended for learning)")
print("2. AI-assisted ranking")

choice = input("> ").strip()

if choice == "1":
    pairs = manual_ranking(candidates)
else:
    pairs = ai_ranking(candidates)

# Save preference pairs
with open("preference_pairs.json", "w") as f:
    json.dump(pairs, f, indent=2)

print(f"\nCreated {len(pairs)} preference pairs")
print(f"Saved to preference_pairs.json")
```

### Step 2.3: Load Standard Preference Dataset (Optional)

```python
# File: load_standard_dataset.py
"""
Load a standard preference dataset
"""

from datasets import load_dataset

# Option 1: HH-RLHF (Anthropic's Helpful-Harmless dataset)
# This requires accepting the dataset terms on Hugging Face
print("Loading HH-RLHF dataset...")
try:
    hh_dataset = load_dataset("Anthropic/hh-rlhf", "harmless-base")
    print(f"HH-RLHF: {hh_dataset}")
except Exception as e:
    print(f"Could not load HH-RLHF: {e}")

# Option 2: OpenAssistant dataset (no approval needed)
print("\nLoading OpenAssistant dataset...")
oa_dataset = load_dataset("OpenAssistant/oasst1")
print(f"OpenAssistant: {oa_dataset}")

# Option 3: Stanford Human Preferences (SHP)
print("\nLoading SHP dataset...")
try:
    shp_dataset = load_dataset("stanfordnlp/SHP")
    print(f"SHP: {shp_dataset}")
except Exception as e:
    print(f"Could not load SHP: {e}")

# Option 4: Use a smaller sample dataset for this lab
print("\nUsing sample preference data for lab...")

sample_data = [
    {
        "prompt": "What is the capital of France?",
        "chosen": "The capital of France is Paris. It's known for landmarks like the Eiffel Tower and the Louvre Museum.",
        "rejected": "Paris.",
    },
    {
        "prompt": "Explain gravity.",
        "chosen": "Gravity is a fundamental force that attracts objects with mass toward each other. On Earth, it gives weight to physical objects.",
        "rejected": "Gravity makes things fall down.",
    },
    {
        "prompt": "How do I bake a cake?",
        "chosen": "To bake a cake: 1) Preheat oven to 350°F, 2) Mix flour, sugar, baking powder, 3) Add eggs, milk, butter, 4) Pour into pan, 5) Bake 30-35 minutes.",
        "rejected": "Just put ingredients in oven.",
    },
    # Add more pairs...
]

print(f"Using {len(sample_data)} sample preference pairs")
```

---

## 🎯 Part 3: Train with DPO (120 min)

### Step 3.1: Setup DPO Trainer

```python
# File: dpo_training.py
"""
Train model with DPO alignment
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from trl import DPOTrainer
from datasets import Dataset
import json

# Load preference pairs
with open("preference_pairs.json", "r") as f:
    preference_data = json.load(f)

# Convert to Hugging Face dataset format
def format_for_dpo(preference_data):
    """Format preference data for DPO trainer"""
    return {
        "prompt": [item["prompt"] for item in preference_data],
        "chosen": [item["chosen"] for item in preference_data],
        "rejected": [item["rejected"] for item in preference_data],
    }

# Create dataset
dataset_dict = format_for_dpo(preference_data)
train_dataset = Dataset.from_dict(dataset_dict)

# Split into train/validation
train_dataset = train_dataset.train_test_split(test_size=0.2)
train_data = train_dataset["train"]
eval_data = train_dataset["test"]

print(f"Training samples: {len(train_data)}")
print(f"Validation samples: {len(eval_data)}")

# Load base model
model_name = "microsoft/Phi-3-mini-4k-instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Apply LoRA for efficient training
from peft import LoraConfig, get_peft_model

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

# Configure DPO training
training_args = TrainingArguments(
    output_dir="./dpo_output",
    num_train_epochs=3,
    per_device_train_batch_size=2,  # Adjust based on GPU memory
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=1e-5,
    warmup_ratio=0.1,
    logging_steps=10,
    save_steps=50,
    eval_steps=50,
    fp16=True,
    gradient_checkpointing=True,
    report_to="wandb",  # Or "tensorboard"
    run_name="dpo-alignment-lab",
)

# DPO configuration
dpo_config = {
    "beta": 0.1,  # DPO temperature (lower = more conservative)
    "label_smoothing": 0.0,  # No label smoothing
    "loss_type": "sigmoid",  # Loss type
}

# Create DPO trainer
dpo_trainer = DPOTrainer(
    model=model,
    ref_model=None,  # Will use model as reference
    args=training_args,
    train_dataset=train_data,
    eval_dataset=eval_data,
    tokenizer=tokenizer,
    beta=dpo_config["beta"],
    max_length=512,
    max_prompt_length=256,
)

print("\nStarting DPO training...")
print(f"Configuration: {dpo_config}")

# Train
dpo_trainer.train()

# Save model
dpo_trainer.save_model("./dpo_final_model")
tokenizer.save_pretrained("./dpo_final_model")

print("\nTraining complete!")
print(f"Model saved to ./dpo_final_model")
```

### Step 3.2: Monitor Training

```python
# File: monitor_training.py
"""
Monitor DPO training with metrics
"""

import wandb

# Initialize wandb
wandb.init(
    project="dpo-alignment-lab",
    config={
        "model": "Phi-3-mini",
        "learning_rate": 1e-5,
        "batch_size": 2,
        "gradient_accumulation": 4,
        "beta": 0.1,
    },
)

# Log metrics during training
# (This is handled automatically by DPOTrainer)

# After training, plot metrics
import matplotlib.pyplot as plt

# Load training logs
# (In production, extract from wandb or trainer logs)

# Example metrics visualization
metrics = {
    "loss": [2.5, 2.1, 1.8, 1.5, 1.3, 1.1, 0.9, 0.8],
    "reward_accuracy": [0.55, 0.62, 0.68, 0.73, 0.78, 0.82, 0.85, 0.87],
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

ax1.plot(metrics["loss"], marker='o')
ax1.set_xlabel("Step")
ax1.set_ylabel("Loss")
ax1.set_title("DPO Loss Over Time")
ax1.grid(True)

ax2.plot(metrics["reward_accuracy"], marker='o', color='green')
ax2.set_xlabel("Step")
ax2.set_ylabel("Accuracy")
ax2.set_title("Reward Accuracy Over Time")
ax2.grid(True)

plt.tight_layout()
plt.savefig("dpo_metrics.png")
print("Metrics plot saved to dpo_metrics.png")
```

---

## 🧪 Part 4: Evaluate Alignment (60 min)

### Step 4.1: Compare Before/After

```python
# File: evaluate_alignment.py
"""
Compare base model vs DPO-aligned model
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Load models
base_model_name = "microsoft/Phi-3-mini-4k-instruct"
aligned_model_name = "./dpo_final_model"

base_tokenizer = AutoTokenizer.from_pretrained(base_model_name)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

aligned_tokenizer = AutoTokenizer.from_pretrained(aligned_model_name)
aligned_model = AutoModelForCausalLM.from_pretrained(
    aligned_model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Test prompts
test_prompts = [
    "What's the capital of France?",
    "Explain quantum computing.",
    "How do I make a cake?",
    "Write a poem about AI.",
    "What causes climate change?",
]

def generate_response(model, tokenizer, prompt, max_length=256):
    """Generate response from model"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response

# Compare responses
print("="*80)
print("COMPARISON: Base Model vs DPO-Aligned Model")
print("="*80)

for prompt in test_prompts:
    print(f"\n{'='*80}")
    print(f"PROMPT: {prompt}")
    print(f"{'='*80}\n")

    # Base model response
    base_response = generate_response(base_model, base_tokenizer, prompt)
    print(f"BASE MODEL:\n{base_response}\n")

    # Aligned model response
    aligned_response = generate_response(aligned_model, aligned_tokenizer, prompt)
    print(f"DPO-ALIGNED:\n{aligned_response}\n")

    # Ask for human preference
    print("-" * 80)
    preference = input("Which is better? (1=base, 2=aligned, =tie, s=skip): ").strip()

    if preference == "1":
        print("Preference: Base model")
    elif preference == "2":
        print("Preference: DPO-aligned")
    elif preference == "=":
        print("Preference: Tie")
    else:
        print("Skipped")
```

### Step 4.2: Automated Evaluation

```python
# File: auto_evaluate.py
"""
Automated evaluation metrics for alignment
"""

import json
from typing import List
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import CrossEncoder

# Load reward model for evaluation
reward_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def score_response(prompt, response):
    """Score a response using a reward model"""
    # Encode prompt-response pair
    features = [[prompt, response]]

    # Get score
    with torch.no_grad():
        scores = reward_model.predict(features)

    return scores[0]

def evaluate_model(model, tokenizer, test_data):
    """Evaluate model on test data"""
    scores = []

    for item in test_data:
        prompt = item["prompt"]

        # Generate response
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)

        # Score response
        score = score_response(prompt, response)
        scores.append(score)

    return sum(scores) / len(scores) if scores else 0

# Test data
test_data = [
    {"prompt": "What's the capital of France?"},
    {"prompt": "Explain gravity."},
    {"prompt": "How do I bake a cake?"},
]

# Evaluate both models
print("Evaluating models...")

base_score = evaluate_model(base_model, base_tokenizer, test_data)
aligned_score = evaluate_model(aligned_model, aligned_tokenizer, test_data)

print(f"\nBase Model Score: {base_score:.3f}")
print(f"Aligned Model Score: {aligned_score:.3f}")
print(f"Improvement: {(aligned_score - base_score) / base_score * 100:.1f}%")
```

---

## 📊 Part 5: Analyze Results (30 min)

### Step 5.1: Training Metrics

```python
# File: analyze_results.py
"""
Analyze DPO training results
"""

# Key metrics to track:
# 1. Loss over time (should decrease)
# 2. Reward accuracy (should increase)
# 3. Chosen vs rejected margin (should increase)
# 4. Response quality (subjective)

# Example results
results = {
    "training_steps": 500,
    "final_loss": 0.8,
    "final_reward_accuracy": 0.87,
    "training_time_hours": 2.5,
    "human_preference_rate": 0.73,  # 73% preferred aligned model
}

print("DPO Training Results:")
print(f"  Training Steps: {results['training_steps']}")
print(f"  Final Loss: {results['final_loss']:.3f}")
print(f"  Final Reward Accuracy: {results['final_reward_accuracy']:.1%}")
print(f"  Training Time: {results['training_time_hours']:.1f} hours")
print(f"  Human Preference Rate: {results['human_preference_rate']:.1%}")
```

### Step 5.2: Compare with Different Beta Values

```python
# File: beta_comparison.py
"""
Compare DPO with different beta values
"""

# Beta controls the "temperature" of DPO
# - Lower beta (0.01-0.1): More conservative, smaller changes
# - Higher beta (0.1-1.0): More aggressive, larger changes

beta_values = [0.01, 0.05, 0.1, 0.5, 1.0]

for beta in beta_values:
    print(f"\nTraining with beta={beta}")

    # Train with this beta
    # (Simplified - in practice, run full training for each)

    # Expected outcomes:
    # beta=0.01: Minimal change, high stability
    # beta=0.1: Balanced change and stability (recommended)
    # beta=0.5: Aggressive alignment, may overfit
    # beta=1.0: Very aggressive, risk of degradation
```

---

## ✅ Completion Checklist

Use this checklist to track your progress:

### Setup
- [ ] Environment configured
- [ ] Dependencies installed
- [ ] Base model downloaded

### Data Preparation
- [ ] Candidates generated
- [ ] Preference pairs created
- [ ] Dataset formatted for DPO

### Training
- [ ] DPO trainer configured
- [ ] Training completed (3 epochs)
- [ ] Model saved

### Evaluation
- [ ] Base model vs aligned comparison
- [ ] Automated evaluation completed
- [ ] Human evaluation completed

### Analysis
- [ ] Training metrics analyzed
- [ ] Results documented
- [ ] Key learnings recorded

---

## 🎓 Key Learnings

### What DPO Does

1. **Directly optimizes** for human preferences
2. **No reward model** needed
3. **Simpler** than RLHF/PPO
4. **More stable** training

### Common Issues

**Issue 1: Training is unstable**
- Solution: Reduce learning rate or increase beta

**Issue 2: Model overfits to training data**
- Solution: Add regularization, reduce training epochs

**Issue 3: Aligned model is too conservative**
- Solution: Reduce beta value

**Issue 4: No improvement over baseline**
- Solution: Check preference data quality, increase training data

### Best Practices

1. **Start with high-quality preference data**
2. **Use beta=0.1** as starting point
3. **Monitor reward accuracy** during training
4. **Use small learning rate** (1e-5 to 5e-5)
5. **Validate with human evaluation**

---

## 🚀 Next Steps

After completing this lab:

1. **LAB-006: Train Model from Scratch** - Learn pre-training
2. **LAB-007: Production RAG** - Build production RAG system
3. **5202-Alignment-Orchestration.md** - Advanced alignment techniques

---

## 📖 Further Reading

- [DPO Paper: Direct Preference Optimization](https://arxiv.org/abs/2305.18290)
- [TRL Documentation](https://huggingface.co/docs/trl/main/en/dpo_trainer)
- [Alignment Research](https://alignment.org/)

---

**Lab Status:** ✅ Complete
**Last Updated:** 2026-02-04
**Maintainer:** AI Engineering Curriculum Team
