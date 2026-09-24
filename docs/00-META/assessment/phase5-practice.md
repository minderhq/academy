# Phase 5: Fine-Tuning Practice

## Hands-On Exercises

### Exercise 1: Implement LoRA from Scratch

```python
import torch
import torch.nn as nn

class LoRALayer(nn.Module):
    """LoRA (Low-Rank Adaptation) implementation"""

    def __init__(self, in_features, out_features, rank=8, alpha=16):
        super().__init__()
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank

        # Trainable low-rank matrices
        self.lora_A = nn.Parameter(torch.randn(rank, in_features) * 0.01)
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))

        # Freeze or not (handled externally)

    def forward(self, x):
        # LoRA forward: W + BA where B is (out, rank) and A is (rank, in)
        lora_output = x @ (self.lora_A @ self.lora_B).T * self.scaling
        return lora_output


class LoRALinear(nn.Module):
    """Linear layer with LoRA"""

    def __init__(self, in_features, out_features, rank=8, alpha=16):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=False)
        self.lora = LoRALayer(in_features, out_features, rank, alpha)

        # Freeze original weights
        self.linear.weight.requires_grad = False

    def forward(self, x):
        # Original + LoRA
        return self.linear(x) + self.lora(x)


def test_lora():
    print("=== LoRA Implementation Test ===")

    # Create LoRA layer
    lora_linear = LoRALinear(768, 768, rank=8, alpha=16)

    # Count trainable parameters
    total_params = sum(p.numel() for p in lora_linear.parameters())
    trainable_params = sum(p.numel() for p in lora_linear.parameters() if p.requires_grad)

    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print(f"Percentage: {trainable_params / total_params * 100:.2f}%")

    # Test forward pass
    x = torch.randn(2, 10, 768)
    output = lora_linear(x)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")

    print("✅ LoRA working!\n")


if __name__ == "__main__":
    test_lora()
```

### Exercise 2: QLoRA Training

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

def setup_qlora():
    """Setup QLoRA for fine-tuning"""

    print("=== QLoRA Setup ===")

    model_name = "mistralai/Mistral-7B-Instruct-v0.2"

    # QLoRA configuration
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    print("Loading 4-bit quantized model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # LoRA configuration
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("\n✅ QLoRA setup complete!\n")

    return model, lora_config


if __name__ == "__main__":
    setup_qlora()
```

### Exercise 3: DPO (Direct Preference Optimization)

```python
import torch
from transformers import AutoModelForCausalLM

class DPOTrainer:
    """Direct Preference Optimization trainer"""

    def __init__(self, model, ref_model, beta=0.1):
        self.model = model
        self.ref_model = ref_model
        self.beta = beta

    def dpo_loss(self, policy_chosen_logps, policy_rejected_logps,
                 ref_chosen_logps, ref_rejected_logps):
        """Calculate DPO loss"""

        # Policy log ratio
        pi_lograt = policy_chosen_logps - policy_rejected_logps
        ref_lograt = ref_chosen_logps - ref_rejected_logps

        # DPO loss
        losses = -torch.logsigmoid(self.beta * (pi_lograt - ref_lograt))

        return losses.mean()


def test_dpo():
    print("=== DPO Implementation Test ===")

    # Sample data
    policy_chosen_logps = torch.randn(10)
    policy_rejected_logps = torch.randn(10)
    ref_chosen_logps = torch.randn(10)
    ref_rejected_logps = torch.randn(10)

    # Calculate DPO loss
    dpo_trainer = DPOTrainer(None, None)
    loss = dpo_trainer.dpo_loss(
        policy_chosen_logps, policy_rejected_logps,
        ref_chosen_logps, ref_rejected_logps
    )

    print(f"DPO Loss: {loss.item():.4f}")
    print("✅ DPO working!\n")


if __name__ == "__main__":
    test_dpo()
```

---

## Completion Checklist

- [ ] LoRA implemented from scratch
- [ ] QLoRA configured and tested
- [ ] DPO loss calculated
- [ ] Fine-tuning loop implemented
- [ ] Memory usage optimized
- [ ] Training speed benchmarked

---

**Last Updated:** 2026-02-05
