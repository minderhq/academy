---
Document ID: INDEX
Title: "Minder Academy"
Last Updated: 2026-10-27
Status: Complete
Difficulty: Beginner
Tags: ['maintenance', 'navigation']
---

# Minder Academy

An applied AI engineering curriculum organized into seven phases and
thirty-three modules - from GPU infrastructure and Kubernetes to transformer
internals, quantization, fine-tuning, retrieval, and agentic systems. The
curriculum includes explanations, code examples, diagrams, practice,
assessments, notebooks, and production-oriented guides. Automated checks keep
its structure, links, code syntax, and navigation consistent.

This site is the browsable form of the
[GitHub repository](https://github.com/minderhq/academy). Read here, run the
code locally - the paths below are ordered the way the curriculum teaches.

[Get Started in 30 Minutes](00-META/QUICK-START.md){ .md-button .md-button--primary }
[Follow the Roadmap](00-META/0000-LEARNING-PATH.md){ .md-button }

| Start with | What you get |
|------------|--------------|
| **[Get Running in 30 Minutes](00-META/QUICK-START.md)** | Install Ollama and try Qwen3.5 0.8B locally; no GPU required, with 8 GB RAM minimum and 16 GB+ recommended for headroom. |
| **[Follow the Week-by-Week Roadmap](00-META/0000-LEARNING-PATH.md)** | A 48-week route from Python fundamentals (Phase 0) through all seven phases to production agentic systems. |
| **[Track Your Progress](00-META/PROGRESS-TRACKER.md)** | Close every module with its practice set and quiz, then log the checkpoint so you always know where you stand. |
| **[Keep a Cheat Sheet Open](learning-resources/cheat-sheets/README.md)** | Eighty concise references, from command and concept sheets to one guide for each of the seven curriculum volumes. |
| **[Prepare for the Job Market](learning-resources/guides/GUIDE-CAREER.md)** | Career, interview, and resume guides that map the curriculum onto real AI engineering roles. |

## Start Here

- [QUICK-START](00-META/QUICK-START.md) - get running in 30 minutes
- [0000-LEARNING-PATH](00-META/0000-LEARNING-PATH.md) - the curriculum roadmap and study tracks
- [ENVIRONMENT-SETUP](00-META/ENVIRONMENT-SETUP.md) - hardware and software prerequisites
- [FAQ](00-META/FAQ.md) - frequently asked questions
- [GLOSSARY](00-META/GLOSSARY.md) - terminology reference

## The Seven Phases

| # | Phase | What it covers |
|---|-------|----------------|
| 1 | [Infrastructure Fabric](phases/phase1-infra/README.md) | Networks, virtualization, Kubernetes, LLMops, monitoring |
| 2 | [Cognitive Science & Frameworks](phases/phase2-foundations/README.md) | Math foundations, deep-learning frameworks, pretraining |
| 3 | [Transformer Physics & LLM Internals](phases/phase3-transformers/README.md) | Attention, embeddings, architectures, multimodal |
| 4 | [Quantization & Compression](phases/phase4-quantization/README.md) | Low-bit quantization, KV cache, QAT, advanced techniques |
| 5 | [Fine-Tuning & Alignment](phases/phase5-finetuning/README.md) | PEFT, alignment, synthetic data, distributed training |
| 6 | [Data Nexus - RAG, CAG & External Memory](phases/phase6-rag/README.md) | Vector retrieval, context engineering, serving pipelines |
| 7 | [Agentic Cognition & Autonomy](phases/phase7-agentic/README.md) | Agent architecture, tools, orchestration, memory, security |

## Beyond the Phases

The curriculum also ships as seven print-style volumes, each a curated route
through its phases:

- [VOLUME-1 - Infrastructure](volumes/VOLUME-1-Infrastructure.md)
- [VOLUME-2 - AI/ML Foundations](volumes/VOLUME-2-AI-Foundations.md)
- [VOLUME-3 - LLM Internals](volumes/VOLUME-3-LLM-Internals.md)
- [VOLUME-4 - Quantization](volumes/VOLUME-4-Quantization.md)
- [VOLUME-5 - Model Adaptation](volumes/VOLUME-5-Model-Adaptation.md)
- [VOLUME-6 - Data Nexus](volumes/VOLUME-6-Data-Nexus.md)
- [VOLUME-7 - Production Mastery](volumes/VOLUME-7-Production-Mastery.md)

## How to Work Through a Lesson

1. Read the module README first - it states prerequisites and the time budget.
2. Check a lesson's prerequisites before running its commands or examples.
   Some code fences are partial snippets or configuration samples rather than
   standalone programs; review commands that create, change, or delete
   resources before executing them. Treat shown output as a reference because
   versions, hardware, data, and model settings can change the result.
3. Close each module with its assessment: the practice set for hands-on work,
   the quiz for retrieval, and the checkpoint to log progress in
   [PROGRESS-TRACKER](00-META/PROGRESS-TRACKER.md).

## Where Everything Lives

The [SITEMAP](00-META/SITEMAP.md) enumerates every document in the corpus,
and the [MASTER-INDEX](00-META/MASTER-INDEX.md) is the full inventory with
per-fleet counts.
