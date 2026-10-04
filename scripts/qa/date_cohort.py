#!/usr/bin/env python3
"""date-cohort filter over the Last Updated field for Minder Academy.

Every doc carries a machine-readable Last Updated (LU-01/LU-02 hard
gate guarantees it: ISO YYYY-MM-DD, zero variants) - this tool turns
that field into the freshness work queue the platform will want:

  - default: docs grouped by YYYY-MM cohort, oldest first - the
    review surface for "which content has not been touched longest"
  - --since YYYY-MM: only docs last updated BEFORE that month (the
    stale-list filter; e.g. --since 2026-03 lists the whole
    2026-02-and-older cohort)
  - repo-wide reconciliation (tick-458): a raw repo grep for
    "Last Updated: 2026-02" sees MORE than the corpus - the
    scratch layer (experiments/, root files) carries dates too.
    The tool now reports that layer as its own section so the
    grep number and the tool number add up instead of looking
    like a bug. Scratch files keep their dates until someone
    really edits them - no fake bumps on the frozen layer.

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

    SKIP = (".git", ".venv", "node_modules", "__pycache__")
    cohorts: dict[str, list[str]] = defaultdict(list)
    out_by_dir: dict[str, list[str]] = defaultdict(list)
    n_docs = 0
    n_out_no_lu = 0
    for path in sorted(args.root.rglob("*.md")):
        rel = path.relative_to(args.root)
        parts = rel.parts
        if not parts or parts[0] in SKIP:
            continue
        c = cohort_of(path)
        if parts[0] == "docs":
            if c is None:
                continue
            n_docs += 1
            cohorts[c].append(rel.as_posix())
        elif c is None:
            n_out_no_lu += 1
        else:
            out_by_dir[parts[0]].append((rel.as_posix(), c))

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

    out_stale: list[tuple[str, str, str]] = []
    for d in sorted(out_by_dir):
        for rel, c in sorted(out_by_dir[d]):
            if args.since is None or c < args.since:
                out_stale.append((d, rel, c))
    if out_stale:
        print(esc("--- outside docs/ (scratch/meta layer; dates move "
                  "only with real edits) ---"))
        by_dir = defaultdict(list)
        for d, rel, c in out_stale:
            by_dir[d].append((rel, c))
        for d in sorted(by_dir):
            print(esc("  %s: %d" % (d, len(by_dir[d]))))
            for rel, c in sorted(by_dir[d]):
                print(esc("    [%s] %s" % (c, rel)))

    n_out_total = sum(len(v) for v in out_by_dir.values())
    if args.since:
        print("date_cohort: %d corpus docs last updated before %s "
              "+ %d outside docs/ = %d repo-wide (grep-reconciled; "
              "%d corpus + %d outside dated; %d outside md files carry "
              "no Last Updated; exit 0 by design - listing tool)"
              % (listed, args.since, len(out_stale),
                 listed + len(out_stale), n_docs, n_out_total,
                 n_out_no_lu))
    else:
        print("date_cohort: %d corpus docs in %d monthly cohorts "
              "(oldest %s, newest %s) + %d dated files outside docs/; "
              "%d outside md files carry no Last Updated; exit 0 by "
              "design - listing tool"
              % (n_docs, len(order), order[0] if order else "-",
                 order[-1] if order else "-", n_out_total, n_out_no_lu))
    return 0


if __name__ == "__main__":
    sys.exit(main())
