#!/usr/bin/env python3
"""Whitespace hygiene (WS-01..03, HARD) for Minder Academy.

Three whitespace rot classes, all fence-aware, all born clean at
the tick-466 census:

WS-01  three or more consecutive blank lines outside fences -
       markdown collapses them to one paragraph break, so a
       triple-blank run is authoring residue, not layout (the two
       found sites both sat before `## Related Documents`);
       inside fences blank runs are teaching examples and legal
WS-02  trailing whitespace on a fence-exempt line - 2+ trailing
       spaces are a CommonMark hard line break (an accidental
       `<br>`), 1 is editor residue; either way the line ends
       with invisible bytes the platform stores and diffs
WS-03  a tab used mid-line outside fences - tabs fragment list
       indentation across renderers; the corpus uses spaces
       everywhere

Invisible-character rot (NBSP/ZWSP/BOM/control chars) was
censused the same tick: zero corpus-wide, left un-gated until a
class appears.

Run over the whole corpus:
    python scripts/qa/whitespace_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(```|~~~)")  # CommonMark: <=3 leading spaces
FM_CLOSE = re.compile(r"^---\s*$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def body_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return lines
    for i, ln in enumerate(lines[1:40], 1):
        if FM_CLOSE.match(ln):
            return lines[i + 1:]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        n_docs += 1
        rel = os.path.relpath(path, args.root).replace("\\", "/")
        lines = body_lines(path.read_text(encoding="utf-8",
                                          errors="replace"))
        in_fence = False
        run = 0
        for i, ln in enumerate(lines, 1):
            if FENCE.match(ln):
                in_fence = not in_fence
                run = 0
                continue
            if in_fence:
                continue
            if not ln.strip():
                run += 1
                if run == 3:
                    findings.append("WS-01 %s:%d: 3+ consecutive "
                                    "blank lines (collapses to one "
                                    "break - authoring residue)"
                                    % (rel, i))
                continue
            run = 0
            stripped = ln.rstrip("\r")
            tail = len(stripped) - len(stripped.rstrip(" \t"))
            if tail:
                findings.append("WS-02 %s:%d: trailing whitespace "
                                "(%d char%s)%s" % (rel, i, tail,
                                "s" if tail != 1 else "",
                                " - accidental <br> if 2+"
                                if tail >= 2 else ""))
            core = stripped.rstrip()
            m = re.search(r"\S\t", core)
            if m:
                findings.append("WS-03 %s:%d: mid-line tab "
                                "(spaces everywhere else in "
                                "the corpus)" % (rel, i))

    for f in findings:
        print("  " + esc(f))
    print("whitespace_scan: %d docs; %d WS findings - all hard "
          "(WS-01 3+ blank runs, WS-02 trailing whitespace, "
          "WS-03 mid-line tabs; all fence-aware; born tick-466 "
          "after 2 triple-blank drains; invisible-char census "
          "clean)" % (n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
