#!/usr/bin/env python3
r"""Markdown table integrity (TB-01/02, HARD) for Minder Academy.

The platform renders tables directly - one broken row is a visible
defect for the learner, not a style nit:

TB-01  every body row's cell count equals the header's. Counting
       is escape-aware: `\|` inside a cell is the canonical literal
       pipe (the corpus uses it, e.g. `dmesg \| grep vfio`) and
       must NOT count as a column break
TB-02  the separator row is well-formed (`|---|:--:|` shape) and
       matches the header's width

Scope: top-level pipe tables (consecutive lines starting and
ending with `|`, length >= 2) outside code fences. A group's
header is its first line.

Born tick-459: 533 tables scanned corpus-wide; one real defect
drained same tick - CP-002's Indexing Speed table had the separator
and the first data row merged onto one line
(`|---|---| Qdrant | ~30 seconds |`). The one escaped-pipe row in
1202-TB3 is canonical usage and passes the escape-aware count.

Run over the whole corpus:
    python scripts/qa/table_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
PIPE_ROW = re.compile(r"^\|.*\|\s*$")
SEP_ROW = re.compile(r"^\|[\s:\-|]+\|\s*$")
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
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


def cells(row: str) -> int:
    return len(UNESCAPED_PIPE.findall(row)) - 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_groups = n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        infence, f_char, f_len = False, "", 0
        group: list[str] = []
        lines = body_lines(text)

        def flush() -> None:
            nonlocal n_groups
            if len(group) < 2:
                group.clear()
                return
            n_groups += 1
            head = cells(group[0])
            if not SEP_ROW.match(group[1]):
                findings.append("TB-02 %s: malformed separator `%s`"
                                % (rel, group[1][:50]))
            elif cells(group[1]) != head:
                findings.append(
                    "TB-02 %s: separator width %d != header %d"
                    % (rel, cells(group[1]), head))
            for i, row in enumerate(group[2:], 2):
                if cells(row) != head:
                    findings.append(
                        "TB-01 %s: row has %d cells, header %d (`%s`)"
                        % (rel, cells(row), head, row[:50]))
            group.clear()

        for ln in lines:
            m = FENCE.match(ln)
            if m:
                ch, n = m.group(1)[0], len(m.group(1))
                if infence:
                    if ch == f_char and n >= f_len:
                        infence = False
                else:
                    infence = True
                    f_char, f_len = ch, n
                flush()
                continue
            if infence:
                continue
            if PIPE_ROW.match(ln):
                group.append(ln.strip())
            else:
                flush()
        flush()
        n_docs += 1
    for f in findings:
        print("  " + esc(f))
    print("table_scan: %d tables in %d docs scanned; %d TB findings "
          "- all hard (row/separator width parity, escape-aware "
          "pipes; born tick-459 after CP-002 merged-separator drain)"
          % (n_groups, n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
