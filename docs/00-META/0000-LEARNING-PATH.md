# PROJECT-OMEGA Learning Path
## Complete AI/LLM Infrastructure Curriculum - From Zero to Hero

**Last Updated:** 2026-02-07
**Estimated Time:** 6-12 months (part-time)
**Prerequisites:** None! We start from absolute zero.

---

## 📚 Curriculum Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROJECT-OMEGA LEARNING PATH                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Phase 0: Python Fundamentals (Week 1) :star3: NEW                      │
│  ├── Python Basics (variables, functions, loops)                        │
│  ├── Data Structures (lists, dicts, tuples)                             │
│  ├── OOP Fundamentals (classes, methods)                                │
│  └── AI-Specific Python (NumPy, type hints, async)                      │
│                                                                           │
│  Phase 1: Foundations (Weeks 2-5)                                        │
│  ├── Linux & Docker Fundamentals                                        │
│  ├── Networking Basics                                                  │
│  └── Hardware Architecture                                              │
│                                                                           │
│  Phase 2: Infrastructure (Weeks 6-13)                                    │
│  ├── Virtualization (Proxmox)                                            │
│  ├── Container Orchestration (K3s)                                      │
│  ├── GPU Passthrough & Drivers                                          │
│  └── Network Topology (2.5Gbps)                                          │
│                                                                           │
│  Phase 3: AI/ML Fundamentals (Weeks 13-20)                               │
│  ├── Neural Network Architecture                                         │
│  ├── Transformers & Attention                                           │
│  ├── Quantization Techniques                                            │
│  └── Model Evaluation                                                   │
│                                                                           │
│  Phase 4: LLMOps (Weeks 21-28)                                           │
│  ├── Model Serving (vLLM/TGI)                                            │
│  ├── Prompt Engineering                                                 │
│  ├── Fine-Tuning (LoRA/QLoRA)                                            │
│  └── Alignment (DPO/RLHF)                                                │
│                                                                           │
│  Phase 5: RAG & Knowledge (Weeks 29-36)                                  │
│  ├── Vector Databases (Qdrant)                                           │
│  ├── Knowledge Graphs (Neo4j)                                            │
│  ├── Hybrid Search                                                      │
│  └── GraphRAG Architecture                                               │
│                                                                           │
│  Phase 6: Agentic AI (Weeks 37-44)                                       │
│  ├── ReAct Agents                                                       │
│  ├── Multi-Agent Systems                                                │
│  ├── Tool Calling                                                       │
│  └── Agent Memory                                                        │
│                                                                           │
│  Phase 7: Production (Weeks 45-52)                                       │
│  ├── Monitoring & Observability                                         │
│  ├── CI/CD Pipelines                                                    │
│  ├── Security & SSL/TLS                                                 │
│  └── Performance Optimization                                           │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Python Fundamentals (Week 1) :star3: NEW

### For Complete Beginners

**Goal:** Learn Python programming from absolute zero

```
Learning Path:
├── [TUTORIAL-000: Python for AI](../learning-resources/tutorials/TUTORIAL-000-Python-for-AI.md)
├── Part 1: Python Basics (2 hours)
├── Part 2: Data Structures (2 hours)
├── Part 3: OOP Fundamentals (1 hour)
├── Part 4: Practical Skills (1 hour)
└── Part 5: AI-Specific Python (2 hours)
```

**Daily Schedule:**

| Day | Topic | Resources | Exercises |
|-----|-------|-----------|-----------|
| 1-2 | Python Basics | TUTORIAL-000 Part 1 | Calculator exercise |
| 3-4 | Data Structures | TUTORIAL-000 Part 2 | Todo list manager |
| 5-6 | OOP + Practical | TUTORIAL-000 Part 3-4 | JSON config loader |
| 7 | AI-Specific Python | TUTORIAL-000 Part 5 | NumPy practice |

**Deliverable:** Complete all exercises in TUTORIAL-000

**Why Phase 0?**
- **Complete beginners** start here (no experience needed)
- **Bootcamp grads** can skip or review quickly
- **Self-taught devs** can fill knowledge gaps
- **Non-technical users** realize if coding is for them

:information_source: **Already know Python?** You can proceed directly to [TUTORIAL-001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md) or skip to Phase 1 infrastructure topics.

---

## Phase 1: Foundations (Weeks 2-5)

### Week 2: Linux Essentials
**Goal:** Become comfortable with Linux command line

| Day | Topic | Resources | Exercises |
|-----|-------|-----------|-----------|
| 1-2 | File System & Commands | [1101: Fiber GPON](../phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md) | Practice: Navigate `/sys`, `/proc`, `/dev` |
| 3-4 | Permissions & Users | `man chmod`, `man chown` | Exercise: Set up user with sudo access |
| 5-7 | Package Management | `apt`, `dnf`, `pip` | Project: Install Docker from scratch |

**Deliverable:** Set up a basic Linux VM and install Docker

### Week 2: Docker Fundamentals
**Goal:** Containerize your first application

| Day | Topic | Resources | Exercises |
|-----|-------|-----------|-----------|
| 1-2 | Docker Images & Containers | Run `nginx`, `redis` containers | Exercise: Build custom image |
| 3-4 | Docker Compose | Multi-container setup | Project: Compose a web stack |
| 5-7 | Volumes & Networks | Data persistence | Project: Persistent database |

**Deliverable:** Deploy a 3-tier app with Docker Compose

### Week 3: Networking Basics
**Goal:** Understand TCP/IP and routing

| Day | Topic | Resources | Exercises |
|-----|-------|-----------|-----------|
| 1-2 | OSI Model & Protocols | [1102: Star Topology](../phases/phase1-infra/1100-network/1102-Star-Topology-Core.md) | Exercise: Packet capture with Wireshark |
| 3-4 | IP Addressing & Subnets | CIDR notation | Project: Design a home network |
| 5-7 | Jumbo Frames & MTU | [1103: Jumbo Frames](../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md) | Lab: Configure MTU 9000 |

**Deliverable:** Configure 2.5Gbps network with jumbo frames

### Week 4: Hardware Architecture
**Goal:** Understand PCIE, TB3, and GPU passthrough

| Day | Topic | Resources | Exercises |
|-----|-------|-----------|-----------|
| 1-2 | PCIE Lanes & Bandwidth | [1202: TB3 Passthrough](../phases/phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md) | Research: Calculate TB3 bandwidth |
| 3-4 | GPU Architecture | CUDA cores, VRAM | Exercise: GPU benchmarking |
| 5-7 | Thunderbolt 3 | TB3 protocol specs | Project: Verify TB3 connection |

**Deliverable:** Document your hardware topology

---

## Phase 2: Infrastructure (Weeks 5-12)

### Week 5-6: Proxmox Virtualization
**Goal:** Master hypervisor basics

```
Learning Path:
├── [1201: Proxmox Hypervisor SOP](../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)
├── VM Creation & Management
├── ZFS Storage Configuration
└── Core Pinning for Performance
```

**Projects:**
1. Create a Proxmox cluster with 2 nodes
2. Configure ZFS with compression
3. Pin CPU cores for GPU passthrough VM

**Deliverable:** Running Proxmox cluster with GPU VM

### Week 7-8: Kubernetes (K3s)
**Goal:** Deploy containerized apps at scale

```
Learning Path:
├── [1301: K3s Architecture](../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md)
├── [1302: GPU Scheduler](../phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)
├── Pod, Service, Ingress concepts
└── Helm Charts
```

**Projects:**
1. Deploy K3s cluster
2. Create a simple deployment
3. Expose service with Ingress

**Deliverable:** K3s cluster running a web application

### Week 9-10: GPU Passthrough Deep Dive
**Goal:** Pass RTX 2080 Ti to VM

```
Learning Path:
├── [1202: TB3 Passthrough](../phases/phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md)
├── [1203: Nvidia Kernel Module](../phases/phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md)
├── IOMMU configuration
└── VFIO setup
```

**Projects:**
1. Enable IOMMU in BIOS
2. Configure VFIO in Proxmox
3. Pass GPU to VM

**Deliverable:** GPU VM with nvidia-smi working

### Week 11-12: Network Optimization
**Goal:** Achieve 2.5Gbps throughput

```
Learning Path:
├── MTU 9000 configuration
├── TCP tuning
├── Bridge vs routed networking
└── Performance testing
```

**Projects:**
1. Benchmark network throughput
2. Optimize TCP settings
3. Verify 2.5Gbps speed

**Deliverable:** Network performance report

---

## Phase 3: AI/ML Fundamentals (Weeks 13-20)

### Week 13-14: Neural Network Foundations
**Goal:** Understand how LLMs work internally

```
Learning Path:
├── [2101: Tensor Algebra](../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)
├── [2102: Backpropagation](../phases/phase2-foundations/2100-calculus/2102-Backpropagation-and-Derivatives.md)
├── [2201: PyTorch Graphs](../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)
└── EXP_2201_PYTORCH_GRAPH.md
```

**Projects:**
1. Implement a simple neural network from scratch
2. Visualize backpropagation
3. Train on MNIST dataset

**Deliverable:** Working neural network with gradient descent

### Week 15-16: Transformer Architecture
**Goal:** Master attention mechanisms

```
Learning Path:
├── [3101: Self-Attention](../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)
├── [3102: Flash Attention](../phases/phase3-transformers/3100-attention/3102-Flash-Attention.md)
├── EXP_3101_SELF_ATTENTION.md
└── EXP_3102_FLASH_ATTENTION.md
```

**Projects:**
1. Implement self-attention from scratch
2. Compare Flash Attention vs standard
3. Profile attention computation

**Deliverable:** Custom attention implementation

### Week 17-18: Embeddings & Tokenization
**Goal:** Understand how text becomes numbers

```
Learning Path:
├── [3201: RoPE](../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)
├── [3202: Tokenizer Sciences](../phases/phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md)
├── EXP_3201_ROPE.md
└── EXP_3202_TOKENIZER.md
```

**Projects:**
1. Train a BPE tokenizer
2. Implement RoPE embeddings
3. Compare embedding methods

**Deliverable:** Custom tokenizer with embeddings

### Week 19-20: Model Architectures
**Goal:** Understand encoder-decoder vs decoder-only

```
Learning Path:
├── [3401: Encoder-Decoder](../phases/phase3-transformers/3400-architectures/3401-Encoder-Decoder-Architectures.md)
├── [3402: Decoder-Only Models](../phases/phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md)
├── [3403: Model Architecture Comparison](../phases/phase3-transformers/3400-architectures/guides/3403-Model-Architecture-Comparison.md)
└── EXP_3401_ENCODER_DECODER.md
```

**Projects:**
1. Implement GPT-style decoder
2. Implement T5-style encoder-decoder
3. Compare performance

**Deliverable:** Working model implementations

---

## Phase 4: LLMOps (Weeks 21-28)

### Week 21-22: Model Serving
**Goal:** Deploy LLMs with vLLM

```
Learning Path:
├── [1402: vLLM and TGI](../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
├── [1404: vLLM Production Deployment](../phases/phase1-infra/1400-llmops/guides/1404-vLLM-Production-Deployment.md)
├── [1405: TGI Deployment Guide](../phases/phase1-infra/1400-llmops/guides/1405-TGI-Deployment-Guide.md)
└── [1401: Ollama Enterprise](../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)
```

**Projects:**
1. Deploy Mistral 7B with vLLM
2. Configure AWQ quantization
3. Benchmark throughput

**Deliverable:** Production model serving endpoint

### Week 23-24: Prompt Engineering
**Goal:** Master effective prompting

```
Topics:
├── System prompts
├── Few-shot learning
├── Chain-of-thought prompting
└── Prompt templates
```

**Projects:**
1. Create a prompt library
2. Implement CoT prompts
3. Build a prompt evaluation system

**Deliverable:** Prompt engineering framework

### Week 25-26: Fine-Tuning
**Goal:** Adapt models to your domain

```
Learning Path:
├── [5101: LoRA Logic](../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
├── [5102: QLoRA Pipelines](../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)
├── [5104: LoRA Implementation Guide](../phases/phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md)
└── EXP_5101_LORA.md
```

**Projects:**
1. Implement LoRA from scratch
2. Fine-tune Mistral with QLoRA
3. Evaluate model performance

**Deliverable:** Custom fine-tuned model

### Week 27-28: Alignment
**Goal:** Align models with human preferences

```
Learning Path:
├── [5201: DPO Theory](../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)
├── [5202: Alignment Orchestration](../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md)
└── EXP_5201_DPO.md
```

**Projects:**
1. Implement DPO from scratch
2. Create preference dataset
3. Align a model

**Deliverable:** DPO-aligned model

---

## Phase 5: RAG & Knowledge (Weeks 29-36)

### Week 29-30: Vector Databases
**Goal:** Master semantic search

```
Learning Path:
├── [6101: HNSW Indexing](../phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md)
├── [6102: Semantic Similarity](../phases/phase6-rag/6100-vector/6102-Semantic-Similarity.md)
├── [6103: HNSW Tuning Guide](../phases/phase6-rag/6100-vector/guides/6103-HNSW-Tuning-Guide.md)
├── [6401: Qdrant Setup](../phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md)
├── [6403: Qdrant Synology Deployment](../phases/phase6-rag/6400-vector-databases/guides/6403-Qdrant-Synology-Deployment.md)
└── EXP_6101_HNSW.md
```

**Projects:**
1. Deploy Qdrant on Synology
2. Index 10K documents
3. Implement semantic search

**Deliverable:** Production vector database

### Week 31-32: Knowledge Graphs
**Goal:** Build Neo4j knowledge graphs

```
Learning Path:
├── [6301: Neo4j and Knowledge Graphs](../phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md)
├── [6303: Neo4j Deployment Guide](../phases/phase6-rag/6300-context/guides/6303-Neo4j-Deployment-Guide.md)
├── [6304: GraphRAG Implementation](../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md)
└── EXP_6303_NEO4J.md
```

**Projects:**
1. Deploy Neo4j on Synology
2. Build knowledge graph from documents
3. Implement graph queries

**Deliverable:** Production knowledge graph

### Week 33-34: Hybrid Search
**Goal:** Combine keyword and semantic search

```
Learning Path:
├── [6201: Hybrid Search](../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)
├── [6202: Re-ranking](../phases/phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md)
└── EXP_6201_HYBRID_SEARCH.md
```

**Projects:**
1. Implement BM25 search
2. Combine with vector search
3. Add re-ranking

**Deliverable:** Hybrid search system

### Week 35-36: GraphRAG
**Goal:** Combine graphs and vectors

```
Learning Path:
├── [6302: CAG Long Context](../phases/phase6-rag/6300-context/6302-CAG-Long-Context-Architectures.md)
├── [6304: GraphRAG Implementation](../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md)
└── Multi-hop reasoning
```

**Projects:**
1. Build GraphRAG pipeline
2. Implement multi-hop reasoning
3. Evaluate RAG quality

**Deliverable:** Production GraphRAG system

---

## Phase 6: Agentic AI (Weeks 37-44)

### Week 37-38: ReAct Agents
**Goal:** Build reasoning agents

```
Learning Path:
├── [7101: ReAct Loop System](../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
├── [7102: Planning Decomposition](../phases/phase7-agentic/7100-architecture/7102-Planning-Decomposition.md)
├── [7103: ReAct Implementation Guide](../phases/phase7-agentic/7100-architecture/guides/7103-ReAct-Implementation-Guide.md)
└── EXP_7101_REACT.md
```

**Projects:**
1. Implement ReAct loop
2. Add tool calling
3. Build query agent

**Deliverable:** Working ReAct agent

### Week 39-40: Multi-Agent Systems
**Goal:** Coordinate multiple agents

```
Learning Path:
├── [7201: Tool Calling](../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md)
├── [7202: Code Interpreter](../phases/phase7-agentic/7200-tools/guides/7202-Code-Interpreter.md)
└── Agent communication patterns
```

**Projects:**
1. Build 3-agent system
2. Implement agent communication
3. Create collaborative workflow

**Deliverable:** Multi-agent system

### Week 41-42: Tool Calling
**Goal:** Give agents real-world capabilities

```
Learning Path:
├── [7301: Orchestration](../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md)
└── Tool validation
```

**Projects:**
1. Implement safe code execution
2. Add file operations
3. Create API tools

**Deliverable:** Tool-enabled agent

### Week 43-44: Agent Memory
**Goal:** Give agents long-term memory

```
Learning Path:
├── [7401: Long-term Memory](../phases/phase7-agentic/7400-memory/7401-Long-term-Memory.md)
├── [7402: Agent Memory Implementation](../phases/phase7-agentic/7400-memory/guides/7402-Agent-Memory-Implementation.md)
├── [4203: Context Window Optimization](../phases/phase4-quantization/4200-kv-cache/guides/4203-Context-Window-Optimization.md)
└── EXP_7401_AGENT_MEMORY.md
```

**Projects:**
1. Implement VectorStore memory
2. Add episodic memory
3. Create Memoria system

**Deliverable:** Agent with persistent memory

---

## Phase 7: Production (Weeks 45-52)

### Week 45-46: Monitoring & Observability
**Goal:** See everything in your system

```
Learning Path:
├── [1501: Monitoring and Observability](../phases/phase1-infra/1500-Monitoring/1501-Monitoring-and-Observability.md)
├── Prometheus metrics
├── Grafana dashboards
├── Loki logs
└── Tempo traces
```

**Projects:**
1. Deploy full monitoring stack
2. Create custom dashboards
3. Set up alerting

**Deliverable:** Production monitoring system

### Week 47-48: CI/CD Pipelines
**Goal:** Automate everything

```
Learning Path:
├── GitHub Actions workflows
├── Docker image building
├── Automated testing
└── Deployment automation
```

**Projects:**
1. Create CI/CD pipeline
2. Add automated tests
3. Implement auto-deployment

**Deliverable:** Fully automated deployment

### Week 49-50: Security & SSL/TLS
**Goal:** Secure your infrastructure

```
Learning Path:
├── [SSL/TLS Setup Guide](../../configs/docs/ssl-tls-setup.md)
├── Certificate management
├── mTLS with Istio
└── Security policies
```

**Projects:**
1. Set up Let's Encrypt
2. Configure mTLS
3. Implement security policies

**Deliverable:** Secured infrastructure

### Week 51-52: Performance Optimization
**Goal:** Make it fast

```
Learning Path:
├── [Performance Testing](../../configs/performance-testing/k6/load-test.js)
├── GPU optimization
├── Network tuning
└── Caching strategies
```

**Projects:**
1. Run load tests
2. Optimize bottlenecks
3. Implement caching

**Deliverable:** Optimized system

---

## 🎯 Capstone Project

### Weeks 52+: Build Your Own AI Application

**Choose One:**

1. **AI Research Assistant**
   - Vector search over papers
   - Graph-based citation network
   - Multi-agent query processing

2. **Code Generation System**
   - RAG over codebase
   - Tool calling for execution
   - Memory for context

3. **Knowledge Management System**
   - Document ingestion
   - GraphRAG for retrieval
   - Agent for queries

---

## 📖 Recommended Reading Order (Book Style)

### Volume 1: Infrastructure Foundations
1. README.md - Start here
2. **SITEMAP.md** - Complete table of contents
3. [0000-LEARNING-PATH.md](0000-LEARNING-PATH.md) ← **You are here**
4. [1101-1103: Network Topology](../phases/phase1-infra/1100-network/)
5. [1201-1203: Virtualization](../phases/phase1-infra/1200-virtualization/)
6. [1301-1303: Kubernetes](../phases/phase1-infra/1300-kubernetes/)

### Volume 2: AI Fundamentals
7. [2101-2102: Calculus of AI](../phases/phase2-foundations/2100-calculus/)
8. [3101-3102: Attention](../phases/phase3-transformers/3100-attention/)
9. [3201-3202: Embeddings](../phases/phase3-transformers/3200-embeddings/)
10. [3401-3402: Model Architectures](../phases/phase3-transformers/3400-architectures/)

### Volume 3: Quantization & Optimization
11. [4101-4103: Low-Bit Quantization](../phases/phase4-quantization/4100-low-bit/)
12. [4201-4203: KV-Cache Engineering](../phases/phase4-quantization/4200-kv-cache/)
13. [3303: Activation Function Comparison](../phases/phase3-transformers/3300-decoding/guides/3303-Activation-Function-Comparison.md)

### Volume 4: Fine-Tuning & Alignment
14. [5101-5102: PEFT](../phases/phase5-finetuning/5100-peft/)
15. [5104: LoRA Implementation](../phases/phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md)
16. [5201-5202: SFT & Preference](../phases/phase5-finetuning/5200-alignment/)

### Volume 5: Data Nexus
17. [6101-6102: Vector Architectures](../phases/phase6-rag/6100-vector/)
18. [6201-6202: RAG 2.0](../phases/phase6-rag/6200-retrieval/)
19. [6301-6304: GraphRAG](../phases/phase6-rag/6300-context/)

### Volume 6: Agentic AI
20. [7101-7103: ReAct](../phases/phase7-agentic/7100-architecture/)
21. [7201-7203: Multi-Agent](../phases/phase7-agentic/7200-tools/)
22. [7301-7302: Tool-Calling](../phases/phase7-agentic/7300-orchestration/)
23. [7401-7402: Agent Memory](../phases/phase7-agentic/7400-memory/)

### Volume 7: Production
24. [1501: Monitoring](../phases/phase1-infra/1500-Monitoring/)
25. [1404-1405: LLMOps](../phases/phase1-infra/1400-llmops/guides/)

---

## 🧪 Experiments (Hands-on Labs)

Each experiment corresponds to a documentation topic:

| Phase | Experiment | Focus |
|-------|-----------|-------|
| Infrastructure | [EXP_1101_GPON.md](../../experiments/EXP_1101_GPON.md) | Network setup |
| Attention | [EXP_3101_SELF_ATTENTION.md](../../experiments/EXP_3101_SELF_ATTENTION.md) | Self-attention |
| Quantization | [EXP_4101_GGUF.md](../../experiments/EXP_4101_GGUF.md) | GGUF format |
| Fine-tuning | [EXP_5101_LORA.md](../../experiments/EXP_5101_LORA.md) | LoRA training |
| RAG | [EXP_6201_HYBRID_SEARCH.md](../../experiments/EXP_6201_HYBRID_SEARCH.md) | Hybrid search |
| Agents | [EXP_7101_REACT.md](../../experiments/EXP_7101_REACT.md) | ReAct loop |

---

## 📊 Progress Tracker

Track your learning journey:

```
[ ] Phase 1: Foundations (Weeks 1-4)
    [ ] Week 1: Linux Essentials
    [ ] Week 2: Docker Fundamentals
    [ ] Week 3: Networking Basics
    [ ] Week 4: Hardware Architecture

[ ] Phase 2: Infrastructure (Weeks 5-12)
    [ ] Week 5-6: Proxmox Virtualization
    [ ] Week 7-8: Kubernetes (K3s)
    [ ] Week 9-10: GPU Passthrough
    [ ] Week 11-12: Network Optimization

[ ] Phase 3: AI/ML Fundamentals (Weeks 13-20)
    [ ] Week 13-14: Neural Network Foundations
    [ ] Week 15-16: Transformer Architecture
    [ ] Week 17-18: Embeddings & Tokenization
    [ ] Week 19-20: Model Architectures

[ ] Phase 4: LLMOps (Weeks 21-28)
    [ ] Week 21-22: Model Serving
    [ ] Week 23-24: Prompt Engineering
    [ ] Week 25-26: Fine-Tuning
    [ ] Week 27-28: Alignment

[ ] Phase 5: RAG & Knowledge (Weeks 29-36)
    [ ] Week 29-30: Vector Databases
    [ ] Week 31-32: Knowledge Graphs
    [ ] Week 33-34: Hybrid Search
    [ ] Week 35-36: GraphRAG

[ ] Phase 6: Agentic AI (Weeks 37-44)
    [ ] Week 37-38: ReAct Agents
    [ ] Week 39-40: Multi-Agent Systems
    [ ] Week 41-42: Tool Calling
    [ ] Week 43-44: Agent Memory

[ ] Phase 7: Production (Weeks 45-52)
    [ ] Week 45-46: Monitoring & Observability
    [ ] Week 47-48: CI/CD Pipelines
    [ ] Week 49-50: Security & SSL/TLS
    [ ] Week 51-52: Performance Optimization

[ ] Capstone Project (Weeks 52+)
```

---

## 🎓 Certification Path

Complete all phases to earn:

- **Level 1: Infrastructure Architect** (Phases 1-2)
- **Level 2: ML Engineer** (Phases 3-4)
- **Level 3: RAG Specialist** (Phase 5)
- **Level 4: Agentic AI Engineer** (Phase 6)
- **Level 5: LLMOps Professional** (Phase 7)
- **Master: PROJECT-OMEGA Architect** (All phases + Capstone)

---

## 📝 Tips for Success

1. **Read Sequentially**: Follow the numbered path
2. **Do the Experiments**: Hands-on practice is essential
3. **Build Projects**: Apply what you learn immediately
4. **Join Community**: Share progress and get feedback
5. **Teach Others: Explain concepts to solidify learning**

---

**Next Steps:**
1. Start with [Phase 1: Foundations](#phase-1-foundations-weeks-1-4)
2. Set up your learning environment
3. Join the community discussions
4. Track your progress in the checklist above

**Remember:** This is a marathon, not a sprint. Take your time with each concept and build a strong foundation before moving forward.

Good luck on your PROJECT-OMEGA journey! 🚀
