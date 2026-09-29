---
Document ID: QA-TOOLING
Title: "PROJECT-OMEGA QA Tooling"
Last Updated: 2026-09-29
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
| pip_uv_scan | - | bare `pip install` only in documented exceptions (Docker, conda, uv bootstraps, uv-first blocks with a labeled plain-pip fallback) |
| langchain_census | LC-01 | every langchain/langgraph import resolves against the installed stack |
| legacy_chain_scan | LC-02 | bare langchain_classic-only name uses (import-less usage) |
| codeblock_syntax_scan | CB-01 | every python fence parses as Python |
| bashblock_syntax_scan | BB-01 | every bash fence passes `bash -n`; runnable `${VAR}` placeholders |
| datablock_syntax_scan | DB-01/02 | json fences parse; yaml fences parse as document streams |
| assessment_lint | AS-01..AS-08 | QUIZ.md + PRACTICE.md coverage per module |
| quiz_export | - | quiz bank parses into complete question records |
| quiz_integrity_scan | QI-01..05, QI-08/09 | content-level quiz integrity on top of quiz_export's parser: self-referential positional option ("Both A and B" at position B), duplicate stem within a module, duplicate option text within a question, option letter beyond A-D (the parser silently drops it), numbering gap (duplicate numbers were flagged, missing ones were not), duplicate Answer Key rows for one question (the key dict overwrites, last row silently wins), orphan Answer Key rows with no matching question (quiz_export's join is one-directional: questions pull from the key, key rows are never checked back); QI-06/QI-07 lines are report inventory - accepted cross-module stem dups and the skewed-answer-key shuffle queue (max letter ≥50% or a letter absent; refines AS-09's 70% tripwire); born from the tick-284 census that found 2 self-reference bugs (fixed at birth), QI-08/09 from the tick-285 census (0/0 across 33 modules - locked at birth), baseline 0 |
| structure_lint | - | fence parity + H1 discipline + heading level jumps (HJ-01: no heading dives more than one level below the previous one, so the document outline stays monotone for TOC renderers, screen readers and platform nav trees) corpus-wide |
| linkcheck | - | every relative link target exists on disk |
| casecheck | - | case-sensitive href/disk match (Windows-invisible breaks) |
| anchor_check | - | in-document AND cross-file anchors vs a GitHub-accurate slugger |
| table_lint | TL-01 | ragged GFM tables (differing cell counts) |
| mermaid_lint | MM-01..03 | diagram headers, balanced brackets, declared direction |
| deprecated_scan | DA-01..03 | deprecated API calls in python fences |
| kwarg_lint | KW-01/02 | removed/renamed kwargs on known APIs |
| typing_legacy_scan | TL-01 | legacy typing spellings (PEP 585/604) in python fences |
| version_alignment_scan | VA-01..04 | code-side python-version drift in any fence: `FROM python:X.Y`, `python3.X` binaries, `--python X.Y` flags, `uv python install/pin` - the corpus standard is 3.13 |
| feed_parity_check | FP-00..06 | cross-feed contract between the platform feeds: runs manifest_export + quiz_export for real and locks module sets, counts-vs-arrays, hierarchy-vs-documents lessons, quiz-file membership, bank-internal totals, and assessment.quiz flag parity (consistency only - content totals stay the living baseline) |
| readme_claims_check | RC-00/01 | every measurable number in README.md (badges, resource tables, per-phase document table, footer) vs its disk measurement; regex-matched claims, an unmatched pattern is skipped on purpose (change the README copy -> teach the new pattern, don't let the gate rot) |
| sitemap_claims_check | SC-00/01 | every measurable number in SITEMAP.md: section headers vs disk, headers vs their own list entries (inline prose links are not entries), and the fenced Statistics block - same regex-claim idiom as readme_claims_check |
| meta_claims_check | MC-00/01 | every measurable number in the remaining entry docs: FAQ.md intro sentence, MASTER-INDEX.md (Total Files, per-phase Status rows, numbered section headers, lab header 3-way split, File Counts block incl. TOTAL as its own sum, module-table "N docs" cells = lesson files), ORGANIZATION-GUIDE.md tree labels, VOLUME-GUIDE.md (tree labels, labs 2-way split, SITEMAP line, Total Documents footer) and PROGRESS-TRACKER.md (per-volume bars + headers, Total bar, SITEMAP line, stats-table targets; bar percent/fill are learner state, only targets are locked) - same regex-claim idiom |
| lab_registry_check | LB-01/02, LR-01 | every `LAB-0NN: Topic` label corpus-wide vs the labs' own frontmatter Titles: wrong lab identity (topic belongs to a different lab than labelled), unknown/ambiguous topic (teach the signal table or fix the label), lab id with no file on disk - word-based matching so legitimate short forms ("Docker & LLM" for "Docker & LLM Fundamentals") and verb-form bridges ("Add knowledge graphs") pass; labels carry identities not numbers, which is why the claims gates can't see this class |
| resource_id_check | RI-01/02 | numbered-resource id identity across the 43 resources (LAB-000..014, PROJECT-001..007, TUTORIAL-000..014, CHEAT-SHEET-001..006): every resource's frontmatter Title and first H1 carries the filename's own `FAMILY-0NN:` id, and the pre-campaign spaced spellings (`LAB 0NN`, `CHEAT SHEET 0NN` - any case, real digits) are banned corpus-wide; born from the 2026-09-29 canonicalization campaign that unified every occurrence to the dashed form - lab_registry_check locks what each id points at, this gate locks the id itself |
| unfinished_marker_scan | UM-01 | unfinished-content markers in prose: `coming soon`, `under construction`, `to be written`, `to be added`, `work in progress`, shouted `TODO`/`TBD`/`FIXME` - checked outside code fences with inline code scrubbed, so fenced starter-code `# TODO:` exercise prompts (the codified notebooks/README.md convention) stay invisible by design and blockquote-prefixed fences still toggle; born from the tick-276 census whose 108 raw matches all landed in legitimate classes (the lock keeps it that way at baseline 0) |
| empty_section_scan | ES-01 | every heading owns content: a section is empty iff nothing but blanks, HRs, blockquote markers and HTML comments sits between its heading and the next same-or-higher-level heading (or EOF) - a filled child fills its parent, so `## Questions` + `### 1.` containers are legitimate. Fence model is structure_lint's length-aware one (a bare closing fence at least as long as its opening run), so 3-backtick examples inside the 4-backtick super-fences cannot mis-toggle and surface fence-interior heading lookalikes; born from the tick-277 census whose 8 findings were all same-level children under container headings (`## Part 1` + `## 1.1`) - fixed by re-leveling 123 headings across 3 files, baseline 0 |
| emoji_shortcode_scan | EM-01 | gemoji shortcodes (`:rocket:` form) banned in prose: the corpus idiom is literal emoji (census: literal dominates by orders of magnitude across 173 files) and a platform load step would need a shortcode table while literals render everywhere; inline code is scrubbed, so technical lookalikes (`:memory:` SQLite URI, `:server:` K3s token - both fence-interior anyway) stay invisible; born from the tick-279 census that found 82 shortcodes in 11 files including the invalid `:star3:` rendering as raw text on GitHub - normalized to literal emoji, baseline 0 |
| fence_label_scan | FL-01/02 | fence info-strings must be lowercase and present: code gates key on the exact lowercase label, so a `Python` case variant or a bare unlabeled open is code every gate silently skips (an audit hole, not a style nit); every fence carries an honest label - `text` is always legitimate for prose dumps; born from the tick-280 census (4243 open fences, 21 distinct labels, already all lowercase and labeled), baseline 0 |
| setext_scan | SE-01..03 | divider and setext hygiene: an underline run (`---`/`===`) directly below a non-blank line is a setext heading in every renderer - invisible to the ATX-only outline gates, so the silent heading escapes the TOC and platform nav tree; bare `===` renders as literal text (never a thematic break), and the divider idiom is `---` exclusively (census: 3008 of 3008); born from the tick-281 census that found 7 doubled dividers - one copy-paste artifact of the footer-nav template across 7 files, fixed by deleting the duplicate line, baseline 0 |
| title_h1_parity_scan | TH-01..03 | frontmatter Title == first ATX H1: manifest_export takes the platform nav label from Title, the rendered page title is the first H1, so drift means the nav tree names a different page than the one that opens; fix is Title := H1 verbatim; born from the tick-283 census (89 lesson docs where the `NNNN: ` id prefix lived only in the H1), baseline 0 |

## 📋 Report Gates (exit 0 by design)

| Gate | What it reports |
| --- | --- |
| objectives_lint | template-objective artifacts (OL-01/OL-02) - the drain queue |
| fence_namecheck | unbound names in python fences, two codes: NC-01 module access without import (`name.attr` on a known module no fence imports - certain NameError, the gate's signal) and NC-02 fragment idiom (accepted teaching texture: usage-before-setup sketches, agent-UI placeholders, pseudo-code) |
| duplicate_heading_scan | duplicate heading texts per file (DH-01) - GitHub suffixes the slugs and binds explicit anchors to the first heading, so a platform TOC/nav generator needs this inventory to suffix deterministically, and a new duplicate outside the accepted idiom lands here as the copy-paste review queue; born from the tick-282 census (69 duplicate classes in 32 files, every one the accepted per-item-sections texture: Task/Requirements per exercise, Overview/Pros/Cons per database, Challenge/Results per case study), so report mode, not a hard ban |
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

Measured 2026-09-28 (424 external URLs probed): 391 ok, 20
redirect, 0 dead, 6 denied, 2 timeout, 5 template - zero dead
links, and every redirect is a healthy root-to-page redirect (docs
landing pages), not rot. Cadence decision from that data: monthly,
plus an on-demand run after major content passes; weekly probes
would spend 424 network requests per run for no rot signal. The
denied class (udemy, leetcode, academy.langchain) is course-
platform bot walls, not dead links.

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
scorecard's corpus line - and that pairing is no longer just
by-construction: the feed_parity_check hard gate runs both exporters
and locks their cross-feed invariants, so classification drift in one
feed cannot ship silently broken JSON to a platform load step.

## 📊 Curriculum Metrics (report tool)

```bash
python scripts/qa/curriculum_metrics.py
python scripts/qa/curriculum_metrics.py --out metrics.json
```

Answers "how good is the teaching material?" with numbers: lesson
content-word distribution (prose + code - code-heavy lessons that put
a full implementation in one fence are dense, not thin), python/bash
fence density, H2/link structure, and quiz coverage per module
(33/33, 660 questions). Report only - the thinnest-lessons list is a
content-pass review queue, not a failure (same stance as
fm_staleness). The sparse-modules (<3 lessons) line shows unit
content next to the count - a 2-lesson focused unit can carry a full
module, so the count alone is never a verdict. `--out` writes the
whole report as one JSON snapshot (same feed idiom as manifest_export
and quiz_export), so content totals and per-lesson stats accumulate
into a trend instead of scrolling away with stdout. Models borrowed
for parity: the corpus classification from quality_report, the fence
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
