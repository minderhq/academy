#!/usr/bin/env python3
"""One-command quality scorecard for the PROJECT-OMEGA curriculum corpus.

Runs every committed QA gate as a subprocess, harvests its summary line,
and prints a single scorecard - the fast answer to "where does the corpus
stand today?" without running each tool by hand.

  hard gates (exit 1 on findings, CI contract):
    frontmatter_lint   frontmatter completeness/consistency (FM-01..FM-09)
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
    structure_lint     fence parity + H1 discipline corpus-wide
    linkcheck          every relative link target exists on disk
    casecheck          case-sensitive href/disk match (Windows-invisible breaks)
    anchor_check       in-document anchors vs GitHub-accurate slugger
                       (2 known inline-code examples allowlisted)
    table_lint         ragged GFM tables - header/separator/body lines
                       with differing cell counts (TL-01); escaped \\|
                       is a literal pipe, not a separator
    mermaid_lint       mermaid diagram fences: known diagram-type header
                       (MM-01), balanced () [] {} (MM-02), declared
                       direction on graph/flowchart (MM-03)
    deprecated_scan    deprecated API calls in python fences (DA-01:
                       datetime.utcnow/utcfromtimestamp - Python 3.12+;
                       use datetime.now(timezone.utc); DA-02: HF
                       use_auth_token kwarg - removed in transformers
                       5.x; use token=); comment-only mentions are
                       not findings
    kwarg_lint         calls with removed/renamed kwargs on known APIs
                       (KW-01 langchain constructor kwargs, KW-02 removed
                       qdrant .search kwargs) - hard gate since the
                       query_points migration drained (tick-220)
    typing_legacy_scan legacy typing spellings in python fences (TL-01:
                       Optional[ Union[ List[ Dict[ Tuple[ Set[
                       FrozenSet[ Type[) - hard gate since the PEP
                       585/604 modernization epic drained (typing /3);
                       4-backtick super-fence teaching content is
                       invisible to the fence model by design
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
                       locks their invariants (FP-00..FP-06: module
                       sets, counts vs arrays, hierarchy vs documents
                       lessons, quiz-file membership, bank-internal
                       totals, assessment.quiz flags) - consistency
                       only, content totals stay the living baseline
  queue gate (drain in progress; never fails the report unless --fail-on-queue):
    objectives_lint    template-objective artifacts (OL-01/OL-02), phase by phase
    fence_namecheck    names used in a python fence that no fence in the
                       document binds (NC-01, report mode): catches missing
                       stdlib imports; the residual pseudo-code/notation
                       fragment idiom is accepted noise for now
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
    ("pip_uv_scan.py", "pip_uv_scan", True),
    ("langchain_census.py", "langchain_census", True),
    ("legacy_chain_scan.py", "legacy_chain_scan", True),
    ("codeblock_syntax_scan.py", "codeblock_syntax_scan", True),
    ("bashblock_syntax_scan.py", "bashblock_syntax_scan", True),
    ("datablock_syntax_scan.py", "datablock_syntax_scan", True),
    ("assessment_lint.py", "assessment_lint", True),
    ("quiz_export.py", "quiz_export", True),
    ("structure_lint.py", "structure_lint", True),
    ("linkcheck.py", "linkcheck", True),
    ("casecheck.py", "casecheck", True),
    ("anchor_check.py", "anchor_check", True),
    ("table_lint.py", "table_lint", True),
    ("mermaid_lint.py", "mermaid_lint", True),
    ("deprecated_scan.py", "deprecated_scan", True),
    ("objectives_lint.py", "objectives_lint", False),
    ("fence_namecheck.py", "fence_namecheck", False),
    ("fm_staleness_scan.py", "fm_staleness", False),
    ("kwarg_lint.py", "kwarg_lint", True),
    ("typing_legacy_scan.py", "typing_legacy_scan", True),
    ("version_alignment_scan.py", "version_alignment_scan", True),
    ("feed_parity_check.py", "feed_parity_check", True),
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
