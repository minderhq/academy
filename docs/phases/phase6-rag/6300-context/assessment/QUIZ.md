---
Document ID: 6300-QUIZ
Title: "6300: Context Window Management - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'rag', 'context']
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

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | The window binds training sequences and inference prompts alike |
| 2 | D | Longer context costs more compute and attention |
| 3 | C | Compression trades some information for space |
| 4 | B | Sliding windows keep only the most recent tokens |
| 5 | A | The KV cache holds keys/values for all tokens so far |
| 6 | C | Context distillation compresses context into weights |
| 7 | A | LongLoRA extends context with efficient fine-tuning |
| 8 | A | Ring attention processes long sequences in chunks across devices |
| 9 | B | Overflow pushes early context out - oldest information lost |
| 10 | B | Selective context keeps the important tokens only |
| 11 | B | Long documents are chunked and retrieved as needed |
| 12 | B | Generation quality follows context quality |
| 13 | A | Lost-in-the-middle: ends draw more attention than the middle |
| 14 | A | Re-ranking surfaces key info at the attentive positions |
| 15 | C | Modern long-context models ship around 128K windows |
| 16 | B | RoPE's rotary encoding scales to longer sequences (with interpolation) |
| 17 | A | YaRN stretches RoPE without full retraining |
| 18 | B | Dynamic context adapts its size to the input |
| 19 | B | Accuracy gains from context show diminishing returns |
| 20 | B | RAG prompts stay relevant and concise |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-2, 4-5, 9:** [4201: Context Window Physics and OOM Prevention](../../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md) — the window-reach-versus-memory trade, the KV cache that holds keys and values for the tokens so far, SlidingWindowKVCache's constant recent-token window, and the eviction and interpolation schemes behind overflow
- **Questions 3, 10-15, 18-20:** [6302: CAG - Context Augmented Generation and Long Context Architectures](../6302-CAG-Long-Context-Architectures.md) — extractive compression that keeps the highest-information sentences, query-relevance pruning and dynamic context sizing, chunking long documents, the lost-in-the-middle ordering effect with its reorder fix, and the 2026 model-window table around 128k+; accuracy's diminishing returns with window size is stated nowhere in the curriculum, so Q19 leans on the lesson's context-curation teaching
- **Question 6:** [5301: Knowledge Distillation - Training Small Models Using Big Model Outputs](../../../phase5-finetuning/5300-synthetic/5301-Knowledge-Distillation.md) — the distillation family's compress-into-a-smaller-form pattern; context distillation itself is taught nowhere in the curriculum
- **Questions 7-8, 16-17:** [3201: Rotary Positional Embeddings (RoPE)](../../../phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md) — rotary encoding and its extension ladder of position interpolation and NTK-aware YaRN base scaling; LongLoRA and ring attention are taught nowhere in the curriculum, so Q7-Q8 lean on the closest context-extension methods
