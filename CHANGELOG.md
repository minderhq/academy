---
Document ID: CHANGELOG
Title: "CHANGELOG"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
---

# CHANGELOG

All notable changes to PROJECT-OMEGA documentation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-10-02

### Fixed - Live-Verified Content Corrections
- **Learner-facing bug chain drained** across the practice and guide
  corpus, every fix executed against the running stack before landing:
  the from-scratch autograd exercise's wrong-axis gradient broadcast
  and backward-hook return contract (phase 2), the transformers 5.x
  output-API drift (CLIP `pooler_output` at fourteen sites across five
  files), the torch.ao QAT legacy-API group (`prepare_qat` train-mode
  requirement, per-channel observer class, HF `post_init` contract,
  phase 4), the float32-vs-float16 KV-cache matmul dtype trap
  (phase 4), the DPO/reward loss and GPT-2 Conv1D LoRA projection
  naming bugs (phase 5), and an offline langgraph agent scaffold that
  no longer needs API credentials to run (phase 6)
- **Execution census fully adjudicated:** 582 → 556 accepted rows,
  every remaining row carrying a verified env-gap / service-needing /
  by-design-hang / learner-artifact note

### Added - Quality Infrastructure Growth
- **92 hard QA gates (total 98)**: census_note_gate (CN-01/02) makes
  the execution census's must-be-adjudicated contract mechanical;
  meta_claims_check now locks this changelog's newest gate-count claim
  to quality_report.GATES itself, and notebook_unfinished_scan
  (NU-01/02) extends the unfinished-marker lock to the .ipynb universe
  the .md-only extraction cannot see - 108 `# TODO:` exercise prompts
  stay legitimate, notebook prose obeys the same rule as file prose
- **lesson_similarity_scan** (report tool): 5-word-shingle Jaccard
  over all 6441 lesson pairs - born at zero clone findings with a max
  similarity of 0.058, lesson diversity under continuous lock
- **Repo hygiene verified:** 604 tracked files, zero committed
  binaries, zero untracked strays

## [1.2.0] - 2026-09-30

### Changed - Curriculum Modernization Era
- **uv everywhere:** installation, Quick Start, labs and project templates
  migrated from `pip` to `uv` for faster, lockfile-based workflows;
  automated checks keep learner install flows on uv
- **Python 3.13 target** with modern typing across code examples
  (PEP 585 built-in generics, PEP 604 `X | Y` unions)
- **LangChain modernization pass** aligned framework teaching to the
  current API surface
- **Model-naming standards** codified in the Style Guide: vendor-era
  casing (Llama 2/3 vs the original LLaMA) and prose-vs-identifier
  name forms (Mistral 7B in prose, Mistral-7B in spec tables, repo
  ids exactly as published)
- **Assessment hardening:** quiz integrity gates, answer-key
  formatting, and difficulty-badge truthfulness (the rendered badge
  must mirror the front-matter value)

### Added - Quality Infrastructure
- **83 hard QA gates** (`scripts/qa/quality_report.py`): structure,
  links, code fences, front matter, tables, diagrams, tags, lesson
  IDs, quiz integrity, and navigation coverage - every module doc is
  linked from its module README, every phase checkpoint from its
  phase README
- **Report-only scanners** for judgment-bound conventions: link
  reachability (this changelog's own discoverability was its first
  catch), model-name forms, stale front matter, and callout texture

## [1.1.0] - 2026-02-04

### Added - Comprehensive Assessment System
- **10 QUIZ.md files** for Phase 6-7 modules (20 questions each, 80% passing score)
  - 6100: Vector Embeddings
  - 6200: Advanced Retrieval
  - 6300: Context Optimization
  - 6400: Vector Databases
  - 6500: RAG MLOps
  - 7100: LLM Reasoning
  - 7200: Tools & Function Calling
  - 7300: Agent Orchestration
  - 7400: Agent Memory
  - 7500: Agent Security

- **15 PRACTICE.md files** with hands-on exercises
  - 1300: Kubernetes exercises
  - 1400: LLMOps exercises
  - 1500: Monitoring setup
  - 2400: Pretraining pipeline
  - 3200: Embedding implementations
  - 3300: Decoding strategies
  - 3400: Transformer architectures
  - 3500: Multimodal AI
  - 4100: Low-bit quantization
  - 4200: KV cache optimization
  - 5100: PEFT techniques
  - 5200: Alignment methods
  - 5300: Synthetic data generation
  - 6200: Advanced retrieval
  - 6300: Context optimization

### Added - 15 Hands-on Labs
- LAB-201: PyTorch Fundamentals
- LAB-202: Deep Learning Basics
- LAB-301: Self-Attention
- LAB-302: Transformer Architecture
- LAB-303: GPT Implementation
- LAB-401: Post-Training Quantization
- LAB-402: GPTQ Quantization
- LAB-403: KV Cache
- LAB-501: LoRA Fine-tuning
- LAB-502: DPO Alignment
- LAB-503: Synthetic Data
- LAB-601: Building RAG
- LAB-602: Advanced RAG
- LAB-603: Vector Databases
- LAB-701: Agentic Systems

### Added - 20 Jupyter Notebooks
- NB-201: PyTorch Basics
- NB-202: Deep Learning Fundamentals
- NB-203: NLP for LLMs
- NB-204: Data Loading & Processing
- NB-205: Evaluation Metrics
- NB-301: Self-Attention Implementation
- NB-302: Transformer Architecture
- NB-303: GPT-Style Decoder
- NB-401: Quantization Techniques
- NB-402: GPTQ Quantization
- NB-403: KV Cache Optimization
- NB-501: LoRA Fine-tuning
- NB-502: DPO Alignment
- NB-503: Synthetic Data Generation
- NB-601: Building RAG
- NB-602: Advanced RAG Techniques
- NB-603: Vector Databases
- NB-701: Agentic Systems
- NB-702: Agent Memory Systems
- NB-703: Agent Security

### Added - 12 Project Templates
- TEMPLATE-001: Simple LLM App
- TEMPLATE-002: Fine-tuning Pipeline
- TEMPLATE-003: RAG System
- TEMPLATE-004: Agent Framework
- TEMPLATE-005: Model Quantization
- TEMPLATE-006: Synthetic Data Generator
- TEMPLATE-007: LLM Evaluation Benchmark
- TEMPLATE-008: Multi-Modal Application
- TEMPLATE-009: Model Deployment
- TEMPLATE-010: Chatbot UI
- TEMPLATE-011: Model Merging & MoE
- TEMPLATE-012: End-to-End Pipeline

### Added - Video & External Resources
- Curated list of 100+ video courses
- Research paper links
- Interactive platform recommendations
- Community resources
- Per-phase resource breakdown

### Added - Interactive Learning Components
- Flashcard system design
- Quiz templates
- Code challenge framework
- Visual diagram templates
- Progress tracking system

### Changed - Documentation Structure
- Reorganized phase directories for consistency
- Updated all module README files
- Added cross-references between related topics
- Improved navigation with quick links

## [1.0.0] - 2026-01-XX

### Added
- Initial PROJECT-OMEGA documentation structure
- 7 phases covering complete LLM development stack
- 85 core technical documents
- Phase-based learning organization
- Volume-based learning guides
- Infrastructure specifications
- Experiment templates

[1.1.0]: https://github.com/your-org/project-omega/releases/tag/v1.1.0
[1.2.0]: https://github.com/your-org/project-omega/releases/tag/v1.2.0
[1.0.0]: https://github.com/your-org/project-omega/releases/tag/v1.0.0

---

## Version Summary

| Version | Date | Changes |
|---------|------|---------|
| **1.2.0** | 2026-09-30 | Curriculum modernization (uv, Python 3.13, LangChain), QA infrastructure |
| **1.1.0** | 2026-02-04 | Assessment system, labs, notebooks, projects, resources |
| **1.0.0** | 2026-01-XX | Initial release with core documentation |
