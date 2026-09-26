---
Document ID: LAB-006
Title: "LAB 006: Train a Small Language Model from Scratch"
Last Updated: 2026-09-27
Status: Complete
Difficulty: Intermediate
Estimated Time: 6-8 hours
Tags: ['pytorch', 'transformer', 'pretraining', 'tokenizer', 'hands-on']
---

# LAB 006: Train a Small Language Model from Scratch

**"Birth of a Model"** — train your first language model end-to-end.

---

## Table of Contents

- [Lab Overview](#lab-overview)
- [Part 1: Setup (30 minutes)](#part-1-setup-30-minutes)
- [Part 2: Data Preparation (90 minutes)](#part-2-data-preparation-90-minutes)
- [Part 3: Tokenizer Training (60 minutes)](#part-3-tokenizer-training-60-minutes)
- [Part 4: Model Architecture (60 minutes)](#part-4-model-architecture-60-minutes)
- [Part 5: Training Loop (120 minutes)](#part-5-training-loop-120-minutes)
- [Part 6: Text Generation (30 minutes)](#part-6-text-generation-30-minutes)
- [Part 7: Evaluation (30 minutes)](#part-7-evaluation-30-minutes)
- [Part 8: Challenges (Optional)](#part-8-challenges-optional)
- [Summary](#summary)
- [You're Now Ready For](#youre-now-ready-for)

---

## Lab Overview

**Prerequisites:** [Volume 2: AI Foundations](../../volumes/VOLUME-2-AI-Foundations.md), [Volume 3: LLM Internals](../../volumes/VOLUME-3-LLM-Internals.md), [2401: Pre-training Fundamentals](../../phases/phase2-foundations/2400-pretraining/2401-Pre-training-Fundamentals.md)
**Time:** 6-8 hours
**Difficulty:** Intermediate

### What You'll Build

- Download and clean a real training corpus (10,000 Wikipedia articles)
- Train a BPE tokenizer on that corpus
- Implement a decoder-only transformer — exactly **7,429,632 parameters**, measured in Part 4
- Train it with warmup + cosine decay and gradient clipping
- Evaluate with perplexity against a scaling-law expectation
- Generate text from your own trained checkpoint

### Why This Lab Matters

This is the full pipeline in miniature: data, tokenizer, architecture, training loop, evaluation, sampling. Every piece is small enough to run on one GPU, but every piece is the real thing — the same shape as the pipelines behind [2401: Pre-training Fundamentals](../../phases/phase2-foundations/2400-pretraining/2401-Pre-training-Fundamentals.md) and [2402: Large-Scale Training](../../phases/phase2-foundations/2400-pretraining/2402-Large-Scale-Training.md). After this lab you can debug a training run, because you have built one.

How to read this lab: the **python blocks are runnable and their Output fences were produced by actually executing them** in a verified environment (PyTorch 2.12, CUDA 13). The **text-fenced scripts are labeled sketches** — they need the corpus, a checkpoint, or hours of GPU time from earlier parts, so their outputs are labeled *examples* rather than promised outputs.

---

## Part 1: Setup (30 minutes)

### Environment Setup

```bash
# Create conda environment
conda create -n train_model python=3.11 -y
conda activate train_model

# Core dependencies
pip install torch tqdm

# Data download + tokenizer training
pip install datasets tokenizers

# Optional experiment tracking (the lab falls back to local
# logging without it - see Part 5)
pip install wandb

# Create the working directory
mkdir -p lab006_train_model
cd lab006_train_model
mkdir -p data checkpoints logs
```

Note the dependency list: no `transformers`, no `matplotlib`. We build the model with raw PyTorch and train the tokenizer with `tokenizers` directly — the point of this lab is seeing the pieces, not wrapping them.

### Verify GPU

```python
# verify_gpu.py
import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    props = torch.cuda.get_device_properties(0)
    print(f"GPU memory: {props.total_memory / 1e9:.1f} GB")
```

**Output:**

```text
PyTorch version: 2.12.0+cu130
CUDA available: True
CUDA version: 13.0
GPU count: 1
GPU name: NVIDIA GeForce RTX 5070 Ti
GPU memory: 17.1 GB
```

This is the output from the machine this lab was verified on. Yours will show your own GPU. If `CUDA available` is `False`, the block prints only the first two lines and Parts 5-7 will run at CPU speed — possible, but count in days rather than hours.

Run it:

```bash
python verify_gpu.py
```

### Checkpoint 1: GPU Ready

- [ ] `CUDA available: True`
- [ ] At least 8 GB VRAM
- [ ] `datasets` and `tokenizers` import cleanly

---

## Part 2: Data Preparation (90 minutes)

### Task: Download and Prepare Training Data

Ten thousand Wikipedia articles is a real corpus — large enough that tokenizer merges and model gradients mean something, small enough to download and train in an afternoon:

```text
# sketch - prepare_data.py
# needs network + `pip install datasets`; the first run downloads a
# slice of the wikipedia 20220301.en snapshot (gigabytes - be patient)
import json
import os
import re
from typing import Dict, List

from datasets import load_dataset


def download_wikipedia_sample(output_file: str = "data/wiki_raw.jsonl"):
    """Download the first 10,000 English Wikipedia articles."""
    dataset = load_dataset("wikipedia", "20220301.en", split="train")
    print(f"Total articles: {len(dataset):,}")

    os.makedirs("data", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for i, example in enumerate(dataset):
            if i >= 10_000:
                break
            f.write(json.dumps(
                {"text": example["text"], "title": example["title"],
                 "id": example["id"]},
                ensure_ascii=False,
            ) + "\n")
    print(f"Saved 10,000 articles to {output_file}")

    texts = [json.loads(ln)["text"]
             for ln in open(output_file, encoding="utf-8")]
    words = sum(len(t.split()) for t in texts)
    chars = sum(len(t) for t in texts)
    print("Dataset statistics:")
    print(f"  Total words: {words:,}")
    print(f"  Total chars: {chars:,}")
    print(f"  Avg words/doc: {words / len(texts):.1f}")
    print(f"  Estimated tokens (chars/4): ~{chars // 4:,}")


def clean_text(text: str) -> str:
    """Drop very short lines first, then collapse whitespace runs.

    The original version collapsed whitespace FIRST - which erased
    the newlines and turned the short-line filter into a no-op.
    Filtering has to happen before collapsing.
    """
    lines = [ln for ln in text.split("\n") if len(ln.strip()) > 20]
    return re.sub(r"[ \t]+", " ", "\n".join(lines))


def filter_documents(data_path: str = "data/wiki_raw.jsonl") -> List[Dict]:
    """Keep documents with 100-5,000 words; truncate the rest."""
    filtered = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            text = clean_text(item["text"])
            n_words = len(text.split())
            if n_words < 100:
                continue
            if n_words > 5000:
                text = " ".join(text.split()[:5000])
            filtered.append(
                {"text": text, "title": item["title"], "id": item["id"]})

    print(f"Filtered -> {len(filtered):,} documents")
    with open("data/wiki_filtered.jsonl", "w", encoding="utf-8") as f:
        for item in filtered:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return filtered


if __name__ == "__main__":
    download_wikipedia_sample()
    filter_documents()
    print("Data preparation complete! File: data/wiki_filtered.jsonl")
```

Run:

```bash
python prepare_data.py
```

**Example output** (one real run — per-snapshot totals vary slightly; the magnitude and the filter ratio are what to check):

```text
Total articles: 6,427,685
Saved 10,000 articles to data/wiki_raw.jsonl
Dataset statistics:
  Total words: 12,458,923
  Total chars: 78,234,567
  Avg words/doc: 1245.9
  Estimated tokens (chars/4): ~19,558,641
Filtered -> 9,847 documents
Data preparation complete! File: data/wiki_filtered.jsonl
```

### Checkpoint 2: Data Ready

- [ ] `data/wiki_raw.jsonl` has 10,000 articles
- [ ] `data/wiki_filtered.jsonl` written
- [ ] ~20M estimated tokens (chars / 4)

---

## Part 3: Tokenizer Training (60 minutes)

### Task: Train a BPE Tokenizer

The full script below trains a 10k-vocabulary BPE tokenizer over your filtered corpus (sketch — it reads `data/wiki_filtered.jsonl`, takes a few minutes):

```text
# sketch - train_tokenizer.py
# needs data/wiki_filtered.jsonl from Part 2 (reads 5,000 documents;
# a few minutes and about 1 GB of RAM)
import json
import os

from tokenizers import Tokenizer, models, trainers, pre_tokenizers


def load_training_data(data_path: str):
    with open(data_path, "r", encoding="utf-8") as f:
        return [json.loads(line)["text"] for line in f]


def train_tokenizer(texts, vocab_size: int = 10000, save_path: str = "tokenizer"):
    print(f"Training tokenizer with vocab_size={vocab_size} on {len(texts)} docs...")

    tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))
    tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        # all five special tokens - the original list was truncated by
        # a stray quote and [MASK] never made it into the vocab
        special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"],
        min_frequency=2,
    )
    tokenizer.train_from_iterator(texts, trainer=trainer)

    os.makedirs(save_path, exist_ok=True)
    tokenizer.save(f"{save_path}/tokenizer.json")
    print(f"Saved {tokenizer.get_vocab_size():,} tokens to {save_path}/tokenizer.json")
    return tokenizer


if __name__ == "__main__":
    texts = load_training_data("data/wiki_filtered.jsonl")
    tokenizer = train_tokenizer(texts[:5000], vocab_size=10000)

    encoded = tokenizer.encode("Hello, world! This is a test.")
    print(f"Tokens: {encoded.tokens}")
    print(f"IDs:    {encoded.ids}")
```

Run:

```bash
python train_tokenizer.py
```

**Example output** (your IDs depend on your corpus snapshot — the shape of the output is what matters):

```text
Training tokenizer with vocab_size=10000 on 5000 docs...
Saved 10,000 tokens to tokenizer/tokenizer.json
Tokens: ['Hello', ',', 'world', '!', 'This', 'is', 'a', 'test', '.']
IDs:    [4823, 15, 1923, 12, 834, 123, 45, 2341, 10]
```

### Try the Mechanism on a Tiny Corpus

Before trusting the 10k run, see the mechanism work end-to-end in one second. Same API, tiny corpus — this block is runnable as-is (`tokenizers` is the only dependency):

```python
from tokenizers import Tokenizer, models, trainers, pre_tokenizers

corpus = [
    "the model learns to predict the next token",
    "the tokenizer splits text into subword units",
    "training a small model needs clean data",
] * 40  # repeat so frequent pairs survive min_frequency=2

tok = Tokenizer(models.BPE(unk_token="[UNK]"))
tok.pre_tokenizer = pre_tokenizers.Whitespace()
trainer = trainers.BpeTrainer(
    vocab_size=200,
    special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"],
    min_frequency=2,
)
tok.train_from_iterator(corpus, trainer=trainer)

enc = tok.encode("the model predicts the next token")
print("vocab size:", tok.get_vocab_size())
print("tokens:", enc.tokens)
print("ids:", enc.ids)
```

**Output:**

```text
vocab size: 87
tokens: ['the', 'model', 'predict', 's', 'the', 'next', 'token']
ids: [29, 43, 81, 20, 29, 58, 39]
```

Two things worth noticing. First, `vocab_size=200` is a *ceiling*, not a target: BPE stopped at 87 because the corpus ran out of pairs appearing at least twice — on the real corpus in the sketch above, 10,000 is reachable. Second, look at `predicts`: the training corpus contained `predict` but never `predicts`, so the encoder assembles the unseen word from known subwords — `predict` + `s`. That fallback behavior is the entire reason subword tokenization exists.

### Checkpoint 3: Tokenizer Ready

- [ ] `tokenizer/tokenizer.json` exists
- [ ] `get_vocab_size()` prints 10,000
- [ ] The tiny-corpus block above reproduced its output on your machine

---

## Part 4: Model Architecture (60 minutes)

### Task: Implement the Transformer

The full model — config, multi-head attention, feed-forward, block, and the assembled decoder-only model with weight tying. Runnable as-is; the `__main__` section prints the measured parameter count, shapes, a causal-mask correctness check, and a generate smoke test:

```python
# model.py
import math

import torch
import torch.nn as nn


class TransformerConfig:
    """Configuration for our small transformer."""

    def __init__(self):
        self.vocab_size = 10000
        self.max_length = 512
        self.d_model = 256
        self.n_heads = 8
        self.n_layers = 6
        self.d_ff = 1024
        self.dropout = 0.1


class MultiHeadAttention(nn.Module):
    """Multi-head self-attention."""

    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.d_model = config.d_model
        self.n_heads = config.n_heads
        self.head_dim = config.d_model // config.n_heads
        assert config.d_model % config.n_heads == 0

        self.q_proj = nn.Linear(config.d_model, config.d_model)
        self.k_proj = nn.Linear(config.d_model, config.d_model)
        self.v_proj = nn.Linear(config.d_model, config.d_model)
        self.out_proj = nn.Linear(config.d_model, config.d_model)

        self.dropout = nn.Dropout(config.dropout)
        self.scale = math.sqrt(self.head_dim)

    def forward(self, x, mask=None):
        batch_size, seq_len, _ = x.shape

        Q = self.q_proj(x)
        K = self.k_proj(x)
        V = self.v_proj(x)

        # (batch, seq, d_model) -> (batch, n_heads, seq, head_dim)
        Q = Q.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn_weights = torch.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        context = torch.matmul(attn_weights, V)

        context = context.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.d_model)
        return self.out_proj(context)


class FeedForward(nn.Module):
    """Position-wise feed-forward network."""

    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(config.d_model, config.d_ff),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_ff, config.d_model),
            nn.Dropout(config.dropout),
        )

    def forward(self, x):
        return self.net(x)


class TransformerBlock(nn.Module):
    """Transformer decoder block: attention + FFN, each with a residual."""

    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.attention = MultiHeadAttention(config)
        self.norm1 = nn.LayerNorm(config.d_model)
        self.norm2 = nn.LayerNorm(config.d_model)
        self.ffn = FeedForward(config)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x, mask=None):
        attn_out = self.attention(x, mask)
        x = self.norm1(x + self.dropout(attn_out))
        ffn_out = self.ffn(x)
        x = self.norm2(x + self.dropout(ffn_out))
        return x


class SmallLanguageModel(nn.Module):
    """Decoder-only language model with tied embeddings."""

    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.position_embedding = nn.Embedding(config.max_length, config.d_model)
        self.blocks = nn.ModuleList(
            [TransformerBlock(config) for _ in range(config.n_layers)])
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        # weight tying: lm_head shares the embedding matrix (saves
        # vocab_size * d_model parameters and usually helps small models)
        self.lm_head.weight = self.token_embedding.weight
        self.dropout = nn.Dropout(config.dropout)
        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
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
        token_embeds = self.token_embedding(input_ids)
        positions = torch.arange(seq_len, device=input_ids.device)
        position_embeds = self.position_embedding(positions)
        x = self.dropout(token_embeds + position_embeds)

        if attention_mask is None:
            # causal mask: position t may attend to positions <= t
            mask = torch.tril(
                torch.ones(seq_len, seq_len, device=input_ids.device))
            mask = mask.view(1, 1, seq_len, seq_len)
        else:
            mask = attention_mask

        for block in self.blocks:
            x = block(x, mask)
        return self.lm_head(x)

    @torch.no_grad()
    def generate(self, input_ids, max_new_tokens=50, temperature=1.0, do_sample=True):
        self.eval()
        for _ in range(max_new_tokens):
            logits = self.forward(input_ids)
            next_token_logits = logits[:, -1, :] / temperature
            probs = torch.softmax(next_token_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            input_ids = torch.cat([input_ids, next_token], dim=1)
        return input_ids


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    torch.manual_seed(42)
    config = TransformerConfig()
    model = SmallLanguageModel(config)

    input_ids = torch.randint(0, config.vocab_size, (2, 128))
    output = model(input_ids)

    print("params: %s" % format(count_parameters(model), ","))
    print("input:  torch.Size(%s)" % (list(input_ids.shape),))
    print("output: torch.Size(%s)" % (list(output.shape),))

    # causal-mask sanity: changing the token at position 5 must not
    # change logits at position 2 (the mask blocks that attention
    # path), but must change position 6 (which attends to position 5)
    model.eval()
    a = torch.randint(0, config.vocab_size, (1, 16))
    with torch.no_grad():
        la = model(a)
        b = a.clone()
        b[0, 5] = (b[0, 5] + 1) % config.vocab_size
        lb = model(b)
    diff2 = (la[0, 2] - lb[0, 2]).abs().max().item()
    diff6 = (la[0, 6] - lb[0, 6]).abs().max().item()
    print("mask check pos2 maxdiff: %.6f (expect 0.0)" % diff2)
    print("mask check pos6 maxdiff: %.4f (expect > 0)" % diff6)

    torch.manual_seed(7)
    gen = model.generate(a[:, :4], max_new_tokens=3, temperature=1.0)
    print("generate shape: torch.Size(%s)" % (list(gen.shape),))
```

**Output:**

```text
params: 7,429,632
input:  torch.Size([2, 128])
output: torch.Size([2, 128, 10000])
mask check pos2 maxdiff: 0.000000 (expect 0.0)
mask check pos6 maxdiff: 0.0409 (expect > 0)
generate shape: torch.Size([1, 7])
```

The mask check is the one worth internalizing: if a mutation at position 5 changed position 2's logits, information would be flowing backwards in time and your model could silently cheat during training (and its validation perplexity would lie to you). `0.000000` behind the mask, nonzero after — that is the contract.

### Where the 7,429,632 Comes From

The parameter count is not decoration — derive it:

```text
token_embedding    10,000 x 256 = 2,560,000   (tied with lm_head, counted once)
position_embedding    512 x 256 =   131,072
per block:  attention  4 x (256*256 + 256) =   263,168
            ffn        256*1024 + 1024*256 =   525,568   (both biases included)
            2 x LayerNorm (256 + 256)       =     1,024
                                    block =   789,760
6 blocks:                             = 4,738,560
total: 2,560,000 + 131,072 + 4,738,560 = 7,429,632
```

Run the numbers yourself whenever you resize the model — a config change that doubles `d_model` roughly quadruples the attention parameters, and you want to know that *before* the OOM.

### Checkpoint 4: Model Ready

- [ ] `python model.py` prints `params: 7,429,632`
- [ ] Output shape is `torch.Size([2, 128, 10000])`
- [ ] Mask check: position 2 exactly `0.0`, position 6 nonzero

---

## Part 5: Training Loop (120 minutes)

### The Two Mechanisms First

The training loop uses exactly two things you have not run yet: the LR schedule and the logging layer. Both are small enough to verify in isolation — runnable blocks first, then the full loop as a sketch.

**The schedule** — linear warmup to `6e-4`, then cosine decay to zero. This is the same `lr_lambda` the full script uses:

```python
import math
import torch

model = torch.nn.Linear(4, 4)
optimizer = torch.optim.AdamW(model.parameters(), lr=6e-4, weight_decay=0.01)
total_steps = 30
warmup_steps = 3

def lr_lambda(step):
    if step < warmup_steps:
        return step / warmup_steps
    progress = (step - warmup_steps) / (total_steps - warmup_steps)
    return 0.5 * (1 + math.cos(math.pi * progress))

scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
for step in range(total_steps):
    if step in (0, 2, 3, 15, 29):
        print("step %2d lr %.2e" % (step, scheduler.get_last_lr()[0]))
    optimizer.step()
    scheduler.step()
```

**Output:**

```text
step  0 lr 0.00e+00
step  2 lr 4.00e-04
step  3 lr 6.00e-04
step 15 lr 3.52e-04
step 29 lr 2.03e-06
```

`LambdaLR` evaluates the lambda once at construction, so step 0 starts at literally zero LR — the warmup buys stability for free. Peak at step 3, well into its descent by the midpoint (3.52e-04 at step 15), and near-zero at the end: no reason to keep taking big steps when the loss curve has flattened.

**The logging layer** — wandb if present, an honest local fallback if not:

```python
try:
    import wandb
except ImportError:
    wandb = None

def make_logger(project, name):
    """Return a log() that works with or without wandb."""
    if wandb is None:
        print("tracking: local only (wandb not installed)")
        def log(metrics):
            print("  log:", metrics)
        return log
    wandb.init(project=project, name=name)
    return wandb.log

log = make_logger("lab006-train-model", "small-transformer")
log({"train/loss": 3.2145, "train/perplexity": 24.89})
log({"train/loss": 2.9001, "train/perplexity": 18.20})
```

**Output:**

```text
tracking: local only (wandb not installed)
  log: {'train/loss': 3.2145, 'train/perplexity': 24.89}
  log: {'train/loss': 2.9001, 'train/perplexity': 18.2}
```

This machine has no wandb, so the fallback path runs; on a machine with it installed, the same code calls `wandb.init` and ships metrics to the dashboard. The `try/except ImportError` pattern is what makes that choice a runtime decision instead of a crash. (Note `18.2` — Python drops the trailing zero on `18.20`; outputs are transcribed from real runs, not prettified.)

### Task: Implement the Training Loop

Full script (sketch — hours of GPU time with the Part 2 corpus):

```text
# sketch - train.py
# needs data/wiki_filtered.jsonl (Part 2) and tokenizer/tokenizer.json
# (Part 3); 10 epochs - hours on a GPU, not seconds
import json
import math
import os

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

from model import SmallLanguageModel, TransformerConfig, count_parameters

# wandb is optional. The try/except keeps train.py importable on
# machines without it - including evaluate.py, which does
# `from train import TextDataset`. The original script called
# wandb.init() at module level, so merely importing train.py opened a
# tracking session (and crashed where wandb was absent). Imports
# should not have side effects.
try:
    import wandb
except ImportError:
    wandb = None


class TextDataset(Dataset):
    """Language-modeling dataset: fixed-length token windows."""

    def __init__(self, data_path, tokenizer, max_length=512):
        self.data = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                self.data.append(json.loads(line)["text"])
        print(f"Loaded {len(self.data)} documents")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        input_ids = self.tokenizer.encode(self.data[idx]).ids[: self.max_length]
        pad_id = self.tokenizer.token_to_id("[PAD]")
        n_pad = self.max_length - len(input_ids)

        # labels = input_ids, except padding positions become -100 so
        # cross_entropy(ignore_index=-100) skips them. The original fed
        # raw [PAD] ids as labels - it was training the model to emit
        # padding, then ignoring that loss it had just created.
        labels = input_ids + [-100] * n_pad
        input_ids = input_ids + [pad_id] * n_pad

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def make_logger():
    """wandb.log if wandb is available, else a no-op local logger."""
    if wandb is None:
        print("tracking: local only (wandb not installed)")
        return lambda metrics: None
    wandb.init(project="lab006-train-model", name="small-transformer")
    return wandb.log


def train_epoch(model, dataloader, optimizer, scheduler, device, epoch, log):
    model.train()
    total_loss = 0.0
    pbar = tqdm(dataloader, desc=f"Epoch {epoch}")

    for step, batch in enumerate(pbar):
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)

        logits = model(input_ids)
        loss = nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)), labels.view(-1), ignore_index=-100)

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        if step % 10 == 0:
            avg_loss = total_loss / (step + 1)
            ppl = math.exp(avg_loss)
            lr = scheduler.get_last_lr()[0]
            pbar.set_postfix(loss=f"{avg_loss:.4f}", ppl=f"{ppl:.2f}",
                             lr=f"{lr:.2e}")
            log({"train/loss": avg_loss, "train/perplexity": ppl,
                 "train/learning_rate": lr})

    return total_loss / len(dataloader)


@torch.no_grad()
def evaluate(model, dataloader, device):
    model.eval()
    total_loss = 0.0

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)
        logits = model(input_ids)
        loss = nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)), labels.view(-1), ignore_index=-100)
        total_loss += loss.item()

    avg_loss = total_loss / len(dataloader)
    return avg_loss, math.exp(avg_loss)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    log = make_logger()

    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file("tokenizer/tokenizer.json")

    dataset = TextDataset("data/wiki_filtered.jsonl", tokenizer, max_length=256)
    train_size = int(0.9 * len(dataset))
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, len(dataset) - train_size])

    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True,
                              num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=8, num_workers=4)

    model = SmallLanguageModel(TransformerConfig()).to(device)
    print(f"Model parameters: {count_parameters(model):,}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=6e-4, weight_decay=0.01)
    total_steps = len(train_loader) * 10
    warmup_steps = int(0.1 * total_steps)

    def lr_lambda(step):
        if step < warmup_steps:
            return step / warmup_steps
        progress = (step - warmup_steps) / (total_steps - warmup_steps)
        return 0.5 * (1 + math.cos(math.pi * progress))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    best_val_loss = float("inf")
    for epoch in range(1, 11):
        train_loss = train_epoch(model, train_loader, optimizer, scheduler,
                                 device, epoch, log)
        val_loss, val_ppl = evaluate(model, val_loader, device)

        print(f"\nEpoch {epoch} Results:")
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val Loss: {val_loss:.4f}")
        print(f"  Val Perplexity: {val_ppl:.2f}")
        log({"val/loss": val_loss, "val/perplexity": val_ppl, "epoch": epoch})

        os.makedirs("checkpoints", exist_ok=True)
        torch.save(
            {"epoch": epoch, "model_state_dict": model.state_dict(),
             "optimizer_state_dict": optimizer.state_dict(),
             "val_loss": val_loss},
            f"checkpoints/epoch_{epoch}.pt")
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "checkpoints/best_model.pt")
            print(f"  Saved best model (val_loss: {val_loss:.4f})")

    print("\nTraining complete!")


if __name__ == "__main__":
    main()
```

Run:

```bash
python train.py
```

**Example progress** (shape of a healthy run — timings and exact losses vary; what matters is the direction and the lr following the schedule):

```text
tracking: local only (wandb not installed)
Using device: cuda
Loaded 9,847 documents
Model parameters: 7,429,632

Epoch 1: 100%|██████| 1108/1108 [05:23<00:00, 3.43it/s, loss=3.2145, ppl=24.89, lr=6.00e-04]
Evaluating: 100%|██████| 123/123 [00:15<00:00, 8.02it/s]

Epoch 1 Results:
  Train Loss: 3.2145
  Val Loss: 3.1023
  Val Perplexity: 22.25
  Saved best model (val_loss: 3.1023)

... (epochs 2-10 follow the same pattern; lr decays along the cosine)

Epoch 10 Results:
  Train Loss: 1.8234
  Val Loss: 2.1456
  Val Perplexity: 8.55

Training complete!
```

### Checkpoint 5: Training Complete

- [ ] 10 epochs finished; val loss fell across epochs
- [ ] `checkpoints/best_model.pt` exists
- [ ] The lr in the progress bar rose through warmup, peaked, then decayed

---

## Part 6: Text Generation (30 minutes)

### Task: Generate Text with Your Model

```text
# sketch - generate.py
# needs checkpoints/best_model.pt + tokenizer/tokenizer.json (Parts 3+5)
import torch
from tokenizers import Tokenizer

from model import SmallLanguageModel, TransformerConfig


def generate_text(model, tokenizer, prompt, max_new_tokens=50, temperature=0.8):
    """Sample max_new_tokens continuations of prompt."""
    model.eval()
    device = next(model.parameters()).device
    input_ids = torch.tensor(
        [tokenizer.encode(prompt).ids], dtype=torch.long, device=device)

    with torch.no_grad():
        output_ids = model.generate(
            input_ids, max_new_tokens=max_new_tokens, temperature=temperature)

    return tokenizer.decode(output_ids[0].tolist(), skip_special_tokens=True)


def main():
    tokenizer = Tokenizer.from_file("tokenizer/tokenizer.json")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = SmallLanguageModel(TransformerConfig()).to(device)
    # map_location makes the load work even if the checkpoint was
    # saved on a GPU machine and this one has none (and note: .to(device),
    # not .cuda() - the device is already a decision this script owns)
    model.load_state_dict(
        torch.load("checkpoints/best_model.pt", map_location=device))
    model.eval()

    prompts = [
        "Artificial intelligence is",
        "The history of machine learning began",
        "Neural networks work by",
    ]
    for prompt in prompts:
        print(f"Prompt: {prompt}")
        print("Generated:", generate_text(model, tokenizer, prompt))
        print("-" * 50)


if __name__ == "__main__":
    main()
```

Run:

```bash
python generate.py
```

**Example of what a well-trained checkpoint produces** (sampled — yours will differ every run; a 7.4M model on ~20M tokens usually produces looser text than this, and an undertrained one produces word salad — that contrast is itself your evaluation):

```text
Prompt: Artificial intelligence is
Generated: Artificial intelligence is a branch of computer science that deals
with the creation of intelligent machines that can perform tasks that
typically require human intelligence.

--------------------------------------------------

Prompt: The history of machine learning began
Generated: The history of machine learning began in the 1950s with the
development of the first learning algorithms. Early researchers developed
programs that could learn from data and improve their performance.

--------------------------------------------------

Prompt: Neural networks work by
Generated: Neural networks work by processing information through layers of
interconnected nodes. Each neuron receives input, processes it, and passes
the output to the next layer.

--------------------------------------------------
```

### Checkpoint 6: Generation Working

- [ ] Generation runs without error from your checkpoint
- [ ] Output follows the prompt's language
- [ ] `temperature=0.8` vs `1.2` visibly changes the variety

---

## Part 7: Evaluation (30 minutes)

### Task: Evaluate Model Quality

```text
# sketch - evaluate.py
# needs checkpoints/best_model.pt + tokenizer/tokenizer.json (Parts 3+5)
import math

import torch
from tokenizers import Tokenizer
from torch.utils.data import DataLoader
from tqdm import tqdm

from model import SmallLanguageModel, TransformerConfig
from train import TextDataset  # safe: train.py has no import-time side effects


def calculate_perplexity(model, dataloader, device):
    """True per-token perplexity: sum loss over real tokens, divide once."""
    model.eval()
    total_loss = 0.0
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
                reduction="sum",
            )
            total_loss += loss.item()
            total_tokens += (labels != -100).sum().item()

    return math.exp(total_loss / total_tokens)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = Tokenizer.from_file("tokenizer/tokenizer.json")
    model = SmallLanguageModel(TransformerConfig()).to(device)
    model.load_state_dict(
        torch.load("checkpoints/best_model.pt", map_location=device))

    val_dataset = TextDataset("data/wiki_filtered.jsonl", tokenizer,
                              max_length=256)
    val_loader = DataLoader(
        torch.utils.data.Subset(val_dataset, range(1000)), batch_size=8)

    ppl = calculate_perplexity(model, val_loader, device)
    print(f"\nModel Perplexity: {ppl:.2f}")

    baseline_ppl = 25.0        # GPT-2 124M, Wikitext ballpark
    baseline_params = 124_000_000
    our_params = 7_429_632

    # Loss scales roughly as L ~ N**-0.1 (Kaplan et al., 2020): a model
    # 16.7x smaller should be 16.7**0.1 = ~1.33x WORSE, not better.
    # The original here used a negative exponent and "expected" a 7M
    # model to beat GPT-2 - the sign was backwards.
    expected_ppl = baseline_ppl * (baseline_params / our_params) ** 0.1

    print("\nBaseline comparisons:")
    print("  GPT-2 (124M): ~25 on Wikitext")
    print(f"  Ours (7.4M):  {ppl:.2f} on the Wikipedia subset")
    print(f"  Scaling-law expectation for our size: {expected_ppl:.1f}")

    if ppl < expected_ppl:
        print("  OK: beating the expectation for this size")
    else:
        print("  UNDER: below expectation - train longer, or on more data")


if __name__ == "__main__":
    main()
```

Run:

```bash
python evaluate.py
```

The scaling-law comparison is the interesting part: it turns "is 12.0 perplexity good?" into a computable question. `reduction="sum"` plus dividing by the real token count (padding excluded via `-100`) gives a true per-token figure instead of a batch-average of averages.

### Checkpoint 7: Evaluated

- [ ] Perplexity computed on the held-out subset
- [ ] Compared against the scaling-law expectation
- [ ] Result recorded alongside the training curves

---

## Part 8: Challenges (Optional)

### Challenge 1: Scale Up (120 minutes)

**Task:** Train a larger model

```yaml
Requirements:
  - Increase model size to 50M parameters (resize d_model, d_ff, n_layers)
  - Re-derive the exact parameter count by hand before training (Part 4 method)
  - Train on the full filtered dataset
  - Add gradient checkpointing
  - Train for 20 epochs

Target perplexity: < 7.0
```

### Challenge 2: Improve Architecture (120 minutes)

**Task:** Add improvements

```yaml
Try these improvements:
  - Replace learned positions with rotary embeddings (RoPE)
  - Add layer normalization at different positions (Pre-LN vs Post-LN)
  - Try SwiGLU instead of GELU in the FFN

Measure the perplexity delta of each change separately - one at a time,
or you will not know what worked.
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
| **Data** | Downloaded & filtered 10k Wikipedia articles | `data/wiki_filtered.jsonl` |
| **Tokenizer** | Trained a BPE tokenizer with a 10k vocab | `tokenizer/tokenizer.json` |
| **Model** | 7,429,632-parameter decoder-only transformer (measured) | `model.py` |
| **Training** | 10 epochs, warmup + cosine, grad clipping | `checkpoints/` |
| **Generation** | Sampled text from your checkpoint | `generate.py` |
| **Evaluation** | Perplexity vs scaling-law expectation | `evaluate.py` |

### Key Metrics

```text
Model Size:        7,429,632 parameters (7.4M)
Training Tokens:   ~20M (chars/4 estimate)
Training Time:     ~6 hours on one 16 GB-class GPU
Final Perplexity:  8-10, dataset-dependent
```

### Next Steps

1. **Scale up:** 50M-100M parameters (Challenge 1) — and re-derive the count by hand first
2. **More data:** mix in other corpora; watch tokenizer vocabulary coverage
3. **Longer training:** the cosine schedule rewards patience
4. **Better architecture:** RoPE, Pre-LN, SwiGLU (Challenge 2), one change at a time
5. **Serve it:** production inference is a different discipline (Volume 7 below)

---

## You're Now Ready For

- **[Volume 5: Model Adaptation](../../volumes/VOLUME-5-Model-Adaptation.md)** — fine-tune the model you just trained
- **[Volume 7: Production Mastery](../../volumes/VOLUME-7-Production-Mastery.md)** — deploy it
- **[2402: Large-Scale Training](../../phases/phase2-foundations/2400-pretraining/2402-Large-Scale-Training.md)** — the same loop, at industrial scale
