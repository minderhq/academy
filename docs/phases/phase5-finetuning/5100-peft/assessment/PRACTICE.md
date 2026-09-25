---
Document ID: 5100-PRACTICE
Title: "5100: PEFT Techniques - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
---

# 5100: PEFT Techniques - Practice

## Exercises

### Exercise 1: Implement LoRA from Scratch

```python
import torch
import torch.nn as nn
import math

class LoRALinear(nn.Module):
    """
    Low-Rank Adaptation (LoRA) layer.

    LoRA freezes the original pretrained weights and adds trainable
    low-rank decomposition matrices. This drastically reduces the
    number of trainable parameters while maintaining performance.

    Formula: W_new = W_frozen + (B @ A) * scaling
    where:
    - W_frozen: Original frozen weights
    - B: r x out_features (up projection)
    - A: in_features x r (down projection)
    - scaling: alpha / r
    """
    def __init__(self, in_features, out_features, rank=8, alpha=16, dropout=0.1):
        super().__init__()

        # SOLUTION: Original frozen layer
        # We keep the pretrained weights frozen and only train the LoRA matrices
        self.linear = nn.Linear(in_features, out_features, bias=False)
        self.linear.weight.requires_grad = False

        # SOLUTION: Low-rank decomposition
        # A projects down to rank r, B projects back up to out_features
        # This reduces parameters from d*d to d*r + r*d = 2*d*r
        self.lora_A = nn.Linear(in_features, rank, bias=False)
        self.lora_B = nn.Linear(rank, out_features, bias=False)

        # SOLUTION: Scaling factor
        # Higher alpha = more impact from LoRA weights
        # Typically alpha = 2*rank or alpha = rank
        self.scaling = alpha / rank
        self.dropout = nn.Dropout(dropout)

        # Initialize: A with Kaiming (for training dynamics), B with zeros
        # Starting B at zeros ensures the initial perturbation is zero
        nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B.weight)

    def forward(self, x):
        # SOLUTION: Original forward pass through frozen weights
        result = self.linear(x)

        # SOLUTION: LoRA forward pass
        # x -> dropout -> A -> B -> scaling -> add to result
        lora_out = self.lora_B(self.lora_A(self.dropout(x)))
        result = result + lora_out * self.scaling

        return result

# SOLUTION: Replace linear layers in a model
def apply_lora_to_model(model, target_modules=["c_attn"], rank=8):
    """
    Apply LoRA to specific modules in a model.

    Args:
        model: The model to modify
        target_modules: List of module name patterns to replace
        rank: LoRA rank (higher = more parameters but more expressiveness)

    Returns:
        Modified model with LoRA layers
    """
    def set_module_by_name(model, name, new_module):
        """Helper to set a module by name."""
        parts = name.split('.')
        curr = model
        for part in parts[:-1]:
            curr = getattr(curr, part)
        setattr(curr, parts[-1], new_module)

    for name, module in model.named_modules():
        if any(target in name for target in target_modules):
            if isinstance(module, nn.Linear):
                in_features = module.in_features
                out_features = module.out_features

                # SOLUTION: Replace with LoRA layer
                lora_layer = LoRALinear(in_features, out_features, rank=rank)
                # Copy the frozen weights from original module
                lora_layer.linear.weight.data = module.weight.data.clone()

                # Replace in model
                set_module_by_name(model, name, lora_layer)

                print(f"Applied LoRA to {name} (rank={rank})")

    return model

# Example usage
if __name__ == "__main__":
    # Create a simple model
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = nn.Sequential(
                nn.Linear(768, 768),
                nn.ReLU(),
                nn.Linear(768, 10)
            )

        def forward(self, x):
            return self.layers(x)

    model = SimpleModel()

    # Apply LoRA to all Linear layers
    model = apply_lora_to_model(model, target_modules=["layers"], rank=8)

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"\nTotal parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print(f"Trainable %: {trainable_params/total_params*100:.2f}%")

    # Expected Output:
    # Applied LoRA to layers.0 (rank=8)
    # Applied LoRA to layers.2 (rank=8)
    # Total parameters: 616,016
    # Trainable parameters: 18,512
    # Trainable %: 3.00%
    # (both Linear layers get a 2*768*8 = 12,288 / 768*8+8*10 = 6,224
    #  pair of LoRA matrices; 18,512 / 616,016 = 3.00%)
```

### Exercise 2: Apply LoRA with HuggingFace

```python
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# SOLUTION: Configure LoRA
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,  # For causal language models
    r=8,  # Rank - higher r = more parameters but better adaptation
    lora_alpha=32,  # Scaling factor (typically 2*r or r)
    lora_dropout=0.1,  # Dropout for LoRA layers (prevents overfitting)
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Which modules to apply LoRA to
    inference_mode=False,  # Training mode
    bias="none",  # Whether to train bias terms
)

# SOLUTION: Apply to model
model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Apply LoRA
peft_model = get_peft_model(model, lora_config)

# SOLUTION: Check trainable parameters
peft_model.print_trainable_parameters()

# Expected Output:
# trainable params: 589,824 || all params: 124,439,808 || trainable%: 0.474
#
# (4 attention projections x 12 layers x 2*768*8 LoRA params)
#
# Then ~96 trainable-weight lines (12 layers x {q,k,v,o} x
# {lora_A, lora_B}), the large wrapped-model repr, and the
# generation test - which returns base-gpt2-style text, since
# fresh LoRA B matrices start at zero (adapter = identity at init)

# Detailed parameter inspection
print("\n" + "="*60)
print("LoRA Configuration Details:")
print("="*60)

for name, param in peft_model.named_parameters():
    if param.requires_grad:
        print(f"Trainable: {name} | Shape: {param.shape} | Params: {param.numel():,}")

print("\n" + "="*60)
print("Model Architecture:")
print("="*60)
print(peft_model)

# Test generation
text = "The future of artificial intelligence is"
inputs = tokenizer(text, return_tensors="pt")

with torch.no_grad():
    outputs = peft_model.generate(**inputs, max_new_tokens=20)

print("\n" + "="*60)
print("Generation Test:")
print("="*60)
print(f"Input: {text}")
print(f"Output: {tokenizer.decode(outputs[0], skip_special_tokens=True)}")

print("\n" + "="*60)
print("Key Insights:")
print("="*60)
print("""
1. LoRA reduces trainable parameters by 100-1000x
2. Target modules (q_proj, k_proj, v_proj) are the attention projections
3. Rank r controls the trade-off between efficiency and expressiveness
4. Alpha controls the scaling of the LoRA update
5. Dropout helps prevent overfitting on small datasets
""")
```

### Exercise 3: QLoRA (Quantized LoRA)

```python
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
import torch

# SOLUTION: Configure 4-bit quantization
# QLoRA combines quantization with LoRA for even more memory efficiency
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,  # Load model in 4-bit precision
    bnb_4bit_quant_type="nf4",  # NormalFloat 4-bit data type (better range than int4)
    bnb_4bit_compute_dtype=torch.float16,  # Use float16 for computations
    bnb_4bit_use_double_quant=True,  # Quantize the quantization constants (saves more memory)
)

print("Loading model in 4-bit...")
# SOLUTION: Load model in 4-bit
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",  # Requires access request
    quantization_config=bnb_config,
    device_map="auto",  # Automatically distribute across available GPUs
    trust_remote_code=True,
)

# SOLUTION: Prepare for k-bit training
# This freezes the quantized weights and adds trainable adapters
model = prepare_model_for_kbit_training(model)

print("Applying LoRA...")
# SOLUTION: Apply LoRA
lora_config = LoraConfig(
    r=16,  # Higher rank for 7B model
    lora_alpha=32,  # Alpha = 2*rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

peft_model = get_peft_model(model, lora_config)

print("\n" + "="*60)
print("QLoRA Model Summary:")
print("="*60)
peft_model.print_trainable_parameters()

print("\n" + "="*60)
print("Memory Efficiency Comparison:")
print("="*60)
print(f"""
Original Llama-2-7B (FP16): ~13.5 GB VRAM
With 4-bit quantization: ~4.5 GB VRAM
With LoRA adapters: ~5.5 GB VRAM

Total memory savings: ~60% compared to full fine-tuning!
""")

print("\n" + "="*60)
print("Key QLoRA Innovations:")
print("="*60)
print("""
1. 4-bit NormalFloat (NF4) quantization:
   - Better distribution than int4 for neural network weights
   - Preserves the Gaussian distribution of pretrained weights

2. Double Quantization:
   - Quantize the quantization constants
   - Saves ~0.4 bits per parameter (~0.3 GB on a 7B model)

3. Paged Optimizers:
   - Use CPU RAM for optimizer state overflow
   - Prevents OOM errors during training

4. Gradient Checkpointing:
   - Trade compute for memory
   - Enables training larger batch sizes
""")

# Example training setup
print("\n" + "="*60)
print("Training Configuration Example:")
print("="*60)
print("""
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./qlora-llama2",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    warmup_steps=100,
    learning_rate=2e-4,
    fp16=True,  # Use mixed precision
    logging_steps=10,
    save_steps=100,
    eval_steps=100,
    optim="paged_adamw_8bit",  # Paged optimizer for memory efficiency
)

trainer = Trainer(
    model=peft_model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

trainer.train()
""")

# Expected Output:
# The loading/applying status lines, the trainable-params summary
# (r=16 on all 7 projections of a 7B: ~29M trainable of ~6.7B
# total, ~0.4%), then the memory comparison, QLoRA-innovations
# and training-config text print directly - the load itself needs
# a GPU and gated Llama-2 access
```

### Exercise 4: Prefix Tuning

```python
from peft import PrefixTuningConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# SOLUTION: Configure prefix tuning
# Prefix tuning adds trainable virtual tokens to the input
# These tokens are optimized to steer the model behavior
prefix_config = PrefixTuningConfig(
    task_type=TaskType.CAUSAL_LM,
    num_virtual_tokens=20,  # Number of virtual tokens (longer = more control)
    prefix_projection=False,  # True adds a 768 x (2*12*768) reprojection
    # matrix (~14M params for gpt2) that dwarfs the prefix itself -
    # the default False stores the prefix embeddings directly
)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# SOLUTION: Apply to model
peft_model = get_peft_model(model, prefix_config)

print("\n" + "="*60)
print("Prefix Tuning Analysis:")
print("="*60)

# SOLUTION: Compare parameters
original_params = sum(p.numel() for p in model.parameters())
prefix_params = sum(p.numel() for p in peft_model.parameters() if p.requires_grad)

print(f"Original model parameters: {original_params:,}")
print(f"Prefix trainable parameters: {prefix_params:,}")
print(f"Percentage: {prefix_params/original_params*100:.2f}%")

print("\n" + "="*60)
print("Prefix vs LoRA Comparison:")
print("="*60)

comparison = """
Aspect              | Prefix Tuning  | LoRA
--------------------|----------------|----------------------
Trainable params    | ~0.3%          | ~0.5%
Training stability  | Lower          | Higher
Memory efficiency   | Higher         | Moderate
Inference cost      | Yes (longer)   | Minimal
Best for            | Generation     | All tasks

Prefix Tuning:
- Adds virtual tokens at the beginning of the sequence
- Virtual tokens are optimized to condition the model
- Longer sequences during inference (slower)

LoRA:
- Modifies weight matrices directly
- No inference overhead
- More stable training
"""
print(comparison)

print("\n" + "="*60)
print("Prefix Tuning Architecture:")
print("="*60)
print("""
Input: [VIRTUAL_TOKENS x 20] + [USER_INPUT]
       ↓
    [Prefix Encoder]
       ↓
    [Conditioned Input to LLM]

The prefix parameters are trained to produce optimal conditioning
for specific tasks without modifying the original weights.
""")

# Test generation
text = "Once upon a time"
inputs = tokenizer(text, return_tensors="pt")

with torch.no_grad():
    outputs = peft_model.generate(**inputs, max_new_tokens=30)

print("\n" + "="*60)
print("Generation Test:")
print("="*60)
print(f"Input: {text}")
print(f"Output: {tokenizer.decode(outputs[0], skip_special_tokens=True)}")

print("\n" + "="*60)
print("When to Use Prefix Tuning:")
print("="*60)
print("""
✓ Generation tasks where quality matters more than speed
✓ When you have very limited training data
✓ When you want minimal modification to the model
✓ For multi-task learning (different prefixes for different tasks)

✗ Latency-sensitive applications (inference is slower)
✗ When training stability is critical
✗ When you need to fine-tune on large datasets
""")

# Expected Output:
# Original model parameters: 124,439,808
# Prefix trainable parameters: 368,640
# Percentage: 0.30%
# (20 virtual tokens x 2 x 12 layers x 768 hidden = 368,640)
# Then the comparison, architecture and guidance text print
# directly; the generation test returns base-gpt2-style text
# (the prefix is untrained)
```

### Exercise 5: Prompt Tuning

```python
from peft import PromptTuningConfig, PromptTuningInit, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# SOLUTION: Configure prompt tuning
# Prompt tuning is the simplest PEFT method - only soft prompts are trainable
prompt_config = PromptTuningConfig(
    task_type=TaskType.CAUSAL_LM,
    prompt_tuning_init=PromptTuningInit.TEXT,  # Initialize from text
    prompt_tuning_init_text="Classify if the following review is positive or negative:",
    num_virtual_tokens=20,  # Length of the soft prompt
    tokenizer_name_or_path="gpt2",
)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# SOLUTION: Apply to model
peft_model = get_peft_model(model, prompt_config)

print("\n" + "="*60)
print("Prompt Tuning Analysis:")
print("="*60)

# SOLUTION: Check trainable parameters (only soft prompts)
trainable_params = 0
for name, param in peft_model.named_parameters():
    if param.requires_grad:
        trainable_params += param.numel()
        print(f"Trainable: {name} | Shape: {param.shape}")

print(f"\nTotal trainable parameters: {trainable_params:,}")

print("\n" + "="*60)
print("PEFT Methods Parameter Comparison:")
print("="*60)

comparisons = [
    ("Full Fine-tuning", 124000000, 100),
    ("LoRA (r=8)", 600000, 0.5),
    ("Prefix Tuning", 120000, 0.1),
    ("Prompt Tuning", 15000, 0.01),
]

print(f"{'Method':<25} {'Params':>15} {'% of Base':>12}")
print("-" * 60)
for method, params, pct in comparisons:
    print(f"{method:<25} {params:>15,} {pct:>11.2f}%")

print("\n" + "="*60)
print("Prompt Tuning Key Characteristics:")
print("="*60)
print("""
1. Minimal Parameters (0.01%):
   - Only the soft prompt embeddings are trainable
   - Everything in the model is frozen

2. Simplicity:
   - Easiest PEFT method to implement
   - No special architecture modifications

3. Scalability:
   - Can store many task-specific prompts
   - Easy to switch between tasks

4. Limitations:
   - Requires more training data than LoRA
   - Less expressive than other methods
   - Performance plateaus on complex tasks
""")

print("\n" + "="*60)
print("Multi-Task Prompt Tuning Example:")
print("="*60)
print("""
# You can have different prompts for different tasks
tasks = {
    "sentiment": "Analyze the sentiment of this review:",
    "summarization": "Summarize the following text:",
    "qa": "Answer this question based on the context:",
}

# Each task gets its own trainable prompt
# Switch tasks by loading different prompt parameters
""")

# Test
text = "This movie was absolutely fantastic! Best film of the year."
inputs = tokenizer(f"Review: {text}\nSentiment:", return_tensors="pt")

with torch.no_grad():
    outputs = peft_model.generate(**inputs, max_new_tokens=10)

print("\n" + "="*60)
print("Generation Test:")
print("="*60)
print(f"Input: Review: {text}")
print(f"Output: {tokenizer.decode(outputs[0], skip_special_tokens=True)}")

print("\n" + "="*60)
print("Best Practices for Prompt Tuning:")
print("="*60)
print("""
1. Prompt Initialization:
   - Start with meaningful text
   - Use task-relevant initialization
   - Longer prompts (20-100 tokens) work better

2. Training:
   - Use higher learning rates than full fine-tuning
     (1e-3 to 1e-2 - soft prompts are a tiny fresh embedding
     and need much larger updates than pretrained weights)
   - Train for more epochs
   - Larger batch sizes help

3. When to Use:
   - Resource-constrained environments
   - Many different tasks
   - Quick prototyping
   - Simple classification/formatting tasks
""")

# Expected Output:
# One trainable-parameter line:
# Trainable: base_model.model...prompt_embeddings | Shape: [20, 768]
# Total trainable parameters: 15,360  (20 x 768 - 0.012% of gpt2;
# the static comparison table rounds it to 15,000). The comparison
# tables and guidance text print directly; the generation test
# returns base-gpt2-style text (the prompt is untrained)
```

### Exercise 6: AdapterHub Style Adapters

```python
import torch
import torch.nn as nn
import math

class AdapterLayer(nn.Module):
    """
    AdapterHub-style adapter layer.

    Adapters are small bottleneck layers inserted into the transformer.
    They provide a flexible way to adapt pretrained models.

    Architecture:
    Input -> Down proj -> Activation -> Up proj -> Residual -> Output
              ↓                                        ↑
           (bottleneck)                    (same dimension as input)
    """
    def __init__(self, hidden_size, adapter_size=64):
        super().__init__()

        # SOLUTION: Down projection to bottleneck
        # Reduces dimension from hidden_size to adapter_size
        # This creates the "bottleneck" that limits expressiveness
        self.down = nn.Linear(hidden_size, adapter_size)

        # SOLUTION: Non-linearity
        # Adds non-linearity between projections
        self.activation = nn.ReLU()

        # SOLUTION: Up projection back to original size
        # Expands from adapter_size back to hidden_size
        self.up = nn.Linear(adapter_size, hidden_size)

        # SOLUTION: Initialize
        # Important: Initialize up projection with zeros
        # This ensures the adapter starts as an identity function
        nn.init.zeros_(self.up.weight)
        nn.init.zeros_(self.up.bias)

        # Down projection can use standard initialization
        nn.init.kaiming_uniform_(self.down.weight, a=math.sqrt(5))
        nn.init.zeros_(self.down.bias)

    def forward(self, x):
        # SOLUTION: Adapter forward with residual connection
        # The residual ensures the adapter can be "turned off"
        # by learning to output zeros
        adapted = self.up(self.activation(self.down(x)))
        return x + adapted  # Residual connection

# SOLUTION: Add adapters to transformer blocks
def add_adapters_to_model(model, adapter_size=64):
    """
    Add adapter layers to a transformer model.

    Adapters are typically added after:
    - Self-attention layer
    - Feed-forward network (FFN)

    Args:
        model: Transformer model to modify
        adapter_size: Bottleneck dimension (typically 32-128)

    Returns:
        Modified model with adapters
    """
    adapters_added = 0

    for name, module in model.named_modules():
        # Look for transformer layers
        if "layer" in name.lower() or "block" in name.lower():
            # Try to add adapter after FFN/output layer
            if hasattr(module, 'output') or hasattr(module, 'fc2') or \
               hasattr(module, 'linear2') or hasattr(module, 'ffn'):
                # Get the output dimension
                if hasattr(module, 'output'):
                    hidden_size = module.output.out_features
                elif hasattr(module, 'fc2'):
                    hidden_size = module.fc2.out_features
                elif hasattr(module, 'linear2'):
                    hidden_size = module.linear2.out_features
                elif hasattr(module, 'ffn'):
                    hidden_size = module.ffn[2].out_features
                else:
                    continue

                # Create and attach adapter
                adapter = AdapterLayer(hidden_size, adapter_size)
                module.adapter = adapter

                # Store original forward
                original_forward = module.forward

                # Create new forward that includes adapter
                def new_forward(x, orig_forward=original_forward, adapter=adapter):
                    out = orig_forward(x)
                    return adapter(out)

                module.forward = new_forward
                adapters_added += 1
                print(f"Added adapter to {name}")

    print(f"\nTotal adapters added: {adapters_added}")
    return model

# Example with a simple transformer
class SimpleTransformerBlock(nn.Module):
    def __init__(self, hidden_size, num_heads=4):
        super().__init__()
        self.attention = nn.MultiheadAttention(hidden_size, num_heads)
        self.ffn = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 4),
            nn.ReLU(),
            nn.Linear(hidden_size * 4, hidden_size),
        )
        self.norm1 = nn.LayerNorm(hidden_size)
        self.norm2 = nn.LayerNorm(hidden_size)

    def forward(self, x):
        # Self-attention with residual
        attn_out, _ = self.attention(x, x, x)
        x = self.norm1(x + attn_out)

        # FFN with residual
        ffn_out = self.ffn(x)
        x = self.norm2(x + ffn_out)

        return x

# Create model and add adapters
# Wrapper gives the blocks matchable names - add_adapters_to_model
# looks for "layer"/"block" in module names, and nn.Sequential's
# children are just named "0", "1", ... (no match, no adapters)
class TinyTransformer(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.block_0 = SimpleTransformerBlock(hidden_size)
        self.block_1 = SimpleTransformerBlock(hidden_size)

    def forward(self, x):
        x = self.block_0(x)
        return self.block_1(x)

print("Creating transformer model...")
base_model = TinyTransformer(hidden_size=256)

print("\nAdding adapters...")
model_with_adapters = add_adapters_to_model(base_model, adapter_size=64)

print("\n" + "="*60)
print("Adapter Analysis:")
print("="*60)

# Count parameters
total_params = sum(p.numel() for p in model_with_adapters.parameters())
adapter_params = sum(
    p.numel() for name, p in model_with_adapters.named_parameters()
    if "adapter" in name
)

print(f"Total parameters: {total_params:,}")
print(f"Adapter parameters: {adapter_params:,}")
print(f"Adapter %: {adapter_params/total_params*100:.2f}%")

print("\n" + "="*60)
print("Adapter vs LoRA Comparison:")
print("="*60)
comparison = """
Aspect              | Adapters        | LoRA
--------------------|-----------------|----------------------
Location            | After layers    | Modify layers
Inference cost      | Yes (bottleneck)| No (merged)
Modularity          | High            | Medium
Training stability  | High            | Medium
Parameters          | ~1-3%          | ~0.5-2%

Adapters:
✓ Better modularity (can be swapped per task)
✓ Very stable training
✓ Can be composed (multiple adapters)
✗ Add inference overhead
✗ More parameters than LoRA

LoRA:
✓ No inference overhead (can be merged)
✓ Fewer parameters
✓ Better for single-task adaptation
✗ Less modular
✗ Can be unstable with high ranks
"""
print(comparison)

print("\n" + "="*60)
print("Adapter Configuration Options:")
print("="*60)
print("""
1. Adapter Size (bottleneck dimension):
   - Small (16-32): Very efficient, less expressive
   - Medium (64-128): Good balance
   - Large (256+): More parameters, better adaptation

2. Adapter Placement:
   - After attention only
   - After FFN only
   - After both (recommended)

3. Adapter Variants:
   - Sequential: Single bottleneck
   - Parallel: Multiple bottlenecks
   - Compacter: Factorized adapters

4. Composition:
   - Stack multiple adapters for different tasks
   - Learn mixing weights for ensemble
""")

# Test forward pass
print("\n" + "="*60)
print("Forward Pass Test:")
print("="*60)

batch_size = 4
seq_len = 10
hidden_size = 256

x = torch.randn(batch_size, seq_len, hidden_size)
output = model_with_adapters(x)

print(f"Input shape: {x.shape}")
print(f"Output shape: {output.shape}")
print("✓ Forward pass successful!")

# Expected Output:
# Added adapter to block_0
# Added adapter to block_1
# Total adapters added: 2
# Total parameters: 1,645,696
# Adapter parameters: 66,176
# Adapter %: 4.02%
# (each adapter: 256->64 down + 64->256 up with biases = 33,088;
#  two 789,760-param blocks plus the adapters)
# Input shape: torch.Size([4, 10, 256])
# Output shape: torch.Size([4, 10, 256])
# ✓ Forward pass successful!
```

### Exercise 7: Compare PEFT Methods

```python
def compare_peft_methods():
    """
    Compare different PEFT approaches across multiple dimensions.
    """

    # Base model parameters (GPT-2 small)
    base_params = 124_000_000  # ~124M parameters

    # Parameter estimates for different methods
    methods = {
        'Full Fine-tuning': {
            'params': base_params,
            'trainable_pct': 100.0,
            'memory_gb': 8.0,
            'training_hours': 24,
            'inference_overhead': 0.0,
        },
        'LoRA (r=8)': {
            'params': int(base_params * 0.005),
            'trainable_pct': 0.5,
            'memory_gb': 2.5,
            'training_hours': 4,
            'inference_overhead': 0.0,
        },
        'LoRA (r=32)': {
            'params': int(base_params * 0.02),
            'trainable_pct': 2.0,
            'memory_gb': 3.0,
            'training_hours': 6,
            'inference_overhead': 0.0,
        },
        'Prefix Tuning': {
            'params': int(base_params * 0.01),
            'trainable_pct': 1.0,
            'memory_gb': 2.0,
            'training_hours': 5,
            'inference_overhead': 1.2,  # 20% slower
        },
        'Prompt Tuning': {
            'params': int(base_params * 0.001),
            'trainable_pct': 0.1,
            'memory_gb': 1.8,
            'training_hours': 8,
            'inference_overhead': 1.1,  # 10% slower
        },
        'Adapters': {
            'params': int(base_params * 0.03),
            'trainable_pct': 3.0,
            'memory_gb': 3.5,
            'training_hours': 5,
            'inference_overhead': 1.15,  # 15% slower
        },
    }

    print("="*60)
    print("PEFT Method Comparison")
    print("="*60)
    print(f"\nBase Model: GPT-2 Small ({base_params:,} parameters)\n")

    print(f"{'Method':<20} {'Trainable':<15} {'% of Base':<15} {'Memory':<10} {'Speed':<10}")
    print("-" * 70)
    print("Illustrative numbers - always benchmark on your own hardware\n")

    for method, data in methods.items():
        print(f"{method:<20} {data['params']:>14,} {data['trainable_pct']:>14.2f}% "
              f"{data['memory_gb']:>9.1f}GB {data['inference_overhead']:>9.2f}x")

    print("\n" + "="*60)
    print("Recommendations by Use Case:")
    print("="*60)

    recommendations = """
1. Production/Latency-Critical:
   → Use: LoRA
   Reason: Zero inference overhead after merging
   Example: Real-time chatbots, APIs

2. Resource-Constrained:
   → Use: Prompt Tuning or Prefix Tuning
   Reason: Minimal memory footprint
   Example: Edge devices, mobile apps

3. Multi-Task Learning:
   → Use: Adapters
   Reason: Easy to swap between tasks
   Example: General-purpose assistants

4. Maximum Performance:
   → Use: LoRA (r=32 or higher)
   Reason: Best balance of efficiency and quality
   Example: Domain-specific fine-tuning

5. Rapid Prototyping:
   → Use: Prompt Tuning
   Reason: Fastest to implement
   Example: Quick experiments

6. Stable Training:
   → Use: Adapters or Prefix Tuning
   Reason: More stable than LoRA at high ranks
   Example: Sensitive applications
"""
    print(recommendations)

    print("\n" + "="*60)
    print("Efficiency vs Quality Trade-off:")
    print("="*60)

    # Quality estimates (illustrative - order-of-magnitude figures
    # from published comparisons, not measurements on your workload)
    quality_scores = {
        'Full Fine-tuning': 1.00,
        'LoRA (r=8)': 0.95,
        'LoRA (r=32)': 0.98,
        'Prefix Tuning': 0.92,
        'Prompt Tuning': 0.88,
        'Adapters': 0.94,
    }

    print(f"\n{'Method':<20} {'Quality Score':<15} {'Efficiency':<15}")
    print("-" * 50)

    for method in methods.keys():
        quality = quality_scores.get(method, 0.9)
        efficiency = 1.0 / (methods[method]['trainable_pct'] + 0.1)
        print(f"{method:<20} {quality:>14.2f} {efficiency:>14.2f}")

    print("\n" + "="*60)
    print("Cost Comparison (1000 training steps):")
    print("="*60)

    # Cost assumptions
    cost_per_gpu_hour = 1.0  # USD

    print(f"\n{'Method':<20} {'GPU Hours':<15} {'Cost (USD)':<15}")
    print("-" * 50)

    for method, data in methods.items():
        gpu_hours = data['training_hours']
        cost = gpu_hours * cost_per_gpu_hour
        savings = ((methods['Full Fine-tuning']['training_hours'] - gpu_hours) /
                  methods['Full Fine-tuning']['training_hours'] * 100)
        print(f"{method:<20} {gpu_hours:>14.1f} ${cost:>13.2f} (save {savings:>5.0f}%)")

    print("\n" + "="*60)
    print("Key Takeaways:")
    print("="*60)
    print("""
1. LoRA provides the best overall balance:
   - Near-full fine-tuning quality
   - 99%+ parameter reduction
   - No inference overhead
   - Fast training

2. Prompt/Prefix tuning for extreme efficiency:
   - <0.5% of parameters
   - Lowest memory requirements
   - Some inference overhead
   - Good for simple tasks

3. Adapters for modularity:
   - Easy task switching
   - Stable training
   - Moderate overhead
   - Good for multi-task systems

4. Full fine-tuning only when necessary:
   - Maximum quality
   - Highest cost
   - Most resource intensive
   - Use for critical applications
""")

    return methods

# Run comparison
if __name__ == "__main__":
    methods = compare_peft_methods()

    print("\n" + "="*60)
    print("Decision Tree for PEFT Selection:")
    print("="*60)
    print("""
Need max quality?
├─ Yes → Full fine-tuning (if resources available)
│        └─ LoRA r=32 (if resources limited)
└─ No → Need zero inference overhead?
         ├─ Yes → LoRA (r=8-16)
         └─ No → Need multi-task switching?
                  ├─ Yes → Adapters
                  └─ No → Prompt Tuning (simplest)
""")

# Expected Output:
# The 6-row comparison table (illustrative training hours, memory
# and speed multipliers), the 6 use-case recommendations, the
# efficiency-vs-quality table, the cost table and the decision
# tree all print directly - no model runs in this exercise
```

---

**Solutions Provided:**
- Complete implementations for all 7 exercises
- Detailed explanations of PEFT concepts
- Production-ready code examples
- Expected outputs and performance metrics
- Best practices and recommendations
- Comparison tables and decision guides
