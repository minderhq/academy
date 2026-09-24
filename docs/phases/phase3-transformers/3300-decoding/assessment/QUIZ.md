# 3300: Decoding - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Greedy decoding selects:**

A) The most likely token at each step
B) Multiple sequences
C) Random tokens
D) The least likely token

**2. Beam search explores:**

A) All possible sequences
B) Multiple hypotheses in parallel
C) Only one sequence
D) Random sequences

**3. Top-k sampling keeps:**

A) Only the top token
B) The k most likely tokens
C) All tokens
D) Random tokens

**4. Nucleus (top-p) sampling:**

A) Keeps tokens above probability threshold p
B) Keeps exactly p tokens
C) Samples uniformly
D) Never samples

**5. Temperature in sampling controls:**

A) The speed of generation
B) The randomness (lower = more deterministic)
C) The beam width
D) The sequence length

**6. A temperature of 1.0 means:**

A) No change to probabilities
B) More random
C) Less random
D) Error

**7. Repetition penalty prevents:**

A) Long sequences
B) Repeated phrases
C) Short sequences
D) All generation

**8. Length penalty adjusts scores based on:**

A) Sequence length
B) Token frequency
C) Model size
D) Vocabulary size

**9. Sampling vs Greedy:**

A) Sampling is always better
B) Sampling adds randomness, greedy is deterministic
C) Greedy adds randomness
D) No difference

**10. Beam width of 1 is equivalent to:**

A) Top-k sampling
B) Greedy decoding
C) Nucleus sampling
D) Random search

**11. Typical beam width is:**

A) 1
B) 4-10
C) 100+
D) Doesn't matter

**12. The main drawback of beam search is:**

A) Too slow
B) Can produce repetitive outputs
C) Doesn't work
D) Too simple

**13. Top-k with k=1 is:**

A) Sampling from all tokens
B) Greedy decoding
C) Nucleus sampling
D) Random sampling

**14. Typical temperature values are:**

A) 0.1 - 0.5
B) 0.7 - 1.0
C) 1.5 - 2.0
D) Any value

**15. Frequency penalty reduces scores based on:**

A) How often tokens appear
B) Token position
C) Model confidence
D) Vocabulary size

**16. Speculative decoding:**

A) Uses a larger model
B) Uses a smaller model to propose tokens
C) Doesn't work
D) Is always slower

**17. KV cache stores:**

A) All previous key and value computations
B) Only the last token
C) Nothing
D) Model parameters

**18. With KV cache, each new token:**

A) Requires full sequence recomputation
B) Only computes new attention
C) Doesn't use attention
D) Is slower

**19. The main benefit of KV cache is:**

A) Better quality
B) Faster generation for long sequences
C) Smaller model
D) Less memory

**20. Contrastive decoding:**

A) Uses one model
B) Compares outputs from two models
C) Is the same as greedy
D) Doesn't exist

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | A |
| 2 | B |
| 3 | B |
| 4 | A |
| 5 | B |
| 6 | A |
| 7 | B |
| 8 | A |
| 9 | B |
| 10 | B |
| 11 | B |
| 12 | B |
| 13 | B |
| 14 | B |
| 15 | A |
| 16 | B |
| 17 | A |
| 18 | B |
| 19 | B |
| 20 | B |

---

**Last Updated:** 2026-02-04
