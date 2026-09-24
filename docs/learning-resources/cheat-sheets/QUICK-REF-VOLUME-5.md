---
Document ID: QUICK-REF-VOLUME-5
Title: "Volume 5: Fine-Tuning Expert - Quick Reference"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Intermediate
---

# Volume 5: Fine-Tuning Expert - Quick Reference

**Adapt Models to Your Needs** - LoRA, QLoRA, DPO, and alignment

---

## 🎯 LoRA (Low-Rank Adaptation)

### Concept
```python
# LoRA: Freeze pretrained weights, add trainable rank decomposition
# Instead of updating W (d x d), update A (d x r) and B (r x d)
# where r << d (typically r = 8, 16, 32)

# Standard fine-tuning:
# W_new = W + ΔW
# ΔW has d x d parameters (e.g., 4096 x 4096 = 16M params)

# LoRA:
# W_new = W + B @ A
# B has r x d parameters (e.g., 16 x 4096 = 65K params)
# A has d x r parameters (e.g., 4096 x 16 = 65K params)
# Total: 130K params (0.8% of original)

# Memory: 130K * 4 bytes = 0.5 MB (vs 64 MB for full fine-tuning)
```

### LoRA Implementation
```python
class LoRALinear(nn.Module):
    """LoRA linear layer"""

    def __init__(self, in_features, out_features, rank=16, alpha=32, dropout=0.1):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha

        # Frozen pretrained weight
        self.weight = nn.Parameter(torch.randn(out_features, in_features))
        self.weight.requires_grad = False

        # Trainable low-rank adapters
        self.lora_A = nn.Parameter(torch.randn(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))
        self.scaling = alpha / rank

        self.dropout = nn.Dropout(dropout)
        self.reset_parameters()

    def reset_parameters(self):
        # Initialize A with Kaiming, B with zeros
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

    def forward(self, x):
        # Standard linear: W @ x
        result = F.linear(x, self.weight)

        # LoRA: (B @ A) @ x
        lora_result = F.linear(
            self.dropout(x),
            self.lora_B @ self.lora_A
        ) * self.scaling

        return result + lora_result

# Usage: Replace nn.Linear with LoRALinear
# No need to modify model architecture
```

### LoRA Configuration
```python
from peft import LoraConfig, get_peft_model

# LoRA configuration
lora_config = LoraConfig(
    r=16,                    # Rank (higher = more capacity, more memory)
    lora_alpha=32,           # Scaling factor (typically 2x rank)
    target_modules=[         # Which modules to apply LoRA
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_dropout=0.05,       # Dropout for LoRA layers
    bias="none",             # Whether to train bias ("none", "all", "lora_only")
    task_type="CAUSAL_LM",   # Task type
)

# Apply to model
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
model = get_peft_model(model, lora_config)

# Check trainable parameters
model.print_trainable_parameters()
# Output: trainable params: 0.8% || all params: 7B || trainable%: 0.8
```

---

## 🔧 QLoRA (Quantized LoRA)

### Concept
```python
# QLoRA: LoRA + 4-bit quantization
# Train LoRA adapters on quantized base model

# Benefits:
# - Even lower memory usage
# - Can fine-tune 7B on single 24GB GPU
# - Minimal quality loss vs full LoRA

# QLoRA innovations:
# 1. 4-bit NormalFloat (NF4) quantization
# 2. Double quantization (quantize the quantization scales)
# 3. Paged optimizers (offload optimizer to CPU RAM)
```

### QLoRA Implementation
```python
from transformers import BitsAndBytesConfig
from peft import LoraConfig, get_peft_model

# 4-bit quantization config
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,   # Compute in FP16
    bnb_4bit_use_double_quant=True,         # Double quantization
    bnb_4bit_quant_type="nf4",              # NormalFloat 4-bit
)

# Load model with 4-bit quantization
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=quantization_config,
    device_map="auto",
)

# Apply LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)

# Memory comparison:
# Full fine-tuning (FP16): 7B * 2 bytes = 14 GB (weights) + 14 GB (gradients) + 14 GB (optimizer) = 42 GB
# LoRA (FP16): 14 GB + 0.1 GB + 0.1 GB = 14.2 GB
# QLoRA (4-bit): 3.5 GB + 0.1 GB + 0.1 GB = 3.7 GB
```

---

## 🎓 DPO (Direct Preference Optimization)

### Concept
```python
# DPO: Direct optimization from preferences without reward model
# Simpler and more stable than RLHF (PPO)

# Standard RLHF:
# 1. Train reward model on preference data
# 2. Optimize policy with PPO using reward model
# Issues: Complex, unstable, hyperparameter sensitive

# DPO:
# 1. Directly optimize policy from preferences
# No reward model needed
# More stable training
```

### DPO Algorithm
```python
class DPOTrainer:
    """Direct Preference Optimization trainer"""

    def __init__(self, policy_model, ref_model, beta=0.1):
        """
        policy_model: Model being trained
        ref_model: Frozen reference model (for KL constraint)
        beta: KL penalty coefficient
        """
        self.policy_model = policy_model
        self.ref_model = ref_model
        self.beta = beta

        # Freeze reference model
        for param in self.ref_model.parameters():
            param.requires_grad = False

    def dpo_loss(self, chosen_logits, rejected_logits, chosen_ref_logits, rejected_ref_logits):
        """
        Compute DPO loss

        chosen_logits: Logits for chosen response
        rejected_logits: Logits for rejected response
        chosen_ref_logits: Reference model logits for chosen
        rejected_ref_logits: Reference model logits for rejected
        """
        # Compute log probabilities
        chosen_logp = F.log_softmax(chosen_logits, dim=-1)
        rejected_logp = F.log_softmax(rejected_logits, dim=-1)
        chosen_ref_logp = F.log_softmax(chosen_ref_logits, dim=-1)
        rejected_ref_logp = F.log_softmax(rejected_ref_logits, dim=-1)

        # Sum over sequence length
        chosen_logp = chosen_logp.sum(dim=-1)  # (batch,)
        rejected_logp = rejected_logp.sum(dim=-1)
        chosen_ref_logp = chosen_ref_logp.sum(dim=-1)
        rejected_ref_logp = rejected_ref_logp.sum(dim=-1)

        # Compute DPO loss
        # loss = -log(sigmoid(beta * (logp_chosen - logp_rejected - (logp_ref_chosen - logp_ref_rejected))))
        log_ratio = (chosen_logp - rejected_logp) - (chosen_ref_logp - rejected_ref_logp)
        loss = -F.logsigmoid(self.beta * log_ratio).mean()

        # Also compute accuracy (how often chosen > rejected)
        with torch.no_grad():
            accuracy = (chosen_logp > rejected_logp).float().mean()

        return loss, accuracy

    def train_step(self, batch):
        """
        batch: {
            "prompt": List[str],
            "chosen": List[str],
            "rejected": List[str],
        }
        """
        # Get policy model outputs
        policy_chosen_logits = self.policy_model(batch["chosen"]).logits
        policy_rejected_logits = self.policy_model(batch["rejected"]).logits

        # Get reference model outputs (no grad)
        with torch.no_grad():
            ref_chosen_logits = self.ref_model(batch["chosen"]).logits
            ref_rejected_logits = self.ref_model(batch["rejected"]).logits

        # Compute loss
        loss, accuracy = self.dpo_loss(
            policy_chosen_logits,
            policy_rejected_logits,
            ref_chosen_logits,
            ref_rejected_logits,
        )

        return loss, accuracy

# Usage
from transformers import AutoModelForCausalLM
from peft import get_peft_model, LoraConfig

# Load models
policy_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
ref_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")

# Apply LoRA to policy model only
policy_model = get_peft_model(policy_model, LoraConfig(r=16, ...))

# Train
trainer = DPOTrainer(policy_model, ref_model, beta=0.1)
for batch in dataloader:
    loss, accuracy = trainer.train_step(batch)
    loss.backward()
    optimizer.step()
```

---

## 📊 Fine-Tuning Data

### Instruction Format
```python
# Standard instruction tuning format
INSTRUCTION_FORMAT = """\
### Instruction:
{instruction}

### Input:
{input}

### Response:
{response}
"""

# Example
format_instruction(
    instruction="Translate to French",
    input="Hello, how are you?",
    response="Bonjour, comment allez-vous?"
)

# Alpaca format (common)
ALPACA_FORMAT = """\
Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{response}
"""

# ShareGPT format (multi-turn conversations)
SHAREGPT_FORMAT = [
    {"from": "human", "value": "Hello!"},
    {"from": "gpt", "value": "Hi! How can I help you today?"},
    {"from": "human", "value": "What's the capital of France?"},
    {"from": "gpt", "value": "The capital of France is Paris."},
]
```

### Preference Data Format
```python
# DPO preference format
PREFERENCE_FORMAT = {
    "prompt": "What is the capital of France?",
    "chosen": "The capital of France is Paris. It's known for the Eiffel Tower, the Louvre Museum, and its rich history.",
    "rejected": "Paris.",
}

# Collecting preference data
# 1. Generate multiple responses
# 2. Rank by quality (human or AI)
# 3. Use (chosen, rejected) pairs for training

# Human ranking
def collect_human_preferences(prompt, responses):
    """
    Have humans rank responses

    Returns: (best_response, worst_response)
    """
    # Show each response to human raters
    # Collect rankings
    # Return top and bottom
    pass

# AI ranking (for bootstrapping)
def collect_ai_preferences(prompt, responses, judge_model):
    """
    Use AI model to rank responses

    Returns: (best_response, worst_response)
    """
    scores = []
    for response in responses:
        # Use judge model to score response
        score = judge_model.score(prompt, response)
        scores.append(score)

    # Return best and worst
    best_idx = max(range(len(scores)), key=lambda i: scores[i])
    worst_idx = min(range(len(scores)), key=lambda i: scores[i])

    return responses[best_idx], responses[worst_idx]
```

---

## 🔬 Training Hyperparameters

### LoRA Hyperparameters
```python
LORA_HYPERPARAMETERS = {
    "rank": {
        "description": "Rank of LoRA decomposition",
        "typical_values": [8, 16, 32, 64],
        "effect": "Higher rank = more capacity, more memory",
        "recommendation": "Start with 16, increase if underfitting",
    },
    "alpha": {
        "description": "Scaling factor",
        "typical_values": [16, 32, 64],
        "effect": "Typically 2x rank",
        "recommendation": "Set to 2x rank",
    },
    "dropout": {
        "description": "Dropout rate for LoRA layers",
        "typical_values": [0.0, 0.05, 0.1],
        "effect": "Higher = more regularization",
        "recommendation": "0.05 for most cases",
    },
    "target_modules": {
        "description": "Which modules to apply LoRA",
        "typical_values": [
            ["q_proj", "v_proj"],  # Minimal
            ["q_proj", "k_proj", "v_proj", "o_proj"],  # Full attention
            ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],  # All linear
        ],
        "effect": "More modules = more capacity, more memory",
        "recommendation": "Start with attention only",
    },
}
```

### Training Hyperparameters
```python
TRAINING_HYPERPARAMETERS = {
    "learning_rate": {
        "description": "Learning rate for LoRA parameters",
        "typical_values": [1e-5, 2e-5, 5e-5, 1e-4],
        "recommendation": "2e-4 for full fine-tuning, 1e-4 for LoRA",
    },
    "batch_size": {
        "description": "Per-device batch size",
        "typical_values": [1, 2, 4, 8],
        "effect": "Larger = more stable, more memory",
        "recommendation": "Use gradient accumulation if memory limited",
    },
    "gradient_accumulation_steps": {
        "description": "Steps to accumulate before optimizer update",
        "typical_values": [1, 2, 4, 8, 16],
        "effect": "Effective batch size = batch_size * grad_accum",
        "recommendation": "Set to achieve effective batch size of 32-128",
    },
    "num_epochs": {
        "description": "Number of training epochs",
        "typical_values": [1, 2, 3, 5, 10],
        "effect": "More epochs = better fit, risk of overfitting",
        "recommendation": "1-3 epochs for instruction tuning, 3-5 for DPO",
    },
    "warmup_steps": {
        "description": "Learning rate warmup steps",
        "typical_values": [100, 500, 1000],
        "effect": "Stabilizes early training",
        "recommendation": "5-10% of total steps",
    },
    "max_seq_length": {
        "description": "Maximum sequence length",
        "typical_values": [512, 1024, 2048, 4096],
        "effect": "Longer = more context, more memory",
        "recommendation": "Match your use case, 1024-2048 typical",
    },
}
```

---

## 🎯 Volume 5 Checklist

- [ ] Understand LoRA concept
- [ ] Implement LoRA layer
- [ ] Apply LoRA to model with PEFT
- [ ] Use QLoRA for memory efficiency
- [ ] Understand DPO algorithm
- [ ] Implement DPO trainer
- [ ] Format instruction data
- [ ] Create preference datasets
- [ ] Tune hyperparameters

---

## 🚀 Next Steps

1. Complete LAB-003: LoRA Fine-Tuning
2. Complete LAB-005: DPO Alignment
3. Read 5301-Knowledge-Distillation.md
4. Practice with different datasets

---

**Last Updated:** 2026-02-04
**Volume:** 5 - Fine-Tuning Expert
**Estimated Time:** 35-40 hours
