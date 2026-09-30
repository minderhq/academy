#!/usr/bin/env python3
"""Stale front-matter dates (report-only) for PROJECT-OMEGA.

Answers the owner question "which files were edited but whose
Last Updated did not move?" - the date filter the owner runs by
hand ("Last Updated: 2026-02") catches the never-touched cohort,
but misses files edited WITHOUT a FM bump. For every docs/**.md
this compares the FM Last Updated date against the file's last
git commit date; commit newer than FM is reported.

REPORT-ONLY by doctrine: dates move only with real edits, and
this tool never gates. Whitespace-only commit touches show up as
stale (no FM bump for invisible bytes is fine); they read as
1-day skew and are harmless. Run from a checkout where git
history matches the working tree.

    python scripts/qa/stale_fm_report.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

FM_LU = re.compile(r"^Last Updated:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def fm_date(text: str) -> str | None:
    head = text.split("---", 2)
    if len(head) < 3:
        return None
    m = FM_LU.search(head[1])
    return m.group(1) if m else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    stale: list[tuple[str, str, str]] = []
    skew_short = 0
    missing_fm: list[str] = []
    n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        n_docs += 1
        rel = os.path.relpath(path, args.root).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = fm_date(text)
        if fm is None:
            missing_fm.append(rel)
            continue
        try:
            out = subprocess.run(
                ["git", "-C", str(args.root), "log", "-1",
                 "--format=%cs", "--", rel],
                capture_output=True, text=True, timeout=10)
            commit = out.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            continue
        if commit and commit > fm:
            days = (date.fromisoformat(commit) -
                    date.fromisoformat(fm)).days
            if days <= 2:
                skew_short += 1  # recent-tick noise: commit bumped a
                continue         # file a day after a real edit
            stale.append((rel, fm, commit))

    for rel, fm, commit in stale:
        print("  STALE " + esc(f"{rel}: FM {fm} < last commit {commit}"))
    for rel in missing_fm:
        print("  NO-FM " + esc(rel))
    print("stale_fm_report: %d docs; %d stale (>2d skew, listed), "
          "%d with 1-2d recent-tick skew (unlisted), %d without FM - "
          "REPORT-ONLY (dates move only with real edits; run the "
          "owner's date filter on the FM column to bucket the "
          "never-touched cohort)" % (n_docs, len(stale), skew_short,
                                     len(missing_fm)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
