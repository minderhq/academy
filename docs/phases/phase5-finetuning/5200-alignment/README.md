---
Document ID: 5200-ALIGNMENT-README
Title: "5200: LLM Alignment"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Prerequisites: []
Estimated Time: 24 hours
Tags: ['module', 'finetuning', 'alignment']
---

# 5200: LLM Alignment

## Module Overview

This module covers techniques for aligning language models with human preferences and safety requirements. You'll learn RLHF, DPO, and modern alignment approaches that make models helpful, harmless, and honest.

**Why This Matters:**

- Base models can generate toxic, biased, or harmful content
- Alignment is critical for real-world deployment
- RLHF/DPO significantly improves instruction following
- Safety alignment prevents misuse and brand damage

## Learning Objectives

After completing this module, you will be able to:

- **Alignment Fundamentals**: Understand the alignment problem and solutions
- **DPO Theory**: Master Direct Preference Optimization math and implementation
- **Reward Modeling**: Build and train reward models for RLHF
- **PPO Training**: Implement Proximal Policy Optimization for LLMs
- **Safety Alignment**: Apply guardrails and content filtering
- **Best-of-N and Rejection Sampling**: Rerank at the endpoint, price the KL rent, and convert picks into weights via RSFT

## Module Contents

### [5201: DPO Theory](./5201-DPO-Theory.md)
**Direct Preference Optimization**

- RLHF vs DPO comparison
- Preference data collection
- DPO mathematical derivation
- Reference model importance
- Beta hyperparameter tuning

**Experiments:**

- Implement DPO from scratch
- Train on preference datasets
- Compare DPO vs PPO
- Analyze alignment quality

### [5202: Alignment Orchestration](./5202-Alignment-Orchestration.md)
**Reward Modeling vs Direct Preference**

- Alignment methods comparison
- Reward modeling (RLHF stage 2)
- Direct Preference Optimization in practice
- KTO (Kahneman-Tversky Optimization)
- Practical alignment pipeline and evaluation

**Experiments:**

- Build end-to-end alignment pipeline
- Compare reward modeling vs DPO vs KTO
- Evaluate alignment quality
- Deploy aligned models

### [5203: RLHF](./5203-RLHF.md)
**Reinforcement Learning from Human Feedback**

- The three-stage RLHF pipeline
- Stage 2: reward model training
- Stage 3: PPO optimization
- KL divergence and reward hacking
- Hands-on: minimal RLHF with TRL

**Experiments:**

- Train a reward model
- Run PPO optimization
- Diagnose reward hacking
- Compare RLHF vs DPO outcomes

### [5204: Preference Dataset Creation](./5204-Preference-Dataset-Creation.md)
**Building the Data Alignment Trains On**

- Anatomy of a preference example
- Prompt sourcing and response pair generation
- Annotation guidelines
- Dataset formats and quality control
- Synthetic preferences and how much data you need

**Experiments:**

- Collect and annotate preference pairs
- Apply quality control to a dataset
- Generate synthetic preferences
- Size a dataset for a target task

### [5205: GRPO and RLVR](./5205-GRPO-RLVR.md)
**Group Relative Policy Optimization and Verifiable Rewards**

- Verifiable rewards vs the learned reward model
- The group-relative advantage: no critic, no value head
- Rule-based reward functions with TRL
- GRPOTrainer configuration and the DAPO refinements
- Saturation, entropy collapse, and verifier gaming

**Experiments:**

- Write verifiable reward functions
- Run a GRPO stage on a small instruct model
- Diagnose prompt saturation from training logs
- Compare GRPO vs PPO vs DPO outcomes

### [5206: Best-of-N and Rejection Sampling](./5206-Best-of-N-and-Rejection-Sampling.md)
**Inference-time reranking and rejection-sampling fine-tuning**

- The BoN contract and the exact KL price log N − (N−1)/N
- The overoptimization curve: proxy monotone up, gold peaking and falling
- Rejection-sampling fine-tuning: the sample-keep-dedup-SFT loop
- Renting versus owning: per-request KL against one-time training
- The campaign ledger: best quality and cheapest row on the same board

**Experiments:**

- Verify the BoN KL identity against Monte-Carlo
- Walk the Goodhart curve and locate the peak N
- Run the RSFT climb and compare raw vs reranked service
- Price the break-even between renting and owning

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 2100: [Calculus for Deep Learning](../../phase2-foundations/2100-calculus/README.md) (optimization, gradients)
- [ ] Module 2200: [Deep Learning Frameworks](../../phase2-foundations/2200-frameworks/README.md) (PyTorch proficiency)
- [ ] Module 2400: [LLM Pretraining](../../phase2-foundations/2400-pretraining/README.md) (training fundamentals)
- [ ] Module 5100: [Parameter-Efficient Fine-Tuning (PEFT)](../5100-peft/README.md) (efficient fine-tuning)
- [ ] Understanding of reinforcement learning basics

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** DPO theory, RLHF pipeline, preference datasets
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Alignment projects
- **Duration:** 10 hours
- **Topics:**
  - Implement DPO training
  - Build reward models
  - Create alignment datasets
  - Evaluate aligned models
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:

- **[5100: Parameter-Efficient Fine-Tuning (PEFT)](../5100-peft/README.md)** (efficient alignment training)
- **[5300: Synthetic Data & Advanced Training](../5300-synthetic/README.md)** (generating preference data)
- **[7400: Agent Memory Systems](../../phase7-agentic/7400-memory/README.md)** (aligning memory-driven agents)
- **[7500: AI Agent Security](../../phase7-agentic/7500-security/README.md)** (safety and guardrails)

## Time Commitment

| Activity | Time |
|----------|------|
| [5201: DPO Theory](./5201-DPO-Theory.md) | 4 hours |
| [5202: Alignment Orchestration](./5202-Alignment-Orchestration.md) | 4 hours |
| [5203: RLHF](./5203-RLHF.md) | 4 hours |
| [5204: Preference Dataset Creation](./5204-Preference-Dataset-Creation.md) | 4 hours |
| [5205: GRPO and RLVR](./5205-GRPO-RLVR.md) | 4 hours |
| [5206: Best-of-N and Rejection Sampling](./5206-Best-of-N-and-Rejection-Sampling.md) | 4 hours |
| Quiz | 30 minutes |
| Practice | 10 hours |
| **Total** | **34.5 hours** |

## Resources

**Essential Libraries:**

- TRL (Transformer Reinforcement Learning)
- Hugging Face PEFT
- Axolotl (alignment support)
- Reward Model API

**Essential Papers:**

- "Training Language Models to Follow Instructions with Human Feedback"
- "Direct Preference Optimization: Your Language Model is Secretly a Reward Model"
- "Constitutional AI: Harmlessness from AI Feedback"

## Alignment Methods Comparison

| Method | Data Needed | Training Time | Quality | Stability |
|--------|-------------|---------------|---------|-----------|
| Supervised Fine-tuning | Instructions | Low | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| RLHF (PPO) | Preferences | High | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| DPO | Preferences | Medium | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| GRPO (RLVR) | Verifiable checkers | Medium-High | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| RLAIF | AI Feedback | Medium | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Constitutional AI | Principles | Medium | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## DPO vs RLHF Pipeline

**Traditional RLHF:**
```text
1. SFT → 2. Reward Model → 3. PPO Training (3 components)
```

**DPO:**
```text
1. SFT → 2. DPO Training (2 components, no reward model)
```

## Preference Dataset Format

```python
{
  "prompt": "How do I make a cake?",
  "chosen": "Here's a simple cake recipe...",
  "rejected": "I don't know. Figure it out yourself."
}
```

## Tips for Success

1. **Start with SFT**: Supervised fine-tuning before alignment
2. **Collect quality preferences**: Garbage in, garbage out
3. **Tune beta carefully**: Controls alignment strength
4. **Use reference model**: Prevents forgetting
5. **Evaluate comprehensively**: Use multiple alignment metrics

## Common Pitfalls

1. **Skipping SFT:** Alignment needs a good base model
2. **Poor preference data:** Noisy labels hurt performance
3. **Over-aligning:** Model becomes too cautious or repetitive
4. **Ignoring safety:** Aligned models can still be jailbroken
5. **Not testing diversity:** Check model doesn't lose capabilities

## Alignment Evaluation Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Helpfulness | Does it follow instructions? | >80% |
| Harmlessness | Does it avoid harmful content? | >95% |
| Honesty | Does it avoid hallucinations? | >70% |
| TT-Eval | Following specific formats | >75% |

## Sample Alignment Pipeline

1. **Pretraining** (Base model)
   ↓
2. **SFT** (Instruction following)
   ↓
3. **DPO** (Preference optimization)
   ↓
4. **Safety Guardrails** (Content filtering)
   ↓
5. **Evaluation** (Alignment benchmarks)

## DPO Hyperparameters

| Parameter | Range | Effect | Default |
|-----------|-------|--------|---------|
| Beta (β) | 0.1-0.5 | Alignment strength | 0.1 |
| Learning Rate | 1e-7 - 5e-6 | Training stability | 1e-6 |
| Epochs | 1-5 | Overfitting vs learning | 3 |
| Max Length | 512-2048 | Context usage | 1024 |

## Safety Considerations

Alignment is not enough. Deploy with:

- [ ] Content filtering layers
- [ ] Output monitoring
- [ ] Jailbreak detection
- [ ] Human in the loop for sensitive tasks
- [ ] Regular safety audits

---

**Next Module:** [5300: Synthetic Data](../5300-synthetic/README.md)

**Previous Module:** [5100: PEFT](../5100-peft/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 5 documentation.

