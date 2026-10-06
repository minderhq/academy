---
Document ID: VOLUME-GUIDE
Title: "Minder Academy: Volume Guide (Book Structure)"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Tags: ['volume', 'roadmap', 'llm']
---

# Minder Academy: Volume Guide (Book Structure)

**Welcome to Minder Academy!** This curriculum is organized as a **7-volume book series**, taking you from complete beginner to production-ready AI infrastructure expert.

---

## How to Use This Guide

### **Are you new to Minder Academy?**
Start here: **[QUICK-START.md](./QUICK-START.md)** (30 minutes)

### **Want to track your progress?**
Use: **[PROGRESS-TRACKER.md](./PROGRESS-TRACKER.md)**

### **Ready to dive deep?**
Follow the volumes below, in order.

---

## Volume Overview

| Volume | Title | Difficulty | Time | Focus |
|--------|-------|------------|------|-------|
| **[Volume 1](#volume-1-infrastructure-fundamentals)** | Infrastructure Fundamentals | ⭐⭐ Intermediate | 4-6 weeks | Docker, networks, local LLMs |
| **[Volume 2](#volume-2-aiml-foundations)** | AI/ML Foundations | ⭐⭐⭐ Advanced | 8-12 weeks | Math, frameworks, model internals |
| **[Volume 3](#volume-3-llm-internals--architecture)** | LLM Internals & Architecture | ⭐⭐⭐ Advanced | 6-8 weeks | Transformers, attention, embeddings |
| **[Volume 4](#volume-4-quantization--optimization)** | Quantization & Optimization | ⭐⭐⭐ Advanced | 5-7 weeks | 4-bit, GGUF, context windows |
| **[Volume 5](#volume-5-model-adaptation)** | Model Adaptation | ⭐⭐⭐ Advanced | 6-8 weeks | LoRA, QLoRA, DPO, alignment |
| **[Volume 6](#volume-6-data-nexus-rag--memory)** | Data Nexus: RAG & Memory | ⭐⭐⭐ Advanced | 6-8 weeks | Vector DBs, GraphRAG, agents |
| **[Volume 7](#volume-7-production-mastery)** | Production Mastery | ⭐⭐⭐⭐ Expert | 8-10 weeks | CI/CD, scaling, monitoring |

**Total Time:** 12-18 months (realistic pace for 10-15 hours/week)

---

## Volume 1: Infrastructure Fundamentals

**Goal:** Set up your AI lab and run your first local LLMs.

### Prerequisites
- Basic computer literacy
- 8GB+ RAM (16GB+ recommended)
- Windows, Mac, or Linux

### Learning Path

**Step 1: Quick Start (30 min)**
1. [QUICK-START.md](QUICK-START.md) - Run your first LLM
2. [CHEAT-SHEET-001-Docker.md](../learning-resources/cheat-sheets/CHEAT-SHEET-001-Docker.md) - Docker basics
3. [CHEAT-SHEET-002-Python-AI.md](../learning-resources/cheat-sheets/CHEAT-SHEET-002-Python-AI.md) - Python for AI

**Step 2: Docker & LLM Lab (3 hours)**
1. [TUTORIAL-002: Docker Essentials](../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md)
2. [LAB-001: Docker & LLM](../learning-resources/labs/LAB-001-Docker-LLM.md)

**Step 3: Network & Hardware (optional)**
1. [1101: Internet Uplink & Modem Configuration](../phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md)
2. [1102: Star Topology Core](../phases/phase1-infra/1100-network/1102-Star-Topology-Core.md)
3. [1201: Proxmox Hypervisor SOP](../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)

**Step 4: Ollama & Local Models (2 hours)**
1. [1401: Ollama Enterprise](../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)
2. [TUTORIAL-001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)

**Step 5: K3s & Container Orchestration (optional)**
1. [1301: K3s Architecture](../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md)
2. [1302: GPU Scheduler](../phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)

### Volume 1 Capstone: PROJECT-001
- [PROJECT-001: AI Assistant](../learning-resources/projects/PROJECT-001-AI-Assistant.md) - Build your first AI assistant

### After Volume 1, you can:
- ✅ Run LLMs locally
- ✅ Containerize applications with Docker
- ✅ Build basic AI applications
- ✅ Understand network topology

---

## Volume 2: AI/ML Foundations

**Goal:** Understand the mathematics and frameworks behind AI.

### Prerequisites
- Complete Volume 1
- High school math (algebra, basic calculus)
- Python programming

### Learning Path

**Step 1: Math Foundations (2 weeks)**
1. [2101: Tensor Algebra](../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)
2. [2102: Backpropagation](../phases/phase2-foundations/2100-calculus/2102-Backpropagation-and-Derivatives.md)

**Step 2: Framework Deep Dive (2 weeks)**
1. [2201: PyTorch Graphs](../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)
2. [2202: TensorFlow XLA](../phases/phase2-foundations/2200-frameworks/2202-TensorFlow-XLA-Compilers.md)
3. [2203: CUDA Kernels](../phases/phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Programming.md)

**Step 3: Linux & Git (1 day)**
1. [CHEAT-SHEET-003: Git](../learning-resources/cheat-sheets/CHEAT-SHEET-003-Git.md)
2. [CHEAT-SHEET-004: Linux](../learning-resources/cheat-sheets/CHEAT-SHEET-004-Linux.md)

### Volume 2 Experiments
- [EXP_2101: Tensor Operations](../../experiments/EXP_2101_TENSOR_ALGEBRA.md)
- [EXP_2102: Gradient Descent](../../experiments/EXP_2102_BACKPROPAGATION.md)

### After Volume 2, you can:
- ✅ Understand tensor operations
- ✅ Implement backpropagation
- ✅ Optimize PyTorch models
- ✅ Write CUDA kernels (basic)

---

## Volume 3: LLM Internals & Architecture

**Goal:** Understand how transformers and LLMs work internally.

### Prerequisites
- Complete Volume 2
- Understanding of neural networks

### Learning Path

**Step 1: Attention Mechanisms (1 week)**
1. [3101: Self-Attention](../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)
2. [3102: Flash Attention](../phases/phase3-transformers/3100-attention/3102-Flash-Attention.md)
3. [Experiment: Flash Attention](../../experiments/EXP_3102_FLASH_ATTENTION.md)

**Step 2: Embeddings & Tokenization (1 week)**
1. [3201: RoPE](../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)
2. [3202: Tokenizer Sciences](../phases/phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md)
3. [Experiment: RoPE](../../experiments/EXP_3201_ROPE.md)
4. [Experiment: Tokenizers](../../experiments/EXP_3202_TOKENIZER.md)

**Step 3: Decoding & Normalization (1 week)**
1. [3301: Activation Functions](../phases/phase3-transformers/3300-decoding/3301-Activation-Functions.md)
2. [3302: Normalization Layers](../phases/phase3-transformers/3300-decoding/3302-Normalization-Layers.md)

**Step 4: Model Architectures (1 week)**
1. [3401: Encoder-Decoder Architectures](../phases/phase3-transformers/3400-architectures/3401-Encoder-Decoder-Architectures.md)
2. [3402: Decoder-Only Models](../phases/phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md)

**Step 5: Multimodal Models (1 week)**
1. [3501: Vision-Language Models](../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md)
2. [3502: Audio Models](../phases/phase3-transformers/3500-multimodal/3502-Audio-Models.md)
3. [Experiment: Multimodal RAG](../../experiments/EXP_3501_MULTIMODAL_RAG.md)

### Volume 3 Capstone
- Decode a transformer model step-by-step
- Implement self-attention from scratch

### After Volume 3, you can:
- ✅ Explain transformer architecture
- ✅ Implement attention mechanisms
- ✅ Understand tokenization
- ✅ Compare model architectures

---

## Volume 4: Quantization & Optimization

**Goal:** Run large models on limited hardware (11GB VRAM optimization).

### Prerequisites
- Complete Volume 3
- NVIDIA GPU recommended

### Learning Path

**Step 1: Low-Bit Quantization (2 weeks)**
1. [4101: GGUF Physics](../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
2. [4102: EXL2 and AWQ](../phases/phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md)
3. [4103: Double Quantization](../phases/phase4-quantization/4100-low-bit/4103-Double-Quantization.md)

**Step 2: Context Window Engineering (2 weeks)**
1. [4201: Context Window Physics](../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
2. [4202: Speculative Decoding](../phases/phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md)
3. [4203: Context Window Optimization](../phases/phase4-quantization/4200-kv-cache/guides/4203-Context-Window-Optimization.md)

**Step 3: Inference Engines (1 week)**
1. [1402: vLLM and TGI](../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
2. [1403: vLLM Production Deployment](../phases/phase1-infra/1400-llmops/guides/1403-vLLM-Production-Deployment.md)
3. [1404: TGI Deployment Guide](../phases/phase1-infra/1400-llmops/guides/1404-TGI-Deployment-Guide.md)

### Volume 4 Experiments
- [EXP_4201: Context Window](../../experiments/EXP_4201_CONTEXT_WINDOW.md)
- [EXP_4202: Speculative Decoding](../../experiments/EXP_4202_SPECULATIVE_DECODING.md)

### Volume 4 Capstone
- Run a 70B model on 11GB VRAM using quantization
- Optimize inference speed with speculative decoding

### After Volume 4, you can:
- ✅ Quantize models to 4-bit
- ✅ Optimize context windows
- ✅ Use vLLM/TGI in production
- ✅ Run models beyond VRAM limits

---

## Volume 5: Model Adaptation

**Goal:** Fine-tune models for your specific use cases.

### Prerequisites
- Complete Volume 4
- GPU with 8GB+ VRAM

### Learning Path

**Step 1: LoRA Fundamentals (1 week)**
1. [5101: LoRA Logic](../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
2. [5104: LoRA Implementation Guide](../phases/phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md)

**Step 2: QLoRA Pipelines (2 weeks)**
1. [5102: QLoRA Pipelines](../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)
2. [LAB-003: LoRA Fine-Tuning](../learning-resources/labs/LAB-003-LoRA-FineTuning.md)

**Step 3: Alignment (1 week)**
1. [5201: DPO Theory](../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)
2. [5202: Alignment Orchestration](../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md)
3. [EXP_5201: DPO Experiments](../../experiments/EXP_5201_DPO.md)
4. [EXP_5303: Federated Learning](../../experiments/EXP_5303_FEDERATED_LEARNING.md)

**Step 4: Synthetic Data (1 week)**
1. [5301: Knowledge Distillation](../phases/phase5-finetuning/5300-synthetic/5301-Knowledge-Distillation.md)
2. [5302: Distributed Training](../phases/phase5-finetuning/5300-synthetic/5302-Distributed-Training.md)
3. [5303: Federated Learning](../phases/phase5-finetuning/5300-synthetic/5303-Federated-Learning.md)

### Volume 5 Capstone
- Fine-tune Mistral 7B on your custom dataset
- Apply DPO alignment to improve responses

### After Volume 5, you can:
- ✅ Implement LoRA from scratch
- ✅ Fine-tune models with QLoRA
- ✅ Apply DPO alignment
- ✅ Generate synthetic training data

---

## Volume 6: Data Nexus: RAG & Memory

**Goal:** Give LLMs access to external knowledge and memory.

### Prerequisites
- Complete Volume 5
- Understanding of vector databases

### Learning Path

**Step 1: Vector Similarity (1 week)**
1. [6101: HNSW Indexing](../phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md)
2. [6102: Semantic Similarity](../phases/phase6-rag/6100-vector/6102-Semantic-Similarity.md)

**Step 2: RAG Fundamentals (2 weeks)**
1. [TUTORIAL-003: RAG Basics](../learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md)
2. [LAB-002: RAG Implementation](../learning-resources/labs/LAB-002-RAG-Implementation.md)
3. [6201: Hybrid Search](../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)
4. [6202: Re-ranking](../phases/phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md)

**Step 3: Knowledge Graphs (2 weeks)**
1. [6301: Neo4j and Knowledge Graphs](../phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md)
2. [6302: CAG Long Context](../phases/phase6-rag/6300-context/6302-CAG-Long-Context-Architectures.md)
3. [6304: GraphRAG Implementation](../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md)
4. [LAB-005: GraphRAG](../learning-resources/labs/LAB-005-GraphRAG.md)

**Step 4: MLOps Pipelines (2 weeks)**
1. [6501: ML Lifecycle Management](../phases/phase6-rag/6500-mlops-pipelines/6501-ML-Lifecycle-Management.md)
2. [6502: CI/CD for ML](../phases/phase6-rag/6500-mlops-pipelines/6502-CI-CD-for-ML.md)
3. [6503: Model Registry](../phases/phase6-rag/6500-mlops-pipelines/6503-Model-Registry.md)

### Volume 6 Experiments
- [EXP_6201: Hybrid Search](../../experiments/EXP_6201_HYBRID_SEARCH.md)
- [EXP_6301: GraphRAG](../../experiments/EXP_6301_GRAPHRAG.md)
- [EXP_6501: MLOps Pipeline](../../experiments/EXP_6501_MLOPS_PIPELINE.md)

### Volume 6 Capstone
- Build production RAG system with Qdrant
- Implement GraphRAG with Neo4j

### After Volume 6, you can:
- ✅ Build RAG systems
- ✅ Use vector databases effectively
- ✅ Implement knowledge graphs
- ✅ Combine vector + graph search

---

## Volume 7: Production Mastery

**Goal:** Deploy and scale AI systems in production.

### Prerequisites
- Complete Volume 6
- Understanding of DevOps basics

### Learning Path

**Step 1: Monitoring & Observability (1 week)**
1. [TUTORIAL-004: Monitoring](../learning-resources/tutorials/TUTORIAL-004-Monitoring.md)
2. [1501: Monitoring Stack](../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
3. [1502: Model Drift Detection](../phases/phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md)
4. [1503: LLM Observability](../phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md)

**Step 2: Production Deployment (2 weeks)**
1. [TUTORIAL-005: Production Deployment](../learning-resources/tutorials/TUTORIAL-005-Production-Deployment.md)
2. [TROUBLESHOOTING: Common Issues](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)

**Step 3: Agentic Systems (2 weeks)**
1. [7101: ReAct Loop](../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
2. [7102: Planning](../phases/phase7-agentic/7100-architecture/7102-Planning-Decomposition.md)
3. [LAB-004: ReAct Agent](../learning-resources/labs/LAB-004-ReAct-Agent.md)
4. [7303: AutoGen vs LangGraph](../phases/phase7-agentic/7300-orchestration/guides/7303-Framework-Comparison.md)
5. [7301: Orchestration](../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md)

**Step 4: Tool Calling & Memory (1 week)**
1. [7201: Tool Calling](../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md)
2. [7402: Memory Implementation](../phases/phase7-agentic/7400-memory/guides/7402-Agent-Memory-Implementation.md)

**Step 5: AI Security (1 week)**
1. [7501: Prompt Injection Defense](../phases/phase7-agentic/7500-security/7501-Prompt-Injection-Defense.md)
2. [7502: PII Redaction](../phases/phase7-agentic/7500-security/7502-PII-Redaction.md)
3. [7503: Adversarial Attacks](../phases/phase7-agentic/7500-security/7503-Adversarial-Attacks.md)
4. [EXP_7501: Prompt Injection](../../experiments/EXP_7501_PROMPT_INJECTION.md)

### Volume 7 Capstone
- Deploy full AI system with monitoring
- Build multi-agent system
- Set up CI/CD pipeline

### After Volume 7, you can:
- ✅ Deploy to production
- ✅ Set up monitoring stack
- ✅ Build agent systems
- ✅ Implement CI/CD

---

## Recommended Reading Paths

### Path 1: Fast Track to Production (8-10 weeks)
**For developers who want to deploy quickly**

```text
Volume 1 (2 weeks) → Volume 3 (3 weeks) → Volume 4 (2 weeks) → Volume 7 (3 weeks)
```

### Path 2: Deep Learning Research (6-8 months)
**For those who want to understand everything**

```text
Volume 1 → Volume 2 → Volume 3 → Volume 4 → Volume 5 → Volume 6 → Volume 7
```

### Path 3: RAG Specialist (10-12 weeks)
**Focus on retrieval-augmented generation**

```text
Volume 1 (2 weeks) → Volume 3 (3 weeks) → Volume 6 (5 weeks) → Volume 7 (2 weeks)
```

### Path 4: Fine-Tuning Expert (10-12 weeks)
**Focus on model adaptation**

```text
Volume 1 (2 weeks) → Volume 2 (2 weeks) → Volume 4 (3 weeks) → Volume 5 (5 weeks)
```

---

## Progress Tracking

Track your progress using: **[PROGRESS-TRACKER.md](PROGRESS-TRACKER.md)**

### Badges You Can Earn

| Badge | Requirement | Volume |
|-------|-------------|--------|
| 🐳 Docker Novice | Complete LAB-001 | 1 |
| 🚀 Local LLM Runner | Complete TUTORIAL-001 | 1 |
| 📐 Tensor Master | Complete Volume 2 | 2 |
| 🤖 Transformer Expert | Complete Volume 3 | 3 |
| ⚡ Quantization Ninja | Run 70B on 11GB VRAM | 4 |
| 🎨 Fine-Tuning Artist | Complete LAB-003 | 5 |
| 🔍 RAG Specialist | Complete LAB-002 + LAB-005 | 6 |
| 🏗️ Production Architect | Complete Volume 7 | 7 |

---

## Need Help?

### Stuck on a concept?
- Check the [troubleshooting guide](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)
- Review the [cheat sheets](../learning-resources/cheat-sheets/)
- Look at the [experiments](../../experiments/) for practical examples

### Want to learn more?
- Each document has cross-references to related topics
- Follow the "Next Steps" links at the bottom of each page
- Check the [SITEMAP.md](SITEMAP.md) for all available resources

---

## Document Structure

```text
Minder Academy/docs/
├── 00-META/                     # Meta documentation
│   ├── VOLUME-GUIDE.md          # This file - volume overview
│   ├── QUICK-START.md           # 30-minute quick start
│   ├── PROGRESS-TRACKER.md      # Track your learning
│   ├── SITEMAP.md               # All 424 documents
│   └── 0000-LEARNING-PATH.md    # Curriculum roadmap
│
├── phases/                      # Phase-based technical documentation
│   ├── phase1-infra/            # [1000] Infrastructure Fabric
│   ├── phase2-foundations/      # [2000] AI/ML Foundations
│   ├── phase3-transformers/     # [3000] LLM Architecture
│   ├── phase4-quantization/     # [4000] Quantization & Compression
│   ├── phase5-finetuning/       # [5000] Model Adaptation
│   ├── phase6-rag/              # [6000] Data Nexus
│   └── phase7-agentic/          # [7000] Agentic Systems
│
├── learning-resources/          # Additional learning materials
│   ├── tutorials/               # Step-by-step tutorials (15 files)
│   ├── labs/                    # Hands-on lab exercises (15 labs + 15 solutions)
│   ├── cheat-sheets/            # Quick reference guides (13 files)
│   ├── troubleshooting/         # Common issues & solutions
│   └── projects/                # Capstone projects (7 files)
│
├── use-cases/                   # Real-world use cases & applications
│   ├── README.md
│   ├── UC-001-Vector-Database-Applications.md
│   ├── UC-002-RAG-Applications.md
│   └── UC-003-Agent-Applications.md
│
├── comparisons/                 # Technology comparison guides
│   ├── README.md
│   ├── CP-001-RAG-vs-FineTuning-vs-Agents.md
│   └── CP-002-Vector-Database-Comparison.md
│
├── industry/                    # Industry-specific applications
│   ├── README.md
│   ├── IND-001-Healthcare-AI-Applications.md
│   ├── IND-002-Finance-AI-Applications.md
│   └── IND-003-Manufacturing-AI.md
│
├── solutions/                   # End-to-end implementation guides
│   ├── README.md
│   ├── SOL-001-Enterprise-Knowledge-Base.md
│   └── SOL-002-Industry-Solution.md
│
└── volumes/                     # Volume-based learning units
    ├── VOLUME-1-Infrastructure.md
    ├── VOLUME-2-AI-Foundations.md
    ├── VOLUME-3-LLM-Internals.md
    ├── VOLUME-4-Quantization.md
    ├── VOLUME-5-Model-Adaptation.md
    ├── VOLUME-6-Data-Nexus.md
    └── VOLUME-7-Production-Mastery.md

Minder Academy/
└── experiments/                 # Practical experiments (47 files)
```

---

**Ready to begin?** Start with **[QUICK-START.md](QUICK-START.md)** and track your progress in **[PROGRESS-TRACKER.md](PROGRESS-TRACKER.md)**!

**Total Documents:** 424 files across 7 volumes
