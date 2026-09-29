---
Document ID: 6300-QUIZ
Title: "6300: Context Window Management - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
---

# 6300: Context Window Management - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Context window limits:**

A) Only training
B) Only inference, with every training pass somehow immune to the same limit
C) Both training and inference
D) Neither

**2. Longer context windows:**

A) Always better, regardless of the compute budget or the serving cost
B) Only affect memory
C) No trade-off
D) Trade-off with computation

**3. Context compression:**

A) Reduces information loss
B) Keeps all information
C) Loses some information
D) Not possible

**4. Sliding window context:**

A) Uses all history, which a fixed-size buffer can never physically hold
B) Uses recent tokens only
C) Uses random tokens
D) No context

**5. Tokens in a KV cache:**

A) All tokens
B) Only recent tokens
C) Only first token
D) No tokens

**6. Context distillation:**

A) Teaches smaller models
B) Removes context
C) Compresses context
D) Not useful

**7. LongLoRA:**

A) Extends context window
B) Shortens context, the opposite of what the method was published to do
C) No effect
D) Not real

**8. Ring attention:**

A) Processes sequences in chunks
B) Processes all at once
C) Doesn't work, which its adoption in long-context training runs disproves outright
D) Only for training

**9. Context overflow causes:**

A) Better results, the opposite of what every truncation benchmark reports
B) Loss of early information
C) No issue
D) Crashes

**10. Selective context:**

A) Keeps all tokens
B) Keeps important tokens
C) Removes all tokens, leaving the model nothing whatsoever to condition on
D) Random selection

**11. To handle long documents:**

A) Must use full document, cramming every page in no matter how large it grows
B) Can chunk and retrieve
C) Can't handle
D) Use shorter documents

**12. Context quality affects:**

A) Only speed
B) Generation quality
C) Memory only, a claim no context-ablation study has ever supported
D) No effect

**13. The "lost in the middle" phenomenon:**

A) Models attend to ends more
B) Models attend to middle more
C) Equal attention
D) Doesn't exist

**14. Context re-ranking:**

A) Puts important info first
B) Random order
C) Alphabetical order, a scheme no retrieval pipeline has any reason to prefer
D) No effect

**15. Typical context window of modern long-context LLMs:**

A) 4K tokens
B) 8K tokens
C) 128K tokens
D) Unlimited, a number no vendor has ever shipped in a real product

**16. RoPE (Rotary Position Embedding):**

A) Extends context to infinity, a claim RoPE's interpolation math itself refutes
B) Helps with longer sequences
C) No effect on context
D) Only for short sequences

**17. YaRN (Yet another RoPE extensioN):**

A) Extends context without fine-tuning
B) Requires full retraining, an expense YaRN was designed specifically to avoid
C) Doesn't work
D) Only for training

**18. Dynamic context:**

A) Fixed size
B) Adjusts based on input
C) Random size, redrawn per request with no reference to the actual content
D) No context

**19. Context window vs accuracy:**

A) Always linear relationship
B) Diminishing returns
C) No relationship
D) Inverse relationship

**20. For RAG, context should:**

A) Be as long as possible
B) Be relevant and concise
C) Be random
D) Be everything

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | C |
| 2 | D |
| 3 | C |
| 4 | B |
| 5 | A |
| 6 | C |
| 7 | A |
| 8 | A |
| 9 | B |
| 10 | B |
| 11 | B |
| 12 | B |
| 13 | A |
| 14 | A |
| 15 | C |
| 16 | B |
| 17 | A |
| 18 | B |
| 19 | B |
| 20 | B |
