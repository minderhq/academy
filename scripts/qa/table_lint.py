#!/usr/bin/env python3
"""table-lint gate for the Minder Academy corpus.

TL-01  a GFM table (header row + ``|---|`` separator row + body) whose
       lines do not all contain the same number of cells. Renderers
       disagree on ragged tables - GitHub pads silently while stricter
       platform renderers (MDX) reject the document - so a curriculum
       destined for a training platform must keep every table
       rectangular.

TL-02  a non-blank line directly after a table block that carries an
       unescaped pipe but is neither a strict row (leading AND
       trailing pipe) nor a GFM table-breaker (heading, blockquote,
       list item, fence): GFM consumes it as one more ragged table
       row - invisible to TL-01's strict model - so a platform
       renderer appends a row the author never wrote as a table.
       Born from the tick-373 census (0 hits) as a lock.

Cell counting follows GFM: ``\\|`` inside a cell is an escaped literal
pipe, not a column separator. The 1202 passthrough troubleshooting
table carries ``dmesg \\| grep vfio`` in a cell - a naive split
miscounts it as a fourth column (tick-225 lesson: the escape must be
resolved before splitting). Fenced regions are skipped so box-drawing
tables inside ```text fences are not scanned.

Hard gate (exit 1 on findings): baseline 0 - the two 3403 category
tables (1-cell divider rows under 6-column headers) and the 6200-
retrieval separator (single column) were drained in tick-225.

Run over the whole corpus:
    python scripts/qa/table_lint.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
BREAK_RE = re.compile(r"^\s*(?:#|>|(?:[-*+]|\d+[.)])\s)")
UNESC_PIPE = re.compile(r"(?<!\\)\|")


def cell_count(line: str) -> int:
    """GFM cells in a table line: resolve \\| escapes, then split."""
    body = line.strip().strip("|").replace("\\|", "\x00")
    return len(body.split("|"))


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    in_fence = False
    lines = path.read_text(encoding="utf-8").split("\n")
    i = 0
    while i < len(lines):
        if FENCE_RE.match(lines[i]):
            in_fence = not in_fence
            i += 1
            continue
        if (not in_fence and i + 1 < len(lines)
                and ROW_RE.match(lines[i]) and SEP_RE.match(lines[i + 1])):
            start = i
            block: list[str] = []
            while i < len(lines) and ROW_RE.match(lines[i]):
                block.append(lines[i])
                i += 1
            counts = sorted({cell_count(l) for l in block})
            if len(counts) > 1:
                findings.append(
                    f"{rel}:{start + 1}: TL-01 ragged table - cells per "
                    f"line {counts} across {len(block)} lines; pad short "
                    f"rows or split the table")
            if i < len(lines):
                nxt = lines[i]
                if (nxt.strip() and not FENCE_RE.match(nxt)
                        and not BREAK_RE.match(nxt)
                        and UNESC_PIPE.search(nxt)
                        and not ROW_RE.match(nxt)):
                    findings.append(
                        f"{rel}:{i + 1}: TL-02 loose table row - an "
                        f"unescaped-pipe line directly after a table "
                        f"block; GFM renders it as an extra ragged row")
            continue
        i += 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_files = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            scan_file(args.root, path, findings)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"table_lint: {len(findings)} findings "
          f"(TL-01 ragged tables: {len(findings)}) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
