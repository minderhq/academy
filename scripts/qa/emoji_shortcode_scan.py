#!/usr/bin/env python3
"""emoji-shortcode gate for the Minder Academy corpus.

EM-01  gemoji shortcodes (``:rocket:`` form) are banned in prose: the
       corpus idiom is literal emoji (tick-279 census: literal forms
       dominate by orders of magnitude - U+2705 x1213 vs 28
       ``:white_check_mark:`` - across 173 files), and a platform load
       step would need a shortcode->emoji mapping while literals render
       everywhere. ``:star3:`` even rendered as raw text on GitHub (not
       a valid gemoji name).

Born from the tick-279 census: 82 real-emoji shortcodes across 11
files, in 10 same-emoji both-form clash classes, normalized to literal
emoji (75 lines via the fence-aware pass, 1 box-drawing banner line by
hand to keep column alignment). Technical tokens that merely look like
shortcodes stay legal: ``:memory:`` (SQLite/Qdrant in-memory URI),
``:server:`` (K3s join token), ``:bus:`` / ``:v2:`` / ``:logger:`` /
``:localhost:`` (format strings and URLs) - all live inside code
fences, which this gate never inspects; inline code is scrubbed too
(UM-01 idiom).

Fence model: length-aware ticks borrowed from structure_lint (the
fence-parity authority) plus the ">" blockquote prefix UM-01
established, and frontmatter is skipped - the same model as
unfinished_marker_scan and empty_section_scan.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-279).

Run over the whole corpus:
    python scripts/qa/emoji_shortcode_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Length-aware ticks (structure_lint's model) + blockquote prefix (UM-01).
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")

# The exact emoji-shortcode names the corpus produced (18 valid gemoji
# names + the invalid ``star3`` that motivated the fix), sorted longest
# first so prefix-overlapping names match whole.
BANNED = sorted(
    {"white_check_mark", "warning", "star", "star3", "rotating_light",
     "information_source", "x", "rocket", "link", "checkered_flag",
     "trophy", "book", "memo", "red_square", "green_square",
     "orange_square", "purple_square", "blue_square"},
    key=len, reverse=True)
SC_RE = re.compile(":(" + "|".join(BANNED) + "):")
INLINE_CODE_RE = re.compile(r"`[^`]*`")  # UM-01 idiom


def scrub_inline_code(line: str) -> str:
    return INLINE_CODE_RE.sub("", line)


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
    for ln, raw in enumerate(lines[start:], start + 1):
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
        for m in SC_RE.finditer(scrub_inline_code(raw)):
            findings.append(
                f"{rel}:{ln}: EM-01 emoji shortcode ':{m.group(1)}:' in "
                f"prose; use the literal emoji (corpus idiom, renders "
                f"everywhere without a shortcode table)")


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
    print(f"emoji_shortcode_scan: {len(findings)} findings "
          f"(EM-01 gemoji shortcodes in prose; literal emoji is the "
          f"corpus idiom) in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
