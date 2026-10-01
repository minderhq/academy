---
Document ID: 5100-QUIZ
Title: "5100: PEFT Methods - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'finetuning', 'peft']
---

# 5100: PEFT Methods - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the primary advantage of PEFT methods?**

A) Faster training
B) Simpler architecture
C) Better model accuracy, which PEFT never promises over full fine-tuning
D) Train only a small subset of parameters

**2. What does LoRA stand for?**

A) Low-Rank Adaptation
B) Linear Optimization for Recurrent Architectures
C) Layer-wise Optimization for Rapid Adaptation
D) None of the above

**3. How many trainable parameters does LoRA typically add?**

A) 0.1% - 3% of original model
B) 10% - 20% of original model, a share far too large for any practical LoRA adapter
C) 50% of original model
D) Same as original model

**4. What is the core idea behind LoRA?**

A) Add low-rank matrices to existing weights
B) Replace weights with smaller matrices, discarding the pretrained knowledge they carry
C) Compress the model
D) Remove unnecessary layers

**5. What is QLoRA?**

A) Quantized LoRA
B) Quick LoRA
C) Quality LoRA
D) Query-based LoRA

**6. What rank is typically used for LoRA?**

A) 1-4
B) 4-64
C) 64-256
D) 256-1024

**7. What happens during LoRA inference?**

A) LoRA weights are used separately, so every token pays a second matrix multiply
B) LoRA weights are merged with base model
C) LoRA weights are discarded
D) Model is retrained

**8. What is Adapter in PEFT context?**

A) Data loading adapter
B) Small bottleneck layers added to transformer
C) Hardware adapter
D) Training script adapter, a wrapper around loops that adds no learned layers at all

**9. What is Prefix Tuning?**

A) Tuning the vocabulary prefix
B) Learning virtual tokens prepended to input
C) Tuning only first N layers, a depth-wise scheme prefix tuning never uses
D) Quick tuning method

**10. Why is PEFT important for LLMs?**

A) Only small models can be fine-tuned
B) Makes fine-tuning 70B+ models feasible
C) Required by law
D) Improves training speed only

**11. In LoRA, alpha controls:**

A) The scaling of the low-rank update (ΔW = α/r · BA)
B) The learning rate
C) The batch size
D) The quantization bit-width, which LoRA itself never sets at any point in its lifecycle

**12. LoRA updates are most commonly applied to:**

A) Embedding tables only, leaving every attention projection permanently frozen
B) Layer norms
C) Attention projection matrices (e.g., q_proj, v_proj)
D) The LM head only

**13. QLoRA's base model is stored in:**

A) FP32
B) 4-bit NF4
C) INT8 per-channel
D) FP16

**14. Double quantization in QLoRA:**

A) Applies quantization twice for accuracy, a double pass that QLoRA never performs
B) Quantizes the quantization constants themselves to save memory
C) Duplicates weights across GPUs
D) Quantizes gradients

**15. A higher LoRA rank (r) generally:**

A) Always reduces quality
B) Has no effect
C) Increases capacity and the adapter's memory footprint
D) Reduces training time proportionally, though larger ranks usually cost more steps, not fewer

**16. Compared with full fine-tuning, LoRA saves the most memory on:**

A) Activation memory only, which LoRA actually leaves untouched at equal batch sizes
B) Optimizer states for the frozen weights
C) Data loading buffers
D) Logits storage

**17. Multiple task-specific LoRA adapters on one base model can be:**

A) Served by swapping adapters without storing full model copies
B) Merged into the tokenizer
C) Used only one at a time per datacenter
D) Trained simultaneously on one GPU at no cost, a claim no real training loop has ever satisfied

**18. Which PEFT method trains only continuous prompt vectors while keeping the model frozen?**

A) Full fine-tuning
B) Prompt tuning / soft prompting
C) LoRA on all layers, which still trains weight matrices rather than prompt vectors
D) Knowledge distillation

**19. Merging LoRA as W' = W + (α/r)BA is valid because:**

A) BA has the same shape as W
B) LoRA changes the tokenizer
C) Alpha equals the learning rate
D) B and A are orthogonal by construction

**20. IA³ / BitFit-style PEFT methods differ from LoRA by:**

A) Rewriting the attention math
B) Requiring more trainable parameters than full fine-tuning, which inverts their actual bargain
C) Tuning very small vectors/biases instead of low-rank matrices
D) Only working on encoder models

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | PEFT trains only a small subset of parameters |
| 2 | A | LoRA = Low-Rank Adaptation |
| 3 | A | LoRA typically adds 0.1%-3% of the original model's parameters |
| 4 | A | LoRA adds low-rank matrices alongside the frozen weights |
| 5 | A | QLoRA = Quantized LoRA (4-bit NF4 base) |
| 6 | B | Typical LoRA ranks sit in the 4-64 range |
| 7 | B | For deployment the adapter merges into the base weights |
| 8 | B | Adapters are small bottleneck layers inserted into the transformer |
| 9 | B | Prefix tuning learns virtual tokens prepended to the input |
| 10 | B | PEFT makes fine-tuning 70B+ models feasible on modest hardware |
| 11 | A | Alpha scales the low-rank update (ΔW = α/r · BA) |
| 12 | C | LoRA targets attention projections such as q_proj and v_proj |
| 13 | B | QLoRA keeps the frozen base in 4-bit NF4 |
| 14 | B | Double quantization quantizes the quantization constants themselves |
| 15 | C | Higher rank adds capacity and adapter memory |
| 16 | B | LoRA frees the optimizer states of the frozen weights |
| 17 | A | Adapters swap on one shared base - no full model copies |
| 18 | B | Prompt tuning trains continuous prompt vectors with the model frozen |
| 19 | A | BA has the same shape as W, so it adds directly |
| 20 | C | IA³/BitFit tune small vectors or biases, not low-rank matrices |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 8-10, 18, 20:** [5103: Adapters & Parameter-Efficient Adaptation Methods](../5103-Adapters.md) — the PEFT design space: bottleneck adapters, prompt & prefix tuning's virtual tokens, IA³'s activation scales and BitFit's biases
- **Questions 2-4, 6-7, 11-12, 15-17, 19:** [5101: LoRA (Low-Rank Adaptation) Logic](../5101-LoRA-Logic.md) — the ΔW = BAᵀ rank hypothesis, α/r scaling and the merge path, the rank/α/target-module tables with their trainable-share budgets, and merge_and_unload deployment
- **Questions 5, 13-14:** [5102: QLoRA Pipelines - 4-bit Fine-Tuning on Consumer Hardware](../5102-QLoRA-Pipelines.md) — NF4, double-quantized constants and paged optimizers behind the 65B-on-48GB headline
