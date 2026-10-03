#!/usr/bin/env python3
"""changelog release-index parity gate for PROJECT-OMEGA.

CHANGELOG.md is a Keep-a-Changelog file with three synchronized
surfaces per release: the "## [X.Y.Z] - DATE" section, the Version
Summary table at the bottom, and the bracketed reference-link
definitions after it. The 1.3.0 entry (tick-551 era) was written and
its gate-count claim healed, but its own two index surfaces were
never updated - the newest release had no summary row and no
reference definition, while 1.2.0/1.1.0/1.0.0 carried both.
meta_claims_check locks gate counts, linkcheck sees no broken link
(an undefined reference renders as literal text), so nothing owned
these surfaces: exactly the invisible index-drift class.

CS-01  every release section has a Version Summary row
CS-02  every Version Summary row corresponds to a release section
CS-03  the date in a summary row equals the date in its section header
CS-04  every bracketed release version has a reference-link definition
CS-05  the Version Summary order equals the release-section order

Hard gate (exit 1 on findings): born tick-552 at the maximal
finding - CS-01 and CS-04 both firing on 1.3.0, drained in the
same tick.

Run over the whole corpus:
    python scripts/qa/changelog_summary_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECTION = re.compile(r"^## \[([\d.]+)\] - (\S+)", re.M)
SUMMARY_ROW = re.compile(r"^\|\s*\*\*([\d.]+)\*\*\s*\|\s*(\S+)\s*\|", re.M)
REF_DEF = re.compile(r"^\[([\d.]+)\]:\s*(\S+)", re.M)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []

    path = args.root / "CHANGELOG.md"
    if not path.exists():
        print("changelog_summary_check: SKIP - CHANGELOG.md not found, nothing to check")
        return 0
    text = path.read_text(encoding="utf-8")

    sections = [(v, d) for v, d in SECTION.findall(text)]
    i = text.find("## Version Summary")
    summary = [(v, d) for v, d in SUMMARY_ROW.findall(text[i:])] if i != -1 else []
    refs = {v for v, _ in REF_DEF.findall(text)}
    sec = dict(sections)
    summ = dict(summary)

    for v, d in sections:
        if v not in summ:
            findings.append(f"{v}: CS-01 release section ({d}) has no "
                            f"Version Summary row")
    for v, d in summary:
        if v not in sec:
            findings.append(f"{v}: CS-02 Version Summary row ({d}) has no "
                            f"release section")
        elif sec[v] != d:
            findings.append(f"{v}: CS-03 date mismatch - section "
                            f"{sec[v]!r} vs summary row {d!r}")
    for v, _ in sections:
        if v not in refs:
            findings.append(f"{v}: CS-04 release section has no "
                            f"[{v}]: reference-link definition")
    if [v for v, _ in summary] != [v for v, _ in sections]:
        findings.append("CS-05 Version Summary order "
                        f"{[v for v, _ in summary]} != section order "
                        f"{[v for v, _ in sections]}")

    for f in findings:
        print(f)
    print(f"changelog_summary_check: {len(findings)} findings "
          f"(CS-01/02 summary parity, CS-03 date parity, CS-04 reference "
          f"definitions, CS-05 order parity) across {len(sections)} release "
          f"sections / {len(summary)} summary rows")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
