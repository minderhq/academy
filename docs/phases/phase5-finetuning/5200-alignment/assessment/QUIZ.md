---
Document ID: 5200-QUIZ
Title: "5200: Alignment Methods - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'finetuning', 'alignment']
---

# 5200: Alignment Methods - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is the primary goal of LLM alignment?**

A) Increase model size while ignoring how the model actually behaves
B) Align model behavior with human preferences/values
C) Speed up inference
D) Reduce training cost

**2. What does RLHF stand for?**

A) Reinforcement Learning from Human Feedback
B) Recurrent Learning with Hidden Features, a pretraining trick from RNNs
C) Rapid Learning via Fine-tuning
D) None of the above

**3. What is the first step in RLHF training?**

A) PPO training
B) Collect human preference comparisons
C) Reward model training, which comes after preferences are gathered
D) Model distillation

**4. What is the reward model in RLHF trained to predict?**

A) Exact response quality score
B) Human preference between responses
C) The training loss over the next batch of tokens
D) Model accuracy

**5. What is DPO?**

A) Direct Preference Optimization
B) Dynamic Parameter Optimization
C) Distributed Policy Optimization
D) Deep Prompt Optimization

**6. What is the main advantage of DPO over RLHF?**

A) No separate reward model needed
B) Faster GPU throughput on the same amount of data
C) Better accuracy
D) Simpler architecture

**7. What does PPO stand for in RLHF context?**

A) Proximal Policy Optimization
B) Progressive Parameter Optimization
C) Parallel Policy Optimization
D) None of the above

**8. What is the purpose of the KL divergence penalty in RLHF?**

A) Prevent model from deviating too far from reference
B) Speed up training by shrinking every gradient step and skipping evaluation
C) Improve accuracy
D) Reduce memory

**9. What type of data is used for preference collection?**

A) Labeled classification data
B) Paired comparisons: which response is better
C) Translation pairs
D) Question-answer pairs with a single gold response per question

**10. What is a common issue with RLHF?**

A) Too expensive
B) Reward hacking
C) Slow convergence during the final weeks of pretraining
D) All of the above

**11. The standard RLHF pipeline order is:**

A) Reward model → SFT → PPO, which trains the policy before a reward exists
B) PPO → SFT → reward model
C) SFT → reward model training → PPO fine-tuning
D) PPO → reward model → SFT

**12. SFT comes before RLHF because:**

A) The policy must already follow the response format for preference comparisons to be meaningful
B) PPO requires GPU warm-up
C) Reward models cannot be trained on raw unstructured text without an existing formatting step somewhere
D) The KL penalty needs it

**13. DPO's loss increases:**

A) The reward model's accuracy
B) The log-probability margin of preferred over rejected responses relative to the reference model
C) The KL divergence between the policy and itself, without any bound or clipping mechanism at all
D) The vocabulary size

**14. "Reward hacking" is when:**

A) The policy exploits reward-model flaws to score high while producing bad outputs
B) Humans mislabel data
C) The GPU is overclocked
D) The reward model is too small to fit on a single accelerator during training runs

**15. Preference pairs are typically modeled with:**

A) The Bradley-Terry model
B) Multi-class cross-entropy
C) Mean squared error
D) K-means clustering

**16. The reference (frozen) model in DPO/PPO provides:**

A) Faster inference
B) A KL anchor so the policy does not drift too far
C) The reward signal that guides every single PPO update step end to end
D) Data augmentation

**17. RLAIF / Constitutional AI replaces (part of) human labels with:**

A) Random rewards
B) AI-generated feedback guided by principles
C) No feedback signal of any kind during training
D) Test-time compute only

**18. Typical preference datasets contain:**

A) Only benchmark questions reused from public eval suites
B) Ten pairs
C) Tens of thousands to millions of comparison pairs
D) Only code snippets

**19. A major preference-data quality risk is:**

A) Excessive GPU memory use during the annotation collection stage
B) Inconsistent annotator labels (low inter-annotator agreement)
C) Slow tokenization
D) Large disk footprint

**20. Best-of-N sampling with a reward model is:**

A) Inference-time alignment without retraining
B) A PPO variant with a different clipping coefficient
C) A tokenizer upgrade
D) A distillation method

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | A |
| 3 | B |
| 4 | B |
| 5 | A |
| 6 | A |
| 7 | A |
| 8 | A |
| 9 | B |
| 10 | D |
| 11 | C |
| 12 | A |
| 13 | B |
| 14 | A |
| 15 | A |
| 16 | B |
| 17 | B |
| 18 | C |
| 19 | B |
| 20 | A |
