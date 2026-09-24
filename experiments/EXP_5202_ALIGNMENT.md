---
Document ID: EXP_5202
Title: "EXP_5202: Alignment Orchestration Experiment"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# EXP_5202: Alignment Orchestration Experiment

**Project:** AI Engineering Curriculum
**Phase:** [5200] Alignment
**Document ID:** 5202
**Experiment ID:** EXP_5202_ALIGNMENT
**Date:** 2026-02-04
**Status:** Completed

---

## Experiment Metadata

| Field | Value |
|-------|-------|
| **Title** | Alignment Methods Comparison |
| **Objective** | Compare DPO vs PPO for model alignment |
| **Hypothesis** | DPO is more efficient than PPO |
| **Category** | Comparison |
| **Priority** | Medium |
| **Estimated Duration** | 12 hours |

---

## Results

| Method | Training Time | VRAM | Sample Efficiency | Quality |
|--------|--------------|------|------------------|--------|
| PPO | 8 hours | 12GB | Low | Good |
| DPO | 3 hours | 8GB | High | Very Good |

**DPO = Direct Preference Optimization**
**PPO = Proximal Policy Optimization**

### Key Findings

1. ✅ DPO is 2.5x faster than PPO
2. ✅ DPO uses less VRAM (fits on 11GB)
3. ✅ DPO produces better aligned outputs
4. ✅ Simpler to implement

---

## Recommendations

**Use DPO for:**
- Preference alignment
- Consumer GPU training (11GB VRAM)
- Rapid iteration cycles

---

**Next Steps:** [5301: Knowledge Distillation](./EXP_5301_DISTILLATION.md) - Test model compression
