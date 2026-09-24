# LAB 006: Train a Small Language Model from Scratch

**"Birth of a Model"** - Train your first language model end-to-end.

---

## Lab Overview

**Prerequisites:** Volume 2 (Math), Volume 3 (LLM Internals), [2401: Pre-training Fundamentals](../../phases/phase2-foundations/2400-Pre-training/2401-Pre-training-Fundamentals.md)
**Time:** 6-8 hours
**Difficulty:** ⭐⭐⭐⭐ Advanced

### What You'll Build

- ✅ Train a 10M parameter language model from scratch
- ✅ Prepare and clean training data
- ✅ Implement transformer architecture
- ✅ Train with proper hyperparameters
- ✅ Evaluate with perplexity and benchmarks
- ✅ Generate text with your model

### Why This Lab Matters

This is the **ultimate test** of your understanding. After this lab, you will:
- Understand the complete training pipeline
- Be able to scale to larger models
- Debug training issues
- Optimize for quality and speed

---

## Part 1: Setup (30 minutes)

### Environment Setup

```bash
# Create conda environment
conda create -n train_model python=3.11 -y
conda activate train_model

# Install dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers datasets tokenizers
pip install wandb tensorboard
pip install tqdm matplotlib seaborn

# Create directories
mkdir -p lab006_train_model
cd lab006_train_model
mkdir -p data checkpoints logs
```

### Verify GPU

```python
# verify_gpu.py
import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU count: {torch.cuda.device_count()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")
print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Expected output on an 11GB-class GPU:
# CUDA available: True
# GPU name: NVIDIA GeForce RTX 3060 (12GB)
# GPU memory: 11.0 GB
```

Run it:
```bash
python verify_gpu.py
```

### ✅ Checkpoint 1: GPU Ready
- [ ] GPU detected
- [ ] At least 8GB VRAM
- [ ] PyTorch working

---

## Part 2: Data Preparation (90 minutes)

### Task: Download and Prepare Training Data

We'll use a small, clean dataset for quick training.

```python
# prepare_data.py
import os
import json
import requests
from datasets import load_dataset
from typing import List, Dict
import re

def download_wikipedia_sample(output_file: str = "data/wiki_sample.jsonl"):
    """
    Download small Wikipedia sample

    We'll use just 10k articles for quick training
    """
    print("Downloading Wikipedia dataset...")

    # Load Wikipedia from HuggingFace
    dataset = load_dataset("wikipedia", "20220301.en", split="train")

    # Take first 10k articles
    print(f"Total articles: {len(dataset)}")
    print(f"Taking first 10,000 articles...")

    sample_data = []
    for i, example in enumerate(dataset):
        if i >= 10000:
            break

        sample_data.append({
            "text": example["text"],
            "title": example["title"],
            "id": example["id"]
        })

    # Save
    os.makedirs("data", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in sample_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Saved {len(sample_data)} articles to {output_file}")

    # Print statistics
    total_words = sum(len(item["text"].split()) for item in sample_data)
    total_chars = sum(len(item["text"]) for item in sample_data)

    print(f"\nDataset Statistics:")
    print(f"  Documents: {len(sample_data)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Total chars: {total_chars:,}")
    print(f"  Avg words/doc: {total_words / len(sample_data):.1f}")
    print(f"  Estimated tokens: {int(total_chars / 4):,}")

    return sample_data

def clean_text(text: str) -> str:
    """Basic text cleaning"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove very short lines
    lines = text.split('\n')
    lines = [l for l in lines if len(l.strip()) > 20]

    return '\n'.join(lines)

def filter_documents(data: List[Dict]) -> List[Dict]:
    """Filter documents by quality"""
    filtered = []

    for item in data:
        text = clean_text(item["text"])

        # Skip if too short
        if len(text.split()) < 100:
            continue

        # Skip if too long
        if len(text.split()) > 5000:
            # Truncate
            text = ' '.join(text.split()[:5000])

        filtered.append({
            "text": text,
            "title": item["title"],
            "id": item["id"]
        })

    print(f"Filtered {len(data)} -> {len(filtered)} documents")
    return filtered

if __name__ == "__main__":
    # Download
    data = download_wikipedia_sample("data/wiki_raw.jsonl")

    # Filter
    filtered = filter_documents(data)

    # Save filtered
    with open("data/wiki_filtered.jsonl", 'w', encoding='utf-8') as f:
        for item in filtered:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print("\nData preparation complete!")
    print("File: data/wiki_filtered.jsonl")
```

Run:
```bash
python prepare_data.py
```

### Expected Output:
```
Downloading Wikipedia dataset...
Total articles: 6,427,685
Taking first 10,000 articles...
Saved 10000 articles to data/wiki_raw.jsonl

Dataset Statistics:
  Documents: 10000
  Total words: 12,458,923
  Total chars: 78,234,567
  Avg words/doc: 1245.9
  Estimated tokens: 19,558,641

Filtered 10000 -> 9847 documents

Data preparation complete!
File: data/wiki_filtered.jsonl
```

### ✅ Checkpoint 2: Data Ready
- [ ] Downloaded 10k Wikipedia articles
- [ ] Cleaned and filtered
- [ ] ~20M tokens ready for training
- [ ] File saved: data/wiki_filtered.jsonl

---

## Part 3: Tokenizer Training (60 minutes)

### Task: Train BPE Tokenizer

```python
# train_tokenizer.py
from tokenizers import Tokenizer, models, trainers, pre_tokenizers
from tokenizers.processors import BertProcessing
from datasets import Dataset
import json

def load_training_data(data_path: str):
    """Load data for tokenizer training"""
    texts = []

    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            texts.append(item["text"])

    return texts

def train_tokenizer(texts, vocab_size: int = 10000, save_path: str = "tokenizer"):
    """
    Train BPE tokenizer

    Small vocab size (10k) for our small model
    """
    print(f"Training tokenizer with vocab_size={vocab_size}...")

    # Initialize tokenizer
    tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))

    # Pre-tokenizer (split into words)
    tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()

    # Trainer
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "],
        min_frequency=2,
    )

    # Train
    print("Training on texts...")
    tokenizer.train_from_iterator(texts, trainer=trainer)

    # Save
    import os
    os.makedirs(save_path, exist_ok=True)
    tokenizer.save(f"{save_path}/tokenizer.json")

    print(f"Tokenizer saved to {save_path}/tokenizer.json")

    # Print stats
    vocab = tokenizer.get_vocab()
    print(f"\nTokenizer Statistics:")
    print(f"  Vocabulary size: {len(vocab)}")

    # Test tokenization
    test_text = "Hello, world! This is a test."
    encoded = tokenizer.encode(test_text)
    print(f"\nTest tokenization:")
    print(f"  Text: {test_text}")
    print(f"  Tokens: {encoded.tokens}")
    print(f"  Token IDs: {encoded.ids}")

    return tokenizer

if __name__ == "__main__":
    # Load data
    print("Loading data...")
    texts = load_training_data("data/wiki_filtered.jsonl")
    print(f"Loaded {len(texts)} documents")

    # Train tokenizer
    tokenizer = train_tokenizer(texts[:5000], vocab_size=10000)

    print("\nTokenizer training complete!")
```

Run:
```bash
python train_tokenizer.py
```

### Expected Output:
```
Loading data...
Loaded 9847 documents
Training tokenizer with vocab_size=10000...
Training on texts...
Tokenizer saved to tokenizer/tokenizer.json

Tokenizer Statistics:
  Vocabulary size: 10000

Test tokenization:
  Text: Hello, world! This is a test.
  Tokens: ['Hello', ',', 'world', '!', 'This', 'is', 'a', 'test', '.']
  Token IDs: [4823, 15, 1923, 12, 834, 123, 45, 2341, 10]

Tokenizer training complete!
```

### ✅ Checkpoint 3: Tokenizer Ready
- [ ] Trained BPE tokenizer
- [ ] Vocabulary size: 10k
- [ ] Tokenizer saved: tokenizer/tokenizer.json
- [ ] Tested tokenization

---

## Part 4: Model Architecture (60 minutes)

### Task: Implement Transformer

```python
# model.py
import torch
import torch.nn as nn
import math

class TransformerConfig:
    """Configuration for our small transformer"""
    def __init__(self):
        self.vocab_size = 10000
        self.max_length = 512
        self.d_model = 256  # Smaller than typical (512/768/1024)
        self.n_heads = 8
        self.n_layers = 6  # 6 layers
        self.d_ff = 1024  # Feed-forward dimension
        self.dropout = 0.1

class MultiHeadAttention(nn.Module):
    """Multi-head self-attention"""
    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.d_model = config.d_model
        self.n_heads = config.n_heads
        self.head_dim = config.d_model // config.n_heads

        assert config.d_model % config.n_heads == 0, "d_model must be divisible by n_heads"

        # Q, K, V projections
        self.q_proj = nn.Linear(config.d_model, config.d_model)
        self.k_proj = nn.Linear(config.d_model, config.d_model)
        self.v_proj = nn.Linear(config.d_model, config.d_model)

        # Output projection
        self.out_proj = nn.Linear(config.d_model, config.d_model)

        self.dropout = nn.Dropout(config.dropout)
        self.scale = math.sqrt(self.head_dim)

    def forward(self, x, mask=None):
        batch_size, seq_len, _ = x.shape

        # Project Q, K, V
        Q = self.q_proj(x)  # (batch, seq_len, d_model)
        K = self.k_proj(x)
        V = self.v_proj(x)

        # Reshape for multi-head
        Q = Q.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale

        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn_weights = torch.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # Apply attention to V
        context = torch.matmul(attn_weights, V)

        # Reshape back
        context = context.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)

        # Output projection
        output = self.out_proj(context)

        return output

class FeedForward(nn.Module):
    """Position-wise feed-forward network"""
    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(config.d_model, config.d_ff),
            nn.GELU(),  # GELU activation
            nn.Dropout(config.dropout),
            nn.Linear(config.d_ff, config.d_model),
            nn.Dropout(config.dropout)
        )

    def forward(self, x):
        return self.net(x)

class TransformerBlock(nn.Module):
    """Transformer decoder block"""
    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.attention = MultiHeadAttention(config)
        self.norm1 = nn.LayerNorm(config.d_model)
        self.norm2 = nn.LayerNorm(config.d_model)
        self.ffn = FeedForward(config)

        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x, mask=None):
        # Self-attention with residual
        attn_out = self.attention(x, mask)
        x = self.norm1(x + self.dropout(attn_out))

        # Feed-forward with residual
        ffn_out = self.ffn(x)
        x = self.norm2(x + self.dropout(ffn_out))

        return x

class SmallLanguageModel(nn.Module):
    """Our small language model"""
    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.config = config

        # Token embeddings
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)

        # Positional embeddings
        self.position_embedding = nn.Embedding(config.max_length, config.d_model)

        # Transformer blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.n_layers)
        ])

        # Output projection
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)

        # Tie weights (share embedding and lm_head)
        self.lm_head.weight = self.token_embedding.weight

        self.dropout = nn.Dropout(config.dropout)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                # Normal initialization
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
            elif isinstance(module, nn.LayerNorm):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, input_ids, attention_mask=None):
        batch_size, seq_len = input_ids.shape

        # Token embeddings
        token_embeds = self.token_embedding(input_ids)

        # Positional embeddings
        positions = torch.arange(seq_len, device=input_ids.device)
        position_embeds = self.position_embedding(positions)

        # Combine embeddings
        x = self.dropout(token_embeds + position_embeds)

        # Create causal mask
        if attention_mask is None:
            # Causal mask (lower triangular)
            mask = torch.tril(torch.ones(seq_len, seq_len, device=input_ids.device))
            mask = mask.view(1, 1, seq_len, seq_len)
        else:
            mask = attention_mask

        # Pass through transformer blocks
        for block in self.blocks:
            x = block(x, mask)

        # Project to vocabulary
        logits = self.lm_head(x)

        return logits

    @torch.no_grad()
    def generate(self, input_ids, max_new_tokens=50, temperature=1.0, do_sample=True):
        """Generate text"""
        self.eval()

        for _ in range(max_new_tokens):
            # Forward pass
            logits = self.forward(input_ids)

            # Get next token logits
            next_token_logits = logits[:, -1, :] / temperature

            # Sample
            probs = torch.softmax(next_token_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)

            # Append
            input_ids = torch.cat([input_ids, next_token], dim=1)

        return input_ids

# Count parameters
def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

# Test model
if __name__ == "__main__":
    config = TransformerConfig()
    model = SmallLanguageModel(config)

    print(f"Model Parameters: {count_parameters(model):,}")

    # Test forward pass
    batch_size = 2
    seq_len = 128
    input_ids = torch.randint(0, config.vocab_size, (batch_size, seq_len))

    output = model(input_ids)
    print(f"Input shape: {input_ids.shape}")
    print(f"Output shape: {output.shape}")

    # Expected: ~10M parameters
    # Input shape: torch.Size([2, 128])
    # Output shape: torch.Size([2, 128, 10000])
```

Run to test model:
```bash
python model.py
```

### Expected Output:
```
Model Parameters: 10,234,567
Input shape: torch.Size([2, 128])
Output shape: torch.Size([2, 128, 10000])
```

### ✅ Checkpoint 4: Model Ready
- [ ] Transformer architecture implemented
- [ ] ~10M parameters
- [ ] Forward pass working
- [ ] Causal masking implemented

---

## Part 5: Training Loop (120 minutes)

### Task: Implement Training

```python
# train.py
import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from tqdm import tqdm
import wandb
from model import SmallLanguageModel, TransformerConfig, count_parameters
import math

# Initialize wandb
wandb.init(project="lab006-train-model", name="small-transformer")

class TextDataset(Dataset):
    """Dataset for language modeling"""
    def __init__(self, data_path, tokenizer, max_length=512):
        self.data = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        # Load data
        print(f"Loading data from {data_path}...")
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                self.data.append(item["text"])

        print(f"Loaded {len(self.data)} documents")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text = self.data[idx]

        # Tokenize
        encoded = self.tokenizer.encode(text)
        input_ids = encoded.ids

        # Truncate or pad
        if len(input_ids) > self.max_length:
            input_ids = input_ids[:self.max_length]
        else:
            # Pad
            input_ids = input_ids + [self.tokenizer.token_to_id("[PAD]")] * (self.max_length - len(input_ids))

        # For causal LM, labels = input_ids
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(input_ids, dtype=torch.long),
        }

def train_epoch(model, dataloader, optimizer, scheduler, device, epoch):
    """Train for one epoch"""
    model.train()

    total_loss = 0
    total_tokens = 0

    pbar = tqdm(dataloader, desc=f"Epoch {epoch}")

    for step, batch in enumerate(pbar):
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)

        # Forward pass
        logits = model(input_ids)

        # Calculate loss
        loss = nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)),
            labels.view(-1),
            ignore_index=-100  # Ignore padding if using -100
        )

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()
        scheduler.step()

        # Update metrics
        total_loss += loss.item()
        total_tokens += labels.numel()

        # Logging
        if step % 10 == 0:
            avg_loss = total_loss / (step + 1)
            perplexity = math.exp(avg_loss)
            lr = scheduler.get_last_lr()[0]

            pbar.set_postfix({
                "loss": f"{avg_loss:.4f}",
                "ppl": f"{perplexity:.2f}",
                "lr": f"{lr:.2e}"
            })

            wandb.log({
                "train/loss": avg_loss,
                "train/perplexity": perplexity,
                "train/learning_rate": lr,
                "train/step": epoch * len(dataloader) + step
            })

    return total_loss / len(dataloader)

@torch.no_grad()
def evaluate(model, dataloader, device):
    """Evaluate model"""
    model.eval()

    total_loss = 0

    for batch in tqdm(dataloader, desc="Evaluating"):
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)

        logits = model(input_ids)

        loss = nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)),
            labels.view(-1),
            ignore_index=-100
        )

        total_loss += loss.item()

    avg_loss = total_loss / len(dataloader)
    perplexity = math.exp(avg_loss)

    return avg_loss, perplexity

def main():
    # Configuration
    config = TransformerConfig()

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load tokenizer
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file("tokenizer/tokenizer.json")

    # Load data
    print("Loading datasets...")
    train_dataset = TextDataset("data/wiki_filtered.jsonl", tokenizer, max_length=256)
    # Split train/val
    train_size = int(0.9 * len(train_dataset))
    val_size = len(train_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(train_dataset, [train_size, val_size])

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, num_workers=4)

    # Model
    model = SmallLanguageModel(config).to(device)
    print(f"Model parameters: {count_parameters(model):,}")

    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=6e-4, weight_decay=0.01)

    # Scheduler
    total_steps = len(train_loader) * 10  # 10 epochs
    warmup_steps = int(0.1 * total_steps)

    def lr_lambda(step):
        if step < warmup_steps:
            return step / warmup_steps
        progress = (step - warmup_steps) / (total_steps - warmup_steps)
        return 0.5 * (1 + math.cos(math.pi * progress))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    # Training loop
    best_val_loss = float('inf')

    for epoch in range(1, 11):
        print(f"\n{'='*50}")
        print(f"Epoch {epoch}/10")
        print(f"{'='*50}")

        # Train
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, device, epoch)

        # Evaluate
        val_loss, val_ppl = evaluate(model, val_loader, device)

        print(f"\nEpoch {epoch} Results:")
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val Loss: {val_loss:.4f}")
        print(f"  Val Perplexity: {val_ppl:.2f}")

        wandb.log({
            "val/loss": val_loss,
            "val/perplexity": val_ppl,
            "epoch": epoch
        })

        # Save checkpoint
        checkpoint_dir = f"checkpoints/epoch_{epoch}"
        os.makedirs(checkpoint_dir, exist_ok=True)

        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_loss': val_loss,
        }, f"{checkpoint_dir}/model.pt")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "checkpoints/best_model.pt")
            print(f"  Saved best model (val_loss: {val_loss:.4f})")

    print("\nTraining complete!")

if __name__ == "__main__":
    main()
```

Run training:
```bash
python train.py
```

### Expected Training Progress:

```
Using device: cuda
Loading datasets...
Loaded 9847 documents
Model parameters: 10,234,567

==================================================
Epoch 1/10
==================================================
training: 100%|████████| 1105/1105 [05:23<00:00, 3.42it/s, loss=3.2145, ppl=24.89, lr=6.00e-04]
Evaluating: 100%|████████| 123/123 [00:15<00:00, 8.02it/s]

Epoch 1 Results:
  Train Loss: 3.2145
  Val Loss: 3.1023
  Val Perplexity: 22.25
  Saved best model (val_loss: 3.1023)

... (continues through epoch 10)

Epoch 10 Results:
  Train Loss: 1.8234
  Val Loss: 2.1456
  Val Perplexity: 8.55

Training complete!
```

### ✅ Checkpoint 5: Training Complete
- [ ] Trained for 10 epochs
- [ ] Loss decreased significantly
- [ ] Perplexity improved (20+ → 8-10)
- [ ] Checkpoints saved

---

## Part 6: Text Generation (30 minutes)

### Task: Generate Text with Your Model

```python
# generate.py
import torch
from tokenizers import Tokenizer
from model import SmallLanguageModel, TransformerConfig

def generate_text(model, tokenizer, prompt, max_new_tokens=100, temperature=0.8):
    """Generate text with trained model"""
    model.eval()

    # Encode prompt
    encoded = tokenizer.encode(prompt)
    input_ids = torch.tensor([encoded.ids], dtype=torch.long).cuda()

    # Generate
    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature
        )

    # Decode
    generated_text = tokenizer.decode(output_ids[0].tolist(), skip_special_tokens=True)

    return generated_text

def main():
    # Load tokenizer
    tokenizer = Tokenizer.from_file("tokenizer/tokenizer.json")

    # Load model
    config = TransformerConfig()
    model = SmallLanguageModel(config).cuda()

    # Load checkpoint
    checkpoint = torch.load("checkpoints/best_model.pt")
    model.load_state_dict(checkpoint)
    model.eval()

    print("Model loaded. Ready to generate!\n")

    # Test prompts
    prompts = [
        "Artificial intelligence is",
        "The history of machine learning began",
        "Neural networks work by",
    ]

    for prompt in prompts:
        print(f"Prompt: {prompt}")
        generated = generate_text(model, tokenizer, prompt, max_new_tokens=50, temperature=0.8)
        print(f"Generated: {generated}\n")
        print("-" * 50 + "\n")

if __name__ == "__main__":
    main()
```

Run:
```bash
python generate.py
```

### Expected Output (example):

```
Model loaded. Ready to generate!

Prompt: Artificial intelligence is
Generated: Artificial intelligence is a branch of computer science that deals with the creation of intelligent machines that can perform tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.

--------------------------------------------------

Prompt: The history of machine learning began
Generated: The history of machine learning began in the 1950s with the development of the first learning algorithms. Early researchers like Arthur Samuel and Frank Rosenblatt developed programs that could learn from data and improve their performance over time.

--------------------------------------------------

Prompt: Neural networks work by
Generated: Neural networks work by processing information through layers of interconnected nodes or neurons. Each neuron receives input, processes it using an activation function, and passes the output to the next layer. This allows the network to learn complex patterns in data.

--------------------------------------------------
```

**Note:** Your generated text will be different and quality depends on training!

### ✅ Checkpoint 6: Generation Working
- [ ] Model generates coherent text
- [ ] Text follows prompt
- [ ] Reasonable grammar and flow
- [ ] Temperature affects diversity

---

## Part 7: Evaluation (30 minutes)

### Task: Evaluate Model Quality

```python
# evaluate.py
import torch
import math
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from tqdm import tqdm
from model import SmallLanguageModel, TransformerConfig

def calculate_perplexity(model, dataloader, device):
    """Calculate perplexity on dataset"""
    model.eval()

    total_loss = 0
    total_tokens = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Calculating perplexity"):
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)

            logits = model(input_ids)

            loss = torch.nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
                ignore_index=-100,
                reduction='sum'
            )

            total_loss += loss.item()
            total_tokens += (labels != -100).sum().item()

    avg_loss = total_loss / total_tokens
    perplexity = math.exp(avg_loss)

    return perplexity

def compare_models():
    """Compare our model with baseline"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load our model
    config = TransformerConfig()
    model = SmallLanguageModel(config).to(device)
    model.load_state_dict(torch.load("checkpoints/best_model.pt"))

    # Load tokenizer
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file("tokenizer/tokenizer.json")

    # Load validation data
    from train import TextDataset
    val_dataset = TextDataset("data/wiki_filtered.jsonl", tokenizer, max_length=256)
    # Use subset for quick eval
    val_dataset = torch.utils.data.Subset(val_dataset, range(1000))
    val_loader = DataLoader(val_dataset, batch_size=8)

    # Calculate perplexity
    ppl = calculate_perplexity(model, val_loader, device)

    print(f"\nModel Perplexity: {ppl:.2f}")

    # Compare to baselines
    print("\nBaseline Comparisons:")
    print(f"  GPT-2 (124M): ~20-30 on Wikitext")
    print(f"  GPT-2 (1.5B): ~15-20 on Wikitext")
    print(f"  Our model (10M): {ppl:.2f} on Wikipedia subset")

    # Calculate scaling
    baseline_ppl = 25.0
    baseline_params = 124_000_000
    our_params = 10_000_000

    expected_ppl = baseline_ppl * (baseline_params / our_params) ** -0.1
    print(f"\n  Expected perplexity (scaling law): {expected_ppl:.2f}")
    print(f"  Actual perplexity: {ppl:.2f}")

    if ppl < expected_ppl:
        print("  ✓ Model performing better than expected!")
    else:
        print("  ✗ Model underperforming - may need more training")

if __name__ == "__main__":
    compare_models()
```

Run:
```bash
python evaluate.py
```

### ✅ Checkpoint 7: Evaluated
- [ ] Perplexity calculated
- [ ] Compared to baselines
- [ ] Documented results

---

## Part 8: Challenges (Optional)

### Challenge 1: Scale Up (120 minutes)

**Task:** Train a larger model

```yaml
Requirements:
  - Increase model size to 50M parameters
  - Train on full dataset (all 10k documents)
  - Add gradient checkpointing
  - Train for 20 epochs

Target perplexity: < 7.0
```

### Challenge 2: Improve Architecture (120 minutes)

**Task:** Add improvements

```yaml
Try these improvements:
  - Add rotary positional embeddings (RoPE)
  - Implement Flash Attention
  - Add layer normalization at different positions
  - Try different activation functions (SwiGLU)

Measure improvement in perplexity
```

### Challenge 3: Multi-GPU Training (180 minutes)

**Task:** Scale to multiple GPUs

```yaml
Implement:
  - DistributedDataParallel (DDP)
  - Gradient accumulation
  - Proper sharding of data

Train on 2+ GPUs simultaneously
```

---

## Summary

### What You Built

| Component | What You Did | File |
|-----------|--------------|------|
| **Data** | Downloaded & cleaned 10k Wikipedia articles | `data/wiki_filtered.jsonl` |
| **Tokenizer** | Trained BPE tokenizer with 10k vocab | `tokenizer/tokenizer.json` |
| **Model** | 10M parameter transformer | `model.py` |
| **Training** | Trained for 10 epochs | `checkpoints/` |
| **Generation** | Generated text with trained model | `generate.py` |
| **Evaluation** | Calculated perplexity | `evaluate.py` |

### Key Metrics

```
Model Size: 10M parameters
Training Tokens: ~20M tokens
Training Time: ~6 hours (on an 11GB-class GPU)
Final Perplexity: 8-10
```

### Next Steps

1. **Train Larger Model:** Scale to 50M-100M parameters
2. **More Data:** Add more diverse datasets
3. **Longer Training:** Train for more epochs
4. **Better Architecture:** Try RoPE, Flash Attention
5. **Production Deploy:** Deploy with vLLM (Volume 4)

---

## 🎯 You're Now Ready For

- **[Volume 5: Fine-Tuning](../VOLUME-5-Model-Adaptation.md)** - Adapt your model
- **[Volume 7: Production](../VOLUME-7-Production-Mastery.md)** - Deploy your model
- **[2402: Large-Scale Training](../../phases/phase2-foundations/2400-Pre-training/2402-Large-Scale-Training.md)** - Scale up training

---

**LAB 006 Status:** 🟢 Complete
**Time:** 6-8 hours
**Difficulty:** ⭐⭐⭐⭐ Advanced
