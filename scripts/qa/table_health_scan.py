#!/usr/bin/env python3
"""Pipe-table structural health (TH-01, HARD) for Minder Academy.

One render-surface class, born clean at the tick-699 census:

TH-01  a row whose pipe-separator count differs from its table
       block's delimiter row - GFM sizes a table by the delimiter
       row, pads shorter rows with empty cells and drops the
       excess of longer ones, so a ragged row is silent content
       loss or a phantom column on the platform (the birth face
       was the fleet's own notebook_execution_scan registration
       row, whose prose carried an unescaped pipe that minted a
       phantom fourth cell; drained in-tick)

The measurement rules ARE the judgment (each learned from the
tick-699 census over the real corpus):

- fence-aware line-state walk: fenced lines are teaching examples,
  a pipe there never renders as a separator, and fence lines
  themselves never join a block
- inline-code spans are stripped before counting - a backticked
  pipe renders literally inside its cell
- a backslash-escaped pipe is cell CONTENT (GFM renders the
  literal character), so it is removed before counting
- a real GFM table block is a run of 2+ consecutive pipe-carrying
  lines whose SECOND line is a delimiter row (dashes, colons,
  spaces and pipes only, at least one dash); runs without a
  delimiter row are prose with pipes in them, not tables
- consistency is per-block, not per-file - a 2-column table three
  lines after a 5-column one is the measured normal shape
- rows carry the corpus's full-pipe shape (leading and trailing
  pipes on every row), so every bare pipe counts as a separator

Scope: docs markdown, front-matter exempt, run over the whole
corpus:
    python scripts/qa/table_health_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
FM_CLOSE = re.compile(r"^---\s*$")
INLINE = re.compile(r"`[^`]*`")
DELIM = re.compile(r"^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")


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


def separators(line: str) -> int:
    stripped = INLINE.sub("", line)
    return stripped.replace("\\|", "").count("|")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    n_blocks = 0
    n_rows = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        n_docs += 1
        rel = os.path.relpath(path, args.root).replace("\\", "/")
        lines = body_lines(path.read_text(encoding="utf-8",
                                          errors="replace"))
        in_fence, f_char, f_len = False, "", 0
        blocks: list[list[tuple[int, str]]] = []
        block: list[tuple[int, str]] = []
        for lineno, ln in enumerate(lines, 1):
            m = FENCE.match(ln)
            if m:
                ch, n = m.group(1)[0], len(m.group(1))
                if in_fence:
                    if ch == f_char and n >= f_len:
                        in_fence = False
                else:
                    in_fence = True
                    f_char, f_len = ch, n
                if len(block) >= 2:
                    blocks.append(block)
                block = []
                continue
            if in_fence:
                if len(block) >= 2:
                    blocks.append(block)
                block = []
                continue
            if "|" in ln:
                block.append((lineno, ln))
            else:
                if len(block) >= 2:
                    blocks.append(block)
                block = []
        if len(block) >= 2:
            blocks.append(block)

        for blk in blocks:
            if len(blk) < 2 or not DELIM.match(blk[1][1]):
                continue
            n_blocks += 1
            n_rows += len(blk)
            width = separators(blk[1][1])
            for lineno, ln in blk:
                n = separators(ln)
                if n != width:
                    findings.append(
                        "TH-01 %s:%d: row carries %d pipe separators, "
                        "the delimiter row %d - GFM pads short rows "
                        "with empty cells and drops long ones"
                        % (rel, lineno, n, width))

    for f in findings:
        print(esc(f))
    print("%d docs, %d table blocks, %d rows, %d findings"
          % (n_docs, n_blocks, n_rows, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
