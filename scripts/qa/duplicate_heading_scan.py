#!/usr/bin/env python3
"""duplicate-heading report for the PROJECT-OMEGA corpus.

DH-01  two or more ATX headings in one file share the same text. GitHub
       disambiguates the slugs (``text``, ``text-1``, ``text-2``) and
       binds an explicit anchor to the FIRST heading, so nothing breaks
       on GitHub - but a platform TOC/nav generator has to suffix the
       duplicates itself, and this inventory is exactly what it needs.
       A new duplicate outside the accepted idiom (a copy-paste
       artifact) lands here as the review queue.

Accepted texture (tick-282 census verdict): per-item sectioned documents
reuse generic section labels - 69 duplicate classes across 32 files,
every one of them that one idiom:
  - assessment/solution templates: Task / Requirements / Solution
    Template / Success Criteria per exercise (phase6/7-practice.md,
    PRACTICE.md, SOLUTION-LAB-*)
  - per-entity comparisons: Overview / Key Features / Pros / Cons per
    database (CP-002), Architecture / Strengths / Weaknesses per
    framework (7303), Windows / macOS / Linux per step (ENVIRONMENT-SETUP)
  - per-example case studies: Challenge / Results / Key Lessons per case
    (REAL-WORLD-EXAMPLES.md), Purpose / Implementation per pattern (2301)

Report mode (exit 0 by design): the corpus idiom is legitimate; the
gate exists so platform nav generation has its slug inventory and rot
cannot hide inside it. Hard-gating this class would fight the corpus's
own teaching texture, like hard-gating NC-02 fragments.

Fence model: the shared family idiom - length-aware ticks, ">"
blockquote prefix, frontmatter skipped. Comparison is case-insensitive
on the raw heading text (close enough for dup detection; exact GitHub
slugger parity is anchor_check's job).

Run over the whole corpus:
    python scripts/qa/duplicate_heading_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# Shared family idiom: length-aware ticks + blockquote prefix.
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
HEAD_RE = re.compile(r"^(#{1,6}) (.+?)\s*$")


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
    heads: list[str] = []
    for raw in lines[start:]:
        m = FENCE_RE.match(raw)
        if m:
            ticks, lang = len(m.group(1)), m.group(2)
            if state and not lang and ticks >= state:
                state = 0
            elif not state:
                state = ticks
            continue
        if state:
            continue
        hm = HEAD_RE.match(raw)
        if hm:
            heads.append(hm.group(2).strip().lower())
    for text, n in Counter(heads).items():
        if n > 1:
            findings.append(
                f"{rel}: DH-01 duplicate heading '{text[:50]}' x{n} - "
                f"GitHub binds the slug to the first; platform TOC "
                f"generators must suffix (per-item sections are the "
                f"accepted idiom)")


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
    print(f"duplicate_heading_scan: {len(findings)} duplicate heading "
          f"texts (DH-01; per-item sections reusing generic labels are "
          f"the accepted texture - platform TOC generators suffix these "
          f"slugs; report mode - exit 0 by design) in {len(n_files)} "
          f"files across docs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
