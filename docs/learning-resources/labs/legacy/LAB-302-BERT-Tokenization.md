# LAB-302: BERT Tokenization

## Overview
Learn BERT-style tokenization with WordPiece.

## Prerequisites
- LAB-201 completed

## Setup

```bash
pip install transformers tokenizers
```

## Exercise 1: Basic Tokenization

```python
from transformers import AutoTokenizer

# TODO: Load BERT tokenizer
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')

# Sample texts
texts = [
    "Hello, world!",
    "Machine learning is fascinating.",
    "I love natural language processing."
]

# TODO: Tokenize
for text in texts:
    tokens = tokenizer.tokenize(text)
    ids = tokenizer.convert_tokens_to_ids(tokens)

    print(f"Text: {text}")
    print(f"Tokens: {tokens}")
    print(f"IDs: {ids}")
    print()
```

## Exercise 2: Special Tokens

```python
# TODO: Check special tokens
print(f"PAD token: {tokenizer.pad_token} (ID: {tokenizer.pad_token_id})")
print(f"UNK token: {tokenizer.unk_token} (ID: {tokenizer.unk_token_id})")
print(f"CLS token: {tokenizer.cls_token} (ID: {tokenizer.cls_token_id})")
print(f"SEP token: {tokenizer.sep_token} (ID: {tokenizer.sep_token_id})")
print(f"MASK token: {tokenizer.mask_token} (ID: {tokenizer.mask_token_id})")

# TODO: Tokenize with special tokens
text = "Hello world!"
encoded = tokenizer(text, return_tensors='pt')

print(f"\nEncoded input IDs: {encoded['input_ids']}")
print(f"Attention mask: {encoded['attention_mask']}")
print(f"Token type IDs: {encoded['token_type_ids']}")

# TODO: Decode back
decoded = tokenizer.decode(encoded['input_ids'][0])
print(f"Decoded: {decoded}")
```

## Exercise 3: Padding and Truncation

```python
# TODO: Tokenize with padding and truncation
texts = [
    "Short text.",
    "This is a much longer text that should demonstrate padding when combined with other texts of different lengths.",
    "Medium length text example."
]

# TODO: Pad to max length
encoded = tokenizer(
    texts,
    padding=True,          # Pad to longest
    truncation=True,       # Truncate if too long
    max_length=32,         # Max length
    return_tensors='pt'
)

print(f"Input IDs shape: {encoded['input_ids'].shape}")  # [3, 32]
print(f"Attention mask:\n{encoded['attention_mask']}")

# TODO: Count padding tokens
for i, (text, ids, mask) in enumerate(zip(texts,
                                           encoded['input_ids'],
                                           encoded['attention_mask'])):
    pad_count = (mask == 0).sum().item()
    actual_len = mask.sum().item()
    print(f"\nText {i+1}: {text}")
    print(f"  Actual length: {actual_len}, Padding: {pad_count}")
```

## Exercise 4: Batch Encoding

```python
# TODO: Create a dataset
class TextDataset(torch.utils.data.Dataset):
    def __init__(self, texts, tokenizer, max_length=128):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]

        # TODO: Tokenize
        encoded = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoded['input_ids'].squeeze(0),
            'attention_mask': encoded['attention_mask'].squeeze(0)
        }

# TODO: Create dataset and dataloader
texts = [
    "The capital of France is Paris.",
    "Machine learning is a subset of artificial intelligence.",
    "Python is a popular programming language."
] * 10

dataset = TextDataset(texts, tokenizer, max_length=64)
dataloader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=True)

# TODO: Iterate
for batch_idx, batch in enumerate(dataloader):
    print(f"\nBatch {batch_idx + 1}:")
    print(f"  Input IDs shape: {batch['input_ids'].shape}")
    print(f"  Attention mask shape: {batch['attention_mask'].shape}")

    if batch_idx >= 2:
        break
```

## Exercise 5: WordPiece Analysis

```python
# TODO: Analyze WordPiece vocabulary
vocab_size = tokenizer.vocab_size
print(f"Vocabulary size: {vocab_size}")

# TODO: Find subword tokens
word = "unbelievable"
tokens = tokenizer.tokenize(word)
print(f"\nWord: {word}")
print(f"Tokens: {tokens}")

# TODO: Count vocabulary tokens by length
from collections import Counter

token_lengths = Counter([len(token) for token in tokenizer.vocab.keys()])
print(f"\nToken length distribution:")
for length in sorted(token_lengths.keys())[:10]:
    count = token_lengths[length]
    print(f"  Length {length}: {count} tokens")
```

## Expected Outputs

1. Exercise 1: Tokens split with WordPiece
2. Exercise 2: Special tokens identified
3. Exercise 3: Padding applied correctly
4. Exercise 4: Batches encoded
5. Exercise 5: Subword breakdown visible

## Time Estimate: 2-3 hours
