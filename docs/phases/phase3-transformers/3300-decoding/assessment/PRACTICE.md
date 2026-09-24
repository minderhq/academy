---
Document ID: 3300-PRACTICE
Title: "3300: Decoding - Practice"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
---

# 3300: Decoding - Practice

## Exercises

### Exercise 1: Implement Greedy Decoding

```python
import torch
import torch.nn.functional as F

def greedy_decode(model, input_ids, max_new_tokens=50, eos_token_id=None):
    """
    Greedy decoding: Always pick the most likely next token.

    Args:
        model: Language model with forward() returning logits
        input_ids: Input token IDs (batch_size, seq_len)
        max_new_tokens: Maximum number of tokens to generate
        eos_token_id: End-of-sequence token ID (if None, use model.config.eos_token_id)

    Returns:
        Generated token IDs
    """
    if eos_token_id is None:
        eos_token_id = getattr(model.config, 'eos_token_id', None)

    generated = input_ids.clone()

    for step in range(max_new_tokens):
        # Forward pass
        with torch.no_grad():
            outputs = model(generated)

        # Get next token logits (last position)
        logits = outputs[:, -1, :] if outputs.dim() == 3 else outputs[:, -1:]

        # Convert to probabilities
        probs = F.softmax(logits, dim=-1)

        # Greedy selection: pick token with highest probability
        next_token = torch.argmax(probs, dim=-1, keepdim=True)

        # Append to sequence
        generated = torch.cat([generated, next_token], dim=1)

        # Check for EOS
        if eos_token_id is not None and next_token.item() == eos_token_id:
            break

    return generated

# Test with a simple model
from transformers import GPT2LMHeadModel, GPT2Tokenizer

print("Loading GPT-2 model...")
model = GPT2LMHeadModel.from_pretrained("gpt2")
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Ensure pad token is set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Test greedy decoding
prompt = "The future of artificial intelligence"
input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"]

print(f"\nPrompt: \"{prompt}\"")
print("Generating with greedy decoding...")

output_ids = greedy_decode(model, input_ids, max_new_tokens=30, eos_token_id=tokenizer.eos_token_id)
text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

print(f"\nGenerated text:\n{text}\n")

# Expected Output:
# Coherent text continuation, but may be repetitive
# Greedy decoding often gets stuck in repetitive loops
```

**Explanation:**
- Greedy decoding always selects the highest probability token
- Fast but can lead to repetitive or suboptimal text
- No exploration of alternative paths

**Pros:** Simple, deterministic, fast
**Cons:** Can get stuck in loops, misses better sequences

---

### Exercise 2: Implement Beam Search

```python
import heapq
import torch
import torch.nn.functional as F

def beam_search(model, input_ids, num_beams=5, max_new_tokens=50, eos_token_id=None):
    """
    Beam search: Maintain top-k most likely sequences at each step.

    Args:
        model: Language model
        input_ids: Input token IDs
        num_beams: Number of beams to maintain
        max_new_tokens: Maximum tokens to generate
        eos_token_id: End-of-sequence token ID

    Returns:
        Best generated sequence
    """
    if eos_token_id is None:
        eos_token_id = getattr(model.config, 'eos_token_id', None)

    batch_size = input_ids.shape[0]

    # Initialize beams with input sequence
    beams = [(0.0, input_ids.clone())]  # (score, sequence)

    for step in range(max_new_tokens):
        new_beams = []
        all_finished = True

        for score, seq in beams:
            # Check if this beam has finished
            if eos_token_id is not None and seq[0, -1].item() == eos_token_id:
                new_beams.append((score, seq))
                continue

            all_finished = False

            # Forward pass
            with torch.no_grad():
                outputs = model(seq)

            # Get logits for next token
            logits = outputs[:, -1, :] if outputs.dim() == 3 else outputs[:, -1:]
            log_probs = F.log_softmax(logits, dim=-1)

            # Get top-k tokens and their log probabilities
            topk_log_probs, topk_ids = torch.topk(log_probs, num_beams, dim=-1)

            # Expand beam: create new sequences for each top-k token
            for i in range(num_beams):
                new_score = score + topk_log_probs[0, i].item()
                new_seq = torch.cat([seq, topk_ids[0, i:i+1]], dim=1)
                new_beams.append((new_score, new_seq))

        # Keep top-k beams overall
        beams = heapq.nlargest(num_beams, new_beams, key=lambda x: x[0])

        # Normalize scores by sequence length to avoid bias toward shorter sequences
        beams = [(score / (seq.shape[1] ** 0.7), seq) for score, seq in beams]

        # Check if all beams finished
        if all_finished:
            break

    # Return best sequence (highest score)
    best_beam = max(beams, key=lambda x: x[0])
    return best_beam[1]

# Test beam search
print("Testing Beam Search")
print("="*60)

for num_beams in [1, 3, 5]:
    output_ids = beam_search(
        model,
        input_ids.clone(),
        num_beams=num_beams,
        max_new_tokens=30,
        eos_token_id=tokenizer.eos_token_id
    )
    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    print(f"\nBeam size {num_beams}:")
    print(f"{text}")

# Expected Output:
# Beam search typically produces more coherent text than greedy
# More beams = better quality but slower
# Beam size 1 is equivalent to greedy decoding
```

**Explanation:**
- Beam search keeps multiple candidate sequences
- Explores more possibilities than greedy
- Length normalization prevents preference for short sequences

**Pros:** Better quality than greedy, still efficient
**Cons:** Can still be repetitive, more compute than greedy

---

### Exercise 3: Implement Top-k Sampling

```python
import torch
import torch.nn.functional as F

def top_k_sampling(model, input_ids, top_k=50, temperature=0.7, max_new_tokens=50, eos_token_id=None):
    """
    Top-k sampling: Sample from top-k most likely tokens.

    Args:
        model: Language model
        input_ids: Input token IDs
        top_k: Number of top tokens to sample from
        temperature: Sampling temperature (lower = more deterministic)
        max_new_tokens: Maximum tokens to generate
        eos_token_id: End-of-sequence token ID

    Returns:
        Generated token IDs
    """
    if eos_token_id is None:
        eos_token_id = getattr(model.config, 'eos_token_id', None)

    generated = input_ids.clone()

    for step in range(max_new_tokens):
        # Forward pass
        with torch.no_grad():
            outputs = model(generated)

        # Get logits and apply temperature
        logits = outputs[:, -1, :] if outputs.dim() == 3 else outputs[:, -1:]
        logits = logits / temperature

        # Get top-k logits and indices
        top_k_logits, top_k_ids = torch.topk(logits, top_k, dim=-1)

        # Convert to probabilities
        probs = F.softmax(top_k_logits, dim=-1)

        # Sample from top-k
        next_token_idx = torch.multinomial(probs, num_samples=1)
        next_token = torch.gather(top_k_ids, -1, next_token_idx)

        # Append to sequence
        generated = torch.cat([generated, next_token], dim=1)

        # Check for EOS
        if eos_token_id is not None and next_token.item() == eos_token_id:
            break

    return generated

# Test top-k sampling
print("\nTesting Top-k Sampling")
print("="*60)

for top_k in [10, 50, 100]:
    output_ids = top_k_sampling(
        model,
        input_ids.clone(),
        top_k=top_k,
        temperature=0.8,
        max_new_tokens=30,
        eos_token_id=tokenizer.eos_token_id
    )
    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    print(f"\nTop-k={top_k}:")
    print(f"{text}")

# Expected Output:
# Lower k (e.g., 10) = more focused, less diverse
# Higher k (e.g., 100) = more diverse, potentially less coherent
# More creative than greedy/beam search
```

**Explanation:**
- Top-k sampling restricts sampling to top-k most likely tokens
- Temperature controls randomness (lower = more deterministic)
- Introduces diversity while maintaining quality

**Temperature Effects:**
- Low temperature (0.1-0.5): More deterministic, focused
- Medium temperature (0.7-1.0): Balanced diversity and coherence
- High temperature (1.5-2.0): Very diverse, potentially incoherent

---

### Exercise 4: Implement Nucleus Sampling

```python
def nucleus_sampling(model, input_ids, top_p=0.9, temperature=0.7, max_new_tokens=50, eos_token_id=None):
    """
    Nucleus (top-p) sampling: Sample from smallest set of tokens with cumulative probability >= top_p.

    Args:
        model: Language model
        input_ids: Input token IDs
        top_p: Cumulative probability threshold (0.0 to 1.0)
        temperature: Sampling temperature
        max_new_tokens: Maximum tokens to generate
        eos_token_id: End-of-sequence token ID

    Returns:
        Generated token IDs
    """
    if eos_token_id is None:
        eos_token_id = getattr(model.config, 'eos_token_id', None)

    generated = input_ids.clone()

    for step in range(max_new_tokens):
        # Forward pass
        with torch.no_grad():
            outputs = model(generated)

        # Get logits and apply temperature
        logits = outputs[:, -1, :] if outputs.dim() == 3 else outputs[:, -1:]
        logits = logits / temperature

        # Sort by probability (descending)
        sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
        sorted_probs = F.softmax(sorted_logits, dim=-1)

        # Calculate cumulative probabilities
        cumulative_probs = torch.cumsum(sorted_probs, dim=-1)

        # Remove tokens beyond top_p threshold
        # Always keep at least one token
        sorted_indices_to_remove = cumulative_probs >= top_p
        sorted_indices_to_remove[..., 0:] = cumulative_probs[..., 0:] >= top_p
        sorted_indices_to_remove[..., 0] = False  # Keep at least the top token

        # Set logits of removed tokens to -inf
        sorted_logits[sorted_indices_to_remove] = float('-inf')

        # Convert back to probabilities and sample
        probs = F.softmax(sorted_logits, dim=-1)
        next_token_idx = torch.multinomial(probs, num_samples=1)
        next_token = torch.gather(sorted_indices, -1, next_token_idx)

        # Append to sequence
        generated = torch.cat([generated, next_token], dim=1)

        # Check for EOS
        if eos_token_id is not None and next_token.item() == eos_token_id:
            break

    return generated

# Test nucleus sampling
print("\nTesting Nucleus (Top-p) Sampling")
print("="*60)

for top_p in [0.5, 0.9, 0.95]:
    output_ids = nucleus_sampling(
        model,
        input_ids.clone(),
        top_p=top_p,
        temperature=0.8,
        max_new_tokens=30,
        eos_token_id=tokenizer.eos_token_id
    )
    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    print(f"\nTop-p={top_p}:")
    print(f"{text}")

# Expected Output:
# Lower p (0.5) = very focused, less diverse
# Higher p (0.95) = more diverse, adaptive vocabulary
# Often better than top-k as it adapts to distribution
```

**Explanation:**
- Nucleus sampling adaptively selects vocabulary based on cumulative probability
- More flexible than fixed top-k
- Adapts to the probability distribution of each step

**Comparison Top-k vs Nucleus:**
- Top-k: Fixed vocabulary size
- Nucleus: Adaptive vocabulary size
- Nucleus often produces better quality text

---

### Exercise 5: Compare All Methods

```python
def compare_decoding_methods(model, tokenizer, prompt, max_new_tokens=30):
    """
    Compare different decoding methods side-by-side.
    """
    input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"]

    methods = {
        'Greedy': lambda: greedy_decode(model, input_ids.clone(), max_new_tokens, tokenizer.eos_token_id),
        'Beam (k=3)': lambda: beam_search(model, input_ids.clone(), 3, max_new_tokens, tokenizer.eos_token_id),
        'Beam (k=5)': lambda: beam_search(model, input_ids.clone(), 5, max_new_tokens, tokenizer.eos_token_id),
        'Top-k (k=50)': lambda: top_k_sampling(model, input_ids.clone(), 50, 0.8, max_new_tokens, tokenizer.eos_token_id),
        'Nucleus (p=0.9)': lambda: nucleus_sampling(model, input_ids.clone(), 0.9, 0.8, max_new_tokens, tokenizer.eos_token_id),
    }

    results = {}

    for method_name, method_fn in methods.items():
        try:
            output_ids = method_fn()
            text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
            results[method_name] = text
        except Exception as e:
            results[method_name] = f"Error: {e}"

    return results

# Run comparison
print("\n" + "="*70)
print("COMPREHENSIVE DECODING METHOD COMPARISON")
print("="*70)

prompts = [
    "The future of artificial intelligence is",
    "Once upon a time",
    "In a galaxy far, far away"
]

for prompt in prompts:
    print(f"\n{'='*70}")
    print(f"Prompt: \"{prompt}\"")
    print(f"{'='*70}")

    results = compare_decoding_methods(model, tokenizer, prompt, max_new_tokens=25)

    for method, text in results.items():
        print(f"\n{method}:")
        print(f"  {text[:200]}")
        if len(text) > 200:
            print("  [...]")

# Analysis
print("\n\n" + "="*70)
print("ANALYSIS OF DECODING METHODS")
print("="*70)

print("""
1. GREEDY DECODING
   - Pros: Fast, deterministic
   - Cons: Repetitive, can get stuck in loops
   - Use when: Speed is critical, deterministic output needed

2. BEAM SEARCH
   - Pros: Better quality than greedy, still efficient
   - Cons: Can still be repetitive, more compute
   - Use when: Quality matters, want some diversity control
   - Beam size: 1=growth, 3-5=typical, 10+=high quality but slow

3. TOP-k SAMPLING
   - Pros: Introduces diversity, controlled randomness
   - Cons: Fixed vocabulary size may be suboptimal
   - Use when: Want creative but controlled text
   - k values: 10=focused, 50=balanced, 100=diverse

4. NUCLEUS (TOP-p) SAMPLING
   - Pros: Adaptive vocabulary, often best quality
   - Cons: Can be unpredictable at extremes
   - Use when: Want natural, diverse text
   - p values: 0.5=focused, 0.9=balanced, 0.95=very diverse

RECOMMENDATIONS:
- For factual/explanatory text: Beam search (k=5)
- For creative writing: Nucleus (p=0.9) with temperature=0.8-1.0
- For code generation: Beam search (k=3-5) with low temperature
- For chatbots: Nucleus (p=0.9) with temperature=0.7-0.9
""")

# Expected Output:
# Each method produces different continuations
# Beam search: most coherent but possibly repetitive
# Sampling methods: more diverse and creative
```

---

## Bonus: Advanced Techniques

### Repetition Penalty

```python
def sample_with_repetition_penalty(model, input_ids, temperature=0.7,
                                    repetition_penalty=1.0, max_new_tokens=50):
    """
    Add repetition penalty to discourage repeating tokens.
    """
    generated = input_ids.clone()

    for step in range(max_new_tokens):
        with torch.no_grad():
            outputs = model(generated)

        logits = outputs[:, -1, :] if outputs.dim() == 3 else outputs[:, -1:]
        logits = logits / temperature

        # Apply repetition penalty
        if repetition_penalty > 1.0:
            # Get token IDs in generated sequence
            for token_id in generated[0].unique():
                logits[0, token_id] /= repetition_penalty

        # Sample
        probs = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)

        generated = torch.cat([generated, next_token], dim=1)

        if next_token.item() == tokenizer.eos_token_id:
            break

    return generated

# Test repetition penalty
print("\nTesting Repetition Penalty")
print("="*60)

for penalty in [1.0, 1.2, 1.5]:
    output_ids = sample_with_repetition_penalty(
        model, input_ids.clone(),
        temperature=0.8,
        repetition_penalty=penalty,
        max_new_tokens=30
    )
    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    print(f"\nPenalty={penalty}:")
    print(text[:200])
```

**Key Takeaways:**

1. **Greedy**: Fast but repetitive
2. **Beam Search**: Better quality, still efficient
3. **Top-k Sampling**: Controlled diversity
4. **Nucleus Sampling**: Adaptive, often best
5. **Repetition Penalty**: Prevents loops

**Production Tips:**
- Use beam search for factual content
- Use nucleus sampling for creative tasks
- Adjust temperature based on desired diversity
- Add repetition penalty for longer generations
- Monitor output quality and adjust parameters

---

**Last Updated:** 2026-02-05
