---
Document ID: ASSESSMENT-GUIDE
Title: "Assessment Guide"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Tags: ['assessment', 'quiz', 'practice']
---

# Assessment Guide

**Purpose:** Comprehensive assessment system for learning validation

---

## Overview

This guide provides assessment materials for each phase of Minder Academy, including quizzes, practical exams, and project evaluation rubrics.

## Two-Tier Assessment System

Assessment happens at two levels. Finish the module checkpoint before moving
to the next module; finish the phase exam before moving to the next phase.

| Tier | Location | Format | When |
|------|----------|--------|------|
| Module checkpoint | `<module>/assessment/QUIZ.md` + `PRACTICE.md` | 20 multiple-choice questions, 80% to pass, plus hands-on practice | End of each module |
| Phase exam | `docs/00-META/assessment/phaseN-quiz.md` + `phaseN-practice.md` | 15-30 cumulative questions, 80% to pass, plus hands-on exercises | End of each phase |

Phase quizzes and practice sets live in `docs/00-META/assessment/` (phase1
through phase7). Phase quiz sizes: 15 / 20 / 25 / 30 / 30 / 30 / 30 questions.

---

## Assessment Structure

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                     Assessment Types                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  KNOWLEDGE CHECKS (Per Phase)                                    │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Multiple Choice Questions                                     │   │
│  │  • True/False Questions                                         │   │
│  │  • Short Answer Questions                                       │   │
│  │  • Code Completion Exercises                                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  PRACTICAL ASSESSMENTS (Per Lab)                                  │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Lab Completion Verification                                   │   │
│  │  • Code Review                                                  │   │
│  │  • Debugging Challenges                                         │   │
│  │  • Performance Optimization Tasks                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  CAPSTONE PROJECT EVALUATION                                     │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Technical Implementation (40%)                                │   │
│  │  • Code Quality (20%)                                           │   │
│  │  • Documentation (15%)                                          │   │
│  │  • Testing & Validation (15%)                                   │   │
│  │  • Deployment & Operations (10%)                                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Quizzes

### Phase 1: Infrastructure (15 Questions)

```markdown
1. What is the primary purpose of jumbo frames in network configuration?
   a) Reduce packet overhead
   b) Increase security
   c) Improve encryption
   d) Reduce latency
   Answer: a

2. Which Kubernetes component manages GPU scheduling?
   a) kube-scheduler
   b) device plugin
   c) kubelet
   d) controller-manager
   Answer: b

[... 13 more questions ...]
```

### Phase 2: Foundations (20 Questions)

```markdown
1. What does the backward pass in neural networks compute?
   a) Gradients of loss with respect to parameters
   b) Forward predictions
   c) Activation values
   d) Learning rate
   Answer: a

2. In PyTorch, what is a computational graph?
   a) Dynamic representation of computations
   b) Static memory allocation
   c) Data storage structure
   d) Network architecture
   Answer: a

[... 18 more questions ...]
```

### Phase 3: Transformers (25 Questions)

```markdown
1. What is the key innovation of self-attention?
   a) Computing relationships between all tokens
   b) Reducing model size
   c) Faster training
   d) Less memory usage
   Answer: a

2. What problem does RoPE (Rotary Position Embedding) solve?
   a) Position encoding for long sequences
   b) Memory optimization
   c) Faster inference
   d) Better generalization
   Answer: a

[... 23 more questions ...]
```

### Phase 4: Quantization (30 Questions)

```markdown
1. What is the main benefit of GGUF quantization?
   a) Runs on consumer hardware
   b) Improves accuracy
   c) Faster training
   d) Smaller model file
   Answer: a

2. What does double quantization reduce?
   a) Memory footprint of quantization constants
   b) Model size
   c) Training time
   d) Inference latency
   Answer: a

[... 28 more questions ...]
```

### Phase 5: Fine-tuning (30 Questions)

```markdown
1. What is the rank 'r' in LoRA?
   a) Dimension of low-rank matrices
   b) Learning rate
   c) Batch size
   d) Number of layers
   Answer: a

2. What makes DPO simpler than PPO?
   a) No reward model needed
   b) Faster training
   c) Better data
   d) More accurate
   Answer: a

[... 28 more questions ...]
```

### Phase 6: RAG (30 Questions)

```markdown
1. What is HNSW in vector databases?
   a) Hierarchical graph index
   b) Hash-based index
   c) Tree structure
   d) Linear scan
   Answer: a

2. What is the benefit of hybrid search?
   a) Combines keyword and semantic search
   b) Faster queries
   c) Less memory
   d) Simpler code
   Answer: a

[... 28 more questions ...]
```

### Phase 7: Agents (30 Questions)

```markdown
1. What is the core idea of ReAct?
   a) Reasoning + Acting loop
   b) Multi-agent system
   c) Tool calling
   d) Memory management
   Answer: a

2. What does a sandboxed code executor provide?
   a) Safe code execution environment
   b) Faster execution
   c) Better accuracy
   d) Less memory
   Answer: a

[... 28 more questions ...]
```

---

## Project Rubrics

### PROJECT-001: AI Assistant Rubric

```markdown
# PROJECT-001: AI Assistant Evaluation Rubric

## Technical Implementation (40 points)

### RAG Service (12 points)
- [ ] 4 points: Vector search with Qdrant working
- [ ] 4 points: Graph search with Neo4j working
- [ ] 4 points: Re-ranking implementation

### ReAct Agent (12 points)
- [ ] 4 points: Agent loop logic correct
- [ ] 4 points: Tool calling functional
- [ ] 4 points: Memory integration

### Tool Executor (8 points)
- [ ] 4 points: Sandboxing implemented
- [ ] 4 points: Error handling robust

### Web Frontend (8 points)
- [ ] 4 points: UI functional and responsive
- [ ] 4 points: Real-time streaming works

## Code Quality (20 points)
- [ ] 10 points: Clean, readable code with comments
- [ ] 5 points: Proper error handling throughout
- [ ] 5 points: Follows Python best practices

## Documentation (15 points)
- [ ] 5 points: README with setup instructions
- [ ] 5 points: API documentation
- [ ] 5 points: Architecture diagram

## Testing & Validation (15 points)
- [ ] 8 points: Unit tests for core components
- [ ] 4 points: Integration tests
- [ ] 3 points: Example queries demonstrated

## Deployment & Operations (10 points)
- [ ] 5 points: Docker Compose works
- [ ] 3 points: Environment variables configured
- [ ] 2 points: Basic monitoring configured

## Bonus Points (5 points)
- [ ] 2 points: Advanced features (caching, rate limiting)
- [ ] 2 points: Performance optimization
- [ ] 1 point: Extra polish (UI/UX)

**Total: 100 + 5 bonus points**

### Grade Scale:
- 90-100: A (Exceptional)
- 80-89: B (Good)
- 70-79: C (Satisfactory)
- 60-69: D (Needs improvement)
- < 60: F (Incomplete)
```

### PROJECT-002: Neural Network Rubric

```markdown
# PROJECT-002: Neural Network from Scratch Rubric

## Implementation (50 points)
- [ ] 15 points: Forward pass correct
- [ ] 15 points: Backward pass correct
- [ ] 10 points: Training loop works
- [ ] 10 points: Model converges (accuracy > 80%)

## Understanding (30 points)
- [ ] 15 points: Code demonstrates mathematical understanding
- [ ] 15 points: Explanations are clear and accurate

## Code Quality (20 points)
- [ ] 10 points: Clean, well-organized code
- [ ] 10 points: Proper documentation

**Total: 100 points**
```

---

## Skills Verification

### Phase Completion Checklist

After completing each phase, learners should be able to:

**Phase 1 - Infrastructure:**
- [ ] Set up Docker containerized applications
- [ ] Configure multi-gigabit network with jumbo frames
- [ ] Deploy GPU-enabled workloads
- [ ] Monitor system with Prometheus/Grafana

**Phase 2 - Foundations:**
- [ ] Implement backpropagation from scratch
- [ ] Build PyTorch computational graphs
- [ ] Understand transformer architecture
- [ ] Calculate tensor operations

**Phase 3 - Transformers:**
- [ ] Implement self-attention mechanism
- [ ] Use RoPE for position encoding
- [ ] Work with different model architectures
- [ ] Optimize transformer inference

**Phase 4 - Quantization:**
- [ ] Quantize models with GGUF
- [ ] Implement AWQ/EXL2 quantization
- [ ] Optimize context windows
- [ ] Benchmark quantized models

**Phase 5 - Fine-tuning:**
- [ ] Implement LoRA fine-tuning
- [ ] Use QLoRA for efficient training
- [ ] Apply DPO for alignment
- [ ] Distill large models

**Phase 6 - RAG:**
- [ ] Build vector search systems
- [ ] Implement hybrid search
- [ ] Create GraphRAG systems
- [ ] Deploy production RAG

**Phase 7 - Agents:**
- [ ] Implement ReAct agents
- [ ] Build multi-agent systems
- [ ] Add tool calling capabilities
- [ ] Implement agent memory

---

## Certification Criteria

### Minder Academy Certification: Associate

**Requirements:**
- Complete all 7 phase quizzes (80%+ passing grade)
- Complete 3 capstone projects (B grade or higher)
- Pass practical skills verification

**Time Estimate:** 3-6 months

### Minder Academy Certification: Professional

**Requirements:**
- Complete all 7 phase quizzes (90%+ passing grade)
- Complete 5 capstone projects (A grade)
- Pass 48-hour practical exam
- Submit production-ready project

**Time Estimate:** 6-12 months

---

## Assessment Administration

### Quiz Format
- **Platform:** Automated (Moodle, Canvas, or custom)
- **Duration:** 30-45 minutes per quiz
- **Attempts:** 2 attempts allowed
- **Passing Score:** 80%

### Project Submission
- **Format:** GitHub repository + documentation
- **Review:** Peer review + instructor evaluation
- **Timeline:** 2-4 weeks per project
- **Feedback:** Detailed rubric-based feedback

### Certification Exam
- **Format:** 48-hour take-home project + 2-hour oral defense
- **Scope:** End-to-end AI system development
- **Evaluation:** Technical depth + practical skills + communication

---

## Tracking Progress

Use the **PROGRESS-TRACKER.md** file to track:
- Phase completion status
- Quiz scores
- Project submissions
- Skill milestones
- Certification progress

---

**Next Steps:** Complete all phase quizzes and submit projects for evaluation
