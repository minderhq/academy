# PROJECT-OMEGA - Complete Sitemap

## 📚 Book Structure - Volume Guides (NEW)

**Start your journey with the volume guides:**

- ✅ **[VOLUME-GUIDE.md](VOLUME-GUIDE.md)** - Complete volume overview and recommended paths (NEW)
- ✅ **[VOLUME-1-Infrastructure.md](../volumes/VOLUME-1-Infrastructure.md)** - Docker, networks, local LLMs (NEW)
- ✅ **[VOLUME-2-AI-Foundations.md](../volumes/VOLUME-2-AI-Foundations.md)** - Math, frameworks, CUDA (NEW)
- ✅ **[VOLUME-3-LLM-Internals.md](../volumes/VOLUME-3-LLM-Internals.md)** - Transformers, attention, embeddings (NEW)
- ✅ **[VOLUME-4-Quantization.md](../volumes/VOLUME-4-Quantization.md)** - GGUF, context windows, vLLM (NEW)
- ✅ **[VOLUME-5-Model-Adaptation.md](../volumes/VOLUME-5-Model-Adaptation.md)** - LoRA, QLoRA, DPO (NEW)
- ✅ **[VOLUME-6-Data-Nexus.md](../volumes/VOLUME-6-Data-Nexus.md)** - RAG, GraphRAG, knowledge graphs (NEW)
- ✅ **[VOLUME-7-Production-Mastery.md](../volumes/VOLUME-7-Production-Mastery.md)** - Deployment, monitoring, agents (NEW)

---

## Phase 1: [1000] - Infrastructure Fabric (18 files including 2 guides)

### [1100] Network Topology & Traffic Management (3 files)
- ✅ [1101-Fiber-GPON-Modem.md](../phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md) - GPON configuration, bridge mode, WAN bypass
- ✅ [1102-Star-Topology-Core.md](../phases/phase1-infra/1100-network/1102-Star-Topology-Core.md) - 2.5Gbps switch hub logic
- ✅ [1103-Jumbo-Frames-and-MTU.md](../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md) - MTU 9000 optimization

### [1200] Host Virtualization & PCIE Passthrough (4 files)
- ✅ [1201-Proxmox-Hypervisor-SOP.md](../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md) - Core pinning, ZFS configs
- ✅ [1202-TB3-UT3G-Passthrough.md](../phases/phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md) - 11GB-class GPU eGPU passthrough
- ✅ [1203-Nvidia-Kernel-Module.md](../phases/phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md) - DKMS, driver stability
- ✅ [1204-Multi-GPU-Setup.md](../phases/phase1-infra/1200-virtualization/1204-Multi-GPU-Setup.md) - Multi-GPU configuration for an 11GB-class GPU

### [1300] Kubernetes & Container Orchestration (3 files)
- ✅ [1301-K3s-Master-Worker-Arch.md](../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md) - Cluster architecture
- ✅ [1302-GPU-Scheduler.md](../phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md) - Nvidia device plugin
- ✅ [1303-Storage-Classes.md](../phases/phase1-infra/1300-kubernetes/1303-Storage-Classes.md) - Dynamic NFS provisioning

### [1400] LLMOps Infrastructure (2 files + 2 guides)
- ✅ [1401-Ollama-Enterprise.md](../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md) - Local model APIs
- ✅ [1402-vLLM-and-TGI.md](../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - High-concurrency engines
- ✅ [1404-vLLM-Production-Deployment.md](../phases/phase1-infra/1400-llmops/guides/1404-vLLM-Production-Deployment.md)
- ✅ [1405-TGI-Deployment-Guide.md](../phases/phase1-infra/1400-llmops/guides/1405-TGI-Deployment-Guide.md) (NEW GUIDE)

### [1500] Monitoring & Observability (3 files - NEW)
- ✅ [1501-Monitoring-and-Observability.md](../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md) - Prometheus, Grafana, Loki, Tempo
- ✅ [1502-Model-Drift-Detection.md](../phases/phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) - Drift detection, statistical tests, retraining (NEW)
- ✅ [1503-LLM-Observability.md](../phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md) - LLM metrics, TTFT, TPS, cost tracking (NEW)

## Phase 2: [2000] - Cognitive Science & Frameworks (9 files including 3 guides)

### [2100] The Calculus of AI (2 files)
- ✅ [2101-Tensor-Algebra.md](../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)
- ✅ [2102-Backpropagation-and-Derivatives.md](../phases/phase2-foundations/2100-calculus/2102-Backpropagation-and-Derivatives.md)

### [2400] Pre-training (NEW)
- ✅ [2401-Pre-training-Fundamentals.md](../phases/phase2-foundations/2400-pretraining/2401-Pre-training-Fundamentals.md) - Data curation, tokenization, training pipeline (NEW)
- ✅ [2402-Large-Scale-Training.md](../phases/phase2-foundations/2400-pretraining/2402-Large-Scale-Training.md) - FSDP, DeepSpeed, multi-node training (NEW)
- ✅ [2403-Evaluation-Frameworks.md](../phases/phase2-foundations/2400-pretraining/2403-Evaluation-Frameworks.md) - MMLU, HellaSwag, GSM8K, evaluation (NEW)

### [2200] Framework Engineering (3 files)
- ✅ [2201-PyTorch-Computational-Graphs.md](../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)
- ✅ [2202-TensorFlow-XLA-Compilers.md](../phases/phase2-foundations/2200-frameworks/2202-TensorFlow-XLA-Compilers.md)
- ✅ [2203-CUDA-Kernel-Syb-Level.md](../phases/phase2-foundations/2200-frameworks/2203-CUDA-Kernel-Syb-Level.md)

### [2300] Framework Engineering (4 files + 2 guides)
- ✅ [2301-Framework-Design-Patterns.md](../phases/phase2-foundations/2300-framework-engineering/2301-Framework-Design-Patterns.md)
- ✅ [2302-Model-Serving-Architectures.md](../phases/phase2-foundations/2300-framework-engineering/2302-Model-Serving-Architectures.md)
- ✅ [2303-API-Design-for-ML.md](../phases/phase2-foundations/2300-framework-engineering/2303-API-Design-for-ML.md)
- ✅ [2304-Production-Deployment-Patterns.md](../phases/phase2-foundations/2300-framework-engineering/2304-Production-Deployment-Patterns.md)
- ✅ [2305-Framework-Comparison.md](../phases/phase2-foundations/2300-framework-engineering/guides/2305-Framework-Comparison.md) (NEW GUIDE)
- ✅ [2306-Building-Production-Framework.md](../phases/phase2-foundations/2300-framework-engineering/guides/2306-Building-Production-Framework.md) (NEW GUIDE)

## Phase 3: [3000] - Transformer Physics & LLM Internals (13 files including 3 guides)

### [3100] Attention Architectures (2 files)
- ✅ [3101-Self-Attention-DeepDive.md](../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)
- ✅ [3102-Flash-Attention.md](../phases/phase3-transformers/3100-attention/3102-Flash-Attention.md)

### [3200] Embedding Latent Spaces (2 files)
- ✅ [3201-Rotary-Positional-Embeddings-RoPE.md](../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)
- ✅ [3202-Tokenizer-Sciences.md](../phases/phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md)

### [3300] The Decoding Block (2 files + 1 guide)
- ✅ [3301-Activation-Functions.md](../phases/phase3-transformers/3300-decoding/3301-Activation-Functions.md)
- ✅ [3302-Normalization-Layers.md](../phases/phase3-transformers/3300-decoding/3302-Normalization-Layers.md)
- ✅ [3303-Activation-Function-Comparison.md](../phases/phase3-transformers/3300-decoding/guides/3303-Activation-Function-Comparison.md) (NEW GUIDE)

### [3400] Model Architectures (2 files + 2 guides)
- ✅ [3401-Encoder-Decoder-Architectures.md](../phases/phase3-transformers/3400-architectures/3401-Encoder-Decoder-Architectures.md) - T5, BART architectures
- ✅ [3402-Decoder-Only-Models.md](../phases/phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md) - GPT, LLaMA, Mistral
- ✅ [3403-Model-Architecture-Comparison.md](../phases/phase3-transformers/3400-architectures/guides/3403-Model-Architecture-Comparison.md) (NEW GUIDE)

### [3500] Multimodal Models (2 files - NEW)
- ✅ [3501-Vision-Language-Models.md](../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md) - CLIP, BLIP, LLaVA, multimodal RAG (NEW)
- ✅ [3502-Audio-Models.md](../phases/phase3-transformers/3500-multimodal/3502-Audio-Models.md) - Whisper, AudioLM, voice assistants (NEW)

## Phase 4: [4000] - Quantization & Compression (20 files including 5 guides)

### [4100] Low-Bit Quantization (3 files)
- ✅ [4101-GGUF-Physics.md](../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- ✅ [4102-EXL2-and-AWQ.md](../phases/phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md)
- ✅ [4103-Double-Quantization.md](../phases/phase4-quantization/4100-low-bit/4103-Double-Quantization.md)

### [4200] KV-Cache Engineering (2 files + 1 guide)
- ✅ [4201-Context-Window-Physics.md](../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- ✅ [4202-Speculative-Decoding.md](../phases/phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md)
- ✅ [4203-Context-Window-Optimization.md](../phases/phase4-quantization/4200-kv-cache/guides/4203-Context-Window-Optimization.md) (NEW GUIDE)

### [4300] Quantization-Aware Training (5 files + 3 guides)
- ✅ [4301-QAT-Foundations.md](../phases/phase4-quantization/4300-quantization-aware-training/4301-QAT-Foundations.md)
- ✅ [4302-Fake-Quantization.md](../phases/phase4-quantization/4300-quantization-aware-training/4302-Fake-Quantization.md)
- ✅ [4303-QAT-for-Transformers.md](../phases/phase4-quantization/4300-quantization-aware-training/4303-QAT-for-Transformers.md)
- ✅ [4304-Low-bit-QAT.md](../phases/phase4-quantization/4300-quantization-aware-training/4304-Low-bit-QAT.md)
- ✅ [4305-Quantization-Configuration.md](../phases/phase4-quantization/4300-quantization-aware-training/4305-Quantization-Configuration.md)
- ✅ [4306-PyTorch-QAT.md](../phases/phase4-quantization/4300-quantization-aware-training/guides/4306-PyTorch-QAT.md) (NEW GUIDE)
- ✅ [4307-Transformers-QAT.md](../phases/phase4-quantization/4300-quantization-aware-training/guides/4307-Transformers-QAT.md) (NEW GUIDE)
- ✅ [4308-BitBlade-QAT.md](../phases/phase4-quantization/4300-quantization-aware-training/guides/4308-BitBlade-QAT.md) (NEW GUIDE)

### [4400] Advanced Techniques (7 files + 2 guides)
- ✅ [4401-GPTQ.md](../phases/phase4-quantization/4400-advanced-techniques/4401-GPTQ.md)
- ✅ [4402-AWQ.md](../phases/phase4-quantization/4400-advanced-techniques/4402-AWQ.md)
- ✅ [4403-GGUF-Format.md](../phases/phase4-quantization/4400-advanced-techniques/4403-GGUF-Format.md)
- ✅ [4404-EXL2-Format.md](../phases/phase4-quantization/4400-advanced-techniques/4404-EXL2-Format.md)
- ✅ [4405-Sparsity-Quantization.md](../phases/phase4-quantization/4400-advanced-techniques/4405-Sparsity-Quantization.md)
- ✅ [4406-1.58-bit-Quantization.md](../phases/phase4-quantization/4400-advanced-techniques/4406-1.58-bit-Quantization.md)
- ✅ [4407-Ternary-Binary.md](../phases/phase4-quantization/4400-advanced-techniques/4407-Ternary-Binary.md)
- ✅ [4408-Quantizing-for-Production.md](../phases/phase4-quantization/4400-advanced-techniques/guides/4408-Quantizing-for-Production.md) (NEW GUIDE)
- ✅ [4409-Hardware-Specific-Optimization.md](../phases/phase4-quantization/4400-advanced-techniques/guides/4409-Hardware-Specific-Optimization.md) (NEW GUIDE)

## Phase 5: [5000] - Model Adaptation: Fine-Tuning & Alignment (16 files including 1 guide)

### [5100] Parameter Efficient Fine-Tuning (2 files + 1 guide)
- ✅ [5101-LoRA-Logic.md](../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
- ✅ [5102-QLoRA-Pipelines.md](../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)
- ✅ [5104-LoRA-Implementation-Guide.md](../phases/phase5-finetuning/5100-peft/guides/5104-LoRA-Implementation-Guide.md) (NEW GUIDE)

### [5200] SFT & Preference (2 files)
- ✅ [5201-DPO-Theory.md](../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)
- ✅ [5202-Alignment-Orchestration.md](../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md)

### [5300] Dataset Synthetic Generation (3 files)
- ✅ [5301-Knowledge-Distillation.md](../phases/phase5-finetuning/5300-synthetic/5301-Knowledge-Distillation.md)
- ✅ [5302-Distributed-Training.md](../phases/phase5-finetuning/5300-synthetic/5302-Distributed-Training.md) - Distributed training orchestration
- ✅ [5303-Federated-Learning.md](../phases/phase5-finetuning/5300-synthetic/5303-Federated-Learning.md) - Federated averaging, differential privacy (NEW)

### [5400] Distributed Training (4 files)
- ✅ [5401-Data-Parallelism.md](../phases/phase5-finetuning/5400-distributed-training/5401-Data-Parallelism.md)
- ✅ [5402-Model-Parallelism.md](../phases/phase5-finetuning/5400-distributed-training/5402-Model-Parallelism.md)
- ✅ [5403-Mixed-Precision.md](../phases/phase5-finetuning/5400-distributed-training/5403-Mixed-Precision.md)
- ✅ [5404-Distributed-Optimization.md](../phases/phase5-finetuning/5400-distributed-training/5404-Distributed-Optimization.md)

### [5500] Advanced Optimization (3 files)
- ✅ [5501-Optimizer-Variants.md](../phases/phase5-finetuning/5500-advanced-optimization/5501-Optimizer-Variants.md)
- ✅ [5502-Learning-Rate-Scheduling.md](../phases/phase5-finetuning/5500-advanced-optimization/5502-Learning-Rate-Scheduling.md)
- ✅ [5503-Advanced-Techniques.md](../phases/phase5-finetuning/5500-advanced-optimization/5503-Advanced-Techniques.md)

## Phase 6: [6000] - Data Nexus (16 files including 4 guides)

### [6100] Vector Architectures (2 files + 1 guide)
- ✅ [6101-HNSW-Indexing.md](../phases/phase6-rag/6100-vector/6101-HNSW-Indexing.md)
- ✅ [6102-Semantic-Similarity.md](../phases/phase6-rag/6100-vector/6102-Semantic-Similarity.md)
- ✅ [6103-HNSW-Tuning-Guide.md](../phases/phase6-rag/6100-vector/guides/6103-HNSW-Tuning-Guide.md) (NEW GUIDE)

### [6200] RAG 2.0 (2 files)
- ✅ [6201-Hybrid-Search.md](../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md)
- ✅ [6202-Re-ranking-and-Retrieval-Logistics.md](../phases/phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md)

### [6300] GraphRAG (2 files + 2 guides)
- ✅ [6301-Neo4j-and-Knowledge-Graphs.md](../phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md)
- ✅ [6302-CAG-Long-Context-Architectures.md](../phases/phase6-rag/6300-context/6302-CAG-Long-Context-Architectures.md)
- ✅ [6303-Neo4j-Deployment-Guide.md](../phases/phase6-rag/6300-context/guides/6303-Neo4j-Deployment-Guide.md)
- ✅ [6304-GraphRAG-Implementation.md](../phases/phase6-rag/6300-context/guides/6304-GraphRAG-Implementation.md) (NEW GUIDE)

### [6400] Vector Databases (2 files + 1 guide)
- ✅ [6401-Qdrant-Setup.md](../phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md) - Qdrant deployment guide
- ✅ [6402-Pinecone-vs-Weaviate.md](../phases/phase6-rag/6400-vector-databases/6402-Pinecone-vs-Weaviate.md) - Comparison
- ✅ [6403-Qdrant-Production-Deployment.md](../phases/phase6-rag/6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md) (NEW GUIDE)

### [6500] MLOps Pipelines (3 files - NEW)
- ✅ [6501-ML-Lifecycle-Management.md](../phases/phase6-rag/6500-mlops-pipelines/6501-ML-Lifecycle-Management.md) - Development, validation, deployment, monitoring, retirement (NEW)
- ✅ [6502-CI-CD-for-ML.md](../phases/phase6-rag/6500-mlops-pipelines/6502-CI-CD-for-ML.md) - Automated ML pipelines, canary deployment (NEW)
- ✅ [6503-Model-Registry.md](../phases/phase6-rag/6500-mlops-pipelines/6503-Model-Registry.md) - MLflow, W&B, versioning, metadata (NEW)

## Phase 7: [7000] - Agentic Cognition & Autonomy (13 files including 4 guides)

### [7100] Reason & Plan (2 files + 1 guide)
- ✅ [7101-ReAct-Loop-System.md](../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
- ✅ [7102-Planning-Decomposition.md](../phases/phase7-agentic/7100-architecture/7102-Planning-Decomposition.md)
- ✅ [7103-ReAct-Implementation-Guide.md](../phases/phase7-agentic/7100-architecture/guides/7103-ReAct-Implementation-Guide.md) (NEW GUIDE)

### [7200] Tool-Calling (1 file + 1 guide)
- ✅ [7201-Tool-Calling.md](../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md)
- ✅ [7202-Code-Interpreter.md](../phases/phase7-agentic/7200-tools/guides/7202-Code-Interpreter.md) (NEW GUIDE)

### [7300] Multi-Agent Orchestration (1 file + 1 guide)
- ✅ [7301-Orchestration.md](../phases/phase7-agentic/7300-orchestration/7301-Orchestration.md)
- ✅ [7303-Framework-Comparison.md](../phases/phase7-agentic/7300-orchestration/guides/7303-Framework-Comparison.md) (NEW GUIDE)

### [7400] Agent Memory (1 file + 1 guide)
- ✅ [7401-Long-term-Memory.md](../phases/phase7-agentic/7400-memory/7401-Long-term-Memory.md) - VectorStore and Memoria
- ✅ [7402-Agent-Memory-Implementation.md](../phases/phase7-agentic/7400-memory/guides/7402-Agent-Memory-Implementation.md) (NEW GUIDE)

### [7500] AI Security (3 files - NEW)
- ✅ [7501-Prompt-Injection-Defense.md](../phases/phase7-agentic/7500-security/7501-Prompt-Injection-Defense.md) - Attack taxonomy, input filtering, perplexity detection (NEW)
- ✅ [7502-PII-Redaction.md](../phases/phase7-agentic/7500-security/7502-PII-Redaction.md) - PII detection, redaction, Presidio, compliance (NEW)
- ✅ [7503-Adversarial-Attacks.md](../phases/phase7-agentic/7500-security/7503-Adversarial-Attacks.md) - FGSM, adversarial training, robustness testing (NEW)

---

## Additional Files

### Root Level
- ✅ [README.md](../../README.md) - Main project overview
- ✅ [SITEMAP.md](SITEMAP.md) - This file
- ✅ **[0000-LEARNING-PATH.md](0000-LEARNING-PATH.md)** ← **START HERE: Complete curriculum roadmap (NEW)**
- ✅ **[QUICK-START.md](QUICK-START.md)** - Get started in 30 minutes (NEW)
- ✅ **[PROGRESS-TRACKER.md](PROGRESS-TRACKER.md)** - Track your learning progress (NEW)

### Tutorials (UPDATED - 14 tutorials total)
- ✅ **[TUTORIAL-000: Python for AI](../learning-resources/tutorials/TUTORIAL-000-Python-for-AI.md)** - Python fundamentals for AI development (NEW)
- ✅ **[TUTORIAL-001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)** - Your first local LLM (NEW)
- ✅ **[TUTORIAL-002: Docker Essentials](../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md)** - Container basics for AI (NEW)
- ✅ **[TUTORIAL-003: RAG Basics](../learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md)** - Build your first RAG system (NEW)
- ✅ **[TUTORIAL-004: Monitoring](../learning-resources/tutorials/TUTORIAL-004-Monitoring.md)** - Observability with Prometheus, Grafana, Loki, Tempo (NEW)
- ✅ **[TUTORIAL-005: Production Deployment](../learning-resources/tutorials/TUTORIAL-005-Production-Deployment.md)** - SSL, Nginx, CI/CD (NEW)
- ✅ **[TUTORIAL-006: Real-time AI](../learning-resources/tutorials/TUTORIAL-006-Real-time-AI.md)** - Streaming responses and WebSockets (NEW)
- ✅ **[TUTORIAL-007: LoRA Basics](../learning-resources/tutorials/TUTORIAL-007-LoRA-Basics.md)** - LoRA fine-tuning fundamentals (NEW)
- ✅ **[TUTORIAL-008: CUDA Programming](../learning-resources/tutorials/TUTORIAL-008-CUDA-Programming.md)** - GPU programming basics (NEW)
- ✅ **[TUTORIAL-009: Advanced RAG Techniques](../learning-resources/tutorials/TUTORIAL-009-Advanced-RAG-Techniques.md)** - Hybrid search, re-ranking, GraphRAG (NEW)
- ✅ **[TUTORIAL-010: Model Evaluation](../learning-resources/tutorials/TUTORIAL-010-Model-Evaluation.md)** - Benchmarking and metrics (NEW)
- ✅ **[TUTORIAL-011: Multi-Modal AI](../learning-resources/tutorials/TUTORIAL-011-Multi-Modal-AI.md)** - Vision and language models (NEW)
- ✅ **[TUTORIAL-012: Production LLMOps](../learning-resources/tutorials/TUTORIAL-012-Production-LLMOps.md)** - Production ML operations (NEW)
- ✅ **[TUTORIAL-013: AI Security](../learning-resources/tutorials/TUTORIAL-013-AI-Security.md)** - Prompt injection, PII redaction (NEW)
- ✅ **[TUTORIAL-014: Production LLM Systems](../learning-resources/tutorials/TUTORIAL-014-Production-LLM-Systems.md)** - End-to-end production systems (NEW)

### Labs (NEW - Hands-on Exercises)
- ✅ **[LAB 001: Docker & LLM](../learning-resources/labs/LAB-001-Docker-LLM.md)** - Run LLMs in Docker (2 hours) (NEW)
- ✅ **[LAB 002: RAG Implementation](../learning-resources/labs/LAB-002-RAG-Implementation.md)** - Build RAG with Qdrant (3 hours) (NEW)
- ✅ **[LAB 003: LoRA Fine-Tuning](../learning-resources/labs/LAB-003-LoRA-FineTuning.md)** - Fine-tune models with QLoRA (4 hours) (NEW)
- ✅ **[LAB 004: ReAct Agent](../learning-resources/labs/LAB-004-ReAct-Agent.md)** - Build reasoning agents (4 hours) (NEW)
- ✅ **[LAB 005: GraphRAG](../learning-resources/labs/LAB-005-GraphRAG.md)** - Knowledge graph RAG (5 hours) (NEW)
- ✅ **[LAB 006: Train Model from Scratch](../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md)** - Train 10M parameter model (6-8 hours) (NEW)
- ✅ **[LAB 007: Production RAG](../learning-resources/labs/LAB-007-Production-RAG.md)** - Enterprise-grade RAG with hybrid search (6-8 hours) (NEW)
- ✅ **[LAB 008: Agent Fleet](../learning-resources/labs/LAB-008-Agent-Fleet.md)** - Multi-agent system orchestration (6-8 hours) (NEW)
- ✅ **[LAB 009: Production Deployment](../learning-resources/labs/LAB-009-Production-Deployment.md)** - Deploy AI systems at scale (8-10 hours) (NEW)
- ✅ **[LAB 010: DPO Alignment](../learning-resources/labs/LAB-010-DPO-Alignment.md)** - Direct Preference Optimization for alignment (5-6 hours) (NEW)
- ✅ **[LAB 011: Multi-Modal AI](../learning-resources/labs/LAB-011-Multi-Modal-AI.md)** - Vision + Language models (6-8 hours) (NEW)
- ✅ **[LAB 012: Audio AI](../learning-resources/labs/LAB-012-Audio-AI.md)** - Speech recognition and synthesis (4-5 hours) (NEW)
- ✅ **[LAB 013: Advanced Function Calling](../learning-resources/labs/LAB-013-Advanced-Function-Calling.md)** - Tool orchestration (5-6 hours) (NEW)
- ✅ **[LAB 014: AI Evaluation & Safety](../learning-resources/labs/LAB-014-AI-Evaluation-Safety.md)** - Testing, benchmarking, and security (4-5 hours) (NEW)

### Cheat Sheets (NEW - Quick Reference)
- ✅ **[CHEAT SHEET 001: Docker](../learning-resources/cheat-sheets/CHEAT-SHEET-001-Docker.md)** - Essential Docker commands (NEW)
- ✅ **[CHEAT SHEET 002: Python AI](../learning-resources/cheat-sheets/CHEAT-SHEET-002-Python-AI.md)** - Python for AI/ML (NEW)
- ✅ **[CHEAT SHEET 003: Git](../learning-resources/cheat-sheets/CHEAT-SHEET-003-Git.md)** - Git & Version Control (NEW)
- ✅ **[CHEAT SHEET 004: Linux](../learning-resources/cheat-sheets/CHEAT-SHEET-004-Linux.md)** - Linux Commands (NEW)
- ✅ **[Volume 1 Quick Reference](../learning-resources/cheat-sheets/QUICK-REF-VOLUME-1.md)** - Infrastructure essentials (NEW)
- ✅ **[Volume 2 Quick Reference](../learning-resources/cheat-sheets/QUICK-REF-VOLUME-2.md)** - AI foundations & math (NEW)
- ✅ **[Volume 3 Quick Reference](../learning-resources/cheat-sheets/QUICK-REF-VOLUME-3.md)** - Transformer internals (NEW)
- ✅ **[Volume 4 Quick Reference](../learning-resources/cheat-sheets/QUICK-REF-VOLUME-4.md)** - Quantization techniques (NEW)
- ✅ **[Volume 5 Quick Reference](../learning-resources/cheat-sheets/QUICK-REF-VOLUME-5.md)** - Fine-tuning & alignment (NEW)
- ✅ **[Volume 6 Quick Reference](../learning-resources/cheat-sheets/QUICK-REF-VOLUME-6.md)** - RAG & vector databases (NEW)
- ✅ **[Volume 7 Quick Reference](../learning-resources/cheat-sheets/QUICK-REF-VOLUME-7.md)** - Production systems & agents (NEW)

### Interactive Elements (NEW - Flashcards, Quizzes, Challenges)
- ✅ **[INTERACTIVE: Learning Components](../learning-resources/interactive/FLASHCARDS.md)** - Flashcards, quizzes, code challenges, visual diagrams (NEW)
  - Flashcards for quick recall
  - Interactive quizzes with immediate feedback
  - Coding challenges with hints and tests
  - Animated concepts and visualizations
  - Progress trackers for monitoring learning

### Troubleshooting (NEW - Common Issues)
- ✅ **[TROUBLESHOOTING: Common Issues](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)** - Solutions to common problems (NEW)

### Capstone Projects (NEW - End-to-End Projects)
- ✅ **[PROJECT 001: Build Your AI Assistant](../learning-resources/projects/PROJECT-001-AI-Assistant.md)** - Complete AI assistant with RAG, ReAct, and tools (NEW)
- ✅ **[PROJECT 002: Train Neural Network from Scratch](../learning-resources/projects/PROJECT-002-Train-Neural-Network.md)** - Mathematics meets implementation - Train your first model (NEW)
- ✅ **[PROJECT 003: Transformer from Scratch](../learning-resources/projects/PROJECT-003-Transformer-From-Scratch.md)** - Build the architecture powering modern LLMs (NEW)
- ✅ **[PROJECT 004: Quantize LLM from Scratch](../learning-resources/projects/PROJECT-004-Quantize-Model.md)** - Run large models on limited hardware (NEW)
- ✅ **[PROJECT 005: Fine-Tune Domain Model](../learning-resources/projects/PROJECT-005-FineTune-Model.md)** - Adapt an LLM to your specific use case (NEW)
- ✅ **[PROJECT 006: Build Production RAG System](../learning-resources/projects/PROJECT-006-Production-RAG.md)** - Integrate LLMs with your knowledge base (NEW)
- ✅ **[PROJECT 007: Deploy Production AI System](../learning-resources/projects/PROJECT-007-Production-AI-System.md)** - Build and deploy a complete AI system at scale (NEW)

### Case Studies (NEW - Real-World Examples)
- ✅ **[Real-World Examples & Case Studies](../learning-resources/case-studies/REAL-WORLD-EXAMPLES.md)** - Production examples from enterprise systems (NEW)

### Configurations
- ✅ [configs/README.md](../../configs/README.md) - Complete configuration guide (UPDATED)
- ✅ [configs/docker-compose.yml](../../configs/docker-compose.yml) - Docker Compose for Synology
- ✅ [configs/docker-compose-complete.yml](../../configs/docker-compose-complete.yml) - Complete stack with monitoring (NEW)
- ✅ [configs/docker-compose-gpu.yml](../../configs/docker-compose-gpu.yml) - GPU VM services (NEW)
- ✅ [configs/k3s-manifests.yaml](../../configs/k3s-manifests.yaml) - Kubernetes manifests
- ✅ [configs/nginx/nginx.conf](../../configs/nginx/nginx.conf) - Nginx API Gateway (NEW)
- ✅ [configs/nginx/conf.d/default.conf](../../configs/nginx/conf.d/default.conf) - Service routes (NEW)
- ✅ [configs/ci-cd/.github/workflows/deploy.yml](../../configs/ci-cd/.github/workflows/deploy.yml) - GitHub Actions CI/CD (NEW)
- ✅ [configs/scripts/backup.sh](../../configs/scripts/backup.sh) - Backup script (NEW)
- ✅ [configs/scripts/restore.sh](../../configs/scripts/restore.sh) - Restore script (NEW)
- ✅ [configs/services/react-agent/Dockerfile](../../configs/services/react-agent/Dockerfile) - ReAct Agent container (NEW)
- ✅ [configs/services/graphrag/Dockerfile](../../configs/services/graphrag/Dockerfile) - GraphRAG container (NEW)
- ✅ [configs/monitoring/prometheus/prometheus.yml](../../configs/monitoring/prometheus/prometheus.yml) - Prometheus config (NEW)
- ✅ [configs/monitoring/loki/loki.yml](../../configs/monitoring/loki/loki.yml) - Loki config (NEW)
- ✅ [configs/monitoring/tempo/tempo.yml](../../configs/monitoring/tempo/tempo.yml) - Tempo config (NEW)
- ✅ [configs/monitoring/promtail/promtail.yml](../../configs/monitoring/promtail/promtail.yml) - Promtail config (NEW)
- ✅ [configs/monitoring/grafana/provisioning/datasources/datasources.yml](../../configs/monitoring/grafana/provisioning/datasources/datasources.yml) - Grafana datasources (NEW)
- ✅ [configs/monitoring/grafana/provisioning/dashboards/dashboards.yml](../../configs/monitoring/grafana/provisioning/dashboards/dashboards.yml) - Grafana dashboards (NEW)
- ✅ [configs/monitoring/grafana/dashboards/project-omega-overview.json](../../configs/monitoring/grafana/dashboards/project-omega-overview.json) - Overview dashboard (NEW)
- ✅ [configs/monitoring/grafana/dashboards/gpu-monitoring.json](../../configs/monitoring/grafana/dashboards/gpu-monitoring.json) - GPU dashboard (NEW)
- ✅ [configs/performance-testing/k6/load-test.js](../../configs/performance-testing/k6/load-test.js) - k6 load tests (NEW)
- ✅ [configs/docs/ssl-tls-setup.md](../../configs/docs/ssl-tls-setup.md) - SSL/TLS setup guide (NEW)
- ✅ [configs/service-mesh/istio/values.yaml](../../configs/service-mesh/istio/values.yaml) - Istio configuration (NEW)
- ✅ [configs/service-mesh/istio/virtualservices.yaml](../../configs/service-mesh/istio/virtualservices.yaml) - Istio virtual services (NEW)

### Experiments
- ✅ 44 experiment template files covering key documentation topics
  - [EXP_1101_GPON.md](../../experiments/EXP_1101_GPON.md)
  - [EXP_1302_GPU_SCHEDULER.md](../../experiments/EXP_1302_GPU_SCHEDULER.md)
  - [EXP_1501_MONITORING.md](../../experiments/EXP_1501_MONITORING.md) (NEW)
  - [EXP_1502_MODEL_DRIFT.md](../../experiments/EXP_1502_MODEL_DRIFT.md) (NEW)
  - [EXP_2101_TENSOR_ALGEBRA.md](../../experiments/EXP_2101_TENSOR_ALGEBRA.md)
  - [EXP_2102_BACKPROPAGATION.md](../../experiments/EXP_2102_BACKPROPAGATION.md)
  - [EXP_2201_PYTORCH_GRAPHS.md](../../experiments/EXP_2201_PYTORCH_GRAPHS.md)
  - [EXP_2202_TENSORFLOW_XLA.md](../../experiments/EXP_2202_TENSORFLOW_XLA.md)
  - [EXP_2203_CUDA_KERNELS.md](../../experiments/EXP_2203_CUDA_KERNELS.md)
  - [EXP_3101_SELF_ATTENTION.md](../../experiments/EXP_3101_SELF_ATTENTION.md)
  - [EXP_3102_FLASH_ATTENTION.md](../../experiments/EXP_3102_FLASH_ATTENTION.md) (NEW)
  - [EXP_3201_ROPE.md](../../experiments/EXP_3201_ROPE.md) (NEW)
  - [EXP_3202_TOKENIZER.md](../../experiments/EXP_3202_TOKENIZER.md) (NEW)
  - [EXP_3401_ENCODER_DECODER.md](../../experiments/EXP_3401_ENCODER_DECODER.md)
  - [EXP_3501_MULTIMODAL_RAG.md](../../experiments/EXP_3501_MULTIMODAL_RAG.md) (NEW)
  - [EXP_4101_GGUF.md](../../experiments/EXP_4101_GGUF.md)
  - [EXP_4102_EXL2_AWQ.md](../../experiments/EXP_4102_EXL2_AWQ.md)
  - [EXP_4103_DOUBLE_QUANT.md](../../experiments/EXP_4103_DOUBLE_QUANT.md)
  - [EXP_4201_CONTEXT_WINDOW.md](../../experiments/EXP_4201_CONTEXT_WINDOW.md) (NEW)
  - [EXP_4202_SPECULATIVE_DECODING.md](../../experiments/EXP_4202_SPECULATIVE_DECODING.md) (NEW)
  - [EXP_5101_LORA.md](../../experiments/EXP_5101_LORA.md) (UPDATED)
  - [EXP_5102_QLORA.md](../../experiments/EXP_5102_QLORA.md)
  - [EXP_5201_DPO.md](../../experiments/EXP_5201_DPO.md) (NEW)
  - [EXP_5202_ALIGNMENT.md](../../experiments/EXP_5202_ALIGNMENT.md)
  - [EXP_5301_DISTILLATION.md](../../experiments/EXP_5301_DISTILLATION.md)
  - [EXP_5302_DISTRIBUTED.md](../../experiments/EXP_5302_DISTRIBUTED.md)
  - [EXP_5303_FEDERATED_LEARNING.md](../../experiments/EXP_5303_FEDERATED_LEARNING.md) (NEW)
  - [EXP_6101_HNSW.md](../../experiments/EXP_6101_HNSW.md)
  - [EXP_6102_SIMILARITY.md](../../experiments/EXP_6102_SIMILARITY.md)
  - [EXP_6201_HYBRID_SEARCH.md](../../experiments/EXP_6201_HYBRID_SEARCH.md) (NEW)
  - [EXP_6202_RERANK.md](../../experiments/EXP_6202_RERANK.md)
  - [EXP_6301_GRAPHRAG.md](../../experiments/EXP_6301_GRAPHRAG.md)
  - [EXP_6302_CAG.md](../../experiments/EXP_6302_CAG.md)
  - [EXP_6303_NEO4J.md](../../experiments/EXP_6303_NEO4J.md) (NEW)
  - [EXP_6401_VECTOR_DB.md](../../experiments/EXP_6401_VECTOR_DB.md)
  - [EXP_6501_MLOPS_PIPELINE.md](../../experiments/EXP_6501_MLOPS_PIPELINE.md) (NEW)
  - [EXP_7101_REACT.md](../../experiments/EXP_7101_REACT.md)
  - [EXP_7102_PLANNING.md](../../experiments/EXP_7102_PLANNING.md)
  - [EXP_7201_MULTI_AGENT.md](../../experiments/EXP_7201_MULTI_AGENT.md)
  - [EXP_7202_COLLABORATION.md](../../experiments/EXP_7202_COLLABORATION.md)
  - [EXP_7301_SANDBOX.md](../../experiments/EXP_7301_SANDBOX.md)
  - [EXP_7401_AGENT_MEMORY.md](../../experiments/EXP_7401_AGENT_MEMORY.md)
  - [EXP_7501_PROMPT_INJECTION.md](../../experiments/EXP_7501_PROMPT_INJECTION.md) (NEW)

### Legacy Labs (Archived)
- ⚠️ 15 legacy labs using old phase-based numbering (archived for reference)
  - See [Legacy Labs](../learning-resources/labs/legacy/README.md) for full list
  - LAB-201 through LAB-603 have been superseded by the new sequential lab system

### Diagrams
- ✅ Architecture diagrams and visualizations
  - [diagrams/README.md](../diagrams/README.md) - Diagram index
  - Infrastructure topology diagrams
  - RAG pipeline diagrams
  - Agent architecture diagrams
  - Transformer architecture diagrams

---

## Statistics

```
Total Documentation Files: 570+ (including all markdown files)
Total Phases: 7
Total Phase Files: 224 (85 technical + 139 supporting)
Total Volumes: 7 (Book-like structure)
Main Categories: 29
Experiment Templates: 47
Configuration Files: 24
Implementation Guides: 14
Learning Resources: 75+ (volume guides + tutorials + labs + cheat sheets + projects + troubleshooting + case studies)
Legacy Labs (Archived): 15 (LAB-201 through LAB-603)
```

**File Breakdown:**
- Technical Modules: 85
- Supporting Files (QUIZ, PRACTICE, CHECKPOINT, etc.): 139
- Volume Guides: 7
- Tutorials: 14
- Active Labs: 15 (LAB-000 through LAB-014)
- Lab Solutions: 15
- Legacy Labs: 15 (archived)
- Cheat Sheets: 11
- Projects: 7 capstone + templates
- Experiments: 47
- Diagrams: 3+
- Configuration Files: 24

---

## Quick Navigation by Topic

| Topic | Files |
|-------|--------|
| **Volume Guides** | VOLUME-1, VOLUME-2, VOLUME-3, VOLUME-4, VOLUME-5, VOLUME-6, VOLUME-7 |
| **Quick Start** | QUICK-START, PROGRESS-TRACKER, 0000-LEARNING-PATH |
| **Tutorials** | TUTORIAL-001 through 006 |
| **Active Labs** | LAB-000 through LAB-014 (15 labs with solutions) |
| **Legacy Labs** | LAB-201 through LAB-603 (archived, see labs/legacy/) |
| **Cheat Sheets** | CHEAT-SHEET-001 through 004, QUICK-REF-VOLUME-1 through 7 |
| **Projects** | PROJECT-001 through 007 |
| **Case Studies** | REAL-WORLD-EXAMPLES |
| **Troubleshooting** | TROUBLESHOOTING-Common-Issues |
| **Diagrams** | Architecture diagrams (see diagrams/README.md) |
| **Experiments** | EXP_1101 through EXP_7501 (47 experiment templates) |
| **Networking** | 1101, 1102, 1103 |
| **Monitoring** | 1501, 1502, 1503, TUTORIAL-004 |
| **LLMOps** | 1401, 1402, 1404, 1405, TUTORIAL-005 |
| **MLOps** | 6501, 6502, 6503 |
| **GPU/Passthrough** | 1202, 1203, 1302 |
| **Kubernetes** | 1301, 1302, 1303 |
| **Math Foundation** | 2101, 2102 |
| **ML Frameworks** | 2201, 2202, 2203 |
| **Transformers** | 3101, 3102, 3201, 3202, 3301, 3302, 3303, 3401, 3402, 3403 |
| **Multimodal** | 3501, 3502 |
| **Quantization** | 4101, 4102, 4103, 4201, 4202, 4203 |
| **Fine-Tuning** | 5101, 5102, 5104, 5201, 5202, 5301, 5302, 5303, LAB-003, LAB-010 |
| **RAG/Vectors** | 6101, 6102, 6103, 6201, 6202, 6301, 6302, 6303, 6304, 6401, 6402, 6403, TUTORIAL-003, LAB-002, LAB-005, LAB-007 |
| **GraphRAG** | 6301, 6302, 6303, 6304, LAB-005 |
| **Agents** | 7101, 7102, 7103, 7201, 7202, 7203, 7301, 7302, 7401, 7402, LAB-004, LAB-008 |
| **Security** | 7501, 7502, 7503 |
| **Production** | 1501, 1502, 1503, LAB-007, LAB-008, LAB-009, TUTORIAL-005, TUTORIAL-006, REAL-WORLD-EXAMPLES |
| **Multi-Modal** | 3501, 3502, LAB-011 |
| **Audio/Speech** | 3502, LAB-012 |
| **Function Calling** | LAB-013 |
| **Evaluation/Safety** | LAB-014 |
