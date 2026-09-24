# EXP_5201: DPO (Direct Preference Optimization) Experiments

## Overview
Practical experiments for DPO alignment on an 11GB VRAM GPU.

## Experiment 1: DPO Implementation from Scratch

### Objective
Implement DPO training loop from scratch.

### Implementation
```python
# dpo_implementation.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass
from typing import Optional

@dataclass
class DPOConfig:
    """DPO configuration"""
    learning_rate: float = 1e-5
    beta: float = 0.1  # DPO temperature parameter
    max_length: int = 512

class DPOTrainer:
    """
    Direct Preference Optimization trainer

    DPO Objective: max E[log(σ(β log(π_θ(y_w)/π_ref(y_w)) - β log(π_θ(y_l)/π_ref(y_l))))]
    """

    def __init__(self, model: nn.Module, ref_model: nn.Module, config: DPOConfig):
        self.model = model
        self.ref_model = ref_model
        self.config = config

        # Freeze reference model
        for param in self.ref_model.parameters():
            param.requires_grad = False

        self.ref_model.eval()

        # Optimizer
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)

    def compute_log_probs(self, model: nn.Module, input_ids: torch.Tensor, attention_mask: torch.Tensor):
        """Compute log probabilities"""
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=input_ids)
        logits = outputs.logits

        # Calculate log probs
        log_probs = F.log_softmax(logits, dim=-1)

        # Gather log probs for actual tokens
        token_log_probs = torch.gather(log_probs, 2, input_ids.unsqueeze(-1)).squeeze(-1)

        # Mask padding
        token_log_probs = token_log_probs * attention_mask

        return token_log_probs.sum(dim=-1)  # Sum over sequence length

    def dpo_loss(
        self,
        policy_chosen_logps: torch.Tensor,
        policy_rejected_logps: torch.Tensor,
        reference_chosen_logps: torch.Tensor,
        reference_rejected_logps: torch.Tensor,
    ) -> torch.Tensor:
        """
        Calculate DPO loss

        L = -log(σ(β (log π(y_w) - log π_ref(y_w)) - β (log π(y_l) - log π_ref(y_l))))
        """
        pi_logratios = policy_chosen_logps - policy_rejected_logps
        ref_logratios = reference_chosen_logps - reference_rejected_logps

        # DPO loss
        logits = self.config.beta * (pi_logratios - ref_logratios)
        loss = -F.logsigmoid(logits).mean()

        return loss

    def train_step(self, batch: dict) -> dict:
        """Single training step"""
        # Extract batch data
        chosen_input_ids = batch["chosen_input_ids"]
        chosen_attention_mask = batch["chosen_attention_mask"]
        rejected_input_ids = batch["rejected_input_ids"]
        rejected_attention_mask = batch["rejected_attention_mask"]

        # Compute policy log probs
        with torch.cuda.amp.autocast():
            policy_chosen_logps = self.compute_log_probs(
                self.model, chosen_input_ids, chosen_attention_mask
            )
            policy_rejected_logps = self.compute_log_probs(
                self.model, rejected_input_ids, rejected_attention_mask
            )

        # Compute reference log probs (no grad)
        with torch.no_grad():
            reference_chosen_logps = self.compute_log_probs(
                self.ref_model, chosen_input_ids, chosen_attention_mask
            )
            reference_rejected_logps = self.compute_log_probs(
                self.ref_model, rejected_input_ids, rejected_attention_mask
            )

        # Calculate loss
        loss = self.dpo_loss(
            policy_chosen_logps,
            policy_rejected_logps,
            reference_chosen_logps,
            reference_rejected_logps,
        )

        # Backward
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

        # Calculate metrics
        with torch.no_grad():
            chosen_logratios = policy_chosen_logps - reference_chosen_logps
            rejected_logratios = policy_rejected_logps - reference_rejected_logps

            # Accuracy: chosen should have higher log probs
            accuracy = (chosen_logratios > rejected_logratios).float().mean()

            # Average margin
            margin = (chosen_logratios - rejected_logratios).mean()

        return {
            "loss": loss.item(),
            "accuracy": accuracy.item(),
            "margin": margin.item(),
        }


def test_dpo_implementation():
    """Test DPO implementation"""

    print("Testing DPO Implementation")
    print("="*60)

    # Create dummy model
    class DummyModel(nn.Module):
        def __init__(self, vocab_size=1000, hidden_dim=128):
            super().__init__()
            self.embed = nn.Embedding(vocab_size, hidden_dim)
            self.lm_head = nn.Linear(hidden_dim, vocab_size)

        def forward(self, input_ids, attention_mask=None, labels=None):
            hidden = self.embed(input_ids)
            logits = self.lm_head(hidden)
            return type('obj', (object,), {'logits': logits})

    # Create models
    model = DummyModel()
    ref_model = DummyModel()

    # Create trainer
    config = DPOConfig(beta=0.1, learning_rate=1e-3)
    trainer = DPOTrainer(model, ref_model, config)

    # Create dummy batch
    batch_size = 4
    seq_len = 32

    batch = {
        "chosen_input_ids": torch.randint(0, 1000, (batch_size, seq_len)),
        "chosen_attention_mask": torch.ones(batch_size, seq_len),
        "rejected_input_ids": torch.randint(0, 1000, (batch_size, seq_len)),
        "rejected_attention_mask": torch.ones(batch_size, seq_len),
    }

    # Training step
    metrics = trainer.train_step(batch)

    print(f"Loss: {metrics['loss']:.4f}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Margin: {metrics['margin']:.4f}")


if __name__ == "__main__":
    test_dpo_implementation()
```

---

## Experiment 2: DPO vs PPO Comparison

### Objective
Compare DPO with PPO (the traditional RLHF approach).

### Comparison Table

| Aspect | PPO | DPO |
|--------|-----|-----|
| Complexity | High (actor-critic, value function) | Low (direct objective) |
| Training Time | 2-3x slower | Baseline |
| Memory | High (4 models) | Lower (2 models) |
| Stability | Needs careful tuning | More stable |
| Implementation | Complex | Simple |
| Sample Efficiency | Lower | Higher |

### Script
```python
# compare_dpo_ppo.py
"""
DPO vs PPO comparison on alignment tasks
"""

methods_comparison = {
    "PPO": {
        "models_needed": 4,  # policy, ref, value, reward
        "training_steps": 10000,
        "memory_gb": 20,
        "stability": "Medium",
    },
    "DPO": {
        "models_needed": 2,  # policy, ref
        "training_steps": 3000,
        "memory_gb": 8,
        "stability": "High",
    },
}
```

---

## Experiment 3: Preference Dataset Creation

### Objective
Create preference pairs from model outputs.

### Script
```python
# preference_dataset.py
from datasets import load_dataset, Dataset
from typing import List, Dict

def create_preference_pairs(
    prompts: List[str],
    model_a_outputs: List[str],
    model_b_outputs: List[str],
    human_preferences: List[int] = None,
) -> Dataset:
    """
    Create preference dataset

    Args:
        prompts: List of prompts
        model_a_outputs: Outputs from model A
        model_b_outputs: Outputs from model B
        human_preferences: 0 if A preferred, 1 if B preferred (optional)
    """

    data = []

    for i, prompt in enumerate(prompts):
        output_a = model_a_outputs[i]
        output_b = model_b_outputs[i]

        # If no human preference, use heuristics (e.g., longer, more coherent)
        if human_preferences is None:
            preference = 0 if len(output_a) > len(output_b) else 1
        else:
            preference = human_preferences[i]

        chosen = output_a if preference == 0 else output_b
        rejected = output_b if preference == 0 else output_a

        data.append({
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
        })

    return Dataset.from_list(data)


def create_synthetic_preferences():
    """Create synthetic preference pairs for testing"""

    from transformers import AutoTokenizer

    prompts = [
        "What is the capital of France?",
        "Explain quantum computing.",
        "Write a Python function.",
    ]

    # Simulated model outputs
    base_outputs = [
        "Paris is the capital of France.",
        "Quantum computing uses quantum mechanics for computation.",
        "def example(): pass",
    ]

    better_outputs = [
        "Paris is the capital and largest city of France. It is located on the Seine River.",
        "Quantum computing harnesses quantum phenomena like superposition and entanglement to process information in fundamentally new ways.",
        "def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
    ]

    # Create dataset
    dataset = create_preference_pairs(
        prompts=prompts,
        model_a_outputs=base_outputs,
        model_b_outputs=better_outputs,
        human_preferences=[1, 1, 1],  # Prefer model B
    )

    print(f"Created preference dataset with {len(dataset)} pairs")

    return dataset
```

---

## Experiment 4: DPO Training with QLoRA

### Objective
Train DPO with QLoRA for memory efficiency.

### Implementation
```python
# dpo_qlora.py
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from dpo_implementation import DPOTrainer, DPOConfig

def train_dpo_with_qlora():
    """Train DPO with QLoRA"""

    # Load models
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"

    # Policy model (with LoRA)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        load_in_4bit=True,
        device_map="auto",
    )

    # Reference model (4-bit, frozen)
    ref_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        load_in_4bit=True,
        device_map="auto",
    )

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # Apply LoRA to policy model only
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # DPO config
    dpo_config = DPOConfig(
        learning_rate=1e-4,
        beta=0.1,
        max_length=512,
    )

    # Create trainer
    trainer = DPOTrainer(model, ref_model, dpo_config)

    print("DPO with QLoRA trainer ready!")
    print(f"Trainable parameters: ~{sum(p.numel() for p in model.parameters() if p.requires_grad):,}")


if __name__ == "__main__":
    train_dpo_with_qlora()
```

---

## Expected Results (11GB VRAM GPU)

### Memory Usage

| Method | VRAM Required | Batch Size | Status |
|--------|---------------|------------|--------|
| DPO (full) | >20GB | 1 | OOM |
| DPO + QLoRA | ~6GB | 2 | ✓ |
| DPO + 4-bit | ~4GB | 4 | ✓ |

### Training Performance

| Configuration | Steps to Converge | Time/Step | Total Time |
|----------------|------------------|-----------|------------|
| DPO-7B (full) | 3000 | ~5s | ~4 hours |
| DPO-7B (QLoRA) | 3000 | ~3s | ~2.5 hours |
| DPO-7B (4-bit) | 3000 | ~4s | ~3.3 hours |

---

## Experiment Checklist

- [ ] DPO implementation from scratch
- [ ] Loss function verification
- [ ] Preference dataset creation
- [ ] Synthetic preference generation
- [ ] DPO vs PPO comparison
- [ ] QLoRA integration
- [ ] 4-bit quantization support
- [ ] Beta parameter sweep
- [ ] Accuracy metrics
- [ ] Margin calculation
- [ ] Model quality evaluation

---

## Related Documentation
- [5201: DPO Theory](../docs/5000-Fine-Tuning/5200-SFT-Preference/5201-DPO-Theory.md)
- [5202: Alignment Orchestration](../docs/5000-Fine-Tuning/5200-SFT-Preference/5202-Alignment-Orchestration.md)
- [5102: QLoRA Pipelines](../docs/5000-Fine-Tuning/5100-PEFT/5102-QLoRA-Pipelines.md)
- [5302: Distributed Training](../docs/5302-Distributed-Training.md)
