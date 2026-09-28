---
Document ID: QA-TOOLING
Title: "PROJECT-OMEGA QA Tooling"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Beginner
---

# PROJECT-OMEGA QA Tooling

**The gate system that keeps the curriculum shippable**

---

## 🚀 One Command

```bash
python scripts/qa/quality_report.py
```

Prints the full scorecard: corpus stats (lesson files / modules /
phases) plus every gate below, then a single `result:` line. Exit 0
means all hard gates are clean - this is the CI contract.

Environment: `uv sync --group qa` installs the offline-gate
dependencies (PyYAML for the frontmatter/yaml parser gates, httpx for
the network link tool) as the PEP 735 `qa` dependency group in the
root `pyproject.toml` (see [ENVIRONMENT-SETUP](ENVIRONMENT-SETUP.md)).
One exception: langchain_census resolves every lesson import against
the kurulu-stack, so run the scorecard under an interpreter that has
the full installed stack. A partial environment fails loud with
`sys.exit(2)` and a named fix (never silently wrong findings).

---

## 🛡️ Hard Gates (exit 1 on findings)

| Gate | Codes | What it checks |
| --- | --- | --- |
| frontmatter_lint | FM-01..FM-09 | frontmatter completeness/consistency |
| pip_uv_scan | - | bare `pip install` only in documented exceptions (Docker, conda, uv bootstraps) |
| langchain_census | LC-01 | every langchain/langgraph import resolves against the installed stack |
| legacy_chain_scan | LC-02 | bare langchain_classic-only name uses (import-less usage) |
| codeblock_syntax_scan | CB-01 | every python fence parses as Python |
| bashblock_syntax_scan | BB-01 | every bash fence passes `bash -n`; runnable `${VAR}` placeholders |
| datablock_syntax_scan | DB-01/02 | json fences parse; yaml fences parse as document streams |
| assessment_lint | AS-01..AS-08 | QUIZ.md + PRACTICE.md coverage per module |
| quiz_export | - | quiz bank parses into complete question records |
| structure_lint | - | fence parity + H1 discipline corpus-wide |
| linkcheck | - | every relative link target exists on disk |
| casecheck | - | case-sensitive href/disk match (Windows-invisible breaks) |
| anchor_check | - | in-document AND cross-file anchors vs a GitHub-accurate slugger |
| table_lint | TL-01 | ragged GFM tables (differing cell counts) |
| mermaid_lint | MM-01..03 | diagram headers, balanced brackets, declared direction |
| deprecated_scan | DA-01..03 | deprecated API calls in python fences |
| kwarg_lint | KW-01/02 | removed/renamed kwargs on known APIs |
| typing_legacy_scan | TL-01 | legacy typing spellings (PEP 585/604) in python fences |

## 📋 Report Gates (exit 0 by design)

| Gate | What it reports |
| --- | --- |
| objectives_lint | template-objective artifacts (OL-01/OL-02) - the drain queue |
| fence_namecheck | names used in a python fence that no fence binds (NC-01); residual fragment idiom is accepted noise |
| fm_staleness | Last Updated age map (fresh/recent/stale/missing) - a stale date is a review queue, not a failure |

---

## 🌐 Network Tool (ad hoc, not in the scorecard)

```bash
python scripts/qa/link_rot_check.py
```

Probes every external http(s) URL (bare prose URLs included). Report
only - network probes are slow and flaky, so the scorecard stays
offline. Notable behavior: a 403 under the tool UA gets an automatic
second chance (browser UA over httpx, then curl - bot walls
fingerprint the TLS stack, not just the UA); placeholder idioms
(`your-username`, `your-org`, `yourapp.com`) are TEMPLATE, not rot;
`discord.gg` invites time out on some networks.

## 🗄️ Epic-Archive Tools (not gates)

| Tool | Purpose |
| --- | --- |
| brand_scan | verifies the pre-rebrand brand name is fully retired (rebrand epic) |
| legacy_ad_scan | classifies remaining old-repo-name mentions by context |
| legacy_ad_rename | mechanical renames used by the same epic |

## 🧾 Platform Feed (not a gate)

```bash
python scripts/qa/manifest_export.py             # JSON to stdout
python scripts/qa/manifest_export.py --out manifest.json
```

Exports the corpus as one deterministic JSON manifest for the future
platform: every doc under docs/ with its frontmatter metadata, plus the
phase/module/lesson hierarchy and per-module assessment flags. Paired
with quiz_export (the question bank), a platform load step never has to
re-parse markdown. Extraction models are borrowed, not reinvented
(quiz_export's frontmatter parser; quality_report's corpus
classification), so the manifest's lesson count always equals the
scorecard's corpus line.

## 📊 Curriculum Metrics (report tool)

```bash
python scripts/qa/curriculum_metrics.py
```

Answers "how good is the teaching material?" with numbers: lesson
content-word distribution (prose + code - code-heavy lessons that put
a full implementation in one fence are dense, not thin), python/bash
fence density, H2/link structure, and quiz coverage per module
(33/33, 660 questions). Report only - the thinnest-lessons list is a
content-pass review queue, not a failure (same stance as
fm_staleness). The sparse-modules (<3 lessons) line shows unit
content next to the count - a 2-lesson focused unit can carry a full
module, so the count alone is never a verdict. Models borrowed for
parity: the corpus classification from quality_report, the fence
model from structure_lint, quiz counts from quiz_export.

## 📐 Conventions

- All gates share one extraction model: naive fence toggle +
  inline-code scrub. The model never changes for one tool - gate
  parity is the contract. Indented (4-space) code blocks are inside
  the model by design; teach content accordingly.
- Scan scope is corpus files only: the tree walk skips virtualenvs
  and tool dirs (`.venv`, `venv`, `.claude`, `node_modules`,
  `__pycache__`, `.git`). A fresh `uv sync` would otherwise leak
  installed package markdown (LICENSE files) into the link gates
  and shift the baselines per machine.
- The scorecard output is the living baseline: any gate going
  non-clean is a regression, and new gates enter through
  `quality_report.py`'s GATES list.
