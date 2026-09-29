---
Document ID: 3300-QUIZ
Title: "3300: Decoding - Quiz"
Last Updated: 2026-09-29
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

A) Multiple sequences in parallel, with no ranking or pruning step anywhere
B) The least likely token
C) Random tokens
D) The most likely token at each step

**2. Beam search explores:**

A) Multiple hypotheses in parallel
B) Only one sequence, expanding it token by token in strict order
C) All possible sequences
D) Random sequences

**3. Top-k sampling keeps:**

A) Only the single top token, discarding every other candidate outright
B) The k most likely tokens
C) All tokens
D) Random tokens

**4. Nucleus (top-p) sampling:**

A) Keeps exactly p tokens, always rounded up to the nearest whole number
B) Samples uniformly
C) Keeps tokens above probability threshold p
D) Never samples

**5. Temperature in sampling controls:**

A) The beam width
B) The speed of generation, measured in tokens per second on the GPU
C) The sequence length
D) The randomness (lower = more deterministic)

**6. A temperature of 1.0 means:**

A) Error, since temperature 1.0 is rejected by every decoder
B) No change to probabilities
C) More random
D) Less random

**7. Repetition penalty prevents:**

A) All generation, by blocking every token after the very first one
B) Repeated phrases
C) Short sequences
D) Long sequences

**8. Length penalty adjusts scores based on:**

A) Vocabulary size, scaled by the number of distinct tokens in training
B) Model size
C) Token frequency
D) Sequence length

**9. Sampling vs Greedy:**

A) Sampling adds randomness, greedy is deterministic
B) Sampling is always better
C) Greedy adds randomness by shuffling candidate tokens before picking
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
D) Too slow to run under any production serving stack in practice

**13. Top-k with k=1 is:**

A) Nucleus sampling
B) Random sampling
C) Greedy decoding
D) Sampling from all tokens

**14. Typical temperature values are:**

A) 0.7 - 1.0
B) 1.5 - 2.0, the range most production stacks use for every task
C) 0.1 - 0.5
D) Any value

**15. Frequency penalty reduces scores based on:**

A) How often tokens appear
B) Token position, offset by each token's index inside the window
C) Model confidence
D) Vocabulary size

**16. Speculative decoding:**

A) Is always slower
B) Uses a smaller model to propose tokens
C) Doesn't work
D) Uses a larger model to draft every token before verification

**17. KV cache stores:**

A) Nothing
B) Model parameters
C) All previous key and value computations
D) Only the last token, evicting everything earlier from memory

**18. With KV cache, each new token:**

A) Requires full sequence recomputation
B) Only computes new attention
C) Is slower
D) Doesn't use attention

**19. The main benefit of KV cache is:**

A) Faster generation for long sequences
B) Less memory, since cached tensors shrink as the context grows
C) Better quality
D) Smaller model

**20. Contrastive decoding:**

A) Uses one model
B) Doesn't exist
C) Compares outputs from two models
D) Is the same as greedy, differing only in the sampling seed

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
