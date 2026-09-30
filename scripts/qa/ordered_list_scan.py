#!/usr/bin/env python3
"""Ordered-list integrity (OL-01, HARD) for PROJECT-OMEGA.

OL-01  an ordered-list-marker line carrying 3+ embedded enumeration
       markers (`1. c, 2. b, 3. c, ...`) - a comma-separated key or
       enumeration pasted as prose. CommonMark parses the leading
       marker as a LIST and eats it: the tick-468 census caught all
       7 phase-quiz Answer Key blocks rendering as one broken
       ordered list whose item text starts at "c," with the "1."
       consumed as the marker (and each wrapped line opening a new
       list at 11, 21, ...). Born after escaping 19 line-start
       markers across those 7 blocks (1. -> 1\\. ).

Siblings censused the same tick and left un-gated:
  - horizontal rules: 3003 dash, 0 star/underscore - uniform
  - list delimiters: 2090 `1.`, 0 `1)` - uniform
  - task-list syntax: clean (6 grep hits were plain links)
  - TODO markers: already UM-01's class; hits are the documented
    `# TODO:` teaching convention
  - blockquote callouts: no systematized convention exists (138
    blockquote lines, 12 bold labels, all free-text texture)
  - lists starting at non-1 (337): deliberate continuation
    numbering (course weeks, question ranges), CommonMark-legal,
    the renderer honors the start value

Run over the whole corpus:
    python scripts/qa/ordered_list_scan.py --root .

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
OL = re.compile(r"^\s*\d+[.)]\s")
EMBED = re.compile(r"\d+[.)]\s")


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
        for i, ln in enumerate(lines, 1):
            if FENCE.match(ln):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if OL.match(ln) and len(EMBED.findall(ln)) >= 3:
                snippet = ln.strip()
                if len(snippet) > 55:
                    snippet = snippet[:52] + "..."
                findings.append("OL-01 %s:%d: list marker line with "
                                "embedded enumeration (leading marker "
                                "is eaten by the list parser) - %s"
                                % (rel, i, snippet))

    for f in findings:
        print("  " + esc(f))
    print("ordered_list_scan: %d docs; %d OL findings - all hard "
          "(OL-01 embedded-enumeration list lines; born tick-468 "
          "after 7 quiz answer-key drains / 19 marker escapes; HR "
          "style, list delimiters, task-list syntax, non-1 starts "
          "censused clean or documented)" % (n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
