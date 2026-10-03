#!/usr/bin/env python3
"""QA-tooling doc coverage (QT-01) for PROJECT-OMEGA.

quality_report.py's GATES list is the authoritative gate inventory
(the CI contract), and docs/00-META/QA-TOOLING.md is its human face.
Those two drifted: at the 2026-09-30 birth census the doc's tables
listed 22 gates while the scorecard ran 60 - even prereq_census, a
hard gate since tick-410, had no row. Hand-maintained duplicates
drift by construction, so this check locks the doc to the scorecard:

QT-01  every script registered in quality_report.GATES must be
       mentioned in QA-TOOLING.md by its script stem. Missing = the
       doc does not tell the reader the gate exists.

HARD GATE - exit 1 on any finding. Birth census 2026-09-30: 22
missing rows out of 59 gates; 1 finding was a checker-matcher false
positive (the doc's `fm_staleness` row names fm_staleness_scan.py
by its gate label, not script stem - the matcher now accepts
either), the 21 real gaps drained same tick by writing the missing
rows into the Hard Gates and Report Gates tables (hand-written
prose stays; the gate only enforces presence). Same drain-then-
harden cycle as CL-01/AS-09.

Run over the whole corpus:
    python scripts/qa/qa_tooling_coverage_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quality_report import GATES  # noqa: E402


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    doc_path = args.root / "docs" / "00-META" / "QA-TOOLING.md"
    if not doc_path.exists():
        print("qa_tooling_coverage_check: SKIP - docs/00-META/QA-TOOLING.md not found, nothing to check")
        return 0
    doc = doc_path.read_text(encoding="utf-8", errors="replace")

    findings: list[str] = []
    for script, label, hard in GATES:
        stem = Path(script).stem
        # Doc rows may use the script stem or the shorter gate label
        # (e.g. fm_staleness for fm_staleness_scan.py) - either names
        # the gate for a reader; neither means the doc is silent.
        if stem not in doc and label not in doc:
            findings.append("QT-01 missing row: %s (%s, %s)"
                            % (stem, label, "hard" if hard else "report"))

    print("qa_tooling_coverage_check: %d gates in quality_report.GATES, "
          "%d mentioned in docs/00-META/QA-TOOLING.md"
          % (len(GATES), len(GATES) - len(findings)))
    if findings:
        for f in findings:
            print("  " + esc(f))
    mode = ("queue empty" if not findings
            else "hard gate - write the missing rows")
    print("qa_tooling_coverage_check: %d findings (QT-01) - %s"
          % (len(findings), mode))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
