# Tutorial to Lab Bridge Guide

**Bridging the Gap Between Tutorials and Hands-on Labs**

---

## Overview

This guide helps you transition from tutorials (watching/reading) to labs (doing). We've identified gaps and created bridges to ensure smooth learning progression.

---

## 📚 Learning Pathway

```
ENVIRONMENT SETUP
        ↓
   TUTORIALS (Learn)
        ↓
   BRIDGE (Connect)
        ↓
    LABS (Practice)
        ↓
   PROJECTS (Build)
```

---

## 🎯 Tutorial → Lab Mappings

### Path 1: Local LLMs

**TUTORIAL-001: Hello LLM** (30 min)
↓
**LAB-000: Environment Setup** (45 min)
↓
**LAB-001: Docker & LLM** (2 hours)

**What You Learn:**
- Tutorial: Basic Ollama usage
- LAB-000: Complete environment setup
- LAB-001: Containerized LLM deployment

**Bridge Content:**
```bash
# From Tutorial: ollama run mistral "hello"
# To Lab: Docker container with Ollama

# Bridge: Understanding containers
docker run -d -p 11434:11434 ollama/ollama
```

---

### Path 2: Docker Essentials

**TUTORIAL-002: Docker Essentials** (45 min)
↓
**LAB-000: Environment Setup** (45 min)
↓
**LAB-001: Docker & LLM** (2 hours)

**What You Learn:**
- Tutorial: Docker commands and concepts
- LAB-000: Verify Docker installation
- LAB-001: Build and run LLM containers

**Bridge Content:**
```dockerfile
# From Tutorial: Basic Dockerfile
# To Lab: Multi-stage build for LLM

# Bridge: Optimizing images
FROM python:3.11-slim AS builder
# vs
FROM python:3.11-alpine
```

---

### Path 3: RAG Systems

**TUTORIAL-003: RAG Basics** (1 hour)
↓
**LAB-002: RAG Implementation** (3 hours)
↓
**LAB-005: GraphRAG** (5 hours)

**What You Learn:**
- Tutorial: RAG concepts and simple example
- LAB-002: Build RAG with Qdrant
- LAB-005: Add knowledge graphs

**Bridge Content:**
```python
# From Tutorial: Simple RAG
def simple_rag(query):
    docs = search(query)
    return generate(query, docs)

# To Lab: Production RAG
class ProductionRAG:
    def __init__(self):
        self.vector_db = QdrantClient()
        self.llm = Ollama()
        self.embedder = SentenceTransformer()

    def retrieve_and_generate(self, query):
        # Hybrid search, re-ranking, etc.
```

---

### Path 4: Fine-Tuning

**[TUTORIAL-007: LoRA Basics](../tutorials/TUTORIAL-007-LoRA-Basics.md)** (1 hour)
↓
**LAB-003: LoRA Fine-Tuning** (4 hours)
↓
**LAB-010: DPO Alignment** (5 hours)

**What You Learn:**
- Tutorial: LoRA concepts
- LAB-003: Fine-tune with QLoRA
- LAB-010: Apply DPO alignment

**Bridge Content:**
```python
# From Tutorial: LoRA concept
add_lora_layer(model, rank=8)

# To Lab: Full QLoRA pipeline
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
)
model = get_peft_model(base_model, config)
```

---

## 🌉 Common Gaps & Bridges

### Gap 1: Environment Differences

**Tutorial:** Simple commands, clean environment
**Lab:** Real-world complexity, multiple tools

**Bridge Strategy:**
1. LAB-000 ensures identical setup
2. Troubleshooting guides for common issues
3. Verification checklists

### Gap 2: Code Complexity

**Tutorial:** Minimal working example
**Lab:** Production-ready implementation

**Bridge Strategy:**
1. Show progression from simple → complex
2. Explain each addition
3. Comment why each line matters

### Gap 3: Error Handling

**Tutorial:** Often omitted for clarity
**Lab:** Essential for real use

**Bridge Strategy:**
```python
# Tutorial style (omitted)
result = api.call(data)

# Lab style (complete)
try:
    result = api.call(data)
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise
```

---

## 📋 Pre-Lab Checklist

Before starting any lab, ensure:

### Environment
- [ ] Completed LAB-000 (Environment Setup)
- [ ] All services running (Docker, Ollama, etc.)
- [ ] Can run basic commands without errors

### Knowledge
- [ ] Read corresponding tutorial
- [ ] Understand key concepts
- [ ] Reviewed prerequisite documentation

### Tools
- [ ] IDE/editor configured
- [ ] Terminal access working
- [ ] Git configured (if needed)

---

## 🔧 Lab Preparation Steps

### Step 1: Review Tutorial (30 min)

1. Watch/read tutorial completely
2. Run tutorial examples yourself
3. Note questions or unclear parts

### Step 2: Check Prerequisites (15 min)

1. Review lab prerequisites
2. Verify environment setup
3. Install missing dependencies

### Step 3: Mental Preparation (5 min)

1. Set realistic time expectations
2. Prepare for challenges/errors
3. Have reference material ready

---

## 💡 Lab Success Tips

### Start Simple
1. Run the provided code first
2. Verify it works
3. Then modify and experiment

### Debug Systematically
1. Read error messages carefully
2. Check common issues in troubleshooting guide
3. Use logs and print statements
4. Ask for help if stuck >30 min

### Build Understanding
1. Don't just copy code
2. Explain each section to yourself
3. Try variations and see what happens
4. Connect back to tutorial concepts

---

## 📊 Progression Difficulty

```
TUTORIAL Difficulty:
⭐ Beginner → ⭐⭐ Intermediate → ⭐⭐⭐ Advanced

LAB Difficulty:
⭐⭐ LAB-000 → ⭐⭐⭐ LAB-001 → ⭐⭐⭐⭐ LAB-002+

PROJECT Difficulty:
⭐⭐⭐ Beginner → ⭐⭐⭐⭐⭐ Advanced
```

**Key Insight:** Labs are harder than tutorials because they're hands-on. This is intentional and necessary for learning.

---

## 🚨 When to Ask for Help

### Green Flags (Keep Going)
- Minor errors you understand
- Documentation is clear
- You're learning from mistakes

### Yellow Flags (Slow Down)
- Repeated errors
- Unclear concepts
- Spending >30 min on one issue

### Red Flags (Ask for Help)
- Completely stuck
- Error makes no sense
- Lab assumes knowledge you don't have

**Where to get help:**
- [TROUBLESHOOTING-QUICKSTART.md](../../00-META/TROUBLESHOOTING-QUICKSTART.md)
- [Troubleshooting Guide](../troubleshooting/TROUBLESHOOTING-Common-Issues.md)
- Community forums
- Project issues

---

## ✅ Post-Lab Reflection

After completing each lab, ask yourself:

1. **What did I learn?** (Write 3 key points)
2. **What was challenging?** (Note for review)
3. **What would I explain differently?** (Teach someone)
4. **How can I apply this?** (Think of projects)

---

## 📈 Recommended Sequences

### Beginner Track
```
QUICK-START → TUTORIAL-001 → LAB-000 → LAB-001
```

### RAG Focus
```
TUTORIAL-003 → LAB-002 → LAB-005 → LAB-007 → PROJECT-006
```

### Agent Focus
```
LAB-004 → LAB-008 → PROJECT-001 → PROJECT-007
```

### Full Curriculum
```
Volume 1 → Volume 3 → Volume 5 → Volume 6 → Volume 7
```

---

## 🎯 Bridge Checkpoints

Use these checkpoints to verify readiness:

### After TUTORIAL-001
- [ ] Can run Ollama CLI
- [ ] Understand basic chat
- [ ] Ready for LAB-000

### After LAB-000
- [ ] Environment fully set up
- [ ] All services verified
- [ ] Ready for LAB-001

### After LAB-001
- [ ] Docker basics understood
- [ ] Can containerize LLM
- [ ] Ready for LAB-002

---

## 📚 Additional Resources

### Learning Resources
- [ENVIRONMENT-SETUP.md](../../00-META/ENVIRONMENT-SETUP.md)
- [GLOSSARY.md](../../00-META/GLOSSARY.md)
- [PROGRESS-TRACKER.md](../../00-META/PROGRESS-TRACKER.md)

### Practice Resources
- [CHEAT SHEET 001: Docker](../cheat-sheets/CHEAT-SHEET-001-Docker.md)
- [CHEAT SHEET 002: Python AI](../cheat-sheets/CHEAT-SHEET-002-Python-AI.md)

### Support Resources
- [Troubleshooting Guide](../troubleshooting/TROUBLESHOOTING-Common-Issues.md)
- Community forums
- Office hours (if available)

---

## 🎉 Celebrate Progress

Learning AI is challenging! Celebrate milestones:

- ✅ First lab completed
- ✅ First bug fixed independently
- ✅ First project finished
- ✅ Each volume completed

**Remember:** Progress, not perfection. Every mistake is learning.

---

**Last Updated:** 2026-02-04
**Version:** 1.0

**Ready to start?** Begin with [QUICK-START.md](../../00-META/QUICK-START.md)
