---
Document ID: 2400-PRACTICE
Title: "2400: Pretraining - Practice"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'training', 'pretraining']
---

# 2400: Pretraining - Practice

## Exercises

### Exercise 1: Dataset Preparation

**Objective:** Load and prepare a dataset for language model pretraining.

**Solution:**

```python
from datasets import load_dataset
from transformers import AutoTokenizer
import torch
from torch.utils.data import Dataset

# Load dataset
print("Loading WikiText-2 dataset...")
# datasets 5.x: load by full hub URI - the bare "wikitext" alias no longer resolves
dataset = load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="train")

# Load tokenizer
print("Loading GPT-2 tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token

# Dataset statistics
print(f"\nDataset statistics:")
print(f"  Total samples: {len(dataset)}")
print(f"  Vocabulary size: {len(tokenizer)}")
# dataset[:1000] returns a dict of columns - iterating that yields the
# column NAME ("text", length 4), not the rows; slice the column first
print(f"  Max length: {max(len(text) for text in dataset['text'][:1000])}")

# Tokenization function
def tokenize_function(examples):
    """Tokenize a batch of examples."""
    # No return_tensors="pt" here: .map() wants per-example lists, and a
    # batched call returning one (batch, 512) tensor collapses the whole
    # batch into a single nested row. Ex2's Dataset wraps each item in
    # torch.tensor itself
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=512,
        padding="max_length"
    )

# Apply tokenization
print("\nTokenizing dataset...")
tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"],
    desc="Tokenizing"
)

print(f"Tokenized dataset size: {len(tokenized_dataset)}")

# Expected output:
# Dataset loaded with ~36k samples
# Vocabulary size: 50257 (GPT-2)
# Tokenized dataset ready for training

# Troubleshooting Tips:
# - If OOM errors: Reduce max_length or batch_size
# - If slow tokenization: Use batched=True and num_proc for parallel processing
# - If empty tokens: Filter out empty text samples before tokenization
```

### Exercise 2: Data Loading

**Objective:** Create a PyTorch DataLoader for pretraining.

**Solution:**

```python
import torch
from torch.utils.data import Dataset, DataLoader

class PretrainingDataset(Dataset):
    """Custom dataset for language model pretraining."""

    def __init__(self, tokenized_data):
        """
        Initialize dataset.

        Args:
            tokenized_data: Tokenized dataset from Hugging Face
        """
        self.data = tokenized_data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        """
        Get a single item.

        Args:
            idx: Index

        Returns:
            Dictionary with input_ids and attention_mask
        """
        item = self.data[idx]

        return {
            'input_ids': torch.tensor(item['input_ids'], dtype=torch.long),
            'attention_mask': torch.tensor(item['attention_mask'], dtype=torch.long)
        }

def create_dataloader(tokenized_dataset, batch_size=8, shuffle=True, num_workers=0):
    """
    Create DataLoader for pretraining.

    Args:
        tokenized_dataset: Tokenized dataset
        batch_size: Batch size
        shuffle: Whether to shuffle data
        num_workers: Number of worker processes

    Returns:
        DataLoader instance
    """
    dataset = PretrainingDataset(tokenized_dataset)

    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True
    )

    return dataloader

# Test the dataloader
print("=== Creating DataLoader ===\n")

dataloader = create_dataloader(tokenized_dataset, batch_size=4)

# Test iteration
print("Testing batch iteration...")
for i, batch in enumerate(dataloader):
    print(f"\nBatch {i+1}:")
    print(f"  Input IDs shape: {batch['input_ids'].shape}")
    print(f"  Attention mask shape: {batch['attention_mask'].shape}")
    print(f"  Sample input (first 10 tokens): {batch['input_ids'][0][:10].tolist()}")

    if i >= 2:  # Only show first 3 batches
        break

print(f"\n✓ DataLoader working correctly")
print(f"  Total batches per epoch: {len(dataloader)}")

# Expected output:
# Input IDs shape: torch.Size([4, 512])
# Attention mask shape: torch.Size([4, 512])
# Total batches: ~9000 (36000 / 4)

# Troubleshooting Tips:
# - If DataLoader is slow: Increase num_workers (but not > CPU cores)
# - If memory errors: Reduce batch_size
# - If hanging, set num_workers=0 to debug
```

### Exercise 3: Training Loop

**Objective:** Implement a complete training loop for language model pretraining.

**Solution:**

```python
import torch
from torch.optim import AdamW  # transformers.AdamW was deprecated (4.29) and has since been removed
from transformers import GPT2LMHeadModel, AutoConfig, get_linear_schedule_with_warmup
from tqdm import tqdm
import time

# Model configuration
print("=== Pretraining Setup ===\n")

config = AutoConfig.from_pretrained("gpt2")
config.n_embd = 128  # Smaller for testing
config.n_head = 4
config.n_layer = 4
config.vocab_size = len(tokenizer)

# Create model
print("Creating model...")
model = GPT2LMHeadModel(config)

# Device setup
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")
model = model.to(device)

# Optimizer setup
dataloader = create_dataloader(tokenized_dataset, batch_size=4)
num_epochs = 3
num_training_steps = len(dataloader) * num_epochs

optimizer = AdamW(model.parameters(), lr=1e-4)
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=100,
    num_training_steps=num_training_steps
)

print(f"\nTraining configuration:")
print(f"  Epochs: {num_epochs}")
print(f"  Batch size: 4")
print(f"  Total steps: {num_training_steps}")
print(f"  Learning rate: 1e-4")

# Training loop
print("\n=== Starting Training ===\n")

global_step = 0
for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    epoch_start_time = time.time()

    progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{num_epochs}")

    for batch_idx, batch in enumerate(progress_bar):
        # Move to device
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)

        # Forward pass (labels=input_ids for LM training)
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=input_ids
        )

        loss = outputs.loss
        total_loss += loss.item()

        # Backward pass
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()

        # Update progress bar
        global_step += 1
        progress_bar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'lr': f'{scheduler.get_last_lr()[0]:.2e}'
        })

        # Log every 100 steps
        if global_step % 100 == 0:
            avg_loss = total_loss / (batch_idx + 1)
            print(f"\nStep {global_step}: Avg Loss = {avg_loss:.4f}")

    # Epoch summary
    avg_loss = total_loss / len(dataloader)
    epoch_time = time.time() - epoch_start_time
    steps_per_sec = len(dataloader) / epoch_time

    print(f"\n{'='*60}")
    print(f"Epoch {epoch+1} Summary:")
    print(f"  Average Loss: {avg_loss:.4f}")
    print(f"  Time: {epoch_time:.1f}s ({steps_per_sec:.2f} steps/s)")
    print(f"{'='*60}\n")

print("\n✓ Training complete!")

# Expected output:
# Loss decreases over epochs
# A freshly initialized LM head starts at loss = ln(vocab) ~ 10.8;
# with this 4-layer/128-dim model expect epoch averages around ~7
# falling toward ~5-6 - exact numbers vary with seed and hardware
# Training speed: tens of steps/s on GPU, only a few on CPU

# Troubleshooting Tips:
# - If loss is NaN: Reduce learning rate or check gradient clipping
# - If loss increases: Check learning rate schedule and data quality
# - If slow training: Enable mixed precision (torch.amp, Exercise 6)
```

### Exercise 4: Checkpointing

**Objective:** Implement model checkpointing and resuming.

**Solution:**

```python
import json
from pathlib import Path

def save_checkpoint(model, optimizer, scheduler, epoch, loss, config, output_dir):
    """
    Save training checkpoint.

    Args:
        model: Model to save
        optimizer: Optimizer state
        scheduler: Scheduler state
        epoch: Current epoch
        loss: Current loss
        config: Training configuration
        output_dir: Output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    model_dir = output_dir / f"checkpoint-epoch-{epoch}"
    model.save_pretrained(model_dir)

    # Save training state
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
        'loss': loss,
        'config': config
    }

    torch.save(checkpoint, model_dir / "training_state.pt")

    # Save metadata
    metadata = {
        'epoch': epoch,
        'loss': float(loss),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    with open(model_dir / "metadata.json", 'w', encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Checkpoint saved to {model_dir}")

def load_checkpoint(model, optimizer, scheduler, checkpoint_dir):
    """
    Load training checkpoint.

    Args:
        model: Model to load into
        optimizer: Optimizer to load into
        scheduler: Scheduler to load into
        checkpoint_dir: Checkpoint directory

    Returns:
        Tuple of (epoch, loss)
    """
    checkpoint_dir = Path(checkpoint_dir)

    # Load training state
    checkpoint = torch.load(checkpoint_dir / "training_state.pt", weights_only=True)

    # Load states
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

    epoch = checkpoint['epoch']
    loss = checkpoint['loss']

    print(f"✓ Checkpoint loaded from {checkpoint_dir}")
    print(f"  Epoch: {epoch}")
    print(f"  Loss: {loss:.4f}")

    return epoch, loss

# Usage example
print("=== Checkpointing Demo ===\n")

output_dir = "./checkpoints/pretraining"

# Save checkpoint after first epoch
print("Saving checkpoint after epoch 1...")
save_checkpoint(
    model=model,
    optimizer=optimizer,
    scheduler=scheduler,
    epoch=1,
    loss=3.2,
    config={"lr": 1e-4, "batch_size": 4},
    output_dir=output_dir
)

# List checkpoints
checkpoint_dir = Path(output_dir)
checkpoints = sorted(checkpoint_dir.glob("checkpoint-*"))
print(f"\nAvailable checkpoints:")
for ckpt in checkpoints:
    metadata_file = ckpt / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
        print(f"  {ckpt.name}: Epoch {metadata['epoch']}, Loss {metadata['loss']:.4f}")

# Load checkpoint
print("\nLoading checkpoint...")
new_model = GPT2LMHeadModel(config)
new_optimizer = AdamW(new_model.parameters(), lr=1e-4)
new_scheduler = get_linear_schedule_with_warmup(new_optimizer, num_warmup_steps=100, num_training_steps=1000)

epoch, loss = load_checkpoint(
    model=new_model,
    optimizer=new_optimizer,
    scheduler=new_scheduler,
    checkpoint_dir=checkpoints[0]
)

print(f"\n✓ Resuming from epoch {epoch + 1}")

# Expected output:
# Checkpoint saved with model, optimizer, and scheduler states
# Can resume training from checkpoint
# Metadata shows epoch and loss information

# Troubleshooting Tips:
# - If loading fails: Ensure checkpoint directory exists and contains all files
# - If model mismatch: Check config matches between save and load
# - If device mismatch: Model loads to CPU, move to GPU manually
```

### Exercise 5: Evaluation

**Objective:** Evaluate trained language model using perplexity.

**Solution:**

```python
import math

def evaluate(model, dataloader, device):
    """
    Evaluate model on validation set.

    Args:
        model: Trained model
        dataloader: Validation dataloader
        device: Device to run on

    Returns:
        Tuple of (avg_loss, perplexity)
    """
    model.eval()
    total_loss = 0.0
    total_examples = 0

    print("\n=== Evaluating Model ===\n")

    with torch.no_grad():
        for batch_idx, batch in enumerate(tqdm(dataloader, desc="Evaluating")):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)

            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=input_ids
            )

            loss = outputs.loss
            # Batch loss is a mean over tokens: weight by the batch's
            # example count. Dividing the weighted sum by len(dataloader)
            # instead inflates the result by the batch size (4x here)
            total_loss += loss.item() * input_ids.size(0)
            total_examples += input_ids.size(0)

    avg_loss = total_loss / total_examples
    perplexity = math.exp(avg_loss)

    return avg_loss, perplexity

# Create validation dataset
print("Creating validation dataset...")
# datasets 5.x: full hub URI (the bare "wikitext" alias no longer resolves)
val_dataset = load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="validation")
val_tokenized = val_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
val_dataloader = create_dataloader(val_tokenized, batch_size=4, shuffle=False)

# Evaluate
val_loss, val_perplexity = evaluate(model, val_dataloader, device)

print(f"\n{'='*60}")
print(f"Validation Results:")
print(f"  Loss: {val_loss:.4f}")
print(f"  Perplexity: {val_perplexity:.2f}")
print(f"{'='*60}")

# Generate text samples
print("\n=== Text Generation ===\n")

model.eval()
prompts = [
    "The capital of France is",
    "Artificial intelligence is",
    "The future of technology"
]

for prompt in prompts:
    print(f"Prompt: {prompt}")

    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=50,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Generated: {generated_text}\n")

# Expected output:
# Loss and perplexity far below the untrained model (which sits at
# perplexity ~ vocab size)
# Note: labels are not masked for padding, so EOS pad tokens count
# toward the loss - computed perplexity underestimates true text
# difficulty; watch the trend, not a specific range
# Generated text: short and repetitive at this model size, coherent
# only in style

# Troubleshooting Tips:
# - If perplexity is >1000: Model may not have trained enough
# - If memory error: Reduce batch size or use gradient accumulation
# - If poor generation: Increase training time or model size

# Additional metrics
def compute_bleu(model, tokenizer, dataloader, device):
    """Compute BLEU score (simplified)."""
    # This is a placeholder - full BLEU requires proper tokenization
    # and reference texts
    pass

def compute_diversity(model, tokenizer, prompts, device):
    """Compute generation diversity metrics."""
    model.eval()
    generations = []

    with torch.no_grad():
        for prompt in prompts:
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            outputs = model.generate(
                **inputs,
                max_length=50,
                num_return_sequences=5,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

            for output in outputs:
                generations.append(tokenizer.decode(output, skip_special_tokens=True))

    # Compute diversity (unique n-grams / total n-grams)
    all_bigrams = []
    for gen in generations:
        words = gen.split()
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        all_bigrams.extend(bigrams)

    unique_bigrams = len(set(all_bigrams))
    total_bigrams = len(all_bigrams)
    diversity = unique_bigrams / total_bigrams if total_bigrams > 0 else 0

    print(f"\nGeneration Diversity: {diversity:.2%}")

    return diversity

# Compute diversity
diversity = compute_diversity(model, tokenizer, prompts, device)

print(f"\n✓ Evaluation complete!")
print(f"  Perplexity: {val_perplexity:.2f}")
print(f"  Diversity: {diversity:.2%}")
```

### Exercise 6: Advanced Training Techniques

**Objective:** Implement advanced pretraining techniques.

**Solution:**

```python
# Mixed Precision Training
# torch.cuda.amp is deprecated since PyTorch 2.4 - the canonical home
# is torch.amp, whose autocast/GradScaler take the device explicitly
from torch.amp import autocast, GradScaler
from transformers import get_cosine_schedule_with_warmup

def train_with_mixed_precision(model, dataloader, optimizer, scheduler, device, epochs=3):
    """Train with automatic mixed precision for faster training."""

    scaler = GradScaler("cuda")

    for epoch in range(epochs):
        model.train()
        total_loss = 0

        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}")

        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)

            optimizer.zero_grad()

            # Mixed precision forward pass
            with autocast("cuda"):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=input_ids
                )
                loss = outputs.loss

            # Scale gradients and update
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            total_loss += loss.item()
            progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}: Loss = {avg_loss:.4f}")

# Gradient Accumulation
def train_with_gradient_accumulation(model, dataloader, optimizer, scheduler, device, accumulation_steps=4, epochs=3):
    """Train with gradient accumulation for larger effective batch size."""

    # One scaler for the whole run: a fresh GradScaler every batch would
    # reset the scale state, so dynamic loss scaling could never adapt
    scaler = GradScaler("cuda")

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        accumulated_steps = 0

        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}")

        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)

            # Forward pass
            with autocast("cuda"):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=input_ids
                )
                loss = outputs.loss / accumulation_steps

            # Backward pass
            scaler.scale(loss).backward()
            accumulated_steps += 1

            # Update weights every accumulation_steps
            if accumulated_steps % accumulation_steps == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                scheduler.step()

            total_loss += loss.item() * accumulation_steps
            progress_bar.set_postfix({'loss': f'{loss.item()*accumulation_steps:.4f}'})

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}: Loss = {avg_loss:.4f}")

# Learning Rate Scheduling
def train_with_warmup_cosine(model, dataloader, device, epochs=3, warmup_ratio=0.1):
    """Train with warmup + cosine annealing schedule."""

    num_training_steps = len(dataloader) * epochs
    num_warmup_steps = int(num_training_steps * warmup_ratio)

    optimizer = AdamW(model.parameters(), lr=1e-4)
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=num_training_steps
    )

    # One persistent scaler for the whole run (see gradient accumulation)
    scaler = GradScaler("cuda")

    for epoch in range(epochs):
        model.train()
        total_loss = 0

        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}")

        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)

            with autocast("cuda"):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=input_ids)
                loss = outputs.loss

            # Same rule: one persistent scaler, not one per batch
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
            scheduler.step()

            total_loss += loss.item()

            current_lr = scheduler.get_last_lr()[0]
            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'lr': f'{current_lr:.2e}'
            })

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}: Loss = {avg_loss:.4f}")

print("=== Advanced Training Techniques ===\n")
print("1. Mixed Precision Training (faster, less memory)")
print("2. Gradient Accumulation (larger effective batch size)")
print("3. Warmup + Cosine Scheduling (better convergence)")

# Expected benefits:
# - Mixed precision: 2-3x faster training on modern GPUs
# - Gradient accumulation: Simulate larger batch sizes
# - Warmup + cosine: More stable and better final loss
```

---

## Summary

This practice guide covers:

1. **Dataset Preparation:** Loading and tokenizing text data for pretraining
2. **Data Loading:** Creating PyTorch DataLoaders for efficient training
3. **Training Loop:** Complete training implementation with optimization
4. **Checkpointing:** Saving and resuming training state
5. **Evaluation:** Computing perplexity and generating text
6. **Advanced Techniques:** Mixed precision, gradient accumulation, and learning rate scheduling

**Expected Learning Outcomes:**
- Prepare datasets for language model pretraining
- Implement efficient data loading pipelines
- Write complete training loops for LMs
- Save and load training checkpoints
- Evaluate models using perplexity
- Apply advanced training techniques
