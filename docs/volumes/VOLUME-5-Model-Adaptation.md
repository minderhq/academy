---
Document ID: VOLUME-5
Title: "Volume 5: Model Adaptation"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Tags: ['volume', 'finetuning', 'lora', 'dpo']
---

# Volume 5: Model Adaptation

**"Making Models Your Own"** - Fine-tune and align LLMs for your specific use cases.

---

## Volume Overview

**Difficulty:** ⭐⭐⭐ Advanced
**Time:** 4-5 weeks (part-time)
**Prerequisites:** Volume 4 (Quantization), GPU with 8GB+ VRAM recommended

### What You'll Learn

After completing this volume, you will be able to:
- ✅ Understand LoRA (Low-Rank Adaptation) theory
- ✅ Implement LoRA from scratch
- ✅ Fine-tune models with QLoRA (4-bit)
- ✅ Apply DPO (Direct Preference Optimization) alignment
- ✅ Generate synthetic training data
- ✅ Evaluate fine-tuned models effectively
- ✅ Merge adapters with base models

### Why This Volume Matters

Pre-trained models are generalists. This volume teaches you to:

- **Specialize for your domain** - Medical, legal, technical, custom
- **Improve specific behaviors** - Format, style, tone
- **Align with preferences** - Human feedback, safety, usefulness
- **Do it efficiently** - Fine-tune 7B model on consumer GPU

---

## Learning Path

### Week 1: LoRA Fundamentals

#### Day 1-3: Understanding LoRA
**Fine-tuning without full retraining**

1. **[5101: LoRA Logic](../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)** (3-4 hours)
   - Parameter-efficient fine-tuning concepts
   - Low-rank matrix decomposition
   - Why LoRA works
   - Rank and alpha parameters
   - Target module selection

**LoRA Concept:**
```python
# Standard fine-tuning:
# Update ALL parameters (7B for Mistral)
# Memory: ~28GB (FP32)
# Time: Days on single GPU

# LoRA fine-tuning:
# Add small adapter matrices (rank 8-128)
# Memory: ~500MB (rank 16)
# Time: Hours on single GPU

# LoRA formula:
W_new = W_frozen + (B @ A) * (alpha / rank)
#             ↑              ↑
#          frozen        trainable
#          (7B params)   (rank * dim * 2)
```

**Key Parameters:**
```python
lora_config = {
    "r": 16,           # Rank (higher = more capacity, more memory)
    "lora_alpha": 32,  # Scaling factor (usually 2x rank)
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "lora_dropout": 0.05,
}
```

**Checkpoint:** You understand LoRA theory

---

#### Day 4-5: Implementing LoRA from Scratch
**Build LoRA yourself**

1. **[5104: LoRA Implementation Guide](../phases/phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md)** (3-4 hours)
   - Implement LoRA layer from scratch
   - Integrate with PyTorch modules
   - Test on simple tasks
   - Compare with PEFT library

**Implementation:**
```python
import torch
import torch.nn as nn

class LoRALayer(nn.Module):
    def __init__(self, base_layer, r=16, alpha=32):
        super().__init__()
        self.base_layer = base_layer
        self.r = r
        self.alpha = alpha

        # Get base layer dimensions
        in_features = base_layer.in_features
        out_features = base_layer.out_features

        # LoRA matrices (low-rank decomposition)
        self.lora_A = nn.Parameter(torch.randn(r, in_features) * 0.01)
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))

        self.scaling = alpha / r

    def forward(self, x):
        # Base layer output (frozen)
        base_out = self.base_layer(x)

        # LoRA adapter output
        lora_out = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling

        return base_out + lora_out

# Apply to linear layer
original_layer = nn.Linear(4096, 4096)
lora_layer = LoRALayer(original_layer, r=16, alpha=32)
```

**Checkpoint:** You can implement LoRA from scratch

---

### Week 2: QLoRA Pipelines

#### Day 1-4: 4-bit Fine-tuning
**Train large models on consumer GPUs**

1. **[5102: QLoRA Pipelines](../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)** (4-5 hours)
   - BitsAndBytes 4-bit loading
   - QLoRA training setup
   - Dataset preparation
   - Training hyperparameters
   - Evaluation metrics

**QLoRA Configuration:**
```python
from transformers import (
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# Load model in 4-bit
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-v0.1",
    quantization_config=bnb_config,
    device_map="auto",
)

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

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # Should show <1%

# Training
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_steps=100,
)

trainer = trainer(model, training_args, train_dataset)
trainer.train()
```

2. **[LAB-003: LoRA Fine-Tuning](../learning-resources/labs/LAB-003-LoRA-FineTuning.md)** (4 hours)
   - Complete hands-on lab
   - Prepare custom dataset
   - Train with QLoRA
   - Evaluate and compare
   - Merge adapters

**Checkpoint:** You can fine-tune with QLoRA

---

#### Day 5: Dataset Preparation
**Create effective training data**

**Dataset Types:**
```python
# 1. Instruction tuning
{
    "instruction": "Explain quantum computing",
    "input": "",
    "output": "Quantum computing uses quantum bits..."
}

# 2. Chat format
[
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's AI?"},
]

# 3. Completion format
prompt = "Question: What is AI?\nAnswer:"
completion = "AI is artificial intelligence..."
```

**Best Practices:**
- Quality > Quantity
- Cover your target domain
- Include edge cases
- Balance different types of queries
- Remove duplicates

**Checkpoint:** You can prepare training datasets

---

### Week 3: Alignment with DPO

#### Day 1-3: Direct Preference Optimization
**Align models with human feedback**

1. **[5201: DPO Theory](../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)** (3-4 hours)
   - RLHF vs DPO
   - Preference modeling
   - DPO algorithm
   - Reward-free optimization
   - Implementation details

**DPO vs RLHF:**
```python
# RLHF (Traditional):
# 1. Train reward model on preferences
# 2. Optimize policy with PPO using reward model
# Complex: Requires reward model, PPO, multiple training loops

# DPO (Simpler):
# Directly optimize on preferences
# Single training loop
# More stable, easier to implement

# DPO objective:
# Maximize probability of chosen responses
# Minimize probability of rejected responses
```

**DPO Implementation:**
```python
from trl import DPOTrainer

# Preference pairs
{
    "prompt": "What's the capital of France?",
    "chosen": "The capital of France is Paris.",
    "rejected": "France is in Europe.",
}

# DPO training
dpo_config = {
    "beta": 0.1,  # DPO temperature
    "learning_rate": 5e-5,
}

dpo_trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    beta=dpo_config["beta"],
    train_dataset=preference_dataset,
    tokenizer=tokenizer,
)

dpo_trainer.train()
```

2. **[EXP_5201: DPO Experiments](../../experiments/EXP_5201_DPO.md)** (3-4 hours)
   - Collect preference data
   - Train with DPO
   - Compare with SFT
   - Evaluate alignment

**Checkpoint:** You understand and can apply DPO

---

#### Day 4-5: Alignment Orchestration
**Putting it all together**

1. **[5202: Alignment Orchestration](../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md)** (2-3 hours)
   - SFT (Supervised Fine-Tuning)
   - Reward Modeling
   - DPO vs RLHF
   - Multi-stage alignment
   - Evaluation metrics

**Alignment Pipeline:**
```python
# Stage 1: Pre-training (done by model creators)
# Model learns from internet-scale data

# Stage 2: SFT (Supervised Fine-Tuning)
# Train on instruction-response pairs
trainer = SFTTrainer(model, dataset)

# Stage 3: Reward Modeling (optional for DPO)
# Train reward model on human preferences
reward_model = train_reward_model(preference_dataset)

# Stage 4: Alignment (DPO or RLHF)
# Align with human preferences
dpo_trainer = DPOTrainer(model, preference_dataset)

# Stage 5: Evaluation
# Test on held-out preferences
evaluate_alignment(model, test_set)
```

**Checkpoint:** You understand the full alignment pipeline

---

### Week 4: Synthetic Data & Advanced Topics

#### Day 1-3: Knowledge Distillation
**Train small models using large models**

1. **[5301: Knowledge Distillation](../phases/phase5-finetuning/5300-synthetic/5301-Knowledge-Distillation.md)** (3-4 hours)
   - Distillation concepts
   - Teacher-student models
   - Synthetic data generation
   - Data quality filtering
   - Domain adaptation

**Distillation Pipeline:**
```python
# 1. Generate synthetic data with teacher
teacher_model = load_model("mistralai/Mistral-7B-v0.1")

prompts = load_your_domain_prompts()
synthetic_data = []

for prompt in prompts:
    response = teacher_model.generate(
        prompt,
        temperature=0.7,
        max_tokens=1024,
    )
    synthetic_data.append({
        "prompt": prompt,
        "response": response,
    })

# 2. Filter for quality
filtered_data = filter_quality(synthetic_data)

# 3. Train student on synthetic data
student_model = load_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
trainer = SFTTrainer(student_model, filtered_data)
trainer.train()

# Result: Student model with teacher's knowledge
```

2. **[5302: Distributed Training](../phases/phase5-finetuning/5300-synthetic/5302-Distributed-Training.md)** (2-3 hours)
   - Multi-GPU training
   - FSDP (Fully Sharded Data Parallel)
   - DeepSpeed integration
   - Training orchestration

**Checkpoint:** You can generate and use synthetic data

---

#### Day 4-5: Evaluation & Model Merging
**Assess and combine fine-tuned models**

**Evaluation Metrics:**
```python
# 1. Perplexity (lower is better)
perplexity = evaluate_perplexity(model, test_set)

# 2. Task accuracy
accuracy = evaluate_task(model, benchmark_dataset)

# 3. Human evaluation
# - Helpfulness
# - Harmlessness
# - Honesty

# 4. Model comparison
base_model_score = evaluate(base_model)
finetuned_score = evaluate(finetuned_model)
improvement = finetuned_score - base_model_score
```

**Model Merging:**
```python
# Merge LoRA adapter with base model
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1")

# Load LoRA adapter
adapter = PeftModel.from_pretrained(base_model, "./my-lora-adapter")

# Merge and save
merged_model = adapter.merge_and_unload()
merged_model.save_pretrained("./merged-model")

# Convert to GGUF for inference
# ./quantize merged-model.gguf merged-model-q4_k_m.gguf Q4_K_M
```

**Checkpoint:** You can evaluate and merge models

---

## Volume 5 Capstone Projects

### Project A: Fine-Tune Domain-Specific Model

**Time:** 8-10 hours
**Difficulty:** ⭐⭐⭐⭐

**Tasks:**
1. Collect domain-specific dataset (medical, legal, technical)
2. Clean and format data
3. Fine-tune with QLoRA
4. Evaluate improvements
5. Deploy with vLLM

**Skills Demonstrated:**
- Dataset preparation ✅
- QLoRA training ✅
- Evaluation ✅
- Deployment ✅

### Project B: Implement LoRA from Scratch

**Time:** 6-8 hours
**Difficulty:** ⭐⭐⭐⭐

**Tasks:**
1. Implement LoRA layer class
2. Apply to transformer model
3. Train on simple task
4. Compare with PEFT library
5. Document differences

**Skills Demonstrated:**
- LoRA implementation ✅
- PyTorch mastery ✅
- Algorithm understanding ✅

### Project C: DPO Alignment Pipeline

**Time:** 10-12 hours
**Difficulty:** ⭐⭐⭐⭐⭐

**Tasks:**
1. Collect preference data
2. Train SFT model
3. Apply DPO alignment
4. Evaluate alignment metrics
5. Compare with baseline

**Skills Demonstrated:**
- Full alignment pipeline ✅
- Preference modeling ✅
- Evaluation ✅

---

## Volume 5 Checklist

Use this checklist to track your progress:

### Core Content (Required)
- [ ] **5101: LoRA Logic** (3-4 hours)
- [ ] **5104: LoRA Implementation Guide** (3-4 hours)
- [ ] **5102: QLoRA Pipelines** (4-5 hours)
- [ ] **LAB-003: LoRA Fine-Tuning** (4 hours)
- [ ] **5201: DPO Theory** (3-4 hours)
- [ ] **EXP_5201: DPO Experiments** (3-4 hours)
- [ ] **5202: Alignment Orchestration** (2-3 hours)
- [ ] **5301: Knowledge Distillation** (3-4 hours)
- [ ] **5302: Distributed Training** (2-3 hours)

**Total Core Time:** ~30-35 hours

### Capstone Projects (Choose 1)
- [ ] **Project A: Domain-Specific Model** (8-10 hours)
- [ ] **Project B: LoRA from Scratch** (6-8 hours)
- [ ] **Project C: DPO Pipeline** (10-12 hours)

---

## Cross-References

### How Volume 5 Connects to Other Volumes:

**LoRA (5101, 5104) →**
- Volume 2: Linear algebra foundations
- Volume 3: Understanding model architecture
- Volume 4: QLoRA uses 4-bit quantization
- Volume 6: Fine-tune models for RAG
- Volume 7: Deploy fine-tuned models

**DPO (5201, 5202) →**
- Volume 3: Understanding model behavior
- Volume 4: Quantized alignment
- Volume 7: Production alignment

**Synthetic Data (5301, 5302) →**
- Volume 6: Generate training data for RAG
- Volume 7: Continuous improvement

---

## Volume 5 Statistics

| Metric | Value |
|--------|-------|
| **Core Documents** | 9 files |
| **Experiments** | 1 experiment |
| **Labs** | 1 lab |
| **Capstone Projects** | 3 projects |
| **Estimated Time** | 30-35 hours (core) + 6-12 hours (project) |
| **Difficulty** | ⭐⭐⭐ Advanced |

---

## Key Takeaways

### LoRA vs Full Fine-Tuning

```text
Full Fine-Tuning:
- Update all 7B parameters
- Memory: ~28GB (FP32)
- Time: Days
- Storage: 28GB per model

LoRA Fine-Tuning:
- Add adapter matrices (rank 16)
- Memory: ~500MB
- Time: Hours
- Storage: 100MB per adapter
- Can swap adapters!

Choose LoRA for:
- Consumer GPU training
- Multiple adapters per base model
- Faster iteration
```

### QLoRA Memory Savings

```text
FP16 Training:
- Model: ~14GB (7B params × 2 bytes)
- Gradients: ~14GB
- Optimizer states: ~42GB
- Total: ~70GB

QLoRA (4-bit):
- Model: ~5GB (4-bit quantized)
- Gradients: ~500MB (LoRA only)
- Optimizer: ~1GB (LoRA only)
- Total: ~7GB

70GB → 7GB = 10x memory reduction!
```

### Alignment Pipeline

```text
1. Pre-training (Base Model)
   ↓
2. SFT (Instruction Following)
   ↓
3. Reward Model (Optional for DPO)
   ↓
4. DPO / RLHF (Alignment)
   ↓
5. Evaluation & Deployment

Each stage specializes the model further.
```

---

## Troubleshooting

### Common Issues in Volume 5

**Problem:** LoRA not learning
- **Solution:** Increase rank, check learning rate, verify data quality

**Problem:** QLoRA OOM
- **Solution:** Reduce batch size, enable gradient checkpointing, reduce rank

**Problem:** DPO makes model worse
- **Solution:** Check preference data quality, adjust beta, reduce learning rate

**Problem:** Synthetic data low quality
- **Solution:** Filter rigorously, use diverse prompts, verify outputs

For more help, see **[TROUBLESHOOTING-Common-Issues.md](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)**

---

## After Volume 5

### You're Ready For:

**Volume 6: Data Nexus** - Build RAG systems with fine-tuned models
**Volume 7: Production** - Deploy fine-tuned models at scale

### Skills You've Gained:

```text
# You can now:
✅ Understand LoRA theory
✅ Implement LoRA from scratch
✅ Fine-tune with QLoRA
✅ Apply DPO alignment
✅ Generate synthetic data
✅ Evaluate model quality
✅ Merge and deploy fine-tuned models
```

---

## Next Steps

1. **Track your progress** in [PROGRESS-TRACKER.md](../00-META/PROGRESS-TRACKER.md)
2. **Continue to Volume 6** for RAG and knowledge systems
3. **OR skip to Volume 7** for production deployment
4. **Review the [VOLUME-GUIDE.md](../00-META/VOLUME-GUIDE.md)** for alternative learning paths

---

**Recommended Resources:**
- **[PEFT Library](https://huggingface.co/docs/peft)** - LoRA implementation
- **[TRL Library](https://huggingface.co/docs/trl)** - DPO and SFT trainers
- **[LoRA Paper](https://arxiv.org/abs/2106.09685)** - Original LoRA paper
- **[QLoRA Paper](https://arxiv.org/abs/2305.14314)** - QLoRA details
- **[DPO Paper](https://arxiv.org/abs/2305.18290)** - DPO algorithm

---

**Volume 5 Status:** 🟢 Complete
**Maintainer:** PROJECT-OMEGA Team
