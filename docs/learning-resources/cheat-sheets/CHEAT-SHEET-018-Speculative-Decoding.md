---
Document ID: CHEAT-SHEET-018
Title: "CHEAT-SHEET-018: Speculative Decoding"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'speculative-decoding', 'inference', 'vllm']
---

# CHEAT-SHEET-018: Speculative Decoding

## Quick Reference for Speculative Decoding

**Version:** 1.0

Latency at low batch is a division of labor: a small draft model
proposes several tokens at once, the large target verifies them all
in one pass, and the output is provably unchanged because the target
still authors every token. This sheet maps the bet, the acceptance
mechanics, the draft ladder, the length tuning, and the draft-free
variants — the whole speculative surface on one page.

---

## The Draft-Target Bet

Draft predicts K tokens greedily; the target verifies all K in ONE
forward pass — turning 1 target run into multiple accepted tokens.
The honest expectation is ~2-3x realized, not the theoretical peak:

`Speedup = 1 / (P_accept × T_draft + (1 − P_accept) × T_target)`

At 80% acceptance with a 10x-faster draft (T_draft = 0.1):
1 / (0.8 × 0.1 + 0.2 × 1) = 1 / 0.28 = **3.57x theoretical**.

```python
DRAFTS = {  # draft ladder for a Llama-2-70B target
    "TinyLlama-1B": (1 / 70, 30.0, (0.60, 0.70)),
    "Llama-2-7B distilled": (0.10, 8.0, (0.85, 0.90)),
    "Llama-2-13B": (13 / 70, 4.0, (0.90, 0.95)),
}
LENS = [(4, 2.5, 0.85), (8, 3.0, 0.70), (12, 2.8, 0.55), (16, 2.5, 0.45)]

def speedup(p_accept, t_draft, t_target=1.0):
    return 1.0 / (p_accept * t_draft + (1.0 - p_accept) * t_target)

def expected_tokens(p, k):
    # accepted tokens per round before the first rejection
    return (1.0 - p ** (k + 1)) / (1.0 - p)

print("speedup P=0.80 T_draft=0.1: %.2fx" % speedup(0.80, 0.1))
print("E[accepted] p=0.70 K=8: %.2f" % expected_tokens(0.7, 8))
for name, (share, fast, (lo, hi)) in DRAFTS.items():
    print("%-22s share %.0f%%  ~%dx faster  accept %d-%d%%"
          % (name, share * 100, fast, lo * 100, hi * 100))
for k, got, acc in LENS:
    print("spec_len %-2d measured %.1fx at %d%% acceptance"
          % (k, got, acc * 100))
print("sweet spot for a 70B target: %dB draft" % round(70 * 0.10))
```

---

## Acceptance Mechanics

Greedy variant: accept draft tokens until the first mismatch, append
the target's corrected token, restart. Probabilistic variant
(speculative sampling): accept draft token x with probability
`min(1, p(x)/q(x))` where p is the target and q the draft
distribution; on rejection resample from the residual
`max(0, p − q)`, renormalized. Quality invariant: the target authors
every token either way, so output distributions match the
non-speculative run exactly.

Acceptance rises with: draft quality (KL-distillation at lr=1e-5
closes the gap), lower temperature, shorter chains, and domain match
between draft and target training data.

---

## The Draft Ladder

| Draft (70B target) | Size share | Speed | Acceptance |
| --- | --- | --- | --- |
| TinyLlama-1B | ~1% | ~30x | 60-70% |
| Llama-2-7B distilled | ~10% | ~8x | 85-90% |
| Llama-2-13B | ~19% | ~4x | 90-95% |

Sweet spot: ~10% of the target's size — a 70B target takes a 7B
draft. Smaller drafts run faster but accept less; larger drafts
accept more but eat the savings. Distill the draft from the target
(KL divergence on the same corpus) rather than reusing an
unrelated checkpoint.

---

## Length Tuning and the Two-Cache Discipline

The ladder trades acceptance for chain length: spec_len 4 gives
2.5x at 85% acceptance, 8 gives 3.0x at 70%, 12 gives 2.8x at 55%,
16 gives 2.5x at 45%. Optimal sits at 8-12 for most setups —
measure with `find_optimal_speculation_length` against a
non-speculative baseline, never eyeball it.

Two caches exist (draft and target) and they must stay consistent:
every verify round ends with `SpeculativeKVCache.commit_accepted`
moving only the accepted prefix from the draft cache to the target
cache and clearing the rest. A skipped commit leaves phantom tokens
in the target's KV cache and corrupts every subsequent step.

---

## Draft-Free Variants

| Variant | Mechanism | Trade |
| --- | --- | --- |
| Lookahead | the target self-verifies its own greedy chain | no extra model, but the "draft" pass pays full target cost |
| Parallel best-of-4 | score 4 parallel draft chains with the target, keep the best | draft still exists; verification is per-chain, not amortized |
| Medusa heads | 4 extra Linear heads predict offsets +1..+4 from one hidden state | one-time head training; no separate draft checkpoint to serve |

---

## Troubleshooting

| Symptom | Root cause | Fix |
| --- | --- | --- |
| Speculation on, latency unchanged | high batch — decode is bandwidth-bound, spec wins at low batch | measure at batch 1; disable under heavy concurrency |
| Speedup far below 3.57x | draft load, cache copies, scheduling overhead | 2-3x realized is the honest budget; profile the verify round |
| Output differs from the plain run | sampler mismatch or a skipped residual resample | identical temperature/top_p; rejected positions resample from max(0, p−q) |
| spec_len 16 slower than 8 | long chains reject more: 45% vs 70% acceptance | tune 8-12 against a non-speculative baseline |
| Target cache holds phantom tokens | draft/target caches desynchronized | commit_accepted after every verify round |
| No draft model to spare | a second checkpoint does not fit or does not exist | lookahead, parallel best-of-N, or Medusa heads |

---

**Quick Reference for:**

- [Module 4202: Speculative Decoding](../../phases/phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md)
- [Module 4201: Context Window Physics and OOM Prevention](../../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [Module 1402: vLLM and TGI](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [CHEAT-SHEET-017: KV Cache](./CHEAT-SHEET-017-KV-Cache.md)
