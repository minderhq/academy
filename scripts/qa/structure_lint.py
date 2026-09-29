#!/usr/bin/env python3
"""Structural lint for the PROJECT-OMEGA corpus: fence parity + H1 discipline.

Hard gates (exit 1 on any finding):
  - unbalanced code fences. Counting is CommonMark length-aware: a closing
    fence carries no info string and at least as many backticks as its
    opener, so triple-backtick examples inside 4-backtick wrappers are
    legal (the naive toggle regex once reported 4193 phantom findings).
  - markdown files with more than one H1 outside fences.
  - markdown files with zero H1 outside fences.
  - heading level jumps outside fences (HJ-01): a heading that skips more
    than one level deeper than the previous heading (H2 -> H4) breaks the
    document outline for TOC renderers, screen readers and any platform
    deriving a navigation tree; going back up is free. Born from the
    tick-278 census that measured the corpus at 0 jumps right after the
    tick-277 same-level-children re-level - the lock keeps the outline
    monotone as content grows.

Baseline (2026-09-29): 462 files scanned, 0 / 0 / 0 / 0 findings.
Materialized from the formerly repo-external verify_a3_omega.py temp script;
the fence/H1 logic is preserved as materialized, HJ-01 joined in
tick-278 (2026-09-29).

Usage:
    python scripts/qa/structure_lint.py [--root REPO_ROOT]

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import io
import re
import sys

SKIP_DIRS = {".git", ".claude", "node_modules", ".venv", "venv",
            "__pycache__"}
SKIP_EXT = {".ipynb", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf",
            ".zip", ".gz", ".whl", ".bin"}

FENCE = re.compile(r"^(\s*)(`{3,})([\w+-]*)\s*$")
H1 = re.compile(r"^# \S")
HEAD_ALL = re.compile(r"^(#{1,6})\s+\S")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=str, default=None,
                        help="repository root (default: two levels up from this script)")
    args = parser.parse_args()
    import os
    root = args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    unbalanced, multi_h1, zero_h1, level_jumps = [], [], [], []
    total = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in (".md", ".markdown", ".mdx", ".txt", "") or ext in SKIP_EXT:
                continue
            p = os.path.join(dirpath, fn)
            try:
                with io.open(p, encoding="utf-8") as f:
                    lines = f.read().split("\n")
            except (UnicodeDecodeError, OSError):
                continue
            total += 1
            rel = os.path.relpath(p, root).replace(os.sep, "/")

            # fence parity (CommonMark): closing fence = no info string AND len >= opener
            state = 0
            for ln in lines:
                m = FENCE.match(ln)
                if m:
                    ticks, lang = len(m.group(2)), m.group(3)
                    if state and not lang and ticks >= state:
                        state = 0
                    elif not state:
                        state = ticks
            if state:
                unbalanced.append(rel)

            # real H1s outside fences + heading level jumps (HJ-01)
            if fn.lower().endswith((".md", ".markdown", ".mdx")):
                in_fence = 0
                h1s = 0
                prev_level = 0
                for ln in lines:
                    m = FENCE.match(ln)
                    if m:
                        ticks, lang = len(m.group(2)), m.group(3)
                        if in_fence and not lang and ticks >= in_fence:
                            in_fence = 0
                        elif not in_fence:
                            in_fence = ticks
                        continue
                    if in_fence:
                        continue
                    hm = HEAD_ALL.match(ln)
                    if hm:
                        level = len(hm.group(1))
                        if prev_level and level > prev_level + 1:
                            level_jumps.append(
                                (rel, prev_level, level,
                                 ln.strip().lstrip("#").strip()))
                        prev_level = level
                    if H1.match(ln):
                        h1s += 1
                if h1s > 1:
                    multi_h1.append((rel, h1s))
                elif h1s == 0:
                    zero_h1.append(rel)

    ok = not (unbalanced or multi_h1 or zero_h1 or level_jumps)
    print(esc("Scanned files: %d" % total))
    print(esc("Unbalanced fences: %d" % len(unbalanced)))
    for x in unbalanced[:10]:
        print("  ", esc(x))
    print(esc("Multi-H1 files: %d" % len(multi_h1)))
    for rel, n in multi_h1[:15]:
        print(esc("  %s (%d)" % (rel, n)))
    print(esc("Zero-H1 md files: %d" % len(zero_h1)))
    for x in zero_h1[:10]:
        print("  ", esc(x))
    print(esc("Heading level jumps: %d" % len(level_jumps)))
    for rel, prev, level, text in level_jumps[:10]:
        print(esc("  %s: H%d->H%d %s" % (rel, prev, level, text[:40])))
    print("structure_lint: %d files scanned, %d unbalanced fences, "
          "%d multi-H1, %d zero-H1, %d level-jumps -> %s"
          % (total, len(unbalanced), len(multi_h1), len(zero_h1),
             len(level_jumps), "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
