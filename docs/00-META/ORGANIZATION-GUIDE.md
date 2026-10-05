---
Document ID: ORGANIZATION-GUIDE
Title: "Minder Academy Organization Guide"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Tags: ['maintenance', 'navigation']
---

# Minder Academy Organization Guide
## Documentation Structure & Maintenance

**Version:** 4.2
**Last Updated:** 2026-09-30
**Purpose:** Guide for understanding and maintaining the Minder Academy documentation structure

---

## Directory Structure

### Root Level

```text
Minder Academy/
├── README.md                          # Main project README
├── LICENSE                            # MIT License
├── prompt.txt                         # AI assistant prompt
├── configs/                           # Configuration files
│   ├── docker-compose.yml
│   ├── .env.example
│   └── performance-testing/k6/
├── docs/                              # All documentation (410 files)
│   ├── 00-META/                      # Meta documentation
│   ├── phases/                       # Phase documentation (33 modules)
│   ├── learning-resources/           # Learning materials
│   ├── experiments/                  # Experiment files (47)
│   ├── comparisons/                  # Comparison docs
│   ├── use-cases/                    # Use case docs
│   ├── industry/                     # Industry applications
│   ├── solutions/                    # Solution docs
│   └── diagrams/                     # Architecture diagrams
├── experiments/                       # Experiment implementations
└── scripts/                          # Utility scripts
```

---

## Documentation Structure

### 00-META: Meta Documentation

**Purpose:** Project-level documentation and guides

```text
docs/00-META/
├── MASTER-INDEX.md                   # ← Start here! Complete navigation
├── QUICK-START.md                    # 5-minute setup guide
├── VOLUME-GUIDE.md                   # 7-volume curriculum
├── 0000-LEARNING-PATH.md             # Learning path selection
├── LEARNING-PATHS-DETAILED.md        # Detailed track guidance
├── PROGRESS-TRACKER.md               # Progress tracking
├── PROGRESS-CHECKPOINTS.md           # Milestone checkpoints
├── ASSESSMENT-GUIDE.md               # Skill evaluation
├── ENVIRONMENT-SETUP.md              # System requirements
├── FAQ.md                            # Common questions
├── GLOSSARY.md                       # Term definitions
├── SITEMAP.md                        # Complete file listing
├── TROUBLESHOOTING-QUICKSTART.md     # Quick issue resolution
├── learning-resources/
│   ├── interactive/                  # Interactive features
│   │   └── FLASHCARDS.md
│   └── resources/
│       └── EXTERNAL-RESOURCES.md
│
├── assessment/                       # Phase-level assessments
│   ├── phase1-practice.md            # Practice exercises
│   ├── phase1-quiz.md                # Quiz questions
│   ├── phase2-practice.md
│   ├── phase2-quiz.md
│   ├── ...
│   └── phase7-quiz.md
│
├── PRINTING-GUIDE.md                 # Book production guide
├── BOOK-OUTLINE.md                   # Book content outline
├── PRINTING-CHECKLIST.md             # Printing decisions
│
├── STYLE-GUIDE.md                    # Documentation standards
├── DOCUMENT-TEMPLATE.md              # File template
├── NAVIGATION-TEMPLATE.md            # Navigation patterns
├── CROSS-REFERENCE-GUIDELINES.md     # Linking standards
└── METADATA-MIGRATION-TOOL.md       # Migration utilities
```

---

### phases/: Phase Documentation

**Purpose:** Core technical content organized by learning phase

```text
docs/phases/
├── phase1-infra/                     # Phase 1: Infrastructure [1000]
│   ├── 1100-network/                 # Module 1100
│   │   ├── README.md                 # Module overview
│   │   ├── 1101-Fiber-GPON-Modem.md
│   │   ├── 1102-Star-Topology-Core.md
│   │   ├── 1103-Jumbo-Frames-and-MTU.md
│   │   └── assessment/
│   │       ├── PRACTICE.md           # Module practice
│   │       └── QUIZ.md               # Module quiz
│   ├── 1200-virtualization/
│   ├── 1300-kubernetes/
│   ├── 1400-llmops/
│   └── 1500-monitoring/
│
├── phase2-foundations/                # Phase 2: Foundations [2000]
│   ├── 2100-calculus/
│   ├── 2200-frameworks/
│   ├── 2300-framework-engineering/
│   └── 2400-pretraining/
│
├── phase3-transformers/              # Phase 3: Transformers [3000]
│   ├── 3100-attention/
│   ├── 3200-embeddings/
│   ├── 3300-decoding/
│   ├── 3400-architectures/
│   └── 3500-multimodal/
│
├── phase4-quantization/              # Phase 4: Quantization [4000]
│   ├── 4100-low-bit/
│   ├── 4200-kv-cache/
│   ├── 4300-quantization-aware-training/
│   └── 4400-advanced-techniques/
│
├── phase5-finetuning/                # Phase 5: Fine-Tuning [5000]
│   ├── 5100-peft/
│   ├── 5200-alignment/
│   ├── 5300-synthetic/
│   ├── 5400-distributed-training/
│   └── 5500-advanced-optimization/
│
├── phase6-rag/                       # Phase 6: Data Nexus [6000]
│   ├── 6100-vector/
│   ├── 6200-retrieval/
│   ├── 6300-context/
│   ├── 6400-vector-databases/
│   └── 6500-mlops-pipelines/
│
└── phase7-agentic/                   # Phase 7: Agentic Systems [7000]
    ├── 7100-architecture/
    ├── 7200-tools/
    ├── 7300-orchestration/
    ├── 7400-memory/
    └── 7500-security/
```

---

### learning-resources/: Learning Materials

**Purpose:** Hands-on learning content

```text
docs/learning-resources/
├── tutorials/                        # 15 tutorial files
│   ├── TUTORIAL-001-Hello-LLM.md
│   ├── TUTORIAL-002-Docker-Essentials.md
│   ├── TUTORIAL-003-RAG-Basics.md
│   ├── ...
│   └── TUTORIAL-013-AI-Security.md
│
├── labs/                             # 15 lab files
│   ├── LAB-000-ENVIRONMENT-SETUP.md
│   ├── LAB-001-Docker-LLM.md
│   ├── LAB-002-RAG-Implementation.md
│   ├── ...
│   └── LAB-014-AI-Evaluation-Safety.md
│
├── labs/solutions/                   # 15 solution files
│   ├── SOLUTION-LAB-000-Environment-Setup.md
│   ├── SOLUTION-LAB-001-Docker-LLM.md
│   └── ...
│
├── cheat-sheets/                     # 13 cheat sheets
│   ├── CHEAT-SHEET-001-Docker.md
│   ├── CHEAT-SHEET-002-Python-AI.md
│   ├── CHEAT-SHEET-003-Git.md
│   ├── CHEAT-SHEET-004-Linux.md
│   ├── CHEAT-SHEET-005-RAG-Systems.md
│   ├── QUICK-REF-VOLUME-1.md
│   ├── ...
│   └── QUICK-REF-VOLUME-7.md
│
├── projects/                         # 7 capstone projects
│   ├── PREREQUISITES-001.md
│   ├── PROJECT-001-AI-Assistant.md
│   ├── PROJECT-002-Train-Neural-Network.md
│   ├── ...
│   ├── PROJECT-007-Production-AI-System.md
│   └── SETUP-GUIDE.md
│
├── bridges/                          # Phase transition guides
├── case-studies/                     # Real-world examples
└── troubleshooting/                  # Issue resolution guides
```

---

## Numbering System

### Module Numbering

```text
[Phase][Module][Sub-module]

Examples:
1100 → Phase 1, Module 1, Sub-module 00
2102 → Phase 2, Module 1, Sub-module 02
6303 → Phase 6, Module 3, Sub-module 03
```

### File Numbering

| Type | Pattern | Example |
|------|---------|---------|
| **Tutorial** | TUTORIAL-XXX | TUTORIAL-001-Hello-LLM.md |
| **Lab** | LAB-XXX | LAB-001-Docker-LLM.md |
| **Cheat Sheet** | CHEAT-SHEET-XXX | CHEAT-SHEET-001-Docker.md |
| **Project** | PROJECT-XXX | PROJECT-001-AI-Assistant.md |
| **Practice** | phaseX-practice.md | phase1-practice.md |
| **Quiz** | phaseX-quiz.md | phase1-quiz.md |

---

## File Naming Conventions

### Standard Naming

| Content Type | Convention | Example |
|--------------|------------|---------|
| **Module README** | README.md | phases/phase1/1100/README.md |
| **Module Content** | [Module-ID]-[Topic].md | 1101-Fiber-GPON-Modem.md |
| **Tutorials** | TUTORIAL-XXX-[Topic].md | TUTORIAL-001-Hello-LLM.md |
| **Labs** | LAB-XXX-[Topic].md | LAB-001-Docker-LLM.md |
| **Solutions** | SOLUTION-LAB-XXX-[Topic].md | SOLUTION-LAB-001-Docker-LLM.md |
| **Practice** | phaseX-practice.md | phase1-practice.md |
| **Quiz** | phaseX-quiz.md | phase1-quiz.md |
| **Cheat Sheets** | CHEAT-SHEET-XXX-[Topic].md | CHEAT-SHEET-001-Docker.md |
| **Quick Ref** | QUICK-REF-VOLUME-X.md | QUICK-REF-VOLUME-1.md |

### Forbidden Patterns

- ❌ Spaces in filenames
- ❌ Special characters (&, %, #, etc.)
- ❌ Mixed separators (use hyphens only)
- ❌ All caps (except acronyms)
- ❌ Inconsistent capitalization

---

## Cross-Reference System

### Internal Links

```markdown
<!-- Link to phase README -->
[Phase 1](../phases/phase1-infra/README.md)

<!-- Link to specific module -->
[Network Module](../phases/phase1-infra/1100-network/README.md)

<!-- Link to tutorial -->
[TUTORIAL-001](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)

<!-- Link to practice -->
[Phase 1 Practice](../00-META/assessment/phase1-practice.md)

<!-- Link to glossary term -->
[Vector Database](../00-META/GLOSSARY.md#vector-database)
```

### External Links

```markdown
<!-- Official documentation -->
[Qdrant Docs](https://qdrant.tech/documentation/)

<!-- Research papers -->
[Attention Is All You Need](https://arxiv.org/abs/1706.03762)

<!-- GitHub repositories -->
[vLLM](https://github.com/vllm-project/vllm)
```

---

## Document Templates

### Module README Template

Every document opens with a YAML front-matter block (see
[Front Matter Standard](#quality-standards)). The `Tags:` field is
mandatory and must follow the canonical quoted-list syntax - both are
QA-gate-enforced (see `docs/00-META/QA-TOOLING.md`).

```markdown
---
Document ID: [MODULE-ID]
Title: "[Module Name]"
Last Updated: YYYY-MM-DD
Status: Complete
Difficulty: Beginner
Tags: ['tag-one', 'tag-two']
---

# [Module ID]: [Module Name]

## Overview

[Brief description of what this module covers]

**Duration:** X hours
**Difficulty:** ⭐ Beginner
**Prerequisites:** [List prerequisites]

---

## Learning Objectives

After this module, you will:
- [Objective 1]
- [Objective 2]
- [Objective 3]

---

## Topics Covered

| Topic | Docs | Status |
|-------|------:|:------:|
| [Topic 1] | 2 | ✅ |
| [Topic 2] | 3 | ✅ |

---

## Resources

- [Related Tutorial](../../learning-resources/tutorials/TUTORIAL-XXX.md)
- [Practice Exercises](../../00-META/assessment/phaseX-practice.md)
- [Next Module](../[next-module]/README.md)

---

**Last Updated:** YYYY-MM-DD
```

### Tutorial Template

```markdown
---
Document ID: TUTORIAL-XXX
Title: "[Tutorial Title]"
Last Updated: YYYY-MM-DD
Status: Complete
Difficulty: Beginner
Tags: ['tag-one', 'tag-two']
---

# TUTORIAL-XXX: [Title]

## Overview

[Brief description]

**Duration:** X hours
**Difficulty:** Beginner/Intermediate/Advanced
**Prerequisites:** TUTORIAL-XXX or [other]

---

## Learning Objectives

After this tutorial, you will:
- [Objective 1]
- [Objective 2]

---

## Part 1: [Title]

### Content

[Explanation, code examples, diagrams]

---

## Exercises

1. [Exercise 1]
2. [Exercise 2]

---

## Completion Checklist

- [ ] Task 1
- [ ] Task 2

---

**Next Steps:** LAB-XXX or [other]

**Last Updated:** YYYY-MM-DD
```

---

## Quality Standards

### Content Requirements

Every document must include:

1. **Header Section**
   - Title with ID (if applicable)
   - Overview/Description
   - Duration (for tutorials/labs)
   - Difficulty level
   - Prerequisites

2. **Learning Objectives**
   - Clear, measurable goals
   - 3-5 objectives per document

3. **Structure**
   - Table of Contents (for long docs)
   - Numbered sections
   - Code examples with syntax highlighting
   - Diagrams where appropriate

4. **Navigation**
   - Links to related content
   - Next steps/continuation links
   - Back to parent/index

5. **Metadata** (YAML front matter - see Front Matter Standard below)
   - Document ID, Title, Last Updated (ISO `YYYY-MM-DD`)
   - Status, Difficulty, Tags (canonical quoted-list syntax)

### Front Matter Standard

Every document in `docs/` opens with a YAML front-matter block. The
QA suite hard-gates each field, so a document that skips the block
does not pass `quality_report.py`:

| Field | Rule | Enforced by |
|-------|------|-------------|
| `Document ID` | stable unique slug, matches filename | doc-id / title gates |
| `Title` | quoted string, unique across corpus | title gate |
| `Last Updated` | ISO `YYYY-MM-DD`; bump on every real edit | LU-01/LU-02 |
| `Status` | one of the corpus statuses | status gate |
| `Difficulty` | Beginner / Intermediate / Advanced | difficulty gate |
| `Tags` | `Tags: ['tag-one', 'tag-two']` - bracketed, comma-space, single-quoted, non-empty, unique | TG-01..03, TS-01 |

Tag tokens come from the controlled vocabulary maintained by
`tag_vocabulary_census.py` (TV-01); extending it is a deliberate
script edit, not a free-form choice. The `Last Updated` field also
drives the freshness work queue: `python scripts/qa/date_cohort.py
--root . --since YYYY-MM` lists every doc last touched before that
month. A date is a freshness signal, not a score - bump it only when
content actually changed.

### Style Guidelines

| Element | Standard |
|---------|----------|
| **Headings** | Title Case, # for H1, ## for H2 |
| **Code Blocks** | Specified language (```python) |
| **Emphasis** | **Bold** for key terms, *italic* for secondary |
| **Lists** | Numbered for ordered, bulleted for unordered |
| **Tables** | With headers, aligned content |
| **Links** | Descriptive text, not raw URLs |
| **Diagrams** | Mermaid format preferred |

---

## Maintenance Procedures

### Adding New Content

1. **Determine document type**
   - Module documentation → `phases/phasex/modules/`
   - Tutorial → `learning-resources/tutorials/`
   - Lab → `learning-resources/labs/`
   - Reference → `00-META/`

2. **Follow naming conventions**
   - Use established numbering system
   - Follow file naming standards

3. **Use templates**
   - Select appropriate template
   - Fill in all required sections

4. **Add cross-references**
   - Link from parent documents
   - Link to related content
   - Update index files

5. **Update metadata**
   - Add to SITEMAP.md
   - Update file counts
   - Update MASTER-INDEX.md

### Updating Existing Content

1. **Check dependencies**
   - What links to this document?
   - What documents does this link to?

2. **Make changes**
   - Edit content
   - Update cross-references if needed

3. **Update metadata**
   - Update "Last Updated" date
   - Update version if major changes

4. **Test links**
   - Verify all internal links work
   - Verify all external links work

### Removing Content

1. **Check dependencies**
   - Find all inbound links
   - Update or remove references

2. **Archive if needed**
   - Move to `archive/` directory
   - Add deprecation notice

3. **Update indexes**
   - Remove from SITEMAP.md
   - Update MASTER-INDEX.md
   - Update file counts

---

## File Audit Checklist

### Monthly Audit Tasks

- [ ] Verify all internal links work
- [ ] Check for broken external links
- [ ] Update file counts in MASTER-INDEX
- [ ] Review recent changes for consistency
- [ ] Update LAST_UPDATED dates where needed
- [ ] Check for orphaned files
- [ ] Verify code examples still work
- [ ] Update deprecated commands
- [ ] Review and update cross-references
- [ ] Archive outdated content

### Quarterly Audit Tasks

- [ ] Review entire documentation structure
- [ ] Identify gaps in content coverage
- [ ] Gather user feedback
- [ ] Plan new content additions
- [ ] Review and update templates
- [ ] Analyze usage metrics
- [ ] Update quality standards
- [ ] Review accessibility compliance
- [ ] Plan reorganization if needed
- [ ] Update style guide

---

## Automation Tools

### QA Gate Suite

The repo's structural quality is enforced by
`scripts/qa/quality_report.py`, which runs the registered gate
scripts (currently 71 - see `docs/00-META/QA-TOOLING.md` for the
full inventory). Hard gates exit non-zero on findings; the report
ends with an authoritative `result: PASS/FAIL` line.

```bash
# full structural review (all gates)
python scripts/qa/quality_report.py --root .

# single gate, e.g. relative-link integrity
python scripts/qa/linkcheck.py --root .
```

### Freshness Queue

`scripts/qa/date_cohort.py` groups every dated doc by its `Last
Updated` month, oldest cohort first - the review surface for "which
content has not been touched longest":

```bash
# cohorts overview
python scripts/qa/date_cohort.py --root .

# docs last updated BEFORE 2026-03
python scripts/qa/date_cohort.py --root . --since 2026-03
```

It is a listing tool, not a gate: it says WHERE to look, the
content gates say WHAT is wrong.

### File Counter

```bash
# Count markdown files by directory
for dir in docs/*/; do
  echo "$dir: $(find "$dir" -name "*.md" | wc -l)"
done
```

### Sitemap Generator

```python
import os
from pathlib import Path

def generate_sitemap():
    """Generate sitemap from docs directory."""
    docs_path = Path("docs")
    markdown_files = docs_path.rglob("*.md")

    with open("SITEMAP.md", "w", encoding="utf-8") as f:
        f.write("# SITEMAP\n\n")
        for file in sorted(markdown_files):
            rel_path = file.relative_to(docs_path)
            f.write(f"- [{rel_path}]({rel_path})\n")

if __name__ == "__main__":
    generate_sitemap()
```

---

## Growth Metrics

### Tracking Documentation Growth

| Month | Files | Lines | Words | Pages |
|-------|-----:|------:|------:|------:|
| **Jan 2026** | 320 | 75,000 | 1.8M | 3,000 |
| **Feb 2026** | 462 | 100,926 | 2.5M | 4,060 |

### Content Distribution

| Category | Files | Percentage |
|----------|-----:|----------:|
| Phase Docs | 111 | 24% |
| Learning Resources | 57 | 12% |
| Experiments | 44 | 10% |
| Meta Docs | 30 | 6% |
| Reference | 220 | 48% |

---

## Best Practices

### For Writers

1. **Start with templates** - Use provided templates
2. **Write clearly** - Short sentences, active voice
3. **Provide examples** - Code, commands, diagrams
4. **Test everything** - Verify instructions work
5. **Get reviews** - Have others review your content
6. **Update regularly** - Keep content current

### For Maintainers

1. **Monitor links** - Check for broken links regularly
2. **Track issues** - Document known issues
3. **Plan updates** - Schedule regular reviews
4. **Gather feedback** - Collect user input
5. **Version control** - Use Git for all changes
6. **Backup regularly** - Keep copies of important docs

---

## Support

### Questions?

- **Documentation:** [MASTER-INDEX.md](MASTER-INDEX.md)
- **Style:** [STYLE-GUIDE.md](STYLE-GUIDE.md)
- **Templates:** [DOCUMENT-TEMPLATE.md](DOCUMENT-TEMPLATE.md)
- **Issues:** GitHub Issues

### Contributing

See [STYLE-GUIDE.md](STYLE-GUIDE.md) for contribution guidelines.

---
