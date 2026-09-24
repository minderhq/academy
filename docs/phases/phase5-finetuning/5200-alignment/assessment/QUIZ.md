# Module 5200: Alignment Methods Quiz

**Module:** LLM Alignment (RLHF & DPO)
**Document ID:** 5200
**Difficulty:** Advanced
**Time:** 30 minutes

---

## Instructions

Select the best answer for each question. Answers are provided at the bottom.

---

## Questions

### 1. What is the primary goal of LLM alignment?

A) Increase model size
B) Align model behavior with human preferences/values
C) Speed up inference
D) Reduce training cost

### 2. What does RLHF stand for?

A) Reinforcement Learning from Human Feedback
B) Recurrent Learning with Hidden Features
C) Rapid Learning via Fine-tuning
D) None of the above

### 3. What is the first step in RLHF training?

A) PPO training
B) Collect human preference comparisons
C) Reward model training
D) Model distillation

### 4. What is the reward model in RLHF trained to predict?

A) Exact response quality score
B) Human preference between responses
C) Training loss
D) Model accuracy

### 5. What is DPO?

A) Direct Preference Optimization
B) Dynamic Parameter Optimization
C) Distributed Policy Optimization
D) Deep Prompt Optimization

### 6. What is the main advantage of DPO over RLHF?

A) No separate reward model needed
B) Faster training
C) Better accuracy
D) Simpler architecture

### 7. What does PPO stand for in RLHF context?

A) Proximal Policy Optimization
B) Progressive Parameter Optimization
C) Parallel Policy Optimization
D) None of the above

### 8. What is the purpose of the KL divergence penalty in RLHF?

A) Prevent model from deviating too far from reference
B) Speed up training
C) Improve accuracy
D) Reduce memory

### 9. What type of data is used for preference collection?

A) Labeled classification data
B) Paired comparisons: which response is better
C) Translation pairs
D) Question-answer pairs

### 10. What is a common issue with RLHF?

A) Too expensive
B) Reward hacking
C) Slow convergence
D) All of the above

---

## Answers

1. **B** - Ensure model outputs match human preferences and values
2. **A** - Reinforcement Learning from Human Feedback
3. **B** - Collect comparison data (response A vs B, which is better?)
4. **B** - Predict which response humans would prefer
5. **A** - Direct Preference Optimization (simpler than RLHF)
6. **A** - Directly optimizes from preferences, no reward model
7. **A** - Proximal Policy Optimization (the RL algorithm used)
8. **A** - KL penalty prevents collapse and keeps model close to reference
9. **B** - Paired comparisons from human labelers
10. **D** - All are challenges with RLHF

---

**Score:** ___ / 10
**Passing:** 7/10

**Next:** Review [PRACTICE.md](./PRACTICE.md) for hands-on exercises
