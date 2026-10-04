#!/usr/bin/env python3
"""Last Updated field parseability (LU-01/LU-02) for Minder Academy.

Every doc carries a Last Updated frontmatter date; the platform uses
it for freshness display and recently-updated sorting, so the value
must be machine-parseable - a prose date ("September 2026") or a
locale variant sorts wrong or not at all.

LU-01 (hard): Last Updated missing or empty in the frontmatter.
LU-02 (hard): present but not ISO YYYY-MM-DD (date.fromisoformat is
the parser; anything it rejects is a finding).

Birth census (2026-09-30) measured 408/408 docs carrying the field,
all ISO-parseable, zero variants (range 2026-02-04..2026-09-30) -
HARD gate from birth (KW-03: deterministic predicate, census 0).

Run over the whole corpus:
    python scripts/qa/last_updated_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
LU_FIELD = re.compile(r"^Last Updated:(.*)$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def lu_value(lines: list[str]) -> str | None:
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = LU_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_docs = 0
    n_have = 0
    findings: list[str] = []

    for path in sorted((args.root / "docs").rglob("*.md")):
        n_docs += 1
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        val = lu_value(lines)
        if val is None:
            rel = path.relative_to(args.root).as_posix()
            findings.append("LU-01 no Last Updated field in %s" % rel)
            continue
        if not val:
            rel = path.relative_to(args.root).as_posix()
            findings.append("LU-01 empty Last Updated in %s" % rel)
            continue
        try:
            datetime.date.fromisoformat(val)
        except ValueError:
            rel = path.relative_to(args.root).as_posix()
            findings.append("LU-02 non-ISO Last Updated %r in %s"
                            % (val, rel))
            continue
        n_have += 1

    print("last_updated_check: %d/%d docs with parseable Last Updated"
          % (n_have, n_docs))
    for f in findings:
        print("  " + esc(f))
    print("last_updated_check: %d LU findings - hard gate, born at zero "
          "(census 2026-09-30: 408/408 ISO-parseable)"
          % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
