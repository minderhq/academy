#!/usr/bin/env python3
"""date-cohort filter over the Last Updated field for PROJECT-OMEGA.

Every doc carries a machine-readable Last Updated (LU-01/LU-02 hard
gate guarantees it: ISO YYYY-MM-DD, zero variants) - this tool turns
that field into the freshness work queue the platform will want:

  - default: docs grouped by YYYY-MM cohort, oldest first - the
    review surface for "which content has not been touched longest"
  - --since YYYY-MM: only docs last updated BEFORE that month (the
    stale-list filter; e.g. --since 2026-03 lists the whole
    2026-02-and-older cohort)

A date is a freshness signal, not a score: a doc can be old because
its subject is stable. The queue says WHERE to look, the content
gates say WHAT is wrong.

Not a quality_report gate (no findings, exit 0 by design) - a
listing tool in the qa/ family.

Run over the whole corpus:
    python scripts/qa/date_cohort.py --root .
    python scripts/qa/date_cohort.py --root . --since 2026-03
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

FM = re.compile(r"^---\s*$")
LU = re.compile(r"^Last Updated:\s*(\d{4}-\d{2})-\d{2}\s*$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def cohort_of(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8",
                               errors="replace").split("\n")
    except (UnicodeDecodeError, OSError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for ln in lines[1:40]:
        if FM.match(ln):
            break
        m = LU.match(ln)
        if m:
            return m.group(1)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--since", type=str, default=None,
                        help="list only docs last updated BEFORE "
                             "YYYY-MM (strictly older cohorts)")
    args = parser.parse_args()

    cohorts: dict[str, list[str]] = defaultdict(list)
    n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        c = cohort_of(path)
        if c is None:
            continue
        n_docs += 1
        cohorts[c].append(path.relative_to(args.root).as_posix())

    order = sorted(cohorts)
    listed = 0
    for c in order:
        if args.since and c >= args.since:
            continue
        files = sorted(cohorts[c])
        listed += len(files)
        print(esc("=== %s: %d docs ===" % (c, len(files))))
        for f in files:
            print("  " + esc(f))
    if args.since:
        print("date_cohort: %d docs last updated before %s "
              "(of %d dated docs; exit 0 by design - listing tool)"
              % (listed, args.since, n_docs))
    else:
        print("date_cohort: %d docs in %d monthly cohorts (oldest %s, "
              "newest %s; exit 0 by design - listing tool)"
              % (n_docs, len(order), order[0] if order else "-",
                 order[-1] if order else "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
