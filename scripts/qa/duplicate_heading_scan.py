#!/usr/bin/env python3
"""duplicate-heading gate (DH-01 HARD, DH-02 report) for PROJECT-OMEGA.

GitHub disambiguates duplicate heading slugs (``text``, ``text-1``,
``text-2``) and binds an explicit anchor to the FIRST heading, so
nothing breaks on GitHub - but a platform TOC/nav generator has to
suffix the duplicates itself, and must know WHICH duplicates are
texture (suffix and move on) and which are artifacts (do not render).

DH-01 (hard): two or more headings in one file share the same text
under the SAME parent heading. The tick-432 parent-context triage
established this as the copy-paste artifact signature: per-item
proof is occurrences sitting under DIFFERENT parent headings, and
the single same-parent pair in the corpus (2102 'Solutions' x2 under
one H2 - indistinguishable TOC slugs) was a real teaching-quality
ambiguity, fixed by renaming to 'Vanishing Gradient Solutions' /
'Exploding Gradient Solutions'. Born drained, hard since. Note the
H2 layer is inside this rule automatically: every H2's parent is the
doc H1, so a duplicated H2 is a same-parent duplicate - and H2 is
the platform nav tree's top level.

DH-02 (report): the same text duplicated under DIFFERENT parent
headings - the accepted per-item texture (assessment/solution
templates: Task / Requirements / Solution Template / Success
Criteria per exercise; per-entity comparisons: Overview / Key
Features / Pros / Cons per database; per-example case studies:
Challenge / Results / Key Lessons per case). The inventory exists so
platform nav generation has its slug inventory and rot cannot hide
inside it; the count moves with content by design.

Fence model: the shared family idiom - length-aware ticks, ">"
blockquote prefix, frontmatter skipped. Comparison is case-insensitive
on the raw heading text (close enough for dup detection; exact GitHub
slugger parity is anchor_check's job). Parent = nearest previous
heading of strictly smaller level; with RH-02 banning skips, children
of one parent share a level, so the rule is level-blind by
construction.

Run over the whole corpus:
    python scripts/qa/duplicate_heading_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
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


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def scan_file(root: Path, path: Path, hard: list[str],
              texture: list[str]) -> None:
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
    heads: list[tuple[int, str]] = []  # (level, normalized text)
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
            heads.append((len(hm.group(1)), hm.group(2).strip().lower()))
    same_parent: Counter[tuple[str, str]] = Counter()
    parents_of_text: dict[str, set[str]] = {}
    for i, (lvl, text) in enumerate(heads):
        # parent = nearest previous heading of strictly smaller level
        parent = ""
        for plvl, ptext in reversed(heads[:i]):
            if plvl < lvl:
                parent = ptext
                break
        same_parent[(parent, text)] += 1
        parents_of_text.setdefault(text, set()).add(parent)
    for (parent, text), n in same_parent.items():
        if n > 1:
            hard.append(
                f"{rel}: DH-01 duplicate heading '{text[:50]}' x{n} "
                f"under the same parent '{parent[:40]}' - copy-paste "
                f"artifact signature (per-item proof is DIFFERENT "
                f"parents; tick-432: the one such pair, 2102 'Solutions'"
                f" x2, was a real ambiguity and was renamed)")
    for text, ps in parents_of_text.items():
        n = sum(cnt for (p, t), cnt in same_parent.items() if t == text)
        if n > 1 and len(ps) > 1:
            texture.append(f"{rel}: DH-02 '{text[:50]}' x{n}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    hard: list[str] = []
    texture: list[str] = []
    n_files: set[str] = set()
    for path in sorted((args.root / "docs").rglob("*.md")):
        before = len(hard) + len(texture)
        scan_file(args.root, path, hard, texture)
        if len(hard) + len(texture) > before:
            n_files.add(path.relative_to(args.root).as_posix())
    for f in hard:
        print(esc(f))
    print(f"duplicate_heading_scan: {len(texture)} DH-02 cross-parent "
          f"per-item duplicate classes (accepted texture - platform "
          f"TOC generators suffix these slugs; inventory, not findings) "
          f"in {len(n_files)} files across docs/")
    for f in texture:
        print(esc("  " + f))
    print(f"duplicate_heading_scan: {len(hard)} DH-01 same-parent "
          f"findings - HARD gate, born drained (tick-432 parent-context "
          f"triage: 67/68 classes cross-parent texture, the single "
          f"same-parent pair 2102 renamed same day)")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
