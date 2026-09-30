#!/usr/bin/env python3
"""Emphasis parity (EM-01, HARD) for PROJECT-OMEGA.

Bold markers `**` must pair within one render block. The tick-465
census found 7 PREREQUISITES.md files carrying a heading that read
`### If you're not familiar:**` - a stray `**` leaked from the
sibling template (`**If you're not familiar:**` paragraph label),
rendering a literal `**` in the published heading. Line-level
counting cannot police this: bold legitimately spans lines inside
a paragraph (`**fp16 7B...` newline `...11GB**`), so parity is
checked per BLOCK:

  - headings (`#`..`######`) are their own one-line block
  - paragraphs run until a blank line, another heading, a table
    row (`|`), a blockquote (`>`), or a list item (`-`/`*`/`+`
    or `1.` style)
  - fenced code blocks are skipped; inline code is scrubbed
    first (` ``...`` ` may contain unpaired asterisks)

EM-01 fires when a block holds an odd number of `**` markers.
Born after the 7-heading drain, at 0 findings.

Run over the whole corpus:
    python scripts/qa/emphasis_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(```|~~~)")  # CommonMark: <=3 leading spaces
HEADING = re.compile(r"^#{1,6}\s")
LIST = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
TABLE = re.compile(r"^\s*\|")
QUOTE = re.compile(r"^\s*>")
FM_CLOSE = re.compile(r"^---\s*$")
INLINE_CODE = re.compile(r"`{2,}[^`]*`{2,}|`[^`]*`")  # double-backtick first


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


def check_block(block: list[str], rel: str, start: int,
                findings: list[str]) -> None:
    joined = "\n".join(block)
    scrubbed = INLINE_CODE.sub("", joined)
    if scrubbed.count("**") % 2 == 1:
        snippet = block[0].strip()
        if len(snippet) > 60:
            snippet = snippet[:57] + "..."
        findings.append("%s:%d: odd `**` count (%d) in block - %s"
                        % (rel, start, scrubbed.count("**"), snippet))


def scan_file(path: Path, rel: str, findings: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = body_lines(text)
    block: list[str] = []
    start = 0
    in_fence = False

    def flush(i: int) -> None:
        nonlocal block, start
        if block:
            check_block(block, rel, start, findings)
        block = []
        start = 0

    for idx, ln in enumerate(lines):
        lineno = idx + 1
        if FENCE.match(ln):
            flush(idx)
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not ln.strip():
            flush(idx)
            continue
        if HEADING.match(ln):
            flush(idx)
            # a heading is its own one-line block
            check_block([ln], rel, lineno, findings)
            continue
        if (LIST.match(ln) or TABLE.match(ln) or QUOTE.match(ln)):
            flush(idx)
            continue  # list/table/quote lines excluded from prose parity
        if not block:
            start = lineno
        block.append(ln)
    flush(len(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        n_docs += 1
        scan_file(path, os.path.relpath(path, args.root).replace("\\", "/"),
                  findings)

    for f in findings:
        print("  EM-01 " + esc(f))
    print("emphasis_scan: %d docs; %d EM findings - all hard "
          "(bold `**` must pair within one block; headings are "
          "own blocks, paragraphs span lines, fences+inline code "
          "skipped; born tick-465 after 7 stray-heading drains)"
          % (n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
