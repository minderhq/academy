#!/usr/bin/env python3
"""Module README lesson order (LO-01) for Minder Academy.

The platform renders module navigation in README document order, so
the order lesson links appear in IS the learning path. Lesson IDs
encode the intended sequence within a module (NNNN monotonically
increasing with difficulty ramp), so a README that lists 5103 before
5101 presents the path scrambled.

LO-01 (hard): the FIRST-OCCURRENCE order of lesson links in each
module README must be strictly increasing. First occurrence - not
every occurrence - because several phase-1/2 READMEs repeat their
full lesson list in a tail summary section; a repeat restarts the
sequence legitimately. Guides and assessments are genre extras, not
sequence members; their link positions are free.

Birth census (2026-09-30): 5 stray lesson bullets (5103, 5203, 5204,
6203, 7403 - appended by the tick-444 nav drain before the first
lesson header instead of after their ID-sorted block) over 4 module
READMEs made the first occurrences 5103-5101-5102 style; drained the
same tick by relocating each bullet after the block of the highest-ID
lesson header it follows. Zero from then on: HARD gate (KW-03).

Run over the whole corpus:
    python scripts/qa/lesson_order_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NUMBERED = re.compile(r"^\d")
LINK_RE = re.compile(r"\]\(([^)#]+?\.md)\)")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    phases = args.root / "docs" / "phases"
    n_modules = 0
    n_lessons = 0
    findings: list[str] = []

    for rd in sorted(p for p in phases.glob("phase*/*") if p.is_dir()):
        if not (rd / "README.md").exists():
            continue
        kids = {k.name for k in rd.glob("*.md")
                if NUMBERED.match(k.name)}
        if not kids:
            continue
        n_modules += 1
        try:
            text = (rd / "README.md").read_text(
                encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        seen: set[int] = set()
        prev = 0
        for m in LINK_RE.findall(text):
            target = (rd / m).resolve()
            if target.parent != rd.resolve() or target.name not in kids:
                continue  # genre extras / cross-references are free
            n = int(target.name[:4])
            if n in seen:
                continue  # tail-repeat sections restart legitimately
            seen.add(n)
            n_lessons += 1
            if n < prev:
                findings.append(
                    "LO-01 lesson %04d listed after %04d in %s"
                    % (n, prev, rd.relative_to(args.root).as_posix()))
            prev = n

    print("lesson_order_check: %d modules, %d first-occurrence lesson "
          "links ordered" % (n_modules, n_lessons))
    for f in findings:
        print("  " + esc(f))
    print("lesson_order_check: %d LO-01 findings - hard gate, born at "
          "zero (census 2026-09-30: 5 stray bullets over 4 READMEs, "
          "drained same tick)" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
