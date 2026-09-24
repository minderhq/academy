---
Document ID: 3202
Title: Tokenizer Sciences - BPE, SentencePiece, and Tiktoken
Phase: 3
Module: 3200
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'embeddings', 'rope', 'tokenization', 'bpe']
---

# 3202: Tokenizer Sciences - BPE, SentencePiece, and Tiktoken

## Abstract
Tokenizers convert text into numerical inputs for language models. The choice of tokenizer affects vocabulary size, sequence length, model size, and multilingual capability.

## Tokenization Pipeline

```
Raw Text
    ↓
Normalization (lowercase, accent removal)
    ↓
Pre-tokenization (split on whitespace/punctuation)
    ↓
Model (BPE/Unigram/WordPiece)
    ↓
Post-processing (add special tokens)
    ↓
Token IDs
```

## Byte-Pair Encoding (BPE)

### Algorithm Overview
```
BPE iteratively merges the most frequent pair of characters/tokens.

Starting: "h u g h u g h u g"
Step 1: Merge "u" + "g" → "ug"
        "h ug h ug h ug"
Step 2: Merge "h" + "ug" → "hug"
        "hug hug hug"
Step 3: Merge "hug" + "hug" → "hug×2"
        "hug×2 hug"

Final vocabulary: {h, u, g, ug, hug, hug×2}
```

### BPE Implementation
```python
import re
from collections import defaultdict

class BPETokenizer:
    def __init__(self, vocab_size=1000):
        self.vocab_size = vocab_size
        self.vocab = {}  # merge rules: (pair) -> merged_token
        self.merges = []

    def get_stats(self, vocab):
        """
        Count frequency of each symbol pair
        vocab: {token: count}
        """
        pairs = defaultdict(int)
        for token, freq in vocab.items():
            symbols = token.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i+1])] += freq
        return pairs

    def merge_vocab(self, vocab, pair):
        """
        Merge the most frequent pair
        """
        new_vocab = {}
        bigram = ' '.join(pair)
        replacement = ''.join(pair)

        for token in vocab:
            new_token = token.replace(bigram, replacement)
            new_vocab[new_token] = vocab[token]
        return new_vocab

    def train(self, corpus):
        """
        Train BPE on corpus
        corpus: list of strings
        """
        # Pre-tokenize: split into characters
        vocab = defaultdict(int)
        for text in corpus:
            tokens = ' '.join(list(text))
            vocab[tokens] += 1

        # Iteratively merge
        for i in range(self.vocab_size - len(vocab)):
            pairs = self.get_stats(vocab)
            if not pairs:
                break
            best_pair = max(pairs, key=pairs.get)
            vocab = self.merge_vocab(vocab, best_pair)
            self.merges.append(best_pair)

        # Build vocab dict
        for token in vocab:
            for subword in token.split():
                if subword not in self.vocab:
                    self.vocab[subword] = len(self.vocab)

    def encode(self, text):
        """
        Encode text to token IDs
        """
        # Start with characters
        tokens = list(text)

        # Apply merges
        while len(tokens) > 1:
            pairs = [(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]

            # Find first applicable merge
            merged = False
            for pair in self.merges:
                if pair in pairs:
                    i = pairs.index(pair)
                    tokens = tokens[:i] + [''.join(pair)] + tokens[i+2:]
                    merged = True
                    break

            if not merged:
                break

        return [self.vocab.get(t, self.vocab.get('<unk>')) for t in tokens]

# Usage
corpus = ["hug", "pug", "pun", "bun", "hugs"]
tokenizer = BPETokenizer(vocab_size=20)
tokenizer.train(corpus)
encoded = tokenizer.encode("hug")
```

### GPT-2 BPE Details
```python
# GPT-2 uses a modified BPE with these rules:
# 1. Regex for pre-tokenization
GPT2_PATTERN = r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

# 2. Byte-level encoding (handles any Unicode)
def bytes_to_unicode():
    """
    Returns list of unicode characters for bytes
    Maps first 256 unicode characters to bytes
    """
    bs = list(range(256))
    cs = list(range(256))
    n = 0
    for b in range(256):
        if b in range(33, 127) or b in [9, 10, 13]:
            cs[b] = b
        else:
            cs[b] = 256 + n
            n += 1
    return [chr(c) for c in cs]
```

## SentencePiece (Unigram Language Model)

### Unigram Tokenization
```
Unlike BPE (bottom-up), Unigram is top-down:

1. Start with large vocabulary
2. Compute loss for removing each token
3. Remove token with minimum increase in loss
4. Repeat until target vocabulary size

Key difference: Can tokenize ambiguous strings differently
  "unbreakable" → "un", "break", "able"
  "unfriendly" → "un", "friendly"
```

### SentencePiece Implementation
```python
# pip install sentencepiece
import sentencepiece as spm

# Train SentencePiece model
spm.SentencePieceTrainer.train(
    input_corpus='corpus.txt',
    model_prefix='mymodel',
    vocab_size=10000,
    model_type='unigram',  # or 'bpe', 'word', 'char'
    character_coverage=0.995,
    input_sentence_size=10000000,
    shuffle_input_sentence=True,
)

# Load and use
sp = spm.SentencePieceProcessor(model_file='mymodel.model')

# Encode
ids = sp.encode('Hello world', out_type=int)
tokens = sp.encode('Hello world', out_type=str)

# Decode
text = sp.decode(ids)

# Special tokens
sp.pad_id()  # <pad>
sp.unk_id()  # <unk>
sp.bos_id()  # <s>
sp.eos_id()  # </s>
```

### SentencePiece Features
```python
# 1. Handles whitespace explicitly
# "Hello world" → "▁Hello", "▁world"
# ▁ is the whitespace token

# 2. User-defined symbols
spm.SentencePieceTrainer.train(
    input_corpus='corpus.txt',
    model_prefix='mymodel',
    vocab_size=10000,
    user_defined_symbols=['[CLS]', '[SEP]', '[MASK]'],
)

# 3. Controlled vocabulary
# Specify exact tokens to include
```

## Tiktoken (OpenAI)

### Tiktoken Design
```
Tiktoken is OpenAI's tokenizer for GPT-3.5/4:
- Byte-level BPE
- Optimized for code + text
- Efficient implementation (Rust)
```

### Using Tiktoken
```python
# pip install tiktoken
import tiktoken

# Load encoding
enc = tiktoken.get_encoding("cl100k_base")  # GPT-4
# or tiktoken.encoding_for_model("gpt-4")

# Encode
tokens = enc.encode("Hello, world!")
# [15496, 11, 1917, 0]

# Decode
text = enc.decode(tokens)

# Count tokens
len(enc.encode("Your text here"))

# Tokenize with offsets
enc.encode("hello world", allowed_special={"<|endoftext|>"})

# Different encodings:
# gpt2: GPT-2
# r50k_base: GPT-3 base
# p50k_base: GPT-3 (code aware)
# cl100k_base: GPT-4 (100k vocab)
```

### Tiktoken Implementation
```python
# Tiktoken merges are optimized for:
# 1. Code: Programming language tokens
# 2. Multilingual: Non-English text
# 3. Efficiency: Faster encoding/decoding

# Example: Python code
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

tokens = enc.encode(code)
# Each keyword, identifier, operator often single token
```

## Tokenizer Comparison

| Tokenizer | Model | Vocab Size | Multilingual | Code Support |
|-----------|-------|------------|--------------|--------------|
| BPE (GPT-2) | GPT-2 | 50k | ✗ | Limited |
| BPE (GPT-4) | GPT-4 | 100k | ✓ | ✓ |
| SentencePiece | T5, mT5 | 32k-250k | ✓ | ✗ |
| Unigram | ALBERT, BERT | 30k | ✓ | ✗ |
| WordPiece | BERT | 30k | Limited | ✗ |

### Token Efficiency Comparison
```python
import tiktoken

# Test different tokenizers
texts = [
    "Hello world",  # English
    "你好世界",  # Chinese
    "def foo(): return 1",  # Code
    "Lorem ipsum dolor sit amet",  # Latin
]

# GPT-4 tokenizer
enc_cl100k = tiktoken.get_encoding("cl100k_base")

# GPT-2 tokenizer
enc_gpt2 = tiktoken.get_encoding("gpt2")

for text in texts:
    gpt4_tokens = len(enc_cl100k.encode(text))
    gpt2_tokens = len(enc_gpt2.encode(text))
    print(f"'{text}'")
    print(f"  GPT-4: {gpt4_tokens}, GPT-2: {gpt2_tokens}")
```

## Special Tokens

### Common Special Tokens
```python
# BERT-style
special_tokens = {
    '[PAD]': 0,  # Padding
    '[UNK]': 1,  # Unknown
    '[CLS]': 2,  # Classification token
    '[SEP]': 3,  # Separator
    '[MASK]': 4, # Mask for MLM
}

# GPT-style
special_tokens = {
    '<|endoftext|>': 50256,  # End of text
    '<|startoftranscript|>': 50362,
    '<|translate|>': 50358,
}

# T5-style
special_tokens = {
    '<pad>': 0,
    '<eos>': 1,
    '<unk>': 2,
}
```

### Adding Special Tokens
```python
# Add special tokens to tokenizer
tokenizer.add_special_tokens({
    'pad_token': '<pad>',
    'eos_token': '<eos>',
    'bos_token': '<bos>',
    'unk_token': '<unk>',
    'mask_token': '<mask>',
})

# Resize model embeddings
model.resize_token_embeddings(len(tokenizer))
```

## Training Custom Tokenizer

### From Scratch (HuggingFace)
```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Initialize tokenizer
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
trainer = BpeTrainer(
    special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"],
    vocab_size=30000,
    min_frequency=2,
)

# Pre-tokenizer
tokenizer.pre_tokenizer = Whitespace()

# Train
files = ["corpus1.txt", "corpus2.txt"]
tokenizer.train(files, trainer)

# Save
tokenizer.save("tokenizer.json")
```

### Using 🤗 Datasets
```python
from datasets import load_dataset
from tokenizers import Tokenizer, models, trainers, pre_tokenizers

# Load dataset
dataset = load_dataset("wikitext", "wikitext-103-raw")

def batch_iterator(batch_size=1000):
    for i in range(0, len(dataset["train"]), batch_size):
        yield dataset["train"][i:i+batch_size]["text"]

# Train
tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))
trainer = trainers.BpeTrainer(
    vocab_size=50000,
    special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"],
)
tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()

tokenizer.train_from_iterator(
    batch_iterator(),
    trainer=trainer,
    len=len(dataset["train"])
)
```

## Tokenizer Metrics

### Vocabulary Coverage
```python
def calculate_coverage(tokenizer, text):
    """
    Calculate what fraction of tokens are in vocabulary
    """
    encoded = tokenizer.encode(text)
    total = len(encoded.tokens)
    unknown = sum(1 for t in encoded.tokens if t == "<unk>")

    coverage = (total - unknown) / total
    return coverage

# Test on domain-specific text
legal_text = load_legal_corpus()
coverage = calculate_coverage(tokenizer, legal_text)
print(f"Coverage on legal text: {coverage:.2%}")
```

### Token Length Analysis
```python
def analyze_token_lengths(tokenizer, texts):
    """
    Analyze token length distribution
    """
    lengths = [len(tokenizer.encode(t)) for t in texts]

    return {
        'mean': sum(lengths) / len(lengths),
        'median': sorted(lengths)[len(lengths)//2],
        'max': max(lengths),
        'min': min(lengths),
    }

# Compare tokenizers
for tokenizer_name in ["gpt2", "cl100k_base", "bert-base-uncased"]:
    tokenizer = load_tokenizer(tokenizer_name)
    stats = analyze_token_lengths(tokenizer, test_texts)
    print(f"{tokenizer_name}: {stats}")
```

---

## Next Steps

- Next Module: **[3300: Decoding](../3300-decoding/)**
- Continue with: **[3301: Activation Functions](../3300-decoding/3301-Activation-Functions.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [3201: RoPE](./3201-Rotary-Positional-Embeddings-RoPE.md)
- [3101: Self-Attention](../3100-attention/3101-Self-Attention-DeepDive.md)
- [6201: Hybrid Search](../../phase6-rag/6200-retrieval/6201-Hybrid-Search.md)

**Experiment Template:** `experiments/EXP_3202_TOKENIZER.md`
