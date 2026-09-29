#!/usr/bin/env python3
"""One-command quality scorecard for the PROJECT-OMEGA curriculum corpus.

Runs every committed QA gate as a subprocess, harvests its summary line,
and prints a single scorecard - the fast answer to "where does the corpus
stand today?" without running each tool by hand.

  hard gates (exit 1 on findings, CI contract):
    frontmatter_lint   frontmatter completeness/consistency (FM-01..FM-09)
    doc_id_check       Document ID unique across the corpus (DD-01):
                       manifest_export copies it into the platform
                       manifest's primary `id` field, so two docs
                       sharing one ID collapse the join; FM-03 locks
                       existence and FM-07 filename-prefix match,
                       this locks cross-file uniqueness - born from
                       the tick-328 census (408 files, 408 distinct
                       IDs, 0 duplicates)
    pip_uv_scan        bare pip install only inside documented exceptions
                       (Docker/container, conda workflows, uv bootstraps,
                       uv-first fallback blocks)
    langchain_census   every langchain/langgraph import in a ```python
                       fence resolves against the installed stack (LC-01)
    legacy_chain_scan  bare Name uses of langchain_classic-only chain/
                       agent names (LC-02) - catches the import-less
                       usage that the import-census cannot see (tick-224)
    codeblock_syntax_scan
                       every ```python fence parses as Python (CB-01);
                       non-Python content lives in an honest fence label
                       (text/bash/yaml) instead
    bashblock_syntax_scan
                       every ```bash fence passes bash -n (BB-01); doc
                       placeholders use runnable ${VAR} form, not <name>
    datablock_syntax_scan
                       every ```json fence parses as JSON (DB-01) and
                       every ```yaml fence parses as a YAML document
                       stream (DB-02); prose/formulas live in text fences
    assessment_lint    assessment/QUIZ.md + PRACTICE.md coverage (AS-01..AS-09;
                       AS-09 option-shuffle queue is report-mode, shown separately)
    quiz_export        quiz bank parses into complete question records
    quiz_integrity_scan
                       content-level quiz integrity (QI-01..06 +
                       QI-08/09 hard: self-referential positional
                       option, in-module duplicate stem, duplicate
                       option text, option beyond A-D, numbering
                       gap, cross-module stem dup, duplicate
                       Answer Key rows, orphan
                       Answer Key rows, QI-11 answer key with
                       no matching option row or <2-option
                       mcq; QI-11 born tick-374, baseline 0) on top of
                       quiz_export's parser; QI-07/QI-10
                       are the report inventory (the
                       skewed-answer-key shuffle queue that
                       refines AS-09's 70% tripwire + the
                       answer-length-bias queue: the correct
                       option is longest-or-tied in >=50% of a
                       module's questions - born from the
                       tick-290 census that measured a ~70%
                       pick-the-longest win rate vs ~25% chance,
                       31/33 modules queued) - born
                       from the tick-284 census (2 self-reference
                       bugs fixed at birth); QI-08/09 born from the
                       tick-285 census (0/0 - the one-directional
                       Answer Key join locked in reverse)
    structure_lint     fence parity + H1 discipline corpus-wide
    linkcheck          every relative link target exists on disk
    casecheck          case-sensitive href/disk match (Windows-invisible breaks)
    anchor_check       in-document anchors vs GitHub-accurate slugger
                       (2 known inline-code examples allowlisted)
    table_lint         ragged GFM tables - header/separator/body lines
                       with differing cell counts (TL-01); escaped \\|
                       is a literal pipe, not a separator; loose rows
                       right after a table (TL-02 - an unescaped-pipe
                       line GFM swallows as an extra ragged row;
                       born tick-373, baseline 0)
    mermaid_lint       mermaid diagram fences: known diagram-type header
                       (MM-01), balanced () [] {} (MM-02), declared
                       direction on graph/flowchart (MM-03), no % outside
                       double quotes (MM-04 - lexer aborts the render)
    deprecated_scan    deprecated API calls in python fences (DA-01:
                       datetime.utcnow/utcfromtimestamp - Python 3.12+;
                       use datetime.now(timezone.utc); DA-02: HF
                       use_auth_token kwarg - removed in transformers
                       5.x; use token=); comment-only mentions are
                       not findings
    action_version_scan
                       uses: pins in docs must match the canonical
                       action registry (AV-01: current majors -
                       checkout@v7, setup-uv@v9, cache@v4,
                       codecov@v5, buildx/login@v3, metadata@v5,
                       build-push@v6, artifact@v7/v8); comment-only
                       mentions are not findings; born tick-368,
                       baseline 0
    unicode_ws_hygiene_scan
                       invisible/control characters (UW-01: ZWSP/
                       NBSP/mid-file BOM etc - copy-paste debris,
                       runtime poison inside code fences), real
                       trailing whitespace (UW-02; the corpus uses
                       no hard-break double spaces) and mixed line
                       endings per file (UW-03); CR-normalized;
                       born tick-371, baseline 0
    kwarg_lint         calls with removed/renamed kwargs on known APIs
                       (KW-01 langchain constructor kwargs, KW-02 removed
                       qdrant .search kwargs, KW-03 removed qdrant
                       .search_batch methods in qdrant-importing docs,
                       locally defined shadows respected) - hard gate
                       since the query_points migration drained
                       (tick-220); KW-03 born from the tick-324
                       blind-spot note, drained at tick-326
    typing_legacy_scan legacy typing spellings in python fences (TL-01:
                       Optional[ Union[ List[ Dict[ Tuple[ Set[
                       FrozenSet[ Type[) - hard gate since the PEP
                       585/604 modernization epic drained (typing /3);
                       TL-02 legacy import lines / TL-03 bare legacy
                       generics born tick-376 as report queues (census
                       139 / 426 - the /1-/3 fixer's bracket pattern
                       missed both); 4-backtick super-fence teaching
                       content is invisible to the fence model by
                       design
    version_alignment_scan
                       code-side python-version drift in ANY fence
                       (VA-01 FROM python:X.Y, VA-02 python3.X
                       binaries, VA-03 --python X.Y flags, VA-04
                       uv python install/pin X.Y): everything must
                       be the corpus standard 3.13 - born from the
                       tick-257 census that found one production
                       Dockerfile on python3.10 after the 3.13
                       epic was declared done
    feed_parity_check  cross-feed contract between the platform feeds:
                       runs manifest_export + quiz_export for real and
                       locks their invariants (FP-00..FP-07: module
                       sets, counts vs arrays, hierarchy vs documents
                       lessons, quiz-file membership, bank-internal
                       totals, assessment.quiz flags, manifest vs the
                       on-disk docs/*.md tree) - consistency only,
                       content totals stay the living baseline
    readme_claims_check
                       every measurable number in README.md (badges,
                       resource tables, per-phase document table,
                       footer) vs its disk measurement (RC-01; RC-00
                       missing README/failed borrow) - born from two
                       consecutive drift waves (tick-260 "463 files",
                       tick-261 experiments/labs/phase-table)
    sitemap_claims_check
                       every measurable number in SITEMAP.md: section
                       headers vs disk, headers vs their own list
                       entries, and the fenced Statistics block
                       (SC-01; SC-00 missing SITEMAP/failed measure)
                       - SITEMAP called itself "derived from the file
                       tree" while its Statistics block had rotted
                       (tick-262: 458/407/1 vs measured 462/408/4)
    meta_claims_check
                       every measurable number in the remaining entry
                       docs: FAQ.md intro sentence, MASTER-INDEX.md
                       (Total Files line, per-phase Status rows,
                       numbered section headers, lab header 3-way
                       split, File Counts block incl. TOTAL as its
                       own sum, module-table "N docs" cells = lesson
                       files), ORGANIZATION-GUIDE.md tree labels,
                       VOLUME-GUIDE.md (tree labels, labs 2-way
                       split, SITEMAP line, Total Documents footer)
                       and PROGRESS-TRACKER.md (per-volume bars +
                       headers, Total bar, SITEMAP line, stats-table
                       targets; bar percent/fill are learner state,
                       only targets are locked)
                       (MC-01; MC-00 missing file/failed measure) -
                       born while these docs still said 462/463
                       documents, 427 total files and 256 "Module
                       Documents" (tick-263; VOLUME-GUIDE joined in
                       tick-264 while it still said "85 files across
                       7 volumes"; PROGRESS-TRACKER joined in
                       tick-265 while it still targeted "0/97 core
                       files")
    lab_registry_check every `LAB-0NN: Topic` label corpus-wide vs the
                       labs' own frontmatter Titles (LB-01 wrong lab
                       identity - the topic belongs to a different lab
                       than the one labelled; LB-02 unknown/ambiguous
                       topic - teach the signal table or fix the label;
                       LR-01 lab id with no file on disk). Labels carry
                       identities, not numbers, so the claims gates
                       cannot see this class - born from the tick-267
                       census (301 labels) that found DPO Alignment
                       credited to LAB-005 twice and "Custom
                       Quantization" invented for LAB-004 three times
    resource_id_check  numbered-resource id identity across the 43
                       resources (LAB-000..014, PROJECT-001..007,
                       TUTORIAL-000..014, CHEAT-SHEET-001..006): every
                       resource's frontmatter Title and first H1 must
                       carry the filename's own `FAMILY-0NN:` id, and
                       the pre-campaign spaced spellings ("LAB 007",
                       "CHEAT SHEET 004", any case) are banned
                       corpus-wide - born from the tick-268..271
                       canonicalization campaign; lab_registry_check
                       locks what each id points at, this gate locks
                       the id itself
    resource_ref_check cross-document references to the 43 resources
                       (RR-01 out-of-range id: "see LAB-016" with no
                       LAB-016 on disk) - a dead pointer in plain
                       prose that linkcheck cannot see because it is
                       not a relative link href; the valid id set is
                       derived from the same disk glob
                       resource_id_check uses; lowercase matches
                       (lab-001) are out of scope by design - the
                       birth census (tick-327: 1316 uppercase
                       references, 0 out of range; 101 lowercase,
                       all filesystem-path idioms) locked baseline 0
                       at birth
    fence_variant_check undefined lexical variants inside ```python
                       fences (PY-01): a bare name loaded but defined
                       nowhere (scope chain, fence module, same doc,
                       builtins) that is a near-miss of an in-scope
                       name - vocab_size vs vocab, range(epochs) vs
                       the epoch loop var, calculate vs
                       calculator_function; lambda/nested bodies
                       resolve against the enclosing chain, two
                       ambient names + CP-001's placeholder-suffix
                       idiom are allowlisted with reasons; the birth
                       census (tick-330/331: 1857 fences, 7 survivors
                       -> 5 drained, 2 FP classes absorbed by design)
                       locked baseline 0
    fence_variant_check_module module-level lexical variants in
                       ```python fences (PY-02): PY-01 v1's declared
                       out-of-scope region - a bare name loaded at
                       module level (outside any function/class body)
                       that is a near-miss of an in-scope name, same
                       predicate; the region is fragment-densest (296
                       distinct bare non-variant names accepted by
                       design) so only the variant class is locked;
                       birth census (tick-332: 35 hits; tick-333
                       drain 13 across 7 docs + 1 reclassified FP)
                       left 16 hits in 6 recorded FP classes - ambient
                       import classes, wrong/right placeholders, QKV
                       notation, documented __main__ fragment,
                       loop-sibling shape, placeholder pipeline
                       functions - each a reasoned (rel, name) accept;
                       locked baseline 0 at birth
    bash_vars_check     undefined shell variables in ```bash fences
                       (BB-02): the shell counterpart of PY-01 - a
                       plain $VAR or bare-braced ${VAR} load stored
                       nowhere (fence, same doc, builtins, systemd
                       Environment= directives, os-release keys after
                       a source) is reported; guarded ${VAR:-def}
                       idiom tolerates absence by design, and
                       template placeholders plus nginx runtime
                       variables in bash-labeled nginx fragments are
                       absorbed as reasoned (rel, name) accepts; born
                       from the tick-335/336 census (697 fences, 22
                       plain -> 38 with braced loads, 5 drained)
                       locked baseline 0 at birth
    uv_install_check    plain 'pip install' bypassing the uv
                       standard (UV-01) inside bash/sh/shell/
                       dockerfile fences; lines using the uv
                       interface (uv pip install) are never
                       reported; reasoned (rel, exact-line)
                       accepts cover the documented fallback,
                       conda, antiexample, bootstrap and notebooks
                       classes; born from the tick-337 census
                       (715 fences, 145 pip-family lines, 30
                       plain) locked baseline 0 at birth
    uv_workflow_census  uv project-workflow adoption census
                       (report): per-subcommand occurrence
                       counts inside bash/sh/shell/dockerfile/
                       powershell fences plus per-doc mention
                       counts of pyproject.toml, uv.lock and
                       requirements.txt; born from the tick-339
                       census - the corpus was fluent in the
                       imperative layer (uv pip install 135)
                       but silent on the declarative standard
                       (uv init/add/sync/run at 0, uv.lock in
                       0 docs) until ENVIRONMENT-SETUP taught
                       the pyproject.toml + uv.lock workflow;
                       numbers are expected to move as the
                       declarative standard spreads - exit 0
                       by design
    fence_label_census fence-label accuracy census (report,
                       FLC-01): a raw Dockerfile or nginx config
                       pasted into a bash/sh/shell fence is a
                       mislabel (>= 4 Dockerfile directives or
                       >= 2 nginx markers with no shell tokens);
                       heredoc-wrapped generation (cat > ...
                       << 'EOF') is the correct shell idiom and
                       only counted as embedded; born from the
                       tick-341 sweep that closed both backlog
                       relabel items as verified-clean - 699
                       shell fences, 0 raw / 0 raw, 3 + 4
                       embedded, 12 nginx + 18 dockerfile
                       fences already correct; a future raw
                       paste surfaces here - exit 0 by design
    term_consistency_scan brand-term consistency (TC-01 hard,
                       TC-02 report): one canonical spelling per
                       brand in prose - bare "HuggingFace" tokens
                       (identifier continuations like
                       HuggingFaceEmbeddings/H4/TB excluded by the
                       predicate) and prose-lowercase "ollama"
                       (fences, inline code and the ollama.com
                       domain legal); born from the tick-400
                       ad-hoc sweep that found the corpus 55/45
                       split (66 bare HuggingFace vs 54 "Hugging
                       Face"; TensorFlow/LangChain/PyTorch/OpenAI
                       already consistent at 0); drained tick-401,
                       TC-01 promoted to hard gate - exit 1 on any
                       TC-01 return, TC-02 report-only (remaining
                       hits are legal literals)
    front_matter_census front-matter integrity (FM-01..FM-06,
                       hard): every doc needs a complete,
                       terminated YAML front-matter block;
                       Difficulty within {Beginner, Intermediate,
                       Advanced, Expert}; Status within {Complete,
                       In Progress, Draft}; Last Updated
                       YYYY-MM-DD and never a future date; declared
                       Phase/Module matching the docs/phases/ path.
                       Born tick-402 measuring 0 across 408 docs in
                       every class, promoted same tick (KW-03
                       pattern) - new enum values must update the
                       script in the same commit
    unfinished_marker_scan unfinished-content markers in prose
                       (UM-01): outside any code fence, inline code
                       scrubbed, a line must not carry "coming soon",
                       "under construction", "to be written", "to be
                       added", "work in progress" or an uppercase
                       TODO/TBD/FIXME - code fences are invisible by
                       design (starter-code "# TODO:" exercise prompts
                       are the codified notebooks/README.md convention)
                       and fence markers may carry a ">" blockquote
                       prefix; born from the tick-276 census (108 raw
                       matches, every one in a legitimate class) that
                       turned the census into a permanent lock at
                       baseline 0
    empty_section_scan every heading must own content (ES-01): a
                       section is empty iff nothing but blanks/HRs/
                       blockquotes/HTML-comments sits between its
                       heading and the next same-or-higher-level
                       heading; a filled child fills its parent, so
                       container sections are legitimate. Born from
                       the tick-277 census (8 findings, all one class:
                       same-level children under container headings -
                       "## Part 1" + "## 1.1" - that left every Part
                       with an empty body and mis-nested the outline);
                       fixed by re-leveling 123 headings across 3
                       files, fence model length-aware as
                       structure_lint's
    emoji_shortcode_scan gemoji shortcodes in prose (EM-01): the
                       corpus idiom is literal emoji - a platform
                       load step would need a shortcode->emoji
                       mapping while literals render everywhere
                       (``:star3:`` even rendered as raw text on
                       GitHub); inline code is scrubbed, technical
                       lookalikes (:memory:, :server:) stay invisible
    fence_label_scan   fence info-strings (FL-01 uppercase label,
                       FL-02 unlabeled fence): code gates key on the
                       exact lowercase label, so ``Python`` or a bare
                       open is code every gate silently skips - an
                       audit hole, not a style nit; census at birth
                       (tick-280): 4243 open fences, 21 labels, all
                       lowercase and labeled
    setext_scan        latent setext headings and divider hygiene
                       (SE-01 underline run under a non-blank line,
                       SE-02 bare '===', SE-03 non-'---' thematic
                       break): a '---' directly under text is a
                       setext H2 in every renderer - a heading the
                       ATX-only outline gates cannot see; blank line
                       above every divider, ATX for headings; born
                       from the tick-281 census (7 doubled dividers,
                       all one footer-nav template artifact)
    title_h1_parity_scan
                       frontmatter Title == first ATX H1 (TH-01/02/03):
                       manifest_export takes the platform nav label
                       from the Title while the rendered page title
                       is the first H1, so any drift means the nav
                       tree names a different page than the one that
                       opens; fix direction is Title := H1 verbatim;
                       born from the tick-283 census (89 lesson docs
                       where the id prefix lived only in the H1)
    fence_class_scan   fence-label classes must be classified (FC-01
                       unknown label class): fence_label_scan locks
                       that a label EXISTS, this locks that it is
                       owned - 5 parser-validated classes (python/
                       bash/json/yaml/mermaid have syntax judges) +
                       16 explicitly accepted unvalidated classes
                       (text/markdown prose, dockerfile/powershell/
                       nginx/cypher/cuda/promql/cron/gitignore
                       operational config, html/typescript/tsx/sql/
                       cpp/c teaching samples); anything else is
                       invisible code - a ``toml`` fence would skip
                       every data-block gate and a platform load
                       step could not tell code from prose; born
                       from the tick-285 label census (21 labels /
                       4244 fences), baseline 0 at birth
    lesson_id_scan     every lesson doc carries its filename's NNNN
                       id (LI-01 first H1 prefix / LI-02 Title
                       prefix): the id is the stable platform join
                       key across filename, manifest nav label and
                       rendered page; title_h1_parity_scan already
                       forces Title := H1 so the prefix lives in
                       both faces or neither, this locks the prefix
                       itself - resource_id_check is the same
                       discipline for the 43 family resources; born
                       from the tick-287 census (114/114 clean),
                       baseline 0 at birth
  queue gate (drain in progress; never fails the report unless --fail-on-queue):
    objectives_lint    template-objective artifacts (OL-01/OL-02), phase by phase
    fence_namecheck    unbound names in python fences (report mode), two
                       codes: NC-01 module access without import (a known
                       module used as `name.attr` that no fence in the
                       document imports - certain NameError) and NC-02
                       fragment idiom (accepted teaching texture) - the
                       2026-09-29 triage split 794 flat findings into
                       4 real module accesses (all fixed) + 790 fragments
    duplicate_heading_scan
                       duplicate heading texts per file (DH-01, report
                       mode): GitHub suffixes the slugs and binds
                       explicit anchors to the first heading, so a
                       platform TOC/nav generator needs this inventory
                       to suffix deterministically; born from the
                       tick-282 census (69 duplicate classes in 32
                       files, every one the accepted per-item-sections
                       idiom - Task/Requirements per exercise,
                       Overview/Pros/Cons per database), so report
                       mode, not a hard ban
    fence_import_check unresolvable imports in python fences (IC-01,
                       hard gate since tick-325): every import in every
                       ```python fence resolves against the
                       kurulu-stack - generalizes langchain_census
                       from the langchain family to all third-party
                       packages, so a lesson teaching code that raises
                       ModuleNotFoundError as written fails the gate;
                       ast-based (CB-01 owns fence syntax), 4-backtick
                       super-fence teaching content invisible by the
                       fence_class_scan model, relative imports
                       skipped; the tick-323/324 census (429 -> 424)
                       classified into two accepted classes locked in
                       the gate's ACCEPTED_PREFIXES (alternative/
                       optional third-party stacks, lesson-local
                       fragments)
    fm_staleness       curriculum freshness map (report mode): Last Updated
                       age distribution across docs/ - surfaces the oldest
                       material so modernization passes can target it; a
                       stale date is a review queue, not a failure

Plus corpus stats (lesson files / modules / phases) so the scorecard doubles
as a curriculum inventory.

Usage:
    python scripts/qa/quality_report.py [--root REPO_ROOT] [--fail-on-queue]

Exit codes: 0 = all hard gates pass (and queue empty unless --fail-on-queue),
            1 = any hard gate fails (or queue non-empty with --fail-on-queue).
Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

LESSON_FILE = re.compile(r"^\d{4}-.*\.md$")
MODULE_DIR = re.compile(r"^\d{4}-")
PHASE_DIR = re.compile(r"^phase\d+-")

# (script, label, hard gate?)
GATES = [
    ("frontmatter_lint.py", "frontmatter_lint", True),
    ("doc_id_check.py", "doc_id_check", True),
    ("pip_uv_scan.py", "pip_uv_scan", True),
    ("langchain_census.py", "langchain_census", True),
    ("legacy_chain_scan.py", "legacy_chain_scan", True),
    ("codeblock_syntax_scan.py", "codeblock_syntax_scan", True),
    ("bashblock_syntax_scan.py", "bashblock_syntax_scan", True),
    ("datablock_syntax_scan.py", "datablock_syntax_scan", True),
    ("assessment_lint.py", "assessment_lint", True),
    ("quiz_export.py", "quiz_export", True),
    ("quiz_integrity_scan.py", "quiz_integrity_scan", True),
    ("structure_lint.py", "structure_lint", True),
    ("linkcheck.py", "linkcheck", True),
    ("casecheck.py", "casecheck", True),
    ("anchor_check.py", "anchor_check", True),
    ("table_lint.py", "table_lint", True),
    ("mermaid_lint.py", "mermaid_lint", True),
    ("deprecated_scan.py", "deprecated_scan", True),
    ("action_version_scan.py", "action_version_scan", True),
    ("unicode_ws_hygiene_scan.py", "unicode_ws_hygiene_scan", True),
    ("objectives_lint.py", "objectives_lint", False),
    ("fence_namecheck.py", "fence_namecheck", False),
    ("duplicate_heading_scan.py", "duplicate_heading_scan", False),
    ("fence_import_check.py", "fence_import_check", True),
    ("fm_staleness_scan.py", "fm_staleness", False),
    ("kwarg_lint.py", "kwarg_lint", True),
    ("typing_legacy_scan.py", "typing_legacy_scan", True),
    ("version_alignment_scan.py", "version_alignment_scan", True),
    ("feed_parity_check.py", "feed_parity_check", True),
    ("readme_claims_check.py", "readme_claims_check", True),
    ("sitemap_claims_check.py", "sitemap_claims_check", True),
    ("meta_claims_check.py", "meta_claims_check", True),
    ("lab_registry_check.py", "lab_registry_check", True),
    ("resource_id_check.py", "resource_id_check", True),
    ("resource_ref_check.py", "resource_ref_check", True),
    ("fence_variant_check.py", "fence_variant_check", True),
    ("fence_variant_check_module.py", "fence_variant_check_module", True),
    ("bash_vars_check.py", "bash_vars_check", True),
    ("uv_install_check.py", "uv_install_check", True),
    ("uv_workflow_census.py", "uv_workflow_census", False),
    ("fence_label_census.py", "fence_label_census", False),
    ("term_consistency_scan.py", "term_consistency_scan", True),
    ("front_matter_census.py", "front_matter_census", True),
    ("unfinished_marker_scan.py", "unfinished_marker_scan", True),
    ("empty_section_scan.py", "empty_section_scan", True),
    ("emoji_shortcode_scan.py", "emoji_shortcode_scan", True),
    ("fence_label_scan.py", "fence_label_scan", True),
    ("setext_scan.py", "setext_scan", True),
    ("title_h1_parity_scan.py", "title_h1_parity_scan", True),
    ("fence_class_scan.py", "fence_class_scan", True),
    ("lesson_id_scan.py", "lesson_id_scan", True),
]


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


QUEUE_SUMMARY = re.compile(r"(\d+) template-objective findings in (\d+) files")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--fail-on-queue", action="store_true",
                        help="exit 1 while the objectives queue is non-empty")
    args = parser.parse_args()

    phases = sorted(d for d in (args.root / "docs" / "phases").iterdir()
                    if d.is_dir() and PHASE_DIR.match(d.name))
    modules = sorted(d for p in phases for d in p.iterdir()
                     if d.is_dir() and MODULE_DIR.match(d.name))
    lessons = sorted(p for m in modules for p in m.rglob("*.md")
                     if LESSON_FILE.match(p.name))

    print("PROJECT-OMEGA quality report - %s" % date.today().isoformat())
    print("=" * 72)
    print("corpus: %d lesson files, %d modules, %d phases"
          % (len(lessons), len(modules), len(phases)))
    print()

    failed = False
    queued = False
    for script, label, hard in GATES:
        proc = subprocess.run(
            [sys.executable, str(args.root / "scripts" / "qa" / script),
             "--root", str(args.root)],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        lines = (proc.stdout or "").strip().split("\n")
        summary = next((l for l in reversed(lines)
                        if l.startswith(label)), "no summary line")
        if hard:
            # CI contract: the gate itself decides via its exit code
            # (queued items like AS-09 exit 0 by design).
            status = "PASS" if proc.returncode == 0 else "FAIL"
            if status == "FAIL":
                failed = True
        else:
            m = QUEUE_SUMMARY.search(summary)
            queued = bool(m and int(m.group(1)) > 0)
            status = "QUEUE" if queued else "PASS"
        print("%-22s %-6s %s" % (label, status, esc(summary)))

    print()
    if failed:
        print("result: FAIL - a hard gate has findings (see its output above)")
    elif queued and args.fail_on_queue:
        print("result: QUEUE - objectives queue still draining (--fail-on-queue)")
    elif queued:
        print("result: PASS - hard gates clean; objectives queue draining "
              "(run objectives_lint.py for the file list)")
    else:
        print("result: PASS - all gates clean")
    return 1 if (failed or (queued and args.fail_on_queue)) else 0


if __name__ == "__main__":
    sys.exit(main())
