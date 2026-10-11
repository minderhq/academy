---
Document ID: CHEAT-SHEET-014
Title: "CHEAT-SHEET-014: Decoding & Sampling Strategies"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'inference', 'sampling', 'decoding']
---

# CHEAT-SHEET-014: Decoding & Sampling Strategies

## Quick Reference for the Sampler Stack

**Version:** 1.0

Every production sampling config is a sequence of distribution edits,
not one dial. This sheet maps the knob each stage owns, the invariant
that survives it, and the order rule that reads them all: the first
truncation wins.

---

## The Stack, In Order

Hugging Face applies its logits warpers in a fixed sequence —
temperature, then top_h, then top_k, then top_p, then min_p, then
typical_p, then epsilon and eta (`generation/utils.py` L1591-1619) —
and each stage renormalizes over the survivors of the previous one.
Sampling configs are not commutative. Module 3304's stack table proves
the rule: the default T0.7 / top_k=4 / top_p=0.9 config on a flat
distribution cuts 0.4196 of mass — ALL of it the top_k cut, because
the four survivors sum to 0.5806, below the 0.90 budget, so top_p
never fired. A config you reason about as "top_p keeps 90 percent" is,
on a flat shape, "top_k keeps the top four and top_p is decorative."

The same knob, different defaults across stacks:

| Parameter | HF GenerationConfig | vLLM SamplingParams |
| --- | --- | --- |
| temperature | 1.0 | 1.0 |
| top_k | 50 (a truncation is ON) | 0 (off) |
| top_p | 1.0 (off) | 1.0 (off) |
| min_p | unset | 0.0 (off) |
| typical_p | unset | not exposed |

Reading a vLLM config through HF eyes silently turns on a truncation
— HF's top_k defaults to 50 while vLLM's defaults to off.

---

## Temperature Reshapes, Never Reorders

Temperature divides the logits before the softmax: `softmax(z/T)`.
Module 3304's walk: entropy climbs monotonically from 0.2128 to 1.8191
nats across T=0.25 to 2.00 while p_top falls from 0.9530 to 0.3101 —
and the argmax reads `the (same)` at every temperature. Dividing by a
positive constant preserves rank; dethroning the top token needs a
truncation rule, never heat. T=0 is the walk's limit, where p_top
reaches 1.0 — what that guarantees (determinism) and what it does not
is module 7505's surface. The same module shows determinism purchased
with config knobs: after T=0.2 sharpens the shape, top_p=0.50 collapses
the set to one token and 2,000 draws produce a single unique output.

---

## Rank vs Mass

Top-k keeps the k highest-rank tokens and never looks at mass: k=1
keeps 0.4995 while a 0.2244 runner-up sits untouched in the discard
pile — and k=1 is greedy search under another name (renormalized
p=1.0). Nucleus (top-p) flips the criterion to mass: keep the
SMALLEST set of most-probable tokens whose probabilities add up to
top_p OR HIGHER — so kept mass always overshoots the budget (p=0.50
keeps two tokens and 0.7240; p=0.90 settles at four tokens, 0.9420),
and the set can never empty: top_p=0.01 still keeps the single top
token, because it alone already adds up to 0.01 or higher. That is
`min_tokens_to_keep=1` in the HF warper signature — the never-empty
property is the contract, not an accident.

```python
import math

LOGITS = [4.0, 3.2, 2.8, 2.0, 1.2, 0.5, 0.0, -1.0]

def softmax(logits, T):
    scaled = [x / T for x in logits]
    m = max(scaled)
    ex = [math.exp(x - m) for x in scaled]
    Z = sum(ex)
    return [e / Z for e in ex]

def nucleus(p, top_p):
    order = sorted(range(len(p)), key=lambda i: -p[i])
    keep, cum = [], 0.0
    for i in order:
        keep.append(i)
        cum += p[i]
        if cum >= top_p:
            break
    return keep, cum

P = softmax(LOGITS, 1.0)
keep, cum = nucleus(P, 0.90)
print("nucleus 0.90:", len(keep), "tokens, kept mass", round(cum, 4))
thr = 0.10 * max(P)
print("min-p 0.10 threshold:", round(thr, 4),
      "-> keeps", sum(1 for x in P if x >= thr), "of", len(P))
print("top-p 0.01 keeps", len(nucleus(P, 0.01)[0]),
      "token(s): the set never empties")
```

---

## Shape-Adaptive Truncation

Top-k and nucleus are shape-blind: one always keeps k, the other
always spends the same budget. Min-p truncates by RATIO — a token
survives if `p_i >= min_p x p_max` — so the same min_p=0.10 gives a
0.0500 threshold on a peaked shape (4 of 8 kept) and a 0.0153
threshold on a flat shape (all 8 kept): the truncation adapts to the
model's own confidence. HF's docs suggest the 0.01-0.2 range; the
formalization is Nguyen et al., arXiv 2407.01082 (ICLR 2025 oral).
Typical-p (Meister et al., arXiv 2202.00666) optimizes a different
target — information content near the conditional entropy H. It ranks
tokens by |info - H|, and on module 3304's three-peak distribution at
the same 0.35 budget where nucleus keeps exactly the top token,
typical keeps two smaller ones and DROPS the winner — its 1.0498 nats
of information sit far from the expected 1.3667, and typical-p exists
to skip boring. That mechanism is behind its measured reduction of
degenerate repetitions. Use nucleus for mass control, typical-p for
repetition control — do not swap them blindly.

---

## Troubleshooting

| Symptom | Root cause | Fix |
| --- | --- | --- |
| Temperature treated as a re-ranker | softmax(z/T) rescales, never reorders — argmax unchanged from T=0.25 to 2.00 | treat T as shape control; dethroning needs truncation |
| top_p read as "keep exactly this mass" | the rule is top_p OR HIGHER — p=0.50 keeps 0.7240 | budget for the overshoot; kept mass is always >= top_p |
| top_k set from habit on flat shapes | rank-blind: k=4 cuts 0.4196 on flat while top_p never fires | check which stage actually cuts; prefer min_p on flat shapes |
| min_p expected to behave like top_p | threshold is a RATIO of p_max: 0.10 gives 0.0500 peaked vs 0.0153 flat | reason in ratios of the top token; range 0.01-0.2 |
| typical_p swapped in as "a better nucleus" | ranks by \|info - H\| and drops the winner at the same budget | nucleus for mass control, typical-p for repetition control |
| Configs reasoned as commutative | each stage renormalizes over survivors; first truncation wins | pin and document the stack order you reason about |

---

**Quick Reference for:**

- [Module 3304: Decoding Sampling Strategies](../../phases/phase3-transformers/3300-decoding/3304-Decoding-Sampling-Strategies.md)
- [Module 1402: vLLM and TGI](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [Module 7505: Temperature Zero and Deterministic Security Testing](../../phases/phase7-agentic/7500-security/7505-Temperature-Zero-and-Deterministic-Security-Testing.md)
- [Module 3401: Encoder-Decoder Architectures](../../phases/phase3-transformers/3400-architectures/3401-Encoder-Decoder-Architectures.md)
