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

### Changed - Lab Fleet Transparency
- **The lab fleet transition is now on record:** the legacy LAB-2xx..7xx fleet was retired from docs/learning-resources/labs/legacy/ on 2026-09-24, before the 1.2.0 release - the 1.1.0 entry below still lists those legacy ids, which was true at that release - while the active fleet is LAB-000 through LAB-014 (15 labs + 15 solutions) and appears in no release entry until now
- **MASTER-INDEX Labs rows drained to lab truth:** 14 of the 15 index rows carried a drift against the labs' own front matter - 12 Duration cells under-reported the declared Estimated Time (the index summed ~53 hours against ~85 declared, LAB-009 reading 4 hours against 12) and 10 Lab titles abbreviated away the full forms - every row now mirrors the front-matter contract verbatim under the new lab_index_parity_check lock

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
- **102 hard QA gates (total 108)**: census_note_gate (CN-01/02) makes
  the execution census's must-be-adjudicated contract mechanical;
  meta_claims_check now locks this changelog's newest gate-count claim
  to quality_report.GATES itself, notebook_unfinished_scan
  (NU-01/02) extends the unfinished-marker lock to the .ipynb universe
  the .md-only extraction cannot see - 108 `# TODO:` exercise prompts
  stay legitimate, notebook prose obeys the same rule as file prose -
  and notebook_catalog_check (NC-01/02) locks the two-table notebook
  catalog (README index vs MASTER-INDEX) against content drift, and changelog_summary_check (CS-01..05) keeps the changelog's own release index (sections vs Version Summary table vs reference-link definitions) synchronized, and lab_index_parity_check (LI-01..03) locks MASTER-INDEX's Labs table to every lab's front-matter contract (id set, Estimated Time, title), and tutorial_index_parity_check (TI-01..05) locks MASTER-INDEX's Tutorials table to every tutorial's front matter (difficulty, Estimated Time, normalized prerequisite sets - free-text prerequisites are findings, id-set parity both directions; the mirror follows the evidence-backed richer side per field), and cheatsheet_index_parity_check (CI-01..04) locks MASTER-INDEX's Cheat Sheets table to the 13-file fleet (id-set parity with QUICK-REF id normalization, the topic cell mirroring the front-matter Title verbatim, the header's file count matching the row count, and every row's link naming its own file) - born catching CHEAT-SHEET-006 invisible to the index it was counted in, and project_index_parity_check (PJ-01..06) locks MASTER-INDEX's Projects table to the 7-file capstone fleet (id-set parity, the project cell mirroring the front-matter Title verbatim, the header's file count matching the row count, every row's link naming its own file, the Difficulty column mirroring front matter verbatim, and a locked "N weeks" duration form - projects deliberately carry no Estimated Time since the pacing census does hour/minute arithmetic) - born at 13 findings: 6 abbreviated project cells and a missing Difficulty column the front matter already declared, and small_index_parity_check (SG-01..04) locks MASTER-INDEX's six small resource tables (Career Guides, Comparisons, Industry Applications, Use Cases, Solutions, Diagrams) to their directories' files (id-set parity per table, every row's link text naming its own target, the header's file count matching the row count, and the description cell mirroring the front-matter Title verbatim - the fleet's heterogeneous title conventions make the mirror deliberately prefix-free) - born at 21 findings: all 21 description cells abbreviated away the front-matter Title, and project_prereq_parity_check (PP-01..03) locks the projects fleet's supporting guides to their projects and their planning surface (each PREREQUISITES-NNN walkthrough's front-matter id matching its filename and its For-line resolving to a real project file, the target project linking back to its walkthrough, and MASTER-INDEX's Projects section linking every supporting guide in the directory) - born at 5 findings: PROJECT-001/007 never mentioned their own dedicated walkthroughs and none of the three supporting guides had a MASTER-INDEX row, and fleet_count_parity_check (FC-01..06) locks the count claims a learner plans from to disk (every MASTER-INDEX File Counts row against its documented disk definition with the TOTAL row to the category sum, the SITEMAP Experiments header to the experiments directory, and the README summary and per-group headers to a section that lists every EXP file in both directions) - born at 16 findings: the README summary said 46 against 47 on disk and 15 experiments were listed nowhere on the README surface, and sitemap_listing_parity_check (SL-01..04) locks the SITEMAP's listing identities to disk (fleet-section listing parity both directions across 19 fleets - every entry resolves to a fleet member and every fleet file is listed exactly once, corpus reachability for every docs markdown plus the root README, module lesson+guide arithmetic across the 33 phase modules, and SL-04 locking the self-explaining "(N files: A x + B y)" header decompositions to disk) - born census-proven clean at zero: count parity was already SC-locked, the identities behind the counts were not; SL-04 joined tick-561 when the MI-vs-SITEMAP census found 4 definitional divergences where each surface was true under its own definition (Notebooks 20 vs 21, Capstone Projects 7 vs 10, Experiments 47 vs 48, Meta Docs 20 vs 11) and the three bare SITEMAP headers drained to the self-explaining form so a future drift cannot hide behind a bare count; SL-05 joined tick-563 locking the count-header FORM itself - the census found 7 of the 29 counted headers carrying the bare "(N)" form (Tutorials, Labs, Lab Solutions, Cheat Sheets, Interactive, Troubleshooting, Case Studies) against the corpus convention SC's own docstring documents, all drained to "(N files)"/"(N file)" so every counted header a platform parser reads opens "(N files" (singular "(N file" at N==1, suffix free, numbers SC-locked), and assessment_lint grew AS-13 (tick-562) locking the MASTER-INDEX Phase Practice/Quiz Files tables' per-row count columns to the linked phase-level files (Exercise headings outside the appendix reference-implementations, numbered "### N." quiz questions) - born with the exercise column drifted on 5 of 7 phases, MI promising 42 exercises against a disk of 34 while the quiz column stood 7/7 true, and the column drained to disk truth before the lock tightened
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

[1.3.0]: https://github.com/your-org/project-omega/releases/tag/v1.3.0
[1.1.0]: https://github.com/your-org/project-omega/releases/tag/v1.1.0
[1.2.0]: https://github.com/your-org/project-omega/releases/tag/v1.2.0
[1.0.0]: https://github.com/your-org/project-omega/releases/tag/v1.0.0

---

## Version Summary

| Version | Date | Changes |
|---------|------|---------|
| **1.3.0** | 2026-10-02 | Live-verified content corrections (phases 2-6), execution census adjudication (582 → 556), quality infrastructure growth |
| **1.2.0** | 2026-09-30 | Curriculum modernization (uv, Python 3.13, LangChain), QA infrastructure |
| **1.1.0** | 2026-02-04 | Assessment system, labs, notebooks, projects, resources |
| **1.0.0** | 2026-01-XX | Initial release with core documentation |
