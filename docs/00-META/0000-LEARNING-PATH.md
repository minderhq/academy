---
Document ID: 0000
Title: "Minder Academy Learning Path"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Beginner
Tags: ['roadmap', 'guide', 'llm']
---

# Minder Academy Learning Path

## Table of Contents

- [Complete AI/LLM Infrastructure Curriculum - From Zero to Hero](#complete-aillm-infrastructure-curriculum---from-zero-to-hero)
- [Curriculum Overview](#curriculum-overview)
- [Phase 0: Python Fundamentals (Week 1)](#phase-0-python-fundamentals-week-1)
- [Phase 1: Infrastructure Fabric (Weeks 2-17)](#phase-1-infrastructure-fabric-weeks-2-17)
- [Phase 2: Cognitive Science & Frameworks (Weeks 18-21)](#phase-2-cognitive-science--frameworks-weeks-18-21)
- [Phase 3: Transformer Physics (Weeks 22-27)](#phase-3-transformer-physics-weeks-22-27)
- [Phase 4: Quantization & Compression (Weeks 28-31)](#phase-4-quantization--compression-weeks-28-31)
- [Phase 5: Fine-Tuning & Alignment (Weeks 32-35)](#phase-5-fine-tuning--alignment-weeks-32-35)
- [Phase 6: Data Nexus (Weeks 36-41)](#phase-6-data-nexus-weeks-36-41)
- [Phase 7: Agentic Systems (Weeks 42-48)](#phase-7-agentic-systems-weeks-42-48)
- [Capstone Project](#capstone-project)
- [Recommended Reading Order (Book Style)](#recommended-reading-order-book-style)
- [Experiments (Hands-on Labs)](#experiments-hands-on-labs)
- [Progress Tracker](#progress-tracker)
- [Certification Path](#certification-path)
- [Tips for Success](#tips-for-success)

---

## Complete AI/LLM Infrastructure Curriculum - From Zero to Hero

**Last Updated:** 2026-10-08

**Estimated Time:** 6-12 months (part-time) - 48 study weeks + capstone

**Prerequisites:** None! We start from absolute zero.

---

## Curriculum Overview

The phase numbers, names and module lists below are the corpus's canonical
structure - the same one used by the [README](../../README.md), the
[Master Index](MASTER-INDEX.md) and the
[Volume Guide](VOLUME-GUIDE.md). This document adds what those surfaces do
not carry: a week-by-week study calendar with projects and deliverables.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                       Minder Academy LEARNING PATH                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 0: Python Fundamentals (Week 1) - pre-work                       │
│  ├── Python Basics (variables, functions, loops)                        │
│  ├── Data Structures (lists, dicts, tuples)                             │
│  ├── OOP Fundamentals (classes, methods)                                │
│  └── AI-Specific Python (NumPy, type hints, async)                      │
│                                                                          │
│  Phase 1: Infrastructure Fabric (Weeks 2-17)                             │
│  ├── Linux & Docker Fundamentals                                        │
│  ├── Network Topology                                                   │
│  ├── Virtualization & GPU Passthrough (Proxmox)                         │
│  ├── Kubernetes (K3s)                                                   │
│  ├── LLMOps Serving (Ollama / vLLM)                                     │
│  └── Monitoring & Observability                                         │
│                                                                          │
│  Phase 2: Cognitive Science & Frameworks (Weeks 18-21)                   │
│  ├── Tensor Algebra & Backpropagation                                   │
│  ├── Frameworks (PyTorch, XLA, CUDA)                                    │
│  └── Pre-training Fundamentals                                          │
│                                                                          │
│  Phase 3: Transformer Physics (Weeks 22-27)                              │
│  ├── Attention & Flash Attention                                        │
│  ├── RoPE & Tokenizers                                                  │
│  ├── Decoding & FFN Internals                                           │
│  ├── Model Architectures                                                │
│  └── Multimodal                                                         │
│                                                                          │
│  Phase 4: Quantization & Compression (Weeks 28-31)                       │
│  ├── GGUF & Low-Bit Formats                                             │
│  ├── KV-Cache & Context Windows                                         │
│  ├── Quantization-Aware Training                                        │
│  └── Advanced Formats (GPTQ / AWQ / EXL2)                               │
│                                                                          │
│  Phase 5: Fine-Tuning & Alignment (Weeks 32-35)                          │
│  ├── PEFT (LoRA / QLoRA)                                                │
│  ├── Alignment (DPO / RLHF)                                             │
│  └── Synthetic Data & Distributed Training                              │
│                                                                          │
│  Phase 6: Data Nexus (Weeks 36-41)                                       │
│  ├── Vector Architectures (HNSW)                                        │
│  ├── Hybrid Search & Re-ranking                                         │
│  ├── Knowledge Graphs & GraphRAG                                        │
│  └── MLOps Pipelines (CI/CD for ML)                                     │
│                                                                          │
│  Phase 7: Agentic Systems (Weeks 42-48)                                  │
│  ├── ReAct Agents & Planning                                            │
│  ├── Tool Calling                                                       │
│  ├── Multi-Agent Orchestration                                          │
│  ├── Agent Memory                                                       │
│  └── Agent Security                                                     │
│                                                                          │
│  Capstone Project (Weeks 49+)                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Python Fundamentals (Week 1)

### For Complete Beginners

**Goal:** Learn Python programming from absolute zero

```text
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
| 3-4 | Data Structures | TUTORIAL-000 Part 2 | To-do list manager |
| 5-6 | OOP + Practical | TUTORIAL-000 Part 3-4 | JSON config loader |
| 7 | AI-Specific Python | TUTORIAL-000 Part 5 | NumPy practice |

**Deliverable:** Complete all exercises in TUTORIAL-000

**Why Phase 0?**

- **Complete beginners** start here (no experience needed)
- **Bootcamp grads** can skip or review quickly
- **Self-taught devs** can fill knowledge gaps
- **Non-technical users** realize if coding is for them

ℹ️ **Already know Python?** You can proceed directly to [TUTORIAL-001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md) or skip to Phase 1 infrastructure topics.

---

## Phase 1: Infrastructure Fabric (Weeks 2-17)

**Turning commodity hardware into a programmable, scalable AI factory.**

### Weeks 2-3: Linux & Docker Fundamentals
**Goal:** Become comfortable with the Linux command line, then containerize your first application

| Day | Topic | Resources | Exercises |
|-----|-------|-----------|-----------|
| 1-3 | File System & Commands | `man chmod`, `man chown`, `man systemctl` | Practice: Navigate `/sys`, `/proc`, `/dev` |
| 4-5 | Permissions & Package Management | `apt`, `dnf`, `pip` | Exercise: Set up a user with sudo access; install Docker from scratch |
| 6-10 | Docker Fundamentals | [TUTORIAL-002: Docker Essentials](../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md) | Project: Build a custom image, then a multi-container stack |

**Deliverable:** Deploy a 3-tier app with Docker Compose on a Linux VM

### Weeks 4-5: Network Topology
**Goal:** Understand TCP/IP, routing and line-rate throughput

| Day | Topic | Resources | Exercises |
|-----|-------|-----------|-----------|
| 1-2 | Internet Uplink & Modem | [1101: Fiber GPON Modem](../phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md) | Exercise: Map your own uplink path |
| 3-4 | OSI Model & Topology Design | [1102: Star Topology Core](../phases/phase1-infra/1100-network/1102-Star-Topology-Core.md) | Exercise: Packet capture with Wireshark |
| 5-7 | IP Addressing & Subnets | CIDR notation | Project: Design a home network |
| 8-10 | Jumbo Frames & MTU | [1103: Jumbo Frames and MTU](../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md) | Lab: Configure MTU 9000 end-to-end |

**Deliverable:** A network performance report with line-rate throughput

### Weeks 6-9: Virtualization & GPU Passthrough
**Goal:** Master the hypervisor and hand a GPU to a VM

```text
Learning Path:
├── [1201: Proxmox Hypervisor SOP](../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)
├── [1202: TB3/UT3G Passthrough (IOMMU/VFIO)](../phases/phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md)
├── [1203: Nvidia Kernel Module](../phases/phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md)
└── [1204: Multi-GPU Setup](../phases/phase1-infra/1200-virtualization/1204-Multi-GPU-Setup.md)
```

**Projects:**

1. Create a Proxmox cluster with 2 nodes
2. Configure ZFS with compression; pin CPU cores for a GPU VM
3. Enable IOMMU in BIOS, configure VFIO, pass the GPU to a VM

**Deliverable:** A GPU VM with `nvidia-smi` working

### Weeks 10-11: Kubernetes (K3s)
**Goal:** Deploy containerized (and GPU-scheduled) workloads at scale

```text
Learning Path:
├── [1301: K3s Master-Worker Architecture](../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md)
├── [1302: GPU Scheduler](../phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)
├── Pod, Service, Ingress concepts
└── Helm Charts
```

**Projects:**

1. Deploy a K3s cluster
2. Create a deployment and expose it with Ingress
3. Schedule a GPU workload with the NVIDIA device plugin

**Deliverable:** A K3s cluster running a GPU-scheduled pod

### Weeks 12-13: LLMOps Serving
**Goal:** Serve LLMs in production

```text
Learning Path:
├── [1401: Ollama Enterprise](../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)
├── [1402: vLLM and TGI](../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
├── [1403: vLLM Production Deployment](../phases/phase1-infra/1400-llmops/guides/1403-vLLM-Production-Deployment.md)
└── [1404: TGI Deployment Guide](../phases/phase1-infra/1400-llmops/guides/1404-TGI-Deployment-Guide.md)
```

**Projects:**

1. Serve a quantized model with Ollama, then with vLLM
2. Benchmark throughput and latency
3. Compare serving stacks on your own hardware

**Deliverable:** A production model-serving endpoint

### Weeks 14-15: Monitoring & Observability
**Goal:** See everything in your system

```text
Learning Path:
├── [1501: Monitoring and Observability](../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
├── [1502: Model Drift Detection](../phases/phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md)
├── [1503: LLM Observability](../phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md)
├── Prometheus metrics
├── Grafana dashboards
└── Loki logs + Tempo traces
```

**Projects:**

1. Deploy the full monitoring stack
2. Create custom dashboards
3. Set up alerting and trace inference calls end-to-end

**Deliverable:** A production monitoring system

### Weeks 16-17: Integration Project
**Goal:** Wire the whole fabric together

**Project:** One documented, single-node AI factory - network uplink to
hypervisor to K3s to a vLLM endpoint under full observability.

**Deliverable:** The end-to-end deployment, documented

---

## Phase 2: Cognitive Science & Frameworks (Weeks 18-21)

**Deep-diving into the "Laws of Physics" of AI and Deep Learning.**

### Weeks 18-19: Tensor Algebra & Backpropagation
**Goal:** Understand how LLMs work internally

```text
Learning Path:
├── [2101: Tensor Algebra](../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)
├── [2102: Backpropagation and Derivatives](../phases/phase2-foundations/2100-calculus/2102-Backpropagation-and-Derivatives.md)
├── [2201: PyTorch Computational Graphs](../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)
└── EXP_2201_PYTORCH_GRAPHS.md
```

**Projects:**

1. Implement a simple neural network from scratch
2. Visualize backpropagation
3. Train on MNIST

**Deliverable:** A working neural network with gradient descent

### Week 20: Frameworks & Framework Engineering
**Goal:** Know your training stack below the API

```text
Learning Path:
├── [2200: Frameworks](../phases/phase2-foundations/2200-frameworks/README.md)
├── [2300: Framework Engineering](../phases/phase2-foundations/2300-framework-engineering/README.md)
├── Compilation paths (XLA, torch.compile)
└── CUDA kernel basics
```

**Projects:**

1. Benchmark eager vs compiled execution
2. Read and modify a framework serving path

**Deliverable:** A short write-up: where your framework spends time

### Week 21: Pre-training Fundamentals
**Goal:** Understand what "pre-trained" actually cost

```text
Learning Path:
├── [2400: Pre-training](../phases/phase2-foundations/2400-pretraining/README.md)
├── [2401: Pre-training Fundamentals](../phases/phase2-foundations/2400-pretraining/2401-Pre-training-Fundamentals.md)
├── Data curation & tokenization
└── Scaling-law arithmetic
```

**Projects:**

1. Estimate the FLOPs/cost of a known training run
2. Train a small BPE tokenizer

**Deliverable:** A cost model for a 7B-class training run

---

## Phase 3: Transformer Physics (Weeks 22-27)

**Dismantling the Generative Pre-trained Transformer architecture.**

### Weeks 22-23: Attention
**Goal:** Master attention mechanisms

```text
Learning Path:
├── [3101: Self-Attention Deep Dive](../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)
├── [3102: Flash Attention](../phases/phase3-transformers/3100-attention/3102-Flash-Attention.md)
├── EXP_3101_SELF_ATTENTION.md
└── EXP_3102_FLASH_ATTENTION.md
```

**Projects:**

1. Implement self-attention from scratch
2. Compare Flash Attention vs standard
3. Profile attention computation

**Deliverable:** A custom attention implementation

### Week 24: RoPE & Tokenization
**Goal:** Understand how text and position become numbers

```text
Learning Path:
├── [3201: Rotary Positional Embeddings](../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)
├── [3202: Tokenizer Sciences](../phases/phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md)
├── EXP_3201_ROPE.md
└── EXP_3202_TOKENIZER.md
```

**Projects:**

1. Implement RoPE embeddings
2. Inspect a real tokenizer's vocabulary behavior

**Deliverable:** RoPE from scratch with a scaling experiment

### Week 25: Decoding & FFN Internals
**Goal:** Know what happens between attention layers

```text
Learning Path:
├── [3300: Decoding](../phases/phase3-transformers/3300-decoding/README.md)
├── Activation functions (GELU, SwiGLU)
└── Normalization (pre-norm vs post-norm)
```

**Projects:**

1. Compare activation functions on a small model
2. Explain the KV-cache role of each block

**Deliverable:** An annotated forward pass

### Week 26: Model Architectures
**Goal:** Understand encoder-decoder vs decoder-only

```text
Learning Path:
├── [3401: Encoder-Decoder Architectures](../phases/phase3-transformers/3400-architectures/3401-Encoder-Decoder-Architectures.md)
├── [3402: Decoder-Only Models](../phases/phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md)
├── [3403: Model Architecture Comparison](../phases/phase3-transformers/3400-architectures/guides/3403-Model-Architecture-Comparison.md)
└── EXP_3401_ENCODER_DECODER.md
```

**Projects:**

1. Implement a GPT-style decoder
2. Implement a T5-style encoder-decoder
3. Compare performance

**Deliverable:** Working model implementations

### Week 27: Multimodal
**Goal:** Extend transformers beyond text

```text
Learning Path:
├── [3500: Multimodal](../phases/phase3-transformers/3500-multimodal/README.md)
├── Vision-language models
└── Audio models
```

**Projects:**

1. Compute a VLM token budget for your VRAM
2. Run a small VLM locally

**Deliverable:** A multimodal inference note

---

## Phase 4: Quantization & Compression (Weeks 28-31)

**Maximizing limited VRAM for 8B-70B model execution.**

### Week 28: GGUF & Low-Bit Formats
**Goal:** Run big models on small cards

```text
Learning Path:
├── [4101: GGUF Physics](../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
├── [4103: Double Quantization](../phases/phase4-quantization/4100-low-bit/4103-Double-Quantization.md)
└── EXP_4101_GGUF.md
```

**Projects:**

1. Quantize a model to Q4_K and verify perplexity drift
2. Map the VRAM ledger block by block

**Deliverable:** A quantized model that fits your card

### Week 29: KV-Cache & Context Windows
**Goal:** Engineer long contexts

```text
Learning Path:
├── [4201: Context Window Physics](../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
├── [4202: Speculative Decoding](../phases/phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md)
└── [4203: Context Window Optimization](../phases/phase4-quantization/4200-kv-cache/guides/4203-Context-Window-Optimization.md)
```

**Projects:**

1. Measure KV-cache growth per token
2. Try context-extension scaling (PI / YaRN)

**Deliverable:** A KV-cache budget table for your hardware

### Week 30: Quantization-Aware Training
**Goal:** Quantize while training, not after

```text
Learning Path:
└── [4300: Quantization-Aware Training](../phases/phase4-quantization/4300-quantization-aware-training/README.md)
```

**Projects:**

1. Run a QAT loop on a small model
2. Compare QAT vs PTQ quality at the same bit width

**Deliverable:** A QAT-vs-PTQ comparison note

### Week 31: Advanced Formats
**Goal:** Pick the right format per runtime

```text
Learning Path:
└── [4400: Advanced Quantization Techniques](../phases/phase4-quantization/4400-advanced-techniques/README.md)
```

**Projects:**

1. Produce GPTQ/AWQ/EXL2 variants of the same model
2. Benchmark them under one serving stack

**Deliverable:** A format decision matrix for your runtime

---

## Phase 5: Fine-Tuning & Alignment (Weeks 32-35)

**Evolving pre-trained weights for specialized domains.**

### Weeks 32-33: PEFT
**Goal:** Adapt models to your domain on one GPU

```text
Learning Path:
├── [5101: LoRA Logic](../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
├── [5102: QLoRA Pipelines](../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)
├── [5104: LoRA Implementation Guide](../phases/phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md)
└── EXP_5101_LORA.md
```

**Projects:**

1. Implement LoRA from scratch
2. Fine-tune a 7B-class model with QLoRA
3. Evaluate against the base model

**Deliverable:** A custom fine-tuned model

### Week 34: Alignment
**Goal:** Align models with human preferences

```text
Learning Path:
├── [5201: DPO Theory](../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)
├── [5202: Alignment Orchestration](../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md)
├── [5203: RLHF](../phases/phase5-finetuning/5200-alignment/5203-RLHF.md)
└── EXP_5201_DPO.md
```

**Projects:**

1. Implement DPO from scratch
2. Create a preference dataset
3. Align your fine-tuned model

**Deliverable:** A DPO-aligned model

### Week 35: Synthetic Data & Distributed Training
**Goal:** Scale beyond one GPU and one dataset

```text
Learning Path:
├── [5300: Synthetic Data](../phases/phase5-finetuning/5300-synthetic/README.md)
└── [5400: Distributed Training](../phases/phase5-finetuning/5400-distributed-training/README.md)
```

**Projects:**

1. Generate and filter a synthetic instruction set
2. Read the ZeRO ladder; plan a multi-GPU run

**Deliverable:** A synthetic-data pipeline plan

---

## Phase 6: Data Nexus (Weeks 36-41)

**Integrating your data into the LLM logic flow.**

### Weeks 36-37: Vector Architectures
**Goal:** Master semantic search

```text
Learning Path:
├── [6101: HNSW Indexing](../phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md)
├── [6102: Semantic Similarity](../phases/phase6-rag/6100-vector/6102-Semantic-Similarity.md)
├── [6103: HNSW Tuning Guide](../phases/phase6-rag/6100-vector/guides/6103-HNSW-Tuning-Guide.md)
└── EXP_6101_HNSW.md
```

**Projects:**

1. Deploy Qdrant on a Linux host (Docker)
2. Index 10K documents
3. Implement semantic search

**Deliverable:** A production vector database

### Week 38: Retrieval & Re-ranking
**Goal:** Combine keyword and semantic search

```text
Learning Path:
├── [6201: Hybrid Search](../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)
├── [6202: Re-ranking and Retrieval Logistics](../phases/phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md)
├── [6203: Advanced Retrieval](../phases/phase6-rag/6200-retrieval/6203-Advanced-Retrieval.md)
└── EXP_6201_HYBRID_SEARCH.md
```

**Projects:**

1. Implement BM25 + vector hybrid with RRF
2. Add re-ranking
3. Build a golden-set evaluation

**Deliverable:** A hybrid search system with metrics

### Weeks 39-40: Knowledge Graphs & GraphRAG
**Goal:** Combine graphs and vectors

```text
Learning Path:
├── [6301: Neo4j and Knowledge Graphs](../phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md)
├── [6302: CAG Long-Context Architectures](../phases/phase6-rag/6300-context/6302-CAG-Long-Context-Architectures.md)
├── [6303: Neo4j Deployment Guide](../phases/phase6-rag/6300-context/guides/6303-Neo4j-Deployment-Guide.md)
├── [6304: GraphRAG Implementation](../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md)
└── EXP_6303_NEO4J.md
```

**Projects:**

1. Deploy Neo4j on a Linux host (Docker)
2. Build a knowledge graph from documents
3. Build a GraphRAG pipeline with multi-hop reasoning

**Deliverable:** A production GraphRAG system

### Week 41: Vector Databases & MLOps Pipelines
**Goal:** Productionize retrieval and its lifecycle

```text
Learning Path:
├── [6401: Qdrant Setup](../phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md)
├── [6403: Qdrant Production Deployment](../phases/phase6-rag/6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md)
├── [6500: MLOps Pipelines](../phases/phase6-rag/6500-mlops-pipelines/README.md)
└── Load testing: [k6 load-test.js](../../configs/performance-testing/k6/load-test.js)
```

**Projects:**

1. Harden your vector DB deployment
2. Build a CI/CD pipeline for the RAG stack
3. Load-test the endpoint

**Deliverable:** A versioned, tested, monitored retrieval service

---

## Phase 7: Agentic Systems (Weeks 42-48)

**Creating a team of agents that can manage infrastructure and code.**

### Weeks 42-43: ReAct Agents
**Goal:** Build reasoning agents

```text
Learning Path:
├── [7101: ReAct Loop System](../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
├── [7102: Planning Decomposition](../phases/phase7-agentic/7100-architecture/7102-Planning-Decomposition.md)
├── [7103: ReAct Implementation Guide](../phases/phase7-agentic/7100-architecture/guides/7103-ReAct-Implementation-Guide.md)
└── EXP_7101_REACT.md
```

**Projects:**

1. Implement the ReAct loop
2. Add planning decomposition
3. Build a query agent

**Deliverable:** A working ReAct agent

### Week 44: Tool Use
**Goal:** Give agents real-world capabilities

```text
Learning Path:
├── [7201: Tool Calling](../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md)
└── [7202: Code Interpreter](../phases/phase7-agentic/7200-tools/guides/7202-Code-Interpreter.md)
```

**Projects:**

1. Implement safe code execution
2. Add file operations and API tools

**Deliverable:** A tool-enabled agent

### Week 45: Orchestration
**Goal:** Coordinate multiple agents

```text
Learning Path:
└── [7300: Orchestration](../phases/phase7-agentic/7300-orchestration/README.md)
```

**Projects:**

1. Build a 3-agent system
2. Implement agent communication patterns

**Deliverable:** A multi-agent system

### Week 46: Agent Memory
**Goal:** Give agents long-term memory

```text
Learning Path:
├── [7401: Long-term Memory](../phases/phase7-agentic/7400-memory/7401-Long-term-Memory.md)
├── [7402: Agent Memory Implementation](../phases/phase7-agentic/7400-memory/guides/7402-Agent-Memory-Implementation.md)
└── EXP_7401_AGENT_MEMORY.md
```

**Projects:**

1. Implement vector-store memory
2. Add episodic memory

**Deliverable:** An agent with persistent memory

### Weeks 47-48: Agent Security
**Goal:** Defend the agent surface

```text
Learning Path:
└── [7500: Security](../phases/phase7-agentic/7500-security/README.md)
```

**Projects:**

1. Red-team your own agent with prompt injection
2. Add input validation and tool-call sandboxing

**Deliverable:** A hardened agent with an attack/defense log

---

## Capstone Project

### Weeks 49+: Build Your Own AI Application

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

## Recommended Reading Order (Book Style)

The corpus ships as a seven-volume book. Each volume has a guided route
under `docs/volumes/` - start there, then dive into the module docs.

### Volume 1: Infrastructure Fundamentals
1. [VOLUME-1: Infrastructure](../volumes/VOLUME-1-Infrastructure.md) - the guided route
2. [1100: Network Topology](../phases/phase1-infra/1100-network/)
3. [1200: Virtualization](../phases/phase1-infra/1200-virtualization/)
4. [1300: Kubernetes](../phases/phase1-infra/1300-kubernetes/)
5. [1400: LLMOps](../phases/phase1-infra/1400-llmops/)
6. [1500: Monitoring](../phases/phase1-infra/1500-monitoring/)

### Volume 2: AI/ML Foundations
7. [VOLUME-2: AI Foundations](../volumes/VOLUME-2-AI-Foundations.md) - the guided route
8. [2100: Calculus of AI](../phases/phase2-foundations/2100-calculus/)
9. [2000: Frameworks & Engineering](../phases/phase2-foundations/)
10. [2400: Pre-training](../phases/phase2-foundations/2400-pretraining/)

### Volume 3: LLM Internals & Architecture
11. [VOLUME-3: LLM Internals](../volumes/VOLUME-3-LLM-Internals.md) - the guided route
12. [3100: Attention](../phases/phase3-transformers/3100-attention/)
13. [3200: Embeddings](../phases/phase3-transformers/3200-embeddings/)
14. [3400: Model Architectures](../phases/phase3-transformers/3400-architectures/)

### Volume 4: Quantization & Optimization
15. [VOLUME-4: Quantization](../volumes/VOLUME-4-Quantization.md) - the guided route
16. [4100: Low-Bit Quantization](../phases/phase4-quantization/4100-low-bit/)
17. [4200: KV-Cache Engineering](../phases/phase4-quantization/4200-kv-cache/)

### Volume 5: Model Adaptation
18. [VOLUME-5: Model Adaptation](../volumes/VOLUME-5-Model-Adaptation.md) - the guided route
19. [5100: PEFT](../phases/phase5-finetuning/5100-peft/)
20. [5200: Alignment](../phases/phase5-finetuning/5200-alignment/)

### Volume 6: Data Nexus: RAG & Memory
21. [VOLUME-6: Data Nexus](../volumes/VOLUME-6-Data-Nexus.md) - the guided route
22. [6100: Vector Architectures](../phases/phase6-rag/6100-vector/)
23. [6200: Retrieval](../phases/phase6-rag/6200-retrieval/)
24. [6300: GraphRAG](../phases/phase6-rag/6300-context/)

### Volume 7: Production Mastery
25. [VOLUME-7: Production Mastery](../volumes/VOLUME-7-Production-Mastery.md) - the guided route
26. [7100: Agentic Architecture](../phases/phase7-agentic/7100-architecture/)
27. [7500: Agent Security](../phases/phase7-agentic/7500-security/)

---

## Experiments (Hands-on Labs)

Each experiment corresponds to a documentation topic:

| Phase | Experiment | Focus |
|-------|-----------|-------|
| Infrastructure | [EXP_1101_GPON.md](../../experiments/EXP_1101_GPON.md) | Network setup (case study) |
| Attention | [EXP_3101_SELF_ATTENTION.md](../../experiments/EXP_3101_SELF_ATTENTION.md) | Self-attention |
| Quantization | [EXP_4101_GGUF.md](../../experiments/EXP_4101_GGUF.md) | GGUF format |
| Fine-tuning | [EXP_5101_LORA.md](../../experiments/EXP_5101_LORA.md) | LoRA training |
| RAG | [EXP_6201_HYBRID_SEARCH.md](../../experiments/EXP_6201_HYBRID_SEARCH.md) | Hybrid search |
| Agents | [EXP_7101_REACT.md](../../experiments/EXP_7101_REACT.md) | ReAct loop |

The full inventory lives in the [SITEMAP Experiments section](SITEMAP.md#experiments-48-files-47-experiments--1-template).

---

## Progress Tracker

Track your learning journey:

```text
[ ] Phase 0: Python Fundamentals (Week 1)
    [ ] TUTORIAL-000 complete

[ ] Phase 1: Infrastructure Fabric (Weeks 2-17)
    [ ] Weeks 2-3: Linux & Docker Fundamentals
    [ ] Weeks 4-5: Network Topology
    [ ] Weeks 6-9: Virtualization & GPU Passthrough
    [ ] Weeks 10-11: Kubernetes (K3s)
    [ ] Weeks 12-13: LLMOps Serving
    [ ] Weeks 14-15: Monitoring & Observability
    [ ] Weeks 16-17: Integration Project

[ ] Phase 2: Cognitive Science & Frameworks (Weeks 18-21)
    [ ] Weeks 18-19: Tensor Algebra & Backpropagation
    [ ] Week 20: Frameworks & Framework Engineering
    [ ] Week 21: Pre-training Fundamentals

[ ] Phase 3: Transformer Physics (Weeks 22-27)
    [ ] Weeks 22-23: Attention
    [ ] Week 24: RoPE & Tokenization
    [ ] Week 25: Decoding & FFN Internals
    [ ] Week 26: Model Architectures
    [ ] Week 27: Multimodal

[ ] Phase 4: Quantization & Compression (Weeks 28-31)
    [ ] Week 28: GGUF & Low-Bit Formats
    [ ] Week 29: KV-Cache & Context Windows
    [ ] Week 30: Quantization-Aware Training
    [ ] Week 31: Advanced Formats

[ ] Phase 5: Fine-Tuning & Alignment (Weeks 32-35)
    [ ] Weeks 32-33: PEFT
    [ ] Week 34: Alignment
    [ ] Week 35: Synthetic Data & Distributed Training

[ ] Phase 6: Data Nexus (Weeks 36-41)
    [ ] Weeks 36-37: Vector Architectures
    [ ] Week 38: Retrieval & Re-ranking
    [ ] Weeks 39-40: Knowledge Graphs & GraphRAG
    [ ] Week 41: Vector Databases & MLOps Pipelines

[ ] Phase 7: Agentic Systems (Weeks 42-48)
    [ ] Weeks 42-43: ReAct Agents
    [ ] Week 44: Tool Use
    [ ] Week 45: Orchestration
    [ ] Week 46: Agent Memory
    [ ] Weeks 47-48: Agent Security

[ ] Capstone Project (Weeks 49+)
```

---

## Certification Path

Complete each phase to earn its level:

- **Level 1: Infrastructure Fabric** (Phase 1)
- **Level 2: Cognitive Science & Frameworks** (Phase 2)
- **Level 3: Transformer Physics** (Phase 3)
- **Level 4: Quantization & Compression** (Phase 4)
- **Level 5: Fine-Tuning & Alignment** (Phase 5)
- **Level 6: Data Nexus** (Phase 6)
- **Level 7: Agentic Systems** (Phase 7)
- **Master: Minder Academy Architect** (All phases + Capstone)

---

## Tips for Success

1. **Read Sequentially**: Follow the numbered path
2. **Do the Experiments**: Hands-on practice is essential
3. **Build Projects**: Apply what you learn immediately
4. **Teach Others**: Explain concepts to solidify learning

---

**Next Steps:**

1. Start with [Phase 1: Infrastructure Fabric](#phase-1-infrastructure-fabric-weeks-2-17)
2. Set up your learning environment with the [Environment Setup guide](ENVIRONMENT-SETUP.md)
3. Track your progress in the checklist above

**Remember:** This is a marathon, not a sprint. Take your time with each concept and build a strong foundation before moving forward.

Good luck on your Minder Academy journey! 🚀
