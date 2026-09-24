---
Document ID: 4202
Title: Speculative Decoding - Accelerating Large Models
Phase: 4
Module: 4200
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'kv-cache', 'context-window', 'speculative-decoding']
---

# 4202: Speculative Decoding - Accelerating Large Models

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Intuition](#the-intuition)
- [Algorithm](#algorithm)
- [Draft Model Selection](#draft-model-selection)
- [Performance Analysis](#performance-analysis)
- [Advanced Techniques](#advanced-techniques)
- [Implementation Tips](#implementation-tips)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain the reasoning behind The Intuition
- Explain Algorithm
- Explain Draft Model Selection
- Measure and evaluate Performance Analysis
- Explain Advanced Techniques
- Apply Implementation Tips

---

## Abstract
Speculative decoding uses a smaller "draft" model to predict tokens that a larger "target" model verifies. This can achieve 2-3x speedup with minimal quality loss.

## The Intuition

### Standard Decoding
```text
For each token:
  1. Run full model (expensive!)
  2. Sample token
  3. Repeat

Bottleneck: Full model for EVERY token
```

### Speculative Decoding
```text
1. Draft model (small, fast) predicts N tokens
2. Target model (large, accurate) verifies all N at once
3. Accept tokens that match
4. If mismatch: target model predicts correct token

Key insight: Most draft predictions are correct!
Result: 1 target model run → multiple tokens
```

## Algorithm

### Standard Speculative Decoding
```python
def speculative_decode(
    draft_model,
    target_model,
    input_ids,
    max_new_tokens=100,
    speculation_len=8  # Number of draft tokens
):
    """
    Speculative decoding with draft model
    """
    generated = input_ids
    total_tokens = 0

    while total_tokens < max_new_tokens:
        # 1. Draft model predicts K tokens
        draft_tokens = []
        draft_input = generated

        for _ in range(speculation_len):
            with torch.no_grad():
                logits = draft_model(draft_input)
            next_token = logits[:, -1:].argmax(dim=-1)
            draft_tokens.append(next_token)
            draft_input = torch.cat([draft_input, next_token], dim=-1)

        # 2. Target model verifies all K tokens at once
        with torch.no_grad():
            # Run target model once
            target_logits = target_model(draft_input)

        # 3. Accept/reject each token
        accepted = 0
        for i, draft_token in enumerate(draft_tokens):
            target_logit = target_logits[:, i + len(generated) - 1, :]

            # Sample from target
            target_token_sampled = torch.multinomial(
                torch.softmax(target_logit, dim=-1), 1
            )

            if target_token_sampled == draft_token:
                accepted += 1
            else:
                # Reject: resample from target
                draft_tokens[i] = target_token_sampled
                break

        # 4. Append accepted tokens
        generated = torch.cat([generated] + draft_tokens[:accepted], dim=-1)
        total_tokens += accepted

        # If rejected early, also add the corrected token
        if accepted < speculation_len:
            if accepted < len(draft_tokens):
                generated = torch.cat([generated, draft_tokens[accepted]], dim=-1)
                total_tokens += 1

    return generated
```

### Multinomial Speculative Sampling
```python
def speculative_sampling(
    draft_logits,
    target_logits,
    n_speculative_tokens=8
):
    """
    More sophisticated: use full probability distributions

    Key: Accept draft token with probability p/q
    p: Target probability of draft token
    q: Draft probability of draft token
    """
    batch_size, vocab_size = target_logits.shape

    # Convert to probabilities
    draft_probs = torch.softmax(draft_logits, dim=-1)
    target_probs = torch.softmax(target_logits, dim=-1)

    # Sample draft tokens
    draft_tokens = torch.multinomial(draft_probs, 1)

    # Get probabilities for sampled tokens
    draft_token_probs = draft_probs.gather(1, draft_tokens)
    target_token_probs = target_probs.gather(1, draft_tokens)

    # Acceptance probability: min(1, p/q)
    acceptance_prob = torch.clamp(
        target_token_probs / (draft_token_probs + 1e-10),
        max=1.0
    )

    # Accept or reject
    uniform = torch.rand(batch_size, 1, device=draft_logits.device)
    accepted = uniform < acceptance_prob

    # If rejected, resample from target (with correction)
    corrected_tokens = draft_tokens.clone()
    corrected_probs = target_probs.clone()

    # For rejected positions: sample from adjusted distribution
    rejected_mask = ~accepted
    if rejected_mask.any():
        # Residual distribution: max(0, p - q)
        residual = torch.clamp(
            target_probs - draft_probs,
            min=0
        )
        residual = residual / residual.sum(dim=-1, keepdim=True)

        corrected_tokens[rejected_mask] = torch.multinomial(
            residual[rejected_mask.squeeze(1)], 1
        )

    return corrected_tokens, accepted
```

## Draft Model Selection

### Model Size Comparison
```yaml
Target Model: Llama-2-70B
Draft Options:
  - TinyLlama-1B    (50x smaller, ~30x faster)
  - Llama-2-7B      (10x smaller, ~8x faster)
  - Llama-2-13B     (5x smaller, ~4x faster)

Trade-off:
  - Smaller draft: Faster but less accurate (lower acceptance)
  - Larger draft: Slower but more accurate (higher acceptance)

Sweet spot: ~10% of target model size
  - 70B target → 7B draft
```

### Training Draft Models
```python
# Train draft model to match target model
# Loss: KL divergence between distributions

def train_draft_model(
    draft_model,
    target_model,
    train_dataloader,
    epochs=1
):
    """
    Train draft model to mimic target model
    """
    optimizer = torch.optim.Adam(draft_model.parameters(), lr=1e-5)

    for epoch in range(epochs):
        for batch in train_dataloader:
            input_ids = batch['input_ids']

            # Get target distribution (no grad)
            with torch.no_grad():
                target_logits = target_model(input_ids)
                target_probs = torch.softmax(target_logits, dim=-1)

            # Get draft distribution
            draft_logits = draft_model(input_ids)
            draft_probs = torch.softmax(draft_logits, dim=-1)

            # KL divergence loss
            kl_loss = (target_probs * (torch.log(target_probs + 1e-10) -
                                       torch.log(draft_probs + 1e-10))).sum(dim=-1).mean()

            # Backward
            optimizer.zero_grad()
            kl_loss.backward()
            optimizer.step()

    return draft_model
```

## Performance Analysis

### Theoretical Speedup
```text
Speedup = 1 / (P_accept × T_draft + (1 - P_accept) × T_target)

Where:
  P_accept: Probability draft is correct
  T_draft: Time for draft model (relative to target)
  T_target: Time for target model

Example:
  Draft is 10x faster (T_draft = 0.1)
  Acceptance rate = 80% (P_accept = 0.8)

  Speedup = 1 / (0.8 × 0.1 + 0.2 × 1)
          = 1 / (0.08 + 0.2)
          = 1 / 0.28
          = 3.57x

Actual speedup: ~2-3x (overhead not accounted)
```

### Acceptance Rate Factors
```python
# What affects acceptance rate?

factors = {
    "Draft quality": "Better draft → higher acceptance",
    "Temperature": "Lower temp → higher acceptance",
    "Speculation length": "Shorter → higher acceptance",
    "Domain match": "Similar training data → higher acceptance",
}

# Measured acceptance rates (Llama-2-7B as target):
# TinyLlama-1B draft:     60-70%
# Llama-2-7B distilled:  85-90%
# Llama-2-13B draft:      90-95%
```

## Advanced Techniques

### Lookahead Decoding
```python
def lookahead_speculative_decode(
    target_model,
    input_ids,
    lookahead_tokens=4
):
    """
    Speculative decode using model's own predictions
    No separate draft model needed!
    """
    generated = input_ids

    while len(generated[0]) < input_ids.shape[1] + 100:
        # 1. Generate K tentative tokens
        tentative = []
        current_input = generated

        with torch.no_grad():
            for _ in range(range(lookahead_tokens)):
                logits = target_model(current_input)
                next_token = logits[:, -1:].argmax(dim=-1)
                tentative.append(next_token)
                current_input = torch.cat([current_input, next_token], dim=-1)

        # 2. Verify in one pass
        with torch.no_grad():
            # Get all logits
            all_logits = target_model(current_input)

        # 3. Accept tokens that match
        for i, tentative_token in enumerate(tentative):
            actual_token = all_logits[:, len(generated) + i, :].argmax(dim=-1, keepdim=True)

            if actual_token == tentative_token:
                generated = torch.cat([generated, actual_token], dim=-1)
            else:
                # Mismatch: add correct and restart
                generated = torch.cat([generated, actual_token], dim=-1)
                break

    return generated
```

### Parallel Speculative Decoding
```python
# Generate multiple draft sequences in parallel
def parallel_speculative_decode(
    draft_model,
    target_model,
    input_ids,
    num_drafts=4
):
    """
    Run multiple draft chains in parallel
    Accept best one according to target model
    """
    # Generate multiple drafts
    drafts = []
    for _ in range(num_drafts):
        draft = generate_sequence(draft_model, input_ids, max_tokens=8)
        drafts.append(draft)

    # Score all drafts with target model
    scores = []
    for draft in drafts:
        with torch.no_grad():
            logits = target_model(draft)
            log_prob = torch.log_softmax(logits, dim=-1)
            scores.append(log_prob.sum().item())

    # Accept best draft
    best_idx = np.argmax(scores)
    return drafts[best_idx]
```

### Medusa Sampling
```python
class MedusaHeads(nn.Module):
    """
    Multiple prediction heads for speculative decoding
    No separate draft model needed!
    """
    def __init__(self, hidden_size, vocab_size, num_heads=4):
        super().__init__()
        self.heads = nn.ModuleList([
            nn.Linear(hidden_size, vocab_size)
            for _ in range(num_heads)
        ])

    def forward(self, hidden_states):
        """
        Predict next N tokens from current position
        Each head predicts offset by its index
        """
        predictions = []
        for head in self.heads:
            predictions.append(head(hidden_states))

        return predictions

# Integration with model
# Add MedusaHeads to each layer
# During inference: use all heads to speculate
# Verify with target model
```

## Implementation Tips

### Optimize Speculation Length
```python
def find_optimal_speculation_length(draft_model, target_model, test_prompts):
    """
    Find best speculation length for your setup
    """
    results = {}

    for spec_len in [2, 4, 6, 8, 12, 16]:
        times = []
        accepted = []

        for prompt in test_prompts:
            start = time.time()
            output, accept_rate = speculative_decode(
                draft_model, target_model, prompt, speculation_len=spec_len
            )
            times.append(time.time() - start)
            accepted.append(accept_rate)

        results[spec_len] = {
            'time': np.mean(times),
            'acceptance': np.mean(accepted),
            'speedup': baseline_time / np.mean(times)
        }

    return results

# Typical results:
# spec_len=4: 2.5x speedup, 85% acceptance
# spec_len=8: 3.0x speedup, 70% acceptance
# spec_len=12: 2.8x speedup, 55% acceptance
# spec_len=16: 2.5x speedup, 45% acceptance
# Optimal: 8-12 for most cases
```

### KV Cache Management
```python
# Speculative decoding needs careful KV cache handling

class SpeculativeKVCache:
    """
    KV cache optimized for speculative decoding
    """
    def __init__(self):
        self.draft_cache = None
        self.target_cache = None
        self.accepted_positions = []

    def update_draft(self, layer, key, value):
        """Update draft model cache"""
        if self.draft_cache is None:
            self.draft_cache = {}

        if layer not in self.draft_cache:
            self.draft_cache[layer] = {'k': [], 'v': []}

        self.draft_cache[layer]['k'].append(key)
        self.draft_cache[layer]['v'].append(value)

    def commit_accepted(self, accepted_count):
        """
        Move accepted tokens from draft to target cache
        """
        for layer in self.draft_cache:
            for i in range(accepted_count):
                self.target_cache[layer]['k'].append(
                    self.draft_cache[layer]['k'][i]
                )
                self.target_cache[layer]['v'].append(
                    self.draft_cache[layer]['v'][i]
                )

        # Clear draft cache
        for layer in self.draft_cache:
            self.draft_cache[layer] = {'k': [], 'v': []}
```

---

## References

### Related ai-engineering-curriculum Documents

- [4201: Context Window Physics and OOM Prevention](4201-Context-Window-Physics.md)

---

## Next Steps

- Next Module: **[4300: QAT](../4300-quantization-aware-training/)**
- Continue with: **[4301: QAT Foundations](../4300-quantization-aware-training/4301-QAT-Foundations.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**
- [4201: Context Window](./4201-Context-Window-Physics.md)
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [3102: Flash Attention](../../phase3-transformers/3100-attention/3102-Flash-Attention.md)

**Experiment Template:** `experiments/EXP_4202_SPECULATIVE_DECODING.md`
