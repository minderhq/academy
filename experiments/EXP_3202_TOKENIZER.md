# EXP_3202: Tokenizer Performance Experiments

## Overview
Practical experiments for understanding tokenizer performance, vocabulary efficiency, and tokenization strategies.

## Experiment 1: Tokenizer Comparison

### Objective
Compare different tokenizers on speed and efficiency.

### Script
```python
# tokenizer_comparison.py
import time
from transformers import AutoTokenizer
from datasets import load_dataset
import matplotlib.pyplot as plt

def compare_tokenizers():
    """Compare different tokenizer implementations"""

    tokenizers = {
        "GPT-2": "gpt2",
        "Llama-2": "meta-llama/Llama-2-7b-hf",
        "Mistral": "mistralai/Mistral-7B-v0.1",
        "T5": "t5-base",
        "Bert": "bert-base-uncased",
    }

    # Test texts
    test_texts = {
        "English": "The quick brown fox jumps over the lazy dog.",
        "Code": "def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
        "Numbers": "The year 2024 had 365 days and PI is approximately 3.14159265359",
        "URL": "Visit https://example.com/path?param=value for more information",
        "Long": "This is a longer text that contains multiple sentences. " * 10,
    }

    results = {}

    for name, model_id in tokenizers.items():
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")

        tokenizer = AutoTokenizer.from_pretrained(model_id)
        results[name] = {
            "vocab_size": len(tokenizer),
            "texts": {}
        }

        for text_type, text in test_texts.items():
            # Tokenize
            tokens = tokenizer.encode(text)
            decoded = tokenizer.decode(tokens, skip_special_tokens=True)

            # Measure speed
            start = time.time()
            for _ in range(1000):
                _ = tokenizer.encode(text)
            encode_time = (time.time() - start) / 1000 * 1000  # ms

            start = time.time()
            for _ in range(1000):
                _ = tokenizer.decode(tokens, skip_special_tokens=True)
            decode_time = (time.time() - start) / 1000 * 1000  # ms

            results[name]["texts"][text_type] = {
                "tokens": len(tokens),
                "chars": len(text),
                "compression": len(text) / len(tokens),
                "encode_ms": encode_time,
                "decode_ms": decode_time,
                "reversible": text == decoded,
            }

            print(f"  {text_type}:")
            print(f"    Tokens: {len(tokens):4d} | Chars: {len(text):4d} | "
                  f"Ratio: {len(text)/len(tokens):.2f}")
            print(f"    Encode: {encode_time:.3f}ms | Decode: {decode_time:.3f}ms")

    # Summary table
    print(f"\n{'='*60}")
    print("SUMMARY - Token Count by Text Type")
    print(f"{'='*60}")

    header = f"{'Tokenizer':<15} | " + " | ".join([f"{k:<8}" for k in test_texts.keys()])
    print(header)
    print("-" * 60)

    for name in results:
        row = f"{name:<15} | "
        for text_type in test_texts:
            count = results[name]["texts"][text_type]["tokens"]
            row += f"{count:<8} | "
        print(row)

    return results


if __name__ == "__main__":
    compare_tokenizers()
```

---

## Experiment 2: Tokenization Analysis

### Objective
Analyze how different tokenizers handle edge cases.

### Script
```python
# tokenization_analysis.py
from transformers import AutoTokenizer
import matplotlib.pyplot as plt

def analyze_tokenization_patterns():
    """Analyze tokenization patterns across models"""

    tokenizers = {
        "GPT-2": AutoTokenizer.from_pretrained("gpt2"),
        "Llama-2": AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf"),
        "Mistral": AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1"),
    }

    # Edge cases
    edge_cases = {
        "Numbers": ["123", "123456", "1.23", "1,234.56"],
        "Words": ["hello", "Hello", "HELLO", "hello!"],
        "Special": ["@user", "#hashtag", "$100", "C++"],
        "Spaces": ["hello world", "hello  world", "hello\nworld"],
        "Code": ["var_name", "function_name()", "a+b=c"],
        "URLs": ["https://example.com", "example.com/path"],
    }

    results = {}

    for tokenizer_name, tokenizer in tokenizers.items():
        results[tokenizer_name] = {}

        for category, examples in edge_cases.items():
            results[tokenizer_name][category] = []

            for example in examples:
                tokens = tokenizer.encode(example)
                token_strs = [tokenizer.decode([t]) for t in tokens]
                results[tokenizer_name][category].append({
                    "input": example,
                    "tokens": tokens,
                    "token_strs": token_strs,
                    "count": len(tokens),
                })

                # Print detailed analysis
                print(f"{tokenizer_name} | {category}: '{example}'")
                print(f"  Tokens ({len(tokens)}): {token_strs}")

    return results


if __name__ == "__main__":
    analyze_tokenization_patterns()
```

---

## Experiment 3: Subword Regularization

### Objective
Test BPE dropout and other regularization methods.

### Script
```python
# subword_regularization.py
import torch
from transformers import AutoTokenizer
import numpy as np

def test_bpe_dropout():
    """Test BPE dropout effects"""

    # Load tokenizer with BPE dropout support
    tokenizer = AutoTokenizer.from_pretrained("facebook/galactica-1.3b")

    text = "The mitochondria is the powerhouse of the cell"

    # Test different dropout rates
    dropout_rates = [0.0, 0.1, 0.2, 0.3, 0.5]

    results = {}

    for dropout in dropout_rates:
        tokenizations = []

        # Sample multiple times
        for _ in range(10):
            # Apply dropout (simulated - actual implementation varies)
            tokens = tokenizer.encode(text)
            tokenizations.append(len(tokens))

        results[dropout] = {
            "mean": np.mean(tokenizations),
            "std": np.std(tokenizations),
            "min": min(tokenizations),
            "max": max(tokenizations),
        }

        print(f"Dropout {dropout:.1f}: "
              f"Mean tokens: {results[dropout]['mean']:.1f} ± "
              f"{results[dropout]['std']:.2f}")

    return results


if __name__ == "__main__":
    test_bpe_dropout()
```

---

## Experiment 4: Multilingual Tokenization

### Objective
Compare multilingual tokenizer efficiency.

### Script
```python
# multilingual_tokenization.py
from transformers import AutoTokenizer

def compare_multilingual_tokenizers():
    """Compare multilingual tokenizer performance"""

    tokenizers = {
        "XLM-R": "xlm-roberta-base",
        "mT5": "google/mt5-base",
        "BLOOM": "bigscience/bloom-560m",
        "LLaMA": "meta-llama/Llama-2-7b-hf",  # Not multilingual but for comparison
    }

    # Texts in different languages
    texts = {
        "English": "The quick brown fox jumps over the lazy dog.",
        "Spanish": "El rápido zorro marrón salta sobre el perro perezoso.",
        "French": "Le renard brun rapide saute par-dessus le chien paresseux.",
        "German": "Der schnelle braune Fuchs springt über den faulen Hund.",
        "Turkish": "Hızlı kahverengi fox tembel köpeğin üzerinden atlar.",
        "Chinese": "快速的棕色狐狸跳过懒狗。",
        "Japanese": "素早い茶色の狐が怠惰な犬を飛び越える。",
        "Arabic": "الثعلب البني السريع يقفز فوق الكلب الكسول.",
        "Code": "def hello_world(): print('Hello, World!')",
    }

    results = {}

    for name, model_id in tokenizers.items():
        print(f"\n{name}:")
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        results[name] = {}

        for lang, text in texts.items():
            tokens = tokenizer.encode(text)
            chars = len(text)
            ratio = chars / len(tokens) if tokens else 0

            results[name][lang] = {
                "tokens": len(tokens),
                "chars": chars,
                "ratio": ratio,
            }

            print(f"  {lang}: {len(tokens):3d} tokens / {chars:3d} chars = {ratio:.2f}")

    return results


if __name__ == "__main__":
    compare_multilingual_tokenizers()
```

---

## Experiment 5: Custom Tokenizer Training

### Objective
Train a custom tokenizer on domain-specific data.

### Script
```python
# train_custom_tokenizer.py
from tokenizers import Tokenizer, models, trainers, pre_tokenizers
from datasets import load_dataset
import os

def train_custom_tokenizer():
    """Train a custom BPE tokenizer"""

    # Load dataset
    dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train")

    # Initialize tokenizer
    tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))
    tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()

    # Special tokens
    special_tokens = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]

    # Trainer
    trainer = trainers.BpeTrainer(
        vocab_size=32000,
        special_tokens=special_tokens,
        min_frequency=2,
    )

    # Train
    print("Training custom tokenizer...")
    tokenizer.train_from_iterator(
        dataset["text"],
        trainer=trainer,
        length=len(dataset)
    )

    # Save
    tokenizer.save("custom_tokenizer.json")
    print("Saved to: custom_tokenizer.json")

    return tokenizer


if __name__ == "__main__":
    train_custom_tokenizer()
```

---

## Expected Results

### Token Count Comparison

| Text | GPT-2 | Llama-2 | Mistral | T5 | Best |
|------|-------|---------|---------|-----|------|
| English prose | ~25 | ~22 | ~21 | ~35 | Mistral |
| Python code | ~40 | ~35 | ~33 | ~55 | Mistral |
| Numbers | ~15 | ~12 | ~11 | ~20 | Mistral |
| URLs | ~30 | ~25 | ~23 | ~45 | Mistral |

### Encoding Speed (tokens/ms)

| Tokenizer | Encode | Decode | Notes |
|-----------|--------|--------|-------|
| GPT-2 | 0.05 | 0.03 | Fastest |
| Llama-2 | 0.08 | 0.05 | Fast |
| Mistral | 0.07 | 0.04 | Fast |
| T5 | 0.12 | 0.08 | Slower |

### Multilingual Efficiency

| Language | XLM-R | mT5 | LLaMA-2 |
|----------|-------|-----|---------|
| English | 1.0x | 0.8x | 1.0x |
| Spanish | 1.0x | 1.0x | 1.5x |
| Chinese | 1.0x | 1.0x | 2.5x |
| Arabic | 1.0x | 1.0x | 3.0x |
| Code | 1.2x | 1.5x | 1.0x |

---

## Experiment Checklist

- [ ] Tokenizer speed comparison
- [ ] Token efficiency analysis
- [ ] Edge case handling
- [ ] Multilingual support
- [ ] Special token handling
- [ ] Reversible encoding test
- [ ] BPE dropout effects
- [ ] Custom tokenizer training
- [ ] Vocabulary size impact
- [ ] Merge rules analysis

---

## Related Documentation
- [3202: Tokenizer Sciences](../docs/3000-Transformer-Physics/3200-Embeddings/3202-Tokenizer-Sciences.md)
- [3402: Decoder-Only Models](../docs/3000-Transformer-Physics/3400-Model-Architectures/3402-Decoder-Only-Models.md)
