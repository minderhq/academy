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
| quiz_integrity_scan | QI-01..06, QI-08/09 | content-level quiz integrity on top of quiz_export's parser: self-referential positional option ("Both A and B" at position B), duplicate stem within a module, duplicate option text within a question, option letter beyond A-D (the parser silently drops it), numbering gap (duplicate numbers were flagged, missing ones were not), duplicate Answer Key rows for one question (the key dict overwrites, last row silently wins), orphan Answer Key rows with no matching question (quiz_export's join is one-directional: questions pull from the key, key rows are never checked back), cross-module duplicate stem (QI-06: same question label reused across two modules; drained tick-343 with 6 rewords, HARD since tick-345); QI-07/QI-10 lines are report inventory - the skewed-answer-key shuffle queue (max letter ≥50% or a letter absent; refines AS-09's 70% tripwire); born from the tick-284 census that found 2 self-reference bugs (fixed at birth), QI-08/09 from the tick-285 census (0/0 across 33 modules - locked at birth), baseline 0; QI-10 lines are the answer-length-bias report queue (correct option longest-or-tied in ≥50% of a module's questions - the pick-the-longest tell wins ~70% corpus-wide vs ~25% chance, born from the tick-290 census, 31/33 modules queued; no mechanical fix, drains via per-module content passes) |
| structure_lint | - | fence parity + H1 discipline + heading level jumps (HJ-01: no heading dives more than one level below the previous one, so the document outline stays monotone for TOC renderers, screen readers and platform nav trees) corpus-wide |
| linkcheck | - | every relative link target exists on disk |
| casecheck | - | case-sensitive href/disk match (Windows-invisible breaks) |
| anchor_check | - | in-document AND cross-file anchors vs a GitHub-accurate slugger |
| table_lint | TL-01 | ragged GFM tables (differing cell counts) |
| mermaid_lint | MM-01..03 | diagram headers, balanced brackets, declared direction |
| deprecated_scan | DA-01..04 | deprecated API calls in python fences (DA-04: the `torch.cuda.amp` namespace, deprecated since PyTorch 2.4 - the modern home is the `torch.amp` namespace with an explicit device on `autocast`; born tick-347, drained same tick: 3 sites across 3 files) |
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
| fence_class_scan | FC-01 | every fence label must be classified: fence_label_scan locks that a label exists, this locks that it is owned - 5 parser-validated classes (python/bash/json/yaml/mermaid, each with a syntax judge) plus 16 explicitly accepted unvalidated classes (text/markdown prose, dockerfile/powershell/nginx/cypher/cuda/promql/cron/gitignore operational config, html/typescript/tsx/sql/cpp/c teaching samples); anything else is invisible code - a `toml` fence would skip every data-block gate and a platform load step could not tell code from prose; a new class lands here as a finding: teach a parser gate or classify it; born from the tick-285 label census (21 labels across 4244 fences), baseline 0 |
| lesson_id_scan | LI-01/02 | every lesson doc (`docs/phases/<phase>/<NNNN-module>/NNNN-*.md`, 114 files) carries its filename's own `NNNN: ` id as the prefix of both the frontmatter Title and the first H1: the id is the stable platform join key across filename, manifest nav label and rendered page; title_h1_parity_scan already forces Title := H1 so the prefix lives in both faces or neither, this locks the prefix itself - resource_id_check is the same discipline for the 43 family resources; born from the tick-287 census (114/114 clean), baseline 0 |
| doc_id_check | DD-01 | corpus-unique Document ID: manifest_export copies the frontmatter Document ID into the platform manifest's primary `id` field, so two docs carrying the same id join-collapse into one nav entry; only cross-corpus uniqueness is enforced (short-form idiom in scope); born from the tick-328 census (408/408 distinct), baseline 0 |
| action_version_scan | AV-01 | every `uses: owner/repo@vN` pin on any line of a docs/*.md file must name an action whose MAJOR version matches the registry - stale sample pins teach deprecated workflows |
| unicode_ws_hygiene_scan | UW-01 | invisible/control characters in prose (zero-width space/joiner/non-joiner, word joiner, figure/narrow no-break spaces, bidi controls, NBSP variants): they render as nothing on GitHub but corrupt search, copy-paste and platform parsing |
| fence_import_check | IC-01 | every import in every ```python fence resolves against the kurulu-stack via importlib+ast - the langchain_census (LC-01) generalization to all packages: an import that ModuleNotFoundError's as written fails the gate; multi-line parens, semicolons and as-aliases parsed, dotted-submodule fallback; alternative/3p stacks and lesson-local fragments live in ACCEPTED_PREFIXES (census 424 packages / 125 modules, allowlist locked tick-325, baseline 0) |
| resource_ref_check | RR-01 | FAMILY-0NN references in prose must exist on disk: a pointer to a non-existent resource id is a dead claim linkcheck cannot see; the valid-id set derives from the same disk glob as resource_id_check (no roto); born from the tick-327 census (1316 refs / 43 ids / 0 out-of-range), baseline 0 |
| fence_variant_check | PY-01 | loaded-but-never-defined near-miss names in python fences: a bare name LOADED in a fence, defined nowhere in its scope, yet a lexical variant of a name that IS in scope (case-equal, length-aware Levenshtein, word-prefix) - the silent NameError class; lambda-closure chains, module fallbacks, dunder exclusions and (rel,name)-keyed accepts modeled; born from the tick-331 census, baseline 0 |
| fence_variant_check_module | PY-02 | module-level face of PY-01 (names LOADED outside any function/class/lambda - PY-01's declared out-of-scope region), same predicate at module granularity; born from the tick-334 census, baseline 0 |
| bash_vars_check | BB-02 | undefined shell variables in bash fences: a plain `$VAR` or bare-braced `${VAR}` load with no assignment in the fence/same-document/builtin/systemd `Environment=`/os-release source set; `${VAR:-default}` guards are the designed idiom and report nothing; born from the tick-336 census, baseline 0 |
| uv_install_check | UV-01 | plain `pip install` outside the uv-first curriculum standard (pip/pip3/python -m pip in bash/sh/shell/dockerfile fences); the lookbehind does not report the `uv pip install` interface; (rel,line)-keyed accepts for documented fallbacks (conda antiexample, pip bootstraps, notebooks); born from the tick-337 census, baseline 0 |
| term_consistency_scan | TC-01/TC-02 | one canonical brand spelling per term: TC-01 bare `HuggingFace` vs canonical Hugging Face (66 sites in 37 files drained tick-401, hard since; identifier continuations like Embeddings/H4/TB excluded), TC-02 reports the remaining legal variants (quoted error titles, literal Tags); TF/LangChain/PyTorch/OpenAI measured 0 at birth tick-400 |
| front_matter_census | FM-01..06 | front-matter integrity as platform metadata: every doc carries the closed 5-key block (Document ID / Title / Last Updated / Status / Difficulty), Status enum {Complete}, Difficulty enum, ISO dates with a future-date guard, Phase/Module path cross-checks; enum widening lands in the same commit as the value change; born at 0/408 (KW-03), hard from birth |
| tag_vocabulary_census | TV-01..03 | closed Tags vocabulary (platform filtering + related-content navigation): TV-01 unknown tag vs WHITELIST (VARIANTS canonicalizer map), TV-02 duplicate tag within one doc, TV-03 non-canonical variant of a whitelisted tag; born from the tick-403 census (111 docs / 216 tags / 0 dup / 0 case), TV-03 sites drained tick-404, hard since; a new tag lands in the same commit as the whitelist entry |
| tags_coverage_check | TG-01/02/03 | Tags coverage - WHO carries tags (TV locks WHAT they say): TG-01 a numbered in-phase lesson outside guides/ with no Tags field is invisible to the platform tag filter (hard; born 2026-09-30 at 0 after the 6-lesson drain - 5103/5203/5204/6203/7302/7403, all 5-key-minimum docs, filled from sibling pools - now 93/93); TG-02/03 report the pending tag-all-or-none decisions: guides/ genre split 9/21 tagged, meta docs 10/146 tagged (the tagged ten all sit in the phase2-revamp zone) |
| related_census | RL-01..03 | Related-field link integrity (platform cross-reference navigation): RL-01 a Related token resolving to ZERO files, RL-02 to MULTIPLE (ambiguous join), RL-03 non-canonical shape (bare lists bracketed to the Related standard); born from the tick-405 census (110 docs / 35 tokens, all exactly-1 resolved), RL-03 sites drained tick-406, hard since |
| estimated_time_census | ET-01..03 | Estimated Time parses for scheduling/progress math: ET-01 missing or unparseable value, ET-02 field-name variant (canonical `Estimated Time:`), ET-03 range values collapsed to the single-duration canonical (midpoint, half-up; drained tick-408); hard from birth at 0 |
| prereq_census | PQ-01..03 | Prerequisites chain integrity - the learning-path backbone: PQ-01 machine-parseable token resolving to ZERO files (a prerequisite that can never be unlocked), PQ-02 token resolving to MULTIPLE, PQ-03 machine-parseable value not in the canonical bracketed bare-token list form (the Related standard); born at 0 (108 docs / 7 tokens, tick-409), PQ-03 drained tick-410, hard since; free-text authoring pointers remain legal |
| prereq_ordering_scan | PO-01/02 | learning-path ORDER integrity: corpus numbering is monotonic, so "earlier on the path" is exactly "smaller 4-digit number" - PO-01 forward reference (a prereq token greater than the referrer's own number) is an unlock deadlock on the platform, PO-02 self reference; numeric predicate, no false-positive class; born at zero 2026-09-30 (95 numbered docs / 4 tokens clean; 13 non-numbered docs are free-text/resource pointers, visible in the skip line), hard from birth |
| prereq_free_text_check | PQ-04 | Prerequisites free-text vocabulary closure: every non-token value must be exactly one role-canonical string - lessons "See module README", module READMEs "See PREREQUISITES.md" - so the platform nav generator can classify every pointer; born 2026-09-30 at 4 prose variants (a vague assumption + three "Phase N completion" statements redundant with spine position), drained same tick, hard since; bracketed resource tokens stay PQ-01..02 territory |
| prereq_target_check | PQ-05 | Canonical pointer target integrity: every "See module README" / "See PREREQUISITES.md" pointer must land - the nearest README-bearing ancestor's README exists and carries a prerequisites section, the module's PREREQUISITES.md exists, and a pointer with no README-bearing ancestor is a finding; born at zero (census 2026-09-30: 33/33 module READMEs carry prerequisites), hard from birth |
| nav_coverage_check | NV-01..02 | Navigation coverage: NV-01 (hard) every learner-facing doc in a module - root lessons, guides/, assessment/ - must be filename-linked from its module README (a lesson the README never links is invisible to the platform nav); NV-02 (hard) phase-level CHECKPOINT.md/PREREQUISITES.md must be filename-linked from the phase README. Born 2026-09-30 at 45 module orphans over 17 READMEs (30 prose-described-but-unlinked lessons, 6 never mentioned, 9 assessments without Location lines) + 7 unlinked phase CHECKPOINTs - both drained same tick (the checkpoint drain also fixed the "Phase s Practice" typo in the phase-2/3 READMEs), both hard since |
| last_updated_check | LU-01..02 | Last Updated parseability: LU-01 missing or empty field, LU-02 non-ISO value (date.fromisoformat is the parser) - the platform's freshness display and recently-updated sorting need a machine-parseable date; hard from birth at 0/408 (census 2026-09-30: all ISO-parseable, range 2026-02-04..2026-09-30) |
| lesson_order_check | LO-01 | Module README lesson order: the first-occurrence order of lesson links in a module README must be strictly increasing - the platform renders nav in document order, so README order IS the learning path, and IDs encode the intended sequence; first occurrence only (phase-1/2 READMEs repeat the full list in tail summaries), guides/assessments are genre extras with free positions. Born 2026-09-30 at 5 stray bullets (5103/5203/5204/6203/7403, appended by the nav drain before the first lesson header), drained same tick, hard since |
| toc_coverage_check | TC-01 | TOC completeness: in a TOC-carrying doc every real content H2 (outside frontmatter and code fences, closing trio Summary/References/Next Steps exempt) must appear as a TOC bullet - matched by display text OR href slug (an industry "Part 1:" prefix or a volume emoji prefix in the label is house style; the nav pane needs the link to exist and resolve, not the label). The TOC becomes the platform's in-doc nav pane, so an unlisted section is invisible in navigation. Fence-aware: a naive census flagged 2 "missing" H2s in 2301 that were literal text inside a python example block; anchor_check's fence tracking was right. Born 2026-09-30 whole-corpus over 141 TOC-carrying docs: 45 rows = 24 label mismatches (resolved by the slug-matching rule, zero doc edits) + 21 genuine gaps (19 phase-README tail sections [Prerequisites x5 on phases 3-7, Assessment x7, Related Topics x7] + 2 guide Abstracts, all drained in document order), hard since |
| difficulty_census | DI-01..03 | closed Difficulty vocabulary (platform filter/sequence dimension): DI-01 missing/empty/unknown value, DI-02 field-name variant (canonical `Difficulty:`), DI-03 value outside the canonical enum {Beginner, Intermediate, Advanced} (5 Expert sites drained tick-412); hard from birth at 0/408 (KW-03) |
| lesson_anatomy_census | LA-01..03 | canonical lesson anatomy: LA-01 every lesson doc opens its pedagogy with the "Learning Objectives" H2 (the syllabus card contract), LA-02 it is the FIRST TOC bullet, LA-03 an Abstract H2 precedes the body (114/114; drains tick-414/415/416); hard since; hands-on and quiz H2s are deliberately not part of the anatomy (assessment lives in separate QUIZ/PRACTICE/lab files) |
| closure_census | CL-01..03 | canonical closing trio after the last content section: a Summary-class recap H2, References H2, Next Steps H2 - CL-01 drained phase-by-phase to 114/114 (hardened tick-431), CL-02/CL-03 hard from birth tick-417 |
| qa_tooling_coverage_check | QT-01 | QA-TOOLING.md locked to the scorecard: every script in quality_report.GATES must be named in this doc by script stem or gate label, so the gate inventory cannot silently drift behind the CI contract again (at the 2026-09-30 birth census this doc listed 22 of 59 gates - prereq_census, hard since tick-410, had no row); hand-written rows stay, the gate enforces presence only; born at 22 findings (1 matcher FP: fm_staleness label form), 21 rows drained same tick, hard since |

## 📋 Report Gates (exit 0 by design)

| Gate | What it reports |
| --- | --- |
| objectives_lint | template-objective artifacts (OL-01/OL-02) - the drain queue |
| fence_namecheck | unbound names in python fences, two codes: NC-01 module access without import (`name.attr` on a known module no fence imports - certain NameError, the gate's signal) and NC-02 fragment idiom (accepted teaching texture: usage-before-setup sketches, agent-UI placeholders, pseudo-code) |
| duplicate_heading_scan | duplicate heading texts per file (DH-01) - GitHub suffixes the slugs and binds explicit anchors to the first heading, so a platform TOC/nav generator needs this inventory to suffix deterministically, and a new duplicate outside the accepted idiom lands here as the copy-paste review queue; born from the tick-282 census (69 duplicate classes in 32 files, every one the accepted per-item-sections texture: Task/Requirements per exercise, Overview/Pros/Cons per database, Challenge/Results per case study), so report mode, not a hard ban |
| fm_staleness | Last Updated age map (fresh/recent/stale/missing) - a stale date is a review queue, not a failure |
| uv_workflow_census | uv project-workflow adoption census (UV-02): every uv subcommand occurrence inside fences (uv pip install, uv venv, uv init/add/sync/run, uvx, uv tool) plus pyproject.toml / uv.lock / requirements.txt doc counts - tracks migration from the imperative layer the uv modernization taught to declarative project workflows; inventory, not a lock (numbers move with content) |
| fence_label_census | fence-label accuracy census (FLC-01): a raw Dockerfile (>=4 directives) or nginx config (>=2 markers) pasted into a bash/sh/shell fence is a mislabel - shell highlighting and the wrong parser gates see it; heredoc GENERATION of such files (cat > ... <<'EOF') is the correct idiom and counts as embedded; born tick-341 at 0 raw / 7 embedded (3 Dockerfile + 4 nginx) across 699 shell fences |
| pacing_consistency_census | Estimated Time vs real reading load (PC-01, report-only): claimed hours against lesson_stats words/code at 200/100 wpm, ratio per doc; born 2026-09-30 at 111 docs, median ratio 4.50 (p10 2.51, p90 8.87) - labels carry hands-on-budget, not reading-time, semantics corpus-wide (naive 2x band flags 107/111, so no hard gate until the platform picks the semantics); module READMEs holding their module's aggregate budget are a known aggregate-by-design class |
| difficulty_distribution_scan | Difficulty as a sequence dimension (DX-01, report-only): per-phase Beginner/Intermediate/Advanced distribution plus docs >=2 bands from their phase's median; born 2026-09-30 with the ramp coherent (phase-1 Intermediate -> phases 3/4/5/7 Advanced, 260 in-phase docs; assessment track ramps phase1 Beginner -> phase3+ Advanced), 25 anomaly candidates almost all entry-point READMEs by design - 2 lesson candidates (3301/3302 Beginner primers) inspected and kept; module README aggregate class is known |

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
