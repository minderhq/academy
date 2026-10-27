---
Document ID: README
Title: "Minder Academy"
Last Updated: 2026-10-27
Status: Complete
Difficulty: Beginner
---

<div align="center">

![Minder Academy](https://img.shields.io/badge/Minder--Academy-AI%20Engineering%20Education-blue?style=for-the-badge&logo=ai&logoColor=white)

# Minder Academy

**A practical, self-paced curriculum for AI engineering, from infrastructure and ML foundations to production LLM and agent systems.**

[![Read the curriculum](https://img.shields.io/badge/Read_the_curriculum-online-8A2BE2?style=for-the-badge)](https://minderhq.github.io/academy/)
[![Quick start](https://img.shields.io/badge/Quick_start-30_minutes-green?style=for-the-badge)](https://minderhq.github.io/academy/00-META/QUICK-START/)
[![Documentation](https://img.shields.io/badge/Docs-520%20Files-orange?style=flat-square)](https://minderhq.github.io/academy/00-META/MASTER-INDEX/)
[![Phases](https://img.shields.io/badge/Phases-7-purple?style=flat-square)](#curriculum)
[![Modules](https://img.shields.io/badge/Modules-33-success?style=flat-square)](https://minderhq.github.io/academy/00-META/MASTER-INDEX/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

Minder Academy combines **7 phases, 33 technical modules, 520 Markdown lessons and references, and 20 executable notebooks**. Study the sequence, jump directly to a topic, or use the hands-on labs and projects to build along. Lessons are designed for local hardware and cloud environments.

## Choose a starting point

| If you want to… | Start here |
|---|---|
| Run a local model and try your first prompt | [Quick Start](https://minderhq.github.io/academy/00-META/QUICK-START/) · [hardware and environment setup](https://minderhq.github.io/academy/00-META/ENVIRONMENT-SETUP/) |
| Follow a structured study plan | [Learning Path](https://minderhq.github.io/academy/00-META/0000-LEARNING-PATH/) · [detailed learning tracks](https://minderhq.github.io/academy/00-META/LEARNING-PATHS-DETAILED/) |
| Find a specific lesson or module | [Master Index](https://minderhq.github.io/academy/00-META/MASTER-INDEX/) · [search the online curriculum](https://minderhq.github.io/academy/) |
| Practice with guided projects | [Labs](https://minderhq.github.io/academy/learning-resources/labs/) · [Projects](https://minderhq.github.io/academy/learning-resources/projects/) · [Notebooks](https://minderhq.github.io/academy/notebooks/) |
| Review a concept quickly | [Cheat sheets](https://minderhq.github.io/academy/learning-resources/cheat-sheets/) · [Glossary](https://minderhq.github.io/academy/00-META/GLOSSARY/) |
| Maintain or contribute to the repository | [Organization Guide](https://minderhq.github.io/academy/00-META/ORGANIZATION-GUIDE/) · [QA Tooling](https://minderhq.github.io/academy/00-META/QA-TOOLING/) · [GitHub issues](https://github.com/minderhq/academy/issues) |

## Curriculum

| Phase | Focus |
|---|---|
| [1 · Infrastructure](https://minderhq.github.io/academy/phases/phase1-infra/) | Networking, virtualization, Kubernetes, serving, and monitoring |
| [2 · Foundations](https://minderhq.github.io/academy/phases/phase2-foundations/) | Mathematics, ML frameworks, and pretraining |
| [3 · Transformers](https://minderhq.github.io/academy/phases/phase3-transformers/) | Attention, tokenization, model architectures, and multimodal systems |
| [4 · Quantization](https://minderhq.github.io/academy/phases/phase4-quantization/) | Low-bit formats, inference memory, and compression |
| [5 · Fine-tuning](https://minderhq.github.io/academy/phases/phase5-finetuning/) | PEFT, alignment, synthetic data, and distributed training |
| [6 · Retrieval and data](https://minderhq.github.io/academy/phases/phase6-rag/) | Search, vector databases, context, and RAG pipelines |
| [7 · Agentic systems](https://minderhq.github.io/academy/phases/phase7-agentic/) | Tools, orchestration, memory, evaluation, and security |

Each phase has module overviews and assessments. Start with a module overview to check prerequisites and effort, then use its lessons, practice, and quiz. You can also follow the [seven-volume reading route](https://minderhq.github.io/academy/volumes/).

## Experiments

**🔬 47 Experiment Files** — browse the [complete experiment listing, grouped by phase](https://github.com/minderhq/academy/blob/main/README-REFERENCE.md#experiments).

## Repository layout

```text
docs/                 Curriculum, guides, assessments, and notebooks
experiments/          Reproducible infrastructure and model experiments
configs/              Reference deployment and performance configurations
scripts/qa/           Documentation and repository quality gates
mkdocs.yml            Online documentation navigation and theme
hooks.py              Build-time site and accessibility adjustments
```

The course content is readable online and in Markdown. To work from a local checkout:

```bash
git clone https://github.com/minderhq/academy.git
cd academy
```

Then follow the [Quick Start](https://minderhq.github.io/academy/00-META/QUICK-START/) for a local model, or browse `docs/` for the lesson sources. The reference deployment configurations are documented in [`configs/README.md`](https://github.com/minderhq/academy/blob/main/configs/README.md).

## Contributing

Corrections and improvements are welcome. Review the [documentation style guide](https://minderhq.github.io/academy/00-META/STYLE-GUIDE/), open an [issue](https://github.com/minderhq/academy/issues), or submit a pull request. The QA workflow runs the content, link, code-block, and structure checks on each pull request.

To preview or strictly validate the documentation site locally, install the
locked documentation tools from the repository root:

```bash
uv sync --group docs
uv run python -m mkdocs serve
uv run python -m mkdocs build --strict
```

The docs group installs the repo-local `gh_slugify.py` helper into the
environment, so both the MkDocs command and Python module invocation can load
the GitHub-compatible Markdown heading anchors.

## Full repository reference

The [full repository reference](README-REFERENCE.md) retains the detailed architecture notes, phase tables, deployment examples, benchmarks, troubleshooting guidance, and other long-form material from the former root README.

## License

Minder Academy is released under the [MIT License](LICENSE).
