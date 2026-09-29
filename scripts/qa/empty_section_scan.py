#!/usr/bin/env python3
"""empty-section gate for the PROJECT-OMEGA corpus.

ES-01  every heading must own content: a section is empty iff, from its
       heading to the next same-or-higher-level heading (or EOF),
       nothing appears but blank lines, horizontal rules, blockquote
       markers and HTML comments. A non-empty CHILD fills its parent,
       so container sections like "## Questions" + "### 1." are
       legitimate - only headings with neither direct content nor
       filled descendants are findings.

Born from the tick-277 census: 8 findings corpus-wide, all one root
class - container headings whose first child sat at the SAME level, so
the outline mis-nested (a renderer shows "## Part 1" and "## 1.1 What
is Python?" as siblings and every Part section had an empty body).
Fixed in content, not waived: TUTORIAL-000-Python-for-AI.md re-leveled
120 headings so its five Part containers and the Practice Exercises
container genuinely hold their numbered sections, CHEAT-SHEET-001-
Docker.md demoted the two Common Patterns children, and VOLUME-1-
Infrastructure.md inlined a bare subtitle heading as bold prose.
Baseline 0 at birth; the gate locks outline integrity corpus-wide.

Fence model: length-aware ticks borrowed from structure_lint (the
fence-parity authority) - a closing fence must be bare and at least as
long as its opening run, so the 3-backtick examples inside the
corpus's 4-backtick super-fences cannot mis-toggle the state and
report fence-interior heading lookalikes - plus the ">" blockquote
prefix UM-01 established for callout-embedded code.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-277).

Run over the whole corpus:
    python scripts/qa/empty_section_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Length-aware ticks (structure_lint's model) + blockquote prefix (UM-01).
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
HEAD_RE = re.compile(r"^(#{1,6})\s+\S")
HR_RE = re.compile(r"^-{3,}\s*$")
EMPTY_BQ_RE = re.compile(r"^\s*(?:>\s*)?$")
COMMENT_OPEN_RE = re.compile(r"^\s*<!--(?!-->)")  # open, not single-line
COMMENT_LINE_RE = re.compile(r"^\s*<!--.*-->\s*$")
COMMENT_END_RE = re.compile(r".*-->\s*$")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (UnicodeDecodeError, OSError):
        return
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break

    state = 0  # backtick run length of the open fence, 0 = none
    in_comment = False
    # stack entries: [level, heading_text, line_no, direct_content,
    #                 saw_comment_only] - comment_only stays False until
    # an HTML comment is actually consumed inside the section
    stack: list[list] = []

    def close_down(level: int) -> bool:
        # close every entry at level or deeper; returns True when any
        # of them (or one closed earlier in the same call) had content
        filled = False
        while stack and stack[-1][0] >= level:
            ent = stack.pop()
            if filled or ent[3] > 0:
                filled = True
                continue
            tag = " (comment-only)" if ent[4] else " (no content)"
            findings.append(
                f"{rel}:{ent[2]}: ES-01 empty section "
                f"'{ent[1][:60]}'{tag}; every heading must own "
                f"content or filled children")
        if filled and stack:
            stack[-1][3] += 1  # a non-empty child fills its parent
        return filled

    for ln, raw in enumerate(lines[start:], start + 1):
        if in_comment:
            if COMMENT_END_RE.match(raw):
                in_comment = False
            continue
        m = FENCE_RE.match(raw)
        if m:
            ticks, lang = len(m.group(1)), m.group(2)
            if state and not lang and ticks >= state:
                state = 0
            elif not state:
                state = ticks
            if stack:
                stack[-1][3] += 1
            continue
        if state:
            continue
        h = HEAD_RE.match(raw)
        if h:
            close_down(len(h.group(1)))
            stack.append([len(h.group(1)), raw.strip().lstrip("#").strip(),
                          ln, 0, False])
            continue
        if not stack:
            continue
        if raw.strip() == "" or HR_RE.match(raw) or EMPTY_BQ_RE.match(raw):
            continue
        if COMMENT_LINE_RE.match(raw):
            stack[-1][4] = True
            continue
        if COMMENT_OPEN_RE.match(raw):
            in_comment = True
            stack[-1][4] = True
            continue
        stack[-1][3] += 1
        stack[-1][4] = False
    close_down(0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []
    n_files: set[str] = set()
    for path in sorted((args.root / "docs").rglob("*.md")):
        before = len(findings)
        scan_file(args.root, path, findings)
        if len(findings) > before:
            n_files.add(path.relative_to(args.root).as_posix())
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"empty_section_scan: {len(findings)} findings "
          f"(ES-01 heading with no content before the next "
          f"same-or-higher-level heading; filled children count) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
