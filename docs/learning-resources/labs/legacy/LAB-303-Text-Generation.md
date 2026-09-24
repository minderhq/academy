# LAB-303: Text Generation

## Overview
Implement greedy search, beam search, and sampling for text generation.

## Prerequisites
- LAB-201 completed

## Setup

```bash
pip install torch transformers
```

## Exercise 1: Greedy Decoding

```python
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# TODO: Load model
model = GPT2LMHeadModel.from_pretrained('gpt2')
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

model.eval()

# TODO: Greedy generation
prompt = "The future of artificial intelligence"
inputs = tokenizer(prompt, return_tensors='pt')

# Generate
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        do_sample=False  # Greedy
    )

generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"Greedy:\n{generated}\n")
```

## Exercise 2: Beam Search

```python
# TODO: Beam search generation
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        num_beams=5,      # Number of beams
        do_sample=False,
        early_stopping=True,
        no_repeat_ngram_size=2
    )

generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"Beam Search (beams=5):\n{generated}\n")

# TODO: Compare different beam widths
for num_beams in [1, 3, 5, 10]:
    outputs = model.generate(
        **inputs,
        max_new_tokens=30,
        num_beams=num_beams,
        do_sample=False,
        early_stopping=True
    )
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Beams={num_beams}: {text[:80]}...")
```

## Exercise 3: Top-k Sampling

```python
# TODO: Top-k sampling
for k in [1, 10, 50, 100]:
    outputs = model.generate(
        **inputs,
        max_new_tokens=30,
        do_sample=True,
        top_k=k,
        temperature=0.7
    )
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Top-k={k}: {text[:80]}...")
```

## Exercise 4: Nucleus (Top-p) Sampling

```python
# TODO: Nucleus sampling
for p in [0.1, 0.5, 0.9, 0.95, 0.99]:
    outputs = model.generate(
        **inputs,
        max_new_tokens=30,
        do_sample=True,
        top_p=p,
        temperature=0.7
    )
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Top-p={p}: {text[:80]}...")
```

## Exercise 5: Temperature

```python
# TODO: Temperature effect
for temp in [0.1, 0.5, 0.7, 1.0, 1.5]:
    outputs = model.generate(
        **inputs,
        max_new_tokens=30,
        do_sample=True,
        temperature=temp,
        top_k=50
    )
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Temp={temp}: {text[:80]}...")
```

## Exercise 6: Combined Strategy

```python
def generate_with_strategy(prompt, max_tokens=30, strategy='greedy', **kwargs):
    """Generate with specified strategy."""

    if strategy == 'greedy':
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False
        )
    elif strategy == 'beam':
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            num_beams=kwargs.get('num_beams', 5),
            do_sample=False,
            early_stopping=True
        )
    elif strategy == 'sampling':
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=kwargs.get('temperature', 0.7),
            top_k=kwargs.get('top_k', 50),
            top_p=kwargs.get('top_p', 0.9)
        )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# TODO: Compare strategies
strategies = [
    {'strategy': 'greedy'},
    {'strategy': 'beam', 'num_beams': 5},
    {'strategy': 'sampling', 'temperature': 0.7, 'top_k': 50},
    {'strategy': 'sampling', 'temperature': 1.2, 'top_k': 50},
]

for config in strategies:
    text = generate_with_strategy(prompt, **config)
    print(f"\n{config}:")
    print(f"  {text[:100]}...")
```

## Exercise 7: Visualization

```python
import matplotlib.pyplot as plt
import numpy as np

def compare_strategies():
    """Compare different generation strategies."""

    strategies = ['greedy', 'beam_3', 'beam_5', 'top50', 'top100']
    outputs = []

    # Generate samples
    for strategy in strategies:
        if strategy == 'greedy':
            out = model.generate(**inputs, max_new_tokens=30, do_sample=False)
        elif 'beam' in strategy:
            beams = int(strategy.split('_')[1])
            out = model.generate(**inputs, max_new_tokens=30, num_beams=beams, do_sample=False)
        elif 'top' in strategy:
            k = int(strategy[3:])
            out = model.generate(**inputs, max_new_tokens=30, do_sample=True, top_k=k, temperature=0.7)

        text = tokenizer.decode(out[0], skip_special_tokens=True)
        outputs.append(text)

    # Display
    for strategy, text in zip(strategies, outputs):
        print(f"\n{strategy.upper()}:")
        print(f"  {text}")

# TODO: Run comparison
compare_strategies()
```

## Expected Outputs

1. Exercise 1: Greedy generation
2. Exercise 2: Beam search produces better quality
3. Exercise 3: Top-k adds diversity
4. Exercise 4: Top-p controls nucleus
5. Exercise 5: Temperature controls randomness
6. Exercise 6: Combined strategies work
7. Exercise 7: Comparison visible

## Time Estimate: 2-3 hours
