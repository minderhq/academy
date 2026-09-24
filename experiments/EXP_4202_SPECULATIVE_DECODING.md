# EXP_4202: Speculative Decoding Experiments

## Overview
Practical experiments for Speculative Decoding (also known as Draft-Verify or Assisted Generation) on an 11GB-class GPU.

## Experiment 1: Speculative Decoding Implementation

### Objective
Implement speculative decoding from scratch.

### Implementation
```python
# speculative_decoding.py
import torch
import torch.nn as nn
from typing import Tuple
from time import time

class SpeculativeDecoder:
    """
    Speculative Decoding with draft model

    Uses a smaller draft model to predict multiple tokens,
    then verifies them with the larger target model.
    """

    def __init__(
        self,
        target_model: nn.Module,
        draft_model: nn.Module,
        tokenizer,
        gamma: int = 5,  # Number of draft tokens
    ):
        self.target_model = target_model
        self.draft_model = draft_model
        self.tokenizer = tokenizer
        self.gamma = gamma

        # Set models to eval mode
        self.target_model.eval()
        self.draft_model.eval()

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
    ) -> str:
        """
        Generate using speculative decoding

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        # Encode prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")

        generated = input_ids.clone()
        draft_tokens = 0
        accepted_tokens = 0
        total_target_steps = 0

        for _ in range(max_new_tokens // self.gamma):
            # Step 1: Draft model generates gamma tokens
            draft_ids = self._draft_generate(generated, self.gamma, temperature)
            draft_tokens += self.gamma

            # Step 2: Target model verifies draft tokens
            accepted_ids, n_accepted = self._verify_tokens(
                generated, draft_ids, temperature
            )
            accepted_tokens += n_accepted
            total_target_steps += 1  # Target runs once per gamma tokens

            # Step 3: Append accepted tokens
            generated = torch.cat([generated, accepted_ids], dim=1)

            # If fewer than gamma tokens accepted, need to sample from target
            if n_accepted < self.gamma:
                # Sample one token from target model
                next_token = self._sample_from_target(generated, temperature)
                generated = torch.cat([generated, next_token], dim=1)
                total_target_steps += 1

            # Stop if EOS
            if generated[0, -1].item() == self.tokenizer.eos_token_id:
                break

        # Decode
        output = self.tokenizer.decode(generated[0], skip_special_tokens=True)

        # Stats
        acceptance_rate = accepted_tokens / draft_tokens if draft_tokens > 0 else 0
        speedup = self.gamma * acceptance_rate

        return output, {
            "draft_tokens": draft_tokens,
            "accepted_tokens": accepted_tokens,
            "acceptance_rate": acceptance_rate,
            "target_steps": total_target_steps,
            "theoretical_speedup": speedup,
        }

    def _draft_generate(
        self, input_ids: torch.Tensor, n_tokens: int, temperature: float
    ) -> torch.Tensor:
        """Generate n tokens using draft model"""
        draft_ids = input_ids.clone()

        for _ in range(n_tokens):
            outputs = self.draft_model(draft_ids)
            logits = outputs.logits[:, -1, :] / temperature

            # Sample
            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)

            draft_ids = torch.cat([draft_ids, next_token], dim=1)

            if next_token.item() == self.tokenizer.eos_token_id:
                break

        return draft_ids[:, input_ids.shape[1]:]

    def _verify_tokens(
        self,
        input_ids: torch.Tensor,
        draft_ids: torch.Tensor,
        temperature: float,
    ) -> Tuple[torch.Tensor, int]:
        """
        Verify draft tokens using target model

        Returns accepted tokens and count
        """
        # Concatenate input + draft
        full_ids = torch.cat([input_ids, draft_ids], dim=1)

        # Get target model logits
        outputs = self.target_model(full_ids)
        logits = outputs.logits[:, input_ids.shape[1]-1:-1, :] / temperature

        # Get draft model logits for same positions
        draft_outputs = self.draft_model(full_ids)
        draft_logits = draft_outputs.logits[:, input_ids.shape[1]-1:-1, :] / temperature

        # Compare probabilities
        target_probs = torch.softmax(logits, dim=-1)
        draft_probs = torch.softmax(draft_logits, dim=-1)

        # Find acceptance point
        accepted = []
        for i in range(draft_ids.shape[1]):
            t = i if i < draft_ids.shape[1] else draft_ids.shape[1] - 1
            token_id = draft_ids[:, t].item()

            # Get probabilities for this token
            target_p = target_probs[:, t, token_id].item()
            draft_p = draft_probs[:, t, token_id].item()

            # Accept or reject
            if target_p >= draft_p:
                accepted.append(draft_ids[:, t:t+1])
            else:
                # Resample from target distribution
                resampled = torch.multinomial(target_probs[:, t], num_samples=1)
                accepted.append(resampled)
                break

        if accepted:
            accepted_ids = torch.cat(accepted, dim=1)
        else:
            accepted_ids = torch.zeros(1, 0, dtype=torch.long, device=input_ids.device)

        return accepted_ids, len(accepted)

    def _sample_from_target(
        self, input_ids: torch.Tensor, temperature: float
    ) -> torch.Tensor:
        """Sample one token from target model"""
        outputs = self.target_model(input_ids)
        logits = outputs.logits[:, -1, :] / temperature
        probs = torch.softmax(logits, dim=-1)
        return torch.multinomial(probs, num_samples=1)


# Test implementation
def test_speculative_decoding():
    """Test speculative decoding"""

    print("Speculative Decoding Test")
    print("="*60)

    # Load models
    from transformers import AutoModelForCausalLM, AutoTokenizer

    # Target model (larger)
    target_model = AutoModelForCausalLM.from_pretrained(
        "mistralai/Mistral-7B-Instruct-v0.2",
        torch_dtype=torch.float16,
        device_map="auto",
    )

    # Draft model (smaller)
    draft_model = AutoModelForCausalLM.from_pretrained(
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        torch_dtype=torch.float16,
        device_map="auto",
    )

    tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")

    # Create speculative decoder
    decoder = SpeculativeDecoder(
        target_model=target_model,
        draft_model=draft_model,
        tokenizer=tokenizer,
        gamma=5,
    )

    # Test generation
    prompt = "Explain quantum computing in simple terms:"

    print(f"\nPrompt: {prompt}")
    print(f"\nGenerating with speculative decoding...")

    start = time.time()
    output, stats = decoder.generate(prompt, max_new_tokens=100)
    elapsed = time.time() - start

    print(f"\nOutput: {output}")
    print(f"\nStats:")
    print(f"  Draft tokens: {stats['draft_tokens']}")
    print(f"  Accepted tokens: {stats['accepted_tokens']}")
    print(f"  Acceptance rate: {stats['acceptance_rate']:.2%}")
    print(f"  Target steps: {stats['target_steps']}")
    print(f"  Theoretical speedup: {stats['theoretical_speedup']:.2f}x")
    print(f"  Time: {elapsed:.2f}s")


if __name__ == "__main__":
    test_speculative_decoding()
```

---

## Experiment 2: Acceptance Rate Analysis

### Objective
Measure acceptance rates at different gamma values.

### Analysis Script
```python
# acceptance_rate_analysis.py
import torch
import matplotlib.pyplot as plt

def analyze_acceptance_rates():
    """Analyze acceptance rates at different gamma values"""

    gammas = [2, 4, 6, 8, 10, 16]
    prompts = [
        "The history of artificial intelligence",
        "Write a Python function to",
        "What is the meaning of life?",
        "Explain the theory of relativity",
    ]

    results = []

    for gamma in gammas:
        print(f"\nTesting gamma={gamma}")

        # Run tests
        acceptance_rates = []

        for prompt in prompts:
            decoder = SpeculativeDecoder(
                target_model=target_model,
                draft_model=draft_model,
                tokenizer=tokenizer,
                gamma=gamma,
            )

            _, stats = decoder.generate(prompt, max_new_tokens=50)
            acceptance_rates.append(stats['acceptance_rate'])

        avg_acceptance = sum(acceptance_rates) / len(acceptance_rates)
        theoretical_speedup = gamma * avg_acceptance

        results.append({
            "gamma": gamma,
            "acceptance_rate": avg_acceptance,
            "speedup": theoretical_speedup,
        })

        print(f"  Avg acceptance: {avg_acceptance:.2%}")
        print(f"  Theoretical speedup: {theoretical_speedup:.2f}x")

    # Plot
    gammas = [r["gamma"] for r in results]
    acceptance = [r["acceptance_rate"] for r in results]
    speedups = [r["speedup"] for r in results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(gammas, acceptance, 'o-', linewidth=2)
    ax1.set_xlabel('Gamma (draft tokens)')
    ax1.set_ylabel('Acceptance Rate')
    ax1.set_title('Acceptance Rate vs Gamma')
    ax1.grid(True, alpha=0.3)

    ax2.plot(gammas, speedups, 's-', color='green', linewidth=2)
    ax2.axhline(y=1, color='r', linestyle='--', label='No speedup')
    ax2.set_xlabel('Gamma (draft tokens)')
    ax2.set_ylabel('Theoretical Speedup')
    ax2.set_title('Speedup vs Gamma')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/workspace/speculative_decoding_analysis.png', dpi=150)
    print("\nPlot saved to: /workspace/speculative_decoding_analysis.png")

    return results


if __name__ == "__main__":
    analyze_acceptance_rates()
```

---

## Experiment 3: Speculative vs Standard Decoding

### Objective
Compare speculative decoding with standard generation.

### Comparison Script
```python
# compare_speculative_standard.py
def compare_generation_methods():
    """Compare speculative vs standard generation"""

    prompts = [
        "Write a short story about",
        "Explain how neural networks",
        "The best way to learn",
    ]

    results_speculative = []
    results_standard = []

    for prompt in prompts:
        print(f"\nPrompt: {prompt}")

        # Speculative decoding
        decoder = SpeculativeDecoder(
            target_model=target_model,
            draft_model=draft_model,
            tokenizer=tokenizer,
            gamma=5,
        )

        start = time.time()
        output_spec, stats_spec = decoder.generate(prompt, max_new_tokens=100)
        time_spec = time.time() - start

        results_speculative.append({
            "prompt": prompt,
            "time": time_spec,
            "tokens": stats_spec['draft_tokens'],
            "tokens_per_sec": stats_spec['draft_tokens'] / time_spec,
        })

        # Standard generation
        start = time.time()
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs_std = target_model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=True,
            temperature=1.0,
        )
        output_std = tokenizer.decode(outputs_std[0], skip_special_tokens=True)
        time_std = time.time() - start

        generated_tokens = outputs_std.shape[1] - inputs["input_ids"].shape[1]

        results_standard.append({
            "prompt": prompt,
            "time": time_std,
            "tokens": generated_tokens,
            "tokens_per_sec": generated_tokens / time_std,
        })

        print(f"  Speculative: {time_spec:.2f}s ({results_speculative[-1]['tokens_per_sec']:.1f} t/s)")
        print(f"  Standard:    {time_std:.2f}s ({results_standard[-1]['tokens_per_sec']:.1f} t/s)")
        print(f"  Speedup:     {time_std/time_spec:.2f}x")

    # Summary
    avg_spec = sum(r['tokens_per_sec'] for r in results_speculative) / len(results_speculative)
    avg_std = sum(r['tokens_per_sec'] for r in results_standard) / len(results_standard)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Avg Speculative: {avg_spec:.1f} tokens/sec")
    print(f"Avg Standard:     {avg_std:.1f} tokens/sec")
    print(f"Overall Speedup:  {avg_std/avg_spec:.2f}x")


if __name__ == "__main__":
    compare_generation_methods()
```

---

## Expected Results (11GB VRAM GPU)

### Acceptance Rate vs Gamma

| Gamma | Acceptance Rate | Theoretical Speedup |
|-------|----------------|---------------------|
| 2 | ~80% | 1.6x |
| 4 | ~70% | 2.8x |
| 5 | ~65% | 3.25x |
| 8 | ~55% | 4.4x |
| 10 | ~50% | 5.0x |
| 16 | ~40% | 6.4x |

### Performance Comparison

| Method | Tokens/sec | VRAM | Speedup vs Standard |
|--------|------------|------|---------------------|
| Standard (7B) | ~25 | ~7GB | 1.0x |
| Speculative (7B + 1B) | ~45 | ~9GB | 1.8x |
| Standard (13B) | ~15 | ~11GB | - |
| Speculative (13B + 1B) | ~35 | OOM | - |

### Draft Model Recommendations

| Target Model | Best Draft Model | Gamma | Notes |
|--------------|------------------|-------|-------|
| Llama-2-7B | TinyLlama-1.1B | 5-8 | Good speedup |
| Mistral-7B | TinyLlama-1.1B | 4-6 | Balanced |
| Llama-2-13B | Phi-2 (2.7B) | 4 | May OOM on 11GB |
| Mixtral-8x7B | Mistral-7B | 2 | Limited by VRAM |

---

## Experiment Checklist

- [ ] Speculative decoding implementation from scratch
- [ ] Token verification logic test
- [ ] Acceptance rate analysis at different gamma values
- [ ] Speculative vs standard generation comparison
- [ ] Draft model selection test
- [ ] Temperature impact on acceptance rate
- [ ] Benchmark with different model sizes
- [ ] Memory usage analysis (target + draft models)
- [ ] Quality comparison (perplexity)
- [ ] Actual speedup measurement (not just theoretical)

---

## Related Documentation
- [4202: Speculative Decoding](../docs/phases/phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md)
- [4201: Context Window Physics](../docs/phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [1402: vLLM and TGI](../docs/phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
