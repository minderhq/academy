---
Document ID: 3300-QUIZ
Title: "3300: Decoding - Quiz"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Advanced
---

# 3300: Decoding - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Greedy decoding selects:**

A) Multiple sequences
B) The least likely token
C) Random tokens
D) The most likely token at each step

**2. Beam search explores:**

A) Multiple hypotheses in parallel
B) Only one sequence
C) All possible sequences
D) Random sequences

**3. Top-k sampling keeps:**

A) Only the top token
B) The k most likely tokens
C) All tokens
D) Random tokens

**4. Nucleus (top-p) sampling:**

A) Keeps exactly p tokens
B) Samples uniformly
C) Keeps tokens above probability threshold p
D) Never samples

**5. Temperature in sampling controls:**

A) The beam width
B) The speed of generation
C) The sequence length
D) The randomness (lower = more deterministic)

**6. A temperature of 1.0 means:**

A) Error
B) No change to probabilities
C) More random
D) Less random

**7. Repetition penalty prevents:**

A) All generation
B) Repeated phrases
C) Short sequences
D) Long sequences

**8. Length penalty adjusts scores based on:**

A) Vocabulary size
B) Model size
C) Token frequency
D) Sequence length

**9. Sampling vs Greedy:**

A) Sampling adds randomness, greedy is deterministic
B) Sampling is always better
C) Greedy adds randomness
D) No difference

**10. Beam width of 1 is equivalent to:**

A) Random search
B) Top-k sampling
C) Nucleus sampling
D) Greedy decoding

**11. Typical beam width is:**

A) 1
B) Doesn't matter
C) 100+
D) 4-10

**12. The main drawback of beam search is:**

A) Doesn't work
B) Too simple
C) Can produce repetitive outputs
D) Too slow

**13. Top-k with k=1 is:**

A) Nucleus sampling
B) Random sampling
C) Greedy decoding
D) Sampling from all tokens

**14. Typical temperature values are:**

A) 0.7 - 1.0
B) 1.5 - 2.0
C) 0.1 - 0.5
D) Any value

**15. Frequency penalty reduces scores based on:**

A) How often tokens appear
B) Token position
C) Model confidence
D) Vocabulary size

**16. Speculative decoding:**

A) Is always slower
B) Uses a smaller model to propose tokens
C) Doesn't work
D) Uses a larger model

**17. KV cache stores:**

A) Nothing
B) Model parameters
C) All previous key and value computations
D) Only the last token

**18. With KV cache, each new token:**

A) Requires full sequence recomputation
B) Only computes new attention
C) Is slower
D) Doesn't use attention

**19. The main benefit of KV cache is:**

A) Faster generation for long sequences
B) Less memory
C) Better quality
D) Smaller model

**20. Contrastive decoding:**

A) Uses one model
B) Doesn't exist
C) Compares outputs from two models
D) Is the same as greedy

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | D |
| 2 | A |
| 3 | B |
| 4 | C |
| 5 | D |
| 6 | B |
| 7 | B |
| 8 | D |
| 9 | A |
| 10 | D |
| 11 | D |
| 12 | C |
| 13 | C |
| 14 | A |
| 15 | A |
| 16 | B |
| 17 | C |
| 18 | B |
| 19 | A |
| 20 | C |
